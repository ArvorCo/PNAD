"""A cauda das seções sem voto em Flávio: de onde o voto sumiu.

Pergunta do autor (27/10/2026): das seções que deram voto a Flávio no 1º turno e
nenhum no 2º, quais são aritmética de número pequeno e quais pedem explicação?
Este módulo responde sobre as mesmas leituras de ``zeros_dados`` (bancos de BUs dos
dois turnos, arquivo de 2022, cadastro do Politize) e acrescenta, sempre somente
leitura:

- governador (cargo 3) nas mesmas seções, nos dois bancos de BUs; nomes, partidos e
  campo de ``analysis/governador_2026/tse_candidatos.json`` (candidaturas do TSE) e,
  para os finalistas do 2º turno, de ``analysis/apuracao_2t_2026/dados/governadores.json``
  (com a comparação, por exemplo "coligação com o PT");
- RDV do 2º turno (``apuracao/data/rdv_2t_2026.sqlite``), com o hash do arquivo
  conferido contra o conteúdo guardado;
- log da urna: métricas do 2º turno (``data/outputs/logs_urnas_2t_2026.sqlite``,
  coluna ``resumo``) e o 1º turno lido de novo pelo leitor da casa
  (``apuracao_logs.parser.analisar``, dia 04/10/2026) sobre o ZIP original de
  ``data/raw/tse_logs_2026/logs.sqlite``, com o hash conferido nos três lugares em
  que aparece.

Regras declaradas (constantes abaixo):

- **universo**: Brasil sem o exterior, seções com BU de presidente nos dois turnos;
- **fatia do 1º turno**: votos do candidato sobre os válidos do 1º turno
  (comparecimento menos brancos e nulos, que é a soma dos votos nominais em todas
  as seções);
- **régua da independência**: cada eleitor que escolhe um finalista no 2º turno vota
  no candidato com a chance da fatia do 1º turno, um independente do outro; a
  chance de zero é ``(1 − p)^n``, perto de ``e^−k`` para quem tinha ``k`` votos.
  Eleitorado de comunidade não vota independente; a régua separa número pequeno de
  queda grande, não mede probabilidade de irregularidade;
- **cauda**: com ao menos ``PISO_NOMINAL_2T`` votos nominais no 2º turno, Flávio com
  6 votos ou mais no 1º e 1 ou nenhum no 2º, ou com 10 ou mais e queda de ao menos
  80%; o **espelho** aplica as duas regras a Lula.

``ESPERADO_CAUDA`` guarda os números conferidos antes da execução; ``falhas`` lista
as divergências e ``zeros_dados.conferir`` levanta ``AssertionError`` com elas.
Rótulo: atipicidade pede explicação, não prova irregularidade.
"""

from __future__ import annotations

import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .zeros_base import (
    BANCO_1T,
    BANCO_2T,
    Chave,
    Politize,
    Secao,
    Secao22,
    pct,
    rel,
    sha256,
    tipo_e_regra,
)
from .zeros_cauda_secao import (
    CAMPO_DIREITA,
    CANDIDATOS_GOV,
    GOVERNADORES,
    LOGS_1T,
    LOGS_2T,
    RDV,
    RDV_RESUMO,
    TOPO_GOV_1T,
    candidatos_governador,
    governador,
    ler_bu,
    ler_rdv,
    log_1t,
    log_2t,
    presidente_rdv,
    troca_de_campo,
)

PISO_NOMINAL_2T = 30
ATE_1 = (6, 1)  # Flávio com ao menos 6 votos no 1º turno e no máximo 1 no 2º
QUEDA = (10, 80)  # ao menos 10 votos no 1º turno e queda de ao menos 80%
LIMITE_PEQUENO = 5  # até 5 votos no 1º turno: número pequeno
# Termo da soma esperada cuja cota de Chernoff fica abaixo do corte vale zero; o
# erro total fica abaixo de (número de seções) x corte, menos de 1e-6.
CORTE_CHERNOFF = 1e-12

