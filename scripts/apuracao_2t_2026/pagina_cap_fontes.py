"""Capítulo 16 do dossiê do 2º turno: fontes e reprodução.

Lista os scripts, cada JSON de `analysis/apuracao_2t_2026/dados/` (e os arquivos
da pasta acima: notícias e vídeo) com tamanho e SHA-256, os memorandos e os
comandos de reprodução. A lista é lida do disco, não digitada.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .dataset import DEPOSITO_BRUTO, ler_manifesto
from .pagina_comum import (
    DADOS,
    MEMOS,
    REPO,
    ROOT,
    SLUG,
    Capitulo,
    Dados,
    cabeca,
    inteiro,
)

COMANDOS = [
    "python3 scripts/apuracao-2t-2026-dados.py",
    "python3 scripts/apuracao-2t-2026-secoes.py --fonte completo",
    "python3 scripts/apuracao-2t-2026-pesquisas.py",
    "python3 scripts/apuracao-2t-2026-build.py",
    f"python3 scripts/social-cards.py --only {SLUG}",
]


def _tam(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f} MB".replace(".", ",")
    return f"{n / 1000:.1f} kB".replace(".", ",")


def _rel(c: Path) -> str:
    return str(c.relative_to(ROOT))


def item_arquivo(c: Path, d: Dados) -> str:
    bruto = c.read_bytes()
    sha = hashlib.sha256(bruto).hexdigest()
    fonte = d.fontes.get(c.name)
    gerado = (
        f" · gerado em {escape(fonte.gerado_em)}" if fonte and fonte.gerado_em else ""
    )
    return (
        f'<li><a href="{REPO}/blob/main/{_rel(c)}"><code>{escape(c.name)}</code></a> · {_tam(len(bruto))}{gerado}'
        f'<br><span class="hash">SHA-256 {sha}</span></li>'
    )


def item_dataset(m: dict | None = None) -> str:
    """Item "Dataset aberto por seção": hash do CSV e nota sobre o depósito bruto."""
    m = m or ler_manifesto()
    if not m:
        return ""
    csv_rel = m["arquivo"]
    deposito = (
        f'em <a href="{REPO}/blob/main/{_rel(DEPOSITO_BRUTO)}"><code>{escape(_rel(DEPOSITO_BRUTO))}</code></a>'
        if DEPOSITO_BRUTO.exists()
        else f"em <code>{escape(_rel(DEPOSITO_BRUTO))}</code> quando o depósito for enviado"
    )
    return (
        f'<li>Dataset aberto por seção: <a href="{csv_rel.removeprefix("docs/")}"><code>{escape(Path(csv_rel).name)}</code></a> '
        f"· {_tam(m['bytes'])} · {inteiro(m['n_linhas'])} linhas · dicionário em "
        f'<a href="{Path(csv_rel).parent.relative_to("docs")}/DICIONARIO.md"><code>DICIONARIO.md</code></a>.'
        f'<br><span class="hash">SHA-256 {escape(m["sha256"])}</span><br>'
        "Os bancos brutos (BUs decodificados, RDV, arquivos .vsc e logs) ficam em depósito à parte "
        f"(Internet Archive, item arvor-apuracao-2026-urnas-brasil, a enviar), com hashes {deposito}.</li>"
    )


def scripts() -> list[Path]:
    base = ROOT / "scripts"
    out = sorted(base.glob("apuracao-2t-2026-*.py"))
    out += sorted((base / "apuracao_2t_2026").glob("*.py"))
    return [c for c in out if c.name != "__init__.py"]


def render(d: Dados, cap: Capitulo) -> str:
    jsons = sorted(DADOS.glob("*.json"))
    extras = [
        c for c in (MEMOS / "noticias_noite.json", MEMOS / "video.json") if c.exists()
    ]
    memos = sorted(MEMOS.glob("*.md")) + sorted(DADOS.glob("*.md"))
    for c in jsons:
        d.get(c.name)
    h = cabeca(
        cap,
        "Fontes<br><em>e reprodução.</em>",
        f"{inteiro(len(jsons))} arquivos de dados, {inteiro(len(memos))} memorandos e os scripts que os geram, com tamanho e SHA-256.",
    )
    h += (
        f'<p class="io">Tudo está no repositório público <a href="{REPO}">{REPO.removeprefix("https://")}</a>: dados em '
        f'<a href="{REPO}/tree/main/analysis/apuracao_2t_2026/dados">analysis/apuracao_2t_2026/dados/</a>, memorandos em '
        f'<a href="{REPO}/tree/main/analysis/apuracao_2t_2026">analysis/apuracao_2t_2026/</a>, scripts em '
        f'<a href="{REPO}/tree/main/scripts">scripts/</a> e o coletor em <a href="{REPO}/tree/main/apuracao">apuracao/</a>. '
        "O banco do coletor, com cada versão dos arquivos do TSE e seu SHA-256, não cabe no GitHub e é enviado a pedido.</p>"
    )
    h += (
        '<h3>Dados</h3><ol class="fontes">'
        + "".join(item_arquivo(c, d) for c in jsons + extras)
        + "</ol>"
    )
    h += (
        '<h3>Memorandos</h3><ul class="fontes">'
        + "".join(
            f'<li><a href="{REPO}/blob/main/{_rel(c)}"><code>{escape(_rel(c))}</code></a></li>'
            for c in memos
        )
        + "</ul>"
    )
    h += (
        '<h3>Scripts</h3><ul class="fontes">'
        + "".join(
            f'<li><a href="{REPO}/blob/main/{_rel(c)}"><code>{escape(_rel(c))}</code></a></li>'
            for c in scripts()
        )
        + "</ul>"
    )
    h += (
        '<h3>Fontes primárias</h3><ul class="fontes">'
        "<li>Arquivos públicos de resultado do TSE, guardados pelo coletor em <code>apuracao/data/apuracao-2t.sqlite</code> com hora de "
        "geração, hora de leitura e SHA-256 (<code>apuracao/README.md</code>).</li>"
        "<li>Régua do 1º turno: <code>apuracao/data/referencia_1t.json</code> e <code>analysis/apuracao_2026/dados/</code>.</li>"
        "<li>Matérias da noite: <code>analysis/apuracao_2t_2026/noticias_noite.json</code>, com veículo, hora, URL e SHA-256 da cópia salva.</li>"
        "<li>Boletins falados: <code>docs/assets/apuracao_2t/boletins/</code> (áudio, roteiro e metadados).</li>"
        "<li>Malhas do IBGE: <code>data/originals/ibge_malhas/</code> e <code>apuracao/public/geo/</code>.</li>"
        + item_dataset()
        + "</ul>"
    )
    h += (
        "<details><summary>Reproduzir no repositório</summary><pre>"
        + "\n".join(COMANDOS)
        + "</pre></details>"
    )
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    h += f'<p class="meta">Página gerada em {agora}.</p>'
    return h
