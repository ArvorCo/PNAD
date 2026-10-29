"""Registros estaduais Sinesp 2025; índice descritivo, nunca risco local."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import openpyxl
from politize_se.perfil import gravar, sha256

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/originals/sinesp_2026"
OUT = ROOT / "docs/assets/politize_se/crimes/dados.json"
UF_CODES = dict(
    zip(
        [
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "21",
            "22",
            "23",
            "24",
            "25",
            "26",
            "27",
            "28",
            "29",
            "31",
            "32",
            "33",
            "35",
            "41",
            "42",
            "43",
            "50",
            "51",
            "52",
            "53",
        ],
        [
            "RO",
            "AC",
            "AM",
            "RR",
            "PA",
            "AP",
            "TO",
            "MA",
            "PI",
            "CE",
            "RN",
            "PB",
            "PE",
            "AL",
            "SE",
            "BA",
            "MG",
            "ES",
            "RJ",
            "SP",
            "PR",
            "SC",
            "RS",
            "MS",
            "MT",
            "GO",
            "DF",
        ],
        strict=True,
    )
)
METRICAS = {
    "homicidio_doloso": ("Homicídio doloso", "total_vitima", "vítimas"),
    "trafico": ("Tráfico de drogas", "total", "ocorrências"),
    "roubo_veiculo": ("Roubo de veículo", "total", "ocorrências"),
    "furto_veiculo": ("Furto de veículo", "total", "ocorrências"),
    "estupro": ("Estupro", "total_vitima", "vítimas"),
    "estupro_vulneravel": ("Estupro de vulnerável", "total_vitima", "vítimas"),
    "roubo_carga": ("Roubo de carga", "total", "ocorrências"),
    "roubo_banco": ("Roubo a instituição financeira", "total", "ocorrências"),
    "feminicidio": ("Feminicídio", "total_vitima", "vítimas"),
}
COMPONENTES = [
    "homicidio_doloso",
    "trafico",
    "roubo_veiculo",
    "furto_veiculo",
    "estupro",
]
NOTAS = "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023"


def percentil(valor: float, valores: list[float]) -> float:
    """Posto médio, empatados recebem a mesma nota. Extremos 0–100."""
    if len(valores) < 2:
        return 50.0
    menores = sum(v < valor for v in valores)
    iguais = sum(v == valor for v in valores)
    return 100 * (menores + (iguais - 1) / 2) / (len(valores) - 1)


def indice(registros: dict) -> dict:
    validos = {
        uf: d
        for uf, d in registros.items()
        if all(d["indicadores"][k]["taxa"] is not None for k in COMPONENTES)
    }
    for uf, d in registros.items():
        notas = (
            {
                k: percentil(
                    d["indicadores"][k]["taxa"],
                    [v["indicadores"][k]["taxa"] for v in validos.values()],
                )
                for k in COMPONENTES
            }
            if uf in validos
            else {}
        )
        d["indice"] = (
            round(sum(notas.values()) / len(COMPONENTES), 2) if notas else None
        )
        d["componentes_indice"] = {k: round(v, 3) for k, v in notas.items()}
    return {
        "componentes": COMPONENTES,
        "pesos": dict.fromkeys(COMPONENTES, 0.2),
        "ufs_completas": len(validos),
        "formula": "Média dos postos percentuais das cinco taxas por 100 mil habitantes, com peso de 20% cada. Posto = 100 × (menores + (empatados−1)/2) / (N−1). Apenas UFs com 12 meses completos nos cinco componentes. Não soma vítimas e ocorrências como um total de crimes.",
    }


def publicar() -> dict:
    fonte = json.loads((RAW / "fonte.json").read_text())
    pop = {
        UF_CODES[r["D1C"]]: {"nome": r["D1N"], "populacao": int(r["V"])}
        for r in json.loads((RAW / "populacao_uf_2025.json").read_text())[1:]
    }
    dados = defaultdict(
        lambda: defaultdict(
            lambda: {
                "meses": set(),
                "soma": 0,
                "faltantes": 0,
                "linhas": 0,
                "municipais": 0,
            }
        )
    )
    eventos = {v[0]: k for k, v in METRICAS.items()}
    wb = openpyxl.load_workbook(
        RAW / "bancovde-2025.xlsx", read_only=True, data_only=True
    )
    rows = iter(wb.active.values)
    cols = next(rows)
    for row in rows:
        r = dict(zip(cols, row, strict=True))
        if r["abrangencia"] != "Estadual" or r["evento"] not in eventos:
            continue
        k = eventos[r["evento"]]
        d = dados[r["uf"]][k]
        v = r[METRICAS[k][1]]
        assert r["data_referencia"].year == 2025
        d["linhas"] += 1
        d["municipais"] += int(r["municipio"] not in [None, "NÃO INFORMADO"])
        if not isinstance(v, (int, float)) or v < 0:
            d["faltantes"] += 1
            continue
        assert int(v) == v
        d["meses"].add(r["data_referencia"].month)
        d["soma"] += int(v)
    wb.close()
    saida = {}
    for uf, p in pop.items():
        inds = {}
        for k in METRICAS:
            d = dados[uf][k]
            completo = len(d["meses"]) == 12 and not d["faltantes"]
            inds[k] = {
                "n": d["soma"] if d["meses"] else None,
                "taxa": (
                    round(100000 * d["soma"] / p["populacao"], 4) if completo else None
                ),
                "meses": len(d["meses"]),
                "linhas_sem_valor": d["faltantes"],
                "completo": completo,
                "linhas_municipais": d["municipais"],
            }
        saida[uf] = {**p, "indicadores": inds}
    metodo = indice(saida)
    meta = {
        "formato": 1,
        "ano": 2025,
        "geografia": "UF",
        "ufs": saida,
        "metricas": {k: {"nome": v[0], "unidade": v[2]} for k, v in METRICAS.items()},
        "metodo_indice": metodo,
        "fontes": [
            {"nome": "Sinesp VDE 2025 · arquivo oficial", **fonte},
            {
                "nome": "Notas metodológicas por UF",
                "url": NOTAS,
                "sha256": sha256(RAW / "notas.html"),
            },
            {
                "nome": "IBGE · população estadual em 1º de julho de 2025",
                "url": "https://apisidra.ibge.gov.br/values/t/6579/n3/all/v/9324/p/2025?formato=json",
                "sha256": sha256(RAW / "populacao_uf_2025.json"),
            },
        ],
        "limites": [
            "Dados estaduais: não medem o crime no prédio, na seção ou no município. Homicídios municipais do Atlas/SIM permanecem em camada separada, de 2024.",
            "Tráfico depende também da atuação policial; estupros, roubos e furtos sofrem subnotificação. Maior registro não é uma medida isolada de maior risco.",
            "Roubo e furto de veículos não representam todos os roubos e furtos. Estupro e estupro de vulnerável são exibidos separadamente; não somamos séries que podem se sobrepor conforme a metodologia estadual.",
            "Índice exploratório e não oficial: pesos iguais são uma escolha editorial, não gravidade validada. Não mede chance de vitimização nem causa do voto. Estupro de vulnerável, feminicídio e outros roubos ficam fora do índice para não ampliar peso ou sobrepor categorias.",
        ],
    }
    gravar(OUT, meta)
    print(
        json.dumps(
            {
                "ufs": len(saida),
                "indice_ufs": metodo["ufs_completas"],
                "CE": saida["CE"],
            },
            ensure_ascii=False,
        )
    )
    return meta


if __name__ == "__main__":
    publicar()
