"""Capítulos 01 a 05 do dossiê da apuração: resultado, noite, falha, regiões, exterior.

Cada capítulo é uma sequência de figuras do catálogo com, entre elas, um ou dois
parágrafos curtos. Os números saem dos JSONs, por `pagina_texto`.
"""

from __future__ import annotations

from html import escape

from . import pagina_comparacao as CMP
from . import pagina_texto as T
from . import pagina_texto_arquitetura as TA
from .pagina_comum import (
    Capitulo,
    Dados,
    checar,
    hora,
    inteiro,
    num,
    secao,
    tabela,
)
from .pagina_texto import fig

HORA_APP_OFICIAL = "19:08"  # minuto em que a casa leu a tela do aplicativo oficial
FONTE_BANCO = "linha_do_tempo.json"


def versoes(L: dict) -> list[dict]:
    v = L["nacional"]["versoes"]
    return [dict(zip(v["colunas"], r, strict=False)) for r in v["linhas"]]


def paradas_nacionais(L: dict) -> list[dict]:
    return [
        t
        for t in L["travamentos"]["nacional"]
        if (t.get("secoes_no_salto") or 0) >= 1000
    ]


# ------------------------------------------------------------------ 01


def r_abertura(d: Dados, cap: Capitulo) -> str:
    P = d.get("presidente.json")
    checar(
        d,
        "presidente.json",
        ["nacional.votos", "nacional.pct", "ufs", "nacional.comparacao"],
    )
    n = P["nacional"]
    h = secao(
        cap,
        "Flávio na frente.<br><em>2º turno com Lula.</em>",
        f"{num(n['pct']['flavio'], 2)}% contra {num(n['pct']['lula'], 2)}% dos válidos, "
        f"{inteiro(n['diferenca_votos'])} votos de diferença, 100% das seções.",
    )
    h += T.abertura_a(P) + fig("placar_candidatos", d)
    h += T.abertura_b(P) + fig("mapa_vencedor_uf", d)
    h += T.abertura_c(P) + "</section>"
    return h


# ------------------------------------------------------------------ 02


def r_noite(d: Dados, cap: Capitulo) -> str:
    L = d.get(FONTE_BANCO)
    checar(
        d,
        FONTE_BANCO,
        ["nacional.versoes", "travamentos.nacional", "conclusao_ufs"],
    )
    linhas = [r for r in versoes(L) if r["gerado_brt"] >= "2026-10-04 17:00"]
    par = paradas_nacionais(L)
    h = secao(
        cap,
        "A noite<br><em>minuto a minuto.</em>",
        f"{inteiro(L['nacional']['n_versoes_genuinas'])} versões do arquivo nacional, três paradas no pico e um lote represado.",
    )
    h += T.noite_a(L, linhas) + fig("acumulado_noite", d)
    h += T.noite_b(par) + fig("lotes_noite", d)
    h += T.noite_c(linhas) + fig("mapa_hora_100", d)
    h += T.noite_d(L) + "</section>"
    return h


# ------------------------------------------------------------------ 03


def r_falha(d: Dados, cap: Capitulo) -> str:
    L = d.get(FONTE_BANCO)
    N = d.get("noticias_noite.json")
    linhas = versoes(L)
    par = paradas_nacionais(L)
    h = secao(
        cap,
        "A falha do TSE.<br><em>Três camadas, três fontes.</em>",
        "O que o banco prova, o que o aplicativo oficial mostrava e o que o TSE disse. Nenhuma hora fundida com outra.",
    )
    pg = L["pausa_geral"]["lacunas"][0]
    banco = "Banco da casa"
    linhas_t = [
        [
            f"{hora(t['de_brt'], True)} a {hora(t['ate_brt'], True)}",
            banco,
            f"Arquivo nacional sem versão nova por {num(t['minutos'], 1)} min, de {num(t['pst_de'], 2)}% a "
            f"{num(t['pst_ate'], 2)}% das seções",
            "linha_do_tempo.json, travamentos.nacional",
        ]
        for t in par
    ]
    linhas_t.append(
        [
            f"{hora(pg['de_brt'], True)} a {hora(pg['ate_brt'], True)}",
            banco,
            f"Nenhum arquivo de resultado de nenhum cargo, em nenhum nível ({num(pg['minutos'], 1)} min)",
            "linha_do_tempo.json, pausa_geral",
        ]
    )
    linhas_t.append(
        [
            HORA_APP_OFICIAL,
            "Aplicativo oficial",
            T.falha_app_curta(L, linhas, HORA_APP_OFICIAL),
            "Leitura da tela pela casa; banco",
        ]
    )
    principal = T.falha_principal_imprensa(N)
    if principal:
        linhas_t.append(
            [
                escape(principal.get("hora_se_houver") or "sem hora"),
                "Imprensa e TSE",
                "Nunes Marques, segundo a imprensa: “congestionamento de dados”. Versão oficial, como reportada: fluxo acima "
                "do normal, isolamento temporário de sistemas, totalização não afetada.",
                f'<a href="{escape(principal["url"])}">{escape(principal["veiculo"])}</a>',
            ]
        )
    h += tabela(
        ["Hora (Brasília)", "Camada", "Fato", "Fonte"],
        linhas_t,
        "Horas de geração do TSE, exceto a linha do aplicativo e a da imprensa, que seguem o carimbo da fonte.",
    )
    h += T.falha_a(L, par) + fig("divergencia_nacional", d)
    h += T.falha_correcao(L) + fig("latencia_hora", d)
    h += T.falha_b(par, L) + T.falha_juizo(par)
    h += TA.bloco(d) + "</section>"
    return h


# ------------------------------------------------------------------ 04


def r_regioes(d: Dados, cap: Capitulo) -> str:
    P = d.get("presidente.json")
    checar(d, "presidente.json", ["regioes", "ufs", "capitais"])
    h = secao(
        cap,
        "Nordeste, Norte<br><em>e Centro-Sul.</em>",
        "2026 contra 2022, mesmo cargo, mesmo turno. Flávio contra Bolsonaro, Lula contra Lula.",
    )
    h += T.regioes_a(P) + fig("regioes_2022_2026", d)
    h += T.regioes_b(P) + fig("dispersao_municipios", d)
    h += T.regioes_c(P) + fig("mapa_swing_uf", d)
    h += T.regioes_d(P) + fig("capitais_interior", d)
    h += T.regioes_e(P) + CMP.regioes(d) + fig("comparecimento_regioes", d)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 05


def r_exterior(d: Dados, cap: Capitulo) -> str:
    E = d.get("exterior.json")
    P = d.get("presidente.json")
    checar(d, "exterior.json", ["total", "paises", "continentes", "hora_local"])
    h = secao(
        cap,
        "Exterior.<br><em>Lula vence; a votação encolhe.</em>",
        f"{E['total']['cidades']} cidades, {E['total']['paises']} países, comparecimento de {num(E['total']['pct_comparecimento'], 2)}%.",
    )
    h += T.exterior_a(E, P) + fig("mapa_mundi_exterior", d)
    h += T.exterior_b(E) + fig("exterior_continentes", d)
    h += T.exterior_c(E) + "</section>"
    return h
