#!/usr/bin/env python3
"""Transferência de voto 1º → 2º turno (presidente, 2026): dados, regressão e matriz.

Grava ``analysis/apuracao_2t_2026/dados/transferencia.json`` e o memorando
``transferencia.md`` ao lado. Três peças, na ordem do método fixo da casa:

1. margens observadas das duas urnas por UF, município e (se os bancos locais
   existirem) seção da amostra sorteada antes da votação;
2. regressão ecológica da variação entre turnos, com efeito fixo de UF e pesos
   pelo eleitorado, e as trocas de especificação pedidas;
3. matriz de hipótese por IPF, UF a UF, com a linha de quem faltou no 1º turno
   fixada pela regressão e as demais ajustadas a partir das linhas publicadas
   pelos institutos; sensibilidades de fidelidade, regressão, terceira via,
   rotatividade e branco/nulo.

Sem os bancos locais de seções, reaproveita o bloco de seções do JSON anterior
(marcado ``"origem": "cache"``). Uso: ``python3 scripts/apuracao-2t-2026-transferencia.py``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import numpy as np
from apuracao_2t_2026 import transferencia_dados as D
from apuracao_2t_2026 import transferencia_ipf as I
from apuracao_2t_2026 import transferencia_priors as P
from apuracao_2t_2026 import transferencia_regressao as R

SAIDA = D.DADOS_2T / "transferencia.json"
MEMO = D.DADOS_2T / "transferencia.md"
TRAVESSAO = chr(0x2014)
ROTULO = (
    "estimativa ecológica e matriz de hipótese: descreve agregados, não identifica o "
    "voto de nenhum eleitor; pede explicação, não prova"
)


def _r(x: float, casas: int = 4) -> float:
    return round(float(x), casas)


def _arredonda(o: Any, casas: int = 6) -> Any:
    if isinstance(o, float):
        return round(o, casas)
    if isinstance(o, dict):
        return {k: _arredonda(v, casas) for k, v in o.items()}
    if isinstance(o, list):
        return [_arredonda(v, casas) for v in o]
    if isinstance(o, np.floating):
        return round(float(o), casas)
    return o


def contabilidade(nac: dict[str, Any]) -> dict[str, Any]:
    o, d = nac["origens"], nac["destinos"]
    terc = sum(o[k] for k in P.TERCEIRA)
    bn1 = o["brancos"] + o["nulos"]
    bn2 = d["brancos"] + d["nulos"]
    c1 = sum(v for k, v in o.items() if k != "abstencao")
    c2 = sum(v for k, v in d.items() if k != "abstencao")
    dl = d["lula"] - o["lula"]
    df = d["flavio"] - o["flavio"]
    disp = terc + (bn1 - bn2) + (c2 - c1)
    return {
        "lula_1t": o["lula"],
        "lula_2t": d["lula"],
        "flavio_1t": o["flavio"],
        "flavio_2t": d["flavio"],
        "ganho_lula": dl,
        "ganho_flavio": df,
        "terceira_via_1t": terc,
        "branco_nulo_1t": bn1,
        "branco_nulo_2t": bn2,
        "queda_branco_nulo": bn1 - bn2,
        "comparecimento_1t": c1,
        "comparecimento_2t": c2,
        "aumento_comparecimento": c2 - c1,
        "abstencao_1t": o["abstencao"],
        "abstencao_2t": d["abstencao"],
        "disponiveis": disp,
        "parte_lula_pct": 100 * dl / disp,
        "parte_flavio_pct": 100 * df / disp,
        "conferencia_disponiveis_menos_ganhos": disp - dl - df,
        "teto_terceira_para_flavio_se_fidelidade_100_pct": 100 * df / terc,
        "h2h_flavio_1t": 100 * o["flavio"] / (o["flavio"] + o["lula"]),
        "h2h_flavio_2t": 100 * d["flavio"] / (d["flavio"] + d["lula"]),
        "por_candidatura_1t": {k: o[k] for k in P.TERCEIRA},
    }


def bloco_secoes(
    anterior: dict[str, Any] | None,
) -> tuple[dict | None, dict | None, str]:
    sec = D.painel_secoes()
    if sec is not None:
        regs = R.secoes(sec)
        piso = D.rotatividade_minima(sec)
        resumo = {
            "origem": "bancos locais",
            "fonte": sec["fonte"],
            "n_lidas": sec["n_lidas"],
            "n_casadas": sec["n_casadas"],
            "excluidas": sec["excluidas"],
            "secoes_json_sha256": sec["secoes_json_sha256"],
            "secoes_json_gerado_em": sec["secoes_json_gerado_em"],
            "bu_1t": sec["bu_1t_sha256_de"],
            "n_municipios_com_duas_ou_mais": regs["n_municipios_com_duas_ou_mais"],
            "especificacoes": {k: regs[k] for k in ("uf", "municipio", "zona")},
        }
        return resumo, piso, f"bancos locais ({sec['fonte']})"
    if anterior and anterior.get("regressao", {}).get("secoes"):
        s = dict(anterior["regressao"]["secoes"])
        s["origem"] = "cache"
        return s, anterior["rotatividade"]["secoes"], "cache"
    return None, None, "ausente"


def amostra_anterior(anterior: dict[str, Any] | None, atual: dict | None) -> list[dict]:
    """Guarda as linhas da amostra sorteada quando o censo das seções a substitui."""
    if not anterior or (atual and atual.get("fonte") == "amostra"):
        return []
    velho = anterior.get("regressao", {})
    if velho.get("secoes_amostra"):
        return velho["secoes_amostra"]
    sec = velho.get("secoes") or {}
    if sec.get("fonte", "amostra") == "amostra" and velho.get("secoes_resumo"):
        return [
            dict(x, nome=x["nome"].replace("Seções,", "Seções (amostra),"))
            for x in velho["secoes_resumo"]
        ]
    return []


def piso_municipal_por_uf(painel: list[dict[str, Any]]) -> dict[str, Any]:
    """Piso entre municípios por UF, usado só se não houver seções nem cache."""
    ufs: dict[str, dict[str, float]] = {}
    for uf in sorted({m["uf"] for m in painel}):
        ms = [m for m in painel if m["uf"] == uf]
        ent = sum(max(m["C2"] - m["C1"], 0) for m in ms)
        sai = sum(max(m["C1"] - m["C2"], 0) for m in ms)
        ufs[uf] = {
            "n_secoes": 0,
            "entrada_min_sobre_ausentes": ent / sum(m["A1"] for m in ms),
            "saida_min_sobre_votantes": sai / sum(m["C1"] for m in ms),
        }
    nac = D.rotatividade_municipal(painel)
    return {"regra": "piso entre municípios (sem seções)", "ufs": ufs, "nacional": nac}


def resumo_uf(cen: dict[str, Any], margens: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for uf, M in cen["por_uf"].items():
        m = I.metricas(M, margens[uf])
        t = m["terceira"]
        out.append(
            {
                "uf": uf,
                "nome": margens[uf]["nome"],
                "voltaram": m["voltaram"],
                "faltaram_no_2t": m["faltaram_no_2t"],
                "terceira_estoque": t["estoque"],
                "terceira_flavio_pct": t["flavio_pct"],
                "terceira_lula_pct": t["lula_pct"],
                "terceira_bn_pct": t["bn_pct"],
                "fidelidade_lula": m["fidelidade_lula"],
                "fidelidade_flavio": m["fidelidade_flavio"],
                "swing_h2h_pp": m["swing_h2h_pp"],
                "explica_pp": m["explica_pp"],
            }
        )
    return sorted(out, key=lambda x: x["uf"])


def tipos() -> dict[str, dict[str, str]]:
    return {a: {b: P.tipo_elo(a, b) for b in P.DESTINOS} for a in P.ORIGENS}


def contagem_tipos(M: np.ndarray) -> dict[str, Any]:
    cont: dict[str, dict[str, float]] = {}
    for i, a in enumerate(P.ORIGENS):
        for j, b in enumerate(P.DESTINOS):
            t = P.tipo_elo(a, b)
            c = cont.setdefault(t, {"elos": 0, "votos": 0.0})
            c["elos"] += 1
            c["votos"] += float(M[i, j])
    tot = float(M.sum())
    for c in cont.values():
        c["pct_votos"] = 100 * c["votos"] / tot
    return cont


def faixa(valores: list[float]) -> list[float]:
    return [min(valores), max(valores)]


def equilibrio(
    alvo: float, margens: dict, piso: dict, b: dict, nac: dict
) -> dict[str, float] | None:
    """Fidelidade de base (prior, igual para os dois) que leva a terceira via a `alvo`% para Flávio.

    A parte de Flávio na terceira via cai quando a fidelidade sobe; bissecção em [0,70; 0,99].
    """

    def parte(f: float) -> dict[str, Any]:
        cen = I.cenario(margens, piso, b, nome="", descricao="", fidelidade=f)
        return I.metricas(cen["matriz"], nac)

    lo, hi = 0.70, 0.99
    if (
        not parte(lo)["terceira"]["flavio_pct"]
        >= alvo
        >= parte(hi)["terceira"]["flavio_pct"]
    ):
        return None
    for _ in range(40):
        mid = (lo + hi) / 2
        if parte(mid)["terceira"]["flavio_pct"] > alvo:
            lo = mid
        else:
            hi = mid
    m = parte((lo + hi) / 2)
    return {
        "alvo_pct": alvo,
        "fidelidade_prior": (lo + hi) / 2,
        "fidelidade_flavio": m["fidelidade_flavio"],
        "fidelidade_lula": m["fidelidade_lula"],
        "flavio_para_lula": m["flavio_para_lula"],
        "perda_base_flavio_pct": 100 - m["fidelidade_flavio"],
    }


def main() -> None:
    anterior = json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else None
    painel = D.painel_municipal()
    margens = D.margens_uf()
    nac = D.margens_nacionais(margens)
    conta = contabilidade(nac)

    regs = R.municipais(painel)
    principal = regs["principal"]
    b = {x: principal["coef"][x]["delta_comparecimento"]["b"] for x in R.DESTINOS_REG}
    lo, hi = R.faixa_ic(principal)
    secoes_res, piso, origem_sec = bloco_secoes(anterior)
    amostra_velha = amostra_anterior(anterior, secoes_res)
    if piso is None:
        piso = piso_municipal_por_uf(painel)

    cenarios: list[tuple[str, dict[str, Any]]] = [
        (
            "central",
            {
                "nome": "Central",
                "descricao": "prior das pesquisas, abstenção pela regressão",
            },
        ),
        (
            "fidelidade_093",
            {
                "nome": "Fidelidade 0,93",
                "descricao": "Lula e Flávio retêm 93% da própria base na prior",
                "fidelidade": 0.93,
            },
        ),
        (
            "fidelidade_099",
            {
                "nome": "Fidelidade 0,99",
                "descricao": "Lula e Flávio retêm 99% da própria base na prior",
                "fidelidade": 0.99,
            },
        ),
        (
            "abstencao_ic_min",
            {
                "nome": "Abstenção, mínimo do IC",
                "descricao": "quem voltou vai a Lula no limite inferior do IC de 95%",
                "b": {"L": lo, "F": 1 - lo - b["BN"], "BN": b["BN"]},
            },
        ),
        (
            "abstencao_ic_max",
            {
                "nome": "Abstenção, máximo do IC",
                "descricao": "quem voltou vai a Lula no limite superior do IC de 95%",
                "b": {"L": hi, "F": 1 - hi - b["BN"], "BN": b["BN"]},
            },
        ),
        (
            "terceira_nexus",
            {
                "nome": "Terceira via toda pela Nexus",
                "descricao": "linhas por candidatura da Nexus de 24/10 (p. 23)",
                "terceira": P.SO_NEXUS,
            },
        ),
        (
            "terceira_datafolha",
            {
                "nome": "Terceira via toda pelo Datafolha",
                "descricao": "agregado do Datafolha de 22/10 (p. 5) para cada candidatura",
                "terceira": P.SO_DATAFOLHA,
            },
        ),
        (
            "rotatividade_dobrada",
            {
                "nome": "Rotatividade dobrada",
                "descricao": "o dobro de eleitores do 1º turno falta no 2º; entra o mesmo líquido",
                "multiplicador": 2.0,
            },
        ),
        (
            "bn_quaest",
            {
                "nome": "Branco e nulo pela Quaest",
                "descricao": "linha mista da Quaest (21/10, p. 20) sem a hipótese de persistência",
                "bn_hipotese": False,
            },
        ),
        (
            "abstencao_ajustada",
            {
                "nome": "Abstenção também ajustada",
                "descricao": "diagnóstico: o IPF mexe também na linha da regressão",
                "abstencao_fixa": False,
            },
        ),
    ]
    if secoes_res is not None:
        cs = secoes_res["especificacoes"]["municipio"]["coef"]
        bs = {x: cs[x]["delta_comparecimento"]["b"] for x in R.DESTINOS_REG}
        cenarios.insert(
            5,
            (
                "abstencao_secoes",
                {
                    "nome": "Abstenção na escala da seção",
                    "descricao": "quem voltou dividido pela regressão entre seções do mesmo município",
                    "b": bs,
                },
            ),
        )

    resultados = {}
    central_cen = None
    for chave, op in cenarios:
        op = dict(op)
        nome = op.pop("nome")
        desc = op.pop("descricao")
        bb = op.pop("b", b)
        cen = I.cenario(margens, piso, bb, nome=nome, descricao=desc, **op)
        if chave == "central":
            central_cen = cen
        resultados[chave] = {
            "nome": nome,
            "descricao": desc,
            "alpha": cen["alpha"],
            "rotatividade": cen["churn_nacional"],
            "metricas": I.metricas(cen["matriz"], nac),
            "confere": I.confere_margens(cen, margens),
            "diagnostico": cen["diagnostico"],
        }
    sem_info = I.cenario(
        margens, piso, b, nome="Sem informação", descricao="", uniforme=True
    )
    m_sem = I.metricas(sem_info["matriz"], nac)
    assert central_cen is not None
    Mc = central_cen["matriz"]
    met = resultados["central"]["metricas"]

    nao_diag = [k for k in resultados if k != "abstencao_ajustada"]
    invariantes = {
        "terceira_flavio_pct": faixa(
            [resultados[k]["metricas"]["terceira"]["flavio_pct"] for k in nao_diag]
        ),
        "terceira_lula_pct": faixa(
            [resultados[k]["metricas"]["terceira"]["lula_pct"] for k in nao_diag]
        ),
        "terceira_flavio_entre_finalistas": faixa(
            [
                resultados[k]["metricas"]["terceira"]["flavio_entre_finalistas"]
                for k in nao_diag
            ]
        ),
        "razao_consolidacao": faixa(
            [
                resultados[k]["metricas"]["razao_consolidacao_flavio_lula"]
                for k in nao_diag
            ]
        ),
        "ganho_fora_base_lula": faixa(
            [resultados[k]["metricas"]["ganho_fora_base_lula"] for k in nao_diag]
        ),
        "ganho_fora_base_flavio": faixa(
            [resultados[k]["metricas"]["ganho_fora_base_flavio"] for k in nao_diag]
        ),
        "voltaram": faixa([resultados[k]["metricas"]["voltaram"] for k in nao_diag]),
        "voltaram_lula_pct": faixa(
            [resultados[k]["metricas"]["voltaram_lula_pct"] for k in nao_diag]
        ),
        "explica_pp": faixa(
            [resultados[k]["metricas"]["explica_pp"] for k in nao_diag]
        ),
        "fidelidade_lula": faixa(
            [resultados[k]["metricas"]["fidelidade_lula"] for k in nao_diag]
        ),
        "fidelidade_flavio": faixa(
            [resultados[k]["metricas"]["fidelidade_flavio"] for k in nao_diag]
        ),
        "bn1_continua_bn_pct": faixa(
            [resultados[k]["metricas"]["bn1_continua_bn_pct"] for k in nao_diag]
        ),
        "por_candidatura_flavio_pct": {
            c: faixa(
                [
                    resultados[k]["metricas"]["terceira"]["por_candidatura"][c][
                        "flavio_pct"
                    ]
                    for k in nao_diag
                ]
            )
            for c in P.TERCEIRA
        },
    }
    ic_volta = [
        resultados["abstencao_ic_min"]["metricas"]["voltaram_lula_pct"],
        resultados["abstencao_ic_max"]["metricas"]["voltaram_lula_pct"],
    ]
    ic_explica = [
        resultados["abstencao_ic_min"]["metricas"]["explica_pp"],
        resultados["abstencao_ic_max"]["metricas"]["explica_pp"],
    ]
    polls = [x for x in P.linhas_publicadas() if x["grupo"] == "terceira"]
    pesquisas_terceira = {
        "linhas": polls,
        "flavio_do_estoque": faixa([x["publicado"]["F"] for x in polls]),
        "lula_do_estoque": faixa([x["publicado"]["L"] for x in polls]),
        "flavio_entre_finalistas": faixa([x["flavio_entre_finalistas"] for x in polls]),
    }
    pesquisas_terceira["equilibrio"] = [
        equilibrio(alvo, margens, piso, b, nac)
        for alvo in pesquisas_terceira["flavio_do_estoque"]
    ]
    reserva = D.reserva_voto_util()
    sintese = D.sintese_pre_1t()
    pesq_1t = D.terceira_via_pesquisas_1t()

    resposta = {
        "voltaram_milhoes": met["voltaram"] / 1e6,
        "voltaram_lula_pct": met["voltaram_lula_pct"],
        "voltaram_lula_ic": ic_volta,
        "liquido_por_100_lula": 100 * b["L"],
        "liquido_por_100_lula_ic": [100 * lo, 100 * hi],
        "explica_pp": met["explica_pp"],
        "explica_pp_ic": ic_explica,
        "swing_h2h_pp": met["swing_h2h_pp"],
        "terceira_flavio_pct": met["terceira"]["flavio_pct"],
        "terceira_flavio_faixa": invariantes["terceira_flavio_pct"],
        "pesquisas_flavio_do_estoque": pesquisas_terceira["flavio_do_estoque"],
        "pesquisas_flavio_entre_finalistas": pesquisas_terceira[
            "flavio_entre_finalistas"
        ],
        "regressao_terceira_flavio_pct": 100
        * principal["coef"]["F"]["terceira_via_1t"]["b"],
    }
    if secoes_res is not None:
        sm = secoes_res["especificacoes"]["municipio"]["coef"]["L"][
            "delta_comparecimento"
        ]
        resposta["secoes_por_100_lula"] = 100 * sm["b"]
        resposta["secoes_por_100_lula_ic"] = [100 * v for v in sm["ic95"]]
        if "abstencao_secoes" in resultados:
            resposta["secoes_voltaram_lula_pct"] = resultados["abstencao_secoes"][
                "metricas"
            ]["voltaram_lula_pct"]
            resposta["secoes_explica_pp"] = resultados["abstencao_secoes"]["metricas"][
                "explica_pp"
            ]

    doc = {
        "meta": {
            "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "script": "scripts/apuracao-2t-2026-transferencia.py",
            "arquivo": "transferencia.json",
            "fontes": D.fontes_usadas(
                [D.SECOES_2T, D.VOTO_UTIL, D.VOTO_UTIL_1T, D.SINTESE_PRE]
            ),
            "secoes": origem_sec,
            "rotulo": ROTULO,
        },
        "rotulo": ROTULO,
        "definicoes": {
            "universo": "eleitorado apurado de cada turno (comparecimento + abstenção); aptos = válidos + brancos + nulos + abstenção nos dois",
            "reescala": "origens do 1º turno reescaladas UF a UF para o eleitorado apurado do 2º turno (fator entre "
            f"{central_cen['diagnostico']['escala_min']:.6f} e {central_cen['diagnostico']['escala_max']:.6f})",
            "aptos_novos": "o eleitorado nacional é o mesmo nos dois arquivos; a diferença do apurado (423 do exterior fora da soma no 1º turno, duas seções não totalizadas no 2º) é absorvida pela reescala",
            "regressao": "Δvotos_X = efeito fixo + b·Δcomparecimento + c·terceira via + d·branco/nulo do 1º turno + e·Δeleitorado, tudo sobre o eleitorado médio, pesos pelo eleitorado, erro-padrão por agrupamento em UF",
            "elo_medido": "linha de origem com prior em matriz publicada por instituto (voto lembrado × intenção); o IPF ajusta",
            "elo_regressao": "linha de quem faltou no 1º turno: divisão pela regressão, retenção pela rotatividade mínima; fixa no IPF",
            "elo_estimado": "hipótese declarada (rotatividade, branco e nulo do 1º turno) ajustada pelo IPF",
            "explica_pp": "pontos da parte de Flávio entre os dois que voltariam se os votos de quem faltou no 1º turno saíssem do 2º",
            "razao_consolidacao": "ganho de Flávio fora da própria base dividido pelo de Lula",
        },
        "margens": {
            "nacional": nac,
            "ufs": {
                uf: {"origens": m["origens"], "destinos": m["destinos"]}
                for uf, m in margens.items()
            },
            "municipios_painel": len(painel),
            "delta_eleitorado_municipal_absoluto": int(
                sum(abs(m["E2"] - m["E1"]) for m in painel)
            ),
        },
        "contabilidade": conta,
        "regressao": {
            "principal": principal,
            "robustez": [R.resumo(v) for v in regs.values()],
            "secoes": secoes_res,
            "secoes_resumo": (
                [
                    R.resumo(secoes_res["especificacoes"][k])
                    for k in ("uf", "municipio", "zona")
                ]
                if secoes_res
                else []
            ),
            "secoes_amostra": amostra_velha,
            "por_uf": R.por_uf(painel),
            "dispersao": R.dispersao(painel),
            "explica_liquido_pp": R.contribuicao_fatia(
                sum(m["F2"] for m in painel),
                sum(m["L2"] for m in painel),
                b["F"] * sum(m["C2"] - m["C1"] for m in painel),
                b["L"] * sum(m["C2"] - m["C1"] for m in painel),
            ),
        },
        "rotatividade": {
            "secoes": piso,
            "municipal": D.rotatividade_municipal(painel),
            "central": resultados["central"]["rotatividade"],
        },
        "priors": {
            "fontes": P.FONTES,
            "linhas_publicadas": P.linhas_publicadas(),
            "central": {
                k: {"linha": P.media(v), "fontes": P.citacao(v)}
                for k, v in P.CENTRAL.items()
            },
            "regras": {
                "ns": "NS, indecisos e não respondeu repartidos na proporção de F, L e BN da linha",
                "piso": "0,2% em cada destino da linha (nenhum zero estrutural)",
                "branco_nulo_1t": "metade continua branco ou nulo (70% no mesmo tipo), metade escolhe um finalista na proporção da linha mista da Quaest (21/10, p. 20)",
                "rotatividade": "a mesma fração de cada eleitorado do 1º turno falta no 2º",
                "brancos_nulos_2t": "BN de cada linha separado em brancos e nulos pela proporção da UF no 2º turno",
                "divisao_dos_que_voltaram": "α = (b·saldo + o·saída)/entrada, com b da regressão principal e o = composição "
                "do comparecimento do 2º turno (como teria votado quem faltou); mantém o saldo que a regressão mede",
            },
        },
        "ipf": {
            "central": {
                "matriz": I.como_dict(Mc),
                "tipos": tipos(),
                "contagem_tipos": contagem_tipos(Mc),
                "metricas": met,
                "por_uf": resumo_uf(central_cen, margens),
                "confere": resultados["central"]["confere"],
                "diagnostico": central_cen["diagnostico"],
                "alpha": central_cen["alpha"],
            },
            "sensibilidades": resultados,
            "invariantes": invariantes,
            "sem_informacao": {
                "voltaram": m_sem["voltaram"],
                "fidelidade_lula": m_sem["fidelidade_lula"],
                "fidelidade_flavio": m_sem["fidelidade_flavio"],
                "terceira_flavio_pct": m_sem["terceira"]["flavio_pct"],
            },
        },
        "pesquisas": {
            "terceira_via_2t": pesquisas_terceira,
            "reserva_voto_util": reserva,
            "sintese_pre_1t": sintese,
            "pesquisas_1t": pesq_1t,
        },
        "resposta": resposta,
    }
    texto = json.dumps(_arredonda(doc), ensure_ascii=False, separators=(",", ":"))
    if TRAVESSAO in texto:
        raise SystemExit("travessão no JSON gerado")
    SAIDA.write_text(texto + "\n", encoding="utf-8")
    memo = memorando(doc)
    if TRAVESSAO in memo:
        raise SystemExit("travessão no memorando")
    MEMO.write_text(memo, encoding="utf-8")
    print(f"{D.rel(SAIDA)}: {SAIDA.stat().st_size:,} bytes; seções: {origem_sec}")
    print(
        f"voltaram {resposta['voltaram_milhoes']:.2f} mi; Lula {resposta['voltaram_lula_pct']:.1f}% "
        f"(IC {ic_volta[0]:.1f} a {ic_volta[1]:.1f}); explica {resposta['explica_pp']:.2f} pp "
        f"de {abs(resposta['swing_h2h_pp']):.2f}; terceira via a Flávio {resposta['terceira_flavio_pct']:.1f}%"
    )


def _pt(x: float, casas: int = 2) -> str:
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def memorando(doc: dict[str, Any]) -> str:
    c = doc["contabilidade"]
    reg = doc["regressao"]
    rp = R.resumo(reg["principal"])
    met = doc["ipf"]["central"]["metricas"]
    inv = doc["ipf"]["invariantes"]
    res = doc["resposta"]
    L = [
        "# Transferência de voto, 1º → 2º turno (presidente, 2026)",
        "",
        f"Gerado por `{doc['meta']['script']}` em {doc['meta']['gerado_em']}. Não editar à mão.",
        "",
        f"Rótulo: {ROTULO}.",
        "",
        "## 1. A conta que as duas urnas fecham (fato)",
        "",
        f"- Lula {_pt(c['lula_1t'], 0)} → {_pt(c['lula_2t'], 0)} ({_pt(c['ganho_lula'], 0)} a mais); "
        f"Flávio {_pt(c['flavio_1t'], 0)} → {_pt(c['flavio_2t'], 0)} ({_pt(c['ganho_flavio'], 0)}).",
        f"- Terceira via no 1º turno: {_pt(c['terceira_via_1t'], 0)}; branco e nulo caíram {_pt(c['queda_branco_nulo'], 0)}; "
        f"comparecimento subiu {_pt(c['aumento_comparecimento'], 0)}.",
        f"- Disponíveis: {_pt(c['disponiveis'], 0)}. Lula ficou com {_pt(c['parte_lula_pct'], 1)}% do ganho líquido; "
        f"Flávio com {_pt(c['parte_flavio_pct'], 1)}%.",
        f"- Parte de Flávio entre os dois: {_pt(c['h2h_flavio_1t'])}% → {_pt(c['h2h_flavio_2t'])}% "
        f"({_pt(c['h2h_flavio_2t'] - c['h2h_flavio_1t'])} pp).",
        "",
        "## 2. Regressão ecológica (inferência)",
        "",
        f"- Principal ({rp['n']} municípios, efeito fixo de UF, pesos pelo eleitorado): de cada 100 eleitores a mais, "
        f"Lula {_pt(rp['lula'], 1)} (IC 95% {_pt(rp['lula_ic95'][0], 1)} a {_pt(rp['lula_ic95'][1], 1)}), "
        f"Flávio {_pt(rp['flavio'], 1)}, branco/nulo {_pt(rp['branco_nulo'], 1)}.",
        f"- Terceira via (mesma regressão): Lula {_pt(rp['terceira_lula'], 1)}, Flávio {_pt(rp['terceira_flavio'], 1)}, "
        f"branco/nulo {_pt(rp['terceira_bn'], 1)} por 100 votos.",
        "",
        "| Especificação | n | Lula por 100 | IC 95% | Flávio | BN |",
        "|---|---|---|---|---|---|",
    ]
    for x in reg["robustez"] + reg["secoes_resumo"] + reg.get("secoes_amostra", []):
        L.append(
            f"| {x['nome']} | {x['n']} | {_pt(x['lula'], 1)} | {_pt(x['lula_ic95'][0], 1)} a {_pt(x['lula_ic95'][1], 1)} "
            f"| {_pt(x['flavio'], 1)} | {_pt(x['branco_nulo'], 1)} |"
        )
    L += [
        "",
        "## 3. Matriz de hipótese (IPF por UF, abstenção fixa pela regressão)",
        "",
        f"- Voltaram (faltaram no 1º turno e votaram no 2º): {_pt(met['voltaram'] / 1e6)} mi; "
        f"Lula {_pt(met['voltaram_lula_pct'], 1)}%, Flávio {_pt(met['voltaram_flavio_pct'], 1)}%, "
        f"branco/nulo {_pt(met['voltaram_bn_pct'], 1)}%.",
        f"- Faltaram no 2º depois de votar no 1º: {_pt(met['faltaram_no_2t'] / 1e6)} mi.",
        f"- Terceira via: Flávio {_pt(met['terceira']['flavio_pct'], 1)}% do estoque, Lula {_pt(met['terceira']['lula_pct'], 1)}%, "
        f"branco/nulo {_pt(met['terceira']['bn_pct'], 1)}% (faixa de Flávio nas sensibilidades: "
        f"{_pt(inv['terceira_flavio_pct'][0], 1)} a {_pt(inv['terceira_flavio_pct'][1], 1)}%).",
        f"- Ganho fora da própria base: Lula {_pt(met['ganho_fora_base_lula'] / 1e6)} mi, Flávio "
        f"{_pt(met['ganho_fora_base_flavio'] / 1e6)} mi; razão {_pt(met['razao_consolidacao_flavio_lula'], 3)} "
        f"(faixa {_pt(inv['razao_consolidacao'][0], 3)} a {_pt(inv['razao_consolidacao'][1], 3)}).",
        f"- Explica {_pt(res['explica_pp'])} pp (IC {_pt(res['explica_pp_ic'][0])} a {_pt(res['explica_pp_ic'][1])}) "
        f"dos {_pt(abs(res['swing_h2h_pp']))} pp que Flávio perdeu entre os dois.",
        "",
        "| Cenário | Voltaram (mi) | Lula entre eles | Terceira → Flávio | Razão de consolidação | Fidelidade L / F |",
        "|---|---|---|---|---|---|",
    ]
    for _k, s in doc["ipf"]["sensibilidades"].items():
        m = s["metricas"]
        L.append(
            f"| {s['nome']} | {_pt(m['voltaram'] / 1e6)} | {_pt(m['voltaram_lula_pct'], 1)}% | "
            f"{_pt(m['terceira']['flavio_pct'], 1)}% | {_pt(m['razao_consolidacao_flavio_lula'], 3)} | "
            f"{_pt(m['fidelidade_lula'], 1)} / {_pt(m['fidelidade_flavio'], 1)} |"
        )
    pt = doc["pesquisas"]["terceira_via_2t"]
    L += [
        "",
        "## 4. Contra as pesquisas",
        "",
        f"- Linhas publicadas da terceira via somada (6 ondas): Flávio de {_pt(pt['flavio_do_estoque'][0], 1)} a "
        f"{_pt(pt['flavio_do_estoque'][1], 1)}% do eleitorado, de {_pt(pt['flavio_entre_finalistas'][0], 1)} a "
        f"{_pt(pt['flavio_entre_finalistas'][1], 1)}% entre os que escolhem um finalista.",
    ]
    if doc["pesquisas"]["sintese_pre_1t"]:
        L.append(
            f"- Síntese da casa de 04/10: {_pt(100 * doc['pesquisas']['sintese_pre_1t']['fracao_flavio'], 1)}% da migração para Flávio."
        )
    if doc["pesquisas"]["reserva_voto_util"]:
        L.append(
            f"- Mapa do voto útil (26/09): reserva de 2º turno de Flávio de {_pt(doc['pesquisas']['reserva_voto_util']['eleitores'] / 1e6, 1)} mi."
        )
    L += [
        "",
        "## 5. Limites",
        "",
        "- Regressão ecológica: agregado para agregado, sensível à escala (município contra seção) e ao efeito fixo.",
        "- A matriz depende da prior; só as razões impostas pelas margens sobrevivem à troca dela.",
        "- Linhas de pesquisa são voto lembrado na mesma entrevista, sem bases publicadas por grupo.",
        "- A rotatividade bruta (quem faltou num turno e votou no outro) não é observada; usamos o piso das seções.",
        "",
    ]
    return "\n".join(L)


if __name__ == "__main__":
    main()
