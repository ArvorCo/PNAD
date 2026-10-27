"""Capítulo 5 do dossiê do 2º turno: o que entrou cedo e o que entrou tarde.

Abre pela régua que derruba a leitura da noite: a fatia de Flávio muda de um
decil de fechamento a outro, mas a mudança contra o 1º turno varia pouco entre
eles. A diferença entre cedo e tarde é sobretudo de composição, e o pequeno
desvio que existe (o último decil anda um pouco mais para Lula) sai com o mesmo
destaque.
"""

from __future__ import annotations

import re

from apuracao_2026.pagina_comum import (
    Capitulo,
    Dados,
    cartao,
    checar,
    inteiro,
    limites,
    nota,
    num,
    p,
)
from apuracao_2026.pagina_fig_base import FLAVIO, pct, pp

from . import pagina_fig_cedo_tarde as F
from . import pagina_texto_angulo_transporte as TA
from .pagina_comum import cabeca
from .pagina_fig_turnos_util import (
    ESTILO,
    linhas_de,
    municipio,
    tabela_compacta,
    universo_municipios,
)

ARQ = "cedo_tarde.json"


def _ponte_alta(d: Dados) -> dict | None:
    P = d.get("presidente.json") or {}
    bloco = P.get("municipios")
    if not bloco:
        return None
    for m in linhas_de(bloco):
        if m["nome"] == "PONTE ALTA DO NORTE" and m["uf"] == "SC":
            return m
    return None


def _antes_das_19(d: Dados) -> tuple[int, int]:
    """Municípios (sem exterior) completos antes de 19:00 e total com minuto."""
    P = d.get("presidente.json") or {}
    bloco = P.get("municipios")
    if not bloco:
        return 0, 0
    ms = [
        m
        for m in linhas_de(bloco)
        if m["uf"] != "ZZ" and m.get("fechou_min") is not None
    ]
    return sum(m["fechou_min"] < 120 for m in ms), len(ms)


def prorrogacao(L: dict | None) -> dict:
    """Horário e janela da prorrogação, lidos de ``linha_do_tempo.json`` (``contexto_externo``).

    O banco não registra a decisão; o texto guardado no JSON diz que o horário vem
    do noticiário. Devolve ``frase`` (atribuída), ``hora`` e a janela ``de``/``ate``.
    """
    ctx = ((L or {}).get("contexto_externo") or {}).get("prorrogacao_stf") or ""
    hora = re.search(r"até (\d{1,2})h", ctx)
    janela = re.search(r"(\d{1,2}:\d{2}) a (\d{1,2}:\d{2})", ctx)
    quem = re.search(r"decisão do STF \(([^)]+)\)", ctx)
    h = f"{hora.group(1)}h" if hora else "19h"
    return {
        "hora": h,
        "de": janela.group(1) if janela else None,
        "ate": janela.group(2) if janela else None,
        "frase": (
            f"segundo o noticiário da noite, decisão do STF ({quem.group(1)}) prorrogou a votação até {h}"
            if quem
            else f"segundo o noticiário da noite, a votação foi prorrogada até {h}"
        ),
    }


def _capitais(C1: dict | None) -> tuple[int, float, float] | None:
    """Mudança da parte de Flávio entre os dois, capitais somadas contra os demais municípios."""
    if not C1 or "municipios" not in C1:
        return None
    ms = linhas_de(C1["municipios"])

    def sw(sel: list[dict]) -> float:
        f1, l1 = sum(m["t1_flavio"] for m in sel), sum(m["t1_lula"] for m in sel)
        f2, l2 = sum(m["t2_flavio"] for m in sel), sum(m["t2_lula"] for m in sel)
        return 100 * f2 / (f2 + l2) - 100 * f1 / (f1 + l1)

    caps = [m for m in ms if m.get("capital")]
    resto = [m for m in ms if not m.get("capital")]
    if not caps or not resto:
        return None
    return len(caps), sw(caps), sw(resto)


def _tabela_ultimos(C: dict) -> str:
    linhas = []
    for m in C["ultimos_50"]:
        linhas.append(
            [
                municipio(m["nome"], m["uf"]),
                inteiro(m["aptos"]),
                m["fechou_hhmm"],
                f"{num(m['pct_flavio'], 2)}",
                f"{num(m['pct_lula'], 2)}",
                f"{num(m['t1_h2h_flavio'], 2)}",
                pp(m["swing_h2h_flavio_pp"]),
            ]
        )
    return tabela_compacta(
        [
            "Município",
            "Eleitores",
            "Completo às",
            "Flávio, %",
            "Lula, %",
            "Flávio 1º turno, % entre os dois",
            "Mudança",
        ],
        linhas,
        "Os 50 últimos municípios a fechar no 2º turno (do mais tardio ao menos tardio). Fonte: cedo_tarde.json, ultimos_50.",
    )


