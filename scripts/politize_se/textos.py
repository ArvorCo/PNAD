"""Frases por regra para a seção e para o local de votação (prédio).

O build decide quais frases valem e grava, por seção e por prédio, uma lista de
``[código, arg0, arg1, ...]`` com os argumentos já formatados em pt-BR. Os modelos ficam
uma vez só em ``indice.json`` (``frases``); o aplicativo troca ``{0}``, ``{1}``... pelos
argumentos. Assim o texto é gerado por regra no Python, testável aqui, sem repetir a
mesma prosa em 500 mil seções.

Regras de escrita: português corrente, sem travessão, nunca "fraude", sem presumir
gênero ("quem votou", "o eleitorado"), nenhum nome de pessoa além dos dois candidatos,
nenhum nome de local ou município dentro da frase (o aplicativo mostra o nome do local
como título, tal como no cadastro do TSE). Sinal pede explicação, não prova irregularidade.
"""

from __future__ import annotations

from typing import Any

from .tempo import hhmm
from .urna import SITUACOES

ROTULO = "Sinal pede explicação, não prova irregularidade."

# Os seis sinais da régua do dossiê (apuracao_2t_2026.secoes_sinais), em português corrente.
SINAIS_NOME = {
    "delta": "comparecimento 5 pontos ou mais acima do 1º turno",
    "sem_bio": "muitos votantes sem digital cadastrada (10% ou mais e o dobro do município)",
    "ano_nasc": "muitos liberados pelo ano de nascimento (10% ou mais e o dobro do município)",
    "salto_bio": "parcela sem digital reconhecida 5 pontos ou mais acima do 1º turno",
    "tardia": "último voto depois das 19h ou 30 minutos ou mais depois do 1º turno",
    "papel": "boletim do sistema de apuração, votação em cédula",
}

# Chaves de apuracao_2t_2026.secoes_ranking.REGRAS_EXPLICACAO, em português corrente.
EXPLICACAO_NOME = {
    "perto_19h": "a seção encerrou perto ou depois das 19h, o que é compatível com a extensão do horário",
    "tardia_fila": "a seção encerrou bem depois do 1º turno, antes das 18h55, o que sugere fila no fechamento",
    "agregada": "a seção recebe seções agregadas",
    "aptos_mudaram": "o número de eleitores aptos mudou mais de 10% entre os turnos",
    "contingencia": "houve urna de contingência ou mais de uma carga",
    "papel": "a votação foi em cédula e o boletim saiu do sistema de apuração",
    "pequena": "a seção é pequena, menos de 100 eleitores, e um voto move mais de um ponto",
    "salto_no_local": "outras seções do mesmo local tiveram o mesmo salto de biometria, o que aponta leitor ou rede",
    "zona_bio_baixa": "a zona já tinha biometria baixa no 1º turno",
    "secao_bio_baixa_1t": "a própria seção já tinha 10% ou mais sem digital no 1º turno",
    "comp1_baixo": "o comparecimento do 1º turno estava 10 pontos ou mais abaixo do município",
    "acompanha": "a alta acompanha a do município ou do estado",
}

