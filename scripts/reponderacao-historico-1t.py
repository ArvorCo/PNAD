"""Recupera a composição dos grupos históricos sem alterar os votos dos líderes.

A geração lê os PDFs locais; o cálculo usa o manifesto compacto versionado.
Uma lista fechada de candidatos permite zero estrutural de um grupo não oferecido.
Ausência de cruzamento de candidato oferecido, por outro lado, nunca vira zero.
"""

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "analysis/reponderacao/grupos_1t_historico.json"
POLLS = ROOT / "analysis/reponderacao/pesquisas"


def refine(poll, entries):
    """Desfaz somente agregações internas comprovadas contra as fontes."""
    entry = entries.get(poll["id"])
    if not entry or "1t" not in poll.get("cruzamentos", {}):
        return poll
    out = deepcopy(poll)
    table = out["cruzamentos"]["1t"]
    pub = out["publicado"]["1t"]
    columns = entry.get("decomposicao_outros")
    if columns:
        idx = table["opcoes"].index("outros")
        expected = [row[idx] for row in table["linhas"]]
        actual = [
            sum(c["renda"][i] for c in columns.values()) for i in range(len(expected))
        ]
        correction = entry.get("correcao_outros")
        if correction:
            assert expected == correction["renda_anterior"], poll["id"]
            expected = correction["renda_corrigida"]
        assert all(
            abs(a - b) < 0.001 for a, b in zip(expected, actual, strict=True)
        ), poll["id"]
        assert (
            abs(sum(c["publicado"] for c in columns.values()) - pub["outros"]) < 0.001
        ), poll["id"]
        table["opcoes"][idx : idx + 1] = columns.keys()
        pub.pop("outros")
        for key, column in columns.items():
            assert key not in pub, (poll["id"], key)
            pub[key] = column["publicado"]
        for i, row in enumerate(table["linhas"]):
            row[idx : idx + 1] = [c["renda"][i] for c in columns.values()]
    out["grupos_1t_fonte"] = {
        k: v for k, v in entry.items() if k != "decomposicao_outros"
    }
    return out


def raw(ident):
    return json.loads((POLLS / f"{ident}.json").read_text())


def page(ident):
    import fitz

    poll = raw(ident)
    doc = fitz.open(ROOT / poll["fonte"]["pdf"])
    return doc[poll["fonte"]["paginas"]["1t_renda"] - 1]


def column(published, values):
    return {"publicado": published, "renda": values}


def aliases(ident, name):
    poll = raw(ident)
    table = poll["cruzamentos"]["1t"]
    idx = table["opcoes"].index("outros")
    return {
        name: column(
            poll["publicado"]["1t"]["outros"], [r[idx] for r in table["linhas"]]
        )
    }


def datafolha(ident, labels):
    """Colunas por coordenadas: conserva células vazias como zero, sem deslocá-las."""
    words = page(ident).get_text("words")
    lula = next(w for w in words if w[4] == "Lula(PT)")

    def row(y):
        return sorted(
            [w for w in words if w[4].isdigit() and abs((w[1] + w[3]) / 2 - y) < 4],
            key=lambda w: w[0],
        )

    lula_values = row((lula[1] + lula[3]) / 2)
    assert len(lula_values) == 15, (ident, len(lula_values))
    positions = [(w[0] + w[2]) / 2 for w in [lula_values[0], *lula_values[-4:]]]
    cols = {}
    for key, label in labels.items():
        word = next(w for w in words if w[4] == label and abs(w[0] - lula[0]) < 1)
        numbers = row((word[1] + word[3]) / 2)
        values = []
        for x in positions:
            matches = [int(w[4]) for w in numbers if abs((w[0] + w[2]) / 2 - x) < 10]
            assert len(matches) <= 1, (ident, key, x)
            values.append(matches[0] if matches else 0)
        cols[key] = column(values[0], values[1:])
    return cols


def nexus(ident, names):
    text = page(ident).get_text()
    block = text[text.index("TOTAL") : text.index("PEA")]
    vals = [float(v.replace(",", ".")) for v in re.findall(r"(\d+(?:,\d+)?)%", block)]
    assert len(vals) == 5 * len(names), (ident, len(vals), len(names))
    return {
        name: column(vals[i], [vals[j * len(names) + i] for j in range(1, 5)])
        for i, name in enumerate(names)
        if name in {"joaquim", "aecio", "daciolo"}
    }


