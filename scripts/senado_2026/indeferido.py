"""Registro indeferido: alerta, cenários do estado e efeito no Senado de 2027.

A central mantém a candidatura: a decisão ainda pode ser revista e o nome segue
na urna. Cada caso de `base.REGISTRO_INDEFERIDO` cuja candidatura está na média
do estado ganha um alerta, lido do `fonte.json` arquivado, e dois cenários
sobre os mesmos sorteios da central:

- voto nulo: a candidatura sai e os válidos das demais são renormalizados;
- migração: o voto dela vai para as demais candidaturas do mesmo grupo de
  campos (`senado.GRUPOS`), na proporção do voto de cada uma no sorteio.

Em 2027 só as duas vagas do estado mudam; os outros estados, inclusive os sem
pesquisa, ficam como na central.
"""

from __future__ import annotations

import hashlib
import re
from datetime import date
from pathlib import Path

import numpy as np

from . import base as B
from . import motor as M
from . import senado as S

MARCADOR = "registro indeferido"
ORGAO_PADRAO = "TSE"
HIPOTESE_NULO = (
    "voto da candidatura vira nulo (não migra para ninguém); o restante é "
    "recalculado nos mesmos sorteios"
)
CHAVES_COMPOSICAO = (
    "p_maioria_direita_mais_centro_direita",
    "p_49_direita_centro_direita",
    "p_54_bloco_oposicao",
    "p_41_direita_centro_direita_centro",
    "p_41_esquerda_centro_esquerda",
    "p_49_esquerda_centro_esquerda",
    "p_54_esquerda_centro_esquerda",
)
REGRA = (
    "Registro indeferido sem decisão definitiva (REGISTRO_INDEFERIDO em "
    "scripts/senado_2026/base.py): a central mantém a candidatura, porque o nome "
    "segue na urna e a decisão ainda pode ser revista. O estado ganha um alerta "
    "com as matérias arquivadas e dois cenários sobre os mesmos sorteios da "
    "central: no primeiro o voto da candidatura é nulo e sai dos válidos; no "
    "segundo migra para as demais candidaturas do mesmo grupo (direita e "
    "centro-direita, centro, ou esquerda e centro-esquerda), na proporção do voto "
    "de cada uma no sorteio. Em senado_2027.cenarios só as duas vagas do estado "
    "mudam; os demais estados, inclusive os sem pesquisa, ficam como na central."
)


# ------------------------------------------------------------------ utilidades


def _dia_mes(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day:02d}/{d.month:02d}"


def _caminho(relativo: str) -> Path:
    """Caminho do repositório; caminho absoluto continua absoluto."""
    return B.ROOT / relativo


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _lista(nomes: list[str]) -> str:
    if len(nomes) <= 1:
        return "".join(nomes)
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


def grupo_de(campo: str) -> str:
    return next(g for g, membros in S.GRUPOS.items() if campo in membros)


def texto_grupo(grupo: str) -> str:
    return " e ".join(S.GRUPOS[grupo])


def ler_fonte(entrada: dict) -> dict:
    """`fonte.json` da decisão, com o SHA-256 de cada matéria conferido no disco.

    Sem o `fonte.json`, ou com hash divergente, o motor para. Matéria ausente do
    disco fica registrada como não conferida (`sha256_conferido` nulo).
    """
    caminho = _caminho(entrada["fonte"])
    dados = B.ler_json(caminho)
    materias = []
    for m in dados.get("materias") or []:
        arquivo = m.get("arquivo")
        conferido = None
        if arquivo and _caminho(arquivo).exists():
            conferido = sha256(_caminho(arquivo)) == m.get("sha256")
            if not conferido:
                raise ValueError(
                    f"SHA-256 divergente em {arquivo}, declarado em {entrada['fonte']}"
                )
        materias.append(
            {
                "veiculo": m.get("veiculo"),
                "publicado_em": m.get("publicado_em"),
                "url": m.get("url"),
                "titulo": m.get("titulo"),
                "arquivo": arquivo,
                "sha256": m.get("sha256"),
                "sha256_conferido": conferido,
            }
        )
    return {
        "arquivo": entrada["fonte"],
        "sha256": sha256(caminho),
        "fatos": dados.get("fatos") or [],
        "materias": materias,
    }


