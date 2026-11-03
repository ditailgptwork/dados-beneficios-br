"""Extrai datas de anúncios oficiais em português (texto já sem HTML)."""
import re
from datetime import date

MESES = {"janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
         "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}
_DIG = r"[0-9](?:\s*(?:,|e|a|ao)\s*[0-9])*"
RE_BOLSA = re.compile(r"NIS\s+(?:de\s+)?(?:final|finais)\s+(" + _DIG + r")\s*[:–\-]\s*(?:dia\s+)?(\d{1,2})\s+de\s+([a-zç]+)", re.I)
RE_JANELA = re.compile(r"vai de (\d{1,2}) de ([a-zç]+) (?:até|a) (\d{1,2}) de ([a-zç]+)", re.I)
RE_PUBLICADO = re.compile(r"Publicado em (\d{2})/(\d{2})/(\d{4})")
AUTH = "É necessário autenticar"


def expandir(spec: str) -> list:
    spec = spec.lower().replace(" ", "")
    out = []
    for parte in re.split(r",|e", spec):
        if not parte:
            continue
        m = re.fullmatch(r"(\d)(?:ao|a)(\d)", parte)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            seq = range(a, b + 1) if a <= b else list(range(a, 10)) + list(range(0, b + 1))
            out += [str(x) for x in seq]
        elif parte.isdigit():
            out.append(parte)
    return out


def ano_publicado(texto: str, padrao: int) -> int:
    m = RE_PUBLICADO.search(texto)
    return int(m.group(3)) if m else padrao


def parse_bolsa(texto: str, ano: int) -> dict:
    out = {}
    for spec, dia, mes in RE_BOLSA.findall(texto):
        n = MESES.get(mes.lower())
        if not n:
            continue
        d = date(ano, n, int(dia)).isoformat()
        for dig in expandir(spec):
            out[dig] = d
    return out


def parse_janela(texto: str, ano: int):
    m = RE_JANELA.search(texto)
    if not m:
        return None
    d1, m1, d2, m2 = int(m.group(1)), MESES.get(m.group(2).lower()), int(m.group(3)), MESES.get(m.group(4).lower())
    if not (m1 and m2):
        return None
    a2 = ano + 1 if m2 < m1 else ano
    return date(ano, m1, d1).isoformat(), date(a2, m2, d2).isoformat()
