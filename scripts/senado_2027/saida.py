"""Monta `docs/assets/senado_2027.json` e `docs/assets/senado_2027.csv` (seção 4).

Junta elenco, fatos copiados dos JSON, scores da régua, simulação, rankings,
agregados e o teste da PEC 8/2021. Todo número publicado sai daqui, com no
máximo uma casa decimal; a página não recalcula nada.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import base as B
from . import scores as S
from . import simulacao as M
from .scores import r1

CAMPOS_COPIADOS = (
    "slug",
    "nome",
    "partido",
    "uf",
    "mandato",
    "bloco",
    "bloco_justificativa",
    "alinhado_governo_lula",
    "votacao_2026",
    "casos",
    "sinais_contrapeso",
    "nota_editorial",
    "scores_anteriores",
    "verificado_em",
)
VOTOS_PEC8 = {
    "voto_pec8_sim": "sim",
    "voto_pec8_nao": "nao",
    "voto_pec8_ausente": "ausente",
}
COLUNAS_CSV = (
    "cadeira",
    "uf",
    "slug",
    "nome",
    "partido",
    "mandato",
    "bloco",
    "alinhado_governo_lula",
    "n_casos",
    "maior_estagio",
    "tipos_de_caso",
    "K",
    "K_patrimonial_ativo",
    "confianca",
    "incerteza_pp",
    "C_imp_flavio",
    "C_pec_flavio",
    "C_imp_lula",
    "C_pec_lula",
    "contingencia",
    "ocupante_lula",
    "C_imp_ocupante_lula",
    "C_pec_ocupante_lula",
    "voto_pec8",
)


def _compacto(pontos: dict[str, dict]) -> dict:
    """Scores de uma pessoa sem repetir K nos dois cenários."""
    flavio = pontos["flavio"]
    return {
        "K": flavio["K"],
        "K_bruto": flavio["K_bruto"],
        "K_por_caso": flavio["K_por_caso"],
        "K_patrimonial_ativo": flavio["K_patrimonial_ativo"],
        "confianca": flavio["confianca"],
        "incerteza_pp": flavio["incerteza_pp"],
        "cenarios": {
            cenario: {
                "C_imp": pontos[cenario]["C_imp"],
                "C_pec": pontos[cenario]["C_pec"],
                "ajustes": pontos[cenario]["ajustes"],
            }
            for cenario in B.CENARIOS
        },
    }


def _pessoa(pessoa: dict, pontos: dict[str, dict], origem: str) -> dict:
    registro = {campo: pessoa.get(campo) for campo in CAMPOS_COPIADOS}
    registro["origem"] = origem
    registro["scores"] = _compacto(pontos)
    return registro


def voto_pec8(pessoa: dict) -> str | None:
    """Voto registrado na PEC 8/2021; sim e não juntos viram `dividido`."""
    votos = {
        VOTOS_PEC8[s["tipo"]]
        for s in pessoa.get("sinais_contrapeso") or []
        if s["tipo"] in VOTOS_PEC8
    }
    if {"sim", "nao"} <= votos:
        return "dividido"
    for voto in ("sim", "nao", "ausente"):
        if voto in votos:
            return voto
    return None


def fisher_bilateral(a: int, b: int, c: int, d: int) -> float:
    """p bilateral do teste exato de Fisher na tabela [[a, b], [c, d]]."""
    linha1, coluna1, total = a + b, a + c, a + b + c + d
    if total == 0:
        return 1.0

    def prob(x: int) -> float:
        return (
            math.comb(coluna1, x)
            * math.comb(total - coluna1, linha1 - x)
            / math.comb(total, linha1)
        )

    observada = prob(a)
    menor = max(0, linha1 + coluna1 - total)
    maior = min(linha1, coluna1)
    return min(
        1.0,
        sum(
            prob(x)
            for x in range(menor, maior + 1)
            if prob(x) <= observada * (1 + 1e-9)
        ),
    )


def _maior_estagio(pontos: dict) -> str | None:
    casos = pontos["K_por_caso"]
    if not casos:
        return None
    return max(casos, key=lambda x: x["pontos"])["estagio"]


def _media(valores: list[float]) -> float | None:
    return r1(sum(valores) / len(valores)) if valores else None


def _ranking(linhas: list[dict], chave: str) -> list[dict]:
    ordenadas = sorted(
        linhas, key=lambda x: (-x[chave], B.normalizar(x["nome"]), x["slug"])
    )
    return [
        {
            "posicao": i,
            "cadeira": x["cadeira"],
            "slug": x["slug"],
            "nome": x["nome"],
            "uf": x["uf"],
            "bloco": x["bloco"],
            "valor": x[chave],
        }
        for i, x in enumerate(ordenadas, start=1)
    ]


def _linhas_ocupantes(
    dados: B.Dados, pontos: dict[str, dict], cenario: str
) -> list[dict]:
    linhas = []
    for cad, pessoa in zip(
        dados.cadeiras, B.ocupantes(dados, cenario, "base"), strict=True
    ):
        if pessoa is None:
            continue
        p = pontos[pessoa["slug"]][cenario]
        linhas.append(
            {
                "cadeira": cad["cadeira"],
                "slug": pessoa["slug"],
                "nome": pessoa["nome"],
                "uf": pessoa["uf"],
                "bloco": pessoa["bloco"],
                "K": p["K"],
                "C_imp": p["C_imp"],
                "C_pec": p["C_pec"],
                "casos": pessoa.get("casos") or [],
            }
        )
    return linhas


def agregados_bloco(linhas: list[dict]) -> dict:
    saida = {}
    for bloco in B.BLOCOS:
        grupo = [x for x in linhas if x["bloco"] == bloco]
        saida[bloco] = {
            "cadeiras": len(grupo),
            "K_medio": _media([x["K"] for x in grupo]),
            "K_positivo": sum(1 for x in grupo if x["K"] > 0),
            "C_imp_medio": _media([x["C_imp"] for x in grupo]),
            "C_pec_medio": _media([x["C_pec"] for x in grupo]),
            "votos_esperados_imp": r1(sum(x["C_imp"] for x in grupo) / 100),
            "votos_esperados_pec": r1(sum(x["C_pec"] for x in grupo) / 100),
        }
    return saida


def agregados_tipo(linhas: list[dict]) -> dict:
    """Por tipo de caso, sobre os ocupantes do cenário (um senador conta em cada tipo)."""
    ativos = set(S.REGUA["C"]["redutor_patrimonial"]["estagios_ativos"])
    saida = {}
    for tipo in B.TIPOS_CASO:
        casos = [(x, c) for x in linhas for c in x["casos"] if c["tipo"] == tipo]
        senadores = {x["slug"]: x for x, _ in casos}
        com_ativo = {x["slug"] for x, c in casos if c["estagio"] in ativos}
        grupo = list(senadores.values())
        saida[tipo] = {
            "casos": len(casos),
            "senadores": len(grupo),
            "senadores_estagio_ativo": len(com_ativo),
            "por_estagio": dict(Counter(c["estagio"] for _, c in casos)),
            "K_medio": _media([x["K"] for x in grupo]),
            "C_imp_medio": _media([x["C_imp"] for x in grupo]),
            "C_pec_medio": _media([x["C_pec"] for x in grupo]),
        }
    sem = [x for x in linhas if not x["casos"]]
    saida["sem_caso"] = {
        "senadores": len(sem),
        "C_imp_medio": _media([x["C_imp"] for x in sem]),
        "C_pec_medio": _media([x["C_pec"] for x in sem]),
    }
    return saida


def teste_pec8(dados: B.Dados, pontos: dict[str, dict]) -> dict:
    """Quem do elenco de 2027 tem voto registrado na PEC 8/2021, cruzado com K."""
    titulares = {cad["slug"] for cad in dados.cadeiras}
    senadores = []
    for pessoa in dados.pessoas():
        voto = voto_pec8(pessoa)
        if voto is None:
            continue
        p = pontos[pessoa["slug"]]["flavio"]
        tipos = sorted({c["tipo"] for c in pessoa.get("casos") or []})
        senadores.append(
            {
                "slug": pessoa["slug"],
                "nome": pessoa["nome"],
                "uf": pessoa["uf"],
                "bloco": pessoa["bloco"],
                "papel": "titular" if pessoa["slug"] in titulares else "substituto",
                "voto": voto,
                "K": p["K"],
                "K_positivo": p["K"] > 0,
                "K_patrimonial_ativo": p["K_patrimonial_ativo"],
                "tipos_de_caso": tipos,
            }
        )
    votos = ("sim", "nao", "ausente", "dividido")
    tabela_k = {
        v: {
            "K_positivo": sum(
                1 for x in senadores if x["voto"] == v and x["K_positivo"]
            ),
            "K_zero": sum(
                1 for x in senadores if x["voto"] == v and not x["K_positivo"]
            ),
        }
        for v in votos
    }
    tabela_tipo = {
        v: {
            **{
                t: sum(
                    1 for x in senadores if x["voto"] == v and t in x["tipos_de_caso"]
                )
                for t in B.TIPOS_CASO
            },
            "sem_caso": sum(
                1 for x in senadores if x["voto"] == v and not x["tipos_de_caso"]
            ),
        }
        for v in votos
    }
    a, b = tabela_k["sim"]["K_positivo"], tabela_k["sim"]["K_zero"]
    c, d = tabela_k["nao"]["K_positivo"], tabela_k["nao"]["K_zero"]

    def pct(x: int, y: int) -> float | None:
        return r1(100 * x / y) if y else None

    return {
        "senadores": senadores,
        "tabela_K": tabela_k,
        "tabela_tipo": tabela_tipo,
        "nota_tabela_tipo": "Senador com casos de mais de um tipo conta em cada tipo.",
        "sim_entre_K_positivo_pct": pct(a, a + c),
        "sim_entre_K_zero_pct": pct(b, b + d),
        "p_fisher_bilateral_pct": r1(100 * fisher_bilateral(a, b, c, d)),
    }


def _contingencia_txt(cad: dict) -> str:
    cont = cad.get("contingencia")
    if not cont:
        return ""
    sub = cont.get("substituto") or {}
    return f"{cont['tipo']}: {sub['nome']}" if sub.get("nome") else cont["tipo"]


def linhas_csv(resultado: dict) -> list[dict]:
    """Uma linha por cadeira, com o titular e o ocupante do cenário Lula."""
    pessoas = {}
    for item in resultado["elenco"]:
        for papel in ("titular", "substituto"):
            if item[papel]:
                pessoas[item[papel]["slug"]] = item[papel]
    linhas = []
    for item in resultado["elenco"]:
        t = item["titular"]
        sc = t["scores"]
        ocupante = pessoas[item["ocupante"]["lula"]]
        oc = ocupante["scores"]["cenarios"]["lula"]
        tipos = sorted({c["tipo"] for c in t["casos"] or []})
        linhas.append(
            {
                "cadeira": item["cadeira"],
                "uf": item["uf"],
                "slug": t["slug"],
                "nome": t["nome"],
                "partido": t["partido"],
                "mandato": t["mandato"],
                "bloco": t["bloco"],
                "alinhado_governo_lula": str(t["alinhado_governo_lula"]).lower(),
                "n_casos": len(t["casos"] or []),
                "maior_estagio": _maior_estagio(sc) or "",
                "tipos_de_caso": "|".join(tipos),
                "K": sc["K"],
                "K_patrimonial_ativo": sc["K_patrimonial_ativo"],
                "confianca": sc["confianca"],
                "incerteza_pp": sc["incerteza_pp"],
                "C_imp_flavio": sc["cenarios"]["flavio"]["C_imp"],
                "C_pec_flavio": sc["cenarios"]["flavio"]["C_pec"],
                "C_imp_lula": sc["cenarios"]["lula"]["C_imp"],
                "C_pec_lula": sc["cenarios"]["lula"]["C_pec"],
                "contingencia": item["contingencia_txt"],
                "ocupante_lula": ocupante["slug"],
                "C_imp_ocupante_lula": oc["C_imp"],
                "C_pec_ocupante_lula": oc["C_pec"],
                "voto_pec8": voto_pec8(t) or "",
            }
        )
    return linhas


def montar(
    dados: B.Dados,
    *,
    sorteios: int | None = None,
    semente: int | None = None,
    gerado_em: str | None = None,
) -> dict:
    """Dicionário final de `docs/assets/senado_2027.json`."""
    B.exigir_valido(dados)
    pontos = {p["slug"]: S.pontuar_cenarios(p) for p in dados.pessoas()}

    elenco = []
    for cad in dados.cadeiras:
        titular = dados.senadores[cad["slug"]]
        substituto = dados.substitutos.get(cad["cadeira"])
        tipo = (cad.get("contingencia") or {}).get("tipo")
        ocupante_lula = (
            substituto["slug"]
            if tipo in B.CONTINGENCIA_EXERCICIO and substituto
            else titular["slug"]
        )
        elenco.append(
            {
                "cadeira": cad["cadeira"],
                "uf": cad["uf"],
                "contingencia": cad.get("contingencia"),
                "contingencia_txt": _contingencia_txt(cad),
                "ocupante": {"flavio": titular["slug"], "lula": ocupante_lula},
                "titular": _pessoa(
                    titular, pontos[titular["slug"]], dados.origem[titular["slug"]]
                ),
                "substituto": (
                    _pessoa(
                        substituto,
                        pontos[substituto["slug"]],
                        dados.origem[substituto["slug"]],
                    )
                    if substituto
                    else None
                ),
            }
        )

    simulacao = M.rodar(dados, pontos, sorteios=sorteios, semente=semente)
    por_cenario = {c: _linhas_ocupantes(dados, pontos, c) for c in B.CENARIOS}
    resultado = {
        "gerado_em": gerado_em
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "referencia": dados.elenco.get("referencia"),
        "regua": S.regua_publicavel(),
        "elenco": elenco,
        "simulacao": simulacao,
        "ranking": {
            "C_imp": {c: _ranking(por_cenario[c], "C_imp") for c in B.CENARIOS},
            "C_pec": {c: _ranking(por_cenario[c], "C_pec") for c in B.CENARIOS},
            "K": _ranking(por_cenario["flavio"], "K"),
        },
        "agregados": {
            "por_bloco": {c: agregados_bloco(por_cenario[c]) for c in B.CENARIOS},
            "por_tipo_de_caso": {c: agregados_tipo(por_cenario[c]) for c in B.CENARIOS},
        },
        "teste_pec8": teste_pec8(dados, pontos),
        "contexto": dados.contexto,
        "arbitragem": dados.arbitragem,
        "validacao": {"erros": list(dados.erros), "avisos": list(dados.avisos)},
        "hashes_sha256": dict(sorted(dados.arquivos.items())),
    }
    return resultado


def gravar(resultado: dict, caminho_json: Path) -> tuple[Path, Path]:
    """Grava o JSON e o CSV de mesmo nome; devolve os dois caminhos."""
    caminho_json = Path(caminho_json)
    caminho_json.parent.mkdir(parents=True, exist_ok=True)
    caminho_json.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    caminho_csv = caminho_json.with_suffix(".csv")
    with caminho_csv.open("w", encoding="utf-8", newline="") as arq:
        escritor = csv.DictWriter(arq, fieldnames=COLUNAS_CSV, lineterminator="\n")
        escritor.writeheader()
        escritor.writerows(linhas_csv(resultado))
    return caminho_json, caminho_csv
