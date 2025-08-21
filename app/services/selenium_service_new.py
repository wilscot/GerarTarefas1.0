"""
Selenium Service
Integração com o script de automação existente com verificação real de TASKIDs
"""

import os
import subprocess
import threading
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.models.database import db

logger = logging.getLogger(__name__)

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOGS_DIR = os.path.join(BASE_DIR, "app", "logs")

# Criar diretórios necessários
os.makedirs(LOGS_DIR, exist_ok=True)

# Caminhos de arquivos
SCRIPT_PATH = os.path.join(BASE_DIR, "1 - Criador de tarefas final 3.0.py")
AUTOMATION_LOG_PATH = os.path.join(LOGS_DIR, "automation.log")
LAST_REQUEST_FILE = os.path.join(BASE_DIR, "last_request.txt")
LAST_HOURS_FILE = os.path.join(BASE_DIR, "last_hours.txt")

class SeleniumService:
    """Serviço para execução do Selenium com verificação real de TASKIDs"""
    
    def __init__(self):
        self.script_path = Path(SCRIPT_PATH)
        self.log_file = Path(AUTOMATION_LOG_PATH)
        self.executions = {}  # execution_id -> execution_data
    
    def _generate_exec_tag(self) -> str:
        """Gera EXEC_TAG único para execução"""
        now = datetime.now()
        return f"AUTO_{now.strftime('%Y%m%d_%H%M%S')}"
    
    def start_automation(self, workorder_id: int, hours_target: float = 8.0) -> Dict[str, Any]:
        """
        Inicia automação Selenium em background com verificação SQL
        
        Args:
            workorder_id: ID do chamado
            hours_target: Horas alvo para geração
            
        Returns:
            Dict com execution_id e status inicial
        """
        try:
            execution_id = str(uuid.uuid4())
            exec_tag = self._generate_exec_tag()
            started_at = datetime.now()
            
            # Dados da execução
            execution_data = {
                "execution_id": execution_id,
                "workorder_id": workorder_id,
                "hours_target": hours_target,
                "exec_tag": exec_tag,
                "status": "started",
                "started_at": started_at,
                "finished_at": None,
                "created_task_ids": [],
                "error": None
            }
            
            self.executions[execution_id] = execution_data
            
            # Salvar configuração para o script
            self._save_automation_config(workorder_id, hours_target, exec_tag)
            
            # Iniciar thread de execução
            thread = threading.Thread(
                target=self._run_selenium_with_verification,
                args=(execution_id,)
            )
            thread.daemon = True
            thread.start()
            
            logger.info(f"Automação iniciada - execution_id: {execution_id}, exec_tag: {exec_tag}, workorder_id: {workorder_id}")
            
            return {
                "execution_id": execution_id,
                "workorder_id": workorder_id,
                "hours_target": hours_target,
                "exec_tag": exec_tag,
                "status": "started",
                "started_at": started_at.isoformat()
            }
            
        except Exception as e:
            error_msg = f"Erro ao iniciar automação: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "status": "error"
            }
    
    def get_execution_result(self, execution_id: str) -> Dict[str, Any]:
        """
        Obtém resultado de uma execução específica
        
        Args:
            execution_id: ID da execução
            
        Returns:
            Dict com status e resultados da execução
        """
        if execution_id not in self.executions:
            return {
                "error": "Execution ID não encontrado",
                "status": "not_found"
            }
        
        execution = self.executions[execution_id]
        
        return {
            "execution_id": execution_id,
            "workorder_id": execution["workorder_id"],
            "hours_target": execution["hours_target"],
            "exec_tag": execution["exec_tag"],
            "status": execution["status"],
            "started_at": execution["started_at"].isoformat(),
            "finished_at": execution["finished_at"].isoformat() if execution["finished_at"] else None,
            "created_task_ids": execution["created_task_ids"],
            "error": execution["error"]
        }
    
    def _run_selenium_with_verification(self, execution_id: str):
        """
        Executa Selenium e verifica criação de tarefas no SQL
        """
        execution = self.executions[execution_id]
        
        try:
            # Atualizar status
            execution["status"] = "running"
            
            logger.info(f"Iniciando Selenium - execution_id: {execution_id}, exec_tag: {execution['exec_tag']}")
            
            # Executar script Selenium
            selenium_success = self._execute_selenium_script(execution["exec_tag"])
            
            if not selenium_success:
                execution["status"] = "error"
                execution["error"] = "Falha na execução do script Selenium"
                execution["finished_at"] = datetime.now()
                return
            
            # Aguardar um pouco antes de verificar SQL
            import time
            time.sleep(5)
            
            # Verificar criação de tarefas no SQL
            created_tasks = self._verify_created_tasks(
                execution["workorder_id"],
                execution["exec_tag"],
                execution["started_at"]
            )
            
            execution["finished_at"] = datetime.now()
            
            if created_tasks:
                execution["status"] = "success"
                execution["created_task_ids"] = created_tasks  # Agora é lista de dicts
                
                # Log resumido para facilitar leitura
                task_summary = ", ".join([f"#{task['task_id']} ({task['time_spent']}h)" for task in created_tasks])
                logger.info(f"Automação concluída com sucesso - execution_id: {execution_id}, "
                           f"{len(created_tasks)} tarefas criadas: {task_summary}")
                
                # Invalidar cache apenas em caso de sucesso
                self._invalidate_cache()
                
            else:
                execution["status"] = "no_tasks_detected"
                logger.warning(f"Automação executada mas nenhuma tarefa detectada - execution_id: {execution_id}")
            
        except Exception as e:
            execution["status"] = "error"
            execution["error"] = str(e)
            execution["finished_at"] = datetime.now()
            logger.error(f"Erro na automação - execution_id: {execution_id}: {str(e)}", exc_info=True)
    
    def _execute_selenium_script(self, exec_tag: str) -> bool:
        """
        Executa o script Selenium com EXEC_TAG
        
        Args:
            exec_tag: Tag de execução para incluir nas tarefas
            
        Returns:
            True se executado com sucesso
        """
        try:
            logger.info("Iniciando execução do script Selenium...")
            
            # Comando para executar o script com exec_tag
            cmd = ["python", str(SCRIPT_PATH), "--exec-tag", exec_tag]
            
            # Configurar ambiente sem prompt interativo
            env = os.environ.copy()
            env["NO_PROMPT"] = "1"
            
            # Executar com timeout
            with open(self.log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"\n=== Automação iniciada: {datetime.now().isoformat()} ===\n")
                log_f.write(f"EXEC_TAG: {exec_tag}\n")
                log_f.write(f"Comando: {' '.join(cmd)}\n\n")
                
                result = subprocess.run(
                    cmd,
                    stdout=log_f,
                    stderr=subprocess.STDOUT,
                    timeout=300,  # 5 minutos timeout
                    cwd=str(self.script_path.parent),
                    env=env
                )
                
                log_f.write(f"=== Automação finalizada: {datetime.now().isoformat()} ===\n")
                log_f.write(f"Exit code: {result.returncode}\n\n")
            
            success = result.returncode == 0
            logger.info(f"Script Selenium finalizado - sucesso: {success}, exit code: {result.returncode}")
            
            return success
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout na execução do script Selenium")
            return False
        except Exception as e:
            logger.error(f"Erro ao executar script Selenium: {str(e)}", exc_info=True)
            return False
    
    def _verify_created_tasks(self, workorder_id: int, exec_tag: str, started_at: datetime) -> List[Dict[str, Any]]:
        """
        Verifica no SQL se tarefas foram criadas com o EXEC_TAG
        
        Args:
            workorder_id: ID do workorder
            exec_tag: Tag de execução
            started_at: Momento que a execução iniciou
            
        Returns:
            Lista de dicionários com informações completas das tarefas criadas:
            [{"task_id": int, "title": str, "time_spent": float}, ...]
        """
        try:
            # Janela de busca: 2 minutos antes do início até agora
            search_start = started_at - timedelta(seconds=120)
            search_end = datetime.now()
            
            # Query corrigida baseada na estrutura real do ServiceDesk
            query = """
            SELECT DISTINCT
                td.TASKID,
                td.TITLE AS TaskTitle,
                TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
                TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
                td.CREATEDDATE,
                tdesc.DESCRIPTION
            FROM dbo.TaskDetails td
            JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.TASKID = td.TASKID
            LEFT JOIN dbo.Task_Fields tf ON tf.TASKID = td.TASKID
            LEFT JOIN dbo.TaskDescription tdesc ON tdesc.TASKID = td.TASKID
            WHERE wttd.WORKORDERID = ?
              AND td.CREATEDDATE >= ?
              AND td.CREATEDDATE <= ?
              AND tdesc.DESCRIPTION LIKE ?
            """
            
            # Parâmetros da query - timestamps em milissegundos (formato ServiceDesk)
            exec_tag_discreto = exec_tag[-4:] + " -->"
            exec_tag_html_encoded = exec_tag[-4:] + " --&gt;"  # Versão HTML encoded
            
            # Buscar ambos os padrões: normal e HTML encoded
            search_pattern_normal = f"%{exec_tag_discreto}%"
            search_pattern_encoded = f"%{exec_tag_html_encoded}%"
            
            timestamp_inicio = int(search_start.timestamp() * 1000)
            timestamp_fim = int(search_end.timestamp() * 1000)
            
            # Tentar primeiro com padrão HTML encoded (mais comum no ServiceDesk)
            params_encoded = (
                workorder_id,
                timestamp_inicio,
                timestamp_fim,
                search_pattern_encoded
            )
            
            results = db.execute_query(query, params_encoded)
            
            # Se não encontrar, tentar com padrão normal
            if not results:
                params_normal = (
                    workorder_id,
                    timestamp_inicio,
                    timestamp_fim,
                    search_pattern_normal
                )
                results = db.execute_query(query, params_normal)
                used_pattern = exec_tag_discreto
            else:
                used_pattern = exec_tag_html_encoded
            
            logger.info(f"Busca por tasks com EXEC_TAG {used_pattern}: "
                       f"workorder_id={workorder_id}, período={search_start} até {search_end}")
            
            if results:
                # Construir lista de tarefas com informações completas
                created_tasks = []
                for row in results:
                    task_info = {
                        "task_id": row["TASKID"],
                        "title": row["TaskTitle"] or "Sem título",
                        "time_spent": float(row["TempoGasto"] or 0.0),
                        "time_estimated": float(row["TempoEstimado"] or 0.0)
                    }
                    created_tasks.append(task_info)
                    
                    # Log detalhado
                    created_dt = datetime.fromtimestamp(row["CREATEDDATE"] / 1000)
                    logger.info(f"Task {task_info['task_id']}: '{task_info['title']}' "
                               f"({task_info['time_spent']}h gasto/{task_info['time_estimated']}h estimado) - criada: {created_dt}")
                
                logger.info(f"Total de {len(created_tasks)} tarefas encontradas com EXEC_TAG {exec_tag}")
                return created_tasks
                
            else:
                logger.warning(f"Nenhuma tarefa encontrada com EXEC_TAG {exec_tag} no período")
                logger.warning(f"Testados padrões: '{exec_tag_discreto}' e '{exec_tag_html_encoded}'")
                
                # Debug: verificar se existem tasks criadas no período (sem o padrão)
                debug_query = """
                SELECT COUNT(*), MIN(td.CREATEDDATE), MAX(td.CREATEDDATE)
                FROM dbo.TaskDetails td
                JOIN dbo.WorkOrderToTaskDetails wttd ON wttd.TASKID = td.TASKID
                WHERE wttd.WORKORDERID = ?
                  AND td.CREATEDDATE >= ?
                  AND td.CREATEDDATE <= ?
                """
                
                debug_results = db.execute_query(debug_query, (workorder_id, timestamp_inicio, timestamp_fim))
                if debug_results and debug_results[0][0] > 0:
                    count = debug_results[0][0]
                    min_date = datetime.fromtimestamp(debug_results[0][1] / 1000)
                    max_date = datetime.fromtimestamp(debug_results[0][2] / 1000)
                    logger.warning(f"AVISO: Existem {count} tasks no período ({min_date} até {max_date}) "
                                 f"mas nenhuma com os padrões testados. "
                                 f"Verificar se o Selenium está inserindo o padrão corretamente.")
                else:
                    logger.warning(f"Nenhuma task encontrada no WorkOrder {workorder_id} no período especificado")
                
                return []
                
        except Exception as e:
            logger.error(f"Erro ao verificar tarefas criadas: {str(e)}", exc_info=True)
            return []
    
    def _invalidate_cache(self):
        """Invalida cache após criação bem-sucedida de tarefas"""
        try:
            from app.services.cache_service import CacheService
            CacheService.clear_all_cache()
            logger.info("Cache invalidado após criação de tarefas")
        except Exception as e:
            logger.warning(f"Erro ao invalidar cache: {str(e)}")
    
    def _save_automation_config(self, workorder_id: int, hours_target: float, exec_tag: str):
        """
        Salva configuração para o script de automação
        
        Args:
            workorder_id: ID do chamado
            hours_target: Horas alvo
            exec_tag: Tag de execução
        """
        try:
            # Salvar workorder_id e exec_tag
            with open(LAST_REQUEST_FILE, "w", encoding="utf-8") as f:
                f.write(f"{workorder_id}|{exec_tag}")
            
            # Salvar horas alvo
            with open(LAST_HOURS_FILE, "w", encoding="utf-8") as f:
                f.write(str(hours_target))
                
            logger.debug(f"Configuração salva - workorder_id: {workorder_id}, exec_tag: {exec_tag}, hours: {hours_target}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração: {str(e)}")
            raise

# Instância global do serviço
selenium_service = SeleniumService()
