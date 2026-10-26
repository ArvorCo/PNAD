"""Linhas de transferência publicadas pelos institutos e a prior do ajuste (IPF).

Toda linha abaixo foi lida na página indicada do PDF arquivado (hash ao lado) e
conferida na imagem renderizada quando o texto nativo não separa as colunas. É
voto lembrado do 1º turno cruzado com a intenção de 2º turno na mesma entrevista:
medição de pesquisa, não percurso de eleitor, e sem bases publicadas por grupo.

Colunas: ``F`` Flávio, ``L`` Lula, ``BN`` branco/nulo/nenhum (na Quaest inclui
"não vai votar"), ``NS`` não sabe, indeciso ou não respondeu. A prior reparte
``NS`` na proporção de F, L e BN da própria linha; o voto que falta (abstenção no
2º turno) entra por outra hipótese (rotatividade, ``prior_linha``).
"""

from __future__ import annotations

from typing import Any

ORIGENS = (
    "lula",
    "flavio",
    "cury",
    "renan",
    "caiado",
    "zema",
    "outros",
    "brancos",
    "nulos",
    "abstencao",
)
DESTINOS = ("lula", "flavio", "brancos", "nulos", "abstencao")
TERCEIRA = ("cury", "renan", "caiado", "zema", "outros")
VOTO_1T = ORIGENS[:-1]
PISO = 0.002
"""Nenhum zero estrutural: todo eleitor pode fazer qualquer caminho. Zero de
pesquisa com base pequena vira piso de 0,2% da linha antes do ajuste."""

FONTES: dict[str, dict[str, Any]] = {
    "nexus_24": {
        "instituto": "Nexus/BTG",
        "registro": "BR-08234/2026",
        "campo": "23 a 24/10/2026",
        "n": 2000,
        "arquivo": "data/originals/nexus_102026_24/relatorio.pdf",
        "sha256": "be0f443c6782cfae598b6e40893402ce7e77f0bc026685c6e9759f4fc8cff92f",
        "paginas": "22 e 23 (cruzamento por candidato), 15 (comparecimento no 1º turno)",
    },
    "nexus_19": {
        "instituto": "Nexus/BTG",
        "registro": "BR-04499/2026",
        "campo": "16 a 18/10/2026",
        "n": 2002,
        "arquivo": "data/originals/nexus_102026_19/relatorio.pdf",
        "sha256": "f6ee08157b9906a8abd4fca2a7a418b329e8895043019bc871b81f12b1eabb45",
        "paginas": "27 e 28",
    },
    "nexus_13": {
        "instituto": "Nexus/BTG",
        "registro": "BR-07997/2026",
        "campo": "10 a 12/10/2026",
        "n": 2002,
        "arquivo": "data/originals/nexus_102026_13/relatorio.pdf",
        "sha256": "122e3f2052c72c3da04f6bd556cf592f2c341cdda90b462632a6a63dbda1c6a7",
        "paginas": "25 e 26",
    },
    "quaest_21": {
        "instituto": "Quaest",
        "registro": "BR-08535/2026",
        "campo": "17 a 20/10/2026",
        "n": 2154,
        "arquivo": "docs/fontes/quaest_21102026.pdf",
        "sha256": "70fe5c5bfcb8b2ccfb8e558b143a00d459328cfbde59ce95f4270dfaf50a40dd",
        "paginas": "19 (grupos) e 20 (por candidato, margem de erro de 17 a 24 pontos)",
    },
    "quaest_14": {
        "instituto": "Quaest",
        "registro": "BR-08729/2026",
        "campo": "10 a 13/10/2026",
        "n": 2154,
        "arquivo": "docs/fontes/quaest_14102026.pdf",
        "sha256": "112fd4b9b104d288394f27d98da77ec1bc2636cce144bb718f8986caf90c7592",
        "paginas": "19 (grupos pelo voto lembrado; Lula e Flávio sem linha)",
    },
    "datafolha_22": {
        "instituto": "Datafolha",
        "registro": "BR-09709/2026",
        "campo": "20 a 22/10/2026",
        "n": 2520,
        "arquivo": "data/originals/datafolha_102026_22_integra/relatorio.pdf",
        "sha256": "c548241d08d526ce1ceecc87e64cd1ba989634130ba165b9660fbab4219321d4",
        "paginas": "5 (texto corrido, eleitorado somado de Cury, Renan, Caiado e Zema)",
    },
    "datafolha_08": {
        "instituto": "Datafolha",
        "registro": "BR-02949/2026",
        "campo": "06 a 07/10/2026",
        "n": 2520,
        "arquivo": "docs/fontes/datafolha_2t_08102026_integra.pdf",
        "sha256": "9b95078c8f04e961b48719c166a303b354c4366eb59b633642ef0fc0de7aafcb",
        "paginas": "5 (texto corrido; 7% restantes não publicados)",
    },
}

