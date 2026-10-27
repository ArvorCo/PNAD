"""Seções com zero voto num finalista: 2º e 1º turno de 2026 contra 2022.

Ponto de partida: a manchete da Folha de S.Paulo de 27/10/2026, "Flávio teve zero
voto em 106 urnas, nas quais Lula somou quase 15 mil". Este módulo refaz a conta
seção a seção sobre as fontes lidas por ``zeros_base`` e grava
``analysis/apuracao_2t_2026/dados/zeros.json``, que o bloco "Seções com zero voto"
do capítulo Grupos (``pagina_fig_zeros``) publica.

Definições declaradas:

- **zero voto**: a seção tem BU do cargo presidente (``bu_cargo``, cargo 1) e
  nenhuma linha nominal do candidato em ``voto_secao``; candidato sem linha é zero
  voto. Seção sem comparecimento conta como zero para os dois finalistas; no 2º
  turno de 2026 isso só acontece no exterior.
- **2022**: linha do arquivo por seção com votos preenchidos; linha vazia fica fora.
- **Brasil**: sem a UF ``zz`` (exterior) no número principal; o exterior sai à parte.
- **Tipo do local**: regra de ``zeros_base.TIPOS``, pelo nome do prédio.

``ESPERADO`` guarda os números conferidos antes da execução; ``conferir`` levanta
``AssertionError`` com a lista de divergências, sem ajustar nada. Rótulo de tudo:
atipicidade pede explicação, não prova irregularidade.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from apuracao_2026.dados import REGIOES, regiao

from .zeros_base import (
    ANOMALIA,
    BANCO_1T,
    BANCO_2T,
    CANDIDATOS,
    CSV_2022,
    DEFINICAO,
    FAIXAS_APTOS,
    INDICE,
    MANCHETE,
    MUNICIPIOS_COMUNIDADE,
    NOME_TIPO,
    ORDEM_TIPOS,
    OUTRO,
    REFERENCIA,
    ROOT,
    ROTULO,
    SAIDA,
    SCRIPT,
    TIPOS,
    Chave,
    Politize,
    Secao,
    Secao22,
    agora_utc,
    ler_2022,
    ler_banco,
    ler_mistura,
    mediana,
    nomes_municipios,
    pct,
    quartis,
    rel,
    sha256,
    tipo_e_regra,
    tipo_local,
)

# Números conferidos pelo autor antes de escrever o script; ``conferir`` compara.
ESPERADO = {
    "2026_2t_direita": (106, 14_860),
    "2026_2t_lula": (4, 296),
    "2026_2t_direita_com_exterior": 108,
    "2026_2t_lula_com_exterior": 6,
    "2026_1t_direita": 79,
    "2026_1t_lula": 8,
    "2022_2t_direita": (141, 16_418),
    "2022_2t_lula": (2, 118),
    "2022_1t_direita": 160,
    "2022_1t_lula": 1,
    "ufs_2026_2t": {"AM": 30, "MA": 20, "PA": 16, "RR": 8, "TO": 7},
    "municipios": 67,
    # A conta prévia dava 165, que é a mediana alta (54º de 106 valores); a mediana
    # usual é a média do 53º e do 54º (157 e 165), 161. Fica a usual.
    "aptos_mediana": 161,
    "aptos_soma": 18_508,
    "comparecimento_soma": 15_222,
    "flavio_1t_soma": 118,
    "flavio_1t_zero": 50,
    "flavio_1t_ate_5": 105,
    "repete_2022_zero_bolsonaro": 23,
    "politize_2022_pareadas": 61,
    "politize_2022_mediana": 0.6,
    "politize_2022_zeros": 23,
}


# ------------------------------------------------------------------ contagens


def votos_2026(secoes: dict[Chave, Secao]) -> dict[Chave, tuple[int, int]]:
    """(lula, direita) por seção."""
    return {ch: (s.lula, s.flavio) for ch, s in secoes.items()}


def votos_2022(s22: dict[Chave, Secao22], turno: int) -> dict[Chave, tuple[int, int]]:
    """(lula, direita) por seção de 2022; linha sem voto preenchido fica fora."""
    out = {}
    for ch, s in s22.items():
        lu = s.lula_1t if turno == 1 else s.lula_2t
        bo = s.bolsonaro_1t if turno == 1 else s.bolsonaro_2t
        if lu is not None and bo is not None:
            out[ch] = (lu, bo)
    return out


def zeros(votos: dict[Chave, tuple[int, int]], lado: str) -> list[Chave]:
    """Seções com zero voto no lado pedido ('direita' ou 'lula'), ordenadas."""
    j = 1 if lado == "direita" else 0
    return sorted(ch for ch, v in votos.items() if v[j] == 0)


def recorte(
    votos: dict[Chave, tuple[int, int]], ano: int, turno: int, lado: str, exterior: bool
) -> dict[str, Any]:
    v = {ch: x for ch, x in votos.items() if (ch[0] == "ZZ") == exterior}
    zs = zeros(v, lado)
    adv = 0 if lado == "direita" else 1
    nomes = CANDIDATOS[ano]
    return {
        "ano": ano,
        "turno": turno,
        "lado": lado,
        "candidato": nomes[lado],
        "adversario": nomes["lula" if lado == "direita" else "direita"],
        "secoes": len(zs),
        "votos_adversario": sum(v[ch][adv] for ch in zs),
        "universo_secoes": len(v),
        "por_100_mil_secoes": round(1e5 * len(zs) / len(v), 2) if v else None,
    }


def por_uf(
    votos: dict[tuple[int, int], dict[Chave, tuple[int, int]]],
) -> list[dict[str, Any]]:
    ufs = sorted({ch[0] for v in votos.values() for ch in v if ch[0] != "ZZ"})
    out = []
    for uf in ufs:
        linha: dict[str, Any] = {"uf": uf}
        for (ano, turno), v in votos.items():
            sel = {ch: x for ch, x in v.items() if ch[0] == uf}
            linha[f"secoes_{ano}_{turno}t"] = len(sel)
            linha[f"zero_direita_{ano}_{turno}t"] = len(zeros(sel, "direita"))
            linha[f"zero_lula_{ano}_{turno}t"] = len(zeros(sel, "lula"))
        out.append(linha)
    return sorted(
        out,
        key=lambda x: (-x["zero_direita_2026_2t"], -x["zero_direita_2022_2t"], x["uf"]),
    )


def por_regiao(
    votos: dict[tuple[int, int], dict[Chave, tuple[int, int]]],
) -> list[dict[str, Any]]:
    """Seções sem voto no candidato da direita por grande região, quatro recortes."""
    out = []
    for rg in REGIOES:
        linha: dict[str, Any] = {"regiao": rg}
        for (ano, turno), v in votos.items():
            sel = {
                ch: x for ch, x in v.items() if ch[0] != "ZZ" and regiao(ch[0]) == rg
            }
            brasil = sum(1 for ch in v if ch[0] != "ZZ")
            n = len(zeros(sel, "direita"))
            tot = len(zeros({c: x for c, x in v.items() if c[0] != "ZZ"}, "direita"))
            linha[f"zero_direita_{ano}_{turno}t"] = n
            linha[f"pct_da_lista_{ano}_{turno}t"] = pct(n, tot, 1)
            linha[f"pct_das_secoes_{ano}_{turno}t"] = pct(len(sel), brasil, 1)
        out.append(linha)
    return out


def contar_tipos(itens: list[dict[str, Any]], campo_votos: str) -> list[dict]:
    c = Counter(x["tipo"] for x in itens)
    votos = Counter()
    for x in itens:
        votos[x["tipo"]] += x.get(campo_votos) or 0
    total = len(itens)
    return [
        {
            "tipo": k,
            "nome": NOME_TIPO[k],
            "secoes": c.get(k, 0),
            "pct": pct(c.get(k, 0), total, 1),
            "votos_adversario": votos.get(k, 0),
        }
        for k in ORDEM_TIPOS
    ]


# ------------------------------------------------------------------ fichas


def ficha_2026(
    ch: Chave,
    s2: Secao,
    s1: Secao | None,
    s22: Secao22 | None,
    pol: dict | None,
    muns: dict[tuple[str, str], str],
    mistura: dict[str, Any],
) -> dict[str, Any]:
    uf, mun, zona, secao = ch
    municipio = muns.get((uf, mun)) or mun
    local = pol.get("local") if pol else None
    tipo, regra = tipo_e_regra(local, uf, municipio)
    b22 = pol.get("bolsonaro22_2t_v") if pol else None
    grupo = None
    if mistura.get("disponivel"):
        g = mistura["grupos"].get(ch)
        grupo = None if g is None else {"id": g[0], "atipico": bool(g[1])}
    return {
        "uf": uf,
        "mun": mun,
        "municipio": municipio,
        "zona": zona,
        "secao": secao,
        "local": local,
        "tipo": tipo,
        "tipo_regra": regra,
        "modelo_urna": s2.modelo,
        "aptos": s2.aptos,
        "comparecimento": s2.comparecimento,
        "lula": s2.lula,
        "flavio": s2.flavio,
        "brancos": s2.brancos,
        "nulos": s2.nulos,
        "t1": (
            None
            if s1 is None
            else {
                "aptos": s1.aptos,
                "comparecimento": s1.comparecimento,
                "lula": s1.lula,
                "flavio": s1.flavio,
            }
        ),
        "t2022": (
            None
            if s22 is None
            else {
                "local": s22.local,
                "aptos": s22.aptos,
                "comparecimento": s22.comparecimento,
                "lula_1t": s22.lula_1t,
                "bolsonaro_1t": s22.bolsonaro_1t,
                "lula_2t": s22.lula_2t,
                "bolsonaro_2t": s22.bolsonaro_2t,
            }
        ),
        "politize_bolsonaro22_2t_pct_validos": b22,
        "mistura": grupo,
        "link": f"politizese.html#uf={uf}&zona={zona}&secao={secao}",
    }


def perfil(
    fichas: list[dict[str, Any]], secoes_pais: dict[Chave, Secao]
) -> dict[str, Any]:
    """Onde ficam e de que tamanho são as seções da lista, contra o país (sem ZZ)."""
    aptos = [x["aptos"] for x in fichas]
    pais = [s for ch, s in secoes_pais.items() if ch[0] != "ZZ"]
    aptos_pais = [s.aptos for s in pais]
    p25, p75 = quartis(aptos)
    faixas = []
    for lo, hi in FAIXAS_APTOS:

        def dentro(a: int, lo: int = lo, hi: int | None = hi) -> bool:
            return a >= lo and (hi is None or a <= hi)

        n = sum(1 for a in aptos if dentro(a))
        n_pais = sum(1 for a in aptos_pais if dentro(a))
        faixas.append(
            {
                "de": lo,
                "ate": hi,
                "secoes": n,
                "pct": pct(n, len(aptos), 1),
                "pct_pais": pct(n_pais, len(aptos_pais), 1),
            }
        )
    ufs = Counter(x["uf"] for x in fichas)
    soma_aptos = sum(aptos)
    soma_comp = sum(x["comparecimento"] for x in fichas)
    return {
        "secoes": len(fichas),
        "ufs": [{"uf": uf, "secoes": n} for uf, n in ufs.most_common()],
        "municipios": len({(x["uf"], x["mun"]) for x in fichas}),
        "aptos": {
            "soma": soma_aptos,
            "mediana": mediana(aptos),
            "p25": p25,
            "p75": p75,
            "min": min(aptos) if aptos else None,
            "max": max(aptos) if aptos else None,
            "mediana_pais": mediana(aptos_pais),
            "faixas": faixas,
        },
        "comparecimento": {
            "soma": soma_comp,
            "pct": pct(soma_comp, soma_aptos, 2),
            "pct_pais": pct(
                sum(s.comparecimento for s in pais), sum(s.aptos for s in pais), 2
            ),
        },
    }


def primeiro_turno(fichas: list[dict[str, Any]], lado: str) -> dict[str, Any]:
    """O 1º turno de 2026 nas mesmas seções: o candidato zerado no 2º turno."""
    com = [x for x in fichas if x["t1"] is not None]
    v = [x["t1"]["flavio" if lado == "direita" else "lula"] for x in com]
    adv = [x["t1"]["lula" if lado == "direita" else "flavio"] for x in com]
    return {
        "secoes_com_1t": len(com),
        "votos_soma": sum(v),
        "secoes_zero": sum(1 for a in v if a == 0),
        "secoes_ate_5": sum(1 for a in v if a <= 5),
        "maximo": max(v) if v else None,
        "votos_adversario_soma": sum(adv),
    }


def repeticao_2022(fichas: list[dict[str, Any]], lado: str) -> dict[str, Any]:
    """A mesma chave em 2022 (arquivo por seção) e a fatia pareada do Politize."""
    cand = "bolsonaro" if lado == "direita" else "lula"
    com = [x for x in fichas if x["t2022"] is not None]
    v2 = [x["t2022"][f"{cand}_2t"] for x in com if x["t2022"][f"{cand}_2t"] is not None]
    v1 = [x["t2022"][f"{cand}_1t"] for x in com if x["t2022"][f"{cand}_1t"] is not None]
    sem = Counter(x["tipo"] for x in fichas if x["t2022"] is None)
    out: dict[str, Any] = {
        "chave_presente": len(com),
        "chave_ausente": len(fichas) - len(com),
        "chave_ausente_por_tipo": {k: sem.get(k, 0) for k in ORDEM_TIPOS},
        "zero_2t": sum(1 for a in v2 if a == 0),
        "zero_1t": sum(1 for a in v1 if a == 0),
        "nota": (
            "mesma chave (UF, município, zona, seção) no arquivo de 2022; seções "
            "renumeradas ou criadas depois de 2022 não casam"
        ),
    }
    if lado == "direita":
        pares = [
            float(x["politize_bolsonaro22_2t_pct_validos"])
            for x in fichas
            if x["politize_bolsonaro22_2t_pct_validos"] is not None
        ]
        out["politize"] = {
            "pareadas": len(pares),
            "mediana_pct_validos": mediana(pares),
            "zeros_exatos": sum(1 for a in pares if a == 0),
            "maximo_pct_validos": max(pares) if pares else None,
            "ate_5_pct": sum(1 for a in pares if a <= 5),
            "nota": (
                "fatia de Bolsonaro no 2º turno de 2022, em % dos válidos, pareada pelo "
                "cadastro do Politize (bolsonaro22_2t_v); seção sem par fica nula"
            ),
        }
    return out


def cruzar_mistura(fichas: list[dict[str, Any]], mistura: dict) -> dict[str, Any]:
    if not mistura.get("disponivel"):
        return {"disponivel": False, "motivo": mistura.get("motivo")}
    dentro = [x for x in fichas if x["mistura"] is not None]
    c = Counter(x["mistura"]["id"] for x in dentro)
    return {
        "disponivel": True,
        "no_universo": len(dentro),
        "fora_do_universo": len(fichas) - len(dentro),
        "grupo_atipico": mistura["atipico"],
        "no_grupo_atipico": sum(1 for x in dentro if x["mistura"]["atipico"]),
        "por_grupo": [
            {
                "id": g,
                "secoes": n,
                "rotulo": mistura["rotulos"].get(g),
            }
            for g, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
        "nota": (
            "universo da mistura: seções com BU nos dois turnos e 30 aptos ou mais em "
            "cada; as menores ficam fora"
        ),
    }


def ficha_2022(
    ch: Chave, s: Secao22, muns: dict[tuple[str, str], str], turno: int
) -> dict:
    """Seção de 2022 com os votos do turno pedido e o tipo do local."""
    uf, mun, zona, secao = ch
    municipio = muns.get((uf, mun)) or mun
    return {
        "uf": uf,
        "mun": mun,
        "municipio": municipio,
        "zona": zona,
        "secao": secao,
        "local": s.local,
        "tipo": tipo_local(s.local, uf, municipio),
        "lula": s.lula_2t if turno == 2 else s.lula_1t,
        "bolsonaro": s.bolsonaro_2t if turno == 2 else s.bolsonaro_1t,
        "aptos": s.aptos,
        "comparecimento": s.comparecimento,
    }


# ------------------------------------------------------------------ conferência


def conferir_referencia(
    fichas: list[dict[str, Any]], caminho: Path = REFERENCIA
) -> dict[str, Any]:
    """Compara a lista com o CSV de conferência (sem a coluna tipo, regra antiga)."""
    if not caminho.exists():
        return {"arquivo": rel(caminho), "disponivel": False}
    with caminho.open(encoding="utf-8", newline="") as f:
        ref = {(x["uf"], int(x["zona"]), int(x["secao"])): x for x in csv.DictReader(f)}
    nossas = {(x["uf"], x["zona"], x["secao"]): x for x in fichas}
    divergencias = []
    for ch in sorted(set(ref) & set(nossas)):
        r, x = ref[ch], nossas[ch]
        b22 = x["politize_bolsonaro22_2t_pct_validos"]
        pares = {
            "municipio": (r["municipio"], x["municipio"]),
            "local": (r["local"], x["local"] or ""),
            "aptos": (int(r["aptos"]), x["aptos"]),
            "comparecimento": (int(r["comparecimento"]), x["comparecimento"]),
            "lula_2t": (int(r["lula_2t"]), x["lula"]),
            "flavio_1t": (int(r["flavio_1t"]), x["t1"]["flavio"] if x["t1"] else None),
            "lula_1t": (int(r["lula_1t"]), x["t1"]["lula"] if x["t1"] else None),
            "bolsonaro22_2t_pct_validos": (
                (
                    float(r["bolsonaro22_2t_pct_validos"])
                    if r["bolsonaro22_2t_pct_validos"]
                    else None
                ),
                None if b22 is None else float(b22),
            ),
        }
        for campo, (a, b) in pares.items():
            if a != b:
                divergencias.append(
                    {"chave": list(ch), "campo": campo, "csv": a, "script": b}
                )
    return {
        "arquivo": rel(caminho),
        "sha256": sha256(caminho),
        "disponivel": True,
        "linhas": len(ref),
        "so_no_csv": [list(c) for c in sorted(set(ref) - set(nossas))],
        "so_no_script": [list(c) for c in sorted(set(nossas) - set(ref))],
        "divergencias": divergencias,
        "nota": (
            "a coluna tipo do CSV usa uma regra anterior e mais curta; não é comparada"
        ),
    }


def _recorte(d: dict, ano: int, turno: int, lado: str) -> dict:
    for r in d["recortes"]:
        if (r["ano"], r["turno"], r["lado"]) == (ano, turno, lado):
            return r
    raise KeyError(f"recorte {ano} {turno} {lado}")


def obtido(d: dict[str, Any]) -> dict[str, Any]:
    """Os mesmos campos de ``ESPERADO``, lidos do resultado."""
    p = d["zero_flavio"]["perfil"]
    t1 = d["zero_flavio"]["primeiro_turno"]
    rp = d["zero_flavio"]["repeticao_2022"]
    out: dict[str, Any] = {}
    for ano in (2026, 2022):
        for turno in (2, 1):
            for lado in ("direita", "lula"):
                r = _recorte(d, ano, turno, lado)
                chave = f"{ano}_{turno}t_{lado}"
                if chave in ESPERADO and isinstance(ESPERADO[chave], tuple):
                    out[chave] = (r["secoes"], r["votos_adversario"])
                else:
                    out[chave] = r["secoes"]
    ce = d["com_exterior"]
    out["2026_2t_direita_com_exterior"] = ce["2026_2t_direita"]
    out["2026_2t_lula_com_exterior"] = ce["2026_2t_lula"]
    ufs = {x["uf"]: x["secoes"] for x in p["ufs"]}
    out["ufs_2026_2t"] = {uf: ufs.get(uf) for uf in ESPERADO["ufs_2026_2t"]}
    out["municipios"] = p["municipios"]
    out["aptos_mediana"] = p["aptos"]["mediana"]
    out["aptos_soma"] = p["aptos"]["soma"]
    out["comparecimento_soma"] = p["comparecimento"]["soma"]
    out["flavio_1t_soma"] = t1["votos_soma"]
    out["flavio_1t_zero"] = t1["secoes_zero"]
    out["flavio_1t_ate_5"] = t1["secoes_ate_5"]
    out["repete_2022_zero_bolsonaro"] = rp["zero_2t"]
    out["politize_2022_pareadas"] = rp["politize"]["pareadas"]
    out["politize_2022_mediana"] = rp["politize"]["mediana_pct_validos"]
    out["politize_2022_zeros"] = rp["politize"]["zeros_exatos"]
    return out


def conferir(d: dict[str, Any]) -> None:
    """Levanta ``AssertionError`` com todas as divergências contra ``ESPERADO``."""
    ob = obtido(d)
    falhas = [
        f"{k}: esperado {v!r}, obtido {ob.get(k)!r}"
        for k, v in ESPERADO.items()
        if ob.get(k) != v
    ]
    ref = d.get("conferencia_csv") or {}
    if ref.get("disponivel"):
        for campo in ("so_no_csv", "so_no_script", "divergencias"):
            if ref[campo]:
                falhas.append(f"conferencia_csv.{campo}: {ref[campo][:5]}")
    assert not falhas, "zeros.json diverge do conferido:\n" + "\n".join(falhas)


# ------------------------------------------------------------------ montagem


def montar() -> dict[str, Any]:
    secoes2 = ler_banco(BANCO_2T, com_modelo=True)
    secoes1 = ler_banco(BANCO_1T, com_modelo=False)
    s22 = ler_2022()
    muns = nomes_municipios()
    pol = Politize()
    mistura = ler_mistura()

    votos = {
        (2026, 2): votos_2026(secoes2),
        (2026, 1): votos_2026(secoes1),
        (2022, 2): votos_2022(s22, 2),
        (2022, 1): votos_2022(s22, 1),
    }
    recortes, exterior = [], []
    for (ano, turno), v in votos.items():
        for lado in ("direita", "lula"):
            recortes.append(recorte(v, ano, turno, lado, exterior=False))
            exterior.append(recorte(v, ano, turno, lado, exterior=True))
    ex_2t = {ch: s for ch, s in secoes2.items() if ch[0] == "ZZ"}
    sem_comp = {ch for ch, s in ex_2t.items() if s.comparecimento == 0}
    ex_votos = {ch: x for ch, x in votos[(2026, 2)].items() if ch[0] == "ZZ"}
    ex_zero = {lado: set(zeros(ex_votos, lado)) for lado in ("direita", "lula")}

    def com_ex(lado: str) -> int:
        return len(zeros(votos[(2026, 2)], lado))

    listas: dict[str, list[dict[str, Any]]] = {}
    for nome, (ano, turno, lado) in {
        "zero_flavio_2t": (2026, 2, "direita"),
        "zero_lula_2t": (2026, 2, "lula"),
        "zero_flavio_1t": (2026, 1, "direita"),
    }.items():
        brasil = {ch: x for ch, x in votos[(ano, turno)].items() if ch[0] != "ZZ"}
        fonte = secoes2 if turno == 2 else secoes1
        outra = secoes1 if turno == 2 else secoes2
        listas[nome] = []
        for ch in zeros(brasil, lado):
            f = ficha_2026(
                ch,
                fonte[ch],
                outra.get(ch),
                s22.get(ch),
                pol.secao(ch),
                muns,
                mistura,
            )
            if turno == 1:
                # Na lista do 1º turno, "t1" guarda o 2º turno da mesma seção.
                f["t2"] = f.pop("t1")
            listas[nome].append(f)
    lista_22 = {}
    for turno in (2, 1):
        brasil = {ch: x for ch, x in votos[(2022, turno)].items() if ch[0] != "ZZ"}
        lista_22[turno] = [
            ficha_2022(ch, s22[ch], muns, turno) for ch in zeros(brasil, "direita")
        ]
    zf = listas["zero_flavio_2t"]
    zl = listas["zero_lula_2t"]

    fontes = {
        rel(BANCO_2T): sha256(BANCO_2T),
        rel(BANCO_1T): sha256(BANCO_1T),
        rel(CSV_2022): sha256(CSV_2022),
        rel(INDICE): sha256(INDICE),
    }
    coluna = ROOT / MANCHETE["arquivo"]
    if coluna.exists():
        fontes[rel(coluna)] = sha256(coluna)
    if ANOMALIA.exists():
        fontes[rel(ANOMALIA)] = sha256(ANOMALIA)
    if mistura.get("disponivel"):
        fontes[rel(mistura["arquivo"])] = mistura["sha256"]
    sem_local = [x for x in [*zf, *zl] if x["local"] is None]

    d: dict[str, Any] = {
        "gerado_em": agora_utc(),
        "script": SCRIPT,
        "rotulo": ROTULO,
        "manchete": MANCHETE,
        "definicao": DEFINICAO,
        "regra_tipo_local": {
            "ordem": [
                {"tipo": k, "nome": nome, "termos": termos} for k, nome, termos in TIPOS
            ]
            + [{"tipo": OUTRO[0], "nome": OUTRO[1], "termos": []}],
            "municipios_comunidade": [
                {"uf": uf, "nome": nome}
                for uf, nome in sorted(MUNICIPIOS_COMUNIDADE, key=lambda x: x[1])
            ],
            "normalizacao": (
                "maiúsculas, sem acento, espaços simples, apóstrofo colado às letras; "
                "termo com apóstrofo casa também com o nome sem espaços"
            ),
            "nota": (
                "classificação pelo nome do prédio no cadastro do Politize (2026) ou no "
                "arquivo de 2022; nome que não diz o tipo fica como outro local"
            ),
        },
        "recortes": recortes,
        "exterior": {
            "recortes": exterior,
            "sem_comparecimento_2t_2026": len(sem_comp),
            "zero_flavio_2t_sem_comparecimento": len(ex_zero["direita"] & sem_comp),
            "zero_lula_2t_sem_comparecimento": len(ex_zero["lula"] & sem_comp),
            "nota": (
                "no exterior, as seções sem nenhum comparecimento contam como zero para os "
                "dois finalistas; ficam fora do número principal"
            ),
        },
        "com_exterior": {
            "2026_2t_direita": com_ex("direita"),
            "2026_2t_lula": com_ex("lula"),
        },
        "por_uf": por_uf(votos),
        "por_regiao": por_regiao(votos),
        "tipo_local": {
            "2026_2t_direita": contar_tipos(zf, "lula"),
            "2026_2t_lula": contar_tipos(zl, "flavio"),
            "2026_1t_direita": contar_tipos(listas["zero_flavio_1t"], "lula"),
            "2022_2t_direita": contar_tipos(lista_22[2], "lula"),
            "2022_1t_direita": contar_tipos(lista_22[1], "lula"),
        },
        "zero_flavio": {
            "perfil": perfil(zf, secoes2),
            "primeiro_turno": primeiro_turno(zf, "direita"),
            "repeticao_2022": repeticao_2022(zf, "direita"),
            "mistura": cruzar_mistura(zf, mistura),
            "sem_nome_de_local": len([x for x in zf if x["local"] is None]),
            "comunidade_pela_regra_do_municipio": sum(
                1 for x in zf if x["tipo_regra"] == "municipio"
            ),
        },
        "zero_lula": {
            "perfil": perfil(zl, secoes2),
            "primeiro_turno": primeiro_turno(zl, "lula"),
            "repeticao_2022": repeticao_2022(zl, "lula"),
            "mistura": cruzar_mistura(zl, mistura),
        },
        "lista_zero_flavio": zf,
        "lista_zero_lula": zl,
        "lista_zero_bolsonaro_2022_2t": lista_22[2],
        "conferencia_csv": conferir_referencia(zf),
        "secoes_sem_local_no_politize": len(sem_local),
        "fontes": fontes,
        "fontes_politize_zonas": dict(sorted(pol.lidos.items())),
    }
    return d


def gravar(d: dict[str, Any], caminho: Path = SAIDA) -> None:
    caminho.write_text(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )


__all__ = [
    "ESPERADO",
    "MANCHETE",
    "NOME_TIPO",
    "ORDEM_TIPOS",
    "ROOT",
    "ROTULO",
    "SAIDA",
    "TIPOS",
    "conferir",
    "gravar",
    "montar",
    "obtido",
    "tipo_local",
]
