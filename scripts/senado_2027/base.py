"""Leitura, validação e casamento dos dados do Senado 2027 (seções 1 e 2 do CONTRATO).

Carrega `analysis/senado_2027/elenco.json`, os JSON de
`analysis/senado_2027/senadores/` e, se existir, `analysis/senado_2027/contexto.json`.
Valida o esquema (campos obrigatórios, enums, datas ISO, travessão em qualquer
string) e casa elenco e JSON por slug. Este módulo não calcula score: só lê,
confere e diz quem ocupa cada cadeira em cada cenário e variante.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from voto_util_base import PARTIDO_CAMPO

ROOT = Path(__file__).resolve().parents[2]
PASTA = ROOT / "analysis/senado_2027"
SAIDA_JSON = ROOT / "docs/assets/senado_2027.json"

CADEIRAS_SENADO = 81

UFS = frozenset(
    (
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    )
)
BLOCOS = ("DB", "D", "CD", "C", "CE", "E")
MANDATOS = (
    "eleito_2026",
    "reeleito_2026",
    "ate_2031",
    "suplente_ate_2031",
    "suplente_em_exercicio",
)
TIPOS_CASO = ("opiniao", "patrimonial", "eleitoral", "8_de_janeiro", "outro")
ESTAGIOS = (
    "condenacao",
    "reu",
    "denuncia_oferecida",
    "indiciado",
    "investigado",
    "alvo_de_busca",
    "citado",
    "eleitoral_pendente",
    "representacao",
    "arquivado",
    "absolvido_ou_trancado",
    "testemunha",
    "acusacao_sem_procedimento",
    "suspenso",
    "condenacao_civel",
    "reu_civel",
    "antigo_sem_desfecho",
    "arquivamento_pedido",
)
FOROS = (
    "STF",
    "STJ",
    "TSE",
    "TRF",
    "primeira_instancia",
    "PF",
    "MP",
    "outro",
    "nao_informado",
)
TIPOS_SINAL = (
    "declaracao_pro_impeachment",
    "assinatura_pedido_impeachment",
    "cpi_contra_ministros",
    "voto_pec8_sim",
    "voto_pec8_nao",
    "voto_pec8_ausente",
    "projeto_ou_pec_contra_stf",
    "declaracao_contra_impeachment",
    "dialogavel_segundo_stf",
    "sem_posicao_localizada",
    "defesa_do_stf",
    "acao_judicial_contra_ministro",
    "representacao_administrativa_contra_ministro",
    "sondagem_com_ministro",
    "nao_assinou_pedido",
    "autoria_pedido_impeachment",
)
SINAL_SEM_FONTE = "sem_posicao_localizada"
ACESSOS = ("pagina", "trecho_de_busca", "relatorio_anterior")
CONFIANCAS = ("alta", "media", "baixa")
RELATORIOS = ("claude", "gemini", "chatgpt", "perplexity")

# O contrato lista quatro tipos; o elenco usa também `suplente` para a cadeira
# que um suplente assume em definitivo (Cleitinho e Moro eleitos governadores).
TIPOS_CONTINGENCIA = (
    "segundo_turno_governo",
    "sub_judice",
    "licenca",
    "ministerio",
    "suplente",
    "cassacao_pendente",
)
# Suplente que já exerce o mandato hoje: ocupa a cadeira no cenário de governo
# Lula; no de governo Flávio o titular volta em 01/01/2027.
CONTINGENCIA_EXERCICIO = ("ministerio", "licenca")
CONTINGENCIA_SEGUNDO_TURNO = "segundo_turno_governo"
CONTINGENCIA_SUB_JUDICE = "sub_judice"
CONTINGENCIA_COM_SUBSTITUTO = (*CONTINGENCIA_EXERCICIO, CONTINGENCIA_SEGUNDO_TURNO)

CENARIOS = ("flavio", "lula")
ROTULO_CENARIO = {"flavio": "governo Flávio Bolsonaro", "lula": "governo Lula"}
VARIANTES = {
    "base": "Elenco projetado para 01/02/2027.",
    "suplentes_segundo_turno": (
        "Os senadores que disputam governo estadual no 2º turno vencem e os "
        "suplentes assumem a cadeira."
    ),
    "cadeira_sub_judice_vaga": (
        "O registro sub judice cai e a cadeira fica vazia até nova eleição; "
        "cadeira vazia conta como voto não."
    ),
}

TRAVESSOES = ("—", "―")
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DATA_ISO = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")

# Campo de PARTIDO_CAMPO (classificação editorial da casa) para bloco, usado
# apenas para substituto sem JSON próprio. Nunca produz DB: núcleo
# bolsonarista é juízo por pessoa, não por sigla.
CAMPO_BLOCO = {
    "direita": "D",
    "centro-direita": "CD",
    "centro": "C",
    "centro-esquerda": "CE",
    "esquerda": "E",
}

# Fonte oficial para a regra de confiança alta (seção 2 do CONTRATO).
DOMINIOS_OFICIAIS = (
    "stf.jus.br",
    "mpf.mp.br",
    "tse.jus.br",
    "senado.leg.br",
    "agenciabrasil.ebc.com.br",
)

CAMPOS_ELENCO = ("slug", "cadeira", "nome", "partido", "uf", "mandato", "bloco")
CAMPOS_SENADOR = (
    "slug",
    "nome",
    "partido",
    "uf",
    "mandato",
    "bloco",
    "bloco_justificativa",
    "alinhado_governo_lula",
    "votacao_2026",
    "casos",
    "sinais_contrapeso",
    "nota_editorial",
    "scores_anteriores",
    "verificado_em",
)
CAMPOS_CASO = (
    "id",
    "titulo",
    "tipo",
    "estagio",
    "foro",
    "relator",
    "data_fato",
    "data_ultima_decisao",
    "resumo",
    "defesa",
    "fontes",
    "confianca",
    "nos_relatorios",
)
CAMPOS_SINAL = ("tipo", "alvo", "data", "resumo", "fontes")
CAMPOS_FONTE = ("url", "veiculo", "data", "titulo", "acesso")


class ErroEsquema(Exception):
    """Dados de entrada fora do contrato; a mensagem lista cada problema."""


@dataclass
class Dados:
    """Tudo o que o motor lê, já validado e casado."""

    pasta: Path
    elenco: dict
    cadeiras: list[dict]
    senadores: dict[str, dict]
    substitutos: dict[str, dict]
    origem: dict[str, str]
    contexto: dict | None
    arbitragem: dict | None
    arquivos: dict[str, str]
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def pessoas(self) -> list[dict]:
        """Titulares na ordem do elenco, depois os substitutos."""
        vistos: set[str] = set()
        saida = []
        for cad in self.cadeiras:
            for pessoa in (
                self.senadores.get(cad["slug"]),
                self.substitutos.get(cad["cadeira"]),
            ):
                if pessoa and pessoa["slug"] not in vistos:
                    vistos.add(pessoa["slug"])
                    saida.append(pessoa)
        return saida


class _Relato:
    """Acumula erros e avisos com o arquivo como prefixo."""

    def __init__(self, prefixo: str) -> None:
        self.prefixo = prefixo
        self.erros: list[str] = []
        self.avisos: list[str] = []

    def erro(self, msg: str) -> None:
        self.erros.append(f"{self.prefixo}: {msg}")

    def aviso(self, msg: str) -> None:
        self.avisos.append(f"{self.prefixo}: {msg}")


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, só letras, dígitos e espaço simples."""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).split())


