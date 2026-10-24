"""Capítulos 8 a 10: o que o dado diz, uso pelo eleitor e pelo fiscal, fontes e limites."""

from __future__ import annotations

import json

from .comum import (
    TAG,
    caixa,
    detalhes,
    lista,
    nota,
    secao,
    tabela,
)
from .util import (
    ROOT,
    Dados,
    dec,
    esc,
    hora_br,
    ic,
    inteiro,
    pct,
    pp,
)

DOWNLOADS = ("dados.json", "locais.csv.gz")


def _item(tag: str, texto: str) -> str:
    return f"{TAG[tag]} {texto}"


def cap8_veredito(dados: Dados) -> str:
    d = dados.d
    faixas = dados.faixas("chuva_votacao", "bateria_votacao")
    forte, seca = faixas[3], faixas[0]
    or_s = dados.reg_bateria("bateria_simultanea", "chuva_votacao_x")
    or_i = dados.reg_bateria("bateria_isolada", "chuva_votacao_x")
    or_r = dados.reg_bateria("bateria_votacao", "rajada_votacao_x")
    rm = d["bateria_x_chuva"]["regressoes"]["robustez_municipio"]["bateria_votacao"][0][
        "termos"
    ]["chuva_votacao_x"]
    b = d["abstencao_x_chuva"]["binario"]["chuva_votacao"]
    pais = b["pais"][1]["abst_vs_ref_pp"]
    uf = next(iter(b["dentro_da_uf"]["grupos"].values()))["abst_vs_ref_pp"]
    mun = next(iter(b["dentro_do_municipio"]["grupos"].values()))["abst_vs_ref_pp"]
    fe_uf = next(
        iter(
            d["abstencao_x_chuva"]["regressoes"]["abstencao_2026"]["chuva_diaria"][
                "fe_uf"
            ]["termos"].values()
        )
    )
    pre = d["abstencao_x_bateria"]["dentro_do_predio"]["grupos"][
        "com bateria durante a votação"
    ]["abst_vs_ref_pp"]
    ch = d["cadeia_completa"]["variantes"]["chuva_forte_no_dia"][
        "abst_alta_por_combinacao"
    ]
    cadeia = {(v["chuva"], v["bateria"]): v["abst_alta_pct"] for v in ch}
    itens = [
        _item(
            "fato",
            f"Com chuva forte nas horas de votação, {pct(forte['parcela_pct']['valor'], 2)} das urnas registraram bateria, contra {pct(seca['parcela_pct']['valor'], 2)} sem chuva. A razão é de {dec(forte['razao_vs_ref']['valor'], 2)}× ({ic(forte['razao_vs_ref']['ic95'], 2, False)}). A rajada não se associa: {dec(or_r['odds_ratio'], 2)} por 10 km/h.",
        ),
        _item(
            "fato",
            f"A associação está na bateria simultânea, quando várias urnas do município registram juntas (razão de chances {dec(or_s['odds_ratio'], 2)} por 10 mm, {ic(or_s['ic95'], 2, False)}). A isolada não se separa do acaso ({dec(or_i['odds_ratio'], 2)}, {ic(or_i['ic95'], 2, False)}).",
        ),
        _item(
            "inf",
            f"A leitura mais simples é que chuva forte atinge a rede elétrica de municípios inteiros, não a tomada de uma urna. Dentro do município o intervalo é largo e inclui o zero ({pp(rm['coef'])} por 10 mm, {ic(rm['ic95'])}), então o dado sugere e não prova.",
        ),
        _item(
            "fato",
            f"A abstenção é {pp(pais['valor'])} maior onde choveu mais de 5 mm ({ic(pais['ic95'])}). Dentro da UF a diferença é de {pp(uf['valor'])} e dentro do município, {pp(mun['valor'])} ({ic(mun['ic95'])}): controlar a geografia reduz muito a associação bruta.",
        ),
        _item(
            "fato",
            f"Com efeito fixo de UF, a chuva do dia vem associada a abstenção menor ({pp(fe_uf['coef'])} por 10 mm, {ic(fe_uf['ic95'])}). Esse sinal não tem leitura causal razoável e some dentro do município.",
        ),
        _item(
            "fato",
            f"Dentro do mesmo prédio, a urna com bateria tem abstenção {pp(pre['valor'])} diferente da urna sem bateria ({ic(pre['ic95'])}). A cadeia chuva forte e bateria tem {pct(cadeia[(True, True)], 2)} de urnas com abstenção acima da mediana do município, contra {pct(cadeia[(False, False)], 2)} sem nenhuma das duas.",
        ),
        _item(
            "nao",
            "A tese de que a tempestade derrubou a eleição não encontra apoio no 1º turno. O dado não mostra chuva afastando eleitor da seção, e o registro de bateria não mede fila nem tempo parado.",
        ),
        _item(
            "nao",
            "Registro de bateria não é defeito nem indício de irregularidade. É operação prevista da urna, e este estudo não trata o registro como problema a explicar.",
        ),
        _item(
            "juizo",
            "Para o 2º turno, a atenção vale para a rede elétrica e para o deslocamento nas áreas de chuva forte prevista. O que o fiscal confere é a ata: horário da queda, da passagem à bateria e do retorno.",
        ),
        _item(
            "juizo",
            "A previsão mostra onde olhar. Não diz que o problema vai ocorrer, e a previsão de 25/10 muda todo dia.",
        ),
    ]
    corpo = (
        '<ul class="veredito">'
        + "".join(f"<li>{i}</li>" for i in itens)
        + "</ul>"
        + nota(
            "Cada item traz a etiqueta de fato medido, inferência, juízo editorial ou não sustentado. A discussão de cada número está no capítulo indicado pelo título."
        )
    )
    return secao(
        8,
        "veredito",
        "O que isto diz <em>e o que não diz</em>",
        "A chuva se associa às baterias simultâneas. Para a abstenção, a associação dentro do município não se separa de zero; isso não prova que o efeito seja nulo.",
        corpo,
    )


