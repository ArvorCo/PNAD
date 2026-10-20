"""Cliente da Open-Meteo com lotes de coordenadas, cota e retomada.

A API aceita listas em ``latitude`` e ``longitude`` e devolve uma lista de respostas na
mesma ordem; cada coordenada conta como uma chamada na cota (cerca de 600 por minuto,
5 mil por hora e 10 mil por dia no plano gratuito). O cliente anda abaixo do limite por
minuto, espera em 429 o que o cabeçalho pedir (ou 60 s, depois 15 min se repetir) e
para quando a resposta diz que a cota do dia acabou, sem perder o que já gravou.

Toda requisição fica registrada (horário, URL, situação, coordenadas) num arquivo JSONL.
Só a biblioteca padrão: o mesmo cliente roda no workflow da previsão sem instalar nada.
"""

from __future__ import annotations

import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from clima_1t.grade import arquivo_da_chave

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
FORECAST = "https://api.open-meteo.com/v1/forecast"
UA = "Mozilla/5.0 (compatible; brasil-arvor-clima/1.0)"
POR_MINUTO = 500  # abaixo dos 600 por minuto da cota gratuita
ESPERA_PADRAO = 60
ESPERA_REPETIDA = 15 * 60


class CotaDiariaEsgotada(RuntimeError):
    """A API respondeu que a cota do dia acabou."""


class PrazoEsgotado(RuntimeError):
    """A próxima espera passaria do prazo dado ao cliente."""


