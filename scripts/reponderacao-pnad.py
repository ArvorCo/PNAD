#!/usr/bin/env python3
"""Agregador Arvor: reponderação por renda de todas as pesquisas nacionais.

Cada pesquisa entra como um arquivo JSON em ``analysis/reponderacao/pesquisas/``
com o que o instituto publicou: perfil de renda da amostra, cruzamento do voto
por faixa de renda e placar. O motor aplica sempre a mesma conta:

1. Recompõe o placar publicado a partir do cruzamento e das bases do próprio
   instituto (prova de leitura: o resíduo precisa ser pequeno).
2. Converte os cortes do cartão de renda para reais de abril de 2026 e lê no
   histograma da PNADC anual 2025 (``reponderacao-benchmark.py``) a fatia de
   pessoas de 16 anos ou mais em cada faixa.
3. Troca só essa margem: ``ajustado = publicado + (contrafactual - recomposto)``.

Depois calcula a média Arvor, uma média ponderada no tempo com meia-vida de
14 dias sobre a data final do campo, publicada e reponderada lado a lado.

Uso:
  python3 scripts/reponderacao-pnad.py            # calcula e grava o JSON
  python3 scripts/reponderacao-pnad.py paginas caminho.pdf   # acha as páginas de renda
  python3 scripts/reponderacao-pnad.py modelo instituto 2026-09-05  # esqueleto JSON
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "reponderacao"
POLLS_DIR = ANALYSIS / "pesquisas"
HISTOGRAM = ANALYSIS / "pnad_2025v1_histograma.json"
IPCA = ROOT / "data" / "outputs" / "ipca.csv"
IPCA_FALLBACK = ANALYSIS / "ipca_mensal.json"
MIN_WAGE = ROOT / "data" / "originals" / "salario_minimo.csv"
DEFAULT_OUTPUT = ROOT / "docs" / "assets" / "reponderacao_pnad.json"

MAIN_SERIES = "pessoas16_efetivo"
SCENARIOS = {
    "pessoas16_efetivo": "PNAD pessoas 16+ (rendimento efetivo, VD5001)",
    "pessoas16_habitual": "PNAD pessoas 16+ (rendimento habitual, VD5007)",
    "domicilios_efetivo": "PNAD domicílios (rendimento efetivo, VD5001)",
}
HALF_LIFE_DAYS = 14.0
NON_VOTE = {"branco_nulo", "indecisos", "nao_sabe", "nenhum", "outros"}
CANDIDATES_2T = ("lula", "flavio")
MIN_WAGE_BY_YEAR = {2024: 1412.0, 2025: 1518.0, 2026: 1621.0}


# --------------------------------------------------------------------------- #
# Séries auxiliares
# --------------------------------------------------------------------------- #
def load_ipca() -> dict[str, float]:
    """Índice IPCA mensal, chave AAAAMM. Usa o CSV do pipeline ou a cópia local."""
    series: dict[str, float] = {}
    if IPCA.exists():
        with IPCA.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                series[row["date"].replace("-", "")] = float(row["index"])
    elif IPCA_FALLBACK.exists():
        series = json.loads(IPCA_FALLBACK.read_text(encoding="utf-8"))
    return series


def ipca_factor(series: dict[str, float], from_month: str, to_month: str) -> float:
    """Fator entre dois meses; meses depois do fim da série ficam no último valor."""
    if not series:
        return 1.0
    last = max(series)
    src = series[min(from_month, last)] if from_month in series else series[last]
    dst = series[min(to_month, last)] if to_month in series else series[last]
    return dst / src


def minimum_wage(year: int) -> float:
    if MIN_WAGE.exists():
        with MIN_WAGE.open(encoding="utf-8") as handle:
            for row in csv.reader(handle):
                if row and row[0].startswith(f"{year}-"):
                    return float(row[1])
    return MIN_WAGE_BY_YEAR[year]


class Benchmark:
    """Histograma ponderado da renda domiciliar, consultável em qualquer corte."""

    def __init__(self, path: Path = HISTOGRAM) -> None:
        data = json.loads(path.read_text(encoding="utf-8"))
        self.meta = {k: v for k, v in data.items() if k != "series"}
        self.bin = float(data["bin_width_brl"])
        self.series = data["series"]
        self.cumulative: dict[str, list[float]] = {}
        for name, spec in self.series.items():
            acc, total = [0.0], 0.0
            for cell in spec["counts"]:
                total += cell
                acc.append(total)
            self.cumulative[name] = acc

    def total(self, name: str) -> float:
        return self.cumulative[name][-1]

    def below(self, name: str, value: float | None) -> float:
        """Peso com renda < value, com interpolação linear dentro da caixa."""
        acc = self.cumulative[name]
        if value is None:
            return acc[-1]
        if value <= 0:
            return 0.0
        pos = value / self.bin
        idx = int(pos)
        if idx >= len(acc) - 2:
            return acc[-2]
        return acc[idx] + (acc[idx + 1] - acc[idx]) * (pos - idx)

    def shares(self, name: str, cuts: list[float | None]) -> list[float]:
        """Fatias (%) das faixas definidas por cortes crescentes em R$ de 2026-04."""
        total = self.total(name)
        edges = [0.0, *cuts]
        out = []
        for lo, hi in pairwise(edges):
            out.append(100 * (self.below(name, hi) - self.below(name, lo)) / total)
        return out


# --------------------------------------------------------------------------- #
# Motor de reponderação
# --------------------------------------------------------------------------- #
def band_cuts_brl(poll: dict[str, Any], ipca: dict[str, float]) -> list[float | None]:
    """Cortes superiores das faixas em reais de abril de 2026."""
    renda = poll["renda"]
    unit = renda["unidade"]
    year = int(renda.get("ano_referencia", poll["campo"]["fim"][:4]))
    wage = minimum_wage(year)
    price_month = renda.get("mes_precos", poll["campo"]["fim"][:7].replace("-", ""))
    factor = ipca_factor(ipca, price_month, "202604")
    cuts: list[float | None] = []
    for band in renda["faixas"]:
        top = band.get("max")
        if top is None:
            cuts.append(None)
            continue
        value = float(top) * (wage if unit == "salarios_minimos" else 1.0)
        cuts.append(value * factor)
    if cuts[-1] is not None:
        raise ValueError(f"{poll['id']}: a última faixa precisa ser aberta (max null)")
    return cuts


def source_profile(poll: dict[str, Any]) -> list[float]:
    renda = poll["renda"]
    if "bases" in renda:
        total = float(sum(renda["bases"]))
        return [100 * b / total for b in renda["bases"]]
    pct = [float(v) for v in renda["amostra_pct"]]
    total = sum(pct)
    return [100 * v / total for v in pct]


def compose(rows: list[list[float]], weights: list[float]) -> list[float]:
    """Média ponderada das linhas do cruzamento (pesos em %)."""
    total = sum(weights)
    return [
        sum(w * row[j] for w, row in zip(weights, rows, strict=False)) / total
        for j in range(len(rows[0]))
    ]


def reweight_table(
    table: dict[str, Any],
    published: dict[str, float],
    source: list[float],
    targets: dict[str, list[float]],
) -> dict[str, Any]:
    options = table["opcoes"]
    rows = [[float(v) for v in row] for row in table["linhas"]]
    if len(rows) != len(source):
        raise ValueError("cruzamento com número de linhas diferente do perfil de renda")
    reproduced = dict(zip(options, compose(rows, source), strict=False))
    pub = {k: float(published.get(k, 0.0)) for k in options}
    residual = max(abs(reproduced[k] - pub[k]) for k in options if k not in NON_VOTE)
    scenarios: dict[str, Any] = {}
    for name, target in targets.items():
        counter = dict(zip(options, compose(rows, target), strict=False))
        adjusted = {k: pub[k] + counter[k] - reproduced[k] for k in options}
        scenarios[name] = {
            "contrafactual": {k: round(v, 3) for k, v in counter.items()},
            "ajustado": {k: round(v, 3) for k, v in adjusted.items()},
        }
    return {
        "opcoes": options,
        "publicado": pub,
        "recomposto": {k: round(v, 3) for k, v in reproduced.items()},
        "residuo_max": round(residual, 3),
        "cenarios": scenarios,
    }


def gap(values: dict[str, float]) -> float | None:
    if all(k in values for k in CANDIDATES_2T):
        return values["lula"] - values["flavio"]
    return None


def difference_margin(p1: float, p2: float, n: int) -> float:
    """Margem de 95% da diferença entre duas proporções sob amostragem simples."""
    a, b = p1 / 100, p2 / 100
    return 100 * 1.96 * math.sqrt(max(a + b - (a - b) ** 2, 0.0) / n)


def process_poll(
    poll: dict[str, Any], bench: Benchmark, ipca: dict[str, float]
) -> dict[str, Any]:
    cuts = band_cuts_brl(poll, ipca)
    source = source_profile(poll)
    targets = {name: bench.shares(name, cuts) for name in SCENARIOS}
    out: dict[str, Any] = {
        key: poll[key]
        for key in (
            "id",
            "instituto",
            "contratante",
            "registro_tse",
            "campo",
            "divulgacao",
            "n",
            "metodo",
            "fonte",
            "dossie",
        )
        if key in poll
    }
    out["renda"] = {
        "unidade": poll["renda"]["unidade"],
        "faixas": [b["rotulo"] for b in poll["renda"]["faixas"]],
        "cortes_brl_202604": [None if c is None else round(c, 2) for c in cuts],
        "amostra_pct": [round(v, 3) for v in source],
        "pnad_pct": {name: [round(v, 3) for v in t] for name, t in targets.items()},
        "nota": poll["renda"].get("nota"),
    }
    out["desvio_ate_primeira_faixa"] = round(source[0] - targets[MAIN_SERIES][0], 3)
    out["turnos"] = {}
    for turno in ("2t", "1t"):
        table = poll.get("cruzamentos", {}).get(turno)
        published = poll.get("publicado", {}).get(turno)
        if not table or not published:
            continue
        result = reweight_table(table, published, source, targets)
        main = result["cenarios"][MAIN_SERIES]["ajustado"]
        result["gap_publicado"] = gap(result["publicado"])
        result["gap_ajustado"] = gap(main)
        if result["gap_publicado"] is not None:
            result["margem_diferenca_95"] = round(
                difference_margin(
                    result["publicado"]["lula"],
                    result["publicado"]["flavio"],
                    poll["n"],
                ),
                3,
            )
        out["turnos"][turno] = result
    return out


# --------------------------------------------------------------------------- #
# Média Arvor
# --------------------------------------------------------------------------- #
def kernel_average(
    polls: list[dict[str, Any]],
    turno: str,
    key: str,
    option: str,
    day: date,
    causal: bool = True,
) -> float | None:
    """Média com peso 0,5^(|dias|/14). Causal usa só ondas já encerradas em ``day``;
    a linha de tendência desenhada usa os dois lados, como um alisador simétrico."""
    num = den = 0.0
    for poll in polls:
        result = poll["turnos"].get(turno)
        if not result:
            continue
        end = date.fromisoformat(poll["campo"]["fim"])
        if end > day and causal:
            continue
        value = (
            result["publicado"][option]
            if key == "publicado"
            else result["cenarios"][MAIN_SERIES]["ajustado"][option]
        )
        if value is None:
            continue
        weight = 0.5 ** (abs((day - end).days) / HALF_LIFE_DAYS)
        num += weight * value
        den += weight
    return None if den == 0 else num / den


def aggregate(polls: list[dict[str, Any]], today: date) -> dict[str, Any]:
    ends = [date.fromisoformat(p["campo"]["fim"]) for p in polls]
    start = min(ends)
    days = [start + timedelta(days=i) for i in range((today - start).days + 1)]
    series: dict[str, Any] = {"datas": [d.isoformat() for d in days]}
    for turno in ("2t", "1t"):
        series[turno] = {}
        for key in ("publicado", "ajustado"):
            series[turno][key] = {}
            for option in CANDIDATES_2T:
                values = [
                    kernel_average(polls, turno, key, option, d, causal=False)
                    for d in days
                ]
                series[turno][key][option] = [
                    None if v is None else round(v, 2) for v in values
                ]
    latest: dict[str, Any] = {}
    for turno in ("2t", "1t"):
        by_institute: dict[str, dict[str, Any]] = {}
        for poll in polls:
            if turno in poll["turnos"]:
                current = by_institute.get(poll["instituto"])
                if current is None or poll["campo"]["fim"] > current["campo"]["fim"]:
                    by_institute[poll["instituto"]] = poll
        if not by_institute:
            continue
        rows = list(by_institute.values())
        summary = {}
        for key in ("publicado", "ajustado"):
            summary[key] = {}
            for option in CANDIDATES_2T:
                vals = [
                    (
                        p["turnos"][turno]["publicado"][option]
                        if key == "publicado"
                        else p["turnos"][turno]["cenarios"][MAIN_SERIES]["ajustado"][
                            option
                        ]
                    )
                    for p in rows
                ]
                summary[key][option] = round(sum(vals) / len(vals), 2)
        latest[turno] = {
            "institutos": sorted(by_institute),
            "media_simples": summary,
            "kernel": {
                key: {
                    option: round(
                        kernel_average(polls, turno, key, option, today) or 0.0, 2
                    )
                    for option in CANDIDATES_2T
                }
                for key in ("publicado", "ajustado")
            },
        }
    return {
        "metodo": {
            "kernel": "média ponderada no tempo, peso 0,5^(dias desde o fim do campo / 14)",
            "linha": "a série desenhada usa o mesmo peso nos dois lados de cada dia (alisador simétrico); o valor corrente usa só ondas já encerradas",
            "meia_vida_dias": HALF_LIFE_DAYS,
            "media_simples": "última onda de cada instituto, peso igual",
            "cenario": SCENARIOS[MAIN_SERIES],
        },
        "serie": series,
        "ultimo": latest,
    }


# --------------------------------------------------------------------------- #
# Entrada e saída
# --------------------------------------------------------------------------- #
def load_polls(
    folder: Path = POLLS_DIR,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Devolve (pesquisas reponderáveis, pesquisas marcadas com ``ignorar``)."""
    polls, skipped = [], []
    for path in sorted(folder.glob("*.json")):
        poll = json.loads(path.read_text(encoding="utf-8"))
        poll.setdefault("id", path.stem)
        poll["_arquivo"] = str(path.relative_to(ROOT))
        (skipped if poll.get("ignorar") else polls).append(poll)
    key = lambda p: (p["campo"]["fim"], p["instituto"])  # noqa: E731
    polls.sort(key=key)
    skipped.sort(key=key)
    return polls, skipped


