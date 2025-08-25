"""
Serviço para gerenciar exclusões de dias da capacidade técnica.
Armazena exclusões em arquivo JSON local.
"""
import json
import os
import uuid
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from app.services.period_service import get_current_26_25_period

class ExclusionService:
    def __init__(self):
        self.exclusions_file = os.path.join("data", "exclusions.json")
        self._ensure_data_dir()
        self._ensure_file_exists()
    
    def _ensure_data_dir(self):
        """Cria o diretório data se não existir"""
        os.makedirs("data", exist_ok=True)
    
    def _ensure_file_exists(self):
        """Cria o arquivo de exclusões se não existir"""
        if not os.path.exists(self.exclusions_file):
            self._save_data({"exclusions": []})
    
    def _load_data(self) -> Dict[str, Any]:
        """Carrega dados do arquivo JSON"""
        try:
            with open(self.exclusions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"exclusions": []}
    
    def _save_data(self, data: Dict[str, Any]):
        """Salva dados no arquivo JSON"""
        with open(self.exclusions_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    
    def add_exclusion(self, exclusion_date: date, reason: str, hours: float, 
                     reference_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Adiciona uma nova exclusão.
        
        Args:
            exclusion_date: Data da exclusão
            reason: Motivo da exclusão ('banco-horas', 'atestado', 'feriado', 'folga')
            hours: Quantidade de horas a excluir (0.5 a 8.0)
            reference_date: Data de referência para determinar o período
        
        Returns:
            Dict com os dados da exclusão criada
            
        Raises:
            ValueError: Se a data não estiver no período vigente ou dados inválidos
        """
        # Validações
        if hours < 0.5 or hours > 8.0:
            raise ValueError("Horas devem estar entre 0.5 e 8.0")
        
        valid_reasons = ['banco-horas', 'atestado', 'feriado', 'folga']
        if reason not in valid_reasons:
            raise ValueError(f"Motivo deve ser um de: {valid_reasons}")
        
        # Verifica se a data está no período vigente
        period_start, period_end = get_current_26_25_period(reference_date)
        if not (period_start <= exclusion_date <= period_end):
            raise ValueError(f"Data deve estar no período vigente: {period_start} a {period_end}")
        
        # Verifica se já existe exclusão para esta data
        data = self._load_data()
        for exclusion in data["exclusions"]:
            if exclusion["date"] == exclusion_date.isoformat():
                raise ValueError(f"Já existe uma exclusão para a data {exclusion_date}")
        
        # Cria a exclusão
        new_exclusion = {
            "id": str(uuid.uuid4()),
            "date": exclusion_date.isoformat(),
            "reason": reason,
            "hours": hours,
            "created_at": datetime.now().isoformat(),
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat()
        }
        
        data["exclusions"].append(new_exclusion)
        self._save_data(data)
        
        return new_exclusion
    
    def get_exclusions_for_period(self, reference_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Retorna todas as exclusões do período vigente.
        
        Args:
            reference_date: Data de referência para determinar o período
            
        Returns:
            Lista de exclusões do período atual
        """
        period_start, period_end = get_current_26_25_period(reference_date)
        data = self._load_data()
        
        period_exclusions = []
        for exclusion in data["exclusions"]:
            exclusion_date = date.fromisoformat(exclusion["date"])
            if period_start <= exclusion_date <= period_end:
                period_exclusions.append(exclusion)
        
        # Ordena por data
        period_exclusions.sort(key=lambda x: x["date"])
        return period_exclusions
    
    def get_exclusions_for_date(self, target_date: date) -> List[Dict[str, Any]]:
        """
        Retorna todas as exclusões de uma data específica.
        
        Args:
            target_date: Data específica para buscar exclusões
            
        Returns:
            Lista de exclusões da data especificada
        """
        data = self._load_data()
        target_date_str = target_date.isoformat()
        
        date_exclusions = []
        for exclusion in data["exclusions"]:
            if exclusion["date"] == target_date_str:
                date_exclusions.append(exclusion)
        
        return date_exclusions
    
    def update_exclusion(self, exclusion_id: str, exclusion_date: date, 
                        reason: str, hours: float) -> Dict[str, Any]:
        """
        Atualiza uma exclusão existente.
        
        Args:
            exclusion_id: ID da exclusão
            exclusion_date: Nova data da exclusão
            reason: Novo motivo
            hours: Nova quantidade de horas
            
        Returns:
            Dict com os dados da exclusão atualizada
            
        Raises:
            ValueError: Se a exclusão não for encontrada ou dados inválidos
        """
        data = self._load_data()
        
        # Encontra a exclusão
        exclusion_index = None
        for i, exclusion in enumerate(data["exclusions"]):
            if exclusion["id"] == exclusion_id:
                exclusion_index = i
                break
        
        if exclusion_index is None:
            raise ValueError("Exclusão não encontrada")
        
        # Validações (similares ao add_exclusion)
        if hours < 0.5 or hours > 8.0:
            raise ValueError("Horas devem estar entre 0.5 e 8.0")
        
        valid_reasons = ['banco-horas', 'atestado', 'feriado', 'folga']
        if reason not in valid_reasons:
            raise ValueError(f"Motivo deve ser um de: {valid_reasons}")
        
        # Atualiza a exclusão
        exclusion = data["exclusions"][exclusion_index]
        exclusion["date"] = exclusion_date.isoformat()
        exclusion["reason"] = reason
        exclusion["hours"] = hours
        exclusion["updated_at"] = datetime.now().isoformat()
        
        self._save_data(data)
        return exclusion
    
    def delete_exclusion(self, exclusion_id: str) -> bool:
        """
        Remove uma exclusão.
        
        Args:
            exclusion_id: ID da exclusão
            
        Returns:
            True se removida com sucesso
            
        Raises:
            ValueError: Se a exclusão não for encontrada
        """
        data = self._load_data()
        
        original_count = len(data["exclusions"])
        data["exclusions"] = [e for e in data["exclusions"] if e["id"] != exclusion_id]
        
        if len(data["exclusions"]) == original_count:
            raise ValueError("Exclusão não encontrada")
        
        self._save_data(data)
        return True
    
    def get_exclusion_summary(self, reference_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Retorna resumo das exclusões do período vigente.
        
        Args:
            reference_date: Data de referência
            
        Returns:
            Dict com estatísticas das exclusões
        """
        exclusions = self.get_exclusions_for_period(reference_date)
        
        total_exclusions = len(exclusions)
        total_hours = sum(e["hours"] for e in exclusions)
        total_days = total_hours / 8.0  # Assumindo 8h por dia
        
        # Agrupamento por motivo
        by_reason = {}
        for exclusion in exclusions:
            reason = exclusion["reason"]
            if reason not in by_reason:
                by_reason[reason] = {"count": 0, "hours": 0}
            by_reason[reason]["count"] += 1
            by_reason[reason]["hours"] += exclusion["hours"]
        
        # Adiciona cálculo de dias para cada motivo
        for reason_data in by_reason.values():
            reason_data["days"] = reason_data["hours"] / 8.0
        
        return {
            "total_exclusions": total_exclusions,
            "total_hours": total_hours,
            "total_days": total_days,
            "by_reason": by_reason
        }
