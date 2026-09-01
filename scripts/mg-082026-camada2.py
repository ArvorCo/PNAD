"""Segunda camada do atlas de Minas: carregadores, corredores e pauta regional.

Le a base municipal ja derivada por scripts/mg-082026-data.py e a votacao nominal
de 2022 do TSE, e escreve:
  docs/assets/mg_082026_camada2.json
  data/pesquisas/estaduais/mg/2026-08/derivados/carregadores-municipais.csv
  data/pesquisas/estaduais/mg/2026-08/derivados/corredores.csv

Reproducao:
    python3 scripts/mg-082026-camada2.py
"""

from __future__ import annotations

import csv
import io
import json
import sys
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(sys.maxsize)

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data/pesquisas/estaduais/mg/2026-08/derivados"
ASSETS = ROOT / "docs/assets"
TSE_ZIP = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"

CARGOS_NOMINAIS = {"SENADOR", "DEPUTADO FEDERAL", "DEPUTADO ESTADUAL"}
CHAVES = [
    ("SENADOR", "CLEITINHO"),
    ("DEPUTADO FEDERAL", "NIKOLAS FERREIRA"),
    ("DEPUTADO ESTADUAL", "BRUNO ENGLER"),
]
NUCLEO = {
    "PL",
    "PP",
    "REPUBLICANOS",
    "NOVO",
    "UNIAO",
    "PRD",
    "PODE",
    "PATRIOTA",
    "PRTB",
    "DC",
}
DIREITA_AMPLA = NUCLEO | {
    "PSDB",
    "PSD",
    "MDB",
    "AVANTE",
    "SOLIDARIEDADE",
    "PSC",
    "PTB",
    "AGIR",
    "PMB",
    "MOBILIZA",
}


def norm(value: str) -> str:
    txt = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    txt = "".join(ch if ch.isalnum() else " " for ch in txt)
    return " ".join(txt.upper().split())


# ----------------------------------------------------------------------------- extracao


def extrai_nominal_mg() -> None:
    """Agrega a votacao nominal de MG por municipio, se ainda nao houver cache."""
    alvo = DERIVED / "chaves_2022_por_municipio.csv"
    perfil = DERIVED / "candidatos_2022_perfil_territorial.csv"
    if alvo.exists() and perfil.exists():
        return
    if not TSE_ZIP.exists():
        raise SystemExit(
            f"faltando {TSE_ZIP}; rode brasil ibge-sync ou baixe o ZIP do TSE"
        )

    master = {
        norm(r["municipio"]): r
        for r in csv.DictReader((DERIVED / "municipios.csv").open(encoding="utf-8"))
    }
    votos: dict[tuple, int] = defaultdict(int)
    por_cidade: dict[tuple, dict[str, int]] = defaultdict(dict)
    total_cidade: dict[tuple, int] = defaultdict(int)
    info: dict[str, tuple] = {}

    with (
        zipfile.ZipFile(TSE_ZIP) as z,
        z.open("votacao_candidato_munzona_2022_MG.csv") as raw,
    ):
        reader = csv.DictReader(
            io.TextIOWrapper(raw, encoding="latin-1", newline=""),
            delimiter=";",
            quotechar='"',
        )
        for row in reader:
            if row["NR_TURNO"] != "1":
                continue
            cargo = row["DS_CARGO"].strip().upper()
            if cargo not in CARGOS_NOMINAIS:
                continue
            cidade = norm(row["NM_MUNICIPIO"])
            if cidade not in master:
                continue
            sq = row["SQ_CANDIDATO"]
            v = int(row["QT_VOTOS_NOMINAIS_VALIDOS"] or 0)
            votos[(cargo, sq)] += v
            if v:
                por_cidade[(cargo, sq)][cidade] = (
                    por_cidade[(cargo, sq)].get(cidade, 0) + v
                )
            total_cidade[(cargo, cidade)] += v
            info.setdefault(
                sq,
                (
                    row["NM_URNA_CANDIDATO"].strip(),
                    row["SG_PARTIDO"].strip(),
                    row["DS_SIT_TOT_TURNO"].strip(),
                ),
            )

    # perfil territorial de cada candidatura relevante
    linhas = []
    for (cargo, sq), total in votos.items():
        if total < 3000:
            continue
        urna, partido, situacao = info[sq]
        cidades = por_cidade[(cargo, sq)]
        ranked = sorted(cidades.items(), key=lambda kv: -kv[1])
        meso: dict[str, int] = defaultdict(int)
        for cidade, v in cidades.items():
            meso[master[cidade]["mesorregiao"]] += v
        meso_top = max(meso.items(), key=lambda kv: kv[1])
        linhas.append(
            {
                "cargo": cargo,
                "nome_urna": urna,
                "partido": partido,
                "situacao": situacao,
                "eleito": situacao.upper().startswith("ELEITO"),
                "bloco": (
                    "nucleo_direita"
                    if partido in NUCLEO
                    else ("direita_ampla" if partido in DIREITA_AMPLA else "outros")
                ),
                "votos_mg": total,
                "top_municipio": ranked[0][0] if ranked else "",
                "top1_concentracao_pct": (
                    round(100 * ranked[0][1] / total, 2) if ranked else 0
                ),
                "mesorregiao_dominante": meso_top[0],
                "mesorregiao_dominante_pct": round(100 * meso_top[1] / total, 2),
            }
        )
    linhas.sort(key=lambda r: -r["votos_mg"])
    with perfil.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    detalhe = []
    for cargo, nome in CHAVES:
        for sq in [s for (c, s) in votos if c == cargo and norm(info[s][0]) == nome]:
            for cidade, v in por_cidade[(cargo, sq)].items():
                m = master[cidade]
                denom = total_cidade[(cargo, cidade)]
                detalhe.append(
                    {
                        "candidato": info[sq][0],
                        "cargo": cargo,
                        "partido": info[sq][1],
                        "codigo_ibge": m["codigo_ibge"],
                        "municipio": m["municipio"],
                        "mesorregiao": m["mesorregiao"],
                        "votos": v,
                        "pct_validos_cargo": round(100 * v / denom, 3) if denom else 0,
                    }
                )
    with alvo.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(detalhe[0].keys()))
        w.writeheader()
        w.writerows(detalhe)


