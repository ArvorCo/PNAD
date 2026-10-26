"""Urna do 2º turno presidencial de 2026 e régua do 1º turno, normalizadas.

Fonte preferida: ``analysis/apuracao_2t_2026/dados/presidente.json`` (gravado
por outro pacote quando a totalização fecha). Sem ele, lê o placar ao vivo do
servidor da apuração (``/api/2t/regioes``, ``/api/2t/ufs`` e
``/api/2t/abstencao``), o que deixa o script reexecutável na noite da eleição.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PRESIDENTE_2T = ROOT / "analysis/apuracao_2t_2026/dados/presidente.json"
PRESIDENTE_1T = ROOT / "analysis/apuracao_2026/dados/presidente.json"
API = "http://127.0.0.1:4180"
NUMERO_CHAVE = {13: "lula", 22: "flavio"}
REGIOES = {
    "N": ("AC", "AM", "AP", "PA", "RO", "RR", "TO"),
    "NE": ("AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"),
    "CO": ("DF", "GO", "MS", "MT"),
    "SE": ("ES", "MG", "RJ", "SP"),
    "S": ("PR", "RS", "SC"),
}
REGIAO_DE = {uf: r for r, ufs in REGIOES.items() for uf in ufs}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def fonte(path: Path) -> dict[str, Any]:
    commit = subprocess.run(
        ["git", "log", "-1", "--format=%h %cI", "--", rel(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return {
        "arquivo": rel(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "ultimo_commit": commit or None,
    }


def _get(rota: str) -> dict[str, Any]:
    with urllib.request.urlopen(API + rota, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def _registro(
    uf: str,
    flavio: int,
    lula: int,
    *,
    validos: int | None = None,
    comparecimento: int | None = None,
    abstencao: int | None = None,
    eleitores: int | None = None,
    pst: float | None = None,
) -> dict[str, Any]:
    fl = flavio + lula
    vv = validos or fl
    pa = (
        100 * abstencao / (comparecimento + abstencao)
        if comparecimento and abstencao is not None
        else None
    )
    return {
        "uf": uf,
        "regiao": REGIAO_DE.get(uf, "ZZ"),
        "votos": {"flavio": flavio, "lula": lula},
        "validos_votos": vv,
        "validos": {"flavio": 100 * flavio / vv, "lula": 100 * lula / vv},
        "comparecimento": comparecimento,
        "abstencao": abstencao,
        "eleitores": eleitores,
        "abstencao_pct": pa,
        "pst": pst,
    }


def _somar(registros: list[dict[str, Any]], uf: str) -> dict[str, Any]:
    def soma(campo: str) -> int | None:
        vals = [r[campo] for r in registros]
        return None if any(v is None for v in vals) else sum(vals)

    return _registro(
        uf,
        sum(r["votos"]["flavio"] for r in registros),
        sum(r["votos"]["lula"] for r in registros),
        validos=sum(r["validos_votos"] for r in registros),
        comparecimento=soma("comparecimento"),
        abstencao=soma("abstencao"),
        eleitores=soma("eleitores"),
    )


def _votos_de(bloco: dict[str, Any]) -> tuple[int, int]:
    if isinstance(bloco.get("flavio"), int) and isinstance(bloco.get("lula"), int):
        return int(bloco["flavio"]), int(bloco["lula"])
    votos = bloco.get("votos") or {}
    if {"flavio", "lula"} <= votos.keys():
        return int(votos["flavio"]), int(votos["lula"])
    por_chave: dict[str, int] = {}
    for c in bloco.get("candidaturas") or []:
        chave = c.get("chave") or NUMERO_CHAVE.get(int(c.get("numero") or 0))
        if chave in ("flavio", "lula"):
            por_chave[chave] = int(c["votos"])
    if len(por_chave) != 2:
        raise ValueError("bloco sem votos de Flávio e Lula")
    return por_chave["flavio"], por_chave["lula"]


def urna_do_arquivo(path: Path) -> dict[str, Any]:
    """Lê ``presidente.json`` do 2º turno no formato do arquivo do 1º turno."""
    d = json.loads(path.read_text(encoding="utf-8"))
    nac = d.get("nacional") or d.get("brasil") or {}
    f, lu = _votos_de(nac)
    brasil = _registro(
        "BR",
        f,
        lu,
        validos=nac.get("validos"),
        comparecimento=nac.get("comparecimento"),
        abstencao=nac.get("abstencao"),
        eleitores=nac.get("eleitores") or nac.get("aptos"),
        pst=nac.get("pst")
        or (
            100 * nac["secoes"] / nac["secoes_total"]
            if nac.get("secoes") and nac.get("secoes_total")
            else None
        ),
    )
    ufs = {}
    for u in d.get("ufs") or []:
        fu, lu_ = _votos_de(u)
        ufs[u["uf"].upper()] = _registro(
            u["uf"].upper(),
            fu,
            lu_,
            validos=u.get("validos"),
            comparecimento=u.get("comparecimento"),
            abstencao=u.get("abstencao"),
            eleitores=u.get("eleitores") or u.get("aptos"),
            pst=u.get("pst"),
        )
    if len([x for x in ufs if x != "ZZ"]) != 27:
        raise ValueError("presidente.json sem as 27 UFs")
    brasil["brancos"], brasil["nulos"] = nac.get("brancos"), nac.get("nulos")
    meta = d.get("meta") or {}
    return {
        "fonte": {
            "tipo": "arquivo",
            **fonte(path),
            "pst": brasil["pst"],
            "versao_gerada_em": meta.get("versao_nacional_gerada_em"),
            "completo": nac.get("completo"),
        },
        "brasil": brasil,
        "ufs": ufs,
        "abstencao_mesmos_municipios": None,
    }


def urna_da_api() -> dict[str, Any]:
    """Placar ao vivo do servidor da apuração (somente leitura)."""
    reg = _get("/api/2t/regioes")
    tab = _get("/api/2t/ufs")
    cands = _get("/api/2t/evolucao?nivel=regiao&passo=3600")["candidatos"]
    chave = {c["sqcand"]: NUMERO_CHAVE[int(c["n"])] for c in cands}

    def votos(bloco: dict[str, Any]) -> tuple[int, int]:
        v = {chave[sq]: x["vap"] for sq, x in bloco["votos"].items()}
        return int(v["flavio"]), int(v["lula"])

    b = reg["brasil"]
    f, lu = votos(b)
    brasil = _registro(
        "BR",
        f,
        lu,
        validos=b["vv"],
        comparecimento=b["comparecimento"],
        abstencao=b["abstencao"],
        eleitores=b["te"],
        pst=b["pst"],
    )
    brasil["brancos"], brasil["nulos"] = b.get("vb"), b.get("vn")
    ufs = {}
    for u in tab["ufs"]:
        fu, lu_ = votos(u)
        ufs[u["uf"]] = _registro(
            u["uf"],
            fu,
            lu_,
            comparecimento=u["comparecimento"],
            abstencao=u["abstencao"],
            eleitores=u["te"],
            pst=u["pst"],
        )
    try:
        abst = _get("/api/2t/abstencao")
        mesmos = {
            "base": abst.get("base"),
            "brasil": abst["brasil"],
            "regioes": abst["regioes"],
        }
    except (OSError, KeyError, ValueError):
        mesmos = None
    return {
        "fonte": {
            "tipo": "api_ao_vivo",
            "url": API + "/api/2t/regioes e /api/2t/ufs",
            "at": reg["at"],
            "atualizado_em": b.get("atualizado_em"),
            "pst": b["pst"],
            "nota": "Placar parcial lido ao vivo; reexecutar quando presidente.json do 2º turno existir.",
        },
        "brasil": brasil,
        "ufs": ufs,
        "abstencao_mesmos_municipios": mesmos,
    }


def carregar_urna() -> dict[str, Any]:
    erro_arquivo = None
    if PRESIDENTE_2T.exists():
        try:
            urna = urna_do_arquivo(PRESIDENTE_2T)
        except (ValueError, KeyError, TypeError) as e:
            erro_arquivo = f"{rel(PRESIDENTE_2T)} ilegível: {e}"
        else:
            with contextlib.suppress(OSError):
                urna["abstencao_mesmos_municipios"] = urna_da_api()[
                    "abstencao_mesmos_municipios"
                ]
            return completar(urna)
    urna = urna_da_api()
    if erro_arquivo:
        urna["fonte"]["aviso"] = erro_arquivo
    return completar(urna)


def completar(urna: dict[str, Any]) -> dict[str, Any]:
    ufs = urna["ufs"]
    urna["brasil_sem_exterior"] = _somar(
        [u for k, u in ufs.items() if k != "ZZ"], "BR sem ZZ"
    )
    urna["regioes"] = {
        r: _somar([ufs[u] for u in lista], r) for r, lista in REGIOES.items()
    }
    return urna


def primeiro_turno() -> dict[str, Any]:
    """Régua do 1º turno: Brasil e UFs com terceira via e branco/nulo."""
    d = json.loads(PRESIDENTE_1T.read_text(encoding="utf-8"))

    def bloco(x: dict[str, Any], uf: str) -> dict[str, Any]:
        v = x["votos"]
        return {
            "uf": uf,
            "flavio": v["flavio"],
            "lula": v["lula"],
            "terceiros": v["terceiros"],
            "validos": x["validos"],
            "branco_nulo": x["brancos"] + x["nulos"],
            "comparecimento": x["comparecimento"],
            "abstencao": x["abstencao"],
            "eleitores": x["eleitores"],
            "abstencao_pct": 100
            * x["abstencao"]
            / (x["comparecimento"] + x["abstencao"]),
            "lula_validos_pct": 100 * v["lula"] / x["validos"],
            "flavio_validos_pct": 100 * v["flavio"] / x["validos"],
        }

    return {
        "fonte": fonte(PRESIDENTE_1T),
        "brasil": bloco(d["nacional"], "BR"),
        "ufs": {u["uf"]: bloco(u, u["uf"]) for u in d["ufs"]},
    }
