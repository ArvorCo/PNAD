"""Erro retrospectivo com autoria explícita e projeções congeladas antes da urna."""

import json
from functools import cache

from apuracao_2026.pesquisas import NAO_ESCOLHA, validos
from reponderacao_vista.context import ROOT, D
from reponderacao_vista.urna_dados import AUDIT, OFFICIAL, RESIDUAL, URNA

PAIR = ("flavio", "lula")
OFF = json.loads(OFFICIAL.read_text(encoding="utf-8"))["nacional"]
FOLDER = ROOT / "analysis/reponderacao/avaliacao_1t"
EVIDENCE = json.loads((FOLDER / "publicados.json").read_text())
FROZEN = json.loads((FOLDER / "arvor_pre_urna.json").read_text())


def urna(mode):
    denominator = (
        OFF["validos"]
        if mode == "validos"
        else OFF["validos"] + OFF["brancos"] + OFF["nulos"]
    )
    return {c: 100 * OFF["votos"][c] / denominator for c in PAIR}


def latest_comparison(name):
    rows = [
        p
        for p in AUDIT["pesquisas"]
        if p["instituto"] == name and p["ultima_onda_da_casa"]
    ]
    for pid, item in EVIDENCE["ondas"].items():
        if item["instituto"] == name and item.get("total"):
            normalized, _ = validos(item["total"])
            rows.append(
                {
                    "id": pid,
                    "instituto": name,
                    "campo": item["campo"],
                    "divulgacao": item["divulgacao"],
                    "publicado": {"total": item["total"], "validos": normalized},
                }
            )
    if not rows:
        for poll in D["pesquisas"] + D.get("nao_reponderaveis", []):
            values = poll.get("publicado", {}).get("1t")
            if (
                poll["instituto"] != name
                or not values
                or poll.get("substituida")
                or poll.get("primeiro_turno_com_marcal")
                or poll["divulgacao"] > "2026-10-04"
                or poll["campo"]["fim"] > "2026-10-04"
            ):
                continue
            if any(
                v > 0 and k not in URNA.keys() | RESIDUAL | NAO_ESCOLHA
                for k, v in values.items()
            ):
                continue
            normalized, _ = validos(values)
            rows.append({**poll, "publicado": {"total": values, "validos": normalized}})
    return (
        max(rows, key=lambda p: (p["campo"]["fim"], p["divulgacao"])) if rows else None
    )


def metrics(values, mode="validos"):
    """No pair-only renormalization, and no cancellation of candidate errors."""
    actual = urna(mode)
    errors = {c: values[c] - actual[c] for c in PAIR}
    return {
        "valores": values,
        "base": mode,
        "erro_pp": errors,
        "eam_fl_pp": sum(abs(v) for v in errors.values()) / 2,
        "erro_vantagem_fl_pp": errors["flavio"] - errors["lula"],
    }


@cache
def evaluate(name):
    poll = latest_comparison(name)
    documentary = next(
        (
            json.loads(p.read_text())
            for p in (ROOT / "analysis/reponderacao/metodologias").glob("*.json")
            if json.loads(p.read_text())["instituto"] == name
        ),
        None,
    )
    result = {
        "instituto": name,
        "id": poll["id"] if poll else None,
        "score_arvor_pp": None,
        "nota_documental": (
            sum(c["pontos"] for c in documentary["criterios"]) if documentary else None
        ),
        "nota_documental_referencia": "2026-09-21",
        "leituras": {},
        "status": "Sem última onda comparável pré-urna no acervo.",
    }
    if poll is None:
        return result
    result.update(campo=poll["campo"], divulgacao=poll["divulgacao"])
    evidence = EVIDENCE["ondas"].get(poll["id"])
    result["evidencia"] = evidence
    reads = result["leituras"]
    reads["total_publicado"] = metrics(poll["publicado"]["total"], "total")
    reads["conversao_arvor"] = metrics(poll["publicado"]["validos"])
    if evidence and evidence["validos"] is not None:
        reads["validos_instituto"] = metrics(evidence["validos"])
        if poll["campo"]["fim"] >= "2026-09-25":
            result["score_arvor_pp"] = reads["validos_instituto"]["eam_fl_pp"]
            result["status"] = "Válidos publicados pelo instituto."
        else:
            result["status"] = "Campo anterior à janela final; fora do ranking."
    else:
        result["status"] = (
            "A casa declara não publicar válidos."
            if evidence and evidence["status"] == "nao_publica_declarado"
            else "Válidos publicados não localizados; sem score eleitoral."
        )
    adjusted = poll.get("reponderado")
    if adjusted:
        reads["pnad_total"] = metrics(adjusted["total"], "total")
        reads["pnad_validos"] = metrics(adjusted["validos"])
    frozen = FROZEN["ondas"].get(poll["id"])
    if frozen:
        reads["arvor_pre_urna"] = metrics(frozen["modelo"])
        result["sensibilidades_pre_urna"] = {
            k: metrics(v) for k, v in frozen["cenarios"].items()
        }
    result["delta_pnad_total"] = (
        {
            c: reads["pnad_total"]["valores"][c]
            - reads["total_publicado"]["valores"][c]
            for c in PAIR
        }
        if "pnad_total" in reads
        else None
    )
    return result


def order_key(name):
    score = evaluate(name)["score_arvor_pp"]
    return (score is None, round(score, 2) if score is not None else 0, name)


def ranking(names):
    rows = []
    for name in sorted(names, key=order_key):
        row = dict(evaluate(name))
        score = row["score_arvor_pp"]
        row["posicao"] = (
            1
            + sum(
                round(p["score_arvor_pp"], 2) < round(score, 2)
                for p in rows
                if p["score_arvor_pp"] is not None
            )
            if score is not None
            else None
        )
        rows.append(row)
    return rows


def write(names):
    result = {
        "versao": 1,
        "conferido_em": EVIDENCE["conferido_em"],
        "score": "EAM F/L = (|F_pesquisa − F_urna| + |L_pesquisa − L_urna|)/2; menor é melhor, em pp dos válidos publicados pela casa. Não é percentual de acerto.",
        "janela": "Campo encerrado de 25/09 a 04/10; divulgação anterior à votação; última onda comparável por casa. Empates a 0,01 pp compartilham posição.",
        "limites": "Uma eleição, dois candidatos, datas e arredondamentos diferentes. Não mede competência permanente nem valida previsão futura. Sem válidos publicados confirmados, não há posição; conversão Arvor fica como diagnóstico separado.",
        "urna": {m: urna(m) for m in ("total", "validos")},
        "projecao_arvor_congelada": {
            k: v for k, v in FROZEN.items() if k not in ("ondas", "agregados")
        },
        "arvor_central_presidencial": {
            "fonte": AUDIT["previsao_casa"]["fonte"],
            **metrics(AUDIT["previsao_casa"]["central"]["validos"]),
        },
        "institutos": ranking(names),
    }
    # One institute per line keeps a large audit export reviewable and bounded.
    header = {k: v for k, v in result.items() if k != "institutos"}
    (ROOT / "docs/assets/reponderacao_score_arvor.json").write_text(
        json.dumps(header, ensure_ascii=False, indent=2)[:-2]
        + ',\n  "institutos": [\n'
        + ",\n".join(json.dumps(r, ensure_ascii=False) for r in result["institutos"])
        + "\n]}\n"
    )
    return result
