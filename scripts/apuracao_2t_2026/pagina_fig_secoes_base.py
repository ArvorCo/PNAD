"""Base do capítulo "Seção por seção" do dossiê do 2º turno: leitura, pesos e indicadores.

Tudo sai de ``secoes.json``, ``secoes_voto.json`` e ``secoes_ranking.json``
(``scripts/apuracao-2t-2026-secoes.py``). A mesma página serve às duas fontes do
script: ``amostra`` (seções sorteadas antes da votação, estimativa nacional
ponderada pelas seções de cada UF, com IC de 95%) e ``completo`` (o banco inteiro
de BUs, contagem do país sem amostragem). Nenhum número é digitado aqui.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import inteiro, num

from . import secoes_linhas

# Correspondência entre os indicadores da estimativa nacional e os agregados
# brutos da fonte, usada quando a estimativa não existe (banco completo).
_N = ("agregados", "brasil", "n")


def linhas(S: dict) -> list[dict]:
    """Tabela de seções como lista de dicionários."""
    bloco = secoes_linhas.bloco(S)
    cols = bloco["colunas"]
    return [dict(zip(cols, r, strict=False)) for r in bloco["linhas"]]


def eh_amostra(S: dict) -> bool:
    return S.get("fonte") == "amostra"


def pesos(S: dict, P: dict | None) -> dict[str, float]:
    """Peso por UF: seções da UF no país sobre seções sorteadas na UF.

    Só vale para a fonte ``amostra``; na fonte ``completo`` todo peso é 1. Sem o
    ``presidente.json`` não há total por UF e o peso também fica 1 (o texto avisa).
    """
    if not eh_amostra(S) or not P:
        return {}
    total = {u["uf"]: u.get("secoes_total") or u.get("secoes") for u in P["ufs"]}
    n: dict[str, int] = {}
    for x in linhas(S):
        if x.get("origem") == "amostra":
            n[x["uf"]] = n.get(x["uf"], 0) + 1
    return {uf: total[uf] / k for uf, k in n.items() if total.get(uf) and k}


def peso_linha(x: dict, w: dict[str, float]) -> float:
    """Peso da seção: zero para a paralela na amostra (não entra na estimativa)."""
    if not w:
        return 1.0
    if x.get("origem") != "amostra":
        return 0.0
    return w.get(x["uf"], 0.0)


def _get(S: dict, *chaves):
    atual = S
    for c in chaves:
        if not isinstance(atual, dict) or c not in atual:
            return None
        atual = atual[c]
    return atual


def _bruto(S: dict, chave: str) -> tuple[float | None, int | None]:
    """Parcela (%) e contagem brutas na fonte lida, para cada indicador."""
    b = _get(S, "agregados", "brasil") or {}
    n = b.get("n") or 0
    pr = _get(S, "prorrogacao", "brasil") or {}
    contagens = {
        "delta": _get(b, "sinais", "delta"),
        "delta_relativo": _get(b, "delta_comp", "n_relativo_5_mais"),
        "sinal_sem_bio": _get(b, "sinais", "sem_bio"),
        "sinal_ano_nasc": _get(b, "sinais", "ano_nasc"),
        "sinal_salto_bio": _get(b, "sinais", "salto_bio"),
        "pianista": _get(b, "salto_biometria", "n_comparecimento_e_salto"),
        "tardia": _get(b, "sinais", "tardia"),
        "contingencia": _get(b, "urna", "contingencia"),
        "escore2": b.get("escore_2_mais"),
        "apos_19h": _get(b, "encerramento", "n_apos_19h"),
    }
    parcelas = {
        "apos_1800": _get(b, "encerramento", "pct_apos_1800_2t"),
        "apos_19h": _get(b, "encerramento", "pct_apos_1900_2t"),
        "recebido_antes_1900": pr.get("pct_recebido_antes_1900"),
        "queda5": _get(b, "delta_comp", "pct_menos_5"),
        "media_delta_pp": _get(b, "delta_comp", "media"),
    }
    if chave in parcelas and parcelas[chave] is not None:
        c = contagens.get(chave)
        return parcelas[chave], c
    c = contagens.get(chave)
    if c is None or not n:
        return None, None
    return 100 * c / n, c


def indicador(S: dict, chave: str) -> dict:
    """{'pct', 'ic', 'secoes', 'estimado'} de um indicador nacional.

    Com a estimativa nacional disponível (amostra), devolve o valor ponderado e o
    IC de 95%; senão, a parcela bruta da fonte lida (banco completo), sem IC.
    """
    est = _get(S, "estimativa_nacional") or {}
    if est.get("disponivel"):
        for i in est.get("indicadores", []):
            if i.get("indicador") == chave:
                valor = i.get("pct", i.get("valor"))
                return {
                    "pct": valor,
                    "ic": i.get("ic95"),
                    "secoes": i.get("secoes_estimadas"),
                    "estimado": True,
                }
    pct, c = _bruto(S, chave)
    return {"pct": pct, "ic": None, "secoes": c, "estimado": False}


def fmt_ind(S: dict, chave: str, casas: int = 2, unidade: str = "%") -> str:
    """'0,72% (IC de 95%: 0,31 a 1,13)' ou '0,32%' sem IC."""
    i = indicador(S, chave)
    if i["pct"] is None:
        return "s/d"
    base = f"{num(i['pct'], casas)}{unidade}"
    if i["ic"]:
        lo, hi = i["ic"]
        base += f" (IC de 95%: {num(lo, casas)} a {num(hi, casas)})"
    return base


def secoes_pais(S: dict, chave: str) -> str:
    """'cerca de 44.469 seções' (estimado) ou '413 seções' (contadas)."""
    i = indicador(S, chave)
    if i["secoes"] is None:
        return ""
    pre = "cerca de " if i["estimado"] else ""
    return f"{pre}{inteiro(i['secoes'])} seções"


def descricao_fonte(S: dict) -> str:
    """Frase que diz na tela qual base o capítulo está lendo."""
    tot = S.get("totais") or {}
    universo = S.get("n_universo_1t")
    cob = S.get("cobertura_completo_pct")
    nbus = S.get("n_bus_completo")
    lido = S.get("max_recebido_hhmm")
    if eh_amostra(S):
        est = _get(S, "estimativa_nacional") or {}
        return (
            f"<b>Base desta versão: amostra.</b> {inteiro(tot.get('amostra'))} seções sorteadas antes da "
            "votação (semente fixa, 150 por UF e mais 600 em cada uma das seis UFs com governador), "
            f"mais {inteiro(tot.get('paralela'))} seções da totalização paralela, que entram nas tabelas e "
            f"não nas estimativas. O país sai da média das {inteiro(est.get('ufs'))} UFs ponderada pelas "
            f"{inteiro(universo)} seções do 1º turno, com intervalo de confiança de 95%. Na leitura, o "
            f"banco completo tinha {inteiro(nbus)} BUs ({num(cob, 1)}% das seções); último recebimento "
            f"lido às {lido}. Quando a coleta terminar, o mesmo script regrava estes números sobre o banco inteiro."
        )
    if S.get("fonte") == "completo":
        return (
            f"<b>Base desta versão: banco completo.</b> {inteiro(tot.get('secoes'))} seções com BU, "
            f"{num(cob, 1)}% das {inteiro(universo)} seções do 1º turno; último recebimento lido às "
            f"{lido}. As contagens são do país, sem amostragem e sem intervalo de confiança."
        )
    return (
        f"<b>Base desta versão: {S.get('fonte')}.</b> {inteiro(tot.get('secoes'))} seções com BU; "
        f"último recebimento lido às {lido}."
    )


def hhmm(minutos: float | None) -> str:
    """Minutos depois das 17:00 viram 'HH:MM' de Brasília."""
    if minutos is None:
        return "s/d"
    m = int(17 * 60 + minutos)
    return f"{m // 60:02d}:{m % 60:02d}"


def min_de(hh: str | None) -> float | None:
    """'19:09' vira minutos depois das 17:00 (pode ser negativo)."""
    if not hh:
        return None
    h, m = hh.strip()[-5:].split(":")
    return int(h) * 60 + int(m) - 17 * 60
