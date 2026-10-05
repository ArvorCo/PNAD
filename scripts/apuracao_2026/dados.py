"""Partes puras dos dados da apuração de 2026: geografia, contas e séries.

Nada aqui lê banco ou disco. As funções recebem números, datas ISO e dicionários
já carregados e devolvem números e dicionários, para que os testes rodem sem o
banco de 10 GB da apuração.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from itertools import pairwise
from typing import Any

BRT = timezone(timedelta(hours=-3))

# ---------------------------------------------------------------- geografia

REGIAO_UF: dict[str, str] = {
    "ac": "Norte",
    "am": "Norte",
    "ap": "Norte",
    "pa": "Norte",
    "ro": "Norte",
    "rr": "Norte",
    "to": "Norte",
    "al": "Nordeste",
    "ba": "Nordeste",
    "ce": "Nordeste",
    "ma": "Nordeste",
    "pb": "Nordeste",
    "pe": "Nordeste",
    "pi": "Nordeste",
    "rn": "Nordeste",
    "se": "Nordeste",
    "df": "Centro-Oeste",
    "go": "Centro-Oeste",
    "ms": "Centro-Oeste",
    "mt": "Centro-Oeste",
    "es": "Sudeste",
    "mg": "Sudeste",
    "rj": "Sudeste",
    "sp": "Sudeste",
    "pr": "Sul",
    "rs": "Sul",
    "sc": "Sul",
    "zz": "Exterior",
}

# Centro-Sul é a soma declarada de Sudeste, Sul e Centro-Oeste.
GRUPO_DA_REGIAO: dict[str, str] = {
    "Norte": "Norte",
    "Nordeste": "Nordeste",
    "Sudeste": "Centro-Sul",
    "Sul": "Centro-Sul",
    "Centro-Oeste": "Centro-Sul",
    "Exterior": "Exterior",
}

GRUPOS = ("Nordeste", "Norte", "Centro-Sul")
REGIOES = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")


def regiao(uf: str) -> str:
    """Grande região do IBGE da UF (sigla em qualquer caixa); `zz` é Exterior."""
    return REGIAO_UF[uf.lower()]


def grupo_regional(uf: str) -> str:
    """Nordeste, Norte, Centro-Sul (Sudeste + Sul + Centro-Oeste) ou Exterior."""
    return GRUPO_DA_REGIAO[regiao(uf)]


# Continentes pela divisão geográfica M49 da ONU, com a América partida em três:
# América do Norte (Northern America), América Central e Caribe (Central America
# e Caribbean, o que põe o México aqui) e América do Sul. Chipre, Turquia,
# Geórgia, Armênia e Azerbaijão ficam na Ásia Ocidental, como no M49; Rússia na
# Europa Oriental; Guiana Francesa na América do Sul.
AMERICA_NORTE = "América do Norte"
AMERICA_CENTRAL = "América Central e Caribe"
AMERICA_SUL = "América do Sul"
AFRICA = "África"
ASIA = "Ásia"
EUROPA = "Europa"
OCEANIA = "Oceania"
CONTINENTES = (
    AMERICA_NORTE,
    AMERICA_CENTRAL,
    AMERICA_SUL,
    EUROPA,
    AFRICA,
    ASIA,
    OCEANIA,
)

PAISES: dict[str, tuple[str, str]] = {
    "AE": ("Emirados Árabes Unidos", ASIA),
    "AG": ("Antígua e Barbuda", AMERICA_CENTRAL),
    "AL": ("Albânia", EUROPA),
    "AM": ("Armênia", ASIA),
    "AO": ("Angola", AFRICA),
    "AR": ("Argentina", AMERICA_SUL),
    "AT": ("Áustria", EUROPA),
    "AU": ("Austrália", OCEANIA),
    "AZ": ("Azerbaijão", ASIA),
    "BA": ("Bósnia e Herzegovina", EUROPA),
    "BB": ("Barbados", AMERICA_CENTRAL),
    "BD": ("Bangladesh", ASIA),
    "BE": ("Bélgica", EUROPA),
    "BF": ("Burkina Faso", AFRICA),
    "BG": ("Bulgária", EUROPA),
    "BH": ("Bahrein", ASIA),
    "BJ": ("Benin", AFRICA),
    "BO": ("Bolívia", AMERICA_SUL),
    "BS": ("Bahamas", AMERICA_CENTRAL),
    "BW": ("Botsuana", AFRICA),
    "BZ": ("Belize", AMERICA_CENTRAL),
    "CA": ("Canadá", AMERICA_NORTE),
    "CD": ("República Democrática do Congo", AFRICA),
    "CG": ("República do Congo", AFRICA),
    "CH": ("Suíça", EUROPA),
    "CI": ("Costa do Marfim", AFRICA),
    "CL": ("Chile", AMERICA_SUL),
    "CM": ("Camarões", AFRICA),
    "CN": ("China", ASIA),
    "CO": ("Colômbia", AMERICA_SUL),
    "CR": ("Costa Rica", AMERICA_CENTRAL),
    "CU": ("Cuba", AMERICA_CENTRAL),
    "CV": ("Cabo Verde", AFRICA),
    "CY": ("Chipre", ASIA),
    "CZ": ("Tchéquia", EUROPA),
    "DE": ("Alemanha", EUROPA),
    "DK": ("Dinamarca", EUROPA),
    "DO": ("República Dominicana", AMERICA_CENTRAL),
    "DZ": ("Argélia", AFRICA),
    "EC": ("Equador", AMERICA_SUL),
    "EE": ("Estônia", EUROPA),
    "EG": ("Egito", AFRICA),
    "ES": ("Espanha", EUROPA),
    "ET": ("Etiópia", AFRICA),
    "FI": ("Finlândia", EUROPA),
    "FR": ("França", EUROPA),
    "GA": ("Gabão", AFRICA),
    "GB": ("Reino Unido", EUROPA),
    "GE": ("Geórgia", ASIA),
    "GF": ("Guiana Francesa", AMERICA_SUL),
    "GH": ("Gana", AFRICA),
    "GN": ("Guiné", AFRICA),
    "GQ": ("Guiné Equatorial", AFRICA),
    "GR": ("Grécia", EUROPA),
    "GT": ("Guatemala", AMERICA_CENTRAL),
    "GW": ("Guiné-Bissau", AFRICA),
    "GY": ("Guiana", AMERICA_SUL),
    "HK": ("Hong Kong", ASIA),
    "HN": ("Honduras", AMERICA_CENTRAL),
    "HR": ("Croácia", EUROPA),
    "HT": ("Haiti", AMERICA_CENTRAL),
    "HU": ("Hungria", EUROPA),
    "ID": ("Indonésia", ASIA),
    "IE": ("Irlanda", EUROPA),
    "IL": ("Israel", ASIA),
    "IN": ("Índia", ASIA),
    "IQ": ("Iraque", ASIA),
    "IR": ("Irã", ASIA),
    "IT": ("Itália", EUROPA),
    "JM": ("Jamaica", AMERICA_CENTRAL),
    "JO": ("Jordânia", ASIA),
    "JP": ("Japão", ASIA),
    "KE": ("Quênia", AFRICA),
    "KP": ("Coreia do Norte", ASIA),
    "KR": ("Coreia do Sul", ASIA),
    "KW": ("Kuwait", ASIA),
    "KZ": ("Cazaquistão", ASIA),
    "LB": ("Líbano", ASIA),
    "LC": ("Santa Lúcia", AMERICA_CENTRAL),
    "LK": ("Sri Lanka", ASIA),
    "LY": ("Líbia", AFRICA),
    "MA": ("Marrocos", AFRICA),
    "ML": ("Mali", AFRICA),
    "MM": ("Mianmar", ASIA),
    "MW": ("Malawi", AFRICA),
    "MX": ("México", AMERICA_CENTRAL),
    "MY": ("Malásia", ASIA),
    "MZ": ("Moçambique", AFRICA),
    "NA": ("Namíbia", AFRICA),
    "NG": ("Nigéria", AFRICA),
    "NI": ("Nicarágua", AMERICA_CENTRAL),
    "NL": ("Países Baixos", EUROPA),
    "NO": ("Noruega", EUROPA),
    "NP": ("Nepal", ASIA),
    "NZ": ("Nova Zelândia", OCEANIA),
    "OM": ("Omã", ASIA),
    "PA": ("Panamá", AMERICA_CENTRAL),
    "PE": ("Peru", AMERICA_SUL),
    "PH": ("Filipinas", ASIA),
    "PK": ("Paquistão", ASIA),
    "PL": ("Polônia", EUROPA),
    "PS": ("Palestina", ASIA),
    "PT": ("Portugal", EUROPA),
    "PY": ("Paraguai", AMERICA_SUL),
    "QA": ("Catar", ASIA),
    "RO": ("Romênia", EUROPA),
    "RS": ("Sérvia", EUROPA),
    "RU": ("Rússia", EUROPA),
    "SA": ("Arábia Saudita", ASIA),
    "SE": ("Suécia", EUROPA),
    "SG": ("Singapura", ASIA),
    "SI": ("Eslovênia", EUROPA),
    "SK": ("Eslováquia", EUROPA),
    "SN": ("Senegal", AFRICA),
    "SR": ("Suriname", AMERICA_SUL),
    "ST": ("São Tomé e Príncipe", AFRICA),
    "SV": ("El Salvador", AMERICA_CENTRAL),
    "SY": ("Síria", ASIA),
    "TG": ("Togo", AFRICA),
    "TH": ("Tailândia", ASIA),
    "TL": ("Timor-Leste", ASIA),
    "TN": ("Tunísia", AFRICA),
    "TR": ("Turquia", ASIA),
    "TT": ("Trinidad e Tobago", AMERICA_CENTRAL),
    "TW": ("Taiwan", ASIA),
    "TZ": ("Tanzânia", AFRICA),
    "UA": ("Ucrânia", EUROPA),
    "US": ("Estados Unidos", AMERICA_NORTE),
    "UY": ("Uruguai", AMERICA_SUL),
    "VA": ("Vaticano", EUROPA),
    "VE": ("Venezuela", AMERICA_SUL),
    "VN": ("Vietnã", ASIA),
    "ZA": ("África do Sul", AFRICA),
    "ZM": ("Zâmbia", AFRICA),
    "ZW": ("Zimbábue", AFRICA),
}


def pais_nome(codigo: str) -> str:
    """Nome em português do país pelo código ISO 3166-1 alfa-2."""
    return PAISES[codigo.upper()][0]


def continente(codigo: str) -> str:
    """Continente declarado do país; código ausente da tabela é erro, não palpite."""
    return PAISES[codigo.upper()][1]


# ---------------------------------------------------------------- números


def num(valor: Any) -> int | float | None:
    """Número do TSE (texto com vírgula decimal) para int ou float; vazio vira None."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return valor
    texto = str(valor).strip()
    if texto == "":
        return None
    if "," in texto:
        return float(texto.replace(".", "").replace(",", "."))
    try:
        return int(texto)
    except ValueError:
        return float(texto)


