"""Texto da página: capítulos explicativos e valores para o template.

Todo número sai do JSON. As frases não presumem gênero: falam da candidatura
de alguém e do eleitorado de alguém.
"""

from __future__ import annotations

from html import escape as esc

from .comum import (
    ASSENTOS,
    POR_ESTADO,
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
    out: dict[str, set[str]] = {}
    for uf, e in data["estados"].items():
        out[uf] = {
            casa_do_arquivo(p.get("arquivo", ""), idx.get(p.get("arquivo")))
            for p in e.get("pesquisas_usadas", [])
        }
    return out


def exemplo(data: dict) -> str:
    """Estado com pesquisa recente e disputa mais apertada entre o 2º e o 3º da média."""
    melhor = None
    for uf, e in data["estados"].items():
        media = sorted(
            e.get("media", []), key=lambda m: m.get("valor") or 0, reverse=True
        )
        if e.get("cobertura") != "recente" or len(media) < 3:
            continue
        gap = (media[1].get("valor") or 0) - (media[2].get("valor") or 0)
        if melhor is None or gap < melhor[0]:
            melhor = (gap, uf, e, media)
    if melhor is None:
        return ""
    gap, uf, e, media = melhor
    probs = {c.get("nome"): c.get("p_eleito") for c in e.get("probabilidades", [])}
    a, b, c = media[0], media[1], media[2]
    return (
        f'<p class="example">Um caso desta página. Em {esc(e.get("nome", uf))}, a média das '
        f"pesquisas põe a candidatura de {esc(a['nome'])} em {num(a['valor'])}% dos "
        f"entrevistados, a de {esc(b['nome'])} em {num(b['valor'])}% e a de "
        f"{esc(c['nome'])} em {num(c['valor'])}%. O segundo está {num(gap)} ponto"
        f"{'' if abs(gap - 1) < 1e-9 else 's'} à frente do terceiro. A chance de eleição da "
        f"segunda candidatura é {pct(probs.get(b['nome']))}; a da terceira, "
        f"{pct(probs.get(c['nome']))}. Estar à frente na média não é ter a vaga: "
        "a probabilidade mede quanto essa posição aguenta o erro das pesquisas.</p>"
    )


def _parametros(data: dict) -> str:
    p = data.get("parametros", {})
    linhas = []
    nomes = {
        "meia_vida_dias": "Meia-vida do peso por idade (dias)",
        "janela_campo_minimo": "Campo mais antigo aceito na central",
        "simulacoes": "Simulações",
        "escala_erro_comum_pp": "Escala do erro comum ao estado (pp)",
        "escala_erro_candidato_pp": "Escala do erro por candidatura (pp)",
    }
    for k, v in p.items():
        if isinstance(v, (dict, list)) or k == "justificativa_erro":
            continue
        rotulo = nomes.get(k, k.replace("_", " "))
        valor = data_br(v) if k.startswith("janela") else esc(str(v))
        linhas.append(f"<li><b>{esc(rotulo)}:</b> {valor}</li>")
    return '<ul class="sn-params">' + "".join(linhas) + "</ul>" if linhas else ""


def _calibracao(data: dict) -> str:
    p, v = data.get("parametros", {}), data.get("validacao", {})
    cal = p.get("calibracao_2022") or v.get("calibracao_2022")
    just = p.get("justificativa_erro")
    if cal:
        corpo = (
            esc(cal)
            if isinstance(cal, str)
            else "; ".join(
                f"{esc(str(k).replace('_', ' '))}: {esc(str(x))}"
                for k, x in cal.items()
            )
        )
        return (
            '<p class="io"><strong>Calibração de 2022:</strong> '
            f"{corpo}{(' ' + esc(just)) if just else ''}</p>"
        )
    return (
        '<p class="hyp"><strong>Hipótese declarada:</strong> a escala do erro das '
        "pesquisas de Senado não foi calibrada com a eleição de 2022."
        f"{(' ' + esc(just)) if just else ''} "
        '<strong class="iffail">Se falhar:</strong> se o erro real for maior que o '
        "declarado, as probabilidades ficam confiantes demais e os intervalos de "
        "90% ficam estreitos demais. Se for menor, ocorre o inverso. A ordem dos "
        "nomes pouco muda; a confiança muda.</p>"
    )


def como_lemos(data: dict) -> str:
    p = data.get("parametros", {})
    meia = p.get("meia_vida_dias")
    janela = p.get("janela_campo_minimo")
    casas = casas_por_estado(data)
    varias = sum(1 for c in casas.values() if len(c) >= 2)
    com_pesq = sum(1 for c in casas.values() if c)
    meia_txt = (
        f"O peso de cada onda cai pela metade a cada {num(meia, 0)} dias, contados do ponto médio do campo."
        if meia is not None
        else "O peso de cada onda cai com a idade, contada do ponto médio do campo."
    )
    janela_txt = (
        f" Só entram ondas com campo a partir de {data_br(janela)}." if janela else ""
    )
    return f"""
<h3>Probabilidade de eleição não é percentual de voto</h3>
<p>O percentual de voto responde a uma pergunta: quanto do eleitorado marca esta candidatura. A probabilidade de eleição responde a outra: em quantas das simulações esta candidatura termina entre as duas mais votadas do estado.</p>
<p class="analogy">Pense numa corrida em que os dois primeiros ganham medalha. Chegar três metros à frente do terceiro colocado a dez metros da linha não garante a medalha. Chegar três metros à frente a cem metros da linha também não. A distância é a mesma; a chance muda com o quanto ainda pode acontecer até o fim. A pesquisa mede a distância. A probabilidade mede a chance.</p>
{exemplo(data)}
<h3>Como as casas são combinadas</h3>
<p>Cada estado recebe uma onda por instituto. {meia_txt}{janela_txt} As casas entram com peso igual na combinação. {num(varias, 0)} dos {num(com_pesq, 0)} estados com pesquisa têm duas casas ou mais; os demais dependem de uma só.</p>
<p class="plain">Em palavras: uma pesquisa antiga vale menos que uma nova, e uma casa não vale mais que outra só por ter feito mais perguntas. A média resume o que as casas disseram, com o tempo pesando contra quem ficou para trás.</p>
<h3>Como os indecisos entram</h3>
<p>Indecisos e votos em branco ou nulo ficam fora da divisão de votos válidos na proporção do voto declarado. Nenhum nome recebe todos eles. A conta tem uma sensibilidade uniforme, que espalha o efeito igualmente entre as candidaturas, para testar quanto o resultado depende dessa escolha.</p>
<p class="hyp"><strong>Hipótese:</strong> quem hoje não declara voto se comporta, na urna, como quem declara. <strong class="iffail">Se falhar:</strong> se os indecisos forem mais para nomes conhecidos, as candidaturas menores perdem mais do que a página mostra. Por isso nenhuma probabilidade aqui é certeza.</p>
<h3>De onde vem a escala do erro</h3>
<p>A probabilidade nasce de um sorteio repetido. Em cada rodada, o estado inteiro recebe um erro comum, porque as casas erram juntas, e cada candidatura recebe um erro próprio. A escala desses erros é o parâmetro que mais pesa no resultado.</p>
{_parametros(data)}
{_calibracao(data)}
<div class="io sn-regra"><strong>Regra do jogo:</strong> cada estado elege {POR_ESTADO} nomes. Em cada estado, as probabilidades de eleição somam {POR_ESTADO},0. O Senado que toma posse em 2027 tem {ASSENTOS} assentos: os que continuam mais os eleitos de 2026.</div>
"""


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
    incertos = [
        data["estados"][uf].get("nome", uf)
        for uf, e in data["estados"].items()
        if e.get("p_dupla_mais_provavel") is not None
        and e["p_dupla_mais_provavel"] < 0.5
    ]
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
    achado = ""
    val = data.get("validacao", {})
    sens = val.get("sensibilidades") if isinstance(val, dict) else None
    if sens:
        itens = "".join(
            f"<li><b>{esc(s.get('rotulo', ''))}.</b> {esc(s.get('descricao', ''))}</li>"
            for s in sens
        )
        achado = (
            "<h3>O que contraria a leitura principal</h3>"
            "<p>As sensibilidades abaixo trocam uma premissa por vez. Elas ficam ao lado da central, "
            f"com o mesmo destaque.</p><ul>{itens}</ul>"
        )
    contra = val.get("achado_contrario") if isinstance(val, dict) else None
    if contra:
        achado += (
            f'<p class="hyp"><strong>Achado contra a tese:</strong> {esc(contra)}</p>'
        )
    return f"""
<ul class="sn-limites">
<li><b>Campo recente.</b> {campo_txt} Mudança de opinião depois do campo não aparece.</li>
<li><b>Uma casa em muitos estados.</b> {num(len(unica), 0)} estados dependem de uma única casa.{casa_txt} Quando a casa erra, o estado erra junto.</li>
<li><b>Cobertura antiga.</b> Estados com pesquisa antiga e peso fraco: {_lista(antigos)}. A incerteza deles é alta.</li>
<li><b>Sem pesquisa.</b> Estados sem pesquisa registrada: {_lista(sem)}. A página não indica nomes nesses estados.</li>
<li><b>Dupla incerta.</b> Em {num(len(incertos), 0)} estados, a dupla mais provável tem menos de 50% de chance: {_lista(sorted(incertos))}.</li>
<li><b>Voto útil de última hora.</b> Quem muda de candidatura na véspera ou no dia da votação fica fora de qualquer pesquisa com campo anterior.</li>
<li><b>Suplentes e migrações.</b> Suplência, renúncia, mudança de partido e cassação ficam fora do modelo. O hemiciclo é o Senado eleito, não o do dia da posse.</li>
<li><b>Campo é classificação editorial.</b> A etiqueta de campo segue a classificação da casa por partido, com exceções declaradas: tucano é centro-esquerda por decisão editorial da casa. Outra classificação muda os totais por campo, não os nomes.</li>
</ul>
{achado}
<p class="plain">Em palavras: a página mostra o que as pesquisas registradas permitem dizer até {ref}. Não mostra o que ainda pode mudar, e diz onde faltam dados.</p>
"""


def values(data: dict) -> dict[str, str]:
    s27 = data["senado_2027"]
    continuam = len(s27.get("continuam", [])) or sum(
        int(v.get("continuam", 0)) for v in s27.get("por_campo", {}).values()
    )
    novos = ASSENTOS - continuam
    return {
        "DATE": data_br(data.get("data_referencia")),
        "ELECTION_DATE": data_br(data.get("eleicao")),
        "CONTINUAM": num(continuam, 0),
        "NOVOS": num(novos, 0),
        "ASSENTOS": num(ASSENTOS, 0),
        "POR_ESTADO": num(POR_ESTADO, 0),
        "N_ESTADOS": num(len(data["estados"]), 0),
        "N_FONTES": num(len(data.get("fontes", [])), 0),
        "P_MAIORIA": pct(s27.get("p_maioria_direita_mais_centro_direita")),
        "GERADO": esc(data.get("gerado_em", "")),
        "COBERTURA_RECENTE": num(len(_por_cobertura(data, "recente")), 0),
        "COBERTURA_ANTIGA": num(len(_por_cobertura(data, "antiga")), 0),
        "COBERTURA_SEM": num(len(_por_cobertura(data, "sem_pesquisa")), 0),
    }


def probabilidades_bloco(data: dict) -> str:
    """Probabilidades agregadas do Senado, lidas do JSON, com leitura declarada."""
    s27 = data["senado_2027"]
    maioria = ASSENTOS // 2 + 1
    dois_tercos = -(-2 * ASSENTOS // 3)
    itens = (
        (
            "p_maioria_direita_mais_centro_direita",
            f"Direita e centro-direita somam {maioria} assentos ou mais",
        ),
        (
            "p_41_direita_centro_direita_centro",
            f"Direita, centro-direita e centro somam {maioria} assentos ou mais",
        ),
        (
            "p_54_bloco_oposicao",
            f"O bloco de oposição chega a {dois_tercos} assentos, dois terços do Senado",
        ),
    )
    linhas = [
        f"<li><strong>{pct(s27[k])}</strong><span>{rotulo}</span></li>"
        for k, rotulo in itens
        if s27.get(k) is not None
    ]
    if not linhas:
        return ""
    return '<ul class="sn-probs">' + "".join(linhas) + "</ul>"
