"""Painel da previsão durante a votação, por período e fuso horário."""

from clima_1t.horaria import PERIODOS, janela_local

from . import mapas
from .comum import detalhes, tabela
from .util import Dados, dec, esc, hora_br, inteiro, pct

FUSOS = [
    (-3, "Brasília e demais estados"),
    (-4, "MT, MS, RO, RR e maior parte do AM"),
    (-5, "Acre e 11 municípios do AM"),
    (-2, "Fernando de Noronha"),
]
TSE = "https://www.justicaeleitoral.jus.br/fato-ou-boato/checagens/2026/e-falso-que-eleitores-devam-votar-em-dias-diferentes-dependendo-do-candidato-escolhido-entenda"


def _janela(ini, fim):
    return f'<span class="hora-local" data-inicio="{ini}" data-fim="{fim}">{ini:02d}h–{fim:02d}h</span>'


def secao_horaria(dados: Dados) -> str:
    p = dados.previsao
    resumos = p["resumo_periodos"]
    botoes, paineis = [], []
    for chave, (nome, ini, fim) in PERIODOS.items():
        r = resumos[chave]
        br = r["grupos"]["BR"]
        ufs = sorted(
            ((uf, g) for uf, g in r["grupos"].items() if uf != "BR"),
            key=lambda ug: -(ug[1]["chuva_media_mm"] or 0),
        )
        topo = ", ".join(
            f"{uf} ({dec(g['chuva_media_mm'], 1)} mm)" for uf, g in ufs[:5]
        )
        tab = tabela(
            [
                "UF",
                "Chuva média (mm)",
                "Média por hora (mm/h)",
                "Cadastro com ≥1 mm",
                "Cobertura",
            ],
            [
                [
                    uf,
                    dec(g["chuva_media_mm"], 2),
                    dec(g["chuva_media_por_hora_mm"], 2),
                    pct(g["cadastro_chuva_1mm_pct"], 1),
                    pct(100 * g["cobertos"] / g["eleitores"], 1),
                ]
                for uf, g in ufs
            ],
            numericas=(1, 2, 3, 4),
            ordenavel=True,
            largura=620,
            ident="chuva-periodo-" + chave,
            rotulo=f"Chuva por UF: {nome}",
        )
        botoes.append(
            f'<button type="button" data-periodo="{chave}" aria-controls="periodo-{chave}" '
            f'aria-pressed="false">{nome}<small>{_janela(ini, fim)}</small></button>'
        )
        mapa = mapas.mapa_chuva_prevista(dados, chave, "maphorario")
        paineis.append(
            f'<div class="painel-periodo" id="periodo-{chave}"><h3>{nome} · {_janela(ini, fim)}</h3>'
            '<div class="mapas-comparados painel-horario">'
            f"<figure>{mapa}<figcaption>"
            f"Acumulado previsto em {fim-ini} horas. Mesma escala em todos os mapas; "
            "branco fora da grade significa ausência de dado.</figcaption></figure>"
            '<div class="leitura-periodo">'
            f'<p class="numero-chuva">{dec(br["chuva_media_mm"], 2)} <small>mm</small></p>'
            "<p>Chuva média no Brasil, ponderada pelo cadastro georreferenciado.</p>"
            f'<p><b>{dec(br["chuva_media_por_hora_mm"], 2)} mm/h</b> em média na janela, '
            f"que dura {fim-ini} horas. Essa taxa permite comparar períodos de durações diferentes.</p>"
            f'<p><b>{pct(br["cadastro_chuva_1mm_pct"], 1)}</b> do cadastro está em células '
            f'com pelo menos 1 mm no período ({inteiro(br["eleitores_chuva_1mm"])} eleitores). '
            "É exposição territorial, não previsão de faltas.</p>"
            f"<p>Maiores médias estaduais: <b>{topo}</b>.</p></div></div>"
            + detalhes("Comparar as 27 UFs neste período", tab)
            + "</div>"
        )
    partes = [resumos[k] for k in PERIODOS if k != "votacao"]
    mais = max(partes, key=lambda r: r["grupos"]["BR"]["chuva_media_por_hora_mm"] or 0)
    tabela_resumo = tabela(
        [
            "Período (Brasília)",
            "Duração",
            "Chuva média (mm)",
            "Média por hora (mm/h)",
            "Cadastro com ≥1 mm",
        ],
        [
            [
                f'{r["nome"]} · {r["inicio_brasilia"]}h–{r["fim_brasilia"]}h',
                f'{r["duracao_h"]} h',
                dec(r["grupos"]["BR"]["chuva_media_mm"], 2),
                dec(r["grupos"]["BR"]["chuva_media_por_hora_mm"], 2),
                pct(r["grupos"]["BR"]["cadastro_chuva_1mm_pct"], 1),
            ]
            for r in partes
        ],
        numericas=(1, 2, 3, 4),
        largura=700,
        ident="resumo-horario",
        rotulo="Comparação dos períodos no Brasil",
    )
    fusos = tabela(
        ["Local", "Votação", "Manhã", "Almoço", "14h–15h BRT", "Tarde"],
        [
            [nome] + [janela_local(ini, fim, utc) for _, ini, fim in PERIODOS.values()]
            for utc, nome in FUSOS
        ],
        largura=760,
        rotulo="Conversão das janelas para hora local",
    )
    opcoes = "".join(
        f'<option value="{utc}">{nome} (UTC{utc})</option>' for utc, nome in FUSOS
    )
    return (
        '<section class="chapter" id="previsao-horaria"><div class="section-heading">'
        '<span class="section-number">25/10</span><div><h2>Chuva <em>na hora de votar</em></h2>'
        '<p class="lead">Nove horas, quatro períodos. A previsão agora acompanha a votação: '
        "das 8h às 17h de Brasília, com conversão para o horário local.</p></div></div>"
        f'<p class="note">Consulta: {hora_br(p["gerado_em"])} · {inteiro(p["coleta"]["respondidas"])} '
        f'células · cobertura de {pct(100*resumos["votacao"]["grupos"]["BR"]["cobertos"]/resumos["votacao"]["grupos"]["BR"]["eleitores"], 1)} do cadastro mapeado.</p>'
        "<p>Os períodos são definidos pelo relógio de Brasília. A faixa <b>14h–15h</b> "
        "completa a hora entre almoço e tarde; as quatro partes somam exatamente a votação. "
        "Chuva antes das 8h e depois das 17h não entra na exposição calculada aqui.</p>"
        '<div id="controles-horarios" hidden><label for="fuso-horario">Mostrar horários de </label>'
        f'<select id="fuso-horario">{opcoes}</select><p class="note">O fuso altera apenas os rótulos do relógio; '
        "os mapas continuam mostrando o Brasil inteiro na mesma janela de votação.</p>"
        f'<div class="botoes-periodos" role="group" aria-label="Período da previsão">{"".join(botoes)}</div></div>'
        + "".join(paineis)
        + "<h3>Onde a chuva se concentra no tempo</h3>"
        + f'<p>Na média nacional ponderada, <b>{esc(mais["nome"].lower())}</b> tem a maior chuva por hora '
        f'({dec(mais["grupos"]["BR"]["chuva_media_por_hora_mm"], 2)} mm/h). '
        "Essa leitura pode mudar por cidade; não identifica quando os eleitores irão sair de casa. "
        "A parcela exposta em cada período não deve ser somada: a mesma pessoa pode aparecer em vários.</p>"
        + tabela_resumo
        + detalhes(
            "Horários locais, incluindo Amazonas e Fernando de Noronha",
            fusos
            + "<p>Seguem o Acre no Amazonas: Amaturá, Atalaia do Norte, Benjamin Constant, Eirunepé, "
            "Envira, Guajará, Ipixuna, Itamarati, Jutaí, Tabatinga e São Paulo de Olivença. "
            f'<a href="{TSE}">Fonte: Justiça Eleitoral</a>.</p>',
        )
        + detalhes(
            "Como calculamos a previsão horária",
            "<p>A API informa a chuva acumulada na hora anterior ao carimbo: "
            "09:00 cobre 08h–09h. Somamos os carimbos de 09:00 a 17:00, em America/Sao_Paulo. "
            "Manhã: 09–12; almoço: 13–14; transição: 15; tarde: 16–17. "
            "Rajada é o máximo na janela. Probabilidade é o maior valor horário de chuva acima de 0,1 mm; "
            "não somamos probabilidades nem a apresentamos como probabilidade conjunta da janela. "
            "Qualquer hora ou variável ausente torna a classificação daquela janela indisponível. "
            "O risco usa os mesmos limiares editoriais anteriores, agora restritos à votação; "
            "não foi calibrado como modelo de abstenção. Médias regionais ponderam cada célula pelos eleitores "
            "do cadastro; a média por hora divide o acumulado pela duração, sem medir picos instantâneos.</p>"
            "<p>A resolução horária melhora o recorte de exposição, mas não valida o acerto da previsão. "
            "A análise histórica abaixo mantém sua janela original de 7h–18h e não é recalculada como se fosse 8h–17h. "
            '<a href="https://open-meteo.com/en/docs">Documentação meteorológica</a> · '
            '<a href="assets/fiscais_mapa/clima/previsao.json">Séries horárias, períodos e acumulado diário (JSON)</a>.</p>',
        )
        + "</section>"
    )
