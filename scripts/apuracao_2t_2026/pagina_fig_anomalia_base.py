"""Base do capítulo "Grupos" do dossiê do 2º turno: leitura, cores e acessores.

Tudo sai de ``analysis/apuracao_2t_2026/dados/anomalia_ml.json`` (contrato em
``analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md``, seção 6) e, só para o mapa de
pontos, do arquivo pesado ``data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz``
apontado por ``secoes_arquivo``. Nenhum número é digitado aqui.

As cores dos grupos reaproveitam ``CLUSTER_COR`` do 1º turno (auditada sobre o
papel) e acrescentam cinco tons escuros para k até dez; ``test_cores_passam_aa``
confere o contraste de cada uma contra o papel.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from functools import cache
from pathlib import Path
from typing import Any

from apuracao_2026.pagina_comum import NOME_UF, ROOT, num
from apuracao_2026.pagina_fig_base import dado
from apuracao_2026.pagina_fig_secoes import CLUSTER_COR, UF_REGIAO

ARQUIVO = "anomalia_ml.json"
INDICE_POLITIZE = ROOT / "docs/assets/politize/dados/indice.json"
POLITIZE_SE = "politizese.html"
ROTULO = "Atipicidade estatística não é irregularidade; o grupo pede explicação, não prova nada."

# Cinco primeiras do 1º turno (do mais lulista ao menos); as demais, tons escuros
# que passam em WCAG AA sobre o papel (#f4f0e6) e sob texto branco.
CORES = [*CLUSTER_COR, "#b0562a", "#2f5d8f", "#0c7a72", "#7a2a6e", "#5f6773"]
EXTENSO = {
    2: "dois",
    3: "três",
    4: "quatro",
    5: "cinco",
    6: "seis",
    7: "sete",
    8: "oito",
    9: "nove",
    10: "dez",
}
COLUNA_NOME = {
    "lula1": "Lula, 1º turno",
    "flavio1": "Flávio, 1º turno",
    "outros1": "outras candidaturas, 1º turno",
    "brancos1": "brancos, 1º turno",
    "nulos1": "nulos, 1º turno",
    "lula2": "Lula, 2º turno",
    "flavio2": "Flávio, 2º turno",
    "brancos2": "brancos, 2º turno",
    "nulos2": "nulos, 2º turno",
}
DELTA_NOME = {
    "comp": "comparecimento",
    "lula": "Lula",
    "flavio": "Flávio",
    "brancos": "brancos",
    "nulos": "nulos",
}
SINAL_NOME = {
    "escore_1_mais_pct": "com um sinal ou mais (escore 1+)",
    "escore_2_mais_pct": "com dois sinais ou mais (escore 2+)",
    "papel_pct": "BU do sistema de apuração",
    "contingencia_pct": "urna de contingência",
    "mudanca_pct": "mudança de local entre os turnos",
}


# ------------------------------------------------------------------ leitura


def anomalia(d) -> dict:
    """``anomalia_ml.json`` pelo leitor ``Dados``; ausente, ``KeyError``."""
    return dado(d, ARQUIVO.removesuffix(".json"))


def g(obj: Any, *chaves: str, padrao=None):
    """Primeira chave presente (o motor e o capítulo foram escritos em paralelo)."""
    if not isinstance(obj, dict):
        return padrao
    for c in chaves:
        if c in obj and obj[c] is not None:
            return obj[c]
    return padrao


def componentes(A: dict) -> list[dict]:
    return sorted(A["componentes"], key=lambda c: c["id"])


def componente(A: dict, k: int) -> dict:
    for c in A["componentes"]:
        if c["id"] == k:
            return c
    raise KeyError(f"componente {k}")


def k_de(A: dict) -> int:
    return int(g(A, "k_escolhido", "k", padrao=len(A["componentes"])))


def extenso(k: int) -> str:
    return EXTENSO.get(k, str(k))


def cor(k: int) -> str:
    return CORES[k % len(CORES)]


def rotulo_grupo(A: dict, k: int, curto: bool = False) -> str:
    """'Grupo 3: Lula sobe, abstenção cai' (ou só 'Grupo 3')."""
    if curto:
        return f"Grupo {k + 1}"
    c = componente(A, k)
    r = c.get("rotulo")
    return f"Grupo {k + 1}: {r}" if r else f"Grupo {k + 1}"


def id_atipico(A: dict) -> int:
    return int(A["mais_anomalo"]["id"])


def atipico(A: dict) -> dict:
    return componente(A, id_atipico(A))


def regiao_da_uf(uf: str | None) -> str:
    return UF_REGIAO.get((uf or "").upper(), "Exterior")


def nome_uf(uf: str) -> str:
    return NOME_UF.get(uf.upper(), uf)


# ------------------------------------------------------------------ centros


def centro(c: dict) -> dict[str, float]:
    """Centro em % do eleitorado, nove colunas (nomes do contrato)."""
    ce = dict(g(c, "centro_pct_eleitorado", padrao={}) or {})
    return {k: float(v) for k, v in ce.items() if v is not None}


def partes_turno(c: dict, turno: int) -> list[tuple[str, float]]:
    """Barra de 100% do eleitorado de um turno: (parte, %), abstenção fechando."""
    ce = centro(c)
    if turno == 1:
        chaves = [
            ("lula", "lula1"),
            ("flavio", "flavio1"),
            ("terceiros", "outros1"),
            ("brancos", "brancos1"),
            ("nulos", "nulos1"),
        ]
    else:
        chaves = [
            ("lula", "lula2"),
            ("flavio", "flavio2"),
            ("brancos", "brancos2"),
            ("nulos", "nulos2"),
        ]
    out = [(nome, ce.get(ch, 0.0)) for nome, ch in chaves]
    soma = sum(v for _, v in out)
    abst = g(c, f"abst{turno}_pct")
    if abst is None:
        abst = max(0.0, 100.0 - soma)
    out.append(("abstencao", float(abst)))
    return out


def deltas(c: dict) -> dict[str, float]:
    """Centro em diferenças 2T menos 1T, pontos do eleitorado."""
    dl = g(c, "centro_delta_pp", padrao={}) or {}
    if dl:
        return {k: float(v) for k, v in dl.items() if v is not None}
    ce = centro(c)
    out = {}
    for k in ("lula", "flavio", "brancos", "nulos"):
        if f"{k}1" in ce and f"{k}2" in ce:
            out[k] = ce[f"{k}2"] - ce[f"{k}1"]
    c1, c2 = g(c, "comp1_pct"), g(c, "comp2_pct")
    if c1 is not None and c2 is not None:
        out["comp"] = float(c2) - float(c1)
    return out


def terceira_1t(c: dict) -> float | None:
    v = g(c, "terceira1_pp")
    if v is None:
        v = g(g(c, "centro_delta_pp", padrao={}) or {}, "terceira1_pp")
    if v is None:
        v = centro(c).get("outros1")
    return None if v is None else float(v)


def pais(A: dict) -> dict[str, float]:
    """Centro do país em frações do eleitorado: o bloco ``pais`` do motor ou, sem
    ele, a média dos grupos ponderada pelas seções."""
    pub = g(A.get("pais") or {}, "centro_pct_eleitorado")
    if pub:
        return {k: float(v) for k, v in pub.items() if v is not None}
    cs = componentes(A)
    tot = sum(c["secoes"] for c in cs) or 1
    out: dict[str, float] = {}
    for c in cs:
        for k, v in centro(c).items():
            out[k] = out.get(k, 0.0) + v * c["secoes"] / tot
    return out


def aptos_medio_pais(A: dict) -> float | None:
    v = g(A.get("pais") or {}, "aptos_medio")
    if v is not None:
        return float(v)
    cs = componentes(A)
    tot = sum(c["secoes"] for c in cs)
    if not tot:
        return None
    return (
        sum((c.get("aptos") or (c.get("aptos_medio") or 0) * c["secoes"]) for c in cs)
        / tot
    )


def sinais_pais(A: dict) -> dict[str, float]:
    """Parcela de cada sinal no país: ``sinais_pais`` do motor ou média ponderada."""
    pub = A.get("sinais_pais")
    if isinstance(pub, dict):
        return {
            k: float(v) for k, v in pub.items() if k in SINAL_NOME and v is not None
        }
    cs = componentes(A)
    tot = sum(c["secoes"] for c in cs) or 1
    out: dict[str, float] = {}
    for c in cs:
        s = c.get("sinais") or {}
        for kk in SINAL_NOME:
            v = g(s, kk)
            if v is not None:
                out[kk] = out.get(kk, 0.0) + float(v) * c["secoes"] / tot
    return out


def deltas_pais(A: dict) -> dict[str, float]:
    cs = componentes(A)
    tot = sum(c["secoes"] for c in cs) or 1
    out: dict[str, float] = {}
    for c in cs:
        for k, v in deltas(c).items():
            out[k] = out.get(k, 0.0) + v * c["secoes"] / tot
    return out


# ------------------------------------------------------------------ voto


def voto(A: dict) -> dict:
    return g(A["mais_anomalo"], "voto", padrao={}) or {}


def ic_de(v: dict, *chaves: str) -> tuple[float, float] | None:
    """IC 95% de uma medida, qualquer que seja o nome que o motor deu."""
    for c in chaves:
        ic = v.get(c)
        if isinstance(ic, (list, tuple)) and len(ic) == 2 and None not in ic:
            return float(ic[0]), float(ic[1])
        if isinstance(ic, dict) and "ic95" in ic:
            return ic_de(ic, "ic95")
    return None


def medida_voto(A: dict, qual: str) -> tuple[float | None, tuple | None]:
    """('fatia' | 'did'): valor em pp e IC 95% do grupo atípico contra as vizinhas."""
    v = voto(A)
    if qual == "fatia":
        val = g(v, "fatia_f2_vs_vizinhas_pp", "dif_fatia_flavio_vs_vizinhas_pp")
        ic = ic_de(
            v, "ic95_fatia", "fatia_ic95", "ic95_fatia_f2_vs_vizinhas_pp", "ic95"
        )
        if val is None and isinstance(v.get("fatia_f2_vs_vizinhas"), dict):
            sub = v["fatia_f2_vs_vizinhas"]
            val, ic = g(sub, "pp", "valor"), ic_de(sub, "ic95")
    else:
        val = g(v, "did_vs_1t_pp", "did_fatia_flavio_pp")
        ic = ic_de(v, "ic95_did", "did_ic95", "ic95_did_vs_1t_pp")
        if val is None and isinstance(v.get("did_vs_1t"), dict):
            sub = v["did_vs_1t"]
            val, ic = g(sub, "pp", "valor"), ic_de(sub, "ic95")
        if ic is None and qual == "did":
            # dois "ic95" no esquema: o segundo pertence ao DiD quando o primeiro é
            # da fatia; sem nome distinto, não há como separar, e fica sem IC.
            ic = ic_de(v, "ic95_did")
    return (None if val is None else float(val)), ic


def contem_zero(ic: tuple | None) -> bool | None:
    if ic is None:
        return None
    lo, hi = ic
    return lo <= 0 <= hi


# ------------------------------------------------------------------ amostras


def amostras(A: dict) -> list[dict]:
    return list(g(A["mais_anomalo"], "amostras", padrao=[]) or [])


def link_politize(a: dict) -> str:
    """Link para a seção no Politize-se (do JSON ou montado pela chave)."""
    lk = a.get("link")
    if lk:
        return lk
    return f"{POLITIZE_SE}#uf={a['uf']}&zona={a['zona']}&secao={a['secao']}"


def municipio_de(a: dict) -> str:
    return str(g(a, "municipio", "mun_nome", "nome", "mun", padrao="") or "")


# ------------------------------------------------------------------ arquivo pesado


def caminho_pesado(A: dict) -> Path | None:
    p = g(A, "secoes_arquivo", padrao={}) or {}
    if not p.get("arquivo"):
        return None
    a = Path(p["arquivo"])
    return a if a.is_absolute() else ROOT / a


@cache
def _ler_pesado(caminho_str: str, sha256: str) -> dict:
    dados = Path(caminho_str).read_bytes()
    if sha256 and hashlib.sha256(dados).hexdigest() != sha256:
        raise ValueError(f"{caminho_str} não confere com o SHA-256 de anomalia_ml.json")
    return json.loads(gzip.decompress(dados))


def secoes_pesado(A: dict) -> dict | None:
    """``{"colunas", "linhas"}`` do arquivo pesado, ou None quando ele falta."""
    c = caminho_pesado(A)
    if c is None or not c.exists():
        return None
    p = A["secoes_arquivo"]
    b = _ler_pesado(str(c), p.get("sha256") or "")
    if p.get("n_linhas") is not None and len(b["linhas"]) != p["n_linhas"]:
        raise ValueError(f"{c} não confere com o ponteiro de anomalia_ml.json")
    return b


def atipicas_por_municipio(A: dict) -> list[dict] | None:
    """Seções do grupo atípico e total por (uf, mun) a partir do arquivo pesado."""
    b = secoes_pesado(A)
    if b is None:
        return None
    cols = b["colunas"]
    iu, im, ia = cols.index("uf"), cols.index("mun"), cols.index("anomalo")
    cont: dict[tuple[str, str], list[int]] = {}
    for x in b["linhas"]:
        ch = (str(x[iu]).upper(), str(x[im]).zfill(5))
        c = cont.setdefault(ch, [0, 0])
        c[1] += 1
        if int(x[ia] or 0) == 1:
            c[0] += 1
    return [
        {"uf": uf, "mun": mun, "anomalas": a, "secoes": n}
        for (uf, mun), (a, n) in cont.items()
        if a
    ]


@cache
def municipios_politize(caminho_str: str = str(INDICE_POLITIZE)) -> dict:
    """(uf, mun_tse) -> {nome, lat, lon} pelo índice do Politize; vazio se faltar."""
    c = Path(caminho_str)
    if not c.exists():
        return {}
    d = json.loads(c.read_text(encoding="utf-8"))
    m = d.get("municipios") or {}
    cols = m.get("colunas") or []
    if not cols:
        return {}
    i = {k: cols.index(k) for k in ("uf", "mun_tse", "nome", "lat", "lon")}
    out = {}
    for x in m.get("linhas") or []:
        out[(x[i["uf"]], str(x[i["mun_tse"]]).zfill(5))] = {
            "nome": x[i["nome"]],
            "lat": x[i["lat"]],
            "lon": x[i["lon"]],
        }
    return out


# ------------------------------------------------------------------ formato


def pct_txt(x, casas: int = 1) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def pp_txt(x, casas: int = 1) -> str:
    if x is None:
        return "s/d"
    s = num(abs(x), casas)
    return ("+" if x > 0 else "−" if x < 0 else "") + s + " pp"


def ic_txt(ic: tuple | None, casas: int = 2) -> str:
    if ic is None:
        return "sem IC"
    return f"IC de 95%: {pp_txt(ic[0], casas).removesuffix(' pp')} a {pp_txt(ic[1], casas)}"


__all__ = [
    "ARQUIVO",
    "COLUNA_NOME",
    "CORES",
    "DELTA_NOME",
    "ROTULO",
    "SINAL_NOME",
    "amostras",
    "anomalia",
    "atipicas_por_municipio",
    "atipico",
    "centro",
    "componente",
    "componentes",
    "contem_zero",
    "cor",
    "deltas",
    "deltas_pais",
    "extenso",
    "g",
    "ic_txt",
    "id_atipico",
    "k_de",
    "link_politize",
    "medida_voto",
    "municipio_de",
    "municipios_politize",
    "nome_uf",
    "pais",
    "partes_turno",
    "pct_txt",
    "pp_txt",
    "regiao_da_uf",
    "rotulo_grupo",
    "secoes_pesado",
    "terceira_1t",
    "voto",
]
