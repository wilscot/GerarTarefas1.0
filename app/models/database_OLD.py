"""
Database connection module
Gerencia conexão com SQL Server ServiceDesk com fallback robusto
"""

import os
import pyodbc
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Gerenciador de conexão com SQL Server com fallback robusto"""
    
    def __init__(self):
        self._connection = None
        self.last_driver = None
        self.last_variant = None
        self.last_error = None
        self.latency_ms = None
    
    def connect(self) -> bool:
        """
        Estabelece conexão com SQL Server usando fallback
        Returns: True se conectou com sucesso
        """
        connection_strings = [
            ("env", os.getenv("DB_CONNECTION_STRING")),
            ("fallback18", "DRIVER={ODBC Driver 18 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"),
            ("fallback17", "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;")
        ]
        
        for variant, conn_string in connection_strings:
            if not conn_string:
                continue
                
            start_time = datetime.now()
            
            try:
                logger.info(f"Tentando conexão SQL - variant: {variant}")
                self._connection = pyodbc.connect(conn_string)
                
                # Teste de latência
                cursor = self._connection.cursor()
                cursor.execute("SELECT 1 as test")
                cursor.fetchone()
                cursor.close()
                
                end_time = datetime.now()
                self.latency_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # Extrair driver da string de conexão
                driver_start = conn_string.find("{") + 1
                driver_end = conn_string.find("}")
                self.last_driver = conn_string[driver_start:driver_end] if driver_start > 0 and driver_end > driver_start else "Unknown"
                
                self.last_variant = variant
                self.last_error = None
                
                logger.info(f"Conexão SQL estabelecida - variant: {variant}, driver: {self.last_driver}, latency: {self.latency_ms}ms")
                return True
                
            except Exception as e:
                error_info = {
                    "type": type(e).__name__,
                    "message": str(e)[:100]  # Limitar tamanho da mensagem
                }
                self.last_error = error_info
                self.last_variant = variant
                
                logger.warning(f"Falha conexão SQL - variant: {variant}, erro: {error_info['type']}: {error_info['message']}")
                
                if self._connection:
                    try:
                        self._connection.close()
                    except:
                        pass
                    self._connection = None
        
        logger.error("Todas as tentativas de conexão SQL falharam")
        return False
    
    def disconnect(self):
        """Fecha conexão com banco"""
        if self._connection:
            try:
                self._connection.close()
                logger.info("Conexão com SQL Server fechada")
            except Exception as e:
                logger.error(f"Erro ao fechar conexão: {str(e)}")
            finally:
                self._connection = None
    
    def execute_query(self, query: str, params: tuple = ()) -> Optional[List[Dict[str, Any]]]:
        """
        Executa query SELECT e retorna resultados
        
        Args:
            query: SQL query
            params: Parâmetros da query
            
        Returns:
            Lista de dicionários com os resultados ou None se erro
        """
        if not self._connection:
            if not self.connect():
                return None
        
        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params)
            
            # Obter nomes das colunas
            columns = [column[0] for column in cursor.description]
            
            # Converter resultados para lista de dicionários
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            logger.debug(f"Query executada com sucesso. {len(results)} registros retornados")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao executar query: {str(e)}")
            return None
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão com banco e mede latência
        
        Returns:
            Dict com status da conexão e latência detalhada
        """
        try:
            if not self._connection:
                connected = self.connect()
            else:
                # Verificar se conexão ainda está ativa
                try:
                    cursor = self._connection.cursor()
                    cursor.execute("SELECT 1 as test")
                    cursor.fetchone()
                    cursor.close()
                    connected = True
                except:
                    # Reconectar se conexão perdida
                    connected = self.connect()
            
            if connected:
                return {
                    "sql_connected": True,
                    "checked_at": datetime.now().isoformat(),
                    "latency_ms": self.latency_ms,
                    "driver_used": self.last_driver,
                    "conn_variant": self.last_variant
                }
            else:
                return {
                    "sql_connected": False,
                    "checked_at": datetime.now().isoformat(),
                    "latency_ms": None,
                    "driver_used": None,
                    "conn_variant": self.last_variant,
                    "error": self.last_error
                }
                
        except Exception as e:
            error_info = {
                "type": type(e).__name__,
                "message": str(e)[:100]
            }
            return {
                "sql_connected": False,
                "checked_at": datetime.now().isoformat(),
                "latency_ms": None,
                "driver_used": None,
                "conn_variant": None,
                "error": error_info
            }

# Instância global da conexão
db = DatabaseConnection()

def get_available_drivers() -> Dict[str, List[str]]:
    """
    Retorna lista de drivers ODBC disponíveis
    """
    try:
        drivers = pyodbc.drivers()
        return {"drivers": list(drivers)}
    except Exception as e:
        logger.error(f"Erro ao listar drivers ODBC: {str(e)}")
        return {"drivers": [], "error": str(e)}
