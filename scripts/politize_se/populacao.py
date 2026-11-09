"""População 16+: Censo observado, estimativa sintética e PNAD somente por UF.

A estimativa municipal mantém a estrutura de 2022: não é uma projeção oficial por
idade, tampouco uma estimativa direta municipal da PNAD. O cadastro não é residência.
"""

from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict

from .perfil import FAIXAS
from .populacao_fontes import RAW, ROOT, UFS, hash_arquivo, ler

OUT = ROOT / "docs/assets/politize_se/populacao"
PERFIL = ROOT / "docs/assets/politize_se/perfil"
DADOS = ROOT / "docs/assets/politize_se/dados"
# Classes mutuamente exclusivas, exatamente compatíveis com as faixas do cadastro.
GRUPOS = [
    [6573, 6574],
    [6575, 6576, 93087],
    [93088, 93089],
    [93090, 93091],
    [93092, 93093],
    [93094],
    [93095],
    [93096, 93097],
    [93098, 49108],
    [49109, 60040, 60041, 6653],
]


def numero(v):
    if v == "-":  # SIDRA: zero absoluto; '..' e '...' permanecem indisponíveis
        return 0
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def proporcao(a, b):
    return round(100 * a / b, 6) if a is not None and b is not None and b > 0 else None


def censo(uf):
    celulas = defaultdict(dict)
    for r in ler(RAW / f"censo_{uf}.json")[0]["resultados"]:
        cls = {c["id"]: next(iter(c["categoria"])) for c in r["classificacoes"]}
        sexo, idade = int(cls["2"]), int(cls["287"])
        for s in r["series"]:
            celulas[s["localidade"]["id"]][sexo, idade] = numero(s["serie"]["2022"])
    out = {}
    for code, d in celulas.items():

        def soma(sexos, ids, d=d):
            vals = [d.get((s, i)) for s in sexos for i in ids]
            return sum(vals) if all(v is not None for v in vals) else None

        vetor = [[soma([s], ids) for s in [4, 5]] for ids in GRUPOS]
        total = soma([4, 5], [100362])
        p16 = soma([4, 5], [i for g in GRUPOS for i in g])
        if p16 is not None and total is not None:
            menores = soma([4, 5], [93070, 93084, 93085, 6572])
            assert menores is not None and menores + p16 == total, code
        out[code] = {"total": total, "p16": p16, "vetor": vetor}
    return out


def perfil(uf):
    d = json.loads(gzip.decompress((PERFIL / f"{uf}.json.gz").read_bytes()))
    muns = defaultdict(lambda: [0] * 33)
    for key, (_, v) in d["secoes"].items():
        mun = key.split("-")[0]
        muns[mun] = [a + b for a, b in zip(muns[mun], v, strict=True)]
    assert sum(map(sum, muns.values())) == d["meta"]["eleitores"]
    return muns


def coordenada(m, code):
    """Índice municipal existente; faltantes usam ponto interno da malha IBGE."""
    if m["lat"] is not None and m["lon"] is not None:
        return m["lat"], m["lon"], "Índice municipal do Politize-se", None
    from shapely.geometry import shape

    path = ROOT / f"apuracao/public/geo/mun/{m['uf']}.geojson"
    for feature in ler(path)["features"]:
        if feature["properties"].get("codarea") == code:
            point = shape(feature["geometry"]).representative_point()
            return (
                point.y,
                point.x,
                "Ponto interno da malha municipal IBGE; não é a sede",
                path,
            )
    return None, None, "Sem coordenada", None


