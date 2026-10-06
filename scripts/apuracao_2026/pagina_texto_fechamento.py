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
from .pagina_comum import NOME_UF, inteiro, nota, num, p, sinal, tabela
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


def _ic(m: dict | None, casas: int = 1) -> str:
    if not m or not m.get("ic95"):
        return "s/d"
    lo, hi = m["ic95"]
    return f"de {sinal(lo, casas)} a {sinal(hi, casas)}"


# ------------------------------------------------------------------ abertura


def abertura(F: dict) -> str:
    c = F["cobertura"]
    lei = next((x for x in F["fontes_legais"] if "23.751" in x["norma"]), None)
    regra = (
        "A votação vai das 8h às 17h de Brasília"
        + (
            " (Res. TSE nº 23.751/2026, pela citação do Poder360; o artigo não foi conferido)"
            if lei
            else ""
        )
        + ", e às 17h quem está na fila recebe senha e vota depois (Código Eleitoral, art. 153)."
    )
    h = p(regra, "verificado")
    if c.get("parcial"):
        h += p(
            f"A coleta dos boletins de 2026 ainda corre ({len(c['ufs_completas'])} UFs completas); a comparação entre "
            "os anos usa só as UFs completas."
        )
    return h


def achados_contrarios(F: dict) -> str:
    return "".join(
        p(escape(x), "contrario") for x in F["achados"].get("contrario") or []
    )


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
    esc = FT.tipo(F, "escola fora de zona rural")
    ald = FT.tipo(F, "aldeia ou terra indígena")

    def tarde(x: dict) -> str:
        return pct((x.get("encerramento_2026") or {}).get("depois_1800_pct"))

    return p(
        f"Metade das urnas encerrou até as <strong>{hora(e.get('mediana'))}</strong> de Brasília; "
        f"{pct(e.get('depois_1800_pct'))} às 18h ou depois e {pct(e.get('depois_1900_pct'))} às 19h ou depois. Às 18h "
        "ou depois, por região: "
        + lista([f"{g['chave']} {tarde(g)}" for g in ordem])
        + f"; no topo, {NOME_UF.get(ufs[0]['chave'], ufs[0]['chave'])} {tarde(ufs[0])}. O boletim chegou ao TSE, na mediana, às {hora(a.get('mediana'))} em 2026 e às {hora(b.get('mediana'))} em "
        f"2022, e depois das 19h chegaram {pct(a.get('depois_1900_pct'))} das seções em 2026 e "
        f"{pct(b.get('depois_1900_pct'))} em 2022; da chegada de 2026, a fila pesa {duracao(dec.get('fila_mediana_min'))} "
        f"na mediana e a mídia até o TSE, {duracao(dec.get('transmissao_mediana_min'))}. Aldeia fecha tarde em "
        f"{tarde(ald)} das seções, mas é só {pct(ald.get('pct_das_tardias_2026'))} das tardias; escola fora de zona rural "
        f"é {pct(esc.get('pct_das_tardias_2026'))}.",
        "verificado",
    )


# ------------------------------------------------------------------ 2 persistência


def persistencia(F: dict) -> str:
    P = F["persistencia"]
    cor = P.get("correlacao") or {}
    dec = P.get("decil") or {}
    loc = P.get("locais") or {}
    ic = cor.get("spearman_ic95") or [None, None]
    h = p(
        f"O atraso mora no mesmo lugar. Entre {inteiro(P.get('municipios'))} municípios, a correlação de postos entre a "
        f"chegada mediana de 2022 e a de 2026 é {num(cor.get('spearman'), 2)} ({num(ic[0], 2)} a {num(ic[1], 2)}); "
        f"dentro da UF, {num(cor.get('spearman_dentro_uf'), 2)}. {inteiro(dec.get('persistentes'))} municípios, com "
        f"{inteiro(dec.get('eleitorado_2026_persistentes'))} aptos, ficaram no décimo mais tardio nos dois anos, "
        f"{num(dec.get('razao'), 1)} vezes o acaso ({num(dec.get('esperado_independencia'), 0)}); entre "
        f"{inteiro(loc.get('casados'))} locais de votação com o mesmo nome, {inteiro(loc.get('persistentes'))}, "
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
                "Hora mediana de Brasília das seções do município. Locais rurais: zona rural, assentamento, quilombo ou "
                "aldeia, pelo nome e endereço.",
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
        f"Sem controle, a relação é forte: nas seções que encerraram de 17:00 a 17:30, Lula teve {pct(f1.get('lula_pct'))} "
        f"e Flávio {pct(f1.get('flavio_pct'))} ({inteiro(f1.get('secoes'))} seções); depois das 19h, Lula "
        f"{pct(f4.get('lula_pct'))} e Flávio {pct(f4.get('flavio_pct'))} ({inteiro(f4.get('secoes'))} seções), e cada hora "
        f"de atraso vem com {pts(ib.get('estimativa'))} de Lula.",
        "verificado",
    )
    frase_uf = ""
    if sp:
        maiores = lista([f"{x['uf']} {sinal(x['rho_lula'], 2)}" for x in sp[:3]])
        menores = lista([f"{x['uf']} {sinal(x['rho_lula'], 2)}" for x in sp[-2:]])
        frase_uf = f" Seção a seção, a correlação de postos dentro de cada UF é pequena: de {maiores} a {menores}."
    h += p(
        f"O que sobrevive ao controle é menor. Dentro da zona, cada hora vale <strong>{pts(iz.get('estimativa'), 2)}</strong> "
        f"de Lula ({_ic(iz, 2)}); com tamanho e tipo de local, <strong>{pts(ic.get('estimativa'), 2)}</strong> "
        f"({_ic(ic, 2)}) e Flávio {pts(ff.get('estimativa'), 2)}: sobra {pct(sob.get('lula_inclinacao'), 0)} da inclinação "
        f"bruta. Depois das 19h, {pts(fb.get('estimativa'))} sem controle, {pts(fz.get('estimativa'))} dentro da zona e "
        f"{pts(fc.get('estimativa'))} com tamanho e tipo." + frase_uf,
        "inferencia",
    )
    return h


