"""Cenários de risco e casos documentados do capítulo 13 (`fontes_fiscais.json`).

O arquivo `analysis/apuracao_2026/fontes_fiscais.json` é curado à mão a partir de
fontes primárias: cada cenário clássico de manipulação do voto (hipótese de risco,
nunca atribuída a 2026), cada caso brasileiro documentado (verificado, com data,
instância e fonte) e cada fonte com URL, veículo, data e, quando o texto bruto foi
arquivado, SHA-256 do arquivo em `data/originals/apuracao_2026/fiscais/`.

Este módulo lê, valida e oferece as consultas usadas pelo texto do dossiê
(`pagina_texto_fiscais_b`), pelas figuras (`pagina_fig_fiscais_d`) e pela thread
dos fiscais (`fthread_*`). `validar` devolve a lista de problemas; vazia é bom.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAMINHO = ROOT / "analysis/apuracao_2026/fontes_fiscais.json"

SINAIS = ("deixa", "parcial", "nenhum")
ROT_SINAL = {
    "deixa": "Deixa sinal nos dados",
    "parcial": "Sinal fraco ou indireto",
    "nenhum": "Não deixa sinal: só o fiscal vê",
}
CURTO_SINAL = {"deixa": "deixa sinal", "parcial": "sinal fraco", "nenhum": "sem sinal"}
COR_SINAL = {"deixa": "#1457aa", "parcial": "#7d5b00", "nenhum": "#7a3500"}

FAMILIAS = ("mesa", "entorno", "territorio", "cadastro")
ROT_FAMILIA = {
    "mesa": "Na mesa e na urna",
    "entorno": "No entorno da seção",
    "territorio": "No território",
    "cadastro": "No cadastro e na apuração",
}
COR_FAMILIA = {
    "mesa": "#1457aa",
    "entorno": "#7d5b00",
    "territorio": "#5b2a86",
    "cadastro": "#0b6650",
}
CAMPOS_CENARIO = (
    "id",
    "familia",
    "nome",
    "o_que_e",
    "como_aparece",
    "sinal",
    "criterios",
    "sinal_texto",
    "confere",
    "confere_curto",
    "base_legal",
)
CAMPOS_CASO = (
    "id",
    "ano",
    "data",
    "titulo",
    "local",
    "instancia",
    "cenario",
    "resultado",
    "resumo",
    "fontes",
    "rotulo_curto",
)
ROTULO_MAX = 22
"""Rótulo curto de cada caso na linha do tempo: até 22 caracteres."""
CAMPOS_FONTE = ("id", "url", "titulo", "veiculo", "data", "como_conferido")


@cache
def carregar(caminho: Path = CAMINHO) -> dict | None:
    """O JSON inteiro, ou None se ainda não existe."""
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


def por_id(lista: list[dict]) -> dict[str, dict]:
    return {x["id"]: x for x in lista}


def fonte(J: dict, ident: str) -> dict:
    return por_id(J["fontes"])[ident]


def lei(J: dict, ident: str) -> dict:
    return por_id(J["base_legal"])[ident]


def cenario(J: dict, ident: str) -> dict:
    return por_id(J["cenarios"])[ident]


def casos_ordenados(J: dict) -> list[dict]:
    return sorted(J["casos"], key=lambda c: (int(c["ano"]), c["data"], c["id"]))


def casos_do_cenario(J: dict, ident: str) -> list[dict]:
    return [c for c in casos_ordenados(J) if c["cenario"] == ident]


def contagem_sinal(J: dict) -> dict[str, int]:
    out = dict.fromkeys(SINAIS, 0)
    for c in J["cenarios"]:
        out[c["sinal"]] += 1
    return out


def data_br(iso: str | None) -> str:
    """'2022-10-30' vira '30/10/2022'; '2022-10' vira '10/2022'; ano fica ano."""
    if not iso:
        return "s/d"
    partes = iso.split("-")
    return "/".join(reversed(partes))


def validar(J: dict, criterios: set[str] | None = None) -> list[str]:
    """Problemas de integridade: campo ausente, referência quebrada, travessão."""
    erros: list[str] = []
    for chave in ("cenarios", "casos", "fontes", "base_legal"):
        if not isinstance(J.get(chave), list) or not J[chave]:
            erros.append(f"{chave} ausente ou vazio")
    if erros:
        return erros
    fontes = por_id(J["fontes"])
    leis = por_id(J["base_legal"])
    cens = por_id(J["cenarios"])
    for nome, lista in (("fonte", J["fontes"]), ("cenário", J["cenarios"])):
        ids = [x["id"] for x in lista]
        if len(ids) != len(set(ids)):
            erros.append(f"{nome}: id repetido")
    for f in J["fontes"]:
        for c in CAMPOS_FONTE:
            if not f.get(c):
                erros.append(f"fonte {f.get('id')}: sem {c}")
        if not str(f.get("url", "")).startswith("http"):
            erros.append(f"fonte {f.get('id')}: url inválida")
    for b in J["base_legal"]:
        if b.get("fonte") not in fontes:
            erros.append(f"base legal {b.get('id')}: fonte {b.get('fonte')} ausente")
    for c in J["cenarios"]:
        for campo in CAMPOS_CENARIO:
            if campo not in c or c[campo] in (None, ""):
                erros.append(f"cenário {c.get('id')}: sem {campo}")
        if c.get("sinal") not in SINAIS:
            erros.append(f"cenário {c.get('id')}: sinal {c.get('sinal')}")
        if c.get("familia") not in FAMILIAS:
            erros.append(f"cenário {c.get('id')}: família {c.get('familia')}")
        for b in c.get("base_legal", []):
            if b not in leis:
                erros.append(f"cenário {c.get('id')}: base legal {b} ausente")
        if criterios is not None:
            for k in c.get("criterios", []):
                if k not in criterios:
                    erros.append(f"cenário {c.get('id')}: critério {k} inexistente")
        if c.get("sinal") == "nenhum" and c.get("criterios"):
            erros.append(f"cenário {c.get('id')}: sem sinal mas com critério")
    for k in J["casos"]:
        for campo in CAMPOS_CASO:
            if campo not in k or k[campo] in (None, "", []):
                erros.append(f"caso {k.get('id')}: sem {campo}")
        if len(str(k.get("rotulo_curto") or "")) > ROTULO_MAX:
            erros.append(
                f"caso {k.get('id')}: rotulo_curto com mais de {ROTULO_MAX} caracteres"
            )
        if k.get("cenario") not in cens:
            erros.append(f"caso {k.get('id')}: cenário {k.get('cenario')} ausente")
        for f in [
            *k.get("fontes", []),
            *([k["fonte_thread"]] if k.get("fonte_thread") else []),
        ]:
            if f not in fontes or f not in k.get("fontes", []):
                erros.append(f"caso {k.get('id')}: fonte {f} ausente")
        ano, data = int(k.get("ano") or 0), str(k.get("data") or "")
        if not data[:4].isdigit() or ano > int(data[:4]):
            erros.append(f"caso {k.get('id')}: data do ato anterior ao ano do fato")
        if ano >= 2026:
            erros.append(
                f"caso {k.get('id')}: caso de 2026 não entra (nada é atribuído a esta eleição)"
            )
    for c in J["cenarios"]:
        for f in c.get("fontes", []):
            if f not in fontes:
                erros.append(f"cenário {c.get('id')}: fonte {f} ausente")
    texto = json.dumps(J, ensure_ascii=False)
    if "—" in texto:
        erros.append("travessão no JSON")
    return erros


__all__ = [
    "CAMINHO",
    "COR_FAMILIA",
    "COR_SINAL",
    "CURTO_SINAL",
    "FAMILIAS",
    "ROTULO_MAX",
    "ROT_FAMILIA",
    "ROT_SINAL",
    "SINAIS",
    "carregar",
    "casos_do_cenario",
    "casos_ordenados",
    "cenario",
    "contagem_sinal",
    "data_br",
    "fonte",
    "lei",
    "por_id",
    "validar",
]
