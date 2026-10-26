"""Memorando da análise por seção do 2º turno, gerado só dos números gravados."""

from __future__ import annotations

from typing import Any


def _n(v: Any) -> str:
    """Número no padrão brasileiro: milhar com ponto, 2 decimais com vírgula."""
    if v is None:
        return "sem dado"
    if isinstance(v, bool):
        return "sim" if v else "não"
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _sinal(v: dict[str, Any], nome: str) -> dict[str, Any]:
    return next(s for s in v["sinais"] if s["sinal"] == nome)


def _linha_voto(s: dict[str, Any]) -> str:
    if "dif_fatia_flavio_vs_vizinhas_pp" not in s:
        return f"| {s['descricao']} | {_n(s['n_sinal_total'])} | n abaixo de 20 | | | |"
    did = s.get("did_fatia_flavio_pp")
    ep = s.get("ep_did_fatia_flavio_pp")
    return (
        f"| {s['descricao']} | {_n(s['n_sinal_total'])} | "
        f"{_n(s['dif_fatia_flavio_vs_vizinhas_pp'])} "
        f"(ep {_n(s['ep_fatia_flavio_vs_vizinhas_pp'])}; n {_n(s['n_sinal_comparavel'])} "
        f"contra {_n(s['n_vizinhas'])} em {_n(s['n_municipios'])} municípios) | "
        f"{_n(s.get('delta_fatia_flavio_vs_1t_pp'))} | {_n(did)} (ep {_n(ep)}; "
        f"n {_n(s['n_did'])}) | {_n(s['dif_lula_no_comp_vs_vizinhas_pp'])} |"
    )


