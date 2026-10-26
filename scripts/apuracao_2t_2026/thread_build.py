"""Montagem e verificação da thread do 2º turno: junta valores, formata posts e
recusa texto fora da regra da casa."""

from __future__ import annotations

from . import thread_valores as VA
from . import thread_valores_b as VB
from .thread_base import PNG_DIR, ROOT, URL_DOSSIE, digitos_soltos, problemas_de_texto
from .thread_fig_b import fig_fecho
from .thread_posts_a import POSTS_A
from .thread_posts_b import POSTS_B

MIN_CHARS, MAX_CHARS = 2000, 2700
MIN_POSTS, MAX_POSTS = 16, 21
# TESE.md (26/10/2026): o afastamento é medida da mudança, não confissão de erro.
VETADAS_TESE = (
    "nós erramos",
    "erramos",
    "errou junto",
    "a casa errou",
    "erraram para o mesmo lado",
    "contraprova",
    "o que a casa muda daqui para frente",
)
CAMPOS_TEXTO = ("tag", "titulo", "metrica", "metrica_rot", "fonte")
FONTES_VALORES = (
    VA.v_resultado,
    VA.v_noite,
    VA.v_prorrogacao,
    VA.v_projecao,
    VA.v_cedo_tarde,
    VA.v_turnos,
    VA.v_abstencao,
    VB.v_secoes,
    VB.v_voto,
    VB.v_pesquisas,
    VB.v_casa,
    VB.v_mudanca,
    VB.v_transferencia,
    VB.v_logs,
    VB.v_hipoteses,
    VB.v_hipotese,
    VB.v_paralela,
    VB.v_limites,
    VB.v_fecho,
)


def valores() -> dict:
    v: dict = {}
    for f in FONTES_VALORES:
        novos = f()
        repetidos = {k for k in novos if k in v and v[k] != novos[k]}
        if repetidos:
            raise ValueError(f"{f.__name__} redefine {sorted(repetidos)}")
        v.update(novos)
    return v


def montar() -> list[dict]:
    v = valores()
    posts = []
    for p in POSTS_A + POSTS_B:
        q = dict(p)
        for campo in CAMPOS_TEXTO:
            q[f"{campo}_f"] = p[campo].format_map(v)
        q["corpo"] = "\n\n".join(par.format_map(v) for par in p["texto"])
        q["svg"] = fig_fecho(v) if p["fig"] == "fecho" else p["fig"]()
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
        for txt in [p["corpo"], *(p[f"{c}_f"] for c in CAMPOS_TEXTO)]:
            for prob in problemas_de_texto(txt):
                erros.append(f"post {i}: {prob}")
        for prob in problemas_de_texto(p["svg"].replace("url(#", "url(")):
            if prob != "hashtag":
                erros.append(f"post {i} (figura): {prob}")
    for i in (0, len(posts) - 1):
        if URL_DOSSIE not in posts[i]["corpo"]:
            erros.append(f"post {i + 1} sem o link do dossiê")
    if not any("sábado" in p["tag_f"].lower() for p in posts):
        erros.append("falta o card do que mudou entre sábado e domingo")
    for i, p in enumerate(posts, 1):
        baixo = (p["corpo"] + p["titulo_f"] + p["tag_f"]).lower()
        for frase in VETADAS_TESE:
            if frase in baixo:
                erros.append(f"post {i}: frase vetada pela tese editorial: {frase!r}")
    return erros


def caminhos_png(n: int) -> list[str]:
    rel = PNG_DIR.relative_to(ROOT / "docs")
    return [f"{rel.as_posix()}/{i:02d}.png" for i in range(1, n + 1)]


__all__ = ["CAMPOS_TEXTO", "caminhos_png", "montar", "valores", "verificar"]
