"""Charts da página de reponderação, compartilhado pelo gerador."""

from __future__ import annotations

import math
from datetime import date
from html import escape as esc

from reponderacao_vista.context import (
    AGG,
    BLUE,
    BLUE_TXT,
    CEN,
    COR,
    COR_TXT,
    GOLD,
    GREEN,
    INK,
    INSTITUTOS,
    LINE,
    MESES,
    MUTED,
    PANEL,
    PAR,
    PESQUISAS,
    RED,
    RED_TXT,
    TURNOS,
    ajustado,
    curto,
    dia,
    forma,
    groups_view,
    rotulo,
    sinal,
)
from reponderacao_vista.markers import (
    abre_alvo,
    alvo_onda,
    area_alvo,
    fecha_alvo,
    halo,
    marcador,
    registra_tip,
)
from svgkit import FULL, MONO, Canvas, br


def meses_no_intervalo(d0: date, d1: date) -> list[date]:
    ano, mes, saida = d0.year, d0.month, []
    while True:
        atual = date(ano, mes, 1)
        if atual > d1:
            return saida
        if atual >= d0:
            saida.append(atual)
        mes += 1
        if mes > 12:
            mes, ano = 1, ano + 1


def caminho(pontos: list[tuple[float, float]]) -> str:
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pontos)


def serie_svg(ident: str, turno: str, compacta: bool = False) -> str:
    serie = AGG["serie"]
    datas = [dia(t) for t in serie["datas"]]
    pub, adj = serie[turno]["publicado"], serie[turno]["ajustado"]
    polls = [p for p in PESQUISAS if turno in p["turnos"]]

    chaves = (*PAR, *groups_view.GROUP_LABELS) if turno == "1t" else PAR
    valores: list[float] = []
    for fonte in (pub, adj):
        for chave in chaves:
            valores += [v for v in fonte[chave] if v is not None]
    for p in polls:
        t = p["turnos"][turno]
        for chave in PAR:
            valores.append(t["publicado"][chave])
            valores.append(ajustado(t)[chave])
    lo = math.floor((min(valores) - 2.0) / 5) * 5
    if turno == "1t":
        lo = 0
    hi = math.ceil((max(valores) + 2.0) / 5) * 5

    legendas = 1 if compacta else (2 if len(INSTITUTOS) > 1 else 1)
    altura = 360 if compacta else 400 + 30 * legendas
    if turno == "1t":
        altura = 660
    largura = FULL
    esq, dir_ = 54, largura - (168 if compacta else 190)
    if turno == "1t":
        dir_ = largura - 225
    topo, base = (
        (30 if compacta else 44),
        altura - (46 if compacta else 46 + 30 * legendas),
    )

    d0, d1 = datas[0], datas[-1]
    vao = max((d1 - d0).days, 1)
    folga = max(round(vao * 0.035), 3)

    def px(d: date) -> float:
        return esq + (dir_ - esq) * ((d - d0).days + folga) / (vao + folga * 2)

    def py(v: float) -> float:
        return base - (base - topo) * (v - lo) / (hi - lo)

    cv = Canvas(
        largura,
        altura,
        aria=(
            f"Série do {TURNOS[turno]}: intenção de voto publicada e reponderada "
            "pela distribuição de renda da PNAD."
        ),
    )
    cv.rect(0, 0, largura, altura, PANEL)

    passo = 5 if hi - lo <= 40 else 10
    grade = lo
    while grade <= hi:
        cv.line(esq, py(grade), dir_, py(grade), stroke=LINE, width=1)
        cv.label(esq - 10, py(grade) + 4, f"{grade}%", anchor="end", size=12)
        grade += passo
    cv.line(esq, base, dir_, base, stroke=INK, width=1.4)

    for m in meses_no_intervalo(d0, d1):
        x = px(m)
        cv.line(x, base, x, base + 6, stroke=INK, width=1)
        cv.label(
            x,
            base + 22,
            f"{MESES[m.month - 1]}/{str(m.year)[2:]}",
            anchor="middle",
            size=12,
        )

    for chave in chaves:
        cv.add(
            f'<g data-serie="{chave}"><title>{esc(rotulo(chave))}: média publicada e reponderada</title>'
        )
        for nome, dados in (("publicado", pub), ("ajustado", adj)):
            trecho: list[tuple[float, float]] = []
            for d, v in zip(datas, dados[chave], strict=True):
                if v is None:
                    if len(trecho) > 1:
                        _linha(cv, trecho, COR[chave], nome)
                    trecho = []
                    continue
                trecho.append((px(d), py(v)))
            if len(trecho) > 1:
                _linha(cv, trecho, COR[chave], nome)

        cv.add("</g>")

    raio = 4.6 if compacta else (5.8 if len(polls) <= 8 else 4.4)
    alcance = max(raio * 2.0, 9.0)
    for p in polls:
        t = p["turnos"][turno]
        x = px(dia(p["campo"]["fim"]))
        shape = forma(p["instituto"])
        alvo_onda(cv, p, turno)
        cv.line(x, topo, x, base, stroke=INK, width=1, **{"class": "hit-cross"})
        for chave in PAR:
            y_pub, y_adj = py(t["publicado"][chave]), py(ajustado(t)[chave])
            cv.line(
                x, y_pub, x, y_adj, stroke=COR[chave], width=1.3, stroke_dasharray="2 3"
            )
            halo(cv, x, y_pub, raio + 4.5, COR[chave])
            halo(cv, x, y_adj, raio + 4.5, COR[chave])
            marcador(cv, shape, x, y_pub, raio, COR[chave], False)
            marcador(cv, shape, x, y_adj, raio, COR[chave], True)
            area_alvo(cv, x, y_pub, alcance)
            area_alvo(cv, x, y_adj, alcance)
        fecha_alvo(cv)

    if turno == "1t":
        groups_view.end_labels(cv, pub, adj, dir_, topo, base, py, COR_TXT, br)
    else:
        _bloco_direita(cv, turno, pub, adj, dir_, topo, base, py, compacta)

    if not compacta:
        _legenda(cv, esq, base + 52, largura)
        if legendas > 1:
            _legenda_institutos(cv, esq, base + 82, {p["instituto"] for p in polls})
    return cv.render()


