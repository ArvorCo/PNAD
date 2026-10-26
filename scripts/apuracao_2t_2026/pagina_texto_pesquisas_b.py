"""Capítulo `pesquisas` (2º turno), parte B: candidatos a explicar a mudança e o que falta explicar.

Tese editorial em `analysis/apuracao_2t_2026/TESE.md`: as pesquisas e a régua de
renda mediram certo até o último campo, e o afastamento comum mede o tamanho da
mudança entre sábado e domingo. Cada candidato sai com o que sustenta e o que
contraria, sem ordem de preferência. Números de `pesquisas_vs_urna.json`; fatos da
noite de `noticias_noite.json`, citados pelo resumo da coleta com veículo e link.
"""

from __future__ import annotations

from html import escape

from . import pagina_texto_noticias as TN
from .pagina_comum import milhoes, nota, num, p, sinal


def s2(x: float) -> str:
    return sinal(x, 2)


def _item(N: dict | None, *partes: str) -> dict | None:
    if not N:
        return None
    return next(
        (i for i in TN.ordenados(N) if all(x in i["resumo"] for x in partes)), None
    )


def _cita(it: dict | None) -> str:
    if not it:
        return ""
    return (
        f"{escape(it['veiculo'])}, {escape(TN.rotulo_hora(it))}: {escape(TN.limpa(it['resumo']))} "
        f'(<a href="{escape(it["url"])}" rel="noopener">fonte</a>)'
    )


def _uf(PV: dict, uf: str) -> dict | None:
    ufs = PV["hipoteses"]["contabilidade_entre_turnos"]["ufs"]
    return next((x for x in ufs if x["uf"] == uf), None)


def candidatos(f: dict, PV: dict, N: dict | None) -> str:
    h = '<h3 id="pesquisas-candidatos">Candidatos a explicar a mudança</h3>'
    h += nota(
        "juizo",
        "Seis candidatos, sem ordem de preferência. Cada um sai com o que o dado sustenta e com o que o "
        "contraria; nenhum foi medido por candidato, e mais de um pode ter agido ao mesmo tempo.",
    )
    # 1. comparecimento
    h += "<h4>1. Comparecimento recorde e diferenciado</h4>"
    cnn = _item(N, "menor desde")
    h += p(
        f"A abstenção foi de {num(f['abst_2t'], 2)}%, contra {num(f['abst_1t'], 2)}% no 1º turno: "
        f"{milhoes(f['comp_var'])} a mais votaram."
        + (f" {_cita(cnn)}." if cnn else ""),
        "verificado",
    )
    h += p(
        f"Mesmo dando a Lula todo o aumento líquido de comparecimento, ele explica no máximo "
        f"{num(f['teto_comp'], 2)} dos {num(f['erro'], 2)} pontos. O comparecimento só explica o resto se "
        "também mudou a composição de quem já votava no 1º turno.",
        "contrario",
    )
    # 2. prorrogação
    ms = {m["chave"]: m for m in TN.marcos(N)} if N else {}
    h += "<h4>2. A prorrogação de duas horas</h4>"
    if "zanin" in ms:
        h += p(_cita(ms["zanin"]["item"]) + ".", "verificado")
    aviso = ms.get("aviso")
    tresp = ms.get("tresp")
    partes = [
        x
        for x in (
            _cita(aviso["item"]) if aviso else "",
            _cita(tresp["item"]) if tresp else "",
        )
        if x
    ]
    if partes:
        h += p(
            "O que ela produziu e o que não produziu, pelas fontes: "
            + "; ".join(partes)
            + ".",
            "verificado",
        )
    jan = TN.janela_parada(N) if N else None
    if jan:
        h += p(
            f"A divulgação do TSE ficou parada de {TN._hm(jan[0])} a {TN._hm(jan[1])}. Quanto da "
            "votação aconteceu depois das 17h, e em que seções, só os logs das urnas vão dizer.",
            "contrario",
        )
    # 3. transporte
    h += "<h4>3. Transporte</h4>"
    for chaves in (("Procon-BA atualizou",), ("mandou prender",)):
        it = _item(N, *chaves)
        if it:
            h += p(_cita(it) + ".", "verificado")
    ba = _uf(PV, "BA")
    media = PV["hipoteses"]["contabilidade_entre_turnos"]["residuo_medio_simples_pp"]
    if ba:
        r_ba = ba["residuo_transporte_flavio_pp"]
        leitura = (
            "Flávio perdeu menos terreno ali que no resto do país: a retenção, se pesou, pesou contra o "
            "movimento em direção a Lula, não a favor."
            if r_ba > media
            else "Flávio perdeu tanto ou mais terreno ali que no resto do país."
        )
        h += p(
            f"Na Bahia, a diferença entre a urna e a repetição do 1º turno na parcela de Flávio foi de "
            f"{s2(r_ba)} pontos, contra {s2(media)} na média das UFs. {leitura}",
            "contrario",
        )
    # 4. indecisos
    ia = f["ind_autor"]
    h += "<h4>4. Destino dos indecisos</h4>"
    h += p(
        f"Os indecisos eram em média {num(ia['indecisos_medios_pct'], 1)}% nas últimas ondas. Com a divisão "
        f"do autor ({num(100 * ia['parte_flavio'], 1)}% para Flávio), o afastamento médio cai de "
        f"{s2(ia['erro_medio_sem_redistribuir'])} para {s2(ia['erro_medio_f_menos_l'])}.",
        "verificado",
    )
    h += p(
        f"Mesmo com todos os indecisos para Lula, sobram {s2(f['indec_erro'])} e Flávio continua à frente "
        f"em {f['indec_frente']} das {f['n']} casas: os indecisos completam a mudança, não a explicam.",
        "contrario",
    )
    # 5. terceira via
    h += "<h4>5. Voto útil da terceira via acima do medido</h4>"
    h += p(
        f"Entre os turnos ficaram disponíveis {milhoes(f['disponivel'])} de votos (terceira via, queda de "
        f"brancos e nulos e aumento de comparecimento). Flávio levou {num(f['parcela_flavio'], 1)}% do ganho "
        f"líquido; mesmo que todo o ganho dele viesse da terceira via, seria no máximo "
        f"{num(f['teto_terceira'], 1)}% dela. Entre as UFs, Flávio ficou mais abaixo da repetição do 1º "
        f"turno onde a terceira via pesou mais (correlação {sinal(f['corr_terc'], 2)}).",
        "verificado",
    )
    h += p(
        "É correlação entre 27 UFs, não migração individual medida: diz onde o voto se moveu, não quem "
        "o moveu.",
        "contrario",
    )
    # 6. logs e BUs
    h += "<h4>6. O que só os logs e os boletins completos vão mostrar</h4>"
    h += p(
        "Comparecimento e horário de votação por seção, votos registrados depois das 17h, biometria e "
        "substituição de urnas estão nos logs e nos boletins de urna de cada seção. O dossiê completa "
        "esta seção quando os logs de todas as urnas do 2º turno estiverem coletados e analisados.",
        "juizo",
    )
    return h


