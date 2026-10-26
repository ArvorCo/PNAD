"""Bloco "Comparecimento e voto em Lula, seção por seção: 1º e 2º turnos" do capítulo Abstenção.

Lê os JSONs de `scripts/abstencao-lula-secoes.py` (1º turno em `analysis/apuracao_2026/`, 2º turno e
variação entre turnos em `analysis/apuracao_2t_2026/dados/`) e mostra as figuras reduzidas de
`docs/img/apuracao_2t/`. Todo número do texto sai dos JSONs; a cobertura do 2º turno é declarada na tela.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import (
    ROOT,
    Dados,
    inteiro,
    num,
    p,
    sinal,
    tabela,
)

IMG = "img/apuracao_2t"
UM_T = "../../apuracao_2026/{eixo}_lula_secoes.json"
DOIS_T = "{eixo}_lula_secoes.json"
VARIACAO = "variacao_comparecimento_lula_secoes.json"
ESTILO = (
    "<style>.galeria-uma{grid-template-columns:minmax(0,1fr);max-width:900px}</style>"
)
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


def _r(x: float | None) -> str:
    return "s/d" if x is None else sinal(x, 3)


def _figura(stem: str, alt: str, legenda: str, altura: int = 1200) -> str:
    if not (ROOT / "docs" / IMG / f"{stem}.jpg").exists():
        return ""
    return (
        f'<figure><a href="img/{stem}.png"><img src="{IMG}/{stem}.jpg" alt="{escape(alt)}" '
        f'loading="lazy" width="1200" height="{altura}"></a>'
        f"<figcaption>{legenda}</figcaption></figure>"
    )


def _par(eixo: str, um: dict, dois: dict, nome: str) -> str:
    cob = dois["cobertura"]
    f1 = _figura(
        f"{eixo}_lula_secoes_1t",
        f"{nome.capitalize()} e voto em Lula por seção no 1º turno",
        f"1º turno, {inteiro(um['n'])} seções: r = {_r(um['pearson'])} (peso igual), "
        f"{_r(um['pearson_ponderado'])} (ponderado por aptos).",
    )
    f2 = _figura(
        f"{eixo}_lula_secoes_2t",
        f"{nome.capitalize()} e voto em Lula por seção no 2º turno"
        + (", cobertura parcial" if cob.get("parcial", True) else ""),
        f"2º turno, {inteiro(dois['n'])} seções lidas"
        + (
            f" ({num(cob['pct'], 1)}% do total)"
            if cob.get("parcial", True)
            else " (todas as seções coletadas)"
        )
        + ": "
        f"r = {_r(dois['pearson'])} (peso igual), {_r(dois['pearson_ponderado'])} (ponderado).",
    )
    return f'<div class="galeria">{f1}{f2}</div>' if f1 or f2 else ""


def _forca(r: float) -> str:
    a = abs(r)
    return "quase nula" if a < 0.1 else "fraca" if a < 0.3 else "moderada"


def _mudanca(r_antes: float, r_depois: float) -> str:
    dif = r_depois - r_antes
    if abs(dif) < 0.02:
        return "praticamente não mudou"
    pouco = "um pouco " if abs(dif) < 0.05 else ""
    rumo = "mais forte" if abs(r_depois) > abs(r_antes) else "mais fraca"
    return f"ficou {pouco}{rumo}"


def _cobertura(cob: dict) -> str:
    regs = []
    for nome in REGIOES:
        v = cob["por_regiao"].get(nome) or {}
        tot = v.get("total_1t") or 0
        pc = 100 * v.get("lidas", 0) / tot if tot else 0
        regs.append(f"{nome} {num(pc, 0)}%")
    ausentes = [n for n in REGIOES if not (cob["por_regiao"].get(n) or {}).get("lidas")]
    hora = (cob.get("_gerado") or "")[11:16]
    if not cob.get("parcial", True):
        return p(
            f"<strong>Cobertura completa.</strong> O banco de boletins do 2º turno foi lido inteiro: "
            f"{inteiro(cob['secoes_lidas'])} seções em {len(cob['ufs_lidas'])} UFs, contra {inteiro(cob['secoes_total_1t'])} "
            "do 1º turno (a diferença vem do cadastro de seções de cada turno). O 1º turno é recalculado "
            "nas mesmas seções antes de qualquer comparação.",
            "verificado",
        )
    return p(
        f"<strong>Cobertura parcial.</strong> O banco de boletins do 2º turno ainda está sendo lido: "
        f"{inteiro(cob['secoes_lidas'])} de {inteiro(cob['secoes_total_1t'])} seções ({num(cob['pct'], 1)}%) "
        f"em {len(cob['ufs_lidas'])} UFs ({', '.join(cob['ufs_lidas'])}){f', às {hora} de 25/10' if hora else ''}. "
        f"Por região: {'; '.join(regs)}."
        + (f" {', '.join(ausentes)} ainda sem nenhuma seção." if ausentes else "")
        + " A coleta avança por UF, então a amostra parcial não é aleatória: por isso o 1º turno é recalculado "
        "nas mesmas seções antes de qualquer comparação.",
        "verificado",
    )


def _tabela_geral(um: dict, dois: dict, var: dict | None) -> str:
    m = dois["primeiro_turno_mesmas_secoes"]
    lf = m["lula_entre_finalistas"]
    linhas = [
        [
            "1º turno, país",
            inteiro(um["n"]),
            _r(um["pearson"]),
            _r(um["pearson_ponderado"]),
            sinal(um["ols"]["inclinacao"], 2),
            "% dos válidos",
        ],
        [
            "1º turno, mesmas seções do 2º",
            inteiro(m["n"]),
            _r(m["pearson"]),
            _r(m["pearson_ponderado"]),
            sinal(m["ols"]["inclinacao"], 2),
            "% dos válidos",
        ],
        [
            "1º turno, mesmas seções do 2º",
            inteiro(m["n"]),
            _r(lf["pearson"]),
            _r(lf["pearson_ponderado"]),
            sinal(lf["ols"]["inclinacao"], 2),
            "% de Lula + Flávio",
        ],
        [
            "2º turno, seções lidas",
            inteiro(dois["n"]),
            _r(dois["pearson"]),
            _r(dois["pearson_ponderado"]),
            sinal(dois["ols"]["inclinacao"], 2),
            "% de Lula + Flávio",
        ],
    ]
    if var:
        linhas.append(
            [
                "Variação 2º − 1º na mesma seção",
                inteiro(var["n"]),
                _r(var["pearson"]),
                _r(var["pearson_ponderado"]),
                sinal(var["ols"]["inclinacao"], 2),
                "pontos de Lula + Flávio",
            ]
        )
    return tabela(
        [
            "Recorte",
            "Seções",
            "Pearson, peso igual",
            "Pearson, por aptos",
            "Inclinação",
            "Lula medido em",
        ],
        linhas,
        "Comparecimento (% dos aptos) e voto em Lula por seção. Inclinação: pontos de Lula por ponto de "
        "comparecimento, mínimos quadrados com peso igual.",
    )


def _tabela_regioes(um: dict, dois: dict) -> str:
    m = dois["primeiro_turno_mesmas_secoes"]["regioes"]
    linhas = []
    for nome in REGIOES:
        r1 = (um["regioes"].get(nome) or {}).get("r")
        rm = (m.get(nome) or {}).get("r")
        v2 = dois["regioes"].get(nome) or {}
        linhas.append(
            [
                nome,
                _r(r1),
                _r(rm),
                _r(v2.get("r")),
                inteiro(v2.get("n")),
                num(v2.get("abst_media"), 1) if v2.get("r") is not None else "s/d",
                num(v2.get("lula_medio"), 1) if v2.get("r") is not None else "s/d",
            ]
        )
    return tabela(
        [
            "Região",
            "r 1º turno, país",
            "r 1º turno, mesmas seções",
            "r 2º turno",
            "Seções 2º turno",
            "Comparecimento 2º turno, %",
            "Lula 2º turno, %",
        ],
        linhas,
        "Pearson com peso igual dentro de cada região; médias do 2º turno ponderadas por aptos. "
        "s/d: região sem seções suficientes na coleta.",
    )


def _leitura_regioes(dois: dict) -> str:
    val = {k: v for k, v in dois["regioes"].items() if v.get("r") is not None}
    if len(val) < 2:
        return ""
    r_nac = dois["pearson"]
    topc = max(val, key=lambda k: val[k]["abst_media"])
    topl = max(val, key=lambda k: val[k]["lula_medio"])
    opostas = [k for k, v in val.items() if (v["r"] > 0) != (r_nac > 0)]
    if topc == topl:
        txt = (
            f"No 2º turno, nas seções lidas, o {topc} tem o maior comparecimento médio "
            f"({num(val[topc]['abst_media'], 1)}%) e o maior voto em Lula ({num(val[topl]['lula_medio'], 1)}%)."
        )
    else:
        txt = (
            f"No 2º turno, nas seções lidas, a região de maior comparecimento médio é o {topc} "
            f"({num(val[topc]['abst_media'], 1)}%) e a de maior voto em Lula é o {topl} "
            f"({num(val[topl]['lula_medio'], 1)}%)."
        )
    if opostas:
        txt += (
            " Dentro "
            + " e ".join(f"do {k} (r = {_r(val[k]['r'])})" for k in opostas)
            + " o sinal é o oposto do nacional: ali, seções com mais comparecimento votaram menos em Lula."
        )
    fracas = [k for k, v in val.items() if abs(v["r"]) < 0.05 and k not in opostas]
    if fracas:
        txt += f" No {' e no '.join(fracas)} a relação dentro da região é quase nula."
    h = p(txt, "verificado")
    if topc == topl and max(abs(v["r"]) for v in val.values()) < abs(r_nac):
        h += p(
            f"Como nenhuma região tem correlação interna tão forte quanto a nacional ({_r(r_nac)}), boa parte "
            "da relação nacional vem da diferença entre regiões, e não de dentro delas.",
            "inferencia",
        )
    return h


def bloco(d: Dados) -> str:
    um = d.get(UM_T.format(eixo="comparecimento"))
    dois = d.get(DOIS_T.format(eixo="comparecimento"))
    if not um or not dois:
        return ""
    um_a = d.get(UM_T.format(eixo="abstencao"))
    dois_a = d.get(DOIS_T.format(eixo="abstencao"))
    var = d.get(VARIACAO)
    cob = dict(dois["cobertura"], _gerado=dois.get("gerado_em", ""))
    m = dois["primeiro_turno_mesmas_secoes"]
    lf = m["lula_entre_finalistas"]

    h = (
        ESTILO
        + "<h3>Comparecimento e voto em Lula, seção por seção: 1º e 2º turnos</h3>"
    )
    h += _cobertura(cob)
    h += p(
        f"No 1º turno, em {inteiro(um['n'])} seções do país, a correlação entre comparecimento e voto em Lula foi "
        f"{_forca(um['pearson'])}: r = {_r(um['pearson'])} com peso igual e {_r(um['pearson_ponderado'])} "
        f"ponderada por aptos. Nas {inteiro(dois['n'])} seções do 2º turno já lidas, r = {_r(dois['pearson'])} e "
        f"{_r(dois['pearson_ponderado'])}; a reta {'sobe' if dois['ols']['inclinacao'] > 0 else 'desce'} "
        f"{num(abs(dois['ols']['inclinacao']), 2)} ponto de Lula por ponto "
        f"de comparecimento, e o comparecimento explica {num(100 * dois['pearson'] ** 2, 1)}% da variação do voto "
        "entre seções.",
        "verificado",
    )
    h += p(
        f"A comparação direta engana, porque as seções lidas não são o país. Recalculado nas mesmas "
        f"{inteiro(m['n'])} seções e com a mesma régua (Lula em % de Lula + Flávio), o 1º turno dá "
        f"r = {_r(lf['pearson'])} e inclinação {sinal(lf['ols']['inclinacao'], 2)}; o 2º turno dá "
        f"{_r(dois['pearson'])} e {sinal(dois['ols']['inclinacao'], 2)}. Entre os turnos, a relação "
        f"{_mudanca(lf['pearson'], dois['pearson'])} nessas seções.",
        "verificado",
    )
    h += _par("comparecimento", um, dois, "comparecimento")
    h += _tabela_geral(um, dois, var)
    h += _leitura_regioes(dois)
    h += _tabela_regioes(um, dois)
    if var:
        q = var["quadrantes_pct"]
        sobe = q["lula_sobe"]
        s_alta = q["lula_sobe_onde_comp_sobe"]
        s_queda = q["lula_sobe_onde_comp_cai"]
        perto = s_alta is not None and s_queda is not None and abs(s_alta - s_queda) < 5
        h += p(
            f"<strong>A mesma seção nos dois turnos.</strong> Em {inteiro(var['n'])} seções casadas pela chave "
            f"UF, município, zona e seção, Lula variou em média {sinal(var['dlula_medio_pond'], 2)} pontos "
            f"(em % de Lula + Flávio) e o comparecimento {sinal(var['dcomp_medio_pond'], 2)}. A correlação entre "
            f"as duas variações é {_forca(var['pearson'])} (r = {_r(var['pearson'])}; inclinação "
            f"{sinal(var['ols']['inclinacao'], 3)}). Lula subiu em {num(sobe, 1)}% das seções: em "
            f"{num(s_alta, 1)}% das que tiveram mais comparecimento e em {num(s_queda, 1)}% das que tiveram menos."
            + (
                " O ganho de Lula entre os turnos não acompanha a mudança do comparecimento seção a seção."
                if perto and abs(var["pearson"]) < 0.1
                else (
                    f" Onde o comparecimento subiu, Lula subiu com um pouco mais de frequência, mas a correlação é "
                    f"{_forca(var['pearson'])}: o ganho entre os turnos foi quase geral, com mais ou menos gente na urna."
                    if abs(var["pearson"]) < 0.1
                    else ""
                )
            ),
            "verificado",
        )
        f3 = _figura(
            "variacao_comparecimento_lula_secoes_2t",
            "Variação do comparecimento e variação do voto em Lula entre os turnos, por seção",
            f"Variação 2º menos 1º turno na mesma seção, {inteiro(var['n'])} seções casadas: "
            f"r = {_r(var['pearson'])}.",
            altura=1000,
        )
        if f3:
            h += f'<div class="galeria galeria-uma">{f3}</div>'
    if um_a and dois_a:
        h += (
            "<details><summary>As mesmas figuras com a abstenção no eixo</summary>"
            + p(
                f"Abstenção é o complemento do comparecimento, então o sinal se inverte e a força é a mesma: "
                f"1º turno r = {_r(um_a['pearson'])}, 2º turno nas seções lidas r = {_r(dois_a['pearson'])}."
            )
            + _par("abstencao", um_a, dois_a, "abstenção")
            + "</details>"
        )
    rumo = "mais" if dois["pearson"] > 0 else "menos"
    h += (
        '<aside class="hyp"><p><strong>Limite da leitura.</strong> Correlação entre seções é ecológica: mostra '
        f"que seções com mais comparecimento votaram, em média, um pouco {rumo} em Lula, não que o eleitor que "
        "compareceu votou em Lula. A mesma correlação aparece se comparecimento e voto dependem de uma terceira "
        "coisa, como a região, a renda ou o tamanho do município. Nenhum destes gráficos identifica eleitor."
        "</p></aside>"
    )
    return h
