"""Dados do laudo reunidos uma vez: JSON do motor, notas dos TREs e painel do TSE."""

from __future__ import annotations

import json
from collections import defaultdict

from . import motivos
from .util import JSON_PAINEL, JSON_TRE, ROOT, carregar

NOME_UF = {"ZZ": "Exterior"}


class Contexto:
    def __init__(self, caminho=None):
        self.d = carregar(caminho) if caminho else carregar()
        self.tre = json.loads(JSON_TRE.read_text(encoding="utf-8"))
        painel = json.loads(JSON_PAINEL.read_text(encoding="utf-8"))
        self.painel = painel["linhas"]
        self.reais = [x for x in self.d["locais"] if x["mudanca_real"]]
        self.motivos = motivos.resumo(self.d["locais"])
        self.ufs = sorted(x["uf"] for x in self.d["por_uf"] if x["uf"] != "ZZ")
        self.mr = self.d["resumo"]["mudanca_real"]
        self.baixar = {
            nome: (ROOT / "docs" / "assets" / "mudancas_secoes" / nome)
            for nome in ("dados.json", "secoes.csv")
        }

    # ---- derivados reutilizados em mais de um capítulo ----
    def secoes_real(self) -> int:
        return self.mr["secoes"]

    def novas_secoes(self) -> int:
        return self.mr["secoes"] - self.mr["por_categoria"]["A"]["secoes"]

    def por_uf_categoria(self) -> dict[str, dict[str, int]]:
        acc: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for x in self.reais:
            acc[x["uf"]][x["categoria"]] += len(x["secoes"])
        return acc

    def painel_por_municipio(self, uf: str) -> dict[str, int]:
        acc: dict[str, int] = defaultdict(int)
        for r in self.painel:
            if r["uf"] == uf:
                acc[r["municipio"]] += 1
        return dict(acc)

    def uf_info(self, uf: str) -> dict:
        return next(x for x in self.d["por_uf"] if x["uf"] == uf)

    def local(self, uf: str, municipio: str) -> list[dict]:
        return [
            x for x in self.d["locais"] if x["uf"] == uf and x["municipio"] == municipio
        ]

    def atrasadas(self) -> tuple[int, list[tuple[tuple[str, str], int]]]:
        acc: dict[tuple[str, str], int] = defaultdict(int)
        for x in self.reais:
            acc[(x["uf"], x["municipio"])] += x["abertura_min_atrasada"]
        ordem = sorted(acc.items(), key=lambda kv: -kv[1])
        return sum(acc.values()), ordem
