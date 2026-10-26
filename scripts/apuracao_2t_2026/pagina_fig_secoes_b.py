"""Figuras e tabelas do capítulo "Seção por seção": mapa, voto, 2×2×2 e ranking.

- ``fig_mapa``: as seções do ranking no contorno do Brasil, cor pelo sinal principal;
- ``fig_did``: diferença em diferenças da fatia de Flávio por sinal, com n e 2 erros-padrão;
- ``tabela_2x2x2``: comparecimento alto × biometria baixa × fatia de Flávio;
- ``tabela_ranking``: as 100 seções mais atípicas, com busca e CSV.

O CSV do ranking é gravado por ``escreve_csv`` em ``docs/assets/apuracao_2t/``
quando o conteúdo muda; nomes de pessoas nunca entram.
"""

from __future__ import annotations

import csv
import io
from html import escape
from pathlib import Path

from apuracao_2026.pagina_comum import (
    INK,
    MUTED,
    ROOT,
    inteiro,
    num,
    sinal,
    tabela,
)
from apuracao_2026.pagina_fig_base import (
    GRADE,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    legenda_html,
    ln,
    nome_bonito,
    r,
    svg_abre,
    t,
)
from apuracao_2026.pagina_mapas import pontos_brasil

CSV_DESTINO = ROOT / "docs/assets/apuracao_2t/secoes_ranking.csv"
CSV_URL = "assets/apuracao_2t/secoes_ranking.csv"

# Sinal principal da seção, na ordem de prioridade do desenho.
SINAL_COR = [
    ("pianista", "comparecimento +5 pp e salto de biometria", "#6b4a92"),
    ("salto_bio", "salto de biometria", "#7d5b00"),
    ("tardia", "encerramento tardio", "#5f6773"),
    ("delta", "comparecimento +5 pp", "#0c7a72"),
    ("biometria", "sem biometria ou ano de nascimento", "#2f5d8f"),
]
COR_SINAL = {k: c for k, _, c in SINAL_COR}
ROT_SINAL = {
    "delta": "comparecimento +5 pp",
    "sem_bio": "sem biometria",
    "ano_nasc": "ano de nascimento",
    "salto_bio": "salto de biometria",
    "tardia": "tardia",
    "papel": "BU do sistema de apuração",
}


def sinal_principal(sinais: list[str]) -> str:
    s = set(sinais)
    if {"delta", "salto_bio"} <= s:
        return "pianista"
    for k in ("salto_bio", "tardia", "delta"):
        if k in s:
            return k
    return "biometria"


def nome_local(s: str | None) -> str:
    return nome_bonito(s or "")


# ------------------------------------------------------------------ mapa


def fig_mapa(R: dict, escore_min: int = 2) -> str:
    secoes = [
        s for s in R["secoes"] if s.get("lat") is not None and s.get("lon") is not None
    ]
    pontos = []
    for s in sorted(secoes, key=lambda s: s.get("posicao", 999)):
        k = sinal_principal(s.get("sinais") or [])
        raio = 3.5 + 1.8 * (s.get("escore") or 0)
        sinais = ", ".join(ROT_SINAL.get(x, x) for x in s.get("sinais") or [])
        titulo = (
            f"{s.get('municipio')} ({s['uf']}), zona {s['zona']}, seção {s['secao']}: escore "
            f"{s.get('escore')}; {sinais}; {s.get('explicacao_provavel') or ''}"
        )
        pontos.append(
            {
                "lat": s["lat"],
                "lon": s["lon"],
                "raio": raio,
                "cor": COR_SINAL[k],
                "titulo": titulo,
                "rotulo": (
                    f"{s.get('municipio')} {s['zona']}/{s['secao']}"
                    if (s.get("escore") or 0) >= 3
                    else ""
                ),
            }
        )
    svg = pontos_brasil(
        pontos,
        "As seções mais atípicas do 2º turno",
        "Pontos das seções do ranking sobre o contorno das UFs; cor pelo sinal principal e raio pelo escore.",
        rotulos=12,
    )
    # Rótulos do contorno saem à direita do ponto: a costa leste precisa de margem.
    svg = svg.replace('viewBox="0 0 640 640"', 'viewBox="0 0 800 640"', 1)
    n2 = sum(1 for s in secoes if (s.get("escore") or 0) >= escore_min)
    leg = legenda_html(
        [(rot, cor) for _, rot, cor in SINAL_COR], "Sinal principal (raio: escore)"
    )
    legenda = (
        f"{inteiro(len(secoes))} seções do ranking com coordenada do local de votação, "
        f"{inteiro(n2)} delas com escore {escore_min} ou mais; rótulo nas de escore 3 ou mais. "
        "O ponto é o prédio, não o eleitor. Fonte: secoes_ranking.json."
    )
    return figura_html(
        "secoes_mapa", svg, legenda, Tips(), modo="fit", apos=leg, dim=False
    )


