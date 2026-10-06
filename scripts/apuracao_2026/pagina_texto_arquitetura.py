"""Bloco de arquitetura do capítulo 3: onde um sistema como o do TSE engasga e o desenho que não engasga.

Os números saem de `arquitetura.json` (gerado por `scripts/apuracao-2026-arquitetura.py`)
e as fontes, da lista curada dentro dele. A hipótese do autor sobre o banco de dados
fica rotulada como hipótese em todo lugar em que aparece; o que os documentos provam
vem com o selo de verificado e o link ao lado.
"""

from __future__ import annotations

from html import escape

from .pagina_comum import (
    Dados,
    caixa,
    checar,
    figura_catalogo,
    inteiro,
    milhoes,
    nota,
    num,
    p,
    tabela,
)
from .pagina_texto import EXTENSO, dados_figuras

ARQ = "arquitetura.json"
CHAVES = [
    "amostra.ufs_cobertas",
    "recebimento_2026.lacunas",
    "recebimento_2022.pico",
    "publicacao_2026.pico_versoes",
    "nacional.pico_sustentado",
    "nacional.parada_mais_longa",
    "volume.linhas_por_secao",
    "fontes",
]


def _fonte(A: dict, ident: str, rotulo: str | None = None) -> str:
    f = next((x for x in A["fontes"] if x["id"] == ident), None)
    if f is None:
        return escape(rotulo or ident)
    data = str(f["data"])[:10]
    dia = f"{data[8:10]}/{data[5:7]}/{data[:4]}" if data[:4].isdigit() else data
    txt = rotulo or f"{f['veiculo']}, {dia}"
    return f'<a href="{escape(f["url"])}">{escape(txt)}</a>'


def _hm(s: str) -> str:
    return s[11:16] if len(s) > 11 else s


def _mb(x: float) -> str:
    return f"{num(x / 1000, 1)} GB" if x >= 1000 else f"{num(x, 0)} MB"


def _fig(nome: str, d: Dados) -> str:
    return figura_catalogo(nome, dados_figuras(d))


# ------------------------------------------------------------------ engasga


def documentos(A: dict) -> str:
    v = A["volume"]
    return p(
        "Em 2020 o TSE centralizou a totalização num banco Oracle em dois equipamentos Exadata X8, numa sala-cofre do "
        f"tribunal ({_fonte(A, 'tse_nota_tecnica_2020', 'nota técnica do TSE, 17/11/2020')}; "
        f"{_fonte(A, 'aosfatos_sala_cofre_2020', 'Aos Fatos, 28/11/2020')}). A nota diz que as tabelas recebiam mais de "
        f"{milhoes(v['linhas_por_minuto_nota_tse_2020'], 0)} de linhas por minuto a partir das 17h e que a lentidão daquela noite "
        "veio do otimizador do banco: o plano de execução feito com as tabelas vazias não servia com elas cheias. O "
        "portal de transparência lista depois a expansão do contrato Oracle Cloud at Customer e suporte Oracle em 2025 "
        f"({_fonte(A, 'tse_contratacoes_tic', 'TSE, contratações de TIC')}). Nenhum documento lido diz em que banco e "
        "equipamento rodaram a totalização e a divulgação de 2026; o anexo técnico não abriu (o portal respondeu “muitas "
        "requisições”). O tribunal disse que o congestionamento ficou na divulgação, na “conversão dos dados”, e que a "
        f"totalização não foi afetada ({_fonte(A, 'tse_encerramento_2026', 'TSE, 04/10/2026')}; "
        f"{_fonte(A, 'cnn_congestionamento_2026', 'CNN Brasil, 04/10/2026')}). Não há relatório técnico.",
        "verificado",
    )


def hipotese_autor() -> str:
    return nota(
        "hipotese",
        "A importação dos boletins fica lenta quando o fluxo cresce, porque cada lote atualiza índices e totais na mesma "
        "operação. Os documentos de 2020 a tornam plausível e não a provam para 2026; o TSE situa o problema na "
        "divulgação, que pode ter banco próprio. O relatório do incidente separaria as duas leituras.",
        "Do autor (Leonardo Dias), não comprovada.",
    )