# Números conferidos pelo autor antes de escrever o módulo; ``falhas`` compara.
ESPERADO_CAUDA: dict[str, Any] = {
    "zero_com_voto_1t": 56,
    "zero_por_k": {1: 30, 2: 10, 3: 9, 4: 5, 5: 1, 16: 1},
    "base_por_k": {
        1: (129, 30),
        2: (150, 10),
        3: (201, 9),
        4: (241, 5),
        5: (263, 1),
        16: (659, 1),
    },
    "zeros_6_a_15": 0,
    "chance_aprox_pct_1_e_4": (37.0, 1.8),
    "queda_ate_1": 6,
    "queda_80": 6,
    "uniao": 10,
    "espelho": (0, 0),
    # (UF, município, zona, seção, Flávio 1º, Flávio 2º, Lula 1º, Lula 2º)
    "cauda": [
        ("AM", "Ipixuna", 45, 63, 61, 2, 135, 167),
        ("AP", "Itaubal", 10, 408, 33, 5, 155, 134),
        ("PA", "Anapu", 80, 254, 29, 4, 127, 158),
        ("AM", "São Paulo de Olivença", 22, 70, 20, 1, 154, 180),
        ("AM", "Maués", 5, 176, 16, 0, 310, 333),
        ("MA", "Icatu", 31, 32, 12, 2, 164, 154),
        ("MT", "Santa Terezinha", 16, 86, 7, 1, 271, 293),
        ("AC", "Marechal Thaumaturgo", 4, 384, 6, 1, 125, 122),
        ("MT", "Barra do Garças", 9, 461, 6, 1, 128, 133),
        ("MT", "Gaúcha do Norte", 57, 78, 6, 1, 170, 196),
    ],
    "locais": [
        "MARECHAL CANDIDO RONDON ALDEIA PIAU",
        "ADELANO NUNES LACERDA",
        "TRINCHEIRA BACAJÁ",
        "TIKUNA DUGUE SEBASTIÃO GASPAR",
        "UNIAWASAP'I",
        "OLAVO BILAC",
    ],
    "secoes_novas": [("AM", 5, 176), ("AP", 10, 408)],
    # Governador, 1º turno (os quatro primeiros) e 2º turno: (número, votos).
    "governador": {
        ("AM", 5, 176): {
            "t1": [(55, 176), (44, 118), (18, 12), (22, 11)],
            "t2": [(55, 328), (22, 1)],
        },
        ("AM", 45, 63): {"t1": {55: 177, 22: 6}, "t2": {55: 172, 22: 1}},
        ("AM", 22, 70): {"t1": {55: 142, 44: 13, 22: 11}, "t2": {55: 178, 22: 2}},
    },
    "maues": {
        "chave": ("AM", "02615", 5, 176),
        "secao_nova": True,
        "aptos": 382,
        "urna": (2341225, 2341225),
        "modelo": "UE2022",
        "mesma_carga": True,
        "carga_dia": "2026-09-29",
        "rdv_confere": 1,
        "rdv_presidente": (333, 4, 0),
        "habilitacao": (328, 6, 3),
        "processo_p50_s": 32,
        "cadencia_p50_s": 59,
        "reinicios": 0,
        "inspecoes": 5,
        "por_hora_2t": {
            "7": 47,
            "8": 56,
            "9": 58,
            "10": 62,
            "11": 60,
            "12": 49,
            "13": 4,
            "15": 1,
        },
        "encerramento_2t": "16:05",
        "horas_1t": (7, 19),
        "cadencia_p50_1t_s": 123,
        "cargos_1t": 5,
    },
    "ipixuna": {
        "chave": ("AM", "02399", 45, 63),
        "urnas_log_1t": ["02018634", "02018717"],
        "urnas_log_2t": ["02018717"],
        "rdv_confere": 1,
    },
}


# ------------------------------------------------------------------ régua


def validos(s: Secao) -> int:
    """Válidos de presidente: comparecimento menos brancos e nulos."""
    return s.comparecimento - s.brancos - s.nulos


def nominal_2t(s: Secao) -> int:
    """Votos nominais do 2º turno (Lula + Flávio)."""
    return s.lula + s.flavio


def chance_ate(n: int, p: float, m: int) -> float:
    """P(X ≤ m) para X ~ Binomial(n, p), somada em escala log."""
    if m < 0:
        return 0.0
    if m >= n or p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 0.0
    lp, lq, ln = math.log(p), math.log1p(-p), math.lgamma(n + 1)
    termos = [
        ln - math.lgamma(j + 1) - math.lgamma(n - j + 1) + j * lp + (n - j) * lq
        for j in range(m + 1)
    ]
    topo = max(termos)
    return math.exp(topo) * math.fsum(math.exp(t - topo) for t in termos)


def cota_chernoff(n: int, p: float, m: int) -> float:
    """Cota superior de P(X ≤ m) quando m/n < p: exp(−n · KL(m/n ‖ p))."""
    a = m / n
    if n <= 0 or not 0.0 < p < 1.0 or a >= p:
        return 1.0
    kl = (a * math.log(a / p) if a > 0 else 0.0) + (1 - a) * math.log((1 - a) / (1 - p))
    return math.exp(-n * kl)


