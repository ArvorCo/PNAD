#!/usr/bin/env python3
"""Pesquisas finais, previsões da casa e voto útil contra a urna do 1º turno de 2026.

Lê o resultado oficial congelado em ``apuracao/data/boletins/final.json`` e no
banco da apuração (somente leitura), as pesquisas nacionais de
``analysis/reponderacao/pesquisas/`` com campo encerrado a partir de 25/09, o
agregador por renda, a previsão presidencial, as de governador e Senado e o
mapa do voto útil, e grava em ``analysis/apuracao_2026/dados/``:

- ``pesquisas_vs_urna.json``: erro de cada pesquisa (publicada e reponderada),
  das médias, das previsões da casa e das previsões estaduais;
- ``voto_util.json``: terceira via nas pesquisas contra a urna, reserva de 2º
  turno medida contra a revelada e a decomposição do erro;
- ``pesquisas.md``: memorando com a tabela e os parágrafos a publicar.

Uso:
    python3 scripts/apuracao-2026-pesquisas.py
"""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
import statistics
import subprocess
from datetime import date
from pathlib import Path

from apuracao_2026 import pesquisas as P
from apuracao_2026 import pesquisas_casa as C
from apuracao_2026 import pesquisas_estaduais as E
from apuracao_2026 import pesquisas_memo as MEMO
from apuracao_2026 import pesquisas_voto_util as V

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "analysis/apuracao_2026/dados"
FINAL = ROOT / "apuracao/data/boletins/final.json"
BANCO = ROOT / "apuracao/data/apuracao.sqlite"
PESQUISAS = ROOT / "analysis/reponderacao/pesquisas"
AGREGADOR = ROOT / "docs/assets/reponderacao_pnad.json"
PREVISAO = ROOT / "docs/assets/predicao_2026_1T_presidente.json"
GOVERNADOR = ROOT / "docs/assets/predicao_governador.json"
SENADO = ROOT / "docs/assets/predicao_senado.json"
VOTO_UTIL = ROOT / "docs/assets/voto_util_092026.json"
ERRO_2022 = ROOT / "analysis/predicao_2026/erro_2022/erro_2022.json"

ELEICAO = date(2026, 10, 4)
INICIO_CAMPO = "2026-09-25"
FEDERAL, ESTADUAL = 6257, 6259
DEFF = 1.5
# Número na urna para a chave usada nas pesquisas.
NUMEROS = {
    22: "flavio",
    13: "lula",
    70: "cury",
    14: "renan_santos",
    55: "caiado",
    30: "zema",
    80: "samara",
    16: "hertz",
    27: "clariana",
    21: "edmilson",
    35: "grassi",
    29: "rui",
}
# Mesma lista de ``scripts/predicao_2026/base.py::national``.
FORA_DO_CENARIO = ("marcal", "ciro", "aldo", "daciolo", "aecio", "hero", "joaquim")


