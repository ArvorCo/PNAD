#!/usr/bin/env python3
"""Monta a base do mapa do voto util em Flavio Bolsonaro (1o turno de 2026).

Entradas, todas no repositorio:
  analysis/voto_util/quaest/<UF>.json      transcricao pagina a pagina (Quaest)
  analysis/voto_util/outros/*.json          pesquisas estaduais de outros institutos
  analysis/voto_util/nacional/*.json        camada nacional (transferencia, certeza)
  analysis/voto_util/tse_2022_uf.json       TSE 2022 por UF + eleitorado 2026
  docs/assets/reponderacao_pnad.json        agregador nacional da casa

Saidas:
  docs/assets/voto_util_092026.json         tudo o que a pagina desenha
  derivados/voto-util-092026-estados.csv    uma linha por UF

Reproducao:
    python3 scripts/voto-util-092026-tse.py
    python3 scripts/voto-util-092026-data.py
"""

from __future__ import annotations

import csv
import importlib.util
import json
import math
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _modulo(nome: str):
    spec = importlib.util.spec_from_file_location(nome, ROOT / "scripts" / f"{nome}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


B = _modulo("voto_util_base")
M = _modulo("voto_util_modelo")

TSE = json.loads(
    (ROOT / "analysis/voto_util/tse_2022_uf.json").read_text(encoding="utf-8")
)
AGREG = json.loads(
    (ROOT / "docs/assets/reponderacao_pnad.json").read_text(encoding="utf-8")
)
NACIONAL_DIR = ROOT / "analysis/voto_util/nacional"
OUT = ROOT / "docs/assets/voto_util_092026.json"
CSV_OUT = ROOT / "derivados/voto-util-092026-estados.csv"

HOJE = date(2026, 9, 26)
INICIO_FENOMENO = "2026-08-26"
ELEICAO = date(2026, 10, 4)
NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins",
}  # fmt: skip

# Alinhamento local que contraria a sigla nacional. Juizo editorial declarado:
# a pagina publica esta tabela.
CAMPO_EXCECAO = {
    ("GO", "Daniel Vilela"): ("centro-direita", "vice e sucessor de Ronaldo Caiado"),
    ("ES", "Ricardo Ferraço"): ("centro-esquerda", "vice de Renato Casagrande (PSB)"),
    ("AP", "Clécio"): ("centro-esquerda", "governador aliado do governo federal"),
    ("AM", "Omar Aziz"): (
        "centro-esquerda",
        "senador do PSD aliado do governo federal",
    ),
    ("AL", "Renan Filho"): (
        "centro-esquerda",
        "ex-ministro dos Transportes do governo Lula",
    ),
    ("RJ", "Eduardo Paes"): ("centro-esquerda", "prefeito do Rio aliado de Lula"),
    ("PB", "Lucas Ribeiro"): ("centro-esquerda", "vice de João Azevêdo (PSB)"),
    ("PE", "João Campos"): ("esquerda", "PSB, aliado de Lula"),
    ("CE", "Ciro Gomes"): ("centro-direita", "oposição ao PT cearense"),
    ("PB", "Cícero Lucena"): ("centro", "prefeito de João Pessoa"),
}
NAO_ESQUERDA = {"direita", "centro-direita", "centro"}


def pct(x: float, total: float) -> float:
    return 100 * x / total if total else 0.0


def rnd(x, d=2):
    return None if x is None else round(float(x), d)


def tse_por_uf() -> dict[str, dict]:
    return {u["uf"]: u for u in TSE["ufs"]}


def classifica(uf: str, lista: list[dict]) -> list[dict]:
    for c in lista:
        exc = CAMPO_EXCECAO.get((uf, c["nome"]))
        if exc:
            c["campo"], c["campo_nota"] = exc
    return lista


# ----------------------------------------------------------------- nacional
def nacional() -> dict:
    """Media publicada das ultimas ondas nacionais (agregador da casa)."""
    ult = AGREG["agregador"]["ultimo"]
    pesquisas = sorted(AGREG["pesquisas"], key=lambda p: p["campo"]["fim"])
    ondas = []
    for p in pesquisas:
        pub = p.get("publicado", {}).get("1t")
        if not pub or p["campo"]["fim"] < "2026-08-20":
            continue
        lula, fl = pub.get("lula", 0.0), pub.get("flavio", 0.0)
        bn, ind = pub.get("branco_nulo", 0.0), pub.get("indecisos", 0.0)
        outros = sum(
            v
            for k, v in pub.items()
            if k not in ("lula", "flavio", "branco_nulo", "indecisos")
        )
        dois = p.get("publicado", {}).get("2t") or {}
        ondas.append(
            {
                "instituto": p["instituto"],
                "id": p["id"],
                "fim": p["campo"]["fim"],
                "divulgacao": p.get("divulgacao"),
                "registro": p.get("registro_tse"),
                "lula": rnd(lula, 1),
                "flavio": rnd(fl, 1),
                "terceira": rnd(outros, 1),
                "indecisos": rnd(ind, 1),
                "branco_nulo": rnd(bn, 1),
                "lula_validos": rnd(pct(lula, lula + fl + outros), 2),
                "flavio_validos": rnd(pct(fl, lula + fl + outros), 2),
                "lula_2t": dois.get("lula"),
                "flavio_2t": dois.get("flavio"),
            }
        )
    return {"media_1t": ult["1t"], "media_2t": ult["2t"], "ondas": ondas}


def fenomeno(ondas: list[dict]) -> dict:
    """Queda da terceira via e para onde ela foi, instituto a instituto.

    Para cada instituto com duas ondas ou mais desde 26/08, compara a primeira
    e a ultima: quanto a terceira via (mais indecisos e branco/nulo) perdeu e
    quanto disso Flavio e Lula ganharam. A razao de captura e o ganho de Flavio
    dividido pelo ganho somado dos dois.
    """
    por = {}
    for o in ondas:
        # A partir de 26/08 todas as candidaturas atuais ja estao no cartao;
        # antes disso ha ondas sem Augusto Cury, e a comparacao ficaria torta.
        if o["fim"] >= INICIO_FENOMENO:
            por.setdefault(o["instituto"], []).append(o)
    linhas = []
    for inst, xs in por.items():
        if len(xs) < 2:
            continue
        a, b = xs[0], xs[-1]
        df, dl = b["flavio"] - a["flavio"], b["lula"] - a["lula"]
        dt = b["terceira"] - a["terceira"]
        linhas.append(
            {
                "instituto": inst,
                "de": a["fim"],
                "ate": b["fim"],
                "terceira_de": a["terceira"],
                "terceira_ate": b["terceira"],
                "delta_terceira": rnd(dt, 1),
                "delta_flavio": rnd(df, 1),
                "delta_lula": rnd(dl, 1),
                "captura_flavio": rnd(df / (df + dl), 3) if (df + dl) > 0 else None,
                "serie": [
                    {
                        k: o[k]
                        for k in (
                            "fim",
                            "flavio",
                            "lula",
                            "terceira",
                            "indecisos",
                            "branco_nulo",
                        )
                    }
                    for o in xs
                ],
            }
        )
    linhas.sort(key=lambda r: r["delta_terceira"])
    df = sum(r["delta_flavio"] for r in linhas)
    dl = sum(r["delta_lula"] for r in linhas)
    dt = sum(r["delta_terceira"] for r in linhas)
    return {
        "institutos": linhas,
        "soma_delta_flavio": rnd(df, 1),
        "soma_delta_lula": rnd(dl, 1),
        "soma_delta_terceira": rnd(dt, 1),
        "captura_flavio": rnd(df / (df + dl), 3) if df + dl > 0 else None,
    }


