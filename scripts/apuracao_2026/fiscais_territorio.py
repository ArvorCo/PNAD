"""Risco e contexto do território por local de votação (capítulo 13, contrato 1.1).

Junta as camadas públicas preparadas por `scripts/apuracao-2026-fiscais-risco.py`
(setor do Censo 2022, terra indígena, quilombo, favela, unidade prisional,
homicídios, mapeamento público de crime organizado, fronteira e garimpo) aos
locais com seção sinalizada, calcula o acesso por estrada (OSRM, com cache) da sede
municipal e do aeródromo público mais próximo (ANAC) e aplica a regra declarada do
nível de risco fiscal. Onde a base não cobre, o campo fica `None`, nunca zero.

O nível de risco fiscal é juízo editorial por regra de pontos, não medição; vem
sempre com a frase "validar com a PM e o TRE local".
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import time
import urllib.request
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RISCO_LOCAIS = ROOT / "data/outputs/fiscais_risco_locais.csv.gz"
RISCO_MUNICIPIOS = ROOT / "data/outputs/fiscais_risco_municipios.csv"
RISCO_FONTES = ROOT / "analysis/apuracao_2026/dados/fiscais_risco_fontes.json"
ANAC = ROOT / "data/raw/anac/AerodromosPublicos.json"
ANAC_URL = (
    "https://sistemas.anac.gov.br/dadosabertos/Aerodromos/Aer%C3%B3dromos%20P%C3%BAblicos/"
    "Lista%20de%20aer%C3%B3dromos%20p%C3%BAblicos/AerodromosPublicos.json"
)
OSRM_URL = "https://router.project-osrm.org/table/v1/driving/"
OSRM_CACHE = ROOT / "data/outputs/fiscais_osrm_cache.json"
OSRM_LOTE = 90  # destinos por consulta (o servidor público aceita até 100 coordenadas)
OSRM_PAUSA_S = 1.1  # política de uso do servidor público: uma consulta por segundo
VALIDAR = "validar com a PM e o TRE local"
NIVEIS_ACESSO = ("alta", "media")

PONTOS = {
    "crime_organizado": 2,
    "homicidios_q5": 2,
    "homicidios_q4": 1,
    "favela_comunidade": 1,
    "terra_indigena_ou_quilombo": 1,
    "fronteira": 1,
    "garimpo": 1,
    "unidade_prisional": 1,
    "acesso_distante": 1,
}
CORTE_ALTO = 4
CORTE_MEDIO = 2
ACESSO_KM = 50.0


def regra() -> dict[str, Any]:
    return {
        "pontos": dict(PONTOS),
        "cortes": {"alto": CORTE_ALTO, "medio": CORTE_MEDIO},
        "acesso_distante_km": ACESSO_KM,
        "texto": (
            "soma de pontos: mapeamento público de crime organizado no município 2; "
            "homicídios no 5º quintil nacional 2 (4º quintil 1); favela ou comunidade "
            "urbana 1; terra indígena ou quilombo a até 2 km 1; faixa de fronteira 1; "
            "garimpo 1; unidade prisional ou socioeducativa 1; sede municipal a "
            f"{ACESSO_KM:.0f} km ou mais por estrada (ou em linha reta, sem rota) 1. "
            f"Alto com {CORTE_ALTO} pontos ou mais, médio com {CORTE_MEDIO} ou 3, baixo "
            "com 0 ou 1; nulo quando nenhuma camada cobre o local. Terra indígena e "
            "quilombo valem por polígono oficial (FUNAI), tipo do setor censitário ou nome "
            "do local; o proxy por ponto de localidade do IBGE vale só a até "
            f"{str(PROXY_PONTO_KM).replace('.', ',')} km e em setor rural"
        ),
        "frase": VALIDAR,
        "natureza": "juízo editorial por regra declarada, não medição de risco",
    }


# ---------------------------------------------------------------- leitura das camadas


def _num(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if s == "" or s.lower() in {"nan", "none", "null"}:
        return None
    try:
        x = float(s.replace(",", "."))
    except ValueError:
        return None
    return None if math.isnan(x) else x


def _bool(v: Any) -> bool | None:
    x = _num(v)
    if x is None:
        return None
    return bool(int(x))


def limpar(s: str) -> str:
    """Texto de base externa sem o travessão (regra da casa): vira vírgula ou hífen."""
    return s.replace(" \u2014 ", ", ").replace("\u2014", "-")


def _txt(v: Any) -> str | None:
    if v is None:
        return None
    s = limpar(str(v).strip())
    return s or None


def ler_locais_risco(caminho: Path = RISCO_LOCAIS) -> dict[str, dict[str, str]]:
    if not caminho.exists():
        return {}
    with gzip.open(caminho, "rt", encoding="utf-8") as f:
        return {r["local_id"]: r for r in csv.DictReader(f)}


def ler_municipios_risco(caminho: Path = RISCO_MUNICIPIOS) -> dict[str, dict[str, str]]:
    if not caminho.exists():
        return {}
    with caminho.open(encoding="utf-8") as f:
        return {
            f"{r['uf'].upper()}-{str(r['mun_tse']).zfill(5)}": r
            for r in csv.DictReader(f)
        }


def ler_fontes(caminho: Path = RISCO_FONTES) -> dict[str, Any]:
    if not caminho.exists():
        return {}
    return json.loads(caminho.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- distâncias


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def ler_aerodromos(caminho: Path = ANAC) -> list[dict[str, Any]]:
    if not caminho.exists():
        return []
    dados = json.loads(caminho.read_text(encoding="utf-8-sig"))
    out = []
    for a in dados:
        lat, lon = _num(a.get("LatGeoPoint")), _num(a.get("LonGeoPoint"))
        if lat is None or lon is None:
            continue
        nome = _txt(a.get("Nome")) or ""
        oaci = _txt(a.get("CódigoOACI"))
        out.append(
            {
                "nome": f"{nome} ({oaci})" if oaci else nome,
                "municipio": _txt(a.get("Município")),
                "lat": lat,
                "lon": lon,
            }
        )
    return out


def mais_proximo(
    lat: float, lon: float, pontos: Sequence[Mapping[str, Any]]
) -> tuple[Mapping[str, Any] | None, float | None]:
    if not pontos:
        return None, None
    la = np.radians([p["lat"] for p in pontos])
    lo = np.radians([p["lon"] for p in pontos])
    p1, l1 = math.radians(lat), math.radians(lon)
    a = (
        np.sin((la - p1) / 2) ** 2
        + np.cos(p1) * np.cos(la) * np.sin((lo - l1) / 2) ** 2
    )
    d = 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    i = int(np.argmin(d))
    return pontos[i], float(d[i])


class Osrm:
    """Consultas `table` ao servidor público do OSRM, com cache em disco."""

    def __init__(self, cache: Path = OSRM_CACHE, ativo: bool = True) -> None:
        self.caminho = cache
        self.ativo = ativo
        self.cache: dict[str, Any] = {}
        if cache.exists():
            self.cache = json.loads(cache.read_text(encoding="utf-8"))
        self.consultas = 0
        self.falhas = 0

    def tabela(
        self,
        origens: Sequence[tuple[float, float]],
        destinos: Sequence[tuple[float, float]],
    ) -> dict[str, Any] | None:
        coords = [*origens, *destinos]
        chave = ";".join(f"{lon:.5f},{lat:.5f}" for lat, lon in coords)
        chave += f"|{len(origens)}"
        if chave in self.cache:
            return self.cache[chave]
        if not self.ativo:
            return None
        src = ";".join(str(i) for i in range(len(origens)))
        dst = ";".join(str(i) for i in range(len(origens), len(coords)))
        url = (
            f"{OSRM_URL}{chave.split('|')[0]}?sources={src}&destinations={dst}"
            "&annotations=distance,duration"
        )
        time.sleep(OSRM_PAUSA_S)
        self.consultas += 1
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "arvor-pnad/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                res = json.loads(r.read().decode("utf-8"))
        except (OSError, ValueError):
            self.falhas += 1
            return None
        if res.get("code") != "Ok":
            self.falhas += 1
            return None
        saida = {"distances": res.get("distances"), "durations": res.get("durations")}
        self.cache[chave] = saida
        return saida

    def gravar(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(json.dumps(self.cache), encoding="utf-8")


def acesso(
    locais: pd.DataFrame,
    sedes: Mapping[str, tuple[float, float]],
    aerodromos: Sequence[Mapping[str, Any]],
    osrm: Osrm,
    por_estrada: set[str],
) -> dict[str, dict[str, Any]]:
    """Distância em linha reta para todos; por estrada (OSRM) para `por_estrada`."""
    out: dict[str, dict[str, Any]] = {}
    for lid, r in locais.iterrows():
        lat, lon = r["lat"], r["lon"]
        if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
            out[lid] = None  # type: ignore[assignment]
            continue
        sede = sedes.get(r["mun_chave"])
        aero, d_aero = mais_proximo(lat, lon, aerodromos)
        out[lid] = {
            "sede_km_reta": (
                round(haversine_km(sede[0], sede[1], lat, lon), 1) if sede else None
            ),
            "sede_km_estrada": None,
            "sede_min": None,
            "aeroporto": aero["nome"] if aero else None,
            "aeroporto_municipio": aero["municipio"] if aero else None,
            "aeroporto_km_reta": round(d_aero, 1) if d_aero is not None else None,
            "aeroporto_km_estrada": None,
            "aeroporto_min": None,
            "_aero": (aero["lat"], aero["lon"]) if aero else None,
            "_sede": sede,
        }
    grupos: dict[tuple, list[str]] = {}
    for lid in por_estrada:
        a = out.get(lid)
        if not a or a["_sede"] is None or a["_aero"] is None:
            continue
        grupos.setdefault((a["_sede"], a["_aero"]), []).append(lid)
    for (sede, aero), ids in sorted(grupos.items(), key=lambda kv: str(kv[0])):
        ids = sorted(ids)
        for i in range(0, len(ids), OSRM_LOTE):
            lote = ids[i : i + OSRM_LOTE]
            dest = [
                (float(locais.at[k, "lat"]), float(locais.at[k, "lon"])) for k in lote
            ]
            res = osrm.tabela([sede, aero], dest)
            if not res:
                continue
            for j, k in enumerate(lote):
                ds, dt = res["distances"], res["durations"]
                if ds[0][j] is not None:
                    out[k]["sede_km_estrada"] = round(ds[0][j] / 1000, 1)
                    out[k]["sede_min"] = round(dt[0][j] / 60, 0)
                if ds[1][j] is not None:
                    out[k]["aeroporto_km_estrada"] = round(ds[1][j] / 1000, 1)
                    out[k]["aeroporto_min"] = round(dt[1][j] / 60, 0)
    for a in out.values():
        if a:
            a.pop("_aero", None)
            a.pop("_sede", None)
            a["fonte"] = "osrm"
    return out


# ---------------------------------------------------------------- nível de risco


def nivel_risco(r: Mapping[str, Any]) -> tuple[str | None, list[str]]:
    """Pontos declarados em `PONTOS`; nulo quando nenhuma camada cobre o local."""
    motivos: list[str] = []
    pts = 0
    cobertas = 0
    co = r.get("crime_organizado") or {}
    if co.get("status") is not None:
        cobertas += 1
        if co["status"] == "mapeamento público":
            pts += PONTOS["crime_organizado"]
            motivos.append("mapeamento público cita o município ou a área (ver fontes)")
    h = r.get("homicidios_municipio") or {}
    if h.get("quintil") is not None:
        cobertas += 1
        q = int(h["quintil"])
        if q >= 4:
            pts += PONTOS["homicidios_q5"] if q == 5 else PONTOS["homicidios_q4"]
            taxa = h.get("taxa_100mil")
            txt = f"{taxa:.1f}".replace(".", ",") if taxa is not None else "s/d"
            motivos.append(
                f"homicídios no {q}º quintil nacional ({txt} por 100 mil, {h.get('ano')})"
            )
    for campo, chave, rotulo in (
        ("favela_comunidade", "favela_comunidade", "favela ou comunidade urbana"),
        (
            "unidade_prisional_ou_socioeducativa",
            "unidade_prisional",
            "unidade prisional ou socioeducativa",
        ),
    ):
        v = r.get(campo)
        if v is not None:
            cobertas += 1
            if v:
                pts += PONTOS[chave]
                motivos.append(rotulo)
    ti, qu = r.get("terra_indigena"), r.get("quilombo")
    if ti is not None or qu is not None:
        cobertas += 1
        if ti or qu:
            pts += PONTOS["terra_indigena_ou_quilombo"]
            motivos.append("terra indígena ou quilombo a até 2 km")
    fg = r.get("fronteira_ou_garimpo") or {}
    for chave, rotulo in (("fronteira", "faixa de fronteira"), ("garimpo", "garimpo")):
        v = fg.get(chave)
        if v is not None:
            cobertas += 1
            if v:
                pts += PONTOS[chave]
                motivos.append(rotulo)
    ac = r.get("acesso") or {}
    dist = ac.get("sede_km_estrada")
    if dist is None:
        dist = ac.get("sede_km_reta")
    if dist is not None:
        cobertas += 1
        if dist >= ACESSO_KM:
            pts += PONTOS["acesso_distante"]
            motivos.append(f"sede municipal a {dist:.0f} km".replace(".", ","))
    if cobertas == 0:
        return None, []
    if pts >= CORTE_ALTO:
        return "alto", motivos
    if pts >= CORTE_MEDIO:
        return "medio", motivos
    return "baixo", motivos


# ---------------------------------------------------------------- montagem


SEM_MAPEAMENTO = "sem mapeamento público"
COM_MAPEAMENTO = "mapeamento público"


def _crime(
    m: Mapping[str, str] | None, ctx_validos: set[str] | None = None
) -> dict[str, Any] | None:
    """Mapeamento público de crime organizado no município, só com fonte documentada.

    Itens de `contexto_seguranca.json` (`ctx-NNN`) valem só quando o tema é facção
    ou milícia (`ctx_validos`); coerção eleitoral e violência no dia ficam no campo
    `contexto` da seção, não aqui. Sem fonte restante, "sem mapeamento público".
    """
    if not m:
        return None
    status = _txt(m.get("crime_organizado"))
    if status is None:
        return None
    fontes = [
        f.strip()
        for f in (m.get("crime_organizado_fontes") or "").split("|")
        if f.strip()
    ]
    if ctx_validos is not None:
        fontes = [
            f
            for f in fontes
            if not f.startswith("ctx-") or f.split(" ")[0].rstrip(",") in ctx_validos
        ]
    if status == COM_MAPEAMENTO and not fontes:
        status = SEM_MAPEAMENTO
    return {"status": status, "fontes": [id_fonte(f) for f in fontes]}


def id_fonte(texto: str) -> str:
    """Identificador curto de uma referência ("ctx-033, Veículo, data, url" vira "ctx-033")."""
    return texto.strip().split(" ")[0].rstrip(",")


def referencias_crime(
    mrisco: Mapping[str, Mapping[str, str]], ctx_validos: set[str] | None
) -> dict[str, str]:
    """id curto da fonte de crime organizado → referência completa (veículo, data, url)."""
    out: dict[str, str] = {}
    for m in mrisco.values():
        for f in (m.get("crime_organizado_fontes") or "").split("|"):
            f = f.strip()
            if not f:
                continue
            i = id_fonte(f)
            if (
                i.startswith("ctx-")
                and ctx_validos is not None
                and i not in ctx_validos
            ):
                continue
            out.setdefault(i, limpar(f))
    return dict(sorted(out.items()))


def risco_local(
    lr: Mapping[str, str] | None,
    mr: Mapping[str, str] | None,
    ac: Mapping[str, Any] | None,
    ctx_validos: set[str] | None = None,
) -> dict[str, Any]:
    g = (lr or {}).get
    m = (mr or {}).get
    taxa = _num(m("homicidios_taxa_100mil"))
    out = {
        "rural_urbano": _txt(g("rural_urbano")),
        "rural_urbano_fonte": _txt(g("rural_urbano_fonte")),
        "setor_cd": _txt(g("setor_cd")),
        "setor_situacao": _txt(g("setor_situacao")),
        "setor_tipo": _txt(g("setor_tipo")),
        "terra_indigena": proxy_estrito(
            _bool(g("terra_indigena")),
            _txt(g("ti_fonte")),
            _num(g("ti_dist_km")),
            _txt(g("rural_urbano")),
            ("funai_tis_poligonais", "ibge_setor_tipo_5", "nome_local"),
        ),
        "terra_indigena_nome": _txt(g("ti_nome")),
        "terra_indigena_dist_km": _num(g("ti_dist_km")),
        "terra_indigena_fonte": _txt(g("ti_fonte")),
        "quilombo": proxy_estrito(
            _bool(g("quilombo")),
            _txt(g("quilombo_fonte")),
            _num(g("quilombo_dist_km")),
            _txt(g("rural_urbano")),
            ("ibge_setor_tipo_9", "nome_local"),
        ),
        "quilombo_nome": _txt(g("quilombo_nome")),
        "quilombo_dist_km": _num(g("quilombo_dist_km")),
        "quilombo_fonte": _txt(g("quilombo_fonte")),
        "favela_comunidade": _bool(g("favela")),
        "favela_comunidade_nome": _txt(g("favela_nome")),
        "favela_comunidade_fonte": _txt(g("favela_fonte")),
        "unidade_prisional_ou_socioeducativa": _bool(g("prisional")),
        "unidade_prisional_fonte": _txt(g("prisional_fonte")),
        "homicidios_municipio": {
            "taxa_100mil": taxa,
            "ano": (
                int(_num(m("homicidios_ano"))) if _num(m("homicidios_ano")) else None
            ),
            "quintil": (
                int(_num(m("homicidios_quintil")))
                if _num(m("homicidios_quintil"))
                else None
            ),
            "fonte": _fonte_homicidio(_txt(m("homicidios_fonte"))),
        },
        "crime_organizado": _crime(mr, ctx_validos),
        "fronteira_ou_garimpo": {
            "fronteira": _bool(g("fronteira")) if lr else _bool(m("fronteira")),
            "cidade_gemea": (
                _bool(g("cidade_gemea")) if lr else _bool(m("cidade_gemea"))
            ),
            "garimpo": _bool(g("garimpo")) if lr else _bool(m("garimpo")),
            "fonte": _txt(g("garimpo_fonte")),
        },
        "acesso": dict(ac) if ac else None,
    }
    nivel, motivos = nivel_risco(out)
    out["nivel_risco_fiscal"] = nivel
    out["motivos_risco"] = motivos
    out["validar"] = VALIDAR
    return out


FONTE_HOMICIDIO = "ipea_atlas_taxa_homicidios"


def _fonte_homicidio(texto: str | None) -> str | None:
    """A série 20 do Atlas da Violência vira a chave curta de `meta.fontes_risco`."""
    if texto and texto.startswith("Ipea, Atlas da Violência, série 20"):
        return FONTE_HOMICIDIO
    return texto


PROXY_PONTO_KM = 0.5


def proxy_estrito(
    valor: bool | None,
    fonte: str | None,
    dist_km: float | None,
    rural: str | None,
    fortes: Sequence[str],
) -> bool | None:
    """Terra indígena e quilombo com regra estrita para o proxy por ponto.

    Vale o positivo que vem de polígono oficial (FUNAI), do tipo do setor censitário
    ou do nome do local. O que vem só da distância até um ponto de localidade do IBGE
    (que não tem limite) vale a até 0,5 km e em setor rural; o resto vira `False`.
    Sem base, `None`.
    """
    if valor is None or not valor:
        return valor
    f = fonte or ""
    if any(x in f for x in fortes):
        return True
    return bool(dist_km is not None and dist_km <= PROXY_PONTO_KM and rural == "rural")


def _sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def territorio(
    sin: pd.DataFrame,
    loc_u: pd.DataFrame,
    usar_osrm: bool = True,
    ctx_validos: set[str] | None = None,
) -> dict[str, Any]:
    """Risco por `local_id` dos locais com seção sinalizada, fontes e regra."""
    lrisco = ler_locais_risco()
    mrisco = ler_municipios_risco()
    fontes_ext = ler_fontes()
    loc = sin.groupby("local_id", sort=False).agg(
        lat=("lat", "first"),
        lon=("lon", "first"),
        uf=("uf", "first"),
        mun=("mun", "first"),
        nivel=(
            "nivel",
            lambda s: next(
                (n for n in ("alta", "media", "baixa") if (s == n).any()), None
            ),
        ),
    )
    loc["mun_chave"] = loc["uf"].str.upper() + "-" + loc["mun"].astype(str)
    sedes: dict[str, tuple[float, float]] = {}
    for k, m in mrisco.items():
        la, lo = _num(m.get("sede_lat")), _num(m.get("sede_lon"))
        if la is not None and lo is not None:
            sedes[k] = (la, lo)
    aerodromos = ler_aerodromos()
    osrm = Osrm(ativo=usar_osrm)
    estrada = set(loc.index[loc["nivel"].isin(NIVEIS_ACESSO)])
    acessos = acesso(loc, sedes, aerodromos, osrm, estrada)
    if osrm.consultas:
        osrm.gravar()
    por_local = {
        lid: risco_local(
            lrisco.get(lid), mrisco.get(r["mun_chave"]), acessos.get(lid), ctx_validos
        )
        for lid, r in loc.iterrows()
    }
    fontes = list(fontes_ext.get("fontes", []))
    if not fontes:
        fontes.append(
            {
                "chave": "camadas_risco",
                "camada": "todas as camadas do território",
                "status": "falhou",
                "motivo": (
                    "arquivos de scripts/apuracao-2026-fiscais-risco.py ausentes nesta "
                    "rodada; campos nulos"
                ),
            }
        )
    if ANAC.exists():
        fontes.append(
            {
                "chave": "anac_aerodromos",
                "camada": "acesso",
                "nome": "Lista de aeródromos públicos",
                "orgao": "ANAC",
                "url": ANAC_URL,
                "baixado_em": datetime.fromtimestamp(
                    ANAC.stat().st_mtime, timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "caminho": str(ANAC.relative_to(ROOT)),
                "bytes": ANAC.stat().st_size,
                "sha256": _sha(ANAC),
                "status": "ok",
                "regra": "aeródromo público mais próximo em linha reta",
            }
        )
    n_estrada = sum(
        1 for k in estrada if (acessos.get(k) or {}).get("sede_km_estrada") is not None
    )
    fontes.append(
        {
            "chave": "osrm",
            "camada": "acesso",
            "nome": "OSRM, serviço table, perfil carro",
            "orgao": "Project OSRM (dados OpenStreetMap)",
            "url": OSRM_URL,
            "baixado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "caminho": str(OSRM_CACHE.relative_to(ROOT)),
            "status": "ok" if n_estrada else ("falhou" if usar_osrm else "pendente"),
            "motivo": (
                None
                if n_estrada
                else "sem sede municipal ou sem resposta do servidor nesta rodada"
            ),
            "regra": (
                "distância e tempo por estrada (OSRM, perfil carro, dados OpenStreetMap) "
                "da sede municipal (IBGE, Localidades 2022) ao local e do local ao "
                "aeródromo público mais próximo em linha reta (ANAC), só para locais de "
                "nível alta e média; os demais trazem só a distância em linha reta"
            ),
            "consultas": osrm.consultas,
            "falhas": osrm.falhas,
            "locais_com_rota": n_estrada,
            "locais_alvo": len(estrada),
        }
    )
    _cobertura(fontes, por_local, sin)
    return {
        "por_local": por_local,
        "fontes": fontes,
        "regra": regra(),
        "referencias_crime": referencias_crime(mrisco, ctx_validos),
    }


CAMADA_CAMPO = {
    "rural_urbano": lambda r: r.get("rural_urbano"),
    "terra_indigena": lambda r: r.get("terra_indigena"),
    "quilombo": lambda r: r.get("quilombo"),
    "favela_comunidade": lambda r: r.get("favela_comunidade"),
    "unidade_prisional_ou_socioeducativa": lambda r: r.get(
        "unidade_prisional_ou_socioeducativa"
    ),
    "homicidios_municipio": lambda r: (r.get("homicidios_municipio") or {}).get(
        "taxa_100mil"
    ),
    "crime_organizado": lambda r: (r.get("crime_organizado") or {}).get("status"),
    "fronteira": lambda r: (r.get("fronteira_ou_garimpo") or {}).get("fronteira"),
    "garimpo": lambda r: (r.get("fronteira_ou_garimpo") or {}).get("garimpo"),
    "acesso": lambda r: (r.get("acesso") or {}).get("sede_km_estrada"),
}


def _cobertura(
    fontes: list[dict[str, Any]], por_local: Mapping[str, Any], sin: pd.DataFrame
) -> None:
    """Seções e locais sinalizados que receberam cada camada (valor não nulo)."""
    secoes_por_local = sin.groupby("local_id").size()
    for f in fontes:
        camada = f.get("camada")
        func = CAMADA_CAMPO.get(str(camada))
        if func is None:
            continue
        com = [k for k, r in por_local.items() if func(r) is not None]
        f["cobertura_locais"] = len(com)
        f["cobertura_secoes"] = int(secoes_por_local.reindex(com).fillna(0).sum())
