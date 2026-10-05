"""Texto de dois blocos do dossiê: a noite por região (cap. 2) e os estados lentos (cap. 3).

Regra da casa: nenhum número digitado. Tudo sai de `noite_regioes.json` e de
`lentidao_ufs.json`; o que é inferência ou juízo editorial leva o selo na frase.
Sem o JSON, o bloco vira "em preparação" e o capítulo continua de pé.
"""

from __future__ import annotations

from .pagina_comum import (
    NOME_UF,
    Dados,
    bloco_pendente,
    checar,
    hora,
    inteiro,
    milhoes,
    nome_proprio,
    num,
    p,
)
from .pagina_texto import fig, lista

NOITE = "noite_regioes.json"
REGIOES_CINCO = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
LENTIDAO = "lentidao_ufs.json"
MIN_LOTE = 10_000


def _pontos(x: float, casas: int = 2) -> str:
    return f"{num(x, casas)} {'ponto' if abs(round(x, casas)) < 2 else 'pontos'}"


def _votos(x: float) -> str:
    """'2,22 milhões de votos' ou '660 mil votos' (sem 'de' depois de 'mil')."""
    return f"{milhoes(abs(x))}{' de' if abs(x) >= 1e6 else ''} votos"


def _validos(x: float) -> str:
    return f"{milhoes(abs(x))}{' de' if abs(x) >= 1e6 else ''} válidos"


def _sinal_mi(x: float) -> str:
    return ("+" if x > 0 else "−") + num(abs(x) / 1e6, 2)


def _linhas(bloco: dict) -> list[dict]:
    return [dict(zip(bloco["colunas"], r, strict=True)) for r in bloco["linhas"]]


def _faixa(lotes: list[dict], de: str, ate: str) -> tuple[float, float] | None:
    xs = [
        x["pct_lula"]
        for x in lotes
        if de <= x["de_brt"][11:16] < ate and x["vv"] >= MIN_LOTE and x["pct_lula"]
    ]
    return (min(xs), max(xs)) if xs else None


def dia(hora_lentidao: str | None, ano: int = 2026) -> str:
    """'02:59 (+1)' vira '02:59 de 05/10' (2026) ou '03/10' (2022)."""
    if not hora_lentidao:
        return "s/d"
    base, _, resto = hora_lentidao.partition(" (+")
    if not resto:
        return base
    dias = int(resto.rstrip(")"))
    dia_ = (4 if ano == 2026 else 2) + dias
    return f"{base} de {dia_:02d}/10"


def _duracao(minutos: float) -> str:
    h, m = divmod(round(minutos), 60)
    return f"{h} horas e {m} minutos" if h else f"{m} minutos"


# ------------------------------------------------------------------ capítulo 2


def noite_por_regiao(d: Dados) -> str:
    N = d.get(NOITE)
    if N is None:
        return "<h3>A noite por região</h3>" + bloco_pendente(NOITE)
    faltam = checar(
        d,
        NOITE,
        [
            "marcos",
            "nordeste.maior_do_que_faltava",
            "lideranca",
            "decomposicao",
            "contribuicao_final",
            "painel_nacional",
            "lotes_5min",
            "minutos",
            "depois_dos_99",
        ],
    )
    if faltam:
        return "<h3>A noite por região</h3>" + bloco_pendente(NOITE)
    h = "<h3>A noite por região</h3>" + fig("noite_regioes_lotes", d)
    h += _chegada(N) + _lotes(N)
    h += fig("noite_regioes_diferenca", d)
    h += _saldo(N) + _decomposicao(N) + _painel(N) + _leitura(N)
    return h