# (fonte, página): {grupo do 1º turno: {F, L, BN, NS}}
LINHAS: dict[tuple[str, int], dict[str, dict[str, float]]] = {
    ("nexus_24", 23): {
        "flavio": {"F": 97.6, "L": 1.7, "BN": 0.2, "NS": 0.5},
        "zema": {"F": 65.9, "L": 18.5, "BN": 0.0, "NS": 15.6},
        "renan": {"F": 54.6, "L": 24.7, "BN": 20.6, "NS": 0.0},
        "caiado": {"F": 47.6, "L": 35.3, "BN": 3.9, "NS": 13.2},
        "cury": {"F": 41.8, "L": 40.6, "BN": 17.4, "NS": 0.2},
        "abstencao": {"F": 40.1, "L": 45.6, "BN": 11.8, "NS": 2.5},
        "lula": {"F": 1.4, "L": 97.9, "BN": 0.2, "NS": 0.5},
        "outros": {"F": 0.0, "L": 49.3, "BN": 0.0, "NS": 50.7},
    },
    ("nexus_24", 22): {
        "terceira": {"F": 48.5, "L": 32.1, "BN": 12.9, "NS": 6.4},
    },
    ("nexus_19", 28): {
        "flavio": {"F": 97.8, "L": 1.6, "BN": 0.3, "NS": 0.3},
        "caiado": {"F": 68.3, "L": 21.6, "BN": 3.8, "NS": 6.4},
        "zema": {"F": 67.7, "L": 13.4, "BN": 18.9, "NS": 0.0},
        "cury": {"F": 44.2, "L": 38.0, "BN": 16.7, "NS": 1.1},
        "abstencao": {"F": 44.1, "L": 49.3, "BN": 4.4, "NS": 2.1},
        "renan": {"F": 43.7, "L": 33.6, "BN": 22.7, "NS": 0.0},
        "lula": {"F": 2.1, "L": 97.4, "BN": 0.3, "NS": 0.1},
        "outros": {"F": 0.0, "L": 100.0, "BN": 0.0, "NS": 0.0},
    },
    ("nexus_19", 27): {
        "terceira": {"F": 50.5, "L": 32.4, "BN": 15.0, "NS": 2.0},
    },
    ("nexus_13", 26): {
        "zema": {"F": 80.0, "L": 0.0, "BN": 12.0, "NS": 8.0},
        "caiado": {"F": 55.0, "L": 27.0, "BN": 11.0, "NS": 7.0},
        "cury": {"F": 43.0, "L": 41.0, "BN": 13.0, "NS": 4.0},
        "renan": {"F": 37.0, "L": 30.0, "BN": 33.0, "NS": 0.0},
        "outros": {"F": 0.0, "L": 100.0, "BN": 0.0, "NS": 0.0},
    },
    ("nexus_13", 25): {
        "flavio": {"F": 98.0, "L": 2.0, "BN": 0.0, "NS": 0.0},
        "lula": {"F": 1.0, "L": 98.0, "BN": 0.0, "NS": 1.0},
        "terceira": {"F": 45.0, "L": 32.0, "BN": 19.0, "NS": 3.0},
        "abstencao": {"F": 49.0, "L": 41.0, "BN": 6.0, "NS": 3.0},
    },
    ("quaest_21", 20): {
        "flavio": {"F": 94.0, "L": 0.0, "BN": 5.0, "NS": 1.0},
        "lula": {"F": 0.0, "L": 95.0, "BN": 4.0, "NS": 1.0},
        "cury": {"F": 33.0, "L": 48.0, "BN": 16.0, "NS": 3.0},
        "caiado": {"F": 57.0, "L": 21.0, "BN": 22.0, "NS": 0.0},
        "renan": {"F": 51.0, "L": 25.0, "BN": 24.0, "NS": 0.0},
        "bn_ou_ausente": {"F": 36.0, "L": 40.0, "BN": 21.0, "NS": 3.0},
    },
    ("quaest_21", 19): {
        "terceira": {"F": 43.0, "L": 37.0, "BN": 19.0, "NS": 1.0},
    },
    ("quaest_14", 19): {
        "cury": {"F": 30.0, "L": 34.0, "BN": 30.0, "NS": 6.0},
        "caiado": {"F": 42.0, "L": 23.0, "BN": 33.0, "NS": 2.0},
        "renan": {"F": 40.0, "L": 14.0, "BN": 43.0, "NS": 3.0},
        "terceira_menores": {"F": 38.0, "L": 33.0, "BN": 22.0, "NS": 7.0},
        "bn_ou_ausente": {"F": 38.0, "L": 43.0, "BN": 17.0, "NS": 2.0},
    },
    ("datafolha_22", 5): {
        "terceira": {"F": 47.0, "L": 26.0, "BN": 21.0, "NS": 6.0},
    },
    ("datafolha_08", 5): {
        "terceira": {"F": 46.0, "L": 32.0, "BN": 15.0, "NS": 7.0},
    },
}