def pct(parte: float | None, total: float | None, casas: int = 4) -> float | None:
    """Percentual de `parte` em `total`; None quando o total é zero ou ausente."""
    if parte is None or not total:
        return None
    return round(100.0 * parte / total, casas)


def dif(a: float | None, b: float | None, casas: int = 4) -> float | None:
    """Diferença a - b em pontos; None se faltar um dos lados."""
    if a is None or b is None:
        return None
    return round(a - b, casas)


def swing(
    votos_a: int | None,
    total_a: int | None,
    votos_b: int | None,
    total_b: int | None,
    casas: int = 4,
) -> dict[str, float | int | None]:
    """Compara uma candidatura (a) com outra numa eleição anterior (b).

    Devolve a fatia de cada uma no próprio total, a diferença em pontos
    percentuais (a menos b) e a diferença em votos.
    """
    pa = pct(votos_a, total_a, casas)
    pb = pct(votos_b, total_b, casas)
    votos = None if votos_a is None or votos_b is None else votos_a - votos_b
    return {"pct_a": pa, "pct_b": pb, "pp": dif(pa, pb, casas), "votos": votos}


def percentil(valores: Sequence[float], p: float) -> float | None:
    """Percentil com interpolação linear entre postos (o padrão do numpy)."""
    if not valores:
        return None
    if not 0 <= p <= 100:
        raise ValueError("p fora de [0, 100]")
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return float(ordenados[0])
    pos = (len(ordenados) - 1) * p / 100.0
    baixo = math.floor(pos)
    alto = math.ceil(pos)
    if baixo == alto:
        return float(ordenados[baixo])
    frac = pos - baixo
    return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * frac


