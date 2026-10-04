"""Texto da página: capítulos explicativos e valores para o template.

Todo número sai do JSON. As frases não presumem gênero: falam da candidatura
de alguém.
"""

from __future__ import annotations

from html import escape as esc

from senado_2026.pagina.comum import (
    casa_do_arquivo,
    data_br,
    indice_fontes,
    num,
    pct,
)


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
    """Estado com pesquisa recente em que a favorita na média não tem a vaga
    garantida: mostra a diferença entre liderar e ser eleita."""
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
        f'<p class="example">Um caso desta página. Em {esc(e.get("nome", uf))}, a média das '
        f"pesquisas põe a candidatura de {esc(fav['nome'])} em {num(fav['validos_central'])}% "
        f"dos válidos, perto da linha dos 50%. O 1º turno decide em {pct(e['p_decide_1t'])} das "
        f"simulações e a chance de eleição dessa candidatura, somando os dois turnos, é "
        f"{pct(fav['p_eleito'])}. Estar perto de 50% na média não é vencer no 1º turno: a "
        "probabilidade mede quanto essa posição aguenta o erro das pesquisas.</p>"
    )


def _parametros(data: dict) -> str:
    p = data.get("parametros", {})
    nomes = {
        "meia_vida_dias": ("Meia-vida do peso por idade (dias)", 1),
        "janela_campo_minimo": ("Campo mais antigo aceito na central", None),
        "simulacoes": ("Simulações", 0),
        "deff": ("Efeito de desenho assumido", 1),
        "escala_erro_pp": ("Escala do erro, candidatura em 30% (pp)", 1),
        "escala_erro_pp_com_deriva_7_dias": (
            "Mesma escala, com 7 dias de deriva (pp)",
            1,
        ),
    }
    linhas = []
    for k, (rotulo, casas) in nomes.items():
        if k not in p:
            continue
        v = p[k]
        valor = data_br(v) if casas is None else num(v, casas)
        linhas.append(f"<li><b>{esc(rotulo)}:</b> {valor}</li>")
    t = p.get("transferencia") or {}
    if t:
        linhas.append(
            f"<li><b>Transferência em par não medido:</b> {num(100 * t['fracao_valida'], 0)}% "
            f"do voto eliminado vai a um finalista; temperatura {num(t['tau'])}; ruído extra "
            f"{num(t['sd_logit'], 2)} no logit</li>"
        )
    return '<ul class="sn-params">' + "".join(linhas) + "</ul>" if linhas else ""


def _calibracao(data: dict) -> str:
    v = data.get("validacao", {})
    cal = v.get("calibracao_2022") or {}
    p = data.get("parametros", {})
    just = p.get("justificativa_erro")
    just_txt = f"<p>{esc(just)}</p>" if just else ""
    if cal.get("fonte") == "wikipedia_2022":
        partes = [
            f"A escala foi conferida contra a urna de 2022: {num(cal['n_pesquisas'], 0)} "
            f"pesquisas finais para governador em {num(cal['n_estados'], 0)} estados."
        ]
        if cal.get("rmse_20_40_pp"):
            partes.append(
                "Entre candidaturas com 20% a 40% dos válidos, a raiz do erro quadrático "
                f"médio foi {num(cal['rmse_20_40_pp'])} pontos."
            )
        if cal.get("erro_medio_abs_pp"):
            partes.append(
                f"No conjunto, o erro médio absoluto foi {num(cal['erro_medio_abs_pp'])} pontos."
            )
        vies = cal.get("vies_medio_por_campo_pp") or {}
        if vies.get("direita") is not None:
            partes.append(
                "Em 2022 as pesquisas finais ficaram, em média, "
                f"{num(abs(vies['direita']))} pontos "
                f"{'abaixo' if vies['direita'] < 0 else 'acima'} da urna para candidaturas de "
                "direita. O modelo não corrige esse viés: ele entra só como tamanho do erro, "
                "nas duas direções."
            )
        link = (
            f' <a href="{esc(cal["url"])}" rel="noopener">Conferir a calibração</a>.'
            if cal.get("url")
            else ""
        )
        return (
            '<p class="io"><strong>Calibração de 2022:</strong> '
            + " ".join(partes)
            + link
            + "</p>"
            + just_txt
        )
    return (
        '<p class="hyp"><strong>Hipótese declarada:</strong> a escala do erro não foi '
        'calibrada com a eleição de 2022. <strong class="iffail">Se falhar:</strong> se o '
        "erro real for maior, as probabilidades ficam confiantes demais; se for menor, "
        f"o inverso.</p>{just_txt}"
    )


