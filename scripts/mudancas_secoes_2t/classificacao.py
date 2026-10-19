"""Classificação de cada seção entre o cadastro do 1º e o do 2º turno.

Duas camadas:

- ``categoria_cadastro``: a regra fixa do contrato (A a Z), aplicada à linha de cada
  seção como o TSE a publica. Reproduz a contagem de referência do orquestrador.
- ``categoria`` e ``mudanca_real``: o que o eleitor sente. Seção agregada vota na urna
  da principal, então herda a classificação da principal (o local que o cadastro
  registra para a agregada pode ser outro prédio, onde ela não vota).

``mudanca_real`` exige evidência de outro prédio: outro número de local (A, B, C, X),
nome e endereço diferentes depois da normalização (D) ou outro logradouro (E). Só a
coordenada (G, H) ou só o nome (F) não bastam; as decisões estão em ``REGRAS``.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from mudancas_secoes_2t import endereco as en

LIMITE_COORD_M = 300.0
LIMITE_SUSPEITA_M = 50_000.0
REPETIDA_MIN_LOCAIS = 3
SEMELHANCA_OUTRA_INSTITUICAO = 0.2

NOMES = {
    "A": "retorno ao original",
    "B": "nova realocação",
    "C": "de um temporário para outro",
    "X": "número original mudou",
    "D": "mesmo número, nome e endereço mudaram",
    "E": "mesmo número, endereço mudou",
    "F": "mesmo número, só o nome mudou",
    "G": "mesmo número, coordenada moveu mais de 300 m",
    "H": "mesmo número, coordenada moveu até 300 m",
    "Z": "igual",
}
REGRAS = {
    "A": "local do 1º turno diferente do 2º; o do 1º era temporário (diferente do "
    "original) e o do 2º é o original.",
    "B": "local do 1º turno diferente do 2º; o do 1º era o original e o do 2º é "
    "temporário.",
    "C": "local do 1º turno diferente do 2º e os dois diferentes do original.",
    "X": "local do 1º turno diferente do 2º, fora dos três casos anteriores.",
    "D": "mesmo número de local; nome e endereço diferentes no texto do TSE.",
    "E": "mesmo número de local; só o endereço difere no texto do TSE.",
    "F": "mesmo número de local; só o nome difere no texto do TSE.",
    "G": "mesmo número, nome e endereço iguais; coordenada a mais de 300 m, ou "
    "coordenada presente em um turno e ausente no outro.",
    "H": "mesmo número, nome e endereço iguais; coordenada moveu até 300 m.",
    "Z": "nada mudou.",
    "mudanca_real": "A, B, C e X contam, salvo quando nome e endereço normalizados são "
    "iguais (outro número para o mesmo prédio). D conta, salvo quando nome e "
    "endereço normalizados são iguais (só grafia). E conta quando o logradouro "
    "normalizado é outro. F, G e H nunca contam: com nome e endereço iguais, o "
    "eleitor vai ao mesmo prédio, e a coordenada é metadado de georreferenciamento.",
    "agregada": "seção agregada vota na urna da principal e herda a classificação "
    "dela; a categoria do próprio registro fica em categoria_cadastro.",
    "normalizacao": "maiúsculas, sem acento, sem pontuação, abreviações expandidas "
    "(R. vira RUA, AV. vira AVENIDA, PÇA. vira PRACA), marcador de número e CEP "
    "removidos, complemento entre parênteses removido; cada parte separada por ' - ' "
    "é candidata a logradouro; mesmo logradouro quando as palavras significativas "
    "da grafia menor estão todas na maior.",
    "coord_repetida": f"coordenada idêntica para {REPETIDA_MIN_LOCAIS} ou mais locais "
    "de números diferentes no mesmo município e turno: marcador de posição, não "
    "posição do prédio; a distância dessas seções fica fora das estatísticas.",
}


@dataclass(frozen=True)
class Classificacao:
    categoria: str
    mudanca_real: bool
    motivo: str
    confianca: str | None
    coord_suspeita: bool
    revisar: bool


def _nan(x: Any) -> bool:
    return x is None or (isinstance(x, float) and math.isnan(x))


def categoria_cadastro(
    l1: Mapping[str, Any], l2: Mapping[str, Any], dist: float | None
) -> str:
    """Regra fixa do contrato sobre os campos crus do TSE."""
    loc1, loc2 = int(l1["local"]), int(l2["local"])
    org1, org2 = int(l1["original"]), int(l2["original"])
    if loc1 != loc2:
        if loc1 != org1 and loc2 == org2:
            return "A"
        if loc1 == org1 and loc2 != org2:
            return "B"
        if loc1 != org1 and loc2 != org2:
            return "C"
        return "X"
    nome_dif = l1["nome"] != l2["nome"]
    end_dif = l1["endereco"] != l2["endereco"]
    if nome_dif and end_dif:
        return "D"
    if end_dif:
        return "E"
    if nome_dif:
        return "F"
    tem1 = not (_nan(l1["lat"]) or _nan(l1["lon"]))
    tem2 = not (_nan(l2["lat"]) or _nan(l2["lon"]))
    if tem1 != tem2:
        return "G"
    if dist is None or _nan(dist) or dist == 0:
        return "Z"
    return "G" if dist > LIMITE_COORD_M else "H"


def classificar_linha(
    l1: Mapping[str, Any],
    l2: Mapping[str, Any],
    dist: float | None = None,
    repetida: bool = False,
) -> Classificacao:
    """Categoria, mudança real e motivo em texto para um par de linhas 1T/2T."""
    if dist is None:
        dist = en.haversine_m(l1["lat"], l1["lon"], l2["lat"], l2["lon"])
    cat = categoria_cadastro(l1, l2, dist)
    mesmo_nome = en.normalizar_nome(l1["nome"]) == en.normalizar_nome(l2["nome"])
    mesmo_end = en.mesmo_endereco(l1["endereco"], l2["endereco"])
    suspeita = dist is not None and not _nan(dist) and dist > LIMITE_SUSPEITA_M
    loc1, loc2, org = int(l1["local"]), int(l2["local"]), int(l2["original"])
    if cat in "ABCX":
        if mesmo_nome and mesmo_end:
            return Classificacao(
                cat,
                False,
                f"Outro número de local ({loc1} para {loc2}) com nome e endereço "
                "iguais depois da normalização: o mesmo prédio.",
                None,
                suspeita,
                True,
            )
        texto = {
            "A": f"Volta ao local original ({loc2}); no 1º turno votou no local "
            f"temporário {loc1}.",
            "B": f"Sai do local original ({loc1}) para o local temporário {loc2}.",
            "C": f"Troca de local temporário ({loc1} para {loc2}); o original ({org}) "
            "segue fora de uso.",
            "X": f"Outro número de local ({loc1} para {loc2}) e outro original no cadastro.",
        }[cat]
        return Classificacao(cat, True, texto, "alta", suspeita, False)
    if cat == "D":
        if mesmo_nome and mesmo_end:
            return Classificacao(
                cat,
                False,
                "Mesmo número; nome e endereço só mudaram de grafia.",
                None,
                False,
                False,
            )
        conf = "alta" if not mesmo_end else "media"
        extra = (
            ""
            if not mesmo_end
            else " O endereço normalizado é o mesmo; o nome é de outro prédio."
        )
        return Classificacao(
            cat,
            True,
            f"Mesmo número de local ({loc1}), com outro nome e outro endereço.{extra}",
            conf,
            suspeita,
            mesmo_end,
        )
    if cat == "E":
        if en.mesmo_logradouro(l1["endereco"], l2["endereco"]):
            return Classificacao(
                cat,
                False,
                "Mesmo nome e número; endereço reescrito no mesmo logradouro "
                "(edição de cadastro).",
                None,
                False,
                False,
            )
        return Classificacao(
            cat,
            True,
            "Mesmo nome e número de local, endereço em outro logradouro; pode ser outra "
            "entrada do mesmo prédio.",
            "media",
            suspeita,
            True,
        )
    if cat == "F":
        sem = en.semelhanca_nomes(l1["nome"], l2["nome"])
        revisar = sem <= SEMELHANCA_OUTRA_INSTITUICAO
        texto = "Só o nome do local mudou; número e endereço iguais."
        if revisar:
            texto += " O nome novo é de outra instituição: conferir no e-Título."
        return Classificacao(cat, False, texto, None, False, revisar)
    if cat == "G":
        if dist is None or math.isnan(dist):
            texto = "Nome e endereço iguais; a coordenada existe em um só dos turnos."
            return Classificacao(cat, False, texto, None, True, False)
        texto = (
            f"Nome e endereço iguais; só a coordenada mudou ({dist / 1000:.1f} km): "
            "correção de georreferenciamento."
        )
        return Classificacao(cat, False, texto, None, suspeita or repetida, False)
    if cat == "H":
        return Classificacao(
            cat,
            False,
            f"Coordenada ajustada em {dist:.0f} m; nada muda para o eleitor.",
            None,
            False,
            False,
        )
    return Classificacao("Z", False, "Sem alteração.", None, False, False)


def coordenadas_repetidas(df: pd.DataFrame, sufixo: str) -> pd.Series:
    """Seções cujo local tem coordenada compartilhada por 3 ou mais locais do município."""
    lat, lon, loc = f"lat{sufixo}", f"lon{sufixo}", f"local{sufixo}"
    base = df[["uf", "mun", loc, lat, lon]].dropna().drop_duplicates()
    cont = base.groupby(["uf", "mun", lat, lon])[loc].nunique()
    marcadas = cont[cont >= REPETIDA_MIN_LOCAIS].reset_index()[["uf", "mun", lat, lon]]
    marcadas["_rep"] = True
    out = df[["uf", "mun", lat, lon]].merge(
        marcadas, on=["uf", "mun", lat, lon], how="left"
    )
    return out["_rep"].eq(True).set_axis(df.index)


CAMPOS_LOCAL = [
    "local",
    "nome",
    "endereco",
    "bairro",
    "cep",
    "lat",
    "lon",
    "original",
    "nome_original",
    "endereco_original",
]


def juntar(t1: pd.DataFrame, t2: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por seção com os campos do 1º turno (``_1t``) e do 2º (``_2t``)."""
    chave = ["uf", "mun", "zona", "secao"]
    extra = ["municipio", "tipo_secao", "principal", "eleitores", "eleitores_federal"]
    base = t1[[*chave, *extra, "tipo_local", *CAMPOS_LOCAL]]
    segundo = t2[[*chave, "eleitores", "tipo_local", *CAMPOS_LOCAL]]
    df = base.merge(
        segundo, on=chave, suffixes=("_1t", "_2t"), validate="1:1", how="outer"
    )
    if df["local_1t"].isna().any() or df["local_2t"].isna().any():
        raise ValueError("seção presente em um só dos cadastros")
    return df.reset_index(drop=True)


