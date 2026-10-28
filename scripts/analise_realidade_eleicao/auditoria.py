"""Auditoria aritmética e triagem simétrica, sem probabilidade de fraude."""

from __future__ import annotations

import hashlib
import sqlite3
from collections import defaultdict

import numpy as np

from .dados import ROOT, ler, linhas

DADOS = ROOT / "analysis/apuracao_2t_2026/dados"


def robusto(x, y):
    """Regressão Huber por IRLS. Regularização não usada; pesos só nos resíduos."""
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    for _ in range(30):
        erro = y - x @ beta
        escala = max(0.1, 1.4826 * np.median(np.abs(erro - np.median(erro))))
        peso = np.minimum(1, 1.345 * escala / np.maximum(np.abs(erro), 1e-9))
        novo = np.linalg.lstsq(
            x * np.sqrt(peso[:, None]), y * np.sqrt(peso), rcond=None
        )[0]
        if np.max(np.abs(novo - beta)) < 1e-7:
            return novo
        beta = novo
    return beta


def prever_fora_amostra(x, y, folds):
    previsao = np.empty(len(y))
    for k in range(5):
        treino, teste = folds != k, folds == k
        previsao[teste] = x[teste] @ robusto(x[treino], y[treino])
    return np.clip(previsao, 0, 100)


def triagem(ms):
    comp = {
        (r["uf"], r["cd_tse"]): r
        for r in linhas(ler(DADOS / "comparacao_1t.json")["municipios"])
    }
    rows = []
    exclusoes = defaultdict(int)
    for m in ms:
        c = comp.get((m["uf"], m["cd_tse"]))
        if not c or not c["completo"] or c["t1_flavio"] + c["t1_lula"] <= 0:
            exclusoes["sem_primeiro_turno_comparavel"] += 1
            continue
        if any(m[k] is None for k in ("renda_ate2", "superior", "rural_pct")):
            exclusoes["perfil_incompleto"] += 1
            continue
        lula_1t = 100 * c["t1_lula"] / (c["t1_flavio"] + c["t1_lula"])
        rows.append(
            {
                **m,
                "lula_1t_entre_dois": lula_1t,
                "swing_lula": m["pct_lula"] - lula_1t,
                "delta_comparecimento": c["delta_comparecimento_pp"],
                "delta_aptos": m["aptos"] - c["t1_aptos"],
                "delta_flavio": c["delta_votos_flavio"],
                "delta_lula": c["delta_votos_lula"],
            }
        )
    ufs = sorted({r["uf"] for r in rows})
    # Escalas fixas, independentes do resultado e do conjunto de validação.
    x = np.array(
        [
            [
                1,
                r["renda_ate2"] / 100,
                r["superior"] / 100,
                r["rural_pct"] / 100,
                np.log1p(r["validos"]) / 15,
                *[float(r["uf"] == uf) for uf in ufs[1:]],
            ]
            for r in rows
        ]
    )
    y = np.array([r["pct_lula"] for r in rows])
    folds = np.array(
        [int(hashlib.sha256(r["ibge"].encode()).hexdigest()[:8], 16) % 5 for r in rows]
    )
    base = prever_fora_amostra(x, y, folds)
    x1 = np.column_stack([x, [r["lula_1t_entre_dois"] / 100 for r in rows]])
    temporal = prever_fora_amostra(x1, y, folds)
    campos = (
        "ibge",
        "uf",
        "nome",
        "pct_lula",
        "validos",
        "renda_ate2",
        "superior",
        "lula_1t_entre_dois",
        "swing_lula",
        "delta_comparecimento",
        "delta_aptos",
        "delta_flavio",
        "delta_lula",
        "sede_lat",
        "sede_lon",
    )
    saida = []
    for i, r in enumerate(rows):
        saida.append(
            {
                **{k: r[k] for k in campos},
                "perfil_predito": float(base[i]),
                "perfil_residuo": float(y[i] - base[i]),
                "com_1t_predito": float(temporal[i]),
                "com_1t_residuo": float(y[i] - temporal[i]),
            }
        )
    ordenados = sorted(saida, key=lambda r: r["com_1t_residuo"])
    return {
        "n": len(rows),
        "exclusoes": dict(exclusoes),
        "mae_perfil": float(np.mean(abs(y - base))),
        "mae_com_1t": float(np.mean(abs(y - temporal))),
        "linhas": saida,
        "cauda_flavio": ordenados[:20],
        "cauda_lula": ordenados[-20:][::-1],
        "metodo": "Huber IRLS, 5 partições por SHA-256 do código IBGE, previsões fora da amostra. Mesmo peso por município. Perfil: UF, renda estimada até 2 SM, superior, rural e log dos votos válidos. Segundo modelo acrescenta Lula entre os dois finalistas no 1º turno. Sem ajuste por comparecimento, que pode fazer parte do mecanismo investigado. Predições limitadas a 0–100%.",
        "limites": "Triagem exploratória, não teste validado de fraude. A validação não separa vizinhos espacialmente. Renda deriva de escolaridade e UF; coeficientes não identificam efeitos causais. Resíduos podem refletir campanhas, transferências, composição dos presentes ou erro do modelo. O controle por UF pode absorver um efeito comum estadual; usar o 1º turno como referência não detecta um eventual problema compartilhado pelos dois turnos. Resíduo pequeno não certifica regularidade. A seleção das 20 caudas é descritiva e simétrica; não aplica correção de múltiplos testes nem declara significância.",
    }