def falta_explicar(f: dict) -> str:
    h = '<h3 id="pesquisas-falta">O que ainda falta explicar</h3>'
    h += p(
        "Regra da casa: o que contraria a tese sai com o mesmo destaque. Estes fatos não se encaixam, "
        "ou ainda não se encaixam, numa mudança entre sábado e domingo."
    )
    itens = [
        f"A variação da abstenção por UF não acompanha o quanto Flávio ficou abaixo da repetição do "
        f"1º turno (correlação {sinal(f['corr_abst'], 2)}). Uma mudança vinda do comparecimento deveria "
        "deixar rastro onde o comparecimento mais mudou.",
        f"Dar a Lula todo o aumento líquido de comparecimento explica no máximo {num(f['teto_comp'], 2)} "
        f"pontos dos {num(f['erro'], 2)}.",
        f"A tendência publicada já era de Flávio perdendo terreno: {sinal(f['incl'], 3)} ponto por dia "
        f"dentro de cada casa, de {s2(f['td_ate12'])} (campo até 12/10) para {s2(f['td_desde19'])} "
        f"(campo desde 19/10). Levada até a urna pelo mesmo ritmo, a média iria a {s2(f['td_extrap'])}: "
        "parte do caminho estava em curso antes de sábado, e o ritmo não chega à urna.",
    ]
    decl = "; ".join(
        f"{escape(k)} desloca F−L {s2(v['deslocamento_f_menos_l'])}"
        for k, v in f["pres_decl"].items()
    )
    lv = f" ({decl})" if decl else ""
    itens.append(
        "A presença declarada aos institutos apontou para Flávio, não para Lula"
        + lv
        + ". Se houve presença diferencial pró-Lula, ela contrariou o que os eleitores disseram na "
        "véspera."
    )
    if "transp_erro" in f:
        itens.append(
            f"Repetir o 1º turno seção a seção, sem pesquisa nenhuma, afastava {s2(f['transp_erro'])}; "
            f"as pesquisas, {s2(f['erro'])}. Elas não se separaram muito da geografia do turno anterior."
        )
    if "est_n" in f:
        itens.append(
            f"As estaduais de duas semanas antes acertaram o vencedor em {f['est_certos']} de "
            f"{f['est_n']} UFs, com afastamento médio de {s2(f['est_erro'])}, menor que o das nacionais "
            "da véspera (seis delas da mesma casa e da mesma semana)."
        )
    itens.append(
        "Uma explicação rival: as casas teriam corrigido as ponderações depois de 04/10 na direção de "
        "Flávio e passado do ponto. Só as matrizes de ponderação de antes e depois do 1º turno "
        "decidem entre ela e a tese."
    )
    h += '<ul class="achados">' + "".join(f"<li>{x}</li>" for x in itens) + "</ul>"
    h += p(
        "O que este capítulo não prova: o dado não identifica comparecimento por candidato nem "
        "migração individual, e não autoriza afirmar intenção de nenhum instituto ou campanha. Mostra "
        "que o afastamento foi comum, grande e no mesmo sentido, e quanto cada candidato a explicação "
        "pode carregar."
    )
    return h
