"""Capítulos 9 a 11: veredito, ficha para o eleitor e fontes."""

from __future__ import annotations

from . import figuras as fg  # noqa: F401  (mantido para extensões futuras de figura)
from .capitulos_a import _nome_uf
from .contexto import Contexto
from .tabelas import (
    caixa,
    detalhes,
    link,
    lista,
    nota,
    secao,
    tabela,
)
from .util import data_br, dec, esc, ic, inteiro, lista_secoes, pct, pp, titulo_pt

TAG = {
    "fato": '<span class="tag fato">Fato medido</span>',
    "inf": '<span class="tag inf">Inferência</span>',
    "juizo": '<span class="tag juizo">Juízo editorial</span>',
    "nao": '<span class="tag nao">Não sustentado</span>',
}


def _item(tag: str, texto: str) -> str:
    return f"{TAG[tag]} {texto}"


def cap9_veredito(c: Contexto) -> str:
    d = c.d
    cp = d["confronto_publico"]
    por_id = {n["id"]: n for n in cp["numeros_publicos"]}
    mr = c.mr
    a = mr["por_categoria"]["A"]["secoes"]
    dist = d["distancia"]["teste_hipotese"]
    cb = d["comportamento_1t"]["grupos"]
    efeito = d["efeito_1t"]["dif_em_dif"]["diferenca"]["mesmo_municipio"][
        "diferenca_pp"
    ]
    cl = d["clima_resumo"]
    mo = c.motivos
    pan = d["confronto_painel"]
    sal = d["cenarios_abstencao"]["estimativa_brasileira"]["saldo_1t_para_2t"][
        "central"
    ]
    novas_f = cb["novas"]["metricas"]["flavio_validos"]["mesmo_municipio"][
        "diferenca_pp"
    ]
    novas_l = cb["novas"]["metricas"]["lula_validos"]["mesmo_municipio"]["diferenca_pp"]
    dose5 = d["efeito_1t"]["dose_resposta"]["faixas"][4]["dif_em_dif"][
        "mesmo_municipio"
    ]["diferenca_pp"]
    itens = [
        _item(
            "fato",
            f"A cifra de {inteiro(por_id['tse_agencia_brasil']['secoes']['publico'])} seções não encontra apoio no painel do TSE de 18/10 ({inteiro(por_id['painel_tse']['secoes']['publico'])}) nem no cadastro de locais ({inteiro(c.secoes_real())} seções com mudança real de prédio, {inteiro(c.mr['eleitores'])} eleitores).",
        ),
        _item(
            "fato",
            f"A maioria das mudanças reais é retorno ao prédio original: {inteiro(a)} de {inteiro(c.secoes_real())} seções ({pct(100 * a / c.secoes_real())}).",
        ),
        _item(
            "fato",
            f"A distância típica é a do prédio vizinho: mediana de {inteiro(d['distancia']['mudanca_real']['mediana_m'])} m. Existe uma cauda: {pct(dist['novas_realocacoes']['parcela_pct']['acima_1km']['valor'])} das novas realocações passam de 1 km ({ic(dist['novas_realocacoes']['parcela_pct']['acima_1km']['ic95'], 1, False)}).",
        ),
        _item(
            "inf",
            f"O clima não explica a maioria. Os locais que mudaram tiveram menos chuva forte que os de controle ({pp(cl['origem_mudanca_real_menos_controle_pp']['chuva_max_05a18_acima_20mm']['valor'], 1)}), e {inteiro(cl['origem_mudanca_real_sem_chuva_nem_vento']['quantidade'])} locais de origem não tiveram chuva acima de 10 mm nem rajada acima de 50 km/h. Parte dos casos tem chuva compatível.",
        ),
        _item(
            "fato",
            f"Só {inteiro(mo['com_nota']['secoes'])} das {inteiro(mo['secoes_total'])} seções ({pct(100 * mo['com_nota']['secoes'] / mo['secoes_total'])}) casam com uma nota que cite o local, a zona ou o município. A maioria não tem motivo publicado por seção.",
        ),
        _item(
            "fato",
            f"O efeito sobre a abstenção, medido no 1º turno, é {pp(efeito['valor'])} ({ic(efeito['ic95'])}). É pequeno no agregado. Acima de 5 km chega a {pp(dose5['valor'])} ({ic(dose5['ic95'])}), com poucas urnas.",
        ),
        _item(
            "fato",
            f"Nada nos dados mostra padrão que favoreça uma candidatura. Contra o município, o placar do 1º turno no conjunto das urnas com mudança real é indistinguível (veja a ressalva abaixo para as novas realocações). O saldo de votos nos cenários medidos é de {inteiro(abs(sal['variacao_diferenca_flavio_menos_lula_votos']))} votos a favor de Lula, na conta em que as novas realocações perdem e a categoria A recupera.",
        ),
        _item(
            "nao",
            f"Os vídeos que falam em junção de seções não encontram apoio: o cadastro tem as mesmas {inteiro(d['resumo']['secoes_total'])} seções nos dois turnos, e o TSE afirma manter 499.248.",
        ),
        _item(
            "juizo",
            f"O problema demonstrável é de transparência. Quatro números atribuídos ao TSE ou ao seu sistema que não batem. Painel e arquivo com o mesmo carimbo e {pct(100 - pan['concordancia_pct'], 2)} de divergência sobre a união. Motivo ausente em {pct(100 * mo['sem_nota']['secoes'] / mo['secoes_total'])} das seções.",
        ),
    ]
    corpo = (
        "<p>Cada linha leva a etiqueta do tipo de afirmação. Fato medido sai do cadastro e dos boletins. Inferência é leitura nossa dos fatos. Juízo editorial é posição da casa. &quot;Não sustentado&quot; marca o que a evidência não apoia.</p>"
        + '<ul class="veredito">'
        + "".join(f"<li>{i}</li>" for i in itens)
        + "</ul>"
        + caixa(
            "O que contraria a tese de que nada importa",
            f"O efeito não é zero: é pequeno no país e maior onde a distância passa de 1 km. Nas novas realocações, o placar do 1º turno era meio ponto mais favorável a Flávio que no resto do município ({pp(novas_f['valor'])}, {ic(novas_f['ic95'])}) e menos a Lula ({pp(novas_l['valor'])}, {ic(novas_l['ic95'])}). O dado descreve onde estão os prédios; não aponta intenção. Para o eleitor da seção, o custo de procurar outro prédio é integral.",
        )
        + "<h3>O que resolveria</h3>"
        + lista(
            [
                "Lista oficial por seção, em arquivo aberto, com o motivo, a data da decisão e o ato do juiz eleitoral.",
                "Uma única fonte de verdade para &quot;seção alterada&quot;, com a regra de contagem publicada junto do número.",
                "Aviso individual ao eleitor da seção alterada (e-Título, SMS), como a coligação pediu ao TSE na ação 0603126-92.2026.6.00.0000.",
            ]
        )
        + nota(
            "Este laudo não afirma intenção de ninguém. Afirma o que os documentos mostram e diz o que resolveria."
        )
    )
    return secao(
        9,
        "veredito",
        "O que isto diz<br><em>e o que não diz.</em>",
        "A manchete de mais de 4 mil seções não se sustenta. O problema demonstrável é de transparência, não de padrão eleitoral.",
        corpo,
    )