def integridade_municipal(ms):
    erros = defaultdict(list)
    for m in ms:
        if m["flavio"] + m["lula"] != m["validos"]:
            erros["candidatos_validos"].append(m["ibge"])
        if m["validos"] + m["brancos"] + m["nulos"] != m["comparecimento"]:
            erros["votos_comparecimento"].append(m["ibge"])
        if m["comparecimento"] + m["abstencao"] != m["aptos_apurados"]:
            erros["presenca_ausencia"].append(m["ibge"])
        if m["comparecimento"] > m["aptos_apurados"]:
            erros["presenca_acima_aptos"].append(m["ibge"])
        if any(
            m[k] < 0
            for k in (
                "flavio",
                "lula",
                "validos",
                "brancos",
                "nulos",
                "comparecimento",
                "abstencao",
            )
        ):
            erros["negativos"].append(m["ibge"])
    ref = ler(DADOS / "presidente.json")["sem_exterior"]
    totais = {
        k: {"municipios": sum(m[k] for m in ms), "brasil_sem_exterior": ref[k]}
        for k in (
            "flavio",
            "lula",
            "validos",
            "brancos",
            "nulos",
            "comparecimento",
            "abstencao",
        )
    }
    return {
        "n": len(ms),
        "erros": dict(erros),
        "totais": totais,
        "aptos_residuo": sum(m["aptos"] - m["aptos_apurados"] for m in ms),
    }


def integridade_bus(ms):
    path = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
    if not path.exists():
        return {"disponivel": False, "motivo": "Banco local de BUs ausente."}
    with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        contas = {
            "bus_presidenciais": db.execute(
                "SELECT count(*) FROM bu_cargo WHERE cargo=1"
            ).fetchone()[0]
        }
        checks = {
            "comparecimento_acima_aptos": "SELECT uf,mun,zona,secao FROM bu_cargo WHERE cargo=1 AND comparecimento>aptos",
            "votos_acima_comparecimento": "SELECT uf,mun,zona,secao FROM bu_cargo WHERE cargo=1 AND votos>comparecimento",
            "negativos": "SELECT uf,mun,zona,secao FROM voto_secao WHERE cargo=1 AND votos<0",
            "soma_votos_diferente_cargo": """SELECT c.uf,c.mun,c.zona,c.secao FROM bu_cargo c
              LEFT JOIN (SELECT uf,mun,zona,secao,sum(votos) AS soma FROM voto_secao WHERE cargo=1 GROUP BY uf,mun,zona,secao) v
              USING(uf,mun,zona,secao) WHERE c.cargo=1 AND ((v.soma IS NULL AND c.votos<>0) OR v.soma<>c.votos)""",
        }
        contas["bus_sem_linhas_com_total_zero"] = [
            dict(r)
            for r in db.execute(
                """SELECT c.uf,c.mun,c.zona,c.secao,c.votos FROM bu_cargo c WHERE c.cargo=1 AND c.votos=0 AND NOT EXISTS (SELECT 1 FROM voto_secao v WHERE v.uf=c.uf AND v.mun=c.mun AND v.zona=c.zona AND v.secao=c.secao AND v.cargo=1)"""
            )
        ]
        for nome, sql in checks.items():
            contas[nome] = [dict(r) for r in db.execute(sql)]
        agregados = {(r["uf"].upper(), r["mun"]): dict(r) for r in db.execute("""
            SELECT uf,mun,sum(CASE WHEN tipo=1 AND numero=13 THEN votos ELSE 0 END) lula,
            sum(CASE WHEN tipo=1 AND numero=22 THEN votos ELSE 0 END) flavio
            FROM voto_secao WHERE cargo=1 GROUP BY uf,mun""")}
        cobertura = {
            (r["uf"].upper(), r["mun"]): r["n"]
            for r in db.execute(
                "SELECT uf,mun,count(*) n FROM bu_cargo WHERE cargo=1 GROUP BY uf,mun"
            )
        }
    diferencas, completos = [], 0
    for m in ms:
        chave = (m["uf"], m["cd_tse"])
        a = agregados.get(chave, {})
        completo = cobertura.get(chave, 0) == m["secoes_total"]
        completos += completo
        df, dl = a.get("flavio", 0) - m["flavio"], a.get("lula", 0) - m["lula"]
        if df or dl:
            diferencas.append(
                {
                    "ibge": m["ibge"],
                    "uf": m["uf"],
                    "nome": m["nome"],
                    "delta_flavio": df,
                    "delta_lula": dl,
                    "bus": cobertura.get(chave, 0),
                    "secoes_oficiais": m["secoes_total"],
                    "cobertura_completa": completo,
                }
            )
    return {
        "disponivel": True,
        "banco": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "testes": contas,
        "municipios_com_bus_completos": completos,
        "diferencas": diferencas,
        "limite": "Compara dados digitais derivados dos arquivos do TSE. Não é verificação independente do voto registrado nem da assinatura criptográfica.",
    }