def carimbo(A: dict) -> str:
    am = A["amostra"]
    lac = A["recebimento_2026"]["lacunas"]
    des = A["recebimento_2026"].get("desaceleracao")
    frase = (
        f"O carimbo de recebimento que cada seção traz no próprio arquivo ({inteiro(am['secoes_com_recebimento'])} "
        f"seções coletadas) some nas {EXTENSO.get(len(lac), len(lac))} janelas da primeira figura do capítulo e volta em rajada depois de cada uma."
    )
    if des:
        r1, r2 = des["retomada"]
        frase += (
            f" Antes de zerar, desacelera: de {des['janela'][0]} a {des['janela'][1]} cai a {inteiro(des['media_janela'])} "
            f"por minuto, contra média de {inteiro(des['media_base'])} ({inteiro(des['min_base'])} a "
            f"{inteiro(des['max_base'])}) entre {des['base'][0]} e {des['base'][1]}, e volta a {inteiro(r1[1])} às "
            f"{r1[0]} e {inteiro(r2[1])} às {r2[0]}: o ritmo cai a cerca de um terço antes de parar."
        )
    return p(frase, "verificado") + p(
        "Ou a recepção parou de registrar boletins, ou o carimbo vem de um componente posterior que parou junto com a "
        "divulgação. Os arquivos não dizem qual; nas duas leituras, a parada não foi só de vitrine.",
        "inferencia",
    )


def volume(A: dict) -> str:
    v = A["volume"]
    pk = A["nacional"]["pico_sustentado"]
    r22 = A["recebimento_2022"]
    at = r22["atraso_recebimento_totalizacao_s"]
    pub = A["publicacao_2026"]
    linhas = [
        [
            "Boletim de urna, tamanho médio",
            f"{num(v['bu_bytes']['media'] / 1000, 1)} KB",
        ],
        [
            f"Os {inteiro(A['amostra']['secoes_pais'])} boletins do país",
            f"{_mb(v['bu_total_mb'])}; com os logs, {_mb(v['bu_total_mb'] + v['log_total_mb'])}",
        ],
        [
            "Linhas de voto (candidato por cargo)",
            f"{num(v['linhas_por_secao'], 0)} por boletim; {num(v['linhas_voto_total'] / 1e6, 1)} milhões na noite",
        ],
        [
            f"Pico do arquivo nacional ({_hm(pk['de'])} a {_hm(pk['ate'])})",
            f"{inteiro(pk['secoes_por_minuto'])} seções por minuto, {num(v['pico_secoes_por_segundo'], 0)} por segundo, "
            f"{inteiro(v['pico_linhas_por_segundo'])} linhas por segundo",
        ],
        [
            "Pico de publicação",
            f"{inteiro(pub['pico_versoes']['versoes'])} versões de arquivos às {pub['pico_versoes']['minuto']}; "
            f"{num(pub['pico_mb']['mb'], 0)} MB por minuto, contra {num(v['pico_bu_mb_por_minuto'], 0)} MB de boletins",
        ],
        [
            "2022, país inteiro",
            f"pico de {inteiro(r22['pico']['secoes'])} boletins por minuto às {r22['pico']['minuto']}; da chegada à "
            f"totalização, {num(at['p50'], 0)} segundos na mediana e {num(at['p90'], 0)} no 90º percentil",
        ],
        [
            "Banco da casa, num notebook",
            f"{inteiro(v['linhas_voto_amostra'])} linhas de voto e {inteiro(pub['versoes_total_banco'])} versões de arquivos",
        ],
    ]
    return tabela(
        ["Medida", "Valor"],
        linhas,
        "A noite em números: volume pequeno para qualquer banco de dados atual.",
    ) + p(
        "Se houve gargalo, ele é de desenho (como a escrita, a soma e a publicação se encadeiam), não de capacidade: "
        "2022 recebeu a mesma ordem de boletins por minuto sem parar. Nenhum documento descreve o desenho de 2026.",
        "inferencia",
    )


def mecanismo(A: dict) -> str:
    return p(
        "Um banco relacional engasga com pouco volume de quatro jeitos: índices (cada índice é mais uma escrita por "
        "linha), totais atualizados no lugar (todas as transações disputam a trava da linha do país), soma recalculada a "
        "cada lote (o custo cresce com o total) e publicação no mesmo caminho da carga. E fila não cresce em linha reta: "
        "perto da capacidade a espera explode, e entre 18h e 20h chega o país inteiro.",
        "inferencia",
    )


