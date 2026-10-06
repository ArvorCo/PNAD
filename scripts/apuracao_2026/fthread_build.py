"""Montagem e verificação da thread dos fiscais: junta valores, formata posts e
recusa texto fora da regra da casa (faixa de caracteres, travessão, hashtag, emoji,
algarismo digitado, rótulos de natureza)."""

from __future__ import annotations

from . import fiscais_cenarios as FC
from .fthread_base import PNG_DIR, cenarios, fiscais
from .fthread_posts import KIT, POSTS
from .fthread_valores import inteiro, v_cenarios, v_lista
from .thread_base import ROOT, digitos_soltos, problemas_de_texto

MIN_CHARS, MAX_CHARS = 2000, 2700
MIN_POSTS, MAX_POSTS = 5, 7
CAMPOS_TEXTO = ("tag", "titulo", "metrica", "metrica_rot", "fonte")
# Ordem de preferência dos casos no post 5: cobre as famílias e os marcos.
FAMILIAS_P = (("mesa", "cadastro"), ("entorno",), ("territorio",))
TETO_PARAGRAFO = 760


def _frase_caso(c: dict, J: dict) -> str:
    f = FC.fonte(J, c.get("fonte_thread") or c["fontes"][0])
    return (
        f"{c['titulo'].rstrip('.')} ({c['local']}, {c['ano']}). {c['resultado_curto'].rstrip('.')}. "
        f"Fonte: {f['veiculo']}, {FC.data_br(f['data'])}."
    )


def paragrafos_casos(J: dict) -> list[str]:
    """Três parágrafos de casos, um por grupo de famílias, até o teto de caracteres.

    Entram só os casos com `resultado_curto`, na ordem de `prioridade`.
    """
    cens = FC.por_id(J["cenarios"])
    rotulo = {
        ("mesa", "cadastro"): "Na mesa, no cadastro e na apuração.",
        ("entorno",): "No entorno da seção.",
        ("territorio",): "No território.",
    }
    out = []
    for fams in FAMILIAS_P:
        casos = [
            c
            for c in FC.casos_ordenados(J)
            if cens[c["cenario"]]["familia"] in fams and c.get("resultado_curto")
        ]
        casos.sort(key=lambda c: (c.get("prioridade", 9), c["data"]))
        texto = rotulo[fams]
        usados = 0
        for c in casos:
            frase = _frase_caso(c, J)
            if len(texto) + 1 + len(frase) > TETO_PARAGRAFO:
                continue
            usados += 1
            texto += " " + frase
        out.append(texto if usados else texto + " Nenhum caso com fonte na base.")
    return out


def v_casos() -> dict:
    J = cenarios()
    cs = FC.casos_ordenados(J)
    p1, p2, p3 = paragrafos_casos(J)
    return {
        "n_casos": inteiro(len(cs)),
        "ano_ini": str(cs[0]["ano"]),
        "ano_fim": str(cs[-1]["ano"]),
        "casos_p1": p1,
        "casos_p2": p2,
        "casos_p3": p3,
    }


def valores() -> dict:
    v: dict = {}
    for f in (v_lista, v_cenarios, v_casos):
        novos = f()
        repetidos = {k for k in novos if k in v and v[k] != novos[k]}
        if repetidos:
            raise ValueError(f"{f.__name__} redefine {sorted(repetidos)}")
        v.update(novos)
    return v


def montar() -> list[dict]:
    erros = FC.validar(cenarios(), {c["id"] for c in fiscais()["criterios"]})
    if erros:
        raise ValueError("fontes_fiscais.json: " + "; ".join(erros[:5]))
    v = valores()
    posts = []
    for p in POSTS:
        q = dict(p)
        for campo in CAMPOS_TEXTO:
            q[f"{campo}_f"] = p[campo].format_map(v)
        q["corpo"] = "\n\n".join(par.format_map(v) for par in p["texto"])
        q["svg"] = p["fig"]()
        posts.append(q)
    return posts


def verificar(posts: list[dict]) -> list[str]:
    """Lista de problemas; vazia quando a thread está dentro da regra."""
    erros = []
    if not MIN_POSTS <= len(posts) <= MAX_POSTS:
        erros.append(f"{len(posts)} posts, fora de {MIN_POSTS} a {MAX_POSTS}")
    for i, p in enumerate(posts, 1):
        n = len(p["corpo"])
        if not MIN_CHARS <= n <= MAX_CHARS:
            erros.append(f"post {i}: {n} caracteres")
        for m in [p[c] for c in CAMPOS_TEXTO] + list(p["texto"]):
            soltos = digitos_soltos(m)
            if soltos:
                erros.append(f"post {i}: algarismo digitado {soltos}")
        for txt in [p["corpo"], *(p[f"{c}_f"] for c in CAMPOS_TEXTO), p["svg"]]:
            for prob in problemas_de_texto(txt.replace("url(#", "url(")):
                if prob == "hashtag" and txt is p["svg"]:
                    continue
                erros.append(f"post {i}: {prob}")
    for titulo, sub in KIT:
        if digitos_soltos(titulo + " " + sub):
            erros.append(f"kit: algarismo digitado em {titulo!r}")
    for c in cenarios()["casos"]:
        if not 0 < len(c.get("rotulo_curto") or "") <= FC.ROTULO_MAX:
            erros.append(
                f"caso {c['id']}: rotulo_curto ausente ou acima de {FC.ROTULO_MAX}"
            )
    cen = [p for p in posts if p["tag"].startswith("Os cenários")]
    for p in cen:
        if "hipótese de risco" not in p["corpo"].lower():
            erros.append(f"post de cenário sem o rótulo hipótese de risco: {p['tag']}")
    for p in posts:
        if p["tag"] == "O que já aconteceu" and not p["corpo"].startswith("Verificado"):
            erros.append("post dos casos sem o rótulo verificado")
    if "validar com a PM e o TRE local" not in posts[-1]["corpo"]:
        erros.append("kit sem a frase validar com a PM e o TRE local")
    return erros


def caminhos_png(n: int) -> list[str]:
    rel = PNG_DIR.relative_to(ROOT / "docs")
    return [f"{rel.as_posix()}/{i:02d}.png" for i in range(1, n + 1)]


__all__ = [
    "CAMPOS_TEXTO",
    "MAX_CHARS",
    "MIN_CHARS",
    "caminhos_png",
    "montar",
    "paragrafos_casos",
    "valores",
    "verificar",
]
