"""Figuras do capítulo "Exterior" do dossiê do 2º turno.

- ``fig_mapa``: bolhas por cidade (área pelos válidos, cor do líder) com ``mapa_mundo``;
- ``fig_continentes``: Flávio × Lula por continente, com o 1º turno e o comparecimento;
- ``tabela_cidades`` e ``tabela_hora_local``: maiores cidades e as últimas a fechar,
  com a hora de Brasília e a da totalização impressa no relógio local.

Coordenadas das cidades: ``apuracao/public/geo/exterior_cidades.json`` (código TSE).
"""

from __future__ import annotations

import json
from functools import cache

from apuracao_2026.pagina_comum import (
    FLAVIO,
    INK,
    LULA,
    MUTED,
    ROOT,
    inteiro,
    num,
    tabela,
)
from apuracao_2026.pagina_fig_base import (
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    nome_bonito,
    r,
    sobre,
    svg_abre,
    t,
)
from apuracao_2026.pagina_mapas import mapa_mundo

GEO = ROOT / "apuracao/public/geo/exterior_cidades.json"


@cache
def coordenadas() -> dict[str, tuple[float, float]]:
    if not GEO.exists():
        return {}
    return {
        str(c["cd"]): (c["lat"], c["lon"])
        for c in json.loads(GEO.read_text(encoding="utf-8"))
        if c.get("lat") is not None
    }


def cidades_mapa(E: dict) -> list[dict]:
    geo = coordenadas()
    out = []
    for c in E["cidades"]:
        ll = geo.get(str(c.get("cd_tse")))
        if not ll:
            continue
        pf, pl = c.get("pct_flavio") or 0, c.get("pct_lula") or 0
        out.append(
            {
                "lat": ll[0],
                "lon": ll[1],
                "nome": c.get("nome", ""),
                "pais_nome": c.get("pais_nome", ""),
                "validos": c.get("validos") or 0,
                "lider": "flavio" if pf > pl else "lula" if pl > pf else None,
                "pct": {"flavio": pf, "lula": pl},
            }
        )
    return out


def fig_mapa(E: dict) -> str:
    cid = cidades_mapa(E)
    svg = mapa_mundo(
        cid,
        "Exterior: Flávio × Lula por cidade no 2º turno",
        "Bolhas por cidade com área proporcional aos válidos; azul onde Flávio lidera, vermelho onde Lula lidera.",
        largura=1100,
        altura=470,
        rotulos=12,
    )
    legenda = (
        f"{inteiro(len(cid))} de {inteiro(len(E['cidades']))} cidades com coordenada. Passe o ponteiro "
        "na bolha para ver o placar. Fonte: exterior.json e apuracao/public/geo/exterior_cidades.json."
    )
    return figura_html(
        "exterior_mapa", svg, legenda, Tips(), modo="scroll", minw=760, dim=False
    )


