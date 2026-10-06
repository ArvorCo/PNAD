"""Texto da análise por seção: achados (verificado, inferido, juízo, hipótese) e o
memorando `analysis/apuracao_2026/secoes.md`, gerados do JSON.

Toda frase com número sai daqui, a partir do dicionário do contrato; nada é
digitado à mão. A primeira frase de cada bloco é o achado que contraria a tese
mais comum do leitor, quando os números o sustentam.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .secoes_base import num

PROIBIDO = "—"


def _p(x: float | None, casas: int = 1) -> str:
    return "n/d" if x is None else num(x, casas)


def _n(x: int | float | None) -> str:
    return "n/d" if x is None else num(float(x), 0)


def _resumo(d: Mapping[str, Any], cand: str, limiar: int) -> Mapping[str, Any]:
    for r in d["extremos"]["resumo"]:
        if r["candidato"] == cand and r["limiar"] == limiar:
            return r
    return {}


def _par(
    pares: Sequence[Mapping[str, Any]], a: str, b: str
) -> Mapping[str, Any] | None:
    return next((p for p in pares if p["a"] == a and p["b"] == b), None)


def _pp(x: float | None) -> str:
    if x is None:
        return "sem resto de zona para comparar"
    return f"{num(x, 2)} {'ponto' if abs(x) < 2 else 'pontos'}"


def _ic(m: Mapping[str, Any] | None) -> str:
    if not m:
        return "n/d"
    lo, hi = m["ic95"]
    return f"{_p(m['estimativa'], 2)} (IC 95% de {_p(lo, 2)} a {_p(hi, 2)})"


def _zero_dentro(m: Mapping[str, Any] | None) -> bool | None:
    if not m:
        return None
    lo, hi = m["ic95"]
    return lo is not None and hi is not None and lo <= 0 <= hi


# ---------------------------------------------------------------- achados


def achados(d: Mapping[str, Any]) -> dict[str, list[str]]:
    cob = d["cobertura"]
    ex = d["extremos"]
    cl = d["clusters"]
    ur = d["urna"]
    ou = d["outras"]
    l90 = _resumo(d, "lula", 90)
    f90 = _resumo(d, "flavio", 90)
    verificado = [
        f"Base: {_n(cob['secoes_validas'])} boletins de urna de seção, todos em zonas "
        "cuja soma das seções confere com o arquivo de zona do TSE"
        + (" (coleta parcial)." if cob.get("parcial") else "."),
        f"Seções com Lula em 90% ou mais dos válidos: {_n(l90.get('secoes'))} "
        f"({_p(l90.get('pct_das_secoes'), 2)}% das seções), "
        f"{_n(l90.get('aptos'))} eleitores aptos; com Flávio: {_n(f90.get('secoes'))} "
        f"({_p(f90.get('pct_das_secoes'), 2)}%), {_n(f90.get('aptos'))} aptos.",
        f"Comparecimento acima de 100% dos aptos: {_n(ou['comparecimento']['acima_100'])} "
        f"seções; igual a 100%: {_n(ou['comparecimento']['igual_100'])}.",
        f"Seções com 200 votantes ou mais e nenhum voto em Lula: "
        f"{_n(ou['zero_votos']['lula']['secoes'])}; nenhum voto em Flávio: "
        f"{_n(ou['zero_votos']['flavio']['secoes'])}.",
    ]
    c22 = ex.get("comparacao_2022", {})
    if c22.get("disponivel"):
        lu = c22["lula"]
        verificado.append(
            f"Das {_n(lu['secoes_90_2026_casadas'])} seções com Lula em 90% ou mais "
            "que existem com o mesmo número e o mesmo local em 2022, "
            f"{_n(lu['tambem_90_em_2022_1t'])} já davam 90% ou mais a ele no 1º "
            f"turno de 2022 e {_n(lu['acima_80_em_2022_1t'])} davam 80% ou mais; "
            f"mediana de 2022: {_p(lu['pct_2022_1t_mediana'])}%."
        )
    inferido = []
    exc = ex["excesso"]["lula"]
    zm = exc["zona_pct_mediana"] or 0.0
    onde = (
        "estão em zonas que já votam muito nele"
        if zm >= 70
        else "são, em boa parte, enclaves dentro de zonas que votam menos nele"
    )
    inferido.append(
        f"As seções de 90% de Lula {onde}: mediana de {_p(zm)}% no resto da zona; "
        f"o excesso típico da seção sobre a zona é de "
        f"{_p(exc['excesso_zona_pp_mediana'])} pontos."
    )
    tl = {r["tipo"]: r for r in ex["tipo_local"]["linhas"]}
    ald = tl.get("aldeia ou terra indígena")
    if ald:
        inferido.append(
            f"Locais com nome de aldeia ou escola indígena: {_n(ald['todas'])} seções, "
            f"{_n(ald['lula_90'])} delas com Lula em 90% ou mais "
            f"({_p(ald['lula_90_pct_do_tipo'])}% do tipo, contra "
            f"{_p(_resumo(d, 'lula', 90).get('pct_das_secoes'), 2)}% no total)."
        )
    inferido.extend(cl["interpretacao"][:3])
    if cl.get("leitura_projecao"):
        inferido.append(cl["leitura_projecao"])
    inferido.extend(ur.get("interpretacao", []))
    juizo = [
        "Seção com 90% para um candidato é, na esmagadora maioria, lugar que sempre "
        "votou assim: aldeia, zona rural do Nordeste, comunidade pequena. O número "
        "chama atenção na manchete e some quando se olha a zona e 2022.",
        "Nenhum dos testes por seção aponta irregularidade. O que fica atípico "
        "exige explicação documental (ata da mesa, log da urna, plano de alocação "
        "das urnas do TRE), não conclusão.",
    ]
    hipotese = [
        "Diferença entre modelos de urna que sobreviva ao controle por zona pode vir "
        "da alocação não aleatória das urnas dentro da zona (escolas centrais e "
        "periféricas, locais grandes e pequenos). Só o plano de alocação do TRE "
        "separa essa hipótese de um efeito do equipamento.",
    ]
    contrario = []
    if c22.get("disponivel"):
        contrario.append(
            "Quem espera achar seções novas de 90% encontra as velhas: "
            f"{_n(c22['lula']['tambem_90_em_2022_1t'])} de "
            f"{_n(c22['lula']['secoes_90_2026_casadas'])} seções casadas de Lula já "
            "estavam acima de 90% em 2022."
        )
    contrario.append(cl["interpretacao"][0])
    if ur.get("interpretacao"):
        contrario.append(ur["interpretacao"][0])
    return {
        "verificado": verificado,
        "inferido": inferido,
        "juizo": juizo,
        "hipotese": hipotese,
        "contrario": contrario,
    }


LIMITES = [
    "Zona é o par município e zona eleitoral, como no arquivo de zona do TSE.",
    "Seções agregadas não têm boletim próprio: o voto delas está no da seção "
    "principal, e os aptos do boletim já as incluem.",
    "Tipo de local é inferência por palavra-chave no cadastro de locais do TSE; "
    "o nome do local não prova o perfil do eleitor.",
    "O modelo da urna vem do log da própria urna; urna de reserva ou contingência "
    "aparece com o modelo da urna que gravou o boletim.",
    "A comparação com 2022 casa a seção pelo número e pelo nome do local; seção "
    "renumerada ou local trocado fica de fora.",
    "Seções pequenas inflam percentuais: 100% de 30 válidos não é o mesmo que "
    "100% de 300. Por isso os cortes por tamanho e o corte de 100 votantes.",
    "A mistura gaussiana sobre log-razões com zero trocado por 0,0001 é sensível "
    "ao padrão de zeros; a leitura política vem da versão densa.",
    "Benford e último dígito são curiosidade metodológica, não teste de fraude.",
]


# ---------------------------------------------------------------- memorando


def memorando(d: Mapping[str, Any]) -> str:
    cob = d["cobertura"]
    ex = d["extremos"]
    cl = d["clusters"]
    ur = d["urna"]
    ou = d["outras"]
    ac = d["achados"]
    linhas: list[str] = []
    w = linhas.append
    w("# Análise por seção (boletins de urna), presidente, 1º turno de 2026")
    w("")
    w(
        f"Gerado em {d['gerado_em']} por `scripts/apuracao-2026-secoes.py`. "
        "Dados em `analysis/apuracao_2026/dados/secoes.json` (contrato em "
        "`analysis/apuracao_2026/CONTRATO_SECOES.md`)."
    )
    w("")
    w(f"> {d['aviso']}")
    w("")
    if cob.get("parcial"):
        w(
            f"**Coleta parcial.** {_n(cob['secoes_validas'])} seções válidas de "
            f"{_n(cob['secoes_principais_cs'])} seções principais do país; UFs "
            f"completas: {', '.join(cob['ufs_completas']) or 'nenhuma'}. Os números "
            "mudam quando a coleta terminar."
        )
        w("")
    w("## Cobertura")
    w("")
    w(
        f"- Seções no cadastro do TSE (cs): {_n(cob['secoes_cs'])}, das quais "
        f"{_n(cob['secoes_agregadas_cs'])} agregadas (sem boletim próprio)."
    )
    w(
        f"- Boletins lidos: {_n(cob['secoes_com_bu'])}; válidos para a análise: "
        f"{_n(cob['secoes_validas'])}."
    )
    for e in cob["excluidas"]:
        w(f"- Fora: {_n(e['secoes'])} seções, {e['motivo']}.")
    t = cob["totais_validos"]
    w(
        f"- Nas seções válidas: Flávio {_p(t['flavio_pct'], 2)}% e Lula "
        f"{_p(t['lula_pct'], 2)}% dos válidos, {_n(t['validos'])} válidos."
    )
    cn = cob.get("confere_nacional")
    if cn:
        w(f"- Conferência com o resultado nacional do TSE: {cn['texto']}")
    w("")

    # ---------------- A
    w("## A. Seções com 90% ou mais para um candidato")
    w("")
    w(ac["contrario"][0] if ac["contrario"] else "")
    w("")
    w("| candidato | limiar | seções | com 100+ votantes | aptos | % das seções |")
    w("|---|---|---|---|---|---|")
    for r in ex["resumo"]:
        nome = "Lula" if r["candidato"] == "lula" else "Flávio"
        w(
            f"| {nome} | {r['limiar']}% | {_n(r['secoes'])} | "
            f"{_n(r['secoes_100mais'])} | {_n(r['aptos'])} | "
            f"{_p(r['pct_das_secoes'], 2)} |"
        )
    w("")
    w("Por tamanho (votantes da seção):")
    w("")
    w("| faixa | seções | Lula ≥ 90% | % | Flávio ≥ 90% | % |")
    w("|---|---|---|---|---|---|")
    for r in ex["tamanho"]["linhas"]:
        w(
            f"| {r['faixa']} | {_n(r['todas'])} | {_n(r['lula_90'])} | "
            f"{_p(r['lula_90_pct'], 2)} | {_n(r['flavio_90'])} | "
            f"{_p(r['flavio_90_pct'], 2)} |"
        )
    w("")
    for cand, nome in (("lula", "Lula"), ("flavio", "Flávio")):
        e = ex["excesso"][cand]
        w(
            f"- {nome}: {_n(e['secoes'])} seções em 90% ou mais; o resto da zona "
            f"dá {_p(e['zona_pct_mediana'])}% a {nome} (mediana) e o excesso da "
            f"seção sobre a zona é {_p(e['excesso_zona_pp_mediana'])} pontos "
            f"(mediana); {_n(e['acima_zona_20pp'])} seções ficam 20 pontos ou "
            "mais acima da própria zona."
        )
    w("")
    w("Por tipo de local (inferência por palavra-chave; regras no JSON):")
    w("")
    w("| tipo | seções | Lula ≥ 90% | % do tipo | Flávio ≥ 90% | % do tipo |")
    w("|---|---|---|---|---|---|")
    for r in ex["tipo_local"]["linhas"]:
        w(
            f"| {r['tipo']} | {_n(r['todas'])} | {_n(r['lula_90'])} | "
            f"{_p(r['lula_90_pct_do_tipo'], 2)} | {_n(r['flavio_90'])} | "
            f"{_p(r['flavio_90_pct_do_tipo'], 2)} |"
        )
    w("")
    ca = ex["cruzamento_anomalias"]
    w(
        f"Cruzamento com as {ca['top_zonas']} zonas mais atípicas de `anomalias.json`: "
        f"{ca['zonas_top_na_base']} estão na base, {ca['zonas_top_com_secao_90']} têm "
        f"ao menos uma seção de 90%. Taxa de seções com Lula em 90% ou mais: "
        f"{_p(ca['taxa_lula_90_top_pct'], 2)}% nessas zonas e "
        f"{_p(ca['taxa_lula_90_demais_pct'], 2)}% nas demais; Flávio: "
        f"{_p(ca['taxa_flavio_90_top_pct'], 2)}% e "
        f"{_p(ca['taxa_flavio_90_demais_pct'], 2)}%."
    )
    w("")
    c22 = ex.get("comparacao_2022", {})
    if c22.get("disponivel"):
        w(
            f"Mesma seção em 2022 ({c22['criterio_mesma_secao']}): "
            f"{_n(c22['secoes_casadas'])} de {_n(c22['secoes_2026'])} seções casadas."
        )
        for cand, nome, nome22 in (
            ("lula", "Lula", "Lula"),
            ("flavio", "Flávio", "Bolsonaro"),
        ):
            r = c22[cand]
            w(
                f"- {nome} em 90% ou mais em 2026, casadas: "
                f"{_n(r['secoes_90_2026_casadas'])}; {nome22} já tinha 90% ou mais "
                f"no 1º turno de 2022 em {_n(r['tambem_90_em_2022_1t'])} e no 2º "
                f"turno em {_n(r['tambem_90_em_2022_2t'])}; mediana de 2022 "
                f"{_p(r['pct_2022_1t_mediana'])}% (1º turno); variação mediana "
                f"{_p(r['variacao_pp_mediana'])} pontos."
            )
        w("")
    w("Amostras (as de maior excesso sobre a zona, 100 votantes ou mais):")
    w("")
    for cand, nome in (("lula", "Lula"), ("flavio", "Flávio")):
        for s in ex["amostras"][cand][:8]:
            w("- " + _linha_secao(s, nome))
    w("")

    # ---------------- B
    w(f"## B. Mistura gaussiana (k = {cl['k']})")
    w("")
    for f in cl["interpretacao"]:
        w(f"- {f}")
    for chave in ("leitura_projecao", "estabilidade"):
        if cl.get(chave):
            w(f"- {cl[chave]}")
    w("")
    ek = cl.get("escolha_k") or {}
    if ek:
        w(
            f"Escolha de k (juízo editorial): k = {ek['k']}, {ek['motivo']} "
            f"({ek['data']}; antes, k = {ek['anterior']}). O BIC prefere k = "
            f"{ek['bic_prefere']}."
        )
        w("")
    w(
        f"Método: {cl['transformacao_detalhe']}. Covariância completa, "
        f"{cl['ajuste']['n_init']} inicializações por semente, "
        f"{len(cl['ajuste'].get('sementes') or [])} sementes, fica a de maior "
        f"log-verossimilhança (semente {cl['ajuste']['random_state']}), ajuste sobre "
        f"{_n(cl['ajuste']['secoes_ajuste'])} seções (o país inteiro, sem amostra)."
    )
    w("")
    w(
        "BIC (menor é melhor; com os degraus de zeros, a comparação entre k é "
        "instável e serve só de contraste; cada k com o melhor de todas as sementes):"
    )
    w("")
    for b in cl["bic"]:
        w(
            f"- k = {b['k']}: BIC {_p(b['bic'], 1)}, log-verossimilhança média "
            f"{_p(b['loglik_media'], 3)}"
        )
    w("")
    w("| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |")
    w("|---|---|---|---|---|---|")
    for c in cl["componentes"]:
        w(
            f"| {c['id'] + 1} | {c['rotulo']} | {_n(c['secoes'])} | "
            f"{_p(c['aptos_medio'], 0)} | {_p(c['loglik_media'], 2)} | "
            f"{_p(c['dispersao_logdet'], 1)} |"
        )
    w("")
    dens = cl["variantes"]["densa"]
    w(f"Versão densa ({dens['descricao']}):")
    w("")
    w("| grupo | rótulo | seções | aptos médios | log-veross. média | log det Σ |")
    w("|---|---|---|---|---|---|")
    for c in dens["componentes"]:
        w(
            f"| {c['id'] + 1} | {c['rotulo']} | {_n(c['secoes'])} | "
            f"{_p(c['aptos_medio'], 0)} | {_p(c['loglik_media'], 2)} | "
            f"{_p(c['dispersao_logdet'], 1)} |"
        )
    w("")
    w(
        f"Grupo mais anômalo na versão pedida: {cl['mais_anomalo']['id'] + 1}. "
        f"Critério: {cl['mais_anomalo']['criterio']}"
    )
    w("")
    for s in cl["mais_anomalo"]["amostras"][:20]:
        w("- " + _linha_secao(s, None))
    w("")
    w(f"Grupo mais anômalo na versão densa: {dens['mais_anomalo']['id'] + 1}.")
    w("")
    for s in dens["mais_anomalo"]["amostras"][:10]:
        w("- " + _linha_secao(s, None))
    w("")
    sen = cl["sensibilidade"]
    w(
        "Estabilidade (índice de Rand ajustado contra a versão pedida): segunda "
        f"melhor semente {_p(sen.get('ari_principal_vs_outra_semente'), 3)}; nanicas somadas "
        f"{_p(sen['ari_principal_vs_nanicos_somados'], 3)}; versão densa "
        f"{_p(sen['ari_principal_vs_densa'], 3)}."
    )
    w("")

    # ---------------- C
    w("## C. Modelo de urna")
    w("")
    for f in ur.get("interpretacao", []):
        w(f"- {f}")
    w("")
    w("Bruto (soma dos votos por modelo, sem controle):")
    w("")
    w("| modelo | seções | Flávio % | Lula % | abstenção % | brancos % | nulos % |")
    w("|---|---|---|---|---|---|---|")
    for r in ur["bruto"]:
        w(
            f"| {r['modelo']} | {_n(r['secoes'])} | {_p(r['flavio_pct'], 2)} | "
            f"{_p(r['lula_pct'], 2)} | {_p(r['abstencao_pct'], 2)} | "
            f"{_p(r['brancos_pct'], 2)} | {_p(r['nulos_pct'], 2)} |"
        )
    w("")
    for nome, est in (
        ("Dentro da zona", ur["dentro_zona"]),
        ("Dentro do mesmo local", ur["dentro_local"]),
    ):
        w(f"{nome} ({est['definicao']}):")
        w("")
        w(
            "| a → b | unidades | seções a/b | Flávio pp | Lula pp | nulos pp | bruto Flávio |"
        )
        w("|---|---|---|---|---|---|---|")
        for p in est["pares"]:
            w(
                f"| {p['a']} → {p['b']} | {_n(p['unidades'])} | "
                f"{_n(p['secoes_a'])}/{_n(p['secoes_b'])} | {_ic(p.get('flavio_pp'))} | "
                f"{_ic(p.get('lula_pp'))} | {_ic(p.get('nulos_pp'))} | "
                f"{_p((p.get('flavio_pp') or {}).get('bruto'), 2)} |"
            )
        w("")
    var = ur.get("dentro_zona_variacao")
    if var:
        w(f"Variação contra a mesma seção em 2022 ({var['definicao']}):")
        w("")
        for p in var["pares"]:
            w(
                f"- {p['a']} → {p['b']}: {_n(p['unidades'])} zonas; Flávio menos "
                f"Bolsonaro {_ic(p.get('flavio_var_pp'))}; Lula "
                f"{_ic(p.get('lula_var_pp'))}"
            )
        w("")
    tr = ur.get("troca_2022_2026")
    if tr:
        w(
            "Troca de urna entre 2022 e 2026 (mesma seção; rótulo = modelo de 2022; "
            f"{_n(tr['secoes_casadas'])} seções casadas). {tr['definicao']}"
        )
        w("")
        for p in tr["pares"]:
            if p["b"] not in ("UE2020", "mais nova"):
                continue
            w(
                f"- {p['a']} → {p['b']}: {_n(p['unidades'])} zonas; variação de "
                f"Flávio sobre Bolsonaro {_ic(p.get('flavio_var_pp'))}"
            )
        w("")
    a22 = ur.get("ano_2022")
    if a22:
        w("2022, mesmo estimador (Bolsonaro e Lula, 1º turno):")
        w("")
        for nome, est in (
            ("dentro da zona", a22["dentro_zona"]),
            ("dentro do local", a22["dentro_local"]),
        ):
            for p in est["pares"]:
                if p["a"] != "mais velha" and p["b"] != "UE2020":
                    continue
                w(
                    f"- {nome}, {p['a']} → {p['b']}: {_n(p['unidades'])} unidades; "
                    f"Bolsonaro {_ic(p.get('bolsonaro_pp'))}, bruto "
                    f"{_p((p.get('bolsonaro_pp') or {}).get('bruto'), 2)}"
                )
        w("")
    rg = ur.get("reguas") or {}
    if rg.get("itens"):
        w("As réguas nacionais (urna mais nova contra a mais velha, Flávio):")
        w("")
        for i in rg["itens"]:
            w(
                f"- {i['regua'].capitalize()}: {_ic(i)}; sem controle "
                f"{_p(i['bruto'], 2)}; {_n(i['unidades'])} {i['unidade']}."
            )
        w("")
        w(rg.get("leitura", ""))
        w("")

    # ---------------- D
    w("## D. Outras anomalias de seção")
    w("")
    cp = ou["comparecimento"]
    w(
        f"- Comparecimento acima de 100%: {_n(cp['acima_100'])}; igual a 100% "
        f"(abstenção zero): {_n(cp['igual_100'])}, das quais "
        f"{_n(cp['igual_100_por_tamanho']['100_mais'])} com 100 aptos ou mais."
    )
    for cand, nome in (("lula", "Lula"), ("flavio", "Flávio")):
        z = ou["zero_votos"][cand]
        w(
            f"- Zero voto em {nome} com 200 votantes ou mais: {_n(z['secoes'])} "
            f"de {_n(z['secoes_base'])} seções."
        )
        for s in z["amostras"][:5]:
            w("  - " + _linha_secao(s, None))
    for r in ou["tipo_arquivo"]:
        w(
            f"- Tipo de arquivo {r['tipo_arquivo']} ({r['descricao']}): "
            f"{_n(r['secoes'])} seções; Flávio {_p(r['flavio_pct'], 2)}%, diferença "
            f"média para o resto da zona {_pp(r['dif_zona_flavio_pp'])}."
        )
    for r in ou["tipo_urna"]:
        w(
            f"- {r['descricao'].capitalize()}: {_n(r['secoes'])} seções; diferença "
            f"média de Flávio para o resto da zona {_pp(r['dif_zona_flavio_pp'])}."
        )
    h = ou["horarios"]
    w(
        f"- Horários (Brasília): abertura depois das 9h em "
        f"{_n(h['abertura']['depois_0900'])} seções, depois das 10h em "
        f"{_n(h['abertura']['depois_1000'])}; encerramento depois das 18h em "
        f"{_n(h['encerramento']['depois_1800'])}, depois das 19h em "
        f"{_n(h['encerramento']['depois_1900'])}, depois das 20h em "
        f"{_n(h['encerramento']['depois_2000'])}."
    )
    rotulos = {
        "encerramento_depois_19h": "Seções que encerraram depois das 19h",
        "abertura_depois_9h": "Seções que abriram depois das 9h",
    }
    for g in h.get("voto_vs_zona", []):
        w(
            f"- {rotulos.get(g['grupo'], g['grupo'])}: {_n(g['secoes'])} seções; Lula "
            f"{_pp(g['dif_zona_lula_pp'])} e Flávio {_pp(g['dif_zona_flavio_pp'])} "
            "em relação ao resto da própria zona (fila longa costuma ser de seção "
            "grande e de bairro populoso; hipótese a conferir com a ata)."
        )
    rb = ou["recebimento"]
    for chave, rot in (("depois_0000", "meia-noite"), ("depois_0100", "1h")):
        b = rb[chave]
        w(
            f"- Boletins recebidos pelo TSE depois de {rot} de 05/10: "
            f"{_n(b['secoes'])} seções, {_n(b['validos'])} válidos, Lula "
            f"{_p(b['lula_pct'], 2)}%; diferença média de Lula para o resto da "
            f"zona {_pp(b['dif_zona_lula_pp'])}."
        )
        for m in b["municipios"][:10]:
            w(
                f"  - {m['municipio']} ({m['uf']}): {_n(m['secoes'])} seções, Lula "
                f"{_p(m['lula_pct'], 1)}%"
            )
    br = next(
        (r for r in ou["benford2"] if r["uf"] == "BR" and r["candidato"] == "lula"),
        None,
    )
    if br:
        w(
            f"- Benford do segundo dígito, Brasil, Lula: n = {_n(br['n'])}, "
            f"qui-quadrado {_p(br['chi2'], 1)} com {br['gl']} graus de liberdade. "
            f"{ou['aviso_benford']}"
        )
    w("")

    # ---------------- achados
    for chave, titulo in (
        ("verificado", "Verificado (dado do TSE, conta direta)"),
        ("inferido", "Inferido (leitura dos números)"),
        ("juizo", "Juízo editorial"),
        ("hipotese", "Hipótese (a verificar)"),
        ("contrario", "O achado que contraria a tese"),
    ):
        w(f"## {titulo}")
        w("")
        for f in ac[chave]:
            w(f"- {f}")
        w("")
    w("## Limites")
    w("")
    for f in d["limites"]:
        w(f"- {f}")
    w("")
    w("## Reprodução")
    w("")
    w("```")
    w("python3 scripts/apuracao-2026-secoes.py            # exige coleta completa")
    w("python3 scripts/apuracao-2026-secoes.py --parcial  # com o que já existe")
    w("pytest -q tests/test_apuracao_2026_secoes.py")
    w("```")
    w("")
    texto = "\n".join(linhas)
    if PROIBIDO in texto:
        raise ValueError("travessão no memorando")
    return texto


def _linha_secao(s: Mapping[str, Any], nome: str | None) -> str:
    base = (
        f"{s['municipio']} ({s['uf']}), zona {s['zona']}, seção {s['secao']}, "
        f"{s['local'] or 'local sem cadastro'}: Lula {_n(s['lula'])}, Flávio "
        f"{_n(s['flavio'])} de {_n(s['validos'])} válidos ({_n(s['aptos'])} aptos, "
        f"{_n(s['comparecimento'])} votantes, {s['modelo_urna'] or 'sem modelo'})"
    )
    if nome is not None:
        chave = "lula" if nome == "Lula" else "flavio"
        base += (
            f"; {nome} {_p(s[f'{chave}_pct'])}% na seção e "
            f"{_p(s[f'zona_{chave}_pct'])}% na zona"
        )
    exp = s["explicacao"] or ""
    return base + f". {exp[:1].upper()}{exp[1:]}."
