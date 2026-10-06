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
    nota,
    num,
    p,
)
from .pagina_texto import fig, lista
from .pagina_texto_senado_flavio import em_uf

NOITE = "noite_regioes.json"
REGIOES_CINCO = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
LENTIDAO = "lentidao_ufs.json"
MIN_LOTE = 10_000
EXT = {2: "duas", 3: "três", 4: "quatro", 5: "cinco", 6: "seis", 7: "sete"}


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
    h = "<h3>A noite por região</h3>" + fig("noite_regioes_lotes", d) + _chegada(N)
    h += fig("noite_regioes_diferenca", d) + _saldo(N)
    h += fig("noite_pesos_regioes", d) + _decomposicao(N)
    return h


def _chegada(N: dict) -> str:
    m = N["marcos"]
    ne = N["nordeste"]
    falta = ne["maior_do_que_faltava"]
    lac = N["lacuna_da_soma"]
    na_pausa = ne["o_que_faltava"].get(lac["de_brt"][:16])
    ordem = sorted(REGIOES_CINCO, key=lambda r: m[r]["90"])
    meio = lista([f"{r} {hora(m[r]['90'])}" for r in ordem[1:-1]])
    frase = (
        f"O {ordem[0]} passou de 90% das seções às {hora(m[ordem[0]]['90'])} e o {ordem[-1]}, por último, às "
        f"{hora(m[ordem[-1]]['90'])} ({meio}). Às {hora(falta['hora_brt'])} o Nordeste já era "
        f"{num(falta['parcela_nordeste_pct'], 1)}% dos {_validos(falta['faltavam_validos'])} que faltavam"
    )
    if na_pausa:
        frase += (
            f"; às {hora(lac['de_brt'])}, quando os arquivos de UF pararam, "
            f"{num(na_pausa['parcela_pct']['Nordeste'], 1)}%"
        )
    frase += "."
    lts = N["lotes_5min"]
    cedo = _faixa(lts, "17:30", "18:30")
    tarde = _faixa(lts, "21:00", "23:00")
    if cedo and tarde:
        frase += (
            f" A parcela de Lula nos lotes subiu junto: de {num(cedo[0], 1)}% a {num(cedo[1], 1)}% entre 17:30 e "
            f"18:30, de {num(tarde[0], 1)}% a {num(tarde[1], 1)}% entre 21h e 23h."
        )
    d99 = N["depois_dos_99"]
    frase += (
        f" Depois dos 99% das seções, às {hora(d99['desde_brt'])}, entraram {inteiro(d99['st'])} seções e "
        f"{_validos(d99['vv'])}, Lula {num(d99['pct_lula'], 2)}%."
    )
    return p(frase, "verificado")


def _saldo(N: dict) -> str:
    lid = N["lideranca"]
    vp, mv = lid["maior_vantagem_pp"], lid["maior_vantagem_votos"]
    vv = sum(x["validos"] for x in N["totais"].values())
    final_pp = 100 * lid["final"]["votos"] / vv
    virada = (
        "Lula não esteve à frente em nenhum minuto."
        if not lid["virada"]
        else f"Lula esteve à frente em {lid['minutos_com_lula_a_frente']} minutos."
    )
    return p(
        f"{virada} A vantagem de Flávio chegou a {_pontos(vp['pp'])} dos válidos apurados às {hora(vp['hora_brt'])}, "
        f"com {num(vp['pst'], 1)}% das seções, e a {milhoes(mv['votos'])} de votos às {hora(mv['hora_brt'])}; terminou "
        f"em {_pontos(final_pp)} e {_votos(lid['final']['votos'])}.",
        "verificado",
    )


