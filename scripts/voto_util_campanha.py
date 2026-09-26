"""Capitulos de campanha do mapa do voto util: argumentos, frases, fichas por
estado, kit de resiliencia e regras da campanha voluntaria.

E juizo editorial declarado, a servico de uma candidatura, com o numero ao lado
de cada argumento. Nenhuma frase atribui ao adversario fato que nao esteja em
documento, e nenhuma ataca a candidatura de terceira via: o alvo e a inutilidade
do voto que nao chega ao 2o turno, nunca a pessoa.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Carregado pelo build depois de voto_util_capitulos, que ja esta em sys.modules.
CAP = sys.modules["voto_util_capitulos"]

D, EST, RES, TSE = CAP.D, CAP.EST, CAP.RES, CAP.TSE
fmt, sgn, mil, pct, section, table, cen, F = (
    CAP.fmt,
    CAP.sgn,
    CAP.mil,
    CAP.pct,
    CAP.section,
    CAP.table,
    CAP.cen,
    CAP.F,
)
DF_CRUZ = json.loads(
    (ROOT / "docs/assets/datafolha_21092026_cruzamentos.json").read_text(
        encoding="utf-8"
    )
)

NOMES = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia",
    "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo",
    "TO": "Tocantins",
}  # fmt: skip
EM = {
    "AC": "no", "AL": "em", "AM": "no", "AP": "no", "BA": "na", "CE": "no", "DF": "no",
    "ES": "no", "GO": "em", "MA": "no", "MG": "em", "MS": "em", "MT": "em", "PA": "no",
    "PB": "na", "PE": "em", "PI": "no", "PR": "no", "RJ": "no", "RN": "no", "RO": "em",
    "RR": "em", "RS": "no", "SC": "em", "SE": "em", "SP": "em", "TO": "no",
}  # fmt: skip
DEMONIMO = {
    "AC": "acreano", "AL": "alagoano", "AM": "amazonense", "AP": "amapaense", "BA": "baiano",
    "CE": "cearense", "DF": "brasiliense", "ES": "capixaba", "GO": "goiano", "MA": "maranhense",
    "MG": "mineiro", "MS": "sul-mato-grossense", "MT": "mato-grossense", "PA": "paraense",
    "PB": "paraibano", "PE": "pernambucano", "PI": "piauiense", "PR": "paranaense",
    "RJ": "fluminense", "RN": "potiguar", "RO": "rondoniense", "RR": "roraimense",
    "RS": "gaúcho", "SC": "catarinense", "SE": "sergipano", "SP": "paulista", "TO": "tocantinense",
}  # fmt: skip


def esc(v) -> str:
    return html.escape(str(v))


def em(uf: str) -> str:
    return f"{EM[uf]} {NOMES[uf]}"


def maiuscula(texto: str) -> str:
    return texto[:1].upper() + texto[1:]


def data_br(campo: str | None) -> str:
    """'2026-09-16 a 2026-09-19' vira '16 a 19/09/2026'; outros formatos passam intactos."""
    if not campo or campo[4:5] != "-":
        return campo or ""
    ini, fim = campo.split(" a ")[0].split("-"), campo.split(" a ")[-1].split("-")
    if len(ini) != 3 or len(fim) != 3:
        return campo
    if ini[1] == fim[1]:
        return f"{ini[2]} a {fim[2]}/{fim[1]}/{fim[0]}"
    return f"{ini[2]}/{ini[1]} a {fim[2]}/{fim[1]}/{fim[0]}"


# ------------------------------------------------------------ segmentos
def segmentos() -> list[dict]:
    """Reserva de Flavio por segmento no Datafolha de 15 a 17/09 (BR-04029/2026)."""
    tab = DF_CRUZ["tabelas"]

    def colunas(nome: str) -> dict:
        out: dict[str, dict] = {}
        for b in tab[nome]["blocks"].values():
            for linha, vals in b["rows"].items():
                for col, v in vals.items():
                    out.setdefault(col, {})[linha] = v
            for col, v in b["base"].items():
                out.setdefault(col, {})["_base"] = v
            for col in b["columns"]:
                out.setdefault(col, {})["_pagina"] = b["pdf_page"]
        return out

    e1, e2, dfn = (
        colunas("estimulada_b"),
        colunas("turno2_flavio"),
        colunas("definicao"),
    )
    rotulos = {
        "Mais de 5 SM": "Renda acima de 5 salários",
        "Nao tem": "Sem partido de preferência",
        "Outro partido": "Outro partido que não PT ou PL",
        "Evangelica": "Evangélicos",
        "Sul": "Sul",
        "25-34": "25 a 34 anos",
        "Superior": "Ensino superior",
        "Centro-Oeste/Norte": "Centro-Oeste e Norte",
        "16-24": "16 a 24 anos",
        "Masculino": "Homens",
        "Branca": "Brancos",
        "2 a 5 SM": "Renda de 2 a 5 salários",
        "PEA": "Quem trabalha ou procura trabalho",
        "Medio": "Ensino médio",
        "Interior": "Interior",
        "Feminino": "Mulheres",
        "Parda": "Pardos",
        "Ate 2 SM": "Renda até 2 salários",
        "Catolica": "Católicos",
        "60+": "60 anos ou mais",
        "Fundamental": "Ensino fundamental",
        "Nordeste": "Nordeste",
    }
    out = []
    for col, nome in rotulos.items():
        f1 = e1[col].get("Flavio Bolsonaro (PL)")
        f2 = next(v for k, v in e2[col].items() if k.startswith("Flavio"))
        l1 = e1[col].get("Lula (PT)")
        l2 = next(v for k, v in e2[col].items() if k.startswith("Lula"))
        tv = sum(
            v or 0
            for k, v in e1[col].items()
            if any(
                s in k
                for s in (
                    "Cury",
                    "Caiado",
                    "Renan",
                    "Zema",
                    "Avalanche",
                    "Clariana",
                    "Grassi",
                )
            )
        )
        out.append(
            {
                "coluna": col,
                "nome": nome,
                "f1": f1,
                "f2": f2,
                "l1": l1,
                "l2": l2,
                "reserva": f2 - f1,
                "terceira": tv,
                "pode_mudar": dfn.get(col, {}).get("Seu voto ainda pode mudar?"),
                "base": e1[col]["_base"],
                "pagina_1t": e1[col].get("_pagina"),
                "pagina_2t": e2[col].get("_pagina"),
            }
        )
    out.sort(key=lambda s: -s["reserva"])
    return out


SEG = segmentos()
SEGD = {s["coluna"]: s for s in SEG}


# ------------------------------------------------------------ frases por estado
def frases_uf(uf: str) -> list[str]:
    out = []
    r = RES[uf]
    e = EST.get(uf)
    if r["reserva_eleitores"] >= 30000:
        out.append(
            f"{maiuscula(em(uf))}, {mil(r['reserva_eleitores'])} de eleitores já votam em Flávio no 2º turno e ainda não no 1º. "
            f"Se eles anteciparem, a eleição muda aqui antes de mudar no país."
        )
    if e:
        for g in e["indicadores"].get("governador_cruzamento", []):
            if (
                g["campo"] in ("direita", "centro-direita")
                and 100 - g["flavio_entre_eleitores"] >= 20
                and g["voto_governador"] >= 10
            ):
                dez = round((100 - g["flavio_entre_eleitores"]) / 10)
                out.append(
                    f"Quem vota em {g['nome']} para governador: {dez} de cada 10 eleitores dele ainda não votam em Flávio para presidente. "
                    f"Governador forte precisa de presidente parceiro."
                )
                break
        v = e["pres_1t"]["valores"]
        tv = max(
            ((k, v.get(k, 0)) for k in ("Cury", "Caiado", "Zema", "Renan")),
            key=lambda x: x[1],
        )
        if tv[1] >= 4:
            out.append(
                f"{tv[0]} tem {fmt(tv[1])}% {em(uf)} e não chega perto do 2º turno em nenhuma pesquisa nacional. O voto nele pesa pouco no 1º turno e não existe no 2º."
            )
        q = (e.get("quem_ganha") or {}).get("valores")
        p2 = e.get("pres_2t")
        if (
            q
            and p2
            and p2["valores"]["Flávio"] > p2["valores"]["Lula"]
            and q.get("Lula", 0) > q.get("Flávio", 0)
        ):
            out.append(
                f"Aqui Flávio vence o 2º turno por {fmt(p2['valores']['Flávio'])} a {fmt(p2['valores']['Lula'])}, e mesmo assim {fmt(q['Lula'])}% acham que Lula vai ganhar. "
                f"Você não está sozinho: está na maioria."
            )
        lv = e.get("lv")
        if (
            lv
            and (lv["outros"]["F"] - lv["outros"]["L"])
            > (lv["sempre"]["F"] - lv["sempre"]["L"]) + 2
        ):
            out.append(
                "Aqui quem costuma faltar vota mais em Flávio do que quem sempre vota. Leve um vizinho, um parente, um colega para votar."
            )
    if TSE[uf]["regiao"] == "Nordeste":
        out.append(
            "Cada voto aqui é um voto a menos na conta que pode fechar a eleição no 1º turno. No Nordeste, votar Flávio é segurar a eleição aberta."
        )
    return out[:4]


def ficha_uf(uf: str) -> str:
    r = RES[uf]
    e = EST.get(uf)
    rt = D["realtime"].get(uf)
    linhas = []
    if e:
        g = e["pres_1t"]["grupos"]
        p2 = e.get("pres_2t")
        linhas.append(
            [
                "Quaest",
                esc(e.get("campo") or "agosto"),
                f"{fmt(g['F'])} × {fmt(g['L'])}",
                (
                    f"{fmt(p2['valores']['Flávio'])} × {fmt(p2['valores']['Lula'])}"
                    if p2
                    else "não mediu"
                ),
                fmt(g["Tdir"]),
                f"{fmt(g['I'])} / {fmt(g['B'])}",
            ]
        )
    if rt:
        g = rt["grupos"]
        v2 = rt["segundo_turno"]
        linhas.append(
            [
                "Real Time",
                esc(data_br(rt.get("campo"))),
                f"{fmt(g['F'])} × {fmt(g['L'])}",
                f"{fmt(v2['Flávio'])} × {fmt(v2['Lula'])}" if v2 else "não mediu",
                fmt(g["Tdir"]),
                f"{fmt(g['I'])} / {fmt(g['B'])}",
            ]
        )
    tab = (
        table(
            [
                "Casa",
                "Campo",
                "1º turno Flávio × Lula",
                "2º turno Flávio × Lula",
                "Terceira via de direita",
                "Indecisos / branco",
            ],
            linhas,
            f"Pesquisas {em(uf)}",
            "compact",
        )
        if linhas
        else "<p class='sub'>Sem pesquisa estadual publicada com presidente no período. Números estimados pela região sobre o resultado de 2022.</p>"
    )
    gov = ""
    if e:
        itens = []
        for g in e["indicadores"].get("governador_cruzamento", []):
            if g["voto_governador"] >= 5:
                itens.append(
                    f"<li>{esc(g['nome'])} ({esc(g['partido'])}), {fmt(g['voto_governador'])}% ao governo: eleitores dele votam {fmt(g['flavio_entre_eleitores'])}% Flávio, {fmt(g['lula_entre_eleitores'])}% Lula, {fmt(g['fora_entre_eleitores'])}% em outro, indecisos ou branco.</li>"
                )
        if itens:
            gov = "<h4>Governador</h4><ul>" + "".join(itens) + "</ul>"
        sen = e.get("senado") or {}
        dirs = [
            c
            for c in sen.get("candidatos", [])
            if c["campo"] in ("direita", "centro-direita") and c["valor"]
        ][:3]
        if dirs:
            gov += (
                "<h4>Senado, direita</h4><p>"
                + "; ".join(
                    f"{esc(c['nome'])} ({esc(c['partido'])}) {fmt(c['valor'])}%"
                    for c in dirs
                )
                + "</p>"
            )
    frases = "".join(f"<li>{esc(f)}</li>" for f in frases_uf(uf))
    resumo = f"{mil(r['reserva_eleitores'])} na reserva"
    return (
        f'<details class="ficha" id="uf-{uf}"><summary><b>{uf}</b> {esc(NOMES[uf])} <span>{esc(resumo)}</span></summary>'
        f'<div class="ficha-corpo">{tab}{gov}<h4>Para usar na conversa</h4><ul class="frases">{frases}</ul></div></details>'
    )


def cap_estados() -> str:
    ordem = sorted(TSE, key=lambda u: -RES[u]["reserva_eleitores"])
    opcoes = "".join(
        f'<option value="uf-{uf}">{esc(NOMES[uf])}</option>'
        for uf in sorted(TSE, key=lambda u: NOMES[u])
    )
    fichas = "".join(ficha_uf(uf) for uf in ordem)
    return section(
        "estados",
        "Estado por estado",
        "A ficha do seu estado",
        f"""
