"""Texto do capítulo "O caminho do 2º turno", gerado do JSON da estratégia.

Nenhum número é digitado aqui: todos saem de ``dados`` (o mesmo dicionário
gravado em ``analysis/apuracao_2026/dados/estrategia_2t.json``). A prosa fixa
carrega só método, rótulo e juízo editorial declarado; frases que dependem do
dado (quem passou de quem, quantas UFs, qual lado) são escolhidas pelo dado.

Regras de escrita da casa: sem travessão, frase curta, número ao lado de cada
movimento, rótulo explícito (Verificado, Inferência, Hipótese, Analogia,
Juízo editorial).
"""

from __future__ import annotations

from .estrategia import milhar
from .estrategia_formato import (
    FRASE_HIPOTESE,
    FRASE_MATRIZ,
    MENOS,
    ROTULO_HIPOTESE,
    ROTULO_MATRIZ,
    UF_NOME,
    acima_abaixo,
    dec,
    extenso,
    faixa_milhoes,
    hora_br,
    lista_e,
    nome,
    pc,
    pontos,
    qtd,
    sinal,
    sinal_votos,
    tabela,
)


def _proj(dados: dict, matriz: str, hipotese: str) -> dict:
    return next(
        p
        for p in dados["aritmetica"]["projecoes"]
        if p["matriz"] == matriz and p["hipotese"] == hipotese
    )


# ---------------------------------------------------------------- abertura


def abertura(dados: dict) -> str:
    a = dados["aritmetica"]
    p1 = a["primeiro_turno"]
    eq = a["equilibrio"]
    geo = dados["geografia"]
    risc = dados["riscos"]
    c = _proj(dados, "nexus", "fica_fora")
    melhor = max(a["projecoes"], key=lambda p: p["margem_votos"])
    cs = geo["regioes"]["Centro-Sul"]
    comp = risc["comparecimento"]["regioes"]
    d_cs = comp["Centro-Sul"]["diferenca_2026_menos_2022_1t_pp"]
    d_ne = comp["Nordeste"]["diferenca_2026_menos_2022_1t_pp"]
    contra = d_cs < 0 < d_ne
    parcela_cs = 100 * cs["estoque_flavio_soma_ufs"] / geo["estoque"]["total_ufs"]
    toda = eq["nao_escolha_toda_para_lula"]["nexus"]
    razao = risc["estoque_lula_maior"]["razao"]
    return f"""# O caminho do 2º turno

Capítulo estratégico do dossiê da apuração do 1º turno de 2026. A casa tem lado: o projeto é a vitória de Flávio Bolsonaro em 25/10. O método não tem lado: cada movimento sai com número e fonte, e o achado que contraria a tese sai com o mesmo peso.

Números de 2026: banco da apuração (`apuracao/data/apuracao.sqlite`), arquivo nacional de presidente gerado pelo TSE em {hora_br(p1["gerado_em_tse"])} ({milhar(p1["secoes_totalizadas"])} de {milhar(p1["secoes"])} seções) e lido pelo coletor em {hora_br(p1["capturado_em"])}, horário de Brasília. Números de 2022: arquivos do TSE em `data/raw/tse_resultados/api_2022/` e a tabela municipal `data/outputs/estaduais2026/municipios.csv`. Tudo se reproduz com `python3 scripts/apuracao-2026-estrategia.py`, que grava `analysis/apuracao_2026/dados/estrategia_2t.json`.

Rótulos: **Verificado** é número da urna ou de documento arquivado. **Inferência** é conta sobre medição publicada. **Hipótese** é suposição declarada, que pode estar errada. **Analogia** é o que aconteceu em 2022, uma eleição só. **Juízo editorial** é opinião da casa.

## Em cinco linhas

1. **Verificado.** Flávio sai do 1º turno com {qtd(p1["diferenca_votos"])} de vantagem, {pontos(p1["diferenca_pp"])} dos válidos ({pc(p1["flavio_pct"])} contra {pc(p1["lula_pct"])}).
2. **Inferência.** A matriz de transferência da Nexus aplicada aos {qtd(p1["terceiros_total"])} de terceira via leva Flávio a {pc(c["flavio_pct"])} dos válidos só com o que foi medido. Na leitura mais favorável a ele, {FRASE_MATRIZ[melhor["matriz"]]} e {FRASE_HIPOTESE[melhor["hipotese"]]}, a {pc(melhor["flavio_pct"])}.
3. **Inferência.** Para virar só com a terceira via, Lula precisaria de {pc(eq["lula_precisa_se_todos_votarem_pct"])} de todos esses votos. A Nexus mede {pc(eq["lula_medido_entre_quem_escolhe_pct"])} entre os que escolhem. Mesmo que toda a não escolha da terceira via fosse para Lula, Flávio ainda teria {qtd(toda["margem_flavio_se_toda_for_lula"])} de vantagem.
4. **Inferência.** O risco maior não está na transferência. Está na base e no comparecimento: se {pc(eq["base_flavio_trocando_para_lula_pct"])} da base de Flávio trocar de lado, a margem central some. Contra o 1º turno de 2022, o comparecimento de 2026 variou {sinal(d_cs)} ponto no Centro-Sul e {sinal(d_ne)} no Nordeste{", a direção errada para Flávio" if contra else ""}.
5. **Inferência.** O estoque de 2022 que Flávio ainda não alcançou soma {qtd(geo["estoque"]["total_ufs"])} e está {dec(parcela_cs, 0)}% no Centro-Sul. O de Lula é {dec(razao)} vezes {"maior" if razao > 1 else "menor"}: {"quem tem mais eleitor de 2022 para buscar é Lula" if razao > 1 else "quem tem mais eleitor de 2022 para buscar é Flávio"}.
"""


# ---------------------------------------------------------------- 1. aritmética


def _tabela_terceiros(p1: dict) -> tuple[str, list[dict]]:
    terc = p1["terceiros"]
    principais = [t for t in terc if t["linha_propria"] and t["numero"] != 80]
    demais = [t for t in terc if t not in principais]
    sem_linha = [t for t in terc if not t["linha_propria"]]
    linhas = [
        [nome(t["nome"]), t["partido"], milhar(t["votos"]), pc(t["pct"]), t["linha"]]
        for t in principais
    ]
    linhas.append(
        [
            f"Demais {extenso(len(demais), True)} candidaturas",
            ", ".join(t["partido"] for t in demais),
            milhar(sum(t["votos"] for t in demais)),
            pc(sum(t["pct"] for t in demais)),
            "própria (Samara) ou do mesmo campo",
        ]
    )
    linhas.append(
        [
            "**Total**",
            "",
            f"**{milhar(p1['terceiros_total'])}**",
            f"**{pc(p1['terceiros_pct'])}**",
            "",
        ]
    )
    cab = ["Candidatura", "Partido", "Votos", "Válidos", "Linha da matriz"]
    return tabela(cab, linhas), sem_linha


def _tabela_matriz(mats: dict) -> str:
    nx = mats["nexus"]["linhas_publicadas"]
    dfm = mats["datafolha"]["linhas_publicadas"]
    linhas = []
    for k, v in nx.items():
        outros = sum(x for c, x in v.items() if c not in ("Lula", "Flávio"))
        linha = [k, f"{v['Flávio']:g}", f"{v['Lula']:g}", f"{outros:g}"]
        linha.append(f"{sum(v.values()):g}")
        if k in dfm:
            d = dfm[k]
            linha.append(
                f"{d['Flávio']:g} × {d['Lula']:g}, não escolha {d['Não escolha']:g}"
            )
        else:
            linha.append("sem linha")
        linhas.append(linha)
    cab = [
        "Eleitorado de",
        "Flávio",
        "Lula",
        "Branco, nulo ou indeciso",
        "Soma",
        "Datafolha (Flávio × Lula)",
    ]
    return tabela(cab, linhas)


