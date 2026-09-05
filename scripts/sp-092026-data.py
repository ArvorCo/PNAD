#!/usr/bin/env python3
"""Atlas descritivo paulista: TSE nominal, IBGE e economia municipal.

Não estima transferência individual nem prioridades de campanha.
Votos de deputados usam a coluna nominal, preservando a votação recebida
mesmo quando o arquivo atualizado contém anulação posterior.
"""

import csv
import gzip
import io
import json
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/pesquisas/estaduais/sp/2026-09"
PUBLIC = ROOT / "docs/assets"
URLS = {
    "localidades": "https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios",
    "malha": "https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio",
    "renda": "https://apisidra.ibge.gov.br/values/t/10295/n6/in%20n3%2035/v/13431/p/2022?formato=json",
    "populacao": "https://apisidra.ibge.gov.br/values/t/4714/n6/in%20n3%2035/v/93/p/2022?formato=json",
}
NAMES = {
    "EDUARDO BOLSONARO": "eduardo",
    "CARLA ZAMBELLI": "carla",
    "MARIO FRIAS": "mario",
    "GIL DINIZ": "gil",
}


def norm(s):
    text = re.sub(
        r"[^A-Z0-9]+",
        " ",
        unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper(),
    ).strip()
    return {
        "SAO LUIS DO PARAITINGA": "SAO LUIZ DO PARAITINGA",
        "EMBU": "EMBU DAS ARTES",
        "BIRITIBA MIRIM": "BIRITIBA MIRIM",
    }.get(text, text)


def cached(name, url):
    path = BASE / "fontes" / f"{name}.json"
    if not path.exists():
        path.write_bytes(
            urlopen(
                Request(url, headers={"User-Agent": "Arvor research"}), timeout=180
            ).read()
        )
    payload = path.read_bytes()
    if payload[:2] == b"\x1f\x8b":
        payload = gzip.decompress(payload)
    return json.loads(payload)


def geography():
    cities = {}
    for r in cached("localidades", URLS["localidades"]):
        cities[norm(r["nome"])] = {
            "id": str(r["id"]),
            "nome": r["nome"],
            "regiao": r["regiao-imediata"]["regiao-intermediaria"]["nome"],
        }
    byid = {r["id"]: r for r in cities.values()}
    for kind in ("renda", "populacao"):
        for r in cached(kind, URLS[kind])[1:]:
            byid[r["D1C"]][kind] = (
                float(r["V"]) if r["V"] not in ("...", "-", "X") else None
            )
    geo = cached("malha", URLS["malha"])
    (PUBLIC / "sp_092026_municipios.geojson").write_text(
        json.dumps(geo, separators=(",", ":"))
    )
    assert len(cities) == 645
    return cities


def elections(cities):
    totals = defaultdict(Counter)
    audit = {}
    for year in (2018, 2022):
        path = ROOT / f"data/raw/tse_resultados/votacao_candidato_munzona_{year}.zip"
        with zipfile.ZipFile(path) as z:
            for suffix in ("SP", "BR"):
                member = next(
                    n for n in z.namelist() if n.endswith(f"_{year}_{suffix}.csv")
                )
                with z.open(member) as raw:
                    for row in csv.DictReader(
                        io.TextIOWrapper(raw, encoding="latin1"), delimiter=";"
                    ):
                        if row["SG_UF"] != "SP":
                            continue
                        office = row["DS_CARGO"].upper()
                        turn = row["NR_TURNO"]
                        name = norm(row["NM_URNA_CANDIDATO"])
                        if office not in (
                            "PRESIDENTE",
                            "GOVERNADOR",
                            "DEPUTADO FEDERAL",
                            "DEPUTADO ESTADUAL",
                            "SENADOR",
                        ):
                            continue
                        # Only the BR member supplies president, preventing duplication.
                        if (suffix == "BR") != (office == "PRESIDENTE"):
                            continue
                        city = norm(row["NM_MUNICIPIO"])
                        if city not in cities:
                            raise ValueError(f"Unmatched TSE municipality: {city}")
                        r = cities[city]
                        v = int(row["QT_VOTOS_NOMINAIS"])
                        valid = int(row["QT_VOTOS_NOMINAIS_VALIDOS"])
                        key = f"{year}_{office}_{turn}"
                        totals[key][name] += v
                        dkey = f"{year}_{office}_{turn}_total"
                        r[dkey] = r.get(dkey, 0) + v
                        selected = None
                        if office == "PRESIDENTE":
                            selected = (
                                "jair"
                                if name == "JAIR BOLSONARO"
                                else (
                                    "pt"
                                    if name in ("LULA", "FERNANDO HADDAD")
                                    else None
                                )
                            )
                        if office == "GOVERNADOR":
                            selected = (
                                "tarcisio"
                                if name in ("TARCISIO", "TARCISIO DE FREITAS")
                                else ("haddad" if name == "FERNANDO HADDAD" else None)
                            )
                        if office.startswith("DEPUTADO"):
                            selected = NAMES.get(name)
                        if selected:
                            k = f"{selected}_{year}_{turn}"
                            r[k] = r.get(k, 0) + v
                            av = f"{selected}_{year}_validos_atualizados"
                            audit[av] = audit.get(av, 0) + valid
        print("TSE", year, flush=True)
    for r in cities.values():
        for year in (2018, 2022):
            for turn in (1, 2):
                r[f"jair_{year}_{turn}_pct"] = (
                    100
                    * r[f"jair_{year}_{turn}"]
                    / r[f"{year}_PRESIDENTE_{turn}_total"]
                )
        for turn in (1, 2):
            r[f"tarcisio_2022_{turn}_pct"] = (
                100
                * r.get(f"tarcisio_2022_{turn}", 0)
                / r[f"2022_GOVERNADOR_{turn}_total"]
            )
        r["mudanca_jair_pp"] = r["jair_2022_2_pct"] - r["jair_2018_2_pct"]
        r["diferenca_governo_presidente_pp"] = (
            r["tarcisio_2022_2_pct"] - r["jair_2022_2_pct"]
        )
        r["virada"] = " → ".join(
            "Jair"
            if r[f"jair_{year}_2"] > r[f"pt_{year}_2"]
            else ("PT" if r[f"jair_{year}_2"] < r[f"pt_{year}_2"] else "Empate")
            for year in (2018, 2022)
        )
    return {k: dict(v) for k, v in totals.items()}, audit