# ------------------------------------------------------------------ diferença em diferenças


def fig_did(V: dict) -> str:
    sinais = [
        s
        for s in V["sinais"]
        if s.get("did_fatia_flavio_pp") is not None
        and (s.get("n_did") or 0) >= (V.get("n_min") or 20)
    ]
    sinais.sort(key=lambda s: s["did_fatia_flavio_pp"])
    w, esq, dir_ = 1100, 470, 150
    topo, passo = 56, 40
    h = topo + passo * len(sinais) + 50
    lim = max(
        [
            abs(s["did_fatia_flavio_pp"]) + 2 * (s.get("ep_did_fatia_flavio_pp") or 0)
            for s in sinais
        ]
        + [1.0]
    )
    lim = max(1.0, round(lim + 0.25, 1))
    x = escala(-lim, lim, esq, w - dir_)
    out = [
        svg_abre(
            w,
            h,
            "Diferença em diferenças da fatia de Flávio, por sinal",
            "Para cada sinal, quanto a fatia de Flávio entre os dois finalistas mudou do 1º para o 2º "
            "turno nas seções com sinal, menos o quanto mudou nas vizinhas do mesmo município; barra "
            "de dois erros-padrão.",
        )
    ]
    v = -lim
    passo_t = 0.5 if lim <= 2 else 1.0
    while v <= lim + 1e-9:
        out.append(ln(x(v), topo - 10, x(v), h - 40, GRADE, 1))
        out.append(t(x(v), h - 22, sinal(v, 1), 12, MUTED, "middle", mono=True))
        v = round(v + passo_t, 6)
    out.append(ln(x(0), topo - 16, x(0), h - 40, INK, 1.4))
    out.append(t(x(-lim), topo - 26, "← na direção de Lula", 13, "#b02f21"))
    out.append(t(x(lim), topo - 26, "na direção de Flávio →", 13, "#1457aa", "end"))
    out.append(
        t(esq - 12, topo - 26, "sinal (n de seções comparáveis)", 13, MUTED, "end")
    )
    out.append(t(w - dir_ + 14, topo - 26, "contra vizinhas", 13, MUTED))
    tips = Tips()
    for i, s in enumerate(sinais):
        y = topo + i * passo + 14
        d = s["did_fatia_flavio_pp"]
        ep = s.get("ep_did_fatia_flavio_pp") or 0
        cor = "#b02f21" if d < 0 else "#1457aa"
        desc = s.get("descricao") or s["sinal"]
        rot = desc if len(desc) <= 58 else desc[:56] + "…"
        partes = [
            t(esq - 12, y + 5, f"{rot} ({inteiro(s.get('n_did'))})", 13, INK, "end"),
            r(min(x(0), x(d)), y - 7, abs(x(d) - x(0)), 14, cor, ' fill-opacity="0.8"'),
            ln(x(d - 2 * ep), y, x(d + 2 * ep), y, INK, 1.4),
            ln(x(d - 2 * ep), y - 6, x(d - 2 * ep), y + 6, INK, 1.4),
            ln(x(d + 2 * ep), y - 6, x(d + 2 * ep), y + 6, INK, 1.4),
            t(
                w - dir_ + 14,
                y + 5,
                f"{sinal(s.get('dif_fatia_flavio_vs_vizinhas_pp'), 2)} pp",
                13,
                INK,
                mono=True,
            ),
        ]
        kk = tips.add(
            ficha(
                desc,
                f"{inteiro(s.get('n_did'))} seções comparáveis",
                [
                    ("diferença em diferenças", f"{sinal(d, 2)} pp"),
                    ("erro-padrão", f"{num(ep, 2)} pp"),
                    (
                        "contra vizinhas no 2º turno",
                        f"{num(s.get('dif_fatia_flavio_vs_vizinhas_pp'), 2)} pp",
                    ),
                    ("seções com sinal", inteiro(s.get("n_sinal_total"))),
                    ("vizinhas", inteiro(s.get("n_vizinhas"))),
                    ("municípios", inteiro(s.get("n_municipios"))),
                ],
                "Erro-padrão aproximado, entre municípios.",
            )
        )
        out.append(
            hit("".join(partes) + area(0, y - passo / 2, w, passo), kk, foco=True)
        )
    out.append("</svg>")
    legenda = (
        "Pontos percentuais da fatia de Flávio entre os dois finalistas. A coluna da direita é a "
        "diferença crua contra as vizinhas no 2º turno; a barra é essa diferença descontada da que já "
        "existia no 1º. Só sinais com n de 20 ou mais. Fonte: secoes_voto.json."
    )
    return figura_html(
        "secoes_did",
        "".join(out),
        legenda,
        tips,
        modo="scroll",
        minw=900,
        foco=(esq - 40, w - dir_, x(0)),
    )


