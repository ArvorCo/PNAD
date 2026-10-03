"""Senado de 2027: os 27 eleitos em 2022 que continuam mais os 54 sorteados.

Campo é classificação editorial da casa (`PARTIDO_CAMPO` em voto_util_base:
tucano é centro-esquerda; PSD, MDB e Avante, centro; União, PP e Podemos,
centro-direita; PL, Novo e Republicanos, direita). Os 27 de 2022 são os
eleitos na urna, não os titulares atuais: suplência, licença e migração
partidária ficam fora do modelo, salvo a exceção declarada abaixo para partido
extinto.
"""

from __future__ import annotations

import numpy as np

from .base import CAMPOS, campo, sigla, titulo_urna

# Exceções de campo para quem continua: UF -> (campo, partido para a contagem,
# motivo). Só partido extinto ou incorporado; migração comum fica fora.
CAMPO_EXCECAO_2022: dict[str, tuple[str, str, str]] = {
    "MG": (
        "direita",
        "REPUBLICANOS",
        "eleito pelo PSC, incorporado ao Podemos em 2023; filiado ao Republicanos",
    ),
}

GRUPOS = {
    "direita": ("direita", "centro-direita"),
    "centro": ("centro",),
    "esquerda": ("esquerda", "centro-esquerda"),
    "indefinido": ("indefinido",),
}
CADEIRAS = 81
LIMIARES = {"maioria": 41, "tres_quintos": 49, "dois_tercos": 54}


def continuam(senadores_2022: list[dict] | None) -> list[dict]:
    saida = []
    for s in senadores_2022 or []:
        partido_eleicao = sigla(s.get("partido"))
        excecao = CAMPO_EXCECAO_2022.get(s["uf"])
        item = {
            "uf": s["uf"],
            "nome": titulo_urna(s["nome"]) if s.get("nome") else None,
            "nome_urna": s.get("nome"),
            "sq_candidato": s.get("sq_candidato"),
            "partido": partido_eleicao,
            "partido_contagem": excecao[1] if excecao else partido_eleicao,
            "campo": excecao[0] if excecao else campo(partido_eleicao),
            "votos_2022": s.get("votos"),
        }
        if excecao:
            item["nota"] = excecao[2]
        saida.append(item)
    return sorted(saida, key=lambda x: x["uf"])


def _quantis(x: np.ndarray) -> list[int]:
    q = np.quantile(x, [0.05, 0.95], method="inverted_cdf")
    return [int(q[0]), int(q[1])]


def composicao(
    campos_novos: np.ndarray,
    partidos_novos: np.ndarray,
    lista_partidos: list[str],
    fixos: list[dict],
) -> dict:
    """Agrega por sorteio.

    `campos_novos` e `partidos_novos` têm forma (sorteios, 54): índice em
    CAMPOS e em `lista_partidos` de cada cadeira sorteada.
    """
    s = campos_novos.shape[0]
    f = len(CAMPOS)
    por_campo = np.zeros((s, f), int)
    for j in range(campos_novos.shape[1]):
        por_campo[np.arange(s), campos_novos[:, j]] += 1
    novos_campo = por_campo.copy()
    cont_fixos = np.zeros(f, int)
    for c in fixos:
        cont_fixos[CAMPOS.index(c["campo"])] += 1
    por_campo += cont_fixos[None, :]
    total = por_campo.sum(axis=1)

    nomes_partidos = list(lista_partidos)
    for c in fixos:
        if c["partido_contagem"] not in nomes_partidos:
            nomes_partidos.append(c["partido_contagem"])
    p_n = len(nomes_partidos)
    por_partido = np.zeros((s, p_n), int)
    for j in range(partidos_novos.shape[1]):
        por_partido[np.arange(s), partidos_novos[:, j]] += 1
    novos_partido = por_partido.copy()
    fixos_partido = np.zeros(p_n, int)
    for c in fixos:
        fixos_partido[nomes_partidos.index(c["partido_contagem"])] += 1
    por_partido += fixos_partido[None, :]

    saida_campo = {
        nome: {
            "esperado": float(por_campo[:, i].mean()),
            "ic90": _quantis(por_campo[:, i]),
            "continuam": int(cont_fixos[i]),
            "novos_esperado": float(novos_campo[:, i].mean()),
        }
        for i, nome in enumerate(CAMPOS)
    }
    saida_grupo = {}
    soma_grupo = {}
    for grupo, membros in GRUPOS.items():
        idx = [CAMPOS.index(m) for m in membros]
        x = por_campo[:, idx].sum(axis=1)
        soma_grupo[grupo] = x
        saida_grupo[grupo] = {
            "campos": list(membros),
            "esperado": float(x.mean()),
            "ic90": _quantis(x),
            "continuam": int(cont_fixos[idx].sum()),
            "novos_esperado": float(novos_campo[:, idx].sum(axis=1).mean()),
        }
    saida_partido = {
        nome: {
            "esperado": float(por_partido[:, i].mean()),
            "ic90": _quantis(por_partido[:, i]),
            "continuam": int(fixos_partido[i]),
            "novos_esperado": float(novos_partido[:, i].mean()),
        }
        for i, nome in enumerate(nomes_partidos)
        if por_partido[:, i].max() > 0
    }
    saida_partido = dict(
        sorted(saida_partido.items(), key=lambda kv: (-kv[1]["esperado"], kv[0]))
    )
    direita = soma_grupo["direita"]
    esquerda = soma_grupo["esquerda"]
    dcc = direita + soma_grupo["centro"]
    return {
        "cadeiras": CADEIRAS,
        "fecha_em_81_em_todo_sorteio": bool((total == CADEIRAS).all()),
        "total_por_sorteio_min_max": [int(total.min()), int(total.max())],
        "por_campo": saida_campo,
        "por_grupo": saida_grupo,
        "por_partido": saida_partido,
        "p_maioria_direita_mais_centro_direita": float(
            (direita >= LIMIARES["maioria"]).mean()
        ),
        "p_49_direita_centro_direita": float(
            (direita >= LIMIARES["tres_quintos"]).mean()
        ),
        "p_54_bloco_oposicao": float((direita >= LIMIARES["dois_tercos"]).mean()),
        "p_41_direita_centro_direita_centro": float(
            (dcc >= LIMIARES["maioria"]).mean()
        ),
        "p_41_esquerda_centro_esquerda": float(
            (esquerda >= LIMIARES["maioria"]).mean()
        ),
        "p_49_esquerda_centro_esquerda": float(
            (esquerda >= LIMIARES["tres_quintos"]).mean()
        ),
        "p_54_esquerda_centro_esquerda": float(
            (esquerda >= LIMIARES["dois_tercos"]).mean()
        ),
        "distribuicao_direita_centro_direita": np.bincount(
            direita, minlength=CADEIRAS + 1
        ).tolist(),
        "distribuicao_esquerda_centro_esquerda": np.bincount(
            esquerda, minlength=CADEIRAS + 1
        ).tolist(),
        "limiares": dict(LIMIARES),
    }
