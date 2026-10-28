"""Posts 25 e 26 da thread do 2º turno: onde Flávio teve menos votos no 2º turno e a
pendência documental com o TSE. Modelos com campos ``{chave}``, nunca algarismo solto.
"""

from __future__ import annotations

from . import thread_fig_d as D

POSTS_C: list[dict] = [
    {
        "tag": "Onde Flávio teve menos votos",
        "tom": "flavio",
        "titulo": "Onde Flávio teve menos votos no 2º turno.",
        "metrica": "{mv_n} de {mv_universo}",
        "metrica_rot": "municípios em que Flávio teve menos votos absolutos no 2º turno; Lula, em {ml_n}",
        "fig": D.fig_perdas,
        "fonte": "comparacao_1t.json e governadores.json, contas de turnos_perdas.py; lista em municipios_flavio_menos_votos_2t.csv",
        "texto": [
            "Verificado. Em {mv_n} dos {mv_universo} municípios, Flávio teve menos votos no 2º turno do que no 1º. Somadas, as perdas dão {mv_perda} votos, em municípios com {mv_aptos} de eleitores, {mv_aptos_pct} do país. Neles, Lula teve {mv_lula_saldo} e ganhou votos em {mv_lula_subiu}; o comparecimento caiu em {mv_comp_caiu}, com {mv_comp_saldo}. Régua: votos absolutos, não fatia dos válidos; menos votos não identifica eleitor nem motivo.",
            "Onde. Norte e Nordeste reúnem {mv_nne} desses municípios. As maiores contagens são {mv_top_ufs}.{mv_todos_frase}{mv_nenhum_frase} A maior perda foi em {mv_maior}, {mv_maior_v} votos.",
            "Inferência, com duas réguas declaradas. Quanto da perda cabe em menos gente votando? Pelo teto, que trata todo eleitor que deixou de votar como eleitor de Flávio, cabem {mv_teto} dos {mv_perda} votos; ao menos {mv_alem_teto} ficam fora, em {mv_n_alem_teto} municípios, e {mv_cobre_teto} Lula ganhou ao menos essa sobra. Pela régua proporcional, que supõe que quem deixou de votar votava como o município no 1º turno, a queda do comparecimento responde por {mv_prop} votos, {mv_prop_pct} da perda, e {mv_alem_prop} ficam fora dela. Nos {mv_n_manteve} municípios em que o comparecimento não caiu, a perda inteira, {mv_perda_manteve} votos, fica fora das duas réguas.",
            "O espelho, pela mesma régua: Lula teve menos votos no 2º turno em {ml_n} municípios, {ml_perda} votos somados, e o comparecimento caiu {ml_caiu}. A régua proporcional cobre {ml_prop_pct} da perda de Lula, contra {mv_prop_pct} da de Flávio. A maior perda de Lula foi em {ml_maior}, {ml_maior_v} votos.",
            "Achado contrário. Uma leitura comum diz que o comparecimento cai onde não há disputa estadual. Nas {gv_n} UFs com 2º turno de governador ({gv_ufs}), o comparecimento caiu em {gv_com} municípios, {gv_com_pct}; nas outras, em {gv_sem}, {gv_sem_pct}. {gv_leitura} A conta não controla região nem tamanho do município e não identifica causa.",
            "Como ler. O que fica fora das réguas é compatível com troca de lado, mas não a identifica: o mesmo saldo aparece se eleitores de Flávio no 1º turno ficaram em casa e outros, que faltaram no 1º, vieram votar em Lula. O município mostra saldos, não pessoas, e o voto é secreto. Subparte do dossiê: {mv_url_cap}. Lista completa, com as duas réguas por município: {mv_csv}",
        ],
    },
    {
        "tag": "Pendência documental",
        "tom": "outros",
        "titulo": "Pendência documental: o que pedir ao TSE.",
        "metrica": "{pd_mr_secoes} · {pd_re_n}",
        "metrica_rot": "seções com série da memória repetida na zona · com urna do 1º turno realocada",
        "fig": D.fig_pendencia,
        "fonte": "logs.json (metadados.serie_mr, metadados.dossie_metadados, rdv); lista de casos em metadados.json",
        "texto": [
            "Verificado. Dois achados do dossiê ficam sem documento público. O primeiro é a série da memória de resultado repetida: {pd_rep} valores aparecem em mais de uma seção, somando {pd_rep_secoes} seções. Os {pd_pares} pares soltos, em lugares diferentes, {pd_pares_leitura} ({pd_pares_esp} esperados). O resto são grupos fechados numa zona: no Brasil, {pd_grupos} grupos com {pd_mr_secoes} seções, nas {pd_blocos}; no exterior, um só valor cobre {pd_ext_secoes} seções em {pd_ext_cidades} cidades.",
            "Nas {pd_mr_secoes} seções do Brasil, a fatia de Flávio no 2º turno ficou {pd_mr_viz} contra as vizinhas do município, mas a mudança do 1º para o 2º turno foi {pd_mr_did}: {pd_mr_leitura}.",
            "O segundo é a urna realocada. O certificado de hardware de {pd_re_n} urnas que serviram uma seção no 1º turno apareceu em outra seção no 2º: {pd_re_mun} no mesmo município, {pd_re_zona} na mesma zona, em {pd_re_ufs} UFs. São {pd_re_aptos} aptos e {pd_re_comp} votantes; Flávio teve {pd_re_f2} dos votos nos finalistas, contra {pd_re_f1} nas mesmas seções no 1º turno, e {pd_re_mov}: a mudança contra elas foi {pd_re_did}. {pd_re_log}, e o registro digital do voto confere com o BU em {pd_rdv} seções do país, {pd_rdv_div}.",
            "Inferência. A explicação operacional é plausível: um lote de mídias com o mesmo número de série de fábrica explica a série repetida dentro de uma zona, e o remanejamento de urna de contingência explica o certificado que muda de seção. Transmitir com a memória de outra urna deixaria outra marca, contagem do log diferente da do BU, {pd_mr_contagem}. O que falta é o documento, e ele não está nos arquivos públicos do TSE. Registramos como pendência documental, não como pedido formal da casa.",
            "O que pedir: a relação das mídias de resultado do 2º turno por zona e lote, com número de série, nas zonas em que a série se repete; e o termo de substituição ou realocação da urna, com data e motivo, de cada uma das {pd_re_n} seções. Como pedir: pela Lei de Acesso à Informação, {pd_lei}, no serviço de informação ao cidadão do TSE ou do TRE da UF, sem precisar dizer por quê; cite o pleito {pd_pleito} e a seção. A lista está em analysis/apuracao_2t_2026/dados/metadados.json, chave entre_turnos_vsc.certificado_do_1t_em_outra_secao_no_2t_casos.",
            "Quem receber resposta pode mandá-la à casa, que publica o documento com hash ao lado da nota do capítulo dos logs: {pd_url_cap}. Atipicidade pede explicação, não prova irregularidade, e nada aqui atribui conduta a alguém.",
        ],
    },
]
