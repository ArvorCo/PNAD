"""Capitulos de analise do mapa do voto util (docs/mapa_do_voto_util.html).

Todo numero do texto sai de `docs/assets/voto_util_092026.json`; nada e
digitado a mao. Os capitulos de campanha (argumentos, frases, fichas por
estado, lei) ficam em `voto_util_campanha.py`.
"""

from __future__ import annotations

import html
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = json.loads((ROOT / "docs/assets/voto_util_092026.json").read_text(encoding="utf-8"))


def _modulo(nome: str):
    if nome in sys.modules:
        return sys.modules[nome]
    spec = importlib.util.spec_from_file_location(nome, ROOT / "scripts" / f"{nome}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nome] = mod
    spec.loader.exec_module(mod)
    return mod


FIG = _modulo("voto_util_figuras")
fmt, sgn, mil = FIG.fmt, FIG.sgn, FIG.mil
QUAEST_PDF = "https://quaest.com.br/wp-content/uploads"


def esc(value) -> str:
    return html.escape(str(value))


def data_campo(campo: str | None) -> str:
    """'2026-09-14 a 2026-09-16' vira '14 a 16/09'; outros formatos passam intactos."""
    if not campo or campo[4:5] != "-":
        return campo or ""
    ini, fim = campo.split(" a ")[0].split("-"), campo.split(" a ")[-1].split("-")
    if ini[1] == fim[1]:
        return f"{ini[2]} a {fim[2]}/{fim[1]}"
    return f"{ini[2]}/{ini[1]} a {fim[2]}/{fim[1]}"


def pct(v, d=1) -> str:
    return f"{fmt(v, d)}%"


def section(slug: str, kicker: str, title: str, body: str, klass: str = "") -> str:
    k = f' class="{klass}"' if klass else ""
    return f'<section id="{slug}"{k}><div class="wrap"><p class="kicker">{esc(kicker)}</p><h2>{title}</h2>{body}</div></section>'


def figure(name: str, caption: str, wide: bool = False) -> str:
    svg = FIG.FIGURAS[name]()
    klass = "fig wide" if wide else "fig"
    return f'<figure class="{klass}" id="fig-{name}">{svg}<figcaption>{caption}</figcaption></figure>'


def table(headers: list[str], rows: list[list], label: str, klass: str = "") -> str:
    head = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
    body = "".join(
        "<tr>"
        + "".join(
            f'<th scope="row">{v}</th>' if i == 0 else f"<td>{v}</td>"
            for i, v in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )
    k = f" {klass}" if klass else ""
    return (
        f'<div class="table-scroll{k}" tabindex="0" role="region" aria-label="{esc(label)}">'
        f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def quaest_link(uf: str, pagina: int | None, rotulo: str | None = None) -> str:
    e = D["estados"].get(uf)
    if not e or not e.get("url"):
        return ""
    alvo = f"{e['url']}#page={pagina}" if pagina else e["url"]
    return f'<a href="{alvo}">{esc(rotulo or ("p." + str(pagina)))}</a>'


# ------------------------------------------------------------------ fatos
EST = D["estados"]
RES = D["auxiliar"]["reserva_uf"]
TSE = D["tse_uf"]
MED = D["modelos"]["media"]
CASAS = D["auxiliar"].get("casas", ["quaest", "realtime"])
NOME_CASA = {"quaest": "Quaest", "realtime": "Real Time", "atlas": "AtlasIntel"}
MODS = {c: D["modelos"][c] for c in CASAS}
MQ, MR = MODS["quaest"], MODS["realtime"]


def grupos(valores: dict) -> dict:
    """F, L, terceira via de direita, indecisos e branco de uma lista de 1o turno."""
    v = {k: (x or 0) for k, x in (valores or {}).items()}
    tdir = sum(
        v.get(k, 0)
        for k in (
            "Cury",
            "Caiado",
            "Renan",
            "Zema",
            "Avalanche",
            "Marçal",
            "Clariana",
            "Grassi",
            "Outros",
        )
    )
    return {
        "F": v.get("Flávio", 0),
        "L": v.get("Lula", 0),
        "Tdir": tdir,
        "I": v.get("Indecisos", 0),
        "B": v.get("Branco/nulo", 0),
    }


def casas_txt() -> str:
    nomes = [NOME_CASA[c] for c in CASAS]
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


def lim_faixa(chave: str) -> tuple[float, float]:
    vals = [
        m["limiares"][chave] for m in MODS.values() if m["limiares"][chave] is not None
    ]
    return min(vals), max(vals)


def p_faixa(cenario: str, chave: str) -> str:
    return faixa_lista(
        [
            next(c for c in m["cenarios"] if c["nome"] == cenario)[chave]
            for m in MODS.values()
        ]
    )


def faixa_lista(vals: list[float]) -> str:
    x, y = round(100 * min(vals)), round(100 * max(vals))
    return f"{x}%" if x == y else f"{x}% a {y}%"


FEN = D["nacional"]["fenomeno"]
ALVO = D["auxiliar"]["alvo_nacional"]
B22 = D["tse_brasil_2022"]


def cen(nome: str, modelo: dict | None = None) -> dict:
    return next(c for c in (modelo or MED)["cenarios"] if c["nome"] == nome)


def _agregador() -> dict:
    return json.loads(
        (ROOT / "docs/assets/reponderacao_pnad.json").read_text(encoding="utf-8")
    )


def _quaest_junho() -> dict:
    """Quaest de junho, a onda em que esta casa falou em voto util reprimido."""
    p = next(x for x in _agregador()["pesquisas"] if x["id"] == "quaest_2026-06-08")
    return {
        "flavio": p["publicado"]["1t"]["flavio"],
        "flavio_2t": p["publicado"]["2t"]["flavio"],
        "divulgacao": p.get("divulgacao"),
    }


def _maior_terceira() -> dict:
    """Maior candidatura de terceira via na ultima onda nacional de cada instituto."""
    ult: dict[str, dict] = {}
    for p in sorted(_agregador()["pesquisas"], key=lambda x: x["campo"]["fim"]):
        if p["campo"]["fim"] >= "2026-09-15" and p["publicado"].get("1t"):
            ult[p["instituto"]] = p
    melhor = {"valor": 0.0}
    for inst, p in ult.items():
        for k, v in p["publicado"]["1t"].items():
            if k in ("lula", "flavio", "branco_nulo", "indecisos", "outros"):
                continue
            if v > melhor["valor"]:
                melhor = {"valor": v, "candidato": k, "instituto": inst}
    return melhor


def _fatos() -> dict:
    t1, t2 = B22["t1"], B22["t2"]
    ondas = D["nacional"]["ondas"]
    quaest = [o for o in ondas if o["instituto"] == "Quaest"]
    atlas = [
        o for o in ondas if o["instituto"] == "AtlasIntel" and o["fim"] >= "2026-08-26"
    ]
    gov_end = gov_lula = 0
    for e in EST.values():
        for g in e["indicadores"].get("governador_cruzamento", []):
            if g["campo"] in ("direita", "centro-direita", "centro"):
                gov_end += g["enderecavel_eleitores"] or 0
                gov_lula += round(e["peso"] * (g["cruzado_lula_pp"] or 0) / 100)
    por_regiao: dict[str, int] = {}
    for uf, r in RES.items():
        reg = TSE[uf]["regiao"]
        por_regiao[reg] = por_regiao.get(reg, 0) + r["reserva_eleitores"]
    return {
        "lula_1t_2022": 100 * t1["lula"] / t1["validos"],
        "bolso_1t_2022": 100 * t1["bolsonaro"] / t1["validos"],
        "bolso_2t_2022": 100 * t2["bolsonaro"] / t2["validos"],
        "ganho_bolso_2022": t2["bolsonaro"] - t1["bolsonaro"],
        "ganho_lula_2022": t2["lula"] - t1["lula"],
        "ciro_tebet_2022": t1["ciro"] + t1["tebet"],
        "faltaram_lula_2022": t1["validos"] / 2 + 1 - t1["lula"],
        "bn_2022": 100 * (t1["brancos"] + t1["nulos"]) / t1["comparecimento"],
        "abst_2022": 100 * t1["abstencao"] / t1["aptos"],
        "reserva_total": sum(r["reserva_eleitores"] for r in RES.values()),
        "reserva_regiao": por_regiao,
        "quaest_ultima": quaest[-1],
        "quaest_inicio_set": next(o for o in quaest if o["fim"] >= "2026-09-01"),
        "quaest_junho": _quaest_junho(),
        "maior_terceira": _maior_terceira(),
        "atlas_ini": atlas[0],
        "atlas_fim": atlas[-1],
        "gov_enderecavel": gov_end,
        "gov_cruzado_lula": gov_lula,
    }


F = _fatos()


# ------------------------------------------------------------------ hero
def hero_stats() -> str:
    hoje = cen("Hoje, eleitor provável")
    completo = cen("Voto útil completo")
    so_lula = cen("Só Lula consolida")
    lim, lim_hi = lim_faixa("primeiro_lugar_so_direita")
    return f"""
<div class="hero-stats">
<div><b>{fmt(100 * FEN["captura_flavio"])}%</b><span>de tudo o que Flávio e Lula ganharam desde 26/08, em oito institutos, foi para Flávio</span></div>
<div><b>{fmt(F["reserva_total"] / 1e6, 1)} mi</b><span>de eleitores já escolhem Flávio no 2º turno e ainda não no 1º</span></div>
<div><b>{fmt(100 * lim)} a {fmt(100 * lim_hi)}%</b><span>dessa reserva basta para Flávio terminar o 1º turno na frente</span></div>
<div><b>{pct(so_lula["lula_validos"])}</b><span>é onde Lula chega se só a esquerda fizer voto útil. Hoje ele tem {pct(hoje["lula_validos"])}; com a direita inteira, Flávio vai a {pct(completo["flavio_validos"])}</span></div>
</div>"""


# ------------------------------------------------------------------ tese
def cap_tese() -> str:
    hoje = cen("Hoje, eleitor provável")
    completo = cen("Voto útil completo")
    so_lula = cen("Só Lula consolida")
    dois = cen("Os dois lados consolidam")
    q, q0, qj = F["quaest_ultima"], F["quaest_inicio_set"], F["quaest_junho"]
    return section(
        "tese",
        "A tese",
        "O voto útil deixou de ser opção. Virou voto necessário.",
        f"""
<p class="lead">Na reta final, a terceira via está secando e quase tudo o que sai dela vai para um lado. Desde 26 de agosto, somando oito institutos nacionais, Flávio ganhou {fmt(FEN["soma_delta_flavio"], 1)} pontos e Lula ganhou {fmt(FEN["soma_delta_lula"], 1)}. De cada dez pontos que mudaram de dono, {fmt(10 * FEN["captura_flavio"])} foram para Flávio. É o fenômeno que esta casa descreveu em junho, quando a Quaest mostrava Flávio com {fmt(qj["flavio"])}% no 1º turno e {fmt(qj["flavio_2t"])}% no 2º, e chamamos os {fmt(qj["flavio_2t"] - qj["flavio"])} pontos de diferença de voto útil reprimido.</p>
<p>O reprimido começou a sair. Em 1º de setembro a Quaest tinha Flávio com {fmt(q0["flavio"])}% no 1º turno e {fmt(q0["flavio_2t"])}% no 2º: {fmt(q0["flavio_2t"] - q0["flavio"])} pontos de distância. Em 20 de setembro, {fmt(q["flavio"])}% e {fmt(q["flavio_2t"])}%: {fmt(q["flavio_2t"] - q["flavio"])} pontos. Andou {fmt((q0["flavio_2t"] - q0["flavio"]) - (q["flavio_2t"] - q["flavio"]))}, faltam {fmt(q["flavio_2t"] - q["flavio"])}. E nos estados, que é onde o voto mora, a mesma conta soma <strong>{fmt(F["reserva_total"] / 1e6, 1)} milhões de eleitores</strong> que já escolheram Flávio contra Lula e ainda não o escolheram no 1º turno.</p>
<p>Este mapa diz onde estão essas pessoas, estado por estado, e por que o voto delas deixou de ser opcional. O modelo de cenário no fim da página, calibrado pela média das pesquisas nacionais da última semana e ponderado por quem de fato comparece, mostra quatro coisas:</p>
<ol class="numeros">
<li><b>Hoje</b>, entre quem vota, Lula tem {pct(hoje["lula_validos"])} dos votos válidos e Flávio {pct(hoje["flavio_validos"])}.</li>
<li><b>Se só a esquerda fizer voto útil</b>, Lula vai a {pct(so_lula["lula_validos"])}, com faixa até {pct(so_lula["lula_p90"])}. Sem pesquisas calibradas pela média nacional, só com os estados, chega a {pct(cen("Só Lula consolida", D["modelos"]["media_bruto"])["lula_validos"])}. A eleição pode acabar no 1º turno por um fio, como quase acabou em 2022.</li>
<li><b>Se os dois lados fizerem</b>, o 1º turno empata: {pct(dois["flavio_validos"])} a {pct(dois["lula_validos"])}. Quem chega na frente depende de quem mobiliza melhor.</li>
<li><b>Se só a direita fizer</b>, Flávio termina o 1º turno com {pct(completo["flavio_validos"])} dos válidos e {fmt(completo["margem"], 1)} pontos de vantagem, com faixa até {pct(completo["flavio_p90"])}.</li>
</ol>
<div class="callout"><b>O que este mapa é.</b> Leitura de {len(EST)} relatórios estaduais da Quaest lidos página a página, {len(D["realtime"])} relatórios estaduais da Real Time Big Data, {len(D.get("atlas", {}))} da AtlasIntel e {len([x for x in D.get("outros_estaduais", []) if "Atlas" not in x["instituto"]])} de outros institutos, as pesquisas nacionais registradas no TSE e o resultado oficial de 2022. O capítulo de campanha é juízo editorial declarado, a serviço de uma candidatura, com o número ao lado de cada argumento. O modelo é cenário condicional, não previsão e não pesquisa: ele não entrevista ninguém, só refaz a conta das pesquisas registradas sob hipóteses explícitas.</div>
""",
    )


# ------------------------------------------------------------------ fenomeno
def cap_fenomeno() -> str:
    a0, a1 = F["atlas_ini"], F["atlas_fim"]
    linhas = []
    for r in FEN["institutos"]:
        linhas.append(
            [
                esc(r["instituto"]),
                f"{r['de'][8:10]}/{r['de'][5:7]} a {r['ate'][8:10]}/{r['ate'][5:7]}",
                f"{fmt(r['terceira_de'], 1)} → {fmt(r['terceira_ate'], 1)}",
                sgn(r["delta_flavio"], 1),
                sgn(r["delta_lula"], 1),
                (
                    f"{fmt(100 * r['captura_flavio'])}%"
                    if r["captura_flavio"] is not None
                    else "n/d"
                ),
            ]
        )
    contra = [
        r
        for r in FEN["institutos"]
        if r["delta_terceira"] >= 0
        or (r["captura_flavio"] is not None and r["captura_flavio"] < 0.5)
    ]
    contra_txt = ", ".join(r["instituto"] for r in contra) or "nenhum"
    return section(
        "fenomeno",
        "O fenômeno",
        "A terceira via está secando, e sete de cada dez pontos vão para Flávio",
        f"""
<p class="lead">A AtlasIntel é o caso mais nítido. Em {a0["fim"][8:10]}/{a0["fim"][5:7]} ela media {fmt(a0["terceira"], 1)}% para todos os candidatos fora da polarização; em {a1["fim"][8:10]}/{a1["fim"][5:7]}, {fmt(a1["terceira"], 1)}%. No mesmo intervalo, Flávio foi de {fmt(a0["flavio"], 1)}% para {fmt(a1["flavio"], 1)}%, e Lula de {fmt(a0["lula"], 1)}% para {fmt(a1["lula"], 1)}%.</p>
{figure("fenomeno", "Primeira onda de cada instituto a partir de 26/08, quando todas as candidaturas atuais já estavam no cartão, contra a mais recente. Terceira via é a soma dos votos em candidatos que não são Lula nem Flávio. Fonte: relatórios registrados no TSE, base do agregador Arvor.")}
{table(["Instituto", "Período", "Terceira via", "Flávio", "Lula", "Parte de Flávio no ganho dos dois"], linhas, "Queda da terceira via por instituto")}
<p>Somando os oito institutos com duas ondas no período, a terceira via perdeu {fmt(-FEN["soma_delta_terceira"], 1)} pontos. Flávio ganhou {fmt(FEN["soma_delta_flavio"], 1)} e Lula {fmt(FEN["soma_delta_lula"], 1)}. A razão de captura, ganho de Flávio sobre o ganho somado dos dois, é de <strong>{fmt(100 * FEN["captura_flavio"])}%</strong>.</p>
<div class="callout contra"><b>O que contraria a tese, com o mesmo destaque.</b> O movimento não é uniforme. Onde o instituto não mostra queda da terceira via ou mostra captura abaixo de metade para Flávio: {esc(contra_txt)}. E Lula também cresce em quase todos: o voto útil está acontecendo dos dois lados, o que é exatamente o risco que o capítulo do modelo mede.</div>
""",
    )


# ------------------------------------------------------------------ matematica
def cap_matematica() -> str:
    return section(
        "matematica",
        "A regra do jogo",
        "Branco e nulo não contam. E é por isso que eles ajudam quem está na frente.",
        f"""
<p class="lead">A Constituição, no art. 77, § 2º, diz que é eleito no 1º turno o candidato que obtiver a maioria absoluta dos votos, <em>não computados os em branco e os nulos</em>. O denominador é o voto válido. Cada branco, cada nulo e cada ausência encolhe o denominador e baixa a régua de 50% para quem lidera.</p>
<div class="grid3">
<div class="card"><h3>Branco e nulo não anulam eleição</h3><p>A anulação prevista no art. 224 do Código Eleitoral trata de votos anulados por fraude ou irregularidade, não do voto nulo que o eleitor digita. O próprio TSE desmente esse boato a cada eleição. Mais nulos não cancelam nada: só facilitam o 1º turno de quem já está na frente.</p></div>
<div class="card"><h3>Branco não vai para o líder</h3><p>Também é mito. O voto branco não é somado a ninguém. O efeito é indireto e pior: ele sai do denominador. Se Lula tem 47 de cada 100 eleitores que comparecem e 6 desses 100 votam branco ou nulo, Lula tem 47 de 94 votos válidos: exatamente metade. Um voto a mais e a eleição acaba.</p></div>
<div class="card"><h3>Em 2022 faltou pouco</h3><p>Lula teve {pct(F["lula_1t_2022"], 2)} dos válidos no 1º turno de 2022. Faltaram {fmt(F["faltaram_lula_2022"] / 1e6, 2)} milhão de votos para acabar ali. Brancos e nulos somaram {pct(F["bn_2022"], 1)} de quem compareceu, e {pct(F["abst_2022"], 1)} dos aptos não foram votar.</p></div>
</div>
<h3>O voto útil que chegou tarde em 2022</h3>
<p>Entre o 1º e o 2º turno de 2022, Bolsonaro ganhou {fmt(F["ganho_bolso_2022"] / 1e6, 1)} milhões de votos; Lula, {fmt(F["ganho_lula_2022"] / 1e6, 1)} milhões. Bolsonaro saiu de {pct(F["bolso_1t_2022"], 1)} para {pct(F["bolso_2t_2022"], 1)} dos válidos. Boa parte desse voto existia no 1º turno, só não estava com ele: Ciro e Tebet somaram {fmt(F["ciro_tebet_2022"] / 1e6, 1)} milhões de votos. Chegou depois, quando a eleição ficou binária, tarde demais para mudar o 1º turno, que terminou com Lula {fmt(F["lula_1t_2022"] - F["bolso_1t_2022"], 1)} pontos à frente. Em 2026 a mesma reserva existe, e o 1º turno ainda não aconteceu.</p>
""",
    )


# ------------------------------------------------------------------ mapa
def nota_terceiros() -> str:
    """Frase sobre UFs sem Quaest nem Real Time, gerada a partir das bases."""
    partes = []
    for uf, r in sorted(RES.items()):
        if r.get("estimado"):
            partes.append(
                f"{NOMES_UF.get(uf, uf)} não tem pesquisa estadual com presidente no período e entra por estimativa regional sobre o resultado de 2022."
            )
        elif r["casas"] and all(
            c["casa"] not in ("quaest", "realtime") for c in r["casas"]
        ):
            c = r["casas"][0]
            partes.append(
                f"{NOMES_UF.get(uf, uf)}, sem Quaest nem Real Time, entra pelo {c['casa']}, campo de {esc(data_campo(c.get('campo')))}."
            )
    return " ".join(partes)


NOMES_UF = {
    "PI": "O Piauí",
    "SE": "Sergipe",
    "AM": "O Amazonas",
    "RO": "Rondônia",
    "PB": "A Paraíba",
}


def cap_mapa() -> str:
    linhas = []
    for uf, r in sorted(RES.items(), key=lambda kv: -kv[1]["reserva_eleitores"]):
        casas = {c["casa"]: c for c in r["casas"]}

        def cel(c):
            if not c:
                return "n/d"
            return f"{fmt(c['F'])} → {fmt(c['F2'])}"

        linhas.append(
            [
                f"{uf} <span class='sub'>{esc(TSE[uf]['regiao'])}</span>",
                mil(r["reserva_eleitores"]),
                fmt(r["reserva_pp"], 1),
                *[cel(casas.get(c)) for c in CASAS],
                mil(r["votantes_esperados"]),
                (
                    "estimativa"
                    if r.get("estimado")
                    else ", ".join(
                        f"{esc(c['casa'])}: {cel(c)}"
                        for c in r["casas"]
                        if c["casa"] not in CASAS
                    )
                ),
            ]
        )
    reg = F["reserva_regiao"]
    ordem = sorted(reg.items(), key=lambda kv: -kv[1])
    reg_txt = "; ".join(f"{k}, {mil(v)}" for k, v in ordem)
    top3 = sorted(RES.items(), key=lambda kv: -kv[1]["reserva_eleitores"])[:3]
    top3_soma = sum(r["reserva_eleitores"] for _, r in top3)
    norte_ne = reg.get("Norte", 0) + reg.get("Nordeste", 0)
    comparacao = (
        f"O Sudeste sozinho ({mil(reg['Sudeste'])}) tem mais reserva do que Norte e Nordeste juntos ({mil(norte_ne)})."
        if reg.get("Sudeste", 0) > norte_ne
        else f"Norte e Nordeste somam {mil(norte_ne)}, contra {mil(reg.get('Sudeste', 0))} do Sudeste."
    )
    return section(
        "mapa",
        "O mapa",
        f"{fmt(F['reserva_total'] / 1e6, 1)} milhões de eleitores que já votam em Flávio no 2º turno",
        f"""
<p class="lead">A reserva de cada estado é a diferença entre o voto de Flávio no 2º turno e no 1º turno, <strong>na mesma amostra</strong>: mesmo questionário, mesmo entrevistado, mesmo peso. Não é suposição sobre para onde vai a terceira via; é gente que o próprio instituto mediu escolhendo Flávio contra Lula e escolhendo outro nome, ou ninguém, no 1º turno. Multiplicada pelos eleitores que compareceram em 2022, vira gente de carne e osso.</p>
<div class="mapa-grid">
{figure("mapa_reserva", "Média das casas que mediram cada estado. Eleitor provável: pesos do cruzamento por comparecimento da Quaest. Passe o ponteiro sobre o estado para ver o número exato e a fonte.")}
{figure("ranking_reserva", "Eleitores esperados = eleitorado de 2026 (TSE, julho) vezes o comparecimento do 1º turno de 2022 no estado.")}
</div>
<p>Por região: {reg_txt}. Os três maiores estados, {", ".join(uf for uf, _ in top3)}, guardam {mil(top3_soma)}, ou {fmt(100 * top3_soma / F["reserva_total"])}% de toda a reserva. {comparacao}</p>
{table(["UF", "Reserva", "Pontos", *[f"{NOME_CASA[c]} 1º → 2º" for c in CASAS], "Votantes esperados", "Outra casa"], linhas, "Reserva de 2º turno por estado")}
<p class="source">Quaest: onda de 19 a 24/09 em 12 estados e de 20 a 28/08 nos demais (neste caso, somado o movimento médio de agosto para setembro medido nos estados que a Quaest ouviu duas vezes). Real Time Big Data: pesquisas estaduais de 29/08 a 24/09. {nota_terceiros()} Fontes completas no fim da página.</p>
""",
    )


# ------------------------------------------------------------------ terceira via
NOMES_TV = ("Cury", "Caiado", "Zema", "Renan", "Avalanche")


def _tv_uf(uf: str) -> tuple[dict, str] | None:
    e = EST.get(uf)
    if e:
        v = e["pres_1t"]["valores"]
        if sum(1 for k in NOMES_TV if k in v) >= 3:
            return v, "Quaest"
    rt = D["realtime"].get(uf)
    if rt:
        return rt["valores"], "Real Time"
    return None


def cap_terceira() -> str:
    linhas = []
    for uf in sorted(TSE, key=lambda u: -RES[u]["votantes_esperados"]):
        r = _tv_uf(uf)
        if not r:
            continue
        v, casa = r
        tot = sum(v.get(k, 0) for k in NOMES_TV) + v.get("Marçal", 0)
        cury_def = (
            EST.get(uf, {}).get("definitiva", {}).get("candidatos", {}).get("Cury")
            or {}
        ).get("definitiva")
        linhas.append(
            [
                uf,
                *[fmt(v.get(k, 0)) for k in NOMES_TV[:4]],
                fmt(tot),
                mil(RES[uf]["votantes_esperados"] * tot / 100),
                (f"{fmt(cury_def)}%" if cury_def is not None else ""),
                casa,
            ]
        )
    go = EST["GO"]
    sv = go["pres_1t"]["serie_valores"]
    caiado_ini, caiado_fim = sv[0]["valores"].get("Caiado"), sv[-1]["valores"].get(
        "Caiado"
    )
    flavio_ini, flavio_fim = sv[0]["valores"].get("Flávio"), sv[-1]["valores"].get(
        "Flávio"
    )
    go_txt = ""
    cx = go.get("pres_x_identificacao")
    if cx and "Direita não bolsonarista" in cx["colunas"]:
        col = cx["colunas"]["Direita não bolsonarista"]
        ant = col.get("anterior") or {}
        go_txt = (
            f" Entre os goianos que se dizem de direita mas não bolsonaristas, Flávio foi de {fmt(ant.get('grupos', {}).get('F'))}% para "
            f"{fmt(col['grupos']['F'])}% em um mês."
        )
    cury_defs = [
        (uf, e["definitiva"]["candidatos"]["Cury"]["definitiva"])
        for uf, e in EST.items()
        if "Cury" in e["definitiva"]["candidatos"]
        and e["definitiva"]["candidatos"]["Cury"]["definitiva"] is not None
    ]
    cury_med = sum(v for _, v in cury_defs) / len(cury_defs) if cury_defs else None
    fl_defs = [
        e["definitiva"]["candidatos"]["Flávio"]["definitiva"]
        for e in EST.values()
        if "Flávio" in e["definitiva"]["candidatos"]
    ]
    fl_med = sum(v for v in fl_defs if v is not None) / len(
        [v for v in fl_defs if v is not None]
    )
    return section(
        "terceira",
        "Oportunidade 1",
        "A terceira via: quem ainda está lá e quão firme está",
        f"""
<p class="lead">Na última pesquisa nacional de cada instituto, nenhuma candidatura de terceira via passa de um dígito: o maior número é {fmt(F["maior_terceira"]["valor"], 1)}%. O voto que ainda está nelas é o mais volátil da eleição: onde a Quaest pergunta, {fmt(cury_med)}% do eleitor de Augusto Cury, em média, diz que o voto é definitivo, contra {fmt(fl_med)}% do eleitor de Flávio. Quase metade do eleitor de Cury diz, com todas as letras, que pode mudar.</p>
<p>O caso de Goiás mostra a velocidade. Ronaldo Caiado, ex-governador e candidato a presidente, tinha {fmt(caiado_ini)}% no próprio estado em agosto. Em 24 de setembro, {fmt(caiado_fim)}%. Flávio subiu de {fmt(flavio_ini)}% para {fmt(flavio_fim)}% no mesmo intervalo.{go_txt}</p>
{table(["UF", "Cury", "Caiado", "Zema", "Renan", "Terceira via de direita", "Eleitores", "Eleitor de Cury com voto definitivo", "Fonte"], linhas, "Terceira via por estado")}
<p class="source">Percentuais do 1º turno presidencial na lista completa de candidatos. Eleitores = votantes esperados vezes o percentual. A coluna de voto definitivo só existe onde a Quaest publicou o recorte por candidato.</p>
""",
    )


# ------------------------------------------------------------------ governadores
def _gov_linhas() -> list[tuple[str, dict]]:
    out = []
    for uf, e in EST.items():
        for g in e["indicadores"].get("governador_cruzamento", []):
            if (
                g["campo"] in ("direita", "centro-direita", "centro")
                and g["voto_governador"] >= 5
            ):
                out.append((uf, g))
    out.sort(key=lambda x: -(x[1]["enderecavel_eleitores"] or 0))
    return out


def cap_governadores() -> str:
    linhas = _gov_linhas()
    destaques = []
    for uf, g in linhas[:6]:
        antes = g.get("flavio_entre_eleitores_antes")
        mov = (
            f", eram {fmt(antes)}% na rodada anterior"
            if antes is not None and antes != g["flavio_entre_eleitores"]
            else ""
        )
        destaques.append(
            f"<li><b>{esc(g['nome'])} ({esc(uf)})</b>: {fmt(g['voto_governador'])}% para governador. Entre os eleitores dele, {fmt(g['flavio_entre_eleitores'])}% votam Flávio{mov}, "
            f"{fmt(g['lula_entre_eleitores'])}% votam Lula e {fmt(g['fora_entre_eleitores'])}% estão na terceira via, indecisos ou em branco: <strong>{mil(g['enderecavel_eleitores'])}</strong> de eleitores.</li>"
        )
    sem_cx = []
    for uf, e in sorted(EST.items()):
        i = e["indicadores"]
        if i.get("governador_cruzamento") or not i.get("governador_nao_esquerda"):
            continue
        g = i["governador_nao_esquerda"]
        sem_cx.append(
            [
                uf,
                f"{esc(g['nome'])} ({esc(g['partido'])})",
                fmt(g["valor"]),
                fmt(e["pres_1t"]["grupos"]["F"]),
                sgn(i["vao_governador_pp"]),
            ]
        )
    subiram = [
        (uf, g)
        for uf, g in linhas
        if g.get("flavio_entre_eleitores_antes") is not None
        and g["flavio_entre_eleitores"] > g["flavio_entre_eleitores_antes"]
    ]
    caiu = [
        (uf, g)
        for uf, g in linhas
        if g.get("flavio_entre_eleitores_antes") is not None
        and g["flavio_entre_eleitores"] < g["flavio_entre_eleitores_antes"]
    ]
    return section(
        "governadores",
        "Oportunidade 2",
        "O eleitor do governador de direita que ainda não é eleitor de Flávio",
        f"""
<p class="lead">Nas doze ondas de setembro, a Quaest cruzou o voto para presidente com o voto para governador. É o dado mais útil da eleição para quem faz campanha de rua: diz, dentro do eleitorado de cada candidato a governador, quantos já votam em Flávio e quantos ainda não. Somados os candidatos fora da esquerda, são <strong>{fmt(F["gov_enderecavel"] / 1e6, 1)} milhões de eleitores</strong> que votam no governador de direita ou de centro e, para presidente, estão na terceira via, indecisos ou em branco. Outros {fmt(F["gov_cruzado_lula"] / 1e6, 1)} milhões votam no mesmo governador e em Lula.</p>
{figure("governadores", "Cruzamento presidente (1º turno) por governador (1º turno), rodada de 19 a 24/09. Só candidatos fora da esquerda com 5% ou mais. Coluna da direita: eleitores do governador que não votam nem em Flávio nem em Lula. Classificação de campo declarada no fim da página.", wide=True)}
<ul class="destaques">{"".join(destaques)}</ul>
<p>O movimento dentro desses eleitorados é o fenômeno em tamanho real. Em {len(subiram)} dos {len(subiram) + len(caiu)} governadores com duas rodadas, a parte que vota em Flávio subiu. {"Caiu em " + ", ".join(esc(g["nome"]) for _, g in caiu) + "." if caiu else ""}</p>
<div class="callout"><b>O eleitor mais difícil vale o dobro.</b> Onde o eleitor do governador de direita vota Lula (ACM Neto na Bahia, Ciro Gomes no Ceará, Raquel Lyra em Pernambuco), cada conversão tira um voto de Lula e dá um a Flávio: move a margem em dois. É a conversa mais difícil e a mais valiosa, e só funciona com o argumento do estado, não com o nacional.</div>
<h3>Estados sem o cruzamento</h3>
<p>Nas ondas de agosto a Quaest não cruzou presidente com governador. Ali só dá para medir o vão: o melhor candidato fora da esquerda ao governo menos o voto de Flávio no mesmo relatório. É teto endereçável, não previsão, porque votar num governador não obriga ninguém a nada para presidente.</p>
{table(["UF", "Candidato fora da esquerda mais votado", "Governo", "Flávio", "Vão"], sem_cx, "Vão entre governador e Flávio nos estados sem cruzamento")}
""",
    )


# ------------------------------------------------------------------ senado
def cap_senado() -> str:
    linhas = []
    for uf, e in sorted(EST.items(), key=lambda kv: -RES[kv[0]]["votantes_esperados"]):
        sen = e.get("senado") or {}
        cands = [c for c in sen.get("candidatos", []) if c["valor"] is not None]
        if not cands:
            continue
        direita = [c for c in cands if c["campo"] in ("direita", "centro-direita")][:3]
        soma = sum(
            c["valor"] for c in cands if c["campo"] in ("direita", "centro-direita")
        )
        linhas.append(
            [
                uf,
                "; ".join(
                    f"{esc(c['nome'])} ({esc(c['partido'])}) {fmt(c['valor'])}"
                    for c in direita
                )
                or "n/d",
                fmt(soma),
                fmt(e["pres_1t"]["grupos"]["F"]),
                sgn(soma - e["pres_1t"]["grupos"]["F"]),
            ]
        )
    return section(
        "senado",
        "Oportunidade 3",
        "O Senado que a direita quer eleger precisa de um presidente para funcionar",
        f"""
<p class="lead">Em 2026 cada estado elege dois senadores, dois terços da Casa. O eleitor de direita que escolhe com cuidado os dois nomes para o Senado e deixa a Presidência para depois está montando uma oposição, não um governo. A tabela compara, estado a estado, a soma dos candidatos de direita e centro-direita ao Senado, na média das duas vagas, com o voto de Flávio na mesma amostra.</p>
{table(["UF", "Principais nomes de direita ao Senado", "Direita no Senado", "Flávio", "Diferença"], linhas, "Senado de direita contra Flávio por estado")}
<p class="source">Quaest, intenção de voto estimulada para senador, média das duas vagas. Classificação por partido, com as exceções declaradas no fim da página. Onde a diferença é positiva, há eleitor que vota em senador de direita e ainda não vota em Flávio; onde é negativa, Flávio já puxa mais que a chapa ao Senado.</p>
<div class="callout"><b>Como usar.</b> O argumento não é contra o candidato ao Senado; é a favor do casamento. Senador de direita com presidente de direita aprova. Senador de direita com presidente de esquerda obstrui, e obstrução não entrega segurança, reforma nem corte de imposto.</div>
""",
    )


# ------------------------------------------------------------------ eleitor provavel
def _alavanca_comparecimento() -> tuple[int, list[tuple[str, int]]]:
    alvo = sorted((t["comparecimento_1t_pct"] for t in TSE.values()), reverse=True)[4]
    total, linhas = 0, []
    for uf, t in TSE.items():
        if t["bolsonaro_2t_validos"] <= 55:
            continue
        extra = max(0.0, alvo - t["comparecimento_1t_pct"]) / 100 * t["eleitorado_2026"]
        liquido = (
            extra
            * (1 - t["branco_nulo_1t_pct_comparecimento"] / 100)
            * (t["bolsonaro_2t_validos"] - t["lula_2t_validos"])
            / 100
        )
        total += round(liquido)
        linhas.append((uf, round(liquido)))
    linhas.sort(key=lambda x: -x[1])
    return total, linhas


def cap_provavel() -> str:
    hoje_todos, hoje_lv = cen("Hoje, todos os entrevistados"), cen(
        "Hoje, eleitor provável"
    )
    medidos = {uf: e for uf, e in EST.items() if e.get("lv")}
    pro_f = [
        uf
        for uf, e in medidos.items()
        if (e["lv"]["outros"]["F"] - e["lv"]["outros"]["L"])
        > (e["lv"]["sempre"]["F"] - e["lv"]["sempre"]["L"])
    ]
    pro_l = [uf for uf in medidos if uf not in pro_f]
    direita = [t for t in TSE.values() if t["bolsonaro_2t_validos"] > 55]
    esquerda = [t for t in TSE.values() if t["bolsonaro_2t_validos"] < 40]

    def media(xs):
        return sum(t["comparecimento_1t_pct"] * t["eleitorado_2026"] for t in xs) / sum(
            t["eleitorado_2026"] for t in xs
        )

    total, linhas = _alavanca_comparecimento()
    top = ", ".join(f"{uf} ({mil(v)})" for uf, v in linhas[:5])
    return section(
        "provavel",
        "Oportunidade 4",
        "Quem de fato vota: o eleitor provável não é trunfo automático",
        f"""
<p class="lead">A Quaest pergunta, em doze estados, se o entrevistado sempre vota, se já deixou de votar e se vai votar agora. Cruzando essa resposta com o voto, dá para pesar cada eleitor pela chance de comparecer. O resultado nacional é quase neutro e merece ser dito sem enfeite: entre todos os entrevistados, Lula tem {pct(hoje_todos["lula_validos"])} dos válidos; entre os eleitores prováveis, {pct(hoje_lv["lula_validos"])}. O comparecimento não entrega a eleição para ninguém.</p>
{figure("provavel", "Quaest, presidente 1º turno por comparecimento às urnas, rodada de 19 a 24/09. Ponto cheio: quem se diz eleitor que sempre vota e vai votar. Ponto vazio: quem já deixou de votar ou diz que não vai.")}
<p>O que muda é a geografia. Onde o eleitor que falta é mais favorável a Flávio que o eleitor fiel ({", ".join(pro_f)}), levar gente à urna rende voto. Onde o eleitor que falta é mais lulista ({", ".join(pro_l)}), a tarefa é outra: garantir que o eleitor fiel de direita não falte. E há um achado que contraria o senso comum: no Nordeste, o eleitor que costuma faltar é bem menos lulista que o eleitor fiel. Levá-lo à urna diminui a vantagem de Lula exatamente onde ela é maior.</p>
<h3>A abstenção de 2022 pesou mais na direita</h3>
<p>Em 2022, os estados onde Bolsonaro passou de 55% dos válidos no 2º turno tiveram comparecimento médio de {pct(media(direita), 1)} no 1º turno; os estados onde ele ficou abaixo de 40%, {pct(media(esquerda), 1)}. Se os estados de direita tivessem comparecido como os cinco estados que mais votaram, a diferença líquida a favor de Bolsonaro teria crescido em cerca de <strong>{mil(total)}</strong> de votos, com {top} à frente. Parte da abstenção é cadastro desatualizado, e por isso esse número é teto, não promessa. Mas o recado é claro: na direita, faltar custa voto.</p>
""",
    )


# ------------------------------------------------------------------ resiliente
def cap_resiliente() -> str:
    sub = []
    for uf, e in sorted(EST.items()):
        f = e["definitiva"]["candidatos"].get("Flávio")
        if f and f.get("anterior") is not None and f["definitiva"] is not None:
            sub.append((uf, f["anterior"], f["definitiva"]))
    subiu = [x for x in sub if x[2] > x[1]]
    pm = [
        e["definitiva"]["candidatos"]["Flávio"]["pode_mudar"]
        for e in EST.values()
        if e["definitiva"]["candidatos"].get("Flávio", {}).get("pode_mudar") is not None
    ]
    exp = []
    for uf, e in EST.items():
        q = (e.get("quem_ganha") or {}).get("valores")
        p2 = e.get("pres_2t")
        if q and p2:
            exp.append(
                (
                    uf,
                    p2["valores"]["Flávio"] - p2["valores"]["Lula"],
                    q.get("Flávio", 0) - q.get("Lula", 0),
                )
            )
    lidera = [x for x in exp if x[1] > 0]
    lidera_e_acha_que_perde = [x for x in lidera if x[2] < 0]
    aposta_maior = sum(
        1
        for e in EST.values()
        if e.get("quem_ganha")
        and e.get("pres_2t")
        and e["quem_ganha"]["valores"].get("Lula", 0) > e["pres_2t"]["valores"]["Lula"]
    )
    sp = next((x for x in exp if x[0] == "SP"), None)
    sp_txt = ""
    if sp:
        v2 = EST["SP"]["pres_2t"]["valores"]
        q = EST["SP"]["quem_ganha"]["valores"]
        sp_txt = f" Em São Paulo, Flávio vence o 2º turno por {fmt(v2['Flávio'])} a {fmt(v2['Lula'])}, e {fmt(q['Lula'])}% acham que Lula vai ganhar, contra {fmt(q['Flávio'])}% que apostam em Flávio."
    return section(
        "resiliente",
        "Voto que aguenta pancada",
        "O voto de Flávio ficou mais firme. O que ameaça é a sensação de derrota.",
        f"""
<p class="lead">Nos estados em que a Quaest mediu duas vezes, a parte do eleitor de Flávio que diz que o voto é definitivo subiu em {len(subiu)} de {len(sub)}. Na última rodada, fica entre {fmt(min(x[2] for x in sub))}% e {fmt(max(x[2] for x in sub))}%. O voto que ainda pode mudar é de {fmt(min(pm))}% a {fmt(max(pm))}% do eleitorado de Flávio, e é para esse eleitor que a última semana de ataques vai ser desenhada.</p>
{figure("definitiva", "Quaest: você diria que a sua escolha de voto para presidente é definitiva ou pode mudar? Ponto vazado: rodada anterior. Verde: candidaturas de terceira via com 5% ou mais no estado.")}
<h3>A profecia que o adversário mais precisa</h3>
<p>Em {len(lidera_e_acha_que_perde)} dos {len(lidera)} estados em que Flávio lidera o 2º turno, mais eleitores apostam na vitória de Lula do que na dele. E em {aposta_maior} dos {len(exp)} estados com as duas perguntas, a aposta na vitória de Lula é maior que o voto em Lula no 2º turno.{sp_txt} Quem acha que já perdeu fica em casa, vota em branco ou vota no candidato de protesto. O antídoto é mostrar ao eleitor o número do estado dele: ele não está sozinho, está na maioria.</p>
{figure("expectativa", "Quaest, 2º turno Lula × Flávio e pergunta sobre quem vai ganhar a eleição para presidente, independentemente do voto. Rodada de 19 a 24/09.")}
""",
    )


# ------------------------------------------------------------------ modelo
def _linha_cenario(nome: str) -> list:
    m, b = cen(nome), cen(nome, D["modelos"]["media_bruto"])
    por_casa = [cen(nome, MODS[c]) for c in CASAS]
    return [
        esc(nome),
        f"{fmt(m['flavio_validos'], 1)} × {fmt(m['lula_validos'], 1)}",
        f"{fmt(m['flavio_p10'], 1)} a {fmt(m['flavio_p90'], 1)}",
        f"{fmt(m['lula_p10'], 1)} a {fmt(m['lula_p90'], 1)}",
        *[
            f"{fmt(x['flavio_validos'], 1)} × {fmt(x['lula_validos'], 1)}"
            for x in por_casa
        ],
        f"{fmt(b['flavio_validos'], 1)} × {fmt(b['lula_validos'], 1)}",
    ]


def calculadora() -> str:
    """Controle interativo sobre as curvas ja calculadas; a tabela abaixo e o fallback."""
    dados = {
        chave: [
            [round(p["lam"], 2), p["flavio_validos"], p["lula_validos"]]
            for p in MED["curvas"][chave]
        ]
        for chave in ("so_direita", "dois_lados", "lula_consolida")
    }
    return f"""
<div class="calc" id="calc" hidden>
<div class="calc-ctrl">
<label for="calc-lam">Quanto da reserva de Flávio antecipa o voto: <b id="calc-lam-out">50%</b></label>
<input id="calc-lam" type="range" min="0" max="100" step="5" value="50">
<fieldset><legend>E o lado de Lula?</legend>
<label><input type="radio" name="calc-lula" value="so_direita" checked> não antecipa nada</label>
<label><input type="radio" name="calc-lula" value="dois_lados"> antecipa a mesma fração</label>
<label><input type="radio" name="calc-lula" value="lula_consolida"> antecipa tudo</label>
</fieldset>
</div>
<div class="calc-out" aria-live="polite">
<div class="calc-bar"><span class="calc-f" id="calc-f"></span><span class="calc-l" id="calc-l"></span><i class="calc-50"></i></div>
<p id="calc-txt"></p>
</div>
</div>
<script type="application/json" id="calc-dados">{json.dumps(dados, separators=(",", ":"))}</script>"""


def titulo_limiar(lo: float, hi: float) -> str:
    """Titulo do cartao do limiar, fiel a faixa entre as bases."""
    if hi <= 0.35:
        return "Um terço basta para liderar"
    if lo <= 0.35:
        return "De um terço a dois quintos bastam para liderar"
    return f"{round(100 * lo)}% a {round(100 * hi)}% bastam para liderar"


def atlas_txt() -> str:
    if "atlas" not in CASAS:
        return ""
    datas = sorted(p["fim"] for p in D["atlas"].values())
    return f", mais AtlasIntel (recrutamento digital, {len(D['atlas'])} estados, campo até {datas[-1][8:10]}/{datas[-1][5:7]})"


def cap_modelo() -> str:
    l1, l2 = lim_faixa("primeiro_lugar_so_direita")
    d1, d2 = lim_faixa("primeiro_lugar_dois_lados")
    completo = cen("Voto útil completo")
    so_lula = cen("Só Lula consolida")
    nomes = [c["nome"] for c in MED["cenarios"]]
    linhas = [_linha_cenario(n) for n in nomes]
    fat = D["auxiliar"]["fatores_calibracao"]
    ondas = ", ".join(o.split("_")[0].capitalize() for o in ALVO["ondas"])
    return section(
        "modelo",
        "O modelo",
        "Se der certo: quanto Flávio teria dos votos válidos",
        f"""
<p class="lead">A pergunta é condicional e o modelo responde condicionalmente. Pegamos cada estado, pesamos cada eleitor pela chance de comparecer, e movemos para o 1º turno uma fração da reserva que o próprio estado já mostra no 2º turno. Somamos os 27 estados pelo número de pessoas que de fato votam. O resultado não é previsão de urna: é a aritmética do voto útil, com as hipóteses na mesa.</p>
{figure("modelo", "Média das bases estaduais ({casas_txt()}), cada uma calibrada pela média nacional da última semana e ponderada por eleitor provável. Faixa amarela: acima de 50% dos válidos a eleição termina no 1º turno.", wide=True)}
{calculadora()}
<div class="grid2">
<div class="card destaque-azul"><h3>{titulo_limiar(l1, l2)}</h3><p>Flávio termina o 1º turno na frente se {faixa_lista([l1, l2])} da reserva antecipar o voto e Lula ficar onde está, conforme a base ({casas_txt()}). Se Lula antecipar a mesma fração, é preciso {faixa_lista([d1, d2])}.</p></div>
<div class="card destaque-vermelho"><h3>O risco é unilateral</h3><p>Se só a esquerda fizer voto útil, Lula vai a {pct(so_lula["lula_validos"])} dos válidos, com faixa até {pct(so_lula["lula_p90"])}. Nas simulações desse cenário, Lula passa de 50% em {p_faixa("Só Lula consolida", "p_lula_50")} das vezes, conforme a base. Com o voto útil completo da direita, Flávio chega a {pct(completo["flavio_validos"])} e passa de 50% em {p_faixa("Voto útil completo", "p_flavio_50")} das simulações.</p></div>
</div>
{table(["Cenário", "Flávio × Lula (válidos)", "Faixa de Flávio", "Faixa de Lula", *[f"Base {NOME_CASA[c]}" for c in CASAS], "Sem calibração"], linhas, "Cenários do modelo")}
<p class="source">Faixas de 80%: 3.000 simulações por base, com erro amostral de cada estado (efeito de desenho 1,5), um erro comum nacional de 1,5 ponto e, onde o 2º turno não foi medido, incerteza de 35% na reserva estimada. A coluna sem calibração usa só as pesquisas estaduais, sem ajuste pela média nacional.</p>
{figure("contribuicao", "Ganho de Flávio, em votos, com o voto útil completo da direita. Média das bases estaduais.")}
<h3>A conta em cinco passos</h3>
<ol class="passos">
<li><b>Base estadual.</b> Para cada estado, a pesquisa mais recente de cada casa: Quaest (presencial, 19 a 24/09 em 12 estados; agosto mais o movimento médio medido nos outros) e Real Time Big Data (telefone, 29/08 a 24/09){atlas_txt()}. Onde uma casa falta, as outras cobrem. {nota_terceiros()}</li>
<li><b>Eleitor provável.</b> Onde a Quaest cruza voto com comparecimento, cada grupo pesa pela proporção dos que dizem que vão votar. Onde não cruza, aplicamos o deslocamento médio medido.</li>
<li><b>Calibração nacional.</b> As pesquisas estaduais têm datas e métodos diferentes. Ajustamos o nível com três fatores comuns a todos os estados (Flávio × {fmt(fat["quaest"]["flavio"], 3)}, Lula × {fmt(fat["quaest"]["lula"], 3)}, terceira via × {fmt(fat["quaest"]["terceira"], 3)} na base Quaest) até a soma nacional reproduzir a média das ondas divulgadas na última semana ({esc(ondas)}): Flávio {pct(ALVO["flavio_validos"], 2)} e Lula {pct(ALVO["lula_validos"], 2)} dos válidos no 1º turno, e Flávio com {pct(ALVO["flavio_2t_dos_dois"], 2)} dos votos dos dois no 2º. A geografia fica, o nível acompanha a notícia mais fresca.</li>
<li><b>Reserva.</b> Em cada estado, Flávio no 2º turno menos Flávio no 1º; o mesmo para Lula. Onde o 2º turno não foi medido na mesma amostra, estimamos pela relação observada nos estados medidos entre a inclinação do estado e o destino do voto de fora.</li>
<li><b>Antecipação.</b> Movemos uma fração da reserva para o 1º turno. A parte que vem da terceira via sai dela; a parte que vem de indecisos e brancos entra no denominador. Somamos os estados pelos votantes esperados e dividimos pelos válidos.</li>
</ol>
""",
    )


# ------------------------------------------------------------------ municipios
def cap_municipios() -> str:
    linhas = []
    for m in D["municipios_2022"][:30]:
        linhas.append(
            [
                f"{esc(m['municipio'].title())} <span class='sub'>{m['uf']}</span>",
                mil(m["ganho_bolsonaro"]),
                mil(m["ganho_lula"]),
                mil(m["ciro_tebet_1t"]),
                fmt(m["bolsonaro_2t_pct"], 1) + "%",
                mil(m["eleitores_2026"]),
            ]
        )
    top10 = sum(m["ganho_bolsonaro"] for m in D["municipios_2022"][:10])
    return section(
        "municipios",
        "Onde bater na porta",
        "As cidades onde o voto útil de 2022 chegou tarde",
        f"""
<p class="lead">O melhor indicador de onde está o voto útil de 2026 é onde ele apareceu em 2022, entre um turno e outro. As dez cidades da lista somaram {mil(top10)} de votos novos para Bolsonaro entre 2 e 30 de outubro de 2022. São quase todas capitais e grandes cidades: o voto útil é urbano.</p>
{table(["Município", "Bolsonaro ganhou entre os turnos", "Lula ganhou", "Ciro + Tebet no 1º turno", "Bolsonaro no 2º turno", "Eleitorado 2026"], linhas, "Municípios com maior ganho de Bolsonaro entre os turnos de 2022")}
<p class="source">TSE, votação por município e zona, 2022, e eleitorado de julho de 2026. Arquivo completo com os 5.570 municípios em <a href="https://github.com/ArvorCo/PNAD/blob/main/analysis/voto_util/reserva_2022_municipios.csv">reserva_2022_municipios.csv</a>.</p>
""",
    )


# ------------------------------------------------------------------ nacional
def _nx(bloco: str) -> dict:
    return (
        D["nacional"]["fontes"]
        .get("nexus_20260921", {})
        .get("blocos", {})
        .get(bloco, {})
    )


def _qn(bloco: str) -> dict:
    return (
        D["nacional"]["fontes"]
        .get("quaest_20260921", {})
        .get("blocos", {})
        .get(bloco, {})
    )


def _df(bloco: str) -> dict:
    return (
        D["nacional"]["fontes"]
        .get("datafolha_20260921", {})
        .get("blocos", {})
        .get(bloco, {})
    )


def cap_nacional() -> str:
    mat = _nx("migracao_1t_para_2t_lula_x_flavio").get("linhas", {})
    dfm = _df("transferencia_1t_para_2t_lula_x_flavio").get("linhas", {})
    linhas = []
    for nome in ("Zema", "Renan", "Cury", "Caiado", "Samara"):
        if nome in mat:
            m = mat[nome]
            d = dfm.get(nome)
            linhas.append(
                [
                    nome,
                    fmt(m["Flávio"]),
                    fmt(m["Lula"]),
                    fmt(m["Branco/nulo"] + m.get("Indecisos", 0)),
                    f"{fmt(d['Flávio'])} × {fmt(d['Lula'])}" if d else "",
                ]
            )
    b22 = (
        _nx("voto_2022_x_voto_1t")
        .get("colunas", {})
        .get("Votou Jair Bolsonaro em 2022", {})
    )
    tv22 = sum(b22.get(k, 0) for k in ("Cury", "Caiado", "Renan", "Zema", "Outros"))
    fora22 = tv22 + b22.get("Branco/nulo", 0) + b22.get("Indecisos", 0)
    votos_b22 = B22["t2"]["bolsonaro"]
    cert = _nx("certeza_1t_por_candidato_serie")
    cert_f = cert.get("Flávio", [])
    cert_r = cert.get("rodadas", [])
    qdef = _qn("voto_definitivo_por_candidato")
    qf = qdef.get("linhas", {}).get("Flávio", [])
    exp = _nx("expectativa_por_voto_1t").get("colunas", {})
    mot = _nx("motivacao_do_voto_1t").get("linhas", {})
    comp = _nx("comparecimento_passado_x_voto_1t").get("colunas", {})
    presenca = comp.get("Presença nas duas últimas eleições", {})
    abst = next((v for k, v in comp.items() if k.startswith("Absten")), {})
    return section(
        "nacional",
        "O que as pesquisas nacionais medem",
        "Para onde vai cada eleitor de terceira via, e o reencontro com 2022",
        f"""
<p class="lead">Uma pesquisa nacional publicou, nesta rodada, o destino no 2º turno de cada eleitorado de terceira via. A Nexus, de 18 a 20 de setembro (BR-00485/2026, p. 79), mostra que o eleitor de Zema e o de Renan Santos vão majoritariamente para Flávio, que o de Cury se divide com vantagem para Flávio, e que o de Caiado é o mais disputado. O Datafolha, no texto do relatório de 15 a 17 de setembro (p. 7), mede Cury e Caiado com vantagem de Flávio.</p>
{table(["Eleitor no 1º turno", "Flávio no 2º turno", "Lula no 2º turno", "Branco, nulo ou indeciso", "Datafolha Flávio × Lula"], linhas, "Destino no 2º turno do eleitor de terceira via")}
<p class="source">Em % dos eleitores de cada candidato no 1º turno. As linhas de Zema e Samara têm cerca de 20 entrevistas cada na Nexus; a de Caiado diverge entre os dois institutos. Nenhum instituto publica o destino do indeciso e do eleitor de branco e nulo.</p>
<div class="grid2">
<div class="card destaque-azul"><h3>O eleitor de Bolsonaro de 2022 que ainda não voltou</h3><p>Entre quem votou em Jair Bolsonaro no 2º turno de 2022, {fmt(b22.get("Flávio"))}% votam hoje em Flávio no 1º turno. {fmt(tv22)}% estão na terceira via, {fmt(b22.get("Lula"))}% em Lula e {fmt(b22.get("Branco/nulo", 0) + b22.get("Indecisos", 0))}% em branco, nulo ou indecisos (Nexus, p. 23). Aplicado aos {fmt(votos_b22 / 1e6, 1)} milhões de votos de Bolsonaro em 2022, cada ponto são {mil(votos_b22 / 100)} de pessoas. Os {fmt(fora22)} pontos fora de Flávio e de Lula são cerca de <strong>{fmt(fora22 * votos_b22 / 100 / 1e6, 1)} milhões</strong> de eleitores que já votaram na direita uma vez. É a conversa mais fácil do país.</p></div>
<div class="card"><h3>O voto de Flávio endureceu</h3><p>Na série da Nexus, a parte do eleitor de Flávio que diz que a decisão está tomada foi de {fmt(cert_f[0]) if cert_f else "n/d"}% em {esc(cert_r[0]) if cert_r else ""} para {fmt(cert_f[-1]) if cert_f else "n/d"}% em {esc(cert_r[-1]) if cert_r else ""}. Na Quaest, de {fmt(qf[0][0]) if qf else "n/d"}% em 14/08 para {fmt(qf[-1][0]) if qf else "n/d"}% em 21/09. O eleitor de Cury, de Caiado e de Zema fica perto de metade: é o voto que ainda se move.</p></div>
</div>
<h3>O eleitor de terceira via acha que Lula vai ganhar</h3>
<p>Entre os eleitores de Cury, {fmt(exp.get("Cury", {}).get("Lula"))}% acham que Lula vence a eleição, contra {fmt(exp.get("Cury", {}).get("Flávio"))}% que apostam em Flávio. Entre os de Caiado, {fmt(exp.get("Caiado", {}).get("Lula"))}% contra {fmt(exp.get("Caiado", {}).get("Flávio"))}% (Nexus, p. 48). E {fmt(mot.get("Cury", [0, 0])[1])}% do eleitor de Cury dizem que ele não é o candidato ideal, só o melhor entre os disponíveis (p. 46). É o eleitor que não quer Lula, acha que Lula ganha e ainda não percebeu que o voto dele é a diferença.</p>
<h3>O comparecimento, pela Nexus</h3>
<p>Quem votou nas duas últimas eleições dá {fmt(presenca.get("Lula"))} a {fmt(presenca.get("Flávio"))} para Lula; quem se absteve nas duas, {fmt(abst.get("Lula"))} a {fmt(abst.get("Flávio"))} (p. 22). Na Nexus, portanto, o eleitor que falta é mais lulista, e o comparecimento favorece Flávio. Na Quaest estadual o efeito líquido é quase nulo. As duas leituras entram no texto; nenhuma autoriza contar com a abstenção do outro lado.</p>
""",
    )


# ------------------------------------------------------------------ limites e fontes
def cap_limites() -> str:
    bruto = cen("Voto útil completo", D["modelos"]["media_bruto"])
    completo = cen("Voto útil completo")
    return section(
        "limites",
        "Limites",
        "O que este mapa não prova",
        f"""
<ol class="limites">
<li><b>Não é previsão.</b> O modelo responde a uma pergunta condicional: se uma fração da reserva de 2º turno antecipar o voto, qual é a conta. A fração que vai de fato antecipar ninguém mede.</li>
<li><b>Reserva não é eleitor garantido.</b> Quem escolhe Flávio contra Lula pode continuar votando no candidato preferido no 1º turno, e tem esse direito. O número é teto endereçável.</li>
<li><b>A calibração muda o ponto de partida.</b> Só com as pesquisas estaduais, sem ajuste pela média nacional, o voto útil completo leva Flávio a {pct(bruto["flavio_validos"])} dos válidos, contra {pct(completo["flavio_validos"])} na versão calibrada. As pesquisas estaduais são mais antigas que as nacionais e estão mais à esquerda na média.</li>
<li><b>Datas diferentes.</b> Treze estados só têm Quaest de agosto; o movimento de setembro foi estimado pelo que a própria Quaest mediu nos outros doze. A Real Time cobre 23 estados, alguns com campo no começo de setembro.</li>
<li><b>Eleitor provável é autodeclarado.</b> A pergunta sobre comparecimento mede intenção, não comportamento. O cadastro eleitoral também infla a abstenção oficial com eleitores que já não existem.</li>
<li><b>Transferência de indecisos e brancos é hipótese.</b> Nenhum instituto publica para onde vão no 2º turno. Isso só afeta quanto da reserva sai de voto válido, não o tamanho dela.</li>
<li><b>Classificação de campo é editorial.</b> Direita, centro e esquerda para governador e senador seguem o partido, com as exceções listadas abaixo. O cruzamento da Quaest não depende dessa classificação: ele mede o voto do eleitor de cada nome.</li>
<li><b>O capítulo de campanha tem lado.</b> Ele foi escrito para quem faz campanha voluntária por Flávio Bolsonaro. Os números que ele usa são os mesmos que o resto da página publica, inclusive os que contrariam a tese.</li>
</ol>
""",
    )


def cap_fontes() -> str:
    q = []
    for uf, e in sorted(EST.items()):
        q.append(
            f'<li><b>{uf}</b>: <a href="{esc(e["url"])}">{esc(e["arquivo"])}</a>, registro {esc(e.get("registro") or "n/d")}'
            f'{" e " + esc(e["registro_presidente"]) if e.get("registro_presidente") else ""}, campo {esc(e.get("campo") or "n/d")}, n = {fmt(e["n"])}.</li>'
        )
    r = []
    for uf, x in sorted(D["realtime"].items()):
        link = f'<a href="{esc(x["url"])}">PDF</a>' if x.get("url") else "PDF"
        r.append(
            f"<li><b>{uf}</b>: {link}, registro {esc(x.get('registro') or 'n/d')}, campo {esc(x.get('campo') or 'n/d')}, n = {fmt(x['n'])}, 1º turno p. {x.get('pagina_1t')}, 2º turno p. {x.get('pagina_2t')}.</li>"
        )
    atl = []
    for uf, x in sorted(D.get("atlas", {}).items()):
        atl.append(
            f"<li><b>{uf}</b>: {esc(x['json'].replace('.json', ''))}, registro {esc(x.get('registro') or 'n/d')}, campo {esc(data_campo(x.get('campo')))}, n = {fmt(x['n'])}, 1º turno p. {x.get('pagina_1t')}, 2º turno p. {x.get('pagina_2t')}.</li>"
        )
    outras = []
    for d in D.get("outros_estaduais", []):
        if "Atlas" in d["instituto"]:
            continue
        link = (
            f'<a href="{esc(d["url_pdf"])}">PDF</a>'
            if d.get("url_pdf")
            else "PDF arquivado"
        )
        uso = "base do modelo na UF" if d.get("usado") else "triangulação"
        outras.append(
            f"<li><b>{esc(d['uf'])}</b>: {esc(d['instituto'])}, {link}, registro {esc(d.get('registro_tse') or 'n/d')}, campo {esc(data_campo(d.get('campo')))}, n = {fmt(d.get('n') or 0)} ({uso}).</li>"
        )
    nac = []
    for o in D["nacional"]["ondas"]:
        nac.append(
            f"{esc(o['instituto'])} {o['fim'][8:10]}/{o['fim'][5:7]} ({esc(o.get('registro') or 'n/d')})"
        )
    exc = "".join(
        f"<li>{esc(x['nome'])} ({x['uf']}): {esc(x['campo'])}, {esc(x['motivo'])}.</li>"
        for x in D["campo_excecao"]
    )
    return section(
        "fontes",
        "Fontes e reprodução",
        "Tudo o que está nesta página, e como refazer",
        f"""
<h3>Pesquisas estaduais Quaest</h3>
<p>Relatórios em imagem, transcritos página a página; cada número guarda a página de origem nos arquivos de <code>analysis/voto_util/quaest/</code>.</p>
<ul class="fontes">{"".join(q)}</ul>
<h3>Pesquisas estaduais AtlasIntel</h3>
<p>Recrutamento digital aleatório; relatórios em imagem, transcritos página a página.</p>
<ul class="fontes">{"".join(atl) or "<li>Nenhuma transcrita nesta versão.</li>"}</ul>
<h3>Pesquisas estaduais Real Time Big Data</h3>
<ul class="fontes">{"".join(r)}</ul>
<h3>Outras pesquisas estaduais</h3>
<ul class="fontes">{"".join(outras)}</ul>
<h3>Pesquisas nacionais</h3>
<p>{"; ".join(nac)}. Matriz de transferência, voto de 2022, certeza, expectativa e comparecimento: Nexus/BTG de 18 a 20/09 (BR-00485/2026), Quaest de 17 a 20/09 (BR-06004/2026), Datafolha de 15 a 17/09 (BR-04029/2026), AtlasIntel, Real Time e PoderData de 24/09.</p>
<h3>Base eleitoral</h3>
<p>TSE, resultados simplificados de 2022 por UF (eleições 544 e 545, <code>resultados.tse.jus.br</code>); votação por município e zona de 2022; perfil do eleitorado de julho de 2026. Malha de UFs do IBGE (API de malhas, qualidade mínima).</p>
<h3>Classificação de campo com exceção declarada</h3>
<ul class="fontes">{exc}</ul>
<h3>Reprodução</h3>
<p class="repro">python3 scripts/voto-util-092026-tse.py<br>python3 scripts/voto-util-092026-data.py<br>python3 scripts/voto-util-092026-build.py<br>pytest -q tests/test_voto_util_092026.py</p>
<p>Base pública: <a href="assets/voto_util_092026.json">voto_util_092026.json</a> e <a href="https://github.com/ArvorCo/PNAD/blob/main/derivados/voto-util-092026-estados.csv">voto-util-092026-estados.csv</a>. Municípios: <a href="https://github.com/ArvorCo/PNAD/blob/main/analysis/voto_util/reserva_2022_municipios.csv">reserva_2022_municipios.csv</a>.</p>
""",
    )
