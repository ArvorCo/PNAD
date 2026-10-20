"""Textos fixos (janela, limites, decisões), o resumo numérico e o relatório em Markdown."""

from __future__ import annotations

from typing import Any

JANELA = {
    "regra": "das 7h às 18h de Brasília de 04/10 (horas 8 a 18 da série horária)",
    "motivo": "a votação de 2026 foi das 8h às 17h de Brasília em todo o país; a janela tem "
    "uma hora de folga de cada lado",
    "local": {
        "UTC-3 (maior parte do país)": "7h às 18h",
        "UTC-4 (AM, MT, MS, RO, RR)": "6h às 17h",
        "UTC-5 (AC e oeste do AM)": "5h às 16h",
        "UTC-2 (Fernando de Noronha)": "8h às 19h",
    },
    "estrita": "8h às 17h de Brasília (horas 9 a 17), só o horário oficial, sem folga",
    "convencao": "o valor horário da Open-Meteo na hora H é a chuva (ou a rajada máxima) "
    "da hora anterior, de H-1 a H",
}

LIMITES = [
    "Correlação não é causa. Chuva e vento não são sorteados entre locais: regiões que "
    "chovem mais diferem em renda, distância, rede elétrica e hábito de voto. Os controles "
    "(efeito fixo de UF e de município, comparação dentro do prédio) reduzem e não eliminam "
    "essa diferença.",
    "O clima é de reanálise (ERA5 e ERA5-Land pela Open-Meteo) numa célula de 0,25°, cerca "
    "de 28 km: não é a chuva medida no telhado do prédio. Pancada isolada pode não aparecer, "
    "e o erro de medida puxa qualquer associação para perto de zero.",
    "Bateria é operação prevista da urna, não irregularidade. O log registra que a urna "
    "operou com a bateria interna, não por quanto tempo nem se a fila parou: tempo em "
    "bateria não é medido.",
    "A separação entre bateria simultânea (5 ou mais outras seções do município no mesmo "
    "minuto) e isolada vem do mapa de fiscais e exige relógio válido; de 1 a 4 seções "
    "coincidentes fica como intermediária.",
    "A comparação com 2022 usa o 2º turno daquele ano nas seções com o mesmo número em UF, "
    "município e zona. Renumeração e remanejamento entre 2022 e 2026 mudam o eleitorado de "
    "parte dessas seções, e 1º e 2º turno têm motivação diferente.",
    "Abstenção é sempre razão de somas ponderada por aptos; locais pequenos não pesam "
    "como grandes.",
    "Locais sem coordenada no cadastro (ou com coordenada fora do território) ficam sem "
    "clima e fora das análises; o exterior fica fora.",
    "Leitura agregada por seção e por local: nada aqui identifica eleitor.",
    "A previsão para 25/10 é de modelo global a 0,5° e muda todo dia; é indicativo de "
    "atenção para a logística, não previsão do que vai acontecer no prédio.",
]

DECISOES = [
    "Janela de votação no relógio de Brasília. O contrato pedia 7h a 18h locais; como a "
    "votação de 2026 abriu às 8h de Brasília no país inteiro (o primeiro voto tem moda às "
    "8h de Brasília em todas as UFs, controle no payload), a janela local mudaria de "
    "posição no Acre, no Amazonas, em MT, MS, RO e RR e cobriria horas sem votação. A "
    "série da Open-Meteo já vem em Brasília; o fuso entra só na hora local do pico.",
    "Seca é 0,0 mm na precisão da Open-Meteo (menos de 0,05 mm). Faixas: fraca até 5, "
    "moderada até 20, forte até 50 e muito forte acima de 50 mm, limites superiores "
    "fechados. Rajada: até 40, até 60, até 80 e acima de 80 km/h.",
    "A faixa de chuva publicada no mapa usa a chuva do dia inteiro de 04/10; as análises "
    "mostram também a faixa pela chuva das horas de votação.",
    "Intervalo de confiança por bootstrap de células de 0,25° (conglomerado do clima), não "
    "de urnas: urnas da mesma célula dividem a mesma chuva. Grupo com menos de 20 células "
    "(ou comparação dentro de estrato com menos de 10 estratos) fica sem intervalo.",
    "Chuva do dia é o dia de 04/10 no relógio de Brasília (00h às 24h), como a Open-Meteo "
    "entrega com timezone=America/Sao_Paulo; no Acre o dia local começa duas horas depois.",
    "Bateria durante a votação tem como denominador as urnas com log e relógio válido; "
    "bateria em qualquer momento e reinício, as urnas com log.",
    "Odds ratio por 10 mm de chuva e por 10 km/h de rajada, em logística com efeito fixo de "
    "UF, log dos aptos e modelo da urna como controles.",
    "Na regressão de abstenção, efeito fixo de município pela subtração das médias "
    "ponderadas: só municípios com urnas em células de chuva diferente informam o "
    "coeficiente.",
    "Listas de locais curiosos exigem ao menos 200 aptos nas seções casadas com 2022 quando "
    "usam a diferença contra 2022, para que uma seção pequena não domine a lista.",
]


