#!/usr/bin/env python3
"""Monta a thread da auditoria Quaest/Globo de 14 de agosto de 2026.

Lê o texto dos posts em `docs/threads/quaest_globo_140826_thread.md` e a camada
estratégica em `docs/assets/quaest_globo_140826_estrategia.json`, e escreve
`docs/quaest_globo_140826_thread.html` com vinte cards 16:9 e texto copiável.

As visualizações são declarativas: cada card escolhe um tipo de gráfico e
entrega os dados já auditados. Nada é desenhado à mão no HTML final.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/threads/quaest_globo_140826_thread.md"
STRATEGY = ROOT / "docs/assets/quaest_globo_140826_estrategia.json"
OUTPUT = ROOT / "docs/quaest_globo_140826_thread.html"

PHOTOS = "img/quaest_082026/web"
OWN = "img/quaest_globo_140826"

# Cor por papel, repetida no CSS da página.
RED = "#ef3e36"
RED_L = "#ff8a84"
BLUE = "#1b54f2"
BLUE_L = "#74a2ff"
LIME = "#d9ff43"
GOLD = "#e8a33d"
GREEN = "#3ec98d"
VIOLET = "#836dff"
GREY = "#6b7382"
INK = "#f6f2e8"
MUTED = "#98a1af"

MONO = "IBM Plex Mono, monospace"
BLACK = "Archivo Black, Impact, sans-serif"
SANS = "IBM Plex Sans Condensed, sans-serif"

# Cada card: foto de fundo, tarja, chips e a especificação do gráfico.
CARDS = [
    {
        "kicker": "a tese",
        "photo": f"{PHOTOS}/urna-fila.jpg",
        "pos": "center 30%",
        "tag": "quaest/globo · 10–13/08 · n = 2.004",
        "chips": [
            ("a", "faltam 10,00"),
            ("b", "Flávio 37,80% dos válidos"),
            ("r", "Lula 46,34%"),
        ],
        "viz": {
            "type": "gauge",
            "title": "votos válidos declarados, 82 pontos",
            "have": 31,
            "need": 41,
            "total": 82,
            "foot": [
                "Flávio precisa de metade mais um.",
                "A distância é de dez pontos.",
            ],
        },
        "foot": [
            "arvor intelligence · quaest/globo 14/08/2026",
            "TSE BR-06773/2026 · p. 16",
        ],
    },
    {
        "kicker": "a margem",
        "photo": f"{PHOTOS}/urna-maquina.jpg",
        "tag": "conta nossa sobre as páginas 16 e 30",
        "chips": [
            ("r", "2º turno inclui zero"),
            ("b", "1º turno resiste"),
            ("a", "margem da diferença"),
        ],
        "viz": {
            "type": "interval",
            "title": "intervalo de 95% da diferença entre os dois",
            "rows": [
                {"label": "1º turno, 7 pontos", "lo": 3.38, "hi": 10.62, "color": BLUE},
                {"label": "2º turno, 3 pontos", "lo": -0.99, "hi": 6.99, "color": RED},
            ],
            "foot": [
                "A linha do zero é a fronteira do empate.",
                "Só o segundo turno a cruza.",
            ],
        },
        "foot": ["aproximação de amostra aleatória simples", "pp. 16 e 30"],
    },
    {
        "kicker": "o mapa",
        "photo": f"{PHOTOS}/praca_conselheiro_pena.jpg",
        "tag": "fato publicado · página 17",
        "chips": [
            ("b", "Sul 40 a 25"),
            ("b", "Sudeste 35 a 32"),
            ("r", "Nordeste 57 a 23"),
        ],
        "viz": {
            "type": "duel",
            "title": "primeiro turno por região",
            "rows": [
                {"label": "Sul", "a": 25, "b": 40},
                {"label": "Sudeste", "a": 32, "b": 35},
                {"label": "Centro-Oeste/Norte", "a": 36, "b": 26},
                {"label": "Nordeste", "a": 57, "b": 23},
            ],
            "legend": ["Lula", "Flávio"],
        },
        "foot": ["margem regional de 3 a 6 pontos", "p. 17"],
    },
    {
        "kicker": "onde mora",
        "photo": f"{PHOTOS}/eleicao-rua.jpg",
        "tag": "conta nossa sobre as páginas 17 e 21",
        "chips": [("a", "59,9% no Sudeste e no Sul"), ("g", "controle: recompõe 12")],
        "viz": {
            "type": "bars",
            "title": "pontos de terceira via por região",
            "rows": [
                {"label": "Centro-Oeste/Norte", "value": 17, "color": VIOLET},
                {"label": "Sudeste", "value": 13, "color": VIOLET},
                {"label": "Sul", "value": 12, "color": VIOLET},
                {"label": "Nordeste", "value": 7, "color": GREY},
            ],
            "max": 20,
            "suffix": " pts",
            "foot": [
                "Onde Flávio já lidera, sobra voto.",
                "No Nordeste não há terceiro a consolidar.",
            ],
        },
        "foot": ["Renan, Caiado, Cury e Zema", "pp. 17 e 21"],
    },
    {
        "kicker": "briga interna",
        "photo": f"{PHOTOS}/feira.jpg",
        "tag": "conta nossa sobre a página 21",
        "chips": [("a", "81,2% acima de 2 SM"), ("b", "16 pts acima de 5 SM")],
        "viz": {
            "type": "bars",
            "title": "pontos de terceira via por faixa de renda",
            "rows": [
                {"label": "Mais de 5 SM", "value": 16, "color": VIOLET},
                {"label": "2 a 5 SM", "value": 12, "color": VIOLET},
                {"label": "Até 2 SM", "value": 7, "color": GREY},
            ],
            "max": 20,
            "suffix": " pts",
            "foot": [
                "O adversário desta etapa não é Lula.",
                "São Caiado, Zema, Renan e Cury.",
            ],
        },
        "foot": ["arvor intelligence", "p. 21"],
    },
    {
        "kicker": "o voto que balança",
        "photo": f"{PHOTOS}/zema.jpg",
        "tag": "fato publicado · página 28 · cinco ondas",
        "chips": [
            ("r", "Zema 77%"),
            ("a", "Caiado 45%"),
            ("b", "Flávio 30%"),
            ("g", "Lula 22%"),
        ],
        "viz": {
            "type": "bars",
            "title": "quanto do voto o eleitor diz que pode mudar",
            "rows": [
                {"label": "Zema", "value": 77, "color": RED},
                {"label": "Caiado", "value": 45, "color": GOLD},
                {"label": "Renan", "value": 43, "color": GOLD},
                {"label": "Flávio", "value": 30, "color": BLUE_L},
                {"label": "Lula", "value": 22, "color": GREEN},
            ],
            "max": 100,
            "suffix": "%",
            "foot": [
                "Margem de 12 a 16 pontos nos menores.",
                "A direção repete em cinco ondas.",
            ],
        },
        "foot": ["quem mediu foi o instituto", "p. 28"],
    },
    {
        "kicker": "a conta",
        "photo": f"{PHOTOS}/congresso.jpg",
        "tag": "conta nossa · aritmética condicional",
        "chips": [("a", "12t + d + 0,5g > 10"), ("b", "83,3% da terceira via")],
        "viz": {
            "type": "equation",
            "title": "quanto falta conforme a captura da terceira via",
            "rows": [
                {"label": "25%", "got": 3.0, "need": 10.0},
                {"label": "50%", "got": 6.0, "need": 10.0},
                {"label": "75%", "got": 9.0, "need": 10.0},
                {"label": "83,3%", "got": 10.0, "need": 10.0},
            ],
            "foot": ["Sem tirar um voto de Lula.", "Dez dos doze pontos disponíveis."],
        },
        "foot": ["não é previsão de resultado", "p. 16"],
    },
    {
        "kicker": "a rota realista",
        "photo": f"{PHOTOS}/rodoviaria_fabriciano.jpg",
        "tag": "conta nossa sobre as páginas 16 e 28",
        "chips": [
            ("a", "6,07 mutáveis"),
            ("r", "faltam 3,93"),
            ("b", "43,6% do bloco de 18"),
        ],
        "viz": {
            "type": "stack",
            "title": "de onde saem os dez pontos",
            "segments": [
                {"label": "terceira via mutável", "value": 6.07, "color": VIOLET},
                {"label": "recrutamento no bloco de 18", "value": 3.93, "color": BLUE},
            ],
            "foot": [
                "Cada ponto recrutado entre indecisos",
                "vale meio ponto, porque muda os dois lados.",
            ],
        },
        "foot": ["arvor intelligence", "pp. 16 e 28"],
    },
    {
        "kicker": "o teste de 2022",
        "photo": f"{PHOTOS}/urna-maquina.jpg",
        "tag": "resultados oficiais do TSE",
        "chips": [("r", "espreme 6,14"), ("r", "faltam 10,00"), ("a", "não basta")],
        "viz": {
            "type": "bars",
            "title": "dois líderes, em % dos votos válidos",
            "rows": [
                {"label": "2022", "value": 91.63, "color": GOLD},
                {"label": "Quaest 14/08", "value": 84.15, "color": BLUE},
                {"label": "2018", "value": 75.72, "color": GREY},
            ],
            "max": 100,
            "suffix": "%",
            "foot": [
                "Repetir 2022 libera 6,14 pontos.",
                "Mesmo todos indo a Flávio, não fecha.",
            ],
        },
        "foot": ["Tebet 4,16 e Ciro 3,04 em 2022", "TSE"],
    },
    {
        "kicker": "a terceira via some",
        "photo": f"{PHOTOS}/banca.jpg",
        "tag": "resultados oficiais do TSE",
        "chips": [("a", "2018: 18,23%"), ("b", "2022: 7,20%"), ("g", "hoje: 14,63%")],
        "viz": {
            "type": "bars",
            "title": "terceira via, em % dos votos válidos",
            "rows": [
                {"label": "2018", "value": 18.23, "color": VIOLET},
                {"label": "hoje, Quaest", "value": 14.63, "color": BLUE_L},
                {"label": "2022", "value": 7.20, "color": GREY},
            ],
            "max": 20,
            "suffix": "%",
            "foot": [
                "O bloco encolhe, mas não anda junto.",
                "Em 2018 ele se rearrumou inteiro.",
            ],
        },
        "foot": ["Ciro, Alckmin e Marina em 2018", "TSE"],
    },
    {
        "kicker": "a trava",
        "photo": f"{PHOTOS}/lula.jpg",
        "tag": "fato publicado · páginas 91, 92 e 96",
        "chips": [
            ("r", "Lula +18"),
            ("b", "Flávio −4"),
            ("a", "22 pontos de distância"),
        ],
        "viz": {
            "type": "duel",
            "title": "voto e expectativa de vitória, nacional",
            "rows": [
                {"label": "Lula", "a": 38, "b": 56},
                {"label": "Flávio", "a": 31, "b": 27},
            ],
            "legend": ["intenção de voto", "acham que vence"],
            "colors": [GREY, GOLD],
        },
        "foot": ["prêmio de inevitabilidade", "pp. 16 e 91"],
    },
    {
        "kicker": "o Sul acha que ele perde",
        "photo": f"{PHOTOS}/antena.jpg",
        "tag": "fato publicado · páginas 92 e 17",
        "chips": [
            ("b", "ganha por 15"),
            ("r", "49% esperam Lula"),
            ("a", "36% esperam ele"),
        ],
        "viz": {
            "type": "duel",
            "title": "no Sul, voto contra expectativa",
            "rows": [
                {"label": "vota Flávio", "a": 25, "b": 40},
                {"label": "acha que vence", "a": 49, "b": 36},
            ],
            "legend": ["Lula", "Flávio"],
        },
        "foot": ["a região mais favorável a Flávio", "pp. 17 e 92"],
    },
    {
        "kicker": "o bloco que decide",
        "photo": f"{PHOTOS}/eleicao-rua.jpg",
        "tag": "fato publicado · página 99",
        "chips": [
            ("r", "52% esperam Lula"),
            ("b", "18% esperam Flávio"),
            ("a", "25% não sabem"),
        ],
        "viz": {
            "type": "bars",
            "title": "entre independentes, quem vai ganhar",
            "rows": [
                {"label": "Lula", "value": 52, "color": RED},
                {"label": "não sabe", "value": 25, "color": GREY},
                {"label": "Flávio", "value": 18, "color": BLUE},
            ],
            "max": 60,
            "suffix": "%",
            "foot": ["Voto útil pede fé na vitória.", "Aqui a fé está no outro lado."],
        },
        "foot": ["independentes são 32% da amostra", "p. 99"],
    },
    {
        "kicker": "a rejeição desmontada",
        "photo": f"{PHOTOS}/flavio.jpg",
        "tag": "fato publicado · páginas 71, 76 e 79",
        "chips": [("a", "55,9% desperdiçada"), ("g", "controle: 53,9 contra 54")],
        "viz": {
            "type": "duel",
            "title": "potencial de voto por recorte",
            "rows": [
                {"label": "Mais de 5 SM", "a": 36, "b": 48},
                {"label": "2 a 5 SM", "a": 40, "b": 44},
                {"label": "Independentes", "a": 35, "b": 34},
                {"label": "Até 2 SM", "a": 59, "b": 30},
            ],
            "legend": ["Lula", "Flávio"],
        },
        "foot": ["quem diz que poderia votar", "pp. 76 e 79"],
    },
    {
        "kicker": "a única ponte",
        "photo": f"{PHOTOS}/fluxo_25demarco.jpg",
        "tag": "fato publicado · páginas 154, 155, 158 e 159",
        "chips": [("a", "1ª em cinco blocos"), ("r", "37% entre lulistas")],
        "viz": {
            "type": "bars",
            "title": "violência como maior preocupação, por bloco",
            "rows": [
                {"label": "Lulista", "value": 37, "color": RED},
                {"label": "Independente", "value": 35, "color": GOLD},
                {"label": "Bolsonarista", "value": 32, "color": BLUE},
                {"label": "Esquerda não lulista", "value": 30, "color": RED},
                {"label": "Direita não bolsonarista", "value": 30, "color": BLUE},
            ],
            "max": 45,
            "suffix": "%",
            "foot": ["Economia divide. Governo divide.", "Violência atravessa."],
        },
        "foot": ["o plano de governo abre por ela", "p. 159"],
    },
    {
        "kicker": "o que atrapalha a tese",
        "photo": f"{PHOTOS}/supermercado.jpg",
        "tag": "a régua é a mesma nos dois sentidos",
        "chips": [
            ("r", "Lula +10 entre engajados"),
            ("r", "Bolsa Família 22%"),
            ("r", "Flávio: 9,3 soltos"),
        ],
        "viz": {
            "type": "duel",
            "title": "primeiro turno por interesse na eleição",
            "rows": [
                {"label": "Muito interessado", "a": 47, "b": 37},
                {"label": "Pouco interessado", "a": 38, "b": 29},
                {"label": "Nada interessado", "a": 26, "b": 24},
            ],
            "legend": ["Lula", "Flávio"],
        },
        "foot": ["engajamento não favorece Flávio", "pp. 25 e 195"],
    },
    {
        "kicker": "o enquadramento",
        "photo": f"{PHOTOS}/banca.jpg",
        "tag": "levantamento nosso · 16/08/2026",
        "chips": [
            ("a", "5 de 7 abrem pelo 2º turno"),
            ("b", "41 perguntas publicadas"),
        ],
        "viz": {
            "type": "compression",
            "title": "do relatório à manchete",
            "left": {"value": "41", "label": "perguntas publicadas em 197 páginas"},
            "right": {"value": "4", "label": "resultados usados pela cobertura"},
            "ratio": "10,2 : 1",
            "foot": [
                "Isso é método, não complô.",
                "As 193 páginas restantes estão públicas.",
            ],
        },
        "foot": [
            "Poder360, EM, Imirante, Oeste, Cafezinho, Metrópoles, Gazeta",
            "16/08/2026",
        ],
    },
    {
        "kicker": "hipótese declarada",
        "photo": f"{OWN}/marcal.jpg",
        "pos": "center 22%",
        "tag": "hipótese, não medição",
        "chips": [
            ("a", "registrado em 15/08"),
            ("r", "inelegível até 2032"),
            ("b", "art. 16-A"),
        ],
        "viz": {
            "type": "timeline",
            "title": "a última foto antes de Marçal",
            "rows": [
                {
                    "date": "10–13/08",
                    "text": "campo desta pesquisa, com Avalanche em 0%",
                },
                {"date": "14/08", "text": "divulgação do relatório de 197 páginas"},
                {"date": "15/08", "text": "PRTB registra Marçal, Avalanche vira vice"},
            ],
            "foot": [
                "Contraprova: em set/2024 a Quaest o mediu",
                "rachando a base bolsonarista, 33% contra 32%.",
            ],
        },
        "foot": [
            "TRE-SP, uso indevido dos meios de comunicação",
            "Lei 9.504/97, art. 16-A",
        ],
    },
    {
        "kicker": "o roteiro",
        "photo": f"{PHOTOS}/caiado.jpg",
        "tag": "inferência nossa · a ordem importa",
        "chips": [("a", "expectativa primeiro"), ("b", "depois o voto útil")],
        "viz": {
            "type": "steps",
            "title": "seis passos, nesta ordem",
            "rows": [
                "Inverter a expectativa",
                "Pedir voto útil no Sudeste, no Sul e acima de 2 SM",
                "Defender os 9,3 pontos mutáveis próprios",
                "Segurança como ponte, não como bandeira",
                "Custo de vida na faixa de 2 a 5 SM",
                "TV, igreja e liderança local",
            ],
        },
        "foot": ["derivado dos números anteriores", "não é previsão"],
    },
    {
        "kicker": "limites",
        "photo": f"{PHOTOS}/urna-fila.jpg",
        "pos": "center 45%",
        "tag": "o que não podemos afirmar",
        "chips": [
            ("g", "334 setores conferem"),
            ("g", "transcrição fecha"),
            ("r", "faltam pesos e desenho"),
        ],
        "viz": {
            "type": "checklist",
            "title": "o que falta para auditoria completa",
            "rows": [
                {
                    "ok": True,
                    "text": "transcrição recomposta por cruzamento independente",
                },
                {"ok": True, "text": "valores contratados batem com as notas fiscais"},
                {"ok": True, "text": "334 geocódigos existem na malha do IBGE"},
                {"ok": False, "text": "pesos finais anonimizados"},
                {"ok": False, "text": "identificador de setor e estrato"},
                {"ok": False, "text": "efeito de desenho e taxas de recusa"},
            ],
        },
        "foot": ["brasil.arvor.co/quaest_globo_140826.html", "dossiê completo"],
    },
]

HEAD = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thread, Quaest/Globo 14/08/2026: faltam dez pontos · Arvor Intelligence</title>
<meta name="description" content="Thread da auditoria Quaest/Globo de 14 de agosto de 2026 (TSE BR-06773/2026, n = 2.004, presencial domiciliar). Vinte posts com card 16:9 e texto copiável: a conta dos dez pontos que faltam a Flávio Bolsonaro no primeiro turno, onde mora a terceira via, o voto infiel medido pelo instituto, o prêmio de inevitabilidade de Lula e o enquadramento da imprensa.">
<link rel="canonical" href="https://brasil.arvor.co/quaest_globo_140826_thread.html">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Arvor Intelligence">
<meta property="og:locale" content="pt_BR">
<meta property="og:url" content="https://brasil.arvor.co/quaest_globo_140826_thread.html">
<meta property="og:title" content="Thread, Quaest/Globo 14/08: faltam dez pontos">
<meta property="og:description" content="Vinte posts prontos para o X: a conta do turno único, a terceira via que mora em campo amigo, o voto infiel que o instituto mediu e a trava que ninguém nomeou.">
<meta property="og:image" content="https://brasil.arvor.co/img/og/quaest_globo_140826_thread.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@leonardodias">
<meta name="twitter:creator" content="@leonardodias">
<meta name="twitter:image" content="https://brasil.arvor.co/img/og/quaest_globo_140826_thread.png">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="img/favicon-180.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=Fraunces:opsz,wght@9..144,600;9..144,900&family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#080c13; --bg2:#0d131d; --ink:#f6f2e8; --ink2:#dcd8cd; --muted:#98a1af; --faint:#6b7382;
  --red:#ef3e36; --red-l:#ff8a84; --blue:#74a2ff; --blue-d:#1b54f2; --lime:#d9ff43; --gold:#e8a33d; --green:#3ec98d;
  --line:rgba(246,242,232,.14); --line2:rgba(246,242,232,.28);
  --display:"Fraunces",Georgia,serif; --black:"Archivo Black",Impact,sans-serif;
  --sans:"IBM Plex Sans Condensed",Arial,sans-serif; --mono:"IBM Plex Mono",ui-monospace,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:
    radial-gradient(120% 60% at 85% -5%, rgba(116,162,255,.10), transparent 55%),
    radial-gradient(110% 60% at 0% 105%, rgba(239,62,54,.09), transparent 55%),
    var(--bg);
  color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.5;-webkit-font-smoothing:antialiased}
.wrap{width:min(1180px,calc(100% - 36px));margin:auto;padding:34px 0 100px}
a{color:var(--blue)}
header.top{padding:30px 0 6px;border-bottom:6px solid var(--lime)}
.brand-lockup{display:flex;align-items:center;gap:12px;margin-bottom:20px}
.brand-lockup img{width:42px;height:42px;object-fit:contain}
.brand-lockup span{font-family:var(--mono);font-weight:700;font-size:.82rem;letter-spacing:.16em;color:var(--lime);text-transform:uppercase}
header.top h1{font-family:var(--display);font-weight:900;font-size:clamp(2.2rem,6.4vw,4.2rem);line-height:.94;margin:0;letter-spacing:-.03em}
header.top h1 span{display:block;color:var(--lime);font-style:italic;font-weight:600;margin-top:.08em}
header.top p{max-width:820px;color:var(--ink2);font-size:1.04rem;margin:22px 0 26px}
header.top p b{color:#fff}
.howto,.sources{border:1px solid var(--line);border-radius:12px;padding:16px 20px;font-size:.9rem;color:var(--ink2);margin:18px 0 0;background:rgba(246,242,232,.02)}
.howto b,.sources b{color:#fff}
.sources{font-size:.8rem;color:var(--muted)}
.sources a{word-break:break-word}
.post{margin:52px 0 0}
.post-label{font-family:var(--mono);font-size:.8rem;color:var(--blue);text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;font-weight:700}
.post-label b{color:var(--lime)}
.card{position:relative;aspect-ratio:16/9;overflow:hidden;border-radius:14px;border:1px solid var(--line2);
  display:flex;flex-direction:column;padding:26px 30px;isolation:isolate;background:var(--bg2)}
.card::before{content:"";position:absolute;inset:0;z-index:0;background-image:var(--photo);
  background-size:cover;background-position:var(--pos,center);filter:grayscale(.6) contrast(1.06) brightness(.72)}
.card::after{content:"";position:absolute;inset:0;z-index:1;
  background:linear-gradient(100deg,rgba(7,11,18,.95) 0%,rgba(7,11,18,.93) 42%,rgba(7,11,18,.74) 68%,rgba(7,11,18,.52) 100%)}
.card>*{position:relative;z-index:2}
.card-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.card-head .brand{display:flex;align-items:center;gap:10px}
.card-head .brand img{width:26px;height:26px;object-fit:contain}
.card-head .brand b{display:block;font-size:.9rem;letter-spacing:.01em}
.card-head .brand span{display:block;font-family:var(--mono);font-size:.72rem;color:var(--muted)}
.card-head .pno{font-family:var(--mono);font-size:.8rem;color:var(--lime);font-weight:700;letter-spacing:.1em}
.card-body{flex:1;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.12fr);gap:30px;align-items:center;padding:18px 0 12px;min-height:0}
.lead-tag{display:inline-block;font-family:var(--mono);font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--lime);border:1px solid rgba(217,255,67,.5);border-radius:999px;padding:4px 10px;margin-bottom:12px}
.card h2{font-family:var(--display);font-weight:900;font-size:clamp(1.4rem,2.4vw,2.35rem);line-height:1.03;margin:0 0 12px;letter-spacing:-.025em}
.card h2 em{font-style:italic;font-weight:600;color:var(--lime)}
.card .metric{font-family:var(--black);font-size:clamp(1.7rem,3.4vw,3rem);line-height:1;color:var(--lime);margin:0 0 10px}
.card .t{margin:0;font-size:.98rem;color:var(--ink2);line-height:1.45}
.kchips{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}
.kchip{border:1px solid var(--line2);border-radius:999px;padding:5px 12px;font-size:.79rem;font-weight:700;color:var(--ink2);background:rgba(7,11,18,.5)}
.kchip.b{color:var(--blue)} .kchip.r{color:var(--red-l)} .kchip.a{color:var(--lime)} .kchip.g{color:var(--green)}
/* O rodapé do card fica sobre a foto, cuja luminância varia. Sem uma faixa
   sólida por baixo, o contraste do texto depende do enquadramento da imagem. */
.card-foot{display:flex;justify-content:space-between;gap:14px;margin:0 -30px -26px;padding:12px 30px 22px;
  border-top:1px solid var(--line);background:rgba(7,11,18,.88);
  font-family:var(--mono);font-size:.74rem;color:var(--muted);letter-spacing:.03em}
.viz{min-width:0}
svg{display:block;width:100%;height:auto}
.copy{margin-top:14px;background:#070b12;border:1px solid var(--line);border-radius:10px;padding:18px 20px;
  font-family:var(--mono);font-size:.9rem;line-height:1.6;color:var(--ink2);white-space:pre-wrap;word-wrap:break-word;position:relative}
.copy .cc{position:absolute;top:10px;right:14px;font-size:.68rem;color:var(--muted)}
.copy-btn{margin-top:9px;background:var(--blue-d);border:0;color:#fff;font-weight:700;font-size:.82rem;padding:9px 16px;border-radius:7px;cursor:pointer;font-family:var(--sans)}
.copy-btn:active{transform:translateY(1px)}
.copy-btn.ok{background:var(--lime);color:#1e2405}
footer.foot{margin-top:60px;border-top:1px solid var(--line);padding-top:20px;font-size:.82rem;color:var(--muted)}
footer.foot b{color:var(--ink2)}
@media (max-width:900px){
  .card{aspect-ratio:auto}
  .card-body{grid-template-columns:1fr;gap:22px}
  .card::after{background:linear-gradient(180deg,rgba(7,11,18,.9) 0%,rgba(7,11,18,.95) 40%,rgba(7,11,18,.97) 100%)}
}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <div class="brand-lockup"><img src="img/arvor_logo.png" alt="Arvor"><span>Arvor Intelligence · perícia eleitoral</span></div>
  <h1>Faltam dez pontos.<span>E eles não estão com Lula.</span></h1>
  <p>Thread da auditoria da <b>Quaest/Globo de 14 de agosto de 2026</b>, registro TSE BR-06773/2026, 2.004 entrevistas presenciais em domicílio entre 10 e 13 de agosto. Vinte posts com card pronto e texto copiável. A imprensa leu empate técnico no segundo turno. O mesmo relatório de 197 páginas guarda a conta do primeiro turno, e ela cabe numa linha.</p>
  <div class="howto"><b>Como usar.</b> Cada bloco traz o card 16:9 para anexar e, logo abaixo, o texto exato do post com a contagem de caracteres. O botão copia o texto sem formatação. Fato publicado vem com a página do relatório. Conta nossa vem com a fórmula aberta. Hipótese vem com etiqueta de hipótese.</div>
</header>
"""

