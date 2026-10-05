"""Previsões de governador e Senado da casa contra a urna de 04/10/2026.

Recebe o leitor do banco da apuração (somente leitura) e os JSONs de previsão.
"Eleito" e "2º turno" vêm do texto ``st`` do TSE; quando o TSE ainda não marcou
a UF (totalização sem ``tf``), a situação é provisória pela regra da eleição
(maioria absoluta dos válidos para governador; duas mais votadas no Senado) e
fica marcada como ``provisorio``.
"""

from __future__ import annotations

import statistics

from . import pesquisas as P

FAIXAS = (0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0)


def resultado_uf(db, eleicao: int, cargo: int, uf: str) -> dict:
    s = db.snapshot(db.arquivo(eleicao, cargo, "uf", uf))
    cands = db.candidatos(s["id"])
    return {
        "versao": {k: s[k] for k in ("id", "gerado_em", "sha256", "tf", "pst")},
        "candidatos": cands,
        "tse": any(c["st"] for c in cands),
    }


def governadores(db, pred: dict, eleicao: int) -> dict:
    linhas, pares_decide, multi = [], [], []
    for uf, e in sorted(pred["estados"].items()):
        r = resultado_uf(db, eleicao, 3, uf)
        cands = r["candidatos"]
        lider, segundo = cands[0], cands[1]
        if r["tse"]:
            if lider["st"] not in ("Eleito", "2º turno"):
                raise SystemExit(f"{uf}: situação inesperada do líder: {lider['st']}")
            decidido = lider["st"] == "Eleito"
        else:
            decidido = lider["pct"] > 50
        prob = {int(p["sq_candidato"]): p for p in e["probabilidades"]}
        media = {int(m["sq_candidato"]): m for m in e["media"]}
        if int(lider["sqcand"]) not in prob:
            raise SystemExit(f"{uf}: líder da urna fora da previsão")
        pl = prob[int(lider["sqcand"])]
        prev_lider = max(e["media"], key=lambda m: m["validos"])
        nomes = {p["nome"]: int(p["sq_candidato"]) for p in e["probabilidades"]}
        par_prev = (
            max(e["pares_2t"], key=lambda x: x["p_par"]) if e["pares_2t"] else None
        )
        par_real = {int(lider["sqcand"]), int(segundo["sqcand"])}
        par_ok = (
            None
            if decidido or par_prev is None
            else {nomes[n] for n in par_prev["nomes"]} == par_real
        )
        p_par_real = None
        if not decidido:
            p_par_real = sum(
                x["p_par"]
                for x in e["pares_2t"]
                if {nomes[n] for n in x["nomes"]} == par_real
            )
        pares_decide.append((e["p_decide_1t"], int(decidido)))
        multi.append(
            sum(
                (prob.get(int(c["sqcand"]), {}).get("p_primeiro", 0.0) - (c is lider))
                ** 2
                for c in cands
            )
        )
        ic = pl["ic90_validos"]
        urna_prev = next(
            (c for c in cands if int(c["sqcand"]) == int(prev_lider["sq_candidato"])),
            None,
        )
        linhas.append(
            {
                "uf": uf,
                "fonte_situacao": "tse" if r["tse"] else "provisorio",
                "versao": r["versao"],
                "cobertura": e["cobertura"],
                "classe": e.get("classe"),
                "lider_urna": lider["nome"],
                "lider_partido": lider["partido"],
                "lider_pct_urna": lider["pct"],
                "segundo_urna": segundo["nome"],
                "segundo_pct_urna": segundo["pct"],
                "decidido_1t_urna": decidido,
                "p_decide_1t": e["p_decide_1t"],
                "favorito_previsto": e["favorito"],
                "p_favorito": e["p_favorito"],
                "lider_previsto_media": prev_lider["nome_urna"],
                "acertou_lider": int(prev_lider["sq_candidato"])
                == int(lider["sqcand"]),
                "p_primeiro_do_lider_urna": pl["p_primeiro"],
                "p_vence_1t_do_lider_urna": pl["p_vence_1t"],
                "validos_previsto_lider": media[int(lider["sqcand"])]["validos"],
                "erro_validos_lider_pp": media[int(lider["sqcand"])]["validos"]
                - lider["pct"],
                "ic90_validos_lider": ic,
                "erro_validos_lider_previsto_pp": (
                    prev_lider["validos"] - urna_prev["pct"] if urna_prev else None
                ),
                "lider_dentro_ic90": ic[0] <= lider["pct"] <= ic[1],
                "par_2t_previsto": par_prev["nomes"] if par_prev else None,
                "acertou_par_2t": par_ok,
                "p_par_2t_real": p_par_real,
            }
        )
    decide = [x for x in linhas if x["decidido_1t_urna"]]
    return {
        "regra": (
            "líder e situação pela urna (texto st do TSE; provisório pela maioria absoluta quando "
            "o TSE não marcou); previsão em docs/assets/predicao_governador.json"
        ),
        "linhas": sorted(linhas, key=lambda x: -abs(x["erro_validos_lider_pp"])),
        "resumo": {
            "n_ufs": len(linhas),
            "decididos_1t_urna": len(decide),
            "decididos_1t_esperado": pred["nacional"]["decididos_1t"]["esperado"],
            "decididos_1t_ic90": pred["nacional"]["decididos_1t"]["ic90"],
            "brier_decide_1t": P.brier(pares_decide),
            "brier_decide_1t_moeda": P.brier((0.5, o) for _, o in pares_decide),
            "brier_multiclasse_primeiro": statistics.fmean(multi),
            "acertos_lider": sum(x["acertou_lider"] for x in linhas),
            "erros_lider": [x["uf"] for x in linhas if not x["acertou_lider"]],
            "lider_dentro_ic90": sum(x["lider_dentro_ic90"] for x in linhas),
            "pares_2t_acertados": sum(bool(x["acertou_par_2t"]) for x in linhas),
            "ufs_2t": [x["uf"] for x in linhas if not x["decidido_1t_urna"]],
            "eam_validos_lider_pp": statistics.fmean(
                abs(x["erro_validos_lider_pp"]) for x in linhas
            ),
            "erro_medio_validos_lider_pp": statistics.fmean(
                x["erro_validos_lider_pp"] for x in linhas
            ),
            "erro_medio_validos_lider_previsto_pp": statistics.fmean(
                x["erro_validos_lider_previsto_pp"] for x in linhas
            ),
            "nota_selecao": (
                "o erro do líder da urna tem viés de seleção (quem liderou tende a ter superado a "
                "previsão); o erro do líder previsto não tem"
            ),
            "provisorios": [
                x["uf"] for x in linhas if x["fonte_situacao"] == "provisorio"
            ],
        },
    }


