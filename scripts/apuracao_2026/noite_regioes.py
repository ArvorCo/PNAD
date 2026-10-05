"""A noite por região: a apuração do 1º turno reconstruída pelos arquivos de UF.

Partes puras, sem banco. A entrada é a série de versões novas de cada arquivo de
UF de presidente (`u:6257:1:uf:<uf>::`), já na ordem de geração, cada versão com
`gerado` (ISO do relógio do TSE), `st`, `ts`, `vv`, `flavio` e `lula`. A soma dos
28 arquivos (27 UFs e exterior) é a contagem que o TSE já tinha totalizado; o
arquivo nacional atrasou em relação a ela nas paradas (capítulo 3).

Tempo em segundos desde a época Unix nas contas e em `AAAA-MM-DD HH:MM` de
Brasília na saída. O estado de um arquivo num instante é a última versão gerada
até ele; entre duas leituras do coletor o TSE pode ter gerado versões que não
foram lidas, então a série por minuto é a do que o tribunal publicou e a casa
guardou, nunca uma interpolação.
"""

from __future__ import annotations

import bisect
import math
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from itertools import pairwise
from typing import Any

from .dados import BRT, colunar, pct, regiao, utc

REGIOES_NOITE = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul", "Exterior")
CAMPOS = ("st", "vv", "flavio", "lula")
FRACOES_REGIAO = (0.5, 0.9, 0.99, 1.0)
MIN_LOTE_PCT = 10_000  # válidos mínimos para o lote entrar na linha da parcela de Lula


def _seg(iso: str) -> float:
    return utc(iso).timestamp()


def hora_de(seg: float) -> str:
    """Segundos Unix para `AAAA-MM-DD HH:MM:SS` de Brasília."""
    return (
        datetime.fromtimestamp(seg, tz=timezone.utc)
        .astimezone(BRT)
        .strftime("%Y-%m-%d %H:%M:%S")
    )


def _zero() -> dict[str, int]:
    return dict.fromkeys(CAMPOS, 0)