def pnads():
    """Lê em lotes o trimestre local, nunca cria estimativas municipais da amostra."""
    import pyarrow.csv as pc

    p = ROOT / "data/outputs/base_labeled.csv"
    with p.open() as f:
        cols = next(csv.reader(f))
    keys = ["Ano", "Trimestre", "UF", "V2009", "V2007", "V1028"]
    names = [next(c for c in cols if c.split("__")[0] == k) for k in keys]
    sums = defaultdict(lambda: [0.0] * 5)
    for batch in pc.open_csv(
        p,
        read_options=pc.ReadOptions(block_size=8 * 1024 * 1024),
        convert_options=pc.ConvertOptions(include_columns=names),
    ):
        for ano, tri, uf, idade, sexo, peso in zip(
            *(batch[c].to_pylist() for c in names), strict=True
        ):
            if idade is None or peso is None or peso <= 0:
                raise ValueError("PNAD sem idade/peso válido")
            k = (int(ano), int(tri), UFS[str(uf)])
            s = sums[k]
            s[0] += peso
            if idade >= 16:
                s[1] += peso
                s[2] += peso * (sexo == 2)
                s[3] += peso * (idade <= 24)
                s[4] += peso * (idade >= 60)
    periodos = {(a, t) for a, t, _ in sums}
    if len(periodos) != 1:
        raise ValueError(f"PNAD precisa de um trimestre: {periodos}")
    ano, tri = next(iter(periodos))
    return {
        "ano": ano,
        "trimestre": tri,
        "peso": "V1028",
        "fonte": str(p.relative_to(ROOT)),
        "sha256": hash_arquivo(p),
        "universo": "Moradores de domicílios particulares permanentes; estimativa amostral estadual.",
        "ufs": {
            u: dict(
                zip(
                    ["total", "p16", "mulheres16", "jovens16_24", "idosos60"],
                    [round(v, 3) for v in s],
                    strict=True,
                )
            )
            for (_, _, u), s in sums.items()
        },
    }


