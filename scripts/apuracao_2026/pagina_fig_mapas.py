"""Mapas do catálogo: vencedor por UF, hora dos 100%, governadores, swing municipal,
mundo do exterior e zonas atípicas.

Malha por UF da casa (`voto_util_mapa`, IBGE mínima); municípios em
`apuracao/public/geo/mun/{UF}.geojson`; mundo em `apuracao/public/geo/mundo.geojson`.
Mapa nunca rola: ocupa a largura da figura (`modo="fit"` ou `"full"`).
"""

from __future__ import annotations

import math
from functools import cache
from html import escape
from itertools import pairwise

import voto_util_mapa as VM

from .pagina_comum import NOME_UF, inteiro, num
from .pagina_fig_base import (
    FLAVIO,
    LULA,
    MUTED,
    PAPER,
    Tips,
    botoes,
    campo_nome,
    chip,
    cor_campo,
    dado,
    ficha,
    figura_html,
    hit,
    legenda_html,
    minutos,
    nome_bonito,
    pct,
    pp,
    registra,
    sobre,
    svg_abre,
    t,
    tabela_linhas,
)
from .pagina_mapas import LAT1, LON0, LON1, _aneis, _geo_municipal, _mundo

MW, MH = 640, 600
AZUIS = ["#dbe5f3", "#a7c0e5", "#2f63ad", "#123f7e"]
VERMELHOS = ["#f4d6ce", "#e5a596", "#a8331f", "#6e1a10"]
FAIXAS = [5, 15, 30]
ROT_FAIXA = ["até 5 pp", "5 a 15 pp", "15 a 30 pp", "30 pp ou mais"]
HORAS = ["#ece6d4", "#c5dccf", "#7fb19e", "#2f7a66", "#0d3f35"]
CORTES_HORA = [21 * 60, 22 * 60, 23 * 60, 24 * 60]
ROT_HORA = ["antes das 21h", "21h a 22h", "22h a 23h", "23h a 00h", "depois de 00h"]
DIVERGENTE = [
    "#8f2618",
    "#d9775f",
    "#f0cfc4",
    "#ece7da",
    "#bfd0ea",
    "#5d8bcb",
    "#123f7e",
]
CORTES_SWING = [-10, -5, -2, 2, 5, 10]
ROT_SWING = [
    "Lula +10",
    "Lula +5 a 10",
    "Lula +2 a 5",
    "−2 a +2",
    "Flávio +2 a 5",
    "Flávio +5 a 10",
    "Flávio +10",
]


def caminho(aneis, proj, tol: float = 1.4) -> str:
    """Contorno decimado no pixel, coordenadas inteiras e passos relativos."""
    partes = []
    for anel in aneis:
        pts, ult = [], None
        for lon, lat in anel:
            x, y = proj(lon, lat)
            if ult is None or abs(x - ult[0]) + abs(y - ult[1]) >= tol:
                pts.append((round(x), round(y)))
                ult = (x, y)
        limpos = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        if len(limpos) < 3:
            continue
        x0, y0 = limpos[0]
        passos = []
        for (xa, ya), (xb, yb) in pairwise(limpos):
            passos.append(f"{xb - xa} {yb - ya}")
        partes.append(f"M{x0} {y0}l" + " ".join(passos) + "z")
    return "".join(partes)


@cache
def paths_uf() -> dict[str, dict]:
    """Contornos das UFs na projeção da casa, decimados."""
    base = VM.paths(MW, MH)
    proj, _ = VM._proj(MW, MH, 10.0)
    out = {}
    for uf, aneis in VM._features().items():
        out[uf] = dict(
            base[uf], d=caminho([[(p[0], p[1]) for p in a] for a in aneis], proj, 0.9)
        )
    return out


def faixa(v: float, cortes: list[float]) -> int:
    return sum(v >= c for c in cortes)


