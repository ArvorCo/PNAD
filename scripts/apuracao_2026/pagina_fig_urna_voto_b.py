"""Figuras do capítulo 12: Flávio × Lula por modelo de urna, em barras simples.

- `voto_modelo_uf_simples`: uma linha por UF, agrupadas por região na ordem de
  `modelo_urna_uf`; um lugar fixo por modelo de urna, do mais velho ao mais novo,
  e no fim a UF inteira (`secoes.json → urna.voto_por_uf_modelo` e
  `urna.voto_por_uf_total`).
- `voto_modelo_exterior`: a mesma forma, uma linha por país com ao menos
  `MINIMO_VOTANTES_PAIS` votantes, agrupados por continente; os demais países
  somados numa linha só (`urna.voto_por_pais_modelo`).

Cada barra é 100% dos válidos: Flávio em azul a partir da esquerda, Lula em
vermelho a partir da direita, os demais candidatos no meio, e um traço marca 50%.
É comparação bruta: mistura o modelo com a geografia. A leitura controlada fica
nas figuras seguintes do capítulo. Versão larga e versão empilhada abaixo de
720 px (`larga_estreita`), sem rolagem lateral.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from html import escape
from typing import Any

from .pagina_comum import FLAVIO, LULA, NOME_UF, inteiro, num, sinal
from .pagina_fig_base import (
    FONTE,
    GRADE,
    INK,
    MUTED,
    REGIOES,
    Tips,
    area,
    figura_html,
    hit,
    larga_estreita,
    legenda_html,
    ln,
    nome_bonito,
    registra,
    svg_abre,
)
from .pagina_fig_secoes import nota_cobertura, regiao_da_uf, secoes
from .pagina_fig_urna_voto import MINIMO_SECOES, modelos_ordenados

MINIMO_VOTANTES_PAIS = 300
"""País com menos votantes que isso entra na linha dos demais países."""
MINIMO_VOTANTES_LUGAR = 100
"""No exterior, modelo com menos votantes que isso no país fica com o lugar vazio."""
SEM_MODELO = "sem modelo"
LARGA, ESTREITA = 1100, 380
DEMAIS = GRADE
"""Cor do meio da barra: os votos válidos dos demais candidatos."""
VAZIO = "#a39b89"
CARACTERE = 6.8
"""Largura de um caractere do rótulo na barra (Archivo 600 a 13 px, por cima: o
dígito mede cerca de 7,3 px, a letra 6,8 e o espaço 3,3)."""
FRASE = (
    "Comparação bruta: mistura o modelo com a geografia. A leitura controlada está "
    "nas figuras seguintes."
)


@dataclass
class Linha:
    """Uma linha da figura: uma UF ou um país, com um lugar por modelo e o total."""

    id: str
    rotulo: str
    nome: str
    grupo: str
    celulas: list[dict[str, Any] | None]
    vazios: list[str]
    total: dict[str, Any]
    extra: dict[str, Any] = field(default_factory=dict)


def _pct(x: float | None, casas: int = 2) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def _parcelas(c: dict[str, Any]) -> dict[str, Any]:
    """Recalcula as parcelas de uma soma de células (válidos e aptos)."""
    v, a = c["validos"], c.get("aptos") or 0
    c["flavio_pct"] = 100 * c["flavio"] / v if v else None
    c["lula_pct"] = 100 * c["lula"] / v if v else None
    c["abstencao_pct"] = 100 * (a - c["votantes"]) / a if a else None
    return c


def _soma(cs: Sequence[dict[str, Any]]) -> dict[str, Any]:
    chaves = ("secoes", "aptos", "votantes", "validos", "lula", "flavio")
    return _parcelas({k: sum(c.get(k) or 0 for c in cs) for k in chaves})


# ------------------------------------------------------------------ dados


def modelos_uf(U: dict, minimo: int = MINIMO_SECOES) -> list[str]:
    """Modelos com ao menos `minimo` seções em alguma UF (o exterior fica de fora)."""
    cheios = {
        x["modelo"]
        for x in U["voto_por_uf_modelo"]
        if regiao_da_uf(x["uf"]) in REGIOES and x["secoes"] >= minimo
    }
    return [m for m in modelos_ordenados(U) if m in cheios]


def linhas_uf(U: dict, minimo: int = MINIMO_SECOES) -> tuple[list[str], list[Linha]]:
    """Modelos (lugares) e uma linha por UF, por região e sigla, como `modelo_urna_uf`."""
    modelos = modelos_uf(U, minimo)
    total = {x["uf"]: x for x in U["voto_por_uf_total"]}
    por: dict[str, dict[str, dict[str, Any]]] = {}
    for x in U["voto_por_uf_modelo"]:
        if regiao_da_uf(x["uf"]) in REGIOES:
            por.setdefault(x["uf"], {})[x["modelo"]] = x
    ufs = sorted(por, key=lambda u: (REGIOES.index(regiao_da_uf(u)), u))
    out = []
    for uf in ufs:
        cel: list[dict[str, Any] | None] = []
        vaz: list[str] = []
        for m in modelos:
            x = por[uf].get(m)
            if x and x["secoes"] >= minimo:
                cel.append(x)
                vaz.append("")
            else:
                cel.append(None)
                vaz.append(
                    f"só {inteiro(x['secoes'])} {'seção' if x['secoes'] == 1 else 'seções'}"
                    if x
                    else ""
                )
        fora = [
            x for m, x in por[uf].items() if m not in modelos or x["secoes"] < minimo
        ]
        out.append(
            Linha(
                uf,
                uf,
                NOME_UF.get(uf, uf),
                regiao_da_uf(uf),
                cel,
                vaz,
                total[uf],
                {"fora": fora},
            )
        )
    return modelos, out


def _rotulo_modelo(m: str) -> str:
    return "papel" if m == SEM_MODELO else m


def linhas_exterior(
    U: dict,
    minimo_pais: int = MINIMO_VOTANTES_PAIS,
    minimo_lugar: int = MINIMO_VOTANTES_LUGAR,
) -> tuple[list[str], list[Linha], dict[str, Any]]:
    """Modelos do exterior, uma linha por país grande e a linha dos demais países.

    Países por continente (o de mais votantes primeiro) e, dentro dele, do maior
    para o menor. `resumo` traz o que a legenda e o texto declaram.
    """
    E = U["voto_por_pais_modelo"]
    if not E or not E.get("paises"):
        raise KeyError("urna.voto_por_pais_modelo")
    P = E["paises"]
    presentes = {m["modelo"] for p in P for m in p["modelos"]}
    reais = [m for m in modelos_ordenados(U) if m in presentes]
    extras = sorted(m for m in presentes if m not in reais and m != SEM_MODELO)
    modelos = reais + extras + ([SEM_MODELO] if SEM_MODELO in presentes else [])
    grandes = [p for p in P if p["total"]["votantes"] >= minimo_pais]
    pequenos = [p for p in P if p["total"]["votantes"] < minimo_pais]
    cont_vot: dict[str, int] = {}
    for p in grandes:
        cont_vot[p["continente"]] = (
            cont_vot.get(p["continente"], 0) + p["total"]["votantes"]
        )
    grandes.sort(
        key=lambda p: (-cont_vot[p["continente"]], -p["total"]["votantes"], p["pais"])
    )

    def lugares(mods: dict[str, dict[str, Any]]) -> tuple[list, list[str]]:
        cel: list[dict[str, Any] | None] = []
        vaz: list[str] = []
        for m in modelos:
            x = mods.get(m)
            if x and x["votantes"] >= minimo_lugar:
                cel.append(x)
                vaz.append("")
            else:
                cel.append(None)
                vaz.append(f"só {inteiro(x['votantes'])} votantes" if x else "")
        return cel, vaz

    out = []
    for p in grandes:
        cel, vaz = lugares({m["modelo"]: m for m in p["modelos"]})
        out.append(
            Linha(
                p["pais"],
                p["pais_nome"],
                p["pais_nome"],
                p["continente"],
                cel,
                vaz,
                p["total"],
                {"cidades": p["cidades"], "modelos": p["modelos"]},
            )
        )
    if pequenos:
        mods = {
            m: _soma([x for p in pequenos for x in p["modelos"] if x["modelo"] == m])
            for m in modelos
        }
        mods = {m: x for m, x in mods.items() if x["secoes"]}
        cel, vaz = lugares(mods)
        out.append(
            Linha(
                "outros",
                "outros países",
                f"Outros {len(pequenos)} países",
                "Demais países",
                cel,
                vaz,
                _soma([p["total"] for p in pequenos]),
                {"paises": pequenos},
            )
        )
    tot = E["votantes"] or 1
    secoes_mod = {
        m: sum(x["secoes"] for p in P for x in p["modelos"] if x["modelo"] == m)
        for m in modelos
    }
    papel = [x for p in P for x in p["modelos"] if x["modelo"] == SEM_MODELO]
    resumo = {
        "paises": len(P),
        "grandes": len(grandes),
        "pequenos": len(pequenos),
        "votantes": E["votantes"],
        "votantes_grandes": sum(p["total"]["votantes"] for p in grandes),
        "pct_grandes": 100 * sum(p["total"]["votantes"] for p in grandes) / tot,
        "secoes": E["secoes"],
        "secoes_modelo": secoes_mod,
        "papel_secoes": sum(x["secoes"] for x in papel),
        "papel_cedula": sum(x.get("secoes_cedula") or 0 for x in papel),
        "papel_votantes": sum(x["votantes"] for x in papel),
        "sem_voto": max(E.get("paises_na_tabela", 0) - len(P), 0),
        "sem_pais": E.get("sem_pais") or {"secoes": 0, "votantes": 0},
    }
    return modelos, out, resumo


def _mais_nova(linha: Linha, modelos: Sequence[str]) -> tuple[str, dict] | None:
    """O modelo mais novo exibido (nunca o papel), se a linha tem dois ou mais."""
    cheios = [
        (m, c)
        for m, c in zip(modelos, linha.celulas, strict=True)
        if c is not None and m != SEM_MODELO
    ]
    return cheios[-1] if len(cheios) > 1 else None


def extremos(modelos: Sequence[str], linhas: Sequence[Linha]) -> dict[str, Any] | None:
    """Onde a urna mais nova da linha dá mais e menos a Flávio contra o total da linha.

    Só entram linhas com dois modelos exibidos ou mais (com um só, o modelo e o
    total são quase a mesma coisa). Devolve as duas pontas e quantas linhas entram.
    """
    casos = []
    for ln_ in linhas:
        if ln_.id == "outros":
            continue
        mn = _mais_nova(ln_, modelos)
        if mn is None:
            continue
        m, c = mn
        tf = ln_.total["flavio_pct"]
        if c["flavio_pct"] is None or tf is None:
            continue
        casos.append(
            {
                "id": ln_.id,
                "nome": ln_.nome,
                "modelo": m,
                "celula": c,
                "total": ln_.total,
                "dif_flavio": c["flavio_pct"] - tf,
                "dif_lula": (c["lula_pct"] or 0) - (ln_.total["lula_pct"] or 0),
            }
        )
    if len(casos) < 2:
        return None
    casos.sort(key=lambda x: -x["dif_flavio"])
    return {
        "mais": casos[0],
        "menos": casos[-1],
        "linhas": len(casos),
        "positivas": sum(round(x["dif_flavio"], 1) > 0 for x in casos),
        "negativas": sum(round(x["dif_flavio"], 1) < 0 for x in casos),
    }


# ------------------------------------------------------------------ desenho
# Desenho compacto: o SVG inteiro herda família, corpo 13 e cinza de um <g>, e
# cada texto só escreve o que muda. São mais de mil textos por figura, e os
# atributos repetidos dobravam o peso do HTML.


def _n(v: float) -> str:
    s = f"{v:.1f}"
    return s.removesuffix(".0")


def _tx(
    x: float,
    y: float,
    s: Any,
    fill: str | None = None,
    anchor: str = "start",
    weight: str | None = None,
    size: int | None = None,
) -> str:
    a = f'<text x="{_n(x)}" y="{_n(y)}"'
    if size:
        a += f' font-size="{size}"'
    if fill:
        a += f' fill="{fill}"'
    if anchor != "start":
        a += f' text-anchor="{anchor}"'
    if weight:
        a += f' font-weight="{weight}"'
    return a + f">{escape(str(s))}</text>"


def _rt(x: float, y: float, w: float, h: float, fill: str, extra: str = "") -> str:
    return (
        f'<rect x="{_n(x)}" y="{_n(y)}" width="{_n(max(w, 0))}" height="{_n(h)}" '
        f'fill="{fill}"{extra}/>'
    )


def _abre(w: float, h: float, titulo: str, desc: str) -> str:
    return (
        svg_abre(w, h, titulo, desc)
        + f'<g font-family="{FONTE}" font-size="13" fill="{MUTED}">'
    )


def _rotulo_barra(letra: str, v: float, largura: float) -> str:
    """'F 47' se couber, só '47' se couber o número, vazio se nada couber."""
    n = num(v, 0)
    for s in (f"{letra} {n}", n):
        if largura >= CARACTERE * len(s) + 8:
            return s
    return ""


def barra(
    x: float, y: float, w: float, h: float, c: dict[str, Any], total: bool = False
) -> str:
    """100% dos válidos: Flávio da esquerda, Lula da direita, demais no meio."""
    f, lu = c["flavio_pct"] or 0, c["lula_pct"] or 0
    wf, wl = w * f / 100, w * lu / 100
    contorno = f' stroke="{INK}" stroke-width="1.6"' if total else ""
    g = [_rt(x, y, w, h, DEMAIS, contorno)]
    if wf >= 0.5:
        g.append(_rt(x, y, wf, h, FLAVIO))
    if wl >= 0.5:
        g.append(_rt(x + w - wl, y, wl, h, LULA))
    xm = _n(x + w / 2)
    g.append(
        f'<path d="M{xm} {_n(y - 5)}v5M{xm} {_n(y + h)}v5" stroke="{INK}" '
        'stroke-width="1.2" fill="none"/>'
    )
    yt = y + h / 2 + 4.5
    sf = _rotulo_barra("F", f, wf)
    if sf:
        g.append(_tx(x + 5, yt, sf, "#ffffff", weight="600"))
    sl = _rotulo_barra("L", lu, wl)
    if sl:
        g.append(_tx(x + w - 5, yt, sl, "#ffffff", "end", "600"))
    return "".join(g)


def _vazio(x: float, y: float, w: float, h: float, texto: str) -> str:
    """Lugar tracejado; o texto só aparece quando o modelo existe e é pequeno."""
    caixa = _rt(x, y, w, h, "none", f' stroke="{VAZIO}" stroke-dasharray="4 3"')
    if not texto:
        return caixa
    return caixa + _tx(x + w / 2, y + h / 2 + 4.5, texto, anchor="middle")


@dataclass
class Forma:
    """O que muda entre a figura das UFs e a do exterior."""

    titulo: str
    desc: str
    rot_w: float
    cab_total: str
    sub: Callable[[dict[str, Any]], str]
    num_rot: str
    num_val: Callable[[dict[str, Any]], str]
    cab_estreito: Callable[[Linha], str]


def _grupos(linhas: Sequence[Linha]) -> list[tuple[str, list[Linha]]]:
    out: list[tuple[str, list[Linha]]] = []
    for ln_ in linhas:
        if not out or out[-1][0] != ln_.grupo:
            out.append((ln_.grupo, []))
        out[-1][1].append(ln_)
    return out


def svg_larga(
    modelos: Sequence[str], linhas: Sequence[Linha], forma: Forma, keys: dict
) -> str:
    w, n = LARGA, len(modelos)
    x0, x1 = forma.rot_w, w - 16
    gap, extra = 14, 14
    sw = (x1 - x0 - gap * n - extra) / (n + 1)
    xs = [x0 + j * (sw + gap) for j in range(n)] + [x0 + n * (sw + gap) + extra]
    cab = [_rotulo_modelo(m) for m in modelos] + [forma.cab_total]
    linha_h, bar_h = 52, 22
    corpo, y = [], 8
    for grupo, lins in _grupos(linhas):
        corpo.append(_tx(16, y + 20, grupo, weight="700", size=14))
        for j, s in enumerate(cab):
            fim = j == n
            corpo.append(
                _tx(
                    xs[j] + sw / 2,
                    y + 20,
                    s,
                    INK if fim else None,
                    "middle",
                    "700" if fim else "600",
                )
            )
        corpo.append(ln(16, y + 30, x1, y + 30, GRADE, 0.8))
        y += 42
        for lin in lins:
            yb = y + 4
            corpo.append(_tx(x0 - 14, yb + 16, lin.rotulo, INK, "end", "700", 14))
            for j, c in enumerate(lin.celulas):
                if c is None:
                    corpo.append(_vazio(xs[j], yb, sw, bar_h, lin.vazios[j]))
                    continue
                corpo.append(hit(barra(xs[j], yb, sw, bar_h, c), keys[(lin.id, j)]))
                corpo.append(_tx(xs[j], yb + bar_h + 18, forma.sub(c)))
            corpo.append(
                hit(
                    barra(xs[n], yb, sw, bar_h, lin.total, total=True),
                    keys[(lin.id, "total")],
                )
            )
            corpo.append(_tx(xs[n], yb + bar_h + 18, forma.sub(lin.total)))
            y += linha_h
        y += 6
    xsep = xs[n] - (gap + extra) / 2
    corpo.append(ln(xsep, 8, xsep, y - 6, GRADE, 1))
    return _abre(w, y + 4, forma.titulo, forma.desc) + "".join(corpo) + "</g></svg>"


def svg_estreita(
    modelos: Sequence[str], linhas: Sequence[Linha], forma: Forma, keys: dict
) -> str:
    """Uma UF (ou país) por bloco; só os modelos presentes, o total por último."""
    w = ESTREITA
    xl, xb0, xb1, xn = 16, 82, w - 66, w - 16
    bw, bar_h, linha_h = xb1 - xb0, 20, 30
    corpo, y = [], 8
    for grupo, lins in _grupos(linhas):
        corpo.append(_tx(xl, y + 20, grupo, weight="700", size=15))
        corpo.append(ln(xl, y + 28, xn, y + 28, GRADE, 0.8))
        y += 36
        for lin in lins:
            corpo.append(
                _tx(xl, y + 16, forma.cab_estreito(lin), INK, weight="700", size=15)
            )
            corpo.append(_tx(xn, y + 16, forma.num_rot, anchor="end"))
            y += 26
            itens = [
                (j, _rotulo_modelo(modelos[j]), c)
                for j, c in enumerate(lin.celulas)
                if c is not None
            ]
            itens.append(("total", "total", lin.total))
            for j, rot, c in itens:
                tot = j == "total"
                corpo.append(_tx(xl, y + 16, rot, INK, weight="700" if tot else "600"))
                corpo.append(
                    hit(
                        barra(xb0, y + 2, bw, bar_h, c, total=tot)
                        + area(xb0, y - 2, bw, bar_h + 8),
                        keys[(lin.id, j)],
                    )
                )
                corpo.append(_tx(xn, y + 17, forma.num_val(c), anchor="end"))
                y += linha_h
            y += 10
        y += 4
    return _abre(w, y + 4, forma.titulo, forma.desc) + "".join(corpo) + "</g></svg>"


def _legenda_cores() -> str:
    return legenda_html(
        [
            ("Flávio, % dos válidos", FLAVIO),
            ("Lula, % dos válidos", LULA),
            ("demais candidatos", DEMAIS),
        ],
        "Cada barra é 100% dos votos válidos; o traço no meio marca 50%",
    )


def _contra(c: dict[str, Any], total: dict[str, Any], quem: str) -> str:
    a, b = c.get(f"{quem}_pct"), total.get(f"{quem}_pct")
    return "s/d" if a is None or b is None else f"{sinal(a - b, 2)} pp"


class Fichas:
    """Fichas em tabela compacta (`Tips.tabela`): título, subtítulo e campos fixos.

    Uma linha por barra, chave `r<i>`; campo vazio não aparece na ficha. Mais de
    cem fichas por figura em HTML repetiam a mesma tabela; em linhas, pesam um terço.
    """

    def __init__(self, campos: Sequence[str], nota: str) -> None:
        self.campos = ["titulo", "sub", *campos]
        self.nota = nota
        self.linhas: list[list[str]] = []

    def add(self, titulo: str, sub: str, valores: dict[str, str]) -> str:
        self.linhas.append(
            [titulo, sub, *(valores.get(c, "") for c in self.campos[2:])]
        )
        return f"r{len(self.linhas) - 1}"

    def tips(self) -> Tips:
        tp = Tips()
        tp.tabela(self.campos, self.linhas, sub=1, nota=self.nota)
        return tp


def _valores(c: dict[str, Any]) -> dict[str, str]:
    return {
        "Seções": inteiro(c["secoes"]),
        "Votantes": inteiro(c["votantes"]),
        "Flávio": _pct(c["flavio_pct"]),
        "Lula": _pct(c["lula_pct"]),
        "Abstenção": _pct(c["abstencao_pct"]),
    }


NOTA_FICHA = (
    "Flávio e Lula em % dos válidos; abstenção em % dos aptos. Diferença bruta não é "
    "efeito da máquina."
)


# ------------------------------------------------------------------ 1 por UF


def _secoes_txt(c: dict[str, Any]) -> str:
    n = c["secoes"]
    return f"{inteiro(n)} {'seção' if n == 1 else 'seções'}"


@registra("voto_modelo_uf_simples")
def voto_modelo_uf_simples(d, **_op) -> str:
    S = secoes(d)
    U = S["urna"]
    modelos, linhas = linhas_uf(U)
    F = Fichas(
        [
            "Seções",
            "Votantes",
            "Flávio",
            "Lula",
            "Abstenção",
            "Flávio contra a UF inteira",
            "Lula contra a UF inteira",
            "Seções sem lugar na linha",
        ],
        NOTA_FICHA,
    )
    keys: dict[tuple[str, Any], str] = {}
    for lin in linhas:
        T = lin.total
        for j, c in enumerate(lin.celulas):
            if c is None:
                continue
            keys[(lin.id, j)] = F.add(
                f"{lin.nome}: {modelos[j]}",
                "dentro da UF",
                {
                    **_valores(c),
                    "Flávio contra a UF inteira": _contra(c, T, "flavio"),
                    "Lula contra a UF inteira": _contra(c, T, "lula"),
                },
            )
        fora = sum(x["secoes"] for x in lin.extra["fora"])
        keys[(lin.id, "total")] = F.add(
            f"{lin.nome}: UF inteira",
            "todas as seções válidas da UF",
            {
                **_valores(T),
                "Seções sem lugar na linha": (
                    f"{inteiro(fora)} (modelo com menos de {MINIMO_SECOES} seções ou sem modelo)"
                    if fora
                    else ""
                ),
            },
        )
    tips = F.tips()
    forma = Forma(
        "Flávio e Lula por modelo de urna em cada UF",
        "Uma linha por UF, agrupadas por região. Em cada linha, uma barra por modelo de urna, do mais velho ao "
        "mais novo, e no fim a UF inteira; cada barra é 100% dos válidos, com Flávio em azul a partir da "
        "esquerda e Lula em vermelho a partir da direita.",
        76,
        "UF inteira",
        _secoes_txt,
        "seções",
        lambda c: inteiro(c["secoes"]),
        lambda lin: f"{lin.id} · {lin.nome}",
    )
    larga = svg_larga(modelos, linhas, forma, keys)
    estreita = svg_estreita(modelos, linhas, forma, keys)
    ext = [x for x in U["voto_por_uf_modelo"] if regiao_da_uf(x["uf"]) not in REGIOES]
    legenda = (
        "Cada barra é um modelo de urna na UF; a última barra é a UF inteira. "
        "Comparação bruta, modelo misturado com geografia; a leitura controlada está nas figuras seguintes. "
        "Lugar tracejado: a UF não tem o modelo (vazio) ou tem menos de "
        f"{MINIMO_SECOES} seções dele (com o número), e essas seções entram só na UF inteira. No celular, cada UF mostra só as barras preenchidas. Números das barras "
        "arredondados ao inteiro; a ficha traz duas casas."
        + (
            f" O exterior ({inteiro(sum(x['secoes'] for x in ext))} seções) está na figura seguinte."
            if ext
            else ""
        )
        + f" {nota_cobertura(S)} Fonte: secoes.json (urna.voto_por_uf_modelo e urna.voto_por_uf_total)."
    )
    return figura_html(
        "voto_modelo_uf_simples",
        larga_estreita(larga, estreita),
        legenda,
        tips,
        modo="full",
        apos=_legenda_cores(),
    )


# ------------------------------------------------------------------ 2 exterior


def _votantes_txt(c: dict[str, Any]) -> str:
    return f"{_secoes_txt(c)} · {inteiro(c['votantes'])} votantes"


def _cidades_do_modelo(lin: Linha, modelo: str) -> str:
    cs = [
        f"{nome_bonito(c['nome'])} ({inteiro(c['modelos'][modelo])})"
        for c in lin.extra.get("cidades", [])
        if modelo in (c.get("modelos") or {})
    ]
    return ", ".join(cs)


@registra("voto_modelo_exterior")
def voto_modelo_exterior(d, **_op) -> str:
    S = secoes(d)
    U = S["urna"]
    modelos, linhas, R = linhas_exterior(U)
    F = Fichas(
        [
            "Seções",
            "Votantes",
            "Flávio",
            "Lula",
            "Abstenção",
            "Flávio contra o total",
            "Lula contra o total",
            "Seções de cédula",
            "Cidades (seções)",
            "Cidades (votantes)",
            "Países",
        ],
        NOTA_FICHA,
    )
    keys: dict[tuple[str, Any], str] = {}
    for lin in linhas:
        T = lin.total
        varias = len(lin.extra.get("cidades") or []) > 1
        for j, c in enumerate(lin.celulas):
            if c is None:
                continue
            m = modelos[j]
            keys[(lin.id, j)] = F.add(
                f"{lin.nome}: {_rotulo_modelo(m)}",
                (
                    "sem log de urna; boletim do Sistema de Apuração"
                    if m == SEM_MODELO
                    else "dentro do país"
                ),
                {
                    **_valores(c),
                    "Flávio contra o total": _contra(c, T, "flavio"),
                    "Lula contra o total": _contra(c, T, "lula"),
                    "Seções de cédula": (
                        inteiro(c["secoes_cedula"])
                        if m == SEM_MODELO and c.get("secoes_cedula") is not None
                        else ""
                    ),
                    "Cidades (seções)": (
                        _cidades_do_modelo(lin, m) or "s/d" if varias else ""
                    ),
                },
            )
        paises = lin.extra.get("paises")
        keys[(lin.id, "total")] = F.add(
            f"{lin.nome}: {'todos' if paises else 'país inteiro'}",
            (
                f"países com menos de {inteiro(MINIMO_VOTANTES_PAIS)} votantes, somados"
                if paises
                else "todas as seções do país"
            ),
            {
                **_valores(T),
                "Cidades (votantes)": (
                    ", ".join(
                        f"{nome_bonito(c['nome'])} ({inteiro(c['votantes'])})"
                        for c in lin.extra["cidades"]
                    )
                    if varias
                    else ""
                ),
                "Países": inteiro(len(paises)) if paises else "",
            },
        )
    tips = F.tips()
    forma = Forma(
        "Flávio e Lula por país e modelo de urna no exterior",
        "Uma linha por país com ao menos 300 votantes, agrupados por continente, e uma linha com os demais "
        "países somados. Em cada linha, uma barra por modelo de urna e uma para as seções de cédula, e no "
        "fim o país inteiro; cada barra é 100% dos válidos, com Flávio em azul a partir da esquerda e Lula "
        "em vermelho a partir da direita.",
        190,
        "país inteiro",
        _votantes_txt,
        "votantes",
        lambda c: inteiro(c["votantes"]),
        lambda lin: lin.nome,
    )
    larga = svg_larga(modelos, linhas, forma, keys)
    estreita = svg_estreita(modelos, linhas, forma, keys)
    mod = R["secoes_modelo"]
    pred = max((m for m in modelos if m != SEM_MODELO), key=lambda m: mod[m])
    papel = ""
    if R["papel_secoes"]:
        todas = R["papel_cedula"] == R["papel_secoes"]
        papel = (
            f" Papel: as {inteiro(R['papel_secoes'])} seções sem modelo"
            + (
                " são todas de votação em cédula"
                if todas
                else f" incluem {inteiro(R['papel_cedula'])} de votação em cédula"
            )
            + f" ({inteiro(R['papel_votantes'])} votantes), apuradas no Sistema de Apuração; "
            "seção de papel não tem log de urna."
        )
    sem_pais = R["sem_pais"]
    legenda = (
        "Cada barra é um modelo de urna no país; a última barra é o país inteiro. "
        f"No exterior a {pred} predomina: {inteiro(mod[pred])} das {inteiro(R['secoes'])} seções."
        + papel
        + f" Uma linha por país com ao menos {inteiro(MINIMO_VOTANTES_PAIS)} votantes ({R['grandes']} países, "
        f"{num(R['pct_grandes'], 1)}% dos {inteiro(R['votantes'])} votantes do exterior); os outros "
        f"{R['pequenos']} países estão somados na última linha. Lugar tracejado: o país não tem o modelo "
        f"(vazio) ou tem menos de {inteiro(MINIMO_VOTANTES_LUGAR)} votantes nele (com o número). Comparação "
        "bruta, modelo misturado com geografia: dentro de um país, cada modelo fica em certas cidades, e a "
        "ficha diz quais. No celular, cada país mostra só as barras preenchidas."
        + (
            f" {R['sem_voto']} países da tabela de cidades não têm seção com voto."
            if R["sem_voto"]
            else ""
        )
        + (
            f" {inteiro(sem_pais['secoes'])} seções sem país na tabela ficam fora."
            if sem_pais.get("secoes")
            else ""
        )
        + " Fonte: secoes.json (urna.voto_por_pais_modelo), país pela tabela de cidades do exterior."
    )
    return figura_html(
        "voto_modelo_exterior",
        larga_estreita(larga, estreita),
        legenda,
        tips,
        modo="full",
        apos=_legenda_cores(),
    )


__all__ = [
    "MINIMO_VOTANTES_LUGAR",
    "MINIMO_VOTANTES_PAIS",
    "Linha",
    "barra",
    "extremos",
    "linhas_exterior",
    "linhas_uf",
    "modelos_uf",
    "voto_modelo_exterior",
    "voto_modelo_uf_simples",
]
