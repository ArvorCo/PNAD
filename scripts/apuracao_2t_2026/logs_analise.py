"""Contas do capítulo ``logs`` do dossiê do 2º turno: cobertura, regra 2, persistência,
metadados e o escore integrado BU × log. A cadência fica em ``logs_cadencia`` e os
reinícios e a bateria em ``logs_reinicio``.

Rótulo fixo: pede explicação, não prova irregularidade.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from functools import cache

import numpy as np
import pandas as pd
from apuracao_logs.criterios import CRITERIOS
from apuracao_logs.familias import FAMILIAS, NOME_CURTO

from . import logs_cadencia as C
from . import logs_rdv
from . import logs_reinicio as R
from .logs_base import CHAVE, LOGS_2T, ROOT, ROTULO, carregar

POLITIZE = ROOT / "docs/assets/politize/dados"
BITS_SERIE = 32


def cobertura(t2: pd.DataFrame, resumo: dict) -> dict:
    nao = t2[~t2["contagem_confere"]]
    bio = t2[~t2["biometria_confere"]]
    lista = []
    for r in nao.itertuples():
        motivo = []
        if r.tipo_urna in R.CONTINGENCIA or r.outras_urnas:
            motivo.append("urna de contingência ou mais de uma urna no pacote")
        if r.reinicios_sist:
            motivo.append(
                f"sistema religado {r.reinicios_sist} vez(es) durante a votação"
            )
        if not r.relogio_ok:
            motivo.append("relógio inconsistente")
        lista.append(
            {
                "uf": r.uf,
                "mun": r.mun,
                "zona": int(r.zona),
                "secao": int(r.secao),
                "computados_log": int(r.computados),
                "comparecimento_bu": int(r.bu_comp),
                "diferenca": int(r.dif_computados),
                "tipo_urna": int(r.tipo_urna),
                "n_cargas": int(r.n_cargas),
                "urnas_no_log": int(r.n_urnas_log),
                "reinicios_sistema": int(r.reinicios_sist),
                "explicacao_possivel": "; ".join(motivo) or "sem explicação no pacote",
            }
        )
    versoes = t2["versoes"].value_counts()
    return {
        "lidos": len(t2),
        "catalogadas": resumo["cobertura"]["catalogadas"],
        "situacoes": {
            k: v["secoes"] for k, v in resumo["situacoes"].items() if v["secoes"]
        },
        "contagem_confere": int(t2["contagem_confere"].sum()),
        "contagem_nao_confere": lista,
        "log_menor_que_bu_em_todas": bool((nao["dif_computados"] < 0).all()),
        "biometria_confere": int(t2["biometria_confere"].sum()),
        "biometria_nao_conferida": len(bio),
        "biometria_ausente_bu": int(bio["bio_ausente_bu"].sum()),
        "biometria_ausente_bu_exterior": int(
            (bio["bio_ausente_bu"] & (bio["uf"] == "ZZ")).sum()
        ),
        "biometria_por_contagem": int(
            (~bio["bio_ausente_bu"] & ~bio["contagem_confere"]).sum()
        ),
        "versoes": {k: int(v) for k, v in versoes.items()},
        "urna_bu_no_log": int(t2["urna_bu_no_log"].fillna(False).astype(bool).sum()),
        "carga_bu_no_log": int(t2["carga_bu_no_log"].fillna(False).astype(bool).sum()),
        "processo_elegivel": resumo["cobertura"]["processo_elegivel"],
        "coleta_hash_anterior_confere": resumo["coleta"]["hash_anterior_confere"],
    }


def regra2(t2: pd.DataFrame, t1: pd.DataFrame, comp: dict) -> dict:
    com = t2["erros"] > 0
    so_mr = com & (t2["erros"] == t2["erro_mr_pre"])
    resto = t2[com & ~so_mr].copy()
    resto["mr_pos"] = resto["erro_mr"] - resto["erro_mr_pre"]
    resto["outros_sem_mr"] = (resto["ecat_outros"] - resto["erro_mr"]).clip(lower=0)
    reinicio = resto["reinicios_sist"] + resto["reinicios_vota"] > 0
    tipos = [
        (
            "memória de resultado depois da zerésima, com reinício na votação",
            (resto["mr_pos"] > 0) & reinicio,
        ),
        (
            "memória de resultado depois da zerésima, sem reinício na votação",
            (resto["mr_pos"] > 0) & ~reinicio,
        ),
        ("outras mensagens sem categoria própria", resto["outros_sem_mr"] > 0),
        ("impressora", resto["ecat_impress"] > 0),
        ("mídia", resto["ecat_mídia"] > 0),
        ("biometria (leitor)", resto["ecat_biometr"] > 0),
        ("assinatura", resto["ecat_assinatura"] > 0),
        ("demais categorias", resto["ecat_resto"] > 0),
    ]
    sem_mr = (resto["outros_sem_mr"] > 0) | (
        resto[
            [
                "ecat_impress",
                "ecat_mídia",
                "ecat_biometr",
                "ecat_assinatura",
                "ecat_resto",
            ]
        ].sum(axis=1)
        > 0
    )
    crit = comp["comparacao"]["por_criterio"]["erro_tecnico"]
    return {
        "secoes_com_erro": int(com.sum()),
        "so_mr_antes_da_zeresima": int(so_mr.sum()),
        "com_mr_antes_da_zeresima": int((t2["erro_mr_pre"] > 0).sum()),
        "erro_tecnico_regra2": len(resto),
        "na_janela_da_votacao": int((resto["erros_janela"] > 0).sum()),
        "com_mensagem_alheia_a_mr": int(sem_mr.sum()),
        "so_mr_depois_da_zeresima": int((~sem_mr).sum()),
        "por_tipo": [{"tipo": n, "secoes": int(m.sum())} for n, m in tipos],
        "primeiro_turno_secoes_com_erro": int((t1["erros1"] > 0).sum()),
        "criterio_1t": int(crit.get("so_1t", 0) + crit.get("ambos", 0)),
        "criterio_2t": int(crit.get("so_2t", 0) + crit.get("ambos", 0)),
        "criterio_ambos": int(crit.get("ambos", 0)),
        "mudanca": comp_mudanca(),
    }


@cache
def comp_mudanca() -> dict:
    r = json.loads((LOGS_2T / "resumo.json").read_text(encoding="utf-8"))
    return (r.get("mudancas_regras") or [{}])[0]


def persistencia(comp: dict) -> dict:
    c = comp["comparacao"]
    diag = []
    for k, v in c["por_criterio"].items():
        ambos, s1, s2 = v.get("ambos", 0), v.get("so_1t", 0), v.get("so_2t", 0)
        tot1, tot2 = ambos + s1, ambos + s2
        diag.append(
            {
                "criterio": k,
                "nome": v["nome"],
                "curto": NOME_CURTO.get(k, v["nome"]),
                "familia": next(
                    (f for f, s in FAMILIAS.items() if k in s["criterios"]), None
                ),
                "ambos": ambos,
                "so_1t": s1,
                "so_2t": s2,
                "total_1t": tot1,
                "total_2t": tot2,
                "pct_persiste": round(100 * ambos / tot1, 2) if tot1 else None,
            }
        )
    diag.sort(key=lambda x: -(x["total_1t"] + x["total_2t"]))
    zeros = [k for k in CRITERIOS if k not in c["por_criterio"]]
    return {
        "matriz": c["atencao_1t_x_2t"],
        "persistencia": c["persistencia"],
        "nos_dois": c["secoes_nos_dois"],
        "diagnosticos": diag,
        "sem_ocorrencia_nos_dois": zeros,
        "familias": c["por_familia"],
    }


def _data(s: str) -> pd.Timestamp | None:
    if not s:
        return None
    return max(pd.to_datetime(x, format="%d/%m/%Y %H:%M:%S") for x in s.split("|"))


def metadados(
    t2: pd.DataFrame, bu: pd.DataFrame, off: pd.DataFrame, ext: pd.DataFrame
) -> dict:
    grupos: dict[str, list[int]] = defaultdict(list)
    for i, sr in enumerate(t2["series_mr_dia"]):
        for v in sr.split("|"):
            if v:
                grupos[v].append(i)
    valores = len(grupos)
    rep = {v: ix for v, ix in grupos.items() if len(ix) > 1}
    estruturais, pares = [], []
    marca = np.zeros(len(t2), bool)
    for v, ix in sorted(rep.items(), key=lambda kv: -len(kv[1])):
        s = t2.iloc[ix]
        mesma_zona = s[["uf", "zona"]].drop_duplicates().shape[0] == 1
        item = {
            "serie": v,
            "secoes": len(ix),
            "ufs": sorted(s["uf"].unique().tolist()),
            "zonas": sorted(
                {f"{a}-{b}" for a, b in zip(s["uf"], s["zona"], strict=True)}
            )[:6],
            "municipios": int(s["mun"].nunique()),
            "so_esse_valor_no_log_todo": int((s["series_mr"] == v).sum()),
            "contagem_confere": int(s["contagem_confere"].sum()),
            "tipo_arquivo_urna": int((s["tipo_arquivo"] == 1).sum()),
            "contingencia": int(s["tipo_urna"].isin(R.CONTINGENCIA).sum()),
            "exemplos": [
                f"{a}-{z}-{x}"
                for a, z, x in zip(s["uf"], s["zona"], s["secao"], strict=True)
            ][:8],
        }
        # mesma definição do capítulo de metadados (metadados_regras.classificar): grupo
        # inteiro numa só UF e zona, sem BU de votação recuperada nem do sistema de apuração
        red_ou_apuracao = bool((s["tipo_arquivo"].fillna(1) != 1).any())
        if mesma_zona and not red_ou_apuracao:
            estruturais.append(item)
            marca[ix] = True
        else:
            pares.append(item)
    esperado = valores * (valores - 1) / 2 / 2**BITS_SERIE
    base = t2[CHAVE].merge(
        bu[[*CHAVE, "fatia_f", "fatia_f1", "fl", "lu"]], on=CHAVE, how="left"
    )
    nacional = ~t2["uf"].eq("ZZ").to_numpy()
    voto_estr = R.comparar_voto(
        base[nacional].reset_index(drop=True), pd.Series(marca[nacional])
    )
    por_grupo, chaves_ext = [], set()
    for item in estruturais:
        m = t2["series_mr_dia"].str.contains(item["serie"], regex=False).to_numpy()
        if item["ufs"] == ["ZZ"]:
            chaves_ext |= set(t2.loc[m, CHAVE].itertuples(index=False, name=None))
            continue
        por_grupo.append(
            {
                "serie": item["serie"],
                "zona": item["zonas"][0],
                **R.comparar_voto(
                    base[nacional].reset_index(drop=True), pd.Series(m[nacional])
                ),
            }
        )
    marca_ext = pd.Series(
        [k in chaves_ext for k in ext[CHAVE].itertuples(index=False, name=None)]
    )
    exterior = {
        "secoes_marcadas": len(chaves_ext),
        "nota": (
            "Exterior separado: a vizinhança é a cidade do consulado e, nos grupos do exterior, "
            "quase todas as seções da cidade têm a mesma série, sobrando poucas vizinhas; o 1º "
            "turno por seção vem do BU do metadados (secoes.json não cobre o exterior)."
        ),
        "regra_5_vizinhas": R.comparar_voto(ext, marca_ext, 5),
        "regra_3_vizinhas": R.comparar_voto(ext, marca_ext, 3),
    }
    cargas = t2["cargas_em"].map(_data)
    dia = pd.Timestamp("2026-10-25")
    depois = t2[cargas >= dia].assign(carga=cargas[cargas >= dia])
    x = t2.merge(off, on=["uf", "mun"], how="inner")
    x = x[x["uf"] != "ZZ"]
    zer = x["zeresima_s"] / 3600 + x["off"]
    pri = x["primeiro_s"] / 3600 + x["off"]
    return {
        "serie_mr": {
            "valores_distintos": valores,
            "repetidos": len(rep),
            "secoes_em_repeticao": int(sum(len(v) for v in rep.values())),
            "estruturais": estruturais,
            "pares_entre_lugares": len(pares),
            "pares_esperados_por_acaso_32_bits": round(esperado, 1),
            "pares_exemplos": pares[:6],
            "secoes_sem_serie_no_dia": int((t2["series_mr_dia"] == "").sum()),
            "voto_estruturais_brasil": voto_estr,
            "voto_por_grupo": por_grupo,
            "voto_exterior": exterior,
            "regra_voto": (
                "vizinhas do mesmo município (5 ou mais sem o sinal), média ponderada pelos votos "
                "dos dois finalistas na seção com sinal, exterior separado; a média simples por "
                "seção fica em sem_peso"
            ),
        },
        "cargas": {
            "antes_do_1t": int((cargas < pd.Timestamp("2026-10-04")).sum()),
            "entre_turnos": int(
                ((cargas >= pd.Timestamp("2026-10-05")) & (cargas < dia)).sum()
            ),
            "no_dia_ou_depois": [
                {
                    "uf": r.uf,
                    "zona": int(r.zona),
                    "secao": int(r.secao),
                    "carga_registrada": r.carga.strftime("%d/%m %H:%M"),
                    "tipo_urna": int(r.tipo_urna),
                    "contagem_confere": bool(r.contagem_confere),
                }
                for r in depois.itertuples()
            ],
            "por_dia": {
                k.strftime("%Y-%m-%d"): int(v)
                for k, v in cargas.dt.normalize().value_counts().sort_index().items()
            },
        },
        "zeresima_brt": {
            "antes_das_7": int((zer < 7).sum()),
            "7_as_8": int(((zer >= 7) & (zer < 8)).sum()),
            "depois_das_8": int((zer >= 8).sum()),
            "sem_zeresima": int(zer.isna().sum()),
        },
        "primeiro_voto_brt": {
            "antes_das_8": int((pri < 8).sum()),
            "8_as_9": int(((pri >= 8) & (pri < 9)).sum()),
            "depois_das_9": int((pri >= 9).sum()),
        },
        "versao_unica": t2["versoes"].nunique() == 1,
    }


@cache
def _mun(uf: str, mun: str) -> dict:
    arq = POLITIZE / "mun" / uf / f"{mun}.json"
    return json.loads(arq.read_text(encoding="utf-8")) if arq.exists() else {}


def _nome_mun(uf: str, mun: str) -> str | None:
    return _mun(uf, mun).get("nome")


@cache
def _locais(uf: str, mun: str) -> dict:
    m = _mun(uf, mun)
    if not m:
        return {}
    d = m["locais"]
    col = {c: i for i, c in enumerate(d["colunas"])}
    return {
        ln[col["local_id"]]: (ln[col["lat"]], ln[col["lon"]], ln[col["nome"]])
        for ln in d["linhas"]
    }


@cache
def _zona(uf: str, zona: int) -> dict:
    arq = POLITIZE / "zona" / uf / f"{zona}.json"
    if not arq.exists():
        return {}
    d = json.loads(arq.read_text(encoding="utf-8"))
    s = d["secoes"]
    col = {c: i for i, c in enumerate(s["colunas"])}
    return {
        int(ln[col["secao"]]): (ln[col["local_id"]], ln[col["mun_tse"]])
        for ln in s["linhas"]
    }


def _coord(uf: str, zona: int, secao: int) -> tuple:
    z = _zona(uf, zona).get(secao)
    if not z:
        return (None, None, None)
    return _locais(uf, z[1]).get(z[0], (None, None, None))


def integrado(t2, bu, s2) -> dict:
    j = bu.merge(s2[[*CHAVE, "sinais", "atencao"]], on=CHAVE, how="inner").merge(
        t2[[*CHAVE, "reinicios_sist", "bateria_votacao", "contagem_confere"]],
        on=CHAVE,
        how="left",
    )
    alvo = j[(j["escore"] >= 2) & (j["atencao"] >= 2)].copy()
    alvo = alvo.sort_values(["escore", "atencao", "magnitude"], ascending=False)
    ufz = j[j["uf"] != "ZZ"]
    out = {
        "bu_escore_2_mais": int((j["escore"] >= 2).sum()),
        "log_atencao_2_mais": int((j["atencao"] >= 2).sum()),
        "as_duas": len(alvo),
        "esperado_se_independentes": round(
            float(
                (ufz["escore"] >= 2).mean() * (ufz["atencao"] >= 2).mean() * len(ufz)
            ),
            1,
        ),
        "regra": "escore do BU (secoes.json, 0 a 6) ≥ 2 e atenção dos logs do 2º turno (0 a 3) ≥ 2; ordem: escore, atenção, magnitude",
    }
    linhas = []
    for r in alvo.itertuples():
        lat, lon, local = _coord(r.uf, int(r.zona), int(r.secao))
        fam = sorted({NOME_CURTO.get(c, c) for c in (r.sinais or "").split("|") if c})
        sinais_bu = [
            n
            for n, f in (
                ("comparecimento", r.sinal_delta),
                ("sem biometria", r.sinal_sem_bio),
                ("ano de nascimento", r.sinal_ano_nasc),
                ("salto da biometria", r.sinal_salto_bio),
                ("encerramento tardio", r.sinal_tardia),
                ("BU de apuração", r.sinal_papel),
            )
            if bool(f)
        ]
        linhas.append(
            {
                "uf": r.uf,
                "mun": r.mun,
                "municipio": _nome_mun(r.uf, r.mun),
                "zona": int(r.zona),
                "secao": int(r.secao),
                "local": local,
                "lat": lat,
                "lon": lon,
                "escore_bu": int(r.escore),
                "magnitude": round(float(r.magnitude), 2),
                "atencao_log": int(r.atencao),
                "sinais_bu": sinais_bu,
                "diagnosticos_log": fam,
                "delta_comp_pp": (
                    None if pd.isna(r.delta_pp) else round(float(r.delta_pp), 2)
                ),
                "fatia_f": None if pd.isna(r.fatia_f) else round(float(r.fatia_f), 2),
                "fatia_f1": (
                    None if pd.isna(r.fatia_f1) else round(float(r.fatia_f1), 2)
                ),
                "reinicio": bool(r.reinicios_sist and r.reinicios_sist > 0),
                "politizese": f"politizese.html#uf={r.uf}&z={int(r.zona)}&s={int(r.secao)}",
            }
        )
    out["secoes"] = linhas
    base = j[[*CHAVE, "fatia_f", "fatia_f1", "fl", "lu"]].reset_index(drop=True)
    m = ((j["escore"] >= 2) & (j["atencao"] >= 2)).reset_index(drop=True)
    out["voto"] = R.comparar_voto(base, m)
    return out


def montar(refazer: bool = False) -> dict:
    d = carregar(refazer)
    t2, t1, s1, s2, bu, a1 = d["t2"], d["t1"], d["s1"], d["s2"], d["bu"], d["a1"]
    resumo = json.loads((LOGS_2T / "resumo.json").read_text(encoding="utf-8"))
    comp = json.loads((LOGS_2T / "comparacao_turnos.json").read_text(encoding="utf-8"))
    off = C.deslocamentos(t2)
    meta_dossie = ROOT / "analysis/apuracao_2t_2026/dados/metadados.json"
    out = {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "rotulo": ROTULO,
        "fontes": {
            "metricas_2t": "data/outputs/logs_urnas_2t_2026.sqlite",
            "metricas_1t": "data/outputs/logs_urnas_2026.sqlite",
            "publico_2t": "docs/assets/logs_urnas_2t_2026/",
            "publico_1t": "docs/assets/logs_urnas_2026/",
            "comparacao": "analysis/apuracao_2t_2026/logs_urnas/comparacao_turnos.json",
            "bu": "analysis/apuracao_2t_2026/dados/secoes.json",
            "versao_parser": resumo["versao_parser"],
            "versao_regras": resumo["versao_regras"],
            "resumo_gerado_em": resumo["gerado_em"],
        },
        "cobertura": cobertura(t2, resumo),
        "regra2": regra2(t2, t1, comp),
        "persistencia": persistencia(comp),
        "cadencia": C.analisar(t2, a1, bu, s2),
        "reinicios": R.reinicios(t2, s1, s2, bu, off),
        "bateria": R.bateria(t2, s1, s2, bu),
        "metadados": metadados(t2, bu, off, d["ext"]),
        "integrado": integrado(t2, bu, s2),
        "rdv": logs_rdv.resumo(),
    }
    if meta_dossie.exists():
        m = json.loads(meta_dossie.read_text(encoding="utf-8"))
        out["metadados"]["dossie_metadados"] = {
            "gerado_em": m.get("gerado_em"),
            "estado": m.get("estado"),
            "coerencia_logs": m.get("coerencia_logs"),
        }
    return out