def generate():
    entries = {}

    def add(
        ident,
        columns=None,
        note="Lista completa do cenário conferida; nomes ausentes não foram oferecidos.",
        **extra,
    ):
        source = raw(ident)["fonte"]
        entries[ident] = {
            "lista_completa": True,
            "pdf": source["pdf"],
            "pagina_renda": source["paginas"]["1t_renda"],
            "nota": note,
            **extra,
        }
        if columns:
            entries[ident]["decomposicao_outros"] = columns
        refine(raw(ident), entries)  # Prova de fechamento de cada desagregação.

    add(
        "atlas_2026-05-18",
        aliases("atlas_2026-05-18", "aldo"),
        "P.20: outros era apenas Aldo Rebelo, agregado pelo nosso manifesto. Nenhum nome do grupo residual foi oferecido neste cenário.",
    )
    add(
        "atlas_2026-06-30",
        {
            "joaquim": column(1, [1.4, 0.6, 0.6, 1, 1.2]),
            "aecio": column(0.7, [2, 0.2, 0.1, 0.4, 0.7]),
            "daciolo": column(0.3, [0, 0.5, 0, 0.7, 0]),
            "rui": column(0.1, [0, 0, 0, 0.3, 0]),
            "edmilson": column(0, [0.2, 0, 0, 0, 0]),
            "hertz": column(0, [0, 0, 0, 0, 0.1]),
        },
        "P.20, imagem do cruzamento: seis candidaturas antes somadas em outros; totais conforme placar da onda e nota do manifesto original.",
    )
    add(
        "atlas_2026-07-27",
        {
            "daciolo": column(0.1, [0, 0, 0.1, 0, 0.1]),
            "hertz": column(0.1, [0, 0.1, 0.1, 0, 0.3]),
            "rui": column(0, [0, 0, 0, 0, 0.1]),
            "edmilson": column(0, [0, 0, 0.2, 0, 0]),
        },
        "Pp.20–21: quatro nomes antes agregados; transcrição das cinco faixas da p.21.",
        pagina_renda=21,
    )
    for ident, labels in {
        "datafolha_2026-05-21": {
            "rui": "Rui",
            "daciolo": "Cabo",
            "aldo": "Aldo",
            "hertz": "Hertz",
        },
        "datafolha_2026-06-18": {
            "aecio": "Aécio",
            "joaquim": "Joaquim",
            "daciolo": "Cabo",
            "rui": "Rui",
            "hertz": "Hertz",
            "edmilson": "Edmilson",
        },
        "datafolha_2026-07-23": {
            "rui": "Rui",
            "daciolo": "Cabo",
            "edmilson": "Edmilson",
            "avalanche": "Leonardo",
            "hertz": "Hertz",
        },
    }.items():
        corrections = {
            "datafolha_2026-06-18": {
                "renda_anterior": [5, 3, 6, 6],
                "renda_corrigida": [5, 3, 7, 5],
            },
            "datafolha_2026-07-23": {
                "renda_anterior": [4, 2, 2, 1],
                "renda_corrigida": [3, 2, 2, 0],
            },
        }
        extra = {"correcao_outros": corrections[ident]} if ident in corrections else {}
        add(
            ident,
            datafolha(ident, labels),
            "Texto nativo extraído por coordenadas da situação A: coluna total e quatro últimas colunas de renda. Células vazias preservadas como zero. Em junho/julho, a releitura visual confirmou erro de soma no antigo outros; vetores anterior e corrigido ficam registrados. Votos de Lula e Flávio preservados.",
            **extra,
        )
    for ident, names in {
        "nexus_2026-05-24": "lula flavio caiado zema renan joaquim cury daciolo bn ns",
        "nexus_2026-06-14": "lula flavio caiado renan zema joaquim cury aecio daciolo bn ns",
        "nexus_2026-06-28": "lula flavio caiado renan zema joaquim cury aecio daciolo bn ns",
        "nexus_2026-07-12": "lula flavio caiado renan zema joaquim cury aecio daciolo bn ns",
        "nexus_2026-07-26": "lula flavio caiado renan zema cury daciolo bn ns",
    }.items():
        add(
            ident,
            nexus(ident, names.split()),
            "Extração do texto nativo: linha TOTAL e quatro linhas de renda, com largura validada contra o cabeçalho. Os menores são individualizados no PDF; outros era soma interna.",
        )
    for ident in ["poderdata_2026-05-28", "poderdata_2026-06-24"]:
        add(
            ident,
            aliases(ident, "joaquim"),
            "P.11: outros era apenas Joaquim Barbosa, agregado internamente. Mantido o topline da divulgação, inclusive 3% de junho contra 2% na coluna Total do cruzamento.",
        )
    for ident in ["poderdata_2026-07-15", "poderdata_2026-07-29"]:
        add(
            ident,
            note="P.11: lista completa contém Lula, Flávio, Cury, Renan, Zema e Caiado, além da não escolha. Nenhum candidato do residual foi oferecido: sua soma no cenário é zero, não uma estimativa de voto em candidato ausente.",
        )
    text = page("poderdata_2026-08-12").get_text()
    cols = {}
    for key, label in {
        "clariana": "Clariana Barão",
        "edmilson": "Edmilson Costa",
        "hertz": "Hertz Dias",
        "avalanche": "Leonardo Avalanche",
        "rui": "Rui Costa Pimenta",
        "grassi": "Veterinário Wilson Grassi",
    }.items():
        block = re.search(re.escape(label) + r"\n((?:\d+%\n){4})", text)
        assert block, label
        v = [int(n) for n in re.findall(r"\d+", block[1])]
        cols[key] = column(v[3], v[:3])
    add(
        "poderdata_2026-08-12",
        cols,
        "P.11: extração por rótulo do texto nativo; todas as 13 candidaturas têm cruzamento, incluindo Clariana e Leonardo Avalanche antes somados a outros.",
    )
    for ident, columns in {
        "quaest_2026-05-11": {
            "daciolo": column(1, [0, 1, 1]),
            "aldo": column(0, [0, 0, 0]),
            "hertz": column(0, [0, 0, 0]),
        },
        "quaest_2026-06-08": {
            "aecio": column(2, [2, 2, 2]),
            "joaquim": column(1, [0, 1, 1]),
            "daciolo": column(0, [0, 0, 0]),
            "edmilson": column(0, [0, 0, 0]),
            "hero": column(0, [0, 0, 0]),
        },
        "quaest_2026-07-13": {
            "daciolo": column(1, [0, 1, 0]),
            "joaquim": column(1, [1, 1, 1]),
            "edmilson": column(0, [0, 0, 0]),
            "hero": column(0, [0, 0, 0]),
            "hertz": column(0, [0, 0, 0]),
        },
        "quaest_2026-08-03": {
            "daciolo": column(1, [1, 0, 1]),
            "clariana": column(0, [0, 0, 0]),
            "edmilson": column(0, [0, 0, 0]),
            "hertz": column(0, [0, 0, 0]),
            "avalanche": column(0, [0, 0, 0]),
        },
        "quaest_2026-08-13": {
            "clariana": column(0, [0, 0, 0]),
            "edmilson": column(0, [1, 0, 0]),
            "hertz": column(0, [0, 0, 0]),
            "avalanche": column(0, [0, 0, 0]),
            "rui": column(0, [0, 0, 0]),
            "grassi": column(0, [0, 0, 0]),
        },
    }.items():
        add(
            ident,
            columns,
            "Transcrição das imagens do topline e do cruzamento por renda nas páginas indicadas no manifesto original. Zeros impressos ou barras/células vazias identificadas, sem deslocar linhas; a soma fecha exatamente o outros anterior.",
        )
    add(
        "realtime_2026-05-04",
        {
            "aldo": column(1, [0, 2, 1]),
            "daciolo": column(1, [1, 1, 0]),
            "rui": column(0, [0, 0, 1]),
        },
        "P.11: composição de outros conferida nos rótulos por candidato e já documentada na nota original. Demais nomes sem barra são zeros; lista completa do cenário 01.",
    )
    add(
        "realtime_2026-05-30",
        {
            "aecio": column(3, [2, 5, 2]),
            "joaquim": column(3, [1, 3, 5]),
            "outros_esquerda": column(1, [1, 0, 1]),
        },
        "P.11 e nota original: Aécio e Joaquim individualizados. Residual contém Cabo Daciolo, Rui, Samara, Edmilson e Hertz; nenhum pertence ao centro-direita acordado.",
        membros_residual=["daciolo", "rui", "samara", "edmilson", "hertz"],
    )
    # Esta alternativa foi conferida e transcrita em reponderacao-cenarios.py.
    entries["gerp_2026-05-12"] = {
        "lista_completa": True,
        "pdf": raw("gerp_2026-05-12")["fonte"]["pdf"],
        "pagina_renda": 14,
        "nota": "Cenário 2 sem Marçal, pp.13–14, selecionado por reponderacao-cenarios.py. Lista completa com Ciro e Aldo; Cury não foi oferecido.",
    }
    MANIFEST.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(entries)} ondas históricas documentadas: {MANIFEST}")


if __name__ == "__main__":
    generate()
