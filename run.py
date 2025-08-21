#!/usr/bin/env python3
"""
ServiceDesk Automations - Main Entry Point
Author: wfrancischini
Version: 1.0.0
"""

import os
import sys
from app.app import app

def main():
    """Main entry point for the ServiceDesk automation application."""
    try:
        # Get configuration
        host = os.getenv('FLASK_HOST', '127.0.0.1')
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                ServiceDesk Automations v1.0                 ║
║                 Fase 1: Foundation & Core Logic             ║
╠══════════════════════════════════════════════════════════════╣
║  🌐 URL: http://{host}:{port}                          ║
║  🐍 Python: {sys.version.split()[0]}                                    ║
║  🔧 Debug: {'ON' if debug else 'OFF'}                                           ║
║  📁 Working Dir: {os.getcwd()[:40]}{'...' if len(os.getcwd()) > 40 else ''}
║                                                              ║
║  Recursos Disponíveis:                                      ║
║  • Status SQL Server                                        ║
║  • Busca de WorkOrders                                      ║
║  • Automação Selenium                                       ║
║  • Cache com TTL                                            ║
║  • Interface Web Moderna                                    ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Start the application
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicação interrompida pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erro fatal ao iniciar aplicação: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
