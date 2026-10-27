"""Bloco "Boca de urna e pressão sobre o eleitor" do capítulo de hipóteses (H4).

Interface: ``bloco(d) -> str``, com ``d`` o leitor de JSONs do dossiê (``Dados``) ou
um dicionário com a chave ``angulo_boca_urna.json``. Sem o JSON, devolve ``""``.
Cada número vem de ``angulo_boca_urna.json`` (``scripts/apuracao-2t-2026-angulo-boca-urna.py``);
nada é digitado aqui. Selos: verificado para o que está no documento arquivado,
inferência para contagem derivada, relato para imprensa, juízo onde a casa opina.
Sem travessão; nunca "fraude".
"""

from __future__ import annotations

import re
from html import escape

from apuracao_2026.pagina_comum import caixa, inteiro, nota, num, p, tabela

from .pagina_texto_noticias import limpa

ARQ = "angulo_boca_urna.json"
ROTULO_TIPO = {
    "boca_de_urna": "boca de urna",
    "mesario_conduta": "conduta de mesário",
    "transporte_irregular": "transporte irregular",
    "fila_longa": "fila longa",
    "urna_trocada": "urna trocada",
    "biometria_falhou": "biometria falhou",
    "votou_sem_biometria": "votou sem biometria",
    "local_mudou": "local mudou",
    "secao_fechou_cedo": "seção fechou cedo",
    "secao_fechou_tarde": "seção fechou tarde",
    "outro": "outro",
}
ROTULO_SUBTEMA = {
    "boca_de_urna": "boca de urna",
    "sigilo_ou_venda_do_voto": "sigilo ou venda do voto",
    "transporte": "transporte",
    "violencia": "violência",
    "outro": "outro",
}
PARTIDOS = re.compile(
    r"\b(PL|PT|PSOL|PSD|PP|MDB|União|Novo|Republicanos|PSDB|PDT|PSB)\b"
)
ROTULO_CLASSE = {
    "registro_oficial": "registro oficial",
    "relato_imprensa": "relato de imprensa",
    "relato_anonimo": "relato anônimo",
}


def _maiuscula(s: str) -> str:
    return s[:1].upper() + s[1:]


def _pct(x: float | None) -> str:
    return "" if x is None else f"{num(x, 1)}%"


def _balancos(B: list[dict]) -> str:
    linhas = []
    for b in B:
        boca = (
            f"{_pct(b['boca_de_urna_pct'])} (cerca de {inteiro(b['boca_de_urna_n_derivado'])}, "
            "conta derivada)"
            if b.get("boca_de_urna_pct") is not None
            else "sem divisão por tipo"
        )
        linhas.append(
            [
                escape(b["corte"]),
                inteiro(b["ocorrencias"]),
                inteiro(b["flagrantes"]),
                inteiro(b["conduzidos"]) if b.get("conduzidos") is not None else "",
                boca,
                f'<a href="{escape(b["url"])}" rel="noopener">{escape(b["publicado"])}</a>',
            ]
        )
    return tabela(
        [
            "Corte",
            "Ocorrências",
            "Flagrantes",
            "Conduzidos",
            "Boca de urna",
            "Publicado",
        ],
        linhas,
        "Balanços do Centro Integrado de Comando e Controle Nacional (MJSP). O MJSP publica o "
        "percentual; a contagem absoluta de boca de urna é percentual vezes total, arredondada, "
        "e fica rotulada como derivada. Páginas arquivadas com SHA-256 em noticias_fontes/.",
    )


def _oficial(D: dict) -> str:
    B = D["balancos_mjsp"]
    final = next((b for b in B if b["id"] == "mjsp_final"), None)
    prelim = next((b for b in B if b["id"] == "mjsp_19h"), None)
    if not final:
        return ""
    h = p(
        f"O balanço do MJSP para o 2º turno inteiro, publicado em {escape(final['publicado'])}, "
        f"soma {inteiro(final['ocorrencias'])} ocorrências, {inteiro(final['flagrantes'])} autos de "
        f"prisão em flagrante, {inteiro(final['termos_circunstanciados'])} termos circunstanciados e "
        f"{inteiro(final['conduzidos'])} pessoas conduzidas. O delito mais registrado foi violar ou "
        f"tentar violar o sigilo do voto ({_pct(final.get('sigilo_do_voto_pct'))}); a boca de urna vem "
        f"em segundo, com {_pct(final['boca_de_urna_pct'])}, seguida da propaganda irregular "
        f"({_pct(final.get('propaganda_irregular_pct'))}). Apreensões: {escape(final['apreensoes'])}.",
        "verificado",
    )
    if prelim:
        h += p(
            f"{_pct(final['boca_de_urna_pct'])} de {inteiro(final['ocorrencias'])} dá cerca de "
            f"{inteiro(final['boca_de_urna_n_derivado'])} ocorrências de boca de urna no país; o "
            f"preliminar das 19h de 25/10 ({inteiro(prelim['ocorrencias'])} ocorrências, "
            f"{_pct(prelim['boca_de_urna_pct'])}) dava cerca de "
            f"{inteiro(prelim['boca_de_urna_n_derivado'])}. O MJSP não publicou a contagem absoluta "
            "nem a divisão por UF ou por candidatura beneficiada; o número é ordem de grandeza, não "
            "lista de casos.",
            "inferencia",
        )
    return h