def _sinais(x: dict) -> str:
    lg = x["logs_1t"]
    s = []
    if lg.get("bateria_votacao"):
        s.append("bateria na votação")
    if x.get("abertura_min_atrasada"):
        s.append("abertura atrasada")
    if x.get("fila_fechamento"):
        s.append("fila no fechamento")
    if (lg.get("atencao_max") or 0) >= 2:
        s.append("atenção 2 ou 3")
    return ", ".join(s) if s else "nenhum"


def linha_local(x: dict) -> tuple[list, str]:
    m = x.get("motivo_tre")
    if m:
        motivo = f"{esc(m['texto'][:140])}<br><small>{link(m['url'], m['veiculo'])}, {esc(data_br(m['data']))} (casamento por {esc(m['grau_casamento'])})</small>"
    else:
        motivo = "sem motivo publicado"
    mapa = link(x["maps_novo"], "Novo endereço")
    if x.get("maps_rota"):
        mapa += " · " + link(x["maps_rota"], "Rota")
    dist = x.get("distancia_m")
    if x.get("coord_repetida") or x.get("coord_suspeita") or dist is None:
        dist_txt = ("sem distância confiável", "")
    else:
        dist_txt = (f"{inteiro(dist)} m", dist)
    uf = _nome_uf(x["uf"])
    linha = [
        (f"{uf}", x["uf"]),
        (
            f"{esc(titulo_pt(x['municipio']))}<br><small>zona {x['zona']}</small>",
            x["municipio"],
        ),
        (
            f"{esc(lista_secoes(x['secoes']))}<br><small>{inteiro(len(x['secoes']))} seções</small>",
            len(x["secoes"]),
        ),
        (inteiro(x["eleitores"]), x["eleitores"]),
        x["categoria"],
        esc(x["nome_1t"]) + f"<br><small>{esc(x['end_1t'])}</small>",
        esc(x["nome_2t"])
        + f"<br><small>{esc(x['end_2t'])}, {esc(x['bairro_2t'])}</small>",
        dist_txt,
        (pct(x["abst_1t_pct"], 1), x["abst_1t_pct"]),
        f"{dec(x['flavio_v'], 1)} × {dec(x['lula_v'], 1)}",
        _sinais(x),
        (
            (
                f"{dec(x['clima']['chuva_max_05a18_mm'], 0)} mm",
                x["clima"]["chuva_max_05a18_mm"],
            )
            if x.get("clima") and x["clima"].get("chuva_max_05a18_mm") is not None
            else "sem dado"
        ),
        motivo,
        mapa,
    ]
    return linha, x["uf"]