def como_lemos(data: dict) -> str:
    p = data.get("parametros", {})
    meia = p.get("meia_vida_dias")
    janela = p.get("janela_campo_minimo")
    casas = casas_por_estado(data)
    varias = sum(1 for c in casas.values() if len(c) >= 2)
    com_pesq = sum(1 for c in casas.values() if c)
    v = data.get("validacao", {})
    n_pares = v.get("pares_2t_medidos_total") or 0
    ufs_par = v.get("ufs_com_par_medido") or []
    meia_txt = (
        f"O peso de cada onda cai pela metade a cada {num(meia, 0)} dias, contados do ponto médio do campo."
        if meia is not None
        else ""
    )
    janela_txt = (
        f" Só entram ondas com campo a partir de {data_br(janela)}." if janela else ""
    )
    return f"""
<h3>Três perguntas, três números</h3>
<p>A página responde a três perguntas por estado. Quem tem mais chance de ser eleita, somando os dois turnos. Qual a chance de a eleição terminar em 04/10, com mais de 50% dos votos válidos. E, se houver 2º turno, quem enfrenta quem e com que placar.</p>
<p class="analogy">Pense num campeonato com final. Chegar à final não é ganhar o título, e ganhar na fase de grupos com folga não dispensa a final: a regra manda jogar. A probabilidade de eleição soma dois caminhos, ganhar na fase de grupos (mais de 50% no 1º turno) ou ganhar a final. Os dois são sorteados, não presumidos.</p>
{exemplo(data)}
<h3>Como as casas são combinadas</h3>
<p>Cada estado recebe uma onda por instituto. {meia_txt}{janela_txt} As casas entram com peso igual na combinação. {num(varias, 0)} dos {num(com_pesq, 0)} estados com pesquisa têm duas casas ou mais; os demais dependem de uma só.</p>
<p class="plain">Em palavras: uma pesquisa antiga vale menos que uma nova, e uma casa não vale mais que outra. A média resume o que as casas disseram, com o tempo pesando contra quem ficou para trás.</p>
<h3>Como os indecisos entram</h3>
<p>{esc(p.get("indecisos_regra") or "")}</p>
<p class="hyp"><strong>Hipótese:</strong> quem hoje não declara voto se comporta, na urna, como quem declara. <strong class="iffail">Se falhar:</strong> se os indecisos forem mais para nomes conhecidos, as candidaturas menores perdem mais do que a página mostra, e a decisão no 1º turno fica mais provável do que o número diz.</p>
<h3>Quando o 1º turno decide</h3>
<p>{esc(p.get("regra_1t") or "")}</p>
<h3>Como o 2º turno é projetado</h3>
<p><b>Par medido.</b> {esc(p.get("regra_2t_medido") or "")} Há {num(n_pares, 0)} pares medidos em {num(len(ufs_par), 0)} estados.</p>
<p><b>Par não medido.</b> {esc(p.get("regra_2t_transferencia") or "")}</p>
<p class="hyp"><strong>Hipótese:</strong> o erro das pesquisas de 2º turno anda junto com o erro do 1º turno, com correlação declarada de 0,5. <strong class="iffail">Se falhar:</strong> se os erros forem independentes, a chance da favorita num 2º turno surpresa fica maior do que a página mostra; se andarem juntos por completo, menor.</p>
<h3>De onde vem a escala do erro</h3>
<p>A probabilidade nasce de um sorteio repetido. Em cada rodada, o campo político inteiro recebe um erro comum, porque as casas erram juntas, e cada candidatura recebe um erro próprio. A escala desses erros é o parâmetro que mais pesa no resultado.</p>
{f'<p class="plain">{esc(p["decomposicao_erro"])}</p>' if p.get("decomposicao_erro") else ""}
{_parametros(data)}
{_calibracao(data)}
<div class="io sn-regra"><strong>Regra do jogo:</strong> cada estado elege uma pessoa para o governo. Em cada estado, as probabilidades de eleição somam 1,0. Mais de 50% dos válidos no 1º turno encerra a disputa; senão, as duas mais votadas voltam à urna em {data_br(data.get("segundo_turno_data"))}.</div>
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
    """O achado que mais pesa contra a leitura central, gerado dos números."""
    estados = data["estados"]
    n = data["nacional"]
    partes = []
    g = n.get("por_grupo", {})
    if g.get("direita") and g.get("esquerda"):
        partes.append(
            f"A leitura central dá {num(g['direita']['esperado'])} governos esperados à direita e "
            f"centro-direita e {num(g['esquerda']['esperado'])} à esquerda e centro-esquerda, mas "
            f"a maioria dos 27 (14 ou mais) para o primeiro bloco só sai em "
            f"{pct(g['direita'].get('p_maioria_14'))} dos sorteios."
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
            f"Em {', '.join(sorted(invertidos))}, quem lidera a média do 1º turno não é a "
            "favorita na eleição: o 2º turno medido inverte a ordem."
        )
    return " ".join(partes)


def limites(data: dict) -> str:
    p = data.get("parametros", {})
    janela = p.get("janela_campo_minimo")
    ref = data_br(data.get("data_referencia"))
    casas = casas_por_estado(data)
    unica = sorted(
        data["estados"][uf].get("nome", uf) for uf, c in casas.items() if len(c) == 1
    )
    antigos = _por_cobertura(data, "antiga")
    sem = _por_cobertura(data, "sem_pesquisa")
    v = data.get("validacao", {})
    sem_par = sorted(
        data["estados"][uf].get("nome", uf)
        for uf, e in data["estados"].items()
        if e.get("cobertura") != "sem_pesquisa" and not e.get("pares_medidos")
    )
    por_casa: dict[str, int] = {}
    for c in casas.values():
        for casa in c:
            por_casa[casa] = por_casa.get(casa, 0) + 1
    lider = max(por_casa.items(), key=lambda kv: kv[1], default=None)
    campo_txt = (
        f"A central usa pesquisas com campo de {data_br(janela)} a {ref}."
        if janela
        else f"A central usa as pesquisas mais recentes até {ref}."
    )
    casa_txt = (
        f" A casa mais presente, {esc(lider[0])}, cobre {num(lider[1], 0)} estados."
        if lider
        else ""
    )
    sens = v.get("sensibilidades") or []
    achado = ""
    if sens:
        itens = "".join(_sens_item(x) for x in sens)
        achado = (
            "<h3>O que contraria a leitura principal</h3>"
            "<p>As sensibilidades abaixo trocam uma premissa por vez. Elas ficam ao lado "
            f"da central, com o mesmo destaque.</p><ul>{itens}</ul>"
        )
    contra = achado_contrario(data)
    if contra:
        achado += (
            f'<p class="hyp"><strong>Achado contra a tese:</strong> {esc(contra)}</p>'
        )
    nao_faz = p.get("o_que_nao_faz")
    return f"""