def carrega_nacional_json() -> dict:
    out = {}
    if NACIONAL_DIR.exists():
        for p in sorted(NACIONAL_DIR.glob("*.json")):
            out[p.stem] = json.loads(p.read_text(encoding="utf-8"))
    return out


# ------------------------------------------------------------------ estados
def estado_quaest(uf: str, d: dict, tse: dict) -> dict:
    p1 = B.pres_1t_quaest(d)
    p2 = B.pres_2t_quaest(d)
    gov = B.governador_1t(d)
    sen = B.senado_1t(d)
    if gov:
        gov["candidatos"] = classifica(uf, gov["candidatos"])
    if sen:
        sen["candidatos"] = classifica(uf, sen["candidatos"])
    ficha = d.get("ficha") or {}
    rec = {
        "uf": uf,
        "nome": NOMES[uf],
        "regiao": tse["regiao"],
        "instituto": "Quaest",
        "arquivo": d.get("arquivo"),
        "url": d.get("url"),
        "registro": ficha.get("registro_tse"),
        "registro_presidente": ficha.get("registro_tse_nacional")
        or ficha.get("registro_tse_presidente"),
        "campo": ficha.get("campo"),
        "n": ficha.get("n") or 800,
        "margem": ficha.get("margem"),
        "contratante": ficha.get("contratante"),
        "onda_setembro": p1["rodada"] is not None
        and ("Set" in p1["rodada"] or "set" in p1["rodada"]),
        "pres_1t": p1,
        "pres_2t": p2,
        "governador": gov,
        "senado": sen,
        "pres_x_governador": B.cruzamento(d, "pres_1t_x_governador"),
        "pres2_x_governador": B.cruzamento(d, "pres_2t_x_governador"),
        "pres_x_identificacao": B.cruzamento(d, "pres_1t_x_identificacao"),
        "pres_x_comparecimento": B.cruzamento(d, "pres_1t_x_comparecimento"),
        "pres_x_interesse": B.cruzamento(d, "pres_1t_x_interesse"),
        "comparecimento": B.comparecimento(d),
        "definitiva": B.definitiva(d),
        "quem_ganha": B.simples(d, "quem_ganha"),
        "medo": B.simples(d, "medo"),
        "lula_aprovacao": B.simples(d, "lula_aprovacao"),
        "escala": B.simples(d, "escala_perfil"),
        "notas": d.get("notas", []),
    }
    return rec


def swing_setembro(estados: dict[str, dict]) -> dict:
    """Movimento medio de agosto para setembro nas UFs que a Quaest mediu duas vezes.

    Mesmo instituto, mesmo metodo, mesma UF: a diferenca entre as rodadas e o
    melhor estimador disponivel do movimento que as UFs de agosto nao mediram.
    Media ponderada pelo eleitorado de 2026.
    """
    deltas, pesos, linhas = [], [], []
    for uf, e in estados.items():
        serie = e["pres_1t"]["serie"]
        if not e["onda_setembro"] or len(serie) < 2:
            continue
        ago = next(
            (s for s in serie if "Ago" in s["rodada"] or "ago" in s["rodada"]), serie[0]
        )
        set_ = serie[-1]
        dlt = {k: set_[k] - ago[k] for k in ("F", "L", "T", "I", "B")}
        deltas.append(dlt)
        pesos.append(e["peso"])
        linhas.append(
            {
                "uf": uf,
                "de": ago["rodada"],
                "ate": set_["rodada"],
                **{k: rnd(v, 1) for k, v in dlt.items()},
            }
        )
    tot = sum(pesos)
    media = {
        k: sum(d[k] * w for d, w in zip(deltas, pesos, strict=True)) / tot
        for k in ("F", "L", "T", "I", "B")
    }
    return {"media": {k: rnd(v, 2) for k, v in media.items()}, "ufs": linhas}


def reserva_modelo(estados: dict[str, dict]) -> dict:
    """Relacao, nas UFs com 2o turno medido, entre inclinacao e destino do voto de fora.

    `pool` = 100 - F1 - L1 (terceira via, indecisos, branco/nulo). A fracao do
    pool que vira Flavio no 2o turno cresce com a inclinacao do estado
    (F1 / (F1 + L1)); ajustamos uma reta por minimos quadrados ponderados pelo
    eleitorado e usamos a reta so onde o 2o turno nao foi medido.
    """
    xs, yf, yl, ws, pts = [], [], [], [], []
    for uf, e in estados.items():
        if not e["pres_2t"]:
            continue
        g = e["pres_1t"]["grupos"]
        v2 = e["pres_2t"]["valores"]
        pool = 100 - g["F"] - g["L"]
        if pool <= 0:
            continue
        x = g["F"] / (g["F"] + g["L"])
        xs.append(x)
        yf.append((v2["Flávio"] - g["F"]) / pool)
        yl.append((v2["Lula"] - g["L"]) / pool)
        ws.append(e["peso"])
        pts.append(
            {
                "uf": uf,
                "inclinacao": rnd(x, 3),
                "fracao_flavio": rnd(yf[-1], 3),
                "fracao_lula": rnd(yl[-1], 3),
            }
        )

    def reta(y: list[float]) -> tuple[float, float]:
        sw = sum(ws)
        mx = sum(w * x for w, x in zip(ws, xs, strict=True)) / sw
        my = sum(w * v for w, v in zip(ws, y, strict=True)) / sw
        sxx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs, strict=True))
        sxy = sum(w * (x - mx) * (v - my) for w, x, v in zip(ws, xs, y, strict=True))
        b = sxy / sxx if sxx else 0.0
        return my - b * mx, b

    af, bf = reta(yf)
    al, bl = reta(yl)
    return {
        "flavio": {"a": af, "b": bf},
        "lula": {"a": al, "b": bl},
        "pontos": pts,
        "n": len(pts),
    }


