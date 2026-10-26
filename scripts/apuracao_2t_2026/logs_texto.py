"""Memorando ``analysis/apuracao_2t_2026/dados/logs.md`` a partir de ``logs.json``."""

from __future__ import annotations


def _n(x, casas: int = 0) -> str:
    if x is None:
        return "n/d"
    s = f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def _ic(b: dict) -> str:
    if not b or b.get("media_pp") is None:
        return "n/d"
    lo, hi = b["ic95_pp"]
    return f"{_n(b['media_pp'], 2)} pp (IC95 {_n(lo, 2)} a {_n(hi, 2)}; n {_n(b['n'])})"


def _v(x: dict | None, casas: int = 2) -> str:
    if not x or x.get("valor") is None:
        return "n/d"
    ic = x.get("ic95")
    base = _n(x["valor"], casas)
    return base + (f" (IC95 {_n(ic[0], casas)} a {_n(ic[1], casas)})" if ic else "")


def clima_observado_md(c: dict) -> list[str]:
    """Bateria e abstenção contra a chuva de 25/10 por estação e por modelo."""
    if not c.get("disponivel"):
        return []
    cob, est = c["cobertura_celulas"], c["estacoes"]
    L = [
        f"- Chuva de 25/10 medida (fonte: {c['fonte']}): {_n(est.get('cemaden_com_dia', 0))} pluviômetros com o dia e "
        f"{_n(est.get('cemaden_com_votacao', 0))} com as horas de votação; {_n(cob['com_estacao_dia'])} de "
        f"{_n(cob['celulas'])} células com estação a até 50 km; {_n(c['secoes_chuva_dia_medida'])} seções. INMET: {est.get('inmet')}.",
    ]
    ref = c.get("referencia_1t") or {}
    for nome, chave in (
        ("dia inteiro, estações", "chuva_dia_medida"),
        ("horas de votação, estações", "chuva_votacao_medida"),
        ("horas de votação, modelo IFS provisório", "chuva_votacao_modelo"),
    ):
        for f in c["bateria"][chave]:
            if not f["secoes"]:
                continue
            L.append(
                f"  - bateria, chuva {nome}, {f['rotulo']}: {_n(f['secoes'])} seções, "
                f"{_v(f['parcela_pct'])}%; razão contra a seca {_v(f.get('razao_vs_seca'), 3)}."
            )
        for f in c["abstencao"][chave]:
            if not f["secoes"]:
                continue
            L.append(
                f"  - abstenção, chuva {nome}, {f['rotulo']}: {_n(f['secoes'])} seções, "
                f"{_v(f['abst_pct'], 1)}%; contra a UF {_v(f['dentro_uf_pp'])} pp; variação 1º→2º contra a UF "
                f"{_v(f['variacao_vs_1t_dentro_uf_pp'])} pp."
            )
    r = (ref.get("chuva_votacao") or {}).get("forte") or {}
    rd = (ref.get("chuva_diaria") or {}).get("forte") or {}
    L.append(
        f"  - 1º turno (ERA5): razão da chuva forte contra a seca {_n(r.get('razao_vs_seca'), 3)} nas horas de "
        f"votação e {_n(rd.get('razao_vs_seca'), 3)} no dia."
    )
    return L


