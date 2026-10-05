"""Texto do fechamento: definições, fontes legais, limites, achados e memorando.

Toda frase com número sai do dicionário do JSON; nada é digitado à mão. Regras
da casa: sem travessão, nunca a palavra que acusa sem prova, verificado,
inferido, juízo editorial e hipótese separados. O primeiro achado é o que
contraria a leitura mais comum, quando os números o sustentam.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .fechamento_base import rotulo_duracao, rotulo_hora
from .secoes_base import num

PROIBIDO = "—"

AVISO = (
    "Seção que fecha tarde é seção que pede explicação, não indício de "
    "irregularidade. O boletim de urna mostra quando a votação terminou e quantos "
    "votaram; não mostra por quê. O que separa fila, identificação lenta e "
    "irregularidade é documento: a ata da mesa e o log da urna."
)

DEFINICOES = {
    "minutos": "minutos depois das 17h de Brasília do dia da eleição (04/10/2026 e 02/10/2022)",
    "encerramento": (
        "hora de término da votação gravada no boletim de urna de 2026 "
        "(dataHoraEncerramento, que a especificação do TSE descreve como término da "
        "aquisição do voto, o último voto), na hora local da urna, convertida para "
        "Brasília pelo fuso do município"
    ),
    "fuso": (
        "a votação abriu às 8h de Brasília no país inteiro; a hora local de abertura mais "
        "frequente no município dá o fuso (6h no Acre e no oeste do Amazonas, 7h em AM, RR, "
        "RO, MT e MS). Seção cujo boletim chegou ao TSE mais de 5 minutos antes do "
        "encerramento convertido fica sem hora de encerramento (relógio ou fuso "
        "inconsistente)"
    ),
    "recebimento": (
        "hora em que o boletim chegou ao TSE, já em hora de Brasília: campo dr/hr do "
        "aux.json em 2026 e DT_RECEBIMENTO_BU_HOR_TSE ('Hora TSE') em 2022. É a única régua "
        "dos dois anos e soma a fila da seção com o transporte da mídia até o ponto de "
        "transmissão"
    ),
    "tardia": "seção com encerramento às 18h de Brasília ou depois",
    "exterior": "fora das contas: vota na hora local da cidade",
}

FONTES_LEGAIS = [
    {
        "norma": "Res. TSE nº 23.751/2026 (atos gerais do processo eleitoral, Eleições 2026)",
        "dispositivo": "artigo não conferido",
        "conteudo": (
            "votação das 8h às 17h, horário de Brasília, em todo o país; no exterior, hora "
            "local"
        ),
        "como_conferido": (
            "pela citação na matéria do Poder360 de 04/10/2026 ('Eleições 2026: saiba até "
            "que horas você pode votar'); tse.jus.br devolveu 403 às ferramentas, por isso o "
            "número do artigo não foi conferido no texto da resolução"
        ),
    },
    {
        "norma": "Código Eleitoral (Lei nº 4.737/1965)",
        "dispositivo": "art. 153 e parágrafo único",
        "conteudo": (
            "às 17 horas o presidente da mesa entrega senhas a todos os eleitores "
            "presentes; a votação continua na ordem das senhas"
        ),
        "como_conferido": "texto do artigo em reprodução da lei (investidura.com.br)",
    },
    {
        "norma": "Código Eleitoral (Lei nº 4.737/1965)",
        "dispositivo": "art. 132",
        "conteudo": (
            "perante as mesas receptoras, candidatos, delegados e fiscais dos partidos "
            "podem fiscalizar a votação, formular protestos e fazer impugnações, inclusive "
            "sobre a identidade do eleitor"
        ),
        "como_conferido": "texto do artigo em resultado de busca (modeloinicial.com.br)",
    },
    {
        "norma": "Lei nº 9.504/1997",
        "dispositivo": "art. 65, caput e §§ 1º a 4º",
        "conteudo": (
            "fiscal maior de 18 anos e fora da mesa; um fiscal pode fiscalizar mais de uma "
            "seção no mesmo local de votação (§ 1º); credenciais expedidas pelos partidos ou "
            "coligações (§ 2º); no máximo 2 fiscais de cada partido ou coligação por seção "
            "(§ 4º)"
        ),
        "como_conferido": "texto do artigo em reprodução da lei (modeloinicial.com.br)",
    },
    {
        "norma": "Lei nº 9.504/1997",
        "dispositivo": "arts. 66 e 68, § 1º",
        "conteudo": (
            "partidos e coligações podem fiscalizar todas as fases da votação e da "
            "apuração (art. 66); o presidente da mesa entrega cópia do boletim de urna ao "
            "partido que a pedir até uma hora depois da expedição (art. 68, § 1º)"
        ),
        "como_conferido": "texto em reprodução da lei (pdba.georgetown.edu)",
    },
    {
        "norma": "Lei nº 9.504/1997",
        "dispositivo": "art. 39, § 5º, II, e art. 41-A",
        "conteudo": (
            "arregimentação de eleitor e propaganda de boca de urna no dia da eleição são "
            "crime (art. 39, § 5º, II); captação ilícita de sufrágio, a compra de voto, "
            "sujeita a multa e cassação do registro ou do diploma (art. 41-A)"
        ),
        "como_conferido": "resultado de busca com o texto dos dispositivos",
    },
]

LIMITES = [
    "A coleta dos boletins de 2026 ainda está em andamento; as contas que comparam anos usam só as UFs completas, e os números mudam na rodada final.",
    "Encerramento existe só em 2026: o arquivo de 2022 não traz a hora do último voto. A comparação entre anos usa a hora de recebimento no TSE, que soma fila e transporte da mídia.",
    "A hora de encerramento depende do relógio da urna e do fuso inferido pelo município; seções com recebimento antes do encerramento convertido ficam fora das contas de encerramento.",
    "Tipo de local é inferência por palavra-chave, não cadastro oficial; em 2022 não há bairro no arquivo do TSE.",
    "Idade do eleitor por seção não está no acervo para o país (só o Acre); a parte da fila que vem de eleitor idoso não é separável aqui.",
    "Correlação dentro da zona não identifica mecanismo: fila, identificação lenta e irregularidade deixam o mesmo rastro no boletim. Só a ata da mesa e o log da urna, que registra cada habilitação com hora, separam as três.",
    "O log da urna de cada seção está publicado pelo TSE; o acervo da coleta guarda só o nome, o tamanho e o SHA-256 dele, não o arquivo.",
    "A hora de recebimento de 2026 atravessa a pausa geral do TSE: boletins que chegaram durante a pausa ficaram registrados no fim dela, e nesse trecho a hora mede o tribunal, não a seção.",
]


def _p(x: float | None, casas: int = 1) -> str:
    return "n/d" if x is None else num(x, casas)


def _s(x: float | None, casas: int = 1) -> str:
    """Com sinal explícito e o menos tipográfico."""
    if x is None:
        return "n/d"
    if round(x, casas) == 0:
        return num(0.0, casas)
    return ("+" if x > 0 else "−") + num(abs(x), casas)


def _n(x: int | float | None) -> str:
    return "n/d" if x is None else num(float(x), 0)


def _h(x: float | None) -> str:
    return rotulo_hora(x)


def _d(x: float | None) -> str:
    return rotulo_duracao(x)


def _ic(m: Mapping[str, Any] | None, casas: int = 1) -> str:
    if not m or m.get("ic95") is None:
        return "n/d"
    lo, hi = m["ic95"]
    return f"de {_s(lo, casas)} a {_s(hi, casas)}"


# ---------------------------------------------------------------- acessores


def estimador(d: Mapping[str, Any], ident: str) -> Mapping[str, Any]:
    for e in d["voto"]["estimadores"]:
        if e["id"] == ident:
            return e.get("resultado") or {}
    return {}


def coef(
    d: Mapping[str, Any], bloco: str, modelo: str, cand: str, nome: str
) -> Mapping[str, Any]:
    """Coeficiente de `lula_hora[bloco]` (por_faixa ou inclinacao)."""
    for m in d["lula_hora"][bloco]:
        if m["id"] == modelo:
            return ((m.get(cand) or {}).get("coeficientes") or {}).get(nome) or {}
    return {}


def faixa_tamanho(d: Mapping[str, Any], nome: str) -> Mapping[str, Any]:
    return next((x for x in d["tamanho"]["linhas"] if x["faixa"] == nome), {})


def tipo(d: Mapping[str, Any], nome: str) -> Mapping[str, Any]:
    return next((x for x in d["tipo_local"]["linhas"] if x["tipo"] == nome), {})


def bruta(d: Mapping[str, Any], grupo: str, faixa: str) -> Mapping[str, Any]:
    return next(
        (
            x
            for x in d["lula_hora"]["bruta"]
            if x["grupo"] == grupo and x["faixa"] == faixa
        ),
        {},
    )


def regioes_ordem(d: Mapping[str, Any], chave: str) -> list[Mapping[str, Any]]:
    """Regiões da maior para a menor parcela depois das 18h (`chave` = régua)."""
    return sorted(
        d["distribuicao"]["regioes"],
        key=lambda g: -((g.get(chave) or {}).get("depois_1800_pct") or 0),
    )


def ufs_ordem(d: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return sorted(
        (
            g
            for g in d["distribuicao"]["ufs"]
            if g["completa_2026"] and g.get("encerramento_2026")
        ),
        key=lambda g: -(g["encerramento_2026"].get("depois_1800_pct") or 0),
    )


def frase_lacuna(d: Mapping[str, Any]) -> str:
    """O buraco na hora de recebimento de 2026 (a pausa do TSE), com o número."""
    lac = d["distribuicao"].get("lacuna_recebimento") or {}
    a, b = lac.get("2026") or {}, lac.get("2022") or {}
    if not a:
        return ""
    corte = (d["persistencia"].get("decil") or {}).get("corte_2026_min")
    efeito = ""
    if corte is not None and corte <= (a.get("ultimo_antes_min") or 0):
        efeito = (
            f" O corte do décimo mais tardio de 2026 ({_h(corte)}) cai antes do buraco: "
            "quem ficou preso nele continua no décimo."
        )
    return (
        f"A régua de chegada de 2026 tem um buraco: nenhum boletim registrado como recebido "
        f"entre {_h(a.get('ultimo_antes_min'))} e {_h(a.get('primeiro_depois_min'))} "
        f"({_p(a.get('minutos'))} minutos) e {_n(a.get('secoes_5min_depois'))} nos cinco minutos "
        "seguintes. É a pausa geral do TSE da noite; nesse trecho a hora de chegada mede o "
        f"tribunal, não a seção. Em 2022, o maior buraco foi de {_p(b.get('minutos'))} minutos."
        + efeito
    )


# ---------------------------------------------------------------- achados


def achados(d: Mapping[str, Any]) -> dict[str, list[str]]:
    br = d["distribuicao"]["brasil"]
    enc, r26, r22 = (
        br.get("encerramento_2026") or {},
        br.get("recebimento_2026") or {},
        br.get("recebimento_2022") or {},
    )
    dec = br.get("decomposicao_2026") or {}
    t_max = faixa_tamanho(d, "400 ou mais")
    t_min = faixa_tamanho(d, "até 199")
    p = d["persistencia"]
    pdec = p.get("decil") or {}
    cor = p.get("correlacao") or {}
    loc = p.get("locais") or {}
    rur = next(
        (
            x
            for x in loc.get("por_tipo") or []
            if x["tipo"] == "zona rural, assentamento ou quilombo"
        ),
        {},
    )
    e22 = estimador(d, "recebimento_decil_2022")
    e26 = estimador(d, "recebimento_decil_2026")
    z18 = estimador(d, "tarde18_zona")
    zt = estimador(d, "tarde18_zona_tamanho")
    ib = coef(d, "inclinacao", "bruta", "lula", "horas_atraso")
    iz = coef(d, "inclinacao", "zona", "lula", "horas_atraso")
    ic = coef(d, "inclinacao", "zona_controles", "lula", "horas_atraso")
    fb = coef(d, "por_faixa", "bruta", "lula", "depois de 19:00")
    fz = coef(d, "por_faixa", "zona", "lula", "depois de 19:00")
    fc = coef(d, "por_faixa", "zona_controles", "lula", "depois de 19:00")
    sob = d["lula_hora"]["sobrevive_pct"]
    ma = d["explicacoes"]["modelo_atraso"]
    tam = (ma.get("so_tamanho") or {}).get("coeficientes") or {}
    top = (tam.get("votantes 350 ou mais") or {}).get("estimativa")
    cob = d["cobertura"]
    vazia = bruta(d, "Brasil", "até 17:00")
    ufs = ufs_ordem(d)
    out: dict[str, list[str]] = {
        "contrario": [
            f"O atraso é, antes de tudo, tamanho de seção: com 400 aptos ou mais, "
            f"{_p((t_max.get('encerramento_2026') or {}).get('depois_1800_pct'))}% das seções "
            f"encerraram às 18h ou depois; com até 199, "
            f"{_p((t_min.get('encerramento_2026') or {}).get('depois_1800_pct'))}%. Dentro da "
            f"mesma zona, a seção com 350 votantes ou mais tem {_p(top)} pontos a mais de "
            "chance de fechar às 18h ou depois do que a de 200 a 249.",
            "Onde a eleição termina tarde nos dois anos, termina tarde mais por distância "
            f"do que por fila: nos {_n(pdec.get('persistentes'))} municípios persistentes a "
            f"votação terminou, na mediana, às {_h(pdec.get('encerramento_mediana_persistentes'))} "
            f"e a mídia levou {_d(pdec.get('transmissao_mediana_persistentes'))} até o TSE; no "
            f"conjunto, {_h(pdec.get('encerramento_mediana_todos'))} e "
            f"{_d(pdec.get('transmissao_mediana_todos'))}. Dos "
            f"{_n(loc.get('persistentes'))} locais de votação persistentes, "
            f"{_p(rur.get('pct_dos_persistentes'))}% ficam em zona rural, assentamento ou "
            f"quilombo pelo nome e endereço, contra {_p(rur.get('pct_dos_locais'))}% dos "
            "locais comparados.",
            "A seção que chega tarde ao TSE vota mais em Lula do que o resto da própria zona "
            "nos dois anos, e por margem parecida: "
            f"{_s((e22.get('lula_pp') or {}).get('estimativa'))} pontos em 2022 e "
            f"{_s((e26.get('lula_pp') or {}).get('estimativa'))} em 2026 (décimo mais tardio "
            "de cada ano). O padrão não nasceu em 2026.",
        ],
        "verificado": [
            f"Nas {len(cob['ufs_completas'])} UFs completas, metade das urnas encerrou a "
            f"votação até as {_h(enc.get('mediana'))} de Brasília; "
            f"{_p(enc.get('depois_1800_pct'))}% encerraram às 18h ou depois e "
            f"{_p(enc.get('depois_1900_pct'))}% às 19h ou depois.",
            f"Nenhuma urna encerrou antes das 17h de Brasília ({_n(vazia.get('secoes'))} "
            "seções nessa faixa), coerente com a regra: às 17h quem está na fila recebe "
            "senha e vota depois.",
            f"O boletim chegou ao TSE, na mediana, às {_h(r26.get('mediana'))} em 2026 e às "
            f"{_h(r22.get('mediana'))} em 2022, nas mesmas UFs; depois das 19h chegaram "
            f"{_p(r26.get('depois_1900_pct'))}% das seções em 2026 e "
            f"{_p(r22.get('depois_1900_pct'))}% em 2022.",
            "As UFs com maior parcela de seções encerradas às 18h ou depois: "
            + "; ".join(
                f"{g['chave']} {_p(g['encerramento_2026'].get('depois_1800_pct'))}%"
                for g in ufs[:5]
            )
            + "; as de menor: "
            + "; ".join(
                f"{g['chave']} {_p(g['encerramento_2026'].get('depois_1800_pct'))}%"
                for g in ufs[-3:]
            )
            + ".",
            frase_lacuna(d),
            f"Da hora de recebimento de 2026, a fila (17h até o último voto) responde por "
            f"{_d(dec.get('fila_mediana_min'))} na mediana e o caminho da mídia até o TSE por "
            f"{_d(dec.get('transmissao_mediana_min'))}.",
        ],
        "inferido": [
            f"Sem controle, cada hora de atraso no encerramento vem com "
            f"{_s(ib.get('estimativa'), 2)} pontos de Lula nos válidos. Dentro da mesma zona, "
            f"{_s(iz.get('estimativa'), 2)} (IC 95% {_ic(iz, 2)}); dentro da zona com "
            f"tamanho e tipo de local, {_s(ic.get('estimativa'), 2)} (IC 95% {_ic(ic, 2)}). "
            f"Sobra {_p(sob.get('lula_inclinacao'))}% da correlação bruta.",
            f"Seções que encerraram depois das 19h: {_s(fb.get('estimativa'))} pontos de "
            f"Lula sem controle, {_s(fz.get('estimativa'))} dentro da zona e "
            f"{_s(fc.get('estimativa'))} com tamanho e tipo, contra as que encerraram entre "
            "17:00 e 17:30.",
            f"A seção tardia tem mais eleitor habilitado por ano de nascimento (biometria "
            f"que não reconheceu): {_s((z18.get('ano_nascimento_pp') or {}).get('estimativa'), 2)} "
            f"ponto dentro da zona e {_s((zt.get('ano_nascimento_pp') or {}).get('estimativa'), 2)} "
            "dentro da zona e da faixa de tamanho. Com o mesmo tamanho, ela processou "
            f"{_p(abs((zt.get('votantes_hora') or {}).get('estimativa') or 0), 1)} votantes "
            "por hora a menos: votação mais lenta, não só mais gente.",
            f"O atraso persiste no lugar: a correlação de postos entre a mediana municipal de "
            f"recebimento de 2022 e a de 2026 é {_p(cor.get('spearman'), 2)} (IC 95% de "
            f"{_p((cor.get('spearman_ic95') or [None])[0], 2)} a "
            f"{_p((cor.get('spearman_ic95') or [None, None])[1], 2)}), "
            f"{_p(cor.get('spearman_dentro_uf'), 2)} dentro da UF; "
            f"{_n(pdec.get('persistentes'))} municípios ficaram no décimo mais tardio nos dois "
            f"anos, {_p(pdec.get('razao'), 1)} vezes o esperado por acaso.",
        ],
        "juizo": [
            "A providência barata é pôr fiscal de partido nas seções que historicamente "
            "fecham tarde: é ali que a fila depois das 17h, o mesário e a boca de urna ficam "
            "sem testemunha. A lei permite que um fiscal cubra todas as seções do mesmo local "
            f"(Lei 9.504, art. 65, § 1º); os {_n(loc.get('persistentes'))} locais persistentes "
            f"somam {_n(loc.get('secoes_2026_nos_persistentes'))} seções.",
            "O número que importa é o que sobra dentro da zona, com tamanho e tipo de local "
            "controlados. Ele existe e é positivo para Lula; ele não diz por quê.",
        ],
        "hipotese": [
            "Mesário que vota no lugar de ausente (o pianista), compra de voto e boca de urna "
            "são hipóteses, não achados: o boletim não as testa. O que as testaria é o log da "
            "urna (cada habilitação com hora e forma; uma sequência de habilitações por ano "
            "de nascimento em poucos segundos no fim do dia é a assinatura do pianista), a ata "
            "da mesa (ocorrências, fiscais presentes, senhas entregues às 17h), boletim de "
            "ocorrência e representação ao juiz eleitoral ou ao Ministério Público Eleitoral.",
            "A parte da correlação que sobra dentro da zona pode vir do perfil do eleitor da "
            "seção (idade, escolaridade, trabalho braçal), que pesa ao mesmo tempo na "
            "identificação biométrica e no voto. Sem idade por seção para o país, isso fica "
            "hipótese.",
        ],
    }
    for lista in out.values():
        for frase in lista:
            if PROIBIDO in frase:
                raise ValueError("travessão no achado")
    return out


# ---------------------------------------------------------------- memorando


def _linha_resumo(rot: str, r: Mapping[str, Any] | None) -> str:
    if not r:
        return f"| {rot} | n/d | | | | | | |"
    return (
        f"| {rot} | {_n(r['secoes'])} | {_h(r['mediana'])} | {_h(r['p90'])} | "
        f"{_h(r['p99'])} | {_p(r['depois_1730_pct'])} | {_p(r['depois_1800_pct'])} | "
        f"{_p(r['depois_1900_pct'])} |"
    )


CAB = (
    "| grupo | seções | mediana | p90 | p99 | % 17:30+ | % 18:00+ | % 19:00+ |\n"
    "|---|---|---|---|---|---|---|---|"
)


def memorando(d: Mapping[str, Any]) -> str:
    c = d["cobertura"]
    L: list[str] = [
        f"# {d['titulo']}",
        "",
        f"Gerado em {d['gerado_em']} por `scripts/apuracao-2026-fechamento.py`. Dados em "
        "`analysis/apuracao_2026/dados/fechamento.json`.",
        "",
        f"> {d['aviso']}",
        "",
    ]
    if c["parcial"]:
        L += [
            f"**Coleta parcial.** UFs completas em 2026: {', '.join(c['ufs_completas'])}. "
            f"Em coleta: {', '.join(c['ufs_em_coleta']) or 'nenhuma'}. Sem boletim ainda: "
            f"{', '.join(c['ufs_sem_2026']) or 'nenhuma'}. As comparações entre anos usam só "
            "as UFs completas. Rodada final: rodar de novo este script e o build da página.",
            "",
        ]
    L += ["## Definições", ""]
    L += [f"- **{k}**: {v}." for k, v in d["definicoes"].items()]
    L += [
        "",
        f"- Seções de 2026 com boletim (Brasil, sem exterior): {_n(c['secoes_2026'])}; "
        f"com voto conferido: {_n(c['secoes_2026_validas_voto'])}; com relógio ou fuso "
        f"inconsistente (sem encerramento): {_n(c['fuso_inconsistente'])}.",
        f"- Seções de 2022 (Brasil): {_n(c['secoes_2022'])}; nas UFs completas de 2026: "
        f"{_n(c['secoes_2022_mesmas_ufs'])}.",
        "",
        "## 1. Quando a votação termina",
        "",
        "Encerramento (2026, último voto, hora de Brasília):",
        "",
        CAB,
    ]
    D = d["distribuicao"]
    grupos = [D["brasil"], *D["regioes"]]
    L += [_linha_resumo(g["chave"], g.get("encerramento_2026")) for g in grupos]
    L += ["", "Recebimento no TSE, 2026:", "", CAB]
    L += [_linha_resumo(g["chave"], g.get("recebimento_2026")) for g in grupos]
    L += ["", "Recebimento no TSE, 2022 (mesmas UFs):", "", CAB]
    L += [_linha_resumo(g["chave"], g.get("recebimento_2022")) for g in grupos]
    L += [
        "",
        "Por UF (encerramento 2026 | recebimento 2026 | recebimento 2022, % depois das 18h e mediana):",
        "",
        "| UF | completa | enc. % 18h+ | enc. mediana | rec. 2026 mediana | rec. 2022 mediana |",
        "|---|---|---|---|---|---|",
    ]
    for g in D["ufs"]:
        e = g.get("encerramento_2026") or {}
        a = g.get("recebimento_2026") or {}
        b = g.get("recebimento_2022") or {}
        L.append(
            f"| {g['chave']} | {'sim' if g['completa_2026'] else 'não'} | "
            f"{_p(e.get('depois_1800_pct'))} | {_h(e.get('mediana'))} | "
            f"{_h(a.get('mediana'))} | {_h(b.get('mediana'))} |"
        )
    L += [
        "",
        "Por tamanho (aptos da seção), UFs completas:",
        "",
        "| faixa | seções 2026 | votantes médios | % enc. 18h+ | % das tardias | % rec. 19h+ 2026 | % rec. 19h+ 2022 |",
        "|---|---|---|---|---|---|---|",
    ]
    for x in d["tamanho"]["linhas"]:
        L.append(
            f"| {x['faixa']} | {_n(x['secoes_2026'])} | {_p(x['votantes_medio_2026'])} | "
            f"{_p((x['encerramento_2026'] or {}).get('depois_1800_pct'))} | "
            f"{_p(x['pct_das_tardias_2026'])} | "
            f"{_p((x['recebimento_2026'] or {}).get('depois_1900_pct'))} | "
            f"{_p((x['recebimento_2022'] or {}).get('depois_1900_pct'))} |"
        )
    L += [
        "",
        "Por tipo de local inferido, UFs completas:",
        "",
        "| tipo | seções 2026 | % enc. 18h+ | % das tardias | rec. 2026 mediana | rec. 2022 mediana |",
        "|---|---|---|---|---|---|",
    ]
    for x in d["tipo_local"]["linhas"]:
        L.append(
            f"| {x['tipo']} | {_n(x['secoes_2026'])} | "
            f"{_p((x['encerramento_2026'] or {}).get('depois_1800_pct'))} | "
            f"{_p(x['pct_das_tardias_2026'])} | "
            f"{_h((x['recebimento_2026'] or {}).get('mediana'))} | "
            f"{_h((x['recebimento_2022'] or {}).get('mediana'))} |"
        )
    L += [
        "",
        d["tipo_local"]["aviso"],
        "",
        "## 2. Persistência (régua de recebimento)",
        "",
    ]
    p = d["persistencia"]
    cor = p.get("correlacao") or {}
    pd_ = p.get("decil") or {}
    p19 = p.get("p90_depois_19h") or {}
    L += [
        f"- Critério: {p.get('criterio_municipio')}. Municípios comparados: {_n(p.get('municipios'))}.",
        f"- Mediana das medianas municipais: {_h(p['mediana_das_medianas']['2022'])} em 2022 e "
        f"{_h(p['mediana_das_medianas']['2026'])} em 2026.",
        f"- Correlação 2022 × 2026 da mediana municipal: Pearson {_p(cor.get('pearson'), 3)}, "
        f"Spearman {_p(cor.get('spearman'), 3)} (IC 95% {_p(cor['spearman_ic95'][0], 3)} a "
        f"{_p(cor['spearman_ic95'][1], 3)}); dentro da UF, Pearson {_p(cor.get('pearson_dentro_uf'), 3)} "
        f"e Spearman {_p(cor.get('spearman_dentro_uf'), 3)}.",
        f"- Décimo mais tardio nos dois anos (corte de 2022: {_h(pd_.get('corte_2022_min'))}; de "
        f"2026: {_h(pd_.get('corte_2026_min'))}): {_n(pd_.get('persistentes'))} municípios, contra "
        f"{_p(pd_.get('esperado_independencia'))} esperados por acaso ({_p(pd_.get('razao'), 2)} vezes).",
        f"- p90 de recebimento às 19h ou depois: {_n(p19.get('municipios_2026'))} municípios em 2026, "
        f"{_n(p19.get('municipios_2022'))} em 2022, {_n(p19.get('ambos'))} nos dois. O corte de hora "
        "fixo quase não separa nada em 2022, quando o recebimento inteiro foi mais tarde; por isso "
        "a persistência usa o décimo de cada ano.",
        "",
        "| UF | município | eleitorado | mediana 2022 | mediana 2026 | último voto (mediana) | transporte (mediana) | % rural |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for x in p.get("lista") or []:
        L.append(
            f"| {x['uf']} | {x['municipio']} | {_n(x['eleitorado_2026'])} | "
            f"{_h(x['mediana_2022'])} | {_h(x['mediana_2026'])} | "
            f"{_h(x['encerramento_mediana_2026'])} | {_d(x['transmissao_mediana_2026'])} | "
            f"{_p(x['rural_pct'], 0)} |"
        )
    loc = p.get("locais") or {}
    L += [
        "",
        f"Locais de votação casados entre os anos: {_n(loc.get('casados'))}; Spearman "
        f"{_p(loc.get('spearman'), 3)}; persistentes {_n(loc.get('persistentes'))} contra "
        f"{_p(loc.get('esperado_independencia'))} esperados; {_n(loc.get('secoes_2026_nos_persistentes'))} "
        "seções de 2026 dentro deles.",
        "",
        "## 3. Encerramento tardio e voto",
        "",
        "Bruta, por faixa de encerramento (% dos válidos, Brasil das UFs completas):",
        "",
        "| faixa | seções | votantes | Lula | Flávio |",
        "|---|---|---|---|---|",
    ]
    for x in d["lula_hora"]["bruta"]:
        if x["grupo"] == "Brasil":
            L.append(
                f"| {x['faixa']} | {_n(x['secoes'])} | {_n(x['votantes'])} | "
                f"{_p(x['lula_pct'], 2)} | {_p(x['flavio_pct'], 2)} |"
            )
    L += ["", "Inclinação (pontos por hora de atraso no encerramento):", ""]
    for m in d["lula_hora"]["inclinacao"]:
        cl = ((m.get("lula") or {}).get("coeficientes") or {}).get("horas_atraso") or {}
        cf = ((m.get("flavio") or {}).get("coeficientes") or {}).get(
            "horas_atraso"
        ) or {}
        L.append(
            f"- {m['rotulo']}: Lula {_s(cl.get('estimativa'), 2)} (IC 95% {_ic(cl, 2)}); "
            f"Flávio {_s(cf.get('estimativa'), 2)} (IC 95% {_ic(cf, 2)})."
        )
    L += [
        "",
        "Spearman seção a seção dentro da UF (hora de encerramento × % de Lula):",
        "",
    ]
    L += [
        f"- {x['uf']}: {_p(x['rho_lula'], 3)} ({_n(x['secoes'])} seções)"
        for x in d["lula_hora"]["spearman_uf"]
    ]
    L += ["", "Estimador do modelo de urna (seção tardia menos as demais da zona):", ""]
    for e in d["voto"]["estimadores"]:
        r = e.get("resultado") or {}
        partes = [
            f"{d['voto']['metricas'].get(k, k)} {_s((r.get(k) or {}).get('estimativa'), 2)} "
            f"({_ic(r.get(k), 2)})"
            for k in d["voto"]["metricas"]
            if r.get(k)
        ]
        L.append(
            f"- {e['rotulo']} ({e['ano']}; {_n(r.get('unidades'))} unidades, "
            f"{_n(r.get('secoes_b'))} seções tardias): " + "; ".join(partes) + "."
        )
    cf = d["conferencia_secoes"]
    pub = cf.get("publicado_secoes_json") or {}
    L += ["", "### Conferência com a análise por seção", ""]
    if pub:
        L.append(
            f"- Publicado em `secoes.json` ({pub.get('gerado_em')}, "
            f"{_n(pub.get('secoes_validas_na_base'))} seções válidas): {_n(pub.get('secoes'))} "
            f"seções depois das 19h, Lula {_s(pub.get('lula_pp'), 2)} e Flávio "
            f"{_s(pub.get('flavio_pp'), 2)} contra o resto da zona."
        )
    for k, rot in (
        (
            "base_atual_mesmas_ufs",
            "Base atual, mesmas UFs completas da rodada publicada",
        ),
        ("base_atual", "Base atual, todas as UFs com boletim"),
    ):
        x = cf.get(k)
        if not x:
            continue
        ez = (x.get("estimador_zona") or {}).get("lula_pp") or {}
        L.append(
            f"- {rot}: {_n(x['secoes_depois_19h'])} seções; fórmula da análise por seção "
            f"{_s(x['formula_secao_contra_resto']['lula_pp'], 2)}; a mesma fórmula contra só as "
            f"não tardias {_s(x['formula_secao_contra_demais']['lula_pp'], 2)}; estimador deste "
            f"capítulo {_s(ez.get('estimativa'), 2)} (IC 95% {_ic(ez, 2)})."
        )
    L += ["", cf.get("diferenca_de_metodo", ""), "", "## Achados", ""]
    rot = {
        "contrario": "Achado contrário",
        "verificado": "Verificado",
        "inferido": "Inferido",
        "juizo": "Juízo editorial",
        "hipotese": "Hipótese",
    }
    for k, nome in rot.items():
        L += [f"### {nome}", ""] + [f"- {x}" for x in d["achados"].get(k) or []] + [""]
    L += ["## Fontes legais", ""]
    L += [
        f"- {f['norma']}, {f['dispositivo']}: {f['conteudo']}. Conferido {f['como_conferido']}."
        for f in d["fontes_legais"]
    ]
    L += ["", "## Limites", ""] + [f"- {x}" for x in d["limites"]] + [""]
    texto = "\n".join(L)
    if PROIBIDO in texto:
        raise ValueError("travessão no memorando")
    return texto
