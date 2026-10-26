"""Regras do estudo de metadados das urnas: repetição entre seções, coerência entre fontes
e cruzamento com o voto. Funções puras sobre DataFrames já lidos por `metadados_base`.

Cada campo tem um escopo declarado, que diz quando a repetição é esperada:

- `secao`: um valor por seção (hash do BU, hash de transmissão, arquivo `.vsc`);
- `urna`: um valor por urna (número interno, código de carga, flash de votação,
  certificado de hardware, série da MR); repetir só é esperado quando a mesma urna
  responde por mais de uma seção (sistema de apuração da junta, contingência);
- `compartilhado`: a mesma mídia ou o mesmo computador servem várias urnas (mídia de
  carga FC, gerador de mídia); repetir é a regra dentro da zona e da UF;
- `global`: um valor para o país (versão do software, chave de software do TSE).

Explicações candidatas, na ordem em que são testadas: valor de preenchimento, sistema de
apuração, votação recuperada (RED), seção agregada, mesma urna (com a classificação de
`urnas_analise.classificar_grupo`), contingência, mídia compartilhada, coincidência de
identificador de 32 bits (só quando o número de pares observado não passa do esperado ao
acaso). O que sobra é "sem explicação pela regra": pede explicação, não prova
irregularidade.
"""

from __future__ import annotations

import json
import math
from collections import Counter

import numpy as np
import pandas as pd

from .urnas_analise import (
    CONTINGENCIA,
    SISTEMA_APURACAO,
    _media_ic,
    classificar_grupo,
    excesso_vizinhas,
    geografia,
)
from .urnas_base import CHAVE

ROTULO = "pede explicação, não prova irregularidade"
MODELO_CODIGO = {13: "UE2013", 15: "UE2015", 20: "UE2020", 22: "UE2022"}
AC_MODELOS = {
    "AC URNA": {"UE2013", "UE2015"},
    "AC UE2020": {"UE2020"},
    "AC UE2022": {"UE2022"},
}
EXPLICACOES = {
    "preenchimento": "Valor de preenchimento (zeros), usado por arquivos do sistema de apuração e da votação recuperada",
    "sistema_apuracao": "Sistema de apuração: o equipamento da junta responde por várias seções",
    "red": "Votação recuperada (RED)",
    "agregada": "Seção agregada a outra",
    "mesma_urna": "A mesma urna responde pelas seções (troca, reserva ou contingência com horários compatíveis)",
    "contingencia": "Contingência, reserva ou recarga declarada no BU",
    "midia_compartilhada": "Mídia ou computador compartilhado dentro da zona ou da UF, como previsto",
    "mr_mesma_serie_na_zona": "Memórias de resultado com o mesmo número de série em várias urnas da mesma zona (candidata: lote de mídias com série de fábrica repetida; não confirmada pelo TSE)",
    "colisao_32_bits": "Coincidência de identificador de 4 bytes entre urnas diferentes, dentro do esperado ao acaso",
    "sem_explicacao": "Sem explicação pela regra",
}