def _decomposicao(N: dict) -> str:
    dec = N["decomposicao"]
    pico = dec["pico_brt"][:16]
    sudeste = {
        x["hora_brt"]: x for x in _linhas(N["minutos"]) if x["regiao"] == "Sudeste"
    }
    se_pico, se_fim = sudeste[pico], list(sudeste.values())[-1]
    c = N["contribuicao_final"]["regioes"]

    def margem(x: dict) -> float:
        return 100 * (x["flavio"] - x["lula"]) / x["vv"]

    return p(
        f"A queda vem sobretudo da ordem de chegada. Com cada região no peso final, a vantagem das {hora(pico)} seria "
        f"{_pontos(dec['pico_peso_final_pp'])}, não {_pontos(dec['pico_pp'])}: {_pontos(dec['entre_regioes_pp'])} "
        f"({num(dec['entre_regioes_pct_da_queda'], 1)}%) da queda são a mistura da hora, e os outros "
        f"{_pontos(dec['dentro_das_regioes_pp'])}, a ordem dentro de cada região (no Sudeste, de "
        f"{_pontos(margem(se_pico), 1)} às {hora(pico)} para {_pontos(margem(se_fim), 1)} no fim). O Nordeste deu "
        f"{num(c['Nordeste']['pct_lula'], 2)}% dos válidos a Lula e fechou por último; o Sul deu "
        f"{num(c['Sul']['pct_flavio'], 2)}% a Flávio e fechou primeiro. Placar parcial sem a lista do que falta mede a "
        "ordem de chegada antes de medir o eleitor.",
        "inferencia",
    )


