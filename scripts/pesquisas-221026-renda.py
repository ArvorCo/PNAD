#!/usr/bin/env python3
"""Integra 22/10 e íntegras de 21/10, preservando a identificação das ondas."""

import gzip
import importlib
import json
import shutil
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-22"


def base(
    slug, house, registry, start, end, release, n, method, pages, count, pub, note
):
    poll = PREVIOUS.base(
        f"{slug}_2026-10-{end}",
        house,
        registry,
        (f"2026-10-{start}", f"2026-10-{end}"),
        release,
        n,
        method,
        f"{slug}_102026_22",
        pages,
        count,
        pub,
        note,
    )
    poll["fonte"]["conferido_em"] = DAY
    return poll


def poderdata():
    note = (
        "Íntegra de 42 páginas. Campo 19–21/10, BR-07926/2026, n=4.000. "
        "P. 2 declara ponderação por sexo, idade, instrução, renda, resultado do 1º turno e região. "
        "Perfil atual 46/33/21 na p. 4, sem etapa antes/depois dos pesos explicitada: "
        "sensibilidade condicional. Total 49/48/3/1 soma 101 por arredondamento; "
        "válidos publicados 51/49 na p. 11 permanecem separados da divisão dos inteiros. "
        "Renda p. 9 e sexo p. 7 conferidos visualmente e por recomposição. "
        "Presença certa por voto atual na p. 19: 97/95/56/72 (F/L/BN/NS); "
        "aplicada somente à projeção documental desta onda. Não confundir decisão "
        "do voto (p. 14), presença passada (p. 10) e presença futura declarada."
    )
    p = base(
        "poderdata",
        "PoderData",
        "BR-07926/2026",
        "19",
        "21",
        DAY,
        4000,
        "telefônico automatizado IVR/URA",
        {
            "metodologia": 2,
            "perfil_renda": 4,
            "2t_topline": 6,
            "2t_validos": 11,
            "2t_renda": 9,
            "sexo": 7,
            "presenca_por_voto": 19,
        },
        42,
        [49, 48, 3, 1],
        note,
    )
    PREVIOUS.income(
        p,
        [2, 5, None],
        [46, 33, 21],
        [[41, 54, 4, 1], [54, 44, 1, 0], [57, 41, 2, 0]],
        [[57, 39, 3, 1], [41, 55, 3, 1]],
        [47, 53],
        note,
    )
    p["renda"]["perfil_tipo"] = "perfil_publicado"
    p["publicado_validos"] = {"2t": {"flavio": 51, "lula": 49}}
    return p


def gerp():
    note = (
        "34º relatório, 59 páginas, publicado em 21/10. Ficha p. 9 confirma campo "
        "19, 20 e 21/10, BR-03835/2026, n=2.400; algumas referências ao registro "
        "informam 17–20/10, divergência preservada. Esta é outra onda, distinta do "
        "tracking de 15–19/10. Perfil ponderado p. 10: renda familiar "
        "13/22/40/17/6/2, sem recusa indicada. Total 50/45/2/2 soma 99; 'nenhum deles' "
        "é não escolha, não abstenção identificada. Válidos publicados 53/47 p. 23. "
        "Cruzamentos ponderados p. 18; não usar as contagens brutas dos cabeçalhos "
        "como pesos. Renda e sexo recompõem o total dentro do arredondamento."
    )
    p = base(
        "gerp",
        "Gerp",
        "BR-03835/2026",
        "19",
        "21",
        "2026-10-21",
        2400,
        "telefônico CATI/GerpCati",
        {
            "metodologia": 9,
            "perfil_renda": 10,
            "2t_topline": 16,
            "2t_validos": 23,
            "2t_renda": 18,
            "sexo": 18,
        },
        59,
        [50, 45, 2, 2],
        note,
    )
    PREVIOUS.income(
        p,
        [1, 2, 5, 10, 20, None],
        [13, 22, 40, 17, 6, 2],
        [
            [35, 62, 0, 3],
            [49, 46, 3, 2],
            [52, 43, 3, 3],
            [54, 44, 1, 1],
            [61, 34, 3, 1],
            [64, 34, 1, 0],
        ],
        [[56, 41, 2, 1], [46, 49, 2, 3]],
        [47, 53],
        note,
    )
    p["publicado_validos"] = {"2t": {"flavio": 53, "lula": 47}}
    return p