def transferencia_nexus(fontes: dict) -> dict:
    """Taxas de transferencia da terceira via para o 2o turno, pela matriz da Nexus.

    A Nexus (21/09, p. 79) e o unico instituto que publica o 2o turno de cada
    eleitorado de terceira via. Ponderamos as linhas pelo peso de cada nome no
    1o turno da mesma pesquisa. Indecisos e branco/nulo nao tem linha publicada:
    a divisao deles e hipotese declarada (30% para cada lado entre indecisos,
    10% e 8% entre branco/nulo), e so afeta quanto da reserva sai de voto valido.
    """
    nx = fontes.get("nexus_20260921", {}).get("blocos", {})
    matriz = (nx.get("migracao_1t_para_2t_lula_x_flavio") or {}).get("linhas", {})
    peso = (nx.get("voto_1t_estimulado") or {}).get("valores", {})
    tot = sum(peso.get(k, 0) for k in matriz)
    if not matriz or not tot:
        return {}
    f = sum(peso.get(k, 0) * v["Flávio"] for k, v in matriz.items()) / tot / 100
    lu = sum(peso.get(k, 0) * v["Lula"] for k, v in matriz.items()) / tot / 100
    return {
        "fonte": "Nexus/BTG, 18 a 20/09/2026, p. 79",
        "linhas": matriz,
        "terceira_flavio": round(f, 4),
        "terceira_lula": round(lu, 4),
        "indecisos_flavio": 0.30,
        "indecisos_lula": 0.30,
        "branco_flavio": 0.10,
        "branco_lula": 0.08,
        "hipotese": "indecisos e branco/nulo sem linha publicada",
    }


def fracao_terceira(nac: dict, g: dict) -> tuple[float, float]:
    """Parcela da reserva de cada lado que sai da terceira via.

    Usa as taxas de transferencia nacionais (quem mede e como estao em
    `nacional["transferencia"]`) aplicadas a composicao do pool da UF.
    """
    t = nac.get("transferencia") or {}
    aT_f, aI_f, aB_f = (
        t.get("terceira_flavio", 0.45),
        t.get("indecisos_flavio", 0.30),
        t.get("branco_flavio", 0.10),
    )
    aT_l, aI_l, aB_l = (
        t.get("terceira_lula", 0.20),
        t.get("indecisos_lula", 0.30),
        t.get("branco_lula", 0.08),
    )
    sf = aT_f * g["T"] + aI_f * g["I"] + aB_f * g["B"]
    sl = aT_l * g["T"] + aI_l * g["I"] + aB_l * g["B"]
    return (aT_f * g["T"] / sf if sf else 0.5), (aT_l * g["T"] / sl if sl else 0.5)


def eleitor_provavel_uf(e: dict) -> dict | None:
    """Mistura as colunas do cruzamento por comparecimento com a propensao declarada."""
    cx = e.get("pres_x_comparecimento")
    comp = e.get("comparecimento")
    if not cx or not comp or not comp.get("valores"):
        return None
    cols = cx["colunas"]
    a = next((c for n, c in cols.items() if n.lower().startswith("sempre")), None)
    b = next((c for n, c in cols.items() if not n.lower().startswith("sempre")), None)
    if not a or not b:
        return None
    v = comp["valores"]
    p_a = v.get("Sempre vota e vai votar", 0)
    vai = v.get("Já deixou de votar, mas vai votar", 0)
    nao = sum(
        v.get(k, 0)
        for k in (
            "Sempre vota, mas não vai votar",
            "Já deixou de votar e não vai votar",
            "Nunca votou e não vai votar",
        )
    )
    p_b = vai + nao
    r = vai / p_b if p_b else 0.5
    ga, gb = a["grupos"], b["grupos"]
    mix = M.eleitor_provavel(ga, gb, p_a, p_b, r)
    return {
        "p_sempre": p_a,
        "p_outros": p_b,
        "r": rnd(r, 3),
        "sempre": {k: rnd(x, 1) for k, x in ga.items()},
        "outros": {k: rnd(x, 1) for k, x in gb.items()},
        "provavel": {k: rnd(x, 2) for k, x in mix.items()},
        "comparecimento_declarado": rnd(p_a + p_b * r, 1),
    }


def monta_estados(nac: dict) -> tuple[dict, dict]:
    tse = tse_por_uf()
    quaest = B.carrega_quaest()
    estados = {}
    for uf, d in quaest.items():
        t = tse[uf]
        rec = estado_quaest(uf, d, t)
        rec["eleitorado_2026"] = t["eleitorado_2026"]
        rec["comparecimento_2022"] = t["comparecimento_1t_pct"]
        rec["peso"] = t["eleitorado_2026"] * t["comparecimento_1t_pct"] / 100
        rec["tse_2022"] = {
            "bolsonaro_1t": t["bolsonaro_1t_validos"],
            "bolsonaro_2t": t["bolsonaro_2t_validos"],
            "lula_1t": t["lula_1t_validos"],
            "terceira_1t": t["terceira_via_1t_validos"],
            "ganho_bolsonaro": t["ganho_bolsonaro_entre_turnos"],
            "ganho_lula": t["ganho_lula_entre_turnos"],
            "branco_nulo_1t": t["branco_nulo_1t_pct_comparecimento"],
        }
        estados[uf] = rec
    swing = swing_setembro(estados)
    reserva = reserva_modelo(estados)
    # Base atual de cada UF: setembro medido, ou agosto + movimento medio medido.
    for e in estados.values():
        g = dict(e["pres_1t"]["grupos"])
        if not e["onda_setembro"]:
            for k in ("F", "L", "T", "I", "B"):
                g[k] = max(0.0, g[k] + swing["media"][k])
            soma = sum(g[k] for k in ("F", "L", "T", "I", "B"))
            g = {
                k: (v * 100 / soma if k in ("F", "L", "T", "I", "B") else v)
                for k, v in g.items()
            }
            e["ajuste"] = (
                "agosto + movimento médio de agosto para setembro nas UFs medidas duas vezes"
            )
        else:
            e["ajuste"] = None
        e["base"] = {k: rnd(v, 2) for k, v in g.items()}
        if e["pres_2t"]:
            v2 = e["pres_2t"]["valores"]
            e["base_2t"] = {"F": v2["Flávio"], "L": v2["Lula"], "medido": True}
        else:
            pool = 100 - g["F"] - g["L"]
            x = g["F"] / (g["F"] + g["L"])
            ff = reserva["flavio"]["a"] + reserva["flavio"]["b"] * x
            fl = reserva["lula"]["a"] + reserva["lula"]["b"] * x
            e["base_2t"] = {
                "F": rnd(g["F"] + max(0.0, ff) * pool, 2),
                "L": rnd(g["L"] + max(0.0, fl) * pool, 2),
                "medido": False,
            }
        e["lv"] = eleitor_provavel_uf(e)
    # Onde nao ha cruzamento por comparecimento, aplica o deslocamento medio medido.
    medidos = [e for e in estados.values() if e["lv"]]
    if medidos:
        tot = sum(e["peso"] for e in medidos)
        desloc = {}
        for k in ("F", "L", "T", "I", "B"):
            num = 0.0
            for e in medidos:
                mix = e["lv"]["provavel"]
                cols = e["pres_x_comparecimento"]["colunas"]
                a = next(c for n, c in cols.items() if n.lower().startswith("sempre"))[
                    "grupos"
                ]
                b = next(
                    c for n, c in cols.items() if not n.lower().startswith("sempre")
                )["grupos"]
                todos = (a[k] * e["lv"]["p_sempre"] + b[k] * e["lv"]["p_outros"]) / (
                    e["lv"]["p_sempre"] + e["lv"]["p_outros"]
                )
                num += (mix[k] - todos) * e["peso"]
            desloc[k] = num / tot
    else:
        desloc = dict.fromkeys(("F", "L", "T", "I", "B"), 0.0)
    for e in estados.values():
        base = e["base"]
        if e["lv"]:
            cols = e["pres_x_comparecimento"]["colunas"]
            a = next(c for n, c in cols.items() if n.lower().startswith("sempre"))[
                "grupos"
            ]
            b = next(c for n, c in cols.items() if not n.lower().startswith("sempre"))[
                "grupos"
            ]
            pa, pb = e["lv"]["p_sempre"], e["lv"]["p_outros"]
            d_uf = {}
            for k in ("F", "L", "T", "I", "B"):
                todos = (a[k] * pa + b[k] * pb) / (pa + pb)
                d_uf[k] = e["lv"]["provavel"][k] - todos
            e["lv_fonte"] = "medido na UF"
        else:
            d_uf = desloc
            e["lv_fonte"] = "deslocamento médio das UFs medidas"
        lv = {k: max(0.0, base[k] + d_uf[k]) for k in ("F", "L", "T", "I", "B")}
        soma = sum(lv.values())
        e["base_lv"] = {k: rnd(v * 100 / soma, 2) for k, v in lv.items()}
        e["base_lv"]["Tdir"] = (
            rnd(base.get("Tdir", base["T"]) * e["base_lv"]["T"] / base["T"], 2)
            if base["T"]
            else 0.0
        )
        e["deslocamento_lv"] = {k: rnd(v, 2) for k, v in d_uf.items()}
        e["base_2t_lv"] = {
            "F": rnd(e["base_2t"]["F"] + d_uf["F"], 2),
            "L": rnd(e["base_2t"]["L"] + d_uf["L"], 2),
            "medido": e["base_2t"]["medido"],
        }
        fT_f, fT_l = fracao_terceira(nac, e["base"])
        e["fT_flavio"], e["fT_lula"] = rnd(fT_f, 3), rnd(fT_l, 3)
    return estados, {
        "swing": swing,
        "reserva": reserva,
        "deslocamento_lv_medio": {k: rnd(v, 2) for k, v in desloc.items()},
    }


