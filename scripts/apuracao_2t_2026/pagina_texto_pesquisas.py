"""Textos e tabelas do capítulo `pesquisas` do dossiê do 2º turno.

Todo número sai de `pesquisas_vs_urna.json`, `projecao_pre_urna.json`,
`pesquisas_estaduais.json` e `hipotese_autor.json` (gerados por
`scripts/apuracao-2t-2026-pesquisas.py`) e do memorando `hipotese_autor.md`
(texto integral do post do autor). Convenção: afastamento (erro) = pesquisa menos urna, em
pontos dos válidos; na diferença Flávio menos Lula (F−L), positivo quer dizer que
a pesquisa pôs Flávio mais à frente do que a urna.
"""

from __future__ import annotations

import re
from html import escape

from .pagina_comum import (
    FLAVIO,
    ROOT,
    cartao,
    inteiro,
    limites,
    memo,
    milhoes,
    nota,
    num,
    p,
    sinal,
    tabela,
)

ARQ = "pesquisas_vs_urna.json"
IMAGEM_TWEET = "img/apuracao_2t/tweet_leonardodias_20261025_2141.webp"
"""Cópia pública em `docs/`; o original fica em `analysis/apuracao_2t_2026/noticias_fontes/`."""


def dm(iso: str | None) -> str:
    return f"{iso[8:10]}/{iso[5:7]}" if iso and len(iso) >= 10 else (iso or "")


def s2(x: float | None) -> str:
    return sinal(x, 2)


# ------------------------------------------------------------------ números


