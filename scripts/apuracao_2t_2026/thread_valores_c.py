"""Valores dos cards 25 e 26 da thread do 2º turno.

Card 25, "Onde Flávio teve menos votos": contas de ``turnos_perdas`` sobre
``comparacao_1t.json`` e ``governadores.json``, as mesmas da subparte do capítulo
"1º turno × 2º turno" do dossiê, e o CSV da lista pelo manifesto do dataset.

Card 26, "Pendência documental": ``logs.json`` (``metadados.serie_mr``,
``metadados.dossie_metadados`` e ``rdv``), com a lista de casos conferida em
``metadados.json`` e o pleito lido de ``urnas.json``.

Nada é digitado: os números saem dos JSONs. A única constante textual é a citação
da Lei de Acesso à Informação, a mesma do dossiê (``pagina_texto_logs.pendencia_tse``),
e um teste confere as duas.
"""

from __future__ import annotations

import math
from functools import cache
from typing import Any

from apuracao_2026.pagina_texto_terceira_via import NA_UF
from apuracao_2026.thread_base import mi, nome_proprio, num, pct, sinal

from . import turnos_perdas as TP
from .dataset import ler_manifesto
from .pagina_texto_turnos_perdas import ANCORA as ANCORA_PERDAS
from .thread_base import DOSSIE, ROOT, URL_DOSSIE, dado
from .thread_valores import NOME_UF

SITE = "https://brasil.arvor.co/"
ANCORA_LOGS = "logs"
# Citação legal (não é medição); a mesma do dossiê, conferida em teste.
LEI_ACESSO = "Lei 12.527/2011"
REGIOES_NNE = ("Norte", "Nordeste")


# ------------------------------------------------------------------ apoio


def _lista(itens: list[str]) -> str:
    return (
        ", ".join(itens[:-1]) + " e " + itens[-1] if len(itens) > 1 else "".join(itens)
    )


def _na(uf: str, inicio: bool = False) -> str:
    """'no Amapá', 'em Roraima'; maiúscula no começo da frase."""
    s = f"{NA_UF.get(uf, 'em')} {NOME_UF.get(uf, uf)}"
    return s[:1].upper() + s[1:] if inicio else s


def _saldo(v: float, coisa: str) -> str:
    """'486.922 votos a mais' ou 'a menos', pelo sinal."""
    return f"{num(abs(v))} {coisa} {'a menos' if v < 0 else 'a mais'}"


def _pontos(v: float) -> str:
    """'+0,19 ponto', '+2,99 pontos': plural a partir de dois."""
    return f"{sinal(v, 2)} {'ponto' if abs(round(v, 2)) < 2 else 'pontos'}"


def _ic(bloco: dict[str, Any]) -> str:
    lo, hi = bloco["ic95_pp"]
    return f"{_pontos(bloco['media_pp'])} (IC95 de {sinal(lo, 2)} a {sinal(hi, 2)})"


def _zero_dentro(bloco: dict[str, Any]) -> bool:
    lo, hi = bloco["ic95_pp"]
    return lo <= 0 <= hi


def _ancora_publicada(ancora: str) -> str:
    """Endereço da âncora no dossiê; falha se o HTML publicado não tiver o id."""
    html = (ROOT / "docs" / f"{DOSSIE}.html").read_text(encoding="utf-8")
    if f'id="{ancora}"' not in html:
        raise ValueError(f"âncora {ancora!r} ausente em docs/{DOSSIE}.html")
    return f"{URL_DOSSIE}#{ancora}"


@cache
def resumos() -> tuple[dict[str, Any], dict[str, Any], tuple[str, ...], dict]:
    """Resumos de Flávio e de Lula, UFs com 2º turno de governador e o contexto."""
    c1 = dado("comparacao_1t")
    gov = TP.ufs_governador(dado("governadores"))
    rf = TP.resumo(c1, "flavio", gov)
    rl = TP.resumo(c1, "lula", gov)
    return rf, rl, tuple(sorted(gov)), TP.contexto_governador(c1, gov)


