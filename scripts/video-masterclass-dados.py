#!/usr/bin/env python3
"""Dados do vídeo masterclass (video/masterclass), lidos das fontes da casa.

Grava `video/masterclass/src/dados/masterclass.json`, que o Remotion importa estaticamente e
que o teste `tests/test_video_masterclass.py` confere contra o roteiro. O esquema está em
`video/masterclass/CONTRATO.md`, seção 3. Nada é digitado à mão: cada número sai de um
arquivo do repositório, e `fontes` guarda o SHA-256 de todo arquivo lido.

Regras declaradas:

- Percentuais com duas casas. Diferenças de pesquisa em votos válidos, Lula menos Flávio,
  como em `docs/assets/reponderacao_urna_1t.json`.
- Concha: última onda de cada instituto com perfil de renda no agregador. Faixas em salários
  mínimos que cortam em 2 e 5 SM viram três faixas (até 2, 2 a 5, mais de 5); cartão em reais
  (AtlasIntel) fica com as próprias faixas e rótulos. Destaques: maior desvio positivo e
  maior negativo na primeira faixa entre os institutos agregados.
- Régua: entre as últimas ondas de cada instituto, a mais recente cujo cartão corta em 2, 5 e
  10 SM, com a PNAD lida pelo motor do agregador (pessoas 16+, rendimento efetivo).
- Exemplos e prédios: seção pelo mapa de fiscais (`docs/assets/fiscais_mapa/uf/<UF>.json`),
  completada pelo capítulo 13 (`fiscais.json`) quando a seção está lá. Campo que não existe
  na fonte fica `null`. Em Oiapoque, a seção da Aldeia Kumaruma é a de nível mais alto,
  depois maior pontuação, depois mais votantes (a regra do vídeo dos fiscais).

Uso: python3 scripts/video-masterclass-dados.py
"""

from __future__ import annotations

import csv
import hashlib
import importlib
import json
import re
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SAIDA = ROOT / "video" / "masterclass" / "src" / "dados" / "masterclass.json"
URNA_1T = ROOT / "docs" / "assets" / "reponderacao_urna_1t.json"
URNA_1T_CSV = ROOT / "docs" / "assets" / "reponderacao_urna_1t.csv"
PNAD = ROOT / "docs" / "assets" / "reponderacao_pnad.json"
TSE = ROOT / "data" / "outputs" / "tse_eleitorado_perfil_benchmark.json"
PRESIDENTE = ROOT / "analysis" / "apuracao_2026" / "dados" / "presidente.json"
METODOLOGIAS = ROOT / "docs" / "assets" / "reponderacao_metodologias.json"
ERRO_2022 = ROOT / "analysis" / "predicao_2026" / "erro_2022" / "erro_2022.json"
INDICE = ROOT / "docs" / "assets" / "fiscais_mapa" / "indice.json"
MAPA_UF = ROOT / "docs" / "assets" / "fiscais_mapa" / "uf"
FISCAIS = ROOT / "analysis" / "apuracao_2026" / "dados" / "fiscais.json"
FAMILIAS = SCRIPTS / "apuracao_logs" / "familias.py"
DADOS_FISCAIS = SCRIPTS / "video-fiscais-dados.py"
MALHA = ROOT / "apuracao" / "public" / "geo" / "br_uf.geojson"
GAME = ROOT / "docs" / "politize_game" / "dados.js"
QR = ROOT / "totalizacao" / "tests" / "fixtures" / "exemplos_tse_2026.json"

# Chaves obrigatórias do contrato: UF, zona e seção de cada exemplo nomeado.
EXEMPLOS: dict[str, tuple[str, int, int]] = {
    "puc_sp": ("SP", 1, 257),
    "marau_rs": ("RS", 62, 15),
    "sao_joao_missoes_mg": ("MG", 166, 267),
    "tabatinga_am": ("AM", 36, 30),
    "nova_andradina_ms": ("MS", 5, 168),
    "baiao_pa": ("PA", 35, 238),
    "porto_acre_ac": ("AC", 1, 621),
    "teixeira_freitas_ba": ("BA", 183, 175),
    "serra_es": ("ES", 53, 211),
    "iranduba_am": ("AM", 56, 19),
}
# Exemplo escolhido por regra: seções da Aldeia Kumaruma, em Oiapoque (AP).
OIAPOQUE = ("oiapoque_ap", "AP", "Oiapoque", "KUMARUMA")
PREDIOS = ("RJ-60011-233-1414", "SP-71072-372-2020")

NIVEL_ORDEM = {"alta": 0, "media": 1, "baixa": 2}
FAIXAS_IDADE = (
    ("16-24", "16 a 24"),
    ("25-34", "25 a 34"),
    ("35-44", "35 a 44"),
    ("45-59", "45 a 59"),
    ("60-100", "60 ou mais"),
)
MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
    "setembro", "outubro", "novembro", "dezembro",
)  # fmt: skip
ROTULOS_3SM = ["Até 2 SM", "2 a 5 SM", "Mais de 5 SM"]
ROTULOS_4SM = ["Até 2 SM", "2 a 5 SM", "5 a 10 SM", "Mais de 10 SM"]
CENARIO = "pessoas16_efetivo"


