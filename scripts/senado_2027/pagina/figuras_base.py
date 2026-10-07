"""Base compartilhada das figuras do Senado de 2027: paleta, formatação, SVG e acesso ao JSON."""

from __future__ import annotations

from html import escape

INK = "#192e2b"
MUTED = "#535b54"
LINE = "#c7c9bb"
GRID = "#e2dfd2"
CARD = "#fffdf8"
TEAL = "#0c7a72"
TEAL_CLARO = "#9fcfc8"
GOLD = "#7d5b00"
RED = "#b02f21"
NEUTRO = "#9aa39b"
FONTE = "IBM Plex Mono, ui-monospace, monospace"

BLOCOS = ("DB", "D", "CD", "C", "CE", "E")
COR_BLOCO = {
    "DB": "#0b3f85",
    "D": "#1457aa",
    "CD": "#4f7fc2",
    "C": "#8a7a3a",
    "CE": "#d9775f",
    "E": "#b02f21",
}
# Contorno mais escuro para que o ponto claro passe de 3:1 sobre o papel.
BORDA_BLOCO = {
    "DB": "#072a59",
    "D": "#0d3b77",
    "CD": "#2f5f9e",
    "C": "#5e5327",
    "CE": "#8f3f2c",
    "E": "#7a1f14",
}
ROTULO_BLOCO = {
    "DB": "direita bolsonarista",
    "D": "direita",
    "CD": "centro-direita",
    "C": "centro",
    "CE": "centro-esquerda",
    "E": "esquerda",
}
ROTULO_CENARIO = {"flavio": "governo Flávio", "lula": "governo Lula"}
ROTULO_ALVO = {"C_imp": "impeachment", "C_pec": "PEC"}
LIMIAR = {"C_pec": 49, "C_imp": 54}
CHAVE_SIM = {"C_pec": "pec", "C_imp": "imp"}

# Faixas de C no hemiciclo: do contrapeso firme ao contra.
FAIXAS_C = (
    (90, 101, "90 ou mais", "#07524c"),
    (80, 90, "80 a 89", TEAL),
    (60, 80, "60 a 79", "#6fb3a9"),
    (40, 60, "40 a 59", "#cfc7a6"),
    (20, 40, "20 a 39", "#d9775f"),
    (-1, 20, "menos de 20", RED),
)
FAIXAS_K = (
    (0, 0, "0"),
    (0.01, 19.99, "1 a 19"),
    (20, 39.99, "20 a 39"),
    (40, 59.99, "40 a 59"),
    (60, 79.99, "60 a 79"),
    (80, 100, "80 a 100"),
)
GRUPOS_TIPO = (
    ("opiniao", "Opinião ou 8 de janeiro"),
    ("patrimonial_ativo", "Patrimonial ativo"),
    ("patrimonial_inativo", "Patrimonial citado ou encerrado"),
    ("eleitoral", "Eleitoral"),
    ("outro", "Outro"),
)


# Utilidades de texto e número


def esc(valor) -> str:
    return escape(str(valor), quote=True)


def fmt(valor: float | None, casas: int = 0) -> str:
    if valor is None:
        return "n/d"
    s = f"{valor:,.{casas}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(valor: float | None, casas: int = 0) -> str:
    return f"{fmt(valor, casas)}%"


def largura(texto: str, tamanho: float) -> float:
    """Largura aproximada de texto em fonte monoespaçada."""
    return len(texto) * 0.6 * tamanho


def txt(
    x: float,
    y: float,
    conteudo: str,
    tamanho: float = 14,
    anchor: str = "start",
    peso: int | None = None,
    cor: str = INK,
    extra: str = "",
) -> str:
    p = f' font-weight="{peso}"' if peso else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{tamanho}" text-anchor="{anchor}" '
        f'fill="{cor}"{p}{extra}>{esc(conteudo)}</text>'
    )


def svg(largura_vb: float, altura_vb: float, rotulo: str, corpo: str, cls: str) -> str:
    return (
        f'<svg class="{cls}" viewBox="0 0 {largura_vb:.0f} {altura_vb:.0f}" '
        f'role="img" aria-label="{esc(rotulo)}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="{FONTE}"><title>{esc(rotulo)}</title>{corpo}</svg>'
    )


def figura(cls: str, conteudo: str, legenda: str, ident: str = "") -> str:
    i = f' id="{ident}"' if ident else ""
    return (
        f'<figure class="sn27-fig {cls}"{i}>{conteudo}'
        f"<figcaption>{legenda}</figcaption></figure>"
    )


# Acesso ao JSON


def ocupantes(data: dict, cenario: str = "flavio") -> list[dict]:
    """Quem ocupa cada uma das 81 cadeiras no cenário, na ordem do elenco."""
    out = []
    for cad in data["elenco"]:
        slug = cad["ocupante"][cenario]
        tit = cad["titular"]
        pessoa = tit if tit["slug"] == slug else cad.get("substituto")
        if not pessoa or pessoa["slug"] != slug:
            raise ValueError(f"ocupante {slug} sem ficha na cadeira {cad['cadeira']}")
        out.append(pessoa)
    return out


def valor_c(pessoa: dict, cenario: str, alvo: str) -> float:
    return float(pessoa["scores"]["cenarios"][cenario][alvo])


def valor_k(pessoa: dict) -> float:
    return float(pessoa["scores"]["K"])


def tipo_dominante(pessoa: dict) -> str | None:
    """Grupo do caso de maior peso em K (None quando K = 0)."""
    casos = pessoa["scores"].get("K_por_caso") or []
    if not casos or valor_k(pessoa) <= 0:
        return None
    maior = max(casos, key=lambda c: c["pontos"])
    tipo = maior["tipo"]
    if tipo in ("opiniao", "8_de_janeiro"):
        return "opiniao"
    if tipo == "patrimonial":
        ativo = maior.get("patrimonial_ativo") or (
            pessoa["scores"].get("K_patrimonial_ativo", 0) > 0
        )
        return "patrimonial_ativo" if ativo else "patrimonial_inativo"
    if tipo == "eleitoral":
        return "eleitoral"
    return "outro"


def sim(data: dict, cenario: str, variante: str = "base") -> dict:
    return data["simulacao"]["cenarios"][cenario][variante]


def sigla(pessoa: dict) -> str:
    return f"{pessoa.get('partido') or 's/partido'}-{pessoa['uf']}"
