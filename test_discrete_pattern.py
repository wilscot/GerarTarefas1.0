"""
Script para testar busca de tasks com padrão discreto específico
"""

import os
import sys
import pyodbc
from datetime import datetime, timedelta

def test_discrete_pattern():
    """Testa busca por padrão discreto específico"""
    
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
    
    try:
        conn = pyodbc.connect(connection_string, timeout=10)
        cursor = conn.cursor()
        
        # Simular busca como no código original
        # Vamos usar um exemplo: se o EXEC_TAG for "12345678", ele procura por "5678 -->"
        exec_tag_exemplo = "5236"  # O último que você viu criado
        exec_tag_discreto = exec_tag_exemplo + " -->"
        
        print(f"🔍 Testando busca por padrão discreto: '{exec_tag_discreto}'")
        print("="*60)
        
        # Query corrigida usando as tabelas corretas
        query_corrigida = """
        SELECT 
            t.TASKID, 
            t.TITLE, 
            t.CREATEDDATE,
            td.DESCRIPTION,
            wt.WORKORDERID
        FROM dbo.TaskDetails t
        JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
        LEFT JOIN dbo.TaskDescription td ON t.TASKID = td.TASKID
        WHERE wt.WORKORDERID = ?
          AND t.CREATEDDATE >= ?
          AND t.CREATEDDATE <= ?
          AND td.DESCRIPTION LIKE ?
        ORDER BY t.CREATEDDATE DESC
        """
        
        # Usar dados do seu WorkOrder mais recente
        workorder_id = 540045
        
        # Período das últimas 24 horas
        agora = datetime.now()
        inicio = agora - timedelta(hours=24)
        fim = agora + timedelta(hours=1)
        
        timestamp_inicio = int(inicio.timestamp() * 1000)
        timestamp_fim = int(fim.timestamp() * 1000)
        
        search_pattern = f"%{exec_tag_discreto}%"
        
        print(f"📋 Parâmetros da busca:")
        print(f"  WorkOrder ID: {workorder_id}")
        print(f"  Período: {inicio} até {fim}")
        print(f"  Padrão: {search_pattern}")
        
        try:
            cursor.execute(query_corrigida, (workorder_id, timestamp_inicio, timestamp_fim, search_pattern))
            results = cursor.fetchall()
            
            if results:
                print(f"\n✅ Encontradas {len(results)} tasks com padrão '{exec_tag_discreto}':")
                for taskid, title, created_date, description, wo_id in results:
                    created_dt = datetime.fromtimestamp(created_date / 1000)
                    print(f"  🎯 TASKID {taskid}: {title}")
                    print(f"     Criada: {created_dt}")
                    print(f"     WorkOrder: {wo_id}")
                    if description and exec_tag_discreto in description:
                        # Mostrar contexto do padrão encontrado
                        idx = description.find(exec_tag_discreto)
                        contexto = description[max(0, idx-20):idx+len(exec_tag_discreto)+20]
                        print(f"     📝 Contexto: ...{contexto}...")
            else:
                print(f"\n❌ Nenhuma task encontrada com padrão '{exec_tag_discreto}'")
                
                # Vamos verificar se existem tasks no período sem o padrão
                query_sem_padrao = """
                SELECT COUNT(*), MIN(t.CREATEDDATE), MAX(t.CREATEDDATE)
                FROM dbo.TaskDetails t
                JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
                WHERE wt.WORKORDERID = ?
                  AND t.CREATEDDATE >= ?
                  AND t.CREATEDDATE <= ?
                """
                
                cursor.execute(query_sem_padrao, (workorder_id, timestamp_inicio, timestamp_fim))
                count_result = cursor.fetchone()
                
                if count_result and count_result[0] > 0:
                    min_date = datetime.fromtimestamp(count_result[1] / 1000)
                    max_date = datetime.fromtimestamp(count_result[2] / 1000)
                    print(f"  ℹ️  Mas existem {count_result[0]} tasks no período ({min_date} até {max_date})")
                    
                    # Mostrar algumas tasks recentes deste WorkOrder
                    query_exemplos = """
                    SELECT TOP 3
                        t.TASKID, 
                        t.TITLE, 
                        t.CREATEDDATE,
                        td.DESCRIPTION
                    FROM dbo.TaskDetails t
                    JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
                    LEFT JOIN dbo.TaskDescription td ON t.TASKID = td.TASKID
                    WHERE wt.WORKORDERID = ?
                    ORDER BY t.CREATEDDATE DESC
                    """
                    
                    cursor.execute(query_exemplos, (workorder_id,))
                    exemplos = cursor.fetchall()
                    
                    print(f"\n📝 Últimas 3 tasks do WorkOrder {workorder_id}:")
                    for taskid, title, created_date, description in exemplos:
                        created_dt = datetime.fromtimestamp(created_date / 1000)
                        print(f"  - TASKID {taskid}: {title} ({created_dt})")
                        if description:
                            desc_preview = description.replace('\n', ' ').replace('\r', ' ')[:100]
                            print(f"    Descrição: {desc_preview}...")
                            # Verificar se tem algum padrão "número -->"
                            if " -->" in description:
                                import re
                                padrao_arrows = re.findall(r'\d{4} -->', description)
                                if padrao_arrows:
                                    print(f"    🎯 Padrões encontrados: {padrao_arrows}")
                else:
                    print(f"  ❌ Nenhuma task encontrada no WorkOrder {workorder_id} no período especificado")
                    
        except Exception as e:
            print(f"❌ Erro na consulta: {e}")
        
        # Teste adicional: vamos verificar se a tabela TaskDescription realmente contém 
        # descrições com padrões como "5236 -->"
        print(f"\n🔍 Buscando qualquer task com padrão '#### -->' nas últimas 24h...")
        try:
            busca_geral = """
            SELECT TOP 5
                t.TASKID, 
                t.TITLE, 
                t.CREATEDDATE,
                td.DESCRIPTION,
                wt.WORKORDERID
            FROM dbo.TaskDetails t
            JOIN dbo.WorkOrderToTaskDetails wt ON t.TASKID = wt.TASKID
            LEFT JOIN dbo.TaskDescription td ON t.TASKID = td.TASKID
            WHERE t.CREATEDDATE >= ?
              AND td.DESCRIPTION LIKE '%[0-9][0-9][0-9][0-9] -->%'
            ORDER BY t.CREATEDDATE DESC
            """
            
            cursor.execute(busca_geral, (timestamp_inicio,))
            results_geral = cursor.fetchall()
            
            if results_geral:
                print(f"✅ Encontradas {len(results_geral)} tasks com padrão numérico '#### -->':")
                for taskid, title, created_date, description, wo_id in results_geral:
                    created_dt = datetime.fromtimestamp(created_date / 1000)
                    print(f"  🎯 TASKID {taskid}: {title} (WO: {wo_id}, {created_dt})")
                    # Extrair os padrões
                    import re
                    padroes = re.findall(r'\d{4} -->', description)
                    print(f"     Padrões: {padroes}")
            else:
                print(f"❌ Nenhuma task encontrada com padrão '#### -->' nas últimas 24h")
                
        except Exception as e:
            print(f"❌ Erro na busca geral: {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🔍 Testando busca por padrão discreto...")
    print("="*60)
    test_discrete_pattern()
