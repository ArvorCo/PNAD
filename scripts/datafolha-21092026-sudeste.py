#!/usr/bin/env python3
"""Camada de dados do Sudeste: governador, senador e presidente na mesma amostra.

Le o texto nativo dos relatorios do Datafolha de 8 a 10 de setembro de 2026 em
SP, RJ e MG, reaproveita o que `datafolha-21092026-governadores.py` ja extraiu,
acrescenta o Rio de Janeiro e o relatorio presidencial estadual, e escreve:

  docs/assets/datafolha_21092026_sudeste.json
  docs/assets/datafolha_21092026_sudeste.csv

O Espirito Santo entra em bloco separado, com outro instituto e outro metodo,
e nunca e somado com o Datafolha.

Reproducao:
    python3 scripts/datafolha-21092026-sudeste.py
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import re
from pathlib import Path
from types import ModuleType

import fitz

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
FONTES = ROOT / "docs/fontes"
GOV_DIR = ROOT / "data/pesquisas/datafolha/2026-09-10-governadores"
ES_DIR = ROOT / "data/originals/es_092026"
PRESIDENCIAL = FONTES / "datafolha_21092026_estaduais.pdf"
NACIONAL_CRUZAMENTOS = ASSETS / "datafolha_21092026_cruzamentos.json"
GOVERNADORES = ASSETS / "datafolha_21092026_governadores.json"
SP_CAMADA2 = ASSETS / "sp_092026_camada2.json"
TSE_SUMMARY = ROOT / "data/outputs/tse_eleitorado_perfil_summary.csv"
TSE_2022 = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"

Z95 = 1.959963984540054
LULA = "Lula (PT)"
FLAVIO = "Flavio Bolsonaro (PL)"

# Colunas do bloco 3 nos relatorios estaduais: nao ha recorte de regiao do pais.
BLOCO3_ESTADUAL = [
    "Total",
    "Regiao metropolitana",
    "Interior",
    "PT",
    "PL",
    "Outro partido",
    "Nao tem",
]

# Dimensoes do anexo. Fechada ou aberta nao e decidido aqui: o script soma as
# bases de cada dimensao e compara com o total, estado a estado. Renda nunca
# fecha, porque recusa e nao sabe existem no cartao e nao ganham coluna; cor e
# religiao tambem nao, porque amarela, indigena, sem religiao e demais credos
# ficam de fora; e o partido de preferencia fecha em SP e MG e nao fecha no RJ.
DIMENSOES = {
    "sexo": ["Masculino", "Feminino"],
    "idade": ["16-24", "25-34", "35-44", "45-59", "60+"],
    "escolaridade": ["Fundamental", "Medio", "Superior"],
    "renda": ["Ate 2 SM", "2 a 5 SM", "Mais de 5 SM"],
    "ocupacao": ["PEA", "Nao PEA"],
    "natureza": ["Regiao metropolitana", "Interior"],
    "partido": ["PT", "PL", "Outro partido", "Nao tem"],
    "cor": ["Branca", "Preta", "Parda"],
    "religiao": ["Catolica", "Evangelica"],
}
# Uma dimensao so conta como particao fechada quando a soma das bases cobre ao
# menos este percentual do total. A folga absorve o arredondamento das bases
# ponderadas, que o instituto publica em numero inteiro.
COBERTURA_MINIMA = 99.0

GOV_PAGINAS = {
    "SP": {
        "espontanea": [30],
        "estimulada": [31, 32],
        "validos": [33, 34],
        "rejeicao": [35, 36],
        "decisao": [37],
        "motivacao": [38],
        "turno2": [39],
        "senado_espontanea": [40, 41],
        "senado_voto1": [42, 43, 44],
        "senado_voto2": [45, 46, 47],
        "senado_alcance": [48, 49, 50],
        "avaliacao_governador": [51],
        "aprovacao_governador": [52],
    },
    "MG": {
        "espontanea": [31, 32],
        "estimulada": [33, 34],
        "validos": [35, 36],
        "rejeicao": [37, 38],
        "turno2_kalil": [39],
        "turno2": [40],
        "decisao": [41],
        "motivacao": [42],
        "senado_espontanea": [43, 44],
        "senado_voto1": [45, 46, 47],
        "senado_voto2": [48, 49, 50],
        "senado_alcance": [51, 52, 53],
        "avaliacao_governador": [54],
        "aprovacao_governador": [55],
    },
    "RJ": {
        "espontanea": [30, 31],
        "estimulada": [32, 33],
        "validos": [34, 35],
        "rejeicao": [36, 37],
        "turno2": [38],
        "decisao": [39],
        "motivacao": [40],
        "senado_espontanea": [41, 42],
        "senado_voto1": [43, 44, 45],
        "senado_voto2": [46, 47, 48],
        "senado_alcance": [49, 50, 51],
        "avaliacao_governador": [52],
        "aprovacao_governador": [53],
    },
}
# O anexo presidencial chama de Situacao A o cenario com Marcal e de Situacao B
# o cenario sem Marcal, que e o que reproduz o placar da manchete. O script
# confere essa leitura pela presenca da linha de Marcal, nao pelo rotulo.
PRES_PAGINAS = {
    "SP": {
        "turno1_com_marcal": [49, 50, 51],
        "turno1": [52, 53],
        "validos_com_marcal": [54, 55],
        "validos": [56, 57],
        "turno2": [58],
        "avaliacao_lula": [59],
        "aprovacao_lula": [60],
    },
    "RJ": {
        "turno1_com_marcal": [67, 68, 69],
        "turno1": [70, 71],
        "validos_com_marcal": [72, 73],
        "validos": [74, 75],
        "turno2": [76],
        "avaliacao_lula": [77],
        "aprovacao_lula": [78],
    },
    "MG": {
        "turno1_com_marcal": [85, 86, 87],
        "turno1": [88, 89],
        "validos_com_marcal": [90, 91],
        "validos": [92, 93],
        "turno2": [94],
        "avaliacao_lula": [95],
        "aprovacao_lula": [96],
    },
}
GOV_OFFSET = {"SP": 23, "MG": 24, "RJ": 23}
PRES_OFFSET = {"SP": 42, "RJ": 60, "MG": 78}
PROJETO = {"SP": "PO4285", "RJ": "PO4286", "MG": "PO4287"}

# Campo declarado de cada candidatura, por partido e por nome, como juizo
# editorial explicito. Centro e categoria propria: somar o centro a direita
# inflaria o bloco e o laudo nao sobreviveria a citacao hostil.
CAMPO_PARTIDO = {
    "PL": "direita",
    "REPUBLICANOS": "direita",
    "PP": "direita",
    "NOVO": "direita",
    "MISSÃO": "direita",
    "DEMOCRATA": "direita",
    "PRTB": "direita",
    "DC": "direita",
    "AGIR": "direita",
    "PSD": "centro",
    "MDB": "centro",
    "PSDB": "centro",
    "PODE": "centro",
    "CIDADANIA": "centro",
    "AVANTE": "centro",
    "PDT": "centro-esquerda",
    "PSB": "centro-esquerda",
    "REDE": "centro-esquerda",
    "PT": "esquerda",
    "PSOL": "esquerda",
    "PCB": "esquerda",
    "PSTU": "esquerda",
    "PCO": "esquerda",
    "UP": "esquerda",
}

# Cruzamentos entre cargos publicados pelo proprio instituto, no texto do
# relatorio presidencial estadual. Cada linha e medicao, nao estimativa.
# A pagina fica ao lado. O relatorio nao diz se a origem e o voto estimulado de
# 1o turno ou o de 2o turno para governador; a leitura adotada esta em
# `origem_pergunta` e a ressalva, em `ressalva`.
CRUZAMENTOS_PUBLICADOS = [
    {
        "uf": "SP",
        "pdf": "datafolha_21092026_estaduais.pdf",
        "pagina": 4,
        "destino_pergunta": "presidente, 1o turno",
        "origem_pergunta": "governador, estimulada",
        "linhas": {
            "Tarcísio (REPUBLICANOS)": {
                FLAVIO: 59,
                LULA: 12,
                "Escritor Augusto Cury (AVANTE)": 8,
            },
            "Fernando Haddad (PT)": {LULA: 78, FLAVIO: 5},
        },
    },
    {
        "uf": "RJ",
        "pdf": "datafolha_21092026_estaduais.pdf",
        "pagina": 12,
        "destino_pergunta": "presidente, 1o turno",
        "origem_pergunta": "governador, estimulada",
        "linhas": {
            "Douglas Ruas (PL)": {FLAVIO: 82, LULA: 3},
            "Eduardo Paes (PSD)": {LULA: 56, FLAVIO: 23},
            "Garotinho (REPUBLICANOS)": {FLAVIO: 38, LULA: 34},
        },
    },
    {
        "uf": "RJ",
        "pdf": "datafolha_21092026_estaduais.pdf",
        "pagina": 13,
        "destino_pergunta": "presidente, 2o turno",
        "origem_pergunta": "governador, estimulada",
        "linhas": {
            "Douglas Ruas (PL)": {FLAVIO: 91, LULA: 7},
            "Eduardo Paes (PSD)": {LULA: 64, FLAVIO: 28},
        },
    },
    {
        "uf": "MG",
        "pdf": "datafolha_21092026_estaduais.pdf",
        "pagina": 20,
        "destino_pergunta": "presidente, 1o turno",
        "origem_pergunta": "governador, estimulada",
        "linhas": {
            "Cleitinho Azevedo (REPUBLICANOS)": {FLAVIO: 60, LULA: 19},
            "Patrus Ananias (PT)": {LULA: 86, FLAVIO: 3},
            "Alexandre Kalil (PDT)": {LULA: 58, FLAVIO: 16},
        },
    },
    {
        "uf": "MG",
        "pdf": "datafolha_21092026_estaduais.pdf",
        "pagina": 21,
        "destino_pergunta": "presidente, 2o turno",
        "origem_pergunta": "governador, estimulada",
        "linhas": {
            "Patrus Ananias (PT)": {LULA: 94, FLAVIO: 3},
            "Alexandre Kalil (PDT)": {LULA: 66, FLAVIO: 24},
            "Cleitinho Azevedo (REPUBLICANOS)": {FLAVIO: 71, LULA: 25},
        },
    },
]
# Aprovacao do presidente cruzada com o voto para governador, mesmo relatorio.
APROVACAO_POR_GOVERNADOR = [
    {
        "uf": "RJ",
        "pagina": 13,
        "linhas": {
            "Eduardo Paes (PSD)": {"aprova": 61, "desaprova": 37},
            "Douglas Ruas (PL)": {"aprova": 7, "desaprova": 91},
        },
    },
    {
        "uf": "MG",
        "pagina": 21,
        "linhas": {
            "Patrus Ananias (PT)": {"aprova": 94},
            "Alexandre Kalil (PDT)": {"aprova": 61},
            "Cleitinho Azevedo (REPUBLICANOS)": {"desaprova": 71},
        },
    },
]

# Espirito Santo: Real Time Big Data, outro instituto, outro metodo, outro campo.
# Transcricao pagina a pagina do texto nativo; os numeros de segundo turno sao
# conferidos pela posicao na pagina em `conferir_es`.
ES_TRANSCRICAO = {
    "instituto": "Real Time Big Data",
    "registros": {
        "estadual": "ES-01967/2026",
        "presidencial": "BR-08236/2026",
    },
    "contratante": "Real Time Midia",
    "campo": "04–08/09/2026",
    "divulgacao": "2026-09-09",
    "n": 1600,
    "margem_declarada_pp": 2.0,
    "metodo": (
        "Não declarado no PDF nem na matéria. O registro da casa anota que a "
        "Real Time declara abordagem mista no TSE e descreve entrevistas "
        "telefônicas nos relatórios nacionais. Não transportar sem conferir."
    ),
    "governador_turno1": {
        "pagina": 7,
        "valores": {
            "Ricardo Ferraço (MDB)": 43,
            "Lorenzo Pazolini (REPUBLICANOS)": 33,
            "Helder Salomão (PT)": 13,
            "Breno Barcelos (MISSÃO)": 2,
            "Rafael Demuner (UP)": 0,
            "Nulo/Branco": 6,
            "NS/NR": 3,
        },
    },
    "governador_turno2": [
        {
            "pagina": 12,
            "valores": {
                "Ricardo Ferraço (MDB)": 49,
                "Lorenzo Pazolini (REPUBLICANOS)": 38,
                "Nulo/Branco": 8,
                "NS/NR": 5,
            },
        },
        {
            "pagina": 13,
            "valores": {
                "Ricardo Ferraço (MDB)": 58,
                "Helder Salomão (PT)": 26,
                "Nulo/Branco": 9,
                "NS/NR": 7,
            },
        },
        {
            "pagina": 14,
            "valores": {
                "Lorenzo Pazolini (REPUBLICANOS)": 51,
                "Helder Salomão (PT)": 30,
                "Nulo/Branco": 9,
                "NS/NR": 10,
            },
        },
    ],
    "senado_alcance": {
        "pagina": 20,
        "nota": "Primeiro e segundo votos consolidados e reduzidos a 100% pelo instituto.",
        "valores": {
            "Renato Casagrande (PSB)": 28,
            "Sergio Meneguelli (PSD)": 12,
            "Evair de Melo (REPUBLICANOS)": 9,
            "Fabiano Contarato (PT)": 9,
            "Maguinha Malta (PL)": 9,
            "Rose de Freitas (MDB)": 9,
            "Marcos do Val (AVANTE)": 5,
            "Leonardo Monjardim (NOVO)": 3,
            "Professor Fabian (PSOL)": 3,
            "Rodney Miranda (PRTB)": 3,
            "Callegari (DC)": 1,
            "Nulo/Branco": 4,
            "NS/NR": 5,
        },
    },
    "senado_voto1": {
        "pagina": 21,
        "valores": {
            "Renato Casagrande (PSB)": 32,
            "Sergio Meneguelli (PSD)": 11,
            "Evair de Melo (REPUBLICANOS)": 9,
            "Fabiano Contarato (PT)": 10,
            "Maguinha Malta (PL)": 9,
            "Rose de Freitas (MDB)": 9,
            "Marcos do Val (AVANTE)": 5,
            "Leonardo Monjardim (NOVO)": 3,
            "Professor Fabian (PSOL)": 2,
            "Rodney Miranda (PRTB)": 4,
            "Callegari (DC)": 3,
            "Nulo/Branco": 3,
        },
    },
    "presidente_turno1": {
        "pagina": 7,
        "valores": {
            FLAVIO: 35,
            LULA: 35,
            "Escritor Augusto Cury (AVANTE)": 6,
            "Renan Santos (MISSÃO)": 6,
            "Ronaldo Caiado (PSD)": 3,
            "Pablo Marçal (PRTB)": 2,
            "Zema (NOVO)": 2,
            "Outros": 1,
            "Nulo/Branco": 8,
            "NS/NR": 2,
        },
    },
    "presidente_turno2": {
        "pagina": 12,
        "valores": {FLAVIO: 47, LULA: 42, "Nulo/Branco": 8, "NS/NR": 3},
    },
    "presidente_renda": {
        "pagina": 10,
        "valores": {
            "Ate 2 SM": {FLAVIO: 30, LULA: 42},
            "2 a 5 SM": {FLAVIO: 38, LULA: 32},
            "Mais de 5 SM": {FLAVIO: 40, LULA: 26},
        },
    },
    "aprovacao_lula": {"pagina": 16, "aprova": 41, "desaprova": 55},
}

# Prior ideologica declarada, por campo da candidatura de origem. Os zeros sao
# estruturais e o IPF os preserva. Nao ha prior empirica fora de SP.
PRIOR_IDEOLOGICA = {
    "direita": {"flavio": 0.90, "lula": 0.02, "nao_escolha": 0.08},
    "centro": {"flavio": 0.34, "lula": 0.40, "nao_escolha": 0.26},
    "centro-esquerda": {"flavio": 0.14, "lula": 0.66, "nao_escolha": 0.20},
    "esquerda": {"flavio": 0.02, "lula": 0.92, "nao_escolha": 0.06},
    "nao_escolha": {"flavio": 0.22, "lula": 0.22, "nao_escolha": 0.56},
}
PRIOR_POLARIZADA = {
    "direita": {"flavio": 0.97, "lula": 0.01, "nao_escolha": 0.02},
    "centro": {"flavio": 0.45, "lula": 0.45, "nao_escolha": 0.10},
    "centro-esquerda": {"flavio": 0.08, "lula": 0.85, "nao_escolha": 0.07},
    "esquerda": {"flavio": 0.01, "lula": 0.97, "nao_escolha": 0.02},
    "nao_escolha": {"flavio": 0.30, "lula": 0.30, "nao_escolha": 0.40},
}
PRIOR_FROUXA = {
    "direita": {"flavio": 0.75, "lula": 0.10, "nao_escolha": 0.15},
    "centro": {"flavio": 0.30, "lula": 0.33, "nao_escolha": 0.37},
    "centro-esquerda": {"flavio": 0.20, "lula": 0.50, "nao_escolha": 0.30},
    "esquerda": {"flavio": 0.08, "lula": 0.77, "nao_escolha": 0.15},
    "nao_escolha": {"flavio": 0.18, "lula": 0.18, "nao_escolha": 0.64},
}
PRIORS = {
    "ideologica": PRIOR_IDEOLOGICA,
    "polarizada": PRIOR_POLARIZADA,
    "frouxa": PRIOR_FROUXA,
}

# Intersecoes minimas ja publicadas no dossie, dentro da preferencia partidaria
# pelo PT. Preferencia por partido nao e voto presidencial nem escala
# bolsonarista/petista; entra aqui so como limite de Frechet ja divulgado.
INTERSECOES_PT_PUBLICADAS = {
    "MG": {"par": "Lula/Cleitinho", "valores": [97, 34], "minimo_pp": 31},
    "SP": {"par": "Lula/Tarcísio", "valores": [95, 19], "minimo_pp": 14},
}

NAO_ESCOLHA = {
    "Em branco/nulo/nenhum",
    "Em branco/ nulo/ nenhum",
    "Indecisos",
    "Não sabe",
}


def modulo(nome: str) -> ModuleType:
    """Carrega um script irmao pelo caminho, porque o nome tem hifen."""
    caminho = ROOT / f"scripts/{nome}.py"
    spec = importlib.util.spec_from_file_location(nome, caminho)
    if spec is None or spec.loader is None:
        raise ImportError(f"nao foi possivel carregar {caminho}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


EXTRACT = modulo("datafolha-21092026-extract")
EXTRACT.COLUMNS[3] = BLOCO3_ESTADUAL


def achatar(tabela: dict) -> tuple[dict, dict]:
    linhas: dict[str, dict] = {}
    bases: dict[str, int] = {}
    for bloco in tabela["blocks"].values():
        bases.update(bloco["base"])
        for rotulo, colunas in bloco["rows"].items():
            linhas.setdefault(rotulo, {}).update(
                {c: (v or 0) for c, v in colunas.items()}
            )
    return linhas, bases


def ler_blocos(doc, paginas: list[int], offset: int) -> dict:
    blocos = {}
    for pagina in paginas:
        partes = re.split(r"Bloco ([123]) de 3,[^\n]*\n", doc[pagina - 1].get_text())
        for i in range(1, len(partes), 2):
            indice = int(partes[i])
            bloco = EXTRACT.block(partes[i + 1], indice, pagina)
            bloco["annex_page"] = pagina - offset
            chave = f"bloco{indice}"
            if chave in blocos:
                raise ValueError(f"Bloco repetido em {paginas}: {chave}")
            blocos[chave] = bloco
    if set(blocos) != {"bloco1", "bloco2", "bloco3"}:
        raise ValueError(f"Blocos incompletos em {paginas}: {sorted(blocos)}")
    rotulos = [list(b["rows"]) for b in blocos.values()]
    if any(x != rotulos[0] for x in rotulos):
        raise ValueError(f"Ordem de linhas divergente em {paginas}")
    return {"blocks": blocos, "pdf_pages": list(paginas)}


def extrair(pdf: Path, mapa: dict, offset: int) -> dict:
    with fitz.open(pdf) as doc:
        return {k: ler_blocos(doc, v, offset) for k, v in mapa.items()}


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for pedaco in iter(lambda: f.read(1 << 20), b""):
            h.update(pedaco)
    return h.hexdigest()


def topo(tabela: dict) -> dict:
    linhas, _ = achatar(tabela)
    return {k: v["Total"] for k, v in linhas.items()}


def campo_de(rotulo: str) -> str:
    achado = re.search(r"\(([^)]+)\)\s*$", rotulo)
    if not achado:
        return "nao_escolha" if rotulo in NAO_ESCOLHA else "desconhecido"
    return CAMPO_PARTIDO.get(achado.group(1).upper(), "desconhecido")


# --------------------------------------------------------------------------- #
# Prova de leitura                                                            #
# --------------------------------------------------------------------------- #


def cobertura(tabela: dict) -> dict:
    """Soma as bases de cada dimensao e compara com o total."""
    _, bases = achatar(tabela)
    saida = {}
    for nome, grupos in DIMENSOES.items():
        if not all(g in bases for g in grupos):
            continue
        soma = sum(bases[g] for g in grupos)
        pct = 100 * soma / bases["Total"]
        saida[nome] = {
            "base_somada": soma,
            "base_total": bases["Total"],
            "cobertura_pct": round(pct, 2),
            "particao_fechada": pct >= COBERTURA_MINIMA,
        }
    return saida


def fechadas(tabela: dict) -> set:
    return {k for k, v in cobertura(tabela).items() if v["particao_fechada"]}


def provar(tabelas: dict, rotulo_fonte: str, dimensoes: set) -> tuple[list, float]:
    """Recompoe cada linha publicada a partir de cada particao fechada."""
    provas = []
    pior = 0.0
    for nome, tabela in tabelas.items():
        linhas, bases = achatar(tabela)
        for dimensao in sorted(dimensoes):
            grupos = DIMENSOES[dimensao]
            if not all(g in bases for g in grupos):
                continue
            soma_bases = sum(bases[g] for g in grupos)
            for candidato, linha in linhas.items():
                valor = sum(bases[g] * linha[g] for g in grupos) / soma_bases
                residuo = valor - linha["Total"]
                pior = max(pior, abs(residuo))
                provas.append(
                    {
                        "fonte": rotulo_fonte,
                        "tabela": nome,
                        "dimensao": dimensao,
                        "candidato": candidato,
                        "recomposto": round(valor, 3),
                        "publicado": linha["Total"],
                        "residuo_pp": round(residuo, 3),
                        "cobertura_pct": round(100 * soma_bases / bases["Total"], 2),
                        "n": bases["Total"],
                    }
                )
    return provas, pior


# --------------------------------------------------------------------------- #
# Incerteza                                                                   #
# --------------------------------------------------------------------------- #


def margem(p: float, n: float) -> float:
    return 100 * Z95 * math.sqrt(max(p, 0) / 100 * (1 - max(p, 0) / 100) / n)


def margem_diferenca(a: float, b: float, n: float) -> float:
    pa, pb = a / 100, b / 100
    var = (pa + pb - (pa - pb) ** 2) / n
    return 100 * Z95 * math.sqrt(max(var, 0))


# --------------------------------------------------------------------------- #
# O vao                                                                       #
# --------------------------------------------------------------------------- #


def melhor_do_campo(valores: dict, campo: str) -> tuple[str | None, float]:
    candidatos = {k: v for k, v in valores.items() if campo_de(k) == campo}
    if not candidatos:
        return None, 0.0
    nome = max(candidatos, key=lambda k: candidatos[k])
    return nome, candidatos[nome]


def vao_por_recorte(gov: dict, pres: dict, nome_gov: str, abertas: set) -> list:
    linhas_gov, bases_gov = achatar(gov)
    linhas_pres, bases_pres = achatar(pres)
    if nome_gov not in linhas_gov:
        raise ValueError(nome_gov)
    saida = []
    for dimensao, grupos in DIMENSOES.items():
        for grupo in grupos:
            if grupo not in bases_gov or grupo not in bases_pres:
                continue
            a = linhas_gov[nome_gov][grupo]
            b = linhas_pres[FLAVIO][grupo]
            c = linhas_pres[LULA][grupo]
            saida.append(
                {
                    "dimensao": dimensao,
                    "recorte": grupo,
                    "particao_fechada": dimensao not in abertas,
                    "governador": a,
                    "flavio": b,
                    "lula": c,
                    "vao_pp": a - b,
                    "base_governador": bases_gov[grupo],
                    "base_presidente": bases_pres[grupo],
                    "margem_vao_pp": round(
                        margem_diferenca(
                            a, b, min(bases_gov[grupo], bases_pres[grupo])
                        ),
                        2,
                    ),
                }
            )
    saida.sort(key=lambda r: -r["vao_pp"])
    return saida


# --------------------------------------------------------------------------- #
# Senado                                                                      #
# --------------------------------------------------------------------------- #


def senado(tabelas: dict, pres_turno2: dict, pres_turno1: dict, abertas: set) -> dict:
    voto1 = topo(tabelas["senado_voto1"])
    voto2 = topo(tabelas["senado_voto2"])
    alcance = topo(tabelas["senado_alcance"])
    nomes = [k for k in alcance if k not in NAO_ESCOLHA]
    combinado = {
        k: round((voto1.get(k, 0) + voto2.get(k, 0)) / 2, 2)
        for k in set(voto1) | set(voto2)
    }
    ordenado = sorted(nomes, key=lambda k: -alcance[k])
    por_campo: dict[str, float] = {}
    for nome in nomes:
        por_campo.setdefault(campo_de(nome), 0.0)
        por_campo[campo_de(nome)] += combinado.get(nome, 0.0)
    nao_escolha = round(
        sum(combinado.get(k, 0.0) for k in combinado if k in NAO_ESCOLHA), 2
    )
    lider = ordenado[0]
    segundo = ordenado[1] if len(ordenado) > 1 else None
    terceiro = ordenado[2] if len(ordenado) > 2 else None
    direita = [n for n in ordenado if campo_de(n) == "direita"]
    melhor_direita = direita[0] if direita else None
    linhas_alc, bases_alc = achatar(tabelas["senado_alcance"])
    linhas_v1, bases_v1 = achatar(tabelas["senado_voto1"])
    linhas_pres, bases_pres = achatar(pres_turno2)
    linhas_pres1, _ = achatar(pres_turno1)
    recortes = []
    if melhor_direita:
        for dimensao, grupos in DIMENSOES.items():
            for grupo in grupos:
                if grupo not in bases_alc or grupo not in bases_pres:
                    continue
                recortes.append(
                    {
                        "dimensao": dimensao,
                        "recorte": grupo,
                        "particao_fechada": dimensao not in abertas,
                        "senador_direita_voto1": linhas_v1[melhor_direita][grupo],
                        "senador_direita_alcance": linhas_alc[melhor_direita][grupo],
                        "flavio_turno1": linhas_pres1[FLAVIO][grupo],
                        "flavio_turno2": linhas_pres[FLAVIO][grupo],
                        "vao_turno1_pp": linhas_v1[melhor_direita][grupo]
                        - linhas_pres1[FLAVIO][grupo],
                        "vao_turno2_pp": linhas_v1[melhor_direita][grupo]
                        - linhas_pres[FLAVIO][grupo],
                        "base": bases_v1[grupo],
                    }
                )
        recortes.sort(key=lambda r: -r["vao_turno1_pp"])
    return {
        "paginas": {
            "voto1": tabelas["senado_voto1"]["pdf_pages"],
            "voto2": tabelas["senado_voto2"]["pdf_pages"],
            "alcance": tabelas["senado_alcance"]["pdf_pages"],
        },
        "voto1": voto1,
        "voto2": voto2,
        "alcance": alcance,
        "combinado_sobre_dois_votos": combinado,
        "soma_alcance_pct": round(sum(alcance[k] for k in nomes), 2),
        "soma_combinado_pct": round(sum(combinado.values()), 2),
        "lider_alcance": {"nome": lider, "valor": alcance[lider]},
        "segunda_vaga": (
            {
                "nome": segundo,
                "valor": alcance[segundo],
                "distancia_para_terceiro_pp": (
                    alcance[segundo] - alcance[terceiro] if terceiro else None
                ),
                "terceiro": terceiro,
            }
            if segundo
            else None
        ),
        "por_campo_sobre_dois_votos": {k: round(v, 2) for k, v in por_campo.items()},
        "nao_escolha_sobre_dois_votos": nao_escolha,
        "melhor_da_direita": melhor_direita,
        "vao_senador_direita_por_recorte": recortes,
        "nota": (
            "Alcance é resposta múltipla: é a parcela que cita o nome em pelo "
            "menos um dos dois votos e não soma 100 entre candidaturas. "
            "O combinado divide a soma dos dois votos por dois, e aí sim soma "
            "100 com branco, nulo e indeciso. A comparação com o voto "
            "presidencial usa o primeiro voto, que é resposta única."
        ),
        "nota_do_vao_do_senado": (
            "A régua honesta é o primeiro voto de senador contra o 1º turno "
            "presidencial: as duas perguntas repartem o voto entre muitos "
            "nomes. Contra o 2º turno presidencial, que é binário, qualquer "
            "senador fica muito abaixo por construção, e o número mede o "
            "formato da pergunta, não força eleitoral."
        ),
    }


# --------------------------------------------------------------------------- #
# Fréchet e IPF                                                               #
# --------------------------------------------------------------------------- #


def frechet(linha: float, coluna: float) -> tuple[float, float]:
    return max(0.0, linha + coluna - 1.0), min(linha, coluna)


def ipf(
    prior: list[list[float]],
    linhas: list[float],
    colunas: list[float],
    iteracoes: int = 2000,
    tolerancia: float = 1e-12,
) -> list[list[float]]:
    m = [row[:] for row in prior]
    for _ in range(iteracoes):
        pior = 0.0
        for i, alvo in enumerate(linhas):
            soma = sum(m[i])
            if soma <= 0:
                if alvo > 0:
                    raise ValueError("Linha com prior nula e margem positiva")
                continue
            fator = alvo / soma
            pior = max(pior, abs(fator - 1))
            m[i] = [v * fator for v in m[i]]
        for j, alvo in enumerate(colunas):
            soma = sum(m[i][j] for i in range(len(m)))
            if soma <= 0:
                if alvo > 0:
                    raise ValueError("Coluna com prior nula e margem positiva")
                continue
            fator = alvo / soma
            pior = max(pior, abs(fator - 1))
            for i in range(len(m)):
                m[i][j] *= fator
        if pior < tolerancia:
            break
    return m


def _normalizar(valores: dict) -> dict:
    total = sum(valores.values())
    return {k: v / total for k, v in valores.items()}


def matriz_transferencia(
    origem: dict,
    destino: dict,
    medidas: dict,
    prior_nome: str,
    prior_empirica: dict | None = None,
) -> dict:
    """IPF contra prior, com as linhas publicadas fixas como medicao."""
    linhas = list(origem)
    colunas = list(destino)
    r = _normalizar(origem)
    c = _normalizar(destino)
    tabela_prior = PRIORS[prior_nome]

    fixo = [[0.0] * len(colunas) for _ in linhas]
    livre = [[1.0] * len(colunas) for _ in linhas]
    marca = [["estimada"] * len(colunas) for _ in linhas]
    for i, nome in enumerate(linhas):
        publicado = medidas.get(nome, {})
        for j, destino_nome in enumerate(colunas):
            if destino_nome in publicado:
                fixo[i][j] = r[nome] * publicado[destino_nome] / 100
                livre[i][j] = 0.0
                marca[i][j] = "medida"

    residuo_linha = [r[nome] - sum(fixo[i]) for i, nome in enumerate(linhas)]
    residuo_coluna = [
        c[nome] - sum(fixo[i][j] for i in range(len(linhas)))
        for j, nome in enumerate(colunas)
    ]
    if min(residuo_linha) < -1e-9 or min(residuo_coluna) < -1e-9:
        raise ValueError("Linhas publicadas incompativeis com as margens")

    prior = [[0.0] * len(colunas) for _ in linhas]
    for i, nome in enumerate(linhas):
        campo = campo_de(nome)
        if prior_empirica and nome in prior_empirica:
            peso = prior_empirica[nome]
        else:
            base = tabela_prior.get(campo, tabela_prior["nao_escolha"])
            peso = base
        for j, destino_nome in enumerate(colunas):
            if livre[i][j] == 0.0:
                continue
            if destino_nome == FLAVIO:
                valor = peso.get("flavio", 0.0)
            elif destino_nome == LULA:
                valor = peso.get("lula", 0.0)
            else:
                valor = peso.get("nao_escolha", 0.0) / max(
                    1, sum(1 for x in colunas if x not in (FLAVIO, LULA))
                )
            prior[i][j] = max(valor, 1e-9)

    ajustado = ipf(prior, residuo_linha, residuo_coluna)
    final = [
        [fixo[i][j] + ajustado[i][j] for j in range(len(colunas))]
        for i in range(len(linhas))
    ]

    celulas = []
    for i, nome in enumerate(linhas):
        for j, destino_nome in enumerate(colunas):
            lo, hi = frechet(r[nome], c[destino_nome])
            estado = marca[i][j]
            if estado != "medida" and hi - lo < 0.01:
                estado = "limitada"
            celulas.append(
                {
                    "origem": nome,
                    "destino": destino_nome,
                    "valor_pp": round(100 * final[i][j], 3),
                    "frechet_min_pp": round(100 * lo, 3),
                    "frechet_max_pp": round(100 * hi, 3),
                    "estado": estado,
                }
            )
    return {
        "prior": prior_nome,
        "prior_empirica": bool(prior_empirica),
        "origem_pct": {k: round(100 * v, 2) for k, v in r.items()},
        "destino_pct": {k: round(100 * v, 2) for k, v in c.items()},
        "matriz_pp": {
            nome: {colunas[j]: round(100 * final[i][j], 3) for j in range(len(colunas))}
            for i, nome in enumerate(linhas)
        },
        "condicional_pct": {
            nome: {
                colunas[j]: round(100 * final[i][j] / r[nome], 2)
                for j in range(len(colunas))
            }
            for i, nome in enumerate(linhas)
            if r[nome] > 0
        },
        "celulas": celulas,
        "linhas_medidas": sorted(set(medidas) & set(linhas)),
        "residuo_margem_linha_pp": round(
            100 * max(abs(sum(final[i]) - r[nome]) for i, nome in enumerate(linhas)), 6
        ),
        "residuo_margem_coluna_pp": round(
            100
            * max(
                abs(sum(final[i][j] for i in range(len(linhas))) - c[nome])
                for j, nome in enumerate(colunas)
            ),
            6,
        ),
    }


def vazamento(matriz: dict, origem: str, destino: str) -> float | None:
    cond = matriz["condicional_pct"].get(origem)
    if not cond:
        return None
    return round(100 - cond.get(destino, 0.0), 2)


# --------------------------------------------------------------------------- #
# Regional contra estadual                                                    #
# --------------------------------------------------------------------------- #


def eleitorado_tse() -> dict:
    with TSE_SUMMARY.open(encoding="utf-8") as f:
        dados = {
            r["category"]: int(r["qt_eleitores"])
            for r in csv.DictReader(f)
            if r["dimension"] in ("uf", "regiao")
        }
    return dados


def votos_2022_validos() -> dict:
    """Votos nominais para presidente no 1o turno de 2022, por UF."""
    import io
    import zipfile

    alvo = {"SP", "RJ", "MG", "ES"}
    total = dict.fromkeys(alvo, 0)
    with zipfile.ZipFile(TSE_2022) as z:
        nome = next(n for n in z.namelist() if n.endswith("_BR.csv"))
        with z.open(nome) as bruto:
            leitor = csv.reader(
                io.TextIOWrapper(bruto, encoding="latin-1"), delimiter=";"
            )
            cabecalho = next(leitor)
            idx = {c: i for i, c in enumerate(cabecalho)}
            for linha in leitor:
                if linha[idx["NR_TURNO"]] != "1":
                    continue
                if linha[idx["DS_CARGO"]].strip().lower() != "presidente":
                    continue
                uf = linha[idx["SG_UF"]]
                if uf in alvo:
                    total[uf] += int(linha[idx["QT_VOTOS_NOMINAIS"]])
    return total


def regional_contra_estadual(estados: dict, eleitores: dict) -> dict:
    nacional = json.loads(NACIONAL_CRUZAMENTOS.read_text(encoding="utf-8"))
    linhas, bases = achatar(nacional["tabelas"]["turno2_flavio"])
    recorte = {
        "lula": linhas[LULA]["Sudeste"],
        "flavio": linhas[FLAVIO]["Sudeste"],
        "base": bases["Sudeste"],
    }
    ufs = ["SP", "RJ", "MG"]
    pesos_regiao = {u: eleitores[u] / eleitores["Sudeste"] for u in [*ufs, "ES"]}
    soma = sum(eleitores[u] for u in ufs)
    pesos_cond = {u: eleitores[u] / soma for u in ufs}
    media = {
        k: sum(pesos_cond[u] * estados[u]["presidente"]["turno2"][v] for u in ufs)
        for k, v in [("lula", LULA), ("flavio", FLAVIO)]
    }
    var_media = {
        k: sum(
            pesos_cond[u] ** 2
            * (estados[u]["presidente"]["turno2"][v] / 100)
            * (1 - estados[u]["presidente"]["turno2"][v] / 100)
            / estados[u]["n"]
            for u in ufs
        )
        for k, v in [("lula", LULA), ("flavio", FLAVIO)]
    }
    dif_media = media["lula"] - media["flavio"]
    var_dif_media = sum(
        pesos_cond[u] ** 2
        * (
            (
                estados[u]["presidente"]["turno2"][LULA]
                + estados[u]["presidente"]["turno2"][FLAVIO]
            )
            / 100
            - (
                (
                    estados[u]["presidente"]["turno2"][LULA]
                    - estados[u]["presidente"]["turno2"][FLAVIO]
                )
                / 100
            )
            ** 2
        )
        / estados[u]["n"]
        for u in ufs
    )
    dif_recorte = recorte["lula"] - recorte["flavio"]
    var_dif_recorte = (
        (recorte["lula"] + recorte["flavio"]) / 100
        - ((recorte["lula"] - recorte["flavio"]) / 100) ** 2
    ) / recorte["base"]
    contraste = dif_recorte - dif_media
    margem_contraste = 100 * Z95 * math.sqrt(var_dif_recorte + var_dif_media)
    implicado = {
        k: (
            recorte[k]
            - sum(pesos_regiao[u] * estados[u]["presidente"]["turno2"][v] for u in ufs)
        )
        / pesos_regiao["ES"]
        for k, v in [("lula", LULA), ("flavio", FLAVIO)]
    }
    return {
        "recorte_nacional": {
            **recorte,
            "campo": "15–17/09/2026",
            "registro": "BR-04029/2026",
            "fonte": {"pdf": "datafolha_21092026.pdf", "pagina": 42},
            "margem_lula_pp": round(margem(recorte["lula"], recorte["base"]), 2),
            "margem_flavio_pp": round(margem(recorte["flavio"], recorte["base"]), 2),
            "diferenca_pp": dif_recorte,
            "margem_diferenca_pp": round(100 * Z95 * math.sqrt(var_dif_recorte), 2),
        },
        "media_estadual": {
            "campo": "08–10/09/2026",
            "ufs": ufs,
            "pesos_condicionais": {k: round(v, 6) for k, v in pesos_cond.items()},
            "lula": round(media["lula"], 3),
            "flavio": round(media["flavio"], 3),
            "margem_lula_pp": round(100 * Z95 * math.sqrt(var_media["lula"]), 2),
            "margem_flavio_pp": round(100 * Z95 * math.sqrt(var_media["flavio"]), 2),
            "diferenca_pp": round(dif_media, 3),
            "margem_diferenca_pp": round(100 * Z95 * math.sqrt(var_dif_media), 2),
        },
        "cobertura_do_eleitorado_pct": round(100 * soma / eleitores["Sudeste"], 4),
        "peso_es_no_sudeste_pct": round(100 * pesos_regiao["ES"], 4),
        "contraste": {
            "diferenca_das_diferencas_pp": round(contraste, 3),
            "margem_pp": round(margem_contraste, 2),
            "ic95": [
                round(contraste - margem_contraste, 3),
                round(contraste + margem_contraste, 3),
            ],
            "separa_com_95": abs(contraste) > margem_contraste,
        },
        "es_implicado": {
            "lula": round(implicado["lula"], 2),
            "flavio": round(implicado["flavio"], 2),
            "uso": "nao_publicavel_como_estimativa_do_es",
            "motivos": [
                "Campos diferentes: o recorte regional é de 15 a 17/09 e as "
                "amostras estaduais são de 8 a 10/09.",
                "O recorte regional é ponderado pelo desenho nacional, não pela "
                "soma de quatro amostras estaduais.",
                "Os quatro valores publicados são arredondados a inteiro, e a "
                "dedução divide o erro pelo peso do ES, que é 4,51%.",
            ],
        },
        "faixa_logicamente_possivel": {
            k: [
                round(
                    sum(
                        pesos_regiao[u] * estados[u]["presidente"]["turno2"][v]
                        for u in ufs
                    ),
                    2,
                ),
                round(
                    sum(
                        pesos_regiao[u] * estados[u]["presidente"]["turno2"][v]
                        for u in ufs
                    )
                    + 100 * pesos_regiao["ES"],
                    2,
                ),
            ]
            for k, v in [("lula", LULA), ("flavio", FLAVIO)]
        },
        "nota": (
            "Comparar primeiro com o Sudeste do mesmo campo. A diferença entre "
            "o recorte regional e a média estadual não é prova de erro nem de "
            "voto capixaba: são desenhos, datas e ponderações diferentes."
        ),
    }


# --------------------------------------------------------------------------- #
# Ordem de grandeza                                                           #
# --------------------------------------------------------------------------- #


def ordem_de_grandeza(estados: dict, eleitores: dict, validos: dict) -> list:
    saida = []
    for uf, dado in estados.items():
        vao = dado["vao"]["turno2"]["vao_pp"]
        saida.append(
            {
                "uf": uf,
                "vao_turno2_pp": vao,
                "eleitorado_tse_2026": eleitores[uf],
                "votos_nominais_presidente_1t_2022": validos[uf],
                "equivalente_sobre_eleitorado": round(eleitores[uf] * vao / 100),
                "equivalente_sobre_validos_2022": round(validos[uf] * vao / 100),
                "rotulo": "estimativa de ordem de grandeza, não projeção de votos",
            }
        )
    return saida


# --------------------------------------------------------------------------- #
# Espírito Santo                                                              #
# --------------------------------------------------------------------------- #


def conferir_es() -> dict:
    """Confere o pareamento rotulo-numero do 2o turno presidencial pela posicao."""
    caminho = ES_DIR / "realtime_es_presidente_0909.pdf"
    with fitz.open(caminho) as doc:
        palavras = doc[ES_TRANSCRICAO["presidente_turno2"]["pagina"] - 1].get_text(
            "words"
        )
    rotulos = {}
    numeros = {}
    for x0, _, x1, _, texto, *_ in palavras:
        meio = (x0 + x1) / 2
        if texto == "LULA":
            rotulos[LULA] = meio
        elif texto == "FLÁVIO":
            rotulos[FLAVIO] = meio
        elif re.fullmatch(r"4[0-9]%", texto):
            numeros[texto] = meio
    pareado = {}
    for valor, x in numeros.items():
        alvo = min(rotulos, key=lambda k: abs(rotulos[k] - x))
        pareado[alvo] = int(valor.rstrip("%"))
    esperado = {
        k: v
        for k, v in ES_TRANSCRICAO["presidente_turno2"]["valores"].items()
        if k in (LULA, FLAVIO)
    }
    return {
        "pareamento_por_posicao": pareado,
        "transcricao": esperado,
        "confere": pareado == esperado,
        "nota": (
            "A página imprime os números antes dos nomes na ordem de leitura. "
            "O pareamento por coordenada devolve o mesmo que a matéria do "
            "Poder360 que divulgou a pesquisa."
        ),
    }


def bloco_es() -> dict:
    gov1 = ES_TRANSCRICAO["governador_turno1"]["valores"]
    pres1 = ES_TRANSCRICAO["presidente_turno1"]["valores"]
    pres2 = ES_TRANSCRICAO["presidente_turno2"]["valores"]
    melhor_1t = melhor_do_campo(gov1, "direita")
    turno2_direita = max(
        (
            (c["valores"][n], n, c["pagina"])
            for c in ES_TRANSCRICAO["governador_turno2"]
            for n in c["valores"]
            if campo_de(n) == "direita"
        ),
        default=(0.0, None, None),
    )
    senado = ES_TRANSCRICAO["senado_alcance"]["valores"]
    por_campo: dict[str, float] = {}
    for nome, valor in senado.items():
        if nome in ("Nulo/Branco", "NS/NR"):
            continue
        por_campo.setdefault(campo_de(nome), 0.0)
        por_campo[campo_de(nome)] += valor
    # A procedencia guarda a URL publica de onde cada PDF foi baixado. Ela vai
    # para o JSON para que a pagina possa citar a origem sem republicar o
    # arquivo do instituto.
    proveniencia = json.loads(
        (ES_DIR / "proveniencia.json").read_text(encoding="utf-8")
    )
    origem = {p["arquivo"]: p for p in proveniencia["pesquisas"]}
    fontes = {}
    for arquivo in ("realtime_es_0909.pdf", "realtime_es_presidente_0909.pdf"):
        caminho = ES_DIR / arquivo
        with fitz.open(caminho) as doc:
            paginas = doc.page_count
        ficha_origem = origem[arquivo]
        fontes[arquivo] = {
            "caminho": str(caminho.relative_to(ROOT)),
            "bytes": caminho.stat().st_size,
            "sha256": sha256(caminho),
            "paginas": paginas,
            "url": ficha_origem["url"],
            "materia": ficha_origem["article"],
            "registro_tse": ficha_origem["registro_tse"],
            "republicado": False,
        }
    return {
        "aviso": (
            "Outro instituto, outro método, outro campo. Não entra em média "
            "com o Datafolha e não fecha a conta do Sudeste."
        ),
        "ficha": {k: v for k, v in ES_TRANSCRICAO.items() if not isinstance(v, dict)},
        "registros": ES_TRANSCRICAO["registros"],
        "campo": ES_TRANSCRICAO["campo"],
        "n": ES_TRANSCRICAO["n"],
        "metodo": ES_TRANSCRICAO["metodo"],
        "fontes": fontes,
        "conferencia_turno2": conferir_es(),
        "governador_turno1": ES_TRANSCRICAO["governador_turno1"],
        "governador_turno2": ES_TRANSCRICAO["governador_turno2"],
        "senado": {
            "alcance": ES_TRANSCRICAO["senado_alcance"],
            "voto1": ES_TRANSCRICAO["senado_voto1"],
            "por_campo_alcance": {k: round(v, 2) for k, v in por_campo.items()},
        },
        "presidente_turno1": ES_TRANSCRICAO["presidente_turno1"],
        "presidente_turno2": ES_TRANSCRICAO["presidente_turno2"],
        "presidente_renda": ES_TRANSCRICAO["presidente_renda"],
        "aprovacao_lula": ES_TRANSCRICAO["aprovacao_lula"],
        "vao": {
            "turno1_melhor_direita": {
                "nome": melhor_1t[0],
                "governador": melhor_1t[1],
                "flavio": pres1[FLAVIO],
                "vao_pp": melhor_1t[1] - pres1[FLAVIO],
            },
            "turno1_direita_estrita": {
                "nome": "Lorenzo Pazolini (REPUBLICANOS)",
                "governador": gov1["Lorenzo Pazolini (REPUBLICANOS)"],
                "flavio": pres1[FLAVIO],
                "vao_pp": gov1["Lorenzo Pazolini (REPUBLICANOS)"] - pres1[FLAVIO],
            },
            "turno2": {
                "nome": turno2_direita[1],
                "pagina": turno2_direita[2],
                "governador": turno2_direita[0],
                "flavio": pres2[FLAVIO],
                "vao_pp": turno2_direita[0] - pres2[FLAVIO],
            },
            "rotulo": "teto endereçável, não previsão",
        },
    }


# --------------------------------------------------------------------------- #
# Montagem                                                                    #
# --------------------------------------------------------------------------- #


def montar_estado(uf: str, gov: dict, pres: dict, n: int, abertas: set) -> dict:
    gov_turno2 = topo(gov["turno2"])
    pres_turno2 = topo(pres["turno2"])
    gov_turno1 = topo(gov["estimulada"])
    pres_turno1 = topo(pres["turno1"])
    lider_gov = next(iter(gov_turno2))
    direita_2t = melhor_do_campo(gov_turno2, "direita")
    direita_1t = melhor_do_campo(gov_turno1, "direita")
    esquerda_2t = melhor_do_campo(gov_turno2, "esquerda")
    esquerda_1t = melhor_do_campo(gov_turno1, "esquerda")

    def bloco_vao(nome, valor, comparado, rotulo):
        if nome is None:
            return None
        return {
            "candidato_governador": nome,
            "governador_pct": valor,
            "presidenciavel_pct": comparado,
            "vao_pp": round(valor - comparado, 2),
            "margem_pp": round(margem_diferenca(valor, comparado, n), 2),
            "rotulo": rotulo,
        }

    vao_turno2 = bloco_vao(
        direita_2t[0],
        direita_2t[1],
        pres_turno2[FLAVIO],
        "teto endereçável, não previsão",
    )
    if vao_turno2 is None:
        vao_turno2 = bloco_vao(
            lider_gov,
            gov_turno2[lider_gov],
            pres_turno2[FLAVIO],
            "sem candidatura de direita no 2º turno estadual",
        )
    if vao_turno2 is None:
        raise ValueError(f"{uf}: sem candidatura de governador no 2o turno")
    vao_inverso_turno2 = bloco_vao(
        esquerda_2t[0],
        pres_turno2[LULA],
        esquerda_2t[1],
        "vão inverso: Lula menos a candidatura da esquerda ao governo",
    )
    if vao_inverso_turno2 is None:
        # No Rio o 2o turno estadual e PSD contra PL: nao ha candidatura da
        # esquerda para comparar. O vao inverso sai pelo centro, declarado.
        centro_2t = melhor_do_campo(gov_turno2, "centro")
        vao_inverso_turno2 = bloco_vao(
            centro_2t[0],
            pres_turno2[LULA],
            centro_2t[1],
            "sem candidatura da esquerda no 2º turno estadual; a comparação "
            "usa a candidatura de centro e não mede transferência de campo",
        )
    if vao_inverso_turno2 is None:
        raise ValueError(f"{uf}: sem comparacao de vao inverso no 2o turno")
    vao = {
        "turno2": vao_turno2,
        "turno1": bloco_vao(
            direita_1t[0],
            direita_1t[1],
            pres_turno1[FLAVIO],
            "teto endereçável, não previsão",
        ),
        "inverso_turno2": vao_inverso_turno2,
        "inverso_turno1": bloco_vao(
            esquerda_1t[0],
            pres_turno1[LULA],
            esquerda_1t[1],
            "vão inverso: Lula menos a candidatura da esquerda ao governo",
        ),
        "lider_do_governo_menos_flavio_pp": round(
            gov_turno2[lider_gov] - pres_turno2[FLAVIO], 2
        ),
    }
    recortes = vao_por_recorte(
        gov["turno2"], pres["turno2"], vao_turno2["candidato_governador"], abertas
    )
    inversoes = [r for r in recortes if r["vao_pp"] < 0]
    medidas_1t = {}
    medidas_2t = {}
    for item in CRUZAMENTOS_PUBLICADOS:
        if item["uf"] != uf:
            continue
        alvo = medidas_1t if "1o turno" in item["destino_pergunta"] else medidas_2t
        for origem, valores in item["linhas"].items():
            alvo.setdefault(origem, {}).update(valores)
    return {
        "uf": uf,
        "n": n,
        "projeto": PROJETO[uf],
        "campo": "08–10/09/2026",
        "governador": {
            "turno1": gov_turno1,
            "turno1_validos": topo(gov["validos"]),
            "turno1_espontanea": topo(gov["espontanea"]),
            "turno2": gov_turno2,
            "rejeicao": topo(gov["rejeicao"]),
            "decisao": topo(gov["decisao"]),
            "motivacao": topo(gov["motivacao"]),
            "avaliacao": topo(gov["avaliacao_governador"]),
            "aprovacao": topo(gov["aprovacao_governador"]),
            "cenarios_alternativos_turno2": (
                {"turno2_kalil": topo(gov["turno2_kalil"])}
                if "turno2_kalil" in gov
                else {}
            ),
            "paginas": {k: v["pdf_pages"] for k, v in gov.items()},
        },
        "senado": senado(gov, pres["turno2"], pres["turno1"], abertas),
        "presidente": {
            "turno1": pres_turno1,
            "turno1_com_marcal": topo(pres["turno1_com_marcal"]),
            "turno1_validos": topo(pres["validos"]),
            "turno2": pres_turno2,
            "avaliacao_lula": topo(pres["avaliacao_lula"]),
            "aprovacao_lula": topo(pres["aprovacao_lula"]),
            "paginas": {k: v["pdf_pages"] for k, v in pres.items()},
        },
        "vao": vao,
        "vao_por_recorte_turno2": recortes,
        "recortes_com_sinal_invertido": inversoes,
        "cobertura_dos_recortes": cobertura(gov["turno2"]),
        "cruzamentos_publicados": {
            "turno1": medidas_1t,
            "turno2": medidas_2t,
        },
    }


def transferencias(uf: str, estado: dict, gov: dict, pres: dict) -> dict:
    gov1 = {
        k: v for k, v in topo(gov["estimulada"]).items() if v > 0 or k in NAO_ESCOLHA
    }
    pres1 = {
        k: v
        for k, v in topo(pres["turno1"]).items()
        if k in (LULA, FLAVIO) or v >= 1 or k in NAO_ESCOLHA
    }
    pres2 = topo(pres["turno2"])
    gov2 = topo(gov["turno2"])
    empirica = None
    if uf == "SP" and SP_CAMADA2.exists():
        fluxo = json.loads(SP_CAMADA2.read_text(encoding="utf-8"))["fluxos"][0]
        traducao = {
            "Tarcísio": "Tarcísio (REPUBLICANOS)",
            "Haddad": "Fernando Haddad (PT)",
        }
        empirica = {
            traducao[k]: {
                "flavio": v["Flávio"],
                "lula": v["Lula"],
                "nao_escolha": v["Não escolha"],
            }
            for k, v in fluxo["prior"].items()
            if k in traducao
        }
    saida = {}
    cenarios = [
        ("gov1_pres1", gov1, pres1, estado["cruzamentos_publicados"]["turno1"], None),
        ("gov1_pres2", gov1, pres2, estado["cruzamentos_publicados"]["turno2"], None),
        ("gov2_pres2", gov2, pres2, {}, empirica),
    ]
    for nome, origem, destino, medidas, emp in cenarios:
        variantes = {}
        for prior in PRIORS:
            variantes[prior] = matriz_transferencia(origem, destino, medidas, prior)
        if emp:
            variantes["empirica_atlas"] = matriz_transferencia(
                origem, destino, medidas, "ideologica", prior_empirica=emp
            )
        direita = melhor_do_campo(origem, "direita")
        robusto = {}
        if direita[0]:
            fugas = {p: vazamento(v, direita[0], FLAVIO) for p, v in variantes.items()}
            robusto["vazamento_da_direita_pct"] = fugas
            validos = [v for v in fugas.values() if v is not None]
            robusto["amplitude_entre_priors_pp"] = round(max(validos) - min(validos), 2)
            robusto["origem"] = direita[0]
            robusto["medida"] = direita[0] in medidas
            base = variantes["ideologica"]
            cond = base["condicional_pct"][direita[0]]
            robusto["destino_do_vazamento_pct"] = {
                "lula": round(cond.get(LULA, 0.0), 2),
                "outras_candidaturas_de_direita": round(
                    sum(
                        v
                        for k, v in cond.items()
                        if k != FLAVIO and campo_de(k) == "direita"
                    ),
                    2,
                ),
                "centro_e_esquerda_alem_de_lula": round(
                    sum(
                        v
                        for k, v in cond.items()
                        if k != LULA
                        and campo_de(k) in ("centro", "centro-esquerda", "esquerda")
                    ),
                    2,
                ),
                "nao_escolha": round(
                    sum(v for k, v in cond.items() if k in NAO_ESCOLHA), 2
                ),
            }
            celula = next(
                c
                for c in base["celulas"]
                if c["origem"] == direita[0] and c["destino"] == FLAVIO
            )
            robusto["celula_direita_para_flavio"] = celula
        saida[nome] = {
            "origem_pergunta": (
                "governador, estimulada"
                if nome.startswith("gov1")
                else "governador, 2o turno"
            ),
            "destino_pergunta": (
                "presidente, 1o turno"
                if nome.endswith("pres1")
                else "presidente, 2o turno"
            ),
            "variantes": variantes,
            "robustez": robusto,
        }
    saida["intersecao_pt_publicada"] = INTERSECOES_PT_PUBLICADAS.get(uf)
    if uf == "SP":
        saida["serie_do_vazamento"] = {
            "agosto_2026_datafolha_pct": 14.0,
            "agosto_2026_atlas_pct": 13.2,
            "fonte_anterior": "docs/assets/sp_092026_camada2.json, campo 18–19/08",
            "setembro_2026_pct": saida["gov2_pres2"]["robustez"][
                "vazamento_da_direita_pct"
            ],
            "nota": (
                "Mesma conta, dois campos. Em setembro a origem é a mesma "
                "pergunta de 2º turno estadual e o destino, a mesma pergunta "
                "de 2º turno presidencial. Comparar como série, não como "
                "medição única: os dois números são estimativa por IPF."
            ),
        }
    saida["limites"] = [
        "Leitura agregada. O diagrama não descreve o percurso de eleitores.",
        "Os limites de Fréchet são os únicos números imunes à prior.",
        "O relatório não declara se a origem do cruzamento publicado é o voto "
        "estimulado de 1º turno ou o de 2º turno para governador; a leitura "
        "adotada é a estimulada de 1º turno.",
        "Preferência partidária não é voto presidencial nem escala "
        "bolsonarista/petista.",
    ]
    return saida


def achados(estados: dict, regional: dict, es: dict, transfer: dict) -> list:
    lista = []
    rj = estados["RJ"]
    lista.append(
        {
            "id": "rj_sinal_invertido",
            "contraprova": True,
            "texto": (
                "No Rio de Janeiro o presidenciável tem mais voto que o "
                "candidato do próprio partido ao governo. Douglas Ruas (PL) "
                f"marca {rj['governador']['turno2']['Douglas Ruas (PL)']} no 2º "
                f"turno estadual e Flávio Bolsonaro marca "
                f"{rj['presidente']['turno2'][FLAVIO]} no 2º turno presidencial, "
                "na mesma amostra."
            ),
            "fonte": {"pdf": "datafolha_21092026_governador_rj.pdf", "pagina": 38},
            "fonte_presidente": {
                "pdf": "datafolha_21092026_estaduais.pdf",
                "pagina": 76,
            },
            "valor_pp": rj["vao"]["turno2"]["vao_pp"],
        }
    )
    for uf in ("SP", "MG"):
        e = estados[uf]
        lista.append(
            {
                "id": f"vao_{uf.lower()}",
                "contraprova": False,
                "texto": (
                    f"Em {uf}, {e['vao']['turno2']['candidato_governador']} tem "
                    f"{e['vao']['turno2']['governador_pct']} no 2º turno estadual "
                    f"e Flávio tem {e['vao']['turno2']['presidenciavel_pct']} no "
                    "2º turno presidencial, na mesma entrevista."
                ),
                "valor_pp": e["vao"]["turno2"]["vao_pp"],
                "rotulo": "teto endereçável, não previsão",
                "fonte": {
                    "pdf": f"datafolha_21092026_governador_{uf.lower()}.pdf",
                    "pagina": e["governador"]["paginas"]["turno2"][0],
                },
            }
        )
    lista.append(
        {
            "id": "cruzamento_publicado",
            "contraprova": False,
            "texto": (
                "O instituto publica linhas do cruzamento governador contra "
                "presidente no texto do relatório presidencial estadual, em SP "
                "(p. 4), RJ (pp. 12 e 13) e MG (pp. 20 e 21). São medições, não "
                "estimativas, e entram fixas em qualquer transferência."
            ),
            "linhas_medidas": sum(len(c["linhas"]) for c in CRUZAMENTOS_PUBLICADOS),
        }
    )
    lista.append(
        {
            "id": "inverso_mg",
            "contraprova": False,
            "texto": (
                "Em Minas o vão inverso é maior que o direto: Lula marca "
                f"{estados['MG']['presidente']['turno2'][LULA]} e Patrus Ananias "
                f"{estados['MG']['governador']['turno2']['Patrus Ananias (PT)']} "
                "no 2º turno estadual."
            ),
            "valor_pp": estados["MG"]["vao"]["inverso_turno2"]["vao_pp"],
        }
    )
    lista.append(
        {
            "id": "regional_contra_estadual",
            "contraprova": False,
            "texto": (
                "O recorte Sudeste do levantamento nacional de 15 a 17/09 dá "
                f"Lula {regional['recorte_nacional']['lula']} contra Flávio "
                f"{regional['recorte_nacional']['flavio']}; a média das três "
                "amostras estaduais de 8 a 10/09, ponderada pelo eleitorado do "
                f"TSE, dá {regional['media_estadual']['lula']} contra "
                f"{regional['media_estadual']['flavio']}."
            ),
            "contraste_pp": regional["contraste"]["diferenca_das_diferencas_pp"],
            "separa_com_95": regional["contraste"]["separa_com_95"],
        }
    )
    lista.append(
        {
            "id": "es_outro_metodo",
            "contraprova": True,
            "texto": (
                "No Espírito Santo, com outro instituto e outro método, a "
                "candidatura de direita ao governo perde para o centro no 1º "
                f"turno: Ferraço {es['governador_turno1']['valores']['Ricardo Ferraço (MDB)']} "
                f"contra Pazolini {es['governador_turno1']['valores']['Lorenzo Pazolini (REPUBLICANOS)']}, "
                f"com Flávio em {es['presidente_turno1']['valores'][FLAVIO]}."
            ),
            "vao_turno2_pp": es["vao"]["turno2"]["vao_pp"],
        }
    )
    senado_atras = {
        uf: {
            "candidato": estados[uf]["senado"]["melhor_da_direita"],
            "voto1_pct": estados[uf]["senado"]["voto1"][
                estados[uf]["senado"]["melhor_da_direita"]
            ],
            "flavio_turno1_pct": estados[uf]["presidente"]["turno1"][FLAVIO],
        }
        for uf in estados
    }
    for valores in senado_atras.values():
        valores["distancia_pp"] = valores["voto1_pct"] - valores["flavio_turno1_pct"]
    lista.append(
        {
            "id": "senado_da_direita_atras_do_topo",
            "contraprova": False,
            "texto": (
                "Nos três estados o melhor primeiro voto de senador da direita "
                "fica pelo menos vinte pontos atrás de Flávio no 1º turno "
                "presidencial, nas mesmas entrevistas. Nenhuma candidatura ao "
                "Senado no Sudeste puxa o topo da chapa."
            ),
            "valores": senado_atras,
            "limite": (
                "O primeiro voto de senador reparte o eleitorado entre muitos "
                "nomes e a candidatura ao Senado disputa duas vagas. A "
                "comparação mede teto, não transferência."
            ),
        }
    )
    lista.append(
        {
            "id": "pl_prefere_flavio_ao_governador",
            "contraprova": True,
            "texto": (
                "Entre quem declara preferência pelo PL, Flávio bate a "
                "candidatura de direita ao governo estadual em MG, 98 contra "
                "96, e no Rio, 99 contra 74. Em SP empatam em 98. O nome "
                "Bolsonaro não depende do palanque estadual dentro da própria "
                "base partidária."
            ),
            "aviso": (
                "Base pequena: 168 entrevistas em MG, 249 no RJ e 252 em SP. "
                "A margem da diferença passa de 16 pontos em todas."
            ),
        }
    )
    sp = transfer["SP"]["gov1_pres1"]["robustez"]
    lista.append(
        {
            "id": "vazamento_sp_medido",
            "contraprova": False,
            "texto": (
                "Em SP o vazamento do eleitor de Tarcísio é medição, não "
                "estimativa: o próprio instituto publica 59% para Flávio, 12% "
                "para Lula e 8% para Cury (p. 4). Isso deixa 41 pontos do "
                "eleitorado de Tarcísio fora de Flávio no 1º turno."
            ),
            "vazamento_pct": sp.get("vazamento_da_direita_pct"),
            "amplitude_entre_priors_pp": sp.get("amplitude_entre_priors_pp"),
        }
    )
    return lista


def escrever_csv(estados: dict, es: dict, destino: Path) -> None:
    campos = [
        "uf",
        "instituto",
        "campo",
        "n",
        "governador_1t_lider",
        "governador_1t_pct",
        "governador_2t_direita",
        "governador_2t_pct",
        "senado_lider",
        "senado_lider_alcance",
        "senado_melhor_direita",
        "presidente_1t_flavio",
        "presidente_1t_lula",
        "presidente_2t_flavio",
        "presidente_2t_lula",
        "vao_1t_pp",
        "vao_2t_pp",
        "vao_inverso_2t_pp",
    ]
    linhas = []
    for uf, e in estados.items():
        g1 = e["governador"]["turno1"]
        lider1 = max(g1, key=lambda k: g1[k] if k not in NAO_ESCOLHA else -1)
        linhas.append(
            {
                "uf": uf,
                "instituto": "Datafolha",
                "campo": e["campo"],
                "n": e["n"],
                "governador_1t_lider": lider1,
                "governador_1t_pct": g1[lider1],
                "governador_2t_direita": e["vao"]["turno2"]["candidato_governador"],
                "governador_2t_pct": e["vao"]["turno2"]["governador_pct"],
                "senado_lider": e["senado"]["lider_alcance"]["nome"],
                "senado_lider_alcance": e["senado"]["lider_alcance"]["valor"],
                "senado_melhor_direita": e["senado"]["melhor_da_direita"],
                "presidente_1t_flavio": e["presidente"]["turno1"][FLAVIO],
                "presidente_1t_lula": e["presidente"]["turno1"][LULA],
                "presidente_2t_flavio": e["presidente"]["turno2"][FLAVIO],
                "presidente_2t_lula": e["presidente"]["turno2"][LULA],
                "vao_1t_pp": e["vao"]["turno1"]["vao_pp"],
                "vao_2t_pp": e["vao"]["turno2"]["vao_pp"],
                "vao_inverso_2t_pp": (
                    e["vao"]["inverso_turno2"]["vao_pp"]
                    if e["vao"]["inverso_turno2"]
                    else ""
                ),
            }
        )
    gov1 = es["governador_turno1"]["valores"]
    linhas.append(
        {
            "uf": "ES",
            "instituto": es["ficha"]["instituto"],
            "campo": es["campo"],
            "n": es["n"],
            "governador_1t_lider": "Ricardo Ferraço (MDB)",
            "governador_1t_pct": gov1["Ricardo Ferraço (MDB)"],
            "governador_2t_direita": es["vao"]["turno2"]["nome"],
            "governador_2t_pct": es["vao"]["turno2"]["governador"],
            "senado_lider": "Renato Casagrande (PSB)",
            "senado_lider_alcance": es["senado"]["alcance"]["valores"][
                "Renato Casagrande (PSB)"
            ],
            "senado_melhor_direita": "Evair de Melo (REPUBLICANOS)",
            "presidente_1t_flavio": es["presidente_turno1"]["valores"][FLAVIO],
            "presidente_1t_lula": es["presidente_turno1"]["valores"][LULA],
            "presidente_2t_flavio": es["presidente_turno2"]["valores"][FLAVIO],
            "presidente_2t_lula": es["presidente_turno2"]["valores"][LULA],
            "vao_1t_pp": es["vao"]["turno1_melhor_direita"]["vao_pp"],
            "vao_2t_pp": es["vao"]["turno2"]["vao_pp"],
            "vao_inverso_2t_pp": "",
        }
    )
    with destino.open("w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)


def publicar_rj() -> dict:
    origem = GOV_DIR / "RJ/relatorio.pdf"
    destino = FONTES / "datafolha_21092026_governador_rj.pdf"
    destino.write_bytes(origem.read_bytes())
    with fitz.open(destino) as doc:
        paginas = doc.page_count
        metadados = doc.metadata
        if metadados is None:
            raise ValueError(f"PDF sem metadados: {destino}")
        criado = metadados.get("creationDate")
    return {
        "caminho": str(destino.relative_to(ROOT)),
        "url": "https://media.folha.com.br/datafolha/2026/09/14/bqte4zka2z4ow4ceoaan9kvjbqba1isxdqzrl-e2jzy.pdf",
        "url_final": "http://media.folha.uol.com.br/datafolha/2026/09/14/bqte4zka2z4ow4ceoaan9kvjbqba1isxdqzrl-e2jzy.pdf",
        "materia": (
            "https://datafolha.folha.uol.com.br/eleicoes/2026/09/"
            "eduardo-paes-psd-mantem-a-lideranca-com-43-das-intencoes-de-voto-"
            "douglas-ruas-pl-cresce-e-tem-25.shtml"
        ),
        "sha256": sha256(destino),
        "bytes": destino.stat().st_size,
        "paginas": paginas,
        "pdf_creation_date": criado,
        "registros_tse": ["RJ-09217/2026", "BR-06361/2026"],
        "projeto": "PO4286",
        "campo": "08–10/09/2026",
        "n": 1204,
        "municipios": 35,
        "contratantes": "Folha de S.Paulo e TV Globo",
        "margem_declarada_pp": 3,
    }


def main() -> None:
    fonte_rj = publicar_rj()
    governadores = json.loads(GOVERNADORES.read_text(encoding="utf-8"))
    tabelas_gov = {"SP": {}, "MG": {}, "RJ": {}}
    for uf in ("SP", "MG"):
        existente = governadores["tables"][uf]["governor"]
        renomeado = {
            "senado_voto1": "senado_1",
            "senado_voto2": "senado_2",
            "senado_alcance": "senado_total",
            "avaliacao_governador": "avaliacao",
            "aprovacao_governador": "aprovacao",
        }
        for chave in GOV_PAGINAS[uf]:
            origem = renomeado.get(chave, chave)
            tabela = dict(existente[origem])
            tabela["pdf_pages"] = GOV_PAGINAS[uf][chave]
            tabelas_gov[uf][chave] = tabela
    tabelas_gov["RJ"] = extrair(
        GOV_DIR / "RJ/relatorio.pdf", GOV_PAGINAS["RJ"], GOV_OFFSET["RJ"]
    )
    tabelas_pres = {
        uf: extrair(PRESIDENCIAL, PRES_PAGINAS[uf], PRES_OFFSET[uf])
        for uf in PRES_PAGINAS
    }
    for uf, blocos in tabelas_pres.items():
        com = topo(blocos["turno1_com_marcal"])
        sem = topo(blocos["turno1"])
        if not any("Marçal" in k for k in com):
            raise ValueError(f"Situacao A sem Marcal em {uf}")
        if any("Marçal" in k for k in sem):
            raise ValueError(f"Situacao B com Marcal em {uf}")

    estados = {}
    provas = []
    pior = 0.0
    for uf in ("SP", "RJ", "MG"):
        n = achatar(tabelas_gov[uf]["turno2"])[1]["Total"]
        n_pres = achatar(tabelas_pres[uf]["turno2"])[1]["Total"]
        if n != n_pres:
            raise ValueError(f"Bases divergentes em {uf}: {n} e {n_pres}")
        dims_fechadas = fechadas(tabelas_gov[uf]["turno2"])
        abertas = set(DIMENSOES) - dims_fechadas
        estados[uf] = montar_estado(uf, tabelas_gov[uf], tabelas_pres[uf], n, abertas)
        estados[uf]["particoes_fechadas"] = sorted(dims_fechadas)
        estados[uf]["particoes_abertas"] = sorted(abertas)
        for rotulo, conjunto in [
            (f"{uf}/governador", tabelas_gov[uf]),
            (f"{uf}/presidente", tabelas_pres[uf]),
        ]:
            p, w = provar(conjunto, rotulo, dims_fechadas)
            provas.extend(p)
            pior = max(pior, w)
    transfer = {
        uf: transferencias(uf, estados[uf], tabelas_gov[uf], tabelas_pres[uf])
        for uf in estados
    }
    eleitores = eleitorado_tse()
    regional = regional_contra_estadual(estados, eleitores)
    validos = votos_2022_validos()
    es = bloco_es()
    if not es["conferencia_turno2"]["confere"]:
        raise ValueError("Pareamento do 2o turno do ES nao confere")

    saida = {
        "meta": {
            "titulo": "Sudeste 2026: governador, senador e presidente na mesma amostra",
            "gerado_por": "scripts/datafolha-21092026-sudeste.py",
            "instituto": "Datafolha",
            "campo_estadual": "08–10/09/2026",
            "campo_nacional": "15–17/09/2026",
            "metodo": (
                "Extração do texto nativo dos anexos de tabelas cruzadas. "
                "Nenhum número do Datafolha é digitado à mão, exceto as linhas "
                "de cruzamento entre cargos publicadas no texto corrido, que "
                "vêm com a página ao lado."
            ),
        },
        "fontes": {
            "datafolha_21092026_governador_rj.pdf": fonte_rj,
            "datafolha_21092026_governador_sp.pdf": {
                "projeto": "PO4285",
                "registros_tse": ["SP-04189/2026", "BR-03904/2026"],
                "n": 1610,
                "municipios": 65,
                "campo": "08–10/09/2026",
            },
            "datafolha_21092026_governador_mg.pdf": {
                "projeto": "PO4287",
                "registros_tse": ["MG-01611/2026", "BR-03022/2026"],
                "n": 1204,
                "municipios": 55,
                "campo": "08–10/09/2026",
            },
            "datafolha_21092026_estaduais.pdf": {
                "projetos": ["PO4285", "PO4286", "PO4287", "PO4288", "PO4289"],
                "paginas_narrativa": {"SP": 4, "RJ": [12, 13], "MG": [20, 21]},
                "campo": "08–10/09/2026",
            },
        },
        "estados": estados,
        "cruzamentos_publicados": CRUZAMENTOS_PUBLICADOS,
        "aprovacao_por_voto_de_governador": APROVACAO_POR_GOVERNADOR,
        "varredura_de_cruzamentos": {
            "arquivos": [
                "datafolha_21092026_governador_sp.pdf",
                "datafolha_21092026_governador_mg.pdf",
                "datafolha_21092026_governador_rj.pdf",
                "datafolha_21092026_estaduais.pdf",
                "datafolha_21092026.pdf",
                "datafolha_21092026_questionario.pdf",
            ],
            "termos": [
                "cruzamento",
                "migracao",
                "vs.",
                "por intencao de voto",
                "voto para presidente",
                "voto para governador",
                "Bloco 4",
            ],
            "resultado": (
                "Os anexos de tabelas cruzadas têm exatamente três blocos e "
                "nenhum deles usa o voto de outro cargo como coluna. O "
                "cruzamento entre cargos existe, mas só no texto corrido do "
                "relatório presidencial estadual, nas páginas 4, 12, 13, 20 e "
                "21. Os relatórios de governador não citam a Presidência."
            ),
            "linhas_medidas": sum(len(c["linhas"]) for c in CRUZAMENTOS_PUBLICADOS),
            "o_que_falta": (
                "A matriz completa governador contra presidente, com bases e "
                "pesos. A fidelidade de base do 2º turno estadual também não é "
                "publicada."
            ),
            "perguntas_ausentes": [
                "Não há pergunta de conhecimento das candidaturas em nenhum "
                "dos três relatórios estaduais de governador e senador.",
                "Não há rejeição ao Senado; a rejeição só existe para o "
                "governo do estado.",
                "Não há cruzamento do voto de 2022 com o voto de 2026 nos "
                "relatórios estaduais.",
            ],
        },
        "discrepancias_documentais": [
            {
                "tema": "Situação A e Situação B no anexo presidencial",
                "achado": (
                    "A Situação A do anexo é o cenário COM Pablo Marçal e a "
                    "Situação B é o cenário SEM Marçal, que é o que reproduz o "
                    "placar da manchete. O rótulo não diz isso; a leitura sai "
                    "da presença da linha de Marçal, conferida pelo script."
                ),
                "efeito": (
                    "O campo `first_president` de "
                    "docs/assets/datafolha_21092026_governadores.json usa a "
                    "Situação A, ou seja, o cenário com Marçal. Esta camada usa "
                    "a Situação B no 1º turno e guarda a A em "
                    "`turno1_com_marcal`."
                ),
            },
            {
                "tema": "Partição fechada varia por estado",
                "achado": (
                    "Renda cobre 95,9% a 97,1% das bases e nunca fecha, porque "
                    "recusa e não sabe existem no cartão e não ganham coluna. "
                    "Partido de preferência fecha em SP e MG e cobre 97,2% no "
                    "Rio. Religião cobre de 64,7% a 81,8%."
                ),
                "efeito": (
                    "Agregar um indicador ao estado por renda ou por religião "
                    "inventa cobertura. Esta camada só recompõe por partição "
                    "fechada, medida estado a estado."
                ),
            },
            {
                "tema": "Registro duplo por relatório estadual",
                "achado": (
                    "Cada estado carrega um registro estadual e um registro "
                    "federal: SP-04189 e BR-03904, RJ-09217 e BR-06361, "
                    "MG-01611 e BR-03022. Número BR não significa amostra "
                    "nacional."
                ),
                "efeito": ("Nenhuma dessas amostras entra em média nacional."),
            },
        ],
        "transferencia": transfer,
        "regional_contra_estadual": regional,
        "ordem_de_grandeza": ordem_de_grandeza(estados, eleitores, validos),
        "espirito_santo": es,
        "provas_de_leitura": {
            "pior_residuo_pp": round(pior, 3),
            "limite_pp": 1.5,
            "total": len(provas),
            "acima_de_1_05pp": [p for p in provas if abs(p["residuo_pp"]) > 1.05],
            "amostra": provas[:40],
        },
        "achados": achados(estados, regional, es, transfer),
        "limites": [
            "O vão é teto endereçável, não previsão: votar no governador não "
            "torna o eleitor disponível para o presidenciável.",
            "Cargos, cédulas e incentivos são diferentes. Diferença entre "
            "cargos não prova inconsistência do instituto.",
            "Sem microdados, a igualdade dos pesos individuais entre as "
            "perguntas não é demonstrável, só a igualdade das bases ponderadas.",
            "As amostras estaduais e o recorte regional do levantamento "
            "nacional têm campos diferentes e desenhos diferentes.",
            "O Espírito Santo entra com outro instituto e outro método, e não "
            "fecha a conta do Sudeste.",
            "Margens calculadas sob amostragem aleatória simples. O efeito de "
            "desenho não é publicado.",
        ],
    }
    (ASSETS / "datafolha_21092026_sudeste.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    escrever_csv(estados, es, ASSETS / "datafolha_21092026_sudeste.csv")
    resumo = {
        uf: {
            "governador_2t": e["vao"]["turno2"]["governador_pct"],
            "flavio_2t": e["vao"]["turno2"]["presidenciavel_pct"],
            "vao_2t_pp": e["vao"]["turno2"]["vao_pp"],
            "vao_1t_pp": e["vao"]["turno1"]["vao_pp"],
            "senado_lider": e["senado"]["lider_alcance"],
        }
        for uf, e in estados.items()
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=2))
    print(f"pior residuo de recomposicao: {pior:.3f} pp")
    print(
        f"linhas de cruzamento medidas: {saida['varredura_de_cruzamentos']['linhas_medidas']}"
    )


if __name__ == "__main__":
    main()
