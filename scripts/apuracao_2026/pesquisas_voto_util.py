"""Voto útil contra a urna: terceira via, reserva de 2º turno e decomposição do erro.

Estimativa sob hipóteses declaradas, não medição de eleitor. A contabilidade da
reserva é a de ``scripts/voto_util_modelo.py``, importada para que o mapa do
voto útil publicado e esta conferência usem a mesma aritmética.
"""

from __future__ import annotations

import math
import statistics

import voto_util_modelo as VU

from . import pesquisas as P
from . import pesquisas_casa as C

MATRIZ_CHAVES = {
    "cury": "Cury",
    "caiado": "Caiado",
    "renan_santos": "Renan",
    "zema": "Zema",
}


CASAS_VU = ("quaest", "realtime", "atlas")


def terceira_via(linhas: list[dict], urna: dict, prev: dict, agg: dict) -> dict:
    finais = [x for x in linhas if x["ultima_onda_da_casa"]]
    alvo = P.blocos(urna["validos"])["terceira_via"]
    por = []
    for x in finais:
        por.append(
            {
                "id": x["id"],
                "instituto": x["instituto"],
                "publicado_validos": P.blocos(x["publicado"]["validos"])[
                    "terceira_via"
                ],
                "reponderado_validos": (
                    P.blocos(x["reponderado"]["validos"])["terceira_via"]
                    if x["reponderado"]
                    else None
                ),
                "nao_escolha_pct_total": x["publicado"]["auditoria"][
                    "nao_escolha_pct_total"
                ],
            }
        )
    com_rep = [r for r in por if r["reponderado_validos"] is not None]
    serie = []
    s = agg["agregador"]["serie"]
    for i, d in enumerate(s["datas"]):
        if d < "2026-08-15":
            continue
        ponto = {"data": d}
        for qual in ("publicado", "ajustado"):
            g = s["1t"][qual]
            vals = [
                g[k][i]
                for k in (
                    "lula",
                    "flavio",
                    "outros_centro_direita",
                    "outros_esquerda_nanicos",
                )
            ]
            if any(v is None for v in vals):
                ponto[qual] = None
                continue
            ponto[qual] = 100 * (vals[2] + vals[3]) / sum(vals)
        serie.append(ponto)
    return {
        "urna_validos": alvo,
        "por_onda": sorted(por, key=lambda r: r["publicado_validos"]),
        "media_publicado_todas": statistics.fmean(r["publicado_validos"] for r in por),
        "n_publicado_todas": len(por),
        "media_publicado_reponderaveis": statistics.fmean(
            r["publicado_validos"] for r in com_rep
        ),
        "media_reponderado": statistics.fmean(
            r["reponderado_validos"] for r in com_rep
        ),
        "n_reponderaveis": len(com_rep),
        "ondas_abaixo_da_urna": [
            r["id"] for r in por if r["publicado_validos"] <= alvo
        ],
        "central_casa": C.pct_validos(prev["central"]["brasil"])["terceira_via"],
        "central_casa_p05": prev["incerteza"]["candidatos"]["outros"]["percentual"][
            "p05"
        ],
        "serie_agregador_7d_validos": serie,
        "nota_serie": "terceira via em parcela dos válidos da média móvel de 7 dias do agregador (docs/assets/reponderacao_pnad.json, agregador.serie)",
    }


def terceiros_por_candidato(linhas: list[dict], urna: dict) -> dict:
    finais = [x for x in linhas if x["ultima_onda_da_casa"]]
    alvo = P.vetor_terceiros(urna["validos"])
    out = {"urna_validos": alvo}
    for qual in ("publicado", "reponderado"):
        vets = [P.vetor_terceiros(x[qual]["validos"]) for x in finais if x[qual]]
        vets = [v for v in vets if v is not None]
        media = P.media_vetores(vets)
        queda = {k: media[k] - alvo[k] for k in (*P.TERCEIROS, P.DEMAIS)}
        total = sum(queda.values())
        out[qual] = {
            "n_ondas": len(vets),
            "media_validos": media,
            "queda_pp": queda,
            "queda_relativa": {k: queda[k] / media[k] for k in queda if media[k] > 0},
            "fatia_da_queda": (
                {k: v / total for k, v in queda.items()} if total else None
            ),
        }
    return out