def build(today: date | None = None) -> dict[str, Any]:
    today = today or date.today()
    bench = Benchmark()
    ipca = load_ipca()
    raw_polls, skipped = load_polls()
    polls = [process_poll(p, bench, ipca) for p in raw_polls]
    for poll, raw in zip(polls, raw_polls, strict=False):
        poll["arquivo"] = raw["_arquivo"]
    institutes = sorted({p["instituto"] for p in polls})
    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "referencia": today.isoformat(),
        "benchmark": {
            **bench.meta,
            "cenario_principal": MAIN_SERIES,
            "cenarios": SCENARIOS,
            "totais_milhoes": {
                name: round(bench.total(name) / 1e6, 2) for name in SCENARIOS
            },
        },
        "metodo": {
            "formula": "ajustado = publicado + (contrafactual PNAD - recomposto pelas bases do instituto)",
            "margem_unica": "só a renda é trocada; sexo, idade, região e escolaridade ficam como o instituto ponderou",
            "limites": [
                "Sem microdados, pesos individuais, estratos, PSU nem efeito de desenho público.",
                "Renda familiar declarada ao entrevistador não é o rendimento domiciliar medido pela PNADC.",
                "Trocar uma margem não identifica interações com escolaridade, região, idade ou religião.",
                "Quem não declara renda fica fora da conta e entra pelo topline publicado.",
                "É sensibilidade sob régua comum, não o resultado real da eleição.",
            ],
        },
        "institutos": institutes,
        "pesquisas": polls,
        "nao_reponderaveis": [
            {
                key: poll.get(key)
                for key in (
                    "id",
                    "instituto",
                    "contratante",
                    "registro_tse",
                    "campo",
                    "divulgacao",
                    "n",
                    "fonte",
                    "publicado",
                    "motivo",
                )
            }
            for poll in skipped
        ],
        "agregador": aggregate(polls, today) if polls else None,
    }


