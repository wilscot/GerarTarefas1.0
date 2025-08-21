"""
Debug para verificar detecção de tarefas criadas
"""
import os
import sys
from datetime import datetime, timedelta

# Adicionar caminho do app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from models.database import db

def test_task_detection():
    """Testar detecção de tarefas com EXEC_TAG"""
    
    # Usar o último EXEC_TAG
    exec_tag = "AUTO_20250821_124713"
    workorder_id = 540030
    
    # Período de busca
    search_start = datetime.now() - timedelta(minutes=30)
    search_end = datetime.now()
    
    print(f"🔍 Testando detecção de tarefas:")
    print(f"   EXEC_TAG: {exec_tag}")
    print(f"   WorkOrder: {workorder_id}")
    print(f"   Período: {search_start} até {search_end}")
    print()
    
    # Parâmetros
    exec_tag_discreto = exec_tag[-4:] + " -->"
    exec_tag_html_encoded = exec_tag[-4:] + " --&gt;"
    
    timestamp_inicio = int(search_start.timestamp() * 1000)
    timestamp_fim = int(search_end.timestamp() * 1000)
    
    print(f"📋 Padrões de busca:")
    print(f"   Normal: {exec_tag_discreto}")
    print(f"   HTML Encoded: {exec_tag_html_encoded}")
    print()
    
    # 1. Query básica para ver se existem tasks no período
    basic_query = """
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
    """
    
    print("📊 Tasks criadas no período (qualquer uma):")
    results = db.execute_query(basic_query, (workorder_id, timestamp_inicio, timestamp_fim))
    
    if results:
        for row in results:
            created_dt = datetime.fromtimestamp(row["CREATEDDATE"] / 1000)
            desc_preview = (row["DESCRIPTION"] or "")[:100] + "..." if len(row["DESCRIPTION"] or "") > 100 else (row["DESCRIPTION"] or "")
            print(f"   ID: {row['TASKID']} | {row['TITLE']} | {created_dt}")
            print(f"   Descrição: {desc_preview}")
            print()
    else:
        print("   ❌ Nenhuma task encontrada no período")
        return
    
    # 2. Testar busca com padrão HTML encoded
    search_pattern_encoded = f"%{exec_tag_html_encoded}%"
    
    print(f"🔍 Buscando com padrão HTML encoded: {search_pattern_encoded}")
    
    # Query completa para busca com padrão
    pattern_query = """
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
    """
    
    encoded_results = db.execute_query(
        pattern_query,
        (workorder_id, timestamp_inicio, timestamp_fim, search_pattern_encoded)
    )
    
    if encoded_results:
        print(f"   ✅ Encontradas {len(encoded_results)} tasks com padrão HTML encoded!")
        for row in encoded_results:
            print(f"   ID: {row['TASKID']} | {row['TITLE']}")
    else:
        print("   ❌ Nenhuma task com padrão HTML encoded")
    
    # 3. Testar busca com padrão normal
    search_pattern_normal = f"%{exec_tag_discreto}%"
    
    print(f"🔍 Buscando com padrão normal: {search_pattern_normal}")
    normal_results = db.execute_query(
        pattern_query,
        (workorder_id, timestamp_inicio, timestamp_fim, search_pattern_normal)
    )
    
    if normal_results:
        print(f"   ✅ Encontradas {len(normal_results)} tasks com padrão normal!")
        for row in normal_results:
            print(f"   ID: {row['TASKID']} | {row['TITLE']}")
    else:
        print("   ❌ Nenhuma task com padrão normal")
    
    # 4. Testar query com UDF para tempo gasto
    if encoded_results or normal_results:
        test_task_id = (encoded_results or normal_results)[0]["TASKID"]
        
        print(f"\n🧪 Testando busca de UDF para task {test_task_id}:")
        
        udf_query = """
        SELECT 
            t.TASKID,
            t.TITLE,
            udf_tempo_gasto.UFVALUE as TEMPO_GASTO,
            udf_tempo_estimado.UFVALUE as TEMPO_ESTIMADO
        FROM dbo.TaskDetails t
        LEFT JOIN dbo.TaskUdfValues udf_tempo_gasto ON t.TASKID = udf_tempo_gasto.TASKID 
            AND udf_tempo_gasto.UDFNAME = 'tempo_gasto'
        LEFT JOIN dbo.TaskUdfValues udf_tempo_estimado ON t.TASKID = udf_tempo_estimado.TASKID 
            AND udf_tempo_estimado.UDFNAME = 'tempo_estimado'
        WHERE t.TASKID = ?
        """
        
        udf_results = db.execute_query(udf_query, (test_task_id,))
        
        if udf_results:
            row = udf_results[0]
            print(f"   Task {row['TASKID']}: {row['TITLE']}")
            print(f"   Tempo Gasto: {row['TEMPO_GASTO']}")
            print(f"   Tempo Estimado: {row['TEMPO_ESTIMADO']}")
        else:
            print("   ❌ Não foi possível buscar UDF")
    
    print("\n✨ Teste completo!")

if __name__ == "__main__":
    test_task_detection()