def slug_de(nome: str) -> str:
    return normalizar(nome).replace(" ", "-")


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def travessoes(obj: Any, caminho: str = "") -> list[str]:
    """Caminhos de toda chave ou string que contém travessão."""
    achados: list[str] = []
    if isinstance(obj, str):
        if any(t in obj for t in TRAVESSOES):
            achados.append(caminho or "(raiz)")
    elif isinstance(obj, dict):
        for chave, valor in obj.items():
            aqui = f"{caminho}.{chave}" if caminho else str(chave)
            if any(t in str(chave) for t in TRAVESSOES):
                achados.append(f"{aqui} (chave)")
            achados.extend(travessoes(valor, aqui))
    elif isinstance(obj, list):
        for i, valor in enumerate(obj):
            achados.extend(travessoes(valor, f"{caminho}[{i}]"))
    return achados


def precisao_data(valor: Any) -> str | None:
    """`dia`, `mes` ou `ano` para data ISO 8601 válida (AAAA-MM-DD, AAAA-MM, AAAA).

    Precisão reduzida é ISO e evita inventar dia ou mês que a fonte não dá.
    Devolve None para qualquer outra coisa, inclusive mês 13 ou 30/02.
    """
    if not isinstance(valor, str):
        return None
    achado = DATA_ISO.match(valor)
    if not achado:
        return None
    ano, mes, dia = achado.groups()
    try:
        date(int(ano), int(mes or 1), int(dia or 1))
    except ValueError:
        return None
    return "dia" if dia else "mes" if mes else "ano"