CENTRAL: dict[str, list[tuple[str, int, str]]] = {
    "lula": [("nexus_24", 23, "lula"), ("quaest_21", 20, "lula")],
    "flavio": [("nexus_24", 23, "flavio"), ("quaest_21", 20, "flavio")],
    "cury": [
        ("nexus_24", 23, "cury"),
        ("quaest_21", 20, "cury"),
        ("datafolha_22", 5, "terceira"),
    ],
    "renan": [
        ("nexus_24", 23, "renan"),
        ("quaest_21", 20, "renan"),
        ("datafolha_22", 5, "terceira"),
    ],
    "caiado": [
        ("nexus_24", 23, "caiado"),
        ("quaest_21", 20, "caiado"),
        ("datafolha_22", 5, "terceira"),
    ],
    "zema": [("nexus_24", 23, "zema"), ("datafolha_22", 5, "terceira")],
    "outros": [("nexus_24", 23, "outros")],
}
"""Prior central: média simples da onda mais recente de cada instituto que
publica a linha (Nexus 24/10, Quaest 21/10, Datafolha 22/10)."""

SO_NEXUS = {k: [("nexus_24", 23, k)] for k in TERCEIRA}
SO_DATAFOLHA = {k: [("datafolha_22", 5, "terceira")] for k in TERCEIRA}


def normaliza(linha: dict[str, float]) -> dict[str, float]:
    """F, L, BN em fração, com o NS repartido na proporção dos três."""
    base = linha["F"] + linha["L"] + linha["BN"]
    if base <= 0:
        raise ValueError("linha sem F, L nem BN")
    return {k: linha[k] / base for k in ("F", "L", "BN")}


def media(chaves: list[tuple[str, int, str]]) -> dict[str, float]:
    linhas = [normaliza(LINHAS[(f, pg)][g]) for f, pg, g in chaves]
    return {k: sum(x[k] for x in linhas) / len(linhas) for k in ("F", "L", "BN")}


def citacao(chaves: list[tuple[str, int, str]]) -> str:
    partes = []
    for f, pg, _g in chaves:
        fo = FONTES[f]
        partes.append(f"{fo['instituto']} ({fo['campo']}, p. {pg})")
    return "; ".join(partes)


