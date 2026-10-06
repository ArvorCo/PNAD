"""Registro, download e proveniência das fontes da camada de risco por local.

Cada fonte pública tem chave, camada, órgão, URL, caminho local em
``data/raw/<fonte>/`` (ignorado pelo git), licença declarada e regra de uso.
O download grava ao lado do arquivo um ``<arquivo>.fonte.json`` com URL,
instante do download, bytes, SHA-256 e status HTTP, para que
``--sem-download`` reaproveite o arquivo com a proveniência original.

Fonte que falha não derruba a rodada: fica com ``status = "falhou"`` e o motivo
exato, e a camada correspondente sai nula (nunca zero).
"""

from __future__ import annotations

import gzip
import hashlib
import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw"

GEOFTP = "https://geoftp.ibge.gov.br/organizacao_do_territorio"
SETORES = (
    f"{GEOFTP}/malhas_territoriais/"
    "malhas_de_setores_censitarios__divisoes_intramunicipais/censo_2022"
)
LOCALIDADES = f"{GEOFTP}/estrutura_territorial/localidades"
FRONTEIRA = f"{GEOFTP}/estrutura_territorial/municipios_da_faixa_de_fronteira/2024"
FUNAI_WFS = "https://geoserver.funai.gov.br/geoserver/Funai/ows"
ANM_REST = "https://geo.anm.gov.br/arcgis/rest/services/SIGMINE/dados_anm/MapServer"
IPEA_API = "https://www.ipea.gov.br/dados-api"
IPEA_CMS = "https://www.ipea.gov.br/cms/api"
# O servidor da FUNAI não envia o certificado intermediário da cadeia. O
# intermediário é baixado do endereço AIA do próprio certificado e somado ao
# pacote de raízes confiáveis: a verificação TLS continua completa.
SECTIGO_INTERMEDIARIO = (
    "http://crt.sectigo.com/SectigoPublicServerAuthenticationCAOVR36.crt"
)

LICENCA_IBGE = (
    "dados públicos do IBGE; o índice do geoftp declara que todos os arquivos "
    "ali disponíveis são públicos"
)
LICENCA_FUNAI = (
    "dados públicos da FUNAI publicados no geoserver oficial; a página de "
    "geoprocessamento não declara licença específica"
)
LICENCA_ANM = (
    "dados abertos da ANM (SIGMINE), serviço REST oficial; licença específica "
    "não declarada no serviço"
)
LICENCA_IPEA = (
    "dados públicos do Atlas da Violência (Ipea), API de dados do próprio "
    "portal; licença específica não declarada"
)


@dataclass
class Fonte:
    """Uma fonte pública com proveniência completa."""

    chave: str
    camada: str
    nome: str
    orgao: str
    url: str
    arquivo: str  # caminho relativo a data/raw/
    licenca: str
    data_referencia: str
    regra: str
    status: str = "pendente"
    motivo: str | None = None
    baixado_em: str | None = None
    bytes: int | None = None
    sha256: str | None = None
    cobertura_locais: int | None = None
    cobertura_municipios: int | None = None
    paginas: list[str] = field(default_factory=list)
    caminho_repo: str | None = None

    @property
    def caminho(self) -> Path:
        return RAW / self.arquivo

    def para_json(self) -> dict[str, Any]:
        return {
            "chave": self.chave,
            "camada": self.camada,
            "nome": self.nome,
            "orgao": self.orgao,
            "url": self.url,
            "baixado_em": self.baixado_em,
            "caminho": self.caminho_repo
            or (f"data/raw/{self.arquivo}" if self.arquivo else None),
            "bytes": self.bytes,
            "sha256": self.sha256,
            "data_referencia": self.data_referencia,
            "licenca": self.licenca,
            "status": self.status,
            "motivo": self.motivo,
            "regra": self.regra,
            "cobertura_locais": self.cobertura_locais,
            "cobertura_municipios": self.cobertura_municipios,
        }


def agora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _query_anm(camada: int, where: str, offset: int) -> str:
    q = {
        "where": where,
        "outFields": "PROCESSO,FASE,SUBS,UF,AREA_HA",
        "returnGeometry": "true",
        "outSR": "4674",
        "f": "geojson",
        "resultOffset": str(offset),
        "resultRecordCount": "1000",
        "orderByFields": "OBJECTID",
    }
    if camada == 4:
        q["outFields"] = "NMReservaGarimpeira,QTAreaHA,DSDocumento"
    return f"{ANM_REST}/{camada}/query?{urlencode(q)}"


