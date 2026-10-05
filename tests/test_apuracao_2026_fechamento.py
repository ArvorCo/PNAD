"""Fechamento das seções (encerramento e recebimento, 2022 e 2026).

Dados sintéticos, um ZIP mínimo criado no diretório temporário e uma fixture
JSON recortada da saída real. Nada aqui lê o banco da coleta nem a rede.
"""

import json
import math
import re
import zipfile
from itertools import pairwise
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from apuracao_2026 import fechamento_base as fb
from apuracao_2026 import fechamento_modelo as fm
from apuracao_2026 import fechamento_persist as fp
from apuracao_2026 import fechamento_texto as ft
from apuracao_2026 import fechamento_voto as fv
from apuracao_2026 import pagina_texto_fechamento as ptf
from apuracao_2026.pagina_figuras import FIGURAS

RAIZ = Path(__file__).resolve().parents[1]
FIXTURE = RAIZ / "tests/fixtures/apuracao_2026/fechamento_fixture.json"
NOMES = [
    "fechamento_regioes",
    "fechamento_persistencia",
    "fechamento_voto_lula",
    "fechamento_voto_zona",
]


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- funções puras


def test_faixas_de_aptos_e_de_hora():
    assert fb.faixa_aptos([0, 199, 200, 349, 350, 400, 1200, None]) == [
        "até 199",
        "até 199",
        "200 a 249",
        "300 a 349",
        "350 a 399",
        "400 ou mais",
        "400 ou mais",
        None,
    ]
    assert fb.faixa_hora([-1, 0, 29.9, 30, 59, 60, 119, 120, 600, float("nan")]) == [
        "até 17:00",
        "17:00 a 17:30",
        "17:00 a 17:30",
        "17:30 a 18:00",
        "17:30 a 18:00",
        "18:00 a 19:00",
        "18:00 a 19:00",
        "depois de 19:00",
        "depois de 19:00",
        None,
    ]


def test_resumo_tempo_e_parcelas():
    x = list(range(200))  # 0 a 199 minutos depois das 17h
    r = fb.resumo_tempo(x)
    assert r["secoes"] == 200
    assert r["mediana"] == pytest.approx(99.5)
    assert r["depois_1730_pct"] == pytest.approx(85.0)
    assert r["depois_1800_pct"] == pytest.approx(70.0)
    assert r["depois_1900_pct"] == pytest.approx(40.0)
    assert fb.resumo_tempo([float("nan")]) is None


def test_acumulada_na_grade():
    cur = fb.acumulada([0, 10, 10, 400])
    assert len(cur) == len(fb.GRADE)
    assert cur[0] == 25.0  # só o 0 está até 17:00
    assert cur[1] == 75.0  # até 17:10
    assert cur[-1] == 100.0
    assert all(a <= b for a, b in pairwise(cur))


def test_rotulos_de_hora_e_duracao():
    assert fb.rotulo_hora(0) == "17:00"
    assert fb.rotulo_hora(65.4) == "18:05"
    assert fb.rotulo_hora(430) == "00:10 (dia seguinte)"
    assert fb.rotulo_hora(None) == "n/d"
    assert fb.rotulo_duracao(6.2) == "6 min"
    assert fb.rotulo_duracao(79) == "1h19"


