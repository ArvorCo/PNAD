"""Blocos HTML da página O Senado de 2027 diante do STF.

Cada função recebe o dicionário de `docs/assets/senado_2027.json` e devolve HTML
pronto para um placeholder do template. Nenhum número é digitado aqui: tudo sai
do JSON do motor. Texto gerado não presume gênero (o JSON não traz gênero), e o
estágio processual é sempre o do documento de origem.
"""

from __future__ import annotations

import re
import statistics
from html import escape as esc

from senado_2026.pagina.comum import data_br, num

from . import fixo
from . import texto as tx
from .anexos import anexo as anexo
from .anexos import arbitragem as arbitragem
from .anexos import fontes as fontes
from .anexos import limites as limites
from .comum import (
    BLOCO,
    CONTINGENCIA,
    ESTAGIO,
    SINAL,
    TIPO,
    _c,
    _chip,
    _evento,
    _iso_br,
    _link,
    _nome_link,
    _ordenado_por_c,
    _partido_uf,
    _pessoas,
    _sinal,
    _tabela,
)
from .fichas import fichas as fichas

ORDEM_BLOCO = ("DB", "D", "CD", "C", "CE", "E")


VOTO = {"sim": "sim", "nao": "não", "ausente": "ausente", "dividido": "dividido"}


VOTOS_PEC8 = {
    "voto_pec8_sim": "sim",
    "voto_pec8_nao": "nao",
    "voto_pec8_ausente": "ausente",
}


FAIXAS_C = ((0, 20), (20, 35), (35, 50), (50, 65), (65, 80), (80, 101))


FAIXA_ALIANCA = (35, 80)


def _pct(p: float | None) -> str:
    return tx.pct_inteiro(p)


def _estagio_mais_grave(p: dict, regua: dict) -> str | None:
    pontos = regua["K"]["estagio"]
    casos = p.get("casos") or []
    if not casos:
        return None
    return max(casos, key=lambda c: pontos.get(c["estagio"], 0))["estagio"]


def _voto_pec8(p: dict) -> str | None:
    votos = {
        VOTOS_PEC8[s["tipo"]]
        for s in p.get("sinais_contrapeso") or []
        if s["tipo"] in VOTOS_PEC8
    }
    if {"sim", "nao"} <= votos:
        return "dividido"
    for v in ("sim", "nao", "ausente"):
        if v in votos:
            return v
    return None


def _tem_sinal(p: dict, *tipos: str) -> bool:
    return any(s["tipo"] in tipos for s in p.get("sinais_contrapeso") or [])


def _tipos(p: dict) -> list[str]:
    vistos: list[str] = []
    for c in p.get("casos") or []:
        if c["tipo"] not in vistos:
            vistos.append(c["tipo"])
    return vistos


def _tipos_txt(p: dict) -> str:
    t = _tipos(p)
    return ", ".join(TIPO.get(x, x) for x in t) if t else "sem caso localizado"


def _ctx_fonte(data: dict, fid: str) -> dict | None:
    return data["contexto"].get("fontes", {}).get(fid)


def _ctx_links(data: dict, ids: list[str]) -> str:
    partes = [_link(f) for i in ids if (f := _ctx_fonte(data, i))]
    return "; ".join(partes)


def _sim(data: dict, cenario: str, variante: str = "base") -> dict:
    return data["simulacao"]["cenarios"][cenario][variante]


def hero(data: dict) -> str:
    fl, lu = _sim(data, "flavio"), _sim(data, "lula")

    def linha(s: dict) -> str:
        return (
            f"49 votos ou mais: {tx.chances(s['P49'])} ({_pct(s['P49'])}). "
            f"54 ou mais: {tx.chances(s['P54'])} ({_pct(s['P54'])})."
        )

    cartoes = [
        (
            "",
            "PEC que limita o STF",
            "governo Flávio",
            num(fl["pec"]["votos_esperados"]),
            tx.frase_hero(fl["pec"]["votos_esperados"], 49, fl["pec"]["P49"])
            + " "
            + linha(fl["pec"]),
        ),
        (
            "",
            "Impeachment de ministro",
            "governo Flávio",
            num(fl["imp"]["votos_esperados"]),
            tx.frase_hero(fl["imp"]["votos_esperados"], 54, fl["imp"]["P54"])
            + " "
            + linha(fl["imp"]),
        ),
        (
            " sn27-hero-card-lula",
            "PEC e impeachment",
            "governo Lula",
            f"{num(lu['pec']['votos_esperados'])} · {num(lu['imp']['votos_esperados'])}",
            "PEC: "
            + tx.frase_hero(lu["pec"]["votos_esperados"], 49, lu["pec"]["P49"])
            + f" Chance de 49: {_pct(lu['pec']['P49'])}. Impeachment: "
            + tx.frase_hero(lu["imp"]["votos_esperados"], 54, lu["imp"]["P54"])
            + f" Chance de 54: {_pct(lu['imp']['P54'])}.",
        ),
    ]
    return "".join(
        f'<article class="sn27-hero-card{extra}">'
        f'<h2 class="sn27-hero-t">{esc(t)} <small>{esc(cen)}</small></h2>'
        f'<b class="sn27-hero-n">{n}</b>'
        f'<p class="sn27-hero-p">{esc(frase)}</p></article>'
        for extra, t, cen, n, frase in cartoes
    )


