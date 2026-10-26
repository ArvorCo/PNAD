"""Mapa do Brasil do Politize-se: leitura dos prédios e das camadas (somente leitura).

Lê ``docs/assets/politize_se/dados/indice.json`` e cada ``mun/<UF>/<mun>.json`` (um
prédio por linha, gerados por ``scripts/politize-se-build.py``) e devolve, por UF, a
tabela compacta de prédios que o aplicativo ``docs/politizese_mapa.html`` desenha, os
totais de cada município (para comparar o prédio com a cidade), o centro de cada zona e
o índice de CEP dos locais de votação. Nada é recalculado a partir do voto: as taxas vêm
prontas do build do Politize-se; aqui só se valida a coordenada e se aplica a regra das
seções pequenas (menos de 30 eleitores não mostram voto nem comparecimento).
"""

from __future__ import annotations

import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from apuracao_logs.mapa import tabela

ROOT = Path(__file__).resolve().parents[2]
ORIGEM = ROOT / "docs/assets/politize_se/dados"
OBSERVADO = ROOT / "docs/assets/fiscais_mapa/clima/observado_2t.json"
CHUVA_FORTE_MM = 20
FORMATO = 3
MIN_APTOS_VOTO = 30
MISTO = "misto"
# Modelos de urna eletrônica (o número é o ano do projeto); nome legível na legenda.
MODELOS_URNA = {
    "UE2009": "modelo de 2009",
    "UE2010": "modelo de 2010",
    "UE2011": "modelo de 2011",
    "UE2013": "modelo de 2013",
    "UE2015": "modelo de 2015",
    "UE2020": "modelo de 2020",
    "UE2022": "modelo de 2022",
}
# caixa do território (Brasil, com ilhas oceânicas) para recusar coordenada trocada
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -34.0, 5.5, -74.5, -28.5

COLUNAS_LOCAIS = [
    "id",
    "nome",
    "endereco",
    "bairro",
    "cep",
    "lat",
    "lon",
    "aprox",
    "n_secoes",
    "n_bu2",
    "secao_link",
    "secoes",
    "aptos1",
    "aptos2",
    "comp_pct1",
    "comp_pct2",
    "d_comp_pp",
    "abst_pct2",
    "bn_pct2",
    "fatia_f1_par",
    "fatia_f2",
    "d_fatia_pp",
    "escore_max",
    "secoes_sinal",
    "secoes_mudaram",
    "urnas_trocadas",
    "secoes_anomalas",
    "modelo",
    "modelos",
    "log1_max",
    "log2_max",
    "log_subiu",
    "chuva2_mm",
    "chuva2_vot_mm",
    "chuva2_fonte",
    "chuva2_fonte_vot",
    "chuva2_dist_km",
    "chuva2_n",
]
I_LAT = COLUNAS_LOCAIS.index("lat")
COLUNAS_MUNICIPIOS = [
    "mun",
    "nome",
    "n_secoes",
    "n_bu2",
    "comp_pct2",
    "d_comp_pp",
    "abst_pct2",
    "bn_pct2",
    "fatia_f1_par",
    "fatia_f2",
    "d_fatia_pp",
    "secoes_sinal",
    "urnas_trocadas",
    "secoes_mudaram",
    "secoes_anomalas",
]
# Campos que dependem do voto: somem em prédio ou município com menos de 30 eleitores.
CAMPOS_VOTO = (
    "comp_pct1",
    "comp_pct2",
    "d_comp_pp",
    "abst_pct2",
    "bn_pct2",
    "fatia_f1_par",
    "fatia_f2",
    "d_fatia_pp",
)

