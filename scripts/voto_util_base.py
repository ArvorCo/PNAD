"""Leitura e normalizacao das transcricoes estaduais do mapa do voto util.

As transcricoes (uma por estado em `analysis/voto_util/quaest/<UF>.json` e uma
por pesquisa em `analysis/voto_util/outros/`) foram feitas pagina a pagina e
guardam a pagina de origem. Este modulo so le, normaliza nomes e escolhe a
rodada mais recente; nao inventa numero. Categoria ausente no PDF fica ausente.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUAEST = ROOT / "analysis/voto_util/quaest"
OUTROS = ROOT / "analysis/voto_util/outros"

# Presidenciaveis por campo. A classificacao e editorial e esta declarada na pagina.
TERCEIRA_DIREITA = (
    "Cury",
    "Caiado",
    "Renan",
    "Zema",
    "Avalanche",
    "Marçal",
    "Clariana",
    "Grassi",
)
ESQUERDA_MENOR = ("Pimenta", "Samara", "Edmilson", "Hertz")
PRINCIPAIS = ("Flávio", "Lula")
NAO_ESCOLHA = ("Indecisos", "Branco/nulo")
META = {"me", "soma", "pagina", "nota", "valores", "n", "base"}

ALIAS = {
    "Flavio": "Flávio",
    "Flavio Bolsonaro": "Flávio",
    "Flávio Bolsonaro": "Flávio",
    "Marcal": "Marçal",
    "Branco/Nulo": "Branco/nulo",
    "Branco/nulo/não vai votar": "Branco/nulo",
    "Branco/Nulo/Não vai votar": "Branco/nulo",
    "Indeciso": "Indecisos",
    "NS/NR": "Indecisos",
}

# Partidos por campo, para classificar governador e senado. Padrao por partido,
# com excecao declarada por candidato quando o alinhamento local contraria a sigla.
PARTIDO_CAMPO = {
    "PL": "direita", "NOVO": "direita", "REPUBLICANOS": "direita", "PP": "direita",
    "UNIÃO": "direita", "UNIAO": "direita", "PODEMOS": "direita", "PRD": "direita",
    "DC": "direita", "AGIR": "direita", "MISSÃO": "direita", "PRTB": "direita",
    "MOBILIZA": "direita", "DEMOCRATA": "direita", "PSD": "centro-direita",
    "MDB": "centro", "PSDB": "centro-direita", "CIDADANIA": "centro", "AVANTE": "centro",
    "SOLIDARIEDADE": "centro-esquerda", "PDT": "esquerda", "PT": "esquerda", "PSB": "esquerda",
    "PCdoB": "esquerda", "PCDOB": "esquerda", "PV": "esquerda", "PSOL": "esquerda",
    "REDE": "esquerda", "UP": "esquerda", "PCB": "esquerda", "PSTU": "esquerda", "PCO": "esquerda",
}  # fmt: skip


def canon(nome: str) -> str:
    nome = nome.strip()
    if nome in ALIAS:
        return ALIAS[nome]
    base = re.sub(r"\s*\(.*\)$", "", nome)
    return ALIAS.get(base, base)


def partido_de(rotulo: str) -> str | None:
    m = re.search(r"\(([^)]+)\)\s*$", rotulo)
    return m.group(1).strip().upper() if m else None


def campo_de(partido: str | None) -> str:
    if not partido:
        return "indefinido"
    return PARTIDO_CAMPO.get(partido.upper(), "indefinido")


def _rodadas(bloco: dict) -> list[str]:
    rod = bloco.get("rodadas")
    if isinstance(rod, dict):
        return [k for k, v in rod.items() if isinstance(v, (dict, list))]
    return []


def ultima(bloco: dict | None) -> tuple[str | None, dict | None]:
    """Rodada mais recente de um bloco com `rodadas` ou `valores`."""
    if not bloco:
        return None, None
    rods = _rodadas(bloco)
    if rods:
        return rods[-1], bloco["rodadas"][rods[-1]]
    if isinstance(bloco.get("valores"), dict):
        return bloco.get("rodada") or bloco.get("coluna"), bloco["valores"]
    return None, None


def primeira(bloco: dict | None) -> tuple[str | None, dict | None]:
    bloco = bloco or {}
    rods = _rodadas(bloco)
    if rods:
        return rods[0], bloco["rodadas"][rods[0]]
    return None, None


def coluna_ultima(col: dict) -> tuple[str | None, dict | None]:
    """Rodada mais recente de uma coluna de cruzamento."""
    if isinstance(col.get("valores"), dict):
        return "valores", col["valores"]
    chaves = [k for k, v in col.items() if k not in META and isinstance(v, dict)]
    if not chaves:
        return None, None
    return chaves[-1], col[chaves[-1]]


def coluna_primeira(col: dict) -> tuple[str | None, dict | None]:
    chaves = [k for k, v in col.items() if k not in META and isinstance(v, dict)]
    if len(chaves) < 2:
        return None, None
    return chaves[0], col[chaves[0]]


def normaliza(valores: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for k, v in valores.items():
        if v is None or not isinstance(v, (int, float)):
            continue
        c = canon(k)
        out[c] = out.get(c, 0.0) + float(v)
    return out


def agrupa(v: dict[str, float]) -> dict[str, float]:
    """F, L, terceira via de direita, esquerda menor, indecisos, branco/nulo."""
    tdir = sum(v.get(k, 0.0) for k in TERCEIRA_DIREITA)
    tesq = sum(v.get(k, 0.0) for k in ESQUERDA_MENOR)
    outros = v.get("Outros", 0.0)
    return {
        "F": v.get("Flávio", 0.0),
        "L": v.get("Lula", 0.0),
        "Tdir": tdir
        + outros,  # "Outros" agregado so aparece quando falta a lista completa
        "Tesq": tesq,
        "T": tdir + tesq + outros,
        "I": v.get("Indecisos", 0.0),
        "B": v.get("Branco/nulo", 0.0),
    }


def n_candidatos(v: dict) -> int:
    return sum(1 for k in normaliza(v) if k not in PRINCIPAIS + NAO_ESCOLHA)


def carrega_quaest() -> dict[str, dict]:
    out = {}
    for path in sorted(QUAEST.glob("*.json")):
        d = json.loads(path.read_text(encoding="utf-8"))
        out[d["uf"]] = d
    return out


def carrega_outros() -> list[dict]:
    out = []
    for path in sorted(OUTROS.glob("*.json")):
        if path.name.startswith("_"):
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        d["_arquivo_json"] = path.name
        out.append(d)
    return out


def pres_1t_quaest(d: dict) -> dict:
    """Escolhe a melhor lista do 1o turno presidencial de uma transcricao Quaest.

    Preferencia: a lista completa da rodada mais recente; nas ondas de agosto,
    o cenario sem Marcal, que e o mais proximo da cedula atual (o PRTB trocou
    Marcal por Leonardo Avalanche). Devolve rodada, pagina, valores e a serie
    agregada (F, L, T, I, B) de todas as rodadas do grafico de evolucao.
    """
    candidatos = []
    for chave in ("pres_1t_lista", "pres_1t_cenario_ii", "pres_1t"):
        bloco = d.get(chave)
        if not bloco:
            continue
        rod, val = ultima(bloco)
        if val:
            candidatos.append((chave, bloco, rod, val))
    if not candidatos:
        raise ValueError(f"{d['uf']}: sem 1o turno presidencial")
    # Rodada mais recente entre os blocos; dentro dela, a lista com mais nomes.
    ordem = {c[0]: i for i, c in enumerate(candidatos)}
    serie_bloco = d.get("pres_1t") or candidatos[0][1]
    rods_serie = _rodadas(serie_bloco)
    alvo = rods_serie[-1] if rods_serie else candidatos[0][2]
    melhores = [c for c in candidatos if c[2] == alvo] or candidatos
    if "pres_1t_cenario_ii" in d:
        melhores = [c for c in melhores if c[0] != "pres_1t"] or melhores
    chave, bloco, rod, val = max(
        melhores, key=lambda c: (n_candidatos(c[3]), -ordem[c[0]])
    )
    serie, serie_valores = [], []
    fonte_serie = (
        d.get("pres_1t_cenario_ii") if chave == "pres_1t_cenario_ii" else serie_bloco
    ) or {}
    for r in _rodadas(fonte_serie):
        serie.append({"rodada": r, **agrupa(normaliza(fonte_serie["rodadas"][r]))})
        serie_valores.append(
            {"rodada": r, "valores": normaliza(fonte_serie["rodadas"][r])}
        )
    return {
        "bloco": chave,
        "rodada": rod,
        "pagina": bloco.get("pagina"),
        "cenario": bloco.get("cenario"),
        "valores": normaliza(val),
        "grupos": agrupa(normaliza(val)),
        "serie": serie,
        "serie_valores": serie_valores,
    }


def pres_2t_quaest(d: dict) -> dict | None:
    bloco = d.get("pres_2t")
    if not bloco:
        return None
    rod, val = ultima(bloco)
    if not val:
        return None
    v = normaliza(val)
    serie = [{"rodada": r, **normaliza(bloco["rodadas"][r])} for r in _rodadas(bloco)]
    return {"rodada": rod, "pagina": bloco.get("pagina"), "valores": v, "serie": serie}


def cruzamento(d: dict, chave: str) -> dict | None:
    """Cruzamento presidente x (governador | comparecimento | identificacao ...)."""
    bloco = d.get(chave)
    if not bloco or "colunas" not in bloco:
        return None
    cols = {}
    for nome, col in bloco["colunas"].items():
        rod, val = coluna_ultima(col)
        if not val:
            continue
        rod0, val0 = coluna_primeira(col)
        cols[nome] = {
            "rodada": rod,
            "me": col.get("me"),
            "valores": normaliza(val),
            "grupos": agrupa(normaliza(val)),
            "anterior": (
                {"rodada": rod0, "grupos": agrupa(normaliza(val0))} if val0 else None
            ),
        }
    return {"pagina": bloco.get("pagina"), "colunas": cols}


def governador_1t(d: dict) -> dict | None:
    """Lista de governador da rodada mais recente, com partido e campo."""
    bloco = d.get("governador_1t_lista") or d.get("governador_1t")
    if not bloco:
        return None
    rod, val = ultima(bloco)
    lista = []
    cands = bloco.get("candidatos") or []
    if val is None and cands and "valor" not in cands[0]:
        # Lista com uma coluna por rodada: {"nome", "partido", "Ago 26": .., "24 Set": ..}
        rodadas = [k for k in cands[0] if k not in ("nome", "partido")]
        rod = rodadas[-1]
        lista = [(c["nome"], c.get("partido"), c.get(rod)) for c in cands]
        val = (d.get("governador_1t") or {}).get("rodadas", {}).get(rod) or {}
    elif isinstance(val, list):
        lista = [(c["nome"], c.get("partido"), c.get("valor")) for c in val]
    elif isinstance(val, dict) and not lista:
        for k, v in val.items():
            if (
                canon(k) in NAO_ESCOLHA
                or k == "Outros"
                or not isinstance(v, (int, float))
            ):
                continue
            lista.append((re.sub(r"\s*\(.*\)$", "", k), partido_de(k), v))
    if not any(p for _, p, _ in lista) and d.get("governador_1t", {}).get("candidatos"):
        partidos = {
            c["nome"]: c.get("partido") for c in d["governador_1t"]["candidatos"]
        }
        lista = [(n, partidos.get(n), v) for n, _, v in lista]
    extra = normaliza(val) if isinstance(val, dict) else {}
    base = d.get("governador_1t", {})
    return {
        "rodada": rod,
        "pagina": bloco.get("pagina"),
        "candidatos": [
            {"nome": n, "partido": p, "valor": v, "campo": campo_de(p)}
            for n, p, v in sorted(lista, key=lambda x: -(x[2] or 0))
        ],
        "Indecisos": extra.get("Indecisos", base.get("Indecisos")),
        "Branco/nulo": extra.get("Branco/nulo", base.get("Branco/nulo")),
    }


def senado_1t(d: dict) -> dict | None:
    """Senado, media das duas vagas, rodada mais recente."""
    bloco = d.get("senado_1t")
    if not bloco:
        return None
    lista, ind, bn, pagina, rod = [], None, None, bloco.get("pagina"), None
    if "colunas" in bloco:
        col = bloco["colunas"].get("Combinação votos totais") or next(
            iter(bloco["colunas"].values())
        )
        lista = [
            (c["nome"], c.get("partido"), c.get("valor"))
            for c in col.get("candidatos", [])
        ]
        ind, bn = col.get("Indecisos"), col.get("Branco/nulo")
    else:
        rod, val = ultima(bloco)
        if isinstance(val, dict):
            for k, v in val.items():
                ck = canon(k)
                if ck == "Indecisos":
                    ind = v
                elif ck == "Branco/nulo":
                    bn = v
                elif k != "Outros" and isinstance(v, (int, float)):
                    lista.append((re.sub(r"\s*\(.*\)$", "", k), partido_de(k), v))
        if not lista and bloco.get("candidatos"):
            lista = [
                (c["nome"], c.get("partido"), c.get("valor"))
                for c in bloco["candidatos"]
            ]
            ind, bn = bloco.get("Indecisos"), bloco.get("Branco/nulo")
        if lista and not any(p for _, p, _ in lista) and bloco.get("candidatos"):
            partidos = {c["nome"]: c.get("partido") for c in bloco["candidatos"]}
            lista = [(n, partidos.get(n), v) for n, _, v in lista]
    return {
        "rodada": rod,
        "pagina": pagina,
        "candidatos": [
            {"nome": n, "partido": p, "valor": v, "campo": campo_de(p)}
            for n, p, v in sorted(lista, key=lambda x: -(x[2] or 0))
            if v is not None
        ],
        "Indecisos": ind,
        "Branco/nulo": bn,
    }


def definitiva(d: dict) -> dict:
    bloco = d.get("pres_definitiva_por_candidato") or {}
    out = {}
    for nome, col in (bloco.get("colunas") or {}).items():
        rod, val = coluna_ultima(col)
        rod0, val0 = coluna_primeira(col)
        if val:
            out[canon(nome)] = {
                "rodada": rod,
                "definitiva": val.get("É definitiva"),
                "pode_mudar": val.get("Pode mudar"),
                "anterior": (val0.get("É definitiva") if val0 else None),
                "rodada_anterior": rod0,
            }
    return {"pagina": bloco.get("pagina"), "candidatos": out}


def comparecimento(d: dict) -> dict | None:
    bloco = d.get("comparecimento")
    if not bloco:
        return None
    _, val = ultima(bloco)
    return {"pagina": bloco.get("pagina"), "valores": val}


def simples(d: dict, chave: str) -> dict | None:
    bloco = d.get(chave)
    if not bloco:
        return None
    rod, val = ultima(bloco)
    return (
        {"pagina": bloco.get("pagina"), "rodada": rod, "valores": val} if val else None
    )
