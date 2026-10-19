"""Cards do laudo de mudanças de local de votação; números lidos do JSON do motor."""

import json


def _n(x):
    return f"{round(x):,}".replace(",", ".")


def _d(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def _dados(root):
    d = json.loads(
        (root / "analysis/mudancas_secoes_2t/mudancas.json").read_text(encoding="utf-8")
    )
    mr = d["resumo"]["mudanca_real"]
    painel = next(
        n for n in d["confronto_publico"]["numeros_publicos"] if n["id"] == "painel_tse"
    )
    dd = d["efeito_1t"]["dif_em_dif"]["diferenca"]["mesmo_municipio"]["diferenca_pp"]
    return d, mr, painel, dd


def card(root):
    _, mr, painel, dd = _dados(root)
    return {
        "slug": "mudancas_secoes_abstencoes",
        "eyebrow": "Laudo · locais de votação · 2º turno de 2026",
        "title": f"O painel do TSE diz {_n(painel['secoes']['publico'])}.",
        "title_em": f"Nossa conta: {_n(mr['secoes'])} seções.",
        "lede": (
            f"<b>{_n(mr['por_categoria']['A']['secoes'])} voltam ao prédio original.</b> "
            "Distância, motivos publicados, clima e abstenção do 1º turno nas seções que mudam de local."
        ),
        "stats": [
            (
                _n(mr["secoes"]),
                f"seções com mudança real, {_n(mr['eleitores'])} eleitores",
            ),
            (f"{_n(mr['distancia_mediana_m'])} m", "distância mediana, em linha reta"),
            (
                f"+{_d(dd['valor'])} pp",
                f"abstenção no 1º turno, IC 95% de {_d(dd['ic95'][0])} a {_d(dd['ic95'][1])}",
            ),
        ],
        "foot": "cadastro do TSE de 18/10 · efeito medido, não causal identificado",
        "accent": "amber",
    }


def card_thread(root):
    d, mr, _, dd = _dados(root)
    cp = {n["id"]: n for n in d["confronto_publico"]["numeros_publicos"]}
    return {
        "slug": "mudancas_secoes_thread",
        "eyebrow": "Thread · mudanças de local de votação",
        "title": "Quatro números.",
        "title_em": "Um só cadastro.",
        "lede": (
            f"{_n(cp['tse_agencia_brasil']['secoes']['publico'])}, "
            f"{_n(cp['coligacao_peticao']['secoes']['publico'])}, "
            f"{_n(cp['forum_exportacao']['secoes']['publico'])} e "
            f"{_n(cp['painel_tse']['secoes']['publico'])} seções. "
            "<b>O que o cadastro mostra, o que o clima explica e o que a abstenção do 1º turno mede.</b>"
        ),
        "stats": [
            (_n(mr["secoes"]), "seções com mudança real de prédio"),
            (_n(mr["por_categoria"]["A"]["secoes"]), "voltam ao prédio original"),
            (f"+{_d(dd['valor'])} pp", "abstenção medida no 1º turno"),
        ],
        "foot": "fato medido, inferência e juízo separados · fonte de cada número no laudo",
        "accent": "blue",
        "thread": True,
    }
