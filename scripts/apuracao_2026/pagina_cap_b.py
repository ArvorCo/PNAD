"""Capítulos 06 a 09 do dossiê da apuração: Câmara, Senado, assembleias e governadores."""

from __future__ import annotations

from html import escape

from senado_2026.pagina import hemiciclo as HEMI81

from . import pagina_comparacao as CMP
from . import pagina_figuras as F
from . import pagina_texto_b as T
from .pagina_comum import (
    CAMPOS,
    COR_CAMPO,
    INK,
    NOME_UF,
    ROTULO_CAMPO,
    Capitulo,
    Dados,
    bloco_pendente,
    checar,
    cor_campo,
    figura,
    inteiro,
    nome_proprio,
    num,
    secao,
    sinal,
    tabela,
)


def campo_rot(c: str | None) -> str:
    return ROTULO_CAMPO.get(c or "indefinido", c or "")


# ------------------------------------------------------------------ 06


def r_camara(d: Dados, cap: Capitulo) -> str:
    C = d.get("camara.json")
    checar(
        d,
        "camara.json",
        [
            "por_campo",
            "blocos",
            "por_partido",
            "votos_por_campo_pct",
            "deputados_mais_votados",
        ],
    )
    b = C["blocos"]
    h = secao(
        cap,
        f"Câmara: {b['direita + centro-direita']} cadeiras<br><em>para direita e centro-direita.</em>",
        f"PL {C['por_partido'].get('PL', 0)}, PT {C['por_partido'].get('PT', 0)}. O bloco passa da maioria e não chega aos três quintos.",
    )
    h += T.camara(C)
    n = C["vagas_total"]
    blocos = [(COR_CAMPO[c], C["por_campo"].get(c, 0), ROTULO_CAMPO[c]) for c in CAMPOS]
    if C["por_campo"].get("indefinido"):
        blocos.append(
            (COR_CAMPO["indefinido"], C["por_campo"]["indefinido"], "Indefinido")
        )
    desc = (
        "Hemiciclo de 513 cadeiras por campo, da esquerda para a direita: "
        + "; ".join(f"{r} {q}" for _, q, r in blocos)
    )
    hemi = F.hemiciclo(
        blocos, "Câmara dos Deputados de 2027 por campo", desc, largura=760
    )
    leg = "".join(
        f'<li><span class="sw" style="background:{cor}"></span>{rot}: <strong>{q}</strong></li>'
        for cor, q, rot in blocos
    )
    h += (
        f'<figure id="fig-hemiciclo-camara"><div class="chart-fit">{hemi}</div>'
        f'<ul class="legenda-mapa">{leg}</ul>'
        f"<figcaption>Cada ponto é uma cadeira. Maioria simples: {T.maioria(n)}; três quintos: {T.tres_quintos(n)}. "
        "Campo é classificação editorial da casa por partido, com exceções por candidatura.</figcaption></figure>"
    )
    vp = C.get("votos_por_partido", [])
    campo_partido = {x["partido"]: x.get("campo") for x in vp}
    partidos = sorted(C["por_partido"].items(), key=lambda kv: -kv[1])[:14]
    h += figura(
        F.barras_h(
            [
                {
                    "rotulo": k,
                    "valor": v,
                    "cor": cor_campo(campo_partido.get(k)),
                    "texto": str(v),
                }
                for k, v in partidos
            ],
            "Cadeiras por partido",
            "Barras horizontais com as cadeiras das 14 maiores bancadas, na cor do campo do partido.",
            largura=720,
            rotulo_w=150,
            passo=28,
        ),
        "As 14 maiores bancadas, na cor do campo.",
        larga=False,
    )
    cp, vpp = C["por_campo"], C["votos_por_campo_pct"]
    h += figura(
        F.empilhadas(
            [
                (
                    "Votos",
                    [(vpp.get(c, 0), COR_CAMPO[c], ROTULO_CAMPO[c]) for c in CAMPOS],
                    "% dos votos",
                ),
                (
                    "Cadeiras",
                    [(cp.get(c, 0), COR_CAMPO[c], ROTULO_CAMPO[c]) for c in CAMPOS],
                    f"{n} cadeiras",
                ),
            ],
            "Votos e cadeiras por campo",
            "Duas barras empilhadas: a parcela dos votos de partido por campo e a parcela das cadeiras por campo.",
            rotulo_w=100,
            direita_w=120,
            marcas=[(T.maioria(n) / n, "maioria"), (T.tres_quintos(n) / n, "3/5")],
        ),
        f"Votos: nominais e de legenda somados nas 27 UFs, em %. Cadeiras: número. As marcas tracejadas contam da esquerda: maioria ({T.maioria(n)}) e três quintos ({T.tres_quintos(n)}).",
    )
    dep = C["deputados_mais_votados"][:15]
    h += tabela(
        ["Deputado", "UF", "Partido", "Campo", "Votos", "% da UF"],
        [
            [
                nome_proprio(x["nome"]),
                x["uf"],
                escape(x["partido"]),
                campo_rot(x.get("campo")),
                inteiro(x["votos"]),
                num(x["pct_na_uf"], 2),
            ]
            for x in dep
        ],
        "Os 15 deputados federais mais votados do país.",
    )
    h += CMP.camara(d)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 07


