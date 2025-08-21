"""
Teste da correção HTML encoding
"""

import os
import sys
import pyodbc
from datetime import datetime, timedelta

def test_html_encoding_fix():
    """Testa a correção do HTML encoding"""
    
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
    
    try:
        conn = pyodbc.connect(connection_string, timeout=10)
        cursor = conn.cursor()
        
        # Testar com a TASKID 53789 que sabemos que existe
        workorder_id = 540030
        target_taskid = 53789
        exec_tag = "12345678902310"  # Simular EXEC_TAG que geraria "2310 -->"
        
        print(f"🧪 Testando correção HTML encoding")
        print(f"📋 WorkOrder: {workorder_id}")
        print(f"🎯 TASKID alvo: {target_taskid}")
        print(f"🏷️ EXEC_TAG: {exec_tag}")
        print("="*60)
        
        # Simular horário da execução
        exec_time = datetime(2025, 8, 21, 11, 23, 32)  # Horário exato da task
        start_time = exec_time - timedelta(minutes=5)
        end_time = exec_time + timedelta(minutes=5)
        
        timestamp_inicio = int(start_time.timestamp() * 1000)
        timestamp_fim = int(end_time.timestamp() * 1000)
        
        # Padrões a testar
        exec_tag_discreto = exec_tag[-4:] + " -->"      # "2310 -->"
        exec_tag_html_encoded = exec_tag[-4:] + " --&gt;"  # "2310 --&gt;"
        
        print(f"🔍 Padrões a testar:")
        print(f"   Normal: '{exec_tag_discreto}'")
        print(f"   HTML Encoded: '{exec_tag_html_encoded}'")
        
        query = """
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
        
        # Teste 1: Padrão normal
        print(f"\n1️⃣ Testando padrão normal: '{exec_tag_discreto}'")
        search_pattern_normal = f"%{exec_tag_discreto}%"
        
        cursor.execute(query, (workorder_id, timestamp_inicio, timestamp_fim, search_pattern_normal))
        results_normal = cursor.fetchall()
        
        if results_normal:
            print(f"   ✅ Encontradas {len(results_normal)} tasks com padrão normal!")
            for taskid, title, created_date, description in results_normal:
                created_dt = datetime.fromtimestamp(created_date / 1000)
                print(f"      🎯 TASKID {taskid}: {title} ({created_dt})")
        else:
            print(f"   ❌ Nenhuma task encontrada com padrão normal")
        
        # Teste 2: Padrão HTML encoded
        print(f"\n2️⃣ Testando padrão HTML encoded: '{exec_tag_html_encoded}'")
        search_pattern_encoded = f"%{exec_tag_html_encoded}%"
        
        cursor.execute(query, (workorder_id, timestamp_inicio, timestamp_fim, search_pattern_encoded))
        results_encoded = cursor.fetchall()
        
        if results_encoded:
            print(f"   ✅ Encontradas {len(results_encoded)} tasks com padrão HTML encoded!")
            for taskid, title, created_date, description in results_encoded:
                created_dt = datetime.fromtimestamp(created_date / 1000)
                print(f"      🎯 TASKID {taskid}: {title} ({created_dt})")
                
                # Mostrar parte da descrição que contém o padrão
                idx = description.find(exec_tag_html_encoded)
                if idx >= 0:
                    contexto = description[max(0, idx-20):idx+len(exec_tag_html_encoded)+10]
                    print(f"         📝 Contexto: ...{contexto}...")
        else:
            print(f"   ❌ Nenhuma task encontrada com padrão HTML encoded")
        
        # Resultado
        print(f"\n📊 Resultado:")
        if results_encoded:
            print(f"   🎉 SUCESSO! A correção funciona - encontrou task com padrão HTML encoded!")
            print(f"   🔧 O sistema agora deve detectar tasks criadas corretamente!")
        elif results_normal:
            print(f"   ⚠️  Encontrou com padrão normal - verificar se ServiceDesk mudou codificação")
        else:
            print(f"   ❌ Não encontrou com nenhum padrão - problema persiste")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_html_encoding_fix()
