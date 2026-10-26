"""Capítulo 6 do dossiê do 2º turno: 1º turno × 2º turno, e 2026 × 2022.

Abre pelo número que contraria a expectativa da casa: a parte de Flávio entre os
dois finalistas caiu em todas as UFs. Depois, de onde vieram os votos novos de cada
um, onde Flávio perdeu votos absolutos e o que 2022 mostra por baixo do agregado.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import (
    Capitulo,
    Dados,
    cartao,
    checar,
    inteiro,
    limites,
    milhoes,
    nota,
    num,
    p,
    sinal_int,
)
from apuracao_2026.pagina_fig_base import FLAVIO, LULA, pct, pp

from . import pagina_fig_turnos as F
from . import pagina_texto_turnos as T
from .pagina_comum import cabeca
from .pagina_fig_turnos_util import ESTILO, municipio

ARQ1 = "comparacao_1t.json"
ARQ22 = "comparacao_2022.json"


def _regiao(lista: list[dict], nome: str) -> dict | None:
    return next(
        (x for x in lista if x.get("regiao") == nome or x.get("uf") == nome), None
    )


def _ufs_top(lista: list[dict], n: int = 3) -> str:
    cont: dict[str, int] = {}
    for m in lista:
        cont[m["uf"]] = cont.get(m["uf"], 0) + 1
    top = sorted(cont.items(), key=lambda kv: -kv[1])[:n]
    return ", ".join(f"{uf} ({k})" for uf, k in top)


def _abstencao_nas_ufs(C1: dict) -> str:
    ufs = set()
    for chave in ("flavio_maiores_perdas", "lula_maiores_perdas"):
        cont: dict[str, int] = {}
        for m in C1[chave]:
            cont[m["uf"]] = cont.get(m["uf"], 0) + 1
        ufs |= {uf for uf, _ in sorted(cont.items(), key=lambda kv: -kv[1])[:3]}
    delta = {u["uf"]: u["delta_abstencao_pp"] for u in C1["ufs"]}
    subiu = sorted(uf for uf in ufs if delta.get(uf, 0) > 0)
    if not subiu:
        return ""
    return (
        f" Em {', '.join(subiu)} a abstenção subiu contra o 1º turno (capítulo seguinte): menos gente votando tira "
        "votos dos dois."
    )


def _norte_arquivo(d: Dados) -> dict | None:
    P = d.get("presidente.json") or {}
    return next((x for x in P.get("regioes", []) if x.get("sigla") == "N"), None)


def _norte_2022(C22: dict | None) -> str:
    n22 = _regiao((C22 or {}).get("regioes", []), "Norte")
    if not n22:
        return ""
    return (
        f" Em 2022, nos mesmos municípios, Bolsonaro teve {pct(n22['r22_pct_bolsonaro'])} no Norte; "
        f"em 2026, Flávio ficou {pp(n22['flavio_menos_bolsonaro_pp'])} abaixo dele."
    )


def render(d: Dados, cap: Capitulo) -> str:
    C1 = d.get(ARQ1)
    C22 = d.get(ARQ22)
    checar(
        d,
        ARQ1,
        [
            "brasil",
            "ufs",
            "municipios",
            "dispersao_municipal",
            "flavio_perdeu_votos",
            "lula_perdeu_votos",
        ],
    )
    b = C1["brasil"]
    disp = C1["dispersao_municipal"]
    ufs = C1["ufs"]
    caiu_uf = sum(u["swing_h2h_flavio_pp"] < 0 for u in ufs)
    menor = max(ufs, key=lambda u: u["swing_h2h_flavio_pp"])
    maior = min(ufs, key=lambda u: u["swing_h2h_flavio_pp"])
    fp = C1["flavio_perdeu_votos"]["n"]
    lp = C1["lula_perdeu_votos"]["n"]
    pior_f = C1["flavio_maiores_perdas"][0]
    pior_l = C1["lula_maiores_perdas"][0]

    h = ESTILO + cabeca(
        cap,
        "Flávio caiu<br><em>em todas as UFs.</em>",
        f"A parte de Flávio entre os dois finalistas foi de {pct(b['t1_h2h_flavio'])} no 1º turno para "
        f"{pct(b['t2_h2h_flavio'])} no 2º ({pp(b['swing_h2h_flavio_pp'])}), nos mesmos "
        f"{inteiro(b['n_municipios'])} municípios. Caiu em {caiu_uf} das {len(ufs)} UFs.",
    )
    h += (
        '<div class="finding-grid">'
        + cartao(
            pp(b["swing_h2h_flavio_pp"]),
            "parte de Flávio entre os dois, 1º para 2º turno",
            FLAVIO,
        )
        + cartao(
            f"{inteiro(disp['n_swing_h2h_pro_lula'])} × {inteiro(disp['n_swing_h2h_pro_flavio'])}",
            "municípios em que a mudança favoreceu Lula × Flávio",
        )
        + cartao(
            pct(b["ganho_flavio_sobre_terceiros_pct"], 1),
            "votos novos de Flávio sobre o estoque de terceiros",
            FLAVIO,
        )
        + cartao(
            pct(b["ganho_lula_sobre_terceiros_pct"], 1),
            "votos novos de Lula sobre o estoque de terceiros",
            LULA,
        )
        + "</div>"
    )
    h += nota(
        "contrario",
        f"A casa esperava que a consolidação da direita levasse Flávio para cima no 2º turno. A urna não sustenta: a parte "
        f"dele entre os dois caiu em {caiu_uf} de {len(ufs)} UFs, da menor queda em {menor['nome_uf']} "
        f"({pp(menor['swing_h2h_flavio_pp'])}) à maior em {maior['nome_uf']} ({pp(maior['swing_h2h_flavio_pp'])}). "
        f"Entre os municípios, a mudança favoreceu Flávio em só {inteiro(disp['n_swing_h2h_pro_flavio'])} de "
        f"{inteiro(disp['n_swing_h2h_pro_flavio'] + disp['n_swing_h2h_pro_lula'])}.",
        "O achado que contraria a tese da casa.",
    )
    h += F.fig_barras_uf(C1, C22)
    h += p(
        "Um esclarecimento de régua. Sobre todos os válidos do 1º turno, que incluíam os terceiros, a parte de Flávio subiu "
        f"de {pct(b['t1_pct_flavio'])} para {pct(b['t2_pct_flavio'])} ({pp(b['delta_fatia_flavio_pp'])}), porque os terceiros "
        f"saíram da cédula; a de Lula subiu {pp(b['delta_fatia_lula_pp'])}. A régua que compara o confronto é a parte entre "
        "os dois finalistas, e por ela Flávio caiu.",
        "verificado",
    )
    h += F.fig_dispersao(C1)
    h += p(
        f"A dispersão mostra que a queda é um degrau quase uniforme. A mediana municipal da mudança é "
        f"{pp(disp['swing_h2h_flavio_pp']['mediana'])}, com desvio de {num(disp['swing_h2h_flavio_pp']['desvio'], 2)} ponto; "
        f"metade dos municípios fica entre {pp(disp['swing_h2h_flavio_pp']['p25'])} e {pp(disp['swing_h2h_flavio_pp']['p75'])}. "
        f"Ponderada pelo eleitorado, a média é {pp(disp['swing_h2h_flavio_pp']['media_ponderada'])}: os grandes municípios "
        "andaram um pouco mais para Lula.",
        "verificado",
    )
    h += "<h3>De onde vieram os votos novos</h3>"
    h += p(
        f"Entre os turnos, Flávio somou {milhoes(b['delta_votos_flavio'])} de votos ({sinal_int(b['delta_votos_flavio'])}) "
        f"e Lula {milhoes(b['delta_votos_lula'])} ({sinal_int(b['delta_votos_lula'])}). Os terceiros do 1º turno tinham "
        f"{milhoes(b['t1_terceiros'])} de votos nesses municípios. O ganho de Flávio equivale a "
        f"{pct(b['ganho_flavio_sobre_terceiros_pct'], 1)} desse estoque; o de Lula, a {pct(b['ganho_lula_sobre_terceiros_pct'], 1)}. "
        f"Lula ganhou mais votos do que havia em terceiros porque o comparecimento cresceu {milhoes(b['delta_comparecimento_votos'])} "
        "de eleitores e brancos e nulos caíram.",
        "verificado",
    )
    h += nota(
        "inferencia",
        "Voto ganho sobre o estoque de terceiros não identifica transferência individual. A conta mistura o eleitor de "
        "terceiro que escolheu um lado, o eleitor que faltou no 1º turno e veio no 2º, o que votou em branco e passou a "
        "escolher e o que trocou de lado. O agregado diz quanto cada um ganhou, não de quem.",
        "Como ler.",
    )
    h += "<h3>Onde cada um perdeu votos</h3>"
    h += p(
        f"Flávio perdeu votos absolutos em {inteiro(fp)} municípios e Lula em {inteiro(lp)}. A maior perda de Flávio foi em "
        f"{municipio(pior_f['nome'], pior_f['uf'])}, {sinal_int(pior_f['delta_votos_flavio'])} votos; a de Lula, em "
        f"{municipio(pior_l['nome'], pior_l['uf'])}, {sinal_int(pior_l['delta_votos_lula'])}. Entre as 30 maiores perdas "
        f"de cada um, as UFs mais frequentes são {_ufs_top(C1['flavio_maiores_perdas'])} (Flávio) e "
        f"{_ufs_top(C1['lula_maiores_perdas'])} (Lula)." + _abstencao_nas_ufs(C1),
        "verificado",
    )
    h += T.listas_votos(C1)
    h += F.fig_mapas_swing(d, C1)
    norte = _regiao(C1.get("regioes", []), "Norte")
    narq = _norte_arquivo(d)
    if norte and narq:
        h += nota(
            "verificado",
            f"No arquivo da região, o Norte terminou {num(narq['pct_lula'], 2)}% a {num(narq['pct_flavio'], 2)}%, com "
            f"{inteiro(abs(narq['margem_lula_votos']))} votos de diferença em {inteiro(narq['validos'])} válidos, a favor de "
            f"{'Lula' if narq['margem_lula_votos'] > 0 else 'Flávio'}. Nos municípios já completos da região, Flávio fica com "
            f"{pct(norte['t2_h2h_flavio'])}; a diferença está nas seções ainda por totalizar no Amazonas e no Pará. Flávio "
            f"somou o equivalente a {pct(norte['ganho_flavio_sobre_terceiros_pct'])} do estoque de terceiros do Norte; Lula, "
            f"{pct(norte['ganho_lula_sobre_terceiros_pct'])}.{_norte_2022(C22)}",
            "O Norte empatado.",
        )
    if C22:
        bb = C22["brasil"]
        dd = C22.get("dispersao_swing_lula_pp", {})
        vc = T.contagem_viradas(C22)
        acima = sorted(
            (
                u
                for u in C22["ufs"]
                if u["uf"] != "ZZ" and u["flavio_menos_bolsonaro_pp"] > 0
            ),
            key=lambda u: -u["flavio_menos_bolsonaro_pp"],
        )
        h += "<h3>Contra o 2º turno de 2022</h3>"
        h += p(
            f"Nos mesmos {inteiro(bb['n_municipios'])} municípios, sem o exterior, Lula foi de {pct(bb['r22_pct_lula'])} em 2022 "
            f"para {pct(bb['pct_lula'])} em 2026 ({pp(bb['swing_lula_pp'])}). O agregado esconde o mapa: Lula caiu contra 2022 "
            f"em {inteiro(C22.get('n_lula_caiu'))} municípios e subiu em {inteiro(C22.get('n_lula_subiu'))}. A mediana municipal "
            f"é {pp(dd.get('mediana'))} e a média ponderada pelo eleitorado é {pp(dd.get('media_ponderada'))}: mediana negativa "
            "com média positiva quer dizer que o avanço de Lula veio dos municípios grandes, e o recuo, dos pequenos.",
            "verificado",
        )
        h += F.fig_hist_2022(C22)
        if acima:
            h += nota(
                "contrario",
                f"Contra Bolsonaro em 2022, Flávio ficou acima em {len(acima)} UFs, com as maiores diferenças em "
                + ", ".join(
                    f"{u['uf']} ({pp(u['flavio_menos_bolsonaro_pp'])})"
                    for u in acima[:5]
                )
                + f". No território nacional, {inteiro(vc.get('br_l_f'))} municípios que votaram em Lula em 2022 votaram em "
                f"Flávio em 2026, contra {inteiro(vc.get('br_b_l'))} no sentido oposto (com as cidades do exterior, que o "
                f"arquivo trata como municípios, {inteiro(vc.get('tot_l_f'))} e {inteiro(vc.get('tot_b_l'))}). O avanço de "
                "Lula sobre 2022 veio dos grandes centros, não do território.",
                "O que o agregado de Lula não mostra.",
            )
        h += T.viraram(C22)
    h += limites(
        [
            "Base: municípios com o arquivo presidencial completo nos dois turnos; exterior fora.",
            "Parte entre os dois finalistas: no 1º turno, Flávio sobre Flávio mais Lula.",
            "2022 casa por código TSE do município; municípios sem par ficam fora.",
            "Votos ganhos não identificam de quem vieram; mudança agregada não é troca individual.",
            "O Norte empatado depende das últimas seções do Amazonas e do Pará na rodada usada.",
        ]
    )
    return h
