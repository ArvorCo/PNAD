"""Textos do capítulo "Exterior" do dossiê do 2º turno; números de ``exterior.json``."""

from __future__ import annotations

from apuracao_2026.pagina_comum import cartao, inteiro, nome_proprio, num, p, sinal


def t1(E: dict) -> dict:
    """Totais do 1º turno somados das cidades (válidos com todos os candidatos)."""
    soma = dict.fromkeys(("aptos", "comparecimento", "validos", "flavio", "lula"), 0)
    for c in E["cidades"]:
        for k in soma:
            soma[k] += c.get(f"t1_{k}") or 0
    out = dict(soma)
    out["pct_comparecimento"] = (
        100 * soma["comparecimento"] / soma["aptos"] if soma["aptos"] else None
    )
    out["pct_flavio"] = (
        100 * soma["flavio"] / soma["validos"] if soma["validos"] else None
    )
    out["pct_lula"] = 100 * soma["lula"] / soma["validos"] if soma["validos"] else None
    return out


def titulo(E: dict) -> str:
    T = E["total"]
    quem = "Lula" if T["pct_lula"] > T["pct_flavio"] else "Flávio"
    return f"Exterior.<br><em>{quem} vence; o comparecimento sobe.</em>"


def lead(E: dict) -> str:
    T, u = E["total"], t1(E)
    return (
        f"Lula {num(T['pct_lula'], 2)}% × Flávio {num(T['pct_flavio'], 2)}% dos válidos em "
        f"{inteiro(T['cidades'])} cidades; comparecimento de {num(T['pct_comparecimento'], 2)}% "
        f"contra {num(u['pct_comparecimento'], 2)}% no 1º turno."
    )


def cartoes(E: dict) -> str:
    T, u = E["total"], t1(E)
    return (
        '<div class="finding-grid">'
        + cartao(f"{num(T['pct_lula'], 2)}%", "Lula nos válidos do exterior", "#b02f21")
        + cartao(
            f"{inteiro(T['margem_lula_votos'])}", "votos de diferença a favor de Lula"
        )
        + cartao(
            f"{num(T['pct_comparecimento'], 2)}%",
            f"comparecimento ({num(u['pct_comparecimento'], 2)}% no 1º turno)",
        )
        + cartao(inteiro(len(E.get("paises") or [])), "países com seção")
        + "</div>"
    )


def abre(E: dict) -> str:
    T, u = E["total"], t1(E)
    return p(
        f"No exterior, {inteiro(T['comparecimento'])} de {inteiro(T['aptos'])} eleitores votaram "
        f"({num(T['pct_comparecimento'], 2)}%, {sinal(T['pct_comparecimento'] - u['pct_comparecimento'], 2)} pp "
        f"contra o 1º turno). Lula teve {inteiro(T['lula'])} votos e Flávio {inteiro(T['flavio'])}: "
        f"{num(T['margem_lula_pp'], 2)} pp de diferença. No 1º turno, com todos os candidatos, Lula "
        f"tinha {num(u['pct_lula'], 2)}% e Flávio {num(u['pct_flavio'], 2)}% dos válidos. O exterior "
        "pesa pouco no total do país e vota diferente de um continente para outro.",
        "verificado",
    )


def _lista(itens: list[str]) -> str:
    if not itens:
        return "nenhum"
    if len(itens) == 1:
        return itens[0]
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def continentes(E: dict) -> str:
    conts = sorted(E["continentes"], key=lambda c: -(c.get("validos") or 0))
    fl = [c for c in conts if (c.get("pct_flavio") or 0) > (c.get("pct_lula") or 0)]
    lu = [c for c in conts if c not in fl]
    pais = sorted(E.get("paises") or [], key=lambda q: -(q.get("validos") or 0))
    frase_p = ""
    if pais:
        q = pais[0]
        nomes = {c.get("pais"): c.get("pais_nome") for c in E["cidades"]}
        frase_p = (
            f" O maior eleitorado, {nomes.get(q.get('pais')) or q.get('pais')}, deu {num(q['pct_flavio'], 2)}% a Flávio, com "
            f"comparecimento de {num(q['pct_comparecimento'], 2)}%."
        )
    base = (
        "Por continente, Flávio lidera "
        + _lista([c["continente"] for c in fl])
        + "; Lula, "
        + _lista([c["continente"] for c in lu])
        + "."
    )
    if conts and conts[0]["continente"] == "Europa":
        base += (
            f" A Europa decide o exterior: {inteiro(conts[0]['validos'])} válidos, Lula "
            f"{num(conts[0]['pct_lula'], 2)}%."
        )
    return p(base + frase_p, "verificado")


def hora(E: dict) -> str:
    ult = E.get("ultimas_a_fechar") or []
    if not ult:
        return ""
    c = ult[0]
    return p(
        f"A última cidade a fechar foi {nome_proprio(c.get('nome', ''))} ({c.get('pais_nome')}), com "
        f"arquivo gerado às {c.get('fechou_gerado_brt') or c.get('fechou_hhmm')} de Brasília. A "
        "totalização impressa no boletim do exterior está no relógio local da cidade; o arquivo do TSE, "
        "no de Brasília. Uma diferença de horas entre as duas colunas é fuso, não atraso.",
        "verificado",
    )


def limites_itens() -> list[str]:
    return [
        "O 1º turno tinha outros candidatos: a comparação de percentuais é entre turnos diferentes.",
        "Hora de fechamento é a da geração do arquivo pelo TSE, em Brasília; a impressa no boletim é local.",
        "Comparecimento no exterior é baixo também porque o cadastro guarda eleitores que mudaram de "
        "cidade ou de país.",
    ]
