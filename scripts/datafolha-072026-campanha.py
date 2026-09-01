#!/usr/bin/env python3
"""Camada de campanha da auditoria Datafolha julho/2026 (BR-01166/2026).

Complementa `scripts/datafolha-072026-audit.py` com três blocos que o laudo
original não cobria:

1. **Painel municipal.** O anexo territorial de maio, junho e julho é lido a
   partir do CSV comparativo já gerado pela auditoria. Aqui se mede quantos
   municípios repetem nas três ondas, se a cota de entrevistas por município é
   idêntica entre rodadas, qual fatia da amostra vive nesse painel fixo e qual
   fatia do eleitorado nacional está coberta pelos 139 municípios.

2. **Cobertura de eleitorado.** Agrega `QT_ELEITORES` do pacote atual do TSE por
   município (streaming, sem extrair o CSV de 2,3 GB para disco) e casa com a
   lista do anexo por UF + nome normalizado. O resultado fica em
   `data/outputs/tse_eleitorado_municipios.csv` para reuso.

3. **Recortes de campanha.** Transcrição auditável dos cruzamentos das páginas
   29–33 do relatório (banner partido/região/natureza do município/cor/religião)
   e 24–25 (banner ocupação), com incerteza AAS da diferença, deff-limite e
   contribuição aritmética de cada grupo para o saldo nacional Flávio−Lula.

4. **Terreno eleitoral de 2022.** Agrega o 2º turno presidencial de 2022 por
   município (pacote oficial do TSE) e mede como o painel de 139 municípios
   votou, comparado ao Brasil. Serve para testar — e não apenas alegar — a
   hipótese de que o instituto teria escolhido cidades politicamente atípicas.

Uso:
  python3 scripts/datafolha-072026-campanha.py
  python3 scripts/datafolha-072026-campanha.py --rebuild-eleitorado

Saídas:
  analysis/datafolha_072026/campanha.json
  docs/assets/datafolha_072026_campanha.json
  docs/assets/datafolha_072026_municipios.json
  docs/assets/datafolha_072026_municipios.js
  data/outputs/datafolha_072026_mapa_municipios.csv
  data/outputs/tse_eleitorado_municipios.csv
  data/outputs/tse_2022_2turno_municipios.csv
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import unicodedata
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import NamedTuple


class PanelCity(NamedTuple):
    """Município do anexo territorial, com o rótulo mais completo observado."""

    municipality: str
    uf: str
    region: str


class CityVote(NamedTuple):
    """Resultado de 2022 em um município do painel."""

    municipality: str
    uf: str
    interviews: int
    bolsonaro_pct: float


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "data" / "outputs"
ANALYSIS = ROOT / "analysis" / "datafolha_072026"

TERRITORY_CSV = OUTPUTS / "datafolha_bairros_072026_compare.csv"
TSE_ZIP = ROOT / "data" / "raw" / "tse_eleitorado" / "perfil_eleitorado_ATUAL.zip"
TSE_MUN_CSV = OUTPUTS / "tse_eleitorado_municipios.csv"
VOTES_ZIP = (
    ROOT / "data" / "raw" / "tse_resultados" / "votacao_partido_munzona_2022.zip"
)
VOTES_CSV = OUTPUTS / "tse_2022_2turno_municipios.csv"
OUT_JSON = ANALYSIS / "campanha.json"
OUT_SITE_JSON = ROOT / "docs" / "assets" / "datafolha_072026_campanha.json"
OUT_SITE_CITIES = ROOT / "docs" / "assets" / "datafolha_072026_municipios.json"
OUT_SITE_CITIES_JS = ROOT / "docs" / "assets" / "datafolha_072026_municipios.js"
OUT_MAP_CSV = OUTPUTS / "datafolha_072026_mapa_municipios.csv"

SAMPLE = 2004
WAVES = ("2026-05", "2026-06", "2026-07")

CAPITAIS = {
    "1400100": "BOA VISTA",
    "1600303": "MACAPA",
    "1302603": "MANAUS",
    "1100205": "PORTO VELHO",
    "1200401": "RIO BRANCO",
    "1721000": "PALMAS",
    "1501402": "BELEM",
    "2111300": "SAO LUIS",
    "2211001": "TERESINA",
    "2304400": "FORTALEZA",
    "2408102": "NATAL",
    "2507507": "JOAO PESSOA",
    "2611606": "RECIFE",
    "2704302": "MACEIO",
    "2800308": "ARACAJU",
    "2927408": "SALVADOR",
    "3106200": "BELO HORIZONTE",
    "3205309": "VITORIA",
    "3304557": "RIO DE JANEIRO",
    "3550308": "SAO PAULO",
    "4106902": "CURITIBA",
    "4205407": "FLORIANOPOLIS",
    "4314902": "PORTO ALEGRE",
    "5002704": "CAMPO GRANDE",
    "5103403": "CUIABA",
    "5208707": "GOIANIA",
    "5300108": "BRASILIA",
}

# ---------------------------------------------------------------------------
# Transcrição auditável dos cruzamentos do relatório de julho/2026.
# Página 32: intenção de voto de 2º turno (situação A, Lula × Flávio).
# Página 33: rejeição. Página 30: 1º turno. Página 25: 2º turno por ocupação.
# ---------------------------------------------------------------------------

CROSSTABS = {
    "natureza_do_municipio": {
        "source_page": 32,
        "groups": {
            "Capital + Região Metropolitana": {"lula": 52, "flavio": 39, "base": 787},
            "Interior": {"lula": 45, "flavio": 45, "base": 1217},
        },
    },
    "preferencia_partidaria": {
        "source_page": 32,
        "groups": {
            "PT": {"lula": 98, "flavio": 2, "base": 485},
            "PL": {"lula": 2, "flavio": 98, "base": 220},
            "Outro partido": {"lula": 42, "flavio": 51, "base": 293},
            "Nenhum / não tem": {"lula": 35, "flavio": 48, "base": 1006},
        },
    },
    "cor_autodeclarada": {
        "source_page": 32,
        "groups": {
            "Parda": {"lula": 51, "flavio": 41, "base": 916},
            "Branca": {"lula": 40, "flavio": 50, "base": 715},
            "Preta": {"lula": 54, "flavio": 34, "base": 290},
        },
    },
    "religiao": {
        "source_page": 32,
        "groups": {
            "Católica": {"lula": 54, "flavio": 37, "base": 988},
            "Evangélica": {"lula": 31, "flavio": 60, "base": 495},
        },
    },
    "ocupacao": {
        "source_page": 25,
        "groups": {
            "Assalariado com registro": {"lula": 40, "flavio": 46, "base": 497},
            "Assalariado sem registro": {"lula": 49, "flavio": 39, "base": 127},
            "Funcionário público": {"lula": 47, "flavio": 42, "base": 136},
            "Autônomo / liberal / bico": {"lula": 43, "flavio": 47, "base": 478},
            "Empresário": {"lula": 27, "flavio": 65, "base": 88},
            "Desempregado": {"lula": 54, "flavio": 34, "base": 74},
            "Dona de casa": {"lula": 61, "flavio": 34, "base": 167},
            "Aposentado": {"lula": 60, "flavio": 35, "base": 294},
        },
    },
}

FIRST_ROUND_BY_NATURE = {
    "source_page": 30,
    "groups": {
        "Capital + Região Metropolitana": {"lula": 43, "flavio": 28, "base": 787},
        "Interior": {"lula": 38, "flavio": 35, "base": 1217},
    },
}

REJECTION_BY_NATURE = {
    "source_page": 33,
    "groups": {
        "Brasil": {"flavio": 48, "lula": 46, "base": SAMPLE},
        "Capital + Região Metropolitana": {"flavio": 51, "lula": 44, "base": 787},
        "Interior": {"flavio": 46, "lula": 48, "base": 1217},
        "Nenhum / não tem partido": {"flavio": 39, "lula": 55, "base": 1006},
    },
}

SPONTANEOUS_BY_NATURE = {
    "source_page": 29,
    "groups": {
        "Capital + Região Metropolitana": {"lula": 31, "flavio": 17, "nao_sabe": 34},
        "Interior": {"lula": 28, "flavio": 17, "nao_sabe": 39},
        "Nenhum / não tem partido": {"lula": 15, "flavio": 13, "nao_sabe": 53},
    },
}


# O anexo do Datafolha grafa dois municípios de forma diferente das bases do
# TSE (S/Z e o apóstrofo elidido). Alias explícito evita casamento por prefixo.
ALIASES = {
    ("PA", "SANTAISABELDOPARA"): "SANTAIZABELDOPARA",
    ("RO", "ALVORADADOESTE"): "ALVORADADOOESTE",
}


def normalize(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "".join(ch for ch in stripped.upper() if ch.isalnum() or ch == " ").strip()


def compact(text: str) -> str:
    return normalize(text).replace(" ", "")


def difference_margin(p_a: float, p_b: float, n: int, z: float = 1.96) -> float:
    """Margem da diferença em pontos percentuais sob amostragem aleatória simples."""
    variance = ((p_a + p_b) - (p_a - p_b) ** 2) / n
    return 100 * z * math.sqrt(variance)


def diagnose(groups: dict[str, dict[str, int]]) -> dict[str, object]:
    """Incerteza AAS, deff-limite e contribuição aritmética por grupo."""
    diagnostics: dict[str, object] = {}
    for name, values in groups.items():
        base = int(values["base"])
        gap = float(values["flavio"]) - float(values["lula"])
        margin = difference_margin(values["lula"] / 100, values["flavio"] / 100, base)
        diagnostics[name] = {
            "lula": values["lula"],
            "flavio": values["flavio"],
            "base": base,
            "share_of_sample_pct": round(100 * base / SAMPLE, 1),
            "flavio_minus_lula_pp": round(gap, 2),
            "srs_margin_of_difference_pp": round(margin, 2),
            "srs_95ci_flavio_minus_lula_pp": [
                round(gap - margin, 2),
                round(gap + margin, 2),
            ],
            "deff_threshold_to_include_zero": (
                round((abs(gap) / margin) ** 2, 2) if margin else None
            ),
            "arithmetic_contribution_pp": round(gap * base / SAMPLE, 2),
        }
    return diagnostics


def build_electorate_by_municipality() -> dict[tuple[str, str], int]:
    """Agrega o eleitorado atual do TSE por UF + município, em streaming."""
    totals: Counter[tuple[str, str]] = Counter()
    with zipfile.ZipFile(TSE_ZIP) as archive:
        name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        with archive.open(name) as handle:
            stream = io.TextIOWrapper(handle, encoding="latin-1", newline="")
            for row in csv.DictReader(stream, delimiter=";", quotechar='"'):
                totals[(row["SG_UF"], row["NM_MUNICIPIO"])] += int(row["QT_ELEITORES"])
    return dict(totals)


def load_electorate(rebuild: bool) -> dict[tuple[str, str], int]:
    if TSE_MUN_CSV.exists() and not rebuild:
        with TSE_MUN_CSV.open(encoding="utf-8") as handle:
            return {
                (row["uf"], row["municipio"]): int(row["eleitores"])
                for row in csv.DictReader(handle)
            }
    totals = build_electorate_by_municipality()
    with TSE_MUN_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["uf", "municipio", "eleitores"])
        for (uf, municipality), voters in sorted(totals.items()):
            writer.writerow([uf, municipality, voters])
    return totals


def lookup(table: dict[str, dict[str, int]], city: PanelCity) -> int | None:
    """Casa o rótulo truncado do anexo com a grafia oficial da base do TSE.

    A grafia varia entre bases do próprio TSE (o cadastro de eleitorado usa
    "Santa Izabel do Pará"; o de resultados, "Santa Isabel do Pará"), por isso
    a chave literal é tentada antes do alias.
    """
    entries = table.get(city.uf, {})
    key = compact(city.municipality)
    for candidate in (key, ALIASES.get((city.uf, key))):
        if candidate and candidate in entries:
            return entries[candidate]
    candidates = [name for name in entries if name.startswith(key)]
    return entries[candidates[0]] if len(candidates) == 1 else None


def index_by_uf(values: dict[tuple[str, str], int]) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = defaultdict(dict)
    for (uf, municipality), value in values.items():
        table[uf][compact(municipality)] = value
    return table


def match_electorate(
    panel: dict[str, PanelCity], electorate: dict[tuple[str, str], int]
) -> tuple[dict[str, int], list[str]]:
    table = index_by_uf(electorate)
    matched: dict[str, int] = {}
    unmatched: list[str] = []
    for code, city in panel.items():
        voters = lookup(table, city)
        if voters is None:
            unmatched.append(f"{city.municipality}/{city.uf}")
        else:
            matched[code] = voters
    return matched, unmatched


def build_votes_2022() -> dict[tuple[str, str], tuple[int, int]]:
    """Votos nominais válidos de PL e PT no 2º turno presidencial de 2022, por município.

    O pacote do TSE traz o mesmo conteúdo nacional em dois arquivos (`_BR` e
    `_BRASIL`); somar os dois dobraria a contagem. Só o `_BR` é lido.
    """
    totals: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    with zipfile.ZipFile(VOTES_ZIP) as archive:
        name = next(n for n in archive.namelist() if n.endswith("_BR.csv"))
        with archive.open(name) as handle:
            stream = io.TextIOWrapper(handle, encoding="latin-1", newline="")
            for row in csv.DictReader(stream, delimiter=";", quotechar='"'):
                if row["NR_TURNO"] != "2" or row["SG_UF"] == "ZZ":
                    continue
                if row["DS_CARGO"].strip().upper() != "PRESIDENTE":
                    continue
                key = (row["SG_UF"], row["NM_MUNICIPIO"])
                totals[key][row["SG_PARTIDO"]] += int(row["QT_VOTOS_NOMINAIS_VALIDOS"])
    return {
        key: (counter.get("PL", 0), counter.get("PT", 0))
        for key, counter in totals.items()
    }


def load_votes_2022(rebuild: bool) -> dict[tuple[str, str], tuple[int, int]]:
    if VOTES_CSV.exists() and not rebuild:
        with VOTES_CSV.open(encoding="utf-8") as handle:
            return {
                (row["uf"], row["municipio"]): (int(row["pl"]), int(row["pt"]))
                for row in csv.DictReader(handle)
            }
    if not VOTES_ZIP.exists():
        return {}
    votes = build_votes_2022()
    with VOTES_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["uf", "municipio", "pl", "pt"])
        for (uf, municipality), (pl, pt) in sorted(votes.items()):
            writer.writerow([uf, municipality, pl, pt])
    return votes


def terrain_2022(
    votes: dict[tuple[str, str], tuple[int, int]],
    panel: dict[str, PanelCity],
    july_interviews: Counter[str],
) -> dict[str, object]:
    if not votes:
        return {"status": "pacote do TSE de 2022 ausente em data/raw/tse_resultados/"}

    pl_table = index_by_uf({key: pair[0] for key, pair in votes.items()})
    pt_table = index_by_uf({key: pair[1] for key, pair in votes.items()})

    national_pl = sum(pl for pl, _ in votes.values())
    national_pt = sum(pt for _, pt in votes.values())

    per_city: list[CityVote] = []
    unmatched: list[str] = []
    panel_pl = 0
    panel_pt = 0
    for code, interviews in july_interviews.items():
        city = panel[code]
        pl = lookup(pl_table, city)
        pt = lookup(pt_table, city)
        if pl is None or pt is None or pl + pt == 0:
            unmatched.append(f"{city.municipality}/{city.uf}")
            continue
        panel_pl += pl
        panel_pt += pt
        per_city.append(
            CityVote(city.municipality, city.uf, interviews, 100 * pl / (pl + pt))
        )

    weighted = sum(item.interviews * item.bolsonaro_pct for item in per_city) / sum(
        item.interviews for item in per_city
    )
    shares = sorted(item.bolsonaro_pct for item in per_city)
    won_by_bolsonaro = [item for item in per_city if item.bolsonaro_pct > 50]
    ranked = sorted(per_city, key=lambda item: -item.bolsonaro_pct)
    interviews_in_bolsonarist = sum(item.interviews for item in won_by_bolsonaro)

    def serialize(items: list[CityVote]) -> list[dict[str, object]]:
        return [
            {
                "municipio": item.municipality,
                "uf": item.uf,
                "entrevistas": item.interviews,
                "bolsonaro_2022_pct": round(item.bolsonaro_pct, 2),
            }
            for item in items
        ]

    return {
        "brasil_bolsonaro_pct": round(
            100 * national_pl / (national_pl + national_pt), 2
        ),
        "brasil_lula_pct": round(100 * national_pt / (national_pl + national_pt), 2),
        "painel_bolsonaro_pct": round(100 * panel_pl / (panel_pl + panel_pt), 2),
        "painel_lula_pct": round(100 * panel_pt / (panel_pl + panel_pt), 2),
        "painel_bolsonaro_ponderado_por_entrevista_pct": round(weighted, 2),
        "mediana_municipal_bolsonaro_pct": round(shares[len(shares) // 2], 2),
        "municipios_vencidos_por_bolsonaro": len(won_by_bolsonaro),
        "entrevistas_em_municipios_bolsonaristas": interviews_in_bolsonarist,
        "share_entrevistas_em_municipios_bolsonaristas_pct": round(
            100 * interviews_in_bolsonarist / SAMPLE, 1
        ),
        "top_10_bolsonaristas": serialize(ranked[:10]),
        "top_10_lulistas": serialize(ranked[-10:][::-1]),
        "municipios_sem_correspondencia": unmatched,
    }


def size_class(voters: int | None) -> str:
    if voters is None:
        return "sem correspondência"
    if voters >= 1_000_000:
        return "1 mi+ eleitores"
    if voters >= 200_000:
        return "200 mil a 1 mi"
    if voters >= 50_000:
        return "50 mil a 200 mil"
    if voters >= 20_000:
        return "20 mil a 50 mil"
    return "até 20 mil"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild-eleitorado",
        action="store_true",
        help="reagrega o eleitorado municipal a partir do ZIP do TSE",
    )
    args = parser.parse_args()

    if not TERRITORY_CSV.exists():
        raise SystemExit(
            f"{TERRITORY_CSV.relative_to(ROOT)} não existe. "
            "Rode antes: python3 scripts/datafolha-072026-audit.py"
        )

    rows = list(csv.DictReader(TERRITORY_CSV.open(encoding="utf-8")))
    by_wave: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_wave[row["wave"]].append(row)

    # Nome mais longo por código: o PDF trunca rótulos em colunas estreitas.
    panel: dict[str, PanelCity] = {}
    for row in rows:
        code = row["municipality_code"]
        current = panel.get(code)
        if current is None or len(row["municipality"]) > len(current.municipality):
            panel[code] = PanelCity(row["municipality"], row["uf"], row["region"])

    interviews: dict[str, Counter[str]] = {}
    sectors: dict[str, set[str]] = {}
    for wave in WAVES:
        counter: Counter[str] = Counter()
        for row in by_wave[wave]:
            counter[row["municipality_code"]] += int(row["interviews"])
        interviews[wave] = counter
        sectors[wave] = {row["sector"] for row in by_wave[wave]}

    july_codes = set(interviews["2026-07"])
    fixed_codes = set(interviews["2026-05"]) & set(interviews["2026-06"]) & july_codes
    identical_quota = [
        code
        for code in fixed_codes
        if interviews["2026-05"][code]
        == interviews["2026-06"][code]
        == interviews["2026-07"][code]
    ]
    interviews_in_fixed = sum(interviews["2026-07"][code] for code in fixed_codes)

    electorate = load_electorate(args.rebuild_eleitorado)
    national_electorate = sum(
        voters for (uf, _), voters in electorate.items() if uf != "ZZ"
    )
    matched, unmatched = match_electorate(panel, electorate)

    brazilian_municipalities = len({key for key in electorate if key[0] != "ZZ"})
    covered = sum(matched[code] for code in july_codes if code in matched)
    covered_fixed = sum(matched[code] for code in fixed_codes if code in matched)

    uf_interviews: Counter[str] = Counter()
    for row in by_wave["2026-07"]:
        uf_interviews[row["uf"]] += int(row["interviews"])
    uf_electorate: Counter[str] = Counter()
    for (uf, _), voters in electorate.items():
        if uf != "ZZ":
            uf_electorate[uf] += voters
    uf_comparison = []
    for uf in sorted(uf_electorate, key=lambda u: -uf_electorate[u]):
        sample_share = 100 * uf_interviews.get(uf, 0) / SAMPLE
        electorate_share = 100 * uf_electorate[uf] / national_electorate
        uf_comparison.append(
            {
                "uf": uf,
                "entrevistas": uf_interviews.get(uf, 0),
                "share_amostra_pct": round(sample_share, 2),
                "share_eleitorado_pct": round(electorate_share, 2),
                "diferenca_pp": round(sample_share - electorate_share, 2),
            }
        )
    absent_ufs = [item for item in uf_comparison if item["entrevistas"] == 0]

    size_buckets: dict[str, dict[str, int]] = defaultdict(
        lambda: {"municipios": 0, "entrevistas": 0, "eleitores": 0}
    )
    for code in july_codes:
        voters = matched.get(code)
        bucket = size_buckets[size_class(voters)]
        bucket["municipios"] += 1
        bucket["entrevistas"] += interviews["2026-07"][code]
        bucket["eleitores"] += voters or 0

    capitals = july_codes & set(CAPITAIS)
    capital_interviews = sum(interviews["2026-07"][code] for code in capitals)

    ordered = sorted(july_codes, key=lambda code: -interviews["2026-07"][code])
    concentration = {}
    running = 0
    for index, code in enumerate(ordered, start=1):
        running += interviews["2026-07"][code]
        if index in (1, 2, 6, 11, 20, 30, 50, 100, 139):
            concentration[f"top_{index}"] = {
                "entrevistas": running,
                "share_pct": round(100 * running / SAMPLE, 1),
            }

    interviews_per_row = Counter(int(row["interviews"]) for row in by_wave["2026-07"])

    output = {
        "generated_from": {
            "territory_csv": str(TERRITORY_CSV.relative_to(ROOT)),
            "tse_zip": str(TSE_ZIP.relative_to(ROOT)),
            "report_pdf": "data/originals/datafolha_072026/DataFolhaRelatorio072026.pdf",
        },
        "painel_municipal": {
            "municipios_por_onda": {wave: len(interviews[wave]) for wave in WAVES},
            "municipios_nas_tres_ondas": len(fixed_codes),
            "municipios_com_cota_identica_nas_tres_ondas": len(identical_quota),
            "entrevistas_no_painel_fixo": interviews_in_fixed,
            "share_entrevistas_no_painel_fixo_pct": round(
                100 * interviews_in_fixed / SAMPLE, 1
            ),
            "setores_unicos_por_onda": {wave: len(sectors[wave]) for wave in WAVES},
            "municipios_que_sairam_jun_jul": sorted(
                f"{panel[c].municipality}/{panel[c].uf}"
                for c in set(interviews["2026-06"]) - july_codes
            ),
            "municipios_que_entraram_jun_jul": sorted(
                f"{panel[c].municipality}/{panel[c].uf}"
                for c in july_codes - set(interviews["2026-06"])
            ),
            "entrevistas_por_linha": dict(sorted(interviews_per_row.items())),
            "concentracao": concentration,
            "capitais_no_painel": len(capitals),
            "entrevistas_em_capitais": capital_interviews,
            "share_entrevistas_em_capitais_pct": round(
                100 * capital_interviews / SAMPLE, 1
            ),
            "classes_de_tamanho": {
                key: dict(value) for key, value in sorted(size_buckets.items())
            },
        },
        "cobertura_eleitoral": {
            "eleitorado_nacional_sem_exterior": national_electorate,
            "municipios_no_brasil": brazilian_municipalities,
            "municipios_na_amostra": len(july_codes),
            "share_municipios_pct": round(
                100 * len(july_codes) / brazilian_municipalities, 2
            ),
            "eleitorado_coberto": covered,
            "share_eleitorado_coberto_pct": round(
                100 * covered / national_electorate, 1
            ),
            "eleitorado_no_painel_fixo": covered_fixed,
            "share_eleitorado_painel_fixo_pct": round(
                100 * covered_fixed / national_electorate, 1
            ),
            "municipios_sem_correspondencia": unmatched,
            "eleitores_por_entrevista_nacional": round(national_electorate / SAMPLE),
            "ufs_ausentes": absent_ufs,
            "comparacao_uf": uf_comparison,
        },
        "recortes_de_campanha": {
            dimension: {
                "fonte_pagina": payload["source_page"],
                "grupos": diagnose(payload["groups"]),
            }
            for dimension, payload in CROSSTABS.items()
        },
        "primeiro_turno_por_natureza": {
            "fonte_pagina": FIRST_ROUND_BY_NATURE["source_page"],
            "grupos": diagnose(FIRST_ROUND_BY_NATURE["groups"]),
        },
        "rejeicao_por_natureza": {
            "fonte_pagina": REJECTION_BY_NATURE["source_page"],
            "grupos": REJECTION_BY_NATURE["groups"],
        },
        "espontanea_por_natureza": {
            "fonte_pagina": SPONTANEOUS_BY_NATURE["source_page"],
            "grupos": SPONTANEOUS_BY_NATURE["groups"],
        },
        "terreno_2022": terrain_2022(
            load_votes_2022(args.rebuild_eleitorado), panel, interviews["2026-07"]
        ),
        "limitacoes": [
            "A margem da diferença assume amostragem aleatória simples; o desenho real usa estratos, pontos de fluxo, cotas e ponderação.",
            "Bases publicadas são ponderadas; sem o n bruto por recorte a incerteza real pode ser maior.",
            "Repetição de município é repetição documental de unidade de seleção, não repetição do mesmo entrevistado.",
            "A cobertura de eleitorado casa nome de município por UF; três nomes com apóstrofo ou grafia divergente exigem conferência manual.",
        ],
    }

    ANALYSIS.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    OUT_JSON.write_text(payload, encoding="utf-8")
    OUT_SITE_JSON.write_text(payload, encoding="utf-8")

    with OUT_MAP_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "municipality_code",
                "municipality",
                "uf",
                "region",
                "entrevistas_jul",
                "entrevistas_jun",
                "entrevistas_mai",
                "nas_tres_ondas",
                "eleitores_tse",
                "classe_tamanho",
            ]
        )
        for code in ordered:
            writer.writerow(
                [
                    code,
                    panel[code].municipality,
                    panel[code].uf,
                    panel[code].region,
                    interviews["2026-07"][code],
                    interviews["2026-06"].get(code, 0),
                    interviews["2026-05"].get(code, 0),
                    int(code in fixed_codes),
                    matched.get(code, ""),
                    size_class(matched.get(code)),
                ]
            )

    votes_2022 = load_votes_2022(False)
    pl_table = index_by_uf({key: pair[0] for key, pair in votes_2022.items()})
    pt_table = index_by_uf({key: pair[1] for key, pair in votes_2022.items()})
    cities = []
    for code in ordered:
        city = panel[code]
        pl = lookup(pl_table, city)
        pt = lookup(pt_table, city)
        cities.append(
            {
                "codigo": code,
                "municipio": city.municipality,
                "uf": city.uf,
                "regiao": city.region,
                "entrevistas": interviews["2026-07"][code],
                "ondas": sum(code in interviews[wave] for wave in WAVES),
                "eleitores": matched.get(code),
                "bolsonaro_2022_pct": (
                    round(100 * pl / (pl + pt), 2) if pl and pt else None
                ),
                "capital": int(code in CAPITAIS),
            }
        )
    OUT_SITE_CITIES.write_text(
        json.dumps(cities, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    # A mesma lista como script clássico: o dossiê precisa abrir também em
    # file://, onde fetch() de JSON local é bloqueado pela política de origem.
    OUT_SITE_CITIES_JS.write_text(
        "window.__DATAFOLHA_MUNICIPIOS__ = "
        + json.dumps(cities, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    print(f"OK: {OUT_JSON.relative_to(ROOT)}")
    print(f"OK: {OUT_SITE_CITIES.relative_to(ROOT)}")
    print(f"OK: {OUT_SITE_CITIES_JS.relative_to(ROOT)}")
    print(f"OK: {OUT_MAP_CSV.relative_to(ROOT)}")
    print(
        f"Painel fixo: {len(fixed_codes)} municípios, "
        f'{output["painel_municipal"]["share_entrevistas_no_painel_fixo_pct"]}% da amostra; '
        f'cobertura eleitoral {output["cobertura_eleitoral"]["share_eleitorado_coberto_pct"]}%.'
    )


if __name__ == "__main__":
    main()
