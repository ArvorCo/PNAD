"""Senado contra Flávio: o voto dos aliados ao Senado e o voto do presidenciável.

Mesma urna, cargos diferentes. No Senado de 2026 cada eleitor dá dois votos, e a
régua precisa ser declarada:

- **principal**: parcela de cada candidatura na base de votos do cargo que o TSE
  divulga (`pvapn`: válidos mais os anulados sub judice), contra a parcela de
  Flávio nos válidos de presidente no mesmo território. Cada voto conta uma vez;
  somadas, as candidaturas dão 100% dos votos e cerca de 200% dos eleitores. Uma
  candidatura isolada não passa de metade da base, porque o eleitor que vota nela
  ainda tem o segundo voto;
- **alternativa**: votos nominais divididos pelos votantes do cargo, a fração dos
  eleitores que escolheu a candidatura como um dos dois votos, contra a fração dos
  votantes de presidente que escolheu Flávio.

Blocos: `PL` são as candidaturas do partido; `aliados de Flávio` são direita e
centro-direita (classificação editorial de `apuracao/public/campos.json`, com as
exceções por candidatura) fora de `ALINHADOS_LULA`, a lista declarada abaixo.

Índice dos carregadores, método da casa (atlas de MG e SP):
`100 × (cand_mun / cand_uf) / (Flávio_mun / Flávio_uf)`, cada parcela sobre a
base do próprio cargo. Cem: a candidatura rende ali o mesmo que Flávio rende, cada
um contra a própria média estadual.

Limites fixos: não é transferência, não é pessoa, não é previsão.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Mapping
from typing import Any

from .coligacoes import FONTE as FONTE_TSE
from .coligacoes import lado_da_coligacao
from .dados import campo_de, versoes_genuinas

BLOCO_CAMPOS = ("direita", "centro-direita")
MIN_VOTANTES = 5000
N_LISTA = 10
N_MAPAS = 4
CORTES_INDICE = (70, 85, 95, 105, 115, 130)
FONTE_CASA = "campo_excecao em docs/assets/voto_util_092026.json (scripts/voto-util-092026-data.py)"
TSE_COLIGACAO = (
    f"coligação registrada no TSE com a federação do PT, sem o PL ({FONTE_TSE})"
)

# Candidaturas de direita e centro-direita ao Senado que ficam fora do bloco de
# Flávio, por SQ_CANDIDATO. Regra: aliado declarado de Lula na exceção de campo
# da casa, ou coligação registrada no TSE com a federação do PT e sem o PL.
ALINHADOS_LULA: dict[str, dict[str, str]] = {
    "100002542867": {
        "uf": "MA",
        "nome": "FUFUCA",
        "motivo": "ex-ministro do Esporte do governo Lula, aliado declarado na exceção de campo da casa",
        "fonte": FONTE_CASA,
    },
    "30002551576": {
        "uf": "AP",
        "nome": "ALLINY SERRÃO",
        "motivo": TSE_COLIGACAO,
        "fonte": FONTE_TSE,
    },
    "140002550780": {
        "uf": "PA",
        "nome": "CHICÃO",
        "motivo": TSE_COLIGACAO,
        "fonte": FONTE_TSE,
    },
    "150002549791": {
        "uf": "PB",
        "nome": "NABOR",
        "motivo": TSE_COLIGACAO,
        "fonte": FONTE_TSE,
    },
    "260002547290": {
        "uf": "SE",
        "nome": "ANDRÉ MOURA",
        "motivo": TSE_COLIGACAO,
        "fonte": FONTE_TSE,
    },
}

LIMITES = [
    "Não é transferência: o voto no senador e o voto no presidente são escolhas do mesmo eleitor "
    "para cargos diferentes, e a soma por território não diz quem votou em quem.",
    "Não é pessoa: o índice compara rendimento relativo por município, não o eleitor individual.",
    "Não é previsão: descreve o 1º turno de 04/10/2026, não o 2º turno nem 2030.",
    "Dois votos por eleitor: uma candidatura isolada não passa de metade da base de votos do Senado, "
    "e a soma de um bloco depende de quantos nomes ele lançou.",
]


def r(x: float | None, casas: int = 2) -> float | None:
    return None if x is None else round(x, casas)


def pct(parte: float, total: float) -> float | None:
    return 100 * parte / total if total else None


def sem_acento(s: str) -> str:
    base = unicodedata.normalize("NFKD", s)
    return "".join(c for c in base if not unicodedata.combining(c)).upper().strip()


# ---------------------------------------------------------------- classificação


def alinhados_da_casa(campo_excecao: Iterable[Mapping[str, Any]]) -> list[dict]:
    """Exceções de campo da casa marcadas como aliadas de Lula."""
    return [dict(e) for e in campo_excecao if e.get("alinhado_lula")]


def conferir_alinhados(
    cands: Iterable[Mapping[str, Any]],
    coligacoes: Mapping[str, Mapping[str, Any]],
    excecao_casa: Iterable[Mapping[str, Any]],
) -> list[str]:
    """SQ das candidaturas do bloco que a regra declarada tira do lado de Flávio.

    `cands` traz `sqcand`, `uf`, `nome` e `campo`. A regra é recomputada das fontes
    e precisa bater com `ALINHADOS_LULA`; sem o arquivo do TSE, só a exceção da
    casa é conferida.
    """
    casa = [(e["uf"].upper(), set(sem_acento(e["nome"]).split())) for e in excecao_casa]
    achados = []
    for c in cands:
        if c["campo"] not in BLOCO_CAMPOS:
            continue
        sq = str(c["sqcand"])
        palavras = set(sem_acento(c["nome"]).split())
        da_casa = any(uf == c["uf"] and nomes <= palavras for uf, nomes in casa)
        col = coligacoes.get(sq)
        pelo_tse = bool(col) and lado_da_coligacao(col["partidos"]) == "lula"
        if da_casa or pelo_tse:
            achados.append(sq)
    presentes = {str(c["sqcand"]) for c in cands}
    declarados = set(ALINHADOS_LULA) & presentes
    faltam = set(achados) - declarados
    sobram = declarados - set(achados) if coligacoes else set()
    if faltam or sobram:
        raise ValueError(
            f"ALINHADOS_LULA desatualizada: faltam {sorted(faltam)}, sobram {sorted(sobram)}"
        )
    return sorted(achados)


def classificar(
    cands: Iterable[Mapping[str, Any]], campos: Mapping[str, Mapping[str, str]]
) -> list[dict]:
    """Campo, PL e bloco de Flávio de cada candidatura ao Senado."""
    saida = []
    for c in cands:
        sq = str(c["sqcand"])
        campo = campo_de(campos, sq, c["partido"], c.get("federacao"))
        saida.append(
            {
                **c,
                "sqcand": sq,
                "campo": campo,
                "pl": c["partido"] == "PL",
                "aliado": campo in BLOCO_CAMPOS and sq not in ALINHADOS_LULA,
                "alinhado_lula": sq in ALINHADOS_LULA,
            }
        )
    return saida


# ---------------------------------------------------------------- contas


def soma_bloco(
    cands: list[dict], chave: str, base: int, comparecimento: int, fl: Mapping
) -> dict[str, Any]:
    """Votos de um bloco contra os de Flávio, nas duas réguas."""
    membros = [c for c in cands if c[chave]]
    votos = sum(c["votos"] for c in membros)
    p_base = pct(votos, base) if membros else None
    return {
        "votos": votos,
        "pct": r(p_base),
        "div_pp": r(p_base - fl["pct"]) if p_base is not None else None,
        "votos_por_voto_flavio": r(votos / fl["votos"], 3) if fl["votos"] else None,
        "pct_votantes": r(pct(votos, comparecimento)),
        "n_candidatos": len(membros),
        "candidatos": [
            {
                "nome": c["nome"],
                "partido": c["partido"],
                "votos": c["votos"],
                "eleito": c["eleito"],
                "sub_judice": c["sub_judice"],
            }
            for c in sorted(membros, key=lambda c: -c["votos"])
        ],
    }


def flavio_em(votos: int, validos: int, comparecimento: int) -> dict[str, Any]:
    return {
        "votos": votos,
        "validos": validos,
        "comparecimento": comparecimento,
        "pct": pct(votos, validos),
        "pct_votantes": pct(votos, comparecimento),
    }


def resumo_uf(uf: str, sen: Mapping[str, Any], fl: Mapping[str, Any]) -> dict:
    """Uma UF: soma do PL, soma dos aliados e a melhor candidatura do bloco."""
    cands = sen["candidatos"]
    base, comp = sen["base"], sen["comparecimento"]
    aliados = sorted((c for c in cands if c["aliado"]), key=lambda c: -c["votos"])
    melhor = None
    if aliados:
        m = aliados[0]
        p_m, pv_m = pct(m["votos"], base), pct(m["votos"], comp)
        melhor = {
            "sqcand": m["sqcand"],
            "nome": m["nome"],
            "partido": m["partido"],
            "campo": m["campo"],
            "votos": m["votos"],
            "pct": r(p_m),
            "pct_votantes": r(pv_m),
            "eleito": m["eleito"],
            "sub_judice": m["sub_judice"],
            "vao_pp": r(p_m - fl["pct"]),
            "vao_votantes_pp": r(pv_m - fl["pct_votantes"]),
            "votos_menos_flavio": m["votos"] - fl["votos"],
        }
    return {
        "uf": uf,
        "base_senado": base,
        "validos_senado": sen["vv"],
        "comparecimento_senado": comp,
        "secoes": sen["secoes"],
        "secoes_total": sen["secoes_total"],
        "gerado_em": sen["gerado_em"],
        "flavio": {k: r(v) if isinstance(v, float) else v for k, v in fl.items()},
        "pl": soma_bloco(cands, "pl", base, comp, fl),
        "aliados": soma_bloco(cands, "aliado", base, comp, fl),
        "melhor": melhor,
        "eleitos": [
            {
                "sqcand": c["sqcand"],
                "nome": c["nome"],
                "partido": c["partido"],
                "campo": c["campo"],
                "aliado": c["aliado"],
                "votos": c["votos"],
                "pct": r(pct(c["votos"], base)),
            }
            for c in sorted(cands, key=lambda c: -c["votos"])
            if c["eleito"]
        ],
        "sub_judice": [
            {"nome": c["nome"], "partido": c["partido"], "votos": c["votos"]}
            for c in cands
            if c["sub_judice"]
        ],
    }


def nacional(ufs: list[dict]) -> dict[str, Any]:
    """Soma das 27 UFs; Flávio só com o eleitor residente (o exterior não vota Senado)."""
    base = sum(u["base_senado"] for u in ufs)
    comp = sum(u["comparecimento_senado"] for u in ufs)
    fl = flavio_em(
        sum(u["flavio"]["votos"] for u in ufs),
        sum(u["flavio"]["validos"] for u in ufs),
        sum(u["flavio"]["comparecimento"] for u in ufs),
    )
    saida: dict[str, Any] = {
        "base_senado": base,
        "comparecimento_senado": comp,
        "flavio": {k: r(v) if isinstance(v, float) else v for k, v in fl.items()},
    }
    for chave in ("pl", "aliados"):
        votos = sum(u[chave]["votos"] for u in ufs)
        p = pct(votos, base)
        saida[chave] = {
            "votos": votos,
            "pct": r(p),
            "div_pp": r(p - fl["pct"]),
            "votos_por_voto_flavio": r(votos / fl["votos"], 3),
            "n_candidatos": sum(u[chave]["n_candidatos"] for u in ufs),
            "ufs_abaixo_de_flavio": sum(
                1 for u in ufs if (u[chave]["div_pp"] or 0) < 0
            ),
            "ufs_acima_de_flavio": sum(1 for u in ufs if (u[chave]["div_pp"] or 0) > 0),
        }
    pl = [u["pl"] for u in ufs]
    saida["pl"]["ufs_com_um_nome"] = sum(1 for x in pl if x["n_candidatos"] == 1)
    saida["pl"]["ufs_com_dois_nomes"] = sum(1 for x in pl if x["n_candidatos"] >= 2)
    saida["pl"]["ufs_sem_nome"] = sum(1 for x in pl if x["n_candidatos"] == 0)
    melhores = [u["melhor"] for u in ufs if u["melhor"]]
    saida["melhor"] = {
        "ufs_acima_na_base": sum(1 for m in melhores if m["vao_pp"] > 0),
        "ufs_acima_em_votantes": sum(1 for m in melhores if m["vao_votantes_pp"] > 0),
        "ufs": len(melhores),
    }
    return saida


# ---------------------------------------------------------------- índice municipal


def indice(c_mun: float, c_uf: float, f_mun: float, f_uf: float) -> float | None:
    """Índice dos carregadores; None quando alguma parcela é zero."""
    if not (c_uf and f_mun and f_uf):
        return None
    return 100 * (c_mun / c_uf) / (f_mun / f_uf)


def faixa_indice(v: float | None) -> int | None:
    return None if v is None else sum(v >= c for c in CORTES_INDICE)


def carregador(
    cand: Mapping[str, Any],
    uf: Mapping[str, Any],
    municipios: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Índice de uma candidatura eleita em cada município da UF, e os extremos.

    Cada item de `municipios` traz `cd`, `ibge`, `nome`, `votantes`, `completo`,
    `base_senado`, `votos` (sqcand -> votos), `flavio` e `validos_pres`.
    """
    sq = cand["sqcand"]
    c_uf = pct(cand["votos"], uf["base_senado"])
    f_uf = uf["flavio"]["pct"]
    linhas = []
    for m in municipios:
        c_mun = pct(m["votos"].get(sq, 0), m["base_senado"])
        f_mun = pct(m["flavio"], m["validos_pres"])
        ind = indice(c_mun or 0, c_uf or 0, f_mun or 0, f_uf)
        linhas.append(
            {
                "cd": m["cd"],
                "ibge": m["ibge"],
                "nome": m["nome"],
                "votantes": m["votantes"],
                "completo": m["completo"],
                "pct_cand": r(c_mun),
                "pct_flavio": r(f_mun),
                "indice": r(ind, 1),
            }
        )
    eleg = [
        x
        for x in linhas
        if x["completo"] and x["votantes"] >= MIN_VOTANTES and x["indice"] is not None
    ]
    n = min(N_LISTA, len(eleg) // 2)
    ordem = sorted(eleg, key=lambda x: -x["indice"])
    acima = [x for x in linhas if x["indice"] is not None and x["indice"] > 100]
    return {
        "sqcand": sq,
        "uf": uf["uf"],
        "nome": cand["nome"],
        "partido": cand["partido"],
        "campo": cand["campo"],
        "pct_uf": r(c_uf),
        "flavio_pct_uf": r(f_uf),
        "municipios": len(linhas),
        "incompletos": sum(1 for x in linhas if not x["completo"]),
        "elegiveis_lista": len(eleg),
        "municipios_acima_de_100": len(acima),
        "votantes_acima_de_100": sum(x["votantes"] for x in acima),
        "maiores": ordem[:n],
        "menores": ordem[::-1][:n],
        "linhas": linhas,
    }


def ufs_do_mapa(ufs: list[dict], eleitores: Mapping[str, int]) -> list[str]:
    """As N_MAPAS maiores UFs (eleitorado) com ao menos um eleito de direita do bloco."""
    com = [
        u["uf"]
        for u in ufs
        if any(e["aliado"] and e["campo"] == "direita" for e in u["eleitos"])
    ]
    return sorted(com, key=lambda uf: -eleitores.get(uf, 0))[:N_MAPAS]


# ---------------------------------------------------------------- banco


def ler_senado(banco: Any, eleicao: int, cargo: int = 5) -> dict[str, Any]:
    """Versão vigente (última gerada) dos arquivos de Senado de UF e de município."""
    cands = {str(c["sqcand"]): c for c in banco.candidatos(eleicao, cargo)}
    arqs = banco.arquivos(
        "tipo = 'u' AND eleicao_cd = ? AND cargo_cd = ? AND nivel IN ('uf', 'mu')",
        (eleicao, cargo),
    )
    snaps = banco.snapshots([a["id"] for a in arqs])
    vig: dict[tuple[str, str], dict] = {}
    for a in arqs:
        versoes = versoes_genuinas(snaps.get(a["id"], []))
        if not versoes:
            raise RuntimeError(f"arquivo sem versão: {a['chave']}")
        snap = banco.completar_totais(versoes[-1])
        vig[(a["nivel"], a["municipio_cd"] or a["uf"])] = {**snap, "uf": a["uf"]}
    votos = banco.votos(list(vig.values()))
    ufs: dict[str, dict] = {}
    for (nivel, chave), snap in vig.items():
        if nivel != "uf":
            continue
        linhas = banco.candidaturas(snap["id"])
        if not linhas:
            raise RuntimeError(f"Senado {chave}: versão {snap['id']} sem candidaturas")
        ufs[chave.upper()] = {
            "vv": snap["vv"],
            "comparecimento": snap["comparecimento"],
            "secoes": snap["st"],
            "secoes_total": snap["ts"],
            "gerado_em": snap["gerado_em"],
            "candidatos": [
                {
                    "sqcand": str(c["sqcand"]),
                    "nome": c["nome_urna"],
                    "partido": c["partido"],
                    "federacao": c["federacao"],
                    "votos": c["vap"] or 0,
                    "eleito": c["st"] == "Eleito",
                    "sub_judice": c["dvt"] != "Válido",
                }
                for c in linhas
            ],
        }
    for u in ufs.values():
        u["base"] = sum(c["votos"] for c in u["candidatos"])
    mun: dict[str, dict] = {}
    for (nivel, chave), snap in vig.items():
        if nivel == "mu":
            v = votos[snap["id"]]
            mun[chave] = {
                "uf": snap["uf"].upper(),
                "votos": v,
                "base_senado": sum(v.values()),
                "comparecimento": snap["comparecimento"],
                "completo": snap["st"] == snap["ts"],
            }
    banco.esquecer_documentos()
    return {"candidatos": cands, "ufs": ufs, "municipios": mun}


def montar(
    senado: Mapping[str, Any],
    presidente: Mapping[str, Any],
    campos: Mapping[str, Mapping[str, str]],
    coligacoes: Mapping[str, Mapping[str, Any]],
    excecao_casa: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Junta Senado (banco) e Flávio (`presidente.json`) nas três camadas."""
    excecao = alinhados_da_casa(excecao_casa)
    ufs_sen = {}
    todos = []
    for uf, u in senado["ufs"].items():
        cl = classificar([{**c, "uf": uf} for c in u["candidatos"]], campos)
        ufs_sen[uf] = {**u, "candidatos": cl}
        todos.extend(cl)
    conferir_alinhados(todos, coligacoes, excecao)
    ausentes = set(ALINHADOS_LULA) - {c["sqcand"] for c in todos}
    if ausentes and len(senado["ufs"]) == 27:
        raise ValueError(f"ALINHADOS_LULA com SQ fora do Senado: {sorted(ausentes)}")
    pres_uf = {u["uf"]: u for u in presidente["ufs"] if u["uf"] != "ZZ"}
    ufs = []
    for uf in sorted(ufs_sen):
        p = pres_uf[uf]
        fl = flavio_em(p["votos"]["flavio"], p["validos"], p["comparecimento"])
        ufs.append(resumo_uf(uf, ufs_sen[uf], fl))
    col = presidente["municipios"]["colunas"]
    pres_mun = [
        dict(zip(col, x, strict=True)) for x in presidente["municipios"]["linhas"]
    ]
    por_uf_mun: dict[str, list[dict]] = {}
    for m in pres_mun:
        s = senado["municipios"].get(m["cd_tse"])
        if s is None:
            raise RuntimeError(f"Senado sem arquivo do município {m['cd_tse']}")
        por_uf_mun.setdefault(m["uf"], []).append(
            {
                "cd": m["cd_tse"],
                "ibge": m["ibge"],
                "nome": m["nome"],
                "votantes": m["comparecimento"],
                "completo": bool(m["completo"]) and s["completo"],
                "base_senado": s["base_senado"],
                "votos": s["votos"],
                "flavio": m["flavio"],
                "validos_pres": m["validos"],
            }
        )
    carregadores = []
    for u in ufs:
        for e in u["eleitos"]:
            if e["aliado"]:
                carregadores.append(carregador(e, u, por_uf_mun[u["uf"]]))
    eleitores = {u["uf"]: u["eleitores"] for u in presidente["ufs"]}
    mapa_ufs = ufs_do_mapa(ufs, eleitores)
    mapa = {}
    for uf in mapa_ufs:
        cs = [c for c in carregadores if c["uf"] == uf]
        base_linhas = cs[0]["linhas"]
        linhas = []
        for i, x in enumerate(base_linhas):
            linha = [
                x["ibge"],
                x["nome"],
                x["votantes"],
                x["completo"],
                x["pct_flavio"],
            ]
            for c in cs:
                y = c["linhas"][i]
                linha += [y["pct_cand"], y["indice"]]
            linhas.append(linha)
        mapa[uf] = {
            "candidatos": [
                {k: c[k] for k in ("sqcand", "nome", "partido", "campo", "pct_uf")}
                for c in cs
            ],
            "flavio_pct_uf": cs[0]["flavio_pct_uf"],
            "colunas": ["ibge", "nome", "votantes", "completo", "pct_flavio"]
            + [f"{k}_{j}" for j in range(len(cs)) for k in ("pct_cand", "indice")],
            "linhas": linhas,
        }
    for c in carregadores:
        del c["linhas"]
    return {
        "regua": {
            "principal": (
                "parcela de cada candidatura ao Senado na base de votos do cargo que o TSE divulga "
                "(válidos mais anulados sub judice; cada voto conta uma vez, a soma das candidaturas "
                "dá 100% dos votos e cerca de 200% dos eleitores), contra a parcela de Flávio nos "
                "válidos de presidente no mesmo território"
            ),
            "alternativa": (
                "votos nominais da candidatura divididos pelos votantes do cargo (fração dos eleitores "
                "que a escolheu como um dos dois votos), contra votos de Flávio divididos pelos "
                "votantes de presidente"
            ),
            "teto": "uma candidatura isolada não passa de 50% da base principal, porque cada eleitor dá dois votos",
        },
        "blocos": {
            "pl": "candidaturas do PL",
            "aliados": (
                "direita e centro-direita (apuracao/public/campos.json, com exceções por candidatura) "
                "fora da lista ALINHADOS_LULA de scripts/apuracao_2026/senado_x_flavio.py"
            ),
            "alinhados_lula": [
                {"sqcand": sq, **v} for sq, v in sorted(ALINHADOS_LULA.items())
            ],
        },
        "nacional": nacional(ufs),
        "ufs": ufs,
        "carregadores": {
            "definicao": (
                "100 × (candidatura no município ÷ candidatura na UF) ÷ (Flávio no município ÷ Flávio na UF), "
                "cada parcela sobre a base do próprio cargo; 100 = rende ali o mesmo que Flávio, cada um "
                "contra a própria média estadual"
            ),
            "listas": (
                f"maiores e menores índices entre municípios com {MIN_VOTANTES} votantes ou mais e os dois "
                "arquivos (Senado e presidente) completos; até "
                f"{N_LISTA} por ponta, sem repetir município"
            ),
            "min_votantes": MIN_VOTANTES,
            "cortes": list(CORTES_INDICE),
            "candidatos": carregadores,
        },
        "mapa": {"ufs": mapa_ufs, "por_uf": mapa},
        "limites": LIMITES,
    }