def _chegada(N: dict) -> str:
    m = N["marcos"]
    ne = N["nordeste"]
    falta = ne["maior_do_que_faltava"]
    lac = N["lacuna_da_soma"]
    na_pausa = ne["o_que_faltava"].get(lac["de_brt"][:16])
    frase_pausa = (
        f" Às {hora(lac['de_brt'])}, quando os arquivos de UF pararam, era "
        f"{num(na_pausa['parcela_pct']['Nordeste'], 1)}%."
        if na_pausa
        else ""
    )
    ordem = sorted(REGIOES_CINCO, key=lambda r: m[r]["90"])
    passos = [f"o {ordem[0]} passou de 90% das seções às {hora(m[ordem[0]]['90'])}"]
    passos += [f"o {r} às {hora(m[r]['90'])}" for r in ordem[1:-1]]
    ultimo = f"o {ordem[-1]}, por último, às {hora(m[ordem[-1]]['90'])}"
    frase = lista([*passos, ultimo])
    return p(
        f"{frase[0].upper()}{frase[1:]}. Às "
        f"{hora(falta['hora_brt'])} o Nordeste já era a maior parte do que faltava apurar: "
        f"{num(falta['parcela_nordeste_pct'], 1)}% dos {_validos(falta['faltavam_validos'])} ainda fora da conta."
        + frase_pausa,
        "verificado",
    )


def _lotes(N: dict) -> str:
    lts = N["lotes_5min"]
    cedo = _faixa(lts, "17:30", "18:30")
    tarde = _faixa(lts, "21:00", "23:00")
    desde = N["nordeste"]["maior_regiao_do_lote_desde"]
    d99 = N["depois_dos_99"]
    partes = []
    if cedo and tarde:
        partes.append(
            f"A parcela de Lula dentro de cada lote subiu junto. Entre 17:30 e 18:30 ficou entre "
            f"{num(cedo[0], 1)}% e {num(cedo[1], 1)}%; entre 21h e 23h, entre {num(tarde[0], 1)}% e "
            f"{num(tarde[1], 1)}%."
        )
    if desde:
        partes.append(
            f"A partir das {hora(desde['de_brt'])}, o Nordeste foi a maior região de todo lote com pelo menos "
            f"{num(MIN_LOTE / 1000, 0)} mil válidos."
        )
    partes.append(
        f"Depois que o país passou de 99% das seções, às {hora(d99['desde_brt'])}, entraram "
        f"{inteiro(d99['st'])} seções e {_validos(d99['vv'])}, com Lula em {num(d99['pct_lula'], 2)}%."
    )
    return p(" ".join(partes), "verificado")


def _saldo(N: dict) -> str:
    lid = N["lideranca"]
    vp, mv = lid["maior_vantagem_pp"], lid["maior_vantagem_votos"]
    c = N["contribuicao_final"]["regioes"]
    vv = sum(x["validos"] for x in N["totais"].values())
    final_pp = 100 * lid["final"]["votos"] / vv
    virada = (
        "Lula não esteve à frente em nenhum minuto: não houve virada."
        if not lid["virada"]
        else f"Lula esteve à frente em {lid['minutos_com_lula_a_frente']} minutos."
    )
    return p(
        f"{virada} A vantagem de Flávio, em pontos dos válidos já apurados, chegou a {_pontos(vp['pp'])} às "
        f"{hora(vp['hora_brt'])}, com {num(vp['pst'], 1)}% das seções; em votos, a {milhoes(mv['votos'])}, às "
        f"{hora(mv['hora_brt'])}. Terminou em {_pontos(final_pp)} e {_votos(lid['final']['votos'])}. "
        f"No saldo, o Nordeste tirou {_votos(c['Nordeste']['votos'])} de Flávio; Sudeste "
        f"({_sinal_mi(c['Sudeste']['votos'])} milhões), Sul ({_sinal_mi(c['Sul']['votos'])}), Centro-Oeste "
        f"({_sinal_mi(c['Centro-Oeste']['votos'])}) e Norte ({_sinal_mi(c['Norte']['votos'])}) somaram a favor dele.",
        "verificado",
    )


def _pesos(N: dict, hora_: str, regioes: list[str]) -> str:
    comp = N["composicao_apurada"][hora_]
    return lista(
        [
            f"o {r}, com {num(comp[r]['apurado_pct'], 1)}% ({num(comp[r]['final_pct'], 1)}% no fim)"
            for r in regioes
        ]
    )


