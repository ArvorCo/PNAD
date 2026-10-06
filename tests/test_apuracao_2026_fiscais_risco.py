"""Camada de risco por local (capítulo 13): funções puras, sem rede e sem bancos."""

import struct
from pathlib import Path

import numpy as np
import pytest
import shapely
from apuracao_2026 import fiscais_risco as fr
from apuracao_2026 import fiscais_risco_camadas as cam
from apuracao_2026 import fiscais_risco_montagem as mont
from shapely.geometry import Point, box


def _blob(geom, *, little=True, envelope=1, srs=4674):
    """Monta um blob GeoPackageBinary com o envelope pedido."""
    ordem = "<" if little else ">"
    flags = (1 if little else 0) | (envelope << 1)
    x0, y0, x1, y1 = geom.bounds
    tamanhos = {0: (), 1: (x0, x1, y0, y1), 2: (x0, x1, y0, y1, 0.0, 0.0)}
    env = struct.pack(f"{ordem}{len(tamanhos[envelope])}d", *tamanhos[envelope])
    cab = b"GP" + bytes([0, flags]) + struct.pack(f"{ordem}i", srs)
    return cab + env + shapely.to_wkb(geom)


# ------------------------------------------------------------- GeoPackage


@pytest.mark.parametrize(("little", "envelope"), [(True, 1), (False, 1), (True, 0)])
def test_blob_gpkg_decodifica_srs_e_geometria(little, envelope):
    poligono = box(-50.0, -10.0, -49.99, -9.99)
    srs, wkb = fr.gpkg_para_wkb(_blob(poligono, little=little, envelope=envelope))
    assert srs == 4674
    assert shapely.from_wkb(wkb).equals(poligono)


def test_blob_gpkg_envelope_xyz_de_48_bytes():
    ponto = Point(-47.9, -15.8)
    assert fr.gpkg_para_geom(_blob(ponto, envelope=2)).equals(ponto)


def test_blob_sem_assinatura_gp_falha():
    with pytest.raises(ValueError, match="assinatura"):
        fr.gpkg_para_wkb(b"XX\x00\x01" + b"\x00" * 20)


# --------------------------------------------------------- ponto e distância


def test_ponto_dentro_do_poligono_tem_distancia_zero():
    quadrado = box(-50.0, -10.0, -49.98, -9.98)
    assert fr.distancia_km(-9.99, -49.99, quadrado) == 0.0


def test_distancia_em_km_pela_projecao_local():
    quadrado = box(-50.0, -10.0, -49.98, -9.98)
    # 1 km a leste da borda direita, na latitude do centro.
    dlon = 1.0 / (fr.RAIO_TERRA_M / 1000 * np.cos(np.radians(-9.99)) * np.pi / 180)
    d = fr.distancia_km(-9.99, -49.98 + dlon, quadrado)
    assert d == pytest.approx(1.0, abs=0.02)


def test_mais_proximo_respeita_o_raio_de_2_km():
    perto = box(-50.0, -10.0, -49.99, -9.99)
    longe = box(-49.9, -10.0, -49.89, -9.99)
    cands = [("perto", perto), ("longe", longe)]
    assert fr.mais_proximo(-9.995, -49.985, cands, 2.0)[0] == "perto"
    assert fr.mais_proximo(-9.995, -49.95, cands, 2.0) is None


def test_pares_no_raio_pre_filtra_sem_perder_o_vizinho():
    geoms = [box(-50.0, -10.0, -49.99, -9.99), box(-40.0, -5.0, -39.99, -4.99)]
    pares = fr.pares_no_raio(np.array([-9.995]), np.array([-49.98]), geoms, 2.0)
    assert pares == {0: [0]}


def test_haversine_um_grau_de_latitude():
    assert fr.haversine_km(0.0, 0.0, 1.0, 0.0) == pytest.approx(111.19, abs=0.05)


# ------------------------------------------------------------------ quintil


def test_quintil_nacional_cinco_e_a_maior_taxa():
    valores = {i: float(i) for i in range(1, 11)}
    q = fr.quintis(valores)
    assert [q[i] for i in range(1, 11)] == [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]


def test_quintil_de_municipio_sem_dado_fica_nulo():
    q = fr.quintis({"a": 10.0, "b": None, "c": 30.0})
    assert q["b"] is None
    assert fr.quintis({"a": None}) == {"a": None}


