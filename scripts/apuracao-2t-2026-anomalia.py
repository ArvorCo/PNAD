#!/usr/bin/env python3
"""Mistura gaussiana sobre as seções do Brasil nos dois turnos de 2026 (anomalia).

Lê, só para leitura, os BUs por seção do 1º e do 2º turno
(``apuracao/data/secoes_2026.sqlite`` e ``secoes_2t_2026.sqlite``), escolhe o
número de grupos pela regra declarada (joelho do BIC, ICL como alternativa),
ajusta a mistura na base inteira até a convergência, contrasta com o k-means e
descreve o grupo mais atípico. Grava:

- ``analysis/apuracao_2t_2026/dados/anomalia_ml.json`` (compacto, no git);
- ``analysis/apuracao_2t_2026/dados/anomalia_ml.md`` (memorando);
- ``data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz`` (uma linha por seção,
  fora do git; ponteiro em ``secoes_arquivo``).

Contrato: ``analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md``. Atipicidade
estatística não é irregularidade; o grupo pede explicação, não prova nada. Uso:

    python3 scripts/apuracao-2t-2026-anomalia.py                  # base inteira
    python3 scripts/apuracao-2t-2026-anomalia.py --amostra 60000  # rascunho
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from apuracao_2t_2026 import anomalia_base as ab
from apuracao_2t_2026 import anomalia_descricao as ad
from apuracao_2t_2026 import anomalia_linhas as al
from apuracao_2t_2026 import anomalia_motor as am
from apuracao_2t_2026 import anomalia_texto as at
from apuracao_2t_2026 import anomalia_voto as av
from apuracao_2t_2026 import secoes_linhas, secoes_ref
from apuracao_2t_2026.urnas_base import BANCO_1T, BANCO_2T
from apuracao_2026.secoes_base import r2
from apuracao_2026.secoes_clusters_diag import convergencia, resumir
from apuracao_2026.secoes_clusters_motor import (
    amostra_estratificada,
    mahalanobis_proprio,
)
from politize_se import fontes as pf
from sklearn.metrics import adjusted_rand_score

ROOT = Path(__file__).resolve().parents[1]
SAIDA = ROOT / "analysis/apuracao_2t_2026/dados"
SECOES_JSON = SAIDA / "secoes.json"
REGUA = ROOT / "apuracao/data/referencia_1t_secoes.json"
INDICE = ROOT / "docs/assets/politize/dados/indice.json"
ZONAS = ROOT / "docs/assets/politize/dados/zona"
N_AMOSTRAS = 50
ROTULO = at.ROTULO
EQUIVALENCIA = (
    "A mistura gaussiana com covariância completa é invariante a transformações afins "
    "invertíveis: trocar as quatro colunas do 2º turno pelas diferenças entre turnos "
    "(Lula, Flávio, brancos e nulos do 2T menos os do 1T) muda só a parametrização. "
    "A partição no ótimo é a mesma e a log-verossimilhança só muda pelo logaritmo do "
    "determinante da troca (zero para as diferenças em pontos; constante quando cada "
    "enquadramento é padronizado). Por isso o ajuste é feito nos níveis padronizados e "
    "os centros são publicados também em diferenças. A inicialização por k-means não "
    "é invariante, e partidas diferentes podem parar em ótimos locais diferentes; por "
    "isso fica a maior log-verossimilhança entre as 16 partidas."
)
LIMITES = [
    "Atipicidade estatística não é irregularidade: o grupo atípico pede explicação, "
    "não prova nada, e nenhuma seção individual é acusada.",
    "O número de grupos é escolha por regra declarada antes de ver os grupos (joelho "
    "do BIC a 5% da queda total, ICL como alternativa); outra regra daria outro k.",
    "O grupo depende do espaço escolhido: nove frações do eleitorado, padronizadas. "
    "Outra padronização, outras variáveis (tamanho, renda, biometria) ou outro modelo "
    "formariam outros grupos.",
    "O grupo foi definido pelas próprias frações de voto; comparar o voto dele com o "
    "das vizinhas descreve o tamanho da diferença, não é teste independente.",
    "Seções pequenas têm frações mais instáveis (um eleitor move mais de um ponto em "
    "seção com menos de 100 aptos), e a mistura lê essa instabilidade como dispersão.",
    "O exterior fica fora (abstenção muito acima da média formaria um grupo só com "
    "essas urnas), assim como seções sem boletim em um dos turnos ou com menos de 30 "
    "aptos.",
    "A densidade é a do modelo ajustado: 'entre as 1% menos prováveis' é posição "
    "relativa no país, não probabilidade de erro ou de irregularidade.",
    "Frações discretas (zero branco, zero nulo) deixam a verossimilhança crescer sem "
    "limite quando um componente se cola num valor exato; essas partidas degeneradas "
    "(menor autovalor da covariância abaixo de 0,0001 nas coordenadas padronizadas) "
    "ficam fora da escolha por regra declarada e são contadas.",
    "O ICL mínimo em k = 2 mostra grupos sobrepostos: a mistura descreve regiões de "
    "uma nuvem contínua, e uma seção perto da fronteira poderia cair no grupo vizinho.",
]
ICL = (
    "ICL = BIC + 2 × entropia das responsabilidades (−Σ τ log τ), na escala de −2 log L "
    "do BIC (Biernacki, Celeux e Govaert, 2000); penaliza grupos sobrepostos"
)


def gravar_json(caminho: Path, obj: dict[str, Any]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_name(f".{caminho.name}.tmp")
    tmp.write_text(
        json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
        encoding="utf-8",
    )
    tmp.replace(caminho)


def sinais(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, str, int]:
    """Sinais por seção do 2T (``secoes.json``) cruzados com o universo.

    Devolve a tabela com os sinais (ordem das linhas preservada), as linhas de
    ``secoes.json``, o SHA-256 dele e quantas seções do universo têm sinal.
    """
    S = json.loads(SECOES_JSON.read_text(encoding="utf-8"))
    b = secoes_linhas.exigir(S)
    sig = pd.DataFrame(b["linhas"], columns=b["colunas"])
    bools = ["contingencia", *[c for c, _ in ad.SINAIS_SEIS]]
    d = df.merge(sig[[*ab.CHAVE, "escore", *bools]], on=ab.CHAVE, how="left")
    if len(d) != len(df) or not (d["grupo"].to_numpy() == df["grupo"].to_numpy()).all():
        raise AssertionError("cruzamento com secoes.json mudou as linhas")
    for c in bools:
        d[c] = d[c].astype("boolean")
    return d, sig, ab.sha256(SECOES_JSON), int(d["escore"].notna().sum())


def mudancas(df: pd.DataFrame) -> np.ndarray:
    """Seção com mudança real de local entre os turnos (cadastro do Politize)."""
    marca = set()
    for uf in sorted(df["uf"].unique()):
        for (z, s), m in pf.mudancas(uf).items():
            if m["real"]:
                marca.add((uf, z, s))
    return np.array(
        [
            (u, int(z), int(s)) in marca
            for u, z, s in zip(df["uf"], df["zona"], df["secao"], strict=True)
        ]
    )


def equivalencia(
    zn: np.ndarray,
    zd: np.ndarray,
    idx: np.ndarray,
    k: int,
    gm_niveis: Any,
    logdet: float,
) -> dict[str, Any]:
    """Mesmas partidas nos deltas padronizados, na amostra da escolha de k."""
    linhas, modelos = am.tabela_bic(zd[idx], ks=(k,))
    gd = modelos[k]
    ll_n = float(gm_niveis.score(zn[idx]))
    ll_d = float(gd.score(zd[idx]))
    return {
        "amostra": len(idx),
        "k": k,
        "ari_particoes": r2(
            adjusted_rand_score(am.prever(gm_niveis, zn[idx]), am.prever(gd, zd[idx])),
            6,
        ),
        "loglik_media_niveis": r2(ll_n, 6),
        "loglik_media_deltas": r2(ll_d, 6),
        "logdet_transformacao": r2(logdet, 6),
        "diferenca_ajustada": r2(ll_d - (ll_n - logdet), 6),
        "partida_deltas": {"semente": linhas[0]["semente"], "init": linhas[0]["init"]},
    }


def ajuste_principal(
    z: np.ndarray, k: int, paralelo: bool
) -> tuple[Any, dict[str, Any], float]:
    """As 16 partidas na base, o diagnóstico de convergência e o ajuste adotado."""
    t0 = time.time()
    aj = am.ajustar_base(z, k, paralelo=paralelo)
    diag, gm = convergencia(z, aj, "continua")
    ap = diag["apertado"]
    ap["degenerou"] = False
    if ap["adotado"] and am.degenerada(gm):
        # a continuação colou um componente num valor exato: fica a partida
        gm = aj.gm
        ap["adotado"] = False
        ap["degenerou"] = True
    if not gm.converged_ or am.degenerada(gm):
        raise RuntimeError(
            "o ajuste adotado não convergiu ou degenerou; nada é publicado"
        )
    seg = time.time() - t0
    escolhida = am.prever(gm, z)
    validas = []
    for linha, (_s, _i, g) in zip(aj.log, aj.todos, strict=True):
        if am.valida(linha):
            linha["ari_com_escolhida"] = r2(
                adjusted_rand_score(escolhida, am.prever(g, z)), 4
            )
            validas.append(linha)
    diag["ajustes"] = validas
    diag["degeneradas"] = sum(r["degenerada"] for r in aj.log)
    diag["nao_convergiram"] = sum(not r["convergiu"] for r in aj.log)
    resumir(diag)
    if diag["degeneradas"]:
        diag["frase"] += (
            f" {diag['degeneradas']} de {len(aj.log)} partidas degeneraram (um componente"
            " colado num valor exato de uma fração, com variância no piso de"
            " regularização) e ficaram fora da escolha e desta conta."
        )
    lls = [r["loglik_media"] for r in validas]
    maximo = max(lls)
    partida = next(
        r for r in aj.log if r["semente"] == aj.semente and r["init"] == aj.init
    )
    ajuste = {
        "covariancia": "full",
        "n_init": 1,
        "inits": list(am.INITS),
        "sementes": aj.log,
        "random_state": aj.semente,
        "init": aj.init,
        "convergiu": bool(gm.converged_),
        "iteracoes": int(gm.n_iter_),
        "iteracoes_partida": partida["iteracoes"],
        "continuacao_adotada": bool(ap["adotado"]),
        "sementes_no_maximo": sum(v >= maximo - am.EMPATE_LOGLIK for v in lls),
        "partidas_validas": len(validas),
        "partidas_degeneradas": diag["degeneradas"],
        "tol": float(gm.tol),
        "max_iter": int(gm.max_iter),
        "tol_partidas": am.TOL,
        "max_iter_partidas": am.MAX_ITER,
        "max_dobras": am.MAX_DOBRAS,
        "limiar_degenerada": am.LIMIAR_DEGENERADA,
        "min_autovalor": float(f"{am.min_autovalor(gm):.3e}"),
        "reg_covar": am.REG_COVAR,
        "loglik_media": r2(float(gm.score(z)), 6),
        "segundos": r2(seg, 1),
        "diagnostico_convergencia": diag,
    }
    return gm, ajuste, seg


def refazer_textos() -> None:
    """Refaz leitura, conclusão e memorando a partir do JSON gravado, sem reajustar."""
    A = json.loads((SAIDA / "anomalia_ml.json").read_text(encoding="utf-8"))
    ma = A["mais_anomalo"]
    comp = A["componentes"][ma["id"]]
    ma["leitura"] = ad.leitura(comp, ma["contra"])
    ma["conclusao"] = ad.conclusao(comp, ma["contra"], ma["voto"])
    gravar_json(SAIDA / "anomalia_ml.json", A)
    (SAIDA / "anomalia_ml.md").write_text(at.memorando(A), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--amostra", type=int, default=None, help="rascunho: N seções")
    ap.add_argument("--sem-cache", action="store_true")
    ap.add_argument("--serial", action="store_true", help="sem processos paralelos")
    ap.add_argument(
        "--so-texto",
        action="store_true",
        help="só refaz o memorando a partir do JSON gravado, sem reajustar",
    )
    a = ap.parse_args()
    if a.so_texto:
        refazer_textos()
        return
    paralelo = not a.serial
    t_ini = time.time()

    t1 = ab.ler_com_cache(BANCO_1T, "1t", not a.sem_cache)
    t2 = ab.ler_com_cache(BANCO_2T, "2t", not a.sem_cache)
    df, excl = ab.unir(t1, t2)
    conf = ab.conferir_comparecimento(df)
    universo_total = len(df)
    if a.amostra:
        df = ab.amostra_universo(df, a.amostra, am.SEMENTE)
    print(f"universo {universo_total} seções; em uso {len(df)}", flush=True)

    f = ab.fracoes(df)
    zn, media, dp = ab.padronizar(ab.matriz(f, ab.COLUNAS))
    zd, _, _ = ab.padronizar(ab.matriz(f, ab.COLUNAS_DELTA))
    logdet = ab.logdet_transformacao(f)

    idx_bic = amostra_estratificada(df["uf"].to_numpy(), am.AMOSTRA_BIC, am.SEMENTE)
    t0 = time.time()
    bic, modelos_bic = am.tabela_bic(zn[idx_bic], paralelo=paralelo)
    escolha = am.escolher_k(bic)
    k = escolha["k_escolhido"]
    print(f"BIC em {time.time() - t0:.0f}s; k* = {k} ({escolha['origem']})", flush=True)
    eq = equivalencia(zn, zd, idx_bic, k, modelos_bic[k], logdet)
    print(f"equivalência afim: {eq}", flush=True)

    gm, ajuste, seg = ajuste_principal(zn, k, paralelo)
    print(f"ajuste em {seg:.0f}s; iterações {ajuste['iteracoes']}", flush=True)

    bruto = am.prever(gm, zn)
    mapa = am.ordem_por_lula2(bruto, f["lula2"].to_numpy(), k)
    rot = mapa[bruto]
    inv = np.argsort(mapa)
    covs = np.asarray(gm.covariances_)[inv]
    pesos = np.asarray(gm.weights_)[inv]
    medias = np.asarray(gm.means_)[inv]
    score, p = am.pontuar(gm, zn)
    maha = mahalanobis_proprio(gm, zn, bruto)

    d = pd.concat([df, f], axis=1)
    d["grupo"] = rot
    d["score"] = score
    d["p"] = p
    d["maha"] = maha
    d["modelo"] = d["modelo_urna_2"].fillna("sem modelo")
    d["tamanho"] = ab.faixa_aptos(d["aptos_2"])
    d["mudanca"] = mudancas(d)
    d, sig, sha_secoes, n_sinais = sinais(d)

    pais = ad.referencia_pais(f)
    pct_sec = ad.pct_maior_resto(np.bincount(rot, minlength=k))
    comps = [
        ad.componente(d, c, covs[c], pesos[c], medias[c], (media, dp), pais, pct_sec[c])
        for c in range(k)
    ]
    ad.rotulos_unicos(comps)
    postos = am.postos_anomalo(
        [c["loglik_media"] for c in comps], [c["dispersao_logdet"] for c in comps]
    )
    anom = postos[0]["id"]
    segundo = postos[1]
    d["anomalo"] = (d["grupo"] == anom).astype(int)

    t0 = time.time()
    km = am.kmeans_contraste({"niveis": zn, "niveis_e_deltas": zd}, paralelo=paralelo)
    ari_km = {
        nome: r2(
            adjusted_rand_score(rot, next(r["rot"] for r in res if r["k"] == k)), 4
        )
        for nome, res in km.items()
    }
    print(f"k-means em {time.time() - t0:.0f}s; ARI {ari_km}", flush=True)

    sel = (d["grupo"] == anom).to_numpy()
    contra = ad.atipico_contra(d, sel)
    voto = av.voto(d, pd.Series(sel, index=d.index))
    regua, _locais, _meta = secoes_ref.ler_regua(REGUA)
    ctx = av.contexto_explicacao(sig, regua)
    nomes = secoes_ref.nomes_municipios(INDICE)
    ordem_anom = np.flatnonzero(sel)[np.argsort(score[sel], kind="stable")][:N_AMOSTRAS]
    ordem_pais = np.argsort(score, kind="stable")[:N_AMOSTRAS]
    zonas = [
        (d["uf"].iat[i], int(d["zona"].iat[i]))
        for i in np.concatenate([ordem_anom, ordem_pais])
    ]
    politize = secoes_ref.locais_politize(ZONAS, zonas)

    linhas = [
        [u, m, int(z), int(s), int(g), r2(sc, 3), r2(pp, 4), int(an)]
        for u, m, z, s, g, sc, pp, an in zip(
            d["uf"],
            d["mun"],
            d["zona"],
            d["secao"],
            d["grupo"],
            d["score"],
            d["p"],
            d["anomalo"],
            strict=True,
        )
    ]
    ponteiro = al.gravar(al.COLUNAS, linhas)

    cruz = ad.cruzamentos(d)
    out: dict[str, Any] = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rotulo": ROTULO,
        "rascunho": {"amostra": len(df)} if a.amostra else None,
        "fonte": {
            "banco_1t": str(BANCO_1T.relative_to(ROOT)),
            "banco_2t": str(BANCO_2T.relative_to(ROOT)),
            "banco_1t_sha256": ab.sha256(BANCO_1T),
            "banco_2t_sha256": ab.sha256(BANCO_2T),
            "secoes_json": str(SECOES_JSON.relative_to(ROOT)),
            "secoes_json_sha256": sha_secoes,
            "regua_1t": str(REGUA.relative_to(ROOT)),
            "mudancas": "docs/assets/politize/dados/mudancas (mudanca_real)",
        },
        "universo": {
            "secoes": len(df),
            "secoes_universo": universo_total,
            "aptos_min": ab.APTOS_MIN,
            "excluidas": excl,
            "comparecimento_divergente": conf,
            "com_sinais_secoes_json": n_sinais,
        },
        "features": {
            "colunas": list(ab.COLUNAS),
            "unidade": "pct do eleitorado",
            "padronizacao": {
                c: {"media": r2(float(media[i]), 6), "desvio": r2(float(dp[i]), 6)}
                for i, c in enumerate(ab.COLUNAS)
            },
            "equivalencia_afim": EQUIVALENCIA,
            "equivalencia_afim_verificacao": eq,
            "colunas_delta": list(ab.COLUNAS_DELTA),
        },
        "amostra_bic": {
            "secoes": len(idx_bic),
            "estratos": "uf",
            "semente": am.SEMENTE,
        },
        "bic": bic,
        "icl_definicao": ICL,
        **{k_: escolha[k_] for k_ in ("k_escolhido", "k_joelho_bic", "k_min_icl")},
        "k": k,
        "k_min_bic": escolha["k_min_bic"],
        "regra": escolha["regra"],
        "regra_declarada": escolha["regra_declarada"],
        "regra_origem": escolha["origem"],
        "quedas_bic": escolha["quedas"],
        "ajuste": ajuste,
        "kmeans": {
            "parametros": {
                "n_init": am.KM_N_INIT,
                "max_iter": am.KM_MAX_ITER,
                "tol": am.KM_TOL,
                "random_state": am.SEMENTE,
                "silhueta_amostra": min(len(df), am.SILHUETA_N),
            },
            **{
                nome: [
                    {
                        "k": r["k"],
                        "inercia": r2(r["inercia"], 1),
                        "silhueta": r2(r["silhueta"], 4),
                        "iteracoes": r["iteracoes"],
                        "convergiu": r["convergiu"],
                    }
                    for r in res
                ]
                for nome, res in km.items()
            },
            "ari_com_mistura_k_estrela": ari_km,
        },
        "pais": {
            "secoes": len(d),
            "aptos_medio": r2(d["aptos_2"].mean(), 1),
            "pequenas_pct": r2(100 * float((d["aptos_2"] < 100).mean()), 2),
            "centro_pct_eleitorado": {c: r2(float(f[c].mean()), 3) for c in ab.COLUNAS},
            "descritores": {
                c: {"media": r2(m, 4), "desvio": r2(s_, 4)}
                for c, (m, s_) in pais.items()
            },
        },
        "sinais_pais": ad.sinais_grupo(d),
        "componentes": comps,
        "mais_anomalo": {
            "id": anom,
            "criterio": (
                "soma dos postos de menor log-verossimilhança média e de maior "
                "dispersão (log-determinante da covariância); empate pela menor "
                "log-verossimilhança média, como no 1º turno."
            ),
            "postos": postos,
            "segundo": {
                "id": segundo["id"],
                "diferenca_postos": segundo["soma_postos"] - postos[0]["soma_postos"],
            },
            "seis_sinais": ad.seis_sinais(d, sel),
            "contra": contra,
            "leitura": ad.leitura(comps[anom], contra),
            "conclusao": ad.conclusao(comps[anom], contra, voto),
            "voto": voto,
            "amostras": av.amostras(d, ordem_anom, nomes, ctx, politize),
        },
        "menos_provaveis": av.amostras(d, ordem_pais, nomes, ctx, politize),
        **cruz,
        "pca": ad.pca(zn, rot, score, d["uf"].to_numpy(), anom),
        "secoes_arquivo": ponteiro,
        "limites": LIMITES,
        "segundos_total": None,
    }
    out["segundos_total"] = r2(time.time() - t_ini, 1)
    gravar_json(SAIDA / "anomalia_ml.json", out)
    (SAIDA / "anomalia_ml.md").write_text(at.memorando(out), encoding="utf-8")
    print(
        f"k={k} atípico={anom} ({comps[anom]['secoes']} seções); "
        f"{out['segundos_total']:.0f}s",
        flush=True,
    )


if __name__ == "__main__":
    main()
