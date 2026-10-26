"""Tabela por seção, por prédio e por município, 1º × 2º turno, para uma UF.

Seção principal é a chave (UF, zona, seção). Seções agregadas resolvem para a principal
de cada turno; quando a agregação muda entre os turnos, a linha diz que a comparação é
aproximada. Os sinais do 2º turno são os seis da régua do dossiê
(``apuracao_2t_2026.secoes_sinais``), calculados aqui com a mesma função, e a explicação
provável vem de ``apuracao_2t_2026.secoes_ranking.explicar``.
"""

from __future__ import annotations

import math
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2t_2026 import secoes_fonte, secoes_ranking, secoes_sinais
from apuracao_logs import familias

from . import fontes, tempo, textos, urna

DIA_1T = "2026-10-04"
DIA_2T = "2026-10-25"
MIN_APTOS = 30
TIPOS_CONTINGENCIA = frozenset({3, 4, 6})
SINAIS = list(secoes_sinais.SINAIS)
CHAVES_EXPLICACAO = [k for k, _ in secoes_ranking.REGRAS_EXPLICACAO]
TEXTO_EXPLICACAO = dict(secoes_ranking.REGRAS_EXPLICACAO)


@dataclass
class Contexto:
    ref: pd.DataFrame
    mun_ref: dict[str, Any]
    med_mun: pd.DataFrame
    med_zona: pd.DataFrame
    mapa_urnas: dict[int, tuple[str, str, int, int]]
    previsao: dict[str, dict[str, Any]]
    catalogo: dict[str, Any]
    observado: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class ResultadoUF:
    uf: str
    secoes: dict[int, list[dict[str, Any]]] = field(default_factory=dict)
    locais: dict[str, dict[str, Any]] = field(default_factory=dict)
    municipios: dict[str, dict[str, Any]] = field(default_factory=dict)
    nomes_mun: dict[str, str] = field(default_factory=dict)
    totais: dict[str, Any] = field(default_factory=dict)