def classificar(t1: pd.DataFrame, t2: pd.DataFrame) -> pd.DataFrame:
    """Classifica todas as seções e acrescenta a camada efetiva (agregada herda)."""
    df = juntar(t1, t2)
    df["distancia_m"] = en.haversine_vetor(
        df["lat_1t"].to_numpy(float),
        df["lon_1t"].to_numpy(float),
        df["lat_2t"].to_numpy(float),
        df["lon_2t"].to_numpy(float),
    )
    df["coord_repetida_1t"] = coordenadas_repetidas(df, "_1t")
    df["coord_repetida_2t"] = coordenadas_repetidas(df, "_2t")
    df["coord_repetida"] = df["coord_repetida_1t"] | df["coord_repetida_2t"]
    df["coord_um_turno"] = df["lat_1t"].isna() != df["lat_2t"].isna()
    df["temp_1t"] = df["local_1t"] != df["original_1t"]
    df["temp_2t"] = df["local_2t"] != df["original_2t"]
    igual = (
        (df["local_1t"] == df["local_2t"])
        & (df["nome_1t"] == df["nome_2t"])
        & (df["endereco_1t"] == df["endereco_2t"])
        & (df["distancia_m"].fillna(0) == 0)
        & (df["lat_1t"].isna() == df["lat_2t"].isna())
    )
    cats = np.full(len(df), "Z", dtype=object)
    reais = np.zeros(len(df), dtype=bool)
    motivos = np.full(len(df), "Sem alteração.", dtype=object)
    conf = np.full(len(df), None, dtype=object)
    susp = np.zeros(len(df), dtype=bool)
    revisar = np.zeros(len(df), dtype=bool)
    registros = df.loc[~igual].to_dict("records")
    for i, r in zip(df.index[~igual], registros, strict=True):
        l1 = {c: r[f"{c}_1t"] for c in CAMPOS_LOCAL}
        l2 = {c: r[f"{c}_2t"] for c in CAMPOS_LOCAL}
        d = r["distancia_m"]
        res = classificar_linha(
            l1, l2, None if _nan(d) else float(d), bool(r["coord_repetida"])
        )
        cats[i], reais[i], motivos[i] = res.categoria, res.mudanca_real, res.motivo
        conf[i], susp[i], revisar[i] = res.confianca, res.coord_suspeita, res.revisar
    df["categoria_cadastro"] = cats
    df["mudanca_real_cadastro"] = reais
    df["motivo_cadastro"] = motivos
    df["confianca_cadastro"] = conf
    df["coord_suspeita_cadastro"] = susp
    df["revisar_cadastro"] = revisar
    return efetiva(df)