def _linha(cv: Canvas, pontos: list[tuple[float, float]], cor: str, tipo: str) -> None:
    if tipo == "publicado":
        cv.path(
            caminho(pontos),
            fill="none",
            stroke=cor,
            stroke_width=1.7,
            stroke_dasharray="7 5",
            opacity="0.7",
        )
    else:
        cv.path(
            caminho(pontos),
            fill="none",
            stroke=cor,
            stroke_width=3.6,
            stroke_linejoin="round",
            stroke_linecap="round",
        )


def _ultimo(dados: list) -> float | None:
    for v in reversed(dados):
        if v is not None:
            return v
    return None


def _bloco_direita(cv, turno, pub, adj, dir_, topo, base, py, compacta) -> None:
    """Rótulos de fim de linha: o número que o leitor leva sem ler o resto."""
    alto = 66
    blocos = []
    for chave in PAR:
        fim_adj, fim_pub = _ultimo(adj[chave]), _ultimo(pub[chave])
        if fim_adj is None:
            continue
        blocos.append((py(fim_adj), chave, fim_adj, fim_pub))
    blocos.sort()
    livre = topo
    postos = []
    for centro, chave, val_adj, val_pub in blocos:
        y = max(centro - alto / 2, livre)
        y = min(y, base - alto)
        livre = y + alto + 10
        postos.append((y, centro, chave, val_adj, val_pub))
    for y, centro, chave, val_adj, val_pub in postos:
        x = dir_ + 16
        cv.line(dir_, centro, x - 6, y + alto / 2, stroke=COR[chave], width=1.2)
        cv.text(
            x,
            y + 12,
            rotulo(chave).upper(),
            size=11,
            fill=COR_TXT[chave],
            weight=700,
            letter_spacing="0.09em",
        )
        cv.number(
            x,
            y + 43,
            br(val_adj, 1) + "%",
            size=30 if not compacta else 27,
            fill=COR_TXT[chave],
        )
        if val_pub is not None:
            cv.text(
                x,
                y + 59,
                f"publicado {br(val_pub, 1)}%",
                size=11.5,
                fill=MUTED,
                family=MONO,
            )


