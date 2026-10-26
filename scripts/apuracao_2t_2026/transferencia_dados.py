"""Margens das duas urnas para a transferência 1º → 2º turno (presidente, 2026).

Lê só JSONs já gerados do repositório e, quando presentes, os bancos locais de
seções (ignorados pelo git):

- 2º turno: ``analysis/apuracao_2t_2026/dados/presidente.json`` (nacional, UFs,
  municípios; brancos, nulos e abstenção separados).
- 1º turno: ``analysis/apuracao_2026/dados/presidente.json`` (UFs e municípios
  com Cury, Renan, Caiado e "outros") e ``terceira_via.json`` (Zema separado de
  "outros" por município).
- Seções, opcional: ``analysis/apuracao_2t_2026/dados/secoes.json`` (amostra
  sorteada antes da votação, BU do 2º turno) com o BU da mesma seção no 1º turno
  em ``apuracao/data/secoes_2026.sqlite``.

Universo: eleitorado apurado de cada turno (comparecimento + abstenção). A
identidade aptos = válidos + brancos + nulos + abstenção é conferida nos dois.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from . import secoes_linhas

ROOT = Path(__file__).resolve().parents[2]
DADOS_2T = ROOT / "analysis/apuracao_2t_2026/dados"
DADOS_1T = ROOT / "analysis/apuracao_2026/dados"
PRES_2T = DADOS_2T / "presidente.json"
PRES_1T = DADOS_1T / "presidente.json"
TERCEIRA_1T = DADOS_1T / "terceira_via.json"
SECOES_2T = DADOS_2T / "secoes.json"
BU_1T = ROOT / "apuracao/data/secoes_2026.sqlite"
VOTO_UTIL = ROOT / "docs/assets/voto_util_092026.json"
VOTO_UTIL_1T = DADOS_1T / "voto_util.json"
SINTESE_PRE = ROOT / "analysis/predicao_2026/snapshots/2026-10-04_ae5671a1311e.json"

CHAVES_1T = ("lula", "flavio", "cury", "renan", "caiado", "zema", "outros")


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def linhas(doc: dict) -> list[dict]:
    cols = doc["colunas"]
    return [dict(zip(cols, r, strict=True)) for r in doc["linhas"]]


def fontes_usadas(extra: list[Path] | None = None) -> list[dict[str, str]]:
    base = [PRES_2T, PRES_1T, TERCEIRA_1T]
    for p in [*(extra or [])]:
        if p.exists() and p not in base:
            base.append(p)
    return [{"arquivo": rel(p), "sha256": sha256(p)} for p in base if p.exists()]


def _identidade_1t(r: dict, chave: str) -> None:
    comp = r["comparecimento"]
    soma = sum(r[k] for k in CHAVES_1T) + r["brancos"] + r["nulos"]
    if soma != comp:
        raise ValueError(
            f"1º turno {chave}: válidos + BN {soma} != comparecimento {comp}"
        )


def _identidade_2t(r: dict, chave: str) -> None:
    soma = r["lula"] + r["flavio"] + r["brancos"] + r["nulos"]
    if soma != r["comparecimento"]:
        raise ValueError(f"2º turno {chave}: válidos + BN != comparecimento")
    if r["comparecimento"] + r["abstencao"] != r["aptos_apurados"]:
        raise ValueError(
            f"2º turno {chave}: comparecimento + abstenção != aptos apurados"
        )


def painel_municipal() -> list[dict[str, Any]]:
    """Municípios do Brasil completos nos dois turnos, com as margens das duas urnas."""
    p2 = ler(PRES_2T)
    p1 = ler(PRES_1T)
    tv = {r["cd"]: r for r in linhas(ler(TERCEIRA_1T)["municipios"])}
    m1 = {r["cd_tse"]: r for r in linhas(p1["municipios"])}
    out = []
    for b in linhas(p2["municipios"]):
        if b["uf"] == "ZZ" or not b["completo"]:
            continue
        a = m1.get(b["cd_tse"])
        t = tv.get(b["cd_tse"])
        if a is None or t is None:
            continue
        if t["zema"] + t["outros"] != a["outros"]:
            raise ValueError(f"{b['cd_tse']}: Zema + outros não fecha com o 1º turno")
        r1 = {
            "comparecimento": a["comparecimento"],
            "brancos": a["brancos"],
            "nulos": a["nulos"],
            "lula": a["lula"],
            "flavio": a["flavio"],
            "cury": a["cury"],
            "renan": a["renan"],
            "caiado": a["caiado"],
            "zema": t["zema"],
            "outros": t["outros"],
        }
        _identidade_1t(r1, b["cd_tse"])
        _identidade_2t(b, b["cd_tse"])
        e1 = a["eleitores"]
        out.append(
            {
                "cd": b["cd_tse"],
                "uf": b["uf"],
                "regiao": b["regiao"],
                "capital": bool(b["capital"]),
                "nome": b["nome"],
                "E1": e1,
                "C1": a["comparecimento"],
                "A1": e1 - a["comparecimento"],
                "L1": a["lula"],
                "F1": a["flavio"],
                "T1": sum(r1[k] for k in ("cury", "renan", "caiado", "zema", "outros")),
                "BN1": a["brancos"] + a["nulos"],
                "E2": b["aptos_apurados"],
                "C2": b["comparecimento"],
                "A2": b["abstencao"],
                "L2": b["lula"],
                "F2": b["flavio"],
                "BN2": b["brancos"] + b["nulos"],
            }
        )
    return out


def _zema_por_uf() -> dict[str, int]:
    soma: Counter = Counter()
    for r in linhas(ler(TERCEIRA_1T)["municipios"]):
        soma[r["uf"]] += r["zema"]
    return dict(soma)


def margens_uf() -> dict[str, dict[str, Any]]:
    """Origens (1º turno) e destinos (2º turno) por UF, exterior como ZZ."""
    p1 = ler(PRES_1T)
    p2 = ler(PRES_2T)
    zema = _zema_por_uf()
    zema_nacional = next(
        c["votos"] for c in p1["nacional"]["candidaturas"] if c["numero"] == 30
    )
    zema["ZZ"] = zema_nacional - sum(v for k, v in zema.items() if k != "ZZ")
    u2 = {u["uf"]: u for u in p2["ufs"]}
    out: dict[str, dict[str, Any]] = {}
    for u in p1["ufs"]:
        uf = u["uf"]
        v = u["votos"]
        z = zema.get(uf, 0)
        if z > v["outros"]:
            raise ValueError(f"{uf}: Zema maior que outros")
        origens = {
            "lula": v["lula"],
            "flavio": v["flavio"],
            "cury": v["cury"],
            "renan": v["renan"],
            "caiado": v["caiado"],
            "zema": z,
            "outros": v["outros"] - z,
            "brancos": u["brancos"],
            "nulos": u["nulos"],
            "abstencao": u["abstencao"],
        }
        comp = sum(origens[k] for k in origens if k != "abstencao")
        if comp != u["comparecimento"]:
            raise ValueError(f"{uf}: soma das origens != comparecimento do 1º turno")
        b = u2[uf]
        _identidade_2t(b, uf)
        destinos = {
            "lula": b["lula"],
            "flavio": b["flavio"],
            "brancos": b["brancos"],
            "nulos": b["nulos"],
            "abstencao": b["abstencao"],
        }
        out[uf] = {
            "nome": u["nome"],
            "regiao": u["regiao"],
            "origens": origens,
            "destinos": destinos,
            "eleitores_1t": u["eleitores"],
            "apurado_1t": u["comparecimento"] + u["abstencao"],
            "aptos_2t": b["aptos"],
            "apurado_2t": b["aptos_apurados"],
        }
    return out


def margens_nacionais(ufs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Soma das UFs, conferida contra o arquivo nacional de cada turno."""
    p1 = ler(PRES_1T)["nacional"]
    p2 = ler(PRES_2T)["nacional"]
    org = Counter()
    dst = Counter()
    for m in ufs.values():
        org.update(m["origens"])
        dst.update(m["destinos"])
    confere = {
        "lula_1t": org["lula"] - p1["votos"]["lula"],
        "flavio_1t": org["flavio"] - p1["votos"]["flavio"],
        "comparecimento_1t": sum(v for k, v in org.items() if k != "abstencao")
        - p1["comparecimento"],
        "abstencao_1t": org["abstencao"] - p1["abstencao"],
        "lula_2t": dst["lula"] - p2["lula"],
        "flavio_2t": dst["flavio"] - p2["flavio"],
        "brancos_2t": dst["brancos"] - p2["brancos"],
        "nulos_2t": dst["nulos"] - p2["nulos"],
        "abstencao_2t": dst["abstencao"] - p2["abstencao"],
    }
    if any(confere.values()):
        raise ValueError(f"soma das UFs difere do nacional: {confere}")
    return {
        "origens": dict(org),
        "destinos": dict(dst),
        "eleitores_1t": p1["eleitores"],
        "apurado_1t": p1["comparecimento"] + p1["abstencao"],
        "aptos_2t": p2["aptos"],
        "apurado_2t": p2["aptos_apurados"],
        "secoes_2t": p2["secoes"],
        "secoes_total_2t": p2["secoes_total"],
        "conferencia_soma_ufs_menos_nacional": confere,
    }


