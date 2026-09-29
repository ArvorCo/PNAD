#!/usr/bin/env python3
"""Integra as íntegras nacionais de 28–29/09; reprodução offline e provas de leitura."""

import hashlib
import importlib
import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao"
WORK = BASE / "atualizacao_20260929"
POLLS = BASE / "pesquisas"
TODAY = "2026-09-29"
CONTROLS = {}


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def source(slug, pages, url=None):
    path = ROOT / f"data/originals/{slug}_092026_29/relatorio.pdf"
    payload = path.read_bytes()
    assert payload.startswith(b"%PDF")
    url = url or next(
        x["url"] for x in read(WORK / "downloads.json") if x["instituto"] == slug
    )
    return {
        "tipo": "relatorio",
        "pdf": str(path.relative_to(ROOT)),
        "url": url,
        "paginas": pages,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "total_paginas": path.with_suffix(".txt").read_text().count("\f"),
        "conferido_em": TODAY,
        "status": "Relatório completo arquivado e conferido.",
    }


def new(previous, slug, start, end, release, registry, n, pages, url=None):
    old = read(POLLS / f"{previous}.json")
    p = {k: deepcopy(old[k]) for k in ["instituto", "contratante", "metodo", "renda"]}
    p.update(
        id=f"{slug}_{end}",
        campo={"inicio": start, "fim": end},
        divulgacao=release,
        registro_tse=registry,
        n=n,
        publicado={},
        cruzamentos={},
        fonte=source(slug, pages, url),
    )
    p["renda"]["mes_precos"] = "202609"
    return p


def values(options, row):
    return dict(zip(options.split(), row, strict=True))


def table(options, rows, note):
    assert all(len(r) == len(options.split()) for r in rows)
    return {"opcoes": options.split(), "linhas": rows, "nota": note}


def control(p, turn, weights, rows, page):
    CONTROLS.setdefault(p["id"], {})[turn] = {
        "particao": "sexo",
        "pagina": page,
        "pesos": weights,
        "linhas": rows,
    }


def quaest():
    p = new(
        "quaest_2026-09-20",
        "quaest",
        "2026-09-24",
        "2026-09-27",
        "2026-09-28",
        "BR-06520/2026",
        2004,
        {
            "metodologia": 2,
            "perfil_renda": 204,
            "1t_topline": 18,
            "1t_renda": 24,
            "2t_topline": 32,
            "2t_renda": 37,
        },
        "https://quaest.com.br/relatorios/pesquisa-de-intencao-de-voto-para-presidente-rodada-6-28-09-2026/",
    )
    p["renda"].update(
        amostra_pct=[31, 42, 27],
        nota="Perfil desta onda, p. 204, confirmado visualmente. Renda familiar em salários mínimos de 2026; referência declarada inclui PNAD anual 2025, 1ª visita (p. 2).",
    )
    opts = "lula flavio outros indecisos branco_nulo"
    p["publicado"]["1t"] = values(opts, [39, 34, 12, 5, 10])
    p["publicado_detalhado"] = {
        "1t": values(
            "lula flavio caiado cury renan_santos zema samara edmilson grassi clariana rui avalanche hertz indecisos branco_nulo",
            [39, 34, 4, 4, 3, 1, 0, 0, 0, 0, 0, 0, 0, 5, 10],
        )
    }
    p["cruzamentos"]["1t"] = table(
        opts,
        [[52, 23, 8, 7, 10], [35, 36, 13, 6, 10], [30, 42, 13, 4, 11]],
        "P. 24, coluna 28/Set. Outros agrega todas as candidaturas além de Lula e Flávio, incluindo Cury. O topline da p. 18 foi agrupado na mesma partição, sem repartir artificialmente o ajuste.",
    )
    opts2 = "lula flavio branco_nulo indecisos"
    p["publicado"]["2t"] = values(opts2, [42, 42, 13, 3])
    p["cruzamentos"]["2t"] = table(
        opts2,
        [[55, 29, 11, 5], [39, 44, 14, 3], [34, 52, 12, 2]],
        "P. 37, coluna 28/Set. Branco/nulo inclui não vai votar; arredondamentos preservados.",
    )
    p["fonte"][
        "nota"
    ] = "PDF de 210 páginas recebido em Downloads. Transcrição visual das tabelas de renda, controlada por sexo (pp. 21, 34 e 201). Outros no 1º turno inclui Cury nesta onda."
    p["fonte"]["atualizado_em"] = TODAY
    control(p, "1t", [53, 47], [[40, 29], [37, 39]], 21)
    control(p, "2t", [53, 47], [[46, 37], [38, 48]], 34)
    return p


