"""Cenário do tweet do autor refeito no motor Python da casa com a urna observada.

Usa ``scripts/reponderacao-simulador.py`` (espelho do motor publicado) sobre o
snapshot da Central Média de 24/10 que o tweet usou e fixa o que a urna mediu:
comparecimento e brancos + nulos. Restam duas incógnitas não identificáveis
juntas (presença relativa de Flávio e destino dos indecisos); resolve cada uma
com a outra fixa. Presença por candidato não é medida: o número que sai é o
ajuste que a aritmética exige, não uma observação.
"""

from __future__ import annotations

import importlib
import json
from collections.abc import Callable
from typing import Any

from .pesquisas_urna import ROOT, fonte

SIM = importlib.import_module("reponderacao-simulador")
SNAPSHOT = "9399acb33c51065d"
CAMINHO = ROOT / f"docs/assets/reponderacao_cenarios/{SNAPSHOT}.json"
TWEET = {
    "centro": "media",
    "presenca_relativa": -12.5,
    "comparecimento": 81.5,
    "indecisos_validos": 100,
    "indecisos_flavio": 34.8,
}


def _bissecao(f: Callable[[float], float], alvo: float, lo: float, hi: float):
    flo, fhi = f(lo) - alvo, f(hi) - alvo
    if flo * fhi > 0:
        return None
    for _ in range(80):
        meio = (lo + hi) / 2
        fm = f(meio) - alvo
        if (fm < 0) == (flo < 0):
            lo, flo = meio, fm
        else:
            hi = meio
    return (lo + hi) / 2


def _placar(r: dict[str, Any], aptos: int) -> dict[str, Any]:
    validos = aptos * r["validos"] / 100
    return {
        "flavio_validos_pct": r["flavio"],
        "lula_validos_pct": r["lula"],
        "diferenca_f_menos_l_pp": r["flavio"] - r["lula"],
        "flavio_votos": validos * r["flavio"] / 100,
        "lula_votos": validos * r["lula"] / 100,
        "validos_votos": validos,
        "branco_nulo_votos": aptos * r["branco_nulo"] / 100,
        "branco_nulo_pct_comparecimento": 100 * r["branco_nulo"] / r["comparecimento"],
        "comparecimento_pct": r["comparecimento"],
        "taxas_presenca": r["taxas"],
    }


