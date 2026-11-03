"""Coleta anúncios oficiais (MDS e Previdência). Falhas viram aviso, nunca dado."""
import requests
from bs4 import BeautifulSoup
from parse import parse_bolsa, parse_janela, ano_publicado, AUTH

UA = {"User-Agent": "dados-beneficios-br/1.0 (dados abertos; contato no README)"}
FONTES = {
    "bolsa": ("https://www.gov.br/mds/pt-br/noticias", ["bolsa família"], ["pagament"]),
    "inss": ("https://www.gov.br/previdencia/pt-br/noticias", ["pagamento"], ["benefício", "aposentad", "13º"]),
}


def _get(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    if AUTH in r.text:
        raise RuntimeError("página pede autenticação (bloqueio de robô)")
    return r.text


def _links(url, chaves, precisa, limite=8):
    soup = BeautifulSoup(_get(url), "html.parser")
    out = []
    for a in soup.find_all("a", href=True):
        t = " ".join(a.get_text(" ").split()).lower()
        if t and all(k in t for k in chaves) and any(p in t for p in precisa):
            href = requests.compat.urljoin(url, a["href"])
            if href not in out:
                out.append(href)
    return out[:limite]


def _texto(url):
    soup = BeautifulSoup(_get(url), "html.parser")
    for s in soup(["script", "style", "nav", "header", "footer"]):
        s.decompose()
    return " ".join(soup.get_text(" ").split())


def coletar(ano_padrao: int) -> dict:
    res = {"bolsa": [], "inss": [], "erros": []}
    for prog, (lista, chaves, precisa) in FONTES.items():
        try:
            urls = _links(lista, chaves, precisa)
        except Exception as e:  # noqa: BLE001
            res["erros"].append(f"{prog}: lista {lista} falhou ({e})")
            continue
        for u in urls:
            try:
                txt = _texto(u)
            except Exception as e:  # noqa: BLE001
                res["erros"].append(f"{prog}: {u} falhou ({e})")
                continue
            ano = ano_publicado(txt, ano_padrao)
            if prog == "bolsa":
                datas = parse_bolsa(txt, ano)
                if datas:
                    mes = sorted(datas.values())[0][:7]
                    res["bolsa"].append({"mes": mes, "datas": datas, "fonte": u})
            else:
                jan = parse_janela(txt, ano)
                if jan:
                    res["inss"].append({"inicio": jan[0], "fim": jan[1], "fonte": u})
    return res
