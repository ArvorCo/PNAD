"""Detecção de anomalias por zona eleitoral: funções puras de escore.

O módulo não lê arquivo nem banco. Recebe matrizes e devolve escores, para que
os testes rodem com dados sintéticos e o script de linha de comando
(``scripts/apuracao-2026-anomalias.py``) cuide da leitura do TSE.

Escore alto quer dizer zona estatisticamente atípica dentro da própria UF. Não
quer dizer fraude, erro nem irregularidade: quer dizer que a zona pede
explicação, e a explicação mais comum é tamanho pequeno, área remota ou mudança
de cadastro.
"""

from __future__ import annotations

import importlib.util
import math
from collections import defaultdict
from collections.abc import Sequence

import numpy as np

MAD_K = 1.4826  # MAD vira desvio-padrão sob normalidade
MEDIA_AD_K = 1.2533  # desvio médio absoluto vira desvio-padrão sob normalidade
EPS = 1e-12
Z_TETO = 12.0  # nenhum atributo sozinho passa disso no modelo
RAIO_TERRA_KM = 6371.0


def sklearn_disponivel() -> bool:
    """Diz se o scikit-learn pode ser importado neste ambiente."""
    return importlib.util.find_spec("sklearn") is not None


def escala_robusta(valores: np.ndarray) -> float:
    """Desvio robusto: MAD x 1,4826; se o MAD for zero, desvio médio absoluto.

    Atributo constante devolve 0, e quem chama trata 0 como "sem variação".
    """
    v = np.asarray(valores, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return 0.0
    desvio = np.abs(v - np.median(v))
    mad = MAD_K * float(np.median(desvio))
    if mad > EPS:
        return mad
    media = MEDIA_AD_K * float(np.mean(desvio))
    return media if media > EPS else 0.0


def z_robusto_grupo(
    valores: Sequence[float] | np.ndarray,
    grupos: Sequence[str] | np.ndarray,
    encolhimento: float = 20.0,
) -> tuple[np.ndarray, dict[str, float], dict[str, float]]:
    """Escore z robusto dentro do grupo (UF): mediana e MAD do próprio grupo.

    A escala do grupo é encolhida para a escala nacional dos desvios, com peso
    n / (n + encolhimento): UF com 16 zonas não tem MAD estável sozinha.
    Valores ausentes ficam ausentes; grupo e país sem variação dão z = 0.
    """
    x = np.asarray(valores, dtype=float)
    g = np.asarray(grupos)
    z = np.full(x.shape, np.nan)
    ok = np.isfinite(x)
    desvio = np.full(x.shape, np.nan)
    centros: dict[str, float] = {}
    for grupo in np.unique(g[ok]):
        m = ok & (g == grupo)
        centros[str(grupo)] = float(np.median(x[m]))
        desvio[m] = x[m] - centros[str(grupo)]
    escala_pais = escala_robusta(desvio[ok])
    escalas: dict[str, float] = {}
    for grupo, _ in centros.items():
        m = ok & (g == grupo)
        n = int(m.sum())
        peso = n / (n + encolhimento)
        s_grupo = escala_robusta(desvio[m])
        s = math.sqrt(peso * s_grupo**2 + (1.0 - peso) * escala_pais**2)
        escalas[grupo] = s
        z[m] = desvio[m] / s if s > EPS else 0.0
    return z, centros, escalas


def fator_tamanho(
    z: np.ndarray,
    log_tamanho: np.ndarray,
    n_faixas: int = 10,
    limites: tuple[float, float] = (0.5, 3.0),
) -> tuple[np.ndarray, float]:
    """Quanto o |z| típico cresce quando a zona encolhe.

    Ajusta log(mediana |z| na faixa) = a + b x log(tamanho) sobre faixas de
    tamanho com o mesmo número de zonas, e devolve exp(b x (log n - mediana)),
    limitado a ``limites``. Dividir z por esse fator impede que zona pequena
    domine o escore só por ter variância maior. Devolve também a inclinação b.
    """
    zz = np.asarray(z, dtype=float)
    ln = np.asarray(log_tamanho, dtype=float)
    ok = np.isfinite(zz) & np.isfinite(ln)
    fator = np.ones(zz.shape)
    if ok.sum() < n_faixas * 5:
        return fator, 0.0
    cortes = np.quantile(ln[ok], np.linspace(0.0, 1.0, n_faixas + 1))
    centros, medianas = [], []
    for i in range(n_faixas):
        baixo, alto = cortes[i], cortes[i + 1]
        if i == n_faixas - 1:
            m = ok & (ln >= baixo) & (ln <= alto)
        else:
            m = ok & (ln >= baixo) & (ln < alto)
        if m.sum() < 5:
            continue
        mediana = float(np.median(np.abs(zz[m])))
        if mediana > EPS:
            centros.append(float(np.median(ln[m])))
            medianas.append(math.log(mediana))
    if len(centros) < 3:
        return fator, 0.0
    inclinacao = float(np.polyfit(centros, medianas, 1)[0])
    referencia = float(np.median(ln[ok]))
    fator[ok] = np.exp(inclinacao * (ln[ok] - referencia))
    return np.clip(fator, *limites), inclinacao


def distancias_km(lat: float, lon: float, lats: np.ndarray, lons: np.ndarray):
    """Distância de haversine, em km, de um ponto a vários."""
    p1, p2 = math.radians(lat), np.radians(lats)
    dlat = p2 - p1
    dlon = np.radians(lons) - math.radians(lon)
    a = np.sin(dlat / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin(dlon / 2) ** 2
    return 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def vizinhos_proximos(
    lat: np.ndarray,
    lon: np.ndarray,
    grupos: Sequence[str] | np.ndarray,
    excluir: Sequence[str] | np.ndarray,
    k: int = 5,
) -> list[np.ndarray]:
    """As k zonas mais próximas da mesma UF, fora do mesmo município."""
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    g = np.asarray(grupos)
    ex = np.asarray(excluir)
    saida: list[np.ndarray] = [np.array([], dtype=int) for _ in range(len(lat))]
    for grupo in np.unique(g):
        idx = np.flatnonzero((g == grupo) & np.isfinite(lat) & np.isfinite(lon))
        for i in idx:
            candidatos = idx[ex[idx] != ex[i]]
            if candidatos.size == 0:
                continue
            d = distancias_km(
                float(lat[i]), float(lon[i]), lat[candidatos], lon[candidatos]
            )
            saida[i] = candidatos[np.argsort(d, kind="stable")[:k]]
    return saida


def _media_ponderada(valores: np.ndarray, pesos: np.ndarray) -> float:
    ok = np.isfinite(valores) & np.isfinite(pesos) & (pesos > 0)
    if not ok.any():
        return float("nan")
    return float(np.average(valores[ok], weights=pesos[ok]))


def residuo_hierarquico(
    swing: Sequence[float] | np.ndarray,
    uf: Sequence[str] | np.ndarray,
    municipio: Sequence[str] | np.ndarray,
    peso: Sequence[float] | np.ndarray,
    vizinhos: list[np.ndarray] | None = None,
    encolhimento: float = 2.0,
) -> dict[str, np.ndarray]:
    """Resíduo da zona contra a expectativa UF + município.

    swing_zona = swing_uf + efeito_local + resíduo. O swing da UF é a média
    ponderada pelo peso (votos válidos). O efeito local é a média ponderada dos
    desvios das OUTRAS zonas do mesmo município (deixa-uma-fora), encolhida por
    n / (n + encolhimento). Município com uma zona só usa as zonas vizinhas mais
    próximas de outros municípios da UF. Sem nenhum dos dois, efeito zero.
    """
    s = np.asarray(swing, dtype=float)
    u = np.asarray(uf)
    mun = np.asarray(municipio)
    w = np.asarray(peso, dtype=float)
    swing_uf = np.full(s.shape, np.nan)
    for grupo in np.unique(u):
        m = u == grupo
        swing_uf[m] = _media_ponderada(s[m], w[m])
    desvio = s - swing_uf
    por_mun: dict[str, list[int]] = defaultdict(list)
    for i, chave in enumerate(mun):
        por_mun[str(chave)].append(i)
    efeito = np.zeros(s.shape)
    fonte = np.full(s.shape, "uf", dtype=object)
    for i in range(len(s)):
        outros = np.array(
            [j for j in por_mun[str(mun[i])] if j != i and np.isfinite(desvio[j])],
            dtype=int,
        )
        origem = "municipio"
        if outros.size == 0 and vizinhos is not None:
            outros = np.array(
                [j for j in vizinhos[i] if np.isfinite(desvio[j])], dtype=int
            )
            origem = "vizinhanca"
        if outros.size == 0:
            continue
        media = _media_ponderada(desvio[outros], w[outros])
        if not np.isfinite(media):
            continue
        efeito[i] = media * outros.size / (outros.size + encolhimento)
        fonte[i] = origem
    esperado = swing_uf + efeito
    return {
        "swing_uf": swing_uf,
        "efeito_local": efeito,
        "esperado": esperado,
        "residuo": s - esperado,
        "fonte": fonte,
    }


def percentis(valores: np.ndarray) -> np.ndarray:
    """Posto médio dividido por n: 1 é o maior valor, empates dividem o posto."""
    v = np.asarray(valores, dtype=float)
    n = v.size
    if n == 0:
        return v
    ordem = np.argsort(v, kind="stable")
    postos = np.empty(n)
    ordenados = v[ordem]
    i = 0
    while i < n:
        j = i
        while j + 1 < n and ordenados[j + 1] == ordenados[i]:
            j += 1
        postos[ordem[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return postos / n


def preparar_matriz(z: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Ausente vira 0 (a mediana da UF), corta em ±Z_TETO, tira coluna constante.

    Devolve a matriz e a máscara das colunas mantidas.
    """
    x = np.where(np.isfinite(z), z, 0.0)
    x = np.clip(x, -Z_TETO, Z_TETO)
    mantidas = x.std(axis=0) > EPS
    return x[:, mantidas], mantidas


def mahalanobis_robusta(x: np.ndarray) -> np.ndarray:
    """Distância de Mahalanobis com centro mediano e covariância winsorizada.

    A covariância sai dos z cortados em ±3, para que poucas zonas extremas não
    inflem a própria escala. Usa pseudo-inversa: atributo quase constante ou
    colinear não quebra a conta. Escolhida em vez do MinCovDet porque atributo
    unilateral (metade das zonas em zero) torna singular o subconjunto do MCD.
    """
    centro = np.median(x, axis=0)
    xw = np.clip(x, -3.0, 3.0)
    cov = np.atleast_2d(np.cov(xw, rowvar=False))
    # Pseudo-inversa por autovalores e einsum: o pinv do numpy com Accelerate
    # (macOS) emite aviso espúrio de divisão por zero no matmul.
    autovalores, autovetores = np.linalg.eigh(cov)
    piso = max(float(autovalores.max()), 0.0) * 1e-9
    inverso = np.where(autovalores > piso, 1.0 / np.maximum(autovalores, piso), 0.0)
    projecao = np.einsum("ij,jk->ik", x - centro, autovetores)
    return np.sqrt(
        np.maximum(np.einsum("ik,k,ik->i", projecao, inverso, projecao), 0.0)
    )


def escores_modelos(
    z: np.ndarray,
    semente: int = 0,
    usar_sklearn: bool | None = None,
    n_vizinhos_lof: int = 35,
) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    """Quatro leituras de atipicidade sobre a matriz de z robustos.

    - ``z_rms``: raiz da média dos z ao quadrado;
    - ``mahalanobis``: distância robusta em numpy (centro mediano, covariância
      winsorizada), que leva em conta a correlação entre atributos;
    - ``isolation_forest`` e ``lof``: só com scikit-learn instalado.
    Sem scikit-learn, o conjunto fica nas duas primeiras. Todas crescem com a
    atipicidade.
    """
    x, mantidas = preparar_matriz(np.asarray(z, dtype=float))
    if usar_sklearn is None:
        usar_sklearn = sklearn_disponivel()
    meta: dict[str, object] = {
        "colunas_usadas": int(mantidas.sum()),
        "colunas_constantes": int((~mantidas).sum()),
        "sklearn": bool(usar_sklearn),
    }
    n = x.shape[0]
    if x.shape[1] == 0:
        zeros = np.zeros(n)
        return {"z_rms": zeros, "mahalanobis": zeros.copy()}, meta
    escores: dict[str, np.ndarray] = {
        "z_rms": np.sqrt(np.mean(x**2, axis=1)),
        "mahalanobis": mahalanobis_robusta(x),
    }
    if usar_sklearn:
        from sklearn.ensemble import IsolationForest
        from sklearn.neighbors import LocalOutlierFactor

        # max_samples="auto" é min(256, n), o padrão do artigo original.
        floresta = IsolationForest(
            n_estimators=500, max_samples="auto", random_state=semente
        ).fit(x)
        escores["isolation_forest"] = -floresta.score_samples(x)
        k = max(2, min(n_vizinhos_lof, n - 1))
        lof = LocalOutlierFactor(n_neighbors=k).fit(x)
        escores["lof"] = -lof.negative_outlier_factor_
        meta["lof_vizinhos"] = k
        meta["isolation_forest"] = {"arvores": 500, "amostra": min(256, n)}
    return escores, meta


def escore_combinado(escores: dict[str, np.ndarray]) -> np.ndarray:
    """Média dos percentis de cada leitura, de 0 a 100.

    Escore 99 quer dizer: na média das leituras, a zona é mais atípica que 99%
    das zonas do país. É posição relativa, não probabilidade.
    """
    if not escores:
        raise ValueError("nenhum escore para combinar")
    pcts = np.vstack([percentis(v) for v in escores.values()])
    return 100.0 * pcts.mean(axis=0)


def motivos(
    z_linha: Sequence[float] | np.ndarray,
    nomes: Sequence[str],
    limiar: float = 2.5,
    maximo: int = 3,
) -> list[tuple[str, float]]:
    """Atributos que puxam o escore: |z| >= limiar, do maior para o menor.

    Sem nenhum acima do limiar, a zona é atípica pela combinação; devolve os
    dois maiores |z| mesmo assim, para o leitor ver de onde vem.
    """
    z = np.asarray(z_linha, dtype=float)
    ordem = [int(i) for i in np.argsort(-np.abs(np.nan_to_num(z))) if np.isfinite(z[i])]
    acima = [(nomes[i], float(z[i])) for i in ordem if abs(z[i]) >= limiar]
    if acima:
        return acima[:maximo]
    return [(nomes[i], float(z[i])) for i in ordem[:2]]


def pct_br(valor: float, casas: int = 1) -> str:
    """Fração como porcentagem com vírgula decimal: 0,1234 vira "12,3%"."""
    return f"{100 * valor:.{casas}f}%".replace(".", ",")


def explicacoes(r: dict) -> list[str]:
    """Explicação provável, por regra declarada, a partir dos dados da zona.

    Toda frase é inferência ou hipótese, nunca verificação. A última regra
    (efeito político local) só entra quando nenhuma outra se aplica.
    """
    saida: list[str] = []
    if r.get("incompleta"):
        saida.append(
            f"arquivo de zona parado em {r['st']} de {r['ts']} seções: "
            "números parciais"
        )
    referencia = r.get("referencia_2022", "zona")
    if referencia == "locais":
        saida.append(
            "zona redesenhada desde 2022: base de 2022 recomposta pelos locais "
            "de votação, aproximada"
        )
    elif referencia in ("imprecisa", "ausente"):
        saida.append("sem base comparável de 2022: variações não calculadas")
    if r.get("secoes", 999) <= 15 or r.get("eleitorado", 10**9) < 5000:
        saida.append(f"zona pequena ({r.get('secoes')} seções), variância alta")
    if r.get("pct_indigena", 0.0) >= 0.15:
        saida.append(
            "locais em aldeias ou terra indígena "
            f"({pct_br(r['pct_indigena'], 0)} do eleitorado)"
        )
    if r.get("pct_quilombola", 0.0) >= 0.15:
        saida.append(
            "locais em comunidade quilombola "
            f"({pct_br(r['pct_quilombola'], 0)} do eleitorado)"
        )
    z_atraso = r.get("z_atraso", 0.0)
    if np.isfinite(z_atraso) and z_atraso >= 2.5:
        z22 = r.get("z_atraso_2022", float("nan"))
        if not np.isfinite(z22):
            saida.append("totalização tardia, sem hora comparável de 2022")
        elif z22 >= 1.5:
            saida.append("totalização tardia que já se repetia em 2022: área remota")
        else:
            saida.append(
                "totalização tardia que não se repetia em 2022: pedir a hora de "
                "transmissão de cada seção"
            )
    var = r.get("var_eleitorado", 0.0)
    if np.isfinite(var) and var <= -0.12 and r.get("d_comparecimento", 0.0) > 0:
        saida.append(
            f"eleitorado caiu {pct_br(abs(var), 0)} desde 2022 (revisão de "
            "cadastro): comparecimento sobe pelo denominador"
        )
    z_var = r.get("z_var_eleitorado", 0.0)
    if np.isfinite(var) and np.isfinite(z_var) and z_var >= 2.5 and var > 0:
        saida.append(
            f"eleitorado cresceu {pct_br(var, 0)} desde 2022, bem acima da UF: "
            "transferência de títulos muda a composição da zona"
        )
    z_terc = r.get("z_terceiros", 0.0)
    lider = r.get("terceiro_lider")
    if np.isfinite(z_terc) and z_terc >= 2.5 and lider and lider[1] >= 0.05:
        saida.append(
            f"voto concentrado em terceira via ({lider[0]} {pct_br(lider[1])})"
        )
    if r.get("n_copias_antigas", 0) > 0:
        saida.append("cópia antiga servida pelo CDN registrada: não muda o final")
    vizinhas = r.get("vizinhos_atipicos", 0)
    if vizinhas >= 2:
        saida.append(
            f"padrão regional: {vizinhas} das 5 zonas mais próximas também estão "
            "entre as 5% mais atípicas, o que aponta para efeito político da "
            "região, não para uma urna isolada"
        )
    if not saida:
        saida.append(
            "efeito político local não medido (liderança, prefeitura, "
            "candidatura estadual): hipótese a verificar"
        )
    return saida