def reserva_nacional(linhas: list[dict], urna: dict, vu: dict) -> dict:
    transf = vu["nacional"]["transferencia"]
    alvo = urna["validos"]
    por = []
    for x in linhas:
        if not x["ultima_onda_da_casa"] or not x["segundo_turno_publicado"]:
            continue
        pub = x["publicado"]["total"]
        t2 = x["segundo_turno_publicado"]
        f1, l1 = float(pub["flavio"]), float(pub["lula"])
        nao = {k: max(0.0, float(pub.get(k, 0))) for k in ("indecisos", "branco_nulo")}
        t1 = sum(
            max(0.0, float(v))
            for k, v in pub.items()
            if k not in P.NAO_ESCOLHA and k not in ("flavio", "lula")
        )
        grupos = {"T": t1, "I": nao["indecisos"], "B": nao["branco_nulo"]}
        ftf, ftl = P.fracao_terceira(transf, grupos)
        entrada = {
            "F": f1,
            "L": l1,
            "T": t1,
            "F2": float(t2["flavio"]),
            "L2": float(t2["lula"]),
            "fT_flavio": ftf,
            "fT_lula": ftl,
        }
        sol = P.resolver_reserva(entrada, alvo["flavio"], alvo["lula"])
        vp = x["publicado"]["validos"]
        por.append(
            {
                "id": x["id"],
                "instituto": x["instituto"],
                "entrada": entrada,
                "ganho_validos_flavio_pp": alvo["flavio"] - vp["flavio"],
                "ganho_validos_lula_pp": alvo["lula"] - vp["lula"],
                **sol,
            }
        )
    lam = [r["lambda_flavio"] for r in por if r["lambda_flavio"] is not None]
    the = [r["theta_lula"] for r in por if r["theta_lula"] is not None]
    return {
        "regra": (
            "reserva = 2º turno menos 1º turno do mesmo finalista na mesma pesquisa, em pontos dos "
            "entrevistados; λ e θ = fração dessa reserva que a urna revelou no 1º turno, pela "
            "contabilidade de scripts/voto_util_modelo.py (parte da reserva sai da terceira via, "
            "o resto de indecisos e branco/nulo, pela regra fracao_terceira)"
        ),
        "por_onda": por,
        "lambda_flavio": {
            "mediana": statistics.median(lam),
            "media": statistics.fmean(lam),
            "min": min(lam),
            "max": max(lam),
            "n": len(lam),
        },
        "theta_lula": {
            "mediana": statistics.median(the),
            "media": statistics.fmean(the),
            "min": min(the),
            "max": max(the),
            "n": len(the),
        },
        "reserva_media_flavio_pp": statistics.fmean(
            r["reserva_flavio_pp"] for r in por
        ),
        "reserva_media_lula_pp": statistics.fmean(r["reserva_lula_pp"] for r in por),
        "ganho_medio_validos_flavio_pp": statistics.fmean(
            r["ganho_validos_flavio_pp"] for r in por
        ),
        "ganho_medio_validos_lula_pp": statistics.fmean(
            r["ganho_validos_lula_pp"] for r in por
        ),
    }


def estados_vu(vu: dict, casa: str) -> list:
    lista = []
    for uf, r in sorted(vu["modelos"][casa]["entradas"].items()):
        t = vu["tse_uf"][uf]
        peso = t["eleitorado_2026"] * t["comparecimento_1t_pct"] / 100
        v = r["lv"]
        lista.append(
            VU.Estado(
                uf,
                peso,
                v["F"],
                v["L"],
                v["T"],
                v["I"],
                v["B"],
                v["F2"],
                v["L2"],
                int(r["n"]),
                r["fT_flavio"],
                r["fT_lula"],
                r["medido_2t"],
            )
        )
    return lista


