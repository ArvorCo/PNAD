#!/usr/bin/env python3
"""Dados compactos do vídeo dos fiscais (video/fiscais), lidos do capítulo 13 da apuração.

Lê `analysis/apuracao_2026/dados/fiscais.json` e a malha de UFs e grava
`video/fiscais/src/dados/dados.json`, que o Remotion importa estaticamente. Para cada um dos
12 critérios escolhe uma seção real como exemplo, por regra declarada (nível mais alto,
depois pontuação, depois votantes; uma seção não repete entre critérios enquanto houver
outra). Nunca editar o JSON de saída à mão.

Uso: python3 scripts/video-fiscais-dados.py
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FISCAIS = ROOT / "analysis" / "apuracao_2026" / "dados" / "fiscais.json"
MALHA = ROOT / "apuracao" / "public" / "geo" / "br_uf.geojson"
SAIDA = ROOT / "video" / "fiscais" / "src" / "dados" / "dados.json"

NIVEL_ORDEM = {"alta": 0, "media": 1, "baixa": 2}
CODAREA_UF = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
    "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
    "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
    "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
}  # fmt: skip
CAMPOS_EXEMPLO = (
    "uf", "municipio", "zona", "secao", "local", "bairro", "aptos", "votantes", "validos",
    "brancos", "nulos", "lula", "flavio", "lula_pct", "flavio_pct", "zona_lula_pct",
    "zona_flavio_pct", "uf_lula_pct", "uf_flavio_pct", "encerramento_brasilia",
    "recebido_tse", "n_cargas", "lula_2022_pct", "flavio_2022_pct", "criterios", "nivel",
    "pontuacao", "explicacao_provavel", "o_que_conferir", "lat", "lon", "local_id",
)  # fmt: skip

# Projeção: equirretangular com correção de latitude média, em caixa de 1000 x 1000.
LON0, LON1, LAT0, LAT1 = -74.2, -34.5, -34.0, 5.5
VIEW = 1000.0
_COS = math.cos(math.radians((LAT0 + LAT1) / 2))
_ESCALA = VIEW / max((LON1 - LON0) * _COS, LAT1 - LAT0)
_DX = (VIEW - (LON1 - LON0) * _COS * _ESCALA) / 2
_DY = (VIEW - (LAT1 - LAT0) * _ESCALA) / 2


def projetar(lon: float, lat: float) -> tuple[float, float]:
    x = (lon - LON0) * _COS * _ESCALA + _DX
    y = (LAT1 - lat) * _ESCALA + _DY
    return round(x, 1), round(y, 1)


def caminho_svg(geometria: dict) -> str:
    aneis = (
        geometria["coordinates"]
        if geometria["type"] == "Polygon"
        else [a for poligono in geometria["coordinates"] for a in poligono]
    )
    partes = []
    for anel in aneis:
        pontos = [projetar(lon, lat) for lon, lat in anel]
        partes.append(
            "M" + " L".join(f"{x} {y}" for x, y in pontos) + " Z",
        )
    return "".join(partes)


def exemplo_por_criterio(secoes: list[dict]) -> dict[str, dict]:
    """Uma seção real por critério, pela regra declarada no cabeçalho."""
    usadas: set[tuple[str, int, int]] = set()
    exemplos: dict[str, dict] = {}
    for cid in "abcdefghijkl":
        candidatas = [
            s
            for s in secoes
            if cid in s["criterios"]
            and not s["sem_boletim"]
            and s["grupo_explicacao"] == "exige_explicacao_documental"
        ]
        candidatas.sort(
            key=lambda s: (
                NIVEL_ORDEM[s["nivel"]],
                -s["pontuacao"],
                -(s["votantes"] or 0),
            )
        )
        escolhida = next(
            (s for s in candidatas if (s["uf"], s["zona"], s["secao"]) not in usadas),
            candidatas[0],
        )
        usadas.add((escolhida["uf"], escolhida["zona"], escolhida["secao"]))
        compacta = {k: escolhida.get(k) for k in CAMPOS_EXEMPLO}
        compacta["detalhe"] = escolhida["detalhe"].get(cid)
        compacta["detalhes"] = escolhida["detalhe"]
        compacta["xy"] = projetar(escolhida["lon"], escolhida["lat"])
        exemplos[cid] = compacta
    return exemplos


def main() -> None:
    dados = json.loads(FISCAIS.read_text(encoding="utf-8"))
    malha = json.loads(MALHA.read_text(encoding="utf-8"))
    exemplos = exemplo_por_criterio(dados["secoes"])
    locais = {loc["local_id"]: loc for loc in dados["por_local"]}
    for e in exemplos.values():
        loc = locais.get(e["local_id"], {})
        e["local_secoes_sinalizadas"] = loc.get("secoes")
        e["local_secoes_total"] = loc.get("secoes_local")

    criterios = []
    for c in dados["criterios"]:
        criterios.append(
            {
                "id": c["id"],
                "nome": c["nome"],
                "mede": c["mede"],
                "limiar": c["limiar"],
                "peso": c["peso"],
                "secoes": c["secoes"],
                "por_nivel": c["secoes_por_nivel"],
                "explicacao_comum": c["explicacao_comum"],
                "o_que_conferir": c["o_que_conferir"],
                "exemplo": exemplos[c["id"]],
            }
        )

    por_uf = [
        {
            "uf": u["uf"],
            "regiao": u["regiao"],
            "secoes": u["secoes"],
            "alta": u["alta"],
            "media": u["media"],
            "baixa": u["baixa"],
            "locais_alta": u["locais_alta"],
            "taxa_pct": round(100 * u["secoes"] / u["secoes_universo"], 2),
        }
        for u in dados["por_uf"]
        if u["uf"] != "ZZ"
    ]

    colunas = dados["mapa"]["colunas"]
    i_lat, i_lon, i_nivel = (colunas.index(k) for k in ("lat", "lon", "nivel"))
    pontos_alta_media = [
        [*projetar(p[i_lon], p[i_lat]), p[i_nivel]]
        for p in dados["mapa"]["pontos"]
        if p[i_nivel] in ("alta", "media") and p[i_lat] is not None
    ]
    baixa = [p for p in dados["mapa"]["pontos"] if p[i_nivel] == "baixa" and p[i_lat]]
    amostra = random.Random(2026).sample(baixa, min(1500, len(baixa)))
    pontos_baixa = [[*projetar(p[i_lon], p[i_lat])] for p in amostra]

    ufs = [
        {"uf": CODAREA_UF[f["properties"]["codarea"]], "d": caminho_svg(f["geometry"])}
        for f in malha["features"]
    ]

    resumo = dados["resumo"]
    saida = {
        "gerado_em": dados["gerado_em"],
        "fonte": "analysis/apuracao_2026/dados/fiscais.json (capítulo 13 do dossiê da apuração)",
        "rotulos": dados["rotulos"],
        "resumo": {
            "secoes_universo": resumo["secoes_universo"],
            "secoes_sinalizadas": resumo["secoes_sinalizadas"],
            "por_nivel": {
                n: {
                    k: v["secoes"] if k == "secoes" else v[k]
                    for k in ("secoes", "locais", "municipios")
                }
                for n, v in resumo["por_nivel"].items()
            },
            "aptos_sinalizadas": resumo["eleitorado"]["aptos_sinalizadas"],
            "pct_sinalizadas": resumo["eleitorado"]["pct_sinalizadas"],
            "fiscais_um_por_local": resumo["fiscais"]["um_por_local"],
            "fiscais_dois_por_secao": resumo["fiscais"]["dois_por_secao_maximo_legal"],
            "explicacao_por_codigo": resumo["explicacao_comum"]["por_codigo"],
            "sem_arquivo": resumo["por_criterio"]["h"],
        },
        "sem_arquivo": sorted(
            {
                (s["uf"], s["municipio"], s["zona"]): 0 for s in dados["sem_arquivo"]
            }.keys()
        ),
        "sem_arquivo_por_zona": _contar_sem_arquivo(dados["sem_arquivo"]),
        "zonas_congeladas": {
            "zonas": len(dados["zonas_congeladas"]),
            "secoes": sum(z["secoes_faltando"] for z in dados["zonas_congeladas"]),
            "horas_min": min(z["horas_parada"] for z in dados["zonas_congeladas"]),
            "horas_max": max(z["horas_parada"] for z in dados["zonas_congeladas"]),
        },
        "criterios": criterios,
        "por_uf": por_uf,
        "municipios": dados["prioridade_pl"]["geral"]["municipios"][:5],
        "contrario": dados["achados"]["contrario"],
        "mapa": {
            "view": VIEW,
            "ufs": ufs,
            "pontos": pontos_alta_media,
            "pontos_baixa": pontos_baixa,
        },
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"{SAIDA.relative_to(ROOT)}: {SAIDA.stat().st_size // 1024} KB")
    for c in criterios:
        e = c["exemplo"]
        print(
            f"  {c['id']} {e['uf']} {e['municipio']} z{e['zona']} s{e['secao']} "
            f"nivel={e['nivel']} pont={e['pontuacao']} detalhe={e['detalhe']}"
        )


def _contar_sem_arquivo(secoes: list[dict]) -> list[dict]:
    contagem: dict[tuple[str, str, int], int] = {}
    for s in secoes:
        chave = (s["uf"], s["municipio"], s["zona"])
        contagem[chave] = contagem.get(chave, 0) + 1
    return [
        {"uf": uf, "municipio": mun, "zona": zona, "secoes": n}
        for (uf, mun, zona), n in sorted(contagem.items(), key=lambda kv: -kv[1])
    ]


if __name__ == "__main__":
    main()
