"""
WorkOrders routes
Endpoints para gerenciamento de chamados
"""

from flask import Blueprint, jsonify, request
from app.services.workorder_service import WorkOrderService
from app.services.cache_service import CacheService

workorders_bp = Blueprint('workorders', __name__)

@workorders_bp.route('/current', methods=['GET'])
def get_current_workorder():
    """
    Obtém chamado vigente (cache first, fallback SQL)
    
    Returns:
        JSON com dados do chamado atual
    """
    try:
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        workorder = None
        
        # Se não forçou refresh, tenta cache primeiro
        if not force_refresh:
            workorder = CacheService.get_current_workorder()
        
        # Se não achou no cache, busca no SQL
        if not workorder:
            workorder = WorkOrderService.get_current_workorder()
            
            if workorder:
                # Salva no cache para próximas consultas
                CacheService.set_current_workorder(workorder)
                workorder.source = "sql"
            else:
                return jsonify({
                    "error": "Nenhum chamado vigente encontrado",
                    "workorder_id": None
                }), 404
        
        return jsonify(workorder.to_dict()), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao buscar chamado vigente: {str(e)}",
            "workorder_id": None
        }), 500

@workorders_bp.route('/cache/invalidate', methods=['POST'])
def invalidate_cache():
    """
    Invalida cache do chamado atual
    
    Returns:
        JSON com status da operação
    """
    try:
        success = CacheService.invalidate_current_workorder()
        
        return jsonify({
            "cache_invalidated": success,
            "timestamp": CacheService.cache.get_cache_info()
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Erro ao invalidar cache: {str(e)}",
            "cache_invalidated": False
        }), 500

@workorders_bp.route('/clear-cache', methods=['POST'])
def clear_cache():
    """
    Limpa o cache do chamado vigente
    """
    try:
        success = CacheService.invalidate_current_workorder()
        return jsonify({"success": success, "message": "Cache limpo"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@workorders_bp.route('/<int:workorder_id>', methods=['GET'])
def get_workorder_by_id(workorder_id: int):
    """
    Obtém chamado por ID específico
    
    Args:
        workorder_id: ID do chamado
        
    Returns:
        JSON com dados do chamado
    """
    try:
        workorder = WorkOrderService.get_workorder_by_id(workorder_id)
        
        if workorder:
            return jsonify(workorder.to_dict()), 200
        else:
            return jsonify({
                "error": f"Chamado {workorder_id} não encontrado",
                "workorder_id": workorder_id
            }), 404
            
    except Exception as e:
        return jsonify({
            "error": f"Erro ao buscar chamado {workorder_id}: {str(e)}",
            "workorder_id": workorder_id
        }), 500
