"""Vídeo masterclass (video/masterclass): ordem das cenas, dados do Remotion contra as fontes,
roteiro com números por extenso conferidos contra `masterclass.json`, voz e portão de duração.

Os testes que dependem de um arquivo ainda não gerado (roteiro, voz, mídia) são pulados até
o arquivo existir; os placeholders vazios do esqueleto contam como ausentes."""

from __future__ import annotations

import importlib
import json
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video" / "masterclass"
DADOS = VIDEO / "src" / "dados" / "masterclass.json"
VOZ = VIDEO / "src" / "dados" / "voz.json"
MIDIA = VIDEO / "src" / "dados" / "midia.json"
CAPTURAS = VIDEO / "src" / "dados" / "capturas.json"
ORDEM_TS = VIDEO / "src" / "ordem.ts"
REGISTRO_TS = VIDEO / "src" / "cenas" / "registro.ts"
ROTEIRO = VIDEO / "roteiro" / "roteiro.md"
FONTES_MD = VIDEO / "roteiro" / "fontes.md"
CONTRATO = VIDEO / "CONTRATO.md"

# CONTRATO.md, seção 1: a tabela lista 37 cenas (o texto do contrato diz 33, contagem antiga).
IDS = [
    "abertura", "tese",
    "cap-sopa", "sopa-panela", "sopa-concha", "sopa-regua", "sopa-conchas-reais", "sopa-moral",
    "cap-urna", "urna-resultado", "urna-erro", "urna-reponderado", "urna-efeito-casa",
    "urna-virada",
    "cap-depois", "depois-contagem-publica", "depois-fiscais", "depois-totalizacao",
    "depois-politize",
    "cap-riscos", "risco-sinais", "risco-pianista", "risco-biometria", "risco-urna-trocada",
    "risco-horarios", "risco-boca-de-urna", "risco-territorio", "risco-conferir-arquivo",
    "risco-fiscal-fica",
    "cap-mapa", "mapa-busca", "mapa-predio-rj", "mapa-predio-sp", "mapa-zoom",
    "cap-fecho", "fecho-argentina", "fecho-chamada",
]  # fmt: skip
EXEMPLOS = {
    "puc_sp", "marau_rs", "sao_joao_missoes_mg", "tabatinga_am", "nova_andradina_ms",
    "baiao_pa", "porto_acre_ac", "teixeira_freitas_ba", "serra_es", "iranduba_am",
    "oiapoque_ap",
}  # fmt: skip
PREDIOS = ["RJ-60011-233-1414", "SP-71072-372-2020"]
FRASES_DA_CASA = (
    "Atipicidade estatística não é irregularidade.",
    "A lista é de prioridade de fiscalização, não de acusação.",
    "O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.",
)
RESPIRO = 0.9
CAUDA = 3.0
PORTAO = (840.0, 930.0)
PROIBIDO_DE = 750.0
TRAVESSAO = "\u2014"

COMENTARIO = re.compile(r"<!--.*?-->", re.DOTALL)
TAG = re.compile(r"\[[a-z ]+\]")
DADO = re.compile(r"<!--\s*dado:\s*(.*?)\s*-->", re.DOTALL)
FONTE = re.compile(r"<!--\s*fonte:\s*(.*?)\s*-->", re.DOTALL)


# --------------------------------------------------------------------------- números por extenso

UNIDADES = (
    "zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez",
    "onze", "doze", "treze", "catorze", "quinze", "dezesseis", "dezessete", "dezoito",
    "dezenove",
)  # fmt: skip
DEZENAS = ("", "", "vinte", "trinta", "quarenta", "cinquenta", "sessenta", "setenta",
           "oitenta", "noventa")  # fmt: skip
CENTENAS = ("", "cento", "duzentos", "trezentos", "quatrocentos", "quinhentos", "seiscentos",
            "setecentos", "oitocentos", "novecentos")  # fmt: skip


