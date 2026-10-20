"""Relatório em Markdown: todos os números com intervalo, controles e decisões.

Tudo sai do payload; nenhum número é digitado aqui.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from clima_1t.texto import _br, _coef, _ic, _or

NOMES_EXP = {
    "chuva_votacao": "chuva nas horas de votação (7h às 18h de Brasília)",
    "chuva_diaria": "chuva no dia 04/10",
    "rajada_votacao": "rajada máxima nas horas de votação",
    "rajada_diaria": "rajada máxima no dia 04/10",
}
NOMES_X = {
    "chuva_votacao_x": "chuva nas horas de votação, por 10 mm",
    "chuva_diaria_x": "chuva no dia, por 10 mm",
    "rajada_votacao_x": "rajada nas horas de votação, por 10 km/h",
    "rajada_diaria_x": "rajada no dia, por 10 km/h",
    "chuva_estrita_x": "chuva das 8h às 17h de Brasília, por 10 mm",
    "bat": "bateria durante a votação",
    "chuva_x_bat": "chuva × bateria",
}


NOMES_MEDIDA = {
    "abstencao_2026": "abstenção de 2026",
    "dif_contra_2022": "2026 menos 2022",
}
NIVEIS = {"alto": "alto", "medio": "médio", "baixo": "baixo", "sem_dado": "sem dado"}
NOMES_FE = {"fe_uf": "UF", "fe_municipio": "município"}
NOMES_CADEIA = {
    "chuva_forte_no_dia": "chuva forte no dia (mais de 20 mm)",
    "chuva_moderada_ou_mais_nas_horas_de_votacao": "chuva moderada ou mais nas horas "
    "de votação (mais de 5 mm)",
}


def _tab(cab: list[str], linhas: Sequence[Sequence[Any]]) -> list[str]:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    out += ["| " + " | ".join(str(c) for c in linha) + " |" for linha in linhas]
    return [*out, ""]


def _cobertura(p: dict[str, Any]) -> list[str]:
    c = p["cobertura"]
    a = c["archive"]
    out = ["## Cobertura", ""]
    out.append(
        f"- Células de 0,25° com local de votação: {_br(a['celulas'])}; com resposta da "
        f"Open-Meteo: {_br(a['coletadas'])} (faltam {_br(a['faltando'])}); valores nulos: "
        f"{_br(a['valores_nulos'])}; requisições registradas: {_br(a['requisicoes'])}."
    )
    out.append(
        f"- Locais do Brasil: {_br(c['locais_brasil'])}; com coordenada no território: "
        f"{_br(c['locais_com_coordenada'])}; com clima: {_br(c['locais_com_clima'])}."
    )
    out.append(
        f"- Urnas do Brasil com boletim: {_br(c['urnas_brasil'])}; na amostra analítica "
        f"(com clima e aptos): {_br(c['urnas_amostra'])}, em "
        f"{_br(c['celulas_na_amostra'])} células."
    )
    out.append("")
    return out


def _janela(p: dict[str, Any]) -> list[str]:
    j = p["janela_votacao"]
    out = [
        "## Janela de votação e relógio",
        "",
        f"- Regra: {j['regra']}; {j['motivo']}.",
    ]
    out += [f"- {k}: {v} locais." for k, v in j["local"].items()]
    out += [f"- Sensibilidade: {j['estrita']}.", f"- Convenção: {j['convencao']}.", ""]
    return out


def _bateria(p: dict[str, Any]) -> list[str]:
    b = p["bateria_x_chuva"]
    out = ["## 1. Bateria e reinício contra chuva e vento", ""]
    out += [f"Unidade: {b['unidade']}. IC: {b['ic']}.", ""]
    out += ["Denominadores:", ""]
    out += [f"- `{k}`: {v}." for k, v in b["desfechos"].items()]
    out.append("")
    for exp, bloco in b["por_exposicao"].items():
        for desfecho in ("bateria_votacao", "bateria_simultanea", "bateria_isolada"):
            out += [f"### {NOMES_EXP[exp]}: `{desfecho}`", ""]
            linhas = [
                [
                    x["rotulo"],
                    _br(x["celulas"]),
                    _br(x["urnas"]),
                    _br(x["com_registro"]),
                    _ic(x["parcela_pct"], "%"),
                    (
                        "referência"
                        if x["razao_vs_ref"] is None
                        else _ic(x["razao_vs_ref"])
                    ),
                ]
                for x in bloco["faixas"][desfecho]
            ]
            out += _tab(
                [
                    "faixa",
                    "células",
                    "urnas",
                    "com registro",
                    "parcela",
                    "razão contra a referência",
                ],
                linhas,
            )
    r = b["regressoes"]
    out += ["### Regressões logísticas", "", r["modelo"] + ".", ""]
    linhas = []
    for desfecho, modelos in r["desfechos"].items():
        for m in modelos:
            for termo, v in m["termos"].items():
                linhas.append(
                    [
                        f"`{desfecho}`",
                        NOMES_X.get(termo, termo),
                        _or(v),
                        _br(m["n"]),
                        _br(m["eventos"]),
                    ]
                )
    out += _tab(["desfecho", "exposição", "odds ratio", "urnas", "eventos"], linhas)
    rob = r["robustez_municipio"]
    out += [rob["modelo"] + ":", ""]
    for m in rob["bateria_votacao"]:
        for termo, v in m["termos"].items():
            out.append(
                f"- {NOMES_X.get(termo, termo)}: {_coef(v)}; "
                f"{_br(m['municipios_informativos'])} municípios informativos, {_br(m['n'])} urnas."
            )
    out.append("")
    return out


def _linhas_abst(lista: list[dict[str, Any]]) -> list[list[str]]:
    return [
        [
            x["grupo"],
            _br(x["urnas"]),
            _br(x["celulas"]),
            _br(x["aptos"]),
            _ic(x["abst_pct"], "%"),
            (
                "referência"
                if x["abst_vs_ref_pp"] is None
                else _ic(x["abst_vs_ref_pp"], " pp")
            ),
            _ic(x["dif_abst_pp"], " pp"),
            (
                "referência"
                if x["dif_vs_ref_pp"] is None
                else _ic(x["dif_vs_ref_pp"], " pp")
            ),
        ]
        for x in lista
    ]


CAB_ABST = [
    "grupo",
    "urnas",
    "células",
    "aptos",
    "abstenção 2026",
    "contra a referência",
    "2026 menos 2022",
    "contra a referência",
]


def _dentro(titulo: str, d: dict[str, Any]) -> list[str]:
    out = [
        f"{titulo} ({_br(d.get('estratos', 0))} estratos com a referência e outro grupo):",
        "",
    ]
    for nome, g in (d.get("grupos") or {}).items():
        out.append(
            f"- {nome}: abstenção {_ic(g['abst_vs_ref_pp'], ' pp')}; 2026 menos 2022 "
            f"{_ic(g['dif_vs_ref_pp'], ' pp')}; {_br(g['estratos_com_os_dois'])} estratos."
        )
    out.append("")
    return out


def _abstencao(p: dict[str, Any]) -> list[str]:
    a = p["abstencao_x_chuva"]
    out = ["## 2. Abstenção contra chuva e vento", ""]
    out += [f"- `{k}`: {v}." for k, v in a["medidas"].items()]
    out.append("")
    for exp, bloco in a["por_exposicao"].items():
        out += [f"### {NOMES_EXP[exp]}", ""]
        out += _tab(CAB_ABST, _linhas_abst(bloco["pais"]))
        out += _dentro("Dentro da mesma UF", bloco["dentro_da_uf"])
        out += _dentro("Dentro do mesmo município", bloco["dentro_do_municipio"])
    out += ["### Cortes binários", "", a["binario"]["regra"] + ".", ""]
    for exp, bloco in a["binario"].items():
        if exp == "regra":
            continue
        out += [f"#### {NOMES_EXP[exp]}, corte em {_br(bloco['corte'], 0)}", ""]
        out += _tab(CAB_ABST, _linhas_abst(bloco["pais"]))
        out += _dentro("Dentro da mesma UF", bloco["dentro_da_uf"])
        out += _dentro("Dentro do mesmo município", bloco["dentro_do_municipio"])
    cb = a["chuva_forte_e_bateria"]
    out += ["### Chuva forte e bateria", "", cb["regra"] + ".", ""]
    out += _tab(CAB_ABST, _linhas_abst(cb["pais"]))
    out += _dentro("Dentro do mesmo município", cb["dentro_do_municipio"])
    r = a["regressoes"]
    out += ["### Regressões lineares", "", r["modelo"] + ".", ""]
    linhas = []
    for medida in ("abstencao_2026", "dif_contra_2022"):
        for mods in r[medida].values():
            for fe, m in mods.items():
                for termo, v in m["termos"].items():
                    linhas.append(
                        [
                            NOMES_MEDIDA[medida],
                            NOMES_X.get(termo, termo),
                            NOMES_FE[fe],
                            _coef(v),
                            _br(m["n"]),
                        ]
                    )
    out += _tab(["medida", "exposição", "efeito fixo", "coeficiente", "urnas"], linhas)
    it = r["interacao_chuva_bateria"]
    out += ["Interação chuva × bateria (" + it["termos"] + "):", ""]
    for medida in ("abstencao_2026", "dif_contra_2022"):
        for fe, m in it[medida].items():
            for termo, v in m["termos"].items():
                out.append(
                    f"- {NOMES_MEDIDA[medida]}, {NOMES_FE[fe]}, "
                    f"{NOMES_X.get(termo, termo)}: {_coef(v)}."
                )
    out.append("")
    return out


def _abst_bateria(p: dict[str, Any]) -> list[str]:
    b = p["abstencao_x_bateria"]
    out = ["## 3. Abstenção contra bateria", ""]
    out += [
        f"- Denominador: {b['denominador']}.",
        f"- Tempo em bateria: {b['tempo_em_bateria']}.",
        "",
    ]
    out += _tab(CAB_ABST, _linhas_abst(b["pais"]))
    out += _dentro("Dentro do mesmo município", b["dentro_do_municipio"])
    out += _dentro("Dentro do mesmo prédio", b["dentro_do_predio"])
    out += ["Por tipo de bateria:", ""]
    out += _tab(CAB_ABST, _linhas_abst(b["por_tipo"]["pais"]))
    out += _dentro(
        "Por tipo, dentro do mesmo município", b["por_tipo"]["dentro_do_municipio"]
    )
    out += _dentro(
        "Por tipo, dentro do mesmo prédio", b["por_tipo"]["dentro_do_predio"]
    )
    r = b["regressao"]
    out += [r["modelo"] + ":", ""]
    for medida in ("abstencao_2026", "dif_contra_2022"):
        v = r[medida]["termos"]["bat"]
        out.append(
            f"- {NOMES_MEDIDA[medida]}: {_coef(v)}; {_br(r[medida]['n'])} urnas."
        )
    out.append("")
    return out


def _cadeia(p: dict[str, Any]) -> list[str]:
    c = p["cadeia_completa"]
    out = ["## 4. Cadeia completa", "", c["regra"] + ".", ""]
    for nome, v in c["variantes"].items():
        out += [f"### {NOMES_CADEIA.get(nome, nome)}", ""]
        out += _tab(
            ["chuva", "bateria", "abstenção alta", "urnas", "aptos"],
            [
                [
                    "sim" if x["chuva"] else "não",
                    "sim" if x["bateria"] else "não",
                    "sim" if x["abst_alta"] else "não",
                    _br(x["urnas"]),
                    _br(x["aptos"]),
                ]
                for x in v["celulas_2x2x2"]
            ],
        )
        out += _tab(
            ["chuva", "bateria", "urnas", "abstenção acima da mediana do município"],
            [
                [
                    "sim" if x["chuva"] else "não",
                    "sim" if x["bateria"] else "não",
                    _br(x["urnas"]),
                    f"{_br(x['abst_alta_pct'])}%",
                ]
                for x in v["abst_alta_por_combinacao"]
            ],
        )
    return out


def _curiosos(p: dict[str, Any]) -> list[str]:
    c = p["locais_curiosos"]
    out = ["## 5. Locais curiosos", ""]
    for nome, lista in c.items():
        if "itens" not in lista:
            continue
        out += [f"### {nome}", "", lista["regra"] + ".", ""]
        out.append(
            f"Atendem à regra: {_br(lista['total_que_atende'])}. Os cinco primeiros:"
        )
        out.append("")
        out += _tab(
            [
                "local",
                "município",
                "chuva dia",
                "chuva votação",
                "urnas",
                "bateria votação",
                "abst.",
                "2026 menos 2022",
            ],
            [
                [
                    f"[{x['nome']}]({x['mapa']})",
                    f"{x['municipio']} ({x['uf']})",
                    _br(x["chuva_04_10_mm"], 1),
                    _br(x["chuva_votacao_mm"], 1),
                    _br(x["urnas"]),
                    _br(x["urnas_bateria_votacao"]),
                    _br(x["abst_pct"]),
                    _br(x["dif_abst_pp"]),
                ]
                for x in lista["itens"][:5]
            ],
        )
    f = c["f_mudancas_2t"]
    out += ["### f. Mudanças do 2º turno e Confresa (MT)", ""]
    out.append(
        f"Pares com mudança real: {_br(f['pares_mudanca_real'])}; origens distintas: "
        f"{_br(f['origens_distintas'])}; com clima: {_br(f['origens_com_clima'])}."
    )
    out.append("")
    cab = [
        "grupo",
        "locais",
        "aptos",
        "chuva média",
        "locais com chuva forte",
        "bateria na votação",
        "abstenção",
        "2026 menos 2022",
    ]
    linhas = []
    for nome, g in (
        ("origens das mudanças", f["origens"]),
        ("demais locais", f["demais_locais"]),
        ("Confresa (MT)", f["confresa_mt"]["municipio"] or {}),
    ):
        linhas.append(
            [
                nome,
                _br(g.get("locais")),
                _br(g.get("aptos")),
                _br(g.get("chuva_04_10_media_mm")),
                f"{_br(g.get('locais_chuva_forte_pct'))}%",
                f"{_br(g.get('urnas_bateria_votacao_pct'))}%",
                f"{_br(g.get('abst_pct'))}%",
                _br(g.get("dif_abst_pp")),
            ]
        )
    out += _tab(cab, linhas)
    return out


def _resumo_uf(p: dict[str, Any]) -> list[str]:
    out = ["## 6. Resumo por UF", ""]
    out += _tab(
        [
            "UF",
            "urnas",
            "chuva média no dia (mm)",
            "chuva média na votação (mm)",
            "locais com chuva forte",
            "urnas com bateria na votação",
            "abstenção",
            "2026 menos 2022",
        ],
        [
            [
                x["uf"],
                _br(x["urnas"]),
                _br(x["chuva_04_10_media_mm"]),
                _br(x["chuva_votacao_media_mm"]),
                f"{_br(x['locais_chuva_forte_pct'])}%",
                f"{_br(x['urnas_bateria_votacao_pct'])}%",
                f"{_br(x['abst_pct'])}%",
                _br(x["dif_abst_pp"]),
            ]
            for x in p["mapa_resumo"]
        ],
    )
    return out


def _previsao(p: dict[str, Any]) -> list[str]:
    v = p["previsao_25_10"]
    out = ["## 7. Previsão para 25/10", ""]
    if "pais" not in v:
        return [*out, v.get("situacao", "sem previsão"), ""]
    out += [f"Gerada em {v['gerado_em']}. {v['rotulo']}", ""]
    out += [
        f"- {NIVEIS.get(k, k)}: {t}."
        for k, t in v["regra_risco"].items()
        if isinstance(t, str)
    ]
    out.append("")
    pais = v["pais"]
    out += _tab(
        ["nível", "eleitores", "locais", "células"],
        [
            [
                NIVEIS.get(n, n),
                _br(pais["eleitores"][n]),
                _br(pais["locais"][n]),
                _br(pais["celulas"][n]),
            ]
            for n in pais["eleitores"]
        ],
    )
    out += ["Cidades com mais eleitores em risco alto:", ""]
    out += _tab(
        [
            "município",
            "eleitores em risco alto",
            "locais",
            "chuva máxima (mm)",
            "rajada máxima (km/h)",
        ],
        [
            [
                f"{c['municipio']} ({c['uf']})",
                _br(c["eleitores_risco_alto"]),
                _br(c["locais_risco_alto"]),
                _br(c["chuva_mm_max"], 1),
                _br(c["rajada_kmh_max"], 1),
            ]
            for c in v["cidades_risco_alto"]
        ],
    )
    return out


def _fim(p: dict[str, Any]) -> list[str]:
    out = ["## Conferências", ""]
    cp = p["conferencia_pontos"]
    if "pares" in cp:
        out.append(
            f"- Ponto exato contra célula ({cp['regra']}): {_br(cp['pares'])} pares, "
            f"correlação {_br(cp['correlacao'], 4)}, diferença absoluta média "
            f"{_br(cp['diferenca_media_absoluta_mm'], 2)} mm (mediana "
            f"{_br(cp['diferenca_mediana_absoluta_mm'], 2)} mm), mesma faixa em "
            f"{_br(cp['mesma_faixa_pct'])}%."
        )
    pz = p["conferencia_politize"]
    out.append(
        f"- Politize: {_br(pz['secoes_conferidas'])} seções conferidas, {_br(pz['iguais'])} "
        f"iguais, {_br(pz['diferentes'])} diferentes."
    )
    out += ["", "## Controles", ""]
    out += _tab(
        ["controle", "esperado", "obtido", "passou"],
        [
            [c["nome"], c["esperado"], c["obtido"], "sim" if c["passou"] else "não"]
            for c in p["controles"]
        ],
    )
    out += ["## Fontes", ""]
    out += _tab(
        ["fonte", "caminho", "bytes", "SHA-256"],
        [
            [
                f["descricao"],
                f"`{f['caminho']}`",
                _br(f.get("bytes")),
                f"`{f.get('sha256', 'ausente')}`",
            ]
            for f in p["fontes"]
        ],
    )
    out += ["## Limites", ""] + [f"- {x}" for x in p["limites"]] + [""]
    out += ["## Decisões", ""] + [f"- {x}" for x in p["decisoes"]] + [""]
    return out


def montar(p: dict[str, Any]) -> str:
    out = [
        "# Clima, bateria e abstenção no 1º turno de 2026: relatório do motor",
        "",
        f"Gerado em {p['gerado_em']} por `scripts/clima-1t.py` "
        f"({_br(p['parametros']['reps'])} réplicas, semente {p['parametros']['seed']}). "
        "Contrato em `analysis/clima_1t_2026/CONTRATO.md`; payload em "
        "`analysis/clima_1t_2026/clima.json`.",
        "",
        "Registro de bateria é operação prevista da urna, não irregularidade; correlação não "
        "é causa; leitura agregada por seção e por local.",
        "",
    ]
    out += ["## Achados", ""] + [f"- {a}" for a in p.get("achados", [])] + [""]
    for parte in (
        _cobertura,
        _janela,
        _bateria,
        _abstencao,
        _abst_bateria,
        _cadeia,
        _curiosos,
        _resumo_uf,
        _previsao,
        _fim,
    ):
        out += parte(p)
    return "\n".join(out).rstrip() + "\n"
