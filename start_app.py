import sys
sys.path.append('.')  # Adiciona o diretório atual ao path

from app.app import app

if __name__ == '__main__':
    print("Starting app...")
    app.run(host='127.0.0.1', port=5000, debug=True)
