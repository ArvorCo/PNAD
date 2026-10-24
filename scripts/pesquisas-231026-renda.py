#!/usr/bin/env python3
"""Integra sete divulgações de 23/10; só ajusta renda documentalmente compatível."""

import importlib
import shutil
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-23"
CHECKED = "2026-10-24"


def base(slug, house, registry, start, end, n, method, pages, count, pub, valid, note):
    p = PREVIOUS.base(
        f"{slug}_2026-10-{end}",
        house,
        registry,
        (f"2026-10-{start}", f"2026-10-{end}"),
        DAY,
        n,
        method,
        f"{'vox' if slug == 'vox_brasil' else slug}_102026_23",
        pages,
        count,
        pub,
        note,
    )
    p["fonte"]["conferido_em"] = CHECKED
    p["publicado_validos"] = {"2t": dict(zip(["flavio", "lula"], valid, strict=True))}
    return p


def realtime():
    note = (
        "Íntegra de 25 páginas, campo 19–22/10, 2.000 entrevistas. Perfil atual "
        "46/33/21 na p. 3; voto por renda p. 11 e sexo p. 9 conferidos visualmente. "
        "Registro BR-09670/2026 define renda domiciliar mensal e fator previsto 1 "
        "para renda; etapa do perfil publicado não explicitada. Sensibilidade "
        "condicional, sem transportar perfil anterior. Válidos oficiais 52/48 "
        "preservados separadamente da normalização dos inteiros 49/45."
    )
    p = base(
        "realtime",
        "Real Time Big Data",
        "BR-09670/2026",
        "19",
        "22",
        2000,
        "entrevistas telefônicas e digitais; método misto declarado no PesqEle",
        {
            "metodologia": 2,
            "perfil_renda": 3,
            "2t_topline": 8,
            "sexo": 9,
            "2t_renda": 11,
            "2t_validos": 16,
        },
        25,
        [49, 45, 5, 1],
        [52, 48],
        note,
    )
    PREVIOUS.income(
        p,
        [2, 5, None],
        [46, 33, 21],
        [[40, 54, 5, 1], [52, 42, 5, 1], [63, 32, 3, 2]],
        [[52, 40, 7, 1], [47, 49, 3, 1]],
        [47, 53],
        note,
    )
    p["renda"]["perfil_tipo"] = "perfil_publicado"
    return p


def alfa():
    note = (
        "Íntegra de 29 páginas, campo 18–22/10, n=2.700. Perfil de renda domiciliar "
        "40/37/23 na p. 6, cruzamentos de renda familiar p. 16 e sexo p. 15. "
        "Etapa do perfil não explicitada; ajuste condicional ao perfil publicado. "
        "Totais 49,9/46/2/2,1 e válidos oficiais 52/48 nas pp. 13–14. "
        "Registro BR-08496/2026 tem cabeçalho n=1.200, plano n=2.700 e texto "
        "telefônico divergente das entrevistas pessoais da íntegra; ficha efetiva "
        "do relatório prevalece, sem apagar a divergência arquivada."
    )
    p = base(
        "alfa",
        "Alfa Inteligência/TMC",
        "BR-08496/2026",
        "18",
        "22",
        2700,
        "entrevistas pessoais; municípios por PPT e cotas de entrevistados",
        {
            "metodologia": 5,
            "perfil_renda": 6,
            "2t_topline": 13,
            "2t_validos": 14,
            "sexo": 15,
            "2t_renda": 16,
        },
        29,
        [49.9, 46, 2, 2.1],
        [52, 48],
        note,
    )
    p["contratante"] = "Alfa Inteligência, recursos próprios"
    PREVIOUS.income(
        p,
        [2, 5, None],
        [40, 37, 23],
        [[44, 52, 2, 2], [52, 43, 2, 3], [56, 40, 2, 2]],
        [[53, 43, 2, 2], [47, 49, 2, 2]],
        [47, 53],
        note,
    )
    p["renda"]["perfil_tipo"] = "perfil_publicado"
    return p


def ipespe():
    note = (
        "Tracking Ipespe/Abrapel, terceira rodada do 2º turno, íntegra oficial "
        "de 41 páginas. Campo 20–22/10, CATI, n=1.500. Perfil de renda familiar "
        "41/37/22 p. 40; cruzamentos atuais p. 6. P. 39 declara controle por renda "
        "e recall do 1º turno. Etapa do perfil não explícita: "
        "sensibilidade condicional. Geral 48/47/3/2 e válidos oficiais 50,5/49,5. "
        "P. 12: certeza máxima de comparecer entre F/L/BN/NS = 94/90/66/61%. "
        "P. 13: subconjunto com certeza máxima tem total 50/47/2/1 e válidos "
        "51,5/48,5. Preservar ambos os publicados; a seleção Arvor usa as taxas "
        "arredondadas e não substitui o resultado oficial do subconjunto."
    )
    p = base(
        "ipespe",
        "Ipespe",
        "BR-04350/2026",
        "20",
        "22",
        1500,
        "telefônico CATI",
        {
            "metodologia": 39,
            "perfil_renda": 40,
            "2t_topline": 5,
            "2t_validos": 5,
            "sexo": 6,
            "2t_renda": 6,
            "presenca_por_voto": 12,
            "subconjunto_presenca": 13,
        },
        41,
        [48, 47, 3, 2],
        [50.5, 49.5],
        note,
    )
    p["contratante"] = "Abrapel"
    PREVIOUS.income(
        p,
        [2, 5, None],
        [41, 37, 22],
        [[40, 54, 2, 3], [53, 44, 2, 1], [54, 39, 5, 2]],
        [[53, 44, 2, 1], [43, 50, 4, 3]],
        [47, 53],
        note,
    )
    p["renda"]["perfil_tipo"] = "perfil_publicado"
    p["subconjunto_presenca_publicado"] = {
        "criterio": "Nota 10 de chance de comparecer",
        "pagina": 13,
        "total": PREVIOUS.vector([50, 47, 2, 1]),
        "validos": {"flavio": 51.5, "lula": 48.5},
    }
    return p


