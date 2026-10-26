"""Caminhos, constantes e leitura somente leitura do banco do 2º turno.

O banco `apuracao/data/apuracao-2t.sqlite` é aberto com `mode=ro` e
`PRAGMA query_only`: o coletor continua escrevendo nele. Versão vigente de cada
arquivo = a mais nova pelo relógio de geração do TSE (`gerado_em`), desempate
pelo `id` de captura, como no dossiê do 1º turno.

Relógio da apuração: minutos após 17:00 de Brasília de 25/10/2026, pelo
`gerado_em` (Brasília real). O `totalizado_em` de AC (+120 min) e de AM, RO, RR,
MT e MS (+60 min) vem em hora local rotulada como Brasília (CONTRATO.md); por
isso nenhum relógio deste pacote usa `totalizado_em` sem correção.
"""

from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Iterable, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from apuracao_2026.dados import regiao, utc, versoes_genuinas

ROOT = Path(__file__).resolve().parents[2]
APURACAO = ROOT / "apuracao"
BANCO_2T = APURACAO / "data/apuracao-2t.sqlite"
REFERENCIA_1T = APURACAO / "data/referencia_1t.json"
REFERENCIA_1T_VOTOS = APURACAO / "data/referencia_1t_votos.json"
SERIE_PROJECAO = APURACAO / "data/projecao_2t_serie.json"
DADOS_1T = ROOT / "analysis/apuracao_2026/dados"
SAIDA = ROOT / "analysis/apuracao_2t_2026/dados"
CACHE = ROOT / "data/outputs/apuracao_2t_2026"
TSE_RESULTADOS = ROOT / "data/raw/tse_resultados"
API_LOCAL = "http://127.0.0.1:4180"

ELE_PRES = 6258
ELE_GOV = 6260
SQ_FLAVIO = "280002551544"
SQ_LULA = "280002542548"
T0 = datetime(2026, 10, 25, 20, 0, tzinfo=timezone.utc)  # 17:00 de Brasília
BRT = timezone(timedelta(hours=-3))
FUSO_TOTALIZACAO_MIN = {"ac": 120, "am": 60, "ro": 60, "rr": 60, "mt": 60, "ms": 60}

ROTULO = "atipicidade pede explicação, não prova irregularidade"
ROTULO_PAUSA = "pausa é intervalo sem versão nova publicada, não acusação"
ROTULO_PROJECAO = (
    "projeção estatística a partir do que já foi totalizado; "
    "não é resultado nem previsão de vitória"
)
ROTULO_PARALELA = "soma dos BUs recebidos, não projeção"

SIGLA_REGIAO = {
    "Norte": "N",
    "Nordeste": "NE",
    "Centro-Oeste": "CO",
    "Sudeste": "SE",
    "Sul": "S",
    "Exterior": "ZZ",
}
NOME_UF = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AM": "Amazonas",
    "AP": "Amapá",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso",
    "PA": "Pará",
    "PB": "Paraíba",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "PR": "Paraná",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RO": "Rondônia",
    "RR": "Roraima",
    "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina",
    "SE": "Sergipe",
    "SP": "São Paulo",
    "TO": "Tocantins",
    "ZZ": "Exterior",
}


# ---------------------------------------------------------------- números


def p2(parte: float | None, total: float | None) -> float | None:
    """Percentual com 2 casas; total nulo ou zero devolve None."""
    if parte is None or not total:
        return None
    return round(100.0 * parte / total, 2)


def d2(a: float | None, b: float | None) -> float | None:
    """Diferença a menos b com 2 casas."""
    if a is None or b is None:
        return None
    return round(a - b, 2)


def r2(x: float | None) -> float | None:
    return None if x is None else round(x, 2)


def mediana(valores: Sequence[float]) -> float | None:
    v = sorted(valores)
    if not v:
        return None
    m = len(v) // 2
    return v[m] if len(v) % 2 else (v[m - 1] + v[m]) / 2


def quantil(valores: Sequence[float], q: float) -> float | None:
    """Quantil com interpolação linear (q de 0 a 1)."""
    v = sorted(valores)
    if not v:
        return None
    pos = q * (len(v) - 1)
    i = math.floor(pos)
    j = min(i + 1, len(v) - 1)
    return v[i] + (v[j] - v[i]) * (pos - i)