def registro() -> list[Fonte]:
    """Todas as fontes públicas consultadas, na ordem das camadas."""
    return [
        Fonte(
            "ibge_setores_2022_malha",
            "rural_urbano",
            "Malha de setores censitários do Censo 2022 (GeoPackage, Brasil)",
            "IBGE",
            f"{SETORES}/setores/gpkg/BR/BR_setores_CD2022.gpkg",
            "ibge_setores_2022/BR_setores_CD2022.gpkg",
            LICENCA_IBGE,
            "Censo Demográfico 2022, malha definitiva (arquivo de 12/11/2024)",
            "setor que contém o ponto do local (lat e lon do cadastro do TSE); "
            "situação, situação detalhada (CD_SIT), tipo (CD_TIPO) e favela e "
            "comunidade urbana (CD_FCU, NM_FCU) do próprio setor",
        ),
        Fonte(
            "ibge_setores_2022_dicionario",
            "rural_urbano",
            "Dicionário de dados da malha de setores e agregados do Censo 2022",
            "IBGE",
            f"{SETORES}/Dicionario_de_dados_malha_agregados.xlsx",
            "ibge_setores_2022/Dicionario_de_dados_malha_agregados.xlsx",
            LICENCA_IBGE,
            "Censo Demográfico 2022",
            "rótulos oficiais de CD_SIT e CD_TIPO lidos da aba Setor",
        ),
        Fonte(
            "funai_tis_poligonais",
            "terra_indigena",
            "Terras indígenas, poligonais (WFS Funai:tis_poligonais, GeoJSON)",
            "FUNAI",
            f"{FUNAI_WFS}?service=WFS&version=1.0.0&request=GetFeature"
            "&typeName=Funai:tis_poligonais&maxFeatures=10000"
            "&outputFormat=application/json",
            "funai/tis_poligonais.geojson",
            LICENCA_FUNAI,
            "base viva do geoserver da FUNAI, lida no dia do download",
            "local dentro do polígono ou a até 2 km da borda; distância por "
            "projeção equiretangular local em metros",
        ),
        Fonte(
            "ibge_localidades_indigenas_2022",
            "terra_indigena",
            "Localidades indígenas do Censo 2022 (LI, pontos, CSV)",
            "IBGE",
            f"{LOCALIDADES}/localidades_indigenas_2022/Arquivos_vetoriais/LI/csv/BR/"
            "BR_LIs_CD2022_20250919.csv",
            "ibge_localidades_indigenas_2022/BR_LIs_CD2022_20250919.csv",
            LICENCA_IBGE,
            "Censo Demográfico 2022, arquivo de 19/09/2025",
            "proxy declarado só para local sem terra indígena da FUNAI até 2 km: "
            "localidade indígena (ponto) a até 2 km do local",
        ),
        Fonte(
            "ibge_lcpi_2022",
            "terra_indigena",
            "Localidades com concentração de pessoas indígenas, Censo 2022 "
            "(LCPI, pontos, CSV)",
            "IBGE",
            f"{LOCALIDADES}/localidades_indigenas_2022/Arquivos_vetoriais/LCPI/csv/BR/"
            "BR_LCPIs_CD2022_20250919.csv",
            "ibge_localidades_indigenas_2022/BR_LCPIs_CD2022_20250919.csv",
            LICENCA_IBGE,
            "Censo Demográfico 2022, arquivo de 19/09/2025",
            "lida para conferência; não marca terra indígena, porque LCPI é "
            "concentração de pessoas indígenas fora de terra indígena",
        ),
        Fonte(
            "ibge_localidades_indigenas_dicionario",
            "terra_indigena",
            "Dicionário de dados das localidades indígenas 2022",
            "IBGE",
            f"{LOCALIDADES}/localidades_indigenas_2022/Arquivos_vetoriais/"
            "Dicionario_de_dados_Localidades_Indigenas.xlsx",
            "ibge_localidades_indigenas_2022/Dicionario_de_dados_Localidades_Indigenas.xlsx",
            LICENCA_IBGE,
            "Censo Demográfico 2022",
            "significado das colunas dos CSV de LI e LCPI",
        ),
        Fonte(
            "incra_areas_quilombolas",
            "quilombo",
            "Áreas de quilombolas (acervo fundiário e certificação do INCRA)",
            "INCRA",
            "https://certificacao.incra.gov.br/csv_shp/export_shp.py",
            "",
            "dados públicos do INCRA",
            "não lido",
            "polígonos de território quilombola, dentro ou até 2 km",
        ),
        Fonte(
            "ibge_localidades_quilombolas_2022",
            "quilombo",
            "Localidades quilombolas do Censo 2022 (pontos, CSV)",
            "IBGE",
            f"{LOCALIDADES}/localidades_quilombolas_2022/Arquivos_vetoriais/csv/BR/"
            "BR_LQs_CD2022.csv",
            "ibge_localidades_quilombolas_2022/BR_LQs_CD2022.csv",
            LICENCA_IBGE,
            "Censo Demográfico 2022, arquivo de 25/07/2024",
            "proxy declarado (o INCRA exige login gov.br): localidade quilombola "
            "(ponto) a até 2 km do local",
        ),
        Fonte(
            "ibge_localidades_quilombolas_dicionario",
            "quilombo",
            "Dicionário das localidades quilombolas 2022",
            "IBGE",
            f"{LOCALIDADES}/localidades_quilombolas_2022/Arquivos_vetoriais/"
            "Dicionario_LQs.xlsx",
            "ibge_localidades_quilombolas_2022/Dicionario_LQs.xlsx",
            LICENCA_IBGE,
            "Censo Demográfico 2022",
            "significado das colunas do CSV de localidades quilombolas",
        ),
        Fonte(
            "ibge_faixa_fronteira_2024",
            "fronteira",
            "Municípios da faixa de fronteira e cidades-gêmeas 2024 (XLS)",
            "IBGE",
            f"{FRONTEIRA}/Mun_Faixa_de_Fronteira_Cidades_Gemeas_2024.xls",
            "ibge_fronteira_2024/Mun_Faixa_de_Fronteira_Cidades_Gemeas_2024.xls",
            LICENCA_IBGE,
            "faixa de fronteira de 150 km, edição 2024",
            "município na lista da faixa de fronteira; cidade-gêmea pela coluna "
            "própria da planilha",
        ),
        Fonte(
            "anm_sigmine_lavra_garimpeira",
            "garimpo",
            "SIGMINE, processos minerários ativos na fase LAVRA GARIMPEIRA "
            "(camada 0, GeoJSON)",
            "ANM",
            _query_anm(0, "FASE='LAVRA GARIMPEIRA'", 0),
            "anm_sigmine/lavra_garimpeira.geojson",
            LICENCA_ANM,
            "serviço com atualização diária, lido no dia do download",
            "local a até 20 km de polígono de permissão de lavra garimpeira "
            "(fase LAVRA GARIMPEIRA) ou dentro de reserva garimpeira; município "
            "com garimpo quando um desses polígonos toca um setor censitário dele",
        ),
        Fonte(
            "anm_sigmine_reservas_garimpeiras",
            "garimpo",
            "SIGMINE, reservas garimpeiras (camada 4, GeoJSON)",
            "ANM",
            _query_anm(4, "1=1", 0),
            "anm_sigmine/reservas_garimpeiras.geojson",
            LICENCA_ANM,
            "serviço com atualização diária, lido no dia do download",
            "local dentro de reserva garimpeira (distância zero) ou a até 20 km",
        ),
        Fonte(
            "ipea_atlas_taxa_homicidios",
            "homicidios_municipio",
            "Atlas da Violência, série 20, taxa de homicídios registrados por "
            "município (abrangência 4)",
            "Ipea",
            f"{IPEA_API}/series-values/20/4",
            "ipea_atlas_violencia/serie_20_abrangencia_4.json",
            LICENCA_IPEA,
            "ano mais recente da série (SIM, CID-10 X85-Y09 e Y35, por residência)",
            "taxa por 100 mil do ano mais recente; quintil nacional sobre os "
            "municípios com valor (5 = maior taxa)",
        ),
        Fonte(
            "ipea_atlas_homicidios",
            "homicidios_municipio",
            "Atlas da Violência, série 328, homicídios registrados por município "
            "(abrangência 4)",
            "Ipea",
            f"{IPEA_API}/series-values/328/4",
            "ipea_atlas_violencia/serie_328_abrangencia_4.json",
            LICENCA_IPEA,
            "ano mais recente da série",
            "número absoluto de homicídios do mesmo ano, para dizer quantos "
            "óbitos sustentam a taxa",
        ),
        Fonte(
            "ipea_atlas_metadados_20",
            "homicidios_municipio",
            "Atlas da Violência, metadados da série 20",
            "Ipea",
            f"{IPEA_CMS}/series/20?filters%5Bprojetos%5D%5Bid%5D%5B%24eq%5D=3",
            "ipea_atlas_violencia/serie_20_metadados.json",
            LICENCA_IPEA,
            "metadados vigentes",
            "definição da taxa (CID-10 X85-Y09 e Y35, óbitos por residência)",
        ),
        Fonte(
            "ibge_localidades_2022",
            "sede_municipal",
            "Localidades do Brasil 2022 (GeoPackage compactado)",
            "IBGE",
            f"{LOCALIDADES}/Localidades_do_Brasil/2022/Localidades_Brasil_gpkg.zip",
            "ibge_localidades_2022/Localidades_Brasil_gpkg.zip",
            LICENCA_IBGE,
            "Localidades 2022 (arquivo de 19/11/2025)",
            "ponto da localidade de categoria cidade (sede municipal) de cada "
            "município",
        ),
        Fonte(
            "geni_uff_grupos_armados",
            "crime_organizado",
            "Mapa histórico dos grupos armados no Rio de Janeiro (GENI/UFF e "
            "Fogo Cruzado)",
            "GENI/UFF",
            "https://geni.uff.br/2025/12/04/atualizacao-do-mapa-historico-dos-grupos-armados-2/",
            "",
            "não declarada",
            "não lido",
            "usado só se houver arquivo de dados público com licença",
        ),
        Fonte(
            "fbsp_cartografias_amazonia_2025",
            "crime_organizado",
            "Cartografias da Violência na Amazônia, 4ª edição, quadros 3.2 a 3.10 "
            "(presença por município)",
            "Fórum Brasileiro de Segurança Pública e Instituto Mãe Crioula",
            "https://forumseguranca.org.br/wp-content/uploads/2025/11/"
            "cartografias-violencia-amazonia-2025.pdf",
            "fbsp/cartografias-violencia-amazonia-2025.pdf",
            "publicação pública do FBSP; licença não declarada no arquivo",
            "pesquisa de novembro de 2024 a setembro de 2025, publicada em "
            "novembro de 2025; cobre só os 772 municípios da Amazônia Legal",
            "município citado nos quadros de presença por UF; só o nome do "
            "município é lido, a coluna de grupos nunca é gravada; a leitura é "
            "conferida contra os totais por UF do quadro 3.1 (344 municípios)",
        ),
    ]


