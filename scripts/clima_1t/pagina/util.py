"""Dados e formatação do relatório de clima. Nenhum número é digitado à mão.

Formatação em pt-BR reaproveitada do laudo irmão (mudanças de local de votação).
"""

from __future__ import annotations

import json
from pathlib import Path

from clima_1t import territorio, texto
from mudancas_secoes_2t.pagina.util import (
    CORES,
    data_br,
    dec,
    esc,
    ic,
    inteiro,
    limpa,
    pct,
    pp,
    sinal,
    titulo_pt,
)

ROOT = Path(__file__).resolve().parents[3]
CLIMA_JSON = ROOT / "analysis" / "clima_1t_2026" / "clima.json"
LITERATURA_JSON = ROOT / "analysis" / "clima_1t_2026" / "literatura.json"
CELULAS_JSON = ROOT / "analysis" / "clima_1t_2026" / "celulas_archive.json"
PREVISAO_JSON = ROOT / "docs" / "assets" / "fiscais_mapa" / "clima" / "previsao.json"
SLUG = "clima_abstencao_1t_2026"
SITE = "https://brasil.arvor.co"

# Gomez, Hansford e Krause (2007): pouco menos de um ponto por polegada (25,4 mm).
GOMEZ_PP_POR_POLEGADA = 0.9
MM_POR_POLEGADA = 25.4

__all__ = [
    "CORES",
    "GOMEZ_PP_POR_POLEGADA",
    "MM_POR_POLEGADA",
    "ROOT",
    "SITE",
    "SLUG",
    "Dados",
    "data_br",
    "dec",
    "esc",
    "hora_br",
    "ic",
    "inteiro",
    "limpa",
    "pct",
    "pp",
    "razao",
    "sinal",
    "titulo_pt",
]


def hora_br(iso: str) -> str:
    """Instante ISO em UTC vira 'DD/MM/AAAA, HHhMM UTC' sem converter fuso."""
    return f"{data_br(iso)}, {iso[11:13]}h{iso[14:16]} UTC"


def razao(x: float) -> str:
    return dec(x, 2) + "×"


class Dados:
    """JSON do motor, literatura, células e previsão lidos uma vez."""

    def __init__(self, caminho: Path | None = None):
        self.d = json.loads((caminho or CLIMA_JSON).read_text(encoding="utf-8"))
        self.lit = json.loads(LITERATURA_JSON.read_text(encoding="utf-8"))["itens"]
        self.celulas = json.loads(CELULAS_JSON.read_text(encoding="utf-8"))
        self.previsao = json.loads(PREVISAO_JSON.read_text(encoding="utf-8"))
        # A análise de 04/10 fica arquivada. Todas as saídas da página usam uma
        # única previsão, inclusive tabelas, texto alternativo, metadados e hashes.
        p = self.previsao
        self.d["previsao_25_10"] = {
            **{
                k: p[k]
                for k in ("gerado_em", "alvo", "regra_risco", "rotulo", "coleta")
            },
            **p["resumo"],
            "arquivo": str(PREVISAO_JSON.relative_to(ROOT)),
        }
        for f in self.d["fontes"]:
            if f["chave"] == "previsao":
                f.update(territorio.fonte(PREVISAO_JSON))
        self.d["achados"] = texto.achados(self.d)
        self.territorio = territorio.carregar(p)
        self.territorio["fontes"].append(territorio.fonte(PREVISAO_JSON))

    # ---- atalhos ----
    def faixas(self, exposicao: str, desfecho: str) -> list[dict]:
        return self.d["bateria_x_chuva"]["por_exposicao"][exposicao]["faixas"][desfecho]

    def reg_bateria(self, desfecho: str, exposicao: str) -> dict:
        """Termo da regressão logística de um desfecho para uma exposição."""
        for r in self.d["bateria_x_chuva"]["regressoes"]["desfechos"][desfecho]:
            if r["exposicao"] == [exposicao]:
                return r["termos"][exposicao]
        raise KeyError((desfecho, exposicao))

    def pais(self, exposicao: str) -> list[dict]:
        return self.d["abstencao_x_chuva"]["por_exposicao"][exposicao]["pais"]

    def previsao_pais(self) -> dict:
        return self.d["previsao_25_10"]["pais"]

    def total_eleitores_previsao(self) -> int:
        e = self.previsao_pais()["eleitores"]
        return sum(e.values())

    def pct_eleitores(self, nivel: str) -> float:
        return (
            100
            * self.previsao_pais()["eleitores"][nivel]
            / (self.total_eleitores_previsao())
        )

    def urnas_sem_clima(self) -> int:
        c = self.d["cobertura"]
        return c["urnas_brasil"] - c["urnas_amostra"]
