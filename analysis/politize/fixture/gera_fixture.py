"""Gera a fixture mínima do app Politize (dados INVENTADOS, marcados como fixture).

Uso: python3 analysis/politize/fixture/gera_fixture.py analysis/politize/fixture

Um município (Rio Branco, AC) com seis locais inventados. As métricas seguem as
fórmulas do contrato (analysis/politize/CONTRATO.md) para o app ter números
coerentes; nenhum número aqui descreve local real. A malha e a pergunta da
Quaest são copiadas dos arquivos reais do repositório.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
COLUNAS = [
    "local_id",
    "local_nr",
    "zona",
    "nome",
    "endereco",
    "bairro",
    "cep",
    "lat",
    "lon",
    "tipo_local",
    "secoes",
    "aptos",
    "comparecimento",
    "flavio",
    "lula",
    "terceira",
    "brancos",
    "nulos",
    "flavio_v",
    "lula_v",
    "terceira_v",
    "flavio_a",
    "lula_a",
    "terceira_a",
    "bn_a",
    "abst_a",
    "margem_v",
    "cobertura_2022",
    "bolsonaro22_1t_v",
    "lula22_1t_v",
    "bolsonaro22_2t_v",
    "lula22_2t_v",
    "abst22_2t_a",
    "reencontro_a",
    "fem",
    "a16_24",
    "a25_34",
    "a35_44",
    "a45_59",
    "a60",
    "fund_inc",
    "fund_med",
    "med_sup_inc",
    "superior",
    "setor_situacao",
    "setor_tipo",
    "renda_ate2",
    "renda_de2a5",
    "renda_mais5",
    "renda_mediana_brl",
    "esperado_flavio_v",
    "vao_perfil_pp",
    "c_terceira",
    "c_ausentes",
    "c_reencontro",
    "c_perfil",
    "potencial",
    "indice",
    "arquetipo",
    "arquetipo_secundario",
    "flavio_2t",
    "lula_2t",
    "faltam",
    "conversas_para_virar",
    "conversas_para_segurar",
    "em_aberto",
    "bna",
    "viravel",
]
# nr, nome, bairro, cep, lat, lon, aptos, comparecimento, flavio, lula, terceira,
# brancos, nulos, bolsonaro22_1t_v, abst22_2t_a, esperado_flavio_v, escolaridade, renda
LOCAIS = [
    (
        9001,
        "FIXTURE Escola Inventada Sol Nascente",
        "Bosque",
        "69900901",
        -9.9705,
        -67.8160,
        2100,
        1700,
        1080,
        480,
        90,
        25,
        25,
        66.0,
        18.0,
        63.0,
        (20, 22, 40, 18),
        (30, 45, 25, 4200),
    ),
    (
        9002,
        "FIXTURE Colégio Inventado Pôr do Sol",
        "Centro",
        "69900902",
        -9.9745,
        -67.8095,
        1800,
        1450,
        640,
        610,
        140,
        30,
        30,
        56.0,
        20.0,
        52.0,
        (25, 25, 35, 15),
        (40, 42, 18, 3300),
    ),
    (
        9003,
        "FIXTURE Escola Inventada Ventania",
        "Floresta",
        "69900903",
        -9.9780,
        -67.8290,
        1500,
        1150,
        470,
        480,
        150,
        25,
        25,
        51.0,
        22.0,
        50.0,
        (35, 28, 30, 7),
        (52, 38, 10, 2600),
    ),
    (
        9004,
        "FIXTURE Escola Inventada Cajueiro",
        "Estação Experimental",
        "69900904",
        -9.9640,
        -67.8380,
        1650,
        1200,
        520,
        600,
        40,
        20,
        20,
        58.0,
        24.0,
        47.0,
        (38, 27, 28, 7),
        (55, 37, 8, 2400),
    ),
    (
        9005,
        "FIXTURE Clube Inventado Ribeirinho",
        "Aeroporto Velho",
        "69900905",
        -9.9850,
        -67.8225,
        1300,
        860,
        330,
        470,
        30,
        15,
        15,
        40.0,
        30.0,
        41.0,
        (48, 26, 22, 4),
        (66, 29, 5, 1900),
    ),
    (
        9006,
        "FIXTURE Igreja Inventada Seringal",
        "Cidade Nova",
        "69900906",
        -9.9930,
        -67.8020,
        1700,
        1280,
        300,
        880,
        50,
        25,
        25,
        30.0,
        22.0,
        36.0,
        (50, 25, 21, 4),
        (70, 26, 4, 1700),
    ),
]
FLAVIO_TERCEIRA = 0.427
LULA_TERCEIRA = 0.273
TAXA_CONVERSAO = 0.35
TETO = 40


def r1(x: float | None) -> float | None:
    return None if x is None else round(x, 1)


def arquetipos(m: dict) -> tuple[str, str | None]:
    regras = [
        ("fortaleza", m["flavio_v"] >= 60),
        ("muro", m["lula_v"] >= 65),
        ("pendulo", abs(m["margem_v"]) <= 6),
        ("reencontro", m["reencontro_a"] >= 5),
        ("fertil", m["terceira_v"] + m["bn_v"] >= 12),
        ("dormindo", m["abst_a"] >= 28),
        ("abaixo_do_perfil", m["vao_perfil_pp"] >= 5),
        ("frente", m["margem_v"] > 6),
        ("atras", True),
    ]
    batem = [codigo for codigo, ok in regras if ok]
    segundo = batem[1] if len(batem) > 1 and batem[1] != "atras" else None
    return batem[0], segundo


def viravel(flavio: int, lula: int, bna: int) -> str | None:
    """Regra do contrato: só branco, nulo e abstenção (bna) >= diferença."""
    if lula > flavio and bna >= lula - flavio:
        return "flavio"
    if flavio > lula and bna >= flavio - lula:
        return "lula"
    return None


def linha_local(i: int, dados: tuple) -> dict:
    (
        nr,
        nome,
        bairro,
        cep,
        lat,
        lon,
        aptos,
        comp,
        fl,
        lu,
        te,
        br,
        nu,
        b22,
        a22,
        esp,
        esc,
        ren,
    ) = dados
    validos = fl + lu + te
    m = {
        "flavio_v": 100 * fl / validos,
        "lula_v": 100 * lu / validos,
        "terceira_v": 100 * te / validos,
        "bn_v": 100 * (br + nu) / validos,
        "flavio_a": 100 * fl / aptos,
        "lula_a": 100 * lu / aptos,
        "terceira_a": 100 * te / aptos,
        "bn_a": 100 * (br + nu) / aptos,
        "abst_a": 100 * (aptos - comp) / aptos,
    }
    m["margem_v"] = m["flavio_v"] - m["lula_v"]
    m["reencontro_a"] = max(0.0, b22 * 0.78 - m["flavio_a"])
    m["vao_perfil_pp"] = esp - m["flavio_v"]
    c_t = m["terceira_a"] + m["bn_a"]
    c_a = 0.5 * m["abst_a"]
    c_r = m["reencontro_a"]
    c_p = max(0.0, m["vao_perfil_pp"]) * validos / aptos
    potencial = c_t + c_a + c_r + c_p
    principal, secundario = arquetipos(m)
    f2 = fl + FLAVIO_TERCEIRA * te
    l2 = lu + LULA_TERCEIRA * te
    faltam = round(l2 - f2) + 1 if l2 >= f2 else 0
    sem_2022 = i == 4
    return {
        "local_id": f"AC-01392-9-{nr}",
        "local_nr": nr,
        "zona": 9,
        "nome": nome,
        "endereco": f"Rua Inventada, {100 + i * 37} (fixture)",
        "bairro": bairro,
        "cep": cep,
        "lat": lat,
        "lon": lon,
        "tipo_local": "Convencional",
        "secoes": max(1, aptos // 380),
        "aptos": aptos,
        "comparecimento": comp,
        "flavio": fl,
        "lula": lu,
        "terceira": te,
        "brancos": br,
        "nulos": nu,
        **{
            k: r1(m[k])
            for k in (
                "flavio_v",
                "lula_v",
                "terceira_v",
                "flavio_a",
                "lula_a",
                "terceira_a",
                "bn_a",
                "abst_a",
                "margem_v",
            )
        },
        "cobertura_2022": None if sem_2022 else 0.95,
        "bolsonaro22_1t_v": None if sem_2022 else b22,
        "lula22_1t_v": None if sem_2022 else r1(100 - b22 - 6),
        "bolsonaro22_2t_v": None if sem_2022 else r1(b22 + 3),
        "lula22_2t_v": None if sem_2022 else r1(97 - b22),
        "abst22_2t_a": a22,
        "reencontro_a": r1(m["reencontro_a"]),
        "fem": 52.0 + i,
        "a16_24": 14.0,
        "a25_34": 19.0 + i,
        "a35_44": 21.0,
        "a45_59": 25.0 - i,
        "a60": 21.0,
        "fund_inc": esc[0],
        "fund_med": esc[1],
        "med_sup_inc": esc[2],
        "superior": esc[3],
        "setor_situacao": "urbana",
        "setor_tipo": "favela" if i == 5 else "comum",
        "renda_ate2": ren[0],
        "renda_de2a5": ren[1],
        "renda_mais5": ren[2],
        "renda_mediana_brl": ren[3],
        "esperado_flavio_v": esp,
        "vao_perfil_pp": r1(m["vao_perfil_pp"]),
        "c_terceira": r1(c_t),
        "c_ausentes": r1(c_a),
        "c_reencontro": r1(c_r),
        "c_perfil": r1(c_p),
        "potencial": r1(potencial),
        "indice": round(100 * min(1.0, potencial / TETO)),
        "arquetipo": principal,
        "arquetipo_secundario": secundario,
        "flavio_2t": round(f2),
        "lula_2t": round(l2),
        "faltam": faltam,
        "conversas_para_virar": round(faltam / TAXA_CONVERSAO) if faltam else None,
        "conversas_para_segurar": None if faltam else round(f2 * a22 / 100),
        "em_aberto": te + br + nu + aptos - comp,
        "bna": br + nu + aptos - comp,
        "viravel": viravel(fl, lu, br + nu + aptos - comp),
    }


COLUNAS_SECAO = [
    "secao",
    "local_id",
    "mun_tse",
    "local",
    "bairro",
    "aptos",
    "comparecimento",
    "flavio",
    "lula",
    "terceira",
    "brancos",
    "nulos",
    "flavio_v",
    "lula_v",
    "terceira_v",
    "abst_a",
    "bn_a",
    "margem_v",
    "cobertura_2022",
    "bolsonaro22_1t_v",
    "lula22_1t_v",
    "bolsonaro22_2t_v",
    "lula22_2t_v",
    "reencontro_a",
    "perfil_fonte",
    "fem",
    "a16_24",
    "a25_34",
    "a35_44",
    "a45_59",
    "a60",
    "fund_inc",
    "fund_med",
    "med_sup_inc",
    "superior",
    "indice",
    "arquetipo",
    "faltam",
    "conversas_para_virar",
    "agregadas",
]


def secoes_do_local(j: int, loc: dict) -> list[dict]:
    """Divide o local inventado em duas seções inventadas, 55% e 45% de cada contagem."""
    saida = []
    for k, peso in enumerate((0.55, 0.45)):
        desvio = 1 + (0.06 if k == 0 else -0.07)
        conta = {
            c: round(loc[c] * peso)
            for c in ("aptos", "comparecimento", "brancos", "nulos")
        }
        conta["flavio"] = round(loc["flavio"] * peso * desvio)
        conta["lula"] = round(loc["lula"] * peso * (2 - desvio))
        conta["terceira"] = round(loc["terceira"] * peso)
        validos = conta["flavio"] + conta["lula"] + conta["terceira"]
        aptos = conta["aptos"]
        flavio_v = 100 * conta["flavio"] / validos
        lula_v = 100 * conta["lula"] / validos
        f2 = conta["flavio"] + FLAVIO_TERCEIRA * conta["terceira"]
        l2 = conta["lula"] + LULA_TERCEIRA * conta["terceira"]
        faltam = round(l2 - f2) + 1 if l2 >= f2 else 0
        saida.append(
            {
                "secao": 100 + j * 10 + k,
                "local_id": loc["local_id"],
                "mun_tse": "01392",
                "local": loc["nome"],
                "bairro": loc["bairro"],
                **conta,
                "flavio_v": r1(flavio_v),
                "lula_v": r1(lula_v),
                "terceira_v": r1(100 * conta["terceira"] / validos),
                "abst_a": r1(100 * (aptos - conta["comparecimento"]) / aptos),
                "bn_a": r1(100 * (conta["brancos"] + conta["nulos"]) / aptos),
                "margem_v": r1(flavio_v - lula_v),
                **{
                    c: loc[c]
                    for c in (
                        "cobertura_2022",
                        "bolsonaro22_1t_v",
                        "lula22_1t_v",
                        "bolsonaro22_2t_v",
                        "lula22_2t_v",
                        "reencontro_a",
                        "fem",
                        "a16_24",
                        "a25_34",
                        "a35_44",
                        "a45_59",
                        "a60",
                        "fund_inc",
                        "fund_med",
                        "med_sup_inc",
                        "superior",
                        "arquetipo",
                    )
                },
                "perfil_fonte": "secao",
                "indice": max(0, min(100, loc["indice"] + (4 if k == 0 else -5))),
                "faltam": faltam,
                "conversas_para_virar": (
                    round(faltam / TAXA_CONVERSAO) if faltam else None
                ),
                "agregadas": [150 + j] if k == 1 and j == 2 else [],
            }
        )
    return saida


def gravar(saida: Path, rel: str, obj: dict) -> None:
    alvo = saida / rel
    alvo.parent.mkdir(parents=True, exist_ok=True)
    alvo.write_text(
        json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )


def main(saida: Path) -> None:
    locais = [linha_local(i, d) for i, d in enumerate(LOCAIS)]
    linhas = [[loc[c] for c in COLUNAS] for loc in locais]
    soma = {
        k: sum(loc[k] for loc in locais)
        for k in (
            "aptos",
            "comparecimento",
            "flavio",
            "lula",
            "terceira",
            "brancos",
            "nulos",
        )
    }
    validos = soma["flavio"] + soma["lula"] + soma["terceira"]
    totais = {
        **soma,
        "flavio_v": r1(100 * soma["flavio"] / validos),
        "lula_v": r1(100 * soma["lula"] / validos),
        "terceira_v": r1(100 * soma["terceira"] / validos),
        "abst_a": r1(100 * (soma["aptos"] - soma["comparecimento"]) / soma["aptos"]),
    }
    gravar(
        saida,
        "mun/AC/01392.json",
        {
            "fixture": True,
            "uf": "AC",
            "mun_tse": "01392",
            "ibge": "1200401",
            "nome": "Rio Branco",
            "totais": totais,
            "perfil_fonte": "secao",
            "locais": {"colunas": COLUNAS, "linhas": linhas},
        },
    )
    secoes = [sec for j, loc in enumerate(locais) for sec in secoes_do_local(j, loc)]
    gravar(
        saida,
        "zona/AC/9.json",
        {
            "fixture": True,
            "uf": "AC",
            "zona": 9,
            "municipios": [{"mun_tse": "01392", "nome": "Rio Branco"}],
            "secoes": {
                "colunas": COLUNAS_SECAO,
                "linhas": [[sec[c] for c in COLUNAS_SECAO] for sec in secoes],
            },
        },
    )
    gravar(
        saida,
        "cep/69.json",
        {
            "exato": {loc["cep"]: [loc["local_id"]] for loc in locais},
            "prefixo5": {"69900": [loc["local_id"] for loc in locais]},
        },
    )
    problemas = json.loads(
        (RAIZ / "analysis/voto_util/problemas_quaest_092026.json").read_text()
    )
    acre = problemas["estados"]["AC"]
    gravar(
        saida,
        "uf/AC.json",
        {
            "fixture": True,
            "uf": "AC",
            "nome": "Acre",
            "regiao": "Norte",
            "totais": totais,
            "problemas": {
                "pergunta": problemas["pergunta"],
                "campo": acre["campo"],
                "valores": acre["valores"],
                "fonte": acre["arquivo"],
                "pagina": acre["pagina"],
            },
            "municipios_mais_disputados": [],
            "ranking_indice": [],
        },
    )
    malha = json.loads((RAIZ / "apuracao/public/geo/mun/AC.geojson").read_text())
    malha["features"] = [
        f
        for f in malha["features"]
        if f["properties"]["codarea"] in ("1200401", "1200450", "1200013")
    ]
    gravar(saida, "geo/AC.geojson", malha)
    gravar(
        saida,
        "indice.json",
        {
            "fixture": True,
            "aviso": "FIXTURE do aplicativo: um município com seis locais inventados. Não é dado real.",
            "gerado_em": "2026-10-07T12:00:00-03:00",
            "versao_contrato": "1.0",
            "fontes": [
                {
                    "chave": "fixture",
                    "caminho": "analysis/politize/fixture/",
                    "bytes": 12345,
                    "sha256": "0" * 64,
                    "data": "2026-10-07",
                },
                {
                    "chave": "malha_municipal",
                    "caminho": "apuracao/public/geo/mun/AC.geojson",
                    "bytes": 31052,
                    "sha256": "ab" * 32,
                    "data": "2026-10-03",
                },
            ],
            "parametros": {
                "taxa_conversao": TAXA_CONVERSAO,
                "transferencia_terceira": {
                    "sem_escolha": 0.30,
                    "flavio_entre_escolhem": 0.61,
                },
                "teto_potencial": TETO,
                "p99_potencial": 38.2,
                "recentragem": {"esperado_bruto_flavio": 45.0, "urna_flavio": 47.03},
            },
            "nacional": {
                "aptos": soma["aptos"],
                "n_locais": len(locais),
                "flavio_v": 47.03,
                "lula_v": 45.16,
                "votos_em_aberto": sum(loc["em_aberto"] for loc in locais),
                "em_aberto": {
                    "terceira": soma["terceira"],
                    "brancos": soma["brancos"],
                    "nulos": soma["nulos"],
                    "abstencao": soma["aptos"] - soma["comparecimento"],
                },
                "locais_viraveis_flavio": sum(
                    loc["viravel"] == "flavio" for loc in locais
                ),
                "aptos_locais_viraveis_flavio": sum(
                    loc["aptos"] for loc in locais if loc["viravel"] == "flavio"
                ),
                "locais_viraveis_lula": sum(loc["viravel"] == "lula" for loc in locais),
                "locais_com_boletim": len(locais),
                "secoes_com_boletim": 12,
            },
            "zonas": {"AC": [1, 9]},
            "ufs": [
                {
                    "uf": "AC",
                    "nome": "Acre",
                    "aptos": soma["aptos"],
                    "flavio_v": totais["flavio_v"],
                    "lula_v": totais["lula_v"],
                    "abst_a": totais["abst_a"],
                    "n_locais": len(locais),
                    "arquivo": "uf/AC.json",
                }
            ],
            "municipios": {
                "colunas": [
                    "uf",
                    "mun_tse",
                    "ibge",
                    "nome",
                    "lat",
                    "lon",
                    "n_locais",
                    "aptos",
                    "flavio_v",
                    "lula_v",
                    "arquivo",
                ],
                "linhas": [
                    [
                        "AC",
                        "01392",
                        "1200401",
                        "Rio Branco",
                        -9.975,
                        -67.82,
                        len(locais),
                        soma["aptos"],
                        totais["flavio_v"],
                        totais["lula_v"],
                        "mun/AC/01392.json",
                    ]
                ],
            },
        },
    )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