def fatos(PV: dict, PP: dict | None, PE: dict | None, H: dict | None = None) -> dict:
    """Números do capítulo num só lugar, para o texto e para o teste."""
    res = PV["resumo"]
    pub = res["publicado_validos_do_total"]
    c = PV["centrais"]
    ef = PV["efeito_reponderacao"]
    t1 = PV["primeiro_turno"]
    pa = PV["painel_1t_2t"]
    td = PV["tendencia_publicada"]
    hi = PV["hipoteses"]
    cont = hi["contabilidade_entre_turnos"]
    urna = PV["urna"]["brasil"]
    por_inst = {x["instituto"]: x for x in PV["pesquisas"]}
    urna_fl = urna["validos"]["flavio"] - urna["validos"]["lula"]
    f = {
        "n": res["n_casas"],
        "erro": pub["media"],
        "mediana": pub["mediana"],
        "dp": pub["desvio_padrao"],
        "dp_aas": res["desvio_esperado_so_amostragem_aas_pp"],
        "positivos": pub["positivos"],
        "negativos": pub["negativos"],
        "amplitude": pub["amplitude"],
        "fora": res["fora_da_margem_aas"],
        "flavio_frente": res["flavio_a_frente_nos_validos"],
        "acertaram": res["acertaram_vencedor"],
        "casas_certas": res["casas_que_acertaram_vencedor"],
        "oficial": res["publicado_validos_oficiais"]["media"],
        "n_oficial": res["publicado_validos_oficiais"]["n"],
        "urna_f": urna["validos"]["flavio"],
        "urna_l": urna["validos"]["lula"],
        "urna_fl": urna_fl,
        "media_arvor": c["media_arvor"]["erro_f_menos_l"],
        "projecao": c["projecao_arvor"]["erro_f_menos_l"],
        "ancora_pub": c["ancora_projecao_published"]["erro_f_menos_l"],
        "ancora_pnad": c["ancora_projecao_pnad"]["erro_f_menos_l"],
        "presenca_pct": c["presenca_relativa_pct"],
        "rep_n": ef["n"],
        "rep_afastou": ef["afastou"],
        "rep_aproximou": ef["aproximou"],
        "rep_neutro": ef["neutro"],
        "rep_desloc": ef["deslocamento_medio_f_menos_l"],
        "rep_pub": res["publicado_mesmas_casas_reponderadas"]["media"],
        "rep_rep": res["reponderado"]["media"],
        "t1_erro": t1["erro_comum_lula_menos_flavio"],
        "t1_n": t1["n_casas"],
        "t1_rep_aprox": t1["efeito_reponderacao_ultimas_ondas"]["aproximou"],
        "t1_rep_n": t1["efeito_reponderacao_ultimas_ondas"]["n"],
        "t1_ag_pub": t1["agregador_publicado_erro"],
        "t1_ag_rep": t1["agregador_reponderado_erro"],
        "e2022": PV["referencia_2022"]["erro_comum_lula_menos_bolsonaro"],
        "inverteram": pa["inverteram_sinal"],
        "painel_n": pa["n"],
        "painel_r": pa["correlacao"],
        "incl": td["pos_urna_05_a_24"]["inclinacao_dentro_da_casa_pp_dia"],
        "td_ate12": td["media_campo_ate_12_10"],
        "td_desde19": td["media_campo_desde_19_10"],
        "td_extrap": td["extrapolacao_ate_a_urna"]["f_menos_l_extrapolado"],
        "td_dias": td["extrapolacao_ate_a_urna"]["dias_do_meio_do_campo_ate_a_urna"],
        "disponivel": cont["brasil"]["disponivel"],
        "parcela_flavio": cont["brasil"]["parcela_flavio_do_ganho_pct"],
        "teto_terceira": cont["brasil"]["teto_parcela_flavio_da_terceira_via_pct"],
        "abst_1t": cont["brasil"]["abstencao_1t_pct"],
        "abst_2t": cont["brasil"]["abstencao_2t_pct"],
        "comp_var": cont["brasil"]["variacao_comparecimento"],
        "corr_abst": cont["correlacao_variacao_abstencao_com_residuo"],
        "corr_terc": cont["correlacao_terceiros_1t_com_residuo"],
        "ufs_neg": cont["ufs_com_residuo_negativo"],
        "teto_comp": cont["limite_comparecimento"]["parcela_maxima_explicada_pp"],
        "fl_sem_aumento": cont["limite_comparecimento"]["f_menos_l_sem_o_aumento"],
        "indec_frente": hi["indecisos_extremo"]["flavio_ainda_a_frente"],
        "indec_erro": hi["indecisos_extremo"]["erro_medio_todos_indecisos_lula"],
        "pres_decl": {x["instituto"]: x for x in hi["presenca_declarada"]},
        "pres_nec": hi["presenca_relativa_necessaria"],
        "ind_autor": hi["indecisos_divisao_autor"],
    }
    f["camada_pnad"] = f["ancora_pnad"] - f["ancora_pub"]
    f["camada_presenca"] = f["projecao"] - f["ancora_pnad"]
    q = por_inst.get("Quaest")
    if q and q.get("eleitor_provavel_oficial"):
        v = q["eleitor_provavel_oficial"]["validos"]
        f["lv_quaest"] = (
            v["flavio"] - v["lula"] - urna_fl,
            q["erro_validos_do_total"]["erro_f_menos_l"],
        )
    nx = por_inst.get("Nexus")
    if nx and nx.get("eleitor_provavel_documental"):
        v = nx["eleitor_provavel_documental"]["validos"]
        f["lv_nexus"] = (
            v["flavio"] - v["lula"] - urna_fl,
            nx["erro_validos_do_total"]["erro_f_menos_l"],
        )
    if PP:
        tr = PP["metodos"]["transportado_25_10"]
        f["transp_erro"] = tr["nacional_erro_f_menos_l_pp"]
        f["transp_vies"] = tr["vies_flavio_pp_ponderado"]
        f["transp_rmse_sv"] = tr["rmse_sem_vies_pp"]
        f["transp_errou"] = tr["errou_vencedor_ufs"]
        pj = PP["metodos"]["projecao_25_10"]
        f["proj_vies"] = pj["vies_flavio_pp_ponderado"]
        f["proj_rmse"] = pj["rmse_flavio_pp_ponderado"]
        f["proj_rmse_sv"] = pj["rmse_sem_vies_pp"]
        f["proj_corr"] = pj["correlacao_previsto_urna"]
        f["proj_errou"] = pj["errou_vencedor_ufs"]
        f["proj_acertou"] = pj["acertou_vencedor"]
    if PE:
        f["est_n"] = PE["resumo"]["n"]
        f["est_certos"] = PE["acertaram_vencedor"]
        f["est_erro"] = PE["resumo"]["media"]
    if H:
        f["pres_aut"] = H.get("presenca_necessaria_a")
    return f


