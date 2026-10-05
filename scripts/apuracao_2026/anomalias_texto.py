"""Empacota a camada de anomalias em JSON e escreve o relatório em Markdown.

Todo número do Markdown sai do pacote JSON montado aqui; nada é digitado à mão.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter

import numpy as np
from apuracao_2026 import anomalias as an

NOMES_CANDIDATOS = {
    "RENAN SANTOS": "Renan Santos",
    "HERTZ DIAS": "Hertz Dias",
    "EDMILSON COSTA": "Edmilson Costa",
    "CLARIANA BARAO": "Clariana Barão",
    "RUI COSTA PIMENTA": "Rui Costa Pimenta",
    "ZEMA": "Zema",
    "VETERINÁRIO WILSON GRASSI": "Wilson Grassi",
    "RONALDO CAIADO": "Caiado",
    "ESCRITOR AUGUSTO CURY": "Augusto Cury",
    "SAMARA": "Samara",
}
ESCORE_VIZINHO = 95.0
COLUNAS_ZONAS = [
    "uf",
    "municipio",
    "ibge",
    "zona",
    "escore",
    "escore_eleitoral",
    "escore_operacional",
    "lat",
    "lon",
    "eleitorado",
    "secoes",
    "flavio_pct",
    "lula_pct",
    "d_flavio_1t_pp",
    "d_lula_1t_pp",
    "d_comparecimento_pp",
    "brancos_nulos_pct",
    "terceiros_pct",
    "residuo_hierarquico_pp",
    "conclusao_brasilia",
    "referencia_2022",
]
ROTULO_MODELO = {
    "z_rms": "z robusto (raiz da média dos quadrados)",
    "mahalanobis": "Mahalanobis robusta (numpy)",
    "isolation_forest": "Isolation Forest (scikit-learn)",
    "lof": "Local Outlier Factor (scikit-learn)",
}


def br(valor: float, casas: int = 1, sinal: bool = False) -> str:
    """Número com vírgula decimal; ``sinal`` força o + nos positivos."""
    if valor is None or not np.isfinite(valor):
        return "n/d"
    formato = f"{{:{'+' if sinal else ''}.{casas}f}}"
    return formato.format(valor).replace(".", ",")


def inteiro(valor: int) -> str:
    return f"{int(valor):,}".replace(",", ".")


def _r(valor, casas=2):
    if valor is None:
        return None
    valor = float(valor)
    return round(valor, casas) if np.isfinite(valor) else None


def _sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFKD", (texto or "").upper())
    return "".join(ch for ch in base if not unicodedata.combining(ch)).strip()


MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "d"}


def titulo_br(nome: str) -> str:
    """Caixa de título com preposições em minúscula: "São João do Triunfo"."""
    palavras = (nome or "").lower().split()
    return " ".join(
        (
            p
            if (i and p in MINUSCULAS)
            else "-".join(q[:1].upper() + q[1:] for q in p.split("-"))
        )
        for i, p in enumerate(palavras)
    )


def _nome_candidato(nome: str) -> str:
    return NOMES_CANDIDATOS.get(nome, nome.title())


def _motivo(nome, i, linha, atributos, resultado, definicoes, mediana_atraso):
    rotulo, unidade, _ = definicoes[nome]
    z = resultado["z"][nome][i]
    centro = resultado["centros"][nome].get(linha["uf"], float("nan"))
    valor = atributos[nome][i]
    if nome == "log_atraso":
        extra = linha["atraso_min"] - mediana_atraso[linha["uf"]]
        return (
            f"conclusão em {linha['conclusao_brasilia']} (Brasília), "
            f"{br(extra, 0)} min depois da mediana da UF (z {br(z, 1, True)})"
        )
    if nome == "versoes_residuo":
        return (
            f"{linha['n_versoes']} versões do arquivo da zona, acima do esperado "
            f"para {linha['secoes']} seções (z {br(z, 1, True)})"
        )
    if unidade == "razao":
        return (
            f"{rotulo}: {br(100 * np.expm1(valor), 1, True)}% (mediana da UF "
            f"{br(100 * np.expm1(centro), 1, True)}%; z {br(z, 1, True)})"
        )
    if unidade == "pp":
        return (
            f"{rotulo}: {br(100 * valor, 1, True)} pp (mediana da UF "
            f"{br(100 * centro, 1, True)}; z {br(z, 1, True)})"
        )
    return (
        f"{rotulo}: {br(100 * valor, 1)}% (mediana da UF {br(100 * centro, 1)}%; "
        f"z {br(z, 1, True)})"
    )


def _regra(frase: str) -> str:
    """Nome da regra de explicação, sem os números do caso."""
    base = frase.split(":")[0].split(" (")[0]
    return re.split(r" \d+%", base)[0]


def _contexto_por_municipio(contexto: dict) -> dict:
    saida: dict = {}
    for item in contexto.get("itens", []):
        for m in item.get("municipios", []) or []:
            chave = (_sem_acento(m.get("nome", "")), (m.get("uf") or "").upper())
            saida.setdefault(chave, []).append(item)
    return saida


def _resumo_contexto(contexto: dict) -> dict:
    itens = contexto.get("itens", [])
    return {
        "presente": bool(contexto),
        "n_itens": len(itens),
        "por_tema": dict(Counter(i.get("tema") for i in itens).most_common()),
        "por_degrau": dict(Counter(i.get("degrau") for i in itens).most_common()),
        "conferidos_na_pagina": sum(1 for i in itens if i.get("conferido") == "pagina"),
    }


def _tardias(linhas, atributos, resultado, limiar: float = 2.5) -> dict:
    """Zonas que fecharam tarde para a própria UF votaram diferente de 2022?

    Compara o resíduo hierárquico (variação da margem além da UF e do
    município) das zonas tardias com o das demais, ponderado pelos válidos.
    """
    z = resultado["z"]["log_atraso"]
    tarde = np.nan_to_num(z) >= limiar
    residuo = atributos["residuo_hierarquico"]
    validos = np.array([linha["validos"] for linha in linhas], dtype=float)
    lula = np.array([linha["lula"] for linha in linhas])
    lula22 = np.array([linha.get("lula_22_1t", np.nan) for linha in linhas])

    def media(valores, mascara) -> float:
        m = mascara & np.isfinite(valores)
        if not m.any():
            return float("nan")
        return float(np.average(valores[m], weights=validos[m]))

    ok = np.isfinite(residuo)
    resumo = {
        "criterio": f"z da hora de conclusão dentro da UF de {br(limiar)} ou mais",
        "n": int(tarde.sum()),
        "margem_swing_pp_tardias": _r(100 * media(atributos["margem_swing"], tarde)),
        "margem_swing_pp_demais": _r(100 * media(atributos["margem_swing"], ~tarde)),
        "swing_uf_pp_tardias": _r(100 * media(atributos["swing_uf"], tarde)),
        "swing_uf_pp_demais": _r(100 * media(atributos["swing_uf"], ~tarde)),
        "efeito_local_pp_tardias": _r(100 * media(atributos["efeito_local"], tarde)),
        "efeito_local_pp_demais": _r(100 * media(atributos["efeito_local"], ~tarde)),
        "residuo_medio_pp_tardias": _r(100 * media(residuo, tarde)),
        "residuo_medio_pp_demais": _r(100 * media(residuo, ~tarde)),
        "correlacao_atraso_residuo": _r(
            float(np.corrcoef(np.nan_to_num(z)[ok], residuo[ok])[0, 1]), 3
        ),
        "lula_2026_pct_tardias": _r(100 * media(lula, tarde)),
        "lula_2022_1t_pct_tardias": _r(100 * media(lula22, tarde)),
        "lula_2026_pct_demais": _r(100 * media(lula, ~tarde)),
        "lula_2022_1t_pct_demais": _r(100 * media(lula22, ~tarde)),
    }
    atraso = np.array([linha["atraso_min"] for linha in linhas], dtype=float)
    ordem = np.argsort(-np.nan_to_num(atraso, nan=-1e9), kind="stable")
    return {"resumo": resumo, "ordem": ordem}


def empacotar(
    *,
    linhas,
    atributos,
    resultado,
    reconciliacao,
    contexto,
    fontes,
    w1a,
    definicoes,
    n_topo,
    gerado_em,
    robustez=None,
) -> dict:
    """Monta o dicionário que vira ``anomalias.json``."""
    n = len(linhas)
    nomes = list(definicoes)
    escore = resultado["escore"]
    uf = np.array([linha["uf"] for linha in linhas])
    lat = np.array([linha["lat"] for linha in linhas], dtype=float)
    lon = np.array([linha["lon"] for linha in linhas], dtype=float)
    vizinhos = an.vizinhos_proximos(lat, lon, uf, np.arange(n).astype(str), k=5)
    atipica = escore >= ESCORE_VIZINHO
    vizinhos_atipicos = np.array([int(atipica[v].sum()) for v in vizinhos])
    mediana_atraso = {
        u: float(
            np.nanmedian([linha["atraso_min"] for linha in linhas if linha["uf"] == u])
        )
        for u in sorted(set(uf))
    }
    pcts = {k: 100.0 * an.percentis(v) for k, v in resultado["escores"].items()}
    por_municipio = _contexto_por_municipio(contexto)
    ordem = np.argsort(-escore, kind="stable")
    posicao = np.empty(n, dtype=int)
    posicao[ordem] = np.arange(1, n + 1)

    def registro(i: int) -> dict:
        linha = linhas[i]
        lider = linha["terceiro_lider"]
        regra = {
            "incompleta": linha["incompleta"],
            "st": linha["secoes_apuradas"],
            "ts": linha["secoes"],
            "referencia_2022": linha["referencia_2022"],
            "secoes": linha["secoes"],
            "eleitorado": linha["eleitorado"],
            "pct_indigena": linha["pct_indigena"],
            "pct_quilombola": linha["pct_quilombola"],
            "z_atraso": resultado["z"]["log_atraso"][i],
            "z_atraso_2022": resultado["z_atraso_2022"][i],
            "var_eleitorado": linha.get("var_eleitorado", float("nan")),
            "d_comparecimento": atributos["d_comparecimento"][i],
            "z_terceiros": resultado["z"]["terceiros"][i],
            "z_var_eleitorado": resultado["z"]["log_var_eleitorado"][i],
            "terceiro_lider": (_nome_candidato(lider[0]), lider[1]) if lider else None,
            "n_copias_antigas": linha["n_copias_antigas"],
            "vizinhos_atipicos": int(vizinhos_atipicos[i]),
        }
        z_linha = [resultado["z"][nome][i] for nome in nomes]
        motivos = [
            _motivo(nome, i, linha, atributos, resultado, definicoes, mediana_atraso)
            for nome, _z in an.motivos(z_linha, nomes)
        ]
        ctx = por_municipio.get((_sem_acento(linha["municipio"]), linha["uf"]), [])
        return {
            "posicao": int(posicao[i]),
            "escore": _r(escore[i], 1),
            "escore_eleitoral": _r(resultado["sub"]["eleitoral"][i], 1),
            "escore_operacional": _r(resultado["sub"]["operacional"][i], 1),
            "percentil_por_modelo": {k: _r(v[i], 1) for k, v in pcts.items()},
            "uf": linha["uf"],
            "municipio": linha["municipio"],
            "ibge": linha["ibge"],
            "municipio_tse": linha["municipio_tse"],
            "zona": linha["zona"],
            "lat": _r(linha["lat"], 4),
            "lon": _r(linha["lon"], 4),
            "fonte_coordenada": linha["fonte_coordenada"],
            "eleitorado": linha["eleitorado"],
            "secoes": linha["secoes"],
            "secoes_apuradas": linha["secoes_apuradas"],
            "comparecimento_pct": _r(100 * linha["comparecimento_pct"]),
            "flavio_pct": _r(100 * linha["flavio"]),
            "lula_pct": _r(100 * linha["lula"]),
            "terceiros_pct": _r(100 * linha["terceiros"]),
            "terceiro_lider": (
                {"nome": _nome_candidato(lider[0]), "pct": _r(100 * lider[1])}
                if lider
                else None
            ),
            "brancos_nulos_pct": _r(100 * linha["brancos_nulos"]),
            "referencia_2022": linha["referencia_2022"],
            "cobertura_ponte": _r(linha.get("cobertura_ponte"), 3),
            "bolsonaro_22_1t_pct": _r(100 * linha.get("bolsonaro_22_1t", float("nan"))),
            "bolsonaro_22_2t_pct": _r(100 * linha.get("bolsonaro_22_2t", float("nan"))),
            "lula_22_1t_pct": _r(100 * linha.get("lula_22_1t", float("nan"))),
            "lula_22_2t_pct": _r(100 * linha.get("lula_22_2t", float("nan"))),
            "comparecimento_22_pct": _r(
                100 * linha.get("comparecimento_22", float("nan"))
            ),
            "var_eleitorado_pct": _r(100 * linha.get("var_eleitorado", float("nan"))),
            "atributos_pp": {
                nome: _r(100 * atributos[nome][i])
                for nome in nomes
                if definicoes[nome][1] in ("pp", "%")
            },
            "esperado_hierarquico_pp": _r(100 * atributos["esperado_hierarquico"][i]),
            "fonte_efeito_local": str(atributos["fonte_efeito"][i]),
            "conclusao_brasilia": linha["conclusao_brasilia"],
            "atraso_vs_mediana_uf_min": _r(
                linha["atraso_min"] - mediana_atraso[linha["uf"]], 0
            ),
            "atraso_2022_min": _r(linha.get("atraso_2022_min"), 0),
            "fuso_horas_corrigido": linha["fuso_horas"],
            "n_versoes": linha["n_versoes"],
            "n_copias_antigas": linha["n_copias_antigas"],
            "n_idg_menor": linha["n_idg_menor"],
            "pct_indigena": _r(100 * linha["pct_indigena"], 1),
            "pct_quilombola": _r(100 * linha["pct_quilombola"], 1),
            "vizinhos_atipicos": int(vizinhos_atipicos[i]),
            "z": {nome: _r(resultado["z"][nome][i]) for nome in nomes},
            "motivos": motivos,
            "explicacao_provavel": an.explicacoes(regra),
            "contexto": [
                {
                    k: item.get(k)
                    for k in ("id", "titulo", "veiculo", "data", "url", "degrau")
                }
                for item in ctx
            ],
        }

    topo = [registro(int(i)) for i in ordem[:n_topo]]
    zonas = []
    for i in range(n):
        linha = linhas[i]
        zonas.append(
            [
                linha["uf"],
                linha["municipio"],
                linha["ibge"],
                linha["zona"],
                _r(escore[i], 1),
                _r(resultado["sub"]["eleitoral"][i], 1),
                _r(resultado["sub"]["operacional"][i], 1),
                _r(linha["lat"], 4),
                _r(linha["lon"], 4),
                linha["eleitorado"],
                linha["secoes"],
                _r(100 * linha["flavio"]),
                _r(100 * linha["lula"]),
                _r(100 * atributos["d_flavio_1t"][i]),
                _r(100 * atributos["d_lula_1t"][i]),
                _r(100 * atributos["d_comparecimento"][i]),
                _r(100 * linha["brancos_nulos"]),
                _r(100 * linha["terceiros"]),
                _r(100 * atributos["residuo_hierarquico"][i]),
                linha["conclusao_brasilia"],
                linha["referencia_2022"],
            ]
        )
    eleitorado = np.array([linha["eleitorado"] for linha in linhas])
    secoes = np.array([linha["secoes"] for linha in linhas])
    idx_topo = ordem[:n_topo]
    regras = Counter(
        _regra(frase) for item in topo for frase in item["explicacao_provavel"]
    )
    fusos = Counter(
        (linha["uf"], linha["fuso_horas"]) for linha in linhas if linha["fuso_horas"]
    )
    tardias = _tardias(linhas, atributos, resultado)
    resumo = {
        "tardias": tardias["resumo"],
        "n_zonas": n,
        "referencia_2022": dict(Counter(linha["referencia_2022"] for linha in linhas)),
        "zonas_incompletas": sum(1 for linha in linhas if linha["incompleta"]),
        "secoes_faltando_nas_zonas": int(
            sum(linha["secoes"] - linha["secoes_apuradas"] for linha in linhas)
        ),
        "zonas_com_copia_antiga": sum(
            1 for linha in linhas if linha["n_copias_antigas"]
        ),
        "eventos_copia_antiga": int(sum(linha["n_copias_antigas"] for linha in linhas)),
        "zonas_com_idg_menor": sum(1 for linha in linhas if linha["n_idg_menor"]),
        "eventos_idg_menor": int(sum(linha["n_idg_menor"] for linha in linhas)),
        "fuso_corrigido": {f"{u}:{h:+d}h": c for (u, h), c in sorted(fusos.items())},
        "eleitorado_mediano": {
            "todas": int(np.median(eleitorado)),
            "topo": int(np.median(eleitorado[idx_topo])),
        },
        "secoes_medianas": {
            "todas": int(np.median(secoes)),
            "topo": int(np.median(secoes[idx_topo])),
        },
        "pequenas_ate_30_secoes": {
            "todas_pct": _r(100 * float(np.mean(secoes <= 30)), 1),
            "topo": int(np.sum(secoes[idx_topo] <= 30)),
        },
        "topo_por_uf": dict(Counter(item["uf"] for item in topo).most_common()),
        "topo_por_regra": dict(regras.most_common()),
        "topo_com_padrao_regional": sum(
            1 for item in topo if item["vizinhos_atipicos"] >= 2
        ),
        "topo_sem_explicacao_estrutural": sum(
            1
            for item in topo
            if item["explicacao_provavel"][0].startswith("efeito político local")
        ),
        "escore_minimo_topo": topo[-1]["escore"] if topo else None,
    }
    metodo = {
        "atributos": {
            nome: {
                "descricao": d[0],
                "unidade": d[1],
                "ajuste_de_tamanho": d[2],
                "inclinacao_tamanho": _r(resultado["inclinacoes"].get(nome), 3),
            }
            for nome, d in definicoes.items()
        },
        "unilaterais": ["log_atraso", "versoes_residuo"],
        "z_robusto": "mediana e MAD (x1,4826) dentro da UF; escala da UF encolhida "
        "para a nacional com peso n/(n+20); desvio médio absoluto se o MAD for zero; "
        "atributo constante dá z = 0",
        "ajuste_tamanho": "z eleitoral dividido por exp(b x (log eleitorado - "
        "mediana)), b estimado nas faixas de tamanho, limitado a [0,5; 3]",
        "residuo_hierarquico": "margem Flávio menos Lula 2026 menos margem "
        "Bolsonaro menos Lula 1º turno 2022; expectativa = variação da UF + efeito "
        "local (outras zonas do município, deixa-uma-fora, ou 5 zonas vizinhas de "
        "outros municípios), encolhido por n/(n+2)",
        "modelos": {k: ROTULO_MODELO[k] for k in resultado["escores"]},
        "meta_modelos": resultado["meta"],
        "combinacao": "média dos percentis das leituras, de 0 a 100",
        "versoes_ajuste": {
            "inclinacao_log_secoes": _r(atributos["_versoes_ajuste"][0], 4),
            "intercepto": _r(atributos["_versoes_ajuste"][1], 4),
        },
        "referencias_2022": {
            "municipio": "município com um só par município-zona em 2026: o "
            "município inteiro de 2022 (mesmo território)",
            "zona": "mesma zona de 2022, com eleitorado coerente com o do "
            "município (|log razão| <= 0,20)",
            "locais": "zona redesenhada: locais de 2026 casados com os de 2022 "
            "pelo nome e endereço; aptos, comparecimento, brancos e nulos exatos "
            "por local; votos por candidato pela composição das zonas de 2022; "
            "exige 60% do eleitorado casado",
            "imprecisa": "ponte cobre menos de 60%: variações não calculadas",
            "ausente": "município sem 2022 (criado depois)",
        },
        "fuso": "o TSE grava a hora de totalização (ht) na hora local; o banco a "
        "converte como se fosse Brasília. A correção usa a menor diferença entre "
        "gerado_em e totalizado_em de cada zona, arredondada em horas",
        "vizinhos_atipicos": f"das 5 zonas mais próximas na UF, quantas têm "
        f"escore >= {ESCORE_VIZINHO:.0f}",
    }
    limites = [
        "Zona não é seção: a unidade aqui soma de "
        f"{int(secoes.min())} a {int(secoes.max())} seções, e um problema numa "
        "seção se dilui na zona.",
        "Variação contra 2022 não é fraude: candidatos diferentes (Flávio não é "
        "Jair, e a terceira via de 2026 não é a de 2022), prefeitos eleitos em "
        "2024, mudança de eleitorado e migração explicam a maior parte.",
        "Zona pequena tem variância maior; o ajuste de tamanho reduz, mas não "
        "elimina, o peso delas no topo.",
        "O escore é posição relativa dentro do país (percentil médio), não "
        "probabilidade de irregularidade; 1% das zonas sempre terá escore 99.",
        "Explicação provável é regra declarada sobre dados públicos, não "
        "verificação no local.",
        f"Os arquivos de zona do TSE pararam antes de 100% em "
        f"{resumo['zonas_incompletas']} zonas ({resumo['secoes_faltando_nas_zonas']}"
        " seções), embora os arquivos de UF tenham fechado: os números dessas "
        "zonas são parciais.",
    ]
    return {
        "titulo": "Anomalias por zona eleitoral, presidente, 1º turno de 2026",
        "gerado_em": gerado_em,
        "aviso": "Escore alto quer dizer zona atípica dentro da própria UF e pede "
        "explicação. Não é indício de fraude.",
        "fontes": fontes,
        "metodo": metodo,
        "limites": limites,
        "resumo": resumo,
        "reconciliacao_uf": reconciliacao,
        "contexto_resumo": _resumo_contexto(contexto),
        "contexto_nacional": [
            i
            for i in contexto.get("itens", [])
            if i.get("tema") in ("nota_tse_tre", "totalizacao_tardia")
        ],
        "cruzamento_zonas_w1a": w1a,
        "robustez": robustez or {},
        "topo": topo,
        "topo_tardias": [registro(int(i)) for i in tardias["ordem"][:15]],
        "mapa": [
            {
                "lat": item["lat"],
                "lon": item["lon"],
                "escore": item["escore"],
                "rotulo": f"{titulo_br(item['municipio'])} ({item['uf']}), zona "
                f"{int(item['zona'])}",
            }
            for item in topo
        ],
        "zonas_colunas": COLUNAS_ZONAS,
        "zonas": zonas,
    }


def gravar_json(pacote: dict) -> str:
    """JSON legível, com uma linha por zona na tabela completa."""
    corpo = dict(pacote)
    zonas = corpo.pop("zonas")
    texto = json.dumps(corpo, ensure_ascii=False, indent=1)
    linhas = ",\n  ".join(json.dumps(z, ensure_ascii=False) for z in zonas)
    return texto[:-2] + f',\n "zonas": [\n  {linhas}\n ]\n}}\n'


TEMA_ROTULO = {
    "urnas_substituidas": "urnas substituídas",
    "contingencia": "contingência",
    "secoes_anuladas": "seções anuladas",
    "violencia": "violência",
    "coercao": "coerção",
    "faccao_milicia": "facção ou milícia",
    "nota_tse_tre": "nota do TSE ou TRE",
    "forcas_armadas_pf": "Forças Armadas e PF",
    "logistica_remota": "logística remota",
    "totalizacao_tardia": "totalização tardia",
    "outro": "outro",
}


def _celula(texto: str) -> str:
    return texto.replace("|", "/").replace("\n", " ")


def _local(item: dict) -> str:
    return f"{titulo_br(item['municipio'])} ({item['uf']}), zona {int(item['zona'])}"


def _explicacao_com_contexto(item: dict) -> str:
    texto = "; ".join(item["explicacao_provavel"])
    ids = [c["id"] for c in item["contexto"] if c.get("id")]
    return f"{texto}; contexto: {', '.join(ids)}" if ids else texto


def _texto_regressivas(r: dict) -> str:
    total = r["eventos_copia_antiga"] + r["eventos_idg_menor"]
    if r["eventos_copia_antiga"]:
        antigas = (
            f"{r['eventos_copia_antiga']} eram cópia antiga de fato, com geração "
            f"anterior à versão já guardada ({r['zonas_com_copia_antiga']} zonas); "
            f"as outras {r['eventos_idg_menor']}"
        )
    else:
        antigas = f"Nenhuma era cópia antiga: as {total}"
    return (
        f"- O coletor marcou como regressivas {total} versões de arquivo de zona, "
        f"porque o contador `idg` do TSE caiu. {antigas} eram versões novas, "
        f"geradas depois da anterior, com `idg` menor ({r['zonas_com_idg_menor']} "
        "zonas). Por isso a versão usada aqui é a de maior hora de geração, não a "
        "última sem a marca.\n"
    )


def _texto_robustez(rob: dict) -> str:
    partes = []
    for v in rob.values():
        partes.append(
            f"{v['rotulo']}: {v['comuns_topo']} das {v['n_topo']} zonas do topo "
            f"repetem, correlação de postos {br(v['spearman'], 3)}"
        )
    return f"- Estabilidade: {'; '.join(partes)}.\n" if partes else ""


def markdown(pacote: dict) -> str:
    """Relatório em Markdown a partir do pacote JSON."""
    r = pacote["resumo"]
    m = pacote["metodo"]
    topo = pacote["topo"]
    ref = r["referencia_2022"]
    rec = [x for x in pacote["reconciliacao_uf"] if x["faltam_nas_zonas"]]
    fusos = ", ".join(
        f"{k.split(':')[0]} {k.split(':')[1]} ({v} {'zona' if v == 1 else 'zonas'})"
        for k, v in r["fuso_corrigido"].items()
    )
    modelos = "; ".join(m["modelos"].values())
    out: list[str] = []
    add = out.append
    add(f"# {pacote['titulo']}\n")
    add(
        f"Gerado em {pacote['gerado_em']} por `scripts/apuracao-2026-anomalias.py`. "
        "Dados em `analysis/apuracao_2026/dados/anomalias.json`.\n"
    )
    add(f"> {pacote['aviso']}\n")
    add("## O que é\n")
    add(
        f"Camada de triagem sobre os {inteiro(r['n_zonas'])} pares município-zona "
        "do Brasil no voto para presidente. Cada zona é comparada com a própria UF "
        "e com o próprio resultado de 2022. O escore de 0 a 100 diz quão atípica a "
        "zona é no país; a coluna de explicação diz por que ela provavelmente é "
        "atípica. A lista serve para escolher onde pedir boletim de urna, ata e "
        "log, não para concluir nada.\n"
    )
    add("## Método\n")
    add(
        "- Dados de 2026: arquivos de zona do TSE guardados pelo coletor "
        f"(`{pacote['fontes']['banco']['caminho']}`, só leitura), versão vigente de "
        "cada arquivo: a de maior hora de geração do TSE, com totais e votos por "
        "candidato (lidos do JSON original quando o coletor não os normalizou).\n"
        "- Base de 2022: votos por candidato por zona "
        f"(`{pacote['fontes']['votos_2022']['caminho']}`) e aptos, comparecimento, "
        f"brancos e nulos por seção (`{pacote['fontes']['secoes_2022']['caminho']}`). "
        f"Referência por zona em {inteiro(ref.get('zona', 0))} casos, pelo "
        f"município inteiro (mesmo território) em {inteiro(ref.get('municipio', 0))}, "
        f"recomposta pelos locais de votação em {ref.get('locais', 0)} zonas "
        f"redesenhadas, sem base em {ref.get('imprecisa', 0) + ref.get('ausente', 0)}.\n"
        "- Atributos: variação de Flávio contra Bolsonaro (1º e 2º turnos de 2022), "
        "variação de Lula, resíduo hierárquico da margem, variação do comparecimento, "
        "brancos e nulos (nível e variação), terceira via, variação do eleitorado, "
        "hora de conclusão da zona e versões do arquivo. Hora e versões contam só "
        "do lado tardio.\n"
        f"- z robusto: {m['z_robusto']}. Ajuste de tamanho: {m['ajuste_tamanho']}.\n"
        f"- Resíduo hierárquico: {m['residuo_hierarquico']}.\n"
        f"- Leituras: {modelos}. Combinação: {m['combinacao']}.\n"
        f"- Fuso: {m['fuso']}. Correções aplicadas: {fusos}.\n"
        "- Localização: média das coordenadas dos locais de votação da zona, "
        "ponderada pelo eleitorado e restrita ao retângulo do município; sem "
        "coordenada válida, centroide do município na malha do IBGE.\n"
    )
    add("## Verificado (dado do TSE, conta direta)\n")
    w1a = pacote["cruzamento_zonas_w1a"]
    if w1a.get("presente"):
        add(
            f"- Leitura conferida contra `{w1a['arquivo']}` (código independente, "
            f"mesmo banco): {w1a['diferentes']} diferenças em "
            f"{inteiro(w1a['zonas_aqui'])} zonas nos campos {w1a['campos']}.\n"
        )
    faltas = (
        ", ".join(f"{x['uf']} {x['faltam_nas_zonas']:+d}" for x in rec) or "nenhuma"
    )
    add(
        f"- Na última versão guardada pelo coletor, {r['zonas_incompletas']} "
        f"arquivos de zona estão abaixo de 100% ({r['secoes_faltando_nas_zonas']} "
        "seções), enquanto os arquivos de UF fecharam todas as seções. Diferença por UF (seções da UF menos soma das "
        f"zonas): {faltas}.\n"
        "- A hora de totalização (campo `ht`) dos arquivos de zona vem na hora "
        "local: a diferença entre a geração do arquivo e a totalização é de um "
        "minuto nas zonas de Brasília e de uma ou duas horas a mais nas de outro "
        f"fuso. Sem correção, essas zonas pareceriam terminar antes do real. "
        f"Correções: {fusos}.\n" + _texto_regressivas(r)
    )
    add("## As 25 zonas mais atípicas\n")
    add("Explicação provável é inferência por regra declarada, não verificação.\n")
    add(
        "| # | Escore | Zona | IBGE | Eleitorado / seções | Flávio × Lula 2026 "
        "(Bolsonaro × Lula 1º t. 2022) | O que puxa o escore | Explicação provável |"
    )
    add("|---|---|---|---|---|---|---|---|")
    for item in topo[:25]:
        voto = (
            f"{br(item['flavio_pct'])} × {br(item['lula_pct'])} "
            f"({br(item['bolsonaro_22_1t_pct'])} × {br(item['lula_22_1t_pct'])})"
        )
        add(
            f"| {item['posicao']} | {br(item['escore'])} | {_celula(_local(item))} | "
            f"{item['ibge']} | {inteiro(item['eleitorado'])} / {item['secoes']} | "
            f"{voto} | {_celula('; '.join(item['motivos']))} | "
            f"{_celula(_explicacao_com_contexto(item))} |"
        )
    add("")
    add("## Inferido (leitura do modelo)\n")
    pequenas = r["pequenas_ate_30_secoes"]
    add(
        f"- Tamanho: a zona mediana do topo 50 tem {inteiro(r['eleitorado_mediano']['topo'])} "
        f"eleitores e {r['secoes_medianas']['topo']} seções; a do país, "
        f"{inteiro(r['eleitorado_mediano']['todas'])} e {r['secoes_medianas']['todas']}. "
        f"{pequenas['topo']} das 50 têm até 30 seções, contra "
        f"{br(pequenas['todas_pct'])}% das zonas do país.\n"
        f"- Padrão regional: {r['topo_com_padrao_regional']} das 50 têm ao menos duas "
        "das cinco zonas vizinhas também entre as 5% mais atípicas. Agrupamento "
        "geográfico aponta para efeito político da região, não para urna isolada.\n"
        f"- UF das 50: {', '.join(f'{k} {v}' for k, v in r['topo_por_uf'].items())}.\n"
        + _texto_robustez(pacote.get("robustez", {}))
        + "- Regras de explicação acionadas no topo 50: "
        + "; ".join(f"{k} ({v})" for k, v in r["topo_por_regra"].items())
        + ".\n"
    )
    t = r["tardias"]
    add(
        f"- Zonas tardias: {t['n']} zonas fecharam bem depois da própria UF "
        f"({t['criterio']}). A variação da margem além da UF e do município foi "
        f"{br(t['residuo_medio_pp_tardias'], 2, True)} pp nelas e "
        f"{br(t['residuo_medio_pp_demais'], 2, True)} pp nas demais (média ponderada "
        f"pelos válidos); correlação entre atraso e resíduo "
        f"{br(t['correlacao_atraso_residuo'], 3, True)}. Lula teve "
        f"{br(t['lula_2026_pct_tardias'])}% dos válidos nas tardias, contra "
        f"{br(t['lula_2022_1t_pct_tardias'])}% no 1º turno de 2022 nas mesmas zonas; "
        f"nas demais, {br(t['lula_2026_pct_demais'])}% contra "
        f"{br(t['lula_2022_1t_pct_demais'])}%. A margem de Flávio sobre Lula "
        f"(contra Bolsonaro e Lula em 2022) andou {br(t['margem_swing_pp_tardias'], 2, True)} "
        f"pp nas tardias e {br(t['margem_swing_pp_demais'], 2, True)} pp nas demais; "
        f"a parte da UF é {br(t['swing_uf_pp_tardias'], 2, True)} contra "
        f"{br(t['swing_uf_pp_demais'], 2, True)}, a da vizinhança "
        f"{br(t['efeito_local_pp_tardias'], 2, True)} contra "
        f"{br(t['efeito_local_pp_demais'], 2, True)}. A diferença vem sobretudo da "
        "UF onde as tardias estão; descontadas UF e vizinhança, a demora não veio "
        "acompanhada de voto diferente do esperado.\n"
    )
    add("### As 15 zonas que fecharam por último\n")
    add(
        "| Zona | Conclusão (Brasília) | Minutos após a mediana da UF | Seções | "
        "Flávio × Lula 2026 | Lula 1º t. 2022 | Escore |"
    )
    add("|---|---|---|---|---|---|---|")
    for item in pacote["topo_tardias"]:
        add(
            f"| {_celula(_local(item))} | {item['conclusao_brasilia']} | "
            f"{br(item['atraso_vs_mediana_uf_min'], 0)} | {item['secoes']} | "
            f"{br(item['flavio_pct'])} × {br(item['lula_pct'])} | "
            f"{br(item['lula_22_1t_pct'])} | {br(item['escore'])} |"
        )
    add("")
    add("## Hipótese (a verificar)\n")
    add(
        f"- {r['topo_sem_explicacao_estrutural']} das 50 não acionam nenhuma regra "
        "estrutural (tamanho, área remota, aldeia, redesenho, crescimento do "
        "eleitorado, terceira via, padrão regional). Para elas a hipótese padrão é efeito político local não medido: "
        "prefeito, liderança, igreja, candidatura estadual.\n"
        "- O que resolveria cada caso: boletim de urna por seção (votos por seção "
        "contra a zona), ata da mesa receptora, log da urna e registro de "
        "substituição ou contingência da seção, todos públicos no TSE.\n"
    )
    ctx = pacote["contexto_resumo"]
    add("## Contexto do dia da eleição\n")
    if ctx["presente"]:
        temas = ", ".join(
            f"{TEMA_ROTULO.get(k, k)} {v}" for k, v in ctx["por_tema"].items()
        )
        degraus = ", ".join(f"{k} {v}" for k, v in ctx["por_degrau"].items())
        add(
            f"`analysis/apuracao_2026/dados/contexto_seguranca.json` tem "
            f"{ctx['n_itens']} itens ({ctx['conferidos_na_pagina']} conferidos na "
            f"página). Temas: {temas}. Degrau de evidência: {degraus}.\n"
        )
        nacionais = [
            i
            for i in pacote.get("contexto_nacional", [])
            if i.get("conferido") == "pagina"
        ]
        if nacionais:
            add("Itens sobre totalização e notas oficiais, conferidos na página:\n")
            for i in nacionais:
                add(
                    f"- {i['id']}: {i['titulo']} ({i['veiculo']}, {i['data']}, "
                    f"{i['degrau']}). {i['resumo']} {i['url']}"
                )
            add("")
        casados = [item for item in topo if item["contexto"]]
        if casados:
            add(
                "Zonas do topo 50 com item de contexto no mesmo município. "
                "Coincidência de município não liga o fato à atipicidade da zona.\n"
            )
            for item in casados:
                for c in item["contexto"]:
                    add(
                        f"- {_local(item)}: {c['titulo']} ({c['veiculo']}, "
                        f"{c['data']}, {c['degrau']}) {c['url']}"
                    )
            add("")
        else:
            add("Nenhum item de contexto cita município do topo 50.\n")
    else:
        add("Arquivo de contexto ainda não gerado.\n")
    add("## Limites\n")
    for limite in pacote["limites"]:
        add(f"- {limite}")
    add("")
    add("## Lista para mapa (topo 50)\n")
    add("```csv\nlat;lon;escore;rotulo")
    for p in pacote["mapa"]:
        add(f"{p['lat']};{p['lon']};{p['escore']};{p['rotulo']}")
    add("```\n")
    add("## Parágrafo publicável\n")
    t = r["tardias"]
    explicadas = len(topo) - r["topo_sem_explicacao_estrutural"]
    add(
        f"A casa rodou uma triagem estatística sobre as {inteiro(r['n_zonas'])} zonas "
        "eleitorais do país no voto para presidente, comparando cada uma com a "
        "própria UF e com o resultado de 2022. Das 50 zonas mais atípicas, "
        f"{r['pequenas_ate_30_secoes']['topo']} têm até 30 seções, e "
        f"{explicadas} têm explicação comum provável: tamanho pequeno, eleitorado "
        "que cresceu muito acima da UF desde 2022, voto regional em candidatura de "
        "terceira via, padrão compartilhado com as zonas vizinhas ou área remota. "
        "As outras "
        f"{r['topo_sem_explicacao_estrutural']} ficam como hipótese de política "
        f"local, a conferir seção por seção. As {t['n']} zonas que fecharam por "
        "último, bem depois da própria UF, votaram como as demais em relação à "
        f"região: a variação da margem além do esperado foi de "
        f"{br(t['residuo_medio_pp_tardias'], 2, True)} ponto nelas e de "
        f"{br(t['residuo_medio_pp_demais'], 2, True)} nas outras. Atipicidade não é "
        "irregularidade. A triagem por zona não prova nem descarta problema em "
        "seção específica; isso exige o boletim de urna, a ata da mesa e o log da "
        "urna, que o TSE publica.\n"
    )
    add("## Reprodução\n")
    add("```\npython3 scripts/apuracao-2026-anomalias.py\n```\n")
    return "\n".join(out)
