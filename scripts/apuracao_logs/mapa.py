"""Integra os registros operacionais ao mapa, sem alterar a pontuação histórica.

``integrar`` devolve a tabela por seção (``colunas``/``linhas``) com as colunas dos logs e,
para toda seção exibida, o nome de município do cadastro, o resultado da urna no 1º
turno (comparecimento e percentuais de válidos, do Politize) e o nível de atenção dos
logs (``familias.atencao``). ``publicar_recortes`` grava o formato normalizado que o
aplicativo lê: locais de votação numa tabela e seções noutra, por UF, mais um recorte
nacional de destaque (capítulo 13 e logs com atenção 2 ou 3).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from .familias import NIVEIS_ATENCAO, NOME_CURTO, atencao, catalogo

ROOT = Path(__file__).resolve().parents[2]
POLITIZE = ROOT / "docs/assets/politize/dados"
LOGS = ROOT / "analysis/apuracao_2026/logs_urnas/sinalizadas.json"
INDICE = ROOT / "docs/assets/logs_urnas_2026/indice.json"

COLUNAS_LOCAIS = [
    "id",
    "uf",
    "mun",
    "municipio",
    "zona",
    "local",
    "endereco",
    "bairro",
    "cep",
    "lat",
    "lon",
    "coord_fonte",
    "risco",
    "risco_motivos",
    "secoes_total",
    "aptos_total",
]
COLUNAS_SECOES = [
    "li",
    "secao",
    "nivel",
    "pontuacao",
    "criterios",
    "explicacao",
    "aptos",
    "comparecimento",
    "flavio_pct",
    "lula_pct",
    "logs",
    "atencao",
    "tempo_voto",
    "processo_mediana",
    "cadencia_mediana",
]
ATENCAO_DESTAQUE = 2


def tabela(obj):
    return [dict(zip(obj["colunas"], row, strict=True)) for row in obj["linhas"]]


class Cadastro:
    """Leitura preguiçosa dos fragmentos do Politize (zona, município e local)."""

    def __init__(self, base: Path):
        self.base = base
        self._zonas: dict[tuple[str, int], dict[int, dict]] = {}
        self._muns: dict[tuple[str, str], tuple[str | None, dict[str, dict]]] = {}

    def zona(self, uf: str, z: int) -> dict[int, dict]:
        chave = (uf, int(z))
        if chave not in self._zonas:
            path = self.base / "zona" / uf / f"{int(z)}.json"
            self._zonas[chave] = (
                {
                    int(r["secao"]): r
                    for r in tabela(json.loads(path.read_text())["secoes"])
                }
                if path.exists()
                else {}
            )
        return self._zonas[chave]

    def municipio(self, uf: str, mun: str) -> tuple[str | None, dict[str, dict]]:
        chave = (uf, mun)
        if chave not in self._muns:
            path = self.base / "mun" / uf / f"{mun}.json"
            if path.exists():
                cad = json.loads(path.read_text())
                self._muns[chave] = (
                    cad.get("nome"),
                    {r["local_id"]: r for r in tabela(cad["locais"])},
                )
            else:
                self._muns[chave] = (None, {})
        return self._muns[chave]


def _mun_de(local_id: str | None) -> str | None:
    partes = str(local_id or "").split("-")
    return partes[1] if len(partes) >= 4 else None


MIN_APTOS_VOTO = 30  # mesma regra do Politize: seção muito pequena não mostra voto


def _resultado(sec: dict | None) -> dict:
    if not sec:
        return {}
    pequena = (sec.get("aptos") or 0) < MIN_APTOS_VOTO
    return {
        "aptos": sec.get("aptos"),
        "comparecimento": sec.get("comparecimento"),
        "flavio_pct": None if pequena else sec.get("flavio_v"),
        "lula_pct": None if pequena else sec.get("lula_v"),
    }


def integrar(obj: dict) -> dict:
    cadastro = Cadastro(POLITIZE)
    linhas = tabela(obj)
    antigos = {(r["uf"], r["zona"], r["secao"]): r for r in linhas}
    for r in linhas:
        r["originais"] = True
        r["logs"] = []
        r["coord_fonte"] = "cadastro" if r["uf"] != "ZZ" else "cidade"
        r.setdefault("mun", _mun_de(r.get("local_id")))
    if LOGS.exists() and INDICE.exists():
        indice = json.loads(INDICE.read_text())
        sinais = json.loads(LOGS.read_text())
        complemento_path = INDICE.parent / "complementos.json"
        complementos = (
            json.loads(complemento_path.read_text())
            if complemento_path.exists()
            else {}
        )
        for log in sinais:
            uf, z, s, m = log["uf"], log["zona"], log["secao"], log["mun"]
            chave = (uf, z, s)
            if chave not in antigos:
                sec = cadastro.zona(uf, z).get(s)
                suplemento = complementos.get(f"{uf}-{z}-{s}")
                if not sec and suplemento:
                    sec = {**suplemento, "mun_tse": m}
                if not sec or str(sec["mun_tse"]) != m:
                    raise ValueError(
                        f"Seção sinalizada sem vínculo cadastral: {uf}-{z}-{s}"
                    )
                nome, locais = cadastro.municipio(uf, m)
                if nome is None:
                    raise ValueError(f"Município sinalizado sem cadastro: {uf}-{m}")
                loc = locais.get(sec["local_id"], {})
                r = {
                    "uf": uf,
                    "mun": m,
                    "municipio": nome,
                    "zona": z,
                    "secao": s,
                    "local_id": sec["local_id"],
                    "local": sec.get("local")
                    or f"Local {sec['local_id'].rsplit('-', 1)[-1]}",
                    "endereco": loc.get("endereco"),
                    "bairro": loc.get("bairro"),
                    "cep": loc.get("cep"),
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon"),
                    "nivel": "logs",
                    "pontuacao": None,
                    "criterios": "",
                    "explicacao": None,
                    "risco": None,
                    "aptos": sec.get("aptos"),
                    "flavio_pct": None,
                    "lula_pct": None,
                    "originais": False,
                    "coord_fonte": loc.get("coord_fonte"),
                }
                antigos[chave] = r
                linhas.append(r)
            antigos[chave]["logs"] = log["sinais"]
            antigos[chave]["tempo_voto"] = (
                log["voto_mediana"] if log["elegivel_tempo"] else None
            )
            for campo in ("processo_mediana", "cadencia_mediana"):
                antigos[chave][campo] = (
                    log.get(campo) if log["elegivel_tempo"] else None
                )
        obj["logs"] = {
            "criterios": {
                k: {**v, "curto": NOME_CURTO.get(k, v["nome"])}
                for k, v in indice["criterios"].items()
            },
            "familias": catalogo(indice["criterios"]),
            "niveis_atencao": {str(k): v for k, v in NIVEIS_ATENCAO.items()},
            "sem_ocorrencia": [
                k for k, v in indice["criterios"].items() if not v.get("secoes")
            ],
            "cobertura": indice["cobertura"],
            "gerado_em": indice["gerado_em"],
        }
    for row in linhas:
        row["logs"] = row.get("logs") or []
        row["atencao"] = atencao(row["logs"]) if row["logs"] else None
        mun = row.get("mun")
        # Nome de município do cadastro para toda linha (o capítulo 13 vinha em maiúsculas),
        # e resultado da urna por seção, do Politize, onde a seção existe no cadastro.
        if mun:
            nome, locais = cadastro.municipio(row["uf"], mun)
            if nome:
                row["municipio"] = nome
            # O capítulo histórico não tinha coordenadas do exterior. O Politize tem
            # centros de cidade, explicitamente aproximados, e nunca endereço inventado.
            if row["uf"] == "ZZ" and row.get("lat") is None:
                local = locais.get(str(row.get("local_id") or ""))
                if local:
                    row["lat"], row["lon"] = local.get("lat"), local.get("lon")
                    row["coord_fonte"] = local.get("coord_fonte")
        sec = cadastro.zona(row["uf"], row["zona"]).get(int(row["secao"]))
        for k, v in _resultado(sec).items():
            if row.get(k) is None:
                row[k] = v
        if (row.get("aptos") or 0) < MIN_APTOS_VOTO:
            row["flavio_pct"] = row["lula_pct"] = None
    colunas = list(
        dict.fromkeys(
            [
                *obj["colunas"],
                "mun",
                "municipio",
                "comparecimento",
                "originais",
                "logs",
                "atencao",
                "tempo_voto",
                "coord_fonte",
                "processo_mediana",
                "cadencia_mediana",
            ]
        )
    )
    obj["colunas"] = colunas
    obj["linhas"] = [[r.get(c) for c in colunas] for r in linhas]
    obj["resumo"]["secoes_originais"] = obj["resumo"]["secoes"]
    obj["resumo"]["secoes"] = len(linhas)
    obj["resumo"]["atencao"] = dict(
        Counter(str(r["atencao"]) for r in linhas if r["atencao"] is not None)
    )
    obj["titulo"] = (
        "Mapa de fiscais: critérios históricos e registros operacionais dos logs"
    )
    return obj


def normalizar(obj: dict, linhas: list[dict]) -> dict:
    """Locais numa tabela, seções noutra; a seção aponta o local pelo índice ``li``."""
    cadastro = Cadastro(POLITIZE)
    risco_local = obj.get("risco_local") or {}
    locais: list[list] = []
    indice: dict[str, int] = {}
    secoes: list[list] = []
    for r in linhas:
        lid = r.get("local_id") or f"{r['uf']}-{r.get('mun')}-{r['zona']}-?"
        if lid not in indice:
            mun = r.get("mun")
            cad = cadastro.municipio(r["uf"], mun)[1] if mun else {}
            loc = cad.get(lid, {})
            indice[lid] = len(locais)
            locais.append(
                [
                    lid,
                    r["uf"],
                    r.get("mun"),
                    r.get("municipio"),
                    r["zona"],
                    r.get("local"),
                    r.get("endereco"),
                    r.get("bairro"),
                    r.get("cep"),
                    r.get("lat"),
                    r.get("lon"),
                    r.get("coord_fonte"),
                    r.get("risco"),
                    risco_local.get(lid) or None,
                    loc.get("secoes"),
                    loc.get("aptos"),
                ]
            )
        li = indice[lid]
        if r.get("risco") and locais[li][12] is None:
            locais[li][12] = r["risco"]
        secoes.append(
            [
                li,
                r["secao"],
                r["nivel"],
                r.get("pontuacao"),
                r.get("criterios") or "",
                r.get("explicacao"),
                r.get("aptos"),
                r.get("comparecimento"),
                r.get("flavio_pct"),
                r.get("lula_pct"),
                r.get("logs") or [],
                r.get("atencao"),
                r.get("tempo_voto"),
                r.get("processo_mediana"),
                r.get("cadencia_mediana"),
            ]
        )
    return {"locais": locais, "secoes": secoes}


def publicar_recortes(obj: dict, destino: Path):
    """Um arquivo por UF, o histórico sozinho e o destaque nacional, todos normalizados."""
    linhas = tabela(obj)
    partes: dict[str, list[dict]] = defaultdict(list)
    for r in linhas:
        partes[r["uf"]].append(r)
    meta = {k: v for k, v in obj.items() if k not in ("linhas", "risco_local")}
    meta["formato"] = 2
    meta["colunas_locais"] = COLUNAS_LOCAIS
    meta["colunas_secoes"] = COLUNAS_SECOES
    meta["partes"] = {
        uf: {
            "arquivo": f"uf/{uf}.json",
            "secoes": len(rows),
            "locais": len({r.get("local_id") for r in rows}),
            "municipios": [
                list(m)
                for m in sorted(
                    {(r.get("mun") or "", r.get("municipio") or "") for r in rows},
                    key=lambda x: x[1],
                )
            ],
        }
        for uf, rows in sorted(partes.items())
    }
    meta["niveis"] = dict(Counter(r["nivel"] for r in linhas))
    originais = [r for r in linhas if r.get("originais", True)]
    destaque = [
        r
        for r in linhas
        if r.get("originais", True)
        or (r.get("atencao") is not None and r["atencao"] >= ATENCAO_DESTAQUE)
    ]
    meta["recortes"] = {
        "originais": {"arquivo": "originais.json", "secoes": len(originais)},
        "destaque": {
            "arquivo": "destaque.json",
            "secoes": len(destaque),
            "atencao_minima": ATENCAO_DESTAQUE,
        },
    }

    def salvar(nome, dados):
        path = destino / nome
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(dados, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    salvar("indice.json", meta)
    salvar("originais.json", normalizar(obj, originais))
    salvar("destaque.json", normalizar(obj, destaque))
    for uf, rows in partes.items():
        salvar(f"uf/{uf}.json", normalizar(obj, rows))
    return meta
