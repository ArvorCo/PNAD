#!/usr/bin/env python3
"""Integra as fontes conferidas em 02/10, sem transformar PDFs tardios em ondas."""

import hashlib
import importlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao"
WORK = BASE / "atualizacao_20261002"
POLLS = BASE / "pesquisas"
TODAY = "2026-10-02"
CONTROLS = {}
DF_PAGES = {
    "espontanea": [42, 43],
    "estimulada": [44, 45, 46],
    "validos": [47, 48],
    "numero_urna": [49],
    "rejeicao": [50, 51, 52],
    "turno2_flavio": [53],
    "turno2_caiado": [54],
    "turno2_zema": [55],
    "turno2_renan": [56],
    "turno2_cury": [57],
    "definicao": [58],
    "segunda_opcao": [59, 60, 61],
    "avaliacao": [62],
    "aprovacao": [63],
    "bets": [64],
    "apostadores": [65, 66],
    "canetas": [67],
    "bolsa_familia": [68],
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def source(slug, pages):
    item = next(x for x in read(WORK / "downloads.json") if x["instituto"] == slug)
    payload = (ROOT / item["arquivo"]).read_bytes()
    assert payload.startswith(b"%PDF")
    assert hashlib.sha256(payload).hexdigest() == item["sha256"]
    assert len(payload) == item["bytes"]
    return {
        "tipo": "relatorio",
        "pdf": item["arquivo"],
        "url": item["url"],
        "paginas": pages,
        "total_paginas": item["paginas"],
        "sha256": item["sha256"],
        "bytes": item["bytes"],
        "conferido_em": TODAY,
        "status": "Íntegra arquivada e conferida.",
    }


def values(options, row):
    return dict(zip(options.split(), row, strict=True))


def table(options, rows, note):
    assert all(len(row) == len(options.split()) for row in rows)
    return {"opcoes": options.split(), "linhas": rows, "nota": note}


def control(poll, turn, weights, rows, page, dimension="sexo"):
    CONTROLS.setdefault(poll["id"], {}).setdefault(turn, []).append(
        {
            "particao": dimension,
            "pagina": page,
            "pesos": weights,
            "linhas": rows,
        }
    )


def new(previous, slug, start, end, release, registry, n, pages):
    old = read(POLLS / f"{previous}.json")
    poll = {k: deepcopy(old[k]) for k in ["instituto", "contratante", "metodo"]}
    if "renda" in old:
        poll["renda"] = deepcopy(old["renda"])
        poll["renda"].pop("bases", None)
        poll["renda"].pop("amostra_pct", None)
        poll["renda"]["mes_precos"] = "202610"
    poll.update(
        id=f"{slug}_{end}",
        campo={"inicio": start, "fim": end},
        divulgacao=release,
        registro_tse=registry,
        n=n,
        publicado={},
        cruzamentos={},
        fonte=source(slug, pages),
    )
    return poll


def datafolha():
    p = new(
        "datafolha_2026-09-23",
        "datafolha",
        "2026-09-29",
        "2026-10-01",
        "2026-10-01",
        "BR-08039/2026",
        2506,
        {
            "metodologia": 2,
            "perfil_renda": 40,
            "1t_topline": 11,
            "1t_renda": 45,
            "2t_topline": 18,
            "2t_renda": 53,
        },
    )
    parser = importlib.import_module("datafolha-21092026-extract")
    parser.PAGES = DF_PAGES
    tables = parser.extract(ROOT / p["fonte"]["pdf"])
    for t in tables.values():
        for block in t["blocks"].values():
            block["annex_page"] = block["pdf_page"] - 35
    extraction = "analysis/reponderacao/datafolha_20261001_cruzamentos.json"
    dump(ROOT / extraction, {"fonte": p["fonte"], "tabelas": tables})
    # Rótulos conferidos, em vez de transportar a ordem dos candidatos de outra onda.
    names = {
        "Lula (PT)": "lula",
        "Flavio Bolsonaro (PL)": "flavio",
        "Escritor Augusto Cury (AVANTE)": "cury",
        "Ronaldo Caiado (PSD)": "caiado",
        "Renan Santos (MISSÃO)": "renan_santos",
        "Zema (NOVO)": "zema",
        "Samara (UP)": "samara",
        "Veterinário Wilson Grassi (DEMOCRATA)": "grassi",
        "Edmilson Costa (PCB)": "edmilson",
        "Rui Costa Pimenta (PCO)": "rui",
        "Hertz Dias (PSTU)": "hertz",
        "Clariana Barao (DC)": "clariana",
        "Leonardo Avalanche (PRTB)": "avalanche",
        "Em branco/ Nulo/ Nenhum": "branco_nulo",
        "Indecisos": "indecisos",
    }
    income = ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"]
    first = tables["estimulada"]["blocks"]["bloco2"]
    second = tables["turno2_flavio"]["blocks"]["bloco2"]
    assert first["base"] == second["base"]
    p["renda"]["bases"] = [first["base"][c] for c in income]
    missing = p["n"] - sum(p["renda"]["bases"])
    p["renda"]["nao_publicada_n"] = missing
    p["renda"]["nota"] = (
        f"Bases ponderadas da intenção de voto, pp. 45 e 53: 1.209/856/344, "
        f"somam 2.409; {missing} dos 2.506 casos ({100*missing/p['n']:.2f}%) "
        "não aparecem no cruzamento de renda. Normalização entre renda declarada "
        "e delta ancorado no placar nacional; não identifica o voto dos ausentes. "
        "Cartão em salários mínimos de 2026. Não usa bases de motivação do voto."
    )
    for turn, key in [("1t", "estimulada"), ("2t", "turno2_flavio")]:
        blocks = tables[key]["blocks"]
        rows = blocks["bloco2"]["rows"]
        mapping = (
            names
            if turn == "1t"
            else {
                "Lula (PT)": "lula",
                "Flavio Bolsonaro (PL)": "flavio",
                "Em branco/nulo/nenhum": "branco_nulo",
                "Indecisos": "indecisos",
            }
        )
        assert set(rows) == set(mapping)
        options = [mapping[label] for label in rows]
        p["publicado"][turn] = {mapping[k]: r["Total"] for k, r in rows.items()}
        p["cruzamentos"][turn] = table(
            " ".join(options),
            [[r[c] if r[c] is not None else 0 for r in rows.values()] for c in income],
            "Extração automática do anexo inteiro, texto nativo. Traço explícito "
            "convertido em zero apenas na conta; nenhuma célula vazia imputada.",
        )
        for block_key, cols, dim in [
            ("bloco1", ["Masculino", "Feminino"], "sexo"),
            ("bloco3", ["Sudeste", "Sul", "Nordeste", "Centro-Oeste/Norte"], "regiao"),
        ]:
            b = blocks[block_key]
            control(
                p,
                turn,
                [b["base"][c] for c in cols],
                [[b["rows"][label][c] for label in list(mapping)[:2]] for c in cols],
                b["pdf_page"],
                dim,
            )
    p["fonte"].update(
        relatorio_completo=TODAY,
        nota="Divulgação original em 01/10; íntegra de 68 páginas disponibilizada "
        "em 02/10. Extração automática das 18 tabelas do anexo, controlada por "
        "gênero e região. A chegada do PDF não cria uma segunda onda.",
        extracao=extraction,
    )
    return p


def realtime():
    p = new(
        "realtime_2026-09-23",
        "realtime",
        "2026-09-26",
        "2026-09-30",
        "2026-10-01",
        "BR-09503/2026",
        2000,
        {
            "metodologia": 2,
            "perfil_renda": 3,
            "1t_topline": 8,
            "1t_renda": 11,
            "2t_topline": 17,
        },
    )
    p["renda"].update(
        amostra_pct=[46, 33, 21],
        nota="Perfil desta onda, p. 3. O relatório não distingue bases brutas e "
        "ponderadas. Percentuais conferidos na íntegra, sem copiar a onda anterior.",
    )
    options = "lula flavio cury renan_santos caiado zema branco_nulo indecisos"
    p["publicado"]["1t"] = values(options, [43, 39, 3, 4, 3, 1, 3, 3]) | {"outros": 1}
    p["cruzamentos"]["1t"] = table(
        options,
        [
            [56, 26, 6, 2, 1, 1, 4, 3],
            [36, 48, 3, 4, 2, 1, 2, 3],
            [25, 52, 1, 10, 8, 2, 1, 1],
        ],
        "P. 11, conferência visual contra o texto nativo. Outros tem 1% nacional, "
        "mas a faixa superior está sem número impresso: não entra no ajuste e não "
        "vira zero. Tabela parcial preservada sem renormalização.",
    )
    p["publicado"]["2t"] = values("lula flavio branco_nulo indecisos", [45, 46, 5, 4])
    p["sem_cruzamento"] = {
        "2t": "As pp. 17–24 trazem os cenários agregados, "
        "sem voto por renda do 2º turno. Renda nas perguntas posteriores trata "
        "de definição/motivação, outro universo. Não se transfere o ajuste do 1º turno."
    }
    control(p, "1t", [47, 53], [[36, 47], [49, 31]], 9)
    return p


def indexa():
    p = {
        "id": "indexa_2026-09-29",
        "instituto": "Indexa/Broadcast",
        "contratante": "Indexa/Broadcast (Agência Estado); contratante não individualizado na ficha",
        "metodo": "telefônico CATI",
        "registro_tse": "BR-00698/2026",
        "n": 2000,
        "campo": {"inicio": "2026-09-27", "fim": "2026-09-29"},
        "divulgacao": "2026-09-30",
        "publicado": {},
        "cruzamentos": {},
        "renda": {
            "unidade": "salarios_minimos",
            "ano_referencia": 2026,
            "mes_precos": "202609",
            "amostra_pct": [42, 38, 20],
            "faixas": [
                {"rotulo": "Até 2 SM", "max": 2},
                {"rotulo": "2 a 5 SM", "max": 5},
                {"rotulo": "Mais de 5 SM", "max": None},
            ],
            "nota": "Perfil desta onda, p. 4: 42/38/20. PA significa percentual "
            "na amostra; a publicação não separa perfil bruto e ponderado. "
            "A referência de renda declarada é PNADC 2024; cartão em SM atuais.",
        },
        "fonte": source(
            "indexa",
            {
                "metodologia": 3,
                "perfil_renda": 4,
                "1t_topline": 8,
                "1t_renda": 11,
                "2t_topline": 18,
                "2t_renda": 21,
            },
        ),
    }
    # P. 11. Quatro candidaturas com 0% no topline não têm coluna na tabela;
    # preservamos essa ausência, sem inventar voto por renda para elas.
    opts = "lula flavio cury caiado renan_santos zema edmilson hertz rui branco_nulo indecisos"
    p["publicado"]["1t"] = values(opts, [39, 34, 4, 4, 3, 1, 0, 0, 0, 8, 7])
    p["publicado"]["1t"].update(clariana=0, samara=0, grassi=0, avalanche=0)
    p["cruzamentos"]["1t"] = table(
        opts,
        [
            [43, 27, 3, 4, 3, 1, 0, 0, 0, 9, 10],
            [37, 37, 5, 4, 4, 1, 0, 0, 0, 8, 4],
            [36, 40, 4, 2, 5, 1, 0, 0, 0, 6, 6],
        ],
        "P. 11. Branco/nulo agrega não iria votar: 5+4, 4+4 e 4+2; "
        "no total da p. 8, 4+4. Quatro candidaturas zero no total não têm coluna "
        "por renda e não recebem células imputadas. Inteiros preservados.",
    )
    opts2 = "lula flavio branco_nulo indecisos"
    p["publicado"]["2t"] = values(opts2, [43, 42, 11, 4])
    p["cruzamentos"]["2t"] = table(
        opts2,
        [[47, 34, 14, 5], [41, 45, 12, 2], [39, 48, 9, 4]],
        "P. 21. Branco/nulo agrega não iria votar: 9+5, 8+4 e 5+4; "
        "no total da p. 18, 7+4. Mesma partição no total e nos recortes.",
    )
    p["fonte"].update(
        nota="PDF de 94 páginas sem texto nativo. OCR integral arquivado como "
        "localizador; transcrição visual das pp. 4, 8, 10–11 e 18, 20–21, "
        "provada por recomposição independente por gênero. PA e pesos "
        "finais não são distinguidos. Não iria votar agregado a branco/nulo.",
        ocr="data/originals/indexa_092026_30/ocr-paginas.txt",
    )
    control(p, "1t", [47, 53], [[35, 36], [42, 33]], 10)
    control(p, "2t", [47, 53], [[39, 44], [45, 40]], 20)
    return p


def futura():
    p = read(POLLS / "futura_2026-09-29.json")
    p["n"] = 2000
    p["metodo"] = "telefônico CATI"
    p["contratante"] = (
        "Futura/100% Cidades (marcas na íntegra); contratante não individualizado na ficha"
    )
    p["fonte"] = source(
        "futura",
        {
            "metodologia": 4,
            "perfil_renda": 7,
            "1t_topline": 22,
            "1t_cruzamentos": "23–25",
            "2t_topline": 29,
            "2t_cruzamentos": 30,
        },
    ) | {
        "relatorio_completo": "2026-09-30",
        "atualizado_em": TODAY,
        "complementos": [
            {
                "url": "assets/futura_20260930_prints.json",
                "rotulo": "Transcrição histórica dos oito prints",
            }
        ],
        "nota": "Íntegra de 46 páginas encontrada em 02/10, da mesma onda "
        "divulgada em 30/09. P. 4 confirma 2.000 entrevistas e campo "
        "25–29/09. Substitui a ficha incompleta dos prints, sem criar "
        "nova onda nem entrar na média. Nenhuma tabela de voto por renda.",
    }
    p["motivo"] = (
        "A íntegra de 46 páginas publica o perfil de renda (p. 7), "
        "mas cruza o voto somente por gênero, região, idade e posição política "
        "(pp. 23–25 e 30). Falta voto por renda; 10% não declaram renda. "
        "A publicação não distingue perfil bruto e ponderado."
    )
    p["notas"] = (
        "Ficha técnica agora conferida na íntegra. A data de aquisição "
        "em 02/10 não muda a divulgação de 30/09. Não há perfil de comparecimento por candidato."
    )
    return p


def vox():
    p = new(
        "vox_brasil_2026-09-28",
        "vox_brasil",
        "2026-09-29",
        "2026-10-01",
        TODAY,
        "BR-00148/2026",
        2100,
        {"metodologia": 2, "perfil_renda": 6, "1t_topline": 7, "2t_topline": 8},
    )
    p["publicado"]["1t"] = values(
        "lula flavio caiado renan_santos zema cury edmilson grassi avalanche clariana rui hertz samara branco_nulo indecisos",
        [40.4, 41.2, 3.3, 2.2, 1.3, 1.2, 0.2, 0, 0, 0, 0, 0, 0, 3.2, 7],
    )
    p["publicado"]["2t"] = values(
        "lula flavio branco_nulo indecisos", [45.2, 48.2, 2.5, 4.1]
    )
    p["perfil_economico_publicado"] = {
        "pagina": 6,
        "faixas_sm": [2, 5, 10, None],
        "percentuais": [83.9, 12.4, 2.8, 0.9],
    }
    p.update(
        ignorar=True,
        motivo="Íntegra de 14 páginas: perfil econômico da p. 6 é "
        "83,9/12,4/2,8/0,9%, mas não há voto por renda. Sem esse cruzamento "
        "não há reponderação nem propensão de comparecimento por candidato.",
    )
    return p


def alfa():
    path = ROOT / "data/originals/alfa_092026_24/divulgacao_1t.html"
    payload = path.read_bytes()
    return {
        "id": "alfa_2026-09-23",
        "instituto": "Alfa Inteligência/TMC",
        "contratante": "TMC",
        "metodo": "presencial, conglomerados em dois estágios",
        "campo": {"inicio": "2026-09-18", "fim": "2026-09-23"},
        "divulgacao": "2026-09-24",
        "registro_tse": "BR-02512/2026",
        "n": 2700,
        "fonte": {
            "tipo": "materia",
            "arquivo": str(path.relative_to(ROOT)),
            "url": "https://tmc.com.br/politica/tmc-instituto-alfa-flavio-bolsonaro-cresce-no-1o-turno-e-distancia-para-lula-cai-pela-metade/",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "conferido_em": TODAY,
            "complementos": [
                {
                    "url": "https://tmc.com.br/politica/alfa-lula-e-flavio-bolsonaro-empatam-com-43-no-2o-turno/",
                    "rotulo": "Divulgação do segundo turno pelo contratante",
                }
            ],
        },
        "publicado": {
            "1t": values(
                "lula flavio cury caiado renan_santos zema outros branco_nulo indecisos",
                [40, 33, 6, 5, 3, 1, 1, 6, 5],
            ),
            "2t": values("lula flavio branco_nulo indecisos", [43, 43, 7, 7]),
        },
        "cruzamentos": {},
        "ignorar": True,
        "motivo": "Pesquisa nacional ausente do inventário anterior. Publicações "
        "do contratante arquivadas; íntegra e voto por renda não "
        "localizados. Apenas placares publicados, sem ajuste imputado.",
    }


def main():
    engine = importlib.import_module("reponderacao-pnad")
    bench, ipca = engine.Benchmark(), engine.load_ipca()
    polls = [datafolha(), realtime(), indexa(), futura(), vox(), alfa()]
    checks = []
    for p in polls:
        if not p.get("ignorar"):
            result = engine.process_poll(p, bench, ipca)
            for turn, r in result["turnos"].items():
                controls = CONTROLS[p["id"]][turn]
                for c in controls:
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
                    assert c["residuo_max_pp"] <= 1.5, (p["id"], turn, c)
                assert r["residuo_max"] <= 1.5, (p["id"], turn, r["residuo_max"])
                checks.append(
                    {
                        "id": p["id"],
                        "turno": turn,
                        "renda_residuo_max_pp": r["residuo_max"],
                        "controles_independentes": controls,
                        "ajustado": r["cenarios"][engine.MAIN_SERIES]["ajustado"],
                    }
                )
                print(
                    p["id"],
                    turn,
                    "resíduo",
                    r["residuo_max"],
                    "ajustado",
                    checks[-1]["ajustado"]["lula"],
                    checks[-1]["ajustado"]["flavio"],
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
        "regra": "Divulgação original define a janela; íntegra tardia apenas "
        "completa a mesma ficha. Sem voto por renda não há ajuste.",
        "varredura": (
            read(WORK / "varredura.json") if (WORK / "varredura.json").exists() else []
        ),
    }
    dump(WORK / "auditoria.json", inventory)
    dump(ROOT / "docs/assets/reponderacao_20261002.json", inventory)


if __name__ == "__main__":
    main()
