#!/usr/bin/env python3
"""Audita as fontes de 21/09/2026 sem misturar amostra estadual e nacional.

Nexus: extração das tabelas nativas, conferida por sexo e renda.
Palver: transcrição visual das páginas de imagem; duas partições independentes.
Microdados individuais não foram publicados; nenhum raking conjunto é imputado.
"""

import hashlib
import importlib.util
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao"
POLLS = BASE / "pesquisas"
PALVER = ROOT / "data/originals/palver_092026_21"
COMMIT = "7523cf14f0095f088ac9680e9c64a9923289fdb1"
GITHUB = f"https://github.com/palverdata/pesquisa-palver/blob/{COMMIT}"

# PDF Onda 3, p. 32: Lula, Flávio, Renan, Cury, Outros.
# O PDF mostra somente cinco opções no cruzamento. Não se inventam as omitidas.
PALVER_1T = [[43, 46, 7, 2, 1], [38, 42, 15, 2, 1], [45, 35, 15, 1, 0]]
# PDF p. 40: Lula, Flávio, branco/nulo/não votaria, indecisos.
PALVER_2T = [[44, 50, 5, 2], [41, 47, 11, 1], [46, 42, 11, 1]]
# PDF pp. 32 e 40, homens/mulheres. Metas da p. 18.
PALVER_SEX = {"1t": [[34, 45], [49, 40]], "2t": [[34, 51], [51, 44]]}


def dump(path, data, indent=2):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n")


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pages(pdf):
    return subprocess.check_output(
        ["pdftotext", "-layout", str(pdf), "-"], text=True
    ).split("\f")


def rows(page, width):
    return [
        [int(v) for v in values]
        for line in page.splitlines()
        if len(values := re.findall(r"(\d+)%", line)) == width
    ]


def nexus():
    poll = json.loads((POLLS / "nexus_2026-09-13.json").read_text())
    pdf = ROOT / "data/originals/nexus_092026_21/relatorio.pdf"
    text = pages(pdf)
    poll.update(
        id="nexus_2026-09-20",
        registro_tse="BR-00485/2026",
        n=2006,
        campo={"inicio": "2026-09-18", "fim": "2026-09-20"},
        divulgacao="2026-09-21",
        notas="15ª rodada; 140 páginas. Leitura comprovada por renda e sexo.",
    )
    poll.pop("dossie", None)
    poll["fonte"] = {
        "pdf": str(pdf.relative_to(ROOT)),
        "tipo": "relatorio",
        "url": "https://static.poder360.com.br/uploads/2026/09/BTG-Nexus-Eleicoes-2026-Rodada-15.pdf",
        "paginas": {
            "metodologia": 4,
            "perfil_renda": 137,
            "1t_renda": 34,
            "2t_renda": 81,
        },
    }
    profile = text[136]
    labels = ["Até 1 S.M.", "De 1 até 2 S.M.", "De 2 até 5 S.M.", "Mais de 5 S.M."]
    poll["renda"]["amostra_pct"] = [
        int(re.search(re.escape(label) + r"\s+(\d+)%", profile).group(1))
        for label in labels
    ]
    poll["renda"]["nota"] = (
        "Perfil ponderado da p. 137; PNADC anual 2025 visita 1 e TSE junho/2026 declarados na p. 4. "
        "O ajuste testa a nossa régua apesar da mesma edição da PNAD: universo, conceito e tratamento "
        "da renda podem diferir. Cortes em salários de 2026 confirmados na PF15, p. 13 do "
        "questionário BR-00485/2026, obtido no PesqEle em 21/09: renda familiar no mês passado, "
        "incluindo trabalho, aposentadoria, pensões, investimentos e auxílios."
    )
    for turn, page in [("1t", 34), ("2t", 81)]:
        options = poll["cruzamentos"][turn]["opcoes"]
        values = rows(text[page - 1], len(options))
        assert len(values) == 16, (page, len(values))
        poll["publicado"][turn] = dict(zip(options, values[0], strict=True))
        poll["cruzamentos"][turn] = {
            "opcoes": options,
            "linhas": values[1:5],
            "nota": f"Extração programática da p. {page}, quatro linhas de renda; conferência visual.",
        }
    controls = {
        turn: {
            "pagina": page,
            "pesos": [53, 47],
            "linhas": [r[:2] for r in rows(text[page - 1], width)[1:3]],
        }
        for turn, page, width in [("1t", 33, 9), ("2t", 80, 4)]
    }
    return poll, controls