# Camadas de cor. Texto em português corrente: é o que aparece na interface.
CAMADAS: dict[str, dict[str, Any]] = {
    "resultado": {
        "nome": "Resultado do 2º turno",
        "campo": "fatia_f2",
        "tipo": "divergente",
        "centro": 50,
        "limite": 30,
        "baixo": "Lula na frente",
        "alto": "Flávio na frente",
        "explica": (
            "Parcela de Flávio entre os votos dados aos dois no prédio. Azul: Flávio na "
            "frente; vermelho: Lula na frente; quanto mais forte a cor, maior a vantagem."
        ),
        "precisa_bu2": True,
    },
    "d_fatia": {
        "nome": "Mudança contra o 1º turno",
        "campo": "d_fatia_pp",
        "tipo": "divergente",
        "centro": 0,
        "limite": 10,
        "baixo": "Lula ganhou espaço",
        "alto": "Flávio ganhou espaço",
        "explica": (
            "Quanto a parcela de Flávio entre os dois mudou do 1º para o 2º turno, nas "
            "mesmas seções do prédio, em pontos. Mudança mistura quem foi votar, quem "
            "trocou de voto e quem anulou."
        ),
        "precisa_bu2": True,
    },
    "d_comp": {
        "nome": "Mudança do comparecimento",
        "campo": "d_comp_pp",
        "tipo": "divergente",
        "centro": 0,
        "limite": 10,
        "baixo": "Menos gente votou",
        "alto": "Mais gente votou",
        "explica": (
            "Diferença entre a parcela de eleitores que votou no 2º e no 1º turno, nas "
            "mesmas seções do prédio, em pontos."
        ),
        "precisa_bu2": True,
    },
    "abst": {
        "nome": "Abstenção no 2º turno",
        "campo": "abst_pct2",
        "tipo": "sequencial",
        "minimo": 10,
        "maximo": 40,
        "baixo": "Poucos faltaram",
        "alto": "Muitos faltaram",
        "explica": "Parcela dos eleitores do prédio que não votou no 2º turno.",
        "precisa_bu2": True,
    },
    "sinal": {
        "nome": "Sinais nas seções",
        "campo": "escore_max",
        "tipo": "sequencial",
        "minimo": 0,
        "maximo": 4,
        "baixo": "Nenhum sinal",
        "alto": "Vários sinais na mesma seção",
        "explica": (
            "Maior número de sinais numa seção do prédio, de 0 a 6 (comparecimento que "
            "subiu muito, biometria, horário, cédula). Sinal pede explicação, não prova "
            "irregularidade."
        ),
        "precisa_bu2": True,
    },
    "urna": {
        "nome": "Urna trocada entre os turnos",
        "campo": "urnas_trocadas",
        "tipo": "presenca",
        "baixo": "Mesma urna",
        "alto": "Alguma urna trocada",
        "explica": (
            "Prédio com ao menos uma seção que votou no 2º turno numa urna diferente da "
            "do 1º turno. Troca de urna é procedimento previsto e não muda votos."
        ),
        "precisa_bu2": True,
    },
    "mudanca": {
        "nome": "Mudança de endereço",
        "campo": "secoes_mudaram",
        "tipo": "presenca",
        "baixo": "Nenhuma seção mudou",
        "alto": "Alguma seção mudou de endereço",
        "explica": (
            "Prédio com ao menos uma seção que mudou de endereço entre os turnos, pelo "
            "arquivo de locais e pelo painel do TSE."
        ),
        "precisa_bu2": False,
    },
    "anomalia": {
        "nome": "Grupo atípico (estatística)",
        "campo": "secoes_anomalas",
        "tipo": "presenca",
        "baixo": "Nenhuma seção no grupo atípico",
        "alto": "Alguma seção no grupo atípico",
        "explica": (
            "Prédio com ao menos uma seção no grupo atípico do país. O grupo foi definido "
            "por mistura estatística sobre as frações do eleitorado nos dois turnos (votos "
            "de cada candidato, brancos, nulos e comparecimento sobre os aptos), sem o "
            "exterior. Atipicidade estatística não é irregularidade: o grupo pede "
            "explicação, não prova nada."
        ),
        "precisa_bu2": True,
        # sem o arquivo do motor o campo é nulo em todo prédio: cinza, não "nenhuma"
        "precisa_ml": True,
    },
}
CAMADAS["modelo"] = {
    "nome": "Modelo da urna",
    "campo": "modelo",
    "tipo": "categoria",
    "categorias": [*MODELOS_URNA, MISTO],
    "nomes": {**MODELOS_URNA, MISTO: "prédio com mais de um modelo"},
    "baixo": "",
    "alto": "",
    "explica": (
        "Modelo da urna eletrônica de cada seção, lido do boletim de urna: o do 2º turno "
        "quando o boletim já foi lido, senão o do 1º. O número do modelo é o ano do "
        "projeto. Prédio com seções em modelos diferentes aparece como misto."
    ),
    "precisa_bu2": False,
}
NIVEIS_LOG = {
    "0": "Registro de rotina",
    "1": "Um sinal no log",
    "2": "Sinais combinados",
    "3": "Conferir o arquivo",
}
CAMADAS["log2"] = {
    "nome": "Sinais nos logs, 2º turno",
    "campo": "log2_max",
    "tipo": "categoria",
    "categorias": list(NIVEIS_LOG),
    "nomes": NIVEIS_LOG,
    "baixo": "",
    "alto": "",
    "explica": (
        "Nível mais alto entre as seções do prédio no registro da urna do 2º turno: "
        "rotina (só bateria ou inspeção longa), um tipo de ocorrência, dois tipos, ou "
        "arquivo a conferir. Sinal pede explicação, não prova irregularidade."
    ),
    "precisa_bu2": False,
    "precisa_log2": True,
}
CAMADAS["log_subiu"] = {
    "nome": "Mudou entre os turnos",
    "campo": "log_subiu",
    "tipo": "presenca",
    "baixo": "Nenhuma seção subiu de nível",
    "alto": "Alguma seção subiu para sinais combinados ou arquivo a conferir",
    "explica": (
        "Prédio com ao menos uma seção que tinha só rotina ou um sinal no registro da "
        "urna do 1º turno e passou a sinais combinados ou arquivo a conferir no 2º."
    ),
    "precisa_bu2": False,
    "precisa_log2": True,
}
CAMADAS["chuva2"] = {
    "nome": "Chuva no dia do 2º turno",
    "campo": "chuva2_mm",
    "tipo": "sequencial",
    "minimo": 0,
    "maximo": 40,
    "baixo": "Sem chuva",
    "alto": "40 mm ou mais",
    "explica": (
        "Chuva de 25/10, das 0h às 24h, medida em pluviômetros do CEMADEN a até 50 km do "
        "local (média pelo inverso do quadrado da distância); sem estação por perto, o "
        "modelo meteorológico, provisório até a reanálise climática. Estimativa para a célula de "
        "0,25 grau, não medição no prédio."
    ),
    "precisa_bu2": False,
}
CAMADA_PADRAO = "resultado"


