#!/usr/bin/env python3
"""Gera relatório editorial a partir do payload, sem recalcular as centrais antigas."""

import json
from html import escape

import pandas as pd
from projecao_secoes_2t.figuras import figures
from projecao_secoes_2t.fontes import ROOT


def number(value, digits=2):
    return f"{value:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def table(headers, rows):
    return (
        '<div class="scroll" tabindex="0"><table><thead><tr>'
        + "".join(f'<th scope="col">{escape(str(h))}</th>' for h in headers)
        + "</tr></thead><tbody>"
        + "".join(
            "<tr>" + "".join(f"<td>{escape(str(v))}</td>" for v in row) + "</tr>"
            for row in rows
        )
        + "</tbody></table></div>"
    )


def build():
    source = ROOT / "docs/assets/projecao_secoes_2t_2026.json"
    data = json.loads(source.read_text())
    figures(data)
    national, fusion, coverage = data["nacional"], data["fusao"], data["cobertura"]
    selected = data["selecionado"]
    main = national["combinado"]["flavio_validos"]
    results = data["validacao"]["resultados"]
    bounds = data["validacao"]["limites_transferencia_2022"]
    states = pd.DataFrame(data["ufs"]["linhas"], columns=data["ufs"]["colunas"])
    historical = pd.DataFrame(
        data["historico_2022_ufs"]["linhas"],
        columns=data["historico_2022_ufs"]["colunas"],
    )
    totals = historical.select_dtypes("number").sum()
    validations = table(
        ["Método", "RMSE / UF", "Erro nacional", "RMSE / seção"],
        [
            [
                r["rotulo"],
                number(r["rmse_uf_pp"]),
                number(r["erro_nacional_pp"]),
                number(r["rmse_secao_pp"]),
            ]
            for r in results.values()
        ],
    )
    alternatives = table(
        ["Hipótese para 2026", "Flávio / válidos", "Comparecimento"],
        [
            [
                r["rotulo"],
                number(r["flavio_validos"]) + "%",
                number(r["comparecimento_pct"]) + "%",
            ]
            for r in national.values()
        ],
    )
    state_rows = []
    for _, r in states.iterrows():
        first = 100 * r.direita_1 / (r.direita_1 + r.esquerda_1)
        raw = (
            100
            * r[f"{selected}_direita"]
            / (r[f"{selected}_direita"] + r[f"{selected}_esquerda"])
        )
        combined = (
            100 * r.combinado_direita / (r.combinado_direita + r.combinado_esquerda)
        )
        state_rows.append(
            [
                r.uf,
                number(first),
                number(raw),
                number(combined),
                number(100 - combined),
                number(r.aptos_1, 0),
            ]
        )
    state_table = table(
        [
            "UF",
            "1T entre finalistas",
            "Urna local / F",
            "Combinado / F",
            "Combinado / L",
            "Eleitores",
        ],
        state_rows,
    )
    polling = table(
        ["UF", "Campo", "F / L, total", "Peso estadual", "Antes", "Após pesquisa*"],
        [
            [
                r["uf"],
                r["campo"]["inicio"][8:] + "–" + r["campo"]["fim"][8:] + "/10",
                f'{r["publicado"]["flavio"]} / {r["publicado"]["lula"]}',
                number(100 * r["peso_pesquisa"], 1) + "%",
                number(r["anterior_pct"]),
                number(r["atualizado_antes_calibracao_pct"]),
            ]
            for r in fusion["estaduais"]
        ],
    )
    houses = table(
        ["Casa", "Fim do campo", "F / válidos antes da tendência", "Peso", "Renda"],
        [
            [
                r["instituto"],
                r["campo"]["fim"],
                number(r["flavio_validos"]),
                number(100 * r["peso"], 1) + "%",
                "PNAD condicional" if r["pnad"] else "Publicado",
            ]
            for r in fusion["nacional"]["casas"]
        ],
    )
    transition = data["ajuste_2022"]["matrizes"]
    origin_names = {
        "direita": "Bolsonaro no 1º turno",
        "esquerda": "Lula no 1º turno",
        "outros": "Terceira via",
        "bn": "Branco/nulo",
        "ausentes": "Ausência",
    }
    matrix_table = table(
        ["Origem / 1T 2022", "→ Bolsonaro", "→ Lula", "→ BN", "→ Ausência"],
        [
            [origin_names[key], *[number(100 * v, 1) + "%" for v in values]]
            for key, values in zip(
                transition["origens"], transition["brasil"], strict=True
            )
        ],
    )
    gains_table = table(
        [
            "UF",
            "Terceiros / 1T",
            "Ganho Bolsonaro",
            "Ganho Lula",
            "Variação BN",
            "Variação ausência",
        ],
        [
            [
                r.uf,
                number(r.outros_1, 0),
                number(r.ganho_direita, 0),
                number(r.ganho_esquerda, 0),
                number(r.bn_2 - r.bn_1, 0),
                number(r.ausentes_2 - r.ausentes_1, 0),
            ]
            for _, r in historical.iterrows()
        ],
    )
    source_links = "".join(
        f'<li><a href="{escape(url)}">TSE · {year} · {kind}</a></li>'
        for year, meta in [
            (2018, data["validacao"]["fontes"][0]),
            (2022, data["fontes"]["2022"]),
        ]
        for kind, url in zip(
            ("votação por seção", "detalhe da seção"), meta["urls"], strict=True
        )
    )
    body = f"""<header class="masthead"><a href="index.html">ARVOR / Biblioteca</a><span>Laboratório eleitoral · versão experimental</span></header>
<main id="conteudo">
<section class="hero"><p class="eyebrow">19 outubro 2026 · 2º turno · Brasil sem exterior</p><h1>A urna encontra<br><em>as pesquisas.</em></h1><p class="deck">Uma projeção construída de baixo para cima: {number(coverage['secoes'], 0)} boletins de seção, histórico de 2018 e 2022, {fusion['nacional']['n_casas']} casas nacionais e pesquisas em seis UFs.</p><div class="hero-bottom"><div><p class="eyebrow">Combinação experimental · votos válidos</p><div class="score"><span class="flavio">{number(main, 2)}<small>Flávio</small></span><span class="versus">×</span><span class="lula">{number(100-main, 2)}<small>Lula</small></span></div></div><aside><strong>A complexidade precisa merecer seu lugar.</strong><p>As matrizes que transportam 2022 chegam perto de 52,6% para Flávio. Na retrospectiva 2018 → 2022, porém, perderam para uma regra simples por seção. Publicamos as duas coisas.</p></aside></div></section>
<nav aria-label="Capítulos"><a href="#combinacao">Combinação</a><a href="#validacao">Teste temporal</a><a href="#transferencia">Transferências</a><a href="#territorio">Território</a><a href="#fontes">Fontes</a></nav>
<section id="combinacao"><p class="eyebrow">01 / Evidências e escolhas</p><h2>Três números.<br>Três perguntas diferentes.</h2><div class="triptych"><article><span>Urna local</span><b>{number(fusion['historico_pct'])}%</b><p>Preserva os votos dos finalistas e divide a terceira via pela razão F/(F+L) da própria seção. Mantém BN e comparecimento do primeiro turno.</p></article><article><span>Pesquisas</span><b>{number(fusion['pesquisas_pct'])}%</b><p>Âncora inclusiva com PNAD onde disponível, recência e tendência até 25/10. Sem reaplicar o ajuste relativo de presença de +3,8% das centrais anteriores.</p></article><article><span>Urna + pesquisas</span><b>{number(main)}%</b><p>{number(100*(1-fusion['peso_pesquisas']),1)}% de peso para a urna local e {number(100*fusion['peso_pesquisas'],1)}% para a âncora de pesquisas. Pesos são hipóteses; não foram validados em várias eleições.</p></article></div><p><strong>O teste temporal abaixo avalia os seis métodos de transporte histórico.</strong> A combinação completa com pesquisas ainda não tem retrospectiva: o acervo de pesquisas de 2022 disponível neste projeto é do primeiro turno e não serve para validar o segundo.</p><p class="callout">O voto por seção dá a distribuição territorial. Não transforma quase meio milhão de seções em quase meio milhão de observações independentes sobre o futuro.</p>
<div class="experiment"><div><p class="eyebrow">Sensibilidade nacional</p><h3>Quanto peso dar às pesquisas?</h3><label for="peso">Peso das pesquisas: <output id="peso-out">{number(100*fusion['peso_pesquisas'],1)}%</output></label><input id="peso" type="range" min="0" max="100" step="0.1" value="{100*fusion['peso_pesquisas']}"><label for="vies">Deslocamento comum na parcela de Flávio: <output id="vies-out">0,0 pp</output></label><input id="vies" type="range" min="-4" max="4" step="0.1" value="0"><button id="reset" type="button">Restaurar combinação</button></div><div class="experiment-result" aria-live="polite"><p>Flávio / Lula, válidos</p><b id="sim-score">{number(main)} × {number(100-main)}</b><p>Os controles alteram somente esta sensibilidade nacional. As tabelas abaixo mostram a combinação de referência.</p></div></div><p>Uma sensibilidade comum de ±2 pp na parcela de Flávio vai de <strong>{number(main-2)}% a {number(main+2)}%</strong>. Inclui a inversão da liderança; não é intervalo de confiança nem probabilidade de vitória.</p><details><summary>Pesquisas nacionais e peso de cada casa</summary>{houses}<p>O peso da combinação usa variância histórica com piso de 2 pp, erro comum das pesquisas de 2 pp, erro amostral/entre casas e incerteza da tendência. A hipótese de independência entre erros das duas fontes não foi validada. PNAD é sensibilidade de composição, não correção observada do voto. {escape(fusion['nacional']['regra'])}</p></details></section>
<section id="validacao"><p class="eyebrow">02 / O teste que pode contrariar o modelo</p><h2>Aprender em 2018.<br>Prever 2022.</h2><p>O treinamento usa apenas 2018. O segundo turno de 2022 fica reservado para avaliação. Mesmas chaves e mesmo nome de local nos dois turnos, partições completas e exterior excluído. O critério escolhido antes dos resultados foi o RMSE por UF ponderado pelos votos válidos.</p><figure><img src="img/projecao_secoes_2t/validacao.svg" alt="Erro por UF dos seis modelos; proporcional por seção apresenta o menor RMSE, 1,73 ponto."><figcaption>Erro na parcela de Bolsonaro entre os finalistas em 2022. <a href="img/projecao_secoes_2t/validacao.pdf">Baixar figura em PDF</a>.</figcaption></figure>{validations}<p class="callout">A regra proporcional venceu entre as seis testadas, mas também subestimou Bolsonaro em {number(-results[selected]['erro_nacional_pp'])} ponto no país. Selecionar o vencedor numa única eleição é exploração, não prova de superioridade futura.</p><p>Em 2018 a terceira via era muito maior, Haddad era o candidato do PT e Bolsonaro ganhou o primeiro turno com ampla vantagem. Transportar sem ajuste a mudança daquele pleito para 2022 fracassou. A eleição anterior informa cenários; não é uma lei de migração.</p><details><summary>Como funcionam as alternativas</summary><ul><li><strong>50/50:</strong> metade dos votos de terceiros para cada finalista; nenhuma mudança nos demais grupos.</li><li><strong>Proporcional local:</strong> terceiros divididos pela razão entre os finalistas naquela seção. Não supõe que pessoas específicas mudem assim.</li><li><strong>Deslocamento UF/seção:</strong> mudança histórica de log-odds de um turno ao outro. Na seção, encolhimento para município (500 votos equivalentes), e município para UF (5 mil). Sem casamento de chave e local, usa município/UF.</li><li><strong>Matrizes:</strong> cinco origens e quatro destinos, coeficientes não negativos e linhas somando um. Penalização de 50 mil aptos para UF contra Brasil, 20 mil para contexto contra UF. Contextos: parcela inicial entre finalistas abaixo de 35%, de 35% a 65% e acima de 65%.</li><li><strong>Sem confundir eleições:</strong> Bolsonaro/17 e Haddad/13 em 2018, Bolsonaro/22 e Lula/13 em 2022, Flávio/22 e Lula/13 em 2026. A correspondência é hipótese de transporte, não identidade de candidaturas.</li></ul></details><h3>Aplicando 2022 à urna de 2026</h3>{alternatives}<p>As matrizes ficam em 52,53%–52,65% para Flávio; transportar o deslocamento histórico fica perto de 52,94%. A inspiração nas imagens de Pedro Werneck aparece nessa comparação. Não é reprodução exata: não recebemos seu código, o algoritmo de agrupamento não está inteiramente especificado e o universo aqui exclui o exterior.</p></section>
<section id="transferencia"><p class="eyebrow">03 / O que a urna identifica</p><h2>Ganho líquido<br>não é migração individual.</h2><p>No conjunto pareado de 2022, Bolsonaro ganhou <strong>{number(totals['ganho_direita'],0)} votos</strong> e Lula <strong>{number(totals['ganho_esquerda'],0)}</strong> entre turnos. Havia {number(totals['outros_1'],0)} votos na terceira via. Essas contas misturam transferências, mudanças de finalista, BN e comparecimento.</p><div class="equation">ganho de B = terceiros → B + L → B + BN → B + ausentes → B<br>− B → L − B → BN − B → ausência</div><p>Nos {number(bounds['secoes'],0)} pares com aptos iguais, os limites aritméticos para terceiros → Bolsonaro vão de <strong>{number(bounds['minimo_pct'])}% a {number(bounds['maximo_pct'])}%</strong> do estoque de terceiros. São limites de Fréchet/Duncan–Davis sob população fechada: igualdade do número de aptos não prova que sejam as mesmas pessoas.</p><p class="callout">Uma matriz ajustada pode prever bem o agregado e ainda atribuir fluxos individuais errados. Por isso mostramos limites, erros e cenários; não afirmamos ter descoberto o destino de cada eleitor.</p><h3>Uma decomposição estimada, sob hipóteses</h3><p>A matriz nacional abaixo foi ajustada aos agregados de 2022. Cada linha soma 100%. Coeficientes na fronteira (0% ou 100%) podem refletir a restrição do modelo, e não fidelidade ou transferência realmente observada. É uma alternativa exploratória, que não venceu a retrospectiva.</p>{matrix_table}<details><summary>Ganhos líquidos observados por UF em 2022</summary>{gains_table}<p>Mesmo conjunto pareado nos dois turnos. As variações de aptos impedem interpretar a identidade como fluxo fechado em todas as seções.</p></details><details><summary>Auditoria do pareamento histórico</summary><p>2018: {number(data['validacao']['fontes'][0]['n_secoes_pareadas'],0)} pares no arquivo completo, incluindo exterior. 2022: {number(data['fontes']['2022']['n_secoes_pareadas'],0)}; {number(data['fontes']['2022']['locais_divergentes'],0)} pares retirados por nome de local diferente. Todas as contas centrais e a avaliação excluem ZZ. O pareamento histórico → 2026 encontrou {number(data['ajuste_2022']['casamento']['secoes_com_chave_e_local'],0)} chaves com mesmo local; os demais usam a hierarquia geográfica nos cenários de deslocamento.</p><p>Igualdade de seção/local não garante eleitorado constante, principalmente com seções agregadas. As matrizes usam proporções por turno quando os aptos mudam. As perdas e os hashes constam no JSON público.</p></details></section>
<section id="territorio"><p class="eyebrow">04 / De baixo para cima</p><h2>O país é a soma<br>das suas seções.</h2><p>{number(coverage['cobertura_secao_pct'],3)}% do eleitorado nacional está em boletins auditados. A parcela restante — {number(coverage['aptos_sem_secao'],0)} eleitores de Betim/MG, Uberlândia/MG e Carapicuíba/SP — entra como resíduo municipal explícito, sem inventar seções. Total: {number(coverage['aptos'],0)} eleitores.</p><figure><img src="img/projecao_secoes_2t/estados.svg" alt="Comparação por UF entre a parcela de Flávio entre finalistas no primeiro turno e a projeção combinada do segundo."><figcaption>Comparação na mesma base F/(F+L), não contra a parcela em todas as candidaturas. <a href="img/projecao_secoes_2t/estados.pdf">PDF</a>.</figcaption></figure>{state_table}<h3>As estaduais mudam a distribuição, sem virar seis pesquisas nacionais</h3><p>Quaest após o primeiro turno em AC, AM, DF, ES, RN e TO: {number(fusion['cobertura_estaduais_pct'],1)}% do eleitorado. Publicados, sem renda imputada. Peso cai com a idade do campo; teto amostral de 2.000, deff 1,5 e erro de casa de 2 pp. Depois, um deslocamento comum de log-odds recentra as seções na combinação nacional.</p>{polling}<p class="note">*Antes da calibração nacional. Níveis nacionais e estaduais da mesma casa podem compartilhar erro; as estaduais redistribuem o país, sem reduzir a incerteza nacional. Há divergências nos registros citados pelo G1 para AC e códigos estaduais para AM/RN; foram preservados literalmente no acervo, sem alegar conferência no PesqEle.</p><h3>Explore seu município</h3><div class="filters"><label>UF <select id="uf"><option value="">Todas</option>{''.join(f'<option>{u}</option>' for u in sorted(states.uf))}</select></label><label>Município <input id="municipio" type="search" placeholder="Digite o nome" autocomplete="off"></label></div><p id="municipios-count" aria-live="polite"></p><div id="municipios-table"></div><noscript><p>A busca requer JavaScript; as tabelas estaduais e os arquivos completos continuam disponíveis.</p></noscript><p><a class="download" href="fontes/projecao_secoes_2t_2026.csv.gz">Baixar projeção de todas as seções · CSV gzip · {number(data['fontes']['extrato_completo']['bytes']/1e6,1)} MB</a></p><p class="note">Contagens projetadas são expectativas fracionárias. Zona/seção zero identifica resíduo municipal. Não converter o arquivo em cadastro de comportamento individual: o voto é secreto.</p></section>
<section id="fontes"><p class="eyebrow">05 / Reproduzir e contestar</p><h2>Hipóteses à vista.<br>Fontes preservadas.</h2><p>Esta página é uma nova versão experimental. As <a href="reponderacao_pnad.html">centrais Média e Projeção Arvor</a> permanecem disponíveis, com seus métodos e snapshots. Não há probabilidade de vitória validada, e o erro histórico não corrige automaticamente o placar.</p><ul>{source_links}<li><a href="{escape(fusion['fonte_estaduais']['url'])}">G1 / Globo · Quaest nas seis UFs</a></li><li><a href="https://gking.harvard.edu/publication/ecological-regression-with-partial-identification/">Jiang, King, Schmaltz e Tanner · identificação parcial</a></li><li><a href="https://imai.fas.harvard.edu/research/files/eiall.pdf">Imai, Lu e Strauss · inferência ecológica</a></li><li><a href="assets/projecao_secoes_2t_2026.json">Payload completo: números, hipóteses, auditorias e hashes</a></li><li><a href="assets/projecao_secoes_2t_ufs.csv">Tabela estadual em CSV</a></li></ul><pre><code>python3 scripts/projecao-secoes-2t-validar.py
python3 scripts/projecao-secoes-2t-dados.py --hoje 2026-10-19
python3 scripts/projecao-secoes-2t-build.py
pytest -q tests/test_projecao_secoes_2t.py</code></pre><p>Snapshot das pesquisas: <code>{escape(data['fontes']['pesquisas_snapshot']['id'] if isinstance(data['fontes']['pesquisas_snapshot'], dict) and 'id' in data['fontes']['pesquisas_snapshot'] else str(data['fontes']['pesquisas_snapshot']))}</code>. Os arquivos pesados locais e fontes oficiais são necessários para reconstruir os extratos.</p></section></main><footer><a href="index.html">Arvor / Biblioteca</a><p>Projeção agregada e experimental. Mais detalhe exige mais teste.</p></footer>"""
    payload = {
        "fusao": {
            k: fusion[k] for k in ("historico_pct", "pesquisas_pct", "peso_pesquisas")
        },
        "municipios": data["municipios"],
    }
    document = (
        (ROOT / "docs/projecao_secoes_2t_2026.template.html")
        .read_text()
        .replace("{{BODY}}", body)
        .replace(
            "{{DATA}}",
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace(
                "</", "<\\/"
            ),
        )
    )
    (ROOT / "docs/projecao_secoes_2t_2026.html").write_text(document)
    # Payload compacto; mantém dados no formato coluna/linhas sem inflar o arquivo.
    source.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        + "\n"
    )
    print("Relatório gerado")


if __name__ == "__main__":
    build()
