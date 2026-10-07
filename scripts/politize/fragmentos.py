"""Escrita dos JSON do app em ``docs/assets/politize/dados/`` (contrato, seção 5).

Listas de locais e municípios saem compactadas como ``{"colunas", "linhas"}``. JSON
sem espaços, UTF-8 sem escape. Nenhum arquivo é editado à mão: tudo sai daqui.
"""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from . import fontes
from . import metricas as mt
from .montagem import (
    COLUNAS_LOCAL,
    COLUNAS_SECAO,
    Local,
    ResultadoUF,
    linha,
    linha_secao,
    totais,
)
from .pnad import TabelaRenda

COLUNAS_MUNICIPIO = (
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
    "coord_fonte",
    "pais",
    "nome_tse",
)
APTOS_RANKING = 300
APTOS_DISPUTA = 5_000
N_DISPUTA = 10
N_RANKING = 20


def gravar_json(caminho: Path, dados: Any) -> int:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    caminho.write_text(texto + "\n", encoding="utf-8")
    return len(texto.encode("utf-8")) + 1


def nome_municipio(
    mun: fontes.Municipio | None, nomes_ibge: Mapping[str, list[str]], bruto: str
) -> str:
    """Nome em caixa normal: o do IBGE; o do distrito-sede quando só ele bate com o
    TSE (caso ``Unas``/``Una``); sem código IBGE, o do TSE em caixa normal."""
    tse = mun.nome_tse if mun else bruto
    if mun is not None and mun.ibge and mun.ibge in nomes_ibge:
        nome, sede = nomes_ibge[mun.ibge]
        alvo = fontes.normalizar_nome(tse)
        if (
            fontes.normalizar_nome(nome) != alvo
            and fontes.normalizar_nome(sede) == alvo
        ):
            return sede
        return nome
    return fontes.caixa_normal(tse)


def nome_alternativo(mun: fontes.Municipio | None, nome: str) -> str | None:
    """Nome do TSE em caixa normal quando difere do exibido (para a busca do app)."""
    if mun is None or not mun.nome_tse:
        return None
    if fontes.normalizar_nome(mun.nome_tse) == fontes.normalizar_nome(nome):
        return None
    return fontes.caixa_normal(mun.nome_tse)


def centro(locais: Iterable[Local]) -> tuple[float | None, float | None]:
    """Centro do eleitorado: média das coordenadas dos locais ponderada por aptos."""
    sx = sy = w = 0.0
    for x in locais:
        if x.cad.lat is None:
            continue
        sx += x.cad.lon * x.c["aptos"]
        sy += x.cad.lat * x.c["aptos"]
        w += x.c["aptos"]
    if not w:
        return None, None
    return round(sy / w, 4), round(sx / w, 4)


