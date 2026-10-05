"""Câmara, Senado, assembleias e governadores a partir de `final.json` e do banco.

`apuracao/data/boletins/final.json` é a avaliação final do telão (regerada com
`cd apuracao && bun run scripts/final-2026.ts`). Aqui ela é reorganizada e
completada com o que o boletim não guarda: bancada por partido em cada UF, votos
por partido na Câmara e os 30 deputados federais mais votados do país.
"""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

from .banco import Banco
from .contexto import ELE_EST, FINAL_JSON, SENADORES_2022
from .dados import bloco_de, brt, campo_de, pct, versoes_genuinas

CARGOS = {3: "governador", 5: "senador", 6: "deputado_federal", 7: "deputado_estadual"}


def ler_final() -> dict[str, Any]:
    return json.loads(FINAL_JSON.read_text(encoding="utf-8"))


def _vigentes_uf(banco: Banco, cargo: int) -> dict[str, dict[str, Any]]:
    """Versão vigente (última gerada) e a da regra do coletor de cada arquivo de UF."""
    arqs = banco.arquivos(
        "tipo = 'u' AND eleicao_cd = ? AND cargo_cd = ? AND nivel = 'uf'",
        (ELE_EST, cargo),
    )
    snaps = banco.snapshots([a["id"] for a in arqs])
    saida = {}
    for a in arqs:
        lista = snaps.get(a["id"], [])
        versoes = versoes_genuinas(lista)
        if not versoes:
            continue
        coletor = max((s for s in lista if not s["regressivo"]), key=lambda s: s["id"])
        saida[a["uf"]] = {"vigente": versoes[-1], "coletor": coletor}
    return saida


def conferencia_versoes(banco: Banco) -> list[dict[str, Any]]:
    """Arquivos de UF em que a versão do boletim não é a última gerada pelo TSE."""
    saida = []
    for cargo, nome in CARGOS.items():
        for uf, par in sorted(_vigentes_uf(banco, cargo).items()):
            vig, col = par["vigente"], par["coletor"]
            if vig["id"] != col["id"]:
                banco.completar_totais(vig)
                saida.append(
                    {
                        "cargo": nome,
                        "uf": uf.upper(),
                        "secoes_no_boletim": col["st"],
                        "secoes_na_ultima_versao": vig["st"],
                        "secoes_total": vig["ts"],
                        "ultima_versao_gerada_brt": brt(vig["gerado_em"]),
                    }
                )
    banco.esquecer_documentos()
    return saida


def camara(
    banco: Banco, final: dict[str, Any], campos: dict[str, dict[str, str]]
) -> dict:
    cam = final["camara"]
    vigentes = _vigentes_uf(banco, 6)
    nacional_partido: Counter = Counter()
    campo_partido: dict[str, str] = {}
    candidatos: list[dict[str, Any]] = []
    eleitos_por_uf = {
        u["uf"]: {(e["nome"], e["votos"]) for e in u["eleitos"]} for u in cam["ufs"]
    }
    ufs = []
    for u in cam["ufs"]:
        uf = u["uf"].lower()
        snap = vigentes[uf]["vigente"]
        partidos = banco.partidos(snap["id"])
        if not partidos:
            raise RuntimeError(
                f"Câmara {uf}: versão {snap['id']} sem votos por partido"
            )
        votos_partido: Counter = Counter()
        for p in partidos:
            sigla = p["sigla"] or str(p["partido_n"])
            votos_partido[sigla] += (p["tvtn"] or 0) + (p["tvtl"] or 0)
            campo_partido[sigla] = campo_de(campos, None, sigla)
        nacional_partido.update(votos_partido)
        total = sum(votos_partido.values())
        for c in banco.candidaturas(snap["id"]):
            candidatos.append({**c, "uf": uf.upper()})
        bancada = Counter(e["partido"] for e in u["eleitos"])
        ufs.append(
            {
                "uf": u["uf"],
                "fonte": u["fonte"],
                "vagas": u["vagas"],
                "secoes": snap["st"],
                "por_campo": u["por_campo"],
                "por_bloco": _blocos(u["por_campo"]),
                "por_partido": dict(bancada.most_common()),
                "votos_por_partido": [
                    {
                        "partido": sigla,
                        "campo": campo_partido[sigla],
                        "votos": v,
                        "pct": pct(v, total, 4),
                    }
                    for sigla, v in votos_partido.most_common()
                ],
                "eleitos": u["eleitos"],
            }
        )
    total_nacional = sum(nacional_partido.values())
    candidatos.sort(key=lambda c: -(c["vap"] or 0))
    top = []
    for c in candidatos[:30]:
        sq = str(c["sqcand"])
        top.append(
            {
                "uf": c["uf"],
                "nome": c["nome_urna"],
                "partido": c["partido"],
                "campo": campo_de(campos, sq, c["partido"], c["federacao"]),
                "votos": c["vap"],
                "pct_na_uf": round(c["pvapn"], 4) if c["pvapn"] is not None else None,
                "eleito": (c["nome_urna"], c["vap"]) in eleitos_por_uf[c["uf"]],
                "situacao_tse": c["st"],
            }
        )
    return {
        "fonte": "apuracao/data/boletins/final.json (camara) e apuracao.sqlite (voto_partido)",
        **{k: cam[k] for k in cam if k != "ufs"},
        "votos_por_partido": [
            {
                "partido": sigla,
                "campo": campo_partido[sigla],
                "votos": v,
                "pct": pct(v, total_nacional, 4),
            }
            for sigla, v in nacional_partido.most_common()
        ],
        "deputados_mais_votados": top,
        "ufs": ufs,
    }


