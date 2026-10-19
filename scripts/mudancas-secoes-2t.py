#!/usr/bin/env python3
"""Motor do laudo sobre mudanças de local de votação entre o 1º e o 2º turno de 2026.

Contrato: ``analysis/mudancas_secoes_2t/CONTRATO.md``. Lê os dois cadastros de locais
do TSE direto do ZIP, classifica cada seção (A a Z), separa a mudança real de prédio,
cruza com a urna, os logs e o 2º turno de 2022, compara com os números públicos e com
o painel do TSE e grava:

- ``analysis/mudancas_secoes_2t/mudancas.json`` e ``relatorio.md``;
- ``docs/assets/mudancas_secoes/dados.json`` e ``secoes.csv``;
- ``docs/assets/politize/dados/mudancas/indice.json`` e ``<UF>/<zona>.json``.

Uso::

    python3 scripts/mudancas-secoes-2t.py              # 2.000 réplicas
    python3 scripts/mudancas-secoes-2t.py --reps 200   # rascunho rápido
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from mudancas_secoes_2t import analises as an
from mudancas_secoes_2t import blocos as bl
from mudancas_secoes_2t import cenarios as ce
from mudancas_secoes_2t import classificacao as cl
from mudancas_secoes_2t import confronto as co
from mudancas_secoes_2t import cruzamentos as cr
from mudancas_secoes_2t import distancia as di
from mudancas_secoes_2t import externos as ex
from mudancas_secoes_2t import leitura as le
from mudancas_secoes_2t import relatorio as rl
from mudancas_secoes_2t import saidas as sa
from mudancas_secoes_2t import textos as tx

ROOT = Path(__file__).resolve().parents[1]
VERSAO = "1.0"
REFERENCIA = {
    "A": (754, 222482),
    "B": (255, 72878),
    "C": (26, 9088),
    "D": (86, 27388),
    "E": (220, 57308),
    "F": (208, 66456),
    "G": (575, 169170),
    "H": (1034, 284030),
    "Z": (514021, None),
}
LIMITE_HASH = 1 << 30


def fonte_local(chave: str, caminho: Path, descricao: str) -> dict[str, Any]:
    st = caminho.stat()
    meta = {
        "chave": chave,
        "caminho": str(caminho.relative_to(ROOT)),
        "descricao": descricao,
        "bytes": st.st_size,
        "modificado_em": datetime.fromtimestamp(st.st_mtime, timezone.utc)
        .replace(microsecond=0)
        .isoformat(),
    }
    if st.st_size < LIMITE_HASH:
        meta["sha256"] = le.sha256(caminho)
    else:
        meta["sha256"] = None
        meta["nota"] = "SHA-256 omitido: banco local acima de 1 GB"
    return meta


def controle(nome: str, esperado: Any, obtido: Any, passou: bool) -> dict[str, Any]:
    return {
        "nome": nome,
        "esperado": esperado,
        "obtido": obtido,
        "passou": bool(passou),
    }


def controles_base(
    cls: pd.DataFrame, fontes: list[dict[str, Any]], totais: dict
) -> list[dict]:
    out = [
        controle(
            f"SHA-256 {f['chave']}", "confere", f["sha256_confere"], f["sha256_confere"]
        )
        for f in fontes
        if "sha256_confere" in f
    ]
    out.append(controle("seções no cadastro", 517179, len(cls), len(cls) == 517179))
    cont = cls["categoria_cadastro"].value_counts()
    out.append(
        controle(
            "soma das categorias", 517179, int(cont.sum()), int(cont.sum()) == 517179
        )
    )
    for c, (secs, el) in REFERENCIA.items():
        obt = int(cont.get(c, 0))
        el_obt = int(cls.loc[cls["categoria_cadastro"] == c, "eleitores_2t"].sum())
        ok = obt == secs and (el is None or el == el_obt)
        out.append(
            controle(
                f"referência do orquestrador, categoria {c}",
                f"{rl.n(secs)} / {rl.n(el)}" if el else secs,
                f"{rl.n(obt)} / {rl.n(el_obt)}" if el else obt,
                ok,
            )
        )
    t1 = cls["temp_1t_cadastro"]
    t2 = cls["temp_2t_cadastro"]
    for nome, m, ref in (
        ("fora do original no 1º turno", t1, (6535, 1916865)),
        ("fora do original no 2º turno", t2, (6036, 1767261)),
    ):
        par = (int(m.sum()), int(cls.loc[m, "eleitores_2t"].sum()))
        out.append(
            controle(
                nome,
                f"{rl.n(ref[0])} / {rl.n(ref[1])}",
                f"{rl.n(par[0])} / {rl.n(par[1])}",
                par == ref,
            )
        )
    rj = cls[
        (cls["uf"] == "RJ")
        & (cls["mun"] == "60011")
        & (cls["zona"] == 188)
        & cls["secao"].between(123, 127)
    ]
    ok_rj = bool(
        len(rj) == 5 and rj["mudanca_real"].all() and (rj["categoria"] == "D").all()
    )
    out.append(
        controle(
            "caso de controle RJ 60011, zona 188, seções 123 a 127 (Rua Muaná para Rua Irapuá)",
            "5 seções, categoria D, mudança real",
            f"{len(rj)} seções, {sorted(rj['categoria'].unique())}, mudança real "
            f"{bool(rj['mudanca_real'].all())}, {int(rj['eleitores_2t'].sum())} eleitores "
            "(TRE-RJ: cerca de 1.800)",
            ok_rj,
        )
    )
    out.append(
        controle(
            "válidos de presidente nas urnas do cadastro = soma de voto_secao",
            totais["validos"],
            totais["validos_nas_urnas_do_cadastro"],
            totais["validos"] == totais["validos_nas_urnas_do_cadastro"],
        )
    )
    return out


def decisoes(r: dict[str, Any], cls: pd.DataFrame) -> list[str]:
    s = r["sensibilidade"]
    g = cls[cls["categoria_cadastro"] == "G"]
    return [
        "G nunca conta como mudança real. A fórmula do contrato incluía G até 50 km, mas G "
        "tem nome e endereço idênticos nos dois arquivos: o eleitor vai ao mesmo prédio. A "
        "conferência mostrou marcadores de posição: em Maringá (zona 137) 14 locais "
        "diferentes tinham no 1º turno a mesma coordenada; em Candeias (zona 127) vários "
        "locais passaram no 2º turno para a mesma coordenada. "
        f"Se G contasse: {rl.n(s['g_se_contasse']['secoes'])} seções, "
        f"{rl.n(s['g_se_contasse']['eleitores'])} eleitores.",
        f"A referência G = 575 inclui {int(g['coord_um_turno'].sum())} "
        "seções em que a coordenada existe em um só dos turnos; elas ficam em G com "
        "coord_suspeita e distância nula.",
        "D só não conta quando nome e endereço normalizados são iguais (mudança de grafia, "
        "um caso em Maringá); D com endereço igual e nome de outra instituição conta, com "
        "confiança média.",
        "E conta quando o logradouro normalizado é outro (comparação tolerante a "
        "abreviação, complemento, número acrescentado e localidade antes da rua); número "
        "diferente no mesmo logradouro não conta. E real tem confiança média: pode ser outra "
        "entrada do mesmo prédio.",
        "A, B, C e X não contam quando nome e endereço normalizados são iguais (outro número "
        f"para o mesmo prédio): {s['abcx_mesmo_predio']['secoes']} seções.",
        "Seção agregada vota na urna da principal: a camada efetiva copia para a agregada o "
        "local e a classificação da principal. "
        f"{s['agregadas_herdam_mudanca']} agregadas mudam de categoria por isso.",
        "Coordenada idêntica para três ou mais locais do mesmo município e turno é marcador "
        "de posição: a distância dessas seções fica fora das estatísticas e o link do mapa "
        "usa o endereço.",
        "No Rio de Janeiro as transferências do TRE-RJ no 1º turno mantiveram o número do "
        "local e trocaram nome e endereço, então não aparecem como local diferente do "
        "original. O efeito do 1º turno ganhou o grupo troca desde 2022 (mesmo número, "
        "nome sem palavra em comum com o de 2022).",
        "Diferença em diferenças: controle = seções estáveis (mesmo número de 2022 e nome "
        "compatível), não todas as demais, para não misturar no controle seções que também "
        "trocaram de prédio.",
        "Fila no fechamento = último voto depois das 18h de Brasília (a votação terminou às "
        "17h); abertura atrasada = primeiro voto às 8h30 de Brasília ou depois; fuso pela "
        "moda da hora de abertura no município (apuracao_2026.secoes_base.fusos_por_municipio).",
        "O exterior fica fora de comportamento, intercorrências e efeito (regra da casa para "
        "comparações nacionais); entra nos cenários e nas contagens.",
        "No Politize, a lista é a união do arquivo de locais (mudança real) com o painel do "
        "TSE de seções alteradas, com o campo fonte.",
        "Medianas de distância com IC por reamostragem de pares de locais (todas as seções "
        "de um par têm a mesma distância). Comparações de votos e logs por bootstrap de "
        "prédios (as urnas de um mesmo local do 1º turno saem juntas), estratificado, e "
        "não seção a seção como dizia o contrato: seções do mesmo prédio dividem o mesmo "
        "evento (em Laranjeiras do Sul, PR, 12 urnas de uma só escola abriram depois das "
        "8h30), e a reamostragem por seção estreitaria o IC sem base. Os pontos não mudam.",
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261019)
    args = ap.parse_args()
    t0 = time.time()
    gerado_em = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    print("lendo cadastros...", flush=True)
    t1, t2, fontes = le.ler_cadastros()
    cls = cl.classificar(t1, t2)
    print(f"classificadas {len(cls)} seções ({time.time() - t0:.0f} s)", flush=True)
    urnas, totais = cr.montar_urnas(cls)
    print(f"urnas cruzadas ({time.time() - t0:.0f} s)", flush=True)
    painel, meta_painel = co.ler_painel()
    p = an.preparar(urnas)
    res = an.executar(p, args.reps, args.seed)
    res_rj = bl.rj(p, an.grupos_celula(an.celulas(p)), args.reps, args.seed + 7)
    print(f"bootstrap pronto ({time.time() - t0:.0f} s)", flush=True)

    cadastro_t1 = {
        "secoes": int(cls["temp_1t_cadastro"].sum()),
        "eleitores": int(cls.loc[cls["temp_1t_cadastro"], "eleitores_2t"].sum()),
    }
    efeito = bl.efeito(res, res_rj, p, cadastro_t1)
    clima = ex.ler_clima()
    tre_itens = ex.ler_tre()
    base_pares = cls[cls["categoria"] != "Z"][
        ["uf", "mun", "municipio", "zona", "local_1t", "local_2t", "nome_1t", "nome_2t"]
    ].drop_duplicates(["uf", "mun", "zona", "local_1t", "local_2t"])
    tre = ex.casar_tre(tre_itens, base_pares)
    pares = sa.montar_pares(cls, urnas, clima, tre)

    mr = cls[cls["mudanca_real"]]
    brasil = cls[cls["uf"] != "ZZ"]
    vizinhos = di.vizinho_mais_proximo(brasil)
    distancia = {
        "regra": di.REGRA,
        "mudanca_real": di.histograma(mr),
        "por_categoria": di.por_categoria(mr),
        "por_uf": di.por_uf(mr),
        "top_20": sa.top_deslocamentos(pares),
        "teste_hipotese": di.teste_hipotese(
            mr, brasil, vizinhos, args.reps, args.seed + 11
        ),
    }
    print(f"distâncias prontas ({time.time() - t0:.0f} s)", flush=True)

    urnas_cen = urnas[urnas["tem_bu"]]
    rio_dd = efeito["rj"]["dif_em_dif_mesma_zona"]["diferenca_pp"]
    efeito_rio = {
        "fonte": "efeito_1t.rj.dif_em_dif_mesma_zona.diferenca_pp",
        "valor": rio_dd["valor"],
        "ic95": rio_dd["ic95"],
    }
    cen = ce.montar(
        urnas_cen, totais["validos"], efeito["magnitude_para_cenarios"], efeito_rio
    )
    resumo = sa.resumo(cls, urnas)
    confronto = co.confronto_publico(cls, meta_painel)
    painel_bloco = None
    painel_chaves: set[tuple] = set()
    originais: dict[tuple, dict[str, Any]] = {}
    if painel is not None and meta_painel is not None:
        cp = co.confronto_painel(cls, painel, meta_painel)
        painel_bloco = cp["resumo"]
        originais = cp["originais"]
        painel_chaves = set(
            map(tuple, painel[["uf", "zona", "secao"]].to_numpy().tolist())
        )
        confronto["painel_contra_tse_16_10"] = (
            f"O painel oficial (atualização {meta_painel['ultima_atualizacao_tse']}) lista "
            f"{meta_painel['linhas']} seções; o TSE divulgou 4.352 seções em 16/10. Mesma "
            "fonte institucional, dois carimbos de hora, números diferentes."
        )
    colunas_local = ["uf", "mun", "zona", "local_1t"]
    ids_real = {
        sa.id_clima(r["uf"], r["mun"], r["zona"], r["local_1t"])
        for r in sa.registros(mr[colunas_local].drop_duplicates())
    }
    todos = cls[cls["categoria"].isin(list("ABCXDEFG"))]
    ids_todos = {
        sa.id_clima(r["uf"], r["mun"], r["zona"], r["local_1t"])
        for r in sa.registros(todos[colunas_local].drop_duplicates())
    }
    casados = sum(1 for x in pares if x["motivo_tre"])
    graus = pd.Series(
        [x["motivo_tre"]["grau_casamento"] for x in pares if x["motivo_tre"]]
    )
    tre_resumo = (
        "pendente: tre_noticias.json não existia no build"
        if not tre_itens
        else f"{len(tre_itens)} itens lidos; {casados} pares de locais casados com alguma "
        f"nota ({graus.value_counts().to_dict()})"
    )
    zonas_mr = {(u, int(z)) for u, z in mr[["uf", "zona"]].drop_duplicates().to_numpy()}
    conferencia = cr.conferir_politize(urnas[urnas["tem_bu"]], zonas_mr)

    fontes_extra = [
        fonte_local(
            "boletins_1t", cr.BU, "Boletins de urna do 1º turno por seção (banco local)"
        ),
        fonte_local("logs_1t", cr.LOGS, "Métricas dos logs das urnas do 1º turno"),
        fonte_local(
            "mapa_fiscais",
            cr.FISCAIS / "indice.json",
            "Índice do mapa de fiscais (atenção)",
        ),
        fonte_local("presidente_2022", cr.CSV_2022, "Presidente por seção em 2022"),
        fonte_local(
            "detalhe_2022",
            ROOT / "data/raw/tse_resultados/detalhe_votacao_secao_2022.zip",
            "Detalhe de votação por seção de 2022 (2º turno: aptos e comparecimento)",
        ),
    ]
    for chave, caminho in (
        ("clima_open_meteo", ex.CLIMA),
        ("tre_noticias", ex.TRE),
        ("fontes_1t_imprensa", ex.FONTES_1T),
    ):
        meta = ex.meta_arquivo(caminho)
        fontes_extra.append(
            {
                "chave": chave,
                **(
                    meta
                    or {
                        "caminho": str(caminho.relative_to(ROOT)),
                        "situacao": "pendente",
                    }
                ),
            }
        )
    if meta_painel:
        fontes_extra.append({"chave": "painel_tse", **meta_painel})

    payload: dict[str, Any] = {
        "gerado_em": gerado_em,
        "versao": VERSAO,
        "parametros": {"reps": args.reps, "seed": args.seed},
        "fontes": fontes + fontes_extra,
        "totais_nacionais_1t": totais,
        "regras": {"nomes": cl.NOMES, "categorias": cl.REGRAS},
        "resumo": resumo,
        "confronto_publico": confronto,
        "confronto_painel": painel_bloco,
        "por_uf": sa.por_uf(cls, ex.notas_por_uf(tre_itens), painel),
        "por_municipio": sa.por_municipio(cls),
        "distancia": distancia,
        "locais": pares,
        "comportamento_1t": bl.comportamento(res, p),
        "intercorrencias_1t": bl.intercorrencias(res, p),
        "efeito_1t": efeito,
        "clima_resumo": ex.clima_resumo(
            clima, ids_real, ids_todos, args.reps, args.seed + 13
        ),
        "tre_resumo": tre_resumo,
        "cenarios_abstencao": ce.tirar_exatos(cen),
        "quem_perde": tx.quem_perde(cen),
        "limites": tx.limites(clima is None, not tre_itens),
        "conferencia_politize": conferencia,
        "_interno": {
            "segundos": None,
            "urnas_municipios_alvo": res["urnas_municipios_alvo"],
            "predios_municipios_alvo": res["predios_municipios_alvo"],
            "predios": res["predios"],
            "unidade_bootstrap": res["unidade"],
            "municipios_alvo": res["municipios_alvo"],
            "celulas": res["celulas"],
        },
    }
    ctrl = controles_base(cls, fontes, totais)
    ctrl.append(
        controle(
            "abstenção nacional com exterior (ConJur: 21,08%)",
            21.08,
            round((1 - urnas["comparecimento"].sum() / urnas["aptos"].sum()) * 100, 2),
            round((1 - urnas["comparecimento"].sum() / urnas["aptos"].sum()) * 100, 2)
            == 21.08,
        )
    )
    ctrl.append(
        controle(
            "aptos e votos das urnas com mudança iguais aos do Politize",
            0,
            conferencia["diferentes"],
            conferencia["diferentes"] == 0,
        )
    )
    fecha = all(
        abs(sum(f[g]["_exato"][c] for c in ce.COMPONENTES) - f[g]["_exato"]["total"])
        < 1e-6
        for f in cen["fixos"]
        for g in ("mudanca_real", "categoria_a", "novas_realocacoes")
    )
    ctrl.append(
        controle("cenários fecham (componentes somam o total)", True, fecha, fecha)
    )
    if painel_bloco:
        ctrl.append(
            controle(
                "eleitorado do painel igual ao do arquivo nas seções dos dois",
                painel_bloco["ambos_eleitorado_painel"],
                painel_bloco["ambos_eleitores_zip"],
                painel_bloco["ambos_eleitorado_painel"]
                == painel_bloco["ambos_eleitores_zip"],
            )
        )
    payload["controles"] = ctrl
    payload["decisoes"] = decisoes(resumo, cls)
    payload["_interno"]["segundos"] = round(time.time() - t0)

    publico = sa.publico(payload)
    texto_publico = json.dumps(publico, ensure_ascii=False)
    sem_travessao = chr(0x2014) not in texto_publico
    sem_palavra = "fraude" not in texto_publico.lower()
    ctrl.append(
        controle("nenhum travessão no JSON público", True, sem_travessao, sem_travessao)
    )
    ctrl.append(
        controle("nenhuma ocorrência da palavra vetada", True, sem_palavra, sem_palavra)
    )
    publico["controles"] = ctrl

    sa.gravar_json(payload, sa.ANALISE / "mudancas.json")
    sa.gravar_json(publico, sa.PUBLICO / "dados.json", compacto=True)
    linhas = sa.linhas_csv(cls, urnas, painel_chaves)
    sa.gravar_csv(linhas, sa.PUBLICO / "secoes.csv")
    indice = sa.politize(cls, pares, painel, gerado_em, originais)
    (sa.ANALISE / "relatorio.md").write_text(
        rl.gerar(payload, ctrl, payload["decisoes"]), encoding="utf-8"
    )
    falhas = [c["nome"] for c in ctrl if not c["passou"]]
    print(
        f"pronto em {time.time() - t0:.0f} s: {resumo['mudanca_real']['secoes']} seções com "
        f"mudança real, {resumo['mudanca_real']['eleitores']} eleitores; Politize "
        f"{indice['total_secoes']} seções; controles que não passaram: {falhas or 'nenhum'}"
    )


if __name__ == "__main__":
    main()