def escrever_uf(
    res: ResultadoUF,
    municipios: Mapping[str, fontes.Municipio],
    nomes_ibge: Mapping[str, list[str]],
    tabela: TabelaRenda | None,
    problemas: Mapping[str, Any],
) -> dict[str, Any]:
    """Arquivos do município e da UF; devolve as linhas do índice e o resumo da UF."""
    uf = res.uf
    pais = (
        {cd: c.get("pais") for cd, c in fontes.cidades_exterior().items()}
        if uf == "ZZ"
        else {}
    )
    por_mun: dict[str, list[Local]] = defaultdict(list)
    for loc in res.locais:
        por_mun[loc.cad.mun_tse].append(loc)
    linhas_indice = []
    resumo_mun = []
    bytes_mun = 0
    for mun_tse, locais in sorted(por_mun.items()):
        mun = municipios.get(mun_tse)
        nome = nome_municipio(mun, nomes_ibge, locais[0].cad.municipio)
        fontes_perfil = {x.perfil_fonte for x in locais if x.perfil_fonte}
        perfil_fonte = (
            fontes_perfil.pop()
            if len(fontes_perfil) == 1
            else ("misto" if fontes_perfil else None)
        )
        tot = totais(locais, tabela)
        arquivo = f"mun/{uf}/{mun_tse}.json"
        bytes_mun += gravar_json(
            fontes.SAIDA / arquivo,
            {
                "uf": uf,
                "mun_tse": mun_tse,
                "ibge": mun.ibge if mun else None,
                "nome": nome,
                "pais": pais.get(mun_tse),
                "totais": tot,
                "perfil_fonte": perfil_fonte,
                "locais": {
                    "colunas": list(COLUNAS_LOCAL),
                    "linhas": [linha(x) for x in locais],
                },
            },
        )
        lat, lon = centro(locais)
        coords = {x.cad.coord_fonte for x in locais if x.cad.coord_fonte}
        linhas_indice.append(
            [
                uf,
                mun_tse,
                mun.ibge if mun else None,
                nome,
                lat,
                lon,
                len(locais),
                tot["aptos"],
                tot["flavio_v"],
                tot["lula_v"],
                arquivo,
                "cidade" if "cidade" in coords else ("cadastro" if coords else None),
                pais.get(mun_tse),
                nome_alternativo(mun, nome),
            ]
        )
        resumo_mun.append((mun_tse, nome, arquivo, tot))
    tot_uf = totais(res.locais, tabela)
    nome_uf, regiao, _ = fontes.UFS[uf]
    gravar_json(
        fontes.SAIDA / f"uf/{uf}.json",
        {
            "uf": uf,
            "nome": nome_uf,
            "regiao": regiao,
            "totais": tot_uf,
            "problemas": problemas_uf(uf, problemas),
            "municipios_mais_disputados": mais_disputados(resumo_mun),
            "ranking_indice": ranking(res.locais, municipios, nomes_ibge),
        },
    )
    copiar_malha(uf)
    return {
        "linhas_indice": linhas_indice,
        "uf": {
            "uf": uf,
            "nome": nome_uf,
            "aptos": tot_uf["aptos"],
            "flavio_v": tot_uf["flavio_v"],
            "lula_v": tot_uf["lula_v"],
            "abst_a": tot_uf["abst_a"],
            "n_locais": len(res.locais),
            "votos_em_aberto": tot_uf["votos_em_aberto"],
            "locais_viraveis_flavio": tot_uf["locais_viraveis_flavio"],
            "aptos_locais_viraveis_flavio": tot_uf["aptos_locais_viraveis_flavio"],
            "locais_viraveis_lula": tot_uf["locais_viraveis_lula"],
            "aptos_locais_viraveis_lula": tot_uf["aptos_locais_viraveis_lula"],
            "locais_com_boletim": tot_uf["locais_com_boletim"],
            "secoes_com_boletim": tot_uf["secoes_com_boletim"],
            "arquivo": f"uf/{uf}.json",
        },
        "bytes_municipios": bytes_mun,
    }


def escrever_zonas(
    res: ResultadoUF,
    municipios: Mapping[str, fontes.Municipio],
    nomes_ibge: Mapping[str, list[str]],
) -> tuple[list[int], int]:
    """Um arquivo por zona eleitoral (única dentro da UF), uma linha por seção."""
    por_zona: dict[int, list] = defaultdict(list)
    for sec in res.secoes():
        por_zona[sec.chave[1]].append(sec)
    total = 0
    for zona, secoes in sorted(por_zona.items()):
        secoes.sort(key=lambda s: s.chave[2])
        muns = sorted({s.chave[0] for s in secoes})
        total += gravar_json(
            fontes.SAIDA / f"zona/{res.uf}/{zona}.json",
            {
                "uf": res.uf,
                "zona": zona,
                "municipios": [
                    {
                        "mun_tse": m,
                        "nome": nome_municipio(
                            municipios.get(m),
                            nomes_ibge,
                            next(
                                s.local.cad.municipio for s in secoes if s.chave[0] == m
                            ),
                        ),
                    }
                    for m in muns
                ],
                "secoes": {
                    "colunas": list(COLUNAS_SECAO),
                    "linhas": [linha_secao(s) for s in secoes],
                },
            },
        )
    return sorted(por_zona), total


def problemas_uf(uf: str, problemas: Mapping[str, Any]) -> dict[str, Any] | None:
    reg = problemas.get("estados", {}).get(uf)
    if not reg:
        return None
    return {
        "pergunta": problemas.get("pergunta"),
        "campo": reg.get("campo"),
        "valores": reg.get("valores"),
        "fonte": f"Quaest, relatório estadual {reg.get('arquivo')}",
        "pagina": reg.get("pagina"),
    }


