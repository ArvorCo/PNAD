#!/usr/bin/env python3
"""Rodada de 20/10: fontes locais verificadas e revisão da DataTrends de 19/10."""

import importlib
import shutil
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
PREVIOUS = importlib.import_module("pesquisas-131026-renda")
ROOT = Path(__file__).resolve().parents[1]
DAY = "2026-10-20"


def base(*args):
    poll = PREVIOUS.base(*args)
    poll["fonte"]["conferido_em"] = DAY
    return poll


def income(poll, weights, rows, sex_rows, sex_weights):
    PREVIOUS.income(
        poll, [2, 5, None], weights, rows, sex_rows, sex_weights, poll["fonte"]["nota"]
    )
    poll["renda"]["perfil_tipo"] = "perfil_publicado"
    return poll


def realtime():
    note = (
        "Íntegra de 48 páginas, campo 15–19/10, 2.000 entrevistas. Estimulada p. 8: "
        "48/45/5/2; não confundir com espontânea 47/44/5/4. Válidos 52/48 na p. 16. "
        "Perfil 46/33/21 na p. 3; renda p. 11 e sexo p. 9. O registro atual no PesqEle "
        "define renda domiciliar mensal; o PDF abrevia o conceito. Perfil publicado sem "
        "etapa pré/pós-pesos explícita: sensibilidade condicional. O PDF descreve entrevistas "
        "telefônicas com entrevistadores; o plano registrado também admite IA e mensagens "
        "digitais, sem informar a participação efetiva dessas modalidades."
    )
    poll = base(
        "realtime_2026-10-19",
        "Real Time Big Data",
        "BR-02952/2026",
        ("2026-10-15", "2026-10-19"),
        DAY,
        2000,
        "telefônico com entrevistadores, conforme relatório",
        "realtime_102026_20",
        {
            "metodologia": 2,
            "perfil_renda": 3,
            "2t_topline": 8,
            "2t_renda": 11,
            "sexo": 9,
            "2t_validos": 16,
        },
        48,
        [48, 45, 5, 2],
        note,
    )
    poll["publicado_validos"] = {"2t": {"flavio": 52, "lula": 48}}
    poll["fonte"]["registro_conferencia"] = COMMON.source(
        COMMON.archive("realtime_102026_20"), "registro-conferencia.txt"
    )
    return income(
        poll,
        [46, 33, 21],
        [[39, 54, 5, 2], [51, 41, 6, 2], [61, 33, 3, 3]],
        [[52, 41, 6, 1], [45, 49, 4, 2]],
        [47, 53],
    )


def alfa():
    note = (
        "Íntegra de 48 páginas, campo 15–19/10, n=2.700. Estimulada 48,8/45,9/3,5/1,8 "
        "na p. 13 e válidos 51,5/48,5 na p. 14. Perfil familiar publicado 40/37/23 "
        "na p. 6; bases 1.115/982/603 não reproduzem esses percentuais. A etapa do perfil "
        "antes/depois dos pesos não está explícita: sensibilidade condicional aos percentuais "
        "publicados, sem tratar contagens como pesos. Cruzamentos p. 16 e sexo p. 15."
    )
    poll = base(
        "alfa_2026-10-19",
        "Alfa Inteligência/TMC",
        "BR-00820/2026",
        ("2026-10-15", "2026-10-19"),
        DAY,
        2700,
        "entrevistas pessoais; municípios por PPT e cotas de entrevistados",
        "alfa_102026_20",
        {
            "metodologia": 5,
            "perfil_renda": 6,
            "2t_topline": 13,
            "2t_validos": 14,
            "sexo": 15,
            "2t_renda": 16,
        },
        48,
        [48.8, 45.9, 3.5, 1.8],
        note,
    )
    poll["contratante"] = "Alfa Inteligência, recursos próprios"
    poll["publicado_validos"] = {"2t": {"flavio": 51.5, "lula": 48.5}}
    poll["bases_renda_publicadas"] = [1115, 982, 603]
    return income(
        poll,
        [40, 37, 23],
        [[43, 52, 3, 2], [51, 44, 4, 1], [56, 40, 3, 1]],
        [[52, 44, 4, 0], [46, 49, 3, 2]],
        [47, 53],
    )