# ------------------------------------------------------------------ abertura


def tese() -> str:
    return nota(
        "juizo",
        "As pesquisas da última semana e a régua de renda da casa mediram o eleitorado até o último "
        "campo, em 23 e 24/10. Entre essa medição e a urna houve uma mudança importante, e é ela que "
        "este capítulo investiga. O afastamento comum entre as casas e a urna é tratado aqui como a "
        "medida do tamanho dessa mudança, não como defeito de medição dos institutos nem da "
        "reponderação. É a posição do autor do dossiê; o que a contraria está publicado ao lado, em "
        "“O que ainda falta explicar”.",
        "A tese do capítulo.",
    )


def cartoes(f: dict) -> str:
    pres = f.get("pres_aut")
    ultimo = (
        cartao(
            f"{sinal(pres, 1)}%",
            "presença relativa de Flávio que reproduz a urna no simulador da casa de 24/10",
        )
        if pres is not None
        else cartao(f"{s2(f['projecao'])}", "afastamento da Projeção Arvor")
    )
    return (
        '<div class="finding-grid">'
        + cartao(
            f"{s2(f['erro'])}",
            f"afastamento comum entre o último campo das {f['n']} casas e a urna, na diferença F−L "
            f"(mediana {s2(f['mediana'])})",
            FLAVIO,
        )
        + cartao(
            f"{f['positivos']} de {f['n']}", "casas com o afastamento no mesmo sentido"
        )
        + cartao(
            f"{f['flavio_frente']} de {f['n']}",
            "punham Flávio à frente no último campo; "
            + " e ".join(escape(x) for x in f["casas_certas"])
            + " já mediam Lula à frente",
        )
        + ultimo
        + "</div>"
    )


def abertura(f: dict) -> str:
    h = '<h3 id="pesquisas-mudanca">O que mudou entre sábado e domingo?</h3>'
    h += p(
        f"No sábado, as {f['n']} casas com campo encerrado na última semana mediam, em média, Flávio "
        f"{s2(f['erro'] + f['urna_fl'])} pontos à frente nos válidos. No domingo, a urna deu Lula "
        f"{num(f['urna_l'], 2)}% e Flávio {num(f['urna_f'], 2)}%, uma diferença F−L de "
        f"{s2(f['urna_fl'])}. O afastamento médio foi de {s2(f['erro'])} pontos, de "
        f"{s2(f['amplitude'][0])} a {s2(f['amplitude'][1])} conforme a casa, no mesmo sentido em todas. "
        f"Pelos válidos que as próprias casas divulgaram ({f['n_oficial']} delas), {s2(f['oficial'])}.",
        "verificado",
    )
    h += p(
        f"As casas concordaram entre si mais do que o acaso permite: a dispersão entre elas foi de "
        f"{num(f['dp'], 2)} pontos, abaixo dos {num(f['dp_aas'], 2)} que só a amostragem simples "
        "produziria. Métodos diferentes (presencial, telefone, painel digital), institutos diferentes e "
        "o mesmo número. Isso indica que mediram o mesmo eleitorado do mesmo jeito.",
        "inferencia",
    )
    h += p(
        "Se a medição estava certa até sábado, o afastamento comum é o tamanho do que mudou entre o "
        "último campo e o voto: cerca de cinco pontos e meio na diferença, em direção a Lula.",
        "juizo",
    )
    return h


def medicao(f: dict) -> str:
    h = '<h3 id="pesquisas-medicao">A medição, casa a casa</h3>'
    h += p(
        f"{f['fora']} dos {f['n']} afastamentos ficam fora da margem de 95% da diferença sob "
        "amostragem simples. A figura põe o último campo de cada casa contra a linha da urna; a "
        "seguinte mostra o tamanho do afastamento de cada uma.",
        "verificado",
    )
    return h