def _decomposicao(N: dict) -> str:
    dec = N["decomposicao"]
    pico = dec["pico_brt"][:16]
    comp = N["composicao_apurada"][pico]
    acima = [r for r in REGIOES_CINCO if comp[r]["apurado_pct"] > comp[r]["final_pct"]]
    abaixo = [r for r in REGIOES_CINCO if r not in acima]
    tarde = N["composicao_apurada"].get(N["lacuna_da_soma"]["de_brt"][:16])
    frase_tarde = ""
    if tarde:
        atras = [
            r
            for r in REGIOES_CINCO
            if tarde[r]["final_pct"] - tarde[r]["apurado_pct"] >= 2
        ]
        if atras:
            verbo = "seguia" if len(atras) == 1 else "seguiam"
            frase_tarde = (
                f" Às {hora(N['lacuna_da_soma']['de_brt'])}, só "
                + _pesos(N, N["lacuna_da_soma"]["de_brt"][:16], atras)
                + f", {verbo} bem abaixo do próprio peso."
            )
    sudeste = {
        x["hora_brt"]: x for x in _linhas(N["minutos"]) if x["regiao"] == "Sudeste"
    }
    se_pico, se_fim = sudeste[pico], list(sudeste.values())[-1]

    def margem(x: dict) -> float:
        return 100 * (x["flavio"] - x["lula"]) / x["vv"]

    return p(
        f"A maior parte da queda vem da ordem das regiões. Com cada região no peso final dos válidos, a vantagem "
        f"das {hora(pico)} seria {_pontos(dec['pico_peso_final_pp'])}, não {_pontos(dec['pico_pp'])}: "
        f"{_pontos(dec['entre_regioes_pp'])} ({num(dec['entre_regioes_pct_da_queda'], 1)}%) da queda até o fim "
        f"são a mistura da hora: nos válidos já apurados, {_pesos(N, pico, acima)}, pesavam acima do próprio "
        f"tamanho; {_pesos(N, pico, abaixo)}, abaixo.{frase_tarde} Os outros "
        f"{_pontos(dec['dentro_das_regioes_pp'])} são a ordem dentro de "
        f"cada região: no Sudeste, a vantagem de Flávio entre as seções já apuradas foi de "
        f"{_pontos(margem(se_pico), 1)} às {hora(pico)} para {_pontos(margem(se_fim), 1)} no fim.",
        "inferencia",
    )


def _painel(N: dict) -> str:
    P = N["painel_nacional"]
    paradas = sorted(
        (x for x in P if (x.get("soma_ufs_a_frente_antes_da_proxima") or 0) > 0),
        key=lambda x: -x["soma_ufs_a_frente_antes_da_proxima"],
    )[:2]
    paradas.sort(key=lambda x: x["gerado_brt"])
    if len(paradas) < 2:
        return ""
    a, b = paradas
    depois = P[P.index(b) + 1]

    def dif(x: dict) -> float:
        return x["pct_flavio"] - x["pct_lula"]

    return p(
        f"Quem olhava o painel do TSE viu outra noite. Às {hora(a['gerado_brt'], True)} o arquivo nacional "
        f"mostrou {num(a['pst'], 2)}% das seções e Flávio {_pontos(dif(a))} à frente: era a soma das UFs das "
        f"{hora(a['soma_ufs_alcancou_brt'])}, e ficou na tela até {hora(b['gerado_brt'])}, quando as UFs já "
        f"tinham {inteiro(a['soma_ufs_a_frente_antes_da_proxima'])} seções a mais. A versão das "
        f"{hora(b['gerado_brt'], True)} trouxe o retrato das {hora(b['soma_ufs_alcancou_brt'])} "
        f"({num(b['pst'], 2)}%, {_pontos(dif(b))}) e ficou até {hora(depois['gerado_brt'], True)}; no último "
        f"segundo, o retrato tinha {num(b['idade_do_retrato_antes_da_proxima_min'], 1)} minutos e estava "
        f"{inteiro(b['soma_ufs_a_frente_antes_da_proxima'])} seções atrás. A versão seguinte já mostrou "
        f"{num(depois['pst'], 2)}% e {_pontos(dif(depois))}. A vantagem encolheu em degraus porque o painel "
        "parou, não porque o voto mudou.",
        "verificado",
    )


