"""Fontes com SHA-256 e controles que precisam passar antes da publicação."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data/originals/clima_1t_2026/sha256_cache.json"
FONTES = {
    "locais_votacao": (
        "data/outputs/locais_votacao_2026.sqlite",
        "cadastro de locais com coordenada (TSE)",
    ),
    "boletins_1t": (
        "apuracao/data/secoes_2026.sqlite",
        "boletins de urna do 1º turno (TSE)",
    ),
    "logs_1t": (
        "data/outputs/logs_urnas_2026.sqlite",
        "métricas dos logs das urnas do 1º turno",
    ),
    "mapa_fiscais_indice": (
        "docs/assets/fiscais_mapa/indice.json",
        "índice do mapa de fiscais (códigos de log)",
    ),
    "presidente_2022": (
        "data/outputs/presidente_secao_2022.csv.gz",
        "seções de 2022 (1º turno, compacto)",
    ),
    "detalhe_2022": (
        "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip",
        "detalhe de votação por seção de 2022 (2º turno)",
    ),
    "clima_archive": (
        "analysis/clima_1t_2026/celulas_archive.json",
        "Open-Meteo archive consolidado",
    ),
    "mudancas_2t": (
        "analysis/mudancas_secoes_2t/mudancas.json",
        "motor das mudanças de seção do 2º turno",
    ),
    "previsao": (
        "docs/assets/fiscais_mapa/clima/previsao.json",
        "previsão Open-Meteo para 25/10",
    ),
}


def sha256(caminho: Path) -> str:
    """SHA-256 com cache por tamanho e data de modificação (os bancos têm gigabytes)."""
    st = caminho.stat()
    chave = f"{caminho.relative_to(ROOT)}|{st.st_size}|{st.st_mtime_ns}"
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    if chave in cache:
        return cache[chave]
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 22), b""):
            h.update(bloco)
    cache[chave] = h.hexdigest()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1))
    return cache[chave]


def fontes() -> list[dict[str, Any]]:
    saida = []
    for chave, (rel, desc) in FONTES.items():
        p = ROOT / rel
        if not p.exists():
            saida.append(
                {"chave": chave, "caminho": rel, "descricao": desc, "existe": False}
            )
            continue
        saida.append(
            {
                "chave": chave,
                "caminho": rel,
                "descricao": desc,
                "bytes": p.stat().st_size,
                "sha256": sha256(p),
            }
        )
    return saida


def _ctl(nome: str, esperado: Any, obtido: Any, passou: bool) -> dict[str, Any]:
    return {
        "nome": nome,
        "esperado": esperado,
        "obtido": obtido,
        "passou": bool(passou),
    }


def controles(
    urnas_todas: pd.DataFrame,
    urnas: pd.DataFrame,
    locais: pd.DataFrame,
    archive: dict[str, Any],
    totais_motor: dict[str, int],
    politize: dict[str, Any] | None,
    atencao: pd.DataFrame,
) -> list[dict[str, Any]]:
    out = []
    mud = json.loads((ROOT / "analysis/mudancas_secoes_2t/mudancas.json").read_text())
    tn = mud["totais_nacionais_1t"]
    for k in ("validos", "flavio", "lula", "brancos", "nulos"):
        out.append(
            _ctl(
                f"total nacional de {k} igual ao motor das mudanças",
                tn[k],
                totais_motor[k],
                tn[k] == totais_motor[k],
            )
        )
    cob = archive["cobertura"]
    out.append(
        _ctl(
            "células de 0,25° com resposta da Open-Meteo",
            cob["celulas"],
            cob["coletadas"],
            cob["completa"],
        )
    )
    out.append(
        _ctl(
            "valores nulos nas respostas do arquivo",
            0,
            cob["valores_nulos"],
            cob["valores_nulos"] == 0,
        )
    )
    br = urnas_todas.loc[urnas_todas["uf"] != "ZZ"]
    sem_local = int(br["local_id"].isna().sum())
    out.append(
        _ctl("urnas do Brasil sem local no cadastro", 0, sem_local, sem_local == 0)
    )
    sem_clima = int((br["local_id"].notna() & ~br["tem_clima"]).sum())
    out.append(
        _ctl(
            "urnas do Brasil sem clima (local sem coordenada no território)",
            "pequeno e declarado",
            sem_clima,
            sem_clima < 0.01 * len(br),
        )
    )
    loc_bu = locais.loc[locais["urnas"] > 0]
    out.append(
        _ctl(
            "soma dos aptos por local igual à soma por urna",
            int(br["aptos"].sum()),
            int(loc_bu["aptos"].sum()),
            int(br.loc[br["local_id"].notna(), "aptos"].sum())
            == int(loc_bu["aptos"].sum()),
        )
    )
    # relógio: a hora de Brasília do primeiro voto tem moda 8 em toda UF
    h = (br["abertura_min"] // 60).dropna()
    modas = h.groupby(br.loc[h.index, "uf"]).agg(
        lambda s: int(s.value_counts().idxmax())
    )
    horas = {int(x) for x in modas}
    out.append(
        _ctl(
            "moda da hora de Brasília do primeiro voto é 8 em todas as UFs (votação unificada)",
            8,
            sorted(horas),
            horas == {8},
        )
    )
    for cod, campo in (
        ("bateria_votacao_local", "bat_vot_local"),
        ("bateria_votacao_isolada", "bat_vot_isolada"),
    ):
        no_mapa = int(atencao["codigos"].apply(lambda x, c=cod: c in x).sum())
        nas_urnas = int(br[campo].sum())
        com_bu = atencao.loc[atencao["codigos"].apply(lambda x, c=cod: c in x)].merge(
            br[["uf", "mun", "zona", "secao"]], on=["uf", "mun", "zona", "secao"]
        )
        out.append(
            _ctl(
                f"seções com o código {cod} (mapa: {no_mapa}; sem boletim do 1º turno: "
                f"{no_mapa - len(com_bu)})",
                len(com_bu),
                nas_urnas,
                nas_urnas == len(com_bu),
            )
        )
    fora = int(
        (br["bat_vot_local"] | br["bat_vot_isolada"]).sum()
        - (br["bateria_votacao"] & (br["bat_vot_local"] | br["bat_vot_isolada"])).sum()
    )
    out.append(
        _ctl(
            "código de simultaneidade só em urna com bateria durante a votação",
            0,
            fora,
            fora == 0,
        )
    )
    if politize is not None:
        out.append(
            _ctl(
                "aptos e votos por seção iguais aos do Politize",
                "todas iguais",
                {k: politize[k] for k in ("secoes_conferidas", "iguais", "diferentes")},
                politize["diferentes"] == 0,
            )
        )
    n_amostra = len(urnas)
    out.append(
        _ctl(
            "urnas na amostra analítica (mais de 99% das urnas do Brasil)",
            len(br),
            n_amostra,
            n_amostra > 0.99 * len(br),
        )
    )
    return out
