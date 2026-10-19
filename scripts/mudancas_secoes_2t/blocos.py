"""Blocos do payload sobre o 1º turno: comportamento, intercorrências e efeito medido."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from mudancas_secoes_2t import analises as an

ROTULO_EFEITO = (
    "Diferença medida com controles por município e por 2022, não efeito causal "
    "identificado: a escolha dos locais pelo TRE não é aleatória."
)
NOMES_GRUPO = {
    "mudanca_real": "todas as urnas com mudança real de prédio entre os turnos",
    "A": "categoria A: votaram em local temporário no 1º turno e voltam ao original",
    "novas": "novas realocações com mudança real (B, C, X, D e E)",
    "temp_1t": "urnas que votaram em local diferente do original no 1º turno",
}


def _tamanho(p: pd.DataFrame, mascara: pd.Series) -> dict[str, int]:
    g = p[mascara]
    return {
        "urnas": len(g),
        "aptos": int(g["aptos"].sum()),
        "comparecimento": int(g["comp"].sum()),
        "municipios": int(g[["uf", "mun"]].drop_duplicates().shape[0]),
    }


def mascaras(p: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "mudanca_real": p["mud"] != "0",
        "A": p["mud"] == "A",
        "novas": p["mud"] == "N",
        "temp_1t": p["t1"],
        "troca": (~p["t1"]) & (p["g22"] == "troca"),
        "est": (~p["t1"]) & (p["g22"] == "est"),
    }


def valores_pais(p: pd.DataFrame) -> dict[str, float]:
    s = p[an.COLUNAS].sum()
    return {
        "abstencao": round(float(s["abst_num"] / s["aptos"] * 100), 2),
        "flavio_validos": round(float(s["flavio"] / s["validos"] * 100), 2),
        "lula_validos": round(float(s["lula"] / s["validos"] * 100), 2),
        "brancos": round(float(s["brancos"] / s["comp"] * 100), 2),
        "nulos": round(float(s["nulos"] / s["comp"] * 100), 2),
        "urnas": len(p),
    }


def comportamento(res: dict[str, Any], p: pd.DataFrame) -> dict[str, Any]:
    m = mascaras(p)
    grupos: dict[str, dict[str, Any]] = {}
    for g in ("mudanca_real", "A", "novas"):
        grupos[g] = {
            "descricao": NOMES_GRUPO[g],
            **_tamanho(p, m[g]),
            "metricas": {
                nome: an.bloco(res, f"comp|{g}|{nome}") for nome in an.METRICAS_VOTO
            },
        }
    a = grupos["A"]["metricas"]["abstencao"]["mesmo_municipio"]["diferenca_pp"]
    return {
        "unidade": "urna (seção principal) com boletim, só Brasil",
        "regra": "Mesmo município: diferença entre o grupo e as demais urnas do município, "
        "município a município, ponderada pelos aptos do grupo. País: grupo contra as "
        "demais urnas do país (razão de somas). Abstenção sobre aptos; Flávio e Lula "
        "sobre válidos; brancos e nulos sobre comparecimento. IC 95% por bootstrap de "
        "prédios (as urnas de um mesmo local do 1º turno saem juntas), estratificado por "
        "município × célula no recorte municipal.",
        "grupos": grupos,
        "teste_abstencao_categoria_a": {
            "pergunta": "As urnas da categoria A, que votaram em local temporário no 1º "
            "turno, tiveram abstenção maior que as demais do mesmo município?",
            "diferenca_pp": a,
            "resposta": _resposta(a),
        },
        "pais_todas_as_urnas": valores_pais(p),
    }


def _br(x: float) -> str:
    return f"{x:+.2f}".replace(".", ",")


def _resposta(d: dict[str, Any]) -> str:
    if d["valor"] is None:
        return "sem dado"
    lo, hi = d["ic95"]
    faixa = f"{_br(d['valor'])} ponto, IC 95% de {_br(lo)} a {_br(hi)}"
    if lo > 0:
        return f"Sim: {faixa}."
    if hi < 0:
        return f"Não, foi menor: {faixa}."
    return f"Inconclusivo: {faixa}, inclui zero."


def intercorrencias(res: dict[str, Any], p: pd.DataFrame) -> dict[str, Any]:
    m = mascaras(p)
    nomes = {
        "bateria": "operação com bateria registrada no log (qualquer momento)",
        "bateria_votacao": "bateria entre o primeiro e o último voto",
        "reinicio": "aplicação reiniciada durante a votação",
        "abertura_atrasada": "primeiro voto às 8h30 de Brasília ou depois",
        "fila_fechamento": "último voto depois das 18h de Brasília (fila no fechamento, "
        "com a votação encerrada às 17h)",
        "atencao_2_ou_3": "nível de atenção 2 ou 3 no mapa de fiscais (sinais combinados ou "
        "conferir o arquivo)",
    }
    grupos = {}
    for g in ("mudanca_real", "A", "novas", "temp_1t"):
        grupos[g] = {
            "descricao": NOMES_GRUPO[g],
            **_tamanho(p, m[g]),
            "metricas": {
                k: an.bloco(res, f"interc|{g}|{k}", razao=True)
                for k in an.METRICAS_INTERC
            },
        }
    tot = p[an.COLUNAS].sum()
    return {
        "unidade": "urna (seção principal) com boletim, só Brasil",
        "definicoes": nomes,
        "denominadores": {
            "logs": "urnas com log processado (bateria, reinício, atenção)",
            "horarios": "urnas com hora do primeiro e do último voto convertida para Brasília",
        },
        "grupos": grupos,
        "pais_parcela_pct": {
            k: round(float(tot[met[1]] / tot[met[2]] * 100), 2)
            for k, met in an.METRICAS_INTERC.items()
        },
        "rotulo": "Parcela de urnas com o registro, contra as demais do país e do mesmo "
        "município; razão e diferença com IC. Registro operacional não é irregularidade.",
    }


def cobertura_2022(p: pd.DataFrame) -> dict[str, Any]:
    t = p[p["t1"]]
    casada = (t["aptos_2022_2t"] > 0) & t["comp_2022_2t"].notna()
    no_original = casada & (t["local_nr_2022"] == t["original_1t"])
    no_temp = casada & (t["local_nr_2022"] == t["local_1t"])
    resto = p[~p["t1"]]
    return {
        "regra": "Seção casada com a de 2022 pela chave (UF, município, zona, seção). "
        "Tratada (local temporário em 2026) entra quando em 2022 votou no número do "
        "local original; controle estável quando votou no mesmo número de 2026 e o nome "
        "do prédio tem ao menos um terço das palavras em comum com o de 2022. Fonte de "
        "2022: detalhe de votação por seção do TSE, 2º turno, a mesma que o Politize lê.",
        "temp_1t": {
            "urnas": len(t),
            "casadas_no_original_2022": int(no_original.sum()),
            "casadas_ja_no_temporario_em_2022": int(no_temp.sum()),
            "casadas_em_outro_local": int((casada & ~no_original & ~no_temp).sum()),
            "sem_secao_2022": int((~casada).sum()),
            "cobertura_pct": (
                round(float(no_original.mean() * 100), 1) if len(t) else None
            ),
        },
        "demais": {k: int(v) for k, v in resto["g22"].value_counts().items()},
        "rotulos_demais": {
            "est": "mesmo número e prédio compatível (controle)",
            "troca": "mesmo número, prédio sem palavra em comum no nome (grupo troca)",
            "amb": "mesmo número, nome parecido em parte (fora dos dois grupos)",
            "outro_nr": "votou em outro número de local em 2022",
            "nc": "sem seção correspondente no 2º turno de 2022",
        },
    }


def efeito(
    res: dict[str, Any],
    res_rj: dict[str, Any],
    p: pd.DataFrame,
    cadastro: dict[str, int],
) -> dict[str, Any]:
    m = mascaras(p)
    dose = []
    for b in range(an.SEM_FAIXA + 1):
        rot = an.FAIXAS_A[b][2] if b < an.SEM_FAIXA else "sem distância confiável"
        mask = (p["mud"] == "A") & (p["faixa"] == b)
        dose.append(
            {
                "faixa": rot,
                **_tamanho(p, mask),
                "urnas_casadas_2022": int((mask & p["dd"]).sum()),
                "abstencao": an.bloco(res, f"dose|{b}|abst"),
                "dif_em_dif": an.bloco(res, f"dose|{b}|dd"),
            }
        )
    dd = an.bloco(res, "dd|temp_1t_dd|dd")
    return {
        "rotulo": ROTULO_EFEITO,
        "tratamento": {
            "definicao": "local do 1º turno diferente do original no cadastro de 02/10",
            "secoes_cadastro": int(cadastro["secoes"]),
            "eleitores_cadastro": int(cadastro["eleitores"]),
            **_tamanho(p, m["temp_1t"]),
        },
        "abstencao": an.bloco(res, "efeito|temp_1t|abstencao"),
        "dif_em_dif": {
            "regra": "variação da abstenção da mesma seção, 1º turno de 2026 menos 2º turno "
            "de 2022, nas tratadas contra as estáveis do mesmo município (ponderada pelos "
            "aptos casados) e do país",
            "cobertura": cobertura_2022(p),
            "diferenca": dd,
            "abstencao_2026": an.bloco(res, "dd|temp_1t_dd|abst_2026"),
            "abstencao_2022": an.bloco(res, "dd|temp_1t_dd|abst_2022"),
        },
        "dose_resposta": {
            "regra": "só categoria A: a distância do local temporário (coordenada do 1º "
            "turno) ao original (coordenada do 2º) é conhecida",
            "faixas": dose,
        },
        "direcao": {
            k: an.bloco(res, f"efeito|temp_1t|{k}")
            for k in ("flavio_validos", "lula_validos")
        },
        "troca_desde_2022": troca(res, p),
        "rj": res_rj,
        "magnitude_para_cenarios": {
            "fonte": "efeito_1t.dif_em_dif.diferenca.mesmo_municipio.diferenca_pp",
            "valor": dd["mesmo_municipio"]["diferenca_pp"]["valor"],
            "ic95": dd["mesmo_municipio"]["diferenca_pp"]["ic95"],
        },
    }


def troca(res: dict[str, Any], p: pd.DataFrame) -> dict[str, Any]:
    m = mascaras(p)
    return {
        "definicao": "mesmo número de local em 2022 e em 2026, prédio com nome sem nenhuma "
        "palavra significativa em comum com o de 2022; é a forma como o TRE-RJ registrou "
        "as transferências da Maré (número mantido, prédio trocado), invisível na regra "
        "local diferente do original",
        **_tamanho(p, m["troca"]),
        "abstencao_contra_estaveis": an.bloco(res, "efeito_troca|troca|abstencao"),
        "dif_em_dif": an.bloco(res, "dd|troca|dd"),
        "abstencao_2026": an.bloco(res, "dd|troca|abst_2026"),
        "abstencao_2022": an.bloco(res, "dd|troca|abst_2022"),
        "direcao": {
            k: an.bloco(res, f"efeito_troca|troca|{k}")
            for k in ("flavio_validos", "lula_validos")
        },
        "limite": "Parte das trocas é só renomeação de escola (nome novo, mesmo prédio); "
        "o grupo mistura mudança de prédio com mudança de nome.",
    }


def _abst(g: pd.DataFrame, num: str = "abst_num", den: str = "aptos") -> float | None:
    d = g[den].sum()
    return round(float(g[num].sum() / d * 100), 2) if d else None


def rj(
    p: pd.DataFrame, grupos: dict[str, np.ndarray], reps: int, seed: int
) -> dict[str, Any]:
    """Município do Rio por zona: local temporário e troca de prédio desde 2022."""
    rio = p[(p["uf"] == "RJ") & (p["mun"] == "60011")].reset_index(drop=True)
    zonas = []
    for z in sorted(rio["zona"].unique()):
        g = rio[rio["zona"] == z]
        trans = g["t1"] | (g["g22"] == "troca")
        est = g[(~g["t1"]) & (g["g22"] == "est")]
        tr = g[trans]
        trm = g[g["dd"] | ((~g["t1"]) & (g["g22"] == "troca"))]
        dd_t = _dd(trm)
        dd_c = _dd(est)
        zonas.append(
            {
                "zona": int(z),
                "urnas": len(g),
                "aptos": int(g["aptos"].sum()),
                "abstencao_zona_1t": _abst(g),
                "urnas_temporario_1t": int(g["t1"].sum()),
                "urnas_troca_desde_2022": int(
                    ((~g["t1"]) & (g["g22"] == "troca")).sum()
                ),
                "abstencao_1t_transferidas": _abst(tr) if len(tr) else None,
                "abstencao_1t_estaveis": _abst(est) if len(est) else None,
                "abstencao_2022_transferidas": (
                    _abst(trm, "abst22", "aptos22") if len(trm) else None
                ),
                "abstencao_2022_estaveis": (
                    _abst(est, "abst22", "aptos22") if len(est) else None
                ),
                "variacao_transferidas_pp": dd_t,
                "variacao_estaveis_pp": dd_c,
                "dif_em_dif_pp": (
                    None if dd_t is None or dd_c is None else round(dd_t - dd_c, 2)
                ),
            }
        )
    pred = an.por_predio(rio, ["uf", "mun", "zona"])
    p_rio = an.montar_passada(pred, pred["zona"], reps, seed)
    tarefas = [
        an.Tarefa(
            "rio|abst", "transferida", None, an.METRICAS_VOTO["abstencao"], "aptos"
        ),
        an.Tarefa("rio|dd", "transferida", "est", an.DD, "aptos_m"),
    ]
    r = an.rodar(p_rio, grupos, tarefas)
    z161 = next((z for z in zonas if z["zona"] == 161), None)
    est = p[p["uf"] == "RJ"]
    tr_est = est[(~est["t1"]) & (est["g22"] == "troca")]
    return {
        "estado_rj": {
            "urnas_troca_desde_2022": len(tr_est),
            "locais_troca_desde_2022": int(
                tr_est[["mun", "zona", "local_1t"]].drop_duplicates().shape[0]
            ),
            "municipios_troca_desde_2022": int(tr_est["mun"].nunique()),
            "aptos_troca_desde_2022": int(tr_est["aptos"].sum()),
            "urnas_temporario_1t": int(est["t1"].sum()),
            "referencia_imprensa": "72 locais alterados no estado, 20 municípios, cerca de "
            "200 mil eleitores (Redes da Maré, citada pela Agência Pública em 16/10)",
            "nota": "O grupo troca desde 2022 é mais largo que as transferências por "
            "segurança: inclui toda troca de prédio com número mantido desde 2022.",
        },
        "municipio": "Rio de Janeiro (CD_MUNICIPIO 60011)",
        "transferida": "local temporário no 1º turno ou troca de prédio desde 2022 com o "
        "mesmo número",
        "abstencao_mesma_zona": an.formatar(r["rio|abst"]),
        "dif_em_dif_mesma_zona": an.formatar(r["rio|dd"]),
        "por_zona": sorted(
            zonas, key=lambda z: -z["urnas_troca_desde_2022"] - z["urnas_temporario_1t"]
        ),
        "zona_161": z161,
        "conferencia_imprensa": {
            "conjur_zona_161_abstencao_pct": 28.46,
            "nossa_zona_161_abstencao_pct": z161["abstencao_zona_1t"] if z161 else None,
            "conjur_media_nacional_pct": 21.08,
        },
        "premissa_que_caiu": "No cadastro de 02/10, as transferências do TRE-RJ não aparecem "
        "como local diferente do original: o número do local foi mantido e o nome e o "
        "endereço foram trocados. Por isso a regra local diferente do original "
        + (
            "não marca nenhuma urna no município do Rio"
            if int(rio["t1"].sum()) == 0
            else f"marca só {int(rio['t1'].sum())} urnas no município do Rio"
        )
        + "; o grupo troca desde 2022 é a forma de enxergá-las.",
    }


def _dd(g: pd.DataFrame) -> float | None:
    if not len(g) or g["aptos_m"].sum() <= 0 or g["aptos22"].sum() <= 0:
        return None
    a = g["abst_m"].sum() / g["aptos_m"].sum()
    b = g["abst22"].sum() / g["aptos22"].sum()
    return round(float((a - b) * 100), 2)