def datatrends():
    note = (
        "Revisão em 20/10 da mesma onda divulgada em 19/10, sem duplicação. Íntegra de "
        "38 páginas, campo 15–17/10, BR-04454/2026. As pp. 4 e 7 definem renda domiciliar "
        "total, resolvendo o conceito desta onda, sem revisar a onda anterior. Perfil da "
        "amostra 46/35/19 na p. 7; alvos declarados 46,7/34,6/18,7 na p. 3 são distintos. "
        "Etapa do perfil antes/depois dos pesos não explicitada: sensibilidade condicional "
        "a 46/35/19. Cruzamentos precisos de renda e sexo na p. 32. Topline 49/46/4/1 "
        "e válidos publicados 51,5/48,5. O relatório declara ausência de recusas de renda "
        "na base final e ponderação por UF, sexo, idade, escolaridade e renda."
    )
    poll = base(
        "datatrends_2026-10-17",
        "DataTrends",
        "BR-04454/2026",
        ("2026-10-15", "2026-10-17"),
        "2026-10-19",
        2000,
        "telefônico automatizado URA/DTMF, 27 UFs",
        "datatrends_102026_19_integra",
        {
            "metodologia": "3–4",
            "perfil_renda": 7,
            "perfil_sexo": 6,
            "2t_topline": 12,
            "2t_validos": 4,
            "2t_renda": 32,
            "sexo": 32,
        },
        38,
        [49, 46, 4, 1],
        note,
    )
    poll["publicado_validos"] = {"2t": {"flavio": 51.5, "lula": 48.5}}
    poll["contratante"] = "não informado no relatório consultado"
    poll["alvos_renda_declarados"] = [46.7, 34.6, 18.7]
    poll["revisao"] = {
        "data": DAY,
        "inventario_inicial": "analysis/reponderacao/auditoria_20261019_complemento.json",
    }
    return income(
        poll,
        [46, 35, 19],
        [[46.4, 49.3, 3.3, 1], [50.6, 43.8, 4.5, 1.1], [50.1, 40.1, 7, 2.8]],
        [[51.5, 43.3, 3.9, 1.3], [45.9, 47.8, 4.8, 1.5]],
        [47, 53],
    )


def failed_control(published, rows, weights):
    """Preserva discrepâncias como diagnóstico, sem afrouxar a validação de renda."""
    recomposed = {
        k: sum(w * row[i] for w, row in zip(weights, rows, strict=True)) / sum(weights)
        for i, k in enumerate(PREVIOUS.OPTIONS)
    }
    residual = {k: recomposed[k] - published[k] for k in recomposed}
    return {
        "pesos": weights,
        "linhas": rows,
        "opcoes": PREVIOUS.OPTIONS,
        "recomposto": recomposed,
        "residuo": residual,
        "residuo_max_abs": max(map(abs, residual.values())),
        "aprovado": False,
    }


def franca():
    note = (
        "Íntegra de 14 páginas, campo 16–20/10, n=3.000. Total p. 6: "
        "40,95/39,65/10,56/8,84; válidos 50,81/49,19 na tabela (p. 5 arredonda para "
        "50,8/49,2). Perfil ponderado familiar 41,9/34,9/23,2 na p. 3. "
        "Os cruzamentos por renda da p. 11 e sexo da p. 8 NÃO recompõem o total. "
        "Indecisos por renda variam de 1,2% a 4%, impossíveis de produzir os 8,84% "
        "do total com qualquer combinação de pesos. Transcrições e resíduos preservados "
        "no inventário de auditoria; sem ajuste PNAD. Somente publicado na Projeção."
    )
    poll = base(
        "franca_2026-10-20",
        "Instituto França",
        "BR-07896/2026",
        ("2026-10-16", "2026-10-20"),
        DAY,
        3000,
        "telefônico CATI; consolidação e ponderação territorial por UF/DDD",
        "franca_102026_20",
        {
            "metodologia": "3–4",
            "perfil_renda": 3,
            "2t_topline": 6,
            "2t_validos": 6,
            "sexo": 8,
            "2t_renda": 11,
        },
        14,
        [40.95, 39.65, 10.56, 8.84],
        note,
    )
    poll["contratante"] = "não informado no relatório consultado"
    poll.update(
        ignorar=True,
        cruzamentos={},
        motivo="Cruzamentos incompatíveis com o total; somente publicado na Projeção.",
        publicado_validos={"2t": {"flavio": 50.81, "lula": 49.19}},
    )
    poll["auditoria_cruzamentos"] = {
        "renda": failed_control(
            poll["publicado"]["2t"],
            [[33.4, 52.9, 9.7, 4], [54.1, 37.3, 7.3, 1.3], [53.8, 34.3, 10.7, 1.2]],
            [41.9, 34.9, 23.2],
        ),
        "sexo": failed_control(
            poll["publicado"]["2t"],
            [[46.5, 37.8, 12.5, 3.2], [36, 45.3, 9.5, 9.2]],
            [47.3, 52.7],
        ),
    }
    return poll


