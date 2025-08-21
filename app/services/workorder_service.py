"""
WorkOrder Service
Lógica de negócio para gerenciamento de chamados
"""

import logging
from typing import Optional
from datetime import datetime
from flask import current_app

from app.models.database import db
from app.models.workorder import WorkOrder

logger = logging.getLogger(__name__)

class WorkOrderService:
    """Serviço para gerenciamento de WorkOrders"""
    
    @staticmethod
    def get_current_workorder() -> Optional[WorkOrder]:
        """
        Busca o chamado vigente baseado nas configurações
        
        Returns:
            WorkOrder atual ou None se não encontrado
        """
        try:
            owner_id = current_app.config['OWNER_ID']
            workorder_title = current_app.config['WORKORDER_TITLE']
            
            query = """
            DECLARE @OwnerId bigint = ?;
            ;WITH CurrentState AS (
              SELECT
                ws.WORKORDERID,
                ws.OWNERID,
                ROW_NUMBER() OVER (PARTITION BY ws.WORKORDERID ORDER BY ws.ASSIGNEDTIME DESC) AS rn
              FROM dbo.WorkOrderStates ws
            )
            SELECT TOP 1
              w.WORKORDERID,
              w.TITLE,
              w.CREATEDTIME,
              cs.OWNERID
            FROM dbo.WorkOrder AS w
            JOIN CurrentState AS cs ON cs.WORKORDERID = w.WORKORDERID AND cs.rn = 1
            WHERE w.TITLE = ?
              AND cs.OWNERID = @OwnerId
            ORDER BY w.CREATEDTIME DESC;
            """
            
            results = db.execute_query(query, (owner_id, workorder_title))
            
            if results and len(results) > 0:
                workorder = WorkOrder.from_sql_result(results[0])
                logger.info(f"WorkOrder encontrado: {workorder.workorder_id}")
                return workorder
            else:
                logger.warning("Nenhum WorkOrder vigente encontrado")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar WorkOrder vigente: {str(e)}")
            return None
    
    @staticmethod
    def get_workorder_by_id(workorder_id: int) -> Optional[WorkOrder]:
        """
        Busca WorkOrder por ID específico
        
        Args:
            workorder_id: ID do chamado
            
        Returns:
            WorkOrder ou None se não encontrado
        """
        try:
            query = """
            SELECT 
              w.WORKORDERID,
              w.TITLE,
              w.CREATEDTIME,
              w.REQUESTERID as OWNERID
            FROM dbo.WorkOrder AS w
            WHERE w.WORKORDERID = ?;
            """
            
            results = db.execute_query(query, (workorder_id,))
            
            if results and len(results) > 0:
                workorder = WorkOrder.from_sql_result(results[0])
                logger.info(f"WorkOrder {workorder_id} encontrado")
                return workorder
            else:
                logger.warning(f"WorkOrder {workorder_id} não encontrado")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar WorkOrder {workorder_id}: {str(e)}")
            return None
    
    @staticmethod
    def validate_workorder_for_automation(workorder: WorkOrder) -> bool:
        """
        Valida se o WorkOrder pode ser usado para automação
        
        Args:
            workorder: WorkOrder a ser validado
            
        Returns:
            True se válido para automação
        """
        if not workorder:
            logger.error("WorkOrder é None")
            return False
        
        expected_title = current_app.config['WORKORDER_TITLE']
        if workorder.title != expected_title:
            logger.error(f"Título do WorkOrder inválido: {workorder.title}")
            return False
        
        expected_owner = current_app.config['OWNER_ID']
        if workorder.owner_id != expected_owner:
            logger.error(f"Owner do WorkOrder inválido: {workorder.owner_id}")
            return False
        
        logger.info(f"WorkOrder {workorder.workorder_id} validado para automação")
        return True