_OBS: dict[str, Any] = {}


def observado() -> dict[str, Any]:
    """Chuva de 25/10 por célula de 0,25° (``clima_2t``); vazio se ainda não gerada."""
    if not _OBS:
        if not OBSERVADO.exists():
            _OBS["doc"] = None
        else:
            d = json.loads(OBSERVADO.read_text(encoding="utf-8"))
            cols = d["colunas"]
            d["por"] = {
                k: dict(zip(cols, v, strict=True)) for k, v in d["celulas"].items()
            }
            _OBS["doc"] = d
    return _OBS["doc"] or {}


def chuva_do_ponto(lat: float, lon: float) -> dict[str, Any]:
    c = (
        observado()
        .get("por", {})
        .get(f"{math.floor(lat * 4) / 4:.2f},{math.floor(lon * 4) / 4:.2f}")
    )
    if not c:
        return {}
    return {
        "chuva2_mm": c["chuva_dia_mm"],
        "chuva2_vot_mm": c["chuva_votacao_mm"],
        "chuva2_fonte": c["fonte_dia"],
        "chuva2_fonte_vot": c["fonte_votacao"],
        "chuva2_dist_km": c["distancia_min_km"],
        "chuva2_n": c["n_estacoes"],
    }


def ponto(uf: str, lat: Any, lon: Any) -> tuple[float, float] | None:
    """Coordenada ``(lat, lon)`` quando é número e cai no território; senão ``None``."""
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return None
    la, lo = float(lat), float(lon)
    if la == 0 and lo == 0:
        return None
    if uf == "ZZ":
        ok = -90 <= la <= 90 and -180 <= lo <= 180
    else:
        ok = LAT_MIN <= la <= LAT_MAX and LON_MIN <= lo <= LON_MAX
    return (la, lo) if ok else None