def markdown(d: dict) -> str:
    c, g, p = d["cobertura"], d["regra2"], d["persistencia"]
    cad, rei, bat, meta, ig = (
        d["cadencia"],
        d["reinicios"],
        d["bateria"],
        d["metadados"],
        d["integrado"],
    )
    b2 = cad["brasil_2t"]
    a = cad["amostra_1t"]
    L = [
        "# O que os logs das urnas dizem: 1º × 2º turno",
        "",
        f"Rótulo: {d['rotulo']}. Gerado em {d['gerado_em']} por `scripts/apuracao-2t-2026-logs.py`.",
        "",
        "## 1. Cobertura e integridade",
        "",
        f"- Logs lidos: {_n(c['lidos'])} de {_n(c['catalogadas'])} seções catalogadas.",
        f"- Contagem do log igual ao BU: {_n(c['contagem_confere'])}; não confere: {len(c['contagem_nao_confere'])} (em todas o log tem menos cômputos que o BU: {c['log_menor_que_bu_em_todas']}).",
    ]
    for r in c["contagem_nao_confere"]:
        L.append(
            f"  - {r['uf']} {r['mun']} zona {r['zona']} seção {r['secao']}: log {r['computados_log']}, BU {r['comparecimento_bu']} ({r['diferenca']}); {r['explicacao_possivel']}."
        )
    L += [
        f"- Biometria conferida: {_n(c['biometria_confere'])}; restantes {_n(c['biometria_nao_conferida'])}: {_n(c['biometria_ausente_bu'])} sem as categorias no BU (exterior {_n(c['biometria_ausente_bu_exterior'])}), {_n(c['biometria_por_contagem'])} pela contagem.",
        f"- Versão do software: {', '.join(f'{k} ({_n(v)})' for k, v in c['versoes'].items())}.",
        f"- Urna do BU no log: {_n(c['urna_bu_no_log'])}; código de carga do BU no log: {_n(c['carga_bu_no_log'])}.",
        "",
        "## 2. Regra 2 (erro de desmontar a memória de resultado)",
        "",
        f"- Seções com ERRO/FATAL no dia: {_n(g['secoes_com_erro'])}; só o erro da MR antes da zerésima: {_n(g['so_mr_antes_da_zeresima'])}.",
        f"- Erro técnico pela regra 2: {_n(g['erro_tecnico_regra2'])} ({_n(g['na_janela_da_votacao'])} com erro dentro da janela de votação). No 1º turno, o critério marcou {_n(g['criterio_1t'])}.",
    ]
    for x in g["por_tipo"]:
        L.append(f"  - {x['tipo']}: {_n(x['secoes'])} seções.")
    L += ["", "## 3. Persistência 1T × 2T", ""]
    L.append("| 1T \\ 2T | 0 | 1 | 2 | 3 |")
    L.append("|---|---|---|---|---|")
    for i in range(4):
        L.append(
            f"| {i} | "
            + " | ".join(_n(p["matriz"].get(f"{i}x{j}", 0)) for j in range(4))
            + " |"
        )
    L += [
        "",
        "| Diagnóstico | nos dois | só 1T | só 2T | persiste |",
        "|---|---|---|---|---|",
    ]
    for x in p["diagnosticos"]:
        L.append(
            f"| {x['nome']} | {_n(x['ambos'])} | {_n(x['so_1t'])} | {_n(x['so_2t'])} | {_n(x['pct_persiste'], 1)}% |"
        )
    L += [
        "",
        "## 4. Cadência horária (hora de Brasília)",
        "",
        f"- 2º turno, {_n(cad['secoes_2t'])} seções: primeira hora {_n(b2['pct_primeira_hora'], 2)}%, última hora (16h) {_n(b2['pct_ultima_hora'], 2)}%, 17h a 19h {_n(b2['pct_17_19'], 3)}% ({_n(b2['computados_17_19'])} cômputos), depois das 19h {_n(b2['computados_depois_19'])} cômputos.",
        f"- 1º turno, amostra de {_n(a['secoes'])} seções: primeira hora {_n(a['brasil_1t']['pct_primeira_hora'], 2)}%, última hora {_n(a['brasil_1t']['pct_ultima_hora'], 2)}%, 17h a 19h {_n(a['brasil_1t']['pct_17_19'], 2)}%.",
        f"- Último voto pelo log: depois das 17:30 em {_n(cad['ultimo_voto']['depois_1730'])} seções, depois das 19:00 em {_n(cad['ultimo_voto']['depois_19'])}.",
        f"- BUs encerrados depois das 19h: {_n(cad['bu_apos_19h']['secoes'])}; último voto até 17:15 em {_n(cad['bu_apos_19h']['ultimo_voto_ate_1715'])}.",
        "",
        "| Grupo | seções | 1ª hora | última hora | 17h–19h |",
        "|---|---|---|---|---|",
    ]
    for x in cad["por_sinal"]:
        L.append(
            f"| {x['grupo']} | {_n(x['secoes'])} | {_n(x['pct_primeira_hora'], 2)}% | {_n(x['pct_ultima_hora'], 2)}% | {_n(x['pct_17_19'], 3)}% |"
        )
    L += [
        "",
        "## 5. Reinícios e bateria",
        "",
        f"- Seções com o sistema religado durante a votação: {_n(rei['secoes'])} ({_n(rei['so_2t'])} só no 2º turno, {_n(rei['nos_dois'])} nos dois); mesma urna {_n(rei['mesma_urna'])}, troca ou contingência {_n(rei['troca_ou_contingencia'])}.",
        f"- Mediana dos votos antes do primeiro reinício: {_n(rei['votos_antes_mediana'])} ({_n(rei['pct_votos_antes_mediana'], 1)}% da seção); depois: {_n(rei['votos_depois_mediana'])}.",
    ]
    for v in rei["voto"]:
        L.append(
            f"  - {v['grupo']}: contra as vizinhas {_ic(v['contra_vizinhas_2t'])}; diferença em diferenças {_ic(v['dif_em_dif_contra_1t'])}."
        )
    L.append(
        f"- Bateria durante a votação: junto com o município {_n(bat['bateria_votacao_local']['2t'])} no 2º turno contra {_n(bat['bateria_votacao_local']['1t'])} no 1º; só nesta urna {_n(bat['bateria_votacao_isolada']['2t'])} contra {_n(bat['bateria_votacao_isolada']['1t'])}."
    )
    for f in bat["por_chuva_prevista"]:
        L.append(
            f"  - chuva prevista {f['faixa']}: {_n(f['secoes'])} seções, bateria na votação {_n(f['pct_bateria_votacao'], 2)}%."
        )
    for v in bat["voto"]:
        L.append(
            f"  - {v['grupo']}: diferença em diferenças {_ic(v['dif_em_dif_contra_1t'])}."
        )
    L += clima_observado_md(d.get("clima_observado") or {})
    s = meta["serie_mr"]
    L += [
        "",
        "## 6. Metadados",
        "",
        f"- Série da memória de resultado no dia: {_n(s['valores_distintos'])} valores, {_n(s['repetidos'])} repetidos em {_n(s['secoes_em_repeticao'])} seções; pares entre lugares distantes {_n(s['pares_entre_lugares'])} contra {_n(s['pares_esperados_por_acaso_32_bits'], 1)} esperados por acaso num número de 32 bits.",
    ]
    for e in s["estruturais"]:
        L.append(
            f"  - {e['serie']}: {_n(e['secoes'])} seções em {', '.join(e['zonas'])}; só esse valor em todo o log (inclusive o trecho do 1º turno) em {_n(e['so_esse_valor_no_log_todo'])}; contagem confere em {_n(e['contagem_confere'])}."
        )
    L.append(
        f"  - Voto nas seções desses grupos (Brasil, sem exterior, ponderado): diferença em diferenças {_ic(s['voto_estruturais_brasil']['dif_em_dif_contra_1t'])}; média simples {_ic(s['voto_estruturais_brasil']['sem_peso']['dif_em_dif_contra_1t'])}."
    )
    for g in s["voto_por_grupo"]:
        L.append(f"    - {g['zona']}: {_ic(g['dif_em_dif_contra_1t'])}.")
    ex = s["voto_exterior"]
    L.append(
        f"  - Exterior, separado ({_n(ex['secoes_marcadas'])} seções): cinco vizinhas {_ic(ex['regra_5_vizinhas']['dif_em_dif_contra_1t'])}; três vizinhas (sensibilidade) {_ic(ex['regra_3_vizinhas']['dif_em_dif_contra_1t'])}. {ex['nota']}"
    )
    L.append(
        f"- Carga registrada: {_n(meta['cargas']['antes_do_1t'])} antes do 1º turno, {_n(meta['cargas']['entre_turnos'])} entre os turnos, {len(meta['cargas']['no_dia_ou_depois'])} no dia ou com data posterior."
    )
    L += [
        "",
        "## 7. Escore integrado",
        "",
        f"- Escore do BU ≥ 2: {_n(ig['bu_escore_2_mais'])}; atenção dos logs ≥ 2: {_n(ig['log_atencao_2_mais'])}; as duas: {_n(ig['as_duas'])} (esperado se fossem independentes: {_n(ig['esperado_se_independentes'], 1)}).",
        f"- Voto nessas seções: diferença em diferenças {_ic(ig['voto']['dif_em_dif_contra_1t'])}.",
        "",
        d["rotulo"] + ".",
        "",
    ]
    return "\n".join(L)
