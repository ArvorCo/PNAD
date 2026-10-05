"""Peças comuns da página do dossiê da apuração: formato, cores, leitura e blocos HTML.

Regra do capítulo defensivo: cada capítulo declara os arquivos de que depende.
Arquivo ausente vira bloco ``pendente``; chave ausente vira aviso no terminal e
bloco ``pendente`` com o nome da chave, nunca exceção que derruba o build.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DADOS = ROOT / "analysis/apuracao_2026/dados"
MEMOS = ROOT / "analysis/apuracao_2026"
SLUG = "apuracao_1o_turno_2026"
URL = f"https://brasil.arvor.co/{SLUG}.html"

PAPER = "#f4f0e6"
INK = "#192e2b"
MUTED = "#535b54"
GOLD = "#7d5b00"
LINE = "#cbc5b5"
LULA = "#b02f21"
FLAVIO = "#1457aa"
OUTROS = "#0f7f5f"
OUTROS_TXT = "#0b6650"
CINZA = "#9a9c94"

CAMPOS = ["esquerda", "centro-esquerda", "centro", "centro-direita", "direita"]
COR_CAMPO = {
    "esquerda": "#b02f21",
    "centro-esquerda": "#d9775f",
    "centro": "#8a7a3a",
    "centro-direita": "#4f7fc2",
    "direita": "#1457aa",
    "indefinido": "#b9bcc2",
}
ROTULO_CAMPO = {
    "esquerda": "Esquerda",
    "centro-esquerda": "Centro-esquerda",
    "centro": "Centro",
    "centro-direita": "Centro-direita",
    "direita": "Direita",
    "indefinido": "Indefinido",
}
CANDIDATO = {
    "flavio": ("Flávio Bolsonaro", FLAVIO),
    "lula": ("Lula", LULA),
    "cury": ("Augusto Cury", OUTROS),
    "renan": ("Renan Santos", "#3d8a74"),
    "renan_santos": ("Renan Santos", "#3d8a74"),
    "caiado": ("Ronaldo Caiado", "#6aa392"),
    "zema": ("Romeu Zema", "#8fb8aa"),
    "outros": ("Outros", CINZA),
}
NOME_UF = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso", "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco",
    "PI": "Piauí", "PR": "Paraná", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul", "SC": "Santa Catarina",
    "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins", "ZZ": "Exterior",
}  # fmt: skip


# ------------------------------------------------------------------ formato


def num(x: float | None, casas: int = 1) -> str:
    """Número no padrão brasileiro: 47,03 e 1.234,5."""
    if x is None:
        return "s/d"
    texto = f"{x:,.{casas}f}"
    return texto.replace(",", " ").replace(".", ",").replace(" ", ".")


def inteiro(x: float | None) -> str:
    if x is None:
        return "s/d"
    return f"{round(x):,}".replace(",", ".")


def sinal(x: float | None, casas: int = 1) -> str:
    """Sinal explícito, com o menos tipográfico (U+2212)."""
    if x is None:
        return "s/d"
    if round(x, casas) == 0:
        return num(0, casas)
    return ("+" if x > 0 else "−") + num(abs(x), casas)


def sinal_int(x: float | None) -> str:
    if x is None:
        return "s/d"
    return ("+" if x > 0 else "−" if x < 0 else "") + inteiro(abs(x))


def milhoes(x: float, casas: int = 2) -> str:
    """2.224.965 vira '2,22 milhões'; abaixo de um milhão, 'mil'."""
    if abs(x) >= 1_000_000:
        valor = num(abs(x) / 1_000_000, casas)
        return f"{valor} {'milhão' if round(abs(x) / 1e6, casas) < 2 else 'milhões'}"
    return f"{num(abs(x) / 1000, 0)} mil"


def hora(s: str | None, segundos: bool = False) -> str:
    """'2026-10-04 18:48:59' vira '18:48' (ou '18:48:59')."""
    if not s:
        return "s/d"
    parte = s.strip().split(" ")[-1]
    return parte[:8] if segundos else parte[:5]


def data_hora(s: str | None) -> str:
    """'2026-10-05 02:59:31' vira '05/10, 02:59'."""
    if not s:
        return "s/d"
    d, _, h = s.strip().partition(" ")
    if "-" in d:
        _, m, dia = d.split("-")
        return f"{dia}/{m}, {h[:5]}"
    return s


def nome_proprio(s: str) -> str:
    """'FLAVIO BOLSONARO' vira 'Flavio Bolsonaro', preservando siglas curtas."""
    minus = {"de", "da", "do", "dos", "das", "e"}
    siglas = {"JHC"}
    out = []
    for i, p in enumerate(s.split()):
        if p in siglas:
            out.append(p)
            continue
        low = p.lower()
        out.append(low if (i and low in minus) else low.capitalize())
    return " ".join(out)


def cor_campo(campo: str | None) -> str:
    return COR_CAMPO.get(campo or "indefinido", COR_CAMPO["indefinido"])


# ------------------------------------------------------------------ leitura


@dataclass
class Fonte:
    caminho: Path
    sha256: str
    gerado_em: str | None


@dataclass
class Dados:
    """Leitor dos JSONs do dossiê. Guarda hash e data de geração de cada um."""

    pasta: Path = DADOS
    cache: dict = field(default_factory=dict)
    fontes: dict = field(default_factory=dict)
    avisos: list = field(default_factory=list)

    def get(self, nome: str):
        if nome in self.cache:
            return self.cache[nome]
        caminho = self.pasta / nome
        if not caminho.exists():
            self.cache[nome] = None
            return None
        bruto = caminho.read_bytes()
        try:
            dado = json.loads(bruto)
        except json.JSONDecodeError as erro:
            self.aviso(f"{nome}: JSON inválido ({erro})")
            self.cache[nome] = None
            return None
        self.cache[nome] = dado
        self.fontes[nome] = Fonte(
            caminho, hashlib.sha256(bruto).hexdigest(), gerado_em_de(dado)
        )
        return dado

    def aviso(self, texto: str) -> None:
        self.avisos.append(texto)
        print(f"aviso: {texto}")


def gerado_em_de(dado) -> str | None:
    if not isinstance(dado, dict):
        return None
    meta = dado.get("meta")
    if isinstance(meta, dict) and meta.get("gerado_em"):
        return meta["gerado_em"]
    return dado.get("gerado_em")


def caminho(dado, chave: str, padrao=None):
    """Lê 'a.b.c' sem levantar exceção."""
    atual = dado
    for parte in chave.split("."):
        if isinstance(atual, dict) and parte in atual:
            atual = atual[parte]
        elif isinstance(atual, list) and parte.isdigit() and int(parte) < len(atual):
            atual = atual[int(parte)]
        else:
            return padrao
    return atual


def checar(dados: Dados, nome: str, chaves: Iterable[str]) -> list[str]:
    """Avisa, sem parar o build, quais chaves esperadas faltam num arquivo."""
    dado = dados.get(nome)
    faltam = [c for c in chaves if caminho(dado, c) is None]
    if faltam:
        dados.aviso(f"{nome}: chaves ausentes {', '.join(faltam)}")
    return faltam


# ------------------------------------------------------------------ HTML


@dataclass
class Capitulo:
    ident: str
    numero: str
    curto: str
    titulo: str
    arquivos: tuple[str, ...]
    render: Callable[[Dados], str]


def pendente(cap: Capitulo, motivos: list[str]) -> str:
    lista = ", ".join(f"<code>{escape(m)}</code>" for m in motivos)
    return (
        f'<section class="pendente" id="{cap.ident}">'
        f'<div class="section-head"><p class="kicker">{cap.numero} / CAPÍTULO</p>'
        f"<h2>{cap.titulo}</h2></div>"
        f"<p>capítulo em preparação: {lista}</p></section>"
    )


def bloco_pendente(nome: str) -> str:
    return f'<div class="pendente-bloco">capítulo em preparação: <code>{escape(nome)}</code></div>'


ERROS_DE_DADO = (KeyError, IndexError, TypeError, ValueError, ZeroDivisionError)


def montar(cap: Capitulo, dados: Dados) -> tuple[str, bool]:
    """Devolve (html, completo). Nunca levanta exceção por dado ausente."""
    faltam = [a for a in cap.arquivos if dados.get(a) is None]
    if faltam:
        dados.aviso(f"capítulo {cap.ident}: falta {', '.join(faltam)}")
        return pendente(cap, faltam), False
    try:
        return cap.render(dados), True
    except ERROS_DE_DADO as erro:
        dados.aviso(f"capítulo {cap.ident}: {type(erro).__name__} {erro}")
        motivo = f"{'/'.join(cap.arquivos)} (chave ausente: {erro})"
        return pendente(cap, [motivo]), False


def secao(cap: Capitulo, titulo_html: str, lead: str) -> str:
    return (
        f'<section id="{cap.ident}"><div class="section-head">'
        f'<p class="kicker">{cap.numero} / {cap.curto.upper()}</p>'
        f'<h2>{titulo_html}</h2><p class="lead">{lead}</p></div>'
    )


def figura(svg: str, legenda: str, larga: bool = True, ident: str = "") -> str:
    classe = "chart-scroll" if larga else "chart-fit"
    idattr = f' id="{ident}"' if ident else ""
    return (
        f'<figure{idattr}><div class="{classe}" tabindex="0">{svg}</div>'
        f"<figcaption>{legenda}</figcaption></figure>"
    )


def figura_dupla(larga: str, estreita: str, legenda: str, ident: str = "") -> str:
    """Duas larguras para a mesma figura; abaixo de 720 px entra a empilhada."""
    idattr = f' id="{ident}"' if ident else ""
    return (
        f'<figure{idattr}><div class="fig-larga">{larga}</div>'
        f'<div class="fig-estreita">{estreita}</div>'
        f"<figcaption>{legenda}</figcaption></figure>"
    )


def _celula_num(v) -> bool:
    if isinstance(v, (int, float)):
        return True
    t = str(v).strip().replace(".", "").replace(",", "").replace("%", "")
    t = t.replace("+", "").replace("−", "").replace(" pp", "").replace(" ", "")
    return t.isdigit()


def tabela(cabecalho: list[str], linhas: list[list], legenda: str = "") -> str:
    """Tabela com colunas numéricas marcadas por `class="num"`."""
    if not linhas:
        return ""
    ncol = len(cabecalho)
    numericas = []
    for j in range(ncol):
        cel = [r[j] for r in linhas if j < len(r) and str(r[j]).strip()]
        numericas.append(
            bool(cel) and sum(_celula_num(c) for c in cel) / len(cel) >= 0.8
        )
    num_cls = ' class="num"'
    th = "".join(
        f'<th scope="col"{num_cls if numericas[j] else ""}>{c}</th>'
        for j, c in enumerate(cabecalho)
    )
    corpo = []
    for r in linhas:
        cels = []
        for j, v in enumerate(r):
            cls = ' class="num"' if numericas[j] else ""
            tag = "th" if j == 0 else "td"
            scope = ' scope="row"' if j == 0 else ""
            cels.append(f"<{tag}{scope}{cls}>{v}</{tag}>")
        corpo.append("<tr>" + "".join(cels) + "</tr>")
    cap = f"<caption>{legenda}</caption>" if legenda else ""
    return (
        '<div class="table-scroll" tabindex="0"><table>'
        f"{cap}<thead><tr>{th}</tr></thead><tbody>{''.join(corpo)}</tbody></table></div>"
    )


def rotulo(tipo: str) -> str:
    """Selo de natureza do enunciado: verificado, inferência, hipótese, juízo."""
    classes = {
        "verificado": "Verificado",
        "inferencia": "Inferência",
        "hipotese": "Hipótese",
        "juizo": "Juízo editorial",
        "relato": "Relato da imprensa",
    }
    return f'<span class="selo selo-{tipo}">{classes[tipo]}</span>'


def p(texto: str, tipo: str | None = None) -> str:
    return f"<p>{rotulo(tipo) + ' ' if tipo else ''}{texto}</p>"


def cartao(valor: str, legenda: str, cor: str = "") -> str:
    estilo = f' style="color:{cor}"' if cor else ""
    return f"<div><b{estilo}>{valor}</b><span>{legenda}</span></div>"
