"""Texto do bloco "Como o eleitor foi habilitado", gerado de ``biometria.json``."""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import inteiro, num
from apuracao_2026.pagina_fig_base import nome_bonito, pct, pp

from .pagina_fig_turnos_util import nome_uf


def _p(s: str) -> str:
    return f"<p>{s}</p>"


def abertura(B: dict) -> str:
    t1, t2 = B["totais"]["1t"], B["totais"]["2t"]
    ex = (B.get("exterior_log") or {}).get("2t") or {}
    h = _p(
        "O boletim de urna conta, seção por seção, como cada eleitor foi liberado para votar. "
        "São quatro situações: <b>biometria reconhecida</b>; <b>ano de nascimento</b>, eleitor "
        "com biometria cadastrada que o leitor não reconheceu, identificado pelo documento e "
        "liberado pela data de nascimento; <b>sem biometria cadastrada</b>, eleitor que nunca "
        "coletou biometria; e o <b>exterior</b>, onde não há conferência biométrica."
    )
    h += _p(
        f"No 2º turno, {inteiro(t2['biometria'])} votaram com biometria reconhecida "
        f"({pct(t2['biometria_pct'])}), {inteiro(t2['ano_nascimento'])} por ano de nascimento "
        f"({pct(t2['ano_nascimento_pct'])}) e {inteiro(t2['sem_cadastro'])} sem cadastro "
        f"({pct(t2['sem_cadastro_pct'])}). As três somam exatamente o comparecimento com "
        f"categoria, {inteiro(t2['comparecimento_com_categoria'])}. No 1º turno foram "
        f"{pct(t1['biometria_pct'])}, {pct(t1['ano_nascimento_pct'])} e "
        f"{pct(t1['sem_cadastro_pct'])}: o retrato quase não mudou entre os turnos."
    )
    h += _p(
        f"O BU do exterior não publica as categorias. Os logs das "
        f"{inteiro(t2['exterior_secoes'])} urnas do exterior registram "
        f"{inteiro(ex.get('sem_biometria'))} habilitações, todas sem biometria"
        + (
            ", nenhuma biométrica"
            if not ex.get("biometrica")
            else f", e {inteiro(ex.get('biometrica'))} biométricas"
        )
        + ": o TSE não usa identificação biométrica "
        "nas seções do exterior, segundo os próprios logs. No gráfico, essa faixa vem do log, "
        "não do BU."
    )
    return h


def ufs(B: dict) -> str:
    us = sorted(B["por_uf"], key=lambda u: -(u["ano_nascimento_pct_2t"] or 0))
    top = ", ".join(
        f"{nome_uf(u['uf'])} {pct(u['ano_nascimento_pct_2t'])}" for u in us[:5]
    )
    fim = ", ".join(
        f"{nome_uf(u['uf'])} {pct(u['ano_nascimento_pct_2t'])}" for u in us[-3:]
    )
    dmax = max(us, key=lambda u: abs(u["ano_nascimento_delta_pp"] or 0))
    return _p(
        f"Por UF, a parcela por ano de nascimento vai de {fim.split(', ')[-1]} até "
        f"{top.split(', ')[0]}. As maiores: {top}. As menores: {fim}. A maior mudança entre os "
        f"turnos é de {pp(dmax['ano_nascimento_delta_pp'])} ({nome_uf(dmax['uf'])}): a parcela "
        "é característica do lugar, não do dia."
    )


def municipios(B: dict) -> str:
    M = B["municipios"]
    m0 = M["maior_ano_nascimento"][0]
    s0 = M["maior_sem_cadastro"][0]
    return _p(
        f"Entre os {inteiro(M['n_municipios'])} municípios com 20 mil aptos ou mais, a mediana "
        f"por ano de nascimento é {pct(M['mediana_ano_nascimento_pct_2t'])}. A maior é "
        f"{escape(nome_bonito(m0['nome']))} ({m0['uf']}), {pct(m0['ano_nascimento_pct_2t'])} no "
        f"2º turno e {pct(m0['ano_nascimento_pct_1t'])} no 1º. Sem cadastro, o extremo é "
        f"{escape(nome_bonito(s0['nome']))} ({s0['uf']}), {pct(s0['sem_cadastro_pct_2t'])}. "
        "Os mesmos municípios lideram nos dois turnos."
    )


