"""Figuras SVG do capítulo Sudeste do dossiê de 21/09/2026.

Tudo é desenhado em Python e os dados vão embutidos no HTML gerado. Nenhuma
figura depende de rede ou de JavaScript: o script só acrescenta a leitura da
fita ao passar o ponteiro. Abrir o arquivo do disco continua mostrando todos
os gráficos.
"""

from html import escape

INK = "#18231d"
PAPER = "#f7f1e5"
FAIXA = "#eee7d8"
MUTED = "#535b54"
RED = "#a52630"
BLUE = "#164d88"
TEAL = "#0c7a72"
# Texto pequeno sobre a faixa listrada da figura reprova em 4,22 com o verde de
# barra. O rótulo usa um tom mais escuro, medido em 5,03 sobre a faixa e 5,50
# sobre o papel, e a barra mantém a cor da casa.
TEAL_TXT = "#0a6d66"
GOLD = "#7d5b00"
UFS = ("SP", "RJ", "MG")
NAO_ESCOLHA = (
    "Em branco/nulo/nenhum",
    "Indecisos",
    "Não sabe",
    "Nulo/Branco",
    "NS/NR",
)
DEMAIS = "Demais candidaturas"
CORES_DESTINO = {
    "Lula (PT)": RED,
    "Flavio Bolsonaro (PL)": BLUE,
    "Em branco/nulo/nenhum": MUTED,
    "Não sabe": GOLD,
}
CURTO = {
    "Lula (PT)": "Lula",
    "Flavio Bolsonaro (PL)": "Flávio",
    "Em branco/nulo/nenhum": "Branco, nulo ou nenhum",
    "Não sabe": "Não sabe",
}


def fmt(valor, casas=1):
    return f"{valor:.{casas}f}".replace(".", ",")


def sinal(valor, casas=0):
    return ("+" if valor > 0 else "") + fmt(valor, casas)


def primeiro_nome(rotulo):
    return rotulo.split(" (")[0]


def milhar(valor):
    return f"{valor:,}".replace(",", ".")


def text(x, y, valor, size=15, color=INK, anchor="start", weight="400"):
    return (
        f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" '
        f'font-weight="{weight}" text-anchor="{anchor}" '
        f'font-family="Archivo, sans-serif">{escape(str(valor))}</text>'
    )


def svg(corpo, altura, rotulo, largura=1100):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {largura} {round(altura)}" '
        f'role="img" aria-label="{escape(rotulo)}">'
        f'<rect width="{largura}" height="{altura}" fill="{PAPER}"/>{corpo}</svg>'
    )


def chip(x, y, rotulo, largura=470):
    return f'<rect x="{x}" y="{y}" width="{largura}" height="26" fill="{INK}"/>' + text(
        x + 13, y + 18, rotulo, 12, PAPER, weight="700"
    )


def _linha_placar(uf, sub, nota, valores, y, escala=4.0):
    """Um estado: governo do estado contra Flávio, nos dois turnos."""
    corpo = text(30, y + 30, uf, 30, INK, weight="700")
    corpo += text(30, y + 52, sub, 12, MUTED)
    corpo += text(30, y + 70, nota, 12, MUTED)
    for coluna, x0 in ((0, 230), (1, 680)):
        gov, pres, vao = valores[coluna]
        for i, (valor, cor) in enumerate(((gov, TEAL), (pres, BLUE))):
            barra_y = y + 8 + i * 30
            corpo += (
                f'<rect x="{x0}" y="{barra_y}" width="{valor * escala}" '
                f'height="22" fill="{cor}"/>'
            )
            corpo += text(
                x0 + valor * escala + 9,
                barra_y + 17,
                f"{valor}%",
                15,
                TEAL_TXT if cor == TEAL else cor,
                weight="600",
            )
        fim = 650 if coluna == 0 else 1090
        corpo += text(fim, y + 25, f"vão {sinal(vao)}", 16, INK, "end", "700")
        corpo += text(fim, y + 45, "pontos", 12, MUTED, "end")
    return corpo


