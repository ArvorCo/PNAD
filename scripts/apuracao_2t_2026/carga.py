"""Carga única do banco do 2º turno e das réguas, compartilhada pelos conjuntos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from . import fontes
from .base import ELE_GOV, ELE_PRES, Banco2T, minuto


@dataclass
class Contexto:
    banco: Banco2T
    br: dict[str, Any]
    ufs: list[dict[str, Any]]
    mus: list[dict[str, Any]]
    zonas: list[dict[str, Any]]
    meta_mun: dict[str, dict[str, Any]]
    fechou: dict[str, dict[str, Any]]
    fechou_zona: dict[tuple[str, int], dict[str, Any]]
    ref: dict[str, Any]
    mun_1t: dict[str, dict[str, Any]]
    ufs_1t: dict[str, dict[str, Any]]
    ext_1t: dict[str, dict[str, Any]]
    fechou_1t: dict[str, float | None]
    gov: list[dict[str, Any]] = field(default_factory=list)


def _fechamentos(
    versoes: dict[int, list[dict[str, Any]]], arquivos: dict[int, dict[str, Any]]
) -> dict[int, dict[str, Any]]:
    """Primeira versão genuína com todas as seções totalizadas de cada arquivo."""
    saida: dict[int, dict[str, Any]] = {}
    for arq_id, vs in versoes.items():
        for v in vs:
            if v["ts"] and v["st"] == v["ts"]:
                saida[arq_id] = {
                    "gerado_em": v["gerado_em"],
                    "min": minuto(v["gerado_em"]),
                    "totalizado_em": v["totalizado_em"],
                    "dt": v["dt"],
                    "ht": v["ht"],
                    "arquivo": arquivos[arq_id],
                }
                break
    return saida


def carregar() -> Contexto:
    banco = Banco2T()
    br = banco.vigentes(ELE_PRES, "br")[0]
    ufs = banco.vigentes(ELE_PRES, "uf")
    mus = banco.vigentes(ELE_PRES, "mu")
    zonas = banco.vigentes(ELE_PRES, "zona")
    arq_mu = {a["id"]: a for a in banco.arquivos(ELE_PRES, "mu")}
    arq_zona = {a["id"]: a for a in banco.arquivos(ELE_PRES, "zona")}
    f_mu = _fechamentos(banco.versoes(ELE_PRES, "mu", com_votos=False), arq_mu)
    f_zona = _fechamentos(banco.versoes(ELE_PRES, "zona", com_votos=False), arq_zona)
    fechou = {v["arquivo"]["municipio_cd"]: v for v in f_mu.values()}
    fechou_zona = {
        (v["arquivo"]["municipio_cd"], int(v["arquivo"]["zona_cd"])): v
        for v in f_zona.values()
    }
    ref = fontes.referencia_1t()
    return Contexto(
        banco=banco,
        br=br,
        ufs=ufs,
        mus=mus,
        zonas=zonas,
        meta_mun=banco.municipios(),
        fechou=fechou,
        fechou_zona=fechou_zona,
        ref=ref,
        mun_1t=fontes.municipios_1t(),
        ufs_1t=fontes.ufs_1t(),
        ext_1t=fontes.exterior_1t(),
        fechou_1t=fontes.fechou_1t(ref),
        gov=banco.vigentes(ELE_GOV, "uf"),
    )
