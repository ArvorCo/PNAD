#!/usr/bin/env python3
"""Coleta as series de intencao de voto para senador (1o turno) do painel do G1.

Para cada UF e instituto: baixa a pagina do painel e a API de graficos de cada
pergunta (estimulada, espontanea, votos validos), guarda o bruto com SHA-256 e
grava um JSON por onda em analysis/senado_2026/pesquisas/ no esquema da secao 1
de analysis/senado_2026/CONTRATO.md.

Uso:
    python3 scripts/senado-2026-g1.py                 # todas as UFs, com rede
    python3 scripts/senado-2026-g1.py --uf SP BA      # so algumas UFs
    python3 scripts/senado-2026-g1.py --skip-download # reprocessa o que ja esta salvo
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data/originals/senado_102026/g1"
OUT_DIR = ROOT / "analysis/senado_2026/pesquisas"
COBERTURA = ROOT / "analysis/senado_2026/cobertura_g1.json"

HOST = "https://especiaisg1.globo"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
CORTE_CAMPO = "2026-09-28"
ANO = 2026

UFS = {
    "AC": "acre",
    "AL": "alagoas",
    "AP": "amapa",
    "AM": "amazonas",
    "BA": "bahia",
    "CE": "ceara",
    "DF": "distrito-federal",
    "ES": "espirito-santo",
    "GO": "goias",
    "MA": "maranhao",
    "MT": "mato-grosso",
    "MS": "mato-grosso-do-sul",
    "MG": "minas-gerais",
    "PA": "para",
    "PB": "paraiba",
    "PR": "parana",
    "PE": "pernambuco",
    "PI": "piaui",
    "RJ": "rio-de-janeiro",
    "RN": "rio-grande-do-norte",
    "RS": "rio-grande-do-sul",
    "RO": "rondonia",
    "RR": "roraima",
    "SC": "santa-catarina",
    "SP": "sao-paulo",
    "SE": "sergipe",
    "TO": "tocantins",
}

MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}
NUMEROS_POR_EXTENSO = {"um": 1, "dois": 2, "tres": 3, "quatro": 4, "cinco": 5}
SLUGS_INSTITUTO = {
    "paranapesquisas": "parana",
    "atlasintel": "atlas",
    "realtimebigdata": "realtime",
    "realtime": "realtime",
}
TIPOS = {
    "ESTIMULADA": "estimulada",
    "ESPONTANEA": "espontanea",
    "VTSVALIDOS": "validos",
}
CODIGO_RE = re.compile(r"\b(ESPONTANEA|ESTIMULADA|VTSVALIDOS)-SEN-(\d+)\b")


# ---------------------------------------------------------------- utilitarios


def sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in base if not unicodedata.combining(c))


def slug_instituto(nome: str) -> str:
    """Slug em minusculas, sem acento, no formato do contrato."""
    chave = re.sub(r"[^a-z0-9]", "", sem_acento(nome).lower())
    return SLUGS_INSTITUTO.get(chave, chave)


def sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def agora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(caminho: Path) -> str:
    return str(caminho.relative_to(ROOT))


# -------------------------------------------------------------------- rede


def baixar(url: str, tentativas: int = 3) -> tuple[int, bytes]:
    """GET com User-Agent de navegador. Devolve (status, corpo); 404 vira (404, b'')."""
    requisicao = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    ultimo_erro: Exception | None = None
    for tentativa in range(tentativas):
        try:
            with urllib.request.urlopen(requisicao, timeout=60) as resposta:
                return resposta.status, resposta.read()
        except urllib.error.HTTPError as erro:
            if erro.code in (403, 404, 410):
                return erro.code, b""
            ultimo_erro = erro
        except (urllib.error.URLError, TimeoutError) as erro:
            ultimo_erro = erro
        time.sleep(1.5 * (tentativa + 1))
    raise RuntimeError(f"falha ao baixar {url}: {ultimo_erro}")


def url_base_uf(uf: str) -> str:
    return (
        f"{HOST}/{uf.lower()}/{UFS[uf]}/eleicoes/2026/pesquisas-eleitorais/"
        "senador/1-turno"
    )


def url_painel(uf: str, instituto_slug: str) -> str:
    return f"{url_base_uf(uf)}/{instituto_slug}/internal/"


def url_api(pagina_id: str, codigo: str, instituto: str) -> str:
    return (
        f"{HOST}/api/pesquisas-eleitorais/graficos/{pagina_id}/"
        f"?tipo_pergunta={codigo}&instituto={urllib.parse.quote(instituto)}"
    )


# ------------------------------------------------------------- parser (HTML)


def parse_institutos(pagina: str) -> list[str]:
    """Nomes dos institutos nos seletores da pagina de senador."""
    achados = re.findall(
        r'data-url="[^"]*/senador/1-turno/([^"/]+)"',
        pagina,
    )
    vistos: list[str] = []
    for nome in achados:
        if nome not in vistos:
            vistos.append(nome)
    return vistos


def parse_config(pagina: str) -> dict[str, str]:
    """Le o bloco window.g1PesquisasEleitorais (paginaId, instituto, tipoPergunta)."""
    bloco = re.search(
        r"window\.g1PesquisasEleitorais\s*=\s*\{(.*?)\}", pagina, re.DOTALL
    )
    if not bloco:
        return {}
    pares = re.findall(r'(\w+):\s*"([^"]*)"', bloco.group(1))
    return dict(pares)


def parse_codigos(pagina: str) -> list[str]:
    """Todos os codigos de pergunta de senador, na ordem em que aparecem."""
    vistos: list[str] = []
    for tipo, numero in CODIGO_RE.findall(pagina):
        codigo = f"{tipo}-SEN-{numero}"
        if codigo not in vistos:
            vistos.append(codigo)
    return vistos


def tipo_do_codigo(codigo: str) -> str:
    return TIPOS[codigo.split("-")[0]]


def parse_metodologia_texto(pagina: str) -> str | None:
    achado = re.search(
        r'class="methodology__description"[^>]*>(.*?)</p>', pagina, re.DOTALL
    )
    if not achado:
        return None
    texto = re.sub(r"<[^>]+>", " ", achado.group(1))
    return re.sub(r"\s+", " ", html.unescape(texto)).strip() or None


# -------------------------------------------------------- parser (metodologia)

_MES = "|".join(MESES)


def _data(dia: str, mes: str, ano: int = ANO) -> str:
    return f"{ano:04d}-{MESES[mes]:02d}-{int(dia):02d}"


def parse_campo(texto: str) -> dict[str, str] | None:
    """Datas de campo ('entre os dias 2 e 3 de outubro', '28 de setembro a 1º de outubro')."""
    t = sem_acento(texto).lower()
    com_dois_meses = re.search(
        rf"(\d{{1,2}})\s*(?:º|°|o)?\s+de\s+({_MES})\s+(?:a|e|ate)\s+"
        rf"(\d{{1,2}})\s*(?:º|°|o)?\s+de\s+({_MES})",
        t,
    )
    if com_dois_meses:
        d1, m1, d2, m2 = com_dois_meses.groups()
        return {"inicio": _data(d1, m1), "fim": _data(d2, m2)}
    com_um_mes = re.search(
        rf"(\d{{1,2}})\s*(?:º|°|o)?\s+(?:a|e|ate)\s+(\d{{1,2}})\s*(?:º|°|o)?\s+"
        rf"de\s+({_MES})",
        t,
    )
    if com_um_mes:
        d1, d2, m = com_um_mes.groups()
        return {"inicio": _data(d1, m), "fim": _data(d2, m)}
    unico = re.search(rf"dia\s+(\d{{1,2}})\s*(?:º|°|o)?\s+de\s+({_MES})", t)
    if unico:
        dia, mes = unico.groups()
        return {"inicio": _data(dia, mes), "fim": _data(dia, mes)}
    return None


def parse_n(texto: str) -> int | None:
    for numero, _ in re.findall(
        r"(\d{1,3}(?:\.\d{3})+|\d{3,})\s+(entrevistas|eleitores|pessoas|moradores)",
        sem_acento(texto).lower(),
    ):
        valor = int(numero.replace(".", ""))
        if valor >= 100:
            return valor
    return None


def parse_margem(texto: str) -> float | None:
    achado = re.search(
        r"margem de erro[^.]*?\b(\d+(?:,\d+)?|um|dois|tres|quatro|cinco)\s+pontos?",
        sem_acento(texto).lower(),
    )
    if not achado:
        return None
    valor = achado.group(1)
    if valor in NUMEROS_POR_EXTENSO:
        return float(NUMEROS_POR_EXTENSO[valor])
    return float(valor.replace(",", "."))


def parse_registros(texto: str, uf: str) -> list[str]:
    """Registros do TSE; o da UF vem primeiro."""
    todos = list(dict.fromkeys(re.findall(r"\b[A-Z]{2}-\d{4,6}/\d{4}\b", texto)))
    return sorted(todos, key=lambda r: not r.startswith(f"{uf}-"))


def parse_contratante(texto: str) -> str | None:
    achado = re.search(
        r"(?:encomendad[ao]|contratad[ao])\s+(?:pel[ao]s?|por)\s+(.+?)"
        r"(?:,\s|\s+e\s+(?:ouviu|realizou|entrevist)|\s+(?:ouviu|realizou|entrevist))",
        texto,
    )
    if not achado:
        return None
    return re.sub(r"\s+e\s+pel[ao]s?\s+", " e ", achado.group(1)).strip()


def parse_metodo(texto: str) -> str:
    t = sem_acento(texto).lower()
    if re.search(r"presenci|pessoais|face a face|domiciliar", t):
        return "presencial"
    if "telefon" in t:
        return "telefonico"
    if re.search(r"online|internet|digital", t):
        return "online"
    return "nao informado"


def parse_metodologia(texto: str | None, uf: str) -> dict:
    """Extrai contratante, n, campo, margem, registro e metodo da metodologia."""
    if not texto:
        return {}
    registros = parse_registros(texto, uf)
    return {
        "contratante": parse_contratante(texto),
        "n": parse_n(texto),
        "campo": parse_campo(texto),
        "margem_pp": parse_margem(texto),
        "registro_tse": registros[0] if registros else None,
        "outros_registros": registros[1:],
        "metodo": parse_metodo(texto),
    }


# -------------------------------------------------------------- parser (API)


def pp(valor: float) -> float:
    """Fracao do painel (0.16) em pontos percentuais (16.0)."""
    return round(valor * 100, 4)


def classificar_opcao(nome: str) -> str:
    """'branco_nulo', 'indecisos', 'outros' ou 'candidato'."""
    t = sem_acento(nome).lower()
    if "branco" in t or "nulo" in t or "nenhum" in t:
        return "branco_nulo"
    if "indecis" in t or "nao sabe" in t or "nao respond" in t:
        return "indecisos"
    if t.strip() in ("outros", "outro"):
        return "outros"
    return "candidato"


def escolher_cenario(resultado: dict) -> dict | None:
    cenarios = resultado.get("cenarios") or []
    for cenario in cenarios:
        if cenario.get("bandeira_slug") == "total":
            return cenario
    return cenarios[0] if cenarios else None


def opcoes_por_nome(cenario: dict) -> dict[str, dict]:
    return {o["nome"]: o for o in cenario.get("opcoes_resposta") or []}


def serie_por_data(cenario: dict) -> dict[str, dict[str, float]]:
    """{data AAAA-MM-DD: {opcao: valor em pp}} a partir de cenarios[0].data.

    O painel usa dois formatos: serie com `values` (varias ondas) e ponto solto
    com `date` e `value` (onda unica, desenhada como barra)."""
    por_data: dict[str, dict[str, float]] = {}
    for item in cenario.get("data") or []:
        pontos = item.get("values", [item])
        for ponto in pontos:
            if ponto.get("value") is None or not ponto.get("date"):
                continue
            data = str(ponto["date"])[:10]
            por_data.setdefault(data, {})[item["option"]] = pp(float(ponto["value"]))
    return por_data


def bloco_resposta(valores: dict[str, float], opcoes: dict[str, dict]) -> dict:
    """Converte o dicionario de uma data em candidatos, indecisos e branco/nulo."""
    candidatos: list[dict] = []
    indecisos: float | None = None
    branco_nulo: float | None = None
    outros: float | None = None
    for nome, valor in valores.items():
        classe = classificar_opcao(nome)
        if classe == "branco_nulo":
            branco_nulo = round((branco_nulo or 0.0) + valor, 4)
        elif classe == "indecisos":
            indecisos = round((indecisos or 0.0) + valor, 4)
        elif classe == "outros":
            outros = round((outros or 0.0) + valor, 4)
        else:
            info = opcoes.get(nome, {})
            partido = (info.get("partido") or {}).get("sigla")
            candidatos.append(
                {
                    "nome": nome,
                    "partido": normalizar_partido(partido),
                    "valor": valor,
                    "foto_url": info.get("foto"),
                }
            )
    candidatos.sort(key=lambda c: (-c["valor"], c["nome"]))
    return {
        "candidatos": candidatos,
        "indecisos": indecisos,
        "branco_nulo": branco_nulo,
        "outros": outros,
    }


def normalizar_partido(sigla: str | None) -> str | None:
    if not sigla:
        return None
    return sem_acento(sigla).upper() if sigla.upper() == "PCDOB" else sigla.upper()


def soma_bloco(bloco: dict) -> float:
    total = sum(c["valor"] for c in bloco["candidatos"])
    for chave in ("indecisos", "branco_nulo", "outros"):
        total += bloco.get(chave) or 0.0
    return round(total, 4)


# ------------------------------------------------------------ montagem da onda


def montar_onda(
    *,
    uf: str,
    instituto: str,
    data: str,
    estimulada: tuple[dict, dict, dict],
    extras: dict[str, tuple[dict, dict]],
    metodologia: dict,
    fonte: dict,
    pergunta: dict,
    com_metodologia: bool,
    disclaimer: str | None,
) -> dict:
    """Monta o JSON de uma onda. `estimulada` = (valores por data, opcoes, cenario)."""
    por_data, opcoes, _ = estimulada
    tem_estimulada = data in por_data
    bloco = bloco_resposta(por_data.get(data, {}), opcoes)
    soma = soma_bloco(bloco) if tem_estimulada else None
    campo = metodologia.get("campo") if com_metodologia else None
    observacoes: list[str] = []
    if disclaimer:
        observacoes.append(disclaimer)
    if com_metodologia and metodologia.get("outros_registros"):
        observacoes.append(
            "Outros registros citados na metodologia: "
            + ", ".join(metodologia["outros_registros"])
            + "."
        )
    if not tem_estimulada:
        observacoes.append(
            "O painel ainda não traz a estimulada nesta data: só há as perguntas "
            "extras (espontânea ou válidos). Sem candidatos para a média."
        )
    if bloco["outros"] is not None:
        observacoes.append(f"Categoria 'Outros' no painel: {bloco['outros']} pp.")
    onda = {
        "instituto": instituto,
        "instituto_slug": slug_instituto(instituto),
        "uf": uf,
        "cargo": "senador",
        "registro_tse": metodologia.get("registro_tse") if com_metodologia else None,
        "campo": campo,
        "divulgacao": data,
        "n": metodologia.get("n") if com_metodologia else None,
        "margem_pp": metodologia.get("margem_pp") if com_metodologia else None,
        "metodo": (
            metodologia.get("metodo", "nao informado") if com_metodologia else None
        ),
        "contratante": metodologia.get("contratante") if com_metodologia else None,
        "fonte": fonte,
        "pergunta": {
            **pergunta,
            "tipo": "estimulada" if tem_estimulada else "espontanea",
            "votos_por_eleitor": 2 if soma and soma > 150 else 1,
            "soma_total": soma,
            "nota": (
                None
                if soma is None
                else (
                    "A soma passa de 150: a pergunta pede dois nomes."
                    if soma > 150
                    else "A soma fica perto de 100: o painel reporta a fração "
                    "de menções, não duas escolhas por eleitor."
                )
            ),
        },
        "candidatos": bloco["candidatos"],
        "indecisos": bloco["indecisos"],
        "branco_nulo": bloco["branco_nulo"],
        "observacoes": observacoes,
    }
    for tipo, (valores, opcoes_extra) in extras.items():
        if data in valores:
            extra = bloco_resposta(valores[data], opcoes_extra)
            onda[tipo] = {
                "candidatos": extra["candidatos"],
                "indecisos": extra["indecisos"],
                "branco_nulo": extra["branco_nulo"],
                "soma_total": soma_bloco(extra),
            }
    return onda


def onda_da_metodologia(datas: list[str], metodologia: dict) -> str | None:
    """Data da onda a que a metodologia se refere: a primeira divulgacao em ate
    3 dias depois do fim do campo. O painel nem sempre atualiza o texto junto com
    a serie, entao a metodologia pode ser de uma onda anterior a mais recente."""
    fim = (metodologia.get("campo") or {}).get("fim")
    if not fim:
        return None
    limite = (datetime.fromisoformat(fim) + timedelta(days=3)).date().isoformat()
    candidatas = [d for d in datas if fim <= d <= limite]
    return candidatas[0] if candidatas else None


def nome_arquivo_onda(onda: dict, usados: set[str]) -> str:
    fim = (onda["campo"] or {}).get("fim") or onda["divulgacao"]
    base = f"{onda['instituto_slug']}_{onda['uf']}_{fim}.json"
    if base in usados:
        base = f"{onda['instituto_slug']}_{onda['uf']}_{onda['divulgacao']}.json"
    usados.add(base)
    return base


# ---------------------------------------------------------------- coleta (E/S)


def salvar_bruto(caminho: Path, dados: bytes) -> dict:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(dados)
    return {"bytes": len(dados), "sha256": sha256_bytes(dados)}


def carregar_fonte(uf: str) -> dict:
    caminho = RAW_DIR / f"{uf}_fonte.json"
    if caminho.exists():
        return json.loads(caminho.read_text(encoding="utf-8"))
    return {"uf": uf, "arquivos": {}}


def registrar(fonte: dict, caminho: Path, url: str, dados: bytes) -> None:
    fonte["arquivos"][caminho.name] = {
        "url": url,
        "arquivo": rel(caminho),
        "bytes": len(dados),
        "sha256": sha256_bytes(dados),
        "capturado_em": agora_utc(),
    }


def coletar_uf(uf: str, fonte: dict) -> list[str]:
    """Baixa painel e APIs de todos os institutos da UF. Devolve os slugs salvos."""
    status, base = baixar(url_base_uf(uf) + "/")
    if status != 200:
        print(f"{uf}: pagina base {status}, sem painel de senador")
        return []
    nomes = parse_institutos(base.decode("utf-8", "replace"))
    if not nomes:
        config = parse_config(base.decode("utf-8", "replace"))
        nomes = [config["instituto"]] if config.get("instituto") else []
    salvos: list[str] = []
    for nome in nomes:
        slug = slug_instituto(nome)
        url = url_painel(uf, nome.lower())
        status, pagina = baixar(url)
        if status != 200:
            print(f"{uf}/{nome}: painel {status}")
            continue
        caminho = RAW_DIR / f"{uf}_{slug}_painel.html"
        salvar_bruto(caminho, pagina)
        registrar(fonte, caminho, url, pagina)
        texto = pagina.decode("utf-8", "replace")
        config = parse_config(texto)
        for codigo in parse_codigos(texto):
            api = url_api(config["paginaId"], codigo, config["instituto"])
            status, corpo = baixar(api)
            if status != 200:
                print(f"{uf}/{nome}/{codigo}: API {status}")
                continue
            destino = RAW_DIR / f"{uf}_{slug}_{codigo}.json"
            salvar_bruto(destino, corpo)
            registrar(fonte, destino, api, corpo)
            time.sleep(0.15)
        salvos.append(slug)
        time.sleep(0.15)
    return salvos


def institutos_salvos(uf: str) -> list[str]:
    return sorted(
        p.name[len(uf) + 1 : -len("_painel.html")]
        for p in RAW_DIR.glob(f"{uf}_*_painel.html")
    )


def ler_series(uf: str, slug: str, config: dict, texto: str) -> dict:
    """Le do disco os JSON da API de cada codigo do painel."""
    series: dict[str, tuple[dict, dict, dict]] = {}
    disclaimer = None
    for codigo in parse_codigos(texto):
        caminho = RAW_DIR / f"{uf}_{slug}_{codigo}.json"
        if not caminho.exists():
            continue
        resultado = json.loads(caminho.read_text(encoding="utf-8")).get("resultado", {})
        cenario = escolher_cenario(resultado)
        if not cenario:
            continue
        series[codigo] = (serie_por_data(cenario), opcoes_por_nome(cenario), cenario)
        disclaimer = disclaimer or resultado.get("disclaimer") or None
    return {"series": series, "disclaimer": disclaimer}


def codigo_principal(codigos: list[str], config: dict) -> str | None:
    estimuladas = [c for c in codigos if c.startswith("ESTIMULADA")]
    padrao = config.get("tipoPergunta")
    if padrao in estimuladas:
        return padrao
    return estimuladas[0] if estimuladas else None


def processar_instituto(uf: str, slug: str, fonte: dict, usados: set[str]) -> dict:
    """Grava as ondas do instituto e devolve o resumo para a cobertura."""
    pagina = RAW_DIR / f"{uf}_{slug}_painel.html"
    texto = pagina.read_text(encoding="utf-8")
    config = parse_config(texto)
    instituto = config.get("instituto") or slug
    lidas = ler_series(uf, slug, config, texto)
    series = lidas["series"]
    principal = codigo_principal(list(series), config)
    if not principal:
        return {"instituto": instituto, "slug": slug, "ondas": 0}
    por_data, opcoes, cenario = series[principal]
    metodologia = parse_metodologia(parse_metodologia_texto(texto), uf)
    extras = {
        tipo_do_codigo(c): (v[0], v[1])
        for c, v in series.items()
        if not c.startswith("ESTIMULADA")
    }
    registro_fonte = fonte["arquivos"].get(f"{uf}_{slug}_{principal}.json", {})
    datas = sorted(set(por_data).union(*(set(v[0]) for v in extras.values())))
    data_metodologia = onda_da_metodologia(datas, metodologia)
    resumo: dict = {
        "instituto": instituto,
        "slug": slug,
        "ondas": len(datas),
        "metodologia_campo": metodologia.get("campo"),
        "metodologia_onda": data_metodologia,
    }
    pasta = rel(RAW_DIR)
    infos: dict[str, dict] = {}
    for data in datas:
        onda = montar_onda(
            uf=uf,
            instituto=instituto,
            data=data,
            estimulada=(por_data, opcoes, cenario),
            extras=extras,
            metodologia=metodologia,
            fonte={
                "tipo": "painel_g1",
                "url": registro_fonte.get("url"),
                "arquivo": f"{pasta}/{uf}_{slug}_{principal}.json",
                "sha256": registro_fonte.get("sha256"),
                "pagina": None,
                "capturado_em": registro_fonte.get("capturado_em"),
                "painel_url": fonte["arquivos"]
                .get(f"{uf}_{slug}_painel.html", {})
                .get("url"),
            },
            pergunta={"codigo": principal},
            com_metodologia=data == data_metodologia,
            disclaimer=lidas["disclaimer"],
        )
        nome = nome_arquivo_onda(onda, usados)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / nome).write_text(
            json.dumps(onda, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        infos[data] = {
            "campo": onda["campo"],
            "n": onda["n"],
            "soma_total": onda["pergunta"]["soma_total"],
            "arquivo": nome,
        }
    resumo.update(resumo_ondas(infos, por_data))
    resumo["codigos"] = sorted(series)
    return resumo


def resumo_ondas(infos: dict[str, dict], por_data: dict) -> dict:
    """Resumo da cobertura: ultima divulgacao e ultima onda com estimulada."""
    ultima = max(infos)
    estimuladas = [d for d in infos if d in por_data]
    resumo = {"ultima_divulgacao": ultima, **infos[ultima]}
    if estimuladas:
        ref = max(estimuladas)
        fim = (infos[ref]["campo"] or {}).get("fim")
        resumo["ultima_estimulada"] = {
            "divulgacao": ref,
            **infos[ref],
            "campo_fim_ate_28_09_ou_depois": (
                None if fim is None else fim >= CORTE_CAMPO
            ),
        }
    else:
        resumo["ultima_estimulada"] = None
    return resumo


def limpar_ondas_antigas(ufs: list[str]) -> None:
    """Remove ondas geradas antes por este script para as UFs em reprocessamento."""
    for uf in ufs:
        for arquivo in OUT_DIR.glob(f"*_{uf}_*.json"):
            try:
                dados = json.loads(arquivo.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if (dados.get("fonte") or {}).get("tipo") == "painel_g1":
                arquivo.unlink()


def tabela(cobertura: dict) -> str:
    linhas = ["UF  instituto        ult. estimulada  campo                  soma"]
    for uf, item in cobertura.items():
        for inst in item["institutos"]:
            ref = inst.get("ultima_estimulada") or {}
            campo = ref.get("campo")
            texto_campo = f"{campo['inicio']}..{campo['fim']}" if campo else "-"
            linhas.append(
                f"{uf:<3} {inst['instituto']:<16} "
                f"{ref.get('divulgacao', '-'):<16} {texto_campo:<22} "
                f"{ref.get('soma_total', '-')}"
            )
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--uf", nargs="*", help="UFs a processar (padrao: todas)")
    analisador.add_argument(
        "--skip-download", action="store_true", help="reprocessa o bruto salvo"
    )
    args = analisador.parse_args(argv)
    ufs = [u.upper() for u in args.uf] if args.uf else list(UFS)
    invalidas = [u for u in ufs if u not in UFS]
    if invalidas:
        print(f"UFs invalidas: {invalidas}", file=sys.stderr)
        return 2
    limpar_ondas_antigas(ufs)
    usados: set[str] = set()
    cobertura: dict[str, dict] = {}
    for uf in ufs:
        fonte = carregar_fonte(uf)
        if not args.skip_download:
            coletar_uf(uf, fonte)
            fonte["uf"] = uf
            (RAW_DIR / f"{uf}_fonte.json").write_text(
                json.dumps(fonte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        institutos = [
            processar_instituto(uf, s, fonte, usados) for s in institutos_salvos(uf)
        ]
        institutos = [i for i in institutos if i["ondas"]]
        cobertura[uf] = {"institutos": institutos, "tem_pesquisa": bool(institutos)}
    existente: dict = {}
    if COBERTURA.exists() and args.uf:
        existente = json.loads(COBERTURA.read_text(encoding="utf-8")).get("ufs", {})
    existente.update(cobertura)
    todas = {uf: existente[uf] for uf in UFS if uf in existente}
    COBERTURA.parent.mkdir(parents=True, exist_ok=True)
    COBERTURA.write_text(
        json.dumps(
            {"gerado_em": agora_utc(), "corte_campo": CORTE_CAMPO, "ufs": todas},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(tabela(cobertura))
    sem = [uf for uf, item in cobertura.items() if not item["tem_pesquisa"]]
    print("\nUFs sem pesquisa de Senado no painel:", ", ".join(sem) or "nenhuma")
    return 0


if __name__ == "__main__":
    sys.exit(main())