def _ate_mil(n: int, feminino: bool = False) -> str:
    """1 a 999 por extenso; `feminino` concorda um, dois e as centenas (duzentas...)."""
    if n == 100:
        return "cem"
    centena, resto = divmod(n, 100)
    partes = []
    if centena:
        nome = CENTENAS[centena]
        partes.append(nome[:-2] + "as" if feminino and centena >= 2 else nome)
    if resto:
        dezena, unidade = divmod(resto, 10)
        if resto < 20:
            partes.append(UNIDADES[resto])
        else:
            partes.append(
                DEZENAS[dezena] + (f" e {UNIDADES[unidade]}" if unidade else "")
            )
    texto = " e ".join(partes)
    if feminino:
        texto = re.sub(r"\bum\b", "uma", texto)
        texto = re.sub(r"\bdois\b", "duas", texto)
    return texto


def _extenso_inteiro(n: int, feminino_mil: bool = False, feminino: bool = False) -> str:
    """0 a 999 999 999 por extenso, com o "e" antes do último grupo quando ele é menor que cem
    ou centena redonda. Milhão é masculino; o milhar e a unidade concordam com o substantivo.
    """
    if not 0 <= n < 1_000_000_000:
        raise ValueError(n)
    if n == 0:
        return "zero"
    milhoes, resto = divmod(n, 1_000_000)
    milhares, unidades = divmod(resto, 1000)
    grupos = []
    if milhoes:
        grupos.append("um milhão" if milhoes == 1 else f"{_ate_mil(milhoes)} milhões")
    if milhares:
        grupos.append(
            "mil" if milhares == 1 else f"{_ate_mil(milhares, feminino_mil)} mil"
        )
    if unidades:
        grupos.append(_ate_mil(unidades, feminino))
    if len(grupos) > 1 and unidades and (unidades < 100 or unidades % 100 == 0):
        return " ".join(grupos[:-1]) + " e " + grupos[-1]
    return " ".join(grupos)


def _extenso(valor: float | int | Decimal | str, feminino: bool = False) -> str:
    """Forma por extenso: inteiros até 999 999 999 e decimais "X vírgula Y" (uma ou duas casas,
    "zero sete" quando a segunda casa vem depois de um zero). Sinal ignorado: a narração diz
    "mais" ou "menos" com palavras."""
    numero = abs(Decimal(str(valor)))
    inteiro = int(numero)
    texto = _extenso_inteiro(inteiro, feminino, feminino)
    casas = format(numero.normalize(), "f").partition(".")[2]
    if not casas:
        return texto
    if len(casas) > 2:
        raise ValueError(f"mais de duas casas: {valor}")
    if len(casas) == 2 and casas[0] == "0":
        return f"{texto} vírgula zero {UNIDADES[int(casas[1])]}"
    return f"{texto} vírgula {_extenso_inteiro(int(casas))}"


def _normalizar(texto: str) -> str:
    """Minúsculas, sem acento, sem pontuação e sem o conectivo "e"; quatorze vira catorze."""
    texto = "".join(
        c
        for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )
    palavras = re.sub(r"[^a-z0-9]+", " ", texto).split()
    palavras = ["catorze" if p == "quatorze" else p for p in palavras if p != "e"]
    return " " + " ".join(palavras) + " "


def _arredondado(valor: float | int, casas: int) -> Decimal:
    return Decimal(str(valor)).quantize(
        Decimal(1).scaleb(-casas), rounding=ROUND_HALF_UP
    )


def _arredondamentos(valor: float | int) -> set[Decimal]:
    return {_arredondado(valor, k).normalize() for k in (0, 1, 2)} | (
        {Decimal(valor)} if isinstance(valor, int) else set()
    )


def _formas(valor: float | int) -> set[str]:
    """Formas narradas aceitas para um número do JSON: arredondado a 0, 1 ou 2 casas, nos dois
    gêneros, e para números grandes também em milhares redondos e em "X vírgula Y milhões".
    """
    formas: set[str] = set()
    for alvo in _arredondamentos(valor):
        if alvo == alvo.to_integral_value():
            n = abs(int(alvo))
            for fm in (False, True):
                for fu in (False, True):
                    formas.add(_extenso_inteiro(n, fm, fu))
        else:
            formas.update(_extenso(alvo, f) for f in (False, True))
    n = abs(int(valor)) if float(valor).is_integer() else 0
    if n >= 10_000:
        redondo = int(_arredondado(n, -3))
        for fm in (False, True):
            formas.add(_extenso_inteiro(redondo, fm, fm))
        for k in (0, 1):
            formas.add(_extenso(_arredondado(n / 1000, k).normalize()) + " mil")
    if n >= 1_000_000:
        for k in (0, 1, 2):
            m = _arredondado(n / 1_000_000, k).normalize()
            formas.add(_extenso(m) + (" milhão" if m == 1 else " milhões"))
    return {_normalizar(f) for f in formas}