def chance_somavel(n: int, p: float, m: int) -> float:
    """``chance_ate`` com corte declarado: termo de cota abaixo do corte vale zero."""
    if cota_chernoff(n, p, m) < CORTE_CHERNOFF:
        return 0.0
    return chance_ate(n, p, m)


def chance_queda(s1: Secao, s2: Secao, quem: str) -> float:
    """Chance, sob independência, de o candidato ficar com tão pouco no 2º turno."""
    v = validos(s1)
    k1, k2 = getattr(s1, quem), getattr(s2, quem)
    return chance_ate(nominal_2t(s2), k1 / v if v else 0.0, k2)


def regra_ate_1(k1: int, k2: int) -> bool:
    return k1 >= ATE_1[0] and k2 <= ATE_1[1]


def regra_queda(k1: int, k2: int) -> bool:
    # Inteiros: (k1 − k2) / k1 ≥ 80% equivale a 100 (k1 − k2) ≥ 80 k1.
    return k1 >= QUEDA[0] and 100 * (k1 - k2) >= QUEDA[1] * k1


def teto_queda(k1: int) -> int:
    """Maior voto no 2º turno que ainda cumpre a regra da queda."""
    return k1 * (100 - QUEDA[1]) // 100


# ------------------------------------------------------------------ contagens


Par = tuple[Secao, Secao]


def pares(s1: dict[Chave, Secao], s2: dict[Chave, Secao]) -> dict[Chave, Par]:
    """Seções do Brasil, sem o exterior, com BU de presidente nos dois turnos."""
    return {ch: (s1[ch], s) for ch, s in s2.items() if ch[0] != "ZZ" and ch in s1}


def numero_pequeno(
    p: dict[Chave, Par], muns: dict[tuple[str, str], str]
) -> dict[str, Any]:
    """Zeros do 2º turno por votos de Flávio no 1º e a taxa base do país por k."""
    zero = {ch: x for ch, x in p.items() if x[1].flavio == 0}
    por_k = Counter(s1.flavio for s1, _ in zero.values())
    k_max = max(por_k)
    base: Counter[int] = Counter()
    chegou: Counter[int] = Counter()
    esperado: defaultdict[int, float] = defaultdict(float)
    for s1, s2 in p.values():
        k = s1.flavio
        if k > k_max:
            continue
        base[k] += 1
        v = validos(s1)
        esperado[k] += (1 - k / v) ** nominal_2t(s2) if v else 1.0
        chegou[k] += s2.flavio == 0
    linhas = [
        {
            "k": k,
            "secoes_pais": base[k],
            "chegaram_a_zero": chegou[k],
            "pct_observado": pct(chegou[k], base[k], 2),
            "chance_aprox_pct": float(f"{100 * math.exp(-k):.6g}"),
            "zeros_esperados": float(f"{esperado[k]:.6g}"),
        }
        for k in range(k_max + 1)
    ]

    def faixa(de: int, ate: int) -> dict[str, Any]:
        ks = range(de, ate + 1)
        return {
            "de": de,
            "ate": ate,
            "secoes_pais": sum(base[k] for k in ks),
            "chegaram_a_zero": sum(chegou[k] for k in ks),
            "zeros_esperados": float(f"{sum(esperado[k] for k in ks):.6g}"),
        }

    lista = []
    for ch, (s1, s2) in sorted(zero.items(), key=lambda kv: (-kv[1][0].flavio, kv[0])):
        if s1.flavio == 0:
            continue
        uf, mun, zona, secao = ch
        lista.append(
            {
                "uf": uf,
                "mun": mun,
                "municipio": muns.get((uf, mun)) or mun,
                "zona": zona,
                "secao": secao,
                "flavio_1t": s1.flavio,
                "validos_1t": validos(s1),
                "nominal_2t": nominal_2t(s2),
                "chance_zero": float(f"{chance_queda(s1, s2, 'flavio'):.6g}"),
            }
        )
    return {
        "secoes_zero_2t": len(zero),
        "com_voto_1t": sum(n for k, n in por_k.items() if k > 0),
        "votos_1t": sum(k * n for k, n in por_k.items()),
        "por_k": [{"k": k, "secoes": n} for k, n in sorted(por_k.items())],
        "taxa_base": linhas,
        "faixas": [
            faixa(1, LIMITE_PEQUENO),
            faixa(LIMITE_PEQUENO + 1, k_max - 1),
            faixa(k_max, k_max),
        ],
        "secoes_com_voto_1t": lista,
        "nota": (
            "taxa_base: seções do Brasil, sem o exterior, com BU nos dois turnos e "
            "exatamente k votos em Flávio no 1º turno; chegaram_a_zero: com zero no 2º; "
            "chance_aprox_pct: 100·e^−k; zeros_esperados: soma de (1 − p)^n nas mesmas "
            "seções, com p = k / válidos do 1º turno e n = Lula + Flávio no 2º turno"
        ),
    }


