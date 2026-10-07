"""Renda domiciliar da PNADC anual 2025 (visita 1) por UF, escolaridade e situação.

Uma passagem pelo microdado (1,5 GB), pessoas de 16 anos ou mais, peso ``V1032``,
rendimento domiciliar efetivo ``VD5001`` já levado a preços de abril de 2026 pelo
pipeline (coluna ``_202604``) e corrigido pelo IPCA até o mês mais recente do
``ipca.csv``. Para cada célula guarda o número de observações, o peso, a parcela nas
três faixas das pesquisas (até 2 SM, de 2 a 5, mais de 5) e um histograma de R$ 10
para a mediana. A escolaridade vem de ``VD3006`` (grupamento de anos de estudo), porque
o arquivo não traz ``VD3004``; a correspondência com os quatro grupos do TSE está em
``ESC_VD3006`` e em ``analysis/politize/DECISOES.md``.

A renda de um local é a mistura das células pelos pesos de escolaridade do eleitorado
(TSE) dentro da situação do setor censitário do ponto. A mediana da mistura sai da
soma das funções de distribuição, não da média das medianas.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from . import fontes

MES_BASE = "2026-04"
COL_UF = "UF__unidade_da_federacao"
COL_SIT = "V1022__tipo_de_situacao_da_regiao"
COL_IDADE = "V2009__idade_na_data_de_referencia"
COL_PESO = "V1032__peso_com_calibracao"
COL_ESC = (
    "VD3006__grupamento_de_anos_de_estudo_pessoas_de_5_anos_ou_mais_de_idade_para"
    "_fundamental_de_9_anos"
)
COL_RENDA = "VD5001__rend_efetivo_domiciliar_202604"
IDADE_MIN = 16
MIN_OBS = 30
ESCOLARIDADES = ("fund_inc", "fund_med", "med_sup_inc", "superior")
SITUACOES = ("urbana", "rural", "total")
FAIXAS = ("ate2", "de2a5", "mais5")
ESC_VD3006 = {
    "1": "fund_inc",  # sem instrução e menos de 1 ano
    "2": "fund_inc",  # 1 a 4 anos
    "3": "fund_inc",  # 5 a 8 anos
    "4": "fund_med",  # 9 a 11 anos
    "5": "med_sup_inc",  # 12 a 15 anos
    "6": "superior",  # 16 anos ou mais
}
SIT_V1022 = {"1": "urbana", "2": "rural"}
LARGURA = 10.0
TETO = 60_000.0
CAIXAS = int(TETO / LARGURA)


def fator_ipca(caminho: Path, de: str = MES_BASE) -> tuple[float, str]:
    """IPCA do mês mais recente sobre o de ``de`` e o mês de destino."""
    indice: dict[str, float] = {}
    with caminho.open(encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            indice[linha["date"]] = float(linha["index"])
    alvo = max(indice)
    return indice[alvo] / indice[de], alvo


def salario_minimo(caminho: Path, ano: int = 2026) -> float:
    valores = set()
    with caminho.open(encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            if linha["date"].startswith(f"{ano}-"):
                valores.add(float(linha["value"]))
    if len(valores) != 1:
        raise ValueError(f"salário mínimo de {ano} não é único: {sorted(valores)}")
    return valores.pop()


def faixa(valor: float, sm: float) -> int:
    """0 até 2 SM (inclusive), 1 de 2 a 5 SM (inclusive), 2 acima de 5 SM."""
    if valor <= 2 * sm:
        return 0
    if valor <= 5 * sm:
        return 1
    return 2


@dataclass
class Celula:
    n: int = 0
    peso: float = 0.0
    faixas: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    hist: np.ndarray = field(default_factory=lambda: np.zeros(CAIXAS + 1))

    def somar(self, valor: float, peso: float, sm: float) -> None:
        self.n += 1
        self.peso += peso
        self.faixas[faixa(valor, sm)] += peso
        self.hist[min(int(valor // LARGURA), CAIXAS)] += peso

    def parcelas(self) -> list[float]:
        return [100.0 * x / self.peso for x in self.faixas] if self.peso else [0.0] * 3

    def cdf(self) -> np.ndarray:
        return np.cumsum(self.hist) / self.peso


def mediana_cdf(cdf: np.ndarray) -> float:
    """Mediana de uma distribuição em caixas de R$ 10, com interpolação linear."""
    i = int(np.searchsorted(cdf, 0.5, side="left"))
    i = min(i, len(cdf) - 1)
    antes = cdf[i - 1] if i > 0 else 0.0
    dentro = cdf[i] - antes
    frac = 0.5 if dentro <= 0 else (0.5 - antes) / dentro
    return LARGURA * (i + min(max(frac, 0.0), 1.0))


def varrer(caminho: Path, fator: float, sm: float) -> tuple[dict, dict[str, int]]:
    """Uma passagem pelo microdado; células (uf, escolaridade, situação), com BR."""
    celulas: dict[tuple[str, str, str], Celula] = {}
    contagem = {"linhas": 0, "usadas": 0, "sem_renda": 0, "sem_escolaridade": 0}
    with caminho.open(encoding="utf-8", newline="") as f:
        leitor = csv.reader(f)
        cab = next(leitor)
        iu, isit, iid = cab.index(COL_UF), cab.index(COL_SIT), cab.index(COL_IDADE)
        ip, ie, ir = cab.index(COL_PESO), cab.index(COL_ESC), cab.index(COL_RENDA)
        for linha in leitor:
            contagem["linhas"] += 1
            try:
                idade = int(linha[iid])
                peso = float(linha[ip])
            except ValueError:
                continue
            if idade < IDADE_MIN or peso <= 0:
                continue
            esc = ESC_VD3006.get(linha[ie].strip())
            if esc is None:
                contagem["sem_escolaridade"] += 1
                continue
            bruto = linha[ir].strip()
            if not bruto:
                contagem["sem_renda"] += 1
                continue
            valor = float(bruto) * fator
            uf = fontes.UF_POR_CODIGO[linha[iu].strip()]
            sit = SIT_V1022[linha[isit].strip()]
            contagem["usadas"] += 1
            for chave in (
                (uf, esc, sit),
                (uf, esc, "total"),
                ("BR", esc, sit),
                ("BR", esc, "total"),
            ):
                cel = celulas.get(chave)
                if cel is None:
                    cel = celulas[chave] = Celula()
                cel.somar(valor, peso, sm)
    return celulas, contagem


class TabelaRenda:
    """Células da PNAD prontas para misturar, com a regra de substituição declarada."""

    def __init__(self, celulas: dict[tuple[str, str, str], Celula], meta: dict):
        self.celulas = celulas
        self.meta = meta
        self._cdf = {k: c.cdf() for k, c in celulas.items()}
        self._parc = {k: np.array(c.parcelas()) for k, c in celulas.items()}

    def efetiva(self, uf: str, esc: str, sit: str) -> tuple[str, str, str]:
        """Célula usada: a própria; se tiver menos de 30 observações, a da UF sem
        situação; se ainda faltar, a nacional da mesma situação."""
        for chave in ((uf, esc, sit), (uf, esc, "total"), ("BR", esc, sit)):
            cel = self.celulas.get(chave)
            if cel is not None and cel.n >= MIN_OBS:
                return chave
        return ("BR", esc, "total")

    def misturar(
        self,
        uf: str,
        sit: str | None,
        pesos_esc: dict[str, float],
        com_mediana: bool = True,
    ) -> dict[str, float | None] | None:
        """Parcelas por faixa (0 a 100) e mediana da mistura pelos pesos de escolaridade."""
        situacao = sit if sit in ("urbana", "rural") else "total"
        total = sum(pesos_esc.get(e, 0.0) for e in ESCOLARIDADES)
        if total <= 0:
            return None
        parc = np.zeros(3)
        cdf = np.zeros(CAIXAS + 1) if com_mediana else None
        for esc in ESCOLARIDADES:
            w = pesos_esc.get(esc, 0.0) / total
            if w <= 0:
                continue
            chave = self.efetiva(uf, esc, situacao)
            parc += w * self._parc[chave]
            if cdf is not None:
                cdf += w * self._cdf[chave]
        return {
            "ate2": float(parc[0]),
            "de2a5": float(parc[1]),
            "mais5": float(parc[2]),
            "mediana_brl": None if cdf is None else mediana_cdf(cdf),
        }

    def misturar_celulas(self, pesos: dict[tuple[str, str, str], float]):
        """Mistura com pesos por (UF, situação, escolaridade), para totais agregados."""
        total = sum(pesos.values())
        if total <= 0:
            return None
        parc = np.zeros(3)
        cdf = np.zeros(CAIXAS + 1)
        for (uf, sit, esc), w in pesos.items():
            if w <= 0:
                continue
            chave = self.efetiva(uf, esc, sit)
            parc += (w / total) * self._parc[chave]
            cdf += (w / total) * self._cdf[chave]
        return {
            "ate2": float(parc[0]),
            "de2a5": float(parc[1]),
            "mais5": float(parc[2]),
            "mediana_brl": mediana_cdf(cdf),
        }

    def json(self) -> dict[str, Any]:
        linhas = []
        for uf in [*sorted(u for u in fontes.UFS if u != "ZZ"), "BR"]:
            for esc in ESCOLARIDADES:
                for sit in SITUACOES:
                    cel = self.celulas.get((uf, esc, sit))
                    if cel is None:
                        continue
                    p = cel.parcelas()
                    efetiva = self.efetiva(uf, esc, sit)
                    linhas.append(
                        {
                            "uf": uf,
                            "escolaridade": esc,
                            "situacao": sit,
                            "ate2": round(p[0], 2),
                            "de2a5": round(p[1], 2),
                            "mais5": round(p[2], 2),
                            "mediana_brl": round(
                                mediana_cdf(self._cdf[(uf, esc, sit)])
                            ),
                            "n_amostra": cel.n,
                            "peso": round(cel.peso),
                            "usa": (
                                None if efetiva == (uf, esc, sit) else "-".join(efetiva)
                            ),
                        }
                    )
        return {**self.meta, "linhas": linhas}


def _salvar(celulas: dict, meta: dict) -> None:
    chaves = sorted(celulas)
    np.savez_compressed(
        fontes.CACHE / "pnad_celulas.npz",
        chaves=np.array(["|".join(k) for k in chaves]),
        n=np.array([celulas[k].n for k in chaves]),
        peso=np.array([celulas[k].peso for k in chaves]),
        faixas=np.array([celulas[k].faixas for k in chaves]),
        hist=np.array([celulas[k].hist for k in chaves]),
    )
    fontes.gravar_cache("pnad_meta.json", assinatura_fontes(), meta)


def assinatura_fontes() -> list:
    return [
        *fontes.assinatura(fontes.CSV_PNAD),
        *fontes.assinatura(fontes.CSV_IPCA),
        *fontes.assinatura(fontes.CSV_SALARIO),
        "v1",
    ]


def _carregar() -> tuple[dict, dict] | None:
    meta = fontes.ler_cache("pnad_meta.json", assinatura_fontes())
    arq = fontes.CACHE / "pnad_celulas.npz"
    if meta is None or not arq.exists():
        return None
    z = np.load(arq)
    celulas = {}
    for i, k in enumerate(z["chaves"]):
        celulas[tuple(str(k).split("|"))] = Celula(
            n=int(z["n"][i]),
            peso=float(z["peso"][i]),
            faixas=[float(x) for x in z["faixas"][i]],
            hist=z["hist"][i].copy(),
        )
    return celulas, meta


def tabela(refazer: bool = False) -> TabelaRenda:
    """Tabela de renda, do cache quando as fontes não mudaram."""
    if not refazer:
        carregado = _carregar()
        if carregado is not None:
            return TabelaRenda(*carregado)
    fator, mes = fator_ipca(fontes.CSV_IPCA)
    sm = salario_minimo(fontes.CSV_SALARIO)
    celulas, contagem = varrer(fontes.CSV_PNAD, fator, sm)
    meta = {
        "fonte": fontes.rel(fontes.CSV_PNAD),
        "universo": "pessoas de 16 anos ou mais, peso V1032",
        "renda": "VD5001, rendimento domiciliar efetivo",
        "escolaridade": "VD3006 (grupamento de anos de estudo), ver ESC_VD3006",
        "situacao": "V1022 (1 urbana, 2 rural); total = UF sem situação",
        "mes_base": MES_BASE,
        "mes_precos": mes,
        "fator_ipca": fator,
        "salario_minimo_2026": sm,
        "faixas": {
            "ate2": f"até 2 SM (até R$ {2 * sm:,.0f})".replace(",", "."),
            "de2a5": f"de 2 a 5 SM (R$ {2 * sm:,.0f} a {5 * sm:,.0f})".replace(
                ",", "."
            ),
            "mais5": f"mais de 5 SM (acima de R$ {5 * sm:,.0f})".replace(",", "."),
        },
        "unidade": "ate2, de2a5 e mais5 em % do peso da célula; mediana em reais",
        "min_observacoes": MIN_OBS,
        "regra_substituicao": (
            "célula com menos de 30 observações usa a da UF sem situação; "
            "se ainda faltar, a nacional da mesma situação (campo usa)"
        ),
        "contagem": contagem,
    }
    _salvar(celulas, meta)
    return TabelaRenda(celulas, meta)
