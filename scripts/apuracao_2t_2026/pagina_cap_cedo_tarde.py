"""Capítulo 5 do dossiê do 2º turno: o que entrou cedo e o que entrou tarde.

Abre pela régua que derruba a leitura da noite: a fatia de Flávio muda de um
decil de fechamento a outro, mas a mudança contra o 1º turno é quase a mesma em
todos. A diferença entre cedo e tarde é de composição, não de voto.
"""

from __future__ import annotations

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
from .pagina_fig_turnos_util import ESTILO, linhas_de, municipio, tabela_compacta

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


def render(d: Dados, cap: Capitulo) -> str:
    C = d.get(ARQ)
    checar(
        d,
        ARQ,
        ["decis_2t", "ultimos_50", "transicao_decil_1t_para_2t.matriz", "zonas.decis"],
    )
    L = d.get("linha_do_tempo.json")
    dec = C["decis_2t"]
    sw = [x["swing_h2h_flavio_pp"] for x in dec]
    zsw = [x["swing_h2h_flavio_pp"] for x in (C.get("zonas") or {}).get("decis", [])]
    d1, d10 = dec[0], dec[-1]
    antes, total = _antes_das_19(d)
    h = ESTILO + cabeca(
        cap,
        "Cedo ou tarde,<br><em>a mesma mudança.</em>",
        f"Nos dez grupos de municípios pela hora em que fecharam, Flávio perdeu entre {pp(max(sw))} e "
        f"{pp(min(sw))} contra o 1º turno. O que muda entre cedo e tarde é quem chega, não como vota.",
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
        f"{pct(max(x['h2h_flavio'] for x in dec))} no grupo mais favorável a ele. Quem lê só esse nível conclui que a "
        "contagem mudou de direção ao longo da noite.",
        "verificado",
    )
    h += p(
        "A segunda linha da figura desmente a conclusão. Nos mesmos municípios, o 1º turno desenha a mesma serra, e a "
        f"distância entre as duas linhas mal se mexe: a mudança fica entre {pp(max(sw))} e {pp(min(sw))}. Nas "
        f"{inteiro((C.get('zonas') or {}).get('n'))} zonas eleitorais, também em dez grupos, fica entre "
        f"{pp(max(zsw)) if zsw else 's/d'} e {pp(min(zsw)) if zsw else 's/d'}. Se o voto tardio fosse diferente, "
        "o último decil se afastaria dos outros na mudança, não só no nível.",
        "verificado",
    )
    h += F.fig_decis(C)
    h += p(
        f"O último decil reúne {inteiro(d10['aptos'])} eleitores e {d10.get('capitais', 's/d')} capitais; o primeiro, "
        f"{inteiro(d1['aptos'])} eleitores e nenhuma capital. A mediana de eleitorado vai de {inteiro(d1['aptos_mediana'])} "
        f"a {inteiro(d10['aptos_mediana'])}. Município grande tem mais seções, mais urnas para transmitir e mais lotes "
        "para totalizar: entra tarde. Município remoto depende de transmissão por satélite ou de deslocamento da mídia: "
        "também entra tarde. A hora de chegada classifica o tamanho e a geografia, não o eleitor.",
        "inferencia",
    )
    if d10["swing_h2h_flavio_pp"] < d1["swing_h2h_flavio_pp"]:
        h += nota(
            "contrario",
            f"A mudança não é perfeitamente plana. O 10º decil perdeu {pp(d10['swing_h2h_flavio_pp'])} contra "
            f"{pp(d1['swing_h2h_flavio_pp'])} do 1º: as capitais e os grandes municípios andaram um pouco mais para Lula. "
            "É o mesmo padrão do capítulo seguinte (Lula cresceu mais onde há mais eleitores), não um lote tardio "
            "com voto de outra natureza: a diferença entre o primeiro e o último decil é menor que um ponto.",
            "O desvio que existe.",
        )
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
        h += F.fig_ufs_vs_1t(L)
        h += p(
            f"No relógio, {tarde} das {len(ufs)} UFs completas na rodada terminaram a apuração mais tarde que no 1º turno, "
            "e isso foi lido como lentidão. A comparação honesta desconta os 120 minutos da prorrogação até 19h: no 1º turno "
            f"a votação terminou às 17h, no 2º às 19h. Descontados os 120 minutos, {antes_desc} das {len(ufs)} fecharam antes "
            "do que no 1º turno, com uma ou duas cédulas no lugar de seis. As urnas fecharam perto das 17h, quando a fila "
            "acabou; o que esperou até perto das 19h foi o recebimento dos boletins (capítulo Seção por seção).",
            "verificado",
        )
        h += F.fig_mapa_hora(L)
    pa = _ponte_alta(d)
    if pa:
        h += nota(
            "apuracao",
            f"Ponte Alta do Norte (SC), {pa['secoes']} seções e {inteiro(pa['aptos'])} eleitores, teve todas as seções "
            f"totalizadas às {pa['fechou_hhmm']}, antes do fim da votação prorrogada até 19h "
            f"(Flávio {pct(pa['pct_flavio'])}, Lula {pct(pa['pct_lula'])}). A análise por seção mostra que quase todas "
            "as urnas do país encerraram perto das 17h, quando acabou a fila, e que algumas transmitiram antes das 19h. "
            + (
                f"No total, só {inteiro(antes)} de {inteiro(total)} municípios "
                f"{'estava completo' if antes == 1 else 'estavam completos'} antes das 19h. "
            )
            + "Atipicidade pede explicação, não prova irregularidade: a pergunta é à Justiça Eleitoral, qual regra "
            "permitiu totalizar antes do novo horário de encerramento.",
            "Totalizado antes do fim da votação.",
        )
    u50 = C["ultimos_50"]
    te50 = sum(m["aptos"] for m in u50) or 1
    sw50 = sum(m["swing_h2h_flavio_pp"] * m["aptos"] for m in u50) / te50
    por_uf: dict[str, int] = {}
    for m in u50:
        por_uf[m["uf"]] = por_uf.get(m["uf"], 0) + 1
    top = sorted(por_uf.items(), key=lambda kv: -kv[1])[:4]
    h += p(
        f"Os {len(u50)} últimos municípios a fechar somam {inteiro(te50)} eleitores e vêm sobretudo de "
        + ", ".join(f"{uf} ({n})" for uf, n in top)
        + f". A mudança média deles contra o 1º turno, ponderada pelo eleitorado, é {pp(sw50)}, perto da média nacional; "
        f"o mais tardio, {municipio(u50[0]['nome'], u50[0]['uf'])}, completou às {u50[0]['fechou_hhmm']}.",
        "verificado",
    )
    h += _tabela_ultimos(C)
    h += TA.bloco_ordem(d.get("angulo_transporte.json"))
    h += limites(
        [
            "O minuto de fechamento é o da primeira versão gerada pelo TSE com todas as seções do município, não o da leitura pelo coletor.",
            "Decis por número de municípios, não por eleitorado: o último decil pesa vinte vezes o primeiro.",
            "Minutos dos dois turnos só se comparam descontando os 120 minutos da prorrogação.",
            "Mudança contra o 1º turno é agregada por município; não identifica troca de voto individual.",
            _ufs_abertas(d),
        ]
    )
    return h
