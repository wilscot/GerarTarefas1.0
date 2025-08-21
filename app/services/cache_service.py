"""
Cache Service
Serviço para gerenciamento de cache com TTL
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from flask import current_app

from app.models.cache import cache
from app.models.workorder import WorkOrder

logger = logging.getLogger(__name__)

class CacheService:
    """Serviço para gerenciamento de cache"""
    
    WORKORDER_CACHE_KEY = "current_workorder"
    
    @staticmethod
    def get_current_workorder() -> Optional[WorkOrder]:
        """
        Obtém WorkOrder atual do cache
        
        Returns:
            WorkOrder do cache ou None se não encontrado/expirado
        """
        try:
            ttl_minutes = current_app.config['CACHE_TTL_MINUTES']
            cached_data = cache.get(CacheService.WORKORDER_CACHE_KEY, ttl_minutes)
            
            if cached_data:
                workorder = WorkOrder.from_dict(cached_data)
                workorder.cached = True
                workorder.source = "cache"
                logger.debug(f"WorkOrder obtido do cache: {workorder.workorder_id}")
                return workorder
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter WorkOrder do cache: {str(e)}")
            return None
    
    @staticmethod
    def set_current_workorder(workorder: WorkOrder) -> bool:
        """
        Armazena WorkOrder no cache
        
        Args:
            workorder: WorkOrder a ser armazenado
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            # Marcar como vindo do cache para futuras consultas
            workorder.cached = True
            workorder.updated_at = datetime.now()
            
            success = cache.set(CacheService.WORKORDER_CACHE_KEY, workorder.to_dict())
            
            if success:
                logger.debug(f"WorkOrder {workorder.workorder_id} armazenado no cache")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao armazenar WorkOrder no cache: {str(e)}")
            return False
    
    @staticmethod
    def invalidate_current_workorder() -> bool:
        """
        Invalida cache do WorkOrder atual
        
        Returns:
            True se invalidado com sucesso
        """
        try:
            success = cache.invalidate(CacheService.WORKORDER_CACHE_KEY)
            
            if success:
                logger.info("Cache do WorkOrder atual invalidado")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao invalidar cache do WorkOrder: {str(e)}")
            return False
    
    @staticmethod
    def clear_all_cache() -> bool:
        """
        Limpa todo o cache
        
        Returns:
            True se limpou com sucesso
        """
        try:
            success = cache.clear_all()
            
            if success:
                logger.info("Todo o cache foi limpo")
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao limpar todo o cache: {str(e)}")
            return False
    
    @staticmethod
    def get_cache_stats() -> Dict[str, Any]:
        """
        Obtém estatísticas do cache
        
        Returns:
            Dict com estatísticas do cache
        """
        try:
            return cache.get_cache_info()
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas do cache: {str(e)}")
            return {"error": str(e)}