def test_spearman_e_pearson():
    assert fb.spearman([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert fb.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)
    assert fb.spearman([1, 2, 3, 4], [1, 4, 9, 100]) == pytest.approx(1.0)
    assert math.isnan(fb.spearman([1, 1, 1], [1, 2, 3]))
    assert fb.pearson([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)


def test_lacuna_acha_o_maior_buraco():
    x = [*np.arange(0, 150, 0.5), *np.arange(180, 200, 0.25)]
    lac = fb.lacuna(x)
    assert lac["ultimo_antes_min"] == pytest.approx(149.5)
    assert lac["primeiro_depois_min"] == pytest.approx(180.0)
    assert lac["minutos"] == pytest.approx(30.5)
    assert lac["secoes_5min_depois"] == 20


# ---------------------------------------------------------------- derivação de horas


def _bu(**kw) -> pd.DataFrame:
    base = {
        "uf": ["ac", "sp", "mt"],
        "mun": ["01007", "71072", "90069"],
        "zona": [9, 1, 53],
        "secao": [1, 1, 113],
        "fuso": [2.0, 0.0, 1.0],
        "abertura": [
            "2026-10-04 06:00:01",
            "2026-10-04 08:00:00",
            "2026-10-04 07:42:34",
        ],
        "encerramento": [
            "2026-10-04 15:07:06",
            "2026-10-04 19:30:00",
            "2026-10-04 18:05:04",
        ],
        "dr_hr": ["2026-10-04 18:55:55", "2026-10-04 20:00:00", "2026-10-04 18:58:00"],
        "comparecimento": [241, 400, 300],
        "hab_ano_nascimento": [8, 40, 0],
        "comp_sem_biometria": [10, 0, 3],
        "aptos": [308, 450, 350],
        "tipo_inferido": ["escola ou universidade", "zona rural", "outro"],
    }
    base.update(kw)
    return pd.DataFrame(base)


def test_derivar_converte_para_brasilia_e_marca_fuso_inconsistente():
    df = fb.derivar(_bu())
    assert df.loc[0, "enc_min"] == pytest.approx(7.1)  # 15:07 no Acre = 17:07
    assert df.loc[0, "rec_min"] == pytest.approx(115 + 55 / 60)
    assert df.loc[1, "enc_min"] == pytest.approx(150)
    assert df.loc[1, "horas"] == pytest.approx(11.5)
    assert df.loc[1, "votantes_hora"] == pytest.approx(400 / 11.5)
    assert df.loc[1, "ano_nascimento_pct"] == pytest.approx(10.0)
    # recebido às 18:58 com encerramento convertido 19:05: relógio ou fuso errado
    assert bool(df.loc[2, "fuso_inconsistente"])
    assert math.isnan(df.loc[2, "enc_min"])
    assert df.loc[1, "faixa_hora"] == "depois de 19:00"
    assert df.loc[1, "grupo_tipo"] == "zona rural, assentamento ou quilombo"
    assert df.loc[0, "grupo_tipo"] == "escola fora de zona rural"


def test_tipos_2022_le_o_zip_em_blocos_e_usa_cache(tmp_path):
    cab = (
        '"NR_TURNO";"SG_UF";"CD_MUNICIPIO";"NR_ZONA";"NR_SECAO";"CD_CARGO";'
        '"NM_LOCAL_VOTACAO";"DS_LOCAL_VOTACAO_ENDERECO"\n'
    )
    linhas = [
        '"1";"AM";"2119";"36";"30";"1";"ESCOLA MUNICIPAL INDÍGENA X";"ALDEIA Y"\n',
        '"1";"SP";"71072";"1";"1";"1";"EMEF JOAO";"RUA A, 10"\n',
        '"1";"MA";"7005";"10";"4";"1";"U.E. MARIA";"POVOADO SAO JOSE"\n',
        '"2";"SP";"71072";"1";"1";"1";"EMEF JOAO";"RUA A, 10"\n',
    ]
    zp = tmp_path / "detalhe.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr(
            "detalhe_votacao_secao_2022_BR.csv",
            (cab + "".join(linhas)).encode("latin-1"),
        )
    cache = tmp_path / "tipos.csv.gz"
    t = fb.tipos_2022(zp, cache).set_index("uf")["tipo_2022"].to_dict()
    assert t == {
        "am": "aldeia ou terra indígena",
        "sp": "escola ou universidade",
        "ma": "zona rural",
    }
    assert cache.exists()
    assert len(fb.tipos_2022(zp, cache)) == 3


# ---------------------------------------------------------------- estimadores


def _zonas(efeito: float, semente: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(semente)
    linhas = []
    for z in range(40):
        base = rng.uniform(20, 70)  # geografia: cada zona vota diferente
        for s in range(20):
            tarde = s < 5
            lula = base + (efeito if tarde else 0.0)
            validos = 200
            linhas.append(
                {
                    "uf": "ce",
                    "mun": f"{z:05d}",
                    "zona": z,
                    "secao": s,
                    "v13": round(validos * lula / 100),
                    "v22": round(validos * (100 - lula) / 100),
                    "validos": validos,
                    "votantes": 210,
                    "comparecimento": 210,
                    "aptos": 300,
                    "lula_pct": 100 * round(validos * lula / 100) / validos,
                    "tarde": tarde,
                    "enc_min": 90.0 if tarde else 5.0,
                }
            )
    return pd.DataFrame(linhas)


def test_dentro_zona_recupera_efeito_conhecido():
    df = _zonas(4.0)
    r = fm.dentro_zona(df, df["tarde"], {"lula_pp": ("v13", "validos")})
    assert r["unidades"] == 40
    assert r["lula_pp"]["estimativa"] == pytest.approx(4.0, abs=0.3)
    lo, hi = r["lula_pp"]["ic95"]
    assert lo <= 4.0 <= hi


def test_fe_wls_absorve_a_zona_e_cobre_o_coeficiente():
    rng = np.random.default_rng(7)
    n_z, n_s = 80, 15
    zona = np.repeat(np.arange(n_z), n_s)
    efeito_zona = rng.normal(0, 10, n_z)[zona]
    x = (
        rng.uniform(0, 3, n_z * n_s) + 0.5 * efeito_zona / 10
    )  # x correlacionado com a zona
    y = 50 + efeito_zona + 2.0 * x + rng.normal(0, 1, n_z * n_s)
    w = rng.uniform(100, 300, n_z * n_s)
    r = fm.fe_wls(y, x, zona, w, ["x"], boot=400)
    c = r["coeficientes"]["x"]
    assert c["estimativa"] == pytest.approx(2.0, abs=0.1)
    assert c["ic95"][0] <= 2.0 <= c["ic95"][1]
    assert r["zonas"] == n_z
    bruta = fm.fe_wls(y, x, zona, w, ["x"], absorver=False, boot=400)
    assert bruta["coeficientes"]["x"]["estimativa"] > 3.0  # a geografia infla o bruto
    again = fm.fe_wls(y, x, zona, w, ["x"], boot=400)
    assert again["coeficientes"]["x"] == c  # semente fixa


def test_dummies_sem_a_referencia_e_sem_categoria_vazia():
    s = pd.Series(["a", "b", "a", "c"])
    m, nomes = fm.dummies(s, "a", ["a", "b", "c", "d"])
    assert nomes == ["b", "c"]
    assert m.tolist() == [[0, 0], [1, 0], [0, 0], [0, 1]]


def test_conta_da_secao_contra_resto_e_contra_demais():
    g = pd.DataFrame(
        {
            "uf": ["ce"] * 4,
            "mun": ["1"] * 4,
            "zona": [1] * 4,
            "v13": [80, 60, 40, 40],
            "v22": [20, 40, 60, 60],
            "validos": [100, 100, 100, 100],
        }
    )
    g["lula_pct"] = g["v13"]
    tot = g["v13"].sum()
    g["zona_resto_lula_pct"] = 100 * (tot - g["v13"]) / (400 - 100)
    tarde = pd.Series([True, True, False, False])
    # contra o resto (inclui a outra tardia): 80 − 46,67 e 60 − 53,33
    assert fm.dif_zona_w6(g[tarde], "lula") == pytest.approx(20.0, abs=0.01)
    # contra só as não tardias (40%): 40 e 20
    assert fm.dif_secao_contra_demais(g, tarde, "lula") == pytest.approx(30.0)


def test_faixa_votantes():
    assert fv.faixa_votantes(pd.Series([10, 150, 249, 350, 900])) == [
        "até 149",
        "150 a 199",
        "200 a 249",
        "350 ou mais",
        "350 ou mais",
    ]


# ---------------------------------------------------------------- persistência


def test_persistencia_marca_o_decimo_mais_tardio_nos_dois_anos():
    idx = pd.MultiIndex.from_tuples(
        [("ce", f"{i:05d}") for i in range(100)], names=["uf", "mun"]
    )
    m26 = pd.DataFrame(
        {
            "med26": np.arange(100, dtype=float),
            "secoes_2026": 10,
            "cobertura": 1.0,
        },
        index=idx,
    )
    med22 = np.arange(100, dtype=float)
    med22[95:] = -1  # cinco dos dez mais tardios de 2026 chegaram cedo em 2022
    m22 = pd.DataFrame({"med22": med22, "secoes_2022": 10}, index=idx)
    m26.loc[("ce", "00000"), "cobertura"] = 0.5  # cobertura baixa: fora
    m = fp.comparar(m26, m22)
    assert len(m) == 99
    assert int(m["persistente"].sum()) == 5
    cor = fp.correlacoes(m)
    assert cor["municipios"] == 99
    assert -1 <= cor["spearman"] <= 1


# ---------------------------------------------------------------- figuras e texto


def _tips(h: str) -> dict:
    m = re.search(
        r'<script type="application/json" class="tips">(.*?)</script>', h, re.DOTALL
    )
    assert m
    return json.loads(m.group(1).replace("<\\/", "</"))


@pytest.mark.parametrize("nome", NOMES)
def test_figura_sobre_a_fixture(nome):
    F = _fixture()
    h = FIGURAS[nome]({"fechamento": F})
    assert h.startswith(f'<figure class="reveal fig-i" id="fig-{nome}"')
    assert h.count("<svg") == 1 and "<title>" in h and "<desc>" in h
    assert "—" not in h and "fraude" not in h.lower()
    tips = _tips(h)
    linhas = tips.get("_rows", {}).get("linhas", [])
    chaves = re.findall(r'data-k="([^"]+)"', h)
    assert chaves or 'data-near="1"' in h
    for k in chaves:
        assert k in tips or (k.startswith("r") and int(k[1:]) < len(linhas)), k
    if "xy" in tips.get("_rows", {}):
        assert len(tips["_rows"]["xy"]) == len(linhas)
    tamanhos = [float(x) for x in re.findall(r'<text[^>]*font-size="([0-9.]+)"', h)]
    assert min(tamanhos) >= 13
    n = len(F["cobertura"]["ufs_completas"])
    assert f"Cobertura parcial: {n} UFs completas" in h


@pytest.mark.parametrize("nome", NOMES)
def test_figura_cobertura_completa(nome):
    F = _fixture()
    F["cobertura"]["parcial"] = False
    h = FIGURAS[nome]({"fechamento": F})
    assert "Cobertura completa" in h


def test_figura_ausente_vira_pendente():
    h = FIGURAS["fechamento_regioes"]({})
    assert 'class="pendente"' in h and "fechamento" in h


def test_listas_vazias_dizem_que_nao_ha():
    F = _fixture()
    F["tamanho"]["linhas"] = []
    F["lula_hora"]["spearman_uf"] = []
    assert "nenhuma seção nesta condição" in FIGURAS["fechamento_regioes"](
        {"fechamento": F}
    )
    assert "nenhuma seção nesta condição" in FIGURAS["fechamento_voto_lula"](
        {"fechamento": F}
    )


def test_faixa_vazia_aparece_como_vazia():
    F = _fixture()
    h = FIGURAS["fechamento_voto_lula"]({"fechamento": F})
    vazia = [x for x in F["lula_hora"]["bruta"] if x["secoes"] == 0]
    if vazia:
        assert "nenhuma seção nesta condição" in h


def test_bloco_de_texto_figura_antes_do_paragrafo():
    F = _fixture()
    h = ptf.bloco(F, lambda nome: f'<figure id="fig-{nome}"></figure>')
    assert h.startswith("<h3>Onde a votação termina tarde, em dois anos</h3>")
    assert "—" not in h and "fraude" not in h.lower()
    pos = [h.index(f'id="fig-{n}"') for n in NOMES]
    assert pos == sorted(pos)
    assert "Juízo editorial" in h and "Hipótese, não achado" in h
    assert "fiscal de partido" in h and "art. 65" in h
    assert h.index("Achado contrário") < h.index('id="fig-fechamento_regioes"')
    # todo parágrafo com selo vem depois da primeira figura ou é abertura
    assert "selo-verificado" in h and "selo-inferencia" in h


def test_achados_e_memorando_sem_travessao():
    F = _fixture()
    A = ft.achados(F)
    assert set(A) == {"contrario", "verificado", "inferido", "juizo", "hipotese"}
    assert all(A[k] for k in A)
    texto = json.dumps(A, ensure_ascii=False)
    assert "—" not in texto and "fraude" not in texto.lower()
    assert "pianista" in " ".join(A["hipotese"])
    assert "fiscal" in " ".join(A["juizo"])
    md = ft.memorando({**F, "achados": A})
    assert md.startswith("# ") and "—" not in md
    assert "## Fontes legais" in md and "## Limites" in md


def test_fixture_respeita_o_contrato():
    F = _fixture()
    for chave in ptf.CHAVES:
        atual = F
        for parte in chave.split("."):
            atual = atual[parte]
    assert F["cobertura"]["parcial"] in (True, False)
    assert {x["faixa"] for x in F["lula_hora"]["bruta"]} == {
        n for n, _a, _b in fb.FAIXAS_HORA
    }
    ref = F["lula_hora"]["referencia"]
    for m in F["lula_hora"]["por_faixa"]:
        assert ref not in m["lula"]["coeficientes"]