def centrais(f: dict) -> str:
    h = "<h4>As centrais da casa</h4>"
    h += p(
        f"A Média Arvor ficou {s2(f['media_arvor'])} pontos longe da urna; a Projeção Arvor, "
        f"{s2(f['projecao'])}. Na Projeção, a média das pesquisas com recência e tendência respondia "
        f"por {s2(f['ancora_pub'])}; a régua de renda da PNAD somou {s2(f['camada_pnad'])}; a presença "
        f"relativa de {sinal(f['presenca_pct'], 1)}% a favor de Flávio, resíduo medido no 1º turno, "
        f"somou {s2(f['camada_presenca'])}.",
        "verificado",
    )
    h += p(
        "As duas camadas descreviam o eleitorado que compareceu no 1º turno. Se a mudança de domingo "
        "veio de quem compareceu, e não de quem foi entrevistado, as centrais se afastam mais que as "
        "pesquisas exatamente na medida dessas camadas.",
        "juizo",
    )
    return h


def reponderacao(f: dict) -> str:
    h = "<h4>A régua de renda nesta rodada</h4>"
    h += p(
        f"A reponderação por renda deslocou as casas em média {s2(f['rep_desloc'])} pontos em direção a "
        f"Flávio: afastou da urna {f['rep_afastou']} de {f['rep_n']}, aproximou {f['rep_aproximou']} e "
        f"deixou {f['rep_neutro']} no mesmo lugar. Nas mesmas casas, o afastamento foi de "
        f"{s2(f['rep_pub'])} publicado para {s2(f['rep_rep'])} reponderado. No 1º turno a mesma régua "
        f"aproximou {f['t1_rep_aprox']} de {f['t1_rep_n']} casas e levou o agregador de "
        f"{s2(f['t1_ag_pub'])} para {s2(f['t1_ag_rep'])} (em Lula menos Flávio).",
        "verificado",
    )
    h += p(
        "A régua corrige quem foi entrevistado para parecer com o eleitorado da PNAD. Quando a mudança "
        "de última hora vem de quem comparece, a régua aplica com mais força a composição de sábado, e "
        "o deslocamento em direção a Flávio é o que se espera. Ela funcionou no 1º turno, quando não "
        "houve mudança desse tamanho entre o último campo e a urna.",
        "juizo",
    )
    return h


def sinal_invertido(f: dict) -> str:
    h = "<h3>Três eleições, o mesmo tamanho, sinais opostos</h3>"
    h += p(
        f"No 1º turno de 2022 o afastamento comum foi de {s2(f['e2022'])} pontos em Lula menos "
        f"Bolsonaro; no 1º turno de 2026, {s2(f['t1_erro'])} em Lula menos Flávio ({f['t1_n']} casas). "
        f"Nos dois, as pesquisas puseram Lula mais à frente que a urna. No 2º turno de 2026, na mesma "
        f"orientação, foi {s2(-f['erro'])}: dos três pontos, é o único a favor do candidato da direita. "
        f"Das {f['painel_n']} casas que publicaram nos dois turnos, {f['inverteram']} inverteram o sinal, "
        f"e a correlação entre os afastamentos de cada uma nos dois turnos é {sinal(f['painel_r'], 2)}.",
        "verificado",
    )
    h += p(
        f"Quem mais pôs Lula à frente no 1º turno não é quem mais pôs Flávio à frente no 2º (correlação "
        f"{sinal(f['painel_r'], 2)}): na leitura da casa, o dado não sustenta viés fixo de cada instituto. Um "
        "movimento que atinge todas as casas igual, depois do último campo, produz esse desenho. O precedente "
        f"acima pede cautela: nos 1º turnos de 2022 ({s2(f['e2022'])}) e de 2026 ({s2(f['t1_erro'])}) as casas "
        "também erraram juntas, sem mudança de última hora medida, e erro comum assim é compatível com viés de "
        "método compartilhado ou com casas que convergem umas para as outras (herding).",
        "juizo",
    )
    return h