def _leitura(N: dict) -> str:
    c = N["contribuicao_final"]["regioes"]
    return p(
        "O efeito Nordeste é ordem de totalização, não movimento de eleitor. Nenhuma seção muda de voto "
        "depois de totalizada; o que muda é a mistura do que já entrou. O Nordeste deu "
        f"{num(c['Nordeste']['pct_lula'], 2)}% dos válidos a Lula e fechou por último; o Sul deu "
        f"{num(c['Sul']['pct_flavio'], 2)}% a Flávio e fechou primeiro. Placar parcial sem a lista do que falta, "
        "por região, mede a ordem de chegada antes de medir o eleitor.",
        "inferencia",
    )


# ------------------------------------------------------------------ capítulo 3


def estados_lentos(d: Dados) -> str:
    T = d.get(LENTIDAO)
    if T is None:
        return "<h3>Os estados lentos, em dois anos</h3>" + bloco_pendente(LENTIDAO)
    faltam = checar(
        d,
        LENTIDAO,
        [
            "nacional.horas_2026",
            "resumo_99.classificacao",
            "resumo_90",
            "estrutural",
            "recebido_x_totalizado_2022",
            "pausa.recebimento.lacuna_2026",
            "encerramento_local_2026",
            "ufs",
        ],
    )
    if faltam:
        return "<h3>Os estados lentos, em dois anos</h3>" + bloco_pendente(LENTIDAO)
    N = d.get(NOITE)
    h = "<h3>Os estados lentos, em dois anos</h3>" + fig("lentidao_ufs_2022_2026", d)
    h += _mais_rapida(T) + _estrutural(T) + _fuso(T) + _cauda(T)
    h += fig("lentidao_marcos", d)
    h += _reguas(T) + _pausa(T) + _juizo_lentos(T, N)
    return h


def _por_uf(T: dict) -> dict[str, dict]:
    return {u["uf"]: u for u in T["ufs"]}


def _nomes(siglas: list[str]) -> str:
    return lista([NOME_UF[s] for s in siglas])


def _mais_rapida(T: dict) -> str:
    n = T["nacional"]
    a, b = n["horas_2026"], n["horas_2022"]
    res = T["resumo_99"]
    n_rap = res["mais_rapidas_em_2026"]
    quantas = "Todas as 27 UFs" if n_rap == 27 else f"{n_rap} das 27 UFs"
    return p(
        f"A apuração de 2026 foi mais rápida que a de 2022. O país, sem o exterior, passou de 50% das seções "
        f"às {a['50']} (em 2022, às {b['50']}), de 90% às {a['90']} ({b['90']}) e de 99% às {a['99']} "
        f"({b['99']}). {quantas} chegaram aos 99% mais cedo. A régua de 2022 é a "
        "primeira totalização parcial de cada seção, carimbada pelo TSE nos dados abertos; a de 2026, a versão "
        "do arquivo de cada UF.",
        "verificado",
    )


def _estrutural(T: dict) -> str:
    res = T["resumo_99"]
    c = res["classificacao"]
    trocas = c["so_2022"] + c["so_2026"]
    return p(
        f"A lentidão é dos mesmos estados nos dois anos. {len(c['lentas_nos_dois'])} UFs ficaram acima da "
        f"mediana do 99% em 2022 e em 2026: {_nomes(c['lentas_nos_dois'])}. Outras "
        f"{len(c['rapidas_nos_dois'])} ficaram abaixo nas duas; só {_nomes(trocas)} trocaram de lado. A ordem "
        f"das UFs pelo 99% tem correlação de postos de {num(res['spearman_ufs'], 2)} entre os dois anos.",
        "verificado",
    )