def cmd_paginas(pdf: Path) -> int:
    """Lista as páginas do PDF que mencionam renda ou salário mínimo."""
    text = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True
    ).stdout
    pattern = re.compile(r"renda|sal[áa]rio|S\.?M\.?\b", re.IGNORECASE)
    for number, page in enumerate(text.split("\f"), start=1):
        hits = pattern.findall(page)
        if hits:
            first = next((ln.strip() for ln in page.splitlines() if ln.strip()), "")
            print(f"p.{number:3d}  {len(hits):2d} menções  {first[:90]}")
    return 0


def cmd_modelo(instituto: str, fim: str) -> int:
    slug = f"{instituto.lower().replace(' ', '_')}_{fim}"
    template = {
        "id": slug,
        "instituto": instituto,
        "contratante": "",
        "registro_tse": "BR-00000/2026",
        "campo": {"inicio": fim, "fim": fim},
        "divulgacao": fim,
        "n": 2000,
        "metodo": "presencial | telefônico | online",
        "fonte": {"pdf": "data/originals/...pdf", "url": "", "paginas": {}},
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": int(fim[:4]),
            "faixas": [
                {"rotulo": "Até 2 SM", "max": 2},
                {"rotulo": "2 a 5 SM", "max": 5},
                {"rotulo": "Mais de 5 SM", "max": None},
            ],
            "amostra_pct": [0, 0, 0],
        },
        "publicado": {"2t": {"lula": 0, "flavio": 0, "branco_nulo": 0, "indecisos": 0}},
        "cruzamentos": {
            "2t": {
                "opcoes": ["lula", "flavio", "branco_nulo", "indecisos"],
                "linhas": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            }
        },
    }
    path = POLLS_DIR / f"{slug}.json"
    if path.exists():
        print(f"já existe: {path}", file=sys.stderr)
        return 1
    path.write_text(json.dumps(template, ensure_ascii=False, indent=1) + "\n")
    print(f"esqueleto gravado em {path.relative_to(ROOT)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Agregador Arvor de reponderação.")
    sub = parser.add_subparsers(dest="cmd")
    run = sub.add_parser("calcular", help="calcula e grava o JSON público")
    run.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    run.add_argument("--hoje", type=date.fromisoformat, default=None)
    pages = sub.add_parser("paginas", help="acha as páginas de renda de um PDF")
    pages.add_argument("pdf", type=Path)
    model = sub.add_parser("modelo", help="cria o esqueleto JSON de uma pesquisa")
    model.add_argument("instituto")
    model.add_argument("fim", help="data final do campo, AAAA-MM-DD")
    args = parser.parse_args(argv)
    if args.cmd == "paginas":
        return cmd_paginas(args.pdf)
    if args.cmd == "modelo":
        return cmd_modelo(args.instituto, args.fim)
    output = getattr(args, "output", DEFAULT_OUTPUT)
    data = build(getattr(args, "hoje", None))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    for poll in data["pesquisas"]:
        line = f"{poll['campo']['fim']}  {poll['instituto']:<16}"
        for turno in ("1t", "2t"):
            result = poll["turnos"].get(turno)
            if result:
                adj = result["cenarios"][MAIN_SERIES]["ajustado"]
                line += (
                    f"  {turno}: {result['publicado']['lula']:.0f}×"
                    f"{result['publicado']['flavio']:.0f} → {adj['lula']:.1f}×"
                    f"{adj['flavio']:.1f} (resíduo {result['residuo_max']:.2f})"
                )
        print(line)
    print(f"gravado em {output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
