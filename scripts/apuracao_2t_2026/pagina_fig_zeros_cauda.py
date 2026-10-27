"""Subparte "A cauda: de onde o voto sumiu" do bloco "Seções com zero voto".

Responde à pergunta do autor sobre as seções que deram voto a Flávio no 1º turno e
nenhum, ou quase nenhum, no 2º. Interface: ``bloco(Z) -> str`` e
``limites_itens(Z) -> list[str]``, com ``Z`` o conteúdo de ``zeros.json``; sem o
bloco ``cauda`` (JSON antigo), as duas devolvem vazio. Todo número sai de
``Z["cauda"]``, gravado por ``scripts/apuracao_2t_2026/zeros_cauda.py``; os nomes de
candidatura vêm de ``governadores.json`` e ``tse_candidatos.json`` pelo JSON, nunca
digitados aqui. Selos pelo padrão da casa; sem travessão; nunca "fraude"; leitura
sempre do eleitorado da seção, nunca do voto de uma pessoa.
"""

from __future__ import annotations

import math
from collections import Counter
from html import escape
from typing import Any

from apuracao_2026.pagina_comum import inteiro, nota, num, p, tabela
from apuracao_2026.pagina_fig_base import nome_bonito

from .pagina_fig_anomalia_base import extenso

ROTULO = "Atipicidade pede explicação, não prova irregularidade."
CAMPO_DIREITA = ("direita", "centro-direita")
ALIANCA = "coligação com o PT"


# ------------------------------------------------------------------ formato


def lista_e(itens: list[str]) -> str:
    itens = [i for i in itens if i]
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def pct_sig(x: float) -> str:
    """Percentual com dois algarismos significativos: 37%, 5,0%, 1,8%, 0,67%."""
    if x <= 0:
        return "0%"
    if x >= 10:
        return f"{num(x, 0)}%"
    casas = max(1, 1 - math.floor(math.log10(x)))
    return f"{num(x, casas)}%"


def _sig2(v: float) -> str:
    return inteiro(v) if v >= 10 else num(v, 1)


def um_em(prob: float) -> str:
    """Chance como "1 em N", legível: 1 em 45, 1 em 16 milhões."""
    if prob <= 0:
        return "menos de 1 em 1 trilhão"
    n = 1 / prob
    if n < 1e6:
        return f"1 em {inteiro(n)}"
    for escala, um, varios in ((1e9, "bilhão", "bilhões"), (1e6, "milhão", "milhões")):
        if 1e12 > n >= escala:
            v = n / escala
            return f"1 em {_sig2(v)} {um if v < 2 else varios}"
    return "menos de 1 em 1 trilhão"


def extenso_f(n: int) -> str:
    """Número por extenso concordando com substantivo feminino (seções, urnas)."""
    return {1: "uma", 2: "duas"}.get(n, extenso(n))


def urna_id(n: int | None) -> str:
    """Número interno da urna como o log o escreve, com oito algarismos."""
    return "s/d" if n is None else f"{n:08d}"


def seta(a: int, b: int) -> str:
    """'155 → 134' sem quebra de linha dentro da célula."""
    return f"{inteiro(a)}&nbsp;→&nbsp;{inteiro(b)}"


def votos_txt(k: int) -> str:
    return f"{inteiro(k)} voto" + ("s" if k != 1 else "")


def lugar(f: dict[str, Any]) -> str:
    return f"{escape(f['municipio'])} ({escape(f['uf'])})"


def chave(f: dict[str, Any]) -> list:
    return [f["uf"], f["mun"], f["zona"], f["secao"]]


def candidatura(c: dict[str, Any], com_votos: bool = True) -> str:
    """'Omar Aziz (PSD, coligação com o PT) 176', com o campo só na direita."""
    nome = nome_bonito(c.get("nome_urna") or f"número {c['numero']}")
    extra = [c.get("partido") or ""]
    if c.get("campo") in CAMPO_DIREITA:
        extra.append(c["campo"])
    if c.get("comparacao") == ALIANCA:
        extra.append(ALIANCA)
    rot = f"{escape(nome)} ({escape(', '.join(x for x in extra if x))})"
    return f"{rot} {inteiro(c['votos'])}" if com_votos else rot