def _sem_conferencia(m: dict) -> dict:
    return {k: v for k, v in m.items() if k != "sha256_conferido"}


def _principal(materias: list[dict], data: str) -> dict:
    """Primeira matéria publicada no dia da decisão ou depois; senão a primeira."""
    depois = [m for m in materias if (m.get("publicado_em") or "")[:10] >= data]
    return (depois or materias or [{}])[0]


# ------------------------------------------------------------------- cenários


def _centrais(validos: list[float], idx: int, receptores: list[int]) -> list[float]:
    """Válidos da média central sem a candidatura `idx`, com a mesma regra do
    sorteio: migração proporcional aos receptores ou voto nulo."""
    vd = validos[idx]
    w = list(validos)
    soma = sum(validos[j] for j in receptores)
    if receptores and soma > 0:
        for j in receptores:
            w[j] = validos[j] * (1 + vd / soma)
        total = 100.0
    else:
        total = 100.0 - vd
    fator = 100.0 / total if total > 0 else 0.0
    return [x * fator for j, x in enumerate(w) if j != idx]


def _cenario(
    prep: dict, sorteio: dict, idx: int, receptores: list[int], textos: dict
) -> tuple[dict, tuple[np.ndarray, np.ndarray]]:
    cands = prep["candidatos"]
    resto = [c for j, c in enumerate(cands) if j != idx]
    novo = M.sem_candidatura(sorteio, idx, receptores)
    resumo = M.resumir_estado(novo, [c["nome"] for c in resto])
    centrais = _centrais([c["validos"] for c in cands], idx, receptores)
    probs = M.linhas_probabilidade(resto, resumo, centrais)
    modal = M.dupla_modal(resumo, probs)
    manter = np.delete(np.arange(len(cands)), idx)
    campos_idx = sorteio["campos_idx"][manter]
    partidos_idx = sorteio["partidos_idx"][manter]
    assentos = (campos_idx[novo["eleitos"]], partidos_idx[novo["eleitos"]])
    saida = {
        **textos,
        "candidatura": cands[idx]["nome"],
        "receptores": [cands[j]["nome"] for j in receptores],
        "probabilidades": probs,
        "eleitos_provaveis": modal["dupla"],
        "dupla_mais_provavel": modal["dupla"],
        "p_dupla_mais_provavel": modal["p"],
        "p_segunda_dupla": modal["p_segunda"],
        "dupla_empatada": modal["empatada"],
        "duplas": modal["duplas"],
        "soma_p_eleito": sum(resumo["p_eleito"]),
    }
    return saida, assentos


def _textos(
    cand: dict, curto: str, entrada: dict, grupo: str, receptores: list[str]
) -> tuple[dict, dict]:
    """Rótulo, descrição e hipótese dos dois cenários, gerados do caso."""
    orgao = entrada.get("orgao") or ORGAO_PADRAO
    nome, quando = cand["nome"], _dia_mes(entrada["data"])
    chave = "registro_indeferido_" + re.sub(r"[^a-z0-9]+", "_", B.normalizar(curto))
    gtxt = texto_grupo(grupo)
    nulo = {
        "chave": chave,
        "rotulo": f"Se os votos de {curto} forem anulados",
        "descricao": (
            f"O {orgao} indeferiu o registro de {nome} em {quando}, em decisão "
            f"{entrada['status']}. Se a decisão prevalecer, o voto dado à "
            "candidatura é nulo: ela sai da disputa pelas duas vagas e os válidos "
            "das demais são recalculados sem esse voto."
        ),
        "hipotese": HIPOTESE_NULO,
    }
    if receptores:
        destino = (
            f"o voto vai para {_lista(receptores)} ({gtxt}), na proporção do voto "
            "de cada candidatura no mesmo sorteio."
        )
    else:
        destino = (
            f"como não há outra candidatura de {gtxt} na média do estado, o voto "
            "vira nulo e o cenário repete o anterior."
        )
    migracao = {
        "chave": chave + "_migracao",
        "rotulo": f"Se o eleitorado de {curto} migrar para candidaturas de {gtxt}",
        "descricao": (
            f"Mesmo indeferimento, mas o eleitorado de {nome} troca de número: "
            + destino
        ),
        "hipotese": (
            f"voto da candidatura migra para as demais candidaturas de {gtxt}, na "
            "proporção do voto de cada uma no mesmo sorteio (regra de voto útil); "
            "nada vai para outros campos, branco ou nulo; o restante é recalculado "
            "nos mesmos sorteios"
        ),
    }
    return nulo, migracao