def _linha_placar_estreito(uf, sub, nota, valores, y, escala=5.4):
    """O mesmo estado com os dois turnos empilhados, para tela estreita.

    Na largura de trabalho as duas colunas cabem lado a lado. Abaixo de
    720px a coluna do 2o turno saía do quadro e exigia rolagem dentro da
    figura, escondendo justamente o número que carrega a tese. Aqui cada
    turno vira um bloco próprio, e nada fica fora da tela.
    """
    corpo = text(16, y + 26, uf, 26, INK, weight="700")
    corpo += text(66, y + 26, nota, 13, INK, weight="600")
    corpo += text(16, y + 46, sub, 11, MUTED)
    for coluna, rotulo in ((0, "PRIMEIRO TURNO"), (1, "SEGUNDO TURNO")):
        gov, pres, vao = valores[coluna]
        base = y + 74 + coluna * 68
        corpo += text(16, base, rotulo, 11, MUTED, weight="700")
        corpo += text(524, base, f"vão {sinal(vao)} pontos", 13, INK, "end", "700")
        for i, (valor, cor) in enumerate(((gov, TEAL), (pres, BLUE))):
            barra_y = base + 8 + i * 24
            corpo += (
                f'<rect x="16" y="{barra_y}" width="{valor * escala}" '
                f'height="18" fill="{cor}"/>'
            )
            corpo += text(
                16 + valor * escala + 8,
                barra_y + 14,
                f"{valor}%",
                13,
                TEAL_TXT if cor == TEAL else cor,
                weight="600",
            )
    return corpo


def placar_estreito(dados):
    """Variante empilhada do placar, exibida por CSS abaixo de 720px."""
    corpo = text(16, 26, "O vão em cada estado", 20, INK, weight="700")
    y = 44
    for uf in UFS:
        estado = dados["estados"][uf]
        vao = estado["vao"]
        corpo += _linha_placar_estreito(
            uf,
            f"Datafolha · n {milhar(estado['n'])}",
            f"{primeiro_nome(vao['turno2']['candidato_governador'])} × Flávio",
            [
                (
                    vao[chave]["governador_pct"],
                    vao[chave]["presidenciavel_pct"],
                    vao[chave]["vao_pp"],
                )
                for chave in ("turno1", "turno2")
            ],
            y,
        )
        y += 216
    corpo += (
        f'<line x1="16" y1="{y - 6}" x2="524" y2="{y - 6}" stroke="{INK}" '
        'stroke-width="2" stroke-dasharray="6 6"/>'
    )
    corpo += chip(16, y + 8, "OUTRO INSTITUTO. NÃO ENTRA EM MÉDIA.", 330)
    es = dados["espirito_santo"]
    corpo += _linha_placar_estreito(
        "ES",
        f"Real Time Big Data · n {milhar(es['n'])}",
        f"{primeiro_nome(es['vao']['turno2']['nome'])} × Flávio",
        [
            (
                es["vao"][chave]["governador"],
                es["vao"][chave]["flavio"],
                es["vao"][chave]["vao_pp"],
            )
            for chave in ("turno1_melhor_direita", "turno2")
        ],
        y + 42,
    )
    rodape = y + 290
    corpo += f'<rect x="16" y="{rodape - 12}" width="14" height="14" fill="{TEAL}"/>'
    corpo += text(38, rodape, "Direita ao governo do estado", 13, TEAL_TXT)
    corpo += f'<rect x="16" y="{rodape + 12}" width="14" height="14" fill="{BLUE}"/>'
    corpo += text(38, rodape + 24, "Flávio Bolsonaro, presidente", 13, BLUE)
    return svg(
        corpo,
        rodape + 46,
        "Vão por estado, versão empilhada para tela estreita: SP mais 14 e mais "
        "9, RJ menos 14 e menos 15, MG mais 2 e mais 14, ES menos 2 e mais 4 "
        "pontos",
        largura=540,
    )


