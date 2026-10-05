"""Partes puras da comparação 2022 × 2026: partidos, campos, cadeiras e regiões.

Nada aqui lê disco ou banco. Recebe dicionários já carregados e devolve números,
para que os testes rodem sem os pacotes do TSE.

Campo político segue `apuracao/public/campos.json` (a mesma tabela do telão e
do `final.json`). Partido de 2018 ou 2022 que não existe mais com a mesma sigla
herda o campo do sucessor de 2026, pela tabela `SUCESSORES` abaixo; a tabela é
declarada, e cada linha diz se o banco de 2026 confirma a sucessão pelo número
do partido ou se ela é fato público sem documento no repositório.
"""

from __future__ import annotations

import math
import unicodedata
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from .dados import GRUPO_DA_REGIAO, REGIAO_UF, bloco_de, pct

CAMPOS = ("esquerda", "centro-esquerda", "centro", "centro-direita", "direita")
BLOCOS = ("esquerda + centro-esquerda", "centro", "direita + centro-direita")
INDEFINIDO = "indefinido"


@dataclass(frozen=True)
class Sucessao:
    """Partido de 2018 ou 2022 e a sigla que o representa em 2026."""

    sigla_2026: str
    tipo: str
    descricao: str


# Siglas como o TSE grava em 2018 e 2022 (caixa alta), para a sigla de 2026
# como grava o banco da apuração (`partido.sigla`). Grafia diferente da mesma
# legenda também entra, para que as contagens por partido se juntem.
SUCESSORES: dict[str, Sucessao] = {
    "PC DO B": Sucessao(
        "PCDOB", "grafia", "mesma legenda; o TSE grafa PC do B até 2022"
    ),
    "SD": Sucessao("SOLIDARIEDADE", "grafia", "sigla antiga do Solidariedade"),
    "PATRI": Sucessao(
        "PRD", "fusão", "grafia do Patriota em 2018; Patriota e PTB formaram o PRD"
    ),
    "PATRIOTA": Sucessao("PRD", "fusão", "Patriota e PTB formaram o PRD"),
    "PTB": Sucessao("PRD", "fusão", "PTB e Patriota formaram o PRD"),
    "PROS": Sucessao(
        "SOLIDARIEDADE", "incorporação", "PROS incorporado ao Solidariedade"
    ),
    "PSC": Sucessao("PODE", "incorporação", "PSC incorporado ao Podemos"),
    "PMN": Sucessao("MOBILIZA", "renomeação", "PMN passou a se chamar Mobiliza"),
    "PMB": Sucessao(
        "DEMOCRATA",
        "renomeação inferida",
        "o número do PMB aparece em 2026 como DEMOCRATA",
    ),
    "PSL": Sucessao("UNIÃO", "fusão", "PSL e DEM formaram o União Brasil"),
    "DEM": Sucessao("UNIÃO", "fusão", "DEM e PSL formaram o União Brasil"),
    "PRB": Sucessao(
        "REPUBLICANOS", "renomeação", "PRB passou a se chamar Republicanos"
    ),
    "PR": Sucessao("PL", "renomeação", "PR voltou a se chamar PL"),
    "PPS": Sucessao("CIDADANIA", "renomeação", "PPS passou a se chamar Cidadania"),
    "PHS": Sucessao("PODE", "incorporação", "PHS incorporado ao Podemos"),
    "PRP": Sucessao(
        "PATRIOTA", "incorporação", "PRP incorporado ao Patriota, depois PRD"
    ),
    "PPL": Sucessao("PCDOB", "incorporação", "PPL incorporado ao PCdoB"),
    "PTC": Sucessao("AGIR", "renomeação", "PTC passou a se chamar Agir"),
    "PMDB": Sucessao("MDB", "renomeação", "PMDB passou a se chamar MDB"),
}


def normalizar_sigla(sigla: str | None) -> str:
    """Sigla em caixa alta, sem espaços nas pontas; vazio vira string vazia."""
    return (sigla or "").strip().upper()


def sigla_2026(sigla: str | None) -> str:
    """Sigla de 2026 que representa o partido (segue a cadeia de sucessão)."""
    atual = normalizar_sigla(sigla)
    vistos: set[str] = set()
    while atual in SUCESSORES:
        if atual in vistos:
            raise ValueError(f"ciclo na tabela de sucessores: {atual}")
        vistos.add(atual)
        atual = SUCESSORES[atual].sigla_2026
    return atual