<p class="lead">Cada ficha junta as duas pesquisas estaduais mais recentes, o cruzamento com governador quando existe, os nomes de direita ao Senado e frases prontas, escritas a partir do número do próprio estado. Estão ordenadas pelo tamanho da reserva.</p>
<div class="seletor" hidden><label for="sel-uf">Ir para o estado</label><select id="sel-uf"><option value="">escolha</option>{opcoes}</select></div>
<div class="fichas">{fichas}</div>
""",
    )


# ------------------------------------------------------------ argumentos
def _seg(col: str) -> dict:
    return SEGD[col]


def cap_argumentos() -> str:
    completo = cen("Voto útil completo")
    so_lula = cen("Só Lula consolida")
    ev, mu, jov, rica, sp, nt = (
        _seg("Evangelica"),
        _seg("Feminino"),
        _seg("16-24"),
        _seg("Mais de 5 SM"),
        _seg("Superior"),
        _seg("Nao tem"),
    )
    go = EST["GO"]["pres_1t"]["serie_valores"]
    caiado0, caiado1 = go[0]["valores"].get("Caiado"), go[-1]["valores"].get("Caiado")
    publicos = [
        (
            "Para quem vota na terceira via",
            [
                "Nenhuma candidatura de terceira via passa de um dígito em pesquisa nacional. O 1º turno não escolhe o melhor nome, escolhe quem vai ao 2º. Escolha quem chega.",
                "Voto de protesto que não chega ao 2º turno vira aplauso para quem já está no poder.",
                f"Não é traição ao seu candidato. É conta: de tudo o que a terceira via perdeu e foi para Flávio ou Lula desde agosto, {fmt(100 * captura_flavio())}% foi para Flávio. Quem pensa como você já está fazendo essa conta.",
            ],
        ),
        (
            "Para o eleitor de Augusto Cury",
            [
                "Decisão boa é decisão tomada com a cabeça fria. No 1º turno, a cabeça fria manda votar em quem pode vencer o 2º.",
                "Quase metade do eleitor de Cury diz que o voto ainda pode mudar. Mudar para quem chega não é desistir das ideias, é dar a elas um lugar para existir.",
            ],
        ),
        (
            "Para o eleitor de Ronaldo Caiado",
            [
                f"Em Goiás, onde Caiado governou, ele caiu de {fmt(caiado0)}% para {fmt(caiado1)}% em um mês. O próprio goiano já fez a conta.",
                "Segurança pública e agro precisam de um presidente que chegue ao 2º turno. O voto que chega é o que protege essa agenda.",
            ],
        ),
        (
            "Para o eleitor de Zema e do Novo",
            [
                "Gestão é escolher onde o recurso rende mais. O voto rende mais onde decide.",
                "O 2º turno já está desenhado: é Lula ou Flávio. Quem quer menos Estado e contas em ordem escolhe agora o lado que pode vencer.",
            ],
        ),
        (
            "Para o eleitor de Renan Santos",
            [
                "Contra o sistema, o voto que conta é o que tira do poder quem está nele.",
                "Protesto que termina em 3% no 1º turno vira nota de rodapé. Protesto que decide o 1º turno vira história.",
            ],
        ),
        (
            "Para quem pensa em votar branco ou anular",
            [
                "Branco e nulo não anulam a eleição e não vão para ninguém. Eles saem da conta, e a régua de 50% desce para quem está na frente.",
                f"Em 2022, faltou {fmt(F['faltaram_lula_2022'] / 1e6, 2)} milhão de votos para a eleição acabar no 1º turno. Brancos e nulos foram {pct(F['bn_2022'])} de quem compareceu.",
                f"Se só a esquerda fizer voto útil, Lula vai a {pct(so_lula['lula_validos'])} dos válidos. Anular agora é empurrar essa conta.",
            ],
        ),
        (
            "Para o indeciso",
            [
                "Indecisão no dia 4 de outubro vale como voto em quem já está na frente.",
                "Você não precisa gostar de tudo. Precisa escolher entre os dois que vão decidir: o 2º turno já é Lula contra Flávio.",
            ],
        ),
        (
            "Para quem vota no governador ou no senador de direita",
            [
                "Governador sem presidente parceiro governa de freio de mão puxado.",
                "Senado de direita sem presidente de direita é oposição. Com presidente, é governo.",
                f"Nos doze estados em que a Quaest cruzou os votos, {fmt(F['gov_enderecavel'] / 1e6, 1)} milhões de eleitores votam num governador de direita ou de centro e ainda não votam em Flávio.",
            ],
        ),
        (
            "Para quem é de direita mas não é bolsonarista",
            [
                "Você não precisa ser bolsonarista para votar útil. Precisa decidir se quer mais quatro anos do mesmo governo.",
                "O voto útil não pede adesão, pede aritmética: no 2º turno, você já escolhe Flávio. Antecipe.",
            ],
        ),
        (
            "Para quem já deixou de votar",
            [
                f"Em 2022, {pct(F['abst_2022'])} dos eleitores aptos não foram votar. Nos estados em que a direita ganhou, faltou mais gente do que nos estados em que ela perdeu.",
                "Quem não vai votar não fica neutro: deixa os outros decidirem por você.",
            ],
        ),
    ]
    blocos = "".join(
        f'<div class="arg"><h3>{esc(t)}</h3><ul>{"".join(f"<li>{esc(x)}</li>" for x in xs)}</ul></div>'
        for t, xs in publicos
    )
    seg_fig = CAP.FIG.fig_segmentos(SEG[:14])
    return section(
        "argumentos",
        "O que dizer",
        "Argumentos por público: o alvo é a inutilidade do voto, nunca a pessoa",
        f"""
