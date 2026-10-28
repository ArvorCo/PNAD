"""IPS Brasil 2026: junção auditável com municípios eleitorais, sem imputar IDHM.

A exportação oficial CSV não inclui código IBGE. O casamento usa UF e nome
normalizado, mais equivalências explícitas. Nunca aproxima nomes automaticamente.
"""

from __future__ import annotations

import csv
import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIGINAIS = ROOT / "data/originals/analise_realidade_eleicao"
# Variações de grafia e denominação entre a exportação IPS e o cadastro TSE.
# Códigos: https://www.ibge.gov.br/explica/codigos-dos-municipios.php
EQUIVALENCIAS = {
    ("PR", "MUNHOZ DE MELO"): "4116307",
    ("MG", "DONA EUZEBIA"): "3122900",
    ("SE", "AMPARO DO SAO FRANCISCO"): "2800100",
    ("MG", "SAO TOME DAS LETRAS"): "3165206",
    ("SE", "GRACHO CARDOSO"): "2802601",
    ("RN", "ARES"): "2401206",
    ("GO", "BOM JESUS DE GOIAS"): "5203500",
    ("RN", "ACU"): "2400208",
    ("MG", "PINGO-D'AGUA"): "3150539",
    ("RO", "ALVORADA D'OESTE"): "1100346",
    ("SP", "SAO LUIZ DO PARAITINGA"): "3550001",
    ("MG", "SEM-PEIXE"): "3165560",
    ("RO", "ESPIGAO D'OESTE"): "1100098",
    ("MG", "OLHOS-D'AGUA"): "3145455",
    ("RN", "JANUARIO CICCO"): "2405306",
    ("MT", "SANTO ANTONIO DE LEVERGER"): "5107800",
    ("PA", "ELDORADO DO CARAJAS"): "1502954",
}
CAMPOS = {
    "ips": "Índice de Progresso Social",
    "necessidades_basicas": "Necessidades Humanas Básicas",
    "bem_estar": "Fundamentos do Bem-estar",
    "oportunidades": "Oportunidades",
    "seguranca_pessoal": "Segurança Pessoal",
    "educacao_superior": "Acesso à Educação Superior",
}


def normalizar(nome: str) -> str:
    return (
        "".join(
            c
            for c in unicodedata.normalize("NFKD", nome.upper())
            if not unicodedata.combining(c)
        )
        .replace("’", "'")
        .strip()
    )


def carregar(municipios: list[dict], origem: Path = ORIGINAIS) -> dict:
    caminho = origem / "ips_2026.csv"
    manifesto = json.loads((origem / "fontes.json").read_text())
    fonte = next(x for x in manifesto if x["arquivo"] == caminho.name)
    if hashlib.sha256(caminho.read_bytes()).hexdigest() != fonte["sha256"]:
        raise ValueError("CSV IPS alterado: confira a fonte e o manifesto")
    por_nome, por_ibge = {}, {}
    for m in municipios:
        if m["uf"] == "ZZ":
            continue
        chave = (m["uf"], normalizar(m["nome"]))
        if chave in por_nome or m["ibge"] in por_ibge:
            raise ValueError(f"Município duplicado: {chave}")
        por_nome[chave] = m
        por_ibge[m["ibge"]] = m
    dados, equivalencias = {}, []
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            chave = (r["UF"], normalizar(r["Município"]))
            m = por_nome.get(chave)
            regra = "UF e nome normalizado"
            if m is None:
                m = por_ibge.get(EQUIVALENCIAS.get(chave))
                regra = "equivalência explícita"
            if m is None or m["uf"] != r["UF"]:
                raise ValueError(f"IPS sem casamento inequívoco: {chave}")
            ibge = m["ibge"]
            if ibge in dados:
                raise ValueError(f"IPS duplicado: {ibge}")
            valores = {k: float(r[v]) for k, v in CAMPOS.items()}
            if any(not 0 <= v <= 100 for v in valores.values()):
                raise ValueError(f"Pontuação IPS fora de 0–100: {ibge}")
            dados[ibge] = {"nome_fonte": r["Município"], "uf": r["UF"], **valores}
            if regra == "equivalência explícita":
                equivalencias.append(
                    {
                        "ibge": ibge,
                        "uf": m["uf"],
                        "nome_ips": r["Município"],
                        "nome_tse": m["nome"],
                    }
                )
    return {
        "indicador": "IPS Brasil 2026",
        "edicao": 2026,
        "corte_disponibilidade": "2026-02-20",
        "escala": "municipal",
        "n_municipios": len(dados),
        "dados": dados,
        "equivalencias": equivalencias,
        "sem_ips": [
            {"ibge": k, "uf": m["uf"], "nome": m["nome"]}
            for k, m in por_ibge.items()
            if k not in dados
        ],
        "fonte": fonte,
        "limites": [
            "IPS é progresso social e ambiental, não IDHM nem medida de renda.",
            "Edição 2026 reúne anos diferentes; 12 de 57 indicadores não mudaram desde a edição anterior.",
            "O índice municipal não identifica desigualdades entre bairros ou zonas eleitorais.",
            "Boa Esperança do Norte/MT não integra o IPS por insuficiência de dados.",
            "As edições originais 2024, 2025 e 2026 não são estritamente comparáveis.",
        ],
    }