def data_iso(valor: Any) -> date | None:
    """Data completa AAAA-MM-DD válida, ou None."""
    return date.fromisoformat(valor) if precisao_data(valor) == "dia" else None


def ano_de(valor: Any) -> int | None:
    """Ano de uma data ISO válida de qualquer precisão."""
    return int(valor[:4]) if precisao_data(valor) else None


def _texto(r: _Relato, obj: dict, chave: str, onde: str, *, nulo: bool = False):
    valor = obj.get(chave)
    if valor is None and nulo:
        return None
    if not isinstance(valor, str) or not valor.strip():
        r.erro(f"{onde}.{chave} precisa ser texto não vazio")
        return None
    return valor


def _enum(r: _Relato, obj: dict, chave: str, opcoes: tuple, onde: str):
    valor = obj.get(chave)
    if valor not in opcoes:
        r.erro(f"{onde}.{chave} = {valor!r} fora do enum {list(opcoes)}")
        return None
    return valor


def _data(
    r: _Relato, obj: dict, chave: str, onde: str, *, nulo: bool = True, parcial=True
) -> str | None:
    """Valida a data e devolve o texto quando válido."""
    valor = obj.get(chave)
    if valor is None:
        if not nulo:
            r.erro(f"{onde}.{chave} é obrigatório (AAAA-MM-DD)")
        return None
    precisao = precisao_data(valor)
    if precisao is None or (precisao != "dia" and not parcial):
        r.erro(f"{onde}.{chave} = {valor!r} não é data ISO AAAA-MM-DD válida")
        return None
    if precisao != "dia":
        r.aviso(f"{onde}.{chave} = {valor!r} com precisão reduzida ({precisao})")
    return valor


def _url_valida(valor: Any) -> bool:
    return isinstance(valor, str) and valor.startswith(("http://", "https://"))


def _campos(r: _Relato, obj: Any, obrigatorios: tuple, onde: str) -> bool:
    if not isinstance(obj, dict):
        r.erro(f"{onde} precisa ser objeto")
        return False
    faltam = [c for c in obrigatorios if c not in obj]
    if faltam:
        r.erro(f"{onde} sem campo obrigatório {faltam}")
    sobram = sorted(set(obj) - set(obrigatorios))
    if sobram:
        r.aviso(f"{onde} com campo fora do contrato {sobram}")
    return True