<p class="lead">Três regras antes das frases. Primeira: não ataque o candidato de quem você quer convencer; ele gosta dele, e é por isso que votou. Ataque a inutilidade do voto que não chega ao 2º turno. Segunda: use o número do estado da pessoa, não o nacional. Terceira: termine sempre com um pedido concreto, votar no dia 4, levar alguém junto.</p>
<div class="args">{blocos}</div>
<h3>Onde está a reserva, por grupo</h3>
<p>No Datafolha de 15 a 17 de setembro, a maior distância entre o voto de Flávio no 2º e no 1º turno está na renda acima de 5 salários ({fmt(rica["f1"])}% no 1º turno, {fmt(rica["f2"])}% no 2º), entre quem não tem partido ({fmt(nt["f1"])}% e {fmt(nt["f2"])}%), entre os evangélicos ({fmt(ev["f1"])}% e {fmt(ev["f2"])}%) e no ensino superior ({fmt(sp["f1"])}% e {fmt(sp["f2"])}%). Entre os jovens de 16 a 24 anos, {fmt(jov["pode_mudar"])}% dizem que o voto ainda pode mudar, a maior volatilidade da pesquisa. Entre as mulheres, Flávio tem {fmt(mu["f1"])}% no 1º turno e {fmt(mu["f2"])}% no 2º, contra {fmt(mu["l2"])}% de Lula: é o grupo mais difícil e o que mais pesa.</p>
<figure class="fig">{seg_fig}<figcaption>Datafolha BR-04029/2026, campo de 15 a 17/09, tabelas do relatório completo. Reserva = Flávio no 2º turno menos Flávio no 1º turno, no mesmo segmento.</figcaption></figure>
{cap_sotaques()}
{cap_ramos()}
<p class="source">O capítulo de argumentos é juízo editorial declarado. Com o voto útil completo da direita, o modelo põe Flávio em {pct(completo["flavio_validos"])} dos válidos; os argumentos existem para mover a reserva, não para inventar voto.</p>
""",
    )


def captura_flavio() -> float:
    return D["nacional"]["fenomeno"]["captura_flavio"]


def cap_sotaques() -> str:
    reg = F["reserva_regiao"]
    sp, mg, rj = RES["SP"], RES["MG"], RES["RJ"]
    sul = sum(RES[u]["reserva_eleitores"] for u in ("PR", "RS", "SC"))
    cartoes = [
        (
            "Nordeste",
            f"Reserva de {mil(reg.get('Nordeste', 0))}",
            [
                "Aqui ninguém gosta de desperdício. Voto em quem não chega é voto que fica pelo caminho.",
                "Lula precisa do Nordeste para fechar no 1º turno. Cada voto de Flávio aqui é o que segura a eleição aberta.",
                "Quem vota em ACM Neto, Ciro Gomes ou Raquel Lyra para governador e ainda não decidiu o presidente: a sua escolha estadual já diz o que você quer mudar.",
            ],
        ),
        (
            "São Paulo",
            f"Reserva de {mil(sp['reserva_eleitores'])}",
            [
                "São Paulo decide o tamanho da vitória. É o maior estoque de voto útil do país.",
                "Três em cada dez eleitores de Tarcísio ainda não votam em Flávio. É conversa de família, de trabalho, de grupo de mensagem.",
            ],
        ),
        (
            "Minas Gerais",
            f"Reserva de {mil(mg['reserva_eleitores'])}",
            [
                "Mineiro faz conta antes de gastar. O voto também: no 2º turno é Lula ou Flávio, então o voto do 1º turno tem que render.",
                "Quem vota em Cleitinho ou em Mateus Simões para governador tem a mesma escolha a fazer para presidente.",
            ],
        ),
        (
            "Rio de Janeiro",
            f"Reserva de {mil(rj['reserva_eleitores'])}",
            [
                "Papo reto: o 2º turno já está escolhido. O 1º turno é para dizer com quantos votos.",
                "Oito em cada dez eleitores de Douglas Ruas já votam em Flávio. Falta o resto do Rio.",
            ],
        ),
        (
            "Sul",
            f"Reserva de {mil(sul)}",
            [
                "No Sul o voto útil está mais adiantado. O que falta agora é comparecer: no Paraná e no Rio Grande do Sul, o eleitor que costuma faltar é mais lulista que o que sempre vota.",
                "Quem vota em Moro, Jorginho Mello ou Zucco já escolheu o lado. Leve esse voto até a urna para presidente também.",
            ],
        ),
        (
            "Centro-Oeste",
            f"Reserva de {mil(reg.get('Centro-Oeste', 0))}",
            [
                "Em Goiás o próprio eleitor de Caiado já está migrando. O agro não pode dividir o voto no 1º turno.",
                "No Distrito Federal, Cury e Caiado somam dois dígitos. É reserva de vizinho, de servidor, de comerciante.",
            ],
        ),
        (
            "Norte",
            f"Reserva de {mil(reg.get('Norte', 0))}",
            [
                f"Rondônia e Acre estão entre os estados mais à direita do país e entre os que menos compareceram em 2022 ({fmt(TSE['RO']['comparecimento_1t_pct'], 1)}% e {fmt(TSE['AC']['comparecimento_1t_pct'], 1)}% dos aptos). Aqui voto útil é comparecer.",
                "Manaus e Belém guardam o maior estoque de voto de direita do Norte. É onde a conversa rende.",
            ],
        ),
    ]
    html_c = "".join(
        f'<div class="arg regiao"><h3>{esc(t)}</h3><p class="sub">{esc(s)}</p><ul>{"".join(f"<li>{esc(x)}</li>" for x in xs)}</ul></div>'
        for t, s, xs in cartoes
    )
    return f"<h3>No sotaque de cada região</h3><div class='args'>{html_c}</div>"


def cap_ramos() -> str:
    ramos = [
        (
            "Quem empreende",
            "O seu voto decide juros, imposto e regra do jogo pelos próximos quatro anos. Só dois nomes chegam para decidir isso.",
        ),
        (
            "Quem trabalha no campo",
            "Safra não espera e voto também não. Dividir o voto do campo no 1º turno é deixar a cidade decidir sozinha.",
        ),
        (
            "Quem dirige por aplicativo ou entrega",
            "Você sabe que corrida parada não paga. Voto em quem não chega ao 2º turno é corrida parada.",
        ),
        (
            "Quem trabalha em segurança",
            "Segurança se decide em Brasília também. O voto que chega ao 2º turno é o que tem chance de virar política.",
        ),
        (
            "Quem vai à igreja",
            f"Entre os evangélicos, {fmt(_seg('Evangelica')['f2'])}% já escolhem Flávio no 2º turno e {fmt(_seg('Evangelica')['f1'])}% no 1º. Os {fmt(_seg('Evangelica')['reserva'])} pontos de distância estão dentro da própria igreja: é conversa de irmão para irmão.",
        ),
        (
            "Quem estuda ou acabou de começar a votar",
            f"Entre 16 e 24 anos, {fmt(_seg('16-24')['pode_mudar'])}% ainda podem mudar o voto. Quem decide por último decide o resultado.",
        ),
        (
            "Quem se aposentou",
            f"Acima de 60 anos o voto é o mais firme: {fmt(100 - _seg('60+')['pode_mudar'])}% já decidiram. Use essa firmeza para puxar a família.",
        ),
    ]
    itens = "".join(f"<li><b>{esc(t)}.</b> {esc(x)}</li>" for t, x in ramos)
    return f"<h3>Em cada ramo</h3><ul class='ramos'>{itens}</ul><p class='source'>Sugestões de abordagem, juízo editorial. Os números citados são do Datafolha de 15 a 17/09.</p>"


# ------------------------------------------------------------ resiliencia
def cap_kit() -> str:
    return section(
        "kit",
        "Voto que aguenta pancada",
        "Kit para a última semana: voto resiliente não é voto cego, é voto que exige prova",
        """