def _alerta(cand: dict, entrada: dict, fonte: dict, grupo: str) -> dict:
    orgao = entrada.get("orgao") or ORGAO_PADRAO
    nome = cand["nome"]
    return {
        "titulo": f"Registro indeferido pelo {orgao} em {_dia_mes(entrada['data'])}",
        "candidato": nome,
        "marcador": MARCADOR,
        "texto": (
            f"{entrada['decisao']} É decisão {entrada['status']}. O nome e o "
            f"número de {nome} continuam na urna. Por isso a central desta página "
            "mantém a candidatura: enquanto a decisão puder ser revista, os votos "
            "ainda podem ser validados. A manutenção é hipótese declarada; os dois "
            "cenários do estado mostram o resultado com os votos anulados e com o "
            "eleitorado da candidatura migrando para candidaturas de "
            f"{texto_grupo(grupo)}."
        ),
        "data": entrada["data"],
        "status": entrada["status"],
        "fontes": [_sem_conferencia(m) for m in fonte["materias"]],
        "arquivo_fonte": fonte["arquivo"],
        "sha256_fonte": fonte["sha256"],
    }


def _nacional(
    central: dict, fixos: list[dict], uf: str, assentos: tuple, comp_central: dict
) -> dict:
    """Composição de 2027 com as duas vagas de `uf` trocadas pelo cenário."""
    trocados = {**central["assentos"], uf: assentos}
    campos, partidos = M.empilhar(trocados, central["ordem"])
    comp = S.composicao(campos, partidos, central["partidos"], fixos)
    return {
        "por_grupo": {
            g: {"esperado": v["esperado"], "ic90": v["ic90"]}
            for g, v in comp["por_grupo"].items()
        },
        "variacao_esperado_por_grupo": {
            g: comp["por_grupo"][g]["esperado"]
            - comp_central["por_grupo"][g]["esperado"]
            for g in comp["por_grupo"]
        },
        **{k: comp[k] for k in CHAVES_COMPOSICAO},
        "variacao_probabilidades": {
            k: comp[k] - comp_central[k] for k in CHAVES_COMPOSICAO
        },
        "fecha_em_81_em_todo_sorteio": comp["fecha_em_81_em_todo_sorteio"],
    }


def _motivo(prep: dict | None, central: dict, idx: int | None) -> str | None:
    if prep is None:
        return "UF fora da lista do motor"
    if prep["media"] is None:
        return "estado sem pesquisa usada na central"
    if prep["uf"] not in central["sorteios"]:
        return "estado sem sorteio na central (menos de duas candidaturas)"
    if idx is None:
        return "candidatura não está nas pesquisas usadas no estado"
    if len(prep["candidatos"]) - 1 < 2:
        return "sobrariam menos de duas candidaturas no estado"
    return None