def indicadores(e: dict) -> dict:
    """Os estoques de voto util de uma UF, em pontos e em eleitores esperados."""
    b, b2 = e["base_lv"], e["base_2t_lv"]
    votantes = e["peso"]

    def eleitores(pp: float | None) -> int | None:
        return None if pp is None else round(votantes * pp / 100)

    reserva = max(0.0, b2["F"] - b["F"])
    out = {
        "flavio": b["F"],
        "lula": b["L"],
        "terceira_direita": b["Tdir"],
        "indecisos": b["I"],
        "branco_nulo": b["B"],
        "reserva_2t_pp": rnd(reserva, 2),
        "reserva_2t_eleitores": eleitores(reserva),
        "reserva_medida": b2["medido"],
        "terceira_direita_eleitores": eleitores(b["Tdir"]),
        "flavio_validos": rnd(pct(b["F"], b["F"] + b["L"] + b["T"]), 2),
        "lula_validos": rnd(pct(b["L"], b["F"] + b["L"] + b["T"]), 2),
    }
    # Governador fora de Flavio, pelo cruzamento quando existe.
    cx = e.get("pres_x_governador")
    gov = e.get("governador") or {}
    campo_por_nome = {c["nome"]: c for c in gov.get("candidatos", [])}
    linhas = []
    if cx:
        for nome, col in cx["colunas"].items():
            base_nome = nome.split(" (")[0]
            cand = campo_por_nome.get(base_nome) or next(
                (
                    c
                    for n, c in campo_por_nome.items()
                    if n.split()[0] == base_nome.split()[0]
                ),
                None,
            )
            if not cand or cand["valor"] is None:
                continue
            g = col["grupos"]
            fora = g["Tdir"] + g["I"] + g["B"]
            linhas.append(
                {
                    "nome": cand["nome"],
                    "partido": cand["partido"],
                    "campo": cand["campo"],
                    "voto_governador": cand["valor"],
                    "flavio_entre_eleitores": g["F"],
                    "lula_entre_eleitores": g["L"],
                    "fora_entre_eleitores": rnd(fora, 1),
                    "flavio_entre_eleitores_antes": (
                        col["anterior"]["grupos"]["F"] if col.get("anterior") else None
                    ),
                    "enderecavel_pp": rnd(cand["valor"] * fora / 100, 2),
                    "cruzado_lula_pp": rnd(cand["valor"] * g["L"] / 100, 2),
                    "enderecavel_eleitores": eleitores(cand["valor"] * fora / 100),
                }
            )
    out["governador_cruzamento"] = linhas
    melhor = max(
        (
            c
            for c in gov.get("candidatos", [])
            if c["campo"] in NAO_ESQUERDA and c["valor"] is not None
        ),
        key=lambda c: c["valor"],
        default=None,
    )
    if melhor:
        out["governador_nao_esquerda"] = {
            "nome": melhor["nome"],
            "partido": melhor["partido"],
            "valor": melhor["valor"],
            "campo": melhor["campo"],
        }
        out["vao_governador_pp"] = rnd(melhor["valor"] - e["pres_1t"]["grupos"]["F"], 1)
    sen = e.get("senado") or {}
    dir_sen = [
        c
        for c in sen.get("candidatos", [])
        if c["campo"] in ("direita", "centro-direita") and c["valor"] is not None
    ]
    if dir_sen:
        out["senado_direita_soma"] = rnd(sum(c["valor"] for c in dir_sen), 1)
        out["senado_direita_lider"] = max(dir_sen, key=lambda c: c["valor"])
    ident = e.get("pres_x_identificacao")
    if ident:
        cols = {}
        for nome, col in ident["colunas"].items():
            g = col["grupos"]
            cols[nome] = {
                "F": g["F"],
                "L": g["L"],
                "Tdir": g["Tdir"],
                "I": g["I"],
                "B": g["B"],
            }
        out["identificacao"] = cols
    esc = (e.get("escala") or {}).get("valores") or {}
    if esc and ident:
        fora_dir = 0.0
        for nome in ("Direita não bolsonarista", "Independente"):
            if nome in ident["colunas"] and nome in esc and esc[nome] is not None:
                g = ident["colunas"][nome]["grupos"]
                fora_dir += esc[nome] * (g["Tdir"] + g["I"] + g["B"]) / 100
        out["direita_independente_fora_pp"] = rnd(fora_dir, 2)
    df = (e.get("definitiva") or {}).get("candidatos", {})
    if "Flávio" in df:
        out["flavio_definitiva"] = df["Flávio"]
    ap = (e.get("lula_aprovacao") or {}).get("valores") or {}
    desap = ap.get("Desaprova")
    if desap is not None:
        out["desaprova_lula"] = desap
        out["vao_desaprovacao_pp"] = rnd(desap - e["pres_1t"]["grupos"]["F"], 1)
    return out


