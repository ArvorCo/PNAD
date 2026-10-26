"""Politize-se: esquema dos JSON, identidades de votos, frases e página."""

from __future__ import annotations

import gzip
import json
import re
from pathlib import Path

import pytest
from politize_se import saida, tempo, textos, urna

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "docs/assets/politize_se/dados"
PAGINA = ROOT / "docs/politizese.html"
CANDIDATOS = {"Flávio", "Lula"}
# palavras com maiúscula permitidas no meio das frases (não são nomes de pessoas)
PERMITIDAS = CANDIDATOS | {"TSE", "Brasília", "Explicação", "Liberados", "Sem"}


def _zona(uf: str, z: int) -> dict:
    with gzip.open(DADOS / "zona" / uf / f"{z}.json.gz", "rt", encoding="utf-8") as f:
        return json.load(f)


def _linhas(t: dict) -> list[dict]:
    return [dict(zip(t["colunas"], x, strict=True)) for x in t["linhas"]]


# ------------------------------------------------------------------ funções puras


def test_tempo_brasilia_e_correcao():
    assert tempo.minutos_locais("2026-10-25 06:00:01", "2026-10-25") == 360
    assert tempo.para_brasilia(360, "AC") == 480
    assert tempo.para_brasilia(360, "ZZ") == 360
    # município do oeste do AM: abertura modal uma hora antes do esperado
    assert tempo.correcoes_municipais(
        "AM", {"02020": [420, 420, 421], "02550": [480]}
    ) == {"02020": 60}
    assert tempo.hhmm(1021) == "17h01"
    assert tempo.hhmm(1445) == "00h05 do dia seguinte"


def test_urna_situacao():
    k = ("SP", "71072", 1, 10)
    assert urna.situacao(1, None, "a", None, None, None, k) is None
    assert urna.situacao(None, 2, None, "b", 1, None, k) == "sem_1t"
    assert urna.situacao(1, 1, "a", "a", 1, None, k) == "mesma"
    assert urna.situacao(1, 1, "a", "b", 1, None, k) == "mesma_recarga"
    assert urna.situacao(1, 2, "a", "b", 4, None, k) == "reserva"
    assert urna.situacao(1, 2, "a", "b", 1, None, k) == "nova"
    assert (
        urna.situacao(1, 2, "a", "b", 1, ("SP", "71072", 1, 11), k)
        == "outra_secao_zona"
    )
    assert (
        urna.situacao(1, 2, "a", "b", 1, ("SP", "71072", 2, 11), k)
        == "outra_secao_municipio"
    )
    assert (
        urna.situacao(1, 2, "a", "b", 1, ("SP", "70000", 2, 11), k) == "outro_municipio"
    )


CAT = {
    "mudanca": {"A": {"nome": "Volta ao local de sempre"}},
    "log": {
        "bateria": "Funcionou na bateria",
        "erro_tecnico": "Erro técnico registrado",
    },
    "log_rotina": ["bateria"],
    "log_niveis": {
        0: "Registro de rotina",
        1: "Um sinal",
        2: "Sinais combinados",
        3: "Conferir o arquivo",
    },
    "fiscal": {"alta": "Prioridade alta"},
}


def _secao(**kw):
    base = {
        "uf": "SP",
        "bu2": True,
        "pequena": False,
        "flavio1": 100,
        "lula1": 120,
        "terceira1": 30,
        "flavio2": 130,
        "lula2": 125,
        "fatia_f1": 45.5,
        "fatia_f2": 51.0,
        "comp_pct1": 80.0,
        "comp_pct2": 82.3,
        "bn_pct1": 3.0,
        "bn_pct2": 4.0,
        "sem_bio_pct1": 2.0,
        "sem_bio_pct2": 2.1,
        "ano_nasc_pct1": 5.0,
        "ano_nasc_pct2": 6.0,
        "enc1": 1030,
        "enc2": 1025,
        "rec2": 1200,
        "urna_situacao": "reserva",
        "contingencia2": True,
        "sinais": ["delta", "tardia"],
        "explicacoes": ["perto_19h"],
        "agreg_igual": False,
        "mudanca": {"cat": "A", "real": True, "dist_m": 1234},
        "log1_atencao": 1,
        "log1_sinais": ["bateria", "erro_tecnico"],
        "fiscal_nivel": "alta",
    }
    base.update(kw)
    return base


