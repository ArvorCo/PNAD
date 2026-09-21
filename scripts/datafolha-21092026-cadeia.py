#!/usr/bin/env python3
"""Motor de transferencia de voto do capitulo Sudeste do dossie de 21/09/2026.

Tres engrenagens, todas declaradas:

1. `matriz_transferencia`: ajuste proporcional iterativo de duas vias contra
   uma prior declarada, com as linhas publicadas pelo instituto fixas como
   medicao e, quando informado, com piso por celula.
2. `cadeia_presidencial`: cubo origem x via x destino quando o par alvo nao tem
   linha medida mas o par governador x presidente de 1o turno tem. A via e o
   voto presidencial de 1o turno. Quem ja vota num finalista no 1o turno
   permanece com ele com probabilidade declarada, e essa parcela entra fixa.
3. `cadeia_estadual`: cubo governador 1o turno x governador 2o turno x
   presidente 2o turno, para estimar o par governador 2o turno x presidente 2o
   turno sem perder as linhas medidas, que vivem no primeiro estagio.

Nenhuma das duas cadeias usa independencia condicional dentro do intermediario.
A prior do cubo e sempre condicionada a origem, com um termo de interacao
declarado entre a via e o destino. Markov, aqui, inflaria o caminho para o
candidato que o intermediario ja nao escolheu.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence

LULA = "Lula (PT)"
FLAVIO = "Flavio Bolsonaro (PL)"

NAO_ESCOLHA = {
    "Em branco/nulo/nenhum",
    "Em branco/ nulo/ nenhum",
    "Indecisos",
    "Não sabe",
}

# Campo declarado de cada candidatura, por partido, como juizo editorial
# explicito. Centro e categoria propria: somar o centro a direita inflaria o
# bloco e o laudo nao sobreviveria a citacao hostil.
CAMPO_PARTIDO = {
    "PL": "direita",
    "REPUBLICANOS": "direita",
    "PP": "direita",
    "NOVO": "direita",
    "MISSÃO": "direita",
    "DEMOCRATA": "direita",
    "PRTB": "direita",
    "DC": "direita",
    "AGIR": "direita",
    "PSD": "centro",
    "MDB": "centro",
    "PSDB": "centro",
    "PODE": "centro",
    "CIDADANIA": "centro",
    "AVANTE": "centro",
    "PDT": "centro-esquerda",
    "PSB": "centro-esquerda",
    "REDE": "centro-esquerda",
    "PT": "esquerda",
    "PSOL": "esquerda",
    "PCB": "esquerda",
    "PSTU": "esquerda",
    "PCO": "esquerda",
    "UP": "esquerda",
}
ORDEM_CAMPO = {"direita": 0, "centro": 1, "centro-esquerda": 2, "esquerda": 3}

# Prior ideologica declarada, por campo da candidatura de origem. Os zeros sao
# estruturais e o IPF os preserva.
PRIOR_IDEOLOGICA = {
    "direita": {"flavio": 0.90, "lula": 0.02, "nao_escolha": 0.08},
    "centro": {"flavio": 0.34, "lula": 0.40, "nao_escolha": 0.26},
    "centro-esquerda": {"flavio": 0.14, "lula": 0.66, "nao_escolha": 0.20},
    "esquerda": {"flavio": 0.02, "lula": 0.92, "nao_escolha": 0.06},
    "nao_escolha": {"flavio": 0.22, "lula": 0.22, "nao_escolha": 0.56},
}
PRIOR_POLARIZADA = {
    "direita": {"flavio": 0.97, "lula": 0.01, "nao_escolha": 0.02},
    "centro": {"flavio": 0.45, "lula": 0.45, "nao_escolha": 0.10},
    "centro-esquerda": {"flavio": 0.08, "lula": 0.85, "nao_escolha": 0.07},
    "esquerda": {"flavio": 0.01, "lula": 0.97, "nao_escolha": 0.02},
    "nao_escolha": {"flavio": 0.30, "lula": 0.30, "nao_escolha": 0.40},
}
PRIOR_FROUXA = {
    "direita": {"flavio": 0.75, "lula": 0.10, "nao_escolha": 0.15},
    "centro": {"flavio": 0.30, "lula": 0.33, "nao_escolha": 0.37},
    "centro-esquerda": {"flavio": 0.20, "lula": 0.50, "nao_escolha": 0.30},
    "esquerda": {"flavio": 0.08, "lula": 0.77, "nao_escolha": 0.15},
    "nao_escolha": {"flavio": 0.18, "lula": 0.18, "nao_escolha": 0.64},
}
PRIORS = {
    "ideologica": PRIOR_IDEOLOGICA,
    "polarizada": PRIOR_POLARIZADA,
    "frouxa": PRIOR_FROUXA,
}

# Retencao: parcela de quem ja escolheu um finalista no 1o turno presidencial
# que continua com ele no 2o. Entra fixa no cubo, e o piso medido de cada
# celula ancorada e exatamente a linha publicada multiplicada por ela.
RETENCAO_PADRAO = 0.98
RETENCOES = (0.93, 0.97, 0.98, 0.99)
# Fidelidade de base no 2o turno estadual: parcela do eleitor de uma
# candidatura ao governo no 1o turno que continua com ela no 2o. So se aplica a
# quem chega ao 2o turno estadual, e nos tres estados as duas candidaturas
# cresceram do 1o para o 2o turno, o que e condicao necessaria da hipotese.
FIDELIDADE_PADRAO = 0.98
FIDELIDADES = (0.93, 0.97, 0.98, 0.99)


def campo_de(rotulo: str) -> str:
    achado = re.search(r"\(([^)]+)\)\s*$", rotulo)
    if not achado:
        return "nao_escolha" if rotulo in NAO_ESCOLHA else "desconhecido"
    return CAMPO_PARTIDO.get(achado.group(1).upper(), "desconhecido")


def frechet(linha: float, coluna: float) -> tuple[float, float]:
    return max(0.0, linha + coluna - 1.0), min(linha, coluna)


def _normalizar(valores: dict) -> dict:
    total = sum(valores.values())
    return {k: v / total for k, v in valores.items()}


def slots_destino(colunas: Sequence[str]) -> dict[str, str]:
    """Liga cada destino a um slot da prior: flavio, lula ou nao_escolha.

    No destino presidencial os dois nomes decidem sozinhos. Num 2o turno
    estadual os finalistas mudam de nome a cada estado, entao o slot sai da
    ordem de campo: a candidatura mais a direita ocupa o slot `flavio` e a mais
    a esquerda, o slot `lula`.
    """
    if FLAVIO in colunas or LULA in colunas:
        return {
            c: ("flavio" if c == FLAVIO else "lula" if c == LULA else "nao_escolha")
            for c in colunas
        }
    mapa = dict.fromkeys(colunas, "nao_escolha")
    candidatos = [
        c for c in colunas if c not in NAO_ESCOLHA and campo_de(c) in ORDEM_CAMPO
    ]
    ordenados = sorted(candidatos, key=lambda c: ORDEM_CAMPO[campo_de(c)])
    if len(ordenados) >= 2:
        mapa[ordenados[0]] = "flavio"
        mapa[ordenados[-1]] = "lula"
    elif ordenados:
        mapa[ordenados[0]] = "flavio" if campo_de(ordenados[0]) == "direita" else "lula"
    return mapa


def peso_destino(peso: dict, destino: str, mapa: dict[str, str]) -> float:
    """Peso da prior num destino, com a nao escolha repartida entre os rotulos."""
    slot = mapa[destino]
    if slot != "nao_escolha":
        return peso.get(slot, 0.0)
    quantos = sum(1 for v in mapa.values() if v == "nao_escolha")
    return peso.get("nao_escolha", 0.0) / max(1, quantos)


def ipf(
    prior: list[list[float]],
    linhas: list[float],
    colunas: list[float],
    iteracoes: int = 2000,
    tolerancia: float = 1e-12,
) -> list[list[float]]:
    m = [row[:] for row in prior]
    for _ in range(iteracoes):
        pior = 0.0
        for i, alvo in enumerate(linhas):
            soma = sum(m[i])
            if soma <= 0:
                if alvo > 0:
                    raise ValueError("Linha com prior nula e margem positiva")
                continue
            fator = alvo / soma
            pior = max(pior, abs(fator - 1))
            m[i] = [v * fator for v in m[i]]
        for j, alvo in enumerate(colunas):
            soma = sum(m[i][j] for i in range(len(m)))
            if soma <= 0:
                if alvo > 0:
                    raise ValueError("Coluna com prior nula e margem positiva")
                continue
            fator = alvo / soma
            pior = max(pior, abs(fator - 1))
            for i in range(len(m)):
                m[i][j] *= fator
        if pior < tolerancia:
            break
    return m


def ipf_generico(
    celulas: dict,
    restricoes: Sequence[tuple[Callable, dict]],
    iteracoes: int = 4000,
    tolerancia: float = 1e-13,
) -> dict:
    """Ajuste proporcional iterativo sobre celulas nomeadas por tupla.

    Cada restricao e um par (funcao de agrupamento, margens alvo). Serve tanto
    para a matriz de duas vias quanto para o cubo de tres, sem duplicar codigo.
    """
    m = dict(celulas)
    grupos = []
    for chave, alvos in restricoes:
        indice: dict = {}
        for k in m:
            indice.setdefault(chave(k), []).append(k)
        for g, alvo in alvos.items():
            if alvo > 1e-12 and g not in indice:
                raise ValueError(f"margem positiva sem celula: {g}")
        grupos.append((indice, alvos))
    for _ in range(iteracoes):
        pior = 0.0
        for indice, alvos in grupos:
            for g, chaves in indice.items():
                alvo = alvos.get(g, 0.0)
                soma = sum(m[k] for k in chaves)
                if soma <= 0:
                    if alvo > 1e-12:
                        raise ValueError(f"prior nula com margem positiva: {g}")
                    continue
                fator = alvo / soma
                pior = max(pior, abs(fator - 1))
                for k in chaves:
                    m[k] *= fator
        if pior < tolerancia:
            break
    return m


def _estado_da_celula(marca: str, baixo: float, alto: float, piso: float | None) -> str:
    if marca == "medida":
        return "medida"
    if piso is not None and piso > 1e-9:
        return "ancorada"
    if alto - baixo < 0.01:
        return "limitada"
    return marca


def montar_saida(
    linhas: Sequence[str],
    colunas: Sequence[str],
    r: dict,
    c: dict,
    final: dict,
    marca: dict,
    pisos: dict,
    fontes_do_piso: dict,
    extra: dict,
) -> dict:
    """Formato unico de saida, seja de duas vias ou de cadeia de tres niveis."""
    celulas = []
    for nome in linhas:
        for destino in colunas:
            baixo, alto = frechet(r[nome], c[destino])
            piso = pisos.get((nome, destino))
            estado = _estado_da_celula(
                marca.get((nome, destino), "estimada"), baixo, alto, piso
            )
            celula = {
                "origem": nome,
                "destino": destino,
                "valor_pp": round(100 * final[(nome, destino)], 3),
                "frechet_min_pp": round(100 * baixo, 3),
                "frechet_max_pp": round(100 * alto, 3),
                "estado": estado,
            }
            informado = 100 * baixo
            fonte = fontes_do_piso.get((nome, destino))
            if estado == "medida" and fonte:
                celula["fonte"] = fonte
            if piso is not None:
                celula["piso_medido_pp"] = round(100 * piso, 3)
                celula["piso_fonte"] = fonte
                informado = max(informado, 100 * piso)
            celula["limite_inferior_informado_pp"] = round(informado, 3)
            celulas.append(celula)
    saida = {
        "origem_pct": {k: round(100 * v, 2) for k, v in r.items()},
        "destino_pct": {k: round(100 * v, 2) for k, v in c.items()},
        "matriz_pp": {
            nome: {d: round(100 * final[(nome, d)], 3) for d in colunas}
            for nome in linhas
        },
        # Mesma matriz sem arredondamento, para encadear um estagio no outro
        # sem acumular erro de terceira casa. Sai do JSON publicado.
        "matriz_exata": {
            nome: {d: 100 * final[(nome, d)] for d in colunas} for nome in linhas
        },
        "condicional_pct": {
            nome: {d: round(100 * final[(nome, d)] / r[nome], 2) for d in colunas}
            for nome in linhas
            if r[nome] > 0
        },
        "celulas": celulas,
        "residuo_margem_linha_pp": round(
            100
            * max(
                abs(sum(final[(nome, d)] for d in colunas) - r[nome]) for nome in linhas
            ),
            6,
        ),
        "residuo_margem_coluna_pp": round(
            100
            * max(
                abs(sum(final[(nome, d)] for nome in linhas) - c[d]) for d in colunas
            ),
            6,
        ),
    }
    saida.update(extra)
    return saida


def matriz_transferencia(
    origem: dict,
    destino: dict,
    medidas: dict,
    prior_nome: str,
    prior_empirica: dict | None = None,
    pisos_pct: dict | None = None,
    fontes_do_piso: dict | None = None,
    fidelidade: float | None = None,
) -> dict:
    """IPF de duas vias, com as linhas publicadas fixas como medicao.

    `pisos_pct` informa, por origem e destino, um piso condicional em pontos
    percentuais da propria origem. O piso entra como parcela ja alocada e o
    ajuste so reparte o que sobra, entao a celula final nunca fica abaixo dele.
    `fidelidade` ativa a regra de base propria fiel quando o mesmo nome aparece
    na origem e no destino, que e o caso do 2o turno estadual.
    """
    linhas = list(origem)
    colunas = list(destino)
    r = _normalizar(origem)
    c = _normalizar(destino)
    tabela_prior = PRIORS[prior_nome]
    mapa = slots_destino(colunas)
    pisos_pct = pisos_pct or {}
    fontes_do_piso = fontes_do_piso or {}

    fixo: dict = {}
    livre: dict = {}
    marca: dict = {}
    pisos: dict = {}
    for nome in linhas:
        publicado = medidas.get(nome, {})
        for destino_nome in colunas:
            chave = (nome, destino_nome)
            if destino_nome in publicado:
                fixo[chave] = r[nome] * publicado[destino_nome] / 100
                livre[chave] = False
                marca[chave] = "medida"
                continue
            piso = pisos_pct.get(nome, {}).get(destino_nome)
            fixo[chave] = r[nome] * piso / 100 if piso else 0.0
            livre[chave] = True
            marca[chave] = "estimada"
            if piso:
                pisos[chave] = fixo[chave]

    residuo_linha = [r[nome] - sum(fixo[(nome, d)] for d in colunas) for nome in linhas]
    residuo_coluna = [c[d] - sum(fixo[(nome, d)] for nome in linhas) for d in colunas]
    if min(residuo_linha) < -1e-9 or min(residuo_coluna) < -1e-9:
        raise ValueError("Linhas publicadas incompativeis com as margens")

    prior = [[0.0] * len(colunas) for _ in linhas]
    for i, nome in enumerate(linhas):
        if prior_empirica and nome in prior_empirica:
            peso = prior_empirica[nome]
        else:
            peso = tabela_prior.get(campo_de(nome), tabela_prior["nao_escolha"])
        fiel = fidelidade is not None and nome in destino
        sobra = 1.0 - (fidelidade or 0.0) if fiel else 1.0
        resto = (
            sum(peso_destino(peso, d, mapa) for d in colunas if d != nome)
            if fiel
            else 0.0
        )
        for j, destino_nome in enumerate(colunas):
            if not livre[(nome, destino_nome)]:
                continue
            if fiel and destino_nome == nome:
                valor = fidelidade or 0.0
            elif fiel:
                base = peso_destino(peso, destino_nome, mapa)
                valor = sobra * base / resto if resto > 0 else sobra
            else:
                valor = peso_destino(peso, destino_nome, mapa)
            prior[i][j] = max(valor, 1e-9)

    ajustado = ipf(prior, residuo_linha, residuo_coluna)
    final = {
        (nome, colunas[j]): fixo[(nome, colunas[j])] + ajustado[i][j]
        for i, nome in enumerate(linhas)
        for j in range(len(colunas))
    }
    extra = {
        "motor": "ipf_2niveis",
        "prior": prior_nome,
        "prior_empirica": bool(prior_empirica),
        "fidelidade": fidelidade,
        "linhas_medidas": sorted(set(medidas) & set(linhas)),
        "linhas_ancoradas": sorted({nome for nome, _ in pisos}),
    }
    return montar_saida(
        linhas, colunas, r, c, final, marca, pisos, fontes_do_piso, extra
    )


def _prior_condicional(
    peso_origem: dict, peso_via: dict | None, colunas: Sequence[str], mapa: dict
) -> dict:
    """Prior de destino condicionada a origem, com interacao declarada da via.

    O produto slot a slot e o que impede a leitura de Markov: o eleitor que
    passou por um intermediario alinhado a um lado nao tem a mesma distribuicao
    de destino do eleitor da mesma origem que passou pelo outro lado.
    """
    if peso_via is None:
        combinado = dict(peso_origem)
    else:
        combinado = {
            slot: peso_origem.get(slot, 0.0) * peso_via.get(slot, 0.0)
            for slot in ("flavio", "lula", "nao_escolha")
        }
    total = sum(combinado.values())
    if total <= 0:
        combinado = dict(peso_origem)
        total = sum(combinado.values())
    combinado = {k: v / total for k, v in combinado.items()}
    return {d: max(peso_destino(combinado, d, mapa), 1e-12) for d in colunas}


def cadeia_presidencial(
    origem: dict,
    via: dict,
    destino: dict,
    estagio1: dict,
    medidas_via: dict,
    prior_nome: str,
    retencao: float = RETENCAO_PADRAO,
    fonte_do_piso: dict | None = None,
    prior_empirica: dict | None = None,
) -> dict:
    """Cubo origem x presidente 1o turno x presidente 2o turno.

    `estagio1` e a matriz governador x presidente de 1o turno em pontos
    percentuais, com as linhas publicadas ja fixas. Quem ja vota num finalista
    no 1o turno permanece com ele em `retencao`, parcela que entra fixa no cubo.
    O resto e repartido por prior condicionada a origem com interacao da via, e
    o cubo fecha nas celulas do estagio 1 e na margem publicada do 2o turno.
    """
    linhas = list(origem)
    vias = list(via)
    colunas = list(destino)
    r = _normalizar(origem)
    c = _normalizar(destino)
    tabela_prior = PRIORS[prior_nome]
    mapa = slots_destino(colunas)
    mapa_via = slots_destino(vias)
    e1 = {
        (o, v): estagio1[o][v] / 100 for o in linhas for v in vias if v in estagio1[o]
    }

    fixo: dict = {}
    for (o, v), massa in e1.items():
        if v in colunas and v in (FLAVIO, LULA):
            fixo[(o, v, v)] = retencao * massa

    livres = {
        (o, v, d): 0.0
        for (o, v) in e1
        for d in colunas
        if (o, v, d) not in fixo and e1[(o, v)] > 1e-15
    }
    for o, v, d in livres:
        if prior_empirica and o in prior_empirica:
            peso_origem = prior_empirica[o]
        else:
            peso_origem = tabela_prior.get(campo_de(o), tabela_prior["nao_escolha"])
        if mapa_via[v] in ("flavio", "lula") and v in colunas:
            peso_via = None
        else:
            peso_via = tabela_prior.get(campo_de(v), tabela_prior["nao_escolha"])
        livres[(o, v, d)] = _prior_condicional(peso_origem, peso_via, colunas, mapa)[d]

    margem_ov = {
        (o, v): e1[(o, v)] - sum(fixo.get((o, v, d), 0.0) for d in colunas)
        for (o, v) in e1
    }
    margem_d = {
        d: c[d] - sum(v for (_, _, dd), v in fixo.items() if dd == d) for d in colunas
    }
    if min(margem_ov.values()) < -1e-9 or min(margem_d.values()) < -1e-9:
        raise ValueError("retencao incompativel com a margem publicada")

    ajustado = ipf_generico(
        livres,
        [(lambda k: (k[0], k[1]), margem_ov), (lambda k: k[2], margem_d)],
    )
    cubo = dict(fixo)
    for k, valor in ajustado.items():
        cubo[k] = cubo.get(k, 0.0) + valor

    final = {
        (o, d): sum(cubo.get((o, v, d), 0.0) for v in vias)
        for o in linhas
        for d in colunas
    }

    marca: dict = {}
    pisos: dict = {}
    fontes: dict = {}
    for o in linhas:
        publicado = medidas_via.get(o, {})
        for d in colunas:
            if d in publicado and d in (FLAVIO, LULA):
                pisos[(o, d)] = retencao * r[o] * publicado[d] / 100
                fontes[(o, d)] = fonte_do_piso
            else:
                marca[(o, d)] = "estimada"

    extra = {
        "motor": "cadeia_3niveis",
        "cadeia": "governador 1o turno, presidente 1o turno, presidente 2o turno",
        "prior": prior_nome,
        "prior_empirica": False,
        "retencao": retencao,
        "linhas_medidas": [],
        "linhas_ancoradas": sorted({o for o, _ in pisos}),
        "via_pct": {k: round(100 * v, 2) for k, v in _normalizar(via).items()},
        "linhas_medidas_no_estagio1": sorted(set(medidas_via) & set(linhas)),
        "celulas_do_cubo": len(cubo),
    }
    return montar_saida(linhas, colunas, r, c, final, marca, pisos, fontes, extra)


def cadeia_estadual(
    origem: dict,
    destino: dict,
    gov1: dict,
    estagio1: dict,
    estagio1_celulas: Sequence[dict],
    transferencia_estadual: dict,
    prior_nome: str,
    fidelidade: float = FIDELIDADE_PADRAO,
    prior_empirica: dict | None = None,
) -> dict:
    """Cubo governador 1o turno x governador 2o turno x presidente 2o turno.

    O par alvo (governador no 2o turno contra presidente no 2o turno) nao tem
    linha publicada em nenhum dos tres estados. As linhas medidas existem no
    primeiro estagio, governador de 1o turno contra presidente, e o cubo as
    carrega para o 2o turno estadual sem reabri-las: as celulas do estagio 1 e a
    transferencia estadual sao margens do ajuste.
    """
    linhas = list(origem)
    colunas = list(destino)
    origens1 = list(gov1)
    r = _normalizar(origem)
    c = _normalizar(destino)
    g1 = _normalizar(gov1)
    tabela_prior = PRIORS[prior_nome]
    mapa = slots_destino(colunas)

    e1 = {(o, d): estagio1[o][d] / 100 for o in origens1 for d in colunas}
    t12 = {
        (o, g2): transferencia_estadual[o][g2] / 100 for o in origens1 for g2 in linhas
    }

    celulas = {}
    for o in origens1:
        peso_o = {d: e1[(o, d)] for d in colunas}
        for g2 in linhas:
            if t12[(o, g2)] <= 1e-15:
                continue
            if prior_empirica and g2 in prior_empirica:
                peso_via = prior_empirica[g2]
            else:
                peso_via = tabela_prior.get(campo_de(g2), tabela_prior["nao_escolha"])
            for d in colunas:
                if peso_o[d] <= 1e-15:
                    continue
                inter = peso_destino(peso_via, d, mapa)
                celulas[(o, g2, d)] = max(peso_o[d] * t12[(o, g2)] * inter, 1e-15)

    ajustado = ipf_generico(
        celulas,
        [(lambda k: (k[0], k[2]), e1), (lambda k: (k[0], k[1]), t12)],
    )
    final = {
        (g2, d): sum(ajustado.get((o, g2, d), 0.0) for o in origens1)
        for g2 in linhas
        for d in colunas
    }

    # Piso de cada celula do 2o turno estadual. O eleitor que escolheu o mesmo
    # nome no 1o turno so escapa pela infidelidade declarada, entao a massa
    # medida no estagio 1 menos essa fuga e um piso aritmetico da celula.
    estado1 = {(c0["origem"], c0["destino"]): c0 for c0 in estagio1_celulas}
    pisos: dict = {}
    fontes: dict = {}
    for g2 in linhas:
        if g2 not in gov1:
            continue
        fuga = g1[g2] - t12[(g2, g2)]
        for d in colunas:
            base = estado1.get((g2, d))
            if base is None or base["estado"] not in ("medida", "ancorada"):
                continue
            piso = max(0.0, e1[(g2, d)] - fuga)
            if piso <= 1e-9:
                continue
            pisos[(g2, d)] = piso
            fontes[(g2, d)] = base.get("piso_fonte") or base.get("fonte")

    marca = {(g2, d): "estimada" for g2 in linhas for d in colunas}
    extra = {
        "motor": "cadeia_3niveis",
        "cadeia": ("governador 1o turno, governador 2o turno, presidente 2o turno"),
        "prior": prior_nome,
        "prior_empirica": False,
        "fidelidade": fidelidade,
        "linhas_medidas": [],
        "linhas_ancoradas": sorted({g2 for g2, _ in pisos}),
        "origem_do_estagio1_pct": {k: round(100 * v, 2) for k, v in g1.items()},
        "celulas_do_cubo": len(ajustado),
    }
    return montar_saida(linhas, colunas, r, c, final, marca, pisos, fontes, extra)


def vazamento(matriz: dict, origem: str, destino: str) -> float | None:
    cond = matriz["condicional_pct"].get(origem)
    if not cond:
        return None
    return round(100 - cond.get(destino, 0.0), 2)


def melhor_do_campo(valores: dict, campo: str) -> tuple[str | None, float]:
    candidatos = {k: v for k, v in valores.items() if campo_de(k) == campo}
    if not candidatos:
        return None, 0.0
    nome = max(candidatos, key=lambda k: candidatos[k])
    return nome, candidatos[nome]


def celula(matriz: dict, origem: str, destino: str) -> dict:
    return next(
        c
        for c in matriz["celulas"]
        if c["origem"] == origem and c["destino"] == destino
    )


def coerencia_turno1_turno2(
    medidas_1t: dict,
    medidas_2t: dict,
    origem_pct: dict,
    retencao: float = RETENCAO_PADRAO,
) -> list[dict]:
    """Confere se a linha medida de 2o turno respeita o piso da de 1o turno.

    Onde o instituto mede os dois turnos, o valor de 2o turno nao pode ficar
    abaixo do de 1o multiplicado pela retencao declarada. Onde ficar, a
    incoerencia e do par de medicoes e precisa ser reportada, nunca corrigida
    em silencio.
    """
    saida = []
    for origem, linha2 in medidas_2t.items():
        linha1 = medidas_1t.get(origem, {})
        for destino in (FLAVIO, LULA):
            if destino not in linha1 or destino not in linha2:
                continue
            piso = linha1[destino] * retencao
            massa = origem_pct.get(origem, 0.0)
            saida.append(
                {
                    "origem": origem,
                    "destino": destino,
                    "turno1_pct": linha1[destino],
                    "turno2_pct": linha2[destino],
                    "piso_pct": round(piso, 2),
                    "folga_pp": round(linha2[destino] - piso, 2),
                    "coerente": linha2[destino] >= piso - 1e-9,
                    "massa_da_origem_pct": massa,
                }
            )
    return saida


def faixa(valores: Iterable[float | None]) -> tuple[float, float]:
    limpos = [v for v in valores if v is not None]
    return min(limpos), max(limpos)
