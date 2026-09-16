#!/usr/bin/env python3
"""Camada de campanha dos dossies nacionais de setembro de 2026.

Os tres dossies de 14/09 auditam o placar e a composicao. Este modulo acrescenta
a cada um o capitulo que a campanha usa: onde esta o voto, por regiao e por
renda, qual e o tema de cada estado e qual e o teto enderecavel medido nas
pesquisas estaduais do mesmo periodo.

O capitulo e autocontido: leva o proprio CSS num `<style>` com escopo em
`.camada-campanha`, para funcionar sobre as tres folhas diferentes dos dossies.

Usado por:
    scripts/datafolha-14092026-build.py
    scripts/nexus-btg-140926-build.py
    scripts/quaest-140926-build.py
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets"

EST = json.loads((ASSETS / "estaduais_092026_data.json").read_text())
DFX = json.loads((ASSETS / "datafolha_14092026_cruzamentos.json").read_text())
NEX = json.loads((ASSETS / "nexus_btg_140926_data.json").read_text())

VAO = {v["uf"]: v for v in EST["vaos"]}
CAP = {c["municipio"]: c for c in EST["capitais"]}
NV = EST["nao_visitados"]
NE = EST["concentracao"]["nordeste"]

CSS = """
.camada-campanha{--cc-line:rgb(128 128 128 / 28%);--cc-dim:#5f6773;--cc-lula:#c8412f;--cc-flavio:#2f6fae;--cc-gold:#7d5b00;--cc-ok:#0c7a72;--cc-lula-txt:#b02f21}
.camada-campanha .cc-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px;margin:22px 0}
.camada-campanha .cc-card{border:1px solid var(--cc-line);border-radius:6px;padding:14px 16px}
.camada-campanha .cc-card b{display:block;font-size:1.7rem;line-height:1.05;font-weight:800}
.camada-campanha .cc-card span{display:block;font-size:.86rem;color:var(--cc-dim);margin-top:6px;line-height:1.45}
.camada-campanha .cc-bars{margin:22px 0;display:grid;gap:9px}
.camada-campanha .cc-row{display:grid;grid-template-columns:132px minmax(0,1fr) 84px;gap:12px;align-items:center}
.camada-campanha .cc-row>i{font-style:normal;font-size:.9rem;font-weight:600}
.camada-campanha .cc-track{display:flex;height:26px;border-radius:4px;overflow:hidden;background:rgb(128 128 128 / 16%)}
.camada-campanha .cc-seg{display:block;height:100%;display:flex;align-items:center;justify-content:center;font-family:ui-monospace,monospace;font-size:.78rem;font-weight:700;color:#fff}
.camada-campanha .cc-tail{font-family:ui-monospace,monospace;font-size:.84rem;font-weight:700;text-align:right}
.camada-campanha .cc-note{border-left:3px solid var(--cc-gold);padding:12px 16px;margin:22px 0;font-size:.95rem;background:rgb(128 128 128 / 9%)}
.camada-campanha .cc-legend{font-family:ui-monospace,monospace;font-size:.76rem;color:var(--cc-dim);margin:6px 0 0}
.camada-campanha ol.cc-rota{padding-left:20px;max-width:78ch}
.camada-campanha ol.cc-rota li{margin:0 0 10px}
"""


def esc(value) -> str:
    return html.escape(str(value))


def fmt(value, digits=0) -> str:
    return f"{value:,.{digits}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def sgn(value, digits=0) -> str:
    rounded = round(value, digits)
    return ("+" if rounded > 0 else "") + fmt(rounded, digits)


def card(valor: str, texto: str, cor: str = "") -> str:
    estilo = f' style="color:{cor}"' if cor else ""
    return f'<div class="cc-card"><b{estilo}>{esc(valor)}</b><span>{esc(texto)}</span></div>'


def duelo(rotulo: str, esquerda: int, direita: int, cauda: str, cor_cauda: str) -> str:
    total = esquerda + direita or 1
    we = 100 * esquerda / total
    return (
        f'<div class="cc-row"><i>{esc(rotulo)}</i><span class="cc-track">'
        f'<b class="cc-seg" style="width:{we:.1f}%;background:var(--cc-lula)">{esquerda}</b>'
        f'<b class="cc-seg" style="width:{100 - we:.1f}%;background:var(--cc-flavio)">{direita}</b>'
        f'</span><span class="cc-tail" style="color:{cor_cauda}">{esc(cauda)}</span></div>'
    )


def rota_curta() -> str:
    manaus, belem, salvador = CAP["Manaus"], CAP["Belém"], CAP["Salvador"]
    recife, fortaleza = CAP["Recife"], CAP["Fortaleza"]
    return f"""
<ol class="cc-rota">
<li><b>Manaus.</b> {fmt(manaus["bolsonaro_2t"])} votos de Bolsonaro em 2022, {fmt(manaus["bolsonaro_2t_pct"], 1)}% do 2º turno, o maior estoque das duas regiões, em estado sem visita da campanha até 14/09.</li>
<li><b>Belém e São Luís.</b> {fmt(belem["bolsonaro_2t"])} e {fmt(CAP["São Luís"]["bolsonaro_2t"])} votos. O Pará é o único grande colégio da região já competitivo na disputa presidencial.</li>
<li><b>Salvador e a Região Metropolitana do Recife.</b> {fmt(salvador["bolsonaro_2t"])} e {fmt(recife["bolsonaro_2t"])} votos nas duas capitais, contra {VAO["BA"]["vao_1t"]} e {VAO["PE"]["vao_1t"]} pontos de vão estadual.</li>
<li><b>Maceió e Aracaju.</b> Maceió é a capital nordestina em que Bolsonaro mais foi longe, {fmt(CAP["Maceió"]["bolsonaro_2t_pct"], 1)}%, e Alagoas e Sergipe seguem sem visita.</li>
<li><b>Fortaleza com o palanque estadual na frente.</b> {fmt(fortaleza["bolsonaro_2t"])} votos e o maior vão do país, {VAO["CE"]["vao_1t"]} pontos, mas rejeição de 60% à candidatura presidencial na região.</li>
</ol>
<p class="cc-legend">Juízo editorial declarado, com o número ao lado de cada movimento. Sem datas: a ordem é de prioridade.</p>
"""


def bloco_vao() -> str:
    linhas = "".join(
        f'<div class="cc-row"><i>{esc(v["uf"])} {esc(v["candidato"])}</i>'
        f'<span class="cc-track">'
        f'<b class="cc-seg" style="width:{100 * v["flavio_1t"] / 62:.1f}%;background:var(--cc-flavio)">{v["flavio_1t"]}</b>'
        f'<b class="cc-seg" style="width:{100 * (v["gov"] - v["flavio_1t"]) / 62:.1f}%;background:var(--cc-ok)">{v["gov"]}</b>'
        f'</span><span class="cc-tail" style="color:var(--cc-ok)">{sgn(v["vao_1t"])} pts</span></div>'
        for v in EST["vaos"][:6]
    )
    return (
        f'<div class="cc-bars">{linhas}</div>'
        '<p class="cc-legend">Azul: Flávio no 1º turno presidencial. Verde: melhor candidatura de direita ao governo do estado, '
        "na mesma entrevista. Quaest, relatórios estaduais de agosto e setembro.</p>"
    )


def capitulo_datafolha() -> str:
    regiao = DFX["tabelas"]["turno2_flavio"]["blocks"]["bloco3"]["rows"]
    rej = DFX["tabelas"]["rejeicao"]["blocks"]["bloco3"]["rows"]
    aprov = DFX["tabelas"]["aprovacao"]["blocks"]["bloco3"]["rows"]
    linhas = "".join(
        duelo(
            nome.replace("Centro-Oeste/Norte", "CO / Norte"),
            regiao["Lula (PT)"][nome],
            regiao["Flavio Bolsonaro (PL)"][nome],
            f'rejeição {rej["Flavio Bolsonaro (PL)"][nome]}%',
            "var(--cc-lula-txt)",
        )
        for nome in ("Nordeste", "Sudeste", "Centro-Oeste/Norte", "Sul")
    )
    urbano = "".join(
        duelo(
            nome.replace("Regiao metropolitana", "Metrópole"),
            regiao["Lula (PT)"][nome],
            regiao["Flavio Bolsonaro (PL)"][nome],
            f'aprovação {aprov["Aprova"][nome]}%',
            "var(--cc-dim)",
        )
        for nome in ("Regiao metropolitana", "Interior")
    )
    return f"""<style>{CSS}</style>
<div class="camada-campanha">
<div class="cc-grid">
{card(f'{rej["Flavio Bolsonaro (PL)"]["Nordeste"]}%', "rejeitam Flávio no Nordeste, contra 32% que rejeitam Lula", "var(--cc-lula-txt)")}
{card(f'{regiao["Flavio Bolsonaro (PL)"]["Sul"]}', "para Flávio no Sul, o espelho exato do Nordeste", "var(--cc-flavio)")}
{card("43 · 43 · 45", "Flávio na capital, na região metropolitana e no interior: a fratura é regional, não urbana")}
{card(f'{aprov["Aprova"]["Nordeste"] - aprov["Aprova"]["Sul"]} pts', "de diferença na aprovação do governo entre Nordeste e Sul")}
</div>
<h3>O 2º turno por região, com a rejeição ao lado</h3>
<div class="cc-bars">{linhas}</div>
<p class="cc-legend">Vermelho: Lula. Azul: Flávio. Datafolha 14/09, p. 48, 49 e 57.</p>
<h3>Metrópole e interior quase não se separam</h3>
<div class="cc-bars">{urbano}</div>
<div class="cc-note"><b>O que isto quer dizer para o calendário.</b> O teto do Nordeste não é de exposição, é de rejeição declarada: 60% contra 32%.
Onde a rejeição é dessa ordem, a candidatura presidencial não abre agenda, e quem abre é o nome estadual. As pesquisas estaduais do mesmo período
medem o tamanho desse nome: o vão chega a {VAO["CE"]["vao_1t"]} pontos no Ceará e {VAO["BA"]["vao_1t"]} na Bahia.</div>
{bloco_vao()}
<h3>Onde está o voto que falta</h3>
<p>{NE["metade_em"]} municípios de {fmt(NE["municipios"])} concentram metade de todo o voto que Bolsonaro teve no Nordeste em 2022, e os maiores estoques são capitais.
Dez estados ficaram fora do roteiro da pré-campanha até 14/09, somando {fmt(NV["eleitores_2026"] / 1e6, 1)} milhões de eleitores e {fmt(NV["bolsonaro_2t"])} votos de Bolsonaro.</p>
{rota_curta()}
<p class="cc-legend">Base municipal e método no <a href="estaduais_092026.html">atlas estadual de setembro</a>. Versão em cards: <a href="superthread_092026.html">a thread</a>.</p>
</div>"""


def capitulo_nexus() -> str:
    t34 = NEX["profile_tables"]["34"]
    t33 = NEX["profile_tables"]["33"]
    t76 = NEX["profile_tables"]["76"]
    faixas = [
        (t34[i]["label"].split("  ")[-1].strip(), t34[i]["values"])
        for i in (1, 2, 3, 4)
    ]
    linhas = "".join(
        duelo(
            rotulo,
            valores[0],
            valores[1],
            sgn(valores[1] - valores[0]),
            "var(--cc-flavio)" if valores[1] > valores[0] else "var(--cc-lula-txt)",
        )
        for rotulo, valores in faixas
    )
    municipio = "".join(
        duelo(
            t76[i]["label"].split("  ")[-1].strip(),
            t76[i]["values"][0],
            t76[i]["values"][1],
            sgn(t76[i]["values"][1] - t76[i]["values"][0]),
            (
                "var(--cc-flavio)"
                if t76[i]["values"][1] > t76[i]["values"][0]
                else "var(--cc-lula-txt)"
            ),
        )
        for i in (13, 14, 15)
    )
    evang = t33[11]["values"]
    catol = t33[10]["values"]
    return f"""<style>{CSS}</style>
<div class="camada-campanha">
<div class="cc-grid">
{card(f'{sgn(faixas[2][1][1] - faixas[2][1][0])}', "vantagem de Flávio na faixa de 2 a 5 salários, a maior do país em tamanho", "var(--cc-flavio)")}
{card(f'{evang[1]} × {evang[0]}', "entre evangélicos no 1º turno: o recorte em que Flávio vai mais longe", "var(--cc-flavio)")}
{card(f'{catol[0]} × {catol[1]}', "entre católicos, o espelho do anterior", "var(--cc-lula-txt)")}
{card(f'{t76[15]["values"][1]} × {t76[15]["values"][0]}', "no interior, no 2º turno: o único dos quatro institutos em que o interior vira")}
</div>
<h3>O gradiente de renda no 1º turno</h3>
<div class="cc-bars">{linhas}</div>
<p class="cc-legend">Vermelho: Lula. Azul: Flávio. BTG/Nexus 14/09, p. 34.</p>
<h3>Capital, região metropolitana e interior no 2º turno</h3>
<div class="cc-bars">{municipio}</div>
<div class="cc-note"><b>O que isto quer dizer para o programa.</b> A faixa de 2 a 5 salários mínimos é a maior do país, 39,3% das pessoas de 16 anos ou mais pela PNAD,
e é onde a direita já ganha. Ela não é o topo: é o assalariado com carteira, o pequeno empresário e o motorista de aplicativo. Acima de cinco salários a vantagem
se perde de novo, {t34[4]["values"][0]} a {t34[4]["values"][1]}. Flávio ganha o miolo e perde as duas pontas.</div>
<h3>O teto enderecável medido nas estaduais</h3>
{bloco_vao()}
<p>Nas quinze pesquisas estaduais publicadas pela Quaest em agosto e setembro, a candidatura de direita ao governo do estado vai muito além da candidatura
presidencial na mesma entrevista. O sinal inverte no Acre e em Rondônia, onde Flávio tem mais voto que o candidato ao governo: o déficit é do Nordeste,
não do candidato.</p>
{rota_curta()}
<p class="cc-legend">Base municipal e método no <a href="estaduais_092026.html">atlas estadual de setembro</a>. Versão em cards: <a href="superthread_092026.html">a thread</a>.</p>
</div>"""


def capitulo_quaest() -> str:
    temas = {uf: dict(itens) for uf, itens in EST["temas"].items()}
    linhas_tema = "".join(
        f'<div class="cc-row"><i>{esc(uf)}</i><span class="cc-track">'
        + "".join(
            f'<b class="cc-seg" style="width:{valor}%;background:{cor}">{valor if valor >= 9 else ""}</b>'
            for valor, cor in (
                (temas[uf].get("Saúde", 0), "var(--cc-ok)"),
                (temas[uf].get("Violência", 0), "var(--cc-lula)"),
                (temas[uf].get("Infraestrutura", 0), "var(--cc-gold)"),
            )
        )
        + f'</span><span class="cc-tail">{esc(max(temas[uf], key=lambda k: temas[uf][k]))}</span></div>'
        for uf in ("CE", "BA", "PE", "MA", "AL", "PA", "AM", "TO")
    )
    return f"""<style>{CSS}</style>
<div class="camada-campanha">
<div class="cc-grid">
{card(f'{VAO["CE"]["vao_1t"]} pts', "de vão no Ceará entre a direita estadual e Flávio, na mesma entrevista", "var(--cc-ok)")}
{card(f'{VAO["PE"]["vao_2t"]} pts', "em Pernambuco na régua mais limpa: 2º turno estadual contra 2º turno presidencial", "var(--cc-ok)")}
{card(f'{fmt(CAP["Manaus"]["bolsonaro_2t"] / 1000)} mil', "votos de Bolsonaro em Manaus, o maior estoque do Norte e do Nordeste")}
{card(f'{NE["metade_em"]}', f'municípios de {fmt(NE["municipios"])} concentram metade do voto bolsonarista do Nordeste')}
</div>
<h3>A mesma casa publicou quinze pesquisas estaduais</h3>
<p>A Quaest que mede o país mede também os estados, e os dois conjuntos conversam. Onde a direita disputa o governo, ela chega a
{VAO["CE"]["gov"]}% no Ceará, {VAO["BA"]["gov"]}% na Bahia e {VAO["PE"]["gov"]}% em Pernambuco. Na mesma entrevista, a candidatura presidencial tem
{VAO["CE"]["flavio_1t"]}%, {VAO["BA"]["flavio_1t"]}% e {VAO["PE"]["flavio_1t"]}%. Não é diferença de amostra: é o mesmo questionário e o mesmo peso.</p>
{bloco_vao()}
<h3>O tema de cada estado, na pergunta aberta do próprio instituto</h3>
<div class="cc-bars">{linhas_tema}</div>
<p class="cc-legend">Verde: saúde. Vermelho: violência. Dourado: infraestrutura. A coluna da direita traz o tema mais citado. Quaest, relatórios estaduais.</p>
<div class="cc-note"><b>O que isto quer dizer para o discurso.</b> Segurança pública é o ativo mais forte do campo e tem retorno máximo no Ceará, onde
{temas["CE"]["Violência"]}% apontam violência como o maior problema do estado, e na Bahia, com {temas["BA"]["Violência"]}%. Em Roraima, no Tocantins e em Alagoas,
saúde vale de duas a cinco vezes mais. O mesmo discurso, no estado errado, responde a uma pergunta que quase ninguém fez.</div>
{rota_curta()}
<p class="cc-legend">Base municipal e método no <a href="estaduais_092026.html">atlas estadual de setembro</a>. Versão em cards: <a href="superthread_092026.html">a thread</a>.</p>
</div>"""


CAPITULOS = {
    "datafolha": capitulo_datafolha,
    "nexus": capitulo_nexus,
    "quaest": capitulo_quaest,
}


if __name__ == "__main__":
    for nome, builder in CAPITULOS.items():
        corpo = builder()
        assert "—" not in corpo, nome
        print(nome, len(corpo), "bytes")
