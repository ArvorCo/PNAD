#!/usr/bin/env python3
"""Ondas estaduais de véspera do Datafolha (presidente por UF) a partir do painel do G1.

O Datafolha divulgou em 02/10/2026 o voto presidencial em SP, MG, RJ, PE e DF,
com campo entre 28/09 e 01/10. Não há PDF estadual publicado: os placares vêm
da API pública do painel do contratante (G1) e a ficha (campo, n, registro)
vem da matéria do próprio instituto em datafolha.folha.uol.com.br.

Uso:
    python3 scripts/predicao-2026-estaduais-vespera.py --capturar   # baixa e arquiva
    python3 scripts/predicao-2026-estaduais-vespera.py              # só transcreve

A transcrição lê apenas o acervo arquivado, confere o SHA-256 de cada arquivo
contra o fonte.json e exige que cada dado da ficha apareça literalmente no texto
da matéria arquivada. Célula ausente no painel não é preenchida.
"""

import argparse
import hashlib
import html
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARQ = ROOT / "data/originals/estaduais_102026_03"
OUT = ROOT / "analysis/predicao_2026/estaduais"
API = "https://especiaisg1.globo/api/pesquisas-eleitorais/graficos/{pid}/?tipo_pergunta={codigo}&instituto=Datafolha"
PAINEL = "https://especiaisg1.globo/{uf}/{slug}/eleicoes/2026/pesquisas-eleitorais/presidente/1-turno/datafolha/internal/"
RESUMO = "https://www1.folha.uol.com.br/poder/2026/10/datafolha-lula-lidera-em-mg-e-flavio-no-rj-no-1o-turno-rivais-estao-empatados-em-sp.shtml"
DF_SITE = "https://datafolha.folha.uol.com.br/eleicoes/2026/10/"
PERGUNTAS = {"1t": "ESTIMULADA-PRE-002", "2t": "SEGTURNO-PRE-001"}
DATA_PAINEL = "2026-10-02"
DIVULGACAO = "2026-10-02"

# Ficha de cada UF, conferida contra a matéria do Datafolha (texto literal em `prova`).
UFS = {
    "SP": {
        "slug": "sao-paulo",
        "pid": 180,
        "materia": DF_SITE
        + "tarcisio-de-freitas-tem-56-dos-validos-e-e-favorito-para-vencer-no-1o-turno-em-sao-paulo.shtml",
        "campo": "2026-09-28 a 2026-09-30",
        "n": 1610,
        "municipios": 65,
        "registro_tse": "BR-02676/2026",
        "registro_tse_estadual": "SP-01367/2026",
        "margem_pp": 2,
        "prova": [
            "entre os dias 28 e 30 de setembro de 2026",
            "1.610 entrevistas presenciais, em 65 municípios",
            "SP-01367/2026 e BR-02676/2026",
        ],
    },
    "MG": {
        "slug": "minas-gerais",
        "pid": 165,
        "materia": DF_SITE
        + "cleitinho-republicanos-segue-na-lideranca-com-49-dos-votos-validos-em-segundo-patrus-ananias-pt-tem-20-kalil-tem-13.shtml",
        "campo": "2026-09-28 a 2026-10-01",
        "n": 1204,
        "municipios": 55,
        "registro_tse": "BR-03604/2026",
        "registro_tse_estadual": "MG-09729/2026",
        "margem_pp": 3,
        "prova": [
            "nos dias 28 de setembro a 01 de outubro de 2026",
            "1.204 entrevistas presenciais, em 55 municípios",
            "MG-09729/2026 e BR-03604/2026",
        ],
    },
    "RJ": {
        "slug": "rio-de-janeiro",
        "pid": 173,
        "materia": DF_SITE
        + "eduardo-paes-psd-mantem-a-lideranca-com-47-dos-votos-validos-douglas-ruas-pl-cresce-e-alcanca-35.shtml",
        "campo": "2026-09-29 a 2026-10-01",
        "n": 1204,
        "municipios": 35,
        "registro_tse": "BR-01272/2026",
        "registro_tse_estadual": "RJ-02070/2026",
        "margem_pp": 3,
        "prova": [
            "nos dias 29 de setembro a 01 de outubro de 2026",
            "1.204 entrevistas presenciais, em 35 municípios",
            "RJ-02070/2026 e BR-01272/2026",
        ],
    },
    "PE": {
        "slug": "pernambuco",
        "pid": 170,
        "materia": DF_SITE
        + "raquel-lyra-psd-e-joao-campos-psb-seguem-tecnicamente-empatados-com-respectivamente-50-e-47-dos-votos-validos-disputa-segue-indefinida.shtml",
        "campo": "2026-09-28 a 2026-10-01",
        "n": 1204,
        "municipios": 48,
        "registro_tse": "BR-00950/2026",
        "registro_tse_estadual": "PE-06822/2026",
        "margem_pp": 3,
        "prova": [
            "nos dias 28 de setembro a 01 de outubro de 2026",
            "1.204 entrevistas presenciais, em 48 municípios",
            "PE-06822/2026 e BR-00950/2026",
        ],
    },
    "DF": {
        "slug": "distrito-federal",
        "pid": 161,
        "materia": DF_SITE
        + "sem-arruda-celina-leao-pp-tem-53-dos-validos-e-pode-vencer-no-1o-turno.shtml",
        "campo": "2026-09-28 a 2026-09-30",
        "n": 910,
        "municipios": None,
        "registro_tse": "BR-09530/2026",
        "registro_tse_estadual": "DF-00905/2026",
        "margem_pp": 3,
        "prova": [
            "entre 28 e 30 de setembro de 2026",
            "910 entrevistas presenciais",
            "DF-00905/2026 e BR-09530/2026",
        ],
    },
}