def r_senado(d: Dados, cap: Capitulo) -> str:
    S = d.get("senado.json")
    checar(
        d,
        "senado.json",
        [
            "senado_2027.por_bloco",
            "senado_2027.continuam_por_campo",
            "senado_2027.novos_por_campo",
            "eleitos_2026",
            "disputas",
        ],
    )
    s = S["senado_2027"]
    h = secao(
        cap,
        f"Senado de 2027:<br><em>{s['por_bloco']['direita + centro-direita']} de {s['total']}.</em>",
        f"Direita e centro-direita passam dos três quintos. O PL terá {s['por_partido'].get('PL', 0)} senadores.",
    )
    h += T.senado(S)
    cont, novos = s["continuam_por_campo"], s["novos_por_campo"]
    blocos = [
        {
            "cor": COR_CAMPO[c],
            "continuam": cont.get(c, 0),
            "novos": novos.get(c, 0),
            "rotulo": ROTULO_CAMPO[c],
        }
        for c in [*CAMPOS, "indefinido"]
        if cont.get(c, 0) or novos.get(c, 0)
    ]
    desc = "Hemiciclo de 81 cadeiras por campo, da esquerda para a direita: " + "; ".join(
        f"{b['rotulo']} {b['continuam']} que continuam e {b['novos']} eleitos em 2026"
        for b in blocos
    )
    svg = HEMI81.svg(blocos, "Senado de 2027 por campo", desc)
    leg = "".join(
        f'<li><span class="sw" style="background:{b["cor"]}"></span>{b["rotulo"]}: <strong>{b["continuam"] + b["novos"]}</strong> '
        f"({b['novos']} novos)</li>"
        for b in blocos
    )
    h += (
        f'<figure id="fig-hemiciclo-senado"><div class="chart-fit">{svg}</div><ul class="legenda-mapa">'
        '<li><span class="sw" style="background:#fffdf8;border:2px solid #535b54"></span>contorno: eleito em 2022, mandato até 2031</li>'
        f"{leg}</ul><figcaption>Assento cheio: eleito em 2026. Assento só com contorno: eleito em 2022 (eleito da urna, não o titular atual).</figcaption></figure>"
    )
    partidos = sorted(s["por_partido"].items(), key=lambda kv: -kv[1])
    novos_p = S["eleitos_2026_por_partido"]
    h += tabela(
        ["Partido", "Senado de 2027", "Eleitos em 2026", "Eleitos em 2022"],
        [[escape(k), v, novos_p.get(k, 0), v - novos_p.get(k, 0)] for k, v in partidos],
        "Bancadas no Senado de 2027.",
    )
    eleitos = {(e["uf"], e["vaga"]): e for e in S["eleitos_2026"]}
    linhas = []
    for dsp in sorted(S["disputas"], key=lambda x: x["margem_2a_vaga_pp"])[:8]:
        a, b = eleitos.get((dsp["uf"], 1)), eleitos.get((dsp["uf"], 2))
        t = dsp["terceiro"]
        linhas.append(
            [
                dsp["uf"],
                f"{nome_proprio(a['nome'])} ({escape(a['partido'])})" if a else "s/d",
                f"{nome_proprio(b['nome'])} ({escape(b['partido'])})" if b else "s/d",
                f"{nome_proprio(t['nome'])} ({escape(t['partido'])})",
                num(dsp["margem_2a_vaga_pp"], 2),
                inteiro(dsp["margem_2a_vaga_votos"]),
            ]
        )
    h += tabela(
        ["UF", "1ª vaga", "2ª vaga", "Terceiro", "Margem (pp)", "Margem (votos)"],
        linhas,
        "As oito segundas vagas mais apertadas.",
    )
    h += CMP.senado(d)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 08


def r_assembleias(d: Dados, cap: Capitulo) -> str:
    A = d.get("assembleias.json")
    checar(d, "assembleias.json", ["casas"])
    casas = A["casas"]
    h = secao(
        cap,
        "Assembleias<br><em>dos estados que pesam.</em>",
        f"{len(casas)} casas, da maior para a menor, por campo.",
    )
    h += T.assembleias(A)
    h += figura(
        F.empilhadas(
            [
                (
                    c["uf"],
                    [
                        (c["por_campo"].get(k, 0), COR_CAMPO[k], ROTULO_CAMPO[k])
                        for k in CAMPOS
                    ],
                    f"{c['vagas']} cadeiras",
                )
                for c in casas
            ],
            "Assembleias legislativas por campo",
            "Barras empilhadas por UF com as cadeiras de cada campo, da esquerda para a direita.",
            rotulo_w=60,
            direita_w=110,
        ),
        "Cadeiras por campo. Composição provisória onde o TSE ainda não fechou a lista (ver tabela).",
        ident="fig-assembleias",
    )
    h += tabela(
        [
            "UF",
            "Cadeiras",
            "Dir. + c-dir.",
            "Centro",
            "Esq. + c-esq.",
            "Mais votado",
            "Votos",
            "Lista",
        ],
        [
            [
                c["uf"],
                c["vagas"],
                c["blocos"].get("direita + centro-direita", 0),
                c["blocos"].get("centro", 0),
                c["blocos"].get("esquerda + centro-esquerda", 0),
                (
                    f"{nome_proprio(c['mais_votados'][0]['nome'])} ({escape(c['mais_votados'][0]['partido'])})"
                    if c.get("mais_votados")
                    else "s/d"
                ),
                (
                    inteiro(c["mais_votados"][0]["votos"])
                    if c.get("mais_votados")
                    else "s/d"
                ),
                "TSE" if c.get("fonte") == "tse" else "provisória",
            ]
            for c in casas
        ],
    )
    h += CMP.assembleias(d)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 09


