#!/usr/bin/env python3
"""Integra a rodada noturna de 24/10 sem transportar perfis de ondas anteriores."""

import importlib
import shutil
from copy import deepcopy
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-24"


def base(
    slug, house, registry, start, end, n, method, pub, note, pages=None, count=None
):
    folder = f"{slug}_102026_24"
    if pages:
        poll = PREVIOUS.base(
            f"{slug}_2026-10-{end}",
            house,
            registry,
            (f"2026-10-{start}", f"2026-10-{end}"),
            DAY,
            n,
            method,
            folder,
            pages,
            count,
            pub,
            note,
        )
    else:
        source = COMMON.source(COMMON.archive(folder), "divulgacao.html.gz")
        poll = {
            "id": f"{slug}_2026-10-{end}",
            "instituto": house,
            "registro_tse": registry,
            "divulgacao": DAY,
            "campo": {"inicio": f"2026-10-{start}", "fim": f"2026-10-{end}"},
            "n": n,
            "metodo": method,
            "publicado": {"2t": PREVIOUS.vector(pub)},
            "fonte": {
                **source,
                "tipo": "divulgacao",
                "rotulo": "Divulgação do contratante",
                "status": "Divulgação arquivada; íntegra não localizada.",
                "nota": note,
            },
        }
    poll["fonte"]["conferido_em"] = DAY
    return poll


def valid(poll, flavio, lula):
    poll["publicado_validos"] = {"2t": {"flavio": flavio, "lula": lula}}


def palver():
    note = (
        "Onda 9, 112 páginas, campo 22–24/10, n=5.000, BR-01794/2026. "
        "P. 20 distingue perfil ponderado 36/41/23 de renda familiar e 48/52 por sexo "
        "das contagens brutas. Renda e sexo p. 25 conferidos visualmente; total "
        "50/49/1/0 nas pp. 23–24. Zero de indecisos é arredondado. O 1% reúne "
        "branco/nulo ou não votaria, sem identificar abstenção. Método v3 e "
        "questionário iguais à onda 8: PNADC 2025 primeira entrevista, voto no "
        "2T/2022, voto no 1T/2026 por região e filiação partidária."
    )
    p = base(
        "palver",
        "Palver",
        "BR-01794/2026",
        "22",
        "24",
        5000,
        "online, recrutamento por anúncios; não probabilística, raking v3",
        [50, 49, 1, 0],
        note,
        {
            "metodologia": [12, 14, 16, 18],
            "perfil_renda": 20,
            "2t_topline": [23, 24],
            "2t_renda": 25,
            "sexo": 25,
        },
        112,
    )
    PREVIOUS.income(
        p,
        [2, 5, None],
        [36, 41, 23],
        [[48, 50, 1, 0], [54, 46, 1, 0], [48, 51, 1, 0]],
        [[59, 40, 1, 0], [43, 57, 1, 0]],
        [48, 52],
        note,
    )
    p["metodologia_onda"] = {
        "versao": "v3",
        "comparavel_onda_anterior": True,
        "n_efetivo": 1943,
        "efeito_pesos": 2.57,
        "margem_publicada_pp": 2.2,
    }
    return p


def gerp():
    note = (
        "Íntegra de 28 páginas, BR-09327/2026. Campo efetivo 22–24/10 na capa e "
        "p. 9, n=2.400; não usar início previsto em registro como início efetivo. "
        "Perfil ponderado de renda p. 10: 13/22/40/17/6/2, sem recusa publicada; "
        "sexo 47/53. Bases brutas da p. 17 não são pesos. Estimulada 49/46/1/3 "
        "soma 99 por arredondamento; votos por renda e sexo p. 17 recompostos. "
        "Válidos oficiais 52/48 preservados separados da normalização de 49/46."
    )
    p = base(
        "gerp",
        "Gerp",
        "BR-09327/2026",
        "22",
        "24",
        2400,
        "telefônico, CATI/GerpCati; ponderação por sexo, idade, escolaridade, renda e região",
        [49, 46, 1, 3],
        note,
        {
            "metodologia": 9,
            "perfil_renda": 10,
            "2t_topline": 15,
            "2t_renda": 17,
            "sexo": 17,
            "2t_validos": 19,
        },
        28,
    )
    valid(p, 52, 48)
    PREVIOUS.income(
        p,
        [1, 2, 5, 10, 20, None],
        [13, 22, 40, 17, 6, 2],
        [
            [32, 61, 0, 6],
            [47, 45, 1, 6],
            [53, 44, 1, 2],
            [54, 44, 1, 2],
            [52, 41, 5, 2],
            [78, 21, 0, 1],
        ],
        [[56, 40, 1, 2], [43, 50, 2, 5]],
        [47, 53],
        note,
    )
    return p


