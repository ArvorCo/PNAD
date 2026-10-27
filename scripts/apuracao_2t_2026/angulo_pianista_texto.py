"""Memorando ``angulo_pianista.md`` e frases comuns ao bloco da página.

Todo número sai de ``angulo_pianista.json``. Sem travessão; rótulo fixo.
"""

from __future__ import annotations

from typing import Any

from apuracao_2026.pagina_comum import inteiro, num, sinal

LINHAS_TABELA = [
    "pct_nbio",
    "excesso_ultima_pp",
    "pct_todos_na_ultima_hora",
    "maior_sequencia_nbio",
    "menos_log10_p",
    "razao_intervalo_nbio",
    "hab_nbio_p50_s",
    "hab_p50_s",
    "reinicios_votacao",
    "marca",
]


def n2(x: float | None, casas: int = 2) -> str:
    """Número com o menos tipográfico quando negativo."""
    return sinal(x, casas) if x is not None and x < 0 else num(x, casas)


def chance(x: float | None) -> str:
    """Chance da sequência sob ordem aleatória, em palavras curtas."""
    if x is None:
        return "s/d"
    if x < 1e-6:
        return "< 1 em 1 milhão"
    return f"{num(100 * x, 2 if x < 0.01 else 1)}%"


def ic(x: dict[str, Any] | None, casas: int = 2) -> str:
    """Estimativa com o IC de 95% do bootstrap de municípios."""
    if not x or x.get("estimativa") is None:
        return "s/d"
    lo, hi = x.get("ic95") or [None, None]
    return f"{sinal(x['estimativa'], casas)} ({sinal(lo, casas)} a {sinal(hi, casas)})"


def linhas_metricas(d: dict) -> list[list[str]]:
    """Métrica, célula 2T e 1T, DiD contra vizinhas, contra salto sem alta, contra o 1T."""
    g = d["grupos"]["celula"]
    out = []
    for m in LINHAS_TABELA:
        c = d["comparacoes"][m]
        out.append(
            [
                c["nome"],
                n2(g.get(m + "_2t")),
                n2(g.get(m + "_1t")),
                ic(c["did_vizinhas"]),
                ic(c["did_salto_sem_delta"]),
                ic(c["celula_2t_menos_1t"]),
            ]
        )
    return out


CAB_METRICAS = [
    "Métrica do log",
    "Célula 2T",
    "Célula 1T",
    "DiD contra vizinhas",
    "DiD contra salto sem alta",
    "Célula 2T menos 1T",
]

CAB_TOP = [
    "UF",
    "Município",
    "Zona",
    "Seção",
    "Aptos",
    "Sem biometria 2T (1T)",
    "Na última hora: sem bio / todos",
    "Maior sequência (chance)",
    "Intervalo sem bio / seção (s)",
    "Habilitação sem bio / bio (s)",
    "Componentes",
]


def linha_top(t: dict, link: str | None = None) -> list[str]:
    secao = str(t["secao"])
    if link:
        secao = f'<a href="{link}">{secao}</a>'
    return [
        t["uf"],
        t["municipio"],
        str(t["zona"]),
        secao,
        inteiro(t["aptos"]),
        f"{num(t['pct_sem_biometria_2t'], 1)}% ({num(t['pct_sem_biometria_1t'], 1)}%)",
        f"{num(t['pct_sem_biometria_na_ultima_hora'], 1)}% / {num(t['pct_todos_na_ultima_hora'], 1)}%",
        f"{t['maior_sequencia']} ({chance(t.get('chance_sequencia'))})",
        f"{num(t['intervalo_sem_biometria_p50_s'], 0)} / {num(t['intervalo_p50_s'], 0)}",
        f"{num(t['hab_sem_biometria_p50_s'], 0)} / {num(t['hab_biometrica_p50_s'], 0)}",
        ", ".join(t["componentes"]) or "nenhum",
    ]