def linhas_publicadas() -> list[dict[str, Any]]:
    """Todas as linhas transcritas, para a tabela de conferência da página."""
    out = []
    for (f, pg), grupos in LINHAS.items():
        for g, v in grupos.items():
            n = normaliza(v)
            out.append(
                {
                    "fonte": f,
                    "instituto": FONTES[f]["instituto"],
                    "campo": FONTES[f]["campo"],
                    "pagina": pg,
                    "grupo": g,
                    "publicado": v,
                    "soma": round(sum(v.values()), 1),
                    "flavio_entre_finalistas": round(
                        100 * n["F"] / (n["F"] + n["L"]), 2
                    ),
                }
            )
    return out


def prior_linha(
    origem: str,
    *,
    q: float,
    r: float,
    alpha: dict[str, float],
    fidelidade: float | None,
    terceira: dict[str, list[tuple[str, int, str]]],
    bn_hipotese: bool,
    fracao_brancos: float,
) -> dict[str, float]:
    """Linha da prior (frações que somam 1) de uma origem do 1º turno.

    `q`: fração do eleitor que votou no 1º turno e faltou no 2º (rotatividade).
    `r`: fração do ausente do 1º turno que votou no 2º.
    `alpha`: divisão desses que voltaram entre L, F e BN (regressão).
    `fidelidade`: força a fidelidade de base de Lula e Flávio (sensibilidade).
    `bn_hipotese`: branco e nulo do 1º turno majoritariamente branco e nulo
    (hipótese da casa); falso usa a linha mista da Quaest (p. 20).
    """
    if origem == "abstencao":
        alpha = _piso(dict(alpha))
        bn = alpha["BN"]
        linha = {
            "lula": r * alpha["L"],
            "flavio": r * alpha["F"],
            "brancos": r * bn * fracao_brancos,
            "nulos": r * bn * (1 - fracao_brancos),
            "abstencao": 1 - r,
        }
    else:
        if origem in ("lula", "flavio"):
            v = media(CENTRAL[origem])
            if fidelidade is not None:
                proprio = "L" if origem == "lula" else "F"
                outro = "F" if origem == "lula" else "L"
                resto = 1 - v[proprio]
                cruz = v[outro] / resto if resto > 0 else 0.5
                v = {
                    proprio: fidelidade,
                    outro: (1 - fidelidade) * cruz,
                    "BN": (1 - fidelidade) * (1 - cruz),
                }
        elif origem in TERCEIRA:
            v = media(terceira[origem])
        elif bn_hipotese:
            q21 = normaliza(LINHAS[("quaest_21", 20)]["bn_ou_ausente"])
            fl = q21["F"] + q21["L"]
            v = {"F": 0.5 * q21["F"] / fl, "L": 0.5 * q21["L"] / fl, "BN": 0.5}
        else:
            v = normaliza(LINHAS[("quaest_21", 20)]["bn_ou_ausente"])
        v = _piso(v)
        if origem == "brancos":
            fb = 0.7 if bn_hipotese else fracao_brancos
        elif origem == "nulos":
            fb = 0.3 if bn_hipotese else fracao_brancos
        else:
            fb = fracao_brancos
        linha = {
            "lula": (1 - q) * v["L"],
            "flavio": (1 - q) * v["F"],
            "brancos": (1 - q) * v["BN"] * fb,
            "nulos": (1 - q) * v["BN"] * (1 - fb),
            "abstencao": q,
        }
    s = sum(linha.values())
    return {k: x / s for k, x in linha.items()}


def _piso(v: dict[str, float]) -> dict[str, float]:
    """Piso de 0,2% em F, L e BN antes de repartir; renormaliza."""
    w = {k: max(x, PISO) for k, x in v.items()}
    s = sum(w.values())
    return {k: x / s for k, x in w.items()}


def tipo_elo(origem: str, destino: str) -> str:
    """Natureza do elo na figura: medido (linha publicada), regressão ou estimado."""
    if origem == "abstencao":
        return "estimado" if destino == "abstencao" else "regressao"
    if destino == "abstencao" or origem in ("brancos", "nulos"):
        return "estimado"
    return "medido"
