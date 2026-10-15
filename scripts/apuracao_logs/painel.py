"""Componentes visuais: números publicados, sem recalcular regras ou escores."""

from __future__ import annotations

from html import escape
from math import ceil

GRUPOS = {
    "tempo": (
        "Tempo e intervalos",
        "Processo do mesário ao cômputo, cadência e pausas.",
    ),
    "biometria": (
        "Identificação e biometria",
        "Taxas comparadas com seções da mesma zona e modelo.",
    ),
    "operacao": (
        "Funcionamento da urna",
        "Suspensão, reinício, energia e erros registrados.",
    ),
    "conferencia": (
        "Conferência dos arquivos",
        "Assinatura, relógio, contagens e fragmentos do pacote.",
    ),
}


def inteiro(v):
    return f"{v:,}".replace(",", ".")


def numero(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def grupo(regra):
    g = regra["grupo"]
    return "conferencia" if g in ("qualidade", "integridade") else g


def mapa_link(k="", texto="Ver seções no mapa"):
    url = "fiscais_mapa.html#ambito=todos&camada=logs"
    if k:
        url += "&log=" + k
    return f'<a href="{escape(url)}">{texto} →</a>'


def teto_percentual(d):
    taxas = [
        100 * r["secoes"] / r["avaliaveis"]
        for r in d["criterios"].values()
        if r["avaliaveis"]
    ]
    return max(5, 5 * ceil(max(taxas, default=0) / 5))


def catalogo(d, compacto=False):
    """Barra = parcela das avaliáveis; escala linear comum, sem piso visual."""
    partes = []
    teto = teto_percentual(d)
    for g, (titulo, descricao) in GRUPOS.items():
        regras = [(k, r) for k, r in d["criterios"].items() if grupo(r) == g]
        itens = []
        for k, r in regras:
            n, den = r["secoes"], r["avaliaveis"]
            taxa = 100 * n / den if den else None
            taxa_txt = (
                numero(taxa, 4 if 0 < taxa < 0.001 else 3 if 0 < taxa < 0.1 else 2)
                + "%"
                if taxa is not None
                else "não avaliável"
            )
            corpo = (
                f'<p><b>Regra:</b> {escape(r["regra"])}</p>'
                f'<p><b>O que conferir:</b> {escape(r["conferir"])}</p>'
                f'<p class="limite">{escape(r["limite"])}</p>'
            )
            itens.append(
                f'<article class="regra" id="{("fiscal-log-" if compacto else "") + k}" data-grupo="{g}">'
                f'<div class="regra-topo"><h4>{escape(r["nome"])}</h4>'
                f'<b class="contagem">{inteiro(n)}<small> seções</small></b></div>'
                f'<div class="barra-regra" aria-hidden="true"><i style="width:{100*(taxa or 0)/teto:.6f}%"></i></div>'
                f'<div class="regra-base"><span>{taxa_txt} de {inteiro(den)} avaliáveis</span>'
                f'{mapa_link(k, "Mapa")}</div>'
                f"<details><summary>Regra e conferência</summary>{corpo}</details></article>"
            )
        partes.append(
            f'<div class="grupo-regras" data-grupo="{g}"><h3>{titulo} <span>{len(regras)}</span></h3>'
            f'<p class="grupo-descricao">{descricao}</p><div class="eixo-regras" aria-hidden="true"><span>0%</span><span>{teto}% das avaliáveis</span></div>{"".join(itens)}</div>'
        )
    return '<div class="catalogo-regras">' + "".join(partes) + "</div>"


def navegacao_criterios(d):
    botoes = f'<button type="button" data-grupo="todos" aria-pressed="true">Todos · {len(d["criterios"])}</button>'
    for g, (nome, _) in GRUPOS.items():
        n = sum(grupo(r) == g for r in d["criterios"].values())
        botoes += f'<button type="button" data-grupo="{g}" aria-pressed="false">{nome} · {n}</button>'
    return (
        f'<div class="filtros-criterios" hidden><div role="group" aria-label="Grupo de diagnóstico">{botoes}</div>'
        '<label for="busca-criterio">Buscar diagnóstico</label>'
        '<input id="busca-criterio" type="search" placeholder="Ex.: reinício, biometria, relógio">'
        f'<p id="resultado-criterios" role="status">{len(d["criterios"])} diagnósticos</p></div>'
    )


def tempos(d, chave="tempos"):
    valores = d.get(chave, {})
    if not valores:
        return "<p>Sem base elegível para esta medida.</p>"
    html = []
    teto = max(max(r["p90_s"], r["media_s"]) for r in valores.values()) * 1.2
    for pais, r in valores.items():
        marcadores = "".join(
            f'<span class="ponto {k}" style="left:{100*r[k]/teto:.3f}%" '
            f'title="{nome}: {numero(r[k])} segundos"></span>'
            for k, nome in (
                ("mediana_s", "Mediana"),
                ("media_s", "Média"),
                ("p90_s", "Percentil 90"),
            )
        )
        html.append(
            f'<article class="tempo {pais}"><h3>{"Brasil" if pais == "brasil" else "Exterior"}</h3>'
            f'<p class="grande">{numero(r["media_s"])}<span> segundos em média</span></p>'
            f'<div class="regua-tempo" aria-hidden="true">{marcadores}<small>0 s</small>'
            f"<small>{numero(teto, 0)} s</small></div>"
            f'<dl class="quantis"><div><dt>Metade durou até</dt><dd>{numero(r["mediana_s"], 0)} s</dd></div>'
            f'<div><dt>90% duraram até</dt><dd>{numero(r["p90_s"], 0)} s</dd></div></dl>'
            f'<p class="base">{inteiro(r["ciclos"])} {"intervalos elegíveis" if chave == "cadencia" else "processos elegíveis" if chave == "processo" else "ciclos completos elegíveis"}.</p></article>'
        )
    return '<div class="tempos">' + "".join(html) + "</div>"


def biometria(d):
    partes = []
    categorias = (
        ("biometricas", "Reconhecimento biométrico"),
        ("biograficas", "Habilitação biográfica"),
        ("sem_biometria", "Sem biometria"),
    )
    for pais, r in d["biometria"].items():
        den = r["comparecimento"]
        segmentos, legendas = [], []
        for k, nome in categorias:
            pct = 100 * r[k] / den
            segmentos.append(
                f'<span class="bio-{k}" style="width:{pct:.6f}%" title="{nome}: {numero(pct)}%"></span>'
            )
            legendas.append(
                f'<div><i class="bio-{k}" aria-hidden="true"></i><h3>{nome}</h3>'
                f"<b>{numero(pct)}%</b><span>{inteiro(r[k])} habilitações</span></div>"
            )
        partes.append(
            f'<figure class="fig-bio"><figcaption>Como foram habilitados os {inteiro(den)} presentes '
            f'no conjunto reconciliado · {"Brasil" if pais == "brasil" else "Exterior"}</figcaption>'
            f'<div class="barra-bio" aria-hidden="true">{"".join(segmentos)}</div>'
            f'<div class="legenda-bio">{"".join(legendas)}</div></figure>'
        )
    return "".join(partes)


def cobertura(d):
    c = d["cobertura"]
    linhas = []
    for key, label in (
        ("lidos", "Log lido e ligado ao BU"),
        ("contagem_confere", "Comparecimento reconciliado"),
        ("biometria_confere", "Categorias de identificação reconciliadas"),
        ("tempo_elegivel", "Etapa de votação elegível"),
        ("processo_elegivel", "Processo com início e cobertura suficientes"),
        ("cadencia_elegivel", "Cadência com intervalos suficientes"),
    ):
        pct = 100 * c[key] / c["catalogadas"]
        linhas.append(
            f'<div class="cobertura-linha"><div><span>{label}</span><b>{inteiro(c[key])}</b></div>'
            f'<div class="trilho"><i style="width:{pct:.6f}%"></i></div>'
            f'<small>{numero(pct, 3)}% das {inteiro(c["catalogadas"])} catalogadas</small></div>'
        )
    return (
        '<figure class="fig-cobertura"><figcaption>Quanto da base sustenta cada leitura</figcaption>'
        + "".join(linhas)
        + "</figure>"
    )


def assinatura(d):
    op = d["operacao"]
    total = op.get("falhas_assinatura_declaradas", 0)
    categorias = (
        (
            "falhas_assinatura_com_sucesso_posterior",
            "Com SUCESSO posterior",
            "recuperado",
        ),
        (
            "falhas_assinatura_sem_sucesso_localizado",
            "Sem sucesso posterior localizado",
            "pendente",
        ),
        ("falhas_assinatura_ordem_incerta", "Ordem temporal incerta", "incerto"),
    )
    linhas = []
    for key, label, classe in categorias:
        n = op.get(key, 0)
        if not n:
            continue
        linhas.append(
            f'<div class="assinatura-linha {classe}"><span>{label}</span><b>{inteiro(n)}</b>'
            f'<div class="trilho"><i style="width:{100*n/total if total else 0:.3f}%"></i></div></div>'
        )
    return (
        '<figure class="fig-assinatura"><figcaption>O que veio depois dos '
        + inteiro(total)
        + " eventos de falha de assinatura</figcaption>"
        + "".join(linhas)
        + "</figure>"
    )
