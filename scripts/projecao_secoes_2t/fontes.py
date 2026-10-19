"""Extratos auditáveis: cada linha é uma seção/BU, nunca uma pessoa."""

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from apuracao_2026.secoes_2022 import normalizar_local
from apuracao_2026.secoes_base import montar

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/outputs/projecao_secoes_2t"
KEYS = ["uf", "mun", "zona", "secao"]
PARTS = ["direita", "esquerda", "outros", "bn", "ausentes"]
VERSION = 1


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda: file.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)
    if text.count("\n") >= 950:
        text = json.dumps(
            data, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        )
    path.write_text(text + "\n")


def keys(frame):
    frame = frame.rename(
        columns={
            "SG_UF": "uf",
            "CD_MUNICIPIO": "mun",
            "NR_ZONA": "zona",
            "NR_SECAO": "secao",
            "NR_TURNO": "turno",
        }
    )
    frame["uf"] = frame.uf.str.upper()
    frame["mun"] = frame.mun.astype(str).str.zfill(5)
    for name in ("zona", "secao", "turno"):
        frame[name] = frame[name].astype(int)
    return frame


def chunks(path, suffix, columns):
    with zipfile.ZipFile(path) as archive:
        member = next(name for name in archive.namelist() if name.endswith(suffix))
        with archive.open(member) as file:
            yield from pd.read_csv(
                file,
                sep=";",
                encoding="latin-1",
                usecols=columns,
                dtype=str,
                chunksize=500_000,
            )


def historical(year):
    votes = ROOT / f"data/raw/tse_resultados/votacao_secao_{year}_BR.zip"
    if year == 2022:
        votes = (
            ROOT
            / "data/raw/tse_resultados/votacao_secao_2022/votacao_secao_2022_BR.zip"
        )
    details = ROOT / f"data/raw/tse_resultados/detalhe_votacao_secao_{year}.zip"
    cache = OUT / f"secoes_{year}.csv.gz"
    meta_path = OUT / f"secoes_{year}.json"
    source = {"version": VERSION, "votos": sha(votes), "detalhe": sha(details)}
    if cache.exists() and meta_path.exists():
        meta = json.loads(meta_path.read_text())
        if meta["source"] == source and meta["sha256"] == sha(cache):
            return pd.read_csv(cache, dtype={"uf": str, "mun": str}), meta
    cols = ["SG_UF", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "NR_TURNO", "CD_CARGO"]
    parts = []
    for block in chunks(
        votes, f"votacao_secao_{year}_BR.csv", [*cols, "NR_VOTAVEL", "QT_VOTOS"]
    ):
        block = keys(block[block.CD_CARGO == "1"].copy())
        number = block.NR_VOTAVEL.astype(int)
        block["grupo"] = np.select(
            [
                number == (17 if year == 2018 else 22),
                number == 13,
                number.isin([95, 96]),
            ],
            ["direita", "esquerda", "bn"],
            default="outros",
        )
        block["votos"] = block.QT_VOTOS.astype(int)
        parts.append(block.groupby([*KEYS, "turno", "grupo"]).votos.sum())
    ballot = (
        pd.concat(parts)
        .groupby(level=[0, 1, 2, 3, 4, 5])
        .sum()
        .unstack("grupo", fill_value=0)
        .reset_index()
    )
    parts = []
    mapping = {
        "QT_APTOS": "aptos",
        "QT_COMPARECIMENTO": "presentes",
        "QT_VOTOS_BRANCOS": "brancos",
        "QT_VOTOS_NULOS": "nulos",
        "QT_VOTOS_NOMINAIS": "nominais",
        "NM_LOCAL_VOTACAO": "local",
    }
    for block in chunks(
        details, f"detalhe_votacao_secao_{year}_BR.csv", cols + list(mapping)
    ):
        block = keys(block[block.CD_CARGO == "1"].copy()).rename(columns=mapping)
        for name in mapping.values():
            if name != "local":
                block[name] = block[name].astype(int)
        parts.append(block[[*KEYS, "turno", *mapping.values()]])
    detail = pd.concat(parts, ignore_index=True)
    if detail.duplicated([*KEYS, "turno"]).any():
        raise ValueError("Detalhes duplicados por seção e turno")
    data = detail.merge(
        ballot.drop(columns="bn", errors="ignore"),
        on=[*KEYS, "turno"],
        how="left",
        validate="one_to_one",
    )
    for name in PARTS[:3]:
        data[name] = data[name].fillna(0).astype(int)
    data["bn"] = data.brancos + data.nulos
    data["ausentes"] = data.aptos - data.presentes
    data["local"] = data.local.fillna("").map(normalizar_local)
    valid = (
        (data.aptos > 0)
        & (data[PARTS].min(axis=1) >= 0)
        & (data[PARTS].sum(axis=1) == data.aptos)
        & (data[PARTS[:3]].sum(axis=1) == data.nominais)
    )
    invalid = data[~valid]
    data = data[valid].copy()
    one, two = [data[data.turno == turn].drop(columns="turno") for turn in (1, 2)]
    paired = one.merge(two, on=KEYS, suffixes=("_1", "_2"), validate="one_to_one")
    stable = (paired.local_1 != "") & (paired.local_1 == paired.local_2)
    excluded_locations = int((~stable).sum())
    paired = paired[stable].reset_index(drop=True)
    OUT.mkdir(parents=True, exist_ok=True)
    paired.to_csv(cache, index=False, compression={"method": "gzip", "mtime": 0})
    meta = {
        "source": source,
        "year": year,
        "arquivo": str(cache.relative_to(ROOT)),
        "sha256": sha(cache),
        "n_secoes_pareadas": len(paired),
        "locais_divergentes": excluded_locations,
        "linhas_invalidas": len(invalid),
        "linhas_sem_par": len(one) + len(two) - 2 * (len(paired) + excluded_locations),
        "aptos_iguais": int((paired.aptos_1 == paired.aptos_2).sum()),
        "totais_pareados": {
            f"{part}_{turn}": int(paired[f"{part}_{turn}"].sum())
            for turn in (1, 2)
            for part in ["aptos", *PARTS]
        },
        "urls": [
            f"https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_secao/votacao_secao_{year}_BR.zip",
            f"https://cdn.tse.jus.br/estatistica/sead/odsele/detalhe_votacao_secao/detalhe_votacao_secao_{year}.zip",
        ],
    }
    save_json(meta_path, meta)
    return paired, meta


