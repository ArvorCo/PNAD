"""Posts da thread das mudanças de local: modelos com campos ``{chave}``, nunca algarismo
solto, montagem e verificação (faixa de caracteres, travessão, hashtag, emoji, links).
"""

from __future__ import annotations

import re

from apuracao_2026.thread_base import digitos_soltos, problemas_de_texto

from . import figuras as G
from .base import URL_LAUDO, URL_POLITIZE, valores

MIN_CHARS, MAX_CHARS = 1000, 2000
CAMPOS_TEXTO = ("tag", "titulo", "metrica", "metrica_rot", "fonte")
PALAVRA_VETADA = "fraude"
LINK = re.compile(r"https?://\S+")

POSTS: list[dict] = [
    {
        "tag": "O problema",
        "tom": "ouro",
        "titulo": "Quatro números oficiais, nenhum igual ao outro",
        "metrica": "{n_mr}",
        "metrica_rot": "seções com mudança real de prédio, pelos dois arquivos do TSE",
        "fig": G.fig_numeros,
        "fonte": "mudancas.json; cadastros de locais do TSE nos dois turnos; painel do TSE",
        "link": None,
        "texto": [
            "A manchete que circulou: mais de {manchete_mil} seções mudaram de endereço entre os turnos. Depois dela vieram quatro números oficiais, e nenhum bate com outro.",
            "{n_tse} seções, segundo o TSE em {d_tse}. {n_col} seções e {e_col} eleitores, no relatório anexo à petição da coligação de Lula em {d_col}. {n_con} seções e {e_con} eleitores, numa consulta ao sistema do TSE em {d_con}. {n_pai} seções e {e_pai} eleitores, no painel oficial do TSE em {d_pai}, às {h_pai}: cerca de um quarto do número de {d_tse}.",
            "Fizemos a conta pelos dois arquivos do TSE, o de locais do 1º turno e o do 2º, seção por seção. {n_mr} seções e {e_mr} eleitores trocam de prédio de verdade, em {n_mun} municípios. Dessas, {n_a} voltam ao prédio original depois de um 1º turno em local temporário. Voltar para casa não é ser mandado para um endereço novo.",
            "Se a pergunta é quantas seções seguem fora do prédio original no 2º turno, a resposta é {n_fora}, com {e_fora} de eleitores. O total de eleitores fica a {dif_col} do da coligação. O de seções difere: {n_col} contra {n_fora}.",
            "A distância típica é pequena: mediana de {med} m, perto dos {viz} m que separam um prédio de votação do mais próximo. Mas {pct1km} das novas realocações passam de {um_km}. É a padaria que mudou de esquina sem aviso: quase todo freguês anda uns passos a mais, e alguns atravessam o bairro.",
            "O clima explica pouco. De {janela_clima}, {chuva_mud} dos locais que mudaram tiveram dia com mais de {mm20} de chuva, contra {chuva_ctl} do grupo de controle. E só {n_com_motivo} dos {n_pares} pares de locais têm motivo em nota de TRE que lemos.",
            "A pergunta certa não é quantas seções mudaram. É por que cada uma mudou e para onde. Isso o TSE não publica por seção.",
        ],
    },
    {
        "tag": "A ferramenta",
        "tom": "verde",
        "titulo": "A sua seção mudou? Confira em {tempo}",
        "metrica": "{med} m",
        "metrica_rot": "mediana entre o endereço antigo e o novo, em linha reta",
        "fig": G.fig_alerta,
        "fonte": "mudancas.json; Politize sua vizinhança",
        "link": URL_POLITIZE,
        "texto": [
            "Sua seção mudou de endereço para o 2º turno? Em {dia_2t}, em alguns casos, você vota em outro prédio. Conferir leva {tempo}.",
            "O Politize sua vizinhança agora avisa. Digite UF, zona e seção. Se a seção mudou, o alerta mostra onde você votou no 1º turno, onde vota em {dia_2t}, a distância em linha reta e um botão que abre o novo endereço no Google Maps. Tem também o link para conferir no e-Título.",
            "A lista do aplicativo é a união de duas fontes do TSE: o arquivo de locais de votação e o painel de seções alteradas. Juntas, somam {pol_secoes} seções e {pol_eleitores} eleitores. As fontes não batem em toda seção: {pol_ambos} aparecem nas duas, {pol_zip} só no arquivo e {pol_painel} só no painel. Por isso o alerta manda conferir no e-Título. Se nada aparecer, isso não prova que a seção não mudou.",
            "A distância típica é de {med} m, quase o prédio ao lado. Mas {pct1km} das novas realocações passam de {um_km}, e para quem anda a pé isso pesa. O aviso é o recado na porta da padaria que mudou de esquina: só ajuda quem lê antes de sair de casa.",
            "Confira a sua seção: {link_politize}",
            "Depois avise vizinhos, família e colegas, antes do dia {dia_2t}. Conversar antes é livre. No dia, boca de urna é crime ({lei}). A seção que você digita não sai do seu aparelho.",
        ],
    },
    {
        "tag": "O que está em jogo",
        "tom": "marinho",
        "titulo": "Quem perde se a abstenção subir nessas seções",
        "metrica": "{dif_votos}",
        "metrica_rot": "votos de diferença a favor de Flávio, no cenário medido",
        "fig": G.fig_cenarios,
        "fonte": "mudancas.json, blocos de cenários e de efeito no 1º turno",
        "link": URL_LAUDO,
        "texto": [
            "Seção que muda faz o eleitorado faltar mais? No 1º turno, um pouco. As urnas em local temporário tiveram {dd} ponto a mais de abstenção que as estáveis do mesmo município, em diferença em diferenças contra 2022 ({ic}: {dd_lo} a {dd_hi}). {faixa_longe}, {longe} pontos. No Rio, onde o TRE transferiu locais por segurança ({rj_locais} alterados no estado, segundo a Agência Pública), {rj} pontos, e a Maré fechou o 1º turno com {mare} de abstenção.",
            "Aplicamos o efeito de {dd} ponto às {urnas_fora} urnas que seguem fora do prédio original em {dia_2t}. Flávio perde {pf} votos; Lula, {pl}. A diferença entre os dois muda {dif_votos} votos a favor de Flávio, porque essas urnas deram {pct_l} a Lula e {pct_f} a Flávio no 1º turno. É a padaria que mudou de esquina: o prejuízo cai sobre quem comprava mais ali.",
            "Nos cenários de {c_min} a {c_max} pontos de abstenção, nas {urnas_mr} urnas com mudança real (Lula com {pct_l_mr}, Flávio com {pct_f_mr}), a diferença varia de {v_min} a {v_max} votos. O saldo entre os turnos fica perto de zero: {saldo} votos a favor de Lula, porque {n_a} seções voltam ao prédio original e recuperam comparecimento.",
            "Conclusão: centenas de votos no cenário medido, poucos milhares no teto do Rio ({teto_rio}), nunca dezenas de milhares. Medimos uma diferença, não um efeito causal, e é conta de tamanho, não previsão.",
            "O dano real é local e recai sobre quem anda mais. O problema demonstrável é outro: quatro números públicos que não batem, painel e arquivo com {concord} de concordância e motivo ausente. Cenários e tabelas: {link_laudo}",
        ],
    },
]


