#!/usr/bin/env python3
"""Integra fontes de 23–24/09 e completa a Quaest de 21/09.

As páginas são físicas, começando em 1. Transcrições de imagens ficam
explícitas; tabelas nativas e Explorer são extraídos sem digitação de células.
Reprodução offline, depois de arquivar os documentos listados no manifesto.
"""

import hashlib
import importlib.util
import json
import re
import subprocess
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao"
WORK = BASE / "atualizacao_20260924"
POLLS = BASE / "pesquisas"
TODAY = "2026-09-24"
EXPLORER = BASE / "palver_explorer_20260924"
WAVE = "04_pesquisa_2026_09_24"
PODER_IMAGE = "pd-pesquisa-eleitoral-intencao-presidente-23-set-2026-06-scaled.jpg"
CONTROLS = {}


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def source(slug, pages, filename="relatorio.pdf", url=None):
    record = next(
        (x for x in read(WORK / "downloads.json") if x["instituto"] == slug), {}
    )
    path = ROOT / f"data/originals/{slug}_092026_24/{filename}"
    payload = path.read_bytes()
    assert payload.startswith(b"%PDF")
    text = subprocess.check_output(["pdftotext", "-layout", str(path), "-"], text=True)
    path.with_suffix(".txt").write_text(text)
    return {
        "tipo": "relatorio",
        "pdf": str(path.relative_to(ROOT)),
        "url": url or record["url"],
        "paginas": pages,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "total_paginas": text.count("\f"),
        "conferido_em": TODAY,
        "status": "Relatório completo arquivado e conferido.",
    }, text.split("\f")


def template(previous, slug, start, end, release, registry, n, pages):
    old = read(POLLS / f"{previous}.json")
    poll = {
        k: deepcopy(old[k]) for k in ["instituto", "contratante", "metodo", "renda"]
    }
    poll.update(
        id=f"{slug}_{end}",
        campo={"inicio": start, "fim": end},
        divulgacao=release,
        registro_tse=registry,
        n=n,
        publicado={},
        cruzamentos={},
    )
    poll["fonte"], text = source(slug, pages)
    poll["renda"]["mes_precos"] = "202609"
    return poll, text


def table(options, rows, note):
    names = options.split()
    assert all(len(row) == len(names) for row in rows)
    return {"opcoes": names, "linhas": rows, "nota": note}


def published(options, values):
    return dict(zip(options.split(), values, strict=True))


def control(poll, turn, weights, rows, page):
    CONTROLS.setdefault(poll["id"], {})[turn] = {
        "particao": "sexo",
        "pagina": page,
        "pesos": weights,
        "linhas": rows,
    }


def atlas():
    p, _ = template(
        "atlas_2026-09-16",
        "atlas",
        "2026-09-17",
        "2026-09-22",
        "2026-09-23",
        "BR-04739/2026",
        5015,
        {"perfil_renda": 5, "1t_topline": 14, "1t_renda": "17–18", "2t_topline": 21},
    )
    opts = "lula flavio renan_santos cury caiado zema samara clariana branco_nulo indecisos"
    # PDF pp. 17–18: cinco colunas de renda, na ordem do perfil da p. 5.
    rows = [
        [34.3, 52.9, 3.6, 4.7, 0.6, 0.1, 0.5, 2.1, 0.6, 0.6],
        [41.3, 52.0, 3.1, 0.6, 1.4, 0.4, 0.6, 0, 0.5, 0.2],
        [40.5, 49.9, 4.9, 0.9, 1.6, 0.8, 0.1, 0, 1.0, 0.3],
        [51.8, 37.4, 5.1, 1.8, 1.4, 1.5, 0.5, 0, 0.1, 0.4],
        [61.2, 25.7, 5.1, 2.2, 1.7, 1.4, 0.6, 0, 1.0, 1.0],
    ]
    p["renda"].update(
        amostra_pct=[19.6, 10.5, 27.1, 26.0, 16.8],
        nota="Perfil desta onda, p. 5, em renda familiar nominal. Não transporta os pesos da onda anterior. As cinco faixas somam 100%.",
    )
    p["publicado"] = {
        "1t": published(opts, [45.8, 43.4, 4.5, 2.1, 1.3, 0.9, 0.4, 0.4, 0.7, 0.5]),
        "2t": {"lula": 47.7, "flavio": 47.4, "branco_nulo": 4.9},
    }
    p["cruzamentos"]["1t"] = table(
        opts,
        rows,
        "Transcrição visual integral das pp. 17–18. Samara e Clariana individualizadas conforme o rodapé da p. 14. Arredondamentos preservados.",
    )
    p["sem_cruzamento"] = {
        "2t": "O relatório publica os cenários, votos válidos e histórico nas pp. 21–23, sem cruzamento de renda do 2º turno. Os 4,9% agregam branco, nulo e não sei; não há separação dessas respostas."
    }
    control(p, "1t", [46.6, 53.4], [[30.7, 56.0], [59.0, 32.3]], 17)
    return p


