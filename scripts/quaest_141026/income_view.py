"""Capítulo de renda com resultado condicional e verificação documental."""

from dossies_2t_2026.view import callout, details, fmt, note, section, signed, table

from .charts import income_charts


def render(d):
    income = d["identificacao_renda"]
    poll = d["pesquisa"]
    cross = poll["cruzamentos"]["2t"]
    rows = [dict(zip(cross["opcoes"], row, strict=True)) for row in cross["linhas"]]
    adjusted = income["reponderacao_pontual"]
    controls = income["controles"]
    return section(
        1,
        "renda",
        "A renda reduz a distância.<br><em>Sob uma hipótese explícita.</em>",
        "O painel salvo pelo usuário trouxe os cruzamentos atuais. Os pesos finais continuam pendentes.",
        income_charts(d)
        + details(
            "Conferir votos por renda e pesos usados",
            table(
                [
                    "Renda domiciliar",
                    "Flávio",
                    "Lula",
                    "BN/não vota",
                    "Indecisos",
                    "Cota TSE / PNAD",
                ],
                [
                    [
                        band["rotulo"],
                        f'{r["flavio"]}%',
                        f'{r["lula"]}%',
                        f'{r["branco_nulo"]}%',
                        f'{r["indecisos"]}%',
                        f"{fmt(w,0)}% / {fmt(q,2)}%",
                    ]
                    for band, r, w, q in zip(
                        poll["renda"]["faixas"],
                        rows,
                        income["pesos_registro_pct"],
                        income["pnad_pct"],
                        strict=True,
                    )
                ],
            ),
        )
        + f'<p>Usando as cotas atuais 31/42/27 como pesos, o cruzamento recompõe <b>{fmt(income["recomposto"]["flavio"],2)}% de Flávio e {fmt(income["recomposto"]["lula"],2)}% de Lula</b>, contra 46% e 44% publicados. O controle por sexo recompõe {fmt(controls["sexo"]["recomposto"]["flavio"],2)}% e {fmt(controls["sexo"]["recomposto"]["lula"],2)}%. Idade e escolaridade também conferem a menos de 0,3 pp por candidato. São verificações da leitura, não confirmação dos pesos finais.</p>'
        + callout(
            f'Sensibilidade PNAD: Flávio {fmt(adjusted["flavio"],2)}% × Lula {fmt(adjusted["lula"],2)}%',
            f'A diferença F−L cai de +2 para {signed(income["gap_ajustado_pp"],2)} pp sobre o total. O delta é {signed(income["delta_ajuste_pp"]["flavio"],2)} pp para Flávio e {signed(income["delta_ajuste_pp"]["lula"],2)} pp para Lula. Retirando apenas brancos/nulos e indecisos, a renormalização dá {fmt(income["flavio_binario_pct"],2)}% × {fmt(100-income["flavio_binario_pct"],2)}%. Não é resultado corrigido nem previsão.',
        )
        + "<p><b>31/42/27 são cotas planejadas, não os pesos finais conferidos.</b> O registro prevê eventual rake e MrP. A conta supõe essas cotas como a distribuição final e preserva o topline: ajustado = publicado + (PNAD × voto por faixa − cotas × voto por faixa). A boa recomposição não verifica a hipótese. Até a íntegra, a estimativa é condicional e pode mudar.</p>"
        + "<p>O registro declara PNADC anual 2025, primeira visita, para renda domiciliar total. A régua Arvor usa a mesma edição, pessoas de 16 anos ou mais e os cortes nominais convertidos aos preços do histograma. A diferença das distribuições exige reconciliar universo, conceito e calibração; não demonstra uso de PNAD antiga.</p>"
        + "<h3>O placar estável esconde movimentos opostos por renda</h3>"
        + table(
            ["Faixa", "03/10 · F × L", "14/10 · F × L", "Mudança F−L na faixa"],
            [
                [
                    r["faixa"],
                    f'{r["antes"]["flavio"]} × {r["antes"]["lula"]}',
                    f'{r["agora"]["flavio"]} × {r["agora"]["lula"]}',
                    signed(r["mudanca_gap_pp"], 0),
                ]
                for r in income["evolucao_0310"]
            ],
        )
        + "<p>Até 2 SM, Flávio sobe três pontos e Lula cai um: a distância muda quatro pontos a favor de Flávio. Entre 2 e 5 SM, Lula cresce quatro contra dois de Flávio; acima de 5 SM, Lula ganha três e Flávio fica parado. São movimentos numéricos em amostras distintas, sem teste de significância por faixa e sem identificar quem mudou de voto.</p>"
        + f'<p>Fixando 31/42/27 nas duas pontas, as contribuições para a mudança F−L são +1,24, −0,84 e −0,81 pp, soma {signed(income["mudanca_gap_recomposto_pp"],2)} pp. O gap publicado não muda; a diferença dos resíduos é {signed(income["mudanca_residuo_pp"],2)} pp. Não forçamos o fechamento. O perfil de 03/10 era hipótese da onda anterior, e o atual é cota registrada. Essa conta não prova composição final constante.</p>'
        + note(income["limite"])
        + callout(
            "Como esta onda entra nas centrais",
            'A Quaest passa a integrar a Média por renda e a Projeção com esta sensibilidade provisória baseada nas cotas atuais. Os rótulos e a ficha identificam a hipótese. Presença, ajuste relativo extra e destino de indecisos são hipóteses comuns do simulador, separadas desta conta de renda. <a href="reponderacao_pnad.html#quaest-1410">Conferir a integração e os limites</a>.',
        )
        + details(
            "Fonte preservada e alternativas de renda",
            '<p><a href="fontes/quaest_14102026/painel-evidencia.html">Cinco gráficos originais extraídos do arquivo salvo</a> · <a href="fontes/quaest_14102026/painel-extraido.csv">Todos os recortes em CSV</a> · <a href="fontes/quaest_14102026/painel-extraido.json">Extração, integridade e limites</a>. São 25 recortes completos mais o total. O gráfico de identificação lulista não tinha rótulos numéricos no arquivo e permanece ausente, nunca zero.</p>'
            + table(
                ["Régua PNAD", "Flávio", "Lula"],
                [
                    [
                        label,
                        fmt(income["cenarios"][key]["flavio"], 2),
                        fmt(income["cenarios"][key]["lula"], 2),
                    ]
                    for key, label in [
                        ("pessoas16_efetivo", "Pessoas 16+, renda efetiva"),
                        ("pessoas16_habitual", "Pessoas 16+, renda habitual"),
                        ("domicilios_efetivo", "Domicílios, renda efetiva"),
                    ]
                ],
            ),
        ),
    )