def cap9_uso(dados: Dados) -> str:
    corpo = (
        "<h3>Para o eleitor</h3>"
        + lista(
            [
                'Veja o boletim do seu local e da sua seção no <a href="politizesuavizinhanca.html">Politize sua vizinhança</a>: digite UF, zona e seção do título de eleitor, ou o CEP.',
                'No <a href="fiscais_mapa.html">mapa de fiscais</a>, procure o seu local e abra a ficha do prédio. O filtro “Risco climático previsto para 25/10” mostra se a célula de 0,5° do seu local está em risco alto ou médio.',
                "Se a energia cair na sua seção, a urna tem bateria interna para esse caso; o log registra quando ela entra em uso. Peça ao mesário que anote na ata.",
            ]
        )
        + "<h3>Para o fiscal</h3>"
        + lista(
            [
                'Abra o <a href="fiscais_mapa.html">mapa de fiscais</a>, escolha o estado e ligue “Risco climático previsto para 25/10”: Alto, ou Alto e médio. A lista de locais vem ordenável e exportável.',
                "Para ver onde choveu forte no 1º turno, escolha o estado e marque “Choveu forte no 1º turno (acima de 20 mm)”. Chuva e previsão são da célula da grade, não do prédio.",
                "Na ficha de cada prédio estão as seções, com a abstenção e o placar do 1º turno e os registros de bateria quando houve.",
            ]
        )
        + "<h3>O que registrar na ata quando a energia cair</h3>"
        + lista(
            [
                "O horário em que a energia caiu e o horário em que voltou, pelo relógio da seção.",
                "O horário em que a urna passou a operar com a bateria, se a mesa viu a mensagem, e se houve reinício.",
                "Se a votação parou ou ficou lenta, e por quanto tempo, com o número aproximado de eleitores na fila.",
                "Quem foi avisado (juiz, cartório, zona eleitoral) e o que foi orientado.",
            ]
        )
        + nota(
            "A ata é a prova do que aconteceu naquele prédio, naquele horário. O log diz que a urna operou com bateria; só a ata diz o que isso significou para a fila. Este é um guia de leitura, não orientação jurídica: vale o procedimento da Justiça Eleitoral."
        )
    )
    return secao(
        9,
        "uso",
        "Para o eleitor <em>e para o fiscal</em>",
        "Como usar o mapa, o Politize e a ata para transformar este relatório em checagem no dia 25.",
        corpo,
    )