def secao_aritmetica(dados: dict) -> str:
    a = dados["aritmetica"]
    p1 = a["primeiro_turno"]
    eq = a["equilibrio"]
    mats = a["matrizes"]
    tab_terc, sem_linha = _tabela_terceiros(p1)
    nomes_sem = lista_e(
        [
            f"{nome(t['nome'])} ({t['partido']}, linha de {t['linha']})"
            for t in sem_linha
        ]
    )
    linhas_p = [
        [
            ROTULO_MATRIZ[p["matriz"]],
            ROTULO_HIPOTESE[p["hipotese"]],
            pc(p["flavio_pct"]),
            pc(p["lula_pct"]),
            sinal_votos(p["margem_votos"]),
            sinal(p["margem_pp"]),
        ]
        for p in a["projecoes"]
    ]
    c = _proj(dados, "nexus", "fica_fora")
    novos = next(
        x
        for x in eq["eleitores_novos_para_empatar"]
        if x["matriz"] == "nexus" and x["hipotese"] == "fica_fora"
    )
    an = a["analogo_2022"]
    et = an["entre_turnos_2022"]
    toda = eq["nao_escolha_toda_para_lula"]
    saldos = sorted(c["detalhe"], key=lambda d: -d["saldo_flavio"])
    maior, menor = saldos[0], saldos[-1]
    margens = [p["margem_votos"] for p in a["projecoes"]]
    todas_flavio = all(m > 0 for m in margens)
    juizo = (
        "A aritmética favorece Flávio por uma margem que nenhuma das seis "
        f"combinações de matriz e hipótese desfaz ({faixa_milhoes(min(margens), max(margens))}). "
        "A campanha de Flávio é de defesa: segurar a base, colher o que as linhas "
        "já mediram e não perder comparecimento. A de Lula precisa mudar as linhas "
        "medidas ou trazer eleitor novo em escala que 2022 não mostrou."
        if todas_flavio
        else "Ao menos uma combinação de matriz e hipótese vira a margem: a "
        "transferência decide a eleição e é ela que a campanha precisa medir."
    )
    return f"""
## 1. A aritmética do 2º turno

**Verificado.** Eleitorado de {milhar(p1["eleitores"])}. Compareceram {milhar(p1["comparecimento"])} ({pc(p1["comparecimento_pct"])}); faltaram {milhar(p1["abstencao"])} ({pc(p1["abstencao_pct"])}). Brancos e nulos somaram {milhar(p1["brancos"] + p1["nulos"])}, {pc(p1["brancos_nulos_pct_comparecimento"])} de quem foi votar. Dos {milhar(p1["validos"])} votos válidos, Flávio teve {milhar(p1["flavio"])} ({pc(p1["flavio_pct"])}) e Lula {milhar(p1["lula"])} ({pc(p1["lula_pct"])}). Diferença: {milhar(p1["diferenca_votos"])} votos.

O 2º turno começa nos {milhar(p1["terceiros_total"])} votos dados às outras candidaturas:

{tab_terc}

**Inferência.** No acervo da casa, a única matriz com uma linha para cada candidatura de terceira via é a da {mats["nexus"]["fonte"]} (`{mats["nexus"]["arquivo"]}`). O Datafolha publicou duas linhas no texto do relatório nacional ({mats["datafolha"]["fonte"]}; `{mats["datafolha"]["arquivo"]}`), para Cury e Caiado; na matriz "Datafolha" as demais linhas vêm da Nexus. Cada linha diz, entre os eleitores de uma candidatura, quantos votariam em Flávio, em Lula ou em nenhum dos dois:

{_tabela_matriz(mats)}

As linhas somam 99 ou 101 por arredondamento do instituto; a conta divide cada uma pela própria soma. As {extenso(len(sem_linha), True)} candidaturas sem linha publicada recebem a linha da candidatura publicada do mesmo campo: {nomes_sem}. Juntas são {pc(sum(t["pct"] for t in sem_linha))} dos válidos.

**Hipóteses fixas da conta.** As bases do 1º turno ficam onde estão; branco, nulo e abstenção do 1º turno não entram; o comparecimento não muda. A única coisa que varia é o destino da parcela de cada linha que não escolheu ninguém:

- **só o medido:** essa parcela não vira voto válido;
- **proporcional:** vota na mesma proporção Flávio:Lula da própria linha;
- **meio a meio:** divide-se igualmente.

{tabela(["Matriz", "Hipótese", "Flávio", "Lula", "Margem (votos)", "Margem (pontos)"], linhas_p)}

Dividir a não escolha meio a meio não mexe na margem em votos: soma o mesmo aos dois lados e só dilui o percentual. Quem decide a margem é a parte medida das linhas. Na conta central (Nexus, só o medido), o eleitorado de {nome(maior["origem"])} entrega a Flávio o maior saldo, {milhar(maior["saldo_flavio"])} votos; o de {nome(menor["origem"])} entrega o maior saldo a Lula, {milhar(-menor["saldo_flavio"])}.

**Inferência. Ponto de equilíbrio.** Para Lula zerar a diferença do 1º turno só com a terceira via, precisaria de {pc(eq["lula_precisa_se_todos_votarem_pct"])} de todos os {qtd(p1["terceiros_total"])}, se todos votassem em alguém. Pela Nexus, só {pc(eq["terceiros_que_escolhem_nexus_pct"])} desse eleitorado escolhe um dos dois; entre eles, Lula precisaria de {pc(eq["lula_precisa_entre_quem_escolhe_pct"])}, e a medição dá {pc(eq["lula_medido_entre_quem_escolhe_pct"])}. Mesmo que toda a não escolha da terceira via ({qtd(toda["nexus"]["nao_escolha_votos"])}, pela Nexus) fosse para Lula, Flávio terminaria com {qtd(toda["nexus"]["margem_flavio_se_toda_for_lula"])} de vantagem; com as linhas do Datafolha para Cury e Caiado, {qtd(toda["datafolha"]["margem_flavio_se_toda_for_lula"])}.

**Inferência. Eleitor novo.** O caminho que sobra a Lula é trazer quem faltou. Para apagar a margem central de {qtd(c["margem_votos"])} só com eleitores que não votaram no 1º turno, seriam precisos {qtd(novos["lula_60"], "eleitores novos")} votando 60% em Lula, ou {qtd(novos["lula_70"], "eleitores novos")} votando 70%. A abstenção do 1º turno foi de {qtd(eq["abstencao_1t"], "eleitores")}. **Verificado:** em 2022 o comparecimento subiu {milhar(et["variacao_votos"])} votos entre os turnos ({sinal(et["variacao_pp"])} ponto).

**Inferência. Base.** A mesma margem central some se {pc(eq["base_flavio_trocando_para_lula_pct"])} dos eleitores de Flávio no 1º turno votarem em Lula, ou se {pc(eq["base_flavio_abstendo_pct"])} deles deixarem de votar.

**Analogia.** Em 2022, entre os turnos, Bolsonaro ganhou {milhar(et["ganho_bolsonaro"])} votos e Lula {milhar(et["ganho_lula"])}, partindo de {milhar(et["terceiros_1t"])} votos de terceira via. A diferença a favor de Lula caiu de {milhar(et["diferenca_1t"])} para {milhar(et["diferenca_2t"])}. Se cada voto de terceira via de 2026 rendesse o que rendeu em 2022 (taxas de {dec(an["nacional"]["taxa_flavio"], 4)} para Bolsonaro e {dec(an["nacional"]["taxa_lula"], 4)} para Lula, que incluem mudança de comparecimento e de branco e nulo), Flávio teria {pc(an["nacional"]["flavio_pct"])}; aplicando a taxa de cada UF à própria UF, {pc(an["por_uf"]["flavio_pct"])}. A terceira via de 2022 era outra (Simone Tebet e Ciro Gomes); a analogia mede ordem de grandeza, não destino.

**Juízo editorial.** {juizo}
"""


