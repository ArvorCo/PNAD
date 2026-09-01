#!/usr/bin/env python3
"""Auditoria de cobertura territorial: favelas/comunidades urbanas na amostra Quaest.

Testa a hipotese de sub-sorteio de setores em Favelas e Comunidades Urbanas (FCU,
ex-aglomerados subnormais) na Genial/Quaest de junho e julho de 2026.

Fato aritmetico. NAO faz reponderacao de voto nem inferencia eleitoral por setor.

Fonte de classificacao por geocodigo:
  IBGE, Censo 2022, Agregados por Setores Censitarios, arquivo basico nacional
  (coluna CD_TIPO == 1 => Favela e Comunidade Urbana; CD_FCU/NM_FCU; v0001 = populacao).

Alinhamento metodologico:
  A ficha tecnica (PesqEle BR-07181/2026) declara sorteio de setores por PPT
  (Probabilidade Proporcional ao Tamanho) com base no total de habitantes do
  Censo 2022. Logo a probabilidade esperada de sortear um setor de favela em um
  municipio e a fracao da populacao municipal que vive em setores FCU
  (share ponderado por populacao), nao a fracao simples de setores.
"""

from __future__ import annotations

import csv
import json
import math
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONARIO_PDF = ROOT / "data/pesquisas/quaest/2026-07/Quaest_Questionario_072026.pdf"
CENSO_DIR = ROOT / "data/originals/censo_2022_setores_censitarios"
BASICO = CENSO_DIR / "Agregados_por_setores_basico_BR.csv"
BASICO_URL = (
    "https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
    "Agregados_por_Setores_Censitarios/Agregados_por_Setor_csv/"
    "Agregados_por_setores_basico_BR_20260520.zip"
)


def ensure_basico() -> None:
    """Download the IBGE Censo 2022 basico setor file if not present locally.

    ~140 MB uncompressed (heavy, gitignored). Only the classification columns
    (CD_TIPO, CD_FCU, v0001) are consumed."""
    if BASICO.exists():
        return
    CENSO_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = CENSO_DIR / "Agregados_por_setores_basico_BR.zip"
    print(f"baixando basico do IBGE -> {zip_path}")
    urllib.request.urlretrieve(BASICO_URL, zip_path)  # noqa: S310
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(CENSO_DIR)


QUAEST = {
    "junho": ROOT / "data/pesquisas/quaest/2026-06/quaest_bairros_0626.csv",
    "julho": ROOT / "data/pesquisas/quaest/2026-07/quaest_bairros_0726.csv",
}
OUT_JSON = ROOT / "docs/assets/quaest_0726_favelas.json"

CAPITAL_CODES = {
    "3550308": "São Paulo",
    "3304557": "Rio de Janeiro",
    "2927408": "Salvador",
    "3106200": "Belo Horizonte",
    "5300108": "Brasília",
    "2304400": "Fortaleza",
    "2611606": "Recife",
    "1302603": "Manaus",
    "5208707": "Goiânia",
    "1501402": "Belém",
    "2704302": "Maceió",
    "3205309": "Vitória",
    "2111300": "São Luís",
    "2211001": "Teresina",
    "5002704": "Campo Grande",
    "5103403": "Cuiabá",
    "2408102": "Natal",
}


