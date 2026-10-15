"""Leitor local das 152 páginas, com catálogo acessível sem JavaScript."""

import json
from html import escape as esc

from dossies_2t_2026.view import details, section, table


def render(data):
    records = data["catalogo"]
    first = next(r for r in records if r["pagina"] == 19)
    payload = [
        {k: r[k] for k in ("pagina", "titulo", "tema", "imagem")} for r in records
    ]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )
    return section(
        12,
        "documentos",
        "A fonte, página por página.<br><em>Sem depender de um print solto.</em>",
        "A cópia recebida tem 152 páginas. Navegue pelos gráficos originais ou abra o PDF completo.",
        '<p><a href="fontes/quaest_14102026.pdf">Baixar íntegra (55 MB)</a> · <a href="assets/quaest_14102026_integra/paginas.csv">Catálogo CSV</a> · <a href="assets/quaest_14102026_integra/auditoria.json">Proveniência e contas</a></p>'
        '<div class="explorer q-document-viewer"><div class="explorer-controls" id="q-document-controls" hidden>'
        '<label>Tema<select id="q-document-topic"><option value="all">Todas as páginas</option><option value="metodo">Método e margens</option>'
        + "".join(
            f'<option value="{t["id"]}">{esc(t["titulo"])}</option>'
            for t in data["temas"]
        )
        + '<option value="separador">Capa e separadores</option></select></label><label>Página<select id="q-document-page">'
        + "".join(
            f'<option value="{r["pagina"]}"'
            + (" selected" if r["pagina"] == 19 else "")
            + f'>{r["pagina"]} · {esc(r["titulo"])}</option>'
            for r in records
        )
        + '</select></label></div><p id="q-document-status" role="status" aria-live="polite">Página 19 de 152 · Transferência declarada</p>'
        f'<a id="q-document-image-link" href="{first["imagem"]}"><img id="q-document-image" loading="lazy" src="{first["imagem"]}" alt="Página 19: transferência de voto do primeiro para o segundo turno" width="1588" height="893"></a>'
        '<p class="note">Toque na imagem para ampliar. Os números e rótulos são os do documento recebido. Trechos com bases ausentes ou rótulos omitidos continuam ausentes.</p>'
        '<div class="q-document-nav" id="q-document-nav" hidden><button id="q-document-prev" type="button">← Anterior</button><a id="q-document-share" href="?pagina=19#documentos">Link desta página</a><button id="q-document-next" type="button">Próxima →</button></div>'
        '<p><a id="q-document-pdf" href="fontes/quaest_14102026.pdf#page=19">Abrir esta página no PDF</a></p></div>'
        + details(
            "Catálogo completo: 152 páginas",
            table(
                ["Página", "Tema/título", "Original"],
                [
                    [
                        str(r["pagina"]),
                        esc(r["titulo"]),
                        f'<a href="fontes/quaest_14102026.pdf#page={r["pagina"]}">PDF</a> · <a href="{r["imagem"]}">Imagem</a>',
                    ]
                    for r in records
                ],
            ),
            ident="q-catalogo-completo",
        )
        + '<p class="note">Arquivo recebido do usuário em 15/10/2026, preservado byte a byte. SHA-256: <code>'
        + data["documento"]["sha256"]
        + "</code>. Renderizações geradas localmente; o PDF original não foi regravado.</p>"
        + '<script type="application/json" id="q-document-data">'
        + encoded
        + "</script>",
    )
