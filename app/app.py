#!/usr/bin/env python3
"""
ServiceDesk Automations - Flask Application
Fase 1: Foundation & Core Logic
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify
from werkzeug.exceptions import HTTPException

# Configuração de caminhos e diretórios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(LOGS_DIR, exist_ok=True)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "app.log")),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'servicedesk-automation-key-2025'

# Configurações fixas
app.config.update({
    'WORKORDER_TITLE': "CSI EAST - Datacenter - Execução de Tarefas",
    'OWNER_ID': 2007,
    'CACHE_TTL_MINUTES': 15,
    'SELENIUM_TIMEOUT_MINUTES': 5,
    'TIMEZONE': "America/Campo_Grande"
})

# Importar routes
from app.routes.status import status_bp
from app.routes.workorders import workorders_bp
from app.routes.automation import automation_bp
from app.routes.capacity_demo import capacity_demo_bp  # novo blueprint

# Registrar blueprints
app.register_blueprint(status_bp, url_prefix='/status')
app.register_blueprint(workorders_bp, url_prefix='/workorders')
app.register_blueprint(automation_bp, url_prefix='/automation')
app.register_blueprint(capacity_demo_bp, url_prefix='/capacity')  # rota demo

@app.route('/')
def index():
    """Página inicial da aplicação"""
    return render_template('index.html')

@app.errorhandler(HTTPException)
def handle_exception(e):
    """Handler para exceções HTTP"""
    return jsonify({
        "error": e.name,
        "description": e.description,
        "code": e.code
    }), e.code

@app.errorhandler(Exception)
def handle_generic_exception(e):
    """Handler para exceções genéricas"""
    app.logger.error(f"Erro não tratado: {str(e)}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "description": "Ocorreu um erro interno no servidor",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