# ----------------------------------------------------------------------------- base


def carrega() -> list[dict]:
    master = list(csv.DictReader((DERIVED / "municipios.csv").open(encoding="utf-8")))
    primeiro: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for r in csv.DictReader(
        (DERIVED / "votos-municipais-tse-2018-2022.csv").open(encoding="utf-8")
    ):
        if r["ano"] == "2022" and r["turno"] == "1" and r["cargo"] == "Presidente":
            primeiro[norm(r["municipio_norm"])][r["candidato"]] += int(r["votos"])
    chave: dict[str, dict[str, float]] = defaultdict(dict)
    for r in csv.DictReader(
        (DERIVED / "chaves_2022_por_municipio.csv").open(encoding="utf-8")
    ):
        chave[r["codigo_ibge"]][r["candidato"]] = float(r["pct_validos_cargo"])

    rows = []
    for m in master:
        d = primeiro.get(norm(m["municipio"]), {})
        tot = sum(d.values())
        c = chave.get(m["codigo_ibge"], {})
        rows.append(
            {
                "ibge": m["codigo_ibge"],
                "mun": m["municipio"],
                "meso": m["mesorregiao"],
                "inter": m["regiao_intermediaria"],
                "el": int(m["eleitores_2026"]),
                "renda": float(m["renda_pc_media_2022"] or 0),
                "atividade": m["atividade_principal_2021"],
                "bol1": (
                    round(100 * d.get("Jair Bolsonaro", 0) / tot, 2) if tot else 0.0
                ),
                "lul1": round(100 * d.get("Lula", 0) / tot, 2) if tot else 0.0,
                "bol2": round(100 - float(m["pres_2022_esquerda_pct_validos"]), 2),
                "marg": float(m["pres_2022_margem_esquerda_pp"]),
                "desl": float(m["pres_deslocamento_esquerda_pp"]),
                "virada": m["pres_virada"],
                "cleit": c.get("CLEITINHO", 0.0),
                "niko": c.get("NIKOLAS FERREIRA", 0.0),
                "engler": c.get("BRUNO ENGLER", 0.0),
            }
        )
    return rows


def aplica_indice(rows: list[dict]) -> dict:
    e = sum(r["el"] for r in rows)
    medias = {
        k: sum(r["el"] * r[k] for r in rows) / e
        for k in ("bol1", "bol2", "lul1", "cleit", "niko", "engler")
    }
    for r in rows:
        base = r["bol1"] / medias["bol1"] if r["bol1"] else 0
        for k, lbl in (("cleit", "iC"), ("niko", "iN"), ("engler", "iE")):
            r[lbl] = round(100 * (r[k] / medias[k]) / base, 1) if base else 0.0
        r["iTrio"] = round((r["iC"] + r["iN"] + r["iE"]) / 3, 1)
    return {k: round(v, 2) for k, v in medias.items()}


# ----------------------------------------------------------------------------- corredores