def r_governadores(d: Dados, cap: Capitulo) -> str:
    G = d.get("governadores.json")
    checar(
        d,
        "governadores.json",
        [
            "ufs",
            "vao_estadual.lista",
            "governador_x_presidente",
            "eleitos_1t_por_campo",
        ],
    )
    h = secao(
        cap,
        "Governadores<br><em>e o 2º turno.</em>",
        f"{G['n_eleitos_1t']} eleitos no 1º turno, {G['n_segundo_turno']} segundos turnos. O vão estadual mede o teto, não a transferência.",
    )
    h += T.governadores(G)
    vao = sorted(G["vao_estadual"]["lista"], key=lambda v: -v["vao_pp"])
    h += figura(
        F.divergentes(
            [
                (f"{v['uf'].upper()} {nome_proprio(v['governador'])}", [v["vao_pp"]])
                for v in vao
            ],
            [("Governo menos presidenciável do mesmo bloco, mesma UF", INK)],
            "Vão estadual",
            "Barras divergentes por UF: candidatura ao governo menos o presidenciável do mesmo bloco, em pontos dos válidos.",
            largura=820,
            rotulo_w=230,
        ),
        "Teto endereçável, nunca transferência certa. "
        + escape(G["vao_estadual"].get("nota", "")),
        ident="fig-vao",
    )
    linhas = []
    for u in G["ufs"]:
        c = u["candidatos"]
        a = c[0]
        b = c[1] if len(c) > 1 else None
        linhas.append(
            [
                f"{NOME_UF.get(u['uf'], u['uf'])}",
                "eleito" if u["decisao"] == "eleito" else "2º turno",
                f"{nome_proprio(a['nome'])} ({escape(a['partido'])}, {campo_rot(a.get('campo')).lower()})",
                num(a["pct"], 2),
                f"{nome_proprio(b['nome'])} ({escape(b['partido'])})" if b else "",
                num(b["pct"], 2) if b else "",
            ]
        )
    h += tabela(
        ["UF", "Situação", "Primeiro", "%", "Segundo", "%"],
        linhas,
        "Governadores, versão final de cada UF. Situação pelo texto do TSE.",
    )
    h += CMP.governadores(d)
    E = d.get("estrategia_2t.json")
    if E is None:
        h += bloco_pendente("estrategia_2t.json")
    else:
        ld = E.get("governadores", {}).get("linhas_datafolha", [])
        if ld:
            h += "<h3>O que o Datafolha mediu antes da urna</h3>"
            h += (
                f"<p>Os relatórios estaduais do Datafolha de setembro publicaram, em texto corrido, quanto do eleitorado de "
                f"cada candidatura a governador votava em cada presidenciável. São {len(ld)} linhas medidas, não estimadas.</p>"
            )
            h += tabela(
                ["UF", "Eleitorado de", "Pergunta", "Flávio", "Lula", "Página"],
                [
                    [
                        x.get("uf", ""),
                        escape(x.get("origem", "")),
                        escape(x.get("destino_pergunta", "")),
                        x.get("Flávio", ""),
                        x.get("Lula", ""),
                        x.get("pagina", ""),
                    ]
                    for x in ld
                ],
                escape(E["governadores"].get("fonte_linhas", "")),
            )
        sg = E.get("governadores", {}).get("segundo_turno_estadual", [])
        if sg:
            h += tabela(
                [
                    "UF",
                    "Par do 2º turno estadual",
                    "Flávio %",
                    "Lula %",
                    "Margem presidencial (votos)",
                ],
                [
                    [
                        x["uf"],
                        " × ".join(
                            f"{nome_proprio(q['nome'])} ({escape(q['partido'])})"
                            for q in x["par"]
                        ),
                        num(x["flavio_pct"], 2),
                        num(x["lula_pct"], 2),
                        sinal(x["margem_flavio_votos"], 0),
                    ]
                    for x in sg
                ],
                "Os sete 2º turnos estaduais e o resultado presidencial na mesma UF.",
            )
    h += "</section>"
    return h
