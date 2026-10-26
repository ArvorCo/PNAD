"""Leitura das fontes, sempre somente leitura e por UF (stream por estado).

Bancos SQLite abertos com ``?mode=ro`` e ``PRAGMA query_only``: o coletor do 2º turno pode
estar escrevendo enquanto o build lê. Fragmentos do Politize, do mapa de fiscais, das
mudanças de local e dos logs do 1º turno são lidos como estão publicados.
"""

from __future__ import annotations

import gzip
import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DB_1T = ROOT / "apuracao/data/secoes_2026.sqlite"
DB_2T = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
REGUA_1T = ROOT / "apuracao/data/referencia_1t_secoes.json"
POLITIZE = ROOT / "docs/assets/politize/dados"
LOGS_1T = ROOT / "docs/assets/logs_urnas_2026"
LOGS_2T_DB = ROOT / "data/outputs/logs_urnas_2t_2026.sqlite"
LOGS_2T = ROOT / "docs/assets/logs_urnas_2t_2026"
CLIMA = ROOT / "docs/assets/fiscais_mapa/clima"
# Mistura estatística dos dois turnos (analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md):
# o arquivo pesado fica fora do git e o compacto traz k, rótulos e o grupo atípico.
ANOMALIA_ML = ROOT / "data/outputs/apuracao_2t_2026/anomalia_secoes.json.gz"
ANOMALIA_ML_INDICE = ROOT / "analysis/apuracao_2t_2026/dados/anomalia_ml.json"

FLAVIO = 22
LULA = 13