def realtime():
    p, pages = template(
        "realtime_2026-08-31",
        "realtime",
        "2026-09-19",
        "2026-09-23",
        TODAY,
        "BR-04202/2026",
        2000,
        {
            "metodologia": 2,
            "perfil_renda": 3,
            "1t_topline": 8,
            "1t_renda": 11,
            "2t_topline": 15,
        },
    )
    p["renda"].update(
        amostra_pct=[46, 33, 21],
        nota="Perfil da onda atual, p. 3. O relatório não distingue bases brutas e ponderadas. As faixas somam 100%.",
    )
    opts = "lula flavio cury renan_santos caiado zema branco_nulo indecisos"
    # A linha Outros tem uma célula sem rótulo; preservar a lacuna, não inventar zero.
    lines = [
        line for line in pages[10].splitlines() if len(re.findall(r"(\d+)%", line)) == 3
    ]
    values = [[int(v) for v in re.findall(r"(\d+)%", line)] for line in lines]
    assert len(values) == 8
    p["publicado"] = {
        "1t": published(opts, [41, 37, 6, 6, 2, 1, 3, 3]),
        "2t": published("lula flavio branco_nulo indecisos", [44, 45, 8, 3]),
    }
    p["publicado"]["1t"]["outros"] = 1
    p["cruzamentos"]["1t"] = table(
        opts,
        list(map(list, zip(*values, strict=True))),
        "Extração nativa da p. 11, conferida visualmente. Outros (1% nacional) não entra no ajuste: a faixa superior está sem valor impresso. Não se renormaliza a tabela parcial.",
    )
    p["sem_cruzamento"] = {
        "2t": "As pp. 15–22 trazem cenários agregados, sem voto por renda do 2º turno. O ajuste do primeiro não é transferido ao segundo."
    }
    control(p, "1t", [47, 53], [[36, 45], [46, 30]], 9)
    return p


def futura():
    p, _ = template(
        "futura_2026-09-15",
        "futura",
        "2026-09-19",
        "2026-09-23",
        TODAY,
        "BR-05268/2026",
        2000,
        {"metodologia": 4, "perfil_renda": 6, "1t_topline": 21, "2t_topline": 25},
    )
    p["renda"].update(
        amostra_pct=[28.9, 21.2, 25.0, 10.0, 5.7],
        nota="Perfil da p. 6: as faixas somam 90,8%; 9,2% não declaram renda. NS/NR não é faixa de renda.",
    )
    p["publicado"] = {
        "1t": published(
            "flavio lula caiado cury renan_santos zema samara rui avalanche edmilson hertz clariana branco_nulo indecisos",
            [40.4, 38.4, 5.7, 5.6, 2.4, 0.9, 0.5, 0.3, 0.2, 0.1, 0.1, 0, 2.1, 3.2],
        ),
        "2t": published("lula flavio branco_nulo indecisos", [43.7, 49.4, 5.6, 1.3]),
    }
    p.update(
        ignorar=True,
        motivo="A p. 6 publica o perfil de renda, mas as pp. 22–24 e 26 cruzam voto por sexo, região, idade e posição política, sem renda. Não há reponderação de nenhum turno com os dados publicados nesta íntegra.",
    )
    return p