def placar(dados):
    """Governador e presidente, mesmo campo, nos quatro estados do Sudeste."""
    corpo = text(30, 28, "O vão em cada estado", 24, INK, weight="700")
    corpo += text(230, 56, "PRIMEIRO TURNO", 13, MUTED, weight="700")
    corpo += text(680, 56, "SEGUNDO TURNO", 13, MUTED, weight="700")
    y = 72
    for uf in UFS:
        estado = dados["estados"][uf]
        vao = estado["vao"]
        corpo += _linha_placar(
            uf,
            f"Datafolha · n {milhar(estado['n'])}",
            f"{primeiro_nome(vao['turno2']['candidato_governador'])} × Flávio",
            [
                (
                    vao[chave]["governador_pct"],
                    vao[chave]["presidenciavel_pct"],
                    vao[chave]["vao_pp"],
                )
                for chave in ("turno1", "turno2")
            ],
            y,
        )
        y += 98
    corpo += (
        f'<line x1="30" y1="{y + 8}" x2="1070" y2="{y + 8}" stroke="{INK}" '
        'stroke-width="2" stroke-dasharray="6 6"/>'
    )
    corpo += chip(30, y + 22, "OUTRO INSTITUTO, OUTRO MÉTODO. NÃO ENTRA EM MÉDIA.")
    es = dados["espirito_santo"]
    corpo += _linha_placar(
        "ES",
        f"Real Time Big Data · n {milhar(es['n'])}",
        f"{primeiro_nome(es['vao']['turno2']['nome'])} × Flávio",
        [
            (
                es["vao"][chave]["governador"],
                es["vao"][chave]["flavio"],
                es["vao"][chave]["vao_pp"],
            )
            for chave in ("turno1_melhor_direita", "turno2")
        ],
        y + 56,
    )
    rodape = y + 180
    corpo += f'<rect x="230" y="{rodape - 13}" width="16" height="16" fill="{TEAL}"/>'
    corpo += text(
        254, rodape, "Candidatura de direita ao governo do estado", 14, TEAL_TXT
    )
    corpo += f'<rect x="680" y="{rodape - 13}" width="16" height="16" fill="{BLUE}"/>'
    corpo += text(704, rodape, "Flávio Bolsonaro, presidente", 14, BLUE)
    return svg(
        corpo,
        rodape + 26,
        "Vão por estado: SP mais 14 e mais 9, RJ menos 14 e menos 15, MG mais 2 "
        "e mais 14, ES menos 2 e mais 4 pontos",
    )


def ordena_origens(origem_pct, medidas, minimo=3.0):
    """Mantém as origens grandes e as publicadas; agrupa a cauda."""
    candidatas = [k for k in origem_pct if k not in NAO_ESCOLHA]
    manter = sorted(
        (k for k in candidatas if origem_pct[k] >= minimo or k in medidas),
        key=lambda k: -origem_pct[k],
    )
    resto = [k for k in candidatas if k not in manter]
    ordem = list(manter)
    if resto:
        ordem.append(DEMAIS)
    ordem += [k for k in origem_pct if k in NAO_ESCOLHA]
    return ordem, resto


def frechet(origem_pp, destino_pp):
    """Limites de Fréchet da célula, imunes à prior."""
    return max(0.0, origem_pp + destino_pp - 100.0), min(origem_pp, destino_pp)


def celulas_do_diagrama(bloco):
    """Linhas do diagrama já agrupadas, com faixa de Fréchet e natureza."""
    variante = bloco["variantes"]["ideologica"]
    medidas = set(variante["linhas_medidas"])
    origem_pct, destino_pct = variante["origem_pct"], variante["destino_pct"]
    publicadas = {(c["origem"], c["destino"]): c for c in variante["celulas"]}
    ordem, resto = ordena_origens(origem_pct, medidas)
    saida = []
    for nome in ordem:
        agrupada = nome == DEMAIS
        massa = sum(origem_pct[k] for k in resto) if agrupada else origem_pct[nome]
        for destino in destino_pct:
            valor = (
                sum(variante["matriz_pp"][k][destino] for k in resto)
                if agrupada
                else variante["matriz_pp"][nome][destino]
            )
            celula = publicadas.get((nome, destino))
            # A faixa auditada vem do JSON, que usa a massa não arredondada.
            # Só a origem agregada precisa de recálculo.
            baixo, alto = (
                frechet(massa, destino_pct[destino])
                if celula is None
                else (celula["frechet_min_pp"], celula["frechet_max_pp"])
            )
            medida = bool(celula) and celula["estado"] == "medida" and not agrupada
            saida.append(
                {
                    "origem": nome,
                    "destino": destino,
                    "massa_origem_pp": massa,
                    "massa_destino_pp": destino_pct[destino],
                    "valor_pp": valor,
                    "frechet_min_pp": baixo,
                    "frechet_max_pp": alto,
                    "medida": medida,
                }
            )
    return ordem, list(destino_pct), medidas, saida


