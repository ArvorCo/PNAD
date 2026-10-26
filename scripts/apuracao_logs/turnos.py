"""Comparação seção a seção dos diagnósticos dos logs entre o 1º e o 2º turno.

Lê os recortes por zona publicados por ``publicacao.montar`` de cada turno (coluna
``sinais``), refaz famílias e nível de atenção (``familias.atencao``) e cruza as
seções presentes nos dois. Lê também, das métricas do 2º turno, a identidade da
urna no log contra o BU e os cômputos por hora (cadência), que são sinais novos.

Rótulo: atipicidade pede explicação, não prova irregularidade. Persistência de um
diagnóstico nos dois turnos aponta mais para o equipamento, o local ou a rotina da
mesa do que para o dia; a regra não separa essas causas.
"""

from __future__ import annotations

import gzip
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from .criterios import CRITERIOS
from .familias import FAMILIAS, atencao, familias_de
from .parser import VERSAO

ROTULO = "pede explicação, não prova irregularidade"


def ler_sinais(publico: Path) -> dict[tuple, list[str]]:
    out = {}
    for arq in sorted((publico / "zona").glob("*/*.json.gz")):
        d = json.loads(gzip.decompress(arq.read_bytes()))
        col = {c: i for i, c in enumerate(d["colunas"])}
        for linha in d["linhas"]:
            chave = (d["uf"], int(d["zona"]), int(linha[col["secao"]]))
            out[chave] = list(linha[col["sinais"]] or [])
    return out


def comparar(s1: dict, s2: dict) -> dict:
    comuns = sorted(s1.keys() & s2.keys())
    matriz = Counter()
    por_criterio = defaultdict(Counter)
    por_familia = defaultdict(Counter)
    for k in comuns:
        a, b = set(s1[k]), set(s2[k])
        matriz[(atencao(a), atencao(b))] += 1
        for c in a | b:
            por_criterio[c][
                "ambos" if c in a and c in b else "so_1t" if c in a else "so_2t"
            ] += 1
        fa, fb = set(familias_de(a)), set(familias_de(b))
        for f in fa | fb:
            por_familia[f][
                "ambos" if f in fa and f in fb else "so_1t" if f in fa else "so_2t"
            ] += 1
    n = len(comuns)

    def taxa(cond_1t: int, alvo: int) -> dict:
        base = sum(v for (x, _), v in matriz.items() if x >= cond_1t)
        ambos = sum(v for (x, y), v in matriz.items() if x >= cond_1t and y >= alvo)
        geral = sum(v for (_, y), v in matriz.items() if y >= alvo)
        return {
            "secoes_1t": base,
            "pct_2t_dado_1t": round(100 * ambos / base, 3) if base else None,
            "pct_2t_geral": round(100 * geral / n, 3) if n else None,
        }

    return {
        "secoes_1t": len(s1),
        "secoes_2t": len(s2),
        "secoes_nos_dois": n,
        "atencao_1t_x_2t": {f"{a}x{b}": v for (a, b), v in sorted(matriz.items())},
        "persistencia": {
            "atencao_2_ou_mais": taxa(2, 2),
            "atencao_3": taxa(3, 3),
        },
        "por_criterio": {
            c: {"nome": CRITERIOS.get(c, {}).get("nome", c), **dict(v)}
            for c, v in sorted(por_criterio.items())
        },
        "por_familia": {
            f: {"nome": FAMILIAS[f]["nome"], **dict(v)} for f, v in por_familia.items()
        },
    }


