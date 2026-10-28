"""Relatório geográfico e de auditoria: apresentação gerada dos dados verificados."""

import math
from html import escape

from .figuras import barras_faixas, mapa, num, regua_correlacao
from .pagina_auditoria import render as auditoria_html
from .pagina_auditoria import tabela
from .pagina_territorio import render as territorio_html


def participacao(rows):
    return 100 * sum(r["lula"] for r in rows) / sum(r["validos"] for r in rows)


def topo(rows, campo):
    rs = sorted(
        [r for r in rows if r[campo] is not None], key=lambda r: (-r[campo], r["ibge"])
    )
    corte = rs[max(0, math.ceil(len(rs) * 0.1) - 1)][campo]
    return [r for r in rs if r[campo] >= corte], corte


def fontes(d):
    p = d["pnad"]
    return f"""<section class="chapter" id="fontes"><span class="sec-no">07 · Fontes e método</span><h2>Uma hipótese forte precisa<br><em>de uma base conferível.</em></h2>
    <ul class="source-list"><li><b>Voto:</b> totalização municipal do TSE, 2º turno de 25/10/2026. Versão nacional gerada em {escape(d['meta_tse']['versao_nacional_gerada_brt'])}. Brasil sem exterior. Cortes calculados nas contagens inteiras, sem arredondar percentuais.</li>
    <li><b>Renda:</b> PNAD Contínua anual 2025, visita 1, pessoas de 16 anos ou mais, peso V1032, rendimento domiciliar efetivo VD5001. Preços de {escape(p['mes_precos'])}; salário mínimo de R$ {num(p['salario_minimo_2026'])}. Perfis estimados por UF × escolaridade × situação urbana/rural, combinados com o cadastro eleitoral. Não são estimativas oficiais de renda municipal nem a renda medida dos eleitores. A renda de um domicílio não equivale à renda por pessoa.</li>
    <li><b>Agregação econômica:</b> médias dos indicadores dos locais, ponderadas pelos aptos. “Mediana estimada dos locais” é a média dessas medianas, não a mediana conjunta do município. Nas zonas, pesos dos locais do 2º turno. Ausência de renda não vira zero. <a href="assets/politize/dados/pnad_renda.json">Tabela PNAD e substituições de células pequenas</a>.</li>
    <li><b>Progresso social:</b> <a href="https://ipsbrasil.org.br/relatorios">IPS Brasil 2026</a>, 5.570 municípios, 57 indicadores sociais e ambientais, dados disponíveis até 20/02/2026. Os indicadores têm anos distintos; 12 não foram atualizados desde a edição anterior. Não é IDHM, não mede riqueza e não permite discriminar zonas dentro da cidade. Boa Esperança do Norte/MT não tem IPS nesta edição.</li>
    <li><b>IDHM:</b> o <a href="https://www.undp.org/pt/brazil/publications/radar-idhm-evolucao-do-idhm-e-de-seus-componentes-periodo-de-2012-2024">Radar PNUD publicado em 2026</a> alcança 2024 para estados e regiões metropolitanas. A série municipal disponível no Atlas continua baseada no Censo 2010. Ela não foi usada para chamar um lugar de rico em 2026; o relatório adota o IPS atual, com seu próprio nome e significado.</li>
    <li><b>Homicídios:</b> <a href="https://www.ipea.gov.br/atlasviolencia/">Atlas da Violência/Ipea, SIM</a>, 2024, séries 20 (taxa) e 328 (número), óbitos por residência, CID-10 X85–Y09 e Y35. Sem valor publicado = sem dado, nunca zero. Taxas de pequenos municípios podem oscilar com poucos casos. <a href="https://www.ipea.gov.br/dados-api/series-values/20/4">Série original</a>.</li>
    <li><b>Presença de grupos:</b> <a href="https://forumseguranca.org.br/wp-content/uploads/2025/11/cartografias-violencia-amazonia-2025.pdf">Cartografias da Violência na Amazônia 2025, FBSP/Instituto Mãe Crioula</a>, quadros municipais, pesquisa novembro/2024 a setembro/2025. Os 343 casamentos do acervo são um recorte documental; o quadro publicado totaliza 344. Cobertura restrita à Amazônia Legal. O cadastro não representa ausência comprovada fora da lista, domínio de bairro ou coação eleitoral.</li>
    <li><b>Mapas:</b> malha mínima das UFs e sedes municipais do IBGE. Círculos nas sedes, área proporcional à diferença absoluta de votos. As sedes não representam os limites municipais. Nas capitais, cada zona inclui somente seus locais dentro da capital; BUs e resultados oficiais municipais foram reconciliados.</li></ul>
    <details><summary>Como calculamos correlações e faixas</summary><p>Pearson mede associação linear; Spearman usa posições. A correlação principal dá o mesmo peso a cada município; uma alternativa pondera pelos votos válidos. Para a leitura dentro da UF, subtraímos de cada variável a média de sua UF e correlacionamos os resíduos. Nas zonas, subtraímos a média de cada capital. É controle descritivo, não efeito causal.</p><p>Quintis são calculados sobre municípios com dados; empates permanecem na mesma faixa. As barras somam votos em cada faixa. No grupo superior de 10%, incluímos todos os empates no valor de corte. Falhas de cobertura e a dependência espacial limitam a inferência: não publicamos valores-p ou intervalos baseados em municípios independentes.</p><p>Não é possível deduzir o voto individual pelo endereço, pela renda, por cor/raça ou pela presença de organizações criminosas. Associação territorial não identifica quem votou em quem.</p></details>
    <p><a href="assets/analise_realidade_eleicao/municipios.csv" download>Municípios (CSV)</a> · <a href="assets/analise_realidade_eleicao/zonas.csv" download>Zonas das capitais (CSV)</a> · <a href="assets/analise_realidade_eleicao/dados.json">Dados e método (JSON)</a> · <a href="assets/analise_realidade_eleicao/auditoria.json">Auditoria e triagem (JSON)</a></p>
    <p class="small">Reprodução: scripts/analise-realidade-dados.py, scripts/analise-realidade-auditoria.py e scripts/analise-realidade-build.py. Fontes originais, hashes, equivalências de nomes e notas de auditoria preservados em analysis/analise_realidade_eleicao/ e data/originals/analise_realidade_eleicao/.</p></section>"""