def current(refresh=False):
    cache, meta_path = OUT / "secoes_2026.csv.gz", OUT / "secoes_2026.json"
    if cache.exists() and meta_path.exists() and not refresh:
        meta = json.loads(meta_path.read_text())
        if meta["sha256"] != sha(cache):
            raise ValueError("Extrato de 2026 mudou: use --refresh")
        return pd.read_csv(cache, dtype={"uf": str, "mun": str}), meta
    base = montar(
        ROOT / "apuracao/data/secoes_2026.sqlite",
        ROOT / "data/outputs/locais_votacao_2026.sqlite",
        ROOT / "apuracao/data/apuracao.sqlite",
    )
    data = base.secoes
    out = data[
        [
            *KEYS,
            "local",
            "aptos",
            "comparecimento",
            "v22",
            "v13",
            "validos",
            "brancos",
            "nulos",
        ]
    ].copy()
    out["uf"] = out.uf.str.upper()
    out["local_1"] = out.local.fillna("").map(normalizar_local)
    out["outros_1"] = out.validos - out.v22 - out.v13
    out["bn_1"] = out.brancos + out.nulos
    out["ausentes_1"] = out.aptos - out.comparecimento
    out = out.rename(
        columns={"aptos": "aptos_1", "v22": "direita_1", "v13": "esquerda_1"}
    )[[*KEYS, "local_1", "aptos_1", *[f"{p}_1" for p in PARTS]]]
    if (out[[f"{p}_1" for p in PARTS]].sum(axis=1) != out.aptos_1).any():
        raise ValueError("Partição de 2026 não conserva aptos")
    out.to_csv(cache, index=False, compression={"method": "gzip", "mtime": 0})
    official = json.loads(
        (ROOT / "analysis/apuracao_2026/dados/presidente.json").read_text()
    )
    checks = []
    for uf in official["ufs"]:
        local = out[out.uf == uf["uf"]]
        expected = {
            "aptos_1": uf["eleitores"],
            "direita_1": uf["votos"]["flavio"],
            "esquerda_1": uf["votos"]["lula"],
            "outros_1": uf["votos"]["terceiros"],
            "bn_1": uf["brancos"] + uf["nulos"],
            "ausentes_1": uf["abstencao"],
        }
        checks.append(
            {
                "uf": uf["uf"],
                "residuos": {k: int(local[k].sum()) - v for k, v in expected.items()},
            }
        )
    meta = {
        "arquivo": str(cache.relative_to(ROOT)),
        "sha256": sha(cache),
        "n_secoes": len(out),
        "n_excluidas": len(base.excluidas),
        "conferencia_uf": checks,
        "source": "apuracao/data/secoes_2026.sqlite, transação de leitura; seleção auditada por apuracao_2026.secoes_base.montar",
        "official_sha256": sha(ROOT / "analysis/apuracao_2026/dados/presidente.json"),
    }
    save_json(meta_path, meta)
    return out, meta