CAMPOS = {
    # fonte, escopo, bits do identificador, valores de preenchimento, descrição
    "numero_interno_urna": ("BU", "urna", None, set(), "Número interno da urna"),
    "codigo_carga": ("BU", "urna", None, set(), "Código da carga"),
    "numero_serie_fv": (
        "BU",
        "urna",
        32,
        {"00000000"},
        "Número de série da flash de votação (FV)",
    ),
    "numero_serie_fc": (
        "BU",
        "compartilhado",
        32,
        {"00000000"},
        "Número de série da mídia de carga (FC)",
    ),
    "gerador_midia": (
        "BU",
        "compartilhado",
        None,
        set(),
        "Computador que gerou a mídia de carga (nome, TPM, instalação)",
    ),
    "versao_votacao": ("BU", "global", None, set(), "Versão do software de votação"),
    "bu_sha256": ("BU", "secao", None, set(), "SHA-256 do arquivo do BU"),
    "hash_transmissao": (
        "BU",
        "secao",
        None,
        set(),
        "Hash de transmissão (diretório do aux)",
    ),
    "vsc_sha256": (".vsc", "secao", None, set(), "SHA-256 do arquivo .vsc"),
    "hw_serial": (
        ".vsc",
        "urna",
        None,
        set(),
        "Série da urna na assinatura de hardware",
    ),
    "cert_sha256": (".vsc", "urna", None, set(), "SHA-256 do certificado de hardware"),
    "cert_chave_sha256": (
        ".vsc",
        "urna",
        None,
        set(),
        "SHA-256 da chave pública do certificado",
    ),
    "cert_serial_ac": (
        ".vsc",
        "urna",
        None,
        set(),
        "Número de série do certificado dentro da AC emissora",
    ),
    "sw_serial": (".vsc", "global", None, set(), "Chave de software do TSE (série)"),
    "sw_chave_data": (
        ".vsc",
        "global",
        None,
        set(),
        "Data da chave de software do TSE",
    ),
    "log_serie_mr_dia": (
        "log",
        "urna",
        32,
        set(),
        "Número de série da memória de resultado (MR) no log, no dia da eleição",
    ),
    "log_midia_votacao_computador": (
        "log",
        "compartilhado",
        None,
        set(),
        "Computador que gerou a mídia de votação, no log do dia",
    ),
    "log_midias": (
        "log",
        "compartilhado",
        32,
        set(),
        "Identificador da mídia de carga no log",
    ),
    "log_midia_computador": (
        "log",
        "compartilhado",
        None,
        set(),
        "Computador da mídia de carga no log",
    ),
    "log_versao": ("log", "global", None, set(), "Versão da aplicação no log"),
}


