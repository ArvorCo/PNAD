#!/usr/bin/env python3
"""Gera os clipes e stills do vídeo masterclass pelo ``openclaw`` e normaliza com ffmpeg.

Lê ``video/masterclass/midia/manifesto.json`` (contrato, seção 4), guarda o estado em
``midia/cache.json`` e o resultado da sondagem em ``midia/sondagem.json``, grava
``public/midia/<id>_<fmt>.mp4|png`` (1920x1080 ou 1080x1920, 30 fps, h264 crf 18,
yuv420p, sem áudio) e escreve ``src/dados/midia.json`` ao fim de toda execução.

Uso:
    python3 scripts/video-masterclass-midia.py --sondar [--dir-sonda DIR]
    python3 scripts/video-masterclass-midia.py                  # gera o que falta
    python3 scripts/video-masterclass-midia.py --imagens        # só os stills
    python3 scripts/video-masterclass-midia.py --videos --formato 16x9
    python3 scripts/video-masterclass-midia.py --so sopa_panela --forcar
    python3 scripts/video-masterclass-midia.py --faltando       # prompts para colar à mão
    python3 scripts/video-masterclass-midia.py --absorver       # normaliza midia/entrada/
    python3 scripts/video-masterclass-midia.py --recortar       # 9x16 pelo centro do 16x9

Item que nenhum provedor gera fica com ``origem: manual`` e ``estado: pendente`` no
cache, com o texto do erro (sem segredos). O arquivo feito à mão entra em
``midia/entrada/<id>_<fmt>.<ext>`` e ``--absorver`` o normaliza.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PROJETO = RAIZ / "video" / "masterclass"
MIDIA = PROJETO / "midia"
MANIFESTO = MIDIA / "manifesto.json"
CACHE = MIDIA / "cache.json"
SONDAGEM = MIDIA / "sondagem.json"
ENTRADA = MIDIA / "entrada"
BRUTOS = MIDIA / "brutos"
PUBLICO = PROJETO / "public" / "midia"
SAIDA_DADOS = PROJETO / "src" / "dados" / "midia.json"

FORMATOS = ("16x9", "9x16")
DIMENSOES = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
PROPORCAO = {"16x9": "16:9", "9x16": "9:16"}
EXTENSAO = {"video": ".mp4", "imagem": ".png"}
EXT_ACEITAS = {
    "video": {".mp4", ".mov", ".webm", ".mkv", ".m4v"},
    "imagem": {".png", ".jpg", ".jpeg", ".webp"},
}
MAX_PARALELO = 2
TIMEOUT_MS = 900_000
VALIDADE_SONDAGEM_S = 6 * 3600

# Tamanhos aceitos pela OpenAI (geometria declarada em `openclaw infer ... providers`).
TAMANHO_SORA = {
    "sora-2": {"16x9": "1280x720", "9x16": "720x1280"},
    "sora-2-pro": {"16x9": "1792x1024", "9x16": "1024x1792"},
}
DURACOES_SORA = (4, 8, 12)
DURACOES_VEO = (4, 6, 8)
TAMANHO_GPT_IMAGE = {"16x9": "2048x1152", "9x16": "2160x3840"}

# Ids de cena da seção 1 do contrato.
CENAS_VALIDAS = frozenset(
    {
        "abertura",
        "tese",
        "cap-sopa",
        "sopa-panela",
        "sopa-concha",
        "sopa-regua",
        "sopa-conchas-reais",
        "sopa-moral",
        "cap-urna",
        "urna-resultado",
        "urna-erro",
        "urna-reponderado",
        "urna-efeito-casa",
        "urna-virada",
        "cap-depois",
        "depois-contagem-publica",
        "depois-fiscais",
        "depois-totalizacao",
        "depois-politize",
        "cap-riscos",
        "risco-sinais",
        "risco-pianista",
        "risco-biometria",
        "risco-urna-trocada",
        "risco-horarios",
        "risco-boca-de-urna",
        "risco-territorio",
        "risco-conferir-arquivo",
        "risco-fiscal-fica",
        "cap-mapa",
        "mapa-busca",
        "mapa-predio-rj",
        "mapa-predio-sp",
        "mapa-zoom",
        "cap-fecho",
        "fecho-argentina",
        "fecho-chamada",
    }
)

# Falhas que valem para o provedor inteiro: depois da primeira, ninguém mais tenta nele.
FALHAS_DO_PROVEDOR = frozenset({"cota", "creditos", "indisponivel", "autenticacao"})

PROMPT_SONDA = {
    "video": "A cup of coffee steaming on a wooden table, slow push-in, soft daylight.",
    "imagem": "A cup of coffee on a wooden table, soft daylight, documentary photo.",
}

FERRAMENTAS_MANUAIS = {
    "video": "Gemini web (Veo 3.1), CapCut (Seedance) ou Grok Imagine "
    "(gere o still e anime com o mesmo prompt)",
    "imagem": "Gemini web (Nano Banana Pro), ChatGPT (imagens) ou Grok Imagine",
}

_REDACOES = (
    (re.compile(r"sk-[A-Za-z0-9_\-]{8,}"), "sk-***"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{10,}"), "AIza***"),
    (re.compile(r"(?i)bearer\s+\S+"), "Bearer ***"),
    (re.compile(r"(?i)(key|token|secret)=([^&\s]+)"), r"\1=***"),
)


# ---------------------------------------------------------------- utilidades


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def relativo(caminho: Path) -> str:
    try:
        return str(caminho.resolve().relative_to(RAIZ))
    except ValueError:
        return str(caminho)


def ler_json(caminho: Path, padrao: dict) -> dict:
    if not caminho.exists():
        return padrao
    return json.loads(caminho.read_text(encoding="utf-8"))


def gravar_json(caminho: Path, dados: dict) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_name(caminho.name + ".tmp")
    texto = json.dumps(dados, ensure_ascii=False, indent=2) + "\n"
    temporario.write_text(texto, encoding="utf-8")
    temporario.replace(caminho)


def sha256_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def limpar_erro(texto: str) -> str:
    """Última linha útil do erro, sem segredos e com no máximo 300 caracteres."""
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    uteis = [
        linha
        for linha in linhas
        if not linha.startswith("openclaw infer")
        and "auth selected" not in linha
        and "candidate failed" not in linha
    ]
    escolhida = (uteis or linhas or ["erro sem mensagem"])[-1]
    for padrao, troca in _REDACOES:
        escolhida = padrao.sub(troca, escolhida)
    return escolhida[:300]


def classificar_erro(texto: str) -> str:
    minusculo = texto.lower()
    if "429" in texto or "resource_exhausted" in minusculo or "quota" in minusculo:
        return "cota"
    if "402" in texto or "credits" in minusculo or "billing" in minusculo:
        return "creditos"
    if "401" in texto or "403" in texto or "missing" in minusculo:
        return "autenticacao"
    if "404" in texto or "not supported" in minusculo or "not found" in minusculo:
        return "indisponivel"
    if any(p in minusculo for p in ("policy", "moderation", "safety", "blocked")):
        return "politica"
    if "timeout" in minusculo or "timed out" in minusculo:
        return "tempo"
    return "erro"


def resumo_erro(tipo: str, texto: str) -> str:
    """Forma curta para o cache: classe da falha e código HTTP, se houver."""
    codigo = re.search(r"HTTP (\d{3})|\"code\":\s*(\d{3})", texto)
    if codigo:
        return f"{tipo} (HTTP {codigo.group(1) or codigo.group(2)})"
    return f"{tipo}: {texto[:120]}"


def duracao(caminho: Path) -> float:
    saida = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(caminho),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return round(float(saida), 3) if saida and saida != "N/A" else 0.0


def tem_audio(caminho: Path) -> bool:
    saida = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index",
            "-of",
            "csv=p=0",
            str(caminho),
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return bool(saida)


def normalizar(origem: Path, destino: Path, fmt: str) -> None:
    """Escala cobrindo o quadro, recorta ao centro e grava no padrão do projeto."""
    largura, altura = DIMENSOES[fmt]
    filtro = (
        f"scale={largura}:{altura}:force_original_aspect_ratio=increase"
        f":flags=lanczos,crop={largura}:{altura},setsar=1"
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_name(f"{destino.stem}.tmp{destino.suffix}")
    if destino.suffix == ".mp4":
        comando = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(origem),
            "-vf",
            f"{filtro},fps=30",
            "-c:v",
            "libx264",
            "-preset",
            "slow",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            "-an",
            str(temporario),
        ]
    else:
        comando = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(origem),
            "-vf",
            filtro,
            "-frames:v",
            "1",
            "-update",
            "1",
            str(temporario),
        ]
    subprocess.run(comando, check=True)
    temporario.replace(destino)


def extrair_som(origem: Path, destino_video: Path) -> Path | None:
    if not tem_audio(origem):
        return None
    destino = destino_video.with_name(f"{destino_video.stem}.som.m4a")
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(origem),
            "-vn",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(destino),
        ],
        check=True,
    )
    return destino


# ---------------------------------------------------------------- manifesto


def carregar_manifesto() -> dict:
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8"))
    vistos: set[str] = set()
    problemas: list[str] = []
    for item in manifesto["itens"]:
        ident = item["id"]
        if ident in vistos:
            problemas.append(f"id repetido: {ident}")
        vistos.add(ident)
        if item["tipo"] not in EXTENSAO:
            problemas.append(f"{ident}: tipo desconhecido {item['tipo']}")
        if not set(item["formatos"]) <= set(FORMATOS):
            problemas.append(f"{ident}: formato desconhecido {item['formatos']}")
        desconhecidas = set(item.get("cenas", [])) - CENAS_VALIDAS
        if desconhecidas:
            problemas.append(f"{ident}: cenas fora do contrato {sorted(desconhecidas)}")
        if "\u2014" in json.dumps(item, ensure_ascii=False):
            problemas.append(f"{ident}: travessão no manifesto")
    if problemas:
        raise SystemExit("manifesto inválido:\n  " + "\n  ".join(problemas))
    return manifesto


def prompt_final(manifesto: dict, item: dict, fmt: str) -> str:
    estilo = item.get("estilo", manifesto["estilo"])
    partes = [item["prompt"], manifesto["enquadramento"][fmt], estilo]
    texto = " ".join(parte.strip() for parte in partes if parte and parte.strip())
    negativo = negativo_de(manifesto, item)
    return f"{texto} Avoid: {negativo}." if negativo else texto


def negativo_de(manifesto: dict, item: dict) -> str:
    return item.get("negativo") or manifesto.get("negativo_padrao", "")


def chave_cache(manifesto: dict, item: dict, fmt: str) -> str:
    dados = [
        prompt_final(manifesto, item, fmt),
        negativo_de(manifesto, item),
        item["segundos"],
        item["modelo"],
        fmt,
    ]
    return hashlib.sha256(json.dumps(dados).encode("utf-8")).hexdigest()[:12]


def destino_publico(item: dict, fmt: str) -> Path:
    return PUBLICO / f"{item['id']}_{fmt}{EXTENSAO[item['tipo']]}"


# ---------------------------------------------------------------- openclaw


class FalhaProvedor(Exception):
    def __init__(self, tipo: str, texto: str) -> None:
        super().__init__(texto)
        self.tipo = tipo
        self.texto = texto

    @property
    def resumo(self) -> str:
        return resumo_erro(self.tipo, self.texto)


def mais_proxima(valor: float, opcoes: tuple[int, ...]) -> int:
    return min(opcoes, key=lambda opcao: (abs(opcao - valor), -opcao))


def argumentos_video(modelo: str, fmt: str, segundos: float, sonda: bool) -> list[str]:
    provedor, _, nome = modelo.partition("/")
    if provedor == "openai":
        tamanhos = TAMANHO_SORA.get(nome, TAMANHO_SORA["sora-2"])
        tamanho = TAMANHO_SORA["sora-2"][fmt] if sonda else tamanhos[fmt]
        return [
            "--size",
            tamanho,
            "--duration",
            str(mais_proxima(segundos, DURACOES_SORA)),
        ]
    return [
        "--aspect-ratio",
        PROPORCAO[fmt],
        "--resolution",
        "720P" if sonda else "1080P",
        "--duration",
        str(mais_proxima(segundos, DURACOES_VEO)),
    ]


def argumentos_imagem(modelo: str, fmt: str, sonda: bool) -> list[str]:
    provedor = modelo.split("/", 1)[0]
    if provedor == "openai":
        tamanho = "1536x1024" if sonda else TAMANHO_GPT_IMAGE[fmt]
        qualidade = "low" if sonda else "high"
        return ["--size", tamanho, "--quality", qualidade, "--output-format", "png"]
    return ["--aspect-ratio", PROPORCAO[fmt], "--resolution", "1K" if sonda else "2K"]


def extrair_saida(texto: str) -> dict | None:
    inicio = texto.find("{")
    while inicio != -1:
        try:
            dados, _ = json.JSONDecoder().raw_decode(texto[inicio:])
        except json.JSONDecodeError:
            inicio = texto.find("{", inicio + 1)
            continue
        if isinstance(dados, dict) and "outputs" in dados:
            return dados
        inicio = texto.find("{", inicio + 1)
    return None


def chamar_openclaw(
    tipo: str,
    modelo: str,
    prompt: str,
    fmt: str,
    segundos: float,
    saida: Path,
    sonda: bool = False,
) -> tuple[Path, str]:
    """Roda o openclaw e devolve (arquivo gerado, modelo efetivo)."""
    if tipo == "video":
        extras = argumentos_video(modelo, fmt, segundos, sonda)
        comando = ["openclaw", "infer", "video", "generate"]
    else:
        extras = argumentos_imagem(modelo, fmt, sonda)
        comando = ["openclaw", "infer", "image", "generate"]
    saida.parent.mkdir(parents=True, exist_ok=True)
    comando += [
        "--model",
        modelo,
        "--prompt",
        prompt,
        *extras,
        "--output",
        str(saida),
        "--timeout-ms",
        str(TIMEOUT_MS),
        "--json",
    ]
    try:
        processo = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_MS / 1000 + 180,
            check=False,
        )
    except subprocess.TimeoutExpired as erro:
        raise FalhaProvedor("tempo", f"sem resposta em {erro.timeout:.0f} s") from erro
    texto = f"{processo.stderr}\n{processo.stdout}"
    if processo.returncode != 0:
        raise FalhaProvedor(classificar_erro(texto), limpar_erro(texto))
    dados = extrair_saida(processo.stdout) or {}
    caminhos = [Path(s["path"]) for s in dados.get("outputs", []) if s.get("path")]
    if not caminhos:
        caminhos = sorted(saida.parent.glob(f"{saida.stem}*"))
    caminhos = [c for c in caminhos if c.exists() and c.stat().st_size > 0]
    if not caminhos:
        raise FalhaProvedor("erro", "o openclaw terminou sem arquivo de saída")
    return caminhos[0], str(dados.get("model") or modelo)


# ---------------------------------------------------------------- contexto


@dataclass
class Contexto:
    manifesto: dict
    cache: dict
    forcar: bool = False
    sondagem: dict = field(default_factory=dict)
    mortos: dict = field(default_factory=dict)
    trava: threading.Lock = field(default_factory=threading.Lock)
    contagem: dict = field(default_factory=lambda: {"pronto": 0, "pendente": 0})

    def registrar(self, chave: str, entrada: dict) -> None:
        with self.trava:
            self.cache[chave] = entrada
            gravar_json(CACHE, self.cache)

    def matar(self, modelo: str, texto: str) -> None:
        with self.trava:
            self.mortos.setdefault(modelo, texto)

    def motivo_morte(self, modelo: str) -> str | None:
        with self.trava:
            return self.mortos.get(modelo)

    def candidatos(self, tipo: str, preferido: str) -> list[str]:
        lista = [preferido, *self.manifesto["provedores"][tipo]]
        return list(dict.fromkeys(lista))


def aplicar_sondagem(contexto: Contexto) -> None:
    """Provedor reprovado na sondagem recente nem é tentado na geração."""
    sondagem = ler_json(SONDAGEM, {})
    if not sondagem:
        return
    idade = time.time() - sondagem.get("epoca", 0)
    if idade > VALIDADE_SONDAGEM_S:
        print(f"sondagem de {sondagem.get('em')} vencida; todos os provedores entram")
        return
    contexto.sondagem = sondagem
    for tipo in ("video", "imagem"):
        for resultado in sondagem.get(tipo, []):
            if not resultado["ok"] and resultado["tipo_erro"] in FALHAS_DO_PROVEDOR:
                resumo = resumo_erro(resultado["tipo_erro"], resultado["erro"])
                contexto.matar(resultado["modelo"], f"sondagem, {resumo}")


def imprimir(trava: threading.Lock, *colunas: object) -> None:
    ident, fmt, provedor, segundos, estado = colunas
    linha = f"{ident:<28} {fmt:<5} {provedor:<46} {segundos:>7.1f}s  {estado}"
    with trava:
        print(linha, flush=True)


# ---------------------------------------------------------------- geração


def gerar_um(contexto: Contexto, item: dict, fmt: str) -> None:
    manifesto = contexto.manifesto
    ident = item["id"]
    rotulo = f"{ident}_{fmt}"
    chave = chave_cache(manifesto, item, fmt)
    destino = destino_publico(item, fmt)
    anterior = contexto.cache.get(rotulo)
    if not contexto.forcar and destino.exists():
        sem_registro = anterior is None
        valido = (
            anterior is not None
            and anterior.get("chave") == chave
            and anterior.get("estado") == "pronto"
        )
        if sem_registro or valido:
            imprimir(contexto.trava, ident, fmt, "(cache)", 0.0, "pronto")
            with contexto.trava:
                contexto.contagem["pronto"] += 1
            return

    prompt = prompt_final(manifesto, item, fmt)
    erros: list[str] = []
    for modelo in contexto.candidatos(item["tipo"], item["modelo"]):
        morte = contexto.motivo_morte(modelo)
        if morte:
            erros.append(f"{modelo}: {morte}")
            continue
        bruto = BRUTOS / f"{rotulo}_{chave}{EXTENSAO[item['tipo']]}"
        inicio = time.monotonic()
        try:
            arquivo, efetivo = chamar_openclaw(
                item["tipo"], modelo, prompt, fmt, item["segundos"], bruto
            )
        except FalhaProvedor as falha:
            gasto = time.monotonic() - inicio
            erros.append(f"{modelo}: {falha.resumo}")
            if falha.tipo in FALHAS_DO_PROVEDOR:
                contexto.matar(modelo, falha.resumo)
            imprimir(
                contexto.trava, ident, fmt, modelo, gasto, f"falha, {falha.resumo}"
            )
            continue
        normalizar(arquivo, destino, fmt)
        som = None
        if item["tipo"] == "video" and item.get("som"):
            som = extrair_som(arquivo, destino)
        gasto = time.monotonic() - inicio
        entrada = {
            "chave": chave,
            "origem": "openclaw",
            "estado": "pronto",
            "modelo": efetivo,
            "provedor": efetivo.split("/", 1)[0],
            "gerado_em": agora(),
            "segundos": duracao(destino) if item["tipo"] == "video" else 0.0,
            "geracao_s": round(gasto, 1),
            "bruto": relativo(arquivo),
            "sha256": sha256_arquivo(destino),
        }
        if som:
            entrada["som"] = relativo(som)
        contexto.registrar(rotulo, entrada)
        imprimir(contexto.trava, ident, fmt, efetivo, gasto, "pronto")
        with contexto.trava:
            contexto.contagem["pronto"] += 1
        return

    entrada = {
        "chave": chave,
        "origem": "manual",
        "estado": "pendente",
        "modelo": None,
        "gerado_em": None,
        "segundos": None,
        "erro": " | ".join(erros) or "nenhum provedor disponível",
        "entrada_esperada": relativo(ENTRADA / f"{rotulo}{EXTENSAO[item['tipo']]}"),
    }
    if destino.exists():
        entrada["arquivo_anterior"] = relativo(destino)
    contexto.registrar(rotulo, entrada)
    imprimir(contexto.trava, ident, fmt, "(manual)", 0.0, "pendente")
    with contexto.trava:
        contexto.contagem["pendente"] += 1


def selecionar(manifesto: dict, args: argparse.Namespace) -> list[tuple[dict, str]]:
    ids = {i.strip() for grupo in args.so or [] for i in grupo.split(",") if i.strip()}
    conhecidos = {item["id"] for item in manifesto["itens"]}
    if ids - conhecidos:
        raise SystemExit(f"ids fora do manifesto: {sorted(ids - conhecidos)}")
    tipos = set()
    if args.imagens:
        tipos.add("imagem")
    if args.videos:
        tipos.add("video")
    tipos = tipos or {"imagem", "video"}
    formatos = [args.formato] if args.formato else list(FORMATOS)
    escolhidos = [
        item
        for item in manifesto["itens"]
        if item["tipo"] in tipos and (not ids or item["id"] in ids)
    ]
    # Stills primeiro (baratos), depois todos os vídeos 16x9, depois os 9x16.
    pares = [
        (item, fmt)
        for item in escolhidos
        if item["tipo"] == "imagem"
        for fmt in formatos
        if fmt in item["formatos"]
    ]
    for fmt in formatos:
        pares += [
            (item, fmt)
            for item in escolhidos
            if item["tipo"] == "video" and fmt in item["formatos"]
        ]
    return pares


def gerar(contexto: Contexto, pares: list[tuple[dict, str]]) -> None:
    aplicar_sondagem(contexto)
    if contexto.mortos:
        for modelo, motivo in contexto.mortos.items():
            print(f"fora desta execução: {modelo} ({motivo})")
    with ThreadPoolExecutor(max_workers=MAX_PARALELO) as executor:
        futuros = [
            executor.submit(gerar_um, contexto, item, fmt) for item, fmt in pares
        ]
        for futuro in futuros:
            futuro.result()


# ---------------------------------------------------------------- sondagem


def sondar(manifesto: dict, dir_sonda: Path) -> dict:
    resultados: dict = {"em": agora(), "epoca": time.time(), "video": [], "imagem": []}
    trava = threading.Lock()

    def um(tipo: str, modelo: str) -> None:
        nome = re.sub(r"[^a-z0-9]+", "_", modelo.lower())
        saida = dir_sonda / f"sonda_{tipo}_{nome}{EXTENSAO[tipo]}"
        inicio = time.monotonic()
        registro = {"modelo": modelo, "ok": False, "tipo_erro": None, "erro": None}
        try:
            arquivo, efetivo = chamar_openclaw(
                tipo, modelo, PROMPT_SONDA[tipo], "16x9", 4, saida, sonda=True
            )
        except FalhaProvedor as falha:
            registro.update(tipo_erro=falha.tipo, erro=falha.texto)
            estado = f"falha ({falha.tipo})"
        else:
            registro.update(ok=True, modelo_efetivo=efetivo, arquivo=str(arquivo))
            estado = "ok"
        registro["segundos"] = round(time.monotonic() - inicio, 1)
        with trava:
            resultados[tipo].append(registro)
        imprimir(trava, "sonda", tipo[:5], modelo, registro["segundos"], estado)
        if registro["erro"]:
            with trava:
                print(f"    {registro['erro']}", flush=True)

    dir_sonda.mkdir(parents=True, exist_ok=True)
    tarefas = [
        (tipo, modelo)
        for tipo in ("imagem", "video")
        for modelo in manifesto["provedores"][tipo]
    ]
    with ThreadPoolExecutor(max_workers=MAX_PARALELO) as executor:
        for futuro in [executor.submit(um, tipo, modelo) for tipo, modelo in tarefas]:
            futuro.result()
    ordem = {modelo: i for i, (_, modelo) in enumerate(tarefas)}
    for tipo in ("video", "imagem"):
        resultados[tipo].sort(key=lambda r: ordem[r["modelo"]])
        ok = [r["modelo"] for r in resultados[tipo] if r["ok"]]
        print(f"{tipo}: {'usar ' + ok[0] if ok else 'nenhum provedor respondeu'}")
    gravar_json(SONDAGEM, resultados)
    return resultados


# ---------------------------------------------------------------- entrada manual


def absorver(contexto: Contexto) -> None:
    manifesto = contexto.manifesto
    por_id = {item["id"]: item for item in manifesto["itens"]}
    ENTRADA.mkdir(parents=True, exist_ok=True)
    padrao = re.compile(r"^(?P<id>[a-z0-9_]+)_(?P<fmt>16x9|9x16)$")
    recebidos: dict[str, set[str]] = {}
    originais: dict[str, Path] = {}
    for arquivo in sorted(ENTRADA.iterdir()):
        if not arquivo.is_file() or arquivo.name.startswith("."):
            continue
        achado = padrao.match(arquivo.stem)
        item = por_id.get(achado["id"]) if achado else None
        if not achado or not item:
            print(f"ignorado (nome fora do padrão <id>_<fmt>.<ext>): {arquivo.name}")
            continue
        fmt = achado["fmt"]
        if arquivo.suffix.lower() not in EXT_ACEITAS[item["tipo"]]:
            print(f"ignorado (extensão não serve para {item['tipo']}): {arquivo.name}")
            continue
        rotulo = f"{item['id']}_{fmt}"
        recebidos.setdefault(item["id"], set()).add(fmt)
        originais[rotulo] = arquivo
        destino = destino_publico(item, fmt)
        assinatura = sha256_arquivo(arquivo)
        anterior = contexto.cache.get(rotulo) or {}
        if anterior.get("sha256_entrada") == assinatura and destino.exists():
            imprimir(contexto.trava, item["id"], fmt, "(entrada)", 0.0, "já absorvido")
            continue
        inicio = time.monotonic()
        normalizar(arquivo, destino, fmt)
        som = None
        if item["tipo"] == "video" and item.get("som"):
            som = extrair_som(arquivo, destino)
        entrada = {
            "chave": chave_cache(manifesto, item, fmt),
            "origem": "manual",
            "estado": "pronto",
            "modelo": "manual",
            "gerado_em": agora(),
            "segundos": duracao(destino) if item["tipo"] == "video" else 0.0,
            "bruto": relativo(arquivo),
            "sha256_entrada": assinatura,
            "sha256": sha256_arquivo(destino),
        }
        if som:
            entrada["som"] = relativo(som)
        contexto.registrar(rotulo, entrada)
        gasto = time.monotonic() - inicio
        imprimir(
            contexto.trava, item["id"], fmt, f"entrada/{arquivo.name}", gasto, "pronto"
        )
    # Só o 16x9 chegou: o retrato sai recortado ao centro e midia.json registra.
    for ident, formatos in recebidos.items():
        if formatos == {"16x9"} and "9x16" in por_id[ident]["formatos"]:
            recortar_um(contexto, por_id[ident], originais[f"{ident}_16x9"])


def fonte_16x9(item: dict, cache: dict) -> Path | None:
    entrada = cache.get(f"{item['id']}_16x9") or {}
    bruto = RAIZ / entrada["bruto"] if entrada.get("bruto") else None
    if bruto and bruto.exists():
        return bruto
    publico = destino_publico(item, "16x9")
    return publico if publico.exists() else None


def recortar_um(contexto: Contexto, item: dict, origem: Path) -> None:
    rotulo = f"{item['id']}_9x16"
    atual = contexto.cache.get(rotulo) or {}
    destino = destino_publico(item, "9x16")
    if (
        destino.exists()
        and atual.get("estado") == "pronto"
        and not atual.get("recorte_de")
    ):
        return
    assinatura = sha256_arquivo(origem)
    mesma_fonte = atual.get("sha256_entrada") == assinatura
    if atual.get("recorte_de") and mesma_fonte and destino.exists():
        return
    inicio = time.monotonic()
    normalizar(origem, destino, "9x16")
    contexto.registrar(
        rotulo,
        {
            "chave": chave_cache(contexto.manifesto, item, "9x16"),
            "origem": (contexto.cache.get(f"{item['id']}_16x9") or {}).get(
                "origem", "manual"
            ),
            "estado": "pronto",
            "modelo": "recorte_central",
            "recorte_de": "16x9",
            "gerado_em": agora(),
            "segundos": duracao(destino) if item["tipo"] == "video" else 0.0,
            "bruto": relativo(origem),
            "sha256_entrada": assinatura,
            "sha256": sha256_arquivo(destino),
        },
    )
    gasto = time.monotonic() - inicio
    imprimir(
        contexto.trava, item["id"], "9x16", "recorte central do 16x9", gasto, "pronto"
    )


def recortar(contexto: Contexto, pares: list[tuple[dict, str]]) -> None:
    for item, fmt in pares:
        if fmt != "9x16" or destino_publico(item, "9x16").exists():
            continue
        origem = fonte_16x9(item, contexto.cache)
        if origem is None:
            print(f"{item['id']}: sem 16x9 para recortar")
            continue
        recortar_um(contexto, item, origem)


# ---------------------------------------------------------------- relatórios


def faltando(contexto: Contexto, pares: list[tuple[dict, str]]) -> int:
    manifesto = contexto.manifesto
    pendentes = [(i, f) for i, f in pares if not destino_publico(i, f).exists()]
    if not pendentes:
        print("nada faltando")
        return 0
    print(
        f"{len(pendentes)} arquivo(s) faltando. Gere à mão e salve com o nome indicado;"
    )
    print("depois rode: python3 scripts/video-masterclass-midia.py --absorver\n")
    for item, fmt in pendentes:
        rotulo = f"{item['id']}_{fmt}"
        alvo = relativo(ENTRADA / f"{rotulo}{EXTENSAO[item['tipo']]}")
        if item["tipo"] == "video":
            ficha = f"vídeo {item['segundos']} s, {PROPORCAO[fmt]}, sem áudio"
        else:
            ficha = f"imagem {PROPORCAO[fmt]}, 2K ou mais"
        motivo = (contexto.cache.get(rotulo) or {}).get("erro", "ainda não tentado")
        print(f"## {rotulo}  ({ficha})")
        print(f"   salvar em: {alvo}")
        print(f"   onde gerar: {FERRAMENTAS_MANUAIS[item['tipo']]}")
        print(f"   cenas: {', '.join(item.get('cenas', []))}")
        print(f"   motivo: {motivo}")
        print(f"   prompt: {prompt_final(manifesto, item, fmt)}\n")
    return len(pendentes)


def escrever_midia_json(contexto: Contexto) -> dict:
    saida: dict = {}
    for item in contexto.manifesto["itens"]:
        presentes = [
            fmt
            for fmt in FORMATOS
            if fmt in item["formatos"] and destino_publico(item, fmt).exists()
        ]
        if not presentes:
            continue
        if item["tipo"] == "video":
            segundos = min(duracao(destino_publico(item, fmt)) for fmt in presentes)
        else:
            segundos = 0.0
        registro = {"tipo": item["tipo"], "formatos": presentes, "segundos": segundos}
        if (contexto.cache.get(f"{item['id']}_9x16") or {}).get("recorte_de") == "16x9":
            registro["recorte_9x16"] = True
        saida[item["id"]] = registro
    gravar_json(SAIDA_DADOS, saida)
    return saida


# ---------------------------------------------------------------- principal


def argumentos() -> argparse.Namespace:
    analisador = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    modo = analisador.add_mutually_exclusive_group()
    modo.add_argument(
        "--sondar", action="store_true", help="um clipe curto por provedor"
    )
    modo.add_argument(
        "--faltando", action="store_true", help="lista o que falta e os prompts"
    )
    modo.add_argument(
        "--absorver", action="store_true", help="normaliza midia/entrada/"
    )
    modo.add_argument("--recortar", action="store_true", help="9x16 recortado do 16x9")
    analisador.add_argument("--so", action="append", help="ids (vírgula ou repetido)")
    analisador.add_argument("--formato", choices=FORMATOS)
    analisador.add_argument("--imagens", action="store_true", help="só stills")
    analisador.add_argument("--videos", action="store_true", help="só vídeos")
    analisador.add_argument("--forcar", action="store_true", help="ignora o cache")
    analisador.add_argument(
        "--dir-sonda",
        type=Path,
        default=Path(tempfile.gettempdir()) / "masterclass-sonda",
        help="pasta temporária dos clipes de sondagem",
    )
    return analisador.parse_args()


def main() -> int:
    args = argumentos()
    inicio = time.monotonic()
    manifesto = carregar_manifesto()
    contexto = Contexto(
        manifesto=manifesto, cache=ler_json(CACHE, {}), forcar=args.forcar
    )
    pares = selecionar(manifesto, args)
    try:
        if args.sondar:
            sondar(manifesto, args.dir_sonda)
        elif args.faltando:
            faltando(contexto, pares)
        elif args.absorver:
            absorver(contexto)
        elif args.recortar:
            recortar(contexto, pares)
        else:
            gerar(contexto, pares)
    except KeyboardInterrupt:
        print(
            "interrompido; cache e midia.json gravados com o que já saiu",
            file=sys.stderr,
        )
    finally:
        gravar_json(CACHE, contexto.cache)
        midia = escrever_midia_json(contexto)
        pendentes = sum(
            1 for item, fmt in pares if not destino_publico(item, fmt).exists()
        )
        total = time.monotonic() - inicio
        print(
            f"\nmidia.json: {len(midia)} item(ns) com arquivo; "
            f"{len(pares) - pendentes} de {len(pares)} arquivo(s) presentes; "
            f"{pendentes} pendente(s); {total / 60:.1f} min"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
