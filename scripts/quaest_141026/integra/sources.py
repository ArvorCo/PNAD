"""Estado documental após o recebimento da íntegra, sem apagar a consulta anterior."""

from html import escape as esc

from dossies_2t_2026.view import callout, note, section, table


def render(data):
    return section(
        13,
        "fontes",
        "Mais evidência.<br><em>Limites que permanecem.</em>",
        "A íntegra foi recebida em 15/10. As consultas anteriores continuam arquivadas com seu contexto e horário.",
        table(
            ["Documento", "O que permite conferir"],
            [
                [
                    '<a href="fontes/quaest_14102026.pdf">Relatório Quaest · 152 páginas</a>',
                    "Método, perguntas publicadas, cruzamentos, perfil e séries. Arquivo fornecido pelo usuário, sem regravar o original.",
                ],
                [
                    '<a href="fontes/quaest_14102026_registro.txt">Transcrição PesqEle BR-08729/2026</a>',
                    "Campo, universo, cotas previstas e plano. A mensagem de relatório indisponível foi observada na madrugada de 15/10; não descreve o estado atual do portal.",
                ],
                [
                    "Questionário QUEST_NACIONAL_2T_R01_V14",
                    "Visualizado anteriormente com 27 páginas; original ainda não arquivado. As formulações nas lâminas não substituem a sequência completa, os filtros e o roteamento do questionário.",
                ],
                [
                    '<a href="assets/quaest_14102026_painel/index.json">Painel G1 / cinco perguntas</a>',
                    "130 recortes e margens, com códigos, fontes e hashes. No G1, Norte e Centro-Oeste são separados; no PDF, agregados.",
                ],
                [
                    '<a href="assets/quaest_14102026_integra/auditoria.json">Auditoria da íntegra</a>',
                    "Memória versus urna, contribuição do grupo misto, cenários de conversão e recortes por interesse. São contas Arvor, não estimativas divulgadas pelo instituto.",
                ],
                [
                    '<a href="assets/quaest_14102026_data.json">Auditoria do dossiê</a>',
                    "Série comparável, sensibilidade PNAD, recomposição, resíduos e referência AAS.",
                ],
                [
                    '<a href="assets/quaest_14102026_sources.json">Manifesto de integridade</a>',
                    "Hashes da cópia recebida, transcrições, fichas e evidências. A integridade identifica a versão examinada; não substitui autenticação externa.",
                ],
                [
                    "Anexo territorial",
                    "Não disponível na reconsulta de 15/10 às 01h12 BRT, dentro do prazo então exibido. Nenhum novo anexo foi recebido com este PDF. Não se infere irregularidade.",
                ],
            ],
        )
        + "<ul>"
        + "".join("<li>" + esc(item) + "</li>" for item in data["pendencias"])
        + "</ul>"
        + callout(
            "O juízo que a documentação sustenta",
            "O relatório confirma a intenção e publica o perfil de renda. Não separa abstencionistas na transferência nem fornece um modelo de eleitor provável. A matriz parcial, as mudanças de pergunta e a descrição genérica da ponderação limitam a interpretação. Nenhum desses limites, sozinho, demonstra fraude ou favorecimento deliberado.",
        )
        + note(
            'As centrais usam hipóteses próprias de presença e renda, expostas no <a href="reponderacao_pnad.html">simulador</a>. A chegada do PDF melhora a proveniência; o perfil e os cruzamentos confirmados não mudam a conta PNAD desta onda. Cenários do grupo misto e de interesse não entram automaticamente nas centrais.'
        ),
    )
