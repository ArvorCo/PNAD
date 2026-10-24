"""Leitura territorial para o 2º turno e a evidência que limita a extrapolação."""

from . import mapas
from .comum import caixa, detalhes, tabela
from .util import Dados, dec, esc, ic, inteiro, pct, pp, titulo_pt


def _tabela(municipios, ident, rotulo):
    return tabela(
        [
            "Município",
            "Abstenção 1º turno",
            "Aptos 1º turno",
            "Cadastro em risco alto",
            "% do cadastro mapeado",
            "Chuva média diária",
        ],
        [
            [
                f"{esc(titulo_pt(m['municipio']))} ({m['uf']})",
                pct(m["abstencao_1t_pct"], 2),
                inteiro(m["aptos_1t"]),
                inteiro(m["eleitores_risco_alto"]),
                (
                    pct(m["risco_alto_pct"], 1)
                    if m["risco_alto_pct"] is not None
                    else "sem dado"
                ),
                (
                    dec(m["chuva_media_mm"], 1) + " mm"
                    if m["chuva_media_mm"] is not None
                    else "sem dado"
                ),
            ]
            for m in municipios
        ],
        numericas=(1, 2, 3, 4, 5),
        ordenavel=True,
        ident=ident,
        rotulo=rotulo,
        largura=780,
    )


def secao_cenario(dados: Dados) -> str:
    t = dados.territorio
    b = dados.d["abstencao_x_chuva"]["binario"]["chuva_votacao"]
    municipios = t["municipios"]
    juntos = [m for m in municipios if m["atencao_conjunta"]]
    maiores = sorted(
        (m for m in municipios if m["aptos_1t"] >= 10000),
        key=lambda m: -m["abstencao_1t_pct"],
    )[:15]
    estados = ", ".join(
        f"{u['uf']} ({pct(u['abstencao_pct'], 2)})" for u in t["ufs"][:6]
    )
    comparacoes = [("Brasil, sem controlar geografia", b["pais"][1]["abst_vs_ref_pp"])]
    for rot, chave in [
        ("Dentro da mesma UF", "dentro_da_uf"),
        ("Dentro do mesmo município", "dentro_do_municipio"),
    ]:
        comparacoes.append(
            (rot, next(iter(b[chave]["grupos"].values()))["abst_vs_ref_pp"])
        )
    conta = tabela(
        ["Comparação: >5 mm contra até 5 mm", "Diferença de abstenção", "IC 95%"],
        [[rot, pp(v["valor"]), ic(v["ic95"])] for rot, v in comparacoes],
        numericas=(1,),
        rotulo="Como a associação muda ao controlar a geografia",
        largura=600,
    )
    reg = dados.d["resumo"]["abstencao_pp_por_10mm_fe_municipio"]
    corpo = (
        '<section class="chapter" id="cenario-abstencao"><div class="section-heading">'
        '<span class="section-number">2T</span><div><h2>Onde pode haver <em>mais abstenção?</em></h2>'
        '<p class="lead">O primeiro turno fornece uma referência territorial. A chuva indica '
        "exposição logística; ainda não fornece um acréscimo de faltas estimável.</p></div></div>"
        '<div class="mapas-comparados">'
        f"<figure><h3>04/10 · Abstenção observada</h3>{mapas.mapa_abstencao(dados)}"
        "<figcaption>Taxa por UF: 100 × (aptos − presentes) / aptos. "
        '<a href="img/abstencao_1t_2026.png">Abrir também o mapa por município</a> '
        "(o card municipal usa o total nacional com exterior; este mapa e a tabela usam Brasil sem exterior).</figcaption></figure>"
        f"<figure><h3>25/10 · Chuva prevista</h3>{mapas.mapa_chuva_prevista(dados)}"
        "<figcaption>Acumulado no dia inteiro, em mm, no relógio de Brasília. "
        "A previsão não informa, nesta consulta diária, quanto cairá durante a votação. "
        "Branco fora da grade significa ausência de dado.</figcaption></figure></div>"
        f'<p>No 1º turno, a abstenção no Brasil sem exterior foi de <b>{pct(t["brasil"]["abstencao_pct"], 2)}</b>. '
        f"As maiores taxas estaduais foram {estados}. <b>Se a distribuição territorial persistir</b>, "
        "esses estados continuam como referência de maior abstenção no segundo turno. "
        "Isso não prova aumento em relação ao primeiro turno.</p>"
        + caixa(
            "Cenário de persistência, sem ajuste climático.",
            "A₂(m) = A₁(m): para cada município, repetimos a taxa de 04/10. "
            "É uma referência transparente, sem validação preditiva municipal, intervalo de previsão "
            "ou probabilidade de posição no ranking. Mudanças de mobilização, transporte e disputa "
            "podem alterar as taxas; a ausência de efeito identificado da chuva não prova efeito zero.",
        )
        + f"<h3>Abstenção anterior alta + previsão de risco alto: {inteiro(len(juntos))} municípios</h3>"
        + f'<p>{esc(t["regra_atencao"])} Abaixo, os primeiros 25. '
        "Os cortes de 10 mil e 50% são critérios editoriais de leitura, não parâmetros aprendidos. "
        "Eleitores expostos não são eleitores que vão faltar.</p>"
        + (
            _tabela(juntos[:25], "tabela-atencao", "Municípios com atenção conjunta")
            if juntos
            else "<p>Nenhum município satisfaz os cortes nesta rodada da previsão.</p>"
        )
        + detalhes(
            "Maiores taxas municipais do 1º turno, com pelo menos 10 mil aptos",
            _tabela(
                maiores,
                "tabela-persistencia",
                "Referência de persistência da abstenção",
            ),
        )
        + f'<p class="note">{esc(t["universos"])} Chuva média ponderada pelos eleitores '
        "do cadastro com valor disponível. "
        '<a href="assets/clima_1t/cenario_2t.json">Todos os municípios, contas e hashes (JSON)</a>.</p>'
        + "<h3>Como medimos a correlação entre chuva e abstenção</h3>"
        + "<p>Cruzamos cada local com a célula meteorológica de 0,25°. Comparamos chuva acima "
        "de 5 mm com até 5 mm na janela das 7h às 18h de Brasília; a taxa é ponderada por aptos. "
        "Refizemos a comparação dentro da UF e dentro do município, onde existiam os dois grupos. "
        "Os intervalos usam 2.000 reamostragens das células, preservando a dependência das urnas "
        "que compartilham a mesma medida de chuva.</p>"
        + conta
        + f'<p>A regressão contínua com efeito fixo municipal encontrou {pp(reg["coef"])} '
        f'por 10 mm ({ic(reg["ic95"])}). A comparação contra 2022 e a análise de bateria '
        "estão detalhadas abaixo. Esses testes medem associação no primeiro turno; "
        "não validam uma previsão de abstenção para 25/10. Por isso não multiplicamos "
        "os milímetros previstos por um coeficiente causal inventado.</p>"
        + '<p><a class="botao" href="#abstencao">Ver todas as especificações e limites</a> '
        '<a class="botao" href="#metodo">Ver a chuva observada no primeiro turno</a></p></section>'
    )
    return corpo
