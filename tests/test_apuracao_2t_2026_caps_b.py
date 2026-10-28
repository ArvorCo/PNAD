"""Capítulos cedo/tarde, turnos e abstenção do dossiê do 2º turno, com os JSONs reais.

Renderiza cada capítulo, confere a ausência de travessão, a presença dos números
centrais lidos do próprio JSON, figuras com viewBox de área positiva e o
noscript das listas longas bem formado. Pula se os dados ainda não existem.
"""

import csv
import importlib
import io
import json
import re

import pytest
from apuracao_2t_2026 import dataset_municipios as DM
from apuracao_2t_2026 import turnos_perdas as TP
from apuracao_2t_2026.dataset import PASTA
from apuracao_2t_2026.pagina_comum import DADOS, Dados
from apuracao_2026.pagina_comum import Capitulo, inteiro, num, sinal_int

pytestmark = pytest.mark.skipif(
    not (DADOS / "cedo_tarde.json").exists(), reason="dados do 2º turno ausentes"
)

CAPS = {
    "cedo_tarde": ("05", ["ct_decis", "ct_transicao"]),
    "turnos": (
        "06",
        [
            "tu_barras_uf",
            "tu_dispersao",
            "tu_perdas_uf",
            "tu_hist_2022",
            "tu_mapas_swing",
        ],
    ),
    "abstencao": (
        "07",
        ["ab_ranking", "ab_mapa_delta", "ab_histograma", "ab_recortes", "ab_quintis"],
    ),
}


@pytest.fixture(scope="module")
def html():
    d = Dados(pasta=DADOS)
    out = {}
    for ident, (numero, _) in CAPS.items():
        mod = importlib.import_module(f"apuracao_2t_2026.pagina_cap_{ident}")
        cap = Capitulo(ident, numero, ident, ident, (), lambda _d: "")
        out[ident] = mod.render(d, cap)
    assert not d.avisos, d.avisos
    return out


def _json(nome):
    return json.loads((DADOS / nome).read_text(encoding="utf-8"))


@pytest.mark.parametrize("ident", CAPS)
def test_sem_travessao_e_sem_pendencia(html, ident):
    h = html[ident]
    assert "—" not in h
    assert "fraude" not in h.lower()
    assert "em preparação" not in h
    assert "<section" not in h
    assert 'class="section-head"' in h


