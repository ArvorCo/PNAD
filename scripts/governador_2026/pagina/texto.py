"""Texto da página: capítulos explicativos e valores para o template.

Linguagem de aula primeiro; os parâmetros e as sensibilidades ficam dentro de
caixas fechadas para quem quiser conferir. Todo número sai do JSON.
"""

from __future__ import annotations

from html import escape as esc

from senado_2026.pagina.comum import casa_do_arquivo, data_br, indice_fontes, num, pct


def _por_cobertura(data: dict, cob: str) -> list[str]:
    return sorted(
        e.get("nome", uf)
        for uf, e in data["estados"].items()
        if e.get("cobertura") == cob
    )


def _lista(nomes: list[str]) -> str:
    if not nomes:
        return "nenhum"
    if len(nomes) == 1:
        return esc(nomes[0])
    return esc(", ".join(nomes[:-1])) + " e " + esc(nomes[-1])


def casas_por_estado(data: dict) -> dict[str, set[str]]:
    idx = indice_fontes(data)
    return {
        uf: {
            casa_do_arquivo(p.get("arquivo", ""), idx.get(p.get("arquivo")))
            for p in e.get("pesquisas_usadas", [])
        }
        for uf, e in data["estados"].items()
    }


def exemplo(data: dict) -> str:
    """Estado em que a favorita está perto dos 50% dos válidos."""
    melhor = None
    for uf, e in data["estados"].items():
        if e.get("cobertura") != "recente" or not e.get("media"):
            continue
        fav = next((p for p in e["probabilidades"] if p["nome"] == e["favorito"]), None)
        if not fav or (fav.get("validos_central") or 0) < 45:
            continue
        gap = abs(50 - fav["validos_central"])
        if melhor is None or gap < melhor[0]:
            melhor = (gap, uf, e, fav)
    if melhor is None:
        return ""
    _, uf, e, fav = melhor
    return (
        f'<p class="example"><b>Um exemplo desta página.</b> Em {esc(e.get("nome", uf))}, '
        f"as pesquisas dão a {esc(fav['nome'])} cerca de {num(fav['validos_central'], 0)}% dos votos "
        f"válidos, bem perto da linha dos 50%. Por isso a conta diz que a eleição termina amanhã em "
        f"{pct(e['p_decide_1t'])} das simulações, e que a chance total de {esc(fav['nome'])} governar, "
        f"somando os dois turnos, é {pct(fav['p_eleito'])}. Estar perto de 50% não é ter vencido: a "
        "chance mede quanto essa posição aguenta o erro das pesquisas.</p>"
    )


def _tecnico(data: dict) -> str:
    p = data.get("parametros", {})
    v = data.get("validacao", {})
    cal = v.get("calibracao_2022") or {}
    linhas = []
    nomes = {
        "meia_vida_dias": ("Meia-vida do peso por idade (dias)", 1),
        "janela_campo_minimo": ("Campo mais antigo aceito na central", None),
        "simulacoes": ("Simulações por estado", 0),
        "deff": ("Efeito de desenho assumido", 1),
        "escala_erro_pp": ("Escala do erro, candidatura em 30% (pontos)", 1),
    }
    for k, (rotulo, casas) in nomes.items():
        if k in p:
            valor = data_br(p[k]) if casas is None else num(p[k], casas)
            linhas.append(f"<li><b>{esc(rotulo)}:</b> {valor}</li>")
    t = p.get("transferencia") or {}
    if t:
        linhas.append(
            f"<li><b>Par sem medição:</b> {num(100 * t['fracao_valida'], 0)}% do voto eliminado vai a "
            f"um finalista, dividido por proximidade de campo (temperatura {num(t['tau'])}); ruído "
            f"extra {num(t['sd_logit'], 2)} no logit</li>"
        )
    linhas.append("<li><b>Correlação do erro entre os turnos:</b> 0,5</li>")
    cal_txt = ""
    if cal.get("fonte") == "wikipedia_2022":
        cal_txt = (
            f"<p>Calibração: {num(cal['n_pesquisas'], 0)} pesquisas finais para governador em "
            f"{num(cal['n_estados'], 0)} estados em 2022, contra a urna. Erro médio absoluto "
            f"{num(cal['erro_medio_abs_pp'])} pontos; raiz do erro quadrático médio entre 20% e 40% "
            f"dos válidos, {num(cal['rmse_20_40_pp'])} pontos."
            + (
                f' <a href="{esc(cal["url"])}" rel="noopener">Conferir</a>.'
                if cal.get("url")
                else ""
            )
            + "</p>"
        )
    just = (
        f"<p>{esc(p['justificativa_erro'])}</p>" if p.get("justificativa_erro") else ""
    )
    dec = f'<p>{esc(p["decomposicao_erro"])}</p>' if p.get("decomposicao_erro") else ""
    return (
        '<details class="gv-tec"><summary>Para quem quer os parâmetros</summary>'
        f'<ul class="sn-params">{"".join(linhas)}</ul>{cal_txt}{just}{dec}'
        f'<p>{esc(p.get("regra_2t_medido") or "")}</p><p>{esc(p.get("regra_2t_transferencia") or "")}</p>'
        "</details>"
    )