def painel_secoes(limite_aptos: float = 0.10) -> dict[str, Any] | None:
    """Seções do 2º turno (amostra sorteada ou censo dos BUs) com o BU da mesma seção no 1º.

    Devolve None sem os dois arquivos locais. A tabela vem em colunas (numpy), para
    o censo de meio milhão de seções caber na memória. Peso de desenho: na amostra,
    seções do 1º turno na UF divididas pelas sorteadas; no censo, 1. Fora da conta,
    com contagem registrada: seção sem BU do 1º turno, seção cujo BU do 1º turno não
    fecha a identidade, seção sem eleitorado e seção cujo eleitorado mudou mais de
    `limite_aptos` entre os turnos (agregação, trânsito, remanejamento).
    """
    if not (SECOES_2T.exists() and BU_1T.exists()):
        return None
    doc = ler(SECOES_2T)
    if not secoes_linhas.disponivel(doc):
        print(
            "aviso: linhas por seção do 2º turno ausentes (fora do git); refaça com "
            f"{secoes_linhas.COMANDO}"
        )
        return None
    bloco = secoes_linhas.bloco(doc)
    cols = bloco["colunas"]
    ix = {c: i for i, c in enumerate(cols)}
    fonte = doc.get("fonte", "amostra")
    rows = [r for r in bloco["linhas"] if r[ix["origem"]] in ("amostra", "completo")]
    con = sqlite3.connect(f"file:{BU_1T}?mode=ro", uri=True)
    excl: Counter = Counter()
    campos: dict[str, list] = {
        k: []
        for k in (
            "uf",
            "mun",
            "zona",
            "E1",
            "C1",
            "L1",
            "F1",
            "T1",
            "BN1",
            "E2",
            "C2",
            "L2",
            "F2",
            "BN2",
        )
    }
    try:
        universo = {
            uf.upper(): n
            for uf, n in con.execute("SELECT uf, COUNT(*) FROM bu GROUP BY uf")
            if uf.lower() != "zz"
        }
        cur = con.cursor()
        for r in rows:
            k = (
                r[ix["uf"]].lower(),
                r[ix["mun"]],
                int(r[ix["zona"]]),
                int(r[ix["secao"]]),
            )
            bu = cur.execute(
                "SELECT aptos, comparecimento FROM bu WHERE uf=? AND mun=? AND zona=? AND secao=?",
                k,
            ).fetchone()
            if not bu:
                excl["sem_bu_1t"] += 1
                continue
            votos = cur.execute(
                "SELECT tipo, numero, votos FROM voto_secao "
                "WHERE uf=? AND mun=? AND zona=? AND secao=? AND cargo=1",
                k,
            ).fetchall()
            l1 = sum(v for t, n, v in votos if t == 1 and n == 13)
            f1 = sum(v for t, n, v in votos if t == 1 and n == 22)
            t1 = sum(v for t, n, v in votos if t == 1 and n not in (13, 22))
            bn1 = sum(v for t, _n, v in votos if t in (2, 3))
            if l1 + f1 + t1 + bn1 != bu[1]:
                excl["identidade_1t_nao_fecha"] += 1
                continue
            e1, e2 = bu[0], r[ix["aptos"]]
            if not e1 or not e2:
                excl["sem_eleitorado"] += 1
                continue
            if abs(e2 - e1) > limite_aptos * (e1 + e2) / 2:
                excl["eleitorado_mudou_mais_de_10_pct"] += 1
                continue
            c2, l2, f2 = r[ix["comp"]], r[ix["lu"]], r[ix["fl"]]
            for nome, v in (
                ("uf", r[ix["uf"]]),
                ("mun", r[ix["mun"]]),
                ("zona", str(r[ix["zona"]])),
                ("E1", e1),
                ("C1", bu[1]),
                ("L1", l1),
                ("F1", f1),
                ("T1", t1),
                ("BN1", bn1),
                ("E2", e2),
                ("C2", c2),
                ("L2", l2),
                ("F2", f2),
                ("BN2", c2 - l2 - f2),
            ):
                campos[nome].append(v)
    finally:
        con.close()
    tab = {
        k: np.array(v, dtype=float if k not in ("uf", "mun", "zona") else str)
        for k, v in campos.items()
    }
    n = len(tab["E1"])
    if fonte == "amostra":
        ufs, cont = np.unique(tab["uf"], return_counts=True)
        por_uf = dict(zip(ufs.tolist(), cont.tolist(), strict=True))
        tab["peso_desenho"] = np.array(
            [universo.get(u, 0) / por_uf[u] for u in tab["uf"]]
        )
    else:
        tab["peso_desenho"] = np.ones(n)
    return {
        "tabela": tab,
        "fonte": fonte,
        "rotulo": "Seções (amostra)" if fonte == "amostra" else "Seções (todas)",
        "n_lidas": len(rows),
        "n_casadas": n,
        "excluidas": dict(excl),
        "universo_uf": universo,
        "secoes_json_sha256": sha256(SECOES_2T),
        "secoes_json_gerado_em": doc.get("gerado_em"),
        "bu_1t_sha256_de": "apuracao/data/secoes_2026.sqlite (banco local, não versionado)",
    }