<p class="lead">A última semana de campanha costuma concentrar denúncias, montagens e boatos, e eles são desenhados para o eleitor que ainda pode mudar. O objetivo não é convencer o eleitor fiel; é fazer o eleitor de voto fraco desistir, anular ou ficar em casa. A resposta que funciona não é gritar mais alto. É ter feito a vacina antes.</p>
<div class="grid3">
<div class="card"><h3>Três perguntas antes de mudar o voto</h3><ol><li>Qual é o documento? Decisão, inquérito, processo, número.</li><li>Quem publicou, e quando o fato aconteceu?</li><li>Por que isso aparece agora, a poucos dias da urna?</li></ol><p>Se a notícia não responde às três, ela não é motivo para mudar um voto pensado para quatro anos.</p></div>
<div class="card"><h3>Não amplifique o ataque</h3><p>Compartilhar a acusação para desmenti-la leva a acusação a quem não a tinha visto. Responda com o dado do estado, com o número do voto definitivo, com o link da checagem. Não repita a manchete.</p></div>
<div class="card"><h3>Confira na fonte oficial</h3><p>O portal Fato ou Boato da Justiça Eleitoral e as agências de checagem publicam desmentidos de conteúdo eleitoral. Conteúdo sabidamente falso ou manipulado é proibido na propaganda (Res. TSE 23.610/2019, arts. 9º-A e 9º-C) e pode ser denunciado nos canais da Justiça Eleitoral.</p></div>
</div>
<h3>Frases para quem vota em Flávio e recebeu um ataque</h3>
<ul class="frases">
<li>Eu decidi olhando quatro anos, não quatro dias.</li>
<li>Denúncia sem documento na véspera não muda voto. Pede prova.</li>
<li>Se for verdade, a Justiça julga. Se for mentira, quem espalhou responde. Em qualquer caso, a escolha entre os dois projetos continua a mesma.</li>
<li>O voto de 2º turno eu já tinha. Só antecipei.</li>
<li>Quem quer que eu desista é quem ganha com a minha desistência.</li>
</ul>
<div class="callout"><b>Limite do kit.</b> Voto resiliente não significa ignorar fato provado. Se aparecer documento sério, ele merece ser lido. O que o kit protege é o voto contra o boato, a montagem e a acusação sem prova lançada quando não há tempo de resposta.</div>
""",
    )


# ------------------------------------------------------------ lei
def cap_lei() -> str:
    return section(
        "lei",
        "Dentro da lei",
        "Campanha voluntária: o que pode e o que não pode até o dia 4",
        """