def aviso(data: dict) -> str:
    idx = _pessoas(data)
    itens = []
    for item in data["elenco"]:
        cont = item.get("contingencia")
        if not cont:
            continue
        t = item["titular"]
        tipo = CONTINGENCIA.get(cont.get("tipo"), cont.get("tipo") or "")
        sub = cont.get("substituto") or {}
        s = item.get("substituto")
        oc_lula = item.get("ocupante", {}).get("lula")
        extra = ""
        if oc_lula and oc_lula != t["slug"] and oc_lula in idx:
            o = idx[oc_lula]["pessoa"]
            extra = (
                f" Em governo Lula a cadeira fica com {esc(o['nome'])} "
                f"({_partido_uf(o)}), C de impeachment {num(_c(o, 'lula'), 0)}, "
                f"contra {num(_c(t, 'lula'), 0)} de {esc(t['nome'])}."
            )
        elif sub.get("nome"):
            c_txt = (
                f" C de impeachment em governo Flávio: {num(_c(s), 0)}, contra "
                f"{num(_c(t), 0)} de {esc(t['nome'])}."
                if s
                else ""
            )
            extra = (
                f" Quem assume: {esc(sub['nome'])} "
                f"({esc(sub.get('partido') or 'partido a confirmar')}).{c_txt}"
            )
        itens.append(
            f'<li><b><a href="#ficha-{esc(t["slug"])}">{esc(t["nome"])}</a></b> '
            f"({_partido_uf(t)}, cadeira {esc(item['cadeira'])}): {esc(tipo)}. "
            f"{_iso_br(cont.get('nota'))}{extra}</li>"
        )
    sims = data["simulacao"]["cenarios"]["flavio"]
    efeitos = []
    for chave, rotulo in (
        ("suplentes_segundo_turno", "Se os senadores no 2º turno de governo vencerem"),
        ("cadeira_sub_judice_vaga", "Se o registro sub judice cair e a cadeira vagar"),
    ):
        dif = sims.get(chave, {}).get("diferenca_para_base")
        if not dif:
            continue
        efeitos.append(
            f"<li>{rotulo}: impeachment {_sinal(dif['imp']['votos_esperados'], 1)} "
            f"voto esperado e {_sinal(dif['imp']['P54'], 1)} ponto na chance de 54; "
            f"PEC {_sinal(dif['pec']['votos_esperados'], 1)} voto esperado e "
            f"{_sinal(dif['pec']['P49'], 1)} ponto na chance de 49. "
            f"{esc(data['simulacao']['variantes'].get(chave, ''))}</li>"
        )
    return (
        '<div class="sn27-caixa">'
        f"<p><b>Contingências abertas na data de corte ({len(itens)} cadeiras).</b> "
        "A página usa o elenco projetado para a posse de 01/02/2027. Estas cadeiras "
        "ainda podem mudar de ocupante:</p>"
        f"<ul>{''.join(itens)}</ul>"
        "<p><b>Quanto isso move a conta</b> (governo Flávio, diferença para o "
        f"elenco base):</p><ul>{''.join(efeitos)}</ul></div>"
    )


def _conta(v) -> int:
    return len(v) if isinstance(v, list) else v


def origem(data: dict) -> str:
    ctx = data["contexto"]
    partes = []
    ev = _evento(data, "matais_x")
    if ev:
        m = re.search(r"'(.+?)'", ev["fato"])
        frase = m.group(1) if m else ev["fato"]
        resto = ev["fato"][m.end() :].strip() if m else ""
        partes.append(
            "<h3>O post</h3>"
            f'<blockquote class="sn27-caixa"><p>“{esc(frase)}”</p>'
            f'<p class="sn27-meta">Andreza Matais, X, {data_br(ev["data"])}. '
            f"{_ctx_links(data, ev['fontes'])}</p></blockquote>"
            f"<p>{esc(resto)}</p>"
        )
    ev = _evento(data, "polliv")
    if ev:
        partes.append(
            "<h3>A coluna de O Globo: duas estratégias</h3>"
            f"<p>{_iso_br(ev['fato'])}</p>"
            f'<p class="sn27-meta">{data_br(ev["data"])}. '
            f"Lido por reproduções: {_ctx_links(data, ev['fontes'])}</p>"
        )
    listas = ctx.get("listas_declarados", {})
    rows = []
    for chave, lst in listas.items():
        if chave.startswith("_") or not isinstance(lst, dict):
            continue
        nome = _ctx_fonte(data, lst.get("fonte", "")) or {}
        if "total" in lst:
            total = str(lst["total"])
        else:
            total = (
                f"{lst.get('total_manchete')} na manchete, "
                f"{lst.get('total_no_texto')} no texto"
            )
        eleitos = lst.get("eleitos_2026", lst.get("eleitos_2026_sim"))
        if lst.get("composicao"):
            comp = lst["composicao"]
        elif eleitos is not None:
            comp = (
                f"{_conta(eleitos)} eleitos + "
                f"{_conta(lst.get('mandato_ate_2031') or 0)} com mandato até 2031"
            )
        else:
            comp = ""
        criterio = lst.get("criterio") or lst.get("nota") or ""
        rows.append(
            [
                esc(nome.get("veiculo") or chave),
                esc(total),
                esc(comp),
                esc(criterio),
                _link(nome) if nome else "",
            ]
        )
    comp = listas.get("_comparacao_eleitos", {})
    porque = ""
    if comp:
        porque = (
            "<h3>Por que as contagens divergem</h3>"
            f"<p>Nas três listas nominais (Metrópoles, Gazeta do Povo e JOTA), "
            f"{_conta(comp.get('nas_tres'))} eleitos aparecem em todas; somadas, são "
            f"{_conta(comp.get('uniao'))} nomes. {esc(comp.get('por_que_divergem', ''))}</p>"
        )
    return (
        "".join(partes)
        + "<h3>As contagens da imprensa</h3>"
        + "<p>Cada veículo usou um critério. A tabela mostra o total, a composição, "
        "o critério declarado e o link.</p>"
        + _tabela(
            ["Veículo", "Total", "Composição", "Critério", "Fonte"],
            rows,
            "Contagens da imprensa de senadores favoráveis a impeachment",
            {1},
        )
        + porque
    )


