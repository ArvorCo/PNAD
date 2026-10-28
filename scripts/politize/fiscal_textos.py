"""Textos dos critérios de fiscalização do Politize (gravados em ``fiscal/regras.json``).

Cada critério tem: nome curto, ``porque`` (por que a seção pede fiscal atento),
``conferir`` (o que o fiscal confere na seção, no dia), ``regra`` (o limiar exato) e
``fonte``. Os números de evidência (ex.: troca de urna por modelo) entram por
``str.format`` com os valores medidos no build. Sem travessão; nunca "fraude".
"""

from __future__ import annotations

from typing import Any

from . import fiscal as fz

ROTULOS = {
    "atipico": "Atipicidade estatística não é irregularidade.",
    "prioridade": "A lista é de prioridade de fiscalização, não de acusação.",
    "resolve": "O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.",
}

NIVEIS = {
    "maxima": {
        "nome": "Prioridade máxima",
        "frase": "Os números desta seção somam vários motivos para ter fiscal do começo ao fim, da zerésima ao boletim impresso.",
    },
    "alta": {
        "nome": "Prioridade alta",
        "frase": "Esta seção tem motivos claros para ter fiscal o dia inteiro, e não só na hora da apuração.",
    },
    "reforcada": {
        "nome": "Atenção reforçada",
        "frase": "Esta seção tem ao menos um motivo a mais para ter fiscal atento.",
    },
    "padrao": {
        "nome": "Atenção padrão",
        "frase": "Nenhum sinal a mais nos números. Ainda assim, sem fiscal, ninguém do nosso lado confere a zerésima, a identificação dos eleitores e o boletim impresso.",
    },
}

GRUPOS = {
    "c13": "Capítulo 13 do dossiê da apuração",
    "secao": "Boletim de urna da seção",
    "local": "Local de votação",
    "zona": "Zona eleitoral",
    "territorio": "Território",
}

CAP13 = {
    "nome": "Seção sinalizada no capítulo 13 do dossiê da apuração",
    "porque": "O capítulo 13 cruzou 12 critérios em todas as seções do país e pôs esta entre as 13.045 com ao menos um sinal.",
    "conferir": "Leve o critério e o que conferir: ata da mesa, boletim impresso afixado contra o publicado, identificação dos eleitores.",
    "fonte": "brasil.arvor.co/apuracao_1o_turno_2026.html#fiscais",
}