def _gov_turno(t: dict[str, Any] | None) -> str:
    if not t:
        return "s/d"
    return ", ".join(
        f"{escape(nome_bonito(c.get('nome_urna') or str(c['numero'])))} {inteiro(c['votos'])}"
        for c in t["candidatos"]
    )


# ------------------------------------------------------------------ textos


def _abertura(C: dict) -> str:
    np_ = C["numero_pequeno"]
    ks = [x for x in np_["por_k"] if x["k"] > 0]
    lista = lista_e([f"{inteiro(x['secoes'])} com {votos_txt(x['k'])}" for x in ks])
    return p(
        f"Das {inteiro(np_['secoes_zero_2t'])} seções sem voto em Flávio no 2º turno, "
        f"{inteiro(np_['com_voto_1t'])} tinham voto nele no 1º: {lista}. Somam "
        f"{inteiro(np_['votos_1t'])} votos no 1º turno.",
        "verificado",
    )


def _regua(C: dict) -> str:
    np_ = C["numero_pequeno"]
    lim = C["regras"]["limite_numero_pequeno"]
    base = {x["k"]: x for x in np_["taxa_base"]}
    chances = lista_e(
        [
            f"{pct_sig(base[k]['chance_aprox_pct'])} com {votos_txt(k)}"
            for k in range(1, lim + 1)
        ]
    )
    k1 = base[1]
    resto = "; ".join(
        f"com {votos_txt(k)}, {inteiro(base[k]['chegaram_a_zero'])} de "
        f"{inteiro(base[k]['secoes_pais'])}"
        for k in range(2, lim + 1)
    )
    meio, topo = np_["faixas"][1], np_["faixas"][2]
    zero_meio = (
        "nenhuma chegou"
        if meio["chegaram_a_zero"] == 0
        else f"{inteiro(meio['chegaram_a_zero'])} chegaram"
    )
    return p(
        "A régua de referência é a da independência: se cada eleitor que escolheu um "
        "finalista no 2º turno votasse em Flávio com a chance da fatia de Flávio nos válidos "
        "do 1º turno, um sem combinar com o outro, a seção terminaria com zero com chance "
        "(1 − p)<sup>n</sup>, perto de e<sup>−k</sup> para quem tinha k votos: "
        f"{chances}. No país, das {inteiro(k1['secoes_pais'])} seções que deram exatamente "
        f"1 voto a Flávio no 1º turno, {inteiro(k1['chegaram_a_zero'])} chegaram a zero no "
        f"2º; {resto}. Das {inteiro(meio['secoes_pais'])} seções com {inteiro(meio['de'])} "
        f"a {inteiro(meio['ate'])} votos, {zero_meio} a zero; das "
        f"{inteiro(topo['secoes_pais'])} com {inteiro(topo['de'])}, "
        f"{extenso_f(topo['chegaram_a_zero'])}.",
        "verificado",
    )


def tabela_k(C: dict) -> str:
    np_ = C["numero_pequeno"]
    lim = C["regras"]["limite_numero_pequeno"]
    base = {x["k"]: x for x in np_["taxa_base"]}
    linhas = [
        [
            inteiro(k),
            inteiro(base[k]["secoes_pais"]),
            inteiro(base[k]["chegaram_a_zero"]),
            pct_sig(base[k]["chance_aprox_pct"]),
            num(base[k]["zeros_esperados"], 1),
        ]
        for k in range(1, lim + 1)
    ]
    meio, topo = np_["faixas"][1], np_["faixas"][2]
    linhas.append(
        [
            f"{inteiro(meio['de'])} a {inteiro(meio['ate'])}",
            inteiro(meio["secoes_pais"]),
            inteiro(meio["chegaram_a_zero"]),
            f"de {pct_sig(base[meio['de']]['chance_aprox_pct'])} a "
            f"{pct_sig(base[meio['ate']]['chance_aprox_pct'])}",
            num(meio["zeros_esperados"], 1),
        ]
    )
    linhas.append(
        [
            inteiro(topo["de"]),
            inteiro(topo["secoes_pais"]),
            inteiro(topo["chegaram_a_zero"]),
            pct_sig(base[topo["de"]]["chance_aprox_pct"]),
            num(topo["zeros_esperados"], 1),
        ]
    )
    return tabela(
        [
            "votos de Flávio no 1º turno",
            "seções no país",
            "chegaram a zero no 2º turno",
            "chance de zero, e<sup>−k</sup>",
            "zeros esperados sob independência",
        ],
        linhas,
        "Brasil sem o exterior, seções com BU de presidente nos dois turnos. Chance de zero: "
        "aproximação e<sup>−k</sup> da conta (1 − p)<sup>n</sup>; zeros esperados: soma de "
        "(1 − p)<sup>n</sup> seção a seção, com p a fatia de Flávio nos válidos do 1º turno "
        "e n os votos em Lula e Flávio no 2º turno.",
    )


