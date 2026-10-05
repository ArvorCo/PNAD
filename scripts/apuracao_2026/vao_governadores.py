"""Vão estadual dos governadores nas 27 UFs, inclusive as candidaturas do centro.

O vão compara, na mesma UF e na mesma urna, a parcela dos válidos de uma
candidatura ao governo (eleita no 1º turno, ou cada nome do par do 2º turno) com
a parcela do finalista presidencial do lado dela. Cargos diferentes, mesmo
eleitor: é **teto endereçável, nunca transferência certa**.

Lado de cada candidatura:

- direita e centro-direita contra Flávio; esquerda e centro-esquerda contra
  Lula (regra do bloco, a mesma de `final.json`);
- centro (PSD, MDB, Avante) não tem finalista próprio e é comparado com o
  finalista que a coligação apoiou, pela tabela editorial `COMPARACAO_CENTRO`;
- candidatura de bloco cuja coligação registrada contraria o bloco (federação do
  PT na coligação de um candidato de centro-direita) entra por
  `COMPARACAO_EXCECAO`, com a mesma evidência.

Evidência: a coligação registrada no TSE (`coligacoes.py`) e a exceção de campo
da casa (`campo_excecao` em `docs/assets/voto_util_092026.json`, gerada por
`scripts/voto-util-092026-data.py`). Sem evidência documental, a candidatura de
centro é comparada com Flávio e marcada "sem apoio declarado". A ficha mostra
sempre as duas diferenças, contra Flávio e contra Lula.
"""

from __future__ import annotations

from typing import Any

from .coligacoes import lado_da_coligacao

FINALISTAS = {"flavio": "FLAVIO BOLSONARO", "lula": "LULA"}
SEM_APOIO = "sem apoio declarado"
ROTULO_TETO = "teto endereçável, nunca transferência certa"

# Tabela editorial: candidatura de centro (UF, nome de urna) -> finalista comparado.
# `comparacao` é o rótulo curto da ficha; `evidencia`, a frase com a fonte.
COMPARACAO_CENTRO: dict[tuple[str, str], dict[str, str]] = {
    ("AM", "OMAR AZIZ"): {
        "finalista": "lula",
        "comparacao": "coligação com o PT",
        "evidencia": "coligação Força Amazonas registrada no TSE com a federação do PT; "
        "aliado declarado do governo federal na exceção de campo da casa",
    },
    ("AP", "DR. FURLAN"): {
        "finalista": "flavio",
        "comparacao": "coligação com o PL",
        "evidencia": "coligação registrada no TSE com o PL (NOVO, PSD, PODE e PL), sem o PT",
    },
    ("ES", "RICARDO FERRAÇO"): {
        "finalista": "lula",
        "comparacao": "aliado declarado de Lula",
        "evidencia": "exceção de campo da casa: vice de Renato Casagrande (PSB), aliado de Lula; "
        "a coligação registrada no TSE tem PSB e PDT, da coligação presidencial de Lula, "
        "e não tem PT nem PL",
    },
    ("GO", "DANIEL VILELA"): {
        "finalista": "flavio",
        "comparacao": SEM_APOIO,
        "evidencia": "coligação registrada no TSE sem PT e sem PL; inclui o PSD de Ronaldo Caiado, "
        "candidato a presidente; a exceção de campo da casa o descreve como vice e sucessor de Caiado, "
        "sem alinhamento com Lula",
    },
    ("MA", "EDUARDO BRAIDE"): {
        "finalista": "flavio",
        "comparacao": SEM_APOIO,
        "evidencia": "coligação registrada no TSE com NOVO e PSD, sem PT e sem PL",
    },
    ("PE", "RAQUEL LYRA"): {
        "finalista": "flavio",
        "comparacao": SEM_APOIO,
        "evidencia": "coligação registrada no TSE com PODE, PSD, AVANTE, PSDB, Cidadania, União e PP, "
        "sem PT e sem PL",
    },
    ("RJ", "EDUARDO PAES"): {
        "finalista": "lula",
        "comparacao": "coligação com o PT",
        "evidencia": "coligação registrada no TSE com a federação do PT, PSB e PDT, sem o PL; "
        "aliado declarado de Lula na exceção de campo da casa",
    },
    ("SE", "FÁBIO"): {
        "finalista": "lula",
        "comparacao": "coligação com o PT",
        "evidencia": "coligação registrada no TSE com a federação do PT e o PSB, sem o PL",
    },
}

# Candidatura de bloco cuja coligação registrada contraria o bloco.
COMPARACAO_EXCECAO: dict[tuple[str, str], dict[str, str]] = {
    ("PB", "LUCAS RIBEIRO"): {
        "finalista": "lula",
        "comparacao": "coligação com o PT",
        "evidencia": "coligação registrada no TSE com a federação do PT e o PSB, sem o PL; "
        "aliado declarado de Lula na exceção de campo da casa (vice de João Azevêdo, PSB)",
    },
}

DIREITA = ("direita", "centro-direita")
ESQUERDA = ("esquerda", "centro-esquerda")