def geografia(f: dict) -> str:
    if "transp_erro" not in f:
        return ""
    h = "<h3>A mudança teve o mesmo tamanho em todo o país</h3>"
    h += p(
        f"Flávio ficou abaixo da repetição do 1º turno seção a seção em {f['ufs_neg']} das 27 UFs. O "
        f"desvio comum na parcela dele foi de {s2(f['transp_vies'])} pontos e, descontado esse desvio, "
        f"o que sobra por UF é {num(f['transp_rmse_sv'], 2)}. A Projeção Arvor por UF acertou a ordem dos "
        f"estados (correlação {num(f['proj_corr'], 3)} entre previsto e urna) e o vencedor em "
        f"{f['proj_acertou']} das 27; errou em {' e '.join(f['proj_errou'])}, com desvio comum de "
        f"{s2(f['proj_vies'])}.",
        "verificado",
    )
    h += p(
        "A geografia ficou onde estava; o nível mudou em todas as UFs juntas. Na leitura da casa, é o "
        "desenho de um deslocamento nacional, não de um erro localizado em algumas UFs. Um viés de método "
        "comum às pesquisas também deslocaria todas as UFs juntas, como o erro comum dos 1º turnos de 2022 "
        "e 2026; o desenho não separa as duas leituras.",
        "juizo",
    )
    return h


# ------------------------------------------------------------------ tabelas


def tabela_casas(PV: dict) -> str:
    por_id = {x["id"]: x for x in PV["pesquisas"]}
    linhas = []
    for i in PV["ranking"]:
        x = por_id.get(i)
        if x is None:
            continue
        pt = x["publicado_total"]
        of = x.get("erro_validos_oficiais")
        rp = x.get("erro_reponderado")
        err = x["erro_validos_do_total"]["erro_f_menos_l"]
        dentro = "" if x["erro_fora_da_margem_aas"] else " (dentro)"
        linhas.append(
            [
                escape(x["instituto"]),
                f"{dm(x['campo']['inicio'])} a {dm(x['campo']['fim'])}",
                escape(x["modo"].replace("_", " ")),
                f"{num(pt['flavio'], 1)} × {num(pt['lula'], 1)}",
                num(x["validos_do_total"]["flavio"], 2),
                s2(err) + dentro,
                s2(of["erro_f_menos_l"]) if of else "n/d",
                s2(rp["erro_f_menos_l"]) if rp else "sem PNAD",
                num(x["margem_95_diferenca_aas_pp"], 2),
            ]
        )
    return tabela(
        [
            "Casa",
            "Campo",
            "Modo",
            "Publicado F × L",
            "Válidos F",
            "Afastamento F−L",
            "Afastamento oficial",
            "Afastamento PNAD",
            "Margem 95%",
        ],
        linhas,
        "Da mais próxima à mais distante da urna. Válidos pela regra da casa (candidaturas renormalizadas); "
        "oficial = válidos divulgados pela casa; PNAD = placar reponderado que entrou nas centrais; "
        "margem da diferença sob amostragem simples, piso e não intervalo da casa.",
    )


def tabela_reponderacao(PV: dict) -> str:
    linhas = []
    for x in sorted(
        PV["efeito_reponderacao"]["por_casa"], key=lambda y: y["variacao_erro_absoluto"]
    ):
        linhas.append(
            [
                escape(x["instituto"]),
                escape(x["perfil_renda"].replace("_", " ")),
                s2(x["erro_publicado_f_menos_l"]),
                s2(x["erro_reponderado_f_menos_l"]),
                s2(x["variacao_erro_absoluto"]),
                escape(x["direcao"]),
            ]
        )
    return tabela(
        [
            "Casa",
            "Perfil de renda",
            "Afastamento publicado",
            "Afastamento PNAD",
            "Variação do afastamento",
            "Direção",
        ],
        linhas,
        "Efeito da reponderação por renda (PNAD, pessoas de 16 anos ou mais) no afastamento F−L. Variação positiva "
        "afastou da urna. Datafolha usou perfil da onda anterior e Veritá perfil condicional, hipóteses "
        "declaradas na época.",
    )


