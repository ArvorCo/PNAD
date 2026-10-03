"""Erro das pesquisas de 2022 contra o TSE, lido para a página da previsão.

A fonte é ``analysis/predicao_2026/erro_2022/erro_2022.json``, gerado por
``scripts/predicao-2026-erro-2022.py``. Este módulo só copia, com arquivo e
hash, e repareia as casas com o desvio relativo de 2026 do build corrente. O
erro comum de 2022 vira duas sensibilidades simétricas; a central não muda.
"""

from __future__ import annotations

from .base import read
from .tse import ROOT, sha

SOURCE = ROOT / "analysis/predicao_2026/erro_2022/erro_2022.json"
MEMO = ROOT / "analysis/predicao_2026/erro_2022/memorando.md"
SENS_REPEAT = "Se o erro comum de 2022 se repetisse (pesquisas superestimando Lula)"
SENS_INVERTED = "Se o erro comum de 2022 se repetisse com sinal invertido"

# Quando a casa de 2026 não é o mesmo instituto de 2022, e sim marca ou grupo.
LINK = {
    "fsb_btg": "Grupo: FSB/BTG em 2022, Nexus (mesmo grupo) em 2026",
    "ideia": "Marca: Exame/Ideia em 2022, Meio/Ideia em 2026",
}
SAME = "Mesmo instituto"

HOUSE_FIELDS = (
    "id",
    "casa",
    "casa_2026",
    "nivel",
    "incluir",
    "motivo_exclusao",
    "registro",
    "campo",
    "n",
    "metodo",
    "base_validos",
    "validos_pp",
    "erro_pp",
    "diferenca_lula_menos_bolsonaro",
    "erro_absoluto_medio_pp",
    "margem_95_diferenca_aas_pp",
    "erro_diferenca_fora_da_margem_aas",
)


def shifts(source=None):
    """Deslocamentos em F−L nas duas direções, lidos do JSON, nunca digitados."""
    d = read(SOURCE) if source is None else source
    s = d["aplicacao_2026"]["deslocamentos_pp_em_flavio_menos_lula"]
    return float(s["repeticao_de_2022"]), float(s["direcao_oposta"])


def pairing(source, house_effects):
    """Casas da média principal de 2022 que publicaram em 2026, com o build atual."""
    main = set(source["media_das_casas"]["casas"])
    rows = []
    for house in source["por_casa"]:
        name = house.get("casa_2026")
        if house["id"] not in main or name not in house_effects:
            continue
        effect = house_effects[name]
        rows.append(
            {
                "id": house["id"],
                "casa_2022": house["casa"],
                "casa_2026": name,
                "ligacao": LINK.get(house["id"], SAME),
                "erro_2022_diferenca_lula_menos_bolsonaro_pp": house[
                    "diferenca_lula_menos_bolsonaro"
                ]["erro"],
                "desvio_relativo_2026_lula_menos_flavio_pp": effect["desvio_margem_pp"],
                "ondas_2026": effect["n_ondas"],
            }
        )
    return rows


def block(house_effects):
    """Bloco ``erro_2022`` do payload: medição histórica, fontes e hashes."""
    d = read(SOURCE)
    official = d["resultado_oficial"]
    shares = official["parcelas_validos_pp"]
    return {
        "natureza": "Medição histórica de uma eleição; usada como cenário nas duas direções, nunca como prognóstico nem como ajuste da central",
        "fonte": {
            "arquivo": str(SOURCE.relative_to(ROOT)),
            "sha256": sha(SOURCE),
            "gerado_por": d["gerado_por"],
            "memorando": {"arquivo": str(MEMO.relative_to(ROOT)), "sha256": sha(MEMO)},
            "transcricao": d["transcricao"],
        },
        "convencao_de_sinal": d["convencao_de_sinal"],
        "resultado_oficial": {
            k: official[k]
            for k in (
                "fonte",
                "sha256",
                "fonte_original",
                "abrangencia",
                "votos",
                "parcelas_validos_pp",
                "conferencia_api_bruta",
            )
        }
        | {"diferenca_lula_menos_bolsonaro_pp": shares["lula"] - shares["bolsonaro"]},
        "por_casa": [
            {k: house[k] for k in HOUSE_FIELDS}
            | {
                "documentos": [
                    {
                        "arquivo": doc["arquivo"],
                        "url": doc["url"],
                        "sha256": doc["sha256"],
                    }
                    for doc in house["documentos"]
                ]
            }
            for house in d["por_casa"]
        ],
        "media_das_casas": d["media_das_casas"],
        "sensibilidades_da_media": [
            {
                k: s[k]
                for k in (
                    "nome",
                    "regra",
                    "casas",
                    "n_casas",
                    "erro_comum_diferenca_lula_menos_bolsonaro",
                    "mediana_dos_erros_diferenca_pp",
                )
            }
            for s in d["sensibilidades_da_media"]
        ],
        "ranking": d["ranking"],
        "comparacao_2026": {
            "fonte": "nacional.efeitos_casa deste build",
            "sinal": d["comparacao_2026"]["sinal"],
            "ressalva": d["comparacao_2026"]["ressalva"],
            "linhas": pairing(d, house_effects),
        },
        "aplicacao_2026": d["aplicacao_2026"]
        | {"sensibilidades": {"repeticao": SENS_REPEAT, "invertido": SENS_INVERTED}},
        "eleicao_2018": d["eleicao_2018"],
        "nao_arquivadas": d["nao_arquivadas"],
    }