# ------------------------------------------------- inferência por cadastro


def test_fallback_rural_pelo_endereco_e_bairro():
    assert fr.rural_por_cadastro("POVOADO VAU - ZONA RURAL", "") == "POVOADO"
    assert fr.rural_por_cadastro("RUA DAS FLORES, 10", "Sítio Novo") == "SITIO"
    assert fr.rural_por_cadastro("RUA DAS FLORES, 10", "CENTRO") is None


def test_prisional_por_nome_evita_nome_de_pessoa():
    assert fr.prisional_por_nome("ESCOLA MUNICIPAL FERNANDO PRESÍDIO") is None
    assert fr.prisional_por_nome("EMEF CUSTÓDIA DIAS DE CAMPOS") is None
    assert fr.prisional_por_nome("FUNDAÇÃO CASA DA JUVENTUDE") is None
    assert fr.prisional_por_nome("PRESÍDIO REGIONAL DE LAGES") == "PRESIDIO"
    assert fr.prisional_por_nome("NÚCLEO PRISIONAL DA POLÍCIA PENAL")
    assert fr.prisional_por_nome("CENTRO SOCIOEDUCATIVO DE UNAÍ")


def test_aldeia_e_quilombo_no_nome_so_fora_da_cidade():
    assert fr.indigena_por_nome("ESCOLA ALDEIA DOS CURUMINS", urbano=True) is None
    assert fr.indigena_por_nome("ESCOLA ALDEIA PAY GAP", urbano=False) == "ALDEIA"
    assert fr.indigena_por_nome("E. M. INDÍGENA KANAMARIS", urbano=True)
    assert fr.quilombola_por_nome("EM QUILOMBO DOS PALMARES", urbano=True) is None
    assert fr.quilombola_por_nome("ASSOCIAÇÃO QUILOMBOLA X", urbano=True)


def test_decimal_aceita_virgula_do_ibge():
    assert fr.decimal("-15,86") == pytest.approx(-15.86)
    assert fr.decimal("-15.86") == pytest.approx(-15.86)
    assert fr.decimal("") is None


# ------------------------------------------------------- crime organizado


def test_crime_organizado_sem_fonte_e_sem_mapeamento_publico():
    assert fr.crime_organizado([]) == ("sem mapeamento público", "")
    sem_url = [{"id": "ctx-1", "tema": "coercao"}]
    assert fr.crime_organizado(sem_url) == ("sem mapeamento público", "")


def test_crime_organizado_cita_so_a_fonte():
    item = {
        "id": "ctx-033",
        "tema": "faccao_milicia",
        "veiculo": "Gazeta do Povo",
        "data": "2026-09-24",
        "url": "https://exemplo.org/materia",
    }
    valor, fontes = fr.crime_organizado([item])
    assert valor == "mapeamento público"
    assert fontes == (
        "ctx-033 (faccao_milicia), Gazeta do Povo, 2026-09-24, "
        "https://exemplo.org/materia"
    )


def test_casamento_de_municipio_fica_na_propria_uf():
    indice = {
        ("MA", "GOVERNADOR NEWTON BELLO"): "07641",
        ("MT", "SAPEZAL"): "90727",
        ("PI", "COIVARAS"): "10189",
    }
    assert fr.casar_municipio("MA", "Gov. Newton Bello", indice)[0] == "07641"
    cd, metodo = fr.casar_municipio("MT", "Sepezal", indice)
    assert cd == "90727"
    assert metodo.startswith("aproximado")
    assert fr.casar_municipio("MA", "Sapezal", indice) == (None, "sem_casamento")


def test_leitor_do_fbsp_guarda_so_o_municipio():
    texto = "\n".join(
        [
            "     Acre                 22 municípios (100%)       17 municípios",
            "  Presença de facções em municípios no Estado do Acre",
            "   Estado     Município     Facções     Situação     Classificação",
            "   Acre    Rio Branco    GRUPO A - GRUPO B    Presença de duas ou mais"
            " facções    Urbano",
            "                           Lagoa Grande do",
            "   Acre                                      GRUPO C      Presença de"
            " uma facção     Rural",
            "                               Acre",
            "                                         GRUPO D - GRUPO",
            "   Acre        Xapuri                                     Presença de"
            " duas ou mais facções   Intermediário",
            "                                              E",
            "  Fonte: Fórum Brasileiro de Segurança Pública, 2025.",
        ]
    )
    por_uf, totais = cam.fbsp_municipios(texto)
    assert totais == {"AC": 22}
    assert por_uf == {"AC": ["Rio Branco", "Lagoa Grande do Acre", "Xapuri"]}
    assert "GRUPO" not in repr(por_uf)