def zona_de(local_id: str) -> int:
    return int(str(local_id).split("-")[2])


def mun_de(local_id: str) -> str:
    return str(local_id).split("-")[1]


def _pequeno(r: dict[str, Any]) -> bool:
    aptos = r.get("aptos2") if r.get("n_bu2") else r.get("aptos1")
    return aptos is not None and aptos < MIN_APTOS_VOTO


def modelo_secao(s: dict[str, Any]) -> str | None:
    """Modelo da urna da seção: o do 2º turno quando o boletim já foi lido, senão o do 1º."""
    if s.get("bu2") and s.get("modelo2"):
        return s["modelo2"]
    return s.get("modelo1")


def resumo_modelos(contagem: dict[str, int]) -> tuple[str | None, list[list[Any]]]:
    """Modelo do prédio (o único, ou ``misto`` com mais de um) e a contagem por modelo."""
    modelos = sorted(([m, n] for m, n in contagem.items()), key=lambda x: (-x[1], x[0]))
    if not modelos:
        return None, []
    return (modelos[0][0] if len(modelos) == 1 else MISTO), modelos


def resumo_logs(secoes: list[dict[str, Any]]) -> dict[str, Any]:
    """Atenção máxima dos logs no prédio em cada turno (0 a 3; ``None`` sem log lido) e
    quantas seções subiram de 0 ou 1 no 1º turno para 2 ou 3 no 2º."""

    def maximo(campo: str) -> int | None:
        vs = [s[campo] for s in secoes if isinstance(s.get(campo), int)]
        return max(vs) if vs else None

    subiu = sum(
        1
        for s in secoes
        if isinstance(s.get("log1_atencao"), int)
        and isinstance(s.get("log2_atencao"), int)
        and s["log1_atencao"] <= 1
        and s["log2_atencao"] >= 2
    )
    l2 = maximo("log2_atencao")
    return {
        "log1_max": maximo("log1_atencao"),
        "log2_max": l2,
        "log_subiu": subiu if l2 is not None else None,
    }


def secoes_por_local(origem: Path, uf: str) -> dict[str, dict[str, Any]]:
    """Seções principais de cada prédio e contagem de seções por modelo de urna."""
    out: dict[str, dict[str, Any]] = {}
    for arq in sorted((origem / "zona" / uf).glob("*.json.gz")):
        with gzip.open(arq, "rt", encoding="utf-8") as fh:
            z = json.load(fh)
        locais = tabela(z["locais"])
        contagem: list[dict[str, int]] = [defaultdict(int) for _ in locais]
        logs = [resumo_logs([]) for _ in locais]
        por_local: list[list[dict[str, Any]]] = [[] for _ in locais]
        for s in tabela(z["secoes"]):
            li = s.get("li")
            if not (isinstance(li, int) and 0 <= li < len(locais)):
                continue
            por_local[li].append(s)
            m = modelo_secao(s)
            if m:
                contagem[li][m] += 1
        for i, secs in enumerate(por_local):
            logs[i] = resumo_logs(secs)
        for loc, cont, lg in zip(locais, contagem, logs, strict=True):
            modelo, modelos = resumo_modelos(cont)
            out[loc["local_id"]] = {
                "secoes": sorted(int(x) for x in loc.get("secoes") or []),
                "modelo": modelo,
                "modelos": modelos,
                **lg,
            }
    return out


