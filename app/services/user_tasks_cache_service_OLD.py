"""
User Tasks Cache Service
Serviço de cache para tarefas do usuário
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import current_app
from app.models.cache import AutoRefreshCache
from app.models.database import db

logger = logging.getLogger(__name__)


class UserTasksCacheService:
    """Serviço de cache para tarefas do usuário"""
    
    def __init__(self, username: str = "wfrancischini"):
        self.username = username
        self.cache = AutoRefreshCache(
            cache_name="user_tasks",
            refresh_callback=self._fetch_user_tasks,
            auto_refresh_minutes=2  # Auto-refresh a cada 2 minutos
        )
    
    def _fetch_user_tasks(self) -> Optional[Dict[str, Any]]:
        """Busca últimas tarefas do usuário no banco de dados"""
        try:
            logger.info(f"Buscando últimas tarefas do usuário {self.username}...")
            
            # Query para últimas 10 workorders (chamados) criados pelo usuário
            query = """
                SELECT TOP 10
                    wo.WORKORDERID as task_number,
                    wo.TITLE as title,
                    1 as state,
                    3 as priority,
                    wo.CREATEDTIME as opened_at,
                    NULL as resolved_at,
                    0.0 as time_spent,
                    0.0 as time_estimated,
                    'Novo' as state_label,
                    'Moderada' as priority_label
                FROM dbo.WorkOrder wo
                WHERE wo.REQUESTERID = ?
                ORDER BY wo.CREATEDTIME DESC
            """
            
            # Usar diretamente o OWNER_ID da configuração ao invés de buscar na sys_user
            owner_id = current_app.config['OWNER_ID']  # 2007
            
            result = db.execute_query(query, [owner_id])
            
            if not result or len(result) == 0:
                logger.warning(f"Nenhuma tarefa encontrada para o usuário {self.username}")
                return {"user_tasks": [], "last_updated": datetime.now().isoformat()}
            
            user_tasks = []
            for row_dict in result:
                # result agora é lista de dicionários, não tuplas
                # Converter timestamp para datetime se necessário
                opened_at = row_dict.get('opened_at')
                if opened_at and isinstance(opened_at, (int, float)):
                    # CREATEDTIME está em milissegundos, converter para datetime
                    opened_timestamp = opened_at / 1000 if opened_at > 1e10 else opened_at
                    opened_dt = datetime.fromtimestamp(opened_timestamp)
                    opened_at = opened_dt.strftime('%Y-%m-%d %H:%M:%S')
                elif opened_at and hasattr(opened_at, 'strftime'):
                    opened_at = opened_at.strftime('%Y-%m-%d %H:%M:%S')
                
                resolved_at = row_dict.get('resolved_at')
                if resolved_at and isinstance(resolved_at, (int, float)):
                    # Converter timestamp para datetime se necessário
                    resolved_timestamp = resolved_at / 1000 if resolved_at > 1e10 else resolved_at
                    resolved_dt = datetime.fromtimestamp(resolved_timestamp)
                    resolved_at = resolved_dt.strftime('%Y-%m-%d %H:%M:%S')
                elif resolved_at and hasattr(resolved_at, 'strftime'):
                    resolved_at = resolved_at.strftime('%Y-%m-%d %H:%M:%S')
                
                user_tasks.append({
                    'task_number': row_dict.get('task_number'),
                    'title': row_dict.get('title') or 'Sem título',
                    'state': int(row_dict.get('state')) if row_dict.get('state') else 1,
                    'priority': int(row_dict.get('priority')) if row_dict.get('priority') else 3,
                    'opened_at': opened_at,
                    'resolved_at': resolved_at,
                    'time_spent': float(row_dict.get('time_spent')) if row_dict.get('time_spent') else 0.0,
                    'time_estimated': float(row_dict.get('time_estimated')) if row_dict.get('time_estimated') else 0.0,
                    'state_label': row_dict.get('state_label'),
                    'priority_label': row_dict.get('priority_label')
                })
            
            logger.info(f"Carregadas {len(user_tasks)} tarefas do usuário {self.username}")
            
            return {
                "user_tasks": user_tasks,
                "username": self.username,
                "last_updated": datetime.now().isoformat(),
                "total_records": len(user_tasks)
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar tarefas do usuário: {str(e)}")
            return None
    
    def get_user_tasks(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Obtém últimas tarefas do usuário (cache-first)
        
        Args:
            force_refresh: Forçar atualização dos dados
            
        Returns:
            Dict com tarefas do usuário
        """
        if force_refresh:
            # Força refresh
            fresh_data = self._fetch_user_tasks()
            if fresh_data:
                self.cache.set("user_tasks", fresh_data)
                self.cache.set_persistent("user_tasks", fresh_data)
                return fresh_data
        
        # Tenta obter do cache com auto-refresh
        cached_data = self.cache.get_with_auto_refresh("user_tasks", ttl_minutes=5)
        
        if cached_data:
            return cached_data
        
        # Fallback: dados vazios mas estruturados
        logger.warning(f"Retornando dados vazios para tarefas do usuário {self.username}")
        return {
            "user_tasks": [],
            "username": self.username,
            "last_updated": datetime.now().isoformat(),
            "total_records": 0,
            "error": "Dados não disponíveis"
        }
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Obtém resumo das tarefas do usuário"""
        try:
            tasks_data = self.get_user_tasks()
            tasks = tasks_data.get("user_tasks", [])
            
            # Calcular estatísticas
            total_tasks = len(tasks)
            resolved_tasks = len([t for t in tasks if t['state'] == 3])
            total_time_spent = sum(t['time_spent'] for t in tasks)
            avg_time_per_task = total_time_spent / total_tasks if total_tasks > 0 else 0
            
            # Contar por prioridade
            priority_counts = {}
            for task in tasks:
                priority = task['priority_label']
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            return {
                "summary": {
                    "total_tasks": total_tasks,
                    "resolved_tasks": resolved_tasks,
                    "resolution_rate": round((resolved_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0,
                    "total_time_spent": round(total_time_spent, 2),
                    "avg_time_per_task": round(avg_time_per_task, 2),
                    "priority_distribution": priority_counts
                },
                "username": self.username,
                "last_updated": tasks_data.get("last_updated")
            }
            
        except Exception as e:
            logger.error(f"Erro ao calcular resumo das tarefas: {str(e)}")
            return {"error": str(e)}
    
    def invalidate_tasks_cache(self):
        """Invalida cache das tarefas do usuário"""
        self.cache.invalidate("user_tasks")
        logger.info(f"Cache de tarefas do usuário {self.username} invalidado")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Retorna status do cache de tarefas do usuário"""
        try:
            # Verifica cache TTL
            ttl_data = self.cache.get("user_tasks", ttl_minutes=5)
            
            # Verifica cache persistente
            persistent_data = self.cache.get_persistent("user_tasks")
            
            return {
                "cache_name": "user_tasks",
                "username": self.username,
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
user_tasks_cache_service = UserTasksCacheService()