def test_frases_cobrem_casos_e_respeitam_regras():
    casos = [
        _secao(),
        _secao(sinais=[], explicacoes=[]),
        _secao(sinais=["papel"], explicacoes=[]),
        _secao(bu2=False, flavio2=None, lula2=None, fatia_f2=None),
        _secao(pequena=True),
        _secao(flavio2=100, lula2=100),
        _secao(
            uf="ZZ",
            urna_situacao="outro_municipio",
            mudanca={"cat": "A", "real": False},
        ),
    ]
    vistos = set()
    for r in casos:
        fr = textos.frases_secao(r, CAT)
        vistos |= {f[0] for f in fr}
        _confere_texto(textos.render(fr))
    p = {
        "n_secoes": 5,
        "n_bu2": 3,
        "fatia_f2": 52.0,
        "fatia_f1_par": 48.0,
        "comp_pct2": 80.0,
        "d_comp_pp": 1.2,
        "secoes_sinal": 2,
        "escore_max": 3,
        "secoes_mudaram": 1,
    }
    m = {"d_fatia_pp": 2.5, "comp_pct2": 79.0}
    fr = textos.frases_local(p, m)
    vistos |= {f[0] for f in fr}
    _confere_texto(textos.render(fr))
    assert {
        "res2",
        "vs1_subiu",
        "sinais_n",
        "explica",
        "mud_real",
        "p_cobertura",
    } <= vistos
    for cod, modelo in textos.FRASES.items():
        _confere_texto(modelo, cod)


def _confere_texto(t: str, onde: str = "") -> None:
    assert "—" not in t and "–" not in t, onde
    assert "fraude" not in t.lower(), onde
    assert "{" not in t or onde, t
    for frase in re.split(r"(?<=[.:;])\s+", t):
        palavras = re.findall(r"\b[A-ZÁÉÍÓÚÂÊÔÃÕ][a-záéíóúâêôãõç]+\b", frase)
        for w in palavras[1:]:
            assert w in PERMITIDAS, (w, frase)


def _log(a1, a2, f1=None, f2=None, **kw):
    r = _secao(
        log1_atencao=a1,
        log1_sinais=["erro_tecnico"] if a1 else [],
        log1_familias=f1 if f1 is not None else (["energia"] if a1 else []),
        log2_atencao=a2,
        log2_sinais=["erro_tecnico"] if a2 else [],
        log2_familias=f2 if f2 is not None else (["energia"] if a2 else []),
    )
    r.update(kw)
    return {f[0] for f in textos.frases_secao(r, CAT)}, textos.render(
        textos.frases_secao(r, CAT)
    )


def test_regra_log_entre_turnos():
    cods, t = _log(1, 3)
    assert (
        "log_subiu" in cods
        and "subiu de um sinal no 1º turno para conferir o arquivo" in t
    )
    assert "log_igual" in _log(2, 2)[0]
    assert "O mesmo sinal já aparecia no 1º turno" in _log(1, 1)[1]
    assert "log_igual_outro" in _log(2, 2, ["energia"], ["ritmo"])[0]
    assert "log2_0_antes" in _log(3, 0)[0]
    assert "log2_n" in _log(3, 1)[0]
    cods, t = _log(
        0,
        1,
        log2_reinicios=[[775, 133, 68]],
        log2_bateria="simultanea",
        log2_erro_mr=1,
    )
    assert {"log_reinicio_1", "log_bat_simultanea", "log_mr"} <= cods
    assert "às 12h55, com 133 votos já computados; depois vieram mais 68 votos" in t
    _confere_texto(t)
    # sem log do 2º turno, cai na frase do 1º
    assert "log1_n" in _log(1, None)[0]


# ------------------------------------------------------------------ dados gerados

pytestmark_dados = pytest.mark.skipif(
    not (DADOS / "indice.json").exists(), reason="dados do Politize-se não gerados"
)


