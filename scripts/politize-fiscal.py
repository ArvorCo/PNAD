#!/usr/bin/env python3
"""Politize sua vizinhança: camada de fiscalização por seção (``dados/fiscal/``).

Toda seção precisa de fiscal; esta camada diz, seção por seção, quais motivos a mais
os números dão. Lê, só para leitura:

- os fragmentos do Politize já publicados (``docs/assets/politize/dados/zona`` e
  ``mun``), para seção, local, margem e perfil;
- o boletim de urna de todas as seções (``apuracao/data/secoes_2026.sqlite``, tabela
  ``bu``): identificação sem a digital, troca de urna, modelo, horários, trânsito;
- o capítulo 13 do dossiê da apuração (``analysis/apuracao_2026/dados/fiscais.json``)
  e a lista de zonas atípicas do capítulo 12 (``anomalias.json``);
- o risco do território do capítulo 13 para todos os locais
  (``data/outputs/fiscais_risco_locais.csv.gz`` e ``fiscais_risco_municipios.csv``).

Grava ``docs/assets/politize/dados/fiscal/<UF>/<zona>.json`` (um por zona),
``fiscal/regras.json`` (critérios, níveis, contagens e fontes) e o relatório
``analysis/politize/relatorio_fiscal.md``. Regras e textos em ``scripts/politize/fiscal.py``
e ``fiscal_textos.py``; contrato em ``analysis/politize/CONTRATO.md`` (seção Fiscalização).

Uso::

    python3 scripts/politize-fiscal.py            # Brasil e exterior
    python3 scripts/politize-fiscal.py --uf AC    # amostra (z e contagens só da amostra)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2026.secoes_base import fusos_por_municipio
from politize import fiscal as fz
from politize import fiscal_textos as ft

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "docs/assets/politize/dados"
SAIDA = DADOS / "fiscal"
BU = ROOT / "apuracao/data/secoes_2026.sqlite"
FISCAIS = ROOT / "analysis/apuracao_2026/dados/fiscais.json"
ANOMALIAS = ROOT / "analysis/apuracao_2026/dados/anomalias.json"
RISCO_LOCAIS = ROOT / "data/outputs/fiscais_risco_locais.csv.gz"
RISCO_MUN = ROOT / "data/outputs/fiscais_risco_municipios.csv"
RELATORIO = ROOT / "analysis/politize/relatorio_fiscal.md"
VERSAO = "1.0"
COLUNAS_SECAO = ["secao", "local_id", "pontos", "nivel", "sinais", "c13"]


def _sha(caminho: Path) -> str | None:
    if not caminho.exists():
        return None
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _fonte(chave: str, caminho: Path, descricao: str) -> dict[str, Any]:
    st = caminho.stat() if caminho.exists() else None
    return {
        "chave": chave,
        "caminho": str(caminho.relative_to(ROOT)),
        "descricao": descricao,
        "bytes": st.st_size if st else None,
        "modificado_em": (
            datetime.fromtimestamp(st.st_mtime, timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            if st
            else None
        ),
        "sha256": None if chave == "boletins" else _sha(caminho),
    }


def _tabela(obj: dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(obj["linhas"], columns=obj["colunas"])


# ---------------------------------------------------------------- leitura


def ler_secoes(ufs: list[str], zonas: dict[str, list[int]]) -> pd.DataFrame:
    partes = []
    for uf in ufs:
        for z in zonas.get(uf, []):
            arq = DADOS / f"zona/{uf}/{z}.json"
            if not arq.exists():
                continue
            t = _tabela(json.loads(arq.read_text(encoding="utf-8"))["secoes"])
            t["uf"], t["zona"] = uf, int(z)
            if len(t):
                partes.append(t)
    d = pd.concat(partes, ignore_index=True)
    d["validos"] = d[["flavio", "lula", "terceira"]].fillna(0).sum(axis=1)
    return d


def ler_bu(ufs: list[str]) -> pd.DataFrame:
    con = sqlite3.connect(f"file:{BU}?mode=ro", uri=True)
    marcas = ",".join("?" for _ in ufs)
    q = (
        "SELECT uf, mun, zona, secao, aptos_tte, hab_ano_nascimento AS ano_nasc, "
        "comp_sem_biometria AS sem_digital, abertura, encerramento, tipo_urna, "
        f"n_cargas, tipo_arquivo, modelo_urna FROM bu WHERE uf IN ({marcas})"
    )
    b = pd.read_sql(q, con, params=[u.lower() for u in ufs])
    con.close()
    fuso = fusos_por_municipio(b)
    for col, nome in (
        ("abertura", "abertura_min"),
        ("encerramento", "encerramento_min"),
    ):
        t = pd.to_datetime(b[col], errors="coerce") + pd.to_timedelta(fuso, unit="h")
        b[nome] = (t.dt.hour * 60 + t.dt.minute + t.dt.second / 60).astype(float)
        # votação de um dia só: hora depois da meia-noite seguinte não entra
        b.loc[t.dt.day != pd.to_datetime(b[col], errors="coerce").dt.day, nome] = np.nan
    b["uf"] = b["uf"].str.upper()
    return b.drop(columns=["abertura", "encerramento", "mun"])


def ler_locais(ufs: list[str], indice: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mun = _tabela(indice["municipios"])
    out: dict[str, dict[str, Any]] = {}
    for arq in mun.loc[mun["uf"].isin(ufs), "arquivo"]:
        p = DADOS / arq
        if not p.exists():
            continue
        t = _tabela(json.loads(p.read_text(encoding="utf-8"))["locais"])
        registros: list[dict[str, Any]] = [
            {str(k): v for k, v in r.items()} for r in t.to_dict("records")
        ]
        for r in registros:
            out[str(r["local_id"])] = r
    return out


def ler_csv_risco() -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    locs: dict[str, dict[str, str]] = {}
    if RISCO_LOCAIS.exists():
        with gzip.open(RISCO_LOCAIS, "rt", encoding="utf-8") as f:
            locs = {r["local_id"]: r for r in csv.DictReader(f)}
    muns: dict[str, dict[str, str]] = {}
    if RISCO_MUN.exists():
        with RISCO_MUN.open(encoding="utf-8") as f:
            muns = {
                f"{r['uf'].upper()}-{str(r['mun_tse']).zfill(5)}": r
                for r in csv.DictReader(f)
            }
    return locs, muns


def ler_cap13() -> dict[str, Any]:
    d = json.loads(FISCAIS.read_text(encoding="utf-8"))
    secoes = {}
    for s in d["secoes"]:
        secoes[(s["uf"], int(s["zona"]), int(s["secao"]))] = [
            s["nivel"],
            list(s["criterios"]),
            s.get("explicacao_provavel"),
        ]
    locais = {
        p["local_id"]: {"nivel": p["nivel"], "secoes": list(p["lista_secoes"])}
        for p in d["por_local"]
    }
    congeladas = {(z["uf"].upper(), int(z["zona"])) for z in d["zonas_congeladas"]}
    criterios = {
        c["id"]: {
            "nome": c["nome"],
            "mede": c.get("mede"),
            "conferir": c.get("o_que_conferir"),
            "explicacao_comum": c.get("explicacao_comum"),
            "secoes": c.get("secoes"),
        }
        for c in d["criterios"]
    }
    a = json.loads(ANOMALIAS.read_text(encoding="utf-8"))
    atipicas = {}
    for t in a["topo"]:
        atipicas[(str(t["uf"]).upper(), int(str(t["zona"])))] = int(t["posicao"])
    return {
        "secoes": secoes,
        "locais": locais,
        "congeladas": congeladas,
        "atipicas": atipicas,
        "criterios": criterios,
        "rotulos": d["rotulos"],
    }


# ---------------------------------------------------------------- montagem


def montar(ufs: list[str]) -> dict[str, Any]:
    t0 = time.time()
    indice = json.loads((DADOS / "indice.json").read_text(encoding="utf-8"))
    zonas = {uf: [int(z) for z in zs] for uf, zs in indice["zonas"].items()}
    sec = ler_secoes(ufs, zonas)
    bu = ler_bu(ufs)
    d = sec.merge(bu, on=["uf", "zona", "secao"], how="left")
    print(
        f"seções {len(d)} (com boletim {d['modelo_urna'].notna().sum()}) {time.time() - t0:.0f}s"
    )
    d["sinais"] = pd.Series(fz.sinais_secao(d), index=d.index, dtype=object)
    locais = ler_locais(ufs, indice)
    rloc, rmun = ler_csv_risco()
    c13 = ler_cap13()

    # local: sinais, território, capítulo 13
    por_local: dict[str, dict[str, Any]] = {}
    for lid, g in d.groupby("local_id", sort=False):
        lid = str(lid)
        cad = locais.get(lid, {})
        uf = lid.split("-")[0]
        mun_chave = "-".join(lid.split("-")[:2])
        val = float(g["validos"].sum())
        margem = (
            100
            * (float(g["flavio"].fillna(0).sum()) - float(g["lula"].fillna(0).sum()))
            / val
            if val > 0
            else None
        )
        cl = c13["locais"].get(lid)
        n_secoes = int(cad.get("secoes") or len(g))
        sl = fz.sinais_local(
            n_secoes,
            margem,
            int(val),
            cl["nivel"] if cl else None,
            len(cl["secoes"]) if cl else 0,
        )
        lat, lon = cad.get("lat"), cad.get("lon")
        terr = fz.territorio(
            rloc.get(lid),
            rmun.get(mun_chave) if uf != "ZZ" else None,
            lat if isinstance(lat, float) else None,
            lon if isinstance(lon, float) else None,
        )
        por_local[lid] = {
            "secoes": n_secoes,
            "aptos": int(g["aptos"].fillna(0).sum()),
            "sinais": sl,
            "territorio": terr,
            "c13": cl,
        }

    linhas_por_zona: dict[tuple[str, int], list[list[Any]]] = defaultdict(list)
    zona_sinais: dict[tuple[str, int], list[list[str]]] = {}
    cont_nivel: Counter[str] = Counter()
    cont_uf: dict[str, Counter[str]] = defaultdict(Counter)
    cont_cod: Counter[str] = Counter()
    aptos_nivel: Counter[str] = Counter()
    for r in d[["uf", "zona", "secao", "local_id", "aptos", "sinais"]].to_dict(
        "records"
    ):
        uf, z, s = r["uf"], int(r["zona"]), int(r["secao"])
        chave_z = (uf, z)
        if chave_z not in zona_sinais:
            zs: list[list[str]] = []
            pos = c13["atipicas"].get(chave_z)
            if pos is not None:
                zs.append(
                    ["zona_atipica", f"posição {pos} entre as 50 zonas mais atípicas"]
                )
            if chave_z in c13["congeladas"]:
                zs.append(["zona_congelada", "arquivo da zona parado 6 horas ou mais"])
            zona_sinais[chave_z] = zs
        loc = por_local[r["local_id"]]
        c = c13["secoes"].get((uf, z, s))
        pts = fz.pontuar(
            r["sinais"],
            loc["sinais"],
            zona_sinais[chave_z],
            c[0] if c else None,
            loc["territorio"],
        )
        niv = fz.nivel(pts)
        loc.setdefault("niveis", Counter())[niv] += 1
        linhas_por_zona[chave_z].append([s, r["local_id"], pts, niv, r["sinais"], c])
        cont_nivel[niv] += 1
        cont_uf[uf][niv] += 1
        aptos_nivel[niv] += int(r["aptos"] or 0)
        cods = {k for k, _ in r["sinais"]} | {k for k, _ in loc["sinais"]}
        cods |= {k for k, _ in zona_sinais[chave_z]}
        if c:
            cods.add(f"c13_{c[0]}")
        terr = loc["territorio"]
        if terr and terr["nivel"] in ("alto", "medio"):
            cods.add(f"territorio_{terr['nivel']}")
        cont_cod.update(cods)

    evid = evidencias(bu)
    return {
        "d": d,
        "por_local": por_local,
        "linhas": linhas_por_zona,
        "zona_sinais": zona_sinais,
        "cont_nivel": cont_nivel,
        "cont_uf": cont_uf,
        "cont_cod": cont_cod,
        "aptos_nivel": aptos_nivel,
        "c13": c13,
        "evid": evid,
    }


def evidencias(bu: pd.DataFrame) -> dict[str, Any]:
    """Números que entram nos textos (troca de urna por modelo, no boletim do 1º turno)."""
    b = bu[bu["modelo_urna"].notna() & (bu["uf"] != "ZZ")]
    troca = (b["tipo_urna"].fillna(1) != 1) | (b["n_cargas"].fillna(1) > 1)
    antigo = b["modelo_urna"] == fz.MODELO_ANTIGO
    taxa_ant = 100 * float(troca[antigo].mean()) if antigo.any() else float("nan")
    taxa_out = 100 * float(troca[~antigo].mean()) if (~antigo).any() else float("nan")
    return {
        "troca_2013": fz.br(taxa_ant),
        "troca_outras": fz.br(taxa_out),
        "secoes_2013": int(antigo.sum()),
        "secoes_outras": int((~antigo).sum()),
    }


# ---------------------------------------------------------------- escrita


def _json(caminho: Path, obj: Any) -> int:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    caminho.write_text(txt, encoding="utf-8")
    return len(txt.encode("utf-8"))


def escrever(m: dict[str, Any], ufs: list[str], completo: bool) -> dict[str, Any]:
    if completo and SAIDA.exists():
        shutil.rmtree(SAIDA)
    for uf in ufs:
        if (SAIDA / uf).exists():
            shutil.rmtree(SAIDA / uf)
    total = 0
    n = 0
    maior = (0, "")
    for (uf, z), linhas in sorted(m["linhas"].items()):
        lids = sorted({ln[1] for ln in linhas})
        locais = {}
        for lid in lids:
            loc = m["por_local"][lid]
            locais[lid] = {
                "secoes": loc["secoes"],
                "aptos": loc["aptos"],
                "sinais": loc["sinais"],
                "territorio": loc["territorio"],
                "c13": loc["c13"],
                "niveis": {k: loc["niveis"].get(k, 0) for k in fz.NIVEIS},
            }
        linhas.sort(key=lambda x: x[0])
        obj = {
            "uf": uf,
            "zona": z,
            "versao": VERSAO,
            "sinais_zona": m["zona_sinais"][(uf, z)],
            "locais": locais,
            "secoes": {"colunas": COLUNAS_SECAO, "linhas": linhas},
        }
        b = _json(SAIDA / uf / f"{z}.json", obj)
        total += b
        n += 1
        if b > maior[0]:
            maior = (b, f"{uf}/{z}.json")
    return {"arquivos": n, "bytes": total, "maior": maior}


def regras(m: dict[str, Any], ufs: list[str]) -> dict[str, Any]:
    crit = ft.criterios(m["evid"])
    total = sum(m["cont_nivel"].values())
    for k, v in crit.items():
        v["secoes"] = int(m["cont_cod"].get(k, 0))
    niveis = {}
    for k in fz.NIVEIS:
        niveis[k] = {
            **ft.NIVEIS[k],
            "secoes": int(m["cont_nivel"].get(k, 0)),
            "pct": round(100 * m["cont_nivel"].get(k, 0) / total, 2) if total else None,
            "aptos": int(m["aptos_nivel"].get(k, 0)),
            "corte": fz.CORTES.get(k, 0),
        }
    cap13 = {
        **ft.CAP13,
        "pesos": {k: fz.PESOS[f"c13_{k}"] for k in ("alta", "media", "baixa")},
        "secoes_por_nivel": {
            k: int(m["cont_cod"].get(f"c13_{k}", 0)) for k in ("alta", "media", "baixa")
        },
        "criterios": m["c13"]["criterios"],
    }
    fontes = [
        _fonte(
            "boletins", BU, "boletins de urna por seção, 1º turno de 2026 (tabela bu)"
        ),
        _fonte(
            "politize_zona",
            DADOS / "indice.json",
            "fragmentos do Politize (seção, local, perfil)",
        ),
        _fonte("fiscais", FISCAIS, "capítulo 13 do dossiê da apuração"),
        _fonte("anomalias", ANOMALIAS, "capítulo 12: 50 zonas mais atípicas"),
        _fonte(
            "risco_locais", RISCO_LOCAIS, "risco do território por local (capítulo 13)"
        ),
        _fonte(
            "risco_municipios",
            RISCO_MUN,
            "risco do território por município (capítulo 13)",
        ),
    ]
    return {
        "versao": VERSAO,
        "gerado_em": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "ufs": ufs,
        "rotulos": ft.ROTULOS,
        "niveis": niveis,
        "ordem_niveis": list(fz.NIVEIS),
        "grupos": ft.GRUPOS,
        "criterios": crit,
        "cap13": cap13,
        "pesos": dict(fz.PESOS),
        "pontos_territorio": dict(fz.PONTOS_TERRITORIO),
        "territorio_cortes": {"alto": fz.TERRITORIO_ALTO, "medio": fz.TERRITORIO_MEDIO},
        "territorio_validar": "validar com a PM e o TRE local",
        "sempre": ft.SEMPRE,
        "cta": ft.CTA,
        "legal": ft.LEGAL,
        "evidencias": m["evid"],
        "resumo": {
            "secoes": total,
            "por_uf": {
                uf: {k: int(c.get(k, 0)) for k in fz.NIVEIS}
                for uf, c in sorted(m["cont_uf"].items())
            },
        },
        "fontes": fontes,
        "regra": (
            "Soma de pontos por seção: sinais do boletim da seção, do local de votação, da "
            "zona, do capítulo 13 e do território, com os pesos em `pesos`. Prioridade "
            f"máxima com {fz.CORTES['maxima']} pontos ou mais, alta com {fz.CORTES['alta']} "
            f"ou {fz.CORTES['maxima'] - 1}, atenção reforçada com 1 a {fz.CORTES['alta'] - 1}, "
            "atenção padrão com zero. Juízo editorial por regra declarada, não medição de "
            "irregularidade."
        ),
    }


def relatorio(m: dict[str, Any], rg: dict[str, Any], esc: dict[str, Any]) -> str:
    linhas = [
        "# Politize: camada de fiscalização por seção",
        "",
        f"Gerado em {rg['gerado_em']} por `python3 scripts/politize-fiscal.py`.",
        "",
        f"Seções: {rg['resumo']['secoes']:,}".replace(",", "."),
        f"Arquivos: {esc['arquivos']} ({esc['bytes'] / 1e6:.1f} MB); maior {esc['maior'][1]} "
        f"({esc['maior'][0] / 1e3:.0f} KB).",
        "",
        "## Nível de atenção",
        "",
        "| nível | seções | % | aptos |",
        "|---|---:|---:|---:|",
    ]
    for k in fz.NIVEIS:
        n = rg["niveis"][k]
        linhas.append(f"| {n['nome']} | {n['secoes']} | {n['pct']} | {n['aptos']} |")
    linhas += [
        "",
        "## Seções por critério (inclui sinais de local, zona e território)",
        "",
    ]
    linhas += ["| código | nome | peso | seções |", "|---|---|---:|---:|"]
    for k, v in rg["criterios"].items():
        linhas.append(f"| {k} | {v['nome']} | {v['peso']} | {v['secoes']} |")
    for k in ("alta", "media", "baixa"):
        linhas.append(
            f"| c13_{k} | capítulo 13, nível {k} | {fz.PESOS['c13_' + k]} | "
            f"{rg['cap13']['secoes_por_nivel'][k]} |"
        )
    ev = rg["evidencias"]
    linhas += [
        "",
        "## Evidência usada nos textos",
        "",
        f"- Troca de urna no 1º turno: UE2013 {ev['troca_2013']}% de {ev['secoes_2013']} "
        f"seções; demais modelos {ev['troca_outras']}% de {ev['secoes_outras']}.",
        "",
        "## Conferência",
        "",
        f"- Seções do capítulo 13 encontradas nos fragmentos: "
        f"{sum(rg['cap13']['secoes_por_nivel'].values())} de {len(m['c13']['secoes'])} "
        "(as que faltam não têm boletim publicado ou são agregadas).",
        "",
    ]
    return "\n".join(linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    ap.add_argument(
        "--uf", action="append", help="UF (repetível ou separada por vírgula)"
    )
    args = ap.parse_args()
    indice = json.loads((DADOS / "indice.json").read_text(encoding="utf-8"))
    todas = sorted(indice["zonas"].keys())
    ufs = todas
    if args.uf:
        ufs = sorted({u.strip().upper() for v in args.uf for u in v.split(",")})
        faltam = [u for u in ufs if u not in todas]
        if faltam:
            raise SystemExit(f"UF sem dados: {faltam}")
    m = montar(ufs)
    esc = escrever(m, ufs, completo=ufs == todas)
    rg = regras(m, ufs)
    _json(SAIDA / "regras.json", rg)
    if ufs == todas:
        RELATORIO.write_text(relatorio(m, rg, esc), encoding="utf-8")
    for k in fz.NIVEIS:
        print(k, rg["niveis"][k]["secoes"], rg["niveis"][k]["pct"])
    print(esc)


if __name__ == "__main__":
    main()
