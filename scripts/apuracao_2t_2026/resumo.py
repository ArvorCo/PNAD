"""Memorando `resumo.md`: os números fortes, de onde saíram, o que contraria a tese e os limites.

Todo número vem dos produtos já montados (nada digitado à mão); cada achado diz o
arquivo e o campo, e a consulta de origem no banco quando há uma.
"""

from __future__ import annotations

from typing import Any

from .base import ROTULO


def n(x: float | int | None) -> str:
    """Número no formato brasileiro: milhar com ponto, decimal com vírgula."""
    if x is None:
        return "n/d"
    if isinstance(x, int):
        return f"{x:,}".replace(",", ".")
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pp(x: float | None) -> str:
    if x is None:
        return "n/d"
    return ("+" if x > 0 else "") + n(x)


def _linhas(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [dict(zip(doc["colunas"], r, strict=True)) for r in doc["linhas"]]


def escrever(produtos: dict[str, dict[str, Any]], meta: dict[str, Any]) -> str:
    pres = produtos["presidente.json"]
    lt = produtos["linha_do_tempo.json"]
    ct = produtos["cedo_tarde.json"]
    c1 = produtos["comparacao_1t.json"]
    c22 = produtos["comparacao_2022.json"]
    ab = produtos["abstencao.json"]
    ext = produtos["exterior.json"]
    gov = produtos["governadores.json"]
    pj = produtos["projecao_noite.json"]
    par = produtos["paralela.json"]
    nac = pres["nacional"]
    s: list[str] = []
    w = s.append
    w("# Apuração do 2º turno de 2026: números do dossiê")
    w("")
    w(
        f"Gerado por `scripts/apuracao-2t-2026-dados.py` em {meta['gerado_em']}, a partir "
        f"da versão nacional gerada pelo TSE às {meta['versao_nacional_gerada_brt']} "
        f"(snapshot {meta['versao_nacional_snapshot_id']}, {n(nac['pst'])}% das seções). "
        "Banco `apuracao/data/apuracao-2t.sqlite` lido em modo somente leitura; versão "
        "vigente de cada arquivo = a mais nova pelo `gerado_em`."
    )
    w("")
    w(f"Rótulo de todo o conjunto: {ROTULO}.")
    w("")
    # ------------------------------------------------------------ placar
    w("## 1. Placar")
    w("")
    w(
        f"- Brasil (arquivo nacional `{nac['arquivo']}`): Lula {n(nac['lula'])} "
        f"({n(nac['pct_lula'])}% dos válidos) × Flávio {n(nac['flavio'])} "
        f"({n(nac['pct_flavio'])}%), diferença de {n(nac['margem_lula_votos'])} votos "
        f"({n(nac['margem_lula_pp'])} pp). Seções {n(nac['secoes'])} de "
        f"{n(nac['secoes_total'])}. Brancos {n(nac['brancos'])} ({n(nac['pct_brancos'])}% "
        f"do comparecimento), nulos {n(nac['nulos'])} ({n(nac['pct_nulos'])}%). "
        f"Abstenção {n(nac['pct_abstencao'])}% do eleitorado das seções totalizadas. "
        "Origem: `presidente.json`, `nacional` (tabelas `snapshot`, `totais`, "
        "`voto_candidato`)."
    )
    se = pres["sem_exterior"]
    zz = pres["exterior"]
    w(
        f"- Sem o exterior: Lula {n(se['pct_lula'])}% × Flávio {n(se['pct_flavio'])}%, "
        f"abstenção {n(se['pct_abstencao'])}%. Exterior: Lula {n(zz['pct_lula'])}% × "
        f"Flávio {n(zz['pct_flavio'])}%, abstenção {n(zz['pct_abstencao'])}%."
    )
    for r in pres["regioes"]:
        w(
            f"- {r['regiao']}: Lula {n(r['pct_lula'])}% × Flávio {n(r['pct_flavio'])}% "
            f"(Lula menos Flávio: {n(r['margem_lula_votos'])} votos), abstenção "
            f"{n(r['pct_abstencao'])}%."
        )
    norte = next(r for r in pres["regioes"] if r["regiao"] == "Norte")
    w(
        f"- Achado: o Norte terminou empatado em {n(norte['pct_lula'])}% a "
        f"{n(norte['pct_flavio'])}%, com {n(abs(norte['margem_lula_votos']))} votos de "
        "diferença em "
        f"{n(norte['validos'])} válidos."
    )
    conf = pres["conferencia"]
    w(
        f"- Conferência: soma das UFs menos nacional = {conf['soma_ufs_menos_nacional']}; "
        f"soma dos municípios menos nacional = {conf['soma_municipios_menos_nacional']}. "
        "Diferença não nula enquanto há seções por totalizar é defasagem entre "
        "versões geradas em instantes diferentes. Municípios incompletos: "
        f"{len(conf['municipios_incompletos'])}."
    )
    w("")
    # ------------------------------------------------------------ fatos da noite
    w("## 2. Os fatos da noite conferidos contra o banco")
    w("")
    minuto_2123 = [
        r
        for r in _linhas(lt["nacional"]["serie"])
        if r["gerado_brt"].startswith("2026-10-25 21:23")
    ]
    for v in minuto_2123:
        w(
            f"- Versão nacional gerada às {v['gerado_brt'][11:]}: {n(v['pst'])}% das "
            f"seções, Lula {n(v['lula'])} × Flávio {n(v['flavio'])}. "
            "Origem: `linha_do_tempo.json`, `nacional.serie`."
        )
    sil = lt["pausas"]["silencio_geral"]
    mai = lt["pausas"]["maior_lacuna_nacional"]
    if sil and mai:
        w(
            f"- Parada: o arquivo nacional não teve versão nova entre {mai['de_brt'][11:]} "
            f"e {mai['ate_brt'][11:]} ({n(mai['minutos'])} min; seções de "
            f"{n(mai['st_antes'])} para {n(mai['st_depois'])}). Em todo o banco (resultado, "
            f"andamento e configuração dos dois pleitos), nenhum arquivo tem hora de "
            f"geração entre {sil['ultimo_gerado_antes_brt'][11:]} e "
            f"{sil['primeiro_gerado_depois_brt'][11:]} ({n(sil['minutos'])} min, "
            f"{sil['versoes_geradas_dentro']} versões); o coletor fez "
            f"{n(sil['leituras_no_intervalo'])} leituras nesse intervalo "
            f"({sil['leituras_por_classe']}). Consulta: `SELECT MAX(gerado_em) FROM "
            "snapshot WHERE gerado_em < meio` e `MIN(gerado_em) ... > meio`."
        )
    geral = lt["pausas"]["parada_geral"]
    if geral:
        w(
            f"- A tabela `pausa` do coletor registra a pausa geral de {geral['de_brt'][11:]} "
            f"a {geral['ate_brt'][11:]} ({n(geral['minutos'])} min)."
        )
    w(f"- Prorrogação: {lt['contexto_externo']['prorrogacao_stf']}.")
    ufp = [p for p in lt["pausas"]["tabela_do_coletor"] if p["nivel"] == "uf"]
    for p in ufp:
        if p["ate_brt"] is None:
            w(
                f"- Pausa de UF {p['uf']}: desde {p['de_brt'][11:16]}, em aberto na rodada "
                f"(seções antes: {n(p['st_antes'])})."
            )
            continue
        w(
            f"- Pausa de UF {p['uf']}: {p['de_brt'][11:16]} a {p['ate_brt'][11:16]} "
            f"({n(p['minutos'])} min; seções {n(p['st_antes'])} para {n(p['st_depois'])})."
        )
    marcos = pj.get("marcos_abstencao_comparecimento") or []
    m2130 = next((m for m in marcos if m["hhmm"] == "21:30"), None)
    if m2130:
        b = m2130["abstencao"]["brasil"]
        w(
            f"- Abstenção às 21:30 (rota /api/2t/abstencao, municípios fechados): "
            f"{n(b['pa_2t'])}% contra {n(b['pa_1t_mesmos'])}% nos mesmos municípios no "
            f"1º turno ({n(b['n_mun_fechados'])} municípios)."
        )
    bab = ab["brasil"]
    w(
        f"- Abstenção final, {n(bab['n_municipios'])} municípios completos sem exterior: "
        f"{n(bab['pa_2t'])}% contra {n(bab['pa_1t_mesmos'])}% no 1º turno e "
        f"{n(bab['pa_2022_2t_mesmos'])}% no 2º turno de 2022 nos mesmos municípios. "
        "Origem: `abstencao.json`, `brasil`."
    )
    rk = ab["ranking_ufs_menor_abstencao"][:7]
    w(
        "- Menores abstenções por UF (arquivo de UF, versão vigente): "
        + "; ".join(f"{r['uf']} {n(r['pa_2t'])}%" for r in rk)
        + ". Os valores citados na noite (CE 14,8, PE 15,3, SE 15,6, PB 15,9, RN 16,4, "
        "SC 16,9) não coincidem com a versão vigente; a diferença pode vir da hora da "
        "leitura ou da base (municípios fechados contra arquivo de UF). Na versão "
        "vigente a BA entra entre as seis menores e SC sai."
    )
    w(
        f"- Paralela: {par['recebidos']['bus']} BUs em {par['recebidos']['ufs']} UFs; "
        f"conferência {par['conferencia']}."
    )
    pp0 = pj.get("primeiro_ponto_com_projecao")
    if pp0:
        w(
            f"- Projeção da casa: primeiro ponto com projeção às {pp0['hhmm']} "
            f"({n(pp0['pst'])}% das seções), Flávio {n(pp0['p_f_projetado'])}% entre os "
            f"dois (faixa de 90% de {n(pp0['faixa90'][0])} a {n(pp0['faixa90'][1])}). "
            f"Líder projetado em todos os {pj['pontos_com_projecao']} pontos: "
            f"{', '.join(pj['lider_projetado_em_todos_os_pontos'])}. Final observado: "
            f"Flávio {n(pj['observado_final']['p_f_entre_os_dois'])}%; erro absoluto "
            f"médio {n(pj['erro_absoluto_pp']['medio'])} pp, máximo "
            f"{n(pj['erro_absoluto_pp']['maximo'])} pp."
        )
        lo = pj["pontos_com_flavio_a_frente_no_observado"]
        if lo["n"]:
            w(
                f"- Achado: na contagem observada, Flávio esteve à frente entre {lo['de']} e "
                f"{lo['ate']} ({lo['n']} pontos de 5 min, máximo de "
                f"{n(lo['maximo_p_f_observado'])}% entre os dois), enquanto a projeção "
                "apontava Lula."
            )
        fora = pj["pontos_fora_da_faixa90"]
        if fora:
            w(
                f"- Limite da projeção: o final ficou fora da faixa de 90% em {len(fora)} "
                f"pontos (de {fora[0]['hhmm']} a {fora[-1]['hhmm']}), a no máximo "
                f"{n(max(f['distancia_pp'] for f in fora))} pp; são os pontos finais, com "
                "faixa de largura quase nula."
            )
    w("")
    # ------------------------------------------------------------ tempo
    w("## 3. Cedo contra tarde")
    w("")
    d = ct["decis_2t"]
    w(
        f"- {n(ct['n_municipios'])} municípios em dez grupos pelo minuto em que fecharam. "
        f"Parte de Flávio entre os dois: {n(d[0]['h2h_flavio'])}% no 1º decil e "
        f"{n(d[-1]['h2h_flavio'])}% no 10º. Mudança contra o 1º turno nos mesmos "
        "municípios (swing): "
        + ", ".join(pp(x["swing_h2h_flavio_pp"]) for x in d)
        + " pp. O swing quase constante mostra que a diferença entre cedo e tarde é de "
        "composição, não de mudança de voto. Origem: `cedo_tarde.json`, `decis_2t`."
    )
    w(
        f"- O último decil tem {n(d[-1]['aptos'])} eleitores e {d[-1]['capitais']} "
        f"capitais; o primeiro, {n(d[0]['aptos'])} eleitores. Correlação de postos entre "
        f"tamanho e minuto de fechamento: {n(ct['spearman_tamanho_x_fechamento_2t'])}; "
        f"entre a ordem de fechamento do 1º e do 2º turno: {n(ct['spearman_ordem_1t_x_2t'])}."
    )
    z = ct["zonas"]["decis"]
    w(
        f"- Zonas ({n(ct['zonas']['n'])}): swing de {pp(min(x['swing_h2h_flavio_pp'] for x in z))} "
        f"a {pp(max(x['swing_h2h_flavio_pp'] for x in z))} pp entre os decis."
    )
    cu = lt["conclusao_ufs"]
    fech = [c for c in cu if c["fechou_min"] is not None]
    abertas = [c["uf"] for c in cu if c["fechou_min"] is None]
    if fech:
        w(
            f"- Primeira UF completa: {fech[0]['uf']} às {fech[0]['fechou_brt'][11:16]}; "
            f"última até a rodada: {fech[-1]['uf']} às {fech[-1]['fechou_brt'][11:16]}. "
            f"Ainda com seção por totalizar: {', '.join(abertas) or 'nenhuma'}."
        )
    pre = [
        r
        for r in _linhas(pres["municipios"])
        if r["fechou_min"] is not None and r["fechou_min"] < 120
    ]
    for r in pre:
        w(
            f"- Atípico: {r['nome']} ({r['uf']}, {r['secoes_total']} seções) teve todas as "
            f"seções totalizadas às {r['fechou_hhmm']}, antes do fim da votação prorrogada. "
            f"{ROTULO}."
        )
    rg = lt["regressoes"]
    w(
        f"- Regressões: {len(rg['contagem_regressiva'])} versões genuínas com menos seções "
        "ou menos comparecimento que a anterior; versões marcadas regressivas pelo coletor "
        "por nível: "
        + "; ".join(
            f"{k} {v['marcadas_regressivas']} (cópias antigas {v['copia_antiga']})"
            for k, v in rg["por_nivel"].items()
        )
        + "."
    )
    w("")
    # ------------------------------------------------------------ 1º turno
    w("## 4. Contra o 1º turno")
    w("")
    b = c1["brasil"]
    w(
        f"- {n(b['n_municipios'])} municípios completos: Flávio {n(b['t1_flavio'])} para "
        f"{n(b['t2_flavio'])} ({pp(b['delta_votos_flavio'])}), Lula {n(b['t1_lula'])} para "
        f"{n(b['t2_lula'])} ({pp(b['delta_votos_lula'])}). Terceiros do 1º turno: "
        f"{n(b['t1_terceiros'])}. Flávio somou o equivalente a "
        f"{n(b['ganho_flavio_sobre_terceiros_pct'])}% desse estoque e Lula a "
        f"{n(b['ganho_lula_sobre_terceiros_pct'])}% (o comparecimento cresceu "
        f"{n(b['delta_comparecimento_votos'])}). Parte de Flávio entre os dois: "
        f"{n(b['t1_h2h_flavio'])}% para {n(b['t2_h2h_flavio'])}% ({pp(b['swing_h2h_flavio_pp'])} pp). "
        "Origem: `comparacao_1t.json`, `brasil`."
    )
    dm = c1["dispersao_municipal"]
    w(
        f"- Swing a favor de Lula em {n(dm['n_swing_h2h_pro_lula'])} municípios e a favor "
        f"de Flávio em {n(dm['n_swing_h2h_pro_flavio'])}; mediana "
        f"{pp(dm['swing_h2h_flavio_pp']['mediana'])} pp, desvio "
        f"{n(dm['swing_h2h_flavio_pp']['desvio'])}."
    )
    w(
        f"- Flávio perdeu votos absolutos em {n(c1['flavio_perdeu_votos']['n'])} municípios "
        f"e ganhou em {n(c1['flavio_ganhou_votos']['n'])}; Lula perdeu em "
        f"{n(c1['lula_perdeu_votos']['n'])} e ganhou em {n(c1['lula_ganhou_votos']['n'])}."
    )
    top = c1["flavio_maiores_perdas"][:5]
    w(
        "- Maiores perdas de Flávio: "
        + "; ".join(
            f"{r['nome']} ({r['uf']}) {n(r['delta_votos_flavio'])}" for r in top
        )
        + "."
    )
    topl = c1["lula_maiores_perdas"][:5]
    w(
        "- Maiores perdas de Lula: "
        + "; ".join(f"{r['nome']} ({r['uf']}) {n(r['delta_votos_lula'])}" for r in topl)
        + "."
    )
    for r in c1["regioes"]:
        w(
            f"- {r['regiao']}: swing {pp(r['swing_h2h_flavio_pp'])} pp; Flávio "
            f"{n(r['ganho_flavio_sobre_terceiros_pct'])}% e Lula "
            f"{n(r['ganho_lula_sobre_terceiros_pct'])}% do estoque de terceiros; "
            f"abstenção {pp(r['delta_abstencao_pp'])} pp."
        )
    sobe = [u for u in c1["ufs"] if (u["delta_abstencao_pp"] or 0) > 0]
    w(
        "- Contrariando a tese de abstenção em queda geral: a abstenção subiu contra o "
        "1º turno em "
        + ", ".join(f"{u['uf']} ({pp(u['delta_abstencao_pp'])} pp)" for u in sobe)
        + ". Parte do estoque de terceiros somada por Flávio nessas UFs: "
        + ", ".join(
            f"{u['uf']} {n(u['ganho_flavio_sobre_terceiros_pct'])}%" for u in sobe
        )
        + "."
    )
    w(
        f"- Municípios com abstenção pelo menos 5 pp menor que no 1º turno e 5 mil "
        f"eleitores ou mais: {c1['abstencao_caiu_5pp']['n']}; com abstenção 5 pp maior: "
        f"{c1['abstencao_subiu_5pp']['n']}."
    )
    w("")
    # ------------------------------------------------------------ 2022
    w("## 5. Contra o 2º turno de 2022")
    w("")
    b = c22["brasil"]
    w(
        f"- Mesmos {n(b['n_municipios'])} municípios, sem exterior: Lula {n(b['r22_pct_lula'])}% "
        f"em 2022 contra {n(b['pct_lula'])}% em 2026 ({pp(b['swing_lula_pp'])} pp); Flávio "
        f"fica {pp(b['flavio_menos_bolsonaro_pp'])} pp de Bolsonaro. Abstenção "
        f"{n(b['r22_pct_abstencao'])}% para {n(b['pct_abstencao'])}%. Origem: "
        "`comparacao_2022.json`, `brasil`; fonte de 2022 em `fontes_2022`."
    )
    dsw = c22["dispersao_swing_lula_pp"]
    w(
        f"- Achado contrário ao agregado: Lula caiu contra 2022 em {n(c22['n_lula_caiu'])} "
        f"municípios e subiu em {n(c22['n_lula_subiu'])}; mediana municipal "
        f"{pp(dsw['mediana'])} pp, média ponderada pelo eleitorado "
        f"{pp(dsw.get('media_ponderada'))} pp: mediana negativa com média ponderada positiva "
        "indica avanço de Lula concentrado nos municípios mais populosos."
    )
    vr = c22["viraram"]
    w(
        f"- Municípios que trocaram de vencedor: {vr['n']} ({vr['lula_2022_para_flavio_2026']} "
        f"de Lula para Flávio, {vr['bolsonaro_2022_para_lula_2026']} de Bolsonaro para Lula)."
    )
    w(
        "- UFs com maior avanço de Lula sobre 2022: "
        + ", ".join(
            f"{u['uf']} {pp(u['swing_lula_pp'])}"
            for u in sorted(c22["ufs"], key=lambda u: -u["swing_lula_pp"])[:5]
        )
        + "; maior recuo: "
        + ", ".join(
            f"{u['uf']} {pp(u['swing_lula_pp'])}"
            for u in sorted(c22["ufs"], key=lambda u: u["swing_lula_pp"])[:5]
        )
        + "."
    )
    w("")
    # ------------------------------------------------------------ abstenção
    w("## 6. Abstenção")
    w("")
    for r in ab["regioes"]:
        w(
            f"- {r['regiao']}: {n(r['pa_2t'])}% (1º turno {n(r['pa_1t_mesmos'])}%, "
            f"2022 {n(r['pa_2022_2t_mesmos'])}%)."
        )
    cx = ab["capitais_x_interior"]
    w(
        f"- Capitais {n(cx['capitais']['pa_2t'])}% ({pp(cx['capitais']['delta_1t_pp'])} pp "
        f"contra o 1º turno); interior {n(cx['interior']['pa_2t'])}% "
        f"({pp(cx['interior']['delta_1t_pp'])} pp)."
    )
    ne = next(c for c in ab["concentracao_abaixo_15"] if c["regiao"] == "Nordeste")
    su = next(c for c in ab["concentracao_abaixo_15"] if c["regiao"] == "Sul")
    w(
        f"- Abstenção abaixo de 15%: o Nordeste concentra {n(ne['pct_aptos_abaixo_15_no_pais'])}% "
        f"do eleitorado desses municípios; o Sul tem {n(su['pct_municipios_abaixo_15'])}% "
        f"dos seus municípios abaixo de 15%, com eleitorado médio de "
        f"{n(su['aptos_abaixo_15'] // max(su['municipios_abaixo_15'], 1))} por município."
    )
    w(
        f"- A abstenção caiu contra o 1º turno em {n(ab['n_municipios_caiu_vs_1t'])} "
        f"municípios e subiu em {n(ab['n_municipios_subiu_vs_1t'])}."
    )
    w(
        "- Explicações legítimas para a queda: prorrogação da votação até 19h em todo o "
        "país, mobilização de segundo turno e transporte; o banco não separa essas causas."
    )
    w("")
    # ------------------------------------------------------------ exterior
    w("## 7. Exterior")
    w("")
    t = ext["total"]
    w(
        f"- {t['cidades']} cidades ({t['cidades_fechadas']} completas): Lula {n(t['pct_lula'])}% × "
        f"Flávio {n(t['pct_flavio'])}%, comparecimento {n(t['pct_comparecimento'])}%."
    )
    for p in ext["paises"][:5]:
        w(
            f"- {p['pais']}: Flávio {n(p['pct_flavio'])}% × Lula {n(p['pct_lula'])}% "
            f"(1º turno {n(p['t1_pct_flavio'])} × {n(p['t1_pct_lula'])}); comparecimento "
            f"{n(p['pct_comparecimento'])}% ({pp(p['delta_comparecimento_pp'])} pp)."
        )
    w("")
    # ------------------------------------------------------------ governadores
    w("## 8. Governadores")
    w("")
    for u in gov["ufs"]:
        cs = u["candidatos"]
        w(
            f"- {u['uf']}: {cs[0]['nome_urna']} {n(cs[0]['pct'])}% × {cs[1]['nome_urna']} "
            f"{n(cs[1]['pct'])}% ({n(u['margem_votos'])} votos, pst {n(u['pst'])}); "
            f"1º turno {n(cs[0]['t1_pct'])} × {n(cs[1]['t1_pct'])}; viradas na noite: "
            f"{u['n_viradas']}; vão do vencedor contra o presidencial do mesmo lado "
            f"{pp(cs[0]['vao_pp'])} pp; brancos e nulos de governador menos os de "
            f"presidente {pp(u['brancos_nulos_gov_menos_pres_pp'])} pp."
        )
    w(f"- Rótulo do vão: {gov['rotulo_vao']}.")
    w("")
    # ------------------------------------------------------------ limites
    w("## 9. Limites")
    w("")
    w(
        "- O horário da decisão do STF vem do noticiário; o banco mostra só o "
        "silêncio de publicação, não a causa."
    )
    w(
        "- Exterior: a totalização impressa está em hora local; os relógios deste "
        "conjunto usam a hora de geração do TSE (Brasília)."
    )
    w(
        "- O 1º turno é comparado pela régua `referencia_1t.json` (fechamento por município) "
        "e por `analysis/apuracao_2026/dados/*.json`; no 1º turno a votação terminou às "
        "17:00 e no 2º às 19:00, então minutos de fechamento não se comparam sem descontar "
        "120 min (`atraso_vs_1t_descontada_prorrogacao_min`)."
    )
    w(
        "- Votos ganhos sobre o estoque de terceiros não identificam transferência "
        "individual: a conta mistura eleitor novo, eleitor que faltou e troca de lado."
    )
    w(
        "- 2022 casa por código TSE do município; municípios sem par: "
        f"{len(c22['sem_2022'])}. Zonas do 1º turno casam por número, e o rezoneamento pode "
        "mudar o território."
    )
    w(
        "- Latência entre geração e captura é teto, não medida, porque inclui o "
        "intervalo de sondagem do coletor."
    )
    w(
        "- A projeção da casa foi relida com `at=` sobre o banco: é a reconstrução do que o "
        "método diria em cada instante, não necessariamente o que a tela mostrou "
        "(`serie_ao_vivo`)."
    )
    w(
        "- A paralela é a soma dos BUs recebidos, não projeção; a amostra é de quem enviou."
    )
    w("")
    return "\n".join(s) + "\n"