def _leitura_pequeno(C: dict) -> str:
    np_ = C["numero_pequeno"]
    lim = C["regras"]["limite_numero_pequeno"]
    pq, topo = np_["faixas"][0], np_["faixas"][2]
    obs, esp = pq["chegaram_a_zero"], pq["zeros_esperados"]
    rel = (
        "menos que o acaso, porque Flávio ganhou voto do 1º para o 2º turno"
        if obs < esp
        else "no nível do acaso"
    )
    maior = next(
        (x for x in np_["secoes_com_voto_1t"] if x["flavio_1t"] == topo["de"]), None
    )
    fim = ""
    if maior is not None:
        fim = (
            f" O zero depois de {votos_txt(maior['flavio_1t'])} é outra coisa: em "
            f"{escape(maior['municipio'])}, a mesma conta dá {um_em(maior['chance_zero'])}."
        )
    return p(
        f"Até {votos_txt(lim)}, o zero é aritmética de número pequeno: a independência "
        f"previa {num(esp, 0)} zeros nessas {inteiro(pq['secoes_pais'])} seções e houve "
        f"{inteiro(obs)}, {rel}.{fim}",
        "inferencia",
    )


def _cauda(C: dict, nomes_tipo: dict[str, str]) -> str:
    R, ca, fichas = C["regras"], C["cauda"], C["fichas"]
    a1, q = R["queda_ate_1"], R["queda_80"]
    tipos = Counter(f["tipo"] for f in fichas)
    tipos_txt = lista_e(
        [f"{inteiro(n)} em {nomes_tipo.get(t, t)}" for t, n in tipos.most_common()]
    )
    tipos_txt = f"ficam {tipos_txt}"
    novas = sum(1 for f in fichas if f["secao_nova"])
    iguais = sum(
        1 for f in fichas if f["urna"]["mesma_urna"] and f["urna"]["mesma_carga"]
    )
    rdv_ok = sum(1 for f in fichas if (f["rdv"] or {}).get("confere") == 1)
    n = len(fichas)
    urna_txt = (
        f"Nas {inteiro(n)}, a urna do BU é a mesma nos dois turnos, com a mesma carga, e o "
        "RDV do 2º turno confere com o BU."
        if iguais == rdv_ok == n
        else f"A urna e a carga são as mesmas nos dois turnos em {inteiro(iguais)} das "
        f"{inteiro(n)}, e o RDV do 2º turno confere com o BU em {inteiro(rdv_ok)}."
    )
    return p(
        f"A cauda está acima de {votos_txt(R['limite_numero_pequeno'])}. No Brasil, sem o "
        f"exterior, entre as seções com ao menos {inteiro(R['piso_nominal_2t'])} votos "
        f"nominais no 2º turno, {inteiro(ca['queda_ate_1'])} seções deram "
        f"{inteiro(a1['flavio_1t_min'])} votos ou mais a Flávio no 1º turno e "
        f"{inteiro(a1['flavio_2t_max'])} ou nenhum no 2º; {inteiro(ca['queda_80'])} deram "
        f"{inteiro(q['flavio_1t_min'])} ou mais e perderam ao menos "
        f"{inteiro(q['queda_min_pct'])}% desses votos. Juntas, são {inteiro(ca['uniao'])} "
        f"seções; {inteiro(ca['nas_duas'])} entram nas duas regras. Pelo nome do prédio, {tipos_txt}. "
        f"{extenso_f(novas).capitalize()} são seções novas, sem a mesma chave em 2022. "
        f"{urna_txt}",
        "verificado",
    )