def r2(valor: float | None) -> float | None:
    return None if valor is None else round(float(valor), 2)


class Fontes:
    """Lê arquivos do repositório e guarda o SHA-256 de cada um, pelo caminho relativo."""

    def __init__(self) -> None:
        self.hashes: dict[str, str] = {}

    def marcar(self, caminho: Path) -> bytes:
        dados = caminho.read_bytes()
        self.hashes[str(caminho.relative_to(ROOT))] = hashlib.sha256(dados).hexdigest()
        return dados

    def texto(self, caminho: Path) -> str:
        return self.marcar(caminho).decode("utf-8")

    def json(self, caminho: Path):
        return json.loads(self.texto(caminho))


def modulo(nome: str, arquivo: Path, fontes: Fontes):
    fontes.marcar(arquivo)
    return importlib.import_module(nome)


# --------------------------------------------------------------------------- urna e TSE


def bloco_urna(pres: dict, urna1t: dict) -> dict:
    n = pres["nacional"]
    brasil = pres["regioes"]["Brasil sem exterior"]["r2026"]
    u = urna1t["urna"]
    if (n["validos"], n["secoes"], n["diferenca_votos"]) != (
        u["validos_votos"],
        u["secoes"],
        u["diferenca_flavio_menos_lula_votos"],
    ):
        raise SystemExit("presidente.json e reponderacao_urna_1t.json divergem na urna")
    return {
        "flavio_pct": r2(n["pct"]["flavio"]),
        "lula_pct": r2(n["pct"]["lula"]),
        "diferenca_pp": r2(n["diferenca_pp"]),
        "diferenca_votos": n["diferenca_votos"],
        "flavio_votos": n["votos"]["flavio"],
        "lula_votos": n["votos"]["lula"],
        "validos": n["validos"],
        "brancos": n["brancos"],
        "nulos": n["nulos"],
        "brancos_pct": r2(n["pct_brancos"]),
        "nulos_pct": r2(n["pct_nulos"]),
        "secoes": n["secoes"],
        "eleitores": n["eleitores"],
        "comparecimento": n["comparecimento"],
        "abstencao": n["abstencao"],
        "comparecimento_pct": r2(n["pct_comparecimento"]),
        "comparecimento_brasil_pct": r2(brasil["pct_comparecimento"]),
        "eleitores_brasil": brasil["eleitores"],
        "cury_pct": r2(n["pct"]["cury"]),
        "renan_pct": r2(n["pct"]["renan"]),
        "caiado_pct": r2(n["pct"]["caiado"]),
        "terceiros_pct": r2(n["pct"]["terceiros"]),
        "gerado_em": n["gerado_em"],
    }


def bloco_tse(bench: dict) -> dict:
    meta = bench["metadata"]
    universo = bench["poll_universe_brazil_excluding_exterior"]
    sexo = universo["gender_binary"]
    idade = universo["age_poll_bands"]
    return {
        "fonte": meta["source_name"],
        "data_geracao": meta["dt_geracao"],
        "eleitores_brasil": int(meta["total_eleitores_brasil_sem_exterior"]),
        "eleitores_total": int(meta["total_eleitores_all_ufs_incl_exterior"]),
        "sexo": [
            {"rotulo": "Mulheres", "pct": r2(sexo["Mulher"]["pct"])},
            {"rotulo": "Homens", "pct": r2(sexo["Homem"]["pct"])},
        ],
        "idade": [
            {"faixa": rotulo, "pct": r2(idade[chave]["pct"])}
            for chave, rotulo in FAIXAS_IDADE
        ],
        "regiao": [
            {"rotulo": nome, "pct": r2(v["pct"]), "eleitores": v["count"]}
            for nome, v in sorted(bench["region"].items(), key=lambda kv: -kv[1]["pct"])
        ],
    }


# --------------------------------------------------------------------------- régua e concha


def agregar(valores: list[float], maximos: list, limites: tuple[int, ...]) -> list:
    """Soma as faixas do cartão nas faixas que cortam nos `limites` (em SM)."""
    saida = [0.0] * (len(limites) + 1)
    for valor, maximo in zip(valores, maximos, strict=True):
        j = next(
            (
                k
                for k, lim in enumerate(limites)
                if maximo is not None and maximo <= lim
            ),
            len(limites),
        )
        saida[j] += valor
    return saida


