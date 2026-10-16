"""Análise somente de leitura dos diagnósticos dos logs das urnas (1º turno de 2026).

Gera memorando.md e tabelas CSV neste diretório. Não grava nada no repositório.

Fontes (todas em ~/arvor/PNAD):
- docs/assets/logs_urnas_2026/secoes.csv.gz e processos_por_tipo.csv.gz
- docs/assets/logs_urnas_2026/indice.json
- data/outputs/logs_urnas_2026.sqlite (metricas.resumo: contagem de mensagens de
  bateria e horário do primeiro e do último cômputo), aberto em modo somente leitura
- data/raw/tse_logs_2026/logs.sqlite (ZIPs originais), somente leitura, para os
  horários das mensagens de bateria e para contagens agregadas de mensagens de
  habilitação em seções com biográfica >= 90% e controles sorteados
- docs/assets/politize/dados/zona/<UF>/<zona>.json: só nome do município e
  comparecimento (conferência). Nenhuma coluna de voto é lida ou usada.

Regras reproduzidas de scripts/apuracao_logs/criterios.py e regras_processo.py.
Uso: python3 analise_logs.py  (caches em ./cache; apague para recalcular)
"""

from __future__ import annotations

import glob
import json
import re
import sqlite3
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/Users/leonardodias/arvor/PNAD")
PUB = REPO / "docs/assets/logs_urnas_2026"
METRICAS = REPO / "data/outputs/logs_urnas_2026.sqlite"
RAW = REPO / "data/raw/tse_logs_2026/logs.sqlite"
POLITIZE = REPO / "docs/assets/politize/dados/zona"
OUT = Path(__file__).resolve().parent
CACHE = OUT / "cache"
CHAVE = ["uf", "mun", "zona", "secao"]
K = 4  # corte principal publicado
DIAS = ("04/10/2026", "05/10/2026")

sys.path.insert(0, str(REPO / "scripts"))
from apuracao_logs.parser import segundos, textos_zip  # noqa: E402

FAMILIAS = {
    "Energia e reinícios": [
        "bateria",
        "reinicio_sistema",
        "reinicios",
        "erro_tecnico",
        "ciclos_incompletos",
    ],
    "Identificação do eleitor": [
        "sem_biometria_alta",
        "biografica_alta",
        "identificacao_lenta",
        "cancelamentos_habilitacao",
    ],
    "Tempo de votação": [
        "tempo_lento",
        "retomadas_inatividade",
        "suspensoes",
        "tempo_rapido",
        "processo_rapido",
        "cadencia_rapida",
        "rajada_rapida",
    ],
    "Interrupções e inspeções": ["inspecao_prolongada", "intervalo_longo"],
    "Conferência do arquivo": [
        "assinatura",
        "relogio",
        "contagem_divergente",
        "biometria_divergente",
        "zeresima_ausente",
        "texto_malformado",
        "identidade_nao_confirmada",
    ],
}
INTEGRIDADE = [
    "assinatura",
    "contagem_divergente",
    "biometria_divergente",
    "zeresima_ausente",
    "identidade_nao_confirmada",
    "relogio",
    "texto_malformado",
]
TAMANHOS = [-1, 49, 99, 149, 199, 249, 299, 349, 10_000]
ROT_TAM = [
    "<50",
    "50-99",
    "100-149",
    "150-199",
    "200-249",
    "250-299",
    "300-349",
    "350+",
]


# ---------------------------------------------------------------- formatação
def num(x, casas=0):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/d"
    s = f"{x:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, casas=1):
    return num(x, casas) + "%"


def tabela(df: pd.DataFrame, casas: dict | None = None) -> str:
    casas = casas or {}
    cab = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    linhas = [cab, sep]
    for r in df.itertuples(index=False, name=None):
        cel = []
        for c, v in zip(df.columns, r, strict=True):
            if isinstance(v, (bool, np.bool_)):
                cel.append("sim" if v else "não")
            elif isinstance(v, (int, np.integer)):
                cel.append(num(int(v)))
            elif isinstance(v, (float, np.floating)):
                cel.append(num(float(v), casas.get(c, 2)))
            else:
                cel.append(str(v))
        linhas.append("| " + " | ".join(cel) + " |")
    return "\n".join(linhas)


# ---------------------------------------------------------------- carga
def carregar():
    CACHE.mkdir(exist_ok=True)
    p = CACHE / "secoes.pkl"
    if not p.exists():
        pd.read_csv(
            PUB / "secoes.csv.gz",
            dtype={"mun": str, "faixa_volume": str, "cargos": str},
            low_memory=False,
        ).to_pickle(p)
    df = pd.read_pickle(p)
    p = CACHE / "processos.pkl"
    if not p.exists():
        pd.read_csv(
            PUB / "processos_por_tipo.csv.gz", dtype={"mun": str, "cargos": str}
        ).to_pickle(p)
    pt = pd.read_pickle(p)
    indice = json.loads((PUB / "indice.json").read_text())
    return df, pt, indice


def carregar_metricas():
    p = CACHE / "metricas_extra.pkl"
    if not p.exists():
        con = sqlite3.connect(f"file:{METRICAS}?mode=ro", uri=True)
        m = pd.read_sql_query(
            "SELECT upper(uf) AS uf, mun, zona, secao, "
            "json_extract(resumo,'$.contagens.eventos_bateria') AS eventos_bateria, "
            "json_extract(resumo,'$.contagens.partidas_sistema') AS partidas_sistema, "
            "json_extract(resumo,'$.primeiro_computo_s') AS primeiro_computo_s, "
            "json_extract(resumo,'$.ultimo_computo_s') AS ultimo_computo_s "
            "FROM metricas",
            con,
        )
        con.close()
        m.to_pickle(p)
    return pd.read_pickle(p)


def carregar_politize():
    p, q = CACHE / "politize_tam.pkl", CACHE / "mun_nomes.pkl"
    if not p.exists():
        rows, nomes = [], {}
        for arq in glob.glob(str(POLITIZE / "*" / "*.json")):
            d = json.loads(Path(arq).read_text())
            for m in d["municipios"]:
                nomes[(d["uf"], m["mun_tse"])] = m["nome"]
            c = d["secoes"]["colunas"]
            ix = [c.index(k) for k in ("secao", "mun_tse", "comparecimento")]
            for linha in d["secoes"]["linhas"]:
                rows.append((d["uf"], int(d["zona"]), *(linha[i] for i in ix)))
        pd.DataFrame(
            rows, columns=["uf", "zona", "secao", "mun", "comp_politize"]
        ).to_pickle(p)
        pd.Series(nomes).rename_axis(["uf", "mun"]).rename(
            "nome"
        ).reset_index().to_pickle(q)
    return pd.read_pickle(p), pd.read_pickle(q)


# ---------------------------------------------------------------- ZIPs originais
def _bateria_lote(chaves):
    con = sqlite3.connect(f"file:{RAW}?mode=ro", uri=True)
    out = []
    for uf, mun, zona, secao in chaves:
        blob = con.execute(
            "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
            (uf.lower(), mun, int(zona), int(secao)),
        ).fetchone()[0]
        reg = {
            "uf": uf,
            "mun": mun,
            "zona": int(zona),
            "secao": int(secao),
            "eventos": set(),
            "zeresima": None,
            "encerramento": None,
        }
        for _, txt in textos_zip(blob):
            for linha in txt.splitlines():
                a = linha.split("\t")
                if len(a) != 6 or not a[0].startswith(DIAS):
                    continue
                try:
                    t = segundos(a[0])
                except (ValueError, IndexError, KeyError):
                    continue
                msg = a[4]
                baixa = msg.lower()
                if "operando" in baixa and "bateria interna" in baixa:
                    reg["eventos"].add((t, a[3]))
                elif msg == "Gerando relatório [ZERÉSIMA] [TÉRMINO]":
                    reg["zeresima"] = min(t, reg["zeresima"] or t)
                elif msg == "Procedimento de encerramento confirmado":
                    reg["encerramento"] = min(t, reg["encerramento"] or t)
        reg["eventos"] = sorted(reg["eventos"])
        out.append(reg)
    con.close()
    return out


def eventos_bateria(df):
    p = CACHE / "bateria_eventos.json"
    if not p.exists():
        alvo = df[df.S_bateria]
        chaves = list(alvo[CHAVE].itertuples(index=False, name=None))
        lotes = [chaves[i : i + 500] for i in range(0, len(chaves), 500)]
        res = []
        with Pool(12) as pool:
            for parte in pool.imap_unordered(_bateria_lote, lotes):
                res.extend(parte)
        p.write_text(json.dumps(res))
    return json.loads(p.read_text())


PADROES = {
    "solicita_digital": "Solicita digital. Tentativa",
    "capturada_digital": "Capturada a digital. Tentativa",
    "nao_corresponde": "Digital capturada não corresponde a digital do eleitor",
    "dado_pessoal_manual": "Solicitação de dado pessoal do eleitor para habilitação manual",
    "mesario_habilitou": "habilitou o eleitor",
    "ano_nasc_igual": "Ano de nascimento digitado é igual ao do cadastro",
}


def vocabulario_bateria(df):
    """Modelos de mensagem com "bateria" (dígitos trocados por #) em 10 seções
    marcadas por modelo, sorteadas com semente fixa. Só contagens agregadas."""
    p = CACHE / "vocabulario_bateria.csv"
    if not p.exists():
        con = sqlite3.connect(f"file:{RAW}?mode=ro", uri=True)
        cont = Counter()
        secoes = Counter()
        for modelo in ("UE2013", "UE2015", "UE2020", "UE2022"):
            amostra = df[df.S_bateria & (df.modelo == modelo)].sample(
                10, random_state=5
            )
            for r in amostra.itertuples():
                blob = con.execute(
                    "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
                    (r.uf.lower(), r.mun, int(r.zona), int(r.secao)),
                ).fetchone()[0]
                vistos = set()
                for _, txt in textos_zip(blob):
                    for linha in txt.splitlines():
                        a = linha.split("\t")
                        if len(a) != 6 or not a[0].startswith(DIAS):
                            continue
                        if "bateria" not in a[4].lower():
                            continue
                        modelo_msg = re.sub(r"\d+(?:[.,]\d+)?", "#", a[4])
                        chave = (modelo, a[3], a[1], modelo_msg)
                        cont[chave] += 1
                        if chave not in vistos:
                            secoes[chave] += 1
                            vistos.add(chave)
        con.close()
        pd.DataFrame(
            [
                {
                    "modelo": k[0],
                    "aplicativo": k[1],
                    "nível": k[2],
                    "mensagem": k[3],
                    "conta na regra": "operando" in k[3].lower()
                    and "bateria interna" in k[3].lower(),
                    "seções (de 10)": secoes[k],
                    "mensagens": v,
                }
                for k, v in cont.items()
            ]
        ).to_csv(p, index=False)
    return pd.read_csv(p)


