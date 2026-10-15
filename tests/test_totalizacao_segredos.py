"""Nenhum segredo do Supabase ou do Turnstile pode entrar no repositorio publico."""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTAS = ["docs", "totalizacao", "scripts", ".github"]
IGNORAR = {"node_modules", "fontes", "img"}
EXTENSOES = {
    ".html",
    ".js",
    ".ts",
    ".json",
    ".py",
    ".yml",
    ".yaml",
    ".toml",
    ".md",
    ".css",
    ".sql",
    ".txt",
    ".csv",
}
PADROES = [
    re.compile(r"sb_secret_[A-Za-z0-9_-]{8,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}"),
    re.compile(r"""SUPABASE_SERVICE_ROLE_KEY\s*[=:]\s*["'](eyJ|sb_secret_)"""),
    re.compile(r"""TURNSTILE_SECRET\s*[=:]\s*["']0x[A-Za-z0-9_-]{20,}"""),
]


def _arquivos():
    for pasta in PASTAS:
        for p in (RAIZ / pasta).rglob("*"):
            if (
                p.is_file()
                and p.suffix in EXTENSOES
                and not (IGNORAR & set(p.relative_to(RAIZ).parts))
            ):
                yield p


def test_sem_segredos_no_repositorio():
    achados = []
    for p in _arquivos():
        texto = p.read_text(encoding="utf-8", errors="ignore")
        for padrao in PADROES:
            if padrao.search(texto):
                achados.append(f"{p.relative_to(RAIZ)}: {padrao.pattern}")
    assert achados == [], "segredo detectado: " + "; ".join(achados)