def ultimas_ondas(pnad: dict) -> list[dict]:
    """Última onda de cada instituto com perfil de renda, pelo fim do campo."""
    ult: dict[str, dict] = {}
    for p in pnad["pesquisas"]:
        if not p.get("renda"):
            continue
        chave = (p["campo"]["fim"], p.get("divulgacao") or "", p["id"])
        atual = ult.get(p["instituto"])
        if atual is None or chave > (
            atual["campo"]["fim"],
            atual.get("divulgacao") or "",
            atual["id"],
        ):
            ult[p["instituto"]] = p
    return sorted(ult.values(), key=lambda p: p["instituto"])


def maximos_do_cartao(p: dict, fontes: Fontes) -> tuple[list, dict]:
    bruto = fontes.json(ROOT / p["arquivo"])["renda"]
    maximos = [f.get("max") for f in bruto["faixas"]]
    if len(maximos) != len(p["renda"]["faixas"]):
        raise SystemExit(f"{p['id']}: faixas do cartão e do agregador divergem")
    return maximos, bruto


def bloco_regua(pnad: dict, fontes: Fontes) -> dict:
    candidatas = []
    for p in ultimas_ondas(pnad):
        if p["renda"]["unidade"] != "salarios_minimos":
            continue
        maximos, bruto = maximos_do_cartao(p, fontes)
        if {2, 5, 10} <= set(maximos):
            ano = bruto.get("ano_referencia") or 0
            candidatas.append(((ano, p["campo"]["fim"], p["id"]), p, maximos))
    if not candidatas:
        raise SystemExit("nenhuma onda com cartão cortando em 2, 5 e 10 SM")
    _, p, maximos = max(candidatas, key=lambda c: c[0])
    bench = pnad["benchmark"]
    mes = bench["price_month"]
    renda = p["renda"]

    def faixas(cenario: str) -> list:
        return [r2(v) for v in agregar(renda["pnad_pct"][cenario], maximos, (2, 5, 10))]

    cortes = zip(renda["cortes_brl_202604"], maximos, strict=True)
    return {
        "fonte": (
            f"{bench['benchmark']}, pessoas 16+, preços de "
            f"{MESES[int(mes[4:]) - 1]} de {mes[:4]}"
        ),
        "faixas": ROTULOS_4SM,
        "pnad_pct": faixas(CENARIO),
        "pnad_habitual_pct": faixas("pessoas16_habitual"),
        "pnad_domicilios_pct": faixas("domicilios_efetivo"),
        "cortes_brl_202604": [r2(c) for c, m in cortes if m in (2, 5, 10)],
        "cartao_de": p["id"],
        "milhoes_pessoas16": bench["totais_milhoes"][CENARIO],
    }


def bloco_concha(pnad: dict, fontes: Fontes) -> tuple[list[dict], dict]:
    concha = []
    for p in ultimas_ondas(pnad):
        renda = p["renda"]
        maximos, _ = maximos_do_cartao(p, fontes)
        amostra = renda["amostra_pct"]
        regua = renda["pnad_pct"][CENARIO]
        agregado = renda["unidade"] == "salarios_minimos" and {2, 5} <= set(maximos)
        if agregado:
            amostra = agregar(amostra, maximos, (2, 5))
            regua = agregar(regua, maximos, (2, 5))
            rotulos = ROTULOS_3SM
        else:
            rotulos = list(renda["faixas"])
        concha.append(
            {
                "instituto": p["instituto"],
                "id": p["id"],
                "campo_fim": p["campo"]["fim"],
                "divulgacao": p.get("divulgacao"),
                "metodo": p.get("metodo"),
                "unidade": renda["unidade"],
                "agregado_sm": agregado,
                "perfil_tipo": renda.get("perfil_tipo"),
                "faixas": rotulos,
                "amostra_pct": [r2(v) for v in amostra],
                "pnad_pct": [r2(v) for v in regua],
                "desvio_pp": [r2(a - b) for a, b in zip(amostra, regua, strict=True)],
            }
        )
    concha.sort(key=lambda c: (not c["agregado_sm"], -c["desvio_pp"][0]))
    comparaveis = [c for c in concha if c["agregado_sm"]]

    def destaque(c: dict) -> dict:
        return {
            "instituto": c["instituto"],
            "id": c["id"],
            "campo_fim": c["campo_fim"],
            "faixa": c["faixas"][0],
            "amostra_pct": c["amostra_pct"][0],
            "pnad_pct": c["pnad_pct"][0],
            "desvio_pp": c["desvio_pp"][0],
        }

    mais_pobre = max(comparaveis, key=lambda c: c["desvio_pp"][0])
    mais_rica = min(comparaveis, key=lambda c: c["desvio_pp"][0])
    if mais_pobre["desvio_pp"][0] <= 0 or mais_rica["desvio_pp"][0] >= 0:
        raise SystemExit("concha sem desvio positivo e negativo na primeira faixa")
    return concha, {
        "mais_pobre": destaque(mais_pobre),
        "mais_rica": destaque(mais_rica),
    }


# --------------------------------------------------------------------------- pesquisas e erro


