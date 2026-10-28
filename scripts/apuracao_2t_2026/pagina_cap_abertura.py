"""Capítulo 01 do dossiê do 2º turno: o resultado e a frase da noite.

Todos os números saem de `presidente.json`; a frase da noite junta, quando os
arquivos existem, `projecao_noite.json`, `secoes.json`, `linha_do_tempo.json`,
`paralela.json` e `pesquisas_vs_urna.json`. Arquivo ausente apaga só a oração.
"""

from __future__ import annotations

from apuracao_2026.pagina_comum import cartao, limites, nota, p

from .pagina_comum import Capitulo, Dados, cabeca, caminho, inteiro, milhoes, num
from .pagina_fig_noite_b import fig_barras, fig_mapa_vencedor


def _pp(v: float, casas: int = 2) -> str:
    return ("+" if v > 0 else "−" if v < 0 else "") + num(abs(v), casas)


def frase_noite(d: Dados) -> str:
    """A frase de um parágrafo sobre a noite, gerada dos JSONs."""
    partes = []
    J = d.get("projecao_noite.json")
    if J and J.get("primeiro_ponto_com_projecao"):
        p0 = J["primeiro_ponto_com_projecao"]
        lider = J.get("lider_projetado_em_todos_os_pontos") or []
        todos = (
            f", e manteve Lula à frente nos {J['pontos_com_projecao']} pontos da noite"
            if lider == ["lula"]
            else ""
        )
        partes.append(
            f"A projeção da casa apontou Lula desde o primeiro ponto, às {p0['hhmm']}, com "
            f"{num(p0['pst'], 2)}% das seções{todos}"
        )
    S = d.get("secoes.json")
    enc = caminho(S, "agregados.brasil.encerramento") if S else None
    if enc:
        partes.append(
            f"o STF prorrogou a votação até as 19h e quase nenhuma urna ficou aberta: "
            f"{'nos boletins de' if S.get('fonte') == 'completo' else 'na amostra de'} "
            f"{inteiro(enc['n'])} seções, o encerramento mediano foi às {enc['p50_2t']} e "
            f"{num(enc['pct_apos_1900_2t'], 2)}% fecharam depois das 19h"
        )
    L = d.get("linha_do_tempo.json")
    sil = caminho(L, "pausas.silencio_geral") if L else None
    if sil:
        partes.append(
            f"o TSE ficou {num(sil['minutos'], 1)} minutos sem gerar arquivo de nenhum tipo"
        )
    Pa = d.get("paralela.json")
    if Pa:
        rec, conf = Pa["recebidos"], Pa.get("conferencia", {})
        iguais = conf.get("igual", 0)
        div = sum(v for k, v in conf.items() if k != "igual")
        partes.append(
            f"a totalização paralela conferiu {inteiro(iguais)} boletins de urna em {rec['ufs']} UFs "
            + (
                "sem nenhuma divergência"
                if div == 0
                else f"com {inteiro(div)} fora do igual"
            )
        )
    Pv = d.get("pesquisas_vs_urna.json")
    if Pv:
        erro = caminho(Pv, "resumo.erro_media_simples.erro_f_menos_l")
        ma = caminho(Pv, "centrais.media_arvor.erro_f_menos_l")
        n = caminho(Pv, "resumo.n_casas")
        pos = caminho(Pv, "resumo.publicado_validos_do_total.positivos")
        if erro is not None:
            frase = f"a urna ficou {_pp(erro)} pontos, na diferença Flávio menos Lula, do que as pesquisas mediam dois dias antes"
            if pos is not None and n:
                frase += f", com o mesmo sinal nas {pos} de {n} casas"
            if ma is not None:
                frase += f" e {_pp(ma)} da Média Arvor, que mediu certo até o último campo: o que mudou no domingo é o objeto deste dossiê"
            partes.append(frase)
    if not partes:
        return ""
    texto = (
        "; ".join(partes[:-1]) + ("; e " if len(partes) > 1 else "") + partes[-1] + "."
    )
    return f'<p class="frase-noite">{texto[0].upper() + texto[1:]}</p>'


def cards(P: dict) -> str:
    n = P["nacional"]
    bn = n["brancos"] + n["nulos"]
    return (
        '<div class="finding-grid">'
        + cartao(
            f"{num(n['pst'], 2)}%",
            f"{inteiro(n['secoes'])} de {inteiro(n['secoes_total'])} seções totalizadas",
        )
        + cartao(
            f"{num(n['pct_comparecimento'], 2)}%",
            f"comparecimento, {milhoes(n['comparecimento'])} de eleitores",
        )
        + cartao(
            f"{num(n['pct_abstencao'], 2)}%",
            f"abstenção, {milhoes(n['abstencao'])} de eleitores",
        )
        + cartao(
            f"{num(n['pct_brancos'] + n['pct_nulos'], 2)}%",
            f"brancos e nulos sobre o comparecimento, {milhoes(bn)}",
        )
        + "</div>"
    )


def bloco_norte(P: dict) -> str:
    norte = next((r for r in P["regioes"] if r["sigla"] == "N"), None)
    if not norte:
        return ""
    lider = "Lula" if norte["margem_lula_votos"] > 0 else "Flávio"
    return p(
        f"O Norte terminou em {num(norte['pct_lula'], 2)}% a {num(norte['pct_flavio'], 2)}%: "
        f"{lider} ficou à frente por {inteiro(abs(norte['margem_lula_votos']))} votos em "
        f"{inteiro(norte['validos'])} válidos, com {num(norte['pst'], 2)}% das seções da região. "
        + (
            "Arredondado a duas casas, é empate; com todas as seções totalizadas, a diferença é a final."
            if norte["secoes"] >= norte["secoes_total"]
            else "Arredondado a duas casas, é empate; a diferença absoluta ainda pode mudar com as seções que faltam."
        ),
        "verificado",
    )