def resposta(d: dict) -> list[str]:
    """As frases centrais, em texto simples (memorando e página)."""
    c, g = d["celula"], d["grupos"]
    gc, gv, gs = g["celula"], g["vizinhas"], g["salto_sem_delta"]
    C = d["comparacoes"]
    R = d["rajadas"]["celula"]
    return [
        (
            "A marca não aparece. "
            if not gc["marca_2t"]
            else "A marca aparece em poucas seções. "
        )
        + f"Das {inteiro(c['secoes'])} seções da célula, todas com log "
        f"relido nos dois turnos, {inteiro(gc['marca_2t'])} têm a marca completa no 2º turno "
        f"e {inteiro(gc['marca_1t'])} no 1º. Nas vizinhas sorteadas do mesmo município, "
        f"{inteiro(gv['marca_2t'])} de {inteiro(gv['secoes'])}; nas seções com salto de "
        f"biometria sem alta de comparecimento, {inteiro(gs['marca_2t'])} de "
        f"{inteiro(gs['secoes'])}.",
        f"A parcela sem biometria reconhecida sobe {sinal(C['pct_nbio']['celula_2t_menos_1t']['estimativa'], 2)} pp "
        "contra a própria seção no 1º turno, porque é assim que a célula foi escolhida. Ela não "
        "se concentra no fim do dia: o excesso da última hora nas habilitações sem biometria, em "
        f"diferença em diferenças contra as vizinhas, é {ic(C['excesso_ultima_pp']['did_vizinhas'])} pp. "
        "A parcela de todos os votos dados na última hora caiu mais na célula do que nas "
        f"vizinhas, {ic(C['pct_todos_na_ultima_hora']['did_vizinhas'])} pp.",
        f"Há {inteiro(R['secoes'])} seções da célula com sequência de habilitações sem biometria "
        "improvável sob ordem aleatória. Nelas o intervalo entre votos sem biometria é "
        f"{num(R['razao_intervalo_p50'], 2)} vez o da própria seção na mediana "
        f"({inteiro(R['metade_do_intervalo_ou_menos'])} com metade ou menos), e a habilitação sem "
        f"biometria leva {num(R['hab_sem_biometria_p50_s'], 0)} s contra "
        f"{num(R['hab_biometrica_p50_s'], 0)} s da biométrica"
        + (
            ": é o ritmo lento de quem tentou a digital e foi liberado pelo documento, o "
            "desenho de leitor falhando, não de digitação em série."
            if (R["razao_intervalo_p50"] or 0) > 1
            and (R["hab_sem_biometria_p50_s"] or 0) > (R["hab_biometrica_p50_s"] or 0)
            else "."
        ),
        f"Contra as seções com o mesmo salto de biometria e sem alta de comparecimento, a célula "
        f"não se distingue no log: habilitação sem biometria {ic(C['hab_nbio_p50_s']['did_salto_sem_delta'])} s, "
        f"improbabilidade da sequência {ic(C['menos_log10_p']['did_salto_sem_delta'])}.",
    ]


