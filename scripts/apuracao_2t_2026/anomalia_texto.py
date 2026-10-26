"""Memorando da mistura gaussiana dos dois turnos (``anomalia_ml.md``).

Gerado do próprio JSON, sem número digitado à mão. Português corrente, sem
travessão; o rótulo da casa abre e fecha o texto.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from apuracao_2026.secoes_base import num
from apuracao_2026.secoes_clusters_diag import dec

ROTULO = (
    "Atipicidade estatística não é irregularidade; o grupo pede explicação, "
    "não prova nada."
)


def n0(v: float | int | None) -> str:
    return "sem dado" if v is None else num(float(v), 0)


def n1(v: float | None, casas: int = 1) -> str:
    return "sem dado" if v is None else num(float(v), casas)


def s1(v: float | None, casas: int = 1) -> str:
    if v is None:
        return "sem dado"
    return ("+" if v >= 0 else "−") + num(abs(float(v)), casas)


def ic(v: Sequence[float | None] | None) -> str:
    if not v or v[0] is None or v[1] is None:
        return "sem IC"
    return f"de {s1(v[0], 2)} a {s1(v[1], 2)}"


def _degeneradas_bic(bic: Sequence[Mapping[str, Any]]) -> str:
    d = [b for b in bic if b.get("partidas_degeneradas")]
    if not d:
        return ""
    return (
        " Partidas degeneradas (um componente colado num valor exato de uma fração,"
        " como zero branco no 2T, com variância no piso de regularização) ficaram fora"
        " da escolha: "
        + "; ".join(
            f"k = {b['k']}, {b['partidas_degeneradas']} de {b['partidas']}" for b in d
        )
        + "."
    )


def _tabela(cab: Sequence[str], linhas: Sequence[Sequence[str]]) -> list[str]:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    out += ["| " + " | ".join(linha) + " |" for linha in linhas]
    return out


def _grupo(c: Mapping[str, Any], anom: int) -> str:
    d = c["centro_delta_pp"]
    marca = " **(grupo atípico)**" if c["id"] == anom else ""
    return (
        f"- Grupo {c['id']}{marca}: {n0(c['secoes'])} seções ({n1(c['pct_secoes'], 2)}%),"
        f" aptos médio {n1(c['aptos_medio'])}. {c['rotulo'][:1].upper()}"
        f"{c['rotulo'][1:]}. Em diferenças: comparecimento {s1(d['comp'])},"
        f" Lula {s1(d['lula'])}, Flávio {s1(d['flavio'])}, brancos {s1(d['brancos'])},"
        f" nulos {s1(d['nulos'])} pontos do eleitorado; terceira via no 1T"
        f" {n1(d['terceira1_pp'])}%. Fatia de Flávio entre os dois: {n1(c['fatia_f1'])}%"
        f" no 1T, {n1(c['fatia_f2'])}% no 2T."
    )


def _amostra(x: Mapping[str, Any]) -> str:
    return (
        f"- {x['uf']}, {x['municipio'] or x['mun']}, zona {x['zona']}, seção"
        f" {x['secao']}: {x['aptos_2t']} aptos; brancos e nulos {x['brancos_1t']} +"
        f" {x['nulos_1t']} no 1T e {x['brancos_2t']} + {x['nulos_2t']} no 2T; Lula"
        f" {x['lula_2t']} e Flávio {x['flavio_2t']} no 2T. Pela régua da casa:"
        f" {x['explicacao_provavel'] or 'sem dado'}."
    )


def memorando(A: Mapping[str, Any]) -> str:
    u = A["universo"]
    ex = u["excluidas"]
    cd = u["comparecimento_divergente"]
    aj = A["ajuste"]
    dg = aj["diagnostico_convergencia"]
    k = A["k_escolhido"]
    comps = A["componentes"]
    ma = A["mais_anomalo"]
    anom = ma["id"]
    ca = next(c for c in comps if c["id"] == anom)
    v = ma["voto"]
    eq = A["features"]["equivalencia_afim_verificacao"]
    linhas = [
        "# Grupos de seções nos dois turnos de 2026 (mistura gaussiana)",
        "",
        f"**{ROTULO}**",
        "",
        f"Gerado em {A['gerado_em']} por `scripts/apuracao-2t-2026-anomalia.py`."
        + (
            f" **Rascunho em amostra de {n0(A['rascunho']['amostra'])} seções.**"
            if A.get("rascunho")
            else ""
        ),
        "",
        "## Universo",
        "",
        f"- {n0(u['secoes'])} seções do Brasil com boletim de urna nos dois turnos e"
        f" pelo menos {u['aptos_min']} aptos em ambos.",
        f"- Fora: {n0(ex['exterior'])} do exterior (abstenção muito acima da média formaria"
        f" um grupo só com elas), {n0(ex['sem_par'])} sem boletim em um dos turnos e"
        f" {n0(ex['aptos_menor_30'])} com menos de 30 aptos em algum turno"
        + (f"; {n0(ex['outros'])} por outros motivos" if ex["outros"] else "")
        + ".",
        f"- Comparecimento implícito (soma dos votos de presidente) contra o do BU:"
        f" diverge em {n0(cd['secoes'])} seções"
        + (
            "; "
            + "; ".join(
                f"{e['uf']} {e['mun']} zona {e['zona']} seção {e['secao']}"
                f" ({e['votos']} votos, comparecimento do BU {e['comparecimento_bu']})"
                for t in ("turno1", "turno2")
                for e in cd[t]["exemplos"]
            )
            if cd["secoes"]
            else ""
        )
        + ". A diferença não muda as features.",
        "",
        "## O espaço",
        "",
        "Nove frações do eleitorado do próprio turno, em pontos percentuais: Lula,"
        " Flávio, outros, brancos e nulos no 1º turno; Lula, Flávio, brancos e nulos no"
        " 2º. Abstenção e comparecimento ficam implícitos. Cada coluna é padronizada"
        " (média zero, desvio um entre seções).",
        "",
        A["features"]["equivalencia_afim"]
        + f" Conferência na amostra da escolha de k, com k = {k}: índice de Rand"
        f" ajustado de {n1(eq['ari_particoes'], 4)} entre as partições ajustadas nos dois"
        f" enquadramentos (melhor de 16 partidas em cada um) e diferença de"
        f" {s1(eq['diferenca_ajustada'], 6)} na log-verossimilhança média, já descontado"
        " o determinante da mudança de coordenadas.",
        "",
        "## Número de grupos",
        "",
        f"BIC e ICL para k = 2 a 10 na amostra estratificada por UF de"
        f" {n0(A['amostra_bic']['secoes'])} seções (semente {A['amostra_bic']['semente']}),"
        " oito sementes e duas inicializações por k, uma partida cada:",
        "",
        *_tabela(
            ["k", "BIC", "ICL", "log-veross. média", "iterações", "convergiu"],
            [
                [
                    str(b["k"]),
                    n0(b["bic"]),
                    n0(b["icl"]),
                    n1(b["loglik_media"], 4),
                    str(b["iteracoes"]),
                    "sim" if b["convergiu"] else "não",
                ]
                for b in A["bic"]
            ],
        ),
        "",
        "Quedas do BIC, em % da queda total: "
        + "; ".join(
            f"{q['de']} para {q['para']}, {n1(q['pct_da_total'], 2)}%"
            for q in A["quedas_bic"]
        )
        + ".",
        "",
        f"Regra declarada: {A['regra_declarada']}. Aplicada: {A['regra']}."
        f" Joelho do BIC: {A['k_joelho_bic'] if A['k_joelho_bic'] is not None else 'nenhum'};"
        f" menor ICL: k = {A['k_min_icl']}. **k* = {k}.**"
        + (
            f" O ICL, que penaliza grupos sobrepostos, é mínimo em k = {A['k_min_icl']}:"
            " os grupos se sobrepõem e a mistura descreve regiões de uma nuvem"
            " contínua, não aglomerados separados."
            if A["k_min_icl"] < k
            else ""
        )
        + _degeneradas_bic(A["bic"]),
        "",
        "## Convergência",
        "",
        dg["frase"]
        + f" A partida escolhida (semente {aj['random_state']}, inicialização"
        f" {aj['init']}) convergiu em {aj['iteracoes_partida']} iterações com tolerância"
        f" {dec(aj['tol_partidas'])} e teto de {n0(aj['max_iter_partidas'])} (dobrado até"
        f" {aj['max_dobras']} vezes se preciso); "
        + (
            f"a continuação adotada parou em {aj['iteracoes']} iterações a mais, com"
            f" tolerância {dec(aj['tol'])}."
            if aj["continuacao_adotada"]
            else "a continuação não mudou o ajuste publicado."
        ),
        "",
        "## k-means como contraste",
        "",
        *_tabela(
            ["k", "silhueta (níveis)", "silhueta (níveis e deltas)"],
            [
                [str(a["k"]), n1(a["silhueta"], 3), n1(b["silhueta"], 3)]
                for a, b in zip(
                    A["kmeans"]["niveis"], A["kmeans"]["niveis_e_deltas"], strict=True
                )
            ],
        ),
        "",
        f"Índice de Rand ajustado entre o k-means com k = {k} e a mistura:"
        f" {n1(A['kmeans']['ari_com_mistura_k_estrela']['niveis'], 3)} nos níveis e"
        f" {n1(A['kmeans']['ari_com_mistura_k_estrela']['niveis_e_deltas'], 3)} nos níveis"
        " e deltas. O k-means não é invariante à troca de coordenadas; a mistura é o"
        " modelo principal.",
        "",
        "## Os grupos",
        "",
        "Ordem por Lula no 2º turno (% do eleitorado) crescente. Centros pela média das"
        " seções de cada grupo.",
        "",
        *[_grupo(c, anom) for c in comps],
        "",
        "## O grupo atípico",
        "",
        f"Grupo {anom}: {ma['criterio']} Segundo colocado: grupo {ma['segundo']['id']},"
        f" {ma['segundo']['diferenca_postos']} posto(s) atrás.",
        "",
        f"- {n0(ca['secoes'])} seções ({n1(ca['pct_secoes'], 2)}%), aptos médio"
        f" {n1(ca['aptos_medio'])} contra {n1(A['pais']['aptos_medio'])} no país;"
        f" seções com menos de 100 aptos: {n1(ca['pequenas_pct'])}% contra"
        f" {n1(A['pais']['pequenas_pct'])}%.",
        "- Regiões: "
        + ", ".join(
            f"{r['regiao']} {n1(r['pct_do_cluster'])}% do grupo"
            f" ({n1(r['pct_da_regiao'], 2)}% da região)"
            for r in ca["regioes"]
        )
        + ".",
        "- Modelo da urna: "
        + ", ".join(
            f"{m['modelo']} {n1(m['pct_do_cluster'])}%" for m in ca["modelo_urna"][:4]
        )
        + ".",
        "- Sinais existentes, no grupo contra o país: "
        + "; ".join(
            f"{s['nome']} {n1(s['pct_grupo'], 2)}% contra {n1(s['pct_pais'], 2)}%"
            for s in ma["seis_sinais"]
        )
        + f"; mudança de local {n1(ca['sinais']['mudanca_pct'], 2)}% contra"
        f" {n1(A['sinais_pais']['mudanca_pct'], 2)}%.",
        (
            f"- Voto: a fatia de Flávio entre os dois no 2T fica"
            f" {s1(v.get('fatia_f2_vs_vizinhas_pp'), 2)} pontos contra as vizinhas do"
            f" mesmo município (IC 95% {ic(v.get('ic95'))}; {n0(v['n'])} seções do grupo,"
            f" {n0(v['n_vizinhas'])} vizinhas, {n0(v['n_municipios'])} municípios). Contra"
            f" o 1T, a diferença em diferenças é {s1(v.get('did_vs_1t_pp'), 2)} pontos"
            f" (IC 95% {ic(v.get('ic95_did'))}). {v['nota'][:1].upper()}{v['nota'][1:]}."
            if not v.get("insuficiente")
            else "- Voto: menos de 20 seções comparáveis; sem estimativa."
        ),
        "",
        "Seções do grupo com menor densidade (as 50 estão no JSON, com o link do"
        " Politize-se):",
        "",
        *[_amostra(x) for x in ma["amostras"][:5]],
        "",
        "## O que a mistura não separa",
        "",
        f"Entre os {k} grupos, o V de Cramér com a região é {n1(A['cramer_v_regiao'], 3)};"
        f" com a UF, {n1(A['cramer_v_uf'], 3)}; com o modelo da urna,"
        f" {n1(A['cramer_v_modelo'], 3)}; com a faixa de aptos,"
        f" {n1(A['cramer_v_tamanho'], 3)}. Os grupos de voto seguem a geografia política"
        " do país; o modelo da urna quase não separa nada.",
        "",
        ma["leitura"],
        "",
        ma["conclusao"],
        "",
        "UFs em que o grupo atípico pesa mais: "
        + "; ".join(
            f"{u['uf']} {n1(u['pct_da_uf'], 2)}% das seções ({n1(u['razao'], 1)} vezes o"
            " país)"
            for u in ma["contra"]["ufs_mais_pesadas"]
        )
        + ". Por faixa de aptos: "
        + "; ".join(
            f"{t['tamanho']}, {n1(t['pct_da_faixa'], 2)}% ({n1(t['razao'], 1)} vezes)"
            for t in ma["contra"]["tamanho"]
        )
        + ".",
        "",
        "## Limites",
        "",
        *[f"- {x}" for x in A["limites"]],
        "",
        f"**{ROTULO}**",
        "",
    ]
    return "\n".join(linhas)