def campo_historico(
    sigla: str | None, cl: Mapping[str, Mapping[str, str]]
) -> tuple[str, str]:
    """Campo de um partido de 2018 ou 2022 e por qual via ele foi atribuído.

    A tabela da casa vence quando lista a sigla antiga (`direto`); senão vale o
    campo do sucessor de 2026 (`sucessor`); sem nenhum dos dois, `indefinido`.
    """
    original = normalizar_sigla(sigla)
    partidos = cl["partidos"]
    if original in partidos:
        return partidos[original], "direto"
    sucessor = sigla_2026(original)
    if sucessor != original and sucessor in partidos:
        return partidos[sucessor], "sucessor"
    return INDEFINIDO, "sem classificação"


def campo_teto_direita(sigla: str | None, cl: Mapping[str, Mapping[str, str]]) -> str:
    """Sensibilidade, não regra: sigla extinta que a sucessão leva à centro-direita
    conta como direita. Dá o teto da direita de 2018 e 2022 e, portanto, o piso do
    crescimento dela; o bloco de direita e centro-direita não muda.
    """
    campo, via = campo_historico(sigla, cl)
    if via == "sucessor" and campo == "centro-direita":
        return "direita"
    return campo


def _sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in base if not unicodedata.combining(c))


def normalizar_texto(texto: str | None) -> str:
    """Caixa alta, sem acento e com espaços simples (para comparar nomes)."""
    return " ".join(_sem_acento(texto or "").upper().split())


def eleito(situacao: str | None) -> bool:
    """`DS_SIT_TOT_TURNO` que dá cadeira: ELEITO, ELEITO POR QP, ELEITO POR MÉDIA.

    NÃO ELEITO, SUPLENTE, 2º TURNO e campos nulos não dão.
    """
    return normalizar_texto(situacao).startswith("ELEITO")


def segundo_turno(situacao: str | None) -> bool:
    """`DS_SIT_TOT_TURNO` de quem foi ao 2º turno (`2º TURNO`)."""
    texto = normalizar_texto(situacao)
    return texto.startswith("2") and texto.endswith("TURNO")


def contar(itens: Iterable[str]) -> dict[str, int]:
    """Contagem em ordem decrescente, desempate alfabético."""
    contagem = Counter(itens)
    return dict(sorted(contagem.items(), key=lambda kv: (-kv[1], kv[0])))


def por_campo(campos: Iterable[str]) -> dict[str, int]:
    """Contagem nos cinco campos (zeros explícitos) mais `indefinido` se houver."""
    contagem = Counter(campos)
    saida = {c: contagem.get(c, 0) for c in CAMPOS}
    extras = sum(v for k, v in contagem.items() if k not in CAMPOS)
    if extras:
        saida[INDEFINIDO] = extras
    return saida


def por_bloco(contagem_campo: Mapping[str, int]) -> dict[str, int]:
    """Soma os campos nos três blocos usados nas bancadas."""
    saida = dict.fromkeys(BLOCOS, 0)
    for campo, n in contagem_campo.items():
        bloco = bloco_de(campo)
        saida[bloco] = saida.get(bloco, 0) + n
    return {k: v for k, v in saida.items() if v or k in BLOCOS}


def diferenca(a: Mapping[str, int], b: Mapping[str, int]) -> dict[str, int]:
    """a menos b chave a chave, na ordem de `a` seguida das chaves só de `b`."""
    chaves = list(a) + [k for k in b if k not in a]
    return {k: a.get(k, 0) - b.get(k, 0) for k in chaves}


