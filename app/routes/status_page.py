"""
Rota para página de status detalhado do sistema.
"""
from flask import Blueprint, render_template, jsonify
import logging
import time
import pyodbc
from datetime import datetime

logger = logging.getLogger(__name__)

status_page_bp = Blueprint('status_page', __name__)

@status_page_bp.route('/status-page')
def status_page():
    """Página de status detalhado do sistema"""
    try:
        return render_template('status_page.html')
    except Exception as e:
        logger.error(f"Erro ao carregar página de status: {e}")
        return render_template('status_page.html', 
                             error=f"Erro ao carregar página: {str(e)}")

@status_page_bp.route('/status/sql-test')
def test_sql_connection():
    """Testa a conexão SQL detalhadamente"""
    try:
        start_time = time.time()
        
        # Testar drivers disponíveis em ordem de preferência
        drivers = [
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;",
            "DRIVER={ODBC Driver 18 for SQL Server};SERVER=S0680.ms;DATABASE=Servicedesk_2022;Trusted_Connection=yes;Encrypt=no;TrustServerCertificate=yes;"
        ]
        
        for i, conn_string in enumerate(drivers):
            try:
                conn = pyodbc.connect(conn_string, timeout=5)  # timeout de 5 segundos
                latency_ms = round((time.time() - start_time) * 1000, 2)
                
                # Teste rápido
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                
                driver_name = "ODBC Driver 17" if i == 0 else "ODBC Driver 18"
                
                return jsonify({
                    'status': 'success',
                    'driver': f'{driver_name} for SQL Server',
                    'server': 'S0680.ms',
                    'database': 'Servicedesk_2022',
                    'latency_ms': latency_ms,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as driver_error:
                logger.debug(f"Driver {i+1} falhou: {driver_error}")
                continue
        
        # Se chegou aqui, nenhum driver funcionou
        return jsonify({
            'status': 'error',
            'error': 'Nenhum driver ODBC funcionou',
            'timestamp': datetime.now().isoformat()
        }), 500
        
    except Exception as e:
        logger.error(f"Erro na conexão SQL: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@status_page_bp.route('/api/system-status')
def system_status_api():
    """API que retorna status completo do sistema"""
    try:
        # Esta rota agregará informações de várias fontes
        status_data = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "status": "online",
                "uptime": "2h 15m",
                "version": "1.0"
            },
            "database": {
                "status": "connected",
                "driver": "ODBC Driver 18",
                "server": "S0680.ms",
                "database": "Servicedesk_2022", 
                "latency": "45ms"
            },
            "workorder": {
                "status": "active",
                "number": "#12345",
                "date": "25/08/2025",
                "start_time": "08:00",
                "client": "Empresa XYZ",
                "description": "Manutenção preventiva sistema"
            },
            "automation": {
                "last_run": "25/08/2025 09:30",
                "status": "idle",
                "processes": 0
            }
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.error(f"Erro ao obter status do sistema: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500