def nexus():
    note = (
        "19ª rodada, 72 páginas, BR-08234/2026, CATI, campo 23–24/10, n=2.000. "
        "10% do campo em 23/10 e 90% em 24/10. Total estimulado p. 14: "
        "47/46/5,2/1,8; renda p. 33, sexo p. 32 e perfil atual p. 69: "
        "21/16/40/23, sexo 47/53. Etapa do perfil antes/depois dos pesos não "
        "explicitada: sensibilidade PNAD condicional ao perfil publicado. "
        "O LVM das pp. 6–10 é outro universo: exclui os 21% classificados como "
        "menos prováveis de comparecer e divulga válidos 52,4/47,6, contra "
        "50,5/49,5 na amostra total. Nas centrais entra a amostra total; não "
        "somar seleção LVM aos ajustes de comparecimento Arvor. Presença declarada "
        "de 93,3% na p. 64 é distinta da hipótese de 79% do LVM."
    )
    p = base(
        "nexus",
        "Nexus",
        "BR-08234/2026",
        "23",
        "24",
        2000,
        "telefônico com entrevistador, CATI, 27 UFs",
        [47, 46, 5.2, 1.8],
        note,
        {
            "metodologia": 4,
            "2t_topline": 14,
            "2t_validos": 19,
            "2t_renda": 33,
            "sexo": 32,
            "perfil_renda": 69,
            "eleitor_provavel": [6, 8, 9, 10],
            "presenca": [64, 67],
        },
        72,
    )
    p["contratante"] = "Banco BTG Pactual"
    valid(p, 50.5, 49.5)
    PREVIOUS.income(
        p,
        [1, 2, 5, None],
        [21, 16, 40, 23],
        [
            [30.9, 59.1, 6.2, 3.8],
            [39.8, 46.5, 11.2, 2.5],
            [53.6, 43, 2.6, 0.8],
            [55.5, 38.9, 5.2, 0.4],
        ],
        [[53.7, 39.8, 5.2, 1.3], [41.1, 51.5, 5.2, 2.2]],
        [47, 53],
        note,
    )
    p["renda"]["perfil_tipo"] = "perfil_publicado"
    p["distribuicao_campo_pct"] = {"2026-10-23": 10, "2026-10-24": 90}
    p["eleitor_provavel_documental"] = {
        "paginas": [6, 8, 9, 10],
        "abstencao_estimada_pct": 21,
        "validos": {"flavio": 52.4, "lula": 47.6},
        "por_100_eleitores": {
            "flavio": 40.6,
            "lula": 36.8,
            "branco_nulo": 0.9,
            "indecisos": 0.6,
            "abstencao": 21,
        },
        "entra_nas_centrais": False,
        "regra": "Seleção dos 79% mais prováveis de comparecer; resultado arredondado soma 99,9.",
    }
    return p