def _par(bloco: dict) -> dict:
    v = bloco["validos"]
    return {
        "lula": r2(v["lula"]),
        "flavio": r2(v["flavio"]),
        "dif": r2(bloco["diferenca_lula_menos_flavio"]["pesquisa"]),
    }


def direcao(erro_pub: float, erro_rep: float | None) -> str | None:
    """Mesma regra de `scripts/apuracao-2026-pesquisas.py`: 0,05 pp de tolerância."""
    if erro_rep is None:
        return None
    delta = abs(erro_rep) - abs(erro_pub)
    return "aproximou" if delta < -0.05 else "afastou" if delta > 0.05 else "neutro"


def bloco_pesquisas(urna1t: dict, linhas_csv: list[dict]) -> list[dict]:
    erro_csv = {
        (row["id"], row["modo"]): float(row["erro_diferenca_lula_flavio_pp"])
        for row in linhas_csv
    }
    saida = []
    for p in urna1t["pesquisas"]:
        pub = p["publicado"]
        rep = p.get("reponderado")
        erro_pub = pub["diferenca_lula_menos_flavio"]["erro"]
        erro_rep = rep["diferenca_lula_menos_flavio"]["erro"] if rep else None
        conferir = [("publicado", erro_pub)] + (
            [("reponderado", erro_rep)] if rep else []
        )
        for modo, erro in conferir:
            if abs(erro_csv[(p["id"], modo)] - erro) > 1e-5:
                raise SystemExit(f"{p['id']} {modo}: JSON e CSV divergem no erro")
        rumo = direcao(erro_pub, erro_rep)
        saida.append(
            {
                "id": p["id"],
                "instituto": p["instituto"],
                "modo": p["modo"],
                "metodo": p["metodo"],
                "campo_fim": p["campo"]["fim"],
                "divulgacao": p.get("divulgacao"),
                "n_entrevistas": p["n"],
                "publicado": _par(pub),
                "publicado_total": {
                    "lula": pub["total"].get("lula"),
                    "flavio": pub["total"].get("flavio"),
                },
                "reponderado": _par(rep) if rep else None,
                "erro_dif_pub_pp": r2(erro_pub),
                "erro_dif_rep_pp": r2(erro_rep),
                "margem_95_pp": r2(p["margem_95_diferenca_aas_pp"]),
                "fora_margem": p["erro_diferenca_fora_da_margem_aas"],
                "aproximou": {"aproximou": True, "afastou": False}.get(rumo or ""),
                "direcao": rumo,
                "efeito_casa_pre_eleicao_pp": r2(p.get("efeito_casa_pre_eleicao_pp")),
                "sem_reponderacao": p.get("reponderado_motivo"),
            }
        )
    saida.sort(key=lambda x: (-x["erro_dif_pub_pp"], x["instituto"]))
    for i, x in enumerate(saida, start=1):
        x["n"] = i
    return [{"n": x.pop("n"), **x} for x in saida]


def bloco_erro(urna1t: dict, erro2022: dict, pesquisas: list[dict]) -> dict:
    res = urna1t["resumo"]
    pub, rep, efeito = res["publicado"], res["reponderado"], urna1t["efeito_pareado"]
    casas22 = erro2022["media_das_casas"]
    rumos = [p["direcao"] for p in pesquisas if p["direcao"]]
    contagem = {k: rumos.count(k) for k in ("aproximou", "afastou", "neutro")}
    if contagem != {k: efeito[k] for k in contagem}:
        raise SystemExit(f"direção por onda {contagem} diverge do efeito pareado")
    erros_pub = [p["erro_dif_pub_pp"] for p in pesquisas]
    if abs(statistics.median(erros_pub) - pub["mediana"]) > 0.01:
        raise SystemExit("mediana do erro publicado diverge do resumo")
    return {
        "n_pub": pub["n"],
        "media_pub_pp": r2(pub["media"]),
        "mediana_pub_pp": r2(pub["mediana"]),
        "media_abs_pub_pp": r2(pub["media_absoluta"]),
        "desvio_padrao_pub_pp": r2(pub["desvio_padrao"]),
        "mais_lula": pub["positivos"],
        "mais_flavio": pub["negativos"],
        "fora_margem": pub["fora_da_margem_aas"],
        "n_rep": rep["n"],
        "media_rep_pp": r2(rep["media"]),
        "mediana_rep_pp": r2(rep["mediana"]),
        "media_abs_rep_pp": r2(rep["media_absoluta"]),
        "mais_lula_rep": rep["positivos"],
        "fora_margem_rep": rep["fora_da_margem_aas"],
        "aproximou": efeito["aproximou"],
        "afastou": efeito["afastou"],
        "neutro": efeito["neutro"],
        "deslocamento_medio_pp": r2(efeito["deslocamento_medio_lula_menos_flavio"]),
        "variacao_media_erro_abs_pp": r2(efeito["variacao_media_erro_absoluto_dif"]),
        "correlacao_casa_erro": r2(res["correlacao_efeito_casa_pre_eleicao_com_erro"]),
        "n_correlacao": res["n_correlacao"],
        "por_modo": {
            modo: {"n": v["n"], "media_pp": r2(v["media"]), "casas": v["casas"]}
            for modo, v in res["por_modo_publicado"].items()
        },
        "erro_comum_2022_pp": r2(casas22["erro_comum_diferenca_lula_menos_bolsonaro"]),
        "mediana_2022_pp": r2(casas22["mediana_dos_erros_diferenca_pp"]),
        "casas_2022": casas22["n_casas"],
        "casas_2022_mais_lula": casas22[
            "casas_que_superestimaram_lula_menos_bolsonaro"
        ],
        "regra": urna1t["regra"],
    }


