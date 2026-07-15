#!/usr/bin/env python3
"""Gera docs/proposta.html a partir das minutas jurídicas do laudo BTG/Nexus.

A página de proposta existe para dar vida própria às duas peças normativas que
nascem no laudo `docs/nexus_btg_0726.html`: a Minuta de Resolução do TSE
(`id="resolucao"`) e o Projeto de Lei que altera a Lei 9.504/1997
(`id="projeto-lei"`). Parlamentares, jornalistas e o próprio Tribunal precisam
ler o texto normativo sem atravessar o laudo inteiro.

O texto jurídico NÃO é duplicado à mão: ele é extraído do laudo a cada build e
injetado num template institucional. Assim, editar o laudo é editar a proposta,
e as duas páginas nunca divergem.

Transformações aplicadas ao trecho extraído:

* remoção das classes de animação ``reveal`` (específicas do laudo);
* remoção da numeração de capítulo (``CAP. 16`` / ``CAP. 17``);
* ancoragem dos ``<h4>`` de artigo, para alimentar o sumário lateral;
* reescrita de âncoras internas: todo ``href="#id"`` cujo destino não exista na
  proposta vira link absoluto para o laudo (``nexus_btg_0726.html#id``).

Se um marcador não for encontrado, o script falha alto (``sys.exit``) em vez de
gerar uma página vazia ou truncada em silêncio.

Uso:
    python3 docs/build_proposta.py [--output docs/proposta.html]
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

DOCS = Path(__file__).resolve().parent
SOURCE = DOCS / "nexus_btg_0726.html"
DEFAULT_OUTPUT = DOCS / "proposta.html"
SOURCE_HREF = "nexus_btg_0726.html"

# Seções extraídas do laudo: (id no laudo, prefixo de âncora dos artigos).
SECTIONS: tuple[tuple[str, str], ...] = (
    ("resolucao", "res"),
    ("projeto-lei", "pl"),
)


class SectionExtractor(HTMLParser):
    """Localiza o intervalo de bytes de ``<section id="...">`` até seu fecho.

    Conta profundidade de ``<section>`` para suportar aninhamento e usa o
    parser da stdlib (em vez de regex sobre o documento inteiro) para não
    tropeçar em comentários ou atributos que contenham o texto procurado.
    """

    def __init__(self, html: str, target_id: str) -> None:
        super().__init__(convert_charrefs=False)
        self.html = html
        self.target_id = target_id
        self.start: int | None = None
        self.end: int | None = None
        self.depth = 0
        self._line_starts = _line_starts(html)

    def _offset(self) -> int:
        line, col = self.getpos()
        return self._line_starts[line - 1] + col

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "section" or self.end is not None:
            return
        if self.start is None:
            if dict(attrs).get("id") == self.target_id:
                self.start = self._offset()
                self.depth = 1
        else:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag != "section" or self.start is None or self.end is not None:
            return
        self.depth -= 1
        if self.depth == 0:
            self.end = self._offset() + len("</section>")


def _line_starts(text: str) -> list[int]:
    """Índice absoluto do primeiro caractere de cada linha."""
    starts = [0]
    for line in text.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    return starts


def extract_section(html: str, section_id: str) -> str:
    """Devolve o HTML bruto da seção, ou aborta com mensagem clara."""
    if f'id="{section_id}"' not in html:
        sys.exit(
            f'ERRO: marcador id="{section_id}" não existe em {SOURCE.name}. '
            "O laudo mudou de estrutura — corrija SECTIONS em build_proposta.py "
            "antes de publicar."
        )
    parser = SectionExtractor(html, section_id)
    parser.feed(html)
    parser.close()
    if parser.start is None:
        sys.exit(f'ERRO: <section id="{section_id}"> não foi localizado em {SOURCE.name}.')
    if parser.end is None:
        sys.exit(
            f'ERRO: <section id="{section_id}"> está aberta e sem </section> correspondente '
            f"em {SOURCE.name}. Recusando gerar página truncada."
        )
    fragment = html[parser.start : parser.end]
    if "<article class=" not in fragment:
        sys.exit(
            f'ERRO: a seção "{section_id}" não contém <article> com o texto normativo. '
            "Extração provavelmente incorreta — recusando gerar página incompleta."
        )
    return fragment


def slugify(text: str) -> str:
    """Converte um título de artigo em fragmento de âncora estável."""
    plain = unicodedata.normalize("NFKD", text)
    plain = plain.encode("ascii", "ignore").decode("ascii").lower()
    plain = re.sub(r"[^a-z0-9]+", "-", plain).strip("-")
    return plain or "art"


def strip_laudo_chrome(fragment: str) -> str:
    """Remove do trecho o que só faz sentido dentro do laudo."""
    # Classes de animação (`reveal` e seu estado `in`), preservando as demais.
    def _clean_class(match: re.Match[str]) -> str:
        kept = [c for c in match.group(1).split() if c not in {"reveal", "in"}]
        return f'class="{" ".join(kept)}"' if kept else ""

    fragment = re.sub(r'class="([^"]*)"', _clean_class, fragment)
    # Numeração de capítulo do laudo ("CAP. 16").
    fragment = re.sub(r'<span class="chapter-no">[^<]*</span>\s*', "", fragment)
    return fragment


def anchor_articles(fragment: str, prefix: str) -> tuple[str, list[tuple[str, str]]]:
    """Dá id a cada ``<h4>`` de artigo e devolve os itens do sumário."""
    items: list[tuple[str, str]] = []

    def _add_id(match: re.Match[str]) -> str:
        label = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        anchor = f"{prefix}-{slugify(label)}"
        items.append((anchor, label))
        return f'<h4 id="{anchor}">{match.group(1)}</h4>'

    fragment = re.sub(r"<h4>(.*?)</h4>", _add_id, fragment, flags=re.S)
    return fragment, items


def rewrite_internal_links(html: str) -> tuple[str, list[str]]:
    """Aponta para o laudo toda âncora cujo destino não exista nesta página."""
    local_ids = set(re.findall(r'id="([^"]+)"', html))
    rewritten: list[str] = []

    def _fix(match: re.Match[str]) -> str:
        target = match.group(1)
        if target in local_ids or target == "":
            return match.group(0)
        rewritten.append(target)
        return f'href="{SOURCE_HREF}#{target}"'

    html = re.sub(r'href="#([^"]*)"', _fix, html)
    return html, rewritten


def render_toc(groups: list[tuple[str, str, list[tuple[str, str]]]]) -> str:
    """Monta o sumário lateral a partir dos artigos realmente extraídos."""
    blocks = []
    for anchor, title, items in groups:
        links = "\n".join(
            f'          <li><a href="#{aid}">{label}</a></li>' for aid, label in items
        )
        blocks.append(
            f'        <p class="toc-group"><a href="#{anchor}">{title}</a></p>\n'
            f"        <ul>\n{links}\n        </ul>"
        )
    return "\n".join(blocks)


TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A proposta: duas minutas para tornar a pesquisa eleitoral auditável · Arvor</title>
  <meta name="description" content="Minuta de Resolução do TSE e Projeto de Lei que alteram a Resolução 23.600/2019 e a Lei 9.504/1997 para que pesos, bases, relatório completo e relação de municípios de uma pesquisa eleitoral sejam públicos antes da manchete — e não depois da eleição. Texto livre para uso.">
  <link rel="canonical" href="https://brasil.arvor.co/proposta.html">
  <link rel="icon" href="img/arvor_logo.png">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="Arvor Intelligence">
  <meta property="og:locale" content="pt_BR">
  <meta property="og:title" content="A proposta: duas minutas para tornar a pesquisa eleitoral auditável">
  <meta property="og:description" content="Uma Resolução que o TSE pode assinar hoje e um Projeto de Lei para o que exige reserva legal. O número sai com o pacote que permite conferi-lo. Texto aberto, sem pedido de crédito.">
  <meta property="og:url" content="https://brasil.arvor.co/proposta.html">
  <meta property="og:image" content="https://brasil.arvor.co/img/proposta_og.png">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="Proposta Arvor: que o número saia com a prova. Relatório completo em 2 dias, relação de municípios junto com o número, vigência imediata.">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="A proposta: duas minutas para tornar a pesquisa eleitoral auditável">
  <meta name="twitter:description" content="Transparência com data marcada para depois da eleição não é transparência; é arquivo. Duas minutas prontas para assinar.">
  <meta name="twitter:image" content="https://brasil.arvor.co/img/proposta_og.png">
  <meta name="twitter:image:alt" content="Proposta Arvor: que o número saia com a prova.">
  <link rel="stylesheet" href="assets/proposta.css">
</head>
<body>
  <div class="progress" aria-hidden="true"><i></i></div>
  <a class="skip-link" href="#minutas">Ir direto às minutas</a>

  <header class="hero">
    <div class="wrap">
      <div class="brand">
        <img src="img/arvor_logo.png" alt="" width="34" height="34">
        <span>Arvor Intelligence · Auditoria Eleitoral</span>
      </div>
      <p class="eyebrow">Proposta institucional · texto aberto</p>
      <h1>Que o número saia <em>com a prova</em></h1>
      <p class="deck">Toda auditoria que publicamos esbarra na mesma parede. A pesquisa é registrada, o número vira manchete — e o que permitiria conferir esse número (os pesos que esticam cada entrevista, as bases de cada recorte, o relatório completo, a relação das cidades onde se ouviu alguém) chega tarde demais ou nunca chega. Nada aqui exige mais do instituto do que ele já produz para entregar ao contratante. Exige apenas que chegue ao público <strong>antes da manchete</strong>, e não depois da eleição.</p>
      <p class="hero-back"><a href="index.html">&#8592; Acervo de auditorias da Arvor</a></p>
    </div>
  </header>

  <div class="shell wrap">
    <nav class="toc" aria-label="Sumário da proposta">
      <div class="toc-inner">
        <p class="toc-title">Nesta página</p>
        <p class="toc-group"><a href="#numeros">O problema em números</a></p>
        <p class="toc-group"><a href="#vias">As duas vias</a></p>
        <p class="toc-group"><a href="#pratica">O que muda na prática</a></p>
<!--TOC-->
        <p class="toc-group"><a href="#uso">Uso e origem</a></p>
      </div>
    </nav>

    <main class="doc">
      <section id="numeros" class="block" aria-labelledby="numeros-h">
        <p class="kicker">Por que existe esta proposta</p>
        <h2 id="numeros-h">O problema em números</h2>
        <p>Os quatro fatos abaixo saem da auditoria da 6ª rodada BTG/Nexus, divulgada em 13 de julho de 2026. Não são o pior caso do mercado: são o caso normal, feito por um instituto que cumpriu a regra. O problema é a regra.</p>
        <div class="facts">
          <div class="fact">
            <strong>12</strong>
            <p>respostas coletadas do eleitor e sem resultado público. Sete blocos do questionário foram perguntados e não voltaram como frequência — só como agregado ou cruzamento escolhido.</p>
          </div>
          <div class="fact">
            <strong>7 dias</strong>
            <p>é o prazo que o registro no PesqEle admite para entregar a relação dos municípios pesquisados, “até o sétimo dia seguinte à data de registro” (Resolução 23.600, art. 2º, § 7º). Nesta rodada: registro em <b>07/07</b>, divulgação em <b>13/07</b>, prazo até <b>14/07</b>. A manchete sai antes de o país saber onde a pesquisa foi feita.</p>
          </div>
          <div class="fact">
            <strong>depois<br>das eleições</strong>
            <p>é quando o art. 2º, § 7º-B da Resolução 23.600 manda publicizar o relatório completo. Transparência póstuma não protege o eleitor; só organiza o arquivo morto.</p>
          </div>
          <div class="fact">
            <strong>±4,18</strong>
            <p>é a margem de 95% da <em>diferença</em> entre dois candidatos com n = 2.003 — não o ±2 do release, que serve para uma porcentagem isolada. Uma vantagem de três pontos tem o zero dentro do intervalo.</p>
          </div>
        </div>
        <p class="src">Fatos e cálculos verificáveis em <a href="nexus_btg_0726.html">O empate que não dá para auditar</a> — auditoria BTG/Nexus, 6ª rodada.</p>
      </section>

      <section id="vias" class="block" aria-labelledby="vias-h">
        <p class="kicker">Desenho</p>
        <h2 id="vias-h">As duas vias</h2>
        <p>São duas peças porque são duas competências. A <strong>Minuta de Resolução</strong> fica dentro do que o TSE já pode regulamentar sozinho: publicidade imediata, relatório, pesos, bases, margem específica e correção cabem confortavelmente na regulamentação do registro, e valem sem esperar o Congresso.</p>
        <p>O <strong>Projeto de Lei</strong> resolve o que exige reserva legal. Microdados anonimizados e a declaração ampliada de relações econômicas podem ser questionados se vierem só por resolução — por isso a minuta preserva o ambiente seguro de auditoria e a lei dá a base robusta. O dever de terceiros (um veículo não divulgar resultado sem pacote público no ar) é matéria de lei por definição: a resolução só alcança quem se registra. O que ela pode fazer, faz — condiciona a própria divulgação ao depósito prévio do pacote.</p>
        <p>As duas peças são independentes e somáveis. O TSE pode assinar a resolução hoje sem prejuízo do projeto; o Congresso pode aprovar a lei sem esperar o Tribunal. Cada seção traz sua própria nota de competência.</p>
      </section>

      <section id="pratica" class="block" aria-labelledby="pratica-h">
        <p class="kicker">Antes e depois</p>
        <h2 id="pratica-h">O que muda na prática</h2>
        <p>Cada linha corresponde a um dispositivo do texto integral abaixo. Nenhuma foi inventada para o quadro.</p>
        <div class="table-wrap">
          <table class="compare">
            <caption class="sr-only">Comparação entre a regra vigente e a proposta, por tema</caption>
            <thead>
              <tr><th scope="col">Tema</th><th scope="col">Hoje</th><th scope="col">Proposta</th></tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Relatório completo</th>
                <td class="now">Público “depois das eleições” (Res. 23.600, art. 2º, § 7º-B).</td>
                <td class="new">Público até a primeira divulgação e, em qualquer hipótese, em no máximo <b>dois dias</b> do fim da coleta. <span class="ref">PL § 6º-A</span></td>
              </tr>
              <tr>
                <th scope="row">Relação de municípios</th>
                <td class="now">Pode ser entregue até o <b>7º dia</b> seguinte ao registro — depois da manchete.</td>
                <td class="new">Sai junto com o número, no mesmo ato, com o n de entrevistas de cada unidade. <span class="ref">PL § 6º e inc. XVII · Res. § 7º-K</span></td>
              </tr>
              <tr>
                <th scope="row">Divulgar sem pacote público</th>
                <td class="now">Livre. O registro prévio basta, ainda que nada auditável esteja no ar.</td>
                <td class="new">Enquanto o registro não for complementado, a pesquisa é <b>considerada não registrada</b>, e sua divulgação atrai a sanção que existe desde 1997. <span class="ref">PL §§ 6º-B e 6º-C · art. 33, § 3º</span></td>
              </tr>
              <tr>
                <th scope="row">Margem de erro</th>
                <td class="now">Uma margem só, de proporção isolada, aplicada a tudo — inclusive à diferença entre candidatos.</td>
                <td class="new">Intervalo próprio por estimativa, subgrupo e diferença; vedado aplicar a margem de uma proporção isolada à diferença. <span class="ref">Res. § 7º-I · PL inc. XII</span></td>
              </tr>
              <tr>
                <th scope="row">Pesos</th>
                <td class="now">Não publicados. Não se sabe o alvo, a fórmula nem quanto cada entrevista foi esticada.</td>
                <td class="new">Variáveis, alvos, distribuições bruta e final, fórmula, <i>trimming</i>, coeficiente de variação, efeito de desenho e n efetivo. <span class="ref">Res. § 7º-H · PL incs. VIII e IX</span></td>
              </tr>
              <tr>
                <th scope="row">Microdados</th>
                <td class="now">Inexistentes para o público. Ninguém refaz a conta.</td>
                <td class="new">Banco anonimizado em <b>48 horas</b>, com peso final, estrato e conglomerado, sob controle de divulgação estatística e LGPD. <span class="ref">Res. § 7º-N · PL § 9º</span></td>
              </tr>
              <tr>
                <th scope="row">Perguntas sem resultado</th>
                <td class="now">O questionário é público, mas o resultado de cada pergunta pode sumir do relatório.</td>
                <td class="new">Resultado completo de <b>toda</b> pergunta substantiva aplicada, ainda que não usada na comunicação principal. <span class="ref">Res. § 7º-G · PL inc. XI</span></td>
              </tr>
              <tr>
                <th scope="row">Vigência</th>
                <td class="now">—</td>
                <td class="new">A lei vale desde a publicação, para toda pesquisa divulgada a partir dali; a resolução, para o campo iniciado 30 dias depois. <span class="ref">PL art. 4º · Res. art. 4º</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div id="minutas" class="minutas">
        <p class="kicker">Texto integral</p>
        <h2 class="minutas-h">As duas minutas</h2>
        <p class="minutas-note">O texto abaixo é extraído automaticamente do laudo que o originou, a cada publicação desta página. Se divergir, é bug — e não versão.</p>
<!--RESOLUCAO-->
<!--PROJETO-LEI-->
      </div>

      <section id="uso" class="block" aria-labelledby="uso-h">
        <p class="kicker">Uso e origem</p>
        <h2 id="uso-h">Pegue e use</h2>
        <p>Este texto é livre. Qualquer parlamentar, partido, entidade científica, associação de imprensa, Ministério Público Eleitoral ou o próprio Tribunal Superior Eleitoral pode copiar, cortar, emendar, melhorar e apresentar como seu, no todo ou em parte, sem pedir autorização e sem citar a Arvor. Não há pedido de crédito, não há reserva de autoria e não há interesse comercial nenhum embutido aqui.</p>
        <p>Só pedimos uma coisa, e nem é para nós: se a proposta virar norma, que vire com o prazo intacto. É o prazo que faz a diferença entre transparência e arquivo.</p>
        <ul class="links">
          <li><a href="nexus_btg_0726.html">O laudo que originou a proposta &#8212; auditoria BTG/Nexus, 6ª rodada</a></li>
          <li><a href="https://github.com/ArvorCo/PNAD">Repositório público: dados, scripts e reprodução</a></li>
          <li><a href="index.html">Acervo completo de auditorias</a></li>
          <li><a href="mailto:ld@arvor.co">Correções e contestações: ld@arvor.co</a></li>
        </ul>
      </section>
    </main>
  </div>

  <footer>
    <div class="wrap">
      <div class="foot-brand"><img src="img/arvor_logo.png" alt="" width="34" height="34"><span>Arvor Intelligence</span></div>
      <p>A Arvor é uma empresa de tecnologia, não um think tank e não um partido. As críticas que originaram esta proposta são de método e de transparência: nenhum documento do nosso acervo afirma que houve fraude em qualquer pesquisa auditada. <strong>Prova de opacidade, não de fraude.</strong></p>
      <p>Auditoria independente baseada em documentos públicos, bases oficiais e cálculos reproduzíveis. Por <strong>Leonardo Dias</strong>, com apoio da Arvor. Última atualização: 15 de julho de 2026.</p>
    </div>
  </footer>

  <script>
    (function () {
      var bar = document.querySelector(".progress > i");
      if (!bar) return;
      var tick = function () {
        var h = document.documentElement;
        var max = h.scrollHeight - h.clientHeight;
        bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
      };
      addEventListener("scroll", tick, { passive: true });
      addEventListener("resize", tick);
      tick();
    })();
  </script>
</body>
</html>
"""


