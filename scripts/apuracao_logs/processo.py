"""Processo observado e cadência: agregados sem expor sequências individuais.

A digitação concluída do identificador é o primeiro marco observável. A espera
anterior pode conter fila, ociosidade e conferência fora da urna; não é atendimento
cronometrado. Identificações repetidas não são vinculadas à mesma pessoa.
"""

from collections import Counter, defaultdict

TIPOS = ("biometrica", "biografica", "sem_biometria")
JANELA = 10  # dez intervalos consecutivos = onze cômputos


def resumir(ciclos, invalidar, distribuicao):
    grupos = defaultdict(list)
    for c in ciclos:
        if not c["parcial"] and c["cargos"] > 0:
            grupos[str(c["cargos"])].append(c)
    principal = max(grupos, key=lambda k: len(grupos[k])) if grupos else "0"
    selecionados = grupos.get(principal, [])
    processos = (
        [
            c
            for c in selecionados
            if c["ident"] is not None
            and c["identificacoes"] == 1
            and not c["cancelamento"]
            and c["ident"] <= c["hab"] <= c["fim"]
        ]
        if not invalidar
        else []
    )
    hist = Counter(c["fim"] - c["ident"] for c in processos)
    por_tipo = {
        tipo: distribuicao(
            [c["fim"] - c["ident"] for c in processos if c["tipo"] == tipo]
        )
        for tipo in TIPOS
    }
    intervalos, janelas, blocos = [], [], defaultdict(list)
    anterior = {}
    for c in ciclos if not invalidar else []:
        chave = (c["urna"], c["sessao"])
        a = anterior.get(chave)
        valido = (
            a is not None
            and a["ordem"] + 1 == c["ordem"]
            and not a["parcial"]
            and not c["parcial"]
            and str(a["cargos"]) == str(c["cargos"]) == principal
            and a["fim"] <= c["fim"]
        )
        if valido:
            delta = c["fim"] - a["fim"]
            intervalos.append(delta)
            blocos[chave].append(delta)
            if len(blocos[chave]) >= JANELA:
                janelas.append(sum(blocos[chave][-JANELA:]) / JANELA)
        else:
            blocos[chave] = []
        anterior[chave] = c
    return {
        "cargos": principal,
        "processo": distribuicao([c["fim"] - c["ident"] for c in processos]),
        "por_tipo": por_tipo,
        "cadencia": distribuicao(intervalos),
        "rajada10_s": min(janelas) if janelas else None,
        "janelas10": len(janelas),
        "excluidos_identificacao": len(selecionados) - len(processos),
        "histograma_processo": sorted(hist.items()),
        "histograma_cadencia": sorted(Counter(intervalos).items()),
    }
