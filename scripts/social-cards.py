#!/usr/bin/env python3
"""Gera todos os social cards do acervo a partir de um manifesto único.

Antes existiam três convenções ao mesmo tempo: uma galeria com ramificação por
query string (docs/social.html?card=...), fontes soltas em docs/assets/og_*.html
e imagens espalhadas em três padrões de caminho, com metade das páginas sem card
nenhum. Este script substitui as três.

    python3 scripts/social-cards.py            gera HTML e renderiza os PNG
    python3 scripts/social-cards.py --html     só regrava o HTML de cada card
    python3 scripts/social-cards.py --only pnad proposta

Saída: docs/assets/og/<slug>.html (fonte) e docs/img/og/<slug>.png (1200x630).
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCE_DIR = DOCS / "assets/og"
IMAGE_DIR = DOCS / "img/og"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 8799

ACCENTS = {
    "lime": "#d9ff43",
    "blue": "#74a2ff",
    "red": "#ef3e36",
    "amber": "#e8a33d",
}

# Cada card: título curto, uma linha de leitura e até três números que o dossiê
# sustenta. Os textos vêm das fichas revisadas do acervo em docs/index.html.
CARDS: list[dict] = [
    {
        "slug": "hub",
        "eyebrow": "Arvor Intelligence · acervo aberto",
        "title": "Toda pesquisa",
        "title_em": "deixa rastro",
        "lede": "Quinze auditorias de pesquisas eleitorais recalculadas contra a fonte oficial: <b>TSE</b> para o eleitorado, <b>IBGE/PNAD</b> para renda e escolaridade.",
        "stats": [
            ("15", "auditorias"),
            ("4", "institutos"),
            ("0", "acusações de fraude"),
        ],
        "foot": "prova de opacidade, não de fraude",
        "accent": "lime",
        "photo": "img/atlas_072026/web/urna-fila.jpg",
    },
    {
        "slug": "pnad",
        "eyebrow": "O Brasil em Números · PNAD Contínua",
        "title": "O país que",
        "title_em": "os dados mostram",
        "lede": "Quinze painéis sobre renda, trabalho, escolaridade e domicílio, direto dos microdados do IBGE, com pesos oficiais e réplicas.",
        "stats": [("15", "painéis"), ("200", "réplicas"), ("PT/EN", "duas línguas")],
        "foot": "microdados PNAD Contínua · IBGE",
        "accent": "blue",
        "photo": "img/atlas_072026/web/feira.jpg",
    },
    {
        "slug": "proposta",
        "eyebrow": "Minutas de uso livre · Resolução e PL",
        "title": "Auditar sem propor",
        "title_em": "é reclamar",
        "lede": "O Pacote Público de Auditoria como condição de divulgação: questionário integral, bases, pesos, <b>deff</b> e taxas de resposta.",
        "stats": [
            ("2", "minutas prontas"),
            ("0", "pedido de crédito"),
            ("1", "exigência"),
        ],
        "foot": "texto livre para qualquer parlamentar, partido ou o próprio TSE",
        "accent": "lime",
        "photo": "img/atlas_072026/web/congresso.jpg",
    },
    {
        "slug": "datafolha_082026",
        "eyebrow": "Datafolha · 21/08/2026 · BR-04496/2026",
        "title": "47×43 é o publicado.",
        "title_em": "A renda troca o sinal.",
        "lede": "Alinhar só a renda à PNADC leva o segundo turno a <b>Lula 44,2 × 46,0 Flávio</b>. Sensibilidade, não recontagem.",
        "stats": [
            ("−1,78", "gap após renda PNADC"),
            ("1,27:1", "consolidação fora das bases"),
            ("47%", "sem partido"),
        ],
        "foot": "auditoria independente · n = 2.058 · ponto de fluxo",
        "accent": "red",
        "photo": "img/atlas_072026/web/eleicao-rua.jpg",
    },
    {
        "slug": "nexus_btg_240826",
        "eyebrow": "BTG/Nexus · 24/08/2026 · BR-09028/2026",
        "title": "Há um roteiro.",
        "title_em": "Falta o log.",
        "lede": "O relato não prova indução. O questionário cria testes. A renda da PNADC <b>muda o sinal</b> do segundo turno.",
        "stats": [
            ("−0,43", "gap com a PNADC"),
            ("4", "respostas ausentes"),
            ("5", "transferências medidas"),
        ],
        "foot": "auditoria independente · n = 2.006 · CATI/RDD",
        "accent": "amber",
        "duo": True,
        "duo_values": ("46", "45"),
    },
    {
        "slug": "nexus_btg_082026_1",
        "eyebrow": "BTG/Nexus · 03/08/2026 · BR-02874/2026",
        "title": "A margem que",
        "title_em": "troca o sinal",
        "lede": "Quatro margens estão travadas por cota e não podem mover o placar. As duas sem cota erram sete vezes mais e puxam para lados opostos.",
        "stats": [
            ("−1,7", "gap com a renda da PNAD"),
            ("8,7%", "erro sem cota"),
            ("0,2%", "erro com cota"),
        ],
        "foot": "auditoria independente · n = 2.002 · CATI/RDD",
        "accent": "lime",
        "duo": True,
        "duo_values": ("41", "37"),
    },
    {
        "slug": "nexus_btg_082026_1_thread",
        "eyebrow": "Thread · BTG/Nexus 03/08/2026",
        "title": "Troque uma linha",
        "title_em": "e o vencedor muda",
        "lede": "Vinte e seis posts com a conta aberta: a fórmula, a cascata faixa a faixa, o teorema das margens e a transferência que o instituto mediu.",
        "stats": [("26", "posts"), ("23", "gráficos"), ("1", "fórmula")],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "atlas_072026",
        "eyebrow": "AtlasIntel/Bloomberg · 07/2026 · BR-08602/2026",
        "title": "O pai: 42,3.",
        "title_em": "O filho: 35,8.",
        "lede": "Mesma amostra, mesma semana, mesmo questionário. Os <b>6,5 pontos</b> que separam Jair de Flávio não foram para Lula: <b>0,5</b> foram.",
        "stats": [
            ("24,7", "fugiram p/ a direita"),
            ("−20,3", "direita não bolsonarista"),
            ("±1,38", "piso real da margem"),
        ],
        "foot": "auditoria independente · n = 5.021 · painel online",
        "accent": "lime",
        "duo": True,
        "duo_values": ("44,9", "35,8"),
    },
    {
        "slug": "atlas_072026_thread",
        "eyebrow": "Thread · AtlasIntel 07/2026",
        "title": "A amostra que",
        "title_em": "o algoritmo escolhe",
        "lede": "O questionário guarda identificadores de clique do Google Ads. Uma amostra online autosselecionada descreve quem a campanha digital alcança.",
        "stats": [
            ("31", "posts"),
            ("2,30×", "divergência em Renan"),
            ("0,99", "acordo nos dois grandes"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "datafolha_072026",
        "eyebrow": "Datafolha · 07/2026 · BR-01166/2026",
        "title": "48×43 é a manchete.",
        "title_em": "45×45 é o interior.",
        "lede": "Toda a vantagem nacional de Lula é metropolitana. No interior, onde vivem <b>1.217 dos 2.004</b> entrevistados, o placar está empatado.",
        "stats": [
            ("45×45", "interior"),
            ("118", "cidades fixas"),
            ("16,6 pp", "amostra mais pobre"),
        ],
        "foot": "auditoria independente · n = 2.004 · ponto de fluxo",
        "accent": "red",
        "photo": "img/atlas_072026/web/eleicao-rua.jpg",
    },
    {
        "slug": "datafolha_072026_thread",
        "eyebrow": "Thread · Datafolha 07/2026",
        "title": "O mapa se repete",
        "title_em": "de uma onda a outra",
        "lede": "Cento e trinta e nove municípios, <b>118 fixos nas três ondas</b> com a mesma cota. E 137 dos 139 de julho já estavam no anexo de junho.",
        "stats": [
            ("139", "municípios"),
            ("87,4%", "das entrevistas"),
            ("ρ=0,088", "apaga o 2º turno"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "quaest_globo_140826",
        "eyebrow": "Quaest/Globo · 14/08/2026 · BR-06773/2026",
        "title": "Faltam dez pontos.",
        "title_em": "E não estão com Lula.",
        "lede": "A imprensa leu empate técnico no segundo turno. O mesmo relatório traz a conta do primeiro: <b>83,3% da terceira via</b>, que mora exatamente onde Flávio já lidera.",
        "stats": [
            ("10,00", "pontos de voto válido"),
            ("81,2%", "da terceira via em campo amigo"),
            ("−4 × +18", "prêmio de inevitabilidade"),
        ],
        "foot": "auditoria independente · n = 2.004 · domiciliar",
        "accent": "blue",
        "duo": True,
        "duo_values": ("43", "40"),
    },
    {
        "slug": "quaest_globo_140826_thread",
        "eyebrow": "Thread · Quaest/Globo 14/08/2026",
        "title": "A conta que cabe",
        "title_em": "numa linha só",
        "lede": "Vinte posts com a fórmula aberta: os dez pontos que faltam, o voto infiel que o próprio instituto mediu e a trava que nenhuma manchete citou.",
        "stats": [
            ("12t + d + 0,5g", "a equação do turno único"),
            ("77%", "do voto de Zema pode mudar"),
            ("10,2 : 1", "compressão até a manchete"),
        ],
        "foot": "arvor intelligence · perícia eleitoral",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "quaest_082026",
        "eyebrow": "Quaest/Genial · 05/08/2026 · BR-06591/2026",
        "title": "O manual de campanha",
        "title_em": "que a Faria Lima pagou",
        "lede": "<b>55%</b> dizem que Lula não merece mais quatro anos. <b>39%</b> votam em Flávio. O vão não está com Lula: está fora da urna.",
        "stats": [
            ("7,43", "pontos sem destino"),
            ("5 × 12", "Flávio e Zema contra Lula"),
            ("51", "resultados ausentes"),
        ],
        "foot": "auditoria independente · n = 2.004 · domiciliar",
        "accent": "lime",
        "duo": True,
        "duo_values": ("44", "39"),
    },
    {
        "slug": "quaest_082026_thread",
        "eyebrow": "Thread · Quaest/Genial 08/2026",
        "title": "O mapa que a direita",
        "title_em": "ia jogar fora",
        "lede": "Vinte e dois posts com a conta aberta: o vão de 7,43 pontos, os quatro cenários na mesma amostra, a faixa de renda que decide e o balanço semântico das 109 perguntas.",
        "stats": [
            ("22", "posts"),
            ("4", "cenários medidos"),
            ("0", "perguntas sobre proposta"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "quaest_0726",
        "eyebrow": "Quaest/Genial · 17/07/2026",
        "title": "Vinte e oito perguntas",
        "title_em": "sem topline",
        "lede": "O suplemento acendeu 8 das 36 perguntas e reescreveu o texto de duas em relação ao instrumento registrado no TSE.",
        "stats": [
            ("36", "perguntas feitas"),
            ("28", "sem resultado"),
            ("2", "enunciados trocados"),
        ],
        "foot": "auditoria independente · n = 2.004 · domiciliar",
        "accent": "amber",
        "photo": "img/atlas_072026/web/urna-maquina.jpg",
    },
    {
        "slug": "quaest_0726_thread",
        "eyebrow": "Thread · Quaest/Genial 17/07/2026",
        "title": "O que foi perguntado",
        "title_em": "e nunca publicado",
        "lede": "A pergunta existe, foi aplicada a dois mil eleitores e o resultado não chegou ao público. O arquivo é o pedido.",
        "stats": [
            ("28", "perguntas na gaveta"),
            ("99,7%", "dos setores girou"),
            ("±2", "margem de vitrine"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "quaest_0726_slides",
        "eyebrow": "Apresentação · Quaest/Genial 17/07/2026",
        "title": "A auditoria",
        "title_em": "em slides",
        "lede": "O dossiê da Quaest de julho em formato de apresentação, com cada achado numa tela e a fonte no rodapé.",
        "stats": [
            ("1", "deck"),
            ("16:9", "pronto para tela"),
            ("0", "número sem fonte"),
        ],
        "foot": "brasil.arvor.co/quaest_0726_slides.html",
        "accent": "amber",
    },
    {
        "slug": "atlasintel_260626",
        "eyebrow": "AtlasIntel/Bloomberg · 26/06/2026 · BR-04582/2026",
        "title": "O “não sei”",
        "title_em": "quase desaparece",
        "lede": "Apenas <b>0,3%</b> não sabem quem os assusta mais. Numa amostra de cinco mil pessoas, é a impressão digital de um painel de escolha forçada.",
        "stats": [
            ("0,3%", "não sabem"),
            ("43,5×29,1", "mulheres e homens"),
            ("1 p.p.", "tolerância estourada"),
        ],
        "foot": "auditoria independente · n = 4.999 · painel RDR online",
        "accent": "amber",
        "photo": "img/atlas_072026/web/urna-maquina.jpg",
    },
    {
        "slug": "atlasintel_260626_thread",
        "eyebrow": "Thread · AtlasIntel 26/06/2026",
        "title": "O registro diz 5.000.",
        "title_em": "O relatório diz 4.999.",
        "lede": "Duas datas de campo e dois tamanhos de amostra para a mesma pesquisa, nos dois documentos do mesmo instituto.",
        "stats": [
            ("5.000", "no registro"),
            ("4.999", "no relatório"),
            ("1 dia", "de diferença"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "datafolha_062026",
        "eyebrow": "Datafolha · 24/06/2026",
        "title": "Lula 47 × 43",
        "title_em": "é empate técnico",
        "lede": "A margem da diferença é de cerca de <b>±4 pontos</b>, maior que os 4 pontos que separam os dois. A manchete não sobrevive à estatística.",
        "stats": [
            ("±4", "margem da diferença"),
            ("45,6×45,9", "com a renda da PNAD"),
            ("4", "pontos de vantagem"),
        ],
        "foot": "auditoria independente · n = 2.004 · ponto de fluxo",
        "accent": "red",
        "photo": "img/atlas_072026/web/urna-maquina.jpg",
    },
    {
        "slug": "datafolha_062026_thread",
        "eyebrow": "Thread · Datafolha 24/06/2026",
        "title": "A vantagem nasce",
        "title_em": "de uma amostra pobre",
        "lede": "Reponderando a renda da amostra à PNAD por pessoas de 16 anos ou mais, o placar de segundo turno vira <b>45,6 × 45,9</b>.",
        "stats": [
            ("45,6×45,9", "reponderado"),
            ("16+", "universo da régua"),
            ("1", "margem trocada"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "nexus_btg_0726",
        "eyebrow": "BTG/Nexus · 13/07/2026 · 6ª rodada",
        "title": "±2 é vitrine.",
        "title_em": "±4,18 é a conta.",
        "lede": "O próprio instituto chama de empate técnico. A vantagem muda de <b>+1,4 a +4,0</b> conforme a régua oficial usada para reponderar.",
        "stats": [
            ("47×44", "publicado"),
            ("±4,18", "margem da diferença"),
            ("+1,4 a +4,0", "conforme a régua"),
        ],
        "foot": "auditoria independente · n = 2.003 · CATI/RDD",
        "accent": "lime",
        "photo": "img/atlas_072026/web/urna-fila.jpg",
    },
    {
        "slug": "nexus_btg_0726_thread",
        "eyebrow": "Thread · BTG/Nexus 13/07/2026",
        "title": "O empate que",
        "title_em": "o release não diz",
        "lede": "A margem divulgada vale para cada percentual isolado, não para a diferença entre dois. A diferença carrega quase o dobro.",
        "stats": [
            ("±2", "no release"),
            ("±4,18", "na diferença"),
            ("2×", "a distância"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "nexus_btg_0726_slides",
        "eyebrow": "Apresentação · BTG/Nexus 13/07/2026",
        "title": "A sexta rodada",
        "title_em": "em slides",
        "lede": "O dossiê da 6ª rodada BTG/Nexus em formato de apresentação, um achado por tela.",
        "stats": [
            ("1", "deck"),
            ("16:9", "pronto para tela"),
            ("0", "número sem fonte"),
        ],
        "foot": "brasil.arvor.co/nexus_btg_0726_slides.html",
        "accent": "lime",
    },
    {
        "slug": "nexus_btg_150626",
        "eyebrow": "BTG/Nexus · 15/06/2026 · BR-06645/2026",
        "title": "A saída neutra",
        "title_em": "está marcada “não ler”",
        "lede": "Na pergunta do tarifaço, a opção que não empurra o entrevistado para um lado existe no questionário e o entrevistador é instruído a não lê-la.",
        "stats": [
            ("±2,7 a ±3,1", "margem plausível"),
            ("±6 a ±8", "recorte pequeno"),
            ("1", "opção não lida"),
        ],
        "foot": "auditoria independente · n = 2.017 · CATI/RDD",
        "accent": "amber",
        "photo": "img/atlas_072026/web/congresso.jpg",
    },
    {
        "slug": "nexus_btg_150626_thread",
        "eyebrow": "Thread · BTG/Nexus 15/06/2026",
        "title": "Perguntou o voto",
        "title_em": "antes do roteiro pesado",
        "lede": "O que o instituto fez certo merece registro na mesma régua do que fez errado. A ordem protege o topline; a margem publicada, não.",
        "stats": [
            ("1º", "o voto vem antes"),
            ("±2", "margem de vitrine"),
            ("0", "deff publicado"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "quaest_100626",
        "eyebrow": "Quaest/Genial · 10/06/2026 · BR-07661/2026",
        "title": "O melhor campo",
        "title_em": "torna a edição mais grave",
        "lede": "Domiciliar, sorteio por setor censitário, cotas claras. E perguntou a 2.004 eleitores sobre trocar Flávio e sobre Trump: nada foi publicado.",
        "stats": [
            ("±2", "divulgado"),
            ("±3 a ±3,5", "plausível"),
            ("2.004", "eleitores ouvidos"),
        ],
        "foot": "auditoria independente · n = 2.004 · domiciliar",
        "accent": "amber",
        "photo": "img/atlas_072026/web/urna-maquina.jpg",
    },
    {
        "slug": "x_thread",
        "eyebrow": "Thread · Quaest/Genial 10/06/2026",
        "title": "Perguntaram.",
        "title_em": "Não publicaram.",
        "lede": "Se Bolsonaro deveria trocar Flávio e o que o eleitor acha do apoio de Trump. Duas perguntas aplicadas, nenhum resultado divulgado.",
        "stats": [
            ("2", "perguntas guardadas"),
            ("2.004", "eleitores ouvidos"),
            ("0", "toplines publicados"),
        ],
        "foot": "cards prontos para publicar · brasil.arvor.co",
        "accent": "blue",
        "thread": True,
    },
    {
        "slug": "datafolha_090526",
        "eyebrow": "Datafolha · 09/05/2026",
        "title": "45 × 45",
        "title_em": "e a renda não bate",
        "lede": "Sexo, escolaridade e região colam na PNAD e no TSE. A faixa até dois salários mínimos dá <b>50,3%</b> na amostra contra 38,7% na PNAD.",
        "stats": [
            ("45×45", "segundo turno"),
            ("50,3 × 38,7", "renda contra a PNAD"),
            ("3", "datas que não fecham"),
        ],
        "foot": "auditoria independente · n = 2.004 · 139 municípios",
        "accent": "red",
        "photo": "img/atlas_072026/web/feira.jpg",
    },
    {
        "slug": "atlas_intel_180526",
        "eyebrow": "AtlasIntel/Bloomberg · 18/05/2026",
        "title": "Mais de vinte itens",
        "title_em": "saem sem topline",
        "lede": "O topline de voto está mais protegido do que parecia. Mas o relatório publica o que convém, e o ±1 anunciado não se sustenta.",
        "stats": [
            ("±1", "anunciado"),
            ("±1,38", "pior caso real"),
            ("20+", "itens sem topline"),
        ],
        "foot": "auditoria independente · n = 5.032 · RDR online",
        "accent": "amber",
        "photo": "img/atlas_072026/web/urna-fila.jpg",
    },
    {
        "slug": "margens_visuais",
        "eyebrow": "Ferramenta aberta · margens de erro",
        "title": "A margem que",
        "title_em": "você não vê",
        "lede": "Uma página para enxergar o que uma margem de erro significa antes de ler qualquer manchete de pesquisa.",
        "stats": [
            ("±2", "o que se anuncia"),
            ("±4", "o que a diferença carrega"),
            ("1", "conceito"),
        ],
        "foot": "brasil.arvor.co/margens_visuais.html",
        "accent": "blue",
    },
    {
        "slug": "artigo_pt",
        "eyebrow": "Artigo · Arvor Intelligence",
        "title": "Uma pesquisa que",
        "title_em": "não dá para refazer",
        "lede": "O texto que resume o método do acervo: o que é fato publicado, o que é inferência com conta aberta e o que continua fechado.",
        "stats": [("PT", "português"), ("EN", "também em inglês"), ("1", "método")],
        "foot": "brasil.arvor.co/artigo_pt.html",
        "accent": "lime",
    },
    {
        "slug": "artigo_en",
        "eyebrow": "Article · Arvor Intelligence",
        "title": "A poll you cannot",
        "title_em": "reproduce isn't science",
        "lede": "The method behind the archive: published fact, inference with the arithmetic shown, and everything the institutes still keep closed.",
        "stats": [("EN", "english"), ("PT", "also in portuguese"), ("1", "method")],
        "foot": "brasil.arvor.co/artigo_en.html",
        "accent": "lime",
    },
    {
        "slug": "artigo_quaest_100626",
        "eyebrow": "Artigo · Quaest/Genial 10/06/2026",
        "title": "As perguntas",
        "title_em": "que ficaram na gaveta",
        "lede": "O artigo sobre a rodada de junho da Quaest: o melhor campo do trio e a edição mais seletiva.",
        "stats": [
            ("2.004", "eleitores"),
            ("2", "perguntas guardadas"),
            ("0", "toplines"),
        ],
        "foot": "brasil.arvor.co/artigo_quaest_100626.html",
        "accent": "amber",
    },
    {
        "slug": "artigo_nexus_btg_150626",
        "eyebrow": "Artigo · BTG/Nexus 15/06/2026",
        "title": "A margem",
        "title_em": "que é vitrine",
        "lede": "O artigo sobre a 4ª rodada BTG/Nexus: sem efeito de desenho publicado, o ±2 da capa não descreve a pesquisa.",
        "stats": [("±2", "na capa"), ("±3,1", "plausível"), ("0", "deff publicado")],
        "foot": "brasil.arvor.co/artigo_nexus_btg_150626.html",
        "accent": "lime",
    },
]

TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Social card · {slug}</title>
<!-- Gerado por scripts/social-cards.py. Não edite à mão: edite o manifesto. -->
<link href="https://fonts.googleapis.com/css2?family=Archivo+Black&family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{width:1200px;height:630px;overflow:hidden;background:#07111f;color:#fffefa;font-family:Inter,system-ui,sans-serif}}
  .card{{position:relative;width:1200px;height:630px;display:grid;grid-template-columns:{columns};overflow:hidden}}
  .card::before{{content:"";position:absolute;inset:0;z-index:0;
    background:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px) 0 0/68px 68px,
               linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px) 0 0/68px 68px;
    -webkit-mask-image:linear-gradient(140deg,#000,transparent 78%)}}
  .left{{position:relative;z-index:2;padding:46px 40px 38px 56px;display:flex;flex-direction:column;justify-content:space-between}}
  .eyebrow{{display:inline-flex;align-items:center;gap:11px;align-self:flex-start;padding:8px 17px;
    border:1px solid rgba(255,255,255,.26);font-family:"IBM Plex Mono",monospace;font-size:15px;
    letter-spacing:.11em;text-transform:uppercase;color:{accent}}}
  .eyebrow i{{width:9px;height:9px;background:{accent};display:block}}
  h1{{font-family:"Archivo Black",sans-serif;font-size:{title_size}px;line-height:.9;letter-spacing:-.03em;
    margin:24px 0 0;text-transform:uppercase}}
  h1 em{{font-style:normal;color:{accent};display:block}}
  .lede{{font-size:21px;line-height:1.36;color:#c3cddd;max-width:{lede_width}px;margin-top:18px}}
  .lede b{{color:#fffefa}}
  .stats{{display:flex;gap:34px}}
  .stats b{{font-family:"Archivo Black",sans-serif;font-size:34px;letter-spacing:-.02em;line-height:1;display:block}}
  .stats span{{display:block;margin-top:6px;font-family:"IBM Plex Mono",monospace;font-size:13px;
    letter-spacing:.07em;text-transform:uppercase;color:#8a95a8}}
  .s0 b{{color:{accent}}}.s1 b{{color:#74a2ff}}.s2 b{{color:#ef3e36}}
  .foot{{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:22px;padding-top:15px;
    border-top:1px solid rgba(255,255,255,.2);font-family:"IBM Plex Mono",monospace;font-size:14.5px;color:#8a95a8}}
  .foot b{{color:{accent}}}
  .right{{position:relative;z-index:1;height:630px;border-left:1px solid rgba(255,255,255,.16);overflow:hidden}}
  .right img{{width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.18) brightness(.7)}}
  .right::after{{content:"";position:absolute;inset:0;background:{accent};opacity:.2;mix-blend-mode:color}}
  .duo{{display:grid;grid-template-rows:315px 315px}}
  .duo figure{{position:relative;height:315px;overflow:hidden}}
  .duo img{{filter:grayscale(.55) contrast(1.1) brightness(.82)}}
  .duo .l::after{{content:"";position:absolute;inset:0;background:#ef3e36;opacity:.34;mix-blend-mode:multiply}}
  .duo .f::after{{content:"";position:absolute;inset:0;background:#1b54f2;opacity:.34;mix-blend-mode:multiply}}
  .duo figcaption{{position:absolute;left:0;right:0;bottom:0;z-index:3;padding:40px 18px 18px;
    background:linear-gradient(transparent,rgba(0,0,0,.88));font-family:"IBM Plex Mono",monospace;
    font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#e7e3d8}}
  .duo figcaption b{{display:block;font-family:"Archivo Black",sans-serif;font-size:34px;letter-spacing:-.02em;color:#fff}}
  .tag{{position:absolute;top:0;right:0;z-index:4;padding:10px 20px;background:{accent};color:#07111f;
    font-family:"IBM Plex Mono",monospace;font-size:14px;font-weight:600;letter-spacing:.14em;text-transform:uppercase}}
</style>
</head>
<body>
  <div class="card">{tag}
    <div class="left">
      <div>
        <span class="eyebrow"><i></i>{eyebrow}</span>
        <h1>{title}{title_em}</h1>
        <p class="lede">{lede}</p>
      </div>
      <div>
        <div class="stats">{stats}</div>
        <div class="foot"><span>{foot}</span><span><b>brasil.arvor.co</b></span></div>
      </div>
    </div>{right}
  </div>
</body>
</html>
"""