def cap10_eleitor(c: Contexto) -> str:
    rows, ufs = [], []
    for x in sorted(c.reais, key=lambda x: (x["uf"], -x["eleitores"])):
        linha, uf = linha_local(x)
        rows.append(linha)
        ufs.append(f'data-uf="{uf}"')
    t = tabela(
        [
            "UF",
            "Município e zona",
            "Seções",
            "Eleitores",
            "Cat.",
            "Local no 1º turno",
            "Local no 2º turno",
            "Distância",
            "Abstenção no 1º turno",
            "Flávio × Lula, válidos do 1º turno",
            "Registros no log do 1º turno",
            "Chuva máxima diária, 05 a 18/10",
            "Motivo publicado",
            "Mapa",
        ],
        rows,
        ordenavel=True,
        numericas=(2, 3, 7, 8, 11),
        rotulo="Todas as trocas de local com mudança real",
        ident="tabela-locais",
        largura=1500,
        atributos_linha=ufs,
    )
    opts = "".join(
        f'<option value="{u}">{_nome_uf(u)}</option>'
        for u in sorted({x["uf"] for x in c.reais})
    )
    baixar = []
    for nome, caminho in c.baixar.items():
        if caminho.exists():
            kb = caminho.stat().st_size / 1024
            baixar.append(
                f'<a class="botao" href="assets/mudancas_secoes/{nome}" download>{nome} ({inteiro(kb)} KB)</a>'
            )
    corpo = (
        "<p>Antes de sair para votar em 25/10, confira o seu local. O TSE indica o Autoatendimento Eleitoral, no portal do tribunal, e o aplicativo e-Título (iOS e Android). A consulta mostra o endereço da sua seção no 2º turno.</p>"
        + lista(
            [
                'No <a href="politizesuavizinhanca.html">Politize sua vizinhança</a>, digite UF, zona e seção. Se a sua seção está nesta lista, o aplicativo mostra o alerta com o novo endereço.',
                "Leve o título ou o e-Título e um documento com foto. Confira a rota antes: a distância aqui é em linha reta, não o caminho a pé.",
                "Se achar que o seu local mudou e não foi avisado, avise o cartório eleitoral da sua zona.",
            ]
        )
        + f"<p>Abaixo, os <b>{inteiro(len(c.reais))} pares de local</b> (origem e destino) com mudança real, {inteiro(c.secoes_real())} seções. Ordene pelas colunas. Com JavaScript, filtre por UF. Sem ele, a tabela inteira fica visível.</p>"
        + f'<div class="filtro js-only" hidden><label for="filtro-uf">Filtrar por UF</label><select id="filtro-uf"><option value="">Todas</option>{opts}</select><output id="filtro-n" aria-live="polite"></output></div>'
        + t
        + nota(
            "Cada linha é um par origem e destino. Seções do mesmo prédio aparecem juntas. A distância é em linha reta; &quot;sem distância confiável&quot; marca coordenada ausente, repetida ou suspeita. Registros no log são operacionais, não irregularidade. A chuva é de reanálise de 9 km."
        )
        + (f'<div class="downloads">{"".join(baixar)}</div>' if baixar else "")
        + nota(
            "Dados abertos: o JSON traz todos os campos do laudo; o CSV, uma linha por seção com mudança real."
        )
    )
    return secao(
        10,
        "eleitor",
        "Para o eleitor:<br><em>confira o seu local.</em>",
        f"Lista completa dos {inteiro(len(c.reais))} pares de local com mudança real, filtrável por UF, com link de mapa.",
        corpo,
    )


