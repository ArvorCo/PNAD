"""Ângulo do pianista: a célula "comparecimento +5 pp e salto de biometria" tem no log
a marca que a liberação de eleitor ausente deixaria?

Célula: coluna ``pianista`` de ``secoes_linhas`` (``sinal_delta`` e ``sinal_salto_bio``,
regra em ``secoes_sinais``). Controles:

- **vizinhas**: seções do mesmo município com escore 0 (nenhum dos seis sinais), até
  ``VIZINHAS_POR_SECAO`` por seção da célula, sorteadas com semente fixa;
- **salto sem comparecimento**: ``sinal_salto_bio`` sem ``sinal_delta``, todas;
- **a própria seção no 1º turno**, relida do original com o mesmo leitor.

Métricas do log por seção e turno em ``angulo_pianista_log.medir``. A marca esperada
(``REGRAS``): habilitações sem biometria reconhecida concentradas numa janela (última
hora ou sequência improvável sob ordem aleatória), com ritmo rápido ou regular ou
habilitação sem biometria tão curta quanto a biométrica, e sem reinício, contingência
ou segunda urna que explique a falha do leitor.

Diferença em diferenças (2T menos 1T da mesma seção, célula menos controle) com IC de
95% por bootstrap de municípios (2.000 reamostragens). Rótulo: sinal pede explicação,
não prova irregularidade.
"""

from __future__ import annotations

import gzip
import json
import math
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import secoes_linhas
from .angulo_pianista_log import ULTIMA_HORA, extrair
from .secoes_ref import nomes_municipios

ROOT = Path(__file__).resolve().parents[2]
DADOS = ROOT / "analysis/apuracao_2t_2026/dados"
CACHE = ROOT / "data/outputs/apuracao_2t_2026/angulo_pianista_metricas.json.gz"
INDICE = ROOT / "docs/assets/politize/dados/indice.json"
ROTULO = "Sinal pede explicação, não prova irregularidade."
REPS = 2000
SEMENTE = 20261026
VIZINHAS_POR_SECAO = 10
TOP = 20

REGRAS: dict[str, Any] = {
    "nbio": (
        "habilitação sem biometria reconhecida = ano de nascimento (biometria "
        "cadastrada não reconhecida) + sem biometria cadastrada, pelo log"
    ),
    "ultima_hora": f"cômputos a partir das {ULTIMA_HORA}:00 de Brasília",
    "concentra": (
        "≥ 5 habilitações sem biometria na última hora e parcela delas na última hora "
        "≥ 20 pp acima da parcela de todos os votos da seção na última hora"
    ),
    "rajada": (
        "maior sequência de habilitações sem biometria seguidas ≥ 5 e chance dessa "
        "sequência sob ordem aleatória < 1% (1 − exp(−n(1−p)p^k))"
    ),
    "ritmo": (
        "intervalo mediano entre cômputos seguidos sem biometria ≤ metade do intervalo "
        "mediano da seção, ou coeficiente de variação ≤ 0,25 com ≥ 8 pares"
    ),
    "hab_curta": (
        "tempo mediano de habilitação sem biometria ≤ o da biométrica na mesma seção "
        "(o fluxo legítimo passa por tentativas de digital antes do ano de nascimento)"
    ),
    "sem_explicacao": "sem reinício na votação, sem contingência, uma urna no log",
    "marca": "(concentra ou rajada) e (ritmo ou hab_curta) e sem_explicacao",
    "marca_forte": "concentra e rajada e ritmo e hab_curta e sem_explicacao",
    "marca_nova": "marca no 2º turno e não no 1º, na mesma seção",
    "forca": (
        "excesso da última hora/10 + min(10, −log10 chance da sequência)/2 "
        "+ 1 se ritmo + 1 se hab_curta (o comprimento cru da sequência fica fora: "
        "seção em que quase ninguém foi reconhecido tem sequência longa e provável)"
    ),
    "leitor_parado": (
        "parcela sem biometria reconhecida ≥ 50% no 2º turno: assinatura de leitor "
        "que não reconhece ninguém, descritiva"
    ),
    "vizinhas": f"escore 0 no mesmo município, até {VIZINHAS_POR_SECAO} por seção da célula",
}

