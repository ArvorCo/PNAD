"""Candidaturas ao Senado 2026, Senado que continua (2022) e fotos oficiais.

Tudo sai dos arquivos oficiais do TSE, lidos em streaming. Nada e digitado a mao,
exceto a tabela APELIDOS, que declara cada excecao de nome de forma explicita.
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/tse_candidatos_2026"
FOTOS_ZIP = RAW / "fotos"
CAND_ZIP = RAW / "consulta_cand_2026.zip"
RES_2022 = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"
ELEITORADO_JSON = ROOT / "data/outputs/predicao_2026/tse.json"
SAIDA = ROOT / "analysis/senado_2026"
IMG = ROOT / "docs/img/senado"
URL_FOTOS = (
    "https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/"
    "foto_cand2026_{uf}_div.zip"
)

UFS = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
]

# Excecoes declaradas: (UF, nome na pesquisa normalizado) -> nome de urna
# normalizado no TSE. Cada linha precisa de motivo escrito ao lado. Vazia por
# decisao: nenhum casamento por adivinhacao silenciosa.
# (UF, nome normalizado na pesquisa) -> nome de urna normalizado no TSE. Cada
# entrada foi conferida contra consulta_cand_2026 em 03/10/2026.
APELIDOS: dict[tuple[str, str], str] = {
    ("PI", "julio cesar"): "julio cesar o julim do lula",
    ("PE", "mailson neto"): "mailson da silva neto",
    ("SE", "renatinha oliveira"): "renatinha",
    ("RO", "bruno bolsonaro scheid"): "bruno scheid",
    ("RR", "helio bolsonaro"): "helio fernando barbosa lopes",
    ("TO", "nilton santos"): "coronel nilton santos",
}

# Nome de urna repetido na mesma UF (dois registros da mesma pessoa no TSE):
# o SQ escolhido e o registro mais recente, declarado aqui.
DESEMPATE: dict[tuple[str, str], str] = {
    ("SP", "guto schiavetto"): "250002554075",
}

NULOS = {"#NULO", "#NE", "-1", "-3", ""}
LADO_FOTO = 240
QUALIDADE_JPEG = 82


def normalizar(nome: str) -> str:
    """Minusculas, sem acento, sem conteudo entre parenteses, espaco unico."""
    sem_parenteses = re.sub(r"\([^)]*\)", " ", nome or "")
    decomposto = unicodedata.normalize("NFKD", sem_parenteses)
    sem_acento = "".join(c for c in decomposto if not unicodedata.combining(c))
    limpo = re.sub(r"[^a-z0-9]+", " ", sem_acento.lower())
    return limpo.strip()


def _valor(texto: str | None) -> str | None:
    texto = (texto or "").strip()
    return None if texto in NULOS else texto


def ler_csv(fluxo: io.BufferedIOBase):
    yield from csv.DictReader(
        io.TextIOWrapper(fluxo, encoding="latin-1", newline=""), delimiter=";"
    )


def linha_candidato(row: dict, campo_de) -> dict:
    """Converte uma linha do consulta_cand em registro de candidatura."""
    partido = _valor(row.get("SG_PARTIDO"))
    federacao = _valor(row.get("NM_FEDERACAO"))
    return {
        "uf": row["SG_UF"],
        "sq_candidato": row["SQ_CANDIDATO"],
        "nome_urna": row["NM_URNA_CANDIDATO"],
        "nome_completo": row["NM_CANDIDATO"],
        "numero": row["NR_CANDIDATO"],
        "partido": partido,
        "campo": campo_de(partido),
        "coligacao": _valor(row.get("NM_COLIGACAO")),
        "composicao_coligacao": _valor(row.get("DS_COMPOSICAO_COLIGACAO")),
        "federacao": federacao,
        "genero": _valor(row.get("DS_GENERO")),
        "ocupacao": _valor(row.get("DS_OCUPACAO")),
        "situacao_candidatura": _valor(row.get("DS_SITUACAO_CANDIDATURA")),
        "situacao_totalizacao": _valor(row.get("DS_SIT_TOT_TURNO")),
        "foto": None,
    }


def ler_candidatos(zip_path: Path, campo_de) -> list[dict]:
    """Candidaturas a senador (CD_CARGO 5) de todas as UFs, ordenadas."""
    saida = []
    with zipfile.ZipFile(zip_path) as z:
        for membro in sorted(z.namelist()):
            nome = Path(membro).stem
            if not membro.endswith(".csv") or nome.rsplit("_", 1)[-1] not in UFS:
                continue
            with z.open(membro) as f:
                saida.extend(
                    linha_candidato(r, campo_de)
                    for r in ler_csv(f)
                    if r["CD_CARGO"] == "5"
                )
    saida.sort(key=lambda c: (c["uf"], c["nome_urna"], c["sq_candidato"]))
    return saida


def eleitos_2022(linhas, campo_de) -> list[dict]:
    """Eleito de cada UF em 2022: soma votos nominais por SQ e filtra ELEITO."""
    votos: dict[str, int] = defaultdict(int)
    info: dict[str, dict] = {}
    for r in linhas:
        if r["CD_CARGO"] != "5":
            continue
        sq = r["SQ_CANDIDATO"]
        votos[sq] += int(r["QT_VOTOS_NOMINAIS"] or 0)
        if (r["DS_SIT_TOT_TURNO"] or "").upper().startswith("ELEITO"):
            info[sq] = r
    saida = []
    for sq, r in info.items():
        saida.append(
            {
                "uf": r["SG_UF"],
                "sq_candidato": sq,
                "nome": r["NM_URNA_CANDIDATO"],
                "nome_completo": r["NM_CANDIDATO"],
                "partido": r["SG_PARTIDO"],
                "campo": campo_de(r["SG_PARTIDO"]),
                "votos": votos[sq],
                "situacao": r["DS_SIT_TOT_TURNO"],
            }
        )
    saida.sort(key=lambda e: e["uf"])
    return saida


def ler_eleitos_2022(zip_path: Path, campo_de) -> list[dict]:
    def todas():
        with zipfile.ZipFile(zip_path) as z:
            for membro in sorted(z.namelist()):
                if membro.endswith(".csv"):
                    with z.open(membro) as f:
                        yield from ler_csv(f)

    return eleitos_2022(todas(), campo_de)


def casar_nomes(
    candidatos: list[dict], citados: list[tuple[str, str]]
) -> tuple[list[dict], list[dict]]:
    """Casa (UF, nome da pesquisa) com a candidatura do TSE, sem adivinhar.

    Ordem: apelido declarado, nome de urna, nome completo. Nome ambiguo na UF
    (duas candidaturas com a mesma forma normalizada) nao casa.
    """
    indice: dict[tuple[str, str], set[str]] = defaultdict(set)
    por_sq = {c["sq_candidato"]: c for c in candidatos}
    for c in candidatos:
        for chave in (c["nome_urna"], c["nome_completo"]):
            indice[(c["uf"], normalizar(chave))].add(c["sq_candidato"])
    casados, perdidos = [], []
    vistos = set()
    for uf, nome in citados:
        if (uf, nome) in vistos:
            continue
        vistos.add((uf, nome))
        norma = normalizar(nome)
        alvo = APELIDOS.get((uf, norma), norma)
        achados = indice.get((uf, alvo), set())
        if len(achados) > 1 and DESEMPATE.get((uf, alvo)) in achados:
            achados = {DESEMPATE[(uf, alvo)]}
        if len(achados) == 1:
            sq = next(iter(achados))
            casados.append(
                {
                    "uf": uf,
                    "nome_pesquisa": nome,
                    "sq_candidato": sq,
                    "nome_urna": por_sq[sq]["nome_urna"],
                    "via_apelido": (uf, norma) in APELIDOS,
                }
            )
        else:
            motivo = "ambiguo" if achados else "sem_candidatura_no_tse"
            perdidos.append({"uf": uf, "nome_pesquisa": nome, "motivo": motivo})
    return casados, perdidos


def nomes_das_pesquisas(pasta: Path) -> list[tuple[str, str]]:
    import json

    saida = []
    for arq in sorted(pasta.glob("*.json")):
        dados = json.loads(arq.read_text(encoding="utf-8"))
        uf = dados.get("uf")
        saida.extend((uf, c["nome"]) for c in dados.get("candidatos", []) if uf)
    return saida


def sq_do_arquivo(nome: str) -> str | None:
    """SQ a partir de F<UF><SQ>_div.jpg ou F<SQ>_div.jpg."""
    m = re.fullmatch(r"F(?:[A-Z]{2})?(\d+)_div\.jpg", Path(nome).name)
    return m.group(1) if m else None


def recorte_quadrado(imagem, lado: int = LADO_FOTO):
    """Recorte central quadrado e reducao para lado x lado (Pillow)."""
    from PIL import Image

    imagem = imagem.convert("RGB")
    w, h = imagem.size
    m = min(w, h)
    esq, topo = (w - m) // 2, (h - m) // 2
    return imagem.crop((esq, topo, esq + m, topo + m)).resize(
        (lado, lado), Image.Resampling.LANCZOS
    )


def baixar_fotos(ufs: list[str]) -> dict[str, str]:
    """Baixa os zips de fotos que faltam. Devolve {UF: erro} das falhas."""
    import urllib.request

    FOTOS_ZIP.mkdir(parents=True, exist_ok=True)
    falhas = {}
    for uf in ufs:
        destino = FOTOS_ZIP / f"foto_cand2026_{uf}_div.zip"
        if destino.exists() and zipfile.is_zipfile(destino):
            continue
        try:
            urllib.request.urlretrieve(URL_FOTOS.format(uf=uf), destino)
            if not zipfile.is_zipfile(destino):
                raise ValueError("arquivo baixado nao e zip")
        except Exception as erro:
            destino.unlink(missing_ok=True)
            falhas[uf] = str(erro)
    return falhas


def exportar_fotos(
    ufs_e_sqs: list[tuple[str, str]], destino: Path = IMG
) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Grava destino/<UF>_<SQ>.jpg 240x240. Devolve (gravadas, ausentes)."""
    from PIL import Image

    destino.mkdir(parents=True, exist_ok=True)
    por_uf: dict[str, set[str]] = defaultdict(set)
    for uf, sq in ufs_e_sqs:
        por_uf[uf].add(sq)
    gravadas, ausentes = [], []
    for uf, sqs in sorted(por_uf.items()):
        caminho = FOTOS_ZIP / f"foto_cand2026_{uf}_div.zip"
        achadas: set[str] = set()
        if caminho.exists():
            with zipfile.ZipFile(caminho) as z:
                for membro in z.namelist():
                    sq = sq_do_arquivo(membro)
                    if sq in sqs:
                        with z.open(membro) as f:
                            img = Image.open(io.BytesIO(f.read()))
                            recorte_quadrado(img).save(
                                destino / f"{uf}_{sq}.jpg",
                                "JPEG",
                                quality=QUALIDADE_JPEG,
                                optimize=True,
                            )
                        achadas.add(sq)
        gravadas.extend((uf, sq) for sq in sorted(achadas))
        ausentes.extend((uf, sq) for sq in sorted(sqs - achadas))
    return gravadas, ausentes
