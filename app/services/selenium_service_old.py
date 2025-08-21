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
LOGS_DIR = os.path.join(BASE_DIR, "logs")

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
                "status": "started"
            }
            
        except Exception as e:
            error_msg = f"Erro ao iniciar automação: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                "error": error_msg,
                "status": "error"
            }
            
            # Preparar ambiente para o script
            env = os.environ.copy()
            env["NO_PROMPT"] = "1"  # Modo sem prompt
            
            # Salvar configurações nos arquivos que o script lê
            self._save_automation_config(workorder_id, hours_target)
            
            # ID único para este processo
            process_id = f"{workorder_id}_{int(started_at.timestamp())}"
            
            # Executar em thread separada
            thread = threading.Thread(
                target=self._run_selenium_thread,
                args=(process_id, env, workorder_id, hours_target)
            )
            thread.daemon = True
            thread.start()
            
            # Registrar processo
            self.running_processes[process_id] = {
                "workorder_id": workorder_id,
                "hours_target": hours_target,
                "started_at": started_at,
                "thread": thread,
                "status": "running"
            }
            
            logger.info(f"Automação iniciada - WorkOrder: {workorder_id}, Horas: {hours_target}")
            
            return {
                "status": "started",
                "process_id": process_id,
                "started_at": started_at.isoformat(),
                "hours_target": hours_target,
                "workorder_id": workorder_id
            }
            
        except Exception as e:
            logger.error(f"Erro ao iniciar automação: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _save_automation_config(self, workorder_id: int, hours_target: float):
        """Salva configurações para o script"""
        try:
            # Salvar ID do chamado
            with open(LAST_REQUEST_FILE, "w", encoding="utf-8") as f:
                f.write(str(workorder_id))
            
            # Salvar horas alvo
            with open(LAST_HOURS_FILE, "w", encoding="utf-8") as f:
                f.write(str(hours_target))
            
            logger.debug(f"Configurações salvas - WO: {workorder_id}, Horas: {hours_target}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar configurações: {str(e)}")
            raise
    
    def _run_selenium_thread(self, process_id: str, env: dict, workorder_id: int, hours_target: float):
        """Executa o script Selenium em thread separada"""
        try:
            # Comando para executar o script
            cmd = ["python", str(SCRIPT_PATH)]
            
            # Executar com timeout
            with open(self.log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"\n=== Automação iniciada: {datetime.now().isoformat()} ===\n")
                log_f.write(f"WorkOrder: {workorder_id}, Horas: {hours_target}\n")
                log_f.flush()
                
                result = subprocess.run(
                    cmd,
                    cwd=Path("..").resolve(),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutos timeout
                )
                
                # Log da saída
                log_f.write(f"STDOUT:\n{result.stdout}\n")
                log_f.write(f"STDERR:\n{result.stderr}\n")
                log_f.write(f"Return code: {result.returncode}\n")
                log_f.write(f"=== Automação finalizada: {datetime.now().isoformat()} ===\n\n")
            
            # Atualizar status
            if process_id in self.running_processes:
                if result.returncode == 0:
                    self.running_processes[process_id]["status"] = "completed"
                    logger.info(f"Automação concluída com sucesso - Process: {process_id}")
                else:
                    self.running_processes[process_id]["status"] = "failed"
                    logger.error(f"Automação falhou - Process: {process_id}, Code: {result.returncode}")
                
                self.running_processes[process_id]["finished_at"] = datetime.now()
                self.running_processes[process_id]["return_code"] = result.returncode
            
        except subprocess.TimeoutExpired:
            logger.error(f"Automação excedeu timeout - Process: {process_id}")
            if process_id in self.running_processes:
                self.running_processes[process_id]["status"] = "timeout"
                self.running_processes[process_id]["finished_at"] = datetime.now()
        
        except Exception as e:
            logger.error(f"Erro na execução do Selenium - Process: {process_id}: {str(e)}")
            if process_id in self.running_processes:
                self.running_processes[process_id]["status"] = "error"
                self.running_processes[process_id]["error"] = str(e)
                self.running_processes[process_id]["finished_at"] = datetime.now()
    
    def get_process_status(self, process_id: str) -> Optional[Dict[str, Any]]:
        """Obtém status de um processo"""
        return self.running_processes.get(process_id)
    
    def get_running_processes(self) -> Dict[str, Any]:
        """Obtém todos os processos em execução"""
        return {
            "total_processes": len(self.running_processes),
            "processes": {
                pid: {
                    "workorder_id": proc["workorder_id"],
                    "hours_target": proc["hours_target"],
                    "started_at": proc["started_at"].isoformat(),
                    "status": proc["status"],
                    "finished_at": proc.get("finished_at", "").isoformat() if proc.get("finished_at") else None
                }
                for pid, proc in self.running_processes.items()
            }
        }
    
    def cleanup_old_processes(self, max_age_hours: int = 24):
        """Remove processos antigos do registro"""
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
            
            to_remove = [
                pid for pid, proc in self.running_processes.items()
                if proc["started_at"].timestamp() < cutoff_time
            ]
            
            for pid in to_remove:
                del self.running_processes[pid]
            
            if to_remove:
                logger.info(f"Removidos {len(to_remove)} processos antigos")
                
        except Exception as e:
            logger.error(f"Erro ao limpar processos antigos: {str(e)}")

# Instância global do serviço
selenium_service = SeleniumService()
