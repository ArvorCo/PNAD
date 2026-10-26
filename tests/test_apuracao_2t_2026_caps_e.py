"""Capítulo `anomalia` (Grupos) do dossiê do 2º turno (docs/apuracao_2T_2026.html).

Renderiza com um JSON sintético no esquema da seção 6 de
``analysis/apuracao_2t_2026/CONTRATO_ANOMALIA.md`` (sempre) e com o JSON real do
motor (quando existe). Confere as figuras obrigatórias da seção 8, as regras de
texto da casa, a degradação sem o arquivo pesado e as cores dos grupos.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import random
import re
from pathlib import Path

import pytest
from apuracao_2t_2026 import pagina_cap_anomalia as CA
from apuracao_2t_2026 import pagina_fig_anomalia as FA
from apuracao_2t_2026 import pagina_fig_anomalia_b as FAB
from apuracao_2t_2026 import pagina_fig_anomalia_base as B
from apuracao_2t_2026 import pagina_texto_anomalia as TA
from apuracao_2t_2026 import pagina_view as V
from apuracao_2t_2026.pagina_comum import DADOS, Dados
from apuracao_2026.pagina_comum import Capitulo, inteiro
from apuracao_2026.pagina_fig_base import PAPER, contraste

ROOT = Path(__file__).resolve().parents[1]
MODULOS = [
    "pagina_cap_anomalia.py",
    "pagina_fig_anomalia.py",
    "pagina_fig_anomalia_b.py",
    "pagina_fig_anomalia_base.py",
    "pagina_texto_anomalia.py",
]
FIGURAS = [
    "an_bic",
    "an_kmeans",
    "an_grupos",
    "an_regiao",
    "an_pca",
    "an_voto",
    "an_mapa",
]
REAL = DADOS / "anomalia_ml.json"
COLS = [
    "lula1",
    "flavio1",
    "outros1",
    "brancos1",
    "nulos1",
    "lula2",
    "flavio2",
    "brancos2",
    "nulos2",
]
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]


def cap() -> Capitulo:
    return Capitulo(
        "anomalia", "10", "Grupos", "Os grupos de seções nos dois turnos", (), None
    )


def texto_publico(h: str) -> str:
    return re.sub(r"<[^>]+>", " ", h)


def _municipios(n: int) -> list[tuple[str, str]]:
    """(uf, mun_tse) reais do índice do Politize, para o mapa casar coordenada."""
    muns = B.municipios_politize()
    pares = sorted(k for k, v in muns.items() if v["lat"] is not None)
    return pares[:n] if pares else [("AC", f"{i:05d}") for i in range(n)]


def sintetico(tmp_path: Path, k: int = 4, pesado: bool = True) -> dict:
    rng = random.Random(20261026)
    n_total = 12000
    pesos = [0.4, 0.3, 0.2, 0.1][:k]
    pesos = [w / sum(pesos) for w in pesos]
    comps = []
    for i in range(k):
        secoes = round(n_total * pesos[i])
        lula2 = 30 + 10 * i
        flavio2 = 45 - 8 * i
        c = {
            "id": i,
            "secoes": secoes,
            "pct_secoes": 100 * secoes / n_total,
            "aptos": secoes * (300 - 40 * i),
            "aptos_medio": 300 - 40 * i,
            "peso": pesos[i],
            "centro_pct_eleitorado": {
                "lula1": lula2 - 4.0,
                "flavio1": flavio2 - 6.0,
                "outros1": 7.5,
                "brancos1": 1.2,
                "nulos1": 2.0,
                "lula2": float(lula2),
                "flavio2": float(flavio2),
                "brancos2": 1.0,
                "nulos2": 2.5,
            },
            "centro_delta_pp": {
                "comp": 1.3 - i,
                "lula": 4.0,
                "flavio": 6.0,
                "brancos": -0.2,
                "nulos": 0.5,
            },
            "terceira1_pp": 7.5,
            "comp1_pct": 78.0 - i,
            "comp2_pct": 79.3 - 2 * i,
            "abst1_pct": 22.0 + i,
            "abst2_pct": 20.7 + 2 * i,
            "fatia_f1": 100 * (flavio2 - 6) / (flavio2 - 6 + lula2 - 4),
            "fatia_f2": 100 * flavio2 / (flavio2 + lula2),
            "dispersao_logdet": -5.0 + i,
            "loglik_media": -4.5 - 0.7 * i,
            "loglik_p05": -7.0 - i,
            "mahalanobis_mediana": 2.0 + 0.3 * i,
            "ufs_top": [
                {
                    "uf": "SP",
                    "secoes": secoes // 3,
                    "pct_do_cluster": 33.3,
                    "pct_da_uf": 10.0 + i,
                },
                {
                    "uf": "BA",
                    "secoes": secoes // 4,
                    "pct_do_cluster": 25.0,
                    "pct_da_uf": 8.0,
                },
            ],
            "regioes": [
                {"regiao": "Sudeste", "secoes": secoes // 2, "pct_do_cluster": 50.0}
            ],
            "modelo_urna": [{"modelo": "UE2020", "pct_do_cluster": 60.0}],
            "sinais": {
                "escore_1_mais_pct": 30.0 + i,
                "escore_2_mais_pct": 3.0 + i,
                "papel_pct": 0.1,
                "contingencia_pct": 1.5,
                "mudanca_pct": 0.3,
            },
            "rotulo": f"rótulo sintético do grupo {i + 1}",
        }
        comps.append(c)
    bic = []
    for kk in range(2, 11):
        bic.append(
            {
                "k": kk,
                "bic": 5_000_000 - 120_000 * min(kk, 4) - 3_000 * max(kk - 4, 0),
                "icl": 5_020_000 - 110_000 * min(kk, 4) + 2_000 * max(kk - 4, 0),
                "loglik_media": -5.2 + 0.05 * kk,
                "iteracoes": 100 + kk,
                "convergiu": True,
            }
        )
    muns = _municipios(6)
    amostras = []
    for j in range(50):
        uf, mun = muns[j % len(muns)]
        amostras.append(
            {
                "uf": uf,
                "mun": mun,
                "municipio": f"Município {j}",
                "zona": 1 + j % 3,
                "secao": 100 + j,
                "aptos_1t": 200 + j,
                "aptos_2t": 201 + j,
                "comparecimento_1t": 150 + j,
                "comparecimento_2t": 160 + j,
                "lula_1t": 50,
                "flavio_1t": 70,
                "lula_2t": 60,
                "flavio_2t": 90,
                "brancos_1t": 2,
                "brancos_2t": 1,
                "nulos_1t": 3,
                "nulos_2t": 4,
                "modelo_urna": "UE2020",
                "escore": j % 3,
                "explicacao": "seção pequena" if j % 2 else "",
                "loglik": -20.0 - j,
                "link": f"politizese.html#uf={uf}&zona={1 + j % 3}&secao={100 + j}",
            }
        )
    pontos = []
    for _ in range(600):
        g = rng.choices(range(k), weights=pesos)[0]
        pontos.append(
            [
                rng.gauss(g - 1.5, 0.6),
                rng.gauss(0.5 * g, 0.5),
                g,
                0,
                rng.choice(["SP", "BA", "RS", "PA"]),
            ]
        )
    for _ in range(30):
        pontos.append([rng.gauss(3.5, 0.4), rng.gauss(2.5, 0.4), k - 1, 1, "AM"])
    A = {
        "gerado_em": "2026-10-26 20:00:00",
        "rotulo": B.ROTULO,
        "fonte": {"banco_1t": "a", "banco_2t": "b"},
        "universo": {
            "secoes": n_total,
            "excluidas": {
                "exterior": 1310,
                "sem_par": 12,
                "aptos_menor_30": 7,
                "outros": 0,
            },
            "comparecimento_divergente": 0,
        },
        "features": {
            "colunas": COLS,
            "unidade": "pct do eleitorado",
            "padronizacao": {
                c: {"media": 10.0 + i, "desvio": 3.0} for i, c in enumerate(COLS)
            },
            "equivalencia_afim": "Trocar níveis do 2º turno por diferenças é uma transformação afim invertível: mesma partição.",
        },
        "bic": bic,
        "k_escolhido": k,
        "k_joelho_bic": k,
        "k_min_icl": k,
        "regra": "k* é o menor k em que a queda seguinte do BIC fica abaixo de 5% da queda total; sem joelho, argmin do ICL.",
        "ajuste": {
            "covariancia": "full",
            "n_init": 1,
            "inits": ["kmeans", "k-means++"],
            "sementes": [
                {"semente": 20261026 + i, "init": "kmeans", "convergiu": True}
                for i in range(16)
            ],
            "random_state": 20261026,
            "init": "kmeans",
            "convergiu": True,
            "iteracoes": 212,
            "sementes_no_maximo": 11,
            "tol": 1e-6,
            "max_iter": 2000,
            "reg_covar": 1e-6,
            "loglik_media": -4.91,
            "segundos": 88.0,
            "diagnostico_convergencia": {"frase": "O EM convergiu nas 16 partidas."},
        },
        "kmeans": {
            "niveis": [
                {
                    "k": kk,
                    "inercia": 1e6 / kk,
                    "silhueta": 0.3 - 0.01 * kk,
                    "iteracoes": 40,
                    "convergiu": True,
                }
                for kk in range(2, 11)
            ],
            "niveis_e_deltas": [
                {
                    "k": kk,
                    "inercia": 1.1e6 / kk,
                    "silhueta": 0.28 - 0.01 * kk,
                    "iteracoes": 50,
                    "convergiu": True,
                }
                for kk in range(2, 11)
            ],
            "ari_com_mistura_k_estrela": {"niveis": 0.71, "niveis_e_deltas": 0.55},
        },
        "componentes": comps,
        "mais_anomalo": {
            "id": k - 1,
            "criterio": "soma dos postos de menor log-verossimilhança média e de maior dispersão",
            "segundo": {"id": k - 2, "diferenca_postos": 3},
            "voto": {
                "fatia_f2_vs_vizinhas_pp": 2.31,
                "ic95_fatia": [1.9, 2.7],
                "did_vs_1t_pp": -0.42,
                "ic95_did": [-0.95, 0.11],
                "n": 1180,
                "n_vizinhas": 9400,
                "n_municipios": 310,
                "bootstrap": 2000,
            },
            "amostras": amostras,
            "seis_sinais": [
                {
                    "sinal": "delta",
                    "descricao": "comparecimento +5 pp",
                    "secoes_no_grupo": 40,
                    "pct_grupo": 3.33,
                    "pct_pais": 1.1,
                    "razao": 3.03,
                }
            ],
        },
        "menos_provaveis": amostras[:10],
        "cluster_regiao": [
            {
                "cluster": i,
                "regiao": rg,
                "secoes": 100 + 10 * i,
                "pct_do_cluster": 100 / len(REGIOES),
                "pct_da_regiao": 5.0,
            }
            for i in range(k)
            for rg in REGIOES
        ],
        "cluster_uf": [
            {
                "cluster": i,
                "uf": "SP",
                "secoes": 10,
                "pct_do_cluster": 1.0,
                "pct_da_uf": 2.0,
            }
            for i in range(k)
        ],
        "cluster_modelo": [
            {"cluster": i, "modelo": m, "secoes": 10, "pct_do_cluster": 50.0}
            for i in range(k)
            for m in ("UE2020", "UE2022")
        ],
        "cramer_v_regiao": 0.41,
        "cramer_v_uf": 0.47,
        "cramer_v_modelo": 0.06,
        "cramer_v_tamanho": 0.12,
        "pais": {
            "secoes": n_total,
            "aptos_medio": 280.0,
            "centro_pct_eleitorado": {c: 10.0 + i for i, c in enumerate(COLS)},
        },
        "sinais_pais": {
            "escore_1_mais_pct": 31.0,
            "escore_2_mais_pct": 3.5,
            "papel_pct": 0.1,
            "contingencia_pct": 1.4,
            "mudanca_pct": 0.3,
        },
        "pca": {
            "colunas": ["x", "y", "cluster", "top", "uf"],
            "pontos": pontos,
            "variancia_explicada": [0.52, 0.21],
            "elipse_nivel": "2 desvios-padrão no plano",
            "elipses": [
                {
                    "cluster": k - 1,
                    "cx": 2.0,
                    "cy": 1.6,
                    "rx": 1.4,
                    "ry": 0.8,
                    "ang": 25.0,
                }
            ],
        },
    }
    if pesado:
        linhas = []
        for j in range(400):
            uf, mun = muns[j % len(muns)]
            grupo = j % k
            linhas.append(
                [
                    uf,
                    mun,
                    1 + j % 3,
                    100 + j,
                    grupo,
                    -4.0 - grupo,
                    0.5,
                    1 if grupo == k - 1 else 0,
                ]
            )
        corpo = json.dumps(
            {
                "colunas": [
                    "uf",
                    "mun",
                    "zona",
                    "secao",
                    "grupo",
                    "score",
                    "p",
                    "anomalo",
                ],
                "linhas": linhas,
            }
        ).encode()
        arq = tmp_path / "anomalia_secoes.json.gz"
        with arq.open("wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as gz:
            gz.write(corpo)
        dados = arq.read_bytes()
        A["secoes_arquivo"] = {
            "arquivo": str(arq),
            "sha256": hashlib.sha256(dados).hexdigest(),
            "bytes": len(dados),
            "n_linhas": len(linhas),
            "colunas": ["uf", "mun", "zona", "secao", "grupo", "score", "p", "anomalo"],
        }
    else:
        A["secoes_arquivo"] = {
            "arquivo": str(tmp_path / "nao_existe.json.gz"),
            "sha256": "",
            "n_linhas": 0,
        }
    return A


def dados_de(tmp_path: Path, A: dict) -> Dados:
    (tmp_path / "anomalia_ml.json").write_text(
        json.dumps(A, ensure_ascii=False), encoding="utf-8"
    )
    return Dados(pasta=tmp_path)


# ------------------------------------------------------------------ estrutura


def test_modulos_abaixo_de_mil_linhas():
    for nome in MODULOS:
        texto = (ROOT / "scripts/apuracao_2t_2026" / nome).read_text(encoding="utf-8")
        assert texto.count("\n") < 1000, nome


def test_capitulo_registrado_entre_secoes_e_logs():
    ids = [c[0] for c in V.CAPITULOS]
    i = ids.index("anomalia")
    assert ids[i - 1] == "secoes" and ids[i + 1] == "logs"
    assert V.CAPITULOS[i][1:] == (
        "Grupos",
        "Os grupos de seções nos dois turnos",
        ("anomalia_ml.json",),
    )


def test_cores_passam_aa():
    """Cor de grupo é preenchimento (3:1 contra o papel) e leva texto branco (4,5:1)."""
    for c in B.CORES:
        assert contraste(c, PAPER) >= 3.0, c
        assert contraste(c, "#ffffff") >= 4.5, c
    assert len(set(B.CORES)) == len(B.CORES) >= 10


def test_sem_dado_levanta_keyerror(tmp_path):
    with pytest.raises(KeyError):
        CA.render(Dados(pasta=tmp_path), cap())


# ------------------------------------------------------------------ sintético


@pytest.fixture(scope="module")
def sint(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("anomalia")
    A = sintetico(tmp)
    return A, CA.render(dados_de(tmp, A), cap())


def test_sintetico_renderiza_todas_as_figuras(sint):
    _, h = sint
    for fig in FIGURAS:
        assert f'id="fig-{fig}"' in h, fig
        i = h.index(f'id="fig-{fig}"')
        assert "pendente" not in h[max(0, i - 40) : i], fig
    assert h.count('viewBox="0 0 ') >= len(FIGURAS)
    assert "—" not in h
    pub = texto_publico(h).lower()
    for proibida in ("fraude", "gmm", "mahalanobis"):
        assert proibida not in pub, proibida
    assert B.ROTULO in h
    for selo in ("Verificado", "Inferência", "Achado contrário"):
        assert selo in h, selo


def test_sintetico_numeros_vem_do_json(sint):
    A, h = sint
    c = B.atipico(A)
    assert inteiro(c["secoes"]) in h
    assert inteiro(A["universo"]["secoes"]) in h
    assert f"k* = {A['k_escolhido']}" in h
    assert "+2,31 pp" in h and "−0,42 pp" in h
    assert "inclui o zero" in h
    assert h.count("politizese.html#uf=") >= 50
    assert A["regra"][:40] in h
    assert "O que a mistura não separa" in h
    assert "3,03×" in h and "não é tamanho de seção" in h
    assert "contra 31,00% no país" in h
    assert (
        h.index("an_bic")
        < h.index("an_kmeans")
        < h.index("an_grupos")
        < h.index("an_regiao")
    )
    assert (
        h.index("an_regiao")
        < h.index("an_pca")
        < h.index("an_voto")
        < h.index("an_mapa")
    )
    assert h.rfind("Limites do capítulo") > h.rfind("an_mapa")


def test_sintetico_barras_dos_grupos_sao_block(sint):
    _, h = sint
    assert ".an-barra>span{display:block" in h
    assert h.count('class="an-barra"') == 2 * 4


def test_sem_arquivo_pesado_so_o_mapa_fica_pendente(tmp_path):
    A = sintetico(tmp_path, pesado=False)
    h = CA.render(dados_de(tmp_path, A), cap())
    assert 'class="pendente" id="fig-an_mapa"' in h
    for fig in FIGURAS[:-1]:
        assert f'id="fig-{fig}"' in h and f'class="pendente" id="fig-{fig}"' not in h


def test_elipse_por_eixos_e_por_covariancia_coincidem():
    sxx, syy, sxy = FAB._cov_de({"rx": 2.0, "ry": 1.0, "ang": 0.0})
    assert (round(sxx, 6), round(syy, 6), round(sxy, 6)) == (1.0, 0.25, 0.0)
    assert FAB._cov_de({"cov": [[1.0, 0.1], [0.1, 0.5]]}) == (1.0, 0.5, 0.1)


def test_acessores_tolerantes():
    assert B.g({"a": None, "b": 2}, "a", "b") == 2
    assert B.medida_voto({"mais_anomalo": {"voto": {}}}, "fatia") == (None, None)
    assert B.contem_zero((-1.0, 0.5)) is True and B.contem_zero((0.2, 0.9)) is False
    assert B.ic_txt((-0.5, 0.25)) == "IC de 95%: −0,50 a +0,25 pp"


def test_textos_sem_travessao_nem_proibidas(sint):
    A, _ = sint
    for fn in (
        TA.lead,
        TA.como_ler,
        TA.abertura,
        TA.espaco,
        TA.escolha_k,
        TA.convergencia,
        TA.grupos,
        TA.atipico,
        TA.contrario,
    ):
        h = fn(A)
        assert "—" not in h, fn.__name__
        assert "fraude" not in h.lower(), fn.__name__
    assert all("—" not in i for i in TA.limites_itens(A))


# ------------------------------------------------------------------ real


@pytest.mark.skipif(
    not REAL.exists(), reason="anomalia_ml.json ainda não gerado pelo motor"
)
def test_real_renderiza_com_o_json_do_motor():
    d = Dados(pasta=DADOS)
    A = d.get("anomalia_ml.json")
    h = CA.render(d, cap())
    for fig in FIGURAS[:-1]:
        assert f'id="fig-{fig}"' in h, fig
        assert f'class="pendente" id="fig-{fig}"' not in h, fig
    assert 'id="fig-an_mapa"' in h
    assert "—" not in h
    assert "fraude" not in texto_publico(h).lower()
    assert B.ROTULO.split(";")[0] in h
    c = B.atipico(A)
    assert inteiro(c["secoes"]) in h
    assert 3 <= B.k_de(A) <= 10
    assert A["ajuste"]["convergiu"] is True
    assert abs(sum(x["pct_secoes"] for x in A["componentes"]) - 100) < 0.05
    assert h.count("politizese.html#uf=") >= len(B.amostras(A))
    assert FA.fig_bic(A) and FAB.fig_voto(A)