def _frase_tamanho(L: dict) -> str:
    """Por que o controle de tamanho não reduz a diferença (número do JSON)."""
    c = ((L.get("controles_lula") or {}).get("coeficientes") or {}).get(
        "aptos até 199"
    ) or {}
    if c.get("estimativa") is None:
        return ""
    return (
        " O tamanho não reduz a diferença porque, dentro da zona, a seção pequena vota mais em Lula "
        f"({pts(c['estimativa'])} com até 199 aptos sobre a de 300 a 349), e a tardia é a grande."
    )


def conferencia(F: dict) -> str:
    C = F["conferencia_secoes"]
    m = C.get("base_atual_mesmas_ufs") or {}
    t = C.get("base_atual") or {}
    if not m or not t:
        return ""
    et = (t.get("estimador_zona") or {}).get("lula_pp") or {}
    return p(
        f"A conta seção contra o resto da zona dá {pts(t['formula_secao_contra_resto']['lula_pp'], 2)} para as que "
        f"encerraram depois das 19h; o estimador deste bloco, que compara os grupos inteiros e pondera pela zona, "
        f"{pts(et.get('estimativa'), 2)}. A diferença é de método, não de dado.",
        "verificado",
    )


def explicacoes(F: dict) -> str:
    z = FT.estimador(F, "tarde18_zona")
    zt = FT.estimador(F, "tarde18_zona_tamanho")
    ma = F["explicacoes"]["modelo_atraso"]
    st = ma.get("so_tamanho") or {}
    cp = ma.get("completo") or {}
    irr = F["explicacoes"]["irregularidade"]

    def est(e: dict, k: str) -> float | None:
        return (e.get(k) or {}).get("estimativa")

    return p(
        "Três explicações concorrem, e o boletim testa duas. Fila de seção grande: dentro da zona, a seção que encerrou "
        f"às 18h ou depois teve {num(est(z, 'votantes_secao'), 0)} votantes a mais, mas o tamanho explica só "
        f"{pct(100 * (st.get('r2_dentro') or 0), 0)} da chance de fechar tarde ({pct(100 * (cp.get('r2_dentro') or 0), 0)} "
        "com biometria e tipo de local). Identificação lenta: a seção tardia habilitou mais eleitores por ano de "
        f"nascimento, o caminho quando a biometria falha ({pts(est(z, 'ano_nascimento_pp'), 2)} dentro da zona, "
        f"{pts(est(zt, 'ano_nascimento_pp'), 2)} na mesma faixa de tamanho), e atendeu "
        f"{num(abs(est(zt, 'votantes_hora') or 0), 1)} votantes por hora a menos. Irregularidade: o boletim não testa; o "
        f"log da urna, com cada habilitação e sua hora, testa, e o acervo guarda o SHA-256 dele em "
        f"{inteiro(irr.get('secoes_com_hash_do_log'))} seções.",
        "inferencia",
    )


def juizo_e_hipotese(F: dict) -> str:
    loc = (F["persistencia"].get("locais") or {}) if F.get("persistencia") else {}
    h = nota(
        "juizo",
        "A providência barata é pôr fiscal de partido nas seções que historicamente fecham tarde, onde a fila depois "
        "das 17h fica sem testemunha. A lei permite dois fiscais por partido em cada seção e um fiscal para várias do "
        "mesmo local (Lei 9.504, art. 65, §§ 1º e 4º), impugnar a identidade do eleitor (Código Eleitoral, art. 132) e "
        "pedir cópia do boletim (Lei 9.504, art. 68, § 1º). Os "
        f"{inteiro(loc.get('persistentes'))} locais do décimo mais tardio nos dois anos somam "
        f"{inteiro(loc.get('secoes_2026_nos_persistentes'))} seções: é uma lista curta.",
    )
    h += nota(
        "hipotese",
        "Mesário que vota no lugar do ausente (o pianista), compra de voto e boca de urna na fila são hipóteses que o "
        "boletim não testa nem descarta. A prova é o log da urna (habilitações por ano de nascimento a segundos uma da "
        "outra no fim do dia), a ata da mesa e, para compra de voto e boca de urna, a representação ao juiz eleitoral "
        "(Lei 9.504, art. 39, § 5º, II, e art. 41-A). Sem documento, hora tardia é só hora tardia.",
        "Não é achado.",
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
        f"<li>{escape(x['norma'])}, {escape(x['dispositivo'])}. <em>Conferido {escape(x['como_conferido'])}.</em></li>"
        for x in F["fontes_legais"]
    )
    return f"<details><summary>Normas citadas e como foram conferidas</summary><ul>{leis}</ul></details>"


def limites_fechamento(F: dict) -> list[str]:
    """Limites do fechamento que seguem valendo; os de coleta em andamento saem quando ela termina."""
    ignora = (
        "Tipo de local",
        "A hora de recebimento de 2026 atravessa",
        "A hora de encerramento depende",
        "O log da urna de cada seção",
    )
    if not F["cobertura"].get("parcial"):
        ignora += ("A coleta dos boletins",)
    return [escape(x) for x in F["limites"] if not x.startswith(ignora)]


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


__all__ = ["CHAVES", "bloco", "limites_fechamento"]
