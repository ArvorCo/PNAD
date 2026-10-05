"""Montagem de `lentidao_ufs.json` a partir das réguas já lidas (sem banco nem disco).

Recebe a série de cada arquivo de UF de 2026 (`noite_regioes_fontes`), o
agregado seção a seção de 2022 e o carimbo de recebimento de 2026
(`lentidao_fontes`) e os municípios completos pelos arquivos de andamento, e
devolve um dicionário por UF com os quatro marcos nas réguas disponíveis, a
cauda (do 99% ao 100%), os últimos municípios e os testes de fuso, de seções
remotas e de repetição entre os anos.
"""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from typing import Any

from . import lentidao as L
from .contexto import NOME_UF
from .dados import regiao, utc
from .lentidao_fontes import FECHAMENTO_2026_UTC

GRADE = list(range(0, 481, 5))  # 17h a 01h, de 5 em 5 minutos
JANELA_PAUSA_MIN = 3.0  # marco na primeira versão até 3 min depois da pausa
COBERTURA_COMPLETA = 0.999


def _min(iso: str) -> float:
    return (utc(iso) - utc(FECHAMENTO_2026_UTC)).total_seconds() / 60


def pontos_uf(versoes: Sequence[Mapping[str, Any]]) -> list[tuple[float, int]]:
    """(minuto desde as 17h, seções totalizadas) de cada versão do arquivo de UF."""
    return [(round(_min(v["gerado"]), 3), v["st"] or 0) for v in versoes]


def cauda_votos(versoes: Sequence[Mapping[str, Any]], marco99: float | None) -> dict:
    """Válidos e votos que entraram na UF depois do marco de 99%."""
    if marco99 is None:
        return {}
    antes = None
    for v in versoes:
        if _min(v["gerado"]) < marco99 - 1e-6:
            antes = v
    fim = versoes[-1]
    if antes is None:
        return {}
    d = {k: (fim[k] or 0) - (antes[k] or 0) for k in ("st", "vv", "flavio", "lula")}
    d["pct_lula"] = round(100 * d["lula"] / d["vv"], 2) if d["vv"] else None
    return d


def _ultimos(muns: Mapping[str, Mapping[str, Any]], uf: str, chave: str, n: int):
    sel = {
        cd: {"nome": m["nome"], "secoes": m["secoes"], "min": m[chave]}
        for cd, m in muns.items()
        if m["uf"] == uf and m.get(chave) is not None
    }
    out = L.ultimos(sel, n)
    for x in out:
        x["hora"] = L.hora(x["min"])
    return out


def _sinalizar_pausa(marcos: Mapping[str, float], pausa: tuple[float, float]) -> list:
    """Marcos registrados logo depois da pausa (a passagem pode ter sido nela)."""
    janela = (pausa[1] - 1e-6, pausa[1] + JANELA_PAUSA_MIN)
    return [k for k, m in marcos.items() if L.dentro(m, janela)]