def fig_continentes(E: dict) -> str:
    conts = sorted(E["continentes"], key=lambda c: -(c.get("validos") or 0))
    w, esq, dir_ = 900, 210, 200
    topo, passo = 50, 52
    h = topo + passo * len(conts) + 20
    x = escala(0, 100, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Exterior por continente: Flávio × Lula no 2º turno",
            "Barra de 100% dos válidos por continente, Flávio à esquerda e Lula à direita; à direita, o "
            "comparecimento no 1º e no 2º turno.",
        )
    ]
    out.append(t(esq, 26, "parte de cada um nos válidos do 2º turno", 13, MUTED))
    out.append(t(w - dir_ + 16, 26, "comparecimento 1º → 2º", 13, MUTED))
    tips = Tips()
    for i, c in enumerate(conts):
        y = topo + i * passo
        pf, pl = c.get("pct_flavio") or 0, c.get("pct_lula") or 0
        partes = [
            t(esq - 10, y + 16, c["continente"], 14, INK, "end", "600"),
            t(
                esq - 10,
                y + 33,
                f"{inteiro(c.get('validos'))} válidos",
                12,
                MUTED,
                "end",
            ),
            r(x(0), y + 2, x(pf) - x(0), 30, FLAVIO),
            r(x(pf), y + 2, x(100) - x(pf), 30, LULA),
            t(x(0) + 6, y + 22, f"{num(pf, 1)}%", 13, sobre(FLAVIO), weight="600"),
            t(x(100) - 6, y + 22, f"{num(pl, 1)}%", 13, sobre(LULA), "end", "600"),
            t(
                w - dir_ + 16,
                y + 22,
                f"{num(c.get('t1_pct_comparecimento'), 1)}% → {num(c.get('pct_comparecimento'), 1)}%",
                13,
                INK,
                mono=True,
            ),
        ]
        if c.get("t1_pct_flavio") is not None and c.get("t1_pct_lula"):
            p1 = 100 * c["t1_pct_flavio"] / (c["t1_pct_flavio"] + c["t1_pct_lula"])
            partes.append(
                f'<line x1="{x(p1):.1f}" y1="{y - 2}" x2="{x(p1):.1f}" y2="{y + 36}" '
                'stroke="#ffffff" stroke-width="2.4"/>'
                f'<line x1="{x(p1):.1f}" y1="{y - 2}" x2="{x(p1):.1f}" y2="{y + 36}" '
                f'stroke="{INK}" stroke-width="1.2" stroke-dasharray="3 2"/>'
            )
        kk = tips.add(
            ficha(
                c["continente"],
                f"{inteiro(c.get('cidades'))} cidades",
                [
                    ("Flávio, 2º turno", f"{num(pf, 2)}%"),
                    ("Lula, 2º turno", f"{num(pl, 2)}%"),
                    (
                        "Flávio, 1º turno (válidos)",
                        f"{num(c.get('t1_pct_flavio'), 2)}%",
                    ),
                    ("Lula, 1º turno (válidos)", f"{num(c.get('t1_pct_lula'), 2)}%"),
                    (
                        "comparecimento 2º turno",
                        f"{num(c.get('pct_comparecimento'), 2)}%",
                    ),
                    (
                        "comparecimento 1º turno",
                        f"{num(c.get('t1_pct_comparecimento'), 2)}%",
                    ),
                ],
            )
        )
        out.append(hit("".join(partes) + area(0, y, w, passo), kk, foco=True))
    out.append("</svg>")
    leg = legenda_html(
        [
            ("Flávio", FLAVIO),
            ("Lula", LULA),
            ("tracejado: Flávio entre os dois no 1º turno", "#ffffff"),
        ]
    )
    legenda = (
        "No 1º turno havia outros candidatos; o tracejado é a parte de Flávio entre os dois finalistas "
        "naquele turno. Fonte: exterior.json (continentes)."
    )
    return figura_html(
        "exterior_continentes",
        "".join(out),
        legenda,
        tips,
        modo="scroll",
        minw=700,
        apos=leg,
    )


def _hora_local(s: str | None) -> str:
    if not s:
        return "s/d"
    return s.strip().split(" ")[-1][:5]


def tabela_cidades(E: dict, n: int = 12) -> str:
    cid = sorted(E["cidades"], key=lambda c: -(c.get("validos") or 0))[:n]
    linhas = [
        [
            nome_bonito(c.get("nome", "")),
            c.get("pais_nome", ""),
            inteiro(c.get("validos")),
            f"{num(c.get('pct_flavio'), 1)}%",
            f"{num(c.get('pct_lula'), 1)}%",
            f"{num(c.get('t1_pct_comparecimento'), 1)}% → {num(c.get('pct_comparecimento'), 1)}%",
        ]
        for c in cid
    ]
    return tabela(
        ["cidade", "país", "válidos", "Flávio", "Lula", "comparecimento 1º → 2º"],
        linhas,
        f"As {n} cidades com mais votos válidos no exterior.",
    )


def _placar(c: dict) -> str:
    if not c.get("validos"):
        return "sem voto válido"
    return f"{num(c.get('pct_flavio'), 1)}% × {num(c.get('pct_lula'), 1)}%"


def tabela_hora_local(E: dict, n: int = 10) -> str:
    ult = (E.get("ultimas_a_fechar") or [])[:n]
    linhas = [
        [
            nome_bonito(c.get("nome", "")),
            c.get("pais_nome", ""),
            c.get("fechou_gerado_brt") or c.get("fechou_hhmm") or "s/d",
            _hora_local(c.get("totalizacao_impressa_local")),
            _placar(c),
        ]
        for c in ult
    ]
    return tabela(
        [
            "cidade",
            "país",
            "fechou (Brasília)",
            "totalização impressa (hora local)",
            "Flávio × Lula",
        ],
        linhas,
        "As últimas cidades a fechar: hora de geração do arquivo pelo TSE e relógio local do boletim.",
    )