# Votos válidos publicados na matéria-resumo da Folha, frase literal como prova.
VALIDOS = {
    "SP": (
        {"Flávio": 41, "Lula": 40},
        "Flávio Bolsonaro registra 41% dos votos válidos no primeiro turno, enquanto Lula aparece com 40%",
    ),
    "MG": (
        {"Lula": 45, "Flávio": 38},
        "indica 45% para Lula e 38% para Flávio Bolsonaro",
    ),
    "RJ": (
        {"Flávio": 48, "Lula": 40},
        "48% das intenções de voto para Flávio Bolsonaro e 40% para Lula",
    ),
    "PE": (
        {"Lula": 65, "Flávio": 26},
        "Lula soma 65% dos votos válidos no primeiro turno, ante 26% de Flávio Bolsonaro",
    ),
    "DF": ({"Flávio": 46, "Lula": 36}, "indica 46% para Flávio e 36% para Lula"),
}

# Rótulo do painel -> chave canônica do acervo. Avalanche não consta do cartão do painel.
NOMES = {
    "Lula": "Lula",
    "Flavio Bolsonaro": "Flávio",
    "Ronaldo Caiado": "Caiado",
    "Escritor Augusto Cury": "Cury",
    "Renan Santos": "Renan",
    "Zema": "Zema",
    "Samara": "Samara",
    "Rui Costa Pimenta": "Pimenta",
    "Veterinário Wilson Grassi": "Grassi",
    "Clariana Barão": "Clariana",
    "Edmilson Costa": "Edmilson",
    "Hertz Dias": "Hertz",
    "Em Branco/Nulo/Nenhum": "Branco/nulo",
    "Indecisos": "Indecisos",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def agora():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def baixa(url, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [
            "curl",
            "-s",
            "-A",
            "Mozilla/5.0",
            "-o",
            str(destino),
            "-w",
            "%{http_code}",
            url,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    if r.stdout != "200":
        raise RuntimeError(f"HTTP {r.stdout} em {url}")
    return {
        "url": url,
        "arquivo": str(destino.relative_to(ROOT)),
        "bytes": destino.stat().st_size,
        "sha256": sha256(destino),
        "capturado_em": agora(),
        "http": 200,
    }


def texto(path):
    bruto = path.read_text(encoding="utf-8", errors="ignore")
    bruto = re.sub(
        r"<script.*?</script>|<style.*?</style>", " ", bruto, flags=re.DOTALL
    )
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", bruto)))


def capturar():
    comum = ARQ / "comum"
    resumo = baixa(RESUMO, comum / "materia_folha_resumo.html")
    (comum / "fonte.json").write_text(
        json.dumps({"materia_folha_resumo": resumo}, ensure_ascii=False, indent=2)
        + "\n"
    )
    for uf, f in UFS.items():
        pasta = ARQ / f"datafolha_{uf}"
        painel = baixa(
            PAINEL.format(uf=uf.lower(), slug=f["slug"]), pasta / "g1_painel.html"
        )
        api = {}
        for turno, codigo in PERGUNTAS.items():
            api[turno] = baixa(
                API.format(pid=f["pid"], codigo=codigo), pasta / f"g1_{turno}.json"
            )
            api[turno]["tipo_pergunta"] = codigo
        materia = baixa(f["materia"], pasta / "materia_datafolha.html")
        fonte = {
            "instituto": "Datafolha",
            "uf": uf,
            "contratante": "Folha de S.Paulo e TV Globo",
            "registro_tse": f["registro_tse"],
            "registro_tse_estadual": f["registro_tse_estadual"],
            "campo": f["campo"],
            "divulgacao": DIVULGACAO,
            "n": f["n"],
            "municipios": f["municipios"],
            "margem_pp": f["margem_pp"],
            "relatorio_pdf": None,
            "relatorio_pdf_status": (
                "Sem PDF estadual publicado até a captura de 03/10/2026: a matéria "
                "do Datafolha não traz link para media.folha.uol.com.br e a página "
                "de eleições do instituto lista só a íntegra nacional."
            ),
            "painel": {**painel, "pagina_id": f["pid"]},
            "api": api,
            "materia_datafolha": materia,
            "materia_folha_resumo": "data/originals/estaduais_102026_03/comum/materia_folha_resumo.html",
        }
        (pasta / "fonte.json").write_text(
            json.dumps(fonte, ensure_ascii=False, indent=2) + "\n"
        )


def confere(fonte):
    for item in [fonte["painel"], fonte["materia_datafolha"], *fonte["api"].values()]:
        path = ROOT / item["arquivo"]
        if sha256(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ValueError(f"Hash divergente: {item['arquivo']}")


def ultima_coluna(path, codigo):
    resultado = json.loads(path.read_text())["resultado"]
    total = resultado["cenarios"][0]
    if total["titulo_visualizado"] != "Total" or total["pergunta"]["codigo"] != codigo:
        raise ValueError(f"Cenário inesperado em {path}")
    valores = {}
    for serie in total["data"]:
        pontos = serie.get("values") or [serie]
        for p in pontos:
            if p["date"][:10] == DATA_PAINEL:
                chave = NOMES[serie["option"]]
                valores[chave] = round(p["value"] * 100)
    if not {"Lula", "Flávio", "Branco/nulo", "Indecisos"} <= valores.keys():
        raise ValueError(f"Coluna {DATA_PAINEL} incompleta em {path}")
    if abs(sum(valores.values()) - 100) > 3:
        raise ValueError(f"Partição fora da tolerância em {path}")
    return valores


def readme(uf, f, v1, v2):
    return f"""# Datafolha · Presidência em {uf} · campo {f["campo"].replace("-", "/")}

Registros {f["registro_tse_estadual"]} e {f["registro_tse"]}, {f["n"]} entrevistas presenciais, margem de {f["margem_pp"]} pontos, contratada pela Folha de S.Paulo e pela TV Globo. Voto presidencial estadual divulgado em 02/10/2026.

**Sem PDF estadual** na captura de 03/10/2026. Os placares vêm da API pública do painel do G1 (coluna {DATA_PAINEL}, cenário Total); a ficha vem da matéria do Datafolha.

- `g1_1t.json`: 1º turno estimulado (`ESTIMULADA-PRE-002`). Lula {v1["Lula"]}, Flávio {v1["Flávio"]}.
- `g1_2t.json`: Lula × Flávio (`SEGTURNO-PRE-001`). Lula {v2["Lula"]}, Flávio {v2["Flávio"]}.
- `g1_painel.html`: página do painel, com o `paginaId` {f["pid"]} e os códigos das perguntas.
- `materia_datafolha.html`: matéria do instituto com campo, n e registros.

URLs, bytes, SHA-256 e hora da captura em `fonte.json`. Transcrição em `analysis/predicao_2026/estaduais/datafolha_{uf}_{f["campo"][-10:].replace("-", "")}.json`, gerada por `scripts/predicao-2026-estaduais-vespera.py`.
"""


def transcrever():
    resumo = texto(ARQ / "comum/materia_folha_resumo.html")
    if "de 28 de setembro a 1º de outubro de 2026" not in resumo:
        raise ValueError("Matéria-resumo da Folha mudou")
    saida = []
    for uf, f in UFS.items():
        pasta = ARQ / f"datafolha_{uf}"
        fonte = json.loads((pasta / "fonte.json").read_text())
        confere(fonte)
        materia = texto(ROOT / fonte["materia_datafolha"]["arquivo"])
        for frase in f["prova"]:
            if frase not in materia:
                raise ValueError(f"{uf}: ficha não encontrada na matéria: {frase}")
        if f'paginaId: "{f["pid"]}"' not in (pasta / "g1_painel.html").read_text():
            raise ValueError(f"{uf}: paginaId do painel divergente")
        v1 = ultima_coluna(ROOT / fonte["api"]["1t"]["arquivo"], PERGUNTAS["1t"])
        v2 = ultima_coluna(ROOT / fonte["api"]["2t"]["arquivo"], PERGUNTAS["2t"])
        publicados, frase = VALIDOS[uf]
        if frase not in resumo:
            raise ValueError(f"{uf}: votos válidos não encontrados na matéria-resumo")
        validos = sum(v for k, v in v1.items() if k not in ("Branco/nulo", "Indecisos"))
        controle = {
            "fonte": RESUMO,
            "publicados": publicados,
            "recompostos": {k: round(100 * v1[k] / validos, 2) for k in publicados},
        }
        if any(
            abs(controle["recompostos"][k] - publicados[k]) > 1.5 for k in publicados
        ):
            raise ValueError(f"{uf}: painel não recompõe os válidos publicados")
        fim = f["campo"][-10:].replace("-", "")
        doc = {
            "instituto": "Datafolha",
            "uf": uf,
            "registro_tse": f["registro_tse"],
            "registro_tse_estadual": f["registro_tse_estadual"],
            "campo": f["campo"],
            "divulgacao": DIVULGACAO,
            "divulgacao_tipo": "matéria do Datafolha e da Folha (contratante), 02/10/2026; placares no painel do G1, sem PDF",
            "n": f["n"],
            "municipios": f["municipios"],
            "margem_pp": f["margem_pp"],
            "metodo": "Entrevistas presenciais com eleitores de 16 anos ou mais (matéria do Datafolha).",
            "contratante": "Folha de S.Paulo e TV Globo",
            "url": fonte["api"]["1t"]["url"],
            "url_painel": fonte["painel"]["url"],
            "url_materia": [f["materia"], RESUMO],
            "arquivo": fonte["api"]["1t"]["arquivo"],
            "sha256": fonte["api"]["1t"]["sha256"],
            "fonte_json": str((pasta / "fonte.json").relative_to(ROOT)),
            "pres_1t": {"pagina": fonte["api"]["1t"]["url"], "valores": v1},
            "controle_validos": controle,
            "pres_2t": {
                "pagina": fonte["api"]["2t"]["url"],
                "arquivo": fonte["api"]["2t"]["arquivo"],
                "sha256": fonte["api"]["2t"]["sha256"],
                "cenarios": [v2],
            },
            "notas": [
                f"Coluna {DATA_PAINEL} do painel do G1 (cenário Total), em fração arredondada ao inteiro percentual; 0 é valor publicado no painel.",
                "Leonardo Avalanche não consta do cartão do painel; a célula fica ausente, não zero.",
                "Sem PDF estadual: campo, n, municípios e registros vêm da matéria do Datafolha, conferidos literalmente no HTML arquivado.",
                "A matéria-resumo da Folha atribui às cinco UFs o campo de 28/09 a 01/10; a matéria do Datafolha de cada UF é a referência por ser a do instituto.",
                "Painel sem cruzamento por hábito de comparecimento; sem comparecimento_compacto.",
            ],
        }
        (pasta / "README.md").write_text(readme(uf, f, v1, v2))
        nome = OUT / f"datafolha_{uf}_{fim}.json"
        nome.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        saida.append((uf, f["campo"], f["n"], v1["Lula"], v1["Flávio"], v2))
    for linha in saida:
        print(*linha)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--capturar", action="store_true", help="baixa e arquiva as fontes")
    args = ap.parse_args()
    if args.capturar:
        capturar()
    transcrever()


if __name__ == "__main__":
    main()
