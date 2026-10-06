"""Capítulos 10 a 15 do dossiê da apuração: pesquisas, voto útil, anomalias, fiscais, 2º turno, auditoria."""

from __future__ import annotations

from html import escape

from . import pagina_texto_b as T
from . import pagina_texto_c as TC
from . import pagina_texto_fechamento as TF
from . import pagina_texto_reguas as PR
from . import pagina_texto_terceira_via as TV
from .pagina_comum import (
    Capitulo,
    Dados,
    checar,
    limites,
    nota,
    num,
    secao,
    sinal,
    tabela,
)
from .pagina_texto import fig

IMG = "img/apuracao_2026"


def dm(iso: str) -> str:
    return f"{iso[8:10]}/{iso[5:7]}" if iso and len(iso) >= 10 else (iso or "")


# ------------------------------------------------------------------ 10


def tabela_pesquisas(PV: dict) -> str:
    pes = sorted(
        PV["pesquisas"],
        key=lambda x: abs(x["publicado"]["diferenca_lula_menos_flavio"]["erro"]),
    )
    linhas = []
    fins = [x["campo"]["fim"] for x in pes]
    for x in pes:
        pub = x["publicado"]
        rep_err = (
            (x.get("reponderado") or {}).get("diferenca_lula_menos_flavio") or {}
        ).get("erro")
        linhas.append(
            [
                f"{escape(x['instituto'])}{' ●' if x.get('ultima_onda_da_casa') else ''}",
                f"{dm(x['campo']['inicio'])} a {dm(x['campo']['fim'])}",
                num(pub["validos"].get("flavio"), 2),
                num(pub["validos"].get("lula"), 2),
                sinal(pub["diferenca_lula_menos_flavio"]["erro"], 2),
                sinal(rep_err, 2) if rep_err is not None else "sem renda",
                num(x.get("margem_95_diferenca_aas_pp"), 2),
            ]
        )
    return tabela(
        [
            "Instituto",
            "Campo",
            "Flávio",
            "Lula",
            "Erro L−F",
            "Erro L−F reponderado",
            "Margem 95% da diferença",
        ],
        linhas,
        f"Pesquisas nacionais com campo encerrado de {dm(min(fins))} a {dm(max(fins))}, nos válidos pela regra da casa. "
        "Ordem: menor erro absoluto "
        "na diferença. ● última onda do instituto.",
    )


def r_pesquisas(d: Dados, cap: Capitulo) -> str:
    PV = d.get("pesquisas_vs_urna.json")
    checar(
        d,
        "pesquisas_vs_urna.json",
        [
            "pesquisas",
            "medias",
            "resumo_ultimas_ondas",
            "previsao_casa",
            "referencia_2022",
        ],
    )
    r = PV["resumo_ultimas_ondas"]["publicado"]
    h = secao(
        cap,
        "Pesquisas contra a urna.<br><em>O erro comum voltou.</em>",
        f"{sinal(r['media'], 2)} pontos na diferença Lula menos Flávio, na mesma direção de 2022.",
    )
    h += T.pesquisas_a(PV) + fig("pesquisas_erro", d)
    h += tabela_pesquisas(PV) + T.pesquisas_proximidade(PV)
    h += fig("pesquisas_serie", d) + T.pesquisas_reponderacao(PV)
    h += fig("central_casa_ufs", d) + T.pesquisas_central(PV)
    h += fig("senado_brier", d) + T.pesquisas_estaduais(PV)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 11


def r_voto_util(d: Dados, cap: Capitulo) -> str:
    V = d.get("voto_util.json")
    checar(
        d,
        "voto_util.json",
        [
            "terceira_via",
            "terceiros_por_candidato",
            "reserva_nacional",
            "decomposicao.agregados",
        ],
    )
    tv = V["terceira_via"]
    h = secao(
        cap,
        "Voto útil.<br><em>De um lado só.</em>",
        f"Terceira via de {num(tv['media_publicado_todas'], 2)}% nas pesquisas finais para {num(tv['urna_validos'], 2)}% na urna.",
    )
    h += T.voto_util_a(V) + fig("voto_util_cascata", d)
    h += T.voto_util_b(V) + T.voto_util_c(V) + fig("reserva_vs_urna", d)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 12


