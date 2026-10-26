"""Registro Digital do Voto (RDV) do 2º turno de 2026: cobertura, conferência e limites.

Lê ``apuracao/data/rdv_2t_2026.sqlite`` (gravado por ``apuracao/scripts/rdv-coletar.ts``)
e, só para contar seções, ``apuracao/data/secoes_2t_2026.sqlite``. Os dois são abertos
só para leitura.

O RDV guarda os votos por eleição e por cargo, cada lista ordenada por tipo e digitação
(especificação oficial ``rdv.asn1`` e README do pacote do TSE). Não existe registro por
eleitor: a matriz presidente × governador de uma seção **não é identificável**. O que se
publica aqui são os limites de Fréchet de cada célula (o mínimo e o máximo compatíveis com
as duas margens da seção), somados por município e UF, e a célula esperada sob
independência só como referência. Somar limites seção a seção dá intervalos mais
estreitos que aplicar Fréchet às margens da UF, mas continuam sendo limites.

O que o RDV mede e o BU não: a digitação dos votos nulos. Um nulo de governador com 13
ou 22 digitado é um número de presidente teclado no campo de governador.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RDV_DB = ROOT / "apuracao/data/rdv_2t_2026.sqlite"
SECOES_DB = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
GOVERNADORES = ROOT / "analysis/apuracao_2t_2026/dados/governadores.json"
SAIDA = ROOT / "analysis/apuracao_2t_2026/dados/rdv.json"

UFS_GOVERNADOR = ("ac", "am", "df", "es", "rn", "to")
PRESIDENTE = {"13": "LULA", "22": "FLÁVIO BOLSONARO"}
ROTULO = (
    "limites, não medição: o RDV guarda presidente e governador em listas separadas e "
    "ordenadas, sem ligar o voto de um eleitor nos dois cargos"
)
ROTULO_CASA = "atipicidade pede explicação, não prova irregularidade"

# Tipos do RDV (rdv.asn1): 1 legenda, 2 nominal, 3 branco, 4 nulo, 5 branco após
# suspensão, 6 nulo após suspensão, 7 nulo por repetição, 8 e 9 cargo sem candidato.
TIPOS_BRANCO = {3, 5}
TIPOS_ESPECIAIS = {5, 6, 7, 8, 9}
STATUS = {"ok", "sem_rdv", "agregada", "aux_404", "rdv_404", "erro"}


def categoria(tipo: int, digitacao: str) -> str:
    """Categoria do voto para a matriz: número do candidato, ``branco`` ou ``nulo``."""
    if tipo == 2:
        return digitacao
    if tipo in TIPOS_BRANCO:
        return "branco"
    return "nulo"


def frechet(
    a: Mapping[str, int], b: Mapping[str, int], n: int
) -> dict[tuple[str, str], tuple[int, int, float]]:
    """Para cada célula (i, j): (mínimo, máximo, esperado sob independência).

    ``a`` e ``b`` são as margens de uma mesma seção, cada uma somando ``n``.
    """
    if sum(a.values()) != n or sum(b.values()) != n:
        raise ValueError("margens não somam n")
    out: dict[tuple[str, str], tuple[int, int, float]] = {}
    for i, ai in a.items():
        for j, bj in b.items():
            esperado = ai * bj / n if n > 0 else 0.0
            out[(i, j)] = (max(0, ai + bj - n), min(ai, bj), esperado)
    return out


@dataclass
class Acumulado:
    """Soma de limites e margens de várias seções."""

    secoes: int = 0
    n: int = 0
    pres: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    gov: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    minimo: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    maximo: dict[tuple[str, str], int] = field(default_factory=lambda: defaultdict(int))
    esperado: dict[tuple[str, str], float] = field(
        default_factory=lambda: defaultdict(float)
    )

    def somar(self, a: Mapping[str, int], b: Mapping[str, int], n: int) -> None:
        self.secoes += 1
        self.n += n
        for k, v in a.items():
            self.pres[k] += v
        for k, v in b.items():
            self.gov[k] += v
        for cel, (lo, hi, e) in frechet(a, b, n).items():
            self.minimo[cel] += lo
            self.maximo[cel] += hi
            self.esperado[cel] += e

    def json(self, eixo_p: list[str], eixo_g: list[str]) -> dict[str, Any]:
        celulas = []
        for i in eixo_p:
            for j in eixo_g:
                lo, hi = self.minimo.get((i, j), 0), self.maximo.get((i, j), 0)
                celulas.append(
                    {
                        "presidente": i,
                        "governador": j,
                        "min": lo,
                        "max": hi,
                        "min_pct": pct(lo, self.n),
                        "max_pct": pct(hi, self.n),
                        "independencia_pct": pct(
                            self.esperado.get((i, j), 0.0), self.n
                        ),
                    }
                )
        return {
            "secoes": self.secoes,
            "n": self.n,
            "presidente": {k: self.pres.get(k, 0) for k in eixo_p},
            "governador": {k: self.gov.get(k, 0) for k in eixo_g},
            "celulas": celulas,
        }


def pct(x: float, n: int) -> float | None:
    return None if n == 0 else round(100 * x / n, 3)


def conectar(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def cobertura(
    rdv: sqlite3.Connection, secoes: sqlite3.Connection | None
) -> dict[str, Any]:
    por_uf: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(int))
    for uf, status, confere, n in rdv.execute(
        "SELECT uf, status, confere, COUNT(*) FROM rdv GROUP BY 1, 2, 3"
    ):
        d = por_uf[uf]
        d[status] += n
        if status == "ok":
            chave = {1: "confere", 0: "diverge"}.get(confere, "sem_bu")
            d[chave] += n
    for uf, total, com_bu in (
        secoes.execute(
            "SELECT uf, COUNT(*), SUM(bu_gz IS NOT NULL) FROM secao GROUP BY uf"
        )
        if secoes is not None
        else []
    ):
        por_uf[uf]["secoes_cs"] = total
        por_uf[uf]["com_bu"] = com_bu or 0
    nao_ordenado = dict(
        rdv.execute(
            "SELECT uf, COUNT(*) FROM rdv_cargo WHERE ordenado = 0 GROUP BY uf"
        ).fetchall()
    )
    total: dict[str, int] = defaultdict(int)
    saida = {}
    for uf in sorted(por_uf):
        d = dict(por_uf[uf])
        d["listas_fora_de_ordem"] = nao_ordenado.get(uf, 0)
        saida[uf] = d
        for k, v in d.items():
            total[k] += v
    return {"total": dict(total), "ufs": saida}


def divergencias(rdv: sqlite3.Connection, limite: int = 50) -> list[dict[str, Any]]:
    return [
        {"uf": uf, "mun": mun, "zona": z, "secao": s, "bu": bu, "divergencias": dv}
        for uf, mun, z, s, bu, dv in rdv.execute(
            "SELECT uf, mun, zona, secao, bu_nome, divergencias FROM rdv "
            "WHERE confere = 0 ORDER BY uf, mun, zona, secao LIMIT ?",
            (limite,),
        )
    ]


MOTIVO_BUSA_SEM_VOTOS = (
    "seção do exterior apurada pelo Sistema de Apuração (totalmente manual, motivo 99, "
    "outros) sem nenhum voto: o busa.dat decodifica com o cargo 1 e lista de votáveis vazia, "
    "comparecimento 0, e o RDV do SA traz o cargo 1 com zero votos; votos iguais (zero). "
    "A divergência 'cargo 1 ausente do BU' vinha do comparador, que inferia o cargo pelas "
    "linhas de voto e cargo sem voto não gera linha; corrigido e reconferido"
)


def conferencia_busa(rdv: sqlite3.Connection) -> dict[str, Any]:
    """Seções conferidas contra o BU do Sistema de Apuração (busa), à parte das do BU da urna."""
    sem_votos = [
        {
            "uf": uf,
            "mun": mun,
            "zona": z,
            "secao": s,
            "bu": bu,
            "motivo": MOTIVO_BUSA_SEM_VOTOS,
        }
        for uf, mun, z, s, bu in rdv.execute(
            "SELECT r.uf, r.mun, r.zona, r.secao, r.bu_nome FROM rdv r WHERE r.status = 'ok' "
            "AND r.confere = 1 AND r.bu_nome LIKE '%-busa.dat' AND NOT EXISTS (SELECT 1 FROM "
            "rdv_cargo c WHERE c.uf = r.uf AND c.mun = r.mun AND c.zona = r.zona "
            "AND c.secao = r.secao AND c.votos > 0) ORDER BY 1, 2, 3, 4"
        )
    ]
    (com_votos,) = rdv.execute(
        "SELECT COUNT(*) FROM rdv r WHERE r.status = 'ok' AND r.confere = 1 "
        "AND r.bu_nome LIKE '%-busa.dat' AND EXISTS (SELECT 1 FROM rdv_cargo c "
        "WHERE c.uf = r.uf AND c.mun = r.mun AND c.zona = r.zona AND c.secao = r.secao "
        "AND c.votos > 0)"
    ).fetchone()
    return {
        "conferidas_pelo_busa_com_votos": com_votos,
        "conferidas_pelo_busa_sem_votos": len(sem_votos),
        "secoes_sem_votos": sem_votos,
    }


def nulos_digitados(rdv: sqlite3.Connection) -> dict[str, Any]:
    """Digitação dos nulos por UF e cargo (os 15 números mais teclados) e tipos especiais."""
    por: dict[tuple[str, int], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    especiais: dict[tuple[str, int], dict[int, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for uf, cargo, tipo, dig, votos in rdv.execute(
        "SELECT uf, cargo, tipo, digitacao, SUM(votos) FROM rdv_voto "
        "WHERE tipo NOT IN (1, 2, 3) GROUP BY 1, 2, 3, 4"
    ):
        if tipo in TIPOS_ESPECIAIS:
            especiais[(uf, cargo)][tipo] += votos
        if tipo != 5:
            por[(uf, cargo)][dig or "(sem digitação)"] += votos
    out: dict[str, Any] = {}
    for (uf, cargo), d in sorted(por.items()):
        total = sum(d.values())
        top = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[:15]
        out.setdefault(uf, {})[str(cargo)] = {
            "nulos": total,
            "digitacoes": [
                {"digitacao": k, "votos": v, "pct": pct(v, total)} for k, v in top
            ],
            "tipos_especiais": {
                str(t): v for t, v in sorted(especiais[(uf, cargo)].items())
            },
        }
    return out


def troca_de_campo(
    rdv: sqlite3.Connection, candidatos_gov: Mapping[str, list[str]]
) -> dict[str, Any]:
    """Nulo de governador com número de presidente e nulo de presidente com número de governador."""
    out: dict[str, Any] = {}
    for uf in UFS_GOVERNADOR:
        cont: dict[tuple[int, str], int] = defaultdict(int)
        nulos: dict[int, int] = defaultdict(int)
        for cargo, dig, votos in rdv.execute(
            "SELECT cargo, digitacao, SUM(votos) FROM rdv_voto "
            "WHERE uf = ? AND cargo IN (1, 3) AND tipo NOT IN (1, 2, 3, 5) GROUP BY 1, 2",
            (uf,),
        ):
            cont[(cargo, dig)] += votos
            nulos[cargo] += votos
        if not nulos:
            continue
        g13, g22 = cont.get((3, "13"), 0), cont.get((3, "22"), 0)
        out[uf] = {
            "nulos_governador": nulos.get(3, 0),
            "governador_com_13": g13,
            "governador_com_22": g22,
            "governador_com_numero_de_presidente_pct": pct(g13 + g22, nulos.get(3, 0)),
            "nulos_presidente": nulos.get(1, 0),
            "presidente_com_numero_de_governador": {
                k: cont.get((1, k), 0)
                for k in candidatos_gov.get(uf, [])
                if k not in PRESIDENTE
            },
            "numero_compartilhado": sorted(
                set(candidatos_gov.get(uf, [])) & set(PRESIDENTE)
            ),
        }
    if out:
        ng = sum(x["nulos_governador"] for x in out.values())
        np_ = sum(x["nulos_presidente"] for x in out.values())
        g = sum(x["governador_com_13"] + x["governador_com_22"] for x in out.values())
        p = sum(
            sum(x["presidente_com_numero_de_governador"].values()) for x in out.values()
        )
        out["seis_ufs"] = {
            "nulos_governador": ng,
            "governador_com_numero_de_presidente": g,
            "governador_com_numero_de_presidente_pct": pct(g, ng),
            "nulos_presidente": np_,
            "presidente_com_numero_de_governador": p,
            "presidente_com_numero_de_governador_pct": pct(p, np_),
            "nota": (
                "piso: onde um candidato a governador tem o número de um finalista "
                "presidencial (13 ou 22, em numero_compartilhado), esse número é voto válido "
                "nos dois campos e a troca não aparece como nulo"
            ),
        }
    return out


def margens_secao(
    linhas: Iterable[tuple[int, int, str, int]],
) -> tuple[dict[str, int], dict[str, int]]:
    pres: dict[str, int] = defaultdict(int)
    gov: dict[str, int] = defaultdict(int)
    for cargo, tipo, dig, votos in linhas:
        alvo = pres if cargo == 1 else gov if cargo == 3 else None
        if alvo is not None:
            alvo[categoria(tipo, dig)] += votos
    return dict(pres), dict(gov)


def completar_transito(
    pres: dict[str, int], gov: dict[str, int]
) -> tuple[dict[str, int], dict[str, int]]:
    """Eleitor em trânsito vota só para presidente: a lista de presidente fica maior.

    A diferença vira a categoria ``transito`` (sem voto para governador), para as duas
    margens somarem o mesmo n. Lista de governador maior que a de presidente fica como está
    e a seção sai da matriz.
    """
    falta = sum(pres.values()) - sum(gov.values())
    if falta > 0:
        gov = {**gov, "transito": falta}
    return pres, gov


def eixos(pres: Iterable[str], gov: Iterable[str]) -> tuple[list[str], list[str]]:
    def ordem(xs: Iterable[str]) -> list[str]:
        especiais = ("branco", "nulo", "transito")
        conj = set(xs)
        nums = sorted(
            {x for x in conj if x not in especiais}, key=lambda x: (len(x), x)
        )
        return [*nums, "branco", "nulo", *(["transito"] if "transito" in conj else [])]

    return ordem(pres), ordem(gov)


def matriz_uf(rdv: sqlite3.Connection, uf: str) -> dict[str, Any]:
    """Limites por UF, município e seção (seções com as duas listas do mesmo tamanho)."""
    secoes: dict[tuple[str, int, int], list[tuple[int, int, str, int]]] = defaultdict(
        list
    )
    for mun, z, s, cargo, tipo, dig, votos in rdv.execute(
        "SELECT v.mun, v.zona, v.secao, v.cargo, v.tipo, v.digitacao, v.votos "
        "FROM rdv_voto v JOIN rdv r USING (uf, mun, zona, secao) "
        "WHERE v.uf = ? AND r.status = 'ok' AND v.cargo IN (1, 3)",
        (uf,),
    ):
        secoes[(mun, z, s)].append((cargo, tipo, dig, votos))
    margens = {k: completar_transito(*margens_secao(v)) for k, v in secoes.items()}
    todos_p = {c for p, _ in margens.values() for c in p}
    todos_g = {c for _, g in margens.values() for c in g}
    eixo_p, eixo_g = eixos(todos_p, todos_g)
    total = Acumulado()
    por_mun: dict[str, Acumulado] = defaultdict(Acumulado)
    linhas_secao = []
    excluidas = 0
    for (mun, z, s), (p, g) in sorted(margens.items()):
        n = sum(p.values())
        if n == 0 or sum(g.values()) != n:
            excluidas += 1
            continue
        total.somar(p, g, n)
        por_mun[mun].somar(p, g, n)
        f = frechet(p, g, n)
        linhas_secao.append(
            [
                mun,
                z,
                s,
                n,
                [p.get(i, 0) for i in eixo_p],
                [g.get(j, 0) for j in eixo_g],
                [
                    [f[(i, j)][0], f[(i, j)][1]] if (i, j) in f else [0, 0]
                    for i in eixo_p
                    for j in eixo_g
                ],
            ]
        )
    return {
        "eixo_presidente": eixo_p,
        "eixo_governador": eixo_g,
        "uf": total.json(eixo_p, eixo_g),
        "secoes_excluidas_governador_maior": excluidas,
        "municipios": {m: a.json(eixo_p, eixo_g) for m, a in sorted(por_mun.items())},
        "secoes_formato": [
            "mun",
            "zona",
            "secao",
            "n",
            "margem_presidente (eixo_presidente)",
            "margem_governador (eixo_governador)",
            "[min, max] por célula, presidente × governador em ordem de linha",
        ],
        "secoes": linhas_secao,
    }


def candidatos_governador(path: Path = GOVERNADORES) -> dict[str, dict[str, str]]:
    import json

    if not path.exists():
        return {}
    d = json.loads(path.read_text(encoding="utf-8"))
    return {
        u["uf"].lower(): {
            str(c["numero"]): c["nome_urna"] for c in u.get("candidatos", [])
        }
        for u in d.get("ufs", [])
    }


def gerar(
    rdv_db: Path = RDV_DB,
    secoes_db: Path | None = SECOES_DB,
    governadores: Path = GOVERNADORES,
) -> dict[str, Any]:
    rdv = conectar(rdv_db)
    sec = conectar(secoes_db) if secoes_db is not None and secoes_db.exists() else None
    try:
        nomes = candidatos_governador(governadores)
        nulos = nulos_digitados(rdv)
        cob = cobertura(rdv, sec)
        tentadas = sum(v for k, v in cob["total"].items() if k in STATUS)
        cruzado = {}
        for uf in UFS_GOVERNADOR:
            m = matriz_uf(rdv, uf)
            if m["uf"]["secoes"] == 0:
                continue
            m["nomes_governador"] = nomes.get(uf, {})
            cruzado[uf] = m
        return {
            "meta": {
                "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "script": "scripts/apuracao-2t-2026-rdv.py",
                "banco": "apuracao/data/rdv_2t_2026.sqlite",
                "especificacao": (
                    "data/originals/tse_formato_bu_rdv_2026/ (rdv.asn1 sha256 "
                    "282dcde0c7ba1f1bb128fe27443ad8d18f7490416c9546d033910a7ec557a465)"
                ),
                "arquivo": "rdv.json",
                "rotulo": ROTULO_CASA,
                "parcial": tentadas < cob["total"].get("secoes_cs", 0) or sec is None,
                "secoes_tentadas": tentadas,
            },
            "rotulo": ROTULO,
            "formato": (
                "votos guardados por eleição e cargo; cada lista ordenada por tipoVoto e "
                "digitação (README do pacote oficial, p. 7); sem vínculo entre cargos"
            ),
            "presidente": PRESIDENTE,
            "cobertura": cob,
            "divergencias_bu": divergencias(rdv),
            "conferencia_busa": conferencia_busa(rdv),
            "nulos_digitados": nulos,
            "troca_de_campo": troca_de_campo(
                rdv, {u: list(v) for u, v in nomes.items()}
            ),
            "cruzado_limites": cruzado,
        }
    finally:
        rdv.close()
        if sec is not None:
            sec.close()
