"""Auditoria de pesos Palver e inventário estadual, sem simular microdados."""

import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/assets/reponderacao_20260921.json"


def fmt(value):
    return f"{value:.2f}".replace(".", ",")


def audit_html(data, table):
    if not AUDIT.exists():
        return ""
    audit = json.loads(AUDIT.read_text())
    poll = next((p for p in data["pesquisas"] if p["id"] == "palver_2026-09-18"), None)
    if not poll:
        return ""
    url = poll["fonte"]["url"]
    github = audit["palver"]["github"]
    score_rows = []
    for turn, title in [("1t", "1º turno"), ("2t", "2º turno")]:
        result = poll["turnos"][turn]
        values = [result["publicado"]] + [
            result["cenarios"][key]["ajustado"]
            for key in ["pessoas16_efetivo", "pessoas16_habitual"]
        ]
        score_rows.append(
            [title] + [f'{fmt(v["lula"])} × {fmt(v["flavio"])}' for v in values]
        )
    sources = {s["instituto"]: s for s in audit["fontes"]}
    states = [
        [
            s["uf"],
            escape(s["registro"]),
            f'{s["n"]:,}'.replace(",", "."),
            "/".join(reversed(s["divulgacao_pdf"].split("-"))),
            f'<a href="{escape(sources[s["fonte"]]["url"], quote=True)}">Íntegra</a>',
        ]
        for s in audit["estaduais"]
    ]
    return (
        '<section id="palver-pesos" class="chapter"><div class="wrap">'
        '<p class="eyebrow">Palver · auditoria de calibração · 21/09/2026</p>'
        "<h2>O código é aberto. Os pesos individuais ainda não.</h2>"
        "<p>A Palver usa <b>PNADC 2024, visita 5</b>, e pondera por "
        "<b>região × voto no segundo turno de 2022</b>. Nesta divulgação, acrescenta "
        "filiação partidária, com cadastro do TSE de agosto de 2026. Não é a régua PNAD 2025 "
        f'usada aqui. <a href="{url}#page=18">Metodologia, pp. 18–20</a>.</p>'
        "<p>O relatório promete divulgar os microdados <b>depois do segundo turno</b>. "
        "O repositório consultado contém o motor e os alvos; o arquivo com uma linha por entrevistado, "
        "<code>peso</code> e <code>peso_norm</code> não está publicado. Sem essas respostas e pesos, "
        "não é possível recalibrar conjuntamente sexo, idade e região pelo eleitorado TSE "
        "e renda e escolaridade pela PNAD 2025. "
        f'<a href="{url}#page=6">Relatório, p. 6</a>; '
        f'<a href="{github}/README.md">README do código arquivado</a>.</p>'
        "<h3>O teste que os dados públicos permitem</h3>"
        "<p>Trocamos somente a margem de renda e mantemos a ancoragem no placar publicado. "
        "A coluna habitual usa o mesmo conceito de rendimento <code>VD5007</code> adotado "
        "no código da Palver; a efetiva segue a convenção do agregador. "
        "<b>Ordem: Lula × Flávio, em %.</b></p>"
        + table(
            ["Turno", "Publicado", "PNAD 2025 · efetiva", "PNAD 2025 · habitual"],
            score_rows,
        )
        + '<p class="note">Sensibilidades marginais, sem recalibração conjunta e sem intervalo novo. '
        "Os pesos de renda de partida são os <b>alvos declarados</b> de 42,12% / 39,56% / 18,31%, "
        "normalizados para 100%, pois não há diagnóstico público da aderência da onda 3. "
        "A p. 20 declara aderência exata sem aparo; a p. 18 admite tolerância de até 3 pp. "
        "Renda e sexo recompõem os dois candidatos a menos de 0,8 pp dos placares, "
        "controle de leitura que não substitui a base individual. Renda nas pp. 32 e 40.</p>"
        "<h3>A onda anterior mudou de método</h3>"
        "<p>A Palver reapresentou a amostra de 04–07/09 sob o registro BR-06100/2026. "
        "Na versão revisada, o primeiro turno passa a <b>Lula 41 × 40 Flávio</b> "
        "(antes, 40 × 39), e o segundo a <b>44 × 47</b> (antes, 44 × 46). "
        "São mudanças de calibração sobre as mesmas entrevistas. A versão original permanece "
        "arquivada e sai da série ativa; a revisada só entra como placar publicado, pois as "
        "pp. 30 e 37 não trazem o cruzamento de renda revisto. "
        f'<a href="{url}#page=12">Mudança explicada pela Palver, pp. 12–16</a>.</p>'
        '<p class="note">O snapshot do GitHub ainda contém apenas as configurações das ondas 1 e 2 '
        "com método v1 e filiação desativada. O PDF da onda 3 descreve o método v2, mas sua "
        "configuração não aparece nesse snapshot. A promessa de código aberto não prova "
        "que a configuração da última divulgação já esteja disponível.</p>"
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