def _blocos(por_campo: dict[str, int]) -> dict[str, int]:
    saida: Counter = Counter()
    for campo, n in por_campo.items():
        saida[bloco_de(campo)] += n
    return dict(saida)


def senado(final: dict[str, Any]) -> dict[str, Any]:
    sen = final["senado"]
    eleitos = []
    for u in sen["ufs"]:
        for posicao, e in enumerate(u["eleitos"], start=1):
            eleitos.append({"uf": u["uf"], "vaga": posicao, "fonte": u["fonte"], **e})
    continuam = json.loads(SENADORES_2022.read_text(encoding="utf-8"))
    return {
        "fonte": "apuracao/data/boletins/final.json (senado) e apuracao/public/senadores_2022.json",
        "n_ufs_tse": sen["n_ufs_tse"],
        "n_ufs_provisorio": sen["n_ufs_provisorio"],
        "eleitos_2026": eleitos,
        "eleitos_2026_por_partido": dict(
            Counter(e["partido"] for e in eleitos).most_common()
        ),
        "eleitos_2026_por_campo": dict(
            Counter(e["campo"] for e in eleitos).most_common()
        ),
        "disputas": [
            {
                "uf": u["uf"],
                "fonte": u["fonte"],
                "terceiro": u["terceiro"],
                "margem_2a_vaga_pp": u["margem_2a_vaga_pp"],
                "margem_2a_vaga_votos": u["margem_2a_vaga_votos"],
            }
            for u in sen["ufs"]
        ],
        "continuam_eleitos_2022": continuam,
        "senado_2027": sen["senado_2027"],
        "comparacao_2023": sen["comparacao_2023"],
    }


def governadores(final: dict[str, Any]) -> dict[str, Any]:
    gov = final["governadores"]
    fatos = final["fatos"]
    return {
        "fonte": "apuracao/data/boletins/final.json (governadores e fatos)",
        **{k: gov[k] for k in gov if k != "ufs"},
        "ufs": gov["ufs"],
        "vao_estadual": fatos["vao_estadual"],
        "governador_x_presidente": fatos["governador_x_presidente"],
        "mais_perto_de_50": fatos["governadores_mais_perto_de_50"],
        "vaga_2t_mais_apertada": fatos["governadores_vaga_2t_mais_apertada"],
        "rotulo_obrigatorio_vao": "teto endereçável, nunca transferência certa",
    }


def assembleias(final: dict[str, Any]) -> dict[str, Any]:
    return {
        "fonte": "apuracao/data/boletins/final.json (assembleias)",
        "casas": final["assembleias"],
    }