FOOT_TEMPLATE = """
<footer class="foot">
  <p><b>Arvor Intelligence.</b> Auditoria independente. Nenhum instituto, veículo, banco, partido ou campanha encomendou, pagou ou revisou este material.</p>
  <div class="sources"><b>Fontes e reprodução.</b>
    Dossiê completo em <a href="quaest_globo_140826.html">brasil.arvor.co/quaest_globo_140826.html</a>.
    Base analítica em <a href="assets/quaest_globo_140826_data.json">quaest_globo_140826_data.json</a> e camada estratégica em <a href="assets/quaest_globo_140826_estrategia.json">quaest_globo_140826_estrategia.json</a>,
    geradas por <code>scripts/quaest-globo-140826-audit.py</code> e <code>scripts/quaest-globo-140826-estrategia.py</code>.
    Esta página é montada por <code>scripts/quaest-globo-140826-thread.py</code>.
    Fotos de fundo do Wikimedia Commons, com autoria e licença em <code>docs/img/quaest_082026/web/CREDITOS.json</code> e <code>docs/img/quaest_globo_140826/CREDITOS.json</code>.
    Retrato de Pablo Marçal por TV Brasil Central, CC BY 3.0.
  </div>
</footer>
</div>
<script>
function cp(btn){
  var node = btn.previousElementSibling;
  var text = node.textContent.replace(/^\\s*\\d+\\s*chars\\s*/, "").trim();
  navigator.clipboard.writeText(text).then(function(){
    btn.classList.add("ok"); btn.textContent = "Copiado";
    setTimeout(function(){ btn.classList.remove("ok"); btn.textContent = "Copiar texto"; }, 1600);
  });
}
</script>
</body>
</html>
"""