def bloco_efeito_casa(metod: dict) -> list[dict]:
    saida = []
    for inst in metod["institutos"]:
        sinal = inst.get("sinal")
        if not sinal:
            continue
        desvios = [o["desvio"] for o in sinal["ondas"]]
        if len(desvios) != sinal["n_ondas"]:
            raise SystemExit(f"{inst['instituto']}: n_ondas diverge das ondas listadas")
        saida.append(
            {
                "instituto": inst["instituto"],
                "desvio_mediano": r2(sinal["desvio_mediano"]),
                "minimo": r2(min(desvios)),
                "maximo": r2(max(desvios)),
                "n_ondas": sinal["n_ondas"],
                "direcao": sinal["direcao"],
                "evidencia": sinal.get("evidencia"),
            }
        )
    saida.sort(key=lambda x: -x["desvio_mediano"])
    return saida


# --------------------------------------------------------------------------- logs e capítulo 13


def bloco_logs(indice: dict, familias) -> dict:
    logs = indice["logs"]
    cobertura = logs["cobertura"]
    diagnosticos = []
    for codigo, c in logs["criterios"].items():
        diagnosticos.append(
            {
                "codigo": codigo,
                "nome": familias.NOME_CURTO[codigo],
                "nome_tecnico": c["nome"],
                "secoes": c["secoes"],
                "avaliaveis": c.get("avaliaveis"),
                "familia": familias.FAMILIA_DE.get(codigo),
                "grupo": c.get("grupo"),
                "regra": c["regra"],
                "limite": c["limite"],
                "conferir": c["conferir"],
            }
        )
    bateria = logs["criterios"]["bateria"]["secoes"]
    return {
        "processados": cobertura["processados"],
        "sinalizados": cobertura["sinalizadas"],
        "atencao": dict(indice["resumo"]["atencao"]),
        "niveis_atencao": logs["niveis_atencao"],
        "familias": {
            f: {k: v[k] for k in ("nome", "curto", "explica", "conferir", "criterios")}
            for f, v in logs["familias"].items()
        },
        "sem_ocorrencia": logs["sem_ocorrencia"],
        "diagnosticos": diagnosticos,
        "bateria_pct_urnas": r2(100 * bateria / cobertura["processados"]),
        "rotina": sorted(familias.ROTINA),
    }


def bloco_criterios(fiscais: dict) -> list[dict]:
    return [
        {
            "codigo": c["id"],
            "nome": c["nome"],
            "mede": c["mede"],
            "secoes": c["secoes"],
            "por_nivel": c["secoes_por_nivel"],
            "peso": c["peso"],
            "explicacao_comum": c["explicacao_comum"],
            "o_que_conferir": c["o_que_conferir"],
        }
        for c in fiscais["criterios"]
    ]


def bloco_sinalizadas(fiscais: dict) -> dict:
    resumo = fiscais["resumo"]
    codigos = resumo["explicacao_comum"]["por_codigo"]
    criterio_a = [s for s in fiscais["secoes"] if "a" in s["criterios"]]
    flavio_90 = sum(1 for s in criterio_a if (s["flavio_pct"] or 0) >= 90)
    lula_90 = sum(1 for s in criterio_a if (s["lula_pct"] or 0) >= 90)
    trocadas = sum(
        1 for s in fiscais["secoes"] if "urna_trocada" in s["explicacao_codigos"]
    )
    texto = " ".join(fiscais["achados"]["contrario"])
    achado = re.search(
        r"(\d[\d.]*) das (\d[\d.]*) seções do critério a são de Flávio", texto
    )
    if not achado or (
        int(achado[1].replace(".", "")),
        int(achado[2].replace(".", "")),
    ) != (
        flavio_90,
        len(criterio_a),
    ):
        raise SystemExit("contagem de Flávio com 90% diverge do achado contrário")
    if trocadas != codigos["urna_trocada"]:
        raise SystemExit("urnas trocadas: seções e resumo divergem")
    locais = len(fiscais["por_local"])
    if locais != resumo["fiscais"]["um_por_local"]["todos"]:
        raise SystemExit("locais sinalizados divergem do resumo de fiscais")
    return {
        "universo": resumo["secoes_universo"],
        "secoes": resumo["secoes_sinalizadas"],
        "locais": locais,
        "alta": resumo["por_nivel"]["alta"]["secoes"],
        "media": resumo["por_nivel"]["media"]["secoes"],
        "baixa": resumo["por_nivel"]["baixa"]["secoes"],
        "locais_alta": resumo["por_nivel"]["alta"]["locais"],
        "locais_alta_media": resumo["fiscais"]["um_por_local"]["alta_media"],
        "aptos_sinalizadas": resumo["eleitorado"]["aptos_sinalizadas"],
        "pct_sinalizadas": r2(resumo["eleitorado"]["pct_sinalizadas"]),
        "urnas_trocadas": codigos["urna_trocada"],
        "rural": codigos["zona_rural"],
        "aldeia": codigos["aldeia"],
        "presidio": codigos["presidio"],
        "enclaves_2022": resumo["enclaves_2022"],
        "explicacao_comum_secoes": resumo["explicacao_comum"]["secoes"],
        "criterio_a": len(criterio_a),
        "flavio_90": flavio_90,
        "lula_90": lula_90,
    }