def totais_por_regiao(series: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict:
    """Seções totais (ts da última versão) e resultado final de cada região."""
    saida = {r: {"ts": 0, **_zero()} for r in REGIOES_NOITE}
    for uf, versoes in series.items():
        fim = versoes[-1]
        alvo = saida[regiao(uf)]
        alvo["ts"] += fim["ts"] or 0
        for c in CAMPOS:
            alvo[c] += fim[c] or 0
    return saida


def eventos(series: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[tuple]:
    """Todas as versões de todas as UFs em ordem de geração: (segundo, uf, versão)."""
    lista = [(_seg(v["gerado"]), uf, v) for uf, vs in series.items() for v in vs]
    lista.sort(key=lambda e: (e[0], e[1]))
    return lista


class Acumulador:
    """Estado corrente de cada UF e a soma de cada região, versão a versão."""

    def __init__(self, ufs: Iterable[str]) -> None:
        self.uf = {u: _zero() for u in ufs}
        self.reg = {r: _zero() for r in REGIOES_NOITE}

    def aplica(self, uf: str, versao: Mapping[str, Any]) -> None:
        r = self.reg[regiao(uf)]
        atual = self.uf[uf]
        for c in CAMPOS:
            novo = versao[c] or 0
            r[c] += novo - atual[c]
            atual[c] = novo

    def nacional(self) -> dict[str, int]:
        return {c: sum(r[c] for r in self.reg.values()) for c in CAMPOS}

    def copia(self) -> dict[str, dict[str, int]]:
        return {r: dict(v) for r, v in self.reg.items()}


def grade(
    series: Mapping[str, Sequence[Mapping[str, Any]]],
    inicio: str,
    fim: str,
    passo_s: int = 60,
) -> list[tuple[float, dict[str, dict[str, int]]]]:
    """Soma de cada região em cada instante da grade, de `inicio` a `fim` (ISO)."""
    ev = eventos(series)
    acc = Acumulador(series)
    t, t_fim = _seg(inicio), _seg(fim)
    saida, i = [], 0
    while t <= t_fim + 1e-6:
        while i < len(ev) and ev[i][0] <= t:
            acc.aplica(ev[i][1], ev[i][2])
            i += 1
        saida.append((t, acc.copia()))
        t += passo_s
    return saida


def _lote(antes: Mapping[str, int], depois: Mapping[str, int]) -> dict[str, int]:
    return {c: depois[c] - antes[c] for c in CAMPOS}


def tabela_minutos(
    pontos: Sequence[tuple[float, dict]], totais: Mapping[str, Mapping[str, int]]
) -> tuple[dict, dict]:
    """Tabelas por minuto: uma linha por região e uma nacional (soma das regiões)."""
    reg_linhas, nac_linhas = [], []
    anterior = None
    for t, estado in pontos:
        hora = hora_de(t)[:16]
        nac = {c: sum(v[c] for v in estado.values()) for c in CAMPOS}
        nac_ant = (
            {c: sum(v[c] for v in anterior.values()) for c in CAMPOS}
            if anterior
            else _zero()
        )
        d_nac = _lote(nac_ant, nac)
        for r in REGIOES_NOITE:
            atual = estado[r]
            d = _lote(anterior[r] if anterior else _zero(), atual)
            reg_linhas.append(
                {
                    "hora_brt": hora,
                    "regiao": r,
                    "st": atual["st"],
                    "pst": pct(atual["st"], totais[r]["ts"], 2),
                    "vv": atual["vv"],
                    "flavio": atual["flavio"],
                    "lula": atual["lula"],
                    "d_st": d["st"],
                    "d_vv": d["vv"],
                    "d_flavio": d["flavio"],
                    "d_lula": d["lula"],
                    "lote_pct_lula": (
                        pct(d["lula"], d["vv"], 2) if d["vv"] > 0 else None
                    ),
                    "parcela_do_lote_pct": (
                        pct(d["vv"], d_nac["vv"], 2) if d_nac["vv"] > 0 else None
                    ),
                }
            )
        ts_total = sum(v["ts"] for v in totais.values())
        nac_linhas.append(
            {
                "hora_brt": hora,
                "st": nac["st"],
                "pst": pct(nac["st"], ts_total, 2),
                "vv": nac["vv"],
                "flavio": nac["flavio"],
                "lula": nac["lula"],
                "dif_votos": nac["flavio"] - nac["lula"],
                "dif_pp": (
                    round(100 * (nac["flavio"] - nac["lula"]) / nac["vv"], 3)
                    if nac["vv"]
                    else None
                ),
                "dif_pp_peso_final": padronizada(estado, totais),
                "d_st": d_nac["st"],
                "d_vv": d_nac["vv"],
                "lote_pct_lula": (
                    pct(d_nac["lula"], d_nac["vv"], 2) if d_nac["vv"] > 0 else None
                ),
                "lote_pct_flavio": (
                    pct(d_nac["flavio"], d_nac["vv"], 2) if d_nac["vv"] > 0 else None
                ),
            }
        )
        anterior = estado
    col_r = list(reg_linhas[0]) if reg_linhas else []
    col_n = list(nac_linhas[0]) if nac_linhas else []
    return colunar(col_r, reg_linhas), colunar(col_n, nac_linhas)


def padronizada(
    estado: Mapping[str, Mapping[str, int]], totais: Mapping[str, Mapping[str, int]]
) -> float | None:
    """Flávio menos Lula, em pontos, com cada região no peso final dos válidos.

    É a diferença que se veria se todas as regiões estivessem sendo apuradas no
    mesmo ritmo: o resultado parcial de cada região, ponderado pela parcela dela
    nos válidos do país. Só existe quando todas as regiões já têm votos.
    """
    vv = sum(v["vv"] for v in totais.values())
    if not vv or any(not estado[r]["vv"] for r in REGIOES_NOITE):
        return None
    soma = sum(
        totais[r]["vv"]
        / vv
        * (estado[r]["flavio"] - estado[r]["lula"])
        / estado[r]["vv"]
        for r in REGIOES_NOITE
    )
    return round(100 * soma, 3)


def decomposicao(nacional: Mapping[str, Any]) -> dict[str, Any]:
    """Queda da vantagem de Flávio, do pico em pontos ao fim, em duas partes.

    Entre regiões: a vantagem medida menos a padronizada pelo peso final (a ordem
    em que as regiões chegaram). Dentro das regiões: a padronizada no pico menos a
    final (a ordem de chegada dentro de cada região).
    """
    cols = nacional["colunas"]
    linhas = [dict(zip(cols, r, strict=True)) for r in nacional["linhas"]]
    com = [x for x in linhas if x["dif_pp_peso_final"] is not None]
    pico = max(com, key=lambda x: x["dif_pp"])
    fim = com[-1]
    queda = pico["dif_pp"] - fim["dif_pp"]
    entre = pico["dif_pp"] - pico["dif_pp_peso_final"]
    dentro = pico["dif_pp_peso_final"] - fim["dif_pp_peso_final"]
    return {
        "pico_brt": pico["hora_brt"],
        "pico_pp": pico["dif_pp"],
        "pico_peso_final_pp": pico["dif_pp_peso_final"],
        "final_pp": fim["dif_pp"],
        "queda_pp": round(queda, 3),
        "entre_regioes_pp": round(entre, 3),
        "dentro_das_regioes_pp": round(dentro, 3),
        "entre_regioes_pct_da_queda": round(100 * entre / queda, 1) if queda else None,
    }


def lotes(pontos: Sequence[tuple[float, dict]], passo: int = 5) -> list[dict[str, Any]]:
    """Lotes de `passo` instantes da grade: o que entrou em cada região no intervalo."""
    saida = []
    for i in range(passo, len(pontos), passo):
        (t0, a), (t1, b) = pontos[i - passo], pontos[i]
        por_regiao = {r: _lote(a[r], b[r]) for r in REGIOES_NOITE}
        tot = {c: sum(v[c] for v in por_regiao.values()) for c in CAMPOS}
        saida.append(
            {
                "de_brt": hora_de(t0)[:16],
                "ate_brt": hora_de(t1)[:16],
                "st": tot["st"],
                "vv": tot["vv"],
                "flavio": tot["flavio"],
                "lula": tot["lula"],
                "pct_lula": pct(tot["lula"], tot["vv"], 2) if tot["vv"] > 0 else None,
                "pct_flavio": (
                    pct(tot["flavio"], tot["vv"], 2) if tot["vv"] > 0 else None
                ),
                "regioes": {
                    r: {
                        **v,
                        "parcela_vv_pct": (
                            pct(v["vv"], tot["vv"], 2) if tot["vv"] > 0 else None
                        ),
                        "pct_lula": pct(v["lula"], v["vv"], 2) if v["vv"] > 0 else None,
                    }
                    for r, v in por_regiao.items()
                },
            }
        )
    return saida


def marcos_regioes(
    series: Mapping[str, Sequence[Mapping[str, Any]]],
    totais: Mapping[str, Mapping[str, int]],
    fracoes: Sequence[float] = FRACOES_REGIAO,
) -> dict[str, dict[str, str | None]]:
    """Primeira versão (hora de geração) em que cada região passou de cada fração."""
    alvos = {
        r: {f: math.ceil(f * totais[r]["ts"]) for f in fracoes} for r in REGIOES_NOITE
    }
    total_nac = sum(v["ts"] for v in totais.values())
    alvos_nac = {f: math.ceil(f * total_nac) for f in fracoes}
    saida: dict[str, dict[str, str | None]] = {
        r: {rotulo_fracao(f): None for f in fracoes} for r in [*REGIOES_NOITE, "Brasil"]
    }
    acc = Acumulador(series)
    for t, uf, v in eventos(series):
        acc.aplica(uf, v)
        r = regiao(uf)
        for f in fracoes:
            k = rotulo_fracao(f)
            if (
                saida[r][k] is None
                and totais[r]["ts"]
                and acc.reg[r]["st"] >= alvos[r][f]
            ):
                saida[r][k] = hora_de(t)
            if saida["Brasil"][k] is None and acc.nacional()["st"] >= alvos_nac[f]:
                saida["Brasil"][k] = hora_de(t)
    return saida


def rotulo_fracao(f: float) -> str:
    return f"{round(f * 100, 1):g}"


def contribuicao_final(totais: Mapping[str, Mapping[str, int]]) -> dict[str, Any]:
    """Flávio menos Lula em cada região, em votos e em pontos dos válidos do país."""
    vv = sum(v["vv"] for v in totais.values())
    dif = sum(v["flavio"] - v["lula"] for v in totais.values())
    regioes = {
        r: {
            "votos": totais[r]["flavio"] - totais[r]["lula"],
            "pp_dos_validos_do_pais": round(
                100 * (totais[r]["flavio"] - totais[r]["lula"]) / vv, 3
            ),
            "validos": totais[r]["vv"],
            "parcela_dos_validos_pct": pct(totais[r]["vv"], vv, 2),
            "pct_flavio": pct(totais[r]["flavio"], totais[r]["vv"], 2),
            "pct_lula": pct(totais[r]["lula"], totais[r]["vv"], 2),
        }
        for r in REGIOES_NOITE
    }
    return {
        "diferenca_votos": dif,
        "diferenca_pp": round(100 * dif / vv, 3) if vv else None,
        "regioes": regioes,
    }


def lideranca(nacional: Mapping[str, Any]) -> dict[str, Any]:
    """Maior vantagem de Flávio em votos e em pontos, e se Lula liderou algum minuto."""
    cols = nacional["colunas"]
    linhas = [dict(zip(cols, r, strict=True)) for r in nacional["linhas"]]
    com = [x for x in linhas if x["vv"]]
    if not com:
        raise ValueError("série nacional sem votos")
    pp = max(com, key=lambda x: x["dif_pp"])
    votos = max(com, key=lambda x: x["dif_votos"])
    lula_frente = [x["hora_brt"] for x in com if x["lula"] > x["flavio"]]
    return {
        "primeiro_minuto_com_votos": com[0]["hora_brt"],
        "maior_vantagem_pp": {
            "hora_brt": pp["hora_brt"],
            "pp": pp["dif_pp"],
            "pst": pp["pst"],
        },
        "maior_vantagem_votos": {
            "hora_brt": votos["hora_brt"],
            "votos": votos["dif_votos"],
            "pst": votos["pst"],
        },
        "final": {"votos": com[-1]["dif_votos"], "pp": com[-1]["dif_pp"]},
        "minutos_com_lula_a_frente": len(lula_frente),
        "virada": bool(lula_frente),
    }


def nordeste_no_fluxo(
    pontos: Sequence[tuple[float, dict]],
    totais: Mapping[str, Mapping[str, int]],
    lts: Sequence[Mapping[str, Any]],
    marcas: Sequence[str] = (),
) -> dict[str, Any]:
    """Quando o Nordeste passou a ser a maior parte do que faltava apurar.

    Duas leituras, as duas retrospectivas (usam o total final de cada região):
    - `maior_do_que_faltava`: primeiro minuto em que os válidos que ainda faltavam
      no Nordeste superam os que faltavam em cada uma das outras regiões;
    - `maior_regiao_do_lote_desde`: primeiro lote a partir do qual o Nordeste é a
      maior região em todos os lotes com pelo menos `MIN_LOTE_PCT` válidos até
      o fim da série.
    `marcas` são minutos (`AAAA-MM-DD HH:MM`) em que se quer o retrato do que falta.
    """

    def faltam(estado: Mapping[str, Mapping[str, int]]) -> dict[str, int]:
        return {r: totais[r]["vv"] - estado[r]["vv"] for r in REGIOES_NOITE}

    primeiro = None
    retratos = {}
    for t, estado in pontos:
        f = faltam(estado)
        tot = sum(f.values())
        hora = hora_de(t)[:16]
        if primeiro is None and tot > 0:
            outros = [f[r] for r in REGIOES_NOITE if r != "Nordeste"]
            if f["Nordeste"] > max(outros):
                primeiro = {
                    "hora_brt": hora,
                    "faltavam_validos": tot,
                    "parcela_nordeste_pct": pct(f["Nordeste"], tot, 2),
                }
        if hora in marcas and tot > 0:
            retratos[hora] = {
                "faltavam_validos": tot,
                "parcela_pct": {r: pct(f[r], tot, 2) for r in REGIOES_NOITE},
            }
    grandes = [x for x in lts if x["vv"] >= MIN_LOTE_PCT]
    desde = None
    for i in range(len(grandes)):
        if all(_ne_maior(x) for x in grandes[i:]):
            desde = grandes[i]
            break
    peso = pct(totais["Nordeste"]["vv"], sum(v["vv"] for v in totais.values()), 2)
    acima = next(
        (
            x
            for i, x in enumerate(grandes)
            if all(
                (y["regioes"]["Nordeste"]["parcela_vv_pct"] or 0) > (peso or 0)
                for y in grandes[i:]
            )
        ),
        None,
    )
    return {
        "peso_final_nordeste_pct": peso,
        "maior_do_que_faltava": primeiro,
        "maior_regiao_do_lote_desde": (
            {
                "de_brt": desde["de_brt"],
                "parcela_pct": desde["regioes"]["Nordeste"]["parcela_vv_pct"],
                "pct_lula_do_lote": desde["pct_lula"],
            }
            if desde
            else None
        ),
        "acima_do_proprio_peso_desde": (
            {
                "de_brt": acima["de_brt"],
                "parcela_pct": acima["regioes"]["Nordeste"]["parcela_vv_pct"],
            }
            if acima
            else None
        ),
        "o_que_faltava": retratos,
        "lote_minimo_validos": MIN_LOTE_PCT,
    }


def _ne_maior(lote: Mapping[str, Any]) -> bool:
    reg = lote["regioes"]
    ne = reg["Nordeste"]["vv"]
    return all(ne > reg[r]["vv"] for r in REGIOES_NOITE if r != "Nordeste")


def painel_nacional(
    nacional: Sequence[Mapping[str, Any]],
    series: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Que retrato da soma das UFs cada versão do arquivo nacional mostrava.

    Para cada versão nacional com seções, procura o primeiro instante em que a soma
    dos arquivos de UF alcançou as mesmas seções. A diferença entre a geração da
    versão nacional e esse instante é o atraso do retrato; os votos da soma nesse
    instante conferem se o nacional era de fato um corte atrasado da mesma conta.
    """
    ev = eventos(series)
    acc = Acumulador(series)
    i = 0
    saida: list[dict[str, Any]] = []
    for v in nacional:
        if not v["st"]:
            continue
        if saida and saida[-1]["st"] == v["ts"]:
            break  # depois da primeira versão completa o TSE só regerou o arquivo
        while i < len(ev) and acc.nacional()["st"] < v["st"]:
            acc.aplica(ev[i][1], ev[i][2])
            i += 1
        soma = acc.nacional()
        t_corte = ev[i - 1][0] if i else None
        if soma["st"] < v["st"] or t_corte is None:
            corte = None
            atraso = None
        else:
            corte = hora_de(t_corte)
            atraso = round((_seg(v["gerado"]) - t_corte) / 60, 2)
        saida.append(
            {
                "gerado_brt": hora_de(_seg(v["gerado"])),
                "st": v["st"],
                "pst": pct(v["st"], v["ts"], 2),
                "pct_flavio": pct(v["flavio"], v["vv"], 2),
                "pct_lula": pct(v["lula"], v["vv"], 2),
                "dif_votos": v["flavio"] - v["lula"],
                "soma_ufs_alcancou_brt": corte,
                "atraso_do_retrato_min": atraso,
                "soma_ufs_st": soma["st"] if corte else None,
                "residuo_pp_flavio": (
                    round(
                        pct(v["flavio"], v["vv"], 4)
                        - pct(soma["flavio"], soma["vv"], 4),
                        3,
                    )
                    if corte and v["vv"] and soma["vv"]
                    else None
                ),
                "residuo_pp_lula": (
                    round(
                        pct(v["lula"], v["vv"], 4) - pct(soma["lula"], soma["vv"], 4), 3
                    )
                    if corte and v["vv"] and soma["vv"]
                    else None
                ),
            }
        )
    linha = _linha_st(ev, series)
    for atual, prox in pairwise(saida):
        antes = _seg_brt(prox["gerado_brt"]) - 1
        atras = _st_em(linha, antes) - atual["st"]
        atual["soma_ufs_a_frente_antes_da_proxima"] = atras
        atual["idade_do_retrato_antes_da_proxima_min"] = (
            round((antes + 1 - _seg_brt(atual["soma_ufs_alcancou_brt"])) / 60, 2)
            if atras > 0 and atual["soma_ufs_alcancou_brt"]
            else None
        )
    return saida


def _linha_st(ev: Sequence[tuple], series) -> list[tuple[float, int]]:
    """Seções da soma das UFs depois de cada versão, em ordem de geração."""
    acc = Acumulador(series)
    saida = []
    for t, uf, v in ev:
        acc.aplica(uf, v)
        saida.append((t, acc.nacional()["st"]))
    return saida


def _st_em(linha: Sequence[tuple[float, int]], seg: float) -> int:
    i = bisect.bisect_right(linha, (seg, math.inf)) - 1
    return linha[i][1] if i >= 0 else 0


def _seg_brt(hora: str) -> float:
    return datetime.fromisoformat(hora).replace(tzinfo=BRT).timestamp()


def lacuna_da_soma(
    series: Mapping[str, Sequence[Mapping[str, Any]]], de: str, ate: str
) -> dict[str, Any]:
    """Maior intervalo sem versão nova em nenhum arquivo de UF, dentro da janela."""
    tempos = sorted({_seg(v["gerado"]) for vs in series.values() for v in vs})
    a, b = _seg(de), _seg(ate)
    tempos = [t for t in tempos if a <= t <= b]
    melhor = max(pairwise(tempos), key=lambda p: p[1] - p[0], default=None)
    if melhor is None:
        return {"de_brt": None, "ate_brt": None, "minutos": 0.0}
    return {
        "de_brt": hora_de(melhor[0]),
        "ate_brt": hora_de(melhor[1]),
        "minutos": round((melhor[1] - melhor[0]) / 60, 2),
    }


def _lacuna_ativa(series, marcos) -> dict[str, Any]:
    """Maior lacuna entre a primeira seção totalizada e os 99% do país."""
    inicio = min(_seg(v["gerado"]) for vs in series.values() for v in vs if v["st"])
    fim = marcos["Brasil"]["99"]
    if fim is None:
        raise ValueError("o país não chegou a 99% das seções")
    lac = lacuna_da_soma(series, hora_iso(inicio), hora_iso(_seg_brt(fim)))
    return {**lac, "janela": [hora_de(inicio), fim]}


def _iso_brt(hora: str) -> str:
    return datetime.fromisoformat(hora).replace(tzinfo=BRT).isoformat()


def hora_iso(seg: float) -> str:
    return datetime.fromtimestamp(seg, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def composicao(
    pontos: Sequence[tuple[float, dict]],
    totais: Mapping[str, Mapping[str, int]],
    horas: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """Peso de cada região nos válidos já apurados, em minutos escolhidos, e no fim."""
    vv_fim = sum(v["vv"] for v in totais.values())
    saida: dict[str, dict[str, Any]] = {}
    for t, estado in pontos:
        hora = hora_de(t)[:16]
        if hora not in horas:
            continue
        vv = sum(v["vv"] for v in estado.values())
        if not vv:
            continue
        saida[hora] = {
            r: {
                "apurado_pct": pct(estado[r]["vv"], vv, 2),
                "final_pct": pct(totais[r]["vv"], vv_fim, 2),
                "secoes_pct": pct(estado[r]["st"], totais[r]["ts"], 2),
            }
            for r in REGIOES_NOITE
        }
    return saida


def depois_de(pontos: Sequence[tuple[float, dict]], hora_iso: str) -> dict[str, int]:
    """O que entrou na soma das UFs depois de um instante, até o fim da grade."""
    corte = _seg(hora_iso)
    antes = None
    for t, estado in pontos:
        if t <= corte:
            antes = estado
    if antes is None:
        raise ValueError("instante antes da grade")
    fim = pontos[-1][1]
    d = {c: sum(fim[r][c] - antes[r][c] for r in REGIOES_NOITE) for c in CAMPOS}
    return {**d, "pct_lula": pct(d["lula"], d["vv"], 2)}


def montar(
    series: Mapping[str, Sequence[Mapping[str, Any]]],
    nacional: Sequence[Mapping[str, Any]],
    inicio: str,
    fim: str,
    marcas: Sequence[str] = (),
) -> dict[str, Any]:
    """Todos os blocos de `noite_regioes.json` menos os metadados."""
    totais = totais_por_regiao(series)
    pontos = grade(series, inicio, fim)
    reg, nac = tabela_minutos(pontos, totais)
    lts = lotes(pontos)
    marcos = marcos_regioes(series, totais)
    t_ini = datetime.fromisoformat(inicio.replace("Z", "+00:00"))
    meia_noite = (t_ini.astimezone(BRT) + timedelta(days=1)).replace(
        hour=0, minute=0, second=0
    )
    return {
        "regioes": list(REGIOES_NOITE),
        "ufs_por_regiao": {
            r: sorted(u.upper() for u in series if regiao(u) == r)
            for r in REGIOES_NOITE
        },
        "totais": {
            r: {
                "secoes": v["ts"],
                "validos": v["vv"],
                "flavio": v["flavio"],
                "lula": v["lula"],
            }
            for r, v in totais.items()
        },
        "contribuicao_final": contribuicao_final(totais),
        "marcos": marcos,
        "lideranca": lideranca(nac),
        "decomposicao": (dec := decomposicao(nac)),
        "composicao_apurada": composicao(pontos, totais, [dec["pico_brt"], *marcas]),
        "nordeste": nordeste_no_fluxo(pontos, totais, lts, marcas),
        "lacuna_da_soma": _lacuna_ativa(series, marcos),
        "depois_da_meia_noite": depois_de(pontos, meia_noite.isoformat()),
        "depois_dos_99": {
            "desde_brt": marcos["Brasil"]["99"],
            **depois_de(pontos, _iso_brt(marcos["Brasil"]["99"])),
        },
        "painel_nacional": painel_nacional(nacional, series),
        "lotes_5min": lts,
        "minutos": reg,
        "nacional_por_minuto": nac,
    }