def sankey(uf, bloco, titulo, subtitulo, escala=3.6):
    """Fluxo agregado do voto de governador para o 2º turno presidencial."""
    ordem, destinos, medidas, celulas = celulas_do_diagrama(bloco)
    massa = {c["origem"]: c["massa_origem_pp"] for c in celulas}
    destino_pct = {c["destino"]: c["massa_destino_pp"] for c in celulas}

    corpo = "<defs>"
    padroes = {}
    for i, (chave, cor) in enumerate(CORES_DESTINO.items()):
        padroes[chave] = f"hachura-{uf.lower()}-{i}"
        corpo += (
            f'<pattern id="{padroes[chave]}" patternUnits="userSpaceOnUse" '
            'width="9" height="9" patternTransform="rotate(35)">'
            f'<rect width="9" height="9" fill="{PAPER}"/>'
            f'<rect width="4" height="9" fill="{cor}"/></pattern>'
        )
    corpo += "</defs>"
    corpo += text(30, 28, titulo, 22, INK, weight="700")
    corpo += text(30, 50, subtitulo, 13, MUTED)
    topo = 84
    corpo += text(238, topo - 14, "VOTO PARA GOVERNADOR", 12, MUTED, weight="700")
    corpo += text(820, topo - 14, "2º TURNO PRESIDENCIAL", 12, MUTED, weight="700")

    espaco = 18
    esquerda, y = {}, topo
    for nome in ordem:
        esquerda[nome] = y
        y += massa[nome] * escala + espaco
    altura = y
    direita, y = {}, topo
    for nome in destinos:
        direita[nome] = y
        y += destino_pct[nome] * escala + espaco
    altura = max(altura, y)

    topo_esq, topo_dir = dict(esquerda), dict(direita)
    for celula in celulas:
        if celula["valor_pp"] < 1e-9:
            continue
        nome, destino = celula["origem"], celula["destino"]
        a, b = topo_esq[nome], topo_dir[destino]
        espessura = celula["valor_pp"] * escala
        topo_esq[nome] += espessura
        topo_dir[destino] += espessura
        natureza = (
            "linha publicada pelo instituto"
            if celula["medida"]
            else "estimada por ajuste proporcional iterativo"
        )
        rotulo = (
            f"{primeiro_nome(nome)} para {CURTO[destino]}: "
            f"{fmt(celula['valor_pp'], 2)} pontos, {natureza}. "
            f"Faixa de Fréchet: {fmt(celula['frechet_min_pp'])} a "
            f"{fmt(celula['frechet_max_pp'])} pontos."
        )
        preenche = (
            CORES_DESTINO[destino] if celula["medida"] else f"url(#{padroes[destino]})"
        )
        corpo += (
            f'<path d="M240 {a:.1f} C480 {a:.1f} 590 {b:.1f} 818 {b:.1f} '
            f"L818 {b + espessura:.1f} C590 {b + espessura:.1f} "
            f'480 {a + espessura:.1f} 240 {a + espessura:.1f}Z" fill="{preenche}" '
            f'opacity=".85" tabindex="0" class="flow" '
            f'aria-label="{escape(rotulo)}"><title>{escape(rotulo)}</title></path>'
        )
    for nome in ordem:
        alto = massa[nome] * escala
        corpo += (
            f'<rect x="228" y="{esquerda[nome]:.1f}" width="10" '
            f'height="{alto:.1f}" fill="{INK}"/>'
        )
        marca = " ·" if nome in medidas else ""
        corpo += text(
            218,
            esquerda[nome] + alto / 2 + 5,
            f"{primeiro_nome(nome)} {fmt(massa[nome])}{marca}",
            14,
            INK,
            "end",
        )
    for nome in destinos:
        alto = destino_pct[nome] * escala
        corpo += (
            f'<rect x="820" y="{direita[nome]:.1f}" width="10" '
            f'height="{alto:.1f}" fill="{CORES_DESTINO[nome]}"/>'
        )
        corpo += text(
            838,
            direita[nome] + alto / 2 + 5,
            f"{CURTO[nome]} {fmt(destino_pct[nome])}",
            15,
            CORES_DESTINO[nome],
            weight="600",
        )
    rodape = altura + 14
    corpo += text(
        30,
        rodape,
        f"Fita sólida: {len(medidas)} origens com linha publicada. "
        f"Fita hachurada: {len(ordem) - len(medidas)} origens estimadas. "
        "O ponto ao lado do nome marca a origem publicada.",
        14,
    )
    return svg(
        corpo,
        rodape + 26,
        f"{uf}: fluxo agregado do voto de governador para o segundo turno "
        f"presidencial, com {len(medidas)} de {len(ordem)} origens medidas",
    )