# ---------------------------------------------------------------- 2. geografia


def _texto_1t(g: dict) -> str:
    reg = g["regioes"]
    excecoes = [u for u in g["ufs"] if u["flavio_menos_bolsonaro_1t_pp"] <= 0]
    if not excecoes:
        fim = "e nas 27 UFs"
    elif len(excecoes) == 1:
        u = excecoes[0]
        fim = (
            f"e em 26 das 27 UFs; a exceção: {UF_NOME[u['uf']]} "
            f"({sinal(u['flavio_menos_bolsonaro_1t_pp'])})"
        )
    else:
        fim = f"e em {27 - len(excecoes)} das 27 UFs; as exceções: " + lista_e(
            [
                f"{UF_NOME[u['uf']]} ({sinal(u['flavio_menos_bolsonaro_1t_pp'])})"
                for u in excecoes
            ]
        )
    partes = [
        f"{r} {sinal(reg[r]['flavio_menos_bolsonaro_1t_pp'])}"
        for r in ("Nordeste", "Norte", "Centro-Sul")
    ]
    todas_acima = all(
        reg[r]["flavio_menos_bolsonaro_1t_pp"] > 0
        for r in ("Nordeste", "Norte", "Centro-Sul")
    )
    abre = (
        "Flávio fica acima de Bolsonaro de 2022 nas três regiões"
        if todas_acima
        else "Flávio contra Bolsonaro de 2022, por região"
    )
    lula = [
        f"{r} {sinal(reg[r]['lula_menos_lula_2022_1t_pp'])}"
        for r in ("Nordeste", "Norte", "Centro-Sul")
    ]
    lula_todas = all(
        reg[r]["lula_menos_lula_2022_1t_pp"] < 0
        for r in ("Nordeste", "Norte", "Centro-Sul")
    )
    lula_txt = (
        "Lula fica abaixo do próprio 1º turno de 2022 nas três regiões"
        if lula_todas
        else "Lula contra o próprio 1º turno de 2022"
    )
    return (
        f"**Verificado.** No 1º turno contra 1º turno, {abre} ({'; '.join(partes)}) "
        f"{fim}. {lula_txt} ({'; '.join(lula)})."
    )


def _tabela_regioes(reg: dict) -> str:
    linhas = []
    for r in ("Nordeste", "Norte", "Centro-Sul"):
        x = reg[r]
        linhas.append(
            [
                r,
                pc(x["flavio_pct"]),
                pc(x["bolsonaro_2022_1t_pct"]),
                pc(x["bolsonaro_2022_2t_pct"]),
                sinal(x["flavio_menos_bolsonaro_2t_pp"]),
                pc(x["lula_pct"]),
                pc(x["lula_2022_1t_pct"]),
                pc(x["terceiros_pct"]),
                milhar(x["estoque_flavio_soma_ufs"]),
                milhar(x["estoque_lula_soma_ufs"]),
            ]
        )
    cab = [
        "Região",
        "Flávio 2026",
        "Bolsonaro 2022, 1º t.",
        "Bolsonaro 2022, 2º t.",
        f"Flávio {MENOS} Bolsonaro 2º t. (pp)",
        "Lula 2026",
        "Lula 2022, 1º t.",
        "Terceira via 2026",
        "Estoque de Flávio",
        "Estoque de Lula",
    ]
    return tabela(cab, linhas)


def _tabela_ufs(g: dict) -> str:
    linhas = []
    for u in sorted(g["ufs"], key=lambda x: -x["estoque_flavio"]):
        linhas.append(
            [
                u["uf"],
                u["regiao"],
                pc(u["flavio_pct"]),
                pc(u["bolsonaro_2022_1t_pct"]),
                pc(u["bolsonaro_2022_2t_pct"]),
                sinal(u["flavio_menos_bolsonaro_2t_pp"]),
                sinal_votos(u["flavio_menos_bolsonaro_2t_votos"]),
                milhar(u["estoque_flavio"]),
                pc(u["lula_pct"]),
                sinal(u["lula_menos_lula_2022_1t_pp"]),
            ]
        )
    cab = [
        "UF",
        "Região",
        "Flávio 2026",
        "Bols. 2022, 1º t.",
        "Bols. 2022, 2º t.",
        f"Flávio {MENOS} Bols. 2º t. (pp)",
        f"Flávio {MENOS} Bols. 2º t. (votos)",
        "Estoque de Flávio",
        "Lula 2026",
        f"Lula {MENOS} Lula 2022, 1º t. (pp)",
    ]
    return tabela(cab, linhas)


def _juizo_nordeste(cap: dict, inte: dict) -> str:
    estoque_capitais = cap["estoque_flavio"] > inte["estoque_flavio"]
    historia_interior = inte["saldo_analogo_2026"] > cap["saldo_analogo_2026"]
    if estoque_capitais and historia_interior:
        return (
            "No Nordeste o estoque aponta para as capitais e a história aponta para "
            "o interior. A casa fica com a história, porque ela mede voto que se "
            "moveu entre turnos e o estoque mede só distância de parcela: interior "
            "primeiro, capitais como vitrine."
        )
    if historia_interior:
        return "Estoque e história apontam para o interior do Nordeste."
    if estoque_capitais:
        return "Estoque e história apontam para as capitais do Nordeste."
    return (
        "No Nordeste o estoque aponta para o interior e a história aponta para as "
        "capitais; a casa fica com a história, que mede voto que se moveu."
    )