def r_anomalias(d: Dados, cap: Capitulo) -> str:
    A = d.get("anomalias.json")
    checar(d, "anomalias.json", ["topo", "resumo", "limites"])
    h = secao(
        cap,
        "Anomalias por zona.<br><em>Triagem, não acusação.</em>",
        "Escore alto quer dizer zona ou seção atípica dentro da própria UF, que pede explicação documental.",
    )
    h += T.anomalias_a(A) + fig("mapa_anomalias", d)
    h += T.anomalias_b(A) + fig("anomalias_features", d)
    C = d.get("contexto_seguranca.json")
    n_itens = len(C["itens"]) if C else None
    n_of = (
        len([i for i in C["itens"] if i.get("degrau") == "documento_oficial"])
        if C
        else None
    )
    h += T.anomalias_c(A, n_itens, n_of)
    lim = [
        escape(x).replace("não é fraude", "não é irregularidade")
        for x in A["limites"]
        if not x.startswith(("Zona pequena", "Explicação provável"))
    ]
    S = d.get("secoes.json")
    if S is None:
        d.aviso("secoes.json ausente: capítulo 12 só com a análise por zona")
    else:
        checar(d, "secoes.json", TC.CHAVES)
        h += TC.bloco(S, lambda nome: fig(nome, d))
        lim += TC.limites_secao(S)
    F = d.get("fechamento.json")
    if F is None:
        d.aviso("fechamento.json ausente: capítulo 12 sem o fechamento das seções")
    else:
        checar(d, "fechamento.json", TF.CHAVES)
        h += TF.bloco(F, lambda nome: fig(nome, d))
        lim += TF.limites_fechamento(F)
    h += limites(
        lim,
        "Os limites da noite (capítulos 2 e 3) valem aqui para as horas de chegada.",
    )
    return h + "</section>"


# ------------------------------------------------------------------ 13


def r_fiscais(d: Dados, cap: Capitulo) -> str:
    """Onde colocar fiscal no 2º turno (`fiscais.json`, contrato em CONTRATO_FISCAIS.md)."""
    h = secao(
        cap,
        "Onde colocar fiscal.<br><em>Prioridade, não acusação.</em>",
        "Atipicidade não é irregularidade: a lista diz onde conferir primeiro.",
    )
    return h + "</section>"


# ------------------------------------------------------------------ 14


def _tabela_movimentos(E: dict, TVJ: dict | None) -> str:
    mov = sorted(E["movimentos"], key=lambda m: m.get("ordem", 99))
    urna = PR.movimentos_urna(TVJ["reguas"]) if TVJ and "reguas" in TVJ else {}
    linhas = []
    for m in mov:
        u = urna.get(m.get("ordem"))
        if u is None:
            esperado, pela_urna, duas = "", "", ""
        else:
            esperado = PR.pv(u["pesquisa"], 0)
            if u["urna"] is None:
                pela_urna, duas = "não se aplica", escape(u.get("nota", ""))
            else:
                pela_urna = PR.pv(u["urna"], 0)
                duas = "mesmo sinal" if u["concordam"] else "sinal oposto"
        linhas.append(
            [
                f"{m.get('ordem', '')}. {escape(m['titulo'])}",
                escape(m.get("regra", "")),
                escape(m.get("rotulo", "")),
                esperado,
                pela_urna,
                duas,
            ]
        )
    return tabela(
        [
            "Movimento",
            "Regra",
            "Natureza",
            "Votos esperados",
            "Pela urna de 2022",
            "As duas réguas",
        ],
        linhas,
        "Os dez movimentos, com a régua do capítulo e, quando ela se aplica, a da urna de 2022. Eles se sobrepõem e "
        "não se somam.",
    )


