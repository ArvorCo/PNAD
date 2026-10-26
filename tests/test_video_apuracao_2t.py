"""Vídeo "A noite do 2º turno" (video/apuracao_2t): ordem das cenas, dados do Remotion contra as
fontes, roteiro com números por extenso conferidos contra `apuracao_2t.json`, voz, portão de
duração e mídia.

Moldado em `test_video_sete_riscos.py`, de onde vêm os auxiliares (números por extenso, leitura
dos blocos `## id` e dos comentários `<!-- dado: caminho = valor -->`). Os testes que dependem de
um arquivo ainda não entregue (roteiro, voz) são pulados até o arquivo existir."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
from test_video_sete_riscos import (
    COMENTARIO,
    DADO,
    FONTE,
    TAG,
    _blocos,
    _conferir_dado,
    _narrado,
    _normalizar,
    _resolver,
)

VIDEO_JSON = (
    Path(__file__).resolve().parents[1] / "analysis/apuracao_2t_2026/video.json"
)


def video_publicado() -> bool:
    """O vídeo só é conferido número a número depois de publicado (youtube_id em video.json).

    Enquanto está em produção, o roteiro pode ficar atrás dos JSONs do dossiê, que são
    regravados a cada rodada de dados; a cena desatualizada é regravada antes da publicação.
    """
    try:
        return bool(
            json.loads(VIDEO_JSON.read_text(encoding="utf-8")).get("youtube_id")
        )
    except (OSError, ValueError):
        return False


ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video" / "apuracao_2t"
DADOS = VIDEO / "src" / "dados" / "apuracao_2t.json"
VOZ = VIDEO / "src" / "dados" / "voz.json"
MIDIA = VIDEO / "src" / "dados" / "midia.json"
CAPTURAS = VIDEO / "src" / "dados" / "capturas.json"
ORDEM_TS = VIDEO / "src" / "ordem.ts"
LINHA_TS = VIDEO / "src" / "linha.ts"
REGISTRO_TS = VIDEO / "src" / "cenas" / "registro.ts"
ROTEIRO = VIDEO / "roteiro" / "roteiro.md"
FONTES_MD = VIDEO / "roteiro" / "fontes.md"
CONTRATO = VIDEO / "CONTRATO.md"

# CONTRATO.md, seção 1: 32 cenas em 8 capítulos.
CAPITULOS = [
    "abertura", "noite", "projecao", "turnos", "secoes", "pesquisas", "urnas", "fecho",
]  # fmt: skip
IDS = [
    "abertura", "tese",
    "cap-noite", "noite-stf", "noite-parada", "noite-virada", "noite-fim",
    "cap-projecao", "proj-primeiro-ponto", "proj-serie", "proj-sem-virada",
    "cap-turnos", "turnos-swing-uf", "turnos-transferencia", "turnos-abstencao",
    "cap-secoes", "secoes-encerramento", "secoes-biometria", "secoes-comparecimento",
    "secoes-ranking",
    "cap-pesquisas", "pesq-erro", "pesq-reponderacao", "pesq-hipotese",
    "cap-urnas", "urnas-cadencia", "urnas-integridade", "urnas-assinatura", "paralela-177",
    "cap-fecho", "fecho-arvor", "fecho-chamada",
]  # fmt: skip
# CONTRATO.md, seção 3: blocos de analysis/apuracao_2t_2026/dados/ que o vídeo lê.
BLOCOS = [
    "presidente", "linha_do_tempo", "projecao_noite", "comparacao_1t", "abstencao",
    "secoes_ranking", "pesquisas_vs_urna", "paralela", "secoes", "secoes_voto", "hipotese_autor",
    "logs", "rdv", "metadados", "transferencia",
]  # fmt: skip
# CONTRATO.md, seção 2: rótulos obrigatórios por cena (trecho normalizado que o bloco precisa ter).
ROTULOS_POR_CENA = {
    "proj-primeiro-ponto": "nao e resultado nem previsao de vitoria",
    "paralela-177": "soma dos BUs recebidos nao projecao",
    "secoes-ranking": "atipicidade estatistica nao e irregularidade",
}
RESPIRO = 0.9
CAUDA = 3.0
PORTAO = (570.0, 660.0)
TRAVESSAO = chr(0x2014)
PROIBIDAS = ("fraud", "roubo de eleição", "eleição roubada")


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def dados() -> dict:
    return json.loads(DADOS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def roteiro() -> str:
    if not ROTEIRO.exists():
        pytest.skip("roteiro ainda não escrito")
    return ROTEIRO.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def blocos(roteiro: str) -> dict[str, str]:
    return _blocos(roteiro)


@pytest.fixture(scope="module")
def ordem() -> list[str]:
    texto = ORDEM_TS.read_text(encoding="utf-8").split("export const ORDEM", 1)[-1]
    return re.findall(r'\bid:\s*"([^"]+)"', texto.split("] as const", 1)[0])


@pytest.fixture(scope="module")
def voz() -> dict:
    dados_voz = json.loads(VOZ.read_text(encoding="utf-8"))
    if not dados_voz.get("cenas"):
        pytest.skip("voz.json ainda é o placeholder vazio")
    return dados_voz


# --------------------------------------------------------------------------- (a) ordem


def test_ordem_igual_ao_contrato(ordem: list[str]) -> None:
    assert ordem == IDS
    secao = CONTRATO.read_text(encoding="utf-8").split("## 1.", 1)[1].split("## 2.")[0]
    linhas = [x for x in secao.splitlines() if x.startswith("| `")]
    tabela = [i for x in linhas for i in re.findall(r"`([a-z0-9-]+)`", x.split("|")[2])]
    assert tabela == IDS


def test_capitulos_na_ordem_do_contrato() -> None:
    texto = ORDEM_TS.read_text(encoding="utf-8")
    bloco = texto.split("export const CAPITULOS_BASE", 1)[1].split("] as const", 1)[0]
    assert re.findall(r'\bid:\s*"([^"]+)"', bloco) == CAPITULOS
    cenas = texto.split("export const ORDEM", 1)[1]
    pares = re.findall(r'id:\s*"([^"]+)",\s*capitulo:\s*"([^"]+)"', cenas)
    assert [c for _, c in pares if c not in CAPITULOS] == []
    # Cada capítulo abre com o cartão `cap-*`, menos a abertura.
    for capitulo in CAPITULOS[1:]:
        primeira = next(i for i, c in pares if c == capitulo)
        assert primeira == f"cap-{capitulo}", capitulo


def test_registro_cobre_a_ordem(ordem: list[str]) -> None:
    registro = REGISTRO_TS.read_text(encoding="utf-8")
    chaves = set(re.findall(r'^\s{2}"?([a-z0-9-]+)"?:\s', registro, re.MULTILINE))
    assert not set(ordem) - chaves, sorted(set(ordem) - chaves)


def test_roteiro_na_ordem(blocos: dict[str, str], ordem: list[str]) -> None:
    assert list(blocos) == ordem


# --------------------------------------------------------------------------- (b) dados


def test_dados_esquema(dados: dict) -> None:
    for chave in ("gerado_em", "fontes", "pendentes", "avisos", "mapa"):
        assert chave in dados, chave
    prontos = [b for b in BLOCOS if b in dados]
    assert sorted(prontos + dados["pendentes"]) == sorted(BLOCOS)
    assert not set(prontos) & set(dados["pendentes"])
    assert len(dados["mapa"]["ufs"]) == 27
    assert all(u["d"].startswith("M") for u in dados["mapa"]["ufs"])


def test_fontes_do_json_batem_com_o_disco(dados: dict) -> None:
    assert dados["fontes"], "apuracao_2t.json sem nenhuma fonte registrada"
    for caminho, hash_gravado in dados["fontes"].items():
        arquivo = ROOT / caminho
        assert arquivo.exists(), caminho
        assert hashlib.sha256(arquivo.read_bytes()).hexdigest() == hash_gravado, caminho


def test_blocos_prontos_vem_do_arquivo_do_dossie(dados: dict) -> None:
    """Cada chave embutida é idêntica à do dossiê; o que faltar foi omitido e está em `avisos`."""
    for bloco in (b for b in BLOCOS if b in dados):
        fonte = ROOT / "analysis" / "apuracao_2t_2026" / "dados" / f"{bloco}.json"
        original = json.loads(fonte.read_text(encoding="utf-8"))
        embutido = dados[bloco]
        _conferir_embutido(f"{bloco}", original, embutido, dados["avisos"])


def _conferir_embutido(
    prefixo: str, original: dict, embutido: dict, avisos: list
) -> None:
    """Chave embutida igual à original, ou dicionário enxugado um nível abaixo (subchaves iguais
    e as que faltam avisadas); chave ausente precisa de aviso."""
    for chave, valor in embutido.items():
        if original[chave] != valor:
            assert isinstance(valor, dict) and isinstance(
                original[chave], dict
            ), f"{prefixo}.{chave}"
            _conferir_embutido(f"{prefixo}.{chave}", original[chave], valor, avisos)
    for chave in set(original) - set(embutido):
        assert any(
            a.startswith(f"{prefixo}.{chave}:") for a in avisos
        ), f"{prefixo}.{chave} omitida sem aviso"


def _caminhos_do_registro() -> list[str]:
    registro = REGISTRO_TS.read_text(encoding="utf-8")
    return sorted(set(re.findall(r'\bdado:\s*"([a-z_0-9.\[\]]+)"', registro)))


def test_caminhos_do_registro_resolvem_nos_blocos_prontos(dados: dict) -> None:
    """Todo `dado:` do registro aponta para um valor que existe; bloco pendente fica de fora."""
    erros = []
    for caminho in _caminhos_do_registro():
        if caminho.split(".")[0].split("[")[0] not in dados:
            continue
        try:
            _resolver(dados, caminho)
        except (KeyError, IndexError, TypeError) as erro:
            erros.append(f"{caminho}: {erro.args[0] if erro.args else erro}")
    assert not erros, "\n".join(erros)


def test_colunas_das_series_existem(dados: dict) -> None:
    registro = REGISTRO_TS.read_text(encoding="utf-8")
    achados = re.findall(
        r'dado:\s*"([^"]+)",\s*xCampo:\s*"([^"]+)",\s*yCampo:\s*"([^"]+)"', registro
    )
    assert achados, "registro sem nenhuma série com xCampo e yCampo"
    for caminho, x, y in achados:
        if caminho.split(".")[0] not in dados:
            continue
        alvo = _resolver(dados, caminho)
        if isinstance(alvo, dict) and "colunas" in alvo:
            colunas = set(alvo["colunas"])
        else:
            assert alvo, caminho
            colunas = set(alvo[0])
        assert {x, y} <= colunas, f"{caminho}: {x}/{y} fora de {sorted(colunas)}"


# --------------------------------------------------------------------------- (c) roteiro


def test_roteiro_sem_travessao_nem_palavra_proibida(roteiro: str) -> None:
    assert TRAVESSAO not in roteiro
    for palavra in PROIBIDAS:
        assert palavra not in roteiro.lower(), palavra
    hashtags = re.findall(r"(?<![#\w])#[^\s#]+", COMENTARIO.sub("", roteiro))
    assert not hashtags, f"hashtag no roteiro: {hashtags}"


def test_narracao_sem_algarismos(blocos: dict[str, str]) -> None:
    erros = [
        f"{cena}: {linha.strip()[:80]}"
        for cena, bloco in blocos.items()
        for linha in COMENTARIO.sub("", bloco).splitlines()
        if not linha.lstrip().startswith("#") and re.search(r"\d", linha)
    ]
    assert not erros, "\n".join(erros)


@pytest.mark.skipif(
    not video_publicado(),
    reason="vídeo em produção: números narrados são conferidos contra os JSONs na publicação",
)
def test_cada_dado_bate_e_aparece_por_extenso(
    dados: dict, blocos: dict[str, str]
) -> None:
    erros = []
    total = 0
    for cena, bloco in blocos.items():
        narrado = _narrado(bloco)
        for dado in DADO.findall(bloco):
            total += 1
            erros.extend(_conferir_dado(dados, cena, dado, narrado))
    assert total, "roteiro sem nenhum comentário de dado"
    assert not erros, "\n".join(erros)


def test_rotulos_obrigatorios_por_cena(blocos: dict[str, str]) -> None:
    for cena, trecho in ROTULOS_POR_CENA.items():
        narrado = _normalizar(TAG.sub(" ", _narrado(blocos.get(cena, ""))))
        assert _normalizar(trecho) in narrado, f"{cena} sem o rótulo: {trecho}"


# --------------------------------------------------------------------------- (e) fontes externas


def test_fontes_citadas_existem(roteiro: str) -> None:
    citadas = {f.strip() for f in FONTE.findall(roteiro)}
    if not citadas:
        pytest.skip("roteiro sem fonte externa citada")
    if not FONTES_MD.exists():
        pytest.skip("roteiro/fontes.md ainda não escrito")
    texto = FONTES_MD.read_text(encoding="utf-8")
    ancoras = set(re.findall(r"""(?:id|name)=["']([^"']+)["']""", texto))
    ancoras |= set(re.findall(r"\{#([^}\s]+)\}", texto))
    for titulo in re.findall(r"^#+\s+(.+?)\s*$", texto, re.MULTILINE):
        limpo = re.sub(r"\{#[^}]*\}", "", titulo).strip().strip("`")
        ancoras.add(limpo)
        ancoras.add(limpo.split()[0].strip("`:") if limpo else limpo)
        ancoras.add(re.sub(r"[^a-z0-9]+", "-", _normalizar(limpo).strip()).strip("-"))
    faltam = sorted(citadas - ancoras)
    assert not faltam, f"fontes citadas sem entrada em fontes.md: {faltam}"


# --------------------------------------------------------------------------- (f, g) voz e duração


def test_voz_cobre_a_ordem(voz: dict, ordem: list[str]) -> None:
    assert [c["id"] for c in voz["cenas"]] == ordem
    for c in voz["cenas"]:
        assert c["segundos"] > 2, c["id"]
        assert c["palavras"] and c["palavras"][-1]["f"] <= c["segundos"] + 0.5, c["id"]
        assert (VIDEO / "public" / c["arquivo"]).exists(), c["arquivo"]


def test_portao_de_duracao(voz: dict) -> None:
    n = len(voz["cenas"])
    total = sum(c["segundos"] for c in voz["cenas"]) + RESPIRO * (n - 1) + CAUDA
    assert PORTAO[0] <= total <= PORTAO[1], f"{total:.0f} s fora de {PORTAO}"


def test_portao_configurado_no_projeto() -> None:
    linha = LINHA_TS.read_text(encoding="utf-8")
    achado = re.search(r"PORTAO = \{ minimo: (\d+), maximo: (\d+) \}", linha)
    assert achado, "PORTAO não encontrado em linha.ts"
    assert (float(achado[1]), float(achado[2])) == PORTAO
    assert "570 a 660" in CONTRATO.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- (h) mídia


def _ids_de_midia(registro: str) -> set[str]:
    ids: set[str] = set()
    for inicio in re.finditer(r"\bmidia\s*:\s*\[([^\]]*)\]", registro):
        ids.update(re.findall(r'"([^"]+)"', inicio[1]))
    return ids


def test_midia_do_registro_existe() -> None:
    midia = json.loads(MIDIA.read_text(encoding="utf-8"))
    capturas = json.loads(CAPTURAS.read_text(encoding="utf-8"))
    usados = _ids_de_midia(REGISTRO_TS.read_text(encoding="utf-8"))
    assert usados, "registro sem nenhuma mídia declarada"
    faltam = sorted(
        i
        for i in usados
        if i not in midia
        and i not in capturas
        and i.removeprefix("cap_") not in capturas
    )
    assert not faltam, f"mídia citada no registro sem entrada: {faltam}"


def test_telas_do_telao_registradas() -> None:
    capturas = json.loads(CAPTURAS.read_text(encoding="utf-8"))
    telas = {k: v for k, v in capturas.items() if v.get("origem") == "telao"}
    if not telas:
        pytest.skip(
            "telas do telão ainda não copiadas (scripts/video-apuracao-2t-capturas.py)"
        )
    for ident, entrada in telas.items():
        assert entrada["formatos"] == ["16x9"], ident
        origem = ROOT / entrada["fonte"]
        if origem.exists():
            assert (
                hashlib.sha256(origem.read_bytes()).hexdigest() == entrada["sha256"]
            ), ident
