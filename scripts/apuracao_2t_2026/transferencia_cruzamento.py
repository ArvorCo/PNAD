"""Cenários de cruzamento entre as bases de Lula e Flávio (capítulo "De onde veio o voto").

O cruzamento (eleitor de Lula no 1º turno que votou em Flávio no 2º, e o
contrário) não é observado nas urnas e as pesquisas discordam entre si sobre ele:
a Quaest publicou zero nas duas direções, a Nexus entre 1% e 2%. Em vez de deixar
o ajuste escolher, cada cenário fixa as duas células e o IPF distribui o resto, UF
a UF, até bater exatamente as duas urnas. Assim a página mostra o que depende do
cruzamento e o que as urnas impõem a todos os cenários.

A figura junta brancos e nulos dos dois lados (nove origens, quatro destinos).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from . import transferencia_ipf as I
from . import transferencia_priors as P

ORIG_FIG = (
    "lula",
    "flavio",
    "cury",
    "renan",
    "caiado",
    "zema",
    "outros",
    "bn",
    "abstencao",
)
DEST_FIG = ("lula", "flavio", "bn", "abstencao")
JUNTA_O = {"brancos": "bn", "nulos": "bn"}
JUNTA_D = {"brancos": "bn", "nulos": "bn"}
TIPOS = ("medido", "regressao", "estimado", "zero")
LIMIAR_ROTULO = 500_000
"""Fita com menos de meio milhão de votos não leva rótulo na fita; vai para a lista ao lado."""


def agrega(M: np.ndarray) -> np.ndarray:
    """Matriz 10 × 5 do ajuste vira a 9 × 4 da figura (brancos e nulos somados)."""
    F = np.zeros((len(ORIG_FIG), len(DEST_FIG)))
    for i, a in enumerate(P.ORIGENS):
        ia = ORIG_FIG.index(JUNTA_O.get(a, a))
        for j, b in enumerate(P.DESTINOS):
            F[ia, DEST_FIG.index(JUNTA_D.get(b, b))] += M[i, j]
    return F


def tipo_fig(a: str, b: str, cruz: str | None) -> str:
    """Natureza do elo da figura; o branco e nulo herda a regra de brancos e de nulos."""
    oa = "brancos" if a == "bn" else a
    ob = "brancos" if b == "bn" else b
    return P.tipo_elo(oa, ob, cruz)


def _pct(M: np.ndarray, eixo: int) -> np.ndarray:
    tot = M.sum(axis=eixo, keepdims=True)
    return np.divide(100 * M, tot, out=np.zeros_like(M), where=tot > 0)


def _dict(M: np.ndarray, orig: tuple, dest: tuple, casas: int) -> dict:
    return {
        a: {b: round(float(M[i, j]), casas) for j, b in enumerate(dest)}
        for i, a in enumerate(orig)
    }


def bloco(M: np.ndarray, cruz: str | None) -> dict[str, Any]:
    """Matriz inteira em votos e em % da origem e do destino, mais a da figura."""
    F = agrega(M)
    tipos = {a: {b: tipo_fig(a, b, cruz) for b in DEST_FIG} for a in ORIG_FIG}
    cont: dict[str, dict[str, float]] = {t: {"fitas": 0, "votos": 0.0} for t in TIPOS}
    for i, a in enumerate(ORIG_FIG):
        for j, b in enumerate(DEST_FIG):
            c = cont[tipos[a][b]]
            c["fitas"] += 1
            c["votos"] += float(F[i, j])
    tot = float(F.sum())
    for c in cont.values():
        c["pct_votos"] = 100 * c["votos"] / tot
    return {
        "matriz": _dict(M, P.ORIGENS, P.DESTINOS, 0),
        "pct_origem": _dict(_pct(M, 1), P.ORIGENS, P.DESTINOS, 4),
        "pct_destino": _dict(_pct(M, 0), P.ORIGENS, P.DESTINOS, 4),
        "figura": {
            "origens": list(ORIG_FIG),
            "destinos": list(DEST_FIG),
            "votos": _dict(F, ORIG_FIG, DEST_FIG, 0),
            "pct_origem": _dict(_pct(F, 1), ORIG_FIG, DEST_FIG, 4),
            "pct_destino": _dict(_pct(F, 0), ORIG_FIG, DEST_FIG, 4),
            "tipos": tipos,
            "contagem_tipos": cont,
            "limiar_rotulo_votos": LIMIAR_ROTULO,
        },
    }


def roda(
    margens: Mapping[str, Mapping[str, Any]],
    piso: Mapping[str, Any],
    b: Mapping[str, float],
    nac: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Os quatro cenários, cada um com o objeto do ajuste (`cen`) e o bloco do JSON."""
    out = {}
    for k, op in P.cenarios_cruzamento().items():
        par = (op["lula_para_flavio"], op["flavio_para_lula"])
        cen = I.cenario(
            margens,
            piso,
            b,
            nome=op["nome"],
            descricao=op["descricao"],
            cruzamento=par,
        )
        out[k] = {
            "cen": cen,
            "json": {
                "nome": op["nome"],
                "botao": op["botao"],
                "descricao": op["descricao"],
                "tipo_cruzamento": op["tipo"],
                "lula_para_flavio_pct": 100 * par[0],
                "flavio_para_lula_pct": 100 * par[1],
                **bloco(cen["matriz"], op["tipo"]),
                "metricas": I.metricas(cen["matriz"], nac),
                "confere": I.confere_margens(cen, margens),
                "diagnostico": cen["diagnostico"],
                "alpha": cen["alpha"],
                "rotatividade": cen["churn_nacional"],
            },
        }
    return out


