"""
Script para buscar a tabela de descrição das Tasks
"""

import os
import sys
import pyodbc
from datetime import datetime, timedelta

def find_task_description():
    """Busca onde está a descrição das tasks"""
    
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
    
    try:
        conn = pyodbc.connect(connection_string, timeout=10)
        cursor = conn.cursor()
        
        # Pegar um TaskID específico do teste anterior
        test_taskid = 52729  # Um dos TaskIDs que encontramos
        print(f"🔍 Buscando descrição para TASKID {test_taskid}")
        print("="*50)
        
        # Verificar tabela TaskDescription
        print("📋 Examinando dbo.TaskDescription...")
        try:
            desc_query = "SELECT TASKID, DESCRIPTION FROM dbo.TaskDescription WHERE TASKID = ?"
            cursor.execute(desc_query, (test_taskid,))
            desc_result = cursor.fetchone()
            
            if desc_result:
                print(f"  ✅ Encontrada descrição na TaskDescription:")
                print(f"  TASKID: {desc_result[0]}")
                print(f"  DESCRIPTION: {desc_result[1][:200]}...")  # Primeiros 200 chars
            else:
                print(f"  ❌ Nenhuma descrição encontrada para TASKID {test_taskid}")
                
        except Exception as e:
            print(f"  ❌ Erro ao consultar TaskDescription: {e}")
        
        # Verificar se TaskDetails tem algum campo de descrição que não vimos
        print(f"\n📋 Detalhes completos do TaskDetails para TASKID {test_taskid}...")
        try:
            task_query = "SELECT * FROM dbo.TaskDetails WHERE TASKID = ?"
            cursor.execute(task_query, (test_taskid,))
            task_result = cursor.fetchone()
            
            if task_result:
                # Pegar nomes das colunas
                columns = [column[0] for column in cursor.description]
                print(f"  ✅ Task encontrada:")
                for i, (col_name, value) in enumerate(zip(columns, task_result)):
                    if value and 'TITLE' in col_name.upper():
                        print(f"    {col_name}: {value}")
                    elif value and len(str(value)) > 50:  # Campos que podem conter descrição
                        print(f"    {col_name}: {str(value)[:100]}...")
            else:
                print(f"  ❌ Task {test_taskid} não encontrada")
                
        except Exception as e:
            print(f"  ❌ Erro ao consultar TaskDetails: {e}")
        
        # Buscar todas as tabelas que tem TASKID e algum campo de texto longo
        print(f"\n🔍 Buscando outras tabelas com TASKID que podem ter descrição...")
        description_candidates = [
            "dbo.TaskDescription",
            "dbo.TaskToComment", 
            "dbo.WorkOrderToDescription"  # Pode ser que descrição está na WorkOrder
        ]
        
        for table_name in description_candidates:
            print(f"\n📋 Verificando {table_name}...")
            try:
                # Verificar estrutura
                columns_query = """
                SELECT COLUMN_NAME, DATA_TYPE 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """
                cursor.execute(columns_query, (table_name.split('.')[1],))
                columns = cursor.fetchall()
                
                print(f"  Colunas: {', '.join([col[0] for col in columns])}")
                
                # Se tem TASKID, testar com nosso TASKID
                has_taskid = any('TASKID' in col[0].upper() for col in columns)
                if has_taskid:
                    test_query = f"SELECT TOP 1 * FROM {table_name} WHERE TASKID = ?"
                    cursor.execute(test_query, (test_taskid,))
                    result = cursor.fetchone()
                    
                    if result:
                        print(f"  ✅ Registro encontrado!")
                        for i, value in enumerate(result):
                            col_name = columns[i][0] if i < len(columns) else f"Col{i}"
                            if value and len(str(value)) > 20:
                                print(f"    {col_name}: {str(value)[:150]}...")
                    else:
                        print(f"  ❌ Nenhum registro para TASKID {test_taskid}")
                        
            except Exception as e:
                print(f"  ❌ Erro ao verificar {table_name}: {e}")
        
        # Teste final: buscar numa task recente criada hoje e ver se conseguimos encontrar o padrão discreto
        print(f"\n🎯 Buscando tasks criadas hoje...")
        try:
            # Converter timestamp atual para formato ServiceDesk (milissegundos desde epoch)
            hoje = datetime.now()
            inicio_hoje = hoje.replace(hour=0, minute=0, second=0, microsecond=0)
            timestamp_inicio = int(inicio_hoje.timestamp() * 1000)
            
            recent_tasks_query = """
            SELECT TOP 10 t.TASKID, t.TITLE, t.CREATEDDATE, wt.WORKORDERID
            FROM dbo.TaskDetails t
            JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
            WHERE t.CREATEDDATE >= ?
            ORDER BY t.CREATEDDATE DESC
            """
            
            cursor.execute(recent_tasks_query, (timestamp_inicio,))
            recent_tasks = cursor.fetchall()
            
            if recent_tasks:
                print(f"  ✅ Encontradas {len(recent_tasks)} tasks criadas hoje:")
                for taskid, title, created_date, workorderid in recent_tasks:
                    # Converter timestamp para datetime
                    created_dt = datetime.fromtimestamp(created_date / 1000)
                    print(f"    TASKID {taskid}: {title[:50]}... (WO: {workorderid}, {created_dt})")
                    
                    # Verificar se tem descrição
                    try:
                        desc_query = "SELECT DESCRIPTION FROM dbo.TaskDescription WHERE TASKID = ?"
                        cursor.execute(desc_query, (taskid,))
                        desc_result = cursor.fetchone()
                        
                        if desc_result and desc_result[0]:
                            desc = desc_result[0]
                            if "-->" in desc:
                                print(f"      🎯 ENCONTROU TAG DISCRETO: ...{desc[-50:]}")
                            else:
                                print(f"      📝 Descrição: {desc[:100]}...")
                    except:
                        pass
            else:
                print(f"  ❌ Nenhuma task criada hoje encontrada")
                
        except Exception as e:
            print(f"  ❌ Erro ao buscar tasks recentes: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🔍 Buscando tabela de descrição das Tasks...")
    print("="*60)
    find_task_description()
