"""
Task Deduplication Service
Serviço para evitar criação de tarefas duplicadas baseado nas últimas tarefas criadas
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from app.services.user_tasks_cache_service import user_tasks_cache_service

logger = logging.getLogger(__name__)

# Caminho do cache local
BASE_DIR = Path(__file__).parent.parent.parent
CACHE_FILE = BASE_DIR / "data" / "cache" / "recent_tasks_dedup.json"

class TaskDeduplicationService:
    """Serviço para evitar tarefas duplicadas"""
    
    def __init__(self):
        self.cache_file = CACHE_FILE
        self.max_recent_tasks = 7  # Últimas 7 tarefas
        
        # Garantir que o diretório existe
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
    
    def get_recent_task_titles(self) -> Set[str]:
        """
        Obtém títulos das últimas 7 tarefas criadas
        
        Returns:
            Set com títulos das tarefas recentes
        """
        try:
            # Buscar tarefas do cache service existente
            tasks_data = user_tasks_cache_service.get_user_tasks()
            
            if not tasks_data or not tasks_data.get('user_tasks'):
                logger.warning("Nenhuma tarefa encontrada no cache")
                return set()
            
            # Extrair títulos das últimas 7 tarefas
            recent_tasks = tasks_data['user_tasks'][:self.max_recent_tasks]
            titles = {task['title'] for task in recent_tasks if task.get('title')}
            
            logger.info(f"Encontrados {len(titles)} títulos únicos nas últimas {self.max_recent_tasks} tarefas")
            
            # Salvar no cache local para análise
            self._save_cache({
                'last_updated': datetime.now().isoformat(),
                'recent_titles': list(titles),
                'task_count': len(recent_tasks),
                'total_titles': len(titles)
            })
            
            return titles
            
        except Exception as e:
            logger.error(f"Erro ao buscar títulos de tarefas recentes: {str(e)}")
            return set()
    
    def filter_available_tasks(self, available_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Filtra tarefas disponíveis removendo as que foram criadas recentemente
        
        Args:
            available_tasks: Lista de tarefas disponíveis do banco_tarefas.csv
            
        Returns:
            Dict com tarefas filtradas e análise detalhada
        """
        try:
            # Obter títulos recentes
            recent_titles = self.get_recent_task_titles()
            
            # Filtrar tarefas
            filtered_tasks = []
            blocked_tasks = []
            
            for task in available_tasks:
                task_title = task.get('title', '').strip()
                if task_title in recent_titles:
                    blocked_tasks.append({
                        'title': task_title,
                        'reason': 'Tarefa criada recentemente'
                    })
                else:
                    filtered_tasks.append(task)
            
            # Preparar análise detalhada
            analysis = {
                'original_count': len(available_tasks),
                'filtered_count': len(filtered_tasks),
                'blocked_count': len(blocked_tasks),
                'recent_titles_count': len(recent_titles),
                'recent_titles': list(recent_titles),
                'blocked_tasks': blocked_tasks,
                'filter_timestamp': datetime.now().isoformat(),
                'can_proceed': len(filtered_tasks) > 0
            }
            
            logger.info(f"Filtro aplicado: {analysis['original_count']} → {analysis['filtered_count']} tarefas disponíveis")
            
            return {
                'filtered_tasks': filtered_tasks,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Erro ao filtrar tarefas: {str(e)}")
            return {
                'filtered_tasks': available_tasks,  # Fallback: retorna todas
                'analysis': {
                    'error': str(e),
                    'original_count': len(available_tasks),
                    'filtered_count': len(available_tasks),
                    'can_proceed': True,
                    'filter_timestamp': datetime.now().isoformat()
                }
            }
    
    def validate_task_selection(self, required_hours: float, available_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida se há tarefas suficientes após filtro de duplicação
        
        Args:
            required_hours: Horas necessárias
            available_tasks: Tarefas disponíveis após filtro
            
        Returns:
            Dict com validação e análise
        """
        total_hours = sum(float(task.get('hours', 0)) for task in available_tasks)
        task_count = len(available_tasks)
        
        validation = {
            'can_proceed': total_hours >= required_hours and task_count > 0,
            'required_hours': required_hours,
            'available_hours': total_hours,
            'available_tasks': task_count,
            'hour_deficit': max(0, required_hours - total_hours),
            'validation_timestamp': datetime.now().isoformat()
        }
        
        if not validation['can_proceed']:
            if task_count == 0:
                validation['abort_reason'] = "Nenhuma tarefa disponível após filtro de duplicação"
            else:
                validation['abort_reason'] = f"Horas insuficientes: {total_hours:.1f}h disponíveis, {required_hours:.1f}h necessárias"
        
        return validation
    
    def _save_cache(self, data: Dict[str, Any]):
        """Salva dados no cache local para análise"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Erro ao salvar cache: {str(e)}")
    
    def get_analysis_report(self) -> Dict[str, Any]:
        """
        Gera relatório de análise para debug
        
        Returns:
            Dict com relatório completo
        """
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
            else:
                cache_data = {}
            
            recent_titles = self.get_recent_task_titles()
            
            return {
                'service_status': 'active',
                'cache_file': str(self.cache_file),
                'cache_exists': self.cache_file.exists(),
                'recent_titles': list(recent_titles),
                'title_count': len(recent_titles),
                'max_recent_tasks': self.max_recent_tasks,
                'cache_data': cache_data,
                'report_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'service_status': 'error',
                'error': str(e),
                'report_timestamp': datetime.now().isoformat()
            }


# Instância global do serviço
task_deduplication_service = TaskDeduplicationService()
