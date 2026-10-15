"""Extrai apenas o DOM salvo pelo usuário, sem executar JS ou acessar a rede."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/originals/quaest_102026_14"
PUBLIC = ROOT / "docs/fontes/quaest_14102026"
ARCHIVE = SOURCE / "g1-painel-salvo.html.gz"
EXTRACT = SOURCE / "g1-painel-extraido.json"
OPTIONS = {
    "flavio-bolsonaro": "flavio",
    "lula": "lula",
    "indecisos": "indecisos",
    "branco-nulo-nao-vai-votar": "branco_nulo",
}


def parse(raw):
    soup = BeautifulSoup(raw, "html.parser")
    methodology = soup.select_one(".methodology__description")
    if methodology is None:
        methodology = soup.find(string=lambda s: s and "BR-08729/2026" in s)
    text = (
        methodology.get_text(" ", strip=True)
        if hasattr(methodology, "get_text")
        else str(methodology).strip()
    )
    if not all(token in text for token in ("2.154", "10 e 13", "BR-08729/2026")):
        raise ValueError("A ficha não identifica a onda de 10–13/10")
    graphs = []
    for graph in soup.select(".graph[graph-id]"):
        graph_id = graph["graph-id"]
        if not graph_id.endswith("-ESTIMULADA-PRE-201"):
            raise ValueError(f"Pergunta inesperada: {graph_id}")
        title = graph.select_one("h4") or graph.select_one("h3")
        values = {}
        for name, key in OPTIONS.items():
            labels = graph.select(f"svg.chart-bars text.label-{name}")
            if len(labels) > 1:
                raise ValueError(f"Mais de um valor por opção em {graph_id}")
            values[key] = int(labels[0].get_text(strip=True)) if labels else None
        complete = all(v is not None for v in values.values())
        if complete and not 98 <= sum(values.values()) <= 102:
            raise ValueError(f"Soma incompatível em {graph_id}")
        margin = graph.select_one(".margem")
        graphs.append(
            {
                "id": graph_id,
                "dimensao": graph.get("stratum-category", "total"),
                "rotulo": title.get_text(" ", strip=True),
                "votos": values,
                "margem_declarada_pp": int(re.search(r"\d+", margin.get_text())[0]),
                "completo": complete,
            }
        )
    total = next(g for g in graphs if g["dimensao"] == "total")
    if total["votos"] != {"flavio": 46, "lula": 44, "indecisos": 1, "branco_nulo": 9}:
        raise ValueError("O gráfico total não corresponde à divulgação de 14/10")
    return {
        "origem": "Página pública salva pelo usuário e fornecida localmente; nenhuma consulta automatizada ao G1/API.",
        "recebido_em": "2026-10-15",
        "url": "https://especiaisg1.globo/politica/eleicoes/2026/pesquisas-eleitorais/presidente/2-turno/Quaest/internal/",
        "pagina_id": "216",
        "pergunta": "ESTIMULADA-PRE-201",
        "metodologia": text,
        "graficos": graphs,
        "nota": "Valores dos rótulos SVG, não dos indicadores circulares transitórios. Ausência de rótulo é null, nunca zero. Bases e perfil final não constam do painel salvo.",
    }


def evidence(raw):
    """Conserva título, legenda e SVG dos cinco gráficos, eliminando scripts."""
    soup = BeautifulSoup(raw, "html.parser")
    chunks = []
    for graph in soup.select(
        '.graph[stratum-category="renda"], .graph[stratum-category="sexo"]'
    ):
        title = graph.select_one("h4").get_text(" ", strip=True)
        svg = graph.select_one("svg.chart-bars")
        # SVG do DOM, com rótulos visíveis. Sem imagens, scripts ou recursos remotos.
        for node in svg.select("script, foreignObject, image, use, a"):
            node.decompose()
        for node in [svg, *svg.find_all(True)]:
            for attr in list(node.attrs):
                if attr.startswith("on") or attr in ("href", "xlink:href"):
                    del node[attr]
        chunks.append(f"<section><h2>{escape(title)}</h2>{svg}</section>")
    return """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Quaest 14/10: evidência do painel salvo</title>