# ------------------------------------------------------------------ 2×2×2


def tabela_2x2x2(V: dict) -> str:
    linhas = []
    for c in V["tabela_2x2x2"]:
        linhas.append(
            [
                "sim" if c["comparecimento_alto"] else "não",
                "sim" if c["biometria_baixa"] else "não",
                inteiro(c["n"]),
                inteiro(c["n_flavio_sobe"]),
                inteiro(c["n_flavio_nao_sobe"]),
                f"{num(c.get('pct_flavio_sobe'), 2)}%",
                f"{sinal(c.get('delta_fatia_flavio_pp'), 2)} pp",
            ]
        )
    return tabela(
        [
            "comparecimento +5 pp",
            "biometria baixa",
            "seções",
            "fatia de Flávio subiu",
            "não subiu",
            "parcela que subiu",
            "fatia de Flávio, 2º menos 1º turno",
        ],
        linhas,
        "Comparecimento alto × biometria baixa × fatia de Flávio contra o 1º turno (fonte lida, sem peso).",
    )


# ------------------------------------------------------------------ ranking

COLUNAS_CSV = [
    "posicao",
    "uf",
    "municipio",
    "zona",
    "secao",
    "local",
    "origem",
    "escore",
    "sinais",
    "aptos_1t",
    "aptos_2t",
    "taxa_comp_1t",
    "taxa_comp_2t",
    "delta_comp_pp",
    "sem_bio_pct_1t",
    "sem_bio_pct_2t",
    "ano_nasc_pct_1t",
    "ano_nasc_pct_2t",
    "salto_bio_pp",
    "encerramento_1t",
    "encerramento_2t",
    "recebimento_2t",
    "flavio_1t",
    "lula_1t",
    "flavio_2t",
    "lula_2t",
    "explicacao_provavel",
    "sem_explicacao",
]


def csv_ranking(R: dict) -> str:
    buf = io.StringIO()
    wr = csv.writer(buf, lineterminator="\n")
    wr.writerow(COLUNAS_CSV)
    for s in R["secoes"]:
        linha = []
        for c in COLUNAS_CSV:
            v = s.get(c)
            if c == "sinais":
                v = " ".join(v or [])
            elif isinstance(v, float) and v.is_integer() and c.endswith(("_1t", "_2t")):
                v = int(v)
            linha.append("" if v is None else v)
        wr.writerow(linha)
    return buf.getvalue()


def escreve_csv(R: dict, destino: Path | None = None) -> Path:
    """Grava o CSV do ranking; só reescreve quando o conteúdo muda."""
    alvo = destino or CSV_DESTINO
    texto = csv_ranking(R)
    if not alvo.exists() or alvo.read_text(encoding="utf-8") != texto:
        alvo.parent.mkdir(parents=True, exist_ok=True)
        alvo.write_text(texto, encoding="utf-8")
    return alvo