METRICAS = {
    "pct_nbio": "parcela sem biometria reconhecida (%)",
    "excesso_ultima_pp": "excesso da última hora nas habilitações sem biometria (pp)",
    "pct_todos_na_ultima_hora": "parcela de todos os votos na última hora (%)",
    "maior_sequencia_nbio": "maior sequência sem biometria (votos seguidos)",
    "menos_log10_p": "improbabilidade da sequência (−log10 da chance)",
    "razao_intervalo_nbio": "intervalo sem biometria / intervalo da seção",
    "hab_nbio_p50_s": "habilitação sem biometria, mediana (s)",
    "hab_p50_s": "habilitação, mediana de todos (s)",
    "voto_p50_s": "tempo de votação, mediana (s)",
    "reinicios_votacao": "reinícios durante a votação",
    "marca": "seções com a marca (%)",
}


def _r(x: Any, c: int = 2) -> float | None:
    if x is None:
        return None
    x = float(x)
    return None if not math.isfinite(x) else round(x, c)


# ---------------------------------------------------------------- grupos


def grupos(linhas: pd.DataFrame, semente: int = SEMENTE) -> pd.DataFrame:
    """Célula, salto sem comparecimento e vizinhas sorteadas, com a coluna ``grupo``."""
    x = linhas[linhas["uf"] != "ZZ"].copy()
    cel = x[x["pianista"].astype(bool)].assign(grupo="celula")
    salto = x[x["sinal_salto_bio"].astype(bool) & ~x["sinal_delta"].astype(bool)]
    salto = salto.assign(grupo="salto_sem_delta")
    n_mun = cel.groupby(["uf", "mun"]).size()
    limpas = x[(x["escore"] == 0) & x.set_index(["uf", "mun"]).index.isin(n_mun.index)]
    rng = np.random.default_rng(semente)
    viz = []
    for (uf, mun), g in limpas.groupby(["uf", "mun"], sort=True):
        k = min(len(g), VIZINHAS_POR_SECAO * int(n_mun[(uf, mun)]))
        viz.append(g.iloc[np.sort(rng.choice(len(g), size=k, replace=False))])
    vz = pd.concat(viz).assign(grupo="vizinhas") if viz else x.iloc[:0]
    return pd.concat([cel, salto, vz], ignore_index=True)


def chave(r) -> tuple:
    return (str(r.uf).lower(), str(r.mun), int(r.zona), int(r.secao))


# ---------------------------------------------------------------- extração


def carregar_metricas(g: pd.DataFrame, refazer: bool = False, workers: int = 8) -> dict:
    """{"2t": {chave_txt: métricas}, "1t": {...}}, com cache em ``CACHE``."""
    cache: dict = {"2t": {}, "1t": {}}
    if CACHE.exists() and not refazer:
        cache = json.loads(gzip.decompress(CACHE.read_bytes()))
    chaves = sorted({chave(r) for r in g.itertuples()})
    for turno, numero in (("2t", 3221), ("1t", 3220)):
        falta = [k for k in chaves if "|".join(map(str, k)) not in cache[turno]]
        if falta:
            novos = extrair(numero, falta, workers=workers)
            for k, v in novos.items():
                cache[turno]["|".join(map(str, k))] = v
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    corpo = json.dumps(cache, separators=(",", ":"), allow_nan=False).encode()
    CACHE.write_bytes(gzip.compress(corpo, mtime=0))
    return cache


