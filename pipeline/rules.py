"""Calendários por regra (previsão). Cada função devolve datas ISO por dígito final.

Bolsa Família: últimos 10 dias úteis do mês, NIS final 1 -> 0 (MDS). Dezembro costuma ser antecipado.
INSS até 1 salário mínimo: 5 últimos dias úteis da competência (finais 1-5) + 5 primeiros do mês seguinte (6-0).
INSS acima de 1 salário mínimo: 5 primeiros dias úteis do mês seguinte (1 e 6, 2 e 7, 3 e 8, 4 e 9, 5 e 0).
Gás do Povo: vale liberado no dia 10 do mês do ciclo da família (2-3 pessoas: a cada 3 meses; 4+: a cada 2).
FGTS saque-aniversário: do 1º dia do mês de aniversário ao último dia útil do 2º mês seguinte.
"""
from datetime import date, timedelta
from holidays import dias_de_pagamento, dia_util

DIGITOS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
PARES_INSS = [("1", "6"), ("2", "7"), ("3", "8"), ("4", "9"), ("5", "0")]


def proximo_mes(ano: int, mes: int):
    return (ano + 1, 1) if mes == 12 else (ano, mes + 1)


def bolsa(ano: int, mes: int) -> dict:
    dias = dias_de_pagamento(ano, mes)[-10:]
    return {dig: dias[i].isoformat() for i, dig in enumerate(DIGITOS)}


def inss_ate_1sm(ano: int, mes: int) -> dict:
    a2, m2 = proximo_mes(ano, mes)
    dias = dias_de_pagamento(ano, mes)[-5:] + dias_de_pagamento(a2, m2)[:5]
    return {dig: dias[i].isoformat() for i, dig in enumerate(DIGITOS)}


def inss_acima_1sm(ano: int, mes: int) -> dict:
    a2, m2 = proximo_mes(ano, mes)
    dias = dias_de_pagamento(a2, m2)[:5]
    out = {}
    for i, (x, y) in enumerate(PARES_INSS):
        out[x] = out[y] = dias[i].isoformat()
    return {d: out[d] for d in DIGITOS}


def janela_inss(ano: int, mes: int):
    """Primeiro e último dia do calendário de uma competência (até 1 SM)."""
    datas = sorted(inss_ate_1sm(ano, mes).values())
    return datas[0], datas[-1]


def gas_liberacoes(ano: int) -> list:
    return [date(ano, m, 10).isoformat() for m in range(1, 13)]


def gas_proximos(ultimo_mes: str, pessoas: int, n: int = 3) -> list:
    passo = 3 if pessoas <= 3 else 2
    a, m = map(int, ultimo_mes.split("-"))
    out = []
    for _ in range(n):
        m += passo
        while m > 12:
            m -= 12
            a += 1
        out.append(date(a, m, 10).isoformat())
    return out


def fgts_janela(ano: int, mes_aniversario: int):
    ini = date(ano, mes_aniversario, 1)
    a, m = ano, mes_aniversario + 2
    if m > 12:
        m -= 12
        a += 1
    fim = date(a + (m == 12), (m % 12) + 1, 1) - timedelta(days=1)
    while not dia_util(fim):
        fim -= timedelta(days=1)
    return ini.isoformat(), fim.isoformat()


def fgts_valor(saldo: float, tabela: list) -> float:
    for de, ate, aliq, adicional in tabela:
        if saldo >= de and (ate is None or saldo <= ate):
            return round(saldo * aliq + adicional, 2)
    return 0.0
