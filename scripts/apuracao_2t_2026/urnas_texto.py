"""Texto de `urnas.md`: fontes de 2022, o que os dados de 2026 mostram e os limites."""

from __future__ import annotations

from .urnas_analise import CLASSES, ROTULO_URNAS, descrever_repetidos


def _n(x) -> str:
    if x is None:
        return "sem dado"
    if isinstance(x, float):
        return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{x:,}".replace(",", ".")


def _ic(d: dict) -> str:
    if not d or not d.get("n"):
        return "sem seções comparáveis"
    ic = d.get("ic95_pp")
    faixa = f", IC95 {_n(ic[0])} a {_n(ic[1])}" if ic else ""
    return f"{_n(d['media_pp'])} pp (n = {_n(d['n'])}{faixa})"


def _por_modelo(t: dict) -> str:
    return "; ".join(
        f"{m} {_n(v.get('id_do_bu_no_log', 0))} de {_n(v['secoes'])}"
        for m, v in t["id_no_log"]["por_modelo"].items()
        if m.startswith("UE")
    )


def _turno(nome: str, t: dict) -> list[str]:
    rep = t["repetidos"]
    out = [
        f"### {nome}",
        "",
        f"- Seções com BU lido: {_n(t['cobertura']['secoes_com_bu'])} de {_n(t['cobertura']['secoes_principais'])} seções principais do catálogo ({_n(t['cobertura']['pct'])}%).",
        "- Modelos: "
        + "; ".join(
            f"{m['rotulo']} {_n(m['secoes'])} ({_n(m['pct'])}%)"
            for m in t["modelos"]["modelo"]
        )
        + ".",
        "- Tipo de urna no BU: "
        + "; ".join(
            f"{m['rotulo']} {_n(m['secoes'])}" for m in t["modelos"]["tipo_urna"]
        )
        + ".",
        f"- IDs distintos: {_n(rep['ids_distintos'])}. IDs em mais de uma seção: {_n(rep['ids_repetidos'])}, somando {_n(rep['secoes_envolvidas'])} seções.",
    ]
    for k, v in rep["por_classe"].items():
        if v["ids"]:
            out.append(
                f"  - {CLASSES[k]}: {_n(v['ids'])} IDs, {_n(v['secoes'])} seções."
            )
    out.append(
        f"- Sem explicação pela regra: {_n(rep['sem_explicacao_pela_regra'])} IDs."
    )
    log = t["id_no_log"]
    out.append(
        f"- ID do BU ausente das urnas que escreveram o log: {_n(log['id_do_bu_ausente_do_log'])} seções (por tipo de arquivo: {log['ausentes_por_tipo_arquivo'] or 'nenhuma'}); seções cujo log traz o número 67305985 de 2022: {_n(log['secoes_com_id_67305985_no_log'])}."
    )
    cc = t["codigo_carga"]
    out.append(
        f"- Código de carga repetido entre seções: {_n(cc['codigos_repetidos'])} códigos, {_n(cc['secoes'])} seções."
    )
    ca = t["carga"]
    out.append(
        f"- Carga: de {ca['primeira']} a {ca['ultima']}; sem data {_n(ca['sem_data'])}; carga depois do 1º turno {_n(ca['carga_depois_do_1t']['secoes'])}; carga depois da eleição {_n(ca['carga_depois_da_eleicao'])}; carga no dia da eleição {_n(ca['carga_no_dia_da_eleicao']['secoes'])} (por tipo de urna {ca['carga_no_dia_da_eleicao']['por_tipo_urna']}); carga registrada depois do primeiro voto da seção {_n(ca['carga_depois_do_primeiro_voto'])}, das quais sem contingência, reserva ou recarga declarada {_n(ca['carga_depois_do_primeiro_voto_sem_contingencia'])} (a abertura do BU de urna de reserva é a da seção, anterior à carga da reserva); BU com seção diferente do caminho {_n(ca['id_nao_confere_caminho'])}."
    )
    rr = t["resultado_repetidos"]
    if rr["secoes"]:
        out.append(
            f"- Seções com ID repetido, fatia de Flávio contra as vizinhas do município: {_ic(rr['contra_vizinhas'])}."
        )
        if "contra_o_proprio_1t_e_vizinhas" in rr:
            out.append(
                f"- Mesmas seções, variação contra o próprio 1º turno menos a das vizinhas: {_ic(rr['contra_o_proprio_1t_e_vizinhas'])}."
            )
    out.append("")
    return out


