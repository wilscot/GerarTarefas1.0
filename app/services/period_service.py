"""
Serviço simples para cálculo do período vigente 26->25 e capacidade técnica.
Não usa histórico, apenas datas atuais e dias úteis (seg-sex), 8h/dia.
"""
from datetime import date, timedelta
from typing import Tuple, Dict, Any

HOURS_PER_WORKDAY = 8


def get_current_26_25_period(today: date | None = None) -> Tuple[date, date]:
    """
    Retorna o período vigente fixo de 26 a 25 com base na data de referência.
    Ex.: se hoje é 22/08/2025 -> 26/07/2025 a 25/08/2025
    
    O período vai do dia 26 de um mês até o dia 25 do mês seguinte.
    """
    today = today or date.today()
    
    # Se estamos no dia 25 ou antes, o período termina neste mês (começa no mês anterior)
    if today.day <= 25:
        # Fim do período é o dia 25 do mês atual
        end = date(today.year, today.month, 25)
        
        # Início do período é o dia 26 do mês anterior
        if today.month == 1:  # Janeiro
            start = date(today.year - 1, 12, 26)  # 26 de dezembro do ano anterior
        else:
            start = date(today.year, today.month - 1, 26)
    # Se estamos no dia 26 ou depois, o período termina no próximo mês (começa no mês atual)
    else:
        # Início do período é o dia 26 do mês atual
        start = date(today.year, today.month, 26)
        
        # Fim do período é o dia 25 do próximo mês
        if today.month == 12:  # Dezembro
            end = date(today.year + 1, 1, 25)  # 25 de janeiro do próximo ano
        else:
            end = date(today.year, today.month + 1, 25)
            
    return start, end


def count_business_days(start: date, end: date) -> int:
    """
    Conta dias úteis (segunda a sexta) no intervalo inclusivo [start, end].
    """
    if end < start:
        return 0
    days = 0
    current = start
    one_day = timedelta(days=1)
    while current <= end:
        if current.weekday() < 5:  # 0=Seg ... 4=Sex
            days += 1
        current += one_day
    return days


def compute_capacity_for_current_period(today: date | None = None) -> Dict[str, Any]:
    """
    Calcula o período vigente, dias úteis e capacidade (horas úteis = dias * 8).
    Não considera feriados nem exclusões.
    """
    start, end = get_current_26_25_period(today)
    business_days = count_business_days(start, end)
    capacity_hours = business_days * HOURS_PER_WORKDAY
    ref = today or date.today()
    return {
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
        "business_days": business_days,
        "hours_per_day": HOURS_PER_WORKDAY,
        "capacity_hours": capacity_hours,
        "reference_date": ref.isoformat(),
        "note": "Período fixo 26->25, considera apenas seg-sex, 8h/dia, sem feriados."
    }