@pytestmark_dados
def test_indice_esquema_e_cobertura():
    ind = json.loads((DADOS / "indice.json").read_text(encoding="utf-8"))
    assert ind["versao"] == saida.VERSAO
    assert ind["frases_codigos"] == list(ind["frases"])
    nac = ind["cobertura"]["nacional"]
    assert nac["secoes"] == sum(c["secoes"] for c in ind["cobertura"]["ufs"].values())
    assert 0 <= nac["com_bu_2t"] <= nac["secoes"]
    assert ind["logs_2t"]["disponivel"] is True
    for uf, zs in ind["zonas"].items():
        for z in zs[:3]:
            assert (DADOS / "zona" / uf / f"{z}.json.gz").exists()
    cols = ind["municipios"]["colunas"]
    for x in ind["municipios"]["linhas"][:50]:
        assert (DADOS / x[cols.index("arquivo")]).exists()
    assert "—" not in (DADOS / "indice.json").read_text(encoding="utf-8")


@pytestmark_dados
def test_zona_ac_identidades_e_frases():
    ind = json.loads((DADOS / "indice.json").read_text(encoding="utf-8"))
    cods = ind["frases_codigos"]
    n_bu = n_log2 = 0
    for z in ind["zonas"]["AC"]:
        d = _zona("AC", z)
        assert d["secoes"]["colunas"] == saida.COLS_SECAO
        assert d["locais"]["colunas"] == saida.CAMPOS_LOCAL
        locais = _linhas(d["locais"])
        for s in _linhas(d["secoes"]):
            assert s["li"] is not None and 0 <= s["li"] < len(locais)
            n_bu += s["bu2"]
            if s["log2_atencao"] is not None:
                n_log2 += 1
                assert 0 <= s["log2_atencao"] <= 3
                for rein in s["log2_reinicios"]:
                    assert len(rein) == 3 and (rein[1] is None or rein[1] >= 0)
                assert s["log2_bateria"] in (None, "simultanea", "isolada", "votacao")
            for t in ("1", "2"):
                comp = s[f"comp{t}"]
                if comp is None or s[f"flavio{t}"] is None:
                    continue
                outros = s["terceira1"] if t == "1" else 0
                assert comp == (
                    s[f"flavio{t}"]
                    + s[f"lula{t}"]
                    + outros
                    + s[f"brancos{t}"]
                    + s[f"nulos{t}"]
                )
                assert s[f"aptos{t}"] >= comp
                assert s[f"abst_pct{t}"] == pytest.approx(
                    100 * (s[f"aptos{t}"] - comp) / s[f"aptos{t}"], abs=0.051
                )
            if s["pequena"]:
                assert s["flavio1"] is None and s["flavio2"] is None
            texto = textos.render([[cods[f[0]], *f[1:]] for f in s["frases"]])
            _confere_texto(texto)
        for p in locais:
            texto = textos.render([[cods[f[0]], *f[1:]] for f in p["frases"]])
            _confere_texto(texto)
    assert n_bu == ind["cobertura"]["ufs"]["AC"]["com_bu_2t"]
    assert n_log2 > 0.95 * n_bu


@pytestmark_dados
def test_mun_contrato_do_mapa():
    arqs = sorted((DADOS / "mun" / "AC").glob("*.json"))
    assert arqs
    d = json.loads(arqs[0].read_text(encoding="utf-8"))
    assert d["locais"]["colunas"] == saida.COLS_LOCAL_MUN
    for p in _linhas(d["locais"]):
        assert re.fullmatch(r"politizese\.html#uf=AC&z=\d+&s=\d+", p["link"])


# ------------------------------------------------------------------ página


def test_pagina_ga_e_regras():
    html = PAGINA.read_text(encoding="utf-8")
    assert html.count("G-ZPYEE8P9YC") == 2  # src do gtag e config, uma tag só
    assert html.index("googletagmanager") < html.index("</head>")
    assert "—" not in html and "fraude" not in html.lower()
    assert (
        'href="apuracao_2T_2026.html"' in html and 'href="politizese_mapa.html"' in html
    )
    js = (ROOT / "docs/assets/politize_se/app.js").read_text(encoding="utf-8")
    assert "log2_reinicios" in js and "log2_meta" in js
    assert "—" not in js and "location.hash =" not in js and "pushState" not in js
    assert "politize/" not in js.replace("politize_se/", "")
    antigo = (ROOT / "docs/politizesuavizinhanca.html").read_text(encoding="utf-8")
    assert 'href="politizese.html"' in antigo
    atalho = (ROOT / "docs/politize-se/index.html").read_text(encoding="utf-8")
    assert "/politizese.html" in atalho and "noindex" in atalho