def exclude(p, reason):
    p.update(ignorar=True, motivo=reason, cruzamentos={})
    return p


def verita():
    note = (
        "Íntegra de 15 páginas, campo 18–22/10, n=15.554, BR-06070/2026. "
        "Totais p. 11: 50,2/47,5/1,4/0,9; válidos publicados 51,3/48,7. "
        "Perfil familiar p. 4: 41,2/40,1/18,7 e frequências 6.401/6.244/2.909 "
        "já somam 100% e 15.554. A tabela ainda acrescenta NS/NR 4,3% e 676: "
        "total 104,3% e 16.230, incompatível com a amostra. Não reinterpretar "
        "como perfil condicional nem emprestar a onda anterior. Cruzamentos "
        "atuais p. 12 preservados para diagnóstico; somente publicado até "
        "reconciliar o denominador. 'Ausente' no voto é BN+NS, não abstenção."
    )
    p = base(
        "verita",
        "Veritá",
        "BR-06070/2026",
        "18",
        "22",
        15554,
        "entrevistas telefônicas automatizadas",
        {
            "perfil_renda": 4,
            "2t_topline": 11,
            "2t_validos": 11,
            "2t_renda": 12,
            "sexo": 12,
        },
        15,
        [50.2, 47.5, 1.4, 0.9],
        [51.3, 48.7],
        note,
    )
    p["perfil_economico_publicado"] = {
        "pagina": 4,
        "percentuais": [41.2, 40.1, 18.7, 4.3],
        "frequencias": [6401, 6244, 2909, 676],
        "categorias": ["Até 2 SM", "2 a 5 SM", "Mais de 5 SM", "NS/NR"],
    }
    p["cruzamentos_diagnosticos"] = {
        "pagina": 12,
        "opcoes": PREVIOUS.OPTIONS,
        "linhas": [
            [44.8, 52.2, 1.6, 1.4],
            [54.3, 43.8, 1.4, 0.6],
            [53.1, 45.5, 0.9, 0.5],
            [46.2, 49.8, 2.2, 1.8],
        ],
    }
    return exclude(
        p,
        "Perfil de renda soma 104,3% e 16.230 pessoas para n=15.554; "
        "sem ajuste PNAD até reconciliar denominadores. Somente publicado na Projeção.",
    )


def vox():
    note = (
        "Íntegra de 38 páginas, campo 20–22/10, n=2.100. Estimulada p. 13: "
        "44,3/45,4/6/4,3; válidos oficiais 49,4/50,6. Perfil econômico p. 6 "
        "84,1/12,3/2,5/1,1; voto por renda p. 18. O conceito de renda não "
        "identifica familiar, individual ou per capita; não substituir pela "
        "renda familiar PNAD. Cruzamentos preservados como diagnóstico."
    )
    p = base(
        "vox_brasil",
        "Vox Brasil",
        "BR-03259/2026",
        "20",
        "22",
        2100,
        "presencial domiciliar",
        {
            "metodologia": 2,
            "perfil_renda": 6,
            "2t_topline": 13,
            "2t_validos": 13,
            "2t_renda": 18,
        },
        38,
        [44.3, 45.4, 6, 4.3],
        [49.4, 50.6],
        note,
    )
    p["perfil_economico_publicado"] = {
        "pagina": 6,
        "faixas_sm": [2, 5, 10, None],
        "percentuais": [84.1, 12.3, 2.5, 1.1],
        "conceito": "não definido",
    }
    p["cruzamentos_diagnosticos"] = {
        "pagina": 18,
        "opcoes": PREVIOUS.OPTIONS,
        "linhas": [
            [43.4, 45.6, 6.4, 4.6],
            [46.7, 46.3, 3.9, 3.1],
            [48.1, 48.1, 1.9, 1.9],
            [82.6, 13, 4.3, 0],
        ],
        "nota": "Última barra NS/NR ausente: zero aritmético, não precisão de zero.",
    }
    return exclude(
        p, "Conceito de renda não identificado; somente publicado na Projeção."
    )