def _contexto_ssl(intermediario: Path | None) -> ssl.SSLContext:
    import certifi

    ctx = ssl.create_default_context(cafile=certifi.where())
    if intermediario is not None and intermediario.exists():
        ctx.load_verify_locations(cafile=str(intermediario))
    return ctx


def intermediario_funai(destino: Path) -> Path:
    """Baixa o intermediário Sectigo (DER) e grava em PEM, uma vez."""
    pem = destino / "sectigo_ov_r36.pem"
    if pem.exists():
        return pem
    destino.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SECTIGO_INTERMEDIARIO, timeout=60) as r:
        der = r.read()
    pem.write_text(ssl.DER_cert_to_PEM_cert(der), encoding="ascii")
    return pem


def _baixar_url(url: str, destino: Path, ctx: ssl.SSLContext, timeout: int) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": "arvor-pnad/1.0"})
    tmp = destino.with_suffix(destino.suffix + ".part")
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        status = r.status
        if r.headers.get("Content-Encoding", "").lower() == "gzip":
            tmp.write_bytes(gzip.decompress(r.read()))
        else:
            with tmp.open("wb") as f:
                for bloco in iter(lambda: r.read(1 << 20), b""):
                    f.write(bloco)
    tmp.replace(destino)
    return status


def _corpo(resposta: Any) -> bytes:
    dados = resposta.read()
    if dados[:2] == b"\x1f\x8b":
        return gzip.decompress(dados)
    return dados


