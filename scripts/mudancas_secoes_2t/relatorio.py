"""Relatório em Markdown com os números do resumo, as decisões e os controles."""

from __future__ import annotations

from typing import Any


def n(x: Any, casas: int = 2) -> str:
    """Número em português: milhar com ponto, decimal com vírgula."""
    if x is None:
        return "sem dado"
    if isinstance(x, bool):
        return "sim" if x else "não"
    if isinstance(x, float) and x.is_integer() and abs(x) >= 100:
        x = int(x)
    if isinstance(x, int):
        return f"{x:,}".replace(",", ".")
    if isinstance(x, float):
        return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(x)


def ic(d: dict[str, Any] | None, un: str = " pp") -> str:
    if not d or d.get("valor") is None:
        return "sem dado"
    lo, hi = d["ic95"]
    return f"{n(d['valor'])}{un} (IC 95% {n(lo)} a {n(hi)})"


def _sentido(v: int) -> str:
    if v > 0:
        return f"{n(v)} votos a favor de Flávio"
    if v < 0:
        return f"{n(-v)} votos a favor de Lula"
    return "nenhuma variação"


def _originais(pc: dict[str, Any]) -> str:
    itens = [
        x["local_final_painel"]
        for x in pc["listas"]["so_painel"]
        if "local_final_painel" in x
    ]
    com_coord = sum(1 for x in itens if x["lat_2t"] is not None)
    com_bairro = sum(1 for x in itens if x["bairro_2t"] is not None)
    return (
        f"Nas seções só do painel cujo local final é o original, o endereço do original "
        f"(nome e endereço da própria linha do arquivo) foi preenchido em {n(len(itens))}; "
        f"bairro e CEP em {n(com_bairro)} e coordenada em {n(com_coord)}, tirados de outra "
        "seção que vota nesse local no 2º turno, no mesmo município e zona."
    )


def _z161(z: dict[str, Any] | None) -> str:
    if not z:
        return "- Zona 161: sem dado."
    return (
        f"- Zona 161 (Maré): {n(z['urnas'])} urnas, abstenção da zona {n(z['abstencao_zona_1t'])}% "
        f"(ConJur: 28,46%); {n(z['urnas_troca_desde_2022'])} urnas com prédio trocado desde "
        f"2022; abstenção 1T transferidas {n(z['abstencao_1t_transferidas'])}% contra estáveis "
        f"{n(z['abstencao_1t_estaveis'])}%; variação desde 2022 {n(z['variacao_transferidas_pp'])} "
        f"contra {n(z['variacao_estaveis_pp'])} pp, diferença em diferenças "
        f"{n(z['dif_em_dif_pp'])} pp."
    )


def _tabela(cab: list[str], linhas: list[list[Any]]) -> list[str]:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    out += [
        "| " + " | ".join(n(c) if not isinstance(c, str) else c for c in li) + " |"
        for li in linhas
    ]
    return out