def esperado_regras(p: dict[Chave, Par]) -> dict[str, float]:
    """Seções que as regras da cauda pegariam no país só pela régua da independência."""
    soma: defaultdict[str, float] = defaultdict(float)
    for s1, s2 in p.values():
        n, v = nominal_2t(s2), validos(s1)
        if n < PISO_NOMINAL_2T or not v:
            continue
        for quem, nome in (("flavio", ""), ("lula", "espelho_")):
            k1 = getattr(s1, quem)
            if k1 >= ATE_1[0]:
                soma[f"{nome}queda_ate_1"] += chance_somavel(n, k1 / v, ATE_1[1])
            if k1 >= QUEDA[0]:
                soma[f"{nome}queda_80"] += chance_somavel(n, k1 / v, teto_queda(k1))
    chaves = ("queda_ate_1", "queda_80", "espelho_queda_ate_1", "espelho_queda_80")
    return {k: round(soma[k], 4) for k in chaves}


def regras(p: dict[Chave, Par], quem: str, piso: bool) -> dict[str, list[Chave]]:
    sel = {
        ch: x for ch, x in p.items() if not piso or nominal_2t(x[1]) >= PISO_NOMINAL_2T
    }
    a = sorted(
        ch
        for ch, (s1, s2) in sel.items()
        if regra_ate_1(getattr(s1, quem), getattr(s2, quem))
    )
    b = sorted(
        ch
        for ch, (s1, s2) in sel.items()
        if regra_queda(getattr(s1, quem), getattr(s2, quem))
    )
    return {"queda_ate_1": a, "queda_80": b}


# ------------------------------------------------------------------ fichas


def ficha(
    ch: Chave,
    par: Par,
    criterios: list[str],
    s22: Secao22 | None,
    pol: dict | None,
    muns: dict[tuple[str, str], str],
    gov: dict[str, Any],
    bu1: dict[str, Any],
    bu2: dict[str, Any],
    rdv: dict[str, Any] | None,
) -> dict[str, Any]:
    uf, mun, zona, secao = ch
    s1, s2 = par
    municipio = muns.get((uf, mun)) or mun
    local = pol.get("local") if pol else None
    tipo, regra = tipo_e_regra(local, uf, municipio)
    b22 = pol.get("bolsonaro22_2t_v") if pol else None
    return {
        "uf": uf,
        "mun": mun,
        "municipio": municipio,
        "zona": zona,
        "secao": secao,
        "local": local,
        "tipo": tipo,
        "tipo_regra": regra,
        "criterios": criterios,
        "aptos_1t": s1.aptos,
        "aptos_2t": s2.aptos,
        "comparecimento_1t": s1.comparecimento,
        "comparecimento_2t": s2.comparecimento,
        "flavio_1t": s1.flavio,
        "flavio_2t": s2.flavio,
        "lula_1t": s1.lula,
        "lula_2t": s2.lula,
        "outros_1t": validos(s1) - s1.lula - s1.flavio,
        "brancos_nulos_1t": s1.brancos + s1.nulos,
        "brancos_nulos_2t": s2.brancos + s2.nulos,
        "validos_1t": validos(s1),
        "nominal_2t": nominal_2t(s2),
        "queda_flavio_pct": pct(s1.flavio - s2.flavio, s1.flavio, 1),
        "chance_independencia": float(f"{chance_queda(s1, s2, 'flavio'):.6g}"),
        "secao_nova": s22 is None and b22 is None,
        "t2022": (
            None
            if s22 is None
            else {
                "local": s22.local,
                "aptos": s22.aptos,
                "comparecimento": s22.comparecimento,
                "lula_2t": s22.lula_2t,
                "bolsonaro_2t": s22.bolsonaro_2t,
            }
        ),
        "politize_bolsonaro22_2t_pct_validos": b22,
        "governador": gov,
        "urna": {
            "t1": bu1["numero_interno_urna"],
            "t2": bu2["numero_interno_urna"],
            "modelo_t1": bu1["modelo_urna"],
            "modelo_t2": bu2["modelo_urna"],
            "mesma_urna": bu1["numero_interno_urna"] == bu2["numero_interno_urna"],
            "mesma_carga": bu1["codigo_carga"] == bu2["codigo_carga"],
            "bu_sha256_t1": bu1["bu_sha256"],
            "bu_sha256_t2": bu2["bu_sha256"],
        },
        "rdv": (
            None
            if rdv is None
            else {
                k: rdv[k]
                for k in (
                    "status",
                    "confere",
                    "confere_hash",
                    "sha256",
                    "numero_interno_urna",
                )
            }
        ),
        "link": f"politizese.html#uf={uf}&zona={zona}&secao={secao}",
    }


