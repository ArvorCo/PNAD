"""Sinal de recuo de carimbo nos logs, com evidência operacional minimizada."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict

from apuracao_2t_2026.encerramento_dados import deslocamento
from apuracao_logs.coleta import ler_compacto
from apuracao_logs.compacto import ler_para_analise
from apuracao_logs.cronologia import preparacao_anterior
from apuracao_logs.parser import segundos, textos_zip
from apuracao_logs.pleito import PLEITOS
from politize_se.transmissao import BANCO, ROOT, catalogo

P = PLEITOS[3221]
SAIDA = ROOT / "docs/assets/politize_se/relogios"
COLUNAS = ["secao", "recuos", "max_s", "ajustes", "contagem_confere", "status"]


def recuos(arquivos, off, primeiro, ultimo):
    out = []
    for indice, (nome, texto) in enumerate(arquivos):
        if preparacao_anterior(nome, texto, P.dia):
            continue
        anteriores, computou = {}, set()
        for linha in texto.splitlines():
            a = linha.split("\t")
            if len(a) != 6 or a[0][:10] not in P.dias:
                continue
            data, _, urna, app, msg, _ = a
            try:
                t = segundos(data, P.dias)
            except (ValueError, IndexError):
                continue
            ant = anteriores.get(urna)
            if ant and t < ant[0]:
                # Não exportar mensagens livres, identificadores de eleitor ou ordem de votos.
                fase = (
                    "antes_primeiro"
                    if max(t, ant[0]) < primeiro
                    else (
                        "depois_ultimo"
                        if min(t, ant[0]) > ultimo
                        else "intersecta_votacao"
                    )
                )
                out.append(
                    {
                        "arquivo_indice": indice + 1,
                        "anterior_s": ant[0] + off * 3600,
                        "seguinte_s": t + off * 3600,
                        "recuo_s": ant[0] - t,
                        "app_anterior": ant[1],
                        "app_seguinte": app,
                        "fase": fase,
                        "antes_computo_na_escrita": urna not in computou,
                        "data_anterior_informada": ant[2],
                    }
                )
            ajuste = re.match(
                r"Data e hora que foi digitada pelo operador: (\d{2}/\d{2}/\d{4})", msg
            )
            informada = (
                ajuste[1]
                if ajuste
                and ajuste[1][6:10] + ajuste[1][3:5] + ajuste[1][:2] < P.dia_ordem
                else None
            )
            anteriores[urna] = (t, app, informada)
            if msg == "O voto do eleitor foi computado":
                computou.add(urna)
    return out


def resumo(rows):
    ok = [r for r in rows if r[5] == "ok"]
    sinais = [r for r in ok if r[1] or r[3]]
    return {
        "secoes": len(rows),
        "cobertas": len(ok),
        "sinalizadas": len(sinais),
        "max_s": max((r[2] for r in ok), default=None),
        "recuos": sum(r[1] for r in ok),
        "ajustes": sum(r[3] for r in ok),
    }


def gerar():
    locais, ids = catalogo()
    linhas, detalhes = defaultdict(list), {}
    digest = hashlib.sha256()
    counts, fases = Counter(), Counter()
    registros = []
    with (
        sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True) as con,
        sqlite3.connect(f"file:{P.raw}?mode=ro", uri=True) as raw,
    ):
        con.execute("ATTACH DATABASE ? AS logs", (f"file:{P.metricas}?mode=ro",))
        query = """SELECT s.uf,s.mun,s.zona,s.secao,s.log_sha256,m.sha256,m.status,
            json_extract(m.resumo,'$.contagens.recuos_relogio'),
            json_extract(m.resumo,'$.contagens.recuo_max_s'),
            json_extract(m.resumo,'$.contagens.ajustes_relogio'),
            json_extract(m.resumo,'$.contagem_confere'),m.resumo
            FROM secao s LEFT JOIN logs.metricas m USING(uf,mun,zona,secao)
            WHERE upper(s.uf)!='ZZ' AND (s.nsp IS NULL OR s.nsp=0 OR s.nsp=s.secao)
            ORDER BY s.uf,s.mun,s.zona,s.secao"""
        for (
            uf,
            mun,
            z,
            s,
            esperado,
            sha,
            status,
            n,
            mx,
            aj,
            confere,
            txt,
        ) in con.execute(query):
            ident = ids.pop((uf.upper(), mun, z, s))
            estado = (
                "sem_log"
                if status != "ok"
                else "sem_vinculo" if not esperado or esperado != sha else "ok"
            )
            row = (
                [s, n or 0, mx or 0, aj or 0, bool(confere), estado]
                if estado == "ok"
                else [s, None, None, None, None, estado]
            )
            linhas[ident].append(row)
            digest.update(
                json.dumps(
                    [uf, mun, z, s, esperado, sha, row], separators=(",", ":")
                ).encode()
            )
            counts[estado] += 1
            if estado == "ok" and (n or aj):
                r = json.loads(txt)
                key = (uf, mun, z, s)
                pacote = ler_compacto(raw, key)
                if pacote:
                    assert pacote["sha256_zip"] == sha
                    arquivos, _ = ler_para_analise(pacote)
                else:
                    blob = raw.execute(
                        "SELECT zip FROM arquivos WHERE uf=? AND mun=? AND zona=? AND secao=?",
                        key,
                    ).fetchone()[0]
                    assert hashlib.sha256(blob).hexdigest() == sha
                    arquivos = textos_zip(blob)
                ev = recuos(
                    arquivos,
                    deslocamento(uf, mun),
                    r["primeiro_computo_s"],
                    r["ultimo_computo_s"],
                )
                assert len(ev) == (n or 0), key
                assert max((e["recuo_s"] for e in ev), default=0) == (mx or 0), key
                fases.update(e["fase"] for e in ev)
                dados = {
                    "local": ident,
                    "secao": s,
                    "recuos": n or 0,
                    "max_s": mx or 0,
                    "ajustes": aj or 0,
                    "contagem_confere": bool(confere),
                    "log_sha256": sha,
                    "eventos": ev,
                }
                detalhes[f"{ident}/{s}"] = dados
                registros.append({**locais[ident], **dados})
    assert not ids
    SAIDA.mkdir(parents=True, exist_ok=True)
    ufs = {}
    por_uf = defaultdict(dict)
    for lid, rows in linhas.items():
        por_uf[locais[lid]["uf"]][lid] = {"secoes": rows, "resumo": resumo(rows)}
    for uf, ls in sorted(por_uf.items()):
        d = {
            "formato": 1,
            "uf": uf,
            "colunas": COLUNAS,
            "locais": ls,
            "detalhes": {k: v for k, v in detalhes.items() if k.startswith(uf + "-")},
        }
        blob = gzip.compress(
            json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0
        )
        (SAIDA / f"{uf}.json.gz").write_bytes(blob)
        ufs[uf] = {
            "arquivo": f"{uf}.json.gz",
            "sha256": hashlib.sha256(blob).hexdigest(),
            "bytes": len(blob),
        }
    meta = {
        "formato": 1,
        "dia": "2026-10-25",
        "fuso": "Brasília",
        "criterio_existente": "relogio",
        "titulo": "Recuos de horário no log",
        "regra": "Carimbo retrocede dentro do mesmo arquivo e urna. Sinal já existente de conferência do arquivo; não soma outro ponto ao diagnóstico.",
        "limite": "Pode refletir relógio ou ordem de gravação. Não identifica causa nem alteração do voto. Fase é comparação de carimbos inconsistentes, não prova do instante real.",
        "fontes": [str(P.metricas.relative_to(ROOT)), str(P.raw.relative_to(ROOT))],
        "extrato_sha256": digest.hexdigest(),
        "cobertura": dict(counts),
        "secoes": sum(counts.values()),
        "sinalizadas": len(registros),
        "locais_sinalizados": len({r["local"] for r in registros}),
        "eventos_por_fase": dict(fases),
        "eventos_antes_computo_na_escrita": sum(
            e["antes_computo_na_escrita"] for r in registros for e in r["eventos"]
        ),
        "eventos_com_data_anterior_informada": sum(
            e["data_anterior_informada"] is not None
            for r in registros
            for e in r["eventos"]
        ),
        "sinalizadas_contagem_confere": sum(r["contagem_confere"] for r in registros),
        "ufs": ufs,
        "sinais": sorted(
            registros, key=lambda r: (-r["max_s"], r["local"], r["secao"])
        ),
    }
    (SAIDA / "indice.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
    )
    cols = [
        "uf",
        "municipio",
        "zona",
        "local",
        "nome",
        "secao",
        "recuos",
        "max_s",
        "ajustes",
        "contagem_confere",
        "log_sha256",
    ]
    with (SAIDA / "secoes.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=cols, extrasaction="ignore", lineterminator="\n"
        )
        w.writeheader()
        w.writerows(meta["sinais"])
    print(
        json.dumps(
            {
                k: meta[k]
                for k in [
                    "secoes",
                    "sinalizadas",
                    "locais_sinalizados",
                    "cobertura",
                    "eventos_por_fase",
                ]
            },
            ensure_ascii=False,
        )
    )
    return meta
