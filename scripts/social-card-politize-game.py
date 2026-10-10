"""Card social do jogo Politize: o jogo da conversa.

Os números saem do roteiro validado (personagens, NPCs e cenários); sem o roteiro, o
card cai num texto neutro, sem número.
"""

from politize_game import roteiro


def card(root):
    try:
        payload = roteiro.montar(root / "analysis/politize_game/roteiro",
                                 root / "docs/assets/politize")  # fmt: skip
    except (OSError, roteiro.RoteiroInvalido):
        payload = None
    stats = [("8", "conversas até o dia 24")]
    if payload:
        stats = [
            (str(len(payload["personagens"])), "personagens para você escolher"),
            (str(len(payload["npcs"])), "perfis de eleitor para convencer"),
            (str(len(payload["cenarios"])), "cenários, da padaria ao grupo da família"),
        ]
    return {
        "slug": "politize_game",
        "eyebrow": "Politize: o jogo da conversa · 2º turno de 2026",
        "title": "Treine a conversa",
        "title_em": "antes de ter a conversa.",
        "lede": (
            "Escolha um personagem, encontre quem votou em outro nome, anulou ou "
            "faltou, e escolha como puxar assunto, escutar e responder. Acerto vira "
            "voto; erro previsto empurra para o outro lado. "
            "<b>Toda lição vem do Politize sua vizinhança.</b>"
        ),
        "stats": stats,
        "foot": "ficção com perfis, não pessoas · o voto é secreto · converse antes do dia 25",
        "accent": "amber",
    }