def _caso(c: dict) -> str:
    """Um caso nominal: registro oficial sai em nome de quem registrou; o veículo é só o meio."""
    if c["classe"] == "registro_oficial" and c.get("quem_disse"):
        quem = f"{escape(c['quem_disse'])}, pelo veículo {escape(c['veiculo'])}"
        meta = escape(ROTULO_CLASSE[c["classe"]])
    else:
        quem = escape(c["veiculo"])
        meta = (
            f"{escape(ROTULO_CLASSE[c['classe']])}; "
            f"{escape(c['quem_disse'] or 'sem fonte nomeada')}"
        )
    return (
        f"<li>{escape(c['quando'][11:16])}, {quem}: {escape(limpa(c['resumo']))} "
        f'<span class="nt-meta">({meta}) '
        f'<a href="{escape(c["url"])}" rel="noopener">fonte</a></span></li>'
    )


def _nominais(oc: dict) -> str:
    casos = oc.get("boca_de_urna_nominais") or []
    if not casos:
        return ""
    oficiais = sum(c["classe"] == "registro_oficial" for c in casos)
    partidos = sorted(
        {
            m
            for c in casos
            for m in PARTIDOS.findall(f"{c.get('titulo') or ''} {c['resumo']}")
        }
    )
    lado = (
        f" Os casos com partido citado envolvem só um lado ({escape(partidos[0])}): isso descreve o que a "
        "imprensa arquivada nomeou, não a distribuição das ocorrências, que o MJSP não divide por candidatura."
        if len(partidos) == 1
        else ""
    )
    return (
        p(
            f"Casos nominais de boca de urna no acervo do dia: {len(casos)}, "
            f"{inteiro(oficiais)} com registro oficial e {inteiro(len(casos) - oficiais)} por relato de "
            f"imprensa, listados abaixo com a fonte.{lado} O acervo é o que a casa arquivou na noite; "
            "ausência no acervo não é ausência de ocorrência.",
            "relato",
        )
        + f'<ul class="nt-lista">{"".join(_caso(c) for c in casos)}</ul>'
    )


def _classes(oc: dict) -> str:
    c = oc["por_classe"]
    partes = [f"{inteiro(n)} {ROTULO_CLASSE[k]}" for k, n in c.items() if n]
    s = oc["por_subtema"]
    sub = ", ".join(
        f"{escape(ROTULO_SUBTEMA.get(k) or k.replace('_', ' '))} {inteiro(n)}"
        for k, n in s.items()
    )
    return p(
        f"Dos {inteiro(oc['n'])} itens do acervo do dia que tratam de ocorrência, prisão, apreensão "
        f"ou pressão sobre o eleitor, {', '.join(partes)}. Por assunto: {sub}. Registro oficial é o "
        "que polícia, Justiça Eleitoral ou MJSP disseram em nome próprio; relato de imprensa inclui "
        "partido ou campanha falando por um veículo. A regra de classificação está no JSON.",
        "verificado",
    )


def _canal(R: dict) -> str:
    if "erro" in R:
        return p(
            f"O canal de relatos do Politize-se não respondeu à consulta de {escape(R['consultado_em'])} "
            f"({escape(R['erro'])}); as contagens ficam para a próxima rodada.",
            "verificado",
        )
    tipos = ", ".join(
        f"{escape(ROTULO_TIPO[k])} {inteiro(v)}" for k, v in R["por_tipo"].items() if v
    )
    ufs = ", ".join(f"{escape(k)} {inteiro(v)}" for k, v in R["por_uf"].items())
    st = R["por_status"]
    h = p(
        f"O canal de relatos por seção do Politize-se recebeu, até a consulta de "
        f"{escape(R['consultado_em'])}, {inteiro(R['total'])} relatos, todos do 2º turno: "
        f"{inteiro(st['novo'])} novos, {inteiro(st['lido'])} lidos e {inteiro(st['descartado'])} "
        f"descartados na moderação. Por tipo: {tipos or 'nenhum'}. Por UF: {ufs or 'nenhuma'}. "
        f"Relatos de pressão sobre o eleitor (boca de urna, conduta de mesário, transporte irregular): "
        f"{inteiro(R['pressao_sobre_o_eleitor'])}. Quem enviou disse ter presenciado em "
        f"{inteiro(R['presenciou']['sim'])} e soube por outra pessoa em "
        f"{inteiro(R['presenciou']['nao'])}; {inteiro(R['secao_no_cadastro']['nao'])} apontam seção "
        "que não existe no cadastro do 1º turno.",
        "verificado",
    )
    h += p(
        f"{inteiro(R['total'])} relatos não medem o país. O canal abriu depois do dia da votação, só é visível a quem "
        "abre a ficha da própria seção, e a contagem é de declarações, não de fatos conferidos. "
        "Texto, contato e hora exata ficam no banco; nada disso é publicado. O que o canal prova é "
        "que o caminho existe e grava sem apagar.",
        "juizo",
    )
    return h