def criterios(ev: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Textos dos critérios novos e de local, zona e território.

    ``ev``: evidências medidas no build, com as chaves ``troca_2013`` e ``troca_outras``
    (boletim do 1º turno) e as ``ml_*`` da mistura dos dois turnos (``ml_k``, ``ml_grupo``,
    ``ml_universo``, ``ml_features``, ``ml_aptos_min``, ``ml_secoes``, ``ml_pct``,
    ``ml_bn1``, ``ml_bn2``, ``ml_bn1_pais``, ``ml_bn2_pais``, ``ml_aptos``,
    ``ml_aptos_pais``), lidas de ``anomalia_ml.json`` por ``politize-fiscal.py``.
    """
    t: dict[str, dict[str, Any]] = {
        "id_ano": {
            "grupo": "secao",
            "nome": "Muitos eleitores liberados sem a digital",
            "porque": "Quando a digital não confere, o mesário pode liberar o voto pela data de nascimento. É legal e comum, mas é o momento em que a identidade do eleitor fica só na conferência do documento.",
            "conferir": "Acompanhe a identificação: documento oficial com foto conferido contra o caderno, e anote na ata quantos foram liberados assim. O fiscal pode impugnar a identidade do eleitor (Código Eleitoral, art. 132).",
            "regra": f"liberados pelo ano de nascimento iguais ou acima de {fz.br(fz.ANO_NASC_PCT, 0)}% do comparecimento, ou {fz.br(fz.ANO_NASC_PCT_Z, 0)}% com {fz.br(fz.Z_ZONA, 0)} desvios-padrão acima das outras seções da zona; {fz.MIN_VOTANTES} votantes ou mais",
            "fonte": "boletim de urna (qtdEleitoresHabilitadosPorBiografia)",
        },
        "urna_troca": {
            "grupo": "secao",
            "nome": "Urna trocada ou dados recuperados no 1º turno",
            "porque": "A urna desta seção foi substituída por uma de contingência ou de reserva, recebeu mais de uma carga ou teve os votos recuperados. Há explicação técnica comum, mas toda troca precisa de registro.",
            "conferir": "Peça a ata: hora, motivo da troca, número da urna nova e lacres. No 2º turno, chegue antes das 7h para ver a urna ligar e a zerésima sair.",
            "regra": "tipo de urna diferente de seção, mais de uma carga ou boletim que não veio da votação normal na urna",
            "fonte": "boletim de urna (tipo de urna, histórico de cargas, tipo de arquivo)",
        },
        "comparecimento": {
            "grupo": "secao",
            "nome": "Comparecimento muito acima do resto da zona",
            "porque": "Quase todo mundo votou aqui, bem mais que nas seções vizinhas. Pode ser eleitorado fiel ao voto; pode ser caderno a conferir.",
            "conferir": "Confira o caderno de votação (quem assinou), a ata e as liberações sem digital. Abstenção baixa se explica com assinatura, não com estimativa.",
            "regra": f"abstenção de até {fz.br(fz.COMPARECIMENTO_ABST, 0)}%, {fz.COMPARECIMENTO_APTOS} aptos ou mais, {fz.br(fz.Z_ZONA, 0)} desvios-padrão abaixo das outras seções da zona",
            "fonte": "boletim de urna (aptos e comparecimento)",
        },
        "abertura": {
            "grupo": "secao",
            "nome": "Votação começou atrasada",
            "porque": "O primeiro voto só entrou meia hora ou mais depois das 8h de Brasília. Pode ser problema na instalação da mesa ou da urna.",
            "conferir": "Chegue às 7h, acompanhe a instalação e a impressão da zerésima, e registre na ata a hora em que o primeiro eleitor votou.",
            "regra": f"primeiro voto {fz.ABERTURA_MIN} minutos ou mais depois das 8h de Brasília; {fz.ABERTURA_APTOS} aptos ou mais",
            "fonte": "boletim de urna (hora do primeiro voto, convertida para Brasília pelo fuso do município)",
        },
        "id_sem_digital": {
            "grupo": "secao",
            "nome": "Muitos eleitores sem digital cadastrada",
            "porque": "Uma parte grande do eleitorado desta seção não tem biometria e vota identificado só pelo documento.",
            "conferir": "Confira o documento com foto de cada eleitor sem biometria contra o caderno de votação.",
            "regra": f"eleitores sem biometria iguais ou acima de {fz.br(fz.SEM_DIGITAL_PCT, 0)}% do comparecimento; {fz.MIN_VOTANTES} votantes ou mais",
            "fonte": "boletim de urna (qtdEleitoresCompBiometrico e afins)",
        },
        "fila": {
            "grupo": "secao",
            "nome": "Fila no fechamento",
            "porque": "O último voto entrou uma hora ou mais depois das 17h. Fila longa no fim é quando o cansaço da mesa e a pressa aparecem.",
            "conferir": "Às 17h, acompanhe a entrega de senhas a quem está na fila e confira que só vota quem recebeu senha. Peça a cópia do boletim (Lei 9.504, art. 68, § 1º).",
            "regra": f"último voto {fz.FILA_MIN} minutos ou mais depois das 17h de Brasília",
            "fonte": "boletim de urna (hora do último voto)",
        },
        "urna_2013": {
            "grupo": "secao",
            "nome": "Urna do modelo mais antigo",
            "porque": "No 1º turno, {troca_2013}% das seções com urna modelo 2013 tiveram a urna trocada, contra {troca_outras}% nas de modelos mais novos.",
            "conferir": "Chegue cedo: se a urna falhar, acompanhe a troca, o lacre e o registro na ata.",
            "regra": "modelo UE2013, segundo o log da urna do 1º turno (a mesma urna pode não voltar no 2º turno)",
            "fonte": "log e boletim de urna (modelo e tipo de urna)",
        },
        "grande": {
            "grupo": "secao",
            "nome": "Seção grande",
            "porque": f"Com {fz.GRANDE_APTOS} eleitores ou mais, a fila cresce e há mais votos em jogo numa só urna.",
            "conferir": "Dois fiscais em revezamento ajudam: a lei permite até dois por partido em cada seção, um de cada vez (Lei 9.504, art. 65, § 4º).",
            "regra": f"{fz.GRANDE_APTOS} aptos ou mais",
            "fonte": "boletim de urna (aptos)",
        },
        "transito": {
            "grupo": "secao",
            "nome": "Eleitores em trânsito",
            "porque": "A seção recebe eleitores de outros municípios, que votam por uma lista à parte.",
            "conferir": "Confira que o eleitor em trânsito está na lista da seção e assina nela.",
            "regra": f"{fz.TRANSITO_APTOS} ou mais aptos em trânsito",
            "fonte": "boletim de urna (aptos em trânsito)",
        },
        "disputa": {
            "grupo": "secao",
            "nome": "Disputa apertada",
            "porque": "Flávio e Lula ficaram a poucos pontos um do outro aqui. Onde a diferença é pequena, cada voto anulado, cada eleitor barrado e cada erro de boletim pesa.",
            "conferir": "Fique até o fim e confira o boletim impresso contra o publicado no site do TSE.",
            "regra": f"diferença de até {fz.br(fz.DISPUTA_PP, 0)} pontos dos válidos na seção ({fz.DISPUTA_VALIDOS_SECAO} válidos ou mais) ou no local ({fz.DISPUTA_VALIDOS_LOCAL} válidos ou mais)",
            "fonte": "boletim de urna (votos de presidente)",
        },
        "assistido": {
            "grupo": "secao",
            "nome": "Eleitorado que mais pede ajuda",
            "porque": "Muitos idosos ou muita gente com pouca escolaridade: é onde mais aparece pedido de ajuda na cabine e onde a fila preferencial pesa.",
            "conferir": "Acompanhante só entra com eleitor com deficiência, e o fato vai para a ata. Ninguém de partido ajuda na cabine.",
            "regra": f"{fz.br(fz.IDOSOS_PCT, 0)}% ou mais com 60 anos ou mais, ou {fz.br(fz.FUND_INC_PCT, 0)}% ou mais sem o fundamental completo (perfil da seção do TSE)",
            "fonte": "perfil do eleitorado por seção, TSE 2026",
        },
        "ml_atipico": {
            "grupo": "secao",
            "nome": "Grupo atípico nos dois turnos",
            "porque": "Uma mistura gaussiana de {ml_k} grupos, ajustada sobre os votos das {ml_universo} seções do país nos dois turnos, pôs esta seção no grupo que o modelo menos explica ({ml_secoes} seções, {ml_pct}% do total). Na média das seções desse grupo, brancos e nulos somam {ml_bn1}% do eleitorado no 1º turno e {ml_bn2}% no 2º, contra {ml_bn1_pais}% e {ml_bn2_pais}% na média do país, e as seções são menores ({ml_aptos} aptos em média, contra {ml_aptos_pais}). Atipicidade estatística não é irregularidade: o grupo pede explicação, não prova nada.",
            "conferir": "Peça a ata e a cópia do boletim impresso e confira brancos, nulos e comparecimento contra o publicado no site do TSE. Em seção pequena, um eleitor move mais de um ponto: compare com as outras seções do prédio antes de concluir. Método e mapa no capítulo Grupos do dossiê da apuração do 2º turno (brasil.arvor.co/apuracao_2T_2026.html#anomalia).",
            "regra": "seção no grupo mais atípico (grupo {ml_grupo} de {ml_k}) da mistura gaussiana sobre {ml_features} frações do eleitorado nos dois turnos, com {ml_aptos_min} aptos ou mais em cada e sem o exterior; seção sem linha no arquivo da mistura não recebe o critério",
            "fonte": "brasil.arvor.co/apuracao_2T_2026.html#anomalia",
        },
        "local_c13_alta": {
            "grupo": "local",
            "nome": "Local de votação sinalizado no capítulo 13",
            "porque": "Outras seções deste prédio foram sinalizadas pelo capítulo 13 do dossiê da apuração, em nível alto.",
            "conferir": "Um fiscal pode cobrir várias seções do mesmo prédio (Lei 9.504, art. 65, § 1º), mas aqui vale um por seção sinalizada.",
            "regra": "local com seção de nível alto no capítulo 13",
            "fonte": "fiscais.json, por_local",
        },
        "local_c13_media": {
            "grupo": "local",
            "nome": "Local de votação sinalizado no capítulo 13",
            "porque": "Outras seções deste prédio foram sinalizadas pelo capítulo 13 do dossiê da apuração, em nível médio.",
            "conferir": "Um fiscal pode cobrir várias seções do mesmo prédio (Lei 9.504, art. 65, § 1º); comece pelas sinalizadas.",
            "regra": "local com seção de nível médio no capítulo 13",
            "fonte": "fiscais.json, por_local",
        },
        "local_c13_baixa": {
            "grupo": "local",
            "nome": "Local de votação sinalizado no capítulo 13",
            "porque": "Outras seções deste prédio entraram na lista do capítulo 13 do dossiê da apuração, em nível baixo.",
            "conferir": "Passe pelas seções sinalizadas na hora da apuração e confira o boletim impresso.",
            "regra": "local com seção de nível baixo no capítulo 13",
            "fonte": "fiscais.json, por_local",
        },
        "local_grande": {
            "grupo": "local",
            "nome": "Prédio com muitas seções",
            "porque": f"Com {fz.LOCAL_GRANDE_SECOES} seções ou mais no mesmo endereço, o movimento é grande e um fiscal sozinho não vê tudo.",
            "conferir": "Combine com outros fiscais: um por corredor no mínimo, e um delegado do partido circulando.",
            "regra": f"{fz.LOCAL_GRANDE_SECOES} seções ou mais no local de votação",
            "fonte": "cadastro de locais do TSE",
        },
        "zona_atipica": {
            "grupo": "zona",
            "nome": "Zona entre as 50 mais atípicas do país",
            "porque": "A zona eleitoral desta seção ficou entre as 50 mais atípicas no capítulo 12 do dossiê, que compara voto, comparecimento e totalização com 2022 e com a UF.",
            "conferir": "Leve a explicação da zona e confira ata e boletim impresso de cada seção que puder.",
            "regra": "zona no topo 50 de anomalias.json",
            "fonte": "brasil.arvor.co/apuracao_1o_turno_2026.html",
        },
        "zona_congelada": {
            "grupo": "zona",
            "nome": "Zona com arquivo parado na noite do 1º turno",
            "porque": "O arquivo de resultados desta zona ficou incompleto por 6 horas ou mais depois do fim da votação.",
            "conferir": "Peça a cópia do boletim ao presidente da mesa e fotografe o boletim afixado na porta.",
            "regra": "zona em zonas_congeladas do capítulo 13",
            "fonte": "fiscais.json, zonas_congeladas",
        },
        "territorio_alto": {
            "grupo": "territorio",
            "nome": "Risco do território: alto",
            "porque": "O entorno soma vários fatores de risco em bases públicas. Território com risco pede fiscal que conheça o lugar e não vá sozinho.",
            "conferir": "Vá acompanhado, combine horário de chegada e saída e acione o juiz eleitoral e a PM diante de qualquer coação. Validar com a PM e o TRE local.",
            "regra": f"{fz.TERRITORIO_ALTO} pontos ou mais na regra de território do capítulo 13",
            "fonte": "IBGE, FUNAI, Ipea, FBSP e matérias com fonte (fiscais_risco_*.csv)",
        },
        "territorio_medio": {
            "grupo": "territorio",
            "nome": "Risco do território: médio",
            "porque": "O entorno tem fatores de risco em bases públicas.",
            "conferir": "Combine a ida com outros fiscais e anote o contato do cartório eleitoral. Validar com a PM e o TRE local.",
            "regra": f"{fz.TERRITORIO_MEDIO} ou {fz.TERRITORIO_ALTO - 1} pontos na regra de território do capítulo 13",
            "fonte": "IBGE, FUNAI, Ipea, FBSP e matérias com fonte (fiscais_risco_*.csv)",
        },
    }
    for v in t.values():
        v["porque"] = v["porque"].format(**ev)
        v["regra"] = v["regra"].format(**ev)
    for k, v in t.items():
        v["peso"] = fz.PESOS[k]
    return t


SEMPRE = [
    "Antes das 8h: confere a zerésima, o papel que a urna imprime mostrando zero voto para todo mundo.",
    "Durante o dia: acompanha a identificação dos eleitores e pode impugnar quem não for quem diz ser (Código Eleitoral, art. 132).",
    "Às 17h: confere a entrega de senhas a quem está na fila.",
    "No fim: pede a cópia do boletim de urna, que o presidente da mesa entrega até uma hora depois (Lei 9.504, art. 68, § 1º), e fotografa o boletim afixado.",
]

CTA = {
    "url": "https://fiscaisdopl.com.br",
    "rotulo": "fiscaisdopl.com.br",
    "titulo": "Seja fiscal no 2º turno",
    "texto": "O cadastro do Partido Liberal pede nome, WhatsApp, estado e município. O próprio site informa prazo final em 24 de outubro, véspera da votação.",
    "botao": "Quero ser fiscal",
}

LEGAL = [
    "Lei 9.504/1997, art. 65: fiscal maior de 18 anos, fora da mesa; até dois por partido em cada seção, um de cada vez; um fiscal pode cobrir várias seções do mesmo local.",
    "Código Eleitoral, art. 132: fiscais podem fiscalizar a votação, protestar e impugnar, inclusive sobre a identidade do eleitor.",
    "Lei 9.504/1997, art. 68, § 1º: o presidente da mesa entrega cópia do boletim de urna ao partido que pedir, até uma hora depois.",
    "Fiscal não faz propaganda: boca de urna e arregimentação de eleitor no dia são crime (Lei 9.504/1997, art. 39, § 5º).",
]
