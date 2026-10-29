"""Intervalo encerramento → recebimento do pacote do BU, por seção e local.

Leitura dos BUs e aux.json arquivados. Não infere instante de envio nem causa.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from statistics import median

from apuracao_2t_2026.encerramento_dados import BANCO, ROOT, deslocamento

SAIDA = ROOT / "docs/assets/politize_se/transmissao"
MAPA = ROOT / "docs/assets/politize_se_mapa/uf"
BASE = datetime(2026, 10, 25)
COLUNAS = [
    "secao",
    "enc_s",
    "emissao_s",
    "recebido_s",
    "intervalo_s",
    "situacao",
    "n_hashes",
    "tipo_arquivo",
]
LIMITES = [3600, 7200, 10800, 14400, 18000]
NOMES = ["Até 1h", ">1h a 2h", ">2h a 3h", ">3h a 4h", ">4h a 5h", "Mais de 5h"]
CORES = ["#d6e6df", "#a7c5ad", "#dcce7e", "#df9b4c", "#bd592e", "#802c35"]


def segundos(texto: str | None, offset: int = 0) -> int | None:
    if not texto:
        return None
    try:
        d = datetime.fromisoformat(texto)
    except ValueError:
        return None
    if d.tzinfo is not None:
        return None
    return int((d + timedelta(hours=offset) - BASE).total_seconds())


def nivel(s: float | None) -> int | None:
    if s is None or s < 0:
        return None
    return next((i for i, limite in enumerate(LIMITES) if s <= limite), len(LIMITES))


def classificar(r: dict) -> list:
    off = deslocamento(r["uf"], r["mun"])
    enc = segundos(r["encerramento"], off or 0)
    em = segundos(r["emissao"], off or 0)
    rec = segundos(r["dr_hr"])
    delta = rec - enc if enc is not None and rec is not None else None
    # O instante é o do pacote selecionado. Não chamar uma retransmissão de
    # primeira chegada quando houver versões; múltiplos pacotes ficam à parte.
    if off is None:
        status = "exterior"
    elif r["id_confere"] != 1 or r["pleito"] != 3221:
        status = "identidade"
    elif enc is None or rec is None or em is None:
        status = "sem_horario"
    elif not (0 <= enc < 86400) or rec < 0:
        status = "data"
    elif rec < enc:
        status = "recebimento_antes_encerramento"
    elif em < enc or rec < em:
        status = "ordem_emissao"
    elif r["n_hashes"] != 1:
        status = "multiplos_pacotes"
    else:
        status = "ok"
    return [r["secao"], enc, em, rec, delta, status, r["n_hashes"], r["tipo_arquivo"]]


def resumo(rows: list[list]) -> dict:
    validas = [r for r in rows if r[5] == "ok"]
    vals = sorted(r[4] for r in validas)
    pior = max(validas, key=lambda r: (r[4], -r[0])) if validas else None
    outras = [r[4] for r in validas if r is not pior]
    referencia = median(outras) if outras else None
    return {
        "secoes": len(rows),
        "cobertas": len(vals),
        "max_s": pior[4] if pior else None,
        "min_s": min(vals) if vals else None,
        "mediana_s": median(vals) if vals else None,
        "secao_max": pior[0] if pior else None,
        "enc_s": pior[1] if pior else None,
        "emissao_s": pior[2] if pior else None,
        "recebido_s": pior[3] if pior else None,
        "mediana_outras_s": referencia,
        "excesso_outras_s": pior[4] - referencia if referencia is not None else None,
        "acima_4h": sum(v > 14400 for v in vals),
        "acima_5h": sum(v > 18000 for v in vals),
        "motivos": dict(Counter(r[5] for r in rows if r[5] != "ok")),
    }


def quantis(vs: list[float]) -> dict:
    v = sorted(vs)

    def q(p):
        pos = (len(v) - 1) * p
        i = int(pos)
        return v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (pos - i)

    return (
        {
            k: q(p)
            for k, p in [
                ("p50", 0.5),
                ("p90", 0.9),
                ("p95", 0.95),
                ("p99", 0.99),
                ("max", 1),
            ]
        }
        if v
        else {}
    )


def catalogo() -> tuple[dict, dict]:
    locais, secoes = {}, {}
    for p in sorted(MAPA.glob("*.json")):
        uf = p.stem
        if uf == "ZZ":
            continue
        d = json.loads(p.read_text())
        municipios = {r[0]: r[1] for r in d["municipios"]["linhas"]}
        for row in d["locais"]["linhas"]:
            local = dict(zip(d["locais"]["colunas"], row, strict=True))
            _, mun, zona, _ = local["id"].split("-")
            locais[local["id"]] = {
                "id": local["id"],
                "uf": uf,
                "mun": mun,
                "zona": int(zona),
                "nome": local["nome"],
                "municipio": municipios[mun],
                "secoes_catalogo": local["n_secoes"],
            }
            for s in local["secoes"]:
                key = (uf, mun, int(zona), s)
                if key in secoes:
                    raise ValueError(f"Seção duplicada no mapa: {key}")
                secoes[key] = local["id"]
    return locais, secoes


def gerar() -> dict:
    locais, ids = catalogo()
    por_local = defaultdict(list)
    fonte = hashlib.sha256()
    auditoria = []
    with sqlite3.connect(f"file:{BANCO}?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA query_only=1")
        for raw in con.execute("""SELECT upper(b.uf) uf,b.mun,b.zona,b.secao,
            b.encerramento,b.emissao,b.id_confere,b.pleito,b.tipo_arquivo,
            s.dr_hr,s.n_hashes,s.hash,s.bu_sha256,s.aux_json
            FROM bu b JOIN secao s USING(uf,mun,zona,secao)
            WHERE upper(b.uf)!='ZZ' AND (s.nsp IS NULL OR s.nsp=0 OR s.nsp=s.secao)
            ORDER BY b.uf,b.mun,b.zona,b.secao"""):
            r = dict(raw)
            key = (r["uf"], r["mun"], r["zona"], r["secao"])
            ident = ids.pop(key)
            aux = json.loads(r["aux_json"])
            hs = [h for h in aux.get("hashes", []) if h.get("hash") == r["hash"]]
            if len(hs) != 1:
                raise ValueError(f"Pacote selecionado não identificado: {key}")
            h = hs[0]
            publicado = datetime.strptime(h["dr"] + " " + h["hr"], "%d/%m/%Y %H:%M:%S")
            if publicado != datetime.fromisoformat(r["dr_hr"]):
                raise ValueError(f"Carimbo da tabela difere do aux.json: {key}")
            fonte.update(
                (json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n").encode()
            )
            row = classificar(r)
            por_local[ident].append(row)
            if row[5] != "ok":
                auditoria.append(
                    {"local_id": ident, **dict(zip(COLUNAS, row, strict=True))}
                )
    if ids:
        raise ValueError(f"Seções do mapa sem BU: {len(ids)}")
    saidas = defaultdict(dict)
    tabela = []
    vals, preparos, posteriores = [], [], []
    for ident, local in locais.items():
        rows = sorted(por_local[ident])
        if len(rows) != local["secoes_catalogo"]:
            raise ValueError(f"Cobertura não recompõe o local: {ident}")
        s = resumo(rows)
        saidas[local["uf"]][ident] = {"resumo": s, "secoes": rows}
        tabela.append({**local, **s, "nivel": nivel(s["max_s"])})
        for r in rows:
            if r[5] == "ok":
                vals.append(r[4])
                preparos.append(r[2] - r[1])
                posteriores.append(r[3] - r[2])
    SAIDA.mkdir(parents=True, exist_ok=True)
    ufs = {}
    for uf, ls in sorted(saidas.items()):
        doc = {"formato": 1, "uf": uf, "colunas": COLUNAS, "locais": ls}
        raw = gzip.compress(
            json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode(), mtime=0
        )
        (SAIDA / f"{uf}.json.gz").write_bytes(raw)
        ufs[uf] = {
            "arquivo": f"{uf}.json.gz",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    ordenados = sorted(
        (r for r in tabela if r["max_s"] is not None),
        key=lambda r: (-r["max_s"], r["id"]),
    )
    isolados = sorted(
        (r for r in tabela if r["excesso_outras_s"] is not None),
        key=lambda r: (-r["excesso_outras_s"], r["id"]),
    )
    faixas = [
        {
            "nome": nome,
            "cor": cor,
            "secoes": sum(nivel(v) == i for v in vals),
            "locais": sum(r["nivel"] == i for r in tabela),
        }
        for i, (nome, cor) in enumerate(zip(NOMES, CORES, strict=True))
    ]
    meta = {
        "formato": 1,
        "dia": "2026-10-25",
        "fuso": "Brasília (UTC-3)",
        "campo": "aux.json: dr/hr do hash selecionado; encerramento e emissão do BU",
        "rotulo": "Intervalo encerramento → recebimento do pacote pelo TSE",
        "limite": "Não mede o início do envio, o tempo de rede ou a causa do intervalo. Pacotes posteriores podem ser retransmissões; não há múltiplos pacotes nesta base nacional.",
        "agregacao": "Maior intervalo de uma mesma seção em cada local. Mediana das demais seções do local como contraste; não subtrair horários de seções diferentes.",
        "atencao": "Acima de 4h: atenção; acima de 5h: muita atenção. Cortes exploratórios para priorizar documentos, sem validação como teste de irregularidade.",
        "fontes": [
            "https://www.tre-mg.jus.br/comunicacao/noticias/2026/Setembro/saiba-como-e-feita-a-transmissao-e-totalizacao-dos-resultados",
            "https://www.tse.jus.br/comunicacao/noticias/2026/Outubro/saiba-como-foi-a-totalizacao-dos-votos-no-1o-turno-das-eleicoes-2026",
        ],
        "banco": str(BANCO.relative_to(ROOT)),
        "extrato_sha256": fonte.hexdigest(),
        "ufs": ufs,
        "colunas": COLUNAS,
        "limites_s": LIMITES,
        "cores": CORES,
        "secoes": len(vals) + len(auditoria),
        "cobertas": len(vals),
        "locais": len(tabela),
        "locais_cobertos": len(ordenados),
        "quantis_s": quantis(vals),
        "preparo_quantis_s": quantis(preparos),
        "pos_emissao_quantis_s": quantis(posteriores),
        "faixas": faixas,
        "auditoria": auditoria,
        "principais": ordenados[:20],
        "maior_contraste_local": isolados[:20],
    }
    (SAIDA / "indice.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n"
    )
    campos = [k for k in tabela[0] if k != "motivos"]
    with (SAIDA / "locais.csv").open("w", newline="") as f:
        w = csv.DictWriter(
            f, fieldnames=campos, extrasaction="ignore", lineterminator="\n"
        )
        w.writeheader()
        w.writerows(sorted(tabela, key=lambda r: (-(r["max_s"] or 0), r["id"])))
    print(
        json.dumps(
            {
                k: meta[k]
                for k in [
                    "secoes",
                    "cobertas",
                    "locais",
                    "quantis_s",
                    "preparo_quantis_s",
                    "faixas",
                ]
            },
            ensure_ascii=False,
        )
    )
    return meta