def complete_current(frame):
    """Resíduos municipais explícitos, sem inventar boletins ou repartir votos."""
    official = json.loads(
        (ROOT / "analysis/apuracao_2026/dados/presidente.json").read_text()
    )
    data = frame[frame.uf != "ZZ"].copy()
    data["unidade"] = "secao"
    cols = ["aptos_1", *[f"{p}_1" for p in PARTS]]
    observed = data.groupby(["uf", "mun"])[cols].sum()
    rows = []
    for values in official["municipios"]["linhas"]:
        row = dict(zip(official["municipios"]["colunas"], values, strict=True))
        if row["uf"] == "ZZ":
            continue
        key = (row["uf"], row["cd_tse"])
        target = np.array(
            [
                row["eleitores"],
                row["flavio"],
                row["lula"],
                row["terceiros"],
                row["brancos"] + row["nulos"],
                row["eleitores"] - row["comparecimento"],
            ]
        )
        local = (
            observed.loc[key].to_numpy()
            if key in observed.index
            else np.zeros(len(cols), int)
        )
        residual = target - local
        if (residual < 0).any():
            raise ValueError(f"Resíduo negativo em {key}: {residual}")
        if residual[0] > 0:
            if residual[1:].sum() != residual[0]:
                raise ValueError(f"Resíduo não conserva aptos em {key}")
            rows.append(
                {
                    "uf": key[0],
                    "mun": key[1],
                    "zona": 0,
                    "secao": 0,
                    "local_1": "",
                    "unidade": "residuo_municipal",
                    **dict(zip(cols, residual, strict=True)),
                }
            )
    result = pd.concat([data, pd.DataFrame(rows)], ignore_index=True)
    expected = sum(u["eleitores"] for u in official["ufs"] if u["uf"] != "ZZ")
    if result.aptos_1.sum() != expected:
        raise ValueError("Eleitorado nacional não confere após complemento municipal")
    return result, {
        "secoes": len(data),
        "municipios_com_residuo": len(rows),
        "residuos": [
            {"uf": row["uf"], "municipio_tse": row["mun"], "aptos": int(row["aptos_1"])}
            for row in rows
        ],
        "aptos_em_secoes": int(data.aptos_1.sum()),
        "aptos_sem_secao": int(sum(r["aptos_1"] for r in rows)),
        "aptos": expected,
        "cobertura_secao_pct": 100 * data.aptos_1.sum() / expected,
        "exterior": "Separado do modelo nacional: pesquisas/PNAD não o cobrem; 423 aptos sem classificação na totalização externa.",
    }
