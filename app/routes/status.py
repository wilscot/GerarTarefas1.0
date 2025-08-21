"""
Status routes
Endpoints para verificação de status da aplicação
"""

from flask import Blueprint, jsonify
from app.models.database import db, get_available_drivers

status_bp = Blueprint('status', __name__)

@status_bp.route('/sql', methods=['GET'])
def test_sql_connection():
    """
    Testa conexão com SQL Server e mede latência
    
    Returns:
        JSON com status detalhado da conexão
    """
    try:
        connection_status = db.test_connection()
        
        if connection_status.get("sql_connected"):
            return jsonify(connection_status), 200
        else:
            return jsonify(connection_status), 503
            
    except Exception as e:
        return jsonify({
            "sql_connected": False,
            "checked_at": None,
            "latency_ms": None,
            "driver_used": None,
            "conn_variant": None,
            "error": {
                "type": type(e).__name__,
                "message": str(e)[:100]
            }
        }), 500

@status_bp.route('/sql/drivers', methods=['GET'])
def list_sql_drivers():
    """
    Lista drivers ODBC disponíveis no sistema
    
    Returns:
        JSON com lista de drivers
    """
    try:
        drivers_info = get_available_drivers()
        return jsonify(drivers_info), 200
        
    except Exception as e:
        return jsonify({
            "drivers": [],
            "error": {
                "type": type(e).__name__,
                "message": str(e)[:100]
            }
        }), 500
