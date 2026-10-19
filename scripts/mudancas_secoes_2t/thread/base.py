"""Base da thread das mudanças de local: caminhos, leitura dos JSONs e valores.

Todo número que aparece num post ou num card sai de ``mudancas.json`` (e do índice do
Politize, para a contagem do aplicativo), formatado em pt-BR. Os modelos de texto só
levam campos ``{nome}``; ``valores()`` é o único lugar onde um número vira texto.
"""

from __future__ import annotations

import json
import re
from functools import cache

from apuracao_2026.thread_base import ROOT, num, pct

SLUG = "mudancas_secoes_thread"
URL = f"https://brasil.arvor.co/{SLUG}.html"
OG = f"https://brasil.arvor.co/img/og/{SLUG}.png"
LAUDO = "mudancas_secoes_abstencoes"
URL_LAUDO = f"https://brasil.arvor.co/{LAUDO}.html"
URL_POLITIZE = "https://brasil.arvor.co/politizesuavizinhanca.html"
SAIDA = ROOT / "docs" / f"{SLUG}.html"
PNG_DIR = ROOT / "docs/img/mudancas_secoes/thread"
JSON_MOTOR = ROOT / "analysis/mudancas_secoes_2t/mudancas.json"
JSON_POLITIZE = ROOT / "docs/assets/politize/dados/mudancas/indice.json"

# Constantes de texto que não são medidas: datas do calendário e a base legal.
DIA_2T = "25/10"
TEMPO = "10 segundos"
UM_KM = "1 km"
CHUVA_FORTE = "20 mm"
JANELA_CLIMA = "5 a 18/10"
IC = "IC de 95%"
LEI = "Lei 9.504/1997, art. 39, § 5º"


@cache
def dados() -> dict:
    return json.loads(JSON_MOTOR.read_text(encoding="utf-8"))


@cache
def politize() -> dict:
    return json.loads(JSON_POLITIZE.read_text(encoding="utf-8"))


def publico(i: str) -> dict:
    return next(
        x for x in dados()["confronto_publico"]["numeros_publicos"] if x["id"] == i
    )


def dia(carimbo: str) -> str:
    """'17/10/2026 06:28' vira '17/10'."""
    return carimbo.split("/2026")[0]


def hora(carimbo: str) -> str:
    """'18/10/2026 20:27' vira '20h27'."""
    return carimbo.split(" ")[-1].replace(":", "h")


def pontos(v: float, casas: int = 2) -> str:
    return num(v, casas)


def mais(v: float, casas: int = 2) -> str:
    return "+" + num(v, casas)


def pares_com_motivo() -> tuple[int, int]:
    """Pares de locais com motivo em nota de TRE contra o total de pares."""
    locais = [x for x in dados()["locais"] if x["mudanca_real"]]
    com = 0
    for x in locais:
        m = x.get("motivo_tre")
        texto = (m or {}).get("texto") if isinstance(m, dict) else m
        if texto and texto.strip().lower() != "não informado":
            com += 1
    return com, len(locais)


def locais_rj() -> int:
    ref = dados()["efeito_1t"]["rj"]["estado_rj"]["referencia_imprensa"]
    m = re.match(r"(\d+) locais", ref)
    if not m:
        raise ValueError("referência de imprensa do Rio sem a contagem de locais")
    return int(m.group(1))


def _fixos() -> dict[float, dict]:
    return {f["abstencao_extra_pp"]: f for f in dados()["cenarios_abstencao"]["fixos"]}