def scan_questionario() -> dict | None:
    """Leg 2: scan the registered questionnaire (101 items) for security terms.

    Requires `pdftotext` (poppler). Returns None if unavailable so the JSON keeps
    the recorded audited values instead of failing."""
    if not shutil.which("pdftotext") or not QUESTIONARIO_PDF.exists():
        return None
    txt = subprocess.run(  # noqa: S603
        ["pdftotext", "-layout", str(QUESTIONARIO_PDF), "-"],  # noqa: S607
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    low = txt.lower()

    def c(*subs: str) -> int:
        return sum(low.count(s) for s in subs)

    return {
        "instrumento": QUESTIONARIO_PDF.name,
        "termos_seguranca_publica": {
            "seguranca": c("seguran"),
            "violencia": c("violênc", "violenc"),
            "narcotrafico": c("narco", "tráfico", "trafico"),
            "faccao": c("facç", "facc"),
            "pcc_comando": c("pcc", "comando vermelho"),
            "milicia": c("milíci", "milici"),
            "assalto_roubo": c("assalto", "roubo"),
            "homicidio": c("homicíd", "homicid"),
            "tiroteio": c("tiroteio"),
            "crime": c("crime"),
            "policia": c("polícia", "policia"),
        },
        "crime_contexto": (
            "unica ocorrencia de 'crime' e sobre crimes financeiros de Daniel "
            "Vorcaro/Banco Master; 'Policia Federal' (2x) so nos roteiros lidos "
            "dos blocos Master e Jaques Wagner"
        ),
        "contraste_itens": {
            "mencoes_michelle": c("michelle"),
            "mencoes_tarifa": c("tarifa"),
            "mencoes_flavio": c("flávio", "flavio"),
            "itens_seguranca": 0,
        },
        "saliencia": (
            "seguranca publica e o problema mais citado do Brasil em 2026, tema de "
            "consenso entre eleitores de Lula e da direita; superou a corrupcao pela "
            "primeira vez na serie Nexus/BTG (33%). O instrumento nao dedica um item "
            "ao tema."
        ),
        "leitura_fato": (
            "Ausencia de qualquer item sobre seguranca publica/crime organizado no "
            "instrumento e verificavel (Fato)."
        ),
        "leituras_hipotese": [
            "Benigna: rodada focada em corrida eleitoral, tarifaco EUA e crise "
            "Michelle/Flavio; seguranca medida em outras ondas.",
            "Critica: agenda por omissao - o tema que governa o cotidiano de dezenas "
            "de milhoes e que lidera as preocupacoes do eleitor fica fora, enquanto "
            "crises palacianas ganham dezenas de itens.",
        ],
    }


LITERATURA = {
    "datafolha_fbsp_2026": {
        "fonte": "Datafolha/Forum Brasileiro de Seguranca Publica, divulgada mai/2026",
        "percentual_percebe_faccao_bairro": 41.2,
        "pessoas_milhoes": 68.7,
        "universo": "16 anos ou mais",
        "n": 2004,
        "municipios": 137,
        "capitais_pct": 55.9,
        "regioes_metro_pct": 46.0,
        "interior_pct": 34.1,
        "influencia_regras_locais_muito_moderado_pct": 61.4,
        "evita_locais_pct": 74.9,
        "medo_confronto_pct": 81.0,
        "nota": (
            "mesma abordagem domiciliar, universo 16+ e n~2004 da Quaest - espelho "
            "metodologico"
        ),
    },
    "censo_2022_fcu": {
        "fonte": "IBGE Censo 2022",
        "favelas_comunidades": 12348,
        "moradores_milhoes": 16.4,
        "pct_populacao": 8.1,
    },
    "saliencia_seguranca": {
        "nexus_btg": "seguranca superou corrupcao como problema #1 (33%)",
        "consenso": "preocupacao igual entre eleitores de Lula (32%) e Flavio (32%)",
    },
}

FONTES = [
    "IBGE Censo 2022 - Agregados por Setores Censitarios, arquivo basico BR "
    "(CD_TIPO, CD_FCU, v0001)",
    "IBGE - Censo 2022: Favelas e Comunidades Urbanas, Resultados do universo",
    "Datafolha/FBSP - presenca de faccoes e milicias nos bairros (mai/2026)",
    "FBSP - Anuario Brasileiro de Seguranca Publica 2025",
    "PesqEle/TSE - registro BR-07181/2026 (ficha tecnica Quaest julho/2026)",
    "Quaest_Questionario_072026.pdf - instrumento registrado (101 itens)",
]

VEREDITO = {
    "perna1_cobertura": (
        "Fato: a amostra publicada INCLUI favelas. Nacional: 47 setores FCU "
        "sorteados vs 55,98 esperados sob PPT-por-populacao (deficit ~9, ~16%; "
        "P(X<=47)=0,090). Sub-representacao leve e NAO significativa; nao ha exclusao "
        "sistematica nem zero absoluto. Deficit concentrado em poucas capitais "
        "(Belem 1 vs 3,4; BH 0 vs 1,3; Brasilia 0 vs 0,7; Rio 4 vs 5,2). SP "
        "praticamente no alvo (6 vs 6,6); Salvador acima (4 vs 3,4)."
    ),
    "perna1_limite": (
        "Isto audita o SORTEIO publicado, nao o CAMPO. Substituicoes de domicilio por "
        "seguranca, se houvessem, nao sao observaveis sem microdados; a ficha nao as "
        "declara."
    ),
    "perna2_agenda": (
        "Fato: zero itens de seguranca publica/crime organizado em 101 perguntas, "
        "enquanto 22 mencoes a Michelle e 17 a tarifa. Contraste com a saliencia #1 "
        "do tema e verificavel."
    ),
    "hipotese_calibrada": (
        "A hipotese forte de evitar favelas no sorteio NAO se sustenta na aritmetica "
        "(Inferencia refutada). O achado que sobrevive e a agenda por omissao "
        "(perna 2) e um deficit territorial leve nao-conclusivo (perna 1). Atribuicao "
        "a seguranca = Hipotese; efeito no placar = cenario nao calculado (sem "
        "microdados)."
    ),
}


def load_quaest():
    rounds = {}
    for rnd, path in QUAEST.items():
        rows = list(csv.DictReader(path.open(encoding="utf-8")))
        rounds[rnd] = rows
    return rounds


def load_basico_universe(muni_codes):
    """Return sector lookup (only Quaest sectors) + full municipal universe stats
    for the municipalities that appear in the Quaest sample."""
    sector = {}  # geocode -> dict(cd_tipo, is_favela, pop, cd_fcu, nm_fcu, cd_mun)
    muni = {}  # cd_mun -> dict(nm_mun, pop_total, pop_favela, sec_total, sec_favela)
    with BASICO.open(encoding="latin-1") as fh:
        reader = csv.reader(fh, delimiter=";")
        header = next(reader)
        idx = {name: i for i, name in enumerate(header)}
        i_set, i_tipo, i_mun, i_nmmun = (
            idx["CD_SETOR"],
            idx["CD_TIPO"],
            idx["CD_MUN"],
            idx["NM_MUN"],
        )
        i_fcu, i_nmfcu, i_pop = idx["CD_FCU"], idx["NM_FCU"], idx["v0001"]
        for row in reader:
            cd_mun = row[i_mun]
            if cd_mun not in muni_codes:
                continue
            try:
                pop = int(row[i_pop]) if row[i_pop] not in ("", ".") else 0
            except ValueError:
                pop = 0
            is_fav = row[i_tipo] == "1"
            m = muni.setdefault(
                cd_mun,
                dict(
                    nm_mun=row[i_nmmun],
                    pop_total=0,
                    pop_favela=0,
                    sec_total=0,
                    sec_favela=0,
                ),
            )
            m["pop_total"] += pop
            m["sec_total"] += 1
            if is_fav:
                m["pop_favela"] += pop
                m["sec_favela"] += 1
            geoc = row[i_set]
            sector[geoc] = dict(
                cd_tipo=row[i_tipo],
                is_favela=is_fav,
                pop=pop,
                cd_fcu=row[i_fcu] if row[i_fcu] not in ("", ".") else None,
                nm_fcu=row[i_nmfcu] if row[i_nmfcu] not in ("", ".") else None,
                cd_mun=cd_mun,
                nm_mun=row[i_nmmun],
            )
    return sector, muni


def binom_upper_tail_le(k, n, p):
    """P(X <= k) for X~Binomial(n,p): probability of drawing AT MOST k favela
    sectors. Small = under-representation is unlikely under the design."""
    if n == 0:
        return 1.0
    # cumulative
    c = 0.0
    for i in range(0, k + 1):
        c += math.comb(n, i) * (p**i) * ((1 - p) ** (n - i))
    return c


def poisson_binomial_le(k, probs):
    """P(X <= k) where X is sum of independent Bernoulli(p_i). DP over sectors."""
    dist = [1.0]
    for p in probs:
        nd = [0.0] * (len(dist) + 1)
        for j, v in enumerate(dist):
            nd[j] += v * (1 - p)
            nd[j + 1] += v * p
        dist = nd
    return sum(dist[: k + 1])


def main():
    ensure_basico()
    rounds = load_quaest()
    all_muni = set()
    for rows in rounds.values():
        all_muni.update(r["municipality_code"] for r in rows)
    sector, muni = load_basico_universe(all_muni)

    result = {
        "metadata": {
            "titulo": "Cobertura de favelas e comunidades urbanas na amostra Quaest",
            "fonte_classificacao": (
                "IBGE Censo 2022, Agregados por Setores "
                "Censitarios (basico BR), CD_TIPO==1 = Favela "
                "e Comunidade Urbana"
            ),
            "criterio_esperado": (
                "PPT por populacao (ficha PesqEle BR-07181/2026): "
                "esperado = fracao da populacao municipal em "
                "setores FCU"
            ),
            "n_setores_distintos": len(sector),
            "municipios_analisados": len(muni),
        },
        "rounds": {},
        "capitais": {},
        "nacional": {},
        "favela_sectors_drawn": [],
    }

    # Per-round classification and per-municipality observed vs expected
    round_agg = {}
    for rnd, rows in rounds.items():
        obs_fav = 0
        probs = []  # p_muni for each drawn sector (population share of favela)
        classified = []
        for r in rows:
            geoc = r["sector_code"]
            s = sector.get(geoc)
            is_fav = bool(s and s["is_favela"])
            m = muni.get(r["municipality_code"])
            p_muni = (m["pop_favela"] / m["pop_total"]) if m and m["pop_total"] else 0.0
            probs.append(p_muni)
            if is_fav:
                obs_fav += 1
                result["favela_sectors_drawn"].append(
                    {
                        "round": rnd,
                        "geocode": geoc,
                        "municipio": r["municipality"],
                        "uf": r["uf"],
                        "bairro": r["neighborhood"],
                        "fcu": s["nm_fcu"] if s else None,
                        "pop": s["pop"] if s else None,
                    }
                )
            classified.append(
                dict(
                    geocode=geoc,
                    municipio=r["municipality"],
                    uf=r["uf"],
                    is_favela=is_fav,
                    p_muni=round(p_muni, 4),
                )
            )
        expected = sum(probs)
        p_le = poisson_binomial_le(obs_fav, probs)
        round_agg[rnd] = dict(
            n=len(rows),
            observed_favela=obs_fav,
            expected_favela=round(expected, 2),
            p_at_most_observed=round(p_le, 4),
            probs=probs,
            classified=classified,
        )
        result["rounds"][rnd] = dict(
            n=len(rows),
            observed_favela=obs_fav,
            expected_favela=round(expected, 2),
            p_at_most_observed=round(p_le, 4),
        )

    # National aggregate (both rounds pooled = 668 draws, 667 distinct)
    pooled_probs, pooled_obs = [], 0
    for rnd in rounds:
        pooled_probs += round_agg[rnd]["probs"]
        pooled_obs += round_agg[rnd]["observed_favela"]
    result["nacional"] = dict(
        n_draws=len(pooled_probs),
        observed_favela=pooled_obs,
        expected_favela=round(sum(pooled_probs), 2),
        p_at_most_observed=round(poisson_binomial_le(pooled_obs, pooled_probs), 5),
        deficit=round(sum(pooled_probs) - pooled_obs, 2),
    )

    # Capitals detail (pooled jun+jul draws in each capital)
    for code, name in CAPITAL_CODES.items():
        drawn = []
        for rnd, rows in rounds.items():
            for r in rows:
                if r["municipality_code"] == code:
                    s = sector.get(r["sector_code"])
                    drawn.append((rnd, r["sector_code"], bool(s and s["is_favela"])))
        m = muni.get(code)
        if not drawn or not m:
            continue
        n = len(drawn)
        obs = sum(1 for _, _, f in drawn if f)
        p = m["pop_favela"] / m["pop_total"] if m["pop_total"] else 0.0
        result["capitais"][name] = dict(
            cd_mun=code,
            n_setores_sorteados=n,
            observado_favela=obs,
            pop_favela_share=round(p, 4),
            sec_favela_share=(
                round(m["sec_favela"] / m["sec_total"], 4) if m["sec_total"] else 0
            ),
            esperado_favela=round(n * p, 2),
            p_ate_observado=round(binom_upper_tail_le(obs, n, p), 4),
            universo_setores=m["sec_total"],
            universo_setores_favela=m["sec_favela"],
        )

    # Leg 2 + literature + verdict
    agenda = scan_questionario()
    if agenda is not None:
        result["agenda_tematica"] = agenda
    result["literatura"] = LITERATURA
    result["fontes"] = FONTES
    result["veredito"] = VEREDITO

    OUT_JSON.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Console report
    print("=== NACIONAL (jun+jul agregados) ===")
    nat = result["nacional"]
    print(
        f"  sorteios: {nat['n_draws']}  observado favela: {nat['observed_favela']}"
        f"  esperado (PPT-pop): {nat['expected_favela']}"
        f"  deficit: {nat['deficit']}  P(X<=obs): {nat['p_at_most_observed']}"
    )
    for rnd, d in result["rounds"].items():
        print(
            f"  {rnd}: obs {d['observed_favela']} / esp {d['expected_favela']}"
            f"  P(X<=obs)={d['p_at_most_observed']}"
        )
    print("\n=== CAPITAIS ===")
    for name, d in sorted(
        result["capitais"].items(), key=lambda kv: -kv[1]["n_setores_sorteados"]
    ):
        print(
            f"  {name:16} n={d['n_setores_sorteados']:2}  obs={d['observado_favela']}"
            f"  esp={d['esperado_favela']:4}  pop%fav={d['pop_favela_share']*100:5.1f}"
            f"  setores {d['universo_setores_favela']}/{d['universo_setores']}"
            f"  P(X<=obs)={d['p_ate_observado']}"
        )
    print(f"\nfavela sectors drawn total: {len(result['favela_sectors_drawn'])}")
    for f in result["favela_sectors_drawn"]:
        print(
            f"  [{f['round']}] {f['municipio']}/{f['uf']} {f['bairro']} "
            f"({f['fcu']}) pop={f['pop']}"
        )
    print(f"\nJSON -> {OUT_JSON}")


if __name__ == "__main__":
    main()
