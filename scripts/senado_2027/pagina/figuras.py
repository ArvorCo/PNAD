"""Figuras SVG da página O Senado de 2027 diante do STF.

Todo gráfico é desenhado aqui, em Python, com os dados embutidos no SVG: a página
abre do disco, sem rede, e continua completa sem JavaScript. Cada marca leva
`<title>` com o número exato, que o navegador mostra ao passar o ponteiro. Barras
são `<rect>`, nunca elemento inline. Texto sempre em tinta ou cinza sobre o papel;
a cor de bloco só pinta marca, nunca texto.

Cada função recebe o JSON inteiro do motor (`docs/assets/senado_2027.json`) e
devolve `<figure class="sn27-fig ...">` com legenda em português corrente.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
import tempfile
from pathlib import Path

from .figuras_base import (
    BLOCOS,
    BORDA_BLOCO,
    CARD,
    CHAVE_SIM,
    COR_BLOCO,
    FAIXAS_C,
    GRID,
    GRUPOS_TIPO,
    INK,
    LINE,
    MUTED,
    ROTULO_ALVO,
    ROTULO_BLOCO,
    ROTULO_CENARIO,
    TEAL,
    esc,
    figura,
    fmt,
    largura,
    ocupantes,
    pct,
    sigla,
    sim,
    svg,
    tipo_dominante,
    txt,
    valor_c,
    valor_k,
)
from .figuras_conta import distribuicao_votos as distribuicao_votos
from .figuras_conta import pivos as pivos
from .figuras_conta import placar_cenarios as placar_cenarios
from .figuras_mapa import _sobrepoe as _sobrepoe
from .figuras_mapa import curva_k as curva_k
from .figuras_mapa import dispersao_k_c as dispersao_k_c
from .figuras_mapa import dispersao_relatorios as dispersao_relatorios
from .figuras_mapa import resolver_rotulos as resolver_rotulos

# 2. Hemiciclo por faixa de C

HW, HH = 720.0, 440.0
HCX, HCY = HW / 2, HH - 20
HRAIOS = (150.0, 192.0, 234.0, 276.0)
HRAIO_ASSENTO = 12.5


def posicoes_hemiciclo() -> list[tuple[float, float, float]]:
    """(ângulo, x, y) dos 81 assentos, da esquerda para a direita."""
    soma = sum(HRAIOS)
    qtd = [round(81 * r / soma) for r in HRAIOS]
    qtd[-1] += 81 - sum(qtd)
    seats = []
    for r, n in zip(HRAIOS, qtd, strict=True):
        for k in range(n):
            ang = math.pi * (1 - k / (n - 1))
            seats.append((ang, r, HCX + r * math.cos(ang), HCY - r * math.sin(ang)))
    seats.sort(key=lambda s: (-s[0], s[1]))
    return [(s[0], s[2], s[3]) for s in seats]


def faixa_c(c: float) -> tuple[str, str]:
    for lo, hi, rot, cor in FAIXAS_C:
        if lo <= c < hi:
            return rot, cor
    return FAIXAS_C[-1][2], FAIXAS_C[-1][3]


def hemiciclo_c(data: dict, alvo: str = "C_imp", cenario: str = "flavio") -> str:
    pessoas = ocupantes(data, cenario)
    ordem = sorted(
        pessoas,
        key=lambda p: (valor_c(p, cenario, alvo), -BLOCOS.index(p["bloco"]), p["nome"]),
    )
    pos = posicoes_hemiciclo()
    corpo = []
    # marcas radiais: o n-ésimo voto mais favorável, contado da direita
    marcas_txt = []
    caixas: list[tuple[float, float, float, float]] = []
    for n, rotulo_lim in ((54, "54: impeachment"), (49, "49: PEC")):
        i = 81 - n
        ang = (pos[i][0] + pos[i - 1][0]) / 2
        anchor = "end" if math.cos(ang) < 0 else "start"
        r0, r1 = HRAIOS[0] - 22, HRAIOS[-1] + 40
        xa, ya = HCX + r0 * math.cos(ang), HCY - r0 * math.sin(ang)
        xb, yb = HCX + r1 * math.cos(ang), HCY - r1 * math.sin(ang)
        c_n = valor_c(ordem[i], cenario, alvo)
        corpo.append(
            f'<line class="sn27-limiar" data-limiar="{n}" x1="{xa:.1f}" y1="{ya:.1f}" '
            f'x2="{xb:.1f}" y2="{yb:.1f}" stroke="{INK}" stroke-width="2.2" '
            'stroke-dasharray="5 3"/>'
        )
        dx = -6 if anchor == "end" else 6
        sub = f"{n}º voto: C {fmt(c_n)}"
        ty = yb - 20
        w = max(largura(rotulo_lim, 16), largura(sub, 15))
        x_a = xb + dx - (w if anchor == "end" else 0)
        while any(_sobrepoe((x_a, ty - 16, x_a + w, ty + 22), c) for c in caixas):
            ty -= 6
        caixas.append((x_a, ty - 16, x_a + w, ty + 22))
        marcas_txt.append(txt(xb + dx, ty, rotulo_lim, 16, anchor, 700))
        marcas_txt.append(txt(xb + dx, ty + 18, sub, 15, anchor, cor=MUTED))
    contagem = {rot: 0 for _, _, rot, _ in FAIXAS_C}
    n_k35 = 0
    for (_, x, y), p in zip(pos, ordem, strict=True):
        c = valor_c(p, cenario, alvo)
        rot, cor = faixa_c(c)
        contagem[rot] += 1
        k = valor_k(p)
        if k >= 35:
            n_k35 += 1
            borda = f'stroke="{INK}" stroke-width="3.4"'
            r = HRAIO_ASSENTO - 1.4
        else:
            borda = 'stroke="#fffdf8" stroke-width="1"'
            r = HRAIO_ASSENTO
        corpo.append(
            f'<circle class="sn27-assento" data-slug="{esc(p["slug"])}" cx="{x:.1f}" '
            f'cy="{y:.1f}" r="{r:.1f}" fill="{cor}" {borda}><title>{esc(p["nome"])} '
            f"({esc(sigla(p))}): C {fmt(c, 1)}, K {fmt(k, 1)}</title></circle>"
        )
    s = sim(data, cenario)[CHAVE_SIM[alvo]]
    corpo.append(txt(HCX, HCY - 62, fmt(s["media"], 1), 44, "middle", 600))
    corpo.append(txt(HCX, HCY - 36, "votos esperados", 16, "middle", cor=MUTED))
    corpo.append(
        txt(
            HCX,
            HCY - 14,
            f"{ROTULO_ALVO[alvo]}, {ROTULO_CENARIO[cenario]}",
            16,
            "middle",
            cor=MUTED,
        )
    )
    corpo += marcas_txt
    c49 = valor_c(ordem[81 - 49], cenario, alvo)
    c54 = valor_c(ordem[81 - 54], cenario, alvo)
    rotulo = (
        f"Hemiciclo de 81 assentos ordenados pelo C do {ROTULO_ALVO[alvo]}, "
        f"{ROTULO_CENARIO[cenario]}: "
        + "; ".join(f"{v} com C {k}" for k, v in contagem.items())
        + f". O 49º voto tem C {fmt(c49)} e o 54º, C {fmt(c54)}."
    )
    itens = []
    for _, _, rot, cor in FAIXAS_C:
        itens.append(
            '<li style="display:flex;align-items:center;gap:8px;margin:0">'
            f'<i aria-hidden="true" style="display:block;flex:none;width:16px;'
            f'height:16px;border-radius:50%;background:{cor}"></i>'
            f"<span>C {rot}: <b>{contagem[rot]}</b></span></li>"
        )
    itens.append(
        '<li style="display:flex;align-items:center;gap:8px;margin:0">'
        '<i aria-hidden="true" style="display:block;flex:none;width:12px;height:12px;'
        f'border-radius:50%;border:3px solid {INK};background:#cfc7a6"></i>'
        f"<span>contorno grosso: K de 35 ou mais (<b>{n_k35}</b>)</span></li>"
    )
    lista = (
        '<ul class="sn27-legenda" style="list-style:none;padding:0;margin:10px 0 0;'
        "display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));"
        f'gap:6px 18px;font-size:15px;color:{INK}">' + "".join(itens) + "</ul>"
    )
    altos = contagem["90 ou mais"] + contagem["80 a 89"]
    legenda = (
        f"Os 81 assentos do {ROTULO_CENARIO[cenario]} ordenados pelo contrapeso no "
        f"{ROTULO_ALVO[alvo]}, do menor C à esquerda ao maior à direita. {altos} "
        f"senadores têm C de 80 ou mais. Contando da direita, o 49º senador mais "
        f"favorável tem C de {fmt(c49)} e o 54º, C de {fmt(c54)}: é nesse trecho, "
        "e não nas pontas, que a conta se decide. Contorno grosso marca quem tem K de "
        "35 ou mais."
    )
    ident = f"hemiciclo-{CHAVE_SIM[alvo]}-{cenario}"
    return figura(
        "sn27-fig-hemi sn27-fig-wide",
        svg(HW, HH, rotulo, "".join(corpo), "sn27-svg-hemi").replace(
            "<svg ", '<svg style="min-width:560px" ', 1
        )
        + lista,
        legenda,
        ident,
    )


# 4. Tipos de caso


def _tabela_tipos(data: dict, cenario: str, alvo: str = "C_imp") -> list[dict]:
    pessoas = ocupantes(data, cenario)
    zero_bloco: dict[str, list[float]] = {}
    for p in pessoas:
        if valor_k(p) == 0:
            zero_bloco.setdefault(p["bloco"], []).append(valor_c(p, cenario, alvo))
    base_bloco = {b: statistics.fmean(v) for b, v in zero_bloco.items()}
    regua = data["regua"]["C"]["base"][alvo]
    linhas = []
    for chave, rot in GRUPOS_TIPO:
        grupo = [p for p in pessoas if valor_k(p) >= 20 and tipo_dominante(p) == chave]
        if not grupo:
            continue
        obs = statistics.fmean(valor_c(p, cenario, alvo) for p in grupo)
        ref = statistics.fmean(
            base_bloco.get(p["bloco"], regua[p["bloco"]]) for p in grupo
        )
        redutor = statistics.fmean(
            0.25 * float(p["scores"].get("K_patrimonial_ativo", 0)) for p in grupo
        )
        linhas.append(
            {
                "chave": chave,
                "rotulo": rot,
                "n": len(grupo),
                "C": obs,
                "ref": ref,
                "dif": obs - ref,
                "redutor": redutor if alvo == "C_imp" else None,
                "blocos": {b: sum(1 for p in grupo if p["bloco"] == b) for b in BLOCOS},
                "nomes": sorted(p["nome"] for p in grupo),
            }
        )
    return linhas


def tipos_de_caso(data: dict, cenario: str = "flavio") -> str:
    alvo = "C_imp"
    linhas = _tabela_tipos(data, cenario, alvo)
    W = 960.0
    topo, passo = 92.0, 78.0
    eixo = topo + passo * len(linhas) + 4
    H = eixo + 62
    lx0, lx1 = 330.0, 640.0

    def bx(v: float) -> float:
        return lx0 + (lx1 - lx0) * v / 100

    corpo = [
        txt(
            20,
            30,
            f"C médio no impeachment, {ROTULO_CENARIO[cenario]}",
            16,
            "start",
            700,
        ),
        txt(
            lx0,
            58,
            "senadores com K de 20 ou mais, pelo caso de maior peso",
            13,
            cor=MUTED,
        ),
        txt(750, 30, "de que bloco", 16, "start", 700),
    ]
    for v in range(0, 101, 25):
        corpo.append(
            f'<line x1="{bx(v):.1f}" x2="{bx(v):.1f}" y1="{topo - 14}" '
            f'y2="{eixo}" stroke="{GRID}"/>'
        )
        corpo.append(txt(bx(v), eixo + 18, str(v), 13, "middle", cor=MUTED))
    for i, ln in enumerate(linhas):
        y = topo + i * passo
        corpo.append(txt(20, y + 16, ln["rotulo"], 15, "start", 700))
        corpo.append(txt(20, y + 36, f"{ln['n']} senadores", 13, cor=MUTED))
        corpo.append(
            f'<rect x="{lx0}" y="{y}" width="{bx(ln["C"]) - lx0:.1f}" height="22" '
            f'fill="{TEAL}"><title>{esc(ln["rotulo"])}: C médio {fmt(ln["C"], 1)}'
            "</title></rect>"
        )
        corpo.append(txt(bx(ln["C"]) + 6, y + 16, fmt(ln["C"], 1), 14, "start", 700))
        corpo.append(
            f'<rect x="{lx0}" y="{y + 28}" width="{bx(ln["ref"]) - lx0:.1f}" '
            f'height="14" fill="{LINE}" stroke="{MUTED}" stroke-width="0.8">'
            f"<title>mesmos blocos, senadores sem caso: C médio {fmt(ln['ref'], 1)}"
            "</title></rect>"
        )
        sinal = "+" if ln["dif"] > 0.05 else ""
        corpo.append(
            txt(
                bx(ln["ref"]) + 6,
                y + 40,
                f"{fmt(ln['ref'], 1)} ({sinal}{fmt(ln['dif'], 1)})",
                13,
                cor=MUTED,
            )
        )
        # composição por bloco
        cx = 750.0
        escala = 190.0 / max(max(r["n"] for r in linhas), 1)
        for b in BLOCOS:
            nb = ln["blocos"][b]
            if not nb:
                continue
            w = nb * escala
            corpo.append(
                f'<rect x="{cx:.1f}" y="{y + 2}" width="{w - 1:.1f}" height="20" '
                f'fill="{COR_BLOCO[b]}"><title>{ROTULO_BLOCO[b]}: {nb}</title></rect>'
            )
            cx += w
    kx = 20.0
    for b in BLOCOS:
        corpo.append(
            f'<rect x="{kx:.1f}" y="{H - 24}" width="14" height="14" '
            f'fill="{COR_BLOCO[b]}"/>' + txt(kx + 20, H - 12, ROTULO_BLOCO[b], 13)
        )
        kx += 20 + largura(ROTULO_BLOCO[b], 13) + 22
    # legenda das barras
    corpo.append(
        f'<rect x="{lx0}" y="68" width="14" height="12" fill="{TEAL}"/>'
        + txt(lx0 + 20, 79, "o grupo", 13)
        + f'<rect x="{lx0 + 110}" y="68" width="14" height="12" fill="{LINE}" '
        f'stroke="{MUTED}" stroke-width="0.8"/>'
        + txt(lx0 + 130, 79, "colegas de bloco com K = 0", 13)
    )
    g = {ln["chave"]: ln for ln in linhas}
    op, pa = g.get("opiniao"), g.get("patrimonial_ativo")
    partes = []
    if op:
        partes.append(
            f"Quem tem caso de opinião ou de 8 de janeiro como o de maior peso "
            f"({op['n']} senadores) tem C médio de {fmt(op['C'], 1)}, contra "
            f"{fmt(op['ref'], 1)} dos colegas de bloco sem caso."
        )
    if pa:
        partes.append(
            f"No patrimonial ativo ({pa['n']} senadores) a média é {fmt(pa['C'], 1)}, "
            f"contra {fmt(pa['ref'], 1)} dos colegas de bloco. A régua desconta "
            "0,25 × K patrimonial ativo, em média "
            f"{fmt(pa['redutor'], 1)} pontos por senador deste grupo antes do piso "
            "de 2: a distância vem em boa parte da própria régua, não de voto "
            "observado."
        )
    rotulo = "Barras do C médio no impeachment por tipo de caso: " + "; ".join(
        f"{ln['rotulo']}, {ln['n']} senadores, C {fmt(ln['C'], 1)} contra "
        f"{fmt(ln['ref'], 1)} sem caso no bloco"
        for ln in linhas
    )
    legenda = (
        " ".join(partes)
        + " Opinião radicaliza: quem responde por fala ou por 8 de janeiro não "
        "recua. Patrimonial é onde o efeito inibidor pode existir, e esta figura não o "
        "prova: o teste com voto observado é o da PEC 8, mais abaixo. A barra à "
        "direita mostra de que bloco vem cada grupo."
    )
    return figura(
        "sn27-fig-wide sn27-fig-tipos",
        svg(W, H, rotulo, "".join(corpo), "sn27-svg-tipos"),
        legenda,
        f"tipos-{cenario}",
    )


# 7. Teste da PEC 8


def teste_pec8(data: dict) -> str:
    t = data["teste_pec8"]
    sen = t["senadores"]
    colunas = [("sim", "Sim"), ("nao", "Não"), ("ausente", "Ausente")]
    if any(s["voto"] == "dividido" for s in sen):
        colunas.append(("dividido", "Dividido"))
    W = 960.0
    cw = W / len(colunas)
    passo = 24.0
    maior = max(sum(1 for s in sen if s["voto"] == c) for c, _ in colunas)
    H = 110 + passo * maior + 20
    corpo = []
    for j, (chave, rot) in enumerate(colunas):
        grupo = sorted(
            (s for s in sen if s["voto"] == chave),
            key=lambda s: (BLOCOS.index(s["bloco"]), s["nome"]),
        )
        x = 20 + j * cw
        com_k = sum(1 for s in grupo if s["K_positivo"])
        corpo.append(txt(x, 30, f"{rot}: {len(grupo)}", 20, "start", 700))
        corpo.append(
            txt(x, 54, f"{com_k} com caso, {len(grupo) - com_k} sem", 14, cor=MUTED)
        )
        if j:
            corpo.append(
                f'<line x1="{x - 14:.1f}" x2="{x - 14:.1f}" y1="12" y2="{H - 10:.1f}" '
                f'stroke="{LINE}"/>'
            )
        for i, s in enumerate(grupo):
            y = 86 + i * passo
            b = s["bloco"]
            if s["K_positivo"]:
                marca = f'fill="{COR_BLOCO[b]}" stroke="{BORDA_BLOCO[b]}" stroke-width="1.2"'
            else:
                marca = f'fill="{CARD}" stroke="{COR_BLOCO[b]}" stroke-width="2.6"'
            corpo.append(
                f'<circle class="sn27-pec8" cx="{x + 8:.1f}" cy="{y - 5:.1f}" r="7" '
                f'{marca}><title>{esc(s["nome"])} ({esc(s["uf"])}), '
                f"{ROTULO_BLOCO[b]}: votou {rot.lower()}, K {fmt(s['K'], 1)}</title>"
                "</circle>"
            )
            nome = f"{s['nome']} ({s['uf']})"
            corpo.append(txt(x + 22, y, nome, 14))
            if s.get("K_patrimonial_ativo", 0) > 0:
                tx = x + 22 + largura(nome, 14) + 8
                corpo.append(
                    f'<rect x="{tx:.1f}" y="{y - 13:.1f}" width="{largura("patrimonial", 12) + 10:.1f}" '
                    f'height="17" rx="3" fill="#f7e7b8" stroke="#b4851a"/>'
                    + txt(tx + 5, y, "patrimonial", 12, "start", 700)
                )
    nao = [s for s in sen if s["voto"] == "nao"]
    nao_esq = sum(1 for s in nao if s["bloco"] in ("E", "CE"))
    nao_cen = sum(1 for s in nao if s["bloco"] == "C")
    nao_pat = sum(1 for s in nao if s.get("K_patrimonial_ativo", 0) > 0)
    n_sim = sum(1 for s in sen if s["voto"] == "sim")
    n_aus = sum(1 for s in sen if s["voto"] == "ausente")
    rotulo = (
        f"{len(sen)} senadores de 2027 que votaram a PEC 8 em 2023: {n_sim} sim, "
        f"{len(nao)} não, {n_aus} ausentes. Sim entre quem tem caso: "
        f"{pct(t['sim_entre_K_positivo_pct'], 1)}; entre quem não tem: "
        f"{pct(t['sim_entre_K_zero_pct'], 1)}."
    )
    legenda = (
        f"Dos {len(sen)} senadores de 2027 que estavam no plenário da PEC 8 em "
        f"novembro de 2023, {n_sim} votaram sim, {len(nao)} não e {n_aus} faltaram. "
        f"Entre os que tinham algum caso (ponto cheio), {pct(t['sim_entre_K_positivo_pct'], 1)} "
        f"votaram sim; entre os sem caso (ponto vazado), "
        f"{pct(t['sim_entre_K_zero_pct'], 1)}. A diferença não se separa do acaso "
        f"(teste exato de Fisher, p = {fmt(t['p_fisher_bilateral_pct'] / 100, 2)}). "
        f"Dos {len(nao)} votos não, {nao_esq} vieram da esquerda e {nao_cen} do centro, "
        f"e {'nenhum' if nao_pat == 0 else nao_pat} tinha caso patrimonial ativo: "
        "os não vieram da ideologia, não "
        "do processo. A tarja marca quem tinha caso patrimonial ativo."
    )
    return figura(
        "sn27-fig-wide sn27-fig-pec8",
        svg(W, H, rotulo, "".join(corpo), "sn27-svg-pec8"),
        legenda,
        "teste-pec8",
    )


# Coleção


def todas(data: dict) -> dict[str, str]:
    return {
        "placar_cenarios": placar_cenarios(data),
        "dispersao_k_c": dispersao_k_c(data, "flavio"),
        "dispersao_k_c_lula": dispersao_k_c(data, "lula"),
        "hemiciclo_c": hemiciclo_c(data, "C_imp", "flavio"),
        "hemiciclo_c_pec": hemiciclo_c(data, "C_pec", "flavio"),
        "distribuicao_votos": distribuicao_votos(data, "flavio"),
        "distribuicao_votos_lula": distribuicao_votos(data, "lula"),
        "tipos_de_caso": tipos_de_caso(data, "flavio"),
        "curva_k": curva_k(data),
        "dispersao_relatorios": dispersao_relatorios(data),
        "teste_pec8": teste_pec8(data),
        "pivos": pivos(data, "flavio", "C_imp"),
        "pivos_pec": pivos(data, "flavio", "C_pec"),
    }


def _pagina_teste(figs: dict[str, str], assets: Path) -> str:
    css = "".join(
        f'<link rel="stylesheet" href="{(assets / n).as_uri()}">'
        for n in ("predicao_2026.css", "senado_2027.css")
    )
    corpo = "".join(
        f"<section id='{k}'><h2>{k}</h2>{v}</section>" for k, v in figs.items()
    )
    return (
        '<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"{css}<style>body{{background:#f4f0e6;padding:16px}}"
        "main{max-width:960px;margin:0 auto}</style></head>"
        f'<body><main id="conteudo">{corpo}</main></body></html>'
    )


if __name__ == "__main__":
    raiz = Path(__file__).resolve().parents[3]
    destino = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(tempfile.gettempdir()) / "senado_2027_figuras"
    )
    destino.mkdir(parents=True, exist_ok=True)
    dados = json.loads(
        (raiz / "docs/assets/senado_2027.json").read_text(encoding="utf-8")
    )
    figs = todas(dados)
    for nome, html in figs.items():
        (destino / f"{nome}.html").write_text(html, encoding="utf-8")
    (destino / "index.html").write_text(
        _pagina_teste(figs, raiz / "docs/assets"), encoding="utf-8"
    )
    print(destino / "index.html")