def _faixa(vals: list[float]) -> list[float]:
    return [min(vals), max(vals)]


def comparacao(cenarios: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """O que muda entre os cenários e o que as urnas e a regressão impõem a todos."""
    ms = [c["metricas"] for c in cenarios.values()]

    def f(chave: str) -> list[float]:
        return _faixa([m[chave] for m in ms])

    def ft(chave: str) -> list[float]:
        return _faixa([m["terceira"][chave] for m in ms])

    def fb(chave: str) -> list[float]:
        return _faixa(
            [c["figura"]["pct_origem"]["bn"][chave] for c in cenarios.values()]
        )

    return {
        "nao_muda": {
            "voltaram": f("voltaram"),
            "voltaram_lula_pct": f("voltaram_lula_pct"),
            "voltaram_flavio_pct": f("voltaram_flavio_pct"),
            "explica_pp": f("explica_pp"),
            "faltaram_no_2t": f("faltaram_no_2t"),
            "lula_de_terceira_bn_e_cruzamento": f("lula_de_terceira_bn_e_cruzamento"),
            "flavio_de_terceira_bn_e_cruzamento": f(
                "flavio_de_terceira_bn_e_cruzamento"
            ),
            "nota": "a linha de quem faltou no 1º turno é a mesma em todos (regressão); o que Lula recebeu da terceira "
            "via, do branco e nulo e do saldo da troca entre as bases soma quase o mesmo em todos, porque a urna "
            "fixa o total dele e a perda da base para branco, nulo e abstenção muda pouco",
        },
        "muda_pouco": {
            "terceira_flavio_pct": ft("flavio_pct"),
            "terceira_lula_pct": ft("lula_pct"),
            "terceira_bn_pct": ft("bn_pct"),
            "terceira_flavio_entre_finalistas": ft("flavio_entre_finalistas"),
            "bn1_lula_pct": fb("lula"),
            "bn1_flavio_pct": fb("flavio"),
            "cruzamento_liquido_para_lula": f("cruzamento_liquido_para_lula"),
            "nota": "com a mesma porcentagem nas duas direções, o que cruza de Lula para Flávio quase empata com o que "
            "cruza de Flávio para Lula (as bases têm tamanho parecido), e o saldo fica perto de zero",
        },
        "muda": {
            "fidelidade_lula": f("fidelidade_lula"),
            "fidelidade_flavio": f("fidelidade_flavio"),
            "ganho_fora_base_lula": f("ganho_fora_base_lula"),
            "ganho_fora_base_flavio": f("ganho_fora_base_flavio"),
            "razao_consolidacao": f("razao_consolidacao_flavio_lula"),
            "lula_para_flavio": f("lula_para_flavio"),
            "flavio_para_lula": f("flavio_para_lula"),
            "nota": "o cruzamento bruto entra no ganho fora da própria base dos dois ao mesmo tempo, então a razão de "
            "consolidação sobe com ele",
        },
    }


def equilibrio(
    alvo: float,
    margens: Mapping[str, Mapping[str, Any]],
    piso: Mapping[str, Any],
    b: Mapping[str, float],
    nac: Mapping[str, Any],
) -> dict[str, float] | None:
    """Cruzamento líquido de Flávio para Lula que leva a terceira via a `alvo`% para Flávio.

    Lula → Flávio fica em zero e Flávio → Lula sobe; a parte de Flávio na terceira
    via cresce com esse saldo, porque a urna fixa o total de cada um. Bissecção em
    [0; 15%] da base de Flávio no 1º turno. None se o alvo ficar fora do intervalo.
    """

    def parte(k: float) -> dict[str, Any]:
        cen = I.cenario(margens, piso, b, nome="", descricao="", cruzamento=(0.0, k))
        return I.metricas(cen["matriz"], nac)

    lo, hi = 0.0, 0.15
    if (
        not parte(lo)["terceira"]["flavio_pct"]
        <= alvo
        <= parte(hi)["terceira"]["flavio_pct"]
    ):
        return None
    for _ in range(36):
        mid = (lo + hi) / 2
        if parte(mid)["terceira"]["flavio_pct"] < alvo:
            lo = mid
        else:
            hi = mid
    k = (lo + hi) / 2
    m = parte(k)
    return {
        "alvo_pct": alvo,
        "flavio_para_lula_pct": 100 * k,
        "flavio_para_lula": m["flavio_para_lula"],
        "fidelidade_flavio": m["fidelidade_flavio"],
        "terceira_flavio_pct": m["terceira"]["flavio_pct"],
    }


def publicado_liquido(
    linhas: list[dict[str, Any]], nac: Mapping[str, Any]
) -> dict[str, Any]:
    """O saldo líquido que cada linha publicada implica, em votos, sobre as bases do 1º turno."""
    o = nac["origens"]
    out = []
    for x in linhas:
        lf = x["lula_para_flavio_pct"] / 100 * o["lula"]
        fl = x["flavio_para_lula_pct"] / 100 * o["flavio"]
        out.append(
            {
                "instituto": x["instituto"],
                "campo": x["campo"],
                "pagina": x["pagina"],
                "liquido_para_lula": fl - lf,
                "liquido_para_lula_pct_base_flavio": 100 * (fl - lf) / o["flavio"],
            }
        )
    return {
        "linhas": out,
        "faixa_votos": _faixa([x["liquido_para_lula"] for x in out]),
        "faixa_pct_base_flavio": _faixa(
            [x["liquido_para_lula_pct_base_flavio"] for x in out]
        ),
    }
