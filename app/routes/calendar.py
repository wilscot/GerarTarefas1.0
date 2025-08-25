"""
Rotas para funcionalidades do calendário de produtividade.
"""
from flask import Blueprint, jsonify, request
from datetime import datetime, date
import logging
from app.services.calendar_service import CalendarService
from app.services.calendar_cache_service import calendar_cache_service

logger = logging.getLogger(__name__)

calendar_bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@calendar_bp.route('/data', methods=['GET'])
def get_calendar_data():
    """
    Retorna dados completos do calendário para o período vigente.
    
    Query params opcionais:
    - reference_date: Data de referência no formato YYYY-MM-DD
    - force_refresh: Força atualização dos dados (true/false)
    """
    try:
        # Parse da data de referência se fornecida
        reference_date = None
        ref_date_str = request.args.get('reference_date')
        if ref_date_str:
            try:
                reference_date = datetime.strptime(ref_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de data inválido. Use YYYY-MM-DD.'
                }), 400
        
        # Verifica se deve forçar refresh
        force_refresh = request.args.get('force_refresh', '').lower() == 'true'
        
        # Usa cache-first approach
        try:
            data = calendar_cache_service.get_calendar_data(force_refresh=force_refresh)
            
            return jsonify({
                'success': True,
                'data': data,
                'cached': True,
                'cache_status': calendar_cache_service.get_cache_status()
            })
            
        except Exception as cache_error:
            logger.warning(f"Erro no cache, fallback para serviço: {cache_error}")
            
            # Fallback para serviço original
            calendar_service = CalendarService()
            data = calendar_service.get_calendar_data(reference_date)
            
            return jsonify({
                'success': True,
                'data': data,
                'cached': False,
                'fallback': True
            })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados do calendário: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@calendar_bp.route('/day/<date_str>', methods=['GET'])
def get_day_details(date_str):
    """
    Retorna detalhes completos de um dia específico.
    
    Params:
    - date_str: Data no formato YYYY-MM-DD
    """
    try:
        # Parse da data
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Formato de data inválido. Use YYYY-MM-DD.'
            }), 400
        
        calendar_service = CalendarService()
        data = calendar_service.get_day_details(target_date)
        
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes do dia {date_str}: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500

@calendar_bp.route('/cache/status', methods=['GET'])
def get_cache_status():
    """Retorna status do cache do calendário"""
    try:
        status = calendar_cache_service.get_cache_status()
        return jsonify({
            'success': True,
            'cache_status': status
        })
    except Exception as e:
        logger.error(f"Erro ao obter status do cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@calendar_bp.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """Invalida cache do calendário"""
    try:
        calendar_cache_service.invalidate_calendar_cache()
        return jsonify({
            'success': True,
            'message': 'Cache invalidado com sucesso'
        })
    except Exception as e:
        logger.error(f"Erro ao invalidar cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@calendar_bp.route('/summary', methods=['GET'])
def get_calendar_summary():
    """
    Retorna apenas o resumo estatístico do período vigente.
    """
    try:
        calendar_service = CalendarService()
        data = calendar_service.get_calendar_data()
        
        return jsonify({
            'success': True,
            'summary': data['summary'],
            'period': {
                'start': data['period_start'],
                'end': data['period_end'],
                'reference_date': data['reference_date']
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar resumo do calendário: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        }), 500
