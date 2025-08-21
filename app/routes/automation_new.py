"""
Automation routes
Endpoints para execução da automação Selenium com verificação real de TASKIDs
"""

from flask import Blueprint, jsonify, request
from app.services.workorder_service import WorkOrderService
from app.services.cache_service import CacheService
from app.services.selenium_service import selenium_service

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
        return jsonify(result), 202
        
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
        
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao obter resultado: {str(e)}",
            "execution_id": execution_id,
            "status": "error"
        }), 500
