#!/usr/bin/env python3
"""Consolida em `hipoteses.json` os números do capítulo "O que poderia ter acontecido".

Nenhum número é digitado aqui: cada valor sai de um JSON do acervo
(`analysis/apuracao_2t_2026/dados/*.json`, `noticias_noite.json`), dos arquivos
do vídeo em `data/originals/prorrogacao_video/` ou, quando o banco local
existe, de duas contas somente leitura sobre `apuracao/data/secoes_2t_2026.sqlite`
e `secoes_2026.sqlite` (conferência BU × zona e deslocamento por modelo de urna).
Sem o banco, essas duas contas repetem a execução anterior e dizem isso.

O que é editorial (a classificação de cada hipótese e de cada teste) fica em
regras declaradas neste arquivo, aplicadas aos números. Rótulo de tudo:
atipicidade pede explicação, não prova irregularidade.

Uso:
    python3 scripts/apuracao-2t-2026-hipoteses.py [--sem-banco]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MEMOS = ROOT / "analysis/apuracao_2t_2026"
DADOS = MEMOS / "dados"
SAIDA = DADOS / "hipoteses.json"
VIDEO = ROOT / "data/originals/prorrogacao_video"
BANCO_2T = ROOT / "apuracao/data/secoes_2t_2026.sqlite"
BANCO_1T = ROOT / "apuracao/data/secoes_2026.sqlite"
BRT = timezone(timedelta(hours=-3))
ROTULO = "atipicidade pede explicação, não prova irregularidade"

ESTADOS = {
    "descartada": "descartada pelos dados",
    "compativel": "compatível, mas não identificada",
    "pendente": "pendente de documento",
}
RESULTADOS = ("exclui", "não exclui", "pendente", "não se aplica")

ARQUIVOS = [
    "presidente.json",
    "linha_do_tempo.json",
    "secoes.json",
    "secoes_voto.json",
    "logs.json",
    "metadados.json",
    "rdv.json",
    "paralela.json",
    "urnas.json",
    "comparacao_1t.json",
    "transferencia.json",
    "pesquisas_vs_urna.json",
    "projecao_pre_urna.json",
]


# ------------------------------------------------------------------ leitura


def sha(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def ler(nome: str) -> dict:
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


def item(N: dict, hora: str, veiculo: str, palavra: str) -> dict:
    """Item de `noticias_noite.json` pela hora (HH:MM), veículo e uma palavra do resumo."""
    for x in N["itens"]:
        if (
            x["quando"][11:16] == hora
            and x["veiculo"].startswith(veiculo)
            and palavra.lower() in x["resumo"].lower()
        ):
            return x
    raise KeyError(f"noticias_noite.json: {hora} {veiculo} '{palavra}'")


def marco(x: dict, hora: str, rotulo: str, raia: str, **extra) -> dict:
    return {
        "hora": hora,
        "rotulo": rotulo,
        "raia": raia,
        "tipo": x["tipo"],
        "veiculo": x["veiculo"],
        "url": x["url"],
        "resumo": x["resumo"],
        "quando_tipo": x["quando_tipo"],
        "origem": "noticias_noite.json",
        **extra,
    }


def video() -> dict:
    """Primeira publicação do vídeo e republicações, pelos carimbos das páginas arquivadas."""
    fonte = json.loads((VIDEO / "fonte.json").read_text(encoding="utf-8"))
    cap = VIDEO / "capturas"
    meta_ig = next(cap.glob("ig_reel_*_meta.json"))
    ig = json.loads(meta_ig.read_text(encoding="utf-8"))
    pub = datetime.fromisoformat(ig["time_datetime"].replace("Z", "+00:00"))
    repub = []
    for f in sorted(cap.glob("p*.html")):
        txt = f.read_text(encoding="utf-8", errors="replace")
        url = re.search(r'og:url"\s*content="([^"]+)"', txt)
        quando = re.search(r'datePublished"\s*:\s*"([^"]+)"', txt)
        if not (url and quando):
            continue
        q = quando.group(1)
        dt = datetime.fromisoformat(q.replace("Z", "+00:00"))
        sem_fuso = dt.tzinfo is None
        if sem_fuso:  # página sem fuso no carimbo: hora local do veículo, Brasília
            dt = dt.replace(tzinfo=BRT)
        dominio = re.sub(r"^https?://(www\.)?", "", url.group(1)).split("/")[0]
        repub.append(
            {
                "veiculo": dominio,
                "url": url.group(1),
                "hora_brt": dt.astimezone(BRT).strftime("%H:%M"),
                "carimbo": q,
                "fuso_inferido": sem_fuso,
                "arquivo": f"data/originals/prorrogacao_video/capturas/{f.name}",
            }
        )
    repub.sort(key=lambda r: r["hora_brt"])
    metricas = None
    pubs = VIDEO / "publicacoes.json"
    if pubs.exists():
        P = json.loads(pubs.read_text(encoding="utf-8"))
        ig_item = next((x for x in P["itens"] if x.get("url") == ig["url"]), None)
        if ig_item:
            metricas = ig_item.get("metricas_no_momento")
    return {
        "perfil": ig["perfil"],
        "url": ig["url"],
        "publicado_utc": ig["time_datetime"],
        "publicado_brt": pub.astimezone(BRT).strftime("%H:%M"),
        "publicado_brt_segundos": pub.astimezone(BRT).strftime("%H:%M:%S"),
        "metricas_na_captura": metricas,
        "capturado_em": ig["capturado_em"],
        "coautores": ig["coautores"],
        "pede_extensao": "EXTENSÃO DOS HORÁRIOS" in ig["legenda"].upper(),
        "republicacoes": repub,
        "primeira_republicacao": repub[0] if repub else None,
        "copia_recebida": {
            "sha256": fonte["sha256"],
            "creation_time_utc": fonte["metadados_do_arquivo"]["creation_time_utc"],
            "conserva_original": False,
            "leitura": fonte["metadados_do_arquivo"]["leitura"],
        },
    }


def cronologia(N: dict, LT: dict, S: dict, V: dict) -> dict:
    sil = LT["pausas"]["silencio_geral"]
    pr = S["prorrogacao"]["brasil"]
    stf = item(N, "17:03", "O Globo", "16:32:49")
    carimbos = re.findall(r"\d{2}:\d{2}:\d{2}", stf["nota"])
    poder = re.findall(r"\d{2}h\d{2}", stf["nota"])
    suspensao = item(N, "17:07", "Agência Brasil", "1.225")
    m = [
        marco(
            item(N, "12:47", "O Globo", "prender"),
            "12:47",
            "TRE-BA manda prender o secretário de Mobilidade de Salvador",
            "transporte",
        ),
        marco(
            item(N, "16:16", "Agência Brasil", "Procon"),
            "16:16",
            "Procon-BA conta 370 ônibus parados",
            "transporte",
        ),
        marco(
            stf,
            min(carimbos),
            f"Pedido da coligação de Lula chega ao STF ({' ou '.join(carimbos)})",
            "justica",
            carimbos_citados=carimbos,
            poder360_citado=poder,
        ),
        marco(
            item(N, "16:54", "Poder360", "Flávio"),
            "16:54",
            "As duas campanhas pedem prorrogação ao TSE",
            "justica",
        ),
        marco(
            item(N, "17:01", "Estadão", "Procuradoria"),
            "17:01",
            "PGE opina contra a prorrogação, no TSE",
            "justica",
        ),
        marco(
            item(N, "17:03", "STF", "Zanin"),
            "17:03",
            "Zanin prorroga a votação até 19h",
            "justica",
        ),
        marco(
            item(N, "17:09", "Agência Brasil", "544"),
            "17:09",
            "Procon-BA atualiza para 544 ônibus parados",
            "transporte",
        ),
        marco(
            item(N, "17:49", "Poder360", "17h49"),
            "17:49",
            "TSE avisa as seções",
            "tse",
        ),
        marco(
            item(N, "18:08", "Agência Brasil", "reajustou"),
            "18:08",
            "Zanin restringe às seções ainda abertas",
            "justica",
        ),
        marco(
            item(N, "19:00", "Agência Brasil", "80%"),
            "18:17",
            "TRE-SP recebe o aviso com mais de 80% das seções fechadas",
            "tse",
        ),
    ]
    num_ab = re.search(r"([\d.]+) de ([\d.]+) seç", suspensao["resumo"])
    lula = re.search(r"Lula ([\d,]+)%", suspensao["resumo"])
    return {
        "marcos": m,
        "silencio": {
            "inicio": sil["ultimo_gerado_antes_brt"][11:19],
            "fim": sil["primeiro_gerado_depois_brt"][11:19],
            "minutos": sil["minutos"],
            "versoes_geradas_dentro": sil["versoes_geradas_dentro"],
            "leituras_no_intervalo": sil["leituras_no_intervalo"],
            "secoes_antes": int(num_ab.group(1).replace(".", "")),
            "lula_pct_antes": float(lula.group(1).replace(",", ".")),
            "fonte_secoes": suspensao["url"],
        },
        "urnas": {
            "encerramento_p50": pr["encerramento_p50"],
            "encerramento_p90": pr["encerramento_p90"],
            "emissao_p50": pr["emissao_p50"],
            "pct_ate_1715": pr["pct_ate_1715"],
            "pct_bu_emitido_ate_1730": pr["pct_bu_emitido_ate_1730"],
            "pct_apos_1900": pr["pct_apos_1900"],
            "recebimento_p50": pr["recebimento_p50"],
            "pct_recebido_antes_1900": pr["pct_recebido_antes_1900"],
        },
        "video": V,
    }


def precedentes() -> dict | None:
    """Precedentes de prorrogação, lidos de `precedentes_prorrogacao.json` (sem reescrever o conteúdo)."""
    arq = MEMOS / "precedentes_prorrogacao.json"
    if not arq.exists():
        return None
    P = json.loads(arq.read_text(encoding="utf-8"))
    campos = (
        "id",
        "pais",
        "eleicao",
        "data",
        "quem_decidiu",
        "hora_e_alcance",
        "resultado",
    )
    itens = []
    for x in P["itens"]:
        it = {k: x.get(k) for k in campos}
        it["relatorios"] = x.get("relatorios_independentes") or []
        it["oposicao"] = x.get("alegacoes_oposicao") or []
        it["fontes"] = [
            {"url": f["url"], "tipo": f.get("tipo")} for f in x.get("fontes", [])
        ]
        itens.append(it)
    return {
        "titulo": P["titulo"],
        "manifesto_fontes": P["manifesto_fontes"],
        "itens": itens,
        "nao_localizado": P.get("nao_localizado", {}),
        "sha256": sha(arq),
    }


# ------------------------------------------------------------------ contas no banco


def _ro(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def conferencia_zona() -> dict:
    c = _ro(BANCO_2T)
    linhas = c.execute(
        "SELECT ok, COUNT(*), SUM(secoes_bu) FROM conferencia_zona WHERE cargo = 1 GROUP BY ok"
    ).fetchall()
    c.close()
    por = {str(ok): {"zonas": n, "secoes": s} for ok, n, s in linhas}
    return {
        "zonas": sum(v["zonas"] for v in por.values()),
        "zonas_conferem": por.get("1", {}).get("zonas", 0),
        "zonas_divergem": por.get("0", {}).get("zonas", 0),
        "zonas_sem_arquivo": por.get("None", {}).get("zonas", 0),
        "secoes_conferidas": por.get("1", {}).get("secoes", 0),
        "regra": "soma dos BUs de presidente de cada zona contra o arquivo de zona do TSE (tabela conferencia_zona)",
    }


def _votos(caminho: Path) -> dict:
    c = _ro(caminho)
    q = """SELECT b.uf, b.mun, b.zona, b.secao, b.modelo_urna,
             SUM(CASE WHEN v.numero = 22 THEN v.votos ELSE 0 END),
             SUM(CASE WHEN v.numero = 13 THEN v.votos ELSE 0 END)
           FROM bu b JOIN voto_secao v USING (uf, mun, zona, secao)
           WHERE v.cargo = 1 AND v.tipo = 1 AND v.numero IN (13, 22)
           GROUP BY 1, 2, 3, 4"""
    out = {(r[0], r[1], r[2], r[3]): (r[4], r[5], r[6]) for r in c.execute(q)}
    c.close()
    return out


def por_modelo(minimo: int = 20) -> dict:
    """Deslocamento da fatia de Flávio (1º → 2º turno) por modelo da urna do 2º turno.

    Cada seção com ao menos `minimo` votos nos dois finalistas nos dois turnos,
    sem exterior. `dentro_do_municipio` desconta o deslocamento médio do
    município (ponderado), então mede a diferença do modelo contra as vizinhas.
    IC de 95% com erro-padrão agrupado por município.
    """
    a, b = _votos(BANCO_2T), _votos(BANCO_1T)
    linhas = []
    for k, (modelo, f2, l2) in a.items():
        if k[0] == "ZZ" or k not in b:
            continue
        _, f1, l1 = b[k]
        if f2 + l2 < minimo or f1 + l1 < minimo:
            continue
        sw = 100 * f2 / (f2 + l2) - 100 * f1 / (f1 + l1)
        linhas.append((k[0], k[1], modelo or "sem modelo", sw, f2 + l2))
    mun = defaultdict(lambda: [0.0, 0.0])
    for uf, mu, _, sw, w in linhas:
        mun[(uf, mu)][0] += w * sw
        mun[(uf, mu)][1] += w
    grupos: dict = defaultdict(list)
    for uf, mu, modelo, sw, w in linhas:
        base = mun[(uf, mu)][0] / mun[(uf, mu)][1]
        grupos[modelo].append(((uf, mu), sw, sw - base, w))
    out = []
    for modelo in sorted(grupos):
        g = grupos[modelo]
        W = sum(x[3] for x in g)
        media = sum(x[1] * x[3] for x in g) / W
        rel = sum(x[2] * x[3] for x in g) / W
        clus = defaultdict(float)
        for m_, _, r, w in g:
            clus[m_] += w * (r - rel)
        ep = math.sqrt(sum(v * v for v in clus.values())) / W
        out.append(
            {
                "modelo": modelo,
                "secoes": len(g),
                "municipios": len(clus),
                "deslocamento_pp": round(media, 3),
                "dentro_do_municipio_pp": round(rel, 3),
                "ep_pp": round(ep, 3),
                "ic95_pp": [round(rel - 1.96 * ep, 3), round(rel + 1.96 * ep, 3)],
            }
        )
    W = sum(x[4] for x in linhas)
    return {
        "secoes": len(linhas),
        "minimo_votos": minimo,
        "deslocamento_brasil_pp": round(sum(x[3] * x[4] for x in linhas) / W, 3),
        "modelos": out,
        "regra": (
            "fatia de Flávio entre os dois finalistas no 2º turno menos a do 1º, na mesma seção, "
            "ponderada pelos votos dos dois no 2º; modelo da urna do 2º turno; sem exterior"
        ),
    }


def do_banco(anterior: dict | None, usar: bool) -> tuple[dict | None, dict | None, str]:
    if usar and BANCO_2T.exists() and BANCO_1T.exists():
        return conferencia_zona(), por_modelo(), "banco local, somente leitura"
    if anterior and anterior.get("banco"):
        b = anterior["banco"]
        return b.get("zona"), b.get("modelo"), "execução anterior (banco ausente)"
    return None, None, "banco ausente"


# ------------------------------------------------------------------ hipóteses


def tercos_abstencao(C: dict) -> list[dict]:
    """Municípios em três grupos de mesmo eleitorado pela fatia de Flávio no 1º turno."""
    col = C["municipios"]["colunas"]
    R = [dict(zip(col, r, strict=True)) for r in C["municipios"]["linhas"]]
    R = [
        r
        for r in R
        if r["completo"] and r["uf"] != "ZZ" and r["t1_h2h_flavio"] is not None
    ]
    R.sort(key=lambda r: r["t1_h2h_flavio"])
    tot = sum(r["aptos"] for r in R)
    g: list[list] = [[], [], []]
    acc = 0
    for r in R:
        g[min(2, int(3 * acc / tot))].append(r)
        acc += r["aptos"]
    nomes = ["Flávio mais fraco", "meio", "Flávio mais forte"]
    out = []
    for nome, x in zip(nomes, g, strict=True):
        W = sum(r["aptos"] for r in x)
        out.append(
            {
                "grupo": nome,
                "municipios": len(x),
                "eleitores": W,
                "flavio_1t_min": x[0]["t1_h2h_flavio"],
                "flavio_1t_max": x[-1]["t1_h2h_flavio"],
                "abstencao_variacao_pp": round(
                    sum(r["delta_abstencao_pp"] * r["aptos"] for r in x) / W, 2
                ),
                "deslocamento_flavio_pp": round(
                    sum(r["swing_h2h_flavio_pp"] * r["aptos"] for r in x) / W, 2
                ),
            }
        )
    return out


def sinal(V: dict, ident: str) -> dict:
    s = next(x for x in V["sinais"] if x["sinal"] == ident)
    ep = s["ep_did_fatia_flavio_pp"]
    did = s["did_fatia_flavio_pp"]
    return {
        "secoes": s["n_sinal_total"],
        "contra_vizinhas_pp": s["dif_fatia_flavio_vs_vizinhas_pp"],
        "did_pp": did,
        "ep_pp": ep,
        "ic95_pp": [round(did - 1.96 * ep, 2), round(did + 1.96 * ep, 2)],
        "n_did": s["n_did"],
    }


def ic(bloco: dict) -> dict:
    return {"media_pp": bloco["media_pp"], "ic95_pp": bloco["ic95_pp"], "n": bloco["n"]}


def montar(anterior: dict | None = None, usar_banco: bool = True) -> dict:
    D = {n: ler(n) for n in ARQUIVOS}
    N = json.loads((MEMOS / "noticias_noite.json").read_text(encoding="utf-8"))
    P, LT, S, SV = (
        D["presidente.json"],
        D["linha_do_tempo.json"],
        D["secoes.json"],
        D["secoes_voto.json"],
    )
    L, M, R, PA = D["logs.json"], D["metadados.json"], D["rdv.json"], D["paralela.json"]
    U, C, T = D["urnas.json"], D["comparacao_1t.json"], D["transferencia.json"]
    PV, PP = D["pesquisas_vs_urna.json"], D["projecao_pre_urna.json"]
    zona, modelo, origem_banco = do_banco(anterior, usar_banco)
    nac = P["nacional"]
    cad = L["cadencia"]
    m2 = M["turnos"]["2t"]
    cv = m2["coerencia_vsc"]
    rep = m2["repeticao"]
    cl = M["coerencia_logs"]

    h1 = {
        "computados": cad["brasil_2t"]["computados"],
        "pct_17_19": cad["brasil_2t"]["pct_17_19"],
        "computados_17_19": cad["brasil_2t"]["computados_17_19"],
        "computados_depois_19": cad["brasil_2t"]["computados_depois_19"],
        "pct_17_19_1t": cad["amostra_1t"]["brasil_1t"]["pct_17_19"],
        "bus_apos_19h": cad["bu_apos_19h"]["secoes"],
        "bus_apos_19h_ultimo_voto_ate_1715": cad["bu_apos_19h"]["ultimo_voto_ate_1715"],
        "ultimo_voto_depois_19": cad["ultimo_voto"]["depois_19"],
        "tardias": sinal(SV, "tardia"),
        "pct_17_19_por_sinal": {g["grupo"]: g["pct_17_19"] for g in cad["por_sinal"]},
        "apos_19h": sinal(SV, "apos_19h"),
        "margem_votos": nac["margem_lula_votos"],
    }
    h2 = {
        "bus": M["cobertura"]["bu_2t"],
        "vsc_ok": cv["secoes_vsc_ok"],
        "vsc_bu_igual": cv["bu_publicado_igual_ao_vsc"]["sim"],
        "vsc_cadeia": cv["cadeia_ate_a_ac"]["sim"],
        "vsc_assinatura_bu": cv["assinatura_hw_do_bu"]["sim"],
        "vsc_falhas": sum(
            v.get("nao", 0) for v in cv.values() if isinstance(v, dict) and "nao" in v
        ),
        "rdv_ok": R["cobertura"]["total"]["ok"],
        "rdv_confere": R["cobertura"]["total"]["confere"],
        "rdv_divergencias": len(R["divergencias_bu"]),
        "log_lidos": L["cobertura"]["lidos"],
        "log_confere": L["cobertura"]["contagem_confere"],
        "log_nao_confere": L["cobertura"]["lidos"] - L["cobertura"]["contagem_confere"],
        "zona": zona,
        "paralela": PA["conferencia"],
        "sistema_apuracao": cv["origem"]["sa"],
        "sistema_apuracao_ufs": sorted(
            {
                ln["uf"].upper()
                for g in U["turnos"]["2t"]["repetidos"]["grupos"]
                if g["classe"] == "sistema_apuracao"
                for ln in g["linhas"]
            }
        ),
        "sistema_apuracao_secoes": sum(
            len(g["linhas"])
            for g in U["turnos"]["2t"]["repetidos"]["grupos"]
            if g["classe"] == "sistema_apuracao"
        ),
        "sistema_apuracao_rdv_conferidas": R["conferencia_busa"][
            "conferidas_pelo_busa_com_votos"
        ]
        + R["conferencia_busa"]["conferidas_pelo_busa_sem_votos"],
        "soma_ufs_menos_nacional": P.get("conferencia", {}).get(
            "soma_ufs_menos_nacional"
        ),
    }
    rec = S["prorrogacao"]["brasil"]
    h2["recebimento_p50"] = rec["recebimento_p50"]
    h2["pct_recebido_antes_1900"] = rec["pct_recebido_antes_1900"]

    cet = PV["hipoteses"]["contabilidade_entre_turnos"]
    reg = {r["uf"]: r for r in C["regioes"]}
    ba = next(u for u in C["ufs"] if u["uf"] == "BA")
    h3 = {
        "tercos": tercos_abstencao(C),
        "correlacao_uf_abstencao_residuo": cet[
            "correlacao_variacao_abstencao_com_residuo"
        ],
        "teto_comparecimento_pp": cet["limite_comparecimento"][
            "parcela_maxima_explicada_pp"
        ],
        "f_menos_l_sem_aumento": cet["limite_comparecimento"][
            "f_menos_l_sem_o_aumento"
        ],
        "regioes": {
            k: {
                "comparecimento_pp": v["delta_comparecimento_pp"],
                "deslocamento_flavio_pp": v["swing_h2h_flavio_pp"],
            }
            for k, v in reg.items()
            if k in ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
        },
        "bahia": {
            "deslocamento_flavio_pp": ba["swing_h2h_flavio_pp"],
            "comparecimento_pp": ba["delta_comparecimento_pp"],
        },
        "brasil_deslocamento_pp": C["brasil"]["swing_h2h_flavio_pp"],
        "ipf_explica_pp": T["resposta"]["explica_pp"],
        "ipf_explica_ic": T["resposta"]["explica_pp_ic"],
        "ultima_hora_2t": cad["brasil_2t"]["pct_ultima_hora"],
        "ultima_hora_1t": cad["amostra_1t"]["brasil_1t"]["pct_ultima_hora"],
    }
    h4 = {"stf_carimbos": None}
    h5 = {
        "versoes": rep["versao_votacao"]["valores_distintos"],
        "versao": rep["versao_votacao"]["valores"][0]["valor"],
        "versao_secoes": rep["versao_votacao"]["valores"][0]["secoes"],
        "ids_repetidos_sem_explicacao": rep["numero_interno_urna"].get(
            "secoes_sem_explicacao", 0
        ),
        "ids_repetidos_secoes": rep["numero_interno_urna"]["secoes_em_grupos"],
        "id_bu_no_log": cl["id_do_bu_no_log"]["confere"],
        "carga_bu_no_log": cl["carga_do_bu_no_log"]["confere"],
        "carga_depois_da_abertura": cl["carga_registrada_vs_abertura"][
            "carga_depois_da_abertura"
        ],
        "cargas_antes_1t": L["metadados"]["cargas"]["antes_do_1t"],
        "cargas_entre_turnos": L["metadados"]["cargas"]["entre_turnos"],
        "mr_repetida": ic(
            L["metadados"]["serie_mr"]["voto_estruturais_brasil"][
                "dif_em_dif_contra_1t"
            ]
        ),
        "mr_repetida_secoes": L["metadados"]["serie_mr"]["voto_estruturais_brasil"][
            "secoes_com_sinal"
        ],
        "reinicios_secoes": L["reinicios"]["secoes"],
        "reinicios": ic(L["reinicios"]["voto"][0]["dif_em_dif_contra_1t"]),
        "urnas_trocadas": ic(
            U["entre_turnos"]["diferenca_em_diferencas"]["todas_trocadas"][
                "fatia_flavio"
            ]
        ),
        "mr_antes_zeresima": L["regra2"]["so_mr_antes_da_zeresima"],
        "secoes_com_erro": L["regra2"]["secoes_com_erro"],
        "assinatura_software_verificada": False,
    }
    if modelo:
        h5["modelo_amplitude_pp"] = round(
            max(
                x["dentro_do_municipio_pp"]
                for x in modelo["modelos"]
                if x["secoes"] >= 1000
            )
            - min(
                x["dentro_do_municipio_pp"]
                for x in modelo["modelos"]
                if x["secoes"] >= 1000
            ),
            3,
        )
    res = PV["resumo"]
    tp = PV["tendencia_publicada"]
    tr = PP["metodos"]["transportado_25_10"]
    h6 = {
        "casas": res["n_casas"],
        "casas_mesmo_sentido": res["publicado_validos_do_total"]["positivos"],
        "erro_medio_pp": res["publicado_validos_do_total"]["media"],
        "dispersao_pp": res["publicado_validos_do_total"]["desvio_padrao"],
        "dispersao_amostral_pp": res["desvio_esperado_so_amostragem_aas_pp"],
        "ufs": tr["n_ufs"],
        "ufs_flavio_abaixo": sum(1 for u in tr["ufs"] if u["erro_flavio_pp"] > 0),
        "vies_comum_pp": tr["vies_flavio_pp_ponderado"],
        "rmse_sem_vies_pp": tr["rmse_sem_vies_pp"],
        "correlacao_previsto_urna": tr["correlacao_previsto_urna"],
        "voltaram_milhoes": T["resposta"]["voltaram_milhoes"],
        "voltaram_lula_pct": T["resposta"]["voltaram_lula_pct"],
        "voltaram_lula_ic": T["resposta"]["voltaram_lula_ic"],
        "por_100_lula_secoes": T["resposta"]["secoes_por_100_lula"],
        "por_100_lula_municipios": T["resposta"]["liquido_por_100_lula"],
        "terceira_flavio_pct": T["resposta"]["terceira_flavio_pct"],
        "terceira_flavio_faixa": T["resposta"]["terceira_flavio_faixa"],
        "pesquisas_flavio_do_estoque": T["resposta"]["pesquisas_flavio_do_estoque"],
        "tendencia_pp_dia": tp["pos_urna_05_a_24"]["inclinacao_dentro_da_casa_pp_dia"],
        "tendencia_extrapolada_f_menos_l": tp["extrapolacao_ate_a_urna"][
            "f_menos_l_extrapolado"
        ],
        "urna_f_menos_l": res["erro_media_simples"]["urna_f_menos_l"],
        "teto_comparecimento_pp": h3["teto_comparecimento_pp"],
        "presenca_declarada": [
            {
                "instituto": x["instituto"],
                "deslocamento_f_menos_l": x["deslocamento_f_menos_l"],
            }
            for x in PV["hipoteses"]["presenca_declarada"]
        ],
        "presenca_relativa_necessaria_pct": PV["hipoteses"][
            "presenca_relativa_necessaria"
        ]["media_arvor_sem_o_extra"],
        "autor_cenario_pct": PV["hipoteses"]["presenca_relativa_necessaria"][
            "autor_cenario_pct"
        ],
    }
    crono = cronologia(N, LT, S, video())
    h4["stf_carimbos"] = crono["marcos"][2]["carimbos_citados"]
    h4["video_antes_da_peticao_min"] = _minutos(
        crono["video"]["publicado_brt_segundos"], min(h4["stf_carimbos"])
    )
    h4["aviso_depois_da_decisao_min"] = _minutos("17:03", "17:49")
    h4["video_antes_da_decisao_min"] = _minutos(
        crono["video"]["publicado_brt_segundos"], "17:03"
    )
    h4["video_antes_da_peticao_faixa_min"] = sorted(
        _minutos(crono["video"]["publicado_brt_segundos"], c)
        for c in h4["stf_carimbos"]
    )
    h4["silencio_min"] = crono["silencio"]["minutos"]

    hip = classificar(h1, h2, h3, h4, h5, h6, modelo)
    testes = discriminador(h1, h2, h3, h5, modelo)
    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gerado_por": "scripts/apuracao-2t-2026-hipoteses.py",
        "rotulo": ROTULO,
        "fontes": {
            **{n: sha(DADOS / n) for n in ARQUIVOS},
            "noticias_noite.json": sha(MEMOS / "noticias_noite.json"),
            "prorrogacao_video/fonte.json": sha(VIDEO / "fonte.json"),
        },
        "banco": {"origem": origem_banco, "zona": zona, "modelo": modelo},
        "cronologia": crono,
        "h1": h1,
        "h2": h2,
        "h3": h3,
        "h4": h4,
        "h5": h5,
        "h6": h6,
        "precedentes": precedentes(),
        "hipoteses": hip,
        "discriminador": testes,
        "estados": ESTADOS,
        "resultados": list(RESULTADOS),
    }


def _minutos(a: str, b: str) -> int:
    """Minutos inteiros (truncados) de `a` até `b`, em HH:MM ou HH:MM:SS."""

    def seg(x: str) -> int:
        p = [int(v) for v in x.split(":")] + [0]
        return p[0] * 3600 + p[1] * 60 + p[2]

    return (seg(b) - seg(a)) // 60


def _ic_contem_zero(b: dict) -> bool:
    lo, hi = b["ic95_pp"]
    return lo <= 0 <= hi


def classificar(h1, h2, h3, h4, h5, h6, modelo) -> list[dict]:
    """Estado de cada hipótese por regra declarada sobre os números."""
    h1_desc = h1["computados_17_19"] < 0.01 * h1["margem_votos"] and _ic_contem_zero(
        h1["apos_19h"]
    )
    somas = h2["vsc_bu_igual"] == h2["bus"] and h2["rdv_confere"] == h2["rdv_ok"]
    zona_ok = bool(h2["zona"]) and h2["zona"]["zonas_divergem"] == 0
    h3_desc = (
        h3["teto_comparecimento_pp"] < h6["erro_medio_pp"]
        and abs(h3["correlacao_uf_abstencao_residuo"]) < 0.2
    )
    return [
        {
            "id": "h1",
            "curto": "Votos tardios",
            "alcance": "como explicação do deslocamento: o que entrou depois das 17h é uma fração mínima da margem",
            "titulo": "Votos tardios com a urna aberta depois das 17h",
            "estado": "descartada" if h1_desc else "compativel",
            "regra": "votos entre 17h e 19h abaixo de 1% da margem e seções encerradas depois das 19h sem deslocamento (IC com zero)",
        },
        {
            "id": "h2",
            "curto": "Totalização no silêncio",
            "alcance": "como lugar do deslocamento: a soma fecha e cada BU é o que a urna assinou",
            "titulo": "Intervenção na totalização durante o silêncio de 114 minutos",
            "estado": "descartada" if (somas and zona_ok) else "pendente",
            "regra": "BU assinado pela urna igual ao publicado em todas as seções, RDV igual ao BU e soma por zona fechada",
        },
        {
            "id": "h3",
            "curto": "Transporte e comparecimento",
            "alcance": "como explicação do deslocamento inteiro; uma parte pequena (estimada em décimos de ponto) continua compatível",
            "titulo": "Transporte e comparecimento diferencial",
            "estado": "descartada" if h3_desc else "compativel",
            "regra": "teto do comparecimento menor que o erro médio das pesquisas e correlação por UF próxima de zero; vale para o deslocamento inteiro, não para uma parte pequena",
        },
        {
            "id": "h4",
            "curto": "Narrativa",
            "alcance": "o propósito não se lê nos arquivos de urna",
            "titulo": "Prorrogação e silêncio como construção de narrativa",
            "estado": "pendente",
            "regra": "a cronologia prova coordenação jurídica e de comunicação; o propósito só se lê em documento (íntegra da Reclamação, original do vídeo, justificativa do TSE)",
        },
        {
            "id": "h5",
            "curto": "Software e metadados",
            "alcance": "descartada nos sinais com marca; a alteração uniforme sem marca depende da assinatura de software",
            "titulo": "Software e metadados da urna",
            "estado": "pendente",
            "regra": "sinais com marca (IDs, cargas, certificados, reinícios, MR) sem efeito; alteração uniforme sem marca só se exclui com a assinatura de software e os resumos do sistema conferidos contra o TSE",
            "modelo_testado": bool(modelo),
        },
        {
            "id": "h6",
            "curto": "Mudança real (tese do autor)",
            "alcance": "tese do autor; nenhum dado público a confirma ou exclui",
            "titulo": "Mudança real de opinião e de comparecimento entre sábado e domingo",
            "estado": "compativel",
            "regra": "nenhum teste exclui e nenhum identifica: não há medição entre o último campo e a urna",
        },
    ]


def discriminador(h1, h2, h3, h5, modelo) -> list[dict]:
    """Testes que separam deslocamento real de deslocamento aplicado, e a matriz hipótese × teste."""
    zona_ok = bool(h2["zona"]) and h2["zona"]["zonas_divergem"] == 0
    mod_ok = bool(modelo) and h5.get("modelo_amplitude_pp", 99) < 0.5
    tercos = h3["tercos"]
    abst = [t["abstencao_variacao_pp"] for t in tercos]
    return [
        {
            "id": "somas",
            "teste": "Somas assinadas",
            "pergunta": "Os BUs assinados pela urna somam o que o TSE publicou?",
            "resultado": "exclui" if zona_ok else "pendente",
            "o_que": "a totalização como lugar do deslocamento",
            "celulas": {
                "h1": "não exclui",
                "h2": "exclui" if zona_ok else "pendente",
                "h3": "não se aplica",
                "h4": "não se aplica",
                "h5": "não exclui",
                "h6": "não exclui",
            },
        },
        {
            "id": "modelo",
            "teste": "Heterogeneidade por modelo de urna",
            "pergunta": "O deslocamento é o mesmo nos quatro modelos, dentro do mesmo município?",
            "resultado": (
                ("exclui" if mod_ok else "não exclui") if modelo else "pendente"
            ),
            "o_que": "alteração restrita a um modelo; não exclui alteração igual em todos",
            "celulas": {
                "h1": "não se aplica",
                "h2": "não se aplica",
                "h3": "não se aplica",
                "h4": "não se aplica",
                "h5": "não exclui",
                "h6": "não exclui",
            },
        },
        {
            "id": "versao",
            "teste": "Heterogeneidade por versão do software",
            "pergunta": "Há mais de uma versão de software para comparar?",
            "resultado": "não exclui" if h5["versoes"] == 1 else "pendente",
            "o_que": "nada: com uma versão só, o teste não tem contraste",
            "celulas": {
                "h1": "não se aplica",
                "h2": "não se aplica",
                "h3": "não se aplica",
                "h4": "não se aplica",
                "h5": "não exclui",
                "h6": "não exclui",
            },
        },
        {
            "id": "cadencia",
            "teste": "Cadência por hora",
            "pergunta": "O 2º turno tem rajada de votos depois das 17h ou uma última hora inchada?",
            "resultado": "exclui" if h1["pct_17_19"] < 0.1 else "não exclui",
            "o_que": "inserção de votos depois das 17h e mobilização concentrada no fim do dia",
            "celulas": {
                "h1": "exclui",
                "h2": "não se aplica",
                "h3": "exclui",
                "h4": "não se aplica",
                "h5": "não exclui",
                "h6": "não exclui",
            },
        },
        {
            "id": "tardias",
            "teste": "Seções tardias contra vizinhas e contra o 1º turno",
            "pergunta": "As seções que encerraram depois das 19h mudaram de voto mais que as vizinhas?",
            "resultado": "exclui" if _ic_contem_zero(h1["apos_19h"]) else "não exclui",
            "o_que": "deslocamento produzido nas seções que ficaram abertas",
            "celulas": {
                "h1": "exclui",
                "h2": "não se aplica",
                "h3": "não exclui",
                "h4": "não se aplica",
                "h5": "não se aplica",
                "h6": "não exclui",
            },
        },
        {
            "id": "abstencao",
            "teste": "Abstenção × força de Flávio",
            "pergunta": "A abstenção caiu mais onde Lula é forte?",
            "resultado": "exclui" if max(abst) - min(abst) < 0.5 else "não exclui",
            "o_que": "comparecimento extra concentrado onde Lula é forte como motor do resultado",
            "celulas": {
                "h1": "não se aplica",
                "h2": "não se aplica",
                "h3": "exclui",
                "h4": "não se aplica",
                "h5": "não se aplica",
                "h6": "não exclui",
            },
        },
        {
            "id": "metadados",
            "teste": "Metadados e eventos da urna",
            "pergunta": "Seções com ID, carga, MR repetida, reinício ou urna trocada votaram diferente?",
            "resultado": (
                "exclui"
                if all(
                    _ic_contem_zero(h5[k])
                    for k in ("mr_repetida", "reinicios", "urnas_trocadas")
                )
                else "não exclui"
            ),
            "o_que": "intervenção por urna que deixe marca no log ou no BU",
            "celulas": {
                "h1": "não se aplica",
                "h2": "não se aplica",
                "h3": "não se aplica",
                "h4": "não se aplica",
                "h5": "exclui",
                "h6": "não exclui",
            },
        },
        {
            "id": "documentos",
            "teste": "Documentos que não temos",
            "pergunta": "Ata das seções, íntegra da Reclamação, original do vídeo, justificativa do TSE, assinatura de software",
            "resultado": "pendente",
            "o_que": "o propósito da prorrogação e do silêncio, e a alteração uniforme sem marca",
            "celulas": {
                "h1": "pendente",
                "h2": "não se aplica",
                "h3": "pendente",
                "h4": "pendente",
                "h5": "pendente",
                "h6": "não se aplica",
            },
        },
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sem-banco", action="store_true", help="não ler os bancos locais")
    a = ap.parse_args()
    anterior = json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else None
    out = montar(anterior, usar_banco=not a.sem_banco)
    SAIDA.write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(f"{SAIDA.relative_to(ROOT)}: banco = {out['banco']['origem']}")
    for h in out["hipoteses"]:
        print(f"  {h['id']}: {ESTADOS[h['estado']]}")
    for t in out["discriminador"]:
        print(f"  teste {t['id']}: {t['resultado']}")


if __name__ == "__main__":
    main()