# --------------------------------------------------------------------------- roteiro


def _blocos(texto: str) -> dict[str, str]:
    """Blocos `## id` do roteiro, com o texto cru (comentários e tags incluídos)."""
    blocos: dict[str, str] = {}
    atual: str | None = None
    for linha in texto.splitlines():
        if linha.startswith("## "):
            atual = linha[3:].strip()
            blocos[atual] = ""
        elif atual is not None:
            blocos[atual] += linha + "\n"
    return blocos


def _narrado(bloco: str) -> str:
    return TAG.sub(" ", COMENTARIO.sub(" ", bloco))


def _separar(dado: str) -> tuple[str, str]:
    """Separa `caminho = valor` no primeiro "=" fora de colchetes."""
    profundidade = 0
    for i, c in enumerate(dado):
        profundidade += {"[": 1, "]": -1}.get(c, 0)
        if c == "=" and profundidade == 0:
            return dado[:i].strip(), dado[i + 1 :].strip()
    raise AssertionError(f"comentário de dado sem '=': {dado}")


TOKEN = re.compile(r"\.?([^.\[\]]+)|\[([^\]]+)\]")


def _resolver(dados: object, caminho: str) -> object:
    """Pontos para objetos, `[i]` para listas, `[campo=valor]` para o primeiro item com esse
    campo e `.length` para o tamanho de uma lista."""
    atual = dados
    for nome, colchete in TOKEN.findall(caminho):
        if nome:
            if nome == "length" and isinstance(atual, (list, str)):
                atual = len(atual)
            elif isinstance(atual, dict) and nome in atual:
                atual = atual[nome]
            elif isinstance(atual, list) and nome.isdigit():
                atual = atual[int(nome)]
            else:
                raise KeyError(f"{caminho}: '{nome}' não existe")
        elif colchete.lstrip("-").isdigit():
            atual = atual[int(colchete)]
        else:
            campo, valor = colchete.split("=", 1)
            achados = [x for x in atual if str(x.get(campo)) == valor]
            if not achados:
                raise KeyError(f"{caminho}: nenhum item com {campo}={valor}")
            atual = achados[0]
    return atual


def _numero(texto: str) -> float:
    return (
        float(texto.replace(",", "."))
        if "," in texto and "." not in texto
        else float(texto)
    )


def _conferir_dado(dados: dict, cena: str, dado: str, narrado: str) -> list[str]:
    caminho, comentado = _separar(dado)
    try:
        valor = _resolver(dados, caminho)
    except (KeyError, IndexError, TypeError) as erro:
        return [f"{cena}: {erro.args[0] if erro.args else erro}"]
    texto = _normalizar(narrado)
    erros = []
    if isinstance(valor, bool) or valor is None:
        if comentado.lower() != json.dumps(valor):
            erros.append(f"{cena}: {caminho} = {valor}, comentário diz {comentado}")
    elif isinstance(valor, (int, float)):
        try:
            numero = _numero(comentado)
        except ValueError:
            return [f"{cena}: {caminho} comentado como '{comentado}', não é número"]
        aceitos = {_arredondado(valor, k) for k in (0, 1, 2)}
        if numero != valor and not any(Decimal(str(numero)) == a for a in aceitos):
            erros.append(
                f"{cena}: {caminho} = {valor} no JSON, comentário diz {comentado}"
            )
        elif not any(f in texto for f in _formas(valor)):
            erros.append(
                f"{cena}: {caminho} = {valor} não aparece por extenso no bloco"
            )
    elif isinstance(valor, str):
        if _normalizar(comentado).strip() not in _normalizar(valor):
            erros.append(
                f"{cena}: {caminho} = '{valor}' no JSON, comentário diz '{comentado}'"
            )
        elif hora := re.fullmatch(r"(\d{1,2}):(\d{2})", valor):
            h, m = int(hora[1]), int(hora[2])
            horas = {_normalizar(_extenso_inteiro(x, True, f)) for x in {h, h % 12 or 12}
                     for f in (False, True)}  # fmt: skip
            minutos = {_normalizar(_extenso_inteiro(m))} if m else {" "}
            if not (
                any(x in texto for x in horas) and any(x in texto for x in minutos)
            ):
                erros.append(
                    f"{cena}: {caminho} = {valor} não aparece por extenso no bloco"
                )
        elif numeros := re.findall(r"\d+(?:[.,]\d+)?", valor):
            if not any(
                f in texto
                for n in numeros
                for f in _formas(int(n) if n.isdigit() else _numero(n))
            ):
                erros.append(
                    f"{cena}: {caminho} = '{valor}' sem número por extenso no bloco"
                )
        elif _normalizar(valor) not in texto:
            erros.append(f"{cena}: {caminho} = '{valor}' não aparece no bloco")
    return erros