def senado(db, pred: dict, eleicao: int) -> dict:
    linhas, pares, base_media, base_uniforme = [], [], [], []
    esperado = 0.0
    for uf, e in sorted(pred["estados"].items()):
        r = resultado_uf(db, eleicao, 5, uf)
        cands = r["candidatos"]
        if r["tse"]:
            eleitos = {int(c["sqcand"]) for c in cands if c["st"] == "Eleito"}
        else:
            eleitos = {int(cands[0]["sqcand"]), int(cands[1]["sqcand"])}
        if len(eleitos) != 2:
            raise SystemExit(f"{uf}: Senado sem duas vagas definidas")
        prob = {int(p["sq_candidato"]): p for p in e["probabilidades"]}
        sq_urna = {int(c["sqcand"]) for c in cands}
        # Candidatura prevista que não aparece no arquivo da urna (registro
        # indeferido ou renúncia) entra no Brier como não eleita.
        fora = [p for sq, p in prob.items() if sq not in sq_urna]
        for p in fora:
            pares.append((p["p_eleito"], 0))
        ordem_media = sorted(e["media"], key=lambda m: -m["validos"])
        top_media = {int(m["sq_candidato"]) for m in ordem_media[:2]}
        k = len(cands)
        for c in cands:
            sq = int(c["sqcand"])
            o = int(sq in eleitos)
            pares.append((prob[sq]["p_eleito"] if sq in prob else 0.0, o))
            base_media.append((1.0 if sq in top_media else 0.0, o))
            base_uniforme.append((2 / k, o))
        top2 = sorted(e["probabilidades"], key=lambda p: -p["p_eleito"])[:2]
        acertos = len({int(p["sq_candidato"]) for p in top2} & eleitos)
        esperado += sum(p["p_eleito"] for p in top2)
        nomes = {p["nome"]: int(p["sq_candidato"]) for p in e["probabilidades"]}
        p_dupla = sum(
            d["p"] for d in e["duplas"] if {nomes.get(n) for n in d["nomes"]} == eleitos
        )
        el = [c for c in cands if int(c["sqcand"]) in eleitos]
        nao = [c for c in cands if int(c["sqcand"]) not in eleitos]
        linhas.append(
            {
                "uf": uf,
                "fonte_situacao": "tse" if r["tse"] else "provisorio",
                "versao": r["versao"],
                "cobertura": e["cobertura"],
                "eleitos": [
                    {
                        "nome": c["nome"],
                        "partido": c["partido"],
                        "pct": c["pct"],
                        "p_eleito": prob.get(int(c["sqcand"]), {}).get("p_eleito", 0.0),
                    }
                    for c in el
                ],
                "nao_eleito_mais_provavel": max(
                    (
                        {
                            "nome": c["nome"],
                            "pct": c["pct"],
                            "p_eleito": prob[int(c["sqcand"])]["p_eleito"],
                        }
                        for c in nao
                        if int(c["sqcand"]) in prob
                    ),
                    key=lambda x: x["p_eleito"],
                ),
                "top2_previsto": [p["nome_urna"] for p in top2],
                "acertos_top2": acertos,
                "dupla_mais_provavel": e["dupla_mais_provavel"],
                "p_dupla_mais_provavel": e["p_dupla_mais_provavel"],
                "p_dupla_eleita": p_dupla,
                "acertos_top2_media_sem_incerteza": len(top_media & eleitos),
                "previstas_fora_da_urna": [
                    {"nome": p["nome_urna"], "p_eleito": p["p_eleito"]} for p in fora
                ],
                "brier_uf": P.brier(
                    (
                        (
                            prob[int(c["sqcand"])]["p_eleito"]
                            if int(c["sqcand"]) in prob
                            else 0.0
                        ),
                        int(int(c["sqcand"]) in eleitos),
                    )
                    for c in cands
                ),
            }
        )
    surpresas = sorted(
        ({"uf": x["uf"], **c} for x in linhas for c in x["eleitos"]),
        key=lambda c: c["p_eleito"],
    )
    falsos = sorted(
        ({"uf": x["uf"], **x["nao_eleito_mais_provavel"]} for x in linhas),
        key=lambda c: -c["p_eleito"],
    )

    def por_cobertura(cob):
        sel = [x for x in linhas if x["cobertura"] == cob]
        return {
            "n_ufs": len(sel),
            "vagas": 2 * len(sel),
            "acertos_top2": sum(x["acertos_top2"] for x in sel),
            "brier_medio_uf": (
                statistics.fmean(x["brier_uf"] for x in sel) if sel else None
            ),
        }

    return {
        "regra": (
            "eleitos pelo texto st do TSE (duas vagas); provisório pelas duas mais votadas quando o "
            "TSE não marcou; candidatura da urna sem previsão entra com p = 0"
        ),
        "linhas": linhas,
        "resumo": {
            "n_ufs": len(linhas),
            "vagas": 2 * len(linhas),
            "n_candidaturas": len(pares),
            "brier": P.brier(pares),
            "brier_media_sem_incerteza": P.brier(base_media),
            "brier_uniforme_2_sobre_k": P.brier(base_uniforme),
            "acertos_top2": sum(x["acertos_top2"] for x in linhas),
            "acertos_top2_media_sem_incerteza": sum(
                x["acertos_top2_media_sem_incerteza"] for x in linhas
            ),
            "ufs_dupla_inteira": sum(x["acertos_top2"] == 2 for x in linhas),
            "acertos_top2_esperados": esperado,
            "por_cobertura": {c: por_cobertura(c) for c in ("recente", "antiga")},
            "eleitos_menos_provaveis": surpresas[:6],
            "nao_eleitos_mais_provaveis": falsos[:6],
            "calibracao": P.calibracao_por_faixa(pares, FAIXAS),
            "provisorios": [
                x["uf"] for x in linhas if x["fonte_situacao"] == "provisorio"
            ],
        },
    }