def _legenda(cv: Canvas, x0: float, y: float, largura: float) -> None:
    itens = [
        ("marcador_vazado", "ponto publicado pelo instituto", "FATO"),
        ("marcador_cheio", "ponto reponderado pela PNAD", "INFERÊNCIA"),
        ("linha_tracejada", "média Arvor publicada", "FATO"),
        ("linha_solida", "média Arvor reponderada", "INFERÊNCIA"),
    ]
    x = x0
    for tipo, texto, marca in itens:
        if tipo == "marcador_vazado":
            marcador(cv, "circulo", x + 8, y, 5.6, INK, False)
        elif tipo == "marcador_cheio":
            marcador(cv, "circulo", x + 8, y, 5.6, INK, True)
        elif tipo == "linha_tracejada":
            cv.line(x, y, x + 26, y, stroke=INK, width=1.7, stroke_dasharray="7 5")
        else:
            cv.line(x, y, x + 26, y, stroke=INK, width=3.6, stroke_linecap="round")
        cv.text(x + 34, y + 4, texto, size=12.5, fill=INK)
        largura_texto = 34 + len(texto) * 6.6
        cv.text(
            x + largura_texto + 8,
            y + 4,
            marca,
            size=10.5,
            fill=GOLD if marca == "INFERÊNCIA" else GREEN,
            weight=700,
            letter_spacing="0.08em",
        )
        x += largura_texto + 8 + len(marca) * 7.4 + 26
        if x > largura - 200:
            x, y = x0, y + 26


def _legenda_institutos(cv: Canvas, x0: float, y: float, presentes: set[str]) -> None:
    x = x0
    for nome in INSTITUTOS:
        if nome not in presentes:
            continue
        marcador(cv, forma(nome), x + 7, y, 5.6, INK, True)
        cv.text(x + 20, y + 4, nome, size=12.5, fill=INK)
        x += 20 + len(nome) * 7.2 + 26