DUO_PANEL = """
    <div class="right duo">
      <figure class="l"><img src="../../img/atlas_072026/web/lula.jpg" alt=""><figcaption>Lula<b>{left_value}</b></figcaption></figure>
      <figure class="f"><img src="../../img/atlas_072026/web/flavio.jpg" style="object-position:center 18%" alt=""><figcaption>Flávio<b>{right_value}</b></figcaption></figure>
    </div>"""


def render_card(card: dict) -> str:
    accent = ACCENTS[card.get("accent", "lime")]
    has_panel = bool(card.get("photo") or card.get("duo"))
    stats = "".join(
        f'<div class="s{i}"><b>{escape(value)}</b><span>{escape(label)}</span></div>'
        for i, (value, label) in enumerate(card.get("stats", []))
    )
    if card.get("duo"):
        values = card.get("duo_values", ("41", "37"))
        right = DUO_PANEL.format(left_value=values[0], right_value=values[1])
    elif card.get("photo"):
        right = (
            f'\n    <div class="right"><img src="../../{card["photo"]}" alt=""></div>'
        )
    else:
        right = ""
    title = escape(card["title"])
    title_em = f'<em>{escape(card["title_em"])}</em>' if card.get("title_em") else ""
    longest = max(len(card["title"]), len(card.get("title_em", "")))
    title_size = 68 if longest <= 20 else 58 if longest <= 26 else 50
    tag = '\n    <span class="tag">Thread</span>' if card.get("thread") else ""
    return TEMPLATE.format(
        slug=card["slug"],
        accent=accent,
        columns="1fr 392px" if has_panel else "1fr",
        lede_width=620 if has_panel else 900,
        title_size=title_size,
        eyebrow=escape(card["eyebrow"]),
        title=title,
        title_em=title_em,
        lede=card["lede"],
        stats=stats,
        foot=escape(card["foot"]),
        right=right,
        tag=tag,
    )