def palver():
    poll = json.loads((POLLS / "palver_2026-09-07.json").read_text())
    for key in ["ignorar", "motivo"]:
        poll.pop(key, None)
    poll.update(
        id="palver_2026-09-18",
        contratante="Palver (iniciativa própria, onda 3, método v2)",
        registro_tse="BR-00860/2026",
        campo={"inicio": "2026-09-15", "fim": "2026-09-18"},
        divulgacao="2026-09-21",
    )
    poll["fonte"] = {
        "pdf": "data/originals/palver_092026_21/relatorio.pdf",
        "tipo": "relatorio",
        "url": "https://www.palver.com/api/surveys/voting-intention-2026-september-w3/report",
        "paginas": {
            "metodologia": 18,
            "perfil_renda": 18,
            "1t_topline": 31,
            "1t_renda": 32,
            "2t_topline": 38,
            "2t_renda": 40,
        },
    }
    poll["renda"].update(
        amostra_pct=[42.12, 39.56, 18.31],
        perfil_tipo="alvo_de_calibracao",
        nota="Metas de calibração declaradas na p. 18, normalizadas de 99,99% para 100%; "
        "não são contagens brutas nem perfil ponderado medido nesta onda. A p. 20 declara aderência "
        "exata às margens sem aparo, mas a p. 18 admite tolerância de até 3 pp. "
        "Sem diagnóstico de margens publicado da onda 3, a recomposição condiciona-se ao alvo. "
        "Referência do instituto: PNADC 2024 visita 5, renda domiciliar habitual VD5007, "
        "cortes nominais de R$ 3.242 e R$ 8.105.",
    )
    first = [
        "lula",
        "flavio",
        "renan_santos",
        "cury",
        "caiado",
        "zema",
        "outros",
        "branco_nulo",
        "indecisos",
    ]
    second = ["lula", "flavio", "branco_nulo", "indecisos"]
    poll["publicado"] = {
        "1t": dict(zip(first, [41, 42, 11, 2, 1, 1, 1, 1, 0], strict=True)),
        "2t": dict(zip(second, [43, 47, 9, 1], strict=True)),
    }
    poll["cruzamentos"] = {
        "1t": {
            "opcoes": ["lula", "flavio", "renan_santos", "cury", "outros"],
            "linhas": PALVER_1T,
            "nota": "Questão 2, p. 32, transcrição visual. Somente as cinco opções exibidas têm ajuste; "
            "não se estima voto das opções omitidas. Controle independente por sexo na mesma página.",
        },
        "2t": {
            "opcoes": second,
            "linhas": PALVER_2T,
            "nota": "Questão 4, cenário 1, p. 40, transcrição visual. Controle independente por sexo. "
            "Arredondamentos mantidos, inclusive soma de 101% na primeira faixa.",
        },
    }
    poll["notas"] = (
        "O PDF pp. 16 e 22 encerra o campo em 18/09, apesar de notícia citar 20/09. "
        "PNAD 2024 visita 5, região × voto de 2022 e filiação partidária. "
        "Microdados prometidos somente após o 2º turno (p. 6). "
        "n efetivo Kish 1.232, efeito dos pesos 4,06, máximo 21,73, sem aparo (p. 20)."
    )
    controls = {
        turn: {"pagina": page, "pesos": [48.12, 51.88], "linhas": PALVER_SEX[turn]}
        for turn, page in [("1t", 32), ("2t", 40)]
    }
    return poll, controls


def evidence(poll, controls, engine):
    result = engine.process_poll(poll, engine.Benchmark(), engine.load_ipca())
    checks = {}
    for turn, control in controls.items():
        recomposed = engine.compose(control["linhas"], control["pesos"])
        pub = [poll["publicado"][turn][c] for c in ["lula", "flavio"]]
        residual = max(abs(a - b) for a, b in zip(recomposed, pub, strict=True))
        assert residual <= 1.5, (poll["id"], turn, residual)
        assert result["turnos"][turn]["residuo_max"] <= 1.5
        checks[turn] = {
            **control,
            "recomposto_lula_flavio": recomposed,
            "residuo_max": residual,
            "residuo_renda": result["turnos"][turn]["residuo_max"],
        }
    return checks


