"""Agregados públicos por zona, cobertura, regras e CSV dos logs.

Nunca grava sequência de eleitores ou identificadores pessoais. A camada de logs
mantém sua cobertura própria e não soma pontos aos 12 critérios históricos.
"""

from __future__ import annotations

import bisect
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

from .coleta import BASE, DESTINO, ORIGEM, ROOT, url
from .complementos import LACUNAS, enderecos, registros_sa
from .complementos import carregar as carregar_complementos
from .conferencias import conferir
from .criterios import (
    CRITERIOS,
    MIN_PARES,
    MUDANCAS_REGRAS,
    VERSAO_REGRAS,
    avaliar,
    campos,
    referencias,
)
from .csv_processo import exportar as exportar_processos
from .parser import VERSAO
from .pleito import Pleito
from .processamento import METRICAS
from .processo import TIPOS
from .regras_processo import avaliar_processo
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

COLUNAS += [
    "processo_media",
    "processo_mediana",
    "processo_p90",
    "n_processo",
    "processo_excluidos",
    "cadencia_mediana",
    "cadencia_media",
    "n_cadencia",
    "rajada10_s",
    "janelas10",
    "processo_tipos",
    "referencias_processo",
    "referencia_cadencia",
    "escala_cadencia",
    "pares_cadencia",
    "referencia_rajada",
    "escala_rajada",
    "pares_rajada",
    "faixa_volume",
    "inspecoes",
    "inspecao_max",
    "retomadas_inatividade",
    "cancelamentos_habilitacao",
    "reinicios_sistema",
    "ocorrencias_operacionais",
    "processo_elegivel",
    "cadencia_elegivel",
    "retomadas_taxa",
    "cancelamentos_taxa",
    "referencia_retomadas",
    "referencia_cancelamentos",
    "escala_retomadas",
    "escala_cancelamentos",
    "pares_retomadas",
    "pares_cancelamentos",
    "preparacao_excluida",
    "bateria_eventos",
    "bateria_fase",
    "bateria_votacao",
    "bateria_simultaneas",
    "erro_mr_pre_zeresima",
]
JANELA_BATERIA_S = 60


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


def simultaneidade_bateria(linhas: list[dict], janela: int = JANELA_BATERIA_S):
    """Para cada seção com bateria durante a votação, quantas outras seções do mesmo
    município registraram o mesmo a até ``janela`` segundos de algum dos seus instantes
    (máximo entre os instantes). Grava ``bateria_simultaneas`` e remove os instantes
    da linha, que não são publicados."""
    por_mun = defaultdict(list)
    for i, row in enumerate(linhas):
        for t in row.pop("_bateria_votacao_s", None) or []:
            por_mun[(row["uf"], row["mun"])].append((t, i))
    maximo = defaultdict(int)
    for eventos in por_mun.values():
        eventos.sort()
        tempos = [t for t, _ in eventos]
        for t, i in eventos:
            a = bisect.bisect_left(tempos, t - janela)
            b = bisect.bisect_right(tempos, t + janela)
            outras = {j for _, j in eventos[a:b] if j != i}
            maximo[i] = max(maximo[i], len(outras))
    for i, row in enumerate(linhas):
        row["bateria_simultaneas"] = maximo[i] if row["bateria_votacao"] else None
    return linhas