def secao_geografia(dados: dict) -> str:
    g = dados["geografia"]
    reg = g["regioes"]
    e = g["estoque"]
    top5 = e["top_ufs"][:5]
    linhas_m = [
        [
            f"{nome(m['municipio'])} ({m['uf']})",
            pc(m["flavio_pct"]),
            pc(m["bolsonaro_2022_2t_pct"]),
            milhar(m["estoque_flavio"]),
        ]
        for m in e["top_municipios"][:15]
    ]
    ne = g["nordeste"]
    cap, inte = (
        ne["capitais_x_interior"]["capitais"],
        ne["capitais_x_interior"]["interior"],
    )
    linhas_ne = []
    for rot, x in (
        (f"Capitais ({cap['municipios']})", cap),
        (f"Interior ({milhar(inte['municipios'])})", inte),
    ):
        linhas_ne.append(
            [
                rot,
                pc(x["flavio_pct"]),
                pc(x["bolsonaro_2022_1t_pct"]),
                pc(x["bolsonaro_2022_2t_pct"]),
                pc(x["lula_pct"]),
                pc(x["lula_2022_1t_pct"]),
                sinal(x["lula_menos_lula_2022_1t_pp"]),
                sinal_votos(x["lula_menos_lula_2022_1t_votos"]),
                milhar(x["estoque_flavio"]),
            ]
        )
    quedas = "; ".join(
        f"{u['uf']} {sinal(u['lula_menos_lula_2022_1t_pp'])}"
        for u in ne["ufs_queda_lula"]
    )
    mq = "; ".join(
        f"{nome(m['municipio'])} ({m['uf']}) {sinal_votos(m['variacao_votos'])}"
        for m in ne["municipios_queda_lula_votos"][:6]
    )
    mg = "; ".join(
        f"{nome(m['municipio'])} ({m['uf']}) {sinal_votos(m['variacao_votos'])}"
        for m in ne["municipios_ganho_flavio_votos"][:6]
    )
    caps = "; ".join(
        f"{nome(m['municipio'])} {pc(m['flavio_pct'])} contra {pc(m['bolsonaro_2022_2t_pct'])}"
        for m in ne["capitais"][:5]
    )
    nordeste = reg["Nordeste"]
    passou_ne = nordeste["flavio_pct"] >= nordeste["bolsonaro_2022_2t_pct"]
    cs = reg["Centro-Sul"]
    risc = dados["riscos"]["estoque_lula_maior"]
    tpr = g["terceiros_por_regiao"]
    cury_caiado = [tpr["Cury"]["votos"], tpr["Caiado"]["votos"]]
    cury_caiado_cs = (
        100
        * sum(v["Centro-Sul"] for v in cury_caiado)
        / sum(sum(v.values()) for v in cury_caiado)
    )
    lula_cs = 100 * reg["Centro-Sul"]["estoque_lula_soma_ufs"] / e["total_lula_ufs"]
    queda_interior = (
        inte["lula_menos_lula_2022_1t_pp"] < cap["lula_menos_lula_2022_1t_pp"]
    )
    return f"""
## 2. Onde está o voto

Comparação de 2026 com 2022 por região: Nordeste (9 UFs), Norte (7) e Centro-Sul (Sudeste, Sul e Centro-Oeste com o DF, 11). Parcelas dos válidos de cada turno; o exterior fica à parte.

{_tabela_regioes(reg)}

{_texto_1t(g)}

**Verificado.** Em {extenso(len(g["ja_supera_bolsonaro_2t"]), True)} UFs o 1º turno de Flávio já passou a parcela de Bolsonaro no 2º turno de 2022: {lista_e(g["ja_supera_bolsonaro_2t"])}. No Nordeste como um todo, {"também" if passou_ne else "ainda não"}: {pc(nordeste["flavio_pct"])} contra {pc(nordeste["bolsonaro_2022_2t_pct"])}. No Centro-Sul, Flávio está {pontos(cs["flavio_menos_bolsonaro_2t_pp"])} {acima_abaixo(cs["flavio_menos_bolsonaro_2t_pp"])} do 2º turno de Bolsonaro, e foi ali que a terceira via teve mais voto: {pc(cs["terceiros_pct"])} dos válidos, contra {pc(nordeste["terceiros_pct"])} no Nordeste e {pc(reg["Norte"]["terceiros_pct"])} no Norte.

### O estoque de 2022

**Método.** {g["metodo_estoque"]}

**Inferência.** O estoque de Flávio soma {milhar(e["total_ufs"])} votos pelas UFs. Cinco UFs guardam {pc(e["top5_ufs_parcela_pct"])}: {lista_e([f"{x['uf']} {milhar(x['estoque_flavio'])}" for x in top5])}. Município a município, o estoque soma {milhar(e["total_municipios"])}; as capitais guardam {pc(e["capitais_pct"])} dele e os 20 maiores estoques municipais, {pc(e["top20_municipios_parcela_pct"])}.

{_tabela_ufs(g)}

Os municípios com maior estoque:

{tabela(["Município", "Flávio 2026", "Bolsonaro 2022, 2º t.", "Estoque"], linhas_m)}

**Achado contrário.** O mesmo cálculo com Lula de 2022 dá {milhar(e["total_lula_ufs"])} votos, {dec(risc["razao"])} vezes o de Flávio. Lula está {pontos(risc["lula_2022_2t_pct"] - risc["lula_2026_pct"])} abaixo do próprio 2º turno de 2022; Flávio, {pontos(risc["bolsonaro_2022_2t_pct"] - risc["flavio_2026_pct"])} abaixo do de Bolsonaro. O estoque de Lula está {dec(lula_cs, 0)}% no Centro-Sul, onde estão {dec(cury_caiado_cs, 0)}% dos votos de Cury e Caiado. E recuperar o estoque de Bolsonaro não basta: Bolsonaro perdeu com ele, com {pc(risc["bolsonaro_2022_2t_pct"])} dos válidos.

### Nordeste: capitais e interior

{tabela(["Grupo", "Flávio 2026", "Bols. 2022, 1º t.", "Bols. 2022, 2º t.", "Lula 2026", "Lula 2022, 1º t.", "Lula, variação (pp)", "Lula, variação (votos)", "Estoque de Flávio"], linhas_ne)}

**Verificado.** {"A queda de Lula no Nordeste é do interior" if queda_interior else "A queda de Lula no Nordeste é maior nas capitais"}: {sinal(inte["lula_menos_lula_2022_1t_pp"])} pontos no interior contra {sinal(cap["lula_menos_lula_2022_1t_pp"])} nas capitais. Flávio varia {sinal(inte["flavio_menos_bolsonaro_1t_pp"])} pontos no interior e {sinal(cap["flavio_menos_bolsonaro_1t_pp"])} nas capitais, sobre Bolsonaro no 1º turno de 2022. Lula contra o próprio 1º turno de 2022, por UF: {quedas}.

**Verificado.** Onde Lula perdeu mais votos contra o 1º turno de 2022: {mq}. Onde Flávio mais ganhou sobre Bolsonaro no 1º turno: {mg}.

**Inferência.** No interior, Flávio {"já passou" if inte["flavio_pct"] >= inte["bolsonaro_2022_2t_pct"] else "ainda não alcançou"} o 2º turno de Bolsonaro ({pc(inte["flavio_pct"])} contra {pc(inte["bolsonaro_2022_2t_pct"])}); nas capitais, {"já passou" if cap["flavio_pct"] >= cap["bolsonaro_2022_2t_pct"] else "ainda não"} ({pc(cap["flavio_pct"])} contra {pc(cap["bolsonaro_2022_2t_pct"])}). O estoque nordestino soma {milhar(cap["estoque_flavio"])} nas capitais e {milhar(inte["estoque_flavio"])} no interior. Capitais com maior estoque: {caps}.

**Analogia.** Em 2022, entre os turnos, o saldo de Bolsonaro sobre Lula foi de {milhar(cap["saldo_bolsonaro_entre_turnos_2022"])} votos nas capitais nordestinas e de {milhar(inte["saldo_bolsonaro_entre_turnos_2022"])} no interior; por voto de terceira via do 1º turno, {dec(cap["taxa_saldo_2022_por_terceiro"], 4)} e {dec(inte["taxa_saldo_2022_por_terceiro"], 4)}. Aplicado à terceira via de 2026, o interior rende {milhar(inte["saldo_analogo_2026"])} votos e as capitais {milhar(cap["saldo_analogo_2026"])}.

**Juízo editorial.** {_juizo_nordeste(cap, inte)}
"""


# ---------------------------------------------------------------- 3. governadores


