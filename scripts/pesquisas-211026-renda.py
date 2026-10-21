#!/usr/bin/env python3
"""Integra cinco ondas de 21/10 a partir de documentos arquivados e conferidos."""

import importlib
import shutil
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-21"


def base(slug, house, registry, start, end, n, method, pages, count, pub, note):
    poll = PREVIOUS.base(
        f"{slug}_2026-10-{end}",
        house,
        registry,
        (f"2026-10-{start}", f"2026-10-{end}"),
        DAY,
        n,
        method,
        f"{slug}_102026_21",
        pages,
        count,
        pub,
        note,
    )
    poll["fonte"]["conferido_em"] = DAY
    return poll


def verita():
    note = (
        "Relatório fornecido pelo usuário, 17 páginas, campo 15–19/10, n=15.554, "
        "BR-06396/2026. Perfil de renda familiar na p. 4: 41,2/40,1/18,7, "
        "frequências 6.405/6.240/2.909. Etapa antes/depois dos pesos não explicitada: "
        "sensibilidade condicional ao perfil publicado. Total na p. 11: "
        "49,7/48,2/1,4/0,7 (F/L/BN/NS); válidos publicados 50,7/49,3 separados. "
        "«Ausente» 2,1% é subtotal BN + NS, não abstenção. Presença certa de 97,4% "
        "na p. 5 é declaração e não altera o comparecimento das centrais. "
        "Renda e sexo na p. 12 conferidos visualmente e por recomposição. "
        "Voto lembrado, intenção de presença e expectativa de vitória são perguntas distintas."
    )
    poll = base(
        "verita",
        "Veritá",
        "BR-06396/2026",
        "15",
        "19",
        15554,
        "telefônico automatizado URA, reconhecimento de voz e transcrição de áudio",
        {
            "metodologia": [2, 3],
            "perfil_renda": 4,
            "2t_topline": 11,
            "2t_validos": 11,
            "2t_renda": 12,
            "sexo": 12,
        },
        17,
        [49.7, 48.2, 1.4, 0.7],
        note,
    )
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [41.2, 40.1, 18.7],
        [[44.5, 53, 1.4, 1.1], [54.6, 43.7, 1.3, 0.5], [50.7, 47.4, 1.5, 0.3]],
        [[57.5, 40.2, 1.5, 0.8], [42.8, 55.4, 1.2, 0.6]],
        [47.2, 52.8],
        note,
    )
    poll["renda"].update(
        perfil_tipo="perfil_publicado", frequencias_publicadas=[6405, 6240, 2909]
    )
    poll["publicado_validos"] = {"2t": {"flavio": 50.7, "lula": 49.3}}
    poll["conferencia_denominadores"] = {
        "pagina_pdf": 11,
        "frequencias_publicadas": {
            "flavio": 7729,
            "lula": 7502,
            "branco_nulo": 211,
            "indecisos": 112,
        },
        "subtotal_candidatos_publicado": 15231,
        "subtotal_ausente_pct": 2.1,
        "ausente_e_subtotal_bn_ns_nr": True,
        "abstencao_2t_medida": False,
    }
    return poll


def palver():
    note = (
        "Onda 8, íntegra de 112 páginas. Campo 18–20/10, n=5.000, BR-04612/2026. "
        "Perfil ponderado p. 20: renda familiar 36/41/23 e sexo 48/52; não usar as "
        "contagens brutas nem as metas não arredondadas como perfil realizado. "
        "Total 50/48/1/0 nas pp. 23–24 soma 99 por arredondamento; zero de indecisos "
        "é arredondado. O grupo de 1% reúne branco/nulo ou não votaria, sem separar "
        "abstenção. Renda e sexo na p. 25. Método v3 permanece igual ao da onda 7: "
        "PNADC 2025, 1ª entrevista, voto no 2T/2022, filiação partidária e voto "
        "no 1T/2026 por região; mudança apenas no questionário. Comparação 7→8 "
        "admitida pelo instituto; não estender essa comparabilidade à onda 6."
    )
    poll = base(
        "palver",
        "Palver",
        "BR-04612/2026",
        "18",
        "20",
        5000,
        "online, recrutamento por anúncios em redes sociais; não probabilística, raking v3",
        {
            "metodologia": "12–18",
            "perfil_renda": 20,
            "2t_topline": [23, 24],
            "2t_renda": 25,
            "sexo": 25,
        },
        112,
        [50, 48, 1, 0],
        note,
    )
    PREVIOUS.income(
        poll,
        [2, 5, None],
        [36, 41, 23],
        [[48, 51, 1, 1], [53, 45, 1, 0], [49, 50, 1, 0]],
        [[55, 43, 1, 0], [46, 53, 1, 0]],
        [48, 52],
        note,
    )
    poll["metodologia_onda"] = {
        "versao": "v3",
        "pnad": "PNADC 2025, 1ª entrevista",
        "voto_1t_2026_por_regiao": True,
        "comparavel_onda_anterior": True,
        "n_efetivo": 1745,
        "efeito_pesos": 2.86,
        "margem_publicada_pp": 2.4,
    }
    return poll


