"""Capítulo estratégico do Sudeste no dossiê de 21/09/2026.

Lê `docs/assets/datafolha_21092026_sudeste.json` e
`docs/assets/datafolha_21092026_cobertura_sudeste.json`, mais as camadas
municipais já publicadas de MG e SP. Nenhum número é digitado aqui: todos vêm
dos JSON auditáveis, com a página do relatório ao lado. O texto é desta casa;
os campos de prosa dos JSON são registro de máquina e não são reproduzidos.
"""

import importlib.util
import json
from html import escape
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"
SLUG = "datafolha_21092026"
UFS = ("SP", "RJ", "MG")
NOME_UF = {
    "SP": "São Paulo",
    "RJ": "Rio de Janeiro",
    "MG": "Minas Gerais",
    "ES": "Espírito Santo",
}
PAGINA_GOV = {"SP": 39, "RJ": 38, "MG": 40}
PAGINA_PRES = {"SP": 58, "RJ": 76, "MG": 94}


def carrega(nome):
    return json.loads((ASSETS / nome).read_text(encoding="utf-8"))


def modulo(caminho: str, nome: str) -> ModuleType:
    alvo = ROOT / caminho
    spec = importlib.util.spec_from_file_location(nome, alvo)
    if spec is None or spec.loader is None:
        raise ImportError(f"nao foi possivel carregar {alvo}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FIG = modulo("scripts/datafolha-21092026-sudeste-figuras.py", "sudeste_figuras")
curto = FIG.primeiro_nome
milhar = FIG.milhar
sinal = FIG.sinal


def num(valor, casas=2):
    return f"{valor:.{casas}f}".replace(".", ",")


def duas_larguras(larga, estreita):
    """Mesma figura em dois desenhos: um para a tela larga, outro para o celular.

    Os dois SVG vão embutidos no HTML e a troca é só de CSS, sem JavaScript:
    a página aberta do disco continua mostrando o gráfico certo para a
    largura da tela.
    """
    return (
        f'<div class="fig-larga">{larga}</div>'
        f'<div class="fig-estreita">{estreita}</div>'
    )


def aviso_rolar(legenda):
    """Legenda com o aviso de rolagem, visível só na tela estreita.

    O diagrama de fitas e o painel de recortes não empilham sem perder a
    leitura. Neles a figura continua rolando para o lado, e o leitor de
    celular precisa saber disso.
    """
    return (
        f'{legenda} <span class="fig-rolar">Em tela estreita o gráfico '
        "continua para o lado: arraste na horizontal.</span>"
    )


def ref_gov(uf, pagina, rotulo=None):
    return (
        f'<a class="refs" href="fontes/{SLUG}_governador_{uf.lower()}.pdf'
        f'#page={pagina}">{rotulo or f"{uf} · governador p. {pagina}"}</a>'
    )


def ref_pres(pagina, rotulo=None):
    return (
        f'<a class="refs" href="fontes/{SLUG}_estaduais.pdf#page={pagina}">'
        f'{rotulo or f"Presidente estadual p. {pagina}"}</a>'
    )


def ref_nac(pagina):
    return (
        f'<a class="refs" href="fontes/{SLUG}.pdf#page={pagina}">'
        f"Nacional p. {pagina}</a>"
    )


def bloco(ident, titulo):
    return f'<h3 id="{ident}">{titulo}</h3>'


def achado(dados, ident):
    return next(a for a in dados["achados"] if a["id"] == ident)


def data_curta(iso):
    return f"{iso[8:10]}/{iso[5:7]}"


def item_de_pauta(cobertura, uf, trecho):
    for item in cobertura["itens"]:
        if item["uf"] == uf and trecho.lower() in item["titulo"].lower():
            return item
    raise KeyError(f"título ausente na cobertura: {uf} / {trecho}")


def link_de_pauta(item):
    return (
        f'<li><a href="{item["url"]}">{escape(item["titulo"])}</a> '
        f'<span class="refs">{escape(item["veiculo"])} · '
        f'{data_curta(item["data"])}/2026</span></li>'
    )


def abertura(dados, table, figure):
    vao = {uf: dados["estados"][uf]["vao"]["turno2"] for uf in UFS}
    es = dados["espirito_santo"]
    h = (
        '<section id="sudeste-campanha">'
        '<div class="section-head"><p class="kicker">02C / CAMPANHA</p>'
        "<h2>O Sudeste não é um problema.<br><em>São três.</em></h2>"
        '<p class="lead">Na mesma amostra e no mesmo campo de 8 a 10 de setembro, '
        "São Paulo e Minas colocam a candidatura de direita ao governo acima de "
        "Flávio Bolsonaro, e o Rio inverte o sinal. Os três estados pedem três "
        "campanhas diferentes.</p></div>"
    )
    h += (
        f"<p>São Paulo: Tarcísio {vao['SP']['governador_pct']} contra Flávio "
        f"{vao['SP']['presidenciavel_pct']} no segundo turno, vão de "
        f"{sinal(vao['SP']['vao_pp'])} pontos. Minas: Cleitinho "
        f"{vao['MG']['governador_pct']} contra {vao['MG']['presidenciavel_pct']}, "
        f"vão de {sinal(vao['MG']['vao_pp'])}. O Rio anda no sentido contrário: "
        f"Flávio {vao['RJ']['presidenciavel_pct']} e Douglas Ruas "
        f"{vao['RJ']['governador_pct']}, vão de {sinal(vao['RJ']['vao_pp'])}. "
        f"{ref_gov('SP', 39)} {ref_gov('RJ', 38)} {ref_gov('MG', 40)} "
        f"{ref_pres(58, 'SP · presidente p. 58')} "
        f"{ref_pres(76, 'RJ · presidente p. 76')} "
        f"{ref_pres(94, 'MG · presidente p. 94')}</p>"
    )
    h += (
        '<p class="boundary">O vão é <strong>teto endereçável, não previsão</strong>. '
        "Votar no governador não torna o eleitor disponível para o presidenciável. "
        "Cargos, cédulas e incentivos são diferentes, e diferença entre cargos não "
        "prova erro do instituto. Este capítulo é camada de apoio: a conclusão do "
        'dossiê continua sendo a <a href="#renda">reponderação por renda</a>.</p>'
    )
    h += figure(
        duas_larguras(FIG.placar(dados), FIG.placar_estreito(dados)),
        "Datafolha em SP, RJ e MG, campo de 8 a 10/09/2026, votos totais. O Espírito "
        "Santo vem da Real Time Big Data, campo de 4 a 8/09/2026, com outro método, "
        "e aparece em bloco separado: não entra em média com o Datafolha e não fecha "
        "a conta do Sudeste.",
    )
    h += bloco("sudeste-placar", "Três cargos por estado, na mesma entrevista.")
    linhas = []
    for uf in UFS:
        estado = dados["estados"][uf]
        senado_uf = estado["senado"]
        gov = estado["vao"]
        pres = estado["presidente"]
        linhas.append(
            [
                f"{uf} · {NOME_UF[uf]}<br><span class=\"refs\">n {milhar(estado['n'])}"
                f" · projeto {escape(estado['projeto'])}</span>",
                f"{curto(gov['turno1']['candidato_governador'])} "
                f"{gov['turno1']['governador_pct']}%",
                f"{curto(gov['turno2']['candidato_governador'])} "
                f"{gov['turno2']['governador_pct']}%",
                f"{curto(senado_uf['lider_alcance']['nome'])} "
                f"{senado_uf['lider_alcance']['valor']}%",
                f"{pres['turno1']['Flavio Bolsonaro (PL)']}% × "
                f"{pres['turno1']['Lula (PT)']}%",
                f"{pres['turno2']['Flavio Bolsonaro (PL)']}% × "
                f"{pres['turno2']['Lula (PT)']}%",
                f"{sinal(gov['turno1']['vao_pp'])} / {sinal(gov['turno2']['vao_pp'])}",
            ]
        )
    h += table(
        [
            "Estado",
            "Governador 1º turno",
            "Direita no 2º turno estadual",
            "Senado, maior alcance",
            "Presidente 1º · Flávio × Lula",
            "Presidente 2º · Flávio × Lula",
            "Vão 1º / 2º",
        ],
        linhas,
    )
    h += (
        '<p class="table-source">Governador: '
        + " · ".join(
            ref_gov(uf, PAGINA_GOV[uf], f"{uf} p. {PAGINA_GOV[uf]}") for uf in UFS
        )
        + ". Presidente: "
        + " · ".join(
            ref_pres(PAGINA_PRES[uf], f"{uf} p. {PAGINA_PRES[uf]}") for uf in UFS
        )
        + ". Senado pelo alcance nos dois votos. O primeiro turno presidencial usado "
        "aqui é a <strong>Situação B do anexo, sem Pablo Marçal</strong>, que é o "
        "cenário que reproduz o placar divulgado.</p>"
    )
    h += (
        "<aside><b>O Espírito Santo entra fora da média.</b>"
        f"Real Time Big Data, contratante Real Time Mídia, campo de {es['campo']}, "
        f"{milhar(es['n'])} entrevistas, registros {es['registros']['estadual']} e "
        f"{es['registros']['presidencial']}. No primeiro turno estadual a direita "
        "perde para o centro: Ferraço "
        f"{es['governador_turno1']['valores']['Ricardo Ferraço (MDB)']} contra "
        f"{es['governador_turno1']['valores']['Lorenzo Pazolini (REPUBLICANOS)']} de "
        f"Pazolini, com Flávio em "
        f"{es['presidente_turno1']['valores']['Flavio Bolsonaro (PL)']}. No segundo "
        f"turno presidencial, Flávio "
        f"{es['presidente_turno2']['valores']['Flavio Bolsonaro (PL)']} e Lula "
        f"{es['presidente_turno2']['valores']['Lula (PT)']}. O método não é "
        "declarado no PDF nem na matéria: o instituto registra abordagem mista no "
        "TSE e descreve entrevistas por telefone nos relatórios nacionais. Não "
        "transportamos esse método sem conferir, e por isso o estado fica em bloco "
        "próprio.</aside>"
    )
    return h


def transferencia(dados, table, figure):
    varredura = dados["varredura_de_cruzamentos"]
    h = bloco("sudeste-transferencia", "Treze linhas medidas. O resto é hipótese.")
    h += (
        "<p>Antes de estimar qualquer coisa, procuramos o cruzamento publicado. Ele "
        "existe. O relatório presidencial estadual cruza o voto para governador com "
        "o voto para presidente no texto corrido, em São Paulo, no Rio e em Minas: "
        f"<strong>{varredura['linhas_medidas']} linhas</strong> de origem, com a "
        "página ao lado. Elas entram fixas, como medição. Os anexos de tabelas "
        "cruzadas têm três blocos e nenhum deles usa o voto de outro cargo como "
        "coluna; os relatórios de governador não citam a Presidência.</p>"
    )
    linhas = []
    for cruzamento in dados["cruzamentos_publicados"]:
        destino = (
            "1º turno" if "1o turno" in cruzamento["destino_pergunta"] else "2º turno"
        )
        for origem, valores in cruzamento["linhas"].items():
            linhas.append(
                [
                    curto(origem),
                    cruzamento["uf"],
                    destino,
                    ", ".join(
                        f"{curto(nome)} {valor}%" for nome, valor in valores.items()
                    ),
                    f"{100 - sum(valores.values())}%",
                    ref_pres(cruzamento["pagina"], f"p. {cruzamento['pagina']}"),
                ]
            )
    h += table(
        [
            "Eleitorado do candidato ao governo",
            "UF",
            "Destino",
            "Destinos publicados",
            "Fora dos destinos publicados",
            "Fonte",
        ],
        linhas,
    )
    h += (
        "<p>Três leituras diretas, sem modelo. Em Minas, <strong>25% do eleitor de "
        "Cleitinho vota em Lula</strong> no segundo turno presidencial, e 29% não "
        f"votam em Flávio. {ref_pres(21, 'p. 21')} Em São Paulo, <strong>41% do "
        "eleitorado de Tarcísio ficam fora de Flávio</strong> já no primeiro turno: "
        f"12 pontos com Lula e 8 com Cury. {ref_pres(4, 'p. 4')} No Rio, o eleitor "
        f"de Eduardo Paes dá 28% a Flávio no segundo turno. {ref_pres(13, 'p. 13')}</p>"
    )
    h += (
        "<p>O que falta é a matriz completa, com bases e pesos, e a fidelidade de "
        "base do segundo turno estadual. Por isso o diagrama abaixo tem duas "
        "naturezas de fita: <strong>sólida onde existe linha publicada</strong> e "
        "hachurada onde a célula é estimada por ajuste proporcional iterativo contra "
        "uma prior declarada. Toda célula não medida carrega a faixa de Fréchet, que "
        "é o único número imune à prior.</p>"
    )
    for uf in UFS:
        alvo = dados["transferencia"][uf]["gov1_pres2"]
        variante = alvo["variantes"]["ideologica"]
        publicadas = len(variante["linhas_medidas"])
        h += figure(
            FIG.sankey(
                uf,
                alvo,
                f"{uf}: do voto de governador ao 2º turno presidencial",
                "Origem: voto estimulado para governador. Destino: 2º turno "
                "presidencial. Mesma amostra, campo de 8 a 10/09/2026.",
            ),
            aviso_rolar(
                f"{NOME_UF[uf]}. {publicadas} das "
                f"{len(variante['origem_pct'])} origens têm linha publicada pelo "
                "instituto; as demais são estimadas. A largura é massa percentual "
                "agregada, não acompanhamento de pessoas. Candidaturas abaixo de "
                "3% sem linha publicada aparecem somadas em uma origem única."
            ),
        )
        h += (
            '<div class="flow-readout" aria-live="polite">Toque em uma fita ou use '
            "Tab para ler origem, destino, natureza e faixa de Fréchet.</div>"
        )
    h += (
        "<p>São Paulo é o caso a cobrar. O instituto publicou o cruzamento com o "
        "<strong>primeiro</strong> turno presidencial e nenhuma linha com o segundo. "
        "Por isso o diagrama paulista sai inteiramente hachurado, enquanto o carioca "
        "tem duas origens sólidas e o mineiro, três.</p>"
    )
    h += bloco("sudeste-robustez", "O que sobrevive à troca da prior.")
    linhas = []
    pares = (
        ("gov1_pres1", "Governador 1º → presidente 1º"),
        ("gov1_pres2", "Governador 1º → presidente 2º"),
        ("gov2_pres2", "Governador 2º → presidente 2º"),
    )
    for uf in UFS:
        for chave, rotulo in pares:
            robustez = dados["transferencia"][uf][chave]["robustez"]
            faixa = robustez["celula_direita_para_flavio"]
            valores = list(robustez["vazamento_da_direita_pct"].values())
            linhas.append(
                [
                    f"{uf} · {rotulo}",
                    "Medida" if robustez["medida"] else "Estimada",
                    f"{num(min(valores))} a {num(max(valores))}%",
                    f"{num(robustez['amplitude_entre_priors_pp'])} pp",
                    f"{num(faixa['frechet_min_pp'], 1)} a "
                    f"{num(faixa['frechet_max_pp'], 1)} pp",
                ]
            )
    h += table(
        [
            "Estado e par de perguntas",
            "Natureza",
            "Vazamento da direita, entre as priors",
            "Amplitude",
            "Fréchet da célula direita → Flávio",
        ],
        linhas,
    )
    amplitude = {
        uf: dados["transferencia"][uf]["gov2_pres2"]["robustez"][
            "amplitude_entre_priors_pp"
        ]
        for uf in UFS
    }
    h += (
        "<p>A leitura é direta. <strong>Onde há linha publicada, a amplitude entre "
        "as priors é zero</strong>: a prior não move nada, porque a margem já está "
        "medida. Onde não há, ela decide o resultado, e vai de "
        f"{num(amplitude['MG'])} pontos em Minas a {num(amplitude['RJ'])} pontos no "
        "Rio, no par de segundo turno contra segundo turno, que é justamente o par "
        "que nenhum dos três relatórios cruza. Publicá-lo custaria uma tabela ao "
        "instituto e encerraria a discussão.</p>"
    )
    serie = dados["transferencia"]["SP"]["serie_do_vazamento"]
    setembro = list(serie["setembro_2026_pct"].values())
    h += (
        "<p><strong>Série de São Paulo.</strong> Em agosto a mesma conta devolveu "
        f"{num(serie['agosto_2026_datafolha_pct'])}% do eleitor de Tarcísio fora de "
        f"Flávio no segundo turno pelo Datafolha e "
        f"{num(serie['agosto_2026_atlas_pct'])}% pela Atlas. Em setembro, a faixa "
        f"entre as priors vai de {num(min(setembro))}% a {num(max(setembro))}%. A "
        "régua é a mesma nos dois campos, com origem e destino nas mesmas perguntas, "
        "e os dois números continuam sendo estimativa por ajuste proporcional, não "
        "medição. Por isso a comparação vale como série, e não como uma medida "
        'única. <a class="refs" href="sp_092026.html">Atlas de São Paulo</a></p>'
    )
    h += (
        "<details><summary>Faixa de Fréchet de cada célula dos três diagramas</summary>"
    )
    linhas = []
    for uf in UFS:
        _, _, _, celulas = FIG.celulas_do_diagrama(
            dados["transferencia"][uf]["gov1_pres2"]
        )
        for celula in celulas:
            linhas.append(
                [
                    f"{uf} · {curto(celula['origem'])}",
                    FIG.CURTO[celula["destino"]],
                    num(celula["valor_pp"]),
                    f"{num(celula['frechet_min_pp'], 1)} a "
                    f"{num(celula['frechet_max_pp'], 1)}",
                    "Publicada" if celula["medida"] else "Estimada",
                ]
            )
    h += table(
        ["Origem", "Destino", "Valor no diagrama, pp", "Fréchet, pp", "Natureza"],
        linhas,
    )
    h += (
        "<p>A prior é declarada e ideológica: base própria fiel, candidatura do mesmo "
        "campo migrando majoritariamente para o líder do campo, cruzamento para o "
        "campo oposto próximo de zero e não escolha absorvendo parte das perdas. Os "
        "zeros são estruturais e o ajuste proporcional os preserva. A leitura é "
        "agregada e nunca descreve o percurso de um entrevistado.</p></details>"
    )
    return h


def vao_por_recorte(dados, table, figure):
    h = bloco("sudeste-vao", "O vão por recorte, e o que ele vale em votos.")
    coberturas = {uf: dados["estados"][uf]["cobertura_dos_recortes"] for uf in UFS}
    renda = [coberturas[uf]["renda"]["cobertura_pct"] for uf in UFS]
    religiao = [coberturas[uf]["religiao"]["cobertura_pct"] for uf in UFS]
    h += (
        "<p>Só agregamos por partição fechada. Renda nunca fecha nos três estados, "
        "porque recusa e não sabe existem no cartão e não ganham coluna: a cobertura "
        f"vai de {num(min(renda))}% a {num(max(renda))}% das bases. Religião cobre de "
        f"{num(min(religiao))}% a {num(max(religiao))}%. Partido de preferência fecha "
        "em São Paulo e em Minas e cobre "
        f"{num(coberturas['RJ']['partido']['cobertura_pct'])}% no Rio. A figura usa "
        "apenas os quatorze recortes que formam partição fechada nos três estados.</p>"
    )
    h += figure(
        FIG.vao_por_recorte(dados),
        aviso_rolar(
            "Vão por recorte no segundo turno: candidatura de direita ao governo "
            "menos Flávio, dentro do mesmo recorte e na mesma entrevista. Sexo, "
            "idade, escolaridade, ocupação e natureza do município fecham a base "
            "nos três estados. Renda, cor, religião e, no Rio, partido de "
            "preferência ficam fora da figura e aparecem na tabela abaixo."
        ),
    )
    linhas = []
    for uf in UFS:
        indice = FIG.indice_de_recortes(dados["estados"][uf])
        for dimensao, recorte in (
            ("renda", "Ate 2 SM"),
            ("renda", "2 a 5 SM"),
            ("renda", "Mais de 5 SM"),
            ("religiao", "Catolica"),
            ("religiao", "Evangelica"),
        ):
            linha = indice[(dimensao, recorte)]
            linhas.append(
                [
                    f"{uf} · {escape(recorte)}",
                    f"{linha['governador']}%",
                    f"{linha['flavio']}%",
                    sinal(linha["vao_pp"]),
                    f"±{num(linha['margem_vao_pp'], 1)} pp",
                    milhar(linha["base_governador"]),
                    "Sim" if linha["particao_fechada"] else "Não",
                ]
            )
    h += table(
        [
            "Recorte de partição aberta",
            "Governo do estado",
            "Flávio",
            "Vão",
            "Margem do vão",
            "Base ponderada",
            "Partição fechada",
        ],
        linhas,
    )
    h += (
        "<p>Esses recortes descrevem, mas não somam. Usá-los para compor um número "
        "estadual inventaria cobertura que o anexo não tem.</p>"
    )
    h += table(
        [
            "Estado",
            "Vão no 2º turno",
            "Eleitorado TSE 2026",
            "Equivalente sobre o eleitorado",
            "Equivalente sobre os válidos de 2022",
        ],
        [
            [
                item["uf"],
                sinal(item["vao_turno2_pp"]),
                milhar(item["eleitorado_tse_2026"]),
                milhar(item["equivalente_sobre_eleitorado"]),
                milhar(item["equivalente_sobre_validos_2022"]),
            ]
            for item in dados["ordem_de_grandeza"]
        ],
    )
    h += (
        '<p class="boundary">Ordem de grandeza, não projeção de votos. A conta aplica '
        "o vão percentual a um universo fixo, ignora comparecimento, abstenção e "
        "margem, e não afirma que esses eleitores estejam disponíveis. Serve para "
        "dimensionar a agenda, não para prometer resultado.</p>"
    )
    return h


def senado(dados, table):
    valores = achado(dados, "senado_da_direita_atras_do_topo")["valores"]
    h = bloco("sudeste-senado", "Nenhum senador da direita puxa o topo da chapa.")
    linhas = []
    for uf in UFS:
        dado = valores[uf]
        bloco_senado = dados["estados"][uf]["senado"]
        pagina = bloco_senado["paginas"]["voto1"][0]
        linhas.append(
            [
                uf,
                f"{curto(dado['candidato'])} {dado['voto1_pct']}%",
                f"{dado['flavio_turno1_pct']}%",
                f"{dado['distancia_pp']} pp",
                f"{curto(bloco_senado['segunda_vaga']['nome'])} "
                f"{bloco_senado['segunda_vaga']['valor']}%",
                f"{num(bloco_senado['nao_escolha_sobre_dois_votos'], 1)}%",
                ref_gov(uf, pagina, f"p. {pagina}"),
            ]
        )
    h += table(
        [
            "Estado",
            "Melhor 1º voto da direita",
            "Flávio no 1º turno",
            "Distância",
            "Segunda vaga, por alcance",
            "Não escolha nos dois votos",
            "Fonte",
        ],
        linhas,
    )
    h += (
        "<p>A régua honesta compara o primeiro voto de senador com o primeiro turno "
        "presidencial: as duas perguntas repartem o voto entre muitos nomes. Mesmo "
        "assim, a melhor candidatura de direita ao Senado fica <strong>22 pontos "
        "atrás de Flávio em São Paulo, 25 em Minas e 27 no Rio</strong>. Nenhuma "
        "delas puxa o topo da chapa no Sudeste; é o topo que puxa a chapa. Contra o "
        "segundo turno presidencial, que é binário, qualquer senador ficaria abaixo "
        "por construção, e o número mediria o formato da pergunta.</p>"
    )
    segunda = {uf: dados["estados"][uf]["senado"]["segunda_vaga"] for uf in UFS}
    h += (
        "<p><strong>São duas vagas em cada um dos três estados</strong>, e o eleitor "
        "responde dois votos. Isso muda o cálculo da chapa: a segunda vaga está "
        "aberta nos três. Em Minas, "
        f"{curto(segunda['MG']['nome'])} e {curto(segunda['MG']['terceiro'])} "
        f"empatam em {segunda['MG']['valor']}%. No Rio, "
        f"{curto(segunda['RJ']['nome'])} e {curto(segunda['RJ']['terceiro'])} empatam "
        f"em {segunda['RJ']['valor']}%. Em São Paulo, "
        f"{segunda['SP']['distancia_para_terceiro_pp']} pontos separam "
        f"{curto(segunda['SP']['nome'])} de {curto(segunda['SP']['terceiro'])}.</p>"
    )
    h += (
        "<aside><b>Coletado e não publicado, no Senado.</b>"
        "Não há pergunta de conhecimento das candidaturas em nenhum dos três "
        "relatórios estaduais. Não há rejeição ao Senado: a rejeição só existe para o "
        "governo do estado. E não há cruzamento do voto de 2022 com o de 2026. Sem "
        "conhecimento e sem rejeição, o relatório mede voto declarado e não mede teto "
        "nem piso de cada candidatura à única casa do Congresso que o eleitor renova "
        "em duas vagas.</aside>"
    )
    return h


def regua(dados, table):
    contraste = dados["regional_contra_estadual"]
    nacional = contraste["recorte_nacional"]
    media = contraste["media_estadual"]
    h = bloco("sudeste-regua", "Recorte regional contra média estadual.")
    h += table(
        ["Régua", "Lula", "Flávio", "Diferença", "Campo", "Base", "Fonte"],
        [
            [
                "Recorte Sudeste do levantamento nacional",
                f"{nacional['lula']}%",
                f"{nacional['flavio']}%",
                f"{sinal(nacional['diferenca_pp'])} pp",
                nacional["campo"],
                milhar(nacional["base"]),
                ref_nac(nacional["fonte"]["pagina"]),
            ],
            [
                "Média das três estaduais, peso do eleitorado TSE",
                f"{num(media['lula'])}%",
                f"{num(media['flavio'])}%",
                f"{sinal(media['diferenca_pp'], 2)} pp",
                media["campo"],
                milhar(sum(dados["estados"][uf]["n"] for uf in UFS)),
                " · ".join(
                    ref_pres(PAGINA_PRES[uf], f"{uf} p. {PAGINA_PRES[uf]}")
                    for uf in UFS
                ),
            ],
        ],
    )
    h += (
        f"<p>As três estaduais cobrem {num(contraste['cobertura_do_eleitorado_pct'])}% "
        "do eleitorado do Sudeste, com pesos condicionais de "
        + ", ".join(
            f"{num(100 * peso)}% para {uf}"
            for uf, peso in media["pesos_condicionais"].items()
        )
        + f". A diferença entre as duas réguas é de "
        f"{num(contraste['contraste']['diferenca_das_diferencas_pp'], 3)} ponto, com "
        f"margem de {num(contraste['contraste']['margem_pp'])} pontos e intervalo de "
        f"95% de {num(contraste['contraste']['ic95'][0])} a "
        f"{num(contraste['contraste']['ic95'][1])}. <strong>As duas réguas não se "
        "separam.</strong> Campos, desenhos e ponderações diferentes bastam para "
        "explicar o que sobra.</p>"
    )
    h += (
        "<p><strong>O Espírito Santo implicado por essa diferença não é "
        "publicável.</strong> A álgebra devolveria "
        f"{num(contraste['es_implicado']['lula'])} para Lula e "
        f"{num(contraste['es_implicado']['flavio'])} para Flávio, e esse resíduo não "
        "mede o estado. Os campos são diferentes, o recorte regional é ponderado pelo "
        "desenho nacional e não pela soma de quatro amostras estaduais, e os quatro "
        "valores publicados são arredondados a inteiro. Como o peso capixaba é de "
        f"{num(contraste['peso_es_no_sudeste_pct'])}% do Sudeste, cada ponto de erro "
        "regional é amplificado por mais de vinte ao ser atribuído ao estado. Quem "
        'quiser explorar hipóteses tem o <a href="#simulador-es">simulador desta '
        "página</a>, que mantém SP, RJ e MG nos pontos publicados e deixa a faixa "
        "capixaba livre.</p>"
    )
    return h


LEITURA_DA_PAUTA = {
    "SP": "A pauta paulista é material e cara. A operação sobre a infiltração do PCC "
    "no transporte só se tornou pública em 17/09, <strong>sete dias depois de o "
    "campo estadual fechar</strong>. A ressalva vem antes da conclusão: o "
    "questionário estadual não poderia ter perguntado sobre ela. As outras três "
    "pautas abaixo são anteriores ao campo e também não viraram pergunta.",
    "RJ": "No Rio está a moldura de imprensa mais dura para o presidenciável. Um "
    "título liga o uso da expressão rachadinha, no mesmo relatório que cita "
    "Flávio Bolsonaro, à cassação de um ex-deputado pelo tribunal eleitoral; "
    "outro registra que vínculos com o crime superaram o caso Master nos ataques "
    "da disputa estadual. Ao lado deles, pautas que cobram o governo do estado. O "
    "questionário carioca não pergunta sobre nenhuma das duas famílias.",
    "MG": "Em Minas a pauta pesa sobre nomes da própria direita: as contas do governo "
    "Zema, a promessa de IPVA de Cleitinho contra o entendimento do STF e o "
    "episódio do deputado investigado. E um título registra, por outro caminho, "
    "o movimento que esta camada mede: os candidatos ao governo mineiro se "
    "descolam dos presidenciáveis no horário eleitoral.",
    "ES": "O Espírito Santo aparece cinco vezes no noticiário do grupo no período, "
    "duas delas fora de política. Ausência em uma busca não prova ausência de "
    "cobertura: a imprensa capixaba tem casa própria, fora do alcance deste "
    "levantamento.",
}
TITULOS_DA_PAUTA = {
    "SP": (
        "Infiltração do PCC",
        "Rota Mogiana",
        "CPTM vai ressarcir",
        "Sabesp encerra",
    ),
    "RJ": (
        "TRE usa 'rachadinha'",
        "Vínculos com o crime",
        "Rio pede à União",
        "Contas do RJ perdem",
    ),
    "MG": (
        "Contas de Zema",
        "Promessa de Cleitinho",
        "Cleitinho é carregado",
        "Candidatos ao Governo de MG se descolam",
    ),
    "ES": (
        "Quaest mostra Ricardo Ferraço",
        "Alemanha deve investir",
        "Faculdade, agronegócio",
    ),
}


def pauta(cobertura, table):
    h = bloco(
        "sudeste-pauta",
        "O que o contratante publicou, e o que a pesquisa perguntou.",
    )
    h += (
        f"<p>{escape(cobertura['pergunta'])} Entre "
        f"{data_curta(cobertura['periodo']['inicio'])} e "
        f"{data_curta(cobertura['periodo']['fim'])} de 2026 foram registrados "
        f"{cobertura['total_itens']} títulos nos quatro estados: "
        + ", ".join(
            f"{quantos} em {uf}" for uf, quantos in cobertura["itens_por_uf"].items()
        )
        + ". Nos três questionários estaduais, o número de perguntas sobre qualquer "
        "dessas pautas é <strong>zero</strong>. Os instrumentos medem voto, "
        "rejeição, decisão, motivação e aprovação do governador, e nada mais.</p>"
    )
    for uf in ("SP", "RJ", "MG", "ES"):
        h += f"<h4>{uf} · {NOME_UF[uf]}</h4><p>{LEITURA_DA_PAUTA[uf]}</p><ul>"
        for trecho in TITULOS_DA_PAUTA[uf]:
            h += link_de_pauta(item_de_pauta(cobertura, uf, trecho))
        h += "</ul>"
    h += table(
        ["Pauta material", "Valor", "Devedor", "Destinatário"],
        [
            [
                f"{uf} · {escape(item['pauta'])}",
                escape(item["valor"] or "Sem valor no título"),
                escape(item["devedor"]),
                escape(item["destinatario"]),
            ]
            for uf, itens in cobertura["pautas_materiais"].items()
            for item in itens[:2]
        ],
    )
    h += (
        '<p class="boundary">Este levantamento mede o que os veículos do grupo '
        "publicaram, não o que deixaram de publicar, e <strong>não afirma que "
        "qualquer veículo escondeu pauta</strong>. Correlação entre pauta publicada e "
        "pergunta ausente não estabelece intenção. O que ela mostra é uma escolha de "
        "instrumento: quatro semanas de assunto material nos quatro estados, e nenhum "
        "item convertido em pergunta. O que resolveria é o instituto publicar o "
        "critério pelo qual um fato entra no questionário.</p>"
    )
    return h


def rota(dados, table):
    mg = carrega("mg_082026_camada2.json")
    sp = carrega("sp_092026_camada2.json")
    minerio = next(c for c in mg["corredores"] if c["slug"] == "minerio")
    vao = {uf: dados["estados"][uf]["vao"]["turno2"]["vao_pp"] for uf in UFS}
    h = bloco("sudeste-rota", "O que fazer. Juízo editorial declarado.")
    h += (
        '<p class="boundary">O que vem abaixo é <strong>juízo editorial desta '
        "casa</strong>, não resultado de pesquisa. Cada movimento traz o número e a "
        "página ao lado. Não há datas, não há promessa de efeito, e o capítulo "
        "termina com o achado que contraria a própria recomendação.</p>"
    )
    h += table(
        ["Prioridade", "Movimento", "Número que o sustenta"],
        [
            [
                "1 · Minas Gerais",
                "Agenda conjunta com Cleitinho e pedido explícito de voto casado, "
                "corredor por corredor.",
                f"Maior vão do Sudeste, {sinal(vao['MG'])} pontos, e o maior "
                "vazamento medido: 25% do eleitor de Cleitinho votam em Lula e 29% "
                f"não votam em Flávio. {ref_pres(21, 'p. 21')}",
            ],
            [
                "2 · São Paulo",
                "Disputar de volta o voto que sai de Tarcísio para outras direitas "
                "antes de disputar o que sai para Lula.",
                "41% do eleitorado de Tarcísio fora de Flávio no 1º turno, dos quais "
                f"8 pontos com Cury e 12 com Lula. {ref_pres(4, 'p. 4')}",
            ],
            [
                "3 · Rio de Janeiro",
                "Flávio é o carregador, não o carregado: a chapa estadual sobe com "
                "ele, e não o contrário.",
                f"Vão de {sinal(vao['RJ'])} pontos, o único sinal invertido do "
                f"Sudeste. {ref_gov('RJ', 38, 'p. 38')}",
            ],
            [
                "4 · Senado",
                "Chapa casada nas duas vagas, com o topo emprestando voto ao Senado.",
                "Melhor primeiro voto da direita 22 pontos atrás de Flávio em SP, "
                "25 em MG e 27 no RJ.",
            ],
        ],
    )
    h += (
        "<h4>Minas: onde a agenda conjunta rende mais</h4>"
        "<p>O índice dos carregadores já publicado mostra que Cleitinho fez "
        f"{num(mg['estado']['cleit'])}% e Bolsonaro {num(mg['estado']['bol1'])}% no "
        "mesmo dia e na mesma urna de 2022: ele não é um puxador maior, é um puxador "
        "complementar. O Corredor do Minério concentra a convergência, com "
        f"{minerio['resumo']['municipios']} municípios, "
        f"{milhar(minerio['resumo']['eleitores'])} eleitores, índice "
        f"{minerio['resumo']['iC']} para Cleitinho, e uma pauta com valor, devedor e "
        "destinatário: a cobrança de R$ 17,7 bilhões de CFEM à Vale, dos quais cerca "
        "de R$ 3,2 bilhões iriam a municípios mineiros. "
        '<a class="refs" href="mg_082026.html">Atlas de Minas</a></p>'
    )
    h += (
        "<h4>São Paulo: o estoque já está localizado</h4>"
        "<p>A camada paulista estima "
        f"{milhar(sp['micro']['estado']['estoque_votos_total'])} votos de eleitores "
        "que hoje escolhem Tarcísio e não escolhem Flávio, "
        f"{num(sp['micro']['estado']['estoque_pct'])}% do eleitorado de Tarcísio de "
        "2022, com densidade seguindo o voto de Rodrigo Garcia. O único nome da "
        "direita acima do topo da chapa em todo o estado é Marcos Pontes, com "
        f"{num(sp['carregadores']['estado']['pontes'])}% contra "
        f"{num(sp['carregadores']['estado']['bolsonaro_1t'])}% de Bolsonaro no "
        "primeiro turno de 2022. "
        '<a class="refs" href="sp_092026.html">Atlas de São Paulo</a></p>'
    )
    h += (
        "<h4>O que cobrar do instituto</h4>"
        "<p>Uma tabela encerra metade da discussão deste capítulo: a <strong>matriz "
        "completa de voto para governador contra voto para presidente e contra voto "
        "para senador</strong>, por estado, com bases brutas, bases ponderadas e os "
        "pesos finais. Sem ela, a fidelidade de base do segundo turno estadual "
        "continua sendo hipótese nossa, e a amplitude entre as priors continua "
        "valendo até "
        f"{num(dados['transferencia']['RJ']['gov2_pres2']['robustez']['amplitude_entre_priors_pp'])} "
        "pontos.</p>"
    )
    return h


def contraprova(dados, table):
    rj = achado(dados, "rj_sinal_invertido")
    es = achado(dados, "es_outro_metodo")
    inverso = dados["estados"]["MG"]["vao"]["inverso_turno2"]
    rj_vao = dados["estados"]["RJ"]["vao"]["turno2"]
    pl = {
        uf: FIG.indice_de_recortes(dados["estados"][uf])[("partido", "PL")]
        for uf in UFS
    }
    h = bloco("sudeste-contraprova", "Contraprova: o que contraria a tese.")
    h += (
        "<p>O padrão de prova é o mesmo para o achado favorável e para o "
        "desfavorável. Os cinco pontos abaixo enfraquecem a leitura deste capítulo e "
        "ficam com o mesmo destaque dos outros.</p>"
    )
    h += table(
        ["Achado", "O que ele diz", "Fonte"],
        [
            [
                "O sinal inverte no Rio",
                "No Rio o presidenciável tem mais voto que o candidato do próprio "
                f"partido ao governo: Douglas Ruas marca "
                f"{rj_vao['governador_pct']}% no segundo turno estadual e Flávio "
                f"Bolsonaro, {rj_vao['presidenciavel_pct']}% no segundo turno "
                "presidencial, na mesma amostra. O déficit do Sudeste não é do "
                "presidenciável em toda parte.",
                ref_gov("RJ", rj["fonte"]["pagina"], "p. 38")
                + " · "
                + ref_pres(rj["fonte_presidente"]["pagina"], "p. 76"),
            ],
            [
                "Dentro do PL, Flávio não depende do palanque",
                "Entre quem declara preferência pelo PL, Flávio bate a candidatura "
                f"de direita ao governo em Minas, {pl['MG']['flavio']} contra "
                f"{pl['MG']['governador']}, e no Rio, {pl['RJ']['flavio']} contra "
                f"{pl['RJ']['governador']}; em São Paulo empatam em "
                f"{pl['SP']['flavio']}. O nome não depende do palanque estadual "
                "dentro da própria base partidária. As bases são pequenas: "
                + ", ".join(
                    f"{pl[uf]['base_governador']} entrevistas em {uf}" for uf in UFS
                )
                + ", e a margem da diferença passa de 16 pontos nas três.",
                ref_gov("MG", 40, "p. 40") + " · " + ref_pres(94, "p. 94"),
            ],
            [
                "O vão inverso de Minas é maior que o direto",
                f"Lula marca {inverso['governador_pct']} e Patrus Ananias, "
                f"{inverso['presidenciavel_pct']}, no mesmo par de perguntas: vão "
                f"inverso de {sinal(inverso['vao_pp'])} pontos, maior que os "
                f"{sinal(dados['estados']['MG']['vao']['turno2']['vao_pp'])} do lado "
                "direito. Lula também rende acima da própria chapa estadual.",
                ref_gov("MG", 40, "p. 40") + " · " + ref_pres(94, "p. 94"),
            ],
            [
                "O Espírito Santo é outro método",
                "No único estado do Sudeste sem pesquisa do mesmo instituto, a "
                "candidatura de direita ao governo perde para o centro no primeiro "
                "turno, com Ferraço em 43 contra 33 de Pazolini, e Flávio em 35. Nada "
                "disso é comparável com o Datafolha e nada disso entra em média.",
                f"Real Time Big Data · ES-01967/2026 · vão de "
                f"{sinal(es['vao_turno2_pp'])} pontos",
            ],
            [
                "Em Minas a pauta pesa sobre a própria direita",
                "Os títulos do período em Minas cobram as contas do governo Zema, a "
                "promessa de IPVA de Cleitinho e o governador em exercício. Uma "
                "agenda conjunta importa a fatura dessa pauta junto com o índice do "
                "carregador.",
                '<a class="refs" href="#sudeste-pauta">Cobertura por estado</a>',
            ],
        ],
    )
    return h


LIMITES = (
    "O vão é teto endereçável, não previsão: votar no governador não torna o eleitor "
    "disponível para o presidenciável.",
    "Cargos, cédulas e incentivos são diferentes. Diferença entre cargos não prova "
    "inconsistência do instituto.",
    "Sem microdados, a igualdade dos pesos individuais entre as perguntas não é "
    "demonstrável; só a igualdade das bases ponderadas.",
    "As amostras estaduais e o recorte regional do levantamento nacional têm campos "
    "e desenhos diferentes.",
    "O Espírito Santo entra com outro instituto e outro método, e não fecha a conta "
    "do Sudeste.",
    "As margens são calculadas sob amostragem aleatória simples. O efeito do desenho "
    "não é publicado.",
    "As linhas medidas vêm do texto corrido dos relatórios, arredondadas a inteiro. "
    "O ajuste proporcional iterativo é estimativa e não recupera microdados.",
)
DISCREPANCIAS = (
    (
        "Situação A e Situação B no anexo presidencial",
        "A Situação A do anexo é o cenário com Pablo Marçal e a Situação B é o "
        "cenário sem ele, que é o que reproduz o placar divulgado. O rótulo não diz "
        "isso: a leitura sai da presença da linha de Marçal, conferida pelo script.",
        "Esta camada usa a Situação B no primeiro turno e preserva a A em campo "
        "próprio. Em Minas a escolha muda o placar do primeiro turno de 38 × 34 para "
        "37 × 35.",
    ),
    (
        "Partição fechada varia por estado",
        "Renda cobre de 95,93% a 97,08% das bases e nunca fecha, porque recusa e não "
        "sabe existem no cartão e não ganham coluna. Partido de preferência fecha em "
        "São Paulo e em Minas e cobre 97,18% no Rio. Religião cobre de 64,70% a "
        "81,81%.",
        "Agregar um indicador ao estado por renda ou por religião inventa cobertura. "
        "Esta camada só recompõe por partição fechada, medida estado a estado.",
    ),
    (
        "Registro duplo por relatório estadual",
        "Cada estado carrega um registro estadual e um federal: SP-04189 e BR-03904, "
        "RJ-09217 e BR-06361, MG-01611 e BR-03022. Número com prefixo BR não "
        "significa amostra nacional.",
        "Nenhuma dessas amostras entra em média nacional.",
    ),
)


def limites(dados, table):
    provas = dados["provas_de_leitura"]
    h = bloco("sudeste-limites", "Limites deste capítulo.")
    h += "<ul>" + "".join(f"<li>{texto}</li>" for texto in LIMITES) + "</ul>"
    h += (
        f"<p><strong>Conferência da extração:</strong> {milhar(provas['total'])} "
        "recomposições por sexo e por natureza do município, nas tabelas dos anexos "
        f"dos três estados. O pior resíduo foi de {num(provas['pior_residuo_pp'])} "
        f"ponto, abaixo do limite de {num(provas['limite_pp'], 1)} que o "
        "arredondamento das células e dos totais explica, e nenhuma recomposição "
        "passou de 1,05 ponto. Isso confere a leitura das tabelas; não certifica o "
        "campo nem testa as relações conjuntas.</p>"
    )
    h += table(
        ["Discrepância documental", "O que os documentos mostram", "Efeito"],
        [list(linha) for linha in DISCREPANCIAS],
    )
    h += (
        "<p>Vão não é transferência, e nenhum número deste capítulo desloca a "
        "conclusão do dossiê, que continua sendo a sensibilidade do placar nacional "
        'à <a href="#renda">régua de renda da PNAD</a>.</p>'
    )
    return h


def fonte_es():
    """Item da seção de fontes: instituto, ficha, registros, hash e origem.

    Os PDFs da Real Time não são republicados aqui. A página cita a URL
    pública de onde cada arquivo foi baixado, com o SHA-256 ao lado, para
    que o leitor confira a integridade contra o original do próprio veículo.
    """
    es = carrega(f"{SLUG}_sudeste.json")["espirito_santo"]
    campo = es["campo"].replace("–", " a ")
    arquivos = []
    for nome, ficha in es["fontes"].items():
        escopo = "Presidência" if "presidente" in nome else "Governo e Senado"
        arquivos.append(
            f'<a href="{ficha["url"]}">{escopo}, {ficha["registro_tse"]}</a> '
            f'<span class="refs">{ficha["paginas"]} páginas · SHA-256 '
            f'{ficha["sha256"][:16]}…</span>'
        )
    return (
        "<li>Espírito Santo: <strong>Real Time Big Data</strong> para Real Time "
        f"Mídia, campo de {campo}, {milhar(es['n'])} entrevistas, registros "
        f"{es['registros']['estadual']} (governo) e "
        f"{es['registros']['presidencial']} (Presidência). Íntegras públicas de "
        "onde cada arquivo foi baixado: "
        + " · ".join(arquivos)
        + ". Cópias preservadas em <code>data/originals/es_092026/</code>; "
        "não republicamos os arquivos do instituto aqui.</li>"
    )


def render(table, figure, fmt=None):
    """Monta o capítulo. `fmt` é aceito por simetria com o gerador do dossiê."""
    dados = carrega(f"{SLUG}_sudeste.json")
    cobertura = carrega(f"{SLUG}_cobertura_sudeste.json")
    partes = [
        abertura(dados, table, figure),
        transferencia(dados, table, figure),
        vao_por_recorte(dados, table, figure),
        senado(dados, table),
        regua(dados, table),
        pauta(cobertura, table),
        rota(dados, table),
        contraprova(dados, table),
        limites(dados, table),
        '<p class="table-source">Reproduzir: '
        "<code>python3 scripts/datafolha-21092026-sudeste.py</code> e "
        "<code>python3 scripts/datafolha-21092026-cobertura-sudeste.py</code>, "
        "seguidos pelo gerador do dossiê. Dados: "
        f'<a href="assets/{SLUG}_sudeste.json">camada do Sudeste em JSON</a> · '
        f'<a href="assets/{SLUG}_sudeste.csv">placar dos quatro estados em CSV</a> · '
        f'<a href="assets/{SLUG}_cobertura_sudeste.json">cobertura do contratante '
        "em JSON</a>.</p></section>",
    ]
    return "".join(partes)