def main():
    engine = load_module("reponderacao-pnad")
    polls = [nexus(), palver()]
    checks = {}
    for poll, controls in polls:
        checks[poll["id"]] = evidence(poll, controls, engine)
        dump(POLLS / f'{poll["id"]}.json', poll)

    # Preserva a ficha original, mas não mistura uma versão retirada com a v2.
    previous = POLLS / "palver_2026-09-07.json"
    old = json.loads(previous.read_text())
    old.update(
        ignorar=True,
        motivo="Versão original v1 substituída pela Palver em 21/09/2026. "
        "Ficha e cruzamentos preservados como arquivo; fora da série ativa e das médias. "
        "O relatório novo publica os placares revisados v2, mas não o voto por renda revisado da onda 2.",
    )
    dump(previous, old, indent=1)
    revised = {
        "id": "palver_2026-09-07_v2",
        "instituto": "Palver",
        "contratante": "Palver",
        "registro_tse": "BR-06100/2026",
        "campo": old["campo"],
        "divulgacao": "2026-09-21",
        "n": 5000,
        "fonte": {
            **polls[1][0]["fonte"],
            "rotulo": "Palver · onda 2 revisada",
            "paginas": {"1t_topline": 30, "2t_topline": 37},
        },
        "publicado": {
            "1t": {"lula": 41, "flavio": 40, "renan_santos": 9, "cury": 5},
            "2t": {"lula": 44, "flavio": 47, "branco_nulo": 8, "indecisos": 1},
        },
        "ignorar": True,
        "motivo": "Recalibração da mesma amostra de 04–07/09 por filiação partidária. "
        "Placares revistos nas pp. 30 e 37 da onda 3, sem cruzamento por renda revisto. "
        "Não se reaplica o cruzamento da versão v1 aos novos placares.",
    }
    dump(POLLS / f'{revised["id"]}.json', revised)
    audit = {
        "data": "2026-09-21",
        "controles": checks,
        "palver": {
            "git_commit": COMMIT,
            "github": GITHUB,
            "microdados_publicos": False,
            "fonte_ausencia": {
                "pdf_pagina": 6,
                "arquivo": "README.md",
                "secao": "Os microdados ponderados",
            },
            "pnad": {
                "ano": 2024,
                "visita": 5,
                "variavel_renda": "VD5007",
                "sm_cortes": 1621,
            },
            "voto_2022": {
                "usa": True,
                "cruzamento": ["reg_std", "vote_std"],
                "categorias": ["Lula", "Jair Bolsonaro", "Branco/Nulo"],
                "exclui_exterior": True,
                "nota": "Código público v1 recodifica quem não votou ou não informou para Branco/Nulo; "
                "o alvo regional considera votos depositados, excluindo abstenções. "
                "O PDF v2 confirma região × voto, mas a configuração da onda 3 não está no snapshot.",
            },
            "filiacao": {
                "introduzida_v2": True,
                "referencia": "TSE agosto/2026",
                "pagina": 13,
            },
            "diagnosticos": {
                "n": 5000,
                "n_efetivo_kish": 1232,
                "deff_pesos": 4.06,
                "peso_min": 0.00022,
                "peso_mediano": 0.404,
                "peso_max": 21.73,
                "aparado": False,
            },
            "onda2_revisada": revised["publicado"],
            "limite": "Sem respostas individuais e pesos, TSE + PNAD 2025 em calibração conjunta não é identificável. "
            "As tabelas de renda permitem somente a sensibilidade marginal publicada no agregador.",
        },
        "fontes": json.loads((BASE / "fontes_20260921.json").read_text()),
        "estaduais": [
            {
                "uf": "SP",
                "registro": "BR-09702/2026",
                "n": 2000,
                "divulgacao_pdf": "2026-09-21",
                "fonte": "realtime_sp",
            },
            {
                "uf": "PR",
                "registro": "BR-08843/2026",
                "n": 1600,
                "divulgacao_pdf": "2026-09-16",
                "fonte": "realtime_pr",
            },
            {
                "uf": "AC",
                "registro": "BR-01620/2026",
                "n": 1600,
                "divulgacao_pdf": "2026-09-21",
                "fonte": "realtime_ac",
            },
            {
                "uf": "MG",
                "registro": "MG-07331/2026",
                "n": 2000,
                "divulgacao_pdf": "2026-09-21",
                "fonte": "realtime_mg",
            },
        ],
    }
    for source in audit["fontes"]:
        payload = (ROOT / source["pdf"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == source["sha256"]
    dump(BASE / "auditoria_20260921.json", audit)
    dump(ROOT / "docs/assets/reponderacao_20260921.json", audit)
    # Explorer supersedes PDF-only transcriptions when the archived tables exist.
    if (BASE / "palver_explorer_20260921/audit.json").exists():
        load_module("palver-explorer-integrate").integrate()
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
