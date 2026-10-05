"""Bloco de arquitetura do capítulo 3: onde um sistema como o do TSE engasga e o desenho que não engasga.

Os números saem de `arquitetura.json` (gerado por `scripts/apuracao-2026-arquitetura.py`)
e as fontes, da lista curada dentro dele. A hipótese do autor sobre o banco de dados
fica rotulada como hipótese em todo lugar em que aparece; o que os documentos provam
vem com o selo de verificado e o link ao lado.
"""

from __future__ import annotations

from html import escape

from .pagina_comum import Dados, checar, figura_catalogo, inteiro, num, p
from .pagina_texto import dados_figuras

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
        "Os documentos públicos dizem três coisas sobre a máquina. Em 2020 o TSE centralizou pela primeira vez a "
        "totalização de todo o país num banco de dados Oracle rodando em dois equipamentos Exadata X8, um com oito nós "
        "de processamento e outro com quatro de reserva, numa sala-cofre do tribunal, operados pela equipe do TSE "
        f"({_fonte(A, 'tse_nota_tecnica_2020', 'nota técnica do TSE, 17/11/2020')}; "
        f"{_fonte(A, 'aosfatos_sala_cofre_2020', 'Aos Fatos, 28/11/2020')}). A mesma nota diz que as tabelas recebiam "
        f"“mais de um milhão de linhas por minuto” a partir das 17h ({inteiro(v['linhas_por_minuto_nota_tse_2020'])} por "
        "minuto, na conta deles) e que a lentidão daquela noite veio do otimizador do banco: o plano de execução gerado "
        "com as tabelas vazias não servia com elas cheias, e o sistema de totalização foi parado para gerar outro. "
        "O portal de transparência lista depois uma “expansão” do contrato Oracle Cloud at Customer (aba de 2022 e 2023) "
        f"e, em 2025, suporte a hardware e sistemas Oracle ({_fonte(A, 'tse_contratacoes_tic', 'TSE, contratações de TIC')}).",
        "verificado",
    )


def sem_prova_2026(A: dict) -> str:
    return p(
        "Nenhum documento lido diz em que banco e em que equipamento rodaram a totalização e a divulgação de 2026, nem "
        "descreve o programa de divulgação. O anexo técnico da expansão do contrato não pôde ser lido (o portal do TSE "
        "respondeu “muitas requisições”). Sobre a noite, o tribunal disse que o congestionamento ficou no sistema de "
        "divulgação, na “conversão dos dados”, que a totalização não foi afetada e que a TI isolou outros sistemas para o "
        f"fluxo passar ({_fonte(A, 'tse_encerramento_2026', 'TSE, 04/10/2026, 23h56')}; "
        f"{_fonte(A, 'cnn_congestionamento_2026', 'CNN Brasil, 04/10/2026')}). Não há relatório técnico.",
        "verificado",
    )


def hipotese_autor() -> str:
    return (
        '<aside class="hyp"><b>Hipótese do autor (Leonardo Dias), não comprovada</b>'
        "A centralização importa os boletins num banco Oracle sobre Exadata, e a importação fica lenta quando o fluxo "
        "cresce, porque cada lote atualiza os índices das tabelas grandes e os totais na mesma operação. Os documentos de "
        "2020 tornam a hipótese plausível: o banco, o equipamento e um gargalo de banco na mesma hora da noite estão "
        "documentados. Não a provam para 2026. Dois fatos pesam contra a forma literal: o TSE situa o problema na "
        "divulgação, não na totalização, e a divulgação também pode ter o próprio banco. Os dados públicos não separam "
        "as duas leituras; o relatório do incidente separaria.</aside>"
    )


def carimbo(A: dict) -> str:
    am = A["amostra"]
    lac = A["recebimento_2026"]["lacunas"]
    pl = A["nacional"]["parada_mais_longa"]
    trechos = [
        f"{_hm(x['de'])} a {_hm(x['ate'])} ({num(x['minutos'], 1)} min)" for x in lac
    ]
    return p(
        "Há um dado novo, que os arquivos públicos guardam e que ninguém tinha olhado. Cada seção tem no próprio arquivo "
        "a hora em que o TSE registrou o recebimento do boletim. Na coleta seção a seção da casa "
        f"({inteiro(am['secoes_com_recebimento'])} seções de {len(am['ufs_cobertas'])} UFs), esse carimbo some em "
        f"{len(lac)} intervalos: {', '.join(trechos)}. São as mesmas janelas das paradas do arquivo nacional e da pausa "
        f"geral; a última cobre a pausa de 19h32 a 20h02 quase minuto a minuto. Depois de cada lacuna os carimbos voltam "
        f"em rajada. A parada mais longa do nacional represou {inteiro(pl['secoes_no_salto'])} seções.",
        "verificado",
    )


