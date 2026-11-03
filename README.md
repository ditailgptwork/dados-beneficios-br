# Calendário de benefícios — dados abertos

Datas de pagamento do Bolsa Família, INSS, Gás do Povo, Abono Salarial e FGTS em JSON, com fonte oficial e situação de cada data.
**Não somos o governo.** Confira sempre no app oficial (Bolsa Família, Meu INSS, Caixa Tem, FGTS).

- Dados: `docs/v1/all.json` (tudo) e `docs/v1/*.json` (por programa); versão em `docs/v1/meta.json`.
- Situação: `verificado` = conferido com anúncio oficial · `previsao` = calculado pela regra publicada · `noticiado` = imprensa, falta confirmação oficial · `confirmar` = anúncio diverge da regra, em revisão · `incerto` = mês com antecipação habitual (dezembro).
- Como funciona: `pipeline/rules.py` calcula pelas regras; `pipeline/collect.py` lê anúncios do MDS e da Previdência; `pipeline/build.py` só publica data nova quando bate com a regra ou com uma exceção registrada em `data/overrides.json`. Divergência vira aviso (issue), não dado.
- Licença dos dados: informação pública; cite a fonte oficial de cada item.