def base_quaest(estados: dict[str, dict]) -> dict[str, dict]:
    """Entradas do modelo pela Quaest, eleitor provavel, uma por UF medida."""
    out = {}
    for uf, e in estados.items():
        b, b2 = e["base_lv"], e["base_2t_lv"]
        a, a2 = e["base"], e["base_2t"]
        out[uf] = {
            "fonte": "Quaest"
            + (" (agosto + movimento de setembro)" if e["ajuste"] else ""),
            "campo": e.get("campo"),
            "n": int(e["n"]),
            "lv": {
                **{k: b[k] for k in ("F", "L", "T", "I", "B", "Tdir")},
                "F2": b2["F"],
                "L2": b2["L"],
            },
            "todos": {
                **{k: a[k] for k in ("F", "L", "T", "I", "B", "Tdir")},
                "F2": a2["F"],
                "L2": a2["L"],
            },
            "medido_2t": b2["medido"],
            "fT_flavio": e["fT_flavio"],
            "fT_lula": e["fT_lula"],
        }
    return out


def estaduais_por_uf(filtro) -> dict[str, dict]:
    """Pesquisa estadual mais recente, por UF, dos institutos aceitos por `filtro`."""
    out: dict[str, dict] = {}
    for d in B.carrega_outros():
        inst = d.get("instituto", "")
        if not filtro(inst):
            continue
        uf = d["uf"]
        fim = (d.get("campo") or "")[-10:]
        if uf in out and out[uf]["fim"] >= fim:
            continue
        v = B.normaliza(d["pres_1t"]["valores"])
        g = B.agrupa(v)
        cen = (d.get("pres_2t") or {}).get("cenarios") or []
        v2 = B.normaliza(cen[0]) if cen else None
        out[uf] = {
            "instituto": inst,
            "fim": fim,
            "campo": d.get("campo"),
            "registro": d.get("registro_tse"),
            "n": d.get("n") or 1000,
            "url": d.get("url_pdf"),
            "materia": d.get("url_materia"),
            "pagina_1t": d["pres_1t"].get("pagina"),
            "pagina_2t": (
                (cen[0].get("pagina") or d["pres_2t"].get("pagina")) if cen else None
            ),
            "valores": v,
            "grupos": g,
            "segundo_turno": v2,
            "json": d["_arquivo_json"],
        }
    return out


def realtime_por_uf() -> dict[str, dict]:
    """Pesquisa estadual mais recente da Real Time Big Data em cada UF."""
    return estaduais_por_uf(lambda inst: "Real Time" in inst)


def terceiros_por_uf() -> dict[str, dict]:
    """Outros institutos com 2o turno medido (Datafolha, Parana Pesquisas etc.).

    Entram so onde nem Quaest nem Real Time mediram a UF; a AtlasIntel, quando
    transcrita, e uma base propria e nao passa por aqui.
    """
    polls = estaduais_por_uf(
        lambda inst: "Real Time" not in inst and "Atlas" not in inst
    )
    return {uf: p for uf, p in polls.items() if p["segundo_turno"]}


def base_estadual(
    polls: dict[str, dict], estados: dict[str, dict], nac: dict, desloc_medio: dict
) -> dict[str, dict]:
    """Entradas do modelo a partir de pesquisas estaduais sem cruzamento por
    comparecimento: aplica o deslocamento de eleitor provavel medido pela Quaest
    na mesma UF, ou o medio onde a Quaest nao mediu."""
    out = {}
    for uf, r in polls.items():
        g = r["grupos"]
        if not r["segundo_turno"]:
            continue
        d_uf = estados[uf]["deslocamento_lv"] if uf in estados else desloc_medio
        lv = {k: g[k] for k in ("F", "L", "T", "I", "B")}
        for k in ("F", "L", "T"):
            lv[k] = max(0.0, lv[k] + d_uf[k])
        soma = sum(lv.values())
        lv = {k: v * 100 / soma for k, v in lv.items()}
        lv["Tdir"] = g["Tdir"] * lv["T"] / g["T"] if g["T"] else 0.0
        v2 = r["segundo_turno"]
        fT_f, fT_l = fracao_terceira(nac, g)
        out[uf] = {
            "fonte": r["instituto"],
            "campo": r["campo"],
            "n": int(r["n"]),
            "lv": {
                **{k: rnd(v, 2) for k, v in lv.items()},
                "F2": rnd(v2["Flávio"] + d_uf["F"], 2),
                "L2": rnd(v2["Lula"] + d_uf["L"], 2),
            },
            "todos": {
                **{k: g[k] for k in ("F", "L", "T", "I", "B", "Tdir")},
                "F2": v2["Flávio"],
                "L2": v2["Lula"],
            },
            "medido_2t": True,
            "fT_flavio": rnd(fT_f, 3),
            "fT_lula": rnd(fT_l, 3),
        }
    return out


def base_realtime(
    rt: dict[str, dict], estados: dict[str, dict], nac: dict, desloc_medio: dict
) -> dict[str, dict]:
    """Entradas do modelo pela Real Time (mantido pelo nome usado nos testes)."""
    return base_estadual(rt, estados, nac, desloc_medio)


def completa(
    base: dict[str, dict],
    outras: list[dict[str, dict]],
    tse: dict[str, dict],
    nome: str,
) -> dict[str, dict]:
    """Preenche UFs sem pesquisa numa base: primeiro com as outras casas, na
    ordem dada, depois por estimativa regional a partir do resultado de 2022."""
    base = dict(base)
    for outra in outras:
        for uf, r in outra.items():
            if uf not in base:
                base[uf] = {
                    **r,
                    "fonte": f"{r['fonte']} (sem {nome} na UF)",
                    "emprestado": True,
                }
    faltam = [uf for uf in tse if uf not in base]
    for uf in faltam:
        reg = tse[uf]["regiao"]
        viz = [u for u in base if tse[u]["regiao"] == reg]
        est = {}
        for modo in ("lv", "todos"):
            rf = statistics.mean(
                base[u][modo]["F"] / tse[u]["bolsonaro_1t_validos"] for u in viz
            )
            rl = statistics.mean(
                base[u][modo]["L"] / tse[u]["lula_1t_validos"] for u in viz
            )
            rf2 = statistics.mean(
                base[u][modo]["F2"] / tse[u]["bolsonaro_2t_validos"] for u in viz
            )
            rl2 = statistics.mean(
                base[u][modo]["L2"] / tse[u]["lula_2t_validos"] for u in viz
            )
            ind = statistics.mean(base[u][modo]["I"] for u in viz)
            bn = statistics.mean(base[u][modo]["B"] for u in viz)
            f = rf * tse[uf]["bolsonaro_1t_validos"]
            lu = rl * tse[uf]["lula_1t_validos"]
            t = max(0.0, 100 - f - lu - ind - bn)
            est[modo] = {
                "F": rnd(f, 2),
                "L": rnd(lu, 2),
                "T": rnd(t, 2),
                "Tdir": rnd(t * 0.8, 2),
                "I": rnd(ind, 2),
                "B": rnd(bn, 2),
                "F2": rnd(rf2 * tse[uf]["bolsonaro_2t_validos"], 2),
                "L2": rnd(rl2 * tse[uf]["lula_2t_validos"], 2),
            }
        base[uf] = {
            "fonte": f"estimado: razão média 2026/2022 das UFs do {reg} aplicada ao resultado de 2022",
            "campo": None,
            "n": 400,
            **est,
            "medido_2t": False,
            "fT_flavio": 0.5,
            "fT_lula": 0.5,
            "estimado": True,
        }
    return base