def _extras(xs: list[dict]) -> str:
    return "; ".join(
        f"{escape(x['municipio'])} ({escape(x['chave'][0])}), {inteiro(x['aptos_2t'])} "
        f"aptos, comparecimento de {inteiro(x['comparecimento_1t'])} para "
        f"{inteiro(x['comparecimento_2t'])}"
        for x in xs
    )


def _espelho(C: dict) -> str:
    R, es, ca = C["regras"], C["espelho"], C["cauda"]
    a1, q = R["queda_ate_1"], R["queda_80"]
    if es["queda_ate_1"] == es["queda_80"] == 0:
        h = (
            f"O espelho está vazio: nenhuma seção com {inteiro(a1['flavio_1t_min'])} votos "
            f"ou mais em Lula no 1º turno terminou com {inteiro(a1['flavio_2t_max'])} ou "
            f"nenhum no 2º, e nenhuma com {inteiro(q['flavio_1t_min'])} ou mais perdeu "
            f"{inteiro(q['queda_min_pct'])}% desses votos."
        )
    else:
        h = (
            f"O espelho, com Lula no lugar de Flávio, pega {inteiro(es['queda_ate_1'])} e "
            f"{inteiro(es['queda_80'])} seções."
        )
    sp, se = ca["sem_piso"], es["sem_piso"]
    extras = {tuple(x["chave"]): x for x in sp["extras"] + se["extras"]}
    if extras:
        h += (
            f" Sem o piso de {inteiro(R['piso_nominal_2t'])} votos nominais, as duas regras "
            f"pegam {inteiro(sp['queda_ate_1'])} e {inteiro(sp['queda_80'])} seções, e o "
            f"espelho, {inteiro(se['queda_ate_1'])} e {inteiro(se['queda_80'])}. As seções a "
            f"mais ficam em {_extras(list(extras.values()))}. Ali um voto pesa demais."
        )
        dois_lados = {tuple(x["chave"]) for x in sp["extras"]} & {
            tuple(x["chave"]) for x in se["extras"]
        }
        for ch in sorted(dois_lados):
            x = extras[ch]
            h += (
                f" A de {escape(x['municipio'])} entra nos dois lados porque o "
                f"comparecimento caiu de {inteiro(x['comparecimento_1t'])} para "
                f"{inteiro(x['comparecimento_2t'])}, e os dois finalistas caíram juntos."
            )
    return p(h, "verificado")


def _calibra(C: dict) -> str:
    ca, es = C["cauda"], C["espelho"]
    e = ca["esperado_independencia"]
    return p(
        "A mesma régua mede as duas regras. No país, a independência esperaria "
        f"{num(e['queda_ate_1'], 1)} seções caindo para quase nada pela primeira regra, e "
        f"houve {inteiro(ca['queda_ate_1'])}; esperaria {num(e['queda_80'], 1)} pela "
        f"segunda, e houve {inteiro(ca['queda_80'])}. Para Lula, esperaria "
        f"{num(e['espelho_queda_ate_1'], 1)} e {num(e['espelho_queda_80'], 1)}, e houve "
        f"{inteiro(es['queda_ate_1'])} e {inteiro(es['queda_80'])}.",
        "verificado",
    )


def _calibra_leitura(C: dict) -> str:
    ca, fichas = C["cauda"], C["fichas"]
    e = ca["esperado_independencia"]
    so_a = [f for f in fichas if f["criterios"] == ["queda_ate_1"]]
    com_b = [f for f in fichas if "queda_80" in f["criterios"]]
    ks = sorted({f["flavio_1t"] for f in so_a})
    primeira = (
        f"A primeira regra, sozinha, não separa a cauda do acaso: as "
        f"{inteiro(len(so_a))} seções que só ela pega, de "
        f"{' ou '.join(inteiro(k) for k in ks)} votos para 1, cabem no que a independência "
        "produz no país."
        if ca["queda_ate_1"] <= e["queda_ate_1"]
        else "A primeira regra já pega mais seções do que a independência produz no país."
    )
    if not com_b:
        return p(primeira, "inferencia")
    lo = max(com_b, key=lambda f: f["chance_independencia"])
    hi = min(com_b, key=lambda f: f["chance_independencia"])
    return p(
        f"{primeira} O excesso está na segunda: nas {inteiro(len(com_b))} seções que "
        f"perderam {inteiro(C['regras']['queda_80']['queda_min_pct'])}% ou mais, a chance de "
        f"terminar com tão pouco vai de {um_em(lo['chance_independencia'])}, em "
        f"{lugar(lo)}, a {um_em(hi['chance_independencia'])}, em {lugar(hi)}.",
        "inferencia",
    )