def _par(a, b, casas: int = 1, sufixo: str = "%") -> str:
    fa = "s/d" if a is None else f"{num(a, casas)}{sufixo}"
    fb = "s/d" if b is None else f"{num(b, casas)}{sufixo}"
    return f"{fa} → {fb}"


def _votos(f, lu) -> str:
    if f is None or lu is None:
        return "s/d"
    return f"{inteiro(f)} × {inteiro(lu)}"


BUSCA_JS = (
    "<script>(function(){var c=document.getElementById('ranking-busca');if(!c)return;"
    "var i=c.querySelector('input'),tb=c.querySelector('tbody'),o=c.querySelector('output');"
    "if(!i||!tb)return;var rs=[].slice.call(tb.rows);"
    "function n(s){return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}"
    "var tx=rs.map(function(r){return n(r.textContent);});"
    "i.addEventListener('input',function(){var q=n(i.value.trim()),k=0;"
    "rs.forEach(function(r,j){var v=!q||tx[j].indexOf(q)>=0;r.hidden=!v;if(v)k++;});"
    "if(o)o.textContent=k+' de '+rs.length+' seções';});})();</script>"
)


def tabela_ranking(R: dict) -> str:
    linhas = []
    for s in R["secoes"]:
        expl = escape(s.get("explicacao_provavel") or "")
        if s.get("sem_explicacao"):
            expl = f"<b>{expl}</b>"
        sinais = ", ".join(ROT_SINAL.get(x, x) for x in s.get("sinais") or [])
        linhas.append(
            [
                inteiro(s.get("posicao")),
                s["uf"],
                escape(s.get("municipio") or ""),
                inteiro(s.get("zona")),
                inteiro(s.get("secao")),
                escape(nome_local(s.get("local"))),
                f"{inteiro(s.get('aptos_1t'))} → {inteiro(s.get('aptos_2t'))}",
                _par(s.get("taxa_comp_1t"), s.get("taxa_comp_2t")),
                _par(s.get("sem_bio_pct_1t"), s.get("sem_bio_pct_2t")),
                _par(s.get("ano_nasc_pct_1t"), s.get("ano_nasc_pct_2t")),
                f"{s.get('encerramento_1t') or 's/d'} → {s.get('encerramento_2t') or 's/d'}",
                _votos(s.get("flavio_1t"), s.get("lula_1t")),
                _votos(s.get("flavio_2t"), s.get("lula_2t")),
                f"{inteiro(s.get('escore'))}: {sinais}",
                expl,
            ]
        )
    corpo = tabela(
        [
            "nº",
            "UF",
            "município",
            "zona",
            "seção",
            "local de votação",
            "aptos 1º → 2º",
            "comparecimento 1º → 2º",
            "sem biometria 1º → 2º",
            "ano de nascimento 1º → 2º",
            "encerramento do BU 1º → 2º",
            "Flávio × Lula, 1º",
            "Flávio × Lula, 2º",
            "escore e sinais",
            "explicação provável",
        ],
        linhas,
        f"As {len(R['secoes'])} seções mais atípicas por {R.get('ordem') or 'escore e magnitude'}.",
    )
    n_sem = sum(1 for s in R["secoes"] if s.get("sem_explicacao"))
    return (
        f'<details class="ranking"><summary>Ver as {len(R["secoes"])} seções ({n_sem} sem explicação '
        "provável pela regra, em negrito)</summary>"
        '<div id="ranking-busca"><label class="fig-ctl"><span class="rot">Buscar</span> '
        '<input type="search" placeholder="UF, município, zona, local ou sinal" '
        'aria-label="Buscar no ranking das seções"></label> <output aria-live="polite"></output></div>'
        f"{corpo}"
        f'<p><a href="{CSV_URL}" download>Baixar o ranking em CSV</a> (mesmas colunas, sem nome de pessoa).</p>'
        f"</details>{BUSCA_JS}"
    )
