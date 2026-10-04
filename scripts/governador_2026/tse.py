"""Candidaturas a governador 2026, fotos oficiais e casamento de nomes.

Reaproveita o leitor do TSE do Senado (`senado_2026.tse`) com o cargo 3 e as
tabelas de apelido próprias deste cargo. Nada é adivinhado: cada exceção de
nome está declarada em APELIDOS com o motivo ao lado.
"""

from __future__ import annotations

import json
from pathlib import Path

from senado_2026 import tse as T

ROOT = T.ROOT
SAIDA = ROOT / "analysis/governador_2026"
PESQUISAS = SAIDA / "pesquisas"
IMG = ROOT / "docs/img/governador"
CARGO = "3"

# (UF, nome normalizado na pesquisa) -> nome de urna normalizado no TSE.
# Conferido contra consulta_cand_2026 em 03/10/2026; motivo ao lado.
APELIDOS: dict[tuple[str, str], str] = {
    # nome de urna "GUSTAVO PELO PIAUÍ OU GUSTAVO"; a pesquisa imprime a primeira parte
    ("PI", "gustavo pelo piaui"): "gustavo pelo piaui ou gustavo",
    # nome de urna "DANILO DA SILVA"; a pesquisa usa o nome do meio (Danilo Pinheiro)
    ("GO", "danilo pinheiro"): "danilo da silva",
    # nome de urna "RODRIGO DE BOLSONARO"; a pesquisa omite a preposição
    ("RN", "rodrigo bolsonaro"): "rodrigo de bolsonaro",
    # nome de urna "CLÉCIO"; a pesquisa imprime nome e sobrenome
    ("AP", "clecio luis"): "clecio",
    # nome de urna "DOUTORA NATASHA"; a pesquisa imprime o nome civil
    ("MT", "natasha slhessarenko"): "doutora natasha",
    # nome de urna "DR. DANIEL"; o 2º turno da Real Time imprime "DR. DANIEL SANTOS"
    ("PA", "dr daniel santos"): "dr daniel",
    # nome de urna "RENAN"; a pesquisa imprime nome e sobrenome
    ("PE", "renan hallais"): "renan",
    # nome de urna "CLÉBIO GENUÍNO"; a pesquisa imprime o sobrenome final
    ("RR", "clebio nascimento"): "clebio genuino",
    # nome de urna "PROFESSOR ROBERIO PAULINO"; uma pesquisa imprime "Roberto"
    ("RN", "professor roberto paulino"): "professor roberio paulino",
    # nome de urna "JEFERSON BEZERRA"; uma pesquisa imprime com dois efes
    ("MS", "jefferson bezerra"): "jeferson bezerra",
    # dois registros da mesma pessoa no TSE; a grafia curta aponta para o registro
    # mais recente (desempate abaixo)
    ("MT", "sgto laudicerio"): "sargento laudicerio",
}

# Grafia de exibição quando a caixa de título erra a sigla ou a pontuação do
# nome de urna. Chave: nome de urna do TSE.
GRAFIA: dict[str, str] = {
    "ACM NETO": "ACM Neto",
    "DR.LUISINHO": "Dr. Luisinho",
    "GUSTAVO PELO PIAUÍ OU GUSTAVO": "Gustavo pelo Piauí",
    "BRUNO PEDREIRO DO PCO": "Bruno Pedreiro do PCO",
    "SIQUEIRA CAMPOS JR": "Siqueira Campos Jr.",
}

# Nome de urna repetido na mesma UF (dois registros da mesma pessoa): SQ do
# registro mais recente, declarado aqui.
DESEMPATE: dict[tuple[str, str], str] = {
    ("MT", "sargento laudicerio"): "110002554073",
}


def nomes_das_pesquisas(pasta: Path = PESQUISAS) -> list[tuple[str, str]]:
    """Nomes citados no 1º turno, nos cenários alternativos e no 2º turno."""
    saida: list[tuple[str, str]] = []
    for arq in sorted(pasta.glob("*.json")):
        dados = json.loads(arq.read_text(encoding="utf-8"))
        uf = dados.get("uf")
        if not uf:
            continue
        blocos = [
            dados,
            *(dados.get("cenarios_alternativos") or []),
            *(dados.get("segundo_turno") or []),
        ]
        for b in blocos:
            saida.extend((uf, c["nome"]) for c in b.get("candidatos") or [])
    return saida


def ler_candidatos(campo_de) -> list[dict]:
    return T.ler_candidatos(T.CAND_ZIP, campo_de, cargo=CARGO)


def casar(candidatos: list[dict], citados) -> tuple[list[dict], list[dict]]:
    return T.casar_nomes(candidatos, citados, APELIDOS, DESEMPATE)