def somar(destino: dict[str, int], origem: Mapping[str, int | None]) -> dict[str, int]:
    """Soma chave a chave `origem` em `destino` (None conta como zero)."""
    for chave, valor in origem.items():
        destino[chave] = destino.get(chave, 0) + (valor or 0)
    return destino


# ---------------------------------------------------------------- tempo


def utc(iso: str) -> datetime:
    """Instante ISO-8601 do banco (`...Z` ou com fuso) como datetime com fuso."""
    texto = iso.strip()
    if texto.endswith("Z"):
        texto = texto[:-1] + "+00:00"
    dt = datetime.fromisoformat(texto)
    if dt.tzinfo is None:
        raise ValueError(f"instante sem fuso: {iso}")
    return dt


def iso_z(dt: datetime) -> str:
    """Datetime para ISO UTC com `Z`, sem frações."""
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def brt(iso: str | None) -> str | None:
    """Horário de Brasília (UTC-3) em `AAAA-MM-DD HH:MM:SS`."""
    if iso is None:
        return None
    return utc(iso).astimezone(BRT).strftime("%Y-%m-%d %H:%M:%S")


def hora_brt(iso: str) -> str:
    """Faixa horária de Brasília (`AAAA-MM-DD HHh`) para agregações por hora."""
    return utc(iso).astimezone(BRT).strftime("%Y-%m-%d %Hh")


