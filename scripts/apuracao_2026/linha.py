"""`linha_do_tempo.json`: versões do arquivo nacional, travamentos e latências.

Toda hora sai do banco em UTC e vai para o JSON também em Brasília (UTC-3). A
hora de geração (`gerado_em`) é o relógio do TSE; a de captura (`capturado_em`)
é o nosso, com leitura a cada 30 a 60 segundos nos arquivos de presidente.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from .banco import Banco
from .contexto import ELE_FED, ORDEM_2026, UFS, Arquivo, Contexto
from .dados import (
    BRT,
    brt,
    classificar_copias,
    colunar,
    deslocamento_horas,
    entradas_ab,
    estado_em,
    hora_brt,
    iso_z,
    lacunas_da_uniao,
    pct,
    percentil,
    travamentos,
    utc,
)

LIMIAR_MIN = 8.0
CORTE_MEIA_NOITE = "2026-10-05T03:00:00Z"
INICIO_CONTAGEM = "2026-10-04T20:21:00Z"
JANELA_DIVERGENCIA = ("2026-10-04T18:40", "2026-10-04T20:10")


def _votos_das_versoes(ctx: Contexto, arq: Arquivo) -> dict[int, dict[str, int]]:
    for snap in arq.versoes:
        ctx.banco.completar_totais(snap)
    brutos = ctx.banco.votos(arq.versoes)
    ctx.banco.esquecer_documentos()
    return {sid: ctx.agrupar(v) for sid, v in brutos.items()}


def versoes_nacionais(ctx: Contexto) -> dict[str, Any]:
    """Cada versão nova do arquivo nacional, com o lote que ela trouxe."""
    arq = ctx.nacional
    votos = _votos_das_versoes(ctx, arq)
    linhas = []
    anterior: dict[str, Any] | None = None
    for snap in arq.versoes:
        v = votos[snap["id"]]
        vv = snap["vv"] or 0
        linha: dict[str, Any] = {
            "snapshot_id": snap["id"],
            "gerado_em": snap["gerado_em"],
            "gerado_brt": brt(snap["gerado_em"]),
            "capturado_brt": brt(snap["capturado_em"]),
            "totalizacao_impressa": (
                f"{snap['dt']} {snap['ht']}" if snap["dt"] else None
            ),
            "idg": snap["idg"],
            "marcada_regressiva": bool(snap["regressivo"]),
            "st": snap["st"],
            "pst": pct(snap["st"], snap["ts"], 4),
            "comparecimento": snap["comparecimento"],
            "vv": vv,
            **{k: v[k] for k in ORDEM_2026},
            **{f"pct_{k}": pct(v[k], vv, 4) for k in ORDEM_2026},
        }
        if anterior is not None:
            d_vv = vv - anterior["vv"]
            linha["d_st"] = snap["st"] - anterior["st"]
            linha["d_vv"] = d_vv
            linha["minutos_desde_anterior"] = round(
                (utc(snap["gerado_em"]) - utc(anterior["gerado_em"])).total_seconds()
                / 60,
                2,
            )
            for k in ORDEM_2026:
                linha[f"d_{k}"] = v[k] - anterior[k]
            linha["lote_pct_flavio"] = (
                pct(linha["d_flavio"], d_vv, 4) if d_vv > 0 else None
            )
            linha["lote_pct_lula"] = pct(linha["d_lula"], d_vv, 4) if d_vv > 0 else None
        linhas.append(linha)
        anterior = linha
    colunas = list(dict.fromkeys(k for linha in linhas for k in linha))
    classes = classificar_copias(arq.snapshots)
    antigas = [sid for sid, c in classes if c == "antiga"]
    por_id = {s["id"]: s for s in arq.snapshots}
    return {
        "arquivo": arq.chave,
        "versoes": colunar(colunas, linhas),
        "n_versoes_genuinas": len(arq.versoes),
        "n_snapshots": len(arq.snapshots),
        "classes_snapshot": dict(Counter(c for _, c in classes)),
        "marcadas_regressivas": sum(1 for s in arq.snapshots if s["regressivo"]),
        "copias_antigas": [
            {
                "snapshot_id": sid,
                "capturado_brt": brt(por_id[sid]["capturado_em"]),
                "gerado_brt": brt(por_id[sid]["gerado_em"]),
                "st": por_id[sid]["st"],
            }
            for sid in antigas
        ],
    }


def _travamentos_do_arquivo(
    banco: Banco, arq: Arquivo, rotulo: str
) -> list[dict[str, Any]]:
    saida = []
    por_gerado = {s["gerado_em"]: s for s in arq.versoes}
    for lac in travamentos(arq.versoes, LIMIAR_MIN):
        ini, fim = por_gerado[lac["de"]], por_gerado[lac["ate"]]
        leituras = banco.leituras(arq.id, ini["capturado_em"], fim["capturado_em"])
        saida.append(
            {
                "arquivo": rotulo,
                **lac,
                "capturado_de_brt": brt(ini["capturado_em"]),
                "capturado_ate_brt": brt(fim["capturado_em"]),
                "leituras_no_intervalo": leituras,
            }
        )
    return saida


def travamentos_presidente(ctx: Contexto) -> dict[str, Any]:
    nacional = _travamentos_do_arquivo(ctx.banco, ctx.nacional, "BR")
    por_uf = []
    for uf in [*UFS, "zz"]:
        por_uf.extend(_travamentos_do_arquivo(ctx.banco, ctx.ufs[uf], uf.upper()))
    tempos = [
        s["gerado_em"]
        for arq in ctx.ufs.values()
        for s in arq.versoes
        if (s["st"] or 0) > 0
    ]
    fim_ufs = max(
        next(s["gerado_em"] for s in arq.versoes if s["st"] == s["ts"] and s["ts"])
        for arq in ctx.ufs.values()
    )
    uniao = [
        x for x in lacunas_da_uniao(tempos, LIMIAR_MIN) if utc(x["de"]) < utc(fim_ufs)
    ]
    for lac in uniao:
        lac["versoes_municipais_novas_no_intervalo"] = sum(
            1
            for arq in ctx.municipios.values()
            for s in arq.versoes
            if utc(lac["de"]) < utc(s["gerado_em"]) < utc(lac["ate"])
        )
        lac["st_nacional_no_inicio"] = _st_em(ctx.nacional, lac["de"])
    return {
        "limiar_min": LIMIAR_MIN,
        "regra": (
            "Lacuna maior que o limiar entre gerações consecutivas de versões novas do "
            "mesmo arquivo, com a contagem iniciada e incompleta. Leituras no intervalo "
            "vêm do log de requisições do coletor."
        ),
        "nacional": nacional,
        "ufs": sorted(por_uf, key=lambda x: (x["de"], x["arquivo"])),
        "todas_as_ufs_sem_versao_nova": uniao,
    }


def _st_em(arq: Arquivo, instante_iso: str) -> int | None:
    alvo = estado_em(arq.versoes, utc(instante_iso), "gerado_em")
    return None if alvo is None else alvo["st"]


def conclusao_ufs(ctx: Contexto) -> list[dict[str, Any]]:
    """Primeira versão com todas as seções, pela geração e pela regra do coletor."""
    saida = []
    for uf, arq in ctx.ufs.items():
        primeira = next(
            (s for s in arq.versoes if s["ts"] and s["st"] == s["ts"]), None
        )
        coletor = next(
            (
                s
                for s in arq.snapshots
                if not s["regressivo"] and s["ts"] and s["st"] == s["ts"]
            ),
            None,
        )
        saida.append(
            {
                "uf": uf.upper(),
                "gerado_brt": brt(primeira["gerado_em"]) if primeira else None,
                "capturado_brt": brt(primeira["capturado_em"]) if primeira else None,
                "totalizacao_impressa": (
                    f"{primeira['dt']} {primeira['ht']}"
                    if primeira and primeira["dt"]
                    else None
                ),
                "regra_do_coletor_gerado_brt": (
                    brt(coletor["gerado_em"]) if coletor else None
                ),
                "atraso_da_regra_do_coletor_min": (
                    round(
                        (
                            utc(coletor["gerado_em"]) - utc(primeira["gerado_em"])
                        ).total_seconds()
                        / 60,
                        2,
                    )
                    if primeira and coletor
                    else None
                ),
            }
        )
    return sorted(saida, key=lambda x: x["gerado_brt"] or "9")


def latencias(banco: Banco) -> dict[str, Any]:
    """Captura menos geração por hora de Brasília e nível, sem cópias antigas."""
    linhas = banco.linhas("""
        WITH s AS (
          SELECT s.arquivo_id, s.gerado_em, s.capturado_em,
            MAX(s.gerado_em) OVER (PARTITION BY s.arquivo_id ORDER BY s.id
              ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS anterior
          FROM snapshot s
        )
        SELECT a.nivel, a.eleicao_cd, a.cargo_cd, s.gerado_em,
          (julianday(s.capturado_em) - julianday(s.gerado_em)) * 86400.0 AS lat
        FROM s JOIN arquivo a ON a.id = s.arquivo_id
        WHERE a.tipo = 'u' AND s.gerado_em >= '2026-10-04T20:00'
          AND (s.anterior IS NULL OR s.gerado_em > s.anterior)
        """)
    grupos: dict[tuple[str, str], list[float]] = defaultdict(list)
    for linha in linhas:
        hora = hora_brt(linha["gerado_em"])
        pres = linha["eleicao_cd"] == ELE_FED and linha["cargo_cd"] == 1
        grupos[(hora, "todos")].append(linha["lat"])
        if pres:
            grupos[(hora, f"presidente_{linha['nivel']}")].append(linha["lat"])
    saida = [
        {
            "hora_brt": hora,
            "grupo": grupo,
            "n": len(vals),
            "p50_s": round(percentil(vals, 50) or 0, 1),
            "p95_s": round(percentil(vals, 95) or 0, 1),
            "max_s": round(max(vals), 1),
        }
        for (hora, grupo), vals in sorted(grupos.items())
    ]
    return {
        "nota": (
            "Segundos entre a geração do arquivo no TSE e a nossa leitura. Inclui o "
            "intervalo de sondagem do coletor (30 s no nacional, mais nos níveis "
            "menores), então é teto da demora de publicação, não medida dela."
        ),
        "por_hora": saida,
    }


def regressivos(banco: Banco) -> dict[str, Any]:
    """Eventos `idg_regressivo` por hora e o que eles eram pela hora de geração."""
    eventos = Counter(hora_brt(e["em"]) for e in banco.eventos("idg_regressivo"))
    linhas = banco.linhas("""
        WITH s AS (
          SELECT s.id, s.capturado_em, s.gerado_em, s.regressivo,
            MAX(s.gerado_em) OVER (PARTITION BY s.arquivo_id ORDER BY s.id
              ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS anterior
          FROM snapshot s
        )
        SELECT capturado_em, gerado_em, anterior FROM s WHERE regressivo = 1
        """)
    classes: dict[str, Counter] = defaultdict(Counter)
    total: Counter = Counter()
    for linha in linhas:
        if linha["anterior"] is None or linha["gerado_em"] > linha["anterior"]:
            classe = "mais_nova_que_todas_as_anteriores"
        elif linha["gerado_em"] == linha["anterior"]:
            classe = "mesma_geracao"
        else:
            classe = "copia_antiga"
        classes[hora_brt(linha["capturado_em"])][classe] += 1
        total[classe] += 1
    horas = sorted(set(eventos) | set(classes))
    return {
        "nota": (
            "O coletor marca como regressiva toda versão cujo contador idg caiu. Pela "
            "hora de geração do próprio TSE, a maioria das marcadas é mais nova que tudo "
            "o que veio antes no mesmo arquivo; só as do grupo copia_antiga são cópias "
            "velhas servidas pelo CDN."
        ),
        "total_eventos": sum(eventos.values()),
        "total_por_classe": dict(total),
        "por_hora": [
            {"hora_brt": h, "eventos": eventos.get(h, 0), **dict(classes.get(h, {}))}
            for h in horas
        ],
    }


def secoes_tardias(ctx: Contexto) -> dict[str, Any]:
    """Seções que chegaram depois da meia-noite de Brasília, por município."""
    corte = utc(CORTE_MEIA_NOITE)
    pares = []
    for arq in ctx.municipios.values():
        antes = [s for s in arq.versoes if utc(s["gerado_em"]) < corte]
        if not antes:
            continue
        pre, fim = antes[-1], arq.vigente
        if (fim["st"] or 0) > (pre["st"] or 0):
            pares.append((arq, pre, fim))
    snaps = [s for _, pre, fim in pares for s in (pre, fim)]
    for s in snaps:
        ctx.banco.completar_totais(s)
    votos = {sid: ctx.agrupar(v) for sid, v in ctx.banco.votos(snaps).items()}
    ctx.banco.esquecer_documentos()
    lista = []
    for arq, pre, fim in pares:
        cad = ctx.cadastro[arq.municipio_cd]
        dv = {k: votos[fim["id"]][k] - votos[pre["id"]][k] for k in ORDEM_2026}
        d_vv = (fim["vv"] or 0) - (pre["vv"] or 0)
        chegadas = [
            {"gerado_brt": brt(s["gerado_em"]), "st": s["st"]}
            for s in arq.versoes
            if utc(s["gerado_em"]) >= corte
        ]
        lista.append(
            {
                "cd_tse": arq.municipio_cd,
                "uf": (arq.uf or "").upper(),
                "nome": cad["nome"],
                "secoes": fim["st"] - pre["st"],
                "comparecimento": (fim["comparecimento"] or 0)
                - (pre["comparecimento"] or 0),
                "validos": d_vv,
                "votos": dv,
                "pct_lula": pct(dv["lula"], d_vv, 2),
                "pct_flavio": pct(dv["flavio"], d_vv, 2),
                "chegadas": chegadas,
            }
        )
    lista.sort(key=lambda x: (-x["secoes"], x["uf"], x["nome"]))
    soma = {k: sum(x["votos"][k] for x in lista) for k in ORDEM_2026}
    vv = sum(x["validos"] for x in lista)
    return {
        "corte_brt": brt(CORTE_MEIA_NOITE),
        "municipios": lista,
        "total": {
            "municipios": len(lista),
            "secoes": sum(x["secoes"] for x in lista),
            "validos": vv,
            "votos": soma,
            "pct_lula": pct(soma["lula"], vv, 2),
            "pct_flavio": pct(soma["flavio"], vv, 2),
        },
        "andamento_ab": _tardias_ab(ctx),
        "nacional_antes_do_corte": _st_em(ctx.nacional, CORTE_MEIA_NOITE),
        "nacional_final": ctx.nacional.vigente["st"],
    }


def _tardias_ab(ctx: Contexto) -> dict[str, Any]:
    """Conferência pelo andamento (-ab) de cada UF: seções após o corte por município."""
    corte = utc(CORTE_MEIA_NOITE)
    secoes = 0
    municipios: list[dict[str, Any]] = []
    for uf in [*UFS, "zz"]:
        versoes = ctx.banco.versoes_de(f"ab:{ELE_FED}::uf:{uf}::")
        antes = [s for s in versoes if utc(s["gerado_em"]) < corte]
        if not antes:
            continue
        pre = entradas_ab(ctx.banco.documento(antes[-1]["sha256"]))
        fim = entradas_ab(ctx.banco.documento(versoes[-1]["sha256"]))
        for cd, entrada in fim.items():
            if entrada["tpabr"] not in ("mu", "mun"):
                continue
            delta = (entrada["st"] or 0) - (pre.get(cd, {}).get("st") or 0)
            if delta > 0:
                secoes += delta
                municipios.append({"uf": uf.upper(), "cd_tse": cd, "secoes": delta})
        ctx.banco.esquecer_documentos()
    return {"secoes": secoes, "municipios": municipios}


def divergencia(ctx: Contexto) -> dict[str, Any]:
    """Soma das UFs contra o arquivo nacional e o andamento nacional, minuto a minuto."""
    ini = datetime.fromisoformat(JANELA_DIVERGENCIA[0]).replace(tzinfo=BRT)
    fim = datetime.fromisoformat(JANELA_DIVERGENCIA[1]).replace(tzinfo=BRT)
    ab_br = ctx.banco.versoes_de(f"ab:{ELE_FED}::br:::")
    ab_lido = []
    for s in ab_br:
        if utc(s["gerado_em"]) < ini.astimezone(timezone.utc) - timedelta(hours=1):
            continue
        if utc(s["gerado_em"]) > fim.astimezone(timezone.utc) + timedelta(minutes=5):
            continue
        entradas = entradas_ab(ctx.banco.documento(s["sha256"]))
        br = entradas.get("br", {})
        ab_lido.append(
            {**s, "st_br": br.get("st"), "dt_ht_br": f"{br.get('dt')} {br.get('ht')}"}
        )
    ctx.banco.esquecer_documentos()
    linhas = []
    instante = ini
    while instante <= fim:
        alvo = instante.astimezone(timezone.utc)
        linha: dict[str, Any] = {"hora_brt": instante.strftime("%H:%M")}
        for campo, sufixo in (("capturado_em", "visivel"), ("gerado_em", "gerado")):
            nac = estado_em(ctx.nacional.versoes, alvo, campo)
            soma = 0
            for arq in ctx.ufs.values():
                atual = estado_em(arq.versoes, alvo, campo)
                soma += (atual["st"] if atual else 0) or 0
            linha[f"nacional_st_{sufixo}"] = nac["st"] if nac else None
            linha[f"soma_ufs_st_{sufixo}"] = soma
            linha[f"diferenca_{sufixo}"] = soma - (nac["st"] if nac else 0)
            if nac:
                linha[f"nacional_gerado_brt_{sufixo}"] = brt(nac["gerado_em"])[11:]
        ab = estado_em(ab_lido, alvo, "capturado_em")
        linha["andamento_br_st_visivel"] = ab["st_br"] if ab else None
        linhas.append(linha)
        instante += timedelta(minutes=1)
    colunas = list(dict.fromkeys(k for linha in linhas for k in linha))
    pior = max(linhas, key=lambda x: x["diferenca_visivel"])
    impressas = sorted({x["dt_ht_br"] for x in ab_lido})
    total = ctx.nacional.vigente["ts"]
    return {
        "janela_brt": list(JANELA_DIVERGENCIA),
        "secoes_total": total,
        "nota": (
            "visivel: última versão nova capturada até o minuto; gerado: última versão "
            "gerada pelo TSE até o minuto. andamento_br é a entrada nacional do arquivo "
            "de andamento (-ab)."
        ),
        "andamento_br_totalizacao_impressa_na_janela": impressas,
        "minutos": colunar(colunas, linhas),
        "maior_diferenca_visivel": {
            "hora_brt": pior["hora_brt"],
            "secoes": pior["diferenca_visivel"],
            "pp_do_total": pct(pior["diferenca_visivel"], total, 2),
            "nacional_st": pior["nacional_st_visivel"],
            "soma_ufs_st": pior["soma_ufs_st_visivel"],
        },
    }


def marcos(ctx: Contexto) -> dict[str, Any]:
    nac = ctx.nacional.versoes
    primeira = next(s for s in nac if (s["st"] or 0) > 0)
    return {
        "primeira_versao_nacional_com_secoes_brt": brt(primeira["gerado_em"]),
        "totalizacao_impressa_nela": f"{primeira['dt']} {primeira['ht']}",
        "versao_final_nacional_brt": brt(nac[-1]["gerado_em"]),
        "secoes_final": nac[-1]["st"],
        "gerado_em": iso_z(datetime.now(timezone.utc)),
    }


def pausa_geral(banco: Banco) -> dict[str, Any]:
    """Lacunas sem nenhuma versão nova em nenhum arquivo de resultado (todos os cargos).

    Junta as horas de geração de todas as versões novas de todos os arquivos `-u`
    entre a primeira totalização e o fim da contagem, e conta as leituras que o
    coletor fez durante cada lacuna (prova de que ele estava lendo).
    """
    tempos = [
        r["gerado_em"]
        for r in banco.linhas(
            """
            WITH s AS (
              SELECT s.arquivo_id, s.gerado_em,
                MAX(s.gerado_em) OVER (PARTITION BY s.arquivo_id ORDER BY s.id
                  ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS anterior
              FROM snapshot s
            )
            SELECT DISTINCT s.gerado_em FROM s JOIN arquivo a ON a.id = s.arquivo_id
            WHERE a.tipo = 'u' AND s.gerado_em BETWEEN ? AND ?
              AND (s.anterior IS NULL OR s.gerado_em > s.anterior)
            """,
            (INICIO_CONTAGEM, CORTE_MEIA_NOITE),
        )
    ]
    lacunas = lacunas_da_uniao(tempos, LIMIAR_MIN)
    for lac in lacunas:
        leituras = banco.linhas(
            "SELECT classe, COUNT(*) AS n FROM fetch "
            "WHERE iniciado_em > ? AND iniciado_em < ? GROUP BY classe",
            (lac["de"], lac["ate"]),
        )
        lac["leituras_no_intervalo"] = {r["classe"]: r["n"] for r in leituras}
        andamento = banco.linhas(
            "SELECT DISTINCT a.chave, s.gerado_em FROM snapshot s "
            "JOIN arquivo a ON a.id = s.arquivo_id "
            "WHERE a.tipo = 'ab' AND s.gerado_em > ? AND s.gerado_em < ? ORDER BY s.gerado_em",
            (lac["de"], lac["ate"]),
        )
        lac["versoes_de_andamento_ab_no_intervalo"] = [
            {"arquivo": r["chave"], "gerado_brt": brt(r["gerado_em"])}
            for r in andamento
        ]
    return {
        "nota": (
            "Nenhum arquivo de resultado de nenhum cargo tem hora de geração dentro "
            "destas lacunas. As leituras com classe ok no intervalo trazem versões "
            "geradas antes dele."
        ),
        "janela": [INICIO_CONTAGEM, CORTE_MEIA_NOITE],
        "versoes_na_janela": len(tempos),
        "lacunas": lacunas,
    }


def fusos_por_uf(ctx: Contexto) -> dict[str, Any]:
    """Hora de totalização impressa menos hora de geração, nos arquivos municipais.

    Mediana, mínimo e máximo em minutos por UF, sobre as versões novas dos
    arquivos municipais de presidente. Perto de zero (um ou dois minutos de atraso
    de geração) quer dizer relógio de Brasília; perto de -60, relógio de UTC-4;
    perto de -120, UTC-5; perto de +60, UTC-2 (Fernando de Noronha).
    """
    por_uf: dict[str, list[float]] = defaultdict(list)
    for arq in ctx.municipios.values():
        for s in arq.versoes:
            desloc = deslocamento_horas(s["dt"], s["ht"], s["gerado_em"])
            if desloc is not None:
                por_uf[(arq.uf or "").upper()].append(desloc * 60)
    linhas = [
        {
            "uf": uf,
            "versoes": len(vals),
            "mediana_min": round(percentil(vals, 50) or 0, 1),
            "minimo_min": round(min(vals), 1),
            "maximo_min": round(max(vals), 1),
        }
        for uf, vals in sorted(por_uf.items())
    ]
    return {
        "nota": (
            "O TSE imprime a hora de totalização (dt e ht) no relógio local da unidade, "
            "e o banco a converte supondo Brasília. A coluna totalizado_em do banco fica "
            "deslocada nas UFs fora de UTC-3 e no exterior; a hora de geração (dg e hg) "
            "está sempre em Brasília."
        ),
        "por_uf": linhas,
    }


def _vigentes_marcadas(ctx: Contexto) -> dict[str, Any]:
    """Arquivos de presidente cuja versão vigente o coletor marcou como regressiva."""
    contagem: Counter = Counter()
    secoes: Counter = Counter()
    todos = [
        ctx.nacional,
        *ctx.ufs.values(),
        *ctx.municipios.values(),
        *ctx.zonas.values(),
    ]
    for arq in todos:
        vig = arq.vigente
        if not vig["regressivo"]:
            continue
        contagem[arq.nivel] += 1
        coletor = max(
            (s for s in arq.snapshots if not s["regressivo"]), key=lambda s: s["id"]
        )
        secoes[arq.nivel] += (vig["st"] or 0) - (coletor["st"] or 0)
    return {
        "arquivos_por_nivel": dict(contagem),
        "secoes_a_mais_na_versao_vigente": dict(secoes),
        "nota": (
            "Nesses arquivos a regra do coletor (última versão não marcada) fica numa "
            "versão anterior; a diferença de seções é o que ela deixa de fora."
        ),
    }


def montar(ctx: Contexto) -> dict[str, Any]:
    return {
        "marcos": marcos(ctx),
        "nacional": versoes_nacionais(ctx),
        "travamentos": travamentos_presidente(ctx),
        "pausa_geral": pausa_geral(ctx.banco),
        "conclusao_ufs": conclusao_ufs(ctx),
        "fuso_da_totalizacao": fusos_por_uf(ctx),
        "latencia": latencias(ctx.banco),
        "idg_regressivo": {
            **regressivos(ctx.banco),
            "presidente_versao_vigente_marcada_regressiva": _vigentes_marcadas(ctx),
        },
        "secoes_tardias": secoes_tardias(ctx),
        "divergencia_soma_ufs": divergencia(ctx),
    }