def _bolsonaro_2022(f: dict[str, Any]) -> str:
    if f["secao_nova"]:
        return "seção nova"
    t = f.get("t2022") or {}
    b = t.get("bolsonaro_2t")
    pv = f.get("politize_bolsonaro22_2t_pct_validos")
    if b is None and pv is None:
        return "s/d"
    votos = "" if b is None else f"{inteiro(b)} "
    return f"{votos}({num(pv, 1)}%)" if pv is not None else votos.strip()


def tabela_cauda(C: dict) -> str:
    linhas = []
    for f in C["fichas"]:
        g = f["governador"]
        gov = f"1º: {_gov_turno(g['t1'])}."
        gov += (
            f" 2º: {_gov_turno(g['t2'])}."
            if g["t2"]
            else " Sem 2º turno de governador na UF."
        )
        linhas.append(
            [
                f"{escape(f['uf'])} {inteiro(f['zona'])}/{inteiro(f['secao'])}",
                escape(f["municipio"]),
                escape(f["local"] or "s/d"),
                seta(f["flavio_1t"], f["flavio_2t"]),
                seta(f["lula_1t"], f["lula_2t"]),
                seta(f["comparecimento_1t"], f["comparecimento_2t"]),
                um_em(f["chance_independencia"]),
                gov,
                _bolsonaro_2022(f),
            ]
        )
    return tabela(
        [
            "seção (UF zona/seção)",
            "município",
            "local",
            "Flávio, 1º → 2º",
            "Lula, 1º → 2º",
            "compareceram, 1º → 2º",
            "chance de tão pouco sob independência",
            "governador, 1º turno (quatro primeiros) e 2º",
            "Bolsonaro, 2º turno de 2022: votos (% dos válidos)",
        ],
        linhas,
        f"As {inteiro(len(C['fichas']))} seções da cauda, da maior para a menor votação de "
        "Flávio no 1º turno. Nomes de candidatura de governador de governadores.json e "
        "tse_candidatos.json; 2022 pela mesma chave no arquivo por seção e pelo cadastro do "
        "Politize; seção nova não tem a mesma chave em 2022.",
    )


def _fluxo(C: dict) -> str:
    fichas = C["fichas"]
    n = len(fichas)
    caiu = [f for f in fichas if f["lula_2t"] < f["lula_1t"]]
    caiu_comp = [f for f in caiu if f["comparecimento_2t"] < f["comparecimento_1t"]]
    subiu = [f for f in fichas if f["lula_2t"] > f["lula_1t"]]
    troca = [
        f
        for f in subiu
        if f["lula_2t"] - f["lula_1t"] >= f["flavio_1t"] - f["flavio_2t"]
    ]
    misto = [f for f in subiu if f not in troca]
    texto = (
        f"Em {inteiro(len(subiu))} das {inteiro(n)}, Lula ganhou votos do 1º para o 2º "
        f"turno; em {inteiro(len(troca))} dessas, ao menos tantos quantos Flávio perdeu."
    )
    if caiu_comp:
        texto += (
            " Em "
            + lista_e([lugar(f) for f in caiu_comp])
            + ", Lula também perdeu votos e o comparecimento caiu ("
            + lista_e(
                [
                    inteiro(f["comparecimento_1t"] - f["comparecimento_2t"])
                    for f in caiu_comp
                ]
            )
            + " eleitores a menos)."
        )
    h = p(texto, "verificado")
    mix = ""
    if misto:
        f = misto[0]
        mix = (
            f" {lugar(f)} tem as duas coisas: Flávio perdeu "
            f"{inteiro(f['flavio_1t'] - f['flavio_2t'])}, Lula ganhou "
            f"{inteiro(f['lula_2t'] - f['lula_1t'])} e "
            f"{inteiro(f['comparecimento_1t'] - f['comparecimento_2t'])} eleitores a menos "
            "votaram."
        )
    h += p(
        "Onde Lula e o comparecimento caíram juntos, o voto que saiu de Flávio é compatível "
        "com abstenção; onde Lula ganhou ao menos o que Flávio perdeu, com troca de lado."
        f"{mix} O dado da seção é agregado e não separa uma coisa da outra eleitor a eleitor.",
        "inferencia",
    )
    return h


