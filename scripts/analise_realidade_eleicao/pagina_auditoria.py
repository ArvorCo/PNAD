"""Leitura forense: separar conferência material de triagem estatística."""

from html import escape

from .figuras import num
from .pagina_pericia import roteiro


def tabela(headers, rows):
    return (
        '<div class="table-scroll"><table><thead><tr>'
        + "".join(f"<th>{h}</th>" for h in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in rows
        )
        + "</tbody></table></div>"
    )


def casos(rows):
    return tabela(
        ["Município", "Lula 1T¹", "Lula 2T", "Desvio²", "Δ presença"],
        [
            [
                f'<button data-ibge="{r["ibge"]}">{escape(r["nome"].title())}/{r["uf"]}</button>',
                f'{num(r["lula_1t_entre_dois"],2)}%',
                f'{num(r["pct_lula"],2)}%',
                f'{num(r["com_1t_residuo"],2)} pp',
                f'{num(r["delta_comparecimento"],2)} pp',
            ]
            for r in rows
        ],
    )


def render(a):
    b, tr = a["bus"], a["triagem"]
    testes = b.get("testes", {})
    checks = [
        [
            "Somar candidatos e demais votos em cada BU",
            num(testes.get("bus_presidenciais")),
            f'{num(len(testes.get("soma_votos_diferente_cargo",[])))} divergências',
            "Consistência do arquivo decodificado",
        ],
        [
            "Comparecimento maior que aptos no cargo",
            num(testes.get("bus_presidenciais")),
            f'{num(len(testes.get("comparecimento_acima_aptos",[])))} casos',
            "Limite aritmético",
        ],
        [
            "Votos dos BUs × total oficial municipal",
            f'{num(b.get("municipios_com_bus_completos"))} municípios',
            f'{num(len(b.get("diferencas",[])))} divergências',
            "Brasil; Lula e Flávio separadamente",
        ],
        [
            "Votos municipais × Brasil sem exterior",
            "7 totais",
            (
                "Todos conferem"
                if all(
                    t["municipios"] == t["brasil_sem_exterior"]
                    for t in a["municipal"]["totais"].values()
                )
                else "Há diferenças"
            ),
            "Candidatos, válidos, BN, presença e ausência",
        ],
        [
            "RDV × BU (auditoria já arquivada)",
            num(a["rdv"].get("com_rdv")),
            f'{num(a["rdv"].get("divergencias"))} divergências',
            "Arquivos digitais da mesma origem",
        ],
        [
            "BUs enviados à paralela × oficial",
            num(a["paralela"]["recebidos"]["bus"]),
            f'{num(a["paralela"]["conferencia"].get("igual"))} iguais',
            "Amostra voluntária, não representativa",
        ],
    ]
    if not b.get("disponivel"):
        for check in checks[:3]:
            check[1:3] = ["Base indisponível", "Não executado"]
    h = """<section class="chapter" id="auditoria"><span class="sec-no">06 · Auditoria e casos a investigar</span>
    <h2>O estranho precisa passar<br><em>pelo teste da evidência.</em></h2>
    <p class="deck">O objetivo é procurar contradições verificáveis e casos que merecem apuração documental. Uma cidade rica votar em Lula, uma cidade pobre votar em Flávio ou uma seção dar zero a um candidato não demonstra, por si, manipulação.</p>
    """
    h += roteiro() + "<h3>Primeiro: a conta fecha?</h3>"
    h += tabela(["Teste", "Cobertura", "Resultado", "O que verifica"], checks)
    if b.get("disponivel") and not b.get("diferencas"):
        h += f"""<div class="note">Os BUs digitais disponíveis reproduzem os totais de votos de Lula e Flávio nos {num(b.get('municipios_com_bus_completos'))} municípios brasileiros com cobertura completa. Isso verifica a agregação desta base. Não certifica o software da urna, a liberdade do eleitor ou a autenticidade criptográfica dos arquivos.</div>"""
    else:
        h += '<p class="note warning">A conferência de BUs não sustenta uma conclusão de concordância completa. Consulte a disponibilidade, cobertura e divergências no arquivo de auditoria.</p>'
    h += f"""
    <p class="small">Dois BUs de apuração manual no exterior têm comparecimento e votos iguais a zero, sem linhas por candidato. A soma vazia vale zero: foram conferidos separadamente, não contados como divergência. Cobertura nacional dos arquivos de seção inclui exterior; os totais municipais deste relatório excluem exterior.</p>
    <h3>Depois: o que continua inesperado ao considerar o 1º turno?</h3>
    <p>O modelo de perfil usa UF, renda estimada, escolaridade, ruralidade e tamanho da votação. Um segundo modelo acrescenta o voto do próprio município no 1º turno, normalizado entre os dois finalistas. Cada município é previsto por um ajuste que não o viu durante o treinamento.</p>
    <div class="hero-stats"><div><strong>{num(tr['mae_perfil'],2)} pp</strong><span>erro absoluto médio: apenas perfil</span></div><div><strong>{num(tr['mae_com_1t'],2)} pp</strong><span>erro ao acrescentar o 1º turno</span></div><div><strong>{num(tr['n'])}</strong><span>municípios comparáveis</span></div><div><strong>2 lados</strong><span>mesma regra para os dois candidatos</span></div></div>
    <p class="note">A forte redução do erro mostra que boa parte do que parece estranho ao olhar só a renda já estava no mapa eleitoral do 1º turno. O desvio restante é uma prioridade de leitura, não uma estimativa de votos adulterados. Não somamos resíduos para dizer quantos votos seriam “suspeitos”.</p>
    <div class="duo"><div><h3>20 desvios maiores para Lula</h3>{casos(tr['cauda_lula'])}</div><div><h3>20 desvios maiores para Flávio</h3>{casos(tr['cauda_flavio'])}</div></div>
    <p class="small">¹ Percentual de Lula entre Lula e Flávio no 1º turno, sem os demais candidatos. ² Observado de Lula menos predito pelo modelo com 1º turno, em pontos percentuais. Positivo favorece Lula, negativo favorece Flávio. A lista é simétrica; não atribui irregularidade aos municípios.</p>
    <p><a href="assets/analise_realidade_eleicao/triagem.csv" download>Baixar a triagem de todos os municípios (CSV)</a></p>
    <details><summary>Modelo, validação e limites</summary><p>{escape(tr['metodo'])}</p><p>{escape(tr['limites'])}</p><p>Não há rótulos de fraude confirmada para treinar ou calibrar um classificador. Não calculamos probabilidade de fraude, valor-p da eleição ou estimativa de votos “legítimos”. A hipótese e os cortes foram escolhidos com o resultado conhecido.</p></details>
    <h3>Uma diferença bruta pode desaparecer ao comparar a mesma seção</h3>
    <p>O dossiê original compara seções com sinais operacionais às vizinhas do mesmo município e desconta a diferença que já existia no 1º turno. A tabela abaixo reproduz esse diagnóstico para ambos os candidatos.</p>"""
    sinais = []
    for s in a["sinais"]:
        if s.get("did_fatia_flavio_pp") is None:
            continue
        did, ep = s["did_fatia_flavio_pp"], s.get("ep_did_fatia_flavio_pp")
        sinais.append(
            [
                escape(s["descricao"]),
                num(s.get("n_did")),
                num(s.get("dif_fatia_flavio_vs_vizinhas_pp"), 2),
                num(did, 2),
                num(-did, 2),
                num(ep, 2),
            ]
        )
    h += tabela(
        [
            "Sinal",
            "Seções pareadas",
            "Diferença bruta F",
            "DiD Flávio",
            "DiD Lula",
            "Erro-padrão¹",
        ],
        sinais,
    )
    h += '<p class="small">Valores em pp entre os dois. DiD = diferença em diferenças contra o 1º turno e as vizinhas. ¹ Erro-padrão reproduzido do dossiê de seções, não reestimado aqui. Múltiplos sinais se sobrepõem; não somar seus efeitos ou tratá-los como provas independentes. <a href="apuracao_2T_2026.html#secoes">Método e análise completa</a>.</p>'
    h += evidencias_adicionais(a)
    h += f"""<h3>As ocorrências técnicas têm endereço e próximo passo</h3><p>Há {num(a['integrado']['as_duas'])} seções com pelo menos dois sinais do BU e atenção elevada nos logs. Esse encontro ajuda a organizar a investigação; os sinais compartilham causas possíveis e não são independentes.</p>"""
    rows = []
    for r in a["integrado"]["secoes"][:15]:
        rows.append(
            [
                f'<a href="{escape(r["politizese"],quote=True)}">{escape(r["municipio"])}/{r["uf"]}, Z{r["zona"]} S{r["secao"]}</a>',
                escape("; ".join(r["sinais_bu"])),
                escape("; ".join(r["diagnosticos_log"])),
                f'{num(r["fatia_f"],2)}% / {num(100-r["fatia_f"],2)}%',
            ]
        )
    h += tabela(["Seção", "Sinais no BU", "Diagnóstico do log", "Flávio / Lula"], rows)
    h += """<p class="small">Lista inicial reproduzida da ordenação do dossiê, não selecionada pelo candidato vencedor. <a href="apuracao_2T_2026.html#logs">Abrir os logs e a lista completa</a>.</p>
    <h3>O que pedir para fechar cada hipótese</h3>"""
    h += tabela(
        ["Hipótese", "Teste documental", "Explicações a confrontar"],
        [
            [
                "Voto alterado na transmissão/totalização",
                "BU impresso ou QR recolhido na seção × BU digital × total por candidato",
                "Coleta incompleta, seção agregada, retotalização ou erro do nosso parser",
            ],
            [
                "Urna, carga ou arquivo incompatível",
                "Zerésima, BU, log completo, assinatura e hash, correspondência efetivada e ata",
                "Contingência, troca autorizada, apuração manual e relógios distintos",
            ],
            [
                "Comparecimento ou habilitação irregular",
                "Caderno de votação e atas sob acesso autorizado; totais de habilitação e registros do mesário",
                "Prorrogação, falha biométrica, eleitores em trânsito e mudança de seção",
            ],
            [
                "Coação em território controlado",
                "Mapa datado, denúncias identificáveis, registros eleitorais e apuração pelas autoridades",
                "Presença de grupo não equivale a domínio; preferência política preexistente",
            ],
            [
                "Virada estatística improvável",
                "Seções pareadas, candidatos simétricos, controles regionais, histórico e teste fora da amostra",
                "Transferência da terceira via, mudança dos presentes e composição dos lotes",
            ],
        ],
    )
    h += """<p class="note warning">A investigação não termina em um gráfico. Uma conclusão sobre fraude exige evidência material, mecanismo e dimensão do efeito, com cadeia de custódia e oportunidade de contraditório. Declarações políticas não entram como dado de validação. A ausência de divergência nos testes executados também não demonstra ausência de toda forma de irregularidade.</p>
    <p class="small">Referências: <a href="https://www.tse.jus.br/eleicoes/urna-eletronica/seguranca-da-urna/auditoria-da-totalizacao">auditoria da totalização</a>; <a href="https://www.justicaeleitoral.jus.br/urna-eletronica/oportunidades-de-auditoria-e-fiscalizacao.html">documentos e etapas de fiscalização</a>; <a href="https://doi.org/10.1073/pnas.2103619118">Eggers, Garro e Grimmer: avaliação de alegações estatísticas</a>. As fontes oficiais descrevem os procedimentos; não substituem a conferência independente de sua execução.</p></section>"""
    return h


