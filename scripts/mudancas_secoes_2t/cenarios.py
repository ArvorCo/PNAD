"""Cenários de abstenção extra nas seções que mudam de prédio.

Regra: ``x`` pontos de abstenção extra sobre os aptos da urna tiram ``x/100 × aptos``
comparecimentos, repartidos na composição do 1º turno da própria urna (Flávio, Lula,
demais candidaturas, brancos e nulos). Cenário de ganho é o mesmo com sinal trocado.
O saldo é a variação da diferença Flávio menos Lula, em votos e em pontos do total
nacional de válidos do 1º turno (soma de ``voto_secao``, cargo 1, tipo 1).

Magnitudes: fixas (+2, +5, +10, +20), a ordem de grandeza de Brady e McNulty (2011,
cerca de 1,9 ponto) e a estimativa brasileira medida no próprio 1º turno
(``efeito_1t``), com o IC dela como faixa.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

MAGNITUDES_FIXAS = (2.0, 5.0, 10.0, 20.0)
REGRA = (
    "x pontos de abstenção extra sobre os aptos da urna tiram x/100 dos aptos do "
    "comparecimento, repartidos na composição do 1º turno da própria urna (Flávio, "
    "Lula, demais candidaturas, brancos e nulos); o cenário de ganho troca o sinal. "
    "O saldo é a variação da diferença Flávio menos Lula, em votos e em pontos do "
    "total nacional de válidos do 1º turno. Não é previsão: é a conta do tamanho."
)
BRADY_MCNULTY_PP = 1.9
COMPONENTES = ("flavio", "lula", "terceira", "brancos", "nulos")


def votos_perdidos(urnas: pd.DataFrame, pp: float) -> dict[str, Any]:
    """Comparecimentos perdidos (ou ganhos, com ``pp`` negativo) por componente."""
    u = urnas[(urnas["comparecimento"] > 0) & (urnas["aptos"] > 0)]
    aptos = u["aptos"].to_numpy(float)
    comp = u["comparecimento"].to_numpy(float)
    x = pp / 100.0 * aptos
    perda = np.minimum(x, comp) if pp >= 0 else -np.minimum(-x, aptos - comp)
    parte = {c: float((perda * u[c].to_numpy(float) / comp).sum()) for c in COMPONENTES}
    total = float(perda.sum())
    return {"total": total, **parte, "urnas": len(u), "aptos": int(aptos.sum())}


def cenario(
    urnas: pd.DataFrame, pp: float, validos_nacionais: float, rotulo: str
) -> dict:
    v = votos_perdidos(urnas, pp)
    saldo = -(v["flavio"] - v["lula"])
    return {
        "rotulo": rotulo,
        "abstencao_extra_pp": round(pp, 3),
        "urnas": v["urnas"],
        "aptos": v["aptos"],
        "comparecimento_perdido": round(v["total"]),
        "perdidos": {c: round(v[c]) for c in COMPONENTES},
        "variacao_diferenca_flavio_menos_lula_votos": round(saldo),
        "variacao_diferenca_pp_validos_nacionais": round(
            saldo / validos_nacionais * 100, 4
        ),
        "_exato": v,
    }


def montar(
    urnas: pd.DataFrame,
    validos_nacionais: float,
    efeito: dict[str, Any] | None,
    efeito_rio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Todos os cenários; ``urnas`` traz as marcas mudanca_real, categoria e temp_2t."""
    mr = urnas[urnas["mudanca_real"]]
    grupo_a = mr[mr["categoria"] == "A"]
    novas = mr[mr["categoria"] != "A"]
    fora_2t = urnas[urnas["temp_2t"]]
    novas_fora = urnas[urnas["temp_2t"] & ~urnas["temp_1t"]]
    fixos = []
    for pp in MAGNITUDES_FIXAS:
        fixos.append(
            {
                "abstencao_extra_pp": pp,
                "mudanca_real": cenario(
                    mr, pp, validos_nacionais, "todas com mudança real"
                ),
                "categoria_a": cenario(grupo_a, pp, validos_nacionais, "categoria A"),
                "novas_realocacoes": cenario(
                    novas, pp, validos_nacionais, "B, C, X, D e E"
                ),
            }
        )
    brady = {
        "fonte": "Brady, H. E. e McNulty, J. E. (2011). Turning Out to Vote: The Costs of "
        "Finding and Getting to the Polling Place. American Political Science Review "
        "105(1). Mudança de local reduz o comparecimento em cerca de 1,9 ponto; ordem "
        "de grandeza, medida em Los Angeles em 2003.",
        "novas_realocacoes": cenario(
            novas, BRADY_MCNULTY_PP, validos_nacionais, "B, C, X, D e E"
        ),
        "categoria_a_ganho": cenario(
            grupo_a, -BRADY_MCNULTY_PP, validos_nacionais, "categoria A recupera"
        ),
    }
    brasil: dict[str, Any] = {"situacao": "sem estimativa"}
    if efeito and efeito.get("valor") is not None:
        central = float(efeito["valor"])
        lo, hi = efeito["ic95"]
        brasil = {
            "fonte": efeito["fonte"],
            "magnitude_pp": {"central": central, "ic95": [lo, hi]},
        }
        for nome, base, sinal, rot in (
            ("seguem_fora_do_original_2t", fora_2t, 1, "fora do original em 25/10"),
            (
                "novas_fora_do_original_2t",
                novas_fora,
                1,
                "fora do original só no 2º turno",
            ),
            ("novas_realocacoes", novas, 1, "B, C, X, D e E"),
            ("categoria_a_ganho", grupo_a, -1, "categoria A recupera"),
        ):
            brasil[nome] = {
                "central": cenario(base, sinal * central, validos_nacionais, rot),
                "ic_baixo": cenario(base, sinal * lo, validos_nacionais, rot),
                "ic_alto": cenario(base, sinal * hi, validos_nacionais, rot),
            }
        liquido = {}
        for k in ("central", "ic_baixo", "ic_alto"):
            soma = (
                brasil["novas_realocacoes"][k][
                    "variacao_diferenca_flavio_menos_lula_votos"
                ]
                + brasil["categoria_a_ganho"][k][
                    "variacao_diferenca_flavio_menos_lula_votos"
                ]
            )
            liquido[k] = {
                "variacao_diferenca_flavio_menos_lula_votos": soma,
                "variacao_diferenca_pp_validos_nacionais": round(
                    soma / validos_nacionais * 100, 4
                ),
            }
        brasil["saldo_1t_para_2t"] = {
            "descricao": "novas realocações perdem e a categoria A recupera, com a mesma "
            "magnitude",
            **liquido,
        }
    rio: dict[str, Any] = {"situacao": "sem estimativa"}
    if efeito_rio and efeito_rio.get("valor") is not None:
        mag = float(efeito_rio["valor"])
        rio = {
            "fonte": efeito_rio["fonte"],
            "magnitude_pp": {"central": mag, "ic95": efeito_rio["ic95"]},
            "uso": "teto de sensibilidade: a diferença medida no município do Rio, onde as "
            "trocas de prédio incluem as transferências por segurança do TRE-RJ, aplicada "
            "ao país",
            "seguem_fora_do_original_2t": cenario(
                fora_2t, mag, validos_nacionais, "fora do original em 25/10"
            ),
            "novas_realocacoes": cenario(
                novas, mag, validos_nacionais, "B, C, X, D e E"
            ),
            "categoria_a_ganho": cenario(
                grupo_a, -mag, validos_nacionais, "categoria A recupera"
            ),
        }
    return {
        "regra": REGRA,
        "validos_nacionais_1t": int(validos_nacionais),
        "composicao_1t": composicao(mr, grupo_a, novas, fora_2t),
        "fixos": fixos,
        "brady_mcnulty": brady,
        "estimativa_brasileira": brasil,
        "estimativa_rio": rio,
    }


def composicao(*grupos: pd.DataFrame) -> dict[str, Any]:
    nomes = ("mudanca_real", "categoria_a", "novas_realocacoes", "fora_do_original_2t")
    out = {}
    for nome, g in zip(nomes, grupos, strict=True):
        val = g["validos"].sum()
        out[nome] = {
            "urnas": len(g),
            "aptos": int(g["aptos"].sum()),
            "comparecimento": int(g["comparecimento"].sum()),
            "flavio_validos_pct": (
                round(g["flavio"].sum() / val * 100, 2) if val else None
            ),
            "lula_validos_pct": round(g["lula"].sum() / val * 100, 2) if val else None,
            "abstencao_pct": (
                round((1 - g["comparecimento"].sum() / g["aptos"].sum()) * 100, 2)
                if g["aptos"].sum()
                else None
            ),
        }
    return out


def tirar_exatos(obj: Any) -> Any:
    """Remove os campos ``_exato`` (usados só nos testes de fechamento)."""
    if isinstance(obj, dict):
        return {k: tirar_exatos(v) for k, v in obj.items() if k != "_exato"}
    if isinstance(obj, list):
        return [tirar_exatos(v) for v in obj]
    return obj