def derivar(m: dict | None) -> dict[str, Any]:
    """Métricas derivadas e componentes da marca de um turno."""
    if not m or "erro" in m or not m.get("n"):
        return {}
    pu, pt = m.get("pct_nbio_na_ultima_hora"), m.get("pct_todos_na_ultima_hora")
    exc = (pu - pt) if pu is not None and pt is not None else None
    p = m.get("p_sequencia")
    mlog = min(10.0, -math.log10(max(p, 1e-300))) if p is not None else None
    ii, ib = m.get("intervalo_nbio_p50_s"), m.get("intervalo_p50_s")
    razao = ii / ib if ii is not None and ib else None
    concentra = (m["nbio_ultima_hora"] >= 5) and exc is not None and exc >= 20
    rajada = m["maior_sequencia_nbio"] >= 5 and p is not None and p < 0.01
    cv = m.get("cv_intervalo_nbio")
    ritmo = (razao is not None and razao <= 0.5) or (
        cv is not None and cv <= 0.25 and m.get("pares_nbio", 0) >= 8
    )
    hn, hb = m.get("hab_nbio_p50_s"), m.get("hab_bio_p50_s")
    hab_curta = hn is not None and hb is not None and m["n_nbio"] >= 5 and hn <= hb
    sem_exp = m["reinicios_votacao"] == 0 and not m["contingencia"] and m["urnas"] == 1
    marca = (concentra or rajada) and (ritmo or hab_curta) and sem_exp
    forte = concentra and rajada and ritmo and hab_curta and sem_exp
    forca = max(0.0, exc or 0) / 10 + (mlog or 0) / 2 + float(ritmo) + float(hab_curta)
    return {
        **m,
        "excesso_ultima_pp": exc,
        "menos_log10_p": mlog,
        "razao_intervalo_nbio": razao,
        "concentra": concentra,
        "rajada": rajada,
        "ritmo": bool(ritmo),
        "hab_curta": hab_curta,
        "sem_explicacao": sem_exp,
        "marca": marca,
        "marca_forte": forte,
        "forca": forca,
    }


def quadro(g: pd.DataFrame, cache: dict) -> pd.DataFrame:
    """Uma linha por seção com as métricas dos dois turnos (sufixos ``_2t`` e ``_1t``)."""
    linhas = []
    for r in g.itertuples():
        k = "|".join(map(str, chave(r)))
        d2, d1 = derivar(cache["2t"].get(k)), derivar(cache["1t"].get(k))
        if not d2:
            continue
        reg = {
            "uf": r.uf,
            "mun": r.mun,
            "zona": int(r.zona),
            "secao": int(r.secao),
            "grupo": r.grupo,
            "aptos": int(r.aptos),
            "delta_pp": r.delta_pp,
            "salto_bio_pp": r.salto_bio_pp,
            "tem_1t": bool(d1),
        }
        for c in [*METRICAS, "concentra", "rajada", "ritmo", "hab_curta"]:
            reg[c + "_2t"] = d2.get(c)
            reg[c + "_1t"] = d1.get(c) if d1 else None
        for c in (
            "marca_forte",
            "sem_explicacao",
            "forca",
            "n",
            "n_nbio",
            "nbio_ultima_hora",
            "pct_nbio_na_ultima_hora",
            "hora_ultima_nbio",
            "intervalo_p50_s",
            "intervalo_nbio_p50_s",
            "hab_bio_p50_s",
            "p_sequencia",
            "contingencia",
            "tempos_validos",
        ):
            reg[c + "_2t"] = d2.get(c)
        reg["marca_1t_val"] = d1.get("marca") if d1 else None
        linhas.append(reg)
    q = pd.DataFrame(linhas)
    for c in [*METRICAS, "concentra", "rajada", "ritmo", "hab_curta"]:
        for t in ("_2t", "_1t"):
            col = q[c + t]
            if col.dtype == object:
                col = col.map(lambda v: np.nan if v is None else float(v))
            q[c + t] = col.astype(float)
    for c in ("marca", "concentra", "rajada", "ritmo", "hab_curta"):
        q[c + "_2t"] *= 100
        q[c + "_1t"] *= 100
    q["marca_nova"] = (q["marca_2t"] > 0) & (q["marca_1t"].fillna(0) == 0) & q["tem_1t"]
    return q


# ---------------------------------------------------------------- comparações


def _boot(est, n_mun: int, reps: int, semente: int) -> list[float | None]:
    if n_mun < 2:
        return [None, None]
    rng = np.random.default_rng(semente)
    cont = rng.multinomial(n_mun, np.full(n_mun, 1.0 / n_mun), size=reps).astype(float)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        v = est(cont)
    v = v[np.isfinite(v)]
    if not len(v):
        return [None, None]
    lo, hi = np.percentile(v, [2.5, 97.5])
    return [_r(lo), _r(hi)]


