"""Orquestra o motor e escreve o payload, as saídas do mapa e o relatório em Markdown."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from clima_1t import (
    analises,
    controles,
    curiosos,
    grade,
    saidas,
    texto,
    texto_md,
    variaveis,
)
from clima_1t import estatistica as es
from clima_1t.coleta import agora
from mudancas_secoes_2t import cruzamentos as cz

ROOT = Path(__file__).resolve().parents[2]
RELATORIO = ROOT / "analysis/clima_1t_2026/relatorio.md"
PREVISAO = ROOT / "docs/assets/fiscais_mapa/clima/previsao.json"
SEED = 20261004


def ler_fontes() -> tuple[dict[str, Any], dict[str, int]]:
    urnas, totais = cz.ler_urnas()
    return (
        {
            "urnas": urnas,
            "logs": cz.ler_logs(),
            "atencao": cz.ler_atencao(),
            "t2022": cz.ler_2022(),
        },
        totais,
    )


def conferir_politize(urnas) -> dict[str, Any]:
    zonas = {
        (str(uf), int(z))
        for uf, z in zip(urnas["uf"], urnas["zona"], strict=True)
        if uf != "ZZ"
    }
    return cz.conferir_politize(urnas, zonas)


def previsao_resumo() -> dict[str, Any]:
    if not PREVISAO.exists():
        return {"situacao": "previsão ainda não gerada (scripts/clima-1t-previsao.py)"}
    d = json.loads(PREVISAO.read_text())
    return {
        "gerado_em": d["gerado_em"],
        "alvo": d["alvo"],
        "regra_risco": d["regra_risco"],
        "rotulo": d["rotulo"],
        "coleta": d.get("coleta"),
        "pais": d["resumo"]["pais"],
        "por_uf": d["resumo"]["por_uf"],
        "cidades_risco_alto": d["resumo"]["cidades_risco_alto"],
        "arquivo": str(PREVISAO.relative_to(ROOT)),
    }


def executar(reps: int = 2000, seed: int = SEED) -> dict[str, Any]:
    t0 = time.time()
    marcas: dict[str, float] = {}

    def marca(nome: str) -> None:
        marcas[nome] = round(time.time() - t0, 1)
        print(f"[{marcas[nome]:7.1f} s] {nome}", flush=True)

    archive = variaveis.ler_consolidado()
    clima = variaveis.clima_por_celula(archive)
    locais = grade.ler_locais()
    fontes, totais = ler_fontes()
    marca("fontes lidas")
    urnas = variaveis.montar_urnas(clima, locais, fontes)
    tab_locais = variaveis.por_local(urnas, locais, clima)
    u, cel, n_cel = analises.preparar(urnas)
    boot = es.BootCelulas(n_cel, reps, seed)
    marca("urnas e locais montados")
    p1 = analises.bateria_x_chuva(u, cel, boot)
    marca("1. bateria x chuva (bootstrap)")
    p1["regressoes"] = analises.regressoes_bateria(u)
    marca("1. regressões")
    p2 = analises.abstencao_x_chuva(u, cel, boot)
    marca("2. abstenção x chuva (bootstrap)")
    p2["regressoes"] = analises.regressoes_abstencao(u)
    marca("2. regressões")
    p3 = analises.abstencao_x_bateria(u, cel, boot)
    marca("3. abstenção x bateria")
    p4 = analises.cadeia_completa(u)
    p5 = curiosos.listas(tab_locais)
    p5["f_mudancas_2t"] = curiosos.mudancas(tab_locais)
    p6 = analises.mapa_resumo(u, tab_locais)
    marca("4 a 6")
    politize = conferir_politize(fontes["urnas"])
    marca("conferência com o Politize")
    gerado = agora()
    fonte_mapa = (
        "Open-Meteo archive (ERA5/ERA5-Land, célula de 0,25°); boletins e logs do 1º turno "
        "(TSE); 2º turno de 2022 (TSE); motor scripts/clima-1t.py"
    )
    contagem = saidas.gravar_mapa(tab_locais, gerado, fonte_mapa)
    n_csv = saidas.gravar_csv(tab_locais)
    payload: dict[str, Any] = {
        "gerado_em": gerado,
        "versao": "1.0",
        "parametros": {"reps": reps, "seed": seed},
        "cobertura": {
            "archive": {
                k: v for k, v in archive["cobertura"].items() if k != "faltando_chaves"
            },
            "locais_brasil": len(locais),
            "locais_com_coordenada": sum(1 for lc in locais if lc.lat is not None),
            "locais_com_clima": int(tab_locais["chuva_04_10_mm"].notna().sum()),
            "urnas_brasil": int((fontes["urnas"]["uf"] != "ZZ").sum()),
            "urnas_amostra": len(u),
            "celulas_na_amostra": n_cel,
            "locais_por_uf_no_mapa": contagem,
            "linhas_csv": n_csv,
        },
        "janela_votacao": texto.JANELA,
        "faixas": {"chuva": variaveis.ROTULO_CHUVA, "rajada": variaveis.ROTULO_RAJADA},
        "totais": totais,
        "bateria_x_chuva": p1,
        "abstencao_x_chuva": p2,
        "abstencao_x_bateria": p3,
        "cadeia_completa": p4,
        "locais_curiosos": p5,
        "mapa_resumo": p6,
        "previsao_25_10": previsao_resumo(),
        "conferencia_pontos": curiosos.conferencia_pontos(tab_locais),
        "conferencia_politize": politize,
        "limites": texto.LIMITES,
        "decisoes": texto.DECISOES,
    }
    payload["controles"] = controles.controles(
        urnas, u, tab_locais, archive, totais, politize, fontes["atencao"]
    )
    payload["fontes"] = controles.fontes()
    payload["resumo"] = texto.resumo(payload)
    payload["achados"] = texto.achados(payload)
    marca("controles e fontes")
    payload["_interno"] = {"segundos": marcas}
    saidas.gravar_json(saidas.PAYLOAD, payload)
    publico = {k: v for k, v in payload.items() if k != "_interno"}
    saidas.gravar_json(saidas.PUBLICO, publico)
    RELATORIO.write_text(texto_md.montar(payload), encoding="utf-8")
    marca("saídas gravadas")
    return payload