def _csv_flavio(n: int) -> str:
    """URL pública do CSV da lista de Flávio; falha se o manifesto não bater com o JSON."""
    m = ler_manifesto() or {}
    e = next(
        (x for x in m.get("listas_municipais") or [] if x["candidato"] == "flavio"),
        None,
    )
    if e is None or e["n_linhas"] != n or not (ROOT / e["arquivo"]).exists():
        raise ValueError(
            "manifesto do dataset sem a lista de Flávio coerente com o JSON"
        )
    return SITE + e["arquivo"].removeprefix("docs/")


# ------------------------------------------------------------------ 25 perdas


def _frases_uf(rf: dict[str, Any]) -> dict[str, str]:
    com = sorted((u for u in rf["por_uf"] if u["n"]), key=lambda u: (-u["n"], u["uf"]))
    top = _lista([f"{u['nome']} ({num(u['n'])} de {num(u['n_uf'])})" for u in com[:5]])
    todos = [u for u in com if u["n"] == u["n_uf"]]
    nenhum = sorted((u for u in rf["por_uf"] if not u["n"]), key=lambda u: u["nome"])
    frase_todos = ""
    if todos:
        lugares = _lista([_na(u["uf"], i == 0) for i, u in enumerate(todos)])
        contas = _lista([f"{num(u['n'])} de {num(u['n_uf'])}" for u in todos])
        frase_todos = (
            f" {lugares}, Flávio teve menos votos em todos os municípios ({contas})."
        )
    frase_nenhum = ""
    if nenhum:
        lugares = _lista([_na(u["uf"], i == 0) for i, u in enumerate(nenhum)])
        frase_nenhum = f" {lugares}, em nenhum."
    return {
        "mv_top_ufs": top,
        "mv_todos_frase": frase_todos,
        "mv_nenhum_frase": frase_nenhum,
    }


def _frase_governador(ctx: dict[str, Any], gov: tuple[str, ...]) -> dict[str, str]:
    com, sem = ctx["com"], ctx["sem"]
    mais = com["comparecimento_caiu"] * sem["n"] > sem["comparecimento_caiu"] * com["n"]
    leitura = (
        "A queda foi mais comum onde houve 2º turno de governador, o contrário do "
        "que essa leitura prevê."
        if mais
        else "A queda foi menos comum onde houve 2º turno de governador, o que é "
        "compatível com essa leitura, mas não a identifica."
    )
    return {
        "gv_n": str(len(gov)),
        "gv_ufs": _lista([NOME_UF[u] for u in gov]),
        "gv_com": f"{num(com['comparecimento_caiu'])} de {num(com['n'])}",
        "gv_com_pct": pct(com["pct"], 1),
        "gv_sem": f"{num(sem['comparecimento_caiu'])} de {num(sem['n'])}",
        "gv_sem_pct": pct(sem["pct"], 1),
        "gv_leitura": leitura,
    }


def v_perdas() -> dict:
    """Card "Onde Flávio teve menos votos no 2º turno"."""
    rf, rl, gov, ctx = resumos()
    reg = rf["por_regiao"]
    manteve = [c for c in rf["categorias"] if not c["comparecimento_caiu"]]
    cobre = rf["n_alem_teto_adversario_cobre"]
    caiu_l = rl["n_comparecimento_caiu"]
    maior, maior_l = rf["maior"], rl["maior"]
    return {
        "mv_n": num(rf["n"]),
        "mv_universo": num(rf["n_universo"]),
        "mv_perda": num(rf["perda"]),
        "mv_aptos": mi(rf["aptos"]),
        "mv_aptos_pct": pct(100 * rf["aptos"] / rf["aptos_universo"], 1),
        "mv_lula_saldo": _saldo(rf["delta_adversario"], "votos"),
        "mv_lula_subiu": num(rf["n_adversario_ganhou"]),
        "mv_comp_caiu": num(rf["n_comparecimento_caiu"]),
        "mv_comp_saldo": _saldo(rf["delta_comparecimento"], "eleitores"),
        "mv_nne": num(sum(reg.get(r, 0) for r in REGIOES_NNE)),
        "mv_maior": f"{nome_proprio(maior['nome'])} ({maior['uf']})",
        "mv_maior_v": num(maior["perda"]),
        **_frases_uf(rf),
        "mv_teto": num(rf["teto"]),
        "mv_alem_teto": num(rf["alem_teto"]),
        "mv_n_alem_teto": num(rf["n_alem_teto"]),
        "mv_cobre_teto": (
            "em todos eles" if cobre == rf["n_alem_teto"] else f"em {num(cobre)} deles"
        ),
        "mv_prop": num(rf["proporcional"]),
        "mv_prop_pct": pct(100 * rf["proporcional"] / rf["perda"], 1),
        "mv_alem_prop": num(rf["alem_proporcional"]),
        "mv_n_alem_prop": num(rf["n_alem_proporcional"]),
        "mv_n_manteve": num(sum(c["n"] for c in manteve)),
        "mv_perda_manteve": num(sum(c["perda"] for c in manteve)),
        "ml_n": num(rl["n"]),
        "ml_perda": num(rl["perda"]),
        "ml_caiu": (
            f"em todos os {num(rl['n'])}"
            if caiu_l == rl["n"]
            else f"em {num(caiu_l)} dos {num(rl['n'])}"
        ),
        "ml_prop_pct": pct(100 * rl["proporcional"] / rl["perda"], 1),
        "ml_maior": f"{nome_proprio(maior_l['nome'])} ({maior_l['uf']})",
        "ml_maior_v": num(maior_l["perda"]),
        **_frase_governador(ctx, gov),
        "mv_url_cap": _ancora_publicada(ANCORA_PERDAS),
        "mv_csv": _csv_flavio(rf["n"]),
    }