def pares(tamanhos) -> int:
    return int(sum(k * (k - 1) // 2 for k in tamanhos))


def _quantil_poisson(lam: float, q: float = 0.999) -> int:
    """Menor k com P(X <= k) >= q para X ~ Poisson(lam), por soma direta dos termos."""
    if lam <= 0:
        return 0
    k = 0
    termo = math.exp(-lam) if lam < 700 else 0.0
    if termo == 0.0:
        return math.ceil(lam + 3.0902 * math.sqrt(lam) + 1)
    acum = termo
    while acum < q:
        k += 1
        termo *= lam / k
        acum += termo
    return k


def colisoes_esperadas(n: int, bits: int) -> dict:
    """Pares de valores iguais esperados ao acaso entre n identificadores uniformes de `bits` bits."""
    esperado = n * (n - 1) / 2 / 2.0**bits
    return {
        "n": n,
        "bits": bits,
        "pares_esperados": round(esperado, 2),
        "limite_999": _quantil_poisson(esperado),
    }


def _lista_nsa(nsa) -> set[int]:
    if not isinstance(nsa, str) or not nsa.strip():
        return set()
    try:
        obj = json.loads(nsa)
    except ValueError:
        return set()
    return {int(x) for x in obj} if isinstance(obj, list) else set()


def _agregadas(linhas: list[dict]) -> bool:
    """Alguma seção do grupo é agregada a outra do mesmo grupo (pela nsp ou pela nsa)."""
    secoes = {(r["uf"], r["mun"], r["zona"], int(r["secao"])) for r in linhas}
    for r in linhas:
        base = (r["uf"], r["mun"], r["zona"])
        nsp = r.get("nsp")
        if (
            nsp is not None
            and not (isinstance(nsp, float) and math.isnan(nsp))
            and (*base, int(nsp)) in secoes
        ):
            return True
        if any(
            (*base, s) in secoes
            for s in _lista_nsa(r.get("nsa"))
            if s != int(r["secao"])
        ):
            return True
    return False


def classificar(linhas: list[dict], campo: str, colisao_aceitavel: bool) -> str:
    _, escopo, bits, preenchimento, _ = CAMPOS[campo]
    valor = str(linhas[0].get("_valor"))
    if valor in preenchimento:
        return "preenchimento"
    if escopo == "compartilhado":
        return _classificar_compartilhado(linhas, campo, bits, colisao_aceitavel)
    tipos = {r.get("tipo_arquivo") for r in linhas}
    if tipos & SISTEMA_APURACAO:
        return "sistema_apuracao"
    if 2 in tipos:
        return "red"
    if _agregadas(linhas):
        return "agregada"
    ids = {r.get("numero_interno_urna") for r in linhas}
    if escopo in ("urna", "secao"):
        if campo == "numero_interno_urna" or (len(ids) == 1 and escopo == "urna"):
            c = classificar_grupo(linhas)
            return "mesma_urna" if c["explicada"] else "sem_explicacao"
        if (
            any(
                (r.get("tipo_urna") in CONTINGENCIA) or (r.get("n_cargas") or 0) > 1
                for r in linhas
            )
            and len(ids) == 1
        ):
            return "contingencia"
        if (
            campo == "log_serie_mr_dia"
            and len({(r["uf"], r["zona"]) for r in linhas}) == 1
        ):
            return "mr_mesma_serie_na_zona"
        if bits and len(ids) == len(linhas) and colisao_aceitavel:
            return "colisao_32_bits"
        return "sem_explicacao"
    return "sem_explicacao"


def _classificar_compartilhado(
    linhas: list[dict], campo: str, bits: int | None, colisao_aceitavel: bool
) -> str:
    """Mídia de carga ou computador: repetir é a regra dentro da UF, com o mesmo computador."""
    uma_uf = len({r["uf"] for r in linhas}) == 1
    if campo in (
        "gerador_midia",
        "log_midia_computador",
        "log_midia_votacao_computador",
    ):
        return "midia_compartilhada" if uma_uf else "sem_explicacao"
    geradores = {r.get("gerador_midia") for r in linhas}
    municipios = {(r["uf"], r["mun"]) for r in linhas}
    # no log, a seção pode listar mídias de outras urnas (contingência, carga anterior):
    # o computador do BU não identifica o de cada mídia, então a regra é a UF
    if uma_uf and (
        campo == "log_midias" or len(geradores) == 1 or len(municipios) == 1
    ):
        return "midia_compartilhada"
    if bits and colisao_aceitavel:
        return "colisao_32_bits"
    return "sem_explicacao"


LINHA_PUBLICA = (
    "uf",
    "mun",
    "zona",
    "secao",
    "local",
    "numero_interno_urna",
    "modelo_urna",
    "tipo_urna",
    "tipo_arquivo",
    "n_cargas",
    "abertura",
    "encerramento",
    "gerador_midia",
    "fatia_flavio",
)


def _publica(r: dict) -> dict:
    out = {}
    for k in LINHA_PUBLICA:
        v = r.get(k)
        if isinstance(v, float) and math.isnan(v):
            v = None
        elif isinstance(v, (np.integer,)):
            v = int(v)
        elif isinstance(v, (np.floating,)):
            v = round(float(v), 3)
        out[k] = v
    return out


def repeticao(
    df: pd.DataFrame, campo: str, coluna: str | None = None, limite_casos: int = 200
) -> dict:
    """Valores que aparecem em mais de uma seção, por explicação candidata."""
    fonte, escopo, bits, preenchimento, descricao = CAMPOS[campo]
    coluna = coluna or campo
    base = {"campo": campo, "fonte": fonte, "escopo": escopo, "descricao": descricao}
    if coluna not in df or df[coluna].isna().all():
        return base | {"secoes_com_valor": 0, "situacao": "sem dados"}
    sub = df[df[coluna].notna()].copy()
    if sub[coluna].map(lambda v: isinstance(v, list)).any():
        sub = sub.explode(coluna)
        sub = sub[sub[coluna].notna()]
        sub = sub.drop_duplicates([*CHAVE, coluna])
    sub["_valor"] = sub[coluna].astype(str)
    tam = sub.groupby("_valor").size()
    out = base | {
        "secoes_com_valor": int(sub[CHAVE].drop_duplicates().shape[0]),
        "valores_distintos": int(tam.size),
    }
    if escopo == "global":
        out["valores"] = [
            {"valor": k, "secoes": int(v)}
            for k, v in tam.sort_values(ascending=False).head(20).items()
        ]
        out["coerente"] = int(tam.size) == 1
        return out
    rep = tam[tam > 1]
    colisao = None
    colisao_aceitavel = False
    if bits:
        validos = sub[~sub._valor.isin(preenchimento)]
        if escopo == "urna":
            # os pares observados são contados depois da classificação, só nos grupos que
            # nenhuma outra explicação cobre (ver abaixo)
            colisao = colisoes_esperadas(int(validos.shape[0]), bits)
            observados = 0
        else:
            # mídia compartilhada: cada par (valor, computador) é uma mídia; conta pares de
            # computadores diferentes com o mesmo valor
            chave_midia = "uf" if campo == "log_midias" else "gerador_midia"
            gm = (
                validos[chave_midia]
                if chave_midia in validos
                else pd.Series("", index=validos.index)
            )
            midias = validos.assign(_g=gm.fillna("")).drop_duplicates(["_valor", "_g"])
            colisao = colisoes_esperadas(int(midias.shape[0]), bits)
            observados = pares(midias.groupby("_valor").size())
        colisao["pares_observados"] = observados
        colisao_aceitavel = escopo == "urna" or observados <= colisao["limite_999"]
    grupos = []
    for valor, g in sub[sub._valor.isin(rep.index)].groupby("_valor"):
        linhas = g.to_dict("records")
        expl = classificar(linhas, campo, colisao_aceitavel)
        grupos.append(
            {
                "valor": valor,
                "secoes": len(linhas),
                "explicacao": expl,
                "geografia": geografia(linhas),
                "linhas": linhas,
            }
        )
    if colisao is not None:
        if escopo == "urna":
            candidatos = [g for g in grupos if g["explicacao"] == "colisao_32_bits"]
            colisao["pares_observados"] = pares(g["secoes"] for g in candidatos)
            colisao_aceitavel = colisao["pares_observados"] <= colisao["limite_999"]
            if not colisao_aceitavel:
                for g in candidatos:
                    g["explicacao"] = "sem_explicacao"
        colisao["dentro_do_esperado"] = colisao_aceitavel
    cont = Counter(g["explicacao"] for g in grupos)
    sec = Counter()
    for g in grupos:
        sec[g["explicacao"]] += g["secoes"]
    sem = [g for g in grupos if g["explicacao"] == "sem_explicacao"]
    out |= {
        "grupos_repetidos": len(grupos),
        "secoes_em_grupos": int(sum(g["secoes"] for g in grupos)),
        "maior_grupo": int(rep.max()) if rep.size else 0,
        "por_explicacao": {
            k: {"grupos": cont[k], "secoes": sec[k]} for k in EXPLICACOES if cont[k]
        },
        "por_geografia": dict(Counter(g["geografia"] for g in grupos)),
        "colisao_aleatoria": colisao,
        "sem_explicacao": {
            "grupos": len(sem),
            "secoes": int(sum(g["secoes"] for g in sem)),
            "casos": [
                {
                    "valor": g["valor"],
                    "secoes": g["secoes"],
                    "geografia": g["geografia"],
                    "linhas": [_publica(r) for r in g["linhas"]],
                }
                for g in sorted(sem, key=lambda g: -g["secoes"])[:limite_casos]
            ],
        },
        "_chaves_mr_zona": [
            tuple(r[c] for c in CHAVE)
            for g in grupos
            if g["explicacao"] == "mr_mesma_serie_na_zona"
            for r in g["linhas"]
        ],
        "_chaves_sem_explicacao": [
            tuple(r[c] for c in CHAVE) for g in sem for r in g["linhas"]
        ],
    }
    if escopo == "compartilhado":
        out["tamanho_dos_grupos"] = {
            "mediana": float(rep.median()) if rep.size else None,
            "p99": float(rep.quantile(0.99)) if rep.size else None,
        }
    return out


# ---------------------------------------------------------------- coerência
def _conta(serie: pd.Series) -> dict:
    s = serie.map(
        lambda v: (
            None if v is None or (isinstance(v, float) and math.isnan(v)) else bool(v)
        )
    )
    return {
        "sim": int(s.eq(True).sum()),
        "nao": int(s.eq(False).sum()),
        "sem_dado": int(s.isna().sum()),
    }


def _data_vsc(v: str | None) -> pd.Timestamp | None:
    if not isinstance(v, str) or len(v) < 15:
        return None
    return pd.Timestamp(f"{v[:4]}-{v[4:6]}-{v[6:8]} {v[9:11]}:{v[11:13]}:{v[13:15]}")


def coerencia_vsc(m: pd.DataFrame, dia: str) -> tuple[dict, dict[str, list]]:
    """Coerência entre BU e `.vsc` na mesma seção. `m` = BU com colunas do `.vsc` (ok)."""
    ok = m[m.status == "ok"].copy()
    urna = ok[ok.origem == "vota"]
    falhas: dict[str, list] = {}

    def marcar(nome: str, mascara: pd.Series) -> None:
        falhas[nome] = [
            tuple(r)
            for r in ok.loc[
                mascara.reindex(ok.index, fill_value=False), CHAVE
            ].itertuples(index=False)
        ]

    # votação recuperada (RED): o arquivo é gerado e assinado por outra urna, horas depois
    red = ok.tipo_arquivo == 2
    mesmo = (ok.mesmo_hash_bu == 1) & ~red
    id_igual = ok.hw_serial.astype(float) == ok.numero_interno_urna.astype(float)
    marcar("id_bu_diferente_da_serie_hw", mesmo & ~id_igual)
    mod = urna.modelo_codigo.map(MODELO_CODIGO)
    mod_dif = mod.notna() & urna.modelo_urna.notna() & (mod != urna.modelo_urna)
    marcar("modelo_vsc_diferente_do_bu", mod_dif)
    ac_ok = ok.apply(
        lambda r: MODELO_CODIGO.get(r.modelo_codigo) in AC_MODELOS.get(r.ac, set()),
        axis=1,
    )
    marcar("ac_incompativel_com_modelo", ~ac_ok & ok.ac.notna())
    for col in (
        "cadeia_valida",
        "hw_assinatura_ok",
        "hw_bu_assinatura_ok",
        "listas_ok",
        "hw_resumo_ok",
        "sw_resumo_ok",
        "cn_confere_usuario",
    ):
        marcar(f"{col}_falso", ok[col] == 0)
    marcar("bu_diferente_do_vsc", ok.bu_confere_vsc == 0)
    validade = (ok.cert_validade_inicio.str[:10] <= dia) & (
        ok.cert_validade_fim.str[:10] >= dia
    )
    marcar("certificado_fora_da_validade", ~validade & ok.cert_validade_inicio.notna())
    criado = ok.hw_criado_em.map(_data_vsc)
    emissao = pd.to_datetime(ok.emissao, errors="coerce")
    delta = (pd.to_datetime(criado) - emissao).dt.total_seconds() / 60
    marcar("vsc_antes_da_emissao_do_bu", mesmo & (ok.origem == "vota") & (delta < -1))
    marcar(
        "vsc_mais_de_4h_depois_da_emissao",
        mesmo & (ok.origem == "vota") & (delta > 240),
    )
    d = delta[mesmo & (ok.origem == "vota")].dropna()
    resumo = {
        "secoes_vsc_ok": len(ok),
        "origem": {str(k): int(v) for k, v in ok.origem.value_counts().items()},
        "mesmo_hash_do_bu": _conta(ok.mesmo_hash_bu),
        "votacao_recuperada_assinada_por_outra_urna": int(
            (
                red
                & (ok.hw_serial.astype(float) != ok.numero_interno_urna.astype(float))
            ).sum()
        ),
        "id_bu_igual_serie_hw": {
            "sim": int((mesmo & id_igual).sum()),
            "nao": int((mesmo & ~id_igual).sum()),
        },
        "cn_do_certificado_igual_serie_hw": _conta(ok.cn_confere_usuario),
        "modelo_vsc_igual_bu": {
            "sim": int((mod.notna() & ~mod_dif).sum()),
            "nao": int(mod_dif.sum()),
        },
        "ac_compativel_com_modelo": {
            "sim": int(ac_ok.sum()),
            "nao": int((~ac_ok & ok.ac.notna()).sum()),
        },
        "por_ac": {str(k): int(v) for k, v in ok.ac.value_counts().items()},
        "cadeia_ate_a_ac": _conta(ok.cadeia_valida),
        "autoassinatura_hw": _conta(ok.hw_assinatura_ok),
        "assinatura_hw_do_bu": _conta(ok.hw_bu_assinatura_ok),
        "bu_publicado_igual_ao_vsc": _conta(ok.bu_confere_vsc),
        "listas_sw_hw_iguais": _conta(ok.listas_ok),
        "certificado_valido_no_dia": {
            "sim": int(validade.sum()),
            "nao": int((~validade & ok.cert_validade_inicio.notna()).sum()),
        },
        "minutos_vsc_depois_da_emissao": {
            "n": int(d.size),
            "mediana": round(float(d.median()), 2) if d.size else None,
            "p99": round(float(d.quantile(0.99)), 2) if d.size else None,
            "min": round(float(d.min()), 2) if d.size else None,
            "max": round(float(d.max()), 2) if d.size else None,
        },
        "falhas": {k: len(v) for k, v in falhas.items()},
    }
    return resumo, falhas


def entre_turnos_vsc(
    v1: pd.DataFrame, v2: pd.DataFrame, b1: pd.DataFrame, b2: pd.DataFrame
) -> tuple[dict, dict[str, list]]:
    """Mesma seção nos dois turnos: certificado e número da urna andam juntos?"""
    cols = [*CHAVE, "hw_serial", "cert_sha256"]
    a = v1[(v1.status == "ok") & (v1.origem == "vota")][cols]
    b = v2[(v2.status == "ok") & (v2.origem == "vota")][cols]
    m = a.merge(b, on=CHAVE, suffixes=("_1t", "_2t"))
    mesmo_id = m.hw_serial_1t == m.hw_serial_2t
    mesmo_cert = m.cert_sha256_1t == m.cert_sha256_2t
    falhas = {
        "mesma_urna_certificado_diferente": [
            tuple(r)
            for r in m.loc[mesmo_id & ~mesmo_cert, CHAVE].itertuples(index=False)
        ],
        "urna_diferente_mesmo_certificado": [
            tuple(r)
            for r in m.loc[~mesmo_id & mesmo_cert, CHAVE].itertuples(index=False)
        ],
    }
    # carga: a urna religada no 2º turno mantém o código de carga do 1º?
    campos_carga = [
        *CHAVE,
        "numero_interno_urna",
        "codigo_carga",
        "n_cargas",
        "carga_em",
    ]
    cc = b1[campos_carga].merge(b2[campos_carga], on=CHAVE, suffixes=("_1t", "_2t"))
    mesma = cc.numero_interno_urna_1t == cc.numero_interno_urna_2t
    carga_igual = cc.codigo_carga_1t == cc.codigo_carga_2t
    nova = cc[mesma & ~carga_igual]
    dia_nova = nova.carga_em_2t.str[:10]
    entre = (dia_nova > "2026-10-04") & (dia_nova < "2026-10-25")
    # o certificado do 1º turno reaparece em outra seção no 2º?
    c1 = a.set_index("cert_sha256")
    outra = b.merge(
        c1[CHAVE].add_suffix("_1t"),
        left_on="cert_sha256",
        right_index=True,
        how="inner",
    )
    outra = outra[
        (outra.uf != outra.uf_1t)
        | (outra.mun != outra.mun_1t)
        | (outra.zona != outra.zona_1t)
        | (outra.secao != outra.secao_1t)
    ]
    return {
        "secoes_com_vsc_nos_dois_turnos": len(m),
        "mesma_urna_mesmo_certificado": int((mesmo_id & mesmo_cert).sum()),
        "urna_trocada_certificado_trocado": int((~mesmo_id & ~mesmo_cert).sum()),
        "mesma_urna_certificado_diferente": len(
            falhas["mesma_urna_certificado_diferente"]
        ),
        "urna_diferente_mesmo_certificado": len(
            falhas["urna_diferente_mesmo_certificado"]
        ),
        "certificado_do_1t_em_outra_secao_no_2t": len(outra),
        "certificado_do_1t_em_outra_secao_no_2t_casos": [
            {
                "secao_2t": "/".join(str(r[c]) for c in CHAVE),
                "secao_1t": "/".join(str(r[f"{c}_1t"]) for c in CHAVE),
                "serie_hw": r["hw_serial"],
            }
            for r in outra.head(100).to_dict("records")
        ],
        "carga": {
            "secoes_nos_dois_turnos": len(cc),
            "mesma_urna_mesma_carga": int((mesma & carga_igual).sum()),
            "mesma_urna_carga_nova": int((mesma & ~carga_igual).sum()),
            "urna_trocada": int((~mesma).sum()),
            "urna_trocada_mesma_carga": int((~mesma & carga_igual).sum()),
            "carga_nova_entre_os_turnos": int(entre.sum()),
            "carga_nova_fora_do_intervalo": int((~entre).sum()),
            "carga_nova_por_dia": {
                str(k): int(v) for k, v in dia_nova.value_counts().sort_index().items()
            },
        },
    }, falhas | {
        "mesma_urna_carga_nova": [
            tuple(r)
            for r in cc.loc[mesma & ~carga_igual, CHAVE].itertuples(index=False)
        ],
        "urna_trocada_mesma_carga": [
            tuple(r)
            for r in cc.loc[~mesma & carga_igual, CHAVE].itertuples(index=False)
        ],
    }


def _nome_maquina(x) -> str:
    """Nome do computador: o BU guarda `nome|tpm|instalação`, o log `nome - tpm - instalação`."""
    return str(x).replace("|", " - ").split(" - ")[0].strip().upper()


def _versao(x) -> str:
    return str(x).split(" ")[0].strip()


def coerencia_logs(m: pd.DataFrame) -> tuple[dict, dict[str, list]]:
    """BU contra o log processado do 2º turno, campo a campo; nulo quando o log não tem o campo."""
    if "log_status" not in m or m.log_status.isna().all():
        return {"situacao": "logs do 2º turno ainda não processados"}, {}
    t = m[m.log_status.notna()].copy()
    falhas: dict[str, list] = {}
    out: dict = {"secoes_com_log": len(t)}

    def teste(nome: str, tem: pd.Series, passa: pd.Series) -> None:
        out[nome] = {
            "cobertas": int(tem.sum()),
            "confere": int((tem & passa).sum()),
            "nao_confere": int((tem & ~passa).sum()),
        }
        falhas[nome] = [
            tuple(r) for r in t.loc[tem & ~passa, CHAVE].itertuples(index=False)
        ]

    def contem(lista, valor, norm=str) -> bool:
        return (
            isinstance(lista, list)
            and valor is not None
            and norm(valor) in {norm(x) for x in lista}
        )

    tem_u = t.log_ids.map(lambda v: isinstance(v, list) and len(v) > 0)
    teste(
        "id_do_bu_no_log",
        tem_u,
        t.apply(
            lambda r: contem(r.log_ids, r.numero_interno_urna, lambda x: str(int(x))),
            axis=1,
        ),
    )
    tem_c = t.log_cargas.map(lambda v: isinstance(v, list) and len(v) > 0)
    teste(
        "carga_do_bu_no_log",
        tem_c,
        t.apply(lambda r: contem(r.log_cargas, r.codigo_carga), axis=1),
    )
    tem_m = t.log_midias.map(lambda v: isinstance(v, list) and len(v) > 0)
    teste(
        "midia_fc_do_bu_no_log",
        tem_m,
        t.apply(
            lambda r: contem(r.log_midias, r.numero_serie_fc, lambda x: str(x).upper()),
            axis=1,
        ),
    )
    tem_g = t.log_midia_computador.map(lambda v: isinstance(v, list) and len(v) > 0)
    teste(
        "computador_da_midia_no_log",
        tem_g,
        t.apply(
            lambda r: contem(r.log_midia_computador, r.gerador_midia, _nome_maquina),
            axis=1,
        ),
    )
    tem_v = t.log_versao.map(lambda v: isinstance(v, list) and len(v) > 0)
    teste(
        "versao_do_bu_no_log",
        tem_v,
        t.apply(lambda r: contem(r.log_versao, r.versao_votacao, _versao), axis=1),
    )
    _carga_e_reinicios(t, out, falhas)
    return out, falhas


def _data_log(v) -> pd.Timestamp | None:
    """Data do log (dd/mm/aaaa hh:mm:ss) como Timestamp; None se ausente ou malformada."""
    if not isinstance(v, str) or len(v) < 19:
        return None
    try:
        return pd.Timestamp(f"{v[6:10]}-{v[3:5]}-{v[:2]} {v[11:19]}")
    except ValueError:
        return None


def _bool_ou_nulo(v) -> bool | None:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    return bool(v)


def _carga_e_reinicios(t: pd.DataFrame, out: dict, falhas: dict[str, list]) -> None:
    """Carga registrada no log da urna do BU contra a abertura; reinícios na votação;
    identidade conferida pelo próprio processamento dos logs."""

    def chaves(mascara: pd.Series) -> list:
        return [tuple(r) for r in t.loc[mascara, CHAVE].itertuples(index=False)]

    def carga_da_urna(r) -> pd.Timestamp | None:
        mapa = r.log_carga_por_urna if isinstance(r.log_carga_por_urna, dict) else {}
        urna = r.numero_interno_urna
        if urna is None or (isinstance(urna, float) and math.isnan(urna)):
            return None
        return _data_log(mapa.get(int(urna)))

    carga = pd.to_datetime(t.apply(carga_da_urna, axis=1), errors="coerce")
    abertura = pd.to_datetime(t.abertura, errors="coerce")
    tem = carga.notna() & abertura.notna()
    depois_log = tem & (carga > abertura)
    # o BU guarda a própria data de carga; quando ela é anterior à abertura, a data do log
    # depois da abertura aponta para o relógio da urna, não para uma carga no dia
    bu_carga = pd.to_datetime(t.carga_em, errors="coerce")
    depois = depois_log & ~(bu_carga < abertura)
    no_dia = carga.dt.strftime("%Y-%m-%d").eq("2026-10-25")
    out["carga_registrada_vs_abertura"] = {
        "cobertas": int(tem.sum()),
        "carga_antes_da_abertura": int((tem & ~depois).sum()),
        "carga_depois_da_abertura_no_log": int(depois_log.sum()),
        "das_quais_bu_registra_carga_antes": int((depois_log & ~depois).sum()),
        "carga_depois_da_abertura": int(depois.sum()),
        "carga_no_dia_da_eleicao": int(no_dia.sum()),
        "carga_por_mes": {
            str(k): int(v)
            for k, v in carga.dt.strftime("%Y-%m").value_counts().sort_index().items()
        },
    }
    falhas["carga_registrada_depois_da_abertura"] = chaves(depois)
    falhas["data_de_carga_do_log_diverge_do_bu"] = chaves(depois_log & ~depois)
    rein = pd.to_numeric(t.log_reinicios_votacao, errors="coerce")
    out["reinicios_durante_votacao"] = {
        "cobertas": int(rein.notna().sum()),
        "secoes_com_reinicio": int((rein > 0).sum()),
        "distribuicao": {
            str(int(k)): int(v)
            for k, v in rein.dropna().value_counts().sort_index().items()
        },
    }
    falhas["reinicio_durante_votacao"] = chaves(rein > 0)
    part = pd.to_numeric(t.log_partidas_vota, errors="coerce")
    out["partidas_do_vota_no_dia"] = {
        str(int(k)): int(v)
        for k, v in part.dropna().value_counts().sort_index().items()
    }
    for col, nome in (
        ("log_urna_bu_no_log", "urna_do_bu_no_log_pelo_processamento"),
        ("log_carga_bu_no_log", "carga_do_bu_no_log_pelo_processamento"),
    ):
        v = t[col].map(_bool_ou_nulo)
        out[nome] = {
            "sim": int(v.eq(True).sum()),
            "nao": int(v.eq(False).sum()),
            "sem_dado": int(v.isna().sum()),
        }
        falhas[nome.replace("_no_log_pelo_processamento", "_ausente_do_log")] = chaves(
            v.eq(False)
        )
    outras = pd.to_numeric(t.log_outras_urnas, errors="coerce")
    out["secoes_com_outra_urna_no_log"] = int((outras > 0).sum())


# ---------------------------------------------------------------- voto
def cruzar_voto(t2: pd.DataFrame, t1: pd.DataFrame, chaves: list, rotulo: str) -> dict:
    """Fatia de Flávio nas seções marcadas contra as vizinhas do município (2º turno) e a
    diferença em diferenças contra o 1º turno, com n."""
    marcadas = set(chaves)
    if not marcadas:
        return {"grupo": rotulo, "n": 0}
    idx = pd.MultiIndex.from_frame(t2[CHAVE])
    marca = pd.Series(idx.isin(list(marcadas)), index=t2.index)
    ex2 = excesso_vizinhas(t2, marca, "fatia_flavio")
    j = t2[[*CHAVE, "fatia_flavio", "validos_fl"]].merge(
        t1[[*CHAVE, "fatia_flavio"]], on=CHAVE, suffixes=("", "_1t"), how="left"
    )
    j["delta"] = j.fatia_flavio - j.fatia_flavio_1t
    marca_j = pd.Series(
        pd.MultiIndex.from_frame(j[CHAVE]).isin(list(marcadas)), index=j.index
    )
    exd = excesso_vizinhas(j, marca_j, "delta")
    return {
        "grupo": rotulo,
        "n": int(marca.sum()),
        "fatia_flavio_2t_menos_vizinhas_do_municipio": _media_ic(ex2),
        "dif_em_dif_contra_1t": _media_ic(exd),
    }