def presidenciaveis(final: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Parcela de Flávio e de Lula nos válidos de presidente em cada UF."""
    nomes = {v: k for k, v in FINALISTAS.items()}
    saida: dict[str, dict[str, float]] = {}
    for u in final["presidente"]["ufs"]:
        par = {
            nomes[u["lider"]]: u["pct_lider"],
            nomes[u["segundo"]]: u["pct_segundo"],
        }
        if set(par) != set(FINALISTAS):
            raise ValueError(f"{u['uf']}: Flávio e Lula não são os dois primeiros")
        saida[u["uf"].upper()] = par
    return saida


def declaracao(uf: str, nome: str, campo: str) -> dict[str, str]:
    """Finalista comparado e o motivo, pela tabela editorial ou pela regra do bloco."""
    chave = (uf, nome)
    if chave in COMPARACAO_CENTRO:
        if campo != "centro":
            raise ValueError(f"{uf} {nome}: está em COMPARACAO_CENTRO, mas é {campo}")
        return COMPARACAO_CENTRO[chave]
    if chave in COMPARACAO_EXCECAO:
        return COMPARACAO_EXCECAO[chave]
    if campo in DIREITA:
        return {
            "finalista": "flavio",
            "comparacao": "mesmo bloco",
            "evidencia": "regra do bloco",
        }
    if campo in ESQUERDA:
        return {
            "finalista": "lula",
            "comparacao": "mesmo bloco",
            "evidencia": "regra do bloco",
        }
    raise ValueError(
        f"{uf} {nome}: candidatura de {campo} sem linha em COMPARACAO_CENTRO"
    )


def conferir(linha: dict[str, Any], coligacao: dict[str, Any] | None) -> None:
    """A coligação registrada não pode contrariar a comparação declarada."""
    if coligacao is None:
        return
    lado = lado_da_coligacao(coligacao["partidos"])
    if linha["comparacao"] == SEM_APOIO and lado is not None:
        raise ValueError(
            f"{linha['uf']} {linha['governador']}: marcado sem apoio, mas a coligação é do lado {lado}"
        )
    if lado is not None and lado != linha["finalista"]:
        raise ValueError(
            f"{linha['uf']} {linha['governador']}: coligação do lado {lado}, comparado com "
            f"{linha['finalista']}; declarar em COMPARACAO_EXCECAO ou COMPARACAO_CENTRO"
        )


def vao_completo(
    final: dict[str, Any],
    coligacoes: dict[tuple[str, str], dict] | None = None,
    precisos: dict[str, dict] | None = None,
) -> dict[str, Any]:
    """Uma linha por candidatura ao governo eleita ou no 2º turno, nas 27 UFs.

    `precisos` traz as parcelas sem arredondar lidas do banco
    (`casas.pct_precisos`); sem ele, valem as de `final.json`, com duas casas.
    """
    pres = presidenciaveis(final)
    gov_preciso: dict[tuple[str, str], float] = {}
    if precisos:
        pres.update(precisos["presidente"])
        gov_preciso = precisos["governador"]
    lista = []
    for u in final["governadores"]["ufs"]:
        uf = u["uf"].upper()
        for i, c in enumerate(u["candidatos"]):
            decl = declaracao(uf, c["nome"], c["campo"])
            fin = decl["finalista"]
            pf, pl = pres[uf]["flavio"], pres[uf]["lula"]
            pg = gov_preciso.get((uf, c["nome"]), c["pct"])
            if abs(pg - c["pct"]) > 0.006:
                raise ValueError(
                    f"{uf} {c['nome']}: {pg} no banco, {c['pct']} no boletim"
                )
            comparado = pf if fin == "flavio" else pl
            linha = {
                "uf": uf.lower(),
                "governador": c["nome"],
                "partido": c["partido"],
                "campo": c["campo"],
                "decisao": u["decisao"],
                "principal": i == 0,
                "pct_governador": round(pg, 2),
                "finalista": fin,
                "presidenciavel": FINALISTAS[fin],
                "pct_presidenciavel": round(comparado, 2),
                "vao_pp": round(pg - comparado, 2),
                "pct_flavio": round(pf, 2),
                "pct_lula": round(pl, 2),
                "vao_flavio_pp": round(pg - pf, 2),
                "vao_lula_pp": round(pg - pl, 2),
                "comparacao": decl["comparacao"],
                "evidencia": decl["evidencia"],
            }
            col = (coligacoes or {}).get((uf, c["nome"]))
            conferir(linha, col)
            if col:
                linha["coligacao"] = col["coligacao"]
                linha["coligacao_partidos"] = col["partidos"]
            lista.append(linha)
    ufs = {x["uf"] for x in lista}
    if len(ufs) != len(final["governadores"]["ufs"]):
        raise ValueError(f"vão estadual cobre {len(ufs)} UFs")
    centro = [x for x in lista if x["campo"] == "centro"]
    return {
        "nota": (
            "candidatura ao governo (eleita no 1º turno ou cada nome do par do 2º turno) menos o finalista "
            "presidencial do lado dela na mesma UF, em pontos dos válidos; direita e centro-direita contra "
            "Flávio, esquerda e centro-esquerda contra Lula; centro contra o finalista que a coligação apoiou "
            "(COMPARACAO_CENTRO em scripts/apuracao_2026/vao_governadores.py), e contra Flávio, marcado "
            "'sem apoio declarado', quando a coligação não tem PT nem PL e a casa não declara alinhamento; "
            "mesma urna, cargos diferentes; não é transferência"
        ),
        "regra_coligacao": (
            "coligação com a federação do PT e sem o PL: lado de Lula; com o PL e sem o PT: lado de Flávio; "
            "fonte: consulta de candidaturas do TSE, data/raw/tse_candidatos_2026/consulta_cand_2026.zip"
        ),
        "rotulo_obrigatorio": ROTULO_TETO,
        "n_ufs": len(ufs),
        "n_candidaturas": len(lista),
        "centro": [
            {
                "uf": x["uf"].upper(),
                "governador": x["governador"],
                "partido": x["partido"],
                "comparado_com": x["presidenciavel"],
                "comparacao": x["comparacao"],
                "vao_flavio_pp": x["vao_flavio_pp"],
                "vao_lula_pp": x["vao_lula_pp"],
            }
            for x in centro
        ],
        "lista": sorted(lista, key=lambda x: -x["vao_pp"]),
    }