# --------------------------------------------------------------------------- mapa de fiscais


class MapaUF:
    """Recortes por UF do mapa de fiscais, com colunas nomeadas pelo índice."""

    def __init__(self, indice: dict, fontes: Fontes) -> None:
        self.col_locais = indice["colunas_locais"]
        self.col_secoes = indice["colunas_secoes"]
        self.fontes = fontes
        self.cache: dict[str, dict] = {}

    def uf(self, uf: str) -> dict:
        if uf not in self.cache:
            bruto = self.fontes.json(MAPA_UF / f"{uf}.json")
            locais = [
                dict(zip(self.col_locais, x, strict=True)) for x in bruto["locais"]
            ]
            secoes = [
                dict(zip(self.col_secoes, x, strict=True)) for x in bruto["secoes"]
            ]
            for s in secoes:
                s["local"] = locais[s["li"]]
            self.cache[uf] = {"locais": locais, "secoes": secoes}
        return self.cache[uf]

    def secao(self, uf: str, zona: int, secao: int) -> dict:
        achadas = [
            s
            for s in self.uf(uf)["secoes"]
            if s["local"]["zona"] == zona and s["secao"] == secao
        ]
        if len(achadas) != 1:
            raise SystemExit(f"{uf} z{zona} s{secao}: {len(achadas)} seções no mapa")
        return achadas[0]

    def local(self, local_id: str) -> tuple[dict, list[dict]]:
        dados = self.uf(local_id.split("-", 1)[0])
        local = next(x for x in dados["locais"] if x["id"] == local_id)
        secoes = [s for s in dados["secoes"] if s["local"] is local]
        return local, sorted(secoes, key=lambda s: s["secao"])


def _nivel(valor: str | None) -> str | None:
    return valor if valor in NIVEL_ORDEM else None


def _risco(valor: str | None) -> str | None:
    """Contrato: "alto", "medio" ou null; o nível cru do mapa (com "baixo") vai em risco_nivel."""
    return valor if valor in ("alto", "medio") else None


def _hora(carimbo: str | None) -> str | None:
    return carimbo[11:16] if carimbo else None


