"""Hemiciclo de 81 assentos em SVG: 27 que continuam (contorno) e 54 esperados."""

from __future__ import annotations

import math
from html import escape as esc

from .comum import (
    ASSENTOS,
    COR,
    ORDEM,
    ROTULO,
    alocar,
    campo_de,
    lerp,
    num,
)

W, H = 640.0, 330.0
CX, CY = W / 2, H - 14
RAIOS = (140.0, 185.0, 230.0, 275.0)
RAIO_ASSENTO = 12.5


def posicoes() -> list[tuple[float, float]]:
    """Coordenadas dos 81 assentos, da esquerda para a direita."""
    soma = sum(RAIOS)
    qtd = [round(ASSENTOS * r / soma) for r in RAIOS]
    qtd[-1] += ASSENTOS - sum(qtd)
    seats = []
    for r, n in zip(RAIOS, qtd, strict=True):
        for k in range(n):
            ang = math.pi * (1 - k / (n - 1))
            seats.append((-ang, r, CX + r * math.cos(ang), CY - r * math.sin(ang)))
    seats.sort(key=lambda s: (s[0], s[1]))
    return [(s[2], s[3]) for s in seats]


def svg(blocos: list[dict], titulo: str, descricao: str) -> str:
    """Cada bloco: cor, rotulo, continuam (int), novos (int)."""
    pos = posicoes()
    i = 0
    seats = []
    for b in blocos:
        for contorno, qtd in ((True, b["continuam"]), (False, b["novos"])):
            for _ in range(qtd):
                x, y = pos[i]
                i += 1
                cor = b["cor"]
                if contorno:
                    attrs = f'fill="#fffdf8" stroke="{cor}" stroke-width="3.2"'
                else:
                    attrs = f'fill="{cor}" stroke="{cor}" stroke-width="1"'
                seats.append(
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{RAIO_ASSENTO}" {attrs}/>'
                )
    return (
        f'<svg class="sn-hemi" viewBox="0 0 {W:.0f} {H:.0f}" role="img" '
        f'aria-label="{esc(descricao)}" xmlns="http://www.w3.org/2000/svg">'
        f"<title>{esc(titulo)}</title>" + "".join(seats) + "</svg>"
    )


def _continuam_por_campo(data: dict) -> dict[str, int]:
    out = dict.fromkeys(ORDEM, 0)
    for c in data["senado_2027"].get("continuam", []):
        out[campo_de(c.get("campo"))] += 1
    return out


def blocos_campo(data: dict) -> list[dict]:
    s27 = data["senado_2027"]
    por_campo = s27.get("por_campo", {})
    cont_lista = _continuam_por_campo(data)
    cont = {k: int(por_campo.get(k, {}).get("continuam", cont_lista[k])) for k in ORDEM}
    total_cont = sum(cont.values())
    novos_v = {k: float(por_campo.get(k, {}).get("novos_esperado", 0)) for k in ORDEM}
    total_novos = max(0, ASSENTOS - total_cont)
    novos_v["indefinido"] += max(0.0, total_novos - sum(novos_v.values()))
    novos = alocar(novos_v, total_novos)
    out = []
    for k in ORDEM:
        if cont[k] == 0 and novos[k] == 0:
            continue
        v = por_campo.get(k, {})
        out.append(
            {
                "chave": k,
                "cor": COR[k],
                "rotulo": ROTULO[k],
                "continuam": cont[k],
                "novos": novos[k],
                "novos_esperado": v.get("novos_esperado", novos_v[k]),
                "esperado": v.get("esperado"),
                "ic90": v.get("ic90"),
            }
        )
    return out


