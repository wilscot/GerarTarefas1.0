from app.models.database import db

# Tentar diferentes nomes de tabela
table_names = [
    "WorkOrder_Tasks",
    "WorkorderTasks", 
    "WorkOrderTasks",
    "Tasks",
    "WO_Tasks"
]

for table_name in table_names:
    try:
        query = f"""
        SELECT TASKID, TITLE, DESCRIPTION, CREATEDTIME
        FROM {table_name}  
        WHERE WORKORDERID = 540030
          AND CREATEDTIME >= '2025-08-21 10:50:00'
        ORDER BY CREATEDTIME DESC
        """
        
        print(f"Tentando tabela: {table_name}")
        results = db.execute_query(query, ())
        
        if results:
            print(f"✅ Encontrado na tabela: {table_name}")
            for row in results:
                print(f'ID: {row["TASKID"]}')
                print(f'Título: {row["TITLE"]}') 
                print(f'Descrição: {row["DESCRIPTION"]}')
                print('---')
            break
        else:
            print(f"❌ Nenhum resultado na tabela: {table_name}")
            
    except Exception as e:
        print(f"❌ Erro na tabela {table_name}: {str(e)}")
        
print("Verificação concluída.")
