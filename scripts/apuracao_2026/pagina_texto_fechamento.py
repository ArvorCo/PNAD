"""Texto do capítulo 12 sobre o fechamento das seções: onde a votação termina tarde.

Lê `fechamento.json`. Regra da casa: figura antes do parágrafo, frase curta,
nenhum número digitado (todo número sai do JSON), uma casa decimal no texto,
achado contrário primeiro. O que é inferência, hipótese ou juízo editorial vem
com o selo correspondente. A frase sobre fiscais de partido é juízo editorial
declarado; mesário pianista, compra de voto e boca de urna entram como
hipótese, com o documento que a provaria.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape

from . import fechamento_texto as FT
from .pagina_comum import NOME_UF, inteiro, num, p, sinal, tabela
from .pagina_fig_base import nome_bonito
from .pagina_fig_fechamento import duracao, hora
from .pagina_texto import lista

CHAVES = [
    "cobertura",
    "distribuicao.brasil",
    "tamanho.linhas",
    "tipo_local.linhas",
    "persistencia.correlacao",
    "lula_hora.inclinacao",
    "voto.estimadores",
    "conferencia_secoes",
    "achados",
    "limites",
    "fontes_legais",
]


def pct(x: float | None, casas: int = 1) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def pts(x: float | None, casas: int = 1) -> str:
    if x is None:
        return "s/d"
    return f"{sinal(x, casas)} {'ponto' if abs(round(x, casas)) < 2 else 'pontos'}"


def contrario(texto: str) -> str:
    return f'<p><span class="selo selo-contrario">Achado contrário</span> {texto}</p>'


def _ic(m: dict | None, casas: int = 1) -> str:
    if not m or not m.get("ic95"):
        return "s/d"
    lo, hi = m["ic95"]
    return f"de {sinal(lo, casas)} a {sinal(hi, casas)}"


# ------------------------------------------------------------------ abertura


def abertura(F: dict) -> str:
    c = F["cobertura"]
    lei = next(
        (x for x in F["fontes_legais"] if "23.751" in x["norma"]),
        None,
    )
    regra = (
        "A votação vai das 8h às 17h de Brasília no país inteiro"
        + (
            " (Res. TSE nº 23.751/2026, citada pelo Poder360 em 04/10; o artigo não foi conferido "
            "porque o site do TSE recusou o acesso automatizado)"
            if lei
            else ""
        )
        + ". Às 17h, quem está na fila recebe senha e vota depois (Código Eleitoral, art. 153)."
    )
    h = p(
        "Onde a eleição termina tarde, se é sempre o mesmo lugar e o que isso tem a ver com o voto. "
        "O boletim de 2026 grava a hora em que a urna encerrou; o de 2022, não. A régua que existe "
        "nos dois anos é outra: a hora em que o boletim chegou ao TSE, que soma a fila e o caminho "
        "da mídia até o ponto de transmissão."
    )
    h += p(regra, "verificado")
    if c.get("parcial"):
        h += p(
            f"A coleta dos boletins de 2026 ainda corre. Estão completas {len(c['ufs_completas'])} UFs "
            f"({lista(c['ufs_completas'])}); faltam {lista(c['ufs_em_coleta'] + c['ufs_sem_2026'])}. "
            "Toda comparação entre os anos usa só as UFs completas, nos dois anos."
        )
    return h


def achados_contrarios(F: dict) -> str:
    return "".join(contrario(escape(x)) for x in F["achados"].get("contrario") or [])


# ------------------------------------------------------------------ 1 regiões


def regioes(F: dict) -> str:
    D = F["distribuicao"]
    br = D["brasil"]
    e, a, b = (
        br.get("encerramento_2026") or {},
        br.get("recebimento_2026") or {},
        br.get("recebimento_2022") or {},
    )
    dec = br.get("decomposicao_2026") or {}
    ordem = FT.regioes_ordem(F, "encerramento_2026")
    ufs = FT.ufs_ordem(F)
    h = p(
        f"Metade das urnas encerrou até as <strong>{hora(e.get('mediana'))}</strong> de Brasília; "
        f"{pct(e.get('depois_1800_pct'))} encerraram às 18h ou depois e {pct(e.get('depois_1900_pct'))} "
        "às 19h ou depois. Por região, a parcela das 18h em diante: "
        + lista(
            [
                f"{g['chave']} {pct((g.get('encerramento_2026') or {}).get('depois_1800_pct'))}"
                for g in ordem
            ]
        )
        + ". Nas UFs, as maiores são "
        + lista(
            [
                f"{NOME_UF.get(g['chave'], g['chave'])} {pct(g['encerramento_2026']['depois_1800_pct'])}"
                for g in ufs[:3]
            ]
        )
        + "; as menores, "
        + lista(
            [
                f"{NOME_UF.get(g['chave'], g['chave'])} {pct(g['encerramento_2026']['depois_1800_pct'])}"
                for g in ufs[-2:]
            ]
        )
        + ".",
        "verificado",
    )
    h += p(
        f"O boletim chegou ao TSE, na mediana, às {hora(a.get('mediana'))} em 2026 e às "
        f"{hora(b.get('mediana'))} em 2022, nas mesmas UFs. Depois das 19h chegaram {pct(a.get('depois_1900_pct'))} "
        f"das seções em 2026 e {pct(b.get('depois_1900_pct'))} em 2022. Da hora de chegada de 2026, a fila "
        f"pesa {duracao(dec.get('fila_mediana_min'))} na mediana; o caminho da mídia até o TSE, "
        f"{duracao(dec.get('transmissao_mediana_min'))}.",
        "verificado",
    )
    lac = FT.frase_lacuna(F)
    if lac:
        h += p(escape(lac), "verificado")
    t400 = FT.faixa_tamanho(F, "400 ou mais")
    t199 = FT.faixa_tamanho(F, "até 199")
    t3 = FT.faixa_tamanho(F, "300 a 349")
    t35 = FT.faixa_tamanho(F, "350 a 399")
    esc = FT.tipo(F, "escola fora de zona rural")
    rur = FT.tipo(F, "zona rural, assentamento ou quilombo")
    ald = FT.tipo(F, "aldeia ou terra indígena")
    tard = F["tamanho"]["secoes_tardias_2026"]
    h += p(
        "O que separa a seção que fecha tarde é o tamanho. Com até 199 aptos, "
        f"{pct((t199.get('encerramento_2026') or {}).get('depois_1800_pct'))} encerraram às 18h ou depois; "
        f"com 400 ou mais, {pct((t400.get('encerramento_2026') or {}).get('depois_1800_pct'))}. As faixas "
        f"de 300 a 399 aptos somam {pct((t3.get('pct_das_tardias_2026') or 0) + (t35.get('pct_das_tardias_2026') or 0))} "
        f"das {inteiro(tard)} seções tardias. Aldeia fecha tarde com frequência "
        f"({pct((ald.get('encerramento_2026') or {}).get('depois_1800_pct'))} das seções), mas é "
        f"{pct(ald.get('pct_das_tardias_2026'))} das tardias; zona rural, "
        f"{pct((rur.get('encerramento_2026') or {}).get('depois_1800_pct'))} e "
        f"{pct(rur.get('pct_das_tardias_2026'))}; escola fora de zona rural, "
        f"{pct((esc.get('encerramento_2026') or {}).get('depois_1800_pct'))} e "
        f"{pct(esc.get('pct_das_tardias_2026'))}. Tipo de local é inferência pelo nome e endereço.",
        "inferencia",
    )
    return h


# ------------------------------------------------------------------ 2 persistência


def persistencia(F: dict) -> str:
    P = F["persistencia"]
    cor = P.get("correlacao") or {}
    dec = P.get("decil") or {}
    loc = P.get("locais") or {}
    ic = cor.get("spearman_ic95") or [None, None]
    h = p(
        f"O atraso mora no mesmo lugar. Entre {inteiro(P.get('municipios'))} municípios, a correlação de "
        f"postos entre a hora mediana de chegada de 2022 e a de 2026 é {num(cor.get('spearman'), 2)} "
        f"(intervalo de 95% de {num(ic[0], 2)} a {num(ic[1], 2)}); dentro da mesma UF, "
        f"{num(cor.get('spearman_dentro_uf'), 2)}. {inteiro(dec.get('persistentes'))} municípios ficaram no "
        f"décimo mais tardio do país nos dois anos, {num(dec.get('razao'), 1)} vezes o que o acaso daria "
        f"({num(dec.get('esperado_independencia'), 0)}). Somam {inteiro(dec.get('eleitorado_2026_persistentes'))} "
        "eleitores aptos.",
        "inferencia",
    )
    h += p(
        "Nesses municípios, a votação terminou, na mediana, às "
        f"{hora(dec.get('encerramento_mediana_persistentes'))} (no conjunto, "
        f"{hora(dec.get('encerramento_mediana_todos'))}) e a mídia levou "
        f"{duracao(dec.get('transmissao_mediana_persistentes'))} até o TSE (no conjunto, "
        f"{duracao(dec.get('transmissao_mediana_todos'))}). O que se repete de um ano para o outro é a "
        f"distância. Entre {inteiro(loc.get('casados'))} locais de votação com o mesmo nome nos dois anos, "
        f"{inteiro(loc.get('persistentes'))} chegaram no décimo mais tardio das duas vezes, "
        f"{num(loc.get('razao'), 1)} vezes o acaso.",
        "inferencia",
    )
    linhas = []
    for x in P.get("lista") or []:
        linhas.append(
            [
                x["uf"],
                escape(nome_bonito(x["municipio"] or x["mun_tse"])),
                inteiro(x["eleitorado_2026"]),
                hora(x["mediana_2022"]),
                hora(x["mediana_2026"]),
                hora(x["encerramento_mediana_2026"]),
                duracao(x["transmissao_mediana_2026"]),
                pct(x["rural_pct"], 0),
            ]
        )
    if linhas:
        h += (
            f"<details><summary>Os {len(linhas)} municípios que chegaram mais tarde nos dois anos</summary>"
            + tabela(
                [
                    "UF",
                    "Município",
                    "Eleitorado",
                    "Chegada 2022",
                    "Chegada 2026",
                    "Fim da votação 2026",
                    "Mídia até o TSE",
                    "Locais rurais",
                ],
                linhas,
                "Hora mediana de Brasília das seções do município. Ordem: posição média no décimo mais tardio "
                "dos dois anos. Locais rurais: zona rural, assentamento, quilombo ou aldeia, pelo nome e endereço.",
            )
            + "</details>"
        )
    return h


# ------------------------------------------------------------------ 3 voto


def voto_lula(F: dict) -> str:
    L = F["lula_hora"]

    def b(faixa: str) -> dict:
        return FT.bruta(F, "Brasil", faixa)

    f1, f4 = b("17:00 a 17:30"), b("depois de 19:00")
    ib = FT.coef(F, "inclinacao", "bruta", "lula", "horas_atraso")
    iz = FT.coef(F, "inclinacao", "zona", "lula", "horas_atraso")
    ic = FT.coef(F, "inclinacao", "zona_controles", "lula", "horas_atraso")
    fb = FT.coef(F, "por_faixa", "bruta", "lula", "depois de 19:00")
    fz = FT.coef(F, "por_faixa", "zona", "lula", "depois de 19:00")
    fc = FT.coef(F, "por_faixa", "zona_controles", "lula", "depois de 19:00")
    ff = FT.coef(F, "inclinacao", "zona_controles", "flavio", "horas_atraso")
    sob = L.get("sobrevive_pct") or {}
    sp = L.get("spearman_uf") or []
    h = p(
        f"Sem controle nenhum, a relação é forte. Nas seções que encerraram de 17:00 a 17:30, Lula teve "
        f"{pct(f1.get('lula_pct'))} dos válidos e Flávio {pct(f1.get('flavio_pct'))} "
        f"({inteiro(f1.get('secoes'))} seções); nas que encerraram depois das 19h, Lula {pct(f4.get('lula_pct'))} "
        f"e Flávio {pct(f4.get('flavio_pct'))} ({inteiro(f4.get('secoes'))} seções). Cada hora a mais de "
        f"atraso vem com <strong>{pts(ib.get('estimativa'))}</strong> de Lula. Essa correlação bruta é "
        "esperada: seção grande, rural e indígena fecha tarde e vota em Lula, e o Nordeste fecha mais tarde "
        "que o Sul.",
        "verificado",
    )
    h += p(
        "O número que interessa é o que sobrevive ao controle. Dentro da mesma zona, cada hora de atraso vale "
        f"<strong>{pts(iz.get('estimativa'), 2)}</strong> de Lula (intervalo de 95% {_ic(iz, 2)}); dentro da zona, "
        f"com tamanho da seção e tipo de local, <strong>{pts(ic.get('estimativa'), 2)}</strong> ({_ic(ic, 2)}), e "
        f"Flávio {pts(ff.get('estimativa'), 2)}. Sobra {pct(sob.get('lula_inclinacao'), 0)} da inclinação bruta. "
        f"Para as seções que encerraram depois das 19h: {pts(fb.get('estimativa'))} sem controle, "
        f"{pts(fz.get('estimativa'))} dentro da zona e {pts(fc.get('estimativa'))} com tamanho e tipo."
        + _frase_tamanho(L),
        "inferencia",
    )
    if sp:
        maiores = lista([f"{x['uf']} {sinal(x['rho_lula'], 2)}" for x in sp[:3]])
        menores = lista([f"{x['uf']} {sinal(x['rho_lula'], 2)}" for x in sp[-2:]])
        h += p(
            f"Seção a seção, dentro de cada UF, a correlação de postos entre a hora de encerramento e a parte de "
            f"Lula é pequena: as maiores são {maiores}; as menores, {menores}. Correlação dentro da "
            "zona não identifica mecanismo: fila, identificação lenta e irregularidade deixam o mesmo rastro no "
            "boletim. Só a ata da mesa e o log da urna separam as três.",
            "inferencia",
        )
    h += conferencia(F)
    return h


def _frase_tamanho(L: dict) -> str:
    """Por que o controle de tamanho não reduz a diferença (número do JSON)."""
    c = ((L.get("controles_lula") or {}).get("coeficientes") or {}).get(
        "aptos até 199"
    ) or {}
    if c.get("estimativa") is None:
        return ""
    return (
        " O controle de tamanho não reduz a diferença porque, dentro da zona, a seção pequena "
        f"vota mais em Lula: com até 199 aptos, {pts(c['estimativa'])} sobre a de 300 a 349. Como a "
        "seção tardia é a grande, tirar o tamanho deixa a parte tardia mais nítida."
    )


def conferencia(F: dict) -> str:
    C = F["conferencia_secoes"]
    pub = C.get("publicado_secoes_json") or {}
    m = C.get("base_atual_mesmas_ufs") or {}
    t = C.get("base_atual") or {}
    if not pub or not m:
        return ""
    ez = (m.get("estimador_zona") or {}).get("lula_pp") or {}
    et = (t.get("estimador_zona") or {}).get("lula_pp") or {}
    return p(
        f"A análise por seção acima publicou {inteiro(pub.get('secoes'))} seções encerradas depois das 19h, "
        f"com Lula {pts(pub.get('lula_pp'), 2)} sobre o resto da zona, na base de {inteiro(pub.get('secoes_validas_na_base'))} "
        f"seções. Nas mesmas UFs completas daquela rodada, a mesma conta dá hoje "
        f"{pts(m['formula_secao_contra_resto']['lula_pp'], 2)} ({inteiro(m['secoes_depois_19h'])} seções). A "
        f"diferença para o estimador deste capítulo ({pts(ez.get('estimativa'), 2)}) é de método: aquela conta "
        "compara cada seção tardia com o resto da zona, inclusive as outras tardias, e pondera pela seção; "
        f"comparada só com as não tardias, a mesma seção dá {pts(m['formula_secao_contra_demais']['lula_pp'], 2)}; "
        "o estimador compara os dois grupos inteiros e pondera pela zona. Com todas as UFs de agora, "
        f"{pts(t['formula_secao_contra_resto']['lula_pp'], 2)} pela conta da seção e "
        f"{pts(et.get('estimativa'), 2)} pelo estimador.",
        "verificado",
    )


def explicacoes(F: dict) -> str:
    z = FT.estimador(F, "tarde18_zona")
    zt = FT.estimador(F, "tarde18_zona_tamanho")
    e22 = FT.estimador(F, "recebimento_decil_2022")
    e26 = FT.estimador(F, "recebimento_decil_2026")
    ma = F["explicacoes"]["modelo_atraso"]
    st = ma.get("so_tamanho") or {}
    cp = ma.get("completo") or {}
    irr = F["explicacoes"]["irregularidade"]

    def est(e: dict, k: str) -> float | None:
        return (e.get(k) or {}).get("estimativa")

    h = p(
        "Três explicações concorrem, e o boletim testa duas. Fila de seção grande: dentro da zona, a seção que "
        f"encerrou às 18h ou depois teve {num(est(z, 'votantes_secao'), 0)} votantes a mais que as demais, e só o "
        f"tamanho explica {pct(100 * (st.get('r2_dentro') or 0), 0)} da variação da chance de fechar tarde dentro "
        f"da zona; com biometria e tipo de local, {pct(100 * (cp.get('r2_dentro') or 0), 0)}.",
        "inferencia",
    )
    h += p(
        "Identificação lenta: a seção tardia tem mais eleitor habilitado por ano de nascimento, que é o "
        "caminho quando a biometria cadastrada não reconhece o dedo: "
        f"{pts(est(z, 'ano_nascimento_pp'), 2)} dentro da zona e {pts(est(zt, 'ano_nascimento_pp'), 2)} dentro da "
        f"zona e da faixa de tamanho. Com o mesmo tamanho, ela atendeu {num(abs(est(zt, 'votantes_hora') or 0), 1)} "
        "votantes por hora a menos: votação mais lenta, não só mais gente. Idade por seção, que pesa na biometria "
        "e no voto, não está no acervo para o país.",
        "inferencia",
    )
    h += p(
        "Irregularidade: não é testável com o boletim. O boletim diz quantos votaram e quando a votação "
        "terminou, não quem habilitou cada eleitor nem em que ritmo. O log da urna registra cada habilitação com "
        f"hora e forma; o acervo da coleta guarda o SHA-256 do log de {inteiro(irr.get('secoes_com_hash_do_log'))} "
        "seções, não o arquivo, que segue publicado pelo TSE.",
        "verificado",
    )
    h += p(
        "E o padrão não é de 2026. Pela régua que existe nos dois anos, a seção que chegou ao TSE no décimo mais "
        f"tardio votou mais em Lula do que o resto da própria zona em 2022 ({pts(est(e22, 'lula_pp'))}, intervalo "
        f"{_ic(e22.get('lula_pp'))}) e em 2026 ({pts(est(e26, 'lula_pp'))}, {_ic(e26.get('lula_pp'))}).",
        "inferencia",
    )
    return h


def juizo_e_hipotese(F: dict) -> str:
    loc = (F["persistencia"].get("locais") or {}) if F.get("persistencia") else {}
    h = (
        '<aside class="juizo"><b>Juízo editorial</b>'
        "A providência barata é pôr fiscal de partido nas seções que historicamente fecham tarde. É ali que a "
        "fila depois das 17h, o mesário e a boca de urna ficam sem testemunha. A lei dá o instrumento: até dois "
        "fiscais por partido em cada seção, e um mesmo fiscal pode cobrir mais de uma seção do mesmo local (Lei 9.504, "
        "art. 65, §§ 1º e 4º); o fiscal pode protestar e impugnar, inclusive a identidade do eleitor (Código "
        "Eleitoral, art. 132), e pedir cópia do boletim até uma hora depois da emissão (Lei 9.504, art. 68, § 1º). "
        f"Os {inteiro(loc.get('persistentes'))} locais que chegaram no décimo mais tardio nos dois anos somam "
        f"{inteiro(loc.get('secoes_2026_nos_persistentes'))} seções: é uma lista curta.</aside>"
    )
    h += (
        '<aside class="hyp"><b>Hipótese, não achado</b>'
        "Mesário que vota no lugar do ausente (o pianista), compra de voto e boca de urna na fila depois das 17h "
        "são hipóteses que o boletim não testa: este capítulo não as mostra e não as descarta. Cada uma tem prova "
        "própria: o log da urna, em que uma sequência de habilitações por ano de nascimento a poucos segundos uma "
        "da outra no fim do dia é a assinatura do pianista; a ata da mesa, com as ocorrências, os fiscais presentes "
        "e as senhas entregues às 17h; e, para compra de voto e boca de urna, boletim de ocorrência e representação "
        "ao juiz eleitoral ou ao Ministério Público Eleitoral (Lei 9.504, art. 39, § 5º, II, e art. 41-A). Sem esses "
        "documentos, a hora tardia é só hora tardia.</aside>"
    )
    return h


def amostras(F: dict) -> str:
    A = (F.get("amostras") or {}).get("encerramento_mais_tarde") or []
    if not A:
        return ""
    linhas = []
    for s in A:
        linhas.append(
            [
                s["uf"],
                escape(nome_bonito(s.get("municipio") or "")),
                str(s["zona"]),
                str(s["secao"]),
                escape(nome_bonito(s.get("local") or "")),
                hora(s.get("enc_min")),
                inteiro(s.get("comparecimento")),
                num(s.get("votantes_hora"), 1),
                pct(s.get("ano_nascimento_pct")),
                pct(s.get("lula_pct")),
                escape(s.get("explicacao") or ""),
            ]
        )
    return (
        f"<details><summary>As {len(linhas)} seções que encerraram mais tarde</summary>"
        + tabela(
            [
                "UF",
                "Município",
                "Zona",
                "Seção",
                "Local",
                "Fim da votação",
                "Votantes",
                "Por hora",
                "Ano de nascimento",
                "Lula",
                "Regra acionada",
            ],
            linhas,
            "Hora de Brasília. Por hora: votantes por hora de urna aberta. Ano de nascimento: parte dos votantes "
            "habilitada por ano de nascimento. A regra acionada é inferência pelo cadastro, não verificação.",
        )
        + "</details>"
    )


def rodape(F: dict) -> str:
    leis = "".join(
        f"<li>{escape(x['norma'])}, {escape(x['dispositivo'])}: {escape(x['conteudo'])}. "
        f"<em>Conferido {escape(x['como_conferido'])}.</em></li>"
        for x in F["fontes_legais"]
    )
    lim = "".join(f"<li>{escape(x)}</li>" for x in F["limites"])
    return (
        f"<details><summary>Normas citadas e como foram conferidas</summary><ul>{leis}</ul></details>"
        f"<details><summary>Limites do fechamento</summary><ul>{lim}</ul></details>"
    )


def bloco(F: dict, fig: Callable[[str], str]) -> str:
    """O fechamento das seções no capítulo 12, figura antes do parágrafo."""
    h = "<h3>Onde a votação termina tarde, em dois anos</h3>" + abertura(F)
    h += achados_contrarios(F)
    h += fig("fechamento_regioes") + regioes(F)
    h += fig("fechamento_persistencia") + persistencia(F)
    h += fig("fechamento_voto_lula") + voto_lula(F)
    h += fig("fechamento_voto_zona") + explicacoes(F)
    h += juizo_e_hipotese(F) + amostras(F) + rodape(F)
    return h


__all__ = ["CHAVES", "bloco"]
