"""Texto do bloco "Como o eleitor foi habilitado", gerado de ``biometria.json``."""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import inteiro, num, p
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
        f"turnos é de {pp(dmax['ano_nascimento_delta_pp'])} ({nome_uf(dmax['uf'])})."
    ) + p(
        "Com mudança tão pequena entre os turnos, a parcela é característica do lugar, não do dia.",
        "inferencia",
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
    a13, a22 = lin[("2t", "UE2013")], lin[("2t", "UE2022")]
    troca = next(
        (x for x in M["mesma_secao_troca"] if x["grupo"].startswith("antiga no 1T")),
        None,
    )
    h = _p(
        f"O modelo da urna pesa. No 2º turno, a UE2013 habilitou {pct(a13['ano_nascimento_pct'])} "
        f"por ano de nascimento e a UE2022, {pct(a22['ano_nascimento_pct'])}. Dentro do mesmo "
        f"município, a urna antiga (UE2013 e UE2015) fica {pp(d2['dif_ano_nascimento_antiga_menos_nova_pp'])} "
        f"acima da nova (erro-padrão {num(d2['ep_pp'], 2)}; {inteiro(d2['municipios'])} municípios "
        f"com os dois tipos). O mesmo aparece no 1º turno."
    )
    h += p(
        "A leitura provável é o leitor biométrico mais antigo reconhecendo menos digitais; só o "
        "log confirma.",
        "hipotese",
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


def _fr(v: dict) -> str:
    return (
        f"{inteiro(v['n_sinal_total'])} seções; fatia de Flávio "
        f"{pp(v.get('dif_fatia_flavio_vs_vizinhas_pp'))} contra as vizinhas do mesmo município "
        f"(erro-padrão {num(v.get('ep_fatia_flavio_vs_vizinhas_pp'), 2)}) e diferença em diferenças "
        f"contra o 1º turno de {pp(v.get('did_fatia_flavio_pp'))} (erro-padrão aproximado, entre "
        f"municípios, {num(v.get('ep_did_fatia_flavio_pp'), 2)}; n {inteiro(v['n_did'])})"
    )


def _no_1t(v: dict) -> float:
    """Diferença contra as vizinhas implícita no 1º turno: a de hoje menos a diferença em diferenças."""
    return v["dif_fatia_flavio_vs_vizinhas_pp"] - v["did_fatia_flavio_pp"]


def _duas_reguas(a: dict, s: dict, sal: dict | None, V: dict | None) -> str:
    """Compara com o bloco de sinais (secoes_voto.json), que usa outra régua e outra definição de salto."""
    sv = {x["sinal"]: x for x in (V or {}).get("sinais", [])}
    an, sb, sl = (
        sv.get("sinal_ano_nasc"),
        sv.get("sinal_sem_bio"),
        sv.get("sinal_salto_bio"),
    )
    if not (an and sb):
        return ""

    def dentro(v: dict) -> bool:
        return (
            abs(v["dif_fatia_flavio_vs_vizinhas_pp"])
            <= v["ep_fatia_flavio_vs_vizinhas_pp"]
        )

    mesmo = (a["dif_fatia_flavio_vs_vizinhas_pp"] > 0) == (
        an["dif_fatia_flavio_vs_vizinhas_pp"] > 0
    )
    h = (
        "Os mesmos sinais aparecem com contagens um pouco diferentes no bloco de sinais mais abaixo: lá a "
        "régua é a mediana do município no 1º turno, como na API do coletor; aqui, a mediana do próprio turno. "
        f"Para sem cadastro, as duas réguas coincidem: {pp(s['dif_fatia_flavio_vs_vizinhas_pp'])} aqui contra "
        f"{pp(sb['dif_fatia_flavio_vs_vizinhas_pp'])} lá, e {pp(s['did_fatia_flavio_pp'])} contra "
        f"{pp(sb['did_fatia_flavio_pp'])} em diferença em diferenças. Para ano de nascimento, "
        + ("o sinal coincide" if mesmo else "o sinal difere")
        + f": {pp(a['dif_fatia_flavio_vs_vizinhas_pp'])} aqui ({inteiro(a['n_sinal_total'])} seções) contra "
        f"{pp(an['dif_fatia_flavio_vs_vizinhas_pp'])} lá ({inteiro(an['n_sinal_total'])})"
        + (", ambos dentro de um erro-padrão" if dentro(a) and dentro(an) else "")
        + f"; em diferença em diferenças, {pp(a['did_fatia_flavio_pp'])} contra {pp(an['did_fatia_flavio_pp'])}."
    )
    if sal and sl and sl.get("did_fatia_flavio_pp") is not None:
        h += (
            " O salto também tem definição diferente: aqui, só o ano de nascimento, 5 pp ou mais acima da própria "
            f"seção no 1º turno ({inteiro(sal['n_sinal_total'])} seções, {pp(sal['dif_fatia_flavio_vs_vizinhas_pp'])} "
            f"contra as vizinhas, {pp(sal['did_fatia_flavio_pp'])} em diferença em diferenças); na figura de diferença "
            f"em diferenças mais abaixo, {sl['descricao']} ({inteiro(sl['n_did'])} seções, "
            f"{pp(sl['dif_fatia_flavio_vs_vizinhas_pp'])} e {pp(sl['did_fatia_flavio_pp'])})."
        )
    return p(h, "verificado")


def voto(B: dict, V: dict | None = None) -> str:
    g = {v["grupo"]: v for v in B["voto"]}
    a, s = g["ano_nascimento_alto"], g["sem_cadastro_alto"]
    sal = g.get("ano_nascimento_salto")
    grupos = [x for x in (a, s, sal) if x]
    maior = max(abs(x["dif_fatia_flavio_vs_vizinhas_pp"]) for x in grupos)
    h = p(
        f"Voto. Ano de nascimento alto (10% ou mais e o dobro da mediana do município): {_fr(a)}. "
        f"Sem cadastro alto, mesma regra: {_fr(s)}."
        + (
            f" Salto do ano de nascimento (5 pp ou mais acima da própria seção no 1º turno): {_fr(sal)}."
            if sal
            else ""
        ),
        "verificado",
    )
    s1, a1 = _no_1t(s), _no_1t(a)
    parte = 100 * s1 / s["dif_fatia_flavio_vs_vizinhas_pp"]
    virou = (a1 > 0) != (a["dif_fatia_flavio_vs_vizinhas_pp"] > 0)
    h += p(
        f"Contra as vizinhas, as diferenças vão até {num(maior, 2)} pp em módulo e em boa parte já existiam "
        f"no 1º turno: no sem cadastro, {pp(s['dif_fatia_flavio_vs_vizinhas_pp'])} hoje menos "
        f"{pp(s['did_fatia_flavio_pp'])} de diferença em diferenças deixa cerca de {pp(s1)} no 1º turno, "
        f"{num(parte, 0)}% da de hoje. No ano de nascimento alto, {pp(a['dif_fatia_flavio_vs_vizinhas_pp'])} hoje e "
        f"{pp(a['did_fatia_flavio_pp'])} de diferença em diferenças deixam cerca de {pp(a1)} no 1º turno"
        + (": o sinal virou entre os turnos." if virou else ".")
        + " A conta é aproximada, porque as duas medidas não usam os mesmos pesos. Parcela alta pede "
        "explicação, não prova irregularidade.",
        "inferencia",
    )
    return h + _duas_reguas(a, s, sal, V)
