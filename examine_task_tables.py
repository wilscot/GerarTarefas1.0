"""
Script para examinar tabelas de Tasks específicas no ServiceDesk Plus
"""

import os
import sys
import pyodbc
from datetime import datetime, timedelta

def examine_task_tables():
    """Examina as principais tabelas de tasks"""
    
    connection_string = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
    
    try:
        conn = pyodbc.connect(connection_string, timeout=10)
        cursor = conn.cursor()
        
        # Candidatos principais para examinar
        candidates = [
            "dbo.WorkOrderToTaskDetails",
            "dbo.TaskDetails", 
            "dbo.WorkOrderToTaskTable",
            "dbo.TaskTable"
        ]
        
        for table_name in candidates:
            print(f"\n🔍 Examinando tabela: {table_name}")
            print("="*50)
            
            try:
                # 1. Estrutura da tabela
                print("📋 Estrutura da tabela:")
                columns_query = """
                SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION
                """
                cursor.execute(columns_query, (table_name.split('.')[1],))
                columns = cursor.fetchall()
                
                for col_name, data_type, max_length in columns:
                    length_info = f"({max_length})" if max_length else ""
                    print(f"  - {col_name}: {data_type}{length_info}")
                
                # 2. Contagem de registros
                print(f"\n📊 Contagem de registros:")
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                cursor.execute(count_query)
                count = cursor.fetchone()[0]
                print(f"  Total: {count:,} registros")
                
                # 3. Alguns registros de exemplo (se não for muito grande)
                if count < 100000:  # Só para tabelas menores
                    print(f"\n📝 Exemplos de registros (primeiros 3):")
                    sample_query = f"SELECT TOP 3 * FROM {table_name}"
                    cursor.execute(sample_query)
                    sample_rows = cursor.fetchall()
                    
                    for i, row in enumerate(sample_rows, 1):
                        print(f"  Registro {i}:")
                        for j, value in enumerate(row):
                            col_name = columns[j][0] if j < len(columns) else f"Col{j}"
                            print(f"    {col_name}: {value}")
                
                # 4. Se tem relação com WorkOrder e algum campo de descrição
                has_workorderid = any('WORKORDERID' in col[0].upper() for col in columns)
                has_description = any('DESCRIPTION' in col[0].upper() for col in columns)
                has_taskid = any('TASKID' in col[0].upper() for col in columns)
                
                print(f"\n🎯 Características importantes:")
                print(f"  - Tem WORKORDERID: {'✅' if has_workorderid else '❌'}")
                print(f"  - Tem TASKID: {'✅' if has_taskid else '❌'}")  
                print(f"  - Tem DESCRIPTION: {'✅' if has_description else '❌'}")
                
                if has_workorderid and has_taskid and has_description:
                    print(f"  🌟 PERFEITA: Esta tabela pode ser a que procuramos!")
                elif has_workorderid and has_taskid:
                    print(f"  ⭐ BOA: Esta tabela pode servir para linking")
                    
            except Exception as e:
                print(f"❌ Erro ao examinar {table_name}: {e}")
        
        # Teste específico: buscar um WorkOrder conhecido e suas tasks
        print(f"\n🎯 Teste com WorkOrder real")
        print("="*50)
        
        # Primeiro, pegar um WorkOrder recente
        recent_wo_query = """
        SELECT TOP 5 WORKORDERID, TITLE, CREATEDTIME 
        FROM dbo.WorkOrder 
        WHERE TITLE LIKE '%CSI EAST%'
        ORDER BY CREATEDTIME DESC
        """
        
        cursor.execute(recent_wo_query)
        workorders = cursor.fetchall()
        
        if workorders:
            print("📋 WorkOrders recentes encontrados:")
            for wo_id, title, created in workorders:
                print(f"  - WO {wo_id}: {title} ({created})")
                
            # Usar o primeiro WorkOrder para teste
            test_wo_id = workorders[0][0]
            print(f"\n🧪 Testando com WorkOrder {test_wo_id}:")
            
            # Testar cada tabela candidata
            for table_name in candidates:
                if table_name == "dbo.WorkOrderToTaskDetails":
                    test_query = f"""
                    SELECT TOP 5 WORKORDERID, TASKID 
                    FROM {table_name} 
                    WHERE WORKORDERID = ?
                    """
                elif table_name == "dbo.WorkOrderToTaskTable":
                    test_query = f"""
                    SELECT TOP 5 WORKORDERID, TASKID 
                    FROM {table_name} 
                    WHERE WORKORDERID = ?
                    """
                elif table_name == "dbo.TaskDetails":
                    # Esta não tem WORKORDERID diretamente, mas podemos verificar via relação
                    continue
                elif table_name == "dbo.TaskTable":
                    # Esta também não tem WORKORDERID diretamente
                    continue
                
                try:
                    cursor.execute(test_query, (test_wo_id,))
                    results = cursor.fetchall()
                    
                    if results:
                        print(f"  ✅ {table_name}: {len(results)} tasks encontradas")
                        for row in results:
                            print(f"    - TASKID: {row[1]}")
                    else:
                        print(f"  ❌ {table_name}: Nenhuma task encontrada")
                        
                except Exception as e:
                    print(f"  ⚠️  {table_name}: Erro - {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")

if __name__ == "__main__":
    print("🔍 Examinando tabelas específicas de Tasks...")
    print("="*60)
    examine_task_tables()
