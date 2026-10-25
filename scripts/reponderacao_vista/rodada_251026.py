"""Divulgação final do PoderData no dia da votação."""


def section(latest):
    if latest.get("PoderData", {}).get("id") != "poderdata_2026-10-24":
        return ""
    return (
        '<aside class="callout" id="poderdata-2510"><h3>25/10: PoderData final</h3>'
        "<p><b>49 × 47 nos totais; 51 × 49 nos válidos oficiais.</b> "
        "Flávio × Lula; brancos/nulos 3%, indecisos 1%. Campo 23–24/10, "
        "4.000 entrevistas em 914 municípios, BR-02828/2026. A onda substitui "
        "a anterior nas duas centrais e nos gráficos do instituto.</p>"
        "<p>O relatório identifica expressamente o perfil de renda 46/33/21 como "
        "<b>ponderado</b>. Os votos Flávio/Lula por faixa são 42/54, 56/40 e 52/44. "
        "A reponderação usa esses dados atuais. Certeza declarada de votar de 96% "
        "entre eleitores de Flávio e 94% entre os de Lula aparece somente na série "
        "documental; as regras das centrais permanecem iguais. Quaest conserva "
        "o 51 × 49 do eleitor provável, sem nova seleção de presença.</p>"
        '<p class="note"><a href="fontes/poderdata_25102026.pdf">Íntegra, 27 páginas</a> · '
        '<a href="assets/reponderacao_poderdata_20261025.json">Fontes e auditoria</a>.'
        "</p></aside>"
    )