def _agregado(q: pd.DataFrame, col: str, grupo: str) -> pd.DataFrame:
    s = q[(q["grupo"] == grupo) & q[col].notna()]
    return s.groupby(["uf", "mun"])[col].agg(["sum", "count"])


def contra_vizinhas(q: pd.DataFrame, col: str, reps: int, semente: int) -> dict:
    """Média por município (célula − vizinhas), ponderada pelo n da célula."""
    a, b = _agregado(q, col, "celula"), _agregado(q, col, "vizinhas")
    t = a.join(b, lsuffix="_c", rsuffix="_v", how="inner")
    if t.empty:
        return {"n_municipios": 0}
    d = (t["sum_c"] / t["count_c"] - t["sum_v"] / t["count_v"]).to_numpy()
    w = t["count_c"].to_numpy(dtype=float)
    est = float(np.sum(w * d) / np.sum(w))

    def f(cont):
        return (cont @ (w * d)) / (cont @ w)

    return {
        "estimativa": _r(est),
        "ic95": _boot(f, len(t), reps, semente),
        "n_celula": int(t["count_c"].sum()),
        "n_controle": int(t["count_v"].sum()),
        "n_municipios": len(t),
    }


def contra_grupo(q: pd.DataFrame, col: str, ctrl: str, reps: int, semente: int) -> dict:
    """Média da célula menos média do controle; municípios reamostrados juntos."""
    a, b = _agregado(q, col, "celula"), _agregado(q, col, ctrl)
    t = a.join(b, lsuffix="_c", rsuffix="_v", how="outer").fillna(0.0)
    if not t["count_c"].sum() or not t["count_v"].sum():
        return {"n_municipios": 0}
    sc, nc = t["sum_c"].to_numpy(), t["count_c"].to_numpy()
    sv, nv = t["sum_v"].to_numpy(), t["count_v"].to_numpy()
    est = sc.sum() / nc.sum() - sv.sum() / nv.sum()

    def f(cont):
        return (cont @ sc) / (cont @ nc) - (cont @ sv) / (cont @ nv)

    return {
        "estimativa": _r(est),
        "ic95": _boot(f, len(t), reps, semente),
        "n_celula": int(nc.sum()),
        "n_controle": int(nv.sum()),
        "n_municipios": len(t),
    }


def contra_1t(q: pd.DataFrame, col: str, reps: int, semente: int) -> dict:
    """Média da variação 2T − 1T na própria seção da célula."""
    a = _agregado(q, col, "celula")
    if a.empty:
        return {"n_municipios": 0}
    s, n = a["sum"].to_numpy(), a["count"].to_numpy(dtype=float)

    def f(cont):
        return (cont @ s) / (cont @ n)

    return {
        "estimativa": _r(s.sum() / n.sum()),
        "ic95": _boot(f, len(a), reps, semente),
        "n_celula": int(n.sum()),
        "n_municipios": len(a),
    }


def comparacoes(q: pd.DataFrame, reps: int = REPS, semente: int = SEMENTE) -> dict:
    q = q.copy()
    out: dict[str, Any] = {}
    for i, (m, nome) in enumerate(METRICAS.items()):
        q[m + "_d"] = q[m + "_2t"] - q[m + "_1t"]
        s = semente + 10 * i
        out[m] = {
            "nome": nome,
            "nivel_2t_celula_menos_vizinhas": contra_vizinhas(q, m + "_2t", reps, s),
            "did_vizinhas": contra_vizinhas(q, m + "_d", reps, s + 1),
            "did_salto_sem_delta": contra_grupo(
                q, m + "_d", "salto_sem_delta", reps, s + 2
            ),
            "celula_2t_menos_1t": contra_1t(q, m + "_d", reps, s + 3),
        }
    return out