FRASES: dict[str, str] = {
    # seção
    "pequena": "Esta seção tem menos de 30 eleitores aptos. Para proteger o voto secreto, os votos dela não aparecem aqui; veja o local de votação.",
    "sem_bu2": "O boletim desta seção no 2º turno ainda não entrou na nossa leitura. Os números do 2º turno aparecem quando a coleta chegar a ela.",
    "res2": "No 2º turno, esta seção deu {0} a Flávio e {1} a Lula, ou {2}% e {3}% dos votos válidos.",
    "res2_empate": "No 2º turno, esta seção empatou: {0} para cada candidato.",
    "res1": "No 1º turno, a seção deu {0} a Flávio, {1} a Lula e {2} às demais candidaturas.",
    "vs1_subiu": "Entre os dois, Flávio tinha {0}% no 1º turno e ficou com {1}% no 2º: alta de {2} pontos.",
    "vs1_caiu": "Entre os dois, Flávio tinha {0}% no 1º turno e ficou com {1}% no 2º: queda de {2} pontos.",
    "vs1_igual": "Entre os dois, a fatia de Flávio ficou praticamente igual: {0}% no 1º turno e {1}% no 2º.",
    "comp_subiu": "O comparecimento subiu de {0}% para {1}% dos aptos, {2} pontos a mais.",
    "comp_caiu": "O comparecimento caiu de {0}% para {1}% dos aptos, {2} pontos a menos.",
    "comp_igual": "O comparecimento ficou praticamente igual: {0}% no 1º turno e {1}% no 2º.",
    "bn": "Brancos e nulos foram {0}% de quem votou no 1º turno e {1}% no 2º.",
    "bio": "Sem digital cadastrada: {0}% de quem votou no 1º turno e {1}% no 2º. Liberados pelo ano de nascimento, quando a digital não confere: {2}% e {3}%.",
    "hora": "O último voto foi às {0} no 2º turno e às {1} no 1º, horário de Brasília.",
    "hora_local": "O último voto foi às {0} no 2º turno e às {1} no 1º, na hora local da cidade.",
    "rec": "O boletim do 2º turno chegou ao TSE às {0}, horário de Brasília.",
    "urna_mesma": SITUACOES["mesma"],
    "urna_mesma_recarga": SITUACOES["mesma_recarga"],
    "urna_reserva": SITUACOES["reserva"]
    + " É a troca prevista quando a urna da seção falha.",
    "urna_nova": SITUACOES["nova"],
    "urna_outra_secao_zona": SITUACOES["outra_secao_zona"]
    + " Remanejar urnas entre seções é logística comum; confira a ata.",
    "urna_outra_secao_municipio": SITUACOES["outra_secao_municipio"]
    + " Remanejar urnas é logística comum; confira a ata.",
    "urna_outro_municipio": SITUACOES["outro_municipio"]
    + " Remanejar urnas é logística comum; confira a ata.",
    "urna_sem_1t": SITUACOES["sem_1t"],
    "sinais_0": "Nenhum dos seis sinais da régua da casa acendeu nesta seção no 2º turno.",
    "sinais_1": "Um sinal da régua da casa acendeu nesta seção: {0}. " + ROTULO,
    "sinais_n": "{0} sinais da régua da casa acenderam nesta seção: {1}. " + ROTULO,
    "explica": "Explicação provável pela regra: {0}.",
    "sem_explicacao": "Nenhuma explicação provável pela regra; vale conferir a ata da seção e o log da urna.",
    "contingencia": "O boletim registra urna de contingência ou mais de uma carga, o que costuma acompanhar uma troca de urna no dia.",
    "agreg_mudou": "As seções agregadas a esta mudaram entre os turnos; a comparação entre 1º e 2º turno é aproximada.",
    "mud_real": "O local de votação desta seção mudou entre os turnos: {0}. Distância em linha reta: {1}.",
    "mud_real_sem_dist": "O local de votação desta seção mudou entre os turnos: {0}.",
    "mud_outra": "O cadastro registra alteração no local desta seção entre os turnos: {0}.",
    "log1_0": "No log da urna do 1º turno, só registros de rotina.",
    "log1_n": "No log da urna do 1º turno: {0}.",
    "log2_0": "No log da urna do 2º turno, só registros de rotina.",
    "log2_0_antes": "No log da urna do 2º turno, só registros de rotina; no 1º turno, o log estava em {0}.",
    "log_subiu": "O nível de atenção do log subiu de {0} no 1º turno para {1} no 2º: {2}. "
    + ROTULO,
    "log_igual": "No log da urna do 2º turno: {0}. O mesmo sinal já aparecia no 1º turno.",
    "log_igual_outro": "No log da urna do 2º turno: {0}. O 1º turno tinha o mesmo nível de atenção, com outro tipo de sinal.",
    "log2_n": "No log da urna do 2º turno: {0}. No 1º turno, o log estava em {1}.",
    "log2_n_sem1": "No log da urna do 2º turno: {0}.",
    "log_reinicio_1": "A urna ligou de novo durante a votação às {0}, com {1} já computados; depois vieram mais {2}. A contagem continua da memória da urna.",
    "log_reinicio_n": "A urna ligou de novo {0} vezes durante a votação; a primeira às {1}, com {2} já computados.",
    "log_bat_simultanea": "Durante a votação, a urna passou para a bateria junto com outras urnas do município, sinal de falta de energia no prédio ou na rede.",
    "log_bat_isolada": "Durante a votação, a urna passou para a bateria sozinha, sem outras urnas do município no mesmo minuto.",
    "log_bat_votacao": "Durante a votação, a urna passou para a bateria.",
    "log_mr": "O aviso de problema ao desmontar a memória de resultado antes da zerésima aparece quando a urna é religada com a mesma carga de setembro; é rotina e não conta como erro técnico.",
    "fiscal1": "Antes do 2º turno, a régua de fiscalização da casa pôs esta seção em {0}.",
    # prédio
    "p_cobertura": "No 2º turno, {0} de {1} seções deste local já têm boletim lido; as contas do 2º turno valem para elas.",
    "p_sem_bu2": "Nenhuma seção deste local tem boletim do 2º turno lido até agora.",
    "p_res2": "Somando as seções com boletim, o local deu {0}% dos válidos a Flávio e {1}% a Lula no 2º turno.",
    "p_var_subiu": "Nas mesmas seções, a fatia de Flávio entre os dois foi de {0}% para {1}%: alta de {2} pontos. No município, a variação foi de {3} pontos.",
    "p_var_caiu": "Nas mesmas seções, a fatia de Flávio entre os dois foi de {0}% para {1}%: queda de {2} pontos. No município, a variação foi de {3} pontos.",
    "p_var_igual": "Nas mesmas seções, a fatia de Flávio entre os dois ficou praticamente igual: {0}% e {1}%. No município, a variação foi de {3} pontos.",
    "p_comp": "Comparecimento do local no 2º turno: {0}% dos aptos, contra {1}% no município; nas mesmas seções, {2} em relação ao 1º turno.",
    "p_sinais_0": "Nenhuma seção deste local acendeu sinal da régua da casa.",
    "p_sinais_n": "{0} de {1} seções deste local acenderam ao menos um sinal; o maior escore é {2} de 6. "
    + ROTULO,
    "p_mud": "{0} deste local mudaram de endereço entre os turnos.",
    "p_log_subiu": "No log do 2º turno, {0} deste local subiram para atenção 2 ou 3, vindas de 0 ou 1 no 1º turno.",
    "p_log_persiste": "{0} deste local têm atenção 2 ou 3 no log dos dois turnos.",
    "p_log_reinicio": "{0} deste local tiveram a urna religada durante a votação no 2º turno.",
    "p_log_bateria": "{0} deste local passaram para a bateria durante a votação no 2º turno.",
}