def datafolha_publicada():
    note = (
        "Divulgação Folha de 24/10 às 18h30 e API G1 atual conferidas: campo "
        "23–24/10, 4.050 entrevistas em 124 municípios, BR-09540/2026. "
        "Total 48/47/3/2; válidos publicados 51/49. O painel G1 tem voto por "
        "renda atual, mas não bases ponderadas atuais. Sem íntegra ou perfil "
        "atual conferido, somente publicado na Projeção; não carregar as bases "
        "de 22/10 nem manter aquela onda na Média como se fosse a mais recente."
    )
    p = base(
        "datafolha",
        "Datafolha",
        "BR-09540/2026",
        "23",
        "24",
        4050,
        "presencial, 124 municípios",
        [48, 47, 3, 2],
        note,
    )
    p["contratante"] = "Folha de S.Paulo e TV Globo"
    valid(p, 51, 49)
    source = COMMON.source(COMMON.archive("datafolha_102026_24"), "g1-estimulada.json")
    source["rotulo"] = "G1: voto estimulado por renda, onda de 24/10"
    data = COMMON.read(ROOT / source["arquivo"])["resultado"]["estratos"]
    labels = ["Até 2 s.m.", "Mais de 2 a 5 s.m", "Mais de 5 s.m."]
    rows = []
    for label in labels:
        c = next(c for c in data if c["variavel_cruzamento"] == label)
        rows.append(
            [
                round(
                    100
                    * next(v["value"] for v in x["values"] if v["date"][:10] == DAY),
                    6,
                )
                for x in c["data"]
            ]
        )
    p["cruzamentos_sem_perfil"] = {
        "fonte": source,
        "opcoes": PREVIOUS.OPTIONS,
        "renda": {"rotulos": labels, "linhas": rows},
    }
    p.update(
        ignorar=True,
        cruzamentos={},
        motivo="Bases ponderadas atuais de renda não localizadas; somente publicado na Projeção.",
    )
    return p


def datafolha():
    """Prévia solicitada: votos atuais, composição e cobertura de 22/10."""
    p = datafolha_publicada()
    old = COMMON.read(
        ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-22.json"
    )
    note = (
        "PRÉVIA PNAD solicitada: voto por renda de 24/10 no G1, com perfil e "
        "cobertura emprestados da íntegra Datafolha de 22/10, p. 27. Bases de "
        "referência 1.171/913/341, soma 2.425 de 2.520 (96,23%). Essa composição "
        "e essa fração, não as contagens, são transportadas à amostra atual de "
        "4.050 por hipótese. A massa restante conserva o topline atual. Não são "
        "bases observadas em 24/10. Cruzamentos atuais F/L/BN/I: 41/53/3/3, "
        "55/41/4/1 e 57/39/3/0. Total 48/47/3/2; válidos oficiais 51/49. "
        "A prévia entra nas duas centrais e na tendência sob estabilidade "
        "provisória do perfil; substituir quando saírem as bases atuais. "
        "Não é resultado confirmado pela íntegra nem previsão de comparecimento."
    )
    p.pop("ignorar")
    p.pop("motivo")
    p["renda"] = deepcopy(old["renda"])
    p["renda"].pop("bases", None)
    p["renda"].pop("nao_publicada_n", None)
    p["renda"].update(
        perfil_tipo="hipotese_onda_anterior",
        nota=note,
        bases_referencia=old["renda"]["bases"],
        referencia_id=old["id"],
        referencia_divulgacao=old["divulgacao"],
        n_referencia=old["n"],
    )
    cross = p.pop("cruzamentos_sem_perfil")
    p["cruzamentos_documentais"] = cross
    p["cruzamentos"] = {
        "2t": {
            "opcoes": PREVIOUS.OPTIONS,
            "linhas": cross["renda"]["linhas"],
            "nota": note,
        }
    }
    p["fonte"].update(status="Prévia PNAD · perfil da onda de 22/10", nota=note)
    ref = COMMON.source(COMMON.archive("datafolha_102026_22_integra"), "relatorio.pdf")
    ref["rotulo"] = (
        "Perfil de referência: Datafolha de 22/10, p. 27; hipótese para 24/10"
    )
    p["fonte"]["complementos"] = [cross["fonte"], ref]
    p["controles"] = {
        "2t": {
            "renda": PREVIOUS.control(
                p["publicado"]["2t"],
                p["cruzamentos"]["2t"]["linhas"],
                p["renda"]["amostra_pct"],
            )
        }
    }
    p["controles"]["2t"]["renda"][
        "nota"
    ] = "Recomposição sob perfil emprestado; não valida as bases atuais."
    return p