def published_only(ident, house, registry, field, n, method, folder, pub, valid, note):
    source = COMMON.source(COMMON.archive(folder), "divulgacao.html")
    return {
        "id": ident,
        "instituto": house,
        "registro_tse": registry,
        "campo": {"inicio": field[0], "fim": field[1]},
        "divulgacao": DAY,
        "n": n,
        "metodo": method,
        "publicado": {"2t": PREVIOUS.vector(pub)},
        "publicado_validos": {"2t": dict(zip(["flavio", "lula"], valid, strict=True))},
        "ignorar": True,
        "cruzamentos": {},
        "motivo": "Sem perfil e voto por renda atuais conferidos; somente publicado na Projeção.",
        "fonte": {
            **source,
            "tipo": "divulgacao",
            "rotulo": "Divulgação arquivada",
            "conferido_em": DAY,
            "status": "Resultado conferido; íntegra pendente.",
            "nota": note,
        },
    }


def gerp():
    note = (
        "Divulgação exclusiva Times Brasil/CNBC em 20/10: 2.400 entrevistas, campo "
        "15–19/10, média móvel de três dias; datas individuais não especificadas. "
        "Estimulada 50/45/2/3, sem alteração do total em relação à rodada anterior. "
        "Válidos divulgados 53/47 preservados separadamente da normalização dos inteiros. "
        "Íntegra atual não localizada no catálogo oficial, que ainda termina em 16/10; "
        "não transportar seu perfil de renda. Registro desta divulgação ainda não confirmado. "
        "BR-03835/2026 foi descartado: no PesqEle corresponde a campo 17–20/10 e divulgação "
        "21/10, outra onda. Somente publicado na Projeção."
    )
    return published_only(
        "gerp_2026-10-19",
        "Gerp",
        "não confirmado",
        ("2026-10-15", "2026-10-19"),
        2400,
        "tracking telefônico, média móvel de três dias",
        "gerp_102026_20",
        [50, 45, 2, 3],
        [53, 47],
        note,
    )


def ranking():
    note = (
        "Divulgação do contratante Fonte83 em 20/10; campo 14–16/10 confirmado no "
        "PesqEle, que prevê divulgação a partir de 19/10. BR-00152/2026, n=2.100. "
        "Total 44,6/45,4/6/4 e válidos publicados 49,6/50,4. Entrevistas pessoais "
        "domiciliares em conglomerados; margem divulgada de 2,15 pp calculada sob "
        "amostragem aleatória simples, sem efeito de desenho. Alvos do registro não "
        "são perfil realizado: sem voto por renda e perfil atual, somente publicado na Projeção."
    )
    poll = published_only(
        "ranking_2026-10-16",
        "Data Ranking",
        "BR-00152/2026",
        ("2026-10-14", "2026-10-16"),
        2100,
        "pessoal domiciliar, conglomerados e cotas",
        "ranking_102026_20",
        [44.6, 45.4, 6, 4],
        [49.6, 50.4],
        note,
    )
    poll["contratante"] = "Fonte83 / Inteligencia.com Serviços Ltda."
    return poll


def main():
    polls = [realtime(), alfa(), datatrends(), franca(), gerp(), ranking()]
    for poll in polls:
        COMMON.write(
            ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
        )
        if "pdf" in poll["fonte"]:
            slug = poll["id"].split("_")[0]
            day = "19102026" if slug == "datatrends" else "20102026"
            shutil.copyfile(
                ROOT / poll["fonte"]["pdf"], ROOT / "docs/fontes" / f"{slug}_{day}.pdf"
            )
        print(poll["id"], "publicado" if poll.get("ignorar") else "PNAD condicional")
    audit = {
        "data": DAY,
        "pesquisas": polls,
        "regra": "Uma onda por casa; revisão DataTrends sem duplicação; snapshots preservados.",
        "pendencias": [
            "Gerp: íntegra atual e código do registro.",
            "Data Ranking: íntegra e cruzamentos por renda.",
            "França: reconciliar totais com cruzamentos antes de qualquer ajuste PNAD.",
        ],
    }
    COMMON.write(ROOT / "analysis/reponderacao/auditoria_20261020.json", audit)
    COMMON.write(ROOT / "docs/assets/reponderacao_20261020.json", audit)


if __name__ == "__main__":
    main()
