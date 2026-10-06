"""Capítulo 13, "Onde colocar fiscal": texto gerado de `fiscais.json`.

Chamado por `pagina_cap_c.r_fiscais`. Contrato em
`analysis/apuracao_2026/CONTRATO_FISCAIS.md`. Regra da casa: figura antes do
parágrafo que a lê, nenhum número digitado, "atípico" e "exige explicação
documental" como vocabulário, nunca a palavra que acusa. As três frases de
`rotulos` abrem o capítulo e voltam nos limites. O bloco `risco` (contrato 1.1) é
opcional: sem ele, a parte do território vira um aviso de base pendente.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape

from .pagina_comum import NOME_UF, caixa, inteiro, limites, milhoes, nota, num, p
from .pagina_fig_base import nome_bonito
from .pagina_fig_fiscais import (
    ROT_NIVEL,
    bloco_download,
    criterios_txt,
    fonte_risco_html,
    tem_risco,
)
from .pagina_texto import lista

CHAVES = [
    "rotulos",
    "meta.criterios",
    "meta.cortes_nivel",
    "meta.exportaveis",
    "criterios",
    "secoes",
    "por_uf",
    "por_municipio",
    "por_local",
    "prioridade_pl.protege_flavio",
    "prioridade_pl.vigia_lula",
    "resumo.por_nivel",
    "resumo.eleitorado",
    "resumo.fiscais",
    "resumo.explicacao_comum",
    "mapa.pontos",
    "limites",
]
H3 = [
    "Como ler a lista",
    "Os critérios",
    "O achado contrário",
    "O mapa",
    "Por UF",
    "Contexto do território",
    "Os municípios",
    "Duas listas do PL",
    "As seções de nível alta",
    "Todos os locais com três ou mais seções",
    "Seções sem arquivo e zonas congeladas",
    "O que o TSE poderia publicar",
    "Fontes do capítulo",
]
CODIGO = {
    "aldeia": "aldeia indígena",
    "presidio": "unidade prisional",
    "exterior": "exterior",
    "transito": "voto em trânsito",
    "minuscula": "seção com menos de 50 votantes",
    "zona_rural": "zona rural",
    "quilombo_assentamento": "quilombo ou assentamento",
    "hospital": "hospital",
    "pequena": "seção de 50 a 99 votantes",
    "urna_trocada": "urna trocada",
    "enclave_2022": "enclave que já existia em 2022",
}


def aptos(x: float | None) -> str:
    """'2,22 milhões de aptos' ou '739 mil aptos' ("mil" não pede "de")."""
    v = milhoes(x or 0)
    return f"{v} de aptos" if "milh" in v else f"{v} aptos"


def pc(x: float | None, casas: int = 1) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def cobertura_local(F: dict) -> dict:
    """Um fiscal por local com três ou mais seções sinalizadas: quantos e quanto cobre."""
    total = len(F["secoes"]) or 1
    loc = [x for x in F["por_local"] if x.get("secoes", 0) >= 3]
    secoes = sum(x["secoes"] for x in loc)
    return {
        "locais": len(loc),
        "secoes": secoes,
        "pct": 100 * secoes / total,
        "aptos": sum(x.get("aptos_local") or 0 for x in loc),
    }


def frase_uso(F: dict) -> str:
    c = cobertura_local(F)
    return (
        f"Um fiscal por local com três ou mais seções sinalizadas cobre <strong>{pc(c['pct'])}</strong> dos sinais "
        f"({inteiro(c['secoes'])} de {inteiro(len(F['secoes']))} seções) com <strong>{inteiro(c['locais'])}</strong> "
        "pessoas, uma em cada local."
    )


# ------------------------------------------------------------------ abertura


def abertura(F: dict) -> str:
    R = F["resumo"]
    N, E, FI = R["por_nivel"], R["eleitorado"], R["fiscais"]
    alta = N.get("alta", {})
    h = p(
        f"Das {inteiro(R['secoes_universo'])} seções com boletim, <strong>{inteiro(R['secoes_sinalizadas'])}</strong> "
        f"dispararam ao menos um dos {len(F['criterios'])} critérios. Elas estão em "
        f"{inteiro(len(F['por_local']))} locais de votação e reúnem {aptos(E['aptos_sinalizadas'])} "
        f"({pc(E.get('pct_sinalizadas'), 2)} do eleitorado do universo). O nível alta tem "
        f"{inteiro(alta.get('secoes'))} seções em {inteiro(alta.get('locais'))} locais de "
        f"{inteiro(alta.get('municipios'))} municípios.",
        "verificado",
    )
    ul, us = FI["um_por_local"], FI["um_por_secao"]
    dois = FI.get("dois_por_secao_maximo_legal", {})
    h += p(
        f"Quantas pessoas isso pede: um fiscal por local cobre o nível alta com {inteiro(ul.get('alta'))} pessoas, "
        f"alta e média com {inteiro(ul.get('alta_media'))}, e a lista inteira com {inteiro(ul.get('todos'))}. "
        f"Um por seção pede {inteiro(us.get('alta'))}, {inteiro(us.get('alta_media'))} e {inteiro(us.get('todos'))}; "
        f"o máximo legal de dois por seção, {inteiro(dois.get('todos'))} ({escape(FI.get('base_legal', ''))}).",
        "inferencia",
    )
    h += nota(
        "juizo",
        escape(F.get("aviso") or " ".join(F["rotulos"].values())),
        "Frase responsável.",
    )
    h += bloco_download(F, frase_uso(F))
    return h


def como_ler(F: dict) -> str:
    cortes = F["meta"]["cortes_nivel"]
    corpo = (
        "<ul>"
        f"<li><strong>{ROT_NIVEL['alta']}</strong>: pontuação {cortes.get('alta')} ou mais, somando os pesos dos "
        "critérios, e nenhuma explicação comum no cadastro (aldeia, presídio, exterior, trânsito, seção minúscula). "
        "É onde o fiscal deve estar primeiro.</li>"
        f"<li><strong>{ROT_NIVEL['media']}</strong>: pontuação {cortes.get('media')} ou mais, ou alta com explicação "
        "comum. Fiscal se houver gente.</li>"
        f"<li><strong>{ROT_NIVEL['baixa']}</strong>: um sinal leve, ou seção que já era assim em 2022. Basta a "
        "conferência do boletim impresso.</li></ul>"
        "<p>O fiscal confere cinco coisas, nesta ordem: a <strong>zerésima</strong> impressa antes da votação, que "
        "prova a urna vazia; a <strong>ata da mesa</strong>, com ocorrências, troca de urna e horário; o "
        "<strong>horário de encerramento</strong>; o <strong>boletim de urna impresso</strong>, fotografado e "
        "comparado com o publicado pelo TSE; e, depois, o <strong>log da urna</strong>, que o partido pode pedir ao "
        f"TRE. {escape(cortes.get('regra', ''))}</p>"
    )
    return "<h3>Como ler a lista</h3>" + caixa("io", "Regra de leitura", corpo)


# ------------------------------------------------------------------ critérios


def criterios(F: dict, fig: Callable[[str], str]) -> str:
    h = "<h3>Os critérios</h3>" + fig("fiscais_criterios")
    crit = sorted(F["criterios"], key=lambda c: -c["secoes"])
    top = crit[:3]
    h += p(
        "Os três critérios que mais disparam são "
        + lista(
            [
                f"{escape(c['nome'])} ({inteiro(c['secoes'])} seções, {inteiro(c.get('so_este'))} só por ele)"
                for c in top
            ]
        )
        + ". Cada um tem uma explicação comum, que não exige nada de errado; a tabela traz a de todos.",
        "verificado",
    )
    itens = "".join(
        f"<li><strong>{escape(c['id'])}. {escape(c['nome'])}</strong>: {escape(c.get('mede') or c.get('regra', ''))} "
        f"Explicação comum: {escape(c.get('explicacao_comum', ''))}</li>"
        for c in F["criterios"]
    )
    h += f'<details><summary>Os {len(F["criterios"])} critérios em linguagem corrente</summary><ul>{itens}</ul></details>'
    return h


def contrario(F: dict) -> str:
    R = F["resumo"]
    ex = R["explicacao_comum"]
    cods = sorted(ex.get("por_codigo", {}).items(), key=lambda kv: -kv[1])
    partes = [f"{CODIGO.get(k, k)} ({inteiro(v)})" for k, v in cods if v]
    h = "<h3>O achado contrário</h3>"
    h += nota(
        "contrario",
        f"{inteiro(ex.get('secoes'))} das {inteiro(R['secoes_sinalizadas'])} seções sinalizadas "
        f"({pc(100 * (ex.get('secoes') or 0) / (R['secoes_sinalizadas'] or 1))}) têm explicação comum documentada no "
        f"próprio cadastro. Por código: {lista(partes) or 'nenhuma'}. Aldeia e presídio sozinhos levam "
        f"{inteiro(ex.get('baixa_aldeia_presidio'))} seções para o nível baixa, e {inteiro(R.get('enclaves_2022'))} "
        "seções já eram assim em 2022. Uma lista que cresce com aldeia, presídio e seção minúscula mede a geografia "
        "do país, não comportamento de mesa.",
    )
    S = F.get("sensibilidade") or {}
    if S.get("leitura"):
        h += p(
            f"Com pesos iguais no lugar dos pesos declarados, {inteiro(S.get('mudam_nivel'))} seções mudam de nível; a "
            f"correlação de postos da pontuação é {num(S.get('spearman_pontuacao'), 2)} e "
            f"{inteiro(S.get('top100_locais_comum'))} dos 100 primeiros locais continuam na lista. "
            + escape(S["leitura"]),
            "inferencia",
        )
    return h


# ------------------------------------------------------------------ mapa e UFs


def mapa(F: dict, fig: Callable[[str], str]) -> str:
    h = "<h3>O mapa</h3>" + fig("fiscais_mapa_navegavel")
    ufs = sorted(F["por_uf"], key=lambda u: -(u.get("locais_alta") or 0))[:3]
    h += p(
        "Cada ponto é um local de votação. O nível alta se concentra em "
        + lista(
            [
                f"{NOME_UF.get(u['uf'], u['uf'])} ({inteiro(u.get('locais_alta'))} locais)"
                for u in ufs
            ]
        )
        + ". Aproxime para ver a malha dos municípios; clique num ponto para o endereço e os links de rota.",
        "verificado",
    )
    h += fig("fiscais_mapa_uf")
    return h


def por_uf(F: dict, fig: Callable[[str], str]) -> str:
    h = "<h3>Por UF</h3>" + fig("fiscais_por_uf")
    ufs = sorted(F["por_uf"], key=lambda u: -u["secoes"])
    tx = [
        (u, 100 * u["secoes"] / u["secoes_universo"])
        for u in ufs
        if u.get("secoes_universo")
    ]
    maior = max(tx, key=lambda x: x[1]) if tx else None
    frase = (
        f"Em número absoluto lidera {NOME_UF.get(ufs[0]['uf'], ufs[0]['uf'])}, com {inteiro(ufs[0]['secoes'])} "
        "seções sinalizadas, o que acompanha o tamanho do eleitorado."
    )
    if maior:
        frase += (
            f" Em proporção das seções da própria UF, a maior taxa é a de {NOME_UF.get(maior[0]['uf'], maior[0]['uf'])}: "
            f"{pc(maior[1])}."
        )
    return h + p(frase, "verificado")


def territorio(F: dict, fig: Callable[[str], str], d_aviso) -> str:
    h = "<h3>Contexto do território</h3>"
    if not tem_risco(F):
        d_aviso(
            "fiscais.json sem secoes[].risco: capítulo 13 sem o contexto do território"
        )
        return h + p(
            "A camada de contexto do território (terra indígena, quilombo, favela, unidade prisional, homicídios, "
            "fronteira, garimpo e acesso) ainda não foi integrada a esta versão da lista.",
            "verificado",
        )
    h += fig("fiscais_risco")
    secs = [s for s in F["secoes"] if isinstance(s.get("risco"), dict)]
    alto = [s for s in secs if s["risco"].get("nivel_risco_fiscal") == "alto"]
    h += p(
        f"{inteiro(len(secs))} das {inteiro(len(F['secoes']))} seções sinalizadas têm base de risco; "
        f"{inteiro(len(alto))} ficam em território de risco alto para o fiscal.",
        "verificado",
    )
    regra = F["meta"].get("risco_regra") or {}
    if regra.get("cortes"):
        pts_ = ", ".join(
            f"{escape(k)} {v}" for k, v in (regra.get("pontos") or {}).items()
        )
        h += p(
            f"O nível de risco soma pontos por camada ({pts_}); risco alto com {regra['cortes'].get('alto')} pontos ou "
            f"mais, médio com {regra['cortes'].get('medio')}. A regra é escolha da casa, não medição.",
            "juizo",
        )
    h += caixa(
        "io",
        "Risco não é indício",
        "<p>Risco é contexto para o fiscal se proteger e planejar a ida: transporte, horário, acompanhante. "
        "Não aumenta a pontuação de nenhuma seção. Onde a base não cobre o município, o campo é desconhecido, "
        "não zero. Validar com a PM e o TRE local antes de mandar alguém.</p>",
    )
    return h


# ------------------------------------------------------------------ municípios e listas


def municipios(F: dict, fig: Callable[[str], str]) -> str:
    h = "<h3>Os municípios</h3>" + fig("fiscais_municipios")
    m = sorted(F["por_municipio"], key=lambda m: m.get("posicao_pontuacao") or 10**6)[
        :3
    ]
    h += p(
        "Pela pontuação somada, os três primeiros são "
        + lista(
            [
                f"{nome_bonito(x['municipio'])} ({x['uf']}, {inteiro(x['secoes'])} seções em {inteiro(x.get('locais'))} locais)"
                for x in m
            ]
        )
        + ". Capital grande sobe por volume; a tabela ordena também por seções de nível alta.",
        "verificado",
    )
    return h


def listas_pl(F: dict, fig: Callable[[str], str]) -> str:
    P = F["prioridade_pl"]
    pf, vl = P["protege_flavio"], P["vigia_lula"]
    h = "<h3>Duas listas do PL</h3>" + fig("fiscais_protege_vigia")
    h += p(
        f"Proteger: {inteiro(pf.get('secoes'))} seções sinalizadas em {inteiro(pf.get('municipios_elegiveis'))} "
        f"municípios onde a margem ficou em até 5 pontos ({aptos(pf.get('aptos'))}). Vigiar: "
        f"{inteiro(vl.get('secoes'))} seções com Lula acima do resto da zona, que somam "
        f"{inteiro(vl.get('excesso_votos_lula'))} votos acima do que a zona sugeriria.",
        "inferencia",
    )
    h += nota(
        "juizo",
        escape(P.get("leitura") or "")
        + " A ordem das duas listas é escolha da casa para alocar gente, não medida de irregularidade.",
    )
    return h


def amostra(F: dict, fig: Callable[[str], str]) -> str:
    h = "<h3>As seções de nível alta</h3>" + fig("fiscais_secoes_amostra")
    return h + p(
        "Cada cartão traz os números da seção, a distância para o resto da zona, os critérios, a explicação provável "
        "pelo cadastro e o que o fiscal confere ali. O endereço e os links de rota estão no pé do cartão.",
        "verificado",
    )


def locais(F: dict, fig: Callable[[str], str]) -> str:
    h = "<h3>Todos os locais com três ou mais seções</h3>" + fig("fiscais_locais")
    c = cobertura_local(F)
    h += p(
        frase_uso(F)
        + f" Esses locais somam {aptos(c['aptos'])}, porque o fiscal enxerga o local inteiro.",
        "inferencia",
    )
    h += caixa(
        "analogy",
        "Como usar o CSV",
        "<p>Abra no Excel, filtre pela sua UF e pelo município, ordene pelo nível e pela pontuação, e distribua um "
        "fiscal por linha da lista de locais. A coluna de seções diz em quais mesas o fiscal passa primeiro; a de "
        "critérios diz o que ele confere. Leve o endereço e o link do mapa no celular.</p>",
    )
    return h


def sem_arquivo(F: dict) -> str:
    sa, zc = F.get("sem_arquivo") or [], F.get("zonas_congeladas") or []
    h = "<h3>Seções sem arquivo e zonas congeladas</h3>"
    ex = lista(
        [
            f"{nome_bonito(s['municipio'])} ({s['uf']}), zona {s['zona']}, seção {s['secao']}"
            for s in sa[:5]
        ]
    )
    h += p(
        f"{inteiro(len(sa))} seções principais ativas não têm boletim publicado pelo TSE"
        + (f", entre elas {ex}" if ex else "")
        + f". {inteiro(len(zc))} arquivos de zona ficaram parados incompletos por seis horas ou mais"
        + (
            ": "
            + lista(
                [
                    f"{nome_bonito(z['municipio'])} ({z['uf']}), zona {z['zona']}, {num(z.get('horas_parada'), 1)} horas"
                    for z in zc[:5]
                ]
            )
            if zc
            else ""
        )
        + ". Atraso de publicação não é irregularidade; o fiscal pede o arquivo ao TRE.",
        "verificado",
    )
    return h


def tse(F: dict) -> str:
    itens = [
        "o boletim de urna de toda seção no mesmo dia, sem lacuna, com o motivo de cada arquivo que falta;",
        "o log de cada urna e o registro de troca, com o horário, ligados à seção no portal;",
        "a coordenada conferida de cada local de votação, para a sociedade saber onde fica a mesa;",
        "o horário de encerramento e de transmissão por seção, num arquivo só, em vez de espalhado por 500 mil arquivos.",
    ]
    return "<h3>O que o TSE poderia publicar</h3>" + nota(
        "juizo",
        "<ul>" + "".join(f"<li>{i}</li>" for i in itens) + "</ul>",
        "Com isso, metade desta lista se resolveria sem fiscal.",
    )


def achados(F: dict) -> str:
    A = F.get("achados") or {}
    tipo = {
        "verificado": "verificado",
        "inferido": "inferencia",
        "hipotese": "hipotese",
        "juizo": "juizo",
    }
    h = ""
    for k, sel in tipo.items():
        for x in A.get(k, []):
            h += p(escape(x), sel)
    for x in A.get("contrario", []):
        h += nota("contrario", escape(x))
    return h


def fontes(F: dict) -> str:
    M = F["meta"]
    lis = "".join(
        f"<li><code>{escape(f.get('caminho', ''))}</code>: {escape(f.get('descricao', ''))}"
        + (
            f'<br><span class="hash">SHA-256 {escape(f["sha256"])}</span>'
            if f.get("sha256")
            else ""
        )
        + "</li>"
        for f in M.get("fontes", [])
    )
    risco = "".join(
        f"<li>{fonte_risco_html(f, len(F['secoes']))}</li>"
        for f in M.get("fontes_risco", [])
    )
    lei = "".join(
        f"<li>{escape(b.get('norma', ''))}, {escape(b.get('dispositivo', ''))}: {escape(b.get('conteudo', ''))}</li>"
        for b in M.get("base_legal", [])
    )
    h = '<h3>Fontes do capítulo</h3><ul class="fontes">' + lis + "</ul>"
    if risco:
        h += (
            '<p>Bases de contexto do território:</p><ul class="fontes">'
            + risco
            + "</ul>"
        )
    if lei:
        h += "<p>Base legal da fiscalização:</p><ul>" + lei + "</ul>"
    h += (
        "<p>Reprodução: <code>python3 scripts/apuracao-2026-fiscais.py</code> grava <code>fiscais.json</code> e os "
        "três exportáveis; contrato em <code>analysis/apuracao_2026/CONTRATO_FISCAIS.md</code>.</p>"
    )
    return h


def capitulo(F: dict, fig: Callable[[str], str], d_aviso) -> str:
    h = abertura(F)
    h += como_ler(F)
    h += criterios(F, fig)
    h += contrario(F)
    h += mapa(F, fig)
    h += por_uf(F, fig)
    h += territorio(F, fig, d_aviso)
    h += municipios(F, fig)
    h += listas_pl(F, fig)
    h += amostra(F, fig)
    h += locais(F, fig)
    h += sem_arquivo(F)
    h += achados(F)
    h += tse(F)
    h += fontes(F)
    lim = [escape(x) for x in F.get("limites", [])] + [
        escape(F["rotulos"].get("atipico", "")),
        escape(F["rotulos"].get("prioridade", "")),
        escape(F["rotulos"].get("resolve", "")),
    ]
    h += limites(
        lim,
        "Os limites do capítulo 12 (boletins por seção, mistura gaussiana) valem para os critérios e e j.",
    )
    return h


__all__ = ["CHAVES", "H3", "capitulo", "criterios_txt", "frase_uso"]