def _ufs_abertas(d: Dados) -> str:
    """Limite sobre UFs com seção por totalizar, lido do presidente.json da rodada."""
    ufs = (d.get("presidente.json") or {}).get("ufs") or []
    abertas = sorted(u["uf"] for u in ufs if not u.get("completo"))
    if not abertas:
        return "Na rodada usada, todas as UFs já tinham todas as seções totalizadas."
    return f"Na rodada usada, {', '.join(abertas)} ainda tinham seção por totalizar."


def _desvio(d: Dados, d1: dict, d10: dict) -> str:
    """Achado contrário: o último decil anda um pouco mais para Lula, com o número do capítulo seguinte."""
    if d10["swing_h2h_flavio_pp"] >= d1["swing_h2h_flavio_pp"]:
        return ""
    C1 = d.get("comparacao_1t.json") or {}
    sw = (C1.get("dispersao_municipal") or {}).get("swing_h2h_flavio_pp") or {}
    cap = _capitais(C1)
    dif = d1["swing_h2h_flavio_pp"] - d10["swing_h2h_flavio_pp"]
    texto = (
        f"A mudança não é plana. O 10º decil, com {d10.get('capitais', 's/d')} capitais, perdeu "
        f"{pp(d10['swing_h2h_flavio_pp'])} contra {pp(d1['swing_h2h_flavio_pp'])} do 1º, {num(dif, 2)} pp a mais."
    )
    if cap:
        texto += f" Somadas, as {cap[0]} capitais mudaram {pp(cap[1])}, contra {pp(cap[2])} nos demais municípios."
    if sw.get("media_ponderada") is not None and sw.get("mediana") is not None:
        texto += (
            " No capítulo seguinte (1º turno × 2º turno), a mudança média por município, ponderada pelo "
            f"eleitorado, é {pp(sw['media_ponderada'])}, contra mediana de {pp(sw['mediana'])}: os grandes "
            "municípios andaram um pouco mais para Lula."
        )
    h = nota("contrario", texto, "O desvio que existe.")
    h += p(
        "É o padrão de tamanho, não um lote tardio com voto de outra natureza: a diferença entre o primeiro e o "
        f"último decil é de {num(dif, 2)} pp, menos de um ponto.",
        "inferencia",
    )
    return h