def evidencias_adicionais(a):
    et = a["entre_turnos"]
    h = "<h3>Perder votos absolutos é diferente de perder participação</h3>"
    h += tabela(
        [
            "Candidato",
            "Municípios com perda",
            "Votos a menos nesses municípios",
            "Com queda de presença",
            "Com alta no % válido",
        ],
        [
            [
                nome,
                num(r["n"]),
                num(r["perda_liquida_nesses_municipios"]),
                num(r["com_queda_comparecimento"]),
                num(r["com_ganho_percentual_validos"]),
            ]
            for cand, nome in [("flavio", "Flávio"), ("lula", "Lula")]
            if (r := et["perdas"][cand])
        ],
    )
    h += '<p class="small">O mesmo eleitorado não significa os mesmos presentes. Redução de votos absolutos pode coexistir com aumento percentual. A presença menor não identifica quem faltou, nem explica sozinha toda perda. <a href="apuracao_2T_2026.html#tu-menos-votos">Decomposição e listas completas</a>.</p>'
    h += "<h3>Seções com zero: verificar os dois lados e a história</h3>"
    h += tabela(
        ["Eleição", "Candidato sem votos", "Seções", "Por 100 mil seções"],
        [
            [
                f'{r["ano"]}, {r["turno"]}º turno',
                escape(r["candidato"]),
                num(r["secoes"]),
                num(r["por_100_mil_secoes"], 2),
            ]
            for r in a["zeros"]["recortes"]
        ],
    )
    f, lula = a["zeros"]["flavio_1t"], a["zeros"]["lula_1t"]
    h += f'<p>Das {num(f["secoes_com_1t"])} seções sem voto em Flávio no 2º turno, {num(f["secoes_zero"])} já tinham zero e {num(f["secoes_ate_5"])} tinham até cinco votos nele no 1º turno. As {num(lula["secoes_com_1t"])} seções sem voto em Lula já tinham zero nele no 1º turno. A concentração local precede o segundo turno em muitos desses casos; não é uma prova automática de regularidade ou irregularidade.</p><p class="small">Brasil sem exterior; bases e pareamento por chave publicados no <a href="apuracao_2T_2026.html#anomalia">dossiê de zeros</a>. Não aplicar a cada seção uma probabilidade binomial com a média nacional: eleitores de um mesmo território não são sorteios independentes do país.</p>'
    h += "<h3>Seis diferenças entre eventos do log e comparecimento do BU</h3><p>Estes são casos concretos para conferência, distintos de um resíduo econômico. O total de eventos “voto computado” extraído do log fica abaixo do comparecimento do BU. As hipóteses técnicas abaixo vêm do diagnóstico arquivado e ainda precisam ser confrontadas com os arquivos completos e a ata.</p>"
    h += tabela(
        [
            "Seção",
            "Eventos no log",
            "Presença no BU",
            "Diferença",
            "Hipótese a verificar",
        ],
        [
            [
                f'<a href="politizese.html#uf={r["uf"]}&z={r["zona"]}&s={r["secao"]}">{r["uf"]}, Z{r["zona"]} S{r["secao"]}</a>',
                num(r["computados_log"]),
                num(r["comparecimento_bu"]),
                num(r["diferenca"]),
                escape(r["explicacao_possivel"]),
            ]
            for r in a["logs_contagem"]
        ],
    )
    h += '<p class="note warning">O evento do log não é um voto atribuível a candidato. Reinício, contingência ou arquivo incompleto podem alterar a contagem extraída. Para concluir, é necessário reler o pacote original de logs, o BU, as contingências e a ata. O relatório não converte essas diferenças em votos de Lula ou Flávio.</p>'
    urnas = et["urnas"]
    did = urnas["diferenca_em_diferencas"]["todas_trocadas"]["fatia_flavio"]
    h += f'<h3>Troca de urna: o sinal persiste no voto?</h3><p>Em {num(urnas["secoes_pareadas"])} seções pareadas, {num(urnas["urna_diferente"])} trocaram de urna. No contraste contra a própria seção no 1º turno e suas vizinhas, a diferença estimada é {num(did["media_pp"],3)} pp para Flávio e {num(-did["media_pp"],3)} pp para Lula. O intervalo arquivado de 95% para Flávio vai de {num(did["ic95_pp"][0],3)} a {num(did["ic95_pp"][1],3)} pp.</p><p class="small">Diagnóstico de associação, não validação do equipamento. <a href="apuracao_2T_2026.html#logs">Modelos, cargas, trocas, método e documentos</a>.</p>'
    return h