class Requisitante(Protocol):
    """O que ``baixar_lotes`` usa do cliente (permite um cliente falso nos testes)."""

    def get(self, base: str, params: dict[str, Any], locais: int = 1) -> Any: ...

    def avisar(self, texto: str) -> None: ...


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class Cliente:
    """GET com ritmo, espera em 429 e registro de cada URL."""

    registro: Path | None = None
    por_minuto: int = POR_MINUTO
    dormir: Callable[[float], None] = time.sleep
    imprimir: Callable[[str], None] = print
    prazo: float | None = None  # instante (time.monotonic) a partir do qual desiste
    _proxima: float = field(default=0.0, init=False)
    chamadas: int = field(default=0, init=False)

    def avisar(self, texto: str) -> None:
        self.imprimir(texto)

    def _anotar(self, item: dict[str, Any]) -> None:
        if self.registro is None:
            return
        self.registro.parent.mkdir(parents=True, exist_ok=True)
        with self.registro.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def _ritmo(self, locais: int) -> None:
        espera = self._proxima - time.monotonic()
        if espera > 0:
            self.dormir(espera)
        self._proxima = time.monotonic() + 60.0 * locais / self.por_minuto

    def get(self, base: str, params: dict[str, Any], locais: int = 1) -> Any:
        """Devolve o JSON da resposta; levanta ``CotaDiariaEsgotada`` se a cota acabou."""
        url = base + "?" + urllib.parse.urlencode(params, safe=",:")
        repetidas = 0
        falhas = 0
        while True:
            self._ritmo(locais)
            pedido = urllib.request.Request(url, headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(pedido, timeout=180) as r:
                    corpo = r.read()
                self.chamadas += locais
                dados = json.loads(corpo)
                self._anotar(
                    {"horario": agora(), "url": url, "status": 200, "locais": locais}
                )
                return dados
            except urllib.error.HTTPError as e:
                corpo = e.read().decode("utf-8", "replace")[:300]
                self._anotar(
                    {
                        "horario": agora(),
                        "url": url,
                        "status": e.code,
                        "locais": locais,
                        "motivo": corpo,
                    }
                )
                if e.code == 429:
                    if "daily" in corpo.lower():
                        raise CotaDiariaEsgotada(corpo) from e
                    pedido_espera = e.headers.get("Retry-After")
                    espera = (
                        float(pedido_espera)
                        if pedido_espera and pedido_espera.isdigit()
                        else ESPERA_PADRAO
                    )
                    if repetidas:
                        espera = max(espera, ESPERA_REPETIDA)
                    repetidas += 1
                    if (
                        self.prazo is not None
                        and time.monotonic() + espera > self.prazo
                    ):
                        raise PrazoEsgotado(corpo) from e
                    self.avisar(f"429 ({corpo.strip()[:120]}); espera {espera:.0f} s")
                    self.dormir(espera)
                    continue
                if e.code >= 500 and falhas < 5:
                    falhas += 1
                    self.dormir(10 * 2**falhas)
                    continue
                raise
            except (
                urllib.error.URLError,
                http.client.HTTPException,
                json.JSONDecodeError,
                TimeoutError,
                ConnectionError,
            ) as e:
                self._anotar(
                    {
                        "horario": agora(),
                        "url": url,
                        "status": None,
                        "locais": locais,
                        "motivo": str(e)[:300],
                    }
                )
                if falhas >= 6:
                    raise
                falhas += 1
                self.dormir(10 * 2**falhas)


def _coord(x: float) -> str:
    return f"{x:.4f}".rstrip("0").rstrip(".")


def params_lote(base: dict[str, Any], pontos: list[tuple[float, float]]) -> dict:
    return {
        **base,
        "latitude": ",".join(_coord(a) for a, _ in pontos),
        "longitude": ",".join(_coord(b) for _, b in pontos),
    }


def baixar_lotes(
    cliente: Requisitante,
    url_base: str,
    params_base: dict[str, Any],
    celulas: dict[str, tuple[float, float]],
    lote: int,
    gravar: Callable[[str, dict[str, Any], str, int], None],
    pular: Iterable[str] = (),
    tolerancia_graus: float = 0.3,
) -> dict[str, Any]:
    """Baixa as células pendentes em lotes; ``gravar(chave, resposta, url, posição)``.

    Confere que cada resposta caiu perto do ponto pedido (a ordem da lista é a do
    pedido) e para sem erro quando a cota do dia acaba.
    """
    feitas = set(pular)
    pendentes = [c for c in celulas if c not in feitas]
    baixadas = 0
    parada = None
    for ini in range(0, len(pendentes), lote):
        grupo = pendentes[ini : ini + lote]
        pontos = [celulas[c] for c in grupo]
        params = params_lote(params_base, pontos)
        try:
            resp = cliente.get(url_base, params, locais=len(grupo))
        except CotaDiariaEsgotada as e:
            parada = f"cota diária esgotada: {str(e)[:200]}"
            break
        except PrazoEsgotado as e:
            parada = f"prazo esgotado esperando a cota: {str(e)[:200]}"
            break
        lista = resp if isinstance(resp, list) else [resp]
        if len(lista) != len(grupo):
            raise RuntimeError(f"lote com {len(grupo)} pontos devolveu {len(lista)}")
        url = url_base + "?" + urllib.parse.urlencode(params, safe=",:")
        for pos, (c, item) in enumerate(zip(grupo, lista, strict=True)):
            lat, lon = celulas[c]
            if (
                abs(item.get("latitude", 999) - lat) > tolerancia_graus
                or abs(item.get("longitude", 999) - lon) > tolerancia_graus
            ):
                raise RuntimeError(f"resposta fora do ponto pedido na célula {c}")
            gravar(c, item, url, pos)
        baixadas += len(grupo)
        cliente.avisar(f"  {ini + len(grupo)}/{len(pendentes)} células")
    return {
        "pendentes_no_inicio": len(pendentes),
        "baixadas": baixadas,
        "parada": parada,
    }


# --- Arquivo observado (ERA5/ERA5-Land) -------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
RAW_ARCHIVE = ROOT / "data/originals/clima_1t_2026/archive"
REGISTRO_ARCHIVE = ROOT / "data/originals/clima_1t_2026/archive_requisicoes.jsonl"
CONSOLIDADO = ROOT / "analysis/clima_1t_2026/celulas_archive.json"
REQUISICOES = ROOT / "analysis/clima_1t_2026/requisicoes_archive.json"
INICIO, FIM, DIA = "2026-10-02", "2026-10-05", "2026-10-04"
DIARIAS = [
    "precipitation_sum",
    "precipitation_hours",
    "wind_gusts_10m_max",
    "temperature_2m_max",
]
HORARIAS = ["precipitation", "wind_gusts_10m"]
PARAMS_ARCHIVE = {
    "start_date": INICIO,
    "end_date": FIM,
    "daily": ",".join(DIARIAS),
    "hourly": ",".join(HORARIAS),
    "timezone": "America/Sao_Paulo",
}


def _gravar_archive(chave_cel: str, item: dict, url: str, pos: int) -> None:
    destino = RAW_ARCHIVE / arquivo_da_chave(chave_cel)
    doc = {
        "coletado_em": agora(),
        "celula": chave_cel,
        "url": url,
        "posicao_no_lote": pos,
        "resposta": item,
    }
    destino.write_text(json.dumps(doc, ensure_ascii=False))


def ja_baixadas(celulas: dict[str, tuple[float, float]]) -> list[str]:
    return [c for c in celulas if (RAW_ARCHIVE / arquivo_da_chave(c)).exists()]


def coletar_archive(
    celulas: dict[str, tuple[float, float]], lote: int = 100
) -> dict[str, Any]:
    """Baixa o que falta do arquivo observado; retomável."""
    RAW_ARCHIVE.mkdir(parents=True, exist_ok=True)
    cliente = Cliente(registro=REGISTRO_ARCHIVE)
    feitas = ja_baixadas(celulas)
    cliente.avisar(f"{len(celulas) - len(feitas)} de {len(celulas)} células a baixar")
    estado = baixar_lotes(
        cliente, ARCHIVE, PARAMS_ARCHIVE, celulas, lote, _gravar_archive, pular=feitas
    )
    estado["chamadas_nesta_execucao"] = cliente.chamadas
    return estado


def _resumir_resposta(r: dict) -> dict[str, Any]:
    d, h = r.get("daily", {}), r.get("hourly", {})
    horas = h.get("time", [])
    idx = [i for i, t in enumerate(horas) if t.startswith(DIA)]
    return {
        "g": [r.get("latitude"), r.get("longitude"), r.get("elevation")],
        "d": {v: d.get(v) for v in DIARIAS},
        "h": {v: [h.get(v, [None] * len(horas))[i] for i in idx] for v in HORARIAS},
        "dias": d.get("time"),
        "horas": [horas[i][11:13] for i in idx],
    }


def _repetidas(requisicoes: list[dict[str, Any]]) -> int:
    vistas: dict[str, int] = {}
    for q in requisicoes:
        if q.get("status") == 200:
            vistas[q["url"]] = vistas.get(q["url"], 0) + 1
    return sum(n - 1 for n in vistas.values())


def consolidar_archive(celulas: dict[str, tuple[float, float]]) -> dict[str, Any]:
    """Junta as respostas cruas num JSON compacto com a cobertura declarada."""
    saida: dict[str, Any] = {}
    faltando: list[str] = []
    dias_ref: list[str] | None = None
    horas_ref: list[str] | None = None
    nulos = 0
    for c in celulas:
        arq = RAW_ARCHIVE / arquivo_da_chave(c)
        if not arq.exists():
            faltando.append(c)
            continue
        cru = json.loads(arq.read_text())
        r = _resumir_resposta(cru["resposta"])
        if dias_ref is None:
            dias_ref, horas_ref = r["dias"], r["horas"]
        if r["dias"] != dias_ref or r["horas"] != horas_ref:
            raise RuntimeError(f"grade temporal diferente na célula {c}")
        nulos += sum(v is None for vs in r["d"].values() for v in (vs or [None]))
        nulos += sum(v is None for vs in r["h"].values() for v in vs)
        saida[c] = [r["g"], [r["d"][v] for v in DIARIAS], [r["h"][v] for v in HORARIAS]]
    requisicoes = []
    if REGISTRO_ARCHIVE.exists():
        for linha in REGISTRO_ARCHIVE.read_text().splitlines():
            requisicoes.append(json.loads(linha))
    doc = {
        "gerado_em": agora(),
        "fonte": {
            "nome": "Open-Meteo Historical Weather API (reanálise ERA5 e ERA5-Land)",
            "url": ARCHIVE,
            "parametros": PARAMS_ARCHIVE,
            "ponto": "centro da célula de 0,25°; a API devolve o ponto de grade usado",
            "registro_de_urls": str(REQUISICOES.relative_to(ROOT)),
        },
        "celula_graus": 0.25,
        "dias": dias_ref,
        "horas_04_10": horas_ref,
        "formato": {
            "celulas": "chave -> [[lat_grade, lon_grade, elevacao_m], "
            "[diarias na ordem de 'diarias', 4 dias cada], "
            "[horarias de 04/10 na ordem de 'horarias', 24 horas de Brasília cada]]",
            "diarias": DIARIAS,
            "horarias": HORARIAS,
            "convencao_horaria": "valor na hora H soma (chuva) ou máximo (rajada) "
            "da hora anterior, H-1 a H, no relógio de Brasília",
        },
        "cobertura": {
            "celulas": len(celulas),
            "coletadas": len(saida),
            "faltando": len(faltando),
            "faltando_chaves": faltando,
            "valores_nulos": nulos,
            "completa": not faltando,
            "requisicoes": len(requisicoes),
            "requisicoes_ok": sum(1 for q in requisicoes if q.get("status") == 200),
            "requisicoes_429": sum(1 for q in requisicoes if q.get("status") == 429),
            "urls_repetidas_apos_200": _repetidas(requisicoes),
            "nota_repeticao": "uma URL com status 200 repetida é resposta truncada que o "
            "cliente baixou de novo (até a correção de 20/10 o registro anotava 200 antes "
            "de ler o corpo)",
        },
        "celulas": saida,
    }
    CONSOLIDADO.parent.mkdir(parents=True, exist_ok=True)
    CONSOLIDADO.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")))
    REQUISICOES.write_text(
        json.dumps(
            {"gerado_em": agora(), "requisicoes": requisicoes},
            ensure_ascii=False,
            indent=0,
        )
    )
    return doc
