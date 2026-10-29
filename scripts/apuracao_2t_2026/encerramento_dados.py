"""Encerramento do BU em segundos exatos, com coluna independente de logs."""

from __future__ import annotations

import bisect
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BANCO = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
SAIDA = ROOT / "docs/assets/encerramento_2t_2026"
DIA = "2026-10-25"
CORTES = [61200 + 60 * m for m in [*range(11), 15, 20, 25, 30, 60, 75, 90, 105, 120]]
AM_ACRE = {
    "02020": "Guajará",
    "02054": "Atalaia do Norte",
    "02135": "Benjamin Constant",
    "02291": "Eirunepé",
    "02313": "Envira",
    "02399": "Ipixuna",
    "02496": "Jutaí",
    "02755": "São Paulo de Olivença",
    "02917": "Amaturá",
    "98370": "Itamarati",
    "98477": "Tabatinga",
}
CAMPOS = (
    "secoes",
    "aptos",
    "comparecimento",
    "validos",
    "flavio",
    "lula",
    "brancos",
    "nulos",
)
FONTES = [
    "https://www.tse.jus.br/comunicacao/noticias/2026/Setembro/faltam-26-dias-votacao-comeca-e-termina-no-mesmo-horario-em-todo-o-pais",
    "https://www.tre-am.jus.br/comunicacao/noticias/2026/Setembro/eleitorado-do-amazonas-deve-ficar-atento-aos-horarios-de-votacao-nas-eleicoes-2026",
]


def deslocamento(uf: str, mun: str) -> int | None:
    """Horas somadas ao relógio local para obter Brasília (UTC−3)."""
    uf = uf.upper()
    if uf == "ZZ":
        return None
    if uf == "AC" or (uf == "AM" and mun in AM_ACRE):
        return 2
    if uf == "PE" and mun == "30015":
        return -1
    return int(uf in {"AM", "RO", "RR", "MT", "MS"})


def segundo_brt(texto: str | None, uf: str, mun: str) -> int | None:
    off = deslocamento(uf, mun)
    if not texto or off is None:
        return None
    try:
        d = datetime.fromisoformat(texto) + timedelta(hours=off)
    except ValueError:
        return None
    if d.date().isoformat() != DIA or d.tzinfo is not None:
        return None
    return d.hour * 3600 + d.minute * 60 + d.second


def faixa(segundo: int) -> int:
    """(corte anterior, corte atual]; 17:02:01 pertence à linha das 17:03."""
    return bisect.bisect_left(CORTES, segundo)


def hora(segundo: int) -> str:
    return f"{segundo // 3600:02d}:{segundo % 3600 // 60:02d}:{segundo % 60:02d}"