# ------------------------------------------------------------------ 26 pendência


@cache
def pendencia() -> dict[str, Any]:
    """Números crus do card da pendência documental, lidos de ``logs.json``."""
    lg = dado("logs")
    m = lg["metadados"]
    s = m["serie_mr"]
    d = m["dossie_metadados"]
    et = d["entre_turnos_vsc"]
    tot = d["certificado_realocado_totais"]
    realocado = next(g for g in d["voto"] if g["grupo"] == "certificado_realocado")
    brasil = [x for x in s["estruturais"] if x["ufs"] != ["ZZ"]]
    exterior = [x for x in s["estruturais"] if x["ufs"] == ["ZZ"]]
    casos = dado("metadados")["entre_turnos_vsc"][
        "certificado_do_1t_em_outra_secao_no_2t_casos"
    ]
    n = et["certificado_do_1t_em_outra_secao_no_2t"]
    if len(casos) != n or tot["2t"]["secoes"] != n:
        raise ValueError(
            "lista de urnas realocadas em metadados.json não bate com logs.json"
        )
    if (
        sum(x["secoes"] for x in brasil)
        != s["voto_estruturais_brasil"]["secoes_com_sinal"]
    ):
        raise ValueError("grupos estruturais do Brasil não batem com a conta do voto")
    pleitos = dado("urnas")["turnos"]["2t"]["carga"]["pleito"]
    if len(pleitos) != 1:
        raise ValueError("mais de um pleito no 2º turno de urnas.json")
    return {
        "serie": s,
        "brasil": brasil,
        "exterior": exterior,
        "voto_mr": s["voto_estruturais_brasil"],
        "et": et,
        "tot": tot,
        "realocado": realocado,
        "log_nao_confere": d["certificado_realocado_log_nao_confere"],
        "rdv": lg["rdv"],
        "pleito": pleitos[0]["valor"],
    }


def _blocos(brasil: list[dict[str, Any]]) -> str:
    """'zonas 162 (RJ, 169 seções), 119 (RJ, 114) ..., e outros 4 grupos, com 8 seções,
    na zona 187 (MG)'."""

    def zona(z: str) -> tuple[str, str]:
        uf, nz = z.split("-")
        return uf, nz

    grandes = [x for x in brasil if x["secoes"] >= 5]
    pequenos = [x for x in brasil if x["secoes"] < 5]
    partes = []
    for i, x in enumerate(grandes):
        uf, nz = zona(x["zonas"][0])
        partes.append(f"{nz} ({uf}, {num(x['secoes'])}{' seções' if i == 0 else ''})")
    txt = ("zonas " if len(partes) > 1 else "zona ") + _lista(partes) if partes else ""
    if pequenos:
        zonas = sorted({z for x in pequenos for z in x["zonas"]})
        if len(zonas) == 1:
            uf, nz = zona(zonas[0])
            onde = f"na zona {nz} ({uf})"
        else:
            onde = f"em {num(len(zonas))} zonas"
        txt += (
            f", e outros {num(len(pequenos))} grupos, com "
            f"{num(sum(x['secoes'] for x in pequenos))} seções, {onde}"
        )
    return txt