def resumo_distribuicao(
    valores: Sequence[float], pesos: Sequence[float] | None = None
) -> dict[str, Any]:
    """Média, desvio, quantis; com pesos, também a média ponderada."""
    n = len(valores)
    if n == 0:
        return {"n": 0}
    media = sum(valores) / n
    dp = math.sqrt(sum((x - media) ** 2 for x in valores) / (n - 1)) if n > 1 else 0.0
    saida: dict[str, Any] = {
        "n": n,
        "media": r2(media),
        "desvio": r2(dp),
        "min": r2(min(valores)),
        "p05": r2(quantil(valores, 0.05)),
        "p25": r2(quantil(valores, 0.25)),
        "mediana": r2(quantil(valores, 0.5)),
        "p75": r2(quantil(valores, 0.75)),
        "p95": r2(quantil(valores, 0.95)),
        "max": r2(max(valores)),
    }
    if pesos is not None:
        total = sum(pesos)
        if total:
            mp = sum(x * w for x, w in zip(valores, pesos, strict=True)) / total
            saida["media_ponderada"] = r2(mp)
    return saida


def spearman(a: Sequence[float], b: Sequence[float]) -> float | None:
    """Correlação de postos (empates pela média dos postos)."""

    def postos(v: Sequence[float]) -> list[float]:
        ordem = sorted(range(len(v)), key=lambda i: v[i])
        saida = [0.0] * len(v)
        i = 0
        while i < len(ordem):
            j = i
            while j + 1 < len(ordem) and v[ordem[j + 1]] == v[ordem[i]]:
                j += 1
            for k in range(i, j + 1):
                saida[ordem[k]] = (i + j) / 2 + 1
            i = j + 1
        return saida

    if len(a) < 3:
        return None
    ra, rb = postos(a), postos(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb, strict=True))
    va = math.sqrt(sum((x - ma) ** 2 for x in ra))
    vb = math.sqrt(sum((y - mb) ** 2 for y in rb))
    return round(cov / (va * vb), 4) if va and vb else None


# ---------------------------------------------------------------- tempo


def minuto(iso: str | None) -> float | None:
    """Minutos após 17:00 de Brasília de 25/10/2026, 1 casa."""
    if iso is None:
        return None
    return round((utc(iso) - T0).total_seconds() / 60.0, 1)


def brt(iso: str | None) -> str | None:
    """Instante ISO em Brasília, `AAAA-MM-DD HH:MM:SS`."""
    if iso is None:
        return None
    return utc(iso).astimezone(BRT).strftime("%Y-%m-%d %H:%M:%S")


def hhmm(min_: float | None) -> str | None:
    if min_ is None:
        return None
    t = T0 + timedelta(minutes=min_)
    texto = t.astimezone(BRT).strftime("%H:%M")
    dias = (t.astimezone(BRT).date() - T0.astimezone(BRT).date()).days
    return texto + (f"+{dias}d" if dias else "")


def totalizado_corrigido(
    uf: str, totalizado: str | None, gerado: str | None
) -> str | None:
    """`totalizado_em` em Brasília real.

    Nas UFs fora de UTC-3 o TSE imprime a hora local rotulada como Brasília.
    Corrige quando gerado menos totalizado fica a até 10 min do deslocamento,
    a mesma regra de `corrigirTotalizadoEm` do coletor.
    """
    if totalizado is None:
        return None
    fuso = FUSO_TOTALIZACAO_MIN.get(uf.lower())
    if not fuso or gerado is None:
        return totalizado
    dif = (utc(gerado) - utc(totalizado)).total_seconds() / 60.0
    if abs(dif - fuso) <= 10:
        t = utc(totalizado) + timedelta(minutes=fuso)
        return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return totalizado


def regiao_de(uf: str) -> str:
    return regiao(uf)


def sigla_regiao(uf: str) -> str:
    return SIGLA_REGIAO[regiao(uf)]