def regua(data: dict) -> str:
    r = data["regua"]
    K, C = r["K"], r["C"]
    inativos = set(K["estagios_inativos"])
    est_rows = [
        [
            _chip(e),
            num(p, 0),
            "encerrado ou parado" if e in inativos else "ativo",
        ]
        for e, p in sorted(K["estagio"].items(), key=lambda kv: -kv[1])
    ]
    foro = "; ".join(f"{k} +{v}" for k, v in K["foro"].items())
    ra = K["relator_alvo"]
    rec = K["recencia"]
    bonus = (
        f"<p>Por caso ativo, somam-se bônus: foro atual ({esc(foro)}); relator entre "
        f"{esc(tx.lista_nomes(ra['ministros']))} (+{ra['pontos']}); última decisão "
        f"a partir de {rec['ano_minimo']} (+{rec['pontos']}). "
        f"{esc(K['regra_inativos'])} O K do senador é o maior caso mais "
        f"{num(K['peso_demais_casos'])} vez a soma dos demais, com teto "
        f"{K['teto']}. {esc(K['regra_empate'])}</p>"
    )
    base_rows = [
        [
            esc(BLOCO[b]),
            num(C["base"]["C_imp"][b], 0),
            num(C["base"]["C_pec"][b], 0),
        ]
        for b in ORDEM_BLOCO
    ]
    aj_rows = [
        [esc(a["rotulo"]), _sinal(a["C_imp"]), _sinal(a["C_pec"])] for a in C["ajustes"]
    ]
    al = C["alinhado_governo_lula"]
    aj_rows.append([esc(al["rotulo"]), _sinal(al["C_imp"]), _sinal(al["C_pec"])])
    pa = C["piso_autoria"]
    red = C["redutor_patrimonial"]
    lula = C["cenario_lula"]
    lula_rows = [
        [
            esc(BLOCO[b]),
            _sinal(lula["C_imp"].get(b, 0)),
            _sinal(lula["C_pec"].get(b, 0)),
        ]
        for b in ORDEM_BLOCO
        if b in lula["C_imp"] or b in lula["C_pec"]
    ]
    lim = C["limites"]
    conf = r["confianca"]
    inc = conf["incerteza_pp"]
    estagios_red = tx.lista_nomes([ESTAGIO.get(e, e) for e in red["estagios_ativos"]])
    return (
        "<h3>K, a exposição judicial</h3>"
        "<p>Cada caso vale pontos pelo estágio do documento de origem. Condenação "
        "vale mais que denúncia, denúncia mais que inquérito, e caso arquivado vale "
        "pouco. O K vai de 0 a 100.</p>"
        + _tabela(
            ["Estágio", "Pontos", "Situação"],
            est_rows,
            "Pontos por estágio processual",
            {1},
        )
        + bonus
        + "<h3>C, o contrapeso</h3>"
        "<p>C começa na base do bloco e anda com sinais públicos: voto, assinatura, "
        "declaração. São dois números separados, um para a PEC (49 votos) e outro "
        "para o impeachment (54 votos).</p>"
        + _tabela(
            ["Bloco", "Base C impeachment", "Base C PEC"],
            base_rows,
            "Base de C por bloco",
            {1, 2},
        )
        + '<details class="gv-tec"><summary>Ajustes, redutor, cenário Lula e '
        "limites</summary>"
        + _tabela(
            ["Sinal", "C impeachment", "C PEC"],
            aj_rows,
            "Ajustes de C por sinal",
            {1, 2},
        )
        + f"<p>{esc(C['regra_ajustes'])} Sinais sem ajuste: "
        f"{esc(tx.lista_nomes([SINAL.get(s, s) for s in C['sinais_sem_ajuste']]))}.</p>"
        f"<p><b>Piso de autoria.</b> {esc(pa['rotulo'])}: C de impeachment no mínimo "
        f"{pa['C_imp']} e C de PEC no mínimo {pa['C_pec']}.</p>"
        f"<p><b>{esc(red['rotulo'])}.</b> Tira {num(red['C_imp'], 2)} × K do C de "
        f"impeachment e {num(red['C_pec'], 2)} × K do C de PEC, só sobre a parcela de "
        f"K que vem de casos patrimoniais ativos ({esc(estagios_red)}). Casos de "
        "opinião e de 8 de janeiro não reduzem.</p>"
        f"<p><b>{esc(lula['rotulo'])}.</b> Desconto por bloco:</p>"
        + _tabela(
            ["Bloco", "C impeachment", "C PEC"],
            lula_rows,
            "Desconto do cenário Lula",
            {1, 2},
        )
        + f"<p><b>Limites.</b> C fica entre {lim[0]} e {lim[1]}.</p>"
        f"<p><b>Confiança.</b> Alta com {conf['minimo_observados_alta']} ou mais "
        f"sinais observados (voto nominal, assinatura, CPI); média com declaração; "
        f"baixa para suplente ou sem sinal. Incerteza: ±{inc['alta']}, "
        f"±{inc['media']} e ±{inc['baixa']} pontos.</p></details>" + fixo.o_que_nao_e()
    )