# ------------------------------------------------ nulo nunca vira zero


def _local(**kw):
    base = {
        "uf": "MA",
        "mun_tse": "07307",
        "municipio": "CAJARI",
        "zona": 20,
        "local_nr": 1104,
        "local": "U.E. FULANO DE TAL",
        "tipo_local": "Convencional",
        "endereco": "RUA X, S/N",
        "bairro": "CENTRO",
        "lat": None,
        "lon": None,
        "eleitores": 300,
        "ibge": "2102408",
    }
    base.update(kw)
    return cam.Local(**base)


def _camadas(**kw):
    lay = {
        "rotulos": None,
        "setores": {},
        "pontos": {},
        "validos": set(),
        "funai": {},
        "li": {},
        "lq": {},
        "garimpo": {},
    }
    lay.update(kw)
    return lay


def _entradas(tmp_path: Path, disponiveis: tuple[str, ...] = ()):
    arquivos = {}
    for chave in disponiveis:
        p = tmp_path / chave
        p.write_text("x", encoding="utf-8")
        arquivos[chave] = p
    return mont.Entradas(tmp_path / "a", tmp_path / "b", tmp_path / "c", arquivos)


def test_local_sem_coordenada_fica_vazio_e_nao_zero(tmp_path):
    loc = _local()
    linha = mont.linha_local(loc, _camadas(), {}, _entradas(tmp_path))
    assert loc.id == "MA-07307-20-1104"
    for campo in ("rural_urbano", "terra_indigena", "quilombo", "favela", "garimpo"):
        assert linha[campo] == "", campo
    assert linha["fronteira"] == ""
    assert linha["prisional"] == "0"


def test_fallback_do_cadastro_declara_a_fonte(tmp_path):
    loc = _local(endereco="POVOADO SANTA RITA", bairro="ZONA RURAL")
    linha = mont.linha_local(loc, _camadas(), {}, _entradas(tmp_path))
    assert linha["rural_urbano"] == "rural"
    assert linha["rural_urbano_fonte"] == "cadastro_local"


def test_local_coberto_sem_achado_vira_zero(tmp_path):
    loc = _local(lat=-3.3, lon=-45.0)
    setor = cam.Setor("210240805000001", "Rural", "8", "0", "2102408", ".", "")
    lay = _camadas(
        rotulos={"CD_SIT": {"8": "Área rural"}, "CD_TIPO": {"0": "Não especial"}},
        setores={loc.id: setor},
        pontos={loc.id: ("confere", 0.0)},
        validos={loc.id},
    )
    ent = _entradas(
        tmp_path,
        (mont.F_FUNAI, mont.F_LI, mont.F_LQ, mont.F_PLG, mont.F_RES),
    )
    muns = {"07307": {"fronteira": False, "cidade_gemea": False}}
    linha = mont.linha_local(loc, lay, muns, ent)
    assert linha["rural_urbano"] == "rural"
    assert linha["setor_situacao"] == "Área rural"
    assert linha["terra_indigena"] == "0"
    assert linha["quilombo"] == "0"
    assert linha["favela"] == "0"
    assert linha["garimpo"] == "0"
    assert linha["fronteira"] == "0"


def test_exterior_fica_com_tudo_vazio(tmp_path):
    loc = _local(uf="ZZ", mun_tse="29173", local="PRESÍDIO REGIONAL", ibge=None)
    linha = mont.linha_local(loc, _camadas(), {}, _entradas(tmp_path))
    preenchidos = {k for k, v in linha.items() if v}
    assert preenchidos == {"uf", "mun_tse", "zona", "local_nr", "local_id"}


def test_formatacao_nunca_transforma_nulo_em_zero():
    assert fr.fmt_flag(None) == ""
    assert fr.fmt_flag(False) == "0"
    assert fr.fmt_num(None) == ""
    assert fr.local_id("ma", "7307", 20, None, secao=45) == "MA-07307-20-s45"
