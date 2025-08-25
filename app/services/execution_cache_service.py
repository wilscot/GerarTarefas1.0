"""
Execution Cache Service
Serviço de cache para dados de execução (automação, último chamado, etc.)
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.cache import PersistentCache

logger = logging.getLogger(__name__)


class ExecutionCacheService:
    """Serviço de cache para dados de execução"""
    
    def __init__(self):
        self.cache = PersistentCache("execution")
    
    def record_automation_execution(self, status: str, details: Dict[str, Any] = None) -> bool:
        """
        Registra execução da automação Selenium
        
        Args:
            status: Status da execução (started, completed, failed, etc.)
            details: Detalhes adicionais da execução
            
        Returns:
            True se registrado com sucesso
        """
        try:
            execution_data = {
                "status": status,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            }
            
            # Registra última execução
            self.cache.set_persistent("last_automation", execution_data)
            
            # Mantém histórico das últimas 10 execuções
            history = self.get_automation_history()
            history.append(execution_data)
            
            # Mantém apenas as últimas 10
            if len(history) > 10:
                history = history[-10:]
            
            self.cache.set_persistent("automation_history", history)
            
            logger.info(f"Execução da automação registrada: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar execução: {str(e)}")
            return False
    
    def get_last_automation(self) -> Optional[Dict[str, Any]]:
        """Obtém dados da última execução da automação"""
        try:
            data = self.cache.get_persistent("last_automation")
            if data:
                return data.get("data")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter última execução: {str(e)}")
            return None
    
    def get_automation_history(self) -> list:
        """Obtém histórico das execuções"""
        try:
            data = self.cache.get_persistent("automation_history")
            if data and "data" in data:
                return data["data"]
            return []
        except Exception as e:
            logger.error(f"Erro ao obter histórico: {str(e)}")
            return []
    
    def record_last_call(self, call_type: str, endpoint: str, details: Dict[str, Any] = None) -> bool:
        """
        Registra último chamado vigente do sistema
        
        Args:
            call_type: Tipo do chamado (automation, calendar, workorders, etc.)
            endpoint: Endpoint chamado
            details: Detalhes adicionais
            
        Returns:
            True se registrado com sucesso
        """
        try:
            call_data = {
                "call_type": call_type,
                "endpoint": endpoint,
                "timestamp": datetime.now().isoformat(),
                "details": details or {}
            }
            
            self.cache.set_persistent("last_call", call_data)
            
            logger.debug(f"Último chamado registrado: {call_type} -> {endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar último chamado: {str(e)}")
            return False
    
    def get_last_call(self) -> Optional[Dict[str, Any]]:
        """Obtém dados do último chamado"""
        try:
            data = self.cache.get_persistent("last_call")
            if data:
                return data.get("data")
            return None
        except Exception as e:
            logger.error(f"Erro ao obter último chamado: {str(e)}")
            return None
    
    def record_system_startup(self) -> bool:
        """Registra startup do sistema"""
        try:
            startup_data = {
                "timestamp": datetime.now().isoformat(),
                "components_loaded": True
            }
            
            self.cache.set_persistent("last_startup", startup_data)
            logger.info("Startup do sistema registrado")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao registrar startup: {str(e)}")
            return False
    
    def get_system_info(self) -> Dict[str, Any]:
        """Obtém informações gerais do sistema"""
        try:
            last_automation = self.get_last_automation()
            last_call = self.get_last_call()
            startup_data = self.cache.get_persistent("last_startup")
            
            return {
                "last_automation": last_automation,
                "last_call": last_call,
                "last_startup": startup_data.get("data") if startup_data else None,
                "current_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter info do sistema: {str(e)}")
            return {"error": str(e)}
    
    def clear_execution_cache(self) -> bool:
        """Limpa cache de execução"""
        try:
            keys = ["last_automation", "automation_history", "last_call", "last_startup"]
            for key in keys:
                self.cache.invalidate(key)
            
            logger.info("Cache de execução limpo")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False


# Instância global do serviço
execution_cache_service = ExecutionCacheService()
