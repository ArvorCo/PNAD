"""Memorando `comparacao_2022.md`: os doze achados da comparação 2022 × 2026.

Nenhum número é digitado: todos saem do corpo de `comparacao_2022.json`. O texto
fixo foi escrito para sobreviver a citação hostil; quando um número muda, a
frase acompanha. Cada achado diz a natureza da afirmação (verificado, verificado
sob classificação editorial, inferido) e o caminho de onde o número sai.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

MENOS = "−"
NOMES_BLOCO = {
    "esquerda + centro-esquerda": "esquerda e centro-esquerda",
    "centro": "centro",
    "direita + centro-direita": "direita e centro-direita",
}
DC = "direita + centro-direita"
EC = "esquerda + centro-esquerda"


def dec(x: float | None, casas: int = 2, sinal: bool = False) -> str:
    """Decimal em pt-BR com vírgula, menos tipográfico e `+` opcional."""
    if x is None:
        return "n/d"
    texto = f"{abs(x):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if round(x, casas) < 0:
        return f"{MENOS}{texto}"
    if sinal and round(x, casas) > 0:
        return f"+{texto}"
    return texto


def mil(n: int | None, sinal: bool = False) -> str:
    """Inteiro com ponto de milhar, menos tipográfico e `+` opcional."""
    if n is None:
        return "n/d"
    texto = f"{abs(n):,}".replace(",", ".")
    if n < 0:
        return f"{MENOS}{texto}"
    if sinal and n > 0:
        return f"+{texto}"
    return texto


def pts(x: float | None, casas: int = 2, sinal: bool = False) -> str:
    """Número seguido de `ponto` (módulo abaixo de 2) ou `pontos`."""
    if x is None:
        return "n/d"
    unidade = "ponto" if abs(round(x, casas)) < 2 else "pontos"
    return f"{dec(x, casas, sinal)} {unidade}"


def lista(itens: Iterable[str]) -> str:
    partes = list(itens)
    if not partes:
        return "nenhuma"
    if len(partes) == 1:
        return partes[0]
    return ", ".join(partes[:-1]) + " e " + partes[-1]


def _uf_pp(itens: Iterable[Mapping[str, Any]], chave: str = "pp", n: int = 5) -> str:
    return lista(f"{x['uf']} {dec(x[chave], 2, True)}" for x in list(itens)[:n])


def _uf_votos(itens: Iterable[Mapping[str, Any]], n: int = 4) -> str:
    return lista(f"{x['uf']} {mil(x['votos'], True)}" for x in list(itens)[:n])


def _partido(tabela: list[dict[str, Any]], sigla: str) -> dict[str, Any]:
    return next(x for x in tabela if x["partido"] == sigla)


def _exige(condicao: bool, frase: str) -> None:
    """Frase fixa do memorando só sai se o número ainda a sustenta."""
    if not condicao:
        raise RuntimeError(
            f"comparacao_2022.md: o dado não sustenta mais a frase: {frase}"
        )


def _achado(titulo: str, texto: str, natureza: str, fonte: str) -> str:
    return f"### {titulo}\n\n{texto}\n\n- Natureza: {natureza}\n- Fonte: {fonte}\n"


def achados(c: dict[str, Any]) -> list[str]:
    pres = c["presidente"]
    br = pres["agregados"]["Brasil"]
    ne = pres["agregados"]["Nordeste"]
    no = pres["agregados"]["Norte"]
    cs = pres["agregados"]["Centro-Sul"]
    v1, v2 = br["comparacao"]["vs_1t"], br["comparacao"]["vs_2t"]
    contrib = pres["contribuicao_regional_vs_1t"]
    cam = c["camara"]
    sen = c["senado"]
    gov = c["governadores"]
    ass = c["assembleias"]["onze_casas"]
    jp = "analysis/apuracao_2026/dados/comparacao_2022.json"
    saida = []

    saida.append(
        _achado(
            f"1. A margem virou {dec(v1['virada_margem_pp'], 1)} pontos sobre o 1º turno "
            "de 2022",
            f"Lula terminou o 1º turno de 2022 com {pts(-v1['margem_2022_pp'])} de "
            f"vantagem sobre Bolsonaro nos válidos. Em 2026 Flávio terminou o 1º turno "
            f"{pts(br['margem_2026_pp'])} à frente de Lula: a margem andou "
            f"{pts(v1['virada_margem_pp'])} para a direita. Flávio teve "
            f"{mil(v1['direita_votos'], True)} votos sobre Bolsonaro no 1º turno de 2022; "
            f"Lula teve {mil(v1['lula_votos'], True)} sobre ele mesmo. Contra o 2º turno "
            f"de 2022 (Lula {pts(-v2['margem_2022_pp'])} à frente), a virada é de "
            f"{pts(v2['virada_margem_pp'])}.",
            "verificado (aritmética sobre os arquivos do TSE)",
            f"{jp} → presidente.saldo_nacional; api_2022 e presidente.json",
        )
    )
    soma2 = v2["direita_votos"] + v2["lula_votos"]
    _exige(soma2 < 0, "finalistas abaixo do 2º turno de 2022")
    _exige(-v2["lula_votos"] > -v2["direita_votos"], "Lula mais longe da própria marca")
    saida.append(
        _achado(
            "2. Os dois finalistas de 2026 somam menos votos que os de 2022 no 2º turno",
            f"Flávio tem {mil(-v2['direita_votos'])} votos a menos que Bolsonaro no 2º "
            f"turno de 2022 ({dec(br['pct_2026']['flavio'])}% contra "
            f"{dec(br['pct_2022_2t']['bolsonaro'])}% dos válidos). Lula tem "
            f"{mil(-v2['lula_votos'])} a menos que ele próprio no 2º turno de 2022 "
            f"({dec(br['pct_2026']['lula'])}% contra {dec(br['pct_2022_2t']['lula'])}%). "
            f"Somados, os dois finalistas estão {mil(-soma2)} votos abaixo do 2º turno "
            f"anterior, e as candidaturas de terceira via têm "
            f"{mil(br['votos_2026']['terceiros'])}. O resultado do dia 25 depende de onde "
            f"esse voto vai, e Lula está mais longe da própria marca que Flávio.",
            "verificado; a leitura do 2º turno é inferência (comparar 1º com 2º turno "
            "mede distância, não prevê transferência)",
            f"{jp} → presidente.agregados.Brasil",
        )
    )
    acima = pres["flavio_acima_bolsonaro_2t"]
    ne_acima = [x["uf"] for x in acima if x["grupo"] == "Nordeste"]
    _exige(ne["comparacao"]["vs_2t"]["direita_votos"] > 0, "Nordeste acima do 2º turno")
    saida.append(
        _achado(
            "3. No Nordeste, Flávio já passou o 2º turno de Bolsonaro",
            f"No Nordeste Flávio fez {mil(ne['votos_2026']['flavio'])} votos no 1º turno, "
            f"{mil(ne['comparacao']['vs_2t']['direita_votos'], True)} sobre os "
            f"{mil(ne['votos_2022_2t']['bolsonaro'])} de Bolsonaro no 2º turno de 2022 "
            f"({dec(ne['pct_2026']['flavio'])}% contra {dec(ne['pct_2022_2t']['bolsonaro'])}% "
            f"dos válidos) e {mil(ne['comparacao']['vs_1t']['direita_votos'], True)} sobre o "
            f"1º turno. No Norte, {mil(no['comparacao']['vs_2t']['direita_votos'], True)} "
            f"sobre o 2º turno. No Centro-Sul, "
            f"{mil(cs['comparacao']['vs_2t']['direita_votos'], True)}. A fatia de Flávio "
            f"passa a de Bolsonaro no 2º turno em {len(acima)} UFs, {len(ne_acima)} delas "
            f"no Nordeste ({lista(ne_acima)}), em pontos: {_uf_pp(acima, n=len(acima))}.",
            "verificado (soma das UFs; votos a mais no agregado não dizem que são os "
            "mesmos eleitores)",
            f"{jp} → presidente.agregados e presidente.flavio_acima_bolsonaro_2t",
        )
    )
    abaixo = pres["flavio_abaixo_bolsonaro_2t"]
    por_votos = sorted(abaixo, key=lambda x: x["votos"])
    faltas = {
        g: pres["agregados"][g]["comparacao"]["vs_2t"]["direita_votos"]
        for g in ("Nordeste", "Norte", "Centro-Sul")
    }
    _exige(
        min(faltas, key=faltas.__getitem__) == "Centro-Sul"
        and faltas["Centro-Sul"] < 0,
        "falta concentrada no Centro-Sul",
    )
    excecoes_1t = sorted(
        {x["uf"] for x in pres["ufs"] if x["uf"] != "ZZ"}
        - set(pres["ufs_flavio_acima_bolsonaro_1t"])
    )
    saida.append(
        _achado(
            "4. O que falta para repetir o 2º turno de 2022 está no Centro-Sul",
            f"Flávio fica abaixo da fatia de Bolsonaro no 2º turno de 2022 em "
            f"{len(abaixo)} UFs. As maiores distâncias em pontos: {_uf_pp(abaixo)}. Em "
            f"votos brutos: {_uf_votos(por_votos)}. Contra o 1º turno de 2022, a fatia de "
            f"Flávio é maior em {pres['n_ufs_flavio_acima_bolsonaro_1t']} das 27 UFs; a "
            f"exceção: {lista(excecoes_1t)}.",
            "verificado; dizer que essa diferença é a reserva do 2º turno é inferência "
            "(teto endereçável, não transferência certa)",
            f"{jp} → presidente.flavio_abaixo_bolsonaro_2t",
        )
    )
    lula_cs = contrib["lula_votos"]["Centro-Sul"]["pct_do_saldo_nacional"]
    _exige(
        v1["lula_votos"] < 0 and lula_cs >= 80, "perda de Lula quase toda no Centro-Sul"
    )
    lula_ne_1t = ne["votos_2022_1t"]["lula"]
    saida.append(
        _achado(
            "5. A perda de Lula sobre 2022 é quase toda do Centro-Sul",
            f"Contra o 1º turno de 2022, Lula perdeu {mil(-v1['lula_votos'])} votos no país. "
            f"O Centro-Sul responde por {dec(contrib['lula_votos']['Centro-Sul']['pct_do_saldo_nacional'], 1)}% "
            f"dessa perda ({mil(contrib['lula_votos']['Centro-Sul']['votos'])}) e o Nordeste "
            f"por {dec(contrib['lula_votos']['Nordeste']['pct_do_saldo_nacional'], 1)}% "
            f"({mil(contrib['lula_votos']['Nordeste']['votos'])}). O ganho de Flávio sobre "
            f"Bolsonaro no 1º turno se divide em "
            f"{dec(contrib['direita_votos']['Centro-Sul']['pct_do_saldo_nacional'], 1)}% no "
            f"Centro-Sul, {dec(contrib['direita_votos']['Nordeste']['pct_do_saldo_nacional'], 1)}% "
            f"no Nordeste e {dec(contrib['direita_votos']['Norte']['pct_do_saldo_nacional'], 1)}% "
            f"no Norte. No Nordeste, Lula perdeu "
            f"{dec(100 * -ne['comparacao']['vs_1t']['lula_votos'] / lula_ne_1t, 1)}% do que "
            f"tinha no 1º turno de 2022, e Flávio teve "
            f"{mil(ne['comparacao']['vs_1t']['direita_votos'], True)} votos sobre Bolsonaro.",
            "verificado",
            f"{jp} → presidente.contribuicao_regional_vs_1t",
        )
    )
    _exige(abs(v1["comparecimento_pp"]) < 0.5, "comparecimento estável no país")
    _exige(
        ne["comparacao"]["vs_1t"]["comparecimento_pp"] > 0
        and no["comparacao"]["vs_1t"]["comparecimento_pp"] > 0
        and cs["comparacao"]["vs_1t"]["comparecimento_pp"] < 0,
        "comparecimento maior no Norte e Nordeste, menor no Centro-Sul",
    )
    _exige(v1["terceiros_votos"] < 0, "terceira via caiu")
    saida.append(
        _achado(
            "6. Comparecimento estável no país, maior no Norte e Nordeste, menor no Centro-Sul",
            f"O comparecimento foi de {dec(br['pct_2026']['comparecimento'])}% contra "
            f"{dec(br['pct_2022_1t']['comparecimento'])}% no 1º turno de 2022 "
            f"({pts(v1['comparecimento_pp'], 2, True)}), com "
            f"{mil(v1['comparecimento_votos'])} votantes a mais e um eleitorado "
            f"{mil(v1['eleitorado_votos'])} maior. Nordeste "
            f"{pts(ne['comparacao']['vs_1t']['comparecimento_pp'], 2, True)}, Norte "
            f"{dec(no['comparacao']['vs_1t']['comparecimento_pp'], 2, True)}, Centro-Sul "
            f"{dec(cs['comparacao']['vs_1t']['comparecimento_pp'], 2, True)}. Brancos "
            f"{dec(br['pct_2026']['brancos'])}% ({dec(v1['brancos_pp'], 2, True)}), nulos "
            f"{dec(br['pct_2026']['nulos'])}% ({dec(v1['nulos_pp'], 2, True)}). A terceira via "
            f"caiu de {dec(br['pct_2022_1t']['terceiros'])}% para "
            f"{dec(br['pct_2026']['terceiros'])}% dos válidos ({mil(v1['terceiros_votos'], True)} votos).",
            "verificado",
            f"{jp} → presidente.agregados (comparecimento e abstenção sobre o eleitorado; "
            "brancos e nulos sobre o comparecimento)",
        )
    )
    b22, b26 = cam["por_bloco_2022"], cam["por_bloco_2026"]
    c22, c26 = cam["por_campo_2022"], cam["por_campo_2026"]
    _exige(
        abs(c26["esquerda"] - c22["esquerda"]) <= 3, "esquerda quase parada na Câmara"
    )
    _exige(
        c26["centro-esquerda"] - c22["centro-esquerda"]
        < c26["esquerda"] - c22["esquerda"],
        "centro-esquerda encolheu mais que a esquerda",
    )
    limite = "abaixo das" if b26[DC] < 308 else "acima das"
    teto = cam["sensibilidade_teto_direita_2022"]
    saida.append(
        _achado(
            f"7. Câmara: a direita ganhou {c26['direita'] - c22['direita']} cadeiras e o bloco "
            f"à direita {'chega' if b26[DC] >= 308 else 'ainda não chega'} a 308",
            f"Eleitos para a Câmara por campo, 2022 contra 2026: direita {c22['direita']} e "
            f"{c26['direita']} ({mil(c26['direita'] - c22['direita'], True)}), centro-direita "
            f"{c22['centro-direita']} e {c26['centro-direita']}, centro {c22['centro']} e "
            f"{c26['centro']}, centro-esquerda {c22['centro-esquerda']} e "
            f"{c26['centro-esquerda']}, esquerda {c22['esquerda']} e {c26['esquerda']}. O "
            f"bloco de direita e centro-direita foi de {b22[DC]} para {b26[DC]} "
            f"({mil(b26[DC] - b22[DC], True)}), {limite} 308 de emenda constitucional; "
            f"esquerda e centro-esquerda, de {b22[EC]} para {b26[EC]}. A esquerda em sentido "
            f"estrito quase não se moveu; quem encolheu foi a centro-esquerda. Contando "
            f"como direita as siglas extintas que a regra leva à centro-direita "
            f"({lista(f'{k} {v}' for k, v in teto['siglas'].items())}), o ganho da direita "
            f"cai para {mil(teto['delta_campo']['direita'], True)}, e o bloco não muda. "
            f"Pelo menos "
            f"{cam['trocas_de_bloco']['cadeiras']} cadeiras trocaram de bloco dentro das UFs.",
            "verificado sob classificação editorial (contagem exata; campo pela tabela da "
            f"casa); 2026 provisório em {lista(cam['ufs_provisorias_2026'])}",
            f"{jp} → camara.por_campo_2022, camara.por_campo_2026, camara.trocas_de_bloco",
        )
    )
    tab = cam["partidos"]
    pl, uni, pdt = _partido(tab, "PL"), _partido(tab, "UNIÃO"), _partido(tab, "PDT")
    pode, novo = _partido(tab, "PODE"), _partido(tab, "NOVO")
    pp_, mdb = _partido(tab, "PP"), _partido(tab, "MDB")
    _exige(
        uni["delta_cadeiras"] < 0 and pdt["delta_cadeiras"] < 0, "União e PDT perderam"
    )
    saida.append(
        _achado(
            f"8. O PL foi de {pl['cadeiras_2022']} para {pl['cadeiras_2026']} deputados; União "
            f"e PDT perderam "
            f"{-(uni['delta_cadeiras'] + pdt['delta_cadeiras'])} juntos",
            f"PL: {pl['cadeiras_2022']} para {pl['cadeiras_2026']} cadeiras e de "
            f"{dec(pl['pct_votos_2022'])}% para {dec(pl['pct_votos_2026'])}% dos votos de "
            f"partido ({pts(pl['delta_pct_votos_pp'], 2, True)}). União: "
            f"{uni['cadeiras_2022']} para {uni['cadeiras_2026']}. PDT: {pdt['cadeiras_2022']} "
            f"para {pdt['cadeiras_2026']}. PP: {pp_['cadeiras_2022']} para "
            f"{pp_['cadeiras_2026']}. MDB: {mdb['cadeiras_2022']} para {mdb['cadeiras_2026']}. "
            f"Podemos, somado ao PSC que incorporou: {pode['cadeiras_2022']} para "
            f"{pode['cadeiras_2026']}. Novo: {novo['cadeiras_2022']} para "
            f"{novo['cadeiras_2026']}.",
            "verificado; as somas de 2022 seguem a tabela de sucessores (PSC no Podemos, "
            "PTB e Patriota no PRD, PROS no Solidariedade)",
            f"{jp} → camara.partidos",
        )
    )
    pr = cam["proporcionalidade"]
    lc22 = {x["chave"]: x for x in pr["campos_2022"]["linhas"]}
    lc26 = {x["chave"]: x for x in pr["campos_2026"]["linhas"]}
    sobra = {k: v["cadeiras_menos_votos_pp"] for k, v in lc26.items()}
    _exige(
        sobra["direita"] < lc22["direita"]["cadeiras_menos_votos_pp"],
        "sobrerrepresentação da direita caiu",
    )
    _exige(
        max(sobra, key=sobra.__getitem__) == "centro-direita",
        "prêmio com a centro-direita",
    )
    _exige(sobra["esquerda"] < 0, "esquerda abaixo do próprio voto")
    saida.append(
        _achado(
            f"9. Cadeiras contra votos: a sobra de cadeiras da direita caiu de "
            f"{dec(lc22['direita']['cadeiras_menos_votos_pp'], 2, True)} para "
            f"{pts(sobra['direita'], 2, True)}",
            f"A direita foi de {dec(lc22['direita']['pct_votos'])}% para "
            f"{dec(lc26['direita']['pct_votos'])}% dos votos de partido na Câmara e de "
            f"{dec(lc22['direita']['pct_cadeiras'])}% para {dec(lc26['direita']['pct_cadeiras'])}% "
            f"das cadeiras. A fatia de cadeiras menos a de votos da direita era de "
            f"{pts(lc22['direita']['cadeiras_menos_votos_pp'], 2, True)} em 2022 e de "
            f"{pts(lc26['direita']['cadeiras_menos_votos_pp'], 2, True)} em 2026. O prêmio de 2026 "
            f"ficou com a centro-direita ({dec(lc26['centro-direita']['cadeiras_menos_votos_pp'], 2, True)}); "
            f"a esquerda fica {pts(-lc26['esquerda']['cadeiras_menos_votos_pp'])} abaixo do "
            f"próprio voto. Votos por cadeira em 2026: esquerda "
            f"{mil(lc26['esquerda']['votos_por_cadeira'])}, direita "
            f"{mil(lc26['direita']['votos_por_cadeira'])}, centro-direita "
            f"{mil(lc26['centro-direita']['votos_por_cadeira'])}. Índice de Gallagher por "
            f"partido: {dec(pr['partidos_2022']['gallagher_pp'])} em 2022 e "
            f"{dec(pr['partidos_2026']['gallagher_pp'])} em 2026.",
            "verificado sob classificação editorial; votos somados no país contra cadeiras "
            "distribuídas por UF; 2022 sem a legenda do MA (ausente do pacote do TSE)",
            f"{jp} → camara.proporcionalidade",
        )
    )
    s23, s27 = sen["senado_2023"], sen["senado_2027"]
    k18, k26 = sen["classe_2018_composicao"], sen["classe_2026_composicao"]
    sens = sen["sensibilidade_psl_2018_direita"]["senado_2023"]
    _exige(
        k26["por_bloco"][EC] < k18["por_bloco"][EC], "esquerda e centro-esquerda caíram"
    )
    atinge = s27["direita_mais_cd_atinge"]
    faixa = (
        f"{'acima' if atinge['tres_quintos'] else 'abaixo'} de 49 (três quintos), "
        f"{'acima' if atinge['dois_tercos'] else 'abaixo'} de 54 (dois terços)"
    )
    bloco_psl = (
        "o bloco não muda"
        if sens["por_bloco"] == s23["por_bloco"]
        else f"o bloco vai a {sens['por_bloco'][DC]}"
    )
    k18_psl = sen["sensibilidade_psl_2018_direita"]["classe_2018"]
    teto_sen = sen["sensibilidade_teto_direita"]
    saida.append(
        _achado(
            f"10. Senado: nas {k18['total']} vagas renovadas, o bloco à direita foi de "
            f"{k18['por_bloco'][DC]} para {k26['por_bloco'][DC]}",
            f"Na urna de 2018, as {k18['total']} vagas renovadas agora deram "
            f"{k18['por_bloco'][DC]} cadeiras ao bloco de direita e centro-direita, "
            f"{k18['por_campo']['direita']} delas de direita "
            f"({k18_psl['por_campo']['direita']} se o PSL de 2018 contar como direita); "
            f"em 2026 são {k26['por_bloco'][DC]} e {k26['por_campo']['direita']}. Esquerda "
            f"e centro-esquerda caíram de {k18['por_bloco'][EC]} para "
            f"{k26['por_bloco'][EC]}. Somando os {sen['classe_2022_composicao']['total']} "
            f"eleitos de 2022, o Senado eleito de 2023 tinha {s23['por_bloco'][DC]} cadeiras "
            f"de direita e centro-direita e o de 2027 terá {s27['por_bloco'][DC]}: {faixa}. "
            f"Direita {s23['por_campo']['direita']} para {s27['por_campo']['direita']} "
            f"({sens['por_campo']['direita']} para {s27['por_campo']['direita']} com o PSL "
            f"de 2018 como direita, e {bloco_psl}); PL {s23['por_partido'].get('PL', 0)} "
            f"para {s27['por_partido'].get('PL', 0)}. No teto da direita de 2018 (toda "
            f"sigla extinta que a regra leva à centro-direita contada como direita), a "
            f"classe de 2018 teria {teto_sen['classe_2018']['por_campo']['direita']} "
            f"senadores de direita e o Senado de 2023, "
            f"{teto_sen['senado_2023']['por_campo']['direita']}. Foram reeleitos "
            f"{len(sen['reeleitos_2018_2026'])} dos senadores eleitos em 2018.",
            "verificado sob classificação editorial; eleitos da urna, não titulares (MT "
            "pela suplementar de 2020); a composição de 2023 é a da urna, não a da posse",
            f"{jp} → senado.classe_2018_composicao, senado.senado_2023, senado.senado_2027",
        )
    )
    fx = gov["fluxo_bloco_decididos"]
    saiu_ec = sum(v for k, v in fx[EC].items() if k != EC)
    entrou_dc = sum(fx[k][DC] for k in fx if k != DC)
    saiu_dc = sum(v for k, v in fx[DC].items() if k != DC)
    definidos = gov["abertos_bloco_definido"]
    certos = gov["abertos_mudam_bloco_com_certeza"]
    frase_certos = (
        f" Em {lista(certos)}, nenhum finalista é do bloco do governador eleito em "
        "2022: a troca de bloco já é certa."
        if certos
        else ""
    )
    frase_definidos = (
        "os dois finalistas são do mesmo bloco em "
        + lista(f"{uf} ({NOMES_BLOCO[b]})" for uf, b in definidos.items())
        if definidos
        else "nenhum tem os dois finalistas no mesmo bloco"
    )
    saida.append(
        _achado(
            f"11. Governadores: {len(gov['decididos_mudaram_bloco'])} dos "
            f"{gov['decididos_2026']} eleitos no 1º turno são de outro bloco",
            f"Dos {gov['decididos_2026']} governadores eleitos no 1º turno de 2026, "
            f"{len(gov['decididos_mudaram_bloco'])} são de bloco diferente do vencedor de "
            f"2022 ({lista(gov['decididos_mudaram_bloco'])}); em "
            f"{lista(gov['decididos_mudaram_bloco_mesma_pessoa'])} é o mesmo governador, que "
            f"trocou de partido. Esquerda e centro-esquerda perderam {saiu_ec} desses "
            f"estados; direita e centro-direita ganharam {entrou_dc} e perderam {saiu_dc}. "
            f"Foram reeleitos {len(gov['decididos_mesma_pessoa'])} governadores "
            f"({lista(gov['decididos_mesma_pessoa'])}), e {len(gov['decididos_mesmo_partido'])} "
            f"estados mantiveram o partido. Em 2022 o placar final foi "
            f"{gov['por_bloco_2022'][EC]} estados para esquerda e centro-esquerda, "
            f"{gov['por_bloco_2022']['centro']} para o centro e {gov['por_bloco_2022'][DC]} "
            f"para direita e centro-direita. Das {gov['segundo_turno_2026']} disputas de 2º "
            f"turno de 2026, {frase_definidos}.{frase_certos}",
            "verificado sob classificação editorial; reeleição pelo nome completo igual",
            f"{jp} → governadores",
        )
    )
    a22, a26 = ass["por_campo_2022"], ass["por_campo_2026"]
    teto_ass = ass["sensibilidade_teto_direita_2022"]
    queda = ass["por_bloco_2026"][EC] - ass["por_bloco_2022"][EC]
    _exige(queda < 0, "esquerda e centro-esquerda caíram nas assembleias")
    d_ce = a26["centro-esquerda"] - a22["centro-esquerda"]
    origem = (
        "toda a queda veio da centro-esquerda"
        if a26["esquerda"] >= a22["esquerda"]
        else f"a centro-esquerda respondeu por {dec(100 * d_ce / queda, 0)}% da queda"
    )
    saida.append(
        _achado(
            f"12. Nas {len(c['assembleias']['casas'])} assembleias comparadas, a direita somou "
            f"{a26['direita'] - a22['direita']} cadeiras",
            f"Nas {len(c['assembleias']['casas'])} casas comparadas ({ass['vagas']} vagas), a "
            f"direita foi de {a22['direita']} para {a26['direita']} e a centro-direita de "
            f"{a22['centro-direita']} para {a26['centro-direita']}; o bloco de direita e "
            f"centro-direita, de {ass['por_bloco_2022'][DC]} para {ass['por_bloco_2026'][DC]}. "
            f"Esquerda e centro-esquerda caíram de {ass['por_bloco_2022'][EC]} para "
            f"{ass['por_bloco_2026'][EC]}, e {origem} "
            f"({a22['centro-esquerda']} para {a26['centro-esquerda']}); a esquerda foi de "
            f"{a22['esquerda']} para {a26['esquerda']}. No teto da direita de 2022 (siglas "
            f"extintas levadas à centro-direita contadas como direita: "
            f"{lista(f'{k} {v}' for k, v in teto_ass['siglas'].items())}), o ganho da "
            f"direita é de {mil(teto_ass['delta_campo']['direita'], True)}.",
            "verificado sob classificação editorial; 2026 provisório em "
            + lista(
                x["uf"] for x in c["assembleias"]["casas"] if x["fonte_2026"] != "tse"
            ),
            f"{jp} → assembleias.onze_casas",
        )
    )
    return saida


def tabela_partidos(c: dict[str, Any]) -> str:
    linhas = [
        "| Sigla antiga | Anos | Nº | Sigla de 2026 | Tipo | Campo usado | Evidência |",
        "|---|---|---|---|---|---|---|",
    ]
    for p in c["partidos"]["siglas_2018_2022"]:
        if "tipo" not in p:
            continue
        evid = (
            "número confirmado no banco de 2026"
            if p["confirmado_pelo_numero"]
            else "fato público, sem documento no repositório"
        )
        linhas.append(
            f"| {p['sigla']} | {', '.join(str(a) for a in p['anos'])} | "
            f"{', '.join(str(n) for n in p['numeros'])} | {p['sigla_2026']} | {p['tipo']} | "
            f"{p['campo']} ({p['via_campo']}) | {evid} |"
        )
    return "\n".join(linhas) + "\n"


def outros_numeros(c: dict[str, Any]) -> str:
    cam = c["camara"]
    ren = cam["renovacao"]
    sen = c["senado"]
    gov = c["governadores"]
    sup = gov["suplementar_governador"]
    total = ren["reeleitos"] + ren["novos"]
    itens = [
        f"Renovação da Câmara: {ren['reeleitos']} dos {total} eleitos em 2026 também foram "
        f"eleitos em 2022 ({dec(100 * ren['reeleitos'] / total, 1)}%), pelo nome completo "
        "igual na mesma UF (inferido: casamento de nomes).",
        "Senadores eleitos em 2018 reeleitos em 2026: "
        + lista(
            "{} ({})".format(x["nome"], x["uf"]) for x in sen["reeleitos_2018_2026"]
        )
        + ".",
        f"Votos de partido na Câmara: {mil(cam['votos_totais_2022'])} em 2022 (sem a legenda "
        f"do MA) e {mil(cam['votos_totais_2026'])} em 2026.",
    ]
    if sup:
        itens.append(
            f"O pacote de 2022 do TSE traz a eleição suplementar para governador de "
            f"{sup[0]['uf']} de {sup[0]['data']}; nenhuma das {len(sup)} candidaturas aparece "
            "como eleita no arquivo. A comparação usa a eleição ordinária de 2022."
        )
    return "\n".join(f"- {x}" for x in itens) + "\n"


def escrever(c: dict[str, Any]) -> str:
    meta = c["meta"]
    partes = [
        "# Apuração de 2026 contra 2022: os doze achados\n",
        f"Gerado por `{meta['script']}` em {meta['gerado_em']}, com o boletim final de "
        f"{meta['final_json_gerado_em']}. Dados completos em "
        "`analysis/apuracao_2026/dados/comparacao_2022.json`. Nenhum número deste texto foi "
        "digitado: todos saem do JSON.\n",
        "## Achados\n",
        *achados(c),
        "## Outros números\n",
        outros_numeros(c),
        "## Pressupostos e lacunas\n",
        "\n".join(f"- {p}" for p in c["pressupostos"]) + "\n",
        "## Tabela de partidos assumida\n",
        "A tabela da casa (`apuracao/public/campos.json`) vence quando lista a sigla "
        "antiga (`direto`); senão vale o campo do sucessor de 2026 (`sucessor`). A coluna "
        "de evidência diz se o número do partido antigo aparece com a sigla sucessora no "
        "banco de 2026 ou se a sucessão é fato público de registro partidário sem "
        "documento arquivado aqui.\n",
        tabela_partidos(c),
    ]
    return "\n".join(partes)
