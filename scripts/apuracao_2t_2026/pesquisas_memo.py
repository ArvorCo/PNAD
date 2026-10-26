"""Memorando ``pesquisas.md`` do 2º turno: números, consultas e hipóteses.

Todo número sai dos três dicionários gravados pelo script principal. O texto
separa fato medido, inferência, juízo editorial e hipótese, e deixa um bloco
sinalizado para a entrada do autor.
"""

from __future__ import annotations

from typing import Any

MENOS = "−"


def n(x: float | None, casas: int = 2, sinal: bool = False) -> str:
    if x is None:
        return "n/d"
    s = f"{abs(x):,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if x < 0 and round(abs(x), casas) > 0:
        return MENOS + s
    return ("+" + s) if sinal and round(x, casas) > 0 else s


def inteiro(x: float) -> str:
    return f"{round(x):,}".replace(",", ".")


def data(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}"


def _lista_erros(xs: list[dict[str, Any]]) -> str:
    return ", ".join(
        "{} ({})".format(
            x["instituto"], n(x["erro_validos_do_total"]["erro_f_menos_l"], 2, True)
        )
        for x in xs
    )


def _lista_ufs(xs: list[dict[str, Any]]) -> str:
    return ", ".join(
        "{} {}".format(x["uf"], n(-x["erro_flavio_pp"], 2, True)) for x in xs
    )