# --------------------------------------------------------------------------- fixtures


@pytest.fixture(scope="module")
def dados() -> dict:
    if not DADOS.exists():
        pytest.skip("masterclass.json não gerado")
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
    if not ORDEM_TS.exists():
        pytest.skip("src/ordem.ts ausente")
    texto = ORDEM_TS.read_text(encoding="utf-8").split("export const ORDEM", 1)[-1]
    return re.findall(r'\bid:\s*"([^"]+)"', texto.split("] as const", 1)[0])


@pytest.fixture(scope="module")
def voz() -> dict:
    if not VOZ.exists():
        pytest.skip("narração não gerada")
    dados_voz = json.loads(VOZ.read_text(encoding="utf-8"))
    if not dados_voz.get("cenas"):
        pytest.skip("voz.json ainda é o placeholder vazio")
    return dados_voz


def _ler(caminho: Path) -> dict:
    return json.loads((ROOT / caminho).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- (a) ordem


def test_extenso_por_extenso() -> None:
    assert _extenso(2224965) == (
        "dois milhões duzentos e vinte e quatro mil novecentos e sessenta e cinco"
    )
    assert _extenso(499248, feminino=True) == (
        "quatrocentas e noventa e nove mil duzentas e quarenta e oito"
    )
    assert _extenso(1000) == "mil"
    assert _extenso(1_000_100) == "um milhão e cem"
    assert _extenso(3.55) == "três vírgula cinquenta e cinco"
    assert _extenso(-1.07) == "um vírgula zero sete"
    assert _extenso(0.88) == "zero vírgula oitenta e oito"
    assert _extenso(21, feminino=True) == "vinte e uma"
    assert _normalizar("cento e cinquenta e sete vírgula oito milhões") in _formas(
        157_846_602
    )


def test_ordem_igual_ao_contrato(ordem: list[str]) -> None:
    assert ordem == IDS
    if CONTRATO.exists():
        secao = (
            CONTRATO.read_text(encoding="utf-8").split("## 1.", 1)[1].split("## 2.")[0]
        )
        linhas = [x for x in secao.splitlines() if x.startswith("| `")]
        tabela = [
            i for x in linhas for i in re.findall(r"`([a-z0-9-]+)`", x.split("|")[2])
        ]
        assert tabela == IDS


def test_roteiro_na_ordem(blocos: dict[str, str], ordem: list[str]) -> None:
    assert list(blocos) == ordem


# --------------------------------------------------------------------------- (b) dados


def test_urna_bate_com_presidente(dados: dict) -> None:
    pres = _ler(Path("analysis/apuracao_2026/dados/presidente.json"))
    n = pres["nacional"]
    u = dados["urna"]
    assert u["flavio_pct"] == round(n["pct"]["flavio"], 2) == 47.03
    assert u["lula_pct"] == round(n["pct"]["lula"], 2) == 45.16
    assert u["diferenca_pp"] == round(n["diferenca_pp"], 2)
    for chave in (
        "diferenca_votos",
        "validos",
        "brancos",
        "nulos",
        "secoes",
        "eleitores",
    ):
        assert u[chave] == n[chave], chave
    assert u["comparecimento"] == n["comparecimento"]
    assert u["comparecimento_pct"] == round(n["pct_comparecimento"], 2)
    brasil = pres["regioes"]["Brasil sem exterior"]["r2026"]
    assert u["comparecimento_brasil_pct"] == round(brasil["pct_comparecimento"], 2)
    for nome in ("cury", "renan", "caiado"):
        assert u[f"{nome}_pct"] == round(n["pct"][nome], 2)


def test_erro_resumo_bate_com_a_urna(dados: dict) -> None:
    fonte = _ler(Path("docs/assets/reponderacao_urna_1t.json"))
    pub, rep = fonte["resumo"]["publicado"], fonte["resumo"]["reponderado"]
    e = dados["erro_resumo"]
    assert (e["n_pub"], e["mais_lula"], e["fora_margem"]) == (
        pub["n"],
        pub["positivos"],
        pub["fora_da_margem_aas"],
    )
    assert e["media_pub_pp"] == round(pub["media"], 2)
    assert e["mediana_pub_pp"] == round(pub["mediana"], 2)
    assert e["n_rep"] == rep["n"]
    assert e["media_rep_pp"] == round(rep["media"], 2)
    assert e["mediana_rep_pp"] == round(rep["mediana"], 2)
    for chave in ("aproximou", "afastou", "neutro"):
        assert e[chave] == fonte["efeito_pareado"][chave]
    assert e["correlacao_casa_erro"] == round(
        fonte["resumo"]["correlacao_efeito_casa_pre_eleicao_com_erro"], 2
    )
    assert len(dados["pesquisas_1t"]) == pub["n"]
    assert sum(p["reponderado"] is not None for p in dados["pesquisas_1t"]) == rep["n"]
    erro22 = ROOT / "analysis" / "predicao_2026" / "erro_2022" / "erro_2022.json"
    if erro22.exists():
        comum = _ler(erro22.relative_to(ROOT))["media_das_casas"]
        assert e["erro_comum_2022_pp"] == round(
            comum["erro_comum_diferenca_lula_menos_bolsonaro"], 2
        )


def test_concha_destaques_recalculados(dados: dict) -> None:
    pnad = _ler(Path("docs/assets/reponderacao_pnad.json"))
    # Recalcula as ondas efetivamente usadas no vídeo congelado, inclusive quando
    # uma publicação anterior ao corte só foi arquivada posteriormente.
    ids_publicados = {p["id"] for p in dados["concha"]}
    pnad["pesquisas"] = [p for p in pnad["pesquisas"] if p["id"] in ids_publicados]
    modulo = importlib.import_module("video-masterclass-dados")
    concha, destaques = modulo.bloco_concha(pnad, modulo.Fontes())
    assert destaques == dados["concha_destaques"]
    assert concha == dados["concha"]
    pobre, rica = destaques["mais_pobre"], destaques["mais_rica"]
    assert pobre["desvio_pp"] > 0 > rica["desvio_pp"]
    for d in (pobre, rica):
        assert d["desvio_pp"] == pytest.approx(
            d["amostra_pct"] - d["pnad_pct"], abs=0.011
        )
        onda = next(p for p in pnad["pesquisas"] if p["id"] == d["id"])
        bruto = _ler(Path(onda["arquivo"]))["renda"]["faixas"]
        ate2 = [
            v
            for v, f in zip(onda["renda"]["amostra_pct"], bruto, strict=True)
            if f["max"] is not None and f["max"] <= 2
        ]
        assert d["amostra_pct"] == round(sum(ate2), 2)
    primeiras = [c["desvio_pp"][0] for c in dados["concha"] if c["agregado_sm"]]
    assert pobre["desvio_pp"] == max(primeiras)
    assert rica["desvio_pp"] == min(primeiras)


def test_tse_bate_com_o_perfil(dados: dict) -> None:
    bench = _ler(Path("data/outputs/tse_eleitorado_perfil_benchmark.json"))
    sexo = bench["poll_universe_brazil_excluding_exterior"]["gender_binary"]
    assert dados["tse"]["sexo"] == [
        {"rotulo": "Mulheres", "pct": round(sexo["Mulher"]["pct"], 2)},
        {"rotulo": "Homens", "pct": round(sexo["Homem"]["pct"], 2)},
    ]
    assert dados["tse"]["eleitores_brasil"] == int(
        bench["metadata"]["total_eleitores_brasil_sem_exterior"]
    )
    assert round(sum(x["pct"] for x in dados["tse"]["idade"]), 0) == 100


def test_exemplos_predios_e_fontes(dados: dict) -> None:
    assert set(dados["exemplos"]) == EXEMPLOS
    for chave, e in dados["exemplos"].items():
        assert e["aptos"] >= e["votantes"] > 0, chave
        assert e["atencao"] in (None, 0, 1, 2, 3), chave
    assert [p["local_id"] for p in dados["predios"]] == PREDIOS
    for p in dados["predios"]:
        assert p["secoes_listadas"] == len(p["secoes"]) <= p["secoes_total"]
        assert sum(p["por_atencao"].values()) + p["sem_log"] == p["secoes_listadas"]
    assert len(dados["criterios"]) == 12
    for caminho, sha in dados["fontes"].items():
        assert (ROOT / caminho).exists(), caminho
        assert re.fullmatch(r"[0-9a-f]{64}", sha), caminho


# --------------------------------------------------------------------------- (c) roteiro


def test_roteiro_sem_travessao_nem_palavra_proibida(roteiro: str) -> None:
    assert TRAVESSAO not in roteiro
    assert "fraud" not in roteiro.lower()
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


# --------------------------------------------------------------------------- (d) links e frases


def test_links_falados_e_frases_da_casa(roteiro: str, blocos: dict[str, str]) -> None:
    assert "fiscais do PL ponto com ponto br" in roteiro
    assert "brasil ponto arvor ponto co" in roteiro
    for cena in ("risco-sinais", "fecho-chamada"):
        texto = _normalizar(_narrado(blocos.get(cena, "")))
        for frase in FRASES_DA_CASA:
            assert _normalizar(frase) in texto, f"{cena} sem: {frase}"


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
        slug = re.sub(r"[^a-z0-9]+", "-", _normalizar(limpo).strip()).strip("-")
        ancoras.add(slug)
    faltam = sorted(citadas - ancoras)
    assert not faltam, f"fontes citadas sem entrada em fontes.md: {faltam}"


# --------------------------------------------------------------------------- (f, g) voz e duração


def test_voz_cobre_a_ordem(voz: dict, ordem: list[str]) -> None:
    assert [c["id"] for c in voz["cenas"]] == ordem
    for c in voz["cenas"]:
        assert c["segundos"] > 3, c["id"]
        assert c["palavras"] and c["palavras"][-1]["f"] <= c["segundos"] + 0.5, c["id"]
        assert (VIDEO / "public" / c["arquivo"]).exists(), c["arquivo"]


def test_portao_de_duracao(voz: dict) -> None:
    n = len(voz["cenas"])
    total = sum(c["segundos"] for c in voz["cenas"]) + RESPIRO * (n - 1) + CAUDA
    assert not PROIBIDO_DE < total < PORTAO[0], (
        f"{total:.0f} s ({total / 60:.1f} min): 13 minutos é proibido, o vídeo tem de ter "
        "de 14 a 15 minutos e meio"
    )
    assert PORTAO[0] <= total <= PORTAO[1], f"{total:.0f} s fora de [840, 930]"


# --------------------------------------------------------------------------- (h) mídia


def _ids_de_midia(registro: str) -> set[str]:
    ids: set[str] = set()
    for inicio in re.finditer(r"\bmidia\s*:\s*", registro):
        resto = registro[inicio.end() :]
        if resto.startswith('"'):
            trecho = resto[: resto.index('"', 1) + 1]
        else:
            abre, fecha = ("[", "]") if resto.startswith("[") else ("{", "}")
            profundidade = 0
            for i, c in enumerate(resto):
                profundidade += (c == abre) - (c == fecha)
                if profundidade == 0:
                    trecho = resto[: i + 1]
                    break
            else:
                trecho = resto
        ids.update(
            x
            for x in re.findall(r'"([^"]+)"', trecho)
            if re.fullmatch(r"[a-z0-9_]+", x)
        )
    return ids


def test_midia_do_registro_existe() -> None:
    if not (REGISTRO_TS.exists() and MIDIA.exists() and CAPTURAS.exists()):
        pytest.skip("registro, midia.json ou capturas.json ausente")
    midia = json.loads(MIDIA.read_text(encoding="utf-8"))
    capturas = json.loads(CAPTURAS.read_text(encoding="utf-8"))
    if not midia and not capturas:
        pytest.skip("midia.json e capturas.json ainda são placeholders vazios")
    usados = _ids_de_midia(REGISTRO_TS.read_text(encoding="utf-8"))
    faltam = sorted(
        i
        for i in usados
        if i not in midia and i not in capturas and i[4:] not in capturas
    )
    assert not faltam, f"mídia citada no registro sem arquivo gerado: {faltam}"