def alvo_nacional(nac: dict) -> dict:
    """Media das ondas nacionais divulgadas na ultima semana, uma por instituto."""
    corte = (HOJE - timedelta(days=7)).isoformat()
    ult: dict[str, dict] = {}
    for o in nac["ondas"]:
        if (o["divulgacao"] or "") >= corte:
            ult[o["instituto"]] = o
    ondas = list(ult.values())
    f = statistics.mean(o["flavio_validos"] for o in ondas)
    lu = statistics.mean(o["lula_validos"] for o in ondas)
    dois = [o for o in ondas if o["flavio_2t"] and o["lula_2t"]]
    f2 = statistics.mean(
        100 * o["flavio_2t"] / (o["flavio_2t"] + o["lula_2t"]) for o in dois
    )
    return {
        "desde": corte,
        "ondas": [o["id"] for o in ondas],
        "flavio_validos": rnd(f, 2),
        "lula_validos": rnd(lu, 2),
        "outros_validos": rnd(100 - f - lu, 2),
        "flavio_2t_dos_dois": rnd(f2, 2),
    }


def calibra(base: dict[str, dict], tse: dict[str, dict], alvo: dict) -> dict[str, dict]:
    """Ajusta o nivel nacional sem mexer na geografia (balanco proporcional).

    Pesquisas estaduais tem datas e casas diferentes; a media nacional da
    ultima semana e mais fresca. Multiplicamos F, L e T de todas as UFs pelos
    mesmos tres fatores (e F2/L2 por um par de fatores) ate a soma nacional em
    eleitores esperados reproduzir a media nacional. Indecisos e branco/nulo
    de cada UF nao mudam, e o deslocamento de eleitor provavel medido em cada
    UF e reaplicado depois.
    """
    pesos = {
        uf: tse[uf]["eleitorado_2026"] * tse[uf]["comparecimento_1t_pct"] / 100
        for uf in base
    }
    kf = kl = kt = k2 = 1.0

    def aplica(t: dict) -> dict:
        val = t["F"] + t["L"] + t["T"]
        f, lu, tt = t["F"] * kf, t["L"] * kl, t["T"] * kt
        s = f + lu + tt
        dois = t["F2"] + t["L2"]
        f2 = t["F2"] * k2 / (t["F2"] * k2 + t["L2"] / k2) * dois if dois else 0.0
        return {
            **t,
            "F": f * val / s,
            "L": lu * val / s,
            "T": tt * val / s,
            "Tdir": t["Tdir"] * (tt * val / s) / t["T"] if t["T"] else 0.0,
            "F2": f2,
            "L2": dois - f2,
        }

    for _ in range(200):
        agr = {uf: aplica(r["todos"]) for uf, r in base.items()}
        tf = sum(pesos[u] * a["F"] for u, a in agr.items())
        tl = sum(pesos[u] * a["L"] for u, a in agr.items())
        tt = sum(pesos[u] * a["T"] for u, a in agr.items())
        t2f = sum(pesos[u] * a["F2"] for u, a in agr.items())
        t2l = sum(pesos[u] * a["L2"] for u, a in agr.items())
        v = tf + tl + tt
        kf *= (alvo["flavio_validos"] / 100) / (tf / v)
        kl *= (alvo["lula_validos"] / 100) / (tl / v)
        kt *= (alvo["outros_validos"] / 100) / (tt / v)
        k2 *= math.sqrt((alvo["flavio_2t_dos_dois"] / 100) / (t2f / (t2f + t2l)))
    out = {}
    for uf, r in base.items():
        cal = aplica(r["todos"])
        delta = {
            k: r["lv"][k] - r["todos"][k] for k in ("F", "L", "T", "I", "B", "F2", "L2")
        }
        lv = {k: max(0.0, cal[k] + delta[k]) for k in ("F", "L", "T", "I", "B")}
        soma = sum(lv.values())
        lv = {k: v * 100 / soma for k, v in lv.items()}
        lv["Tdir"] = cal["Tdir"] * lv["T"] / cal["T"] if cal["T"] else 0.0
        lv["F2"], lv["L2"] = cal["F2"] + delta["F2"], cal["L2"] + delta["L2"]
        out[uf] = {
            **r,
            "todos": {k: rnd(v, 3) for k, v in cal.items()},
            "lv": {k: rnd(v, 3) for k, v in lv.items()},
        }
    fatores = {
        "flavio": rnd(kf, 4),
        "lula": rnd(kl, 4),
        "terceira": rnd(kt, 4),
        "segundo_turno": rnd(k2 * k2, 4),
    }
    return {"base": out, "fatores": fatores}


def _estados_modelo(base: dict[str, dict], tse: dict[str, dict], modo: str) -> list:
    lista = []
    for uf, r in sorted(base.items()):
        t = tse[uf]
        peso = t["eleitorado_2026"] * t["comparecimento_1t_pct"] / 100
        v = r[modo]
        lista.append(
            M.Estado(
                uf,
                peso,
                v["F"],
                v["L"],
                v["T"],
                v["I"],
                v["B"],
                v["F2"],
                v["L2"],
                int(r["n"]),
                r["fT_flavio"],
                r["fT_lula"],
                r["medido_2t"],
            )
        )
    return lista


CENARIOS = (
    ("Hoje, todos os entrevistados", "todos", 0.0, 0.0),
    ("Hoje, eleitor provável", "lv", 0.0, 0.0),
    ("Um quarto do voto útil", "lv", 0.25, 0.0),
    ("Metade do voto útil", "lv", 0.5, 0.0),
    ("Três quartos do voto útil", "lv", 0.75, 0.0),
    ("Voto útil completo", "lv", 1.0, 0.0),
    ("Os dois lados consolidam", "lv", 1.0, 1.0),
    ("Só Lula consolida", "lv", 0.0, 1.0),
    ("Lula consolida e a direita faz metade", "lv", 0.5, 1.0),
)


