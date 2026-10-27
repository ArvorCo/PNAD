"""Leitores por seção da cauda (somente leitura): governador, BU, RDV e log.

Usados por ``zeros_cauda`` para as seções da cauda e para as duas lidas por dentro.
Governador: cargo 3 de ``voto_secao`` e ``bu_cargo`` nos bancos de BUs dos dois
turnos, com nome, partido e campo de ``analysis/governador_2026/tse_candidatos.json``
e, para os finalistas do 2º turno, de ``analysis/apuracao_2t_2026/dados/governadores.json``
(que traz também a comparação, por exemplo "coligação com o PT"). BU: tabela ``bu``
e ``secao`` (hash do BU conferido contra o conteúdo guardado). RDV: ``rdv`` e
``rdv_voto`` de ``apuracao/data/rdv_2t_2026.sqlite`` (tipos da especificação: 2
nominal, 3 e 5 branco, demais nulo). Log: ``metricas.resumo`` do 2º turno e o ZIP
original do 1º turno relido por ``apuracao_logs.parser.analisar``.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import sqlite3
from collections import Counter
from typing import Any

from apuracao_logs import parser as log_parser

from .zeros_base import DADOS, ROOT, Chave, rel

RDV = ROOT / "apuracao/data/rdv_2t_2026.sqlite"
LOGS_2T = ROOT / "data/outputs/logs_urnas_2t_2026.sqlite"
LOGS_1T = ROOT / "data/raw/tse_logs_2026/logs.sqlite"
GOVERNADORES = DADOS / "governadores.json"
CANDIDATOS_GOV = ROOT / "analysis/governador_2026/tse_candidatos.json"
RDV_RESUMO = DADOS / "rdv.json"
DIA_1T = "04/10/2026"
CAMPO_DIREITA = ("direita", "centro-direita")
TOPO_GOV_1T = 4
NUMEROS = {"lula": 13, "flavio": 22}


# ------------------------------------------------------------------ governador


def candidatos_governador() -> tuple[dict[tuple[str, int], dict[str, Any]], set[str]]:
    """Ficha por (UF, número) e as UFs com 2º turno de governador."""
    info: dict[tuple[str, int], dict[str, Any]] = {}
    for c in json.loads(CANDIDATOS_GOV.read_text(encoding="utf-8")):
        info[(c["uf"], int(c["numero"]))] = {
            "nome_urna": c["nome_urna"],
            "partido": c["partido"],
            "campo": c["campo"],
            "comparacao": None,
            "fonte": rel(CANDIDATOS_GOV),
        }
    G = json.loads(GOVERNADORES.read_text(encoding="utf-8"))
    for u in G["ufs"]:
        for c in u["candidatos"]:
            info[(u["uf"], int(c["numero"]))] = {
                "nome_urna": c["nome_urna"],
                "partido": c["partido"],
                "campo": c["campo"],
                "comparacao": c.get("comparacao"),
                "fonte": rel(GOVERNADORES),
            }
    return info, {u["uf"] for u in G["ufs"]}


def _onde(ch: Chave) -> tuple[str, str, int, int]:
    uf, mun, zona, secao = ch
    return (uf.lower(), mun, zona, secao)


ONDE = "uf = ? AND mun = ? AND zona = ? AND secao = ?"


def votos_governador(
    con: sqlite3.Connection, ch: Chave, info: dict[tuple[str, int], dict[str, Any]]
) -> dict[str, Any] | None:
    """Votos de governador da seção num banco de BUs; None sem BU do cargo 3."""
    bc = con.execute(
        f"SELECT aptos, comparecimento FROM bu_cargo WHERE {ONDE} AND cargo = 3",
        _onde(ch),
    ).fetchone()
    if bc is None:
        return None
    nominais: Counter[int] = Counter()
    outros: Counter[int] = Counter()
    for tipo, numero, votos in con.execute(
        f"SELECT tipo, numero, votos FROM voto_secao WHERE {ONDE} AND cargo = 3",
        _onde(ch),
    ):
        if tipo == 1:
            nominais[int(numero)] += votos
        else:
            outros[int(tipo)] += votos
    cands = []
    for numero, votos in sorted(nominais.items(), key=lambda kv: (-kv[1], kv[0])):
        c = info.get((ch[0], numero)) or {}
        cands.append(
            {
                "numero": numero,
                "nome_urna": c.get("nome_urna"),
                "partido": c.get("partido"),
                "campo": c.get("campo"),
                "comparacao": c.get("comparacao"),
                "votos": votos,
            }
        )
    return {
        "aptos": bc[0],
        "comparecimento": bc[1],
        "candidatos": cands,
        "brancos": outros.get(2, 0),
        "nulos": outros.get(3, 0),
        "outros_tipos": {str(k): v for k, v in outros.items() if k not in (2, 3)},
        "direita_e_centro_direita": sum(
            c["votos"] for c in cands if c["campo"] in CAMPO_DIREITA
        ),
    }


def governador(
    ch: Chave,
    con1: sqlite3.Connection,
    con2: sqlite3.Connection,
    info: dict[tuple[str, int], dict[str, Any]],
    ufs_2t: set[str],
) -> dict[str, Any]:
    t1 = votos_governador(con1, ch, info)
    t2 = votos_governador(con2, ch, info)
    if t1 is not None:
        t1["outros_candidatos"] = sum(
            c["votos"] for c in t1["candidatos"][TOPO_GOV_1T:]
        )
        t1["candidatos"] = t1["candidatos"][:TOPO_GOV_1T]
    return {"uf_tem_2t": ch[0] in ufs_2t, "t1": t1, "t2": t2}


# ------------------------------------------------------------------ BU, RDV e log


def hhmm(segundos: int | None) -> str | None:
    if segundos is None:
        return None
    return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}"


def ler_bu(con: sqlite3.Connection, ch: Chave) -> dict[str, Any]:
    """Urna, habilitação, horários e hashes do BU da seção (somente leitura)."""
    cols = (
        "numero_interno_urna",
        "modelo_urna",
        "tipo_urna",
        "aptos",
        "comparecimento",
        "hab_biometria",
        "hab_ano_nascimento",
        "comp_sem_biometria",
        "abertura",
        "encerramento",
        "carga_em",
        "codigo_carga",
        "n_cargas",
    )
    linha = con.execute(f"SELECT {', '.join(cols)} FROM bu WHERE {ONDE}", _onde(ch))
    bu = dict(zip(cols, linha.fetchone(), strict=True))
    sha_bu, gz, sha_log = con.execute(
        f"SELECT bu_sha256, bu_gz, log_sha256 FROM secao WHERE {ONDE}", _onde(ch)
    ).fetchone()
    cargos = con.execute(
        f"SELECT cargo, votos, comparecimento FROM bu_cargo WHERE {ONDE} ORDER BY cargo",
        _onde(ch),
    ).fetchall()
    comp = bu["comparecimento"] or 0
    bu |= {
        "cargos": [c for c, _, _ in cargos],
        "votos_por_eleitor": (
            round(sum(v for _, v, _ in cargos) / comp, 4) if comp else None
        ),
        "bu_sha256": sha_bu,
        "bu_confere_hash": hashlib.sha256(gzip.decompress(gz)).hexdigest() == sha_bu,
        "log_sha256": sha_log,
    }
    return bu


def ler_rdv(con: sqlite3.Connection, ch: Chave) -> dict[str, Any] | None:
    """RDV do 2º turno: estado, conferência com o BU e votos por cargo."""
    linha = con.execute(
        "SELECT status, confere, mesmo_hash_bu, sha256, rdv_gz, numero_interno_urna, "
        f"origem, tipo_urna, gerado_em FROM rdv WHERE {ONDE}",
        _onde(ch),
    ).fetchone()
    if linha is None:
        return None
    status, confere, mesmo, sha, gz, urna, origem, tipo_urna, gerado = linha
    por_cargo: dict[str, dict[str, Any]] = {}
    for cargo, tipo, dig, votos in con.execute(
        f"SELECT cargo, tipo, digitacao, votos FROM rdv_voto WHERE {ONDE}", _onde(ch)
    ):
        c = por_cargo.setdefault(
            str(cargo),
            {"nominais": {}, "brancos": 0, "nulos": 0, "nulos_digitados": {}},
        )
        if tipo == 2:
            c["nominais"][dig] = c["nominais"].get(dig, 0) + votos
        elif tipo in (3, 5):
            c["brancos"] += votos
        else:
            c["nulos"] += votos
            if dig:
                c["nulos_digitados"][dig] = c["nulos_digitados"].get(dig, 0) + votos
    return {
        "status": status,
        "confere": confere,
        "mesmo_hash_bu": mesmo,
        "sha256": sha,
        "confere_hash": (
            gz is not None and hashlib.sha256(gzip.decompress(gz)).hexdigest() == sha
        ),
        "numero_interno_urna": urna,
        "origem": origem,
        "tipo_urna": tipo_urna,
        "gerado_em": gerado,
        "por_cargo": por_cargo,
    }


def resumo_log(r: dict[str, Any]) -> dict[str, Any]:
    """Campos do leitor de logs usados no texto, iguais para os dois turnos."""
    po = r.get("processo_observado") or {}
    cont = r.get("contagens") or {}
    return {
        "versao_parser": r.get("versao_parser"),
        "urnas_log": r.get("urnas_log"),
        "cargas_log": r.get("cargas_log"),
        "modelos": r.get("modelos"),
        "votos_por_eleitor": int(po["cargos"]) if po.get("cargos") else None,
        "computados": cont.get("computados"),
        "habilitacao": r.get("tipos_habilitacao_computados"),
        "processo_p50_s": (po.get("processo") or {}).get("p50"),
        "cadencia_p50_s": (po.get("cadencia") or {}).get("p50"),
        "reinicios_durante_votacao": cont.get("reinicios_durante_votacao"),
        "inspecoes": cont.get("inspecoes_iniciadas"),
        "por_hora": r.get("computados_por_hora"),
        "por_hora_confiavel": r.get("computados_por_hora_confiavel"),
        "primeiro_computo": hhmm(r.get("primeiro_computo_s")),
        "ultimo_computo": hhmm(r.get("ultimo_computo_s")),
        "partidas_dia": [
            {k: x.get(k) for k in ("tipo", "urna", "fase", "votos_antes")}
            for x in r.get("partidas_dia") or []
        ],
    }


def log_2t(con: sqlite3.Connection, ch: Chave) -> dict[str, Any]:
    sha, versao, status, resumo = con.execute(
        f"SELECT sha256, versao, status, resumo FROM metricas WHERE {ONDE}", _onde(ch)
    ).fetchone()
    out = resumo_log(json.loads(resumo))
    return out | {
        "fonte": rel(LOGS_2T),
        "status": status,
        "versao": versao,
        "log_sha256": sha,
        "resumo_sha256": hashlib.sha256(resumo.encode("utf-8")).hexdigest(),
    }


def log_1t(con: sqlite3.Connection, ch: Chave) -> dict[str, Any]:
    sha, status, zp = con.execute(
        f"SELECT sha256, status, zip FROM arquivos WHERE {ONDE}", _onde(ch)
    ).fetchone()
    out = resumo_log(log_parser.analisar(zp, dia=DIA_1T))
    return out | {
        "fonte": rel(LOGS_1T),
        "leitor": f"apuracao_logs.parser.analisar (versão {log_parser.VERSAO}), dia {DIA_1T}",
        "status": status,
        "log_sha256": sha,
        "zip_confere_hash": hashlib.sha256(zp).hexdigest() == sha,
    }


def presidente_rdv(rdv: dict[str, Any]) -> dict[str, Any]:
    c = rdv["por_cargo"].get("1") or {}
    nom = c.get("nominais") or {}
    return {
        "lula": nom.get(str(NUMEROS["lula"]), 0),
        "flavio": nom.get(str(NUMEROS["flavio"]), 0),
        "brancos": c.get("brancos", 0),
        "nulos": c.get("nulos", 0),
        "nulos_digitados": c.get("nulos_digitados") or {},
    }


def troca_de_campo(uf: str) -> dict[str, Any] | None:
    """Nulos de presidente digitados com número de governador, na UF (rdv.json)."""
    if not RDV_RESUMO.exists():
        return None
    t = json.loads(RDV_RESUMO.read_text(encoding="utf-8")).get("troca_de_campo") or {}
    u = t.get(uf.lower())
    if not u:
        return None
    return {
        "uf": uf,
        "nulos_presidente": u.get("nulos_presidente"),
        "presidente_com_numero_de_governador": u.get(
            "presidente_com_numero_de_governador"
        ),
        "fonte": rel(RDV_RESUMO),
    }


__all__ = [
    "CAMPO_DIREITA",
    "CANDIDATOS_GOV",
    "DIA_1T",
    "GOVERNADORES",
    "LOGS_1T",
    "LOGS_2T",
    "NUMEROS",
    "RDV",
    "RDV_RESUMO",
    "TOPO_GOV_1T",
    "candidatos_governador",
    "governador",
    "hhmm",
    "ler_bu",
    "ler_rdv",
    "log_1t",
    "log_2t",
    "presidente_rdv",
    "resumo_log",
    "troca_de_campo",
    "votos_governador",
]