def publicar():
    OUT.mkdir(parents=True, exist_ok=True)
    estimativa = ler(RAW / "estimativa.json")[0]["resultados"][0]["series"]
    anos = {a for s in estimativa for a in s["serie"]}
    assert len(anos) == 1
    ano = int(next(iter(anos)))
    pops = {s["localidade"]["id"]: numero(s["serie"][str(ano)]) for s in estimativa}
    ind = ler(DADOS / "indice.json")
    refs = [
        dict(zip(ind["municipios"]["colunas"], r, strict=True))
        for r in ind["municipios"]["linhas"]
        if r[0] != "ZZ"
    ]
    todos, fontes = [], []
    for uf in UFS.values():
        cen, per = censo(uf), perfil(uf)
        ctx = ler(ROOT / f"docs/assets/politize_se_mapa/contexto/{uf}.json")[
            "municipios"
        ]
        for m in (r for r in refs if r["uf"] == uf):
            mun = str(m["mun_tse"]).zfill(5)
            code = str(ctx.get(mun, {}).get("ibge") or "")
            c = cen.get(code)
            v = per.get(mun)
            total = sum(v) if v else None
            t = ler(DADOS / f"mun/{uf}/{mun}.json")["totais"]
            lat, lon, coord_fonte, coord_path = coordenada(m, code)
            if coord_path:
                fontes.append(
                    {
                        "arquivo": str(coord_path.relative_to(ROOT)),
                        "sha256": hash_arquivo(coord_path),
                    }
                )
            recente = pops.get(code)
            est16 = (
                recente * c["p16"] / c["total"]
                if c and c["p16"] and c["total"] and recente
                else None
            )
            feminino = sum(v[1::3]) if v else None
            jovens = sum(v[:6]) if v else None
            idosos = sum(v[18:30]) if v else None
            row = {
                "uf": uf,
                "mun": mun,
                "ibge": code or None,
                "nome": m["nome"],
                "lat": lat,
                "lon": lon,
                "coordenada_fonte": coord_fonte,
                "pop_total_recente": recente,
                "censo_total": c["total"] if c else None,
                "censo16": c["p16"] if c else None,
                "estimativa16": round(est16, 3) if est16 is not None else None,
                "eleitorado": total,
                "eleitorado_bu1": t["aptos1"],
                "eleitorado_bu2": t["aptos2"],
                "comparecimento1": t["comp1"] if t["n_1t"] else None,
                "comparecimento2": t["comp2"] if t["n_bu2"] else None,
                "secoes": t["n_secoes"],
                "bu1": t["n_1t"],
                "bu2": t["n_bu2"],
                "censo_idade_sexo": c["vetor"] if c else None,
                "tse_idade_sexo": v,
                "mulheres_tse_pct": proporcao(feminino, total),
                "jovens_tse_pct": proporcao(jovens, total),
                "idosos_tse_pct": proporcao(idosos, total),
                "nota": (
                    None
                    if est16 is not None
                    else "Sem correspondência comparável no Censo 2022 ou na estimativa recente; não imputado."
                ),
            }
            for key, idx in [
                ("mulheres", None),
                ("jovens", [0, 1]),
                ("idosos", [6, 7, 8, 9]),
            ]:
                count = (
                    (
                        sum(a[1] for a in c["vetor"])
                        if idx is None
                        else sum(sum(c["vetor"][i]) for i in idx)
                    )
                    if c and c["p16"]
                    else None
                )
                cp = proporcao(count, c["p16"] if c else None)
                row[key + "_censo_pct"] = cp
                row[key + "_dif_pp"] = (
                    round(row[key + "_tse_pct"] - cp, 6)
                    if cp is not None and row[key + "_tse_pct"] is not None
                    else None
                )
            for key in ["eleitorado", "comparecimento1", "comparecimento2"]:
                row[key + "_por100"] = proporcao(row[key], row["estimativa16"])
                row[key + "_saldo"] = (
                    round(row[key] - row["estimativa16"], 3)
                    if row[key] is not None and row["estimativa16"] is not None
                    else None
                )
            todos.append(row)
        for path in [
            PERFIL / f"{uf}.json.gz",
            ROOT / f"docs/assets/politize_se_mapa/contexto/{uf}.json",
        ]:
            fontes.append(
                {"arquivo": str(path.relative_to(ROOT)), "sha256": hash_arquivo(path)}
            )
    pnad = pnads()
    fontes += [
        {
            "arquivo": str(
                p.with_name(p.name.replace(".fonte.json", ".json")).relative_to(ROOT)
            ),
            **ler(p),
        }
        for p in sorted(RAW.glob("*.fonte.json"))
    ]
    # Hash dos próprios totais reutilizados: prova o estado do acervo sem reabrir bancos vivos.
    eleicao_hash = (
        __import__("hashlib")
        .sha256(
            json.dumps(
                [
                    {
                        k: r[k]
                        for k in [
                            "uf",
                            "mun",
                            "eleitorado_bu1",
                            "eleitorado_bu2",
                            "comparecimento1",
                            "comparecimento2",
                            "secoes",
                            "bu1",
                            "bu2",
                        ]
                    }
                    for r in todos
                ],
                sort_keys=True,
            ).encode()
        )
        .hexdigest()
    )
    meta = {
        "formato": 1,
        "ano_estimativa": ano,
        "ano_censo": 2022,
        "eleicao": 2026,
        "faixas": FAIXAS,
        "sexos_censo": ["Homens", "Mulheres"],
        "sexos_tse": ["Masculino", "Feminino", "Não informado"],
        "metodo": "Estimativa municipal 16+ = população total IBGE recente × proporção 16+ do Censo 2022. Estrutura etária e sexual constante: estimativa sintética Arvor, não projeção oficial por idade. PNAD é referência estadual independente e não é distribuída pelos municípios.",
        "limites": [
            "População residente e domicílio eleitoral são universos distintos. Diferença não demonstra irregularidade.",
            "Cadastro de 2026 e Censo de 2022 têm datas distintas. Migração, vínculos eleitorais, cobertura censitária e mudanças de limites podem contribuir; o painel não identifica a causa.",
            "Comparecimento soma os boletins disponíveis; cobertura incompleta representa um mínimo observado, não zero nas seções ausentes.",
            "Sem população do entorno de cada escola: o município inteiro aparece uma única vez no mapa.",
            "Razões usam todos os inscritos; sexo e idade não informados permanecem no denominador do TSE.",
        ],
        "pnad": pnad,
        "fontes": fontes,
        "boletins_gerado_em": ind["gerado_em"],
        "boletins_totais_sha256": eleicao_hash,
        "perfil_fonte": ler(PERFIL / "indice.json"),
        "cobertura": {
            "municipios": len(todos),
            "com_estimativa16": sum(r["estimativa16"] is not None for r in todos),
            "sem_estimativa": [
                {k: r[k] for k in ["uf", "mun", "ibge", "nome", "nota"]}
                for r in todos
                if r["estimativa16"] is None
            ],
        },
    }
    for name, obj in [
        ("municipios.json", {"municipios": todos}),
        ("indice.json", meta),
    ]:
        (OUT / name).write_text(
            json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            + "\n"
        )
    simples = [k for k in todos[0] if not k.endswith("idade_sexo")]
    with (OUT / "municipios.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(
            f, fieldnames=simples, extrasaction="ignore", lineterminator="\n"
        )
        w.writeheader()
        w.writerows(todos)
    print(json.dumps(meta["cobertura"], ensure_ascii=False, indent=2))
