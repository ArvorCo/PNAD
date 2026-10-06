#!/usr/bin/env python3
"""Camada de risco e contexto do território por local de votação (capítulo 13).

Para cada local de votação do cadastro do TSE (``data/outputs/
locais_votacao_2026.sqlite``, só leitura) grava atributos com fonte pública e
data: setor censitário e situação rural ou urbana (Censo 2022), terra indígena
(FUNAI, com proxies do IBGE), quilombo (IBGE), favela e comunidade urbana,
unidade prisional, fronteira e cidade-gêmea, garimpo (ANM) e, por município,
taxa de homicídios (Ipea), mapeamento público de crime organizado e sede
municipal. Onde a base não cobre, o campo sai vazio, nunca zero.

Saídas:

- ``data/outputs/fiscais_risco_locais.csv.gz`` (uma linha por local);
- ``data/outputs/fiscais_risco_municipios.csv`` (uma linha por município);
- ``analysis/apuracao_2026/dados/fiscais_risco_fontes.json`` (proveniência,
  cobertura e limites).

Uso:

    python3 scripts/apuracao-2026-fiscais-risco.py            # baixa tudo
    python3 scripts/apuracao-2026-fiscais-risco.py --sem-download
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from apuracao_2026 import fiscais_risco_camadas as cam
from apuracao_2026 import fiscais_risco_fontes as fontes
from apuracao_2026 import fiscais_risco_montagem as mont

ROOT = Path(__file__).resolve().parents[1]
LOCAIS_DB = ROOT / "data/outputs/locais_votacao_2026.sqlite"
APURACAO_DB = ROOT / "apuracao/data/apuracao.sqlite"
CONTEXTO = ROOT / "analysis/apuracao_2026/dados/contexto_seguranca.json"
SAIDA_LOCAIS = ROOT / "data/outputs/fiscais_risco_locais.csv.gz"
SAIDA_MUNICIPIOS = ROOT / "data/outputs/fiscais_risco_municipios.csv"
SAIDA_FONTES = ROOT / "analysis/apuracao_2026/dados/fiscais_risco_fontes.json"
DADOS_EXT = re.compile(r'href="([^"]+\.(?:csv|xlsx?|ods|geojson|json|zip|shp|kml))"')


def sondar(url: str) -> tuple[int | None, str]:
    """Status HTTP e corpo (até 2 MB) de uma página, sem levantar exceção."""
    req = urllib.request.Request(url, headers={"User-Agent": "arvor-pnad/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read(2_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except (urllib.error.URLError, OSError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def sondar_incra(f: fontes.Fonte) -> None:
    status, corpo = sondar(f.url)
    indice, _ = sondar("https://certificacao.incra.gov.br/csv_shp/")
    login = "sso.acesso.gov.br" in corpo
    f.status = "falhou"
    f.baixado_em = fontes.agora_utc()
    f.motivo = (
        f"a exportação de shapefile da certificação do INCRA ({f.url}) devolveu "
        f"HTTP {status}"
        + (" com a tela de login gov.br (sso.acesso.gov.br)" if login else "")
        + f"; o índice csv_shp devolveu HTTP {indice}; o serviço OGC do acervo "
        "fundiário (acervofundiario.incra.gov.br/i3geo) não listou camada de "
        "quilombolas; sem polígono oficial de território quilombola, a camada usa "
        "o proxy declarado do IBGE"
    )


def sondar_geni(f: fontes.Fonte) -> None:
    status, corpo = sondar(f.url)
    mapa, _ = sondar("https://fogocruzado.org.br/mapadosgruposarmados/")
    arquivos = sorted(set(DADOS_EXT.findall(corpo)))
    f.status = "falhou"
    f.baixado_em = fontes.agora_utc()
    f.motivo = (
        f"a página do GENI/UFF devolveu HTTP {status} e traz relatório em PDF e "
        f"link para mapa interativo (fogocruzado.org.br, HTTP {mapa}); arquivos de "
        f"dados encontrados na página: {len(arquivos)}"
        + (f" ({', '.join(arquivos)})" if arquivos else "")
        + "; sem base de dados com licença declarada, a fonte não é usada"
    )


def preparar_fontes(sem_download: bool) -> list[fontes.Fonte]:
    lista = fontes.registro()
    for f in lista:
        if f.chave == "incra_areas_quilombolas":
            sondar_incra(f)
        elif f.chave == "geni_uff_grupos_armados":
            sondar_geni(f)
        else:
            fontes.baixar(f, sem_download=sem_download)
        print(f"  {f.chave}: {f.status} {f.bytes or ''} {f.motivo or ''}".rstrip())
    return lista


def escrever_csv(caminho: Path, colunas: list[str], linhas: list[dict[str, str]]):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    abrir = gzip.open if caminho.suffix == ".gz" else open
    with abrir(caminho, "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colunas, lineterminator="\n")
        w.writeheader()
        w.writerows(linhas)


def coberturas_por_fonte(
    lista: list[fontes.Fonte],
    ent: mont.Entradas,
    linhas: list[dict[str, str]],
    muns: list[dict[str, str]],
) -> None:
    """Preenche ``cobertura_locais`` e ``cobertura_municipios`` de cada fonte."""
    br = [r for r in linhas if r["uf"] != "ZZ"]
    muns_br = [m for m in muns if m["uf"] != "ZZ"]

    def n_mun(rows: list[dict[str, str]]) -> int:
        return len({(r["uf"], r["mun_tse"]) for r in rows})

    com_setor = [r for r in br if r["setor_cd"]]
    por_chave = {
        mont.F_SETOR: com_setor,
        "ibge_setores_2022_dicionario": com_setor,
        mont.F_FUNAI: [r for r in br if r["terra_indigena"] != ""],
        mont.F_LI: [r for r in br if r["terra_indigena"] != ""],
        mont.F_LQ: [r for r in br if r["quilombo"] != ""],
        mont.F_PLG: [r for r in br if r["garimpo"] != ""],
        mont.F_RES: [r for r in br if r["garimpo"] != ""],
        mont.F_FRONT: [r for r in br if r["fronteira"] != ""],
    }
    for f in lista:
        if f.status != "ok":
            continue
        if f.chave in por_chave:
            rows = por_chave[f.chave]
            f.cobertura_locais = len(rows)
            f.cobertura_municipios = n_mun(rows)
            if f.chave in ent.positivos_fonte:
                f.cobertura_locais = ent.avaliados_fonte[f.chave]
        elif f.chave.startswith("ipea_"):
            f.cobertura_municipios = sum(
                1 for m in muns_br if m["homicidios_taxa_100mil"]
            )
        elif f.chave == mont.F_SEDE:
            f.cobertura_municipios = sum(1 for m in muns_br if m["sede_lat"])
        elif f.chave == mont.F_FBSP:
            f.cobertura_municipios = sum(
                1
                for m in muns_br
                if "fbsp-cartografias" in m["crime_organizado_fontes"]
            )


def limites(
    notas: dict[str, Any],
    linhas: list[dict[str, str]],
    lay: dict[str, Any],
) -> list[str]:
    br = [r for r in linhas if r["uf"] != "ZZ"]
    pontos = Counter(r["ponto_municipio"] or "sem_coordenada" for r in br)
    fbsp = notas.get("fbsp", {})
    rural_cad = sum(1 for r in br if r["rural_urbano_fonte"] == "cadastro_local")
    return [
        "Toda camada espacial usa a coordenada do cadastro do TSE. Ponto que cai "
        "em setor de outro município e fica a mais de 5 km de qualquer setor do "
        f"próprio município é tratado como inconsistente ({pontos['inconsistente']} "
        "locais) e nenhuma camada espacial o usa; "
        f"{pontos['vizinho_ate_5km']} locais caem em setor vizinho a até 5 km e "
        f"usam o setor que contém o ponto; {pontos['sem_coordenada']} locais do "
        "Brasil não têm coordenada no cadastro.",
        "Rural ou urbano vem do setor censitário do Censo 2022 que contém o ponto. "
        "Sem setor, o cadastro do local só marca rural quando o endereço ou o "
        f"bairro trazem palavra rural declarada ({rural_cad} locais); nunca marca "
        "urbana, e sem palavra o campo fica vazio.",
        "Terra indígena: polígonos da FUNAI (dentro ou até 2 km). Setor do tipo "
        "agrupamento indígena, localidade indígena do IBGE até 2 km e palavra no "
        "nome do local (ALDEIA, INDIGENA, TERRA INDIG) entram como proxy declarado "
        "em ti_fonte; um local positivo só pelo nome é inferência, não medição. "
        "LCPI (concentração de pessoas indígenas fora de terra indígena) não marca "
        "o campo.",
        "Quilombo: o INCRA exige login gov.br para exportar os polígonos e o "
        "acervo fundiário não devolveu a camada; o campo usa o proxy do IBGE "
        "(localidade quilombola do Censo 2022 até 2 km, setor de agrupamento "
        "quilombola) e a palavra QUILOMBO no nome do local. Localidade é ponto, "
        "não território: o raio de 2 km pode alcançar escola urbana vizinha.",
        "Favela e comunidade urbana: setor com código de favela e comunidade urbana "
        "(CD_FCU) na malha do Censo 2022. Local na borda de uma comunidade pode "
        "cair em setor vizinho sem o código.",
        "Prisional: tipo oficial do TSE (Preso provisório), palavra no nome do "
        "local e setor do tipo unidade prisional; a palavra no nome é inferência "
        "declarada em prisional_fonte.",
        "Garimpo: só a ANM, permissões de lavra garimpeira ativas (fase LAVRA "
        "GARIMPEIRA) e reservas garimpeiras. Garimpo sem título, que é justamente o "
        "ilegal, não aparece nessa base; zero quer dizer nenhum título da ANM a até "
        "20 km, não ausência de garimpo.",
        f"Homicídios: Ipea, série 20, ano {notas.get('homicidios_ano')}. O Ipea só "
        "publica município com ao menos um homicídio registrado no ano; "
        f"{notas.get('ibge_sem_taxa')} municípios ficam vazios e não viram zero, "
        "porque o arquivo não diz que o valor é zero. Município pequeno com um ou "
        "dois óbitos tem taxa alta por construção; homicidios_n traz o número de "
        "óbitos que sustenta a taxa.",
        "Crime organizado: só mapeamento público citado. O FBSP (Cartografias da "
        "Violência na Amazônia, 2025) cobre só a Amazônia Legal; fora dela, o "
        "valor 'sem mapeamento público' quer dizer ausência de mapeamento público, "
        "não ausência de crime. Nenhum grupo é nomeado. Itens de imprensa de "
        "contexto_seguranca.json entram com o tema ao lado (faccao_milicia, "
        "coercao, violencia); coerção eleitoral e violência pontual não são, por "
        "si, crime organizado.",
        "Itens de imprensa que citam só a UF, sem município, não são atribuídos a "
        f"município nenhum ({', '.join(notas.get('crime_so_uf', [])) or 'nenhum'}).",
        "Casamentos de nome do FBSP que não foram exatos (grafia do relatório "
        "diferente do cadastro do TSE): "
        + ("; ".join(fbsp.get("casamentos_nao_exatos", [])) or "nenhum")
        + ". Sem casamento: "
        + (", ".join(fbsp.get("sem_casamento", [])) or "nenhum")
        + ".",
        "Fronteira e cidade-gêmea valem para o município inteiro (lista do IBGE de "
        "2024), não para a distância do local à linha de fronteira.",
        "Sede municipal: ponto da localidade do IBGE de 2022 (categoria cidade); "
        "o acesso por estrada fica para o capítulo, não para esta camada.",
        f"Polígonos de garimpo lidos: {lay.get('n_poligonos_garimpo')}.",
        "O exterior (UF ZZ) fica com todos os campos vazios.",
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--sem-download",
        action="store_true",
        help="reaproveita os arquivos já baixados em data/raw/",
    )
    args = ap.parse_args()

    print("Fontes:")
    lista = preparar_fontes(args.sem_download)
    lista += [
        fontes.fonte_local(
            "tse_locais_votacao_2026",
            "todas",
            "Cadastro de locais de votação e seções do TSE, 2026 (tabela secao)",
            LOCAIS_DB,
            "chave do local (UF, município TSE, zona, número do local), nome, "
            "tipo, endereço, bairro e coordenada",
        ),
        fontes.fonte_local(
            "apuracao_municipio",
            "todas",
            "Tabela municipio do banco da apuração (código TSE para IBGE)",
            APURACAO_DB,
            "junção do código TSE do município com o código IBGE",
            em_gravacao=True,
        ),
        fontes.fonte_local(
            "contexto_seguranca",
            "crime_organizado",
            "Itens de imprensa arquivados sobre segurança na eleição",
            CONTEXTO,
            "itens com tema faccao_milicia, coercao ou violencia e município "
            "citado; casamento do nome pelo cadastro do TSE",
        ),
    ]
    arquivos = {f.chave: (f.caminho if f.status == "ok" else None) for f in lista}
    ent = mont.Entradas(LOCAIS_DB, APURACAO_DB, CONTEXTO, arquivos)

    tse_ibge = cam.mapa_tse_ibge(APURACAO_DB)
    locais = cam.carregar_locais(LOCAIS_DB, tse_ibge)
    print(f"Locais: {len(locais)}; com coordenada: {sum(x.tem_ponto for x in locais)}")
    lay = mont.camadas_locais(ent, locais)
    muns_raw, notas = mont.municipios(ent, locais, lay.get("garimpo_mun"))
    muns = [mont.formatar_municipio(m) for m in muns_raw.values()]
    linhas = [mont.linha_local(loc, lay, muns_raw, ent) for loc in locais]

    escrever_csv(SAIDA_LOCAIS, mont.COLUNAS_LOCAIS, linhas)
    escrever_csv(SAIDA_MUNICIPIOS, mont.COLUNAS_MUNICIPIOS, muns)
    coberturas_por_fonte(lista, ent, linhas, muns)

    saida = {
        "gerado_em": fontes.agora_utc(),
        "saidas": {
            "locais": str(SAIDA_LOCAIS.relative_to(ROOT)),
            "municipios": str(SAIDA_MUNICIPIOS.relative_to(ROOT)),
            "linhas_locais": len(linhas),
            "linhas_municipios": len(muns),
        },
        "fontes": [f.para_json() for f in lista],
        "cobertura": mont.cobertura(linhas, muns),
        "distribuicoes": {
            "rural_urbano_fonte": mont.contagem_por(linhas, "rural_urbano_fonte"),
            "ponto_municipio": mont.contagem_por(linhas, "ponto_municipio"),
            "setor_tipo": mont.contagem_por(linhas, "setor_tipo"),
            "homicidios_quintil": mont.contagem_por(muns, "homicidios_quintil"),
            "crime_organizado": mont.contagem_por(muns, "crime_organizado"),
        },
        "notas": notas,
        "limites": limites(notas, linhas, lay),
    }
    texto = json.dumps(saida, ensure_ascii=False, indent=1)
    if "—" in texto:
        raise SystemExit("travessão no JSON de fontes; reescreva o texto")
    SAIDA_FONTES.parent.mkdir(parents=True, exist_ok=True)
    SAIDA_FONTES.write_text(texto + "\n", encoding="utf-8")
    print(f"Gravado: {SAIDA_LOCAIS}, {SAIDA_MUNICIPIOS}, {SAIDA_FONTES}")
    print(json.dumps(saida["cobertura"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
