"""Textos do bloco "O registro digital do voto" do capítulo de logs.

Números de ``logs.json`` (chave ``rdv``, destilada de ``rdv.json``). Formato,
especificação e alegações de 2022 em ``analysis/apuracao_2t_2026/RDV.md``.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import inteiro, nota, num, p, tabela


def rdv(R: dict) -> str:
    s = R["seis_ufs"]
    comp = ", ".join(
        f"{u['uf']} ({', '.join(u['numero_compartilhado'])})"
        for u in R["ufs"]
        if u["numero_compartilhado"]
    )
    return (
        p(
            f"<strong>{inteiro(R['conferem'])} de {inteiro(R['com_rdv'])} registros digitais do voto</strong> "
            f"repetem, voto a voto, o BU da mesma seção; divergências: {inteiro(R['divergencias'])}. "
            f"{inteiro(R['com_rdv'] - R['contra_busa'])} foram conferidos contra o BU da urna e "
            f"{inteiro(R['contra_busa'])} contra o BU do sistema de apuração; {inteiro(R['busa_sem_votos'])} "
            "deles, do exterior, não tiveram voto algum e conferem por igualdade em zero. Das "
            f"{inteiro(R['tentadas'])} seções tentadas, {inteiro(R['sem_aux'])} não têm arquivo de "
            f"transmissão publicado (as mesmas sem BU) e {inteiro(R['aux_sem_rdv'])} têm o arquivo sem RDV. "
            f"Listas fora da ordem que a especificação exige: {inteiro(R['listas_fora_de_ordem'])}.",
            "verificado",
        )
        + p(
            "O RDV guarda cada cargo numa lista própria, ordenada por tipo de voto e pelo que foi "
            "digitado, sem registro por eleitor. Ele confere o BU por outra via publicada pelo TSE, mas não "
            "liga o voto de presidente ao de governador de uma mesma pessoa, nem a ordem dos votos ao "
            "horário. O voto cruzado presidente × governador só tem limites: o intervalo que as duas "
            "contagens permitem, somadas as seções da UF (tabela abaixo).",
            "verificado",
        )
        + p(
            f"<strong>{num(s['governador_com_numero_de_presidente_pct'], 1)}% dos nulos de governador</strong> "
            f"nas seis UFs ({inteiro(s['governador_com_numero_de_presidente'])} de "
            f"{inteiro(s['nulos_governador'])}) são 13 ou 22, o número de um finalista presidencial, "
            f"digitado no campo do governo. Na outra direção, {num(s['presidente_com_numero_de_governador_pct'], 1)}% "
            f"dos nulos de presidente ({inteiro(s['presidente_com_numero_de_governador'])} de "
            f"{inteiro(s['nulos_presidente'])}) são o número de um candidato a governador da UF. As taxas "
            f"são piso onde um candidato a governador tem o número de um finalista, {comp}: ali a troca vira "
            "voto válido e não aparece.",
            "verificado",
        )
        + nota(
            "hipotese",
            "A digitação mostra o que foi teclado, não a intenção: erro de ordem entre as telas, protesto "
            "ou recusa das duas candidaturas cabem no mesmo número. Parte da diferença de brancos e nulos "
            "entre governador e presidente nessas UFs é número de presidente digitado no governo.",
            "O que o número digitado não diz.",
        )
    )


def tabela_limites(R: dict) -> str:
    nome = {"13": "Lula (13)", "22": "Flávio (22)"}
    linhas = []
    for u in R["ufs"]:
        for x in u["limites"]:
            gov = (
                f"{x['governador']} ({x['partido']})"
                if x["partido"]
                else x["governador"]
            )
            linhas.append(
                [
                    u["uf"],
                    nome.get(x["presidente"], x["presidente"]),
                    gov,
                    f"{num(x['min_pct'], 1)}% a {num(x['max_pct'], 1)}%",
                    f"{num(x['independencia_pct'], 1)}%",
                ]
            )
    return tabela(
        [
            "UF",
            "presidente",
            "governador (número e partido)",
            "parcela dos votantes no par: limites",
            "se fossem independentes",
        ],
        linhas,
        "Voto cruzado presidente × governador: só os limites que o RDV permite (soma das seções)",
    )


def limites_itens() -> list[str]:
    return [
        "O RDV não liga votos entre cargos nem a horários: a tabela do voto cruzado traz limites, não medição.",
    ]
