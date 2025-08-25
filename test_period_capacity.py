#!/usr/bin/env python3
"""
Script para testar e demonstrar o cálculo do período 26->25 e capacidade técnica.
Exemplo de uso:
    python test_period_capacity.py
    python test_period_capacity.py 2025-07-15
    python test_period_capacity.py 2025-08-30
"""
import sys
from datetime import datetime, date
from app.services.period_service import (
    get_current_26_25_period,
    count_business_days,
    compute_capacity_for_current_period
)

def format_date(d: date) -> str:
    """Formata data em formato amigável."""
    return d.strftime("%d/%m/%Y")

def main():
    # Usar data passada como argumento ou data atual
    ref_date = None
    if len(sys.argv) > 1:
        try:
            ref_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
            print(f"Usando data de referência: {format_date(ref_date)}")
        except ValueError:
            print(f"Data inválida: {sys.argv[1]}. Use o formato YYYY-MM-DD.")
            sys.exit(1)
    else:
        ref_date = date.today()
        print(f"Usando data atual: {format_date(ref_date)}")

    # Calcular período 26->25
    start, end = get_current_26_25_period(ref_date)
    print(f"\nPeríodo 26->25: {format_date(start)} a {format_date(end)}")

    # Calcular dias úteis
    business_days = count_business_days(start, end)
    print(f"Dias úteis no período: {business_days} dias (seg-sex)")

    # Calcular capacidade
    capacity = business_days * 8
    print(f"Capacidade técnica: {capacity} horas (8h/dia)")

    # Detalhes completos
    print("\nDetalhes completos (via compute_capacity_for_current_period):")
    capacity_data = compute_capacity_for_current_period(ref_date)
    for key, value in capacity_data.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