def markdown(d: dict) -> str:
    t1, t2, et = d["turnos"]["1t"], d["turnos"]["2t"], d["entre_turnos"]
    did = et["diferenca_em_diferencas"]
    linhas = [
        "# IDs das urnas por seção, 1º e 2º turnos de 2026",
        "",
        f"Gerado em {d['gerado_em']}. Coleta do 2º turno: **{d['estado_coleta_2t']}**. Rótulo de tudo o que segue: {ROTULO_URNAS}.",
        "",
        "Reprodução: `python3 scripts/apuracao-2t-2026-urnas.py` (lê os dois bancos de BUs por seção em modo somente leitura; reexecutável sobre a coleta parcial e a completa).",
        "",
        "## O que se alegou em 2022 e o que o TSE respondeu",
        "",
        "Fontes arquivadas com SHA-256 em `analysis/apuracao_2t_2026/urnas_fontes/fontes.json`.",
        "",
        "- **A alegação** [pl_peticao, poder360_250mil, poder360_pedido]. Em 22/11/2022 a Coligação Pelo Bem do Brasil (PL, PP e Republicanos) pediu ao TSE verificação extraordinária (PetCiv 0601958-94.2022.6.00.0000), com relatório do Instituto Voto Legal. O argumento: nos logs das urnas UE2009, 2010, 2011, 2013 e 2015 o campo que deveria identificar a urna trazia o mesmo número, 67305985, em 59,1% das linhas; seriam 279.336 urnas (a decisão fala em 279.383). Pedia invalidar os votos dessas urnas só no 2º turno. A alegação era de um número genérico repetido no log de todas as urnas antigas, **não** de uma mesma urna votando em várias seções.",
        "- **A resposta** [moraes_despacho, tse_decisao, cnn_area_tecnica, tse_noticia_plenario, agenciabrasil_plenario]. Em 22/11 o ministro Alexandre de Moraes deu 24 horas para incluir o 1º turno; em 23/11 indeferiu a petição por inépcia e falta de indícios, fixou multa de R$ 22.991.544,60 por litigância de má-fé e determinou outras providências; o Plenário confirmou em 15/12/2022. O parecer técnico da Secretaria de Tecnologia da Informação, transcrito na decisão, diz que cada urna tem número interno único (ID Urna), que o código de carga é gerado a partir dele, da seção e da hora da carga, fica gravado no log e consta do BU, e que por isso a urna é identificável independentemente do número interno no log das urnas antigas. As fontes oficiais obtidas não explicam a causa da repetição do 67305985.",
        "- **Checagem com caso real** [aosfatos]. Na seção 511 da 1ª zona de Rio Branco (AC), o BU traz o ID 1103958, o log traz 67305985, e os dois compartilham o mesmo código de carga, mídia, seção, zona e município.",
        "",
        "## O que os BUs e logs de 2026 mostram sobre o mesmo fenômeno",
        "",
        f"- **O número de 2022 não aparece.** Em nenhuma seção de 2026 o log traz 67305985 (1º turno: {_n(t1['id_no_log']['secoes_com_id_67305985_no_log'])}; 2º turno até aqui: {_n(t2['id_no_log']['secoes_com_id_67305985_no_log'])}). Seções em que o número interno do BU escreveu linhas no log, por modelo (1º turno): {_por_modelo(t1)}; (2º turno até aqui): {_por_modelo(t2)}. Nas UE2013 e UE2015, o campo do log que em 2022 trazia o número genérico traz agora o número interno da urna, como nas UE2020 e UE2022.",
        f"- **ID do BU contra o log.** No 1º turno, {_n(t1['id_no_log']['id_do_bu_ausente_do_log'])} seções têm um ID no BU que não escreveu linha no log; por tipo de arquivo {t1['id_no_log']['ausentes_por_tipo_arquivo']} (2 = votação recuperada: o BU sai da mídia da urna que falhou, gravado por outra urna, cujo log é o que se publica). No 2º turno até aqui: {_n(t2['id_no_log']['id_do_bu_ausente_do_log'])}.",
        f"- **Mesma urna em mais de uma seção.** 1º turno: {_n(t1['repetidos']['ids_repetidos'])} ID(s) em {_n(t1['repetidos']['secoes_envolvidas'])} seções ({descrever_repetidos(t1['repetidos'])}); sem explicação pela regra: {_n(t1['repetidos']['sem_explicacao_pela_regra'])}. 2º turno até aqui: {_n(t2['repetidos']['ids_repetidos'])} ID(s) em {_n(t2['repetidos']['secoes_envolvidas'])} seções ({descrever_repetidos(t2['repetidos'])}); sem explicação pela regra: {_n(t2['repetidos']['sem_explicacao_pela_regra'])}. Classe sistema_apuracao: o BU foi emitido pelo sistema de apuração da junta (tipo de arquivo 3 a 6) e o número interno é o do equipamento da junta, não de uma urna que recebeu votos na seção.",
        f"- **Mesma seção, mesma urna?** Das {_n(et['secoes_pareadas'])} seções com BU nos dois turnos, {_n(et['mesma_urna'])} votaram na mesma urna e {_n(et['urna_diferente'])} em urna diferente. Mesma urna com o mesmo código de carga: {_n(et['mesma_urna_mesma_carga'])}; mesma urna com carga diferente (recarga entre turnos): {_n(et['mesma_urna_carga_diferente'])}. Origem das urnas trocadas: {et['trocadas_por_origem_da_urna']}. Tipo da urna no 2º turno entre as trocadas: {et['trocadas_por_tipo_urna_2t']} (1 = urna de seção, 4 = reserva que substituiu a da seção no dia). `urna_sem_bu_no_1t` é urna que não emitiu BU no 1º turno: substituição antes do 2º turno (com carga nova depois de 04/10) ou reserva acionada no dia.",
        f"- **As trocadas votam diferente das vizinhas?** Variação da fatia de Flávio do 1º para o 2º turno, menos a das seções do mesmo município que mantiveram a urna: todas as trocadas {_ic(did['todas_trocadas']['fatia_flavio'])}; reserva ou contingência no 2º turno {_ic(did['trocada_reserva_no_2t']['fatia_flavio'])}; urna de seção diferente da do 1º turno {_ic(did['trocada_urna_de_secao_no_2t']['fatia_flavio'])}. Comparecimento, mesma conta: {_ic(did['todas_trocadas']['comparecimento'])}. {et['nota_did']}",
        f"- **Urnas que mudaram de seção entre os turnos**: {d['ids_em_outra_secao']}.",
        "",
        "## Por turno",
        "",
        *_turno("1º turno (base)", t1),
        *_turno("2º turno", t2),
        "## Regra de classificação dos IDs repetidos",
        "",
        "Para cada número interno presente em mais de uma seção do mesmo turno, testam-se as explicações legítimas nesta ordem: (1) mesmo BU, isto é, seção agregada; (2) BU emitido pelo sistema de apuração (tipo de arquivo 3 a 6); (3) se algum par de seções tem intervalo de votação (primeiro ao último voto, hora local da urna) sobreposto, a mesma urna não poderia estar nas duas: fica sem explicação; (4) contingência, reserva (tipo de urna 3, 4 ou 6) ou recarga (mais de uma carga) com horários disjuntos: troca compatível; (5) horários disjuntos sem nenhuma dessas declarações: sem explicação pela regra. Geografia registrada à parte (mesmo local, zona, município, UF ou UFs diferentes). Comparação de horários entre UFs de fusos diferentes é marcada.",
        "",
        "## Limites",
        "",
        "- Lê os BUs publicados pelo TSE e o resumo das urnas que escreveram o log, feito pelo coletor de BUs; não valida assinatura digital dos arquivos.",
        "- Enquanto a coleta do 2º turno não termina, a ordem de coleta é por UF e os números do 2º turno não representam o país.",
        "- A diferença em diferenças compara seções que trocaram de urna com vizinhas que não trocaram; troca de urna decorre de defeito ou de logística, não de sorteio, e por isso não identifica efeito causal.",
        f"- {ROTULO_URNAS}.",
        "",
    ]
    return "\n".join(linhas)