def mensagens_habilitacao(df):
    """Contagens agregadas por tipo de mensagem; nada individual é guardado."""
    p = CACHE / "biografica_mensagens.csv"
    if not p.exists():
        b = df[df.biometria_status == "confere"]
        grupos = [
            b[b.biografica_pct >= 90].assign(grupo="biográfica >= 90%"),
            b[(b.modelo == "UE2013") & (b.biografica_pct < 20) & (b.uf != "ZZ")]
            .sample(300, random_state=11)
            .assign(grupo="controle UE2013 (< 20%)"),
            b[b.modelo.isin(["UE2020", "UE2022"]) & (b.biografica_pct < 20)]
            .sample(300, random_state=12)
            .assign(grupo="controle UE2020/UE2022 (< 20%)"),
        ]
        con = sqlite3.connect(f"file:{RAW}?mode=ro", uri=True)
        out = []
        for _, r in pd.concat(grupos).iterrows():
            blob = con.execute(
                "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
                (r.uf.lower(), r.mun, int(r.zona), int(r.secao)),
            ).fetchone()[0]
            c = dict.fromkeys(PADROES, 0)
            vistos = set()
            for _, txt in textos_zip(blob):
                for linha in txt.splitlines():
                    a = linha.split("\t")
                    if len(a) != 6 or not a[0].startswith(DIAS[0]) or linha in vistos:
                        continue
                    vistos.add(linha)
                    for k, padrao in PADROES.items():
                        if padrao in a[4]:
                            c[k] += 1
            out.append(
                {
                    "grupo": r.grupo,
                    "modelo": r.modelo,
                    "computados": int(r.computados),
                    "biograficas_bu": r.biograficas_bu,
                    **c,
                }
            )
        con.close()
        pd.DataFrame(out).to_csv(p, index=False)
    return pd.read_csv(p)


# ---------------------------------------------------------------- referências
def referencias(df, coluna, grupos, elegivel, piso):
    """Cópia literal de scripts/apuracao_logs/criterios.py::referencias."""
    t = df.assign(_x=pd.to_numeric(df[coluna], errors="coerce").where(elegivel))
    g = t.groupby(grupos)["_x"]
    med = g.transform("median")
    n = g.transform("count")
    desvios = (t["_x"] - med).abs()
    mad = t.assign(_d=desvios).groupby(grupos)["_d"].transform("median")
    escala = (1.4826 * mad).clip(lower=piso)
    return pd.DataFrame({"ref": med.where(n >= 30), "escala": escala, "n": n})


# ---------------------------------------------------------------- Q1
def q1(df, pt, indice):
    R = {"conferencia": [], "linhas": [], "frases": {}}
    el = df.elegivel_tempo
    ok = df.cadencia_elegivel
    # 1. Reprodução das referências publicadas a partir do próprio CSV
    checks = [
        ("voto", "voto_mediana", ["uf", "modelo", "cargos"], el),
        ("cadencia", "cadencia_mediana", ["uf", "modelo", "cargos"], ok),
        ("rajada", "rajada10_s", ["uf", "modelo", "cargos", "faixa_volume"], ok),
    ]
    for nome, col, gr, e in checks:
        r = referencias(df, col, gr, e, 3)
        R["conferencia"].append(
            (
                f"referencia_{nome}",
                bool(np.allclose(r.ref, df[f"referencia_{nome}"], equal_nan=True)),
                bool(
                    np.allclose(
                        r.escala.where(r.ref.notna()),
                        df[f"escala_{nome}"],
                        equal_nan=True,
                    )
                ),
            )
        )
    m = pt.merge(df[[*CHAVE, "processo_elegivel", "elegivel_bio"]], on=CHAVE)
    tipos = {}
    for tipo in ("biometrica", "biografica", "sem_biometria"):
        s = m[m.tipo == tipo].reset_index(drop=True)
        e = s.processo_elegivel & s.elegivel_bio & (s.n >= 30)
        r = referencias(s, "mediana_s", ["uf", "modelo", "cargos"], e, 3)
        R["conferencia"].append(
            (
                f"processo_{tipo}",
                bool(np.allclose(r.ref, s.referencia_mediana_s, equal_nan=True)),
                bool(
                    np.allclose(
                        r.escala.where(r.ref.notna()), s.escala_s, equal_nan=True
                    )
                ),
            )
        )
        tipos[tipo] = s
    # Controle positivo: as mesmas regras reproduzem os diagnósticos não nulos.
    v_ref, v_esc = df.referencia_voto, df.escala_voto
    R["controle_lento"] = int(
        (
            el & (df.voto_mediana > v_ref + K * v_esc) & (df.voto_mediana > 1.5 * v_ref)
        ).sum()
    )
    R["controle_ident"] = int(
        (
            el
            & (df.n_habilitacao >= 30)
            & (
                df.habilitacao_mediana
                > df.referencia_habilitacao + K * df.escala_habilitacao
            )
            & (df.habilitacao_mediana >= df.referencia_habilitacao + 20)
        ).sum()
    )
    # Controle por injeção: seção fictícia a 45% da referência no maior grupo.
    grupo = df[el].groupby(["uf", "modelo", "cargos"]).size().idxmax()
    filtro = (df.uf == grupo[0]) & (df.modelo == grupo[1]) & (df.cargos == grupo[2])
    base = df[filtro & el][["uf", "modelo", "cargos", "voto_mediana"]].copy()
    ref0 = base.voto_mediana.median()
    falsa = pd.DataFrame(
        [
            {
                "uf": grupo[0],
                "modelo": grupo[1],
                "cargos": grupo[2],
                "voto_mediana": 0.45 * ref0,
            }
        ]
    )
    inj = pd.concat([base, falsa], ignore_index=True)
    todas = pd.Series(True, index=inj.index)
    ri = referencias(inj, "voto_mediana", ["uf", "modelo", "cargos"], todas, 3)
    xi = inj.voto_mediana.iloc[-1]
    R["injecao"] = {
        "grupo": " × ".join(map(str, grupo)),
        "n": len(base),
        "ref": float(ri.ref.iloc[-1]),
        "escala": float(ri.escala.iloc[-1]),
        "x": float(xi),
        "dispara": bool(
            (xi < ri.ref.iloc[-1] - K * ri.escala.iloc[-1])
            and (xi < 0.5 * ri.ref.iloc[-1])
        ),
    }

    def avalia(nome, frame, col, refc, escc, e, grupos, extra=None):
        E = e & frame[refc].notna() & frame[col].notna()
        x, ref, esc = frame[col], frame[refc], frame[escc]
        z = (x - ref) / esc
        razao = x / ref
        limiar = np.minimum(ref - K * esc, 0.5 * ref)
        if extra is not None:
            limiar = np.minimum(limiar, extra)
        fator = (x / limiar).where(limiar > 0)  # >1: ainda não dispara
        gb = [frame[g] for g in grupos]
        q = x.where(E).groupby(gb).transform(lambda s: s.quantile(0.001))
        lx = np.log(x.where(E & (x > 0)))
        lmed = lx.groupby(gb).transform("median")
        lmad = (lx - lmed).abs().groupby(gb).transform("median") * 1.4826
        zl = (lx - lmed) / lmad
        flags = {
            "z_lt4": E & (z < -K),
            "z_le4": E & (z <= -K),
            "z_lt3": E & (z < -3),
            "z_lt5": E & (z < -5),
            "razao_lt05": E & (razao < 0.5),
            "ambos3": E & (z < -3) & (razao < 0.5),
            "ambos4": E & (z < -K) & (razao < 0.5),
            "pct01": E & (x < q),
            "logz4": E & (zl < -4),
            "logz3": E & (zl < -3),
            "razao_lt07": E & (razao < 0.7),
        }
        if extra is not None:
            flags["ambos4"] &= x < extra
            flags["ambos3"] &= x < extra
        iz, ir, iff = z[E].idxmin(), razao[E].idxmin(), fator[E].idxmin()

        def ident(i):
            r = frame.loc[i]
            return f"{r.uf}, zona {int(r.zona)}, seção {int(r.secao)}, mun. {r.mun}"

        linha = {
            "diag": nome,
            "avaliaveis": int(E.sum()),
            "grupos": int(frame[E].groupby(grupos).ngroups),
            "z_min": float(z[E].min()),
            "z_min_secao": ident(iz),
            "z_min_x": float(x[iz]),
            "z_min_ref": float(ref[iz]),
            "z_min_esc": float(esc[iz]),
            "z_min_razao": float(razao[iz]),
            "razao_min": float(razao[E].min()),
            "razao_min_secao": ident(ir),
            "razao_min_z": float(z[ir]),
            "fator_min": float(fator[E].min()),
            "fator_secao": ident(iff),
            "fator_x": float(x[iff]),
            "fator_ref": float(ref[iff]),
            "fator_esc": float(esc[iff]),
            "metade_mais_exigente_pct": float(
                100 * ((0.5 * ref) < (ref - K * esc))[E].mean()
            ),
            "z_exigido_metade_mediana": float((-0.5 * ref / esc)[E].median()),
            "cv_mediano": float((esc / ref)[E].median()),
            "grupos_impossiveis_secoes": int((E & (ref - K * esc <= 0)).sum()),
            "grupos_impossiveis": sorted(
                {
                    " × ".join(map(str, t))
                    for t in frame.loc[E & (ref - K * esc <= 0), grupos].itertuples(
                        index=False, name=None
                    )
                }
            ),
            "logz_min": float(zl[E].min()),
        }
        return linha, flags, E

    linhas, flags_all = [], {}
    for nome, frame, col, refc, escc, e, gr, extra in (
        (
            "tempo_rapido",
            df,
            "voto_mediana",
            "referencia_voto",
            "escala_voto",
            el,
            ["uf", "modelo", "cargos"],
            None,
        ),
        (
            "cadencia_rapida",
            df,
            "cadencia_mediana",
            "referencia_cadencia",
            "escala_cadencia",
            ok,
            ["uf", "modelo", "cargos"],
            None,
        ),
        (
            "rajada_rapida",
            df,
            "rajada10_s",
            "referencia_rajada",
            "escala_rajada",
            ok,
            ["uf", "modelo", "cargos", "faixa_volume"],
            0.5 * df.cadencia_mediana,
        ),
    ):
        linha, fl, E = avalia(nome, frame, col, refc, escc, e, gr, extra)
        linhas.append(linha)
        flags_all[nome] = {k: int(v.sum()) for k, v in fl.items()}
    proc = {}
    for tipo, s in tipos.items():
        linha, fl, E = avalia(
            f"processo_rapido ({tipo})",
            s,
            "mediana_s",
            "referencia_mediana_s",
            "escala_s",
            s.elegivel,
            ["uf", "modelo", "cargos"],
        )
        linhas.append(linha)
        flags_all[linha["diag"]] = {k: int(v.sum()) for k, v in fl.items()}
        proc[tipo] = (s, fl, E)
    # União por seção para processo_rapido
    uni = {}
    for k in flags_all["tempo_rapido"]:
        chaves = set()
        for s, fl, _ in proc.values():
            chaves |= set(map(tuple, s.loc[fl[k], CHAVE].itertuples(index=False)))
        uni[k] = len(chaves)
    av = set()
    for s, _, E in proc.values():
        av |= set(map(tuple, s.loc[E, CHAVE].itertuples(index=False)))
    flags_all["processo_rapido (seções, união)"] = uni
    R["proc_avaliaveis"] = len(av)
    R["linhas"] = linhas
    R["flags"] = flags_all
    R["indice_aval"] = {
        k: indice["criterios"][k]["avaliaveis"]
        for k in ("tempo_rapido", "cadencia_rapida", "rajada_rapida", "processo_rapido")
    }
    R["indice_secoes"] = {k: indice["criterios"][k]["secoes"] for k in R["indice_aval"]}
    R["sens"] = {
        c: {
            k: indice["sensibilidade"][c]["criterios"].get(k, 0)
            for k in R["indice_aval"]
        }
        for c in ("3", "4", "5")
    }
    return R