def rotatividade_minima(sec: dict[str, Any]) -> dict[str, Any]:
    """Piso do fluxo bruto: dentro de uma seção, quem entrou >= max(variação, 0).

    A variação usa taxas de cada turno sobre o eleitorado médio da seção, para não
    confundir eleitor em trânsito ou seção agregada com comparecimento. No censo, o
    piso é exato para o conjunto de seções casadas; na amostra, é extrapolado pelo
    peso de desenho.
    """
    t = sec["tabela"]
    e = (t["E1"] + t["E2"]) / 2
    d = (t["C2"] / t["E2"] - t["C1"] / t["E1"]) * e
    w = t["peso_desenho"]
    ent = w * np.maximum(d, 0.0)
    sai = w * np.maximum(-d, 0.0)
    a1 = w * (t["E1"] - t["C1"])
    c1 = w * t["C1"]
    ufs = {}
    for uf in sorted(set(t["uf"].tolist())):
        m = t["uf"] == uf
        ufs[uf] = {
            "n_secoes": int(m.sum()),
            "entrada_min_sobre_ausentes": float(ent[m].sum() / a1[m].sum()),
            "saida_min_sobre_votantes": float(sai[m].sum() / c1[m].sum()),
        }
    return {
        "regra": (
            "piso por seção: entrou >= max(variação líquida, 0) e saiu >= max(-variação, 0); "
            "taxas sobre ausentes e votantes do 1º turno"
            + (
                "; amostra extrapolada pelo peso de desenho"
                if sec["fonte"] == "amostra"
                else "; todas as seções casadas"
            )
        ),
        "fonte": sec["fonte"],
        "ufs": ufs,
        "nacional": {
            "n_secoes": len(e),
            "entrada_min_sobre_ausentes": float(ent.sum() / a1.sum()),
            "saida_min_sobre_votantes": float(sai.sum() / c1.sum()),
            "entrada_min_votos": float(ent.sum()),
            "saida_min_votos": float(sai.sum()),
            "liquido_votos": float(ent.sum() - sai.sum()),
        },
    }


