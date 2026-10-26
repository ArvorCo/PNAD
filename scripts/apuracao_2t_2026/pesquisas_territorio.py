"""Estaduais, projeção territorial da casa e contabilidade agregada por UF.

Tudo aqui é comparação de agregados por UF contra a urna. A urna por UF é a
soma dos arquivos de UF (Brasil sem exterior), o mesmo universo das projeções.
A contabilidade de votos entre turnos é identidade aritmética, não migração
individual: ninguém sabe, por esses números, quem trocou de voto.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections.abc import Mapping
from typing import Any

from apuracao_2026 import pesquisas as P

from .pesquisas_urna import REGIAO_DE, REGIOES


def parcela_flavio(urna_uf: Mapping[str, Any]) -> float:
    v = urna_uf["votos"]
    return 100 * v["flavio"] / (v["flavio"] + v["lula"])


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or statistics.pstdev(xs) == 0 or statistics.pstdev(ys) == 0:
        return None
    return statistics.correlation(xs, ys)


def avaliar_metodo(
    nome: str, rotulo: str, pred: dict[str, tuple[float, float]], urna: dict[str, Any]
) -> dict[str, Any]:
    """Erro por UF de uma projeção dada em votos (Flávio, Lula) por UF.

    O erro por UF é na parcela de Flávio entre os dois (pp); na diferença F−L é
    o dobro. RMSE ponderado pelos votos em Flávio e Lula na urna, como na
    retrospectiva 2018→2022 da casa.
    """
    linhas = []
    for uf in sorted(pred):
        f, lu = pred[uf]
        p = 100 * f / (f + lu)
        u = parcela_flavio(urna["ufs"][uf])
        peso = sum(urna["ufs"][uf]["votos"].values())
        linhas.append(
            {
                "uf": uf,
                "regiao": REGIAO_DE[uf],
                "flavio_previsto": p,
                "flavio_urna": u,
                "erro_flavio_pp": p - u,
                "erro_f_menos_l_pp": 2 * (p - u),
                "vencedor_previsto": "flavio" if p > 50 else "lula",
                "vencedor_urna": "flavio" if u > 50 else "lula",
                "acertou_vencedor": (p > 50) == (u > 50),
                "peso": peso,
            }
        )
    pesos = [r["peso"] for r in linhas]
    erros = [r["erro_flavio_pp"] for r in linhas]
    tot = sum(pesos)
    vies = sum(e * w for e, w in zip(erros, pesos, strict=True)) / tot
    rmse = math.sqrt(sum(e * e * w for e, w in zip(erros, pesos, strict=True)) / tot)
    sf = sum(pred[uf][0] for uf in pred)
    sl = sum(pred[uf][1] for uf in pred)
    nac = 100 * sf / (sf + sl)
    u_nac = (
        100
        * sum(urna["ufs"][uf]["votos"]["flavio"] for uf in pred)
        / sum(sum(urna["ufs"][uf]["votos"].values()) for uf in pred)
    )
    regioes = {}
    for r, ufs in REGIOES.items():
        sel = [uf for uf in ufs if uf in pred]
        if not sel:
            continue
        pf = sum(pred[uf][0] for uf in sel)
        pl = sum(pred[uf][1] for uf in sel)
        uf_ = sum(urna["ufs"][uf]["votos"]["flavio"] for uf in sel)
        ul = sum(urna["ufs"][uf]["votos"]["lula"] for uf in sel)
        regioes[r] = {
            "flavio_previsto": 100 * pf / (pf + pl),
            "flavio_urna": 100 * uf_ / (uf_ + ul),
            "erro_flavio_pp": 100 * pf / (pf + pl) - 100 * uf_ / (uf_ + ul),
        }
    return {
        "metodo": nome,
        "rotulo": rotulo,
        "n_ufs": len(linhas),
        "acertou_vencedor": sum(r["acertou_vencedor"] for r in linhas),
        "errou_vencedor_ufs": [r["uf"] for r in linhas if not r["acertou_vencedor"]],
        "rmse_flavio_pp_ponderado": rmse,
        "rmse_flavio_pp_simples": math.sqrt(statistics.fmean(e * e for e in erros)),
        "mae_flavio_pp": statistics.fmean(abs(e) for e in erros),
        "vies_flavio_pp_ponderado": vies,
        "rmse_sem_vies_pp": math.sqrt(max(rmse**2 - vies**2, 0.0)),
        "correlacao_previsto_urna": _pearson(
            [r["flavio_previsto"] for r in linhas], [r["flavio_urna"] for r in linhas]
        ),
        "nacional_flavio_previsto": nac,
        "nacional_flavio_urna": u_nac,
        "nacional_erro_f_menos_l_pp": 2 * (nac - u_nac),
        "regioes": regioes,
        "ufs": linhas,
    }


def metodos_mapa(mapa: dict[str, Any], sufixo: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for chave, rotulo in (
        ("media", "Média Arvor por UF"),
        ("projecao", "Projeção Arvor por UF"),
        ("transportado", "Transporte proporcional do 1º turno, sem pesquisa"),
    ):
        out[f"{chave}_{sufixo}"] = {
            "rotulo": f"{rotulo} (mapa de {mapa['referencia']})",
            "votos": {
                u["uf"]: (u[chave]["flavio_votos"], u[chave]["lula_votos"])
                for u in mapa["ufs"]
            },
        }
    return out


ROTULOS_CSV = {
    "metade": "Terceira via dividida 50/50",
    "proporcional": "Terceira via proporcional à seção (método selecionado)",
    "deslocamento_uf": "Deslocamento uniforme por UF",
    "deslocamento_secao": "Deslocamento uniforme por seção",
    "matriz_uf": "Matriz ecológica de 2022 por UF",
    "matriz_contexto": "Matriz ecológica de 2022 por contexto",
    "combinado": "Combinação experimental com âncora PNAD",
}


def metodos_csv(caminho) -> dict[str, dict]:
    with caminho.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    out = {}
    for m, rotulo in ROTULOS_CSV.items():
        out[f"secoes_{m}"] = {
            "rotulo": f"{rotulo} (projeção territorial de 19/10)",
            "votos": {
                r["uf"]: (float(r[f"{m}_direita"]), float(r[f"{m}_esquerda"]))
                for r in linhas
            },
        }
    return out


def estaduais(
    pesquisas: list[dict[str, Any]], urna: dict[str, Any], mapa: dict[str, Any]
) -> dict[str, Any]:
    transp = {u["uf"]: u["transportado"] for u in mapa["ufs"]}
    linhas = []
    for p in pesquisas:
        v, _ = P.validos({k: float(x) for k, x in p["publicado"].items()})
        uf = p["uf"]
        u = urna["ufs"][uf]["validos"]
        uu = parcela_flavio(urna["ufs"][uf])
        e = (v["flavio"] - v["lula"]) - (2 * uu - 100)
        t = transp.get(uf)
        linhas.append(
            {
                "id": p["id"],
                "instituto": p["instituto"],
                "uf": uf,
                "campo": p["campo"],
                "n": p.get("n"),
                "publicado": p["publicado"],
                "validos": v,
                "urna_validos": u,
                "urna_flavio_entre_os_dois": uu,
                "erro_f_menos_l_pp": e,
                "acertou_vencedor": (v["flavio"] > v["lula"]) == (uu > 50),
                "transporte_flavio": t["flavio_pct"] if t else None,
                "erro_transporte_f_menos_l_pp": (
                    2 * (t["flavio_pct"] - uu) if t else None
                ),
            }
        )
    es = [r["erro_f_menos_l_pp"] for r in linhas]
    return {
        "regra": (
            "estaduais do 2º turno pós-urna; erro F−L nos válidos contra a urna da UF; "
            "campo de 06 a 13/10, duas semanas antes da urna"
        ),
        "pesquisas": linhas,
        "resumo": P.resumo_erros(es) if es else None,
        "acertaram_vencedor": sum(r["acertou_vencedor"] for r in linhas),
    }


def contabilidade(
    urna: dict[str, Any], um: dict[str, Any], transportado: dict[str, Any]
) -> dict[str, Any]:
    """Identidade de votos entre turnos e relação com a variação de comparecimento.

    ``disponivel`` = terceira via do 1º turno + queda de branco/nulo + aumento
    de comparecimento. Fecha com ganho de Flávio + ganho de Lula; é conta de
    agregados, não fluxo de pessoas.
    """

    def bloco(u2: dict[str, Any], u1: dict[str, Any]) -> dict[str, Any] | None:
        if u2["comparecimento"] is None:
            return None
        bn2 = u2["comparecimento"] - u2["validos_votos"]
        df = u2["votos"]["flavio"] - u1["flavio"]
        dl = u2["votos"]["lula"] - u1["lula"]
        dcomp = u2["comparecimento"] - u1["comparecimento"]
        disp = u1["terceiros"] + (u1["branco_nulo"] - bn2) + dcomp
        return {
            "ganho_flavio": df,
            "ganho_lula": dl,
            "terceiros_1t": u1["terceiros"],
            "branco_nulo_1t": u1["branco_nulo"],
            "branco_nulo_2t": bn2,
            "variacao_comparecimento": dcomp,
            "disponivel": disp,
            "parcela_flavio_do_ganho_pct": (
                100 * df / (df + dl) if df >= 0 and dl >= 0 and df + dl else None
            ),
            "residuo_identidade": disp - df - dl,
            "teto_parcela_flavio_da_terceira_via_pct": (
                100 * df / u1["terceiros"] if u1["terceiros"] else None
            ),
            "abstencao_1t_pct": u1["abstencao_pct"],
            "abstencao_2t_pct": u2["abstencao_pct"],
            "variacao_abstencao_pp": (
                u2["abstencao_pct"] - u1["abstencao_pct"]
                if u2["abstencao_pct"] is not None
                else None
            ),
        }

    br = bloco(urna["brasil"], um["brasil"])
    limite = None
    if br and br["variacao_comparecimento"] > 0:
        f2 = urna["brasil"]["votos"]["flavio"]
        l2 = urna["brasil"]["votos"]["lula"] - br["variacao_comparecimento"]
        limite = {
            "regra": (
                "limite extremo: todo o aumento líquido de comparecimento atribuído a Lula "
                "e retirado; não é estimativa, é o máximo que a variação poderia explicar"
            ),
            "flavio_validos_sem_o_aumento": 100 * f2 / (f2 + l2),
            "f_menos_l_sem_o_aumento": 100 * (f2 - l2) / (f2 + l2),
            "f_menos_l_urna": urna["brasil"]["validos"]["flavio"]
            - urna["brasil"]["validos"]["lula"],
        }
        limite["parcela_maxima_explicada_pp"] = (
            limite["f_menos_l_sem_o_aumento"] - limite["f_menos_l_urna"]
        )
    ufs = []
    for uf, u1 in um["ufs"].items():
        if uf == "ZZ" or uf not in urna["ufs"]:
            continue
        b = bloco(urna["ufs"][uf], u1)
        if b is None:
            continue
        t = transportado.get(uf)
        u_par = parcela_flavio(urna["ufs"][uf])
        ufs.append(
            {
                "uf": uf,
                "regiao": REGIAO_DE[uf],
                **b,
                "lula_1t_validos_pct": u1["lula_validos_pct"],
                "terceiros_1t_validos_pct": 100 * u1["terceiros"] / u1["validos"],
                "flavio_urna_entre_os_dois": u_par,
                "residuo_transporte_flavio_pp": (
                    u_par - t["flavio_pct"] if t else None
                ),
            }
        )
    com = [r for r in ufs if r["variacao_abstencao_pp"] is not None]
    xs = [r["variacao_abstencao_pp"] for r in com]
    res = [r["residuo_transporte_flavio_pp"] for r in com]
    lula1 = [r["lula_1t_validos_pct"] for r in com]
    terc = [r["terceiros_1t_validos_pct"] for r in com]
    perto = [abs(50 - r["flavio_urna_entre_os_dois"]) for r in com]
    return {
        "regra": (
            "identidade de agregados entre turnos; resíduo do transporte = Flávio na urna "
            "menos Flávio no transporte proporcional do 1º turno, entre os dois, por UF"
        ),
        "brasil": br,
        "limite_comparecimento": limite,
        "ufs": sorted(ufs, key=lambda r: r["uf"]),
        "correlacao_variacao_abstencao_com_residuo": _pearson(xs, res),
        "correlacao_lula_1t_com_residuo": _pearson(lula1, res),
        "correlacao_terceiros_1t_com_residuo": _pearson(terc, res),
        "correlacao_distancia_de_50_com_residuo": _pearson(perto, res),
        "residuo_medio_simples_pp": statistics.fmean(res) if res else None,
        "ufs_com_residuo_negativo": sum(r < 0 for r in res),
        "nota": (
            "correlação entre 27 UFs; agregado ecológico, não diz quem votou. "
            "Resíduo negativo: Flávio rendeu menos que a repetição local do 1º turno"
        ),
    }