def ranking(data: dict) -> str:
    rg = data["regua"]
    rows = []
    for item in _ordenado_por_c(data):
        t = item["titular"]
        sc = t["scores"]
        voto = _voto_pec8(t)
        rows.append(
            [
                f'<a href="#ficha-{esc(t["slug"])}">{esc(t["nome"])}</a>',
                _partido_uf(t),
                esc(BLOCO.get(t["bloco"], t["bloco"])),
                num(sc["K"], 0),
                num(_c(t, "flavio", "C_imp"), 0),
                num(_c(t, "flavio", "C_pec"), 0),
                num(_c(t, "lula", "C_imp"), 0),
                esc(sc["confianca"].replace("media", "média")),
                _chip(_estagio_mais_grave(t, rg)),
                esc(VOTO.get(voto, "não estava") if voto else "não estava"),
            ]
        )
    return _tabela(
        [
            "Senador",
            "Partido-UF",
            "Bloco",
            "K",
            "C imp. Flávio",
            "C PEC Flávio",
            "C imp. Lula",
            "Confiança",
            "Estágio mais grave",
            "PEC 8",
        ],
        rows,
        "Ranking dos 81 senadores por contrapeso",
        {3, 4, 5, 6},
        sortable=True,
        extra="sn27-ranking",
    )


def _faixa(c: float) -> str:
    for lo, hi in FAIXAS_C:
        if lo <= c < hi:
            return f"{lo} a {min(hi, 100)}"
    return "fora"


def conta(data: dict) -> str:
    idx = _pessoas(data)
    variantes = data["simulacao"]["variantes"]
    linhas = []
    for cen in tx.CENARIOS:
        for var, desc in variantes.items():
            s = _sim(data, cen, var)
            linhas.append(
                [
                    esc(tx.NOME_CENARIO[cen]),
                    esc(desc),
                    num(s["pec"]["votos_esperados"]),
                    f"{s['pec']['p5']} a {s['pec']['p95']}",
                    _pct(s["pec"]["P49"]),
                    num(s["imp"]["votos_esperados"]),
                    f"{s['imp']['p5']} a {s['imp']['p95']}",
                    _pct(s["imp"]["P54"]),
                ]
            )
    tabela_sim = _tabela(
        [
            "Cenário",
            "Variante do elenco",
            "PEC: esperado",
            "PEC: 90% entre",
            "PEC: 49 ou mais",
            "Imp.: esperado",
            "Imp.: 90% entre",
            "Imp.: 54 ou mais",
        ],
        linhas,
        "Votos simulados por cenário e variante",
        {2, 4, 5, 7},
    )
    faixas_rows = []
    for cen in tx.CENARIOS:
        ocup = [idx[s]["pessoa"] for s in _sim(data, cen)["ocupantes"] if s in idx]
        for alvo, rot in (("C_imp", "impeachment"), ("C_pec", "PEC")):
            cont = {f"{lo} a {min(hi, 100)}": 0 for lo, hi in FAIXAS_C}
            for p in ocup:
                cont[_faixa(_c(p, cen, alvo))] += 1
            faixas_rows.append(
                [esc(tx.NOME_CENARIO[cen]), rot, *[str(v) for v in cont.values()]]
            )
    tabela_faixas = _tabela(
        ["Cenário", "Alvo", *[f"C {lo} a {min(hi, 100)}" for lo, hi in FAIXAS_C]],
        faixas_rows,
        "Senadores por faixa de C",
        set(range(2, 2 + len(FAIXAS_C))),
    )
    fl = _sim(data, "flavio")
    sem = fl["imp"]["sem_correlacao"]
    pivos_html = []
    for alvo, rot, q in (("imp", "impeachment", 54), ("pec", "PEC", 49)):
        lst = tx.pivos(data, "flavio", alvo)
        itens = "".join(
            f"<li><b>{_nome_link(idx[p['slug']]) if p['slug'] in idx else esc(p['nome'])}"
            f"</b><br>{_partido_uf(idx[p['slug']]['pessoa']) if p['slug'] in idx else ''}"
            f" · {esc(BLOCO.get(p['bloco'], p['bloco']))}<br>"
            f'<span class="sn27-meta">C {num(p["C"], 0)} · muda a chance de {q} em '
            f"{num(p['decisivo_pp'])} pontos</span></li>"
            for p in sorted(lst, key=lambda x: -x["decisivo_pp"])
        )
        pivos_html.append(
            f"<h3>Pivôs do {rot} em governo Flávio ({len(lst)})</h3>"
            f'<ul class="sn27-pivos">{itens}</ul>'
        )
    return (
        "<p>O Senado tem 81 cadeiras. Uma PEC precisa de 49 votos, três quintos, em "
        "dois turnos. Um impeachment de ministro do STF precisa de 54, dois terços, "
        "já na admissibilidade pela liminar em vigor. A simulação sorteia cada voto "
        f"{num(data['simulacao']['parametros']['sorteios'], 0)} vezes com a "
        "probabilidade C de cada senador.</p>"
        + tabela_sim
        + "<p>A faixa de 90% vai do percentil 5 ao 95 dos sorteios. Sem a correlação "
        f"por bloco, o impeachment em governo Flávio iria de {sem['p5']} a "
        f"{sem['p95']} votos, com {_pct(sem['P54'])} de chance de 54: a correlação "
        "alarga a faixa porque senadores do mesmo bloco tendem a mudar juntos.</p>"
        "<h3>Quantos senadores em cada faixa de C</h3>"
        + tabela_faixas
        + "".join(pivos_html)
        + f"<p><b>Quem decide.</b> {tx.frase_pivos(data, 'flavio', 'pec')} "
        f"{tx.frase_pivos(data, 'flavio', 'imp')}</p>" + fixo.aula_rito()
    )