def _fuso(T: dict) -> str:
    f = T["resumo_99"]["fuso"]
    enc = T["encerramento_local_2026"]
    por = _por_uf(T)
    cedo = {
        uf: enc[uf]["primeiro"][11:16]
        for uf in f["ufs_fora_de_brasilia"]
        if uf in enc and enc[uf].get("primeiro")
    }
    as15 = sorted(uf for uf, h in cedo.items() if h.startswith("15"))
    as16 = sorted(uf for uf, h in cedo.items() if h.startswith("16"))
    ac22 = por.get("AC", {}).get("primeira_secao", {}).get("2022_recebido")
    lentas = f["fora_entre_as_lentas_2026"]
    frase_ac = (
        f", e em 2022 o primeiro boletim do Acre chegou ao TSE às {_hm(ac22)} de Brasília"
        if ac22 is not None
        else ""
    )
    return p(
        "Fuso não explica. As urnas fecharam às 17h de Brasília em todo o país; o boletim de urna marca a hora "
        f"local, e o encerramento mais cedo é 15:00 nas urnas de {lista(as15)} e 16:00 nas de {lista(as16)}"
        f"{frase_ac}. As "
        f"seis UFs fora de Brasília chegaram aos 99% em mediana às {_hm(f['mediana_2026_fora'])}, antes das "
        f"demais ({_hm(f['mediana_2026_brasilia'])}). "
        + (
            f"Entre elas, só uma está entre as lentas: {_nomes(lentas)}."
            if len(lentas) == 1
            else (
                f"Entre elas, {len(lentas)} estão entre as lentas: {_nomes(lentas)}."
                if lentas
                else "Nenhuma delas está entre as lentas."
            )
        ),
        "verificado",
    )


def _hm(minutos: float) -> str:
    total = 17 * 60 + int(minutos)
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"


def _cauda(T: dict) -> str:
    ufs = [u for u in T["ufs"] if u["cauda_min"]["2026"] is not None]
    longas = sorted(ufs, key=lambda u: -u["cauda_min"]["2026"])[:3]
    ultimos = sorted(
        (
            (u["ultimos_municipios_2026"][0], u["uf"])
            for u in T["ufs"]
            if u["ultimos_municipios_2026"]
        ),
        key=lambda x: -x[0]["min"],
    )[:4]
    rep = [(u["uf"], n) for u in T["ufs"] for n in u["repetem_entre_os_5_ultimos"]]
    rep_longas = [
        f"{nome_proprio(n)} ({uf})" for uf, n in rep if uf in {x["uf"] for x in longas}
    ]
    est = T["estrutural"]
    texto = (
        "Do 99% ao 100% das seções passaram "
        + lista(
            [
                (
                    f"{num(u['cauda_min']['2026'], 0)} minutos ({u['uf']})"
                    if i == 0
                    else f"{num(u['cauda_min']['2026'], 0)} ({u['uf']})"
                )
                for i, u in enumerate(longas)
            ]
        )
        + ". As últimas a fechar: "
        + lista(
            [
                f"{nome_proprio(m['nome'])} ({uf}) às {dia(m['hora'])}"
                for m, uf in ultimos
            ]
        )
        + "."
    )
    if rep_longas:
        texto += (
            f" {lista(rep_longas)} já {'estava' if len(rep_longas) == 1 else 'estavam'} entre os cinco "
            "últimos municípios da UF em 2022."
        )
    texto += (
        f" No país, a ordem em que os municípios fecharam se repete com correlação de postos de "
        f"{num(est['spearman_nacional'], 2)} ({inteiro(est['municipios_comparados'])} municípios)."
    )
    inferencia = p(
        "Nas caudas mais longas, as últimas seções são de municípios do interior, e a ordem dos municípios "
        "se repete de uma eleição para a outra. A demora final é do lugar, não do dia.",
        "inferencia",
    )
    return p(texto, "verificado") + inferencia