def como_lemos(data: dict) -> str:
    p = data.get("parametros", {})
    meia = p.get("meia_vida_dias")
    casas = casas_por_estado(data)
    varias = sum(1 for c in casas.values() if len(c) >= 2)
    com_pesq = sum(1 for c in casas.values() if c)
    v = data.get("validacao", {})
    n_pares = v.get("pares_2t_medidos_total") or 0
    ufs_par = v.get("ufs_com_par_medido") or []
    cal = v.get("calibracao_2022") or {}
    erro_txt = (
        f"Em 2022, as pesquisas finais para governador erraram em média {num(cal['erro_medio_abs_pp'], 0)} "
        f"pontos por candidatura, e {num(cal['rmse_20_40_pp'], 0)} pontos nas disputas de meio de tabela. "
        "É esse tamanho de erro que a conta repete milhares de vezes."
        if cal.get("rmse_20_40_pp")
        else "O tamanho do erro é uma hipótese declarada nos parâmetros."
    )
    meia_txt = (
        f"Uma pesquisa vale metade a cada {num(meia, 0)} dias que passam."
        if meia is not None
        else "Pesquisa mais nova vale mais."
    )
    return f"""
<h3>O que é "chance de governar"</h3>
<p>Não é o percentual de votos. É quantas vezes a candidatura termina eleita quando a eleição é simulada milhares de vezes, cada vez com um erro de pesquisa diferente, do tamanho que as pesquisas erraram de verdade em 2022.</p>
<p class="analogy">Pense numa previsão do tempo. "70% de chance de chuva" não quer dizer que vai chover 70% do dia: quer dizer que, em dez dias assim, chove em sete. Aqui é igual: "70% de chance de governar" quer dizer que, em dez eleições com pesquisas assim, a candidatura ganha em sete.</p>
{exemplo(data)}
<h3>Os dois caminhos até o governo</h3>
<p>O 1º turno acaba a eleição quando alguém passa de metade dos votos válidos (brancos, nulos e indecisos ficam fora da conta). Se ninguém passa, os dois mais votados voltam em {data_br(data.get("segundo_turno_data"))}. A chance de governar soma os dois caminhos: vencer já amanhã ou vencer o 2º turno.</p>
<h3>Como o 2º turno é projetado</h3>
<p>Quando um instituto perguntou "e se fosse só entre A e B?", a página usa essa medição: {num(n_pares, 0)} pares foram medidos em {num(len(ufs_par), 0)} estados, e aparecem com o selo <span class="gv-chip gv-chip-medido">medido</span>. Quando ninguém mediu, a página estima para onde iria o voto de quem ficou de fora, puxando pela proximidade política, e avisa com o selo <span class="gv-chip gv-chip-estimado">estimado</span>.</p>
<h3>Como as pesquisas são juntadas</h3>
<p>Cada estado recebe a pesquisa mais recente de cada instituto. {meia_txt} Nenhuma casa vale mais que outra. {num(varias, 0)} dos {num(com_pesq, 0)} estados com pesquisa têm dois institutos ou mais; os outros dependem de um só.</p>
<p>Quem está indeciso é repartido na proporção de quem já escolheu, com uma parte das simulações repartindo por igual. Branco e nulo nunca viram voto.</p>
<h3>De onde vem o tamanho do erro</h3>
<p>{erro_txt}</p>
{_tecnico(data)}
"""


def _sens_item(x: dict) -> str:
    muda = x.get("favoritos_que_mudam") or []
    ufs = ", ".join(
        f"{m.get('uf', '')} ({m.get('central')} para {m.get('sensibilidade')})"
        for m in muda
    )
    resumo = (
        f" A favorita muda em {num(len(muda), 0)} estados: {esc(ufs)}."
        if muda
        else " A favorita não muda em nenhum estado."
    )
    dec = x.get("decididos_1t_esperado")
    dec_txt = (
        f" Estados decididos no 1º turno: {num(dec)} esperados."
        if dec is not None
        else ""
    )
    return f"<li><b>{esc(x.get('rotulo', ''))}.</b> {esc(x.get('descricao', ''))}{resumo}{dec_txt}</li>"


