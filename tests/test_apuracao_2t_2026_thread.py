"""Testes da thread do dossiê da apuração do 2º turno de 2026."""

import re
from pathlib import Path

import pytest
from apuracao_2t_2026 import turnos_perdas as TP
from apuracao_2t_2026.pagina_texto_logs import pendencia_tse
from apuracao_2t_2026.thread_base import (
    URL_DOSSIE,
    dado,
    digitos_soltos,
    problemas_de_texto,
)
from apuracao_2t_2026.thread_build import (
    CAMPOS_TEXTO,
    MAX_CHARS,
    MAX_POSTS,
    MIN_CHARS,
    MIN_POSTS,
    VETADAS_TESE,
    caminhos_png,
    montar,
    valores,
    verificar,
)
from apuracao_2t_2026.thread_pagina import pagina
from apuracao_2t_2026.thread_valores_c import LEI_ACESSO
from apuracao_2026.thread_base import num, pct, sinal

ROOT = Path(__file__).resolve().parents[1]
PAGINA = ROOT / "docs/apuracao_2T_2026_thread.html"
DOSSIE = ROOT / "docs/apuracao_2T_2026.html"


@pytest.fixture(scope="module")
def posts():
    return montar()


@pytest.fixture(scope="module")
def html(posts):
    return pagina(posts, caminhos_png(len(posts)), valores())


def test_quantidade_de_cards(posts):
    assert MIN_POSTS <= len(posts) <= MAX_POSTS
    assert len(posts) == MAX_POSTS == 26


def test_tamanho_dos_posts(posts):
    for i, p in enumerate(posts, 1):
        assert MIN_CHARS <= len(p["corpo"]) <= MAX_CHARS, (i, len(p["corpo"]))


def test_verificacao_completa_sem_erros(posts):
    assert verificar(posts) == []


def test_sem_travessao_hashtag_emoji_ou_palavra_vetada(posts, html):
    for p in posts:
        assert problemas_de_texto(p["corpo"]) == []
    assert "—" not in html
    assert "–" not in html
    assert "fraude" not in html.lower()


def test_nenhum_algarismo_digitado(posts):
    for p in posts:
        for modelo in [p[c] for c in CAMPOS_TEXTO] + list(p["texto"]):
            assert digitos_soltos(modelo) == [], modelo


def test_detector_de_algarismo_pega_numero_solto():
    assert digitos_soltos("Lula teve 51,78% dos válidos") == ["51,78%"]
    assert digitos_soltos("Lula teve {l_pct} no 2º turno de 2026") == []


def test_link_do_dossie_no_primeiro_e_no_ultimo(posts):
    assert URL_DOSSIE in posts[0]["corpo"]
    assert URL_DOSSIE in posts[-1]["corpo"]


def test_card_sabado_domingo_e_tese(posts):
    card = [p for p in posts if "sábado" in p["tag_f"].lower()]
    assert len(card) == 1
    assert "juízo editorial" in card[0]["corpo"].lower()
    assert "juízo editorial declarado do autor" in posts[0]["corpo"].lower()


def test_sem_frases_vetadas_pela_tese(posts, html):
    for frase in VETADAS_TESE:
        assert frase not in html.lower(), frase


def test_hipotese_do_autor_rotulada(posts):
    hip = next(p for p in posts if "hipótese do autor" in p["tag_f"].lower())
    assert "juízo editorial" in hip["corpo"].lower()
    assert "se foi isso mesmo, não saberemos" in hip["corpo"]


def test_numeros_chave_batem_com_os_dados(posts):
    n = dado("presidente")["nacional"]
    corpo = posts[1]["corpo"]
    assert pct(n["pct_lula"]) in corpo
    assert pct(n["pct_flavio"]) in corpo
    assert num(n["margem_lula_votos"]) in corpo
    sil = dado("linha_do_tempo")["pausas"]["silencio_geral"]
    assert num(sil["minutos"], 1) in posts[2]["titulo_f"]
    pv = dado("pesquisas_vs_urna")["resumo"]
    assert (
        f"+{num(pv['publicado_validos_do_total']['media'], 2)}"
        in next(p for p in posts if p["tag_f"] == "Pesquisas × urna")["metrica_f"]
    )