def mapa_ufs(
    fill: dict[str, str],
    chaves: dict[str, str],
    titulo: str,
    desc: str,
    leg: str = "",
    rotulo: dict[str, str] | None = None,
    chip_em: set[str] | None = None,
    defs: str = "",
) -> str:
    """Coroplético por UF com alvo de ficha em cada estado."""
    geo = paths_uf()
    out = [svg_abre(MW, MH, titulo, desc), defs]
    labels = []
    for uf, g in sorted(geo.items()):
        cor = fill.get(uf, "#d8d4c8")
        forma = (
            f'<path d="{g["d"]}" fill="{cor}" stroke="{PAPER}" stroke-width="1.1" '
            'stroke-linejoin="round"/>'
        )
        k = chaves.get(uf)
        out.append(hit(forma, k) if k else forma)
        texto = (rotulo or {}).get(uf, uf)
        lx, ly = g["label"]
        if g["fora"] or uf in (chip_em or set()):
            if g["fora"]:
                ax, ay = g["anchor"]
                labels.append(
                    f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{lx - 3:.1f}" y2="{ly - 4:.1f}" '
                    f'stroke="{MUTED}" stroke-width="0.8"/>'
                )
            labels.append(
                chip(lx - 4, ly, texto, 13, "start" if g["fora"] else "middle")
            )
        else:
            labels.append(
                t(
                    lx,
                    ly + 5,
                    texto,
                    13,
                    sobre(cor),
                    "middle",
                    "700",
                    extra=' pointer-events="none"',
                )
            )
    out.append(f'<g pointer-events="none">{"".join(labels)}</g>{leg}</svg>')
    return "".join(out)


# ------------------------------------------------------------------ 01 vencedor


@registra("mapa_vencedor_uf")
def mapa_vencedor_uf(d, **_op) -> str:
    P = dado(d, "presidente")
    tips, fill, chaves = Tips(), {}, {}
    n_f = n_l = 0
    for u in P["ufs"]:
        uf = u["uf"]
        if uf == "ZZ":
            continue
        pf, pl = u["pct"]["flavio"], u["pct"]["lula"]
        m = pf - pl
        lider = "flavio" if m > 0 else "lula"
        n_f += lider == "flavio"
        n_l += lider == "lula"
        fill[uf] = (AZUIS if lider == "flavio" else VERMELHOS)[faixa(abs(m), FAIXAS)]
        t1 = u["r2022"]["t1"]["pct"]
        t2 = u["r2022"]["t2"]["pct"]
        chaves[uf] = tips.add(
            ficha(
                f"{u['nome']} ({uf})",
                "Flávio vence" if lider == "flavio" else "Lula vence",
                [
                    ("Flávio", f"{pct(pf)} · {inteiro(u['votos']['flavio'])}"),
                    ("Lula", f"{pct(pl)} · {inteiro(u['votos']['lula'])}"),
                    ("Margem", f"{pp(m)} · {inteiro(abs(u['margem_votos']))} votos"),
                    (
                        "2022, 1º turno",
                        f"Bolsonaro {pct(t1['bolsonaro'], 1)} × Lula {pct(t1['lula'], 1)}",
                    ),
                    (
                        "2022, 2º turno",
                        f"Bolsonaro {pct(t2['bolsonaro'], 1)} × Lula {pct(t2['lula'], 1)}",
                    ),
                    (
                        "Seções",
                        f"{inteiro(u['secoes'])} de {inteiro(u['secoes_total'])}",
                    ),
                ],
            )
        )
    itens = [(f"Flávio, {ROT_FAIXA[i]}", AZUIS[i]) for i in range(4)]
    itens += [(f"Lula, {ROT_FAIXA[i]}", VERMELHOS[i]) for i in range(4)]
    svg = mapa_ufs(
        fill,
        chaves,
        "Vencedor por UF, presidente, 1º turno de 2026",
        f"Flávio vence em {n_f} UFs e Lula em {n_l}; a cor mais escura marca margem maior.",
    )
    legenda = (
        f"Flávio Bolsonaro venceu em {n_f} UFs e Lula em {n_l}. Tom pela margem nos válidos. "
        "Fonte: arquivos de UF do TSE a 100% (presidente.json)."
    )
    leg = legenda_html(itens, "Margem nos válidos")
    return figura_html("mapa_vencedor_uf", svg, legenda, tips, modo="fit", apos=leg)


# ------------------------------------------------------------------ 02 hora dos 100%