def achado_contrario(data: dict) -> str:
    estados = data["estados"]
    n = data["nacional"]
    partes = []
    g = n.get("por_grupo", {})
    if g.get("direita") and g.get("esquerda"):
        partes.append(
            f"A leitura central dá {num(g['direita']['esperado'])} governos à direita e centro-direita "
            f"e {num(g['esquerda']['esperado'])} à esquerda e centro-esquerda, mas a maioria dos 27 "
            f"(14 ou mais) para o primeiro bloco só sai em {pct(g['direita'].get('p_maioria_14'))} "
            "das simulações."
        )
    apertadas = n.get("por_classe", {}).get("apertada") or []
    if apertadas:
        partes.append(
            f"Em {num(len(apertadas), 0)} estados a favorita tem menos de 70% de chance "
            f"({', '.join(apertadas)}): nesses, a página não sabe quem ganha."
        )
    invertidos = [
        uf
        for uf, e in estados.items()
        if e.get("media") and e["media"][0]["nome"] != e.get("favorito")
    ]
    if invertidos:
        partes.append(
            f"Em {', '.join(sorted(invertidos))}, quem lidera as pesquisas do 1º turno não é a "
            "favorita na eleição: o 2º turno medido inverte a ordem."
        )
    return " ".join(partes)


def limites(data: dict) -> str:
    ref = data_br(data.get("data_referencia"))
    casas = casas_por_estado(data)
    unica = sorted(
        data["estados"][uf].get("nome", uf) for uf, c in casas.items() if len(c) == 1
    )
    antigos = _por_cobertura(data, "antiga")
    v = data.get("validacao", {})
    sem_par = sorted(
        data["estados"][uf].get("nome", uf)
        for uf, e in data["estados"].items()
        if e.get("cobertura") != "sem_pesquisa" and not e.get("pares_medidos")
    )
    sens = v.get("sensibilidades") or []
    extra = ""
    if sens:
        extra = (
            '<details class="gv-tec"><summary>O que muda se uma premissa mudar</summary>'
            f'<ul>{"".join(_sens_item(x) for x in sens)}</ul></details>'
        )
    contra = achado_contrario(data)
    contra_txt = (
        f'<p class="hyp"><strong>O que pesa contra esta leitura:</strong> {esc(contra)}</p>'
        if contra
        else ""
    )
    return f"""
<ul class="sn-limites gv-limites">
<li><b>Pesquisa não é urna.</b> Tudo aqui parte das pesquisas publicadas até {ref}. Quem mudou de ideia depois não aparece.</li>
<li><b>Um instituto só.</b> {num(len(unica), 0)} estados dependem de um único instituto. Se ele errou, o estado erra junto.</li>
<li><b>Pesquisa antiga.</b> {_lista(antigos)}: sem pesquisa recente, a incerteza é alta.</li>
<li><b>2º turno sem medição.</b> Em {_lista(sem_par)}, nenhum instituto mediu o par; o placar é estimativa.</li>
<li><b>Campo político é rótulo da casa.</b> Tucano conta como centro-esquerda por decisão editorial. Outra régua muda as cores do mapa, não os nomes.</li>
</ul>
{contra_txt}
{extra}
<p class="plain">Em palavras: a página mostra o que as pesquisas permitem dizer até {ref}, e diz onde faltam dados.</p>
"""


def values(data: dict) -> dict[str, str]:
    n = data["nacional"]
    dec = n.get("decididos_1t") or {}
    seg = n.get("segundo_turno") or {}
    classes = n.get("por_classe") or {}
    v = data.get("validacao", {})
    return {
        "DATE": data_br(data.get("data_referencia")),
        "ELECTION_DATE": data_br(data.get("eleicao")),
        "SEGUNDO_TURNO_DATE": data_br(data.get("segundo_turno_data")),
        "N_ESTADOS": num(len(data["estados"]), 0),
        "N_FONTES": num(len(data.get("fontes", [])), 0),
        "DECIDIDOS_1T": num(dec.get("esperado", 0), 0),
        "DECIDIDOS_IC": f"{num(dec.get('ic90', [0, 0])[0], 0)} a {num(dec.get('ic90', [0, 0])[1], 0)}",
        "SEGUNDO_TURNO_ESPERADO": num(seg.get("esperado", 0), 0),
        "N_APERTADAS": num(len(classes.get("apertada", [])), 0),
        "N_PROVAVEIS": num(len(classes.get("provavel", [])), 0),
        "N_DECIDIDAS": num(len(classes.get("decidida", [])), 0),
        "N_PARES_MEDIDOS": num(v.get("pares_2t_medidos_total", 0), 0),
        "N_UFS_PAR_MEDIDO": num(len(v.get("ufs_com_par_medido", [])), 0),
        "GERADO": esc(data.get("gerado_em", "")),
        "COBERTURA_RECENTE": num(len(_por_cobertura(data, "recente")), 0),
        "COBERTURA_ANTIGA": num(len(_por_cobertura(data, "antiga")), 0),
        "COBERTURA_SEM": num(len(_por_cobertura(data, "sem_pesquisa")), 0),
    }