def pivos_frase(data: dict) -> str:
    """Frase que acompanha a figura dos pivôs."""
    return (
        f"<p>{tx.frase_pivos(data, 'flavio', 'imp')}</p>"
        f"<p>{tx.frase_pivos(data, 'lula', 'imp')}</p>"
    )


def tipos_frase(data: dict) -> str:
    return f"<p>{esc(tx.frase_tipos(data, 'flavio'))}</p>"


def teste_pec8(data: dict) -> str:
    t = data["teste_pec8"]
    pres = tx.pec8_presentes(data)
    no_painel = {
        s for k in ("sim", "nao", "ausente", "presente_sem_voto") for s in pres[k]
    }
    tk, tt = t["tabela_K"], t["tabela_tipo"]
    tipos = ("opiniao", "patrimonial", "eleitoral", "8_de_janeiro", "outro")
    rows = []
    for voto in ("sim", "nao", "ausente", "dividido"):
        k = tk.get(voto, {})
        tp = tt.get(voto, {})
        if not (k.get("K_positivo") or k.get("K_zero")):
            continue
        rows.append(
            [
                esc(VOTO[voto]),
                str(k.get("K_positivo", 0) + k.get("K_zero", 0)),
                str(k.get("K_positivo", 0)),
                str(k.get("K_zero", 0)),
                *[str(tp.get(x, 0)) for x in tipos],
                str(tp.get("sem_caso", 0)),
            ]
        )
    tabela = _tabela(
        [
            "Voto na PEC 8",
            "Senadores",
            "K maior que 0",
            "K igual a 0",
            *[f"Caso de {TIPO[x]}" for x in tipos],
            "Sem caso",
        ],
        rows,
        "Voto na PEC 8/2021 por exposição judicial e tipo de caso",
        set(range(1, 10)),
    )
    sen = t["senadores"]
    fora = [s for s in sen if s["slug"] not in no_painel]
    fora_txt = ""
    if fora:
        fora_txt = (
            f"<p>A tabela tem {len(sen)} linhas: os {pres['total']} do painel "
            "oficial mais "
            + esc(
                tx.lista_nomes(
                    [
                        f"{s['nome']} ({'suplente, ' if s['papel'] != 'titular' else ''}"
                        f"{VOTO.get(s['voto'], s['voto'])})"
                        for s in fora
                    ]
                )
            )
            + ", com o voto registrado nas fichas. Quem estava presente sem votar "
            "conta como ausente. "
            f"{esc(t.get('nota_tabela_tipo', ''))}</p>"
        )
    nao_total = tk["nao"]["K_positivo"] + tk["nao"]["K_zero"]
    sim_pat = [s for s in sen if s["voto"] == "sim" and s["K_patrimonial_ativo"] > 0]
    pat_txt = (
        esc(
            tx.lista_nomes(
                [
                    f"{s['nome']} (K {num(s['K'], 0)}, parcela patrimonial ativa "
                    f"{num(s['K_patrimonial_ativo'], 0)})"
                    for s in sim_pat
                ]
            )
        )
        if sim_pat
        else "nenhum"
    )
    a, b = t["sim_entre_K_positivo_pct"], t["sim_entre_K_zero_pct"]
    if a < b:
        direcao = (
            f"Entre os expostos, {num(a)}% votaram sim; entre os sem caso, {num(b)}%. "
            "A diferença vai na direção do post, mas é pequena"
        )
    else:
        direcao = (
            f"Entre os expostos, {num(a)}% votaram sim; entre os sem caso, {num(b)}%. "
            "A diferença vai na direção contrária à do post"
        )
    conclusao = (
        f"<p><b>O que os números dizem.</b> Dos {nao_total} votos não, "
        f"{tk['nao']['K_positivo']} vieram de quem tem K maior que zero. Entre os "
        f"{tk['sim']['K_positivo'] + tk['sim']['K_zero']} votos sim, "
        f"{len(sim_pat)} tinham caso patrimonial ativo: {pat_txt}. {direcao}, e o "
        f"teste exato de Fisher dá p = {num(t['p_fisher_bilateral_pct'])}%: com "
        f"{len(sen)} senadores, a diferença não se separa do acaso. A PEC 8 não "
        "mostra os expostos votando para proteger o STF.</p>"
    )
    contra = []
    por_slug = {s["slug"]: s for s in sen}
    idx = _pessoas(data)
    for slug in ("alessandro-vieira", "damares-alves", "rogerio-carvalho"):
        s = por_slug.get(slug)
        if not s or slug not in idx:
            continue
        contra.append(
            f"<li>{_nome_link(idx[slug])} ({_partido_uf(idx[slug]['pessoa'])}): "
            f"votou {esc(VOTO.get(s['voto'], s['voto']))}, K {num(s['K'], 0)}, "
            f"casos: {esc(_tipos_txt(idx[slug]['pessoa']))}.</li>"
        )
    contra_html = (
        "<h3>Contraexemplos nomeados</h3><ul>" + "".join(contra) + "</ul>"
        if contra
        else ""
    )
    return tabela + fora_txt + conclusao + contra_html