@pytest.mark.parametrize("ident", CAPS)
def test_figuras_presentes_e_com_area(html, ident):
    h = html[ident]
    for fig in CAPS[ident][1]:
        assert f'id="fig-{fig}"' in h, fig
    for w, hh in re.findall(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', h):
        assert float(w) > 0 and float(hh) > 0
    for x in re.findall(r'<rect [^>]*width="(-[\d.]+)"', h):
        pytest.fail(f"retângulo com largura negativa {x}")


@pytest.mark.parametrize("ident", CAPS)
def test_noscript_bem_formado(html, ident):
    h = html[ident]
    assert h.count('<noscript class="fig-src">') == h.count("</noscript>")


def test_cedo_tarde_numeros(html):
    C = _json("cedo_tarde.json")
    h = html["cedo_tarde"]
    sw = [x["swing_h2h_flavio_pp"] for x in C["decis_2t"]]
    assert num(abs(max(sw)), 2) in h and num(abs(min(sw)), 2) in h
    assert num(C["decis_2t"][0]["h2h_flavio"], 2) in h
    assert "Ponte Alta do Norte" in h
    assert h.count("<tr>") >= len(C["ultimos_50"])


def test_turnos_numeros(html):
    C1 = _json("comparacao_1t.json")
    h = html["turnos"]
    b = C1["brasil"]
    assert num(b["t1_h2h_flavio"], 2) in h and num(b["t2_h2h_flavio"], 2) in h
    assert sum(u["swing_h2h_flavio_pp"] < 0 for u in C1["ufs"]) == len(C1["ufs"])
    assert f"Caiu em {len(C1['ufs'])} das {len(C1['ufs'])} UFs" in h
    assert "Macapá (AP)" in h
    assert num(C1["dispersao_municipal"]["n_swing_h2h_pro_flavio"], 0) in h
    # listas completas: uma linha por município em que Flávio ganhou votos
    n = C1["flavio_ganhou_votos"]["n"]
    i = h.index('id="tu-lista-flavio-ganhou-votos"')
    trecho = h[i : h.index("</details>", i)]
    assert trecho.count("<tr>") == n + 1


def test_abstencao_numeros(html):
    A = _json("abstencao.json")
    P = _json("presidente.json")
    h = html["abstencao"]
    assert num(P["nacional"]["pct_abstencao"], 2) in h
    assert num(A["brasil"]["pa_1t_mesmos"], 2) in h
    for uf in ("AP", "RR", "AC"):
        assert uf in h
    assert (
        "82,7" in h
        or num(A["concentracao_abaixo_15"][1]["pct_aptos_abaixo_15_no_pais"], 1) in h
    )
    assert "Hipótese" in h and "Achado contrário" in h


# Contagens e somas do 2º turno de 2026 (comparacao_1t.json de 26/10); falha se a conta mudar.
ESPERADO_PERDAS = {
    "flavio": {
        "n": 938,
        "perda": 133_900,
        "delta_adversario": 486_922,
        "n_comparecimento_caiu": 728,
        "n_adversario_ganhou": 863,
        "delta_comparecimento": -274_667,
    },
    "lula": {
        "n": 79,
        "perda": 16_115,
        "delta_adversario": -31_853,
        "n_comparecimento_caiu": 79,
        "n_adversario_ganhou": 5,
        "delta_comparecimento": -87_567,
    },
}


def _contas_diretas(C1, quem):
    """As mesmas somas, refeitas linha a linha sem passar por turnos_perdas."""
    cols = C1[f"{quem}_perdeu_votos"]["lista"]["colunas"]
    lista = [
        dict(zip(cols, r, strict=True))
        for r in C1[f"{quem}_perdeu_votos"]["lista"]["linhas"]
    ]
    mcols = C1["municipios"]["colunas"]
    mun = {
        r[mcols.index("cd_tse")]: dict(zip(mcols, r, strict=True))
        for r in C1["municipios"]["linhas"]
    }
    adv = TP.ADVERSARIO[quem]
    dc = [mun[m["cd_tse"]]["delta_comparecimento_votos"] for m in lista]
    return lista, {
        "n": len(lista),
        "perda": -sum(m[f"delta_votos_{quem}"] for m in lista),
        "delta_adversario": sum(m[f"delta_votos_{adv}"] for m in lista),
        "n_comparecimento_caiu": sum(v < 0 for v in dc),
        "n_adversario_ganhou": sum(m[f"delta_votos_{adv}"] > 0 for m in lista),
        "delta_comparecimento": sum(dc),
    }


def _subparte(h):
    i = h.index('<h3 id="tu-menos-votos">Onde Flávio teve menos votos no 2º turno')
    return h[i : h.index("tu-lista-flavio-ganhou-votos", i)]


@pytest.mark.parametrize("quem", TP.CANDIDATOS)
def test_turnos_menos_votos_listas_completas(html, quem):
    C1 = _json("comparacao_1t.json")
    lista, contas = _contas_diretas(C1, quem)
    assert contas == ESPERADO_PERDAS[quem]
    assert C1[f"{quem}_perdeu_votos"]["n"] == contas["n"]
    R = TP.resumo(C1, quem)
    for k, v in contas.items():
        assert R[k] == v, k
    h = html["turnos"]
    i = h.index(f'id="tu-lista-{quem}-menos-votos"')
    trecho = h[i : h.index("</details>", i)]
    assert trecho.count("<tr>") == contas["n"] + 1
    assert 'data-ordena="1"' in trecho and "<thead>" in trecho
    assert 'class="ct-lista-c"' in trecho and '<details class="ct-det"' in h[i - 40 : i]
    # da maior perda para a menor, e o mesmo conjunto de municípios do JSON
    linhas = [
        re.findall(r"<td(?: data-v=([^>]*))?>([^<]*)", tr)
        for tr in trecho.split("<tr>")[2:]
    ]
    assert len(linhas) == contas["n"]
    assert all(len(cel) == 15 for cel in linhas)
    ms = TP.municipios(C1, quem)
    assert [int(cel[5][0]) for cel in linhas] == [m[f"delta_votos_{quem}"] for m in ms]
    assert [(cel[0][1], cel[2][0]) for cel in linhas] == [
        (m["uf"], str(m["aptos"])) for m in ms
    ]
    perdas = [m["perda"] for m in ms]
    assert perdas == sorted(perdas, reverse=True)
    assert sum(perdas) == contas["perda"]
    linhas_csv = list(
        csv.reader(io.StringIO((PASTA / DM.ARQUIVOS[quem]).read_text(encoding="utf-8")))
    )
    assert linhas_csv[0] == DM.NOMES
    corpo = linhas_csv[1:]
    assert len(corpo) == contas["n"]
    assert {r[1] for r in corpo} == {m["cd_tse"] for m in lista}
    assert [r[1] for r in corpo] == [m["cd_tse"] for m in TP.municipios(C1, quem)]
    dif = DM.NOMES.index(f"dif_{quem}")
    assert -sum(int(r[dif]) for r in corpo) == contas["perda"]


def test_turnos_menos_votos_texto(html):
    C1 = _json("comparacao_1t.json")
    h = html["turnos"]
    sub = _subparte(h)
    assert (
        "Votos absolutos, não fatia dos válidos; menos votos não identifica eleitor nem motivo"
        in sub
    )
    for quem in TP.CANDIDATOS:
        e = ESPERADO_PERDAS[quem]
        assert f"{inteiro(e['n'])}" in sub
        assert inteiro(e["perda"]) in sub
        assert inteiro(abs(e["delta_comparecimento"])) in sub
    f = ESPERADO_PERDAS["flavio"]
    assert (
        f"Em {inteiro(f['n'])} dos {inteiro(C1['n_municipios_completos'])} municípios"
        in sub
    )
    assert sinal_int(f["delta_adversario"]) in sub
    assert f"ganhou votos em {inteiro(f['n_adversario_ganhou'])}" in sub
    assert f"caiu em {inteiro(f['n_comparecimento_caiu'])} dos {inteiro(f['n'])}" in sub
    assert "selo-verificado" in sub and "selo-inferencia" in sub
    assert (
        'href="assets/apuracao_2t/dataset/municipios_flavio_menos_votos_2t.csv"' in sub
    )
    assert 'href="assets/apuracao_2t/dataset/municipios_lula_menos_votos_2t.csv"' in sub
    assert "Macapá (AP)" in sub and "Mazagão (AP)" in sub
    # contexto do 2º turno de governador, lido de governadores.json
    for uf in TP.ufs_governador(_json("governadores.json")):
        assert uf in sub
    for proibido in ("—", "fraude", "eleitores dele", "eleitores dela"):
        assert proibido not in sub.lower()


def test_reguas_da_decomposicao_sinteticas():
    """Teto e régua proporcional numa lista de dois municípios montada à mão."""
    cols = [
        "cd_tse",
        "uf",
        "nome",
        "regiao",
        "aptos",
        "t1_flavio",
        "t1_lula",
        "delta_votos_flavio",
        "delta_votos_lula",
        "delta_comparecimento_votos",
        "t1_comparecimento",
    ]
    linhas = [
        ["00001", "AC", "A", "Norte", 1000, 300, 500, -100, 50, -60, 1000],
        ["00002", "AM", "B", "Norte", 900, 200, 400, -30, 80, 20, 800],
    ]
    C1 = {
        "municipios": {"colunas": cols, "linhas": linhas},
        "flavio_perdeu_votos": {"colunas": cols[:3], "linhas": [r[:3] for r in linhas]},
    }
    C1["flavio_perdeu_votos"] = {"n": 2, "lista": C1["flavio_perdeu_votos"]}
    a, b = TP.municipios(C1, "flavio", {"AM"})
    assert (a["teto_comparecimento"], a["alem_teto"]) == (60, 40)
    assert a["proporcional_comparecimento"] == pytest.approx(18.0)
    assert a["alem_proporcional"] == pytest.approx(82.0)
    assert (b["teto_comparecimento"], b["alem_teto"]) == (0, 30)
    assert b["proporcional_comparecimento"] == 0 and b["governador_2t"]
    assert not a["governador_2t"]