<ul class="sn-limites">
<li><b>Campo recente.</b> {campo_txt} Mudança de opinião depois do campo não aparece.</li>
<li><b>Uma casa em muitos estados.</b> {num(len(unica), 0)} estados dependem de uma única casa.{casa_txt} Quando a casa erra, o estado erra junto.</li>
<li><b>Cobertura antiga.</b> Estados com pesquisa antiga e peso fraco: {_lista(antigos)}. A incerteza deles é alta.</li>
<li><b>Sem pesquisa.</b> Estados sem pesquisa registrada: {_lista(sem)}.</li>
<li><b>2º turno sem medição.</b> Estados em que nenhum instituto mediu par de 2º turno: {_lista(sem_par)}. Ali a projeção é transferência declarada, não medição.</li>
<li><b>Cenários alternativos ficam fora.</b> Quando o instituto publica um cenário com dois nomes sem chamá-lo de 2º turno, ele entra no acervo como cenário alternativo e não como par medido.</li>
<li><b>Voto útil de última hora.</b> Quem muda de candidatura na véspera ou no dia da votação fica fora de qualquer pesquisa com campo anterior.</li>
<li><b>Campo é classificação editorial.</b> A etiqueta de campo segue a classificação da casa por partido, com exceções declaradas: tucano é centro-esquerda por decisão editorial da casa. Outra classificação muda os totais por campo, não os nomes.</li>
{f'<li><b>O que o modelo não faz.</b> {esc(nao_faz)}</li>' if nao_faz else ''}
</ul>
{achado}
<p class="plain">Em palavras: a página mostra o que as pesquisas registradas permitem dizer até {ref}. Não mostra o que ainda pode mudar, e diz onde faltam dados.</p>
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
        "DECIDIDOS_1T": num(dec.get("esperado", 0)),
        "DECIDIDOS_IC": f"{num(dec.get('ic90', [0, 0])[0], 0)} a {num(dec.get('ic90', [0, 0])[1], 0)}",
        "SEGUNDO_TURNO_ESPERADO": num(seg.get("esperado", 0)),
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
