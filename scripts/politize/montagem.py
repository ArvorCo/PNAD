"""Junção das fontes por local de votação e cálculo das métricas do contrato.

Um local é ``(UF, município TSE, zona, número do local)``. Entram as seções principais
com boletim de urna (cargo 1); seção agregada já vem somada na principal e vota no
local da principal. Duas passagens: a primeira junta contagens, 2022, perfil, setor e
renda e calcula o voto esperado bruto; a segunda, depois da recentragem por UF,
calcula vão, componentes, índice, arquétipo e conta do 2º turno.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from . import arquetipos, fontes
from . import metricas as mt
from .pnad import ESCOLARIDADES, TabelaRenda

COLUNAS_LOCAL = (
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
    "cury",
    "renan",
    "caiado",
    "zema",
    "outros_nominais",
    "coord_fonte",
    "percentil",
    "percentil_uf",
)
APTOS_MIN_SECAO = 30
SECAO_SEMPRE = {
    "secao",
    "local_id",
    "mun_tse",
    "local",
    "bairro",
    "aptos",
    "agregadas",
    "coord_fonte",
}
INTEIROS = {
    "local_nr",
    "zona",
    "secoes",
    "aptos",
    "comparecimento",
    "flavio",
    "lula",
    "terceira",
    "brancos",
    "nulos",
    "indice",
    "flavio_2t",
    "lula_2t",
    "faltam",
    "conversas_para_virar",
    "conversas_para_segurar",
    "percentil",
    "percentil_uf",
    "em_aberto",
    "bna",
    "cury",
    "renan",
    "caiado",
    "zema",
    "outros_nominais",
}
UMA_CASA = {
    "flavio_v",
    "lula_v",
    "terceira_v",
    "bn_v",
    "flavio_a",
    "lula_a",
    "terceira_a",
    "bn_a",
    "abst_a",
    "margem_v",
    "bolsonaro22_1t_v",
    "lula22_1t_v",
    "bolsonaro22_2t_v",
    "lula22_2t_v",
    "abst22_2t_a",
    "reencontro_a",
    "fem",
    "masc",
    "a16_24",
    "a25_34",
    "a35_44",
    "a45_59",
    "a60",
    "fund_inc",
    "fund_med",
    "med_sup_inc",
    "superior",
    "renda_ate2",
    "renda_de2a5",
    "renda_mais5",
    "esperado_flavio_v",
    "esperado_lula_v",
    "vao_perfil_pp",
    "c_terceira",
    "c_ausentes",
    "c_reencontro",
    "c_perfil",
    "potencial",
}
PERFIL_SHARES = (
    "fem",
    "masc",
    "a16_24",
    "a25_34",
    "a35_44",
    "a45_59",
    "a60",
    "fund_inc",
    "fund_med",
    "med_sup_inc",
    "superior",
)


COLUNAS_SECAO = (
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
    "em_aberto",
    "bna",
    "viravel",
    "cury",
    "renan",
    "caiado",
    "zema",
    "outros_nominais",
    "coord_fonte",
    "percentil",
    "percentil_uf",
)


def _contadores() -> dict[str, float]:
    return dict.fromkeys(mt.CONTADORES + mt.CONTADORES_2022, 0)


@dataclass
class Local:
    cad: fontes.LocalCadastro
    c: dict[str, float] = field(default_factory=_contadores)
    perfil: list[float] | None = None
    perfil_fonte: str | None = None
    setor: list | None = None
    renda: dict[str, Any] | None = None
    esperado: tuple[float, float] | None = None
    m: dict[str, Any] = field(default_factory=dict)
    secoes: list[Secao] = field(default_factory=list)

    @property
    def id(self) -> str:
        return self.cad.id


@dataclass
class Secao:
    """Seção principal com boletim (a urna); as agregadas já estão somadas nela."""

    chave: fontes.SecaoKey
    local: Local
    agregadas: list[int]
    c: dict[str, float] = field(default_factory=_contadores)
    perfil: list[float] | None = None
    perfil_fonte: str | None = None
    renda: dict[str, Any] | None = None
    esperado: tuple[float, float] | None = None
    m: dict[str, Any] = field(default_factory=dict)

    @property
    def setor(self) -> list | None:
        return self.local.setor


@dataclass
class ResultadoUF:
    uf: str
    locais: list[Local]
    meta: dict[str, Any]

    def secoes(self) -> list[Secao]:
        return [s for loc in self.locais for s in loc.secoes]


def montar_uf(
    uf: str,
    numeros: set[int],
    s22: Mapping[fontes.SecaoKey, list[int | None]],
    tabela: TabelaRenda | None,
    voto_faixa: list[dict[str, float]],
    com_setor: bool,
) -> ResultadoUF:
    """Primeira passagem: contagens, 2022, perfil, setor, renda e esperado bruto."""
    votos, meta_votos = fontes.votos_uf(uf, numeros)
    secao_local, cadastro, principal_de = fontes.cadastro_uf(uf)
    agregadas: dict[fontes.SecaoKey, list[int]] = defaultdict(list)
    for s, p in principal_de.items():
        if s != p:
            agregadas[p].append(s[2])
    locais: dict[fontes.LocalKey, Local] = {}
    secoes: dict[fontes.SecaoKey, Secao] = {}
    fora_cadastro = 0
    for chave_s, v in votos.items():
        chave_l = secao_local.get(chave_s)
        if chave_l is None or chave_l not in cadastro:
            fora_cadastro += 1
            continue
        loc = locais.get(chave_l)
        if loc is None:
            loc = locais[chave_l] = Local(cad=cadastro[chave_l])
        sec = Secao(
            chave=chave_s, local=loc, agregadas=sorted(agregadas.get(chave_s, []))
        )
        secoes[chave_s] = sec
        loc.secoes.append(sec)
        for c in (loc.c, sec.c):
            _somar_secao(c, v, s22.get(chave_s), chave_l[2])
    meta = {
        "votos": meta_votos,
        "secoes_fora_do_cadastro": fora_cadastro,
        **_perfil(uf, locais, secoes, secao_local, principal_de),
    }
    if com_setor and uf != "ZZ":
        pontos = {
            loc.id: (loc.cad.lat, loc.cad.lon)
            for loc in locais.values()
            if loc.cad.lat is not None
        }
        setores = fontes.setores_uf(uf, pontos)
        for loc in locais.values():
            loc.setor = setores.get(loc.id)
    for loc in locais.values():
        sit = fontes.situacao_setor(loc.setor[1]) if loc.setor else None
        for unidade in (loc, *loc.secoes):
            unidade.m = {**mt.metricas_votos(unidade.c), **mt.metricas_2022(unidade.c)}
            if tabela is None or uf == "ZZ" or unidade.perfil is None:
                continue
            pesos = parcelas_escolaridade(unidade.perfil)
            if not pesos:
                continue
            unidade.renda = tabela.misturar(uf, sit, pesos, com_mediana=unidade is loc)
            unidade.esperado = mt.esperado_bruto(unidade.renda, voto_faixa)
    ordenados = sorted(
        locais.values(), key=lambda x: (x.cad.mun_tse, x.cad.zona, x.cad.local_nr)
    )
    for loc in ordenados:
        loc.secoes.sort(key=lambda s: s.chave)
    return ResultadoUF(uf=uf, locais=ordenados, meta=meta)


def _somar_secao(c: dict, v: list[int], s: list[int | None] | None, local_nr: int):
    c["secoes"] += 1
    c["aptos"] += v[fontes.V_APTOS]
    c["comparecimento"] += v[fontes.V_COMP]
    c["flavio"] += v[fontes.V_FLAVIO]
    c["lula"] += v[fontes.V_LULA]
    c["terceira"] += v[fontes.V_TERCEIRA]
    c["brancos"] += v[fontes.V_BRANCOS]
    c["nulos"] += v[fontes.V_NULOS]
    nomeadas = 0
    for nome, i in (
        ("cury", fontes.V_CURY),
        ("renan", fontes.V_RENAN),
        ("caiado", fontes.V_CAIADO),
        ("zema", fontes.V_ZEMA),
    ):
        c[nome] += v[i]
        nomeadas += v[i]
    c["outros_nominais"] += v[fontes.V_TERCEIRA] - nomeadas
    if s is None or s[0] != local_nr or not s[7] or not s[3]:
        return
    c["aptos_casado"] += v[fontes.V_APTOS]
    c["flavio_casado"] += v[fontes.V_FLAVIO]
    c["aptos22"] += s[7]
    c["b22_1t"] += s[2] or 0
    c["l22_1t"] += s[1] or 0
    c["nom22_1t"] += s[3] or 0
    c["b22_2t"] += s[5] or 0
    c["l22_2t"] += s[4] or 0
    c["nom22_2t"] += s[6] or 0
    if s[9] is not None and s[10] is not None:
        c["aptos22_2t"] += s[9]
        c["comp22_2t"] += s[10]


def parcelas_escolaridade(vetor: list[float]) -> dict[str, float]:
    i = {c: k for k, c in enumerate(fontes.PERFIL_COLS)}
    total = sum(vetor[i[e]] for e in ESCOLARIDADES)
    if total <= 0:
        return {}
    return {e: vetor[i[e]] / total for e in ESCOLARIDADES}


def _acrescentar(unidade: Local | Secao, vetor: list[float], fonte: str) -> None:
    if unidade.perfil is None:
        unidade.perfil = [0.0] * len(vetor)
        unidade.perfil_fonte = fonte
    unidade.perfil = [a + b for a, b in zip(unidade.perfil, vetor, strict=True)]


def _perfil(
    uf: str,
    locais: dict[fontes.LocalKey, Local],
    secoes: dict[fontes.SecaoKey, Secao],
    secao_local: Mapping[fontes.SecaoKey, fontes.LocalKey],
    principal_de: Mapping[fontes.SecaoKey, fontes.SecaoKey],
) -> dict[str, Any]:
    """Perfil por seção quando o arquivo da UF existe e é íntegro; senão, por zona.

    O perfil de uma seção agregada vai para a principal (mesma urna) e para o local
    da principal. Seção do perfil ausente do cadastro de outubro vai para o local
    que o próprio perfil declara, se ele estiver no universo.
    """
    por_secao, motivo = fontes.perfil_secao_uf(uf)
    eleitores_perfil = eleitores_casados = 0
    if por_secao is not None:
        for chave, vetor in por_secao.items():
            mun, zona, secao, nr = chave.split("|")
            chave_s = (mun, int(zona), int(secao))
            eleitores_perfil += vetor[-1]
            loc = locais.get(secao_local.get(chave_s, (mun, int(zona), int(nr))))
            if loc is None:
                continue
            eleitores_casados += vetor[-1]
            _acrescentar(loc, vetor, "secao")
            sec = secoes.get(principal_de.get(chave_s, chave_s))
            if sec is not None:
                _acrescentar(sec, vetor, "secao")
    unidades = [*locais.values(), *secoes.values()]
    sem_perfil = [u for u in unidades if u.perfil is None]
    if sem_perfil:
        por_zona = fontes.perfil_zona_uf(uf)
        for u in sem_perfil:
            mun, zona = (
                (u.cad.mun_tse, u.cad.zona) if isinstance(u, Local) else u.chave[:2]
            )
            vetor = por_zona.get(f"{mun}|{zona}")
            if vetor is None or not vetor[-1]:
                continue
            # Pseudo-contagem: shares da zona aplicados aos aptos da unidade.
            escala = u.c["aptos"] / vetor[-1]
            u.perfil = [x * escala for x in vetor]
            u.perfil_fonte = "zona"
    contar = {"secao": 0, "zona": 0, None: 0}
    contar_s = {"secao": 0, "zona": 0, None: 0}
    for loc in locais.values():
        contar[loc.perfil_fonte] += 1
    for sec in secoes.values():
        contar_s[sec.perfil_fonte] += 1
    return {
        "perfil_secao": motivo,
        "perfil_eleitores_arquivo": eleitores_perfil,
        "perfil_eleitores_casados": eleitores_casados,
        "locais_perfil_secao": contar["secao"],
        "locais_perfil_zona": contar["zona"],
        "locais_sem_perfil": contar[None],
        "secoes_perfil_secao": contar_s["secao"],
        "secoes_perfil_zona": contar_s["zona"],
        "secoes_sem_perfil": contar_s[None],
    }


# ------------------------------------------------------------ segunda passagem


def finalizar(
    loc: Local | Secao, desloc: tuple[float, float] | None, abst_ref: float | None
) -> None:
    """Esperado recentrado, vão, componentes, índice, arquétipo e conta do 2º turno.

    Vale para o local e para a seção, com as mesmas funções. ``abst_ref`` é a abstenção
    do 2º turno de 2022 do município, usada quando a unidade não tem seção casada.
    """
    m = loc.m
    if loc.perfil is not None:
        m.update(mt.parcelas_perfil(loc.perfil, fontes.PERFIL_COLS))
    if loc.setor:
        m["setor_situacao"] = fontes.situacao_setor(loc.setor[1])
        m["setor_tipo"] = fontes.tipo_setor(loc.setor[2])
    if loc.renda is not None:
        m["renda_ate2"] = loc.renda["ate2"]
        m["renda_de2a5"] = loc.renda["de2a5"]
        m["renda_mais5"] = loc.renda["mais5"]
        m["renda_mediana_brl"] = loc.renda["mediana_brl"]
    vao = None
    if loc.esperado is not None and desloc is not None and m["flavio_v"] is not None:
        m["esperado_flavio_v"] = loc.esperado[0] + desloc[0]
        m["esperado_lula_v"] = loc.esperado[1] + desloc[1]
        vao = m["esperado_flavio_v"] - m["flavio_v"]
        m["vao_perfil_pp"] = vao
    m["aptos"] = loc.c["aptos"]
    m.update(mt.componentes(m, vao))
    m["indice"] = mt.indice(m["potencial"])
    abst = m.get("abst22_2t_a")
    m.update(
        mt.conta_2t(
            loc.c["flavio"],
            loc.c["lula"],
            loc.c["terceira"],
            abst if abst is not None else abst_ref,
        )
    )
    m["em_aberto"] = mt.em_aberto(loc.c)
    m["bna"] = mt.bna(loc.c)
    m["viravel"] = mt.viravel(loc.c["flavio"], loc.c["lula"], m["bna"])
    m["arquetipo"], m["arquetipo_secundario"] = arquetipos.classificar(publicaveis(m))


def publicaveis(m: Mapping[str, Any]) -> dict[str, Any]:
    """Valores como saem no JSON (uma casa nos percentuais)."""
    saida = {}
    for k, v in m.items():
        if k in UMA_CASA:
            saida[k] = mt.r1(v)
        elif k == "renda_mediana_brl":
            saida[k] = None if v is None else int(round(v / 10.0) * 10)
        elif k == "cobertura_2022":
            saida[k] = None if v is None else round(v / 100.0, 3)
        elif k in INTEIROS and isinstance(v, (int, float)):
            saida[k] = round(v)
        else:
            saida[k] = v
    return saida


def linha(loc: Local) -> list[Any]:
    cad = loc.cad
    valores = publicaveis({**loc.c, **loc.m})
    valores.update(
        {
            "local_id": cad.id,
            "local_nr": cad.local_nr,
            "zona": cad.zona,
            "nome": cad.nome,
            "endereco": cad.endereco,
            "bairro": cad.bairro,
            "cep": cad.cep,
            "lat": None if cad.lat is None else round(cad.lat, 5),
            "lon": None if cad.lon is None else round(cad.lon, 5),
            "tipo_local": cad.tipo_local,
            "coord_fonte": cad.coord_fonte,
        }
    )
    return [valores.get(c) for c in COLUNAS_LOCAL]


def linha_secao(sec: Secao) -> list[Any]:
    loc = sec.local
    valores = publicaveis({**sec.c, **sec.m})
    valores.update(
        {
            "secao": sec.chave[2],
            "local_id": loc.id,
            "mun_tse": sec.chave[0],
            "local": loc.cad.nome,
            "bairro": loc.cad.bairro,
            "perfil_fonte": sec.perfil_fonte,
            "agregadas": list(sec.agregadas),
            "coord_fonte": loc.cad.coord_fonte,
        }
    )
    if sec.c["aptos"] < APTOS_MIN_SECAO:
        # Grupo pequeno demais para leitura própria: só identificação e aptos.
        return [valores.get(c) if c in SECAO_SEMPRE else None for c in COLUNAS_SECAO]
    return [valores.get(c) for c in COLUNAS_SECAO]


# ------------------------------------------------------------------- totais


def totais(locais: Iterable[Local], tabela: TabelaRenda | None) -> dict[str, Any]:
    """Totais de um conjunto de locais (município, UF, país).

    Contagens somadas e taxas recalculadas sobre a soma. Componentes do potencial são
    a soma dos votos endereçáveis de cada local por 100 aptos do conjunto (saldo
    positivo de um local não se cancela com o negativo de outro); ``reencontro_a`` e
    ``vao_perfil_pp`` seguem a mesma regra, ponderados por aptos e por válidos.
    """
    locais = list(locais)
    c = mt.somar((x.c for x in locais), mt.CONTADORES + mt.CONTADORES_2022)
    m: dict[str, Any] = {**mt.metricas_votos(c), **mt.metricas_2022(c)}
    aptos = c["aptos"]
    m["reencontro_a"] = mt.media_ponderada(
        (x.m.get("reencontro_a"), x.c["aptos"]) for x in locais
    )
    vetor = None
    for x in locais:
        if x.perfil is None:
            continue
        vetor = (
            list(x.perfil)
            if vetor is None
            else [a + b for a, b in zip(vetor, x.perfil, strict=True)]
        )
    if vetor is not None:
        m.update(mt.parcelas_perfil(vetor, fontes.PERFIL_COLS))
    if tabela is not None:
        pesos: dict[tuple[str, str, str], float] = defaultdict(float)
        for x in locais:
            if x.renda is None or x.perfil is None:
                continue
            sit = x.m.get("setor_situacao") or "total"
            for esc, w in parcelas_escolaridade(x.perfil).items():
                pesos[(x.cad.uf, sit, esc)] += w * x.c["aptos"]
        renda = tabela.misturar_celulas(dict(pesos)) if pesos else None
        if renda is not None:
            m["renda_ate2"] = renda["ate2"]
            m["renda_de2a5"] = renda["de2a5"]
            m["renda_mais5"] = renda["mais5"]
            m["renda_mediana_brl"] = renda["mediana_brl"]
    for chave in ("esperado_flavio_v", "esperado_lula_v", "vao_perfil_pp"):
        m[chave] = mt.media_ponderada((x.m.get(chave), m_validos(x)) for x in locais)
    for chave in ("c_terceira", "c_ausentes", "c_reencontro", "c_perfil"):
        soma = sum((x.m.get(chave) or 0.0) * x.c["aptos"] for x in locais)
        m[chave] = soma / aptos if aptos else None
    if m["c_terceira"] is not None:
        m["potencial"] = sum(
            m[k] or 0.0
            for k in ("c_terceira", "c_ausentes", "c_reencontro", "c_perfil")
        )
    else:
        m["potencial"] = None
    m["indice"] = mt.indice(m["potencial"])
    m.update(mt.conta_2t(c["flavio"], c["lula"], c["terceira"], m.get("abst22_2t_a")))
    m["n_locais"] = len(locais)
    m["arquetipo"], m["arquetipo_secundario"] = arquetipos.classificar(publicaveis(m))
    m.update(abertos(locais, c))
    saida = publicaveis({**c, **m})
    for k in ("aptos_casado", "flavio_casado", "bolsonaro22_1t_a", "abstencao"):
        saida.pop(k, None)
    for k in mt.CONTADORES_2022:
        saida.pop(k, None)
    saida["validos"] = round(m["validos"])
    return saida


def abertos(locais: list[Local], c: Mapping[str, float]) -> dict[str, Any]:
    """Votos em aberto somados e locais que os votos em aberto já dariam para virar."""
    vf = [x for x in locais if x.m.get("viravel") == "flavio"]
    vl = [x for x in locais if x.m.get("viravel") == "lula"]
    partes = {
        "terceira": round(c["terceira"]),
        "brancos": round(c["brancos"]),
        "nulos": round(c["nulos"]),
        "abstencao": round(c["aptos"] - c["comparecimento"]),
    }
    return {
        "votos_em_aberto": sum(partes.values()),
        "em_aberto": partes,
        "em_aberto_por_origem": {
            "abstencao": partes["abstencao"],
            **{k: round(c[k]) for k in ("caiado", "renan", "cury", "zema")},
            "outros_nominais": round(c["outros_nominais"]),
            "nulos": partes["nulos"],
            "brancos": partes["brancos"],
        },
        "locais_viraveis_flavio": len(vf),
        "aptos_locais_viraveis_flavio": round(sum(x.c["aptos"] for x in vf)),
        "locais_viraveis_lula": len(vl),
        "aptos_locais_viraveis_lula": round(sum(x.c["aptos"] for x in vl)),
        "locais_com_boletim": len(locais),
        "secoes_com_boletim": round(c["secoes"]),
    }


def m_validos(x: Local | Secao) -> float:
    return x.c["flavio"] + x.c["lula"] + x.c["terceira"]


def percentis_potencial(resultados: Iterable[ResultadoUF]) -> None:
    """Posição do potencial (0 a 100) no país e na UF, para locais e seções.

    Locais: referência = locais do Brasil com boletim e potencial. Seções: só as com
    30 aptos ou mais. O exterior recebe só ``percentil_uf`` (entre os locais do
    exterior), porque o potencial dele não tem o componente de renda.
    """
    resultados = list(resultados)

    def ref(itens):
        return sorted(
            x.m["potencial"] for x in itens if x.m.get("potencial") is not None
        )

    def secoes(res: ResultadoUF) -> list[Secao]:
        return [s for s in res.secoes() if s.c["aptos"] >= APTOS_MIN_SECAO]

    brasil = [r for r in resultados if r.uf != "ZZ"]
    ref_locais = ref(x for r in brasil for x in r.locais)
    ref_secoes = ref(s for r in brasil for s in secoes(r))
    for res in resultados:
        uf_locais = ref(res.locais)
        uf_secoes = ref(secoes(res))
        for loc in res.locais:
            pot = loc.m.get("potencial")
            loc.m["percentil"] = (
                None if res.uf == "ZZ" else mt.posicao_percentil(pot, ref_locais)
            )
            loc.m["percentil_uf"] = mt.posicao_percentil(pot, uf_locais)
            for sec in loc.secoes:
                if sec.c["aptos"] < APTOS_MIN_SECAO:
                    sec.m["percentil"] = sec.m["percentil_uf"] = None
                    continue
                pot = sec.m.get("potencial")
                sec.m["percentil"] = (
                    None if res.uf == "ZZ" else mt.posicao_percentil(pot, ref_secoes)
                )
                sec.m["percentil_uf"] = mt.posicao_percentil(pot, uf_secoes)


# ----------------------------------------------------------------- recentragem


def recentragem_por_uf(resultados: Iterable[ResultadoUF]) -> dict[str, Any]:
    """Deslocamento aditivo por UF: o esperado médio de cada UF iguala a urna da UF.

    Para cada UF, sobre os locais com renda estimada (o exterior não tem PNAD):
    esperado = bruto + (urna da UF − média do bruto na UF), médias ponderadas por
    válidos. O vão passa a medir quanto o local rende abaixo do que o perfil de renda
    sugere dentro do próprio estado, sem carregar a diferença entre regiões. Como cada
    UF fecha com a própria urna, a média nacional também fecha com a urna do Brasil.
    """
    por_uf: dict[str, dict[str, float]] = {}
    for res in resultados:
        pares_f, pares_l = [], []
        f = lu = v = 0.0
        for loc in res.locais:
            w = m_validos(loc)
            if loc.esperado is None or not w:
                continue
            pares_f.append((loc.esperado[0], w))
            pares_l.append((loc.esperado[1], w))
            f += loc.c["flavio"]
            lu += loc.c["lula"]
            v += w
        if not v:
            continue
        urna = (100.0 * f / v, 100.0 * lu / v)
        media_f, desl_f = mt.deslocamento(pares_f, urna[0])
        media_l, desl_l = mt.deslocamento(pares_l, urna[1])
        por_uf[res.uf] = {
            "validos": round(v),
            "esperado_bruto_flavio": media_f,
            "esperado_bruto_lula": media_l,
            "urna_flavio": urna[0],
            "urna_lula": urna[1],
            "deslocamento_flavio_pp": desl_f,
            "deslocamento_lula_pp": desl_l,
        }
    return {
        "metodo": (
            "deslocamento aditivo por UF: esperado = bruto + (urna da UF − média do "
            "bruto na UF), médias ponderadas por válidos sobre os locais com renda "
            "estimada; o exterior não tem PNAD e fica sem esperado"
        ),
        "por_uf": por_uf,
    }
