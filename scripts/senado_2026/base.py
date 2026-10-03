"""Leitura, normalização e média das pesquisas de Senado 2026 por estado.

Lê os JSON de `analysis/senado_2026/pesquisas/` (esquema da seção 1 do
CONTRATO.md), casa nomes com o TSE pela tabela `casamento_nomes.json` e por
apelidos declarados aqui, escolhe uma onda por casa e calcula a média central
por recência. Não sorteia nada: o sorteio fica em `motor.py`.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from voto_util_base import PARTIDO_CAMPO

from .tse import APELIDOS, DESEMPATE, normalizar

ROOT = Path(__file__).resolve().parents[2]
PASTA = ROOT / "analysis/senado_2026"
PESQUISAS = PASTA / "pesquisas"
DOCS = ROOT / "docs"

DATA_REFERENCIA = date(2026, 10, 3)
ELEICAO = date(2026, 10, 4)
CORTE_CAMPO = date(2026, 9, 28)
# Onda sem campo divulgada a partir desta data entra na central com campo
# inferido (fim = divulgação - 1 dia, início = divulgação - 3 dias).
CORTE_INFERENCIA = date(2026, 9, 30)
MEIA_VIDA_DIAS = 5.0
LIMIAR_UNIFORME_PP = 1.0

UFS = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

CAMPOS = (
    "direita",
    "centro-direita",
    "centro",
    "centro-esquerda",
    "esquerda",
    "indefinido",
)

# Siglas que chegam abreviadas ou antigas e a sigla de PARTIDO_CAMPO a que
# correspondem. Só grafia: nenhuma troca de campo é feita aqui.
SIGLA = {
    "PODE": "PODEMOS",
    "REP": "REPUBLICANOS",
    "CID": "CIDADANIA",
    "MOB": "MOBILIZA",
    "SD": "SOLIDARIEDADE",
    "PC DO B": "PCDOB",
    "UNIAO": "UNIÃO",
    "MISSAO": "MISSÃO",
}

# Exceções de campo por candidatura de 2026, (UF, SQ) -> (campo, motivo).
# Vazia por decisão: nenhuma candidatura de 2026 tem exceção declarada.
CAMPO_EXCECAO_2026: dict[tuple[str, str], tuple[str, str]] = {}

# Mesma pessoa com nomes diferentes entre casas quando nenhum dos nomes casa
# com o TSE: (UF, variante normalizada) -> forma canônica normalizada.
APELIDOS_NOMES: dict[tuple[str, str], str] = {}

# Candidaturas retiradas depois do prazo de substituição: o nome pode seguir
# na urna, mas o voto nele é nulo. (UF, nome normalizado) -> (data, fonte).
# Em toda onda usada na previsão de 04/10 o valor dela passa a indeciso e ela
# nunca é sorteada como eleita.
RETIRADAS: dict[tuple[str, str], tuple[date, str]] = {
    ("SP", "salles"): (
        date(2026, 9, 28),
        "observações de futura_SP_2026-10-01.json e realtime_SP_2026-09-28.json",
    ),
    ("DF", "ronaldo fonseca"): (
        date(2026, 9, 28),
        "observações de realtime_DF_2026-09-28.json",
    ),
}

PARTICULAS = {"da", "de", "do", "das", "dos", "e"}


# ------------------------------------------------------------------ utilidades


def ler_json(caminho: Path):
    return json.loads(caminho.read_text(encoding="utf-8"))


def ler_opcional(caminho: Path):
    return ler_json(caminho) if caminho.exists() else None


def sigla(partido: str | None) -> str | None:
    if not partido:
        return None
    p = partido.strip().upper()
    return SIGLA.get(p, p)


def campo(partido: str | None) -> str:
    s = sigla(partido)
    if not s:
        return "indefinido"
    return PARTIDO_CAMPO.get(s, "indefinido")


def nome_exibicao(nome: str) -> str:
    """Nome da pesquisa com partículas em minúsculas ('André do Prado')."""
    partes = nome.split()
    return " ".join(
        p.lower() if i > 0 and p.lower() in PARTICULAS else p
        for i, p in enumerate(partes)
    )


# Grafias que o cadastro do TSE perde (apostrofo removido no nome de urna).
GRAFIA_URNA = {"MANUELA D ÁVILA": "MANUELA D'ÁVILA"}


def titulo_urna(nome_urna: str) -> str:
    """Nome de urna do TSE (caixa alta) em caixa de título, partículas baixas.

    Sigla sem vogal (JHC, MLB) fica em caixa alta.
    """
    nome_urna = GRAFIA_URNA.get(nome_urna, nome_urna)
    partes = []
    for i, p in enumerate(nome_urna.split()):
        baixa = p.lower()
        letras = re.sub(r"[^a-z]", "", normalizar(p))
        if i > 0 and baixa in PARTICULAS:
            partes.append(baixa)
        elif letras and not re.search(r"[aeiouy]", letras) and not p.endswith("."):
            partes.append(p)
        else:
            partes.append(
                re.sub(
                    r"(^|[-'])([a-zà-ú])",
                    lambda m: m.group(1) + m.group(2).upper(),
                    baixa,
                )
            )
    return " ".join(partes)


def meio(inicio: date, fim: date) -> float:
    return (inicio.toordinal() + fim.toordinal()) / 2


def decaimento(dias: float, meia_vida: float) -> float:
    if meia_vida <= 0:
        raise ValueError("Meia-vida precisa ser positiva")
    return float(2 ** (-max(0.0, dias) / meia_vida))


# ------------------------------------------------------------------------ TSE


class Tse:
    """Candidaturas, casamento de nomes e fotos. Funciona sem os arquivos."""

    def __init__(self, pasta: Path = PASTA, docs: Path = DOCS):
        self.candidatos = ler_opcional(pasta / "tse_candidatos.json") or []
        self.por_sq = {c["sq_candidato"]: c for c in self.candidatos}
        casamento = ler_opcional(pasta / "casamento_nomes.json") or {}
        self.casados = {
            (c["uf"], normalizar(c["nome_pesquisa"])): c["sq_candidato"]
            for c in casamento.get("casados", [])
        }
        self.nao_casados = casamento.get("nao_casados", [])
        self.docs = docs
        self.via_apelido = [
            c for c in casamento.get("casados", []) if c.get("via_apelido")
        ]
        self.ambiguidades: list[dict] = []
        self._resolver_ambiguos()

    def _tem_foto(self, c: dict) -> bool:
        return bool(c.get("foto")) and (self.docs / c["foto"]).exists()

    def _resolver_ambiguos(self) -> None:
        """Nome com duas candidaturas de mesma forma: a com foto, depois a de SQ
        maior (registro mais recente). A escolha fica registrada."""
        for item in self.nao_casados:
            if item.get("motivo") != "ambiguo":
                continue
            uf, norma = item["uf"], normalizar(item["nome_pesquisa"])
            opcoes = [
                c
                for c in self.candidatos
                if c["uf"] == uf
                and norma
                in {normalizar(c["nome_urna"]), normalizar(c["nome_completo"])}
            ]
            if not opcoes:
                continue
            opcoes.sort(key=lambda c: (self._tem_foto(c), c["sq_candidato"]))
            escolhida = opcoes[-1]
            self.casados[(uf, norma)] = escolhida["sq_candidato"]
            self.ambiguidades.append(
                {
                    "uf": uf,
                    "nome_pesquisa": item["nome_pesquisa"],
                    "candidaturas": [c["sq_candidato"] for c in opcoes],
                    "escolhida": escolhida["sq_candidato"],
                    "regra": "a que tem foto; empate decidido pelo SQ maior",
                }
            )

    def sq(self, uf: str, nome: str) -> str | None:
        """SQ pelo casamento gravado; senão pelas tabelas de apelido e
        desempate de `tse.py` e pelo nome de urna exato (onda nova)."""
        norma = normalizar(nome)
        sq = self.casados.get((uf, norma))
        if sq:
            return sq
        alvo = APELIDOS.get((uf, norma), norma)
        if (uf, alvo) in DESEMPATE:
            return DESEMPATE[(uf, alvo)]
        achados = {
            c["sq_candidato"]
            for c in self.candidatos
            if c["uf"] == uf
            and alvo in {normalizar(c["nome_urna"]), normalizar(c["nome_completo"])}
        }
        return next(iter(achados)) if len(achados) == 1 else None

    def desempates(self) -> list[dict]:
        """Nomes de urna repetidos na UF resolvidos pela tabela DESEMPATE."""
        saida = []
        for (uf, norma), sq in sorted(DESEMPATE.items()):
            opcoes = [
                c
                for c in self.candidatos
                if c["uf"] == uf and normalizar(c["nome_urna"]) == norma
            ]
            saida.append(
                {
                    "uf": uf,
                    "nome": norma,
                    "candidaturas": [
                        {
                            "sq_candidato": c["sq_candidato"],
                            "tem_foto": self._tem_foto(c),
                        }
                        for c in opcoes
                    ],
                    "escolhida": sq,
                    "regra": (
                        "tabela DESEMPATE de scripts/senado_2026/tse.py: registro mais "
                        "recente, com foto"
                    ),
                }
            )
        return saida

    def foto(self, sq: str | None) -> str | None:
        c = self.por_sq.get(sq or "")
        return c["foto"] if c and self._tem_foto(c) else None


# ------------------------------------------------------------------ pesquisas


def _data(texto: str | None) -> date | None:
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def normalizar_onda(dados: dict, arquivo: str, n_ausente: int) -> dict:
    """Uma onda no formato interno: valores divididos por votos por eleitor."""
    pergunta = dados.get("pergunta") or {}
    votos = pergunta.get("votos_por_eleitor") or 1
    divulgacao = _data(dados.get("divulgacao"))
    campo_json = dados.get("campo") or {}
    inicio, fim = _data(campo_json.get("inicio")), _data(campo_json.get("fim"))
    inferido = None
    if (inicio is None or fim is None) and divulgacao:
        if divulgacao >= CORTE_INFERENCIA:
            fim = divulgacao - timedelta(days=1)
            inicio = divulgacao - timedelta(days=3)
            inferido = "divulgacao_menos_1_a_3_dias"
        else:
            inicio = fim = divulgacao
            inferido = "data_de_divulgacao"

    def div(x):
        return None if x is None else float(x) / votos

    uf = str(dados.get("uf") or "")
    candidatos, retiradas = [], []
    indecisos = div(dados.get("indecisos"))
    for c in dados.get("candidatos") or []:
        v = div(c.get("valor"))
        retirada = RETIRADAS.get((uf, normalizar(c["nome"])))
        if retirada:
            # Voto em candidatura retirada vira indeciso nesta onda.
            retiradas.append(
                {
                    "nome_pesquisa": c["nome"],
                    "valor_pp": v,
                    "data_retirada": retirada[0].isoformat(),
                    "fonte": retirada[1],
                }
            )
            if v and pergunta.get("base") != "validos":
                indecisos = (indecisos or 0.0) + v
            continue
        candidatos.append(
            {
                "nome_pesquisa": c["nome"],
                "partido_pesquisa": sigla(c.get("partido")),
                "valor": v,
            }
        )

    n = dados.get("n")
    fonte = dados.get("fonte") or {}
    return {
        "arquivo": arquivo,
        "instituto": dados.get("instituto"),
        "casa": dados.get("instituto_slug") or normalizar(dados.get("instituto") or ""),
        "uf": uf,
        "registro_tse": dados.get("registro_tse"),
        "divulgacao": divulgacao,
        "campo_inicio": inicio,
        "campo_fim": fim,
        "campo_inferido": inferido,
        "n": n,
        "n_usado": n or n_ausente,
        "n_assumido": not n,
        "tipo": pergunta.get("tipo"),
        "base": pergunta.get("base") or "total",
        "votos_por_eleitor": votos,
        "soma_total": pergunta.get("soma_total"),
        "candidatos": candidatos,
        "indecisos": indecisos,
        "retiradas": retiradas,
        "branco_nulo": div(dados.get("branco_nulo")),
        "outros": div(dados.get("outros")),
        "fonte": {
            "url": fonte.get("url") or next(iter(fonte.get("materia") or []), None),
            "painel_url": fonte.get("painel_url"),
            "arquivo": fonte.get("arquivo"),
            "sha256": fonte.get("sha256"),
            "pagina": fonte.get("pagina"),
            "tipo": fonte.get("tipo"),
        },
        "bruto": {
            "candidatos": [c.get("valor") for c in dados.get("candidatos") or []],
            "indecisos": dados.get("indecisos"),
            "branco_nulo": dados.get("branco_nulo"),
            "outros": dados.get("outros"),
        },
    }


def n_minimo(pasta: Path = PESQUISAS) -> int:
    """Menor n declarado no acervo: o n assumido quando a onda não traz n."""
    ns = [
        d["n"]
        for d in (ler_json(a) for a in sorted(pasta.glob("*.json")))
        if isinstance(d.get("n"), (int, float)) and d["n"] > 0
    ]
    return int(min(ns)) if ns else 600


def ler_pesquisas(pasta: Path = PESQUISAS, n_ausente: int | None = None) -> list[dict]:
    if not pasta.exists():
        return []
    n_ausente = n_ausente or n_minimo(pasta)
    ondas = []
    for arq in sorted(pasta.glob("*.json")):
        dados = ler_json(arq)
        ondas.append(normalizar_onda(dados, arq.name, n_ausente))
    return ondas


def recomposicao(onda: dict) -> dict:
    """Candidaturas + indecisos + branco/nulo (+ outros) contra a soma gravada."""
    b = onda["bruto"]
    soma = sum(v for v in b["candidatos"] if v is not None)
    for k in ("indecisos", "branco_nulo", "outros"):
        soma += b[k] or 0.0
    alvo = onda["soma_total"]
    return {
        "arquivo": onda["arquivo"],
        "soma_recomposta": round(soma, 4),
        "soma_total": alvo,
        "diferenca": None if alvo is None else round(soma - alvo, 4),
        "votos_por_eleitor": onda["votos_por_eleitor"],
        "fechamento_em_100": round(soma / onda["votos_por_eleitor"] - 100, 4),
    }


def motivo_descarte(onda: dict) -> str | None:
    if onda["tipo"] != "estimulada":
        return f"pergunta {onda['tipo'] or 'sem tipo'}: só a estimulada entra"
    nomeados = [c for c in onda["candidatos"] if c["valor"] is not None]
    if len(nomeados) < 2 or sum(c["valor"] for c in nomeados) <= 0:
        return "sem candidaturas com valor"
    if onda["campo_fim"] is None:
        return "sem campo nem divulgação: não há data para a recência"
    return None


def selecionar(ondas: list[dict], uf: str) -> tuple[list[dict], list[dict], str]:
    """Uma onda por casa e a cobertura do estado.

    Ordem: a onda estimulada mais recente de cada casa (divulgação, depois fim
    do campo). Recente quando o fim do campo é 28/09 ou depois. Se nenhuma casa
    tem onda recente, as mais recentes de cada casa viram prior fraca.
    """
    do_estado = [o for o in ondas if o["uf"] == uf]
    descartadas = []
    validas = []
    for o in do_estado:
        motivo = motivo_descarte(o)
        if motivo:
            descartadas.append({"arquivo": o["arquivo"], "motivo": motivo})
        else:
            validas.append(o)
    por_casa: dict[str, list[dict]] = defaultdict(list)
    for o in validas:
        por_casa[o["casa"]].append(o)
    ultimas = []
    for casa in sorted(por_casa):
        lista = sorted(
            por_casa[casa],
            key=lambda o: (o["divulgacao"] or o["campo_fim"], o["campo_fim"]),
        )
        ultimas.append(lista[-1])
        descartadas.extend(
            {"arquivo": o["arquivo"], "motivo": "onda anterior da mesma casa"}
            for o in lista[:-1]
        )
    recentes = [
        o
        for o in ultimas
        if o["campo_fim"] >= CORTE_CAMPO and o["campo_inferido"] != "data_de_divulgacao"
    ]
    if recentes:
        for o in ultimas:
            if o not in recentes:
                descartadas.append(
                    {
                        "arquivo": o["arquivo"],
                        "motivo": (
                            "campo anterior a 28/09 (ou sem campo e divulgada antes "
                            "de 30/09) e o estado tem onda recente"
                        ),
                    }
                )
        return recentes, descartadas, "recente"
    if ultimas:
        return ultimas, descartadas, "antiga"
    return [], descartadas, "sem_pesquisa"


def chave_pessoa(uf: str, nome: str, tse: Tse) -> tuple[str, str | None]:
    """Identidade da candidatura: SQ do TSE quando casa, senão o nome."""
    sq = tse.sq(uf, nome)
    if sq:
        return f"sq:{sq}", sq
    norma = normalizar(nome)
    return f"nome:{APELIDOS_NOMES.get((uf, norma), norma)}", None


def media_estado(
    usadas: list[dict],
    uf: str,
    tse: Tse,
    *,
    meia_vida: float = MEIA_VIDA_DIAS,
    hoje: date = DATA_REFERENCIA,
) -> dict:
    """Média por recência, peso igual entre casas, nos válidos e no total.

    Cada casa entra com o vetor fechado em 100 (candidaturas, outros,
    indecisos, branco/nulo). A parte válida é renormalizada entre candidaturas
    e outros; indecisos e branco/nulo são médias entre as casas que os trazem.
    """
    pesos = [
        decaimento(
            hoje.toordinal() - meio(o["campo_inicio"], o["campo_fim"]), meia_vida
        )
        for o in usadas
    ]
    total = sum(pesos)
    pesos = [p / total for p in pesos]
    pessoas: dict[str, dict] = {}
    ordem: list[str] = []
    aliases: dict[str, set[str]] = defaultdict(set)
    for o in usadas:
        for c in o["candidatos"]:
            chave, sq = chave_pessoa(uf, c["nome_pesquisa"], tse)
            aliases[chave].add(c["nome_pesquisa"])
            if chave not in pessoas:
                pessoas[chave] = {
                    "chave": chave,
                    "sq_candidato": sq,
                    "nome_pesquisa": c["nome_pesquisa"],
                    "partido_pesquisa": c["partido_pesquisa"],
                }
                ordem.append(chave)
            elif not pessoas[chave]["partido_pesquisa"] and c["partido_pesquisa"]:
                pessoas[chave]["partido_pesquisa"] = c["partido_pesquisa"]
    k = len(ordem)
    idx = {ch: i for i, ch in enumerate(ordem)}
    casas = []
    for o, w in zip(usadas, pesos, strict=True):
        cand = [0.0] * k
        presentes = set()
        for c in o["candidatos"]:
            if c["valor"] is None:
                continue
            chave, _ = chave_pessoa(uf, c["nome_pesquisa"], tse)
            cand[idx[chave]] += c["valor"]
            presentes.add(chave)
        outros = o["outros"] or 0.0
        tem_nao_escolha = o["base"] != "validos" and (
            o["indecisos"] is not None or o["branco_nulo"] is not None
        )
        ind = (o["indecisos"] or 0.0) if tem_nao_escolha else 0.0
        bn = (o["branco_nulo"] or 0.0) if tem_nao_escolha else 0.0
        soma = sum(cand) + outros + ind + bn
        casas.append(
            {
                "onda": o,
                "peso": w,
                "candidatos": [x / soma for x in cand],
                "outros": outros / soma,
                "indecisos": ind / soma if tem_nao_escolha else None,
                "branco_nulo": bn / soma if tem_nao_escolha else None,
                "ausentes": [ch for ch in ordem if ch not in presentes],
            }
        )
    validos = [0.0] * k
    outros_v = 0.0
    for c in casas:
        soma_v = sum(c["candidatos"]) + c["outros"]
        for i in range(k):
            validos[i] += c["peso"] * c["candidatos"][i] / soma_v
        outros_v += c["peso"] * c["outros"] / soma_v
    com_ne = [c for c in casas if c["indecisos"] is not None]
    peso_ne = sum(c["peso"] for c in com_ne)
    ind = sum(c["peso"] * c["indecisos"] for c in com_ne) / peso_ne if com_ne else 0.0
    bn = sum(c["peso"] * c["branco_nulo"] for c in com_ne) / peso_ne if com_ne else 0.0
    decididos = 1 - ind - bn
    valor = [100 * v * decididos for v in validos]
    elegivel_uniforme = [v >= LIMIAR_UNIFORME_PP for v in valor]
    m = sum(elegivel_uniforme)
    uniforme = []
    for i in range(k):
        bruto = validos[i] * decididos + (ind / m if elegivel_uniforme[i] and m else 0)
        uniforme.append(bruto)
    soma_u = sum(uniforme) + outros_v * decididos
    pessoas_lista = [pessoas[ch] for ch in ordem]
    for i, p in enumerate(pessoas_lista):
        p["aliases"] = sorted(aliases[p["chave"]])
        # Entre grafias da mesma pessoa, a acentuada (a sem acento perde o dado).
        p["nome_pesquisa"] = max(
            p["aliases"], key=lambda n: (sum(not ch.isascii() for ch in n), n)
        )
        p["valor"] = valor[i]
        p["validos"] = 100 * validos[i]
        p["validos_uniforme"] = 100 * uniforme[i] / soma_u if soma_u else None
        p["elegivel_uniforme"] = elegivel_uniforme[i]
    return {
        "pesos": pesos,
        "casas": casas,
        "pessoas": pessoas_lista,
        "validos": validos,
        "outros_validos": outros_v,
        "indecisos": ind,
        "branco_nulo": bn,
        "dias_ate_eleicao": sum(
            w * (ELEICAO - o["campo_fim"]).days
            for o, w in zip(usadas, pesos, strict=True)
        ),
    }