def colunar(colunas: Sequence[str], linhas: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {
        "colunas": list(colunas),
        "linhas": [[r.get(c) for c in colunas] for r in linhas],
    }


def ler_json(caminho: Path) -> Any:
    return json.loads(caminho.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- banco

CAMPOS = (
    "ts",
    "st",
    "pst",
    "te",
    "comparecimento",
    "abstencao",
    "vv",
    "vb",
    "tvn",
    "tv",
)


def _lotes(valores: Sequence[Any], tamanho: int = 900) -> Iterable[Sequence[Any]]:
    for i in range(0, len(valores), tamanho):
        yield valores[i : i + tamanho]


class Banco2T:
    """Consultas somente leitura ao banco do 2º turno."""

    def __init__(self, caminho: Path = BANCO_2T) -> None:
        self.caminho = caminho
        self.con = sqlite3.connect(f"file:{caminho}?mode=ro", uri=True, timeout=30)
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA query_only = 1")

    def fechar(self) -> None:
        self.con.close()

    def linhas(self, sql: str, parametros: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self.con.execute(sql, parametros).fetchall()]

    def um(self, sql: str, parametros: Sequence[Any] = ()) -> Any:
        return self.con.execute(sql, parametros).fetchone()[0]

    def arquivos(self, ele: int, nivel: str) -> list[dict[str, Any]]:
        return self.linhas(
            "SELECT id, chave, uf, municipio_cd, zona_cd FROM arquivo "
            "WHERE tipo = 'u' AND eleicao_cd = ? AND nivel = ?",
            (ele, nivel),
        )

    def vigentes(self, ele: int, nivel: str) -> list[dict[str, Any]]:
        """Versão vigente (maior gerado_em) de cada arquivo de resultado do nível."""
        campos = ", ".join(f"t.{c}" for c in CAMPOS)
        sql = (
            "WITH r AS (SELECT s.id, s.arquivo_id, s.gerado_em, s.capturado_em, "
            "s.totalizado_em, s.dt, s.ht, s.regressivo, ROW_NUMBER() OVER ("
            "PARTITION BY s.arquivo_id ORDER BY s.gerado_em DESC, s.id DESC) AS rn "
            "FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id "
            "WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.nivel = ?) "
            "SELECT a.id AS arquivo_id, a.chave, a.uf, a.municipio_cd, a.zona_cd, "
            "r.id AS snapshot_id, r.gerado_em, r.capturado_em, r.totalizado_em, "
            f"r.dt, r.ht, r.regressivo, {campos} FROM r "
            "JOIN arquivo a ON a.id = r.arquivo_id "
            "JOIN totais t ON t.snapshot_id = r.id WHERE r.rn = 1"
        )
        saida = self.linhas(sql, (ele, nivel))
        votos = self.votos([r["snapshot_id"] for r in saida])
        for r in saida:
            r["votos"] = votos.get(r["snapshot_id"], {})
        return saida

    def votos(self, snapshot_ids: Sequence[int]) -> dict[int, dict[str, int]]:
        saida: dict[int, dict[str, int]] = {}
        for lote in _lotes(list(snapshot_ids)):
            marcas = ",".join("?" * len(lote))
            for sid, sq, vap in self.con.execute(
                "SELECT snapshot_id, sqcand, vap FROM voto_candidato "
                f"WHERE snapshot_id IN ({marcas})",
                lote,
            ).fetchall():
                saida.setdefault(sid, {})[str(sq)] = vap or 0
        return saida

    def versoes(
        self, ele: int, nivel: str, com_votos: bool = True
    ) -> dict[int, list[dict[str, Any]]]:
        """Todas as versões genuínas (pela hora de geração) de cada arquivo do nível."""
        campos = ", ".join(f"t.{c}" for c in CAMPOS)
        sql = (
            "SELECT s.id, s.arquivo_id, s.gerado_em, s.capturado_em, s.totalizado_em, "
            f"s.dt, s.ht, s.idg, s.regressivo, {campos} FROM snapshot s "
            "JOIN arquivo a ON a.id = s.arquivo_id "
            "JOIN totais t ON t.snapshot_id = s.id "
            "WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.nivel = ? "
            "ORDER BY s.arquivo_id, s.id"
        )
        por_arq: dict[int, list[dict[str, Any]]] = {}
        for r in self.linhas(sql, (ele, nivel)):
            por_arq.setdefault(r["arquivo_id"], []).append(r)
        saida = {k: [dict(s) for s in versoes_genuinas(v)] for k, v in por_arq.items()}
        if com_votos:
            ids = [s["id"] for v in saida.values() for s in v]
            votos = self.votos(ids)
            for v in saida.values():
                for s in v:
                    s["votos"] = votos.get(s["id"], {})
        return saida

    def todas_versoes(self, ele: int, nivel: str) -> dict[int, list[dict[str, Any]]]:
        """Todas as capturas (inclusive cópias), sem votos, para regressões."""
        sql = (
            "SELECT s.id, s.arquivo_id, s.gerado_em, s.capturado_em, s.idg, "
            "s.regressivo, t.st, t.ts FROM snapshot s "
            "JOIN arquivo a ON a.id = s.arquivo_id "
            "LEFT JOIN totais t ON t.snapshot_id = s.id "
            "WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.nivel = ? "
            "ORDER BY s.arquivo_id, s.id"
        )
        saida: dict[int, list[dict[str, Any]]] = {}
        for r in self.linhas(sql, (ele, nivel)):
            saida.setdefault(r["arquivo_id"], []).append(r)
        return saida

    def municipios(self) -> dict[str, dict[str, Any]]:
        return {
            r["cd"]: r
            for r in self.linhas("SELECT cd, uf, ibge, nome, capital FROM municipio")
        }

    def candidatos(self, ele: int) -> list[dict[str, Any]]:
        return self.linhas(
            "SELECT c.sqcand, c.uf, c.numero, c.nome_urna, p.sigla AS partido "
            "FROM candidato c LEFT JOIN partido p ON p.n = c.partido_n "
            "WHERE c.eleicao_cd = ? ORDER BY c.uf, c.numero",
            (ele,),
        )


# ---------------------------------------------------------------- placar


def placar(r: dict[str, Any], f: str = SQ_FLAVIO, l_: str = SQ_LULA) -> dict[str, Any]:
    """Placar de uma linha vigente: contagens, fatias e identidade dos aptos."""
    votos = r.get("votos", {})
    vf, vl = votos.get(f, 0), votos.get(l_, 0)
    comp, abst = r["comparecimento"] or 0, r["abstencao"] or 0
    vv, vb, vn = r["vv"] or 0, r["vb"] or 0, r["tvn"] or 0
    return {
        "secoes": r["st"],
        "secoes_total": r["ts"],
        "pst": r2(r["pst"]),
        "aptos": r["te"],
        "aptos_apurados": comp + abst,
        "comparecimento": comp,
        "abstencao": abst,
        "validos": vv,
        "brancos": vb,
        "nulos": vn,
        "flavio": vf,
        "lula": vl,
        "pct_flavio": p2(vf, vv),
        "pct_lula": p2(vl, vv),
        "margem_lula_votos": vl - vf,
        "margem_lula_pp": d2(p2(vl, vv), p2(vf, vv)),
        "pct_comparecimento": p2(comp, comp + abst),
        "pct_abstencao": p2(abst, comp + abst),
        "pct_brancos": p2(vb, comp),
        "pct_nulos": p2(vn, comp),
        "completo": bool(r["ts"]) and r["st"] == r["ts"],
        "gerado_em": r["gerado_em"],
        "gerado_brt": brt(r["gerado_em"]),
        "snapshot_id": r.get("snapshot_id", r.get("id")),
    }


def somar_placares(linhas: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Soma contagens de placares e recalcula as fatias."""
    chaves = (
        "secoes",
        "secoes_total",
        "aptos",
        "aptos_apurados",
        "comparecimento",
        "abstencao",
        "validos",
        "brancos",
        "nulos",
        "flavio",
        "lula",
    )
    s = dict.fromkeys(chaves, 0)
    n = 0
    for r in linhas:
        n += 1
        for k in chaves:
            s[k] += r.get(k) or 0
    comp, abst = s["comparecimento"], s["abstencao"]
    s.update(
        {
            "n": n,
            "pst": p2(s["secoes"], s["secoes_total"]),
            "pct_flavio": p2(s["flavio"], s["validos"]),
            "pct_lula": p2(s["lula"], s["validos"]),
            "margem_lula_votos": s["lula"] - s["flavio"],
            "margem_lula_pp": d2(
                p2(s["lula"], s["validos"]), p2(s["flavio"], s["validos"])
            ),
            "pct_comparecimento": p2(comp, comp + abst),
            "pct_abstencao": p2(abst, comp + abst),
            "pct_brancos": p2(s["brancos"], comp),
            "pct_nulos": p2(s["nulos"], comp),
        }
    )
    return s