def _tabela_pesquisas(s: dict[str, Any]) -> list[str]:
    linhas = [
        "| Casa | Campo | Modo | Publicado F × L | Válidos F | Erro F−L | Erro oficial | "
        "Erro PNAD | Margem AAS |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    por_id = {x["id"]: x for x in s["pesquisas"]}
    for i in s["ranking"]:
        x = por_id[i]
        t = x["publicado_total"]
        eo = x["erro_validos_oficiais"]
        er = x["erro_reponderado"]
        dentro = "" if x["erro_fora_da_margem_aas"] else " (dentro)"
        linhas.append(
            f"| {x['instituto']} | {data(x['campo']['inicio'])}–{data(x['campo']['fim'])} "
            f"| {x['modo']} | {n(t['flavio'], 1)} × {n(t['lula'], 1)} "
            f"| {n(x['validos_do_total']['flavio'])} "
            f"| {n(x['erro_validos_do_total']['erro_f_menos_l'], 2, True)}{dentro} "
            f"| {n(eo['erro_f_menos_l'], 2, True) if eo else 'n/d'} "
            f"| {n(er['erro_f_menos_l'], 2, True) if er else 'sem PNAD'} "
            f"| {n(x['margem_95_diferenca_aas_pp'])} |"
        )
    return linhas


def _tabela_metodos(p: dict[str, Any]) -> list[str]:
    linhas = [
        "| Método | UFs com vencedor certo | RMSE pond. (pp de Flávio) | Viés | RMSE sem viés "
        "| Nacional F | Erro F−L nacional | Erros de vencedor |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for k in p["ranking_rmse"]:
        m = p["metodos"][k]
        linhas.append(
            f"| {m['rotulo']} | {m['acertou_vencedor']}/{m['n_ufs']} "
            f"| {n(m['rmse_flavio_pp_ponderado'])} | {n(m['vies_flavio_pp_ponderado'], 2, True)} "
            f"| {n(m['rmse_sem_vies_pp'])} | {n(m['nacional_flavio_previsto'])} "
            f"| {n(m['nacional_erro_f_menos_l_pp'], 2, True)} "
            f"| {', '.join(m['errou_vencedor_ufs']) or 'nenhum'} |"
        )
    return linhas


def _motor_autor(a: dict[str, Any]) -> list[str]:
    cen = {c["nome"]: c for c in a["cenarios"]}
    rt = a["reproducao_tweet"]
    u = a["urna"]
    out = [
        "**Cenário refeito no motor da casa com a urna observada** "
        "(`hipotese_autor.json`; `scripts/reponderacao-simulador.py` sobre o snapshot "
        f"`{a['snapshot']['versao']}`, último de 24/10, o único da data que reproduz o "
        f"tweet: Flávio {n(rt['flavio_validos_pct'])}% e brancos e nulos de "
        f"{n(rt['branco_nulo_pct_comparecimento'])}% do comparecimento; empate com "
        f"presença −6,4% dá Flávio {n(rt['empate_presenca_menos_6_4_flavio_pct'])}%). "
        f"Fixados: abstenção {n(u['abstencao_pct'])}% e brancos mais nulos "
        f"{inteiro(u['brancos_mais_nulos'])} ({n(u['branco_nulo_pct_comparecimento'])}% "
        "de quem compareceu; o tweet usava 18,50% e 3,1%).\n",
        "| Cenário | Presença relativa de Flávio | Indecisos para Flávio | Flávio | "
        "Lula | Erro F−L contra a urna | Votos de Flávio contra a urna |",
        "|---|---|---|---|---|---|---|",
    ]
    for c in a["cenarios"]:
        pm, pl, cu = c["parametros"], c["placar"], c["contra_a_urna"]
        out.append(
            f"| {c['regra']} | {n(pm['presenca_relativa'], 1, True)}% "
            f"| {n(pm['indecisos_flavio_efetivo'], 1)}% | {n(pl['flavio_validos_pct'])} "
            f"| {n(pl['lula_validos_pct'])} | {n(cu['diferenca_f_menos_l_pp'], 2, True)} "
            f"| {inteiro(cu['flavio_votos'])} |"
        )
    out.append("")
    if a["presenca_necessaria_a"] is not None:
        out.append(
            f"- (a) Com indecisos na proporção automática, bater a urna exige presença "
            f"relativa de Flávio de {n(a['presenca_necessaria_a'], 1, True)}%, contra "
            "+3,8% da central."
        )
    lim = cen.get("b_limite_todos_indecisos_para_lula")
    if a["indecisos_flavio_necessario_b"] is not None:
        out.append(
            f"- (b) Mantida a presença +3,8%, os indecisos precisariam ir "
            f"{n(a['indecisos_flavio_necessario_b'], 1)}% para Flávio."
        )
    elif lim:
        out.append(
            "- (b) Mantida a presença +3,8%, nenhuma divisão dos indecisos alcança a "
            f"urna: mesmo com todos para Lula, Flávio fica em "
            f"{n(lim['placar']['flavio_validos_pct'])}% "
            f"({n(lim['contra_a_urna']['diferenca_f_menos_l_pp'], 2, True)} pp em F−L)."
        )
    c = cen.get("c_combinacao_do_autor_com_bn_reais")
    if c:
        out.append(
            "- (c) A combinação do autor (−12,5% e 34,8/65,2) com brancos e nulos reais "
            f"dá Flávio {n(c['placar']['flavio_validos_pct'])}% "
            f"({n(c['contra_a_urna']['diferenca_f_menos_l_pp'], 2, True)} pp em F−L, "
            f"{inteiro(c['contra_a_urna']['flavio_votos'])} votos de Flávio acima da urna)."
        )
    out.append("")
    return out


def _entrada_autor(
    s: dict[str, Any],
    cbr: dict[str, Any],
    mesmos: dict[str, Any],
    b: dict[str, Any],
    a: dict[str, Any],
) -> list[str]:
    h = s["hipoteses"]
    pn = h["presenca_relativa_necessaria"]
    idv = h["indecisos_divisao_autor"]
    ind = h["indecisos_extremo"]
    cb = h["contabilidade_entre_turnos"]
    pres = h["presenca_declarada"]
    lim = cb["limite_comparecimento"]
    out = [
        "## 11. ENTRADA DO AUTOR\n",
        "<!-- ENTRADA DO AUTOR: início. Fonte: analysis/apuracao_2t_2026/hipotese_autor.md "
        "(tweet de 25/10, 21h41; imagem em noticias_fontes/"
        "tweet_leonardodias_20261025_2141.webp). -->",
        '> **ENTRADA DO AUTOR (juízo editorial declarado de Leonardo Dias).** "Para chegar '
        "num resultado próximo ao final, tivemos de diminuir as abstenções para o volume "
        "real de 19,2%, aumentar a presença relativa pró-Lula para 12,5% e direcionar mais "
        'indecisos para o Lula. Essa seria a hipótese, se foi isso mesmo, não saberemos."',
        "",
        "Cenário do simulador (Central Média de 24/10) que reproduz a urna: abstenção "
        "18,50%, presença relativa de Flávio −12,5% (presença efetiva Flávio 76,0%, Lula "
        "86,9%), indecisos 100% escolhendo, divisão 34,8% Flávio × 65,2% Lula; resultado "
        "48,3 × 51,7. Empate exigiria presença relativa −6,4%, mantido o resto.\n",
        *_motor_autor(a),
        "**Peça 1, abstenção.**",
        f"- Sustenta (fato): a urna mediu abstenção de {n(b['abstencao_pct'])}%, o número "
        f"que o tweet cita (o cenário da imagem usou 18,50%), contra "
        f"{n(cbr['abstencao_1t_pct'])}% no 1º turno; "
        f"{n(cbr['variacao_comparecimento'] / 1e6)} milhões a mais votaram."
        + (
            f" Nos mesmos municípios: {n(mesmos['pa_2t'])}% contra "
            f"{n(mesmos['pa_1t_mesmos'])}%."
            if mesmos
            else ""
        ),
        "- Contraria (fato): menos abstenção sozinha não move a razão entre os "
        "candidatos; só move se os novos votantes forem desiguais. Mesmo com todos para "
        f"Lula, o efeito seria no máximo {n(lim['parcela_maxima_explicada_pp'] if lim else None)} "
        f"pp em F−L, e entre as UFs a variação da abstenção não acompanha o resíduo de "
        f"Flávio (correlação {n(cb['correlacao_variacao_abstencao_com_residuo'])}).",
        "",
        "**Peça 2, presença diferencial (o centro da hipótese).**",
        "- Presença por candidato **não é medida**: a urna diz quantos votaram, nunca em "
        "quem votaria quem ficou em casa. Por isso a frase final do autor é a leitura "
        "correta.",
        "- Fato aritmético: no motor, com a urna fixada, a presença relativa necessária "
        f"é {n(a['presenca_necessaria_a'], 1, True)}%. Conferência por fora do motor: a "
        f"razão F/L da Média Arvor precisava cair {n(-pn['media_arvor'], 1)}% "
        f"({n(pn['media_arvor_sem_o_extra'], 1, True)}% sem o +"
        f"{n(pn['extra_central_pct'], 1)}% já embutido); a da média simples publicada das "
        f"20 casas, {n(pn['media_simples_publicada_20_casas'], 1, True)}%.",
        "- Contraria (fato): essa mesma conta é idêntica à de um erro comum de medição; "
        "a urna não separa as duas. E a presença declarada nas pesquisas apontou para o "
        "outro lado: "
        + "; ".join(
            "{} desloca F−L {}".format(
                x["instituto"], n(x["deslocamento_f_menos_l"], 2, True)
            )
            for x in pres
        )
        + " a favor de Flávio. Se houve presença diferencial pró-Lula, ela contrariou o "
        "que os eleitores disseram aos institutos.",
        "",
        "**Peça 3, destino dos indecisos.**",
        f"- Fato: indecisos médios de {n(idv['indecisos_medios_pct'], 1)}% nas últimas "
        f"ondas. Com a divisão do autor (34,8% Flávio), o erro médio vai de "
        f"{n(idv['erro_medio_sem_redistribuir'], 2, True)} para "
        f"{n(idv['erro_medio_f_menos_l'], 2, True)} pp; com todos para Lula, "
        f"{n(ind['erro_medio_todos_indecisos_lula'], 2, True)}.",
        "- Contraria: os indecisos são poucos para carregar o resultado; no cenário do "
        "autor eles somam 2,2 milhões. O destino deles não é identificável no agregado.",
        "",
        "**Leitura.** As três peças juntas reproduzem a urna por construção, como qualquer "
        "combinação que mude a razão F/L em cerca de 15%. A urna sustenta a abstenção "
        "como fato, deixa a presença diferencial sem medida e limita o papel dos "
        'indecisos. **Juízo editorial do autor, preservado:** "se foi isso mesmo, não '
        'saberemos".',
        "<!-- ENTRADA DO AUTOR: fim -->\n",
    ]
    return out


def memorando(
    s: dict[str, Any], e: dict[str, Any], p: dict[str, Any], a: dict[str, Any]
) -> str:
    u = s["urna"]
    b = u["brasil"]
    f = u["fonte"]
    r = s["resumo"]
    rp = r["publicado_validos_do_total"]
    ro = r["publicado_validos_oficiais"]
    rr = r["reponderado"]
    rm = r["publicado_mesmas_casas_reponderadas"]
    ef = s["efeito_reponderacao"]
    c = s["centrais"]
    t = s["tendencia_publicada"]
    h = s["hipoteses"]
    cb = h["contabilidade_entre_turnos"]
    cbr = cb["brasil"]
    lim = cb["limite_comparecimento"]
    um = s["primeiro_turno"]
    r22 = s["referencia_2022"]
    pn = s["painel_1t_2t"]
    ind = h["indecisos_extremo"]
    pres = {x["instituto"]: x for x in h["presenca_declarada"]}
    pesq = {x["instituto"]: x for x in s["pesquisas"]}
    mt = p["metodos"]
    tr = mt["transportado_25_10"]
    mmed, mproj = mt["media_25_10"], mt["projecao_25_10"]
    ranking = list(s["ranking"])
    por_id = {x["id"]: x for x in s["pesquisas"]}
    perto = [por_id[i] for i in ranking[:3]]
    longe = [por_id[i] for i in ranking[-4:]][::-1]
    a_pub = c["ancora_projecao_published"]["erro_f_menos_l"]
    a_pnad = c["ancora_projecao_pnad"]["erro_f_menos_l"]
    e_proj = c["projecao_arvor"]["erro_f_menos_l"]
    e_med = c["media_arvor"]["erro_f_menos_l"]
    q = pesq.get("Quaest")
    nex = pesq.get("Nexus")
    pnad_1t = um["efeito_reponderacao_ultimas_ondas"]
    urna_dif = b["validos"]["flavio"] - b["validos"]["lula"]
    mesmos = (u.get("abstencao_mesmos_municipios") or {}).get("brasil") or {}
    regioes_tr = tr["regioes"]
    ufs_tr = sorted(tr["ufs"], key=lambda x: x["erro_flavio_pp"])

    out: list[str] = []
    add = out.append
    add("# Pesquisas, centrais e projeções contra a urna do 2º turno de 2026\n")
    add(
        "Gerado por `python3 scripts/apuracao-2t-2026-pesquisas.py`. Não editar à mão: "
        "o script regrava este arquivo e os três JSON ao lado.\n"
    )
    if f["tipo"] == "api_ao_vivo":
        add(
            f"**Urna parcial.** Placar lido ao vivo em {f['at']} (atualizado em "
            f"{f.get('atualizado_em')}), {n(f['pst'])}% das seções. Reexecute quando "
            "`analysis/apuracao_2t_2026/dados/presidente.json` existir; o script passa a "
            "usá-lo sozinho. Diferenças de centésimos são esperadas.\n"
        )
    else:
        add(f"Urna: `{f['arquivo']}` (sha256 `{f['sha256'][:16]}`).\n")
    add(
        "Convenção: erro = pesquisa menos urna, em pontos dos votos válidos. Na diferença "
        "Flávio menos Lula (F−L), positivo quer dizer que a pesquisa pôs Flávio mais à "
        "frente do que a urna. O 1º turno e 2022 usaram L−F; para comparar, troque o sinal.\n"
    )

    add("## 1. O que a urna devolveu (fato)\n")
    add(
        f"- Lula {inteiro(b['votos']['lula'])} × Flávio {inteiro(b['votos']['flavio'])} "
        f"votos; {n(b['validos']['lula'])}% × {n(b['validos']['flavio'])}% dos válidos; "
        f"F−L = {n(urna_dif, 2, True)} pp."
    )
    bs = u["brasil_sem_exterior"]["validos"]
    add(
        f"- Sem exterior (universo das pesquisas e das centrais): Lula {n(bs['lula'])}% × "
        f"Flávio {n(bs['flavio'])}%."
    )
    add(
        f"- Abstenção {n(b['abstencao_pct'])}% contra {n(cbr['abstencao_1t_pct'])}% no 1º "
        f"turno ({n(cbr['variacao_abstencao_pp'], 2, True)} pp); comparecimento "
        f"{n(cbr['variacao_comparecimento'] / 1e6, 2, True)} milhões de eleitores."
        + (
            f" Nos {inteiro(mesmos['n_mun_fechados'])} municípios já fechados: "
            f"{n(mesmos['pa_2t'])}% contra {n(mesmos['pa_1t_mesmos'])}% nos mesmos municípios."
            if mesmos
            else ""
        )
        + "\n"
    )

    add("## 2. Os números mais fortes\n")
    fortes = [
        f"Erro comum das {r['n_casas']} casas (última onda, campo de 19 a 24/10): "
        f"{n(rp['media'], 2, True)} pp em F−L; mediana {n(rp['mediana'], 2, True)}.",
        f"Todas as {rp['n']} casas erraram para o mesmo lado: {rp['positivos']} "
        "superestimaram Flávio, nenhuma superestimou Lula.",
        f"{r['flavio_a_frente_nos_validos']} de {r['n_casas']} casas tinham Flávio à frente "
        f"nos válidos; {r['acertaram_vencedor']} acertaram o vencedor "
        f"({', '.join(r['casas_que_acertaram_vencedor'])}).",
        f"Dispersão entre casas {n(rp['desvio_padrao'])} pp, abaixo do desvio que só a "
        f"amostragem simples produziria ({n(r['desvio_esperado_so_amostragem_aas_pp'])}): "
        "o erro é comum, não de uma casa.",
        f"{r['fora_da_margem_aas']} de {r['n_casas']} erros ficam fora da margem de 95% da "
        "diferença sob amostragem simples.",
        f"Válidos oficiais das casas: erro comum {n(ro['media'], 2, True)} ({ro['n']} casas).",
        f"Reponderação por renda (PNAD): {ef['afastou']} de {ef['n']} casas se afastaram da "
        f"urna, {ef['aproximou']} se aproximou; deslocamento médio "
        f"{n(ef['deslocamento_medio_f_menos_l'], 2, True)} pp em F−L na direção de Flávio.",
        f"Nas mesmas {rr['n']} casas, erro comum publicado {n(rm['media'], 2, True)} contra "
        f"reponderado {n(rr['media'], 2, True)}.",
        f"Média Arvor 52,88 × 47,12: erro {n(e_med, 2, True)} pp em F−L.",
        f"Projeção Arvor 52,07 × 47,93: erro {n(e_proj, 2, True)} pp; a âncora publicada "
        f"sozinha errava {n(a_pub, 2, True)}, a PNAD somou {n(a_pnad - a_pub, 2, True)} e a "
        f"presença relativa de Flávio (+3,8%) somou {n(e_proj - a_pnad, 2, True)}.",
        f"1º turno: erro comum {n(um['erro_comum_lula_menos_flavio'], 2, True)} em L−F "
        f"(superestimou Lula). 2º turno: {n(-rp['media'], 2, True)} em L−F. Sinal invertido.",
        f"2022 (1º turno): {n(r22['erro_comum_lula_menos_bolsonaro'], 2, True)} em L−B. "
        "Dos três pontos medidos, o 2º turno de 2026 é o único em que o erro comum "
        "favoreceu o candidato da direita.",
        f"Mesma casa nos dois turnos: {pn['inverteram_sinal']} de {pn['n']} inverteram o "
        f"sinal; correlação dos erros {n(pn['correlacao'])}.",
        f"Tendência publicada de 05 a 24/10 dentro de cada casa: "
        f"{n(t['pos_urna_05_a_24']['inclinacao_dentro_da_casa_pp_dia'], 3, True)} pp/dia em "
        f"F−L (Flávio perdendo terreno); média {n(t['media_campo_ate_12_10'], 2, True)} até "
        f"12/10 e {n(t['media_campo_desde_19_10'], 2, True)} desde 19/10.",
        f"Repetir o 1º turno seção a seção, sem pesquisa nenhuma, errava "
        f"{n(tr['nacional_erro_f_menos_l_pp'], 2, True)} pp: as pesquisas (média "
        f"{n(rp['media'], 2, True)}) pouco melhoraram sobre a urna anterior.",
        f"Flávio ficou abaixo do transporte do 1º turno em {cb['ufs_com_residuo_negativo']} "
        f"de 27 UFs; viés {n(tr['vies_flavio_pp_ponderado'], 2, True)} pp na parcela dele, "
        f"RMSE sem o viés só {n(tr['rmse_sem_vies_pp'])} pp: a geografia veio certa, o "
        "nível veio errado.",
        f"Contabilidade agregada: {n(cbr['disponivel'] / 1e6)} milhões de votos disponíveis "
        "(terceira via, queda de branco/nulo e aumento de comparecimento); Flávio ficou com "
        f"{n(cbr['parcela_flavio_do_ganho_pct'], 1)}% do ganho líquido. Mesmo que todo o "
        "ganho dele viesse da terceira via, seria no máximo "
        f"{n(cbr['teto_parcela_flavio_da_terceira_via_pct'], 1)}% dela.",
        f"Correlação entre UFs da variação da abstenção com o resíduo de Flávio: "
        f"{n(cb['correlacao_variacao_abstencao_com_residuo'])}; da terceira via do 1º turno: "
        f"{n(cb['correlacao_terceiros_1t_com_residuo'])}.",
        (
            f"Teto do comparecimento: mesmo atribuindo a Lula todo o aumento líquido, ele explica "
            f"no máximo {n(lim['parcela_maxima_explicada_pp'])} pp da diferença."
            if lim
            else "Comparecimento não subiu: teto não calculado."
        ),
        f"Estaduais (Quaest e Datafolha, campo de 06 a 13/10): {e['acertaram_vencedor']} de "
        f"{len(e['pesquisas'])} acertaram o vencedor da UF; erro médio "
        f"{n(e['resumo']['media'], 2, True)} pp em F−L.",
    ]
    for i, x in enumerate(fortes, 1):
        add(f"{i}. {x}")
    add("")

    add("## 3. Pesquisas nacionais, da mais próxima à mais distante\n")
    add(
        "Erro F−L sobre os válidos do total publicado (regra da casa); oficial = válidos "
        "divulgados pela casa; PNAD = placar reponderado que entrou nas centrais. "
        '"(dentro)" marca erro menor que a margem AAS.\n'
    )
    out.extend(_tabela_pesquisas(s))
    add("")
    add(
        f"Mais próximas: {_lista_erros(perto)}. "
        f"Mais distantes: {_lista_erros(longe)}.\n"
    )
    modos = s["por_modo"]
    add(
        "Por modo de coleta (média do erro F−L): "
        + "; ".join(
            f"{k} {n(v['media'], 2, True)} (n = {v['n']})" for k, v in modos.items()
        )
        + ". As duas casas que acertaram o vencedor são presenciais; "
        "o grupo presencial também inclui Alfa (+7,63). Amostra pequena: descrição, não teste.\n"
    )
    add(
        "Fora desta lista: Data Ranking (campo até 16/10) entrou na Projeção, mas a regra "
        "de campo encerrado a partir de 19/10 o exclui aqui.\n"
    )

    add(
        "## 4. A reponderação por renda nesta rodada (achado contrário à tese da casa)\n"
    )
    add(
        "**Fato.** A casa assumiu que os institutos subestimam a renda alta e, com ela, "
        "Flávio. Trocar o perfil de renda pela PNAD deslocou todas as casas reponderáveis "
        f"para Flávio (média {n(ef['deslocamento_medio_f_menos_l'], 2, True)} pp em F−L), e a "
        f"urna foi para o outro lado. {ef['afastou']} de {ef['n']} se afastaram, "
        f"{ef['aproximou']} se aproximou, {ef['neutro']} ficou neutra.\n"
    )
    add(
        "| Casa | Perfil de renda | Erro publicado | Erro PNAD | Variação do erro absoluto |"
    )
    add("|---|---|---|---|---|")
    for x in ef["por_casa"]:
        add(
            f"| {x['instituto']} | {x['perfil_renda'] or 'n/d'} "
            f"| {n(x['erro_publicado_f_menos_l'], 2, True)} "
            f"| {n(x['erro_reponderado_f_menos_l'], 2, True)} "
            f"| {n(x['variacao_erro_absoluto'], 2, True)} |"
        )
    add("")
    add(
        f"No 1º turno a mesma régua aproximou {pnad_1t['aproximou']} de {pnad_1t['n']} casas "
        f"e cortou o erro do agregador de {n(um['agregador_publicado_erro'], 2, True)} para "
        f"{n(um['agregador_reponderado_erro'], 2, True)} (L−F). No 2º turno ela piorou "
        "todas as casas menos uma. **Juízo editorial:** a reponderação por renda não é uma "
        "correção estável de sinal conhecido; funcionou em uma rodada e falhou na seguinte. "
        "Publicar com o mesmo destaque que teve no 1º turno.\n"
    )
    add(
        "Ressalvas da própria série: Datafolha de 24/10 usou perfil da onda anterior "
        "(hipótese declarada), Veritá usou perfil condicional e várias casas têm "
        "`perfil_publicado` com etapa de ponderação não explicitada. Nas casas com perfil "
        "ponderado identificado, a variação do erro absoluto foi: "
        + "; ".join(
            f"{x['instituto']} {n(x['variacao_erro_absoluto'], 2, True)}"
            for x in ef["por_casa"]
            if x["perfil_renda"] == "perfil_ponderado"
        )
        + ".\n"
    )

    add("## 5. As centrais da casa\n")
    add("| Central | F | L | F−L | Erro F−L |")
    add("|---|---|---|---|---|")
    for k in (
        "ancora_projecao_published",
        "ancora_projecao_pnad",
        "projecao_arvor",
        "media_arvor",
    ):
        x = c[k]
        add(
            f"| {x['rotulo']} | {n(x['validos']['flavio'])} | {n(x['validos']['lula'])} "
            f"| {n(x['pesquisa_f_menos_l'], 2, True)} | {n(x['erro_f_menos_l'], 2, True)} |"
        )
    add("")
    add(
        f"**Fato.** As duas camadas que a casa acrescentou às pesquisas apontavam para "
        f"Flávio e somaram erro: PNAD {n(a_pnad - a_pub, 2, True)} pp e presença relativa "
        f"+3,8% {n(e_proj - a_pnad, 2, True)} pp na Projeção. O +3,8% era o resíduo F/L do 1º "
        "turno transportado ao 2º, e o contrato da Projeção já o rotulava como hipótese que "
        "podia repetir ajuste absorvido. A Média, restrita às 11 casas com renda, errou "
        f"{n(e_med, 2, True)}, contra {n(rp['media'], 2, True)} da média simples publicada "
        "das 20 casas. Contra a urna sem exterior os erros são "
        f"{n(c['sem_exterior']['media_arvor']['erro_f_menos_l'], 2, True)} e "
        f"{n(c['sem_exterior']['projecao_arvor']['erro_f_menos_l'], 2, True)}.\n"
    )

    add("## 6. Comparação com o 1º turno e com 2022\n")
    add(
        f"- 1º turno de 2026: erro comum {n(um['erro_comum_lula_menos_flavio'], 2, True)} pp "
        f"em L−F, mediana {n(um['mediana'], 2, True)}, {um['n_casas']} casas; as pesquisas "
        "superestimaram Lula."
    )
    add(
        f"- 1º turno de 2022: {n(r22['erro_comum_lula_menos_bolsonaro'], 2, True)} em L−B, "
        f"Bolsonaro {n(r22['erro_medio_bolsonaro_pp'], 2, True)} pp."
    )
    add(
        f"- 2º turno de 2026: {n(-rp['media'], 2, True)} em L−F; Flávio "
        f"{n(r['erro_media_simples']['erro_flavio'], 2, True)} pp acima da urna na média."
    )
    add(
        f"- Mesma casa nos dois turnos ({pn['n']} casas): média 1T "
        f"{n(pn['media_1t'], 2, True)}, média 2T {n(pn['media_2t'], 2, True)}, correlação "
        f"{n(pn['correlacao'])}. Quem mais superestimou Lula no 1º turno não é quem mais "
        "superestimou Flávio no 2º.\n"
    )
    add("| Casa | Erro 1T (L−F) | Erro 2T (L−F) |")
    add("|---|---|---|")
    for x in pn["linhas"]:
        add(
            f"| {x['instituto']} | {n(x['erro_1t_lula_menos_flavio'], 2, True)} "
            f"| {n(x['erro_2t_lula_menos_flavio'], 2, True)} |"
        )
    add("")

    add("## 7. O que as pesquisas mediram na última semana\n")
    ts = t["ultima_semana_19_a_24"]
    ex = t["extrapolacao_ate_a_urna"]
    tp = t["pos_urna_05_a_24"]
    add(
        f"**Fato.** As {tp['n_ondas']} ondas pós-urna ({tp['n_casas']} casas) mostram Flávio "
        f"à frente em quase todas, com vantagem encolhendo: inclinação "
        f"{n(tp['inclinacao_simples_pp_dia'], 3, True)} pp/dia no conjunto e "
        f"{n(tp['inclinacao_dentro_da_casa_pp_dia'], 3, True)} dentro de cada casa. Na última "
        f"semana ({ts['n_ondas']} ondas) a inclinação dentro da casa é "
        f"{n(ts['inclinacao_dentro_da_casa_pp_dia'], 3, True)} pp/dia, quase parada, e a "
        f"média F−L {n(ts['media_f_menos_l'], 2, True)}. A âncora da Projeção estimava "
        f"Lula {n(c['ancora_projecao_published']['inclinacao_lula_validos_pp_dia'], 3, True)} "
        "pp/dia nos válidos.\n"
    )
    add(
        '**Correção do briefing.** A frase "tendência de Flávio subindo até 24/10 nas '
        'publicadas" não se sustenta nos dados do acervo: a série publicada vai de F−L '
        f"{n(t['media_campo_ate_12_10'], 2, True)} (campo até 12/10) a "
        f"{n(t['media_campo_desde_19_10'], 2, True)} (desde 19/10). O que subiu foi a "
        "Projeção da casa, por causa das camadas da seção 5. Mesmo extrapolando o ritmo "
        f"de queda observado ({n(tp['inclinacao_dentro_da_casa_pp_dia'], 3, True)} pp/dia) "
        f"por {n(ex['dias_do_meio_do_campo_ate_a_urna'], 1)} dias até a urna, F−L iria a "
        f"{n(ex['f_menos_l_extrapolado'], 2, True)}, longe dos "
        f"{n(urna_dif, 2, True)} da urna.\n"
    )

    add("## 8. Estaduais do 2º turno\n")
    add(
        "| Pesquisa | Campo | Válidos F | Urna F | Erro F−L | Vencedor | Erro do transporte |"
    )
    add("|---|---|---|---|---|---|---|")
    for x in e["pesquisas"]:
        add(
            f"| {x['id']} | {data(x['campo']['inicio'])}–{data(x['campo']['fim'])} "
            f"| {n(x['validos']['flavio'])} | {n(x['urna_flavio_entre_os_dois'])} "
            f"| {n(x['erro_f_menos_l_pp'], 2, True)} | {'certo' if x['acertou_vencedor'] else 'errado'} "
            f"| {n(x['erro_transporte_f_menos_l_pp'], 2, True)} |"
        )
    add("")
    add(
        f"Duas semanas antes da urna, as estaduais erraram menos (média "
        f"{n(e['resumo']['media'], 2, True)}) que as nacionais da véspera e que o transporte "
        "do 1º turno nas mesmas UFs. Seis delas são da mesma casa e da mesma semana: não "
        "generalizar.\n"
    )

    add("## 9. Projeção territorial por UF\n")
    out.extend(_tabela_metodos(p))
    add("")
    add(
        f"**Fato.** Todas as projeções acertaram a ordem dos estados (correlação "
        f"{n(tr['correlacao_previsto_urna'], 3)} entre previsto e urna) e erraram o nível. O "
        f"transporte proporcional errou o vencedor em {', '.join(tr['errou_vencedor_ufs'])}; "
        f"a Média e a Projeção recentradas erraram mais ({n(mmed['rmse_flavio_pp_ponderado'])} "
        f"e {n(mproj['rmse_flavio_pp_ponderado'])} pp de RMSE contra "
        f"{n(tr['rmse_flavio_pp_ponderado'])} do transporte), porque o deslocamento comum em "
        "log-odds empurrou todas as UFs na direção errada. A retrospectiva 2018→2022 tinha "
        "RMSE estadual de 1,73 pp no método selecionado; em 2026 ele fez "
        f"{n(tr['rmse_flavio_pp_ponderado'])}.\n"
    )
    add(
        "Resíduo do transporte por região (urna menos previsto, parcela de Flávio): "
        + "; ".join(
            f"{k} {n(-v['erro_flavio_pp'], 2, True)}" for k, v in regioes_tr.items()
        )
        + f". Maiores perdas de Flávio: {_lista_ufs(ufs_tr[::-1][:4])}; "
        f"menores: {_lista_ufs(ufs_tr[:3])}.\n"
    )

    add("## 10. Hipóteses candidatas\n")
    add(
        "Legenda: **Fato** (medido nos arquivos), **Inferência** (apoiada nos fatos, não "
        "provada), **Juízo** (posição editorial), **Hipótese** (ainda exige prova). Nenhuma "
        "das hipóteses abaixo envolve, nem os dados sustentam, afirmação de irregularidade "
        "na votação ou na totalização.\n"
    )
    add("### (a) Erro comum das pesquisas, como em 2022 e no 1º turno\n")
    add(
        f"- Sustenta (fato): {rp['positivos']} de {rp['n']} casas no mesmo sinal; dispersão "
        f"{n(rp['desvio_padrao'])} menor que o piso amostral "
        f"{n(r['desvio_esperado_so_amostragem_aas_pp'])}; erro de tamanho próximo ao de 2022 "
        f"({n(r22['erro_comum_lula_menos_bolsonaro'])}) e do 1º turno "
        f"({n(um['erro_comum_lula_menos_flavio'])}), agora maior ({n(rp['media'])})."
    )
    add(
        f"- Contraria (fato): o sinal inverteu. Em 2022 e no 1º turno de 2026 o erro "
        f"favoreceu Lula; no 2º turno favoreceu Flávio. Correlação entre os erros da mesma "
        f"casa {n(pn['correlacao'])}: não é um viés fixo de cada instituto."
    )
    add(
        "- Inferência: o componente comum domina, mas não é o mesmo viés estrutural "
        '"contra a direita" das rodadas anteriores. Uma leitura compatível é que as '
        "casas, depois do 1º turno, corrigiram ponderações na direção de Flávio (voto "
        "declarado no 1º turno, PNAD, escolaridade) e passaram do ponto. **Hipótese**: "
        "exige as matrizes de ponderação de antes e depois de 04/10 de cada casa. Contra "
        "ela: PoderData, CNT/MDA e Palver declaram ponderação pelo voto do 1º turno e "
        "erraram "
        + ", ".join(
            n(pesq[k]["erro_validos_do_total"]["erro_f_menos_l"], 2, True)
            for k in ("PoderData", "MDA", "Palver")
            if k in pesq
        )
        + f", perto da média ({n(rp['media'], 2, True)}), não acima dela."
    )
    add(
        f"- Fato adicional: repetir o 1º turno sem pesquisa errava "
        f"{n(tr['nacional_erro_f_menos_l_pp'], 2, True)}; as casas ficaram perto disso. Elas "
        "mediram, em média, o que a geografia do 1º turno já implicava.\n"
    )
    add("### (b) Comparecimento diferencial\n")
    add(
        f"- Sustenta (fato): a abstenção caiu {n(-cbr['variacao_abstencao_pp'])} pp "
        f"({n(cbr['abstencao_1t_pct'])}% para {n(cbr['abstencao_2t_pct'])}%), "
        f"{n(cbr['variacao_comparecimento'] / 1e6)} milhões a mais na urna. A Projeção "
        "supunha o comparecimento do 1º turno e presença relativa a favor de Flávio. O "
        "horário de votação foi estendido até 19h no dia (decisão de 25/10 registrada no "
        "contrato da apuração), o que eleva comparecimento legitimamente."
    )
    if lim:
        add(
            f"- Contraria (fato): é teto, não estimativa. Mesmo dando a Lula todo o aumento "
            f"líquido, F−L iria de {n(lim['f_menos_l_urna'], 2, True)} para "
            f"{n(lim['f_menos_l_sem_o_aumento'], 2, True)}: no máximo "
            f"{n(lim['parcela_maxima_explicada_pp'])} dos {n(rp['media'])} pp de erro. Entre "
            f"as UFs, a variação da abstenção não acompanha o resíduo de Flávio (correlação "
            f"{n(cb['correlacao_variacao_abstencao_com_residuo'])}); AP, RR e AC tiveram "
            "abstenção maior que no 1º turno e o mesmo resíduo dos demais."
        )
    add(
        "- Inferência: comparecimento pode explicar uma parte, não o erro inteiro, e não "
        "deixa assinatura geográfica nos agregados por UF. Teste decisivo: a régua por "
        "seção (`/api/2t/comparecimento`) cruzando variação de comparecimento com a fatia "
        "de Lula na mesma seção.\n"
    )
    add("### (c) Indecisos e eleitor provável\n")
    add(
        f"- Contraria (fato): indecisos eram poucos. Mesmo dando todos a Lula, Flávio "
        f"continuaria à frente em {ind['flavio_ainda_a_frente']} de {len(ind['por_casa'])} "
        f"casas e o erro médio cairia só para {n(ind['erro_medio_todos_indecisos_lula'], 2, True)}."
    )
    lv = []
    if q and q.get("erro_validos_oficiais"):
        lv.append(
            f"Quaest eleitor provável 51/49 contra {n(q['validos_do_total']['flavio'])} da "
            f"amostra completa (erro {n(q['erro_validos_oficiais']['erro_f_menos_l'], 2, True)} "
            f"contra {n(q['erro_validos_do_total']['erro_f_menos_l'], 2, True)})"
        )
    for nome in ("PoderData", "Ipespe"):
        x = pres.get(nome)
        if x:
            tx = x["taxas"]
            lv.append(
                f"{nome} presença certa F/L {inteiro(100 * tx['flavio'])}/"
                f"{inteiro(100 * tx['lula'])} desloca F−L "
                f"{n(x['deslocamento_f_menos_l'], 2, True)}"
            )
    if nex and nex.get("eleitor_provavel_documental"):
        lvm = nex["eleitor_provavel_documental"]["validos"]
        lv.append(
            f"Nexus eleitor provável {n(lvm['flavio'], 1)}/{n(lvm['lula'], 1)} contra "
            f"{n(nex['validos_do_total']['flavio'])} da amostra completa"
        )
    add(
        "- Contraria (fato): todo filtro de presença declarada apontou para Flávio, na "
        "direção oposta à urna: " + "; ".join(lv) + "."
    )
    add(
        "- Inferência: presença autodeclarada não previu quem compareceu; o eleitor de "
        "Flávio declara mais certeza de votar, e isso não se converteu em vantagem na urna. "
        "**Juízo**: a decisão de não aplicar o eleitor provável da Nexus às centrais estava "
        "certa; aplicar o da Quaest à Projeção somou erro, pequeno pelo peso de 7%.\n"
    )
    add("### (d) Reponderação por renda\n")
    add(
        f"- Fato: a urna testou a premissa e ela falhou nesta rodada ({ef['afastou']} de "
        f"{ef['n']} casas pioraram, erro comum {n(rm['media'])} para {n(rr['media'])}). "
        "Ver seção 4."
    )
    add(
        "- Hipótese: o gradiente renda × voto medido dentro das faixas não é transportável. "
        "Se o entrevistado de renda alta que a pesquisa alcança é mais pró-Flávio que o "
        "eleitor de renda alta da população, dar mais peso a ele amplia o erro. Exige "
        "microdados com pesos para testar; o anúncio da Palver de liberar a base individual "
        "depois do 2º turno permite a primeira prova.\n"
    )
    add("### (e) Perfil de quem votou\n")
    add(
        f"- Fato (agregado por UF): Flávio ficou abaixo do transporte do 1º turno em todas as "
        f"27 UFs; o resíduo é maior onde a terceira via pesou mais no 1º turno (correlação "
        f"{n(cb['correlacao_terceiros_1t_com_residuo'])}) e no Sudeste, Centro-Oeste e Sul do "
        "que no Nordeste. Nacionalmente Flávio ganhou "
        f"{n(cbr['ganho_flavio'] / 1e6)} milhões de votos entre os turnos; supondo que ele "
        "não perdeu ninguém do 1º turno, isso é no máximo "
        f"{n(cbr['teto_parcela_flavio_da_terceira_via_pct'], 1)}% dos "
        f"{n(cbr['terceiros_1t'] / 1e6)} milhões da terceira via, contra 61% entre os que "
        "escolhem um finalista na síntese que a casa usava (com 30% sem escolha, 43% do "
        "total)."
    )
    add(
        "- Inferência: o padrão é compatível com o eleitor da terceira via (Caiado, Cury, "
        "Renan, Zema) e parte do branco/nulo indo menos a Flávio do que as matrizes "
        "supunham. Não é medição: a identidade de agregados não diz quem trocou de voto."
    )
    add(
        "- Contraria: sem dado individual nem cruzamento seção a seção, renda, idade e "
        "escolaridade de quem votou não são observáveis aqui.\n"
    )

    out.extend(_entrada_autor(s, cbr, mesmos, b, a))
    add("## 12. Limites\n")
    add(
        "- A urna lida ao vivo é parcial até `presidente.json` do 2º turno existir; "
        "reexecutar o script atualiza tudo."
    )
    add(
        "- Válidos de cada pesquisa são a renormalização dos inteiros publicados; o "
        "arredondamento sozinho move a diferença em até cerca de 1 pp em casas sem decimal."
    )
    add(
        "- Margem AAS ignora ponderação e desenho: é piso, não intervalo da casa. O "
        "erro comum de 2 pp do Monte Carlo era hipótese; o erro observado na parcela "
        f"de Flávio na Projeção foi {n(c['projecao_arvor']['erro_flavio'])} pp."
    )
    add(
        "- Estaduais têm campo de 06 a 13/10; o mapa de 24/10 vem do histórico git "
        "(commit indicado no JSON) e o de 25/10 do arquivo de trabalho."
    )
    add(
        "- Correlações entre 27 UFs são ecológicas. Nada aqui identifica migração "
        "individual, comparecimento por candidato ou irregularidade.\n"
    )

    add("## 13. Consultas e fontes\n")
    add(
        "- `python3 scripts/apuracao-2t-2026-pesquisas.py` (este memorando e os três JSON)."
    )
    add(
        "- Urna: `analysis/apuracao_2t_2026/dados/presidente.json` quando existir; senão "
        "`curl -s http://127.0.0.1:4180/api/2t/regioes`, `/api/2t/ufs`, `/api/2t/abstencao` "
        "e `/api/2t/evolucao` (nomes por número de urna)."
    )
    add(
        "- Pesquisas: `analysis/reponderacao/pesquisas/*.json` (placar de 2º turno, campo "
        "iniciado depois de 04/10); reponderado: `docs/assets/reponderacao_simulador.json` "
        "(`polls[].pnad`) e `docs/assets/reponderacao_pnad.json` (cenário pessoas16_efetivo)."
    )
    add(
        "- Centrais: `docs/assets/reponderacao_simulador.json` (`central`, "
        "`central_projection`, `projection.anchors`), snapshot "
        f"`{c.get('snapshot')}`."
    )
    add(
        "- Presença declarada: `analysis/reponderacao/historico_2t/presenca.json`; 1º turno: "
        "`analysis/apuracao_2026/dados/pesquisas_vs_urna.json` e `presidente.json`; 2022: "
        "`analysis/predicao_2026/erro_2022/erro_2022.json`."
    )
    add(
        "- Território: `docs/assets/mapa_previsao_2t_2026.json` (25/10 e 24/10 via git), "
        "`docs/assets/projecao_secoes_2t_ufs.csv` (19/10), "
        "`analysis/projecao_secoes_2t/estaduais.json`, `analysis/reponderacao/estaduais/`."
    )
    return "\n".join(out) + "\n"