# ------------------------------------------------------------------ formatação pt-BR


def f1(v: float) -> str:
    return f"{v:.1f}".replace(".", ",")


def inteiro(v: int) -> str:
    return f"{int(v):,}".replace(",", ".")


def votos(v: int) -> str:
    return f"{inteiro(v)} voto" if int(v) == 1 else f"{inteiro(v)} votos"


def secoes(v: int) -> str:
    return f"{inteiro(v)} seção" if int(v) == 1 else f"{inteiro(v)} seções"


def distancia(m: float) -> str:
    if m < 950:
        return f"{max(50, round(m / 50) * 50)} m"
    return f"{f1(m / 1000)} km"


def pontos(d: float) -> str:
    """Variação com sinal, em pontos: ``+2,1``, ``-0,4``, ``0,0``."""
    r = round(d, 1)
    if r == 0:
        return "0,0"
    return ("+" if r > 0 else "-") + f1(abs(r))


def lista(itens: list[str]) -> str:
    if len(itens) <= 1:
        return "".join(itens)
    return ", ".join(itens[:-1]) + " e " + itens[-1]


def _ok(*vs: Any) -> bool:
    return all(v is not None for v in vs)


# ------------------------------------------------------------------ regras


def frases_secao(r: dict[str, Any], catalogo: dict[str, Any]) -> list[list[str]]:
    """Frases da seção. ``r`` tem as colunas da seção (contrato); ``catalogo`` traz os
    nomes curtos dos níveis de fiscalização e dos sinais do log."""
    out: list[list[str]] = []
    if r.get("pequena"):
        out.append(["pequena"])
    elif not r.get("bu2"):
        out.append(["sem_bu2"])
        if _ok(r.get("flavio1"), r.get("lula1"), r.get("terceira1")):
            out.append(
                ["res1", votos(r["flavio1"]), votos(r["lula1"]), votos(r["terceira1"])]
            )
    else:
        f2, l2 = r["flavio2"], r["lula2"]
        if f2 == l2:
            out.append(["res2_empate", votos(f2)])
        elif r.get("fatia_f2") is not None:
            out.append(
                [
                    "res2",
                    votos(f2),
                    votos(l2),
                    f1(r["fatia_f2"]),
                    f1(100 - r["fatia_f2"]),
                ]
            )
        if _ok(r.get("fatia_f1"), r.get("fatia_f2")):
            d = r["fatia_f2"] - r["fatia_f1"]
            cod = (
                "vs1_igual" if abs(d) < 0.5 else ("vs1_subiu" if d > 0 else "vs1_caiu")
            )
            out.append([cod, f1(r["fatia_f1"]), f1(r["fatia_f2"]), f1(abs(d))])
        if _ok(r.get("comp_pct1"), r.get("comp_pct2")):
            d = r["comp_pct2"] - r["comp_pct1"]
            cod = (
                "comp_igual" if abs(d) < 1 else ("comp_subiu" if d > 0 else "comp_caiu")
            )
            out.append([cod, f1(r["comp_pct1"]), f1(r["comp_pct2"]), f1(abs(d))])
        if _ok(r.get("bn_pct1"), r.get("bn_pct2")):
            out.append(["bn", f1(r["bn_pct1"]), f1(r["bn_pct2"])])
        if _ok(
            r.get("sem_bio_pct1"),
            r.get("sem_bio_pct2"),
            r.get("ano_nasc_pct1"),
            r.get("ano_nasc_pct2"),
        ):
            out.append(
                [
                    "bio",
                    f1(r["sem_bio_pct1"]),
                    f1(r["sem_bio_pct2"]),
                    f1(r["ano_nasc_pct1"]),
                    f1(r["ano_nasc_pct2"]),
                ]
            )
    if r.get("bu2") and _ok(r.get("enc2"), r.get("enc1")):
        cod = "hora_local" if r.get("uf") == "ZZ" else "hora"
        out.append([cod, hhmm(r["enc2"]) or "", hhmm(r["enc1"]) or ""])
    if r.get("bu2") and r.get("rec2") is not None:
        out.append(["rec", hhmm(r["rec2"]) or ""])
    sit = r.get("urna_situacao")
    if sit:
        out.append([f"urna_{sit}"])
    if r.get("bu2") and r.get("contingencia2") and sit != "reserva":
        out.append(["contingencia"])
    if r.get("bu2") and not r.get("pequena"):
        sinais = list(r.get("sinais") or [])
        if not sinais:
            out.append(["sinais_0"])
        else:
            nomes = lista([SINAIS_NOME[s] for s in sinais])
            if len(sinais) == 1:
                out.append(["sinais_1", nomes])
            else:
                out.append(["sinais_n", str(len(sinais)), nomes])
            exp = list(r.get("explicacoes") or [])
            if exp:
                out.append(["explica", lista([EXPLICACAO_NOME[e] for e in exp])])
            else:
                out.append(["sem_explicacao"])
    if r.get("agreg_igual") is False:
        out.append(["agreg_mudou"])
    mud = r.get("mudanca")
    if mud:
        nome_cat = catalogo["mudanca"].get(mud.get("cat"), {}).get("nome", "")
        nome_cat = nome_cat[:1].lower() + nome_cat[1:]
        if mud.get("real") and mud.get("dist_m") is not None:
            out.append(["mud_real", nome_cat, distancia(mud["dist_m"])])
        elif mud.get("real"):
            out.append(["mud_real_sem_dist", nome_cat])
        else:
            out.append(["mud_outra", nome_cat])
    out.extend(_frases_log(r, catalogo))
    if r.get("fiscal_nivel"):
        nome = catalogo["fiscal"].get(r["fiscal_nivel"], "")
        if nome:
            out.append(["fiscal1", nome[:1].lower() + nome[1:]])
    return out