def gap_svg(ident: str, turno: str) -> str:
    polls = [p for p in PESQUISAS if turno in p["turnos"]]
    apertado = len(polls) > 14
    linha_alt = 48 if apertado else 66
    altura = 96 + linha_alt * len(polls) + 46
    largura = FULL
    esq = 300
    dir_ = largura - 44
    meio = (esq + dir_) / 2

    limite = 2.0
    for p in polls:
        t = p["turnos"][turno]
        limite = max(
            limite,
            abs(t["gap_publicado"]) + t["margem_diferenca_95"],
            abs(t["gap_ajustado"]),
        )
    limite = math.ceil(limite / 2) * 2

    def px(v: float) -> float:
        return meio + (dir_ - meio) * v / limite

    cv = Canvas(
        largura,
        altura,
        aria=(
            f"Diferença Lula menos Flávio no {TURNOS[turno]}, publicada e "
            "reponderada, com a margem de 95% da diferença."
        ),
    )
    cv.rect(0, 0, largura, altura, PANEL)
    hatch_red = cv.hatch(f"{ident}-hr", RED, 0.3)
    hatch_blue = cv.hatch(f"{ident}-hb", BLUE, 0.3)

    cv.text(
        meio - 18,
        26,
        "◀ Flávio à frente",
        size=12.5,
        fill=BLUE_TXT,
        weight=700,
        anchor="end",
    )
    cv.text(meio + 18, 26, "Lula à frente ▶", size=12.5, fill=RED_TXT, weight=700)
    for marca in range(-limite, limite + 1, 2):
        x = px(marca)
        cv.line(x, 40, x, altura - 46, stroke=LINE, width=1)
        cv.label(x, altura - 28, br(abs(marca), 0), anchor="middle", size=11.5)
    cv.line(meio, 40, meio, altura - 46, stroke=INK, width=1.6)
    cv.label(
        meio, altura - 12, "diferença em pontos percentuais", anchor="middle", size=11.5
    )

    y = 52
    for p in polls:
        t = p["turnos"][turno]
        alvo_onda(cv, p, turno)
        cv.rect(20, y, dir_ - 20, linha_alt, "transparent", **{"class": "hit-area"})
        cv.rect(
            20,
            y,
            dir_ - 20,
            linha_alt,
            "none",
            stroke=INK,
            stroke_width=1.5,
            **{"class": "hit-halo"},
        )
        cv.line(20, y, dir_, y, stroke=LINE, width=1)
        cv.text(
            20,
            y + (18 if apertado else 22),
            p["instituto"],
            size=13 if apertado else 14.5,
            fill=INK,
            weight=700,
        )
        campo = f"campo até {curto(p['campo']['fim'])}/{dia(p['campo']['fim']).year}"
        if apertado:
            cv.text(
                20,
                y + 34,
                f"{curto(p['campo']['fim'])} · n = {br(p['n'], 0)}",
                size=10.5,
                fill=MUTED,
                family=MONO,
            )
        else:
            cv.text(20, y + 39, campo, size=11, fill=MUTED, family=MONO)
            cv.text(
                20,
                y + 54,
                f"n = {br(p['n'], 0)} · {p['registro_tse']}",
                size=11,
                fill=MUTED,
                family=MONO,
            )

        barra = 11 if apertado else 13
        for nome, valor, altura_barra, deslocamento in (
            ("publicado", t["gap_publicado"], barra, 6 if apertado else 9),
            ("reponderado", t["gap_ajustado"], barra, 25 if apertado else 33),
        ):
            cor = RED if valor >= 0 else BLUE
            fill = (
                cor
                if nome == "publicado"
                else (hatch_red if valor >= 0 else hatch_blue)
            )
            x0, x1 = sorted((px(0), px(valor)))
            cv.rect(
                x0,
                y + deslocamento,
                x1 - x0,
                altura_barra,
                fill,
                stroke=cor,
                stroke_width=1,
            )
            cv.text(
                esq - 14,
                y + deslocamento + altura_barra - 2,
                nome,
                size=10.5 if apertado else 11,
                fill=MUTED,
                anchor="end",
                family=MONO,
            )
            fim = px(valor)
            ancora = "start" if valor >= 0 else "end"
            cv.text(
                fim + (8 if valor >= 0 else -8),
                y + deslocamento + altura_barra - 2,
                sinal(valor, 1),
                size=12 if apertado else 13,
                fill=RED_TXT if valor >= 0 else BLUE_TXT,
                weight=700,
                anchor=ancora,
                family=MONO,
            )

        margem = t["margem_diferenca_95"]
        ym = y + (6 if apertado else 9) + barra / 2
        a, b = px(t["gap_publicado"] - margem), px(t["gap_publicado"] + margem)
        cv.line(a, ym, b, ym, stroke=INK, width=1.4)
        cv.line(a, ym - 6, a, ym + 6, stroke=INK, width=1.4)
        cv.line(b, ym - 6, b, ym + 6, stroke=INK, width=1.4)
        fecha_alvo(cv)
        y += linha_alt

    cv.line(20, y, dir_, y, stroke=LINE, width=1)
    return cv.render()