def conectar(banco: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{banco}?mode=ro", uri=True, timeout=60)
    con.execute("PRAGMA query_only=1")
    return con


def linhas(t: dict[str, Any]) -> Iterator[dict[str, Any]]:
    cols = t["colunas"]
    for x in t["linhas"]:
        yield dict(zip(cols, x, strict=True))


def _json(caminho: Path) -> Any:
    if caminho.suffix == ".gz":
        with gzip.open(caminho, "rt", encoding="utf-8") as f:
            return json.load(f)
    return json.loads(caminho.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ Politize (1º turno)


def ufs_politize() -> list[str]:
    return sorted(p.name for p in (POLITIZE / "zona").iterdir() if p.is_dir())


def politize_zonas(uf: str) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for arq in (POLITIZE / "zona" / uf).glob("*.json"):
        d = _json(arq)
        out[int(d["zona"])] = {
            "municipios": d["municipios"],
            "secoes": {int(r["secao"]): r for r in linhas(d["secoes"])},
        }
    return out


def politize_locais(uf: str) -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    """Cadastro dos locais (``local_id`` → campos) e nome de cada município."""
    locais: dict[str, dict[str, Any]] = {}
    nomes: dict[str, str] = {}
    campos = ("local_nr", "zona", "nome", "endereco", "bairro", "cep", "lat", "lon")
    for arq in (POLITIZE / "mun" / uf).glob("*.json"):
        d = _json(arq)
        nomes[d["mun_tse"]] = d["nome"]
        for r in linhas(d["locais"]):
            locais[r["local_id"]] = {
                "mun_tse": d["mun_tse"],
                "coord_fonte": r.get("coord_fonte"),
                **{c: r.get(c) for c in campos},
            }
    return locais, nomes


def politize_indice() -> dict[str, Any]:
    return _json(POLITIZE / "indice.json")


def fiscal(uf: str) -> dict[tuple[int, int], tuple[str, int, list[str], str | None]]:
    out: dict[tuple[int, int], tuple[str, int, list[str], str | None]] = {}
    pasta = POLITIZE / "fiscal" / uf
    if not pasta.exists():
        return out
    for arq in pasta.glob("*.json"):
        d = _json(arq)
        z = int(d["zona"])
        for r in linhas(d["secoes"]):
            c13 = r.get("c13")
            out[(z, int(r["secao"]))] = (
                r["nivel"],
                int(r["pontos"]),
                [s[0] for s in (r.get("sinais") or [])],
                c13[0] if c13 else None,
            )
    return out


def regras_fiscal() -> dict[str, Any]:
    return _json(POLITIZE / "fiscal" / "regras.json")


def mudancas(uf: str) -> dict[tuple[int, int], dict[str, Any]]:
    out: dict[tuple[int, int], dict[str, Any]] = {}
    pasta = POLITIZE / "mudancas" / uf
    if not pasta.exists():
        return out
    for arq in pasta.glob("*.json"):
        d = _json(arq)
        z = int(d["zona"])
        for s, m in d["secoes"].items():
            out[(z, int(s))] = {
                "cat": m.get("categoria"),
                "nome1": m.get("nome_1t"),
                "nome2": m.get("nome_2t"),
                "end2": m.get("end_2t"),
                "bairro2": m.get("bairro_2t"),
                "dist_m": m.get("distancia_m"),
                "motivo": m.get("motivo_tre"),
                "url": m.get("url_tre"),
                "fonte": m.get("fonte"),
                "real": bool(m.get("mudanca_real")),
                "maps": m.get("maps_novo"),
            }
    return out


def mudancas_indice() -> dict[str, Any]:
    return _json(POLITIZE / "mudancas" / "indice.json")


# ------------------------------------------------------------------ logs e clima


def logs_1t(uf: str) -> dict[tuple[int, int], list[str]]:
    out: dict[tuple[int, int], list[str]] = {}
    pasta = LOGS_1T / "zona" / uf
    if not pasta.exists():
        return out
    for arq in pasta.glob("*.json.gz"):
        d = _json(arq)
        z = int(d["zona"])
        cols = d["colunas"]
        i_s, i_g = cols.index("secao"), cols.index("sinais")
        for x in d["linhas"]:
            out[(z, int(x[i_s]))] = list(x[i_g] or [])
    return out


def clima_1t(uf: str) -> dict[str, dict[str, Any]]:
    arq = CLIMA / f"{uf}.json"
    if not arq.exists():
        return {}
    d = _json(arq)
    out = {}
    for r in linhas(d):
        out[r["local_id"]] = {
            "chuva_mm": r.get("chuva_votacao_mm"),
            "chuva_dia_mm": r.get("chuva_04_10_mm"),
            "faixa": r.get("faixa_chuva_votacao"),
            "rajada_kmh": r.get("rajada_votacao_kmh"),
            "pico": r.get("hora_pico_chuva"),
            "urnas": r.get("urnas"),
            "urnas_bateria_votacao": r.get("urnas_bateria_votacao"),
        }
    return out


def previsao_2t() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    arq = CLIMA / "previsao.json"
    if not arq.exists():
        return {}, {}
    d = _json(arq)
    cel = {
        k: {
            "chuva_mm": v.get("chuva_mm"),
            "prob_pct": v.get("prob_pct"),
            "rajada_kmh": v.get("rajada_kmh"),
            "risco": v.get("risco"),
        }
        for k, v in d["celulas"].items()
    }
    meta = {k: d.get(k) for k in ("gerado_em", "alvo", "rotulo", "celula_graus")}
    return cel, meta


def observado_2t() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Chuva de 25/10 por célula de 0,25° (estação CEMADEN ou modelo provisório)."""
    arq = CLIMA / "observado_2t.json"
    if not arq.exists():
        return {}, {}
    d = _json(arq)
    cols = d["colunas"]
    rot = d.get("rotulos_fonte", {})
    cel = {}
    for k, v in d["celulas"].items():
        r = dict(zip(cols, v, strict=True))
        cel[k] = {
            "chuva_mm": r["chuva_votacao_mm"],
            "fonte_votacao": r["fonte_votacao"],
            "chuva_dia_mm": r["chuva_dia_mm"],
            "fonte_dia": r["fonte_dia"],
            "rajada_kmh": r["rajada_votacao_kmh"],
            "n_estacoes": r["n_estacoes"],
            "dist_km": r["distancia_min_km"],
            "fonte": r["fonte"],
        }
    meta = {
        k: d.get(k)
        for k in (
            "gerado_em",
            "dia",
            "fonte",
            "celula_graus",
            "raio_km",
            "janela_votacao_brasilia",
            "nota",
            "cortes",
        )
    }
    meta["rotulos_fonte"] = rot
    return cel, meta


# ------------------------------------------------------------------ boletins de urna


def catalogo_2t(uf: str) -> list[tuple[str, int, int, int | None, str | None]]:
    """(mun, zona, seção, principal, recebimento) de todas as seções do 2º turno."""
    with conectar(DB_2T) as con:
        return con.execute(
            "SELECT mun, zona, secao, nsp, dr_hr FROM secao WHERE uf=?", (uf.lower(),)
        ).fetchall()


CAMPOS_BU = (
    "mun, zona, secao, local, aptos, comparecimento, comp_sem_biometria, "
    "hab_biometria, hab_ano_nascimento, abertura, encerramento, emissao, "
    "numero_interno_urna, modelo_urna, tipo_urna, tipo_arquivo, n_cargas, codigo_carga"
)


def bu(banco: Path, uf: str) -> dict[tuple[int, int], dict[str, Any]]:
    """BU por (zona, seção) com votos de presidente e o recebimento do arquivo."""
    out: dict[tuple[int, int], dict[str, Any]] = {}
    with conectar(banco) as con:
        con.row_factory = sqlite3.Row
        for r in con.execute(
            f"SELECT {CAMPOS_BU}, s.dr_hr FROM bu b JOIN secao s "
            "USING (uf, mun, zona, secao) WHERE b.uf=?",
            (uf.lower(),),
        ):
            d = dict(r)
            d.update(flavio=0, lula=0, brancos=0, nulos=0, outros=0)
            out[(int(r["zona"]), int(r["secao"]))] = d
        for z, s, tipo, numero, v in con.execute(
            "SELECT zona, secao, tipo, numero, votos FROM voto_secao "
            "WHERE uf=? AND cargo=1",
            (uf.lower(),),
        ):
            d = out.get((int(z), int(s)))
            if d is None:
                continue
            if tipo == 1 and numero == FLAVIO:
                d["flavio"] += v
            elif tipo == 1 and numero == LULA:
                d["lula"] += v
            elif tipo == 2:
                d["brancos"] += v
            elif tipo == 3:
                d["nulos"] += v
            else:
                d["outros"] += v
    return out


def mapa_urnas_1t() -> dict[int, tuple[str, str, int, int]]:
    """Número interno da urna → seção onde emitiu BU no 1º turno (país inteiro)."""
    out: dict[int, tuple[str, str, int, int]] = {}
    with conectar(DB_1T) as con:
        for uf, mun, z, s, i, ta in con.execute(
            "SELECT uf, mun, zona, secao, numero_interno_urna, tipo_arquivo FROM bu "
            "WHERE numero_interno_urna IS NOT NULL"
        ):
            # BU do sistema de apuração traz o número do equipamento da junta
            if (ta or 0) >= 3:
                continue
            out.setdefault(int(i), (uf.upper(), mun, int(z), int(s)))
    return out


def contar_2t() -> tuple[int, int]:
    with conectar(DB_2T) as con:
        n_bu = con.execute("SELECT COUNT(*) FROM bu").fetchone()[0]
        n_pr = con.execute(
            "SELECT COUNT(*) FROM secao WHERE nsp IS NULL OR nsp=secao"
        ).fetchone()[0]
    return int(n_bu), int(n_pr)


def logs_2t_disponivel() -> bool:
    return LOGS_2T_DB.exists() and (LOGS_2T / "zona").exists()


def logs_2t(uf: str) -> dict[tuple[int, int], dict[str, Any]]:
    """Camada pública dos logs do 2º turno (mesmo formato do 1º), mais o erro da MR."""
    out: dict[tuple[int, int], dict[str, Any]] = {}
    pasta = LOGS_2T / "zona" / uf
    if not pasta.exists():
        return out
    for arq in pasta.glob("*.json.gz"):
        d = _json(arq)
        z = int(d["zona"])
        for r in linhas(d):
            out[(z, int(r["secao"]))] = {
                "sinais": list(r.get("sinais") or []),
                "bateria_votacao": r.get("bateria_votacao"),
                "bateria_simultaneas": r.get("bateria_simultaneas"),
                "erro_mr": r.get("erro_mr_pre_zeresima"),
                "reinicios_sistema": r.get("reinicios_sistema"),
            }
    return out


# ------------------------------------------------------------------ mistura estatística

SecaoML = tuple[int, float, float, bool]
_ANOMALIA_CACHE: dict[
    tuple[Path, int | None], dict[str, dict[tuple[int, int], SecaoML]]
] = {}


def _anomalia_ml_tudo() -> dict[str, dict[tuple[int, int], SecaoML]]:
    """Arquivo pesado inteiro, lido uma vez por caminho e data, separado por UF.

    Convenção de ``secoes_linhas``: ``{"colunas": [uf, mun, zona, secao, grupo, score, p,
    anomalo], "linhas": [...]}`` em gzip. Ausente, devolve ``{}``.
    """
    arq = ANOMALIA_ML
    chave = (arq, arq.stat().st_mtime_ns if arq.exists() else None)
    if chave in _ANOMALIA_CACHE:
        return _ANOMALIA_CACHE[chave]
    por_uf: dict[str, dict[tuple[int, int], SecaoML]] = {}
    if arq.exists():
        d = _json(arq)
        cols = d["colunas"]
        i = {
            c: cols.index(c)
            for c in ("uf", "zona", "secao", "grupo", "score", "p", "anomalo")
        }
        for x in d["linhas"]:
            por_uf.setdefault(str(x[i["uf"]]).upper(), {})[
                (int(x[i["zona"]]), int(x[i["secao"]]))
            ] = (
                int(x[i["grupo"]]),
                float(x[i["score"]]),
                float(x[i["p"]]),
                bool(x[i["anomalo"]]),
            )
    _ANOMALIA_CACHE.clear()
    _ANOMALIA_CACHE[chave] = por_uf
    return por_uf


def anomalia_ml(uf: str) -> dict[tuple[int, int], SecaoML]:
    """(zona, seção) → (grupo, score, p, anomalo) da UF; ``{}`` sem o arquivo pesado."""
    return _anomalia_ml_tudo().get(uf.upper(), {})


def anomalia_ml_indice() -> dict[str, Any]:
    """Disponibilidade e catálogo da mistura: só fica ``disponivel`` com os dois arquivos."""
    out: dict[str, Any] = {
        "disponivel": False,
        "secoes": None,
        "anomalas": None,
        "gerado_em": None,
        "k": None,
        "grupo_atipico": None,
        "rotulos": {},
        "rotulo": None,
    }
    compacto = ANOMALIA_ML_INDICE.exists()
    if compacto:
        d = _json(ANOMALIA_ML_INDICE)
        out.update(
            gerado_em=d.get("gerado_em"),
            k=d.get("k_escolhido"),
            grupo_atipico=(d.get("mais_anomalo") or {}).get("id"),
            rotulos={str(c["id"]): c.get("rotulo") for c in d.get("componentes") or []},
            rotulo=d.get("rotulo"),
        )
    tudo = _anomalia_ml_tudo()
    if tudo and compacto:
        out["disponivel"] = True
        out["secoes"] = sum(len(v) for v in tudo.values())
        out["anomalas"] = sum(1 for v in tudo.values() for t in v.values() if t[3])
    return out


def logs_2t_detalhe(uf: str) -> dict[tuple[int, int], dict[str, Any]]:
    """Partidas da urna no dia e metadados (versão, carga, MR) do banco de métricas do 2º turno."""
    out: dict[tuple[int, int], dict[str, Any]] = {}
    if not LOGS_2T_DB.exists():
        return out
    with conectar(LOGS_2T_DB) as con:
        for z, s, partidas, meta in con.execute(
            "SELECT zona, secao, json_extract(resumo, '$.partidas_dia'), "
            "json_extract(resumo, '$.metadados_urna') FROM metricas "
            "WHERE lower(uf)=? AND status='ok'",
            (uf.lower(),),
        ):
            out[(int(z), int(s))] = {
                "partidas": json.loads(partidas) if partidas else [],
                "meta": json.loads(meta) if meta else {},
            }
    return out
