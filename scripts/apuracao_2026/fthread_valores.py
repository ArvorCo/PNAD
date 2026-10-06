"""Valores da thread dos fiscais: todo número e toda referência legal que entra num
post sai daqui, formatado a partir de `fiscais.json` e de `fontes_fiscais.json`."""

from __future__ import annotations

from . import fiscais_cenarios as FC
from .fthread_base import cenarios, fiscais
from .thread_base import mi, num, pct

NOME_UF = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AM": "Amazonas",
    "AP": "Amapá",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MG": "Minas Gerais",
    "MS": "Mato Grosso do Sul",
    "MT": "Mato Grosso",
    "PA": "Pará",
    "PB": "Paraíba",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "PR": "Paraná",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RO": "Rondônia",
    "RR": "Roraima",
    "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina",
    "SE": "Sergipe",
    "SP": "São Paulo",
    "TO": "Tocantins",
}


def inteiro(x) -> str:
    return num(x or 0, 0)


def tamanho(b: int) -> str:
    return f"{num(b / 1e6, 1)} MB"


def v_lista() -> dict:
    F = fiscais()
    R = F["resumo"]
    N, E, FI, EX = R["por_nivel"], R["eleitorado"], R["fiscais"], R["explicacao_comum"]
    crit = {c["id"]: c for c in F["criterios"]}
    top = sorted(F["criterios"], key=lambda c: -c["secoes"])
    ufs_alta = sorted(
        F["por_uf"], key=lambda u: (-(u.get("locais_alta") or 0), u["uf"])
    )
    taxa = sorted(F["por_uf"], key=lambda u: -u["secoes"] / u["secoes_universo"])
    exp = {e["formato"]: e for e in F["meta"]["exportaveis"]}
    cod = EX["por_codigo"]
    S = F.get("sensibilidade") or {}
    v = {
        "n_secoes": inteiro(R["secoes_sinalizadas"]),
        "n_universo": inteiro(R["secoes_universo"]),
        "pct_secoes": pct(100 * R["secoes_sinalizadas"] / R["secoes_universo"], 1),
        "n_locais": inteiro(FI["um_por_local"]["todos"]),
        "n_criterios": inteiro(len(F["criterios"])),
        "aptos_sinal": mi(E["aptos_sinalizadas"]),
        "pct_aptos": pct(E["pct_sinalizadas"]),
        "corte_alta": inteiro(F["meta"]["cortes_nivel"]["alta"]),
        "corte_media": inteiro(F["meta"]["cortes_nivel"]["media"]),
        "xlsx_tam": tamanho(exp["xlsx"]["bytes"]),
        "rot_atipico": F["rotulos"]["atipico"],
        "rot_prioridade": F["rotulos"]["prioridade"],
        "rot_resolve": F["rotulos"]["resolve"],
        "fis_alta": inteiro(FI["um_por_local"]["alta"]),
        "fis_alta_media": inteiro(FI["um_por_local"]["alta_media"]),
        "fis_todos": inteiro(FI["um_por_local"]["todos"]),
        "fis_secao_todos": inteiro(FI["um_por_secao"]["todos"]),
        "fis_dois_todos": inteiro(FI["dois_por_secao_maximo_legal"]["todos"]),
        "sem_coord": inteiro(R["sem_coordenada"]["locais"]),
        "explic_secoes": inteiro(EX["secoes"]),
        "baixa_aldeia_presidio": inteiro(EX["baixa_aldeia_presidio"]),
        "enclaves": inteiro(R["enclaves_2022"]),
        "cod_rural": inteiro(cod.get("zona_rural")),
        "cod_aldeia": inteiro(cod.get("aldeia")),
        "cod_presidio": inteiro(cod.get("presidio")),
        "cod_urna": inteiro(cod.get("urna_trocada")),
        "cod_transito": inteiro(cod.get("transito")),
        "cod_quilombo": inteiro(cod.get("quilombo_assentamento")),
        "mudam_nivel": inteiro(S.get("mudam_nivel")),
        "mudam_nivel_pct": pct(S.get("mudam_nivel_pct") or 0),
        "uf_taxa": NOME_UF[taxa[0]["uf"]],
        "uf_taxa_pct": pct(100 * taxa[0]["secoes"] / taxa[0]["secoes_universo"], 1),
    }
    for nivel in ("alta", "media", "baixa"):
        v[f"{nivel}_secoes"] = inteiro(N[nivel]["secoes"])
        v[f"{nivel}_locais"] = inteiro(N[nivel]["locais"])
        v[f"{nivel}_mun"] = inteiro(N[nivel]["municipios"])
    for i, c in enumerate(top[:3], 1):
        v[f"top{i}_nome"] = c["nome"]
        v[f"top{i}_n"] = inteiro(c["secoes"])
    for k, c in crit.items():
        v[f"crit_{k}"] = inteiro(c["secoes"])
        v[f"crit_{k}_nome"] = c["nome"]
    for i, u in enumerate(ufs_alta[:3], 1):
        v[f"uf_alta{i}"] = NOME_UF[u["uf"]]
        v[f"uf_alta{i}_n"] = inteiro(u.get("locais_alta"))
    return v


def _lei(J: dict, ident: str) -> str:
    x = FC.lei(J, ident)
    return f"{x['norma']}, {x['dispositivo']}"


def v_cenarios() -> dict:
    J = cenarios()
    n = FC.contagem_sinal(J)
    v = {
        "n_cenarios": inteiro(len(J["cenarios"])),
        "n_deixa": inteiro(n["deixa"]),
        "n_parcial": inteiro(n["parcial"]),
        "n_nenhum": inteiro(n["nenhum"]),
    }
    for b in J["base_legal"]:
        v[f"lei_{b['id']}"] = _lei(J, b["id"])
        if b.get("pena"):
            v[f"pena_{b['id']}"] = b["pena"]
    return v


__all__ = ["NOME_UF", "inteiro", "tamanho", "v_cenarios", "v_lista"]
