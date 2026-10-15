"""Card social do mapa de fiscais em tela cheia (docs/fiscais_mapa.html).

Os números saem de docs/assets/fiscais_mapa/dados.json; sem o arquivo, o card cai num
texto neutro, sem número.
"""

import json


def _int(x):
    return f"{x:,}".replace(",", ".")


def card(root):
    caminho = root / "docs/assets/fiscais_mapa/dados.json"
    stats = [("CEP", "zona ou município: o mapa centra onde você está")]
    if caminho.exists():
        d = json.loads(caminho.read_text(encoding="utf-8"))
        stats = [
            (
                _int(d["resumo"].get("secoes_originais", len(d["linhas"]))),
                "seções nos critérios históricos preservados",
            ),
            (
                f'+{len(d.get("logs", {}).get("criterios", {}))}',
                "diagnósticos operacionais dos logs, em camada própria",
            ),
            ("Brasil e exterior", "filtros por território, cidade, zona e ocorrência"),
        ]
    return {
        "slug": "fiscais_mapa",
        "eyebrow": "Mapa de fiscais · 2º turno, 25 de outubro",
        "title": "Mapa de fiscais.",
        "title_em": "Agora com os logs.",
        "lede": (
            "Consulte tempos, biometria, reinícios e registros técnicos por seção, "
            "com fonte, cobertura e limites. Mapa, lista e exportação em CSV. "
            "<b>Ocorrência operacional não é prova de irregularidade.</b>"
        ),
        "stats": stats,
        "foot": "boletins e logs oficiais (TSE) · critérios históricos preservados · brasil.arvor.co",
        "accent": "amber",
    }