def published_only(poll, reason):
    poll.update(ignorar=True, cruzamentos={}, motivo=reason)
    return poll


def futura():
    note = (
        "Íntegra de 18 páginas. BR-06614/2026, campo 19–20/10, n=2.000. "
        "Estimulada p. 10: 48,9/46,8/2/2,3; válidos p. 12: 51,1/48,9. "
        "Não confundir com espontânea 47,2/46,1. Perfil familiar na p. 7, "
        "mas cruzamentos de voto da p. 11 contêm somente sexo, região e idade. "
        "Sem voto por renda, entra pelo publicado na Projeção."
    )
    poll = base(
        "futura",
        "Futura",
        "BR-06614/2026",
        "19",
        "20",
        2000,
        "telefônico CATI",
        {
            "metodologia": 4,
            "perfil_renda": 7,
            "2t_topline": 10,
            "sexo": 11,
            "2t_validos": 12,
        },
        18,
        [48.9, 46.8, 2, 2.3],
        note,
    )
    poll["publicado_validos"] = {"2t": {"flavio": 51.1, "lula": 48.9}}
    poll["contratante"] = "100% Cidades"
    return published_only(
        poll, "Íntegra sem voto por renda; somente publicado na Projeção."
    )


def ideia():
    note = (
        "Íntegra pública de 59 páginas do contratante Meio. Campo 15–19/10, "
        "n=1.500, BR-08251/2026. P. 7: 48/46/3,4/2,6 no total; p. 6: "
        "51,1/48,9 nos válidos, preservados separadamente. O PDF publica recortes "
        "temáticos, mas não fornece perfil de renda familiar e voto por suas faixas. "
        "As cotas de sexo/idade/escolaridade/atividade da p. 58 não substituem renda. "
        "Sem ajuste PNAD, somente publicado na Projeção."
    )
    poll = base(
        "ideia",
        "Meio/Ideia",
        "BR-08251/2026",
        "15",
        "19",
        1500,
        "telefônico, questionário estruturado",
        {"metodologia": [2, 58], "2t_topline": 7, "2t_validos": 6},
        59,
        [48, 46, 3.4, 2.6],
        note,
    )
    poll["contratante"] = "Meio"
    poll["publicado_validos"] = {"2t": {"flavio": 51.1, "lula": 48.9}}
    return published_only(poll, "Sem perfil e cruzamento de renda na íntegra pública.")


def quaest_values(chart):
    """Seleciona a data explicitamente: a API agora entrega uma série de ondas."""
    names = {
        "Flávio Bolsonaro": "flavio",
        "Lula": "lula",
        "Branco/Nulo/Não Vai Votar": "branco_nulo",
        "Indecisos": "indecisos",
    }
    result = {}
    for option in chart["data"]:
        points = [v for v in option["values"] if v["date"] == DAY + "T00:00:00Z"]
        if len(points) != 1 or option["option"] not in names:
            raise ValueError("Onda ou opção inesperada no painel Quaest")
        result[names[option["option"]]] = round(100 * points[0]["value"], 6)
    if set(result) != set(PREVIOUS.OPTIONS):
        raise ValueError("Painel Quaest incompleto")
    return result