def mais_disputados(resumo: list[tuple[str, str, str, dict]]) -> list[dict[str, Any]]:
    """Municípios com pelo menos 5 mil aptos e a menor distância entre os dois."""
    elegiveis = [
        r
        for r in resumo
        if r[3]["aptos"] >= APTOS_DISPUTA and r[3]["margem_v"] is not None
    ]
    elegiveis.sort(key=lambda r: (abs(r[3]["margem_v"]), -r[3]["aptos"]))
    saida = []
    for mun_tse, nome, arquivo, t in elegiveis[:N_DISPUTA]:
        saida.append(
            {
                "mun_tse": mun_tse,
                "nome": nome,
                "aptos": t["aptos"],
                "flavio_v": t["flavio_v"],
                "lula_v": t["lula_v"],
                "margem_v": t["margem_v"],
                "indice": t["indice"],
                "faltam": t["faltam"],
                "arquivo": arquivo,
            }
        )
    return saida


def ranking(
    locais: list[Local],
    municipios: Mapping[str, fontes.Municipio],
    nomes_ibge: Mapping[str, list[str]],
) -> list[dict[str, Any]]:
    """20 locais de maior índice com pelo menos 300 aptos (desempate: potencial, aptos)."""
    elegiveis = [
        x
        for x in locais
        if x.c["aptos"] >= APTOS_RANKING and x.m.get("indice") is not None
    ]
    elegiveis.sort(key=lambda x: (-x.m["indice"], -x.m["potencial"], -x.c["aptos"]))
    saida = []
    for x in elegiveis[:N_RANKING]:
        nome_mun = nome_municipio(
            municipios.get(x.cad.mun_tse), nomes_ibge, x.cad.municipio
        )
        saida.append(
            {
                "local_id": x.id,
                "nome": x.cad.nome,
                "municipio": nome_mun,
                "mun_tse": x.cad.mun_tse,
                "bairro": x.cad.bairro,
                "aptos": round(x.c["aptos"]),
                "indice": x.m["indice"],
                "potencial": mt.r1(x.m["potencial"]),
                "arquetipo": x.m["arquetipo"],
                "margem_v": mt.r1(x.m["margem_v"]),
                "arquivo": f"mun/{x.cad.uf}/{x.cad.mun_tse}.json",
            }
        )
    return saida


def copiar_malha(uf: str) -> None:
    """Malha municipal da UF; para o exterior, o planisfério."""
    origem = fontes.GEO_MUNDO if uf == "ZZ" else fontes.DIR_MALHA / f"{uf}.geojson"
    destino = fontes.SAIDA / f"geo/{uf}.geojson"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origem, destino)


def escrever_ceps(locais: Iterable[Local], ufs_refeitas: set[str]) -> dict[str, int]:
    """Índice de CEP dos locais, por dois primeiros dígitos.

    Ao refazer só algumas UFs, as entradas das demais UFs já gravadas são mantidas.
    """
    novos: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(
        lambda: {"exato": defaultdict(list), "prefixo5": defaultdict(list)}
    )
    for x in locais:
        cep = x.cad.cep
        if not cep:
            continue
        arq = novos[cep[:2]]
        arq["exato"][cep].append(x.id)
        arq["prefixo5"][cep[:5]].append(x.id)
    pasta = fontes.SAIDA / "cep"
    prefixos = set(novos)
    if pasta.exists():
        prefixos |= {p.stem for p in pasta.glob("*.json")}
    contagem = {"arquivos": 0, "ceps": 0}
    for prefixo in sorted(prefixos):
        caminho = pasta / f"{prefixo}.json"
        dados: dict[str, dict[str, list[str]]] = {"exato": {}, "prefixo5": {}}
        if caminho.exists():
            antigo = json.loads(caminho.read_text(encoding="utf-8"))
            for parte in ("exato", "prefixo5"):
                for chave, ids in antigo.get(parte, {}).items():
                    manter = [i for i in ids if i.split("-")[0] not in ufs_refeitas]
                    if manter:
                        dados[parte][chave] = manter
        for parte in ("exato", "prefixo5"):
            for chave, ids in novos.get(prefixo, {}).get(parte, {}).items():
                dados[parte][chave] = sorted(
                    set(dados[parte].get(chave, [])) | set(ids)
                )
        if not dados["exato"]:
            caminho.unlink(missing_ok=True)
            continue
        dados = {p: dict(sorted(dados[p].items())) for p in ("exato", "prefixo5")}
        gravar_json(caminho, dados)
        contagem["arquivos"] += 1
        contagem["ceps"] += len(dados["exato"])
    return contagem


def escrever_pnad(tabela: TabelaRenda) -> None:
    gravar_json(fontes.SAIDA / "pnad_renda.json", tabela.json())