def refazer(urna: dict[str, Any]) -> dict[str, Any]:
    data = json.loads(CAMINHO.read_text(encoding="utf-8"))
    b = urna["brasil"]
    aptos, comp = b["eleitores"], b["comparecimento"]
    bn = (b.get("brancos") or 0) + (b.get("nulos") or 0)
    if not bn:
        bn = comp - b["validos_votos"]
    # Base apurada (comparecimento + abstenção), como a abstenção oficial publicada.
    comp_pct = 100 * comp / (comp + b["abstencao"])
    bn_por_100 = 100 * bn / aptos
    alvo_f = b["validos"]["flavio"]
    base = {"centro": "media", "comparecimento": comp_pct, "indecisos_validos": 100}

    def avaliar(presenca: float, split: float | None) -> dict[str, Any]:
        p = {**base, "presenca_relativa": presenca, "indecisos_flavio": split}

        def bn_de(x: float) -> float:
            return SIM.evaluate(data, {**p, "branco_nulo_pp": x})["branco_nulo"]

        x = _bissecao(bn_de, bn_por_100, -10, 20)
        if x is None:
            raise ValueError("brancos e nulos fora do alcance do motor")
        r = SIM.evaluate(data, {**p, "branco_nulo_pp": x})
        r["branco_nulo_pp_ajuste"] = x
        return r

    def cenario(nome: str, regra: str, presenca: float, split: float | None):
        r = avaliar(presenca, split)
        pl = _placar(r, aptos)
        return {
            "nome": nome,
            "regra": regra,
            "parametros": {
                **base,
                "presenca_relativa": presenca,
                "indecisos_flavio": split,
                "indecisos_flavio_efetivo": (
                    split
                    if split is not None
                    else SIM.allocation_parameters(
                        data,
                        SIM.parameters(
                            data,
                            {
                                **base,
                                "presenca_relativa": presenca,
                                "branco_nulo_pp": 0,
                            },
                        ),
                    )["indecisos_flavio"]
                ),
                "branco_nulo_pp": r["branco_nulo_pp_ajuste"],
            },
            "placar": pl,
            "contra_a_urna": {
                "flavio_validos_pp": pl["flavio_validos_pct"] - alvo_f,
                "diferenca_f_menos_l_pp": pl["diferenca_f_menos_l_pp"]
                - (alvo_f - b["validos"]["lula"]),
                "flavio_votos": pl["flavio_votos"] - b["votos"]["flavio"],
                "lula_votos": pl["lula_votos"] - b["votos"]["lula"],
            },
        }

    def f_com_presenca(x: float) -> float:
        return avaliar(x, None)["flavio"]

    def f_com_split(x: float) -> float:
        return avaliar(3.8, x)["flavio"]

    pres_a = _bissecao(f_com_presenca, alvo_f, -30, 30)
    split_b = _bissecao(f_com_split, alvo_f, 0, 100)
    tweet = SIM.evaluate(data, TWEET)
    empate = SIM.evaluate(data, {**TWEET, "presenca_relativa": -6.4})
    central = SIM.evaluate(data, {})
    cenarios = [
        cenario(
            "c_combinacao_do_autor_com_bn_reais",
            "presença −12,5% e indecisos 34,8/65,2, com comparecimento e brancos e nulos "
            "da urna",
            -12.5,
            34.8,
        ),
        cenario(
            "central_com_bn_reais",
            "central (+3,8%, divisão automática) só com comparecimento e BN da urna",
            3.8,
            None,
        ),
    ]
    if pres_a is not None:
        cenarios.insert(
            0,
            cenario(
                "a_presenca_necessaria",
                "presença relativa resolvida para bater Flávio da urna; indecisos na "
                "proporção automática da central",
                pres_a,
                None,
            ),
        )
    if split_b is not None:
        cenarios.insert(
            1,
            cenario(
                "b_indecisos_necessarios",
                "divisão dos indecisos resolvida para bater a urna; presença +3,8% da "
                "central",
                3.8,
                split_b,
            ),
        )
    limite_b = None
    if split_b is None:
        limite_b = cenario(
            "b_limite_todos_indecisos_para_lula",
            "sem solução entre 0 e 100%: mesmo com 100% dos indecisos para Lula e "
            "presença +3,8% da central, Flávio fica acima da urna",
            3.8,
            0.0,
        )
        cenarios.insert(1, limite_b)
    return {
        "descricao": (
            "Hipótese do autor (tweet de 25/10, 21h41) refeita no motor Python da casa "
            "com comparecimento e brancos e nulos observados. Presença por candidato não "
            "é medida; os valores resolvidos são o ajuste que a aritmética exige."
        ),
        "gerado_por": "scripts/apuracao-2t-2026-pesquisas.py",
        "motor": "scripts/reponderacao-simulador.py (evaluate)",
        "snapshot": {"versao": SNAPSHOT, **fonte(CAMINHO)},
        "escolha_do_snapshot": (
            "último snapshot com referência 2026-10-24; o único da data que reproduz o "
            "tweet (Flávio 48,3% e brancos e nulos de 3,1% do comparecimento)"
        ),
        "urna": {
            "fonte": urna["fonte"],
            "aptos": aptos,
            "comparecimento": comp,
            "abstencao_pct": 100 - comp_pct,
            "brancos_mais_nulos": bn,
            "branco_nulo_pct_comparecimento": 100 * bn / comp,
            "flavio_validos_pct": alvo_f,
            "votos": b["votos"],
            "nota_universo": (
                "taxas da urna nacional com exterior aplicadas ao motor, cujo universo é "
                "Brasil sem exterior; votos do cenário escalados aos aptos da urna"
            ),
        },
        "reproducao_tweet": {
            "parametros": TWEET,
            "flavio_validos_pct": tweet["flavio"],
            "branco_nulo_pct_comparecimento": 100
            * tweet["branco_nulo"]
            / tweet["comparecimento"],
            "taxas_presenca": tweet["taxas"],
            "empate_presenca_menos_6_4_flavio_pct": empate["flavio"],
        },
        "central_do_snapshot": {"flavio": central["flavio"], "lula": central["lula"]},
        "presenca_necessaria_a": pres_a,
        "indecisos_flavio_necessario_b": split_b,
        "cenarios": cenarios,
    }
