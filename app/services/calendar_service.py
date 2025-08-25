"""
Serviço para gerenciar dados do calendário de produtividade.
Calcula dados diários para visualização em calendário mensal.
"""
from datetime import date, datetime, timedelta, time
from typing import Dict, List, Any, Optional
import logging
from app.services.period_service import get_current_26_25_period
from app.models.database import db

logger = logging.getLogger(__name__)
import logging
from app.services.period_service import get_current_26_25_period
from app.models.database import db
import pyodbc

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self):
        self.owner_id = 2007
        self.workorder_title = "CSI EAST - Datacenter - Execução de Tarefas"
    
    def get_calendar_data(self, reference_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Retorna dados completos do calendário para o período vigente.
        Inclui dados diários de tarefas, exclusões e produtividade.
        """
        ref_date = reference_date or date.today()
        start_date, end_date = get_current_26_25_period(ref_date)
        
        # Obter dados de tarefas do banco
        tasks_data = self._get_tasks_data(start_date, end_date)
        
        # Obter dados de exclusões
        exclusions_data = self._get_exclusions_data(start_date, end_date)
        
        # Processar dados diários
        daily_data = self._process_daily_data(start_date, end_date, tasks_data, exclusions_data)
        
        # Organizar em semanas para exibição
        weeks_data = self._organize_weeks(start_date, end_date, daily_data)
        
        return {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "reference_date": ref_date.isoformat(),
            "daily_data": daily_data,
            "weeks_data": weeks_data,
            "summary": self._calculate_summary(daily_data)
        }
    
    def _get_tasks_data(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Busca dados de tarefas do banco para o período especificado.
        """
        try:
            # Converter datas para timestamps (milissegundos)
            start_dt = datetime.combine(start_date, time.min)
            end_dt = datetime.combine(end_date, time.max)
            start_timestamp = int(start_dt.timestamp() * 1000)
            end_timestamp = int(end_dt.timestamp() * 1000)
            
            query = """
            DECLARE @OwnerId   bigint = ?;
            DECLARE @CutoffMs  bigint = ?;
            DECLARE @EndMs     bigint = ?;

            ;WITH CurrentState AS (
              SELECT
                ws.WORKORDERID,
                ws.OWNERID,
                ROW_NUMBER() OVER (PARTITION BY ws.WORKORDERID ORDER BY ws.ASSIGNEDTIME DESC) AS rn
              FROM dbo.WorkOrderStates ws
            )
            SELECT
              td.TASKID,
              td.TITLE AS TaskTitle,
              w.WORKORDERID,
              w.TITLE AS WorkOrderTitle,
              TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR1, ',', '.')) AS TempoEstimado,
              TRY_CONVERT(decimal(10,2), REPLACE(tf.UDF_CHAR2, ',', '.')) AS TempoGasto,
              tf.UDF_PICK1 AS ComplexidadeCodigo,
              upv.[VALUE] AS ComplexidadeLabel,
              CONVERT(date, DATEADD(SECOND, td.CREATEDDATE / 1000, '1970-01-01')) AS DataCriacao,
              CASE 
                WHEN td.ACTUALENDTIME IS NOT NULL AND td.ACTUALENDTIME > 0 
                THEN CONVERT(date, DATEADD(SECOND, td.ACTUALENDTIME / 1000, '1970-01-01'))
                ELSE CONVERT(date, DATEADD(SECOND, td.CREATEDDATE / 1000, '1970-01-01'))
              END AS DataFechamento,
              td.CREATEDDATE,
              td.ACTUALENDTIME
            FROM dbo.WorkOrder AS w
            JOIN CurrentState AS cs ON cs.WORKORDERID = w.WORKORDERID AND cs.rn = 1
            LEFT JOIN dbo.WorkOrderToTaskDetails AS wttd ON wttd.WORKORDERID = w.WORKORDERID
            LEFT JOIN dbo.TaskDetails AS td ON td.TASKID = wttd.TASKID
            LEFT JOIN dbo.Task_Fields AS tf ON tf.TASKID = td.TASKID
            LEFT JOIN dbo.UDF_PickListValues AS upv
                   ON upv.PickListID = tf.UDF_PICK1
                  AND upv.TABLENAME = 'Task_Fields'
                  AND upv.COLUMNNAME = 'UDF_PICK1'
            WHERE w.TITLE = ?
              AND cs.OWNERID = @OwnerId
              AND td.CREATEDDATE >= @CutoffMs
              AND td.CREATEDDATE <= @EndMs
            ORDER BY td.CREATEDDATE DESC
            """
            
            # Estabelecer conexão
            if not db.connect():
                logger.error("Não foi possível conectar ao banco de dados")
                return []
            
            conn = db._connection
            cursor = conn.cursor()
            cursor.execute(query, [self.owner_id, start_timestamp, end_timestamp, self.workorder_title])
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                # Converter datas para string se necessário
                if row_dict.get('DataCriacao'):
                    row_dict['DataCriacao'] = row_dict['DataCriacao'].isoformat()
                if row_dict.get('DataFechamento'):
                    row_dict['DataFechamento'] = row_dict['DataFechamento'].isoformat()
                results.append(row_dict)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Encontradas {len(results)} tarefas para o período {start_date} a {end_date}")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados de tarefas: {e}")
            return []
    
    def _get_exclusions_data(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Busca dados de exclusões do arquivo JSON para o período especificado.
        """
        try:
            from app.services.exclusion_service import ExclusionService
            exclusion_service = ExclusionService()
            
            # Buscar exclusões para cada dia do período
            exclusions = []
            current_date = start_date
            
            while current_date <= end_date:
                daily_exclusions = exclusion_service.get_exclusions_for_date(current_date)
                for exclusion in daily_exclusions:
                    exclusions.append({
                        'date': current_date.isoformat(),
                        'hours': exclusion.get('hours', 0),
                        'reason': exclusion.get('reason', ''),
                        'type': exclusion.get('type', 'partial')
                    })
                current_date += timedelta(days=1)
            
            logger.info(f"Encontradas {len(exclusions)} exclusões para o período {start_date} a {end_date}")
            return exclusions
            
        except Exception as e:
            logger.error(f"Erro ao buscar dados de exclusões: {e}")
            return []
    
    def _process_daily_data(self, start_date: date, end_date: date, tasks_data: List[Dict], exclusions_data: List[Dict]) -> Dict[str, Dict]:
        """
        Processa dados diários combinando tarefas e exclusões.
        """
        daily_data = {}
        current_date = start_date
        
        # Organizar dados por data
        tasks_by_date = {}
        for task in tasks_data:
            task_date = task.get('DataCriacao')
            if task_date:
                if task_date not in tasks_by_date:
                    tasks_by_date[task_date] = []
                tasks_by_date[task_date].append(task)
        
        exclusions_by_date = {}
        for exclusion in exclusions_data:
            exc_date = exclusion.get('date')
            if exc_date:
                if exc_date not in exclusions_by_date:
                    exclusions_by_date[exc_date] = []
                exclusions_by_date[exc_date].append(exclusion)
        
        # Processar cada dia do período
        while current_date <= end_date:
            date_str = current_date.isoformat()
            day_tasks = tasks_by_date.get(date_str, [])
            day_exclusions = exclusions_by_date.get(date_str, [])
            
            # Calcular total de horas trabalhadas
            hours_worked = sum(task.get('TempoGasto', 0) or 0 for task in day_tasks)
            
            # Calcular total de horas excluídas
            hours_excluded = sum(exc.get('hours', 0) for exc in day_exclusions)
            
            # Determinar tipo de exclusão
            exclusion_type = None
            if hours_excluded >= 8:
                exclusion_type = 'total'
            elif hours_excluded > 0:
                exclusion_type = 'partial'
            
            # Determinar cor do calendário baseada na produtividade
            calendar_color = self._get_calendar_color(
                current_date, hours_worked, hours_excluded, exclusion_type
            )
            
            daily_data[date_str] = {
                'date': date_str,
                'day_of_week': current_date.weekday(),  # 0=segunda, 6=domingo
                'is_weekend': current_date.weekday() >= 5,
                'tasks_count': len(day_tasks),
                'hours_worked': hours_worked,
                'hours_excluded': hours_excluded,
                'exclusion_type': exclusion_type,
                'calendar_color': calendar_color,
                'tasks': day_tasks,
                'exclusions': day_exclusions
            }
            
            current_date += timedelta(days=1)
        
        return daily_data
    
    def _get_calendar_color(self, date_obj: date, hours_worked: float, hours_excluded: float, exclusion_type: Optional[str]) -> str:
        """
        Determina a cor do calendário baseada nas regras de produtividade.
        """
        # Se é fim de semana, cor neutra
        if date_obj.weekday() >= 5:
            return 'weekend'
        
        # Se tem exclusão total (8h+), cor específica
        if exclusion_type == 'total':
            return 'excluded-total'
        
        # Se tem exclusão parcial, considerar horas líquidas
        if exclusion_type == 'partial':
            net_hours = max(0, 8 - hours_excluded)  # Horas que deveria trabalhar
            if hours_worked >= net_hours * 0.8:  # 80% das horas líquidas
                return 'good-with-exclusion'
            else:
                return 'low-with-exclusion'
        
        # Sem exclusões, baseado apenas nas horas trabalhadas
        if hours_worked >= 6:  # 75% de 8h
            return 'good'
        elif hours_worked >= 4:  # 50% de 8h
            return 'average'
        elif hours_worked > 0:
            return 'low'
        else:
            return 'none'
    
    def _organize_weeks(self, start_date: date, end_date: date, daily_data: Dict) -> List[List[Dict]]:
        """
        Organiza os dados diários em semanas para exibição em calendário.
        Cada semana tem 7 dias (domingo a sábado).
        """
        weeks = []
        
        # Encontrar o primeiro domingo do período ou anterior
        first_date = start_date
        days_to_sunday = (first_date.weekday() + 1) % 7
        week_start = first_date - timedelta(days=days_to_sunday)
        
        while week_start <= end_date:
            week = []
            
            # Construir os 7 dias da semana
            for i in range(7):  # Domingo a sábado
                day_date = week_start + timedelta(days=i)
                day_str = day_date.isoformat()
                
                if day_str in daily_data:
                    # Dia dentro do período
                    week.append(daily_data[day_str])
                elif start_date <= day_date <= end_date:
                    # Dia dentro do período mas sem dados (não deveria acontecer)
                    week.append({
                        'date': day_str,
                        'day_of_week': day_date.weekday(),
                        'is_weekend': day_date.weekday() >= 5,
                        'tasks_count': 0,
                        'hours_worked': 0,
                        'hours_excluded': 0,
                        'exclusion_type': None,
                        'calendar_color': 'none'
                    })
                else:
                    # Dia fora do período
                    week.append({
                        'date': day_str,
                        'day_of_week': day_date.weekday(),
                        'is_weekend': day_date.weekday() >= 5,
                        'out_of_period': True,
                        'calendar_color': 'out-of-period'
                    })
            
            weeks.append(week)
            week_start += timedelta(days=7)
            
            # Parar se a próxima semana está completamente fora do período
            if week_start > end_date + timedelta(days=6):
                break
        
        return weeks
    
    def _calculate_summary(self, daily_data: Dict) -> Dict[str, Any]:
        """
        Calcula resumo estatístico do período.
        """
        total_days = len(daily_data)
        business_days = sum(1 for day in daily_data.values() if not day['is_weekend'])
        
        total_hours_worked = sum(day['hours_worked'] for day in daily_data.values())
        total_hours_excluded = sum(day['hours_excluded'] for day in daily_data.values())
        total_tasks = sum(day['tasks_count'] for day in daily_data.values())
        
        days_with_tasks = sum(1 for day in daily_data.values() if day['tasks_count'] > 0)
        days_with_exclusions = sum(1 for day in daily_data.values() if day['hours_excluded'] > 0)
        
        return {
            'total_days': total_days,
            'business_days': business_days,
            'total_hours_worked': total_hours_worked,
            'total_hours_excluded': total_hours_excluded,
            'total_tasks': total_tasks,
            'days_with_tasks': days_with_tasks,
            'days_with_exclusions': days_with_exclusions,
            'average_hours_per_business_day': total_hours_worked / business_days if business_days > 0 else 0
        }
    
    def get_day_details(self, target_date: date) -> Dict[str, Any]:
        """
        Retorna detalhes completos de um dia específico.
        """
        try:
            # Buscar dados apenas para esse dia
            tasks_data = self._get_tasks_data(target_date, target_date)
            exclusions_data = self._get_exclusions_data(target_date, target_date)
            
            daily_data = self._process_daily_data(target_date, target_date, tasks_data, exclusions_data)
            day_data = daily_data.get(target_date.isoformat(), {})
            
            return {
                'date': target_date.isoformat(),
                'day_data': day_data,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar detalhes do dia {target_date}: {e}")
            return {
                'date': target_date.isoformat(),
                'error': str(e),
                'success': False
            }
