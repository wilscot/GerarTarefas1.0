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

# Instância global do cache
cache = CacheManager()