def aplicar(
    preps: list[dict],
    central: dict,
    tabela: dict,
    tse: B.Tse,
    fixos: list[dict],
    comp_central: dict,
) -> dict:
    """Alertas e cenários por estado, cenários de 2027 e a validação.

    `central` vem de `motor.rodar` com as UFs da tabela em `guardar`.
    """
    por_uf = {p["uf"]: p for p in preps}
    estados: dict[str, dict] = {}
    nacionais: list[dict] = []
    validacao: list[dict] = []
    for (uf, nome_tabela), entrada in tabela.items():
        prep = por_uf.get(uf)
        idx = (
            B.localizar_pessoa(uf, nome_tabela, prep["media"]["pessoas"], tse)
            if prep and prep["media"]
            else None
        )
        registro = {
            "uf": uf,
            "nome_tabela": nome_tabela,
            "data": entrada["data"],
            "status": entrada["status"],
            "fonte": entrada["fonte"],
        }
        motivo = _motivo(prep, central, idx)
        if motivo or prep is None or idx is None:
            validacao.append({**registro, "aplicado": False, "motivo": motivo})
            continue
        cand = prep["candidatos"][idx]
        fonte = ler_fonte(entrada)
        grupo = grupo_de(cand["campo"])
        receptores = (
            [
                j
                for j, c in enumerate(prep["candidatos"])
                if j != idx and grupo_de(c["campo"]) == grupo
            ]
            if grupo != "indefinido"
            else []
        )
        curto = entrada.get("curto") or cand["nome"].split()[0]
        principal = _principal(fonte["materias"], entrada["data"])
        fonte_cenario = {
            "veiculo": principal.get("veiculo"),
            "publicado_em": principal.get("publicado_em"),
            "url": principal.get("url"),
            "titulo": principal.get("titulo"),
            "arquivo": principal.get("arquivo"),
            "sha256": principal.get("sha256"),
            "decisao": entrada["decisao"],
            "data": entrada["data"],
            "status": entrada["status"],
            "fonte_json": entrada["fonte"],
        }
        sorteio = central["sorteios"][uf]
        resumo = central["resumos"][uf]
        destino = estados.setdefault(uf, {"alertas": [], "cenarios": []})
        destino["alertas"].append(_alerta(cand, entrada, fonte, grupo))
        aplicados = []
        nomes_receptores = [prep["candidatos"][j]["nome"] for j in receptores]
        for textos, rec in zip(
            _textos(cand, curto, entrada, grupo, nomes_receptores),
            ([], receptores),
            strict=True,
        ):
            cen, assentos = _cenario(prep, sorteio, idx, rec, textos)
            cen["fonte"] = fonte_cenario
            destino["cenarios"].append(cen)
            nacionais.append(
                {
                    "chave": cen["chave"],
                    "rotulo": cen["rotulo"],
                    "hipotese": cen["hipotese"],
                    "ufs": [uf],
                    "candidatura": cand["nome"],
                    **_nacional(central, fixos, uf, assentos, comp_central),
                }
            )
            aplicados.append(
                {
                    "chave": cen["chave"],
                    "eleitos_provaveis": cen["eleitos_provaveis"],
                    "p_dupla_mais_provavel": cen["p_dupla_mais_provavel"],
                    "soma_p_eleito": cen["soma_p_eleito"],
                }
            )
        validacao.append(
            {
                **registro,
                "aplicado": True,
                "candidatura": cand["nome"],
                "sq_candidato": cand["sq_candidato"],
                "partido": cand["partido"],
                "campo": cand["campo"],
                "p_eleito_central": resumo["p_eleito"][idx],
                "p_primeiro_central": resumo["p_primeiro"][idx],
                "validos_central": cand["validos"],
                "receptores_migracao": nomes_receptores,
                "cenarios": aplicados,
                "sha256_fonte": fonte["sha256"],
                "materias_conferidas": [
                    {"arquivo": m["arquivo"], "sha256_conferido": m["sha256_conferido"]}
                    for m in fonte["materias"]
                ],
            }
        )
    return {"estados": estados, "senado_2027": nacionais, "validacao": validacao}
