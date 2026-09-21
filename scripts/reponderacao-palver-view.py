"""Auditoria de pesos Palver e inventário estadual, sem simular microdados."""

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/assets/reponderacao_20260921.json"
HISTORY = ROOT / "docs/assets/palver_explorer_historico.json"


def history_polls():
    return json.loads(HISTORY.read_text())["pesquisas"]


def fmt(value):
    return f"{value:.2f}".replace(".", ",")


def audit_html(data, table):
    if not AUDIT.exists():
        return ""
    audit = json.loads(AUDIT.read_text())
    poll = next((p for p in data["pesquisas"] if p["id"] == "palver_2026-09-18"), None)
    if not poll:
        return ""
    url = "https://www.palver.com/api/surveys/voting-intention-2026-september-w3/report"
    github = audit["palver"]["github"]
    score_rows = []
    for wave in history_polls():
        cells = [
            f'<a href="{escape(wave["fonte"]["url"], quote=True)}">{escape(wave["rotulo_historico"])}</a>'
        ]
        for turn in ["1t", "2t"]:
            result = wave["turnos"][turn]
            for values in [
                result["publicado"],
                result["cenarios"]["pessoas16_efetivo"]["ajustado"],
            ]:
                cells.append(f"{fmt(values['lula'])} × {fmt(values['flavio'])}")
        cells.append(
            "Arquivo, fora das médias"
            if wave["substituida"]
            else "Só 2º turno (1º com Marçal)"
            if wave["primeiro_turno_com_marcal"]
            else "1º e 2º turnos"
        )
        score_rows.append(cells)
    sources = {s["instituto"]: s for s in audit["fontes"]}
    states = [
        [
            s["uf"],
            escape(s["registro"]),
            f"{s['n']:,}".replace(",", "."),
            "/".join(reversed(s["divulgacao_pdf"].split("-"))),
            f'<a href="{escape(sources[s["fonte"]]["url"], quote=True)}">Íntegra</a>',
        ]
        for s in audit["estaduais"]
    ]
    return (
        '<section id="palver-pesos" class="chapter"><div class="wrap">'
        '<p class="eyebrow">Palver · auditoria de calibração · 21/09/2026</p>'
        "<h2>Três ondas. Quatro versões. Todas visíveis.</h2>"
        '<p>O <a href="https://www.palver.com.br/survey/explore">Explorer da Palver</a> '
        "disponibiliza percentuais sem arredondamento, contagens por célula e tamanho efetivo. "
        "Integramos todas as ondas: agosto, setembro original, setembro revisada e a onda 3. "
        "A segunda onda é a mesma amostra em duas calibrações, portanto só a revisada entra nas médias. "
        "Os primeiros turnos de 07/09 incluem Marçal: aparecem no histórico, mas ficam fora da média do 1º turno.</p>"
        "<p>Os placares de partida são agora os <b>valores exatos do Explorer</b>. "
        "Isso evita ancorar tabelas decimais em totais já arredondados. Todos os cenários abaixo "
        "trocam somente a distribuição de renda pela PNAD 2025. <b>Ordem: Lula × Flávio, em %.</b></p>"
        + table(
            [
                "Onda e fonte",
                "1º publicado",
                "1º reponderado",
                "2º publicado",
                "2º reponderado",
                "Uso nas médias",
            ],
            score_rows,
        )
        + '<p class="note">Três ondas independentes, quatro versões documentais. Pontos do histórico '
        "não são conectados: a mudança entre v1 e v2 é de calibração, sem novo campo. "
        "Sensibilidade de renda, sem recalibração conjunta e sem novo intervalo de confiança.</p>"
        "<h3>A distribuição de renda foi conferida</h3>"
        "<p>Na onda 3, as bases brutas são <b>1.321 / 2.203 / 1.476</b>. Elas não são os pesos: "
        "o perfil ponderado recuperado das tabelas é <b>42,1229% / 39,5631% / 18,3140%</b>, "
        "coerente com os alvos declarados. O sistema linear tem posto completo, recompõe "
        "43 perguntas de base 5.000 e recupera o n efetivo de <b>1.231,71</b>. "
        "Agora verificamos a aderência; antes, o cálculo dependia da hipótese de aderência aos alvos.</p>"
        "<p>A Palver declara <b>PNADC 2024, visita 5</b>, ponderação por "
        "<b>região × voto no segundo turno de 2022</b> e, na versão revisada, filiação partidária. "
        "Os cruzamentos públicos não expõem os pesos individuais nem a tabela conjunta necessária "
        "para recalibrar simultaneamente TSE + PNAD 2025. "
        f'<a href="{url}#page=18">Metodologia, pp. 18–20</a>.</p>'
        '<p><a href="assets/palver_explorer_historico.json">Histórico completo calculado (JSON)</a> · '
        '<a href="assets/palver_explorer_auditoria.json">Auditoria dos cruzamentos (JSON)</a> · '
        '<a href="https://github.com/ArvorCo/PNAD/tree/main/analysis/reponderacao/palver_explorer_20260921">'
        "186 tabelas e reprodução</a>.</p>"
        "<h3>Divergências documentais preservadas</h3>"
        "<p>O catálogo do Explorer encerra a onda 3 em 20/09, mas o PDF informa 18/09; "
        "mantemos 18/09 na série. Na onda 2 revisada, Lula aparece com 40,440% no primeiro "
        "turno do Explorer e 41% no PDF p. 30. O arredondamento convencional isolado não "
        "explica essa diferença. Os valores do painel e do PDF permanecem separados nos arquivos.</p>"
        "<details><summary>Como o código trata o voto de 2022 e os pesos extremos</summary>"
        "<p>Na versão pública consultada, o alvo usa Lula, Jair Bolsonaro e branco/nulo "
        "por região, exclui o exterior e considera os votos depositados. Os totais regionais "
        "são reescalados para a população da PNAD. Portanto, usar TSE para voto passado "
        "não equivale a usar o perfil demográfico do eleitorado atual do TSE.</p>"
        "<p>O questionário do código v1 reúne quem não votou e quem não informou "
        "em branco/nulo, enquanto o alvo de branco/nulo não contém abstenções. "
        "É uma diferença de universo que merece teste quando a base abrir; não é possível "
        "medir seu efeito no voto atual apenas com as marginais. "
        f'<a href="{github}/ondas/2026-09-09/questionario.yaml">Recodificação</a> e '
        f'<a href="{github}/scripts/gerar-margens-tse.R">construção do alvo</a>.</p>'
        "<p>O questionário registrado da onda 3 já separa elegibilidade, comparecimento e "
        "escolha em 2022 nas perguntas 39–41. Isso impede atribuir automaticamente a "
        "recodificação v1 à onda atual; falta o código v2 para conferir seu tratamento. "
        '<a href="fontes/reponderacao_metodologias/palver_2026-09-18/questionario.pdf#page=11">'
        "Questionário do TSE, pp. 11–12</a>.</p>"
        "<p>Na onda 3, 5.000 respostas produzem <b>n efetivo de Kish de 1.232</b>. "
        "O efeito dos pesos é 4,06, o peso máximo 21,73 e não há aparo. "
        "Esses diagnósticos medem a dispersão dos pesos; não eliminam o viés de recrutamento "
        "de uma amostra não probabilística. Relatório, p. 20.</p></details>"
        "<h3>Real Time: quatro íntegras estaduais arquivadas</h3>"
        "<p>As amostras abaixo pertencem a estados e não entram nas médias nacionais. "
        "O prefixo BR do registro não transforma uma pesquisa estadual para presidente "
        "em uma pesquisa nacional.</p>"
        + table(
            ["UF", "Registro no PDF", "Entrevistas", "Divulgação no PDF", "Fonte"],
            states,
        )
        + '<p class="note">O Poder360 publicou a matéria do Paraná em 21/09, mas o PDF indica '
        "divulgação em 16/09 e campo de 11 a 15/09. Preservamos a data do documento. "
        "Para a Palver, o PDF informa campo até 18/09 nas pp. 16 e 22, apesar de notícia "
        "mencionar 20/09. A Nexus nacional declara PNAD 2025 visita 1 e TSE junho/2026 "
        "na p. 4; nosso ajuste testa diferenças de régua, não uma atualização do ano de sua PNAD.</p>"
        '<p><a href="assets/reponderacao_20260921.json">Baixar auditoria: fontes, SHA-256, '
        "páginas e controles de recomposição</a>.</p></div></section>"
    )