def atlas():
    p = new(
        "atlas_2026-09-22",
        "atlas",
        "2026-09-23",
        "2026-09-28",
        TODAY,
        "BR-04391/2026",
        5005,
        {"perfil_renda": 5, "1t_topline": 14, "1t_renda": "17–18", "2t_topline": 20},
    )
    opts = "lula flavio renan_santos cury caiado zema samara rui branco_nulo indecisos"
    p["renda"].update(
        amostra_pct=[19.5, 11.1, 26.7, 25.5, 17.3],
        nota="Perfil desta onda, p. 5, renda familiar nominal. Soma 100,1% por arredondamento; normalizada proporcionalmente pelo motor. Não reutiliza a onda anterior.",
    )
    p["publicado"]["1t"] = values(
        opts, [45.3, 42.2, 5.2, 2.0, 1.8, 0.9, 0.4, 0.1, 0.9, 1.2]
    )
    p["cruzamentos"]["1t"] = table(
        opts,
        [
            [37.7, 52.9, 1.8, 2.9, 0.8, 0.6, 0.1, 0, 1.3, 1.8],
            [48.5, 38.2, 3.2, 1.9, 1.5, 0.4, 0.7, 0, 0.7, 5.0],
            [39.7, 44.3, 8.9, 2.6, 1.3, 1.9, 0.6, 0, 0.5, 0.2],
            [47.6, 42.4, 5.4, 0.7, 1.9, 0.3, 0.3, 0.1, 0.9, 0.2],
            [57.4, 28.8, 4.7, 2.4, 3.4, 1.0, 0.5, 0.1, 1.1, 0.7],
        ],
        "Transcrição visual integral das pp. 17–18; colunas de renda na ordem do perfil. Samara e Rui individualizados conforme rodapé da p. 14. Arredondamentos preservados.",
    )
    p["publicado"]["2t"] = {"lula": 47.6, "flavio": 47.7, "branco_nulo": 4.8}
    p["sem_cruzamento"] = {
        "2t": "As pp. 20–22 publicam cenários, válidos e histórico, sem voto por renda do 2º turno. Os 4,8% agregam branco, nulo e não sei; o total impresso soma 100,1%. Não se transporta o ajuste de renda do 1º turno."
    }
    control(p, "1t", [47.9, 52.1], [[32.1, 52.4], [57.4, 32.9]], 17)
    return p


