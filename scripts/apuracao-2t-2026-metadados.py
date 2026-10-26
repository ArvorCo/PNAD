#!/usr/bin/env python3
"""Metadados das urnas por seção: repetição entre seções e coerência entre BU, `.vsc` e log.

Lê, só para leitura, os BUs dos dois turnos (`apuracao/data/secoes_2026.sqlite` e
`secoes_2t_2026.sqlite`), os `.vsc` (`apuracao/data/vsc_2t_2026.sqlite`, coleta de
`apuracao/scripts/vsc-coletar.ts`) e, quando existir, o log processado do 2º turno
(`data/outputs/logs_urnas_2t_2026.sqlite`). Roda com qualquer cobertura: o relatório
diz quanto de cada fonte foi lido. Grava `analysis/apuracao_2t_2026/dados/metadados.json`
e `metadados.md`. Rótulo: pede explicação, não prova irregularidade.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from apuracao_2t_2026 import metadados_regras as rg
from apuracao_2t_2026.base import SAIDA
from apuracao_2t_2026.metadados_base import (
    BANCO_1T,
    BANCO_2T,
    BANCO_LOGS_2T,
    BANCO_VSC,
    ler_bu,
    ler_logs,
    ler_vsc,
)
from apuracao_2t_2026.metadados_texto import markdown
from apuracao_2t_2026.urnas_analise import preparar
from apuracao_2t_2026.urnas_base import CHAVE

DIAS = {"1t": "2026-10-04", "2t": "2026-10-25"}
FORMATO_VSC = (
    "Arquivo DER com três blocos: assinatura de software do TSE (usuário SEVIN), assinatura de "
    "hardware da urna (usuário UEAO e a série da urna) e um rodapé com o código do modelo (13, 15, "
    "20, 22) e o algoritmo da chave de hardware. Cada bloco lista os arquivos da seção (bu.dat, "
    "rdv.dat, jufa.dat, imgbu.dat, imgze.dat, hash.dat, wsqbio.jez, wsqman.jez, wsqmes.jez, mr.ver, "
    "log.jez; no sistema de apuração, busa.dat e logsa.jez) com tamanho, SHA-512 e assinatura. O "
    "bloco de hardware termina no certificado X.509 da urna: PEM e Ed521 nas UE2020 e UE2022 (AC "
    "UE2020 e AC UE2022), DER e ECDSA P-521 nas UE2013 e UE2015 (AC URNA). A urna assina o SHA-512 "
    "do resumo SHA-512, a mesma regra do QR Code do BU."
)


def preparar_vsc(v: pd.DataFrame) -> pd.DataFrame:
    v = v.rename(columns={"sha256": "vsc_sha256"}).copy()
    v["cert_serial_ac"] = v.ac.astype(str) + ":" + v.cert_serial.astype(str)
    v.loc[v.cert_serial.isna(), "cert_serial_ac"] = None
    return v


NOTA_MR = {
    "mr_mesma_serie_na_zona": (
        "Média simples por seção, 3+ vizinhas: sensibilidade. O número publicado no dossiê "
        "(capítulo logs, logs.json, metadados.serie_mr.voto_estruturais_brasil) usa os mesmos "
        "grupos, ponderado pelos votos dos dois finalistas e com 5+ vizinhas."
    ),
    "mr_mesma_serie_na_zona_exterior": (
        "Exterior separado: a vizinhança é a cidade do consulado, onde quase todas as seções têm "
        "a mesma série; sensibilidade, não resultado."
    ),
}


def _mil(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def cobertura_vsc(v: pd.DataFrame, s: dict, n_bu: int) -> str:
    if s.get("banco") == "ausente":
        return "banco ausente"
    st = {str(k): int(x) for k, x in v.status.value_counts().items()}
    s["status"] = st
    det = ", ".join(f"{k} {_mil(x)}" for k, x in st.items())
    return f"{_mil(sum(st.values()))} seções tentadas ({det}) para {_mil(n_bu)} BUs"


def bloco_turno(m: pd.DataFrame, nome: str) -> dict:
    rep = {campo: rg.repeticao(m, campo) for campo in rg.CAMPOS}
    out = {"repeticao": rep}
    if "status" in m and (m.status == "ok").any():
        out["coerencia_vsc"], out["_falhas"] = rg.coerencia_vsc(m, DIAS[nome])
    else:
        out["_falhas"] = {}
    return out


def limpar(o):
    if isinstance(o, dict):
        return {k: limpar(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, list):
        return [limpar(x) for x in o]
    return o


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--banco-1t", type=Path, default=BANCO_1T)
    p.add_argument("--banco-2t", type=Path, default=BANCO_2T)
    p.add_argument("--banco-vsc", type=Path, default=BANCO_VSC)
    p.add_argument("--banco-logs", type=Path, default=BANCO_LOGS_2T)
    p.add_argument("--saida", type=Path, default=SAIDA)
    p.add_argument(
        "--ufs",
        help="restringe a análise a estas UFs (ex.: ac,ro), para rodadas parciais",
    )
    p.add_argument("--sem-cache", action="store_true")
    a = p.parse_args()

    b1 = preparar(ler_bu(a.banco_1t, "1t", not a.sem_cache))
    b2 = preparar(ler_bu(a.banco_2t, "2t"))
    v1, s1 = ler_vsc(a.banco_vsc, 1)
    v2, s2 = ler_vsc(a.banco_vsc, 2)
    lg, sl = ler_logs(a.banco_logs)
    if a.ufs:
        ufs = {u.strip().lower() for u in a.ufs.split(",")}
        b1, b2, v1, v2, lg = (x[x.uf.isin(ufs)] for x in (b1, b2, v1, v2, lg))
    v1, v2 = preparar_vsc(v1), preparar_vsc(v2)
    m1 = b1.merge(v1, on=CHAVE, how="left")
    m2 = b2.merge(v2, on=CHAVE, how="left").merge(lg, on=CHAVE, how="left")

    t2 = bloco_turno(m2, "2t")
    t1 = bloco_turno(m1, "1t")
    et, falhas_et = rg.entre_turnos_vsc(v1, v2, b1, b2)
    cl, falhas_log = rg.coerencia_logs(m2)

    marcas: dict[str, list] = {}
    for campo, r in t2["repeticao"].items():
        ch = r.get("_chaves_sem_explicacao") or []
        if ch:
            marcas[f"repetição sem explicação: {campo}"] = ch
    mr = t2["repeticao"].get("log_serie_mr_dia", {}).get("_chaves_mr_zona") or []
    if mr:
        # Exterior separado (26/10): a vizinhança lá é a cidade do consulado, onde quase
        # todas as seções têm a mesma série; misturar muda o sinal do Brasil. O número
        # publicado (ponderado pelos votos, 5+ vizinhas) sai de logs.json, capítulo logs.
        marcas["mr_mesma_serie_na_zona"] = [k for k in mr if str(k[0]).lower() != "zz"]
        marcas["mr_mesma_serie_na_zona_exterior"] = [
            k for k in mr if str(k[0]).lower() == "zz"
        ]
    for nome, ch in {**t2["_falhas"], **falhas_et, **falhas_log}.items():
        if ch:
            marcas[nome] = ch
    operacionais = {
        "mesma_urna_carga_nova",
        "reinicio_durante_votacao",
        "mr_mesma_serie_na_zona",
        "mr_mesma_serie_na_zona_exterior",
        "data_de_carga_do_log_diverge_do_bu",
    }
    todas = sorted(
        {k for nome, ch in marcas.items() if nome not in operacionais for k in ch}
    )
    voto = [rg.cruzar_voto(b2, b1, ch, nome) for nome, ch in marcas.items()]
    for v in voto:
        if v["grupo"] in NOTA_MR:
            v["nota"] = NOTA_MR[v["grupo"]]
    voto.append(
        rg.cruzar_voto(
            b2,
            b1,
            todas,
            "qualquer sinal fora da regra (exceto recarga entre turnos, reinício, MR repetida na zona e data de carga do log)",
        )
    )

    ok2 = int((v2.status == "ok").sum())
    completa = ok2 >= 0.99 * len(b2) and not a.ufs
    pend = []
    if a.ufs:
        pend.append(f"Rodada restrita às UFs {a.ufs}; rodar sem --ufs para o país.")
    elif not completa:
        pend.append(
            f"`.vsc` do 2º turno parcial: {_mil(ok2)} de {_mil(len(b2))} seções com BU; rodar de novo ao fim da coleta."
        )
    if int((v1.status == "ok").sum()) < 0.99 * len(b1):
        pend.append(
            "`.vsc` do 1º turno parcial: a comparação de certificado entre turnos cobre só as seções já lidas."
        )
    if "situacao" in cl:
        pend.append(
            "Campos do log do 2º turno (série da MR, códigos de carga e mídias do log, versão da aplicação, "
            "computador e data da mídia, zerésima) aguardam `data/outputs/logs_urnas_2t_2026.sqlite`; o hash "
            "do sistema não é extraído hoje pelo `parser.py` (META_URNA) e precisa de campo novo."
        )
    pend.append(
        "A assinatura de software (SEVIN, algoritmo 3 de 256 bits) não é verificada; só o resumo SHA-512 dela."
    )
    out = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rotulo": rg.ROTULO,
        "estado": (
            "completo"
            if completa
            else ("parcial (UFs: " + a.ufs + ")" if a.ufs else "parcial")
        ),
        "formato_vsc": FORMATO_VSC,
        "cobertura": {
            "bu_1t": len(b1),
            "bu_2t": len(b2),
            "vsc_2t": cobertura_vsc(v2, s2, len(b2)),
            "vsc_1t": cobertura_vsc(v1, s1, len(b1)),
            "vsc_detalhe": {"1t": s1, "2t": s2},
            "logs_2t": sl,
            "logs_2t_texto": (
                "banco ausente"
                if sl.get("banco") == "ausente"
                else f"{_mil(sl.get('secoes', 0))} seções, {_mil(sl.get('com_metadados_urna', 0))} com metadados da urna"
            ),
        },
        "explicacoes": rg.EXPLICACOES,
        "turnos": {"2t": t2, "1t": t1},
        "entre_turnos_vsc": et,
        "coerencia_logs": cl,
        "voto": voto,
        "pendencias": pend,
    }
    out = limpar(out)
    a.saida.mkdir(parents=True, exist_ok=True)
    (a.saida / "metadados.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1, default=str) + "\n",
        encoding="utf-8",
    )
    (a.saida / "metadados.md").write_text(markdown(out), encoding="utf-8")
    print(f"metadados: {out['estado']}; .vsc 2T {out['cobertura']['vsc_2t']}")


if __name__ == "__main__":
    main()