def montar() -> list[dict]:
    v = valores()
    posts = []
    for p in POSTS:
        q = dict(p)
        for campo in CAMPOS_TEXTO:
            q[f"{campo}_f"] = p[campo].format_map(v)
        q["corpo"] = "\n\n".join(par.format_map(v) for par in p["texto"])
        q["svg"] = p["fig"]()
        posts.append(q)
    return posts


def verificar(posts: list[dict]) -> list[str]:
    """Lista de problemas; vazia quando a thread está dentro da regra da casa."""
    erros = []
    if len(posts) != 3:
        erros.append(f"{len(posts)} posts, esperados 3")
    for i, p in enumerate(posts, 1):
        n = len(p["corpo"])
        if not MIN_CHARS <= n <= MAX_CHARS:
            erros.append(f"post {i}: {n} caracteres")
        for m in [p[c] for c in CAMPOS_TEXTO] + list(p["texto"]):
            soltos = digitos_soltos(m)
            if soltos:
                erros.append(f"post {i}: algarismo digitado {soltos}")
        textos = [p["corpo"], *(p[f"{c}_f"] for c in CAMPOS_TEXTO)]
        for txt in textos:
            for prob in problemas_de_texto(txt):
                erros.append(f"post {i}: {prob}")
        for txt in [*textos, p["svg"]]:
            if PALAVRA_VETADA in txt.lower():
                erros.append(f"post {i}: palavra vetada")
        if "—" in p["svg"] or "–" in p["svg"]:
            erros.append(f"post {i}: travessão na figura")
        links = LINK.findall(p["corpo"])
        esperado = [p["link"]] if p["link"] else []
        if links != esperado:
            erros.append(f"post {i}: links {links}, esperado {esperado}")
    return erros
