"""Motivos alegados: do texto das notas dos TREs aos pares origem e destino do motor.

Duas leituras separadas, para não misturar o que a nota diz de um local com o que diz de
todo o estado:
- atribuído: o texto casado com o par (campo motivo_tre do motor), já sem as frases que a
  nota marca como gerais;
- citado em geral: todo motivo que qualquer nota ou o TSE cita, sem ligação com local.
"""

from __future__ import annotations

SEM = "sem"
GERAL = "geral"

ROTULOS = {
    SEM: "Sem motivo publicado",
    GERAL: "Só a justificativa geral da nota",
    "conforto": "Calor, conforto ou falta de espaço",
    "reforma": "Reforma",
    "retorno": "Retorno do provisório ao original",
    "pedido": "Pedido de eleitores, mesários ou coordenadores",
    "acesso": "Acesso ou acessibilidade",
    "energia": "Problema de energia elétrica",
    "agua": "Enchente ou alagamento",
    "infra": "Melhor infraestrutura de atendimento",
    "chuva": "Chuva, temporal, vento ou telhado",
    "seguranca": "Segurança",
    "interdicao": "Laudo de engenharia ou interdição",
    "predio": "Prédio indisponível, danificado ou com problema estrutural",
    "fluxo": "Fechamento de escola ou redistribuição de fluxo",
    "logistica": "Logística e locomoção dos eleitores",
}

PALAVRAS = {
    "conforto": ("calor", "térmico", "conforto", "espaço", "estreito", "concentração"),
    "reforma": ("reforma",),
    "retorno": ("retorno",),
    "pedido": ("solicita",),
    "acesso": ("acesso", "acessibilidade"),
    "energia": ("energia", "elétric"),
    "agua": ("enchente", "alag", "inunda"),
    "chuva": (
        "chuva",
        "temporal",
        "temporais",
        "telhado",
        "climátic",
        "vento",
        "ventania",
        "destelh",
    ),
    "infra": ("infraestrutura",),
    "seguranca": ("segurança",),
    "interdicao": ("interdi", "laudo"),
    "predio": (
        "indisponibilidade",
        "estruturais",
        "estruturas físicas",
        "emergenciais",
        "danific",
        "desmoron",
        "incêndio",
    ),
    "fluxo": ("fechamento de escolas", "fluxo"),
    "logistica": ("logística", "locomoção"),
}


def _segmento_geral(seg: str) -> bool:
    s = seg.strip().lower()
    return (
        "texto geral" in s
        or s.startswith(("motivos gerais", "nota cita"))
        or s in ("não informado", "idem", "")
    )


def _chaves(texto: str) -> set[str]:
    t = texto.lower()
    return {c for c, ps in PALAVRAS.items() if any(p in t for p in ps)}


def classificar_par(local: dict) -> list[str]:
    """Categorias atribuídas ao par; sem nota casada, só 'sem'."""
    m = local.get("motivo_tre")
    if not m:
        return [SEM]
    segmentos = [
        s for s in str(m.get("texto", "")).split(";") if not _segmento_geral(s)
    ]
    achadas: set[str] = set()
    for s in segmentos:
        achadas |= _chaves(s)
    return sorted(achadas) if achadas else [GERAL]


def resumo(locais: list[dict]) -> dict:
    """Seções, eleitores e pares por categoria, só para mudança real."""
    reais = [x for x in locais if x["mudanca_real"]]
    tot_s = sum(len(x["secoes"]) for x in reais)
    tot_e = sum(x["eleitores"] for x in reais)
    acc: dict[str, dict] = {}
    for x in reais:
        for c in classificar_par(x):
            a = acc.setdefault(c, {"secoes": 0, "eleitores": 0, "pares": 0})
            a["secoes"] += len(x["secoes"])
            a["eleitores"] += x["eleitores"]
            a["pares"] += 1
    fixos = [SEM, GERAL]
    resto = sorted((c for c in acc if c not in fixos), key=lambda c: -acc[c]["secoes"])
    linhas = [
        {"chave": c, "rotulo": ROTULOS[c], **acc[c]} for c in fixos + resto if c in acc
    ]
    com_nota = [x for x in reais if x.get("motivo_tre")]
    return {
        "linhas": linhas,
        "secoes_total": tot_s,
        "eleitores_total": tot_e,
        "pares_total": len(reais),
        "com_nota": {
            "pares": len(com_nota),
            "secoes": sum(len(x["secoes"]) for x in com_nota),
            "eleitores": sum(x["eleitores"] for x in com_nota),
        },
        "sem_nota": acc.get(SEM, {"secoes": 0, "eleitores": 0, "pares": 0}),
        "especificos": {
            "pares": sum(
                1 for x in reais if classificar_par(x) not in ([SEM], [GERAL])
            ),
            "secoes": sum(
                len(x["secoes"])
                for x in reais
                if classificar_par(x) not in ([SEM], [GERAL])
            ),
        },
    }


def citado_em_geral(notas: list[dict]) -> list[dict]:
    """Para cada motivo, as unidades (UF ou BR) cujas notas o citam, com a fonte."""
    por: dict[str, dict[str, dict]] = {}
    for n in notas:
        if not n.get("url"):
            continue
        textos = list(n.get("motivos_citados") or [])
        for t in textos:
            for c in _chaves(t):
                por.setdefault(c, {})[n["uf"]] = n
    ordem = sorted(por, key=lambda c: -len(por[c]))
    return [
        {
            "chave": c,
            "rotulo": ROTULOS[c],
            "ufs": sorted(por[c]),
            "fontes": [por[c][u] for u in sorted(por[c])],
        }
        for c in ordem
    ]


def ufs_sem_nota(notas: list[dict], todas: list[str]) -> list[str]:
    com = {n["uf"] for n in notas if n.get("url") and n["uf"] != "BR"}
    return sorted(u for u in todas if u not in com)