def _pauta(p: dict, data: dict) -> str:
    slug = p["slug"]
    master = next(
        (
            x
            for x in data["contexto"].get("pedidos", [])
            if x["id"].startswith("cpi-master")
        ),
        None,
    )
    assinou_master = bool(master) and slug in (
        master.get("signatarios_no_senado_2027") or []
    )
    if _tem_sinal(p, "declaracao_contra_impeachment"):
        return (
            "declarou-se contra o impeachment: nada de impeachment; a conversa é a "
            "PEC e o regimento"
        )
    partes = []
    if _tem_sinal(p, "voto_pec8_sim"):
        partes.append("votou sim na PEC 8: reforma do rito e decisões monocráticas")
    if assinou_master:
        partes.append("assinou a CPI do Master: a CPI como porta de entrada")
    if _tem_sinal(p, "voto_pec8_nao"):
        partes.append(
            "votou não na PEC 8: transparência (estoque de pedidos e prazo de "
            "decisão) antes de qualquer limite ao STF"
        )
    if _tem_sinal(p, "dialogavel_segundo_stf", "sondagem_com_ministro"):
        partes.append("descrito como dialogável por ministros: regimento, não pessoa")
    if not partes:
        partes.append(
            "sem sinal público de pauta; começar pelo prazo de decisão do "
            "presidente do Senado"
        )
    return "; ".join(partes)


def _aliados(data: dict, alvo: str) -> list[tuple[dict, dict]]:
    idx = _pessoas(data)
    lo, hi = FAIXA_ALIANCA
    out = []
    for p in sorted(tx.pivos(data, "flavio", alvo), key=lambda x: -x["decisivo_pp"]):
        if lo <= p["C"] <= hi and p["slug"] in idx:
            out.append((p, idx[p["slug"]]))
    return out


def _lista_aliados(data: dict, alvo: str) -> str:
    itens = []
    for p, info in _aliados(data, alvo):
        pe = info["pessoa"]
        itens.append(
            f"<li><b>{_nome_link(info)}</b> ({_partido_uf(pe)}), C {num(p['C'], 0)}, "
            f"K {num(pe['scores']['K'], 0)}, casos: {esc(_tipos_txt(pe))}. "
            f"Pauta: {esc(_pauta(pe, data))}.</li>"
        )
    return (
        "<ul>" + "".join(itens) + "</ul>" if itens else "<p>Nenhum pivô na faixa.</p>"
    )