def trocas_de_bloco(
    antes: Mapping[str, Mapping[str, int]], depois: Mapping[str, Mapping[str, int]]
) -> dict[str, Any]:
    """Cadeiras que trocaram de bloco, somando o saldo positivo de cada unidade.

    Dentro de cada UF, a contagem mínima de cadeiras que mudaram de mãos é a soma
    dos ganhos líquidos por bloco (igual à soma das perdas quando as vagas são as
    mesmas). Devolve o total, os ganhos e as perdas por bloco.
    """
    ganhos: Counter = Counter()
    perdas: Counter = Counter()
    for unidade, a in antes.items():
        d = depois[unidade]
        if sum(a.values()) != sum(d.values()):
            raise ValueError(f"{unidade}: vagas diferentes entre os anos")
        for bloco in set(a) | set(d):
            delta = d.get(bloco, 0) - a.get(bloco, 0)
            if delta > 0:
                ganhos[bloco] += delta
            elif delta < 0:
                perdas[bloco] += -delta
    return {
        "cadeiras": sum(ganhos.values()),
        "ganhos": {b: ganhos.get(b, 0) for b in BLOCOS},
        "perdas": {b: perdas.get(b, 0) for b in BLOCOS},
    }


def troca_no_segundo_turno(
    bloco_antes: str, blocos_finalistas: Iterable[str]
) -> bool | None:
    """Se o bloco do governo estadual muda com um 2º turno ainda por disputar.

    True quando nenhum finalista é do bloco anterior, False quando todos são, None
    quando depende do resultado.
    """
    iguais = [b == bloco_antes for b in blocos_finalistas]
    if not iguais:
        raise ValueError("2º turno sem finalistas")
    if not any(iguais):
        return True
    return False if all(iguais) else None


def fluxo(pares: Iterable[tuple[str, str]]) -> dict[str, dict[str, int]]:
    """Matriz origem -> destino (blocos), com zeros explícitos nos três blocos."""
    matriz = {a: dict.fromkeys(BLOCOS, 0) for a in BLOCOS}
    for origem, destino in pares:
        matriz.setdefault(origem, dict.fromkeys(BLOCOS, 0))
        matriz[origem][destino] = matriz[origem].get(destino, 0) + 1
    return matriz


# ---------------------------------------------------------------- regiões


def membros_regionais(ufs: Iterable[str]) -> dict[str, list[str]]:
    """UFs de cada agregado: grupos (NE, N, Centro-Sul), regiões, Exterior, Brasil.

    Nordeste e Norte são ao mesmo tempo grupo e região; o conjunto garante que
    cada UF entra uma vez só em cada agregado.
    """
    membros: dict[str, set[str]] = {}
    for uf in ufs:
        u = uf.upper()
        regiao = REGIAO_UF[u.lower()]
        nomes = {regiao, GRUPO_DA_REGIAO[regiao], "Brasil"}
        if u != "ZZ":
            nomes.add("Brasil sem exterior")
        for nome in nomes:
            membros.setdefault(nome, set()).add(u)
    return {nome: sorted(lista) for nome, lista in membros.items()}


def agregar(
    linhas: Mapping[str, Mapping[str, Any]],
    campos: Sequence[str],
    membros: Mapping[str, Sequence[str]],
) -> dict[str, dict[str, int]]:
    """Soma os campos numéricos das UFs de cada agregado (None conta como erro)."""
    saida: dict[str, dict[str, int]] = {}
    for nome, ufs in membros.items():
        soma = dict.fromkeys(campos, 0)
        for uf in ufs:
            linha = linhas[uf]
            for campo in campos:
                valor = linha[campo]
                if valor is None:
                    raise ValueError(f"{uf}: {campo} ausente na agregação de {nome}")
                soma[campo] += valor
        saida[nome] = soma
    return saida


# ---------------------------------------------------------------- proporcionalidade


def gallagher(
    votos_pct: Mapping[str, float], cadeiras_pct: Mapping[str, float]
) -> float:
    """Índice de mínimos quadrados de Gallagher, em pontos percentuais.

    LSq = raiz(0,5 × soma dos quadrados de votos% menos cadeiras%), sobre a união
    das chaves (partido sem cadeira entra com zero cadeira).
    """
    chaves = set(votos_pct) | set(cadeiras_pct)
    soma = sum((votos_pct.get(k, 0.0) - cadeiras_pct.get(k, 0.0)) ** 2 for k in chaves)
    return math.sqrt(0.5 * soma)


