"""Insere os capitulos da segunda camada em docs/mg_082026.html.

Idempotente: reescreve tudo entre os marcadores camada2. O restante do dossie
continua sendo editado a mao.

Reproducao:
    python3 scripts/mg-082026-camada2.py && python3 scripts/mg-082026-camada2-render.py
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/mg_082026.html"
DATA = ROOT / "docs/assets/mg_082026_camada2.json"
INICIO = "    <!-- camada2:inicio -->"
FIM = "    <!-- camada2:fim -->"

D = json.loads(DATA.read_text(encoding="utf-8"))
EST = D["estado"]


def num(v: float, casas: int = 0) -> str:
    return f"{v:,.{casas}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def pct(v: float, casas: int = 1) -> str:
    return f"{v:.{casas}f}".replace(".", ",") + "%"


def pp(v: float, casas: int = 1) -> str:
    return f"{v:+.{casas}f}".replace(".", ",") + " pp"


def idx(v: float) -> str:
    cls = "up" if v > 100 else ("dn" if v < 100 else "eq")
    return f'<td class="num idx-{cls}">{v:.0f}</td>'


def linha_meso(m: dict) -> str:
    return (
        f"<tr><th scope=row>{escape(m['meso'])}</th>"
        f"<td class=num>{num(m['eleitores'])}</td>"
        f"<td class=num>{pct(m['bol1'])}</td>"
        f"<td class=num>{pp(m['marg'])}</td>"
        f"{idx(m['iC'])}{idx(m['iN'])}{idx(m['iE'])}</tr>"
    )


def linha_cidade(c: dict) -> str:
    virou = (
        '<span class="tag-virou">virou</span>'
        if c["virada"] == "Direita→esquerda"
        else ""
    )
    return (
        f"<tr><th scope=row>{escape(c['mun'])} {virou}</th>"
        f"<td class=num>{num(c['el'])}</td>"
        f"<td class=num>{pct(c['bol1'])}</td>"
        f"<td class=num>{pp(c['marg'])}</td>"
        f"<td class=num>{pp(c['desl'])}</td>"
        f"{idx(c['iC'])}{idx(c['iN'])}{idx(c['iE'])}</tr>"
    )


def corredor(c: dict) -> str:
    r, p = c["resumo"], c["pauta"]
    fatos = "".join(
        f'<li>{escape(t)} <cite><a href="{escape(u)}" rel="noopener">{escape(v)}</a></cite></li>'
        for t, v, u in p["fatos"]
    )
    anc = (
        "".join(
            f"<tr><th scope=row>{escape(a['nome'])}</th><td>{escape(a['partido'])}</td>"
            f"<td>{escape(a['casa'])}</td><td class=num>{num(a['votos_mg'])}</td>"
            f"<td class=num>{pct(a['concentracao_meso_pct'])}</td><td>{escape(a['base'])}</td></tr>"
            for a in c["ancoras"]
        )
        or "<tr><td colspan=6>Nenhum eleito de 2022 do campo tem votação concentrada nesta mesorregião.</td></tr>"
    )
    cidades = "".join(linha_cidade(x) for x in c["cidades"] if x["el"] >= 20000)
    eventos = "".join(f"<li>{escape(e)}</li>" for e in p["eventos"])
    return f"""
        <article class="corridor reveal" id="corr-{c['slug']}">
          <header class="corridor-head">
            <div><p class="kicker">{escape(c['sub'])}</p><h3>{escape(c['nome'])}</h3></div>
            <dl class="corridor-kpi">
              <div><dt>eleitores</dt><dd>{num(r['eleitores'])}</dd></div>
              <div><dt>% de Minas</dt><dd>{pct(r['share_mg'], 2)}</dd></div>
              <div><dt>Bolsonaro 1º turno</dt><dd>{pct(r['bol1'])}</dd></div>
              <div><dt>margem da esquerda</dt><dd>{pp(r['marg'])}</dd></div>
              <div><dt>viradas</dt><dd>{r['viradas']}</dd></div>
            </dl>
          </header>
          <div class="corridor-body">
            <div>
              <p class="corridor-agenda">{escape(p['agenda'])}</p>
              <h4>O que a imprensa mineira publicou</h4>
              <ul class="fatos">{fatos}</ul>
              <h4>Quem sobe no palanque</h4>
              <p>{escape(p['palanque'])}</p>
              <p class="corridor-frase">{escape(p['frase'])}</p>
              <h4>Formato de encontro que a região comporta</h4>
              <ul class="eventos">{eventos}</ul>
              <p class="corridor-alerta"><b>O que não dizer.</b> {escape(p['nao_dizer'])}</p>
              <p class="corridor-juizo"><b>Juízo editorial.</b> {escape(p['juizo'])}</p>
            </div>
            <aside>
              <h4>Índice dos carregadores</h4>
              <div class="idx-cards">
                <div class="{'up' if r['iC'] > 100 else 'dn'}"><b>{r['iC']}</b><span>Cleitinho</span></div>
                <div class="{'up' if r['iN'] > 100 else 'dn'}"><b>{r['iN']}</b><span>Nikolas</span></div>
                <div class="{'up' if r['iE'] > 100 else 'dn'}"><b>{r['iE']}</b><span>Engler</span></div>
              </div>
              <h4>Quem tem base medida na região</h4>
              <div class="scroll-x"><table class="mini">
                <thead><tr><th>eleito em 2022</th><th>partido</th><th>casa</th><th>votos MG</th><th>na meso</th><th>cidade base</th></tr></thead>
                <tbody>{anc}</tbody></table></div>
              <p class="micro">Concentração é a fatia da votação nominal de 2022 do parlamentar que veio da mesorregião de referência do corredor. Situação de candidatura em 2026 não está verificada aqui.</p>
            </aside>
          </div>
          <div class="scroll-x"><table class="corridor-cities">
            <caption>Municípios do corredor com pelo menos vinte mil eleitores</caption>
            <thead><tr><th>município</th><th>eleitores 2026</th><th>Bolsonaro 1T</th><th>margem E 2T</th><th>desloc. 18→22</th><th>Cleitinho</th><th>Nikolas</th><th>Engler</th></tr></thead>
            <tbody>{cidades}</tbody></table></div>
        </article>"""


PARADAS = [
    (
        "Congonhas",
        "minerio",
        "Trocou de lado em 2022 e Cleitinho correu dez pontos à frente de Bolsonaro ali.",
        "Caminhada de romaria no entorno da Basílica do Bom Jesus de Matosinhos.",
    ),
    (
        "Itabira",
        "minerio",
        "É o maior credor individual da cobrança de CFEM, com R$ 822,6 milhões estimados, e trocou de lado em 2022.",
        "Audiência aberta com prefeito e câmara, com o valor devido no painel.",
    ),
    (
        "Mariana",
        "minerio",
        "Bolsonaro fez menos de trinta por cento no 1º turno e os três carregadores rendem acima dele.",
        "Encontro de centro histórico, sem carreata.",
    ),
    (
        "Contagem",
        "metropolitano",
        "Segunda maior cidade do estado, margem apertada e Nikolas passou de vinte por cento dos válidos.",
        "Motociata metropolitana ligando Contagem, Betim e Ibirité.",
    ),
    (
        "Betim",
        "metropolitano",
        "Ficou dentro de cinco pontos em 2022 e recebe o novo campus da UFMG no ano que vem.",
        "Portaria de fábrica e caminhada de comércio, com Nikolas.",
    ),
    (
        "Ribeirão das Neves",
        "metropolitano",
        "É a terceira maior virada do estado em eleitorado e ficou a pouco mais de um ponto.",
        "Feira livre de sábado de manhã.",
    ),
    (
        "Ibirité",
        "metropolitano",
        "Foi decidida por menos de meio ponto e tem deputado federal de base própria na cidade.",
        "Agenda de segurança em base comunitária, com Engler.",
    ),
    (
        "Divinópolis",
        "oeste",
        "Cleitinho fez quase vinte pontos a mais que Bolsonaro ali, no mesmo dia e na mesma urna.",
        "Comício de praça com o senador abrindo e fechando.",
    ),
    (
        "Nova Serrana",
        "oeste",
        "É a maior cidade mais bolsonarista de Minas e o polo calçadista opera com cerca de 30% da capacidade.",
        "Chão de fábrica, com pauta de crédito, energia e importação.",
    ),
    (
        "Ipatinga",
        "aco",
        "A Usiminas desativou o alto-forno 1 e demitiu mais de cem pessoas na usina da cidade.",
        "Portaria de fábrica na troca de turno.",
    ),
    (
        "Governador Valadares",
        "aco",
        "É polo de sete regiões e a região ficou quase empatada, mesmo com a cidade mais à direita que o entorno.",
        "Motociata em avenida larga, mais reunião separada com comércio.",
    ),
    (
        "Juiz de Fora",
        "mata",
        "É o maior município do estado que trocou de lado entre 2018 e 2022, com quase quatrocentos mil eleitores.",
        "A motociata pendente, do aeroporto ao centro.",
    ),
    (
        "Barbacena",
        "mata",
        "Trocou de lado e deslocou nove pontos para a esquerda entre as duas eleições.",
        "Caminhada de comércio de rua, com pauta de fila de saúde.",
    ),
    (
        "Uberlândia",
        "producao",
        "Concentra cerca de 58% das empresas abertas no Triângulo no primeiro trimestre de 2026 e tem margem estreita.",
        "Motociata, onde Bolsonaro fez a primeira de Minas, mais agenda de logística.",
    ),
    (
        "Varginha",
        "producao",
        "Está no centro da cadeia do café que perdeu 34% do valor exportado aos Estados Unidos no semestre.",
        "Encontro de cooperativas, com pauta de tarifa, crédito e frete.",
    ),
    (
        "Montes Claros",
        "vales",
        "Maior cidade do Norte, onde a tarefa declarada é comprimir diferença e não converter região.",
        "Rádio AM e FM regional, mais agenda de água e irrigação.",
    ),
]


def paradas_html() -> str:
    por_nome = {c["mun"]: (c, cor) for cor in D["corredores"] for c in cor["cidades"]}
    linhas = []
    for mun, slug, motivo, formato in PARADAS:
        c, cor = por_nome[mun]
        virou = (
            ' <span class="tag-virou">virou</span>'
            if c["virada"] == "Direita→esquerda"
            else ""
        )
        linhas.append(
            f"<tr><th scope=row>{escape(mun)}{virou}<small>{escape(cor['nome'])}</small></th>"
            f"<td class=num>{num(c['el'])}</td><td class=num>{pct(c['bol1'])}</td>"
            f"<td class=num>{pp(c['marg'])}</td>"
            f"<td>{escape(motivo)}</td><td>{escape(formato)}</td></tr>"
        )
    return "".join(linhas)


trio = D["trio"]
trio_linhas = "".join(
    f"<tr><th scope=row>{escape(x['mun'])}</th><td>{escape(x['meso'])}</td>"
    f"<td class=num>{num(x['el'])}</td><td class=num>{pct(x['bol1'])}</td>"
    f"<td class=num>{pp(x['marg'])}</td>{idx(x['iC'])}{idx(x['iN'])}{idx(x['iE'])}</tr>"
    for x in trio["lista"]
    if x["el"] >= 20000
)

bh = D["bh_zonas"]
bh_max = max(bh, key=lambda r: r["iE"])
bh_min = min(bh, key=lambda r: r["iE"])

CH = f"""{INICIO}
    <section id="carregadores" class="chapter carriers-chapter dark">
      <div class="wrap">
        <div class="chapter-head"><p class="sec-no">12 · carregadores</p><div><h2>Quem puxa voto <em>onde o topo da chapa não puxou.</em></h2><p class="lead">Comparar 41% de um senador com 6% de um deputado estadual não diz nada. A régua abaixo divide o desempenho de cada nome em cada município pela própria média estadual dele, e compara esse número com o mesmo cálculo feito para Bolsonaro no primeiro turno de 2022. Cem significa render exatamente o que Bolsonaro rendeu ali.</p></div></div>
        <div class="carrier-ledger reveal">
          <div><span>Bolsonaro 1º turno</span><b>{pct(EST['bol1'])}</b><small>votos válidos para presidente</small></div>
          <div><span>Cleitinho</span><b>{pct(EST['cleit'])}</b><small>válidos para senador, mesma cédula</small></div>
          <div><span>Nikolas Ferreira</span><b>{pct(EST['niko'])}</b><small>válidos para deputado federal</small></div>
          <div><span>Bruno Engler</span><b>{pct(EST['engler'])}</b><small>válidos para deputado estadual</small></div>
        </div>
        <div class="plain-language">O primeiro achado desmonta um lugar-comum. No mesmo dia e na mesma urna, Cleitinho fez {pct(EST['cleit'])} e Bolsonaro fez {pct(EST['bol1'])}: o senador mais votado do estado correu atrás do candidato a presidente, não à frente. O valor dele não está no volume. Está na geografia.</div>
        <div class="scroll-x reveal"><table class="carrier-table">
          <caption>Índice por mesorregião, ponderado pelo eleitorado de 2026</caption>
          <thead><tr><th>mesorregião</th><th>eleitores</th><th>Bolsonaro 1T</th><th>margem E 2T</th><th>Cleitinho</th><th>Nikolas</th><th>Engler</th></tr></thead>
          <tbody>{''.join(linha_meso(m) for m in D['mesorregioes'])}</tbody></table></div>
        <div class="grid-3 mt reveal">
          <article class="card"><span class="metric gold">130</span><h3>Cleitinho no Oeste</h3><p>É o avesso do mapa de Bolsonaro. Ele rende acima no Oeste, na Central Mineira, nos vales pobres e no cinturão do minério, e rende abaixo no Triângulo, no Sul e na região metropolitana, que já eram território consolidado da direita.</p></article>
          <article class="card"><span class="metric">152</span><h3>Nikolas na metrópole</h3><p>O pico absoluto dele está onde Bolsonaro já era forte, como Nova Serrana e Itajubá, o que faz dele um amplificador de base. A exceção que importa é a periferia metropolitana, onde Bolsonaro ficou perto da metade e Nikolas passou de vinte por cento dos válidos.</p></article>
          <article class="card"><span class="metric red">52</span><h3>Engler nos vales</h3><p>Engler quase não viaja. Sua votação é metropolitana e, dentro de Belo Horizonte, a zona onde ele mais supera Bolsonaro rende índice {bh_max['iE']:.0f} e a onde menos rende {bh_min['iE']:.0f}. A leitura fina por bairro exige o arquivo de seção cruzado com locais de votação, que não está nesta versão.</p></article>
        </div>
        <div class="split mt reveal">
          <div class="chart-shell dark-card">
            <div class="chart-title"><div><p class="kicker">Onde a chapa inteira supera o topo</p><h3>As {trio['municipios']} cidades do trio</h3></div><span>{num(trio['eleitores'])} eleitores</span></div>
            <div class="scroll-x"><table class="carrier-table compact">
              <thead><tr><th>município</th><th>mesorregião</th><th>eleitores</th><th>Bolso 1T</th><th>margem E</th><th>Cleit</th><th>Niko</th><th>Engl</th></tr></thead>
              <tbody>{trio_linhas}</tbody></table></div>
            <p class="chart-note">Municípios em que Cleitinho, Nikolas e Engler superam ao mesmo tempo o desempenho relativo de Bolsonaro. Mostrados os de pelo menos vinte mil eleitores.</p>
          </div>
          <div class="chart-shell dark-card">
            <div class="chart-title"><div><p class="kicker">Limite do índice</p><h3>O que ele não mede</h3></div></div>
            <div class="limit-list">
              <p><b>Não é transferência.</b> São cargos, cédulas e incentivos diferentes, medidos em eleições passadas. O índice mostra alcance territorial comparado, não que o eleitor de um nome siga para outro.</p>
              <p><b>Não é pessoa.</b> A unidade é o município. Nenhuma linha aqui autoriza afirmar comportamento de indivíduo ou de grupo demográfico dentro de uma cidade.</p>
              <p><b>Não é previsão.</b> O denominador é 2022. Estrutura partidária, adversários e contexto econômico mudaram desde então.</p>
            </div>
          </div>
        </div>
        <p class="source-note"><b>Cálculo.</b> {escape(D['meta']['definicao_indice'])} Base auditável em <code>data/pesquisas/estaduais/mg/2026-08/derivados/carregadores-municipais.csv</code>.</p>
      </div>
    </section>

    <section id="corredores" class="chapter corridors-chapter paper-grid">
      <div class="wrap wide">
        <div class="chapter-head"><p class="sec-no">13 · sete corredores</p><div><h2>A economia manda na pauta, <em>e a pauta muda a cada duzentos quilômetros.</em></h2><p class="lead">Cada corredor reúne municípios com a mesma base econômica, a mesma imprensa e o mesmo tipo de encontro público possível. Para cada um: o que os jornais mineiros publicaram, quem tem base eleitoral medida ali, quem deveria subir no palanque, o formato que a região comporta e o que não dizer.</p></div></div>\n        <div class="stance reveal"><span class="stamp limit">Posição declarada</span><p>Este capítulo tem lado, e o diz. As recomendações são dirigidas à campanha de Flávio Bolsonaro em Minas. A regra da casa continua valendo dentro dele: cada movimento recomendado tem número e fonte ao lado, o juízo editorial está rotulado como juízo editorial, e o capítulo publica com o mesmo destaque o achado que contraria a própria tese. Esse achado está no Corredor da Produção, que reúne 13,85% do eleitorado mineiro e onde nenhum dos três carregadores ajuda.</p></div>
        {''.join(corredor(c) for c in D['corredores'])}
      </div>
    </section>

    <section id="roteiro" class="chapter route-order-chapter dark">
      <div class="wrap">
        <div class="chapter-head"><p class="sec-no">14 · ordem de leitura</p><div><h2>Sem datas. <em>Com ordem.</em></h2><p class="lead">A sequência abaixo é dirigida à campanha de Flávio Bolsonaro em Minas e não traz datas. Ela ordena os corredores por relação entre esforço e voto, com o critério declarado em cada linha, e termina no achado que contraria a própria recomendação.</p></div></div>
        <div class="stake reveal">
          <div><span>Datafolha MG, 1º turno</span><b>Lula 37 × Flávio 31</b></div>
          <div><span>Datafolha MG, 2º turno</span><b>Lula 46 × Flávio 42</b></div>
          <div><span>desenho</span><b>1.204 entrevistas, 18 a 20/08, margem de 3 pontos</b></div>
          <p>A diferença de quatro pontos no segundo turno cabe dentro da margem da própria diferença, que é maior que a margem de cada candidato isolado. Minas está indefinida e é isso que dá sentido a discutir corredor por corredor em vez de discutir o estado como bloco. Fonte: <a href="https://www.poder360.com.br/poder-eleicoes-2026/lula-tem-46-e-flavio-42-no-2o-turno-em-mg-diz-datafolha/" rel="noopener">Poder360</a>.</p>
        </div>
        <ol class="wave-list reveal">
          <li><b>Tornar visível a aliança estadual antes de qualquer outra coisa.</b> A Quaest mede que 81% não sabem quem Flávio apoia para o governo de Minas, e que o endosso dele hoje tem saldo praticamente nulo, com 27% dizendo que aumentaria a chance de voto e 28% que diminuiria. Enquanto os dois números forem esses, nenhum ativo de transferência opera e todo cálculo de repasse de voto é especulação. O indicador de saída é o próprio "sabe quem apoia quem", não a intenção de voto.</li>
          <li><b>O cinturão do minério.</b> Único corredor em que os três carregadores rendem acima do topo da chapa ao mesmo tempo, com pauta material de valor definido e seis municípios que trocaram de lado em 2022.</li>
          <li><b>A periferia metropolitana.</b> Quase um quarto do eleitorado do estado, com os dois nomes de maior alcance urbano da direita mineira e uma pauta de serviço público que não depende de guerra cultural.</li>
          <li><b>O eixo produtivo.</b> Sul, Triângulo e Alto Paranaíba não têm carregador: os três índices ficam abaixo de cem. É onde o nome do topo da chapa precisa se sustentar sozinho, com tarifa, frete, energia e conta fiscal.</li>
          <li><b>Juiz de Fora e a Mata.</b> O maior município que trocou de lado entre 2018 e 2022, com a agenda simbólica mais carregada e ainda pendente do calendário de campanha.</li>
          <li><b>Os vales, em fundo contínuo.</b> Nunca uma onda própria. Rádio regional e parlamentar local. O objetivo mensurável é reduzir diferença, não vencer região.</li>
        </ol>
        <div class="scroll-x reveal"><table class="carrier-table paradas">
          <caption>Dezesseis paradas, sem data, cobrindo os sete corredores</caption>
          <thead><tr><th>parada</th><th>eleitores</th><th>Bolso 1T</th><th>margem E 2T</th><th>por que aqui</th><th>formato</th></tr></thead>
          <tbody>{paradas_html()}</tbody></table></div>
        <div class="counterpoint">
          <span class="stamp limit">Contraponto obrigatório</span>
          <p>A tese deste capítulo enfraquece em {pct([c for c in D['corredores'] if c['slug'] == 'producao'][0]['resumo']['share_mg'], 2)} do eleitorado de Minas. No Corredor da Produção os três carregadores rendem abaixo de Bolsonaro, o que significa que a parte mais rica e mais industrial do estado não é destravável por aliança regional. Some-se a isso que as {EST['viradas_de']} cidades que trocaram de lado têm margem média de {pp(EST['margem_media_viradas'])} para a esquerda, e não empate: apenas {EST['viradas_ate_5pp']} delas ficaram dentro de cinco pontos. Recuperar esse bloco é mais caro do que o mapa sugere à primeira vista.</p>
        </div>
      </div>
    </section>
{FIM}"""


def main() -> None:
    html = PAGE.read_text(encoding="utf-8")
    if INICIO in html and FIM in html:
        antes = html.split(INICIO)[0]
        depois = html.split(FIM)[1]
        html = antes + CH + depois
    else:
        alvo = '    <section id="fontes"'
        if alvo not in html:
            raise SystemExit("nao achei a secao de fontes para ancorar a insercao")
        html = html.replace(alvo, CH + "\n\n" + alvo, 1)
    PAGE.write_text(html, encoding="utf-8")
    if "—" in CH:
        raise SystemExit("travessao encontrado no fragmento gerado")
    print("capitulos inseridos em", PAGE)


if __name__ == "__main__":
    main()
