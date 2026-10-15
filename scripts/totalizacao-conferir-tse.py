#!/usr/bin/env python3
"""Confere cada BU aceito (lido do QR impresso) com o BU que o TSE publica para a mesma secao.

Le as views publicas do Supabase, baixa o aux.json e o -bu.dat (ou -busa.dat) oficial da secao no
site de resultados do TSE, decodifica o ASN.1 com a especificacao de apuracao/scripts/secoes/bu.asn1
e compara, por eleicao e cargo, votos nominais por numero, legenda por partido, brancos, nulos,
comparecimento e aptos. Grava docs/assets/totalizacao_dados/conferencia_tse.json e .csv.

Retomavel: secoes ja conferidas como iguais ou divergentes com o mesmo hash do BU nao sao
rebaixadas; as ainda nao publicadas pelo TSE sao reconsultadas a cada execucao. Igualdade comprova
transmissao e soma; nao diz nada sobre o interior da urna.

Uso: python3 scripts/totalizacao-conferir-tse.py [--refazer] [--paralelo 6]
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import asn1tools
from totalizacao_comum import consultar

RAIZ = Path(__file__).resolve().parents[1]
SPEC = RAIZ / "apuracao" / "scripts" / "secoes" / "bu.asn1"
SAIDA = RAIZ / "docs" / "assets" / "totalizacao_dados"
BASE = "https://resultados.tse.jus.br/oficial/ele2026/arquivo-urna"
CABECALHOS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "application/json,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
SITUACOES_FINAIS = {"igual", "divergente"}


def p4(n: int) -> str:
    return f"{int(n):04d}"


def url_aux(uf: str, muni: int, zona: int, secao: int, pleito: int) -> str:
    base = f"{BASE}/{pleito}/dados/{uf}/{int(muni):05d}/{p4(zona)}/{p4(secao)}"
    return (
        f"{base}/p{pleito:06d}-{uf}-m{int(muni):05d}-z{p4(zona)}-s{p4(secao)}-aux.json"
    )


def escolher_arquivo(aux: dict) -> dict | None:
    """Hash mais recente com boletim; busa (apuracao) vale mais que bu quando os dois existem."""
    melhor = None
    for h in aux.get("hashes") or []:
        bu = None
        for arq in h.get("arq") or []:
            nome = arq.get("nm") or ""
            if nome.endswith("-busa.dat"):
                bu = nome
                break
            if nome.endswith("-bu.dat") and bu is None:
                bu = nome
        if bu is None:
            continue
        chave = (h.get("dr") or "", h.get("hr") or "")
        if melhor is None or chave >= melhor["chave"]:
            melhor = {
                "hash": h["hash"],
                "arquivo": bu,
                "recebido": f"{h.get('dr', '')} {h.get('hr', '')}".strip(),
                "chave": chave,
            }
    return melhor


def baixar(url: str, tentativas: int = 3) -> tuple[int, bytes]:
    for i in range(tentativas):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=CABECALHOS), timeout=60
            ) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 404, b""
            if e.code in (429, 500, 502, 503, 504) and i < tentativas - 1:
                time.sleep(2 * (i + 1))
                continue
            return e.code, b""
        except urllib.error.URLError:
            if i < tentativas - 1:
                time.sleep(2 * (i + 1))
                continue
            return 0, b""
    return 0, b""


_ASN1 = None


def asn1():
    global _ASN1
    if _ASN1 is None:
        _ASN1 = asn1tools.compile_files(str(SPEC), codec="ber")
    return _ASN1


def enum_cargos() -> dict[str, int]:
    m = re.search(
        r"CargoConstitucional ::= ENUMERATED \{(.*?)\}",
        SPEC.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert m is not None
    return {k: int(v) for k, v in re.findall(r"(\w+)\s*\((\d+)\)", m[1])}


def decodificar(raw: bytes) -> dict:
    env = asn1().decode("EntidadeEnvelopeGenerico", raw)
    return asn1().decode("EntidadeBoletimUrna", env["conteudo"])


def tse_comparavel(bu: dict) -> dict:
    """Reduz o BU do TSE ao mesmo esqueleto do BU lido do QR: eleicao -> cargo -> contagens."""
    cargos = enum_cargos()
    out = {"comparecimento": bu.get("qtdEleitoresCompareceram"), "eleicoes": {}}
    for ele in bu.get("resultadosVotacaoPorEleicao") or []:
        e = {"aptos": ele.get("qtdEleitoresAptos"), "cargos": {}}
        for rv in ele.get("resultadosVotacao") or []:
            for tc in rv.get("totaisVotosCargo") or []:
                tipo, valor = tc["codigoCargo"]
                codigo = cargos[valor] if tipo == "cargoConstitucional" else int(valor)
                c = {
                    "nominais": {},
                    "legenda": {},
                    "branco": 0,
                    "nulo": 0,
                    "comparecimento": rv.get("qtdComparecimento"),
                }
                for v in tc.get("votosVotaveis") or []:
                    t, q = v["tipoVoto"], int(v["quantidadeVotos"])
                    ident = v.get("identificacaoVotavel") or {}
                    if t == "nominal":
                        c["nominais"][str(ident.get("codigo"))] = (
                            c["nominais"].get(str(ident.get("codigo")), 0) + q
                        )
                    elif t == "legenda":
                        c["legenda"][str(ident.get("partido"))] = (
                            c["legenda"].get(str(ident.get("partido")), 0) + q
                        )
                    elif t == "branco":
                        c["branco"] += q
                    elif t == "nulo":
                        c["nulo"] += q
                e["cargos"][codigo] = c
        out["eleicoes"][int(ele["idEleicao"])] = e
    return out


def qr_comparavel(bu: dict, cargos: list[dict], votos: list[dict]) -> dict:
    """Mesmo esqueleto a partir das linhas publicas do banco (um BU, seus cargos e votos)."""
    out = {"comparecimento": bu.get("comparecimento"), "eleicoes": {}}
    for c in cargos:
        e = out["eleicoes"].setdefault(int(c["idel"]), {"aptos": None, "cargos": {}})
        e["aptos"] = c["apta"] if e["aptos"] is None else e["aptos"]
        e["cargos"][int(c["cargo"])] = {
            "nominais": {},
            "legenda": {},
            "branco": int(c["bran"]),
            "nulo": int(c["nulo"]),
            "comparecimento": int(c["totc"]),
            "apta": int(c["apta"]),
        }
    for v in votos:
        cargo = (
            out["eleicoes"]
            .get(int(v["idel"]), {})
            .get("cargos", {})
            .get(int(v["cargo"]))
        )
        if cargo is None:
            continue
        cand = str(v["candidato"])
        if cand.startswith("LEGP"):
            cargo["legenda"][cand[4:]] = int(v["votos"])
        else:
            cargo["nominais"][cand] = int(v["votos"])
    return out


def comparar(qr: dict, tse: dict) -> list[dict]:
    """Diferencas campo a campo; lista vazia significa BU identico ao publicado."""
    dif: list[dict] = []

    def reg(campo, qr_v, tse_v, idel=None, cargo=None, chave=None):
        if (qr_v or 0) != (tse_v or 0):
            dif.append(
                {
                    "campo": campo,
                    "idel": idel,
                    "cargo": cargo,
                    "chave": chave,
                    "qr": qr_v,
                    "tse": tse_v,
                }
            )

    reg("comparecimento", qr.get("comparecimento"), tse.get("comparecimento"))
    for idel in sorted(set(qr["eleicoes"]) | set(tse["eleicoes"])):
        eq, et = qr["eleicoes"].get(idel), tse["eleicoes"].get(idel)
        if eq is None or et is None:
            dif.append(
                {
                    "campo": "eleicao_ausente",
                    "idel": idel,
                    "cargo": None,
                    "chave": None,
                    "qr": eq is not None,
                    "tse": et is not None,
                }
            )
            continue
        reg("aptos", eq.get("aptos"), et.get("aptos"), idel)
        for cargo in sorted(set(eq["cargos"]) | set(et["cargos"])):
            cq, ct = eq["cargos"].get(cargo), et["cargos"].get(cargo)
            if cq is None or ct is None:
                dif.append(
                    {
                        "campo": "cargo_ausente",
                        "idel": idel,
                        "cargo": cargo,
                        "chave": None,
                        "qr": cq is not None,
                        "tse": ct is not None,
                    }
                )
                continue
            reg("branco", cq["branco"], ct["branco"], idel, cargo)
            reg("nulo", cq["nulo"], ct["nulo"], idel, cargo)
            reg(
                "comparecimento_cargo",
                cq.get("comparecimento"),
                ct.get("comparecimento"),
                idel,
                cargo,
            )
            for n in sorted(set(cq["nominais"]) | set(ct["nominais"])):
                reg(
                    "nominal",
                    cq["nominais"].get(n),
                    ct["nominais"].get(n),
                    idel,
                    cargo,
                    n,
                )
            for p in sorted(set(cq["legenda"]) | set(ct["legenda"])):
                reg(
                    "legenda",
                    cq["legenda"].get(p),
                    ct["legenda"].get(p),
                    idel,
                    cargo,
                    p,
                )
    return dif


def conferir_secao(bu: dict, cargos: list[dict], votos: list[dict]) -> dict:
    base = {
        "bu_id": bu["id"],
        "uf": bu["uf"],
        "muni": bu["muni"],
        "zona": bu["zona"],
        "secao": bu["secao"],
        "hash_final": bu["hash_final"],
    }
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if bu.get("fase") != "O":
        return {
            **base,
            "situacao": "fora_do_oficial",
            "diferencas": [],
            "conferido_em": agora,
        }
    st, corpo = baixar(
        url_aux(bu["uf"], bu["muni"], bu["zona"], bu["secao"], int(bu["pleito"]))
    )
    if st == 404:
        return {
            **base,
            "situacao": "tse_ainda_nao_publicou",
            "diferencas": [],
            "conferido_em": agora,
        }
    if st != 200:
        return {
            **base,
            "situacao": "erro",
            "erro": f"aux HTTP {st}",
            "diferencas": [],
            "conferido_em": agora,
        }
    try:
        aux = json.loads(corpo)
    except ValueError:
        return {
            **base,
            "situacao": "erro",
            "erro": "aux invalido",
            "diferencas": [],
            "conferido_em": agora,
        }
    esc = escolher_arquivo(aux)
    if esc is None:
        return {
            **base,
            "situacao": "tse_ainda_nao_publicou",
            "diferencas": [],
            "conferido_em": agora,
        }
    u = url_aux(
        bu["uf"], bu["muni"], bu["zona"], bu["secao"], int(bu["pleito"])
    ).rsplit("/", 1)[0]
    st, raw = baixar(f"{u}/{esc['hash']}/{esc['arquivo']}")
    if st != 200:
        return {
            **base,
            "situacao": "erro",
            "erro": f"bu HTTP {st}",
            "diferencas": [],
            "conferido_em": agora,
        }
    try:
        tse = tse_comparavel(decodificar(raw))
    except Exception as e:
        return {
            **base,
            "situacao": "erro",
            "erro": f"decodificacao: {type(e).__name__}",
            "diferencas": [],
            "conferido_em": agora,
        }
    dif = comparar(qr_comparavel(bu, cargos, votos), tse)
    return {
        **base,
        "situacao": "igual" if not dif else "divergente",
        "diferencas": dif,
        "tse_hash": esc["hash"],
        "tse_arquivo": esc["arquivo"],
        "tse_sha256": hashlib.sha256(raw).hexdigest(),
        "tse_recebido_em": esc["recebido"],
        "conferido_em": agora,
    }


def resumir(secoes: list[dict]) -> dict:
    r = {
        "aceitos": len(secoes),
        "iguais": 0,
        "divergentes": 0,
        "nao_publicados": 0,
        "erros": 0,
        "fora_do_oficial": 0,
    }
    for s in secoes:
        chave = {
            "igual": "iguais",
            "divergente": "divergentes",
            "tse_ainda_nao_publicou": "nao_publicados",
            "erro": "erros",
            "fora_do_oficial": "fora_do_oficial",
        }[s["situacao"]]
        r[chave] += 1
    r["conferidos"] = r["iguais"] + r["divergentes"]
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--refazer",
        action="store_true",
        help="reconfere tambem as secoes ja iguais ou divergentes",
    )
    ap.add_argument("--paralelo", type=int, default=6)
    ap.add_argument("--saida", type=Path, default=SAIDA)
    args = ap.parse_args()
    args.saida.mkdir(parents=True, exist_ok=True)
    arquivo = args.saida / "conferencia_tse.json"
    anterior = {}
    if arquivo.exists() and not args.refazer:
        for s in json.loads(arquivo.read_text(encoding="utf-8")).get("secoes", []):
            anterior[(s["bu_id"], s["hash_final"])] = s

    bus = consultar(
        "v_bu_publico",
        {
            "select": "id,uf,muni,zona,secao,fase,pleito,hash_final,aptos,comparecimento",
            "order": "id",
        },
    )
    cargos = consultar("v_bu_cargo_publico", {"order": "bu_id,idel,cargo"})
    votos = consultar("v_bu_voto_publico", {"order": "bu_id,idel,cargo,candidato"})
    por_bu_c: dict[int, list[dict]] = {}
    por_bu_v: dict[int, list[dict]] = {}
    for c in cargos:
        por_bu_c.setdefault(int(c["bu_id"]), []).append(c)
    for v in votos:
        por_bu_v.setdefault(int(v["bu_id"]), []).append(v)

    prontos: list[dict] = []
    pendentes: list[dict] = []
    for b in bus:
        s = anterior.get((b["id"], b["hash_final"]))
        if s is not None and s["situacao"] in SITUACOES_FINAIS:
            prontos.append(s)
        else:
            pendentes.append(b)
    with ThreadPoolExecutor(max_workers=max(1, args.paralelo)) as pool:
        novos = list(
            pool.map(
                lambda b: conferir_secao(
                    b, por_bu_c.get(b["id"], []), por_bu_v.get(b["id"], [])
                ),
                pendentes,
            )
        )
    secoes = sorted(prontos + novos, key=lambda s: s["bu_id"])
    resumo = resumir(secoes)
    saida = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": "BU aceito (QR impresso) contra -bu.dat/-busa.dat publicado em resultados.tse.jus.br, decodificado com bu.asn1",
        "nota": "Igualdade comprova transmissao e soma da secao; nao diz nada sobre o interior da urna. Secoes fora da fase oficial (testes) nao sao conferidas.",
        "resumo": resumo,
        "secoes": secoes,
    }
    arquivo.write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    with (args.saida / "conferencia_tse.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(
            [
                "bu_id",
                "uf",
                "muni",
                "zona",
                "secao",
                "hash_final",
                "situacao",
                "n_diferencas",
                "diferencas",
                "tse_hash",
                "tse_arquivo",
                "tse_sha256",
                "tse_recebido_em",
                "conferido_em",
            ]
        )
        for s in secoes:
            w.writerow(
                [
                    s["bu_id"],
                    s["uf"],
                    s["muni"],
                    s["zona"],
                    s["secao"],
                    s["hash_final"],
                    s["situacao"],
                    len(s["diferencas"]),
                    json.dumps(s["diferencas"], ensure_ascii=False),
                    s.get("tse_hash", ""),
                    s.get("tse_arquivo", ""),
                    s.get("tse_sha256", ""),
                    s.get("tse_recebido_em", ""),
                    s["conferido_em"],
                ]
            )
    print(json.dumps(resumo, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