def proporcionalidade(
    votos: Mapping[str, int], cadeiras: Mapping[str, int], casas: int = 4
) -> dict[str, Any]:
    """Cadeiras contra votos por chave (partido ou campo), com o índice de Gallagher."""
    total_votos = sum(votos.values())
    total_cadeiras = sum(cadeiras.values())
    chaves = sorted(
        set(votos) | set(cadeiras),
        key=lambda k: (-cadeiras.get(k, 0), -votos.get(k, 0), k),
    )
    linhas = []
    exato_v: dict[str, float] = {}
    exato_c: dict[str, float] = {}
    for k in chaves:
        v = votos.get(k, 0)
        c = cadeiras.get(k, 0)
        exato_v[k] = 100.0 * v / total_votos if total_votos else 0.0
        exato_c[k] = 100.0 * c / total_cadeiras if total_cadeiras else 0.0
        linhas.append(
            {
                "chave": k,
                "votos": v,
                "pct_votos": round(exato_v[k], casas),
                "cadeiras": c,
                "pct_cadeiras": round(exato_c[k], casas),
                "cadeiras_menos_votos_pp": round(exato_c[k] - exato_v[k], casas),
                "votos_por_cadeira": round(v / c) if c else None,
            }
        )
    return {
        "total_votos": total_votos,
        "total_cadeiras": total_cadeiras,
        "gallagher_pp": round(gallagher(exato_v, exato_c), casas),
        "linhas": linhas,
    }


# ---------------------------------------------------------------- presidente

CAMPOS_PRES_2026 = (
    "e26",
    "c26",
    "a26",
    "vv26",
    "vb26",
    "vn26",
    "flavio",
    "lula26",
    "cury",
    "renan",
    "caiado",
    "outros26",
)
CAMPOS_PRES_2022 = (
    *(
        f"{base}_{t}"
        for t in (1, 2)
        for base in ("e22", "c22", "a22", "vv22", "vb22", "vn22", "bolsonaro", "lula22")
    ),
    "ciro_1",
    "tebet_1",
    "outros22_1",
)
CAMPOS_PRES = (*CAMPOS_PRES_2026, *CAMPOS_PRES_2022)


def _fr(parte: int, total: int) -> float:
    return parte / total if total else 0.0