def desaceleracao(A: dict) -> str:
    des = A["recebimento_2026"].get("desaceleracao")
    if not des:
        return ""
    r1, r2 = des["retomada"]
    return p(
        f"A parada geral não veio de repente. De {des['janela'][0]} a {des['janela'][1]}, os carimbos caem para cerca "
        f"de {inteiro(des['media_janela'])} por minuto, contra {inteiro(des['min_base'])} a "
        f"{inteiro(des['max_base'])} por minuto (média de {inteiro(des['media_base'])}) entre {des['base'][0]} e "
        f"{des['base'][1]}: o ritmo cai a cerca de um terço antes de zerar. Na volta, {inteiro(r1[1])} às {r1[0]} e "
        f"{inteiro(r2[1])} às {r2[0]}, acima do ritmo anterior. Medido na coleta parcial, sem extrapolação; vale a "
        "mesma ressalva do carimbo, que pode ser aplicado por um componente posterior ao recebimento. Desacelerar antes "
        "de travar é o comportamento de fila perto da saturação.",
        "verificado",
    )


def carimbo_leitura() -> str:
    return p(
        "Duas leituras cabem nesse fato. Ou a recepção parou de registrar boletins, e então o problema estava antes da "
        "divulgação; ou o carimbo de “recebimento” é aplicado por um componente que fica depois da recepção e parou junto "
        "com a divulgação. Os arquivos públicos não dizem qual. Em qualquer das duas, o carimbo mostra que a parada não "
        "foi só de vitrine: um registro que o próprio TSE chama de recebimento também ficou em branco.",
        "inferencia",
    )


def volume(A: dict) -> str:
    v = A["volume"]
    pk = A["nacional"]["pico_sustentado"]
    r22 = A["recebimento_2022"]
    at = r22["atraso_recebimento_totalizacao_s"]
    return p(
        f"O volume é pequeno. Um boletim tem em média {num(v['bu_bytes']['media'] / 1000, 1)} KB; os "
        f"{inteiro(A['amostra']['secoes_pais'])} boletins do país somam {_mb(v['bu_total_mb'])}, e com os registros de log das urnas, "
        f"{_mb(v['bu_total_mb'] + v['log_total_mb'])}. Cada boletim vira em média {num(v['linhas_por_secao'], 0)} linhas "
        f"de voto (candidato por cargo): {num(v['linhas_voto_total'] / 1e6, 1)} milhões de linhas na noite inteira. O "
        f"ritmo mais alto do arquivo nacional, entre {_hm(pk['de'])} e {_hm(pk['ate'])}, foi de "
        f"{inteiro(pk['secoes_por_minuto'])} seções por minuto, {num(v['pico_secoes_por_segundo'], 0)} por segundo, "
        f"cerca de {inteiro(v['pico_linhas_por_segundo'])} linhas de voto por segundo. Em 2022, com o país inteiro medido "
        f"seção a seção, o pico de recebimento foi de {inteiro(r22['pico']['secoes'])} boletins por minuto às "
        f"{r22['pico']['minuto']}, e a mediana entre receber um boletim e incluí-lo na primeira totalização foi de "
        f"{num(at['p50'], 0)} segundos (90% em até {num(at['p90'], 0)}).",
        "verificado",
    )


def volume_leitura(A: dict) -> str:
    v = A["volume"]
    pub = A["publicacao_2026"]
    return p(
        "Isso é pouco para qualquer banco de dados atual, e muito menos que a classe de equipamento que o TSE comprou. "
        f"O banco desta casa, num notebook, guarda {inteiro(v['linhas_voto_amostra'])} linhas de voto por seção e "
        f"{inteiro(pub['versoes_total_banco'])} versões de arquivos do TSE. O pico de 2026 também não foi inédito: 2022 "
        "recebeu a mesma ordem de boletins por minuto sem parar. Se houve gargalo, ele é de desenho (como a escrita, a "
        "soma e a publicação se encadeiam), não de capacidade. É inferência: nenhum documento descreve o desenho de 2026.",
        "inferencia",
    )