def _tabela_aliados(gv: dict) -> str:
    linhas = []
    for a in gv["aliados"]:
        rot = nome(a["governador"])
        if a["alinhado_lula"]:
            rot += " (aliado de Lula)"
        top = a["top_municipios"][0] if a["top_municipios"] else None
        linhas.append(
            [
                a["uf"],
                rot,
                f"{a['partido']}, {a['campo']}",
                milhar(a["governador_votos"]),
                pc(a["governador_pct"]),
                milhar(a["flavio_votos"]),
                pc(a["flavio_pct"]),
                sinal(a["vao_pp"]),
                sinal_votos(a["vao_votos"]),
                (
                    f"{nome(top['municipio'])} {sinal_votos(top['vao_votos'])}"
                    if top and top["vao_votos"] > 0
                    else "nenhum"
                ),
            ]
        )
    cab = [
        "UF",
        "Governador",
        "Partido e campo",
        "Votos",
        "% válidos (gov.)",
        "Flávio",
        "% válidos (pres.)",
        "Vão (pp)",
        "Vão (votos)",
        "Município de maior vão",
    ]
    return tabela(cab, linhas)


def _linhas_datafolha(gv: dict) -> str:
    ln = {(x["uf"], x["turno"]): x for x in gv["linhas_datafolha"] if x["uf"] == "SP"}
    sp1 = ln[("SP", "1t")]
    cons = {c["origem"].split(" (")[0]: c for c in gv["consolidacao_medida"]}
    mg = cons["Cleitinho Azevedo"]
    ruas = cons["Douglas Ruas"]
    paes = cons["Eduardo Paes"]
    sp = next(a for a in gv["aliados"] if a["uf"] == "SP")
    tarc_lula = round(sp["governador_votos"] * sp1["Lula"] / 100)
    cury = next((v for k, v in sp1.items() if "Cury" in k), None)
    cury_txt = f", Cury {cury}%" if cury is not None else ""
    comp = "mais" if tarc_lula > sp["vao_votos"] else "menos"
    return f"""- **SP, p. {sp1["pagina"]}:** entre os eleitores de Tarcísio, Flávio {sp1["Flávio"]}%, Lula {sp1["Lula"]}%{cury_txt} no 1º turno. Aplicada aos {milhar(sp["governador_votos"])} votos de Tarcísio, a linha de Lula daria {milhar(tarc_lula)} eleitores de Tarcísio com Lula, {comp} que o vão bruto de {milhar(sp["vao_votos"])}. Ordem de grandeza, não medição da urna: a linha é de setembro.
- **MG, pp. {mg["paginas"][0]} e {mg["paginas"][1]}:** eleitores de Cleitinho, Flávio {mg["linha_1t"]["Flávio"]} → {mg["linha_2t"]["Flávio"]} e Lula {mg["linha_1t"]["Lula"]} → {mg["linha_2t"]["Lula"]} do 1º para o 2º turno. Saldo de {sinal(mg["saldo_flavio_pontos"], 0)} pontos para Flávio; sobre a urna de Cleitinho, {sinal_votos(mg["saldo_aplicado_a_urna"])} votos. Os {mg["linha_2t"]["Lula"]}% com Lula no 2º turno equivalem a {milhar(mg["lula_2t_aplicado_a_urna"])} eleitores de Cleitinho.
- **RJ, pp. {ruas["paginas"][0]} e {ruas["paginas"][1]}:** eleitores de Douglas Ruas, Flávio {ruas["linha_1t"]["Flávio"]} → {ruas["linha_2t"]["Flávio"]} e Lula {ruas["linha_1t"]["Lula"]} → {ruas["linha_2t"]["Lula"]} (saldo de {sinal(ruas["saldo_flavio_pontos"], 0)} pontos; {sinal_votos(ruas["saldo_aplicado_a_urna"])} votos). **Achado contrário:** eleitores de Eduardo Paes, Flávio {paes["linha_1t"]["Flávio"]} → {paes["linha_2t"]["Flávio"]} e Lula {paes["linha_1t"]["Lula"]} → {paes["linha_2t"]["Lula"]} (saldo de {sinal(paes["saldo_flavio_pontos"], 0)} pontos; {sinal_votos(paes["saldo_aplicado_a_urna"])} votos)."""


def _juizo_segundo_turno(disputas: list[dict]) -> str:
    """Leitura dos 2º turnos estaduais a partir do lado de cada finalista."""
    polarizadas = [d for d in disputas if d["tipo"] == "flavio+lula"]
    favoraveis = [d for d in polarizadas if d["margem_flavio_votos"] > 0]
    adversas = [d for d in polarizadas if d["margem_flavio_votos"] <= 0]
    mesmo_lado = [d for d in disputas if d["tipo"] in ("flavio", "lula")]
    outras = [d for d in disputas if d not in polarizadas and d not in mesmo_lado]
    frases = []
    if favoraveis:
        maior = max(favoraveis, key=lambda d: d["eleitores"])
        frases.append(
            f"A arena que mais pesa é a disputa do {maior['uf']}: {milhar(maior['eleitores'])} "
            f"eleitores, Flávio {sinal_votos(maior['margem_flavio_votos'])} votos no "
            "1º turno e um finalista da direita ou da centro-direita contra um da "
            "esquerda, da centro-esquerda ou aliado de Lula."
        )
        resto = [d["uf"] for d in favoraveis if d is not maior]
        if resto:
            frases.append(
                f"{lista_e(resto)} repetem o desenho em escala menor, também em UFs "
                "que Flávio venceu."
            )
    if adversas:
        frases.append(
            f"Em {lista_e([d['uf'] for d in adversas])} o desenho é o mesmo, mas Lula "
            "venceu a UF: a disputa estadual mobiliza o eleitor do outro lado também."
        )
    if mesmo_lado:
        frases.append(
            f"Em {lista_e([d['uf'] for d in mesmo_lado])} os dois finalistas são do "
            "mesmo bloco: não há polarização a explorar."
        )
    if outras:
        frases.append(
            f"Em {lista_e([d['uf'] for d in outras])} um dos finalistas é do centro."
        )
    return " ".join(frases)