def pct(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b <= 0:
        return None
    return round(100 * a / b, 1)


def dif(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else round(a - b, 1)


# ------------------------------------------------------------------ horários


def _horas(
    uf: str, bus: dict[tuple[int, int], dict[str, Any]], dia: str
) -> tuple[
    dict[tuple[int, int], tuple[int | None, int | None, int | None]], dict[str, int]
]:
    """(abertura, encerramento, recebimento) em minutos de Brasília desde a meia-noite."""
    brutos = {}
    aberturas: dict[str, list[int]] = defaultdict(list)
    for k, b in bus.items():
        a = tempo.para_brasilia(tempo.minutos_locais(b["abertura"], dia), uf)
        e = tempo.para_brasilia(tempo.minutos_locais(b["encerramento"], dia), uf)
        brutos[k] = (b["mun"], a, e, tempo.minutos_locais(b.get("dr_hr"), dia))
        if a is not None:
            aberturas[b["mun"]].append(a)
    corr = tempo.correcoes_municipais(uf, aberturas)
    out = {}
    for k, (mun, a, e, r) in brutos.items():
        c = corr.get(mun, 0)
        out[k] = (
            None if a is None else a + c,
            None if e is None else e + c,
            r,
        )
    return out, corr


# ------------------------------------------------------------------ sinais do 2º turno


def _sinais(
    uf: str,
    b2: dict[tuple[int, int], dict[str, Any]],
    ctx: Contexto,
    agregadas1: dict[tuple[int, int], list[int]],
) -> dict[tuple[int, int], tuple[int, list[str], list[str], bool]]:
    if not b2:
        return {}
    df = pd.DataFrame(
        [
            {
                "uf": uf,
                "mun": str(b["mun"]).zfill(5),
                "zona": z,
                "secao": s,
                "origem": "completo",
                "aptos": b["aptos"],
                "comp": b["comparecimento"],
                "fl": b["flavio"],
                "lu": b["lula"],
                "brancos": b["brancos"],
                "nulos": b["nulos"],
                "hab_bio": b["hab_biometria"],
                "ano_nasc": b["hab_ano_nascimento"],
                "sem_bio": b["comp_sem_biometria"],
                "tipo_arquivo": b["tipo_arquivo"],
                "tipo_urna": b["tipo_urna"],
                "n_cargas": b["n_cargas"],
                "abertura": b["abertura"],
                "encerramento": b["encerramento"],
                "emissao": b["emissao"],
                "dr_hr": b.get("dr_hr"),
            }
            for (z, s), b in b2.items()
        ]
    )
    u = df["uf"]
    warnings.filterwarnings("ignore", message="Could not infer format")
    df["abert_min"] = secoes_fonte.minutos_local(df["abertura"], u)
    df["enc_min"] = secoes_fonte.minutos_local(df["encerramento"], u)
    df["emis_min"] = secoes_fonte.minutos_local(df["emissao"], u)
    df["rec_min"] = secoes_fonte.minutos_local(
        df["dr_hr"], pd.Series("BR", index=df.index)
    )
    df = df[secoes_fonte.COLUNAS].copy()
    corr = secoes_fonte.correcao_fuso_municipal(df)
    df["corr_fuso_min"] = corr
    for c in ("abert_min", "enc_min", "emis_min"):
        df[c] = df[c] + corr
        df.loc[df["uf"] == "ZZ", c] = np.nan
    for c in ("tipo_arquivo", "tipo_urna", "n_cargas"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    ref = ctx.ref[ctx.ref["uf"] == uf]
    x = secoes_sinais.montar(df, ref, ctx.mun_ref, ctx.med_mun, ctx.med_zona)
    x = secoes_sinais.sinais(x)
    saltos = x[x["sinal_salto_bio"] & x["local"].notna() & (x["local"] >= 0)]
    por_local = saltos.groupby("local").size()
    texto_para_chave = {t: k for k, t in secoes_ranking.REGRAS_EXPLICACAO}
    out = {}
    for _, r in x.iterrows():
        k = (int(r["zona"]), int(r["secao"]))
        sinais = [s for s in SINAIS if bool(r[f"sinal_{s}"])]
        exp: list[str] = []
        if sinais:
            li = r["local"]
            sl = (
                int(por_local.get(li, 0)) - int(bool(r["sinal_salto_bio"]))
                if pd.notna(li)
                else 0
            )
            txt = secoes_ranking.explicar(r, agregadas1.get(k, []), sl)
            exp = [texto_para_chave[t] for t in txt if t in texto_para_chave]
        out[k] = (int(r["escore"]), sinais, exp, bool(r["contingencia"]))
    return out


# ------------------------------------------------------------------ agregação


SOMAS = (
    "aptos1",
    "comp1",
    "flavio1",
    "lula1",
    "terceira1",
    "bn1",
    "aptos2",
    "comp2",
    "flavio2",
    "lula2",
    "bn2",
    "aptos1p",
    "comp1p",
    "flavio1p",
    "lula1p",
)


def somar(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Totais de um grupo de seções (prédio, município, UF) e as taxas sobre as somas."""
    s: dict[str, Any] = dict.fromkeys(SOMAS, 0)
    n_bu = n_par = n_1 = 0
    esc_max = sinal = sinal2 = mud = trocadas = 0
    log_max = log_subiu = log_persiste = log_reinicio = log_bat = 0
    # Mistura estatística dos dois turnos: só conta onde a análise cobre a seção; sem o
    # arquivo do motor, o campo fica nulo (o mapa pinta de cinza, não de "nenhuma").
    anomalas: int | None = None
    for r in rows:
        v = r["_raw"]
        if v["bu2"] and r.get("ml_anomalo") is not None:
            anomalas = (anomalas or 0) + int(bool(r["ml_anomalo"]))
        if v["flavio1"] is not None:
            n_1 += 1
            for c in ("aptos1", "comp1", "flavio1", "lula1", "terceira1", "bn1"):
                s[c] += v[c]
        if v["bu2"]:
            n_bu += 1
            for c in ("aptos2", "comp2", "flavio2", "lula2", "bn2"):
                s[c] += v[c]
            if v["flavio1"] is not None:
                n_par += 1
                s["aptos1p"] += v["aptos1"]
                s["comp1p"] += v["comp1"]
                s["flavio1p"] += v["flavio1"]
                s["lula1p"] += v["lula1"]
            esc = r.get("escore") or 0
            esc_max = max(esc_max, esc)
            sinal += esc >= 1
            sinal2 += esc >= 2
            if r.get("urna_situacao") not in (None, "mesma", "mesma_recarga", "sem_1t"):
                trocadas += 1
        if (r.get("mudanca") or {}).get("real"):
            mud += 1
        a2, a1 = r.get("log2_atencao"), r.get("log1_atencao")
        if a2 is not None:
            log_max = max(log_max, a2)
            log_subiu += a2 >= 2 and a1 is not None and a1 <= 1
            log_persiste += a2 >= 2 and a1 is not None and a1 >= 2
            log_reinicio += bool(r.get("log2_reinicios"))
            log_bat += r.get("log2_bateria") in ("simultanea", "isolada", "votacao")
    val1 = s["flavio1"] + s["lula1"] + s["terceira1"]
    t = {
        **s,
        "n_secoes": len(rows),
        "n_1t": n_1,
        "n_bu2": n_bu,
        "n_par": n_par,
        "comp_pct1": pct(s["comp1"], s["aptos1"]),
        "comp_pct2": pct(s["comp2"], s["aptos2"]),
        "comp_pct1_par": pct(s["comp1p"], s["aptos1p"]),
        "abst_pct1": pct(s["aptos1"] - s["comp1"], s["aptos1"]),
        "abst_pct2": pct(s["aptos2"] - s["comp2"], s["aptos2"]),
        "bn_pct1": pct(s["bn1"], s["comp1"]),
        "bn_pct2": pct(s["bn2"], s["comp2"]),
        "flavio_v1": pct(s["flavio1"], val1),
        "lula_v1": pct(s["lula1"], val1),
        "terceira_v1": pct(s["terceira1"], val1),
        "fatia_f1": pct(s["flavio1"], s["flavio1"] + s["lula1"]),
        "fatia_f1_par": pct(s["flavio1p"], s["flavio1p"] + s["lula1p"]),
        "fatia_f2": pct(s["flavio2"], s["flavio2"] + s["lula2"]),
        "escore_max": esc_max,
        "secoes_sinal": sinal,
        "secoes_sinal2": sinal2,
        "secoes_mudaram": mud,
        "urnas_trocadas": trocadas,
        "log2_atencao_max": log_max,
        "secoes_log_subiu": log_subiu,
        "secoes_log_persiste": log_persiste,
        "secoes_log_reinicio": log_reinicio,
        "secoes_log_bateria": log_bat,
        "secoes_anomalas": anomalas,
    }
    t["d_fatia_pp"] = dif(t["fatia_f2"], t["fatia_f1_par"])
    t["d_comp_pp"] = dif(t["comp_pct2"], t["comp_pct1_par"])
    return t


def _campos_log2(
    uf: str,
    mun: str,
    lg: dict[str, Any] | None,
    det: dict[str, Any] | None,
    corr: dict[str, int],
) -> dict[str, Any]:
    """Campos ``log2_*`` da seção: atenção, sinais, reinícios na votação, bateria, MR."""
    vazio = dict.fromkeys(LOG2, None)
    if lg is None:
        return vazio
    sinais = lg["sinais"]
    if "bateria_votacao_local" in sinais:
        bat = "simultanea"
    elif "bateria_votacao_isolada" in sinais:
        bat = "isolada"
    elif (lg.get("bateria_votacao") or 0) > 0:
        bat = "votacao"
    else:
        bat = None
    reinicios: list[list[int | None]] = []
    meta: list[Any] | None = None
    if det:
        na_votacao = [p for p in det["partidas"] if p.get("fase") == "votacao"]
        sistema = [p for p in na_votacao if p.get("tipo") == "sistema"]
        for p in sistema or na_votacao:
            seg = p.get("segundo")
            m = (
                None
                if seg is None
                else tempo.para_brasilia(int(seg) // 60, uf, corr.get(mun, 0))
            )
            reinicios.append([m, p.get("votos_antes"), p.get("votos_depois")])
        urnas = list((det.get("meta") or {}).values())
        if urnas:
            u = urnas[-1]
            meta = [
                "; ".join(
                    u.get("versao_aplicacao_dia") or u.get("versao_aplicacao") or []
                )
                or None,
                u.get("carga_registrada_em"),
                ", ".join(u.get("serie_mr_dia") or u.get("serie_mr") or []) or None,
            ]
    return {
        "log2_atencao": familias.atencao(sinais),
        "log2_sinais": sinais,
        "log2_familias": familias.familias_de(sinais),
        "log2_reinicios": reinicios,
        "log2_bateria": bat,
        "log2_bateria_simultaneas": lg.get("bateria_simultaneas"),
        "log2_erro_mr": lg.get("erro_mr"),
        "log2_meta": meta,
    }


LOG2 = [
    "log2_atencao",
    "log2_sinais",
    "log2_familias",
    "log2_reinicios",
    "log2_bateria",
    "log2_bateria_simultaneas",
    "log2_erro_mr",
    "log2_meta",
]


def _celula(lat: float | None, lon: float | None) -> str | None:
    if lat is None or lon is None:
        return None
    return f"{math.floor(lat * 2) / 2},{math.floor(lon * 2) / 2}"


def _celula25(lat: float | None, lon: float | None) -> str | None:
    """Célula de 0,25° da chuva observada: canto sudoeste com duas casas."""
    if lat is None or lon is None:
        return None
    return f"{math.floor(lat * 4) / 4:.2f},{math.floor(lon * 4) / 4:.2f}"


# ------------------------------------------------------------------ UF


def processar_uf(uf: str, ctx: Contexto) -> ResultadoUF:
    res = ResultadoUF(uf=uf)
    pz = fontes.politize_zonas(uf)
    locais, nomes_mun = fontes.politize_locais(uf)
    res.nomes_mun = dict(nomes_mun)
    cat = fontes.catalogo_2t(uf)
    b2 = fontes.bu(fontes.DB_2T, uf)
    b1 = fontes.bu(fontes.DB_1T, uf)
    fis = fontes.fiscal(uf)
    mud = fontes.mudancas(uf)
    log1 = fontes.logs_1t(uf)
    clima1 = fontes.clima_1t(uf)
    ml = fontes.anomalia_ml(uf)

    principais2: set[tuple[int, int]] = set()
    agreg2: dict[tuple[int, int], list[int]] = defaultdict(list)
    mun2: dict[tuple[int, int], str] = {}
    for mun, z, s, nsp, _rec in cat:
        z, s = int(z), int(s)
        p = int(nsp) if nsp and int(nsp) != s else s
        mun2[(z, s)] = mun
        if p == s:
            principais2.add((z, s))
        else:
            agreg2[(z, p)].append(s)
    agreg1: dict[tuple[int, int], list[int]] = {}
    for z, d in pz.items():
        for s, r in d["secoes"].items():
            agreg1[(z, s)] = sorted(int(a) for a in (r.get("agregadas") or []))
    chaves = sorted(set(agreg1) | principais2)

    h1, _ = _horas(uf, b1, DIA_1T)
    h2, corr2 = _horas(uf, b2, DIA_2T)
    log2 = fontes.logs_2t(uf)
    log2d = fontes.logs_2t_detalhe(uf)
    sin = _sinais(uf, b2, ctx, agreg1)
    nomes_fiscal = ctx.catalogo["fiscal"]

    for z, s in chaves:
        pol = pz.get(z, {}).get("secoes", {}).get(s)
        bb1 = b1.get((z, s))
        bb2 = b2.get((z, s))
        mun = (
            (pol or {}).get("mun_tse")
            or mun2.get((z, s))
            or (bb2 or bb1 or {}).get("mun")
        )
        if mun and mun not in res.nomes_mun:
            res.nomes_mun[mun] = mun
        local_id = (pol or {}).get("local_id")
        if not local_id and bb2 and bb2.get("local") is not None:
            local_id = f"{uf}-{mun}-{z}-{int(bb2['local'])}"
        a1 = sorted(agreg1.get((z, s), []))
        a2 = sorted(agreg2.get((z, s), []))
        tem2cat = (z, s) in principais2
        raw: dict[str, Any] = {
            "aptos1": (pol or {}).get("aptos"),
            "comp1": (pol or {}).get("comparecimento"),
            "flavio1": (pol or {}).get("flavio"),
            "lula1": (pol or {}).get("lula"),
            "terceira1": (pol or {}).get("terceira"),
            "bn1": None,
            "bu2": bb2 is not None,
            "aptos2": None,
            "comp2": None,
            "flavio2": None,
            "lula2": None,
            "bn2": None,
        }
        if raw["flavio1"] is not None:
            raw["bn1"] = (pol.get("brancos") or 0) + (pol.get("nulos") or 0)
        elif bb1 is not None:
            # seção pequena no Politize: os votos vêm do BU para os totais
            raw.update(
                aptos1=bb1["aptos"],
                comp1=bb1["comparecimento"],
                flavio1=bb1["flavio"],
                lula1=bb1["lula"],
                terceira1=bb1["outros"],
                bn1=bb1["brancos"] + bb1["nulos"],
            )
        if bb2 is not None:
            raw.update(
                aptos2=bb2["aptos"],
                comp2=bb2["comparecimento"],
                flavio2=bb2["flavio"],
                lula2=bb2["lula"],
                bn2=bb2["brancos"] + bb2["nulos"],
                brancos2=bb2["brancos"],
                nulos2=bb2["nulos"],
            )
        pequena = any(
            v is not None and v < MIN_APTOS for v in (raw["aptos1"], raw["aptos2"])
        )
        hh1 = h1.get((z, s), (None, None, None))
        hh2 = h2.get((z, s), (None, None, None))
        esc, sinais, exp, cont = sin.get((z, s), (None, [], [], False))
        orig = (
            ctx.mapa_urnas.get(bb2["numero_interno_urna"])
            if bb2 and bb2.get("numero_interno_urna")
            else None
        )
        sit = urna.situacao(
            (bb1 or {}).get("numero_interno_urna"),
            (bb2 or {}).get("numero_interno_urna"),
            (bb1 or {}).get("codigo_carga"),
            (bb2 or {}).get("codigo_carga"),
            (bb2 or {}).get("tipo_urna"),
            orig,
            (uf, str(mun), z, s),
        )
        fz = fis.get((z, s))
        logs = log1.get((z, s))
        mls = ml.get((z, s))
        r: dict[str, Any] = {
            "uf": uf,
            "secao": s,
            "mun_tse": mun,
            "local_id": local_id,
            "local_nr2": (bb2 or {}).get("local"),
            "agregadas1": a1 if pol else None,
            "agregadas2": a2 if tem2cat else None,
            "agreg_igual": (a1 == a2) if (pol and tem2cat) else None,
            "pequena": pequena,
            "aptos1": raw["aptos1"],
            "aptos2": raw["aptos2"],
            "bu2": raw["bu2"],
            "abert1": hh1[0],
            "enc1": hh1[1],
            "rec1": hh1[2],
            "abert2": hh2[0],
            "enc2": hh2[1],
            "rec2": hh2[2],
            "urna1": (bb1 or {}).get("numero_interno_urna"),
            "modelo1": (bb1 or {}).get("modelo_urna"),
            "tipo_urna1": (bb1 or {}).get("tipo_urna"),
            "cargas1": (bb1 or {}).get("n_cargas"),
            "urna2": (bb2 or {}).get("numero_interno_urna"),
            "modelo2": (bb2 or {}).get("modelo_urna"),
            "tipo_urna2": (bb2 or {}).get("tipo_urna"),
            "cargas2": (bb2 or {}).get("n_cargas"),
            "tipo_arquivo2": (bb2 or {}).get("tipo_arquivo"),
            "urna_situacao": sit,
            "mesma_carga": (
                (bb1 or {}).get("codigo_carga") == bb2.get("codigo_carga")
                if bb1 and bb2
                else None
            ),
            "contingencia2": (
                (
                    bool(cont)
                    or (
                        bb2 is not None
                        and (
                            bb2.get("tipo_urna") in TIPOS_CONTINGENCIA
                            or (bb2.get("n_cargas") or 0) > 1
                        )
                    )
                )
                if bb2
                else None
            ),
            "escore": esc,
            "sinais": sinais,
            "explicacoes": exp,
            "fiscal_nivel": fz[0] if fz else None,
            "fiscal_pontos": fz[1] if fz else None,
            "fiscal_sinais": fz[2] if fz else [],
            "c13_nivel": fz[3] if fz else None,
            "log1_atencao": familias.atencao(logs) if logs is not None else None,
            "log1_sinais": logs if logs is not None else None,
            "log1_familias": familias.familias_de(logs) if logs is not None else None,
            **_campos_log2(uf, str(mun), log2.get((z, s)), log2d.get((z, s)), corr2),
            "ml_grupo": mls[0] if mls else None,
            "ml_anomalo": mls[3] if mls else None,
            "ml_p": round(mls[2], 4) if mls else None,
            "mudanca": mud.get((z, s)),
            "_raw": raw,
            "_pol_local": (pol or {}).get("local"),
            "_pol_bairro": (pol or {}).get("bairro"),
        }
        if not pequena:
            v = raw
            r.update(
                comp1=v["comp1"],
                flavio1=v["flavio1"],
                lula1=v["lula1"],
                terceira1=v["terceira1"],
                brancos1=(
                    (pol or {}).get("brancos")
                    if pol and pol.get("flavio") is not None
                    else None
                ),
                nulos1=(
                    (pol or {}).get("nulos")
                    if pol and pol.get("flavio") is not None
                    else None
                ),
                comp2=v["comp2"],
                flavio2=v["flavio2"],
                lula2=v["lula2"],
                brancos2=v.get("brancos2"),
                nulos2=v.get("nulos2"),
                sem_bio1=(bb1 or {}).get("comp_sem_biometria"),
                ano_nasc1=(bb1 or {}).get("hab_ano_nascimento"),
                hab_bio1=(bb1 or {}).get("hab_biometria"),
                sem_bio2=(bb2 or {}).get("comp_sem_biometria"),
                ano_nasc2=(bb2 or {}).get("hab_ano_nascimento"),
                hab_bio2=(bb2 or {}).get("hab_biometria"),
            )
            val1 = (
                v["flavio1"] + v["lula1"] + v["terceira1"]
                if v["flavio1"] is not None
                else None
            )
            r.update(
                comp_pct1=pct(v["comp1"], v["aptos1"]),
                comp_pct2=pct(v["comp2"], v["aptos2"]),
                abst_pct1=pct(
                    None if v["comp1"] is None else v["aptos1"] - v["comp1"],
                    v["aptos1"],
                ),
                abst_pct2=pct(
                    None if v["comp2"] is None else v["aptos2"] - v["comp2"],
                    v["aptos2"],
                ),
                bn_pct1=pct(v["bn1"], v["comp1"]),
                bn_pct2=pct(v["bn2"], v["comp2"]),
                flavio_v1=pct(v["flavio1"], val1),
                lula_v1=pct(v["lula1"], val1),
                terceira_v1=pct(v["terceira1"], val1),
                fatia_f1=pct(
                    v["flavio1"],
                    None if v["flavio1"] is None else v["flavio1"] + v["lula1"],
                ),
                fatia_f2=pct(
                    v["flavio2"],
                    None if v["flavio2"] is None else v["flavio2"] + v["lula2"],
                ),
                sem_bio_pct1=pct(r["sem_bio1"], (bb1 or {}).get("comparecimento")),
                sem_bio_pct2=pct(r["sem_bio2"], (bb2 or {}).get("comparecimento")),
                ano_nasc_pct1=pct(r["ano_nasc1"], (bb1 or {}).get("comparecimento")),
                ano_nasc_pct2=pct(r["ano_nasc2"], (bb2 or {}).get("comparecimento")),
            )
            r["d_comp_pp"] = dif(r["comp_pct2"], r["comp_pct1"])
            r["d_fatia_pp"] = dif(r["fatia_f2"], r["fatia_f1"])
        r["fiscal_nome"] = (
            nomes_fiscal.get(r["fiscal_nivel"]) if r["fiscal_nivel"] else None
        )
        r["frases"] = textos.frases_secao(r, ctx.catalogo)
        res.secoes.setdefault(z, []).append(r)

    # prédios
    por_local: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for z, rows in res.secoes.items():
        for r in rows:
            if not r["local_id"]:
                r["local_id"] = f"{uf}-{r['mun_tse']}-{z}-sem-local"
            por_local[r["local_id"]].append(r)
    por_mun: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for lid, rows in por_local.items():
        cad = locais.get(lid, {})
        mun = rows[0]["mun_tse"]
        por_mun[mun].extend(rows)
        t = somar(rows)
        lat, lon = cad.get("lat"), cad.get("lon")
        prim = min(rows, key=lambda r: r["secao"])
        res.locais[lid] = {
            "local_id": lid,
            "mun_tse": mun,
            "zona": int(lid.split("-")[2]) if lid.count("-") >= 3 else None,
            "nome": cad.get("nome") or (prim.get("_pol_local")),
            "endereco": cad.get("endereco"),
            "bairro": cad.get("bairro") or prim.get("_pol_bairro"),
            "cep": cad.get("cep"),
            "lat": lat,
            "lon": lon,
            "secoes": sorted(r["secao"] for r in rows),
            "secao_link": prim["secao"],
            "clima1": clima1.get(lid),
            "clima2": ctx.previsao.get(_celula(lat, lon) or ""),
            "clima2o": ctx.observado.get(_celula25(lat, lon) or ""),
            **t,
        }
    for mun, rows in por_mun.items():
        res.municipios[mun] = {
            "mun_tse": mun,
            "nome": res.nomes_mun.get(mun, mun),
            **somar(rows),
        }
    for p in res.locais.values():
        p["frases"] = textos.frases_local(p, res.municipios[p["mun_tse"]])
    todas = [r for rows in res.secoes.values() for r in rows]
    res.totais = somar(todas)
    return res
