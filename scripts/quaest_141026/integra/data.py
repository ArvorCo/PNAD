"""Dados conferidos e contas com denominadores explícitos; não imputa abstenção."""

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "analysis/quaest_141026/integra"
PUBLIC = ROOT / "docs/assets/quaest_14102026_integra"


def read(path):
    return json.loads(path.read_text())


def topics():
    return [read(DATA / "temas" / f"{key}.json") for key in read(DATA / "ordem.json")]


def official():
    source = ROOT / "analysis/apuracao_2026/dados/presidente.json"
    raw = read(source)
    ufs = [row for row in raw["ufs"] if row["uf"] != "ZZ"]
    counts = {
        key: sum(row[key] for row in ufs)
        for key in (
            "eleitores",
            "comparecimento",
            "abstencao",
            "validos",
            "brancos",
            "nulos",
        )
    }
    counts.update(
        {key: sum(row["votos"][key] for row in ufs) for key in ("flavio", "lula")}
    )
    denominator = counts["eleitores"]
    shares = {key: 100 * value / denominator for key, value in counts.items()}
    shares["terceiros"] = shares["validos"] - shares["flavio"] - shares["lula"]
    shares["sem_voto_valido"] = (
        shares["abstencao"] + shares["brancos"] + shares["nulos"]
    )
    return {
        "universo": "Eleitorado no Brasil, sem exterior; eleição de 04/10/2026",
        "contagens": counts,
        "pct_eleitorado": shares,
        "fonte": str(source.relative_to(ROOT)),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "snapshot": raw["meta"]["versao_nacional_snapshot_id"],
    }


def build():
    themes = topics()
    by_id = {t["id"]: t for t in themes}
    tr = by_id["transferencia"]
    group = tr["linhas"]["Branco/nulo/não foi votar"]
    mass = tr["pesos_lembrados_pct"]["Branco/nulo/não foi votar"]
    contributions = {
        key: mass * value / 100
        for key, value in zip(
            ("flavio", "lula", "indecisos", "sem_escolha"), group, strict=True
        )
    }
    published = by_id["estimulada"]["valores"]
    base_f = published["Flávio"]
    base_l = published["Lula"]
    stress = []
    for conversion in (0, 25, 50, 75, 100):
        remaining_f = base_f - contributions["flavio"] * (1 - conversion / 100)
        remaining_l = base_l - contributions["lula"] * (1 - conversion / 100)
        stress.append(
            {
                "conversao_relativa_pct": conversion,
                "flavio_total": remaining_f,
                "lula_total": remaining_l,
                "flavio_validos": 100 * remaining_f / (remaining_f + remaining_l),
                "lula_validos": 100 * remaining_l / (remaining_f + remaining_l),
            }
        )
    interest = by_id["estimulada"]["recortes"]["Interesse"]
    scenarios = [
        {
            "grupo": "Total publicado",
            "flavio": base_f,
            "lula": base_l,
            "soma": base_f + base_l,
            "flavio_validos": 100 * base_f / (base_f + base_l),
        }
    ]
    for name, row in interest["linhas"].items():
        scenarios.append(
            {
                "grupo": name,
                "flavio": row[0],
                "lula": row[1],
                "soma": row[0] + row[1],
                "flavio_validos": 100 * row[0] / (row[0] + row[1]),
            }
        )
    proposals = [
        {
            "proposta": name,
            "apoio_apos_apresentacao": row[0] + row[1],
            "oposicao_apos_apresentacao": row[2] + row[3],
            "conhecimento_declarado": row[0] + row[3],
            "ns_nr": row[4],
        }
        for name, row in by_id["propostas"]["linhas"].items()
    ]
    return {
        "documento": read(DATA / "documento.json"),
        "temas": themes,
        "catalogo": read(DATA / "paginas.json"),
        "urna": official(),
        "transferencia": {
            "grupo_pct": mass,
            "contribuicoes_total_pp": contributions,
            "vantagem_lula_no_grupo_pp": group[1] - group[0],
            "vantagem_lula_total_pp": contributions["lula"] - contributions["flavio"],
            "matriz_completa": False,
            "ausentes_separados": False,
            "cenario_conversao": stress,
            "nota": "Cenário: só o voto válido declarado pelo grupo misto é reduzido proporcionalmente; restante do topline fixo. Não é modelo de comparecimento, correção da pesquisa nem abstenção identificada.",
        },
        "eleitor_provavel": {
            "regra_publicada": False,
            "universo_declarado": "Eleitores brasileiros com 16 anos ou mais",
            "documentos_examinados": [
                "PDF pp. 2–4, 17–29, 117–118, 129; catálogo das 152 páginas",
                "Transcrição arquivada do registro BR-08729/2026",
            ],
            "limite": "Não se localizou regra, escore, limiar, taxa prevista ou validação de eleitor provável nos documentos examinados. Isso não prova ausência de tratamentos internos não divulgados. Questionário integral e microdados continuam pendentes.",
            "sensibilidades_por_interesse": scenarios,
        },
        "propostas": proposals,
    }


def write():
    data = build()
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "referencias.json").write_bytes((DATA / "referencias.json").read_bytes())
    for theme in data["temas"]:
        (PUBLIC / (theme["id"] + ".json")).write_text(
            json.dumps(theme, ensure_ascii=False, indent=2) + "\n"
        )
    # Catálogo separado: o payload de contas não duplica as 152 renderizações.
    catalog = data.pop("catalogo")
    themes = data.pop("temas")
    data["temas"] = [
        {
            "id": t["id"],
            "titulo": t["titulo"],
            "arquivo": t["id"] + ".json",
            "paginas": t["paginas"],
        }
        for t in themes
    ]
    (PUBLIC / "auditoria.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    )
    (PUBLIC / "paginas.json").write_text(
        "[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in catalog) + "\n]\n"
    )
    with (PUBLIC / "paginas.csv").open("w", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(["pagina", "tema", "titulo", "imagem", "sha256"])
        writer.writerows(
            [r[k] for k in ("pagina", "tema", "titulo", "imagem", "sha256")]
            for r in catalog
        )
    return build()