def release_only(slug, house, registry, start, end, n, method, pub, valid, note):
    source = COMMON.source(COMMON.archive(f"{slug}_102026_23"), "divulgacao.html")
    p = {
        "id": f"{slug}_2026-10-{end}",
        "instituto": house,
        "registro_tse": registry,
        "campo": {"inicio": f"2026-10-{start}", "fim": f"2026-10-{end}"},
        "divulgacao": DAY,
        "n": n,
        "metodo": method,
        "publicado": {"2t": PREVIOUS.vector(pub)},
        "publicado_validos": {"2t": dict(zip(["flavio", "lula"], valid, strict=True))},
        "fonte": {
            **source,
            "tipo": "divulgacao",
            "rotulo": "Divulgação arquivada",
            "conferido_em": CHECKED,
            "nota": note,
            "status": "Resultado confirmado; íntegra não localizada na consulta.",
        },
    }
    return exclude(p, note)


def datatrends():
    return release_only(
        "datatrends",
        "DataTrends",
        "BR-03365/2026",
        "19",
        "21",
        2000,
        "telefônico automatizado",
        [50, 46, 4, 1],
        [51.9, 48.1],
        "Divulgação de 23/10, campo 19–21/10, n=2.000. Total 50/46/4/1 soma 101 "
        "por arredondamento. Válidos publicados 51,9/48,1 preservados. Íntegra "
        "atual não localizada; não transportar perfil ou cruzamentos de 19/10. "
        "Somente publicado na Projeção até obter documentação atual.",
    )


def vetor():
    return release_only(
        "vetor",
        "Vetor/Arrow",
        "BR-06957/2026",
        "22",
        "23",
        6867,
        "telefônico automatizado URA",
        [50, 44.9, 3.6, 1.5],
        [52.7, 47.3],
        "Divulgação de 23/10, campo 22–23/10, 6.867 entrevistas em 1.559 municípios "
        "segundo a divulgação; amostra planejada registrada de 3.000. Release "
        "menciona 824 entrevistas adicionais de jovens, 616 classificações de gênero "
        "pelo nome e 628 municípios não informados. Totais 50/44,9/3,6/1,5 e "
        "válidos oficiais 52,7/47,3. Íntegra não localizada; sem perfil e voto "
        "por renda atuais, somente publicado na Projeção.",
    )


def main():
    polls = [realtime(), alfa(), ipespe(), vox(), verita(), datatrends(), vetor()]
    for p in polls:
        COMMON.write(ROOT / "analysis/reponderacao/pesquisas" / (p["id"] + ".json"), p)
        if "pdf" in p["fonte"]:
            slug = "vox" if p["id"].startswith("vox_brasil") else p["id"].split("_")[0]
            shutil.copyfile(
                ROOT / p["fonte"]["pdf"], ROOT / f"docs/fontes/{slug}_23102026.pdf"
            )
        print(p["id"], "publicado" if p.get("ignorar") else "PNAD condicional")
    presence_path = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
    presence = COMMON.read(presence_path)
    presence["conferido_em"] = CHECKED
    source = polls[2]["fonte"]
    presence["ondas"][polls[2]["id"]] = {
        "tipo": "direto",
        "taxas": {"flavio": 0.94, "lula": 0.90, "indecisos": 0.61},
        "regra": "Seleção pela nota 10 de chance de comparecer (p. 12). Autodeclaração, "
        "não probabilidade calibrada. Aplicar as mesmas taxas à PNAD supõe estabilidade "
        "dentro de cada eleitorado; renda × voto × presença não publicada. "
        "P. 13 publica 50/47/2/1 no subconjunto e válidos 51,5/48,5, preservados "
        "separadamente da projeção Arvor. Não muda as centrais.",
        "fonte": {k: source[k] for k in ["arquivo", "sha256", "url"]}
        | {"paginas": [12, 13]},
        "subconjunto_publicado": {"flavio": 50, "lula": 47},
        "subconjunto_validos_publicado": {"flavio": 51.5, "lula": 48.5},
    }
    houses = {p["instituto"] for p in polls}
    presence["auditoria_ultima_onda"] = [
        p for p in presence["auditoria_ultima_onda"] if p["instituto"] not in houses
    ] + [
        {
            "instituto": p["instituto"],
            "id": p["id"],
            "tipo": "direto" if p["instituto"] == "Ipespe" else "neutro",
            "fonte": p["fonte"]["url"],
            "arquivo": p["fonte"]["arquivo"],
            "nota": (
                "Presença certa por voto atual conferida nas pp. 12–13; geral e subconjunto preservados."
                if p["instituto"] == "Ipespe"
                else "Sem filtro diferencial incorporado nesta onda. Não transportar taxas anteriores "
                "nem converter firmeza ou rejeição em probabilidade de presença."
            ),
        }
        for p in polls
    ]
    COMMON.write(presence_path, presence)
    audit = {
        "data": DAY,
        "conferido_em": CHECKED,
        "pesquisas": polls,
        "regra": "Uma onda por casa em cada central; sem imputar renda ausente ou contraditória.",
        "pendencias": [p["motivo"] for p in polls if p.get("ignorar")],
        "integra_baixada": [p["id"] for p in polls if "pdf" in p["fonte"]],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261023.json", audit)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261023.json", audit)


if __name__ == "__main__":
    main()