def render(d: Dados, cap: Capitulo) -> str:
    C = d.get(ARQ)
    checar(
        d,
        ARQ,
        ["decis_2t", "ultimos_50", "transicao_decil_1t_para_2t.matriz", "zonas.decis"],
    )
    if C is None:
        raise KeyError(ARQ)
    L = d.get("linha_do_tempo.json")
    pr = prorrogacao(L)
    dec = C["decis_2t"]
    sw = [x["swing_h2h_flavio_pp"] for x in dec]
    niv = [x["h2h_flavio"] for x in dec]
    amp_sw, amp_niv = max(sw) - min(sw), max(niv) - min(niv)
    zsw = [x["swing_h2h_flavio_pp"] for x in (C.get("zonas") or {}).get("decis", [])]
    d1, d10 = dec[0], dec[-1]
    pior = min(dec, key=lambda x: x["swing_h2h_flavio_pp"])
    antes, total = _antes_das_19(d)
    h = ESTILO + cabeca(
        cap,
        "Cedo ou tarde,<br><em>quase a mesma mudança.</em>",
        f"Nos dez grupos de municípios pela hora em que fecharam, Flávio perdeu entre {pp(max(sw))} e "
        f"{pp(min(sw))} contra o 1º turno. Entre cedo e tarde muda sobretudo quem chega; como se vota muda "
        f"pouco: {num(amp_sw, 2)} pp entre o grupo de menor e o de maior queda.",
    )
    h += (
        '<div class="finding-grid">'
        + cartao(
            pct(d1["h2h_flavio"]),
            f"Flávio no 1º decil (fechou {d1['fechou_hhmm_de']}–{d1['fechou_hhmm_ate']})",
            FLAVIO,
        )
        + cartao(
            pct(d10["h2h_flavio"]),
            f"Flávio no 10º decil (fechou {d10['fechou_hhmm_de']}–{d10['fechou_hhmm_ate']})",
            FLAVIO,
        )
        + cartao(
            f"{pp(max(sw))} a {pp(min(sw))}", "mudança contra o 1º turno, dez decis"
        )
        + cartao(
            num(C["spearman_tamanho_x_fechamento_2t"], 2),
            "correlação de postos entre tamanho e hora de fechamento",
        )
        + "</div>"
    )
    h += p(
        f"Os {inteiro(C['n_municipios'])} municípios foram ordenados pelo minuto em que a primeira versão do arquivo de "
        "presidente chegou com todas as seções e divididos em dez grupos de mesmo tamanho. A parte de Flávio entre os dois "
        f"vai de {pct(d1['h2h_flavio'])} no 1º decil a {pct(d10['h2h_flavio'])} no 10º, passando por "
        f"{pct(max(niv))} no grupo mais favorável a ele. Quem lê só esse nível conclui que a "
        "contagem mudou de direção ao longo da noite.",
        "verificado",
    )
    h += p(
        "Nos mesmos municípios, o 1º turno desenha a mesma serra. A distância entre as duas linhas varia pouco: "
        f"{num(amp_sw, 2)} pp de amplitude na mudança (de {pp(max(sw))} a {pp(min(sw))}) contra {num(amp_niv, 2)} pp "
        f"no nível. Nas {inteiro((C.get('zonas') or {}).get('n'))} zonas eleitorais, também em dez grupos, a mudança "
        f"fica entre {pp(max(zsw)) if zsw else 's/d'} e {pp(min(zsw)) if zsw else 's/d'}. A maior queda é a do "
        f"{pior['decil']}º decil, {num(d1['swing_h2h_flavio_pp'] - pior['swing_h2h_flavio_pp'], 2)} pp além da do 1º.",
        "verificado",
    )
    h += p(
        "A segunda linha da figura não sustenta a leitura de virada. Se o voto tardio fosse muito diferente, o último "
        "decil se afastaria dos outros na mudança, não só no nível; ele se afasta pouco"
        + (
            ", e na direção de Lula."
            if d10["swing_h2h_flavio_pp"] < d1["swing_h2h_flavio_pp"]
            else "."
        ),
        "inferencia",
    )
    h += p(
        universo_municipios(d.get("comparacao_1t.json"), d.get("comparacao_2022.json")),
        "verificado",
    )
    h += F.fig_decis(C)
    cap1 = d1.get("capitais")
    h += p(
        f"O último decil reúne {inteiro(d10['aptos'])} eleitores e {d10.get('capitais', 's/d')} capitais; o primeiro, "
        f"{inteiro(d1['aptos'])} eleitores e "
        + (
            "nenhuma capital"
            if cap1 == 0
            else f"{cap1 if cap1 is not None else 's/d'} capitais"
        )
        + f". A mediana de eleitorado vai de {inteiro(d1['aptos_mediana'])} a {inteiro(d10['aptos_mediana'])}, e a "
        f"correlação de postos entre tamanho e minuto de fechamento é {num(C['spearman_tamanho_x_fechamento_2t'], 2)}.",
        "verificado",
    )
    h += p(
        "Município grande tem mais seções, mais urnas para transmitir e mais lotes para totalizar: entra tarde. A hora "
        "de chegada classifica sobretudo o tamanho, não o eleitor.",
        "inferencia",
    )
    h += p(
        "Município pequeno que também entra tarde tem explicação provável na logística, como transmissão por satélite "
        "ou deslocamento da mídia; estes arquivos não registram o meio de transmissão.",
        "hipotese",
    )
    h += _desvio(d, d1, d10)
    h += F.fig_transicao(C)
    h += p(
        "A fila de chegada se repete em parte. Dos municípios que fecharam no primeiro décimo no 1º turno, "
        f"{inteiro(C['transicao_decil_1t_para_2t']['matriz'][0][0])} voltaram ao primeiro décimo no 2º. Tamanho e "
        "logística pesam nos dois turnos.",
        "verificado",
    )
    ufs = [
        u
        for u in (L or {}).get("conclusao_ufs", [])
        if u.get("uf") != "ZZ" and u.get("fechou_min") is not None
    ]
    if ufs:
        tarde = sum(u["atraso_vs_1t_min"] > 0 for u in ufs)
        antes_desc = sum(u["atraso_vs_1t_descontada_prorrogacao_min"] < 0 for u in ufs)
        G = d.get("governadores.json") or {}
        n_gov = len(G.get("ufs") or [])
        h += F.fig_ufs_vs_1t(L)
        h += p(
            f"No relógio, {tarde} das {len(ufs)} UFs completas na rodada terminaram a apuração mais tarde que no 1º turno, "
            "e isso foi lido como lentidão. A comparação justa desconta os 120 minutos da prorrogação: no 1º turno o "
            f"encerramento era às 17h; no 2º, {pr['frase']}. Descontados os 120 minutos, {antes_desc} das {len(ufs)} "
            "fecharam antes do que no 1º turno. As urnas fecharam perto das 17h; o que esperou até perto das "
            f"{pr['hora']} foi o recebimento dos boletins (capítulo Seção por seção).",
            "verificado",
        )
        h += p(
            "Parte da diferença pode vir da urna mais curta: no 2º turno, um voto (presidente) ou dois"
            + (f" (presidente e governador, em {n_gov} UFs)" if n_gov else "")
            + ", contra seis votos em cinco cargos no 1º turno. Estes arquivos não medem esse efeito.",
            "hipotese",
        )
        h += F.fig_mapa_hora(L)
    pa = _ponte_alta(d)
    if pa:
        janela = ""
        if pr["de"] and pr["ate"]:
            dentro = pr["de"] <= pa["fechou_hhmm"] <= pr["ate"]
            janela = (
                f"O minuto {'coincide com o' if dentro else 'fica fora do'} intervalo de {pr['de']} a {pr['ate']} em que, "
                "segundo o noticiário, a prorrogação foi anunciada (linha_do_tempo.json, contexto_externo). "
            )
        h += nota(
            "apuracao",
            f"Ponte Alta do Norte (SC), {pa['secoes']} seções e {inteiro(pa['aptos'])} eleitores, teve todas as seções "
            f"totalizadas às {pa['fechou_hhmm']}, antes das {pr['hora']}, o novo horário de encerramento informado pelo "
            f"noticiário (Flávio {pct(pa['pct_flavio'])}, Lula {pct(pa['pct_lula'])}). {janela}A análise por seção "
            f"mostra que quase todas as urnas do país encerraram perto das 17h e que algumas transmitiram antes das "
            f"{pr['hora']}. "
            + (
                f"No total, só {inteiro(antes)} de {inteiro(total)} municípios "
                f"{'estava completo' if antes == 1 else 'estavam completos'} antes das {pr['hora']}. "
            )
            + "Atipicidade pede explicação, não prova irregularidade: a pergunta à Justiça Eleitoral é se as seções do "
            "município encerraram e transmitiram antes de a prorrogação chegar a elas.",
            f"Completo antes das {pr['hora']}: pede explicação.",
        )
    u50 = C["ultimos_50"]
    te50 = sum(m["aptos"] for m in u50) or 1
    sw50 = sum(m["swing_h2h_flavio_pp"] * m["aptos"] for m in u50) / te50
    por_uf: dict[str, int] = {}
    for m in u50:
        por_uf[m["uf"]] = por_uf.get(m["uf"], 0) + 1
    top = sorted(por_uf.items(), key=lambda kv: -kv[1])[:4]
    tardios = [m for m in u50 if m["fechou_hhmm"] == u50[0]["fechou_hhmm"]]
    nomes = [municipio(m["nome"], m["uf"]) for m in tardios]
    quem = (
        f"o mais tardio, {nomes[0]}, completou"
        if len(nomes) == 1
        else f"os mais tardios, {', '.join(nomes[:-1])} e {nomes[-1]}, completaram"
    )
    h += p(
        f"Os {len(u50)} últimos municípios a fechar somam {inteiro(te50)} eleitores e vêm sobretudo de "
        + ", ".join(f"{uf} ({n})" for uf, n in top)
        + f". A mudança média deles contra o 1º turno, ponderada pelo eleitorado, é {pp(sw50)}, perto da média nacional; "
        f"{quem} às {u50[0]['fechou_hhmm']}.",
        "verificado",
    )
    h += _tabela_ultimos(C)
    h += TA.bloco_ordem(d.get("angulo_transporte.json"))
    h += limites(
        [
            "O minuto de fechamento é o da primeira versão gerada pelo TSE com todas as seções do município, não o da leitura pelo coletor.",
            "Decis por número de municípios, não por eleitorado: o último decil tem "
            f"{num(d10['aptos'] / d1['aptos'], 1)} vezes o eleitorado do primeiro.",
            "Minutos dos dois turnos só se comparam descontando os 120 minutos da prorrogação; o novo horário vem do "
            "noticiário (linha_do_tempo.json, contexto_externo), não do banco.",
            "Mudança contra o 1º turno é agregada por município; não identifica troca de voto individual.",
            _ufs_abertas(d),
        ]
    )
    return h
