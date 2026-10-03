#!/usr/bin/env python3
"""Integra a Datafolha de 02 e 03/10/2026 a partir do painel do G1.

O PDF completo não estava publicado na véspera do 1º turno. O painel do
contratante (G1) expõe uma API pública com a série inteira e os estratos,
inclusive renda em três faixas. Este script lê as respostas arquivadas em
``data/originals/datafolha_102026_03/``, confere os hashes, escreve a ficha do
agregador e registra dois controles independentes de recomposição do placar
(renda e sexo). Nenhum número é digitado à mão, exceto os metadados da
matéria da Folha (registro, campo, n), que ficam citados ao lado.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/originals/datafolha_102026_03"
PREV = ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-01.json"
PREV_CROSS = ROOT / "analysis/reponderacao/datafolha_20261001_cruzamentos.json"
OUT = ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-03.json"
DATE = "2026-10-03"
LIMIT = 1.5

NAMES = {
    "Lula": "lula",
    "Flavio Bolsonaro": "flavio",
    "Escritor Augusto Cury": "cury",
    "Ronaldo Caiado": "caiado",
    "Renan Santos": "renan_santos",
    "Zema": "zema",
    "Samara": "samara",
    "Edmilson Costa": "edmilson",
    "Rui Costa Pimenta": "rui",
    "Veterinário Wilson Grassi": "grassi",
    "Clariana Barão": "clariana",
    "Hertz Dias": "hertz",
    "Em Branco/Nulo/Nenhum": "branco_nulo",
    "Indecisos": "indecisos",
}
FILES = {"1t": "g1_estimulada_1t.json", "2t": "g1_segundo_turno.json"}
INCOME = ["renda-ate-2-sm-2", "renda-mais-de-2-a-5-sm-2", "renda-mais-de-5-sm-2"]
SEX = ["sexo-masculino", "sexo-feminino"]


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def checked(name: str) -> dict[str, Any]:
    fonte = read(SRC / "fonte.json")
    item = next(x for x in fonte["api"] if x["arquivo"].endswith(name))
    payload = (SRC / name).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == item["sha256"], name
    assert len(payload) == item["bytes"], name
    return item


def row(data: list[dict[str, Any]], day: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for option in data:
        for value in option["values"]:
            if value["date"].startswith(day):
                pct = 100 * value["value"]
                assert abs(pct - round(pct)) < 1e-9, (option["option"], pct)
                out[NAMES[option["option"]]] = round(pct)
    return out


def strata(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {e["identificador"].rsplit("-", 3)[0]: e for e in result["estratos"]}


def wave(turn: str, day: str) -> tuple[dict[str, int], dict[str, dict[str, int]]]:
    result = read(SRC / FILES[turn])["resultado"]
    total = row(result["cenarios"][0]["data"], day)
    by = {}
    for key, item in strata(result).items():
        by[key] = row(item["data"], day)
    return total, by


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
    """O painel de 01/10 precisa reproduzir o PDF de 01/10 célula a célula."""
    diffs = []
    for turn in ("1t", "2t"):
        total, by = wave(turn, "2026-10-01")
        for key, value in total.items():
            if prev["publicado"][turn].get(key) != value:
                diffs.append(f"{turn} total {key}")
        options = prev["cruzamentos"][turn]["opcoes"]
        for i, band in enumerate(INCOME):
            for j, key in enumerate(options):
                if key in by[band] and by[band][key] != (
                    prev["cruzamentos"][turn]["linhas"][i][j]
                ):
                    diffs.append(f"{turn} {band} {key}")
    return diffs


def main() -> None:
    prev = read(PREV)
    assert not previous_panel_matches_pdf(prev), previous_panel_matches_pdf(prev)
    sex_base = read(PREV_CROSS)["tabelas"]["estimulada"]["blocks"]["bloco1"]["base"]
    sex_weights = [float(sex_base["Masculino"]), float(sex_base["Feminino"])]
    income_weights = [float(b) for b in prev["renda"]["bases"]]
    items = {turn: checked(name) for turn, name in FILES.items()}

    published, crosses, controls = {}, {}, {}
    for turn in ("1t", "2t"):
        total, by = wave(turn, DATE)
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
                f"{items[turn]['tipo_pergunta']}), estratos de renda "
                "'Até 2 s.m.', 'Mais de 2 a 5 s.m' e 'Mais de 5 s.m.'. Valores "
                "arredondados ao inteiro pelo próprio painel e sem bases. O mesmo "
                "painel reproduz célula a célula o PDF da onda de 01/10."
            ),
        }
        controls[turn] = {
            "renda": control(total, rows, income_weights),
            "sexo": control(total, [by[s] for s in SEX], sex_weights),
        }
        for dim in ("renda", "sexo"):
            assert controls[turn][dim]["residuo_max_abs"] <= LIMIT, (turn, dim)

    fonte = read(SRC / "fonte.json")
    materia = fonte["materias"][0]
    c = controls
    poll = {
        "instituto": "Datafolha",
        "contratante": "Folha de S.Paulo e TV Globo",
        "metodo": "presencial, pontos de fluxo",
        "id": "datafolha_2026-10-03",
        "registro_tse": fonte["registro_tse"],
        "campo": {"inicio": "2026-10-02", "fim": "2026-10-03"},
        "divulgacao": DATE,
        "n": fonte["n"],
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "faixas": prev["renda"]["faixas"],
            "mes_precos": "202610",
            "bases": prev["renda"]["bases"],
            "perfil_tipo": "hipotese_onda_anterior",
            "nota": (
                "Hipótese explícita: o painel do G1 não publica o perfil da "
                "amostra, então o perfil usado é o das bases ponderadas de renda "
                "da onda de 01/10 do próprio Datafolha (PDF de 02/10, pp. 45 e "
                "53: 1.209/856/344). O Datafolha pondera às mesmas metas "
                "declaradas no registro entre ondas, e a matéria da Folha de "
                "03/10 confirma a composição desta onda nas duas primeiras "
                "faixas: os 48% mais pobres e 34% da amostra entre 2 e 5 "
                "salários (01/10: 48,2% e 34,2% do total). Será substituído "
                "pelo perfil do PDF quando a íntegra sair."
            ),
        },
        "publicado": published,
        "cruzamentos": crosses,
        "controles": {
            "pesos_renda": income_weights,
            "pesos_sexo_masculino_feminino": sex_weights,
            "pesos_sexo_nota": (
                "Hipótese explícita: bases de sexo da onda de 01/10 (PDF p. 44: "
                "1.215 homens, 1.291 mulheres)."
            ),
            **{t: controls[t] for t in ("1t", "2t")},
        },
        "fonte": {
            "tipo": "painel_contratante",
            "rotulo": "Painel do G1, 1º turno (API)",
            "url": items["1t"]["url"],
            "arquivo": items["1t"]["arquivo"],
            "sha256": items["1t"]["sha256"],
            "bytes": items["1t"]["bytes"],
            "paginas": {
                "1t_topline": "API ESTIMULADA-PRE-002, total",
                "1t_renda": "API ESTIMULADA-PRE-002, estratos de renda",
                "2t_topline": "API SEGTURNO-PRE-001, total",
                "2t_renda": "API SEGTURNO-PRE-001, estratos de renda",
                "perfil_renda": "não publicado; hipótese da onda de 01/10",
            },
            "conferido_em": DATE,
            "status": (
                "Íntegra em PDF não publicada até a consulta de 03/10/2026; "
                "números lidos da API pública do painel do G1, contratante. "
                "Conferir contra o PDF quando sair."
            ),
            "nota": (
                "O painel do G1 reproduz célula a célula o PDF da onda de 01/10. "
                "Os valores vêm arredondados ao inteiro e sem bases; o perfil de "
                "renda é o da onda anterior, como hipótese explícita."
            ),
            "complementos": [
                {
                    "rotulo": "G1: 2º turno, Lula × Flávio",
                    "url": items["2t"]["url"],
                    "arquivo": items["2t"]["arquivo"],
                    "sha256": items["2t"]["sha256"],
                },
                {
                    "rotulo": "Folha: matéria da divulgação",
                    "url": materia["url"],
                    "arquivo": materia["arquivo"],
                    "sha256": materia["sha256"],
                },
            ],
        },
        "notas": (
            "PDF não publicado em 03/10/2026; todos os números de voto vêm da "
            "API do painel do G1 e os metadados (registro, campo de 02 e 03/10, "
            "4.006 entrevistas em 122 municípios, margem de 2 pontos) da matéria "
            "da Folha. O cartão do painel não lista Leonardo Avalanche, que teve "
            "zero no PDF de 01/10. Recomposição por renda: 1º turno Lula "
            f"{c['1t']['renda']['recomposto']['lula']:.2f} e Flávio "
            f"{c['1t']['renda']['recomposto']['flavio']:.2f} contra "
            f"{published['1t']['lula']} e {published['1t']['flavio']}, maior "
            f"resíduo {c['1t']['renda']['residuo_max_abs']:.2f} pp; 2º turno Lula "
            f"{c['2t']['renda']['recomposto']['lula']:.2f} e Flávio "
            f"{c['2t']['renda']['recomposto']['flavio']:.2f} contra "
            f"{published['2t']['lula']} e {published['2t']['flavio']}, maior "
            f"resíduo {c['2t']['renda']['residuo_max_abs']:.2f} pp. Controle por "
            f"sexo: maior resíduo {c['1t']['sexo']['residuo_max_abs']:.2f} pp no "
            f"1º turno e {c['2t']['sexo']['residuo_max_abs']:.2f} pp no 2º. A "
            "conta preserva o placar publicado e acrescenta apenas o delta da "
            "troca de renda."
        ),
    }
    OUT.write_text(json.dumps(poll, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(controls, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