COLUNAS_HERDADAS = [
    *(f"{c}_1t" for c in CAMPOS_LOCAL),
    *(f"{c}_2t" for c in CAMPOS_LOCAL),
    "tipo_local_1t",
    "tipo_local_2t",
    "distancia_m",
    "coord_repetida",
    "coord_repetida_1t",
    "coord_repetida_2t",
    "temp_1t",
    "temp_2t",
]


def efetiva(df: pd.DataFrame) -> pd.DataFrame:
    """Camada efetiva: agregada recebe local e classificação da principal."""
    df["urna"] = np.where(df["tipo_secao"] == 2, df["principal"], df["secao"]).astype(
        "int64"
    )
    df["agregada"] = df["tipo_secao"] == 2
    princ = df.loc[~df["agregada"]].set_index(["uf", "mun", "zona", "secao"])
    chave = pd.MultiIndex.from_arrays([df["uf"], df["mun"], df["zona"], df["urna"]])
    pares = {
        "categoria": "categoria_cadastro",
        "mudanca_real": "mudanca_real_cadastro",
        "motivo_classificacao": "motivo_cadastro",
        "confianca": "confianca_cadastro",
        "coord_suspeita": "coord_suspeita_cadastro",
        "revisar": "revisar_cadastro",
    }
    for novo, velho in pares.items():
        df[novo] = princ[velho].reindex(chave).to_numpy()
    df["local_cadastro_1t"] = df["local_1t"]
    df["local_cadastro_2t"] = df["local_2t"]
    df["temp_1t_cadastro"] = df["temp_1t"]
    df["temp_2t_cadastro"] = df["temp_2t"]
    for c in COLUNAS_HERDADAS:
        df[c] = princ[c].reindex(chave).to_numpy()
    df["herdada"] = df["agregada"] & (df["categoria"] != df["categoria_cadastro"])
    if df["categoria"].isna().any():
        raise ValueError("agregada sem principal no cadastro")
    df["mudanca_real"] = df["mudanca_real"].astype(bool)
    df["coord_suspeita"] = df["coord_suspeita"].astype(bool)
    df["revisar"] = df["revisar"].astype(bool)
    df["distancia_suspeita"] = df["distancia_m"] > LIMITE_SUSPEITA_M
    df.loc[df["agregada"], "motivo_classificacao"] = (
        "Seção agregada à seção " + df["urna"].astype(str) + ", vota na urna dela. "
    ) + df.loc[df["agregada"], "motivo_classificacao"]
    return df