def mecanismo(A: dict) -> str:
    pub = A["publicacao_2026"]
    v = A["volume"]
    return p(
        "Como um banco relacional engasga com pouco volume. Primeiro, índices: cada linha gravada numa tabela com "
        "cinco índices B-tree vira seis escritas, uma na tabela e uma em cada índice, e cada escrita de índice pode "
        "dividir páginas e disputar as mesmas folhas quando as chaves chegam em ordem parecida (hora, seção). "
        "Segundo, totais: se o total por candidato, município, UF e país mora numa tabela e cada lote faz "
        "<code>UPDATE</code> nela, todas as transações querem a mesma linha (a do país, a do candidato) e fazem fila "
        "pela trava dessa linha. Terceiro, recomputar: se cada lote dispara um <code>SUM</code> sobre tudo o que já "
        "foi apurado, o custo de cada lote cresce com o total, e às 19h o total já é dezenas de vezes o das 17h30. Quarto, "
        "publicar dentro do mesmo caminho: se a geração dos arquivos públicos lê o banco enquanto a carga escreve, "
        "leitura e escrita disputam o mesmo recurso.",
        "inferencia",
    ) + p(
        "A publicação multiplica o trabalho. Cada lote de boletins obriga a regenerar os arquivos de cada cargo em "
        f"cada nível que ele toca: no pico, o coletor da casa viu {inteiro(pub['pico_versoes']['versoes'])} versões "
        f"novas de arquivos num só minuto ({pub['pico_versoes']['minuto']}) e até "
        f"{num(pub['pico_mb']['mb'], 0)} MB de arquivos publicados por minuto, contra cerca de "
        f"{num(v['pico_bu_mb_por_minuto'], 0)} MB de boletins entrando no mesmo intervalo. E nenhum desses "
        "mecanismos cresce em linha reta. Fila é como trânsito: com a via a 70% da capacidade, o carro espera pouco; "
        "a 95%, a espera explode, e um minuto de rajada leva muitos minutos para escoar. Entre 18h e 20h chegam os "
        "boletins de quase todo o país ao mesmo tempo, então é ali que um desenho síncrono passa do ponto.",
        "inferencia",
    )


ANALOGIA = (
    '<aside class="analogy"><b>Em linguagem de casa</b>Pense no caixa de uma padaria em dia de festa. Um caixa anota '
    "cada venda e, ao fim, soma a fita. Outro caixa, a cada venda, para tudo, reconta a gaveta inteira, reescreve a "
    "lista de todos os produtos vendidos no dia em ordem alfabética e pendura um cartaz novo na porta com o total. "
    "Com três clientes por hora, os dois dão conta. Com a fila dobrando o quarteirão às seis da tarde, o segundo para "
    "de atender, e o cartaz da porta fica parado numa hora antiga. Ninguém roubou nada; o método é que não aguenta "
    "a hora do rush.</aside>"
)


# ------------------------------------------------------------------ não engasga


def desenho(A: dict) -> str:
    return p(
        "O desenho que não engasga separa em etapas o que hoje parece ser um caminho só. Um: cada boletim verificado é "
        "gravado uma única vez num log de eventos, só acrescentado ao fim, sem índice nem total a atualizar (Kafka ou "
        "equivalente, com partição por UF ou por zona, para a ordem valer dentro de cada partição). Dois: consumidores "
        "leem o log no próprio ritmo, um grupo por UF, e são idempotentes: a chave é a seção, e o mesmo boletim lido "
        "duas vezes soma uma vez só. Três: os totais são incrementais, cada boletim acrescenta os próprios votos aos "
        "contadores da zona, do município, da UF e do país, sem recalcular o que já estava somado. Quatro: a publicação "
        "é assíncrona, uma fotografia assinada dos totais a cada 30 segundos, com o número do último evento incluído. Se "
        "a publicação atrasar, só a vitrine atrasa; a soma segue, e quando a vitrine volta ela mostra o estado certo de "
        "uma vez, sem lote represado.",
        "juizo",
    )


def uber(A: dict) -> str:
    return p(
        "Esse é o padrão que empresas com volume muito maior usam. A Uber descreve o Kafka como a espinha dorsal que leva "
        "os eventos dos aplicativos para os sistemas de processamento, com trilhões de mensagens e petabytes por dia "
        f"({_fonte(A, 'uber_kafka_2020', 'Uber Engineering, 21/12/2020')}; "
        f"{_fonte(A, 'uber_sigmod_2021', 'Fu e Soman, SIGMOD 2021')}), e grava em Cassandra dados que chegam o tempo todo, "
        "como a posição de motoristas e passageiros a cada 30 segundos, com mais de um milhão de escritas por segundo "
        f"nos maiores clusters em 2016 ({_fonte(A, 'highscalability_uber_2016', 'palestra de 2016, resumo da High Scalability')}) "
        f"e centenas de clusters em 2023 ({_fonte(A, 'uber_cassandra_2023', 'Uber Engineering, 20/07/2023')}). O TSE já "
        "tem uma fila: em 2022 a própria área de TI descreveu a chegada dos boletins como “uma fila de banco” "
        f"({_fonte(A, 'conjur_fila_2022', 'ConJur, 29/10/2022')}). O ponto não é ter fila; é o que acontece depois "
        "dela.",
        "verificado",
    )