def _g(d: Any, *ch: Any) -> Any:
    for c in ch:
        if d is None:
            return None
        d = d[c] if isinstance(c, int) else d.get(c)
    return d


def resumo(p: dict[str, Any]) -> dict[str, Any]:
    """Números de manchete, lidos do próprio payload (nada digitado à mão)."""
    rb = p["bateria_x_chuva"]["regressoes"]["desfechos"]
    ra = p["abstencao_x_chuva"]["regressoes"]
    out: dict[str, Any] = {
        "bateria_votacao_or_chuva_votacao_10mm": _g(
            rb, "bateria_votacao", 0, "termos", "chuva_votacao_x"
        ),
        "bateria_votacao_or_chuva_diaria_10mm": _g(
            rb, "bateria_votacao", 1, "termos", "chuva_diaria_x"
        ),
        "bateria_votacao_or_rajada_votacao_10kmh": _g(
            rb, "bateria_votacao", 2, "termos", "rajada_votacao_x"
        ),
        "bateria_simultanea_or_chuva_votacao_10mm": _g(
            rb, "bateria_simultanea", 0, "termos", "chuva_votacao_x"
        ),
        "bateria_isolada_or_chuva_votacao_10mm": _g(
            rb, "bateria_isolada", 0, "termos", "chuva_votacao_x"
        ),
        "abstencao_pp_por_10mm_fe_municipio": _g(
            ra,
            "abstencao_2026",
            "chuva_votacao",
            "fe_municipio",
            "termos",
            "chuva_votacao_x",
        ),
        "dif_2022_pp_por_10mm_fe_municipio": _g(
            ra,
            "dif_contra_2022",
            "chuva_votacao",
            "fe_municipio",
            "termos",
            "chuva_votacao_x",
        ),
        "abstencao_bateria_dentro_do_predio_pp": _g(
            p,
            "abstencao_x_bateria",
            "dentro_do_predio",
            "grupos",
            "com bateria durante a votação",
            "abst_vs_ref_pp",
        ),
        "dif_bateria_dentro_do_predio_pp": _g(
            p,
            "abstencao_x_bateria",
            "dentro_do_predio",
            "grupos",
            "com bateria durante a votação",
            "dif_vs_ref_pp",
        ),
    }
    return out


def _ic(x: Any, sufixo: str = "") -> str:
    if not x or x.get("valor") is None:
        return "sem dado"
    if not x.get("ic95"):
        return f"{_br(x['valor'])}{sufixo} ({x.get('nota', 'sem intervalo')})"
    lo, hi = x["ic95"]
    return f"{_br(x['valor'])}{sufixo} (IC 95% {_br(lo)} a {_br(hi)})"


def _or(x: Any) -> str:
    if not x:
        return "sem dado"
    lo, hi = x["ic95"]
    return (
        f"{_br(x['odds_ratio'], 3)} (IC 95% {_br(lo, 3)} a {_br(hi, 3)}; {_p(x['p'])})"
    )


def _coef(x: Any, sufixo: str = " pp") -> str:
    if not x:
        return "sem dado"
    lo, hi = x["ic95"]
    return f"{_br(x['coef'], 3)}{sufixo} (IC 95% {_br(lo, 3)} a {_br(hi, 3)}; {_p(x['p'])})"


def _p(p: float) -> str:
    """Valor-p em português: abaixo de 0,001 vira desigualdade."""
    if p < 0.001:
        return "p < 0,001"
    return "p = " + f"{p:.3f}".replace(".", ",")


def _br(v: Any, casas: int = 2) -> str:
    if v is None:
        return "sem dado"
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    s = f"{v:,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _sig_or(x: dict[str, Any]) -> bool:
    lo, hi = x["ic95"]
    return lo > 1 or hi < 1


def _sig(x: dict[str, Any]) -> bool:
    if not x or not x.get("ic95"):
        return False
    lo, hi = x["ic95"]
    return lo > 0 or hi < 0