CORREDORES = [
    (
        "minerio",
        "Corredor do Minério",
        "Quadrilátero Ferrífero e Itabira",
        [
            "Itabira",
            "Nova Lima",
            "Ouro Preto",
            "Mariana",
            "Itabirito",
            "Brumadinho",
            "Sarzedo",
            "Santa Bárbara",
            "Barão de Cocais",
            "Congonhas",
            "Rio Piracicaba",
            "São Gonçalo do Rio Abaixo",
            "Catas Altas",
            "Itatiaiuçu",
            "Ouro Branco",
            "João Monlevade",
            "Conceição do Mato Dentro",
            "Raposos",
            "Caeté",
            "Nova Era",
        ],
    ),
    (
        "metropolitano",
        "Corredor Metropolitano",
        "volume, periferia e colar",
        [
            "Belo Horizonte",
            "Contagem",
            "Betim",
            "Ribeirão das Neves",
            "Santa Luzia",
            "Ibirité",
            "Sabará",
            "Vespasiano",
            "Esmeraldas",
            "Igarapé",
            "Juatuba",
            "Mateus Leme",
            "São Joaquim de Bicas",
            "Lagoa Santa",
            "Pedro Leopoldo",
            "Sete Lagoas",
            "São José da Lapa",
            "Confins",
            "Matozinhos",
        ],
    ),
    (
        "oeste",
        "Corredor Oeste",
        "o centro-oeste industrial",
        [
            "Divinópolis",
            "Nova Serrana",
            "Itaúna",
            "Formiga",
            "Arcos",
            "Oliveira",
            "Bom Despacho",
            "Lagoa da Prata",
            "Pará de Minas",
            "Campo Belo",
            "Santo Antônio do Monte",
            "Itapecerica",
            "Cláudio",
            "Perdigão",
            "Pains",
            "Bom Sucesso",
            "Carmo do Cajuru",
        ],
    ),
    (
        "aco",
        "Corredor do Aço e Rio Doce",
        "siderurgia e emprego formal",
        [
            "Ipatinga",
            "Coronel Fabriciano",
            "Timóteo",
            "Governador Valadares",
            "Caratinga",
            "Santana do Paraíso",
            "Mesquita",
            "Açucena",
            "Conselheiro Pena",
            "Mantena",
        ],
    ),
    (
        "mata",
        "Corredor da Mata e das Vertentes",
        "a maior virada do estado",
        [
            "Juiz de Fora",
            "Barbacena",
            "Muriaé",
            "Ubá",
            "Viçosa",
            "Cataguases",
            "São João del Rei",
            "Manhuaçu",
            "Ponte Nova",
            "Conselheiro Lafaiete",
            "Visconde do Rio Branco",
            "Além Paraíba",
            "Leopoldina",
            "Carangola",
            "Santos Dumont",
        ],
    ),
    (
        "producao",
        "Corredor da Produção",
        "Sul, Triângulo e Alto Paranaíba",
        [
            "Uberlândia",
            "Uberaba",
            "Varginha",
            "Pouso Alegre",
            "Poços de Caldas",
            "Patos de Minas",
            "Passos",
            "Araguari",
            "Ituiutaba",
            "Extrema",
            "Três Corações",
            "Itajubá",
            "Três Pontas",
            "Guaxupé",
            "Patrocínio",
            "Monte Carmelo",
            "Santa Rita do Sapucaí",
            "Alfenas",
            "Lavras",
            "São Sebastião do Paraíso",
            "Araxá",
            "Unaí",
            "Paracatu",
        ],
    ),
    (
        "vales",
        "Corredor dos Vales",
        "Norte, Jequitinhonha e Mucuri",
        [
            "Montes Claros",
            "Teófilo Otoni",
            "Januária",
            "Pirapora",
            "Janaúba",
            "Salinas",
            "Almenara",
            "Capelinha",
            "Diamantina",
            "Nanuque",
            "Curvelo",
            "Várzea da Palma",
            "São Francisco",
            "Jaíba",
            "Bocaiúva",
            "Araçuaí",
            "Itaobim",
            "Turmalina",
            "Minas Novas",
            "Rio Pardo de Minas",
        ],
    ),
]


def agrega(sel: list[dict], eleitorado_mg: int) -> dict:
    e = sum(r["el"] for r in sel)

    def w(k: str) -> float:
        return sum(r["el"] * r[k] for r in sel) / e

    return {
        "municipios": len(sel),
        "eleitores": e,
        "share_mg": round(100 * e / eleitorado_mg, 2),
        "bol1": round(w("bol1"), 2),
        "bol2": round(w("bol2"), 2),
        "lul1": round(w("lul1"), 2),
        "marg": round(w("marg"), 2),
        "desl": round(w("desl"), 2),
        "renda": round(w("renda")),
        "cleit": round(w("cleit"), 2),
        "niko": round(w("niko"), 2),
        "engler": round(w("engler"), 2),
        "iC": round(w("iC")),
        "iN": round(w("iN")),
        "iE": round(w("iE")),
        "viradas": sum(1 for r in sel if r["virada"] == "Direita→esquerda"),
        "disputados_5pp": sum(1 for r in sel if abs(r["marg"]) <= 5),
        "eleitores_disputados_5pp": sum(r["el"] for r in sel if abs(r["marg"]) <= 5),
    }


def ancoras(perfil: list[dict], meso: str, minimo: float = 45.0) -> list[dict]:
    sel = [
        r
        for r in perfil
        if r["eleito"] in ("True", True)
        and r["bloco"] in ("nucleo_direita", "direita_ampla")
        and r["mesorregiao_dominante"] == meso
        and float(r["mesorregiao_dominante_pct"]) >= minimo
        and r["cargo"] in ("DEPUTADO FEDERAL", "DEPUTADO ESTADUAL")
    ]
    sel.sort(key=lambda r: -int(r["votos_mg"]))
    return [
        {
            "nome": r["nome_urna"],
            "partido": r["partido"],
            "casa": "federal" if r["cargo"] == "DEPUTADO FEDERAL" else "estadual",
            "votos_mg": int(r["votos_mg"]),
            "concentracao_meso_pct": float(r["mesorregiao_dominante_pct"]),
            "base": r["top_municipio"].title(),
        }
        for r in sel[:6]
    ]


