"""Bloco "bateria e abstenção contra a chuva medida de 25/10" do capítulo dos logs.

Lê ``logs.json`` (chave ``clima_observado``, de ``logs_clima_obs``). Mantém o bloco da
chuva prevista; este acrescenta a chuva medida em estação e o modelo provisório, cada um
com a fonte escrita. Sem estação medida, o texto diz que o teste continua pendente.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import inteiro, nota, num, p, sinal, tabela


def _f(fx: list[dict], nome: str) -> dict | None:
    return next((x for x in fx if x["faixa"] == nome), None)


def _pct(x: dict | None) -> str:
    if not x or x["parcela_pct"]["valor"] is None:
        return "n/d"
    v = x["parcela_pct"]
    ic = v.get("ic95")
    return f"{num(v['valor'], 1)}%" + (
        f" (IC95 {num(ic[0], 1)} a {num(ic[1], 1)})" if ic else ""
    )


def _razao(x: dict | None) -> str:
    r = (x or {}).get("razao_vs_seca")
    if not r or r.get("valor") is None:
        return "n/d"
    ic = r.get("ic95")
    return num(r["valor"], 2) + (
        f" (IC95 {num(ic[0], 2)} a {num(ic[1], 2)})" if ic else ""
    )


def _pp(v: dict | None) -> str:
    if not v or v.get("valor") is None:
        return "n/d"
    ic = v.get("ic95")
    return sinal(v["valor"], 2) + (
        f" (IC95 {sinal(ic[0], 2)} a {sinal(ic[1], 2)})" if ic else ""
    )


def _tabela_bateria(fx: list[dict], titulo: str) -> str:
    linhas = [
        [x["rotulo"], inteiro(x["celulas"]), inteiro(x["secoes"]), _pct(x), _razao(x)]
        for x in fx
        if x["secoes"]
    ]
    return tabela(
        ["chuva", "células", "seções", "bateria na votação", "razão contra a seca"],
        linhas,
        titulo,
    )


def _tabela_abst(fx: list[dict], titulo: str) -> str:
    linhas = [
        [
            x["rotulo"],
            inteiro(x["secoes"]),
            num((x["abst_pct"] or {}).get("valor"), 1) + "%",
            _pp(x["dentro_uf_pp"]),
            _pp(x["variacao_vs_1t_dentro_uf_pp"]),
        ]
        for x in fx
        if x["secoes"]
    ]
    return tabela(
        [
            "chuva",
            "seções",
            "abstenção",
            "contra a média da UF (pp)",
            "variação 1º→2º contra a UF (pp)",
        ],
        linhas,
        titulo,
    )


def clima_observado(L: dict) -> str:
    C = L.get("clima_observado") or {}
    if not C.get("disponivel"):
        return ""
    ref = (C.get("referencia_1t") or {}).get("chuva_votacao", {})
    ref_dia = (C.get("referencia_1t") or {}).get("chuva_diaria", {})
    cob = C["cobertura_celulas"]
    est = C["estacoes"]
    bd = C["bateria"]["chuva_dia_medida"]
    bv = C["bateria"]["chuva_votacao_medida"]
    bm = C["bateria"]["chuva_votacao_modelo"]
    ad = C["abstencao"]["chuva_dia_medida"]
    am = C["abstencao"]["chuva_votacao_modelo"]
    r1 = (ref.get("forte") or {}).get("razao_vs_seca")
    h = p(
        f"<strong>Chuva medida.</strong> {inteiro(est.get('cemaden_com_dia', 0))} pluviômetros do CEMADEN têm o "
        f"acumulado de 25/10 (00h às 24h de Brasília) e {inteiro(est.get('cemaden_com_votacao', 0))} têm a série "
        f"das horas de votação. Com estação a até 50 km, {inteiro(cob['com_estacao_dia'])} das "
        f"{inteiro(cob['celulas'])} células de 0,25° (média ponderada pelo inverso do quadrado da distância), "
        f"{inteiro(C['secoes_chuva_dia_medida'])} seções. As estações automáticas do INMET não tinham dado público "
        "de 25/10 na consulta: a rota aberta devolve vazio e a tabela do site exige captcha.",
        "verificado",
    )
    if not C["secoes_chuva_dia_medida"]:
        h += p(
            "Até esta versão nenhuma estação entrou: a série horária do CEMADEN respondeu 503 em 26/10 e a "
            "tabela de acumulados só isola o dia 25/10 (00h às 24h) a partir das 03h UTC de 27/10. Enquanto isso, "
            "todas as células usam o modelo, e o teste com chuva medida fica pendente.",
            "verificado",
        )
    if C["secoes_chuva_dia_medida"]:
        f20 = _f(bd, "20_ou_mais")
        h += p(
            f"Bateria durante a votação por chuva medida no dia: {_pct(_f(bd, 'seca'))} na seca, "
            f"{_pct(_f(bd, 'moderada'))} com 5 a 20 mm e {_pct(f20)} com 20 mm ou mais; razão contra a seca "
            f"{_razao(f20)}. No 1º turno, com a reanálise ERA5, a razão da chuva forte nas horas de votação foi "
            f"{num(r1, 2)} e a da chuva forte no dia, {num((ref_dia.get('forte') or {}).get('razao_vs_seca'), 2)}.",
            "verificado",
        )
        h += _tabela_bateria(
            bd,
            "Bateria durante a votação por chuva medida em 25/10 (dia inteiro, estações CEMADEN)",
        )
        if bv:
            h += _tabela_bateria(
                bv,
                "Bateria durante a votação por chuva medida nas horas de votação (07h às 18h)",
            )
        h += p(
            f"Abstenção dentro da UF por chuva medida: {_pp((_f(ad, 'seca') or {}).get('dentro_uf_pp'))} na seca e "
            f"{_pp((_f(ad, '20_ou_mais') or {}).get('dentro_uf_pp'))} com 20 mm ou mais, em pontos contra a média "
            "da própria UF; descontada a abstenção do 1º turno na mesma seção, "
            f"{_pp((_f(ad, '20_ou_mais') or {}).get('variacao_vs_1t_dentro_uf_pp'))} com 20 mm ou mais.",
            "verificado",
        )
        h += _tabela_abst(
            ad, "Abstenção do 2º turno por chuva medida em 25/10, dentro da UF"
        )
    m20 = _f(bm, "20_ou_mais")
    h += p(
        f"Com o modelo ECMWF IFS (análise operacional, provisória) em todas as células, nas horas de votação: "
        f"bateria {_pct(_f(bm, 'seca'))} na seca e {_pct(m20)} com 20 mm ou mais, razão {_razao(m20)}, "
        f"contra {num(r1, 2)} no 1º turno com a reanálise. Abstenção contra a média da UF "
        f"{_pp((_f(am, '20_ou_mais') or {}).get('dentro_uf_pp'))} ponto com 20 mm ou mais; descontada a "
        "abstenção do 1º turno na mesma seção, "
        f"{_pp((_f(am, '20_ou_mais') or {}).get('variacao_vs_1t_dentro_uf_pp'))} ponto.",
        "verificado",
    )
    h += _tabela_bateria(
        bm,
        "Bateria durante a votação por chuva do modelo nas horas de votação (provisório)",
    )
    h += _tabela_abst(
        am,
        "Abstenção do 2º turno por chuva do modelo nas horas de votação, dentro da UF (provisório)",
    )
    h += nota(
        "contrario",
        "Pluviômetro a até 50 km é estimativa para a célula, não medição no prédio; o acumulado diário inclui a "
        "madrugada e a noite, fora da votação. O modelo é provisório e será trocado pela reanálise ERA5 quando ela "
        "cobrir 25/10 (prevista para 31/10). Associação entre lugares, não efeito da chuva sobre a urna ou o eleitor.",
        "Medição de estação não é chuva no prédio.",
    )
    return h


LIMITE = (
    "A chuva medida do 2º turno vem de pluviômetros do CEMADEN a até 50 km da célula e, onde não há estação, do "
    "modelo ECMWF IFS provisório; a reanálise ERA5 de 25/10 sai por volta de 31/10."
)
