#!/usr/bin/env python3
"""Politize-se: dados por seção e por local de votação, 1º × 2º turno de 2026.

Lê, somente leitura, os boletins de urna dos dois turnos
(``apuracao/data/secoes_2026.sqlite`` e ``secoes_2t_2026.sqlite``, este possivelmente
ainda em coleta), a régua do 1º turno, os fragmentos do Politize (voto, local,
fiscalização, mudanças de local), os logs do 1º turno e o clima, e grava em
``docs/assets/politize_se/dados/``:

- ``zona/<UF>/<zona>.json``: uma linha por seção principal, os prédios da zona e os
  totais dos municípios da zona (o aplicativo abre só este arquivo para uma seção);
- ``mun/<UF>/<mun>.json``: um prédio por linha, com o link para o Politize-se (é o que
  o mapa do Brasil consome);
- ``indice.json``: cobertura por UF (seções com BU do 2º turno), zonas, municípios,
  modelos das frases, catálogos e fontes;
- ``cep/``: cópia do índice de CEP do Politize (CEP dos locais de votação).

Reexecutável: roda sobre a coleta parcial do 2º turno e marca a cobertura. Contrato em
``analysis/politize_se/CONTRATO.md``. Uso::

    python3 scripts/politize-se-build.py            # Brasil e exterior
    python3 scripts/politize-se-build.py --uf AC    # amostra (mescla no índice)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from apuracao_2t_2026 import secoes_ref
from apuracao_logs import familias
from politize_se import fontes, montagem, saida, textos, urna

ROOT = fontes.ROOT
LIMITE_HASH = 300 * 1024 * 1024


def _fonte(chave: str, caminho: Path, nota: str = "") -> dict[str, Any]:
    if not caminho.exists():
        return {
            "chave": chave,
            "caminho": str(caminho.relative_to(ROOT)),
            "existe": False,
        }
    st = caminho.stat()
    out: dict[str, Any] = {
        "chave": chave,
        "caminho": str(caminho.relative_to(ROOT)),
        "bytes": st.st_size if caminho.is_file() else None,
        "modificado_em": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(
            timespec="seconds"
        ),
    }
    if caminho.is_file() and st.st_size <= LIMITE_HASH:
        h = hashlib.sha256()
        with caminho.open("rb") as f:
            for bloco in iter(lambda: f.read(1 << 20), b""):
                h.update(bloco)
        out["sha256"] = h.hexdigest()
    elif caminho.is_file():
        out["sha256"] = None
        out["nota"] = (
            nota or "arquivo grande ou em escrita: registro por tamanho e data"
        )
    if nota and "nota" not in out:
        out["nota"] = nota
    return out


def contexto() -> montagem.Contexto:
    ref, _locais, _meta = secoes_ref.ler_regua(fontes.REGUA_1T)
    mun_ref = json.loads(fontes.REGUA_1T.read_text(encoding="utf-8"))["municipios"]
    med_mun, med_zona = secoes_ref.medianas_1t(ref)
    prev, _ = fontes.previsao_2t()
    regras = fontes.regras_fiscal()
    cat = {
        "mudanca": fontes.mudancas_indice()["categorias"],
        "log": familias.NOME_CURTO,
        "log_rotina": sorted(familias.ROTINA),
        "log_niveis": {k: v["nome"] for k, v in familias.NIVEIS_ATENCAO.items()},
        "fiscal": {k: v["nome"] for k, v in regras["niveis"].items()},
    }
    return montagem.Contexto(
        ref=ref,
        mun_ref=mun_ref,
        med_mun=med_mun,
        med_zona=med_zona,
        mapa_urnas=fontes.mapa_urnas_1t(),
        previsao=prev,
        catalogo=cat,
        observado=fontes.observado_2t()[0],
    )


def catalogos(ctx: montagem.Contexto) -> dict[str, Any]:
    regras = fontes.regras_fiscal()
    _, meta_prev = fontes.previsao_2t()
    return {
        "sinais": textos.SINAIS_NOME,
        "explicacoes": textos.EXPLICACAO_NOME,
        "urna": urna.SITUACOES,
        "fiscal_niveis": {
            k: {"nome": v["nome"], "frase": v["frase"]}
            for k, v in regras["niveis"].items()
        },
        "fiscal_criterios": {k: v["nome"] for k, v in regras["criterios"].items()},
        "log": familias.NOME_CURTO,
        "log_rotina": sorted(familias.ROTINA),
        "log_familias": {
            k: {"nome": v["nome"], "curto": v["curto"], "criterios": v["criterios"]}
            for k, v in familias.FAMILIAS.items()
        },
        "log_niveis": {str(k): v for k, v in familias.NIVEIS_ATENCAO.items()},
        "mudanca": ctx.catalogo["mudanca"],
        "modelos_urna": {
            "1": "urna da seção",
            "3": "urna de contingência",
            "4": "urna de reserva da seção",
            "6": "urna de reserva no encerramento",
        },
        "clima2": meta_prev,
        "clima2o": fontes.observado_2t()[1],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--uf", help="UFs separadas por vírgula (amostra; mescla no índice)"
    )
    args = ap.parse_args()
    t0 = time.time()
    todas = fontes.ufs_politize()
    ufs = [u.strip().upper() for u in args.uf.split(",")] if args.uf else todas
    gerado_em = datetime.now(timezone.utc).isoformat(timespec="seconds")
    ctx = contexto()
    print(f"contexto pronto em {time.time() - t0:.0f}s", flush=True)

    ind_arq = saida.SAIDA / "indice.json"
    antigo = json.loads(ind_arq.read_text(encoding="utf-8")) if ind_arq.exists() else {}
    cob = dict(antigo.get("cobertura", {}).get("ufs", {})) if args.uf else {}
    zonas = dict(antigo.get("zonas", {})) if args.uf else {}
    tot_uf = dict(antigo.get("ufs", {})) if args.uf else {}
    linhas_mun = (
        [x for x in antigo.get("municipios", {}).get("linhas", []) if x[0] not in ufs]
        if args.uf
        else []
    )
    pol_ind = fontes.politize_indice()
    pc = pol_ind["municipios"]["colunas"]
    coord = {
        (x[pc.index("uf")], x[pc.index("mun_tse")]): x
        for x in pol_ind["municipios"]["linhas"]
    }
    bytes_tot = {"zona": 0, "mun": 0}
    for uf in ufs:
        t1 = time.time()
        res = montagem.processar_uf(uf, ctx)
        b = saida.escrever_uf(res, gerado_em, list(textos.FRASES))
        for k in bytes_tot:
            bytes_tot[k] += b[k]
        t = res.totais
        cob[uf] = {
            "secoes": t["n_secoes"],
            "com_bu_2t": t["n_bu2"],
            "pct": round(100 * t["n_bu2"] / t["n_secoes"], 2) if t["n_secoes"] else 0.0,
        }
        zonas[uf] = sorted(res.secoes)
        tot_uf[uf] = saida.totais(t)
        for mun, m in sorted(res.municipios.items()):
            pc_row = coord.get((uf, mun))
            linhas_mun.append(
                [
                    uf,
                    mun,
                    m["nome"],
                    pc_row[pc.index("lat")] if pc_row else None,
                    pc_row[pc.index("lon")] if pc_row else None,
                    pc_row[pc.index("pais")] if pc_row else None,
                    pc_row[pc.index("nome_tse")] if pc_row else None,
                    sum(1 for p in res.locais.values() if p["mun_tse"] == mun),
                    m["n_secoes"],
                    m["n_bu2"],
                    m["aptos2"] or m["aptos1"],
                    m["fatia_f1"],
                    m["fatia_f2"],
                    f"mun/{uf}/{mun}.json",
                ]
            )
        print(
            f"{uf}: {t['n_secoes']} seções, {t['n_bu2']} com BU do 2º turno, "
            f"{len(res.locais)} locais, {time.time() - t1:.0f}s",
            flush=True,
        )
        del res

    # índice de CEP: o mesmo do Politize (CEP dos locais de votação)
    cep_dst = saida.SAIDA / "cep"
    if not args.uf or not cep_dst.exists():
        if cep_dst.exists():
            shutil.rmtree(cep_dst)
        shutil.copytree(fontes.POLITIZE / "cep", cep_dst)

    soma_s = sum(c["secoes"] for c in cob.values())
    soma_b = sum(c["com_bu_2t"] for c in cob.values())
    n_bu, n_pr = fontes.contar_2t()
    linhas_mun.sort(key=lambda x: (x[0], x[1]))
    indice = {
        "versao": saida.VERSAO,
        "gerado_em": gerado_em,
        "rotulo": textos.ROTULO,
        "rotulos": [
            "Leitura agregada por seção, como o TSE publica. O voto é secreto: nenhum número descreve uma pessoa.",
            textos.ROTULO,
            "A atipicidade pede explicação; a explicação provável vem antes de qualquer suspeita.",
        ],
        "cobertura": {
            "nacional": {
                "secoes": soma_s,
                "com_bu_2t": soma_b,
                "pct": round(100 * soma_b / soma_s, 2) if soma_s else 0.0,
                "banco_2t_bus": n_bu,
                "banco_2t_principais": n_pr,
                "coleta_completa": n_bu >= n_pr > 0,
            },
            "ufs": dict(sorted(cob.items())),
        },
        "logs_2t": {
            "disponivel": fontes.logs_2t_disponivel(),
            "nota": "Logs do 2º turno processados (regra 2: o aviso de problema ao desmontar a memória de resultado antes da zerésima fica fora do erro técnico, em erro_mr_pre_zeresima).",
        },
        "ufs": dict(sorted(tot_uf.items())),
        "zonas": dict(sorted(zonas.items())),
        "municipios": {
            "colunas": [
                "uf",
                "mun_tse",
                "nome",
                "lat",
                "lon",
                "pais",
                "nome_tse",
                "n_locais",
                "n_secoes",
                "n_bu2",
                "aptos",
                "fatia_f1",
                "fatia_f2",
                "arquivo",
            ],
            "linhas": linhas_mun,
        },
        "frases": textos.FRASES,
        "frases_codigos": list(textos.FRASES),
        "catalogos": catalogos(ctx),
        "fontes": [
            _fonte("boletins_1t", fontes.DB_1T),
            _fonte(
                "boletins_2t", fontes.DB_2T, "em coleta: registro por tamanho e data"
            ),
            _fonte("regua_1t", fontes.REGUA_1T),
            _fonte("politize_indice", fontes.POLITIZE / "indice.json"),
            _fonte("fiscal_regras", fontes.POLITIZE / "fiscal/regras.json"),
            _fonte("mudancas_indice", fontes.POLITIZE / "mudancas/indice.json"),
            _fonte("logs_1t_indice", fontes.LOGS_1T / "indice.json"),
            _fonte("logs_2t_indice", fontes.LOGS_2T / "indice.json"),
            _fonte(
                "logs_2t_metricas", fontes.LOGS_2T_DB, "registro por tamanho e data"
            ),
            _fonte("clima_previsao", fontes.CLIMA / "previsao.json"),
        ],
        "escopo": "Brasil e exterior" if not args.uf else ", ".join(sorted(cob)),
    }
    saida.gravar(saida.SAIDA / "indice.json", indice)
    print(
        f"pronto em {time.time() - t0:.0f}s: {soma_b} de {soma_s} seções com BU do 2º turno; "
        f"zona {bytes_tot['zona'] / 1e6:.1f} MB, mun {bytes_tot['mun'] / 1e6:.1f} MB",
        flush=True,
    )


if __name__ == "__main__":
    main()