def _frase_or(nome: str, x: dict[str, Any] | None, unidade: str) -> str:
    if not x:
        return f"{nome}: sem estimativa."
    if _sig_or(x):
        sentido = "maiores" if x["odds_ratio"] > 1 else "menores"
        return (
            f"{nome}: cada {unidade} se associa a chances {_br(x['odds_ratio'], 2)} vezes "
            f"{sentido} (IC 95% {_br(x['ic95'][0], 2)} a {_br(x['ic95'][1], 2)})."
        )
    return (
        f"{nome}: razão de chances de {_br(x['odds_ratio'], 2)} por {unidade} (IC 95% "
        f"{_br(x['ic95'][0], 2)} a {_br(x['ic95'][1], 2)}), sem associação que se separe "
        "do acaso."
    )


def _frase_pp(nome: str, x: dict[str, Any] | None, por: str = "") -> str:
    if not x or (x.get("valor") is None and x.get("coef") is None):
        return f"{nome}: sem estimativa."
    v = float(x["coef"] if x.get("coef") is not None else x["valor"])
    lo, hi = x["ic95"] if x.get("ic95") else (None, None)
    faixa = f" (IC 95% {_br(lo)} a {_br(hi)})" if lo is not None else ""
    pp = "ponto percentual" if abs(v) < 2 else "pontos percentuais"
    if _sig(x):
        sentido = "a mais" if v > 0 else "a menos"
        return f"{nome}: {_br(abs(v))} {pp} {sentido}{por}{faixa}."
    return f"{nome}: {_br(v)} {pp}{por}{faixa}, que não se separa de zero."


def achados(p: dict[str, Any]) -> list[str]:
    """Frases geradas dos números, nos dois sentidos (inclusive o que contraria)."""
    r = p["resumo"]
    out = [
        _frase_or(
            "Bateria durante a votação e chuva nas horas de votação (efeito fixo de UF)",
            r["bateria_votacao_or_chuva_votacao_10mm"],
            "10 mm",
        ),
        _frase_or(
            "Bateria simultânea no município (assinatura de rede)",
            r["bateria_simultanea_or_chuva_votacao_10mm"],
            "10 mm",
        ),
        _frase_or(
            "Bateria isolada (assinatura de tomada ou fonte)",
            r["bateria_isolada_or_chuva_votacao_10mm"],
            "10 mm",
        ),
        _frase_or(
            "Bateria durante a votação e rajada nas horas de votação",
            r["bateria_votacao_or_rajada_votacao_10kmh"],
            "10 km/h",
        ),
    ]
    rob = _g(
        p,
        "bateria_x_chuva",
        "regressoes",
        "robustez_municipio",
        "bateria_votacao",
        0,
        "termos",
        "chuva_votacao_x",
    )
    out.append(
        _frase_pp(
            "Dentro do mesmo município (probabilidade linear), bateria durante a votação",
            rob,
            " por 10 mm",
        )
    )
    out.append(
        _frase_pp(
            "Abstenção de 2026 e chuva nas horas de votação, dentro do mesmo município",
            r["abstencao_pp_por_10mm_fe_municipio"],
            " por 10 mm",
        )
    )
    out.append(
        _frase_pp(
            "Abstenção de 2026 menos a do 2º turno de 2022, dentro do mesmo município",
            r["dif_2022_pp_por_10mm_fe_municipio"],
            " por 10 mm",
        )
    )
    out.append(
        _frase_pp(
            "Abstenção das urnas com bateria durante a votação contra as do mesmo prédio "
            "sem bateria",
            r["abstencao_bateria_dentro_do_predio_pp"],
        )
    )
    out.append(
        _frase_pp(
            "Mesma comparação dentro do prédio, na diferença contra 2022",
            r["dif_bateria_dentro_do_predio_pp"],
        )
    )
    cad = _g(
        p,
        "cadeia_completa",
        "variantes",
        "chuva_forte_no_dia",
        "abst_alta_por_combinacao",
    )
    if cad:
        txt = "; ".join(
            f"{'com' if c['chuva'] else 'sem'} chuva forte e "
            f"{'com' if c['bateria'] else 'sem'} bateria: {_br(c['abst_alta_pct'])}% "
            f"de {_br(c['urnas'])} urnas"
            for c in cad
        )
        out.append(
            "Cadeia completa (parcela de urnas com abstenção acima da mediana do "
            f"município, que seria 50% sem relação nenhuma): {txt}."
        )
    prev = p.get("previsao_25_10", {})
    if "pais" in prev:
        el = prev["pais"]["eleitores"]
        tot = sum(el.values()) or 1
        out.append(
            f"Previsão para 25/10 gerada em {prev['gerado_em']}: "
            f"{_br(el['alto'])} eleitores ({_br(100 * el['alto'] / tot)}%) em células de "
            f"risco alto e {_br(el['medio'])} ({_br(100 * el['medio'] / tot)}%) em risco "
            "médio; a previsão muda todo dia."
        )
    return out
