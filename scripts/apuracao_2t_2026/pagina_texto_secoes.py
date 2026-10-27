"""Textos do capítulo "Seção por seção" do dossiê do 2º turno.

Cada função recebe os JSONs e devolve HTML. Todo número vem de ``secoes.json``,
``secoes_voto.json``, ``secoes_ranking.json`` e ``noticias_noite.json``; as frases
que comparam (mais, menos, subiu, caiu) escolhem o verbo pelo próprio número,
para continuarem certas quando o banco completo substituir a amostra.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import (
    caixa,
    cartao,
    inteiro,
    nota,
    num,
    p,
    sinal,
)

from .pagina_fig_secoes_base import (
    descricao_fonte,
    eh_amostra,
    fmt_ind,
    hhmm,
    indicador,
    linhas,
    min_de,
    secoes_pais,
)
from .secoes_linhas import LinhasAusentes

ROTULO = "Sinal pede explicação, não prova irregularidade."

# Itens do noticiário citados no capítulo: trecho do endereço de cada matéria.
# Trecho do endereço e, quando a mesma matéria rende mais de um item, a hora do item.
NOTICIAS = [
    ("stf-prorroga-votacao", None),
    ("zanin-manda-ampliar", None),
    ("tse-avisou-secoes-sobre-prorrogacao", "17:49"),
    ("horario-de-votacao-ampliado-sera-apenas", None),
    ("secoes-eleitorais-ainda-abertas", None),
    ("80-das-urnas-estavam-encerradas", None),
    ("tse-retoma-contagem", None),
    ("nunes-marques-pronunciamento", "21:55"),
]
TIPO_NOTICIA = {
    "fato": "fato relatado",
    "declaracao": "declaração",
    "relato": "relato",
    "hipotese": "hipótese",
}


def _b(S: dict) -> dict:
    return S["agregados"]["brasil"]


def _pr(S: dict) -> dict:
    return S["prorrogacao"]["brasil"]


def _mais_menos(a: float | None, b: float | None) -> str:
    if a is None or b is None:
        return "comparável a"
    return "menos que" if a < b else "mais que" if a > b else "igual a"


# ------------------------------------------------------------------ abertura


def titulo(S: dict) -> str:
    p50 = _pr(S).get("encerramento_p50") or ""
    if p50 and p50 < "17:30":
        return "Seção por seção.<br><em>A urna fechou às 17h; o BU esperou.</em>"
    return "Seção por seção.<br><em>Encerramento, biometria, comparecimento.</em>"


def lead(S: dict) -> str:
    pr = _pr(S)
    return (
        f"Último voto na mediana às {pr.get('encerramento_p50')}, 99º percentil às "
        f"{pr.get('encerramento_p99')}. Só {fmt_ind(S, 'recebido_antes_1900')} dos BUs chegaram "
        "ao TSE antes das 19:00."
    )


def fonte(S: dict) -> str:
    return caixa("io", "Que base este capítulo lê", f" {descricao_fonte(S)} {ROTULO}")


def cartoes(S: dict) -> str:
    pr = _pr(S)
    a19 = indicador(S, "apos_19h")
    rec = indicador(S, "recebido_antes_1900")
    return (
        '<div class="finding-grid">'
        + cartao(
            pr.get("encerramento_p50") or "s/d",
            f"encerramento do BU, mediana das seções (99º percentil {pr.get('encerramento_p99')})",
        )
        + cartao(f"{num(a19['pct'], 2)}%", "dos BUs encerrados depois das 19:00")
        + cartao(f"{num(rec['pct'], 2)}%", "dos BUs recebidos pelo TSE antes das 19:00")
        + cartao(
            f"{num(pr.get('lag_encerramento_recebimento_p50_min'), 0)} min",
            "do encerramento do BU ao recebimento, mediana",
        )
        + "</div>"
    )


# ------------------------------------------------------------------ horário


def encerramento(S: dict) -> str:
    pr = _pr(S)
    b = _b(S)
    enc = b["encerramento"]
    u1 = (S.get("enc_1t_pct") or {}).get("apos_1900")
    a19 = indicador(S, "apos_19h")
    verbo = _mais_menos(a19["pct"], u1)
    sp = secoes_pais(S, "apos_19h")
    sp = f", {sp}" if sp else ""
    return p(
        "A premissa de que as urnas ficaram abertas até as 19h não passa no BU. O encerramento do BU "
        "(o último cômputo registrado no boletim, não um voto identificado) "
        f"tem mediana às {pr.get('encerramento_p50')}, 90º percentil às {pr.get('encerramento_p90')} "
        f"e 99º às {pr.get('encerramento_p99')}; {num(pr.get('pct_ate_1715'), 2)}% das seções da base "
        f"encerraram até 17:15. O BU saiu {num(pr.get('emissao_menos_encerramento_p50_min'), 0)} min "
        f"depois do encerramento (mediana) e {num(pr.get('pct_bu_emitido_ate_1730'), 2)}% dos BUs "
        "estavam emitidos até 17:30. Emitir o BU encerra a votação naquela urna. Encerraram o BU depois das "
        f"19:00 {fmt_ind(S, 'apos_19h')} das seções do país{sp}: {verbo} os {num(u1, 2)}% do "
        f"universo do 1º turno ({num(enc.get('pct_apos_1900_1t_mesmas'), 2)}% nas mesmas seções da "
        "base). O 2º turno tem um ou dois cargos contra seis no 1º, e a fila anda mais depressa.",
        "verificado",
    )


def recebimento(S: dict) -> str:
    pr = _pr(S)
    ant = [x for x in linhas(S) if x.get("rec_min") is not None and x["rec_min"] < 120]
    tarde = []
    for u in S["prorrogacao"]["por_uf"]:
        m = min_de(u.get("recebimento_primeiro"))
        if m is not None and m >= 120:
            tarde.append((m, u["uf"], u["recebimento_primeiro"]))
    tarde.sort()
    frase_ant = ""
    if ant:
        ufs_ant = sorted({x["uf"] for x in ant})
        frase_ant = (
            f" Na base, os {inteiro(len(ant))} BUs que chegaram antes das 19:00 chegaram todos até "
            f"{hhmm(max(x['rec_min'] for x in ant))}, nos primeiros minutos depois do fechamento, em "
            f"{len(ufs_ant)} UFs ({', '.join(ufs_ant)}); depois disso, nenhum até as 19h."
        )
    frase_ufs = ""
    if tarde:
        ult = tarde[-1]
        resto = tarde[:-1]
        if resto:
            faixa = (
                f"às {resto[0][2]}"
                if resto[0][2] == resto[-1][2]
                else f"entre {resto[0][2]} e {resto[-1][2]}"
            )
            frase_ufs = (
                f" Em {len(resto)} UFs o primeiro recebimento da base só aparece {faixa} "
                f"({', '.join(u for _, u, _ in resto)}), e no {ult[1]} às {ult[2]}."
            )
        else:
            frase_ufs = (
                f" No {ult[1]}, o primeiro recebimento da base só aparece às {ult[2]}."
            )
    return p(
        f"O que atrasou foi a transmissão. Só {fmt_ind(S, 'recebido_antes_1900')} dos BUs foram "
        f"recebidos pelo TSE antes das 19:00.{frase_ant}{frase_ufs} Do encerramento do BU ao recebimento "
        f"passaram {num(pr.get('lag_encerramento_recebimento_p50_min'), 0)} min na mediana "
        f"(90º percentil {num(pr.get('lag_encerramento_recebimento_p90_min'), 0)} min); a mediana do "
        f"recebimento é {pr.get('recebimento_p50')}.",
        "verificado",
    )


def _hora_item(i: dict) -> str:
    q = i.get("quando") or ""
    return q[11:16] if len(q) >= 16 else "sem hora"


def noticias(N: dict | None) -> str:
    if not N:
        return ""
    itens = []
    for chave, hora_item in NOTICIAS:
        for i in N.get("itens", []):
            if chave in (i.get("url") or "") and hora_item in (None, _hora_item(i)):
                itens.append(i)
                break
    if not itens:
        return ""
    itens.sort(key=_hora_item)
    lis = "".join(
        f"<li><b>{_hora_item(i)}</b> {escape(i.get('resumo') or '')} "
        f'(<a href="{escape(i["url"])}" rel="noopener">{escape(i.get("veiculo") or "fonte")}</a>; '
        f"{TIPO_NOTICIA.get(i.get('tipo'), i.get('tipo') or '')})</li>"
        for i in itens
    )
    return (
        p(
            "O noticiário da noite conta a mesma história pela outra ponta. As horas são as das "
            "matérias; a cópia de cada página está guardada com SHA-256 em "
            "<code>analysis/apuracao_2t_2026/noticias_fontes/</code>.",
            "relato",
        )
        + f'<ul class="cronologia">{lis}</ul>'
    )


def leitura_horario(S: dict) -> str:
    t19 = _b(S)["encerramento"].get("n_tardias")
    n = _b(S).get("n")
    return nota(
        "inferencia",
        "a extensão até as 19h não deixou o país votando. A urna fechou quando acabou a fila, o BU "
        "foi emitido em minutos e ficou à espera da transmissão. Quem atribuir a alta de "
        "comparecimento à prorrogação precisa mostrar seção que votou depois das 17h: na base lida "
        f"são {inteiro(t19)} tardias em {inteiro(n)} seções. Por que o recebimento só começou perto "
        "das 19h (ordem do TSE, regra de transmissão ou bloqueio da rede) não está nos BUs: é "
        "pergunta à Justiça Eleitoral.",
        "Leitura.",
    )


# ------------------------------------------------------------------ comparecimento


def comparecimento(S: dict) -> str:
    quedas = [
        (u["uf"], u["delta_comp"]["media"])
        for u in S["agregados"]["por_uf"]
        if (u.get("delta_comp") or {}).get("media") is not None
        and u["delta_comp"]["media"] <= -3
    ]
    quedas.sort(key=lambda q: q[1])
    fq = ""
    if quedas:
        fq = (
            " E houve queda: na média por seção, o comparecimento caiu contra o 1º turno em "
            + ", ".join(f"{u} ({sinal(v, 2)} pp)" for u, v in quedas)
            + "."
        )
    d = secoes_pais(S, "delta")
    d = f", {d}" if d else ""
    return p(
        f"O comparecimento subiu {fmt_ind(S, 'media_delta_pp', 2, ' pp')} por seção contra a "
        f"própria seção no 1º turno. Subiram 5 pp ou mais {fmt_ind(S, 'delta')} das seções{d}; "
        f"mas só {fmt_ind(S, 'delta_relativo')} ficaram 5 pp acima da alta mediana do próprio "
        "município ou UF. A alta é geral e pequena, não pontual. Caíram 5 pp ou mais "
        f"{fmt_ind(S, 'queda5')}.{fq}",
        "verificado",
    )


# ------------------------------------------------------------------ biometria


def _maior_salto(R: dict) -> dict | None:
    cand = [s for s in R["secoes"] if s.get("salto_bio_pp") is not None]
    return max(cand, key=lambda s: s["salto_bio_pp"]) if cand else None


def biometria(S: dict, R: dict, V: dict | None = None) -> str:
    b = _b(S)
    sb, an, pe = b["sem_biometria"], b["ano_nascimento"], b["persistencia"]
    h = p(
        f"Sem biometria cadastrada: {num(sb['pct_2t'], 2)}% dos votantes no 2º turno contra "
        f"{num(sb['pct_1t_mesmas'], 2)}% nas mesmas seções no 1º. Das {inteiro(pe['sem_bio_n'])} "
        f"seções com sinal, {inteiro(pe['sem_bio_ja_no_1t'])} já tinham o mesmo sinal no 1º turno "
        f"(variação mediana {sinal(pe['sem_bio_dif_p50_pp'], 2)} pp): é estrutural, do cadastro, "
        f"não do dia. Habilitados por ano de nascimento (biometria cadastrada e não reconhecida): "
        f"{num(an['pct_2t'], 2)}% contra {num(an['pct_1t_mesmas'], 2)}%; aqui o sinal se move mais, "
        f"{inteiro(pe['ano_nasc_ja_no_1t'])} de {inteiro(pe['ano_nasc_n'])} já o tinham, variação "
        f"mediana {sinal(pe['ano_nasc_dif_p50_pp'], 2)} pp. Salto da parcela sem biometria "
        f"reconhecida contra a própria seção: {fmt_ind(S, 'sinal_salto_bio')} das seções do país.",
        "verificado",
    )
    m = _maior_salto(R)
    if m:
        h += nota(
            "hipotese",
            f"o maior salto da base é {escape(m.get('municipio') or '')} ({m['uf']}), zona "
            f"{m['zona']}, seção {m['secao']}: a parcela sem biometria reconhecida subiu "
            f"{sinal(m['salto_bio_pp'], 2)} pp contra o 1º turno, com habilitados por ano de "
            f"nascimento de {num(m.get('ano_nasc_pct_1t'), 2)}% para {num(m.get('ano_nasc_pct_2t'), 2)}%, "
            f"comparecimento {sinal(m.get('delta_comp_pp'), 2)} pp e votos Flávio × Lula de "
            f"{inteiro(m.get('flavio_1t'))} × {inteiro(m.get('lula_1t'))} no 1º turno para "
            f"{inteiro(m.get('flavio_2t'))} × {inteiro(m.get('lula_2t'))} no 2º. O voto quase não "
            "mudou: é o padrão de um leitor biométrico que deixou de reconhecer a seção inteira. "
            "Hipótese a conferir no log da urna e na ata.",
            "Um leitor que falhou?",
        )
    n13 = b["salto_biometria"].get("n_comparecimento_e_salto")
    pi = secoes_pais(S, "pianista")
    pi = f", {pi}" if pi else ""
    h += p(
        f"Comparecimento +5 pp e salto de biometria na mesma seção: {fmt_ind(S, 'pianista')} do "
        f"país{pi} ({inteiro(n13)} na base lida). É o padrão mais próximo da hipótese do mesário "
        "que libera eleitor ausente, o “pianista”. A combinação também aparece quando o leitor falha "
        "num dia de fila maior; só a ata, o caderno de votação e o log separam as duas coisas."
        + _voto_celula_pianista(V, S),
        "inferencia",
    )
    return h


def _voto_celula_pianista(V: dict | None, S: dict | None = None) -> str:
    """O voto da célula do pianista (`secoes_voto.json`, sinal ``pianista``), quando existe."""
    c = next(
        (x for x in (V or {}).get("sinais") or [] if x.get("sinal") == "pianista"), None
    )
    if not c or c.get("did_fatia_flavio_pp") is None:
        return ""
    return (
        f" O voto nessa célula: a fatia de Flávio fica {sinal(c['dif_fatia_flavio_vs_vizinhas_pp'], 2)} pp "
        f"contra as vizinhas do município e, descontado o 1º turno, {sinal(c['did_fatia_flavio_pp'], 2)} pp "
        f"(erro-padrão {num(c['ep_did_fatia_flavio_pp'], 2)}, n {inteiro(c['n_did'])}): a célula votava "
        "assim antes e andou como as vizinhas entre os turnos."
        + _contingencia_celula(S)
    )


def _contingencia_celula(S: dict | None) -> str:
    """Urna de contingência na célula do pianista contra o país: explicação concorrente."""
    if not S:
        return ""
    try:
        ls = linhas(S)
    except LinhasAusentes:
        return ""
    cel = [
        x
        for x in ls
        if x.get("sinal_delta") and x.get("sinal_salto_bio") and x.get("uf") != "ZZ"
    ]
    pais = [x for x in ls if x.get("uf") != "ZZ"]
    if not cel or not pais:
        return ""
    pc = 100 * sum(1 for x in cel if x.get("contingencia")) / len(cel)
    pp_ = 100 * sum(1 for x in pais if x.get("contingencia")) / len(pais)
    return (
        f" Explicação concorrente: urna de contingência em {num(pc, 1)}% das seções da célula, "
        f"contra {num(pp_, 1)}% no país; a troca de urna muda leitor e cadastro no meio do dia."
    )


# ------------------------------------------------------------------ voto


def _sinal_v(V: dict, k: str) -> dict:
    for s in V["sinais"]:
        if s["sinal"] == k:
            return s
    return {}


def voto(V: dict) -> str:
    def par(k: str, nome: str) -> str:
        s = _sinal_v(V, k)
        if s.get("did_fatia_flavio_pp") is None:
            return ""
        return (
            f"{nome}: {sinal(s.get('dif_fatia_flavio_vs_vizinhas_pp'), 2)} pp contra as vizinhas, "
            f"{sinal(s['did_fatia_flavio_pp'], 2)} pp na diferença em diferenças "
            f"(ep {num(s.get('ep_did_fatia_flavio_pp'), 2)}, n {inteiro(s.get('n_did'))})"
        )

    partes = [
        par("delta", "Comparecimento +5 pp"),
        par("sinal_sem_bio", "sem biometria"),
        par("sinal_salto_bio", "salto de biometria"),
        par("delta_relativo", "alta acima da local"),
        par("tardia", "tardias"),
    ]
    h = p(
        "As seções com sinal votam diferente das vizinhas do mesmo município porque já votavam assim "
        "no 1º turno. A conta que separa as duas coisas é a diferença em diferenças: quanto a fatia "
        "de Flávio mudou entre os turnos na seção, menos quanto mudou nas vizinhas. "
        + "; ".join(x for x in partes if x)
        + ".",
        "verificado",
    )
    sig = [
        s
        for s in V["sinais"]
        if s.get("did_fatia_flavio_pp") is not None
        and s.get("ep_did_fatia_flavio_pp")
        and abs(s["did_fatia_flavio_pp"]) > 2 * s["ep_did_fatia_flavio_pp"]
    ]
    if sig:
        vals = [abs(s["did_fatia_flavio_pp"]) for s in sig]
        lado = (
            "na direção de Lula"
            if all(s["did_fatia_flavio_pp"] < 0 for s in sig)
            else "em direções diferentes"
        )
        h += nota(
            "inferencia",
            f"{len(sig)} sinais passam de dois erros-padrão ("
            + ", ".join(
                f"{escape(s.get('descricao') or s['sinal'])}: {sinal(s['did_fatia_flavio_pp'], 2)} pp"
                for s in sig
            )
            + f"). São deslocamentos de {num(min(vals), 1)} a {num(max(vals), 1)} pp, {lado}, "
            "sem mecanismo identificado: podem vir de quem decidiu votar no 2º turno, de mudança de "
            "voto concentrada em certos bairros ou do erro-padrão aproximado. Não medem intenção de "
            f"ninguém. {ROTULO}",
        )
    return h


def tabela_e_extras(S: dict, V: dict) -> str:
    b = _b(S)
    va = V.get("votos_absolutos") or {}
    papel = b["urna"].get("sistema_apuracao", b["sinais"].get("papel"))
    h = p(
        f"Urna de contingência ou com mais de uma carga: {fmt_ind(S, 'contingencia')} das seções; "
        f"BU do sistema de apuração (votação em cédula): {inteiro(papel)} na base lida. Escore 2 ou "
        f"mais, somando os seis sinais: {fmt_ind(S, 'escore2')}.",
        "verificado",
    )
    if va:
        h += p(
            f"Votos absolutos contra o 1º turno, seção a seção (n {inteiro(va.get('n'))}): Flávio "
            f"ganhou votos em {num(va['flavio_ganhou']['pct'], 2)}% das seções e Lula em "
            f"{num(va['lula_ganhou']['pct'], 2)}%; Flávio ganhou e Lula perdeu em "
            f"{inteiro(va['flavio_ganhou_lula_perdeu']['n'])}, o inverso em "
            f"{inteiro(va['lula_ganhou_flavio_perdeu']['n'])}. Ganho médio por seção: Flávio "
            f"{num(va.get('ganho_medio_flavio'), 2)}, Lula {num(va.get('ganho_medio_lula'), 2)} votos.",
            "verificado",
        )
    return h


def tabela_2x2x2_texto(V: dict) -> str:
    cel = {
        (c["comparecimento_alto"], c["biometria_baixa"]): c for c in V["tabela_2x2x2"]
    }
    a, z = cel.get((True, True)), cel.get((False, False))
    if not a or not z:
        return ""
    return p(
        "Se comparecimento alto e biometria baixa juntos fossem rastro de liberação indevida em "
        f"benefício de um lado, a fatia desse lado subiria mais nessa célula. Nas {inteiro(a['n'])} seções com os "
        f"dois sinais, a fatia de Flávio subiu em {inteiro(a['n_flavio_sobe'])} e mudou "
        f"{sinal(a.get('delta_fatia_flavio_pp'), 2)} pp; nas {inteiro(z['n'])} sem nenhum, mudou "
        f"{sinal(z.get('delta_fatia_flavio_pp'), 2)} pp. A célula combinada acompanha o país.",
        "verificado",
    )


# ------------------------------------------------------------------ ranking e fechamento


def ranking(R: dict) -> str:
    n_sem = sum(1 for s in R["secoes"] if s.get("sem_explicacao"))
    regras = "".join(f"<li>{escape(x)}</li>" for x in R.get("regras_explicacao") or [])
    return p(
        f"O ranking lista as {len(R['secoes'])} seções mais atípicas da base por escore e "
        "magnitude. Cada uma recebe uma explicação provável por regra declarada, quando alguma "
        f"cabe; {inteiro(n_sem)} não têm explicação pela regra e pedem conferência da ata e do log "
        "da urna. O mapa marca o prédio do local de votação.",
        "verificado",
    ) + (
        f'<details><summary>As {len(R.get("regras_explicacao") or [])} regras da explicação '
        f"provável</summary><ul>{regras}</ul></details>"
    )


def fiscal_e_log() -> str:
    return caixa(
        "io",
        "Quem responde o quê",
        "<p><strong>O fiscal e a ata confirmam</strong> a hora em que a seção encerrou, se houve fila às 17h e "
        "senhas distribuídas, troca de urna, falha do leitor biométrico registrada, eleitores "
        "habilitados por ano de nascimento e o número de votantes no caderno.</p>"
        "<p><strong>Só o log da urna responde</strong> o minuto de cada habilitação, a sequência de tentativas "
        "biométricas que falharam, as liberações manuais em rajada e se o leitor parou de reconhecer "
        "a seção inteira a partir de certa hora.</p>"
        "<p><strong>Nenhum dos dois diz em quem cada eleitor votou</strong>, e este capítulo nunca nomeia "
        "mesário, fiscal ou eleitor.</p>",
    )


def limites_itens(S: dict) -> list[str]:
    itens = []
    if eh_amostra(S):
        itens += [
            "Amostra de 150 seções por UF (600 nas UFs com governador): estima o país com IC de 95%, "
            "mas não localiza o caso raro, e as diferenças por UF ficam abaixo de n 20.",
            "O primeiro recebimento por UF é o da amostra, não o da UF; a contagem nacional de cada "
            "sinal e a vizinhança do mesmo local de votação só saem do banco completo.",
        ]
    itens += [
        "Horas do BU são locais: convertidas pelo fuso da UF e corrigidas por município pela "
        "abertura modal (a votação abriu às 08:00 de Brasília em todo o país).",
        "BU não diz quem votou: só a ata, o caderno de votação e o log separam falha de leitor, "
        "eleitor sem biometria e liberação indevida.",
        "Os votos do 1º turno vêm da seção principal no cadastro; seção agregada entre os turnos "
        "distorce a comparação (a explicação provável avisa).",
        "O erro-padrão da diferença em diferenças é aproximado, entre municípios.",
        ROTULO,
    ]
    return itens