def r_segundo_turno(d: Dados, cap: Capitulo) -> str:
    E = d.get("estrategia_2t.json")
    checar(
        d,
        "estrategia_2t.json",
        [
            "aritmetica.projecoes",
            "aritmetica.equilibrio",
            "geografia.estoque",
            "movimentos",
            "riscos",
        ],
    )
    TVJ = d.get("terceira_via.json")
    h = secao(
        cap,
        "O caminho do 2º turno.<br><em>Juízo editorial declarado.</em>",
        "A casa tem lado: o projeto é a vitória de Flávio. O método não tem lado: cada movimento sai com número e fonte, e o achado contrário sai com o mesmo peso.",
    )
    h += T.segundo_turno_a(E) + fig("transferencia_cenarios", d)
    h += T.segundo_turno_b(E) + T.segundo_turno_c(E) + fig("estoque_uf", d)
    h += T.segundo_turno_d(E) + T.segundo_turno_riscos(E)
    h += nota(
        "juizo",
        "A ordem dos dez movimentos é da casa. O número de cada um sai da regra escrita na tabela, sobre medição "
        "publicada ou analogia declarada; nenhum é previsão.",
    )
    h += fig("movimentos_2t", d) + _tabela_movimentos(E, TVJ)
    if TVJ is None:
        d.aviso(
            "terceira_via.json ausente: capítulo 14 sem o voto da terceira via por cidade"
        )
    else:
        checar(d, "terceira_via.json", TV.CHAVES)
        h += TV.bloco(TVJ, lambda nome: fig(nome, d))
    h += limites(
        TV.LIMITES,
        "Os limites das pesquisas (capítulos 10 e 11) valem para as matrizes de transferência.",
    )
    return h + "</section>"


# ------------------------------------------------------------------ 15

GALERIA = [
    (
        "live-mov.png",
        "Telão: movimento da apuração às 18h07",
        "Movimento dos válidos a cada leitura, das 17h às 18h.",
    ),
    (
        "i1-mun-zonas.png",
        "Telão: São Paulo por zona eleitoral",
        "Município de São Paulo por zona, às 18h12.",
    ),
    (
        "live-est-pr.png",
        "Telão: deputados estaduais do Paraná",
        "Deputados estaduais do Paraná em apuração.",
    ),
    (
        "f4-exterior-dados.png",
        "Telão: voto no exterior",
        "Tela do exterior no início da divulgação.",
    ),
    (
        "i1-diretor.png",
        "Painel de direção do telão",
        "Painel de direção: telas, estados e roteiro.",
    ),
    (
        "f3b-sen.png",
        "Telão: Senado em modo ensaio",
        "Modo ensaio, com arquivos de teste: os números não são da eleição.",
    ),
]


def r_auditoria(d: Dados, cap: Capitulo) -> str:
    P = d.get("presidente.json")
    L = d.get("linha_do_tempo.json")
    h = secao(
        cap,
        "Auditoria do próprio<br><em>acompanhamento.</em>",
        "O que o coletor da casa é, o que ele guardou e onde ele errou ao vivo.",
    )
    h += T.auditoria_a(P) + fig("auditoria_coletor", d)
    h += T.auditoria_b(L)
    erros = [
        "Os arquivos municipais não seguiam atualizando na pausa geral, como dissemos ao vivo (capítulo 3).",
        "A regra do coletor para cópia antiga comparava o contador de versão do TSE, que não cresce dentro do arquivo. A página usa a hora de geração.",
        "A hora de 100% de algumas UFs saiu atrasada no telão pela mesma regra; as horas desta página são as da hora de geração.",
    ]
    h += (
        "<h3>Onde o acompanhamento errou ao vivo</h3><ul>"
        + "".join(f"<li>{e}</li>" for e in erros)
        + "</ul>"
    )
    figs = ""
    for arq, alt, leg in GALERIA:
        alt_px = 1125 if arq == "i1-diretor.png" else 900
        figs += (
            f'<figure><img src="{IMG}/{arq}" alt="{escape(alt)}" loading="lazy" width="1600" height="{alt_px}">'
            f"<figcaption>{escape(leg)} Print do acompanhamento.</figcaption></figure>"
        )
    h += f'<details><summary>Prints do telão</summary><div class="galeria">{figs}</div></details>'
    h += limites(
        [
            "Os proporcionais por município guardam só o primeiro e o último retrato da noite.",
            "Os boletins por seção do capítulo 12 vêm de outra coleta, feita depois da noite, e não do telão.",
            "Campo é classificação editorial (tucano é centro-esquerda).",
        ]
    )
    return h + "</section>"