def colectta():
    note = (
        "Divulgação do contratante Brazil Economy, 24/10 às 10h49, atualizada "
        "12h04. BR-05601/2026, campo 23/10, 3.000 entrevistas presenciais "
        "em 101 municípios nas 27 UFs. Total 46/46,5/4,4/3,1 e válidos "
        "49,7/50,3. Íntegra e perfil atual por renda não localizados; "
        "somente publicado na Projeção. Certeza de comparecer de 92,6% "
        "é autodeclaração, não previsão calibrada de comparecimento."
    )
    p = base(
        "colectta",
        "Colectta",
        "BR-05601/2026",
        "23",
        "23",
        3000,
        "presencial, 101 municípios, 27 UFs",
        [46, 46.5, 4.4, 3.1],
        note,
    )
    p["contratante"] = "Brazil Economy"
    valid(p, 49.7, 50.3)
    p.update(
        ignorar=True,
        cruzamentos={},
        motivo="Íntegra e perfil de renda não localizados; somente publicado na Projeção.",
    )
    return p


def main():
    polls = [palver(), gerp(), nexus(), datafolha(), colectta()]
    for poll in polls:
        COMMON.write(
            ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
        )
        if poll["fonte"].get("pdf"):
            slug = poll["id"].split("_")[0]
            shutil.copyfile(
                ROOT / poll["fonte"]["pdf"], ROOT / f"docs/fontes/{slug}_24102026.pdf"
            )
        print(poll["id"], "publicado" if poll.get("ignorar") else "PNAD")
    path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(path)
    houses = {p["instituto"] for p in polls}
    presence["auditoria_ultima_onda"] = [
        p for p in presence["auditoria_ultima_onda"] if p["instituto"] not in houses
    ] + [
        {
            "instituto": p["instituto"],
            "id": p["id"],
            "tipo": "neutro",
            "fonte": p["fonte"]["url"],
            "arquivo": p["fonte"]["arquivo"],
            "nota": "Sem seleção de presença incorporada nesta série; não transportar taxas anteriores. "
            + (
                "LVM Nexus de 24/10 preservado na ficha documental, separado das centrais."
                if p["instituto"] == "Nexus"
                else ""
            ),
        }
        for p in polls
    ]
    COMMON.write(path, presence)
    audit = {
        "data": DAY,
        "conferido_em": DAY,
        "corte_consulta": "2026-10-24T18:48:00-03:00",
        "busca_sem_novo_resultado_confirmado": [
            "Quaest",
            "AtlasIntel nacional",
            "Futura",
            "Veritá",
            "Phoenix",
            "Simplex",
        ],
        "nota_busca": "Registro e agenda não são resultado publicado. Quaest consultada "
        "na API G1 e no catálogo de PDFs; Atlas no catálogo oficial e na cobertura "
        "nacional. Buscas por instituto, data e registro nos demais casos. "
        "Novas estaduais Atlas não entram como pesquisas nacionais. PoderData de "
        "23–24/10 tem divulgação prevista para 25/10; onda anterior preservada.",
        "pesquisas": polls,
        "regra": "Uma onda por casa, sempre a mais recente. Datafolha com prévia "
        "solicitada sob perfil de 22/10 explicitamente hipotético; demais perfis "
        "são atuais. Sem dupla seleção LVM.",
        "previas": [
            p["id"]
            for p in polls
            if p.get("renda", {}).get("perfil_tipo") == "hipotese_onda_anterior"
        ],
        "pendencias": [p["motivo"] for p in polls if p.get("ignorar")],
        "integra_baixada": [p["id"] for p in polls if p["fonte"].get("pdf")],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261024_noite.json", audit)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261024_noite.json", audit)


if __name__ == "__main__":
    main()
