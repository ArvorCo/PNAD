"""Projeção da casa relida ao longo da noite e totalização paralela por QR do BU."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from datetime import timedelta
from typing import Any

from .base import (
    API_LOCAL,
    ROTULO,
    ROTULO_PARALELA,
    ROTULO_PROJECAO,
    SERIE_PROJECAO,
    SQ_FLAVIO,
    SQ_LULA,
    T0,
    brt,
    hhmm,
    ler_json,
    minuto,
    p2,
    r2,
)
from .carga import Contexto

PASSO_MIN = 5
DE_MIN = 120  # 19:00
ATE_MIN = 330  # 22:30
MARCOS_MIN = (150, 180, 210, 240, 270, 300, 330)
CHAVES_COMPARECIMENTO = (
    "rotulo",
    "regras",
    "referencia",
    "totais",
    "sinais",
    "delta",
    "por_uf",
    "prorrogacao",
    "municipios_uf",
    "municipios_delta",
    "municipios_top",
)


def _api(rota: str, at_iso: str) -> dict[str, Any]:
    url = f"{API_LOCAL}{rota}?at={at_iso}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _iso(min_: float) -> str:
    return (T0 + timedelta(minutes=min_)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _bloco_proj(b: dict[str, Any]) -> dict[str, Any]:
    proj = b.get("projetado") or {}
    obs = b.get("observado") or {}
    return {
        "sigla": b.get("sigla"),
        "pst": b.get("pst"),
        "pct_vv_observado": b.get("pct_vv_observado"),
        "p_f_observado": obs.get("p_f"),
        "p_f_projetado": proj.get("p_f"),
        "p_l_projetado": proj.get("p_l"),
        "faixa90": proj.get("faixa90"),
        "swing_pp": b.get("swing_pp"),
    }


def projecao_noite(ctx: Contexto) -> dict[str, Any]:
    pontos = []
    erro = None
    regioes_fim: list[dict[str, Any]] = []
    ufs_fim: list[dict[str, Any]] = []
    parametros = None
    m = DE_MIN
    while m <= ATE_MIN:
        at = _iso(m)
        try:
            d = _api("/api/2t/projecao", at)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            erro = f"{type(e).__name__}: {e}"
            break
        parametros = d.get("parametros")
        b = _bloco_proj(d["brasil"])
        lider = None
        if b["p_f_projetado"] is not None:
            lider = "flavio" if b["p_f_projetado"] > 50 else "lula"
        pontos.append(
            {
                "min": m,
                "hhmm": hhmm(m),
                "at": at,
                **b,
                "lider_projetado": lider,
                "st": d["cobertura"]["st"],
                "municipios_observados": d["cobertura"]["municipios_observados"],
                "municipios_fechados": d["cobertura"]["municipios_fechados"],
                "motivo_sem_projecao": d.get("motivo_sem_projecao"),
            }
        )
        regioes_fim = [_bloco_proj(x) for x in d.get("regioes", [])]
        ufs_fim = [_bloco_proj(x) for x in d.get("ufs", [])]
        m += PASSO_MIN
    marcos = []
    for mm in MARCOS_MIN:
        if erro:
            break
        at = _iso(mm)
        try:
            ab = _api("/api/2t/abstencao", at)
            co = _api("/api/2t/comparecimento", at)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            erro = f"{type(e).__name__}: {e}"
            break
        marcos.append(
            {
                "min": mm,
                "hhmm": hhmm(mm),
                "abstencao": {
                    "brasil": ab.get("brasil"),
                    "regioes": ab.get("regioes"),
                },
                "comparecimento": {k: co.get(k) for k in CHAVES_COMPARECIMENTO},
            }
        )
    vv = ctx.br["vv"]
    f, l_ = ctx.br["votos"].get(SQ_FLAVIO, 0), ctx.br["votos"].get(SQ_LULA, 0)
    observado_final = {
        "p_f_entre_os_dois": p2(f, f + l_),
        "pct_flavio_validos": p2(f, vv),
        "pct_lula_validos": p2(l_, vv),
        "pst": r2(ctx.br["pst"]),
        "gerado_brt": brt(ctx.br["gerado_em"]),
    }
    com_proj = [p for p in pontos if p["p_f_projetado"] is not None]
    primeiro = com_proj[0] if com_proj else None
    erros = [
        abs(p["p_f_projetado"] - observado_final["p_f_entre_os_dois"]) for p in com_proj
    ]
    dentro = [
        p
        for p in com_proj
        if p["faixa90"]
        and p["faixa90"][0] <= observado_final["p_f_entre_os_dois"] <= p["faixa90"][1]
    ]
    alvo = observado_final["p_f_entre_os_dois"]
    fora = [
        {
            "hhmm": p["hhmm"],
            "pst": p["pst"],
            "faixa90": p["faixa90"],
            "distancia_pp": r2(
                min(abs(alvo - p["faixa90"][0]), abs(alvo - p["faixa90"][1]))
            ),
        }
        for p in com_proj
        if p not in dentro
    ]
    lider_obs = [
        p for p in pontos if p["p_f_observado"] is not None and p["p_f_observado"] > 50
    ]
    try:
        ao_vivo = ler_json(SERIE_PROJECAO).get("serie")
    except (OSError, ValueError):
        ao_vivo = None
    return {
        "rotulo": ROTULO_PROJECAO,
        "rotulo_dossie": ROTULO,
        "pontos_fora_da_faixa90": fora,
        "pontos_com_flavio_a_frente_no_observado": {
            "n": len(lider_obs),
            "de": lider_obs[0]["hhmm"] if lider_obs else None,
            "ate": lider_obs[-1]["hhmm"] if lider_obs else None,
            "maximo_p_f_observado": max(
                (p["p_f_observado"] for p in lider_obs), default=None
            ),
        },
        "metodo": (
            "rota /api/2t/projecao do servidor local relida com at= a cada "
            f"{PASSO_MIN} min de 19:00 a 22:30 de Brasília; o estado em cada instante "
            "é a última versão gerada até ele, então a série é reconstruída, não a "
            "que foi exibida ao vivo (essa vai em serie_ao_vivo)"
        ),
        "erro": erro,
        "parametros": parametros,
        "pontos": pontos,
        "observado_final": observado_final,
        "primeiro_ponto_com_projecao": primeiro,
        "lider_projetado_em_todos_os_pontos": sorted(
            {p["lider_projetado"] for p in com_proj}
        ),
        "erro_absoluto_pp": {
            "medio": r2(sum(erros) / len(erros)) if erros else None,
            "maximo": r2(max(erros)) if erros else None,
        },
        "pontos_com_final_dentro_da_faixa90": len(dentro),
        "pontos_com_projecao": len(com_proj),
        "regioes_ultimo_ponto": regioes_fim,
        "ufs_ultimo_ponto": ufs_fim,
        "marcos_abstencao_comparecimento": marcos,
        "serie_ao_vivo": {
            "fonte": "apuracao/data/projecao_2t_serie.json",
            "colunas": ["min", "p_f_proj", "faixa_a", "faixa_b", "p_f_obs", "pst"],
            "linhas": ao_vivo,
        },
    }


def paralela(ctx: Contexto) -> dict[str, Any]:
    banco = ctx.banco
    bus = banco.linhas(
        "SELECT b.*, c.situacao, c.diferencas_json, c.erro AS erro_conf, c.tse_arquivo, "
        "c.tse_recebido_iso, c.conferido_em FROM paralela_bu b "
        "LEFT JOIN paralela_conferencia c ON c.bu_id = b.id ORDER BY b.recebido_em"
    )
    ts_uf = {u["uf"].upper(): u["ts"] for u in ctx.ufs}
    votos = Counter()
    soma = Counter()
    gov: dict[str, Counter] = defaultdict(Counter)
    lista = []
    situacoes = Counter()
    por_uf: dict[str, int] = defaultdict(int)
    for b in bus:
        cargos = json.loads(b["cargos_json"])
        pres = next((c for c in cargos if c["cargo"] == 1), None)
        uf = b["uf"].upper()
        por_uf[uf] += 1
        situacoes[b["situacao"] or "pendente"] += 1
        linha = {
            "uf": uf,
            "mun": b["mun"],
            "zona": b["zona"],
            "secao": b["secao"],
            "recebido_brt": brt(b["recebido_em"]),
            "recebido_min": minuto(b["recebido_em"]),
            "fase": b["fase"],
            "aptos": b["aptos"],
            "comparecimento": b["comparecimento"],
            "situacao": b["situacao"],
            "conferido_brt": brt(b["conferido_em"]),
            "tse_recebido_brt": brt(b["tse_recebido_iso"]),
            "diferencas": (
                json.loads(b["diferencas_json"]) if b["diferencas_json"] else None
            ),
        }
        if pres:
            linha.update(
                {
                    "lula": pres["votos"].get("13", 0),
                    "flavio": pres["votos"].get("22", 0),
                    "brancos": pres["bran"],
                    "nulos": pres["nulo"],
                    "nominais": pres["nomi"],
                }
            )
            for k, v in pres["votos"].items():
                votos[k] += v
            soma.update(
                {
                    "aptos": b["aptos"] or 0,
                    "comparecimento": b["comparecimento"] or 0,
                    "brancos": pres["bran"],
                    "nulos": pres["nulo"],
                    "secoes": 1,
                }
            )
        for c in cargos:
            if c["cargo"] == 3:
                for k, v in c["votos"].items():
                    gov[uf][k] += v
                gov[uf]["secoes"] += 1
        lista.append(linha)
    nominais = votos["13"] + votos["22"]
    return {
        "rotulo": ROTULO_PARALELA,
        "rotulo_dossie": ROTULO,
        "limite": (
            "a amostra é de quem enviou; a conferência prova transmissão e "
            "totalização da seção, nunca o interior da urna"
        ),
        "recebidos": {
            "bus": len(bus),
            "secoes": len({(b["uf"], b["mun"], b["zona"], b["secao"]) for b in bus}),
            "ufs": len(por_uf),
        },
        "conferencia": dict(situacoes),
        "cobertura_uf": [
            {
                "uf": uf,
                "bus": n,
                "secoes_total": ts_uf.get(uf),
                "pct": p2(n, ts_uf.get(uf)),
            }
            for uf, n in sorted(por_uf.items(), key=lambda kv: -kv[1])
        ],
        "placar_bus": {
            "presidente": {
                "votos": dict(votos),
                "pct_lula_nominais": p2(votos["13"], nominais),
                "pct_flavio_nominais": p2(votos["22"], nominais),
                "pct_comparecimento": p2(soma["comparecimento"], soma["aptos"]),
                **dict(soma),
            },
            "governador": {uf: dict(c) for uf, c in gov.items()},
        },
        "bus": lista,
    }


def projecao_vazia() -> dict[str, Any]:
    """Sem o servidor local: só a série exibida ao vivo."""
    try:
        ao_vivo = ler_json(SERIE_PROJECAO).get("serie")
    except (OSError, ValueError):
        ao_vivo = None
    return {
        "rotulo": ROTULO_PROJECAO,
        "rotulo_dossie": ROTULO,
        "erro": "rodada sem o servidor local (--sem-api)",
        "pontos": [],
        "serie_ao_vivo": {
            "fonte": "apuracao/data/projecao_2t_serie.json",
            "colunas": ["min", "p_f_proj", "faixa_a", "faixa_b", "p_f_obs", "pst"],
            "linhas": ao_vivo,
        },
    }