def test_cada_card_tem_svg(posts):
    for p in posts:
        assert p["svg"].startswith("<svg") and "</svg>" in p["svg"]


def test_pagina_publicada_igual_a_gerada(html):
    assert PAGINA.read_text(encoding="utf-8") == html


def test_pngs_existem(posts):
    for rel in caminhos_png(len(posts)):
        assert (ROOT / "docs" / rel).exists(), rel


def test_pagina_tem_ga_e_og(html):
    assert html.count("G-ZPYEE8P9YC") >= 1
    assert re.search(
        r'og:image" content="https://brasil\.arvor\.co/img/og/apuracao_2T_2026_thread\.png',
        html,
    )


def test_card_transferencia_rotulado(posts):
    i = next(k for k, p in enumerate(posts) if "Transferência" in p["tag_f"])
    assert "1º × 2º turno" in posts[i - 1]["tag_f"]
    corpo = posts[i]["corpo"]
    assert corpo.startswith("Estimativa, não medição.")
    assert "hachurada" in corpo
    assert "url(#tr-" in posts[i]["svg"]


def test_card_logs(posts):
    i = next(k for k, p in enumerate(posts) if p["tag_f"] == "Os logs das urnas")
    assert posts[i - 1]["tag_f"] == "Seções: biometria"
    corpo = posts[i]["corpo"]
    assert "pede explicação" in corpo
    assert "deslocamento de voto" not in corpo


def test_hashtag_so_aceita_fragmento_de_pagina():
    assert problemas_de_texto("veja https://brasil.arvor.co/x.html#logs") == []
    assert problemas_de_texto("leia #apuracao") == ["hashtag"]
    assert problemas_de_texto("arquivo x.csv#a") == ["hashtag"]


def _card(posts, tag):
    achados = [i for i, p in enumerate(posts) if p["tag_f"] == tag]
    assert len(achados) == 1, tag
    return achados[0], posts[achados[0]]


def test_card_onde_flavio_teve_menos_votos(posts):
    i, p = _card(posts, "Onde Flávio teve menos votos")
    assert i == 24
    corpo = p["corpo"]
    assert MIN_CHARS <= len(corpo) <= MAX_CHARS
    assert "—" not in corpo and "–" not in corpo
    c1 = dado("comparacao_1t")
    gov = TP.ufs_governador(dado("governadores"))
    rf = TP.resumo(c1, "flavio", gov)
    rl = TP.resumo(c1, "lula", gov)
    assert rf["n"] == c1["flavio_perdeu_votos"]["n"]
    assert rl["n"] == c1["lula_perdeu_votos"]["n"]
    assert p["metrica_f"] == f"{num(rf['n'])} de {num(c1['n_municipios_completos'])}"
    for valor in (
        rf["perda"],
        rf["delta_adversario"],
        rf["n_adversario_ganhou"],
        rf["n_comparecimento_caiu"],
        -rf["delta_comparecimento"],
        rf["teto"],
        rf["alem_teto"],
        rf["n_alem_teto"],
        round(rf["proporcional"]),
        round(rf["alem_proporcional"]),
        rl["perda"],
        rf["maior"]["perda"],
        rl["maior"]["perda"],
    ):
        assert num(valor) in corpo, valor
    assert pct(100 * rf["proporcional"] / rf["perda"], 1) in corpo
    assert pct(100 * rl["proporcional"] / rl["perda"], 1) in corpo
    assert rf["n_alem_teto_adversario_cobre"] == rf["n_alem_teto"]
    assert "em todos eles Lula ganhou ao menos essa sobra" in corpo
    assert rl["n_comparecimento_caiu"] == rl["n"]
    assert f"o comparecimento caiu em todos os {num(rl['n'])}" in corpo
    todos = {u["uf"] for u in rf["por_uf"] if u["n"] == u["n_uf"]}
    nenhum = {u["uf"] for u in rf["por_uf"] if not u["n"]}
    assert todos == {"AP", "RR"} and nenhum == {"DF", "ES", "GO"}
    assert "No Amapá e em Roraima, Flávio teve menos votos em todos" in corpo
    assert "No Distrito Federal, no Espírito Santo e em Goiás, em nenhum." in corpo
    ctx = TP.contexto_governador(c1, gov)
    assert ctx["com"]["pct"] > ctx["sem"]["pct"]
    assert pct(ctx["com"]["pct"], 1) in corpo and pct(ctx["sem"]["pct"], 1) in corpo
    assert "Achado contrário." in corpo
    assert "mais comum onde houve 2º turno de governador" in corpo
    assert "votos absolutos, não fatia dos válidos" in corpo
    assert "menos votos não identifica eleitor nem motivo" in corpo
    assert f"{URL_DOSSIE}#tu-menos-votos" in corpo
    assert 'id="tu-menos-votos"' in DOSSIE.read_text(encoding="utf-8")
    csv = "assets/apuracao_2t/dataset/municipios_flavio_menos_votos_2t.csv"
    assert f"https://brasil.arvor.co/{csv}" in corpo
    assert (ROOT / "docs" / csv).exists()
    for u in rf["por_uf"]:
        assert f">{u['uf']}<" in p["svg"]
        assert f">{num(u['n'])} de {num(u['n_uf'])}<" in p["svg"]