<div class="grid2">
<div class="card ok"><h3>Pode</h3><ul>
<li>Conversar, publicar e compartilhar opinião na internet como pessoa física, sem pagar para impulsionar (Lei 9.504/1997, art. 57-C: impulsionamento pago é só de partido, coligação e candidato).</li>
<li>Distribuir material, fazer caminhada, carreata e passeata até as 22h do sábado, 3 de outubro (art. 39, § 9º).</li>
<li>No dia 4, manifestar a preferência em silêncio, com bandeira, broche, adesivo ou camiseta (art. 39-A).</li>
<li>Levar à seção quem mora com você, no seu carro, para votar (Lei 6.091/1974, art. 5º, III).</li>
</ul></div>
<div class="card nao"><h3>Não pode</h3><ul>
<li>Publicar conteúdo novo ou impulsionar propaganda no dia da eleição. O que foi publicado antes pode ficar no ar (Lei 9.504/1997, art. 39, § 5º, IV).</li>
<li>Boca de urna, aglomeração com propaganda e abordagem de eleitor no dia 4 (art. 39, § 5º).</li>
<li>Oferecer transporte, comida, dinheiro ou qualquer vantagem em troca de voto (Código Eleitoral, art. 299; Lei 6.091/1974).</li>
<li>Espalhar fato sabidamente falso, montagem ou deepfake, contra qualquer candidato (Res. TSE 23.610/2019).</li>
</ul></div>
</div>
<p class="source">Resumo informativo, não consultoria jurídica. Na dúvida, confira no portal do TSE ou com a coordenação jurídica da campanha. A campanha voluntária vale tanto quanto a campanha paga, e só vale se estiver dentro da regra.</p>
""",
    )
