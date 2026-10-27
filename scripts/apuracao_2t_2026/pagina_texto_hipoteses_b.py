"""Bloco "Precedentes: quando a votação foi estendida no dia", do capítulo de hipóteses.

Lê ``hipoteses.json`` (``precedentes``, que copia ``precedentes_prorrogacao.json``
sem reescrever o conteúdo, e os números de H1 e H2). Os textos de cada caso são
os campos do memorando de precedentes; a síntese usa os números do próprio acervo.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import (
    caixa,
    inteiro,
    nota,
    num,
    p,
    rotulo,
    sinal,
    tabela,
)

ROTULO_PAIS = {
    "ve_2015_legislativas": "Venezuela, legislativas de 2015",
    "ve_2013_presidencial": "Venezuela, presidencial de 2013",
    "ve_2018_presidencial": "Venezuela, presidencial de 2018",
    "ve_2024_presidencial": "Venezuela, presidencial de 2024",
    "pe_2026_gerais": "Peru, gerais de 2026",
    "us_2022_harris": "EUA, condado de Harris (Texas), 2022",
    "bo_2019_geral": "Bolívia, gerais de 2019",
    "ar_regra": "Argentina, a regra",
    "br_regra_e_precedentes": "Brasil, a regra e os pedidos anteriores",
    "br_2026_2t": "Brasil, 2º turno de 2026",
}


def _data(x: str | None) -> str:
    return f"{x[8:10]}/{x[5:7]}/{x[:4]}" if x else "regra"


def _fontes(it: dict) -> str:
    links = [
        f'<a href="{escape(f["url"])}" rel="noopener">{i}</a>'
        for i, f in enumerate(it["fontes"][:4], start=1)
    ]
    return " ".join(links)


def _resultado(it: dict, nac: dict | None) -> str:
    """Resultado do caso com selo: o do Brasil sai do arquivo nacional do TSE; o da Wikipédia é relato."""
    if it["id"] == "br_2026_2t" and nac:
        return (
            f"{rotulo('verificado')} Lula {num(nac['pct_lula'], 2)}% × Flávio {num(nac['pct_flavio'], 2)}% dos "
            f"válidos, {num(nac['pst'], 2)}% das seções totalizadas (arquivo nacional do TSE gerado às "
            f"{escape(nac['gerado_brt'][11:19])} de {escape(nac['gerado_brt'][8:10])}/{escape(nac['gerado_brt'][5:7])}; "
            "presidente.json)"
        )
    r = escape(it["resultado"] or "")
    return f"{rotulo('relato')} {r}" if "Wikipédia" in r else r


def tabela_precedentes(P: dict, nac: dict | None = None) -> str:
    linhas = []
    for it in P["itens"]:
        registro = (
            it["relatorios"][0]
            if it["relatorios"]
            else (it["oposicao"][0] if it["oposicao"] else "")
        )
        linhas.append(
            [
                escape(ROTULO_PAIS.get(it["id"], f"{it['pais']}, {it['eleicao']}")),
                _data(it["data"]),
                escape(it["hora_e_alcance"] or ""),
                escape(registro),
                _resultado(it, nac),
                _fontes(it),
            ]
        )
    return tabela(
        [
            "Caso",
            "Data",
            "Extensão e alcance",
            "O que se registrou",
            "Resultado",
            "Fontes",
        ],
        linhas,
        f"{len(P['itens'])} casos; páginas arquivadas com SHA-256 em {escape(P['manifesto_fontes'])}. "
        "Resultado citado da Wikipédia leva o selo de relato; o do Brasil vem do arquivo nacional do TSE",
    )


def precedentes(H: dict, PR: dict | None = None) -> str:
    """Bloco dos precedentes; ``PR`` é ``presidente.json``, de onde sai o resultado do Brasil."""
    P = H.get("precedentes")
    if not P:
        return ""
    nac = (PR or {}).get("nacional")
    h1, h2 = H["h1"], H["h2"]
    z = h2.get("zona") or {}
    ps = h1["pct_17_19_por_sinal"]
    sem_bio = ps.get("liberação sem biometria alta (BU)")
    todas = ps.get("todas")
    h = "<h3>Precedentes: quando a votação foi estendida no dia</h3>"
    h += caixa(
        "io",
        "De onde vêm os casos",
        f" Memorando de precedentes da casa (26/10), com {len(P['itens'])} casos e as páginas arquivadas com SHA-256. "
        "Cada caso traz quem decidiu, o alcance, o que oposição e observadores registraram e o resultado, nas palavras "
        "das fontes. Acusação de oposição entra como relato, nunca como fato.",
    )
    h += p(
        "Na Venezuela, em 6 de dezembro de 2015, o Conselho Nacional Eleitoral estendeu a votação até 19h "
        "“ou enquanto houver fila”, em anúncio da reitora Sandra Oblitas; pouco antes, Diosdado Cabello, presidente "
        "da Assembleia, havia defendido a ampliação. O reitor Luis Emilio Rondón e a oposição (MUD) chamaram a medida "
        "de ilegal. A CIDH registrou a “highly-questioned extension” do horário. A MUD venceu com maioria de dois terços.",
        "verificado",
    )
    h += p(
        "Líderes da oposição venezuelana suspeitavam de uma “operación remate”: manter centros abertos sem fila para "
        "buscar votantes de última hora. É relato de imprensa sem fonte nominal, e nenhuma fonte localizada mede "
        "quantos votos entraram depois das 18h, nem para quem.",
        "relato",
    )
    h += p(
        "Em 2013 o Centro Carter registrou encerramento anunciado bem depois das 18h, “puntos rojos” perto dos centros "
        "e voto assistido fora da norma em parte das mesas; em 2018 e em 2024 não houve extensão formal, e OEA, Centro "
        "Carter e União Europeia questionaram o processo por outras razões, principalmente a falta de resultados "
        "verificáveis por mesa em 2024. No Peru, em 12 de abril de 2026, a autoridade eleitoral estendeu a votação em "
        "todo o país às 11h da manhã. No condado de Harris, no Texas, em 2022, um juiz estendeu a votação em uma hora; "
        "a Suprema Corte do Texas mandou separar os votos tardios e verificar o efeito, e nenhuma disputa mudou. Na "
        "Bolívia, em 2019, não houve extensão, e sim interrupção da divulgação: a auditoria da OEA concluiu por "
        "manipulação, e Idrobo, Kronick e Rodríguez concluíram que a virada se explica pela ordem de contagem. Na "
        "Argentina, só vota depois do horário quem já está no local.",
        "verificado",
    )
    h += p(
        "No Brasil, o Código Eleitoral (arts. 144 e 153) e a Res. TSE 23.751/2026 (art. 160) mandam encerrar às 17h e "
        "distribuir senhas a quem está na fila; nenhum dos dois prevê prorrogação geral. Em 2020 o então presidente do "
        "TSE, Luís Roberto Barroso, recusou estender além das 17h; em 2022 Alexandre de Moraes negou à campanha de Lula "
        "o adiamento pedido por causa das operações da PRF. A extensão de 25/10/2026 é o primeiro caso nacional que "
        "localizamos.",
        "verificado",
    )
    h += f"<details><summary>Os {len(P['itens'])} casos, com fonte</summary>{tabela_precedentes(P, nac)}</details>"
    h += p(
        "O expediente denunciado na Venezuela precisa de urnas abertas, sem fila, depois do horário. No Brasil, "
        f"{num(h1['pct_17_19'], 3)}% dos votos do dia entraram entre 17h e 19h ({inteiro(h1['computados_17_19'])} "
        f"votos, contra uma diferença de {inteiro(h1['margem_votos'])}) e {inteiro(h1['computados_depois_19'])} depois "
        "das 19h. Mesmo todos de um só lado, não mudariam o resultado. A marca que a extensão deixaria como canal de "
        "votos não aparece nos arquivos públicos; o teste não alcança a totalização nem as urnas, que têm testes "
        "próprios (H2 e H5).",
        "inferencia",
    )
    testes = [
        [
            "Separar os votos tardios, como em Harris",
            "feito",
            f"{inteiro(h1['computados_17_19'])} votos entre 17h e 19h, {inteiro(h1['computados_depois_19'])} depois",
        ],
        [
            "Comparar as seções tardias com o próprio 1º turno",
            "feito",
            f"seções encerradas depois das 19h: {sinal(h1['apos_19h']['did_pp'], 2)} pp na fatia de Flávio "
            f"(IC95 de {sinal(h1['apos_19h']['ic95_pp'][0], 2)} a {sinal(h1['apos_19h']['ic95_pp'][1], 2)})",
        ],
        [
            "Biometria na janela final",
            "em parte",
            (
                (
                    f"nas seções com liberação sem biometria acima da regra, {num(sem_bio, 3)}% dos votos entre 17h e 19h, "
                    f"contra {num(todas, 3)}% em todas; a contagem do método de habilitação por hora ainda não foi feita"
                )
                if sem_bio is not None and todas is not None
                else "pendente"
            ),
        ],
        [
            "BU, RDV e QR contra a totalização do silêncio",
            "feito",
            f"{inteiro(h2['vsc_bu_igual'])} BUs iguais ao que a urna assinou; RDV igual em "
            f"{inteiro(h2['rdv_confere'])}; "
            + (
                f"{inteiro(z['zonas_conferem'])} de {inteiro(z['zonas'])} zonas fecham; "
                if z
                else ""
            )
            + f"{inteiro(h2['paralela'].get('igual', 0))} BUs impressos iguais",
        ],
    ]
    h += tabela(
        ["Teste sugerido pelos precedentes", "Situação", "Resultado"],
        testes,
        "O que os precedentes mandam testar",
    )
    h += nota(
        "juizo",
        "Na forma, o caso brasileiro é o mais atípico da lista: a ampliação nacional veio de um ministro da corte "
        "constitucional, a pedido de uma das campanhas, contra o parecer do Ministério Público Eleitoral no TSE, sem "
        "decisão localizada do próprio TSE e depois do horário de fechamento. Atipicidade de forma não mede efeito: "
        "o efeito, medido acima, é o de uma fração mínima dos votos.",
    )
    return h
