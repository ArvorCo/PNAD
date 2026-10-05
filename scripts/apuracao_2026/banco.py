"""Leitura somente leitura do banco de auditoria da apuração (`apuracao.sqlite`).

O banco é aberto com `mode=ro` e `PRAGMA query_only`, sem tocar no coletor que
continua escrevendo. Esquema em `apuracao/src/db/schema.sql`.

Regra de versão vigente: a última gerada pelo TSE (maior `gerado_em`, desempate
pelo `id` de captura). A coluna `regressivo` do coletor marca toda versão cujo
contador `idg` caiu, mas esse contador não é monotônico dentro do arquivo: a
maioria das versões marcadas é mais nova que todas as anteriores. Por isso a
versão vigente sai do relógio de geração, e as versões marcadas que não têm
linhas normalizadas são lidas do corpo original (`blob`).
"""

from __future__ import annotations

import gzip
import json
import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from .dados import resultado_do_documento, versoes_genuinas

CAMPOS_TOTAIS = (
    "st",
    "ts",
    "te",
    "comparecimento",
    "abstencao",
    "vv",
    "vb",
    "vn",
    "vnt",
    "tvn",
)


def _lotes(valores: Sequence[Any], tamanho: int = 900) -> Iterable[Sequence[Any]]:
    for i in range(0, len(valores), tamanho):
        yield valores[i : i + tamanho]