def write_sources(cards: list[dict]) -> None:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    for card in cards:
        (SOURCE_DIR / f"{card['slug']}.html").write_text(
            render_card(card), encoding="utf-8"
        )


def shoot(cards: list[dict]) -> list[str]:
    if not Path(CHROME).exists():
        sys.exit(f"Chrome não encontrado em {CHROME}")
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(PORT)],
        cwd=DOCS,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    done = []
    try:
        time.sleep(1.5)
        for card in cards:
            slug = card["slug"]
            target = IMAGE_DIR / f"{slug}.png"
            subprocess.run(
                [
                    CHROME,
                    "--headless",
                    "--disable-gpu",
                    "--hide-scrollbars",
                    "--window-size=1200,630",
                    "--virtual-time-budget=8000",
                    f"--screenshot={target}",
                    f"http://localhost:{PORT}/assets/og/{slug}.html",
                ],
                check=True,
                capture_output=True,
            )
            done.append(slug)
    finally:
        server.terminate()
    return done


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--html", action="store_true", help="só regrava as fontes HTML")
    parser.add_argument("--only", nargs="*", help="gera apenas estes slugs")
    args = parser.parse_args()

    cards = CARDS
    if args.only:
        wanted = set(args.only)
        cards = [card for card in CARDS if card["slug"] in wanted]
        missing = wanted - {card["slug"] for card in cards}
        if missing:
            sys.exit(f"slug desconhecido: {sorted(missing)}")

    write_sources(cards)
    report = {"cards": len(cards), "fontes": str(SOURCE_DIR)}
    if not args.html:
        report["renderizados"] = len(shoot(cards))
        report["imagens"] = str(IMAGE_DIR)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    if shutil.which("python3") is None:
        sys.exit("python3 não encontrado")
    main()