def painel(d: Dados) -> str:
    """O que o painel do TSE mostrava: degraus, não movimento de voto (capítulo 3)."""
    N = d.get(NOITE)
    if not N:
        return ""
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
        f"Quem olhava o painel viu a vantagem encolher em degraus. A versão das {hora(a['gerado_brt'], True)} mostrava "
        f"{num(a['pst'], 2)}% das seções e Flávio {_pontos(dif(a))} à frente, retrato da soma das UFs das "
        f"{hora(a['soma_ufs_alcancou_brt'])}, e ficou até {hora(b['gerado_brt'])}, quando as UFs já tinham "
        f"{inteiro(a['soma_ufs_a_frente_antes_da_proxima'])} seções a mais. A das {hora(b['gerado_brt'], True)} trouxe o "
        f"retrato das {hora(b['soma_ufs_alcancou_brt'])} ({num(b['pst'], 2)}%, {_pontos(dif(b))}) e ficou até "
        f"{hora(depois['gerado_brt'], True)}, já com {num(b['idade_do_retrato_antes_da_proxima_min'], 1)} minutos e "
        f"{inteiro(b['soma_ufs_a_frente_antes_da_proxima'])} seções de atraso. A seguinte mostrou {num(depois['pst'], 2)}% "
        f"e {_pontos(dif(depois))}. O painel parou; o voto não mudou.",
        "verificado",
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
            "ufs",
        ],
    )
    if faltam:
        return "<h3>Os estados lentos, em dois anos</h3>" + bloco_pendente(LENTIDAO)
    N = d.get(NOITE)
    h = "<h3>Os estados lentos, em dois anos</h3>" + fig("lentidao_ufs_2022_2026", d)
    h += _mais_rapida(T) + _cauda(T)
    h += fig("lentidao_marcos", d)
    h += _pausa(T) + _juizo_lentos(T, N)
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
    quantas = "todas as 27 UFs" if n_rap == 27 else f"{n_rap} das 27 UFs"
    c = res["classificacao"]
    f = res["fuso"]
    lentas = f["fora_entre_as_lentas_2026"]
    fuso = (
        f"só {_nomes(lentas)} está entre as lentas"
        if len(lentas) == 1
        else (
            f"{len(lentas)} estão entre as lentas"
            if lentas
            else "nenhuma está entre as lentas"
        )
    )
    return p(
        f"A apuração de 2026 foi mais rápida que a de 2022: o país passou de 50%, 90% e 99% das seções às {a['50']}, "
        f"{a['90']} e {a['99']} (em 2022, {b['50']}, {b['90']} e {b['99']}), e {quantas} chegaram aos 99% mais cedo. A "
        f"lentidão é dos mesmos estados: {len(c['lentas_nos_dois'])} UFs ficaram acima da mediana do 99% nos dois anos "
        f"({_nomes(c['lentas_nos_dois'])}), e a ordem tem correlação de postos de {num(res['spearman_ufs'], 2)}. Fuso não "
        f"explica: as {EXT.get(len(f['ufs_fora_de_brasilia']), len(f['ufs_fora_de_brasilia']))} UFs fora da hora de Brasília chegaram aos 99% em mediana às {_hm(f['mediana_2026_fora'])}, "
        f"antes das demais ({_hm(f['mediana_2026_brasilia'])}), e {fuso}.",
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
    est = T["estrutural"]
    cauda = [
        f"{num(u['cauda_min']['2026'], 0)}{' minutos' if i == 0 else ''} {em_uf(u['uf'])}"
        for i, u in enumerate(longas)
    ]
    madrugada = all("(+" in m["hora"] for m, _ in ultimos)
    fim = [
        f"{nome_proprio(m['nome'])} ({uf}) às {m['hora'].split(' ')[0] if madrugada else dia(m['hora'])}"
        for m, uf in ultimos
    ]
    texto = (
        "Do 99% ao 100% das seções passaram "
        + lista(cauda)
        + (
            ". Fecharam por último, na madrugada de 05/10, "
            if madrugada
            else ". Fecharam por último "
        )
        + lista(fim)
        + f". A ordem dos municípios se repete entre os anos, com correlação de postos de "
        f"{num(est['spearman_nacional'], 2)} em {inteiro(est['municipios_comparados'])} municípios."
    )
    return p(texto, "verificado") + p(
        "A demora final é do lugar, não do dia.", "inferencia"
    )


def _pausa(T: dict) -> str:
    at = T["recebido_x_totalizado_2022"]
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
        f"; {_nomes(atras90)}, as {EXT.get(len(atras90), len(atras90))} UFs que chegaram aos 90% mais tarde que em 2022, cruzaram a marca "
        "depois da pausa"
        if atras90 and todas_depois
        else ""
    )
    frase99 = (
        f"{_nomes(apos99)} cruzaram 99% dos boletins recebidos nos três minutos depois que o carimbo voltou"
        if apos99
        else "nenhuma UF cruzou 99% dos boletins recebidos logo depois da pausa"
    )
    return p(
        f"Em 2022, recebido e totalizado quase coincidem: a primeira totalização veio, em mediana, "
        f"{num(at['mediana_s'], 0)} segundos depois do recebimento, e {num(at['ate_60s_pct'], 1)}% em até um minuto. Na "
        f"pausa de 2026, nenhum boletim das {len(rec['ufs'])} UFs tem carimbo de recebimento de {l26['de_hora']} a "
        f"{l26['ate_hora']} ({num(l26['minutos'], 1)} minutos), contra no máximo {num(l22['minutos'] * 60, 0)} segundos "
        f"em 2022 no mesmo relógio, e os arquivos de UF ficam sem versão nova de {ger['de']} a {ger['ate']}. O tempo é do "
        f"tribunal, não dos estados: {frase99}{frase90}.",
        "verificado",
    )


def _min_de(hms: str) -> float:
    h, m, s = (int(x) for x in hms.split(":"))
    return h * 60 + m + s / 60 - 17 * 60


def _juizo_lentos(T: dict, N: dict | None) -> str:
    n = T["nacional"]
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
    return nota(
        "juizo",
        f"Quem segura a totalização é previsível: {_nomes(ultimas)} fecharam por último, e o último 1% das seções do "
        f"país levou {_duracao(cauda)}{frase_votos}. Mostrar ao lado do placar quantas seções faltam em cada UF tiraria "
        "da madrugada a impressão de que o resultado mudou.",
    )