def quaest():
    note = (
        "Íntegra oficial de 207 páginas publicada em 22/10, relativa à divulgação "
        "de 21/10 e ao campo 17–20/10. BR-08535/2026, n=2.154. "
        "Perfil atual conferido na p. 203: renda domiciliar total 31/42/27; "
        "sexo 47/53 na p. 200. Etapa antes/depois dos pesos não explicitada: "
        "sensibilidade condicional ao perfil publicado. Cruzamentos atuais p. 25 "
        "(renda) e p. 22 (sexo), iguais ao painel G1 arquivado. Revisão da mesma "
        "onda, sem duplicação; substitui a pendência de perfil. Branco/nulo/não vai "
        "votar forma categoria conjunta e não mede abstenção isoladamente. "
        "Não foi localizada regra de likely voter para esta onda na íntegra."
    )
    p = base(
        "quaest",
        "Quaest",
        "BR-08535/2026",
        "17",
        "20",
        "2026-10-21",
        2154,
        "presencial domiciliar",
        {
            "metodologia": 2,
            "perfil_renda": 203,
            "2t_topline": 17,
            "2t_renda": 25,
            "sexo": 22,
        },
        207,
        [45, 44, 9, 2],
        note,
    )
    p["contratante"] = "TV Globo e O Globo"
    PREVIOUS.income(
        p,
        [2, 5, None],
        [31, 42, 27],
        [[37, 51, 9, 3], [48, 42, 8, 2], [50, 39, 10, 1]],
        [[50, 40, 8, 2], [41, 47, 10, 2]],
        [47, 53],
        note,
    )
    p["renda"]["perfil_tipo"] = "perfil_publicado"
    p["fonte"]["relatorio_completo"] = DAY
    p["revisao_documental"] = {
        "data": DAY,
        "motivo": "Íntegra atual e perfil localizados; mesma onda.",
        "inventario_inicial": "analysis/reponderacao/auditoria_20261021.json",
    }
    return p


def indexa():
    folder = ROOT / "data/originals/indexa_102026_22"
    raw = json.loads(gzip.decompress((folder / "relatorio.json.gz").read_bytes()))
    items = COMMON.archive("indexa_102026_22")
    source = COMMON.source(items, "relatorio.json.gz")
    options = ["flavio", "lula", "branco_nulo", "indecisos", "nao_vai_votar"]
    keys = ["flaviobolsonaro", "lula", "nulobranco", "indecisonaosabe", "naoiriavotar"]
    question = raw["seg"]["q"]["2"]
    dims = {d["key"]: d["segs"] for d in question["dims"]}
    rows = [[s["vals"][k] for k in keys] for s in dims["rendadomiciliaremsalarios"]]
    published = dict(zip(options, [45.2, 44.1, 4.3, 1.6, 4.8], strict=True))
    recomposed = {
        k: sum(r[i] * w for r, w in zip(rows, [42, 38, 20], strict=True)) / 100
        for i, k in enumerate(options)
    }
    note = (
        "Caderno digital completo oficial, rodada 8, arquivado em JSON/HTML e respostas da API; "
        "sem PDF disponibilizado. BR-02348/2026, CATI, n=2.000, campo 20–21/10. "
        "Placar divulgado pelo Broadcast: F/L/BN/NS/não votaria 45,2/44,1/4,3/1,6/4,8; "
        "válidos 50,6/49,4 preservados. A API guarda 45,2/44,15/4,35/1,55/4,75, "
        "e a tela arredonda para inteiros; as três precisões estão documentadas. "
        "Perfil publicado 42/38/20 e cruzamentos da pergunta 2 recompõem Flávio em "
        "43,806%, resíduo −1,394 pp contra a divulgação, incompatível com arredondamento "
        "de décimos e pesos inteiros. Não ajustar PNAD até reconciliar a base/etapa desse perfil. "
        "Decisão definitiva de voto não é probabilidade de comparecimento."
    )
    return {
        "id": "indexa_2026-10-21",
        "instituto": "Indexa/Broadcast",
        "registro_tse": "BR-02348/2026",
        "contratante": "Agência Estado / Broadcast",
        "campo": {"inicio": "2026-10-20", "fim": "2026-10-21"},
        "divulgacao": DAY,
        "n": 2000,
        "metodo": "telefônico CATI",
        "publicado": {"2t": published},
        "publicado_validos": {"2t": {"flavio": 50.6, "lula": 49.4}},
        "fonte": {
            **source,
            "tipo": "relatorio_digital",
            "rotulo": "Caderno digital oficial completo",
            "url": "https://sistema.indexapesquisas.com.br/pesquisaspublicadas/nacional?r=8&embed=1",
            "paginas": {
                "metodologia": "Ficha técnica",
                "perfil_renda": "Propriedades da amostra",
                "2t_topline": "Pergunta 2",
                "2t_renda": "Pergunta 2, renda domiciliar",
            },
            "conferido_em": DAY,
            "status": "Caderno digital completo arquivado; perfil incompatível.",
            "nota": note,
        },
        "ignorar": True,
        "motivo": "Perfil de renda não recompõe o total; sem PNAD até reconciliação.",
        "cruzamentos": {},
        "perfil_documental": {"renda": [42, 38, 20], "sexo": [47, 53]},
        "cruzamentos_documentais": {
            "opcoes": options,
            "renda": rows,
            "sexo": dims["sexo"],
        },
        "controle_documental": {
            "recomposto": recomposed,
            "residuo": {k: recomposed[k] - published[k] for k in options},
        },
        "api_sem_arredondar": {
            k: question["geral"][key] * 100
            for k, key in zip(options, keys, strict=True)
        },
    }