def rotatividade_municipal(painel: list[dict[str, Any]]) -> dict[str, Any]:
    """O mesmo piso entre municípios (mais fraco que o das seções)."""
    ent = sum(max(m["C2"] - m["C1"], 0) for m in painel)
    sai = sum(max(m["C1"] - m["C2"], 0) for m in painel)
    return {
        "entrada_min_votos": ent,
        "saida_min_votos": sai,
        "liquido_votos": ent - sai,
        "entrada_min_sobre_ausentes": ent / sum(m["A1"] for m in painel),
        "saida_min_sobre_votantes": sai / sum(m["C1"] for m in painel),
        "municipios": len(painel),
    }


def reserva_voto_util() -> dict[str, Any] | None:
    """Reserva de 2º turno de Flávio no mapa do voto útil (26/09, média das casas)."""
    if not VOTO_UTIL.exists():
        return None
    d = ler(VOTO_UTIL)
    ufs = d["auxiliar"]["reserva_uf"]
    return {
        "arquivo": rel(VOTO_UTIL),
        "sha256": sha256(VOTO_UTIL),
        "gerado_em": d.get("gerado_em"),
        "eleitores": sum(u["reserva_eleitores"] for u in ufs.values()),
        "ufs": {uf: u["reserva_eleitores"] for uf, u in ufs.items()},
    }


