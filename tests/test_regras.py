import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "pipeline"))
from datetime import date
from holidays import feriados, pascoa
from rules import bolsa, inss_ate_1sm, inss_acima_1sm, janela_inss, gas_proximos, fgts_janela, fgts_valor
from parse import parse_bolsa, parse_janela, expandir


def test_pascoa_e_feriados():
    assert pascoa(2026) == date(2026, 4, 5) and pascoa(2027) == date(2027, 3, 28)
    f = feriados(2027)
    for d in ["2027-02-08", "2027-02-09", "2027-03-26", "2027-05-27", "2027-11-20"]:
        assert date.fromisoformat(d) in f


def test_bolsa_bate_com_anuncios_2026():
    # anúncios MDS: jul 20, ago 18, set 17, out 19 (primeiro dia, NIS final 1)
    for m, d in [(7, 20), (8, 18), (9, 17), (10, 19)]:
        assert bolsa(2026, m)["1"] == f"2026-{m:02d}-{d:02d}"


def test_inss_maio_2026_bate_com_previdencia():
    assert janela_inss(2026, 5) == ("2026-05-25", "2026-06-08")


def test_inss_nov_dez_2026_bate_com_dados_v0():
    assert inss_ate_1sm(2026, 11) == {"1": "2026-11-24", "2": "2026-11-25", "3": "2026-11-26", "4": "2026-11-27", "5": "2026-11-30",
                                     "6": "2026-12-01", "7": "2026-12-02", "8": "2026-12-03", "9": "2026-12-04", "0": "2026-12-07"}
    assert inss_ate_1sm(2026, 12)["1"] == "2026-12-22" and inss_ate_1sm(2026, 12)["3"] == "2026-12-28"
    assert inss_ate_1sm(2026, 12)["0"] == "2027-01-08"
    assert inss_acima_1sm(2026, 12)["1"] == "2027-01-04" and inss_acima_1sm(2026, 12)["0"] == "2027-01-08"


def test_gas_e_fgts():
    assert gas_proximos("2026-09", 3, 2) == ["2026-12-10", "2027-03-10"]
    assert gas_proximos("2026-11", 4, 2) == ["2027-01-10", "2027-03-10"]
    assert fgts_janela(2026, 11) == ("2026-11-01", "2027-01-29")
    tabela = [[0, 500.0, 0.5, 0], [500.01, 1000.0, 0.4, 50], [1000.01, 5000.0, 0.3, 150]]
    assert fgts_valor(2000, tabela) == 750.0


def test_parse_anuncios():
    txt = "Calendário de pagamento de outubro NIS final 1: 19 de outubro NIS final 2: 20 de outubro NIS finais 3 a 9 e 0: 21 de outubro"
    r = parse_bolsa(txt, 2026)
    assert r["1"] == "2026-10-19" and r["2"] == "2026-10-20" and r["0"] == "2026-10-21" and r["7"] == "2026-10-21" and len(r) == 10
    assert parse_janela("O calendário de pagamentos vai de 25 de maio até 8 de junho.", 2026) == ("2026-05-25", "2026-06-08")
    assert parse_janela("vai de 22 de dezembro a 8 de janeiro", 2026) == ("2026-12-22", "2027-01-08")
    assert expandir("1 e 6") == ["1", "6"]