def bloco_regioes(P: dict) -> str:
    nomes = {"NE": "Nordeste", "SE": "Sudeste", "S": "Sul", "CO": "Centro-Oeste"}
    rg = {r["sigla"]: r for r in P["regioes"]}
    ne = rg.get("NE")
    pedacos = []
    if ne:
        pedacos.append(
            f"O Nordeste deu a Lula {milhoes(ne['margem_lula_votos'])} de votos de vantagem "
            f"({num(ne['pct_lula'], 2)}% dos válidos)"
        )
    contra = [
        f"{milhoes(-rg[s]['margem_lula_votos'])} no {nomes[s]}"
        for s in ("S", "SE", "CO")
        if s in rg and rg[s]["margem_lula_votos"] < 0
    ]
    if contra:
        pedacos.append(
            "Flávio abriu "
            + (
                ", ".join(contra[:-1]) + " e " + contra[-1]
                if len(contra) > 1
                else contra[0]
            )
        )
    if not pedacos:
        return ""
    return p(
        ". ".join(pedacos)
        + ". A soma das vantagens de Flávio no Centro-Sul não cobriu a do Nordeste.",
        "verificado",
    )


def bloco_pesquisas(d: Dados) -> str:
    Pv = d.get("pesquisas_vs_urna.json")
    if not Pv:
        return ""
    ma = caminho(Pv, "centrais.media_arvor")
    pa = caminho(Pv, "centrais.projecao_arvor")
    erro = caminho(Pv, "resumo.erro_media_simples.erro_f_menos_l")
    acert = caminho(Pv, "resumo.casas_que_acertaram_vencedor") or []
    if not ma or erro is None:
        return ""
    texto = (
        f"As pesquisas e a régua de renda da casa mediram o eleitorado até o último campo, em 23 e 24/10. A urna ficou "
        f"{_pp(erro)} pontos, na diferença Flávio menos Lula, do que as {caminho(Pv, 'resumo.n_casas')} casas mediam dois dias antes, "
        "com o mesmo sinal em todas. Esse deslocamento é a medida do que mudou entre a última pesquisa e o domingo, e é isso que o dossiê investiga."
    )
    texto += (
        f" Os números ficam publicados: a Média Arvor da véspera dava Flávio {num(ma['validos']['flavio'], 2)}% × Lula "
        f"{num(ma['validos']['lula'], 2)}%, distância de {_pp(ma['erro_f_menos_l'])} pontos da urna"
    )
    if pa:
        texto += (
            f"; a Projeção Arvor ({num(pa['validos']['flavio'], 2)}% × {num(pa['validos']['lula'], 2)}%), "
            f"{_pp(pa['erro_f_menos_l'])}"
        )
    texto += "."
    if acert:
        texto += f" Só {' e '.join(acert)} indicaram Lula à frente nos válidos."
    rep = caminho(Pv, "resumo.reponderado")
    pub = caminho(Pv, "resumo.publicado_mesmas_casas_reponderadas")
    if rep and pub:
        texto += (
            f" Nas {rep['n']} casas com voto por renda, a distância média foi de {_pp(pub['media'])} pontos pelo publicado e "
            f"{_pp(rep['media'])} com a régua da PNAD: é o que se espera quando a mudança de última hora vem de quem comparece, "
            "não de quem foi entrevistado."
        )
    texto += ' O capítulo <a href="#pesquisas">Pesquisas × urna</a> abre a conta casa por casa e o que ainda falta explicar.'
    return nota("juizo", texto, "O que mudou no domingo.")


def render(d: Dados, cap: Capitulo) -> str:
    P = d.get("presidente.json")
    n = P["nacional"]
    h = cabeca(
        cap,
        f"Lula, {num(n['pct_lula'], 2)}%.<br><em>Flávio, {num(n['pct_flavio'], 2)}%.</em>",
        f"{milhoes(n['margem_lula_votos'])} de votos de diferença ({num(n['margem_lula_pp'], 2)} pontos dos válidos), "
        f"com {num(n['pst'], 2)}% das seções.",
    )
    h += frase_noite(d)
    h += '<p>A leitura territorial e a trilha de auditoria estão no relatório <a href="analise_realidade_eleicao.html">A geografia do voto e o que pede explicação</a>: municípios, zonas das capitais, renda, desenvolvimento e evidências entre turnos.</p>'
    h += cards(P)
    h += bloco_regioes(P) + fig_barras(P)
    h += bloco_norte(P)
    h += fig_mapa_vencedor(P)
    h += bloco_pesquisas(d)
    h += limites(
        [
            f"Placar da versão nacional gerada às {n['gerado_brt'][11:19]} de 25/10, com {num(n['pst'], 2)}% das seções"
            + (
                f" ({inteiro(n['secoes'])} de {inteiro(n['secoes_total'])}), todas totalizadas."
                if n["secoes"] >= n["secoes_total"]
                else f"; faltavam {inteiro(n['secoes_total'] - n['secoes'])} seções."
            ),
            (
                "Abstenção sobre o eleitorado de todas as seções; brancos e nulos sobre o comparecimento."
                if n["secoes"] >= n["secoes_total"]
                else "Abstenção sobre o eleitorado das seções já totalizadas; brancos e nulos sobre o comparecimento."
            ),
            "A frase da noite junta cinco arquivos com regras próprias; cada capítulo traz a conta e o limite de cada parte.",
            "Atipicidade pede explicação, não prova irregularidade.",
        ]
    )
    return h