def _host(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return host.removeprefix("www.")


def fonte_oficial(fonte: dict) -> bool:
    url = fonte.get("url")
    if not isinstance(url, str) or not _url_valida(url):
        return False
    partes = urlparse(url)
    host = _host(url)
    if host == "gov.br" and partes.path.lower().startswith("/pf"):
        return True
    return any(host == d or host.endswith("." + d) for d in DOMINIOS_OFICIAIS)


def confianca_sustentada(fontes: list[dict]) -> bool:
    """Regra do contrato para `confianca: alta`."""
    lidas = [f for f in fontes if isinstance(f, dict) and f.get("acesso") == "pagina"]
    if any(fonte_oficial(f) for f in lidas):
        return True
    hosts = {_host(f["url"]) for f in lidas if _url_valida(f.get("url"))}
    return len(hosts) >= 2


def _fonte(r: _Relato, fonte: Any, onde: str) -> None:
    if not _campos(r, fonte, CAMPOS_FONTE, onde):
        return
    acesso = _enum(r, fonte, "acesso", ACESSOS, onde)
    url = fonte.get("url")
    if url is None:
        if acesso != "relatorio_anterior":
            r.erro(f"{onde}.url nula só é aceita com acesso relatorio_anterior")
    elif not _url_valida(url):
        r.erro(f"{onde}.url = {url!r} não começa com http(s)://")
    _texto(r, fonte, "veiculo", onde)
    _texto(r, fonte, "titulo", onde, nulo=True)
    _data(r, fonte, "data", onde)


def _fontes(r: _Relato, obj: dict, onde: str, *, vazia: bool = False) -> list:
    fontes = obj.get("fontes")
    if not isinstance(fontes, list):
        r.erro(f"{onde}.fontes precisa ser lista")
        return []
    if not fontes and not vazia:
        r.erro(f"{onde}.fontes vazia: todo fato precisa de URL de origem")
    for i, fonte in enumerate(fontes):
        _fonte(r, fonte, f"{onde}.fontes[{i}]")
    return fontes


def _caso(r: _Relato, caso: Any, onde: str) -> None:
    if not _campos(r, caso, CAMPOS_CASO, onde):
        return
    _texto(r, caso, "id", onde)
    _texto(r, caso, "titulo", onde)
    _enum(r, caso, "tipo", TIPOS_CASO, onde)
    _enum(r, caso, "estagio", ESTAGIOS, onde)
    _enum(r, caso, "foro", FOROS, onde)
    _texto(r, caso, "relator", onde, nulo=True)
    fato = _data(r, caso, "data_fato", onde)
    decisao = _data(r, caso, "data_ultima_decisao", onde)
    if fato and decisao:
        comum = min(len(fato), len(decisao))
        if decisao[:comum] < fato[:comum]:
            r.aviso(f"{onde}: data_ultima_decisao anterior a data_fato")
    _texto(r, caso, "resumo", onde)
    _texto(r, caso, "defesa", onde)
    fontes = _fontes(r, caso, onde)
    confianca = _enum(r, caso, "confianca", CONFIANCAS, onde)
    if confianca == "alta" and fontes and not confianca_sustentada(fontes):
        r.aviso(
            f"{onde}: confianca alta sem fonte oficial lida (acesso pagina) nem "
            "dois veículos independentes lidos"
        )
    nos = caso.get("nos_relatorios")
    if not isinstance(nos, dict):
        r.erro(f"{onde}.nos_relatorios precisa ser objeto com {list(RELATORIOS)}")
    else:
        faltam = [k for k in RELATORIOS if k not in nos]
        if faltam:
            r.erro(f"{onde}.nos_relatorios sem {faltam}")
        ruins = [k for k in RELATORIOS if k in nos and not isinstance(nos[k], bool)]
        if ruins:
            r.erro(f"{onde}.nos_relatorios com valor não booleano em {ruins}")
        extras = sorted(set(nos) - set(RELATORIOS))
        if extras:
            r.aviso(f"{onde}.nos_relatorios com chave desconhecida {extras}")


def _sinal(r: _Relato, sinal: Any, onde: str) -> None:
    if not _campos(r, sinal, CAMPOS_SINAL, onde):
        return
    tipo = _enum(r, sinal, "tipo", TIPOS_SINAL, onde)
    _texto(r, sinal, "alvo", onde, nulo=True)
    _data(r, sinal, "data", onde)
    if sinal.get("data") is None and tipo != SINAL_SEM_FONTE:
        r.aviso(f"{onde}.data nula")
    _texto(r, sinal, "resumo", onde)
    _fontes(r, sinal, onde, vazia=tipo == SINAL_SEM_FONTE)


def _numero(valor: Any) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _scores_anteriores(r: _Relato, valor: Any, onde: str) -> None:
    if not isinstance(valor, dict):
        r.erro(f"{onde} precisa ser objeto com {list(RELATORIOS)}")
        return
    extras = sorted(set(valor) - set(RELATORIOS))
    if extras:
        r.aviso(f"{onde} com relatório desconhecido {extras}")
    for nome, notas in valor.items():
        if notas is None:
            continue
        if not isinstance(notas, dict):
            r.erro(f"{onde}.{nome} precisa ser objeto ou null")
            continue
        for chave, nota in notas.items():
            if nota is not None and not _numero(nota):
                r.erro(f"{onde}.{nome}.{chave} = {nota!r} não é número")


def validar_senador(dado: Any, slug_arquivo: str) -> tuple[list[str], list[str]]:
    """Erros e avisos de um JSON de senador contra a seção 2 do contrato."""
    r = _Relato(f"senadores/{slug_arquivo}.json")
    if not _campos(r, dado, CAMPOS_SENADOR, "senador"):
        return r.erros, r.avisos
    slug = dado.get("slug")
    if slug != slug_arquivo:
        r.erro(f"senador.slug = {slug!r} difere do nome do arquivo")
    for chave in ("nome", "partido", "bloco_justificativa", "nota_editorial"):
        _texto(r, dado, chave, "senador")
    if dado.get("uf") not in UFS:
        r.erro(f"senador.uf = {dado.get('uf')!r} não é UF")
    mandato = _enum(r, dado, "mandato", MANDATOS, "senador")
    _enum(r, dado, "bloco", BLOCOS, "senador")
    if not isinstance(dado.get("alinhado_governo_lula"), bool):
        r.erro("senador.alinhado_governo_lula precisa ser true ou false")
    votacao = dado.get("votacao_2026")
    if votacao is None:
        if mandato in ("eleito_2026", "reeleito_2026"):
            r.aviso("senador.votacao_2026 nula para mandato eleito em 2026")
    elif not isinstance(votacao, dict):
        r.erro("senador.votacao_2026 precisa ser objeto ou null")
    else:
        votos = votacao.get("votos")
        if votos is not None and (
            not isinstance(votos, int) or isinstance(votos, bool) or votos < 0
        ):
            r.erro(f"senador.votacao_2026.votos = {votos!r} não é inteiro >= 0")
        fonte = votacao.get("fonte")
        if fonte is not None and not _url_valida(fonte):
            r.erro(f"senador.votacao_2026.fonte = {fonte!r} não é URL")
        extras = sorted(set(votacao) - {"votos", "fonte"})
        if extras:
            r.aviso(f"senador.votacao_2026 com campo fora do contrato {extras}")
    _data(r, dado, "verificado_em", "senador", nulo=False, parcial=False)
    _scores_anteriores(r, dado.get("scores_anteriores"), "senador.scores_anteriores")

    casos = dado.get("casos")
    if not isinstance(casos, list):
        r.erro("senador.casos precisa ser lista")
    else:
        ids = [c.get("id") for c in casos if isinstance(c, dict)]
        repetidos = sorted({i for i in ids if i is not None and ids.count(i) > 1})
        if repetidos:
            r.erro(f"senador.casos com id repetido {repetidos}")
        for i, caso in enumerate(casos):
            _caso(r, caso, f"casos[{i}]")
    sinais = dado.get("sinais_contrapeso")
    if not isinstance(sinais, list):
        r.erro("senador.sinais_contrapeso precisa ser lista")
    else:
        for i, sinal in enumerate(sinais):
            _sinal(r, sinal, f"sinais_contrapeso[{i}]")
    for caminho in travessoes(dado):
        r.erro(f"travessão em {caminho}")
    return r.erros, r.avisos


def validar_elenco(elenco: Any) -> tuple[list[str], list[str]]:
    """Erros e avisos do elenco contra a seção 1 do contrato."""
    r = _Relato("elenco.json")
    if not isinstance(elenco, dict) or not isinstance(elenco.get("cadeiras"), list):
        r.erro("elenco precisa ser objeto com a lista `cadeiras`")
        return r.erros, r.avisos
    if elenco.get("referencia") is not None and data_iso(elenco["referencia"]) is None:
        r.erro(f"referencia = {elenco['referencia']!r} não é data ISO")
    cadeiras = elenco["cadeiras"]
    if len(cadeiras) != CADEIRAS_SENADO:
        r.aviso(f"{len(cadeiras)} cadeiras; o Senado tem {CADEIRAS_SENADO}")
    vistos_slug: set[str] = set()
    vistos_cadeira: set[str] = set()
    for i, cad in enumerate(cadeiras):
        onde = f"cadeiras[{i}]"
        if not isinstance(cad, dict):
            r.erro(f"{onde} precisa ser objeto")
            continue
        faltam = [c for c in (*CAMPOS_ELENCO, "contingencia") if c not in cad]
        if faltam:
            r.erro(f"{onde} sem campo obrigatório {faltam}")
            continue
        slug = cad["slug"]
        if not isinstance(slug, str) or not SLUG.match(slug):
            r.erro(f"{onde}.slug = {slug!r} fora do padrão kebab-case")
        elif slug in vistos_slug:
            r.erro(f"{onde}.slug {slug!r} repetido")
        vistos_slug.add(slug)
        if cad["cadeira"] in vistos_cadeira:
            r.erro(f"{onde}.cadeira {cad['cadeira']!r} repetida")
        vistos_cadeira.add(cad["cadeira"])
        for chave in ("cadeira", "nome", "partido"):
            _texto(r, cad, chave, onde)
        if cad["uf"] not in UFS:
            r.erro(f"{onde}.uf = {cad['uf']!r} não é UF")
        _enum(r, cad, "mandato", MANDATOS, onde)
        _enum(r, cad, "bloco", BLOCOS, onde)
        cont = cad["contingencia"]
        if cont is None:
            continue
        if not isinstance(cont, dict):
            r.erro(f"{onde}.contingencia precisa ser objeto ou null")
            continue
        tipo = _enum(r, cont, "tipo", TIPOS_CONTINGENCIA, f"{onde}.contingencia")
        sub = cont.get("substituto")
        if sub is None:
            if tipo in CONTINGENCIA_COM_SUBSTITUTO:
                r.erro(f"{onde}.contingencia do tipo {tipo} exige substituto")
        elif not isinstance(sub, dict):
            r.erro(f"{onde}.contingencia.substituto precisa ser objeto ou null")
        else:
            _texto(r, sub, "nome", f"{onde}.contingencia.substituto")
            _texto(r, sub, "partido", f"{onde}.contingencia.substituto")
            slug_sub = sub.get("slug")
            if slug_sub is not None and not (
                isinstance(slug_sub, str) and SLUG.match(slug_sub)
            ):
                r.erro(f"{onde}.contingencia.substituto.slug fora do padrão")
        _texto(r, cont, "nota", f"{onde}.contingencia", nulo=True)
    for caminho in travessoes(elenco):
        r.erro(f"travessão em {caminho}")
    return r.erros, r.avisos


def slug_substituto(cadeira: dict) -> str | None:
    sub = (cadeira.get("contingencia") or {}).get("substituto")
    if not isinstance(sub, dict) or not sub.get("nome"):
        return None
    return sub.get("slug") or slug_de(sub["nome"])


def bloco_por_partido(partido: str | None) -> str | None:
    if not partido:
        return None
    campo = PARTIDO_CAMPO.get(partido.upper()) or PARTIDO_CAMPO.get(
        normalizar(partido).upper()
    )
    return CAMPO_BLOCO.get(campo) if campo else None


def substituto_por_partido(cadeira: dict) -> dict | None:
    """Registro mínimo de substituto sem JSON: bloco pelo partido, sem fatos."""
    sub = cadeira["contingencia"]["substituto"]
    bloco = bloco_por_partido(sub.get("partido"))
    if bloco is None:
        return None
    return {
        "slug": slug_substituto(cadeira),
        "nome": sub["nome"],
        "partido": sub["partido"],
        "uf": cadeira["uf"],
        "mandato": "suplente_ate_2031",
        "bloco": bloco,
        "bloco_justificativa": (
            "Sem JSON próprio nesta rodada: bloco derivado do partido "
            f"{sub['partido']} pela classificação editorial da casa "
            "(PARTIDO_CAMPO), sem fato nem sinal pesquisado."
        ),
        "alinhado_governo_lula": False,
        "votacao_2026": None,
        "casos": [],
        "sinais_contrapeso": [],
        "nota_editorial": None,
        "scores_anteriores": {},
        "verificado_em": None,
    }


def casar(
    cadeiras: list[dict], senadores: dict[str, dict]
) -> tuple[dict[str, dict], dict[str, str], list[str], list[str]]:
    """Casa elenco e JSON por slug.

    Devolve (substitutos por cadeira, origem por slug, erros, avisos). Cadeira
    sem JSON do titular e JSON sem cadeira são erros; substituto sem JSON é
    aviso e recebe o registro mínimo de `substituto_por_partido`.
    """
    erros: list[str] = []
    avisos: list[str] = []
    substitutos: dict[str, dict] = {}
    origem = dict.fromkeys(senadores, "json")
    esperados: set[str] = set()
    for cad in cadeiras:
        slug = cad["slug"]
        esperados.add(slug)
        rotulo = f"cadeira {cad['cadeira']} ({slug})"
        pessoa = senadores.get(slug)
        if pessoa is None:
            erros.append(f"{rotulo}: sem JSON em senadores/{slug}.json")
        else:
            for chave in ("uf", "bloco", "mandato"):
                if pessoa.get(chave) != cad.get(chave):
                    erros.append(
                        f"{rotulo}: {chave} no JSON = {pessoa.get(chave)!r}, "
                        f"no elenco = {cad.get(chave)!r}"
                    )
            if str(pessoa.get("partido", "")).upper() != str(cad["partido"]).upper():
                avisos.append(
                    f"{rotulo}: partido no JSON = {pessoa.get('partido')!r}, "
                    f"no elenco = {cad['partido']!r}"
                )
            if normalizar(str(pessoa.get("nome", ""))) != normalizar(cad["nome"]):
                avisos.append(
                    f"{rotulo}: nome no JSON = {pessoa.get('nome')!r}, "
                    f"no elenco = {cad['nome']!r}"
                )
        slug_sub = slug_substituto(cad)
        if slug_sub is None:
            continue
        esperados.add(slug_sub)
        sub = cad["contingencia"]["substituto"]
        if slug_sub in senadores:
            pessoa_sub = senadores[slug_sub]
            if pessoa_sub.get("uf") != cad["uf"]:
                erros.append(
                    f"{rotulo}: substituto {slug_sub} com uf "
                    f"{pessoa_sub.get('uf')!r} diferente da cadeira"
                )
            if (
                str(pessoa_sub.get("partido", "")).upper()
                != str(sub["partido"]).upper()
            ):
                avisos.append(
                    f"{rotulo}: partido do substituto no JSON = "
                    f"{pessoa_sub.get('partido')!r}, no elenco = {sub['partido']!r}"
                )
            substitutos[cad["cadeira"]] = pessoa_sub
            continue
        registro = substituto_por_partido(cad)
        if registro is None:
            erros.append(
                f"{rotulo}: substituto {slug_sub} sem JSON e com partido "
                f"{sub.get('partido')!r} fora de PARTIDO_CAMPO"
            )
            continue
        avisos.append(
            f"{rotulo}: substituto {slug_sub} sem JSON; bloco {registro['bloco']} "
            f"derivado do partido {sub['partido']}"
        )
        substitutos[cad["cadeira"]] = registro
        origem[slug_sub] = "partido"
    for slug in sorted(set(senadores) - esperados):
        erros.append(f"senadores/{slug}.json: JSON sem cadeira no elenco")
    return substitutos, origem, erros, avisos


def _rotulo(caminho: Path, pasta: Path) -> str:
    try:
        return caminho.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return caminho.resolve().relative_to(pasta.resolve()).as_posix()


def _ler(caminho: Path, erros: list[str], pasta: Path) -> Any:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        erros.append(f"{_rotulo(caminho, pasta)}: JSON inválido ({exc})")
        return None


def carregar(pasta: Path = PASTA) -> Dados:
    """Lê, valida e casa. Nunca levanta exceção por dado ruim: acumula erros."""
    pasta = Path(pasta)
    erros: list[str] = []
    avisos: list[str] = []
    arquivos: dict[str, str] = {}

    caminho_elenco = pasta / "elenco.json"
    if not caminho_elenco.exists():
        raise ErroEsquema(f"elenco não encontrado em {caminho_elenco}")
    elenco = _ler(caminho_elenco, erros, pasta)
    arquivos[_rotulo(caminho_elenco, pasta)] = sha256(caminho_elenco)
    if elenco is not None:
        e, a = validar_elenco(elenco)
        erros += e
        avisos += a
    cadeiras_ok = (
        isinstance(elenco, dict)
        and isinstance(elenco.get("cadeiras"), list)
        and all(
            isinstance(c, dict)
            and all(k in c for k in (*CAMPOS_ELENCO, "contingencia"))
            for c in elenco["cadeiras"]
        )
    )
    cadeiras = elenco["cadeiras"] if cadeiras_ok else []

    senadores: dict[str, dict] = {}
    for caminho in sorted((pasta / "senadores").glob("*.json")):
        arquivos[_rotulo(caminho, pasta)] = sha256(caminho)
        dado = _ler(caminho, erros, pasta)
        if dado is None:
            continue
        e, a = validar_senador(dado, caminho.stem)
        erros += e
        avisos += a
        if isinstance(dado, dict):
            senadores[caminho.stem] = dado

    contexto = None
    caminho_contexto = pasta / "contexto.json"
    if caminho_contexto.exists():
        arquivos[_rotulo(caminho_contexto, pasta)] = sha256(caminho_contexto)
        contexto = _ler(caminho_contexto, erros, pasta)
        if contexto is not None and not isinstance(contexto, dict):
            erros.append("contexto.json: precisa ser objeto")
            contexto = None
    arbitragem = None
    caminho_arbitragem = pasta / "arbitragem.json"
    if caminho_arbitragem.exists():
        arquivos[_rotulo(caminho_arbitragem, pasta)] = sha256(caminho_arbitragem)
        arbitragem = _ler(caminho_arbitragem, erros, pasta)
        if arbitragem is not None and not isinstance(arbitragem, dict):
            erros.append("arbitragem.json: precisa ser objeto")
            arbitragem = None
        for caminho in travessoes(contexto) if contexto else []:
            erros.append(f"contexto.json: travessão em {caminho}")

    substitutos: dict[str, dict] = {}
    origem: dict[str, str] = dict.fromkeys(senadores, "json")
    if cadeiras:
        substitutos, origem, e, a = casar(cadeiras, senadores)
        erros += e
        avisos += a
    return Dados(
        pasta=pasta,
        elenco=elenco if isinstance(elenco, dict) else {},
        cadeiras=cadeiras,
        senadores=senadores,
        substitutos=substitutos,
        origem=origem,
        contexto=contexto,
        arbitragem=arbitragem,
        arquivos=arquivos,
        erros=erros,
        avisos=avisos,
    )


def exigir_valido(dados: Dados) -> None:
    if dados.erros:
        linhas = "\n".join(f"  - {e}" for e in dados.erros)
        raise ErroEsquema(f"{len(dados.erros)} erro(s) de esquema:\n{linhas}")


def ocupantes(dados: Dados, cenario: str, variante: str) -> list[dict | None]:
    """Ocupante de cada cadeira, na ordem do elenco; None é cadeira vazia."""
    if cenario not in CENARIOS:
        raise ValueError(f"cenário {cenario!r} fora de {CENARIOS}")
    if variante not in VARIANTES:
        raise ValueError(f"variante {variante!r} fora de {list(VARIANTES)}")
    saida: list[dict | None] = []
    for cad in dados.cadeiras:
        tipo = (cad.get("contingencia") or {}).get("tipo")
        pessoa: dict | None = dados.senadores[cad["slug"]]
        if cenario == "lula" and tipo in CONTINGENCIA_EXERCICIO:
            pessoa = dados.substitutos[cad["cadeira"]]
        if variante == "suplentes_segundo_turno" and tipo == CONTINGENCIA_SEGUNDO_TURNO:
            pessoa = dados.substitutos[cad["cadeira"]]
        if variante == "cadeira_sub_judice_vaga" and tipo == CONTINGENCIA_SUB_JUDICE:
            pessoa = None
        saida.append(pessoa)
    return saida