@registra("mapa_hora_100")
def mapa_hora_100(d, **_op) -> str:
    L = dado(d, "linha_do_tempo")
    tardias: dict[str, list] = {}
    for m in L["secoes_tardias"]["municipios"]:
        tardias.setdefault(m["uf"], []).append(m)
    fuso = {f["uf"]: f for f in L["fuso_da_totalizacao"]["por_uf"]}
    tips, fill, chaves, rot = Tips(), {}, {}, {}
    ordem = sorted(L["conclusao_ufs"], key=lambda c: c["gerado_brt"])
    for c in ordem:
        uf = c["uf"]
        if uf == "ZZ":
            continue
        mm = minutos(c["gerado_brt"])
        fill[uf] = HORAS[faixa(mm, CORTES_HORA)]
        tt = tardias.get(uf, [])
        linhas = [
            (
                "Arquivo a 100% (Brasília)",
                c["gerado_brt"][11:16]
                + (" de 05/10" if c["gerado_brt"][8:10] == "05" else " de 04/10"),
            ),
            ("Lido pelo coletor", c["capturado_brt"][11:19]),
            (
                "Totalização impressa",
                f"{c['totalizacao_impressa'][-8:-3]} (hora local)",
            ),
            ("Ordem de chegada", f"{ordem.index(c) + 1}ª de {len(ordem)}"),
        ]
        if uf in fuso:
            linhas.append(
                ("Fuso lido no arquivo", f"{num(fuso[uf]['mediana_min'], 0)} min")
            )
        if tt:
            linhas.append(
                (
                    "Seções depois de 00h",
                    f"{sum(m['secoes'] for m in tt)} em {', '.join(nome_bonito(m['nome']) for m in tt)}",
                )
            )
        chaves[uf] = tips.add(
            ficha(f"{NOME_UF.get(uf, uf)} ({uf})", "presidente a 100%", linhas)
        )
        rot[uf] = uf
    primeira, ultima = ordem[0], [c for c in ordem if c["uf"] != "ZZ"][-1]
    svg = mapa_ufs(
        fill,
        chaves,
        "Hora em que cada UF chegou a 100% das seções",
        f"{primeira['uf']} fechou primeiro, às {primeira['gerado_brt'][11:16]}; {ultima['uf']} por último, "
        f"às {ultima['gerado_brt'][11:16]}.",
        rotulo=rot,
    )
    legenda = (
        f"Hora de Brasília em que o TSE gerou o arquivo presidencial de cada UF com todas as seções. "
        f"{NOME_UF[primeira['uf']]} foi a primeira ({primeira['gerado_brt'][11:16]}); "
        f"{NOME_UF[ultima['uf']]}, a última ({ultima['gerado_brt'][11:16]} de 05/10). "
        "A hora impressa no arquivo é local; a ficha mostra as duas. Fonte: linha_do_tempo.json."
    )
    leg = legenda_html(
        list(zip(ROT_HORA, HORAS, strict=True)), "Arquivo da UF a 100% (Brasília)"
    )
    return figura_html("mapa_hora_100", svg, legenda, tips, modo="fit", apos=leg)


# ------------------------------------------------------------------ 09 governadores


@registra("governadores_mapa")
def governadores_mapa(d, **_op) -> str:
    G = dado(d, "governadores")
    tips, fill, chaves, chips = Tips(), {}, {}, set()
    defs = ["<defs>"]
    for campo in ("esquerda", "centro-esquerda", "centro", "centro-direita", "direita"):
        cor = cor_campo(campo)
        defs.append(
            f'<pattern id="gv-{campo}" width="8" height="8" patternUnits="userSpaceOnUse" '
            f'patternTransform="rotate(45)"><rect width="8" height="8" fill="#f3eee2"/>'
            f'<rect width="3" height="8" fill="{cor}"/></pattern>'
        )
    defs.append("</defs>")
    n1 = n2 = 0
    for u in G["ufs"]:
        uf = u["uf"]
        cands = u["candidatos"]
        lider = cands[0]
        if u["decisao"] == "eleito":
            n1 += 1
            fill[uf] = cor_campo(lider["campo"])
            sub = "eleito no 1º turno"
        else:
            n2 += 1
            fill[uf] = f"url(#gv-{lider['campo'] or 'centro'})"
            chips.add(uf)
            sub = "2º turno"
        linhas = [
            (
                nome_bonito(c["nome"]),
                f"{c['partido']} · {campo_nome(c['campo'])} · {pct(c['pct'])}",
            )
            for c in cands
        ]
        if u.get("terceiro"):
            c = u["terceiro"]
            linhas.append(
                ("3º: " + nome_bonito(c["nome"]), f"{c['partido']} · {pct(c['pct'])}")
            )
        linhas.append(("Fonte", "TSE" if u["fonte"] == "tse" else "provisória"))
        chaves[uf] = tips.add(ficha(f"{NOME_UF.get(uf, uf)} ({uf})", sub, linhas))
    itens = [
        (campo_nome(c), cor_campo(c))
        for c in ("esquerda", "centro", "centro-direita", "direita")
    ]
    svg = mapa_ufs(
        fill,
        chaves,
        "Governadores: eleitos no 1º turno e disputas de 2º turno",
        f"{n1} governadores eleitos no 1º turno, por campo; {n2} UFs vão ao 2º turno.",
        chip_em=chips,
        defs="".join(defs),
    )
    legenda = (
        f"{n1} UFs decidiram o governo no 1º turno (cor cheia do campo do eleito) e {n2} vão ao 2º turno "
        "(hachura na cor do líder). Campo é classificação editorial da casa. Fonte: governadores.json."
    )
    itens.append(
        (
            "vai ao 2º turno (hachura na cor do líder)",
            "repeating-linear-gradient(45deg,#1457aa 0 3px,#f3eee2 3px 8px)",
        )
    )
    leg = legenda_html(itens, "Eleito no 1º turno, por campo")
    return figura_html("governadores_mapa", svg, legenda, tips, modo="fit", apos=leg)


