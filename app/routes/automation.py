"""
Automation routes
Endpoints para execução da automação Selenium com verificação real de TASKIDs
"""

from flask import Blueprint, jsonify, request
from app.services.workorder_service import WorkOrderService
from app.services.cache_service import CacheService
from app.services.selenium_service_new import selenium_service

automation_bp = Blueprint('automation', __name__)

@automation_bp.route('/run', methods=['POST'])
def run_automation():
    """
    Inicia automação Selenium com verificação real de TASKIDs
    
    Request JSON:
        {
            "hours_target": 8.0,
            "workorder_id": 540030  // opcional
        }
    
    Returns:
        202 JSON com execution_id para polling
    """
    try:
        data = request.get_json() or {}
        hours_target = data.get('hours_target', 8.0)
        workorder_id_override = data.get('workorder_id')
        
        # Validar horas alvo
        try:
            hours_target = float(hours_target)
            if hours_target <= 0 or hours_target > 24:
                return jsonify({
                    "error": "Horas alvo deve estar entre 0.1 e 24",
                    "hours_target": hours_target
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "error": "Horas alvo deve ser um número válido",
                "hours_target": hours_target
            }), 400
        
        # Determinar WorkOrder a usar
        if workorder_id_override:
            # Usar ID específico fornecido
            workorder = WorkOrderService.get_workorder_by_id(workorder_id_override)
            if not workorder:
                return jsonify({
                    "error": f"Chamado {workorder_id_override} não encontrado",
                    "workorder_id": workorder_id_override
                }), 404
        else:
            # Usar chamado vigente
            workorder = CacheService.get_current_workorder()
            if not workorder:
                workorder = WorkOrderService.get_current_workorder()
                if workorder:
                    CacheService.set_current_workorder(workorder)
            
            if not workorder:
                return jsonify({
                    "error": "Nenhum chamado vigente encontrado para automação",
                    "workorder_id": None
                }), 404
        
        # Validar workorder para automação
        if not WorkOrderService.validate_workorder_for_automation(workorder):
            return jsonify({
                "error": "Chamado não é válido para automação",
                "workorder_id": workorder.workorder_id,
                "title": workorder.title
            }), 400
        
        # Iniciar automação com verificação SQL
        result = selenium_service.start_automation(workorder.workorder_id, hours_target)
        
        if result.get("error"):
            return jsonify(result), 500
        
        # Retornar 202 Accepted com execution_id para polling
        # IMPORTANTE: Este é apenas o início da execução. 
        # Para saber se tarefas foram realmente criadas, 
        # use GET /automation/result/{execution_id}
        return jsonify({
            **result,
            "message": "Automação iniciada. Use GET /automation/result/{execution_id} para verificar se tarefas foram criadas.",
            "polling_url": f"/automation/result/{result['execution_id']}"
        }), 202
        
    except Exception as e:
        return jsonify({
            "error": f"Erro interno: {str(e)}",
            "status": "error"
        }), 500

@automation_bp.route('/result/<execution_id>', methods=['GET'])
def get_automation_result(execution_id: str):
    """
    Obtém resultado de uma execução específica via polling
    
    Args:
        execution_id: ID da execução
        
    Returns:
        JSON com status e resultados da execução
        Possíveis status: started, running, success, no_tasks_detected, error, timeout, aborted
    """
    try:
        result = selenium_service.get_execution_result(execution_id)
        
        if result.get("status") == "not_found":
            return jsonify(result), 404
        
        # Determinar código HTTP baseado no status
        status_code = 200
        if result.get("status") in ["started", "running"]:
            status_code = 202  # Still processing
        elif result.get("status") == "error":
            status_code = 500
        elif result.get("status") == "no_tasks_detected":
            status_code = 206  # Partial content - ran but no tasks detected
        
        # Adicionar informações mais claras sobre o resultado
        enhanced_result = {**result}
        
        if result.get("status") == "success":
            task_count = len(result.get("created_task_ids", []))
            total_hours = sum(task.get("time_spent", 0) for task in result.get("created_task_ids", []))
            enhanced_result["summary"] = {
                "success": True,
                "tasks_created": task_count,
                "total_hours_logged": round(total_hours, 2),
                "message": f"Automação concluída com sucesso! {task_count} tarefas criadas, {total_hours:.2f}h registradas."
            }
        elif result.get("status") == "no_tasks_detected":
            enhanced_result["summary"] = {
                "success": False,
                "tasks_created": 0,
                "total_hours_logged": 0,
                "message": "Automação executada mas nenhuma tarefa foi criada. Verifique os logs para mais detalhes."
            }
        elif result.get("status") == "error":
            enhanced_result["summary"] = {
                "success": False,
                "tasks_created": 0,
                "total_hours_logged": 0,
                "message": f"Erro na automação: {result.get('error', 'Erro desconhecido')}"
            }
        elif result.get("status") in ["started", "running"]:
            enhanced_result["summary"] = {
                "success": None,
                "tasks_created": None,
                "total_hours_logged": None,
                "message": f"Automação em andamento... (status: {result.get('status')})"
            }
        
        return jsonify(enhanced_result), status_code
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao obter resultado: {str(e)}",
            "execution_id": execution_id,
            "status": "error"
        }), 500