def _baixar_anm_paginado(fonte: Fonte, ctx: ssl.SSLContext, timeout: int) -> int:
    """O REST da ANM devolve no máximo 1.000 feições por página: junta todas."""
    camada = 4 if "reservas" in fonte.chave else 0
    where = "1=1" if camada == 4 else "FASE='LAVRA GARIMPEIRA'"
    feicoes: list[dict[str, Any]] = []
    offset = 0
    status = 0
    while True:
        url = _query_anm(camada, where, offset)
        req = urllib.request.Request(url, headers={"User-Agent": "arvor-pnad/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
            status = r.status
            pagina = json.loads(_corpo(r).decode("utf-8"))
        if "error" in pagina:
            raise ValueError(f"ANM devolveu erro: {pagina['error']}")
        fonte.paginas.append(url)
        lote = pagina.get("features") or []
        feicoes.extend(lote)
        if len(lote) < 1000 and not pagina.get("exceededTransferLimit"):
            break
        offset += len(lote)
    fonte.caminho.write_text(
        json.dumps({"type": "FeatureCollection", "features": feicoes}),
        encoding="utf-8",
    )
    return status


def _meta(fonte: Fonte) -> Path:
    return fonte.caminho.with_name(fonte.caminho.name + ".fonte.json")


def baixar(fonte: Fonte, *, sem_download: bool, timeout: int = 3000) -> Fonte:
    """Baixa (ou reaproveita) a fonte e preenche bytes, SHA-256 e status."""
    if not fonte.arquivo:
        return fonte
    meta = _meta(fonte)
    if sem_download:
        if fonte.caminho.exists():
            info = json.loads(meta.read_text("utf-8")) if meta.exists() else {}
            fonte.baixado_em = info.get("baixado_em")
            fonte.bytes = fonte.caminho.stat().st_size
            fonte.sha256 = sha256_arquivo(fonte.caminho)
            fonte.paginas = info.get("paginas", [])
            fonte.status = "ok"
            if info.get("sha256") and info["sha256"] != fonte.sha256:
                fonte.motivo = "arquivo local difere do SHA-256 gravado no download"
        else:
            fonte.status = "falhou"
            fonte.motivo = "--sem-download e o arquivo não está em data/raw"
        return fonte
    fonte.caminho.parent.mkdir(parents=True, exist_ok=True)
    intermediario = None
    if fonte.url.startswith(FUNAI_WFS):
        try:
            intermediario = intermediario_funai(fonte.caminho.parent)
        except (urllib.error.URLError, OSError) as exc:
            fonte.status, fonte.motivo = "falhou", f"intermediário TLS: {exc}"
            return fonte
    ctx = _contexto_ssl(intermediario)
    try:
        if fonte.url.startswith(ANM_REST):
            status = _baixar_anm_paginado(fonte, ctx, timeout)
        else:
            status = _baixar_url(fonte.url, fonte.caminho, ctx, timeout)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        fonte.status = "falhou"
        fonte.motivo = f"{type(exc).__name__}: {exc}"
        return fonte
    fonte.baixado_em = agora_utc()
    fonte.bytes = fonte.caminho.stat().st_size
    fonte.sha256 = sha256_arquivo(fonte.caminho)
    fonte.status = "ok"
    meta.write_text(
        json.dumps(
            {
                "url": fonte.url,
                "paginas": fonte.paginas,
                "baixado_em": fonte.baixado_em,
                "http_status": status,
                "bytes": fonte.bytes,
                "sha256": fonte.sha256,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    return fonte


def fonte_local(
    chave: str,
    camada: str,
    nome: str,
    caminho: Path,
    regra: str,
    *,
    em_gravacao: bool = False,
) -> Fonte:
    """Arquivo do próprio repositório lido pela camada (sem download).

    Banco que outro processo ainda grava fica com SHA-256 nulo e o motivo,
    com tamanho e data de modificação, como manda o contrato do capítulo.
    """
    f = Fonte(chave, camada, nome, "Arvor (repositório)", "", "", "", "", regra)
    f.caminho_repo = str(caminho.relative_to(ROOT))
    f.licenca = "arquivo do repositório, derivado de fonte pública citada nele"
    info = caminho.stat()
    f.bytes = info.st_size
    f.data_referencia = "modificado em " + datetime.fromtimestamp(
        info.st_mtime, timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    f.status = "ok"
    if em_gravacao:
        f.motivo = "banco ainda gravado por outro processo; SHA-256 não é estável"
    else:
        f.sha256 = sha256_arquivo(caminho)
    return f