def medias(q: pd.DataFrame) -> dict:
    out = {}
    for g, s in q.groupby("grupo"):
        r: dict[str, Any] = {"secoes": len(s), "com_1t": int(s["tem_1t"].sum())}
        for m in METRICAS:
            for t in ("_2t", "_1t"):
                v = s[m + t].dropna()
                r[m + t] = _r(v.mean()) if len(v) else None
        for t in ("_2t", "_1t"):
            j = (s["concentra" + t].fillna(0) > 0) | (s["rajada" + t].fillna(0) > 0)
            r["janela" + t] = int(j.sum())
        for c in ("concentra", "rajada", "ritmo", "hab_curta"):
            r[f"{c}_n_2t"] = int((s[c + "_2t"].fillna(0) > 0).sum())
            r[c + "_pct_2t"] = _r(s[c + "_2t"].mean())
            r[c + "_pct_1t"] = _r(s[c + "_1t"].dropna().mean())
        r["leitor_parado_2t"] = int((s["pct_nbio_2t"] >= 50).sum())
        r["leitor_parado_1t"] = int((s["pct_nbio_1t"] >= 50).sum())
        r["marca_2t"] = int((s["marca_2t"] > 0).sum())
        r["marca_1t"] = int((s["marca_1t"].fillna(0) > 0).sum())
        r["marca_forte_2t"] = int(s["marca_forte_2t"].fillna(False).astype(bool).sum())
        r["marca_nova"] = int(s["marca_nova"].sum())
        r["sem_explicacao_2t"] = int(s["sem_explicacao_2t"].fillna(False).sum())
        r["tempos_validos_2t"] = int(s["tempos_validos_2t"].fillna(False).sum())
        out[g] = r
    return out


def rajadas(q: pd.DataFrame) -> dict:
    """Como são as sequências improváveis da célula: ritmo e habilitação nelas."""
    out = {}
    for g, s in q.groupby("grupo"):
        r = s[s["rajada_2t"] > 0]
        razao = r["razao_intervalo_nbio_2t"].dropna()
        out[g] = {
            "secoes": len(r),
            "razao_intervalo_p50": _r(razao.median()) if len(razao) else None,
            "mais_rapidas_que_a_secao": int((razao < 1).sum()),
            "metade_do_intervalo_ou_menos": int((razao <= 0.5).sum()),
            "hab_sem_biometria_p50_s": _r(r["hab_nbio_p50_s_2t"].median()),
            "hab_biometrica_p50_s": _r(r["hab_bio_p50_s_2t"].median()),
            "hab_sem_biometria_curta": int((r["hab_curta_2t"] > 0).sum()),
            "parcela_sem_biometria_p50": _r(r["pct_nbio_2t"].median()),
        }
    return out