def poderdata():
    p, pages = template(
        "poderdata_2026-09-16",
        "poderdata",
        "2026-09-20",
        "2026-09-23",
        TODAY,
        "BR-01739/2026",
        3000,
        {"metodologia": 2, "perfil_renda": 4, "1t_renda": 12, "2t_topline": 18},
    )
    p["renda"].update(
        amostra_pct=[46, 33, 21],
        nota="Perfil da onda atual, p. 4: 46/33/21. A primeira faixa inclui sem rendimentos. Perfil conferido na imagem do PDF.",
    )
    opts = "lula flavio cury renan_santos caiado zema samara rui clariana avalanche hertz edmilson grassi branco_nulo indecisos"
    rows = [
        [int(v) for v in re.findall(r"(\d+)%", line)]
        for line in pages[11].splitlines()
        if len(re.findall(r"(\d+)%", line)) == 4
        and not line.strip().startswith("Total")
    ]
    assert len(rows) == len(opts.split())
    p["publicado"]["1t"] = published(opts, [r[-1] for r in rows])
    p["cruzamentos"]["1t"] = table(
        opts,
        list(map(list, zip(*(r[:3] for r in rows), strict=True))),
        "Extração nativa da p. 12; conferência por sexo na p. 8.",
    )
    p["publicado"]["2t"] = published(
        "lula flavio branco_nulo indecisos", [45, 46, 7, 2]
    )
    p["cruzamentos"]["2t"] = table(
        "lula flavio",
        [[50, 38], [41, 52], [40, 54]],
        "Gráfico de estratificação publicado pelo PoderData em 24/09, campo 20–23/09. O PDF não traz este cruzamento. Branco/nulo e indecisos não são separados por renda; só Lula e Flávio são ajustados.",
    )
    image_path = ROOT / f"data/originals/poderdata_092026_24/{PODER_IMAGE}"
    p["fonte"]["complementos"] = [
        {
            "rotulo": "PoderData: 2º turno por renda",
            "url": f"https://static.poder360.com.br/uploads/2026/09/{PODER_IMAGE}",
            "arquivo": str(image_path.relative_to(ROOT)),
            "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        }
    ]
    p["fonte"]["paginas"]["2t_renda"] = "gráfico complementar de 24/09"
    p["notas"] = (
        "O cruzamento do 1º turno recompõe Flávio em 40,47%, contra 39% publicado, resíduo de 1,47 pp. A conta preserva o placar publicado e acrescenta apenas o delta da troca de renda. No 2º turno o maior resíduo é 0,07 pp."
    )
    control(p, "1t", [47, 53], [[38, 45], [44, 34]], 8)
    control(p, "2t", [47, 53], [[40, 52], [49, 40]], "gráfico complementar de 24/09")
    return p


def quaest():
    p = read(POLLS / "quaest_2026-09-20.json")
    p.pop("sem_cruzamento", None)
    p["fonte"], _ = source(
        "quaest",
        {
            "metodologia": 2,
            "perfil_renda": 241,
            "1t_topline": 17,
            "1t_renda": 23,
            "2t_topline": 30,
            "2t_renda": 35,
        },
        filename="relatorio-instituto.pdf",
        url="https://quaest.com.br/wp-content/uploads/2026/09/QUAEST5PRESIDENCIAL2109.pdf",
    )
    p["fonte"]["atualizado_em"] = TODAY
    p["fonte"][
        "nota"
    ] = "Relatório de 247 páginas disponibilizado pelo instituto em 22/09 e integrado em 24/09. Mesma pesquisa divulgada em 21/09, não uma nova onda. Substitui a fonte parcial do G1."
    p["renda"].update(
        amostra_pct=[31, 42, 27],
        perfil_tipo="perfil_publicado",
        nota="Perfil final confirmado na p. 241: 31/42/27. A p. 2 declara PNAD anual 2025, 1ª visita. Renda de todos os moradores, incluindo benefícios e pensões. As cotas antes provisórias coincidem com o perfil publicado.",
    )
    opts = "lula flavio cury outros indecisos branco_nulo"
    p["publicado"]["1t"] = published(opts, [37, 33, 6, 9, 8, 7])
    p["cruzamentos"]["1t"] = table(
        opts,
        [[49, 23, 4, 6, 8, 10], [34, 33, 6, 9, 10, 8], [29, 41, 7, 11, 6, 5]],
        "P. 23, coluna 21/Set, rótulos impressos e legenda completa. Outros reúne as candidaturas além de Lula, Flávio e Cury; não é repartido em grupos. Cury acima de 5 SM é 7 no PDF, contra 8 na transcrição anterior do print do G1. A nova conta usa integralmente o PDF.",
    )
    opts2 = "lula flavio branco_nulo indecisos"
    p["publicado"]["2t"] = published(opts2, [41, 42, 14, 3])
    p["cruzamentos"]["2t"] = table(
        opts2,
        [[52, 30, 13, 5], [38, 43, 15, 4], [33, 53, 13, 1]],
        "P. 35, coluna 21/Set. Branco/nulo inclui não vai votar. Todas as respostas do cenário Lula × Flávio.",
    )
    p["notas"] = (
        "Íntegra de 247 páginas substitui os prints parciais. Dois turnos verificados por renda e sexo. Não se usa a data de obtenção do PDF como data da divulgação para calcular a janela."
    )
    control(p, "1t", [53, 47], [[37, 32], [39, 34]], 20)
    control(p, "2t", [53, 47], [[44, 37], [37, 48]], 32)
    return p


def palver():
    audit = module("palver-explorer-audit")
    audit.BASE = EXPLORER
    margins = {key: audit.recover_margin(WAVE, key) for key in ["inc_std", "sex_std"]}
    assert all(m["identified"] for m in margins.values())
    p, _ = template(
        "palver_2026-09-18",
        "palver",
        "2026-09-20",
        "2026-09-23",
        TODAY,
        "BR-09587/2026",
        5000,
        {
            "metodologia": 19,
            "1t_topline": 30,
            "1t_renda": 31,
            "2t_topline": 37,
            "2t_renda": 38,
        },
    )
    p["fonte"].update(
        tipo="explorer",
        url=f"https://www.palver.com.br/survey/explore?wave={WAVE}&question=lula_flavio&breakdown=inc_std",
        url_pdf=p["fonte"]["url"],
        onda_explorer=WAVE,
        snapshot=str(EXPLORER.relative_to(ROOT)),
        nota="Onda 4. PDF e tabelas públicas exatas do Explorer arquivados. Perfil ponderado recuperado por sistema linear de posto completo nos dois turnos e validado pelo n efetivo. Bases brutas não são pesos de composição.",
    )
    p["renda"].update(
        amostra_pct=margins["inc_std"]["weighted_pct"],
        perfil_tipo="perfil_ponderado_reconstituido",
        nota="Margem ponderada recuperada das tabelas exatas da onda 4. Recomposição dos dois turnos, sistema de posto completo e n efetivo conferidos; não usa as contagens brutas como pesos.",
    )
    names = module("palver-explorer-integrate").NAMES
    for turn, question in audit.BALLOTS.items():
        tot = audit.table(WAVE, question)
        inc = audit.table(WAVE, question, "inc_std")
        sex = audit.table(WAVE, question, "sex_std")
        p["publicado"][turn] = {
            names[c["answer"]]: c["share"] * 100 for c in tot["cells"]
        }
        p["cruzamentos"][turn] = {
            "opcoes": [names[a] for a in inc["answers"]],
            "linhas": (audit.matrix(inc).T * 100).tolist(),
            "nota": "Extração programática das tabelas exatas do Explorer, onda 4, todas as alternativas expostas.",
            "proveniencia": {
                kind: read(EXPLORER / WAVE / f"{question}--{key}.json")["source"]
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
        "1t": {"lula": 43, "flavio": 43},
        "2t": {"lula": 45, "flavio": 48},
    }
    dump(WORK / "palver-margens.json", margins)
    return p


def verita():
    current = next(
        x for x in read(WORK / "verita-catalogo.json") if "Brasil" in x["titulo"]
    )
    p = read(POLLS / "verita_2026-09-04.json")
    p.update(
        id="verita_2026-09-19",
        campo={"inicio": "2026-09-10", "fim": "2026-09-19"},
        divulgacao=TODAY,
        n=40500,
        registro_tse="27 registros estaduais (p. 4)",
        ignorar=True,
        cruzamentos={},
    )
    p["fonte"], _ = source(
        "verita",
        {"metodologia": 3, "registros": 4, "1t_topline": 5, "1t_renda": 12},
        url=current["pdf_url"],
    )
    p["renda"].pop("bases", None)
    p["renda"][
        "nota"
    ] = "Há voto por renda na p. 12, mas não há composição ponderada nacional de renda. Não se reutilizam as bases da pesquisa anterior."
    p["publicado"] = {
        "1t": published(
            "flavio lula cury renan_santos caiado zema marcal clariana samara hertz edmilson rui grassi indecisos branco_nulo",
            [43.6, 40.0, 5.4, 2.9, 1.8, 0.6, 0.5, 0.3, 0.2, 0.1, 0.1, 0.1, 0, 3.6, 0.7],
        )
    }
    p["cruzamentos"]["1t"] = table(
        "flavio lula outros nao_escolha",
        [[39, 43.9, 11.8, 5.3], [46.3, 37.5, 12.8, 3.4], [47.5, 37.1, 11.4, 4]],
        "P. 12, base total. Branco/nulo e NS/NR vêm agrupados. Não confundir com votos válidos da p. 19.",
    )
    p["motivo"] = (
        "Consolidação nacional de 27 amostras estaduais, ponderadas pelo eleitorado de cada UF. Há cruzamento de renda, mas falta a distribuição ponderada nacional entre as faixas. O 1º turno inclui Marçal e não há alternativa sem ele; o relatório não publica 2º turno. Não integra as médias."
    )
    p["notas"] = (
        "BR-02386/2026 refere-se apenas ao Acre, não às 40.500 entrevistas nacionais. Todos os 27 registros constam da p. 4. Placares em votos totais, não válidos."
    )
    return p


def datafolha():
    article = next(
        a
        for a in read(WORK / "fontes-web.json")
        if "empatam-em-2o-turno-diz-datafolha" in a["url"]
    )
    p = {
        "id": "datafolha_2026-09-23",
        "instituto": "Datafolha",
        "contratante": "Folha de S.Paulo e TV Globo",
        "metodo": "presencial",
        "registro_tse": "BR-00304/2026",
        "n": 2002,
        "campo": {"inicio": "2026-09-22", "fim": "2026-09-23"},
        "divulgacao": TODAY,
        "fonte": {
            "tipo": "materia",
            "url": article["url"],
            "pdf": None,
            "paginas": {},
            "conferido_em": TODAY,
            "status": "Placar divulgado; relatório e cruzamentos ainda não localizados na consulta de 24/09.",
        },
        "publicado": {
            "1t": published(
                "lula flavio cury caiado renan_santos zema samara branco_nulo indecisos",
                [40, 36, 5, 4, 3, 1, 1, 5, 2],
            ),
            "2t": published("lula flavio branco_nulo indecisos", [47, 45, 7, 1]),
        },
        "cruzamentos": {},
        "ignorar": True,
        "motivo": "Divulgação de 24/09 cadastrada. A matéria não fornece perfil e voto por renda; a página do instituto consultada ainda aponta o relatório da onda anterior. Sem esses dados da mesma onda, nenhum ajuste é calculado.",
    }
    return p


def american():
    info, _ = source("american", {})
    info.update(
        tipo="materia_em_pdf",
        status="Arquivo é matéria que anuncia a pesquisa, não relatório com resultados.",
    )
    return {
        "id": "american_analytics_2026-09-20",
        "instituto": "American Analytics",
        "contratante": "Time Brasil Media",
        "registro_tse": "BR-02587/2026",
        "n": 2000,
        "campo": {"inicio": "2026-09-15", "fim": "2026-09-20"},
        "divulgacao": None,
        "divulgacao_prevista": "2026-09-21",
        "fonte": info,
        "publicado": {},
        "cruzamentos": {},
        "ignorar": True,
        "motivo": "Pesquisa anunciada para 21/09. O arquivo vinculado como íntegra pelo Poder360 é uma matéria de quatro páginas que anuncia a divulgação e cita resultados de junho. Não comprova o resultado desta onda. Relatório atual, perfil e cruzamentos pendentes; nenhum placar antigo foi transportado para setembro.",
    }


def main():
    engine = module("reponderacao-pnad")
    bench, ipca = engine.Benchmark(), engine.load_ipca()
    polls = [
        atlas(),
        realtime(),
        futura(),
        poderdata(),
        quaest(),
        palver(),
        verita(),
        datafolha(),
        american(),
    ]
    checks = []
    for p in polls:
        if not p.get("ignorar"):
            result = engine.process_poll(p, bench, ipca)
            for turn, r in result["turnos"].items():
                assert r["residuo_max"] <= 1.5, (p["id"], turn, r["residuo_max"])
                c = CONTROLS[p["id"]][turn]
                c["recomposto"] = {
                    key: sum(
                        w * row[j]
                        for w, row in zip(c["pesos"], c["linhas"], strict=True)
                    )
                    / sum(c["pesos"])
                    for j, key in enumerate(["lula", "flavio"])
                }
                c["residuo_max_pp"] = max(
                    abs(c["recomposto"][k] - p["publicado"][turn][k])
                    for k in ["lula", "flavio"]
                )
                assert c["residuo_max_pp"] <= 1.5, (p["id"], c)
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
    unchanged = []
    for ident in ["nexus_2026-09-20", "gerp_2026-09-16", "mda_2026-09-13"]:
        old = read(POLLS / f"{ident}.json")
        path = ROOT / old["fonte"]["pdf"]
        unchanged.append(
            {
                "id": ident,
                "instituto": old["instituto"],
                "divulgacao": old["divulgacao"],
                "situacao": "Já integrado; nenhuma onda posterior confirmada na busca.",
                "fonte": old["fonte"],
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    verification = {
        "data": TODAY,
        "controles": checks,
        "fontes": [{"id": p["id"], **p["fonte"]} for p in polls],
        "ja_integradas": unchanged,
        "quaest_estaduais": "data/pesquisas/quaest/2026-09-23/manifesto.json",
        "escopo": "Pesquisas nacionais recentes. As cinco íntegras estaduais Quaest recebidas foram arquivadas separadamente e não entram nas médias nacionais.",
        "limite": "Sensibilidade de uma margem, não previsão nem voto corrigido.",
    }
    dump(WORK / "verificacao.json", verification)
    dump(ROOT / "docs/assets/reponderacao_20260924.json", verification)
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