def montar_ufs(
    series: Mapping[str, Sequence[Mapping[str, Any]]],
    s22: Mapping[str, Any],
    r26: Mapping[str, Any],
    ab26: Mapping[str, Mapping[str, Any]],
    pausa_geracao: tuple[float, float],
    pausa_recebimento: tuple[float, float] | None,
) -> list[dict[str, Any]]:
    """Uma entrada por UF (sem o exterior), ordenada pelo 99% de 2026."""
    saida = []
    muns22 = s22["municipios"]
    for uf in sorted(u for u in series if u != "zz"):
        vs = series[uf]
        ts = vs[-1]["ts"]
        p26 = pontos_uf(vs)
        m26 = L.marco_serie(p26, ts)
        cont = r26["contagens"].get(uf, {})
        rec26 = r26["tempos"].get(uf, [])
        proprias = cont.get("proprias", 0)
        cobertura = (
            (cont.get("totalizadas_com_carimbo", 0) + cont.get("recebidas_depois", 0))
            / proprias
            if proprias
            else 0.0
        )
        completa = cobertura >= COBERTURA_COMPLETA
        m26r = L.marco_tempos(rec26) if rec26 and completa else {}
        m22t = L.marco_tempos(s22["totalizacao"].get(uf, []))
        m22r = L.marco_tempos(s22["recebimento"].get(uf, []))
        ab = {cd: m for cd, m in ab26.items() if m["uf"] == uf}
        comuns = sorted(set(ab) & {cd for cd, m in muns22.items() if m["uf"] == uf})
        rho = L.spearman(
            [muns22[cd]["tot"] for cd in comuns], [ab[cd]["min"] for cd in comuns]
        )
        ult26 = L.ultimos(
            {
                cd: {"nome": m["nome"], "secoes": m["secoes"], "min": m["min"]}
                for cd, m in ab.items()
            },
            5,
        )
        ult22 = _ultimos(muns22, uf, "tot", 5)
        repetem = sorted(
            {x["cd"] for x in ult26} & {x["cd"] for x in ult22},
            key=lambda cd: -ab[cd]["min"],
        )
        for x in ult26:
            x["hora"] = L.hora(x["min"])
        saida.append(
            {
                "uf": uf.upper(),
                "nome": NOME_UF[uf],
                "regiao": regiao(uf),
                "fuso_utc": L.fuso(uf),
                "secoes_2026": ts,
                "secoes_2022": s22["secoes"].get(uf, 0),
                "marcos": {
                    "2026_totalizado": m26,
                    "2026_recebido": m26r,
                    "2022_totalizado": m22t,
                    "2022_recebido": m22r,
                },
                "horas": {
                    k: {f: L.hora(v) for f, v in m.items()}
                    for k, m in (
                        ("2026_totalizado", m26),
                        ("2026_recebido", m26r),
                        ("2022_totalizado", m22t),
                        ("2022_recebido", m22r),
                    )
                },
                "recebido_2026": {
                    "cobertura_pct": round(100 * cobertura, 2),
                    "completa": completa,
                    **cont,
                },
                "primeira_secao": {
                    "2026_totalizado": next((m for m, st in p26 if st > 0), None),
                    "2022_recebido": min(s22["recebimento"].get(uf, []), default=None),
                    "2022_totalizado": min(
                        s22["totalizacao"].get(uf, []), default=None
                    ),
                },
                "cauda_min": {
                    "2026": _cauda(m26),
                    "2022": _cauda(m22t),
                },
                "cauda_votos_2026": cauda_votos(vs, m26.get("99")),
                "marcos_logo_apos_pausa": {
                    "2026_totalizado": _sinalizar_pausa(m26, pausa_geracao),
                    "2026_recebido": (
                        _sinalizar_pausa(m26r, pausa_recebimento)
                        if pausa_recebimento
                        else []
                    ),
                },
                "ultimos_municipios_2026": ult26[:3],
                "ultimos_municipios_2022": ult22[:3],
                "repetem_entre_os_5_ultimos": [ab[cd]["nome"] for cd in repetem],
                "spearman_municipios": {"rho": rho, "n": len(comuns)},
                "curva_2026": L.curva_serie(p26, ts, GRADE),
                "curva_2022": L.curva_tempos(
                    s22["totalizacao"].get(uf, []), s22["secoes"].get(uf, 0), GRADE
                ),
            }
        )
    saida.sort(key=lambda x: x["marcos"]["2026_totalizado"].get("99", 1e9))
    return saida


def _cauda(m: Mapping[str, float]) -> float | None:
    if "99" in m and "100" in m:
        return round(m["100"] - m["99"], 2)
    return None


def nacional(
    series: Mapping[str, Sequence[Mapping[str, Any]]], s22: Mapping[str, Any]
) -> dict[str, Any]:
    """Os quatro marcos do país sem o exterior, nas réguas de totalização."""
    ufs = [u for u in series if u != "zz"]
    eventos = sorted(
        (_min(v["gerado"]), u, v["st"] or 0) for u in ufs for v in series[u]
    )
    atual = dict.fromkeys(ufs, 0)
    pontos = []
    for m, u, st in eventos:
        atual[u] = st
        pontos.append((round(m, 3), sum(atual.values())))
    ts = sum(series[u][-1]["ts"] for u in ufs)
    t22 = [t for u, xs in s22["totalizacao"].items() if u != "zz" for t in xs]
    n22 = sum(n for u, n in s22["secoes"].items() if u != "zz")
    m26 = L.marco_serie(pontos, ts)
    m22 = L.marco_tempos(t22, n22)
    return {
        "secoes_2026": ts,
        "secoes_2022": n22,
        "2026_totalizado": m26,
        "2022_totalizado": m22,
        "horas_2026": {k: L.hora(v) for k, v in m26.items()},
        "horas_2022": {k: L.hora(v) for k, v in m22.items()},
        "curva_2026": L.curva_serie(pontos, ts, GRADE),
        "curva_2022": L.curva_tempos(t22, n22, GRADE),
    }


