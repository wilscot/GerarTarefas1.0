"""
Rotas para gerenciar exclusões de capacidade técnica.
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import datetime, date
from app.services.exclusion_service import ExclusionService
from app.services.period_service import get_current_26_25_period
import logging

logger = logging.getLogger(__name__)

exclusions_bp = Blueprint('exclusions', __name__)
exclusion_service = ExclusionService()

@exclusions_bp.route('/exclusions')
def exclusions_page():
    """Página de gerenciamento de exclusões"""
    try:
        # Obter período vigente
        period_start, period_end = get_current_26_25_period()
        
        # Obter exclusões do período
        exclusions = exclusion_service.get_exclusions_for_period()
        
        # Obter resumo
        summary = exclusion_service.get_exclusion_summary()
        
        # Formatação das datas para o template
        period_display = f"{period_start.strftime('%d/%m/%Y')} - {period_end.strftime('%d/%m/%Y')}"
        
        # Formatação das exclusões para exibição
        formatted_exclusions = []
        for exclusion in exclusions:
            formatted_exclusions.append({
                **exclusion,
                "date_display": datetime.fromisoformat(exclusion["date"]).strftime('%d/%m/%Y'),
                "created_display": datetime.fromisoformat(exclusion["created_at"]).strftime('%d/%m/%Y %H:%M'),
                "reason_display": _get_reason_display(exclusion["reason"])
            })
        
        return render_template('exclusions.html', 
                             exclusions=formatted_exclusions,
                             summary=summary,
                             period_display=period_display,
                             period_start=period_start.isoformat(),
                             period_end=period_end.isoformat())
    
    except Exception as e:
        logger.error(f"Erro ao carregar página de exclusões: {e}")
        return render_template('exclusions.html', 
                             error=f"Erro ao carregar exclusões: {str(e)}")

@exclusions_bp.route('/api/exclusions', methods=['POST'])
def add_exclusion():
    """API para adicionar nova exclusão"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Validação dos campos obrigatórios
        required_fields = ['date', 'reason', 'hours']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo obrigatório: {field}"}), 400
        
        # Conversão da data
        try:
            exclusion_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400
        
        # Conversão das horas
        try:
            hours = float(data['hours'])
        except ValueError:
            return jsonify({"error": "Horas devem ser um número válido"}), 400
        
        # Adicionar exclusão
        exclusion = exclusion_service.add_exclusion(
            exclusion_date=exclusion_date,
            reason=data['reason'],
            hours=hours
        )
        
        return jsonify({
            "message": "Exclusão adicionada com sucesso",
            "exclusion": exclusion
        }), 201
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao adicionar exclusão: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@exclusions_bp.route('/api/exclusions/<exclusion_id>', methods=['PUT'])
def update_exclusion(exclusion_id):
    """API para atualizar exclusão existente"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400
        
        # Validação dos campos obrigatórios
        required_fields = ['date', 'reason', 'hours']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo obrigatório: {field}"}), 400
        
        # Conversão da data
        try:
            exclusion_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Formato de data inválido. Use YYYY-MM-DD"}), 400
        
        # Conversão das horas
        try:
            hours = float(data['hours'])
        except ValueError:
            return jsonify({"error": "Horas devem ser um número válido"}), 400
        
        # Atualizar exclusão
        exclusion = exclusion_service.update_exclusion(
            exclusion_id=exclusion_id,
            exclusion_date=exclusion_date,
            reason=data['reason'],
            hours=hours
        )
        
        return jsonify({
            "message": "Exclusão atualizada com sucesso",
            "exclusion": exclusion
        })
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erro ao atualizar exclusão: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@exclusions_bp.route('/api/exclusions/<exclusion_id>', methods=['DELETE'])
def delete_exclusion(exclusion_id):
    """API para remover exclusão"""
    try:
        exclusion_service.delete_exclusion(exclusion_id)
        return jsonify({"message": "Exclusão removida com sucesso"})
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Erro ao remover exclusão: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@exclusions_bp.route('/api/exclusions/summary')
def get_exclusion_summary():
    """API para obter resumo das exclusões"""
    try:
        summary = exclusion_service.get_exclusion_summary()
        return jsonify(summary)
    
    except Exception as e:
        logger.error(f"Erro ao obter resumo de exclusões: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

def _get_reason_display(reason: str) -> str:
    """Converte código do motivo para texto exibível"""
    reason_map = {
        'banco-horas': 'Banco de Horas',
        'atestado': 'Atestado',
        'feriado': 'Feriado',
        'folga': 'Folga'
    }
    return reason_map.get(reason, reason)
