"""Capítulo 03 do dossiê do 2º turno: a projeção da casa durante a noite.

Lê `projecao_noite.json`: a série relida com `at=` a cada 5 minutos (o que o
método diria em cada instante) e, separada, a série exibida ao vivo.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import limites, nota, p, tabela

from .pagina_comum import Capitulo, Dados, cabeca, caminho, inteiro, num
from .pagina_fig_noite_b import fig_projecao, pontos_proj


def _pp(v: float) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "") + num(abs(v), 2)


def tabela_marcos(J: dict) -> str:
    final = J["observado_final"]["p_f_entre_os_dois"]
    proj = pontos_proj(J)
    marcos = {"19:15", "19:30", "20:00", "20:30", "21:00", "21:30", "22:00"}
    linhas = []
    for pt in proj:
        if pt["hhmm"] not in marcos:
            continue
        linhas.append(
            [
                pt["hhmm"],
                f"{num(pt['pst'], 2)}%",
                num(pt["p_f_observado"], 2),
                num(pt["p_f_projetado"], 2),
                num(100 - pt["p_f_observado"], 2),
                num(100 - pt["p_f_projetado"], 2),
                f"{num(pt['faixa90'][0], 2)} a {num(pt['faixa90'][1], 2)}",
                f"{num(100 - pt['faixa90'][1], 2)} a {num(100 - pt['faixa90'][0], 2)}",
                _pp(pt["p_f_projetado"] - final),
            ]
        )
    return tabela(
        [
            "Hora",
            "Seções",
            "Flávio observado",
            "Flávio projetado",
            "Lula observado",
            "Lula projetado",
            "Faixa 90% Flávio",
            "Faixa 90% Lula",
            "Erro de Flávio (pp)",
        ],
        linhas,
        f"Percentuais entre os dois. Final: Flávio {num(final, 2)}%, Lula {num(100 - final, 2)}%. O erro de Lula tem sinal oposto e a mesma magnitude. Fonte: projecao_noite.json, pontos.",
    )


def metodo(J: dict) -> str:
    par = J["parametros"]
    return (
        "<details><summary>Como a projeção funciona</summary>"
        "<p>Para cada município, a projeção compara o que já foi contado no 2º turno com o 1º turno no mesmo estágio da contagem "
        "(a mesma fração das seções do município) e calcula a oscilação, o <i>swing</i>, da parte de Flávio entre os dois. "
        f"Município com poucas seções empresta força da UF: pesa n/(n+{inteiro(par['K'])}) e o resto vem da UF; a UF pesa "
        f"N/(N+{inteiro(par['K_uf'])}) e o resto vem do Brasil. A parte não totalizada recebe os votos dos dois que faltavam no 1º turno "
        "nesse estágio, multiplicados pela razão de comparecimento observada.</p>"
        f"<p>A faixa de {par['nivel_faixa']}% sai de {inteiro(par['reps'])} reamostragens dos municípios observados dentro de cada UF, "
        f"mais o resíduo municipal e um erro comum de {num(par['erro_comum_pp'], 0)} ponto, aplicados só ao que falta totalizar. "
        f"Abaixo de {num(par['minimo_pst'], 0)}% das seções do país a rota não projeta: a base é pequena e concentrada demais.</p>"
        f"<p>Método registrado no arquivo: {par['metodo']}.</p></details>"
    )


def render(d: Dados, cap: Capitulo) -> str:
    J = d.get("projecao_noite.json")
    p0 = J["primeiro_ponto_com_projecao"]
    err = J["erro_absoluto_pp"]
    final = J["observado_final"]
    proj = pontos_proj(J)
    ult = proj[-1]
    lider = J.get("lider_projetado_em_todos_os_pontos") or []
    todos_lula = lider == ["lula"]
    h = cabeca(
        cap,
        (
            f"Lula à frente<br><em>em {J['pontos_com_projecao']} de {J['pontos_com_projecao']} pontos.</em>"
            if todos_lula
            else "A projeção<br><em>da casa.</em>"
        ),
        f"Primeiro ponto às {p0['hhmm']}, com {num(p0['pst'], 2)}% das seções: Flávio {num(p0['p_f_projetado'], 2)}% "
        f"e Lula {num(p0['p_l_projetado'], 2)}% entre os dois.",
    )
    h += p(
        f"Às {p0['hhmm']}, com {inteiro(p0['st'])} seções ({num(p0['pst'], 2)}%) de {inteiro(p0['municipios_observados'])} municípios, "
        f"a projeção dava Flávio {num(p0['p_f_projetado'], 2)}% e Lula {num(p0['p_l_projetado'], 2)}%, faixa de 90% de "
        f"{num(p0['faixa90'][0], 2)} a {num(p0['faixa90'][1], 2)} para Flávio. A contagem observada naquele instante tinha Flávio com "
        f"{num(p0['p_f_observado'], 2)}%. O resultado final ficou em {num(final['pct_flavio_validos'], 2)}% × {num(final['pct_lula_validos'], 2)}%: "
        f"{_pp(p0['p_f_projetado'] - final['p_f_entre_os_dois'])} ponto de distância, dentro da faixa.",
        "verificado",
    )
    fr = J.get("pontos_com_flavio_a_frente_no_observado") or {}
    if fr.get("n"):
        h += p(
            f"Entre {fr['de']} e {fr['ate']}, a contagem observada teve Flávio à frente em {fr['n']} pontos de 5 minutos, com máximo "
            f"de {num(fr['maximo_p_f_observado'], 2)}% entre os dois na soma usada pela rota. A projeção seguiu com Lula, porque o que faltava "
            "contar era, no 1º turno, mais favorável a ele.",
            "verificado",
        )
    h += fig_projecao(J)
    h += p(
        f"Erro absoluto médio contra o final: {num(err['medio'], 2)} ponto; máximo de {num(err['maximo'], 2)}. "
        f"Em {J['pontos_com_final_dentro_da_faixa90']} dos {J['pontos_com_projecao']} pontos o final ficou dentro da faixa de 90%. "
        f"No último ponto, às {ult['hhmm']}, a projeção era {num(ult['p_f_projetado'], 2)}% contra {num(final['p_f_entre_os_dois'], 2)}% observado.",
        "verificado",
    )
    fora = J.get("pontos_fora_da_faixa90") or []
    if fora:
        dist = max(f["distancia_pp"] for f in fora)
        h += nota(
            "contrario",
            f"Nos {len(fora)} últimos pontos (de {fora[0]['hhmm']} a {fora[-1]['hhmm']}), o final ficou fora da faixa de 90%, "
            f"a no máximo {num(dist, 2)} ponto. Com quase tudo contado, a faixa encolhe a centésimos e deixa de cobrir o que ainda "
            "muda nas seções finais: a incerteza do fim da noite foi subestimada. Erro pequeno em pontos não absolve faixa estreita demais.",
            "A faixa ficou estreita demais no fim.",
        )
    h += tabela_marcos(J)
    viv = J.get("serie_ao_vivo")
    if viv:
        h += p(
            "A série relida não é necessariamente a que a tela mostrou: a rota foi chamada de novo sobre o banco com o relógio de cada "
            f"instante. A série exibida ao vivo ({inteiro(len(viv['linhas']))} leituras do telão, arquivo <code>{viv['fonte']}</code>) "
            "aparece separada no gráfico, em pontilhado.",
            "verificado",
        )
    h += metodo(J)
    h += limites(
        [
            caminho(J, "rotulo")
            or "Projeção estatística; não é resultado nem previsão de vitória.",
            "A régua é o 1º turno no mesmo estágio da contagem: se a ordem de chegada das seções mudar entre turnos, o swing por estágio carrega viés.",
            "O erro comum de 1 ponto é hipótese declarada, não estimado na noite.",
            "A série relida reconstrói o método sobre o banco; o que foi ao ar está na série ao vivo.",
        ]
    )
    return h