def bh_por_zona() -> list[dict]:
    """Le a votacao de BH por zona eleitoral, ja extraida em derivados."""
    caminho = DERIVED / "mg_presidente_zona_2022.csv"
    if not caminho.exists():
        return []
    pres: dict[tuple, int] = defaultdict(int)
    for r in csv.DictReader(caminho.open(encoding="utf-8")):
        if r["municipio"].strip().upper() == "BELO HORIZONTE":
            pres[(r["zona"], r["turno"], r["candidato"])] += int(r["votos"])
    nominal: dict[tuple, int] = defaultdict(int)
    total: dict[tuple, int] = defaultdict(int)
    with (
        zipfile.ZipFile(TSE_ZIP) as z,
        z.open("votacao_candidato_munzona_2022_MG.csv") as raw,
    ):
        for r in csv.DictReader(
            io.TextIOWrapper(raw, encoding="latin-1", newline=""),
            delimiter=";",
            quotechar='"',
        ):
            if r["NM_MUNICIPIO"].strip().upper() != "BELO HORIZONTE":
                continue
            cargo = r["DS_CARGO"].strip().upper()
            if cargo not in CARGOS_NOMINAIS:
                continue
            z_, v = r["NR_ZONA"], int(r["QT_VOTOS_NOMINAIS_VALIDOS"] or 0)
            total[(z_, cargo)] += v
            nome = r["NM_URNA_CANDIDATO"].strip().upper()
            if (cargo, nome) in {(c, n) for c, n in CHAVES}:
                nominal[(z_, nome, cargo)] += v
    zonas = sorted({k[0] for k in total}, key=int)
    saida = []
    for z_ in zonas:
        p1 = {c: v for (zz, t, c), v in pres.items() if zz == z_ and t == "1"}
        b2 = pres.get((z_, "2", "JAIR BOLSONARO"), 0)
        l2 = pres.get((z_, "2", "LULA"), 0)
        if not p1 or not (b2 + l2):
            continue
        d = {
            "zona": z_,
            "validos_2t": b2 + l2,
            "bol1": round(100 * p1.get("JAIR BOLSONARO", 0) / sum(p1.values()), 2),
            "bol2": round(100 * b2 / (b2 + l2), 2),
        }
        for cargo, nome in CHAVES:
            d[nome.split()[0].title()] = round(
                100 * nominal.get((z_, nome, cargo), 0) / total[(z_, cargo)], 2
            )
        saida.append(d)
    v = sum(r["validos_2t"] for r in saida)
    med = {
        k: sum(r["validos_2t"] * r[k] for r in saida) / v
        for k in ("bol1", "Cleitinho", "Nikolas", "Bruno")
    }
    for r in saida:
        base = r["bol1"] / med["bol1"]
        for k, lbl in (("Cleitinho", "iC"), ("Nikolas", "iN"), ("Bruno", "iE")):
            r[lbl] = round(100 * (r[k] / med[k]) / base, 1)
    return sorted(saida, key=lambda r: -r["iE"])


# ----------------------------------------------------------------------------- pauta regional