def instituto_svg(nome: str, turno: str, historico: list[dict] | None = None) -> str:
    polls = (
        historico
        if historico is not None
        else [p for p in PESQUISAS if p["instituto"] == nome and turno in p["turnos"]]
    )
    largura, altura = 380, 284 if historico is not None else 258
    esq, dir_, topo, base = 44, largura - 16, 30, altura - (76 if historico is not None else 54)
    cv = Canvas(
        largura, altura, aria=f"{nome}: {TURNOS[turno]} publicado e reponderado."
    )
    cv.rect(0, 0, largura, altura, PANEL)
    if not polls:
        cv.text(esq, topo + 40, "sem onda com esse turno", size=13, fill=MUTED)
        return cv.render()

    valores: list[float] = []
    for p in polls:
        t = p["turnos"][turno]
        for chave in PAR:
            valores += [t["publicado"][chave], ajustado(t)[chave]]
    lo = math.floor((min(valores) - 2) / 5) * 5
    hi = math.ceil((max(valores) + 2) / 5) * 5

    def py(v: float) -> float:
        return base - (base - topo) * (v - lo) / (hi - lo)

    def px(i: int) -> float:
        if len(polls) == 1:
            return (esq + dir_) / 2
        return esq + (dir_ - esq - 24) * i / (len(polls) - 1) + 12

    marca = lo
    while marca <= hi:
        cv.line(esq, py(marca), dir_, py(marca), stroke=LINE, width=1)
        cv.label(esq - 8, py(marca) + 4, f"{marca}", anchor="end", size=11)
        marca += 5
    cv.line(esq, base, dir_, base, stroke=INK, width=1.2)

    shape = forma(nome)
    for chave in PAR:
        pub = [
            (px(i), py(p["turnos"][turno]["publicado"][chave]))
            for i, p in enumerate(polls)
        ]
        adj = [
            (px(i), py(ajustado(p["turnos"][turno])[chave]))
            for i, p in enumerate(polls)
        ]
        if len(polls) > 1:
            _linha(cv, pub, COR[chave], "publicado")
            _linha(cv, adj, COR[chave], "ajustado")
        for indice, (ponto_pub, ponto_adj) in enumerate(zip(pub, adj, strict=True)):
            x, y_pub = ponto_pub
            y_adj = ponto_adj[1]
            alvo_onda(cv, polls[indice], turno)
            cv.line(
                x, y_pub, x, y_adj, stroke=COR[chave], width=1.2, stroke_dasharray="2 3"
            )
            halo(cv, x, y_pub, 9.0, COR[chave])
            halo(cv, x, y_adj, 9.0, COR[chave])
            marcador(cv, shape, x, y_pub, 4.6, COR[chave], False)
            marcador(cv, shape, x, y_adj, 4.6, COR[chave], True)
            area_alvo(cv, x, y_pub, 10.0)
            area_alvo(cv, x, y_adj, 10.0)
            fecha_alvo(cv)

    passo = max(1, math.ceil(len(polls) / 6))
    for i, p in enumerate(polls):
        if (len(polls) - 1 - i) % passo:
            continue
        cv.label(
            px(i),
            base + 20,
            p.get("rotulo_eixo", curto(p["campo"]["fim"])),
            anchor="middle",
            size=10 if historico is not None else 11,
        )
        if historico is not None:
            status = "substituída" if p.get("substituida") else ""
            if turno == "1t" and p.get("primeiro_turno_com_marcal"):
                status = "com Marçal"
            cv.label(px(i), base + 33, status, anchor="middle", size=9)
    ultimo = polls[-1]["turnos"][turno]
    cv.text(
        esq,
        altura - 12,
        f"{sinal(ultimo['gap_publicado'], 1)} publicado · {sinal(ultimo['gap_ajustado'], 1)} reponderado",
        size=12,
        fill=MUTED,
        family=MONO,
    )
    return cv.render()