def corpo(d, a, t):
    ms, stats = d["municipios"], d["estatisticas"]["municipios"]
    maxd = max(m["diferenca"] for m in ms if m["ibge"] in d["cortes"]["30"])
    rich, richcut = topo(ms, "renda_mais5")
    high, highcut = topo(ms, "ips")
    fbsp = [m for m in ms if m["crime_fbsp"]]
    h = f"""<header><p class="eyebrow">Arvor Intelligence · 2º turno de 2026 · análise territorial</p>
    <h1>A geografia do voto.<br><em>E o que pede explicação.</em></h1>
    <p class="intro">Renda, desenvolvimento, violência e mudanças entre os turnos. Um retrato dos municípios e das zonas nas capitais, com os dois candidatos à vista e uma trilha de auditoria que vai do padrão estatístico à conferência dos boletins.</p>
    <div class="links"><a href="#mapas">Quatro mapas</a><a href="#renda">Renda e voto</a><a href="#desenvolvimento">Áreas mais favorecidas</a><a href="#seguranca">Violência</a><a href="#capitais">Capitais por zona</a><a href="#auditoria">Auditoria</a></div>
    <div class="hero-stats"><div><strong>{num(len(ms))}</strong><span>municípios · Brasil sem exterior</span></div><div><strong>{num(len(d['zonas']))}</strong><span>zonas nas 27 capitais</span></div><div><strong>{num(len(d['cortes']['10']))}</strong><span>municípios com Flávio abaixo de 10%</span></div><div><strong>{num(stats['homicidios_taxa_100mil']['n'])}</strong><span>municípios com taxa de homicídios</span></div></div></header>
    <section class="chapter" id="mapas"><span class="sec-no">01 · Concentração do voto</span><h2>Onde Flávio ficou<br><em>abaixo de 5, 10, 25 e 30%.</em></h2>
    <p class="deck">Cada ponto é a sede de um município. Quanto maior a área do círculo, maior a diferença absoluta entre os votos dos candidatos. A escala dos círculos é a mesma nos quatro mapas.</p>
    <div class="size-key"><b>Diferença de votos</b><svg viewBox="0 0 180 65" aria-label="Escala de área dos círculos">"""
    for i, v in enumerate((1000, 10000, 50000)):
        radius = 19 * math.sqrt(v / maxd)
        h += f'<circle cx="{30+i*60}" cy="25" r="{radius:.3f}" fill="{ "#ae3428" }" opacity=".6"/><text x="{30+i*60}" y="58" text-anchor="middle" font-size="10">{num(v)}</text>'
    h += '</svg><span>Toque em um ponto para abrir os números.</span></div><div class="map-grid">'
    h += "".join(mapa(ms, t, maxd) for t in (5, 10, 25, 30)) + "</div>"
    h += """<p class="small">Os cortes são cumulativos: um município abaixo de 10% também entra em 25% e 30%. O corte de 5% vazio é um resultado da base, não uma falha do mapa.</p>
    <div id="selecionado" class="selected" aria-live="polite"><h3>Explore um município</h3><p>Selecione um círculo ou busque pelo nome na tabela para ver voto, renda estimada, progresso social e homicídios.</p></div>
    <div class="controls js-only"><label>Buscar município<input id="busca-municipio" type="search" placeholder="Nome ou código IBGE"></label><label>Estado<select id="uf"><option value="">Brasil</option></select></label><label>Corte de Flávio<select id="corte"><option value="100">Todos os municípios</option><option value="5">Abaixo de 5%</option><option value="10">Abaixo de 10%</option><option value="25">Abaixo de 25%</option><option value="30">Abaixo de 30%</option></select></label><label>Ordenar<select id="ordem"><option value="pct_flavio">Menor votação de Flávio</option><option value="diferenca">Maior diferença de votos</option><option value="nome">Nome do município</option></select></label></div>
    <div id="tabela-municipios" class="js-only"></div><div class="pager js-only" id="paginacao"></div>"""
    h += (
        '<details class="static-list"><summary>Os 11 municípios abaixo de 10%, nas contagens exatas</summary>'
        + tabela(
            ["Município", "Flávio", "Lula", "Flávio %"],
            [
                [
                    escape(m["nome"].title()) + "/" + m["uf"],
                    num(m["flavio"]),
                    num(m["lula"]),
                    num(m["pct_flavio"], 2),
                ]
                for m in sorted(ms, key=lambda r: r["pct_flavio"])
                if m["ibge"] in d["cortes"]["10"]
            ],
        )
        + "</details>"
    )
    h += """<p><a href="assets/analise_realidade_eleicao/municipios.csv" download>Baixar a lista completa com os quatro cortes (CSV)</a></p></section>"""
    h += f"""<section class="chapter" id="renda"><span class="sec-no">02 · Renda e geografia</span><h2>Uma associação forte.<br><em>Mas a região muda a leitura.</em></h2><p class="deck">Quanto maior a parcela estimada de baixa renda, maior foi, em geral, o voto municipal em Lula. A correlação cai de {num(stats['renda_ate2']['pearson'],2)} para {num(stats['renda_ate2']['dentro_grupo'],2)} ao retirar as diferenças médias entre estados.</p>
    <div class="duo">{barras_faixas(stats['renda_ate2'],'Parcela estimada com renda domiciliar até 2 SM','%')}{regua_correlacao(stats['renda_ate2'])}</div>
    <p class="note">A PNAD não mede cada município desta base. A estimativa usa escolaridade eleitoral, UF e situação urbana/rural. Uma relação com voto também pode refletir essas variáveis, além da renda. Os valores não descrevem a renda de uma pessoa nem seu voto.</p>
    <h3>Explore os municípios, um a um</h3><div class="controls js-only"><label>Indicador no eixo horizontal<select id="variavel"><option value="renda_ate2">Renda estimada até 2 SM (%)</option><option value="renda_mais5">Renda estimada acima de 5 SM (%)</option><option value="superior">Superior completo no cadastro (%)</option><option value="ips">IPS Brasil 2026</option><option value="homicidios_taxa_100mil">Homicídios por 100 mil (2024)</option><option value="rural_pct">Eleitorado em locais rurais (%)</option></select></label><label>Comparação<select id="escala"><option value="bruta">Valores observados</option><option value="uf">Desvios da média da UF</option></select></label></div><div id="coeficientes" class="coef-grid js-only"></div><div id="dispersao" class="scatter js-only"></div><p id="scatter-caption" class="small js-only"></p></section>"""
    h += f"""<section class="chapter" id="desenvolvimento"><span class="sec-no">03 · A hipótese das áreas favorecidas</span><h2>O perfil favorecido<br><em>não tem um voto único.</em></h2>
    <p class="deck">Entre os {num(len(rich))} municípios no grupo superior de renda estimada acima de 5 salários, Lula recebeu {num(participacao(rich),1)}% dos votos. Nos {num(len(high))} municípios no grupo superior do IPS, recebeu {num(participacao(high),1)}%. São conceitos distintos, e nenhum identifica uma “elite” individual.</p>
    <div class="duo">{barras_faixas(stats['renda_mais5'],'Parcela estimada acima de 5 SM','%')}{barras_faixas(stats['ips'],'IPS Brasil 2026',' pontos')}</div>
    <p class="small">Grupo superior = aproximadamente 10% dos municípios, incluindo empates: renda acima de 5 SM ≥ {num(richcut,2)}%; IPS ≥ {num(highcut,2)}. Renda domiciliar acima de 5 SM significa acima de R$ {num(d['pnad']['salario_minimo_2026']*5)}, não renda individual. “IPS alto” aqui é posição relativa, não a faixa oficial “IDHM muito alto”.</p>
    <h3>Entre os maiores IPS, os resultados variam</h3>"""
    h += tabela(
        ["Município", "IPS 2026", "Lula", "Flávio"],
        [
            [
                escape(r["nome"].title()) + "/" + r["uf"],
                num(r["ips"], 2),
                num(r["pct_lula"], 2) + "%",
                num(r["pct_flavio"], 2) + "%",
            ]
            for r in sorted(high, key=lambda r: -r["ips"])[:12]
        ],
    )
    h += "</section>"
    h += f"""<section class="chapter" id="seguranca"><span class="sec-no">04 · Violência e presença criminal</span><h2>Violência, território e voto:<br><em>três perguntas diferentes.</em></h2><p class="deck">A associação municipal entre taxa de homicídios e voto em Lula é {num(stats['homicidios_taxa_100mil']['pearson'],2)} no país. Dentro das UFs, fica em {num(stats['homicidios_taxa_100mil']['dentro_grupo'],2)}, próxima de zero. O contraste regional pesa mais do que a relação linear dentro dos estados.</p>
    <div class="duo">{barras_faixas(stats['homicidios_taxa_100mil'],'Homicídios por 100 mil habitantes','')}{regua_correlacao(stats['homicidios_taxa_100mil'])}</div>
    <h3>Municípios com presença documentada de grupos armados</h3><p>No recorte do FBSP conciliado pelo acervo, {num(len(fbsp))} municípios têm presença citada. Somados, deram {num(participacao(fbsp),2)}% a Lula e {num(100-participacao(fbsp),2)}% a Flávio. Lula teve maioria em {num(sum(r['lula']>r['flavio'] for r in fbsp))} deles. A presença documentada não forma um bloco eleitoral uniforme.</p>"""
    h += tabela(
        ["UF", "Municípios citados", "Lula", "Flávio"],
        [
            [
                uf,
                num(len(rs)),
                num(participacao(rs), 2) + "%",
                num(100 - participacao(rs), 2) + "%",
            ]
            for uf in sorted({r["uf"] for r in fbsp})
            if (rs := [r for r in fbsp if r["uf"] == uf])
        ],
    )
    h += '<p class="small">Fora dos municípios citados, a classificação é “sem documentação nesta base”, não “sem crime organizado”. Não há comparação causal entre presença e ausência.</p>'
    h += territorio_html(t) + "</section>"
    h += """<section class="chapter" id="capitais"><span class="sec-no">05 · Dentro das capitais</span><h2>A cidade muda<br><em>de zona para zona.</em></h2><p class="deck">A renda estimada e a escolaridade dos locais variam dentro da capital. Explore as zonas em ordem de perfil econômico e compare os votos dos dois candidatos.</p><div class="controls js-only"><label>Capital<select id="capital"></select></label><label>Ordenar zonas<select id="ordem-zona"><option value="renda_mais5">Maior parcela acima de 5 SM</option><option value="renda_ate2">Maior parcela até 2 SM</option><option value="superior">Maior escolaridade superior</option><option value="pct_lula">Maior voto em Lula</option><option value="zona">Número da zona</option></select></label></div><div id="capital-resumo" class="js-only"></div><div class="key"><span>Lula</span><span>Flávio</span></div><div id="zonas-barras" class="zone-bars js-only"></div><div id="zonas-tabela" class="js-only"></div><p class="note">A zona pode abranger vários municípios: aqui entram apenas os locais dentro da capital selecionada. IPS e homicídios são municipais e não foram replicados como se diferenciassem zonas. Todos os totais das capitais foram conferidos contra a totalização oficial. Renda segue sendo aproximação pelo perfil dos locais, não medição dos moradores.</p><p><a href="assets/analise_realidade_eleicao/zonas.csv" download>Dados das 298 zonas (CSV)</a></p></section>"""
    h += auditoria_html(a) + fontes(d)
    return h
