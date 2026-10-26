"""Memorando da habilitação do eleitor, gerado só dos números de ``biometria.json``."""

from __future__ import annotations

from typing import Any

from .secoes_texto import _n


def memorando(B: dict[str, Any]) -> str:
    t1, t2 = B["totais"]["1t"], B["totais"]["2t"]
    L: list[str] = []
    a = L.append
    a("# Como o eleitor foi habilitado: biometria, ano de nascimento e sem cadastro")
    a("")
    a(f"> {B['rotulo']}")
    a("")
    a(
        f"Gerado em {B['gerado_em']} a partir dos BUs de todas as seções dos dois turnos."
    )
    a("")
    a("## Totais")
    a("")
    a(
        "| turno | comparecimento com categoria | biometria | ano de nascimento | sem cadastro | fecha |"
    )
    a("|---|---|---|---|---|---|")
    for nome, t in (("1º turno", t1), ("2º turno", t2)):
        a(
            f"| {nome} | {_n(t['comparecimento_com_categoria'])} | {_n(t['biometria'])} "
            f"({_n(t['biometria_pct'])}%) | {_n(t['ano_nascimento'])} "
            f"({_n(t['ano_nascimento_pct'])}%) | {_n(t['sem_cadastro'])} "
            f"({_n(t['sem_cadastro_pct'])}%) | {_n(t['identidade_fecha'])} |"
        )
    a("")
    ex = B.get("exterior_log") or {}
    e1, e2 = ex.get("1t") or {}, ex.get("2t") or {}
    mods = ", ".join(f"{k} {_n(v)}" for k, v in t2["exterior_modelos"].items())
    a(
        "Quatro situações: biometria reconhecida; ano de nascimento (biometria "
        "cadastrada e não reconhecida, Brasil); sem biometria cadastrada (Brasil); e "
        "exterior, onde não há conferência biométrica."
    )
    a("")
    a(
        f"Exterior: {_n(t2['exterior_secoes'])} urnas ({mods}) e "
        f"{_n(t2['exterior_comparecimento_sem_categoria'])} votantes no 2T "
        f"({_n(t1['exterior_comparecimento_sem_categoria'])} no 1T); o BU não publica as "
        f"categorias. Pelo log das urnas: {_n(e2.get('sem_biometria'))} habilitações sem "
        f"biometria e {_n(e2.get('biometrica'))} biométricas no 2T "
        f"({_n(e1.get('sem_biometria'))} e {_n(e1.get('biometrica'))} no 1T). "
        f"{ex.get('nota', '')}"
    )
    a("")
    a(
        f"Sistema de apuração no Brasil: {_n(t1['sistema_apuracao_secoes_brasil'])} seções "
        f"no 1T e {_n(t2['sistema_apuracao_secoes_brasil'])} no 2T, sem categorias. "
        f"Comparecimento total: {_n(t2['comparecimento_total'])} (2T) e "
        f"{_n(t1['comparecimento_total'])} (1T)."
    )
    a("")
    a("## Por UF (ano de nascimento, % do comparecimento)")
    a("")
    a("| UF | 2T | 1T | dif. pp | sem cadastro 2T |")
    a("|---|---|---|---|---|")
    for u in B["por_uf"]:
        a(
            f"| {u['uf']} | {_n(u['ano_nascimento_pct_2t'])} | {_n(u['ano_nascimento_pct_1t'])} | "
            f"{_n(u['ano_nascimento_delta_pp'])} | {_n(u['sem_cadastro_pct_2t'])} |"
        )
    a("")
    M = B["modelos"]
    a("## Modelo de urna")
    a("")
    a("| turno | modelo | seções | ano de nascimento | mediana por seção |")
    a("|---|---|---|---|---|")
    for x in M["por_modelo"]:
        a(
            f"| {x['turno']} | {x['modelo']} | {_n(x['secoes'])} | {_n(x['ano_nascimento_pct'])}% | "
            f"{_n(x['ano_nascimento_p50_secao'])}% |"
        )
    a("")
    for k, d in M["dentro_do_municipio"].items():
        a(
            f"- {k}: dentro do mesmo município, urna antiga (UE2013/2015) menos nova "
            f"(UE2020/2022): {_n(d['dif_ano_nascimento_antiga_menos_nova_pp'])} pp (ep "
            f"{_n(d['ep_pp'])}; {_n(d['municipios'])} municípios, {_n(d['secoes_antigas'])} "
            f"seções antigas contra {_n(d['secoes_novas'])} novas)."
        )
    for x in M["mesma_secao_troca"]:
        a(
            f"- Mesma seção, {x['grupo']}: {_n(x['secoes'])} seções, variação média do ano "
            f"de nascimento {_n(x['variacao_ano_nascimento_media_pp'])} pp."
        )
    a("")
    mu = B["municipios"]
    a(f"## Municípios (aptos ≥ 20.000; {_n(mu['n_municipios'])} municípios)")
    a("")
    a("| UF | município | ano de nascimento 2T | 1T | sem cadastro 2T |")
    a("|---|---|---|---|---|")
    for m in mu["maior_ano_nascimento"][:15]:
        a(
            f"| {m['uf']} | {m['nome']} | {_n(m['ano_nascimento_pct_2t'])}% | "
            f"{_n(m['ano_nascimento_pct_1t'])}% | {_n(m['sem_cadastro_pct_2t'])}% |"
        )
    a("")
    a("## Relação com o voto (dentro do município)")
    a("")
    for v in B["voto"]:
        if "dif_fatia_flavio_vs_vizinhas_pp" in v:
            a(
                f"- {v['descricao']}: {_n(v['n_sinal_total'])} seções; fatia de Flávio "
                f"{_n(v['dif_fatia_flavio_vs_vizinhas_pp'])} pp contra as vizinhas (n "
                f"{_n(v['n_sinal_comparavel'])} contra {_n(v['n_vizinhas'])}); diferença em "
                f"diferenças contra o 1T {_n(v.get('did_fatia_flavio_pp'))} pp (ep "
                f"{_n(v.get('ep_did_fatia_flavio_pp'))}, n {_n(v['n_did'])})."
            )
        else:
            a(f"- {v['descricao']}: {_n(v['n_sinal_total'])} seções, n abaixo de 20.")
    a("")
    a(
        "Limites: o BU não diz quem votou nem por que o leitor falhou; a ata e o log da "
        "urna separam leitor, digital gasta e liberação indevida."
    )
    a("")
    return "\n".join(L)