def v_pendencia() -> dict:
    """Card "Pendência documental: o que pedir ao TSE"."""
    P = pendencia()
    s, et, tot, rdv = P["serie"], P["et"], P["tot"], P["rdv"]
    t2, t1 = tot["2t"], tot["1t"]
    ext = P["exterior"]
    nao = P["log_nao_confere"]
    div = rdv["divergencias"]
    did_mr = P["voto_mr"]["dif_em_dif_contra_1t"]
    did_re = P["realocado"]["dif_em_dif_contra_1t"]
    f2 = 100 * t2["flavio"] / (t2["flavio"] + t2["lula"])
    f1 = 100 * t1["flavio"] / (t1["flavio"] + t1["lula"])
    esperados = s["pares_esperados_por_acaso_32_bits"]
    acaso = abs(s["pares_entre_lugares"] - esperados) <= 2 * math.sqrt(esperados)
    estr = s["estruturais"]
    fora = sum(x["secoes"] - x["contagem_confere"] for x in estr)
    return {
        "pd_rep": num(s["repetidos"]),
        "pd_rep_secoes": num(s["secoes_em_repeticao"]),
        "pd_pares": num(s["pares_entre_lugares"]),
        "pd_pares_esp": num(esperados, 1),
        "pd_pares_leitura": (
            "batem com o acaso" if acaso else "passam do que o acaso daria"
        ),
        "pd_grupos": num(len(P["brasil"])),
        "pd_mr_secoes": num(sum(x["secoes"] for x in P["brasil"])),
        "pd_blocos": _blocos(P["brasil"]),
        "pd_mr_contagem": (
            "que não aparece em nenhuma seção dos grupos"
            if fora == 0
            else f"que aparece em {num(fora)} das {num(sum(x['secoes'] for x in estr))} "
            "seções dos grupos"
        ),
        "pd_ext_secoes": num(sum(x["secoes"] for x in ext)),
        "pd_ext_cidades": num(sum(x["municipios"] for x in ext)),
        "pd_ext_grupos": num(len(ext)),
        "pd_mr_viz": _ic(P["voto_mr"]["contra_vizinhas_2t"]),
        "pd_mr_did": _ic(did_mr),
        "pd_mr_leitura": (
            "a diferença já existia no 1º turno, e o 2º não a moveu"
            if _zero_dentro(did_mr)
            else "o intervalo não contém o zero, e a mudança pede a mesma explicação"
        ),
        "pd_re_n": num(et["certificado_do_1t_em_outra_secao_no_2t"]),
        "pd_re_mun": num(tot["mesmo_municipio"]),
        "pd_re_zona": num(tot["mesma_zona"]),
        "pd_re_ufs": num(tot["ufs"]),
        "pd_re_aptos": num(t2["aptos"]),
        "pd_re_comp": num(t2["comparecimento"]),
        "pd_re_f2": pct(f2, 2),
        "pd_re_f1": pct(f1, 2),
        "pd_re_mov": (
            f"{'a queda' if f2 < f1 else 'a alta'} "
            f"{'' if _zero_dentro(did_re) else 'não '}acompanhou a das vizinhas"
        ),
        "pd_re_viz": _ic(P["realocado"]["fatia_flavio_2t_menos_vizinhas_do_municipio"]),
        "pd_re_did": _ic(did_re),
        "pd_re_log": (
            "Em todas, a contagem de votos do log fecha com o BU"
            if nao == 0
            else f"Em {num(nao)} delas, a contagem de votos do log não fecha com o BU"
        ),
        "pd_rdv": num(rdv["conferem"]),
        "pd_rdv_div": (
            "sem nenhuma divergência" if div == 0 else f"com {num(div)} divergências"
        ),
        "pd_lei": LEI_ACESSO,
        "pd_pleito": str(P["pleito"]),
        "pd_url_cap": _ancora_publicada(ANCORA_LOGS),
    }


__all__ = ["LEI_ACESSO", "pendencia", "resumos", "v_pendencia", "v_perdas"]