RECORTES = (
    ("sexo", "Masculino"),
    ("sexo", "Feminino"),
    ("idade", "16-24"),
    ("idade", "25-34"),
    ("idade", "35-44"),
    ("idade", "45-59"),
    ("idade", "60+"),
    ("escolaridade", "Fundamental"),
    ("escolaridade", "Medio"),
    ("escolaridade", "Superior"),
    ("ocupacao", "PEA"),
    ("ocupacao", "Nao PEA"),
    ("natureza", "Regiao metropolitana"),
    ("natureza", "Interior"),
)
NOMES = {
    "Medio": "Médio",
    "Nao PEA": "Fora da PEA",
    "Regiao metropolitana": "Região metropolitana",
    "16-24": "16 a 24 anos",
    "25-34": "25 a 34 anos",
    "35-44": "35 a 44 anos",
    "45-59": "45 a 59 anos",
    "60+": "60 anos ou mais",
}


def indice_de_recortes(estado):
    return {(r["dimensao"], r["recorte"]): r for r in estado["vao_por_recorte_turno2"]}


def vao_por_recorte(dados, escala=4.2):
    """Barras divergentes, só em partições fechadas nos três estados."""
    tabelas = {uf: indice_de_recortes(dados["estados"][uf]) for uf in UFS}
    centros = {"SP": 380, "RJ": 660, "MG": 940}
    corpo = text(30, 28, "O vão dentro de cada recorte", 24, INK, weight="700")
    corpo += text(
        30,
        50,
        "Candidatura de direita ao governo menos Flávio, no 2º turno, na mesma "
        "entrevista. Só partições fechadas nos três estados.",
        13,
        MUTED,
    )
    topo = 104
    for uf, cx in centros.items():
        vao = dados["estados"][uf]["vao"]["turno2"]["vao_pp"]
        corpo += text(cx, topo - 38, uf, 21, INK, "middle", "700")
        corpo += text(cx, topo - 18, f"total {sinal(vao)}", 13, MUTED, "middle")
    altura_linha = 26
    for i, chave in enumerate(RECORTES):
        y = topo + i * altura_linha
        if i % 2 == 0:
            corpo += (
                f'<rect x="24" y="{y - 3}" width="1052" '
                f'height="{altura_linha}" fill="{FAIXA}"/>'
            )
        corpo += text(30, y + 15, NOMES.get(chave[1], chave[1]), 14)
        for uf, cx in centros.items():
            linha = tabelas[uf][chave]
            valor = linha["vao_pp"]
            largura = abs(valor) * escala
            cor = TEAL if valor >= 0 else BLUE
            dica = (
                f"{uf}, {NOMES.get(chave[1], chave[1])}: governo do estado "
                f"{linha['governador']}%, Flávio {linha['flavio']}%, vão "
                f"{sinal(valor)} pontos, base ponderada {linha['base_governador']}."
            )
            corpo += (
                f'<rect x="{(cx if valor >= 0 else cx - largura):.1f}" y="{y + 2}" '
                f'width="{largura:.1f}" height="16" fill="{cor}">'
                f"<title>{escape(dica)}</title></rect>"
            )
            corpo += text(
                cx + largura + 7 if valor >= 0 else cx - largura - 7,
                y + 15,
                sinal(valor),
                12,
                TEAL_TXT if valor >= 0 else cor,
                "start" if valor >= 0 else "end",
                "600",
            )
    base = topo + len(RECORTES) * altura_linha
    for cx in centros.values():
        corpo += (
            f'<line x1="{cx}" y1="{topo - 6}" x2="{cx}" y2="{base}" '
            f'stroke="{INK}" stroke-width="2"/>'
        )
    corpo += text(
        30,
        base + 28,
        "Barra à direita: a candidatura estadual tem mais voto que Flávio. "
        "À esquerda: Flávio tem mais voto. Um ponto vale 4,2 pixels.",
        13,
        MUTED,
    )
    return svg(
        corpo,
        base + 48,
        "Vão por recorte em SP, RJ e MG: positivo em quatorze recortes de São "
        "Paulo e de Minas, negativo em quatorze recortes do Rio",
    )
