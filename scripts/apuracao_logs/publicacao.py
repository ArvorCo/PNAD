"""Agregados públicos por zona, cobertura, regras e CSV dos logs.

Nunca grava sequência de eleitores ou identificadores pessoais. A camada de logs
mantém sua cobertura própria e não soma pontos aos 12 critérios históricos.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .coleta import DESTINO, ORIGEM, ROOT, url
from .complementos import LACUNAS, enderecos, registros_sa
from .complementos import carregar as carregar_complementos
from .conferencias import conferir
from .criterios import CRITERIOS, MIN_PARES, avaliar, campos
from .parser import VERSAO
from .processamento import METRICAS
from .resumo import SITUACOES, duracoes, situacao

PUBLICO = ROOT / "docs/assets/logs_urnas_2026"
ANALISE = ROOT / "analysis/apuracao_2026/logs_urnas"
COLUNAS = [
    "mun",
    "secao",
    "comparecimento",
    "cargos",
    "n_tempo",
    "voto_media",
    "voto_mediana",
    "voto_p90",
    "habilitacao_mediana",
    "biografica_pct",
    "sem_biometria_pct",
    "suspensoes",
    "reinicios",
    "erros",
    "intervalo_max",
    "elegivel_tempo",
    "elegivel_bio",
    "sinais",
    "sha256",
    "url",
    "referencia_voto",
    "referencia_biografica",
    "pares_tempo",
    "pares_biometria",
    "biometria_status",
    "hash_anterior_confere",
    "n_habilitacao",
    "computados",
    "ciclos_reconstruidos",
    "motivos_tempo",
    "erros_categoria",
    "erros_na_janela_votacao",
    "assinatura_sucesso_posterior",
    "assinatura_sem_sucesso_localizado",
    "assinatura_ordem_incerta",
    "recuo_max_s",
    "modelo",
    "modelo_comparavel",
    "den_bio",
    "biometricas_bu",
    "biograficas_bu",
    "sem_biometria_bu",
    "habilitacoes_log",
    "mensagens_criticas_alteradas",
    "linhas_invalidas",
    "bu_suplementar",
    "identificadores_excluidos",
    "referencia_habilitacao",
    "referencia_sem_biometria",
    "pares_habilitacao",
    "pares_sem_biometria",
    "escala_voto",
    "escala_habilitacao",
    "escala_biografica",
    "escala_sem_biometria",
]


def gravar(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    tmp = path.with_suffix(path.suffix + ".tmp")
    if path.suffix == ".gz":
        tmp.write_bytes(gzip.compress(texto.encode("utf-8"), mtime=0))
    else:
        tmp.write_text(texto, encoding="utf-8")
    tmp.replace(path)


def nulo(x):
    if isinstance(x, (list, dict, str)):
        return x
    return None if x is None or pd.isna(x) else x.item() if hasattr(x, "item") else x


def montar() -> dict:
    raw = sqlite3.connect(f"file:{DESTINO}?mode=ro", uri=True)
    raw.row_factory = sqlite3.Row
    catalogo = {
        tuple(r[k] for k in ("uf", "mun", "zona", "secao")): dict(r)
        for r in raw.execute("SELECT * FROM catalogo")
    }
    raw.close()
    complementos = {k: r for k, r in carregar_complementos().items() if k in catalogo}
    gravar(PUBLICO / "complementos.json", enderecos())
    catalogo_hash = hashlib.sha256()
    for key, cat in sorted(catalogo.items()):
        catalogo_hash.update(
            json.dumps(
                [key, cat], sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            + b"\n"
        )
    con = sqlite3.connect(f"file:{METRICAS}?mode=ro", uri=True)
    linhas, resumos = [], []
    hist = defaultdict(Counter)
    cargos = defaultdict(lambda: defaultdict(Counter))
    bio = defaultdict(Counter)
    operacao = Counter()
    cobertura = defaultdict(Counter)
    processados = {}
    for uf, mun, z, s, sha, st, txt in con.execute(
        "SELECT uf,mun,zona,secao,sha256,status,resumo FROM metricas WHERE versao=? ORDER BY uf,mun,zona,secao",
        (VERSAO,),
    ):
        cobertura[uf]["processados"] += 1
        processados[(uf, mun, z, s)] = st
        r = json.loads(txt)
        if st != "ok":
            cobertura[uf]["erro_leitura"] += 1
            continue
        cobertura[uf]["lidos"] += 1
        for k in (
            "erros",
            "falhas_assinatura_declaradas",
            "falhas_assinatura_com_sucesso_posterior",
            "falhas_assinatura_sem_sucesso_localizado",
            "falhas_assinatura_ordem_incerta",
        ):
            operacao[k] += r["contagens"].get(k, 0)
        janela = r["contagens"].get("erros_na_janela_votacao")
        if janela is not None:
            operacao["secoes_janela_classificavel"] += 1
            operacao["erros_na_janela_votacao"] += janela
            operacao["erros_fora_da_janela"] += r["contagens"].get("erros", 0) - janela
        cobertura[uf]["contagem_confere"] += r["contagem_confere"]
        cobertura[uf]["biometria_confere"] += bool(r["biometria_confere"])
        cobertura[uf]["biometria_ausente_bu"] += r["biometria_confere"] is None
        row = {
            "uf": uf.upper(),
            "mun": mun,
            "zona": z,
            "secao": s,
            "sha256": sha,
            **campos(r),
        }
        cobertura[uf]["tempo_elegivel"] += row["elegivel_tempo"]
        row["url"] = url(catalogo[(uf, mun, z, s)])
        suplemento = complementos.get((uf, mun, z, s))
        row["bu_suplementar"] = suplemento["fonte_bu"] if suplemento else None
        esperado = catalogo[(uf, mun, z, s)]["sha256_esperado"]
        row["hash_anterior_confere"] = sha == esperado if esperado else None
        linhas.append(row)
        pais = "exterior" if uf == "zz" else "brasil"
        if row["elegivel_bio"]:
            bio[pais].update(
                {
                    "secoes": 1,
                    "biometricas": r["bu"]["hab_biometria"],
                    "biograficas": r["bu"]["hab_ano_nascimento"],
                    "sem_biometria": r["bu"]["comp_sem_biometria"],
                    "comparecimento": r["bu"]["comparecimento"],
                }
            )
        if row["elegivel_tempo"]:
            hist[pais].update({int(k): n for k, n in r["histograma_voto"]})
            for numero, dist in r["tempo_por_cargos"].items():
                cargos[pais][numero].update(
                    {"ciclos": dist["n"], "soma_s": dist["n"] * dist["media"]}
                )
        # Guardar só campos necessários às regras, sem histogramas por seção.
        resumos.append(
            {
                k: r[k]
                for k in (
                    "contagens",
                    "tempos_validos",
                    "contagem_confere",
                    "biometria_confere",
                    "zeresima_antes",
                    "intervalo_computados",
                )
            }
        )
    con.close()
    # A coleta pode continuar enquanto este build lê as métricas. Conferir seu
    # estágio depois da leitura evita apresentar menos baixados do que analisados.
    raw = sqlite3.connect(f"file:{DESTINO}?mode=ro", uri=True)
    downloads = {
        tuple(r[:4]): r[4]
        for r in raw.execute("SELECT uf,mun,zona,secao,status FROM arquivos")
    }
    status = dict(
        raw.execute("SELECT status,COUNT(*) FROM arquivos GROUP BY status").fetchall()
    )
    status["hash_anterior_confere"] = raw.execute(
        "SELECT COUNT(*) FROM arquivos a JOIN catalogo c USING(uf,mun,zona,secao) "
        "WHERE a.status='ok' AND a.sha256=c.sha256_esperado"
    ).fetchone()[0]
    raw.close()
    src = sqlite3.connect(f"file:{ORIGEM}?mode=ro", uri=True)
    tipos_bu = {
        tuple(r[:4]): r[4]
        for r in src.execute("SELECT uf,mun,zona,secao,tipo_arquivo FROM bu")
    }
    bus = set(tipos_bu)
    src.close()
    bus.update(complementos)
    situacoes = Counter()
    indisponiveis = defaultdict(list)
    arquivos_sa = registros_sa()
    for key, cat in catalogo.items():
        cod = situacao(
            cat, downloads.get(key), processados.get(key), key in bus, tipos_bu.get(key)
        )
        situacoes[cod] += 1
        if cod != "lido":
            uf, mun, z, s = key
            indisponiveis[(uf.upper(), z)].append(
                {"mun": mun, "secao": s, "motivo": cod, "logsa": arquivos_sa.get(key)}
            )
    if not linhas:
        raise ValueError("Nenhum log válido processado nesta versão")
    df = pd.DataFrame(linhas)
    sinais, refs = avaliar(df, resumos)
    valores_refs = {
        campo: ref[["ref", "escala", "n"]].to_numpy() for campo, ref in refs.items()
    }
    for i, row in enumerate(linhas):
        row["sinais"] = sinais[i]
        for campo, nome, pares in (
            ("voto_mediana", "voto", "pares_tempo"),
            ("habilitacao_mediana", "habilitacao", "pares_habilitacao"),
            ("biografica_pct", "biografica", "pares_biometria"),
            ("sem_biometria_pct", "sem_biometria", "pares_sem_biometria"),
        ):
            mediana, escala, quantidade = valores_refs[campo][i]
            row[f"referencia_{nome}"] = nulo(mediana)
            row[f"escala_{nome}"] = nulo(escala) if pd.notna(mediana) else None
            row[pares] = int(quantidade)
        cobertura[row["uf"].lower()]["sinalizadas"] += bool(sinais[i])
    sens = {}
    for corte in (3, 4, 5):
        ss = sinais if corte == 4 else avaliar(df, resumos, corte)[0]
        cnt = Counter(k for s in ss for k in s)
        sens[str(corte)] = {"secoes": sum(bool(s) for s in ss), "criterios": dict(cnt)}
    contagem = Counter(k for s in sinais for k in s)
    por_zona = defaultdict(list)
    for row in linhas:
        por_zona[(row["uf"], row["zona"])].append([nulo(row.get(k)) for k in COLUNAS])
    for uf, z in por_zona.keys() | indisponiveis.keys():
        gravar(
            PUBLICO / "zona" / uf / f"{z}.json.gz",
            {
                "uf": uf,
                "zona": z,
                "colunas": COLUNAS,
                "linhas": por_zona[(uf, z)],
                "indisponiveis": indisponiveis[(uf, z)],
            },
        )
    for (uf, _, _, _), cat in catalogo.items():
        cobertura[uf]["catalogadas"] += 1
        cobertura[uf]["com_log_no_catalogo"] += cat["nome"] is not None
    totais = sum(cobertura.values(), Counter())
    denominadores = {
        "intervalo_longo": sum(
            r["tempos_validos"] and r["intervalo_computados"]["n"] > 0 for r in resumos
        ),
        "zeresima_ausente": sum(
            r["contagens"].get("computados", 0) > 0 for r in resumos
        ),
        "biometria_divergente": sum(
            r["biometria_confere"] is not None for r in resumos
        ),
        "tempo_rapido": int(
            (df.elegivel_tempo & refs["voto_mediana"].ref.notna()).sum()
        ),
        "tempo_lento": int(
            (df.elegivel_tempo & refs["voto_mediana"].ref.notna()).sum()
        ),
        "identificacao_lenta": int(
            (
                df.elegivel_tempo
                & (df.n_habilitacao >= 30)
                & refs["habilitacao_mediana"].ref.notna()
            ).sum()
        ),
        "biografica_alta": int(
            (
                df.elegivel_bio
                & df.modelo_comparavel
                & (df.den_bio >= 50)
                & refs["biografica_pct"].ref.notna()
            ).sum()
        ),
        "sem_biometria_alta": int(
            (
                df.elegivel_bio
                & df.modelo_comparavel
                & (df.comparecimento >= 50)
                & refs["sem_biometria_pct"].ref.notna()
            ).sum()
        ),
    }
    criterios = {
        k: {**v, "secoes": contagem[k], "avaliaveis": denominadores.get(k, len(linhas))}
        for k, v in CRITERIOS.items()
    }
    resumo_tempo = {
        pais: {
            **duracoes(h),
            "por_cargos": {
                k: {
                    "ciclos": v["ciclos"],
                    "media_s": round(v["soma_s"] / v["ciclos"], 3),
                }
                for k, v in sorted(cargos[pais].items())
                if v["ciclos"]
            },
        }
        for pais, h in hist.items()
    }
    indice = {
        "versao_parser": VERSAO,
        "formato_zonas": "json.gz",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "cobertura": dict(totais),
        "por_uf": {u.upper(): dict(v) for u, v in sorted(cobertura.items())},
        "coleta": dict(status),
        "complementos": {
            "secoes": len(complementos),
            "lidos": sum(processados.get(k) == "ok" for k in complementos),
            "pendentes_catalogo": sum(
                catalogo[k]["nome"] != r["nome"] for k, r in complementos.items()
            ),
        },
        "catalogo_sha256": catalogo_hash.hexdigest(),
        "situacoes": {
            k: {"nome": v, "secoes": situacoes[k]} for k, v in SITUACOES.items()
        },
        "concluido": not (
            situacoes["download_pendente"] or situacoes["processamento_pendente"]
        ),
        "integridade_codigo": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(__file__).parent.glob("*.py"))
        },
        "criterios": criterios,
        "sensibilidade": sens,
        "tempos": resumo_tempo,
        "biometria": {k: dict(v) for k, v in bio.items()},
        "operacao": dict(operacao),
        "zonas": {
            u: sorted(z for uu, z in por_zona if uu == u)
            for u in sorted({u for u, _ in por_zona})
        },
        "regra": {
            "pares_minimos": MIN_PARES,
            "referencia_tempo": "UF × modelo × número de confirmações de cargo no ciclo",
            "referencia_biometria": "UF × município × zona × modelo",
            "escala": "1,4826 × mediana dos desvios absolutos em torno da mediana; piso 3 segundos ou 1 ponto percentual",
            "cortes": "4 escalas na principal; sensibilidades com 3 e 5. A seção participa da referência empírica.",
            "limite": "Diagnósticos exploratórios e correlacionados. Não são testes de fraude, não identificam eleitores e não somam pontos aos 12 critérios históricos.",
        },
    }
    indice["concluido"] = (
        indice["concluido"] and not indice["complementos"]["pendentes_catalogo"]
    )
    if LACUNAS.exists() and complementos:
        lacunas = json.loads(LACUNAS.read_text())
        indice["lacunas"] = {k: v for k, v in lacunas.items() if k != "linhas"}
        gravar(PUBLICO / "lacunas.json", lacunas)
    indice["casos_conferidos"] = conferir()
    gravar(PUBLICO / "indice.json", indice)
    gravar(ANALISE / "resumo.json", indice)
    with (
        (PUBLICO / "secoes.csv.gz").open("wb") as out,
        gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as gz,
        io.TextIOWrapper(gz, encoding="utf-8", newline="") as f,
    ):
        w = csv.DictWriter(f, fieldnames=["uf", "zona", *COLUNAS])
        w.writeheader()
        for row in linhas:
            w.writerow(
                {
                    k: (
                        "|".join(row[k])
                        if isinstance(row.get(k), list)
                        else (
                            json.dumps(row[k], ensure_ascii=False, sort_keys=True)
                            if isinstance(row.get(k), dict)
                            else nulo(row.get(k))
                        )
                    )
                    for k in w.fieldnames
                }
            )
    # Arquivo compacto privado para o build do mapa, só linhas sinalizadas.
    gravar(
        ANALISE / "sinalizadas.json",
        [{k: nulo(v) for k, v in r.items()} for r in linhas if r["sinais"]],
    )
    # Remove só a representação antiga deste mesmo conjunto gerado, após sucesso.
    for antigo in (PUBLICO / "zona").rglob("*.json"):
        antigo.unlink()
    return indice