def por_dentro(
    ch: Chave,
    regra: str,
    f: dict[str, Any],
    bu1: dict[str, Any],
    bu2: dict[str, Any],
    rdv: dict[str, Any] | None,
    lg1: dict[str, Any],
    lg2: dict[str, Any],
) -> dict[str, Any]:
    uf, mun, zona, secao = ch
    return {
        "chave": [uf, mun, zona, secao],
        "municipio": f["municipio"],
        "local": f["local"],
        "regra_de_escolha": regra,
        "secao_nova": f["secao_nova"],
        "bu_1t": bu1,
        "bu_2t": bu2,
        "rdv": None if rdv is None else rdv | {"presidente": presidente_rdv(rdv)},
        "log_1t": lg1,
        "log_2t": lg2,
        "hashes_conferem": {
            "bu_1t": bu1["bu_confere_hash"],
            "bu_2t": bu2["bu_confere_hash"],
            "rdv": bool(rdv and rdv["confere_hash"]),
            "log_1t_zip": lg1["zip_confere_hash"],
            "log_1t_igual_bancos": lg1["log_sha256"] == bu1["log_sha256"],
            "log_2t_igual_bancos": lg2["log_sha256"] == bu2["log_sha256"],
        },
        "troca_de_campo_uf": troca_de_campo(uf),
    }