# ------------------------------------------------------------------ 04 swing municipal

UFS_SWING = ["SP", "MG", "BA", "PE"]


def cor_swing(v: float | None) -> str:
    return "#d8d4c8" if v is None else DIVERGENTE[faixa(v, CORTES_SWING)]


@registra("mapa_swing_uf")
def mapa_swing_uf(d, **_op) -> str:
    P = dado(d, "presidente")
    mun = {m["ibge"]: m for m in tabela_linhas(P["municipios"]) if m["uf"] in UFS_SWING}
    w, h = 640, 600
    tips = Tips()
    linhas, grupos = [], []
    for k, uf in enumerate(UFS_SWING):
        geo = _geo_municipal(uf)
        if geo is None:
            raise KeyError(f"apuracao/public/geo/mun/{uf}.geojson")
        feats = geo["features"]
        lons = [c[0] for f in feats for a in _aneis(f["geometry"]) for c in a]
        lats = [c[1] for f in feats for a in _aneis(f["geometry"]) for c in a]
        cosl = math.cos(math.radians((min(lats) + max(lats)) / 2))
        sx, sy = (max(lons) - min(lons)) * cosl, max(lats) - min(lats)
        pad, topo, base = 10, 8, 12
        esc = min((w - 2 * pad) / sx, (h - topo - base) / sy)
        ox = pad + ((w - 2 * pad) - sx * esc) / 2
        oy = topo + ((h - topo - base) - sy * esc) / 2
        lon0, lat1 = min(lons), max(lats)

        def proj(lon, lat, lon0=lon0, lat1=lat1, cosl=cosl, esc=esc, ox=ox, oy=oy):
            return ox + (lon - lon0) * cosl * esc, oy + (lat1 - lat) * esc

        partes = []
        for f in feats:
            cod = str(f.get("properties", {}).get("codarea", ""))
            m = mun.get(cod)
            dd = caminho(_aneis(f["geometry"]), proj, 1.6)
            if not dd:
                continue
            v = m.get("virada_margem_pp") if m else None
            i = len(linhas)
            if m:
                linhas.append(
                    [
                        f"{nome_bonito(m['nome'])} ({uf})",
                        pp(v, 1),
                        f"{num(m['pct_flavio'], 1)} × {num(m['pct_bolsonaro_2022_1t'], 1)}",
                        f"{num(m['pct_lula'], 1)} × {num(m['pct_lula_2022_1t'], 1)}",
                        inteiro(m["eleitores"]),
                    ]
                )
                partes.append(
                    f'<path class="hit" data-k="r{i}" d="{dd}" fill="{cor_swing(v)}"/>'
                )
            else:
                partes.append(f'<path d="{dd}" fill="#d8d4c8"/>')
        mostra = "" if k == 0 else ' display="none"'
        grupos.append(
            f'<g data-alt-show="{uf}" stroke="{PAPER}" stroke-width="0.4"{mostra}>{"".join(partes)}</g>'
        )
    tips.tabela(
        [
            "Município",
            "Virada da margem",
            "Flávio 2026 × Bolsonaro 2022, %",
            "Lula 2026 × Lula 2022, %",
            "Eleitores 2026",
        ],
        linhas,
        nota="2022 = 1º turno; virada = margem de 2026 menos margem de 2022",
    )
    svg = (
        svg_abre(
            w,
            h,
            "Virada da margem por município em SP, MG, BA e PE",
            "Variação da margem Flávio menos Lula em 2026 contra Bolsonaro menos Lula no 1º turno de 2022.",
        )
        + "".join(grupos)
        + "</svg>"
    )
    abas = botoes([(u, NOME_UF[u]) for u in UFS_SWING], "SP", "Estado", "tab")
    legenda = (
        "Cada município pela virada da margem: (Flávio − Lula em 2026) − (Bolsonaro − Lula no 1º turno de 2022). "
        "Azul andou para Flávio; vermelho, para Lula. Abas trocam o estado. Fonte: presidente.json (municípios) e malha do IBGE."
    )
    leg = legenda_html(
        list(zip(ROT_SWING, DIVERGENTE, strict=True)), "Virada da margem, em pontos"
    )
    return figura_html(
        "mapa_swing_uf", svg, legenda, tips, controles=abas, modo="fit", apos=leg
    )


