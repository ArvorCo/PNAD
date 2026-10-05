#!/usr/bin/env python3
"""A noite por região e os estados lentos, 2022 contra 2026.

Lê, só para leitura, o banco da apuração (`apuracao/data/apuracao.sqlite`: os 28
arquivos de UF de presidente, o nacional e os arquivos de andamento por UF), a
coleta seção a seção de 2026 (`apuracao/data/secoes_2026.sqlite`, parcial) e o
detalhe por seção de 2022 do TSE (`data/raw/tse_resultados/
detalhe_votacao_secao_2022.zip`, membro `_BR.csv`, em fluxo). Grava:

- `analysis/apuracao_2026/dados/noite_regioes.json`: a apuração minuto a minuto
  por região, os lotes de 5 minutos, os marcos de 50%, 90% e 100% de cada região,
  a contribuição de cada região para a diferença e o retrato que o painel
  nacional mostrava em cada versão;
- `analysis/apuracao_2026/dados/lentidao_ufs.json`: os marcos de 50%, 90%, 99% e
  100% das seções de cada UF em 2022 e 2026, nas duas réguas, os últimos
  municípios, a cauda e os testes de fuso e de repetição.

Uso:
    python3 scripts/apuracao-2026-noite-regioes.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apuracao_2026 import lentidao_dados as LD
from apuracao_2026 import lentidao_fontes as LF
from apuracao_2026 import noite_regioes as NR
from apuracao_2026.banco import Banco
from apuracao_2026.contexto import BANCO, DETALHE_2022, SAIDA
from apuracao_2026.noite_regioes_fontes import series_presidente

ROOT = Path(__file__).resolve().parents[1]
SECOES_2026 = ROOT / "apuracao/data/secoes_2026.sqlite"
INICIO = "2026-10-04T20:00:00Z"  # 17h de Brasília, fechamento das urnas
FIM = "2026-10-05T06:00:00Z"  # 03h de Brasília, depois da versão nacional final
MARCAS = (
    "2026-10-04 18:30",
    "2026-10-04 19:00",
    "2026-10-04 19:32",
    "2026-10-04 20:30",
)


def _sha(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def _agora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _minutos_desde_17h(hora_brt: str) -> float:
    dt = datetime.fromisoformat(hora_brt)
    return (dt - LF.FECHAMENTO_2026).total_seconds() / 60


def noite(series, nacional) -> dict[str, Any]:
    corpo = NR.montar(series, nacional, INICIO, FIM, MARCAS)
    meta = {
        "gerado_em": _agora(),
        "fonte": (
            "apuracao/data/apuracao.sqlite, arquivos u:6257:1:uf:<uf>:: (27 UFs e "
            "exterior) e u:6257:1:br:::, versões novas pela hora de geração do TSE"
        ),
        "relogio": "hora de geração do TSE, Brasília (UTC-3)",
        "passo_min": 1,
        "lote_min": 5,
        "inicio_brt": NR.hora_de(
            datetime.fromisoformat(INICIO.replace("Z", "+00:00")).timestamp()
        ),
        "fim_brt": NR.hora_de(
            datetime.fromisoformat(FIM.replace("Z", "+00:00")).timestamp()
        ),
        "regra": (
            "Estado de cada arquivo de UF num instante = última versão gerada até ele. "
            "Soma das regiões = soma dos 28 arquivos, que é a contagem já totalizada; o "
            "arquivo nacional atrasou em relação a ela nas paradas. Lote = o que entrou "
            "entre dois instantes da grade. A série mostra o que o TSE publicou e o "
            "coletor guardou (leitura a cada 30 a 60 s; em MG e SP, de 2 a 3 min)."
        ),
        "nota_painel": (
            "painel_nacional: para cada versão do arquivo nacional, o primeiro instante "
            "em que a soma das UFs alcançou as mesmas seções; o atraso do retrato é a "
            "geração da versão nacional menos esse instante."
        ),
    }
    return {"meta": meta, **corpo}


def lentidao(series, banco: Banco, pausa_ger) -> dict[str, Any]:
    print("lendo 2022 por seção (fluxo)...")
    s22 = LF.secoes_2022(DETALHE_2022)
    print("lendo carimbos de recebimento de 2026...")
    r26 = LF.recebimento_2026(SECOES_2026)
    print("lendo municípios pelos arquivos de andamento...")
    ab26 = LF.municipios_ab(banco)
    completas = sorted(
        u
        for u, c in r26["contagens"].items()
        if u != "zz"
        and c.get("proprias")
        and (c.get("totalizadas_com_carimbo", 0) + c.get("recebidas_depois", 0))
        / c["proprias"]
        >= LD.COBERTURA_COMPLETA
    )
    pausa_rec = LD.pausa_no_recebimento(r26, s22, completas)
    lac = pausa_rec["lacuna_2026"]
    janela_rec = (lac["de"], lac["ate"]) if lac["minutos"] else None
    ufs = LD.montar_ufs(series, s22, r26, ab26, pausa_ger, janela_rec)
    meta = {
        "gerado_em": _agora(),
        "fontes": {
            "2026_totalizado": (
                "apuracao/data/apuracao.sqlite, arquivos u:6257:1:uf:<uf>::, hora de "
                "geração da versão em que as seções totalizadas passaram de cada fração"
            ),
            "2026_recebido": (
                "apuracao/data/secoes_2026.sqlite, secao.dr_hr (carimbo de recebimento "
                "do boletim no aux de cada seção, hora do TSE), só status Totalizada; "
                "coleta parcial, ver recebido_2026 de cada UF"
            ),
            "2026_municipios": (
                "apuracao/data/apuracao.sqlite, arquivos ab:6257::uf:<uf>::, primeira "
                "versão com st = ts em cada município"
            ),
            "2022": (
                f"{DETALHE_2022.relative_to(ROOT)}, membro {LF.MEMBRO_2022}, 1º turno, "
                "cargo 1; DT_RECEBIMENTO_BU_HOR_TSE (recebimento do boletim) e "
                "DT_PRIM_TOT_PARCIAL_HOR_TSE (primeira totalização parcial), "
                "definidas no leiame.pdf do mesmo ZIP, p. 5"
            ),
        },
        "sha256_2022_zip": _sha(DETALHE_2022),
        "coleta_secoes_2026": {
            "meta": r26["meta"],
            "ufs_com_carimbo_completo": [u.upper() for u in completas],
        },
        "relogio": (
            "minutos desde as 17h de Brasília do dia da eleição (02/10/2022 e "
            "04/10/2026); urnas fecharam às 17h de Brasília nas 27 UFs nos dois anos"
        ),
        "regra_marco": (
            "fração q alcançada quando ceil(q × seções) já têm tempo; 100% é a última "
            "seção. Totalizado 2026 = versão do arquivo de UF; totalizado 2022 = "
            "primeira totalização parcial da seção."
        ),
        "regra_lenta": "lenta = marco acima da mediana das 27 UFs naquele ano",
    }
    return {
        "meta": meta,
        "nacional": LD.nacional(series, s22),
        "resumo_99": LD.resumo_marcos(ufs, "99"),
        "resumo_90": LD.resumo_marcos(ufs, "90"),
        "estrutural": LD.estrutural(ufs, s22, ab26),
        "recebido_x_totalizado_2022": LD.atraso_2022(s22),
        "pausa": {
            "geracao_uf": {
                "de": LD.hms(pausa_ger[0]),
                "ate": LD.hms(pausa_ger[1]),
                "minutos": round(pausa_ger[1] - pausa_ger[0], 2),
                "fonte": "noite_regioes.json, lacuna_da_soma",
            },
            "recebimento": pausa_rec,
        },
        "encerramento_local_2026": {
            u.upper(): v for u, v in sorted(r26["encerramento_local"].items())
        },
        "sem_carimbo_2022": s22["sem_carimbo"],
        "grade_min": LD.GRADE,
        "ufs": ufs,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", type=Path, default=SAIDA)
    a = ap.parse_args()
    banco = Banco(BANCO)
    try:
        print("lendo séries de presidente por UF...")
        series, nacional = series_presidente(banco)
        N = noite(series, nacional)
        lac = N["lacuna_da_soma"]
        pausa = (_minutos_desde_17h(lac["de_brt"]), _minutos_desde_17h(lac["ate_brt"]))
        T = lentidao(series, banco, pausa)
    finally:
        banco.fechar()
    a.saida.mkdir(parents=True, exist_ok=True)
    for nome, obj in (("noite_regioes.json", N), ("lentidao_ufs.json", T)):
        caminho = a.saida / nome
        caminho.write_text(
            json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        print(f"{caminho.relative_to(ROOT)}: {caminho.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