@automation_bp.route('/run-sync', methods=['POST'])
def run_automation_sync():
    """
    Executa automação de forma síncrona com timeout
    
    Request JSON:
        {
            "hours_target": 8.0,
            "workorder_id": 540030,  // opcional
            "timeout": 300           // opcional, padrão 300s (5min)
        }
    
    Returns:
        JSON com resultado final da execução (success/error)
        Só retorna após a automação completar ou dar timeout
    """
    try:
        data = request.get_json() or {}
        hours_target = data.get('hours_target', 8.0)
        workorder_id_override = data.get('workorder_id')
        timeout_seconds = data.get('timeout', 300)  # 5 minutos padrão
        
        # Validar timeout
        if timeout_seconds < 30 or timeout_seconds > 600:
            return jsonify({
                "error": "Timeout deve estar entre 30 e 600 segundos",
                "timeout": timeout_seconds
            }), 400
        
        # Validar horas alvo (mesmo código do endpoint async)
        try:
            hours_target = float(hours_target)
            if hours_target <= 0 or hours_target > 24:
                return jsonify({
                    "error": "Horas alvo deve estar entre 0.1 e 24",
                    "hours_target": hours_target
                }), 400
        except (ValueError, TypeError):
            return jsonify({
                "error": "Horas alvo deve ser um número válido",
                "hours_target": hours_target
            }), 400
        
        # Determinar WorkOrder (mesmo código do endpoint async)
        if workorder_id_override:
            workorder = WorkOrderService.get_workorder_by_id(workorder_id_override)
            if not workorder:
                return jsonify({
                    "error": f"Chamado {workorder_id_override} não encontrado",
                    "workorder_id": workorder_id_override
                }), 404
        else:
            workorder = CacheService.get_current_workorder()
            if not workorder:
                workorder = WorkOrderService.get_current_workorder()
                if workorder:
                    CacheService.set_current_workorder(workorder)
            
            if not workorder:
                return jsonify({
                    "error": "Nenhum chamado vigente encontrado para automação",
                    "workorder_id": None
                }), 404
        
        # Validar workorder para automação
        if not WorkOrderService.validate_workorder_for_automation(workorder):
            return jsonify({
                "error": "Chamado não é válido para automação",
                "workorder_id": workorder.workorder_id,
                "title": workorder.title
            }), 400
        
        # Iniciar automação
        start_result = selenium_service.start_automation(workorder.workorder_id, hours_target)
        
        if start_result.get("error"):
            return jsonify(start_result), 500
        
        execution_id = start_result["execution_id"]
        
        # Fazer polling até completar ou timeout
        import time
        start_time = time.time()
        poll_interval = 2  # 2 segundos entre checks
        
        while time.time() - start_time < timeout_seconds:
            result = selenium_service.get_execution_result(execution_id)
            
            if result.get("status") not in ["started", "running"]:
                # Automação completou
                if result.get("status") == "success":
                    task_count = len(result.get("created_task_ids", []))
                    total_hours = sum(task.get("time_spent", 0) for task in result.get("created_task_ids", []))
                    
                    return jsonify({
                        "success": True,
                        "execution_id": execution_id,
                        "workorder_id": workorder.workorder_id,
                        "hours_target": hours_target,
                        "tasks_created": task_count,
                        "total_hours_logged": round(total_hours, 2),
                        "created_task_ids": result.get("created_task_ids", []),
                        "message": f"Automação concluída com sucesso! {task_count} tarefas criadas, {total_hours:.2f}h registradas.",
                        "execution_time": round(time.time() - start_time, 2)
                    }), 200
                    
                else:
                    # Erro ou nenhuma tarefa detectada
                    return jsonify({
                        "success": False,
                        "execution_id": execution_id,
                        "workorder_id": workorder.workorder_id,
                        "hours_target": hours_target,
                        "tasks_created": 0,
                        "total_hours_logged": 0,
                        "error": result.get("error"),
                        "status": result.get("status"),
                        "message": "Automação executada mas falhou ou não criou tarefas. Verifique os logs.",
                        "execution_time": round(time.time() - start_time, 2)
                    }), 400 if result.get("status") == "no_tasks_detected" else 500
            
            time.sleep(poll_interval)
        
        # Timeout atingido
        return jsonify({
            "success": False,
            "execution_id": execution_id,
            "workorder_id": workorder.workorder_id,
            "hours_target": hours_target,
            "tasks_created": 0,
            "total_hours_logged": 0,
            "error": f"Timeout de {timeout_seconds}s atingido",
            "status": "timeout",
            "message": f"Automação não completou dentro de {timeout_seconds}s. Use GET /automation/result/{execution_id} para verificar posteriormente.",
            "execution_time": timeout_seconds
        }), 408  # Request Timeout
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Erro interno: {str(e)}",
            "status": "error"
        }), 500

@automation_bp.route('/status', methods=['GET'])
def automation_status():
    """
    Retorna o status atual da automação
    """
    try:
        # Status básico sem dependências complexas
        status_data = {
            "status": "idle",
            "processes": [],
            "process_count": 0,
            "last_run": "2025-08-25 10:46:20",
            "last_success": False,
            "message": "Sistema de automação disponível"
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        return jsonify({
            "error": "Erro ao obter status da automação",
            "details": str(e),
            "status": "unknown",
            "processes": [],
            "process_count": 0
        }), 500