def quaest():
    folder = "quaest_102026_21"
    items = COMMON.archive(folder)
    item = COMMON.source(items, "g1-estimulada.json")
    raw = COMMON.read(ROOT / item["arquivo"])["resultado"]
    published = quaest_values(raw["cenarios"][0])
    if published != {"flavio": 45, "lula": 44, "branco_nulo": 9, "indecisos": 2}:
        raise ValueError("Resultado Quaest divergente da divulgação")
    note = (
        "Campo 17–20/10, n=2.154, BR-08535/2026, divulgação 21/10. "
        "Painel/API do G1 arquivados; seleção explícita de 21/10 na série, sem "
        "reutilizar a onda de 14/10. Total 45/44/9/2; grupo de 9% junta "
        "branco/nulo/não vai votar e não identifica abstenção. Há voto por renda "
        "atual, mas não perfil realizado nem bases ponderadas no painel. Íntegra "
        "não localizada nesta consulta; Poder360 informa disponibilidade no dia "
        "seguinte. Não transportar o perfil 31/42/27 da onda anterior: "
        "somente publicado na Projeção, fora da Média até conferir o perfil atual."
    )
    poll = {
        "id": "quaest_2026-10-20",
        "instituto": "Quaest",
        "registro_tse": "BR-08535/2026",
        "contratante": "TV Globo e O Globo",
        "campo": {"inicio": "2026-10-17", "fim": "2026-10-20"},
        "divulgacao": DAY,
        "n": 2154,
        "metodo": "presencial domiciliar",
        "publicado": {"2t": published},
        "fonte": {
            **item,
            "tipo": "painel",
            "rotulo": "G1: painel Quaest de 21/10",
            "conferido_em": DAY,
            "status": "Painel atual arquivado; íntegra pendente.",
            "nota": note,
        },
        "cruzamentos_documentais": [
            {
                "dimensao": x["bandeira"],
                "recorte": x["variavel_cruzamento"],
                "votos": quaest_values(x),
                "base": None,
            }
            for x in raw["estratos"]
            if x["bandeira"] in ("Renda", "Sexo")
        ],
    }
    return published_only(
        poll, "Perfil de renda atual não localizado; íntegra pendente."
    )


def main():
    polls = [verita(), palver(), futura(), ideia(), quaest()]
    for poll in polls:
        COMMON.write(
            ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
        )
        if "pdf" in poll["fonte"]:
            slug = poll["id"].split("_")[0]
            shutil.copyfile(
                ROOT / poll["fonte"]["pdf"],
                ROOT / "docs/fontes" / f"{slug}_21102026.pdf",
            )
        print(poll["id"], "publicado" if poll.get("ignorar") else "PNAD")
    audit = {
        "data": DAY,
        "pesquisas": polls,
        "regra": "Uma onda por casa; histórico e snapshots publicados preservados.",
        "escopo_varredura": {
            "periodo_divulgacao": ["2026-10-20", DAY],
            "novas": [p["id"] for p in polls],
            "ja_integradas_20_10": [
                "realtime_2026-10-19",
                "alfa_2026-10-19",
                "franca_2026-10-20",
                "gerp_2026-10-19",
                "ranking_2026-10-16",
            ],
            "revisao_ja_integrada": "datatrends_2026-10-17",
        },
        "varredura": [
            {
                "instituto": "Quaest",
                "status": "Publicado na Projeção; sem PNAD",
                "conclusao": "Íntegra e perfil de renda atual pendentes; cruzamentos atuais arquivados.",
                "pendente": True,
                "fontes": [
                    "https://especiaisg1.globo/politica/eleicoes/2026/pesquisas-eleitorais/presidente/2-turno/Quaest/internal/"
                ],
            }
        ],
        "pendencias": [
            "Quaest: íntegra e perfil de renda da onda atual.",
            "Gerp e Data Ranking de 20/10: íntegra ainda não localizada.",
            "França de 20/10: incompatibilidade entre total e cruzamentos permanece.",
        ],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261021.json", audit)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261021.json", audit)


if __name__ == "__main__":
    main()
