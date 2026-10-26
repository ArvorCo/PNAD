"""Resumo em Markdown do estudo de metadados das urnas (`metadados.md`)."""

from __future__ import annotations

from .metadados_regras import EXPLICACOES


def _n(v) -> str:
    if v is None:
        return "sem dado"
    if isinstance(v, float):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    return str(v)


def _ic(v) -> str:
    if not v:
        return ""
    return f"{_n(float(v[0]))} a {_n(float(v[1]))}"


def _sim_nao(d: dict | None) -> str:
    if not d:
        return "sem dado"
    partes = [f"{_n(d.get('sim', 0))} sim", f"{_n(d.get('nao', 0))} não"]
    if d.get("sem_dado"):
        partes.append(f"{_n(d['sem_dado'])} sem dado")
    return ", ".join(partes)


def _tabela_repeticao(campos: dict) -> list[str]:
    linhas = [
        "| Campo | Fonte | Escopo | Seções com valor | Valores distintos | Grupos repetidos | Seções em grupos | Sem explicação (grupos/seções) |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in campos.values():
        if r.get("secoes_com_valor", 0) == 0:
            linhas.append(
                f"| {r['descricao']} | {r['fonte']} | {r['escopo']} | 0 | | | | sem dados |"
            )
            continue
        if r["escopo"] == "global":
            vals = "; ".join(
                f"{v['valor']} ({_n(v['secoes'])})" for v in r["valores"][:3]
            )
            linhas.append(
                f"| {r['descricao']} | {r['fonte']} | global | {_n(r['secoes_com_valor'])} | {_n(r['valores_distintos'])} | | | {'coerente' if r['coerente'] else 'mais de um valor'}: {vals} |"
            )
            continue
        sem = r["sem_explicacao"]
        linhas.append(
            f"| {r['descricao']} | {r['fonte']} | {r['escopo']} | {_n(r['secoes_com_valor'])} | {_n(r['valores_distintos'])} | {_n(r['grupos_repetidos'])} | {_n(r['secoes_em_grupos'])} | {_n(sem['grupos'])} / {_n(sem['secoes'])} |"
        )
    return linhas


def _explicacoes(campos: dict) -> list[str]:
    out = []
    for r in campos.values():
        pe = r.get("por_explicacao")
        if not pe:
            continue
        itens = "; ".join(
            f"{EXPLICACOES[k].split(' (')[0].split(':')[0].split(',')[0]}: {_n(v['grupos'])} grupos, {_n(v['secoes'])} seções"
            for k, v in pe.items()
        )
        out.append(f"- {r['descricao']}: {itens}.")
        col = r.get("colisao_aleatoria")
        if col:
            out.append(
                f"  Pares iguais observados {_n(col['pares_observados'])}; esperados ao acaso entre {_n(col['n'])} identificadores de {col['bits']} bits: {_n(col['pares_esperados'])} (limite de 99,9%: {_n(col['limite_999'])})."
            )
    return out


def markdown(d: dict) -> str:
    c = d["cobertura"]
    linhas = [
        "# Metadados das urnas por seção: repetição e coerência (2º turno de 2026)",
        "",
        f"Gerado em {d['gerado_em']}. Rótulo: **{d['rotulo']}**. Estado: {d['estado']}.",
        "",
        "## Cobertura",
        "",
        f"- BUs: 1º turno {_n(c['bu_1t'])}, 2º turno {_n(c['bu_2t'])} seções.",
        f"- `.vsc` do 2º turno: {c['vsc_2t']}.",
        f"- `.vsc` do 1º turno: {c['vsc_1t']}.",
        f"- Logs processados do 2º turno: {c['logs_2t_texto']}.",
        "",
        "## O que o `.vsc` contém",
        "",
        d["formato_vsc"],
        "",
    ]
    for t in ("2t", "1t"):
        bloco = d["turnos"][t]
        linhas += [
            f"## Repetição entre seções, {t[0]}º turno",
            "",
            *_tabela_repeticao(bloco["repeticao"]),
            "",
            *_explicacoes(bloco["repeticao"]),
            "",
        ]
        cv = bloco.get("coerencia_vsc")
        if cv and cv.get("secoes_vsc_ok"):
            linhas += [
                f"### Coerência BU × `.vsc`, {t[0]}º turno ({_n(cv['secoes_vsc_ok'])} seções com `.vsc` lido)",
                "",
                f"- Número interno do BU igual à série da assinatura de hardware: {_sim_nao(cv['id_bu_igual_serie_hw'])}.",
                f"- CN do certificado igual à série: {_sim_nao(cv['cn_do_certificado_igual_serie_hw'])}.",
                f"- Modelo no `.vsc` igual ao do BU: {_sim_nao(cv['modelo_vsc_igual_bu'])}; AC compatível com o modelo: {_sim_nao(cv['ac_compativel_com_modelo'])}.",
                f"- Cadeia até a AC arquivada: {_sim_nao(cv['cadeia_ate_a_ac'])}. Por AC: {', '.join(f'{k} {_n(v)}' for k, v in cv['por_ac'].items())}.",
                f"- Autoassinatura de hardware: {_sim_nao(cv['autoassinatura_hw'])}; assinatura de hardware do BU: {_sim_nao(cv['assinatura_hw_do_bu'])}.",
                f"- BU publicado com o SHA-512 listado no `.vsc`: {_sim_nao(cv['bu_publicado_igual_ao_vsc'])}.",
                f"- Certificado válido no dia: {_sim_nao(cv['certificado_valido_no_dia'])}.",
                f"- Minutos entre a emissão do BU e a assinatura de hardware: mediana {_n(cv['minutos_vsc_depois_da_emissao']['mediana'])}, máximo {_n(cv['minutos_vsc_depois_da_emissao']['max'])}.",
                f"- Falhas por teste: {', '.join(f'{k} {_n(v)}' for k, v in cv['falhas'].items())}.",
                "",
            ]
    et = d.get("entre_turnos_vsc")
    if et and et.get("secoes_com_vsc_nos_dois_turnos"):
        cg = et["carga"]
        linhas += [
            "## A mesma seção nos dois turnos",
            "",
            f"- Seções com `.vsc` nos dois turnos: {_n(et['secoes_com_vsc_nos_dois_turnos'])}; mesma urna e mesmo certificado {_n(et['mesma_urna_mesmo_certificado'])}; urna e certificado trocados juntos {_n(et['urna_trocada_certificado_trocado'])}.",
            f"- Mesma urna com certificado diferente: {_n(et['mesma_urna_certificado_diferente'])}. Urna diferente com o mesmo certificado: {_n(et['urna_diferente_mesmo_certificado'])}. Certificado do 1º turno em outra seção no 2º: {_n(et['certificado_do_1t_em_outra_secao_no_2t'])}.",
            f"- Carga (BU, {_n(cg['secoes_nos_dois_turnos'])} seções): mesma urna e mesma carga {_n(cg['mesma_urna_mesma_carga'])}; mesma urna com carga nova {_n(cg['mesma_urna_carga_nova'])} ({_n(cg['carga_nova_entre_os_turnos'])} com a carga feita entre 05/10 e 24/10, recarga para o 2º turno); urna trocada {_n(cg['urna_trocada'])}, das quais com o mesmo código de carga {_n(cg['urna_trocada_mesma_carga'])}.",
            "",
        ]
    lg = d.get("coerencia_logs") or {}
    linhas += ["## BU × log do 2º turno", ""]
    if "situacao" in lg:
        linhas += [
            f"{lg['situacao']}. O cruzamento está previsto e roda quando `data/outputs/logs_urnas_2t_2026.sqlite` existir.",
            "",
        ]
    else:
        for k, v in lg.items():
            if isinstance(v, dict) and "cobertas" in v and "confere" in v:
                linhas.append(
                    f"- {k}: cobertas {_n(v['cobertas'])}, confere {_n(v['confere'])}, não confere {_n(v['nao_confere'])}."
                )
        cv = lg.get("carga_registrada_vs_abertura", {})
        if cv:
            linhas.append(
                f"- Carga registrada no log da urna do BU: {_n(cv['cobertas'])} cobertas; antes da abertura {_n(cv['carga_antes_da_abertura'])}, depois da abertura pelo log {_n(cv['carga_depois_da_abertura_no_log'])} (em {_n(cv['das_quais_bu_registra_carga_antes'])} o BU registra a carga antes da abertura: relógio, não carga no dia), depois da abertura também pelo BU {_n(cv['carga_depois_da_abertura'])}, no dia da eleição {_n(cv['carga_no_dia_da_eleicao'])}. Por mês: {', '.join(f'{k} {_n(x)}' for k, x in cv['carga_por_mes'].items())}."
            )
        rv = lg.get("reinicios_durante_votacao", {})
        if rv:
            linhas.append(
                f"- Reinícios durante a votação: {_n(rv['secoes_com_reinicio'])} seções de {_n(rv['cobertas'])}. Distribuição: {', '.join(f'{k}: {_n(x)}' for k, x in rv['distribuicao'].items())}."
            )
        for k in (
            "urna_do_bu_no_log_pelo_processamento",
            "carga_do_bu_no_log_pelo_processamento",
        ):
            if k in lg:
                linhas.append(f"- {k}: {_sim_nao(lg[k])}.")
        if "secoes_com_outra_urna_no_log" in lg:
            linhas.append(
                f"- Seções com outra urna além da do BU no log: {_n(lg['secoes_com_outra_urna_no_log'])}."
            )
        linhas.append("")
    linhas += [
        "## Voto nos grupos fora da regra",
        "",
        "Fatia de Flávio entre os válidos dos dois finalistas, menos a média das demais seções do município; e a mesma diferença para a variação 1º → 2º turno. Média, erro-padrão e IC de 95%.",
        "",
        "| Grupo | n | 2º turno contra vizinhas (pp) | IC 95% | Dif. em dif. contra o 1º turno (pp) | IC 95% |",
        "|---|---:|---:|---|---:|---|",
    ]
    for v in d["voto"]:
        if not v["n"]:
            linhas.append(f"| {v['grupo']} | 0 | | | | |")
            continue
        a, b = (
            v["fatia_flavio_2t_menos_vizinhas_do_municipio"],
            v["dif_em_dif_contra_1t"],
        )
        linhas.append(
            f"| {v['grupo']} | {_n(v['n'])} | {_n(a['media_pp'])} | {_ic(a['ic95_pp'])} | {_n(b['media_pp'])} | {_ic(b['ic95_pp'])} |"
        )
    linhas += ["", "## Pendências", "", *(f"- {p}" for p in d["pendencias"]), ""]
    return "\n".join(linhas)
