"""Capítulo 02 do dossiê do 2º turno: a noite minuto a minuto.

Abre pelo silêncio de publicação (`linha_do_tempo.pausas.silencio_geral`), põe
ao lado as marcas da decisão do STF com veículo, hora e link
(`noticias_noite.json`), e segue pelas figuras de `pagina_fig_noite`.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import limites, nota, p, rotulo, tabela

from .pagina_comum import NOME_UF, Capitulo, Dados, cabeca, caminho, inteiro, num
from .pagina_fig_noite import (
    fig_acumulado,
    fig_fatia,
    fig_lotes,
    fig_mapa_fechou,
    fig_regua,
    serie,
    trechos_flavio_frente,
)

NOTICIAS = "../noticias_noite.json"
L1T = "../../apuracao_2026/dados/linha_do_tempo.json"

# Matérias da cronologia da decisão, escolhidas pelo trecho do endereço.
CRONOLOGIA = [
    "estadao.com.br/politica/eleicoes/antes-de-decisao-de-zanin",
    "stf-prorroga-votacao-ate-as-19h",
    "zanin-do-stf-determina-extensao",
    "zanin-manda-ampliar-horario",
    "tse-pausa-divulgacao-de-resultados",
    "tse-avisou-secoes-sobre-prorrogacao",
    "prorrogacao-ate-19h-e-so-para-urnas",
    "horario-de-votacao-ampliado-sera-apenas",
    "tse-secoes-eleitorais-ainda-abertas",
    "presidente-do-tre-sp-afirma-que-so-recebeu",
    "em-sp-80-das-urnas-estavam-encerradas",
    "presidente-do-tre-sp-diz-que-recebeu-decisao-de-zanin-perto-das-17h",
]
TIPO = {
    "fato": "fato documentado pela fonte",
    "declaracao": "declaração",
    "relato": "relato",
    "hipotese": "análise",
}


def hora_item(it: dict) -> str:
    q = it.get("quando", "")
    if "T" in q:
        return q.split("T")[1][:5]
    return "hora não informada"


def cronologia(N: dict | None) -> str:
    if not N:
        return ""
    itens = []
    achados = [
        x for x in N.get("itens", []) if any(c in x.get("url", "") for c in CRONOLOGIA)
    ]
    achados.sort(
        key=lambda x: x.get("quando", "") if "T" in x.get("quando", "") else "9"
    )
    for it in achados:
        selo = (
            rotulo("relato") + " " if it.get("tipo") in ("relato", "declaracao") else ""
        )
        itens.append(
            f'<li>{selo}<b>{hora_item(it)}</b> · <a href="{escape(it["url"])}">{escape(it.get("veiculo", ""))}</a>'
            f" ({TIPO.get(it.get('tipo', ''), it.get('tipo', ''))}): {escape(it.get('resumo', ''))}</li>"
        )
    if not itens:
        return ""
    return (
        "<h3>A decisão, pelas fontes</h3>"
        "<p>Horário de Brasília. A hora é a de publicação da página, salvo quando a matéria cita a hora do fato; "
        "o banco do coletor não registra a decisão, só o silêncio que veio junto.</p>"
        f'<ul class="fontes">{"".join(itens)}</ul>'
    )


def bloco_parada(L: dict) -> str:
    sil = L["pausas"]["silencio_geral"]
    lac = L["pausas"]["maior_lacuna_nacional"]
    cl = sil.get("leituras_por_classe", {})
    classes = ", ".join(
        f"{inteiro(v)} {k.replace('_', ' ')}"
        for k, v in sorted(cl.items(), key=lambda kv: -kv[1])
    )
    return p(
        f"Entre {sil['ultimo_gerado_antes_brt'][11:19]} e {sil['primeiro_gerado_depois_brt'][11:19]}, "
        f"nenhum arquivo de nenhum tipo (resultado, andamento ou configuração, dos dois pleitos) tem hora de geração: "
        f"{inteiro(sil['versoes_geradas_dentro'])} versões em {num(sil['minutos'], 1)} minutos. O coletor não parou: fez "
        f"{inteiro(sil['leituras_no_intervalo'])} leituras no intervalo ({classes}). O arquivo nacional foi de "
        f"{inteiro(lac['st_antes'])} para {inteiro(lac['st_depois'])} seções entre {lac['de_brt'][11:19]} e {lac['ate_brt'][11:19]}.",
        "verificado",
    ) + p(
        "A pausa coincide com a janela da prorrogação. O banco mostra o silêncio de publicação, não a causa; "
        "segundo a Agência Brasil, o TSE suspendeu a totalização às 17h06 por causa da decisão.",
        "inferencia",
    )


def bloco_frente(L: dict, d: Dados) -> str:
    vs = [v for v in serie(L) if v["pct_flavio"] is not None and v["min"] >= 120]
    fr = trechos_flavio_frente(vs)
    if not fr:
        return ""
    mx = max(v["pct_flavio"] for v in vs)
    J = d.get("projecao_noite.json")
    proj = ""
    if J and J.get("lider_projetado_em_todos_os_pontos") == ["lula"]:
        proj = " Nesse mesmo intervalo, a projeção da casa continuava com Lula à frente (capítulo 03)."
    return p(
        f"Depois das 19:00, Flávio teve mais da metade dos válidos contados no arquivo nacional de {fr[0][0]['gerado_brt'][11:16]} a "
        f"{fr[-1][1]['gerado_brt'][11:16]}, com máximo de {num(mx, 2)}%.{proj}",
        "verificado",
    ) + p(
        "A leitura provável é de composição, não de virada: o que entra primeiro depende de onde as seções transmitem antes. "
        'O capítulo <a href="#cedo_tarde">Cedo e tarde</a> testa isso comparando cada grupo de municípios com ele mesmo no 1º turno.',
        "inferencia",
    )


def tabela_pausas_uf(L: dict) -> str:
    linhas = []
    for pz in L["pausas"]["tabela_do_coletor"]:
        if pz.get("nivel") != "uf":
            continue
        ate = pz.get("ate_brt")
        linhas.append(
            [
                f"{NOME_UF.get(pz['uf'], pz['uf'])} ({pz['uf']})",
                pz["de_brt"][11:19],
                ate[11:19] if ate else "em aberto na rodada",
                num(pz["minutos"], 1) if pz.get("minutos") is not None else "s/d",
                inteiro(pz.get("st_antes")),
                (
                    inteiro(pz.get("st_depois"))
                    if pz.get("st_depois") is not None
                    else "s/d"
                ),
            ]
        )
    if not linhas:
        return ""
    return tabela(
        ["UF", "De", "Até", "Minutos", "Seções antes", "Seções depois"],
        linhas,
        "Pausas por UF gravadas pelo coletor depois das 19:00 (sem versão nova do arquivo de UF por mais de 7 minutos, com contagem incompleta). Pausa é intervalo sem versão nova publicada, não acusação.",
    )


def bloco_ponte_alta(d: Dados) -> str:
    P = d.get("presidente.json")
    if not P:
        return ""
    c = P["municipios"]["colunas"]
    rows = [dict(zip(c, r, strict=False)) for r in P["municipios"]["linhas"]]
    rows = [r for r in rows if r.get("fechou_min") is not None]
    if not rows:
        return ""
    m = min(rows, key=lambda r: r["fechou_min"])
    if m["fechou_min"] >= 120:
        return ""
    seg = sorted(r["fechou_min"] for r in rows)[1]
    return nota(
        "apuracao",
        f"{m['nome'].title()} ({m['uf']}, {inteiro(m['secoes'])} seções) teve todas as seções totalizadas na versão das "
        f"{m['fechou_hhmm']}, antes do fim da votação prorrogada; o segundo município completo só apareceu {num(seg - m['fechou_min'], 0)} "
        "minutos depois. A prorrogação valia apenas para urnas ainda abertas, e as seções do município podem ter fechado às 17h. "
        "Atipicidade pede explicação, não prova irregularidade.",
        "Um município completo às 17:07.",
    )


def bloco_regressivas(L: dict) -> str:
    pn = L["regressoes"]["por_nivel"]
    marc = sum(v["marcadas_regressivas"] for v in pn.values())
    cop = sum(v["copia_antiga"] for v in pn.values())
    gen = len(L["regressoes"].get("contagem_regressiva") or [])
    det = ", ".join(
        f"{k} {v['copia_antiga']}" for k, v in pn.items() if v["copia_antiga"]
    )
    return p(
        f"O coletor marcou {inteiro(marc)} versões como regressivas (o contador do arquivo caiu). Pela hora de geração, "
        f"{inteiro(cop)} eram cópias antigas servidas de novo pelo CDN ({det}), e {inteiro(gen)} versões genuínas tiveram "
        "menos seções ou menos comparecimento que a anterior. Nenhuma contagem andou para trás.",
        "verificado",
    )


def tabela_latencia(L: dict) -> str:
    nomes = {"br": "Nacional", "uf": "UF", "mu": "Município", "zona": "Zona"}
    linhas = [
        [
            nomes.get(k, k),
            inteiro(v["n"]),
            num(v["p50_s"], 1),
            num(v["p95_s"], 1),
            num(v["max_s"] / 60, 1),
        ]
        for k, v in L["latencia"]["por_nivel"].items()
    ]
    return tabela(
        ["Nível", "Versões", "Mediana (s)", "p95 (s)", "Máximo (min)"],
        linhas,
        "Segundos entre a geração do arquivo no TSE e a primeira captura pelo coletor. Inclui o intervalo de sondagem: "
        "é teto da demora, não medida dela. Os máximos são as versões geradas às 17:07 e lidas depois da parada.",
    )


def render(d: Dados, cap: Capitulo) -> str:
    L = d.get("linha_do_tempo.json")
    N = d.get(NOTICIAS)
    sil = L["pausas"]["silencio_geral"]
    vs = serie(L)
    h = cabeca(
        cap,
        f"{num(sil['minutos'], 1)} minutos<br><em>sem um arquivo.</em>",
        f"{inteiro(len(vs))} versões do arquivo nacional desde as 17:00, uma parada de "
        f"{sil['ultimo_gerado_antes_brt'][11:16]} a {sil['primeiro_gerado_depois_brt'][11:16]} e a decisão do STF no meio.",
    )
    h += bloco_parada(L) + cronologia(N)
    h += fig_acumulado(L, N)
    h += bloco_frente(L, d) + fig_fatia(L)
    h += fig_lotes(L)
    h += "<h3>As pausas de Amazonas e Roraima</h3>" + tabela_pausas_uf(L)
    h += "<h3>A hora em que cada UF fechou</h3>" + fig_mapa_fechou(L)
    h += "<h3>A mesma régua para as duas noites</h3>" + fig_regua(L, d.get(L1T))
    h += bloco_ponte_alta(d)
    h += "<h3>O que o coletor viu</h3>" + bloco_regressivas(L) + tabela_latencia(L)
    h += limites(
        [
            "A hora é a de geração de cada versão pelo TSE, não a de leitura pelo coletor.",
            "As marcas da decisão vêm do noticiário, com veículo e link; o banco não registra decisões.",
            "Fatia de Flávio ao longo da noite mostra quem já tinha sido contado, não a direção do resultado.",
            "A régua do 1º turno desconta os 120 minutos da prorrogação; as duas noites tiveram fluxos de transmissão diferentes.",
            caminho(L, "rotulo_pausa")
            or "Pausa é intervalo sem versão nova publicada, não acusação.",
        ]
    )
    return h