# ---------------------------------------------------------------- Q2
def coincidencias(v, janela=60):
    v = v.sort_values(["uf", "mun", "t"]).reset_index(drop=True)
    res = np.zeros(len(v), dtype=int)
    for _, g in v.groupby(["uf", "mun"], sort=False):
        t, s, idx = g.t.to_numpy(), g.sid.to_numpy(), g.index.to_numpy()
        lo = np.searchsorted(t, t - janela, "left")
        hi = np.searchsorted(t, t + janela, "right")
        for k in range(len(t)):
            if hi[k] - lo[k] > 1:
                res[idx[k]] = len(set(s[lo[k] : hi[k]].tolist()) - {s[k]})
    v["outras"] = res
    return v.groupby("sid").outras.max()


def mantel_haenszel(df, a, b, col):
    num = den = 0.0
    zonas = 0
    for _, g in df[df.modelo.isin([a, b])].groupby(["uf", "zona"]):
        if g.modelo.nunique() < 2:
            continue
        zonas += 1
        n = len(g)
        ga, gb = g.modelo == a, g.modelo == b
        num += (ga & g[col]).sum() * (gb & ~g[col]).sum() / n
        den += (ga & ~g[col]).sum() * (gb & g[col]).sum() / n
    return zonas, num / den


def q2(df, ev):
    R = {}
    rows = [
        (
            r["uf"],
            r["mun"],
            r["zona"],
            r["secao"],
            t,
            app,
            r["zeresima"],
            r["encerramento"],
        )
        for r in ev
        for t, app in r["eventos"]
    ]
    # Ordem fixa: o cache vem de processos paralelos e o nulo usa sorteio.
    E = (
        pd.DataFrame(rows, columns=[*CHAVE, "t", "app", "zer", "enc"])
        .sort_values([*CHAVE, "t", "app"])
        .reset_index(drop=True)
    )
    E = E.merge(
        df[
            [
                *CHAVE,
                "modelo",
                "primeiro_computo_s",
                "ultimo_computo_s",
                "eventos_bateria",
            ]
        ],
        on=CHAVE,
    )
    n_ext = E.groupby(CHAVE).size()
    comp = df.set_index(CHAVE).loc[n_ext.index, "eventos_bateria"]
    R["conf_contagem"] = (int((n_ext == comp).sum()), len(n_ext))

    fase = np.select(
        [
            E.zer.notna() & (E.t < E.zer),
            E.primeiro_computo_s.notna() & (E.t < E.primeiro_computo_s),
            E.enc.notna() & (E.t > E.enc),
            E.ultimo_computo_s.notna() & (E.t > E.ultimo_computo_s),
        ],
        [
            "antes da zerésima",
            "zerésima ao 1º voto",
            "após encerramento",
            "após o último voto",
        ],
        "durante a votação",
    )
    E["fase"] = fase
    R["fase_app"] = pd.crosstab(E.app, E.fase)
    R["fase_modelo"] = pd.crosstab(E.modelo, E.fase, margins=True, margins_name="Total")

    def classe(s):
        if "durante a votação" in s:
            return "durante a votação"
        if "zerésima ao 1º voto" in s:
            return "entre zerésima e 1º voto"
        if "antes da zerésima" in s:
            return "só antes da zerésima"
        return "só após o último voto"

    cl = E.groupby(CHAVE).fase.agg(lambda s: classe(set(s))).rename("classe")
    df = df.merge(cl.reset_index(), on=CHAVE, how="left")
    df["bat_voto"] = df.classe.eq("durante a votação")
    R["classe"] = df.classe.value_counts()

    # Contagem por sessão do VOTA: indício de teto de 10 mensagens
    vota = E[E.app == "VOTA"].groupby(CHAVE).size().rename("vota").reset_index()
    vota = vota.merge(df[[*CHAVE, "partidas_sistema"]], on=CHAVE)
    um = vota[vota.partidas_sistema == 1]
    R["teto"] = {
        "secoes_1_partida": len(um),
        "eq10": int((um.vota == 10).sum()),
        "eq9": int((um.vota == 9).sum()),
        "gt10": int((um.vota > 10).sum()),
    }

    # Simultaneidade no município (±60 s) contra nulo uniforme na janela da seção
    v = E[E.fase == "durante a votação"].copy()
    v["sid"] = v.groupby(CHAVE).ngroup()
    obs = coincidencias(v)
    rng = np.random.default_rng(42)
    nul = v.copy()
    lo, hi = nul.primeiro_computo_s.to_numpy(), nul.ultimo_computo_s.to_numpy()
    nul["t"] = np.floor(lo + rng.random(len(nul)) * (hi - lo)).astype(int)
    nulo = coincidencias(nul)
    R["simult"] = {
        "secoes": len(obs),
        "obs0": int((obs == 0).sum()),
        "obs1_4": int(((obs >= 1) & (obs <= 4)).sum()),
        "obs5": int((obs >= 5).sum()),
        "obs20": int((obs >= 20).sum()),
        "nulo5": float((nulo >= 5).mean()),
        "nulo20": float((nulo >= 20).mean()),
        "nulo0": float((nulo == 0).mean()),
    }
    sid_chave = v.drop_duplicates("sid").set_index("sid")[CHAVE]
    sim = sid_chave.assign(simult5=(obs >= 5)).reset_index(drop=True)
    df = df.merge(sim, on=CHAVE, how="left")
    df["simult5"] = df.simult5.eq(True)

    u = df.groupby("uf").agg(
        secoes=("S_bateria", "size"),
        bateria=("S_bateria", "sum"),
        durante=("bat_voto", "sum"),
        simult=("simult5", "sum"),
    )
    u["% bateria"] = 100 * u.bateria / u.secoes
    u["% durante votação"] = 100 * u.durante / u.secoes
    u["% simultânea (das durante)"] = 100 * u.simult / u.durante.replace(0, np.nan)
    R["uf"] = u.sort_values("% bateria", ascending=False)
    mo = df.groupby("modelo").agg(
        secoes=("S_bateria", "size"),
        bateria=("S_bateria", "sum"),
        durante=("bat_voto", "sum"),
    )
    mo["% bateria"] = 100 * mo.bateria / mo.secoes
    mo["% durante votação"] = 100 * mo.durante / mo.secoes
    R["modelo"] = mo
    R["mh"] = {
        f"{a} × UE2020": {
            "bateria": mantel_haenszel(df, a, "UE2020", "S_bateria"),
            "durante": mantel_haenszel(df, a, "UE2020", "bat_voto"),
        }
        for a in ("UE2022", "UE2015", "UE2013")
    }
    z = df.groupby(["uf", "zona"]).agg(
        n=("S_bateria", "size"), b=("S_bateria", "mean"), bv=("bat_voto", "mean")
    )
    R["zonas"] = (len(z), int((z.b > 0.5).sum()), int((z.bv > 0.5).sum()))
    mm = df.groupby(["uf", "mun"]).agg(n=("S_bateria", "size"), bv=("bat_voto", "mean"))
    R["mun"] = (int((mm.n >= 20).sum()), int(((mm.n >= 20) & (mm.bv > 0.5)).sum()))
    hora = E[(E.fase == "durante a votação") & (E.uf != "ZZ")].t // 3600
    R["hora"] = hora.value_counts().sort_index()
    df["tam"] = pd.cut(df.comparecimento, TAMANHOS, labels=ROT_TAM)
    R["tam"] = df.groupby("tam", observed=True).agg(
        secoes=("S_bateria", "size"),
        pct=("S_bateria", "mean"),
        pct_v=("bat_voto", "mean"),
    )
    R["n_ev"] = df.loc[df.S_bateria, "eventos_bateria"]
    return R, df