PAUTA = {
    "minerio": {
        "agenda": "A conta da mineração. Não é debate ambiental abstrato: é crédito municipal com valor, devedor e prazo.",
        "palanque": "Flávio com Cleitinho, Nikolas e Engler juntos. É o único corredor de Minas onde os três rendem acima do topo da chapa ao mesmo tempo, e portanto o único onde a foto conjunta soma em vez de dividir.",
        "frase": "O minério sai daqui e a conta fica aqui.",
        "fatos": [
            (
                "A Agência Nacional de Mineração cobra da Vale R$ 17,7 bilhões de CFEM não recolhida entre novembro de 2017 e dezembro de 2022. Cerca de R$ 3,2 bilhões seriam repassados a municípios mineiros.",
                "Diário do Comércio",
                "https://diariodocomercio.com.br/geral/vale-pode-pagar-r-32-bilhoes-a-municipios-de-mg-apos-cobranca-de-royalties/",
            ),
            (
                "Itabira aparece com a maior estimativa individual, R$ 822,6 milhões, seguida de Nova Lima com R$ 460,8 milhões e Mariana com R$ 449,4 milhões.",
                "O Fator",
                "https://ofator.com.br/informacao/os-municipios-de-minas-que-podem-receber-r-32-bilhoes-da-vale/",
            ),
            (
                "No primeiro semestre de 2026 Minas acumulou cerca de R$ 3,6 bilhões em royalties da mineração.",
                "Por Dentro de Minas",
                "https://pordentrodeminas.com.br/noticias/exposibram/2026/08/quanto-a-mineracao-movimenta-em-mg-veja-os-numeros/",
            ),
        ],
        "eventos": [
            "Audiência aberta de prefeitos e vereadores credores da CFEM, com o valor devido de cada município num painel atrás do palco. Formato de mesa, não de comício.",
            "Caminhada de romaria em Congonhas, no entorno da Basílica do Bom Jesus de Matosinhos, que é o maior ativo simbólico católico do corredor e fica numa cidade que trocou de lado em 2022.",
            "Visita curta a área de reassentamento em Brumadinho ou Barão de Cocais, com pauta de reparação e sem palanque montado.",
            "Motociata não cabe aqui. Cidade histórica, ladeira estreita e calçamento de pedra transformam a carreata em transtorno, e o ganho de imagem é menor que o atrito local.",
        ],
        "nao_dizer": "Não entrar como advogado da mineradora. Nestas cidades a empresa é empregadora e ré ao mesmo tempo, e a posição defensável é a do município credor: licenciamento mais rápido em troca de contrapartida cobrada e paga.",
        "juizo": "É o corredor de melhor relação entre esforço e voto do estado. Bolsonaro fez aqui bem menos que a média estadual, seis municípios trocaram de lado, e existe uma pauta material com valor, devedor e destinatário definidos.",
    },
    "metropolitano": {
        "agenda": "Serviço público e segurança. A pauta de costumes rende menos aqui que transporte, posto de saúde e policiamento de bairro.",
        "palanque": "Nikolas e Engler no comando, Flávio como convidado. Cleitinho rende abaixo da média neste corredor e não deve ser o rosto da operação metropolitana, ainda que lidere a disputa estadual.",
        "frase": "Aqui não falta discurso. Falta ônibus, posto e polícia.",
        "fatos": [
            (
                "Operação contra a liderança do PCC cumpriu 320 mandados em Minas e outros cinco estados em julho de 2026.",
                "Estado de Minas",
                "https://www.em.com.br/gerais/2026/07/7452592-operacao-contra-o-pcc-tem-320-alvos-em-minas-gerais-e-outros-cinco-estados.html",
            ),
            (
                "Documento atribuído a quatro organizações criminosas anunciou união em Minas, e a polícia passou a monitorar risco de confronto com grupo rival.",
                "CNN Brasil",
                "https://www.cnnbrasil.com.br/nacional/sudeste/mg/faccoes-anunciam-uniao-em-minas-e-policia-faz-monitoramento/",
            ),
            (
                "O novo campus da UFMG em Betim começa a funcionar no ano que vem.",
                "Rádio Itatiaia",
                "https://www.itatiaia.com.br/editorial/politica",
            ),
        ],
        "eventos": [
            "Motociata metropolitana ligando Contagem, Betim e Ibirité. É o formato de maior densidade de público por hora de agenda em todo o estado, e as três cidades ficaram dentro de cinco pontos ou perto disso em 2022.",
            "Caminhada de feira livre em Ribeirão das Neves, Santa Luzia e Vespasiano, em sábado de manhã, com Nikolas.",
            "Agenda de segurança com Engler em base comunitária do Barreiro e de Venda Nova, com comandante local presente.",
            "Culto e evento de igreja com Nikolas na periferia norte, onde o alcance digital dele já é maior e o custo de mobilização é o menor da região.",
        ],
        "nao_dizer": "Não tratar o colar metropolitano como extensão da capital. Renda, transporte e acesso à saúde funcionam de outro modo ali, e a fala que serve na Savassi não serve em Justinópolis.",
        "juizo": "Quase um quarto do eleitorado do estado, e o único lugar de Minas onde Nikolas e Engler valem mais que qualquer outro nome da direita mineira. É onde a campanha tem ativo próprio e não depende de aliança.",
    },
    "oeste": {
        "agenda": "Indústria leve e crédito. Calçado, confecção, fundição e siderurgia de pequeno porte.",
        "palanque": "Cleitinho abrindo e fechando, Flávio no meio. É a região natal dele e o único corredor onde o palanque estadual empurra o nacional em vez do contrário.",
        "frase": "Quem já votou aqui em quem fala como gente sabe reconhecer o resto.",
        "fatos": [
            (
                "O polo calçadista de Nova Serrana opera com cerca de 30% da capacidade instalada.",
                "Diário do Comércio",
                "https://diariodocomercio.com.br/economia/polo-calcadista-de-nova-serrana-opera-com-30-da-capacidade/",
            ),
            (
                "Divinópolis e Nova Serrana lideraram a geração de emprego da região no mês, enquanto Itaúna recuou.",
                "Portal Gerais",
                "https://portalgerais.com/divinopolis-e-nova-serrana-lideram-empregos-itauna-recua-em-agosto/",
            ),
            (
                "A FIEMG mantém programa de qualificação e oportunidades no eixo Nova Serrana, Divinópolis e Curvelo.",
                "FIEMG",
                "https://www.fiemg.com.br/fiemg/noticias/fiemg-oferece-oportunidades-em-nova-serrana-divinopolis-e-curvelo/",
            ),
        ],
        "eventos": [
            "Comício de praça em Divinópolis, onde Cleitinho fez quase vinte pontos a mais que Bolsonaro na mesma cédula de 2022.",
            "Chão de fábrica em Nova Serrana, que é a maior cidade mais bolsonarista de Minas e está com o polo calçadista muito abaixo da capacidade. Pauta de crédito, energia e importação.",
            "Cavalgada e comitiva no eixo Formiga, Arcos e Santo Antônio do Monte, onde a cultura de montaria é consolidada e o custo logístico é baixo.",
            "Motociata funciona bem em Divinópolis e Itaúna, com avenida larga e frota alta.",
        ],
        "nao_dizer": "Não pedir voto para presidente antes de entregar o palco ao senador. A ordem inversa reduz o efeito e expõe o saldo neutro do endosso presidencial medido pela Quaest.",
        "juizo": "O maior índice de Cleitinho no estado. A campanha ganha mais aqui organizando a foto conjunta do que gastando tempo de discurso próprio.",
    },
    "aco": {
        "agenda": "Importação de aço e energia. O eleitor conhece o número de fornos parados e percebe imprecisão.",
        "palanque": "Flávio com os deputados de base própria da região. Nenhum carregador estadual domina aqui, e o crédito local vale mais que o nome estadual.",
        "frase": "Quem fecha alto-forno não é ideologia. É importação sem regra.",
        "fatos": [
            (
                "A Usiminas desativou o alto-forno 1 e demitiu mais de cem pessoas na usina de Ipatinga sob pressão do aço importado.",
                "Diário do Comércio",
                "https://diariodocomercio.com.br/economia/usiminas-demite-ipatinga/",
            ),
            (
                "A siderurgia brasileira fechou 2025 com R$ 2,5 bilhões de investimento cancelado, 5,1 mil demissões e quatro altos-fornos parados.",
                "Diário do Comércio",
                "https://diariodocomercio.com.br/economia/siderurgia-importacoes-aco/",
            ),
            (
                "O tarifaço norte-americano de 25% poupou café e carne, mas atingiu aço e açúcar.",
                "Sul de Minas Online",
                "https://www.suldeminasonline.com.br/noticia/16405/geral/eua-impoem-tarifaco-de-25-a-produtos-brasileiros-cafe-e-carne-ficam-de-fora-mas-aco-e-acucar-sao-taxados.html",
            ),
        ],
        "eventos": [
            "Portaria de fábrica em Ipatinga e Timóteo na troca de turno. É o formato clássico da região e continua o mais eficiente.",
            "Duas reuniões separadas no mesmo dia, uma com o sindicato dos metalúrgicos e outra com o comércio local, com a mesma pauta de importação e energia.",
            "Motociata em Governador Valadares, que tem avenida larga, frota alta e é polo de sete regiões vizinhas.",
            "Café da manhã com pequena indústria em João Monlevade e Caratinga, onde o emprego formal depende da cadeia da usina.",
        ],
        "nao_dizer": "Não repetir discurso genérico de desindustrialização. Aqui a plateia sabe qual forno parou e em que mês, e a imprecisão custa mais que o silêncio.",
        "juizo": "A pauta é de comércio exterior e energia, competência federal direta. É o corredor onde o candidato a presidente fala com autoridade sem precisar de intermediário estadual.",
    },
    "mata": {
        "agenda": "Reindustrialização e universidade. A cidade polo aprovou lei de inovação e corredores tecnológicos ligados à federal.",
        "palanque": "Flávio com os deputados locais. Nenhum carregador domina o corredor, e o peso simbólico da cidade polo é o próprio ativo.",
        "frase": "Foi aqui que começou.",
        "fatos": [
            (
                "A indústria responde por 17% dos empregos formais de Juiz de Fora e o setor busca recuperar protagonismo.",
                "Tribuna de Minas",
                "https://tribunademinas.com.br/noticias/cidade/30-08-2026/empregos-formais-industria-protagonismo.html",
            ),
            (
                "A imprensa local convocou os candidatos ao governo de Minas a dizer o que prometem especificamente para Juiz de Fora e região.",
                "Tribuna de Minas",
                "https://tribunademinas.com.br/noticias/politica/eleicoes-2026/22-08-2026/eleicoes-2026-candidatos-ao-governo-de-minas-dizem-o-que-prometem-para-juiz-de-fora-e-regiao-confira.html",
            ),
            (
                "A motociata que sairia do aeroporto de Juiz de Fora até o ponto do atentado de 2018 foi cancelada por condição de voo e seguia sem data nova em meados de agosto.",
                "O Tempo",
                "https://www.otempo.com.br/eleicoes/2026/presidentes/2026/8/17/flavio-ainda-nao-preve-nova-data-para-motociata-simbolica-em-juiz-de-fora-apos-cancelamento",
            ),
        ],
        "eventos": [
            "A motociata pendente de Juiz de Fora, do aeroporto ao centro. É a agenda de maior carga simbólica disponível à campanha, está inacabada por motivo de força maior, e acontece no maior município que trocou de lado entre 2018 e 2022.",
            "Caminhada de comércio de rua em Barbacena, Ubá e Muriaé, com pauta de móveis, confecção e fila de saúde.",
            "Encontro com cafeicultores em Manhuaçu, que é a cidade grande da Mata onde a direita seguiu majoritária.",
            "Evitar o campus da federal como palco principal. Em Viçosa e em Juiz de Fora a universidade rende melhor como visita curta que como comício.",
        ],
        "nao_dizer": "Não transformar a data do atentado em promessa de revanche. O que rende na cidade é a memória do episódio e a ideia de continuidade, não o ajuste de contas.",
        "juizo": "Volume, memória e cobertura nacional garantida no mesmo lugar. Juiz de Fora sozinha tem mais eleitores que o corredor do minério inteiro.",
    },
    "producao": {
        "agenda": "Tarifa, frete, energia e conta fiscal. É o eleitorado menos tolerante a promessa sem fonte.",
        "palanque": "Flávio sozinho, com os deputados de base regional. Os três carregadores rendem abaixo de Bolsonaro aqui, e chamar qualquer um deles ao palco não acrescenta.",
        "frase": "Minas produz o que o Brasil exporta e paga o que o Brasil gasta.",
        "fatos": [
            (
                "As exportações mineiras de café aos Estados Unidos caíram 34% no primeiro semestre de 2026, o equivalente a US$ 642,3 milhões.",
                "Diário do Comércio",
                "https://diariodocomercio.com.br/economia/cafe-exporacoes-minas-gerais-estados-unidos/",
            ),
            (
                "O Triângulo abriu 3.621 empresas no primeiro trimestre de 2026, com Uberlândia concentrando cerca de 58% do total.",
                "Regionalzão",
                "https://regionalzao.com.br/economia/empresas-triangulo-mineiro-1-trimestre-2026/",
            ),
            (
                "Um novo terminal rodoferroviário deve integrar o Triângulo ao Porto de Santos, com investimento em torno de R$ 130 milhões.",
                "Portos e Navios",
                "https://www.portosenavios.com.br/edicao-752-marco-abril-de-2026/terminal-rodoferroviario-integrara-triangulo-mineiro-ao-porto-de-santos",
            ),
        ],
        "eventos": [
            "Exposição agropecuária de grande porte, com a ExpoZebu de Uberaba como referência de escala e público do calendário mineiro.",
            "Motociata em Uberlândia, onde Bolsonaro fez a primeira motociata de Minas e a cidade guarda memória de mobilização.",
            "Encontro de cooperativas de café no eixo Varginha, Três Pontas, Guaxupé e Patrocínio, com pauta de tarifa, crédito e frete.",
            "Visita ao polo tecnológico de Santa Rita do Sapucaí e ao distrito logístico de Extrema, com pauta de energia e imposto.",
        ],
        "nao_dizer": "Não usar aqui a fala do corredor do minério. Este é o eleitorado que mais reage a promessa sem fonte e o que mais lê conta fiscal.",
        "juizo": "Contraponto que a própria campanha precisa ouvir: neste corredor os três carregadores rendem abaixo de Bolsonaro. É onde o nome do topo da chapa se sustenta sozinho ou não se sustenta.",
    },
    "vales": {
        "agenda": "Água, saúde e mineral crítico. A distância até o atendimento especializado pesa mais aqui do que em qualquer outra região de Minas.",
        "palanque": "Cleitinho e rádio. Nikolas e Engler não viajam para cá, e agenda presidencial longa nesta região é tempo mal empregado.",
        "frase": "Aqui não se pede o voto. Pede-se para ser ouvido.",
        "fatos": [
            (
                "O Vale do Jequitinhonha concentra os projetos de lítio de Araçuaí e Itinga, com refino de pureza para bateria e expansão de capacidade em curso.",
                "CNN Brasil",
                "https://www.cnnbrasil.com.br/infra/vale-do-litio-completa-tres-anos-com-desenvolvimento-e-gargalos-em-mg/",
            ),
            (
                "Araçuaí, Poços de Caldas e Araxá aparecem como polos de terras raras que colocam Minas no centro da nova economia mineral.",
                "O Tempo",
                "https://www.otempo.com.br/economia/2026/5/13/projetos-de-terras-raras-em-minas-colocam-estado-no-epicentro-da-nova-economia-global",
            ),
            (
                "O governo estadual investiu R$ 15 milhões em estudos da Barragem de Congonhas, no Norte, com conclusão prevista para 2026 e foco em agricultura irrigada.",
                "Agência Minas",
                "https://agenciaminas.mg.gov.br/noticia/em-montes-claros-vice-governador-acompanha-apresentacao-do-projeto-barragem-de-congonhas",
            ),
        ],
        "eventos": [
            "Entrevista em rádio AM e FM de alcance regional, que continua sendo o meio dominante e vale mais que qualquer palanque montado.",
            "Agenda de irrigação e água no eixo Jaíba, Janaúba e Montes Claros, com pauta de barragem e adutora.",
            "Visita ao polo de lítio em Araçuaí e Itinga com pauta de contrapartida local, nunca como propaganda de mineradora.",
            "Motociata rende imagem em Montes Claros e Teófilo Otoni pela frota alta, mas o objetivo ali é cobertura nacional, não conversão local.",
        ],
        "nao_dizer": "Não prometer reversão eleitoral nesta região nem gastar semana inteira de agenda presidencial. Cada ponto aqui custa muitas vezes mais do que no corredor do minério.",
        "juizo": "Contenção, não conversão. E a direita não tem dono regional: no Jequitinhonha o único parlamentar com domínio de votação na região é do PT, e no Mucuri e na Central Mineira nenhum eleito de 2022 tem base concentrada.",
    },
}