# ------------------------------------------------------------------ 05 mundo


@registra("mapa_mundi_exterior")
def mapa_mundi_exterior(d, **_op) -> str:
    E = dado(d, "exterior")
    cidades = [c for c in E["cidades"] if c.get("lat") is not None]
    w = 1100
    lat0 = -56.0
    esc = w / (LON1 - LON0)
    h = round(12 + (LAT1 - lat0) * esc)
    ox = (w - (LON1 - LON0) * esc) / 2

    def proj(lon, lat):
        return ox + (lon - LON0) * esc, 6 + (LAT1 - lat) * esc

    out = [
        svg_abre(
            w,
            h,
            "Exterior: voto por cidade",
            "Bolhas por cidade com área proporcional aos válidos; azul onde Flávio lidera, vermelho onde Lula lidera.",
        )
    ]
    mundo = _mundo()
    if mundo:
        partes = [caminho(_aneis(f["geometry"]), proj, 1.5) for f in mundo["features"]]
        out.append(
            f'<path d="{"".join(p for p in partes if p)}" fill="#e3ddce" stroke="{PAPER}" stroke-width="0.5"/>'
        )
    vmax = max(c.get("validos") or 0 for c in cidades) or 1
    tips = Tips()
    linhas = []
    for c in sorted(cidades, key=lambda c: -(c.get("validos") or 0)):
        x, y = proj(c["lon"], c["lat"])
        raio = 2.5 + 22 * math.sqrt((c.get("validos") or 0) / vmax)
        cor = (
            FLAVIO
            if c.get("lider") == "flavio"
            else LULA if c.get("lider") == "lula" else "#8a8a80"
        )
        i = len(linhas)
        p = c.get("pct", {})
        linhas.append(
            [
                nome_bonito(c["nome"]),
                c.get("pais_nome", ""),
                inteiro(c["eleitores"]),
                f"{inteiro(c['comparecimento'])} ({pct(c['pct_comparecimento'], 1)})",
                pct(p.get("flavio"), 1),
                pct(p.get("lula"), 1),
                inteiro(c["validos"]),
                _hora_local(c.get("totalizacao_impressa")),
            ]
        )
        out.append(
            f'<circle class="hit" data-k="r{i}" cx="{x:.1f}" cy="{y:.1f}" r="{raio:.1f}" fill="{cor}" '
            f'fill-opacity="0.62" stroke="{cor}" stroke-width="1"/>'
        )
    tips.tabela(
        [
            "Cidade",
            "País",
            "Eleitorado",
            "Votantes",
            "Flávio",
            "Lula",
            "Válidos",
            "Totalização (hora local)",
        ],
        linhas,
        sub=1,
    )
    usados: list[tuple[float, float]] = []
    for c in sorted(cidades, key=lambda c: -(c.get("validos") or 0))[:9]:
        x, y = proj(c["lon"], c["lat"])
        if any(abs(x - a) < 110 and abs(y - b) < 22 for a, b in usados):
            continue
        usados.append((x, y))
        # o mapa-múndi encolhe a um terço no celular: o rótulo some abaixo de 720 px
        # (a ficha continua dando o nome ao tocar)
        out.append(
            f'<g class="so-largo" pointer-events="none">{chip(x + 10, y - 8, nome_bonito(c["nome"]), 13)}</g>'
        )
    out.append("</svg>")
    T = E["total"]
    legenda = (
        f"{T['cidades']} cidades em {T['paises']} países; comparecimento de {pct(T['pct_comparecimento'], 1)}. "
        "A hora de totalização que o TSE grava é a hora local da cidade. Fonte: exterior.json."
    )
    leg = legenda_html(
        [("Flávio lidera a cidade", FLAVIO), ("Lula lidera a cidade", LULA)],
        "Área da bolha pelos votos válidos",
    )
    return figura_html(
        "mapa_mundi_exterior", "".join(out), legenda, tips, modo="full", apos=leg
    )