# ---------------------------------------------------------------- Q3
def q3(df, nomes, msgs):
    R = {}
    b = df[df.biometria_status == "confere"]
    R["nac"] = {
        "secoes": len(b),
        "sem": b.sem_biometria_bu.sum(),
        "comp": b.comparecimento.sum(),
        "bio": b.biometricas_bu.sum(),
        "bg": b.biograficas_bu.sum(),
    }
    R["status"] = df.biometria_status.value_counts()
    ok_sb = df.elegivel_bio & df.modelo_comparavel & (df.comparecimento >= 50)
    ok_bg = df.elegivel_bio & df.modelo_comparavel & (df.den_bio >= 50)
    R["aval"] = {
        "sb": int((ok_sb & df.referencia_sem_biometria.notna()).sum()),
        "bg": int((ok_bg & df.referencia_biografica.notna()).sum()),
        "sb_sem_ref": int((ok_sb & df.referencia_sem_biometria.isna()).sum()),
        "bg_sem_ref": int((ok_bg & df.referencia_biografica.isna()).sum()),
        "sb_ok": int(ok_sb.sum()),
        "bg_ok": int(ok_bg.sum()),
    }
    g = b.groupby("uf")
    u = pd.DataFrame(
        {
            "seções": g.size(),
            "taxa sem bio %": 100 * g.sem_biometria_bu.sum() / g.comparecimento.sum(),
            "mediana sem bio %": g.sem_biometria_pct.median(),
            "p90 sem bio %": g.sem_biometria_pct.quantile(0.9),
            "ref. mediana %": df[ok_sb].groupby("uf").referencia_sem_biometria.median(),
            "sem_biometria_alta": df.groupby("uf").S_sem_biometria_alta.sum(),
            "taxa biográfica %": 100
            * g.biograficas_bu.sum()
            / (g.biometricas_bu.sum() + g.biograficas_bu.sum()),
            "mediana biográfica %": g.biografica_pct.median(),
            "biografica_alta": df.groupby("uf").S_biografica_alta.sum(),
        }
    )
    u = u.loc[g.size().index]
    for c in ("seções", "sem_biometria_alta", "biografica_alta"):
        u[c] = u[c].astype(int)
    u["% sem_bio_alta"] = 100 * u.sem_biometria_alta / u["seções"]
    u["% biog_alta"] = 100 * u.biografica_alta / u["seções"]
    R["uf"] = u.sort_values("mediana sem bio %", ascending=False)
    R["corr_uf"] = float(np.corrcoef(u["mediana sem bio %"], u["% sem_bio_alta"])[0, 1])
    mo = df.groupby("modelo").agg(
        secoes=("S_bateria", "size"),
        sem_bio_alta=("S_sem_biometria_alta", "sum"),
        biog_alta=("S_biografica_alta", "sum"),
        mediana_sem_bio=("sem_biometria_pct", "median"),
        mediana_biog=("biografica_pct", "median"),
    )
    R["modelo"] = mo
    t = df.groupby("tam", observed=True).agg(
        secoes=("S_bateria", "size"),
        sem_bio_alta=("S_sem_biometria_alta", "sum"),
        biog_alta=("S_biografica_alta", "sum"),
        mediana_sem_bio=("sem_biometria_pct", "median"),
        mediana_biog=("biografica_pct", "median"),
    )
    R["tam"] = t
    cf = []
    for campo, ok in (("sem_biometria_pct", ok_sb), ("biografica_pct", ok_bg)):
        for nome, gr in (
            (
                "publicada: UF × município × zona × modelo",
                ["uf", "mun", "zona", "modelo"],
            ),
            ("UF × modelo", ["uf", "modelo"]),
            ("Brasil × modelo", ["modelo"]),
        ):
            r = referencias(df, campo, gr, ok, 1)
            f = ok & (df[campo] > r.ref + K * r.escala) & (df[campo] >= r.ref + 10)
            top = f.groupby(df.uf).sum().sort_values(ascending=False).head(4)
            cf.append(
                {
                    "medida": campo.replace("_pct", ""),
                    "referência": nome,
                    "sinalizadas": int(f.sum()),
                    "maiores UFs": ", ".join(f"{k} {v}" for k, v in top.items()),
                    "_top": list(top.index),
                }
            )
    R["contrafactual"] = pd.DataFrame(cf)
    for campo, flag, refc in (
        ("sem_biometria_pct", "S_sem_biometria_alta", "referencia_sem_biometria"),
        ("biografica_pct", "S_biografica_alta", "referencia_biografica"),
    ):
        hi = b[campo] >= 50
        resto = hi & ~b[flag] & b[refc].notna()
        R[f"ge50_{campo}"] = (
            int(hi.sum()),
            int((hi & b[flag]).sum()),
            int((hi & b[refc].isna()).sum()),
            int(resto.sum()),
            float(b.loc[resto, refc].median()),
        )
    hi90 = b.biografica_pct >= 90
    R["bg90"] = {
        "total": int(hi90.sum()),
        "modelo": b[hi90].modelo.value_counts(),
        "sinalizadas": int((hi90 & b.S_biografica_alta).sum()),
        "sem_ref": int((hi90 & b.referencia_biografica.isna()).sum()),
        "den_lt50": int((hi90 & (b.den_bio < 50)).sum()),
        "ue2013_secoes": int((df.modelo == "UE2013").sum()),
    }
    bb = b.merge(nomes, on=["uf", "mun"], how="left")
    bb["município"] = bb.nome.fillna(bb.mun)
    top_sb = bb.sort_values("sem_biometria_pct", ascending=False).head(20)
    R["top_sb"] = top_sb[
        [
            "uf",
            "zona",
            "município",
            "secao",
            "modelo",
            "comparecimento",
            "sem_biometria_pct",
            "referencia_sem_biometria",
            "escala_sem_biometria",
            "pares_sem_biometria",
            "S_sem_biometria_alta",
        ]
    ].rename(
        columns={
            "sem_biometria_pct": "sem bio %",
            "referencia_sem_biometria": "ref. %",
            "escala_sem_biometria": "escala pp",
            "pares_sem_biometria": "pares",
            "S_sem_biometria_alta": "sinalizada",
        }
    )
    top_bg = bb.sort_values("biografica_pct", ascending=False).head(20)
    R["top_bg"] = top_bg[
        [
            "uf",
            "zona",
            "município",
            "secao",
            "modelo",
            "comparecimento",
            "den_bio",
            "biografica_pct",
            "referencia_biografica",
            "escala_biografica",
            "pares_biometria",
            "S_biografica_alta",
        ]
    ].rename(
        columns={
            "den_bio": "bio+biog",
            "biografica_pct": "biog. %",
            "referencia_biografica": "ref. %",
            "escala_biografica": "escala pp",
            "pares_biometria": "pares",
            "S_biografica_alta": "sinalizada",
        }
    )
    cols = list(PADROES)
    mm = msgs.copy()
    for c in cols:
        mm[c] = mm[c] / mm.computados
    mm["biográficas/cômputos"] = mm.biograficas_bu / mm.computados
    R["msgs"] = mm.groupby("grupo")[["biográficas/cômputos", *cols]].median()
    R["msgs_n"] = mm.groupby("grupo").size()
    return R


# ---------------------------------------------------------------- Q4 e Q5
def q4_q5(df, S):
    R = {}
    cols = list(S.columns)
    C = S.T.astype(int) @ S.astype(int)
    R["matriz"] = C
    n = np.diag(C)
    pares = []
    for i, a in enumerate(cols):
        for j in range(i + 1, len(cols)):
            b = cols[j]
            ab = int(C.iloc[i, j])
            if ab == 0:
                continue
            pares.append(
                {
                    "par": f"{a} × {b}",
                    "ambos": ab,
                    "n_a": int(n[i]),
                    "n_b": int(n[j]),
                    "Jaccard": ab / (n[i] + n[j] - ab),
                    "P(b|a)": ab / n[i],
                    "P(a|b)": ab / n[j],
                    "lift": ab * len(S) / (n[i] * n[j]),
                }
            )
    R["pares"] = pd.DataFrame(pares).sort_values("Jaccard", ascending=False)
    R["especificos"] = {
        "reinicio_sistema sem reinicios": int(
            (S.reinicio_sistema & ~S.reinicios).sum()
        ),
        "reinicios sem reinicio_sistema": int(
            (S.reinicios & ~S.reinicio_sistema).sum()
        ),
        "ciclos_incompletos sem reinício": int(
            (S.ciclos_incompletos & ~S.reinicios & ~S.reinicio_sistema).sum()
        ),
        "erro_tecnico sem reinício": int(
            (S.erro_tecnico & ~S.reinicios & ~S.reinicio_sistema).sum()
        ),
        "contagem_divergente == biometria_divergente": bool(
            (S.contagem_divergente == S.biometria_divergente).all()
        ),
    }
    fam = {f: [c for c in cs if c in S.columns] for f, cs in FAMILIAS.items()}
    F = pd.DataFrame({f: S[c].any(axis=1) for f, c in fam.items()})
    so_bat = (S.sum(axis=1) == 1) & S.bateria
    R["familias"] = pd.DataFrame(
        {
            "sinais ativos": [", ".join(c) for c in fam.values()],
            "seções": F.sum().astype(int).values,
            "só esta família": [int((F[f] & (F.sum(axis=1) == 1)).sum()) for f in F],
        },
        index=F.columns,
    )
    R["so_bateria"] = int(so_bat.sum())
    R["nfam"] = F.sum(axis=1).value_counts().sort_index()
    # Q5: famílias contadas sem a bateria (contexto de massa)
    Fx = pd.DataFrame(
        {f: S[[c for c in cs if c != "bateria"]].any(axis=1) for f, cs in fam.items()}
    )
    nfx = Fx.sum(axis=1)
    integ = S[INTEGRIDADE].any(axis=1)
    sem_bat = S.drop(columns="bateria").sum(axis=1)
    # inspeção breve: único sinal (fora bateria) é inspecao_prolongada com janela
    # máxima de 5 a 10 minutos (o diagnóstico já exige 300 s ou mais)
    so_insp_breve = (sem_bat == 1) & S.inspecao_prolongada & (df.inspecao_max < 600)
    nivel = pd.Series(
        np.select(
            [integ | (nfx >= 3), nfx == 2, (nfx == 1) & ~so_insp_breve], [3, 2, 1], 0
        ),
        index=S.index,
    )
    R["nivel"] = nivel
    R["nivel0"] = {
        "sem sinal": int((S.sum(axis=1) == 0).sum()),
        "só bateria": int(so_bat.sum()),
        "só inspeção breve (com ou sem bateria)": int(so_insp_breve.sum()),
    }
    R["nivel3"] = {
        "integridade": int(integ.sum()),
        "3+ famílias": int((nfx >= 3).sum()),
        "ambos": int((integ & (nfx >= 3)).sum()),
        "por sinal": S.loc[nivel == 3, INTEGRIDADE].sum(),
        "ZZ": int(((nivel == 3) & (df.uf == "ZZ")).sum()),
        "ZZ_relogio": int(((nivel == 3) & (df.uf == "ZZ") & S.relogio).sum()),
    }
    R["nivel1_fam"] = Fx[nivel == 1].sum()
    R["nivel1_so_insp"] = int(
        ((nivel == 1) & (sem_bat == 1) & S.inspecao_prolongada).sum()
    )
    so_int = (sem_bat == 1) & S.intervalo_longo
    R["nivel1_so_intervalo"] = (
        int((so_int & (nivel == 1)).sum()),
        int((so_int & (nivel == 1) & (df.comparecimento < 150)).sum()),
    )
    R["nivel2_pares"] = Counter(
        " + ".join(sorted(Fx.columns[Fx.loc[i]])) for i in nivel.index[nivel == 2]
    ).most_common(6)
    nf = F.sum(axis=1)
    var_b = np.select(
        [integ | (nf >= 3), nf == 2, (nf == 1) & ~so_bat & ~so_insp_breve], [3, 2, 1], 0
    )
    R["var_bateria"] = pd.Series(var_b).value_counts().sort_index()
    var_i = np.select([integ | (nfx >= 3), nfx == 2, nfx == 1], [3, 2, 1], 0)
    R["var_insp"] = pd.Series(var_i).value_counts().sort_index()
    R["so_insp_breve"] = int(so_insp_breve.sum())
    R["nivel_tam"] = pd.crosstab(df.tam, nivel, normalize="index") * 100
    R["nivel_uf"] = pd.crosstab(df.uf, nivel)
    return R


