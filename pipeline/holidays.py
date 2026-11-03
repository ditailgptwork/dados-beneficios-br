"""Feriados bancários nacionais do Brasil (calculados) e dias sem pagamento.

Regra de cálculo: feriados fixos nacionais + Carnaval (seg/ter), Sexta-feira da Paixão e
Corpus Christi a partir da Páscoa. 20/11 é nacional desde 2024 (Lei 14.759/2023).
Calendários de pagamento oficiais também pulam 24/12 e 31/12 (sem expediente ao público).
Conferência anual: ANBIMA feriados_nacionais.xls (https://www.anbima.com.br/feriados/).
"""
from datetime import date, timedelta
from functools import lru_cache

FIXOS = [
    (1, 1, "Confraternização Universal"),
    (4, 21, "Tiradentes"),
    (5, 1, "Dia do Trabalho"),
    (9, 7, "Independência do Brasil"),
    (10, 12, "Nossa Senhora Aparecida"),
    (11, 2, "Finados"),
    (11, 15, "Proclamação da República"),
    (11, 20, "Dia Nacional de Zumbi e da Consciência Negra"),
    (12, 25, "Natal"),
]
SEM_PAGAMENTO = [(12, 24, "Véspera de Natal (sem pagamento)"), (12, 31, "Fim de ano (sem expediente ao público)")]


def pascoa(ano: int) -> date:
    a = ano % 19; b = ano // 100; c = ano % 100; d = b // 4; e = b % 4
    f = (b + 8) // 25; g = (b - f + 1) // 3; h = (19 * a + b - d - g + 15) % 30
    i = c // 4; k = c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(ano, mes, dia)


@lru_cache(maxsize=None)
def feriados(ano: int) -> dict:
    p = pascoa(ano)
    out = {date(ano, m, d): n for m, d, n in FIXOS if not (m == 11 and d == 20 and ano < 2024)}
    out[p - timedelta(days=48)] = "Carnaval (segunda-feira)"
    out[p - timedelta(days=47)] = "Carnaval (terça-feira)"
    out[p - timedelta(days=2)] = "Sexta-feira da Paixão"
    out[p + timedelta(days=60)] = "Corpus Christi"
    return dict(sorted(out.items()))


@lru_cache(maxsize=None)
def sem_pagamento(ano: int) -> dict:
    out = dict(feriados(ano))
    for m, d, n in SEM_PAGAMENTO:
        out.setdefault(date(ano, m, d), n)
    return dict(sorted(out.items()))


def dia_util(d: date) -> bool:
    return d.weekday() < 5 and d not in feriados(d.year)


def dia_de_pagamento(d: date) -> bool:
    return d.weekday() < 5 and d not in sem_pagamento(d.year)


def dias_de_pagamento(ano: int, mes: int) -> list:
    d = date(ano, mes, 1)
    out = []
    while d.month == mes:
        if dia_de_pagamento(d):
            out.append(d)
        d += timedelta(days=1)
    return out