def minutos(de: str, ate: str) -> float:
    """Minutos entre dois instantes ISO."""
    return (utc(ate) - utc(de)).total_seconds() / 60.0


def local_como_brt(dt: str | None, ht: str | None) -> datetime | None:
    """Lê `dd/mm/aaaa` e `hh:mm:ss` do TSE supondo horário de Brasília."""
    if not dt or not ht:
        return None
    return datetime.strptime(f"{dt} {ht}", "%d/%m/%Y %H:%M:%S").replace(tzinfo=BRT)


def deslocamento_horas(dt: str | None, ht: str | None, gerado_iso: str) -> float | None:
    """Hora de totalização impressa pelo TSE menos a hora de geração do arquivo.

    O TSE imprime a totalização no relógio local da unidade. Lida como se fosse
    Brasília, ela fica deslocada do relógio de geração (que é o de Brasília) pelo
    fuso local menos o atraso de geração, em horas.
    """
    local = local_como_brt(dt, ht)
    if local is None:
        return None
    return round((local - utc(gerado_iso)).total_seconds() / 3600.0, 4)


def fuso_inferido(
    deslocamento_h: float | None, tolerancia_h: float = 0.25
) -> float | None:
    """Fuso UTC provável a partir do deslocamento aparente, quando ele é inequívoco.

    Arredonda o deslocamento para a hora inteira mais próxima e só aceita quando a
    sobra cabe na tolerância; meio fuso (Nepal, Índia) ou atraso grande de geração
    devolvem None em vez de chute.
    """
    if deslocamento_h is None:
        return None
    inteiro = round(deslocamento_h)
    if abs(deslocamento_h - inteiro) > tolerancia_h:
        return None
    return float(inteiro - 3)


# ---------------------------------------------------------------- versões e lacunas