def _tamanho(caminho, payload=None) -> str:
    n = (
        len(
            json.dumps(
                payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        )
        if payload is not None
        else caminho.stat().st_size
    )
    return (
        f"{dec(n / 1_000_000, 1)} MB" if n >= 1_000_000 else f"{inteiro(n / 1000)} KB"
    )


def cap10_fontes(dados: Dados) -> str:
    d = dados.d
    cob = d["cobertura"]
    fontes = tabela(
        ["Fonte", "Caminho", "Bytes", "SHA-256"],
        [
            [
                esc(f["descricao"]),
                f"<code>{esc(f['caminho'])}</code>",
                inteiro(f["bytes"]),
                f'<code class="hash">{esc(f["sha256"])}</code>',
            ]
            for f in d["fontes"]
        ],
        numericas=(2,),
        rotulo="Fontes e SHA-256",
        largura=860,
    )
    ctrl = d["controles"]
    ctrl_tab = tabela(
        ["Controle", "Esperado", "Obtido", "Passou"],
        [
            [
                esc(c["nome"]),
                esc(c["esperado"]),
                esc(c["obtido"]),
                "sim" if c["passou"] else "NÃO",
            ]
            for c in ctrl
        ],
        rotulo="Controles do motor",
        largura=760,
    )
    limites = [esc(x) for x in d["limites"]] + [
        "Reanálise não é estação. O ERA5 suaviza a chuva convectiva local, a que cai em pancada curta sobre um bairro; o erro de medida puxa a associação para perto de zero.",
        f"{inteiro(dados.urnas_sem_clima())} urnas ficam sem clima porque o local não tem coordenada no território; o exterior fica fora.",
        "Correlação não é causa. Os controles reduzem e não eliminam as diferenças entre regiões.",
    ]
    lit = "".join(
        f'<li><b>{esc(x["ref"])}</b> {esc(x["achado"])} <a href="{esc(x["url"])}" rel="noopener">Fonte</a>. <i>Uso aqui:</i> {esc(x["uso"])}.</li>'
        for x in dados.lit
    )
    botoes = "".join(
        f'<a class="botao" href="assets/clima_1t/{n}">{rot} ({_tamanho(ROOT / "docs" / "assets" / "clima_1t" / n, {k: v for k, v in dados.d.items() if k != "_interno"} if n == "dados.json" else None)})</a>'
        for n, rot in (
            ("dados.json", "Dados (JSON)"),
            ("locais.csv.gz", "Locais (CSV comprimido)"),
        )
    )
    passaram = sum(1 for c in ctrl if c["passou"])
    pr = d["previsao_25_10"]
    repro = (
        "python3 scripts/clima-1t.py --tudo          # coleta (retomável) e análises\n"
        "python3 scripts/clima-1t-previsao.py        # só a previsão, rodada todo dia pelo workflow\n"
        "python3 scripts/clima-1t-build.py           # gera esta página a partir do JSON\n"
        "python3 scripts/social-cards.py --only clima_abstencao_1t_2026\n"
        "pytest -q tests/test_clima_1t.py tests/test_clima_1t_pagina.py"
    )
    corpo = (
        f"<p>Clima observado: Open-Meteo archive (reanálise ERA5 e ERA5-Land), {inteiro(cob['archive']['celulas'])} células de 0,25° em {inteiro(cob['archive']['requisicoes'])} requisições, "
        f"janela de 02 a 05/10, horário em 04/10. Previsão: Open-Meteo forecast, {inteiro(pr['coleta']['celulas'])} células de 0,5°, gerada em {hora_br(pr['gerado_em'])}. "
        "Boletins de urna, logs e cadastro de locais: TSE. O hash da previsão é o do retrato usado aqui; o arquivo do mapa muda todo dia.</p>"
        + fontes
        + f'<div class="downloads">{botoes}</div>'
        + "<h3>Limites</h3>"
        + lista(limites)
        + "<h3>Literatura</h3>"
        + f"<ul>{lit}</ul>"
        + "<h3>Reprodução</h3>"
        + f"<pre><code>{esc(repro)}</code></pre>"
        + detalhes(
            f"Controles do motor: {passaram} de {len(ctrl)} passaram",
            ctrl_tab,
        )
        + detalhes(
            "Decisões de método",
            lista([esc(x) for x in d["decisoes"]]),
        )
        + nota(
            f"Janela da chuva: {esc(d['janela_votacao']['regra'])}. IC por bootstrap de células de 0,25° ({inteiro(d['parametros']['reps'])} réplicas, semente {d['parametros']['seed']})."
        )
        + caixa(
            "Regra da casa.",
            "Registro de bateria é operação prevista da urna, correlação não é causa, e a leitura é agregada por seção e por local: nada aqui identifica eleitor.",
        )
    )
    return secao(
        10,
        "fontes",
        "Fontes, método <em>e limites</em>",
        "Cada número vem do JSON do motor. Fontes com SHA-256, limites declarados e o comando que reproduz tudo.",
        corpo,
    )


__all__ = ["cap8_veredito", "cap9_uso", "cap10_fontes"]