def recomendacoes(data: dict) -> str:
    idx = _pessoas(data)
    fl, lu = _sim(data, "flavio"), _sim(data, "lula")
    lo, hi = FAIXA_ALIANCA
    # (a) alianças
    n, nomes, ganho = tx.pivos_necessarios(data, "flavio", "imp", FAIXA_ALIANCA)
    falta = 54 - fl["imp"]["votos_esperados"]
    ordenados = sorted(tx.pivos(data, "flavio", "imp"), key=lambda x: -x["decisivo_pp"])
    abaixo = [p["nome"] for p in ordenados if p["C"] < lo]
    acima = [p["nome"] for p in ordenados if p["C"] > hi]
    fora_txt = ""
    if abaixo:
        fora_txt += (
            f" Os pivôs com C abaixo de {lo} ({esc(tx.lista_nomes(abaixo))}) movem "
            "mais a conta por voto, mas pedem mudança de posição, não persuasão."
        )
    if acima:
        fora_txt += (
            f" Os pivôs com C acima de {hi} ({esc(tx.lista_nomes(acima))}) já estão "
            "perto do sim: o trabalho com eles é não perder o voto."
        )
    if falta <= 0:
        precisa = "O esperado já passa de 54."
    elif n is None:
        precisa = (
            f"Faltam {num(falta)} votos esperados para 54. Mesmo virando todos os "
            f"pivôs da faixa, a soma do que eles ainda podem acrescentar "
            f"({num(ganho)}) não fecha a conta.{fora_txt}"
        )
    else:
        precisa = (
            f"Faltam {num(falta)} votos esperados para 54. Pela aritmética do "
            f"esperado, é preciso virar {n} dos pivôs da faixa, do mais ao menos "
            f"decisivo: {esc(tx.lista_nomes(nomes))}.{fora_txt}"
        )
    folga_pec = fl["pec"]["votos_esperados"] - 49
    sup = data["simulacao"]["cenarios"]["flavio"].get("suplentes_segundo_turno", {})
    dif = sup.get("diferenca_para_base", {})
    st_itens = []
    for item in data["elenco"]:
        cont = item.get("contingencia") or {}
        s = item.get("substituto")
        if cont.get("tipo") != "segundo_turno_governo" or not s:
            continue
        t = item["titular"]
        st_itens.append(
            f"<li>{esc(t['nome'])} ({_partido_uf(t)}), C {num(_c(t), 0)}, cede a "
            f"cadeira a {esc(s['nome'])} ({_partido_uf(s)}), C {num(_c(s), 0)}.</li>"
        )
    suplentes = ""
    if st_itens and dif:
        suplentes = (
            "<p><b>Os suplentes do 2º turno.</b> Se os senadores que disputam governo "
            "em 25/10 vencerem, entram os suplentes:</p>"
            f"<ul>{''.join(st_itens)}</ul>"
            f"<p>O efeito na conta do impeachment é de "
            f"{_sinal(dif['imp']['votos_esperados'], 1)} voto esperado e "
            f"{_sinal(dif['imp']['P54'], 1)} ponto na chance de 54; na PEC, "
            f"{_sinal(dif['pec']['votos_esperados'], 1)} voto e "
            f"{_sinal(dif['pec']['P49'], 1)} ponto na chance de 49.</p>"
        )
    alian = (
        "<h3>a) Alianças: quem cortejar e com que pauta</h3>"
        f"<p>Pivôs da simulação com C entre {lo} e {hi}, em governo Flávio, do "
        "mais ao menos decisivo. A pauta sugerida sai dos sinais públicos de cada "
        "um.</p>"
        f"<h4>Quem fecha os 49 (PEC)</h4><p>O esperado da PEC é "
        f"{num(fl['pec']['votos_esperados'])}, {num(folga_pec)} acima de 49, com "
        f"{_pct(fl['pec']['P49'])} de chance: a tarefa é não perder votos.</p>"
        + _lista_aliados(data, "pec")
        + f"<h4>Quem fecha os 54 (impeachment)</h4><p>{precisa}</p>"
        + _lista_aliados(data, "imp")
        + suplentes
    )
    # (b) ordem das pautas
    marinho = data["contexto"]["rito"].get("proposta_marinho", {})
    ordem = (
        "<h3>b) Ordem das pautas</h3>"
        "<ol>"
        f"<li><b>PEC primeiro.</b> Decisões monocráticas, rito e mandato de ministro. "
        f"É a pauta com {_pct(fl['pec']['P49'])} de chance de 49 em governo Flávio "
        f"({_pct(lu['pec']['P49'])} em governo Lula), e vale para todos os ministros, "
        "não para uma pessoa.</li>"
        f"<li><b>Regimento depois.</b> {_iso_br(marinho.get('materia'))}: "
        f"{_iso_br(marinho.get('conteudo'))} {_iso_br(marinho.get('status'))} A regra "
        "tira do presidente do Senado o poder de engavetar sem prazo, que é o gargalo "
        "real do rito.</li>"
        f"<li><b>Impeachment só com gatilho.</b> A chance de 54 é "
        f"{_pct(fl['imp']['P54'])} em governo Flávio e {_pct(lu['imp']['P54'])} em "
        "governo Lula. Abrir um processo que cai na admissibilidade fortalece o "
        "ministro. O gatilho é fato novo documentado, não a contagem de declarações."
        "</li></ol>"
    )
    # (c) transparência
    rito = data["contexto"]["rito"].get("presidente_do_senado", {})
    casos = [c for t in tx.titulares(data) for c in t.get("casos") or []]
    stf = [c for c in casos if c.get("foro") == "STF"]
    sem_relator = [c for c in stf if not c.get("relator")]
    pagina = sum(1 for c in casos for f in c["fontes"] if f.get("acesso") == "pagina")
    total_f = sum(len(c["fontes"]) for c in casos)
    listas = data["contexto"].get("listas_declarados", {})
    n_listas = sum(1 for k in listas if not k.startswith("_"))
    melhorias = (
        "<h3>c) O que exigir de transparência</h3>"
        "<ul>"
        f"<li><b>Do Senado:</b> publicar o estoque de pedidos de impeachment de "
        f"ministro, com data de entrada e prazo de decisão. Hoje o número depende de "
        f"quem conta: {esc(rito.get('estoque_2026', ''))}</li>"
        f"<li><b>Do STF:</b> uma lista pública de inquéritos e ações contra "
        f"parlamentares, com estágio e relator. Esta página precisou montar "
        f"{len(casos)} casos dos {len(tx.titulares(data))} senadores a partir de "
        f"imprensa e buscas: {len(stf)} estão no STF, {len(sem_relator)} deles sem "
        f"relator informado na fonte, e só {pagina} das {total_f} fontes de casos "
        "puderam ser abertas e lidas.</li>"
        f"<li><b>Da imprensa:</b> o critério de cada lista de “bancada do "
        f"impeachment”. As {n_listas} contagens do capítulo 01 usam critérios "
        "diferentes, e duas não publicam a lista nominal.</li></ul>"
    )
    # (d) contraprova
    db = sorted(
        (t for t in tx.titulares(data) if t["bloco"] == "DB" and t["scores"]["K"] > 0),
        key=lambda t: -t["scores"]["K"],
    )[:5]
    db_txt = tx.lista_nomes(
        [f"{t['nome']} (K {num(t['scores']['K'], 0)}, C {num(_c(t), 0)})" for t in db]
    )
    av = idx.get("alessandro-vieira")
    av_txt = ""
    if av:
        pe = av["pessoa"]
        autor = [
            x
            for x in data["contexto"].get("pedidos", [])
            if "Vieira" in (x.get("autor") or "")
        ]
        av_txt = (
            f" {esc(pe['nome'])} ({_partido_uf(pe)}, bloco "
            f"{esc(BLOCO.get(pe['bloco'], pe['bloco']))}) tem K "
            f"{num(pe['scores']['K'], 0)} e C {num(_c(pe), 0)}, e é autor de "
            f"{len(autor)} dos pedidos e CPIs contra ministros registrados na página."
        )
    piv_slugs = {p["slug"] for a in ("pec", "imp") for p in tx.pivos(data, "flavio", a)}
    pat = sorted(
        (
            idx[s]["pessoa"]
            for s in piv_slugs
            if s in idx and idx[s]["pessoa"]["scores"]["K_patrimonial_ativo"] > 0
        ),
        key=lambda p: -p["scores"]["K"],
    )
    pat_txt = tx.lista_nomes(
        [
            f"{p['nome']} ({p.get('partido')}-{p.get('uf')}, K "
            f"{num(p['scores']['K'], 0)}, C {num(_c(p), 0)})"
            for p in pat
        ]
    )
    mediana_c = statistics.median(_c(t) for t in tx.titulares(data))
    if db and min(_c(t) for t in db) > mediana_c:
        abertura = (
            "Os bolsonaristas mais expostos estão entre os votos mais prováveis, "
            f"todos com C acima da mediana do Senado ({num(mediana_c, 0)}): "
        )
        fecho = " Processo, para eles, não comprou silêncio."
    else:
        abertura = "Os bolsonaristas mais expostos: "
        fecho = ""
    contraprova = (
        '<div class="contraprova"><strong>O achado que contraria a tese</strong>'
        f"<p>{abertura}{esc(db_txt)}.{fecho}{av_txt}</p>"
        f"<p>A única região onde a hipótese do post pode valer são os pivôs com caso "
        f"patrimonial ativo: {esc(pat_txt) if pat else 'nenhum'}. Ali o redutor "
        "patrimonial é uma hipótese da régua, não uma medição: nenhum desses nomes "
        "votou ainda um impeachment, e a hipótese segue sem teste.</p></div>"
    )
    hipotese = (
        '<div class="hyp"><p><b>Hipótese.</b> Se a profecia do post vale, os pivôs com '
        "caso patrimonial ativo votarão abaixo do seu C nas votações de 2027, e os "
        "demais pivôs, não.</p>"
        '<strong class="iffail">Se falhar: os pivôs patrimoniais votam como os demais, '
        "e o redutor patrimonial da régua deve sair.</strong></div>"
    )
    teste = (
        "<h3>e) Como a profecia será testada em 2027</h3>"
        "<p>Duas votações bastam. Numa PEC sobre o STF e numa admissibilidade de "
        f"impeachment, compare o voto de {esc(pat_txt) if pat else 'os pivôs'} com o "
        "C publicado aqui. Se votarem abaixo do C e os pivôs sem caso não, a hipótese "
        "ganha a primeira evidência. Se votarem igual, perde. A página publicará o "
        "resultado com o mesmo destaque, qualquer que seja.</p>"
    )
    return (
        "<p><b>Tudo neste capítulo é juízo editorial da casa</b>, construído sobre os "
        "números das seções anteriores. Cada recomendação traz o número ao lado; "
        "nenhuma é previsão.</p>"
        + hipotese
        + alian
        + ordem
        + melhorias
        + "<h3>d) O achado que contraria a tese</h3>"
        + contraprova
        + teste
    )


def como_lemos(data: dict) -> str:
    tit = tx.titulares(data)
    k = [t["scores"]["K"] for t in tit]
    return (
        fixo.aula_estagios()
        + fixo.como_ler_ficha()
        + f'<p class="sn27-meta">Nesta edição: K médio {num(statistics.fmean(k))}, '
        f"mediana {num(statistics.median(k))}, máximo {num(max(k), 0)}.</p>"
    )