def _lei(L: dict) -> str:
    lei, res = L.get("lei_9504", {}), L.get("res_23751", {})
    disp_lei = {d["dispositivo"]: d for d in lei.get("dispositivos", [])}
    disp_res = {d["dispositivo"]: d for d in res.get("dispositivos", [])}
    ok_lei = all(d["conferido_no_arquivo"] for d in disp_lei.values())
    ok_res = all(d["conferido_no_arquivo"] for d in disp_res.values())
    h = p(
        "A Lei 9.504/1997 faz da boca de urna crime do dia da eleição: o art. 39, § 5º, II, pune "
        "a arregimentação de eleitor e a propaganda de boca de urna com detenção de seis meses a um "
        "ano, alternativa de prestação de serviços e multa; o inciso I alcança alto-falante, comício "
        "e carreata, e o III a divulgação de propaganda. O art. 39-A permite ao eleitor a "
        "manifestação individual e silenciosa, por bandeira, broche, dístico e adesivo, e veda até o "
        "fim da votação a aglomeração com vestuário padronizado. "
        + (
            "Texto conferido na cópia arquivada do Planalto."
            if ok_lei
            else "Trecho não conferido no arquivo nesta rodada."
        ),
        "verificado",
    )
    h += p(
        "A Resolução TSE 23.751/2026 (atos gerais, DJE de 03/03/2026) diz onde isso vira "
        "documento dentro da seção: os mesários lavram a Ata da Mesa Receptora anotando, durante os "
        "trabalhos, todas as ocorrências (art. 128, V); o presidente mantém a ordem com força pública, "
        "comunica ao juiz eleitoral o que dele depender e consigna na ata as impugnações de fiscais e "
        "de qualquer eleitor (art. 126, VIII a X); fiscais podem formular protestos e impugnações "
        "(art. 176) e usam crachá só com nome e sigla (art. 177); a ata final registra as ocorrências "
        "significativas (art. 161). "
        + (
            "Artigos lidos no PDF do DJE arquivado."
            if ok_res
            else "Algum trecho não foi conferido no arquivo nesta rodada."
        ),
        "verificado",
    )
    return h


def _caminho(C: list[dict]) -> str:
    itens = "".join(
        f"<li><b>{escape(c['passo'])}</b> ({escape(c['quem'])}): {escape(c['como'])} "
        f"<em>Vira:</em> {escape(c['vira'])}</li>"
        for c in C
    )
    return caixa(
        "io",
        "Como um relato vira documento",
        f"<ol>{itens}</ol>"
        "<p>Os endereços e prazos das ouvidorias dos TREs não foram conferidos nesta rodada.</p>",
    )


def bloco(d) -> str:
    D = d.get(ARQ)
    if not D:
        return ""
    h = "<h4>Boca de urna e pressão sobre o eleitor</h4>"
    h += p(
        _maiuscula(escape(D["o_que_a_totalizacao_nao_mede"]))
        + ". O que existe é documento: o registro das forças de segurança, o que a imprensa relatou "
        "com nome, e o que chegou ao canal de relatos da casa. As três camadas estão abaixo, com "
        "a fonte de cada uma.",
        "verificado",
    )
    h += _oficial(D) + _balancos(D["balancos_mjsp"])
    h += _classes(D["ocorrencias"]) + _nominais(D["ocorrencias"])
    h += _canal(D["relatos"])
    h += _lei(D["base_legal"]) + _caminho(D["caminho_documental"])
    h += nota(
        "juizo",
        "Boca de urna existe em toda eleição e o balanço do MJSP a coloca em segundo lugar entre as "
        "ocorrências do dia. Nada no acervo liga essas ocorrências a seção, município ou candidatura, "
        "e a totalização não tem onde registrá-las. Quem quiser medir o efeito precisa das atas das "
        "seções e dos boletins de ocorrência com a seção anotada; sem isso, o que a casa publica é a "
        "contagem oficial, os casos nominais com fonte e o caminho para que o próximo relato vire "
        "documento. Relato pede explicação, não prova irregularidade.",
    )
    return h