REFERENCIAS = [
    "Brady, H. E. e McNulty, J. E. (2011). Turning Out to Vote: The Costs of Finding and Getting to the Polling Place. American Political Science Review, 105(1). Mudança de local reduziu o comparecimento em cerca de 1,9 ponto em Los Angeles, em 2003 (1,85 no texto).",
    "Clinton, J. D., Eubank, N., Fresh, A. e Shepherd, M. E. (2021). Polling Place Changes and Political Participation: Evidence from North Carolina Presidential Elections, 2008 to 2016. Political Science Research and Methods, 9(4). Segundo os autores, o efeito da mudança de local é compensado pelo voto antecipado.",
    "Portaria TSE nº 527/2026, que instituiu a Sala Nacional de Situação Climática (art. 6º, parágrafo único: medidas excepcionais, como a alteração de locais, dependem de decisão da autoridade competente).",
    "Resolução TSE nº 23.751/2026, arts. 6º, 16 e 18 (agregação de seções, publicação e ampla divulgação da localização das seções), conforme o Fato ou Boato do TSE de 16/10/2026.",
    "Ação TSE 0603126-92.2026.6.00.0000 (pedido da coligação Brasil Pronto pra Mais por divulgação individualizada das mudanças).",
]


def cap11_fontes(c: Contexto) -> str:
    d = c.d
    linhas_f = []
    for f in d["fontes"]:
        h = f.get("sha256")
        linhas_f.append(
            [
                esc(f.get("descricao", f["chave"])),
                f'<code>{esc(f["caminho"])}</code>',
                inteiro(f["bytes"]) if f.get("bytes") else "",
                (
                    f'<code class="hash">{h}</code>'
                    if h
                    else esc(f.get("nota") or "hash não calculado")
                ),
            ]
        )
    t_f = tabela(
        ["Fonte", "Arquivo no repositório", "Bytes", "SHA-256"],
        linhas_f,
        numericas=(2,),
        rotulo="Fontes e hashes",
        largura=860,
    )
    t_n = tabela(
        ["UF", "Veículo", "Data", "Título", "SHA-256 do HTML salvo"],
        [
            [
                n["uf"],
                esc(n["veiculo"]),
                esc(data_br(n["data"]) if str(n["data"])[:2] == "20" else n["data"]),
                link(n["url"], n["titulo"]),
                f'<code class="hash">{n["sha256_html"]}</code>',
            ]
            for n in c.tre
            if n.get("url")
        ],
        rotulo="Notas e matérias",
        largura=860,
    )
    lim = d["limites"]
    comandos = (
        "python3 scripts/mudancas-secoes-2t.py\n"
        "python3 scripts/mudancas-secoes-2t-build.py\n"
        "python3 scripts/social-cards.py --only mudancas_secoes_abstencoes mudancas_secoes_thread\n"
        "pytest -q tests/test_mudancas_secoes_2t.py tests/test_mudancas_secoes_2t_pagina.py"
    )
    corpo = (
        f"<p>Motor gerado em {data_br(d['gerado_em'])}, versão {esc(d['versao'])}, {inteiro(d['parametros']['reps'])} réplicas de bootstrap, semente {d['parametros']['seed']}. O cadastro de 18/10 ainda pode mudar até 25/10.</p>"
        + "<h3>Arquivos e hashes</h3>"
        + detalhes("Fontes do motor, com SHA-256", t_f)
        + detalhes(
            "Notas dos TREs e matérias, com data, link e hash do HTML salvo", t_n
        )
        + "<h3>Literatura e normas</h3>"
        + lista([esc(r) for r in REFERENCIAS])
        + "<h3>Limites</h3>"
        + lista([esc(x) for x in lim])
        + "<h3>Reprodução</h3>"
        + f"<pre><code>{esc(comandos)}</code></pre>"
        + nota(
            "Os números desta página saem de analysis/mudancas_secoes_2t/mudancas.json pelo gerador. Nenhum é digitado à mão."
        )
    )
    return secao(
        11,
        "fontes",
        "Fontes e método.",
        "Cada arquivo com hash, cada nota com data e link, cada limite declarado.",
        corpo,
    )