def ficha_faixa(pesquisa: dict, indice: int) -> str:
    """Ficha de uma faixa de renda: o que o instituto tinha e o que a PNAD mede."""
    renda = pesquisa["renda"]
    perfil = (
        "cota registrada"
        if renda.get("perfil_tipo") == "cota_registrada"
        else (
            "meta de calibração"
            if renda.get("perfil_tipo") == "alvo_de_calibracao"
            else "amostra"
        )
    )
    faixa = renda["faixas"][indice]
    amostra = renda["amostra_pct"][indice]
    corte = renda["cortes_brl_202604"][indice]
    piso = renda["cortes_brl_202604"][indice - 1] if indice else 0.0
    linhas = [
        f'<p class="tip-head"><b>{esc(faixa)}</b>'
        f"<span>{esc(pesquisa['instituto'])}</span></p>"
    ]
    if corte is None:
        regua = f"acima de R$ {br(piso, 0)}"
    elif indice == 0:
        regua = f"até R$ {br(corte, 0)}"
    else:
        regua = f"de R$ {br(piso, 0)} a R$ {br(corte, 0)}"
    linhas.append(
        f'<p class="tip-doc">na régua da PNAD, {esc(regua)} a preços de abr. de 2026</p>'
    )
    linhas.append(
        '<table class="tip-tab"><thead><tr><th></th><th>fatia</th></tr></thead><tbody>'
    )
    for nome, valor, cls in (
        (perfil, amostra, "pub"),
        ("PNAD 16+", renda["pnad_pct"][CEN][indice], "adj"),
    ):
        linhas.append(
            f'<tr class="{cls}"><th scope="row">{nome}</th>'
            f"<td>{br(valor, 1)}%</td></tr>"
        )
    delta = amostra - renda["pnad_pct"][CEN][indice]
    linhas.append("</tbody></table>")
    lado = "acima" if delta >= 0 else "abaixo"
    linhas.append(
        f'<p class="tip-nota">A {perfil} está {br(abs(delta), 1)} pontos {lado} da '
        "régua oficial nesta faixa. A reponderação corrige exatamente isso, "
        "mantendo o voto medido dentro dela.</p>"
    )
    return "".join(linhas)


def renda_svg(pesquisa: dict) -> str:
    renda = pesquisa["renda"]
    perfil = (
        "cota registrada"
        if renda.get("perfil_tipo") == "cota_registrada"
        else (
            "meta de calibração"
            if renda.get("perfil_tipo") == "alvo_de_calibracao"
            else "amostra"
        )
    )
    faixas = renda["faixas"]
    amostra = renda["amostra_pct"]
    alvo = renda["pnad_pct"][CEN]
    largura = 566
    alto_grupo = 78
    altura = 66 + alto_grupo * len(faixas) + 34
    esq, dir_ = 210, largura - 78
    maximo = max(max(amostra), max(alvo), 10) * 1.06

    cv = Canvas(
        largura,
        altura,
        aria=f"Composição de renda: {perfil} do instituto contra a PNAD.",
    )
    cv.rect(0, 0, largura, altura, PANEL)
    cv.text(
        16,
        24,
        {
            "cota registrada": "COTA REGISTRADA",
            "meta de calibração": "META DE CALIBRAÇÃO",
        }.get(perfil, "AMOSTRA DO INSTITUTO"),
        size=10.5,
        fill=INK,
        weight=700,
        letter_spacing="0.08em",
    )
    cv.text(
        16,
        40,
        "PNAD PESSOAS 16+",
        size=10.5,
        fill=GREEN,
        weight=700,
        letter_spacing="0.08em",
    )

    y = 58
    for i, faixa in enumerate(faixas):
        chave = registra_tip(f"{pesquisa['id']}|renda|{i}", ficha_faixa(pesquisa, i))
        abre_alvo(
            cv,
            chave,
            f"{faixa}: {perfil} {br(amostra[i], 1)}%, PNAD {br(alvo[i], 1)}%.",
        )
        cv.rect(
            8, y, largura - 16, alto_grupo - 6, "transparent", **{"class": "hit-area"}
        )
        cv.rect(
            8,
            y,
            largura - 16,
            alto_grupo - 6,
            "none",
            stroke=GOLD,
            stroke_width=1.5,
            **{"class": "hit-halo"},
        )
        cv.text(16, y + 16, faixa, size=12.5, fill=INK)
        for nome, valor, cor, deslocamento in (
            ("amostra", amostra[i], INK, 26),
            ("pnad", alvo[i], GREEN, 48),
        ):
            comprimento = (dir_ - esq) * valor / maximo
            cv.rect(esq, y + deslocamento, comprimento, 16, cor)
            cv.text(
                esq + comprimento + 8,
                y + deslocamento + 13,
                br(valor, 1) + "%",
                size=12.5,
                fill=INK if nome == "amostra" else GREEN,
                weight=700,
                family=MONO,
            )
        delta = amostra[i] - alvo[i]
        cv.text(
            esq - 12,
            y + 39,
            sinal(delta, 1),
            size=13,
            fill=GOLD,
            weight=700,
            anchor="end",
            family=MONO,
        )
        fecha_alvo(cv)
        y += alto_grupo
    cv.label(16, altura - 12, f"diferença em pontos, {perfil} menos PNAD", size=11.5)
    return cv.render()