def tabela_centrais(PV: dict) -> str:
    c = PV["centrais"]
    linhas = []
    for k in (
        "ancora_projecao_published",
        "ancora_projecao_pnad",
        "projecao_arvor",
        "media_arvor",
    ):
        x = c[k]
        linhas.append(
            [
                escape(x["rotulo"]),
                num(x["validos"]["flavio"], 2),
                num(x["validos"]["lula"], 2),
                s2(x["pesquisa_f_menos_l"]),
                s2(x["erro_f_menos_l"]),
            ]
        )
    return tabela(
        ["Central", "Flávio", "Lula", "F−L", "Afastamento F−L"],
        linhas,
        f"As centrais da casa no snapshot {escape(c['snapshot'])}, referência {dm(c['referencia'])}.",
    )


def tabela_estaduais(PE: dict) -> str:
    linhas = []
    for x in PE["pesquisas"]:
        linhas.append(
            [
                f"{escape(x['instituto'])} {escape(x['uf'])}",
                f"{dm(x['campo']['inicio'])} a {dm(x['campo']['fim'])}",
                num(x["validos"]["flavio"], 2),
                num(x["urna_validos"]["flavio"], 2),
                s2(x["erro_f_menos_l_pp"]),
                "certo" if x["acertou_vencedor"] else "errado",
                s2(x["erro_transporte_f_menos_l_pp"]),
            ]
        )
    return tabela(
        [
            "Pesquisa",
            "Campo",
            "Válidos F",
            "Urna F",
            "Afastamento F−L",
            "Vencedor",
            "Afastamento do transporte",
        ],
        linhas,
        "Estaduais presidenciais do 2º turno contra a urna da UF.",
    )


# ------------------------------------------------------------------ hipótese do autor


def tweet() -> dict:
    """Texto integral, data e metadados do post, lidos de `hipotese_autor.md`."""
    md = memo("hipotese_autor.md")
    out = {"texto": [], "fonte": "", "data": "", "hora": ""}
    if not md:
        return out
    m = re.search(r"## Texto integral\s*\n(.*?)\n## ", md, re.DOTALL)
    if m:
        bloco = [
            ln_[1:].strip() for ln_ in m.group(1).splitlines() if ln_.startswith(">")
        ]
        paragrafos, atual = [], []
        for ln_ in bloco:
            if ln_:
                atual.append(ln_)
            elif atual:
                paragrafos.append(" ".join(atual))
                atual = []
        if atual:
            paragrafos.append(" ".join(atual))
        out["texto"] = paragrafos
    f = re.search(r"^Fonte: (.*)$", md, re.MULTILINE)
    if f:
        out["fonte"] = f.group(1)
        dh = re.search(r"(\d{2}/\d{2}/\d{4}) às (\d{1,2}:\d{2})", f.group(1))
        if dh:
            out["data"], out["hora"] = dh.group(1), dh.group(2)
    return out


def _imagem(rt: dict) -> str:
    """Imagem do simulador que acompanha o post, ao lado da transcrição."""
    arq = ROOT / "docs" / IMAGEM_TWEET
    if not arq.exists():
        return ""
    dim = ""
    try:
        from PIL import Image

        with Image.open(arq) as im:
            dim = f' width="{im.width}" height="{im.height}"'
    except (ImportError, OSError):
        pass
    pr = rt["parametros"]
    fl = rt["flavio_validos_pct"]
    alt = (
        "Captura do post de Leonardo Dias no X com a imagem do simulador da Arvor no cenário Média: "
        f"presença relativa de Flávio em {sinal(pr['presenca_relativa'], 1)}%, abstenção de "
        f"{num(100 - pr['comparecimento'], 1)}%, indecisos divididos {num(pr['indecisos_flavio'], 1)}% "
        f"para Flávio e {num(100 - pr['indecisos_flavio'], 1)}% para Lula; resultado Flávio "
        f"{num(fl, 1)}% e Lula {num(100 - fl, 1)}% dos válidos."
    )
    return (
        f'<figure class="p2t-tweet"><img src="{IMAGEM_TWEET}" loading="lazy"{dim} '
        'style="max-width:min(100%,720px);height:auto;display:block" '
        f'alt="{escape(alt)}">'
        "<figcaption>Post do autor com o cenário do simulador da casa (versão de 24/10). "
        "Original em <code>analysis/apuracao_2t_2026/noticias_fontes/</code>.</figcaption></figure>"
    )


