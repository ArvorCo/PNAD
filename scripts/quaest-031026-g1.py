#!/usr/bin/env python3
"""Integra a Quaest de 02 e 03/10/2026 a partir do painel e das matérias do G1.

O PDF completo não estava publicado na véspera do 1º turno. O painel do
contratante (G1) expõe uma API pública com a série inteira e os estratos,
inclusive renda em três faixas. Este script lê as respostas e as matérias
arquivadas em ``data/originals/quaest_102026_03/``, confere os hashes, prova
que o mesmo painel reproduz o PDF da onda de 27/09 célula a célula, escreve a
ficha do agregador e registra dois controles independentes de recomposição do
placar (renda e sexo). Os números de voto saem da API ou do texto das matérias;
nenhum é digitado à mão.

Se a série do 1º turno no painel ainda não tiver a coluna de 03/10, o placar
do 1º turno vem dos votos totais da matéria do G1 e o turno fica sem
cruzamento, declarado em ``sem_cruzamento``. Nenhum cruzamento de onda
anterior é reaproveitado.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/originals/quaest_102026_03"
PREV = ROOT / "analysis/reponderacao/pesquisas/quaest_2026-09-27.json"
PREV_AUDIT = ROOT / "analysis/reponderacao/atualizacao_20260929/auditoria.json"
OUT = ROOT / "analysis/reponderacao/pesquisas/quaest_2026-10-03.json"
DATE = "2026-10-03"
PREV_PANEL_DATE = "2026-09-28"
LIMIT = 1.5

NAMES = {
    "Lula": "lula",
    "Flávio Bolsonaro": "flavio",
    "Escritor Augusto Cury": "cury",
    "Renan Santos": "renan_santos",
    "Ronaldo Caiado": "caiado",
    "Romeu Zema": "zema",
    "Samara Martins": "samara",
    "Rui Costa Pimenta": "rui",
    "Wilson Grassi": "grassi",
    "Veterinário Wilson Grassi": "grassi",
    "Clariana Barão": "clariana",
    "Edmilson Costa": "edmilson",
    "Hertz Dias": "hertz",
    "Leonardo Avalanche": "avalanche",
    "Indecisos": "indecisos",
    "Branco/Nulo/Não Vai Votar": "branco_nulo",
    "Branco/nulo/não vai votar": "branco_nulo",
}
FILES = {"1t": "g1_estimulada_1t.json", "2t": "g1_segundo_turno.json"}
INCOME = ["renda-ate-2-sm", "renda-mais-de-2-a-5-sm", "renda-mais-de-5-sm"]
SEX = ["sexo-masculino", "sexo-feminino"]
LINE = re.compile(r"^(?P<nome>[^:(]+?)(?: \([^)]*\))?: (?P<v>\d+)%?(?: \(.*\))?$")


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def checked(item: dict[str, Any]) -> bytes:
    payload = (ROOT / item["arquivo"]).read_bytes()
    assert len(payload) == item["bytes"], item["arquivo"]
    assert hashlib.sha256(payload).hexdigest() == item["sha256"], item["arquivo"]
    return payload


def api_item(fonte: dict[str, Any], name: str) -> dict[str, Any]:
    return next(x for x in fonte["api"] if x["arquivo"].endswith(name))


def row(data: list[dict[str, Any]], day: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for option in data:
        for value in option["values"]:
            if value["date"].startswith(day):
                pct = 100 * value["value"]
                assert abs(pct - round(pct)) < 1e-9, (option["option"], pct)
                out[NAMES[option["option"]]] = round(pct)
    return out


def wave(turn: str, day: str) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    result = read(SRC / FILES[turn])["resultado"]
    total = row(result["cenarios"][0]["data"], day)
    by = {}
    for item in result["estratos"]:
        by[item["identificador"].rsplit("-", 3)[0]] = row(item["data"], day)
    return total, by


def materia_block(path: Path, start: str, stop: str) -> dict[str, int]:
    """Lê as linhas 'Nome (Partido): N%' de uma seção do texto da matéria."""
    lines = path.read_text(encoding="utf-8").splitlines()
    i = next(n for n, x in enumerate(lines) if x.strip().startswith(start))
    out: dict[str, int] = {}
    for line in lines[i + 1 :]:
        if line.startswith(stop):
            break
        match = LINE.match(line.strip())
        if match:
            out[NAMES[match["nome"].strip()]] = int(match["v"])
    return out


def compose(rows: list[dict[str, int]], weights: list[float], option: str) -> float:
    return sum(w * r[option] for w, r in zip(weights, rows, strict=True)) / sum(weights)


def control(
    published: dict[str, int], rows: list[dict[str, int]], weights: list[float]
) -> dict[str, Any]:
    rec = {k: round(compose(rows, weights, k), 2) for k in published}
    res = {k: round(rec[k] - published[k], 2) for k in published}
    return {
        "recomposto": rec,
        "residuo": res,
        "residuo_max_abs": max(abs(v) for v in res.values()),
    }


def previous_panel_matches_pdf(prev: dict[str, Any]) -> list[str]:
    """O painel de 28/09 precisa reproduzir o PDF da onda de 27/09."""
    diffs = []
    for turn in ("1t", "2t"):
        total, by = wave(turn, PREV_PANEL_DATE)
        options = prev["cruzamentos"][turn]["opcoes"]
        for i, band in enumerate(INCOME):
            line = dict(
                zip(options, prev["cruzamentos"][turn]["linhas"][i], strict=True)
            )
            got = dict(by[band])
            if "outros" in options:
                got["outros"] = sum(
                    v for k, v in got.items() if k not in options and k != "outros"
                )
            diffs += [f"{turn} {band} {k}" for k in options if got.get(k) != line[k]]
        published = prev.get("publicado_detalhado", {}).get(
            turn, prev["publicado"][turn]
        )
        diffs += [
            f"{turn} total {k}" for k, v in total.items() if published.get(k, 0) != v
        ]
    return diffs


def sex_weights() -> list[float]:
    """Pesos de sexo da onda de 27/09 (PDF p. 201), na ordem masculino, feminino."""
    audit = read(PREV_AUDIT)
    check = next(
        c
        for c in audit["controles"]
        if c["id"] == "quaest_2026-09-27" and c["turno"] == "2t"
    )
    feminino, masculino = check["controle_independente"]["pesos"]
    return [float(masculino), float(feminino)]


def main() -> None:
    fonte = read(SRC / "fonte.json")
    for item in [*fonte["api"], *fonte["materias"]]:
        checked(item)
    checked(fonte["painel"])
    prev = read(PREV)
    assert not previous_panel_matches_pdf(prev), previous_panel_matches_pdf(prev)
    income_weights = [float(v) for v in prev["renda"]["amostra_pct"]]
    sexw = sex_weights()

    materias = {m["chave"]: ROOT / m["texto"] for m in fonte["materias"]}
    validos = materia_block(materias["materia_1t"], "Votos Válidos", "Quaest:")
    totais_1t = materia_block(materias["materia_1t"], "Votos totais", "Grau")
    totais_2t = materia_block(materias["materia_2t"], "Veja abaixo", "Esta")
    assert sum(totais_1t.values()) == 100, totais_1t
    assert sum(totais_2t.values()) == 100, totais_2t

    published: dict[str, dict[str, int]] = {}
    crosses: dict[str, Any] = {}
    controls: dict[str, Any] = {}
    sem: dict[str, str] = {}
    pdf_1t = api_item(fonte, FILES["1t"])
    has_1t = pdf_1t["ultima_data_serie"] == DATE
    for turn in ("1t", "2t"):
        materia = totais_1t if turn == "1t" else totais_2t
        if turn == "1t" and not has_1t:
            published[turn] = {k: v for k, v in materia.items() if k != "avalanche"}
            sem[turn] = (
                "A série do 1º turno no painel do G1 (ESTIMULADA-PRE-003) terminava "
                f"em {pdf_1t['ultima_data_serie']} na captura de "
                f"{pdf_1t['capturado_em']}: sem cruzamento por renda desta onda. "
                "Placar dos votos totais lido da matéria do G1. Não se transporta "
                "o cruzamento da onda de 27/09."
            )
            continue
        total, by = wave(turn, DATE)
        for key, value in materia.items():
            assert total.get(key, 0) == value, (turn, key, total.get(key), value)
        options = list(total)
        published[turn] = total
        rows = [by[band] for band in INCOME]
        for r in rows:
            assert list(r) == options
        crosses[turn] = {
            "opcoes": options,
            "linhas": [[r[k] for k in options] for r in rows],
            "nota": (
                "Painel do G1 (API pública, tipo_pergunta "
                f"{api_item(fonte, FILES[turn])['tipo_pergunta']}), estratos de "
                "renda 'Até 2 sm', 'Mais de 2 a 5 sm' e 'Mais de 5 sm', coluna "
                "03/10. Valores arredondados ao inteiro pelo próprio painel e sem "
                "bases; zero do painel é arredondamento abaixo de 0,5, não "
                "imputação. O mesmo painel reproduz célula a célula o PDF da onda "
                "de 27/09 na coluna 28/09."
            ),
        }
        controls[turn] = {
            "renda": control(total, rows, income_weights),
            "sexo": control(total, [by[s] for s in SEX], sexw),
        }

    def fmt(x: float) -> str:
        return f"{x:.2f}".replace(".", ",")

    resumo = []
    for turn, label in (("1t", "1º turno"), ("2t", "2º turno")):
        if turn not in controls:
            continue
        c = controls[turn]
        resumo.append(
            f"{label}: renda recompõe Lula {fmt(c['renda']['recomposto']['lula'])} e "
            f"Flávio {fmt(c['renda']['recomposto']['flavio'])} contra "
            f"{published[turn]['lula']} e {published[turn]['flavio']}, maior "
            f"resíduo {fmt(c['renda']['residuo_max_abs'])} pp; sexo, maior resíduo "
            f"{fmt(c['sexo']['residuo_max_abs'])} pp"
        )
    main_item = api_item(fonte, FILES["1t"] if has_1t else FILES["2t"])
    complementos = [
        {
            "rotulo": f"G1: {item['rotulo']}",
            "url": item["url"],
            "arquivo": item["arquivo"],
            "sha256": item["sha256"],
        }
        for item in fonte["api"]
        if item is not main_item
    ] + [
        {
            "rotulo": f"G1: matéria ({m['chave'].removeprefix('materia_')})",
            "url": m["url"],
            "arquivo": m["arquivo"],
            "sha256": m["sha256"],
        }
        for m in fonte["materias"]
    ]
    poll: dict[str, Any] = {
        "instituto": "Quaest",
        "contratante": prev["contratante"],
        "metodo": prev["metodo"],
        "id": "quaest_2026-10-03",
        "registro_tse": fonte["registro_tse"],
        "campo": {"inicio": "2026-10-02", "fim": DATE},
        "divulgacao": DATE,
        "n": fonte["n"],
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "faixas": prev["renda"]["faixas"],
            "amostra_pct": prev["renda"]["amostra_pct"],
            "mes_precos": "202610",
            "perfil_tipo": "hipotese_onda_anterior",
            "nota": (
                "Hipótese explícita: o painel do G1 não publica o perfil da "
                "amostra, então o perfil usado é o da onda de 27/09 da própria "
                "Quaest (PDF p. 204: 31/42/27). Será substituído pelo perfil do "
                "PDF quando a íntegra sair."
            ),
        },
        "publicado": published,
        "publicado_validos": {
            "1t": validos,
            "nota": (
                "Votos válidos da matéria do G1. A Quaest os estima com modelo de "
                "eleitor provável (perfil de comparecimento), não por simples "
                "renormalização dos votos totais; por isso Flávio tem 45 nos "
                "válidos, e não 44 como daria 38/87. Não entram no motor."
            ),
        },
        "cruzamentos": crosses,
        "controles": {
            "pesos_renda": income_weights,
            "pesos_sexo_masculino_feminino": sexw,
            "pesos_sexo_nota": (
                "Hipótese explícita: pesos de sexo da onda de 27/09 (PDF p. 201: "
                "47% homens, 53% mulheres)."
            ),
            **controls,
        },
        "fonte": {
            "tipo": "painel_contratante",
            "rotulo": "Painel do G1 (API) e matérias do G1",
            "url": main_item["url"],
            "arquivo": main_item["arquivo"],
            "sha256": main_item["sha256"],
            "bytes": main_item["bytes"],
            "paginas": {
                "1t_topline": (
                    "API ESTIMULADA-PRE-003, total"
                    if has_1t
                    else "matéria do G1, votos totais"
                ),
                "1t_renda": (
                    "API ESTIMULADA-PRE-003, estratos de renda"
                    if has_1t
                    else "não disponível no corte"
                ),
                "2t_topline": "API SEGTURNO-PRE-001, total",
                "2t_renda": "API SEGTURNO-PRE-001, estratos de renda",
                "perfil_renda": "não publicado; hipótese da onda de 27/09",
            },
            "conferido_em": DATE,
            "status": fonte["relatorio_pdf_status"],
            "nota": (
                "O painel do G1 reproduz célula a célula o PDF da onda de 27/09. "
                "Os valores vêm arredondados ao inteiro e sem bases; o perfil de "
                "renda é o da onda anterior, como hipótese explícita. Registro, "
                "campo, n e margem lidos das matérias do G1."
            ),
            "complementos": complementos,
        },
        "notas": (
            "PDF não publicado em 03/10/2026; números de voto da API do painel do "
            "G1 e das matérias, metadados (registro BR-02197/2026, campo de 02 e "
            "03/10, 3.702 entrevistas, margem de 2 pontos) das matérias do G1. "
            + "; ".join(resumo)
            + ". A conta preserva o placar publicado e acrescenta apenas o delta "
            "da troca de renda."
        ),
    }
    if sem:
        poll["sem_cruzamento"] = sem
    for turn, c in controls.items():
        for dim in ("renda", "sexo"):
            assert c[dim]["residuo_max_abs"] <= LIMIT, (turn, dim, c[dim])
    OUT.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(controls, ensure_ascii=False, indent=1))
    print("1t no painel:", has_1t)


if __name__ == "__main__":
    main()