ANALOGIA = caixa(
    "analogy",
    "Em linguagem de casa",
    "Um caixa de padaria anota cada venda e soma a fita no fim. Outro, a cada venda, reconta a gaveta e pendura um "
    "cartaz novo com o total. Com a fila dobrando o quarteirão, o segundo para de atender e o cartaz fica parado numa "
    "hora antiga. Ninguém roubou nada; o método não aguenta a hora do rush.",
)


# ------------------------------------------------------------------ não engasga


def desenho(A: dict) -> str:
    v = A["volume"]
    return nota(
        "juizo",
        "<ol>"
        "<li>Gravar cada boletim verificado uma vez num log de eventos só de acréscimo, particionado por UF, com hash "
        "encadeado.</li>"
        "<li>Somar por consumidores idempotentes: a chave é a seção, e o mesmo boletim lido duas vezes soma uma.</li>"
        "<li>Totais incrementais: cada boletim acrescenta os próprios votos à zona, ao município, à UF e ao país, sem "
        "recalcular nada.</li>"
        "<li>Publicar por fotografia assíncrona e assinada, a cada meio minuto, com o número do último evento incluído: "
        "se a vitrine atrasa, a soma segue.</li>"
        "<li>Ensaiar com o volume real. Em 2020 só dois de cinco testes rodaram no equipamento novo, e a nota técnica "
        "admite que a calibragem teria evitado o atraso.</li>"
        f"<li>Banco distribuído só por disponibilidade entre centros de dados: a noite inteira cabe em "
        f"{num(v['linhas_voto_total'] / 1e6, 0)} milhões de linhas. Fila, totais incrementais e publicação assíncrona "
        "rodam sobre um banco relacional comum, Oracle inclusive.</li></ol>",
        "Recomendação ao TSE.",
    )


def uber(A: dict) -> str:
    v = A["volume"]
    return p(
        "É o padrão de quem tem volume muito maior. A Uber usa o Kafka como espinha dorsal de eventos, com trilhões de "
        f"mensagens por dia ({_fonte(A, 'uber_kafka_2020', 'Uber Engineering, 2020')}; "
        f"{_fonte(A, 'uber_sigmod_2021', 'SIGMOD 2021')}), e já passava de um milhão de escritas por segundo no Cassandra "
        f"em 2016 ({_fonte(A, 'highscalability_uber_2016', 'High Scalability')}; "
        f"{_fonte(A, 'uber_cassandra_2023', 'Uber Engineering, 2023')}), cerca de "
        f"{num(1e6 / v['pico_linhas_por_segundo'], 0)} vezes o pico de linhas de voto de 2026. O TSE já tem fila: em 2022 "
        f"a TI descreveu a chegada dos boletins como “uma fila de banco” ({_fonte(A, 'conjur_fila_2022', 'ConJur')}). O "
        "ponto é o que vem depois dela.",
        "verificado",
    )


def publicar(A: dict) -> str:
    return (
        p(
            "O desenho ideal é também o mais auditável: com log imutável e hash encadeado, qualquer pessoa refaz a soma do "
            "zero. O TSE encerraria a dúvida publicando o desenho da totalização e da divulgação de 2026, o log de eventos "
            "da noite (cada recebimento, cada inclusão na totalização, cada arquivo gerado) e o relatório do incidente. Em "
            "2020 a nota técnica saiu dois dias depois do 1º turno.",
            "juizo",
        )
        + "<p><strong>O dossiê prova a parada pelos arquivos públicos; a causa é hipótese até o TSE publicar o relatório.</strong></p>"
    )


def bloco(d: Dados) -> str:
    """HTML do bloco de arquitetura do capítulo 3; vazio se `arquitetura.json` ainda não existe."""
    A = d.get(ARQ)
    if not A:
        return ""
    checar(d, ARQ, CHAVES)
    h = '<h3 id="arquitetura">Onde um sistema como esse engasga</h3>'
    h += documentos(A) + hipotese_autor() + carimbo(A)
    h += volume(A) + _fig("volume_noite", d) + mecanismo(A) + ANALOGIA
    h += '<h3 id="arquitetura-ideal">O desenho que não engasga</h3>'
    h += desenho(A) + uber(A) + _fig("arquitetura_totalizacao", d) + publicar(A)
    return h