def secao_governadores(dados: dict) -> str:
    gv = dados["governadores"]
    por_uf = {a["uf"]: a for a in gv["aliados"]}
    sem_voto = [a for a in gv["aliados"] if a["vao_votos"] < 0]
    sem_voto_txt = lista_e(
        [
            f"{a['uf']} ({nome(a['governador'])}, {sinal_votos(a['vao_votos'])})"
            for a in sem_voto
        ]
    )
    divergem = [a for a in gv["aliados"] if a["vao_pp"] > 0 > a["vao_votos"]]
    divergem_txt = (
        f" Em {lista_e([a['uf'] for a in divergem])} o governador tem parcela maior e "
        "menos votos que Flávio porque a eleição de governador teve menos votos "
        "válidos na mesma urna ("
        + "; ".join(
            f"{a['uf']}: {milhar(a['validos_governador'])} contra {milhar(a['validos_presidente'])}"
            for a in divergem
        )
        + ")."
        if divergem
        else ""
    )
    maiores = sorted(gv["aliados"], key=lambda a: -a["vao_votos"])[:3]
    maiores_txt = lista_e(
        [f"{a['uf']} ({sinal_votos(a['vao_votos'])})" for a in maiores]
    )
    pb = por_uf["PB"]
    tops = []
    for a in gv["aliados"]:
        if a["vao_votos"] <= 0:
            continue
        lista = ", ".join(
            f"{nome(m['municipio'])} {sinal_votos(m['vao_votos'])}"
            for m in a["top_municipios"]
            if m["vao_votos"] > 0
        )
        tops.append(
            f"- **{a['uf']}, {nome(a['governador'])}:** {lista}. O governador passou "
            f"Flávio em {milhar(a['municipios_governador_acima'])} municípios, somando "
            f"{milhar(a['soma_vao_municipal_positivo'])} votos."
        )
    agenda = [a for a in gv["aliados"] if a["vao_votos"] > 0 and not a["alinhado_lula"]]
    agenda_txt = "; ".join(
        f"{a['uf']} com {nome(a['governador'])} ("
        + lista_e(
            [
                nome(m["municipio"])
                for m in a["top_municipios"][:3]
                if m["vao_votos"] > 0
            ]
        )
        + ")"
        for a in agenda
    )
    excluidos = [
        a["uf"] for a in gv["aliados"] if a["vao_votos"] > 0 and a["alinhado_lula"]
    ]
    excluidos_txt = (
        f" Fica de fora {lista_e(excluidos)}, onde o governador é aliado de Lula."
        if excluidos
        else ""
    )
    seg = []
    for s in gv["segundo_turno_estadual"]:
        p0, p1 = s["par"]
        seg.append(
            [
                s["uf"],
                f"{nome(p0['nome'])} ({p0['partido']}, {p0['campo']}) {pc(p0['pct'])}",
                f"{nome(p1['nome'])} ({p1['partido']}, {p1['campo']}) {pc(p1['pct'])}",
                milhar(s["eleitores"]),
                pc(s["abstencao_pct"]),
                f"{pc(s['flavio_pct'])} × {pc(s['lula_pct'])}",
                sinal_votos(s["margem_flavio_votos"]),
            ]
        )
    g22 = dados["riscos"]["comparecimento"]["grupos_2022"]
    com, sem = g22["com_2t_governador_2022"], g22["sem_2t_governador_2022"]
    paginas = "; ".join(
        f"{uf} p{'p' if len(pg) > 1 else ''}. {lista_e([str(x) for x in pg])}"
        for uf, pg in gv["paginas_linhas"].items()
    )
    return f"""
## 3. Governadores como aliados

**Método.** Vão = votos do governador eleito menos votos de Flávio na mesma UF e na mesma urna; em pontos, cada um sobre os válidos do próprio cargo, como calcula o TSE (no governador, a base inclui votos anulados sub judice). Rótulo obrigatório: **teto endereçável, nunca transferência certa.** Parte do eleitorado do governador vota Lula por escolha medida.

{_tabela_aliados(gv)}

**Verificado.** Os três maiores vãos em votos: {maiores_txt}. Em {extenso(len(sem_voto), True)} UFs o governador aliado teve menos votos que Flávio: {sem_voto_txt}. Ali o governador não tem voto a emprestar; é palanque, não reserva.{divergem_txt}

**Verificado, com ressalva.** {nome(pb["governador"])} ({pb["partido"]}) é centro-direita pela classificação partidária da casa, mas é {pb["nota_alinhamento"]} (`docs/assets/voto_util_092026.json`, `campo_excecao`). O vão de {pontos(pb["vao_pp"])} na Paraíba não é endereçável como aliança: é o eleitor de um governo aliado de Lula.

**Inferência sobre medição publicada.** O Datafolha publicou no texto dos relatórios estaduais, com campo em {gv["campo_linhas"]}, como vota para presidente o eleitor de cada governador. Páginas: {paginas}. Transcrição em `{gv["arquivo_linhas"]}`.

{_linhas_datafolha(gv)}

Onde cada governador mais superou Flávio, em votos (base para agenda conjunta):

{chr(10).join(tops)}

**Juízo editorial.** Agenda conjunta vale onde o vão é positivo e o governador não é aliado de Lula: {agenda_txt}.{excluidos_txt} Mesmo ali o vão é teto: parte do eleitor do governador vota Lula por escolha medida.

### Os sete 2º turnos estaduais

{tabela(["UF", "1º colocado", "2º colocado", "Eleitorado", "Abstenção", "Presidente (Flávio × Lula)", "Margem de Flávio"], seg)}

**Verificado.** Em 2022, nas {len(com["ufs"])} UFs com 2º turno de governador ({lista_e(com["ufs"])}), o comparecimento variou {sinal(com["variacao_pp"])} ponto entre os turnos; nas outras {len(sem["ufs"])}, {sinal(sem["variacao_pp"])}. A lista sai de `data/raw/tse_resultados/votacao_candidato_munzona_2022.zip`.

**Juízo editorial.** {_juizo_segundo_turno(gv["segundo_turno_estadual"])}
"""


# ---------------------------------------------------------------- 4. Congresso


def secao_congresso(dados: dict) -> str:
    c = dados["congresso"]
    cam = c["camara"]
    sen = c["senado_2027"]
    dir_cam = cam["blocos"]["direita + centro-direita"]
    esq_cam = cam["blocos"]["esquerda + centro-esquerda"]
    dir_sen = sen["por_bloco"]["direita + centro-direita"]
    esq_sen = sen["por_bloco"]["esquerda + centro-esquerda"]
    linhas = []
    for d in c["deputados_federais_top3"]:
        anc = d["ancora_direita"]
        linhas.append(
            [d["uf"]]
            + [
                f"{nome(t['nome'])} ({t['partido']}) {milhar(t['votos'])}"
                for t in d["top3"]
            ]
            + [
                (
                    f"{nome(anc['nome'])} ({anc['partido']}, {pc(anc['pct_validos_uf'])})"
                    if anc
                    else "nenhuma"
                )
            ]
        )
    grandes = sorted(
        (
            (d["uf"], t)
            for d in c["deputados_federais_top3"]
            for t in d["top3"]
            if t["campo"] in ("direita", "centro-direita")
        ),
        key=lambda x: -x[1]["votos"],
    )[:10]
    grandes_txt = "; ".join(
        f"{nome(t['nome'])} ({uf}, {t['partido']}) {milhar(t['votos'])}, "
        f"{pc(t['pct_validos_uf'])} dos válidos"
        for uf, t in grandes
    )
    sens = sorted(
        (
            (s["uf"], e)
            for s in c["senadores_eleitos_2026"]
            for e in s["eleitos"]
            if e["campo"] in ("direita", "centro-direita")
        ),
        key=lambda x: -x[1]["votos"],
    )[:8]
    sens_txt = "; ".join(
        f"{nome(e['nome'])} ({uf}, {e['partido']}) {milhar(e['votos'])}"
        for uf, e in sens
    )
    prov = lista_e(cam["ufs_provisorias"]) or "nenhuma"
    acima_maioria = dir_cam >= cam["maioria_absoluta"]
    acima_pec = dir_cam >= cam["tres_quintos"]
    sen_pec = dir_sen >= sen["tres_quintos"]
    return f"""
## 4. Senado e Câmara como argumento

**Verificado.** Na Câmara eleita, direita e centro-direita somam {dir_cam} das {cam["vagas"]} cadeiras: {"acima" if acima_maioria else "abaixo"} da maioria absoluta ({cam["maioria_absoluta"]}) e {"acima" if acima_pec else "abaixo"} dos três quintos de emenda constitucional ({cam["tres_quintos"]}). Esquerda e centro-esquerda somam {esq_cam}; o centro, {cam["blocos"]["centro"]}. PL {cam["por_partido"]["PL"]}, PT {cam["por_partido"]["PT"]}. No Senado de 2027, direita e centro-direita somam {dir_sen} de {sen["total"]}, {"acima" if sen_pec else "abaixo"} dos três quintos ({sen["tres_quintos"]}); esquerda e centro-esquerda, {esq_sen}. O PL terá {sen["por_partido"]["PL"]} senadores, {sen["pl_eleitos_2026"]} eleitos agora. Fonte: `{c["fonte"]}`, gerado em {hora_br(c["fonte_gerado_em"])}; UFs da Câmara ainda em alocação provisória: {prov}.

**Juízo editorial, a favor de Flávio.** Pela classificação de campo da casa, um presidente Flávio começa com maioria nas duas Casas sem depender do centro; a fidelidade de PP, União e Podemos a essa maioria é hipótese, não número. Um presidente Lula governaria contra {dir_cam} deputados e {dir_sen} senadores da direita e da centro-direita. O argumento é governabilidade: o eleitor de centro que quer estabilidade tem, na composição já eleita, um motivo concreto.

**Juízo editorial, achado contrário.** O mesmo número serve a Lula. Com Câmara e Senado à direita, o eleitor que teme concentração de poder pode votar Lula como contrapeso. A campanha de Flávio não deve vender a maioria como cheque em branco; deve vendê-la como fim do impasse.

**Verificado.** Âncoras de campanha. Deputados federais mais votados da direita e da centro-direita: {grandes_txt}. Senadores eleitos com mais votos nesse campo: {sens_txt}.

Os três deputados federais mais votados em cada UF e a âncora da direita (o mais votado da direita ou da centro-direita, com a parcela dos válidos da UF):

{tabela(["UF", "1º", "2º", "3º", "Âncora da direita"], linhas)}
"""


