#!/usr/bin/env python3
"""Camada de detecção de anomalias por zona eleitoral, presidente, 1º turno 2026.

Lê os 6.106 pares município-zona do Brasil no banco do coletor
(``apuracao/data/apuracao.sqlite``, só leitura), compara com 2022 por zona,
calcula atributos, roda quatro leituras de atipicidade e grava:

- ``analysis/apuracao_2026/dados/anomalias.json``: todas as zonas com escore,
  as 50 mais atípicas com motivo, explicação provável e localização, a
  reconciliação por UF e o método;
- ``analysis/apuracao_2026/anomalias.md``: método, limites, as 25 primeiras,
  lista pronta para mapa e o parágrafo publicável.

Escore alto não é fraude. É zona que pede explicação, e a explicação provável
vem ao lado, rotulada como inferência ou hipótese. Uso:

    python3 scripts/apuracao-2026-anomalias.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from apuracao_2026 import anomalias as an
from apuracao_2026 import anomalias_dados as dados
from apuracao_2026 import anomalias_texto as texto

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "apuracao/data/apuracao.sqlite"
ZIP_VOTOS_2022 = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"
ZIP_SECOES_2022 = ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip"
ZIP_LOCAIS_2026 = ROOT / "data/raw/tse_eleitorado/eleitorado_local_votacao_2026.zip"
GEO_MUN = ROOT / "apuracao/public/geo/mun"
SAIDA_DIR = ROOT / "analysis/apuracao_2026"
SAIDA_JSON = SAIDA_DIR / "dados/anomalias.json"
SAIDA_MD = SAIDA_DIR / "anomalias.md"
CONTEXTO = SAIDA_DIR / "dados/contexto_seguranca.json"
ZONAS_W1A = SAIDA_DIR / "dados/zonas.json"

N_TOPO = 50
LIMIAR_REDESENHO = 0.20  # |log(razão da zona) - log(razão do município)|
MARGEM_BBOX_GRAUS = 0.25

# Atributos que entram nos modelos. Os eleitorais recebem ajuste de tamanho.
ATRIBUTOS = {
    "d_flavio_1t": ("Flávio 2026 menos Bolsonaro 1º turno 2022", "pp", True),
    "d_flavio_2t": ("Flávio 2026 menos Bolsonaro 2º turno 2022", "pp", True),
    "d_lula_1t": ("Lula 2026 menos Lula 1º turno 2022", "pp", True),
    "d_lula_2t": ("Lula 2026 menos Lula 2º turno 2022", "pp", True),
    "residuo_hierarquico": (
        "variação da margem Flávio menos Lula além da UF e do município",
        "pp",
        True,
    ),
    "d_comparecimento": ("comparecimento 2026 menos 2022", "pp", True),
    "brancos_nulos": ("brancos e nulos em 2026", "%", True),
    "d_brancos_nulos": ("brancos e nulos 2026 menos 2022", "pp", True),
    "terceiros": ("terceira via em 2026", "%", True),
    "log_var_eleitorado": ("eleitorado de 2026 contra o de 2022", "razao", True),
    "log_atraso": ("conclusão da zona mais tarde que a UF", "min", False),
    "versoes_residuo": ("versões do arquivo além do esperado pelo tamanho", "", False),
}
# Terminar cedo ou em poucas versões não é sinal de nada: só o lado tardio conta.
UNILATERAIS = ("log_atraso", "versoes_residuo")
ELEITORAIS = [k for k, v in ATRIBUTOS.items() if v[2]]
OPERACIONAIS = [k for k, v in ATRIBUTOS.items() if not v[2]]


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as fh:
        for bloco in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _frac(a: float, b: float) -> float:
    return a / b if b else float("nan")


def _agregar_municipios(v22: dict, s22: dict):
    """Somas de 2022 por município (uf, código TSE), para a referência municipal."""
    votos: dict[tuple, Counter] = defaultdict(Counter)
    secoes: dict[tuple, dict] = defaultdict(lambda: defaultdict(int))
    for (k, turno), contagem in v22.items():
        votos[(k[0], k[1], turno)].update(contagem)
    for (k, turno), a in s22.items():
        alvo = secoes[(k[0], k[1], turno)]
        for campo in ("aptos", "comparecimento", "brancos", "nulos", "nominais"):
            alvo[campo] += a[campo]
    return votos, secoes


def _pacote_ref(votos_1t, votos_2t, base, eleitorado_comparavel) -> dict:
    return {
        "votos_1t": votos_1t,
        "votos_2t": votos_2t,
        "aptos": base["aptos"],
        "comparecimento": base["comparecimento"],
        "brancos": base["brancos"],
        "nulos": base["nulos"],
        "eleitorado_comparavel": eleitorado_comparavel,
    }


class Referencias:
    """Escolhe a base de 2022 de cada zona de 2026.

    Ordem: município com um par só em 2026 usa o município inteiro de 2022
    (mesmo território); zona com o mesmo número e eleitorado coerente com o do
    município usa a própria zona; zona redesenhada usa a ponte por local de
    votação, se cobrir ao menos 60% do eleitorado; o resto fica sem base.
    """

    COBERTURA_MINIMA = 0.6

    def __init__(self, zonas, v22, s22):
        self.zonas, self.v22, self.s22 = zonas, v22, s22
        self.votos_mun, self.secoes_mun = _agregar_municipios(v22, s22)
        self.te_mun: dict[tuple, int] = defaultdict(int)
        self.pares_mun: Counter = Counter()
        for k, z in zonas.items():
            self.te_mun[(k[0], k[1])] += z["eleitorado"]
            self.pares_mun[(k[0], k[1])] += 1
        self.ponte: dict = {}
        self.fim_mun: dict = {}
        for (k, turno), a in s22.items():
            mun = (k[0], k[1])
            if turno == 1 and a["fim"] is not None:
                atual = self.fim_mun.get(mun)
                self.fim_mun[mun] = a["fim"] if atual is None else max(atual, a["fim"])

    def _zona_coerente(self, k) -> bool:
        if (k, 1) not in self.s22 or (k, 2) not in self.s22:
            return False
        mun1 = self.secoes_mun[(k[0], k[1], 1)]
        razao_mun = self.te_mun[(k[0], k[1])] / mun1["aptos"]
        razao_zona = self.zonas[k]["eleitorado"] / self.s22[(k, 1)]["aptos"]
        return abs(math.log(razao_zona / razao_mun)) <= LIMIAR_REDESENHO

    def fim_2022(self, k):
        """Hora em que a zona (ou, sem ela, o município) fechou em 2022."""
        if (k, 1) in self.s22 and self.s22[(k, 1)]["fim"] is not None:
            return self.s22[(k, 1)]["fim"]
        return self.fim_mun.get((k[0], k[1]))

    def redesenhados(self) -> set:
        """Municípios com mais de um par e alguma zona sem base própria."""
        saida = set()
        for k in self.zonas:
            mun = (k[0], k[1])
            if (k[0], k[1], 1) not in self.secoes_mun or self.pares_mun[mun] == 1:
                continue
            if not self._zona_coerente(k):
                saida.add(mun)
        return saida

    def escolher(self, k) -> tuple[str, dict | None]:
        mun = (k[0], k[1])
        mk1, mk2 = (k[0], k[1], 1), (k[0], k[1], 2)
        if mk1 not in self.secoes_mun:
            return "ausente", None
        if self.pares_mun[mun] == 1:
            return "municipio", _pacote_ref(
                self.votos_mun[mk1],
                self.votos_mun[mk2],
                self.secoes_mun[mk1],
                self.zonas[k]["eleitorado"],
            )
        if self._zona_coerente(k):
            return "zona", _pacote_ref(
                self.v22[(k, 1)],
                self.v22[(k, 2)],
                self.s22[(k, 1)],
                self.zonas[k]["eleitorado"],
            )
        ponte = self.ponte.get(k)
        if ponte and ponte["cobertura"] >= self.COBERTURA_MINIMA:
            return "locais", _pacote_ref(
                ponte["votos_1t"], ponte["votos_2t"], ponte, ponte["eleitores_casados"]
            )
        return "imprecisa", None


def _localizar(k, z, locais, geo):
    """Média ponderada pelo eleitorado das coordenadas válidas dos locais."""
    centro = geo.get(str(z["ibge"]))
    caixa = centro["bbox"] if centro else None
    soma = slat = slon = 0.0
    for eleitores, lat, lon, *_ in locais.get(k, []):
        if lat is None or lon is None or eleitores <= 0:
            continue
        if caixa and not (
            caixa[0] - MARGEM_BBOX_GRAUS <= lon <= caixa[2] + MARGEM_BBOX_GRAUS
            and caixa[1] - MARGEM_BBOX_GRAUS <= lat <= caixa[3] + MARGEM_BBOX_GRAUS
        ):
            continue
        soma += eleitores
        slat += lat * eleitores
        slon += lon * eleitores
    if soma > 0:
        return slat / soma, slon / soma, "locais_de_votacao"
    if centro:
        return centro["lat"], centro["lon"], "centroide_municipio"
    return float("nan"), float("nan"), "ausente"


def montar_tabela(zonas, rotulos, refs: Referencias, s22, locais, geo) -> list[dict]:
    """Uma linha por zona com os atributos brutos (frações e minutos)."""
    linhas = []
    for k in sorted(zonas):
        z = zonas[k]
        validos = z["validos"]
        f26 = _frac(z["votos"].get(dados.FLAVIO, 0), validos)
        l26 = _frac(z["votos"].get(dados.LULA, 0), validos)
        terceiros = {n: _frac(v, validos) for n, v in z["votos"].items()}
        terceiros.pop(dados.FLAVIO, None)
        terceiros.pop(dados.LULA, None)
        lider = max(terceiros, key=lambda n: terceiros[n]) if terceiros else None
        ref_tipo, ref = refs.escolher(k)
        conclusao = dados.iso_utc(z["conclusao_em"] or z["totalizado_em"])
        if conclusao is not None:
            conclusao += timedelta(hours=z["fuso_horas"])
        linha = {
            "chave": k,
            "uf": z["uf"],
            "municipio": z["municipio"],
            "municipio_tse": z["municipio_tse"],
            "ibge": z["ibge"],
            "zona": z["zona"],
            "eleitorado": z["eleitorado"],
            "secoes": z["ts"],
            "secoes_apuradas": z["st"],
            "incompleta": z["st"] < z["ts"],
            "comparecimento": z["comparecimento"],
            "validos": validos,
            "flavio": f26,
            "lula": l26,
            "terceiros": 1.0 - f26 - l26,
            "terceiro_lider": (
                (rotulos.get(lider, str(lider)), terceiros[lider])
                if lider is not None
                else None
            ),
            "comparecimento_pct": _frac(z["comparecimento"], z["eleitorado_apurado"]),
            "brancos_nulos": _frac(z["brancos"] + z["nulos"], z["total_votos"]),
            "referencia_2022": ref_tipo,
            "cobertura_ponte": refs.ponte[k]["cobertura"] if k in refs.ponte else None,
            "n_versoes": z["n_versoes"],
            "n_copias_antigas": z["n_copias_antigas"],
            "n_idg_menor": z["n_idg_menor"],
            "fuso_horas": z["fuso_horas"],
            "conclusao_brasilia": (
                (conclusao - timedelta(hours=3)).strftime("%d/%m %H:%M")
                if conclusao
                else None
            ),
            "atraso_min": (
                (conclusao - dados.FECHAMENTO_2026).total_seconds() / 60.0
                if conclusao
                else float("nan")
            ),
            "snapshot_id": z["snapshot_id"],
        }
        if ref is not None:
            n1, n2 = sum(ref["votos_1t"].values()), sum(ref["votos_2t"].values())
            linha.update(
                {
                    "bolsonaro_22_1t": _frac(ref["votos_1t"][dados.BOLSONARO], n1),
                    "lula_22_1t": _frac(ref["votos_1t"][dados.LULA], n1),
                    "bolsonaro_22_2t": _frac(ref["votos_2t"][dados.BOLSONARO], n2),
                    "lula_22_2t": _frac(ref["votos_2t"][dados.LULA], n2),
                    "comparecimento_22": _frac(ref["comparecimento"], ref["aptos"]),
                    "brancos_nulos_22": _frac(
                        ref["brancos"] + ref["nulos"], ref["comparecimento"]
                    ),
                    "var_eleitorado": _frac(ref["eleitorado_comparavel"], ref["aptos"])
                    - 1.0,
                }
            )
        fim22 = refs.fim_2022(k)
        if fim22 is not None:
            linha["atraso_2022_min"] = (
                fim22 - dados.FECHAMENTO_2022
            ).total_seconds() / 60.0
        secoes_locais = locais.get(k, [])
        total = sum(s[0] for s in secoes_locais) or 1
        linha["pct_indigena"] = sum(s[0] for s in secoes_locais if s[3]) / total
        linha["pct_quilombola"] = sum(s[0] for s in secoes_locais if s[4]) / total
        linha["lat"], linha["lon"], linha["fonte_coordenada"] = _localizar(
            k, z, locais, geo
        )
        linhas.append(linha)
    return linhas


def _coluna(linhas, nome):
    return np.array([linha.get(nome, float("nan")) for linha in linhas], dtype=float)


def calcular_atributos(linhas: list[dict]) -> dict[str, np.ndarray]:
    """Atributos derivados, alinhados à ordem de ``linhas``."""
    f26, l26 = _coluna(linhas, "flavio"), _coluna(linhas, "lula")
    b1, lu1 = _coluna(linhas, "bolsonaro_22_1t"), _coluna(linhas, "lula_22_1t")
    b2, lu2 = _coluna(linhas, "bolsonaro_22_2t"), _coluna(linhas, "lula_22_2t")
    uf = np.array([linha["uf"] for linha in linhas])
    mun = np.array([f"{linha['uf']}-{linha['municipio_tse']}" for linha in linhas])
    lat, lon = _coluna(linhas, "lat"), _coluna(linhas, "lon")
    vizinhos = an.vizinhos_proximos(lat, lon, uf, mun, k=5)
    margem = (f26 - l26) - (b1 - lu1)
    hier = an.residuo_hierarquico(
        margem, uf, mun, _coluna(linhas, "validos"), vizinhos=vizinhos
    )
    atraso = _coluna(linhas, "atraso_min")
    log_secoes = np.log(np.maximum(_coluna(linhas, "secoes"), 1.0))
    log_versoes = np.log(np.maximum(_coluna(linhas, "n_versoes"), 1.0))
    inclinacao, intercepto = np.polyfit(log_secoes, log_versoes, 1)
    return {
        "d_flavio_1t": f26 - b1,
        "d_flavio_2t": f26 - b2,
        "d_lula_1t": l26 - lu1,
        "d_lula_2t": l26 - lu2,
        "margem_swing": margem,
        "residuo_hierarquico": hier["residuo"],
        "esperado_hierarquico": hier["esperado"],
        "swing_uf": hier["swing_uf"],
        "efeito_local": hier["efeito_local"],
        "fonte_efeito": hier["fonte"],
        "d_comparecimento": _coluna(linhas, "comparecimento_pct")
        - _coluna(linhas, "comparecimento_22"),
        "brancos_nulos": _coluna(linhas, "brancos_nulos"),
        "d_brancos_nulos": _coluna(linhas, "brancos_nulos")
        - _coluna(linhas, "brancos_nulos_22"),
        "terceiros": _coluna(linhas, "terceiros"),
        "log_var_eleitorado": np.log1p(_coluna(linhas, "var_eleitorado")),
        "log_atraso": np.log(np.maximum(atraso, 1.0)),
        "log_atraso_2022": np.log(np.maximum(_coluna(linhas, "atraso_2022_min"), 1.0)),
        "versoes_residuo": log_versoes - (intercepto + inclinacao * log_secoes),
        "_versoes_ajuste": np.array([inclinacao, intercepto]),
    }


def pontuar(linhas, atributos, semente=0, usar_sklearn=None):
    """z robustos por UF, ajuste de tamanho, quatro modelos e escore 0 a 100."""
    uf = np.array([linha["uf"] for linha in linhas])
    log_n = np.log(_coluna(linhas, "eleitorado"))
    zs, fatores, inclinacoes, centros = {}, {}, {}, {}
    for nome in ATRIBUTOS:
        z, centro, _escala = an.z_robusto_grupo(atributos[nome], uf)
        centros[nome] = centro
        if nome in ELEITORAIS:
            fator, b = an.fator_tamanho(z, log_n)
            z = z / fator
            fatores[nome] = fator
            inclinacoes[nome] = b
        if nome in UNILATERAIS:
            z = np.where(np.isfinite(z), np.maximum(z, 0.0), z)
        zs[nome] = z
    z22, _, _ = an.z_robusto_grupo(atributos["log_atraso_2022"], uf)
    matriz = np.column_stack([zs[n] for n in ATRIBUTOS])
    escores, meta = an.escores_modelos(
        matriz, semente=semente, usar_sklearn=usar_sklearn
    )
    final = an.escore_combinado(escores)
    sub = {}
    for rotulo, grupo in (("eleitoral", ELEITORAIS), ("operacional", OPERACIONAIS)):
        x, _ = an.preparar_matriz(np.column_stack([zs[n] for n in grupo]))
        sub[rotulo] = 100.0 * an.percentis(np.sqrt(np.mean(x**2, axis=1)))
    return {
        "z": zs,
        "z_atraso_2022": z22,
        "fatores": fatores,
        "inclinacoes": inclinacoes,
        "centros": centros,
        "escores": escores,
        "meta": meta,
        "escore": final,
        "sub": sub,
    }


def comparar_rankings(base, alternativo, n_topo, rotulo) -> dict:
    """Quantas zonas do topo se repetem e a correlação de postos entre leituras."""
    topo_a = set(np.argsort(-base, kind="stable")[:n_topo].tolist())
    topo_b = set(np.argsort(-alternativo, kind="stable")[:n_topo].tolist())
    pa, pb = an.percentis(base), an.percentis(alternativo)
    return {
        "rotulo": rotulo,
        "n_topo": n_topo,
        "comuns_topo": len(topo_a & topo_b),
        "spearman": round(float(np.corrcoef(pa, pb)[0, 1]), 4),
    }


def reconciliar(linhas, ufs) -> list[dict]:
    """Soma das zonas contra o arquivo da UF: seções, Flávio e Lula."""
    soma: dict[str, Counter] = defaultdict(Counter)
    for linha in linhas:
        s = soma[linha["uf"]]
        s["ts"] += linha["secoes"]
        s["st"] += linha["secoes_apuradas"]
        s["validos"] += linha["validos"]
        s["flavio"] += round(linha["flavio"] * linha["validos"])
        s["lula"] += round(linha["lula"] * linha["validos"])
    saida = []
    for uf in sorted(ufs):
        a, s = ufs[uf], soma[uf]
        saida.append(
            {
                "uf": uf,
                "arquivo_uf_gerado_em": a["gerado_em"],
                "secoes_uf": a["st"],
                "secoes_total_uf": a["ts"],
                "secoes_zonas": s["st"],
                "secoes_total_zonas": s["ts"],
                "faltam_nas_zonas": a["st"] - s["st"],
                "flavio_uf": a["flavio"],
                "flavio_zonas": s["flavio"],
                "lula_uf": a["lula"],
                "lula_zonas": s["lula"],
                "validos_uf": a["validos"],
                "validos_zonas": s["validos"],
            }
        )
    return saida


def _contexto(caminho: Path) -> dict:
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


def cruzar_zonas_json(caminho: Path, zonas: dict) -> dict:
    """Confere a leitura do banco com ``zonas.json`` da camada de dados do dossiê.

    As duas leituras são independentes (mesmo banco, código diferente). Compara
    Flávio, Lula, válidos, seções apuradas e totais, comparecimento e a versão.
    """
    if not caminho.exists():
        return {"presente": False}
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    colunas = conteudo["zonas"]["colunas"]
    outras = {}
    for valores in conteudo["zonas"]["linhas"]:
        r = dict(zip(colunas, valores, strict=True))
        outras[dados.chave(r["uf"], r["cd_tse"], r["zona"])] = r
    diferentes = []
    for k, z in zonas.items():
        r = outras.get(k)
        nossa = (
            z["votos"].get(dados.FLAVIO),
            z["votos"].get(dados.LULA),
            z["validos"],
            z["st"],
            z["ts"],
            z["comparecimento"],
            z["snapshot_id"],
        )
        deles = (
            None
            if r is None
            else (
                r["flavio"],
                r["lula"],
                r["validos"],
                r["secoes"],
                r["secoes_total"],
                r["comparecimento"],
                r["snapshot_id"],
            )
        )
        if nossa != deles:
            diferentes.append("-".join(k))
    return {
        "presente": True,
        "arquivo": str(caminho.relative_to(ROOT)),
        "sha256": sha256(caminho),
        "gerado_em": conteudo.get("meta", {}).get("gerado_em"),
        "campos": "flavio, lula, validos, secoes, secoes_total, comparecimento, "
        "snapshot_id",
        "zonas_aqui": len(zonas),
        "zonas_la": len(outras),
        "diferentes": len(diferentes),
        "exemplos_diferentes": diferentes[:10],
    }


def principal() -> None:
    parser = argparse.ArgumentParser(
        description="Anomalias por zona eleitoral, presidente, 1º turno 2026."
    )
    parser.add_argument("--semente", type=int, default=0)
    parser.add_argument("--sem-sklearn", action="store_true")
    parser.add_argument("--sem-hash", action="store_true", help="pula SHA-256")
    args = parser.parse_args()

    zonas, rotulos = dados.ler_zonas_2026(DB)
    ufs = dados.ler_ufs_2026(DB)
    v22 = dados.ler_votos_2022(ZIP_VOTOS_2022)
    s22 = dados.ler_secoes_2022(ZIP_SECOES_2022)
    locais = dados.ler_locais_2026(ZIP_LOCAIS_2026)
    geo = dados.ler_centroides(GEO_MUN)
    refs = Referencias(zonas, v22, s22)
    alvo = refs.redesenhados()
    locais22 = dados.ler_locais_2022(ZIP_SECOES_2022, alvo)
    locais26 = dados.ler_locais_2026_nomes(ZIP_LOCAIS_2026, alvo)
    refs.ponte = dados.referencia_por_locais(
        locais22, locais26, dados.cruzar_locais(locais22, locais26), v22
    )

    linhas = montar_tabela(zonas, rotulos, refs, s22, locais, geo)
    atributos = calcular_atributos(linhas)
    resultado = pontuar(
        linhas,
        atributos,
        semente=args.semente,
        usar_sklearn=False if args.sem_sklearn else None,
    )
    robustez = {}
    for chave, rotulo, kwargs in (
        (
            "numpy",
            "só z robusto e Mahalanobis (sem scikit-learn)",
            {"usar_sklearn": False},
        ),
        (
            "semente_1",
            "outra semente do Isolation Forest",
            {"semente": args.semente + 1},
        ),
    ):
        if args.sem_sklearn and chave == "numpy":
            continue
        alt = pontuar(linhas, atributos, **kwargs)["escore"]
        robustez[chave] = comparar_rankings(resultado["escore"], alt, N_TOPO, rotulo)
    fontes = {
        "banco": {
            "caminho": str(DB.relative_to(ROOT)),
            "regra": "arquivo nivel='zona', eleicao_cd=6257, cargo_cd=1, uf<>'zz'; "
            "versão vigente = maior gerado_em com totais e voto_candidato (a marca "
            "regressivo do coletor segue o idg e erra em 30 zonas)",
            "maior_snapshot_id": max(z["snapshot_id"] for z in zonas.values()),
        },
    }
    for rotulo, caminho in (
        ("votos_2022", ZIP_VOTOS_2022),
        ("secoes_2022", ZIP_SECOES_2022),
        ("locais_2026", ZIP_LOCAIS_2026),
    ):
        fontes[rotulo] = {
            "caminho": str(caminho.relative_to(ROOT)),
            "sha256": None if args.sem_hash else sha256(caminho),
        }
    fontes["malha"] = {"caminho": str(GEO_MUN.relative_to(ROOT)) + "/{UF}.geojson"}
    pacote = texto.empacotar(
        linhas=linhas,
        atributos=atributos,
        resultado=resultado,
        reconciliacao=reconciliar(linhas, ufs),
        contexto=_contexto(CONTEXTO),
        fontes=fontes,
        w1a=cruzar_zonas_json(ZONAS_W1A, zonas),
        definicoes=ATRIBUTOS,
        n_topo=N_TOPO,
        gerado_em=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        robustez=robustez,
    )
    SAIDA_JSON.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_JSON.write_text(texto.gravar_json(pacote), encoding="utf-8")
    SAIDA_MD.write_text(texto.markdown(pacote), encoding="utf-8")
    print(f"{len(linhas)} zonas; gravado {SAIDA_JSON.relative_to(ROOT)}")
    print(f"gravado {SAIDA_MD.relative_to(ROOT)}")
    for item in pacote["topo"][:10]:
        print(
            f"{item['posicao']:>2} {item['escore']:5.1f} {item['municipio']} "
            f"({item['uf']}) z{item['zona']}: {'; '.join(item['motivos'])}"
        )


if __name__ == "__main__":
    principal()