def montar(pleito: Pleito | None = None) -> dict:
    """Sem ``pleito``, os padrões do 1º turno (constantes do módulo, como antes).
    Com ``pleito``, originais, BUs, métricas e saídas do turno correspondente;
    os casos conferidos à mão (``conferir``) são do 1º turno e só entram nele."""
    if pleito is None:
        DESTINO_, ORIGEM_, METRICAS_ = DESTINO, ORIGEM, METRICAS
        PUBLICO_, ANALISE_, LACUNAS_, BASE_ = PUBLICO, ANALISE, LACUNAS, BASE
    else:
        DESTINO_, ORIGEM_, METRICAS_ = pleito.raw, pleito.origem, pleito.metricas
        PUBLICO_, ANALISE_, LACUNAS_ = pleito.publico, pleito.analise, pleito.lacunas
        BASE_ = pleito.base
    raw = sqlite3.connect(f"file:{DESTINO_}?mode=ro", uri=True)
    raw.row_factory = sqlite3.Row
    catalogo = {
        tuple(r[k] for k in ("uf", "mun", "zona", "secao")): dict(r)
        for r in raw.execute("SELECT * FROM catalogo")
    }
    raw.close()
    complementos = {
        k: r for k, r in carregar_complementos(pleito).items() if k in catalogo
    }
    gravar(PUBLICO_ / "complementos.json", enderecos(pleito))
    catalogo_hash = hashlib.sha256()
    for key, cat in sorted(catalogo.items()):
        catalogo_hash.update(
            json.dumps(
                [key, cat], sort_keys=True, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            + b"\n"
        )
    con = sqlite3.connect(f"file:{METRICAS_}?mode=ro", uri=True)
    linhas, resumos = [], []
    hist = defaultdict(Counter)
    hist_processo, hist_cadencia = defaultdict(Counter), defaultdict(Counter)
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
            "erro_mr_pre_zeresima",
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
        row["processo_elegivel"] = bool(
            row["elegivel_tempo"] and row["n_processo"] >= max(30, 0.9 * row["n_tempo"])
        )
        row["cadencia_elegivel"] = bool(
            row["elegivel_tempo"] and row["n_cadencia"] >= 30
        )
        cobertura[uf]["processo_elegivel"] += row["processo_elegivel"]
        cobertura[uf]["cadencia_elegivel"] += row["cadencia_elegivel"]
        row["_bateria_votacao_s"] = r.get("bateria_votacao_segundos") or []
        row["url"] = url(catalogo[(uf, mun, z, s)], BASE_)
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
        p = r.get("processo_observado", {})
        if row["elegivel_tempo"] and row["n_processo"] >= max(30, 0.9 * row["n_tempo"]):
            hist_processo[pais].update(dict(p.get("histograma_processo", [])))
        if row["elegivel_tempo"] and row["n_cadencia"] >= 30:
            hist_cadencia[pais].update(dict(p.get("histograma_cadencia", [])))
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
                    "inspecoes",
                )
            }
        )
    con.close()
    # A coleta pode continuar enquanto este build lê as métricas. Conferir seu
    # estágio depois da leitura evita apresentar menos baixados do que analisados.
    raw = sqlite3.connect(f"file:{DESTINO_}?mode=ro", uri=True)
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
    src = sqlite3.connect(f"file:{ORIGEM_}?mode=ro", uri=True)
    tipos_bu = {
        tuple(r[:4]): r[4]
        for r in src.execute("SELECT uf,mun,zona,secao,tipo_arquivo FROM bu")
    }
    bus = set(tipos_bu)
    src.close()
    bus.update(complementos)
    situacoes = Counter()
    indisponiveis = defaultdict(list)
    arquivos_sa = registros_sa(pleito)
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
    simultaneidade_bateria(linhas)
    df = pd.DataFrame(linhas)
    sinais, refs = avaliar(df, resumos)
    valores_refs = {
        campo: ref[["ref", "escala", "n"]].to_numpy() for campo, ref in refs.items()
    }
    for i, row in enumerate(linhas):
        row["sinais"] = sinais[i]
        for campo, nome, pares in (
            ("voto_mediana", "voto", "pares_tempo"),
            ("cadencia_mediana", "cadencia", "pares_cadencia"),
            ("rajada10_s", "rajada", "pares_rajada"),
            ("retomadas_taxa", "retomadas", "pares_retomadas"),
            ("cancelamentos_taxa", "cancelamentos", "pares_cancelamentos"),
            ("habilitacao_mediana", "habilitacao", "pares_habilitacao"),
            ("biografica_pct", "biografica", "pares_biometria"),
            ("sem_biometria_pct", "sem_biometria", "pares_sem_biometria"),
        ):
            mediana, escala, quantidade = valores_refs[campo][i]
            row[f"referencia_{nome}"] = nulo(mediana)
            row[f"escala_{nome}"] = nulo(escala) if pd.notna(mediana) else None
            row[pares] = int(quantidade)
        row["referencias_processo"] = {
            t: {
                k: nulo(v)
                for k, v in zip(
                    ("mediana", "escala", "pares"),
                    valores_refs[f"processo_{t}"][i],
                    strict=True,
                )
            }
            for t in TIPOS
        }
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
            PUBLICO_ / "zona" / uf / f"{z}.json.gz",
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
    denominadores.update(avaliar_processo(df, referencias, 4)[2])
    em_votacao = sum(
        r["tempos_validos"] and r["contagens"].get("computados", 0) > 0 for r in resumos
    )
    denominadores["bateria_votacao_local"] = em_votacao
    denominadores["bateria_votacao_isolada"] = em_votacao
    denominadores["inspecao_prolongada"] = sum(
        r["tempos_validos"] and r["inspecoes"]["n"] > 0 for r in resumos
    )
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
        "versao_regras": VERSAO_REGRAS,
        "mudancas_regras": MUDANCAS_REGRAS,
        "processo": {p: duracoes(h) for p, h in hist_processo.items()},
        "cadencia": {p: duracoes(h) for p, h in hist_cadencia.items()},
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
            "referencia_processo": "UF × modelo × cargos × tipo de habilitação, ≥30 processos por tipo e ≥90% de cobertura de início inequívoco",
            "referencia_rajada": "Mínimo de 10 intervalos comparado a mínimos por UF × modelo × cargos × faixa de 100 intervalos (500+ juntos)",
            "escala": "1,4826 × mediana dos desvios absolutos em torno da mediana; piso 3 segundos, 1 ponto percentual na biometria ou 1 evento por 100 cômputos nas retomadas e cancelamentos",
            "cortes": "4 escalas na principal; sensibilidades com 3 e 5. A seção participa da referência empírica.",
            "limite": "Diagnósticos exploratórios e correlacionados. Não são testes de fraude, não identificam eleitores e não somam pontos aos 12 critérios históricos.",
        },
    }
    indice["concluido"] = (
        indice["concluido"] and not indice["complementos"]["pendentes_catalogo"]
    )
    if LACUNAS_.exists() and complementos:
        lacunas = json.loads(LACUNAS_.read_text())
        indice["lacunas"] = {k: v for k, v in lacunas.items() if k != "linhas"}
        gravar(PUBLICO_ / "lacunas.json", lacunas)
    indice["casos_conferidos"] = (
        conferir() if pleito is None or pleito.numero == 3220 else []
    )
    gravar(PUBLICO_ / "indice.json", indice)
    gravar(ANALISE_ / "resumo.json", indice)
    with (
        (PUBLICO_ / "secoes.csv.gz").open("wb") as out,
        gzip.GzipFile(filename="", mode="wb", fileobj=out, mtime=0) as gz,
        io.TextIOWrapper(gz, encoding="utf-8", newline="") as f,
    ):
        compactas = [
            k
            for k in COLUNAS
            if k
            not in (
                "processo_tipos",
                "referencias_processo",
                "ocorrencias_operacionais",
            )
        ]
        w = csv.DictWriter(f, fieldnames=["uf", "zona", *compactas])
        w.writeheader()
        for row in linhas:
            w.writerow(
                {
                    k: (
                        "|".join(row[k])
                        if isinstance(row.get(k), list)
                        and all(isinstance(x, str) for x in row[k])
                        else (
                            json.dumps(row[k], ensure_ascii=False, sort_keys=True)
                            if isinstance(row.get(k), (dict, list))
                            else nulo(row.get(k))
                        )
                    )
                    for k in w.fieldnames
                }
            )
    exportar_processos(linhas, PUBLICO_ / "processos_por_tipo.csv.gz")
    # Arquivo compacto privado para o build do mapa, só linhas sinalizadas.
    gravar(
        ANALISE_ / "sinalizadas.json",
        [{k: nulo(v) for k, v in r.items()} for r in linhas if r["sinais"]],
    )
    # Remove só a representação antiga deste mesmo conjunto gerado, após sucesso.
    for antigo in (PUBLICO_ / "zona").rglob("*.json"):
        antigo.unlink()
    return indice