def exemplo(mapa: dict, cap13: dict | None, familias, nomes_criterios: dict, projetar):
    local = mapa["local"]
    c13 = cap13 or {}
    criterios = c13.get("criterios") or list(mapa["criterios"] or "")
    logs = mapa["logs"] or []
    fams = familias.familias_de(logs)
    tipo_urna = (c13.get("detalhe") or {}).get("f", {}).get("tipo_urna")
    votantes = c13.get("votantes", mapa["comparecimento"])
    return {
        "uf": local["uf"],
        "municipio": local["municipio"],
        "zona": local["zona"],
        "secao": mapa["secao"],
        "local_id": local["id"],
        "local": local["local"],
        "bairro": local["bairro"],
        "endereco": local["endereco"],
        "aptos": mapa["aptos"],
        "votantes": votantes,
        "comparecimento_pct": (
            r2(100 * votantes / mapa["aptos"]) if votantes and mapa["aptos"] else None
        ),
        "lula_pct": r2(mapa["lula_pct"]),
        "flavio_pct": r2(mapa["flavio_pct"]),
        "zona_lula_pct": r2(c13.get("zona_lula_pct")),
        "zona_flavio_pct": r2(c13.get("zona_flavio_pct")),
        "uf_lula_pct": r2(c13.get("uf_lula_pct")),
        "uf_flavio_pct": r2(c13.get("uf_flavio_pct")),
        "lula_2022_pct": r2(c13.get("lula_2022_pct")),
        "flavio_2022_pct": r2(c13.get("flavio_2022_pct")),
        "abertura": _hora(c13.get("abertura_brasilia")),
        "encerramento": _hora(c13.get("encerramento_brasilia")),
        "recebido_tse": c13.get("recebido_tse"),
        "modelo_urna": c13.get("modelo_urna"),
        "tipo_urna": c13.get("tipo_urna"),
        "tipo_urna_texto": tipo_urna,
        "n_cargas": c13.get("n_cargas"),
        "criterios": criterios,
        "criterios_nomes": [nomes_criterios[c] for c in criterios],
        "nivel": _nivel(c13.get("nivel") or mapa["nivel"]),
        "pontuacao": c13.get("pontuacao", mapa["pontuacao"]),
        "explicacao_provavel": c13.get("explicacao_provavel"),
        "explicacao_codigos": c13.get("explicacao_codigos"),
        "logs": logs,
        "logs_nomes": [familias.NOME_CURTO[c] for c in logs],
        "familias": fams,
        "atencao": mapa["atencao"],
        "risco": _risco(local["risco"]),
        "risco_nivel": local["risco"],
        "risco_motivos": local["risco_motivos"] or [],
        "o_que_conferir": c13.get("o_que_conferir"),
        "conferir_logs": [familias.FAMILIAS[f]["conferir"] for f in fams],
        "detalhe": c13.get("detalhe"),
        "tempo_voto": mapa["tempo_voto"],
        "processo_mediana": mapa["processo_mediana"],
        "cadencia_mediana": mapa["cadencia_mediana"],
        "local_secoes_total": local["secoes_total"],
        "local_aptos_total": local["aptos_total"],
        "xy": (
            projetar(local["lon"], local["lat"]) if local["lat"] is not None else None
        ),
    }


def bloco_exemplos(mapa: MapaUF, fiscais: dict, familias, projetar) -> dict:
    cap13 = {(s["uf"], s["zona"], s["secao"]): s for s in fiscais["secoes"]}
    nomes = {c["id"]: c["nome"] for c in fiscais["criterios"]}
    saida = {}
    for chave, (uf, zona, secao) in EXEMPLOS.items():
        m = mapa.secao(uf, zona, secao)
        saida[chave] = exemplo(
            m, cap13.get((uf, zona, secao)), familias, nomes, projetar
        )
    chave, uf, municipio, marca = OIAPOQUE
    candidatas = [
        s
        for s in mapa.uf(uf)["secoes"]
        if s["local"]["municipio"] == municipio
        and marca in f"{s['local']['local']} {s['local']['bairro']}".upper()
    ]
    if not candidatas:
        raise SystemExit(f"{municipio}: nenhuma seção com {marca}")
    candidatas.sort(
        key=lambda s: (
            NIVEL_ORDEM.get(s["nivel"], 3),
            -(s["pontuacao"] or 0),
            -(s["comparecimento"] or 0),
            s["secao"],
        )
    )
    m = candidatas[0]
    c13 = cap13.get((uf, m["local"]["zona"], m["secao"]))
    saida[chave] = exemplo(m, c13, familias, nomes, projetar)
    saida[chave]["secoes_no_local_com_sinal"] = len(candidatas)
    return saida


def bloco_predios(mapa: MapaUF, familias, projetar) -> list[dict]:
    saida = []
    for local_id in PREDIOS:
        local, secoes = mapa.local(local_id)
        por_atencao = {str(k): 0 for k in range(4)}
        sem_log = 0
        for s in secoes:
            if s["atencao"] is None:
                sem_log += 1
            else:
                por_atencao[str(s["atencao"])] += 1
        saida.append(
            {
                "local_id": local_id,
                "uf": local["uf"],
                "municipio": local["municipio"],
                "zona": local["zona"],
                "local": local["local"],
                "endereco": local["endereco"],
                "bairro": local["bairro"],
                "secoes_total": local["secoes_total"],
                "aptos_total": local["aptos_total"],
                "risco": _risco(local["risco"]),
                "risco_nivel": local["risco"],
                "risco_motivos": local["risco_motivos"] or [],
                "secoes_listadas": len(secoes),
                "secoes_sem_sinal": local["secoes_total"] - len(secoes),
                "por_atencao": por_atencao,
                "sem_log": sem_log,
                "xy": projetar(local["lon"], local["lat"]),
                "secoes": [
                    {
                        "secao": s["secao"],
                        "nivel": _nivel(s["nivel"]),
                        "criterios": list(s["criterios"] or ""),
                        "atencao": s["atencao"],
                        "logs": s["logs"] or [],
                        "logs_nomes": [familias.NOME_CURTO[c] for c in s["logs"] or []],
                        "familias": familias.familias_de(s["logs"] or []),
                        "aptos": s["aptos"],
                        "comparecimento": s["comparecimento"],
                        "flavio_pct": r2(s["flavio_pct"]),
                        "lula_pct": r2(s["lula_pct"]),
                    }
                    for s in secoes
                ],
            }
        )
    return saida