# ---------------------------------------------------------------- 5. riscos


def _tabela_comparecimento(reg: dict) -> str:
    linhas = []
    for r in ("Nordeste", "Norte", "Centro-Sul"):
        x = reg[r]
        linhas.append(
            [
                r,
                pc(x["comparecimento_2022_1t_pct"]),
                pc(x["comparecimento_2026_pct"]),
                sinal(x["diferenca_2026_menos_2022_1t_pp"]),
                sinal(x["variacao_2022_pp"]),
                sinal_votos(x["valor_1pp_2026"]),
            ]
        )
    cab = [
        "Região",
        "2022, 1º turno",
        "2026, 1º turno",
        f"2026 {MENOS} 2022 (pp)",
        "2022, entre turnos (pp)",
        "Valor de +1 ponto em 2026 (saldo de Flávio)",
    ]
    return tabela(cab, linhas)


def secao_riscos(dados: dict) -> str:
    r = dados["riscos"]
    comp = r["comparecimento"]
    reg = comp["regioes"]
    t = r["transferencia"]
    ext = r["exterior"]
    pp_txt = "; ".join(
        f"{x['uf']} {sinal(x['flavio_menos_bolsonaro_2t_pp'])} "
        f"(terceira via {pc(x['terceiros_pct'])})"
        for x in r["piores_ufs_pp_contra_2t_2022"]
    )
    votos_txt = "; ".join(
        f"{x['uf']} {sinal_votos(x['flavio_menos_bolsonaro_2t_votos'])}"
        for x in r["piores_ufs_votos_contra_2t_2022"]
    )
    abaixo_1t = [
        x["uf"]
        for x in r["piores_ufs_contra_1t_2022"]
        if x["flavio_menos_bolsonaro_1t_pp"] < 0
    ]
    abaixo_1t_txt = (
        (
            " A única UF em que Flávio fica abaixo até do 1º turno de Bolsonaro: "
            if len(abaixo_1t) == 1
            else " UFs em que Flávio fica abaixo até do 1º turno de Bolsonaro: "
        )
        + lista_e([UF_NOME[u] for u in abaixo_1t])
        + "."
        if abaixo_1t
        else ""
    )
    grandes = r["municipios_grandes_abaixo_de_bolsonaro_1t_pp"]
    mun_txt = "; ".join(
        f"{nome(m['municipio'])} ({m['uf']}) {sinal(m['diferenca_pp'])}"
        for m in grandes
    )
    por_uf: dict[str, list[dict]] = {}
    for m in grandes:
        por_uf.setdefault(m["uf"], []).append(m)
    uf_mais, lista_mais = max(por_uf.items(), key=lambda kv: len(kv[1]))
    leitura = (
        f"{extenso(len(lista_mais)).capitalize()} dos {extenso(len(grandes))} são de {UF_NOME[uf_mais]}."
        if len(lista_mais) > 1
        else ""
    )
    caiado_br = next(
        x["pct"]
        for x in dados["aritmetica"]["primeiro_turno"]["terceiros"]
        if x["numero"] == 55
    )
    # Caiado é citado onde teve ao menos o dobro da parcela nacional.
    caiado = [m for m in grandes if m["caiado_pct"] >= 2 * caiado_br]
    if caiado:
        leitura += (
            " Caiado teve "
            + lista_e(
                [f"{pc(m['caiado_pct'])} em {nome(m['municipio'])}" for m in caiado]
            )
            + f", contra {pc(caiado_br)} no país."
        )
    gov = r["governador_direita_eleito_flavio_perdeu"]
    alinhados = {
        a["uf"] for a in dados["governadores"]["aliados"] if a["alinhado_lula"]
    }
    gov_txt = "; ".join(
        f"{x['uf']}, {nome(x['governador'])} ({x['partido']}"
        + (", aliado de Lula" if x["uf"] in alinhados else "")
        + f") eleito com {pc(x['governador_pct'])}, e Lula {pc(x['lula_pct'])} × Flávio {pc(x['flavio_pct'])}"
        for x in gov
    )
    vf = comp["valor_1pp_ufs_flavio"]
    vl = comp["valor_1pp_ufs_lula"]
    corr = comp["correlacao_variacao_2022_x_lula_2t_2022"]
    cn, cd_ = t["caiado_nexus"], t["caiado_datafolha"]
    d_cs = reg["Centro-Sul"]["diferenca_2026_menos_2022_1t_pp"]
    d_ne = reg["Nordeste"]["diferenca_2026_menos_2022_1t_pp"]
    d_no = reg["Norte"]["diferenca_2026_menos_2022_1t_pp"]
    por_uf_22 = comp["por_uf_2022"]
    quedas_22 = lista_e([f"{x['uf']} {sinal(x['variacao_pp'])}" for x in por_uf_22[:3]])
    altas_22 = lista_e(
        [f"{x['uf']} {sinal(x['variacao_pp'])}" for x in reversed(por_uf_22[-3:])]
    )
    return f"""
## 5. Riscos e achados contrários

**Verificado. Onde Flávio mais fica abaixo de Bolsonaro no 2º turno de 2022.** Em pontos: {pp_txt}. Em votos: {votos_txt}.{abaixo_1t_txt}

**Verificado. Municípios grandes (mais de {milhar(r["municipio_grande_minimo_validos"])} válidos) onde Flávio ficou abaixo do 1º turno de Bolsonaro:** {mun_txt}. {leitura}

**Verificado. Governador de direita ou centro-direita eleito onde Flávio perdeu:** {gov_txt}. Nas {extenso(len(gov), True)} UFs o governador do bloco venceu e o presidenciável do bloco perdeu, na mesma urna.

**Comparecimento.**

{_tabela_comparecimento(reg)}

**Verificado.** Contra o 1º turno de 2022, o comparecimento de 2026 variou {sinal(d_cs)} ponto no Centro-Sul, {sinal(d_ne)} no Nordeste e {sinal(d_no)} no Norte. Em 2022, entre os turnos, variou {sinal(reg["Centro-Sul"]["variacao_2022_pp"])} no Centro-Sul, {sinal(reg["Nordeste"]["variacao_2022_pp"])} no Nordeste e {sinal(reg["Norte"]["variacao_2022_pp"])} no Norte; por UF, as maiores quedas foram {quedas_22} e as maiores altas, {altas_22}; a correlação entre a variação de cada UF e a parcela de Lula no 2º turno de 2022 foi de {dec(corr, 2) if corr is not None else "indefinida"}. **Hipótese.** Um ponto a mais de comparecimento nas {len(comp["ufs_flavio"])} UFs de Flávio vale {sinal_votos(vf["saldo_flavio"])} votos de saldo; nas {len(comp["ufs_lula"])} de Lula, {sinal_votos(vl["saldo_flavio"])}. {comp["nota"]}

**Verificado. Exterior.** Lula {pc(ext["lula_pct"])} × Flávio {pc(ext["flavio_pct"])}, margem de {milhar(abs(ext["margem_votos"]))} votos para {"Lula" if ext["margem_votos"] < 0 else "Flávio"}, com {milhar(ext["validos"])} válidos e comparecimento de {pc(ext["comparecimento_2026_pct"])} (era {pc(ext["comparecimento_2022_1t_pct"])} no 1º turno de 2022). Não muda a conta nacional.

**Inferência. Incerteza da transferência.** As duas medições de Caiado discordam: Nexus Flávio {cn["Flávio"]:g} × Lula {cn["Lula"]:g}; Datafolha Flávio {cd_["Flávio"]:g} × Lula {cd_["Lula"]:g}. Entre as seis combinações de matriz e hipótese, a margem projetada vai {faixa_milhoes(t["margem_min"], t["margem_max"])}. As linhas vêm de pesquisas de setembro. A central da casa, feita com o mesmo acervo de pesquisas, dava a Flávio {sinal(t["central_casa_margem_pp"])} ponto sobre Lula nos válidos, e a urna deu {sinal(t["urna_margem_pp"])}. Em 2022 a média das pesquisas finais tinha superestimado a vantagem de Lula em {pontos(t["erro_comum_2022_pp"])} (erro comum de {t["erro_comum_2022_casas"]} casas, `analysis/predicao_2026/erro_2022/erro_2022.json`). Nas duas eleições as pesquisas ficaram abaixo da urna na margem da direita; isso não diz em que direção erram as linhas de transferência, só que elas vêm de instrumentos que erraram.

**Inferência. Base.** {pc(r["base"]["trocar_para_lula_pct"])} da base de Flávio trocando para Lula, ou {pc(r["base"]["abster_pct"])} deixando de votar, zeram a margem central. É o número que a campanha deve vigiar.
"""