def versoes_genuinas(snapshots: Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    """Versões novas de um arquivo, na ordem de captura.

    Cada snapshot precisa de `id` (ordem de captura) e `gerado_em` (relógio de
    geração do TSE). Uma versão é nova quando foi gerada depois de todas as
    anteriores já capturadas; as demais são cópias antigas servidas pelo CDN ou
    repetições da mesma geração. O contador `idg` não entra: ele não cresce de
    forma monotônica dentro do mesmo arquivo.
    """
    saida: list[Mapping[str, Any]] = []
    maior: str | None = None
    for snap in sorted(snapshots, key=lambda s: s["id"]):
        gerado = snap.get("gerado_em")
        if gerado is None:
            continue
        if maior is None or utc(gerado) > utc(maior):
            saida.append(snap)
            maior = gerado
    return saida


def classificar_copias(snapshots: Iterable[Mapping[str, Any]]) -> list[tuple[int, str]]:
    """Classe de cada snapshot de um arquivo pela hora de geração.

    `primeira`, `nova` (gerada depois de tudo o que veio antes), `mesma_geracao`
    ou `antiga` (gerada antes da maior geração já capturada).
    """
    saida: list[tuple[int, str]] = []
    maior: datetime | None = None
    for snap in sorted(snapshots, key=lambda s: s["id"]):
        gerado = snap.get("gerado_em")
        if gerado is None:
            saida.append((snap["id"], "sem_geracao"))
            continue
        g = utc(gerado)
        if maior is None:
            classe = "primeira"
        elif g > maior:
            classe = "nova"
        elif g == maior:
            classe = "mesma_geracao"
        else:
            classe = "antiga"
        saida.append((snap["id"], classe))
        if maior is None or g > maior:
            maior = g
    return saida


def travamentos(
    versoes: Sequence[Mapping[str, Any]], limiar_min: float = 8.0
) -> list[dict[str, Any]]:
    """Intervalos sem versão nova acima do limiar, com a apuração em andamento.

    `versoes` são as versões genuínas em ordem, cada uma com `gerado_em`, `st`
    (seções totalizadas) e `ts` (total de seções). Só contam lacunas que começam
    com a contagem já iniciada (st > 0) e ainda incompleta (st < ts).
    """
    saida: list[dict[str, Any]] = []
    for anterior, atual in pairwise(versoes):
        st0 = anterior.get("st") or 0
        ts0 = anterior.get("ts") or 0
        if st0 <= 0 or st0 >= ts0:
            continue
        duracao = minutos(anterior["gerado_em"], atual["gerado_em"])
        if duracao <= limiar_min:
            continue
        st1 = atual.get("st") or 0
        saida.append(
            {
                "de": anterior["gerado_em"],
                "ate": atual["gerado_em"],
                "de_brt": brt(anterior["gerado_em"]),
                "ate_brt": brt(atual["gerado_em"]),
                "minutos": round(duracao, 2),
                "st_de": st0,
                "st_ate": st1,
                "secoes_no_salto": st1 - st0,
                "pst_de": pct(st0, ts0, 3),
                "pst_ate": pct(st1, atual.get("ts") or ts0, 3),
            }
        )
    return saida


def lacunas_da_uniao(
    tempos: Iterable[str], limiar_min: float = 8.0
) -> list[dict[str, Any]]:
    """Lacunas acima do limiar numa lista de instantes de vários arquivos juntos."""
    ordenados = sorted(set(tempos), key=utc)
    saida: list[dict[str, Any]] = []
    for de, ate in pairwise(ordenados):
        duracao = minutos(de, ate)
        if duracao > limiar_min:
            saida.append(
                {
                    "de": de,
                    "ate": ate,
                    "de_brt": brt(de),
                    "ate_brt": brt(ate),
                    "minutos": round(duracao, 2),
                }
            )
    return saida


def estado_em(
    versoes: Sequence[Mapping[str, Any]],
    instante: datetime,
    campo: str = "capturado_em",
) -> Mapping[str, Any] | None:
    """Última versão com `campo` até o instante (versões em ordem de geração)."""
    escolhida = None
    for versao in versoes:
        momento = utc(versao[campo])
        if momento <= instante and (
            escolhida is None or momento >= utc(escolhida[campo])
        ):
            escolhida = versao
    return escolhida


# ---------------------------------------------------------------- arquivos do TSE


def resultado_do_documento(doc: Mapping[str, Any]) -> dict[str, Any]:
    """Totais e votos por candidatura de um arquivo `-u.json` do TSE."""
    s = doc.get("s") or {}
    e = doc.get("e") or {}
    v = doc.get("v") or {}
    votos: dict[str, int] = {}
    partidos: list[dict[str, Any]] = []
    for cargo in doc.get("carg") or []:
        for agr in cargo.get("agr") or []:
            for par in agr.get("par") or []:
                partidos.append(
                    {
                        "agremiacao": str(agr.get("n")),
                        "partido_n": num(par.get("n")),
                        "sigla": par.get("sg"),
                        "tvtn": num(par.get("tvtn")) or 0,
                        "tvtl": num(par.get("tvtl")) or 0,
                    }
                )
                for cand in par.get("cand") or []:
                    votos[str(cand["sqcand"])] = num(cand.get("vap")) or 0
    return {
        "st": num(s.get("st")),
        "ts": num(s.get("ts")),
        "te": num(e.get("te")),
        "comparecimento": num(e.get("c")),
        "abstencao": num(e.get("a")),
        "vv": num(v.get("vv")),
        "vb": num(v.get("vb")),
        "vn": num(v.get("vn")),
        "vnt": num(v.get("vnt")),
        "tvn": num(v.get("tvn")),
        "votos": votos,
        "partidos": partidos,
    }


def entradas_ab(doc: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Entradas de um arquivo de andamento `-ab.json`, por código de abrangência."""
    saida: dict[str, dict[str, Any]] = {}
    for entrada in doc.get("abr") or []:
        s = entrada.get("s") or {}
        saida[str(entrada.get("cdabr"))] = {
            "tpabr": entrada.get("tpabr"),
            "dt": entrada.get("dt"),
            "ht": entrada.get("ht"),
            "st": num(s.get("st")),
            "ts": num(s.get("ts")),
        }
    return saida


# ---------------------------------------------------------------- tabelas


def colunar(
    colunas: Sequence[str], linhas: Iterable[Mapping[str, Any]]
) -> dict[str, Any]:
    """Tabela compacta: nomes das colunas uma vez e cada linha como lista."""
    nomes = list(colunas)
    return {
        "colunas": nomes,
        "linhas": [[linha.get(c) for c in nomes] for linha in linhas],
    }


def extremos(
    linhas: Sequence[Mapping[str, Any]],
    chave: str,
    n: int,
    campos: Sequence[str],
    minimo: Mapping[str, float] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """As n maiores e as n menores linhas por `chave`, ignorando valores ausentes.

    `minimo` filtra por piso em outras colunas (por exemplo, eleitorado).
    """
    validas = [
        linha
        for linha in linhas
        if linha.get(chave) is not None
        and all((linha.get(k) or 0) >= v for k, v in (minimo or {}).items())
    ]
    ordem = sorted(validas, key=lambda linha: (linha[chave], str(linha.get(campos[0]))))
    menores = ordem[:n]
    maiores = list(reversed(ordem[-n:])) if n else []

    def corte(linha: Mapping[str, Any]) -> dict[str, Any]:
        return {c: linha.get(c) for c in [*campos, chave]}

    return {
        "maiores": [corte(x) for x in maiores],
        "menores": [corte(x) for x in menores],
    }


# ---------------------------------------------------------------- campos políticos

CAMPOS_POLITICOS = (
    "esquerda",
    "centro-esquerda",
    "centro",
    "centro-direita",
    "direita",
)


def classificador(bruto: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """Tabela de campos de `apuracao/public/campos.json` (partidos e exceções).

    Mesma regra do telão: sigla em caixa alta, valor fora da lista é ignorado.
    """
    validos = {*CAMPOS_POLITICOS, "indefinido"}
    partidos = {
        str(sigla).upper(): campo
        for sigla, campo in (bruto.get("partidos") or {}).items()
        if campo in validos
    }
    excecoes = {
        str(sq): campo
        for sq, campo in (bruto.get("excecoes") or {}).items()
        if campo in validos
    }
    return {"partidos": partidos, "excecoes": excecoes}


def campo_de(
    cl: Mapping[str, Mapping[str, str]], sq: str | None, *siglas: str | None
) -> str:
    """Exceção por candidatura vence; depois o partido; depois a federação."""
    if sq is not None and str(sq) in cl["excecoes"]:
        return cl["excecoes"][str(sq)]
    for sigla in siglas:
        if sigla and sigla.upper() in cl["partidos"]:
            return cl["partidos"][sigla.upper()]
    return "indefinido"


def bloco_de(campo: str) -> str:
    """Bloco de dois campos usado nas contagens de bancada."""
    if campo in ("direita", "centro-direita"):
        return "direita + centro-direita"
    if campo in ("esquerda", "centro-esquerda"):
        return "esquerda + centro-esquerda"
    return "centro" if campo == "centro" else "indefinido"