def _afasta(alturas: dict[str, float], minimo: float) -> dict[str, float]:
    """Separa rótulos que caem quase na mesma linha, sem mover os pontos."""
    ordem = sorted(alturas.items(), key=lambda item: item[1])
    saida: dict[str, float] = {}
    anterior = None
    for chave, y in ordem:
        if anterior is not None and y - anterior < minimo:
            y = anterior + minimo
        saida[chave] = y
        anterior = y
    return saida


def slope_svg(pesquisa: dict) -> str:
    turnos = [t for t in ("2t", "1t") if t in pesquisa["turnos"]]
    largura = 566
    alto = 236
    altura = 26 + alto * len(turnos)
    cv = Canvas(
        largura, altura, aria="Placar publicado e placar reponderado pela renda."
    )
    cv.rect(0, 0, largura, altura, PANEL)

    for indice, turno in enumerate(turnos):
        t = pesquisa["turnos"][turno]
        base_y = 26 + alto * indice
        topo, chao = base_y + 44, base_y + 176
        x0, x1 = 176, largura - 176
        valores = [t["publicado"][c] for c in PAR] + [ajustado(t)[c] for c in PAR]
        lo = math.floor((min(valores) - 3) / 5) * 5
        hi = math.ceil((max(valores) + 3) / 5) * 5

        def py(v: float, topo=topo, chao=chao, lo=lo, hi=hi) -> float:
            return chao - (chao - topo) * (v - lo) / (hi - lo)

        cv.text(
            16,
            base_y + 16,
            TURNOS[turno].upper(),
            size=10.5,
            fill=INK,
            weight=700,
            letter_spacing="0.1em",
        )
        cv.line(x0, topo - 14, x0, chao + 14, stroke=LINE, width=1)
        cv.line(x1, topo - 14, x1, chao + 14, stroke=LINE, width=1)
        cv.label(x0, chao + 32, "publicado", anchor="middle", size=11.5)
        cv.label(x1, chao + 32, "reponderado", anchor="middle", size=11.5)

        rotulo_y = {
            lado: _afasta({c: py(fonte(t)[c]) for c in PAR}, 17)
            for lado, fonte in (
                ("pub", lambda t: t["publicado"]),
                ("adj", ajustado),
            )
        }
        for chave in PAR:
            a, b = t["publicado"][chave], ajustado(t)[chave]
            ya, yb = py(a), py(b)
            cv.line(
                x0, ya, x1, yb, stroke=COR[chave], width=3.4, stroke_linecap="round"
            )
            marcador(cv, "circulo", x0, ya, 6, COR[chave], False)
            marcador(cv, "circulo", x1, yb, 6, COR[chave], True)
            cv.text(
                x0 - 14,
                rotulo_y["pub"][chave] + 5,
                f"{rotulo(chave)} {br(a, 1)}",
                size=13.5,
                fill=COR_TXT[chave],
                weight=700,
                anchor="end",
            )
            cv.text(
                x1 + 14,
                rotulo_y["adj"][chave] + 5,
                f"{br(b, 1)} {rotulo(chave)}",
                size=13.5,
                fill=COR_TXT[chave],
                weight=700,
            )
        cv.text(
            (x0 + x1) / 2,
            base_y + 32,
            f"diferença {sinal(t['gap_publicado'], 1)} para {sinal(t['gap_ajustado'], 1)}",
            size=12.5,
            fill=MUTED,
            anchor="middle",
            family=MONO,
        )
    return cv.render()