def atraso_2022(s22: Mapping[str, Any]) -> dict[str, Any]:
    """Segundos entre o recebimento e a primeira totalização parcial, em 2022."""
    xs = sorted(s22["atraso_totalizacao_s"])
    if not xs:
        return {}
    n = len(xs)
    return {
        "secoes": n,
        "mediana_s": statistics.median(xs),
        "p95_s": xs[min(n - 1, round(0.95 * n) - 1)],
        "ate_60s_pct": round(100 * sum(1 for x in xs if x <= 60) / n, 2),
        "negativos": sum(1 for x in xs if x < 0),
    }


def pausa_no_recebimento(
    r26: Mapping[str, Any], s22: Mapping[str, Any], ufs: Sequence[str]
) -> dict[str, Any]:
    """Carimbos de recebimento por minuto das 19h às 20h30, em 2026 e em 2022.

    Nas mesmas UFs (as que têm carimbo de 2026 completo), mesmo relógio (minutos
    desde as 17h). A maior lacuna de 2026 dentro da janela é a que se compara
    com a pausa geral de geração de arquivos.
    """
    de, ate = 120, 210
    t26 = [t for u in ufs for t in r26["tempos"].get(u, [])]
    t22 = [t for u in ufs for t in s22["recebimento"].get(u, [])]
    lac26 = L.maior_lacuna(t26, de, ate)
    lac22 = L.maior_lacuna(t22, de, ate)
    return {
        "ufs": [u.upper() for u in ufs],
        "secoes_2026": len(t26),
        "secoes_2022": len(t22),
        "janela": [L.hora(de), L.hora(ate)],
        "lacuna_2026": {
            **lac26,
            "de_hora": hms(lac26["de"]),
            "ate_hora": hms(lac26["ate"]),
        },
        "lacuna_2022": {
            **lac22,
            "de_hora": hms(lac22["de"]),
            "ate_hora": hms(lac22["ate"]),
        },
        "por_minuto_2026": L.por_minuto(t26, de, ate),
        "por_minuto_2022": L.por_minuto(t22, de, ate),
    }


def hms(m: float | None) -> str | None:
    if m is None:
        return None
    seg = round((17 * 60 + m) * 60)
    h, resto = divmod(seg, 3600)
    return f"{h % 24:02d}:{resto // 60:02d}:{resto % 60:02d}"


def estrutural(
    ufs: Sequence[Mapping[str, Any]],
    s22: Mapping[str, Any],
    ab26: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Os mesmos lugares fecham por último nos dois anos?"""
    muns22 = s22["municipios"]
    comuns = sorted(cd for cd in set(ab26) & set(muns22) if ab26[cd]["uf"] != "zz")
    mesmo_ultimo = [
        u["uf"]
        for u in ufs
        if u["ultimos_municipios_2026"]
        and u["ultimos_municipios_2022"]
        and u["ultimos_municipios_2026"][0]["cd"]
        == u["ultimos_municipios_2022"][0]["cd"]
    ]
    return {
        "spearman_nacional": L.spearman(
            [muns22[cd]["tot"] for cd in comuns], [ab26[cd]["min"] for cd in comuns]
        ),
        "municipios_comparados": len(comuns),
        "ufs_com_o_mesmo_ultimo_municipio": mesmo_ultimo,
        "ufs_com_repeticao_entre_os_5_ultimos": [
            u["uf"] for u in ufs if u["repetem_entre_os_5_ultimos"]
        ],
    }


def resumo_marcos(ufs: Sequence[Mapping[str, Any]], chave: str = "99") -> dict:
    """Classificação, teste de fuso e quantas UFs andaram mais rápido em 2026."""
    m26 = {u["uf"].lower(): u["marcos"]["2026_totalizado"].get(chave) for u in ufs}
    m22 = {u["uf"].lower(): u["marcos"]["2022_totalizado"].get(chave) for u in ufs}
    ganhos = {
        u: round(m22[u] - m26[u], 2)
        for u in m26
        if m26[u] is not None and m22[u] is not None
    }
    return {
        "marco": chave,
        "classificacao": {
            k: [x.upper() for x in v] for k, v in L.classificar(m22, m26).items()
        },
        "mediana_2026": L.mediana_grupo(m26, list(m26)),
        "mediana_2022": L.mediana_grupo(m22, list(m22)),
        "fuso": {
            k: ([x.upper() for x in v] if isinstance(v, list) else v)
            for k, v in L.teste_fuso(m22, m26).items()
        },
        "mais_rapidas_em_2026": sum(1 for g in ganhos.values() if g > 0),
        "mais_lentas_em_2026": sorted(u.upper() for u, g in ganhos.items() if g < 0),
        "spearman_ufs": L.spearman([m22[u] for u in ganhos], [m26[u] for u in ganhos]),
        "ganho_min": {u.upper(): g for u, g in sorted(ganhos.items())},
    }
