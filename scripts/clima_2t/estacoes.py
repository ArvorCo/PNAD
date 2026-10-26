"""Coleta de chuva medida em estações (CEMADEN e INMET) para 25/10/2026.

CEMADEN: o catálogo vem da camada pública do mapa interativo
(``resources.cemaden.gov.br/dados/311_24.json``, com coordenadas) e a série horária de cada
estação vem do serviço que o próprio gráfico da estação consome
(``mapservices.cemaden.gov.br/MapaInterativoWS/resources/horario/<id>/<horas-1>``), que só
alcança as últimas 96 horas. A consulta por período do CEMADEN exige captcha e não é usada.

INMET: o catálogo ``apitempo.inmet.gov.br/estacoes/T`` responde; a rota pública por estação
devolve 204 para qualquer data, e a tabela do site busca os dados por POST com reCAPTCHA
(``/estacao/front/``). Não contornamos captcha: a coleta INMET só registra a tentativa.

Toda requisição fica num JSONL; respostas cruas em ``data/originals/clima_2t_2026/``.
Só biblioteca padrão. Retomável: estação com resposta válida gravada não é pedida de novo.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/originals/clima_2t_2026"
FONTES = ROOT / "analysis/clima_2t_2026/fontes"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
)
CEMADEN_CATALOGO = "https://resources.cemaden.gov.br/dados/311_24.json"
CEMADEN_HORARIO = (
    "https://mapservices.cemaden.gov.br/MapaInterativoWS/resources/horario"
)
CEMADEN_REFERER = (
    "https://resources.cemaden.gov.br/graficos/interativo/grafico_pcds.php"
)
INMET_CATALOGO = "https://apitempo.inmet.gov.br/estacoes/T"
INMET_ESTACAO = "https://apitempo.inmet.gov.br/estacao"
# Votação de 25/10: 08h às 17h de Brasília; janela de análise 07h às 18h = 10h a 21h UTC.
INICIO_UTC = datetime(2026, 10, 25, 10, tzinfo=timezone.utc)
FIM_UTC = datetime(2026, 10, 25, 21, tzinfo=timezone.utc)
HORAS_MAX = 96  # o serviço do gráfico só alcança 96 horas


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def baixar(
    url: str, headers: dict[str, str] | None = None, timeout: int = 60
) -> tuple[int | None, bytes, str]:
    """GET simples; devolve (status, corpo, erro)."""
    pedido = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as r:
            return r.status, r.read(), ""
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:2000], str(e)
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        return None, b"", str(e)[:300]


def anotar(registro: Path, item: dict[str, Any]) -> None:
    registro.parent.mkdir(parents=True, exist_ok=True)
    with registro.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def jsonp(texto: str) -> Any:
    """Tira o embrulho ``estacoes(...)`` da camada do mapa."""
    return json.loads(texto[texto.index("(") + 1 : texto.rindex(")")])


def arquivar_fonte(nome: str, corpo: bytes, url: str, status: int | None) -> dict:
    """Guarda catálogo ou amostra em ``analysis/clima_2t_2026/fontes`` com SHA-256."""
    FONTES.mkdir(parents=True, exist_ok=True)
    (FONTES / nome).write_bytes(corpo)
    meta = {
        "arquivo": nome,
        "url": url,
        "status": status,
        "bytes": len(corpo),
        "sha256": sha256(corpo),
        "baixado_em": agora(),
    }
    manifesto = FONTES / "manifesto.json"
    itens = json.loads(manifesto.read_text()) if manifesto.exists() else []
    itens = [i for i in itens if i["arquivo"] != nome] + [meta]
    manifesto.write_text(json.dumps(itens, ensure_ascii=False, indent=1))
    return meta


# --- CEMADEN ---------------------------------------------------------------------


def catalogo_cemaden(baixar_de_novo: bool = False) -> list[dict[str, Any]]:
    destino = FONTES / "cemaden_catalogo_311_24.jsonp"
    if baixar_de_novo or not destino.exists():
        st, corpo, erro = baixar(CEMADEN_CATALOGO)
        if st != 200:
            raise RuntimeError(f"catálogo CEMADEN: {st} {erro}")
        arquivar_fonte(destino.name, corpo, CEMADEN_CATALOGO, st)
    doc = jsonp(destino.read_text(encoding="utf-8"))
    return [e for e in doc[0]["estacao"] if e.get("latitude") is not None]


def horas_pedidas(agora_utc: datetime | None = None) -> int:
    """Horas para trás que alcançam 25/10 10h UTC, no máximo do serviço."""
    t = agora_utc or datetime.now(timezone.utc)
    precisa = int((t - INICIO_UTC).total_seconds() // 3600) + 3
    if precisa > HORAS_MAX:
        raise RuntimeError("o serviço horário do CEMADEN já não alcança 25/10 10h UTC")
    return max(precisa, 36)


def resposta_valida(dados: Any) -> bool:
    return (
        isinstance(dados, dict)
        and isinstance(dados.get("datas"), list)
        and isinstance(dados.get("horarios"), list)
        and isinstance(dados.get("acumulados"), list)
    )


def coletar_cemaden(
    pausa: float = 0.25,
    espera_503: float = 120.0,
    imprimir: Callable[[str], None] = print,
) -> dict[str, Any]:
    """Baixa a série horária de cada estação que ainda não tem resposta válida."""
    pasta = RAW / "cemaden"
    pasta.mkdir(parents=True, exist_ok=True)
    registro = RAW / "cemaden_requisicoes.jsonl"
    estacoes = catalogo_cemaden()
    pendentes = [e for e in estacoes if not (pasta / f"{e['idestacao']}.json").exists()]
    imprimir(f"{len(pendentes)} de {len(estacoes)} estações CEMADEN a baixar")
    feitas = falhas = 0
    seguidas_503 = 0
    for e in pendentes:
        horas = horas_pedidas()
        url = f"{CEMADEN_HORARIO}/{e['idestacao']}/{horas - 1}"
        while True:
            st, corpo, erro = baixar(
                url, {"Referer": f"{CEMADEN_REFERER}?idpcd={e['idestacao']}"}
            )
            anotar(
                registro,
                {
                    "horario": agora(),
                    "url": url,
                    "status": st,
                    "bytes": len(corpo),
                    "erro": erro[:200],
                },
            )
            if st in (502, 503, 504, None, 429):
                seguidas_503 += 1
                espera = min(espera_503 * (1 + seguidas_503 // 5), 900)
                imprimir(f"{st} em {e['idestacao']}; espera {espera:.0f} s")
                time.sleep(espera)
                horas = horas_pedidas()
                url = f"{CEMADEN_HORARIO}/{e['idestacao']}/{horas - 1}"
                continue
            seguidas_503 = 0
            break
        dados: Any = None
        if st == 200:
            try:
                dados = json.loads(corpo)
            except json.JSONDecodeError:
                dados = None
        if resposta_valida(dados):
            doc = {"coletado_em": agora(), "url": url, "estacao": e, "resposta": dados}
            (pasta / f"{e['idestacao']}.json").write_text(
                json.dumps(doc, ensure_ascii=False)
            )
            feitas += 1
        else:
            falhas += 1
        if (feitas + falhas) % 100 == 0:
            imprimir(f"  {feitas + falhas}/{len(pendentes)} (válidas {feitas})")
        time.sleep(pausa)
    return {"pendentes": len(pendentes), "validas": feitas, "falhas": falhas}


# --- INMET -----------------------------------------------------------------------


def testar_inmet(amostra: int = 5) -> dict[str, Any]:
    """Arquiva o catálogo e registra o que a rota pública devolve para 25/10."""
    st, corpo, erro = baixar(
        INMET_CATALOGO,
        {
            "Origin": "https://tempo.inmet.gov.br",
            "Referer": "https://tempo.inmet.gov.br/",
        },
    )
    if st != 200:
        return {"catalogo": st, "erro": erro}
    arquivar_fonte("inmet_catalogo_T.json", corpo, INMET_CATALOGO, st)
    estacoes = json.loads(corpo)
    tentativas = []
    for e in [x for x in estacoes if x.get("CD_SITUACAO") == "Operante"][:amostra]:
        url = f"{INMET_ESTACAO}/2026-10-25/2026-10-25/{e['CD_ESTACAO']}"
        st2, corpo2, erro2 = baixar(
            url,
            {
                "Origin": "https://tempo.inmet.gov.br",
                "Referer": "https://tempo.inmet.gov.br/",
                "Accept": "application/json, text/plain, */*",
            },
        )
        tentativas.append(
            {
                "url": url,
                "status": st2,
                "bytes": len(corpo2),
                "erro": erro2[:200],
                "horario": agora(),
            }
        )
    return {
        "catalogo_estacoes": len(estacoes),
        "automaticas_operantes": sum(
            1 for x in estacoes if x.get("CD_SITUACAO") == "Operante"
        ),
        "tentativas_25_10": tentativas,
        "nota": "a rota pública devolve 204 sem corpo (também para 2025); a tabela do site "
        "busca os dados por POST em /estacao/front/ com token reCAPTCHA, que não usamos; o "
        "arquivo anual de dados históricos (portal.inmet.gov.br/uploads/dadoshistoricos/"
        "2026.zip) foi modificado em 05/10/2026 e não chega a 25/10",
    }


# --- CEMADEN, acumulados da tabela das estações -------------------------------------

CEMADEN_TABELA = "https://resources.cemaden.gov.br/graficos/interativo/getJson2.php"
UFS = [
    "AC",
    "AL",
    "AM",
    "AP",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MG",
    "MS",
    "MT",
    "PA",
    "PB",
    "PE",
    "PI",
    "PR",
    "RJ",
    "RN",
    "RO",
    "RR",
    "RS",
    "SC",
    "SE",
    "SP",
    "TO",
]


def foto_acumulados(rotulo: str) -> dict[str, Any]:
    """Grava a tabela de acumulados (1 a 96 h) de todas as UFs num instante.

    A diferença ``acc48hr - acc24hr`` numa foto tirada às 03h UTC de 27/10 é a chuva de
    25/10 das 00h às 24h de Brasília; ``acc72hr - acc48hr`` às 03h UTC de 28/10 dá o
    mesmo dia (conferência). É total diário, não as horas da votação.
    """
    pasta = RAW / "cemaden_acumulados" / rotulo
    pasta.mkdir(parents=True, exist_ok=True)
    resumo: dict[str, Any] = {"rotulo": rotulo, "inicio": agora(), "ufs": {}}
    for uf in UFS:
        url = f"{CEMADEN_TABELA}?uf={uf}"
        for tentativa in range(4):
            st, corpo, erro = baixar(url)
            if st == 200:
                break
            time.sleep(20 * (tentativa + 1))
        (pasta / f"{uf}.json").write_bytes(corpo)
        resumo["ufs"][uf] = {
            "status": st,
            "bytes": len(corpo),
            "sha256": sha256(corpo),
            "erro": erro[:200],
        }
    resumo["fim"] = agora()
    (pasta / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=1))
    return resumo
