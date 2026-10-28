"""Gravação dos dados do mapa do Brasil do Politize-se (formato 3).

``docs/assets/politize_se_mapa/``:

- ``indice.json``: camadas, catálogos de sinais, cobertura do 2º turno por UF, lista de
  municípios por UF, centro de cada zona e contagens;
- ``uf/<UF>.json``: prédios da UF (``locais``) e totais dos municípios (``municipios``);
- ``cep/<2 dígitos>.json``: CEP de local de votação (8 e 5 dígitos) para coordenada.

JSON compacto, UTF-8. O formato 3 é próprio deste mapa; o aplicativo recusa outro.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import mapa_dados as md
from . import territorio

SAIDA = md.ROOT / "docs/assets/politize_se_mapa"
UFS_ORDEM = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT", "PA",
    "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO", "ZZ",
]  # fmt: skip


def gravar_json(caminho: Path, obj: Any) -> int:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    caminho.write_text(txt, encoding="utf-8")
    return len(txt.encode("utf-8"))


def _contagem(locais: list[list[Any]]) -> dict[str, int]:
    c = {k: i for i, k in enumerate(md.COLUNAS_LOCAIS)}
    return {
        "locais": len(locais),
        "com_coord": sum(r[c["lat"]] is not None for r in locais),
        "com_bu2": sum(bool(r[c["n_bu2"]]) for r in locais),
        "secoes": sum(r[c["n_secoes"]] or 0 for r in locais),
        "secoes_bu2": sum(r[c["n_bu2"]] or 0 for r in locais),
        "aptos": sum((r[c["aptos2"]] or r[c["aptos1"]] or 0) for r in locais),
    }


def contagem_modelos(lido: dict[str, Any], anterior: dict | None) -> dict[str, Any]:
    """Seções por modelo de urna e prédios por modelo (``misto`` à parte), por UF e no país."""
    c = {k: i for i, k in enumerate(md.COLUNAS_LOCAIS)}
    por_uf = dict((anterior or {}).get("ufs") or {})
    for uf, d in lido["ufs"].items():
        secoes: dict[str, int] = {}
        predios: dict[str, int] = {}
        for r in d["locais"]:
            for m, n in r[c["modelos"]]:
                secoes[m] = secoes.get(m, 0) + n
            chave = r[c["modelo"]] or "sem_dado"
            predios[chave] = predios.get(chave, 0) + 1
        por_uf[uf] = {"secoes": secoes, "predios": predios}
    nac: dict[str, dict[str, int]] = {"secoes": {}, "predios": {}}
    for v in por_uf.values():
        for k in ("secoes", "predios"):
            for m, n in v[k].items():
                nac[k][m] = nac[k].get(m, 0) + n
    return {"nacional": nac, "ufs": por_uf}


def contagem_logs(lido: dict[str, Any], anterior: dict | None) -> dict[str, Any]:
    """Prédios por atenção máxima no 2º turno e prédios em que alguma seção subiu de
    nível, por UF (mesclados com o índice anterior numa amostra) e no país."""
    c = {k: i for i, k in enumerate(md.COLUNAS_LOCAIS)}
    por_uf = dict((anterior or {}).get("ufs") or {})
    for uf, d in lido["ufs"].items():
        niveis: dict[str, int] = {}
        subiu = com_log = 0
        for r in d["locais"]:
            n = r[c["log2_max"]]
            if n is None:
                continue
            com_log += 1
            niveis[str(n)] = niveis.get(str(n), 0) + 1
            subiu += bool(r[c["log_subiu"]])
        por_uf[uf] = {"com_log": com_log, "por_nivel": niveis, "subiu": subiu}
    niveis_nac: dict[str, int] = {}
    for v in por_uf.values():
        for n, q in v["por_nivel"].items():
            niveis_nac[n] = niveis_nac.get(n, 0) + q
    return {
        "predios_com_log": sum(v["com_log"] for v in por_uf.values()),
        "predios_por_nivel": niveis_nac,
        "predios_subiu": sum(v["subiu"] for v in por_uf.values()),
        "ufs": por_uf,
    }


def gravar(lido: dict[str, Any], saida: Path = SAIDA, mesclar: bool = False) -> dict:
    """Grava índice, arquivos por UF e CEP; devolve o índice gravado."""
    origem = lido["indice"]
    agora = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    anterior: dict[str, Any] = {}
    if mesclar and (saida / "indice.json").exists():
        anterior = json.loads((saida / "indice.json").read_text(encoding="utf-8"))
    ufs = dict(anterior.get("ufs") or {})
    zonas = dict(anterior.get("zonas") or {})
    tamanhos: dict[str, int] = {}
    for uf, d in lido["ufs"].items():
        col = md.COLUNAS_LOCAIS.index("id")
        locais = sorted(d["locais"], key=lambda r: r[col])
        arquivo = f"uf/{uf}.json"
        tamanhos[uf] = gravar_json(
            saida / arquivo,
            {
                "formato": md.FORMATO,
                "uf": uf,
                "gerado_em": agora,
                "municipios": {
                    "colunas": md.COLUNAS_MUNICIPIOS,
                    "linhas": sorted(d["municipios"]),
                },
                "locais": {"colunas": md.COLUNAS_LOCAIS, "linhas": locais},
            },
        )
        ufs[uf] = {
            "arquivo": arquivo,
            "bytes": tamanhos[uf],
            **_contagem(locais),
            "municipios": sorted(d["lista_mun"], key=lambda m: m[1]),
        }
        ctx = lido.get("contextos", {}).get(uf, {})
        gravar_json(
            saida / f"contexto/{uf}.json",
            {
                "uf": uf,
                "municipios": ctx.get("municipios", {}),
                "locais": {
                    "colunas": territorio.COLUNAS,
                    "linhas": [
                        [r.get(k) for k in territorio.COLUNAS]
                        for _, r in sorted(ctx.get("locais", {}).items())
                    ],
                },
            },
        )
        if uf in lido["zonas"]:
            zonas[uf] = lido["zonas"][uf]
    # Um prefixo de CEP atravessa estados (69 = AM, AC e RR): numa amostra o índice de CEP
    # fica como estava, porque regravá-lo com uma UF só apagaria as outras.
    if mesclar:
        tam_cep = int(anterior.get("bytes_cep") or 0)
    else:
        for velho in (saida / "cep").glob("*.json"):
            velho.unlink()
        tam_cep = sum(
            gravar_json(saida / f"cep/{p}.json", v)
            for p, v in sorted(lido["cep"].items())
        )
    ufs = {u: ufs[u] for u in UFS_ORDEM if u in ufs}
    total = {
        k: sum(u[k] for u in ufs.values())
        for k in ("locais", "com_coord", "com_bu2", "secoes", "secoes_bu2", "aptos")
    }
    total["sem_coord"] = total["locais"] - total["com_coord"]
    modelos = contagem_modelos(lido, anterior.get("modelos_urna"))
    cat = origem.get("catalogos") or {}
    indice = {
        "formato": md.FORMATO,
        "versao": "1.0",
        "gerado_em": agora,
        "fonte": "docs/assets/politize_se/dados (scripts/politize-se-build.py)",
        "fonte_gerado_em": origem.get("gerado_em"),
        "rotulo": origem.get("rotulo"),
        "rotulos": origem.get("rotulos") or [],
        "cobertura": origem.get("cobertura") or {},
        "camadas": md.CAMADAS,
        "camada_padrao": md.CAMADA_PADRAO,
        "min_aptos_voto": md.MIN_APTOS_VOTO,
        "catalogos": {
            k: cat.get(k) or {}
            for k in (
                "sinais",
                "explicacoes",
                "urna",
                "log",
                "log_familias",
                "log_niveis",
                "ml",
            )
        },
        "logs_2t": {
            **(origem.get("logs_2t") or {}),
            **contagem_logs(lido, anterior.get("logs_2t")),
        },
        # mistura estatística dos dois turnos: copiado do Politize-se; sem o motor, indisponível
        "anomalia_ml": origem.get("anomalia_ml") or {"disponivel": False},
        "clima2": {
            k: (md.observado() or {}).get(k)
            for k in (
                "gerado_em",
                "dia",
                "fonte",
                "rotulos_fonte",
                "raio_km",
                "cortes",
                "nota",
            )
        },
        "chuva_forte_mm": md.CHUVA_FORTE_MM,
        "colunas_locais": md.COLUNAS_LOCAIS,
        "colunas_municipios": md.COLUNAS_MUNICIPIOS,
        "resumo": {**total, "bytes_ufs": sum(u["bytes"] for u in ufs.values())},
        "bytes_cep": tam_cep,
        "modelos_urna": modelos,
        "ufs": ufs,
        "zonas": zonas,
    }
    gravar_json(saida / "indice.json", indice)
    gravar_json(saida / "contexto/indice.json", territorio.metadados())
    return indice