# ---------------------------------------------------------------- entrada


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def ler(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def fonte(path: Path) -> dict:
    commit = subprocess.run(
        ["git", "log", "-1", "--format=%h %cI", "--", rel(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return {
        "arquivo": rel(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "ultimo_commit": commit or None,
    }


def arredondar(x, casas: int = 6):
    if isinstance(x, float):
        return round(x, casas)
    if isinstance(x, dict):
        return {k: arredondar(v, casas) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [arredondar(v, casas) for v in x]
    return x


def modo_coleta(metodo: str) -> str:
    m = metodo.lower()
    if m.startswith("presencial"):
        return "presencial"
    if m.startswith("online"):
        return "online"
    if m.startswith("telef"):
        return "telefone"
    return "outro"


# ---------------------------------------------------------------- urna


class Banco:
    """Leitura do banco da apuração sem escrita (``mode=ro``)."""

    def __init__(self, path: Path):
        self.con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        self.cur = self.con.cursor()

    def arquivo(self, eleicao: int, cargo: int, nivel: str, uf: str | None) -> int:
        sql = (
            "SELECT id FROM arquivo WHERE tipo = 'u' AND eleicao_cd = ? "
            "AND cargo_cd = ? AND nivel = ?"
        )
        args: list = [eleicao, cargo, nivel]
        if uf is not None:
            sql += " AND lower(uf) = ?"
            args.append(uf.lower())
        rows = self.cur.execute(sql, args).fetchall()
        if len(rows) != 1:
            raise SystemExit(
                f"Arquivo ambíguo ou ausente: {eleicao} {cargo} {nivel} {uf}"
            )
        return rows[0][0]

    def snapshot(
        self, arquivo_id: int, *, gerado_em: str | None = None, ate: str | None = None
    ) -> dict:
        sql = (
            "SELECT s.id, s.gerado_em, s.capturado_em, s.sha256, s.tf, t.pst, t.vv, "
            "t.st, t.ts FROM snapshot s JOIN totais t ON t.snapshot_id = s.id "
            "WHERE s.arquivo_id = ? AND s.regressivo = 0"
        )
        args: list = [arquivo_id]
        if gerado_em is not None:
            sql += " AND s.gerado_em = ?"
            args.append(gerado_em)
        if ate is not None:
            sql += " AND s.capturado_em <= ?"
            args.append(ate)
        row = self.cur.execute(sql + " ORDER BY s.id DESC LIMIT 1", args).fetchone()
        if row is None:
            raise SystemExit(f"Sem versão para o arquivo {arquivo_id}")
        chaves = ("id", "gerado_em", "capturado_em", "sha256", "tf", "pst", "vv")
        out = dict(zip(chaves, row[:7], strict=True))
        out["secoes"], out["secoes_total"] = row[7], row[8]
        return out

    def candidatos(self, snapshot_id: int) -> list[dict]:
        rows = self.cur.execute(
            "SELECT v.sqcand, c.numero, c.nome_urna, p.sigla, v.vap, v.pvapn, v.st, "
            "v.eleito FROM voto_candidato v JOIN candidato c ON c.sqcand = v.sqcand "
            "LEFT JOIN partido p ON p.n = c.partido_n WHERE v.snapshot_id = ? "
            "ORDER BY v.vap DESC",
            (snapshot_id,),
        ).fetchall()
        chaves = ("sqcand", "numero", "nome", "partido", "votos", "pct", "st", "eleito")
        return [dict(zip(chaves, r, strict=True)) for r in rows]


def versao(s: dict) -> dict:
    return {k: s[k] for k in ("id", "gerado_em", "capturado_em", "sha256", "tf", "pst")}


def votos_presidente(cands: list[dict]) -> dict[str, int]:
    votos = {}
    for c in cands:
        if c["numero"] not in NUMEROS:
            raise SystemExit(f"Candidatura sem chave: {c['numero']} {c['nome']}")
        votos[NUMEROS[c["numero"]]] = int(c["votos"] or 0)
    return votos


def urna_presidente(db: Banco, final: dict) -> dict:
    """Presidente no corte do ``final.json``: Brasil, UFs e regiões."""
    pres = final["presidente"]
    if pres["fonte"] != "tse":
        raise SystemExit("final.json não traz o arquivo nacional do TSE")
    snap = db.snapshot(db.arquivo(FEDERAL, 1, "br", None), gerado_em=pres["gerado_em"])
    cands = db.candidatos(snap["id"])
    votos = votos_presidente(cands)
    if snap["vv"] != pres["validos"]:
        raise SystemExit("Válidos do banco diferem do final.json")
    for t in pres["top5"]:
        c = next(x for x in cands if x["nome"] == t["nome"])
        if c["votos"] != t["votos"]:
            raise SystemExit(f"Votos de {t['nome']} diferem do final.json")
    validos = {k: 100 * v / snap["vv"] for k, v in votos.items()}
    ufs = {}
    ref = {u["uf"]: u for u in pres["ufs"]}
    for uf in [*sorted(ref), "ZZ"]:
        s = db.snapshot(db.arquivo(FEDERAL, 1, "uf", uf), ate=final["gerado_em"])
        v = votos_presidente(db.candidatos(s["id"]))
        pct = {k: 100 * x / s["vv"] for k, x in v.items()}
        if uf in ref:
            r = ref[uf]
            lider, seg = (
                ("flavio", "lula") if r["lider"] != "LULA" else ("lula", "flavio")
            )
            if (round(pct[lider], 2), round(pct[seg], 2)) != (
                r["pct_lider"],
                r["pct_segundo"],
            ):
                raise SystemExit(f"{uf}: percentuais diferem do final.json")
        ufs[uf] = {
            "votos": v,
            "validos_votos": s["vv"],
            "validos": pct,
            "versao": versao(s),
        }
    soma = {k: sum(u["votos"][k] for u in ufs.values()) for k in votos}
    soma_validos = sum(u["validos_votos"] for u in ufs.values())
    sem_zz = {k: sum(u["votos"][k] for x, u in ufs.items() if x != "ZZ") for k in votos}
    validos_sem_zz = sum(u["validos_votos"] for x, u in ufs.items() if x != "ZZ")
    return {
        "versao_nacional": versao(snap),
        "corte_final_json": final["gerado_em"],
        "secoes": snap["secoes"],
        "secoes_total": snap["secoes_total"],
        "comparecimento": pres["comparecimento"],
        "brancos": pres["brancos"],
        "nulos": pres["nulos"],
        "votos": votos,
        "validos_votos": snap["vv"],
        "validos": validos,
        "validos_sem_exterior": {
            k: 100 * v / validos_sem_zz for k, v in sem_zz.items()
        },
        "soma_ufs_validos": soma_validos,
        "soma_ufs_votos": soma,
        "ufs": ufs,
    }


# ---------------------------------------------------------------- pesquisas


def carregar_pesquisas(agg: dict, previsao: dict, urna: dict) -> list[dict]:
    rep = {p["id"]: p for p in agg["pesquisas"]}
    cenario = agg["benchmark"]["cenario_principal"]
    efeitos = previsao["nacional"]["efeitos_casa"]
    alvo = urna["validos"]
    eam = sorted(k for k, x in alvo.items() if x >= 2)
    linhas = []
    for path in sorted(PESQUISAS.glob("*.json")):
        p = ler(path)
        if p["campo"]["fim"] < INICIO_CAMPO:
            continue
        pub = p["publicado"]["1t"]
        if any(pub.get(k, 0) > 0 for k in FORA_DO_CENARIO):
            raise SystemExit(f"{p['id']}: cartão fora do cenário")
        v_pub, aud_pub = P.validos(pub)
        r = rep.get(p["id"])
        if r is not None and r["publicado"]["1t"] != pub:
            raise SystemExit(f"{p['id']}: publicado difere do agregador")
        adj = (
            ((r or {}).get("turnos", {}).get("1t") or {})
            .get("cenarios", {})
            .get(cenario, {})
            .get("ajustado")
        )
        rep_bloco = None
        if adj:
            v_rep, aud_rep = P.validos({**pub, **adj})
            rep_bloco = {
                "total": {**pub, **adj},
                "validos": v_rep,
                "auditoria": aud_rep,
                **P.erros_vs_urna(v_rep, alvo, eam),
            }
        n_validos = p["n"] * aud_pub["soma_candidaturas_pct_total"] / 100
        margem = P.margem_diferenca_aas(
            p["n"],
            aud_pub["soma_candidaturas_pct_total"] / 100,
            v_pub["lula"],
            v_pub["flavio"],
        )
        erros_pub = P.erros_vs_urna(v_pub, alvo, eam)
        efeito = efeitos.get(p["instituto"])
        linhas.append(
            {
                "id": p["id"],
                "instituto": p["instituto"],
                "registro_tse": p.get("registro_tse"),
                "campo": p["campo"],
                "divulgacao": p.get("divulgacao"),
                "n": p["n"],
                "metodo": p.get("metodo"),
                "modo": modo_coleta(p.get("metodo") or ""),
                "dias_fim_campo_ate_urna": (
                    ELEICAO - date.fromisoformat(p["campo"]["fim"])
                ).days,
                "fonte": fonte(path),
                "perfil_renda": (p.get("renda") or {}).get("perfil_tipo"),
                "publicado": {
                    "total": pub,
                    "validos": v_pub,
                    "auditoria": aud_pub,
                    **erros_pub,
                },
                "reponderado": rep_bloco,
                "reponderado_cenario": cenario if rep_bloco else None,
                "reponderado_motivo": (
                    None
                    if rep_bloco
                    else (p.get("motivo") or "sem cruzamento de renda no 1º turno")
                ),
                "segundo_turno_publicado": p["publicado"].get("2t"),
                "n_validos_aproximado": n_validos,
                "margem_95_diferenca_aas_pp": margem,
                "margem_95_diferenca_deff_pp": margem * math.sqrt(DEFF),
                "erro_diferenca_fora_da_margem_aas": abs(
                    erros_pub["diferenca_lula_menos_flavio"]["erro"]
                )
                > margem,
                "efeito_casa_pre_eleicao_pp": (
                    efeito["desvio_margem_pp"] if efeito else None
                ),
            }
        )
    chaves = [(x["instituto"], x["campo"]["inicio"], x["campo"]["fim"]) for x in linhas]
    if len(chaves) != len(set(chaves)):
        raise SystemExit("Mesma casa e campo duas vezes")
    ultima = {}
    for x in linhas:
        k = (x["campo"]["fim"], x["divulgacao"] or "", x["id"])
        if x["instituto"] not in ultima or k > ultima[x["instituto"]][0]:
            ultima[x["instituto"]] = (k, x["id"])
    finais = {v[1] for v in ultima.values()}
    for x in linhas:
        x["ultima_onda_da_casa"] = x["id"] in finais
    return linhas


def linha_media(
    nome: str, regra: str, linhas: list[dict], qual: str, urna: dict
) -> dict:
    """Média simples das parcelas válidas: blocos com todas, candidatos com quem abre."""
    alvo = urna["validos"]
    eam = sorted(k for k, x in alvo.items() if x >= 2)
    vets = [x[qual]["validos"] for x in linhas]
    blocos = P.media_vetores([P.blocos(v) for v in vets])
    abertos = [P.vetor_terceiros(v) for v in vets]
    abertos = [v for v in abertos if v is not None]
    cand = P.media_vetores(abertos) if abertos else None
    erro_b = {k: blocos[k] - P.blocos(alvo)[k] for k in blocos}
    dif = blocos["lula"] - blocos["flavio"]
    dif_u = alvo["lula"] - alvo["flavio"]
    erros_cand = (
        P.erros_vs_urna({**cand}, {**P.vetor_terceiros(alvo)}, eam) if cand else None
    )
    return {
        "nome": nome,
        "regra": regra,
        "qual": qual,
        "ondas": [x["id"] for x in linhas],
        "n_ondas": len(linhas),
        "validos_blocos": blocos,
        "erro_blocos_pp": erro_b,
        "diferenca_lula_menos_flavio": {
            "pesquisa": dif,
            "urna": dif_u,
            "erro": dif - dif_u,
        },
        "eam_blocos_pp": statistics.fmean(abs(e) for e in erro_b.values()),
        "validos_candidatos": cand,
        "n_ondas_com_candidatos": len(abertos),
        "erros_candidatos": erros_cand,
    }


def resumo_casas(linhas: list[dict], qual: str) -> dict:
    erros = [x[qual]["diferenca_lula_menos_flavio"]["erro"] for x in linhas]
    se = [x["margem_95_diferenca_aas_pp"] / P.Z95 for x in linhas]
    amostral = math.sqrt(statistics.fmean(s**2 for s in se))
    out = P.resumo_erros(erros)
    out["desvio_esperado_so_amostragem_aas_pp"] = amostral
    out["desvio_esperado_so_amostragem_deff_pp"] = amostral * math.sqrt(DEFF)
    out["fora_da_margem_aas"] = sum(
        abs(e) > x["margem_95_diferenca_aas_pp"]
        for e, x in zip(erros, linhas, strict=True)
    )
    return out


def efeito_reponderacao(linhas: list[dict]) -> dict:
    por_onda = []
    for x in linhas:
        if not x["reponderado"]:
            continue
        ep = x["publicado"]["diferenca_lula_menos_flavio"]["erro"]
        er = x["reponderado"]["diferenca_lula_menos_flavio"]["erro"]
        delta = abs(er) - abs(ep)
        por_onda.append(
            {
                "id": x["id"],
                "instituto": x["instituto"],
                "ultima_onda_da_casa": x["ultima_onda_da_casa"],
                "perfil_renda": x["perfil_renda"],
                "erro_dif_publicado": ep,
                "erro_dif_reponderado": er,
                "deslocamento_lula_menos_flavio": er - ep,
                "variacao_erro_absoluto_dif": delta,
                "direcao": (
                    "aproximou"
                    if delta < -0.05
                    else "afastou" if delta > 0.05 else "neutro"
                ),
                "variacao_flavio": x["reponderado"]["validos"]["flavio"]
                - x["publicado"]["validos"]["flavio"],
                "variacao_lula": x["reponderado"]["validos"]["lula"]
                - x["publicado"]["validos"]["lula"],
                "variacao_eam_blocos": x["reponderado"]["eam_blocos_pp"]
                - x["publicado"]["eam_blocos_pp"],
            }
        )
    finais = [r for r in por_onda if r["ultima_onda_da_casa"]]

    def resumo(rs):
        return {
            "n": len(rs),
            "aproximou": sum(r["direcao"] == "aproximou" for r in rs),
            "afastou": sum(r["direcao"] == "afastou" for r in rs),
            "neutro": sum(r["direcao"] == "neutro" for r in rs),
            "deslocamento_medio_lula_menos_flavio": statistics.fmean(
                r["deslocamento_lula_menos_flavio"] for r in rs
            ),
            "variacao_media_erro_absoluto_dif": statistics.fmean(
                r["variacao_erro_absoluto_dif"] for r in rs
            ),
        }

    return {
        "regra": "variação do erro absoluto na diferença L−F; negativa aproxima da urna",
        "por_onda": por_onda,
        "todas": resumo(por_onda),
        "ultimas_ondas": resumo(finais),
    }


def painel_2022_2026(erro22: dict, finais: list[dict]) -> dict:
    """A mesma casa nas duas eleições: erro na diferença e teste da margem."""
    por_casa = {x["instituto"]: x for x in finais}
    linhas = []
    for c in erro22["por_casa"]:
        x = por_casa.get(c["casa_2026"] or "")
        if x is None:
            continue
        e26 = x["publicado"]["diferenca_lula_menos_flavio"]["erro"]
        linhas.append(
            {
                "casa_2022": c["casa"],
                "casa_2026": x["instituto"],
                "id_2026": x["id"],
                "na_media_2022": c["incluir"],
                "motivo_fora_2022": c.get("motivo_exclusao"),
                "erro_2022_lula_menos_bolsonaro": c["diferenca_lula_menos_bolsonaro"][
                    "erro"
                ],
                "fora_da_margem_aas_2022": c["erro_diferenca_fora_da_margem_aas"],
                "erro_2026_lula_menos_flavio": e26,
                "fora_da_margem_aas_2026": x["erro_diferenca_fora_da_margem_aas"],
                "dentro_da_margem_nas_duas": not c["erro_diferenca_fora_da_margem_aas"]
                and not x["erro_diferenca_fora_da_margem_aas"],
                "mesmo_sinal": (c["diferenca_lula_menos_bolsonaro"]["erro"] > 0)
                == (e26 > 0),
            }
        )
    base = [r for r in linhas if r["na_media_2022"]]
    return {
        "regra": (
            "casas com onda final arquivada nas duas eleições; 2022 de "
            "analysis/predicao_2026/erro_2022/erro_2022.json, 2026 da última onda"
        ),
        "linhas": linhas,
        "n_casas": len(base),
        "correlacao_erros": statistics.correlation(
            [r["erro_2022_lula_menos_bolsonaro"] for r in base],
            [r["erro_2026_lula_menos_flavio"] for r in base],
        ),
        "superestimaram_lula_nas_duas": [
            r["casa_2026"]
            for r in base
            if r["erro_2022_lula_menos_bolsonaro"] > 0
            and r["erro_2026_lula_menos_flavio"] > 0
        ],
        "subestimaram_lula_nas_duas": [
            r["casa_2026"]
            for r in base
            if r["erro_2022_lula_menos_bolsonaro"] < 0
            and r["erro_2026_lula_menos_flavio"] < 0
        ],
        "dentro_da_margem_nas_duas": [
            r["casa_2026"] for r in base if r["dentro_da_margem_nas_duas"]
        ],
        "mesmo_sinal_nas_duas": sum(r["mesmo_sinal"] for r in base),
    }


# ---------------------------------------------------------------- previsão da casa


# ---------------------------------------------------------------- voto útil


# ---------------------------------------------------------------- principal


def main() -> None:
    final = ler(FINAL)
    agg, prev, vu = ler(AGREGADOR), ler(PREVISAO), ler(VOTO_UTIL)
    erro22 = ler(ERRO_2022)
    db = Banco(BANCO)
    urna = urna_presidente(db, final)
    linhas = carregar_pesquisas(agg, prev, urna)
    finais = [x for x in linhas if x["ultima_onda_da_casa"]]
    cobertura = agg["agregador"]["ultimo"]["1t"]["cobertura_movel"]["ondas"]
    agreg = [x for x in linhas if x["id"] in cobertura]
    if len(agreg) != len(cobertura):
        raise SystemExit("Ondas do agregador fora do conjunto de pesquisas")
    for qual, chave in (("publicado", "publicado"), ("reponderado", "ajustado")):
        esperado = agg["agregador"]["ultimo"]["1t"]["kernel"][chave]
        for k in ("lula", "flavio"):
            m = statistics.fmean(float(x[qual]["total"][k]) for x in agreg)
            if abs(m - esperado[k]) > 0.01:
                raise SystemExit(
                    f"Média do agregador ({qual}, {k}) não reproduz o JSON"
                )
    medias = {
        "ultimas_ondas_publicado": linha_media(
            "Última onda de cada casa, publicada",
            "13 casas com campo encerrado de 25/09 a 03/10, peso igual",
            finais,
            "publicado",
            urna,
        ),
        "agregador_publicado": linha_media(
            "Agregador Arvor de 04/10, publicado",
            "ondas da média móvel de 7 dias de 04/10, peso igual",
            agreg,
            "publicado",
            urna,
        ),
        "agregador_reponderado": linha_media(
            "Agregador Arvor de 04/10, reponderado por renda",
            "mesmas ondas, renda trocada pela PNAD (pessoas 16+, VD5001)",
            agreg,
            "reponderado",
            urna,
        ),
    }
    for m in medias.values():
        m["n_institutos"] = len(
            {x["instituto"] for x in linhas if x["id"] in m["ondas"]}
        )
    ranking = P.ordenar_por_erro(
        linhas, lambda x: x["publicado"]["diferenca_lula_menos_flavio"]["erro"]
    )
    ranking_rep = P.ordenar_por_erro(
        [x for x in linhas if x["reponderado"]],
        lambda x: x["reponderado"]["diferenca_lula_menos_flavio"]["erro"],
    )
    casa = {"fonte": fonte(PREVISAO), **C.previsao_casa(prev, urna)}
    efeitos = [
        (
            x["efeito_casa_pre_eleicao_pp"],
            x["publicado"]["diferenca_lula_menos_flavio"]["erro"],
        )
        for x in finais
        if x["efeito_casa_pre_eleicao_pp"] is not None
    ]
    corr = (
        statistics.correlation([a for a, _ in efeitos], [b for _, b in efeitos])
        if len(efeitos) > 2
        else None
    )
    comum = statistics.fmean(b - a for a, b in efeitos)
    res_pub = resumo_casas(finais, "publicado")
    perto = P.prob_alguma_perto_de_zero(
        res_pub["media"], res_pub["desvio_padrao"], res_pub["n"], 0.5
    )
    m22 = erro22["media_das_casas"]
    por_modo = {}
    for modo in sorted({x["modo"] for x in finais}):
        es = [
            x["publicado"]["diferenca_lula_menos_flavio"]["erro"]
            for x in finais
            if x["modo"] == modo
        ]
        por_modo[modo] = {
            "n": len(es),
            "media": statistics.fmean(es),
            "casas": [x["instituto"] for x in finais if x["modo"] == modo],
        }
    painel = painel_2022_2026(erro22, finais)
    governador = E.governadores(db, ler(GOVERNADOR), ESTADUAL)
    senado = E.senado(db, ler(SENADO), ESTADUAL)
    saida = {
        "descricao": (
            "Pesquisas nacionais de 1º turno com campo encerrado a partir de 25/09/2026, médias, "
            "previsões da casa e previsões estaduais contra a urna. Erro = pesquisa menos urna em "
            "pontos dos votos válidos; na diferença Lula menos Flávio, positivo superestima Lula."
        ),
        "gerado_por": "scripts/apuracao-2026-pesquisas.py",
        "fontes": [
            fonte(p)
            for p in (
                FINAL,
                AGREGADOR,
                PREVISAO,
                GOVERNADOR,
                SENADO,
                VOTO_UTIL,
                ERRO_2022,
            )
        ],
        "urna": {
            "banco": rel(BANCO),
            "versao_nacional": urna["versao_nacional"],
            "corte_final_json": urna["corte_final_json"],
            "secoes": urna["secoes"],
            "secoes_total": urna["secoes_total"],
            "validos_votos": urna["validos_votos"],
            "diferenca_flavio_menos_lula_votos": urna["votos"]["flavio"]
            - urna["votos"]["lula"],
            "diferenca_pp_final_json": final["presidente"]["diferenca_pp"],
            "votos": urna["votos"],
            "validos": urna["validos"],
            "validos_sem_exterior": urna["validos_sem_exterior"],
            "candidaturas_eam": sorted(k for k, v in urna["validos"].items() if v >= 2),
            "ufs": {
                uf: {"validos": u["validos"], "versao": u["versao"]}
                for uf, u in urna["ufs"].items()
            },
        },
        "regra_validos": "candidaturas renormalizadas para 100; indecisos e branco/nulo fora; negativos da reponderação truncados em zero (scripts/predicao_2026/base.py::grouped)",
        "pesquisas": linhas,
        "ranking_publicado": [x["id"] for x in ranking],
        "ranking_reponderado": [x["id"] for x in ranking_rep],
        "medias": medias,
        "resumo_ultimas_ondas": {
            "publicado": res_pub,
            "reponderado": resumo_casas(
                [x for x in finais if x["reponderado"]], "reponderado"
            ),
            "por_modo_publicado": por_modo,
            "correlacao_efeito_casa_pre_eleicao_com_erro": corr,
            "n_correlacao": len(efeitos),
            "componente_comum_descontado_efeito_casa_pp": comum,
            "nota_efeito_casa": (
                "efeito de casa = desvio da diferença L−F de cada casa contra a mediana das casas "
                "pareadas por época, medido antes da urna (predicao_2026_1T_presidente.json, "
                "nacional.efeitos_casa); ordena as casas, mas por construção não mede o erro comum"
            ),
            "prob_alguma_casa_a_meio_ponto_por_acaso": perto,
            "nota_prob": (
                "probabilidade de ao menos uma de n casas errar a diferença por menos de 0,5 pp se os "
                "erros fossem normais com a média e o desvio observados; ilustração, não teste"
            ),
        },
        "efeito_reponderacao": efeito_reponderacao(linhas),
        "previsao_casa": casa,
        "referencia_2022": {
            "fonte": fonte(ERRO_2022),
            "erro_comum_diferenca_lula_menos_bolsonaro": m22[
                "erro_comum_diferenca_lula_menos_bolsonaro"
            ],
            "mediana": m22["mediana_dos_erros_diferenca_pp"],
            "desvio_entre_casas": m22["desvio_padrao_entre_casas_pp"][
                "diferenca_lula_menos_bolsonaro"
            ],
            "n_casas": m22["n_casas"],
            "casas_que_superestimaram_lula": m22[
                "casas_que_superestimaram_lula_menos_bolsonaro"
            ],
            "melhor": erro22["ranking"]["melhor_casa_2022"],
            "pior": erro22["ranking"]["pior_casa_2022"],
        },
        "painel_2022_2026": painel,
        "governador": governador,
        "senado": senado,
    }
    vu_saida = {
        "descricao": (
            "Voto útil medido contra a urna: terceira via nas pesquisas finais, reserva de 2º turno "
            "revelada no 1º e decomposição do erro. Estimativa sob hipóteses declaradas, não medição."
        ),
        "gerado_por": "scripts/apuracao-2026-pesquisas.py",
        "fontes": [fonte(p) for p in (FINAL, AGREGADOR, PREVISAO, VOTO_UTIL)],
        "urna_validos": urna["validos"],
        "terceira_via": V.terceira_via(linhas, urna, prev, agg),
        "terceiros_por_candidato": V.terceiros_por_candidato(linhas, urna),
        "reserva_nacional": V.reserva_nacional(linhas, urna, vu),
        "modelo_voto_util": {"fonte": fonte(VOTO_UTIL), **V.modelo_voto_util(vu, urna)},
        "reserva_ufs": V.reserva_ufs(vu, urna, prev),
        "decomposicao": V.decomposicao(
            medias, prev["central"]["brasil"], prev["central"]["ufs"], linhas, urna, vu
        ),
        "matriz_transferencia": vu["nacional"]["transferencia"],
    }
    DADOS.mkdir(parents=True, exist_ok=True)
    saida, vu_saida = arredondar(saida), arredondar(vu_saida)
    (DADOS / "pesquisas_vs_urna.json").write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (DADOS / "voto_util.json").write_text(
        json.dumps(vu_saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (DADOS / "pesquisas.md").write_text(
        MEMO.memorando(saida, vu_saida), encoding="utf-8"
    )
    print(f"gravado: {rel(DADOS)}/pesquisas_vs_urna.json, voto_util.json, pesquisas.md")


if __name__ == "__main__":
    main()