class Banco:
    """Consultas usadas pelos dados do dossiê."""

    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        self.con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA query_only = 1")
        self._docs: dict[str, dict[str, Any]] = {}

    def fechar(self) -> None:
        self.con.close()

    def linhas(self, sql: str, parametros: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self.con.execute(sql, parametros).fetchall()]

    # ------------------------------------------------------------ configuração

    def candidatos(self, eleicao: int, cargo: int, uf: str | None = None) -> list[dict]:
        sql = (
            "SELECT c.sqcand, c.numero, c.nome_urna, c.nome, c.uf, c.partido_n, "
            "c.federacao_n, p.sigla AS partido, f.sigla AS federacao "
            "FROM candidato c LEFT JOIN partido p ON p.n = c.partido_n "
            "LEFT JOIN federacao f ON f.n = c.federacao_n "
            "WHERE c.eleicao_cd = ? AND c.cargo_cd = ?"
        )
        parametros: list[Any] = [eleicao, cargo]
        if uf is not None:
            sql += " AND c.uf = ?"
            parametros.append(uf)
        return self.linhas(sql, parametros)

    def municipios(self) -> list[dict[str, Any]]:
        return self.linhas("SELECT cd, uf, ibge, nome, capital FROM municipio")

    def arquivos(
        self, where: str, parametros: Sequence[Any] = ()
    ) -> list[dict[str, Any]]:
        return self.linhas(
            "SELECT id, chave, tipo, eleicao_cd, cargo_cd, nivel, uf, municipio_cd, zona_cd "
            f"FROM arquivo WHERE {where}",
            parametros,
        )

    # ------------------------------------------------------------ versões

    def snapshots(self, arquivo_ids: Sequence[int]) -> dict[int, list[dict[str, Any]]]:
        """Todas as versões capturadas dos arquivos, com os totais normalizados."""
        saida: dict[int, list[dict[str, Any]]] = defaultdict(list)
        campos = ", ".join(f"t.{c}" for c in CAMPOS_TOTAIS)
        for lote in _lotes(list(arquivo_ids)):
            marcas = ",".join("?" * len(lote))
            sql = (
                "SELECT s.id, s.arquivo_id, s.capturado_em, s.gerado_em, s.totalizado_em, "
                "s.dt, s.ht, s.idg, s.regressivo, s.sha256, s.andamento, "
                f"t.snapshot_id AS tem_totais, {campos} "
                "FROM snapshot s LEFT JOIN totais t ON t.snapshot_id = s.id "
                f"WHERE s.arquivo_id IN ({marcas}) ORDER BY s.arquivo_id, s.id"
            )
            for linha in self.linhas(sql, lote):
                saida[linha["arquivo_id"]].append(linha)
        return saida

    def documento(self, sha256: str) -> dict[str, Any]:
        """Corpo original (JSON do TSE) guardado em `blob`, com cache."""
        if sha256 not in self._docs:
            linha = self.con.execute(
                "SELECT gz FROM blob WHERE sha256 = ?", (sha256,)
            ).fetchone()
            if linha is None:
                raise KeyError(f"blob ausente: {sha256}")
            self._docs[sha256] = json.loads(gzip.decompress(linha[0]))
        return self._docs[sha256]

    def esquecer_documentos(self) -> None:
        self._docs.clear()

    def votos(self, snapshots: Sequence[dict[str, Any]]) -> dict[int, dict[str, int]]:
        """Votos por candidatura (sqcand) de cada versão.

        Usa `voto_candidato`; versão sem linhas normalizadas é lida do corpo.
        """
        ids = [s["id"] for s in snapshots]
        saida: dict[int, dict[str, int]] = {}
        for lote in _lotes(ids):
            marcas = ",".join("?" * len(lote))
            sql = (
                "SELECT snapshot_id, sqcand, vap FROM voto_candidato "
                f"WHERE snapshot_id IN ({marcas})"
            )
            for sid, sq, vap in self.con.execute(sql, lote).fetchall():
                saida.setdefault(sid, {})[str(sq)] = vap or 0
        for snap in snapshots:
            if snap["id"] not in saida:
                saida[snap["id"]] = resultado_do_documento(
                    self.documento(snap["sha256"])
                )["votos"]
        return saida

    def completar_totais(self, snap: dict[str, Any]) -> dict[str, Any]:
        """Preenche os totais de uma versão sem linha em `totais`, a partir do corpo."""
        if snap.get("tem_totais") is not None:
            return snap
        lido = resultado_do_documento(self.documento(snap["sha256"]))
        for campo in CAMPOS_TOTAIS:
            snap[campo] = lido[campo]
        snap["tem_totais"] = "blob"
        return snap

    def partidos(self, snapshot_id: int) -> list[dict[str, Any]]:
        return self.linhas(
            "SELECT vp.agremiacao_n, vp.partido_n, p.sigla, vp.tvtn, vp.tvtl "
            "FROM voto_partido vp LEFT JOIN partido p ON p.n = vp.partido_n "
            "WHERE vp.snapshot_id = ?",
            (snapshot_id,),
        )

    def candidaturas(self, snapshot_id: int) -> list[dict[str, Any]]:
        return self.linhas(
            "SELECT vc.sqcand, vc.vap, vc.pvapn, vc.st, vc.dvt, c.nome_urna, c.uf, "
            "c.numero, p.sigla AS partido, f.sigla AS federacao "
            "FROM voto_candidato vc JOIN candidato c ON c.sqcand = vc.sqcand "
            "LEFT JOIN partido p ON p.n = c.partido_n "
            "LEFT JOIN federacao f ON f.n = c.federacao_n "
            "WHERE vc.snapshot_id = ?",
            (snapshot_id,),
        )

    # ------------------------------------------------------------ log e eventos

    def leituras(self, arquivo_id: int, de: str, ate: str) -> dict[str, Any]:
        """Requisições ao arquivo entre dois instantes de captura, por classe."""
        linhas = self.linhas(
            "SELECT classe, COUNT(*) AS n, MAX(iniciado_em) AS ultima FROM fetch "
            "WHERE arquivo_id = ? AND iniciado_em > ? AND iniciado_em < ? GROUP BY classe",
            (arquivo_id, de, ate),
        )
        ultima = max((r["ultima"] for r in linhas), default=None)
        return {
            "por_classe": {r["classe"]: r["n"] for r in linhas},
            "total": sum(r["n"] for r in linhas),
            "ultima": ultima,
        }

    def versoes_de(self, chave: str) -> list[dict[str, Any]]:
        """Versões genuínas (pela hora de geração) do arquivo com a chave dada."""
        arq = self.arquivos("chave = ?", (chave,))[0]
        return versoes_genuinas(self.snapshots([arq["id"]])[arq["id"]])

    def eventos(self, tipo: str) -> list[dict[str, Any]]:
        return self.linhas(
            "SELECT id, em, tipo, nivel, uf FROM evento WHERE tipo = ?", (tipo,)
        )

    def contagens_gerais(self) -> dict[str, int]:
        def um(sql: str) -> int:
            return int(self.con.execute(sql).fetchone()[0])

        return {
            "snapshots": um("SELECT COUNT(*) FROM snapshot"),
            "fetches": um("SELECT COUNT(*) FROM fetch"),
            "arquivos": um("SELECT COUNT(*) FROM arquivo"),
        }