def _por_ch(C: dict) -> dict[tuple, dict]:
    return {tuple(chave(f)): f for f in C["fichas"]}


def _governador(C: dict) -> str:
    G = C["governador"]
    fichas = _por_ch(C)
    ufs = sorted({f["uf"] for f in C["fichas"]})
    com = [u for u in ufs if u in G["ufs_com_2t"]]
    sem = [u for u in ufs if u not in G["ufs_com_2t"]]
    h = p(
        f"Entre as UFs da cauda, {lista_e(com)} tiveram 2º turno de governador; "
        f"{lista_e(sem)}, não. A tabela traz os votos de governador nas mesmas seções, "
        "nos dois turnos.",
        "verificado",
    )
    caiu = [fichas[tuple(x)] for x in G["direita_caiu"]]
    if caiu:
        somas = lista_e(
            [
                f"{inteiro(f['governador']['t1']['direita_e_centro_direita'])} para "
                f"{inteiro(f['governador']['t2']['direita_e_centro_direita'])} em "
                f"{escape(f['municipio'])}"
                for f in caiu
            ]
        )
        ufs_caiu = sorted({f["uf"] for f in caiu})
        maior = max(
            caiu,
            key=lambda f: f["governador"]["t1"]["direita_e_centro_direita"]
            - f["governador"]["t2"]["direita_e_centro_direita"],
        )
        t1 = {c["numero"]: c for c in maior["governador"]["t1"]["candidatos"]}
        t2 = {c["numero"]: c for c in maior["governador"]["t2"]["candidatos"]}
        alianca = [c for c in t2.values() if c.get("comparacao") == ALIANCA]
        fora = [
            c for n, c in t1.items() if n not in t2 and c.get("campo") in CAMPO_DIREITA
        ]
        detalhe = ""
        if alianca and alianca[0]["numero"] in t1:
            a = alianca[0]
            detalhe = (
                f" Em {escape(maior['municipio'])}, {candidatura(a, False)} foi de "
                f"{inteiro(t1[a['numero']]['votos'])} para {inteiro(a['votos'])} votos"
            )
            if len(fora) == 1:
                detalhe += (
                    f", e {candidatura(fora[0], False)}, que teve "
                    f"{inteiro(fora[0]['votos'])} votos no 1º turno, não disputou o 2º."
                )
            elif fora:
                detalhe += (
                    f", e {lista_e([candidatura(c, False) for c in fora])}, que somaram "
                    f"{inteiro(sum(c['votos'] for c in fora))} votos no 1º turno, não "
                    "disputaram o 2º."
                )
            else:
                detalhe += "."
        nomes = lista_e([escape(f["municipio"]) for f in caiu])
        h += p(
            f"Em {nomes} ({', '.join(ufs_caiu)}), o voto de Flávio sumiu junto com o voto "
            "de governador de direita e centro-direita, nas mesmas seções e no mesmo dia: "
            f"{somas}.{detalhe}",
            "inferencia",
        )
    return h