def blocos_partido(data: dict, campo_do_partido: dict[str, str], top: int = 8):
    s27 = data["senado_2027"]
    partidos = s27.get("por_partido", {})
    ranking = sorted(
        partidos.items(), key=lambda kv: kv[1].get("esperado", 0), reverse=True
    )
    maiores, resto = ranking[:top], ranking[top:]
    itens = []
    for nome, v in maiores:
        campo = campo_de(v.get("campo") or campo_do_partido.get(nome.upper()))
        itens.append((nome, campo, v))
    campos_vistos: dict[str, int] = {}
    entradas = []
    for nome, campo, v in itens:
        idx = campos_vistos.get(campo, 0)
        campos_vistos[campo] = idx + 1
        entradas.append(
            {
                "chave": nome,
                "campo": campo,
                "cor": lerp(COR[campo], "#ffffff", min(0.5, 0.22 * idx)),
                "rotulo": nome,
                "cont": int(v.get("continuam", 0)),
                "esp": float(v.get("esperado", 0)),
                "ic90": v.get("ic90"),
            }
        )
    out_cont = sum(int(v.get("continuam", 0)) for _, v in resto)
    out_esp = sum(float(v.get("esperado", 0)) for _, v in resto)
    soma_cont = sum(e["cont"] for e in entradas) + out_cont
    soma_esp = sum(e["esp"] for e in entradas) + out_esp
    # O que o JSON não distribui por partido entra em "Outros".
    out_cont += max(0, len(data["senado_2027"].get("continuam", [])) - soma_cont)
    out_esp += max(0.0, ASSENTOS - soma_esp)
    entradas.sort(key=lambda e: (ORDEM.index(e["campo"]), -e["esp"]))
    entradas.append(
        {
            "chave": "Outros",
            "campo": "indefinido",
            "cor": "#b9bcc2",
            "rotulo": "Outros partidos",
            "cont": out_cont,
            "esp": out_esp,
            "ic90": None,
        }
    )
    total_cont = sum(e["cont"] for e in entradas)
    total_novos = max(0, ASSENTOS - total_cont)
    novos_v = {e["chave"]: max(0.0, e["esp"] - e["cont"]) for e in entradas}
    novos = alocar(novos_v, total_novos)
    blocos = []
    for e in entradas:
        blocos.append(
            {
                **e,
                "continuam": e["cont"],
                "novos": novos[e["chave"]],
                "novos_esperado": novos_v[e["chave"]],
                "esperado": e["esp"],
            }
        )
    return blocos


def legenda(blocos: list[dict]) -> str:
    linhas = []
    for b in blocos:
        ic = b.get("ic90")
        ic_txt = f", IC90 de {num(ic[0], 0)} a {num(ic[1], 0)}" if ic else ""
        esperado = b.get("esperado")
        total = f"{num(esperado)} no total{ic_txt}" if esperado is not None else ""
        linhas.append(
            "<li>"
            f'<span class="sn-sw sn-sw-cheio" style="background:{b["cor"]}" aria-hidden="true"></span>'
            f"<b>{esc(b['rotulo'])}</b>"
            f"<span>{b['continuam']} continuam, "
            f"{num(b['novos_esperado'])} novos esperados"
            f"{', ' + total if total else ''}</span></li>"
        )
    return (
        '<ul class="sn-legenda">'
        '<li class="sn-key"><span class="sn-sw sn-sw-vazado" aria-hidden="true"></span>'
        "<span>Assento com contorno: mandato que continua até 2031.</span></li>"
        '<li class="sn-key"><span class="sn-sw sn-sw-cheio" style="background:#5d6a66" '
        'aria-hidden="true"></span><span>Assento cheio: vaga em disputa em 2026, '
        "distribuída pelo valor esperado.</span></li>" + "".join(linhas) + "</ul>"
    )


def render(data: dict, campo_do_partido: dict[str, str]) -> str:
    campos = blocos_campo(data)
    partidos = blocos_partido(data, campo_do_partido)
    soma = sum(b["continuam"] + b["novos"] for b in campos)
    desc_c = (
        f"Hemiciclo de {soma} assentos ordenados da esquerda para a direita: "
        + "; ".join(
            f"{b['rotulo']} {b['continuam']} que continuam e {b['novos']} esperados"
            for b in campos
        )
        + "."
    )
    desc_p = (
        "Hemiciclo por partido, da esquerda para a direita: "
        + "; ".join(
            f"{b['rotulo']} {b['continuam'] + b['novos']} assentos" for b in partidos
        )
        + "."
    )
    return (
        '<div class="sn-hemi-grid">'
        '<figure class="sn-hemi-fig" id="hemiciclo-campo">'
        '<figcaption class="sn-fig-title">Por campo</figcaption>'
        f"{svg(campos, 'Senado de 2027 por campo', desc_c)}{legenda(campos)}</figure>"
        '<figure class="sn-hemi-fig" id="hemiciclo-partido">'
        '<figcaption class="sn-fig-title">Por partido</figcaption>'
        f"{svg(partidos, 'Senado de 2027 por partido', desc_p)}{legenda(partidos)}</figure>"
        "</div>"
    )