def construir(ms):
    fontes = {
        n: ler(DADOS / f"{n}.json")
        for n in ("paralela", "logs", "secoes_voto", "zeros")
    }
    return {
        "municipal": integridade_municipal(ms),
        "entre_turnos": entre_turnos(),
        "zeros": {
            "recortes": fontes["zeros"]["recortes"],
            "flavio_1t": fontes["zeros"]["zero_flavio"]["primeiro_turno"],
            "lula_1t": fontes["zeros"]["zero_lula"]["primeiro_turno"],
        },
        "bus": integridade_bus(ms),
        "triagem": triagem(ms),
        "paralela": {
            k: fontes["paralela"][k] for k in ("recebidos", "conferencia", "limite")
        },
        "rdv": {
            k: v
            for k, v in fontes["logs"]["rdv"].items()
            if k not in ("ufs", "seis_ufs")
        },
        "logs_contagem": fontes["logs"]["cobertura"].get("contagem_nao_confere", []),
        "integrado": fontes["logs"]["integrado"],
        "sinais": fontes["secoes_voto"]["sinais"],
        "fontes_sha256": {
            n: hashlib.sha256((DADOS / f"{n}.json").read_bytes()).hexdigest()
            for n in (*fontes, "comparacao_1t", "urnas", "presidente")
        },
    }


def entre_turnos():
    c = ler(DADOS / "comparacao_1t.json")
    rs = [r for r in linhas(c["municipios"]) if r["completo"]]
    perdas = {}
    for cand in ("flavio", "lula"):
        reduzidos = [r for r in rs if r[f"delta_votos_{cand}"] < 0]
        perdas[cand] = {
            "n": len(reduzidos),
            "perda_liquida_nesses_municipios": sum(
                -r[f"delta_votos_{cand}"] for r in reduzidos
            ),
            "com_queda_comparecimento": sum(
                r["delta_comparecimento_votos"] < 0 for r in reduzidos
            ),
            "com_ganho_percentual_validos": sum(
                r[f"delta_fatia_{cand}_pp"] > 0 for r in reduzidos
            ),
        }
    erros = []
    for r in rs:
        if r["t1_flavio"] + r["t1_lula"] + r["t1_terceiros"] != r["t1_validos"]:
            erros.append(
                {"uf": r["uf"], "municipio": r["nome"], "regra": "votos nominais 1T"}
            )
        if (
            r["t1_validos"] > r["t1_comparecimento"]
            or r["t1_comparecimento"] > r["t1_aptos"]
        ):
            erros.append(
                {
                    "uf": r["uf"],
                    "municipio": r["nome"],
                    "regra": "limites de comparecimento 1T",
                }
            )
    return {
        "n": len(rs),
        "brasil": c["brasil"],
        "perdas": perdas,
        "erros_1t": erros,
        "urnas": ler(DADOS / "urnas.json")["entre_turnos"],
    }