def sinais_novos(metricas: Path) -> dict:
    """Identidade da urna no log contra o BU e cadência horária, das métricas."""
    con = sqlite3.connect(f"file:{metricas}?mode=ro", uri=True)
    ident = Counter()
    versoes = Counter()
    por_valor = {
        k: defaultdict(set)
        for k in (
            "serie_mr",
            "serie_mr_dia",
            "serie_chave_publica",
            "codigo_carga",
            "midia_carga",
        )
    }
    reinicios = []
    primeiro_voto = Counter()
    so_mr = 0
    com_erro = 0
    carga = Counter()
    horas = Counter()
    ultima = []
    exemplos = []
    for uf, mun, z, s, txt in con.execute(
        "SELECT uf,mun,zona,secao,resumo FROM metricas WHERE status='ok' AND versao=?",
        (VERSAO,),
    ):
        r = json.loads(txt)
        c = r.get("contagens", {})
        chave = (uf, mun, z, s)
        bu_urna = r.get("bu", {})
        for urna, m in (r.get("metadados_urna") or {}).items():
            for v in m.get("versao_aplicacao", []):
                versoes[v] += 1
            for campo in ("serie_mr", "serie_mr_dia", "serie_chave_publica"):
                for v in m.get(campo, []):
                    por_valor[campo][v].add((chave, urna))
        for urna, cods in (r.get("cargas_log") or {}).items():
            for v in cods:
                por_valor["codigo_carga"][v].add((chave, urna))
        for urna, ids in (r.get("midias_log") or {}).items():
            for v in ids:
                por_valor["midia_carga"][v].add((chave, urna))
        for p in r.get("partidas_dia") or []:
            if p["fase"] == "votacao":
                reinicios.append(
                    {
                        "uf": uf,
                        "mun": mun,
                        "zona": z,
                        "secao": s,
                        "tipo_urna_bu": bu_urna.get("tipo_urna"),
                        **p,
                    }
                )
        if r.get("primeiro_computo_s") is not None:
            primeiro_voto[r["primeiro_computo_s"] // 3600] += 1
        if c.get("erros", 0):
            com_erro += 1
            so_mr += c.get("erros", 0) == c.get("erro_mr_pre_zeresima", 0)
        il = r.get("identidade_log") or {}
        ident[str(il.get("urna_bu_no_log"))] += 1
        carga[str(il.get("carga_bu_no_log"))] += 1
        if il.get("urna_bu_no_log") is False and len(exemplos) < 50:
            exemplos.append(
                {
                    "uf": uf,
                    "mun": mun,
                    "zona": z,
                    "secao": s,
                    "urnas_log": r.get("urnas_log"),
                    "tipo_arquivo": r["bu"].get("tipo_arquivo"),
                }
            )
        ph = {int(h): n for h, n in (r.get("computados_por_hora") or {}).items()}
        if not ph or not r.get("computados_por_hora_confiavel"):
            continue
        horas.update(ph)
        total = sum(ph.values())
        if total >= 100:
            ultima.append(
                {
                    "uf": uf,
                    "mun": mun,
                    "zona": z,
                    "secao": s,
                    "computados": total,
                    "hora_final": max(ph),
                    "pct_ultima_hora": round(100 * ph[max(ph)] / total, 2),
                    "pct_hora_mais_cheia": round(100 * max(ph.values()) / total, 2),
                }
            )
    con.close()
    ultima.sort(key=lambda x: -x["pct_ultima_hora"])
    total = sum(horas.values())
    return {
        "erro_tecnico": {
            "secoes_com_erro": com_erro,
            "so_desmontar_mr_antes_da_zeresima": so_mr,
            "nota": "GAP 'Problema ao desmontar a MR' antes da zerésima: urna religada no 2º turno com a carga de setembro. Desde a regra 2 (26/10/2026) esse erro sai do critério de erro técnico e fica em contagem própria (erro_mr_pre_zeresima).",
        },
        "versao_aplicacao": dict(versoes),
        "repeticao_entre_secoes": {
            campo: {
                "valores": len(v),
                "valores_em_mais_de_uma_secao": sum(
                    len({k for k, _ in x}) > 1 for x in v.values()
                ),
                "maior_numero_de_secoes": max(
                    (len({k for k, _ in x}) for x in v.values()), default=0
                ),
                "exemplos": [
                    {
                        "valor": val,
                        "secoes": sorted({"-".join(map(str, k)) for k, _ in x})[:10],
                    }
                    for val, x in sorted(v.items(), key=lambda i: -len(i[1]))[:10]
                    if len({k for k, _ in x}) > 1
                ],
            }
            for campo, v in por_valor.items()
        },
        "nota_repeticao": "Mídia de carga é gerada uma vez e carrega várias urnas: repetição esperada. A chave pública é a da eleição, igual em todas as urnas. serie_mr reúne a memória de resultado de todo o log (1º e 2º turnos; a MR é reaproveitada entre turnos); serie_mr_dia só a do dia do pleito. Série da memória de resultado, chave pública e código de carga deveriam ser próprios de uma urna e de uma seção; repetição pede explicação, não prova irregularidade.",
        "reinicios_durante_votacao": {
            "partidas": len(reinicios),
            "secoes": len(
                {(r["uf"], r["mun"], r["zona"], r["secao"]) for r in reinicios}
            ),
            "lista": reinicios[:500],
        },
        "primeiro_voto_por_hora_relogio_da_urna": {
            str(h): n for h, n in sorted(primeiro_voto.items())
        },
        "urna_do_bu_no_log": dict(ident),
        "carga_do_bu_no_log": dict(carga),
        "exemplos_urna_ausente": exemplos,
        "computados_por_hora_relogio_da_urna": {
            str(h): {"computados": n, "pct": round(100 * n / total, 3)}
            for h, n in sorted(horas.items())
        },
        "secoes_com_cadencia": len(ultima),
        "maiores_parcelas_na_ultima_hora": ultima[:50],
        "nota": "Hora do relógio da urna (local). A última hora de votação concentra fila e fechamento; parcela alta pede explicação, não prova irregularidade.",
    }


def markdown(d: dict) -> str:
    c = d["comparacao"]
    linhas = [
        "# Logs das urnas: 1º × 2º turno, seção a seção",
        "",
        f"Rótulo: {ROTULO}.",
        "",
        f"- Seções com log analisado: 1º turno {c['secoes_1t']}, 2º turno {c['secoes_2t']}, nos dois {c['secoes_nos_dois']}.",
        f"- Atenção 2 ou mais no 2º turno entre as que tinham 2 ou mais no 1º: {c['persistencia']['atencao_2_ou_mais']}.",
        f"- Atenção 3 nos dois: {c['persistencia']['atencao_3']}.",
        "",
        "## Matriz de atenção (1º turno x 2º turno)",
        "",
        "| 1T \\ 2T | 0 | 1 | 2 | 3 |",
        "|---|---|---|---|---|",
    ]
    for a in range(4):
        linhas.append(
            f"| {a} | "
            + " | ".join(str(c["atencao_1t_x_2t"].get(f"{a}x{b}", 0)) for b in range(4))
            + " |"
        )
    linhas += [
        "",
        "## Diagnósticos",
        "",
        "| Diagnóstico | nos dois | só 1T | só 2T |",
        "|---|---|---|---|",
    ]
    for v in c["por_criterio"].values():
        linhas.append(
            f"| {v['nome']} | {v.get('ambos', 0)} | {v.get('so_1t', 0)} | {v.get('so_2t', 0)} |"
        )
    n = d.get("sinais_novos")
    if n:
        linhas += [
            "",
            "## Sinais novos do 2º turno",
            "",
            f"- Erro técnico: {n['erro_tecnico']['secoes_com_erro']} seções com ERRO/FATAL no dia; em {n['erro_tecnico']['so_desmontar_mr_antes_da_zeresima']} o único erro é o do GAP ao desmontar a memória de resultado, antes da zerésima. {n['erro_tecnico']['nota']}",
            f"- Urna do BU entre as que escreveram o log: {n['urna_do_bu_no_log']}.",
            f"- Código de carga do BU registrado no log da mesma urna: {n['carga_do_bu_no_log']} (None: o log não traz a cerimônia de carga da urna do BU).",
            f"- Seções com cadência horária confiável e 100 cômputos ou mais: {n['secoes_com_cadencia']}.",
        ]
    linhas += ["", f"{ROTULO}.", ""]
    return "\n".join(linhas)


def gerar(publico_1t: Path, publico_2t: Path, metricas_2t: Path, saida: Path) -> dict:
    d = {
        "rotulo": ROTULO,
        "comparacao": comparar(ler_sinais(publico_1t), ler_sinais(publico_2t)),
        "sinais_novos": sinais_novos(metricas_2t) if metricas_2t.exists() else None,
    }
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "comparacao_turnos.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (saida / "comparacao_turnos.md").write_text(markdown(d), encoding="utf-8")
    return d
