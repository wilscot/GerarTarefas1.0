"""
WorkOrder model
Modelo para trabalhar com chamados do ServiceDesk
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class WorkOrder:
    """Modelo de dados para WorkOrder"""
    
    workorder_id: int
    title: str
    owner_id: Optional[int] = None
    created_time: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cached: bool = False
    source: str = "sql"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte WorkOrder para dicionário"""
        return {
            "workorder_id": self.workorder_id,
            "title": self.title,
            "owner_id": self.owner_id,
            "created_time": self.created_time.isoformat() if self.created_time else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cached": self.cached,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkOrder':
        """Cria WorkOrder a partir de dicionário"""
        return cls(
            workorder_id=data["workorder_id"],
            title=data["title"],
            owner_id=data.get("owner_id"),
            created_time=datetime.fromisoformat(data["created_time"]) if data.get("created_time") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            cached=data.get("cached", False),
            source=data.get("source", "sql")
        )
    
    @classmethod
    def from_sql_result(cls, sql_row: Dict[str, Any]) -> 'WorkOrder':
        """Cria WorkOrder a partir do resultado SQL"""
        # Converter CREATEDTIME se for timestamp
        created_time = sql_row.get("CREATEDTIME")
        if created_time and isinstance(created_time, (int, float)):
            # Se for timestamp Unix, converter para datetime
            created_time = datetime.fromtimestamp(created_time / 1000 if created_time > 1e10 else created_time)
        elif created_time and not isinstance(created_time, datetime):
            # Se for string ou outro formato, tentar converter
            try:
                created_time = datetime.fromisoformat(str(created_time))
            except:
                created_time = datetime.now()
        
        return cls(
            workorder_id=sql_row["WORKORDERID"],
            title=sql_row["TITLE"],
            owner_id=sql_row.get("OWNERID"),
            created_time=created_time,
            updated_at=datetime.now(),
            cached=False,
            source="sql"
        )
