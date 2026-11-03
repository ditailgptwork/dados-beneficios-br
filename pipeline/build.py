"""Junta regra + exceções oficiais + coleta -> docs/v1/*.json e docs/index.html.

Uso: python pipeline/build.py [--collect]
Princípio: se o anúncio oficial diverge da regra, NÃO publica a data nova sozinho;
marca o mês como "confirmar" e escreve issues.md para revisão humana.
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from holidays import feriados  # noqa: E402
from rules import bolsa, inss_ate_1sm, inss_acima_1sm, janela_inss, gas_liberacoes  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "v1"
MESES_PT = ["", "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
            "setembro", "outubro", "novembro", "dezembro"]


def carregar(nome):
    return json.loads((ROOT / "data" / nome).read_text(encoding="utf-8"))


def meses(inicio: dt.date, n: int):
    a, m = inicio.year, inicio.month
    for _ in range(n):
        yield a, m
        m += 1
        if m > 12:
            m, a = 1, a + 1


def construir(hoje: dt.date, coleta: dict):
    ov = carregar("overrides.json")
    avisos = list(coleta.get("erros", []))
    inicio = (hoje.replace(day=1) - dt.timedelta(days=1)).replace(day=1)  # mês anterior

    b_out = {}
    for a, m in meses(inicio, 15):
        k = f"{a}-{m:02d}"
        datas, status, fonte = bolsa(a, m), "previsao", "regra: últimos 10 dias úteis (MDS)"
        if m == 12:
            status = "incerto"  # dezembro costuma ser antecipado
        if k in ov.get("bolsa", {}):
            o = ov["bolsa"][k]
            datas, status, fonte = o["datas"], o["status"], o["fonte"]
        for c in [c for c in coleta.get("bolsa", []) if c["mes"] == k]:
            if all(datas.get(d) == v for d, v in c["datas"].items()):
                status, fonte = "verificado", c["fonte"]
            else:
                status = "confirmar"
                avisos.append(f"Bolsa {k}: anúncio {c['fonte']} diverge do publicado. Anúncio={c['datas']} Publicado={datas}")
        b_out[k] = {"datas": datas, "status": status, "fonte": fonte}

    i_out = {}
    for a, m in meses(inicio, 14):
        k = f"{a}-{m:02d}"
        ate, acima = inss_ate_1sm(a, m), inss_acima_1sm(a, m)
        status, fonte = "previsao", "regra INSS (5+5 dias úteis; acima de 1 SM 5 dias úteis)"
        if k in ov.get("inss", {}):
            o = ov["inss"][k]
            ate, acima, status, fonte = o["ate_1sm"], o["acima_1sm"], o["status"], o["fonte"]
        ini, fim = sorted(ate.values())[0], sorted(ate.values())[-1]
        for c in coleta.get("inss", []):
            if c["inicio"][:7] == ini[:7] and abs((dt.date.fromisoformat(c["inicio"]) - dt.date.fromisoformat(ini)).days) < 20:
                if (c["inicio"], c["fim"]) == (ini, fim):
                    status, fonte = "verificado", c["fonte"]
                else:
                    status = "confirmar"
                    avisos.append(f"INSS {k}: anúncio {c['fonte']} diz {c['inicio']}→{c['fim']}, regra diz {ini}→{fim}")
        i_out[k] = {"ate_1sm": ate, "acima_1sm": acima, "janela": [ini, fim], "status": status, "fonte": fonte}

    anos = [hoje.year, hoje.year + 1]
    fer = {str(a): [{"data": d.isoformat(), "nome": n} for d, n in feriados(a).items()] for a in anos}
    gas = {"regra": "vale liberado no dia 10 do mês do ciclo da família; 2-3 pessoas a cada 3 meses, 4 ou mais a cada 2 meses",
           "liberacoes": {str(a): gas_liberacoes(a) for a in anos},
           "fonte": "https://www.gov.br/mds/pt-br/noticias/gas-do-povo-familias-podem-consultar-a-situacao-do-vale-a-partir-desta-quinta-feira-10-09"}
    dados = {
        "bolsa": b_out, "inss": i_out, "feriados": fer, "gas": gas,
        "abono": carregar("abono.json"), "fgts": carregar("fgts.json"), "valores": carregar("valores.json"),
    }
    return dados, avisos


def html_pagina(dados, meta):
    def tabela_bolsa():
        linhas = []
        for k, v in list(dados["bolsa"].items())[:4]:
            a, m = map(int, k.split("-"))
            cel = "".join(f"<td>{v['datas'][d][8:]}/{v['datas'][d][5:7]}</td>" for d in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
            linhas.append(f"<tr><th>{MESES_PT[m]}/{a}</th>{cel}<td>{html.escape(v['status'])}</td></tr>")
        cab = "".join(f"<th>{d}</th>" for d in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
        return f"<table><tr><th>Mês</th>{cab}<th>Situação</th></tr>{''.join(linhas)}</table>"

    def tabela_inss():
        linhas = []
        for k, v in list(dados["inss"].items())[:4]:
            a, m = map(int, k.split("-"))
            cel = "".join(f"<td>{v['ate_1sm'][d][8:]}/{v['ate_1sm'][d][5:7]}</td>" for d in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
            linhas.append(f"<tr><th>{MESES_PT[m]}/{a}</th>{cel}<td>{html.escape(v['status'])}</td></tr>")
        cab = "".join(f"<th>{d}</th>" for d in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])
        return f"<table><tr><th>Competência</th>{cab}<th>Situação</th></tr>{''.join(linhas)}</table>"

    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Calendário de benefícios — dados abertos</title>
<meta name="description" content="Datas de pagamento do Bolsa Família, INSS, Gás do Povo, Abono e FGTS em dados abertos, com fonte oficial e situação de cada data.">
<style>body{{font-family:system-ui,sans-serif;max-width:860px;margin:auto;padding:16px;color:#1d1d1f;background:#fff}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:8px 0 24px}}th,td{{border:1px solid #ddd;padding:4px 6px;text-align:center}}
small{{color:#666}}</style></head><body>
<h1>Calendário de benefícios — dados abertos</h1>
<p><b>Não somos o governo.</b> Estas datas vêm de anúncios oficiais (MDS, INSS, Caixa) e de regras publicadas. Confira sempre no app oficial.
Situação: <i>verificado</i> = conferido com anúncio oficial; <i>previsao</i> = calculado pela regra; <i>confirmar</i> = anúncio diferente da regra, em revisão.</p>
<h2>Bolsa Família — dia por final do NIS</h2>{tabela_bolsa()}
<h2>INSS até 1 salário mínimo — dia por final do benefício</h2>{tabela_inss()}
<h2>Gás do Povo</h2><p>{html.escape(dados['gas']['regra'])}.</p>
<h2>Dados em JSON</h2><p><a href="v1/all.json">v1/all.json</a> · <a href="v1/meta.json">v1/meta.json</a></p>
<p><small>Atualizado em {meta['atualizado_em']} · versão {meta['versao']} · <a href="privacidade.html">Privacidade do app Benefício em Dia</a></small></p>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--hoje")
    args = ap.parse_args()
    hoje = dt.date.fromisoformat(args.hoje) if args.hoje else dt.date.today()
    coleta = {"bolsa": [], "inss": [], "erros": []}
    if args.collect:
        try:
            from collect import coletar
            coleta = coletar(hoje.year)
        except Exception as e:  # noqa: BLE001
            coleta["erros"].append(f"coleta: {e!r}")
    dados, avisos = construir(hoje, coleta)
    corpo = json.dumps(dados, ensure_ascii=False, sort_keys=True)
    versao = hashlib.sha256(corpo.encode()).hexdigest()[:12]
    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / "meta.json"
    antigo = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    if antigo.get("versao") != versao:
        meta = {"versao": versao, "atualizado_em": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "esquema": "beneficios/v1", "aviso": "Não somos o governo. Confira no app oficial."}
        (OUT / "all.json").write_text(json.dumps({"meta": meta, **dados}, ensure_ascii=False, indent=1), encoding="utf-8")
        for k in ["bolsa", "inss", "feriados", "gas", "abono", "fgts", "valores"]:
            (OUT / f"{k}.json").write_text(json.dumps(dados[k], ensure_ascii=False, indent=1), encoding="utf-8")
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
        (ROOT / "docs" / "index.html").write_text(html_pagina(dados, meta), encoding="utf-8")
        print("publicado", versao)
    else:
        pagina = html_pagina(dados, antigo)
        idx = ROOT / "docs" / "index.html"
        if not idx.exists() or idx.read_text(encoding="utf-8") != pagina:
            idx.write_text(pagina, encoding="utf-8")
            print("página refeita", versao)
        else:
            print("sem mudanças", versao)
    issues = ROOT / "issues.md"
    if avisos:
        issues.write_text("# Revisar dados\n\n" + "\n".join(f"- {a}" for a in avisos) + "\n", encoding="utf-8")
        print(f"{len(avisos)} aviso(s) -> issues.md")
    elif issues.exists():
        issues.unlink()


if __name__ == "__main__":
    main()