def modelo(base: dict[str, dict], tse: dict[str, dict], n_sim: int = 3000) -> dict:
    lista = _estados_modelo(base, tse, "lv")
    lista_todos = _estados_modelo(base, tse, "todos")
    grade = [i / 20 for i in range(21)]
    curvas = {
        "so_direita": [
            {"lam": lam, **{k: rnd(v, 3) for k, v in M.agrega(lista, lam, 0.0).items()}}
            for lam in grade
        ],
        "dois_lados": [
            {"lam": lam, **{k: rnd(v, 3) for k, v in M.agrega(lista, lam, lam).items()}}
            for lam in grade
        ],
        "lula_consolida": [
            {"lam": lam, **{k: rnd(v, 3) for k, v in M.agrega(lista, lam, 1.0).items()}}
            for lam in grade
        ],
    }
    limiares = {
        "primeiro_lugar_so_direita": M.limiar(lista, "margem", 0.0),
        "primeiro_lugar_dois_lados": M.limiar(lista, "margem", 0.0, dois_lados=True),
        "cinquenta_so_direita": M.limiar(lista, "flavio_validos", 50.0),
        "cinquenta_dois_lados": M.limiar(
            lista, "flavio_validos", 50.0, dois_lados=True
        ),
    }
    cenarios = []
    for nome, modo, lam, theta in CENARIOS:
        estados = lista_todos if modo == "todos" else lista
        pont = M.agrega(estados, lam, theta)
        sim = M.simula(estados, lam, theta, n_sim=n_sim)
        cenarios.append(
            {
                "nome": nome,
                "modo": modo,
                "lam": lam,
                "theta": theta,
                **{k: rnd(v, 2) for k, v in pont.items()},
                **{k: rnd(v, 3) for k, v in sim.items()},
            }
        )
    contrib = []
    total_validos = sum(e.peso * (e.F1 + e.L1 + e.T1) for e in lista)
    for e in lista:
        c0, c1 = M.cenario(e, 0.0, 0.0), M.cenario(e, 1.0, 0.0)
        ganho = e.peso * (c1["F"] - c0["F"]) / 100
        contrib.append(
            {
                "uf": e.uf,
                "ganho_flavio_eleitores": round(ganho),
                "pontos_nacionais": rnd(100 * 100 * ganho / total_validos, 3),
            }
        )
    contrib.sort(key=lambda r: -r["ganho_flavio_eleitores"])
    return {
        "curvas": curvas,
        "limiares": {k: rnd(v, 3) for k, v in limiares.items()},
        "cenarios": cenarios,
        "contribuicao": contrib,
        "entradas": {
            uf: {
                k: v
                for k, v in r.items()
                if k
                in (
                    "fonte",
                    "campo",
                    "n",
                    "lv",
                    "todos",
                    "medido_2t",
                    "fT_flavio",
                    "fT_lula",
                )
            }
            for uf, r in sorted(base.items())
        },
    }


def reencontro_2022(tse: dict[str, dict]) -> dict[str, dict]:
    """Eleitor de Bolsonaro em 2022 que ainda nao vota em Flavio, por UF.

    A AtlasIntel cruza, em cada estado, o voto de 2026 com a lembranca
    declarada do voto no 2o turno de 2022. Multiplicamos a parte desse
    eleitorado que esta na terceira via, indecisa ou em branco pelos votos que
    Bolsonaro teve no estado no 2o turno de 2022 (TSE). E lembranca declarada
    numa pesquisa de 2026, nao pesquisa de 2022.
    """
    out = {}
    for d in B.carrega_outros():
        if "Atlas" not in d.get("instituto", ""):
            continue
        cx = (d.get("cruzamentos") or {}).get("pres_1t_x_voto_2022") or {}
        col = next(
            (
                v
                for k, v in (cx.get("colunas") or {}).items()
                if k.startswith("Bolsonaro")
            ),
            None,
        )
        if not col:
            continue
        v = B.normaliza(col)
        g = B.agrupa(v)
        cx2 = (d.get("cruzamentos") or {}).get("pres_2t_x_voto_2022") or {}
        col2 = next(
            (
                x
                for k, x in (cx2.get("colunas") or {}).items()
                if k.startswith("Bolsonaro")
            ),
            None,
        )
        nao = next(
            (
                x
                for k, x in (cx.get("colunas") or {}).items()
                if k.startswith("Não votou")
            ),
            None,
        )
        fora = g["Tdir"] + g["I"] + g["B"]
        votos = tse[d["uf"]]["t2"]["bolsonaro"]
        out[d["uf"]] = {
            "campo": d.get("campo"),
            "pagina": cx.get("pagina"),
            "flavio": rnd(g["F"], 1),
            "lula": rnd(g["L"], 1),
            "terceira": rnd(g["Tdir"], 1),
            "branco_indeciso": rnd(g["I"] + g["B"], 1),
            "fora_pp": rnd(fora, 1),
            "flavio_2t": rnd(B.normaliza(col2).get("Flávio"), 1) if col2 else None,
            "bolsonaro_2022_votos": votos,
            "fora_eleitores": round(votos * fora / 100),
            "lula_eleitores": round(votos * g["L"] / 100),
            "nao_votou_2022": (
                {k: rnd(x, 1) for k, x in B.agrupa(B.normaliza(nao)).items()}
                if nao
                else None
            ),
        }
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["fora_eleitores"]))


def media_modelos(mods: dict[str, dict]) -> dict:
    """Media simples das duas casas, cenario a cenario e ponto a ponto da curva."""
    nomes = list(mods)
    cen = []
    for i, c in enumerate(mods[nomes[0]]["cenarios"]):
        linha = {"nome": c["nome"], "lam": c["lam"], "theta": c["theta"]}
        for k in (
            "flavio_validos",
            "lula_validos",
            "outros_validos",
            "margem",
            "flavio_p10",
            "flavio_p90",
            "margem_p10",
            "margem_p90",
            "lula_p10",
            "lula_p90",
        ):
            linha[k] = rnd(statistics.mean(mods[n]["cenarios"][i][k] for n in nomes), 2)
        cen.append(linha)
    curvas = {}
    for chave in ("so_direita", "dois_lados", "lula_consolida"):
        pts = []
        for i, p in enumerate(mods[nomes[0]]["curvas"][chave]):
            pts.append(
                {
                    "lam": p["lam"],
                    **{
                        k: rnd(
                            statistics.mean(
                                mods[n]["curvas"][chave][i][k] for n in nomes
                            ),
                            3,
                        )
                        for k in (
                            "flavio_validos",
                            "lula_validos",
                            "outros_validos",
                            "margem",
                        )
                    },
                }
            )
        curvas[chave] = pts
    return {"cenarios": cen, "curvas": curvas}


