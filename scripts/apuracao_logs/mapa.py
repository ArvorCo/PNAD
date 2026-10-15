"""Integra os registros operacionais ao mapa, sem alterar a pontuação histórica."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLITIZE = ROOT / "docs/assets/politize/dados"
LOGS = ROOT / "analysis/apuracao_2026/logs_urnas/sinalizadas.json"
INDICE = ROOT / "docs/assets/logs_urnas_2026/indice.json"


def tabela(obj):
    return [dict(zip(obj["colunas"], row, strict=True)) for row in obj["linhas"]]


def integrar(obj: dict) -> dict:
    if not LOGS.exists() or not INDICE.exists():
        return obj
    indice = json.loads(INDICE.read_text())
    sinais = json.loads(LOGS.read_text())
    complemento_path = INDICE.parent / "complementos.json"
    complementos = (
        json.loads(complemento_path.read_text()) if complemento_path.exists() else {}
    )
    linhas = [dict(zip(obj["colunas"], row, strict=True)) for row in obj["linhas"]]
    antigos = {(r["uf"], r["zona"], r["secao"]): r for r in linhas}
    for r in linhas:
        r["originais"] = True
        r["logs"] = []
        r["coord_fonte"] = "cadastro" if r["uf"] != "ZZ" else "cidade"
    zonas, muns = {}, {}
    for log in sinais:
        uf, z, s, m = log["uf"], log["zona"], log["secao"], log["mun"]
        chave = (uf, z, s)
        if chave not in antigos:
            if (uf, z) not in zonas:
                path = POLITIZE / "zona" / uf / f"{z}.json"
                zonas[(uf, z)] = (
                    {
                        r["secao"]: r
                        for r in tabela(json.loads(path.read_text())["secoes"])
                    }
                    if path.exists()
                    else {}
                )
            sec = zonas[(uf, z)].get(s)
            suplemento = complementos.get(f"{uf}-{z}-{s}")
            if not sec and suplemento:
                sec = {**suplemento, "mun_tse": m}
            if not sec or str(sec["mun_tse"]) != m:
                raise ValueError(
                    f"Seção sinalizada sem vínculo cadastral: {uf}-{z}-{s}"
                )
            if (uf, m) not in muns:
                path = POLITIZE / "mun" / uf / f"{m}.json"
                if not path.exists():
                    raise ValueError(f"Município sinalizado sem cadastro: {uf}-{m}")
                cad = json.loads(path.read_text())
                muns[(uf, m)] = (
                    cad["nome"],
                    {r["local_id"]: r for r in tabela(cad["locais"])},
                )
            nome, locais = muns[(uf, m)]
            loc = locais.get(sec["local_id"], {})
            r = {
                "uf": uf,
                "municipio": nome,
                "zona": z,
                "secao": s,
                "local_id": sec["local_id"],
                "local": sec.get("local")
                or f"Local {sec['local_id'].rsplit('-', 1)[-1]}",
                "endereco": loc.get("endereco"),
                "bairro": loc.get("bairro"),
                "cep": loc.get("cep"),
                "lat": loc.get("lat"),
                "lon": loc.get("lon"),
                "nivel": "logs",
                "pontuacao": None,
                "criterios": "",
                "explicacao": None,
                "risco": None,
                "aptos": sec.get("aptos"),
                "flavio_pct": None,
                "lula_pct": None,
                "originais": False,
                "coord_fonte": loc.get("coord_fonte"),
            }
            antigos[chave] = r
            linhas.append(r)
        antigos[chave]["logs"] = log["sinais"]
        antigos[chave]["tempo_voto"] = (
            log["voto_mediana"] if log["elegivel_tempo"] else None
        )
        for campo in ("processo_mediana", "cadencia_mediana"):
            antigos[chave][campo] = log.get(campo) if log["elegivel_tempo"] else None
    # O capítulo histórico não tinha coordenadas do exterior. O Politize tem
    # centros de cidade, explicitamente aproximados, e nunca endereço inventado.
    for row in linhas:
        if row["uf"] != "ZZ" or row.get("lat") is not None:
            continue
        mun = row["local_id"].split("-")[1]
        path = POLITIZE / "mun" / "ZZ" / f"{mun}.json"
        if not path.exists():
            continue
        cad = json.loads(path.read_text())
        local = next(
            (
                loc
                for loc in tabela(cad["locais"])
                if loc["local_id"] == row["local_id"]
            ),
            None,
        )
        if local:
            row["lat"], row["lon"] = local.get("lat"), local.get("lon")
            row["coord_fonte"] = local.get("coord_fonte")
    colunas = [
        *obj["colunas"],
        "originais",
        "logs",
        "tempo_voto",
        "coord_fonte",
        "processo_mediana",
        "cadencia_mediana",
    ]
    obj["colunas"] = colunas
    obj["linhas"] = [[r.get(c) for c in colunas] for r in linhas]
    obj["logs"] = {
        "criterios": indice["criterios"],
        "cobertura": indice["cobertura"],
        "gerado_em": indice["gerado_em"],
    }
    obj["resumo"]["secoes_originais"] = obj["resumo"]["secoes"]
    obj["resumo"]["secoes"] = len(linhas)
    obj["titulo"] = (
        "Mapa de fiscais: critérios históricos e registros operacionais dos logs"
    )
    return obj


def publicar_recortes(obj: dict, destino: Path):
    """A consulta local baixa só a UF escolhida; o histórico abre sem o país inteiro."""
    cols = {k: i for i, k in enumerate(obj["colunas"])}
    partes, municipios = defaultdict(list), defaultdict(set)
    for row in obj["linhas"]:
        uf = row[cols["uf"]]
        partes[uf].append(row)
        municipios[uf].add(row[cols["municipio"]])
    meta = {k: v for k, v in obj.items() if k != "linhas"}
    meta["partes"] = {
        uf: {
            "arquivo": f"uf/{uf}.json",
            "secoes": len(rows),
            "municipios": sorted(municipios[uf]),
        }
        for uf, rows in partes.items()
    }
    meta["niveis"] = dict(Counter(r[cols["nivel"]] for r in obj["linhas"]))

    def salvar(nome, dados):
        path = destino / nome
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dados, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    salvar("indice.json", meta)
    original = cols.get("originais")
    salvar(
        "originais.json",
        {"linhas": [r for r in obj["linhas"] if original is None or r[original]]},
    )
    for uf, rows in partes.items():
        salvar(f"uf/{uf}.json", {"linhas": rows})