def linha_local(
    uf: str, r: dict[str, Any], zona: dict[str, Any] | None = None
) -> list[Any]:
    """Uma linha de ``COLUNAS_LOCAIS``; coordenada inválida vira ``null``."""
    pt = ponto(uf, r.get("lat"), r.get("lon"))
    z = zona or {}
    v = dict(r)
    v["secoes"] = z.get("secoes") or ([r["secao_link"]] if r.get("secao_link") else [])
    v["modelo"] = z.get("modelo")
    v["modelos"] = z.get("modelos") or []
    for c in ("log1_max", "log2_max", "log_subiu"):
        v[c] = z.get(c)
    v["id"] = r["local_id"]
    v["lat"], v["lon"] = (round(pt[0], 5), round(pt[1], 5)) if pt else (None, None)
    v["aprox"] = 1 if uf == "ZZ" and pt else 0
    if pt and uf != "ZZ":
        v.update(chuva_do_ponto(*pt))
    if not v.get("n_bu2"):
        # sem boletim do 2º turno não há variação nem sinal do 2º turno
        for c in (
            "comp_pct2",
            "d_comp_pp",
            "abst_pct2",
            "bn_pct2",
            "fatia_f2",
            "secoes_anomalas",
        ):
            v[c] = None
        v["d_fatia_pp"] = None
    if _pequeno(r):
        for c in CAMPOS_VOTO:
            v[c] = None
    return [v.get(c) for c in COLUNAS_LOCAIS]


def linha_municipio(mun: str, nome: str, t: dict[str, Any]) -> list[Any]:
    v = {"mun": mun, "nome": nome, **t}
    aptos = t.get("aptos2") if t.get("n_bu2") else t.get("aptos1")
    if aptos is not None and aptos < MIN_APTOS_VOTO:
        for c in CAMPOS_VOTO:
            v[c] = None
    return [v.get(c) for c in COLUNAS_MUNICIPIOS]


def _media(pts: list[tuple[float, float]]) -> list[float]:
    return [
        round(sum(p[0] for p in pts) / len(pts), 5),
        round(sum(p[1] for p in pts) / len(pts), 5),
        len(pts),
    ]


def ler(origem: Path = ORIGEM, ufs: set[str] | None = None) -> dict[str, Any]:
    """Lê o Politize-se e devolve ``{indice, ufs, zonas, cep}`` prontos para gravar."""
    indice = json.loads((origem / "indice.json").read_text(encoding="utf-8"))
    por_uf: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"locais": [], "municipios": [], "lista_mun": []}
    )
    zonas: dict[str, dict[int, list[tuple[float, float]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    cep8: dict[str, list[tuple[float, float]]] = defaultdict(list)
    cep5: dict[str, list[tuple[float, float]]] = defaultdict(list)
    secoes: dict[str, dict[str, dict[str, Any]]] = {}
    for m in tabela(indice["municipios"]):
        uf = m["uf"]
        if ufs and uf not in ufs:
            continue
        if uf not in secoes:
            secoes[uf] = secoes_por_local(origem, uf)
        arq = origem / m["arquivo"]
        if not arq.exists():
            continue
        cad = json.loads(arq.read_text(encoding="utf-8"))
        nome = cad.get("nome") or m["nome"]
        alvo = por_uf[uf]
        alvo["lista_mun"].append([m["mun_tse"], nome])
        alvo["municipios"].append(
            linha_municipio(m["mun_tse"], nome, cad.get("totais") or {})
        )
        for r in tabela(cad["locais"]):
            linha = linha_local(uf, r, secoes[uf].get(r["local_id"]))
            alvo["locais"].append(linha)
            if linha[I_LAT] is None:
                continue
            pt = (linha[I_LAT], linha[I_LAT + 1])
            zonas[uf][zona_de(r["local_id"])].append(pt)
            cep = str(r.get("cep") or "")
            if uf != "ZZ" and len(cep) == 8 and cep.isdigit():
                cep8[cep].append(pt)
                cep5[cep[:5]].append(pt)
    cep: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: {"exato": {}, "p5": {}}
    )
    for c, pts in cep8.items():
        cep[c[:2]]["exato"][c] = _media(pts)
    for c, pts in cep5.items():
        cep[c[:2]]["p5"][c] = _media(pts)
    return {
        "indice": indice,
        "ufs": dict(por_uf),
        "zonas": {
            uf: {str(z): _media(p) for z, p in sorted(zs.items())}
            for uf, zs in zonas.items()
        },
        "cep": dict(cep),
    }