def hipotese(H: dict, f: dict) -> str:
    tw = tweet()
    cen = {c["nome"]: c for c in H["cenarios"]}
    a = cen.get("a_presenca_necessaria")
    b = cen.get("b_limite_todos_indecisos_para_lula")
    c = cen.get("c_combinacao_do_autor_com_bn_reais")
    urna = H["urna"]
    pn = f["pres_nec"]
    ia = f["ind_autor"]
    h = '<h3 id="pesquisas-hipotese">A hipótese do autor: mudou quem compareceu</h3>'
    corpo = "".join(f"<p>{escape(x)}</p>" for x in tw["texto"])
    quando = f"{tw['data']}, {tw['hora']}" if tw["data"] else "25/10/2026"
    h += nota(
        "juizo",
        "A hipótese de Leonardo Dias, fundador da Arvor, é o eixo deste capítulo: o que mudou entre "
        "sábado e domingo foi quem compareceu. Abaixo, a conta no motor da casa com a urna real e o "
        "que cada peça tem a seu favor; o que a contraria está em “O que ainda falta explicar”.",
    )
    citacao = (
        f"<blockquote>{corpo}<cite>Leonardo Dias (@leonardodias), no X, {escape(quando)} "
        "(horário de Brasília). Fonte do registro: "
        "<code>analysis/apuracao_2t_2026/hipotese_autor.md</code>.</cite></blockquote>"
    )
    img = _imagem(H["reproducao_tweet"])
    h += f'<div class="duas">{citacao}{img}</div>' if img else citacao
    rt = H["reproducao_tweet"]
    h += p(
        f"O cenário da imagem foi refeito no motor da casa (<code>{escape(H['motor'])}</code>, snapshot "
        f"<code>{escape(H['snapshot']['versao'])}</code>, o último de 24/10): presença relativa de Flávio "
        f"{sinal(rt['parametros']['presenca_relativa'], 1)}%, comparecimento de "
        f"{num(rt['parametros']['comparecimento'], 1)}%, indecisos divididos "
        f"{num(rt['parametros']['indecisos_flavio'], 1)}% para Flávio. O motor devolve Flávio "
        f"{num(rt['flavio_validos_pct'], 2)}%, o número da imagem. Depois a conta foi refeita com a "
        f"abstenção real de {num(urna['abstencao_pct'], 2)}% e os brancos e nulos reais "
        f"({inteiro(urna['brancos_mais_nulos'])}, {num(urna['branco_nulo_pct_comparecimento'], 2)}% "
        "de quem compareceu).",
        "verificado",
    )
    itens = []
    if a:
        itens.append(
            f"(a) Com indecisos na proporção automática da central, bater a urna exige presença "
            f"relativa de Flávio de {sinal(a['parametros']['presenca_relativa'], 1)}%, contra "
            f"{sinal(f['presenca_pct'], 1)}% da central."
        )
    if b:
        itens.append(
            f"(b) Mantida a presença de {sinal(b['parametros']['presenca_relativa'], 1)}%, nenhuma divisão "
            "dos indecisos chega à urna: mesmo com todos para Lula, Flávio fica em "
            f"{num(b['placar']['flavio_validos_pct'], 2)}% ({s2(b['contra_a_urna']['diferenca_f_menos_l_pp'])} "
            "pontos em F−L)."
        )
    if c:
        itens.append(
            f"(c) A combinação do autor com brancos e nulos reais dá Flávio "
            f"{num(c['placar']['flavio_validos_pct'], 2)}%, {num(c['contra_a_urna']['diferenca_f_menos_l_pp'], 2)} "
            f"ponto acima da urna em F−L ({inteiro(c['contra_a_urna']['flavio_votos'])} votos de Flávio "
            "a mais que a urna)."
        )
    h += "<ul>" + "".join(f"<li>{x}</li>" for x in itens) + "</ul>"
    h += tabela_cenarios(H)
    h += "<h4>Peça 1: abstenção</h4>"
    h += p(
        f"A urna mediu abstenção de {num(f['abst_2t'], 2)}%, contra {num(f['abst_1t'], 2)}% no 1º "
        f"turno: {milhoes(f['comp_var'])} a mais votaram. É o número que o post cita.",
        "verificado",
    )
    h += "<h4>Peça 2: presença diferencial, o centro da hipótese</h4>"
    h += p(
        "Presença por candidato não é medida: a urna diz quantos votaram, nunca em quem votaria quem "
        f"ficou em casa. Por fora do motor, a razão F/L da Média Arvor precisava cair "
        f"{num(-pn['media_arvor'], 1)}% ({num(-pn['media_arvor_sem_o_extra'], 1)}% sem o extra já "
        f"embutido); a da média simples das {f['n']} casas, {num(-pn['media_simples_publicada_20_casas'], 1)}%.",
        "verificado",
    )
    h += p(
        "Essa conta é a mesma que um erro comum de medição exigiria; a urna sozinha não separa as "
        "duas leituras. A presença diferencial é a explicação que o autor propõe para a mudança.",
        "inferencia",
    )
    h += "<h4>Peça 3: destino dos indecisos</h4>"
    h += p(
        f"Com a divisão do autor, {num(100 * ia['parte_flavio'], 1)}% para Flávio, os indecisos "
        "completam a conta; o tamanho do que carregam está no candidato 4, abaixo.",
        "verificado",
    )
    ultima = tw["texto"][-1] if tw["texto"] else ""
    m = re.search(r"(se foi isso mesmo, não saberemos)", ultima)
    frase = m.group(1) if m else "se foi isso mesmo, não saberemos"
    h += nota(
        "juizo",
        "Com abstenção e brancos e nulos reais, a combinação do autor chega a poucos décimos da urna "
        "partindo da Média de 24/10, sem mexer em nenhuma pesquisa. A abstenção é fato medido; a "
        "presença diferencial não é medida por candidato em lugar nenhum; os indecisos ajudam pouco. "
        f"A frase final do autor diz o limite do que se pode afirmar: “{escape(frase)}”.",
        "Leitura do autor.",
    )
    return h