def _contrario(C: dict) -> str:
    G, ca, fichas = C["governador"], C["cauda"], C["fichas"]
    por = _por_ch(C)
    itens = []
    for x in G["direita_subiu"]:
        f = por[tuple(x)]
        g = f["governador"]
        lider = g["t2"]["candidatos"][0]
        itens.append(
            f"<li>Em {lugar(f)}, a outra seção da cauda com 2º turno de governador, a "
            "direção é a oposta: o voto de governador de direita e centro-direita foi de "
            f"{inteiro(g['t1']['direita_e_centro_direita'])} para "
            f"{inteiro(g['t2']['direita_e_centro_direita'])}, com "
            f"{inteiro(lider['votos'])} de {candidatura(lider, False)}, e Flávio foi de "
            f"{inteiro(f['flavio_1t'])} para {inteiro(f['flavio_2t'])}. Ali o governador de "
            "direita e centro-direita cresceu e o presidente não acompanhou.</li>"
        )
    e = ca["esperado_independencia"]
    so_a = [f for f in fichas if f["criterios"] == ["queda_ate_1"]]
    if ca["queda_ate_1"] <= e["queda_ate_1"]:
        itens.append(
            f"<li>A regra de {inteiro(C['regras']['queda_ate_1']['flavio_1t_min'])} votos "
            f"para 1 ou nenhum pega {inteiro(ca['queda_ate_1'])} seções, e a independência "
            f"esperaria {num(e['queda_ate_1'], 1)}: {inteiro(len(so_a))} das "
            f"{inteiro(len(fichas))} seções da tabela cabem no acaso.</li>"
        )
    outro = [f for f in fichas if f["tipo"] == "outro"]
    if outro:
        itens.append(
            f"<li>{inteiro(len(outro))} das {inteiro(len(fichas))} ficam em local cujo nome "
            "não diz o tipo: pelo nome do prédio, a leitura de comunidade indígena não vale "
            "para todas.</li>"
        )
    if not itens:
        return ""
    return nota("contrario", "<ul>" + "".join(itens) + "</ul>", "O que a cauda não diz")


def _por_dentro(C: dict) -> str:
    h = ""
    por = _por_ch(C)
    for x in C["por_dentro"]:
        f = por[tuple(x["chave"])]
        b1, b2, l1, l2 = x["bu_1t"], x["bu_2t"], x["log_1t"], x["log_2t"]
        rdv = x["rdv"] or {}
        pr = rdv.get("presidente") or {}
        cab = f"<strong>{lugar(f)}, zona {inteiro(f['zona'])}, seção {inteiro(f['secao'])}, por dentro.</strong> "
        if len(l1["urnas_log"] or []) > 1:
            mesma = (
                "com a mesma carga do 1º"
                if b1["codigo_carga"] == b2["codigo_carga"]
                else "com carga diferente da do 1º"
            )
            h += p(
                cab
                + f"O log do 1º turno registra {extenso_f(len(l1['urnas_log']))} urnas, "
                + lista_e(l1["urnas_log"])
                + ": houve troca de urna no dia, e o BU saiu da "
                + f"{urna_id(b1['numero_interno_urna'])}"
                + (", registrada como reserva da seção" if b1["tipo_urna"] == 4 else "")
                + ". No 2º turno, só a "
                + lista_e(l2["urnas_log"] or [])
                + f" aparece no log, {mesma}, e o RDV "
                + ("confere" if rdv.get("confere") == 1 else "não confere")
                + " com o BU.",
                "verificado",
            )
            continue
        hab = l2["habilitacao"] or {}
        nova = (
            f"Seção nova, sem a mesma chave no arquivo de 2022, com {inteiro(b2['aptos'])} "
            "eleitores aptos."
            if x["secao_nova"]
            else f"Seção com {inteiro(b2['aptos'])} eleitores aptos."
        )
        reinicio = l2["reinicios_durante_votacao"] or 0
        reinicio_txt = (
            "sem reinício durante a votação"
            if reinicio == 0
            else f"{inteiro(reinicio)} reinício"
            + ("s" if reinicio > 1 else "")
            + " durante a votação"
        )
        urna = (
            "a mesma urna nos dois turnos"
            if b1["numero_interno_urna"] == b2["numero_interno_urna"]
            else "urnas diferentes nos dois turnos"
        )
        carga = (
            "com a mesma carga"
            if b1["codigo_carga"] == b2["codigo_carga"]
            else "com cargas diferentes"
        )
        dia_carga = "/".join(reversed((b2["carga_em"] or "")[:10].split("-")))
        nulos_dig = pr.get("nulos_digitados") or {}
        tc = x.get("troca_de_campo_uf") or {}
        troca = ""
        if nulos_dig and len(nulos_dig) == 1:
            dig, n = next(iter(nulos_dig.items()))
            uf_n = (tc.get("presidente_com_numero_de_governador") or {}).get(dig)
            g = f["governador"]
            cands = (g["t2"] or {}).get("candidatos", []) + (g["t1"] or {}).get(
                "candidatos", []
            )
            dono = next((c for c in cands if str(c["numero"]) == dig), None)
            de_quem = (
                f"o número de {escape(nome_bonito(dono['nome_urna']))} para governador"
                if dono and dono.get("nome_urna")
                else "número de governador"
            )
            troca = f"; os {inteiro(n)} nulos foram digitados {escape(dig)}, {de_quem}"
            if uf_n:
                troca += (
                    f", a mesma troca de campo que soma {inteiro(uf_n)} dos "
                    f"{inteiro(tc['nulos_presidente'])} nulos de presidente no "
                    f"{escape(tc['uf'])}"
                )
        nb = pr.get("brancos") or 0
        brancos = "nenhum branco" if nb == 0 else f"{inteiro(nb)} brancos"
        horas = ", ".join(
            f"{h_}h {inteiro(n)}" for h_, n in (l2["por_hora"] or {}).items()
        )
        h += p(
            cab + f"{nova} {urna.capitalize()} "
            f"(número interno {urna_id(b2['numero_interno_urna'])}, modelo "
            f"{escape(b2['modelo_urna'] or 's/d')}), {carga}, de {dia_carga}. O RDV do 2º "
            "turno, o registro embaralhado de cada voto, "
            + ("confere" if rdv.get("confere") == 1 else "não confere")
            + f" com o BU: {inteiro(pr.get('lula'))} votos em Lula, "
            f"{inteiro(pr.get('nulos'))} nulos e {brancos} para presidente{troca}. No 2º turno, {inteiro(hab.get('biometrica'))} eleitores "
            f"foram habilitados pela biometria, {inteiro(hab.get('biografica'))} pelo ano de "
            f"nascimento e {inteiro(hab.get('sem_biometria'))} sem biometria cadastrada; a "
            f"mediana foi de {inteiro(l2['processo_p50_s'])} s da habilitação ao voto e de "
            f"{inteiro(l2['cadencia_p50_s'])} s entre um voto e o próximo, "
            f"{reinicio_txt} e com {inteiro(l2['inspecoes'])} inspeções. Votos por hora, no "
            f"horário local: {horas}; "
            f"o BU registra o encerramento às {escape((b2['encerramento'] or '')[11:16])}. No "
            f"1º turno, com {extenso(len(b1['cargos']))} cargos e "
            f"{extenso(l1['votos_por_eleitor'] or 0)} votos por eleitor, a mesma urna recebeu "
            f"votos das {inteiro(int(l1['primeiro_computo'][:2]))}h às "
            f"{inteiro(int(l1['ultimo_computo'][:2]))}h, com mediana de "
            f"{inteiro(l1['cadencia_p50_s'])} s entre um voto e o próximo.",
            "verificado",
        )
    return h