def resumir(registros: list[dict]) -> dict:
    blocos = [Counter(dict.fromkeys(CAMPOS, 0)) for _ in range(len(CORTES) + 1)]
    ufs = [Counter() for _ in blocos]
    abertura = defaultdict(Counter)
    segundos = Counter()
    fuso_secoes = Counter()
    digest = hashlib.sha256()
    for r in registros:
        # A lista deve estar ordenada pela chave para que o hash seja reproduzível.
        digest.update(
            (json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n").encode()
        )
        uf, mun = r["uf"], r["mun"]
        s = segundo_brt(r["encerramento"], uf, mun)
        if s is None or r["id_confere"] != 1 or r["pleito"] != 3221:
            raise ValueError(
                f"BU sem horário/identidade válida: {uf}/{mun}/{r['secao']}"
            )
        if any(
            r[k] is None or r[k] < 0 for k in CAMPOS if k not in {"secoes", "validos"}
        ):
            raise ValueError("Contagem ausente ou negativa no BU")
        b = blocos[faixa(s)]
        b.update({k: r[k] for k in CAMPOS if k not in {"secoes", "validos"}})
        b["secoes"] += 1
        b["validos"] += r["flavio"] + r["lula"]
        ufs[faixa(s)][uf] += 1
        segundos[s] += 1
        fuso_secoes[deslocamento(uf, mun)] += 1
        a = segundo_brt(r["abertura"], uf, mun)
        if a is not None:
            abertura[(uf, mun)][a // 3600] += 1
    # Conferência independente do deslocamento territorial contra a moda de
    # abertura do próprio BU. Não usa log nem dados do primeiro turno.
    divergencias = [
        {"uf": uf, "mun": mun, "hora_modal_brt": c.most_common(1)[0][0]}
        for (uf, mun), c in abertura.items()
        if c.most_common(1)[0][0] != 8
    ]
    if divergencias:
        raise ValueError(f"Fusos divergem da abertura modal: {divergencias}")
    n = len(registros)
    acumulado = Counter(dict.fromkeys(CAMPOS, 0))
    linhas = []
    for i, b in enumerate(blocos):
        acumulado.update(b)
        linhas.append(
            {
                "corte_s": CORTES[i] if i < len(CORTES) else None,
                "hora": hora(CORTES[i]) if i < len(CORTES) else "Após 19:00:00",
                "inicio_exclusivo_s": CORTES[i - 1] if i else None,
                **dict(b),
                "parcela_secoes_pct": 100 * b["secoes"] / n,
                "encerradas_acumuladas": acumulado["secoes"],
                "encerradas_pct": 100 * acumulado["secoes"] / n,
                "restantes": n - acumulado["secoes"],
                "restantes_pct": 100 * (n - acumulado["secoes"]) / n,
                "comparecimento_pct": (
                    100 * b["comparecimento"] / b["aptos"] if b["aptos"] else None
                ),
                "flavio_pct": (
                    100 * b["flavio"] / b["validos"] if b["validos"] else None
                ),
                "lula_pct": 100 * b["lula"] / b["validos"] if b["validos"] else None,
                "acumulado": dict(acumulado),
                "ufs": [
                    {"uf": uf, "secoes": v, "pct": 100 * v / b["secoes"]}
                    for uf, v in sorted(ufs[i].items(), key=lambda x: (-x[1], x[0]))
                ],
            }
        )
    return {
        "dia": DIA,
        "fuso": "America/Sao_Paulo (UTC-3)",
        "campo": "bu.encerramento ← dadosSecao.dataHoraEncerramento do BU binário",
        "regra": "Cortes exatos inclusivos, sem arredondar segundos. Votos do dia inteiro nas seções de cada intervalo.",
        "universo": "Seções principais com BU presidencial no Brasil; exterior excluído; agregadas não duplicadas.",
        "fontes_fusos": FONTES,
        "extrato_ordenado_sha256": digest.hexdigest(),
        "total": dict(acumulado),
        "linhas": linhas,
        "fuso_secoes": dict(fuso_secoes),
        "conferencia_abertura": {
            "municipios": len(abertura),
            "divergencias": divergencias,
        },
        "primeiro_encerramento_brt": hora(min(segundos)),
        "ultimo_encerramento_brt": hora(max(segundos)),
        "segundos": [
            {"segundo_brt": s, "secoes": v} for s, v in sorted(segundos.items())
        ],
        "residuo_comparecimento_menos_votos": acumulado["comparecimento"]
        - sum(acumulado[k] for k in ["validos", "brancos", "nulos"]),
    }


def gerar(banco: Path = BANCO, saida: Path = SAIDA, refazer_logs=False) -> dict:
    with sqlite3.connect(f"file:{banco}?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=1")
        con.execute("BEGIN")
        cat = con.execute("""SELECT count(*) FROM secao WHERE upper(uf)!='ZZ'
            AND (nsp IS NULL OR nsp=0 OR nsp=secao)""").fetchone()[0]
        registros = [dict(r) for r in con.execute("""
            WITH votos AS (
              SELECT uf,mun,zona,secao,
                sum(CASE WHEN tipo=1 AND numero=22 THEN votos ELSE 0 END) flavio,
                sum(CASE WHEN tipo=1 AND numero=13 THEN votos ELSE 0 END) lula,
                sum(CASE WHEN tipo=2 THEN votos ELSE 0 END) brancos,
                sum(CASE WHEN tipo=3 THEN votos ELSE 0 END) nulos
              FROM voto_secao WHERE cargo=1 GROUP BY uf,mun,zona,secao
            ) SELECT upper(b.uf) uf,b.mun,b.zona,b.secao,b.abertura,b.encerramento,
              b.id_confere,b.pleito,c.aptos,c.comparecimento,
              v.flavio,v.lula,v.brancos,v.nulos,s.bu_sha256
            FROM bu b JOIN secao s USING(uf,mun,zona,secao)
            JOIN bu_cargo c USING(uf,mun,zona,secao)
            LEFT JOIN votos v USING(uf,mun,zona,secao)
            WHERE upper(b.uf)!='ZZ' AND c.cargo=1 AND c.eleicao=6258
              AND (s.nsp IS NULL OR s.nsp=0 OR s.nsp=s.secao)
            ORDER BY b.uf,b.mun,b.zona,b.secao
        """)]
    if len(registros) != cat:
        raise ValueError(f"Cobertura incompleta: {len(registros)}/{cat}")
    d = resumir(registros)
    d["catalogo_principais_brasil"] = cat
    d["cobertura_pct"] = 100 * len(registros) / cat
    d["banco"] = str(banco.relative_to(ROOT))
    d["banco_bytes"] = banco.stat().st_size
    saida.mkdir(parents=True, exist_ok=True)
    from .encerramento_logs import carregar_logs, integrar

    integrar(d, carregar_logs(saida, refazer=refazer_logs))
    (saida / "dados.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=2) + "\n"
    )
    colunas = [k for k in d["linhas"][0] if k not in {"acumulado", "ufs"}]
    with (saida / "intervalos.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[*colunas, "principais_ufs"],
            extrasaction="ignore",
            lineterminator="\n",
        )
        w.writeheader()
        for r in d["linhas"]:
            w.writerow(
                dict(
                    r,
                    principais_ufs="; ".join(
                        f"{u['uf']}:{u['secoes']}" for u in r["ufs"]
                    ),
                )
            )
    return d