def gerar(
    p: dict[str, Any], controles: list[dict[str, Any]], decisoes: list[str]
) -> str:
    r = p["resumo"]
    mr = r["mudanca_real"]
    out = [
        "# Mudanças de local de votação entre os turnos de 2026: relatório do motor",
        "",
        f"Gerado em {p['gerado_em']} por `python3 scripts/mudancas-secoes-2t.py` "
        f"({p['parametros']['reps']} réplicas de bootstrap, semente {p['parametros']['seed']}).",
        "",
        "## Fontes",
        "",
    ]
    out += _tabela(
        ["chave", "caminho", "bytes", "SHA-256", "confere"],
        [
            [
                f["chave"],
                f"`{f['caminho']}`",
                f.get("bytes"),
                f"`{f.get('sha256')}`",
                f.get("sha256_confere", ""),
            ]
            for f in p["fontes"]
        ],
    )
    out += ["", "## Controles", ""]
    out += _tabela(
        ["controle", "esperado", "obtido", "passou"],
        [
            [
                c["nome"],
                n(c["esperado"]),
                n(c["obtido"]),
                "sim" if c["passou"] else "NÃO",
            ]
            for c in controles
        ],
    )
    out += ["", "## Decisões que o contrato não previa", ""]
    out += [f"- {d}" for d in decisoes]
    out += ["", "## Categorias (registro de cada seção como o TSE publica)", ""]
    out += _tabela(
        ["categoria", "nome", "seções", "eleitores"],
        [
            [c, p["regras"]["nomes"][c], v["secoes"], v["eleitores"]]
            for c, v in sorted(r["por_categoria_cadastro"].items())
        ],
    )
    out += ["", "Camada efetiva (agregada herda a principal):", ""]
    out += _tabela(
        ["categoria", "mudança real", "seções", "eleitores"],
        [
            [x["categoria"], x["mudanca_real"], x["secoes"], x["eleitores"]]
            for x in r["por_categoria_efetiva"]
        ],
    )
    fo = r["fora_do_original"]
    out += [
        "",
        "## Mudança real",
        "",
        f"- Seções: {n(mr['secoes'])} ({n(mr['secoes_principais'])} principais e "
        f"{n(mr['secoes_agregadas'])} agregadas), {n(mr['eleitores'])} eleitores, "
        f"{n(mr['aptos_1t'])} aptos nas urnas do 1º turno.",
        f"- Locais de origem {n(mr['locais_origem'])}, de destino {n(mr['locais_destino'])}, "
        f"pares {n(mr['pares'])}, municípios {n(mr['municipios'])}, UFs {n(mr['ufs'])}.",
        f"- Distância: mediana {n(mr['distancia_mediana_m'])} m, p90 "
        f"{n(mr['distancia_p90_m'])} m ({n(mr['secoes_com_distancia'])} seções com distância "
        "confiável).",
        "- Por categoria: "
        + "; ".join(
            f"{k} {n(v['secoes'])} seções / {n(v['eleitores'])} eleitores"
            for k, v in mr["por_categoria"].items()
        ),
        f"- Confiança média (E com outro logradouro, D com endereço igual): "
        f"{n(mr['confianca_media']['secoes'])} seções.",
        f"- Fora do original: 1º turno {n(fo['secoes_1t'])} seções / {n(fo['eleitores_1t'])} "
        f"eleitores; 2º turno {n(fo['secoes_2t'])} / {n(fo['eleitores_2t'])}.",
        f"- Sensibilidade: G contaria {n(r['sensibilidade']['g_se_contasse']['secoes'])} seções "
        f"({n(r['sensibilidade']['g_se_contasse']['eleitores'])} eleitores); F com nome de outra "
        f"instituição {n(r['sensibilidade']['f_nome_de_outra_instituicao']['secoes'])} seções.",
        "",
        "## Confronto com os números públicos",
        "",
    ]
    for it in p["confronto_publico"]["numeros_publicos"]:
        s = it["secoes"]
        e = it["eleitores"]
        out.append(
            f"- **{it['fonte']}** ({it['carimbo']}): hipótese mais próxima "
            f"`{it['hipotese_mais_proxima']}` ({it['descricao_hipotese']}), "
            f"{n(s['nosso'])} seções contra {n(s['publico'])} ({n(s['diferenca_pct'])}%)"
            + (
                f", {n(e['nosso'])} eleitores contra {n(e['publico'])} ({n(e['diferenca_pct'])}%)"
                if e
                else ""
            )
            + ". Não explica: "
            + " ".join(it["o_que_nao_explica"])
        )
    pc = p.get("confronto_painel")
    if pc:
        out += [
            "",
            "## Painel do TSE contra o arquivo de locais",
            "",
            f"União {n(pc['uniao'])}; ambos {n(pc['ambos'])}; só painel {n(pc['so_painel'])}; "
            f"só arquivo {n(pc['so_zip'])}; concordância {n(pc['concordancia_pct'])}%. "
            f"Nos que constam dos dois, nomes conferem em {n(pc['ambos_nomes_conferem'])} e o "
            f"eleitorado é {n(pc['ambos_eleitorado_painel'])} no painel contra "
            f"{n(pc['ambos_eleitores_zip'])} no arquivo.",
            "",
            pc["hipotese"]["resultado"],
            "",
            _originais(pc),
            "",
            f"Seções de mesmo número com prédio trocado (D e E): "
            f"{n(pc['mesmo_numero_outro_predio']['secoes_d_e_no_arquivo'])} no arquivo, "
            f"{n(pc['mesmo_numero_outro_predio']['secoes_d_e_com_mudanca_real'])} com mudança "
            f"real; listadas no painel: {n(pc['mesmo_numero_outro_predio']['listadas_no_painel'])}. "
            + pc["mesmo_numero_outro_predio"]["nota"],
        ]
    d = p["distancia"]
    t = d["teste_hipotese"]
    out += [
        "",
        "## Distância",
        "",
        f"- Novas realocações: mediana {ic(t['novas_realocacoes']['mediana_m'], ' m')}; acima de "
        f"1 km {ic(t['novas_realocacoes']['parcela_pct']['acima_1km'], '%')}; acima de 2 km "
        f"{ic(t['novas_realocacoes']['parcela_pct']['acima_2km'], '%')}.",
        f"- Categoria A no 1º turno: mediana {ic(t['categoria_a_no_1t']['mediana_m'], ' m')}.",
        f"- Prédio vizinho (país): mediana {ic(t['predio_vizinho']['mediana_m'], ' m')}; "
        f"das origens das novas: {ic(t['predio_vizinho_das_novas']['mediana_m'], ' m')}.",
        f"- Diferenças: novas menos A {ic(t['diferencas_m']['novas_menos_a'], ' m')}; novas "
        f"menos vizinho {ic(t['diferencas_m']['novas_menos_vizinho'], ' m')}.",
        "",
        "## Comportamento no 1º turno",
        "",
    ]
    for g, v in p["comportamento_1t"]["grupos"].items():
        mm = v["metricas"]
        out.append(
            f"- {g} ({n(v['urnas'])} urnas): abstenção contra o município "
            f"{ic(mm['abstencao']['mesmo_municipio']['diferenca_pp'])}, contra o país "
            f"{ic(mm['abstencao']['pais']['diferenca_pp'])}; Flávio nos válidos contra o "
            f"município {ic(mm['flavio_validos']['mesmo_municipio']['diferenca_pp'])}, contra "
            f"o país {ic(mm['flavio_validos']['pais']['diferenca_pp'])}; Lula contra o "
            f"município {ic(mm['lula_validos']['mesmo_municipio']['diferenca_pp'])}."
        )
    out.append(
        f"- Teste da categoria A: {p['comportamento_1t']['teste_abstencao_categoria_a']['resposta']}"
    )
    out += ["", "## Intercorrências no 1º turno (razão contra o país)", ""]
    for g, v in p["intercorrencias_1t"]["grupos"].items():
        partes = [f"{k} {ic(m['pais']['razao'], '')}" for k, m in v["metricas"].items()]
        out.append(f"- {g}: " + "; ".join(partes) + ".")
    e = p["efeito_1t"]
    dd = e["dif_em_dif"]
    out += [
        "",
        "## Efeito medido no 1º turno",
        "",
        f"Rótulo: {e['rotulo']}",
        "",
        f"- Tratamento: {n(e['tratamento']['secoes_cadastro'])} seções / "
        f"{n(e['tratamento']['eleitores_cadastro'])} eleitores no cadastro; "
        f"{n(e['tratamento']['urnas'])} urnas com boletim no Brasil.",
        f"- Abstenção contra o município: {ic(e['abstencao']['mesmo_municipio']['diferenca_pp'])}; "
        f"contra o país: {ic(e['abstencao']['pais']['diferenca_pp'])}.",
        f"- Diferença em diferenças (2026 1T menos 2022 2T): {ic(dd['diferenca']['mesmo_municipio']['diferenca_pp'])} "
        f"contra estáveis do município; cobertura {n(dd['cobertura']['temp_1t']['cobertura_pct'])}%.",
        f"- Direção: Flávio {ic(e['direcao']['flavio_validos']['mesmo_municipio']['diferenca_pp'])}; "
        f"Lula {ic(e['direcao']['lula_validos']['mesmo_municipio']['diferenca_pp'])} (contra o município).",
        f"- Troca de prédio desde 2022: {n(e['troca_desde_2022']['urnas'])} urnas; diferença em "
        f"diferenças {ic(e['troca_desde_2022']['dif_em_dif']['mesmo_municipio']['diferenca_pp'])}.",
        "- Dose e resposta (categoria A, diferença em diferenças contra o município): "
        + "; ".join(
            f"{f['faixa']} ({n(f['urnas_casadas_2022'])} urnas) "
            f"{ic(f['dif_em_dif']['mesmo_municipio']['diferenca_pp'])}"
            for f in e["dose_resposta"]["faixas"]
        ),
        f"- Rio de Janeiro, transferidas contra estáveis da mesma zona: abstenção "
        f"{ic(e['rj']['abstencao_mesma_zona']['diferenca_pp'])}, diferença em diferenças "
        f"{ic(e['rj']['dif_em_dif_mesma_zona']['diferenca_pp'])}.",
        _z161(e["rj"]["zona_161"]),
        f"- {e['rj']['premissa_que_caiu']}",
        "",
        "## Cenários",
        "",
    ]
    for f in p["cenarios_abstencao"]["fixos"]:
        c = f["mudanca_real"]
        out.append(
            f"- +{n(f['abstencao_extra_pp'])} pontos nas urnas com mudança real: Flávio perde "
            f"{n(c['perdidos']['flavio'])}, Lula {n(c['perdidos']['lula'])}; diferença F menos L "
            f"varia {n(c['variacao_diferenca_flavio_menos_lula_votos'])} votos "
            f"({n(c['variacao_diferenca_pp_validos_nacionais'], 4)} ponto dos válidos)."
        )
    br = p["cenarios_abstencao"]["estimativa_brasileira"]
    if "saldo_1t_para_2t" in br:
        fora = br["seguem_fora_do_original_2t"]["central"]
        out += [
            f"- Estimativa brasileira ({n(br['magnitude_pp']['central'])} ponto, IC "
            f"{n(br['magnitude_pp']['ic95'][0])} a {n(br['magnitude_pp']['ic95'][1])}): "
            f"nas {n(fora['urnas'])} urnas fora do original em 25/10, Flávio perde "
            f"{n(fora['perdidos']['flavio'])} e Lula {n(fora['perdidos']['lula'])} em relação "
            "a votar no original; diferença entre os dois: "
            f"{_sentido(fora['variacao_diferenca_flavio_menos_lula_votos'])}.",
            "- Saldo entre turnos (novas perdem, A recupera): "
            + _sentido(
                br["saldo_1t_para_2t"]["central"][
                    "variacao_diferenca_flavio_menos_lula_votos"
                ]
            )
            + ".",
        ]
    rio = p["cenarios_abstencao"].get("estimativa_rio", {})
    if "seguem_fora_do_original_2t" in rio:
        f2 = rio["seguem_fora_do_original_2t"]
        out.append(
            f"- Teto pelo Rio ({n(rio['magnitude_pp']['central'])} ponto): nas urnas fora do "
            f"original, Flávio perde {n(f2['perdidos']['flavio'])} e Lula "
            f"{n(f2['perdidos']['lula'])}; diferença: "
            f"{_sentido(f2['variacao_diferenca_flavio_menos_lula_votos'])}."
        )
    out += ["", "## Quem perde", ""]
    out += [f"- {v}" for v in p["quem_perde"].values()]
    cr = p["clima_resumo"]
    out += ["", "## Clima e notas dos TREs", "", f"- Clima: {cr.get('situacao')}."]
    if cr.get("situacao") == "ok":
        for g in ("origem_mudanca_real", "origem_qualquer_alteracao", "controle"):
            x = cr[g]
            out.append(
                f"  - {g}: {n(x['com_dado'])} locais com dado; chuva em 04/10 acima de 20 mm "
                f"{n(x['chuva_04_10_acima_20mm_pct'])}%, acima de 50 mm "
                f"{n(x['chuva_04_10_acima_50mm_pct'])}%; máximo de 05 a 18/10 acima de 20 mm "
                f"{n(x['chuva_max_05a18_acima_20mm_pct'])}%, acima de 50 mm "
                f"{n(x['chuva_max_05a18_acima_50mm_pct'])}%; rajada acima de 60 km/h "
                f"{n(x['rajada_acima_60kmh'])}."
            )
        dif = cr["origem_mudanca_real_menos_controle_pp"]
        out.append(
            "  - origem com mudança real menos controle: máximo de 05 a 18/10 acima de 20 mm "
            f"{ic(dif['chuva_max_05a18_acima_20mm'])}; chuva em 04/10 acima de 20 mm "
            f"{ic(dif['chuva_04_10_acima_20mm'])}; rajada acima de 60 km/h "
            f"{ic(dif['rajada_acima_60kmh'])}; sem chuva acima de 10 mm nem rajada acima de "
            f"50 km/h no período: {n(cr['origem_mudanca_real_sem_chuva_nem_vento']['quantidade'])} "
            "locais de origem."
        )
    out.append(f"- Notas dos TREs: {p['tre_resumo']}")
    out += ["", "## Limites", ""]
    out += [f"- {x}" for x in p["limites"]]
    out += [
        "",
        "## Reprodução",
        "",
        "```",
        "python3 scripts/mudancas-secoes-2t.py",
        "pytest -q tests/test_mudancas_secoes_2t.py",
        "ruff check scripts/mudancas_secoes_2t scripts/mudancas-secoes-2t.py "
        "tests/test_mudancas_secoes_2t.py",
        "```",
        "",
    ]
    return "\n".join(out)