def modelo_voto_util(vu: dict, urna: dict) -> dict:
    """Reconstrói o mapa do voto útil (26/09) e acha o λ, θ que reproduz a urna."""
    alvo = urna["validos_sem_exterior"]
    out = {}
    for variante, sufixo in (("calibrado", ""), ("bruto", "_bruto")):
        listas = {c: estados_vu(vu, f"{c}{sufixo}") for c in CASAS_VU}

        def media(lam, theta, listas=listas):
            rs = [VU.agrega(lst, lam, theta) for lst in listas.values()]
            return (
                statistics.fmean(r["flavio_validos"] for r in rs),
                statistics.fmean(r["lula_validos"] for r in rs),
            )

        curva = vu["modelos"][f"media{sufixo}"]["curvas"]
        for lam_ref in (0.0, 1.0):
            ponto = next(p for p in curva["so_direita"] if p["lam"] == lam_ref)
            f, lu = media(lam_ref, 0.0)
            if (
                abs(f - ponto["flavio_validos"]) > 0.002
                or abs(lu - ponto["lula_validos"]) > 0.002
            ):
                raise SystemExit(
                    f"Reconstrução do voto útil ({variante}) não bate com a curva"
                )
        lam, theta = P.resolver_2d(media, (alvo["flavio"], alvo["lula"]))
        cen = []
        for c in vu["modelos"][f"media{sufixo}"]["cenarios"]:
            cen.append(
                {
                    "nome": c["nome"],
                    "lam": c["lam"],
                    "theta": c["theta"],
                    "flavio_validos": c["flavio_validos"],
                    "lula_validos": c["lula_validos"],
                    "terceira_via_validos": c["outros_validos"],
                    "erro_diferenca_lula_menos_flavio": (
                        c["lula_validos"] - c["flavio_validos"]
                    )
                    - (alvo["lula"] - alvo["flavio"]),
                    "distancia_pp": math.hypot(
                        c["flavio_validos"] - alvo["flavio"],
                        c["lula_validos"] - alvo["lula"],
                    ),
                }
            )
        cen.sort(key=lambda r: r["distancia_pp"])
        out[variante] = {
            "lambda_flavio": lam,
            "theta_lula": theta,
            "lambda_so_direita_para_flavio_da_urna": P.interpolar_curva(
                curva["so_direita"], "flavio_validos", alvo["flavio"]
            ),
            "lambda_dois_lados_para_margem_da_urna": P.interpolar_curva(
                curva["dois_lados"], "margem", alvo["flavio"] - alvo["lula"]
            ),
            "hoje_eleitor_provavel": media(0.0, 0.0),
            "cenarios_por_distancia": cen,
        }
    return {
        "gerado_em": vu["gerado_em"],
        "urna_sem_exterior": {k: alvo[k] for k in ("flavio", "lula")},
        **out,
    }


def reserva_ufs(vu: dict, urna: dict, prev: dict) -> list[dict]:
    central = {u["uf"]: u for u in prev["central"]["ufs"]}
    linhas = []
    for uf, r in sorted(vu["auxiliar"]["reserva_uf"].items()):
        uv = urna["ufs"][uf]["validos"]
        sols = []
        for c in r["casas"]:
            casa = c["casa"]
            if casa not in CASAS_VU:
                continue
            ent = vu["modelos"][f"{casa}_bruto"]["entradas"][uf]
            if (
                abs(ent["lv"]["F"] - c["F"]) > 0.01
                or abs(ent["lv"]["F2"] - c["F2"]) > 0.01
            ):
                raise SystemExit(
                    f"{uf} {casa}: reserva_uf não bate com as entradas brutas"
                )
            entrada = {
                **{k: ent["lv"][k] for k in ("F", "L", "T", "F2", "L2")},
                "fT_flavio": ent["fT_flavio"],
                "fT_lula": ent["fT_lula"],
            }
            sol = P.resolver_reserva(entrada, uv["flavio"], uv["lula"])
            v = ent["lv"]["F"] + ent["lv"]["L"] + ent["lv"]["T"]
            sols.append(
                {
                    "casa": casa,
                    "campo": ent.get("campo"),
                    "flavio_validos_pesquisa": 100 * ent["lv"]["F"] / v,
                    "lula_validos_pesquisa": 100 * ent["lv"]["L"] / v,
                    **sol,
                }
            )
        cu = central[uf]
        vc = C.pct_validos(cu)
        lam = [s["lambda_flavio"] for s in sols if s["lambda_flavio"] is not None]
        the = [s["theta_lula"] for s in sols if s["theta_lula"] is not None]
        linhas.append(
            {
                "uf": uf,
                "reserva_flavio_pp_media_casas": r["reserva_pp"],
                "reserva_flavio_eleitores": r["reserva_eleitores"],
                "flavio_validos_urna": uv["flavio"],
                "lula_validos_urna": uv["lula"],
                "ganho_flavio_sobre_pesquisa_pp": (
                    uv["flavio"]
                    - statistics.fmean(s["flavio_validos_pesquisa"] for s in sols)
                    if sols
                    else None
                ),
                "ganho_lula_sobre_pesquisa_pp": (
                    uv["lula"]
                    - statistics.fmean(s["lula_validos_pesquisa"] for s in sols)
                    if sols
                    else None
                ),
                "ganho_flavio_sobre_central_pp": uv["flavio"] - vc["flavio"],
                "ganho_lula_sobre_central_pp": uv["lula"] - vc["lula"],
                "lambda_flavio_media_casas": statistics.fmean(lam) if lam else None,
                "theta_lula_media_casas": statistics.fmean(the) if the else None,
                "casas": sols,
                "estimado": bool(r.get("estimado")),
            }
        )
    return linhas