def _reguas(T: dict) -> str:
    at = T["recebido_x_totalizado_2022"]
    comp = T["meta"]["coleta_secoes_2026"]["ufs_com_carimbo_completo"]
    return p(
        "Recebido não é totalizado. O recebimento é a chegada do boletim ao TSE; a totalização, a entrada dele "
        f"na conta. Em 2022 as duas réguas quase coincidem: a primeira totalização veio, em mediana, "
        f"{num(at['mediana_s'], 0)} segundos depois do recebimento, e {num(at['ate_60s_pct'], 1)}% em até um "
        f"minuto. Em 2026 o carimbo de recebimento só existe para as seções já coletadas uma a uma: "
        f"{len(comp)} UFs completas, onde ele acompanha o arquivo da UF; nas outras {27 - len(comp)} a coleta "
        "ainda não terminou.",
        "verificado",
    )


def _pausa(T: dict) -> str:
    rec = T["pausa"]["recebimento"]
    ger = T["pausa"]["geracao_uf"]
    l26, l22 = rec["lacuna_2026"], rec["lacuna_2022"]
    por = _por_uf(T)
    apos99 = [
        u["uf"]
        for u in T["ufs"]
        if "99" in u["marcos_logo_apos_pausa"]["2026_recebido"]
    ]
    atras90 = T["resumo_90"]["mais_lentas_em_2026"]
    fim_pausa = _min_de(ger["ate"])
    todas_depois = all(
        por[uf]["marcos"]["2026_totalizado"].get("90", 0) > fim_pausa for uf in atras90
    )
    frase90 = (
        f", e as {len(atras90)} UFs que chegaram aos 90% mais tarde que em 2022 ({_nomes(atras90)}) cruzaram a "
        "marca depois da pausa"
        if atras90 and todas_depois
        else ""
    )
    frase99 = (
        f"{_nomes(apos99)} cruzaram 99% dos boletins recebidos nos três minutos depois que o carimbo voltou"
        if apos99
        else "nenhuma UF cruzou 99% dos boletins recebidos logo depois da pausa"
    )
    return p(
        f"A pausa do TSE é outra coisa. Nessas {len(rec['ufs'])} UFs, nenhum boletim tem carimbo de recebimento "
        f"entre {l26['de_hora']} e {l26['ate_hora']}, {num(l26['minutos'], 1)} minutos; em 2022, no mesmo relógio "
        f"e nas mesmas UFs, a maior lacuna foi de {num(l22['minutos'] * 60, 0)} segundos. Os arquivos de UF ficaram "
        f"sem versão nova de {ger['de']} a {ger['ate']}. Esse tempo é do tribunal, não dos estados: "
        f"{frase99}{frase90}.",
        "verificado",
    )


def _min_de(hms: str) -> float:
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 60 + m + s / 60 - 17 * 60


def _juizo_lentos(T: dict, N: dict | None) -> str:
    n = T["nacional"]
    c = T["resumo_99"]["classificacao"]["lentas_nos_dois"]
    ultimas = [
        u["uf"]
        for u in sorted(
            T["ufs"], key=lambda u: -(u["marcos"]["2026_totalizado"].get("100") or 0)
        )[:4]
    ]
    cauda = n["2026_totalizado"]["100"] - n["2026_totalizado"]["99"]
    frase_votos = ""
    if N and N.get("depois_dos_99"):
        d99 = N["depois_dos_99"]
        frase_votos = (
            f" e trouxe {_validos(d99['vv'])}, {num(d99['pct_lula'], 1)}% de Lula"
        )
    return (
        '<aside class="juizo"><b>Juízo editorial</b>Quem segura a totalização é previsível: '
        f"{_nomes(ultimas)} fecharam por último em 2026, e {len(c)} UFs ficaram entre as lentas nos dois anos. "
        f"O último 1% das seções do país levou {_duracao(cauda)}{frase_votos}. Divulgar, ao lado do placar, "
        "quantas seções faltam em cada UF e onde elas ficam tiraria da madrugada a impressão de que o resultado "
        "mudou. A pausa das 19:32 é outra conta e pede relatório técnico próprio.</aside>"
    )
