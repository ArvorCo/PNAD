"""Resumo do Registro Digital do Voto (``rdv.json``) para o capítulo ``logs``.

``rdv.json`` é gerado por ``scripts/apuracao-2t-2026-rdv.py`` (ver
``analysis/apuracao_2t_2026/RDV.md``). Aqui só se destila o que a página usa:
cobertura, conferência com o BU, troca de campo nos nulos e os limites de Fréchet
presidente × governador por UF (os candidatos a governador entram pelo número e
pelo partido, de ``governadores.json``).
"""

from __future__ import annotations

import json

from .logs_base import DADOS

UFS = ("ac", "am", "df", "es", "rn", "to")


def _partidos() -> dict[tuple[str, str], str]:
    arq = DADOS / "governadores.json"
    if not arq.exists():
        return {}
    g = json.loads(arq.read_text(encoding="utf-8"))
    return {
        (u["uf"].lower(), str(c["numero"])): c.get("partido", "")
        for u in g.get("ufs", [])
        for c in u.get("candidatos", [])
    }


def resumo() -> dict | None:
    arq = DADOS / "rdv.json"
    if not arq.exists():
        return None
    d = json.loads(arq.read_text(encoding="utf-8"))
    tot = d["cobertura"]["total"]
    cb = d["conferencia_busa"]
    tc = d["troca_de_campo"]
    part = _partidos()
    ufs = []
    for uf in UFS:
        t = tc.get(uf)
        c = (d.get("cruzado_limites") or {}).get(uf)
        if not t or not c:
            continue
        pres_gov = sum(t["presidente_com_numero_de_governador"].values())
        limites = [
            {
                "presidente": x["presidente"],
                "governador": x["governador"],
                "partido": part.get((uf, x["governador"]), ""),
                "min_pct": x["min_pct"],
                "max_pct": x["max_pct"],
                "independencia_pct": x.get("independencia_pct"),
            }
            for x in c["uf"]["celulas"]
            if x["presidente"] in d["presidente"]
            and x["governador"] not in ("branco", "nulo", "transito")
        ]
        ufs.append(
            {
                "uf": uf.upper(),
                "secoes": c["uf"]["secoes"],
                "votantes": c["uf"]["n"],
                "nulos_governador": t["nulos_governador"],
                "governador_com_13": t["governador_com_13"],
                "governador_com_22": t["governador_com_22"],
                "governador_com_finalista_pct": t[
                    "governador_com_numero_de_presidente_pct"
                ],
                "nulos_presidente": t["nulos_presidente"],
                "presidente_com_governador": pres_gov,
                "presidente_com_governador_pct": (
                    round(100 * pres_gov / t["nulos_presidente"], 3)
                    if t["nulos_presidente"]
                    else None
                ),
                "presidente_com_governador_numeros": t[
                    "presidente_com_numero_de_governador"
                ],
                "numero_compartilhado": t["numero_compartilhado"],
                "transito": c["uf"]["governador"].get("transito", 0),
                "limites": limites,
            }
        )
    return {
        "fonte": "analysis/apuracao_2t_2026/dados/rdv.json",
        "gerado_em": d["meta"]["gerado_em"],
        "parcial": d["meta"]["parcial"],
        "tentadas": tot["secoes_cs"],
        "com_rdv": tot["ok"],
        "sem_aux": tot["aux_404"],
        "aux_sem_rdv": tot.get("sem_rdv", 0),
        "conferem": tot["confere"],
        "divergencias": len(d["divergencias_bu"]),
        "listas_fora_de_ordem": tot["listas_fora_de_ordem"],
        "contra_busa": cb["conferidas_pelo_busa_com_votos"]
        + cb["conferidas_pelo_busa_sem_votos"],
        "busa_sem_votos": cb["conferidas_pelo_busa_sem_votos"],
        "seis_ufs": tc["seis_ufs"],
        "ufs": ufs,
        "formato": d["formato"],
        "rotulo": d["rotulo"],
    }
