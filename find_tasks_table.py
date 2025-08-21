"""
Script para encontrar a tabela correta de Tasks no ServiceDesk Plus
"""

import os
import sys
import pyodbc
from datetime import datetime

# Adicionar o diretório da aplicação ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_connection():
    """Testa conexão com banco usando diferentes drivers"""
    
    # Usar configurações que já funcionam no seu sistema
    connection_strings = [
        ("Driver 18", "DRIVER={ODBC Driver 18 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"),
        ("Driver 17", "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;")
    ]
    
    for driver_name, connection_string in connection_strings:
        try:
            
            print(f"Tentando conectar com driver: {driver_name}")
            conn = pyodbc.connect(connection_string, timeout=10)
            print(f"✅ Conexão estabelecida com {driver_name}")
            
            # Lista todas as tabelas que contém "task" no nome
            cursor = conn.cursor()
            
            print("\n📋 Buscando tabelas relacionadas a Tasks...")
            tables_query = """
            SELECT TABLE_SCHEMA, TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_TYPE = 'BASE TABLE'
              AND (
                LOWER(TABLE_NAME) LIKE '%task%' OR
                LOWER(TABLE_NAME) LIKE '%work%' OR
                LOWER(TABLE_NAME) LIKE '%order%'
              )
            ORDER BY TABLE_NAME
            """
            
            cursor.execute(tables_query)
            tables = cursor.fetchall()
            
            if tables:
                print(f"\n📊 Encontradas {len(tables)} tabelas relacionadas:")
                for schema, table in tables:
                    full_name = f"{schema}.{table}"
                    print(f"  - {full_name}")
                    
                    # Para cada tabela, vamos verificar as colunas
                    try:
                        columns_query = """
                        SELECT COLUMN_NAME, DATA_TYPE 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                        ORDER BY ORDINAL_POSITION
                        """
                        cursor.execute(columns_query, (schema, table))
                        columns = cursor.fetchall()
                        
                        # Verifica se tem colunas típicas de tasks
                        has_taskid = any('TASKID' in col[0].upper() for col in columns)
                        has_workorderid = any('WORKORDERID' in col[0].upper() for col in columns)
                        has_description = any('DESCRIPTION' in col[0].upper() for col in columns)
                        
                        if has_taskid and has_workorderid and has_description:
                            print(f"    🎯 CANDIDATA: {full_name} tem TASKID, WORKORDERID e DESCRIPTION")
                            print(f"    📝 Colunas: {', '.join([col[0] for col in columns])}")
                        elif has_taskid or (has_workorderid and has_description):
                            print(f"    ⚠️  POSSÍVEL: {full_name}")
                            print(f"    📝 Colunas: {', '.join([col[0] for col in columns])}")
                            
                    except Exception as e:
                        print(f"    ❌ Erro ao verificar colunas: {e}")
                        
            else:
                print("❌ Nenhuma tabela relacionada encontrada")
                
            # Teste específico para WorkOrder (sabemos que existe)
            print(f"\n🔍 Testando estrutura da tabela WorkOrder...")
            try:
                test_query = "SELECT TOP 1 * FROM dbo.WorkOrder"
                cursor.execute(test_query)
                columns = [column[0] for column in cursor.description]
                print(f"📋 Colunas da WorkOrder: {', '.join(columns)}")
            except Exception as e:
                print(f"❌ Erro ao consultar WorkOrder: {e}")
                
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Falha com {driver_name}: {e}")
            continue
    
    print("❌ Não foi possível estabelecer conexão com nenhum driver")
    return False

if __name__ == "__main__":
    print("🔍 Procurando tabela correta de Tasks no ServiceDesk Plus...")
    print("=" * 60)
    test_connection()
