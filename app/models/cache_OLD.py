"""
Cache management module
Gerencia cache TTL para otimização de performance
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuração de caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "cache")

class CacheManager:
    """Gerenciador de cache com TTL"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = DATA_DIR
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_file(self, key: str) -> Path:
        """Retorna caminho do arquivo de cache para uma chave"""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str, ttl_minutes: int = 15) -> Optional[Dict[str, Any]]:
        """
        Obtém valor do cache se ainda válido
        
        Args:
            key: Chave do cache
            ttl_minutes: TTL em minutos
            
        Returns:
            Dados do cache ou None se expirado/inexistente
        """
        cache_file = self._get_cache_file(key)
        
        if not cache_file.exists():
            logger.debug(f"Cache miss - arquivo não existe: {key}")
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Verificar se não expirou
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            expires_at = cached_at + timedelta(minutes=ttl_minutes)
            
            if datetime.now() > expires_at:
                logger.debug(f"Cache expired para chave: {key}")
                self.invalidate(key)
                return None
            
            logger.debug(f"Cache hit para chave: {key}")
            return cache_data['data']
            
        except Exception as e:
            logger.error(f"Erro ao ler cache {key}: {str(e)}")
            return None
    
    def set(self, key: str, data: Dict[str, Any]) -> bool:
        """
        Armazena dados no cache
        
        Args:
            key: Chave do cache
            data: Dados a serem armazenados
            
        Returns:
            True se armazenado com sucesso
        """
        cache_file = self._get_cache_file(key)
        
        try:
            cache_entry = {
                "data": data,
                "cached_at": datetime.now().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Cache atualizado para chave: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar cache {key}: {str(e)}")
            return False
    
    def invalidate(self, key: str) -> bool:
        """
        Remove entrada do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            True se removido com sucesso
        """
        cache_file = self._get_cache_file(key)
        
        try:
            if cache_file.exists():
                cache_file.unlink()
                logger.debug(f"Cache invalidado para chave: {key}")
            return True
        except Exception as e:
            logger.error(f"Erro ao invalidar cache {key}: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """
        Limpa todo o cache
        
        Returns:
            True se limpou com sucesso
        """
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cache completo limpo")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar cache: {str(e)}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o cache
        
        Returns:
            Dict com estatísticas do cache
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            
            info = {
                "total_entries": len(cache_files),
                "cache_dir": str(self.cache_dir),
                "entries": []
            }
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    
                    cached_at = datetime.fromisoformat(cache_data['cached_at'])
                    
                    info["entries"].append({
                        "key": cache_file.stem,
                        "cached_at": cache_data['cached_at'],
                        "size_bytes": cache_file.stat().st_size,
                        "age_minutes": int((datetime.now() - cached_at).total_seconds() / 60)
                    })
                except Exception:
                    continue
            
            return info
            
        except Exception as e:
            logger.error(f"Erro ao obter info do cache: {str(e)}")
            return {"error": str(e)}

# Classes especializadas para diferentes tipos de cache

class PersistentCache(CacheManager):
    """Cache persistente para dados que devem sobreviver entre reinicializações"""
    
    def __init__(self, cache_name: str, cache_dir: str = None):
        super().__init__(cache_dir)
        self.cache_name = cache_name
        self.persistent_file = self.cache_dir / f"{cache_name}_persistent.json"
    
    def get_persistent(self, key: str) -> Optional[Dict[str, Any]]:
        """Obtém dados persistentes (sem TTL)"""
        if not self.persistent_file.exists():
            return None
            
        try:
            with open(self.persistent_file, 'r', encoding='utf-8') as f:
                persistent_data = json.load(f)
            
            return persistent_data.get(key)
        except Exception as e:
            logger.error(f"Erro ao ler cache persistente {key}: {str(e)}")
            return None
    
    def set_persistent(self, key: str, data: Any) -> bool:
        """Armazena dados persistentes"""
        try:
            # Carrega dados existentes
            persistent_data = {}
            if self.persistent_file.exists():
                with open(self.persistent_file, 'r', encoding='utf-8') as f:
                    persistent_data = json.load(f)
            
            # Atualiza com novos dados
            persistent_data[key] = {
                "data": data,
                "last_updated": datetime.now().isoformat()
            }
            
            # Salva de volta
            with open(self.persistent_file, 'w', encoding='utf-8') as f:
                json.dump(persistent_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Cache persistente atualizado: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar cache persistente {key}: {str(e)}")
            return False


class AutoRefreshCache(PersistentCache):
    """Cache com auto-refresh baseado em callback"""
    
    def __init__(self, cache_name: str, refresh_callback=None, auto_refresh_minutes: int = 5):
        super().__init__(cache_name)
        self.refresh_callback = refresh_callback
        self.auto_refresh_minutes = auto_refresh_minutes
    
    def get_with_auto_refresh(self, key: str, ttl_minutes: int = 15) -> Optional[Dict[str, Any]]:
        """Obtém dados com auto-refresh se necessário"""
        # Tenta cache normal primeiro
        cached_data = self.get(key, ttl_minutes)
        if cached_data is not None:
            return cached_data
        
        # Se não há dados em cache, tenta persistente
        persistent_data = self.get_persistent(key)
        if persistent_data is not None:
            # Verifica se precisa refresh
            last_updated = datetime.fromisoformat(persistent_data['last_updated'])
            should_refresh = (datetime.now() - last_updated).total_seconds() > (self.auto_refresh_minutes * 60)
            
            if not should_refresh:
                # Dados persistentes ainda válidos, atualiza cache temporário
                self.set(key, persistent_data['data'])
                return persistent_data['data']
        
        # Precisa fazer refresh
        if self.refresh_callback:
            try:
                fresh_data = self.refresh_callback()
                if fresh_data is not None:
                    self.set(key, fresh_data)
                    self.set_persistent(key, fresh_data)
                    return fresh_data
            except Exception as e:
                logger.error(f"Erro no auto-refresh para {key}: {str(e)}")
        
        # Fallback para dados persistentes mesmo se expirados
        if persistent_data is not None:
            return persistent_data['data']
        
        return None

# Instâncias globais do cache
cache = CacheManager()
persistent_cache = PersistentCache("global")