def electorate(cities):
    profile = ROOT / "data/raw/tse_eleitorado/perfil_eleitorado_ATUAL.zip"
    totals = Counter()
    dates = set()
    with zipfile.ZipFile(profile) as z:
        member = next(n for n in z.namelist() if n.endswith(".csv"))
        with z.open(member) as raw:
            for row in csv.DictReader(
                io.TextIOWrapper(raw, encoding="latin1"), delimiter=";"
            ):
                if row["SG_UF"] != "SP":
                    continue
                r = cities[norm(row["NM_MUNICIPIO"])]
                v = int(row["QT_ELEITORES"])
                r["eleitorado"] = r.get("eleitorado", 0) + v
                totals[row["DS_GENERO"]] += v
                dates.add(row["DT_GERACAO"])
    return {
        "sexo": dict(totals),
        "datas_geracao": sorted(dates),
        "total": sum(totals.values()),
    }


def economy(cities):
    import pandas as pd

    path = ROOT / "data/originals/ibge_pib_municipios/base_de_dados_2010_2023_xlsx.zip"
    with zipfile.ZipFile(path) as z:
        data = z.read(z.namelist()[0])
    df = pd.read_excel(io.BytesIO(data), sheet_name="PIB dos Municípios")
    df = df[(df["Sigla da Unidade da Federação"] == "SP") & (df["Ano"] == 2023)]
    vc = next(
        c
        for c in df
        if c.startswith("Produto Interno Bruto,") and "per capita" not in c
    )
    pc = next(c for c in df if c.startswith("Produto Interno Bruto per capita"))
    nc = next(c for c in df if c == "Nome do Município")
    for _, row in df.iterrows():
        r = cities[norm(row[nc])]
        r["pib_2023"] = float(row[vc]) * 1000
        r["pib_pc_2023"] = float(row[pc])


def main():
    (BASE / "fontes").mkdir(parents=True, exist_ok=True)
    (BASE / "derivados").mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    cities = geography()
    print("IBGE", len(cities), flush=True)
    totals, audit = elections(cities)
    profile = electorate(cities)
    print("Eleitorado", profile, flush=True)
    economy(cities)
    regs = []
    for name in sorted({r["regiao"] for r in cities.values()}):
        group = [r for r in cities.values() if r["regiao"] == name]
        a = {"nome": name, "municipios": len(group)}
        for k in (
            "eleitorado",
            "populacao",
            "pib_2023",
            "jair_2018_2",
            "jair_2022_2",
            "2018_PRESIDENTE_2_total",
            "2022_PRESIDENTE_2_total",
            "tarcisio_2022_2",
            "2022_GOVERNADOR_2_total",
        ):
            a[k] = sum(r[k] for r in group)
        a["renda_media_municipal_ponderada_pop"] = (
            sum(r["renda"] * r["populacao"] for r in group) / a["populacao"]
        )
        regs.append(a)
    out = {
        "corte": "2026-09-05",
        "municipios": list(cities.values()),
        "regioes": regs,
        "eleitorado": profile,
        "totais_nominais": totals,
        "validos_atualizados_selecionados": audit,
        "fontes": URLS,
        "nota": "Deputados: votos nominais recebidos, não situação jurídica atual; sem votos de legenda. Presidência e governo: totais nominais dos candidatos.",
    }
    (PUBLIC / "sp_092026_data.json").write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    fields = sorted(set().union(*(r.keys() for r in cities.values())))
    for path in (
        BASE / "derivados/municipios.csv",
        PUBLIC / "sp_092026_municipios.csv",
    ):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(cities.values())
    print("saved", flush=True)


if __name__ == "__main__":
    main()
