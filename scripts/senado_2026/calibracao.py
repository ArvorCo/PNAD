"""Calibração do erro de pesquisa de Senado com a eleição de 2022.

Duas fontes, as duas guardadas no repositório com SHA-256:

- urna: `data/raw/tse_resultados/votacao_candidato_munzona_2022.zip`, cargo 5
  (Senador), 1º turno, soma de `QT_VOTOS_NOMINAIS_VALIDOS` por `SQ_CANDIDATO`
  em streaming (latin-1, `;`);
- pesquisas: o texto bruto (wikitext) das páginas da Wikipédia em português
  "Eleições estaduais em <estado> em 2022", seção de pesquisas para senador,
  usado como índice das pesquisas finais. Cada linha guarda o instituto, as
  datas e o link da matéria que a Wikipédia cita.

O módulo só lê, casa e mede. A escala do erro não amostral sai daqui para o
motor; se a cobertura não alcançar o mínimo declarado, o motor usa a hipótese
declarada em `HIPOTESE`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from collections import defaultdict
from datetime import date, datetime, timezone
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
URNA_ZIP = ROOT / "data/raw/tse_resultados/votacao_candidato_munzona_2022.zip"
WIKI_DIR = ROOT / "data/originals/senado_102026/wikipedia_2022"
SAIDA = ROOT / "analysis/senado_2026/calibracao_2022.json"
ELEICAO_2022 = date(2022, 10, 2)

# Janela das pesquisas finais de 2022: fim do campo até 8 dias antes do 1º turno,
# espelhando o corte de 2026 (28/09 para a eleição de 04/10, 6 dias, mais folga
# porque em 2022 as últimas ondas estaduais terminaram entre 24/09 e 01/10).
CORTE_2022 = date(2022, 9, 24)
CASAS_PRINCIPAIS = ("ipec", "datafolha", "quaest")
DEFF = 1.5
MIN_ESTADOS = 15
# Limiares para a medida em log: abaixo deles o log amplifica arredondamento.
MIN_VALIDO_POLL = 0.02
MIN_VALIDO_URNA = 0.01

TITULOS = {
    "AC": "Eleições estaduais no Acre em 2022",
    "AL": "Eleições estaduais em Alagoas em 2022",
    "AP": "Eleições estaduais no Amapá em 2022",
    "AM": "Eleições estaduais no Amazonas em 2022",
    "BA": "Eleições estaduais na Bahia em 2022",
    "CE": "Eleições estaduais no Ceará em 2022",
    "DF": "Eleições distritais no Distrito Federal em 2022",
    "ES": "Eleições estaduais no Espírito Santo em 2022",
    "GO": "Eleições estaduais em Goiás em 2022",
    "MA": "Eleições estaduais no Maranhão em 2022",
    "MT": "Eleições estaduais em Mato Grosso em 2022",
    "MS": "Eleições estaduais em Mato Grosso do Sul em 2022",
    "MG": "Eleições estaduais em Minas Gerais em 2022",
    "PA": "Eleições estaduais no Pará em 2022",
    "PB": "Eleições estaduais na Paraíba em 2022",
    "PR": "Eleições estaduais no Paraná em 2022",
    "PE": "Eleições estaduais em Pernambuco em 2022",
    "PI": "Eleições estaduais no Piauí em 2022",
    "RJ": "Eleições estaduais no Rio de Janeiro em 2022",
    "RN": "Eleições estaduais no Rio Grande do Norte em 2022",
    "RS": "Eleições estaduais no Rio Grande do Sul em 2022",
    "RO": "Eleições estaduais em Rondônia em 2022",
    "RR": "Eleições estaduais em Roraima em 2022",
    "SC": "Eleições estaduais em Santa Catarina em 2022",
    "SP": (
        "Predefinição:Pesquisas de opinião das Eleições estaduais em São Paulo "
        "em 2022 (senador)"
    ),
    "SE": "Eleições estaduais em Sergipe em 2022",
    "TO": "Eleições estaduais no Tocantins em 2022",
}

# Hipótese usada só quando a calibração não alcança MIN_ESTADOS: desvio total
# de 6 pontos dos válidos para candidatura em 30%. Motivo: muitas candidaturas,
# voto útil tardio e amostras estaduais menores fazem o erro de Senado ser bem
# maior que o presidencial (erro comum de 2022 na diferença L-B: 3,92 pp,
# analysis/predicao_2026/erro_2022/erro_2022.json).
HIPOTESE = {"sd_pp_30": 6.0}

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

PARTIDO_ALIAS = {
    "PODEMOS": "PODE",
    "UNIAOBRASIL": "UNIAO",
    "PCDOB": "PCDOB",
    "SOLIDARIEDADE": "SOLIDARIEDADE",
    "SD": "SOLIDARIEDADE",
    "PATRI": "PATRIOTA",
    "REPUBLICANO": "REPUBLICANOS",
}


def sem_acento(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in base if not unicodedata.combining(c))


def chave_partido(sigla: str | None) -> str:
    limpo = re.sub(r"[^A-Z0-9]", "", sem_acento(sigla or "").upper())
    return PARTIDO_ALIAS.get(limpo, limpo)


def tokens(texto: str) -> set[str]:
    limpo = re.sub(r"[^a-z0-9]+", " ", sem_acento(texto).lower())
    return {t for t in limpo.split() if len(t) >= 3}


def sha256(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


# ------------------------------------------------------------------ urna 2022


FILTRO_CARGO = {"5": b';5;"Senador";', "3": b';3;"Governador";'}


def urna_2022(zip_path: Path = URNA_ZIP, cargo: str = "5") -> dict[str, list[dict]]:
    """Votos nominais e válidos por candidatura ao cargo (5 senador, 3
    governador), por UF, 1º turno."""
    filtro = FILTRO_CARGO[cargo]
    saida: dict[str, list[dict]] = {}
    with zipfile.ZipFile(zip_path) as z:
        for membro in sorted(z.namelist()):
            uf = membro.rsplit("_", 1)[-1].removesuffix(".csv")
            if not membro.endswith(".csv") or len(uf) != 2 or uf == "BR":
                continue
            votos: dict[str, list[int]] = defaultdict(lambda: [0, 0])
            info: dict[str, dict] = {}
            with z.open(membro) as f:
                cab = next(csv.reader([f.readline().decode("latin-1")], delimiter=";"))
                idx = {k: i for i, k in enumerate(cab)}
                for linha in f:
                    # Filtro em bytes antes do csv: só as linhas do cargo.
                    if filtro not in linha:
                        continue
                    r = next(csv.reader([linha.decode("latin-1")], delimiter=";"))
                    if r[idx["NR_TURNO"]] != "1":
                        continue
                    sq = r[idx["SQ_CANDIDATO"]]
                    votos[sq][0] += int(r[idx["QT_VOTOS_NOMINAIS"]] or 0)
                    votos[sq][1] += int(r[idx["QT_VOTOS_NOMINAIS_VALIDOS"]] or 0)
                    info[sq] = {
                        "sq_candidato": sq,
                        "nome_urna": r[idx["NM_URNA_CANDIDATO"]],
                        "nome_completo": r[idx["NM_CANDIDATO"]],
                        "partido": r[idx["SG_PARTIDO"]],
                        "situacao": r[idx["DS_SIT_TOT_TURNO"]],
                        "destinacao": r[idx["NM_TIPO_DESTINACAO_VOTOS"]],
                    }
            total = sum(v[1] for v in votos.values())
            linhas = [
                {
                    **info[sq],
                    "votos_nominais": votos[sq][0],
                    "votos_validos": votos[sq][1],
                    "pct_validos": 100 * votos[sq][1] / total if total else 0.0,
                }
                for sq in votos
            ]
            linhas.sort(key=lambda c: -c["votos_validos"])
            saida[uf] = linhas
    return saida


# ---------------------------------------------------------------- wikipédia


def url_wiki(titulo: str, *, raw: bool) -> str:
    if raw:
        q = urllib.parse.urlencode({"title": titulo, "action": "raw"})
        return f"https://pt.wikipedia.org/w/index.php?{q}"
    return "https://pt.wikipedia.org/wiki/" + urllib.parse.quote(
        titulo.replace(" ", "_")
    )


def baixar_wiki(uf: str, destino: Path = WIKI_DIR) -> dict:
    """Baixa o wikitext bruto e grava com SHA-256 e hora de acesso."""
    destino.mkdir(parents=True, exist_ok=True)
    titulo = TITULOS[uf]
    req = urllib.request.Request(
        url_wiki(titulo, raw=True),
        headers={"User-Agent": "brasil.arvor.co pesquisa (ld@arvor.co)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        corpo = resp.read()
    arquivo = destino / f"{uf}.wiki"
    arquivo.write_bytes(corpo)
    return {
        "uf": uf,
        "titulo": titulo,
        "url": url_wiki(titulo, raw=False),
        "url_bruto": url_wiki(titulo, raw=True),
        "arquivo": str(arquivo.relative_to(ROOT)),
        "sha256": hashlib.sha256(corpo).hexdigest(),
        "acessado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def secao_senado(
    texto: str, *, modelo: bool = False, padrao: str = "senad"
) -> str | None:
    """Primeira tabela de pesquisa do cargo (título com `padrao`) na seção de
    pesquisas."""
    if modelo:
        bloco = texto
    else:
        m = re.search(r"^==\s*Pesquisas[^=\n]*==\s*$", texto, re.MULTILINE)
        if not m:
            return None
        resto = texto[m.end() :]
        fim = re.search(r"^==[^=]", resto, re.MULTILINE)
        resto = resto[: fim.start()] if fim else resto
        s = re.search(
            rf"^(=+)[^=\n]*{padrao}[^=\n]*=+\s*$", resto, re.MULTILINE | re.IGNORECASE
        )
        if not s:
            return None
        nivel = len(s.group(1))
        bloco = resto[s.end() :]
        # O bloco vai até o próximo título de nível igual ou superior, exceto
        # os subtítulos de turno ("Primeiro turno"), que ficam dentro dele.
        prox = next(
            (
                m
                for m in re.finditer(
                    rf"^(={{1,{nivel}}})([^=\n]*)=+\s*$", bloco, re.MULTILINE
                )
                if "turno" not in m.group(2).lower()
            ),
            None,
        )
        bloco = bloco[: prox.start()] if prox else bloco
    ini = bloco.find("{|")
    if ini < 0:
        return None
    fim_tab = bloco.find("\n|}", ini)
    return bloco[ini : fim_tab if fim_tab > 0 else len(bloco)]


def _limpa_refs(texto: str) -> str:
    texto = re.sub(r"<ref[^>/]*/>", "", texto)
    texto = re.sub(r"<ref[^>]*>.*?</ref>", "", texto, flags=re.DOTALL)
    # Notas {{Efn...}} podem conter barras e colchetes: remove com contagem.
    saida, i = [], 0
    while i < len(texto):
        if texto.startswith("{{Efn", i) or texto.startswith("{{efn", i):
            prof, j = 0, i
            while j < len(texto):
                if texto.startswith("{{", j):
                    prof += 1
                    j += 2
                elif texto.startswith("}}", j):
                    prof -= 1
                    j += 2
                    if prof == 0:
                        break
                else:
                    j += 1
            i = j
        else:
            saida.append(texto[i])
            i += 1
    return "".join(saida)


def _divide(linha: str, sep: str) -> list[str]:
    """Divide por `||` ou `!!` fora de [[ ]] e {{ }}."""
    partes, prof, atual, i = [], 0, [], 0
    while i < len(linha):
        dois = linha[i : i + 2]
        if dois in ("[[", "{{"):
            prof += 1
            atual.append(dois)
            i += 2
        elif dois in ("]]", "}}"):
            prof = max(0, prof - 1)
            atual.append(dois)
            i += 2
        elif dois == sep and prof == 0:
            partes.append("".join(atual))
            atual = []
            i += 2
        else:
            atual.append(linha[i])
            i += 1
    partes.append("".join(atual))
    return partes


def _celula(bruto: str) -> tuple[dict, str]:
    """Separa atributos do conteúdo: `attr | conteúdo` (barra fora de links)."""
    prof, corte = 0, None
    i = 0
    while i < len(bruto):
        dois = bruto[i : i + 2]
        if dois in ("[[", "{{"):
            prof += 1
            i += 2
            continue
        if dois in ("]]", "}}"):
            prof = max(0, prof - 1)
            i += 2
            continue
        if bruto[i] == "[":
            prof += 1
        elif bruto[i] == "]":
            prof = max(0, prof - 1)
        elif bruto[i] == "|" and prof == 0:
            corte = i
            break
        i += 1
    attrs: dict = {}
    if corte is not None and "=" in bruto[:corte]:
        a = bruto[:corte]
        for k in ("rowspan", "colspan"):
            m = re.search(rf'{k}\s*=\s*"?(\d+)', a)
            if m:
                attrs[k] = int(m.group(1))
        return attrs, bruto[corte + 1 :].strip()
    return attrs, bruto.strip()


def tabela(texto: str) -> list[list[str]]:
    """Grade da tabela com rowspan e colspan expandidos."""
    texto = _limpa_refs(texto)
    linhas_brutas: list[list[tuple[dict, str]]] = [[]]
    for linha in texto.split("\n")[1:]:
        s = linha.rstrip()
        if s.startswith("|-"):
            linhas_brutas.append([])
            continue
        if s.startswith("|}"):
            break
        if s.startswith(("|", "!")):
            sep = "!!" if s.startswith("!") else "||"
            linhas_brutas[-1].extend(_celula(c) for c in _divide(s[1:], sep))
        elif linhas_brutas[-1]:
            a, c = linhas_brutas[-1][-1]
            linhas_brutas[-1][-1] = (a, c + " " + s)
    grade: list[list[str]] = []
    pendentes: dict[int, tuple[int, str]] = {}
    for brutas in linhas_brutas:
        if not brutas:
            continue
        linha_out: list[str] = []
        col = 0
        fila = list(brutas)
        while fila or col in pendentes:
            if col in pendentes:
                resta, val = pendentes[col]
                linha_out.append(val)
                if resta > 1:
                    pendentes[col] = (resta - 1, val)
                else:
                    del pendentes[col]
                col += 1
                continue
            attrs, val = fila.pop(0)
            for _ in range(attrs.get("colspan", 1)):
                linha_out.append(val)
                if attrs.get("rowspan", 1) > 1:
                    pendentes[col] = (attrs["rowspan"] - 1, val)
                col += 1
        grade.append(linha_out)
    return grade


def _texto(celula: str) -> str:
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", celula)
    t = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", t)
    t = re.sub(r"\{\{[^{}|]*\|([^{}]*)\}\}", r"\1", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t.replace("'''", "").replace("''", "")).strip()


def cabecalho_candidato(celula: str) -> dict | None:
    """Nome curto, alvo do link e partido de uma célula de cabeçalho.

    O partido vem em `{{small|..}}`, `{{pequeno|..}}`, `<small>..</small>` ou
    entre parênteses no fim do texto, conforme a página.
    """
    padroes = (
        r"\{\{\s*(?:small|pequeno)\s*\|(.*?)\}\}\s*$",
        r"<small>(.*?)</small>\s*$",
        r"\(([^()]*)\)\s*$",
    )
    for padrao in padroes:
        m = re.search(padrao, celula.strip(), re.DOTALL | re.IGNORECASE)
        if m:
            break
    else:
        return None
    partido = _texto(m.group(1)).strip("() ")
    if not partido or len(partido) > 20:
        return None
    antes = celula.strip()[: m.start()]
    alvo = re.search(r"\[\[([^|\]]+)(?:\|[^\]]*)?\]\]", antes)
    rotulo = _texto(antes)
    if not rotulo:
        return None
    return {
        "rotulo": rotulo,
        "alvo": alvo.group(1) if alvo else None,
        "partido": partido,
    }


def numero(celula: str) -> float | None:
    t = _texto(celula).replace("%", "").strip()
    m = re.match(r"^-?\d+(?:[.,]\d+)?$", t)
    if not m:
        return None
    return float(t.replace(".", "").replace(",", ".") if "," in t else t)


def amostra(celula: str) -> int | None:
    t = re.sub(r"[^\d]", "", _texto(celula))
    return int(t) if t else None


def datas(celula: str, ano_padrao: int = 2022) -> tuple[date, date] | None:
    """'27–29 de setembro de 2022', '30 de setembro–1 de outubro', '27/08-02/09'."""
    t = _texto(celula).replace(".º", "").replace("º", "").replace("ª", "")
    t = sem_acento(t).lower()
    t = re.sub(r"(\d)o\b", r"\1", t)
    partes = [s.strip() for s in re.split(r"\s*[-–]\s*|\s+a\s+", t) if s.strip()]
    if not partes:
        return None
    barra = r"^(\d{1,2})(?:/(\d{1,2}))?(?:/(\d{2,4}))?$"
    com_barra = [re.match(barra, s) for s in partes[:2]]
    if all(com_barra):
        lidas = [m.groups() for m in com_barra if m]
        d2, m2, a2 = lidas[-1]
        if m2 is None:
            return None
        ano = int(a2) + (2000 if a2 and len(a2) == 2 else 0) if a2 else ano_padrao
        d1, m1, _ = lidas[0]
        return date(ano, int(m1 or m2), int(d1)), date(ano, int(m2), int(d2))
    padrao = r"^(\d{1,2})(?: de ([a-z]+))?(?: de (\d{4}))?"
    achados = [re.match(padrao, s) for s in partes[:2]]
    lidas = [m.groups() for m in achados if m]
    if len(lidas) != len(achados):
        return None
    d2, m2, a2 = lidas[-1]
    if m2 not in MESES:
        return None
    d1, m1, a1 = lidas[0]
    ano = int(a2) if a2 else ano_padrao
    fim = date(ano, MESES[m2], int(d2))
    ini = date(int(a1) if a1 else ano, MESES.get(m1 or m2, MESES[m2]), int(d1))
    return ini, fim


def nome_instituto(celula: str) -> str:
    """Nome do instituto sem o registro do TSE nem notas."""
    primeiro = re.split(r"<br\s*/?>", celula, maxsplit=1)[0]
    texto = re.sub(r"[A-Z]{2}-\d{5}/\d{4}", "", _texto(primeiro))
    return re.sub(r"\s+", " ", texto).strip(" ,;")


def slug_casa(nome: str) -> str:
    t = sem_acento(nome).lower()
    for casa in ("ipec", "datafolha", "quaest", "atlas", "real time", "realtime"):
        if casa in t:
            return casa.replace(" ", "")
    return re.sub(r"[^a-z0-9]+", "", t)


def pesquisas_wiki(
    texto: str, *, modelo: bool = False, padrao: str = "senad"
) -> list[dict]:
    """Linhas de pesquisa do cargo de uma página, já em números."""
    tab = secao_senado(texto, modelo=modelo, padrao=padrao)
    if not tab:
        return []
    grade = tabela(tab)
    if not grade:
        return []
    cab = grade[0]
    colunas = []
    papel: dict[str, int] = {}
    for j, c in enumerate(cab):
        info = cabecalho_candidato(c)
        rot = sem_acento(_texto(c)).lower()
        if info:
            colunas.append(("candidato", j, info))
        elif "instituto" in rot and "instituto" not in papel:
            papel["instituto"] = j
        elif ("data" in rot or "periodo" in rot) and "datas" not in papel:
            papel["datas"] = j
        elif ("entrevist" in rot or "amostra" in rot) and "n" not in papel:
            papel["n"] = j
        elif "outro" in rot:
            colunas.append(("outros", j, None))
        elif any(k in rot for k in ("indecis", "absten", "branco", "nulo", "nao sab")):
            colunas.append(("nao_escolha", j, None))
    if not colunas or not {"instituto", "datas"} <= papel.keys():
        return []
    linhas = []
    for linha in grade[1:]:
        if len(linha) <= max(papel.values()):
            continue
        inst = nome_instituto(linha[papel["instituto"]])
        per = datas(linha[papel["datas"]])
        if not inst or not per:
            continue
        url = re.search(r"\[(https?://\S+)", linha[papel["instituto"]])
        valores, outros, nao = [], 0.0, 0.0
        for tipo, j, info in colunas:
            v = numero(linha[j]) if j < len(linha) else None
            if tipo == "candidato":
                valores.append({**info, "valor": v})
            elif tipo == "outros" and v is not None:
                outros += v
            elif tipo == "nao_escolha" and v is not None:
                nao += v
        linhas.append(
            {
                "instituto": inst,
                "casa": slug_casa(inst),
                "campo_inicio": per[0].isoformat(),
                "campo_fim": per[1].isoformat(),
                "n": amostra(linha[papel["n"]]) if "n" in papel else None,
                "url_materia": url.group(1) if url else None,
                "candidatos": valores,
                "outros": outros,
                "nao_escolha": nao,
            }
        )
    return linhas


# --------------------------------------------------------------- casamento


def casar(cand: dict, urna: list[dict]) -> dict | None:
    """Casa a coluna da Wikipédia com a candidatura: nome e partido."""
    alvo = tokens(cand["rotulo"]) | tokens(cand.get("alvo") or "")
    partido = chave_partido(cand["partido"])
    achados = []
    for u in urna:
        nomes = tokens(u["nome_urna"]) | tokens(u["nome_completo"])
        comum = alvo & nomes
        if comum:
            achados.append((chave_partido(u["partido"]) == partido, len(comum), u))
    if not achados:
        return None
    achados.sort(key=lambda a: (a[0], a[1]), reverse=True)
    if len(achados) > 1 and achados[0][:2] == achados[1][:2]:
        return None
    return achados[0][2]


def _anulada(u: dict | None) -> bool:
    return bool(u) and not str(u.get("destinacao") or "").startswith("V")


def pares_estado(uf: str, linhas: list[dict], urna: list[dict]) -> list[dict]:
    """Cada pesquisa final (uma onda por casa) contra a urna, nos válidos.

    Candidatura com votos anulados na urna (indeferida, sub judice) sai dos dois
    lados: a urna já não a conta nos válidos, e a pesquisa a mediu como voto
    que virou nulo.
    """
    finais: dict[str, dict] = {}
    for p in linhas:
        fim = date.fromisoformat(p["campo_fim"])
        if fim < CORTE_2022 or fim >= ELEICAO_2022:
            continue
        atual = finais.get(p["casa"])
        if atual is None or p["campo_fim"] > atual["campo_fim"]:
            finais[p["casa"]] = p
    saida = []
    for casa, p in sorted(finais.items()):
        casados = [
            (c, casar(c, urna)) for c in p["candidatos"] if c["valor"] is not None
        ]
        validos = [(c, u) for c, u in casados if not _anulada(u)]
        soma_validos = sum(c["valor"] for c, _ in validos) + p["outros"]
        if soma_validos <= 0:
            continue
        cands = []
        for c, u in casados:
            anulada = _anulada(u)
            cands.append(
                {
                    "rotulo": c["rotulo"],
                    "partido_wiki": c["partido"],
                    "sq_candidato": u["sq_candidato"] if u else None,
                    "nome_urna": u["nome_urna"] if u else None,
                    "partido": u["partido"] if u else None,
                    "anulada_na_urna": anulada,
                    "pesquisa_pct_total": c["valor"],
                    "pesquisa_pct_validos": (
                        None if anulada else 100 * c["valor"] / soma_validos
                    ),
                    "urna_pct_validos": (
                        u["pct_validos"] if u and not anulada else None
                    ),
                }
            )
        saida.append(
            {
                "uf": uf,
                "casa": casa,
                "instituto": p["instituto"],
                "campo_inicio": p["campo_inicio"],
                "campo_fim": p["campo_fim"],
                "dias_ate_eleicao": (
                    ELEICAO_2022 - date.fromisoformat(p["campo_fim"])
                ).days,
                "n": p["n"],
                "url_materia": p["url_materia"],
                "soma_validos_pesquisa": soma_validos,
                "nao_escolha_pct": p["nao_escolha"],
                "candidatos": cands,
            }
        )
    return saida


# ------------------------------------------------------------- estatísticas


def _resumo(xs: list[float]) -> dict:
    if not xs:
        return {"n": 0}
    n = len(xs)
    media = sum(xs) / n
    return {
        "n": n,
        "media": media,
        "erro_medio_absoluto": sum(abs(x) for x in xs) / n,
        "rmse": math.sqrt(sum(x * x for x in xs) / n),
        "desvio_padrao": (
            math.sqrt(sum((x - media) ** 2 for x in xs) / (n - 1)) if n > 1 else None
        ),
    }


def _comparaveis(p: dict) -> list[tuple[float, float, dict]]:
    """(pesquisa, urna, candidatura) em pontos dos válidos, só casadas válidas."""
    saida = []
    for c in p["candidatos"]:
        q, u = c["pesquisa_pct_validos"], c["urna_pct_validos"]
        if q is not None and u is not None:
            saida.append((float(q), float(u), c))
    return saida


def estatisticas(pares: list[dict], campo_de) -> dict:
    """Erros em pontos dos válidos: por candidatura e nas diferenças de posição."""
    por_cand: list[float] = []
    competitivas: list[float] = []
    por_campo: dict[str, list[float]] = defaultdict(list)
    dif_23: list[float] = []
    dif_12: list[float] = []
    for p in pares:
        itens = _comparaveis(p)
        for q, u, c in itens:
            por_cand.append(q - u)
            por_campo[campo_de(c["partido"])].append(q - u)
            if 20 <= u <= 40:
                competitivas.append(q - u)
        ordem = sorted(itens, key=lambda t: -t[1])
        if len(ordem) >= 3:
            (_, _, _), (q2, u2, _), (q3, u3, _) = ordem[:3]
            dif_23.append((q2 - q3) - (u2 - u3))
        if len(ordem) >= 2:
            (q1, u1, _), (q2, u2, _) = ordem[:2]
            dif_12.append((q1 - q2) - (u1 - u2))
    return {
        "por_candidatura": _resumo(por_cand),
        "candidaturas_entre_20_e_40_pct": _resumo(competitivas),
        "diferenca_2o_3o": _resumo(dif_23),
        "diferenca_1o_2o": _resumo(dif_12),
        "por_campo": {k: _resumo(v) for k, v in sorted(por_campo.items())},
    }


def _itens_log(p: dict, minimo: float, deff: float) -> list[dict]:
    """Candidaturas acima dos limiares, com o log-erro e a variância amostral."""
    n = p["n"] or 0
    if n <= 0:
        return []
    n_ef = n / deff
    itens = []
    for q, u, c in _comparaveis(p):
        if q / 100 < minimo or u / 100 < MIN_VALIDO_URNA:
            continue
        frac_total = max(float(c["pesquisa_pct_total"]) / 100, 1e-6)
        itens.append(
            {
                "d": math.log(u / q),
                "v": 1 / (n_ef * frac_total),
                "partido": c["partido"],
            }
        )
    return itens


def variancia_log(
    pares: list[dict], campo_de, *, minimo: float = MIN_VALIDO_POLL, deff=DEFF
) -> dict:
    """Variância não amostral do log das frações, líquida da amostragem.

    Para cada pesquisa, d_i = log(urna_i) - log(pesquisa_i) nos válidos, só
    entre candidaturas acima dos limiares. Centrar d dentro da pesquisa elimina
    a constante da renormalização (o softmax é invariante a ela). A esperança
    da soma dos quadrados centrados é (1 - 1/K) vezes a soma das variâncias;
    a parte amostral de cada termo é 1 / (n_ef * fração no total de
    entrevistados), a variância do log-razão multinomial.

    Decomposição: o efeito de campo comum aos estados (média dos resíduos
    centrados por campo, descontado o ruído da própria média), o efeito de
    campo dentro do estado (covariância entre pares do mesmo campo na mesma
    pesquisa menos a covariância entre pares de campos diferentes) e o resto,
    idiossincrático.
    """
    soma_q, soma_amostral, soma_k = 0.0, 0.0, 0
    centrados: list[list[tuple[str, float]]] = []
    for p in pares:
        itens = _itens_log(p, minimo, deff)
        k = len(itens)
        if k < 2:
            continue
        media = sum(i["d"] for i in itens) / k
        soma_q += sum((i["d"] - media) ** 2 for i in itens)
        soma_amostral += (1 - 1 / k) * sum(i["v"] for i in itens)
        soma_k += k - 1
        centrados.append([(campo_de(i["partido"]), i["d"] - media) for i in itens])
    if soma_k == 0:
        return {}
    total = soma_q / soma_k
    amostral = soma_amostral / soma_k
    nao_amostral = max(0.0, total - amostral)
    por_campo: dict[str, list[float]] = defaultdict(list)
    for linha in centrados:
        for campo, e in linha:
            por_campo[campo].append(e)
    medias = {k: sum(v) / len(v) for k, v in por_campo.items() if len(v) >= 3}
    nacional = 0.0
    if len(medias) >= 2:
        m = sum(medias.values()) / len(medias)
        var_medias = sum((x - m) ** 2 for x in medias.values()) / (len(medias) - 1)
        ruido = sum(total / len(por_campo[k]) for k in medias) / len(medias)
        nacional = max(0.0, var_medias - ruido)
    mesmo, diferente = [], []
    for linha in centrados:
        resid = [(c, e - medias.get(c, 0.0)) for c, e in linha]
        for a in range(len(resid)):
            for b in range(a + 1, len(resid)):
                prod = resid[a][1] * resid[b][1]
                igual = resid[a][0] == resid[b][0] and resid[a][0] != "indefinido"
                (mesmo if igual else diferente).append(prod)
    cov_mesmo = sum(mesmo) / len(mesmo) if mesmo else None
    cov_dif = sum(diferente) / len(diferente) if diferente else None
    estado_campo = (
        max(0.0, cov_mesmo - cov_dif)
        if cov_mesmo is not None and cov_dif is not None
        else None
    )
    return {
        "limiar_validos_pesquisa": minimo,
        "pesquisas": len(centrados),
        "graus_de_liberdade": soma_k,
        "var_total_log": total,
        "var_amostral_log": amostral,
        "var_nao_amostral_log": nao_amostral,
        "efeito_campo_medio_log": {k: medias[k] for k in sorted(medias)},
        "n_por_campo": {k: len(v) for k, v in sorted(por_campo.items())},
        "var_campo_nacional_log": nacional,
        "pares_mesmo_campo": len(mesmo),
        "cov_mesmo_campo_log": cov_mesmo,
        "cov_campos_diferentes_log": cov_dif,
        "var_campo_estadual_log": estado_campo,
    }


def deriva(linhas_por_uf: dict[str, list[dict]], *, minimo=0.10, deff=DEFF) -> dict:
    """Variância por dia do passeio aleatório, de ondas seguidas da mesma casa.

    Para cada par de ondas consecutivas da mesma casa e estado com campo entre
    01/09/2022 e a eleição, mede a variação do log das frações nos válidos
    (centrada, só candidaturas acima de `minimo` nas duas), desconta a parte
    amostral das duas ondas e divide pelos dias entre os pontos médios.
    """
    soma_liq, soma_peso, pares = 0.0, 0.0, []
    inicio = date(2022, 9, 1)
    for uf, linhas in sorted(linhas_por_uf.items()):
        por_casa: dict[str, list[dict]] = defaultdict(list)
        for p in linhas:
            ini = date.fromisoformat(p["campo_inicio"])
            fim = date.fromisoformat(p["campo_fim"])
            if ini >= inicio and fim < ELEICAO_2022 and p["n"]:
                por_casa[p["casa"]].append(p)
        for casa, ondas in por_casa.items():
            ondas.sort(key=lambda p: p["campo_fim"])
            for a, b in pairwise(ondas):
                ma, mb = _meio(a), _meio(b)
                dt = (mb - ma).days if ma and mb else 0
                if dt < 3:
                    continue
                va = _fracoes(a)
                vb = _fracoes(b)
                comuns = [
                    k
                    for k in va
                    if k in vb and va[k][0] >= minimo and vb[k][0] >= minimo
                ]
                k = len(comuns)
                if k < 2:
                    continue
                d = [math.log(vb[x][0] / va[x][0]) for x in comuns]
                m = sum(d) / k
                ss = sum((x - m) ** 2 for x in d)
                amostral = (1 - 1 / k) * sum(
                    deff / (a["n"] * va[x][1]) + deff / (b["n"] * vb[x][1])
                    for x in comuns
                )
                soma_liq += ss - amostral
                soma_peso += (k - 1) * dt
                pares.append(
                    {
                        "uf": uf,
                        "casa": casa,
                        "de": a["campo_fim"],
                        "para": b["campo_fim"],
                        "dias": dt,
                        "candidaturas": k,
                    }
                )
    tau2 = max(0.0, soma_liq / soma_peso) if soma_peso else None
    return {"var_por_dia_log": tau2, "pares_de_ondas": len(pares), "pares": pares}


def _meio(p: dict) -> date | None:
    try:
        a = date.fromisoformat(p["campo_inicio"]).toordinal()
        b = date.fromisoformat(p["campo_fim"]).toordinal()
    except (TypeError, ValueError):
        return None
    return date.fromordinal((a + b) // 2)


def _fracoes(p: dict) -> dict[str, tuple[float, float]]:
    """Rótulo -> (fração nos válidos, fração no total) de uma onda da tabela."""
    nomeados = [c for c in p["candidatos"] if c["valor"] is not None]
    soma = sum(c["valor"] for c in nomeados) + p["outros"]
    if soma <= 0:
        return {}
    return {
        f"{c['rotulo']}|{chave_partido(c['partido'])}": (
            c["valor"] / soma,
            max(c["valor"] / 100, 1e-6),
        )
        for c in nomeados
        if c["valor"] > 0
    }


def calibrar(
    urna: dict,
    paginas: dict[str, str],
    campo_de,
    fontes: dict,
    *,
    padrao: str = "senad",
    modelos: frozenset[str] = frozenset({"SP"}),
    cargo: str = "5",
) -> dict:
    """Junta tudo: pares, estatísticas, variâncias e deriva. `modelos` são as
    UFs cujo arquivo é a predefinição com a tabela, sem seções."""
    todas, principais, por_uf, linhas_uf = [], [], {}, {}
    for uf, texto in sorted(paginas.items()):
        linhas = pesquisas_wiki(texto, modelo=uf in modelos, padrao=padrao)
        linhas_uf[uf] = linhas
        pares = pares_estado(uf, linhas, urna.get(uf, []))
        por_uf[uf] = {
            "linhas_na_tabela": len(linhas),
            "pesquisas_finais": len(pares),
            "casas_principais": sorted(
                p["casa"] for p in pares if p["casa"] in CASAS_PRINCIPAIS
            ),
            "nao_casadas": sorted(
                {
                    c["rotulo"]
                    for p in pares
                    for c in p["candidatos"]
                    if c["sq_candidato"] is None
                }
            ),
        }
        todas.extend(pares)
        principais.extend(p for p in pares if p["casa"] in CASAS_PRINCIPAIS)
    estados = sorted({p["uf"] for p in principais})
    dias = [p["dias_ate_eleicao"] for p in principais]
    return {
        "fontes_wikipedia": [fontes[uf] for uf in sorted(fontes)],
        "fonte_urna": {
            "arquivo": str(URNA_ZIP.relative_to(ROOT)),
            "regra": f"cargo {cargo}, 1º turno, soma de QT_VOTOS_NOMINAIS_VALIDOS por SQ",
        },
        "janela": {
            "campo_fim_minimo": CORTE_2022.isoformat(),
            "eleicao": ELEICAO_2022.isoformat(),
            "casas_principais": list(CASAS_PRINCIPAIS),
            "regra": "uma onda por casa e estado, a de campo mais recente",
            "deff": DEFF,
        },
        "cobertura": {
            "estados_casas_principais": estados,
            "n_estados_casas_principais": len(estados),
            "n_pesquisas_casas_principais": len(principais),
            "n_estados_todas_as_casas": len({p["uf"] for p in todas}),
            "n_pesquisas_todas_as_casas": len(todas),
            "por_uf": por_uf,
        },
        "estatisticas": {
            "casas_principais": estatisticas(principais, campo_de),
            "todas_as_casas": estatisticas(todas, campo_de),
        },
        "variancia_log": {
            "casas_principais": variancia_log(principais, campo_de),
            "casas_principais_competitivas": variancia_log(
                principais, campo_de, minimo=0.10
            ),
            "todas_as_casas": variancia_log(todas, campo_de),
        },
        "deriva": deriva(linhas_uf),
        "dias_ate_eleicao_medio": sum(dias) / len(dias) if dias else None,
        "pares": todas,
        "urna": urna,
    }


def ler(caminho: Path = SAIDA) -> dict | None:
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))
