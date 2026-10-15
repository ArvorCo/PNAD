"""Arquivo imutável e renderizações da íntegra recebida; comando optativo pesado."""

import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "data/originals/quaest_102026_14/Quaest_14102026.pdf"
PUBLIC = ROOT / "docs/fontes/quaest_14102026.pdf"
DATA = ROOT / "analysis/quaest_141026/integra"
PAGES = ROOT / "docs/fontes/quaest_14102026/integra"
EXPECTED_SHA = "112fd4b9b104d288394f27d98da77ec1bc2636cce144bb718f8986caf90c7592"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_pages():
    import fitz
    from PIL import Image

    if digest(SOURCE) != EXPECTED_SHA:
        raise ValueError(
            "O PDF difere da versão conferida; não substituir silenciosamente."
        )
    shutil.copyfile(SOURCE, PUBLIC)
    PAGES.mkdir(parents=True, exist_ok=True)
    topics = [json.loads(p.read_text()) for p in (DATA / "temas").glob("*.json")]
    doc = fitz.open(SOURCE)
    records = []
    dividers = {
        1: "Capa",
        5: "Intenção espontânea",
        16: "Intenção estimulada",
        30: "Firmeza da escolha",
        33: "Potencial e rejeição",
        44: "Medo",
        55: "Razões do medo",
        57: "Merecimento",
        61: "Expectativa",
        72: "Aprovação",
        82: "Avaliação",
        92: "Direção do país",
        102: "Custo de vida",
        113: "Propostas",
        116: "Interesse",
        119: "Preocupações",
        128: "Voto lembrado",
        130: "Alternativas",
        132: "Momento da decisão",
        135: "Motivo do voto em Lula",
        138: "Motivo do voto em Flávio",
        141: "Identificação política",
        143: "Perfil da amostra",
        152: "Encerramento",
    }
    for number, page in enumerate(doc, 1):
        text = page.get_text().strip()
        lines = [s.strip() for s in text.splitlines() if s.strip()]
        topic = next((t for t in topics if number in t["paginas"]), None)
        title = lines[0] if lines else dividers.get(number, "Especificações técnicas")
        image = PAGES / f"p{number:03}.webp"
        pix = page.get_pixmap(matrix=fitz.Matrix(3.5, 3.5), alpha=False)
        Image.frombytes("RGB", (pix.width, pix.height), pix.samples).save(
            image, "WEBP", quality=88, method=6
        )
        records.append(
            {
                "pagina": number,
                "titulo": title,
                "tema": (
                    topic["id"]
                    if topic
                    else "metodo" if number in (2, 3, 4) else "separador"
                ),
                "texto_nativo": text,
                "imagem": str(image.relative_to(ROOT / "docs")),
                "sha256": digest(image),
            }
        )
    document = {
        "arquivo": str(SOURCE.relative_to(ROOT)),
        "arquivo_publico": "fontes/quaest_14102026.pdf",
        "nome_recebido": SOURCE.name,
        "origem": "Arquivo fornecido pelo usuário em Downloads; cópia recebida preservada byte a byte.",
        "recebido_em": "2026-10-15",
        "sha256": digest(SOURCE),
        "bytes": SOURCE.stat().st_size,
        "paginas": len(doc),
        "metadados_pdf": doc.metadata,
        "nota": "Hash identifica esta cópia, não uma autenticação externa. Gráficos são imagens; extração de texto não é transcrição dos valores.",
    }
    (DATA / "documento.json").write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    )
    # Uma página por linha mantém o catálogo compacto e revisável.
    (DATA / "paginas.json").write_text(
        "[\n" + ",\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n]\n"
    )
    print(
        f'{len(doc)} páginas renderizadas; {sum(p.stat().st_size for p in PAGES.glob("*.webp"))/1e6:.1f} MB'
    )
