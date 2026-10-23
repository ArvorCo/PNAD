#!/usr/bin/env python3
"""Integra a divulgação de 22/10; não transforma metas do registro em bases."""

import hashlib
import importlib
import shutil
from copy import deepcopy
from pathlib import Path

COMMON = importlib.import_module("pesquisas-081026-renda")
ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/originals/datafolha_102026_22"
DAY = "2026-10-22"
PAGE = "https://especiaisg1.globo/politica/eleicoes/2026/pesquisas-eleitorais/presidente/2-turno/Datafolha/internal/"
API = "https://especiaisg1.globo/api/pesquisas-eleitorais/graficos/216/"
TSE = "https://pesqele-divulgacao.tse.jus.br/app/pesquisa/listar.xhtml"
OPTIONS = ["flavio", "lula", "branco_nulo", "indecisos"]
NAMES = {
    "Flavio Bolsonaro": "flavio",
    "Lula": "lula",
    "Em Branco/Nulo/Nenhum": "branco_nulo",
    "Indecisos": "indecisos",
}


def current(chart):
    """Seleciona por data, nunca pela posição da onda na API."""
    result = {}
    for item in chart["data"]:
        values = [v for v in item["values"] if v["date"] == DAY + "T00:00:00Z"]
        if len(values) != 1:
            raise ValueError("Onda atual ausente ou duplicada no painel")
        result[NAMES[item["option"]]] = round(100 * values[0]["value"], 6)
    return result