def memorando(s: dict[str, Any], v: dict[str, Any], r: dict[str, Any]) -> str:
    b = s["agregados"]["brasil"]
    p = s["prorrogacao"]["brasil"]
    dc, sb, an = b["delta_comp"], b["sem_biometria"], b["ano_nascimento"]
    enc, per, sal = b["encerramento"], b["persistencia"], b["salto_biometria"]
    e1 = s.get("enc_1t_pct") or {}
    fonte = s["fonte"]
    L: list[str] = []
    a = L.append
    a("# Análise por seção do 2º turno de 2026: comparecimento, biometria e horário")
    a("")
    a(f"> {s['rotulo']}")
    a("")
    a(
        f"Gerado em {s['gerado_em']} sobre a fonte **{fonte}** (`{s['banco']}`), "
        f"{_n(s['totais']['secoes'])} seções com BU, {_n(s['totais']['com_ref_1t'])} "
        f"com a mesma seção na régua do 1T. Último recebimento lido: "
        f"{s['max_recebido_hhmm']} de Brasília. Régua do 1T: `{s['regua_1t']}` "
        f"(SHA-256 `{s['regua_1t_sha256'][:16]}`, gerada em {s['regua_1t_gerada_em']})."
    )
    if fonte == "amostra":
        a("")
        a(
            "A amostra foi sorteada antes da votação (semente fixa, cota por município "
            "proporcional ao número de seções, autoponderada dentro da UF): 150 seções "
            "por UF, mais 600 nas seis UFs com governador, e as da totalização paralela, "
            "que entram nas tabelas mas não nas estimativas. Toda seção sorteada tem BU. "
            "As somas brutas da amostra pesam demais as UFs pequenas; o país sai da "
            "seção Estimativa nacional, ponderada pelas seções de cada UF."
        )
    a("")
    a("## Método")
    a("")
    rg = s["regras"]
    a(
        f"Cada seção é comparada com ela mesma no 1º turno. Seis sinais: (1) "
        f"comparecimento/aptos ao menos {rg['delta_pp_min']} pp acima do 1T; (2) sem "
        f"biometria cadastrada ≥ {rg['sem_bio_min_pct']}% e ≥ {rg['sem_bio_fator']}x a "
        f"mediana do município no 1T; (3) habilitados por ano de nascimento (biometria "
        f"cadastrada e não reconhecida) ≥ {rg['ano_nasc_min_pct']}% e ≥ "
        f"{rg['ano_nasc_fator']}x a mediana municipal; (4) salto: a soma das duas "
        f"parcelas ≥ {rg['salto_bio_min_pct']}% e {rg['salto_bio_pp_min']} pp acima da "
        f"própria seção no 1T; (5) tardia: último voto depois das 19:00 de Brasília ou "
        f"{rg['tardia_min_vs_1t']} min depois do da própria seção no 1T; (6) BU do "
        f"sistema de apuração. Os sinais 1, 2, 5 e 6 formam o escore 0 a 4 da rota "
        f"`/api/2t/comparecimento`; esta análise soma 3 e 4 (escore 0 a 6). "
        f"Contingência e encerramento depois das 17:00 são descrição."
    )
    a("")
    a(
        "Horas: a do BU é local; converte pelo fuso da UF e depois corrige por "
        "município pela abertura modal (a votação abriu às 08:00 de Brasília em todo o "
        f"país). {_n(len(s['fuso']['municipios_corrigidos']))} municípios corrigidos "
        "(oeste do Amazonas); a régua do 1T recebe a mesma correção. Conferência: com o "
        "fuso só da UF, as contagens repetem as da rota: "
        + ", ".join(f"{k} {_n(v)}" for k, v in s["conferencia_api_fuso_uf"].items())
        + "."
    )
    a("")
    a(
        "Voto: fatia de Flávio entre os dois (F/(F+L)). Toda comparação é dentro do "
        "município (seções com sinal contra as demais do mesmo município, média "
        "ponderada pelos votos das seções com sinal) e contra a própria seção no 1T "
        "(diferença em diferenças). Diferença só com n ≥ 20; o erro-padrão (ep) é "
        "aproximado, entre municípios."
    )
    a("")
    en = s.get("estimativa_nacional") or {}
    ind = {i["indicador"]: i for i in en.get("indicadores", [])}
    if en.get("disponivel"):
        a("## Estimativa nacional (amostra estratificada por UF)")
        a("")
        a(
            f"{_n(en['n'])} seções sorteadas em {_n(en['ufs'])} UFs, pesos pelas "
            f"{_n(en['secoes_universo'])} seções do 1T; IC de 95% estratificado."
        )
        a("")
        a("| indicador | estimativa | IC 95% | seções no país |")
        a("|---|---|---|---|")
        for i in en["indicadores"]:
            val = f"{_n(i['pct'])}%" if "pct" in i else f"{_n(i['valor'])} pp"
            a(
                f"| {i['descricao']} | {val} | {_n(i['ic95'][0])} a {_n(i['ic95'][1])} | "
                f"{_n(i.get('secoes_estimadas'))} |"
            )
        a("")
    a("## As seções ficaram abertas até 19h?")
    a("")
    a(
        f"Não, na quase totalidade. O último voto tem mediana {p['encerramento_p50']}, "
        f"p90 {p['encerramento_p90']} e p99 {p['encerramento_p99']}; "
        f"{_n(p['pct_ate_1715'])}% encerraram até 17:15 e só {_n(p['pct_apos_1900'])}% "
        f"({_n(p['n_apos_1900'])} seções) depois das 19:00. O BU foi emitido "
        f"{_n(p['emissao_menos_encerramento_p50_min'])} min depois do último voto "
        f"(mediana; p90 {_n(p['emissao_menos_encerramento_p90_min'])} min): emissão "
        f"mediana {p['emissao_p50']}, {_n(p['pct_bu_emitido_ate_1730'])}% emitidos até "
        f"17:30. Emitir o BU fecha a urna. O que demorou foi o recebimento: mediana "
        f"{p['recebimento_p50']}, só {_n(p['pct_recebido_antes_1900'])}% recebidos "
        f"antes das 19:00, intervalo encerramento→recebimento de "
        f"{_n(p['lag_encerramento_recebimento_p50_min'])} min na mediana (p90 "
        f"{_n(p['lag_encerramento_recebimento_p90_min'])})."
    )
    a("")
    a(
        f"Contra o 1T nas mesmas seções, o 2T fechou mais cedo: depois das 18:00, "
        f"{_n(p['pct_apos_1800'])}% contra {_n(p['pct_apos_1800_1t_mesmas'])}%; depois "
        f"das 19:00, {_n(p['pct_apos_1900'])}% contra {_n(p['pct_apos_1900_1t_mesmas'])}%. "
        f"No universo do 1T: {_n(e1.get('apos_1700'))}% depois de 17:00, "
        f"{_n(e1.get('apos_1800'))}% depois de 18:00 e {_n(e1.get('apos_1900'))}% "
        f"depois de 19:00. O 2T tem um ou dois cargos contra seis no 1T, e a fila anda "
        f"mais rápido. Leitura: a extensão até 19h não deixou urnas abertas; a "
        f"urna fechou quando acabou a fila e o BU ficou à espera de transmissão. Quem "
        f"atribuir a alta de comparecimento à prorrogação precisa mostrar seção que "
        f"encerrou depois das 17h; na fonte lida são {_n(enc['n_tardias'])} tardias de "
        f"{_n(enc['n'])}. Por que o recebimento começou perto das 19h (regra de "
        f"transmissão ou ordem do TSE) não está nos BUs: é pergunta à Justiça Eleitoral."
    )
    a("")
    a(
        "| UF | n | último voto p50 | p90 | depois 19:00 | BU emitido p50 | "
        "1º recebimento | recebido antes 19:00 | atraso p50 (min) |"
    )
    a("|---|---|---|---|---|---|---|---|---|")
    for u in s["prorrogacao"]["por_uf"]:
        a(
            f"| {u['uf']} | {_n(u['n'])} | {u['encerramento_p50']} | "
            f"{u['encerramento_p90']} | {_n(u['pct_apos_1900'])}% | {u['emissao_p50']} | "
            f"{u['recebimento_primeiro']} | {_n(u['pct_recebido_antes_1900'])}% | "
            f"{_n(u['lag_encerramento_recebimento_p50_min'])} |"
        )
    a("")
    a("## Números por sinal")
    a("")
    if fonte == "amostra":
        a(
            "Somas brutas da fonte lida, sem peso por UF: servem para os sinais e a "
            "persistência; o nível do país está na Estimativa nacional."
        )
        a("")
    a(
        f"- Comparecimento: {_n(dc['comp_2t_pct'])}% no 2T contra {_n(dc['comp_1t_pct'])}% "
        f"nas mesmas seções no 1T; diferença por seção p10 {_n(dc['p10'])}, p50 "
        f"{_n(dc['p50'])}, p90 {_n(dc['p90'])} pp (n {_n(dc['n'])}). "
        f"{_n(dc['pct_5_mais'])}% das seções subiram 5 pp ou mais; "
        f"{_n(dc['pct_menos_5'])}% caíram 5 pp ou mais; {_n(dc['pct_10_mais'])}% "
        f"subiram 10 pp ou mais."
    )
    a(
        f"- Sem biometria cadastrada: {_n(sb['pct_2t'])}% dos votantes no 2T contra "
        f"{_n(sb['pct_1t_mesmas'])}% no 1T; {_n(sb['n_sinal'])} seções com sinal, das "
        f"quais {_n(per['sem_bio_ja_no_1t'])} já tinham o mesmo sinal no 1T (variação "
        f"mediana {_n(per['sem_bio_dif_p50_pp'])} pp)."
    )
    a(
        f"- Ano de nascimento: {_n(an['pct_2t'])}% no 2T contra {_n(an['pct_1t_mesmas'])}% "
        f"no 1T; {_n(an['n_sinal'])} seções com sinal, {_n(per['ano_nasc_ja_no_1t'])} "
        f"já com o sinal no 1T (variação mediana {_n(per['ano_nasc_dif_p50_pp'])} pp)."
    )
    a(
        f"- Salto da parcela sem biometria reconhecida contra a própria seção: "
        f"{_n(sal['n_sinal'])} seções (variação p50 {_n(sal['p50_salto_pp'])} pp, p90 "
        f"{_n(sal['p90_salto_pp'])}); salto junto com comparecimento +5 pp: "
        f"{_n(sal['n_comparecimento_e_salto'])} seções."
    )
    a(
        f"- Tardias: {_n(enc['n_tardias'])}, das quais {_n(enc['n_apos_19h'])} depois "
        f"das 19:00. Contingência ou mais de uma carga: {_n(b['urna']['contingencia'])}. "
        f"BU do sistema de apuração: {_n(b['urna']['sistema_apuracao'])}."
    )
    a(
        "- Escore (0 a 6): "
        + ", ".join(f"{k}: {_n(v)}" for k, v in b["escore"].items())
        + f"; 2 ou mais: {_n(b['escore_2_mais'])}."
    )
    a("")
    a("## Relação com o voto (dentro do município)")
    a("")
    a(
        "| Sinal | seções | fatia F contra vizinhas (pp) | fatia F 2T−1T nas seções "
        "(pp) | diferença em diferenças (pp) | Lula no comparecimento contra vizinhas (pp) |"
    )
    a("|---|---|---|---|---|---|")
    for x in v["sinais"]:
        a(_linha_voto(x))
    a("")
    a("Comparecimento alto × biometria baixa × fatia de Flávio contra o 1T:")
    a("")
    a(
        "| comp. +5 pp | biometria baixa | n | F subiu | F não subiu | fatia F 2T−1T (pp) |"
    )
    a("|---|---|---|---|---|---|")
    for c in v["tabela_2x2x2"]:
        a(
            f"| {_n(c['comparecimento_alto'])} | {_n(c['biometria_baixa'])} | {_n(c['n'])} "
            f"| {_n(c['n_flavio_sobe'])} | {_n(c['n_flavio_nao_sobe'])} | "
            f"{_n(c.get('delta_fatia_flavio_pp'))} |"
        )
    va = v["votos_absolutos"]
    c10 = va["comparecimento_10pp"]
    a("")
    a(
        f"Votos absolutos contra o 1T (n {_n(va['n'])}): Flávio ganhou votos em "
        f"{_n(va['flavio_ganhou']['pct'])}% das seções e Lula em "
        f"{_n(va['lula_ganhou']['pct'])}%; Flávio ganhou e Lula perdeu em "
        f"{_n(va['flavio_ganhou_lula_perdeu']['n'])} seções, o inverso em "
        f"{_n(va['lula_ganhou_flavio_perdeu']['n'])}. Ganho médio por seção: Flávio "
        f"{_n(va['ganho_medio_flavio'])}, Lula {_n(va['ganho_medio_lula'])} votos. "
        f"Seções com comparecimento +10 pp: {_n(c10['n'])} (Lula ganhou mais em "
        f"{_n(c10['lula_ganhou_mais'])}, Flávio em {_n(c10['flavio_ganhou_mais'])})."
    )
    a("")
    d = _sinal(v, "delta")
    sbv = _sinal(v, "sinal_sem_bio")
    tv = _sinal(v, "tardia")
    salv = _sinal(v, "sinal_salto_bio")
    a("## O que pede explicação")
    a("")
    rs0 = r["secoes"]
    pian = [x for x in rs0 if "delta" in x["sinais"] and "salto_bio" in x["sinais"]]
    if ind:
        pi = ind["pianista"]
        a(
            f"- Comparecimento +5 pp junto com salto da parcela sem biometria "
            f"reconhecida, a combinação mais próxima da hipótese do mesário que libera "
            f"ausente: {_n(sal['n_comparecimento_e_salto'])} seções na fonte lida, "
            f"{_n(pi['pct'])}% do país (IC {_n(pi['ic95'][0])} a {_n(pi['ic95'][1])}), "
            f"cerca de {_n(pi['secoes_estimadas'])} seções; {_n(len(pian))} delas estão "
            f"no ranking."
        )
    maior = max(rs0, key=lambda x: x["salto_bio_pp"] or 0, default=None)
    if maior and (maior["salto_bio_pp"] or 0) >= 20:
        a(
            f"- Maior salto de biometria: {maior['municipio']} ({maior['uf']}), zona "
            f"{maior['zona']}, seção {maior['secao']}: +{_n(maior['salto_bio_pp'])} pp "
            f"na parcela sem biometria reconhecida contra o 1T, com comparecimento "
            f"{_n(maior['delta_comp_pp'])} pp; habilitados por ano de nascimento "
            f"{_n(maior['ano_nasc_pct_1t'])}% no 1T e {_n(maior['ano_nasc_pct_2t'])}% no "
            f"2T. Votos Flávio × Lula: {_n(maior['flavio_1t'])} × {_n(maior['lula_1t'])} "
            f"no 1T, {_n(maior['flavio_2t'])} × {_n(maior['lula_2t'])} no 2T. Padrão de "
            f"leitor biométrico que não reconheceu a seção inteira, hipótese a conferir "
            f"no log. Classificação: {maior['explicacao_provavel']}."
        )
    fortes = [
        x
        for x in v["sinais"]
        if x.get("ep_did_fatia_flavio_pp")
        and abs(x["did_fatia_flavio_pp"]) > 2 * x["ep_did_fatia_flavio_pp"]
    ]
    if fortes:
        a(
            "- Diferença em diferenças na fatia de Flávio maior que duas vezes o "
            "erro-padrão: "
            + "; ".join(
                f"{x['descricao']}, {_n(x['did_fatia_flavio_pp'])} pp (ep "
                f"{_n(x['ep_did_fatia_flavio_pp'])}, n {_n(x['n_did'])})"
                for x in fortes
            )
            + ". São deslocamentos de menos de um ponto, na direção de Lula quando "
            "negativos; não identificam mecanismo."
        )
    a("")
    a("## Achados que contrariam a tese")
    a("")
    dr = _sinal(v, "delta_relativo")
    if ind:
        md, d5, dr5 = ind["media_delta_pp"], ind["delta"], ind["delta_relativo"]
        a(
            f"- A alta de comparecimento é geral, não pontual: no país a seção subiu "
            f"{_n(md['valor'])} pp em média (IC {_n(md['ic95'][0])} a "
            f"{_n(md['ic95'][1])}). As seções com +5 pp são {_n(d5['pct'])}% do país, "
            f"mas só {_n(dr5['pct'])}% ficam 5 pp acima da alta mediana do próprio "
            f"município ou UF."
        )
    quedas = [
        f"{u['uf']} {_n(u['delta_comp']['media'])} pp"
        for u in s["agregados"]["por_uf"]
        if (u["delta_comp"]["media"] or 0) <= -3
    ]
    if quedas:
        a(
            "- Em algumas UFs o comparecimento caiu contra o 1T (média por seção): "
            + ", ".join(quedas)
            + "."
        )
    if "did_fatia_flavio_pp" in dr:
        a(
            f"- As seções com alta acima da local são mais favoráveis a Lula que as "
            f"vizinhas ({_n(dr['dif_fatia_flavio_vs_vizinhas_pp'])} pp na fatia de "
            f"Flávio, n {_n(dr['n_sinal_comparavel'])}), mas já eram no 1T: a diferença "
            f"em diferenças é {_n(dr['did_fatia_flavio_pp'])} pp (ep "
            f"{_n(dr['ep_did_fatia_flavio_pp'])}, n {_n(dr['n_did'])})."
        )
    a(
        f"- Biometria baixa é estrutural, não do dia: {_n(per['sem_bio_ja_no_1t'])} das "
        f"{_n(per['sem_bio_n'])} seções com sinal de sem biometria já o tinham no 1T, "
        f"com variação mediana de {_n(per['sem_bio_dif_p50_pp'])} pp."
    )
    a(
        f"- As seções com sinal votam diferente das vizinhas porque já votavam assim: "
        f"comparecimento +5 pp tem fatia de Flávio "
        f"{_n(d.get('dif_fatia_flavio_vs_vizinhas_pp'))} pp contra as vizinhas, mas a "
        f"diferença em diferenças contra o 1T é {_n(d.get('did_fatia_flavio_pp'))} pp "
        f"(ep {_n(d.get('ep_did_fatia_flavio_pp'))}); sem biometria, "
        f"{_n(sbv.get('dif_fatia_flavio_vs_vizinhas_pp'))} e "
        f"{_n(sbv.get('did_fatia_flavio_pp'))} pp; salto de biometria, "
        f"{_n(salv.get('did_fatia_flavio_pp'))} pp (n {_n(salv['n_did'])})."
    )
    a(
        f"- As tardias são seções mais favoráveis a Flávio que as vizinhas "
        f"({_n(tv.get('dif_fatia_flavio_vs_vizinhas_pp'))} pp), sem mudança relativa "
        f"contra o 1T ({_n(tv.get('did_fatia_flavio_pp'))} pp, n {_n(tv['n_did'])})."
    )
    a(
        "- Nenhuma diferença acima mede fraude nem intenção: sinal pede explicação, "
        "não prova irregularidade."
    )
    a("")
    a("## As mais atípicas")
    a("")
    rs = r["secoes"]
    a(
        f"{_n(len(rs))} seções em `secoes_ranking.json`, por escore e magnitude; "
        f"{_n(sum(1 for x in rs if x['sem_explicacao']))} sem explicação provável pela "
        f"regra. As dez primeiras:"
    )
    a("")
    a(
        "| UF | município | zona | seção | escore | sinais | comp. 2T−1T (pp) | "
        "salto biometria (pp) | último voto 1T → 2T | explicação provável |"
    )
    a("|---|---|---|---|---|---|---|---|---|---|")
    for x in rs[:10]:
        a(
            f"| {x['uf']} | {x['municipio']} | {x['zona']} | {x['secao']} | "
            f"{x['escore']} | {', '.join(x['sinais'])} | {_n(x['delta_comp_pp'])} | "
            f"{_n(x['salto_bio_pp'])} | {x['encerramento_1t']} → {x['encerramento_2t']} "
            f"| {x['explicacao_provavel']} |"
        )
    a("")
    a("## Limites e o que só o banco completo responde")
    a("")
    a(
        "- Amostra de 150 seções por UF: não estima o país nem localiza o caso raro; "
        "seções com sinal são poucas por UF e as diferenças por UF ficam abaixo de n 20."
    )
    a(
        "- Só o banco completo dá: a contagem nacional de cada sinal; a vizinhança do "
        "mesmo local de votação (salto de biometria em várias seções do mesmo prédio "
        "indica leitor ou rede, não mesário); a distribuição municipal com n suficiente; "
        "as seções agregadas e as urnas trocadas em todo o país."
    )
    a(
        "- BU não diz quem votou: só a ata, o caderno de votação e o log da urna separam "
        "falha de leitor, eleitor sem biometria e liberação indevida."
    )
    a(
        "- Os votos de Flávio e Lula no 1T vêm da seção principal no Politize; seção "
        "agregada entre os turnos distorce a comparação (a explicação provável avisa)."
    )
    a("")
    a(
        "Rodar sobre o banco completo, sem mudar código: "
        "`python3 scripts/apuracao-2t-2026-secoes.py --fonte completo` (ou `--fonte auto`, "
        "que o escolhe quando cobre 90% das seções do 1T)."
    )
    a("")
    return "\n".join(L)