def _nomes_log(cods: list[str], catalogo: dict[str, Any]) -> list[str]:
    out = []
    for c in cods:
        if c in catalogo["log"] and c not in catalogo["log_rotina"]:
            n = catalogo["log"][c]
            out.append(n[:1].lower() + n[1:])
    return out


def _frases_log(r: dict[str, Any], catalogo: dict[str, Any]) -> list[list[str]]:
    """Log do 2º turno ao lado do 1º (regra do coordenador de 26/10)."""
    a1, a2 = r.get("log1_atencao"), r.get("log2_atencao")
    niveis = catalogo.get("log_niveis", {})

    def nivel(a: int) -> str:
        n = niveis.get(a, str(a))
        return n[:1].lower() + n[1:]

    out: list[list[str]] = []
    if a2 is None:
        if a1 is not None:
            nomes = _nomes_log(r.get("log1_sinais") or [], catalogo)
            out.append(["log1_n", lista(nomes)] if a1 > 0 and nomes else ["log1_0"])
        return out
    nomes2 = _nomes_log(r.get("log2_sinais") or [], catalogo)
    if a2 == 0 or not nomes2:
        if a1 is not None and a1 >= 2:
            out.append(["log2_0_antes", nivel(a1)])
        else:
            out.append(["log2_0"])
    elif a1 is not None and a1 <= 1 and a2 >= 2:
        out.append(["log_subiu", nivel(a1), nivel(a2), lista(nomes2)])
    elif a1 is not None and a1 == a2:
        f1 = set(r.get("log1_familias") or [])
        f2 = set(r.get("log2_familias") or [])
        out.append(["log_igual" if f1 & f2 else "log_igual_outro", lista(nomes2)])
    elif a1 is not None:
        out.append(["log2_n", lista(nomes2), nivel(a1)])
    else:
        out.append(["log2_n_sem1", lista(nomes2)])
    rein = r.get("log2_reinicios") or []
    if len(rein) == 1 and rein[0][0] is not None and rein[0][1] is not None:
        m, antes, depois = rein[0]
        out.append(["log_reinicio_1", hhmm(m) or "", votos(antes), votos(depois or 0)])
    elif len(rein) > 1 and rein[0][0] is not None and rein[0][1] is not None:
        out.append(
            [
                "log_reinicio_n",
                str(len(rein)),
                hhmm(rein[0][0]) or "",
                votos(rein[0][1]),
            ]
        )
    if r.get("log2_bateria"):
        out.append([f"log_bat_{r['log2_bateria']}"])
    if (r.get("log2_erro_mr") or 0) > 0:
        out.append(["log_mr"])
    return out