def partilhas(vu: dict, variante: str, pesquisa: dict) -> dict:
    linhas = vu["nacional"]["transferencia"]["linhas"]
    out = {}
    for k, nome in MATRIZ_CHAVES.items():
        if variante == "proporcional":
            s = pesquisa["flavio"] / (pesquisa["flavio"] + pesquisa["lula"])
            out[k] = (s, 1 - s)
        elif variante == "nexus_com_vazamento":
            out[k] = P.partilha(
                linhas[nome], "com_vazamento", pesquisa["flavio"], pesquisa["lula"]
            )
        else:
            out[k] = P.partilha(linhas[nome], "renormalizada")
    if variante == "datafolha_caiado":
        t = vu["auxiliar"]["desistencias"]["taxas"]["caiado_datafolha"]
        out["caiado"] = P.partilha(
            {"Flávio": t["flavio"], "Lula": t["lula"]}, "renormalizada"
        )
    out[P.DEMAIS] = (0.5, 0.5)
    return out


VARIANTES = {
    "nexus_renormalizada": "principal: linhas da Nexus (p. 79) renormalizadas entre Flávio e Lula",
    "nexus_com_vazamento": "linhas da Nexus; a parte que iria a branco, nulo ou indeciso sai dos válidos",
    "datafolha_caiado": "como a principal, com a linha de Caiado do Datafolha (Flávio 42, Lula 27)",
    "proporcional": "sem matriz: cada ponto da terceira via vai a Flávio e Lula na proporção do placar",
}


def decomposicao(
    medias: dict,
    central: dict,
    prev_ufs: list[dict],
    linhas: list[dict],
    urna: dict,
    vu: dict,
) -> dict:
    alvo = P.vetor_terceiros(urna["validos"])
    alvos = {}
    for nome, m in medias.items():
        if m["validos_candidatos"]:
            alvos[nome] = m["validos_candidatos"]
    br = central
    dem = {k: 100 * v / br["validos"] for k, v in br["demais"].items()}
    vc = C.pct_validos(br)
    alvos["central_casa"] = {
        "flavio": vc["flavio"],
        "lula": vc["lula"],
        **{k: dem[k] for k in P.TERCEIROS},
        P.DEMAIS: dem["restantes"],
    }
    out = {
        "variantes": VARIANTES,
        "hipotese_demais": "candidaturas menores e 'outros' repartidas meio a meio (sem linha publicada)",
        "agregados": {},
        "por_onda": [],
    }
    for nome, vet in alvos.items():
        out["agregados"][nome] = {
            v: P.decompor_consolidacao(vet, alvo, partilhas(vu, v, vet))
            for v in VARIANTES
        }
    out["por_uf_central"] = []
    for u in prev_ufs:
        uv = P.vetor_terceiros(urna["ufs"][u["uf"]]["validos"])
        tot = u["lula"] + u["flavio"] + u["outros"]
        vet = {
            "flavio": 100 * u["flavio"] / tot,
            "lula": 100 * u["lula"] / tot,
            **{k: 100 * u["demais"][k] / tot for k in P.TERCEIROS},
            P.DEMAIS: 100 * u["demais"]["restantes"] / tot,
        }
        d = P.decompor_consolidacao(vet, uv, partilhas(vu, "nexus_renormalizada", vet))
        out["por_uf_central"].append({"uf": u["uf"], "regiao": u["regiao"], **d})
    for x in linhas:
        if not x["ultima_onda_da_casa"]:
            continue
        vet = P.vetor_terceiros(x["publicado"]["validos"])
        if vet is None:
            continue
        out["por_onda"].append(
            {
                "id": x["id"],
                "instituto": x["instituto"],
                **{
                    v: P.decompor_consolidacao(vet, alvo, partilhas(vu, v, vet))
                    for v in VARIANTES
                },
            }
        )
    return out
