#!/usr/bin/env python3
"""Cobertura dos proprios contratantes nos dias anteriores ao campo de agosto.

O Datafolha de agosto de 2026 foi contratado pela Folha de S.Paulo e pela TV
Globo. Este modulo registra o que esses dois veiculos publicaram sobre o caso
que a pesquisa nao perguntou, entre 31 de julho e 19 de agosto de 2026, com
data e hora de publicacao.

A coleta e manual e reproduzivel: cada item foi lido nos buscadores dos
proprios veiculos, search.folha.uol.com.br e g1.globo.com/busca, com filtro de
periodo. As consultas estao declaradas em CONSULTAS e qualquer pessoa refaz.
Nada aqui e inferencia: sao titulos publicados, com carimbo de data do veiculo.

Uso:
  python3 scripts/datafolha-082026-cobertura.py

Saidas:
  analysis/datafolha_082026/cobertura.json
  docs/assets/datafolha_082026_cobertura.json
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis" / "datafolha_082026"
ASSETS = ROOT / "docs" / "assets"

CAMPO = {"inicio": "2026-08-18", "fim": "2026-08-19", "divulgacao": "2026-08-21"}

CONSULTAS = [
    {
        "veiculo": "Folha de S.Paulo",
        "url": "https://search.folha.uol.com.br/?q=Lulinha&periodo=personalizado&sd=25/07/2026&ed=17/08/2026",
        "resultados": 79,
        "nota": "busca do proprio jornal, termo Lulinha, de 25/07 a 17/08/2026",
    },
    {
        "veiculo": "Folha de S.Paulo",
        "url": "https://search.folha.uol.com.br/?q=INSS+Lulinha&periodo=personalizado&sd=01/08/2026&ed=17/08/2026",
        "resultados": 45,
        "nota": "busca do proprio jornal, termos INSS e Lulinha, de 01/08 a 17/08/2026",
    },
    {
        "veiculo": "G1",
        "url": "https://g1.globo.com/busca/?q=Lulinha&order=recent&from=2026-08-01&to=2026-08-17",
        "resultados": None,
        "nota": "busca do proprio portal, termo Lulinha, de 01/08 a 17/08/2026",
    },
]

# Cada item: data ISO, veiculo, titulo publicado, observacao.
LINHA_DO_TEMPO = [
    {
        "data": "2026-07-31",
        "veiculo": "G1",
        "titulo": "PF abre inquérito contra Lulinha: entenda o que está sendo investigado",
        "url": "https://g1.globo.com/politica/noticia/2026/07/31/pf-abre-inquerito-contra-lulinha-entenda-o-que-esta-sendo-investigado.ghtml",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-04",
        "hora": "12:35",
        "veiculo": "G1",
        "titulo": "Dino autoriza abertura do terceiro inquérito envolvendo Lulinha",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-05",
        "hora": "09:07",
        "veiculo": "Bom Dia Brasil, TV Globo",
        "titulo": "Dino autoriza terceiro inquérito contra Lulinha",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-10",
        "hora": "14:57",
        "veiculo": "Folha de S.Paulo, coluna",
        "titulo": "A CPMI do INSS será usada para reforçar o assunto Lulinha na campanha",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-11",
        "hora": "19:15",
        "veiculo": "Folha de S.Paulo, coluna",
        "titulo": "O espectro que ronda a eleição de 2026",
        "trecho": "O dos descontos ilegais do INSS já alcançou o entorno de Lula, com investigações envolvendo Lulinha e integrantes do governo e da campanha.",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-13",
        "hora": "22:06",
        "veiculo": "Folha de S.Paulo",
        "titulo": "Plano de Flávio Bolsonaro usa escândalo do INSS para desgastar Lula",
        "trecho": "Auxiliares do candidato apostam em Lulinha e no escândalo do INSS como pontos centrais de desgaste para Lula durante a campanha.",
        "fase": "antes do campo",
        "destaque": True,
    },
    {
        "data": "2026-08-14",
        "hora": "13:07",
        "veiculo": "Folha de S.Paulo",
        "titulo": "Lula diz não saber a verdade sobre caso Lulinha, mas que acredita no filho e quer investigação",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-14",
        "hora": "14:59",
        "veiculo": "G1",
        "titulo": "Lula diz confiar em Lulinha, mas afirma que não pedirá encerramento de investigação contra filho",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-16",
        "hora": "13:08",
        "veiculo": "Folha de S.Paulo",
        "titulo": "Flávio começa campanha em Copacabana e diz que país olha para Brasília com nojo",
        "trecho": "Ao atacar o governo Lula, disse que Lulinha teria transformado a Presidência em um balcão de negócios ao citar o caso do INSS.",
        "fase": "antes do campo",
    },
    {
        "data": "2026-08-17",
        "hora": "21:07",
        "veiculo": "Folha de S.Paulo",
        "titulo": "Amiga de Lulinha comprou joias para ex-chefe de gabinete de Lula, aponta PF",
        "fase": "véspera do campo",
        "destaque": True,
    },
    {
        "data": "2026-08-18",
        "veiculo": "Datafolha",
        "titulo": "Primeiro dia de campo do BR-04496/2026",
        "fase": "campo",
        "questionario": "Nenhuma pergunta sobre o caso, nem sobre qualquer outro fato.",
        "destaque": True,
    },
    {
        "data": "2026-08-21",
        "veiculo": "Folha e TV Globo",
        "titulo": "Divulgação da pesquisa: Lula 47, Flávio 43 no segundo turno",
        "fase": "divulgação",
    },
    {
        "data": "2026-08-23",
        "hora": "13:02",
        "veiculo": "Folha de S.Paulo",
        "titulo": "Casos Master, Dark Horse, INSS e Lulinha atravessam campanhas e põem holofotes sobre PF e tribunais",
        "trecho": "Corrupção se tornou tema central da eleição, enquanto ações da PF, do STF e do TSE afetam o xadrez eleitoral.",
        "fase": "depois da divulgação",
        "destaque": True,
    },
]

CONTRAPONTOS = [
    "A Folha noticia com intensidade os casos dos dois lados. A busca do próprio jornal devolve 377 resultados para Dark Horse e 79 para Lulinha. O desequilíbrio que este capítulo aponta não está na cobertura: está no questionário que a cobertura contratou.",
    "As mensagens da Polícia Federal que citam nominalmente o filho do presidente vieram a público em 20 de agosto, depois de o campo fechar. Uma bateria como a de maio precisaria de um documento que ainda não existia no dia 18. Esse é o melhor argumento de defesa do instituto e ele precisa estar aqui.",
    "Só que o caso não nasceu em 20 de agosto. O primeiro inquérito virou notícia no G1 em 31 de julho, o terceiro foi autorizado em 4 de agosto, e no dia 14 o próprio presidente falou publicamente sobre o assunto nos dois veículos contratantes. Em maio, o instituto transformou um fato da semana anterior em sete perguntas.",
]


def main() -> None:
    antes = [
        item for item in LINHA_DO_TEMPO if item["fase"].startswith(("antes", "véspera"))
    ]
    payload = {
        "pergunta": (
            "O que os dois contratantes da pesquisa publicaram sobre o caso nos dias "
            "anteriores ao campo, e o que a pesquisa perguntou sobre ele."
        ),
        "campo": CAMPO,
        "metodo": (
            "Coleta manual nos buscadores dos proprios veiculos, com filtro de periodo. "
            "As consultas estao declaradas e sao reproduziveis. Cada item traz o titulo "
            "publicado e o carimbo de data do veiculo."
        ),
        "consultas": CONSULTAS,
        "linha_do_tempo": LINHA_DO_TEMPO,
        "itens_antes_do_campo": len(antes),
        "perguntas_no_questionario_sobre_o_caso": 0,
        "contrapontos": CONTRAPONTOS,
        "leitura": (
            "Entre 31 de julho e 17 de agosto os dois veiculos que pagaram a pesquisa "
            "publicaram, com data e hora, a abertura de tres inqueritos, a fala do "
            "proprio presidente sobre o caso e a informacao de que o adversario faria "
            "dele eixo de campanha. O questionario aplicado nos dias 18 e 19 nao tem "
            "uma pergunta sobre isso. Dois dias depois da divulgacao, a Folha escreveu "
            "que corrupcao virou tema central da eleicao."
        ),
    }
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(payload, ensure_ascii=False, indent=2)
    (ANALYSIS / "cobertura.json").write_text(texto + "\n", encoding="utf-8")
    (ASSETS / "datafolha_082026_cobertura.json").write_text(
        texto + "\n", encoding="utf-8"
    )
    print(f"itens na linha do tempo: {len(LINHA_DO_TEMPO)}")
    print(f"publicados antes do campo pelos contratantes: {len(antes)}")
    for item in LINHA_DO_TEMPO:
        marca = " <-" if item.get("destaque") else ""
        print(
            f"  {item['data']} {item.get('hora', '     ')}  {item['veiculo'][:22]:<22} {item['titulo'][:62]}{marca}"
        )


if __name__ == "__main__":
    main()