def metricas_presidente(r: Mapping[str, int], casas: int = 6) -> dict[str, Any]:
    """Comparação 1º turno de 2026 contra os dois turnos de 2022 numa linha somada.

    Fatias de candidatura sobre os válidos do próprio turno; comparecimento e
    abstenção sobre o eleitorado; brancos e nulos sobre o comparecimento.
    Diferenças em pontos (2026 menos 2022) e em votos. Seis casas decimais, para
    que o texto arredonde uma vez só a partir do JSON.
    """
    terc26 = r["cury"] + r["renan"] + r["caiado"] + r["outros26"]
    terc22 = r["ciro_1"] + r["tebet_1"] + r["outros22_1"]
    f26 = {
        "flavio": _fr(r["flavio"], r["vv26"]),
        "lula": _fr(r["lula26"], r["vv26"]),
        "terceiros": _fr(terc26, r["vv26"]),
        "cury": _fr(r["cury"], r["vv26"]),
        "renan": _fr(r["renan"], r["vv26"]),
        "caiado": _fr(r["caiado"], r["vv26"]),
        "outros": _fr(r["outros26"], r["vv26"]),
        "comparecimento": _fr(r["c26"], r["e26"]),
        "abstencao": _fr(r["a26"], r["e26"]),
        "brancos": _fr(r["vb26"], r["c26"]),
        "nulos": _fr(r["vn26"], r["c26"]),
    }
    f22 = {}
    for t in (1, 2):
        f22[t] = {
            "bolsonaro": _fr(r[f"bolsonaro_{t}"], r[f"vv22_{t}"]),
            "lula": _fr(r[f"lula22_{t}"], r[f"vv22_{t}"]),
            "comparecimento": _fr(r[f"c22_{t}"], r[f"e22_{t}"]),
            "abstencao": _fr(r[f"a22_{t}"], r[f"e22_{t}"]),
            "brancos": _fr(r[f"vb22_{t}"], r[f"c22_{t}"]),
            "nulos": _fr(r[f"vn22_{t}"], r[f"c22_{t}"]),
        }
    f22[1]["terceiros"] = _fr(terc22, r["vv22_1"])
    f22[1]["ciro"] = _fr(r["ciro_1"], r["vv22_1"])
    f22[1]["tebet"] = _fr(r["tebet_1"], r["vv22_1"])
    f22[1]["outros"] = _fr(r["outros22_1"], r["vv22_1"])

    def p(x: float) -> float:
        return round(100.0 * x, casas)

    def pp(a: float, b: float) -> float:
        return round(100.0 * (a - b), casas)

    margem26 = f26["flavio"] - f26["lula"]
    margem22 = {t: f22[t]["bolsonaro"] - f22[t]["lula"] for t in (1, 2)}
    comp = {}
    for t in (1, 2):
        comp[f"vs_{t}t"] = {
            "direita_pp": pp(f26["flavio"], f22[t]["bolsonaro"]),
            "direita_votos": r["flavio"] - r[f"bolsonaro_{t}"],
            "lula_pp": pp(f26["lula"], f22[t]["lula"]),
            "lula_votos": r["lula26"] - r[f"lula22_{t}"],
            "margem_2022_pp": p(margem22[t]),
            "virada_margem_pp": pp(margem26, margem22[t]),
            "comparecimento_pp": pp(f26["comparecimento"], f22[t]["comparecimento"]),
            "comparecimento_votos": r["c26"] - r[f"c22_{t}"],
            "abstencao_pp": pp(f26["abstencao"], f22[t]["abstencao"]),
            "abstencao_votos": r["a26"] - r[f"a22_{t}"],
            "brancos_pp": pp(f26["brancos"], f22[t]["brancos"]),
            "brancos_votos": r["vb26"] - r[f"vb22_{t}"],
            "nulos_pp": pp(f26["nulos"], f22[t]["nulos"]),
            "nulos_votos": r["vn26"] - r[f"vn22_{t}"],
            "eleitorado_votos": r["e26"] - r[f"e22_{t}"],
            "validos_votos": r["vv26"] - r[f"vv22_{t}"],
        }
    comp["vs_1t"]["terceiros_pp"] = pp(f26["terceiros"], f22[1]["terceiros"])
    comp["vs_1t"]["terceiros_votos"] = terc26 - terc22
    gap_2t = f26["flavio"] - f22[2]["bolsonaro"]
    return {
        "votos_2026": {
            "flavio": r["flavio"],
            "lula": r["lula26"],
            "cury": r["cury"],
            "renan": r["renan"],
            "caiado": r["caiado"],
            "outros": r["outros26"],
            "terceiros": terc26,
            "validos": r["vv26"],
            "brancos": r["vb26"],
            "nulos": r["vn26"],
            "comparecimento": r["c26"],
            "abstencao": r["a26"],
            "eleitorado": r["e26"],
        },
        "votos_2022_1t": {
            "bolsonaro": r["bolsonaro_1"],
            "lula": r["lula22_1"],
            "ciro": r["ciro_1"],
            "tebet": r["tebet_1"],
            "outros": r["outros22_1"],
            "terceiros": terc22,
            "validos": r["vv22_1"],
            "brancos": r["vb22_1"],
            "nulos": r["vn22_1"],
            "comparecimento": r["c22_1"],
            "abstencao": r["a22_1"],
            "eleitorado": r["e22_1"],
        },
        "votos_2022_2t": {
            "bolsonaro": r["bolsonaro_2"],
            "lula": r["lula22_2"],
            "validos": r["vv22_2"],
            "brancos": r["vb22_2"],
            "nulos": r["vn22_2"],
            "comparecimento": r["c22_2"],
            "abstencao": r["a22_2"],
            "eleitorado": r["e22_2"],
        },
        "pct_2026": {k: p(v) for k, v in f26.items()},
        "pct_2022_1t": {k: p(v) for k, v in f22[1].items()},
        "pct_2022_2t": {k: p(v) for k, v in f22[2].items()},
        "margem_2026_pp": p(margem26),
        "comparacao": comp,
        "flavio_supera_bolsonaro_2t": gap_2t > 0,
        "flavio_menos_bolsonaro_2t_pp": p(gap_2t),
        "flavio_menos_bolsonaro_2t_votos": r["flavio"] - r["bolsonaro_2"],
        "flavio_menos_bolsonaro_2t_votos_equivalentes": round(gap_2t * r["vv26"]),
    }


def fatia(parte: int, total: int, casas: int = 4) -> float | None:
    """Percentual com o arredondamento da casa (atalho para `dados.pct`)."""
    return pct(parte, total, casas)
