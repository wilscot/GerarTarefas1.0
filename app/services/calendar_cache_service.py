"""
Calendar Cache Service
Serviço de cache para dados do calendário
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from app.models.cache import AutoRefreshCache

logger = logging.getLogger(__name__)


class CalendarCacheService:
    """Serviço de cache para dados do calendário"""
    
    def __init__(self):
        self.cache = AutoRefreshCache(
            cache_name="calendar",
            refresh_callback=self._fetch_calendar_data,
            auto_refresh_minutes=999  # Desabilitar auto-refresh temporariamente - 999 minutos
        )
    
    def _fetch_calendar_data(self) -> Optional[Dict[str, Any]]:
        """Busca dados do calendário usando o serviço original"""
        try:
            logger.info("Buscando dados do calendário usando CalendarService...")
            
            # Importar aqui para evitar problemas de circular import
            from app.services.calendar_service import CalendarService
            
            calendar_service = CalendarService()
            calendar_data = calendar_service.get_calendar_data()
            
            if not calendar_data:
                logger.warning("Nenhum dado retornado pelo CalendarService")
                return None
            
            # Verificar se tem weeks_data
            if 'weeks_data' not in calendar_data:
                logger.error("CalendarService não retornou weeks_data")
                return None
            
            # Adicionar timestamp para controle de cache
            calendar_data["last_updated"] = datetime.now().isoformat()
            calendar_data["cached"] = True
            
            logger.info(f"Dados do calendário carregados: {len(calendar_data.get('weeks_data', []))} semanas")
            return calendar_data
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados do calendário: {str(e)}")
            return None
    
    def get_calendar_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtém dados do calendário (cache-first)
        
        Args:
            force_refresh: Forçar atualização dos dados
            
        Returns:
            Dict com dados do calendário na estrutura esperada pelo frontend
        """
        if force_refresh:
            # Força refresh
            fresh_data = self._fetch_calendar_data()
            if fresh_data:
                self.cache.set("calendar_data", fresh_data)
                self.cache.set_persistent("calendar_data", fresh_data)
                return fresh_data
        
        # Tenta obter do cache com auto-refresh
        cached_data = self.cache.get_with_auto_refresh("calendar_data", ttl_minutes=5)
        
        if cached_data:
            return cached_data
        
        # Fallback: tentar serviço original diretamente
        try:
            logger.warning("Cache falhou, tentando serviço original diretamente...")
            from app.services.calendar_service import CalendarService
            calendar_service = CalendarService()
            fallback_data = calendar_service.get_calendar_data()
            if fallback_data and 'weeks_data' in fallback_data:
                # Adicionar indicador de que veio do fallback
                fallback_data["last_updated"] = datetime.now().isoformat()
                fallback_data["fallback"] = True
                return fallback_data
        except Exception as e:
            logger.error(f"Fallback também falhou: {str(e)}")
        
        # Último recurso: dados vazios mas estruturados
        logger.error("Retornando dados vazios para o calendário")
        return {
            "period_start": datetime.now().date().isoformat(),
            "period_end": (datetime.now().date() + timedelta(days=30)).isoformat(),
            "reference_date": datetime.now().date().isoformat(),
            "daily_data": {},
            "weeks_data": [],
            "summary": {},
            "last_updated": datetime.now().isoformat(),
            "error": "Dados não disponíveis"
        }
    
    def invalidate_calendar_cache(self):
        """Invalida cache do calendário"""
        self.cache.invalidate("calendar_data")
        logger.info("Cache do calendário invalidado")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retorna status do cache do calendário"""
        try:
            # Verifica cache TTL
            ttl_data = self.cache.get("calendar_data", ttl_minutes=5)
            
            # Verifica cache persistente
            persistent_data = self.cache.get_persistent("calendar_data")
            
            return {
                "cache_name": "calendar",
                "ttl_cache_available": ttl_data is not None,
                "persistent_cache_available": persistent_data is not None,
                "last_ttl_update": ttl_data.get('last_updated') if ttl_data else None,
                "last_persistent_update": persistent_data.get('last_updated') if persistent_data else None,
                "auto_refresh_minutes": self.cache.auto_refresh_minutes
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status do cache: {str(e)}")
            return {"error": str(e)}


# Instância global do serviço
calendar_cache_service = CalendarCacheService()
