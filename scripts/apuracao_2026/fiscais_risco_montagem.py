"""Monta as linhas por local e por município a partir das camadas lidas.

Regras de precedência e de ausência ficam todas aqui, num lugar só:

- ponto válido: o ponto do cadastro do TSE cai num setor do próprio município
  ou a até ``TOLERANCIA_MUN_KM`` de um setor dele; senão o ponto é tratado como
  inconsistente e nenhuma camada espacial usa a coordenada;
- positivo de qualquer fonte vence; zero só quando todas as fontes da camada
  cobrem o local e nenhuma acusa; sem cobertura, vazio;
- o exterior (UF ZZ) fica com tudo vazio.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import fiscais_risco as fr
from . import fiscais_risco_camadas as cam

RAIO_TI_KM = 2.0
RAIO_QUILOMBO_KM = 2.0
RAIO_GARIMPO_KM = 20.0
TOLERANCIA_MUN_KM = 5.0
TIPO_PRESO = "Preso provisório"

COLUNAS_LOCAIS = [
    "uf",
    "mun_tse",
    "zona",
    "local_nr",
    "local_id",
    "setor_cd",
    "rural_urbano",
    "rural_urbano_fonte",
    "setor_situacao",
    "setor_tipo_cd",
    "setor_tipo",
    "terra_indigena",
    "ti_nome",
    "ti_dist_km",
    "ti_fonte",
    "quilombo",
    "quilombo_nome",
    "quilombo_dist_km",
    "quilombo_fonte",
    "favela",
    "favela_nome",
    "favela_fonte",
    "prisional",
    "prisional_fonte",
    "fronteira",
    "cidade_gemea",
    "garimpo",
    "garimpo_fonte",
    # Colunas a mais, depois das do contrato.
    "setor_sit_cd",
    "ponto_municipio",
    "ponto_dist_municipio_km",
    "garimpo_dist_km",
]
COLUNAS_MUNICIPIOS = [
    "uf",
    "mun_tse",
    "ibge",
    "municipio",
    "homicidios_taxa_100mil",
    "homicidios_ano",
    "homicidios_fonte",
    "homicidios_quintil",
    "crime_organizado",
    "crime_organizado_fontes",
    "fronteira",
    "cidade_gemea",
    "garimpo",
    "sede_lat",
    "sede_lon",
    "sede_fonte",
    # Coluna a mais: número de homicídios que sustenta a taxa.
    "homicidios_n",
]

F_SETOR = "ibge_setores_2022_malha"
F_FUNAI = "funai_tis_poligonais"
F_LI = "ibge_localidades_indigenas_2022"
F_LQ = "ibge_localidades_quilombolas_2022"
F_FRONT = "ibge_faixa_fronteira_2024"
F_PLG = "anm_sigmine_lavra_garimpeira"
F_RES = "anm_sigmine_reservas_garimpeiras"
F_TAXA = "ipea_atlas_taxa_homicidios"
F_CONT = "ipea_atlas_homicidios"
F_SEDE = "ibge_localidades_2022"
F_FBSP = "fbsp_cartografias_amazonia_2025"
URL_FBSP = (
    "https://forumseguranca.org.br/wp-content/uploads/2025/11/"
    "cartografias-violencia-amazonia-2025.pdf"
)


@dataclass
class Entradas:
    """Caminhos das bases já baixadas; ``None`` quando a fonte falhou."""

    locais_db: Path
    apuracao_db: Path
    contexto_json: Path
    arquivos: dict[str, Path | None]
    positivos_fonte: Counter = field(default_factory=Counter)
    avaliados_fonte: Counter = field(default_factory=Counter)

    def tem(self, chave: str) -> bool:
        p = self.arquivos.get(chave)
        return p is not None and p.exists()


def _validar_pontos(
    ent: Entradas, locais: list[cam.Local], setores: dict[str, cam.Setor]
) -> dict[str, tuple[str, float | None]]:
    """Situação do ponto de cada local: confere, vizinho, inconsistente."""
    gpkg = ent.arquivos[F_SETOR]
    assert gpkg is not None
    duvidosos = [
        loc
        for loc in locais
        if loc.tem_ponto
        and (loc.id not in setores or setores[loc.id].cd_mun != loc.ibge)
    ]
    dist = cam.distancia_ao_municipio(gpkg, duvidosos, TOLERANCIA_MUN_KM)
    saida: dict[str, tuple[str, float | None]] = {}
    for loc in locais:
        if not loc.tem_ponto:
            continue
        if loc.id in setores and setores[loc.id].cd_mun == loc.ibge:
            saida[loc.id] = ("confere", 0.0)
            continue
        d = dist.get(loc.id)
        if d is not None and d <= TOLERANCIA_MUN_KM:
            saida[loc.id] = ("vizinho_ate_5km", d)
        else:
            saida[loc.id] = ("inconsistente", d)
    return saida


def camadas_locais(ent: Entradas, locais: list[cam.Local]) -> dict[str, Any]:
    """Calcula todas as camadas espaciais; devolve dicionários por local_id."""
    out: dict[str, Any] = {"rotulos": None, "setores": {}, "pontos": {}}
    if ent.tem(F_SETOR) and ent.tem("ibge_setores_2022_dicionario"):
        out["rotulos"] = cam.rotulos_setor(ent.arquivos["ibge_setores_2022_dicionario"])
        out["setores"] = cam.setores_dos_pontos(ent.arquivos[F_SETOR], locais)
        out["pontos"] = _validar_pontos(ent, locais, out["setores"])
    validos = [
        loc
        for loc in locais
        if loc.tem_ponto
        and (not out["pontos"] or out["pontos"][loc.id][0] != "inconsistente")
    ]
    out["validos"] = {loc.id for loc in validos}
    out["funai"] = {}
    if ent.tem(F_FUNAI):
        tis = [
            (p.get("terrai_nome"), g) for p, g in cam.ler_geojson(ent.arquivos[F_FUNAI])
        ]
        if len(tis) >= 10_000:
            raise ValueError("WFS da FUNAI no teto de maxFeatures: resposta truncada")
        out["n_tis"] = len(tis)
        out["funai"] = cam.vizinho_poligono(validos, tis, RAIO_TI_KM)
    out["li"] = {}
    if ent.tem(F_LI):
        linhas = cam.ler_csv_pontos(ent.arquivos[F_LI], "LAT", "LONG")
        pts = [(cam.nome_ti_localidade(r), r["_lat"], r["_lon"]) for r in linhas]
        out["li"] = cam.vizinho_ponto(validos, pts, RAIO_TI_KM)
    out["lq"] = {}
    if ent.tem(F_LQ):
        linhas = cam.ler_csv_pontos(ent.arquivos[F_LQ], "Lat_d", "Long_d")
        pts = [(cam.nome_quilombo(r), r["_lat"], r["_lon"]) for r in linhas]
        out["lq"] = cam.vizinho_ponto(validos, pts, RAIO_QUILOMBO_KM)
    out["garimpo"] = {}
    out["garimpo_mun"] = None
    if ent.tem(F_PLG) and ent.tem(F_RES):
        polis = [
            (f"permissão de lavra garimpeira {p.get('PROCESSO')}", g)
            for p, g in cam.ler_geojson(ent.arquivos[F_PLG])
        ]
        polis += [
            ("reserva garimpeira", g) for _, g in cam.ler_geojson(ent.arquivos[F_RES])
        ]
        out["garimpo"] = cam.vizinho_poligono(validos, polis, RAIO_GARIMPO_KM)
        out["n_poligonos_garimpo"] = len(polis)
        if ent.tem(F_SETOR):
            tocados = cam.municipios_tocados(
                ent.arquivos[F_SETOR], [g for _, g in polis]
            )
            out["garimpo_mun"] = set().union(*tocados.values()) if tocados else set()
    return out


def _rural(loc: cam.Local, setor: cam.Setor | None) -> tuple[str | None, str | None]:
    if setor is not None and setor.situacao.lower() in ("urbana", "rural"):
        return setor.situacao.lower(), "setor_censitario_2022"
    if fr.rural_por_cadastro(loc.endereco, loc.bairro):
        return "rural", "cadastro_local"
    return None, None


def linha_local(
    loc: cam.Local,
    lay: dict[str, Any],
    mun: dict[str, dict[str, Any]],
    ent: Entradas,
) -> dict[str, str]:
    """Uma linha do CSV por local, com vazio onde a base não cobre."""
    base = {
        "uf": loc.uf,
        "mun_tse": loc.mun_tse,
        "zona": str(loc.zona),
        "local_nr": str(loc.local_nr),
        "local_id": loc.id,
    }
    if loc.uf == "ZZ":
        return {c: base.get(c, "") for c in COLUNAS_LOCAIS}
    valido = loc.id in lay["validos"]
    setor = lay["setores"].get(loc.id) if valido else None
    rot = lay["rotulos"] or {"CD_SIT": {}, "CD_TIPO": {}}
    situacao_ponto = lay["pontos"].get(loc.id)
    r: dict[str, Any] = dict(base)

    r["rural_urbano"], r["rural_urbano_fonte"] = _rural(loc, setor)
    if setor is not None:
        r["setor_cd"] = setor.cd
        r["setor_sit_cd"] = setor.cd_sit
        r["setor_situacao"] = rot["CD_SIT"].get(setor.cd_sit)
        r["setor_tipo_cd"] = setor.cd_tipo
        r["setor_tipo"] = rot["CD_TIPO"].get(setor.cd_tipo)
    if situacao_ponto is not None:
        r["ponto_municipio"] = situacao_ponto[0]
        r["ponto_dist_municipio_km"] = fr.fmt_num(situacao_ponto[1])

    _indigena(loc, r, lay, setor, valido, ent)
    _quilombo(loc, r, lay, setor, valido, ent)
    _favela(r, setor, valido)
    _prisional(loc, r, setor)

    m = mun.get(loc.mun_tse, {})
    r["fronteira"] = m.get("fronteira")
    r["cidade_gemea"] = m.get("cidade_gemea")
    if ent.tem(F_PLG) and ent.tem(F_RES) and valido:
        achado = lay["garimpo"].get(loc.id)
        r["garimpo"] = achado is not None
        if achado is not None:
            r["garimpo_fonte"] = f"ANM SIGMINE, {achado[0]}"
            r["garimpo_dist_km"] = achado[1]
    return _formatar(r)


def _urbano(setor: cam.Setor | None) -> bool:
    return setor is not None and setor.situacao.lower() == "urbana"


def _marca(ent: Entradas, chave: str, positivo: bool) -> None:
    ent.avaliados_fonte[chave] += 1
    if positivo:
        ent.positivos_fonte[chave] += 1


def _indigena(loc, r, lay, setor, valido, ent) -> None:
    fontes: list[str] = []
    nome = dist = None
    if valido and ent.tem(F_FUNAI):
        ti = lay["funai"].get(loc.id)
        _marca(ent, F_FUNAI, ti is not None)
        if ti is not None:
            nome, dist = f"TI {ti[0]}", ti[1]
            fontes.append("funai_tis_poligonais")
    if setor is not None and setor.cd_tipo == "5":
        fontes.append("ibge_setor_tipo_5_agrupamento_indigena (proxy)")
    if valido and ent.tem(F_LI):
        li = lay["li"].get(loc.id)
        _marca(ent, F_LI, li is not None)
        if li is not None:
            fontes.append("ibge_localidades_indigenas_2022 (proxy)")
            if nome is None:
                nome, dist = li[0], li[1]
    palavra = fr.indigena_por_nome(loc.local, _urbano(setor))
    if palavra:
        fontes.append(f"nome_local (proxy: {palavra})")
    if fontes:
        r["terra_indigena"] = True
    elif valido and ent.tem(F_FUNAI) and ent.tem(F_LI) and setor is not None:
        r["terra_indigena"] = False
    r["ti_nome"], r["ti_dist_km"], r["ti_fonte"] = nome, dist, "; ".join(fontes)


def _quilombo(loc, r, lay, setor, valido, ent) -> None:
    fontes: list[str] = []
    nome = dist = None
    if setor is not None and setor.cd_tipo == "9":
        fontes.append("ibge_setor_tipo_9_agrupamento_quilombola (proxy)")
    if valido and ent.tem(F_LQ):
        lq = lay["lq"].get(loc.id)
        _marca(ent, F_LQ, lq is not None)
        if lq is not None:
            fontes.append("ibge_localidades_quilombolas_2022 (proxy)")
            nome, dist = lq[0], lq[1]
    palavra = fr.quilombola_por_nome(loc.local, _urbano(setor))
    if palavra:
        fontes.append(f"nome_local (proxy: {palavra})")
    if fontes:
        r["quilombo"] = True
    elif valido and ent.tem(F_LQ) and setor is not None:
        r["quilombo"] = False
    r["quilombo_nome"], r["quilombo_dist_km"] = nome, dist
    r["quilombo_fonte"] = "; ".join(fontes)


def _favela(r, setor, valido) -> None:
    if not valido or setor is None:
        return
    fcu = setor.cd_fcu not in ("", ".") or setor.cd_tipo == "1"
    r["favela"] = fcu
    if fcu:
        r["favela_nome"] = setor.nm_fcu or None
        r["favela_fonte"] = "ibge_setor_fcu_2022 (CD_FCU do setor)"


def _prisional(loc, r, setor) -> None:
    fontes = []
    if loc.tipo_local == TIPO_PRESO:
        fontes.append("tse_tipo_local (Preso provisório)")
    palavra = fr.prisional_por_nome(loc.local)
    if palavra:
        fontes.append(f"nome_local (inferido: {palavra})")
    if setor is not None and setor.cd_tipo == "6":
        fontes.append("ibge_setor_tipo_6_unidade_prisional")
    r["prisional"] = bool(fontes)
    r["prisional_fonte"] = "; ".join(fontes)


def _formatar(r: dict[str, Any]) -> dict[str, str]:
    saida = {}
    for c in COLUNAS_LOCAIS:
        v = r.get(c)
        if isinstance(v, bool):
            saida[c] = fr.fmt_flag(v)
        elif isinstance(v, float):
            saida[c] = fr.fmt_num(v)
        else:
            saida[c] = fr.fmt_txt(v)
    return saida


def municipios(
    ent: Entradas,
    locais: list[cam.Local],
    garimpo_mun: set[str] | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Atributos por município TSE e notas de cobertura e casamento."""
    notas: dict[str, Any] = {}
    nomes: dict[str, tuple[str, str]] = {}
    for loc in locais:
        nomes.setdefault(loc.mun_tse, (loc.uf, loc.municipio))
    tse_ibge = {loc.mun_tse: loc.ibge for loc in locais}

    front = cam.faixa_fronteira(ent.arquivos[F_FRONT]) if ent.tem(F_FRONT) else None
    sedes = cam.sedes_municipais(ent.arquivos[F_SEDE]) if ent.tem(F_SEDE) else {}
    ano, taxa, cont = None, {}, {}
    if ent.tem(F_TAXA) and ent.tem(F_CONT):
        ano, taxa, cont = cam.homicidios(ent.arquivos[F_TAXA], ent.arquivos[F_CONT])
    nome_para_tse = {(uf, fr.normalizar(n)): cd for cd, (uf, n) in nomes.items()}
    crime, sem_casar, so_uf = cam.contexto_crime(ent.contexto_json, nome_para_tse)
    fbsp, notas_fbsp = itens_fbsp(ent, nome_para_tse)
    for cd, itens in fbsp.items():
        crime.setdefault(cd, []).extend(itens)
    notas.update(
        homicidios_ano=ano,
        crime_sem_casamento=sem_casar,
        crime_so_uf=so_uf,
        ibge_sem_taxa=0,
        fbsp=notas_fbsp,
        fronteira_sem_municipio_tse=sorted(
            set(front or {}) - {ib for ib in tse_ibge.values() if ib}
        ),
    )

    taxa_tse: dict[str, float | None] = {}
    for cd, ib in tse_ibge.items():
        if nomes[cd][0] == "ZZ" or not ib:
            continue
        taxa_tse[cd] = taxa.get(ib[:6])
    quint = fr.quintis(taxa_tse)
    notas["ibge_sem_taxa"] = sum(1 for v in taxa_tse.values() if v is None)

    saida: dict[str, dict[str, Any]] = {}
    for cd, (uf, nome) in sorted(nomes.items(), key=lambda x: (x[1][0], x[0])):
        ib = tse_ibge.get(cd)
        m: dict[str, Any] = {"uf": uf, "mun_tse": cd, "ibge": ib, "municipio": nome}
        if uf != "ZZ" and ib:
            t = taxa_tse.get(cd)
            m["homicidios_taxa_100mil"] = t
            if t is not None:
                m["homicidios_ano"] = ano
                m["homicidios_fonte"] = (
                    "Ipea, Atlas da Violência, série 20 (SIM, CID-10 X85-Y09 e Y35, "
                    "óbitos por residência)"
                )
                m["homicidios_quintil"] = quint.get(cd)
                m["homicidios_n"] = cont.get(ib[:6])
            m["crime_organizado"], m["crime_organizado_fontes"] = fr.crime_organizado(
                crime.get(cd, [])
            )
            if front is not None:
                f = front.get(ib)
                m["fronteira"] = f is not None
                m["cidade_gemea"] = bool(f and f["cidade_gemea"])
            if garimpo_mun is not None:
                m["garimpo"] = ib in garimpo_mun
            if ib in sedes:
                lat, lon, cat = sedes[ib]
                m["sede_lat"], m["sede_lon"] = round(lat, 6), round(lon, 6)
                m["sede_fonte"] = f"IBGE, Localidades do Brasil 2022 ({cat})"
        saida[cd] = m
    return saida, notas