MESO_DO_CORREDOR = {
    "minerio": "Metropolitana de Belo Horizonte",
    "metropolitano": "Metropolitana de Belo Horizonte",
    "oeste": "Oeste de Minas",
    "aco": "Vale do Rio Doce",
    "mata": "Zona da Mata",
    "producao": "Triângulo Mineiro/Alto Paranaíba",
    "vales": "Norte de Minas",
}


def main() -> None:
    extrai_nominal_mg()
    rows = carrega()
    medias = aplica_indice(rows)
    eleitorado = sum(r["el"] for r in rows)
    por_nome = {r["mun"]: r for r in rows}
    perfil = list(
        csv.DictReader(
            (DERIVED / "candidatos_2022_perfil_territorial.csv").open(encoding="utf-8")
        )
    )

    meso: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        meso[r["meso"]].append(r)

    corredores = []
    for slug, nome, sub, municipios in CORREDORES:
        sel = [por_nome[m] for m in municipios if m in por_nome]
        faltando = [m for m in municipios if m not in por_nome]
        if faltando:
            print("aviso, municipio nao encontrado:", faltando)
        corredores.append(
            {
                "slug": slug,
                "nome": nome,
                "sub": sub,
                "resumo": agrega(sel, eleitorado),
                "pauta": PAUTA[slug],
                "ancoras": ancoras(perfil, MESO_DO_CORREDOR[slug]),
                "cidades": [
                    {
                        k: c[k]
                        for k in (
                            "mun",
                            "meso",
                            "el",
                            "bol1",
                            "bol2",
                            "marg",
                            "desl",
                            "virada",
                            "cleit",
                            "niko",
                            "engler",
                            "iC",
                            "iN",
                            "iE",
                        )
                    }
                    for c in sorted(sel, key=lambda r: -r["el"])
                ],
            }
        )

    trio = sorted(
        [r for r in rows if r["iC"] > 100 and r["iN"] > 100 and r["iE"] > 100],
        key=lambda r: -r["iTrio"],
    )
    viradas = [r for r in rows if r["virada"] == "Direita→esquerda"]

    payload = {
        "meta": {
            "gerado_por": "scripts/mg-082026-camada2.py",
            "fontes": [
                "TSE votacao_candidato_munzona 2018 e 2022",
                "TSE perfil do eleitorado 01/07/2026",
                "IBGE Censo 2022 e PIB municipal 2023",
            ],
            "definicao_indice": (
                "O índice divide o desempenho do candidato no município pela média "
                "estadual dele, divide o mesmo cálculo feito com Bolsonaro no primeiro "
                "turno de 2022, e multiplica por cem. Todos os percentuais são sobre "
                "votos válidos do próprio cargo."
            ),
        },
        "estado": {
            "eleitores": eleitorado,
            "municipios": len(rows),
            **medias,
            "viradas_de": len(viradas),
            "eleitores_viradas": sum(r["el"] for r in viradas),
            "margem_media_viradas": round(
                sum(r["el"] * r["marg"] for r in viradas)
                / sum(r["el"] for r in viradas),
                2,
            ),
            "viradas_ate_5pp": sum(1 for r in viradas if abs(r["marg"]) <= 5),
            "disputados_5pp": sum(1 for r in rows if abs(r["marg"]) <= 5),
            "eleitores_disputados_5pp": sum(
                r["el"] for r in rows if abs(r["marg"]) <= 5
            ),
        },
        "mesorregioes": [
            {"meso": k, **agrega(v, eleitorado)}
            for k, v in sorted(
                meso.items(), key=lambda kv: -agrega(kv[1], eleitorado)["iC"]
            )
        ],
        "corredores": corredores,
        "trio": {
            "municipios": len(trio),
            "eleitores": sum(r["el"] for r in trio),
            "lista": [
                {
                    k: r[k]
                    for k in (
                        "mun",
                        "meso",
                        "el",
                        "bol1",
                        "marg",
                        "virada",
                        "iC",
                        "iN",
                        "iE",
                        "iTrio",
                    )
                }
                for r in trio
            ],
        },
        "bh_zonas": bh_por_zona(),
    }

    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "mg_082026_camada2.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    with (DERIVED / "carregadores-municipais.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        campos = [
            "ibge",
            "mun",
            "meso",
            "inter",
            "el",
            "bol1",
            "lul1",
            "bol2",
            "marg",
            "desl",
            "virada",
            "cleit",
            "niko",
            "engler",
            "iC",
            "iN",
            "iE",
            "iTrio",
        ]
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: -r["el"]))
    with (DERIVED / "corredores.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["slug", "nome"] + list(corredores[0]["resumo"].keys())
        )
        w.writeheader()
        for c in corredores:
            w.writerow({"slug": c["slug"], "nome": c["nome"], **c["resumo"]})

    print(f"MG {eleitorado:,} eleitores | medias {medias}")
    print(
        f"trio acima de Bolsonaro: {len(trio)} municipios, {sum(r['el'] for r in trio):,} eleitores"
    )
    for c in corredores:
        r = c["resumo"]
        print(
            f"  {c['nome']:<34}{r['eleitores']:>10,} ({r['share_mg']:>5.2f}%) Bol1T {r['bol1']:>5.1f} "
            f"marg {r['marg']:>+6.1f} iC{r['iC']:>4} iN{r['iN']:>4} iE{r['iE']:>4} ancoras={len(c['ancoras'])}"
        )


if __name__ == "__main__":
    main()