def _hipotese() -> str:
    return nota(
        "hipotese",
        "Uma explicação compatível com todos os dados acima, e que nenhum dado identifica: "
        "comunidade que vota em bloco por orientação de liderança, com parte do bloco numa "
        "candidatura de centro-direita no 1º turno e tudo consolidado na chapa de governador "
        "e presidente no 2º. O voto é secreto, e nenhum dado público identifica orientação "
        f"de voto. {ROTULO}",
    )


def bloco(Z: dict) -> str:
    """A subparte inteira; vazio quando ``zeros.json`` ainda não tem ``cauda``."""
    C = Z.get("cauda")
    if not C:
        return ""
    nomes_tipo = {x["tipo"]: x["nome"] for x in Z["regra_tipo_local"]["ordem"]}
    return (
        f'<h4 id="zeros-cauda">{escape(C["titulo"])}</h4>'
        + _abertura(C)
        + _regua(C)
        + tabela_k(C)
        + _leitura_pequeno(C)
        + _cauda(C, nomes_tipo)
        + _espelho(C)
        + _calibra(C)
        + _calibra_leitura(C)
        + tabela_cauda(C)
        + _fluxo(C)
        + _governador(C)
        + _contrario(C)
        + _por_dentro(C)
        + _hipotese()
    )


def limites_itens(Z: dict) -> list[str]:
    C = Z.get("cauda")
    if not C:
        return []
    return [
        "A cauda usa a independência como régua: eleitorado de comunidade vota "
        "correlacionado, e a régua separa número pequeno de queda grande, sem medir "
        "probabilidade de irregularidade.",
    ]


__all__ = ["bloco", "limites_itens", "pct_sig", "um_em"]
