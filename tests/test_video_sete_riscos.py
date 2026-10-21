"""Vídeo "Sete riscos, um fiscal" (video/sete_riscos): ordem das cenas, dados do Remotion
contra as fontes, roteiro com números por extenso conferidos contra `sete_riscos.json`, voz,
portão de duração e mídia.

Os testes que dependem de um arquivo ainda não entregue (roteiro, voz, mídia) são pulados até
o arquivo existir; o roteiro copiado da masterclass, sem os ids da ordem nova, e os
placeholders vazios do esqueleto contam como ausentes."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import unicodedata
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VIDEO = ROOT / "video" / "sete_riscos"
DADOS = VIDEO / "src" / "dados" / "sete_riscos.json"
VOZ = VIDEO / "src" / "dados" / "voz.json"
MIDIA = VIDEO / "src" / "dados" / "midia.json"
CAPTURAS = VIDEO / "src" / "dados" / "capturas.json"
ORDEM_TS = VIDEO / "src" / "ordem.ts"
REGISTROS_TS = (
    VIDEO / "src" / "cenas" / "registro.ts",
    VIDEO / "src" / "cenas" / "registro_b.ts",
)
ROTEIRO = VIDEO / "roteiro" / "roteiro.md"
FONTES_MD = VIDEO / "roteiro" / "fontes.md"
CONTRATO = VIDEO / "CONTRATO.md"
FONTES_FISCAIS = ROOT / "analysis" / "apuracao_2026" / "fontes_fiscais.json"

# CONTRATO.md, seção 1: 20 cenas.
IDS = [
    "abertura", "tese",
    "cap-lei", "lei-poderes", "lei-postura",
    "cap-riscos", "risco-boca-de-urna", "risco-compra", "risco-transporte", "risco-medo",
    "risco-mesario", "risco-pianista", "risco-totalizacao",
    "cap-fechamento", "fecha-ultimos", "fecha-totalizacao",
    "cap-mapa", "mapa-fiscais", "mapa-cadastro",
    "fecho-chamada",
]  # fmt: skip
# CONTRATO.md, seção 3: risco, cena, cenário, casos (o primeiro é o principal) e lei.
RISCOS = [
    ("boca_urna", "risco-boca-de-urna", "boca_urna",
     ["paulista_pe_2020", "mj_1t_2024"], ["l9504_39_p5", "l9504_39a"]),
    ("compra", "risco-compra", "compra",
     ["jackson_lago_2009", "mj_1t_2024"], ["l9504_41a", "ce_299"]),
    ("transporte", "risco-transporte", "transporte",
     ["hornung_reserva_2004", "anchieta_sc_2012", "mj_1t_2024"], ["l6091_11", "l6091_5"]),
    ("medo", "risco-medo", "medo",
     ["santa_quiteria_ce_faccao_2024", "trerj_locais_votacao_milicia_2024"],
     ["ce_301", "ce_23_xiv"]),
    ("mesario", "risco-mesario", "mesario",
     ["itumbiara_2018", "paulista_pe_2020"], ["ce_309", "ce_132"]),
    ("pianista", "risco-pianista", "pianista",
     ["pescaria_brava_2016", "doppelganger_macapa_2024"], ["ce_309", "res_23751_senhas"]),
    ("totalizacao", "risco-totalizacao", "apuracao_papel",
     ["proconsult_rj_1982", "rj_1994_proporcional_anulada"],
     ["l9504_68", "res_23751_bu", "l9504_66"]),
]  # fmt: skip
EXEMPLOS = {
    "tabatinga_am": ("AM", 36, 30),
    "baiao_pa": ("PA", 35, 238),
    "puc_sp": ("SP", 1, 257),
    "sao_joao_missoes_mg": ("MG", 166, 267),
    "marau_rs": ("RS", 62, 15),
    "porto_acre_ac": ("AC", 1, 621),
}
CHAVES_EXEMPLO = {
    "uf", "municipio", "zona", "secao", "local", "bairro", "aptos", "votantes",
    "comparecimento_pct", "lula_pct", "flavio_pct", "nivel", "criterios", "explicacao",
    "logs", "atencao", "o_que_conferir",
}  # fmt: skip
CHAVES_FRENTE = {
    "uf", "municipio", "zona", "secao", "aptos", "votantes", "comparecimento_pct",
    "lula_pct", "flavio_pct", "nivel", "criterios", "explicacao",
}  # fmt: skip
PREDIOS = ["RJ-60011-233-1414"]
LEI_FISCAL = ["fiscalizar", "dois", "credencial", "impugnar", "copia", "ate_a_junta"]
FECHAMENTO = [
    "senhas",
    "ultimos_dois",
    "bu_afixado",
    "copia_no_encerramento",
    "comparar_depois",
]
FRASES_DA_CASA = (
    "Atipicidade estatística não é irregularidade.",
    "A lista é de prioridade de fiscalização, não de acusação.",
    "O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal.",
)
RESPIRO = 0.9
CAUDA = 3.0
PORTAO = (540.0, 690.0)
TRAVESSAO = chr(0x2014)
PROIBIDAS = ("fraud", "roubo de eleição", "eleição roubada")

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
        pytest.skip("sete_riscos.json não gerado")
    dados_json = json.loads(DADOS.read_text(encoding="utf-8"))
    if not dados_json.get("riscos"):
        pytest.skip("sete_riscos.json ainda é o placeholder do esqueleto")
    return dados_json


@pytest.fixture(scope="module")
def fontes_fiscais() -> dict:
    return json.loads(FONTES_FISCAIS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def roteiro() -> str:
    if not ROTEIRO.exists():
        pytest.skip("roteiro ainda não escrito")
    texto = ROTEIRO.read_text(encoding="utf-8")
    novos = {"risco-compra", "risco-medo", "fecha-ultimos", "mapa-cadastro"}
    if not novos & set(_blocos(texto)):
        pytest.skip(
            "roteiro.md ainda é a cópia da masterclass, sem os ids da ordem nova"
        )
    return texto


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
    assert _extenso(1170) == "mil cento e setenta"
    assert _extenso(638000) == "seiscentos e trinta e oito mil"
    assert _extenso(98.21) == "noventa e oito vírgula vinte e um"
    assert _extenso(21, feminino=True) == "vinte e uma"


def test_resolver_com_seletor() -> None:
    dados = {"riscos": [{"id": "a", "casos": [{"ano": 1}]}, {"id": "b", "casos": []}]}
    assert _resolver(dados, "riscos[id=a].casos[0].ano") == 1
    assert _resolver(dados, "riscos[1].casos.length") == 0
    with pytest.raises(KeyError):
        _resolver(dados, "riscos[id=z].casos")


def test_ordem_igual_ao_contrato(ordem: list[str]) -> None:
    assert ordem == IDS
    secao = CONTRATO.read_text(encoding="utf-8").split("## 1.", 1)[1].split("## 2.")[0]
    linhas = [x for x in secao.splitlines() if x.startswith("| `")]
    tabela = [i for x in linhas for i in re.findall(r"`([a-z0-9-]+)`", x.split("|")[2])]
    assert tabela == IDS


def test_roteiro_na_ordem(blocos: dict[str, str], ordem: list[str]) -> None:
    assert list(blocos) == ordem


# --------------------------------------------------------------------------- (b) dados


def test_riscos_sete_na_ordem_do_contrato(dados: dict) -> None:
    assert len(dados["riscos"]) == 7
    for r, (rid, cena, cenario, casos, lei) in zip(
        dados["riscos"], RISCOS, strict=True
    ):
        assert (r["id"], r["cena"], r["cenario"]) == (rid, cena, cenario)
        assert [c["id"] for c in r["casos"]] == casos, rid
        assert [x["id"] for x in r["lei"]] == lei, rid
        assert r["sinal"] in ("nenhum", "parcial", "deixa"), rid
        for chave in ("nome", "familia", "o_que_e", "como_aparece", "confere"):
            assert r[chave], f"{rid}.{chave}"
    contrato = (
        CONTRATO.read_text(encoding="utf-8").split("## 3.", 1)[1].split("## 4.")[0]
    )
    for rid, _, cenario, casos, lei in RISCOS:
        linha = next(x for x in contrato.splitlines() if x.startswith(f"| `{rid}`"))
        assert re.findall(r"`([a-z0-9_]+)`", linha) == [rid, cenario, *casos, *lei]
    for r in dados["riscos"]:
        if "mj_1t_2024" in [c["id"] for c in r["casos"]]:
            assert r["numeros"]["mj_1t_2024"] in dados["balanco_mj"]["1t_2024"].values()


def test_casos_batem_com_fontes_fiscais(dados: dict, fontes_fiscais: dict) -> None:
    casos = {c["id"]: c for c in fontes_fiscais["casos"]}
    fontes = {f["id"]: f for f in fontes_fiscais["fontes"]}
    for r in dados["riscos"]:
        for c in r["casos"]:
            origem = casos[c["id"]]
            assert c["ano"] == origem["ano"], c["id"]
            assert c["ano"] < 2026, f"{c['id']}: caso de 2026 não entra como risco"
            primeira = next(fontes[f] for f in origem["fontes"] if fontes[f].get("url"))
            assert c["fonte"]["id"] == primeira["id"], c["id"]
            assert c["fonte"]["url"] == primeira["url"], c["id"]
            assert c["fonte"]["url"].startswith("https://"), c["id"]


def test_lei_ids_existem(dados: dict, fontes_fiscais: dict) -> None:
    base = {b["id"]: b for b in fontes_fiscais["base_legal"]}
    for r in dados["riscos"]:
        for lei in r["lei"]:
            assert lei["id"] in base, lei["id"]
            assert lei["resumo"] == base[lei["id"]]["conteudo"]
            assert lei["pena"] == base[lei["id"]].get("pena")
    assert [x["id"] for x in dados["lei_fiscal"]] == LEI_FISCAL
    assert [x["id"] for x in dados["fechamento"]] == FECHAMENTO
    for item in dados["lei_fiscal"] + dados["fechamento"]:
        assert item["texto"] and item["referencia"], item["id"]
        assert TRAVESSAO not in item["texto"] + item["referencia"], item["id"]
        if item["base_legal"]:
            assert item["base_legal_conteudo"] == base[item["base_legal"]]["conteudo"]
    referencias = {x["id"]: x["referencia"] for x in dados["fechamento"]}
    assert referencias["ultimos_dois"].endswith("art. 160, § 1º")
    assert referencias["senhas"].endswith("art. 160, § 2º")


def test_balanco_mj_relido(dados: dict, fontes_fiscais: dict) -> None:
    casos = {c["id"]: c for c in fontes_fiscais["casos"]}
    b = dados["balanco_mj"]
    assert b["1t_2024"]["fonte_caso"] == "mj_1t_2024"
    assert "1.170 ocorrências de boca de urna" in casos["mj_1t_2024"]["resumo"]
    assert b["1t_2024"]["boca_urna"] == 1170
    assert "R$ 638 mil" in casos["mj_1t_2024"]["resumo"]
    assert b["1t_2024"]["apreendido_reais"] == 638000
    assert (
        f"{b['1t_2022']['crimes']:,}".replace(",", ".")
        in casos["mj_1t_2022"]["resultado"]
    )


def test_urna_bate_com_presidente(dados: dict) -> None:
    n = _ler(Path("analysis/apuracao_2026/dados/presidente.json"))["nacional"]
    u = dados["urna"]
    assert u["flavio_pct"] == round(n["pct"]["flavio"], 2) == 47.03
    assert u["lula_pct"] == round(n["pct"]["lula"], 2) == 45.16
    assert u["diferenca_pp"] == round(n["diferenca_pp"], 2)
    for chave in ("diferenca_votos", "secoes", "eleitores", "comparecimento"):
        assert u[chave] == n[chave], chave
    assert u["comparecimento_pct"] == round(n["pct_comparecimento"], 2)


def _hash(caminho: Path) -> str:
    if caminho.is_dir():
        linhas = [
            f"{p.relative_to(ROOT)}\t{hashlib.sha256(p.read_bytes()).hexdigest()}\n"
            for p in sorted(caminho.rglob("*.json"))
        ]
        return hashlib.sha256("".join(linhas).encode("utf-8")).hexdigest()
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def test_exemplos_predios_e_fontes(dados: dict) -> None:
    esperadas = set(EXEMPLOS) | {"frente_1", "frente_2", "frente_3"}
    assert set(dados["exemplos"]) == esperadas
    for chave, e in dados["exemplos"].items():
        assert set(e) >= CHAVES_EXEMPLO, f"{chave}: faltam {CHAVES_EXEMPLO - set(e)}"
        assert e["aptos"] >= e["votantes"] > 0, chave
        assert e["atencao"] in (None, 0, 1, 2, 3), chave
        assert e["nivel"] in (None, "alta", "media", "baixa"), chave
        assert e["comparecimento_pct"] == round(100 * e["votantes"] / e["aptos"], 2)
    for chave, (uf, zona, secao) in EXEMPLOS.items():
        e = dados["exemplos"][chave]
        assert (e["uf"], e["zona"], e["secao"]) == (uf, zona, secao), chave
    for i, s in enumerate(dados["lula_frente"]["lista"][:3], start=1):
        e = dados["exemplos"][f"frente_{i}"]
        assert (e["uf"], e["zona"], e["secao"]) == (s["uf"], s["zona"], s["secao"])
        assert e["lula_pct"] == s["lula_pct"]
    assert [p["local_id"] for p in dados["predios"]] == PREDIOS
    for p in dados["predios"]:
        assert p["secoes_listadas"] == len(p["secoes"]) <= p["secoes_total"]
        assert sum(p["por_atencao"].values()) + p["sem_log"] == p["secoes_listadas"]
        assert 0 < p["lula_pct"] + p["flavio_pct"] <= 100
    for caminho, sha in dados["fontes"].items():
        assert (ROOT / caminho).exists(), caminho
        assert _hash(ROOT / caminho) == sha, f"{caminho}: SHA-256 mudou, rode o script"
    assert dados["totalizacao"]["exemplos_oficiais"] == len(
        _ler(Path("totalizacao/tests/fixtures/exemplos_tse_2026.json"))["exemplos"]
    )
    assert dados["cadastro"]["site"] == "fiscaisdopl.com.br"


def test_lula_frente_regras(dados: dict) -> None:
    """Recalcula a regra numa UF pelo Politize e pelo mapa, com a função do script."""
    modulo = importlib.import_module("video-sete-riscos-dados")
    frente = dados["lula_frente"]
    lista = frente["lista"]
    assert 0 < len(lista) <= 12
    assert frente["secoes_lula_80_comp_95"] >= len(lista)
    ordem = {"alta": 0, "media": 1, "baixa": 2, None: 3}
    chaves = [(ordem[s["nivel"]], -s["lula_pct"]) for s in lista]
    assert chaves == sorted(chaves)
    for s in lista:
        assert set(s) >= CHAVES_FRENTE
        assert s["lula_pct"] >= 80 and s["comparecimento_pct"] >= 95, s
        assert s["aptos"] >= 100 and s["uf"] != "ZZ", s
        assert not modulo.EXCLUI_EXPLICACAO.search(s["explicacao"] or ""), s
        assert not modulo.EXCLUI_LOCAL.search(s["local"] or ""), s
    assert frente["secoes_lula_90"] > frente["secoes_flavio_90"] > 0

    uf = lista[0]["uf"]
    fontes = modulo.mc.Fontes()
    indice = _ler(Path("docs/assets/fiscais_mapa/indice.json"))
    mapa = modulo.mc.MapaUF(indice, fontes)
    secoes_mapa = modulo.mapa_todo(mapa, [uf])
    cap13 = {
        (s["uf"], s["zona"], s["secao"]): s
        for s in _ler(Path("analysis/apuracao_2026/dados/fiscais.json"))["secoes"]
        if s["uf"] == uf
    }
    politize = {}
    for arquivo in sorted((modulo.POLITIZE_ZONA / uf).glob("*.json")):
        z = json.loads(arquivo.read_text(encoding="utf-8"))
        nomes = {m["mun_tse"]: m["nome"] for m in z["municipios"]}
        for linha in z["secoes"]["linhas"]:
            s = dict(zip(z["secoes"]["colunas"], linha, strict=True))
            s["municipio"] = nomes.get(s["mun_tse"])
            politize[(uf, int(z["zona"]), s["secao"])] = s
    local = modulo.bloco_lula_frente(politize, secoes_mapa, cap13)
    da_uf = [s for s in lista if s["uf"] == uf]
    assert local["lista"][: len(da_uf)] == da_uf
    # Contagem manual, sem a função: lula >= 90 sobre válidos, aptos >= 100, sem exclusão.
    manual = 0
    for chave, p in politize.items():
        validos = (p["flavio"] or 0) + (p["lula"] or 0) + (p["terceira"] or 0)
        if (p["aptos"] or 0) < 100 or not validos:
            continue
        if modulo._excluida(chave, p, secoes_mapa.get(chave), cap13):
            continue
        manual += 100 * p["lula"] / validos >= 90
    assert manual == local["secoes_lula_90"] <= frente["secoes_lula_90"]


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
    for url in (
        "fiscais do PL ponto com ponto br",
        "brasil ponto arvor ponto co barra totalização",
        "brasil ponto arvor ponto co barra fiscais",
    ):
        assert _normalizar(url) in _normalizar(roteiro), url
    abertura = _normalizar(_narrado(blocos.get("abertura", "")))
    assert _normalizar(FRASES_DA_CASA[0]) in abertura, "abertura sem a primeira frase"
    fecho = _normalizar(_narrado(blocos.get("fecho-chamada", "")))
    for frase in FRASES_DA_CASA:
        assert _normalizar(frase) in fecho, f"fecho-chamada sem: {frase}"


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
        assert c["segundos"] > 2, c["id"]
        assert c["palavras"] and c["palavras"][-1]["f"] <= c["segundos"] + 0.5, c["id"]
        assert (VIDEO / "public" / c["arquivo"]).exists(), c["arquivo"]


def test_portao_de_duracao(voz: dict) -> None:
    n = len(voz["cenas"])
    total = sum(c["segundos"] for c in voz["cenas"]) + RESPIRO * (n - 1) + CAUDA
    assert (
        PORTAO[0] <= total <= PORTAO[1]
    ), f"{total:.0f} s ({total / 60:.1f} min) fora de [540, 690]"


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
    if not (
        all(r.exists() for r in REGISTROS_TS) and MIDIA.exists() and CAPTURAS.exists()
    ):
        pytest.skip("registro, midia.json ou capturas.json ausente")
    midia = json.loads(MIDIA.read_text(encoding="utf-8"))
    capturas = json.loads(CAPTURAS.read_text(encoding="utf-8"))
    if not midia and not capturas:
        pytest.skip("midia.json e capturas.json ainda são placeholders vazios")
    usados = set().union(
        *(_ids_de_midia(r.read_text(encoding="utf-8")) for r in REGISTROS_TS)
    )
    faltam = sorted(
        i
        for i in usados
        if i not in midia and i not in capturas and i[4:] not in capturas
    )
    assert not faltam, f"mídia citada no registro sem arquivo gerado: {faltam}"