def sintese_pre_1t() -> dict[str, Any] | None:
    """Fração da migração da terceira via que ia a Flávio na síntese de 04/10."""
    if not SINTESE_PRE.exists():
        return None
    texto = SINTESE_PRE.read_text(encoding="utf-8")
    d = json.loads(texto)

    def acha(o):
        if isinstance(o, dict):
            if "divisao_migracao" in o:
                return o["divisao_migracao"]
            for v in o.values():
                r = acha(v)
                if r is not None:
                    return r
        elif isinstance(o, list):
            for v in o:
                r = acha(v)
                if r is not None:
                    return r
        return None

    dm = acha(d)
    if not dm:
        return None
    return {
        "arquivo": rel(SINTESE_PRE),
        "sha256": sha256(SINTESE_PRE),
        "fracao_flavio": dm["sintese"]["fracao_flavio"],
        "dp_so_amostral": dm["sintese"]["dp_so_amostral"],
        "componentes": dm["resumo"],
        "pergunta": dm.get("pergunta"),
    }


def terceira_via_pesquisas_1t() -> dict[str, Any] | None:
    """Terceira via nas pesquisas finais do 1º turno (média publicada, voto_util.json)."""
    if not VOTO_UTIL_1T.exists():
        return None
    d = ler(VOTO_UTIL_1T)
    return {
        "arquivo": rel(VOTO_UTIL_1T),
        "media_publicado_validos": d["terceira_via"]["media_publicado_todas"],
        "urna_validos": d["terceira_via"]["urna_validos"],
        "flavio_pesquisas_validos": d["terceiros_por_candidato"]["publicado"][
            "media_validos"
        ]["flavio"],
    }