def palver():
    audit = importlib.import_module("palver-explorer-audit")
    explorer = BASE / "palver_explorer_20260929"
    audit.BASE = explorer
    wave = "05_pesquisa_2026_09_29"
    margins = {k: audit.recover_margin(wave, k) for k in ["inc_std", "sex_std"]}
    assert all(m["identified"] for m in margins.values())
    p = new(
        "palver_2026-09-23",
        "palver",
        "2026-09-24",
        "2026-09-27",
        TODAY,
        "BR-02990/2026",
        5000,
        {
            "metodologia": "17–21",
            "1t_topline": 30,
            "1t_renda": 31,
            "2t_topline": 37,
            "2t_renda": 38,
        },
    )
    p["fonte"].update(
        tipo="explorer",
        url_pdf=p["fonte"]["url"],
        url=f"https://www.palver.com.br/survey/explore?wave={wave}&question=lula_flavio&breakdown=inc_std",
        onda_explorer=wave,
        snapshot=str(explorer.relative_to(ROOT)),
        nota="Onda 5. PDF e tabelas exatas do Explorer arquivados. Perfil ponderado recuperado por sistema linear de posto completo e validado pelo n efetivo. Datas do campo conforme p. 21 do PDF.",
    )
    p["renda"].update(
        amostra_pct=margins["inc_std"]["weighted_pct"],
        perfil_tipo="perfil_ponderado_reconstituido",
        nota="Margem ponderada recuperada das tabelas exatas da onda 5; recomposição dos dois turnos e n efetivo conferidos. Contagens brutas não são os pesos de composição.",
    )
    names = importlib.import_module("palver-explorer-integrate").NAMES
    for turn, question in audit.BALLOTS.items():
        tot = audit.table(wave, question)
        inc = audit.table(wave, question, "inc_std")
        sex = audit.table(wave, question, "sex_std")
        p["publicado"][turn] = {
            names[c["answer"]]: c["share"] * 100 for c in tot["cells"]
        }
        p["cruzamentos"][turn] = {
            "opcoes": [names[a] for a in inc["answers"]],
            "linhas": (audit.matrix(inc).T * 100).tolist(),
            "nota": "Extração programática das tabelas exatas do Explorer, onda 5, todas as alternativas disponíveis.",
            "proveniencia": {
                kind: read(explorer / wave / f"{question}--{key}.json")["source"]
                for kind, key in [("total", "total"), ("renda", "inc_std")]
            },
        }
        control(
            p,
            turn,
            margins["sex_std"]["weighted_pct"],
            (
                audit.matrix(sex, ["Lula (PT)", "Flávio Bolsonaro (PL)"]).T * 100
            ).tolist(),
            "Explorer: sex_std",
        )
    p["publicado_pdf"] = {
        "1t": {"lula": 44, "flavio": 44},
        "2t": {"lula": 45, "flavio": 47},
    }
    dump(WORK / "palver-margens.json", margins)
    return p


def gerp():
    p = new(
        "gerp_2026-09-16",
        "gerp",
        "2026-09-24",
        "2026-09-28",
        TODAY,
        "BR-03929/2026",
        2400,
        {
            "metodologia": 7,
            "perfil_renda": 8,
            "1t_topline": 13,
            "1t_renda": 15,
            "2t_topline": 22,
            "2t_renda": 24,
        },
    )
    p["renda"].update(
        amostra_pct=[23, 23, 33, 14, 5, 2],
        nota="Perfil ponderado desta onda, p. 8, confirmado visualmente. As bases de campo das pp. 15 e 24 não substituem esses pesos; percentuais das tabelas explicitamente ponderados.",
    )
    pages = (ROOT / p["fonte"]["pdf"]).with_suffix(".txt").read_text().split("\f")
    for turn, page, opts in [
        (
            "1t",
            15,
            "flavio lula cury caiado renan_santos samara zema branco_nulo indecisos",
        ),
        ("2t", 24, "flavio lula branco_nulo indecisos"),
    ]:
        rows = [
            [int(v) for v in re.findall(r"(\d+)%", line)]
            for line in pages[page - 1].splitlines()
            if len(re.findall(r"(\d+)%", line)) == 14
        ]
        assert len(rows) == len(opts.split()), (turn, rows)
        p["publicado"][turn] = values(opts, [r[0] for r in rows])
        p["cruzamentos"][turn] = table(
            opts,
            list(map(list, zip(*(r[-6:] for r in rows), strict=True))),
            f"Extração nativa da p. {page}, conferida visualmente. Arredondamentos preservados; controle independente por sexo na mesma página.",
        )
        li = opts.split().index("lula")
        fi = opts.split().index("flavio")
        control(
            p,
            turn,
            [47, 53],
            [[rows[li][1], rows[fi][1]], [rows[li][2], rows[fi][2]]],
            page,
        )
    p["publicado"]["2t"]["indecisos"] = 1
    p["fonte"].update(
        atualizado_em=TODAY,
        nota="Divergência documental no 2º turno: a p. 22 informa 1% de indecisos, enquanto a coluna TOTAL da p. 24 informa 2%. Preservamos o topline da p. 22 como âncora e a tabela da p. 24 no cruzamento. As candidaturas omitidas no 1º turno são zero no total publicado; não se inventam células por renda.",
    )
    return p