def hhmm(h: float | None) -> str | None:
    if h is None or not math.isfinite(h):
        return None
    m = round(h * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def top(q: pd.DataFrame, n: int = TOP) -> list[dict]:
    nomes = nomes_municipios(INDICE) if INDICE.exists() else {}
    c = q[q["grupo"] == "celula"]
    c = c.sort_values(["marca_2t", "forca_2t"], ascending=[False, False]).head(n)
    out = []
    for r in c.itertuples():
        nome = nomes.get((r.uf, r.mun)) or nomes.get((r.uf.lower(), r.mun)) or r.mun
        out.append(
            {
                "uf": r.uf,
                "municipio": nome,
                "mun_tse": r.mun,
                "zona": r.zona,
                "secao": r.secao,
                "aptos": r.aptos,
                "comparecimento_delta_pp": _r(r.delta_pp),
                "salto_bio_pp": _r(r.salto_bio_pp),
                "votos_log": int(r.n_2t),
                "sem_biometria": int(r.n_nbio_2t),
                "pct_sem_biometria_2t": _r(r.pct_nbio_2t),
                "pct_sem_biometria_1t": _r(r.pct_nbio_1t),
                "sem_biometria_ultima_hora": int(r.nbio_ultima_hora_2t),
                "pct_sem_biometria_na_ultima_hora": _r(r.pct_nbio_na_ultima_hora_2t),
                "pct_todos_na_ultima_hora": _r(r.pct_todos_na_ultima_hora_2t),
                "ultima_sem_biometria": hhmm(r.hora_ultima_nbio_2t),
                "maior_sequencia": int(r.maior_sequencia_nbio_2t),
                "chance_sequencia": (
                    float(f"{r.p_sequencia_2t:.2g}")
                    if r.p_sequencia_2t is not None
                    else None
                ),
                "intervalo_p50_s": _r(r.intervalo_p50_s_2t, 1),
                "intervalo_sem_biometria_p50_s": _r(r.intervalo_nbio_p50_s_2t, 1),
                "hab_sem_biometria_p50_s": _r(r.hab_nbio_p50_s_2t, 1),
                "hab_biometrica_p50_s": _r(r.hab_bio_p50_s_2t, 1),
                "componentes": [
                    k
                    for k in ("concentra", "rajada", "ritmo", "hab_curta")
                    if (getattr(r, k + "_2t") or 0) > 0
                ],
                "marca_2t": bool(r.marca_2t > 0),
                "marca_no_1t": bool(r.marca_1t_val) if r.tem_1t else None,
                "forca": _r(r.forca_2t),
                "link": f"politizese.html#uf={r.uf}&zona={r.zona}&secao={r.secao}",
            }
        )
    return out


def analisar(
    secoes: dict | None = None,
    refazer: bool = False,
    workers: int = 8,
    reps: int = REPS,
) -> dict:
    secoes = secoes or json.loads((DADOS / "secoes.json").read_text(encoding="utf-8"))
    b = secoes_linhas.exigir(secoes)
    linhas = pd.DataFrame(b["linhas"], columns=b["colunas"])
    g = grupos(linhas)
    cache = carregar_metricas(g, refazer=refazer, workers=workers)
    q = quadro(g, cache)
    cel = q[q["grupo"] == "celula"]
    n_cel_total = int(linhas["pianista"].astype(bool).sum())
    erros = {t: sum(1 for v in cache[t].values() if "erro" in v) for t in ("2t", "1t")}
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rotulo": ROTULO,
        "pergunta": (
            "A célula comparecimento +5 pp e salto de biometria tem no log a marca que "
            "a liberação de eleitor ausente deixaria?"
        ),
        "regras": REGRAS,
        "metricas": METRICAS,
        "fontes": {
            "linhas": (
                secoes["secoes"].get("arquivo")
                if isinstance(secoes.get("secoes"), dict)
                else None
            ),
            "logs_2t": "data/raw/tse_logs_2026/logs_2t.sqlite (leitor apuracao_logs.parser, versão 12)",
            "logs_1t": "data/raw/tse_logs_2026/logs.sqlite (mesmo leitor)",
            "metricas_2t": "data/outputs/logs_urnas_2t_2026.sqlite (deslocamento de fuso)",
            "voto": "analysis/apuracao_2t_2026/dados/secoes_voto.json, sinal pianista",
        },
        "bootstrap": {
            "reamostragens": reps,
            "semente": SEMENTE,
            "unidade": "município",
        },
        "celula": {
            "secoes": n_cel_total,
            "com_log_2t": len(cel),
            "com_log_1t": int(cel["tem_1t"].sum()),
            "municipios": int(cel.groupby(["uf", "mun"]).ngroups),
        },
        "leitura_erros": erros,
        "grupos": medias(q),
        "comparacoes": comparacoes(q, reps=reps),
        "rajadas": rajadas(q),
        "top": top(q),
        "voto_ja_medido": voto_medido(),
    }


def voto_medido() -> dict:
    p = DADOS / "secoes_voto.json"
    if not p.exists():
        return {}
    v = json.loads(p.read_text(encoding="utf-8"))
    x = next((s for s in v.get("sinais") or [] if s.get("sinal") == "pianista"), None)
    if not x:
        return {}
    return {
        k: x.get(k)
        for k in (
            "n_sinal_total",
            "dif_fatia_flavio_vs_vizinhas_pp",
            "ep_fatia_flavio_vs_vizinhas_pp",
            "did_fatia_flavio_pp",
            "ep_did_fatia_flavio_pp",
        )
    }