# ---------------------------------------------------------------- 6. movimentos


def _onde(onde: list[dict]) -> str:
    if "municipio" in onde[0]:
        return ", ".join(
            f"{nome(x['municipio'])} ({sinal_votos(x['vao_votos'])})" for x in onde
        )
    if "votos" in onde[0]:
        return ", ".join(
            f"{x['uf']} {milhar(x['votos'])} ({pc(x['pct'])})" for x in onde
        )
    return ", ".join(f"{x['uf']} {sinal_votos(x['saldo_flavio'])}" for x in onde)


def _bloco_movimento(m: dict) -> str:
    linhas = [
        f"### {m['ordem']}. {m['titulo']}",
        "",
        f"- **Votos esperados (saldo para Flávio): {sinal_votos(m['votos_esperados'])}.** Regra: {m['regra']}.",
        f"- **Alvo:** {m['alvo']}.",
    ]
    if m.get("teto"):
        linhas.append(f"- **Teto endereçável:** {milhar(m['teto'])} votos.")
    if m.get("faixa"):
        a, b = m["faixa"]
        linhas.append(
            f"- **Faixa entre as duas medições:** {sinal_votos(a)} a {sinal_votos(b)}."
        )
    if m.get("partes"):
        p = m["partes"]
        linhas.append(
            f"- **Partes:** interior {sinal_votos(p['interior'])}, capitais {sinal_votos(p['capitais'])}."
        )
    if m.get("linha_medida_1t"):
        lm = m["linha_medida_1t"]
        linhas.append(
            "- **Linha medida no 1º turno (Datafolha, SP p. 4):** eleitor de Tarcísio "
            f"com Flávio {lm['Flávio']}%, com Lula {lm['Lula']}%."
        )
    if m.get("governador_go"):
        go = m["governador_go"]
        nota = f"; {go['nota']}" if go.get("nota") else ""
        linhas.append(
            f"- **Governador eleito em Goiás:** {nome(go['nome'])} ({go['partido']}), "
            f"{milhar(go['votos'])} votos{nota}."
        )
    if m.get("contraprova") is not None:
        linhas.append(
            f"- **Contraprova:** {sinal_votos(m['contraprova'])} votos do lado oposto, pela mesma regra."
        )
    if m.get("onde"):
        linhas.append(f"- **Onde:** {_onde(m['onde'])}.")
    linhas.append(f"- **Rótulo:** {m['rotulo']}.")
    return "\n".join(linhas)


def secao_movimentos(dados: dict) -> str:
    blocos = "\n\n".join(_bloco_movimento(m) for m in dados["movimentos"])
    lista = "\n".join(
        f"{m['ordem']}. {m['titulo']}: {sinal_votos(m['votos_esperados'])}"
        for m in dados["movimentos"]
    )
    return f"""
## 6. Dez movimentos, do maior para o menor em votos esperados

**Juízo editorial.** A ordem é da casa. O número de cada movimento sai de uma regra escrita ao lado, sobre medição publicada, analogia declarada ou hipótese; nenhum é previsão. Os movimentos não se somam: o eleitor de Renan em São Paulo é o mesmo que a agenda com Tarcísio procura, e os movimentos territoriais (São Paulo, Minas, Rio, Nordeste) são o canal por onde passa parte do voto dos movimentos de terceira via. Só o comparecimento traz eleitor novo.

{lista}

{blocos}

## O que mudaria esta leitura

- Uma matriz de transferência medida por UF. O acervo da casa tem a matriz nacional da Nexus e duas linhas nacionais do Datafolha; nenhuma diz para onde vai, em São Paulo ou em Goiás, o eleitor de Renan, Cury ou Caiado.
- A linha de 2º turno do eleitor de Tarcísio. A transcrição da casa tem a de Cleitinho e a de Ruas; a de São Paulo, que mais pesa, não está no acervo.
- Pesquisas do 2º turno com cruzamento pelo voto declarado no 1º turno. Com elas, as hipóteses deste capítulo viram medição.
"""


def capitulo(dados: dict) -> str:
    partes = [
        abertura(dados),
        secao_aritmetica(dados),
        secao_geografia(dados),
        secao_governadores(dados),
        secao_congresso(dados),
        secao_riscos(dados),
        secao_movimentos(dados),
    ]
    texto = "\n".join(p.strip("\n") + "\n" for p in partes)
    while "\n\n\n" in texto:
        texto = texto.replace("\n\n\n", "\n\n")
    return texto