def vox():
    p = {
        "id": "vox_brasil_2026-09-28",
        "instituto": "Vox Brasil",
        "contratante": "Instituto Vox Brasil, recursos próprios",
        "metodo": "presencial domiciliar",
        "campo": {"inicio": "2026-09-26", "fim": "2026-09-28"},
        "divulgacao": TODAY,
        "n": 2100,
        "registro_tse": "BR-00895/2026",
        "fonte": source(
            "vox",
            {
                "metodologia": 2,
                "perfil_renda": 6,
                "comparecimento": 7,
                "1t_topline": 8,
                "2t_topline": 9,
            },
            "https://static.poder360.com.br/uploads/2026/09/pesquisa-vox-nacional-29set2026.pdf",
        ),
        "cruzamentos": {},
        "ignorar": True,
    }
    p["publicado"] = {
        "1t": values(
            "lula flavio caiado renan_santos cury zema edmilson grassi avalanche clariana rui hertz samara branco_nulo indecisos",
            [41.1, 37.8, 3.8, 2.7, 2.2, 1.8, 0.2, 0.1, 0, 0, 0, 0, 0, 3.5, 6.8],
        ),
        "2t": values("lula flavio branco_nulo indecisos", [44.7, 45.2, 6.8, 3.3]),
    }
    p["motivo"] = (
        "A íntegra de 28 páginas publica perfil econômico (p. 6) e disposição de comparecer (p. 7), mas nenhum cruzamento de voto por renda ou comparecimento por candidato. Sem esses cruzamentos, não há ajuste de renda nem nova propensão de presença identificável para o modelo."
    )
    return p


def main():
    engine = importlib.import_module("reponderacao-pnad")
    bench = engine.Benchmark()
    ipca = engine.load_ipca()
    polls = [quaest(), atlas(), palver(), gerp(), vox()]
    checks = []
    for p in polls:
        if not p.get("ignorar"):
            result = engine.process_poll(p, bench, ipca)
            for turn, r in result["turnos"].items():
                c = CONTROLS[p["id"]][turn]
                c["recomposto"] = {
                    k: sum(
                        w * row[j]
                        for w, row in zip(c["pesos"], c["linhas"], strict=True)
                    )
                    / sum(c["pesos"])
                    for j, k in enumerate(["lula", "flavio"])
                }
                c["residuo_max_pp"] = max(
                    abs(c["recomposto"][k] - p["publicado"][turn][k])
                    for k in ["lula", "flavio"]
                )
                assert r["residuo_max"] <= 1.5, (p["id"], turn, r["residuo_max"])
                assert c["residuo_max_pp"] <= 1.5, (p["id"], turn, c)
                checks.append(
                    {
                        "id": p["id"],
                        "turno": turn,
                        "renda_residuo_max_pp": r["residuo_max"],
                        "controle_independente": c,
                        "ajustado": r["cenarios"]["pessoas16_efetivo"]["ajustado"],
                    }
                )
        dump(POLLS / f"{p['id']}.json", p)
    inventory = {
        "data": TODAY,
        "fontes": [
            {
                "id": p["id"],
                "fonte": p["fonte"],
                "ajustavel": not p.get("ignorar", False),
            }
            for p in polls
        ],
        "controles": checks,
        "escopo": "Atualização do agregador; novos dossiês Quaest e Atlas não produzidos nesta etapa.",
    }
    dump(WORK / "auditoria.json", inventory)
    dump(ROOT / "docs/assets/reponderacao_20260929.json", inventory)
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