def itens_fbsp(
    ent: Entradas, nome_para_tse: dict[tuple[str, str], str]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Municípios citados pelo FBSP (Amazônia Legal) como itens de fonte.

    A leitura só vale se bater com os totais por UF do quadro 3.1; senão a
    fonte é recusada inteira, para não publicar mapeamento pela metade.
    """
    notas: dict[str, Any] = {"usada": False}
    if not ent.tem(F_FBSP):
        notas["motivo"] = "arquivo do FBSP ausente"
        return {}, notas
    por_uf, totais = cam.fbsp_municipios(cam.texto_pdf(ent.arquivos[F_FBSP]))
    lidos = {uf: len(v) for uf, v in por_uf.items()}
    notas.update(totais_quadro_3_1=totais, lidos=lidos)
    if lidos != totais or sum(totais.values()) != 344:
        notas["motivo"] = "leitura dos quadros não bate com o quadro 3.1"
        return {}, notas
    saida: dict[str, list[dict[str, Any]]] = defaultdict(list)
    aproximados, sem_casamento = [], []
    for uf, municipios_uf in sorted(por_uf.items()):
        for nome in municipios_uf:
            cd, metodo = fr.casar_municipio(uf, nome, nome_para_tse)
            if cd is None:
                sem_casamento.append(f"{nome}/{uf}")
                continue
            if metodo != "exato":
                aproximados.append(f"{nome}/{uf} -> {metodo}")
            saida[cd].append(
                {
                    "id": "fbsp-cartografias-amazonia-2025",
                    "tema": f"presença citada no quadro de {uf}",
                    "veiculo": "Fórum Brasileiro de Segurança Pública",
                    "data": "2025-11",
                    "url": URL_FBSP,
                }
            )
    notas.update(
        usada=True,
        municipios_casados=len(saida),
        casamentos_nao_exatos=aproximados,
        sem_casamento=sem_casamento,
    )
    return dict(saida), notas


def formatar_municipio(m: dict[str, Any]) -> dict[str, str]:
    saida = {}
    for c in COLUNAS_MUNICIPIOS:
        v = m.get(c)
        if isinstance(v, bool):
            saida[c] = fr.fmt_flag(v)
        elif c in ("sede_lat", "sede_lon") and v is not None:
            saida[c] = f"{v:.6f}"
        elif isinstance(v, float):
            saida[c] = fr.fmt_num(v, 2)
        else:
            saida[c] = fr.fmt_txt(v)
    return saida


def cobertura(linhas: list[dict[str, str]], muns: list[dict[str, str]]):
    """Locais com valor, positivos e municípios com valor, por camada."""
    camadas = {
        "rural_urbano": ("rural_urbano", "rural"),
        "terra_indigena": ("terra_indigena", "1"),
        "quilombo": ("quilombo", "1"),
        "favela_comunidade": ("favela", "1"),
        "unidade_prisional_ou_socioeducativa": ("prisional", "1"),
        "fronteira": ("fronteira", "1"),
        "cidade_gemea": ("cidade_gemea", "1"),
        "garimpo": ("garimpo", "1"),
    }
    saida: dict[str, dict[str, int]] = {}
    for nome, (col, pos) in camadas.items():
        com = [r for r in linhas if r[col] != ""]
        saida[nome] = {
            "locais_com_valor": len(com),
            "locais_positivos": sum(1 for r in com if r[col] == pos),
            "municipios_com_valor": len({(r["uf"], r["mun_tse"]) for r in com}),
        }
    muni = {
        "homicidios_municipio": "homicidios_taxa_100mil",
        "crime_organizado": "crime_organizado",
        "sede_municipal": "sede_lat",
    }
    for nome, col in muni.items():
        com = [m for m in muns if m[col] != ""]
        positivos = (
            sum(1 for m in com if m[col] == fr.COM_MAPEAMENTO)
            if nome == "crime_organizado"
            else (
                sum(1 for m in com if m.get("homicidios_quintil") == "5")
                if nome == "homicidios_municipio"
                else len(com)
            )
        )
        saida[nome] = {
            "locais_com_valor": None,
            "locais_positivos": None,
            "municipios_com_valor": len(com),
            "municipios_positivos": positivos,
        }
    return saida


def contagem_por(linhas: list[dict[str, str]], col: str) -> dict[str, int]:
    c: defaultdict[str, int] = defaultdict(int)
    for r in linhas:
        c[r[col] or "(vazio)"] += 1
    return dict(sorted(c.items(), key=lambda x: -x[1]))