def esc(value: str) -> str:
    return html.escape(value, quote=False)


def text_node(
    x, y, content, size=13, fill=MUTED, family=MONO, weight=None, anchor=None
):
    attrs = [
        f'x="{x}"',
        f'y="{y}"',
        f'font-family="{family}"',
        f'font-size="{size}"',
        f'fill="{fill}"',
    ]
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    return f"<text {' '.join(attrs)}>{esc(str(content))}</text>"


def footer_lines(parts, lines, y, width):
    parts.append(
        f'<line x1="14" y1="{y}" x2="{width - 14}" y2="{y}" stroke="rgba(246,242,232,.2)"/>'
    )
    for index, line in enumerate(lines):
        color = INK if index == 0 else LIME
        parts.append(text_node(14, y + 26 + index * 22, line, 16, color, SANS, "700"))


def viz_bars(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    rows = spec["rows"]
    top, gap = 40, 34
    scale = (width - 190) / spec["max"]
    for index, row in enumerate(rows):
        y = top + index * gap
        parts.append(text_node(14, y + 16, row["label"], 13, INK, SANS, "600"))
        length = max(2, row["value"] * scale)
        parts.append(
            f'<rect x="170" y="{y}" width="{length:.1f}" height="21" rx="2" fill="{row["color"]}"/>'
        )
        label = f'{row["value"]:g}'.replace(".", ",") + spec.get("suffix", "")
        parts.append(text_node(176 + length, y + 16, label, 14, INK, MONO, "700"))
    if spec.get("foot"):
        footer_lines(parts, spec["foot"], top + len(rows) * gap + 12, width)
    return parts


def viz_duel(spec, width):
    colors = spec.get("colors", [RED, BLUE])
    parts = [text_node(14, 24, spec["title"])]
    rows = spec["rows"]
    top, gap = 46, 52
    scale = (width - 210) / 70
    for index, row in enumerate(rows):
        y = top + index * gap
        parts.append(text_node(14, y + 14, row["label"], 13, INK, SANS, "600"))
        for offset, (key, color) in enumerate(zip(("a", "b"), colors, strict=False)):
            value = row[key]
            length = max(2, value * scale)
            bar_y = y + offset * 17
            parts.append(
                f'<rect x="190" y="{bar_y}" width="{length:.1f}" height="14" rx="2" fill="{color}"/>'
            )
            parts.append(
                text_node(196 + length, bar_y + 12, value, 13, INK, MONO, "700")
            )
    legend_y = top + len(rows) * gap + 6
    for offset, (name, color) in enumerate(zip(spec["legend"], colors, strict=False)):
        x = 14 + offset * 190
        parts.append(
            f'<rect x="{x}" y="{legend_y}" width="13" height="13" fill="{color}"/>'
        )
        parts.append(text_node(x + 20, legend_y + 12, name, 13, MUTED, MONO))
    return parts


def viz_gauge(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    track = width - 28
    scale = track / spec["total"]
    parts.append(
        f'<rect x="14" y="42" width="{track}" height="54" rx="3" fill="rgba(246,242,232,.10)"/>'
    )
    parts.append(
        f'<rect x="14" y="42" width="{spec["have"] * scale:.1f}" height="54" rx="3" fill="{BLUE_L}"/>'
    )
    need_x = 14 + spec["have"] * scale
    need_w = (spec["need"] - spec["have"]) * scale
    parts.append(
        f'<rect x="{need_x:.1f}" y="42" width="{need_w:.1f}" height="54" fill="none" '
        f'stroke="{LIME}" stroke-width="2" stroke-dasharray="6 4"/>'
    )
    parts.append(text_node(26, 78, spec["have"], 30, "#0b1420", BLACK))
    parts.append(
        text_node(need_x + need_w / 2, 78, "+10", 26, LIME, BLACK, anchor="middle")
    )
    half = 14 + spec["need"] * scale
    parts.append(
        f'<line x1="{half:.1f}" y1="32" x2="{half:.1f}" y2="108" stroke="{LIME}" stroke-width="2"/>'
    )
    parts.append(
        text_node(half, 126, "metade dos válidos", 12, LIME, MONO, anchor="middle")
    )
    footer_lines(parts, spec["foot"], 150, width)
    return parts


def viz_interval(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    lo, hi = -2.0, 12.0
    left, span = 150, width - 175
    scale = span / (hi - lo)
    zero = left + (0 - lo) * scale
    parts.append(
        f'<line x1="{zero:.1f}" y1="40" x2="{zero:.1f}" y2="170" stroke="{LIME}" stroke-width="2"/>'
    )
    parts.append(
        text_node(zero, 188, "zero, o empate", 12, LIME, MONO, anchor="middle")
    )
    for index, row in enumerate(spec["rows"]):
        y = 62 + index * 52
        parts.append(text_node(14, y + 6, row["label"], 13, INK, SANS, "600"))
        x0 = left + (row["lo"] - lo) * scale
        x1 = left + (row["hi"] - lo) * scale
        parts.append(
            f'<rect x="{x0:.1f}" y="{y - 9}" width="{x1 - x0:.1f}" height="18" rx="9" fill="{row["color"]}" opacity=".85"/>'
        )
        label = f'{row["lo"]:.2f} a {row["hi"]:.2f}'.replace(".", ",")
        parts.append(text_node(x0, y + 28, label, 12, INK, MONO, "700"))
    footer_lines(parts, spec["foot"], 210, width)
    return parts


def viz_equation(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    track = width - 200
    for index, row in enumerate(spec["rows"]):
        y = 44 + index * 44
        parts.append(text_node(14, y + 16, row["label"], 14, INK, SANS, "700"))
        parts.append(
            f'<rect x="120" y="{y}" width="{track}" height="22" fill="rgba(246,242,232,.10)"/>'
        )
        got = track * row["got"] / row["need"]
        parts.append(
            f'<rect x="120" y="{y}" width="{got:.1f}" height="22" fill="{BLUE}"/>'
        )
        missing = row["need"] - row["got"]
        label = (
            "fecha" if missing <= 0.01 else f"faltam {missing:.2f}".replace(".", ",")
        )
        color = LIME if missing <= 0.01 else RED_L
        parts.append(text_node(126 + track, y + 17, label, 13, color, MONO, "700"))
    footer_lines(parts, spec["foot"], 44 + len(spec["rows"]) * 44 + 8, width)
    return parts


def viz_stack(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    total = sum(item["value"] for item in spec["segments"])
    track = width - 28
    x = 14.0
    for item in spec["segments"]:
        w = track * item["value"] / total
        parts.append(
            f'<rect x="{x:.1f}" y="42" width="{w:.1f}" height="52" fill="{item["color"]}"/>'
        )
        value = f'{item["value"]:.2f}'.replace(".", ",")
        parts.append(text_node(x + 12, 76, value, 24, "#0b1420", BLACK))
        x += w
    y = 118
    for index, item in enumerate(spec["segments"]):
        parts.append(
            f'<rect x="14" y="{y + index * 24 - 11}" width="13" height="13" fill="{item["color"]}"/>'
        )
        parts.append(text_node(34, y + index * 24, item["label"], 13, MUTED, MONO))
    footer_lines(parts, spec["foot"], y + len(spec["segments"]) * 24 + 6, width)
    return parts


def viz_compression(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    parts.append(
        f'<rect x="14" y="44" width="{width * .40:.0f}" height="96" rx="4" fill="{BLUE}" opacity=".85"/>'
    )
    parts.append(text_node(30, 108, spec["left"]["value"], 52, "#fffefa", BLACK))
    parts.append(text_node(14, 162, spec["left"]["label"], 12, MUTED, MONO))
    right_x = width * 0.58
    parts.append(
        f'<rect x="{right_x:.0f}" y="44" width="{width * .28:.0f}" height="96" rx="4" fill="{RED}" opacity=".85"/>'
    )
    parts.append(
        text_node(right_x + 16, 108, spec["right"]["value"], 52, "#fffefa", BLACK)
    )
    parts.append(text_node(right_x, 162, spec["right"]["label"], 12, MUTED, MONO))
    parts.append(text_node(width * 0.50, 100, "→", 30, LIME, SANS, anchor="middle"))
    parts.append(
        text_node(
            width * 0.50, 132, spec["ratio"], 15, LIME, MONO, "700", anchor="middle"
        )
    )
    footer_lines(parts, spec["foot"], 186, width)
    return parts


def viz_timeline(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    for index, row in enumerate(spec["rows"]):
        y = 56 + index * 46
        parts.append(
            f'<circle cx="24" cy="{y - 5}" r="7" fill="{LIME if index == 2 else BLUE_L}"/>'
        )
        if index < len(spec["rows"]) - 1:
            parts.append(
                f'<line x1="24" y1="{y + 3}" x2="24" y2="{y + 34}" stroke="rgba(246,242,232,.3)" stroke-width="2"/>'
            )
        parts.append(text_node(44, y, row["date"], 14, LIME, MONO, "700"))
        parts.append(text_node(44, y + 20, row["text"], 14, INK, SANS))
    footer_lines(parts, spec["foot"], 56 + len(spec["rows"]) * 46, width)
    return parts


def viz_steps(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    for index, row in enumerate(spec["rows"]):
        y = 54 + index * 38
        parts.append(
            f'<rect x="14" y="{y - 18}" width="26" height="26" rx="3" fill="{LIME}"/>'
        )
        parts.append(text_node(27, y, index + 1, 15, "#1e2405", BLACK, anchor="middle"))
        parts.append(text_node(52, y, row, 15, INK, SANS, "600"))
    return parts


def viz_checklist(spec, width):
    parts = [text_node(14, 24, spec["title"])]
    for index, row in enumerate(spec["rows"]):
        y = 54 + index * 34
        color = GREEN if row["ok"] else RED
        mark = "✓" if row["ok"] else "✕"
        parts.append(
            f'<rect x="14" y="{y - 15}" width="22" height="22" rx="3" fill="{color}" opacity=".2"/>'
        )
        parts.append(
            text_node(25, y + 1, mark, 15, color, SANS, "700", anchor="middle")
        )
        parts.append(
            text_node(46, y, row["text"], 14, INK if row["ok"] else MUTED, SANS, "600")
        )
    return parts


RENDERERS = {
    "bars": viz_bars,
    "duel": viz_duel,
    "gauge": viz_gauge,
    "interval": viz_interval,
    "equation": viz_equation,
    "stack": viz_stack,
    "compression": viz_compression,
    "timeline": viz_timeline,
    "steps": viz_steps,
    "checklist": viz_checklist,
}


def render_viz(spec, label):
    width, height = 620, 340
    parts = RENDERERS[spec["type"]](spec, width)
    body = "".join(parts)
    return f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{esc(label)}">{body}</svg>'


def parse_posts(text: str) -> list[dict]:
    posts = []
    blocks = re.split(r"\n## Post ", text)[1:]
    for block in blocks:
        number = block.split("/", 1)[0].strip()
        found_title = re.search(r"\*\*Título:\*\*\s*(.+)", block)
        found_highlight = re.search(r"\*\*Destaque:\*\*\s*(.+)", block)
        if not found_title or not found_highlight:
            raise ValueError(f"Post {number} sem título ou destaque")
        title = found_title.group(1).strip()
        highlight = found_highlight.group(1).strip()
        body = block.split("**Texto:**", 1)[1]
        body = body.split("\n---", 1)[0].strip()
        posts.append(
            {
                "number": int(number),
                "title": title,
                "highlight": highlight,
                "text": body,
            }
        )
    return posts


def build(posts: list[dict]) -> str:
    if len(posts) != len(CARDS):
        raise ValueError(f"{len(posts)} posts para {len(CARDS)} cards")
    chunks = [HEAD]
    total = len(posts)
    for post, card in zip(posts, CARDS, strict=False):
        number = post["number"]
        lead = post["text"].split("\n\n")[0]
        photo = card["photo"]
        pos = card.get("pos", "center")
        chips = "".join(
            f'<span class="kchip {kind}">{esc(label)}</span>'
            for kind, label in card["chips"]
        )
        viz = render_viz(card["viz"], f'{card["viz"]["title"]}, post {number}')
        chars = len(post["text"])
        copy_text = esc(post["text"])
        chunks.append(f"""
<section class="post">
  <div class="post-label">Post {number}/{total} · {esc(card["kicker"])} · <b>{esc(post["highlight"])}</b></div>
  <div class="card" style="--photo:url('{photo}');--pos:{pos}">
    <div class="card-head"><div class="brand"><img src="img/arvor_logo.png" alt="Arvor"><div><b>Arvor Intelligence</b><span>@leonardodias · perícia eleitoral</span></div></div><div class="pno">{number}/{total}</div></div>
    <div class="card-body">
      <div>
        <span class="lead-tag">{esc(card["tag"])}</span>
        <p class="metric">{esc(post["highlight"])}</p>
        <h2>{esc(post["title"])}</h2>
        <p class="t">{esc(lead)}</p>
        <div class="kchips">{chips}</div>
      </div>
      <div class="viz">{viz}</div>
    </div>
    <div class="card-foot"><span>{esc(card["foot"][0])}</span><span>{esc(card["foot"][1])}</span></div>
  </div>
  <div class="copy"><span class="cc">{chars} chars</span>{copy_text}</div>
  <button class="copy-btn" onclick="cp(this)">Copiar texto</button>
</section>
""")
    chunks.append(FOOT_TEMPLATE)
    return "".join(chunks)


def check(page: str, posts: list[dict]) -> dict:
    if "—" in page:
        raise ValueError("Travessão encontrado na thread")
    lengths = [len(post["text"]) for post in posts]
    if max(lengths) > 1900:
        raise ValueError(f"Post longo demais: {max(lengths)} caracteres")
    strategy = json.loads(STRATEGY.read_text())
    single = strategy["single_round"]
    if single["points_needed"] != 10.0:
        raise ValueError("Camada estratégica divergente da thread")
    return {
        "posts": len(posts),
        "chars_min": min(lengths),
        "chars_max": max(lengths),
        "chars_total": sum(lengths),
        "points_needed": single["points_needed"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    posts = parse_posts(SOURCE.read_text())
    page = build(posts)
    summary = check(page, posts)
    args.output.write_text(page)
    summary["output"] = str(args.output.relative_to(ROOT))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