def markdown(d: dict) -> str:
    c, g = d["celula"], d["grupos"]
    v = d.get("voto_ja_medido") or {}
    out = [
        "# Ângulo do pianista no 2º turno de 2026: o log da célula",
        "",
        f"Gerado em {d['gerado_em']}. {d['rotulo']}",
        "",
        "## Pergunta",
        "",
        d["pergunta"],
        "",
        "## Resposta",
        "",
        *[f"- {x}" for x in resposta(d)],
        f"- O voto já medido na mesma célula: {n2(v.get('dif_fatia_flavio_vs_vizinhas_pp'))} pp "
        f"na fatia de Flávio contra as vizinhas (ep {num(v.get('ep_fatia_flavio_vs_vizinhas_pp'), 2)}) "
        f"e {sinal(v.get('did_fatia_flavio_pp'), 2)} pp em diferença em diferenças contra o 1º "
        f"turno (ep {num(v.get('ep_did_fatia_flavio_pp'), 2)}).",
        "",
        "## Método",
        "",
        f"- Célula: {inteiro(c['secoes'])} seções em {inteiro(c['municipios'])} municípios "
        "(`pianista` de `secoes_linhas`: comparecimento ≥ +5 pp e salto da parcela sem "
        "biometria reconhecida contra a própria seção no 1º turno).",
        f"- Controles: vizinhas sem sinal do mesmo município ({inteiro(g['vizinhas']['secoes'])}, "
        f"até 10 por seção da célula, semente {d['bootstrap']['semente']}); salto de biometria "
        f"sem alta de comparecimento ({inteiro(g['salto_sem_delta']['secoes'])}); a própria "
        "seção no 1º turno.",
        "- Fonte: logs originais dos dois turnos relidos com o leitor versão 12 "
        "(`apuracao_logs.parser`); a lista de ciclos que o leitor monta é capturada e reduzida "
        "a agregados por seção. Nenhuma sequência individual é gravada. Hora de Brasília pela "
        "regra de `logs_cadencia` (8 menos a hora modal do primeiro cômputo do município).",
        f"- Erros de leitura: 2T {d['leitura_erros']['2t']}, 1T {d['leitura_erros']['1t']}.",
        "- Diferença em diferenças: 2T menos 1T da mesma seção; contra vizinhas, média por "
        "município (célula menos vizinhas) ponderada pelo n da célula; contra salto sem alta, "
        "média da célula menos média do controle. IC de 95% por bootstrap de municípios "
        f"({inteiro(d['bootstrap']['reamostragens'])} reamostragens).",
        "",
        "### Regras",
        "",
        *[f"- `{k}`: {t}" for k, t in d["regras"].items()],
        "",
        "## Números",
        "",
        "| " + " | ".join(CAB_METRICAS) + " |",
        "|" + "---|" * len(CAB_METRICAS),
        *["| " + " | ".join(r) + " |" for r in linhas_metricas(d)],
        "",
        "Componentes da marca no 2º turno (seções):",
        "",
        "| Grupo | Seções | Concentra | Rajada | Ritmo | Hab. curta | Janela | Marca | Marca nova | Leitor parado |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for nome, k in (
        ("Célula", "celula"),
        ("Vizinhas", "vizinhas"),
        ("Salto sem alta", "salto_sem_delta"),
    ):
        x = g[k]
        out.append(
            f"| {nome} | {inteiro(x['secoes'])} | {x['concentra_n_2t']} | {x['rajada_n_2t']} | "
            f"{x['ritmo_n_2t']} | {x['hab_curta_n_2t']} | {x['janela_2t']} | {x['marca_2t']} | "
            f"{x['marca_nova']} | {x['leitor_parado_2t']} |"
        )
    out += [
        "",
        "## As 20 seções da célula com a marca mais forte",
        "",
        f"Seções da célula com a marca completa: {g['celula']['marca_2t']}. A lista ordena "
        "pela marca e depois pela força declarada nas regras.",
        "",
        "| " + " | ".join([*CAB_TOP, "Politize-se"]) + " |",
        "|" + "---|" * (len(CAB_TOP) + 1),
        *["| " + " | ".join([*linha_top(t), t["link"]]) + " |" for t in d["top"]],
        "",
        "## Limites",
        "",
        "- O log registra como cada eleitor foi liberado e quando, não quem votou. Um "
        "mesário que digitasse o ano de nascimento no ritmo normal, depois de tentativas "
        "simuladas de digital, não deixaria marca no log; a ausência da marca reduz, não "
        "elimina, a hipótese.",
        "- A célula foi escolhida pelo salto da parcela sem biometria: métricas de nível dessa "
        "parcela crescem por construção. Os testes informativos são os de tempo, ritmo e "
        "concentração.",
        "- O que decidiria: a ata da mesa (liberações por ano de nascimento, troca de urna, "
        "ocorrência, fila às 17h) e o caderno de votação (assinatura de cada eleitor liberado "
        "pelo documento; nome de falecido, de quem estava fora do país ou justificou).",
        "- Bootstrap entre municípios não incorpora o sorteio das vizinhas nem o desenho do "
        "pleito. As regras da marca foram declaradas antes da contagem e não foram ajustadas; "
        "a fórmula de força, que só ordena a lista, foi revista uma vez para tirar o "
        "comprimento cru da sequência (seção em que quase ninguém foi reconhecido liderava "
        "por ter sequência longa e provável).",
        "",
    ]
    return "\n".join(out)