def test_card_pendencia_documental(posts):
    i, p = _card(posts, "Pendência documental")
    assert i == len(posts) - 1 == 25
    corpo = p["corpo"]
    assert MIN_CHARS <= len(corpo) <= MAX_CHARS
    assert "—" not in corpo and "–" not in corpo
    lg = dado("logs")
    s = lg["metadados"]["serie_mr"]
    d = lg["metadados"]["dossie_metadados"]
    brasil = [x for x in s["estruturais"] if x["ufs"] != ["ZZ"]]
    n_br = sum(x["secoes"] for x in brasil)
    assert n_br == s["voto_estruturais_brasil"]["secoes_com_sinal"]
    n_re = d["entre_turnos_vsc"]["certificado_do_1t_em_outra_secao_no_2t"]
    tot = d["certificado_realocado_totais"]
    casos = dado("metadados")["entre_turnos_vsc"][
        "certificado_do_1t_em_outra_secao_no_2t_casos"
    ]
    assert len(casos) == n_re == tot["2t"]["secoes"]
    assert p["metrica_f"] == f"{num(n_br)} · {num(n_re)}"
    for valor in (
        s["repetidos"],
        s["secoes_em_repeticao"],
        s["pares_entre_lugares"],
        len(brasil),
        n_br,
        n_re,
        tot["mesmo_municipio"],
        tot["mesma_zona"],
        tot["ufs"],
        tot["2t"]["aptos"],
        tot["2t"]["comparecimento"],
        lg["rdv"]["conferem"],
    ):
        assert num(valor) in corpo, valor
    vb = s["voto_estruturais_brasil"]["dif_em_dif_contra_1t"]
    g = next(x for x in d["voto"] if x["grupo"] == "certificado_realocado")
    for bloco in (vb, g["dif_em_dif_contra_1t"]):
        lo, hi = bloco["ic95_pp"]
        assert lo <= 0 <= hi
        assert f"IC95 de {sinal(lo, 2)} a {sinal(hi, 2)}" in corpo
    assert d["certificado_realocado_log_nao_confere"] == 0
    assert lg["rdv"]["divergencias"] == 0
    assert "sem nenhuma divergência" in corpo
    pleito = dado("urnas")["turnos"]["2t"]["carga"]["pleito"]
    assert f"cite o pleito {pleito[0]['valor']} e a seção" in corpo
    assert LEI_ACESSO in corpo
    assert LEI_ACESSO in pendencia_tse(lg)
    assert "analysis/apuracao_2t_2026/dados/metadados.json" in corpo
    assert "entre_turnos_vsc.certificado_do_1t_em_outra_secao_no_2t_casos" in corpo
    assert "relação das mídias de resultado" in corpo
    assert "termo de substituição ou realocação da urna" in corpo
    assert "publica o documento com hash" in corpo
    assert "Atipicidade pede explicação, não prova irregularidade" in corpo
    assert f"{URL_DOSSIE}#logs" in corpo
    assert 'id="logs"' in DOSSIE.read_text(encoding="utf-8")
    for palavra in ("fraude", "eleitores dele", "eleitores dela"):
        assert palavra not in corpo.lower()
    assert f">{num(n_br)}<" in p["svg"] and f">{num(n_re)}<" in p["svg"]