def banco_distribuido(A: dict) -> str:
    v = A["volume"]
    return p(
        "E o banco distribuído? HBase e Cassandra (colunares, escrita barata, sem transação entre linhas) ou "
        "CockroachDB e YugabyteDB (relacionais distribuídos, com SQL e transação) resolvem escala que o TSE não tem. "
        f"A noite inteira cabe em {num(v['linhas_voto_total'] / 1e6, 0)} milhões de linhas e "
        f"{num(v['pico_secoes_por_segundo'], 0)} boletins por segundo no pico, cerca de "
        f"{inteiro(v['pico_linhas_por_segundo'])} linhas por segundo; os maiores clusters da Uber já passavam de um milhão "
        f"de escritas por segundo em 2016, uns {num(1e6 / v['pico_linhas_por_segundo'], 0)} vezes isso. Para este volume, trocar o banco seria trocar o motor de um carro que está parado no "
        "semáforo. A recomendação proporcional é a fila, os totais incrementais e a publicação assíncrona sobre um banco "
        "relacional comum, Oracle inclusive, sem índice pesado na tabela de chegada. Banco distribuído só entra se o "
        "TSE quiser dois centros de dados ativos ao mesmo tempo, por resiliência, e aí pela disponibilidade, não pelo volume.",
        "juizo",
    )


def auditoria(A: dict) -> str:
    return p(
        "O desenho ideal também é o mais auditável. Um log imutável, com cada evento carregando o hash do anterior, deixa "
        "qualquer pessoa conferir que nada foi trocado no caminho e refazer a soma do zero; cada arquivo publicado diria "
        "até qual evento ele vai. É o que este dossiê fez com os arquivos públicos, guardando cada versão com hora de "
        "geração e SHA-256, só que de fora e incompleto. Com o log da noite, a pergunta “o que parou, onde e por quanto "
        "tempo” teria resposta em minutos, e não dependeria de declaração.",
        "juizo",
    )


def recomendacao() -> str:
    return (
        '<aside class="juizo"><b>Recomendação ao TSE (juízo editorial da casa)</b>'
        "<ol>"
        "<li>Gravar cada boletim verificado num log de eventos só de acréscimo, particionado por UF, com hash encadeado.</li>"
        "<li>Somar por consumidores idempotentes e totais incrementais, sem recalcular o país a cada lote.</li>"
        "<li>Publicar por fotografia assíncrona e assinada, com o número do último evento incluído, para a vitrine nunca "
        "segurar a soma.</li>"
        "<li>Ensaiar com o volume real: em 2020 só dois de cinco testes rodaram no equipamento novo, e a nota técnica "
        "admite que a calibragem teria evitado o atraso.</li>"
        "<li>Banco distribuído só por disponibilidade entre centros de dados, não por volume.</li>"
        "</ol></aside>"
    )


def publicar(A: dict) -> str:
    return (
        p(
            "O que o TSE poderia publicar para encerrar a dúvida: o desenho da totalização e da divulgação de 2026 (quais "
            "componentes, em que ordem, sobre que banco); o log de eventos da noite, com carimbo de tempo de cada "
            "recebimento, de cada inclusão na totalização e de cada arquivo gerado, como fez em 2022 nos dados abertos "
            "por seção; e o relatório do incidente, com a causa do fluxo acima do normal e o que foi isolado. Em 2020 a "
            "nota técnica saiu dois dias depois do primeiro turno.",
            "juizo",
        )
        + "<p><strong>O dossiê prova a parada pelos arquivos públicos; a causa é hipótese até o TSE publicar o relatório.</strong></p>"
    )


def bloco(d: Dados) -> str:
    """HTML do bloco novo do capítulo 3; vazio se `arquitetura.json` ainda não existe."""
    A = d.get(ARQ)
    if not A:
        return ""
    checar(d, ARQ, CHAVES)
    h = '<h3 id="arquitetura">Onde um sistema como esse engasga</h3>'
    h += documentos(A) + sem_prova_2026(A) + hipotese_autor()
    h += (
        carimbo(A)
        + desaceleracao(A)
        + carimbo_leitura()
        + volume(A)
        + volume_leitura(A)
    )
    h += _fig("volume_noite", d)
    h += mecanismo(A) + ANALOGIA
    h += '<h3 id="arquitetura-ideal">O desenho que não engasga</h3>'
    h += desenho(A) + uber(A) + banco_distribuido(A)
    h += _fig("arquitetura_totalizacao", d)
    h += auditoria(A) + recomendacao() + publicar(A)
    return h