# --------------------------------------------------------------------------- mapa, app e QR


def bloco_mapa(malha: dict, fiscais_video) -> dict:
    return {
        "view": fiscais_video.VIEW,
        "ufs": [
            {
                "uf": fiscais_video.CODAREA_UF[f["properties"]["codarea"]],
                "d": fiscais_video.caminho_svg(f["geometry"]),
            }
            for f in malha["features"]
        ],
    }


def bloco_politize(texto: str) -> dict:
    achado = re.search(
        r"window\.POLITIZE_GAME\s*=\s*(\{.*\})\s*;?\s*$", texto, re.DOTALL
    )
    if not achado:
        raise SystemExit("docs/politize_game/dados.js sem window.POLITIZE_GAME")
    jogo = json.loads(achado[1])
    return {
        "personagens": len(jogo["personagens"]),
        "cenas": len(jogo["cenarios"]),
        "eleitores": len(jogo["npcs"]),
        "versao": jogo.get("versao"),
    }


def main() -> None:
    fontes = Fontes()
    urna1t = fontes.json(URNA_1T)
    linhas_csv = list(csv.DictReader(fontes.texto(URNA_1T_CSV).splitlines()))
    pnad = fontes.json(PNAD)
    pres = fontes.json(PRESIDENTE)
    metod = fontes.json(METODOLOGIAS)
    erro2022 = fontes.json(ERRO_2022)
    indice = fontes.json(INDICE)
    fiscais = fontes.json(FISCAIS)
    malha = fontes.json(MALHA)
    familias = modulo("apuracao_logs.familias", FAMILIAS, fontes)
    fiscais_video = modulo("video-fiscais-dados", DADOS_FISCAIS, fontes)
    mapa = MapaUF(indice, fontes)

    concha, destaques = bloco_concha(pnad, fontes)
    pesquisas = bloco_pesquisas(urna1t, linhas_csv)
    saida = {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fontes": {},
        "rotulos": indice["rotulos"],
        "urna": bloco_urna(pres, urna1t),
        "tse": bloco_tse(fontes.json(TSE)),
        "regua": bloco_regua(pnad, fontes),
        "concha": concha,
        "concha_destaques": destaques,
        "pesquisas_1t": pesquisas,
        "erro_resumo": bloco_erro(urna1t, erro2022, pesquisas),
        "efeito_casa": bloco_efeito_casa(metod),
        "efeito_casa_regra": metod["efeito_casa"],
        "logs": bloco_logs(indice, familias),
        "criterios": bloco_criterios(fiscais),
        "sinalizadas": bloco_sinalizadas(fiscais),
        "exemplos": bloco_exemplos(mapa, fiscais, familias, fiscais_video.projetar),
        "predios": bloco_predios(mapa, familias, fiscais_video.projetar),
        "mapa": bloco_mapa(malha, fiscais_video),
        "politize": bloco_politize(fontes.texto(GAME)),
        "totalizacao": {"exemplos_oficiais": len(fontes.json(QR)["exemplos"])},
    }
    saida["fontes"] = dict(sorted(fontes.hashes.items()))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    resumo(saida)


def resumo(s: dict) -> None:
    print(f"{SAIDA.relative_to(ROOT)}: {SAIDA.stat().st_size // 1024} KB, ", end="")
    print(f"{len(s['fontes'])} fontes com SHA-256")
    print(f"  urna: {json.dumps(s['urna'], ensure_ascii=False)}")
    print(f"  erro_resumo: {json.dumps(s['erro_resumo'], ensure_ascii=False)[:600]}")
    print(
        f"  regua: {s['regua']['faixas']} {s['regua']['pnad_pct']} ({s['regua']['cartao_de']})"
    )
    print(
        f"  concha_destaques: {json.dumps(s['concha_destaques'], ensure_ascii=False)}"
    )
    for c in s["concha"]:
        print(
            f"    concha {c['instituto']} {c['campo_fim']} {c['faixas'][0]} desvio {c['desvio_pp']}"
        )
    for p in s["predios"]:
        print(
            f"  prédio {p['local_id']} {p['local']}: {p['secoes_total']} seções, "
            f"{p['aptos_total']} aptos, {p['secoes_listadas']} listadas, "
            f"por atenção {p['por_atencao']}, risco {p['risco']}"
        )
    for chave, e in s["exemplos"].items():
        nulos = sorted(k for k, v in e.items() if v is None)
        print(
            f"  exemplo {chave}: {e['uf']} {e['municipio']} z{e['zona']} s{e['secao']} "
            f"nivel={e['nivel']} atencao={e['atencao']} nulos={nulos}"
        )
    print(f"  sinalizadas: {json.dumps(s['sinalizadas'], ensure_ascii=False)}")
    print(f"  politize: {s['politize']} totalizacao: {s['totalizacao']}")


if __name__ == "__main__":
    main()