def record(name, url):
    path = FOLDER / name
    raw = path.read_bytes()
    return {
        "arquivo": str(path.relative_to(ROOT)),
        "url": url,
        "rotulo": {
            "g1_painel.html": "Painel G1",
            "g1_estimulada.json": "G1: estimulada e cruzamentos",
            "g1_validos.json": "G1: votos válidos divulgados",
            "registro-tse.txt": "TSE: registro BR-09709/2026",
            "registro-plano-amostral.txt": "TSE: detalhamento do plano amostral",
        }[name],
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def datafolha():
    raw = COMMON.read(FOLDER / "g1_estimulada.json")["resultado"]
    valid = COMMON.read(FOLDER / "g1_validos.json")["resultado"]
    strata = [
        {
            "dimensao": row["bandeira"],
            "recorte": row["variavel_cruzamento"],
            "valores_pct": current(row),
            "base": None,
            "margem_publicada_pp": row["margem"],
        }
        for row in raw["estratos"]
    ]
    income = {
        r["recorte"]: r["valores_pct"] for r in strata if r["dimensao"] == "Renda"
    }
    bands = ["Até 2 s.m.", "Mais de 2 a 5 s.m", "Mais de 5 s.m."]
    note = (
        "Divulgação de 22/10: F/L/BN/NS 47/46/5/2; válidos oficiais 50/50. "
        "Campo 20–22/10 e n=2.520 confirmados no painel G1 e no registro "
        "BR-09709/2026. O registro descreve 2.520 como amostra prevista; o G1 "
        "informa 2.520 ouvidos. Cruzamentos atuais de renda: 39/54/5/2, "
        "54/39/6/1 e 54/40/5/1. As bases efetivas dos recortes não estão no painel. "
        "O TSE traz referência 49/47/4 (até 2 SM, mais de 2 SM, NS/recusa), "
        "fator previsto de renda 1; não é perfil observado nem separa as duas "
        "faixas superiores. Relatório completo não fornecido pela empresa no "
        "TSE na consulta. Entra pelo publicado na Projeção; sem ajuste PNAD "
        "até obter as bases atuais, sem transportar pesos da onda anterior. "
        "A passagem de PNAD na onda anterior a publicado nesta pode afetar a tendência. "
        "Válidos divulgados preservados separadamente da normalização 47/93."
    )
    sources = [
        record("g1_painel.html", PAGE),
        record(
            "g1_estimulada.json",
            API + "?tipo_pergunta=ESTIMULADA-PRE-201&instituto=Datafolha",
        ),
        record(
            "g1_validos.json",
            API + "?tipo_pergunta=VTSVALIDOS-PRE-201&instituto=Datafolha",
        ),
        record("registro-tse.txt", TSE),
        record(
            "registro-plano-amostral.txt",
            "https://pesqele-divulgacao.tse.jus.br/app/pesquisa/metodologia/registroDetalhamento.xhtml?id=457618",
        ),
    ]
    return {
        "id": "datafolha_2026-10-22",
        "instituto": "Datafolha",
        "registro_tse": "BR-09709/2026",
        "divulgacao": DAY,
        "campo": {"inicio": "2026-10-20", "fim": DAY},
        "n": 2520,
        "contratante": "Folha de S.Paulo e TV Globo",
        "metodo": "presencial, pontos de fluxo",
        "publicado": {"2t": current(raw["cenarios"][0])},
        "publicado_validos": {"2t": current(valid["cenarios"][0])},
        "fonte": {
            **sources[0],
            "tipo": "painel_contratante",
            "rotulo": "Painel G1 e registro TSE conferidos",
            "conferido_em": DAY,
            "status": "Cruzamentos atuais arquivados; bases de renda pendentes.",
            "paginas": {},
            "nota": note,
            "complementos": sources[1:],
        },
        "ignorar": True,
        "motivo": "Bases atuais de renda ausentes no painel; referências do TSE são metas, não perfil realizado. Publicado disponível na Projeção.",
        "cruzamentos": {},
        "cruzamentos_documentais": {
            "opcoes": OPTIONS,
            "faixas": bands,
            "linhas": [[income[b][c] for c in OPTIONS] for b in bands],
            "bases": [None, None, None],
            "nota": note,
        },
        "registro_conferido": {
            "n_previsto": 2520,
            "n_divulgado_g1": 2520,
            "renda_referencia_pct": [49, 47, 4],
            "renda_referencia_faixas": ["Até 2 SM", "Mais de 2 SM", "NS/recusa"],
            "fator_renda_previsto": 1,
            "usado_como_perfil": False,
            "integra_anexada": False,
        },
        "painel_recortes": strata,
    }


def previa():
    """Hipótese solicitada: perfil e cobertura de 15/10, votos de 22/10."""
    poll = datafolha()
    old = COMMON.read(
        ROOT / "analysis/reponderacao/pesquisas/datafolha_2026-10-14.json"
    )
    note = (
        "PRÉVIA PNAD: cruzamentos atuais de 22/10 com perfil de renda emprestado "
        "da Datafolha divulgada em 15/10 (campo 13–14/10). Bases de referência "
        "1.172/918/335; cobertura assumida 2.425/2.520 (96,23%). Os 95/2.520 "
        "restantes conservam o topline atual. Essas bases e essa cobertura não "
        "foram observadas na onda de 22/10: sua estabilidade é hipótese provisória. "
        "Votos por renda de 22/10: 39/54/5/2, 54/39/6/1 e 54/40/5/1 (F/L/BN/NS). "
        "Total atual 47/46/5/2, n=2.520, campo 20–22/10, BR-09709/2026. "
        "Válidos oficiais 50/50 preservados. Prévia incluída nas duas centrais e "
        "na tendência; substituir o perfil quando saírem as bases atuais. "
        "Não é ajuste confirmado pela íntegra atual nem provável eleitor medido."
    )
    poll.pop("ignorar")
    poll.pop("motivo")
    poll["renda"] = deepcopy(old["renda"])
    poll["renda"].pop("bases", None)
    poll["renda"].pop("nao_publicada_n", None)
    poll["renda"].update(
        perfil_tipo="hipotese_onda_anterior",
        nota=note,
        bases_referencia=old["renda"]["bases"],
        referencia_id=old["id"],
        referencia_divulgacao=old["divulgacao"],
    )
    poll["cruzamentos"] = {
        "2t": {
            "opcoes": OPTIONS,
            "linhas": poll["cruzamentos_documentais"]["linhas"],
            "nota": note,
        }
    }
    poll["fonte"].update(status="Prévia PNAD · perfil da onda de 15/10", nota=note)
    ref = {k: old["fonte"][k] for k in ("arquivo", "url", "bytes", "sha256")}
    ref["rotulo"] = "Perfil emprestado: Datafolha de 15/10, anexo p. 8"
    poll["fonte"]["complementos"].append(ref)
    return poll


def completa():
    """Revisa a mesma onda com bases atuais; mantém a prévia reproduzível."""
    from datafolha_221026.extract import tables

    helper = importlib.import_module("pesquisas-131026-renda")
    poll = datafolha()
    segments = tables()["voto"]["segments"]
    note = (
        "Íntegra oficial de 36 páginas publicada em 23/10, campo 20–22/10, "
        "2.520 entrevistas em 154 municípios, BR-09709/2026. P. 22 declara "
        "bases ponderadas. P. 27 (anexo p. 8): renda 1.171/913/341, soma 2.425; "
        "95 sem renda conservam o publicado. Cruzamentos F/L/BN/I atuais "
        "39/54/5/2, 54/39/6/1, 54/40/5/1. Substitui a hipótese de bases "
        "emprestadas de 15/10, sem criar nova onda. Válidos oficiais 50/50 "
        "preservados separadamente da normalização dos inteiros 47/93. "
        "P. 9 indica base de 2.347 entrevistas; p. 28 declara base ponderada "
        "2.351: naturezas distintas, sem converter bases em contagens de voto. "
        "Ajuste PNAD é sensibilidade de composição, não correção do voto."
    )
    original = poll["fonte"]
    poll.pop("ignorar")
    poll.pop("motivo")
    labels = list(segments["total"]["responses"])

    def rows(names):
        return [[segments[n]["responses"][k] for k in labels] for n in names]

    def bases(names):
        return [segments[n]["base_ponderada"] for n in names]

    bands = ["até 2 SM", "2–5 SM", ">5 SM"]
    sex = ["homens", "mulheres"]
    weights = bases(bands)
    helper.income(
        poll,
        [2, 5, None],
        weights,
        rows(bands),
        rows(sex),
        bases(sex),
        note,
        100 * sum(weights) / poll["n"],
    )
    poll["renda"].update(bases=weights, nao_publicada_n=poll["n"] - sum(weights))
    regions = ["Sudeste", "Sul", "Nordeste", "CO/Norte"]
    poll["controles"]["2t"]["regiao"] = helper.control(
        poll["publicado"]["2t"], rows(regions), bases(regions)
    )
    poll["cruzamentos_documentais"].update(bases=weights, nota=note)
    poll["fonte"] = helper.source(
        "datafolha_102026_22_integra",
        {
            "metodologia": [2, 22],
            "perfil_renda": 24,
            "2t_topline": 8,
            "2t_renda": 27,
            "sexo": 27,
            "regiao": 27,
            "2t_validos": [9, 28],
        },
        36,
        note,
    )
    poll["fonte"].update(conferido_em="2026-10-23", publicado_em="2026-10-23")
    poll["fonte"]["complementos"] = [
        {k: original[k] for k in ("arquivo", "url", "bytes", "sha256", "rotulo")},
        *original["complementos"],
        {
            **COMMON.source(
                COMMON.archive("datafolha_102026_22_integra"), "datafolha.html"
            ),
            "rotulo": "Divulgação oficial e link para a íntegra de 23/10",
        },
    ]
    poll["registro_conferido"].update(
        consulta_em="2026-10-22",
        integra_oficial_obtida_em="2026-10-23",
        nota="Anexo no TSE não reconsultado; íntegra obtida no site oficial do Datafolha.",
    )
    return poll


def main():
    poll = completa()
    sources = [
        {k: poll["fonte"][k] for k in ("arquivo", "url", "bytes", "sha256")},
        *poll["fonte"]["complementos"],
    ]
    COMMON.write(
        ROOT / "analysis/reponderacao/pesquisas" / (poll["id"] + ".json"), poll
    )
    audit = {
        "referencia": DAY,
        "pesquisa": poll,
        "fontes": sources,
        "revisao_em": "2026-10-23",
        "pendencias": [
            "Percentuais não arredondados e pesos individuais não publicados."
        ],
    }
    COMMON.write(
        ROOT / "analysis/reponderacao/auditoria_datafolha_20261022_integra.json", audit
    )
    COMMON.write(
        ROOT / "docs/assets/reponderacao_datafolha_20261022_integra.json", audit
    )
    shutil.copyfile(
        FOLDER / "registro-tse.txt",
        ROOT / "docs/fontes/datafolha_22102026_registro.txt",
    )
    print(
        "Datafolha 22/10: íntegra atual, bases 1.171/913/341; prévia preservada no arquivo."
    )


if __name__ == "__main__":
    main()