def valores() -> dict[str, str]:
    D = dados()
    P = politize()
    R = D["resumo"]
    MR = R["mudanca_real"]
    FO = R["fora_do_original"]
    tse, col = publico("tse_agencia_brasil"), publico("coligacao_peticao")
    con, pai = publico("forum_exportacao"), publico("painel_tse")
    T = D["distancia"]["teste_hipotese"]
    EF = D["efeito_1t"]
    DD = EF["dif_em_dif"]["diferenca"]["mesmo_municipio"]["diferenca_pp"]
    faixas = {f["faixa"]: f for f in EF["dose_resposta"]["faixas"]}
    longe = faixas["acima de 5 km"]["dif_em_dif"]["mesmo_municipio"]["diferenca_pp"]
    rj = EF["rj"]["dif_em_dif_mesma_zona"]["diferenca_pp"]["valor"]
    C = D["cenarios_abstencao"]
    E = C["estimativa_brasileira"]
    comp = C["composicao_1t"]
    fixos = _fixos()
    pp = sorted(fixos)
    var = [
        fixos[p]["mudanca_real"]["variacao_diferenca_flavio_menos_lula_votos"]
        for p in pp
    ]
    centro = E["seguem_fora_do_original_2t"]["central"]
    clima = D["clima_resumo"]
    com_motivo, n_pares = pares_com_motivo()
    por_fonte = P["por_fonte"]
    return {
        "manchete_mil": f"{tse['secoes']['publico'] // 1000} mil",
        "n_tse": num(tse["secoes"]["publico"]),
        "d_tse": dia(tse["carimbo"]),
        "n_col": num(col["secoes"]["publico"]),
        "e_col": num(col["eleitores"]["publico"]),
        "d_col": dia(col["carimbo"]),
        "n_con": num(con["secoes"]["publico"]),
        "e_con": num(con["eleitores"]["publico"]),
        "d_con": dia(con["carimbo"]),
        "n_pai": num(pai["secoes"]["publico"]),
        "e_pai": num(pai["eleitores"]["publico"]),
        "d_pai": dia(pai["carimbo"]),
        "h_pai": hora(pai["carimbo"]),
        "n_mr": num(MR["secoes"]),
        "e_mr": num(MR["eleitores"]),
        "n_mun": num(MR["municipios"]),
        "n_a": num(R["mudanca_real"]["por_categoria"]["A"]["secoes"]),
        "n_fora": num(FO["secoes_2t"]),
        "e_fora": mi(FO["eleitores_2t"]),
        "dif_col": pct(
            abs(
                D["confronto_publico"][
                    "eleitores_fora_do_original_2t_contra_coligacao"
                ]["diferenca_pct"]
            ),
            1,
        ),
        "med": num(MR["distancia_mediana_m"]),
        "viz": num(T["predio_vizinho"]["mediana_m"]["valor"]),
        "pct1km": pct(T["novas_realocacoes"]["parcela_pct"]["acima_1km"]["valor"], 1),
        "chuva_mud": pct(
            clima["origem_mudanca_real"]["chuva_max_05a18_acima_20mm_pct"], 1
        ),
        "chuva_ctl": pct(clima["controle"]["chuva_max_05a18_acima_20mm_pct"], 1),
        "n_com_motivo": num(com_motivo),
        "n_pares": num(n_pares),
        "pol_secoes": num(P["total_secoes"]),
        "pol_eleitores": num(P["total_eleitores"]),
        "pol_ambos": num(por_fonte["ambos"]),
        "pol_zip": num(por_fonte["so_zip"]),
        "pol_painel": num(por_fonte["so_painel"]),
        "dd": pontos(DD["valor"]),
        "dd_lo": pontos(DD["ic95"][0]),
        "dd_hi": pontos(DD["ic95"][1]),
        "longe": mais(longe["valor"]),
        "rj": mais(rj),
        "rj_locais": num(locais_rj()),
        "mare": pct(EF["rj"]["zona_161"]["abstencao_zona_1t"]),
        "urnas_fora": num(centro["urnas"]),
        "pf": num(centro["perdidos"]["flavio"]),
        "pl": num(centro["perdidos"]["lula"]),
        "dif_votos": num(centro["variacao_diferenca_flavio_menos_lula_votos"]),
        "pct_l": pct(comp["fora_do_original_2t"]["lula_validos_pct"]),
        "pct_f": pct(comp["fora_do_original_2t"]["flavio_validos_pct"]),
        "urnas_mr": num(comp["mudanca_real"]["urnas"]),
        "pct_l_mr": pct(comp["mudanca_real"]["lula_validos_pct"]),
        "pct_f_mr": pct(comp["mudanca_real"]["flavio_validos_pct"]),
        "c_min": mais(pp[0], 0),
        "c_max": mais(pp[-1], 0),
        "v_min": num(var[0]),
        "v_max": num(var[-1]),
        "saldo": num(
            abs(
                E["saldo_1t_para_2t"]["central"][
                    "variacao_diferenca_flavio_menos_lula_votos"
                ]
            )
        ),
        "teto_rio": num(
            D["cenarios_abstencao"]["estimativa_rio"]["seguem_fora_do_original_2t"][
                "variacao_diferenca_flavio_menos_lula_votos"
            ]
        ),
        "concord": pct(D["confronto_painel"]["concordancia_pct"], 1),
        "dia_2t": DIA_2T,
        "tempo": TEMPO,
        "um_km": UM_KM,
        "mm20": CHUVA_FORTE,
        "janela_clima": JANELA_CLIMA,
        "ic": IC,
        "lei": LEI,
        "faixa_longe": "Acima de 5 km",
        "link_politize": URL_POLITIZE,
        "link_laudo": URL_LAUDO,
    }


def mi(v: float) -> str:
    """1.767.261 vira '1,77 milhão'."""
    x = num(v / 1e6, 2)
    return f"{x} milhão" if v < 2e6 else f"{x} milhões"


def caminhos_png(n: int) -> list[str]:
    rel = PNG_DIR.relative_to(ROOT / "docs")
    return [f"{rel.as_posix()}/{i:02d}.png" for i in range(1, n + 1)]