<style>body{font:18px Georgia,serif;color:#18271d;background:#fff;margin:32px;max-width:1050px}
section{margin:32px 0}h2{font-size:22px}svg{display:block;max-width:100%;height:auto}
.legend{font:16px sans-serif}.f{color:#30306d}.l{color:#c0122d}</style></head><body>
<h1>Quaest 14/10/2026: gráficos preservados no arquivo recebido</h1>
<p>Campo 10–13/10 · 2.154 entrevistas · BR-08729/2026.<br>
SVGs extraídos do HTML fornecido pelo usuário, sem consulta remota ou execução de scripts.
Os eixos e rótulos numéricos são os do arquivo original.</p>
<p class="legend"><b class="f">Flávio Bolsonaro</b> · <b class="l">Lula</b> · Indecisos · Branco/nulo/não vai votar<br>
Mesma ordem da esquerda para a direita em cada gráfico.</p>
""" + "\n".join(chunks) + "</body></html>\n"


def ingest(path):
    raw = path.read_bytes()
    data = parse(raw)
    SOURCE.mkdir(parents=True, exist_ok=True)
    PUBLIC.mkdir(parents=True, exist_ok=True)
    ARCHIVE.write_bytes(gzip.compress(raw, mtime=0))
    data["arquivo_original"] = {
        "arquivo": str(ARCHIVE.relative_to(ROOT)),
        "nome_recebido": path.name,
        "bytes_descomprimidos": len(raw),
        "sha256_descomprimido": hashlib.sha256(raw).hexdigest(),
    }
    EXTRACT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    (PUBLIC / "painel-evidencia.html").write_text(evidence(raw))
    (PUBLIC / "painel-extraido.json").write_text(EXTRACT.read_text())
    with (PUBLIC / "painel-extraido.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(
            ["dimensao", "rotulo", *OPTIONS.values(), "margem_declarada_pp", "completo"]
        )
        for row in data["graficos"]:
            writer.writerow(
                [
                    row["dimensao"],
                    row["rotulo"],
                    *row["votos"].values(),
                    row["margem_declarada_pp"],
                    row["completo"],
                ]
            )
    return data


def integrate(data):
    """Atualiza a entrada mantendo explícita a hipótese das cotas atuais."""
    path = ROOT / "analysis/reponderacao/pesquisas/quaest_2026-10-13.json"
    poll = json.loads(path.read_text())

    def group(name):
        return [g for g in data["graficos"] if g["dimensao"] == name]

    options = list(OPTIONS.values())
    income = group("renda")
    if len(income) != 3 or not all(g["completo"] for g in income + group("sexo")):
        raise ValueError(
            "Os cruzamentos atuais de renda e sexo precisam estar completos"
        )
    poll.pop("ignorar", None)
    poll.pop("motivo", None)
    note = "Hipótese provisória: cotas de renda 31/42/27 do registro atual BR-08729/2026 usadas como pesos. Perfil final, bases após rake/MrP e não resposta à renda não publicados no arquivo salvo. A conta assume cobertura integral dessas faixas. A boa recomposição não comprova os pesos. Nenhum voto por renda de onda anterior foi transportado."
    poll["renda"] = {
        "unidade": "salarios_minimos",
        "ano_referencia": 2026,
        "faixas": [
            {"rotulo": label, "max": top}
            for label, top in zip(
                poll["perfil_economico_publicado"]["faixas"], [2, 5, None], strict=True
            )
        ],
        "amostra_pct": [31, 42, 27],
        "mes_precos": "202610",
        "perfil_tipo": "cota_registrada",
        "nota": note,
    }
    poll["cruzamentos"] = {
        "2t": {
            "opcoes": options,
            "linhas": [[g["votos"][k] for k in options] for g in income],
            "nota": "Rótulos SVG do painel G1 salvo pelo usuário. Valores inteiros, sem bases; 0 é arredondado no painel. Extração local, sem acesso remoto à API.",
        }
    }
    controls = {}
    for dimension, weights in (
        ("renda", [31, 42, 27]),
        ("sexo", [53, 47]),
        ("idade", [31, 45, 24]),
        ("escolaridade", [42, 39, 19]),
    ):
        graphs = group(dimension)
        totals = {
            k: round(
                sum(w * g["votos"][k] for w, g in zip(weights, graphs, strict=True))
                / 100,
                6,
            )
            for k in options
        }
        controls[dimension] = {
            "pesos_cotas_previstas_pct": weights,
            "ordem": [g["rotulo"] for g in graphs],
            "recomposto": totals,
            "residuo_recomposto_menos_publicado": {
                k: round(v - poll["publicado"]["2t"][k], 6) for k, v in totals.items()
            },
        }
    (SOURCE / "g1-controles.json").write_text(
        json.dumps(controls, ensure_ascii=False, indent=2) + "\n"
    )
    poll["controles_arquivo"] = str((SOURCE / "g1-controles.json").relative_to(ROOT))
    poll["fonte"].update(
        {
            "tipo": "painel_contratante_salvo_pelo_usuario",
            "rotulo": "G1: painel salvo pelo usuário, cruzamentos extraídos do DOM; registro TSE conferido",
            "url": data["url"],
            "arquivo": str(ARCHIVE.relative_to(ROOT)),
            "sha256": hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
            "status": "Totais e 25 recortes completos extraídos do arquivo salvo. Cotas atuais conferidas no TSE; sensibilidade provisória, perfil final não verificado.",
            "nota": note,
        }
    )
    poll["fonte"]["complementos"][1][
        "rotulo"
    ] = "G1: página externa; painel recebido em arquivo local"
    path.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    return poll
