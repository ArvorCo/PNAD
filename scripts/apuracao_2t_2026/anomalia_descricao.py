"""Descrição dos grupos da mistura: centros, rótulos, sinais, cruzamentos e PCA.

Tudo aqui recebe a tabela de trabalho (uma linha por seção do universo, com as
frações em pp, o grupo, a log-densidade e os sinais já cruzados) e devolve
blocos prontos para o JSON. Nenhuma leitura de disco.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2026.secoes_base import num, r2
from apuracao_2026.secoes_clusters_motor import _cruzar, cramer, projecao

from .anomalia_base import COLUNAS

MAX_PONTOS = 8000
MIN_POR_GRUPO = 300
TOP_PCA = 300
SEMENTE_PCA = 20261026
NIVEL_ELIPSE = 2.0  # desvios-padrão no plano
SINAIS_SEIS = (
    ("sinal_delta", "comparecimento ≥ +5 pp contra a própria seção no 1T"),
    ("sinal_sem_bio", "sem biometria cadastrada acima da regra"),
    ("sinal_ano_nasc", "habilitados por ano de nascimento acima da regra"),
    ("sinal_salto_bio", "salto da parcela sem biometria reconhecida"),
    ("sinal_tardia", "encerramento tardio (depois das 19:00 ou 30 min após o 1T)"),
    ("sinal_papel", "BU do sistema de apuração"),
)
NOME_SINAL = {
    "sinal_delta": "comparecimento +5 pp",
    "sinal_sem_bio": "sem biometria",
    "sinal_ano_nasc": "ano de nascimento",
    "sinal_salto_bio": "salto de biometria",
    "sinal_tardia": "encerramento tardio",
    "sinal_papel": "BU de apuração",
}
# o que o rótulo de cada grupo pode citar: chave, nome, unidade
DESCRITORES = (
    ("comp2", "comparecimento no 2º turno", "nivel"),
    ("d_comp", "variação do comparecimento entre turnos", "delta"),
    ("lula2", "Lula no 2º turno", "nivel"),
    ("flavio2", "Flávio no 2º turno", "nivel"),
    ("outros1", "terceira via no 1º turno", "nivel"),
    ("bn1", "brancos e nulos no 1º turno", "nivel"),
    ("bn2", "brancos e nulos no 2º turno", "nivel"),
    ("d_lula", "ganho de Lula entre turnos", "delta"),
    ("d_flavio", "ganho de Flávio entre turnos", "delta"),
)
Z_ROTULO = 0.5
Z_FORTE = 1.0  # "muito acima" / "muito abaixo" no rótulo curto


def pct_maior_resto(cont: Sequence[int], casas: int = 2) -> list[float]:
    """Percentuais com ``casas`` decimais que somam exatamente 100 (maior resto)."""
    c = np.asarray(cont, dtype=float)
    total = c.sum()
    if total <= 0:
        return [0.0] * len(c)
    esc = 10**casas
    bruto = c * 100 * esc / total
    piso = np.floor(bruto).astype(int)
    falta = 100 * esc - int(piso.sum())
    piso[np.argsort(-(bruto - piso), kind="stable")[:falta]] += 1
    return [round(float(v) / esc, casas) for v in piso]


def _pct(a: float, b: float, casas: int = 2) -> float | None:
    return round(100.0 * a / b, casas) if b else None


def _contagem(
    g: pd.Series, total: pd.Series, chave: str, extra: str, top: int | None = None
) -> list[dict[str, Any]]:
    vc = g.value_counts()
    n = int(vc.sum())
    if top is not None:
        vc = vc.head(top)
    return [
        {
            chave: str(v),
            "secoes": int(m),
            "pct_do_cluster": _pct(int(m), n),
            extra: _pct(int(m), int(total.get(v, 0))),
        }
        for v, m in vc.items()
    ]


def sinais_grupo(g: pd.DataFrame) -> dict[str, float | None]:
    """Parcelas (%) dos sinais existentes num conjunto de seções."""
    esc = g["escore"]
    tem = esc.notna()
    n = int(tem.sum())
    return {
        "escore_1_mais_pct": _pct(int((esc[tem] >= 1).sum()), n),
        "escore_2_mais_pct": _pct(int((esc[tem] >= 2).sum()), n),
        "papel_pct": _pct(int((g["tipo_arquivo_2"].fillna(0) >= 3).sum()), len(g)),
        "contingencia_pct": _pct(int(g["contingencia"].fillna(False).sum()), n),
        "mudanca_pct": _pct(int(g["mudanca"].sum()), len(g)),
        "secoes_com_escore": n,
    }


def seis_sinais(d: pd.DataFrame, sel: np.ndarray) -> list[dict[str, Any]]:
    """Os seis sinais do escore no grupo contra o país (mesmas seções com escore)."""
    out = []
    tem = d["escore"].notna().to_numpy()
    for col, desc in SINAIS_SEIS:
        v = d[col].fillna(False).astype(bool).to_numpy()
        g = _pct(int((v & sel & tem).sum()), int((sel & tem).sum()), 3)
        p = _pct(int((v & tem).sum()), int(tem.sum()), 3)
        out.append(
            {
                "sinal": col.removeprefix("sinal_"),
                "nome": NOME_SINAL[col],
                "descricao": desc,
                "secoes_no_grupo": int((v & sel).sum()),
                "pct_grupo": g,
                "pct_pais": p,
                "razao": r2(g / p, 2) if g is not None and p else None,
            }
        )
    return out


def _destaques(
    centro: Mapping[str, float], pais: Mapping[str, tuple[float, float]]
) -> list[tuple[float, str, str, str]]:
    """Os dois maiores desvios do centro contra o país, acima de ``Z_ROTULO``.

    Desvio em unidades do desvio-padrão entre seções: (z, chave, nome, unidade).
    """
    cand = []
    for chave, nome, unidade in DESCRITORES:
        media, dp = pais[chave]
        z = (centro[chave] - media) / dp if dp else 0.0
        cand.append((z, chave, nome, unidade))
    cand.sort(key=lambda c: -abs(c[0]))
    return [c for c in cand[:2] if abs(c[0]) >= Z_ROTULO]


def rotulo(centro: Mapping[str, float], pais: Mapping[str, tuple[float, float]]) -> str:
    """O que distingue o centro do grupo do país, com os números."""
    partes = []
    for _z, chave, nome, unidade in _destaques(centro, pais):
        v, m = centro[chave], pais[chave][0]
        if unidade == "nivel":
            partes.append(
                f"{nome}: {num(v, 1)}% do eleitorado, contra {num(m, 1)}% no país"
            )
        else:
            partes.append(f"{nome}: {_sinal(v)} pontos, contra {_sinal(m)} no país")
    return "; ".join(partes) if partes else "perto da média do país em todas as frações"


def rotulo_curto(
    centro: Mapping[str, float], pais: Mapping[str, tuple[float, float]]
) -> str:
    """O mesmo destaque, sem números, para caber numa caixa de interface.

    "muito acima" ou "muito abaixo" quando o desvio passa de ``Z_FORTE``.
    """
    partes = [
        f"{nome} {'muito ' if abs(z) >= Z_FORTE else ''}"
        f"{'acima' if z > 0 else 'abaixo'} do país"
        for z, _c, nome, _u in _destaques(centro, pais)
    ]
    texto = "; ".join(partes) if partes else "perto da média do país"
    return texto[:1].upper() + texto[1:]


def rotulos_unicos(comps: Sequence[dict[str, Any]]) -> None:
    """Rótulos curtos repetidos entre grupos ganham o número do grupo."""
    vistos: dict[str, int] = {}
    for c in comps:
        vistos[c["rotulo_curto"]] = vistos.get(c["rotulo_curto"], 0) + 1
    for c in comps:
        if vistos[c["rotulo_curto"]] > 1:
            c["rotulo_curto"] += f" (grupo {c['id']})"


def conclusao(
    comp: Mapping[str, Any], contra: Mapping[str, Any], voto: Mapping[str, Any]
) -> str:
    """Leitura do grupo atípico por regra declarada, com os números ao lado.

    Geografia quando o V de Cramér do indicador com a região ou a UF passa de
    0,3; tamanho de seção quando as seções de 30 a 99 aptos caem no grupo três
    vezes ou mais que o país; o voto entre turnos anda como o das vizinhas quando
    o IC da diferença em diferenças contém o zero.
    """
    cv = contra["cramer_v"]
    pequena = contra["tamanho"][0]
    geo = max(cv["regiao"], cv["uf"]) >= 0.3
    tam = (pequena["razao"] or 0) >= 3
    if geo and tam:
        quem = "é geografia e tamanho de seção ao mesmo tempo"
    elif geo:
        quem = "é sobretudo geografia"
    elif tam:
        quem = "não é geografia; é, em boa parte, tamanho de seção"
    else:
        quem = "não é geografia nem tamanho de seção"
    frase = (
        f"Pela régua declarada, o grupo atípico {quem} (V de Cramér com a região "
        f"{num(cv['regiao'], 3)}, com a UF {num(cv['uf'], 3)}, com a faixa de aptos "
        f"{num(cv['tamanho'], 3)}; seções de 30 a 99 aptos {num(pequena['razao'], 1)} "
        f"vezes mais frequentes que no país). No centro, o que o distingue é: "
        f"{comp['rotulo']}."
    )
    ic = voto.get("ic95_did") or [None, None]
    if ic[0] is not None and ic[1] is not None:
        if ic[0] <= 0 <= ic[1]:
            frase += (
                " Entre os turnos, a fatia de Flávio no grupo andou como a das vizinhas "
                f"do mesmo município (diferença em diferenças de "
                f"{_sinal(voto['did_vs_1t_pp'], 2)} ponto, IC de 95% com o zero dentro)."
            )
        else:
            frase += (
                " Entre os turnos, a fatia de Flávio no grupo andou diferente da das "
                f"vizinhas (diferença em diferenças de {_sinal(voto['did_vs_1t_pp'], 2)} "
                "ponto, IC de 95% sem o zero), o que pede explicação, não prova nada."
            )
    return frase


def _sinal(v: float, casas: int = 1) -> str:
    return ("+" if v >= 0 else "−") + num(abs(v), casas)


def referencia_pais(f: pd.DataFrame) -> dict[str, tuple[float, float]]:
    g = f.assign(bn1=f["brancos1"] + f["nulos1"], bn2=f["brancos2"] + f["nulos2"])
    return {
        c: (float(g[c].mean()), float(g[c].std(ddof=0))) for c, _n, _u in DESCRITORES
    }


def componente(
    d: pd.DataFrame,
    c: int,
    cov: np.ndarray,
    peso: float,
    media_modelo: np.ndarray,
    pad: tuple[np.ndarray, np.ndarray],
    pais: Mapping[str, tuple[float, float]],
    pct_secoes: float,
) -> dict[str, Any]:
    """Um grupo: tamanho, centros em níveis e diferenças, densidade, geografia e sinais."""
    sel = (d["grupo"] == c).to_numpy()
    g = d[sel]
    n = int(sel.sum())
    centro = {k: float(g[k].mean()) for k in COLUNAS}
    extra = {
        k: float(g[k].mean())
        for k in ("comp1", "comp2", "d_lula", "d_flavio", "d_brancos", "d_nulos")
    }
    extra["d_comp"] = extra["comp2"] - extra["comp1"]
    extra["bn1"] = centro["brancos1"] + centro["nulos1"]
    extra["bn2"] = centro["brancos2"] + centro["nulos2"]
    sinal, logdet = np.linalg.slogdet(cov)
    media, dp = pad
    f1 = int(g["flavio_1"].sum())
    l1 = int(g["lula_1"].sum())
    f2 = int(g["flavio_2"].sum())
    l2 = int(g["lula_2"].sum())
    return {
        "id": c,
        "secoes": n,
        "pct_secoes": pct_secoes,
        "aptos": int(g["aptos_2"].sum()),
        "aptos_1t": int(g["aptos_1"].sum()),
        "aptos_medio": r2(g["aptos_2"].mean(), 1),
        "aptos_mediana": r2(g["aptos_2"].median(), 1),
        "pequenas_pct": _pct(int((g["aptos_2"] < 100).sum()), n),
        "peso": r2(peso, 4),
        "centro_pct_eleitorado": {k: r2(v, 3) for k, v in centro.items()},
        "centro_modelo_pct_eleitorado": {
            k: r2(float(media_modelo[i] * dp[i] + media[i]), 3)
            for i, k in enumerate(COLUNAS)
        },
        "centro_delta_pp": {
            "comp": r2(extra["d_comp"], 3),
            "lula": r2(extra["d_lula"], 3),
            "flavio": r2(extra["d_flavio"], 3),
            "brancos": r2(extra["d_brancos"], 3),
            "nulos": r2(extra["d_nulos"], 3),
            "terceira1_pp": r2(centro["outros1"], 3),
        },
        "comp1_pct": r2(extra["comp1"], 2),
        "comp2_pct": r2(extra["comp2"], 2),
        "abst1_pct": r2(100 - extra["comp1"], 2),
        "abst2_pct": r2(100 - extra["comp2"], 2),
        "fatia_f1": _pct(f1, f1 + l1),
        "fatia_f2": _pct(f2, f2 + l2),
        "dispersao_logdet": r2(logdet if sinal > 0 else float("nan"), 3),
        "dispersao_traco": r2(np.trace(cov), 3),
        "loglik_media": r2(g["score"].mean(), 3),
        "loglik_p05": r2(np.percentile(g["score"], 5), 3),
        "mahalanobis_mediana": r2(g["maha"].median(), 3),
        "ufs_top": _contagem(g["uf"], d["uf"].value_counts(), "uf", "pct_da_uf", 6),
        "regioes": _contagem(
            g["regiao"], d["regiao"].value_counts(), "regiao", "pct_da_regiao"
        ),
        "modelo_urna": _contagem(
            g["modelo"], d["modelo"].value_counts(), "modelo", "pct_do_modelo"
        ),
        "sinais": sinais_grupo(g),
        "dispersao_relativa": {
            k: r2(float(g[k].std(ddof=0) / d[k].std(ddof=0)), 2) for k in COLUNAS
        },
        "rotulo": rotulo({**centro, **extra}, pais),
        "rotulo_curto": rotulo_curto({**centro, **extra}, pais),
    }


def atipico_contra(d: pd.DataFrame, sel: np.ndarray) -> dict[str, Any]:
    """O grupo atípico (indicador 0/1) contra região, UF, modelo e tamanho.

    O V de Cramér do indicador responde se o grupo é uma geografia, um tamanho de
    seção ou um modelo de urna; a parcela de cada faixa de aptos que cai no grupo
    mostra a sobrerrepresentação das seções pequenas.
    """
    marca = pd.Series(sel.astype(int), index=d.index)
    base = float(sel.mean())
    faixas = []
    for faixa, g in d.groupby("tamanho", sort=False):
        m = sel[d.index.get_indexer(g.index)]
        faixas.append(
            {
                "tamanho": str(faixa),
                "secoes": len(g),
                "no_grupo": int(m.sum()),
                "pct_da_faixa": _pct(int(m.sum()), len(g)),
                "razao": r2(float(m.mean()) / base, 2) if base else None,
            }
        )
    ordem = ["30 a 99", "100 a 199", "200 a 299", "300 a 399", "400 ou mais"]
    faixas.sort(key=lambda r: ordem.index(r["tamanho"]))
    por_uf = (
        pd.DataFrame({"uf": d["uf"], "m": sel})
        .groupby("uf")["m"]
        .agg(["sum", "size"])
        .assign(pct=lambda t: 100 * t["sum"] / t["size"])
        .sort_values("pct", ascending=False)
    )
    menor = (d["aptos_2"] < 200).to_numpy()
    return {
        "pct_grupo_menos_200_aptos": _pct(int((menor & sel).sum()), int(sel.sum())),
        "pct_pais_menos_200_aptos": _pct(int(menor.sum()), len(d)),
        "cramer_v": {
            nome: r2(cramer(marca, d[col]), 3)
            for nome, col in (
                ("regiao", "regiao"),
                ("uf", "uf"),
                ("modelo", "modelo"),
                ("tamanho", "tamanho"),
            )
        },
        "tamanho": faixas,
        "ufs_mais_pesadas": [
            {
                "uf": str(u),
                "secoes": int(r["sum"]),
                "pct_da_uf": r2(r["pct"], 2),
                "razao": r2(r["pct"] / (100 * base), 2) if base else None,
            }
            for u, r in por_uf.head(6).iterrows()
        ],
        "pct_pais": r2(100 * base, 2),
    }


def leitura(comp: Mapping[str, Any], contra: Mapping[str, Any]) -> str:
    """Frase gerada por regra: o grupo atípico é geografia, tamanho ou voto?"""
    cv = contra["cramer_v"]
    reg = sorted((r["pct_da_regiao"] for r in comp["regioes"]), key=float)
    pequena = contra["tamanho"][0]
    disp = sorted(comp["dispersao_relativa"].items(), key=lambda kv: -kv[1])[:2]
    nomes = {
        "lula1": "Lula no 1º turno",
        "flavio1": "Flávio no 1º turno",
        "outros1": "terceira via no 1º turno",
        "brancos1": "brancos no 1º turno",
        "nulos1": "nulos no 1º turno",
        "lula2": "Lula no 2º turno",
        "flavio2": "Flávio no 2º turno",
        "brancos2": "brancos no 2º turno",
        "nulos2": "nulos no 2º turno",
    }
    geo = (
        f"O grupo atípico pesa de {num(reg[0], 2)}% a {num(reg[-1], 2)}% das seções de "
        f"cada região, e o V de Cramér entre ele e a região é {num(cv['regiao'], 3)}"
        f" (UF: {num(cv['uf'], 3)})"
    )
    tam = (
        f"; com a faixa de aptos, {num(cv['tamanho'], 3)}: "
        f"{num(pequena['pct_da_faixa'], 1)}% das seções de {pequena['tamanho']} aptos "
        f"caem nele, contra {num(contra['pct_pais'], 2)}% do país "
        f"({num(pequena['razao'], 1)} vezes), e seções com menos de 200 aptos são "
        f"{num(contra['pct_grupo_menos_200_aptos'], 1)}% do grupo contra "
        f"{num(contra['pct_pais_menos_200_aptos'], 1)}% do país"
    )
    dis = "; o desvio entre as seções do grupo é " + " e ".join(
        f"{num(v, 1)} vezes o do país em {nomes[k]}" for k, v in disp
    )
    return geo + tam + dis + "."


def cruzamentos(d: pd.DataFrame) -> dict[str, Any]:
    """Grupo contra região, UF, modelo da urna e faixa de aptos, com V de Cramér."""
    t = d.assign(_cl=d["grupo"])
    modelo = [
        {("pct_do_modelo" if k == "pct_da_modelo" else k): v for k, v in linha.items()}
        for linha in _cruzar(t, "modelo", "modelo")
    ]
    tamanho = [
        {("pct_da_faixa" if k == "pct_da_tamanho" else k): v for k, v in linha.items()}
        for linha in _cruzar(t, "tamanho", "tamanho")
    ]
    return {
        "cluster_regiao": _cruzar(t, "regiao", "regiao"),
        "cluster_uf": _cruzar(t, "uf", "uf"),
        "cluster_modelo": modelo,
        "cluster_tamanho": tamanho,
        "cramer_v_regiao": r2(cramer(t["_cl"], t["regiao"]), 3),
        "cramer_v_uf": r2(cramer(t["_cl"], t["uf"]), 3),
        "cramer_v_modelo": r2(cramer(t["_cl"], t["modelo"]), 3),
        "cramer_v_tamanho": r2(cramer(t["_cl"], t["tamanho"]), 3),
    }


def elipse(q: np.ndarray, c: int, nivel: float = NIVEL_ELIPSE) -> dict[str, Any]:
    """Centro, semieixos (``nivel`` desvios) e ângulo (graus) da nuvem no plano."""
    cov = np.cov(q, rowvar=False, bias=True) if len(q) > 1 else np.zeros((2, 2))
    val, vec = np.linalg.eigh(cov)
    val = np.clip(val, 0, None)
    i = int(np.argmax(val))
    ang = float(np.degrees(np.arctan2(vec[1, i], vec[0, i])))
    if ang > 90:
        ang -= 180
    elif ang <= -90:
        ang += 180
    return {
        "cluster": c,
        "cx": r2(q[:, 0].mean(), 4),
        "cy": r2(q[:, 1].mean(), 4),
        "rx": r2(nivel * np.sqrt(val[i]), 4),
        "ry": r2(nivel * np.sqrt(val[1 - i]), 4),
        "ang": r2(ang, 2),
    }


def pca(
    z: np.ndarray,
    rot: np.ndarray,
    score: np.ndarray,
    ufs: np.ndarray,
    anom: int,
    max_pontos: int = MAX_PONTOS,
) -> dict[str, Any]:
    """Dois componentes principais das nove frações padronizadas.

    Pontos: amostra estratificada por grupo (proporcional, ao menos 300 por
    grupo), cerca de ``max_pontos``, mais as 300 seções menos prováveis do país.
    Elipses com todas as seções de cada grupo.
    """
    modelo, p, cargas = projecao(z)
    n = len(z)
    rng = np.random.default_rng(SEMENTE_PCA)
    top = np.argsort(score, kind="stable")[:TOP_PCA]
    topset = {int(i) for i in top}
    escolhidos = set(topset)
    for c in np.unique(rot):
        idx = np.flatnonzero(rot == c)
        alvo = min(len(idx), max(MIN_POR_GRUPO, round(max_pontos * len(idx) / n)))
        escolhidos.update(int(i) for i in rng.choice(idx, size=alvo, replace=False))
    pontos = [
        [r2(p[i, 0], 3), r2(p[i, 1], 3), int(rot[i]), int(i in topset), str(ufs[i])]
        for i in sorted(escolhidos)
    ]
    return {
        "base": (
            "dois componentes principais das nove frações do eleitorado padronizadas "
            "(média zero, desvio-padrão um), mesmo espaço da mistura"
        ),
        "colunas": ["x", "y", "cluster", "top", "uf"],
        "top": TOP_PCA,
        "pontos": pontos,
        "n_pontos": len(pontos),
        "variancia_explicada": [r2(v, 4) for v in modelo.explained_variance_ratio_],
        "cargas": [
            {"feature": k, "pc1": r2(cargas[0, i], 4), "pc2": r2(cargas[1, i], 4)}
            for i, k in enumerate(COLUNAS)
        ],
        "elipses": [elipse(p[rot == c], int(c)) for c in np.unique(rot)],
        "elipse_nivel": (
            f"{num(NIVEL_ELIPSE, 0)} desvios-padrão no plano (cerca de 86% de uma "
            "normal bivariada); ângulo em graus, sentido anti-horário a partir do eixo x"
        ),
        "anomalo": anom,
    }