# ---------------------------------------------------------------- memorando
def escrever(df, R1, R2, R3, R45, indice, conf_politize):
    L = []
    w = L.append
    nsec = len(df)
    PP = R45["pares"].set_index("par")

    def par(x, y):
        return (
            PP.loc[f"{x} × {y}"] if f"{x} × {y}" in PP.index else PP.loc[f"{y} × {x}"]
        )

    pb_ = R45["pares"][
        R45["pares"].par.str.contains("bateria") & (R45["pares"].ambos >= 100)
    ]
    outros = pb_.lift
    top_bat = ", ".join(
        f"{r.par.replace('bateria × ', '')} {num(r.lift, 1)}"
        for r in pb_.sort_values("lift", ascending=False).head(3).itertuples()
    )
    w(
        "# Logs das urnas, 1º turno de 2026: diagnósticos sem disparo, bateria, "
        "biometria e régua de atenção\n"
    )
    w(
        f"Memorando interno de análise, somente leitura. Base: `secoes.csv.gz` com "
        f"{num(nsec)} seções lidas (`indice.json`, gerado em {indice['gerado_em'][:10]}, "
        f"versão do leitor {indice['versao_parser']}). Todo número abaixo sai de "
        f"`analise_logs.py`, no mesmo diretório. Atipicidade operacional não é "
        f"irregularidade; ALERTA não é ERRO; nenhuma conta usa voto em candidato.\n"
    )
    w(
        "Contagens publicadas conferidas: as 21 marcas com ocorrência na coluna "
        "`sinais` reproduzem exatamente `indice.json/criterios` (por exemplo, "
        f"bateria {num(indice['criterios']['bateria']['secoes'])}, "
        f"sinalizadas {num(indice['cobertura']['sinalizadas'])}).\n"
    )

    # ---------------- Q1
    w("## 1. Os quatro diagnósticos de rapidez com zero seções\n")
    w(
        "**Conferência de identificação.** As referências (mediana) e escalas "
        "(1,4826 × MAD com piso) foram recalculadas a partir do próprio CSV com a "
        "função de `criterios.py` e coincidem com as colunas publicadas em todos os "
        "casos:\n"
    )
    w(
        tabela(
            pd.DataFrame(
                R1["conferencia"],
                columns=["referência", "mediana confere", "escala confere"],
            )
        )
    )
    w("")
    ia = R1["indice_aval"]
    w(
        f"Avaliáveis recalculados contra `indice.json`: tempo_rapido "
        f"{num(R1['linhas'][0]['avaliaveis'])} ({num(ia['tempo_rapido'])} publicado), "
        f"cadencia_rapida {num(R1['linhas'][1]['avaliaveis'])} "
        f"({num(ia['cadencia_rapida'])}), rajada_rapida "
        f"{num(R1['linhas'][2]['avaliaveis'])} ({num(ia['rajada_rapida'])}), "
        f"processo_rapido {num(R1['proc_avaliaveis'])} seções na união dos três tipos "
        f"({num(ia['processo_rapido'])}).\n"
    )
    inj = R1["injecao"]
    w(
        f"**Controles positivos.** Com as mesmas colunas, as regras irmãs reproduzem "
        f"tempo_lento = {num(R1['controle_lento'])} e identificacao_lenta = "
        f"{num(R1['controle_ident'])}, iguais ao publicado. Uma seção fictícia "
        f"injetada no maior grupo ({inj['grupo']}, {num(inj['n'])} seções) com mediana "
        f"de {num(inj['x'], 1)} s, 45% da referência de {num(inj['ref'], 1)} s "
        f"(escala {num(inj['escala'], 2)} s), "
        f"{'dispara' if inj['dispara'] else 'NÃO dispara'} a regra. O mecanismo "
        f"identifica rapidez quando ela existe; o zero não é defeito de código, de "
        f"junção ou de valores ausentes.\n"
    )
    w(
        "**Distância até disparar.** z robusto = (valor − referência) / escala. "
        "Fator = valor / limiar efetivo, em que o limiar é o menor entre "
        "referência − 4 escalas e metade da referência (na rajada, também metade da "
        "cadência da própria seção); um fator f significa que a mediana precisaria cair "
        "uma fração 1 − 1/f para disparar.\n"
    )
    t = pd.DataFrame(
        [
            {
                "diagnóstico": r["diag"],
                "avaliáveis": r["avaliaveis"],
                "z mínimo": r["z_min"],
                "seção do z mínimo": r["z_min_secao"],
                "razão nessa seção": r["z_min_razao"],
                "razão mínima": r["razao_min"],
                "z nessa seção": r["razao_min_z"],
                "fator mínimo": r["fator_min"],
                "seção mais próxima (fator)": r["fator_secao"],
            }
            for r in R1["linhas"]
        ]
    )
    w(
        tabela(
            t,
            {
                "z mínimo": 2,
                "razão nessa seção": 3,
                "razão mínima": 3,
                "z nessa seção": 2,
                "fator mínimo": 3,
            },
        )
    )
    w("")
    t = pd.DataFrame(
        [
            {
                "diagnóstico": r["diag"],
                "valor (s)": r["fator_x"],
                "referência (s)": r["fator_ref"],
                "escala (s)": r["fator_esc"],
            }
            for r in R1["linhas"]
        ]
    )
    w("Valores da seção mais próxima de disparar em cada diagnóstico:\n")
    w(tabela(t, {"valor (s)": 1, "referência (s)": 1, "escala (s)": 2}))
    w("")
    w(
        "**Contagens com regras alternativas** (seções avaliáveis; na linha de "
        "processo por seção, união dos três tipos):\n"
    )
    rot = {
        "z_lt4": "z < −4 sem a metade",
        "z_le4": "z ≤ −4",
        "z_lt3": "z < −3 sem a metade",
        "razao_lt05": "só valor < metade",
        "ambos3": "regra completa, corte 3",
        "ambos4": "regra completa, corte 4",
        "razao_lt07": "valor < 0,7 × ref.",
        "logz4": "z em log < −4",
        "logz3": "z em log < −3",
        "pct01": "abaixo do percentil 0,1% do grupo",
    }
    t = pd.DataFrame(
        [
            {"diagnóstico": d, **{rot[k]: v[k] for k in rot}}
            for d, v in R1["flags"].items()
        ]
    )
    w(tabela(t))
    w("")
    s3 = R1["sens"]["3"]
    w(
        "Sensibilidade publicada em `indice.json` com corte 3: "
        + ", ".join(f"{k} {num(v)}" for k, v in s3.items())
        + ". A regra completa com corte 3 recalculada também dá zero nos quatro.\n"
    )
    t = pd.DataFrame(
        [
            {
                "diagnóstico": r["diag"],
                "metade é a condição mais exigente (% das seções)": r[
                    "metade_mais_exigente_pct"
                ],
                "z mediano exigido pela metade": r["z_exigido_metade_mediana"],
                "escala/referência mediana": r["cv_mediano"],
                "seções em grupo onde ref − 4 escalas ≤ 0": r[
                    "grupos_impossiveis_secoes"
                ],
                "z mínimo em log": r["logz_min"],
            }
            for r in R1["linhas"]
        ]
    )
    w("Peso de cada condição:\n")
    w(
        tabela(
            t,
            {
                "metade é a condição mais exigente (% das seções)": 1,
                "z mediano exigido pela metade": 2,
                "escala/referência mediana": 3,
                "z mínimo em log": 2,
            },
        )
    )
    w("")
    li = {r["diag"]: r for r in R1["linhas"]}
    fl = R1["flags"]
    w("**Leitura por diagnóstico.**\n")
    r = li["tempo_rapido"]
    w(
        f"- **tempo_rapido**: zero genuíno. Nenhuma seção tem mediana de votação abaixo "
        f"de metade da referência (razão mínima {num(r['razao_min'], 3)}), e mesmo sem a "
        f"condição da metade o z robusto mínimo é {num(r['z_min'], 2)}, exatamente no "
        f"corte, que a regra exige estrito (`<`); com `≤` seria "
        f"{num(fl['tempo_rapido']['z_le4'])} seção ({r['z_min_secao']}: mediana "
        f"{num(r['z_min_x'], 1)} s, referência {num(r['z_min_ref'], 1)} s, escala no "
        f"piso de {num(r['z_min_esc'], 1)} s; a metade exigiria menos de "
        f"{num(r['z_min_ref'] / 2, 1)} s). A metade é a condição mais exigente em "
        f"{num(r['metade_mais_exigente_pct'], 1)}% das seções, mas o zero se mantém sem "
        f"ela: a cauda inferior é curta."
    )
    r = li["cadencia_rapida"]
    w(
        f"- **cadencia_rapida**: zero genuíno e folgado. O z robusto "
        f"mínimo é {num(r['z_min'], 2)}; nenhuma seção chega a −3. A única com razão "
        f"abaixo de 0,5 ({r['razao_min_secao']}, razão {num(r['razao_min'], 3)}) está em "
        f"grupo tão disperso que fica a z {num(r['razao_min_z'], 2)}. Em "
        f"{num(r['grupos_impossiveis_secoes'])} seções, de "
        f"{num(len(r['grupos_impossiveis']))} "
        f"grupo{'s' if len(r['grupos_impossiveis']) != 1 else ''} "
        f"({', '.join(r['grupos_impossiveis'][:6])}"
        f"{', …' if len(r['grupos_impossiveis']) > 6 else ''}), a referência menos "
        f"4 escalas é negativa e a condição de 4 escalas é inatingível."
    )
    r = li["rajada_rapida"]
    w(
        f"- **rajada_rapida**: zero genuíno. É o diagnóstico que mais se aproxima: "
        f"{num(fl['rajada_rapida']['z_lt3'])} seções têm z < −3, mas nenhuma < −4 "
        f"(mínimo {num(r['z_min'], 2)}); a condição de metade da própria cadência "
        f"também elimina candidatos."
    )
    nomes_proc = [d for d in li if d.startswith("processo_rapido (")]
    zmins = ", ".join(
        f"{d.split('(')[1][:-1]} {num(li[d]['z_min'], 2)}" for d in nomes_proc
    )
    w(
        f"- **processo_rapido**: zero genuíno nos três tipos (z mínimo: {zmins}). Na "
        f"habilitação sem biometria a metade quase nunca é a condição mais exigente "
        f"({num(li['processo_rapido (sem_biometria)']['metade_mais_exigente_pct'], 1)}%), "
        f"e mesmo assim nada passa.\n"
    )
    w(
        "Em resumo, o zero **não** decorre principalmente da dupla condição: o corte de "
        "4 escalas sozinho já não marca nenhuma seção nos quatro diagnósticos. A razão é "
        "estrutural. Tempos têm piso físico e assimetria à direita, e uma escala "
        "simétrica (MAD) calibrada pelo miolo da distribuição torna −4 escalas "
        "praticamente inalcançável pela esquerda, enquanto +4 escalas é alcançado "
        f"pela direita (tempo_lento = {num(R1['controle_lento'])}). A condição da metade "
        "seria redundante na prática; ela só ganharia peso se a escala fosse trocada.\n"
    )
    w(
        "**Limiar alternativo defensável (diagnóstico, sem mudar a regra publicada).** "
        "Duas famílias de alternativa, com propriedades distintas:\n"
    )
    w(
        f"1. *Percentil 0,1% por grupo* (UF × modelo × cargos, mais faixa de volume na "
        f"rajada, e tipo no processo), estrito: marca "
        f"{num(fl['tempo_rapido']['pct01'])} (tempo), "
        f"{num(fl['cadencia_rapida']['pct01'])} (cadência), "
        f"{num(fl['rajada_rapida']['pct01'])} (rajada) e "
        f"{num(fl['processo_rapido (seções, união)']['pct01'])} seções (processo, união). "
        f"É uma fila de conferência de tamanho fixo, não um teste de anomalia: em grupos "
        f"com menos de 1.001 seções o percentil cai entre o menor e o segundo menor "
        f"valor, então marca o mínimo do grupo exista ou não algo fora do comum. Serve "
        f"para ordenar visitas, não para afirmar rapidez atípica."
    )
    w(
        f"2. *z robusto na escala logarítmica* (razões em vez de diferenças, coerente "
        f"com a assimetria dos tempos), corte −4: marca "
        f"{num(fl['tempo_rapido']['logz4'])} (tempo), "
        f"{num(fl['cadencia_rapida']['logz4'])} (cadência), "
        f"{num(fl['rajada_rapida']['logz4'])} (rajada) e "
        f"{num(fl['processo_rapido (seções, união)']['logz4'])} (processo); com −3, "
        f"{num(fl['tempo_rapido']['logz3'])}, {num(fl['cadencia_rapida']['logz3'])}, "
        f"{num(fl['rajada_rapida']['logz3'])} e "
        f"{num(fl['processo_rapido (seções, união)']['logz3'])}. É a alternativa "
        f"estatisticamente coerente e confirma o zero: mesmo com escala adequada à "
        f"assimetria, quase nenhuma seção é muito mais rápida que os pares.\n"
    )
    w(
        "Recomendação: manter a regra publicada e registrar no catálogo que o zero foi "
        "verificado com as duas alternativas acima. Qualquer troca precisa de registro "
        "prévio de versão, porque escolher o corte depois de ver os dados é seleção.\n"
    )

    # ---------------- Q2
    nbat = int(df.S_bateria.sum())
    w(f"## 2. Bateria: {num(nbat)} seções\n")
    cc = R2["conf_contagem"]
    w(
        f"A regra conta mensagens do dia (4 ou 5/10) com “operando” e “bateria "
        f"interna”. A releitura dos ZIPs originais das seções marcadas, com o mesmo "
        f"filtro, reproduz `eventos_bateria` de `metricas` em {num(cc[0])} de "
        f"{num(cc[1])} seções; as {num(cc[1] - cc[0])} diferenças vêm da deduplicação "
        f"de linhas e da exclusão de identificadores feitas pelo leitor.\n"
    )
    voc = R2["vocab"]
    fa_ = R2["fase_app"]
    gap_antes = fa_.loc["GAP", "antes da zerésima"] / fa_.loc["GAP"].sum()
    w(
        "Vocabulário nos originais (10 seções marcadas por modelo, sorteio com "
        "semente fixa; mensagens com “bateria”, dígitos trocados por #):\n"
    )
    vt = (
        voc.groupby(["mensagem", "conta na regra"])
        .agg(
            aplicativos=("aplicativo", lambda x: ", ".join(sorted(set(x)))),
            modelos=("modelo", lambda x: ", ".join(sorted(set(x)))),
            secoes=("seções (de 10)", "sum"),
            mensagens=("mensagens", "sum"),
        )
        .reset_index()
        .sort_values("secoes", ascending=False)
        .rename(columns={"secoes": "seções (de 40)"})
    )
    w(tabela(vt))
    w("")
    w(
        f"Só as linhas com “conta na regra” = sim entram no diagnóstico. A leitura "
        f"periódica de tensão das UE2020/UE2022 e os avisos de carga não contam; a "
        f"marca exige uma passagem para a bateria. Na base inteira, "
        f"{pct(100 * gap_antes)} das mensagens do GAP que contam estão antes da "
        f"zerésima, ou seja, na partida da urna. A regra também não conta "
        f"“Urna operando na bateria externa” (vista numa UE2015 da amostra) nem a "
        f"leitura “desconectada da rede CA” das UE2020/UE2022; uma seção que tenha "
        f"só esses registros fica sem marca.\n"
    )
    w(
        "**Quando a passagem para a bateria aconteceu** (seção classificada pela fase "
        "mais relevante; janela de votação = do primeiro ao último cômputo):\n"
    )
    cl = R2["classe"]
    w(
        tabela(
            pd.DataFrame(
                {
                    "classe": cl.index,
                    "seções": cl.values,
                    "% das marcadas": 100 * cl.values / cl.sum(),
                }
            ),
            {"% das marcadas": 1},
        )
    )
    w("")
    fa = R2["fase_app"]
    w("Mensagens por aplicativo e fase (contagem de mensagens, não de seções):\n")
    w(tabela(fa.reset_index().rename(columns={"app": "aplicativo"})))
    w("")
    te = R2["teto"]
    w(
        f"**Contagem censurada.** Entre {num(te['secoes_1_partida'])} seções marcadas "
        f"com uma única partida do sistema, {num(te['eq10'])} têm exatamente 10 "
        f"mensagens do VOTA, {num(te['eq9'])} têm 9 e só {num(te['gt10'])} têm mais de "
        f"10. O padrão é compatível com um limite de 10 registros por sessão do "
        f"aplicativo (não documentado aqui: o PDF de formato do log não foi lido). Na "
        f"prática, o número de mensagens não mede a duração nem a quantidade de quedas "
        f"acima de 10.\n"
    )
    si = R2["simult"]
    w(
        f"**Simultaneidade.** Das {num(si['secoes'])} seções com passagem durante a "
        f"votação, {num(si['obs5'])} ({pct(100 * si['obs5'] / si['secoes'])}) têm ao "
        f"menos uma mensagem a até 60 s de mensagens de 5 ou mais outras seções do "
        f"mesmo município, e {num(si['obs20'])} "
        f"({pct(100 * si['obs20'] / si['secoes'])}) de 20 ou mais. Num nulo em que os "
        f"mesmos horários são sorteados uniformemente na janela de votação de cada "
        f"seção, essas parcelas seriam {pct(100 * si['nulo5'])} e "
        f"{pct(100 * si['nulo20'])}. Só {num(si['obs0'])} "
        f"({pct(100 * si['obs0'] / si['secoes'])}) ficam isoladas (nenhuma outra seção "
        f"do município em ±60 s; nulo {pct(100 * si['nulo0'])}). A coincidência no "
        f"mesmo minuto em várias seções é a assinatura de evento de fornecimento "
        f"compartilhado (local de votação ou rede), não de comportamento de urna "
        f"isolada. O nulo uniforme ignora o perfil horário do movimento; serve de "
        f"ordem de grandeza.\n"
    )
    w(
        "**Por modelo.** Comparação dentro da mesma zona (razão de chances de "
        "Mantel-Haenszel por UF × zona, referência UE2020):\n"
    )
    mo = R2["modelo"].reset_index()
    w(tabela(mo, {"% bateria": 1, "% durante votação": 1}))
    w("")
    mh = R2["mh"]
    w(
        tabela(
            pd.DataFrame(
                [
                    {
                        "comparação": k,
                        "zonas com os dois modelos": v["bateria"][0],
                        "OR bateria": v["bateria"][1],
                        "OR durante a votação": v["durante"][1],
                    }
                    for k, v in mh.items()
                ]
            ),
            {"OR bateria": 2, "OR durante a votação": 2},
        )
    )
    w("")
    o22 = mh["UE2022 × UE2020"]
    ors_old = [
        mh[k][c][1]
        for k in ("UE2015 × UE2020", "UE2013 × UE2020")
        for c in ("bateria", "durante")
    ]
    zz = df[df.uf == "ZZ"]
    w(
        f"UE2020 e UE2022 se comportam igual dentro da mesma zona (OR "
        f"{num(o22['bateria'][1], 2)} e {num(o22['durante'][1], 2)}). UE2013 e UE2015 "
        f"registram menos (OR de {num(min(ors_old), 2)} a {num(max(ors_old), 2)}); o "
        f"dado não separa sensibilidade do sensor de diferença de instalação. Não há "
        f"efeito de modelo que explique a massa. No exterior (ZZ, {num(len(zz))} seções, "
        f"modelos {', '.join(sorted(zz.modelo.unique()))}) há "
        f"{num(int(zz.S_bateria.sum()))} marcas de bateria; a causa não foi "
        f"investigada.\n"
    )
    w("**Por UF** (nenhuma UF passa de 50%):\n")
    u = R2["uf"].reset_index()[
        [
            "uf",
            "secoes",
            "bateria",
            "% bateria",
            "durante",
            "% durante votação",
            "% simultânea (das durante)",
        ]
    ]
    w(
        tabela(
            u, {"% bateria": 1, "% durante votação": 1, "% simultânea (das durante)": 1}
        )
    )
    w("")
    zn = R2["zonas"]
    mn = R2["mun"]
    w(
        f"Concentração local: {num(zn[1])} de {num(zn[0])} zonas têm mais de 50% das "
        f"seções marcadas e {num(zn[2])} têm mais de 50% com passagem durante a "
        f"votação; {num(mn[1])} de {num(mn[0])} municípios com 20 seções ou mais têm "
        f"mais da metade das seções com passagem durante a votação. A marca cai com o "
        f"tamanho da seção:\n"
    )
    tt = R2["tam"].reset_index()
    tt["pct"] *= 100
    tt["pct_v"] *= 100
    w(
        tabela(
            tt.rename(
                columns={
                    "tam": "comparecimento",
                    "pct": "% bateria",
                    "pct_v": "% durante votação",
                }
            ),
            {"% bateria": 1, "% durante votação": 1},
        )
    )
    w("")
    cl_ = R2["classe"]
    w(
        f"**Para o fiscal.** Como marca única, “bateria” é ruído de massa: "
        f"{pct(100 * nbat / len(df))} das seções; "
        f"{pct(100 * cl_['só antes da zerésima'] / nbat)} das marcadas só têm passagem "
        f"antes da zerésima (compatível com urna ligada antes de conectada à rede ou "
        f"instabilidade na preparação; o log não distingue) e a associação com os "
        f"demais sinais é fraca (lift de {num(outros.min(), 1)} a "
        f"{num(outros.max(), 1)} nos pares com 100 seções ou mais; os maiores são "
        f"{top_bat}). A parte informativa é "
        f"estreita: passagem para bateria **durante a votação** "
        f"({num(si['secoes'])} seções), separada em (i) simultânea com 5 ou mais "
        f"seções do município ({num(si['obs5'])}), que pede conferir na ata a falta "
        f"de energia do local e se o atendimento parou; (ii) isolada "
        f"({num(si['obs0'])}), que pede conferir tomada, cabo e fonte daquela urna; e "
        f"(iii) intermediária, com 1 a 4 outras seções ({num(si['obs1_4'])}). Nenhuma "
        f"informa a duração, que o log da regra não mede.\n"
    )

    # ---------------- Q3
    w("## 3. Biometria\n")
    nac = R3["nac"]
    w(
        f"Taxas nacionais (seções com categorias conciliadas ao BU, "
        f"{num(nac['secoes'])}): sem biometria / comparecimento = "
        f"{num(nac['sem'])} / {num(nac['comp'])} = "
        f"{pct(100 * nac['sem'] / nac['comp'], 2)}; biográficas / (biométricas + "
        f"biográficas) = {num(nac['bg'])} / {num(nac['bio'] + nac['bg'])} = "
        f"{pct(100 * nac['bg'] / (nac['bio'] + nac['bg']), 2)}. As duas taxas têm "
        f"denominadores diferentes e não se somam. Estados da biometria: "
        + ", ".join(f"{k} {num(v)}" for k, v in R3["status"].items())
        + f" (ausente_bu: {num(int((df.biometria_status == 'ausente_bu').sum()))} "
        f"seções, das quais "
        f"{num(int(((df.biometria_status == 'ausente_bu') & (df.uf == 'ZZ')).sum()))} "
        f"no exterior).\n"
    )
    av = R3["aval"]
    w(
        f"Cobertura das referências: {num(av['sb_ok'])} seções elegíveis para "
        f"sem_biometria_alta, das quais {num(av['sb_sem_ref'])} "
        f"({pct(100 * av['sb_sem_ref'] / av['sb_ok'])}) ficam sem referência porque o "
        f"grupo UF × município × zona × modelo tem menos de 30 seções; para "
        f"biografica_alta, {num(av['bg_sem_ref'])} de {num(av['bg_ok'])}. Essas seções "
        f"nunca podem ser marcadas, por mais alta que seja a taxa.\n"
    )
    w("**Por UF**, ordenado pela mediana de sem biometria por seção:\n")
    u = R3["uf"].reset_index()
    w(
        tabela(
            u[
                [
                    "uf",
                    "seções",
                    "taxa sem bio %",
                    "mediana sem bio %",
                    "p90 sem bio %",
                    "ref. mediana %",
                    "sem_biometria_alta",
                    "% sem_bio_alta",
                    "taxa biográfica %",
                    "mediana biográfica %",
                    "biografica_alta",
                    "% biog_alta",
                ]
            ],
            dict.fromkeys(u.columns, 2),
        )
    )
    w("")
    w(
        f"A correlação entre a mediana de sem biometria da UF e a parcela de seções "
        f"marcadas é {num(R3['corr_uf'], 2)}: UFs com cadastro biométrico mais "
        f"incompleto ({', '.join(R3['uf'].index[:3])} no topo da mediana) **não** são "
        f"as mais marcadas. A "
        f"referência local absorve o nível: a mediana da referência acompanha a "
        f"mediana da UF, e a marca só aparece quando uma seção destoa da própria zona e "
        f"do próprio modelo. O efeito da escolha do estrato:\n"
    )
    cf = R3["contrafactual"]
    w(tabela(cf.drop(columns="_top")))
    w("")
    top_nac = cf[
        (cf.medida == "sem_biometria") & cf["referência"].str.startswith("Brasil")
    ]
    top_pub = cf[
        (cf.medida == "sem_biometria") & cf["referência"].str.startswith("publ")
    ]
    w(
        f"Com referência nacional por modelo, {' e '.join(top_nac._top.iloc[0][:2])} "
        f"dominariam as marcas de sem biometria (diferença de cadastro entre regiões); "
        f"com a referência publicada, lideram {', '.join(top_pub._top.iloc[0])} "
        f"(seções que destoam da própria zona).\n"
    )
    w(
        "**Por modelo** (biográfica é muito mais alta nas UE2013/UE2015; a referência "
        "inclui o modelo e absorve isso):\n"
    )
    w(tabela(R3["modelo"].reset_index(), {"mediana_sem_bio": 2, "mediana_biog": 2}))
    w("")
    pbg = nac["bg"] / (nac["bio"] + nac["bg"])
    w(
        "**Por tamanho** (comparecimento). Sem biometria alta cresce levemente com o "
        "tamanho; biográfica alta se concentra em seções pequenas. Mecanismo provável, "
        "não testado aqui: a variação aleatória de uma proporção é maior com poucos "
        f"eleitores (na taxa nacional de {pct(100 * pbg, 2)}, desvio-padrão binomial de "
        f"{num(100 * np.sqrt(pbg * (1 - pbg) / 75), 1)} pp com 75 habilitações e "
        f"{num(100 * np.sqrt(pbg * (1 - pbg) / 275), 1)} pp com 275), "
        "enquanto a escala da referência é comum ao grupo e a regra não ajusta pelo "
        "tamanho; a mediana de biográficas também é maior nas seções pequenas:\n"
    )
    w(
        tabela(
            R3["tam"].reset_index().rename(columns={"tam": "comparecimento"}),
            {"mediana_sem_bio": 2, "mediana_biog": 2},
        )
    )
    w("")
    sb50 = R3["ge50_sem_biometria_pct"]
    bg50 = R3["ge50_biografica_pct"]
    w(
        f"Seções com 50% ou mais sem biometria: {num(sb50[0])}; só {num(sb50[1])} "
        f"marcadas e {num(sb50[2])} sem referência; as outras {num(sb50[3])} não "
        f"destoam o bastante da referência da própria zona e modelo, cuja mediana "
        f"nelas é {pct(sb50[4])}. Seções com 50% ou mais de biográficas: "
        f"{num(bg50[0])}; {num(bg50[1])} marcadas e {num(bg50[2])} sem referência.\n"
    )
    bg = R3["bg90"]
    w(
        f"**Biográfica quase total.** {num(bg['total'])} seções têm 90% ou mais de "
        f"habilitações biográficas; "
        + ", ".join(f"{k} {num(v)}" for k, v in bg["modelo"].items())
        + f". As UE2013 são {pct(100 * bg['ue2013_secoes'] / nsec)} das seções e "
        f"{pct(100 * bg['modelo'].get('UE2013', 0) / bg['total'])} desse grupo. Só "
        f"{num(bg['sinalizadas'])} estão marcadas; {num(bg['sem_ref'])} não têm "
        f"referência e {num(bg['den_lt50'])} tem denominador menor que 50. Contagens "
        f"agregadas de mensagens nos originais (medianas por voto computado):\n"
    )
    ms = R3["msgs"].reset_index()
    ms.insert(1, "seções", R3["msgs_n"].loc[ms.grupo].values)
    w(tabela(ms, dict.fromkeys(ms.columns, 3)))
    w("")
    alvo_ = R3["msgs"].loc["biográfica >= 90%"]
    ctrl_ = R3["msgs"].drop(index="biográfica >= 90%")
    w(
        f"Nessas seções a urna pediu e capturou digitais "
        f"({num(alvo_.solicita_digital, 2)} pedidos por voto, contra "
        f"{num(ctrl_.solicita_digital.min(), 2)} a {num(ctrl_.solicita_digital.max(), 2)} "
        f"nos controles) e depois seguiu para habilitação manual por dado pessoal "
        f"({num(alvo_.dado_pessoal_manual, 2)} por voto, contra "
        f"{num(ctrl_.dado_pessoal_manual.min(), 2)} a "
        f"{num(ctrl_.dado_pessoal_manual.max(), 2)}). Ou seja, a biometria foi tentada "
        "e não reconheceu; o "
        "log não sustenta a hipótese de mesa que pulou a leitura. A mensagem explícita "
        "de não correspondência é rara, então o log não diz por que o reconhecimento "
        "falhou (sensor, calibração, base biométrica carregada ou outro motivo).\n"
    )
    w(
        "**As 20 seções com maior sem_biometria_pct** (seções com categorias "
        "conciliadas):\n"
    )
    w(tabela(R3["top_sb"], {"sem bio %": 1, "ref. %": 1, "escala pp": 1}))
    w("")
    w("**As 20 seções com maior biografica_pct:**\n")
    w(tabela(R3["top_bg"], {"biog. %": 1, "ref. %": 1, "escala pp": 1}))
    w("")
    w(
        "**Explicações operacionais plausíveis e o que o fiscal confere.** "
        "(a) *Sem biometria*: categoria do BU para eleitor sem biometria no cadastro; o "
        "nível é cadastral (revisão biométrica não concluída na região, eleitores "
        "transferidos ou inscritos sem coleta). O fiscal compara com a lista de "
        "eleitores sem biometria da seção e do local, antes de atribuir a taxa à urna. "
        "(b) *Biográfica*: eleitor com biometria cadastrada que não foi reconhecido e "
        "foi habilitado por dado pessoal; explicações possíveis são leitor sujo ou "
        "defeituoso, digitais desgastadas e procedimento da mesa. O padrão de quase "
        "100% concentrado em UE2013, com tentativas registradas, aponta para o "
        "equipamento ou a base daquela urna, não para escolha da mesa. O fiscal "
        "confere na ata o registro de falha do leitor, eventual troca de urna, a "
        "quantidade de habilitações por dado pessoal e se a mesa seguiu o número "
        "previsto de tentativas. Nenhuma das duas marcas é voto irregular.\n"
    )

    # ---------------- Q4
    w("## 4. Co-ocorrência e famílias\n")
    C = R45["matriz"]
    cod = {c: f"S{i + 1:02d}" for i, c in enumerate(C.columns)}
    w(
        "Matriz de co-ocorrência (seções com ambos; diagonal = total do sinal). "
        "Legenda: " + "; ".join(f"{v} {k}" for k, v in cod.items()) + ".\n"
    )
    Cm = C.rename(index=cod, columns=cod).reset_index().rename(columns={"index": ""})
    w(tabela(Cm))
    w("")
    w(
        "Pares mais redundantes (Jaccard = ambos / união; lift = observado / "
        "esperado sob independência):\n"
    )
    w(
        tabela(
            R45["pares"].head(15), {"Jaccard": 3, "P(b|a)": 3, "P(a|b)": 3, "lift": 1}
        )
    )
    w("")
    pb = R45["pares"]
    pb = (
        pb[pb.par.str.contains("bateria")].sort_values("ambos", ascending=False).head(6)
    )
    w("Pares com bateria (os maiores em contagem):\n")
    w(tabela(pb, {"Jaccard": 3, "P(b|a)": 3, "P(a|b)": 3, "lift": 2}))
    w("")
    e = R45["especificos"]
    w(
        "Redundâncias: "
        + "; ".join(
            f"{k}: {('sim' if v else 'não') if isinstance(v, bool) else num(v)}"
            for k, v in e.items()
        )
        + f". reinicio_sistema e reinicios têm Jaccard "
        f"{num(par('reinicio_sistema', 'reinicios').Jaccard, 3)}; "
        f"{pct(100 * par('ciclos_incompletos', 'reinicios')['P(b|a)'])} de "
        f"ciclos_incompletos e {pct(100 * par('erro_tecnico', 'reinicios')['P(b|a)'])} "
        f"de erro_tecnico acompanham reinicios; contagem_divergente e "
        f"biometria_divergente marcam as mesmas "
        f"{num(int(par('biometria_divergente', 'contagem_divergente').ambos))} seções. "
        f"Bateria tem lift de {num(outros.min(), 1)} a {num(outros.max(), 1)} com os "
        f"sinais com que divide 100 seções ou mais (maiores: {top_bat}).\n"
    )
    w(
        "**Famílias propostas** (cada sinal em uma só família; os quatro diagnósticos "
        "sem ocorrência ficam em Tempo de votação):\n"
    )
    fm = R45["familias"].reset_index().rename(columns={"index": "família"})
    w(tabela(fm))
    w("")
    w(
        f"Seções só com bateria: {num(R45['so_bateria'])}. Número de famílias por "
        f"seção: " + ", ".join(f"{k}: {num(v)}" for k, v in R45["nfam"].items()) + ".\n"
    )

    def lf(x, y):
        return num(par(x, y).lift, 1)

    il = df.S_intervalo_longo
    w(
        f"Critério de agrupamento: lifts altos dentro da família (erro_tecnico × "
        f"reinicios {lf('erro_tecnico', 'reinicios')}; ciclos_incompletos × reinicios "
        f"{lf('ciclos_incompletos', 'reinicios')}; biografica_alta × identificacao_lenta "
        f"{lf('biografica_alta', 'identificacao_lenta')}; retomadas_inatividade × "
        f"tempo_lento {lf('retomadas_inatividade', 'tempo_lento')}; inspecao_prolongada "
        f"× intervalo_longo {lf('inspecao_prolongada', 'intervalo_longo')}) e "
        f"significado legível. Há ligações entre famílias que o leitor deve conhecer: "
        f"identificacao_lenta × tempo_lento {lf('identificacao_lenta', 'tempo_lento')} "
        f"e intervalo_longo × tempo_lento {lf('intervalo_longo', 'tempo_lento')}. "
        f"suspensoes fica em Tempo de votação porque se associa a tempo_lento "
        f"({lf('suspensoes', 'tempo_lento')}) e a retomadas_inatividade "
        f"({lf('retomadas_inatividade', 'suspensoes')}), não a inspecao_prolongada "
        f"({lf('inspecao_prolongada', 'suspensoes')}) nem a intervalo_longo "
        f"({lf('intervalo_longo', 'suspensoes')}). "
        f"Interrupções e inspeções depende muito do tamanho: intervalo_longo marca "
        f"{pct(100 * il[df.comparecimento < 100].mean())} das seções com menos de 100 "
        f"votantes e {pct(100 * il[df.comparecimento >= 250].mean(), 2)} das que têm "
        f"250 ou mais, porque poucos eleitores deixam intervalos longos entre votos.\n"
    )

    # ---------------- Q5
    w("## 5. Régua de atenção para o mapa (0 a 3)\n")
    w(
        "Ordenação para fiscalização a partir dos logs. **Não é probabilidade de "
        "fraude, não é pontuação política e não usa voto.** Bateria é tratada como "
        "contexto: não conta como família, porque é de massa e quase independente dos "
        "demais sinais.\n"
    )
    w(
        "- **0** (a): nenhum sinal; só bateria; ou só inspeção breve, isto é, o único "
        "sinal fora a bateria é inspecao_prolongada com janela máxima de 5 a 10 min "
        "(inspeções abaixo de 5 min nunca são sinal; o corte de 10 min é escolha "
        "declarada desta régua)."
    )
    w(
        "- **1** (b): sinais de uma única família, sem contar bateria (pares "
        "redundantes como reinicio_sistema + reinicios contam uma vez)."
    )
    w("- **2** (c): sinais de duas famílias diferentes.")
    w(
        "- **3** (d): qualquer sinal de integridade ou qualidade do arquivo (assinatura, "
        "contagem_divergente, biometria_divergente, zeresima_ausente, "
        "identidade_nao_confirmada, relogio, texto_malformado) ou três ou mais "
        "famílias.\n"
    )
    nv = R45["nivel"].value_counts().sort_index()
    w(
        tabela(
            pd.DataFrame(
                {
                    "nível": nv.index,
                    "seções": nv.values,
                    "% das seções": 100 * nv.values / nsec,
                }
            ),
            {"% das seções": 2},
        )
    )
    w("")
    n0 = R45["nivel0"]
    n3 = R45["nivel3"]
    si_ = R45["nivel1_so_intervalo"]
    w(
        "Nível 0 = "
        + " + ".join(f"{num(v)} {k}" for k, v in n0.items())
        + ". Nível 1 por família (sem bateria): "
        + ", ".join(f"{k} {num(v)}" for k, v in R45["nivel1_fam"].items())
        + f"; {num(R45['nivel1_so_insp'])} seções do nível 1 têm como único sinal "
        f"inspeção de 10 min ou mais, e {num(si_[0])} têm como único sinal "
        f"intervalo_longo ({num(si_[1])} delas com menos de 150 votantes). Nível 2, "
        f"combinações mais comuns: "
        + "; ".join(f"{k} {num(v)}" for k, v in R45["nivel2_pares"])
        + f". Nível 3: {num(n3['integridade'])} por integridade, {num(n3['3+ famílias'])} "
        f"por três famílias ou mais, {num(n3['ambos'])} pelos dois; por sinal: "
        + ", ".join(f"{k} {num(v)}" for k, v in n3["por sinal"].items() if v)
        + f". {num(n3['ZZ'])} das seções de nível 3 são do exterior, "
        f"{num(n3['ZZ_relogio'])} delas por relógio.\n"
    )
    vb = R45["var_bateria"]
    vi = R45["var_insp"]
    w("Sensibilidade da régua:\n")
    w(
        tabela(
            pd.DataFrame(
                {
                    "nível": vb.index,
                    "principal": nv.reindex(vb.index).values,
                    "bateria conta como Energia": vb.values,
                    f"inspeção única de 5 min ou mais vai a 1 (+{num(R45['so_insp_breve'])})": vi.reindex(
                        vb.index
                    ).values,
                }
            )
        )
    )
    w("")
    w(
        "Distribuição dos níveis por tamanho (% da linha). A régua aponta mais para "
        "seções pequenas, onde intervalos longos e inspeções longas são esperados; o "
        "mapa deve mostrar o tamanho ao lado do nível:\n"
    )
    nt = R45["nivel_tam"].reset_index().rename(columns={"tam": "comparecimento"})
    nt.columns = [str(c) for c in nt.columns]
    w(tabela(nt, dict.fromkeys(nt.columns, 2)))
    w("")
    w("Níveis por UF:\n")
    nu = R45["nivel_uf"].reset_index()
    nu.columns = [str(c) for c in nu.columns]
    w(tabela(nu))
    w("")
    w("## Limites\n")
    w(
        "- Tudo é triagem exploratória de registros operacionais; nenhum número aqui "
        "é teste de fraude ou de alteração de votos."
    )
    mn_ = R3["msgs_n"]
    w(
        f"- A leitura dos ZIPs originais foi feita só para bateria ({num(nbat)} seções) "
        f"e para contagens agregadas de mensagens de habilitação em {num(int(mn_.sum()))} "
        f"seções ({num(int(mn_['biográfica >= 90%']))} com biográfica de 90% ou mais e "
        f"{num(int(mn_.sum() - mn_['biográfica >= 90%']))} controles sorteados com "
        f"semente fixa). Nenhum identificador de mesário, horário individual de eleitor "
        f"ou opção de voto saiu do processo de leitura."
    )
    w(
        "- O teto de 10 mensagens de bateria por sessão é inferido da distribuição, "
        "não de documentação. A simultaneidade usa o município porque o local de "
        "votação não foi usado nesta análise."
    )
    cp = conf_politize
    w(
        f"- Os dados do Politize foram usados só para o nome do município e para "
        f"conferir o comparecimento (o tamanho usado nas tabelas é o comparecimento do "
        f"próprio log). Das {num(cp[0])} seções do log, {num(cp[1])} casam com o "
        f"Politize e {num(cp[2])} têm comparecimento lá, igual ao do log em todas."
    )
    return "\n".join(L) + "\n"


