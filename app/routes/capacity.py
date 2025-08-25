from flask import Blueprint, jsonify, request
from datetime import datetime, date
from app.services.period_service import compute_capacity_for_current_period

capacity_bp = Blueprint('capacity', __name__)

@capacity_bp.route('/api', methods=['GET'])
def capacity_api():
    """
    API: retorna o período 26->25 vigente, dias úteis e capacidade em horas.
    Agora inclui cálculo de capacidade líquida com exclusões.
    Aceita parâmetro opcional ?reference=YYYY-MM-DD para simular outra data.
    """
    ref_param = request.args.get('reference')
    ref_date: date | None = None
    if ref_param:
        try:
            ref_date = datetime.strptime(ref_param, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                "error": "Parâmetro 'reference' inválido. Use YYYY-MM-DD.",
                "example": "/capacity/api?reference=2025-08-22"
            }), 400

    data = compute_capacity_for_current_period(ref_date)
    # Formatação amigável adicional
    data["period_display"] = f"{datetime.fromisoformat(data['period_start']).strftime('%d/%m/%Y')} - {datetime.fromisoformat(data['period_end']).strftime('%d/%m/%Y')}"
    return jsonify(data)

# Mantém a rota /demo para compatibilidade com a homepage atual
@capacity_bp.route('/demo', methods=['GET'])
def capacity_demo():
    """Compatibilidade - redireciona para /api"""
    return capacity_api()
