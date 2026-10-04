#!/usr/bin/env python3
"""Integra as ondas finais da AtlasIntel (campo 27/09 a 02/10/2026).

Os relatórios são imagem: os números abaixo foram lidos página a página em
renderizações de 200 a 300 dpi (as de 130 dpi ficam em
``analysis/predicao_2026/atualizacao_20261004/atlas/``). O script não digita
nada além dessas tabelas: confere hashes, somas e a partição de "Outros" com
o rodapé de cada página, grava ``fonte.json`` e ``README.md`` de cada pacote e
as fichas estaduais lidas por ``scripts/predicao_2026/base.py``.

Uso: ``python3 scripts/atlas-102026-integrar.py``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
NACIONAL = ROOT / "data/originals/atlas_102026_04"
ESTADUAIS = ROOT / "data/originals/atlas_estaduais_102026_04"
FICHAS = ROOT / "analysis/predicao_2026/estaduais"
RENDER = "analysis/predicao_2026/atualizacao_20261004/atlas"
CAMPO = "2026-09-27 a 2026-10-02"
DIVULGACAO = "2026-10-03"
CONFERIDO = "2026-10-04"
CDN = "https://cdn1.atlasintel.org/"
SITE = "https://atlasintel.org/poll/"

NAC = {
    "url": CDN + "pesquisa_atlas_bloomberg__nacional_261003_1_2c124be0d65430b5.pdf",
    "pagina_instituto": SITE + "brazil-national-2026-10-03",
    "registro_tse": "BR-00999/2026",
    "n": 4945,
    "paginas": {
        "perfil_amostra": 5,
        "1t_topline": 14,
        "1t_validos": 15,
        "1t_serie": 16,
        "1t_cruzamentos": 17,
        "2t_topline": 19,
        "2t_validos": 20,
        "2t_serie": 21,
    },
}

# Uma linha por UF: arquivo no CDN, página do instituto, registros (p. 5),
# n (p. 5), parceiro impresso, páginas e placares. "outros" reparte a barra
# "Outros" pelo rodapé da mesma página; "nao_pontuaram" vem do mesmo rodapé.
UFS: dict[str, dict] = {
    "AC": {
        "pdf": "pesquisa_atlas__eleicoes_acre_2026_261003_3c685f199202964d.pdf",
        "slug": "brazil-acre-pesquisa-atlas-2026-10-03",
        "br": "BR-02212/2026",
        "uf": "AC-00679/2026",
        "n": 836,
        "margem": "3 p.p., 95%",
        "parceiro": None,
        "p1": 27,
        "p2": 32,
        "t1": {
            "Flávio": 59.7,
            "Lula": 29.0,
            "Cury": 3.7,
            "Caiado": 2.3,
            "Renan": 0.9,
            "Samara": 0.5,
            "Zema": 0.4,
            "Pimenta": 0.0,
            "Branco/nulo": 2.1,
            "Indecisos": 1.4,
        },
        "barra_outros": None,
        "outros": {},
        "nao_pontuaram": [],
        "t2": {"Flávio": 64.2, "Lula": 31.7, "Branco/nulo": 4.1},
        "anterior": None,
    },
    "ES": {
        "pdf": "pesquisa_atlas__eleicoes_espirito_santo_2026__261003_990b45cf157d3409.pdf",
        "slug": "brazil-espirito-santo-2026-10-03",
        "br": "BR-02089/2026",
        "uf": "ES-01573/2026",
        "n": 1226,
        "margem": "±3 p.p., 95%",
        "parceiro": None,
        "p1": 21,
        "p2": 26,
        "t1": {
            "Flávio": 48.8,
            "Lula": 34.4,
            "Renan": 6.2,
            "Caiado": 2.9,
            "Cury": 2.3,
            "Branco/nulo": 2.9,
            "Indecisos": 1.3,
        },
        "barra_outros": 1.2,
        "outros": {"Zema": 0.5, "Clariana": 0.4, "Samara": 0.3},
        "nao_pontuaram": ["Grassi", "Pimenta", "Hertz", "Edmilson"],
        "t2": {"Flávio": 51.7, "Lula": 39.2, "Branco/nulo": 9.1},
        "anterior": "analysis/voto_util/outros/atlasintel_ES_20260831.json",
    },
    "GO": {
        "pdf": "pesquisa_atlas__eleicoes_goias_2026__261003_48680e1775c298f2.pdf",
        "slug": "brazil-goias-2026-10-03",
        "br": "BR-02318/2026",
        "uf": "GO-03367/2026",
        "n": 1198,
        "margem": "±3 p.p., 95%",
        "parceiro": None,
        "p1": 25,
        "p2": 30,
        "t1": {
            "Flávio": 47.7,
            "Lula": 33.2,
            "Caiado": 10.7,
            "Renan": 4.8,
            "Cury": 2.9,
            "Branco/nulo": 0.2,
            "Indecisos": 0.4,
        },
        "barra_outros": 0.0,
        "outros": {"Clariana": 0.0, "Hertz": 0.0},
        "nao_pontuaram": [
            "Zema",
            "Edmilson",
            "Pimenta",
            "Samara",
            "Avalanche",
            "Grassi",
        ],
        "t2": {"Flávio": 53.5, "Lula": 38.5, "Branco/nulo": 8.0},
        "anterior": "analysis/voto_util/outros/atlasintel_GO_20260901.json",
    },
    "MT": {
        "pdf": "pesquisa_atlas__eleicoes_mato_grosso_2026__261003_6c9e24b8c820dd44.pdf",
        "slug": "brazil-mato-grosso-2026-10-03",
        "br": "BR-02167/2026",
        "uf": "MT-00323/2026",
        "n": 1194,
        "margem": "3 p.p., 95%",
        "parceiro": None,
        "p1": 24,
        "p2": 29,
        "t1": {
            "Flávio": 61.0,
            "Lula": 30.7,
            "Cury": 3.4,
            "Renan": 2.9,
            "Caiado": 0.7,
            "Zema": 0.3,
            "Branco/nulo": 0.7,
            "Indecisos": 0.0,
        },
        "barra_outros": 0.3,
        "outros": {"Samara": 0.2, "Clariana": 0.1, "Edmilson": 0.0, "Hertz": 0.0},
        "nao_pontuaram": [],
        "t2": {"Flávio": 63.6, "Lula": 32.8, "Branco/nulo": 3.5},
        "anterior": "analysis/voto_util/outros/atlasintel_MT_20260909.json",
    },
    "MS": {
        "pdf": "pesquisa_atlas__eleicoes_mato_grosso_do_sul_2026__261003_e4d7cb11c9340c6d.pdf",
        "slug": "brazil-mato-grosso-do-sul-2026-10-03",
        "br": "BR-07964/2026",
        "uf": "MS-05642/2026",
        "n": 1211,
        "margem": "±3 p.p., 95%",
        "parceiro": "Estadão (cabeçalho textual da p. 5: PESQUISA ATLAS/ESTADÃO)",
        "p1": 25,
        "p2": 30,
        "t1": {
            "Flávio": 53.2,
            "Lula": 37.2,
            "Cury": 4.2,
            "Renan": 1.8,
            "Caiado": 1.7,
            "Zema": 0.3,
            "Branco/nulo": 0.7,
            "Indecisos": 0.6,
        },
        "barra_outros": 0.2,
        "outros": {"Samara": 0.2, "Hertz": 0.0, "Pimenta": 0.0},
        "nao_pontuaram": [],
        "t2": {"Flávio": 55.3, "Lula": 39.3, "Branco/nulo": 5.4},
        "anterior": "analysis/voto_util/outros/atlasintel_MS_20260901.json",
    },
    "PA": {
        "pdf": "pesquisa_atlas__eleicoes_para_2026_261003_73d3d84100fa7c48.pdf",
        "slug": "brazil-para-2026-10-03",
        "br": "BR-07727/2026",
        "uf": "PA-06872/2026",
        "n": 1206,
        "margem": "±3 p.p., 95%",
        "parceiro": None,
        "p1": 23,
        "p2": 27,
        "t1": {
            "Lula": 50.6,
            "Flávio": 40.6,
            "Cury": 5.0,
            "Renan": 1.1,
            "Branco/nulo": 0.5,
            "Indecisos": 1.1,
        },
        "barra_outros": 1.0,
        "outros": {
            "Caiado": 0.8,
            "Zema": 0.2,
            "Samara": 0.0,
            "Pimenta": 0.0,
            "Clariana": 0.0,
        },
        "nao_pontuaram": [],
        "t2": {"Lula": 53.1, "Flávio": 43.8, "Branco/nulo": 3.0},
        "anterior": None,
    },
    "BA": {
        "pdf": "pesquisa_atlas_atarde__eleicoes_bahia_2026__261003_bbda22d478a4743d.pdf",
        "slug": "brazil-bahia-pesquisa-atlas-a-tarde-2026-10-03",
        "br": "BR-01177/2026",
        "uf": "BA-05671/2026",
        "n": 2199,
        "margem": "±2 p.p., 95%",
        "parceiro": "A Tarde (logo no cabeçalho)",
        "p1": 26,
        "p2": 31,
        "t1": {
            "Lula": 59.1,
            "Flávio": 29.2,
            "Caiado": 3.9,
            "Cury": 3.0,
            "Renan": 1.9,
            "Branco/nulo": 1.2,
            "Indecisos": 1.0,
        },
        "barra_outros": 0.6,
        "outros": {
            "Clariana": 0.6,
            "Pimenta": 0.0,
            "Samara": 0.0,
            "Grassi": 0.0,
            "Zema": 0.0,
        },
        "nao_pontuaram": [],
        "t2": {"Lula": 61.6, "Flávio": 34.3, "Branco/nulo": 2.6, "Indecisos": 1.5},
        "anterior": "analysis/voto_util/outros/atlasintel_BA_20260902.json",
    },
    "RJ": {
        "pdf": "pesquisa_atlas_estadao__eleicoes_rio_de_janeiro_2026__261003_c8af612fe782f5a9.pdf",
        "slug": "brazil-rio-de-janeiro-pesquisa-atlasestadao-2026-10-03",
        "br": "BR-02842/2026",
        "uf": "RJ-02601/2026",
        "n": 2244,
        "margem": "±2 p.p., 95%",
        "parceiro": "Estadão (logo no cabeçalho)",
        "p1": 24,
        "p2": 29,
        "t1": {
            "Flávio": 46.6,
            "Lula": 43.5,
            "Renan": 4.1,
            "Caiado": 1.9,
            "Cury": 1.4,
            "Branco/nulo": 1.5,
            "Indecisos": 0.4,
        },
        "barra_outros": 0.6,
        "outros": {
            "Samara": 0.2,
            "Zema": 0.2,
            "Hertz": 0.1,
            "Pimenta": 0.1,
            "Edmilson": 0.0,
        },
        "nao_pontuaram": [],
        "t2": {"Flávio": 48.7, "Lula": 46.4, "Branco/nulo": 4.9},
        "anterior": "analysis/voto_util/outros/atlasintel_RJ_20260920.json",
    },
    "SP": {
        "pdf": "pesquisa_atlas_estadao__eleicoes_sao_paulo_2026__261003_7480fedfda9e694f.pdf",
        "slug": "brazil-sao-paulo-pesquisa-atlasestadao-2026-10-03",
        "br": "BR-08300/2026",
        "uf": "SP-06906/2026",
        "n": 2243,
        "margem": "±2 p.p., 95%",
        "parceiro": "Estadão (cabeçalho textual e logo)",
        "p1": 25,
        "p2": 30,
        "t1": {
            "Flávio": 46.3,
            "Lula": 42.0,
            "Renan": 6.5,
            "Cury": 1.7,
            "Caiado": 1.4,
            "Branco/nulo": 0.3,
            "Indecisos": 0.7,
        },
        "barra_outros": 0.9,
        "outros": {
            "Zema": 0.5,
            "Avalanche": 0.3,
            "Hertz": 0.1,
            "Edmilson": 0.0,
            "Pimenta": 0.0,
            "Samara": 0.0,
        },
        "nao_pontuaram": [],
        "t2": {"Flávio": 49.6, "Lula": 42.9, "Branco/nulo": 7.5},
        "anterior": "analysis/voto_util/outros/atlasintel_SP_20260920.json",
    },
    "CE": {
        "pdf": "pesquisa_atlas_focus__eleicoes_ceara_2026__261003_77dad3caef63e1c9.pdf",
        "slug": "brazil-ceara-pesquisa-atlasfocus-2026-10-03",
        "br": "BR-09756/2026",
        "uf": "CE-01031/2026",
        "n": 2227,
        "margem": "±2 p.p., 95%",
        "parceiro": "Focus Poder (cabeçalho textual e logo)",
        "p1": 26,
        "p2": 31,
        "t1": {
            "Lula": 60.8,
            "Flávio": 28.9,
            "Cury": 3.9,
            "Renan": 3.4,
            "Branco/nulo": 1.1,
            "Indecisos": 0.3,
        },
        "barra_outros": 1.7,
        "outros": {"Caiado": 1.5, "Zema": 0.1, "Samara": 0.1},
        "nao_pontuaram": ["Grassi", "Edmilson", "Hertz", "Clariana", "Pimenta"],
        "t2": {"Lula": 63.2, "Flávio": 31.8, "Branco/nulo": 4.9},
        "anterior": "analysis/voto_util/outros/atlasintel_CE_20260920.json",
    },
    "PI": {
        "pdf": "pesquisa_atlas_meionorte__piaui__eleicoes_2026_261003_8d805ba05c5d32d1.pdf",
        "slug": "brazil-piaui-pesquisa-atlasmeio-norte-2026-10-03",
        "br": "BR-06245/2026",
        "uf": "PI-03386/2026",
        "n": 1230,
        "margem": "±3 p.p., 95%",
        "parceiro": "Meio Norte (logo no cabeçalho)",
        "p1": 20,
        "p2": 25,
        "t1": {
            "Lula": 66.4,
            "Flávio": 26.9,
            "Renan": 2.1,
            "Cury": 1.4,
            "Caiado": 0.9,
            "Branco/nulo": 0.7,
            "Indecisos": 1.5,
        },
        "barra_outros": 0.1,
        "outros": {"Zema": 0.0, "Hertz": 0.1, "Avalanche": 0.0, "Samara": 0.0},
        "nao_pontuaram": [],
        "t2": {"Lula": 68.3, "Flávio": 28.4, "Branco/nulo": 2.7, "Indecisos": 0.6},
        "anterior": "analysis/voto_util/outros/atlasintel_PI_20260902.json",
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def pdf_meta(path: Path) -> dict:
    doc = fitz.open(path)
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "paginas": doc.page_count,
        "creationDate": doc.metadata.get("creationDate") or None,
        "producer": doc.metadata.get("creator") or None,
        "titulo_pdf": doc.metadata.get("title") or None,
    }


def page_text(path: Path, page: int) -> str:
    return " ".join(fitz.open(path)[page - 1].get_text().split())


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n")


def check_poll(uf: str, spec: dict, pdf: Path) -> dict:
    perfil = page_text(pdf, 5)
    for token in (spec["br"], spec["uf"], "27/09/2026-02/10/2026"):
        if token not in perfil:
            raise SystemExit(f"{uf}: {token} ausente da p. 5")
    if f"{spec['n']:,}".replace(",", ".") not in perfil:
        raise SystemExit(f"{uf}: n {spec['n']} ausente da p. 5")
    if "PRESIDEN" not in page_text(pdf, spec["p1"]).upper():
        raise SystemExit(f"{uf}: p. {spec['p1']} não é presidente 1º turno")
    if "segundo turno" not in page_text(pdf, spec["p2"]):
        raise SystemExit(f"{uf}: p. {spec['p2']} não é 2º turno")
    outros = spec["outros"]
    if (
        spec["barra_outros"] is not None
        and abs(sum(outros.values()) - spec["barra_outros"]) > 0.05
    ):
        raise SystemExit(f"{uf}: rodapé de Outros não fecha a barra")
    valores = {**spec["t1"], **outros}
    soma1 = round(sum(valores.values()), 1)
    soma2 = round(sum(spec["t2"].values()), 1)
    if abs(soma1 - 100) > 0.25 or abs(soma2 - 100) > 0.15:
        raise SystemExit(f"{uf}: soma fora do arredondamento ({soma1}, {soma2})")
    return {"valores": valores, "soma1": soma1, "soma2": soma2}


def state_package(uf: str, spec: dict) -> dict:
    folder = ESTADUAIS / uf
    pdf = folder / "relatorio.pdf"
    meta = pdf_meta(pdf)
    if meta["sha256"] != sha256(pdf):
        raise SystemExit(f"{uf}: hash instável")
    checked = check_poll(uf, spec, pdf)
    url = CDN + spec["pdf"]
    fonte = {
        "instituto": "AtlasIntel",
        "uf": uf,
        "registro_tse": spec["br"],
        "registro_tse_estadual": spec["uf"],
        "campo": CAMPO,
        "divulgacao": DIVULGACAO,
        "n": spec["n"],
        "baixado_em": CONFERIDO,
        "url": url,
        "pagina_instituto": SITE + spec["slug"],
        "arquivo": rel(pdf),
        **meta,
        "creationDate_nota": "Metadado creator Google e creationDate vazio; a data de divulgação vem do cartão 03.10.2026 da página do instituto.",
        "paginas_conteudo": {
            "perfil_amostra": 5,
            "presidente_1t": spec["p1"],
            "presidente_2t": spec["p2"],
        },
        "renderizacoes": f"{RENDER}/{uf}_pNN.png",
    }
    write_json(folder / "fonte.json", fonte)
    (folder / "README.md").write_text(
        f"# AtlasIntel {uf}, onda final de 27/09 a 02/10/2026\n\n"
        f"Relatório estadual da AtlasIntel ({spec['br']}, {spec['uf']}), "
        f"{spec['n']} entrevistas por recrutamento digital aleatório, campo de "
        "27/09 a 02/10/2026, publicado na página do instituto em 03/10/2026. "
        f"PDF original em `relatorio.pdf`, texto nativo em `relatorio.txt`. "
        f"O relatório é imagem: o 1º turno presidencial está na p. {spec['p1']} "
        f"e o 2º turno Lula contra Flávio na p. {spec['p2']}; renderizações em "
        f"`{RENDER}/`. URL, bytes e SHA-256 em `fonte.json`. Ficha da previsão: "
        f"`analysis/predicao_2026/estaduais/atlasintel_{uf}_20261002.json`.\n"
    )
    t2 = dict(spec["t2"])
    juntos = "Indecisos" not in t2
    if juntos:
        t2["Indecisos"] = None
    nota2 = (
        "O gráfico agrega 'Branco / Nulo / Não sei' numa só barra: gravada em "
        "Branco/nulo como a casa publica; Indecisos = null (não separado)."
        if juntos
        else "Nesta UF o gráfico separa 'Voto branco/nulo' e 'Não sei'."
    )
    ficha = {
        "instituto": "AtlasIntel",
        "uf": uf,
        "registro_tse": spec["br"],
        "registro_tse_estadual": spec["uf"],
        "campo": CAMPO,
        "divulgacao": DIVULGACAO,
        "divulgacao_tipo": "cartão de 03.10.2026 na página de pesquisas da AtlasIntel, com o PDF",
        "n": spec["n"],
        "margem": spec["margem"],
        "metodo": "Recrutamento digital aleatório (Atlas RDR)",
        "parceiro_midia": spec["parceiro"],
        "url": url,
        "url_pdf": url,
        "pagina_instituto": SITE + spec["slug"],
        "arquivo": rel(pdf),
        "fonte_json": rel(folder / "fonte.json"),
        "sha256_pdf": meta["sha256"],
        "bytes": meta["bytes"],
        "pres_1t": {
            "pagina": spec["p1"],
            "valores": checked["valores"],
            "soma": checked["soma1"],
            "barra_outros": spec["barra_outros"],
            "nao_pontuaram": spec["nao_pontuaram"],
            "nota": "Uma casa decimal, como impressa. 'Voto branco/nulo' = Branco/nulo e 'Não sei' = Indecisos, separados no 1º turno. A barra 'Outros' foi repartida pelo rodapé da mesma página, que imprime cada nome com o seu valor; os nomes que 'não pontuaram' ficam fora do vetor.",
        },
        "pres_2t": {
            "pagina": spec["p2"],
            "cenarios": [{**t2, "pagina": spec["p2"], "soma": checked["soma2"]}],
            "nota": nota2,
        },
        "substitui": spec["anterior"],
        "notas": [
            f"Relatório em imagem: números lidos página a página em renderização de 200 dpi; cópias de 130 dpi em {RENDER}/.",
            "registro_tse = registro nacional (BR); registro_tse_estadual = registro do estado; ambos na p. 5, com período 27/09/2026-02/10/2026.",
            "Os cruzamentos demográficos do relatório não trazem hábito de comparecimento; sem comparecimento_compacto.",
            "Onda final antes do 1º turno; base.state_polls mantém a mais recente por casa e UF.",
        ],
    }
    write_json(FICHAS / f"atlasintel_{uf}_20261002.json", ficha)
    return ficha


def national_package() -> None:
    pdf = NACIONAL / "relatorio.pdf"
    perfil = page_text(pdf, 5)
    for token in (NAC["registro_tse"], "4.945", "27/09/2026-02/10/2026"):
        if token not in perfil:
            raise SystemExit(f"nacional: {token} ausente da p. 5")
    fonte = {
        "instituto": "AtlasIntel",
        "contratante": "Bloomberg",
        "registro_tse": NAC["registro_tse"],
        "campo": CAMPO,
        "divulgacao": DIVULGACAO,
        "n": NAC["n"],
        "baixado_em": CONFERIDO,
        "url": NAC["url"],
        "pagina_instituto": NAC["pagina_instituto"],
        "arquivo": rel(pdf),
        **pdf_meta(pdf),
        "creationDate_nota": "Metadado creator Google e creationDate vazio; a data de divulgação vem do cartão 03.10.2026 da página do instituto.",
        "paginas_conteudo": NAC["paginas"],
        "renderizacoes": f"{RENDER}/nacional_pNN.png",
        "localizacao": "A listagem de pesquisas exclusivas ainda mostrava a onda de 23 a 28/09; o cartão da onda final aparece na página própria e na aba Latam Pulse do mesmo site.",
    }
    write_json(NACIONAL / "fonte.json", fonte)
    (NACIONAL / "README.md").write_text(
        "# AtlasIntel nacional final, BR-00999/2026\n\n"
        "Pesquisa Atlas/Bloomberg, 4.945 entrevistas por recrutamento digital "
        "aleatório, campo de 27/09 a 02/10/2026, publicada em 03/10/2026. PDF em "
        "`relatorio.pdf` e texto nativo em `relatorio.txt`; o relatório é imagem. "
        "Perfil de renda na p. 5 (20,0/12,0/24,0/26,6/17,4), 1º turno na p. 14, "
        "cruzamentos do 1º turno na p. 17 (renda, sexo e região) e 2º turno na "
        "p. 19, sem cruzamento por renda. Renderizações em "
        f"`{RENDER}/`. Ficha do agregador: "
        "`analysis/reponderacao/pesquisas/atlas_2026-10-02.json`.\n"
    )


def main() -> None:
    national_package()
    for uf, spec in UFS.items():
        ficha = state_package(uf, spec)
        print(
            uf,
            ficha["pres_1t"]["valores"]["Lula"],
            ficha["pres_1t"]["valores"]["Flávio"],
            ficha["pres_2t"]["cenarios"][0]["Lula"],
            ficha["pres_2t"]["cenarios"][0]["Flávio"],
        )


if __name__ == "__main__":
    main()
