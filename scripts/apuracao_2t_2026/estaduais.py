"""As seis disputas estaduais de 2º turno (AC, AM, DF, ES, RN, TO)."""

from __future__ import annotations

from typing import Any

from apuracao_2026.vao_governadores import ROTULO_TETO, declaracao

from .base import (
    ELE_GOV,
    NOME_UF,
    ROTULO,
    brt,
    d2,
    minuto,
    p2,
    r2,
    totalizado_corrigido,
)
from .carga import Contexto
from .fontes import governadores_1t

ORDEM = ("AC", "AM", "DF", "ES", "RN", "TO")


def governadores(ctx: Contexto, ufs_pres: list[dict[str, Any]]) -> dict[str, Any]:
    banco = ctx.banco
    cands = banco.candidatos(ELE_GOV)
    g1 = governadores_1t()
    pres = {u["uf"]: u for u in ufs_pres}
    arq = {a["id"]: a["uf"].upper() for a in banco.arquivos(ELE_GOV, "uf")}
    versoes = banco.versoes(ELE_GOV, "uf")
    vig = {r["uf"].upper(): r for r in ctx.gov}
    ref_gov = ctx.ref.get("governador_1t", {})
    saida = []
    for uf in ORDEM:
        r = vig[uf]
        lista = [c for c in cands if (c["uf"] or "").upper() == uf]
        campos_1t = {c["nome"]: c for c in g1[uf]["candidatos"]}
        vv = r["vv"] or 0
        comp, abst = r["comparecimento"] or 0, r["abstencao"] or 0
        cand_saida = []
        for c in lista:
            sq = str(c["sqcand"])
            votos = r["votos"].get(sq, 0)
            c1 = campos_1t.get(c["nome_urna"], {})
            campo = c1.get("campo")
            dec = declaracao(uf, c["nome_urna"], campo) if campo else None
            p = pres[uf]
            lado = dec["finalista"] if dec else None
            pct_pres = (
                p["pct_flavio"]
                if lado == "flavio"
                else p["pct_lula"] if lado == "lula" else None
            )
            votos_pres = (
                p["flavio"]
                if lado == "flavio"
                else p["lula"] if lado == "lula" else None
            )
            cand_saida.append(
                {
                    "sqcand": sq,
                    "numero": c["numero"],
                    "nome_urna": c["nome_urna"],
                    "partido": c["partido"],
                    "campo": campo,
                    "votos": votos,
                    "pct": p2(votos, vv),
                    "t1_votos": c1.get("votos"),
                    "t1_pct": c1.get("pct"),
                    "delta_votos": (
                        votos - c1["votos"] if c1.get("votos") is not None else None
                    ),
                    "delta_pct_pp": d2(p2(votos, vv), c1.get("pct")),
                    "finalista_comparado": lado,
                    "comparacao": dec["comparacao"] if dec else None,
                    "evidencia": dec["evidencia"] if dec else None,
                    "pct_presidencial_mesmo_lado": pct_pres,
                    "vao_pp": d2(p2(votos, vv), pct_pres),
                    "vao_votos": votos - votos_pres if votos_pres is not None else None,
                }
            )
        cand_saida.sort(key=lambda c: -c["votos"])
        lider = cand_saida[0] if cand_saida else None
        # viradas durante a noite
        vs = next(v for k, v in versoes.items() if arq[k] == uf)
        viradas = []
        anterior = None
        serie = []
        for v in vs:
            if not v["st"]:
                continue
            ordem = sorted(v["votos"].items(), key=lambda kv: -kv[1])
            if not ordem:
                continue
            topo = ordem[0][0]
            a, b = [*ordem, ("", 0)][:2]
            serie.append(
                [
                    minuto(v["gerado_em"]),
                    r2(v["pst"]),
                    {k: p2(x, v["vv"]) for k, x in v["votos"].items()},
                ]
            )
            if anterior is not None and topo != anterior:
                viradas.append(
                    {
                        "min": minuto(v["gerado_em"]),
                        "gerado_brt": brt(v["gerado_em"]),
                        "pst": r2(v["pst"]),
                        "de": anterior,
                        "para": topo,
                        "margem_votos": a[1] - b[1],
                    }
                )
            anterior = topo
        nomes = {c["sqcand"]: c["nome_urna"] for c in cand_saida}
        for vi in viradas:
            vi["de_nome"] = nomes.get(vi["de"])
            vi["para_nome"] = nomes.get(vi["para"])
        fim = next((v for v in vs if v["ts"] and v["st"] == v["ts"]), None)
        rg = ref_gov.get(uf, {})
        p = pres[uf]
        saida.append(
            {
                "uf": uf,
                "nome": NOME_UF[uf],
                "secoes": r["st"],
                "secoes_total": r["ts"],
                "pst": r2(r["pst"]),
                "aptos": r["te"],
                "comparecimento": comp,
                "abstencao": abst,
                "validos": vv,
                "brancos": r["vb"],
                "nulos": r["tvn"],
                "pct_abstencao": p2(abst, comp + abst),
                "pct_brancos": p2(r["vb"], comp),
                "pct_nulos": p2(r["tvn"], comp),
                "presidente_pct_brancos": p["pct_brancos"],
                "presidente_pct_nulos": p["pct_nulos"],
                "brancos_nulos_gov_menos_pres_pp": d2(
                    p2((r["vb"] or 0) + (r["tvn"] or 0), comp),
                    p2(p["brancos"] + p["nulos"], p["comparecimento"]),
                ),
                "candidatos": cand_saida,
                "lider": lider["nome_urna"] if lider else None,
                "margem_pp": (
                    d2(cand_saida[0]["pct"], cand_saida[1]["pct"])
                    if len(cand_saida) > 1
                    else None
                ),
                "margem_votos": (
                    cand_saida[0]["votos"] - cand_saida[1]["votos"]
                    if len(cand_saida) > 1
                    else None
                ),
                "viradas": viradas,
                "n_viradas": len(viradas),
                "fechou_min": minuto(fim["gerado_em"]) if fim else None,
                "fechou_brt": brt(fim["gerado_em"]) if fim else None,
                "gerado_brt": brt(r["gerado_em"]),
                "totalizado_corrigido_brt": brt(
                    totalizado_corrigido(uf, r["totalizado_em"], r["gerado_em"])
                ),
                "t1_decisao": g1[uf]["decisao"],
                "t1_terceiro": g1[uf].get("terceiro"),
                "t1_pa_final": (rg.get("final") or {}).get("pa"),
                "t1_fechou_p100_min": (rg.get("marcos") or {}).get("p100"),
                "serie": serie,
            }
        )
    return {
        "rotulo": ROTULO,
        "rotulo_vao": ROTULO_TETO,
        "definicoes": {
            "pct": "sobre os válidos de governador do próprio turno",
            "vao_pp": (
                "candidatura ao governo menos o finalista presidencial do mesmo lado na "
                "mesma UF, ambos no 2º turno; lado pela regra do bloco ou pela tabela "
                "editorial de centro (scripts/apuracao_2026/vao_governadores.py)"
            ),
            "viradas": "troca de liderança entre versões genuínas consecutivas do arquivo de UF",
            "serie": "[min após 17:00, pst, {sqcand: % dos válidos}] por versão",
        },
        "ufs": saida,
    }
