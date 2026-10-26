"""Capítulo 14 do dossiê do 2º turno: o acompanhamento, auditado.

O coletor (leituras, versões, latência, alertas gravados) sai de
`linha_do_tempo.json`; a amostra de seções, de `secoes.json`; as telas do telão
são as capturas de `video/vinheta_2t/public/final/*.png`, reduzidas para JPEG
de no máximo 1.280 px em `docs/img/apuracao_2t/` na hora do build.
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

from apuracao_2026.pagina_comum import limites, p, tabela

from .pagina_comum import ROOT, Capitulo, Dados, cabeca, caminho, inteiro, num

ORIGEM = ROOT / "video/vinheta_2t/public/final"
DESTINO = ROOT / "docs/img/apuracao_2t"
TELAS = [
    ("pres", "Placar presidencial com o duelo e a régua do 1º turno"),
    ("projecao", "Projeção da casa com a faixa de 90%"),
    ("regioes", "Duelo por região, seções e abstenção"),
    ("ufs", "Ranking das UFs, mais lentas primeiro, com o chip de parada"),
    ("pausas", "Linha do tempo da noite com as pausas e a faixa do 1º turno"),
    ("abstencao", "Abstenção dos municípios fechados contra o 1º turno"),
    ("comparecimento", "Vigilância de comparecimento nas seções recebidas"),
    ("gov-2t", "Os seis duelos de governador"),
    ("paralela", "Totalização paralela: cobertura e conferência"),
]
LARGURA = 1280
DURACAO_ENCERRAMENTO = "3:59"


def reduz(nome: str) -> Path | None:
    """Copia a captura como JPEG (máximo 1.280 px, qualidade 80) se faltar ou estiver velha."""
    src = ORIGEM / f"{nome}.png"
    dst = DESTINO / f"{nome}.jpg"
    if not src.exists():
        return dst if dst.exists() else None
    if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    from PIL import Image

    DESTINO.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB")
        if im.width > LARGURA:
            im = im.resize(
                (LARGURA, round(im.height * LARGURA / im.width)), Image.LANCZOS
            )
        im.save(dst, "JPEG", quality=80, optimize=True, progressive=True)
    return dst


def galeria() -> str:
    figs = []
    for nome, legenda in TELAS:
        dst = reduz(nome)
        if not dst:
            continue
        src = ORIGEM / f"{nome}.png"
        quando = (
            datetime.fromtimestamp(src.stat().st_mtime).strftime("%H:%M")
            if src.exists()
            else "s/d"
        )
        figs.append(
            f'<figure><img src="img/apuracao_2t/{dst.name}" alt="{escape(legenda)}" loading="lazy" '
            f'width="1280" height="720"><figcaption>{escape(legenda)}. Captura do telão às {quando} de 25/10.</figcaption></figure>'
        )
    if not figs:
        return ""
    return f'<div class="galeria">{"".join(figs)}</div>'


def tabela_coletor(L: dict) -> str:
    nomes = {"br": "Nacional", "uf": "UF", "mu": "Município", "zona": "Zona"}
    pn = L["regressoes"]["por_nivel"]
    lat = L["latencia"]["por_nivel"]
    linhas = []
    for k, v in pn.items():
        lt = lat.get(k, {})
        linhas.append(
            [
                nomes.get(k, k),
                inteiro(v["capturas"]),
                inteiro(v["marcadas_regressivas"]),
                inteiro(v["copia_antiga"]),
                num(lt.get("p50_s"), 1) if lt else "s/d",
            ]
        )
    return tabela(
        [
            "Nível",
            "Versões capturadas",
            "Marcadas regressivas",
            "Cópias antigas",
            "Latência mediana (s)",
        ],
        linhas,
        "Versões do presidente lidas pelo coletor por nível de arquivo. Fonte: linha_do_tempo.json (regressoes e latencia).",
    )


def tabela_alertas(L: dict) -> str:
    ev = sorted(L.get("eventos_por_tipo") or [], key=lambda e: -e["n"])
    if not ev:
        return ""
    sev = {"error": "erro", "warn": "aviso", "info": "informação"}
    linhas = [
        [
            e["tipo"].replace("_", " "),
            sev.get(e["severidade"], e["severidade"]),
            inteiro(e["n"]),
        ]
        for e in ev
    ]
    return (
        "<details><summary>Os alertas que o coletor gravou na noite</summary>"
        + tabela(
            ["Tipo", "Severidade", "Ocorrências"],
            linhas,
            "Contagem por tipo na tabela de anomalias do banco do 2º turno. Alerta é sinal para olhar, não conclusão.",
        )
        + "</details>"
    )


def render(d: Dados, cap: Capitulo) -> str:
    L = d.get("linha_do_tempo.json")
    S = d.get("secoes.json")
    pn = L["regressoes"]["por_nivel"]
    capt = sum(v["capturas"] for v in pn.values())
    sil = L["pausas"]["silencio_geral"]
    h = cabeca(
        cap,
        f"{inteiro(capt)} versões lidas,<br><em>nenhuma contagem para trás.</em>",
        "O coletor, o telão, os boletins e a vigília automática da noite, com o que cada um provou e o que não alcança.",
    )
    h += p(
        f"O coletor leu os arquivos públicos de resultado do TSE e guardou {inteiro(capt)} versões do presidente nos quatro níveis "
        f"(nacional, UF, município e zona), cada uma com hora de geração, hora de leitura e SHA-256. Durante a parada de "
        f"{num(sil['minutos'], 1)} minutos fez {inteiro(sil['leituras_no_intervalo'])} leituras: é por isso que a página afirma "
        "que nada foi gerado no intervalo, e não apenas que nada foi lido.",
        "verificado",
    )
    h += tabela_coletor(L)
    br = L["latencia"]["por_nivel"].get("br", {})
    if br:
        h += p(
            f"No arquivo nacional, a mediana entre a geração no TSE e a leitura foi de {num(br['p50_s'], 1)} segundos, com p95 de "
            f"{num(br['p95_s'], 1)}. O máximo, {num(br['max_s'] / 60, 1)} minutos, é a última versão de antes da parada, lida quando "
            "o fluxo voltou. Latência inclui o intervalo de sondagem e é teto, não medida.",
            "verificado",
        )
    h += tabela_alertas(L)
    if S:
        enc = caminho(S, "agregados.brasil.encerramento") or {}
        if S.get("fonte") == "completo":
            h += "<h3>Os boletins de todas as seções</h3>" + p(
                f"Ao lado dos arquivos agregados, a casa leu o boletim de urna de cada seção: "
                f"{inteiro(caminho(S, 'totais.secoes'))} seções com horário de encerramento, emissão e recebimento, "
                f"último recebimento às {S.get('max_recebido_hhmm', 's/d')}. Na noite, o coletor lia uma amostra equiprovável por "
                f"município; esta página usa o banco completo. É dele que sai o encerramento mediano às {enc.get('p50_2t', 's/d')}.",
                "verificado",
            )
        else:
            h += "<h3>A amostra de seções ao vivo</h3>" + p(
                f"Ao lado dos arquivos agregados, o coletor buscou o boletim de urna de uma amostra equiprovável por município: "
                f"{inteiro(caminho(S, 'totais.secoes'))} seções com horário de encerramento, emissão e recebimento. É dela que sai o "
                f"encerramento mediano às {enc.get('p50_2t', 's/d')}. O banco completo, com todas as seções, ainda estava em coleta "
                "quando esta página foi gerada; o capítulo 08 diz qual fonte usou.",
                "verificado",
            )
    h += "<h3>O telão</h3>" + p(
        "A live foi um telão em navegador, com telas trocadas pela playlist do 2º turno e por teclado, alimentado pela API local "
        "sobre o mesmo banco. As capturas abaixo são do fim da noite.",
        "verificado",
    )
    h += galeria()
    h += "<h3>Vinhetas e vigília</h3>" + p(
        "A vinheta de abertura (Remotion, voz do autor pelo ElevenLabs v4) foi programada para as 17:00 e para cada retomada da divulgação. "
        f"O vídeo de encerramento, de {DURACAO_ENCERRAMENTO}, só toca por comando manual. A partida foi programada: um agendador ligado "
        "dias antes disparava às 16:40 a conferência prévia (régua do 1º turno, configuração do pleito, Supabase da totalização paralela, "
        "relógio, disco), o coletor, o servidor e a publicação da página ao vivo a cada 5 minutos.",
        "verificado",
    )
    h += p(
        'Como reproduzir: <code>apuracao/README.md</code>, seção "2º turno (25/10)". O banco do coletor não cabe no GitHub e é enviado a pedido.',
    )
    h += limites(
        [
            (
                f"Boletins de urna de {inteiro(caminho(S, 'totais.secoes'))} seções, banco completo lido depois da noite."
                if S and S.get("fonte") == "completo"
                else f"Amostra de {inteiro(caminho(S, 'totais.secoes')) if S else 's/d'} seções ao vivo; o banco completo de boletins de urna estava em coleta."
            ),
            "O coletor lê o que o TSE publica; não vê o que acontece entre a urna e o arquivo público.",
            "Latência inclui o intervalo de sondagem: é teto da demora de publicação.",
            "As telas são capturas para registro, não a gravação da live (que está no topo da página).",
        ]
    )
    return h
