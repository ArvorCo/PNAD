"""Capítulos 01 a 05 do dossiê da apuração: resultado, noite, falha, regiões, exterior.

Cada capítulo é uma sequência de figuras do catálogo com, entre elas, um ou dois
parágrafos curtos. Os números saem dos JSONs, por `pagina_texto`.
"""

from __future__ import annotations

from . import pagina_comparacao as CMP
from . import pagina_texto as T
from . import pagina_texto_arquitetura as TA
from . import pagina_texto_noite_regioes as TNR
from .pagina_comum import (
    Capitulo,
    Dados,
    checar,
    inteiro,
    limites,
    num,
    secao,
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
    h += T.teses(d) + fig("placar_candidatos", d)
    h += T.abertura_b(P) + fig("mapa_vencedor_uf", d) + "</section>"
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
    h = secao(
        cap,
        "A noite<br><em>minuto a minuto.</em>",
        f"{inteiro(L['nacional']['n_versoes_genuinas'])} versões do arquivo nacional, três paradas no pico e um lote represado.",
    )
    h += T.noite_a(L, linhas) + fig("acumulado_noite", d) + fig("lotes_noite", d)
    h += fig("mapa_hora_100", d) + T.noite_d(L)
    h += TNR.noite_por_regiao(d)
    h += limites(
        [
            "A hora é a de geração de cada versão pelo TSE, não a de leitura pelo coletor.",
            "A noite por região soma os 28 arquivos de UF de presidente, não o arquivo nacional.",
            "Voto de seção já totalizada não muda: toda variação da vantagem é mistura do que entrou.",
        ]
    )
    return h + "</section>"


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
    h += T.falha_abre(L, par) + fig("marcos_falha", d)
    h += T.falha_camadas(L, linhas, N, HORA_APP_OFICIAL) + T.falha_juizo(par, L)
    h += fig("divergencia_nacional", d) + TNR.painel(d)
    h += T.falha_correcao() + fig("latencia_hora", d)
    h += TNR.estados_lentos(d)
    h += TA.bloco(d)
    h += limites(
        [
            "A latência inclui o intervalo de sondagem do coletor: é teto da demora de publicação, não medida dela.",
            "O carimbo de recebimento pode ser aplicado por um componente posterior à recepção; os arquivos não dizem qual.",
            "A régua de 2022 é a primeira totalização parcial de cada seção; a de 2026, a versão do arquivo de cada UF.",
            "Nenhum documento descreve a arquitetura de 2026: o mecanismo é inferência, e a causa, hipótese.",
        ]
    )
    return h + "</section>"


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
