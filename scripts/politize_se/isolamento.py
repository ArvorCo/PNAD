"""Isolation Forest descritivo de combinações eleitorais agregadas.

Quatro ajustes nacionais independentes, uma unidade = um peso em cada nível.
Ausência, grupos de seções alterados e contagens inconsistentes não viram zero.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import sklearn
from scipy.stats import rankdata, spearmanr
from sklearn.ensemble import IsolationForest

from .fontes import ROOT, linhas
from .saida import gravar

ORIGEM = ROOT / "docs/assets/politize_se/dados/zona"
SAIDA = ROOT / "docs/assets/politize_se/isolamento"
NIVEIS = ("secoes", "locais", "zonas", "municipios")
SEMENTES = (20261029, 731, 991)
COLUNAS = [
    "percentil",
    "percentil_min",
    "percentil_max",
    "score",
    "secoes_usadas",
    "secoes_total",
    "aptos2",
    "percentil_porte",
    "faixa_porte",
]
CONTAGENS = [
    "aptos1",
    "comp1",
    "flavio1",
    "lula1",
    "terceira1",
    "brancos1",
    "nulos1",
    "aptos2",
    "comp2",
    "flavio2",
    "lula2",
    "brancos2",
    "nulos2",
]
FEATURES = [
    {
        "id": "fatia_f2",
        "nome": "Flávio entre os dois candidatos no 2º turno",
        "formula": "flavio2 / (flavio2 + lula2)",
    },
    {
        "id": "bn2",
        "nome": "Brancos e nulos entre presentes no 2º turno",
        "formula": "(brancos2 + nulos2) / comp2",
    },
    {"id": "abst2", "nome": "Abstenção no 2º turno", "formula": "1 - comp2 / aptos2"},
    {
        "id": "delta_f",
        "nome": "Mudança da parcela de Flávio entre os dois",
        "formula": "fatia_f2 - flavio1 / (flavio1 + lula1)",
    },
    {
        "id": "delta_bn",
        "nome": "Mudança de brancos e nulos",
        "formula": "bn2 - (brancos1 + nulos1) / comp1",
    },
    {
        "id": "delta_abst",
        "nome": "Mudança de abstenção",
        "formula": "abst2 - (1 - comp1 / aptos1)",
    },
    {
        "id": "terceira1",
        "nome": "Terceira via entre válidos do 1º turno",
        "formula": "terceira1 / (flavio1 + lula1 + terceira1)",
    },
]
NOTA = (
    "Combinações de resultados agregados, comparadas nacionalmente dentro de cada nível. "
    "Percentil alto significa maior isolamento estatístico; não é probabilidade de "
    "irregularidade, fraude, causalidade ou voto individual. O 1% superior é uma "
    "convenção de exploração, existente por construção, não teste de hipótese. "
    "Estrutura regional, diferenças sociais e tamanho das seções podem produzir "
    "combinações raras legítimas."
)


def elegibilidade(r: dict) -> str:
    """Valida pares de BUs completos e comparáveis antes de qualquer agregação."""
    if r.get("pequena") or any(
        isinstance(r.get(c), (int, float)) and r[c] < 30 for c in ("aptos1", "aptos2")
    ):
        return "pequena"
    if not r.get("bu2"):
        return "sem_bu2"
    if any(r.get(c) is None for c in CONTAGENS):
        return "contagem_ausente"
    if any(type(r[c]) is not int or r[c] < 0 for c in CONTAGENS):
        return "contagem_invalida"
    if r.get("agregadas1") is None or r.get("agregadas2") is None:
        return "agregacao_ausente"
    if not r.get("agreg_igual") or set(r["agregadas1"]) != set(r["agregadas2"]):
        return "agregacao_alterada"
    for t in (1, 2):
        total = sum(r[f"{c}{t}"] for c in ("flavio", "lula", "brancos", "nulos"))
        if t == 1:
            total += r["terceira1"]
        if total != r[f"comp{t}"] or r[f"comp{t}"] > r[f"aptos{t}"]:
            return "conservacao"
        if r[f"flavio{t}"] + r[f"lula{t}"] == 0:
            return "sem_voto_nos_dois"
    return ""


def vetor(r: dict) -> list[float]:
    """Taxas calculadas sobre somas, nunca médias de taxas de seções."""
    f = [r[f"flavio{t}"] / (r[f"flavio{t}"] + r[f"lula{t}"]) for t in (1, 2)]
    bn = [(r[f"brancos{t}"] + r[f"nulos{t}"]) / r[f"comp{t}"] for t in (1, 2)]
    abst = [1 - r[f"comp{t}"] / r[f"aptos{t}"] for t in (1, 2)]
    terceira = r["terceira1"] / (r["flavio1"] + r["lula1"] + r["terceira1"])
    return [
        f[1],
        bn[1],
        abst[1],
        f[1] - f[0],
        bn[1] - bn[0],
        abst[1] - abst[0],
        terceira,
    ]


def percentis(scores: np.ndarray) -> np.ndarray:
    """Empates conservam rank médio; observação única fica no percentil 50."""
    return 100 * (rankdata(scores, method="average") - 0.5) / len(scores)


def ajustar(x: np.ndarray, arvores: int = 256) -> tuple[np.ndarray, dict]:
    """Média dos scores de três florestas; ranks individuais medem estabilidade."""
    if len(x) < 2 or not np.isfinite(x).all():
        raise ValueError("Ajuste exige ao menos duas unidades e vetores finitos")
    scores = []
    for seed in SEMENTES:
        m = IsolationForest(
            n_estimators=arvores,
            max_samples=min(1024, len(x)),
            max_features=1.0,
            contamination="auto",
            random_state=seed,
            n_jobs=1,
        ).fit(x)
        scores.append(-m.score_samples(x))
    raw = np.asarray(scores)
    ranks = np.asarray([percentis(s) for s in raw])
    media = raw.mean(axis=0)
    principal = percentis(media)
    # Inclui o rank final nos limites para que o intervalo sempre contenha o valor exibido.
    limites = np.vstack([ranks, principal])
    resultado = np.column_stack(
        [principal, limites.min(axis=0), limites.max(axis=0), media]
    )
    overlaps = []
    correlacoes = []
    for i, j in combinations(range(len(SEMENTES)), 2):
        a, b = ranks[i] >= 99, ranks[j] >= 99
        uniao = int((a | b).sum())
        overlaps.append(float((a & b).sum() / uniao) if uniao else None)
        correlacoes.append(
            float(spearmanr(ranks[i], ranks[j]).statistic)
            if np.ptp(ranks[i]) and np.ptp(ranks[j])
            else None
        )
    return resultado, {
        "jaccard_top1_pares": overlaps,
        "spearman_pares": correlacoes,
        "largura_percentil_mediana": float(np.median(np.ptp(limites, axis=0))),
        "largura_percentil_p95": float(np.percentile(np.ptp(limites, axis=0), 95)),
        "top1_unidades": int((principal >= 99).sum()),
        "nota": "Faixa entre sementes e rank final, não intervalo de confiança.",
    }


def ler(origem: Path) -> tuple[dict, dict]:
    """Retém só contagens e chaves; cada fragmento pesado é liberado após leitura."""
    dados = {nivel: {} for nivel in NIVEIS}
    metas = {}
    for folder in sorted(origem.iterdir()):
        if not folder.is_dir() or folder.name == "ZZ":
            continue
        uf = folder.name
        exclusoes = Counter()
        digest = hashlib.sha256()
        n = usados = 0
        for path in sorted(folder.glob("*.json.gz")):
            raw = path.read_bytes()
            digest.update(path.name.encode())
            digest.update(hashlib.sha256(raw).digest())
            d = json.loads(gzip.decompress(raw))
            locais = list(linhas(d["locais"]))
            for r in linhas(d["secoes"]):
                mun, zona, secao = (
                    str(r["mun_tse"]).zfill(5),
                    str(d["zona"]),
                    str(r["secao"]),
                )
                lid = locais[r["li"]]["local_id"]
                chaves = (f"{mun}-{zona}-{secao}", lid, zona, mun)
                motivo = elegibilidade(r)
                n += 1
                if motivo:
                    exclusoes[motivo] += 1
                else:
                    usados += 1
                for nivel, chave in zip(NIVEIS, chaves, strict=True):
                    key = (uf, chave)
                    if nivel == "secoes" and key in dados[nivel]:
                        raise ValueError(f"Seção duplicada: {key}")
                    g = dados[nivel].setdefault(key, dict.fromkeys(CONTAGENS, 0))
                    g["secoes_total"] = g.get("secoes_total", 0) + 1
                    g.setdefault("secoes_usadas", 0)
                    if not motivo:
                        g["secoes_usadas"] += 1
                        for c in CONTAGENS:
                            g[c] += r[c]
        metas[uf] = {
            "secoes_total": n,
            "secoes_usadas": usados,
            "exclusoes": dict(exclusoes),
            "sha256_fragmentos_origem": digest.hexdigest(),
        }
        print(f"{uf}: {usados}/{n} seções elegíveis", flush=True)
    return dados, metas


def diagnostico_tamanho(registros: list[dict], p: np.ndarray) -> list[dict]:
    out = []
    aptos = np.asarray([r["aptos2"] for r in registros])
    for lo, hi in ((30, 100), (100, 200), (200, 400), (400, None)):
        mask = (aptos >= lo) & ((aptos < hi) if hi else True)
        n = int(mask.sum())
        out.append(
            {
                "aptos_min": lo,
                "aptos_max_exclusivo": hi,
                "unidades": n,
                "top1": int((p[mask] >= 99).sum()),
                "top1_pct": float(100 * (p[mask] >= 99).mean()) if n else None,
            }
        )
    return out


def ranks_porte(registros: list[dict], scores: np.ndarray) -> list[list]:
    """Percentil do mesmo score dentro de faixas de aptos2; não é novo modelo."""
    out = [[None, None] for _ in registros]
    aptos = np.asarray([r["aptos2"] for r in registros])
    for lo, hi, label in (
        (30, 100, "30–99"),
        (100, 200, "100–199"),
        (200, 400, "200–399"),
        (400, None, "400+"),
    ):
        idx = np.flatnonzero((aptos >= lo) & ((aptos < hi) if hi else True))
        if len(idx):
            for i, rank in zip(idx, percentis(scores[idx]), strict=True):
                out[i] = [round(float(rank), 4), label]
    return out


def sensibilidade_porte(
    registros: list[dict], x: np.ndarray, scores: np.ndarray, arvores: int
) -> dict:
    """Reajusta em seções >=200 aptos, sem substituir os scores publicados."""
    mask = np.asarray([min(r["aptos1"], r["aptos2"]) >= 200 for r in registros])
    n = int(mask.sum())
    if n < 2:
        return {"unidades": n, "motivo": "menos_de_duas_unidades"}
    refit, estabilidade = ajustar(x[mask], arvores)
    antigo = percentis(scores[mask])
    a, b = antigo >= 99, refit[:, 0] >= 99
    uniao = int((a | b).sum())
    return {
        "unidades": n,
        "regra": "Ao menos 200 aptos em ambos os turnos; reajuste nacional com as mesmas sete variáveis e sementes.",
        "spearman_rank": (
            float(spearmanr(antigo, refit[:, 0]).statistic)
            if np.ptp(antigo) and np.ptp(refit[:, 0])
            else None
        ),
        "jaccard_top1": float((a & b).sum() / uniao) if uniao else None,
        "estabilidade_refit": estabilidade,
        "nota": "Compara ranks dentro do mesmo subconjunto com e sem as seções menores no ajuste. Não corrige geografia nem valida irregularidade.",
    }


def publicar(origem: Path = ORIGEM, saida: Path = SAIDA, arvores: int = 256) -> dict:
    dados, ufs = ler(origem)
    payloads = {
        uf: {"formato": 1, "uf": uf, "colunas": COLUNAS, **{n: {} for n in NIVEIS}}
        for uf in ufs
    }
    meta = {
        "formato": 1,
        "nota": NOTA,
        "features": FEATURES,
        "ufs": ufs,
        "niveis": {},
        "modelo": {
            "nome": "Isolation Forest",
            "sementes": list(SEMENTES),
            "arvores": arvores,
            "max_samples": 1024,
            "max_features": 1.0,
            "sklearn": sklearn.__version__,
            "numpy": np.__version__,
            "peso": "uma unidade, um peso; ajustes nacionais separados por nível",
            "score": "média de -score_samples das três sementes; maior = mais isolado",
        },
        "regras": [
            "Brasil sem exterior; ao menos 30 aptos em cada turno; BUs com contagens completas e conservadas.",
            "Mesmas seções agregadas nos dois turnos; ausências e pares alterados ficam fora de todos os níveis.",
            "Taxas dos agrupamentos são calculadas depois de somar apenas os pares elegíveis; cobertura explícita.",
            "Local usa a chave cadastral do mapa; mudança de prédio não representa mudança de eleitorado.",
            "Sem renda, sexo, idade, escolaridade, crimes, coordenadas, escores anteriores ou votos absolutos no modelo.",
            "Tamanho não entra no score; diagnóstico separado mostra concentração de seções pequenas no topo.",
            "Percentil da média de scores; empates recebem rank médio. Corte 99 é convenção, não p-value.",
            "Percentil_porte somente nas seções: rank do mesmo score dentro de faixas de aptos2 (30–99, 100–199, 200–399, 400+). Não é novo ajuste nem elimina efeito regional.",
        ],
        "referencias": [
            "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html"
        ],
    }
    for nivel in NIVEIS:
        chaves = sorted(k for k, r in dados[nivel].items() if r["secoes_usadas"])
        registros = [dados[nivel][k] for k in chaves]
        print(f"Ajustando {nivel}: {len(chaves)} unidades", flush=True)
        if len(chaves) < 2:
            meta["niveis"][nivel] = {"unidades": 0, "motivo": "menos_de_duas_unidades"}
            continue
        x = np.asarray([vetor(r) for r in registros], dtype=np.float32)
        resultados, estabilidade = ajustar(x, arvores)
        meta["niveis"][nivel] = {
            "unidades": len(chaves),
            "unidades_total": len(dados[nivel]),
            "estabilidade": estabilidade,
            "totais_elegiveis": {c: sum(r[c] for r in registros) for c in CONTAGENS},
        }
        if nivel == "secoes":
            meta["niveis"][nivel]["diagnostico_tamanho"] = diagnostico_tamanho(
                registros, resultados[:, 0]
            )
            meta["niveis"][nivel]["sensibilidade_porte"] = sensibilidade_porte(
                registros, x, resultados[:, 3], arvores
            )
        porte = (
            ranks_porte(registros, resultados[:, 3])
            if nivel == "secoes"
            else [[None, None] for _ in registros]
        )
        for (uf, chave), r, resultado, rank_porte in zip(
            chaves, registros, resultados, porte, strict=True
        ):
            valores = [
                round(float(v), 4 if i < 3 else 6) for i, v in enumerate(resultado)
            ]
            payloads[uf][nivel][chave] = [
                *valores,
                r["secoes_usadas"],
                r["secoes_total"],
                r["aptos2"],
                *rank_porte,
            ]
        del dados[nivel]
    for uf, payload in payloads.items():
        path = saida / f"{uf}.json.gz"
        size = gravar(path, payload)
        ufs[uf].update(
            arquivo=path.name,
            bytes=size,
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    meta["secoes_total"] = sum(m["secoes_total"] for m in ufs.values())
    meta["secoes_usadas"] = sum(m["secoes_usadas"] for m in ufs.values())
    meta["sha256_codigo"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    gravar(saida / "indice.json", meta)
    return meta