def tabela_cenarios(H: dict) -> str:
    linhas = []
    for c in H["cenarios"]:
        pr = c["parametros"]
        linhas.append(
            [
                escape(c["regra"]),
                sinal(pr["presenca_relativa"], 1) + "%",
                num(pr["indecisos_flavio_efetivo"], 1) + "%",
                num(c["placar"]["flavio_validos_pct"], 2),
                num(c["placar"]["lula_validos_pct"], 2),
                s2(c["contra_a_urna"]["diferenca_f_menos_l_pp"]),
            ]
        )
    return tabela(
        [
            "Cenário",
            "Presença relativa de Flávio",
            "Indecisos para Flávio",
            "Flávio",
            "Lula",
            "Afastamento F−L da urna",
        ],
        linhas,
        "Hipótese do autor refeita no motor da casa, com comparecimento e brancos e nulos da urna "
        "(hipotese_autor.json). Presença por candidato não é medida; os valores resolvidos são o "
        "ajuste que a aritmética exige.",
    )


LIMITES = [
    "Válidos de cada pesquisa são a renormalização dos inteiros publicados; o arredondamento sozinho move a diferença em até cerca de 1 ponto em casas sem decimal.",
    "A margem de 95% sob amostragem simples ignora ponderação e desenho: é piso, não o intervalo da casa.",
    "A urna é a versão nacional mais recente do arquivo do TSE lida pelo coletor; o memorando registra o percentual de seções totalizadas.",
    "Correlações entre 27 UFs são ecológicas. Nada aqui identifica migração individual, comparecimento por candidato ou irregularidade.",
    "Estaduais têm campo de duas semanas antes da urna; o mapa de 24/10 vem do histórico git.",
]


def limites_cap() -> str:
    return limites(
        LIMITES,
        "Memorando completo, com as hipóteses candidatas e as consultas: "
        "<code>analysis/apuracao_2t_2026/dados/pesquisas.md</code>.",
    )
