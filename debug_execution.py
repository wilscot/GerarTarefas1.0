"""
Script para debug da execução específica
"""

import os
import sys
import pyodbc
from datetime import datetime, timedelta

def debug_execution():
    """Debug da execução específica que falhou"""
    
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
    
    try:
        conn = pyodbc.connect(connection_string, timeout=10)
        cursor = conn.cursor()
        
        execution_id = "01195460-3d7f-4165-9d7b-ec49160ef1ce"
        workorder_id = 540030
        target_taskid = 53789  # Task específica criada no teste
        
        print(f"🔍 Debug da execução {execution_id}")
        print(f"📋 WorkOrder: {workorder_id}")
        print(f"🎯 TASKID criada: {target_taskid}")
        print("="*60)
        
        # 1. Verificar se o WorkOrder existe e tem tasks
        print(f"1️⃣ Verificando WorkOrder {workorder_id}...")
        
        wo_query = "SELECT WORKORDERID, TITLE, CREATEDTIME FROM dbo.WorkOrder WHERE WORKORDERID = ?"
        cursor.execute(wo_query, (workorder_id,))
        wo_result = cursor.fetchone()
        
        if wo_result:
            created_dt = datetime.fromtimestamp(wo_result[2] / 1000)
            print(f"   ✅ WorkOrder encontrado: {wo_result[1]} (criado: {created_dt})")
        else:
            print(f"   ❌ WorkOrder {workorder_id} não encontrado!")
            return
        
        # 2. Verificar a task específica criada (TASKID 53789)
        print(f"\n2️⃣ Analisando TASKID {target_taskid}...")
        
        specific_task_query = """
        SELECT 
            t.TASKID, 
            t.TITLE, 
            t.CREATEDDATE,
            td.DESCRIPTION,
            wt.WORKORDERID
        FROM dbo.TaskDetails t
        LEFT JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
        LEFT JOIN dbo.TaskDescription td ON t.TASKID = td.TASKID
        WHERE t.TASKID = ?
        """
        
        cursor.execute(specific_task_query, (target_taskid,))
        specific_task = cursor.fetchone()
        
        if specific_task:
            taskid, title, created_date, description, linked_wo = specific_task
            created_dt = datetime.fromtimestamp(created_date / 1000)
            
            print(f"   ✅ Task encontrada:")
            print(f"      � TASKID: {taskid}")
            print(f"      📝 Título: {title}")
            print(f"      📅 Criada: {created_dt}")
            print(f"      🔗 WorkOrder linkado: {linked_wo}")
            
            if description:
                print(f"      📄 Descrição completa:")
                print(f"         {repr(description)}")  # Mostrar com caracteres de escape
                
                # Verificar padrões
                if " -->" in description:
                    import re
                    padroes = re.findall(r'\d{4} -->', description)
                    if padroes:
                        print(f"      🎯 Padrões '#### -->' encontrados: {padroes}")
                    else:
                        print(f"      ⚠️  Tem '-->' mas não no formato esperado")
                        # Mostrar contexto do -->
                        idx = description.find(" -->")
                        if idx > 0:
                            contexto = description[max(0, idx-10):idx+10]
                            print(f"         Contexto: {repr(contexto)}")
                else:
                    print(f"      ❌ Sem padrão '-->' na descrição")
                    desc_preview = description.replace('\n', ' ').replace('\r', ' ')[:200]
                    print(f"         Preview: {desc_preview}...")
            else:
                print(f"      ❌ Sem descrição na tabela TaskDescription")
            
            # Verificar se está linkada ao WorkOrder correto
            if linked_wo == workorder_id:
                print(f"      ✅ Task corretamente linkada ao WorkOrder {workorder_id}")
            elif linked_wo:
                print(f"      ⚠️  Task linkada ao WorkOrder {linked_wo}, não {workorder_id}")
            else:
                print(f"      ❌ Task não linkada a nenhum WorkOrder!")
                
        else:
            print(f"   ❌ TASKID {target_taskid} não encontrada!")
            return
        
        # 3. Simular busca que o código faz (horário da execução: 11:23:44)
        print(f"\n3️⃣ Simulando busca do código...")
        
        # Horário da execução: 21/08/2025, 11:23:44
        exec_time = datetime(2025, 8, 21, 11, 23, 44)
        start_time = exec_time - timedelta(minutes=15)  # 15 min antes da execução
        end_time = exec_time + timedelta(minutes=10)    # 10 min depois da execução
        
        print(f"   📅 Período de busca: {start_time} até {end_time}")
        
        # Converter para timestamps ServiceDesk
        timestamp_inicio = int(start_time.timestamp() * 1000)
        timestamp_fim = int(end_time.timestamp() * 1000)
        
        # Simular diferentes padrões que podem ter sido usados
        padroes_teste = ["0030 -->", "540030"[-4:] + " -->"]  # WO 540030 -> "0030 -->"
        
        for padrao in padroes_teste:
            print(f"\n   🔍 Testando padrão: '{padrao}'")
            
            search_query = """
            SELECT 
                t.TASKID, 
                t.TITLE, 
                t.CREATEDDATE,
                td.DESCRIPTION
            FROM dbo.TaskDetails t
            JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
            LEFT JOIN dbo.TaskDescription td ON t.TASKID = td.TASKID
            WHERE wt.WORKORDERID = ?
              AND t.CREATEDDATE >= ?
              AND t.CREATEDDATE <= ?
              AND td.DESCRIPTION LIKE ?
            ORDER BY t.CREATEDDATE DESC
            """
            
            search_pattern = f"%{padrao}%"
            
            cursor.execute(search_query, (workorder_id, timestamp_inicio, timestamp_fim, search_pattern))
            search_results = cursor.fetchall()
            
            if search_results:
                print(f"      ✅ Encontradas {len(search_results)} tasks com padrão '{padrao}':")
                for taskid, title, created_date, description in search_results:
                    created_dt = datetime.fromtimestamp(created_date / 1000)
                    print(f"         🎯 TASKID {taskid}: {title} ({created_dt})")
            else:
                print(f"      ❌ Nenhuma task encontrada com padrão '{padrao}'")
                
                # Verificar se tem tasks no período (sem o padrão)
                period_query = """
                SELECT COUNT(*), MIN(t.CREATEDDATE), MAX(t.CREATEDDATE)
                FROM dbo.TaskDetails t
                JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
                WHERE wt.WORKORDERID = ?
                  AND t.CREATEDDATE >= ?
                  AND t.CREATEDDATE <= ?
                """
                
                cursor.execute(period_query, (workorder_id, timestamp_inicio, timestamp_fim))
                period_result = cursor.fetchone()
                
                if period_result and period_result[0] > 0:
                    count = period_result[0]
                    min_date = datetime.fromtimestamp(period_result[1] / 1000)
                    max_date = datetime.fromtimestamp(period_result[2] / 1000)
                    print(f"         ℹ️  Mas existem {count} tasks no período ({min_date} até {max_date})")
                else:
                    print(f"         ❌ Nenhuma task no período")
        
        # 4. Verificar se alguma task foi criada recentemente (últimas 2 horas)
        print(f"\n4️⃣ Verificando tasks criadas nas últimas 2 horas...")
        
        duas_horas_atras = datetime.now() - timedelta(hours=2)
        timestamp_2h = int(duas_horas_atras.timestamp() * 1000)
        
        recent_query = """
        SELECT TOP 10
            t.TASKID, 
            t.TITLE, 
            t.CREATEDDATE,
            wt.WORKORDERID,
            td.DESCRIPTION
        FROM dbo.TaskDetails t
        JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
        LEFT JOIN dbo.TaskDescription td ON t.TASKID = td.TASKID
        WHERE t.CREATEDDATE >= ?
        ORDER BY t.CREATEDDATE DESC
        """
        
        cursor.execute(recent_query, (timestamp_2h,))
        recent_tasks = cursor.fetchall()
        
        if recent_tasks:
            print(f"   ✅ Encontradas {len(recent_tasks)} tasks criadas nas últimas 2h:")
            
            for taskid, title, created_date, wo_id, description in recent_tasks:
                created_dt = datetime.fromtimestamp(created_date / 1000)
                print(f"      🔹 TASKID {taskid}: {title}")
                print(f"         WO: {wo_id}, Criada: {created_dt}")
                
                if description and " -->" in description:
                    import re
                    padroes = re.findall(r'\d{4} -->', description)
                    if padroes:
                        print(f"         🎯 Padrões: {padroes}")
        else:
            print(f"   ❌ Nenhuma task criada nas últimas 2 horas")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    debug_execution()