def _hora_local(s: str | None) -> str:
    if not s:
        return "s/d"
    return f"{s[-8:-3]} de {s[:5]}"


# ------------------------------------------------------------------ 12 anomalias

COR_HIPOTESE = "#7d5b00"
COR_EXPLICADA = "#0f7f5f"


def _hipotese(z: dict) -> bool:
    return any("hipótese" in e for e in z.get("explicacao_provavel", []))


@registra("mapa_anomalias")
def mapa_anomalias(d, **_op) -> str:
    A = dado(d, "anomalias")
    topo = A["topo"][:50]
    geo = paths_uf()
    proj, _ = VM._proj(MW, MH, 10.0)
    out = [
        svg_abre(
            MW,
            MH,
            "As 50 zonas mais atípicas do país",
            "Zonas com maior escore de atipicidade dentro da própria UF; tamanho pelo escore, cor pela explicação.",
        )
    ]
    for _uf, g in sorted(geo.items()):
        out.append(
            f'<path d="{g["d"]}" fill="#e7e1d2" stroke="#b9b29f" stroke-width="0.8"/>'
        )
    emin = min(z["escore"] for z in topo)
    emax = max(z["escore"] for z in topo)
    tips = Tips()
    n_h = 0
    for z in sorted(topo, key=lambda z: z["escore"]):
        x, y = proj(z["lon"], z["lat"])
        raio = 5 + 9 * (z["escore"] - emin) / ((emax - emin) or 1)
        hip = _hipotese(z)
        n_h += hip
        cor = COR_HIPOTESE if hip else COR_EXPLICADA
        a = z["atributos_pp"]
        k = tips.add(
            ficha(
                f"{nome_bonito(z['municipio'])} ({z['uf']}), zona {int(z['zona'])}",
                f"{z['posicao']}º · escore {num(z['escore'], 1)}",
                [
                    (
                        "Flávio · Lula 2026",
                        f"{pct(z['flavio_pct'], 1)} · {pct(z['lula_pct'], 1)}",
                    ),
                    (
                        "Bolsonaro · Lula 2022 (1º t.)",
                        f"{pct(z['bolsonaro_22_1t_pct'], 1)} · {pct(z['lula_22_1t_pct'], 1)}",
                    ),
                    ("Resíduo da margem", pp(a.get("residuo_hierarquico"), 1)),
                    ("Brancos e nulos", pct(z["brancos_nulos_pct"], 1)),
                    ("Comparecimento", pct(z["comparecimento_pct"], 1)),
                    (
                        "Eleitorado · seções",
                        f"{inteiro(z['eleitorado'])} · {z['secoes']}",
                    ),
                    ("Conclusão (Brasília)", z.get("conclusao_brasilia", "s/d")),
                ],
                "; ".join(z.get("explicacao_provavel", [])[:2]),
            )
        )
        out.append(
            hit(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{raio:.1f}" fill="{cor}" fill-opacity="0.78" '
                f'stroke="#ffffff" stroke-width="1"/>',
                k,
            )
        )
    for z in topo[:3]:
        x, y = proj(z["lon"], z["lat"])
        out.append(
            f'<g pointer-events="none">{chip(x + 12, y - 10, nome_bonito(z["municipio"]), 13)}</g>'
        )
    out.append("</svg>")
    legenda = (
        f"As 50 zonas de escore mais alto, entre {inteiro(A['resumo']['n_zonas'])}. {50 - n_h} têm explicação "
        f"estrutural comum e {n_h} ficam como hipótese de política local a checar seção a seção. "
        f"{escape(A['aviso'])} Fonte: anomalias.json."
    )
    leg = legenda_html(
        [
            ("explicação estrutural comum", COR_EXPLICADA),
            ("hipótese de política local a checar", COR_HIPOTESE),
        ],
        "Raio pelo escore (0 a 100)",
    )
    return figura_html(
        "mapa_anomalias", "".join(out), legenda, tips, modo="fit", apos=leg
    )
