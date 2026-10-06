"""Montagem e verificação da super thread: junta valores, formata posts e recusa
texto fora da regra da casa."""

from __future__ import annotations

from datetime import date

from . import thread_valores as VA
from . import thread_valores_b as VB
from .thread_base import PNG_DIR, ROOT, dado, digitos_soltos, problemas_de_texto
from .thread_fig_c import fig_checklist
from .thread_posts_a import POSTS_A
from .thread_posts_b import LIMITES, POSTS_B, etapas_checklist

MIN_CHARS, MAX_CHARS = 2000, 2700
MIN_POSTS, MAX_POSTS = 20, 25


def _data_curta(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{d.day:02d}/{d.month:02d}"


def valores() -> dict:
    v: dict = {}
    for f in (
        VA.v_resultado,
        VA.v_noite,
        VA.v_falha,
        VA.v_arquitetura,
        VA.v_regioes,
        VA.v_exterior,
        VA.v_camara,
        VA.v_senado,
        VA.v_assembleias,
        VA.v_governadores,
        VA.v_pesquisas,
        VA.v_voto_util,
        VB.v_anomalias,
        VB.v_secoes,
        VB.v_clusters,
        VB.v_urna,
        VB.v_fechamento,
        VB.v_lentidao,
        VB.v_fontes,
        VB.v_segundo_turno,
        VB.v_reguas,
        VB.v_militancia,
        VB.v_extras,
        VB.v_mais,
        VB.v_mais_b,
    ):
        novos = f()
        repetidos = {k for k in novos if k in v and v[k] != novos[k]}
        if repetidos:
            raise ValueError(f"{f.__name__} redefine {sorted(repetidos)}")
        v.update(novos)
    v["gerado_data"] = _data_curta(dado("presidente")["nacional"]["gerado_em_brt"])
    cit = VB.citacoes()
    for chave, ident in (
        ("cury", "cury_2t"),
        ("renan", "renan_noite"),
        ("zema_maio", "zema_maio"),
        ("zema_noite", "zema_noite_ncnews"),
        ("psd", "psd_liberou"),
    ):
        x = cit.get(ident)
        if x is None:
            raise ValueError(f"citação sem fonte arquivada: {ident}")
        trecho = CORTES.get(ident, x["trecho"])
        if trecho not in x["trecho"]:
            raise ValueError(f"corte fora do trecho arquivado: {ident}")
        v[f"cit_{chave}"] = f"“{trecho}”"
        v[f"cit_{chave}_veic"] = f"{x['veiculo']}, {_data_curta(x['data'])}"
    return v


# Cortes curtos dos trechos arquivados (sempre substrings literais deles).
CORTES = {
    "cury_2t": "ninguém está autorizado em meu nome",
    "renan_noite": "A eleição já é do Flávio Bolsonaro",
    "zema_maio": "terão meu total apoio contra o PT",
    "zema_noite_ncnews": "eu estarei contra o PT",
    "psd_liberou": "terão liberdade para definir seu apoio",
}

CAMPOS_TEXTO = ("tag", "titulo", "metrica", "metrica_rot", "fonte")


def montar() -> list[dict]:
    v = valores()
    posts = []
    for p in POSTS_A + POSTS_B:
        q = dict(p)
        for campo in CAMPOS_TEXTO:
            q[f"{campo}_f"] = p[campo].format_map(v)
        q["corpo"] = "\n\n".join(par.format_map(v) for par in p["texto"])
        if p.get("fig") is None:
            q["svg"] = fig_checklist(etapas_checklist(v))
        else:
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
        modelos = [p[c] for c in CAMPOS_TEXTO] + list(p["texto"])
        for m in modelos:
            soltos = digitos_soltos(m)
            if soltos:
                erros.append(f"post {i}: algarismo digitado {soltos}")
        textos = [p["corpo"], *(p[f"{c}_f"] for c in CAMPOS_TEXTO), p["svg"]]
        for txt in textos:
            for prob in problemas_de_texto(txt.replace("url(#", "url(")):
                if prob == "hashtag" and txt is p["svg"]:
                    continue
                erros.append(f"post {i}: {prob}")
    for _, _, itens in LIMITES:
        for item in itens:
            if digitos_soltos(item):
                erros.append(f"limites: algarismo digitado em {item!r}")
    if "juízo editorial" not in " ".join(p["corpo"].lower() for p in posts[-4:]):
        erros.append("posts do 2º turno sem o rótulo juízo editorial")
    for p in posts[-4:]:
        if "juízo editorial" not in p["corpo"].lower():
            erros.append(f"post estratégico sem juízo editorial: {p['tag_f']}")
    return erros


def caminhos_png(n: int) -> list[str]:
    rel = PNG_DIR.relative_to(ROOT / "docs")
    return [f"{rel.as_posix()}/{i:02d}.png" for i in range(1, n + 1)]


__all__ = ["CORTES", "caminhos_png", "montar", "valores", "verificar"]