def main():
    polls = [poderdata(), indexa(), gerp(), quaest()]
    for p in polls:
        COMMON.write(ROOT / "analysis/reponderacao/pesquisas" / (p["id"] + ".json"), p)
        if "pdf" in p["fonte"]:
            slug = p["id"].split("_")[0]
            date = "22102026" if slug == "poderdata" else "21102026"
            shutil.copyfile(
                ROOT / p["fonte"]["pdf"], ROOT / "docs/fontes" / f"{slug}_{date}.pdf"
            )
        print(p["id"], "publicado" if p.get("ignorar") else "PNAD")
    shutil.copyfile(
        ROOT / "data/originals/indexa_102026_22/relatorio.json.gz",
        ROOT / "docs/fontes/indexa_22102026.json.gz",
    )
    presence_path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(presence_path)
    presence["conferido_em"] = DAY
    source = polls[0]["fonte"]
    presence["ondas"][polls[0]["id"]] = {
        "tipo": "direto",
        "taxas": {"flavio": 0.97, "lula": 0.95, "indecisos": 0.72},
        "regra": "Seleção pela resposta 'Com certeza vai votar', por voto atual (p. 19). Autodeclaração, não probabilidade calibrada. Aplicar as mesmas taxas à PNAD supõe estabilidade dentro de cada eleitorado; renda × voto × presença não publicada. Não muda as centrais.",
        "fonte": {k: source[k] for k in ["arquivo", "sha256", "url"]}
        | {"paginas": [15, 19]},
    }
    COMMON.write(presence_path, presence)
    audit = {
        "data": DAY,
        "pesquisas": polls,
        "regra": "Uma onda por casa nas centrais; histórico e snapshots publicados preservados.",
        "escopo_varredura": {
            "periodo_divulgacao": ["2026-10-21", DAY],
            "novas": [p["id"] for p in polls[:3]],
            "revisoes": [polls[3]["id"]],
        },
        "varredura": [
            {
                "instituto": "Datafolha",
                "status": "Anunciada para 19h; resultado ainda não divulgado na consulta",
                "conclusao": "Consulta em 22/10 às 17h47 (Brasília); aguarda divulgação efetiva.",
                "pendente": True,
                "fontes": [
                    "https://www1.folha.uol.com.br/poder/2026/10/saiba-quando-saem-as-principais-pesquisas-eleitorais-ate-o-2o-turno.shtml"
                ],
            },
            {
                "instituto": "Data Tempo",
                "status": "Registro para Minas Gerais; não é pesquisa nacional",
                "pendente": False,
                "fontes": [
                    "https://www.opovo.com.br/noticias/politica/eleicoes/2026/10/22/pesquisas-para-o-2-turno-veja-quais-sao-publicadas-nesta-quinta-22-10.html"
                ],
            },
        ],
        "pendencias": [
            "Datafolha de 22/10: divulgação anunciada para 19h.",
            "Indexa: reconciliar perfil e cruzamentos antes de ajustar renda.",
            "Gerp tracking de 20/10 e Data Ranking: íntegra ainda não localizada; nova Gerp de 21/10 é outra onda.",
            "França de 20/10: incompatibilidade entre total e cruzamentos permanece.",
        ],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261022.json", audit)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261022.json", audit)


if __name__ == "__main__":
    main()