def frases_local(p: dict[str, Any], mun: dict[str, Any]) -> list[list[str]]:
    """Frases do prédio, com o município ao lado (``mun`` são os totais do município)."""
    out: list[list[str]] = []
    n, nbu = p["n_secoes"], p["n_bu2"]
    if nbu == 0:
        out.append(["p_sem_bu2"])
        return out
    if nbu < n:
        out.append(["p_cobertura", inteiro(nbu), inteiro(n)])
    if p.get("fatia_f2") is not None:
        out.append(["p_res2", f1(p["fatia_f2"]), f1(100 - p["fatia_f2"])])
    if _ok(p.get("fatia_f1_par"), p.get("fatia_f2"), mun.get("d_fatia_pp")):
        d = p["fatia_f2"] - p["fatia_f1_par"]
        cod = (
            "p_var_igual"
            if abs(d) < 0.5
            else ("p_var_subiu" if d > 0 else "p_var_caiu")
        )
        out.append(
            [
                cod,
                f1(p["fatia_f1_par"]),
                f1(p["fatia_f2"]),
                f1(abs(d)),
                pontos(mun["d_fatia_pp"]),
            ]
        )
    if _ok(p.get("comp_pct2"), mun.get("comp_pct2"), p.get("d_comp_pp")):
        out.append(
            [
                "p_comp",
                f1(p["comp_pct2"]),
                f1(mun["comp_pct2"]),
                pontos(p["d_comp_pp"]) + " pontos",
            ]
        )
    if p.get("secoes_sinal", 0) == 0:
        out.append(["p_sinais_0"])
    else:
        out.append(
            [
                "p_sinais_n",
                inteiro(p["secoes_sinal"]),
                inteiro(nbu),
                str(p["escore_max"]),
            ]
        )
    if p.get("secoes_mudaram"):
        out.append(["p_mud", secoes(p["secoes_mudaram"])])
    for k in (
        "secoes_log_subiu",
        "secoes_log_persiste",
        "secoes_log_reinicio",
        "secoes_log_bateria",
    ):
        if p.get(k):
            out.append(["p_" + k.removeprefix("secoes_"), secoes(p[k])])
    return out


def render(frases: list[list[str]]) -> str:
    """Mesmo algoritmo do aplicativo: troca ``{i}`` pelo argumento ``i``."""
    partes = []
    for cod, *args in frases:
        t = FRASES[cod]
        for i, a in enumerate(args):
            t = t.replace("{" + str(i) + "}", a)
        partes.append(t)
    return " ".join(partes)