def histograma(B: dict) -> str:
    h1, h2 = (
        B["histograma_ano_nascimento"]["turnos"]["1t"],
        B["histograma_ano_nascimento"]["turnos"]["2t"],
    )
    return _p(
        f"Seção por seção, a mediana é {pct(h2['p50'])} no 2º turno ({pct(h1['p50'])} no 1º) e o "
        f"90º percentil {pct(h2['p90'])}. {inteiro(h2['secoes_10_mais'])} seções passam de 10%, "
        f"{inteiro(h2['secoes_30_mais'])} de 30% e {inteiro(h2['secoes_50_mais'])} de 50% "
        f"(no 1º turno, {inteiro(h1['secoes_10_mais'])}, {inteiro(h1['secoes_30_mais'])} e "
        f"{inteiro(h1['secoes_50_mais'])})."
    )


def modelos(B: dict) -> str:
    M = B["modelos"]
    d2 = M["dentro_do_municipio"]["2t"]
    lin = {(x["turno"], x["modelo"]): x for x in M["por_modelo"]}
    a13, a22 = lin.get(("2t", "UE2013")), lin.get(("2t", "UE2022"))
    troca = next(
        (x for x in M["mesma_secao_troca"] if x["grupo"].startswith("antiga no 1T")),
        None,
    )
    h = _p(
        f"O modelo da urna pesa. No 2º turno, a UE2013 habilitou {pct(a13['ano_nascimento_pct'])} "
        f"por ano de nascimento e a UE2022, {pct(a22['ano_nascimento_pct'])}. Dentro do mesmo "
        f"município, a urna antiga (UE2013 e UE2015) fica {pp(d2['dif_ano_nascimento_antiga_menos_nova_pp'])} "
        f"acima da nova (erro-padrão {num(d2['ep_pp'], 2)}; {inteiro(d2['municipios'])} municípios "
        f"com os dois tipos). O mesmo aparece no 1º turno. A leitura provável é o leitor "
        "biométrico mais antigo reconhecendo menos digitais, hipótese que só o log confirma."
    )
    if troca and troca["variacao_ano_nascimento_media_pp"] is not None:
        h += _p(
            f"Nas {inteiro(troca['secoes'])} seções que tinham urna antiga no 1º turno e nova no 2º, "
            f"a parcela mudou {pp(troca['variacao_ano_nascimento_media_pp'])} em média."
        )
    elif troca:
        h += _p(
            f"Só {inteiro(troca['secoes'])} seções trocaram de urna antiga para nova entre os "
            "turnos: poucas para medir."
        )
    return h


def voto(B: dict) -> str:
    g = {v["grupo"]: v for v in B["voto"]}
    a, s = g["ano_nascimento_alto"], g["sem_cadastro_alto"]

    def fr(v: dict) -> str:
        return (
            f"{inteiro(v['n_sinal_total'])} seções; fatia de Flávio "
            f"{pp(v.get('dif_fatia_flavio_vs_vizinhas_pp'))} contra as vizinhas do mesmo município "
            f"e diferença em diferenças contra o 1º turno de {pp(v.get('did_fatia_flavio_pp'))} "
            f"(erro-padrão {num(v.get('ep_did_fatia_flavio_pp'), 2)}, n {inteiro(v['n_did'])})"
        )

    return _p(
        f"Voto. Ano de nascimento alto (10% ou mais e o dobro da mediana do município): {fr(a)}. "
        f"Sem cadastro alto: {fr(s)}. São diferenças de menos de dois pontos, em direções opostas, "
        "e quase todas já existiam no 1º turno. Parcela alta pede explicação, não prova "
        "irregularidade."
    )
