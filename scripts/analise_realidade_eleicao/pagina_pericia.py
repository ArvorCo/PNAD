"""Escopo da investigação e estado das evidências, sem selo de certificação."""

from html import escape


def roteiro():
    etapas = [
        (
            "01",
            "Registro → publicação",
            "Parcial",
            "parcial",
            "Confrontar BU físico ou QR coletado na seção, BU digital e totalização, por candidato. Preservar o original, origem e horário da coleta.",
            "BUs digitais e totais municipais conferidos; a coleta paralela é voluntária. Falta uma amostra independente com seleção probabilística e verificação dos originais.",
        ),
        (
            "02",
            "Pessoas → votos registrados",
            "Parcial",
            "parcial",
            "Confrontar aptos, comparecimento, habilitações, votos, caderno de votação e ata. Investigar presença impossível e registros incompatíveis.",
            "Limites aritméticos conferidos. Seis diferenças log × BU aguardam pacote completo e ata. Cadernos e identidade dos votantes não foram auditados.",
        ),
        (
            "03",
            "Equipamento → arquivo",
            "Parcial",
            "parcial",
            "Conferir assinaturas, versões, cargas, correspondência da urna, trocas, zerésima e cadeia de custódia; reproduzir o problema em ambiente autorizado.",
            "Trocas e sinais de operação foram relacionados ao voto. Autenticidade criptográfica, software executado e integridade física não foram certificados por esta análise.",
        ),
        (
            "04",
            "Primeiro → segundo turno",
            "Triagem feita",
            "triagem",
            "Parear a mesma seção, tratar agregações e mudanças cadastrais; comparar votos absolutos, presença, brancos/nulos e os dois candidatos contra locais semelhantes.",
            "Há comparações entre turnos e contra vizinhas no dossiê. Os resíduos municipais fora da amostra organizam os casos, sem identificar transferências individuais.",
        ),
        (
            "05",
            "Horário → composição dos lotes",
            "Análise no dossiê",
            "triagem",
            "Separar horário de votação, fechamento e recebimento. Reconstituir quais seções compõem cada salto; investigar alterações na mesma seção e retotalizações.",
            "A curva da noite e a composição dos lotes estão no dossiê. Uma virada no agregado exige decomposição territorial; a hora de transmissão não é a hora do voto.",
        ),
        (
            "06",
            "Liberdade → escolha do eleitor",
            "Pendente",
            "pendente",
            "Investigar coação, compra de voto e impedimento de votar com denúncias verificáveis, ocorrências, atas e evidência territorial datada.",
            "Homicídios e presença municipal não medem coação. A camada territorial GENI/Fogo Cruzado de 2024 foi cruzada com locais de votação de 2026. A investigação de denúncias, atas e ameaças documentadas permanece pendente.",
        ),
    ]
    cards = "".join(
        f'<article class="pericia-item"><div class="pericia-top"><span>{numero}</span>'
        f'<b class="estado {classe}">{escape(estado)}</b></div>'
        f"<h4>{escape(titulo)}</h4><p>{escape(teste)}</p>"
        f'<p class="pericia-status"><strong>Neste relatório:</strong> {escape(status)}</p></article>'
        for numero, titulo, estado, classe, teste, status in etapas
    )
    return f"""<h3>Se a eleição fosse uma perícia: seis caminhos de investigação</h3>
    <p>Uma hipótese de fraude precisa especificar o mecanismo, os registros que seriam alterados e a evidência capaz de confirmá-la ou refutá-la. A mesma exigência vale para qualquer candidato. Estes estados descrevem a cobertura do trabalho, não uma nota de integridade da eleição.</p>
    <div class="pericia-grid">{cards}</div>
    <details><summary>Como selecionar casos sem fabricar suspeitas</summary>
    <p>Prioridade documental: divergências entre fontes independentes, impossibilidades aritméticas e ocorrências com arquivos originais. Prioridade estatística: mudanças que persistem ao comparar a mesma seção, vizinhas e histórico, sobretudo quando coincidem com uma ocorrência verificável. A fila deve mostrar cobertura, votos envolvidos, hipóteses alternativas e documento faltante.</p>
    <p>Resultados extremos, zeros, números repetidos e dígitos incomuns podem servir de pistas, mas exigem um modelo nulo compatível com tamanho e composição das seções. Testar milhares de lugares produz extremos mesmo sem fraude. Hipóteses descobertas na exploração precisam de replicação em dados reservados e tratamento de múltiplas comparações antes de qualquer alegação de significância.</p>
    <p>Renda e voto são dados agregados: não identificam como votou cada pessoa. Ganhar mais votos que o total da terceira via não é impossibilidade: comparecimento, votos brancos/nulos e escolhas entre os finalistas podem mudar. Mesmo com aptos idênticos, os presentes podem ser diferentes.</p>
    <p>Uma irregularidade demonstrada exige dimensionar seu alcance. Em uma disputa entre dois candidatos, transferir um voto de um para o outro altera a margem em dois; adicionar ou retirar um voto altera a margem em um. Só entram nessa conta alterações comprovadas, sem somar resíduos de modelos, sinais sobrepostos ou extrapolar uma amostra voluntária.</p>
    <p>Concordância entre RDV, BU e totalização pode testar a passagem entre esses registros, mas todos podem compartilhar a mesma origem. Ela não demonstra, sozinha, que o registro inicial corresponde à escolha do eleitor. Uma assinatura válida identifica a origem e a integridade do arquivo assinado; não prova a correção de cada voto. A fiscalização de software, as verificações de autenticidade e os testes de integridade precisam ser avaliados pelos seus próprios registros e pela cadeia de custódia.</p>
    <p>As <a href="https://www.justicaeleitoral.jus.br/urna-eletronica/oportunidades-de-auditoria-e-fiscalizacao.html">etapas oficiais de fiscalização</a> indicam os documentos e verificações disponíveis. Os <a href="https://www.stat.berkeley.edu/~stark/Java/Html/auditTools.htm">métodos de auditoria com limite de risco</a> dependem de uma trilha íntegra e adequada para confrontar o resultado. Não chamamos a comparação entre arquivos digitais de auditoria com limite de risco nem atribuímos a ela uma probabilidade de eleição correta.</p>
    </details>"""