def _abre(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def montar(
    secoes1: dict[Chave, Secao],
    secoes2: dict[Chave, Secao],
    s22: dict[Chave, Secao22],
    pol: Politize,
    muns: dict[tuple[str, str], str],
) -> dict[str, Any]:
    """O bloco ``cauda`` de ``zeros.json``."""
    p = pares(secoes1, secoes2)
    pequeno = numero_pequeno(p, muns)
    flavio = regras(p, "flavio", piso=True)
    lula = regras(p, "lula", piso=True)
    flavio_sem = regras(p, "flavio", piso=False)
    lula_sem = regras(p, "lula", piso=False)
    a, b = set(flavio["queda_ate_1"]), set(flavio["queda_80"])
    uniao = sorted(a | b, key=lambda ch: (-p[ch][0].flavio, ch))
    info, ufs_2t = candidatos_governador()
    fichas = []
    con1, con2, con_rdv = _abre(BANCO_1T), _abre(BANCO_2T), _abre(RDV)
    try:
        bus: dict[Chave, tuple[dict, dict, dict | None]] = {}
        for ch in uniao:
            bu1, bu2, rdv = ler_bu(con1, ch), ler_bu(con2, ch), ler_rdv(con_rdv, ch)
            bus[ch] = (bu1, bu2, rdv)
            crit = [n for n, s in (("queda_ate_1", a), ("queda_80", b)) if ch in s]
            gov = governador(ch, con1, con2, info, ufs_2t)
            fichas.append(
                ficha(
                    ch,
                    p[ch],
                    crit,
                    s22.get(ch),
                    pol.secao(ch),
                    muns,
                    gov,
                    bu1,
                    bu2,
                    rdv,
                )
            )
    finally:
        con1.close()
        con2.close()
        con_rdv.close()
    escolhas = escolher_por_dentro(fichas)
    dentro = []
    c1, c2 = _abre(LOGS_1T), _abre(LOGS_2T)
    try:
        for ch, regra in escolhas:
            f = next(
                x for x in fichas if (x["uf"], x["mun"], x["zona"], x["secao"]) == ch
            )
            bu1, bu2, rdv = bus[ch]
            dentro.append(
                por_dentro(ch, regra, f, bu1, bu2, rdv, log_1t(c1, ch), log_2t(c2, ch))
            )
    finally:
        c1.close()
        c2.close()

    def extras(com: list[Chave], sem: list[Chave]) -> list[dict[str, Any]]:
        return [
            {
                "chave": list(ch),
                "municipio": muns.get(ch[:2]) or ch[1],
                "aptos_2t": p[ch][1].aptos,
                "comparecimento_1t": p[ch][0].comparecimento,
                "comparecimento_2t": p[ch][1].comparecimento,
                "nominal_2t": nominal_2t(p[ch][1]),
            }
            for ch in sem
            if ch not in set(com)
        ]

    lula_subiu = [f for f in fichas if f["lula_2t"] > f["lula_1t"]]
    lula_caiu = [
        f
        for f in fichas
        if f["lula_2t"] < f["lula_1t"]
        and f["comparecimento_2t"] < f["comparecimento_1t"]
    ]
    com_gov = [f for f in fichas if f["governador"]["t2"] is not None]
    return {
        "titulo": "A cauda: de onde o voto sumiu",
        "regras": {
            "universo": (
                "Brasil sem o exterior, seções com BU de presidente nos dois turnos de 2026"
            ),
            "piso_nominal_2t": PISO_NOMINAL_2T,
            "queda_ate_1": {"flavio_1t_min": ATE_1[0], "flavio_2t_max": ATE_1[1]},
            "queda_80": {"flavio_1t_min": QUEDA[0], "queda_min_pct": QUEDA[1]},
            "espelho": "as mesmas duas regras com Lula no lugar de Flávio",
            "limite_numero_pequeno": LIMITE_PEQUENO,
            "fatia_1t": "votos do candidato / válidos do 1º turno (comparecimento menos brancos e nulos)",
            "independencia": (
                "(1 − p)^n para zero e a soma binomial até o voto do 2º turno para a "
                "chance de ficar com tão pouco; p = fatia do 1º turno, n = Lula + "
                "Flávio no 2º turno; aproximação e^−k"
            ),
            "corte_chernoff": CORTE_CHERNOFF,
            "governador_direita": list(CAMPO_DIREITA),
            "governador_topo_1t": TOPO_GOV_1T,
            "por_dentro": (
                "a seção da cauda com zero no 2º turno e mais votos de Flávio no 1º, e "
                "a seção da cauda com mais votos de Flávio no 1º"
            ),
        },
        "numero_pequeno": pequeno,
        "cauda": {
            "queda_ate_1": len(a),
            "queda_80": len(b),
            "uniao": len(uniao),
            "nas_duas": len(a & b),
            "esperado_independencia": esperado_regras(p),
            "sem_piso": {
                "queda_ate_1": len(flavio_sem["queda_ate_1"]),
                "queda_80": len(flavio_sem["queda_80"]),
                "extras": extras(
                    flavio["queda_ate_1"] + flavio["queda_80"],
                    sorted(
                        set(flavio_sem["queda_ate_1"]) | set(flavio_sem["queda_80"])
                    ),
                ),
            },
        },
        "espelho": {
            "queda_ate_1": len(lula["queda_ate_1"]),
            "queda_80": len(lula["queda_80"]),
            "secoes": [list(ch) for ch in lula["queda_ate_1"] + lula["queda_80"]],
            "sem_piso": {
                "queda_ate_1": len(lula_sem["queda_ate_1"]),
                "queda_80": len(lula_sem["queda_80"]),
                "extras": extras(
                    lula["queda_ate_1"] + lula["queda_80"],
                    sorted(set(lula_sem["queda_ate_1"]) | set(lula_sem["queda_80"])),
                ),
            },
        },
        "fichas": fichas,
        "fluxo": {
            "lula_subiu": len(lula_subiu),
            "lula_e_comparecimento_cairam": [
                {
                    "chave": [f["uf"], f["mun"], f["zona"], f["secao"]],
                    "municipio": f["municipio"],
                    "comparecimento_caiu": f["comparecimento_1t"]
                    - f["comparecimento_2t"],
                    "lula_caiu": f["lula_1t"] - f["lula_2t"],
                }
                for f in lula_caiu
            ],
        },
        "governador": {
            "ufs_com_2t": sorted(ufs_2t),
            "secoes_com_2t": len(com_gov),
            "direita_caiu": [
                [f["uf"], f["mun"], f["zona"], f["secao"]]
                for f in com_gov
                if f["governador"]["t2"]["direita_e_centro_direita"]
                < f["governador"]["t1"]["direita_e_centro_direita"]
            ],
            "direita_subiu": [
                [f["uf"], f["mun"], f["zona"], f["secao"]]
                for f in com_gov
                if f["governador"]["t2"]["direita_e_centro_direita"]
                > f["governador"]["t1"]["direita_e_centro_direita"]
            ],
            "nota": (
                "direita_e_centro_direita soma os candidatos de governador com campo "
                "direita ou centro-direita na classificação editorial da casa "
                "(tse_candidatos.json e governadores.json); no 1º turno conta todos os "
                "candidatos, não só os quatro primeiros"
            ),
        },
        "por_dentro": dentro,
        "bancos": {
            rel(
                BANCO_1T
            ): "bu, secao, bu_cargo e voto_secao (cargo 3) das seções da cauda",
            rel(
                BANCO_2T
            ): "bu, secao, bu_cargo e voto_secao (cargo 3) das seções da cauda",
            rel(RDV): "rdv e rdv_voto; hash de cada RDV conferido contra o conteúdo",
            rel(LOGS_2T): "metricas.resumo (leitor da casa, 2º turno)",
            rel(LOGS_1T): "arquivos.zip, relido pelo leitor da casa com dia 04/10/2026",
        },
        "rotulo": "atipicidade pede explicação, não prova irregularidade",
    }


def fontes_leves() -> dict[str, str]:
    """Arquivos leves lidos pela cauda, com SHA-256, para a lista geral de fontes."""
    return {
        rel(c): sha256(c)
        for c in (GOVERNADORES, CANDIDATOS_GOV, RDV_RESUMO)
        if c.exists()
    }


def escolher_por_dentro(fichas: list[dict[str, Any]]) -> list[tuple[Chave, str]]:
    """As duas seções lidas por dentro, pela regra declarada em ``regras.por_dentro``."""

    def chave(f: dict[str, Any]) -> Chave:
        return (f["uf"], f["mun"], f["zona"], f["secao"])

    zeradas = [f for f in fichas if f["flavio_2t"] == 0]
    out: list[tuple[Chave, str]] = []
    if zeradas:
        f = max(zeradas, key=lambda x: (x["flavio_1t"], chave(x)))
        out.append((chave(f), "zero no 2º turno com mais votos de Flávio no 1º"))
    if fichas:
        f = max(fichas, key=lambda x: (x["flavio_1t"], chave(x)))
        if chave(f) not in {c for c, _ in out}:
            out.append((chave(f), "mais votos de Flávio no 1º turno na cauda"))
    return out


# ------------------------------------------------------------------ conferência


def _chave3(f: dict[str, Any]) -> tuple[str, int, int]:
    return (f["uf"], f["zona"], f["secao"])


def _pares_gov(t: dict[str, Any] | None) -> list[tuple[int, int]]:
    return [] if t is None else [(c["numero"], c["votos"]) for c in t["candidatos"]]


def obtido_cauda(c: dict[str, Any]) -> dict[str, Any]:
    """Os campos de ``ESPERADO_CAUDA``, lidos do bloco gravado."""
    np_ = c["numero_pequeno"]
    base = {x["k"]: x for x in np_["taxa_base"]}
    fichas = c["fichas"]
    out: dict[str, Any] = {
        "zero_com_voto_1t": np_["com_voto_1t"],
        "zero_por_k": {x["k"]: x["secoes"] for x in np_["por_k"] if x["k"] > 0},
        "base_por_k": {
            k: (base[k]["secoes_pais"], base[k]["chegaram_a_zero"])
            for k in ESPERADO_CAUDA["base_por_k"]
            if k in base
        },
        "zeros_6_a_15": sum(
            base[k]["chegaram_a_zero"] for k in range(6, 16) if k in base
        ),
        "chance_aprox_pct_1_e_4": (
            round(base[1]["chance_aprox_pct"], 0),
            round(base[4]["chance_aprox_pct"], 1),
        ),
        "queda_ate_1": c["cauda"]["queda_ate_1"],
        "queda_80": c["cauda"]["queda_80"],
        "uniao": c["cauda"]["uniao"],
        "espelho": (c["espelho"]["queda_ate_1"], c["espelho"]["queda_80"]),
        "cauda": [
            (
                f["uf"],
                f["municipio"],
                f["zona"],
                f["secao"],
                f["flavio_1t"],
                f["flavio_2t"],
                f["lula_1t"],
                f["lula_2t"],
            )
            for f in fichas
        ],
        "locais": [
            t
            for t in ESPERADO_CAUDA["locais"]
            if any(t in (f["local"] or "") for f in fichas)
        ],
        "secoes_novas": sorted(_chave3(f) for f in fichas if f["secao_nova"]),
    }
    gov: dict[tuple[str, int, int], dict[str, Any]] = {}
    por_ch = {_chave3(f): f for f in fichas}
    for ch, esp in ESPERADO_CAUDA["governador"].items():
        f = por_ch.get(ch)
        g = (f or {}).get("governador") or {}
        t1, t2 = _pares_gov(g.get("t1")), _pares_gov(g.get("t2"))
        if isinstance(esp["t1"], dict):
            gov[ch] = {"t1": {n: dict(t1).get(n) for n in esp["t1"]}}
            gov[ch]["t2"] = {n: dict(t2).get(n) for n in esp["t2"]}
        else:
            gov[ch] = {"t1": t1, "t2": t2}
    out["governador"] = gov
    dentro = {tuple(x["chave"]): x for x in c["por_dentro"]}
    m = dentro.get(ESPERADO_CAUDA["maues"]["chave"])
    out["maues"] = None if m is None else _obtido_maues(m)
    ip = dentro.get(ESPERADO_CAUDA["ipixuna"]["chave"])
    out["ipixuna"] = (
        None
        if ip is None
        else {
            "chave": tuple(ip["chave"]),
            "urnas_log_1t": ip["log_1t"]["urnas_log"],
            "urnas_log_2t": ip["log_2t"]["urnas_log"],
            "rdv_confere": (ip["rdv"] or {}).get("confere"),
        }
    )
    return out


def _obtido_maues(m: dict[str, Any]) -> dict[str, Any]:
    b1, b2, l1, l2 = m["bu_1t"], m["bu_2t"], m["log_1t"], m["log_2t"]
    pr = (m["rdv"] or {}).get("presidente") or {}
    hab = l2["habilitacao"] or {}
    return {
        "chave": tuple(m["chave"]),
        "secao_nova": m["secao_nova"],
        "aptos": b2["aptos"],
        "urna": (b1["numero_interno_urna"], b2["numero_interno_urna"]),
        "modelo": b2["modelo_urna"],
        "mesma_carga": b1["codigo_carga"] == b2["codigo_carga"],
        "carga_dia": (b2["carga_em"] or "")[:10],
        "rdv_confere": (m["rdv"] or {}).get("confere"),
        "rdv_presidente": (pr.get("lula"), pr.get("nulos"), pr.get("brancos")),
        "habilitacao": (
            hab.get("biometrica"),
            hab.get("biografica"),
            hab.get("sem_biometria"),
        ),
        "processo_p50_s": l2["processo_p50_s"],
        "cadencia_p50_s": l2["cadencia_p50_s"],
        "reinicios": l2["reinicios_durante_votacao"],
        "inspecoes": l2["inspecoes"],
        "por_hora_2t": l2["por_hora"],
        "encerramento_2t": (b2["encerramento"] or "")[11:16],
        "horas_1t": (
            int(l1["primeiro_computo"][:2]),
            int(l1["ultimo_computo"][:2]),
        ),
        "cadencia_p50_1t_s": l1["cadencia_p50_s"],
        "cargos_1t": len(b1["cargos"]),
    }


def falhas(c: dict[str, Any]) -> list[str]:
    """Divergências contra ``ESPERADO_CAUDA`` e hashes que não conferem."""
    ob = obtido_cauda(c)
    out = [
        f"cauda.{k}: esperado {v!r}, obtido {ob.get(k)!r}"
        for k, v in ESPERADO_CAUDA.items()
        if k != "secoes_novas" and ob.get(k) != v
    ]
    if ob["secoes_novas"] != sorted(ESPERADO_CAUDA["secoes_novas"]):
        out.append(
            f"cauda.secoes_novas: esperado {ESPERADO_CAUDA['secoes_novas']!r}, "
            f"obtido {ob['secoes_novas']!r}"
        )
    for x in c["por_dentro"]:
        ruins = [k for k, ok in x["hashes_conferem"].items() if not ok]
        if ruins:
            out.append(f"cauda.por_dentro {x['chave']}: hash não confere em {ruins}")
    for f in c["fichas"]:
        gov = f["governador"]
        if (gov["t2"] is not None) != gov["uf_tem_2t"]:
            out.append(f"cauda.governador {_chave3(f)}: 2º turno sem a UF na lista")
        if not (f["rdv"] and f["rdv"]["confere_hash"]):
            out.append(f"cauda.rdv {_chave3(f)}: hash do RDV não confere")
    return out


__all__ = [
    "ATE_1",
    "CAMPO_DIREITA",
    "CORTE_CHERNOFF",
    "ESPERADO_CAUDA",
    "LIMITE_PEQUENO",
    "PISO_NOMINAL_2T",
    "QUEDA",
    "chance_ate",
    "cota_chernoff",
    "escolher_por_dentro",
    "falhas",
    "fontes_leves",
    "montar",
    "obtido_cauda",
    "regra_ate_1",
    "regra_queda",
    "teto_queda",
]
