"""Dataset aberto por seção do 2º turno de 2026: CSV, dicionário e manifesto.

Uma linha por seção do Brasil e do exterior com boletim de urna em ao menos um
turno (união das chaves dos dois bancos locais). Votos, horários e metadados da
urna vêm dos BUs decodificados (``politize_se.fontes.bu``); sinais, escore,
atenção dos logs, mudança de local, situação da urna e grupo da mistura vêm dos
arquivos públicos do Politize-se. Bytes reprodutíveis: gzip com ``mtime=0`` e
linhas ordenadas por UF, município, zona e seção. Rótulo: sinal pede explicação,
não prova irregularidade; atipicidade estatística não é irregularidade.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import time
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from politize_se import fontes

ROOT = fontes.ROOT
PASTA = ROOT / "docs/assets/apuracao_2t/dataset"
CSV_NOME = "secoes_1t_2t_2026.csv.gz"
CSV = PASTA / CSV_NOME
DICIONARIO = PASTA / "DICIONARIO.md"
MANIFESTO = PASTA / "manifesto.json"
PARTES = PASTA / "uf"
POLITIZE_SE = ROOT / "docs/assets/politize_se/dados"
LOGS_2T_CSV = "docs/assets/logs_urnas_2t_2026/secoes.csv.gz"
DEPOSITO_BRUTO = ROOT / "analysis/apuracao_2t_2026/deposito_bruto.json"
LIMITE_PARTES = 95 * 1024 * 1024
ROTULO = (
    "Sinal pede explicação, não prova irregularidade; "
    "atipicidade estatística não é irregularidade."
)

UFS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS", "MT",
    "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP",
    "TO", "ZZ",
]  # fmt: skip

# (coluna, definição, fonte, unidade); a ordem é a do CSV.
COLUNAS: list[tuple[str, str, str, str]] = [
    ("uf", "Unidade da federação; ZZ é o exterior", "BU", "sigla"),
    (
        "mun_tse",
        "Código TSE do município, cinco dígitos com zeros à esquerda",
        "BU",
        "código",
    ),
    (
        "municipio",
        "Nome do município no cadastro do Politize-se",
        "Politize-se",
        "texto",
    ),
    ("zona", "Zona eleitoral", "BU", "número"),
    (
        "secao",
        "Seção eleitoral (seção principal; seções agregadas entram nela)",
        "BU",
        "número",
    ),
    (
        "local_id",
        "Identificador do local de votação (UF-município-zona-número do local)",
        "Politize-se",
        "código",
    ),
    (
        "aptos_1t",
        "Eleitores aptos na urna no 1º turno (seção mais trânsito)",
        "BU",
        "pessoas",
    ),
    ("comparecimento_1t", "Eleitores que compareceram no 1º turno", "BU", "pessoas"),
    (
        "lula_1t",
        "Votos nominais em Lula (13) para presidente no 1º turno",
        "BU",
        "votos",
    ),
    (
        "flavio_1t",
        "Votos nominais em Flávio Bolsonaro (22) para presidente no 1º turno",
        "BU",
        "votos",
    ),
    (
        "outros_1t",
        "Votos nominais nas demais candidaturas a presidente no 1º turno",
        "BU",
        "votos",
    ),
    ("brancos_1t", "Votos em branco para presidente no 1º turno", "BU", "votos"),
    ("nulos_1t", "Votos nulos para presidente no 1º turno", "BU", "votos"),
    (
        "sem_biometria_1t",
        "Eleitores que compareceram sem biometria cadastrada no 1º turno",
        "BU",
        "pessoas",
    ),
    (
        "ano_nascimento_1t",
        "Eleitores habilitados por dados biográficos (ano de nascimento) no 1º turno",
        "BU",
        "pessoas",
    ),
    (
        "biometria_1t",
        "Eleitores habilitados pela biometria no 1º turno",
        "BU",
        "pessoas",
    ),
    (
        "abertura_1t",
        "Horário do primeiro voto no 1º turno, como impresso no BU, sem conversão de fuso",
        "BU",
        "data e hora",
    ),
    (
        "encerramento_1t",
        "Horário do último voto no 1º turno, como impresso no BU",
        "BU",
        "data e hora",
    ),
    ("emissao_bu_1t", "Horário de emissão do BU no 1º turno", "BU", "data e hora"),
    (
        "recebimento_1t",
        "Recebimento do arquivo pelo TSE no 1º turno, como publicado",
        "BU",
        "data e hora",
    ),
    (
        "urna_1t",
        "Número interno (série) da urna que emitiu o BU no 1º turno",
        "BU",
        "número",
    ),
    (
        "modelo_1t",
        "Modelo da urna no 1º turno (UE2009 a UE2022), lido do log",
        "log",
        "texto",
    ),
    (
        "tipo_urna_1t",
        "Tipo da urna no 1º turno: 1 seção, 3 contingência, 4 reserva de seção, 6 reserva encerrando seção",
        "BU",
        "código",
    ),
    (
        "tipo_arquivo_1t",
        "Tipo do arquivo no 1º turno: 1 votação na urna, 2 votação recuperada, 3 a 6 sistema de apuração",
        "BU",
        "código",
    ),
    (
        "cargas_1t",
        "Número de cargas no histórico da urna no 1º turno",
        "BU",
        "contagem",
    ),
    (
        "aptos_2t",
        "Eleitores aptos na urna no 2º turno (seção mais trânsito)",
        "BU",
        "pessoas",
    ),
    ("comparecimento_2t", "Eleitores que compareceram no 2º turno", "BU", "pessoas"),
    ("lula_2t", "Votos nominais em Lula (13) no 2º turno", "BU", "votos"),
    ("flavio_2t", "Votos nominais em Flávio Bolsonaro (22) no 2º turno", "BU", "votos"),
    ("brancos_2t", "Votos em branco para presidente no 2º turno", "BU", "votos"),
    ("nulos_2t", "Votos nulos para presidente no 2º turno", "BU", "votos"),
    (
        "sem_biometria_2t",
        "Eleitores que compareceram sem biometria cadastrada no 2º turno",
        "BU",
        "pessoas",
    ),
    (
        "ano_nascimento_2t",
        "Eleitores habilitados por dados biográficos (ano de nascimento) no 2º turno",
        "BU",
        "pessoas",
    ),
    (
        "biometria_2t",
        "Eleitores habilitados pela biometria no 2º turno",
        "BU",
        "pessoas",
    ),
    (
        "abertura_2t",
        "Horário do primeiro voto no 2º turno, como impresso no BU, sem conversão de fuso",
        "BU",
        "data e hora",
    ),
    (
        "encerramento_2t",
        "Horário do último voto no 2º turno, como impresso no BU",
        "BU",
        "data e hora",
    ),
    ("emissao_bu_2t", "Horário de emissão do BU no 2º turno", "BU", "data e hora"),
    (
        "recebimento_2t",
        "Recebimento do arquivo pelo TSE no 2º turno, como publicado",
        "BU",
        "data e hora",
    ),
    (
        "urna_2t",
        "Número interno (série) da urna que emitiu o BU no 2º turno",
        "BU",
        "número",
    ),
    (
        "modelo_2t",
        "Modelo da urna no 2º turno (UE2009 a UE2022), lido do log",
        "log",
        "texto",
    ),
    (
        "tipo_urna_2t",
        "Tipo da urna no 2º turno: 1 seção, 3 contingência, 4 reserva de seção, 6 reserva encerrando seção",
        "BU",
        "código",
    ),
    (
        "tipo_arquivo_2t",
        "Tipo do arquivo no 2º turno: 1 votação na urna, 2 votação recuperada, 3 a 6 sistema de apuração",
        "BU",
        "código",
    ),
    (
        "cargas_2t",
        "Número de cargas no histórico da urna no 2º turno",
        "BU",
        "contagem",
    ),
    (
        "urna_situacao",
        "Situação da urna entre os turnos: mesma, mesma_recarga, reserva, nova, outra_secao_zona, outra_secao_municipio, outro_municipio, sem_1t",
        "Politize-se",
        "categoria",
    ),
    (
        "escore_sinais_2t",
        "Número de sinais do 2º turno na seção (regras em politize_se/secoes)",
        "Politize-se",
        "contagem",
    ),
    (
        "sinais_2t",
        "Sinais do 2º turno separados por barra vertical: delta, sem_bio, ano_nasc, salto_bio, tardia, papel",
        "Politize-se",
        "lista",
    ),
    (
        "log_atencao_1t",
        "Nível de atenção do log da urna no 1º turno, 0 a 3 (0 rotina, 1 um sinal, 2 sinais combinados, 3 conferir o arquivo)",
        "log",
        "nível",
    ),
    (
        "log_atencao_2t",
        "Nível de atenção do log da urna no 2º turno, mesma escala",
        "log",
        "nível",
    ),
    (
        "log_sinais_2t",
        "Diagnósticos do log do 2º turno separados por barra vertical (catálogo em politize_se/dados/indice.json)",
        "log",
        "lista",
    ),
    (
        "mudanca_local",
        "1 quando a seção mudou de prédio entre os turnos (mudança real pelo cadastro do TSE), 0 quando não; vazio sem cadastro",
        "Politize-se",
        "0 ou 1",
    ),
    (
        "ml_grupo",
        "Grupo da mistura estatística dos dois turnos (0 a k menos 1); vazio para exterior e seções fora do motor",
        "mistura",
        "código",
    ),
    (
        "ml_anomalo",
        "1 quando a seção está no grupo atípico do país, 0 quando não; vazio sem dado",
        "mistura",
        "0 ou 1",
    ),
    (
        "ml_p",
        "Parcela das seções do país com densidade menor na mistura (0,01 = entre as 1% menos prováveis)",
        "mistura",
        "fração",
    ),
]
NOMES = [c[0] for c in COLUNAS]

CAMPOS_TURNO = {
    "aptos": "aptos",
    "comparecimento": "comparecimento",
    "lula": "lula",
    "flavio": "flavio",
    "brancos": "brancos",
    "nulos": "nulos",
    "sem_biometria": "comp_sem_biometria",
    "ano_nascimento": "hab_ano_nascimento",
    "biometria": "hab_biometria",
    "abertura": "abertura",
    "encerramento": "encerramento",
    "emissao_bu": "emissao",
    "recebimento": "dr_hr",
    "urna": "numero_interno_urna",
    "modelo": "modelo_urna",
    "tipo_urna": "tipo_urna",
    "tipo_arquivo": "tipo_arquivo",
    "cargas": "n_cargas",
}


# ------------------------------------------------------------------ leitura


def municipios() -> dict[tuple[str, str], str]:
    """(UF, código TSE) → nome, pelo índice do Politize-se."""
    d = json.loads((POLITIZE_SE / "indice.json").read_text(encoding="utf-8"))
    cols = d["municipios"]["colunas"]
    i_uf, i_m, i_n = cols.index("uf"), cols.index("mun_tse"), cols.index("nome")
    return {(x[i_uf], x[i_m]): x[i_n] for x in d["municipios"]["linhas"]}


def politize_se(uf: str) -> dict[tuple[int, int], dict[str, Any]]:
    """Campos derivados por (zona, seção) dos arquivos públicos ``zona/<UF>/*.json.gz``."""
    out: dict[tuple[int, int], dict[str, Any]] = {}
    pasta = POLITIZE_SE / "zona" / uf
    if not pasta.exists():
        return out
    for arq in pasta.glob("*.json.gz"):
        with gzip.open(arq, "rt", encoding="utf-8") as f:
            d = json.load(f)
        z = int(d["zona"])
        lc = d["locais"]["colunas"].index("local_id")
        locais = [x[lc] for x in d["locais"]["linhas"]]
        for r in fontes.linhas(d["secoes"]):
            li = r.get("li")
            mud = r.get("mudanca")
            out[(z, int(r["secao"]))] = {
                "local_id": locais[li] if li is not None else None,
                "urna_situacao": r.get("urna_situacao"),
                "escore": r.get("escore"),
                "sinais": list(r.get("sinais") or []),
                "log1_atencao": r.get("log1_atencao"),
                "log2_atencao": r.get("log2_atencao"),
                "log2_sinais": list(r.get("log2_sinais") or []),
                "mudanca": None if mud is None else int(bool(mud.get("real"))),
                "ml_grupo": r.get("ml_grupo"),
                "ml_anomalo": r.get("ml_anomalo"),
                "ml_p": r.get("ml_p"),
            }
    return out


# ------------------------------------------------------------------ linhas


def _turno(b: dict[str, Any] | None) -> list[Any]:
    if b is None:
        return [None] * len(CAMPOS_TURNO)
    return [b.get(campo) for campo in CAMPOS_TURNO.values()]


def _local_id(uf: str, mun: str, z: int, pol: dict | None, b1, b2) -> str | None:
    if pol and pol.get("local_id"):
        return pol["local_id"]
    for b in (b2, b1):
        if b and b.get("local") is not None:
            return f"{uf}-{mun}-{z}-{int(b['local'])}"
    return None


def _lista(v: Iterable[str] | None) -> str | None:
    return "|".join(v) if v else None


def linha(
    uf: str,
    chave: tuple[int, int],
    b1: dict | None,
    b2: dict | None,
    pol: dict | None,
    nomes: dict[tuple[str, str], str],
) -> list[Any]:
    z, s = chave
    mun = (b2 or b1)["mun"]
    t1 = _turno(b1)
    t2 = _turno(b2)
    # 1º turno tem a coluna "outros" entre flavio e brancos; 2º turno não
    t1.insert(4, b1.get("outros") if b1 else None)
    p = pol or {}
    return [
        uf,
        mun,
        nomes.get((uf, mun)),
        z,
        s,
        _local_id(uf, mun, z, pol, b1, b2),
        *t1,
        *t2,
        p.get("urna_situacao"),
        p.get("escore"),
        _lista(p.get("sinais")),
        p.get("log1_atencao"),
        p.get("log2_atencao"),
        _lista(p.get("log2_sinais")),
        p.get("mudanca"),
        p.get("ml_grupo"),
        p.get("ml_anomalo"),
        p.get("ml_p"),
    ]


def linhas_uf(
    uf: str, nomes: dict[tuple[str, str], str], db_1t: Path, db_2t: Path
) -> list[list[Any]]:
    b1 = fontes.bu(db_1t, uf)
    b2 = fontes.bu(db_2t, uf)
    pol = politize_se(uf)
    chaves = set(b1) | set(b2)
    out = [linha(uf, k, b1.get(k), b2.get(k), pol.get(k), nomes) for k in chaves]
    out.sort(key=lambda r: (r[1], r[3], r[4]))
    return out


# ------------------------------------------------------------------ escrita


def _celula(v: Any) -> Any:
    return "" if v is None else v


def _csv_bytes(linhas: list[list[Any]], cabecalho: bool) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    if cabecalho:
        w.writerow(NOMES)
    for r in linhas:
        w.writerow([_celula(v) for v in r])
    return buf.getvalue().encode("utf-8")


class EscritorGz:
    """Gzip com cabeçalho fixo (sem nome, ``mtime=0``), gravado de forma atômica."""

    def __init__(self, destino: Path) -> None:
        destino.parent.mkdir(parents=True, exist_ok=True)
        self.destino = destino
        self.tmp = destino.with_name(f".{destino.name}.tmp")
        self.sha = hashlib.sha256()
        self.bytes = 0
        self._f = self.tmp.open("wb")
        self._gz = gzip.GzipFile(
            filename="", mode="wb", fileobj=self._f, mtime=0, compresslevel=9
        )

    def escrever(self, dados: bytes) -> None:
        self._gz.write(dados)

    def fechar(self) -> None:
        self._gz.close()
        self._f.close()
        bruto = self.tmp.read_bytes()
        self.sha.update(bruto)
        self.bytes = len(bruto)
        self.tmp.replace(self.destino)


def _rel(caminho: Path) -> str:
    """Caminho relativo ao repositório; fora dele (amostra em pasta temporária), absoluto."""
    return (
        str(caminho.relative_to(ROOT)) if caminho.is_relative_to(ROOT) else str(caminho)
    )


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        while bloco := f.read(1 << 24):
            h.update(bloco)
    return h.hexdigest()


def _fonte(chave: str, caminho: Path, com_hash: bool) -> dict[str, Any]:
    st = caminho.stat()
    return {
        "chave": chave,
        "caminho": _rel(caminho),
        "bytes": st.st_size,
        "modificado_em": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(
            timespec="seconds"
        ),
        "sha256": sha256_arquivo(caminho) if com_hash else None,
    }


def gerar(
    pasta: Path = PASTA,
    ufs: list[str] | None = None,
    db_1t: Path = fontes.DB_1T,
    db_2t: Path = fontes.DB_2T,
    hash_bancos: bool = True,
    log=print,
) -> dict[str, Any]:
    """Grava CSV, partes por UF (se preciso), dicionário e manifesto; devolve o manifesto."""
    inicio = time.time()
    ufs = ufs or UFS
    nomes = municipios()
    csv_path = pasta / CSV_NOME
    w = EscritorGz(csv_path)
    cabecalho = _csv_bytes([], cabecalho=True)
    w.escrever(cabecalho)
    partes: dict[str, bytes] = {}
    n = 0
    for uf in ufs:
        t = time.time()
        rows = linhas_uf(uf, nomes, db_1t, db_2t)
        n += len(rows)
        dados = _csv_bytes(rows, cabecalho=False)
        w.escrever(dados)
        partes[uf] = gzip.compress(cabecalho + dados, compresslevel=9, mtime=0)
        log(f"{uf}: {len(rows):,} seções em {time.time() - t:.1f}s")
    w.fechar()
    sha = w.sha.hexdigest()
    gerado_em = datetime.now(timezone.utc).isoformat(timespec="seconds")
    arq_partes = _partes(pasta, partes, w.bytes > LIMITE_PARTES)
    manifesto = {
        "arquivo": _rel(csv_path),
        "bytes": w.bytes,
        "sha256": sha,
        "n_linhas": n,
        "colunas": NOMES,
        "gerado_em": gerado_em,
        "universo": (
            "seções do Brasil e do exterior com boletim de urna em ao menos um dos "
            "dois turnos de 2026 (união das chaves dos dois bancos locais)"
        ),
        "rotulo": ROTULO,
        "partes_por_uf": arq_partes,
        "fontes": [
            _fonte("boletins_1t", db_1t, hash_bancos),
            _fonte("boletins_2t", db_2t, hash_bancos),
            _fonte("politize_se_indice", POLITIZE_SE / "indice.json", True),
        ],
        "segundos": round(time.time() - inicio, 1),
    }
    (pasta / "DICIONARIO.md").write_text(dicionario(manifesto), encoding="utf-8")
    (pasta / "manifesto.json").write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifesto


def _partes(pasta: Path, partes: dict[str, bytes], gravar: bool) -> list[dict] | None:
    destino = pasta / "uf"
    if destino.exists():
        for arq in destino.glob("*.csv.gz"):
            arq.unlink()
    if not gravar:
        if destino.exists() and not any(destino.iterdir()):
            destino.rmdir()
        return None
    destino.mkdir(parents=True, exist_ok=True)
    out = []
    for uf, dados in partes.items():
        arq = destino / f"{uf}.csv.gz"
        arq.write_bytes(dados)
        out.append(
            {
                "uf": uf,
                "arquivo": _rel(arq),
                "bytes": len(dados),
                "sha256": hashlib.sha256(dados).hexdigest(),
            }
        )
    return out


# ------------------------------------------------------------------ dicionário e leitura


def _pt(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _mb(n: int) -> str:
    return f"{n / 1_000_000:.1f} MB".replace(".", ",")


def dicionario(m: dict[str, Any]) -> str:
    """Markdown com cabeçalho (universo, data, hash, linhas, rótulo) e uma linha por coluna."""
    fontes_txt = "\n".join(
        f"- `{f['caminho']}`: {_pt(f['bytes'])} bytes"
        + (f", SHA-256 `{f['sha256']}`" if f["sha256"] else ", hash não calculado")
        for f in m["fontes"]
    )
    partes = ""
    if m.get("partes_por_uf"):
        partes = (
            "\n\nO arquivo único passa de 95 MB, por isso há também uma parte por UF em "
            "`uf/<UF>.csv.gz`, com o mesmo cabeçalho e as mesmas linhas; o arquivo único "
            "continua sendo a referência do hash.\n"
        )
    linhas = "\n".join(f"| `{c}` | {d} | {f} | {u} |" for c, d, f, u in COLUNAS)
    return f"""# Dataset aberto por seção: 1º e 2º turnos de 2026

**Universo.** {m["universo"][0].upper()}{m["universo"][1:]}. Nenhum voto de seção
pequena é ocultado: o TSE publica o boletim de cada seção.

**Arquivo.** `{Path(m["arquivo"]).name}`, {_pt(m["bytes"])} bytes ({_mb(m["bytes"])}),
{_pt(m["n_linhas"])} linhas de dados mais o cabeçalho, CSV separado por vírgula, UTF-8, gzip.
SHA-256 `{m["sha256"]}`. Gerado em {m["gerado_em"]}.{partes}

**Rótulo.** {m["rotulo"]} Os sinais e o grupo da mistura ordenam o que merece
conferência; não identificam causa nem conduta.

**Vazio** significa sem dado: seção sem boletim naquele turno, sem log processado,
sem cadastro no Politize-se ou fora do motor da mistura (exterior e seções com menos
de 30 aptos). Horários estão como impressos no BU, sem conversão de fuso.

**Fontes.** Boletins de urna decodificados dos arquivos públicos do TSE (bancos locais do
coletor), logs das urnas e camada pública do Politize-se:
{fontes_txt}

Cada log de urna do 2º turno tem URL oficial e SHA-256 em `{LOGS_2T_CSV}`. Os bancos
brutos (BUs decodificados, RDV, arquivos `.vsc` e logs) não cabem no repositório e ficam
em depósito separado; seus hashes são publicados em `analysis/apuracao_2t_2026/deposito_bruto.json`
quando o depósito é enviado.

## Colunas

| coluna | definição | fonte | unidade |
|---|---|---|---|
{linhas}

Fonte "BU": boletim de urna decodificado. "log": log da urna (modelo e diagnósticos).
"Politize-se": camada pública em `docs/assets/politize_se/dados/`. "mistura": modelo
estatístico dos dois turnos (`analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md`).
"""


def ler_manifesto(caminho: Path = MANIFESTO) -> dict[str, Any] | None:
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def colunas_do_dicionario(texto: str) -> list[str]:
    """Nomes das colunas na ordem da tabela do dicionário."""
    out = []
    for ln in texto.splitlines():
        if ln.startswith("| `") and "` |" in ln:
            out.append(ln[3 : ln.index("` |")])
    return out