def main():
    df, pt, indice = carregar()
    S = df.sinais.fillna("").str.get_dummies("|").astype(bool)
    for c in S.columns:
        df[f"S_{c}"] = S[c]
    met = carregar_metricas()
    df = df.merge(met, on=CHAVE, how="left")
    P, nomes = carregar_politize()
    conf = df[[*CHAVE, "comparecimento"]].merge(P, on=CHAVE)
    tem = conf.comp_politize.notna()
    assert (conf.comparecimento[tem] == conf.comp_politize[tem]).all()
    conf_politize = (len(df), len(conf), int(tem.sum()))
    df["tam"] = pd.cut(df.comparecimento, TAMANHOS, labels=ROT_TAM)
    R1 = q1(df, pt, indice)
    ev = eventos_bateria(df)
    R2, df2 = q2(df, ev)
    msgs = mensagens_habilitacao(df)
    R2["vocab"] = vocabulario_bateria(df)
    R3 = q3(df, nomes, msgs)
    R45 = q4_q5(df, S)
    R45["matriz"].to_csv(OUT / "coocorrencia_sinais.csv")
    R45["pares"].to_csv(OUT / "pares_sinais.csv", index=False)
    R3["top_sb"].to_csv(OUT / "top20_sem_biometria.csv", index=False)
    R3["top_bg"].to_csv(OUT / "top20_biografica.csv", index=False)
    pd.DataFrame(R1["linhas"]).to_csv(OUT / "q1_distancias.csv", index=False)
    pd.DataFrame(R1["flags"]).T.to_csv(OUT / "q1_alternativas.csv")
    R2["uf"].to_csv(OUT / "bateria_por_uf.csv")
    df[CHAVE].assign(nivel=R45["nivel"].values).to_csv(
        OUT / "nivel_atencao_por_secao.csv.gz", index=False
    )
    texto = escrever(df2, R1, R2, R3, R45, indice, conf_politize)
    assert "\u2014" not in texto, "travessão no memorando"
    (OUT / "memorando.md").write_text(texto)
    print("ok", len(texto))


if __name__ == "__main__":
    main()