def main() -> None:
    nac = nacional()
    nac["fenomeno"] = fenomeno(nac["ondas"])
    nac["fontes"] = carrega_nacional_json()
    nac["transferencia"] = transferencia_nexus(nac["fontes"])
    estados, aux = monta_estados(nac)
    tse = tse_por_uf()
    rt = realtime_por_uf()
    for uf, e in estados.items():
        e["realtime"] = rt.get(uf)
        e["indicadores"] = indicadores(e)
    bq = base_quaest(estados)
    brt = base_realtime(rt, estados, nac, aux["deslocamento_lv_medio"])
    terceiros = terceiros_por_uf()
    bter = base_estadual(terceiros, estados, nac, aux["deslocamento_lv_medio"])
    atlas = estaduais_por_uf(lambda inst: "Atlas" in inst)
    bat = base_estadual(atlas, estados, nac, aux["deslocamento_lv_medio"])
    bases = {
        "quaest": completa(bq, [brt, bat, bter], tse, "Quaest"),
        "realtime": completa(brt, [bq, bat, bter], tse, "Real Time"),
    }
    # A AtlasIntel so vira base propria com cobertura suficiente; abaixo disso
    # cada estado dela seria emprestado de outra casa e a media ficaria torta.
    if len(bat) >= 15:
        bases["atlas"] = completa(bat, [bq, brt, bter], tse, "AtlasIntel")
    casas = list(bases)
    alvo = alvo_nacional(nac)
    calibradas = {nome: calibra(b, tse, alvo) for nome, b in bases.items()}
    mods = {nome: modelo(c["base"], tse) for nome, c in calibradas.items()}
    for nome, b in bases.items():
        mods[f"{nome}_bruto"] = modelo(b, tse, n_sim=1500)
    mods["media"] = media_modelos({k: mods[k] for k in casas})
    mods["media_bruto"] = media_modelos({k: mods[f"{k}_bruto"] for k in casas})
    aux["casas"] = casas
    aux["reencontro_2022"] = reencontro_2022(tse)
    aux["alvo_nacional"] = alvo
    aux["fatores_calibracao"] = {nome: c["fatores"] for nome, c in calibradas.items()}
    # Reserva por UF na media das casas que mediram a UF, para o mapa.
    for uf in tse:
        vals = []
        for nome in casas:
            r = bases[nome][uf]
            if r.get("emprestado") or r.get("estimado"):
                continue
            v = r["lv"]
            vals.append(
                {
                    "casa": nome,
                    "reserva": max(0.0, v["F2"] - v["F"]),
                    "F": v["F"],
                    "L": v["L"],
                    "Tdir": v["Tdir"],
                    "F2": v["F2"],
                    "L2": v["L2"],
                }
            )
        peso = tse[uf]["eleitorado_2026"] * tse[uf]["comparecimento_1t_pct"] / 100
        if vals:
            res = statistics.mean(x["reserva"] for x in vals)
            aux.setdefault("reserva_uf", {})[uf] = {
                "casas": vals,
                "reserva_pp": rnd(res, 2),
                "reserva_eleitores": round(peso * res / 100),
                "terceira_direita_pp": rnd(statistics.mean(x["Tdir"] for x in vals), 2),
                "terceira_direita_eleitores": round(
                    peso * statistics.mean(x["Tdir"] for x in vals) / 100
                ),
                "flavio_pp": rnd(statistics.mean(x["F"] for x in vals), 2),
                "lula_pp": rnd(statistics.mean(x["L"] for x in vals), 2),
                "votantes_esperados": round(peso),
            }
        else:
            b = bases["quaest"][uf]
            r = b["lv"]
            casas_uf = []
            if not b.get("estimado"):
                casas_uf = [
                    {
                        "casa": b["fonte"].split(" (")[0],
                        "reserva": max(0.0, r["F2"] - r["F"]),
                        "F": r["F"],
                        "L": r["L"],
                        "Tdir": r["Tdir"],
                        "F2": r["F2"],
                        "L2": r["L2"],
                        "campo": b.get("campo"),
                    }
                ]
            aux.setdefault("reserva_uf", {})[uf] = {
                "casas": casas_uf,
                "estimado": bool(b.get("estimado")),
                "reserva_pp": rnd(max(0.0, r["F2"] - r["F"]), 2),
                "reserva_eleitores": round(peso * max(0.0, r["F2"] - r["F"]) / 100),
                "terceira_direita_pp": r["Tdir"],
                "terceira_direita_eleitores": round(peso * r["Tdir"] / 100),
                "flavio_pp": r["F"],
                "lula_pp": r["L"],
                "votantes_esperados": round(peso),
            }
    payload = {
        "gerado_em": HOJE.isoformat(),
        "eleicao": ELEICAO.isoformat(),
        "nacional": nac,
        "estados": estados,
        "realtime": rt,
        "atlas": atlas,
        "auxiliar": aux,
        "modelos": mods,
        "sem_quaest": sorted(set(NOMES) - set(estados)),
        "tse_uf": {
            uf: {
                k: t[k]
                for k in (
                    "regiao",
                    "eleitorado_2026",
                    "comparecimento_1t_pct",
                    "bolsonaro_1t_validos",
                    "bolsonaro_2t_validos",
                    "lula_1t_validos",
                    "lula_2t_validos",
                    "terceira_via_1t_validos",
                    "ganho_bolsonaro_entre_turnos",
                    "ganho_lula_entre_turnos",
                    "branco_nulo_1t_pct_comparecimento",
                )
            }
            for uf, t in tse.items()
        },
        "outros_estaduais": [
            {
                **{
                    k: d.get(k)
                    for k in (
                        "instituto",
                        "uf",
                        "registro_tse",
                        "campo",
                        "n",
                        "url_pdf",
                        "arquivo",
                        "sha256",
                    )
                },
                "json": d["_arquivo_json"],
                "usado": d["uf"] in terceiros
                and terceiros[d["uf"]]["json"] == d["_arquivo_json"]
                and d["uf"] not in bq
                and d["uf"] not in brt,
                "pres_1t": d["pres_1t"].get("valores"),
                "pres_2t": ((d.get("pres_2t") or {}).get("cenarios") or [None])[0],
            }
            for d in B.carrega_outros()
            if "Real Time" not in d.get("instituto", "")
        ],
        "tse_brasil_2022": TSE["brasil_2022"],
        "municipios_2022": TSE["municipios_top_ganho_bolsonaro"],
        "campo_excecao": [
            {"uf": k[0], "nome": k[1], "campo": v[0], "motivo": v[1]}
            for k, v in CAMPO_EXCECAO.items()
        ],
    }
    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    CSV_OUT.parent.mkdir(exist_ok=True)
    campos = [
        "uf",
        "nome",
        "regiao",
        "reserva_pp",
        "reserva_eleitores",
        "terceira_direita_pp",
        "terceira_direita_eleitores",
        "flavio_pp",
        "lula_pp",
        "votantes_esperados",
        "fontes",
    ]
    with CSV_OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for uf in sorted(tse):
            r = aux["reserva_uf"][uf]
            w.writerow(
                {
                    "uf": uf,
                    "nome": NOMES[uf],
                    "regiao": tse[uf]["regiao"],
                    **r,
                    "fontes": "+".join(x["casa"] for x in r["casas"]) or "estimado",
                }
            )
    print(
        "UFs Quaest:",
        len(estados),
        "Real Time:",
        len(rt),
        "sem Quaest:",
        payload["sem_quaest"],
    )
    print("swing medio ago->set:", aux["swing"]["media"])
    print("reserva: reta", aux["reserva"]["flavio"], "n", aux["reserva"]["n"])
    print("deslocamento LV medio:", aux["deslocamento_lv_medio"])
    print("alvo nacional:", alvo, aux["fatores_calibracao"])
    for nome in (*casas, "media", "media_bruto"):
        print("==", nome)
        for c in mods[nome]["cenarios"]:
            print(
                f"   {c['nome']:32} F {c['flavio_validos']:6.2f} L {c['lula_validos']:6.2f} margem {c['margem']:6.2f} | p10-p90 {c['flavio_p10']:.1f}-{c['flavio_p90']:.1f}"
            )
        if "limiares" in mods[nome]:
            print("   limiares:", mods[nome]["limiares"])
    print("fenomeno:", {k: v for k, v in nac["fenomeno"].items() if k != "institutos"})


if __name__ == "__main__":
    main()
