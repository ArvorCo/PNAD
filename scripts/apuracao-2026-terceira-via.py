#!/usr/bin/env python3
"""Onde está o voto da terceira via, cidade por cidade (capítulo 14 do dossiê da apuração).

Lê o banco da apuração (somente leitura; versão vigente = última gerada pelo
TSE), os arquivos de 2022 do TSE e os JSON da casa, e grava:

- ``analysis/apuracao_2026/dados/terceira_via.json``: estoque de terceira via por
  município, matriz de transferência aplicada localmente, direita local (vão do
  governador e do Senado sobre Flávio), teto endereçável, índice de prioridade
  com sensibilidades, agregados por região e UF, riscos, achado contrário e o
  nulo do 2º turno de 2022;
- ``analysis/apuracao_2026/terceira_via.md``: o memorando com os números.

Uso:
    python3 scripts/apuracao-2026-terceira-via.py
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apuracao_2026 import terceira_via as T
from apuracao_2026 import terceira_via_agregados as A
from apuracao_2026 import terceira_via_leitura as L
from apuracao_2026 import terceira_via_regua as RU
from apuracao_2026 import terceira_via_reguas as RG
from apuracao_2026 import terceira_via_secoes as S
from apuracao_2026 import terceira_via_texto as X
from apuracao_2026.dados import iso_z

TRAVESSAO = chr(0x2014)
SAIDA_JSON = L.DADOS / "terceira_via.json"
SAIDA_MD = L.ROOT / "analysis/apuracao_2026/terceira_via.md"
COLUNAS = (
    "cd",
    "ibge",
    "uf",
    "nome",
    "regiao",
    "capital",
    "eleitores",
    "comparecimento",
    "validos",
    "flavio",
    "lula",
    *T.GRUPOS,
    "estoque",
    "estoque_pct",
    "margem_pp",
    "classe",
    "para_flavio",
    "para_lula",
    "fora",
    "saldo",
    "saldo_df",
    "b22_2t_pct",
    "tv22_pct",
    "bn22_1t_pct",
    "bn22_2t_pct",
    "delta_bn22_pp",
    "gov22_2t",
    "gov26_2t",
    "local_lider",
    "vao_votos",
    "vao_pp",
    "teto",
    "fator",
    "prioridade",
    "posicao",
    "saldo_urna",
    "regua_motivo",
)
INTEIROS = {
    "para_flavio",
    "para_lula",
    "fora",
    "saldo",
    "saldo_df",
    "prioridade",
    "saldo_urna",
}


def _celula(chave: str, v: Any) -> Any:
    if v is None:
        return None
    if chave in INTEIROS:
        return round(v)
    if isinstance(v, float):
        return round(v, 3 if chave == "fator" else 2)
    return v


def colunar(linhas: list[dict]) -> dict[str, Any]:
    return {
        "colunas": list(COLUNAS),
        "linhas": [[_celula(c, m.get(c)) for c in COLUNAS] for m in linhas],
    }


def conferencia(
    fontes: dict, brasil: list[dict], exterior: list[dict]
) -> dict[str, Any]:
    """Somas municipais contra o arquivo nacional; 2022 contra o arquivo do TSE."""
    pres = fontes["pres"]
    numero_de = {sq: int(c["numero"]) for sq, c in pres["candidatos"].items()}
    br = pres["arquivos"]["BR"]
    soma: dict[int, int] = {}
    for a in pres["arquivos"].values():
        if a["nivel"] != "mu":
            continue
        for sq, v in a["votos"].items():
            soma[numero_de[sq]] = soma.get(numero_de[sq], 0) + v
    nac = {numero_de[sq]: v for sq, v in br["votos"].items()}
    dif = {str(n): soma.get(n, 0) - v for n, v in sorted(nac.items())}
    det = fontes["det22"]
    det_soma = {
        t: {
            k: sum(x[t][k] for x in det.values() if t in x)
            for k in ("comparecimento", "brancos", "nulos")
        }
        for t in (1, 2)
    }
    det_ok = all(
        det_soma[t][k] == fontes["api22"][t][k] for t in (1, 2) for k in det_soma[t]
    )
    P = fontes["presidente"]
    cols = P["municipios"]["colunas"]
    antigos = {r[0]: dict(zip(cols, r, strict=True)) for r in P["municipios"]["linhas"]}
    mudaram = [
        {
            "cd": m["cd"],
            "uf": m["uf"],
            "nome": m["nome"],
            "validos_presidente_json": antigos[m["cd"]]["validos"],
            "validos_agora": m["validos"],
        }
        for m in brasil
        if m["cd"] in antigos and antigos[m["cd"]]["validos"] != m["validos"]
    ]
    mais_nova = max(
        a["gerado_em"] for a in pres["arquivos"].values() if a["nivel"] == "mu"
    )
    return {
        "soma_municipal_menos_nacional": dif,
        "soma_municipal_igual_nacional": all(v == 0 for v in dif.values()),
        "validos_nacional": br["validos"],
        "validos_municipios": sum(m["validos"] for m in brasil)
        + sum(m["validos"] for m in exterior),
        "arquivo_nacional_gerado_em": br["gerado_em"],
        "arquivo_municipal_mais_novo_gerado_em": mais_nova,
        "municipios_incompletos": sum(
            1
            for a in pres["arquivos"].values()
            if a["nivel"] == "mu" and a["secoes"] < a["secoes_total"]
        ),
        "regerados_depois_de_presidente_json": mudaram,
        "presidente_json_gerado_em": P["meta"]["gerado_em"],
        "detalhe_2022_soma": det_soma,
        "detalhe_2022_igual_arquivo_nacional": det_ok,
        "municipios_sem_2022": [
            m["cd"] for m in brasil if m.get("delta_bn22_pp") is None
        ],
    }


def _publico(modelo: dict) -> dict:
    return {k: v for k, v in modelo.items() if not k.startswith("_")}


def montar_reguas(brasil: list[dict], conv: dict, fontes: dict) -> dict[str, Any]:
    """Régua da urna de 2022 (regressão ecológica), aplicação a 2026 e as duas réguas lado a lado."""
    amostra = RU.amostra(brasil)
    classe = RU.modelo(amostra, "classe", T.CLASSES)
    regiao = RU.modelo(amostra, "regiao", RU.REGIOES)
    unico = RU.modelo(amostra, None, [])
    RU.aplicar(brasil, classe, regiao, conv["por_classe"])
    nac = RG.preparar(brasil)
    return {
        "regras": X.regras_reguas(),
        "modelos": {
            "classe": _publico(classe),
            "regiao": _publico(regiao),
            "unico": _publico(unico),
            "sem_efeito_fixo": RU.sem_efeito_fixo(amostra),
        },
        "media_nacional_por_voto": {k: round(v, 4) for k, v in nac.items()},
        "totais": RG.totais(brasil, RU.total_ic(brasil, classe)),
        "rankings": RG.rankings(brasil),
        "movimentos": RG.movimentos(brasil, fontes["estrategia_2t"]),
        "retrovisao": L.retrovisao(),
    }


def montar(fontes: dict) -> dict[str, Any]:
    mat = S.matrizes(fontes)
    locais = S.direita_local(fontes)
    brasil, exterior = S.municipios(fontes, mat, locais)
    A.aplicar_prioridade(brasil)
    ag = A.agregados(brasil, exterior)
    diferenca = fontes["estrategia_2t"]["aritmetica"]["primeiro_turno"][
        "diferenca_votos"
    ]
    nulo = A.nulo_2022(brasil, fontes["api22"], ag)
    conv = A.conversao_2022(brasil)
    reguas = montar_reguas(brasil, conv, fontes)
    return {
        "meta": {
            "gerado_em": iso_z(datetime.now(timezone.utc)),
            "arquivo": "terceira_via.json",
            "script": "scripts/apuracao-2026-terceira-via.py",
            "banco": L.relativo(L.BANCO),
            "regra_de_versao": "versão vigente de cada arquivo = última gerada pelo TSE (gerado_em)",
            "fontes": [
                "apuracao/data/apuracao.sqlite (presidente, cargo 1; governador, cargo 3; Senado, cargo 5; arquivos de UF e de município)",
                L.relativo(L.MUNICIPIOS_2022),
                f"{L.relativo(L.DETALHE_2022)} (membro {L.MEMBRO_DETALHE})",
                "data/raw/tse_resultados/api_2022/br-c0001-e000544-r.json e -e000545-r.json (conferência)",
                "analysis/apuracao_2026/dados/estrategia_2t.json (matrizes Nexus e Datafolha, linha de cada candidatura, UFs com 2º turno de governador em 2022)",
                "analysis/apuracao_2026/dados/senado_x_flavio.json (bloco aliado ao Senado, eleitos e melhor candidatura)",
                "analysis/apuracao_2026/dados/governadores.json (vão estadual, lado de cada governador, 2º turno de 2026)",
                "analysis/apuracao_2026/dados/exterior.json (país de cada cidade)",
            ],
        },
        "regras": X.regras(mat),
        "conferencia": conferencia(fontes, brasil, exterior),
        "matriz": {k: v for k, v in mat.items() if k not in ("nexus", "datafolha")}
        | {"linhas_nexus": mat["nexus"], "linhas_datafolha": mat["datafolha"]},
        "direita_local": locais,
        "agregados": ag,
        "conversao_2022": conv,
        "reguas": reguas,
        "prioridade": A.prioridade(brasil, diferenca),
        "teto": A.teto(brasil),
        "riscos": A.riscos(brasil, ag, nulo),
        "contrario": A.contrario(brasil, ag),
        "nulo_2022": nulo,
        "exterior": {
            "cidades": len(exterior),
            "maiores": [
                {
                    "cd": m["cd"],
                    "nome": m["nome"],
                    "pais": m.get("pais"),
                    "estoque": m["estoque"],
                    "margem_pp": T.r2(m["margem_pp"]),
                    "classe": m["classe"],
                    "saldo": round(m["saldo"]),
                }
                for m in exterior[:15]
            ],
        },
        "municipios": colunar(brasil),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, default=SAIDA_JSON)
    ap.add_argument("--md", type=Path, default=SAIDA_MD)
    a = ap.parse_args()
    inicio = time.time()
    dados = montar(L.ler_tudo())
    texto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    if TRAVESSAO in texto:
        raise SystemExit("terceira_via.json: travessão no texto gerado")
    if not dados["conferencia"]["soma_municipal_igual_nacional"]:
        print(
            "aviso: soma dos municípios difere do arquivo nacional",
            dados["conferencia"]["soma_municipal_menos_nacional"],
        )
    a.json.write_text(texto + "\n", encoding="utf-8")
    memo = X.memorando(dados)
    if TRAVESSAO in memo:
        raise SystemExit("terceira_via.md: travessão no texto gerado")
    a.md.write_text(memo, encoding="utf-8")
    n = dados["agregados"]["brasil"]
    print(
        f"{L.relativo(a.json)}: {a.json.stat().st_size:,} bytes; {L.relativo(a.md)}; "
        f"estoque {n['estoque']:,} ({n['onde_flavio_venceu_parcela']}% onde Flávio venceu); "
        f"{time.time() - inicio:.1f} s"
    )


if __name__ == "__main__":
    main()