def build(output: Path) -> int:
    if not SOURCE.exists():
        sys.exit(f"ERRO: fonte não encontrada: {SOURCE}")
    html = SOURCE.read_text(encoding="utf-8")

    rendered: dict[str, str] = {}
    groups: list[tuple[str, str, list[tuple[str, str]]]] = []
    sizes: list[tuple[str, int, int]] = []

    for section_id, prefix in SECTIONS:
        raw = extract_section(html, section_id)
        fragment = strip_laudo_chrome(raw)
        fragment, items = anchor_articles(fragment, prefix)
        if not items:
            sys.exit(
                f'ERRO: nenhum artigo (<h4>) encontrado na seção "{section_id}". '
                "O sumário ficaria vazio — recusando gerar página degradada."
            )
        title_match = re.search(r"<h2[^>]*>(.*?)</h2>", fragment, flags=re.S)
        if not title_match:
            sys.exit(f'ERRO: seção "{section_id}" sem <h2> — não dá para montar o sumário.')
        title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
        rendered[section_id] = fragment
        groups.append((section_id, title, items))
        sizes.append((section_id, len(raw), len(fragment)))

    page = TEMPLATE
    page = page.replace("<!--TOC-->", render_toc(groups))
    page = page.replace("<!--RESOLUCAO-->", rendered["resolucao"])
    page = page.replace("<!--PROJETO-LEI-->", rendered["projeto-lei"])
    page, rewritten = rewrite_internal_links(page)

    output.write_text(page, encoding="utf-8")

    print(f"proposta gerada: {output}")
    for section_id, raw_len, out_len in sizes:
        print(f"  · {section_id:<12} extraído {raw_len:>6} B → injetado {out_len:>6} B")
    print(f"  · sumário       {sum(len(i) for _, _, i in groups)} artigos")
    if rewritten:
        print(f"  · âncoras reescritas para o laudo: {', '.join(sorted(set(rewritten)))}")
    else:
        print("  · âncoras internas: nenhuma pendente de reescrita")
    print(f"  · total         {len(page.encode('utf-8'))} B")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="caminho do HTML gerado (padrão: docs/proposta.html)",
    )
    args = parser.parse_args()
    return build(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
