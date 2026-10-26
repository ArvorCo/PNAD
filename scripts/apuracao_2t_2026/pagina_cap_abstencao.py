"""Capítulo 7 do dossiê do 2º turno: a abstenção de 2º turno mais baixa desde 2006.

Abre pelo número oficial e pela régua dos mesmos municípios; publica onde a
abstenção subiu (o Norte inteiro inverte o sinal), testa as explicações candidatas
e mostra que a abstenção baixa não explica nem a queda de Flávio nem o erro das
pesquisas.
"""

from __future__ import annotations

import re

from apuracao_2026.pagina_comum import (
    Capitulo,
    Dados,
    caminho,
    cartao,
    checar,
    inteiro,
    limites,
    milhoes,
    nota,
    num,
    p,
)
from apuracao_2026.pagina_fig_base import pct, pp

from . import pagina_fig_abstencao as F
from . import pagina_fig_correlacao as FC
from . import pagina_texto_abstencao as T
from .pagina_comum import cabeca
from .pagina_fig_turnos_util import ESTILO, nome_uf

ARQ = "abstencao.json"


def _valores_uf(u: dict) -> tuple[float, float]:
    return F._uf_valores(u)


def _oficial(itens: list[dict]) -> dict | None:
    """Matéria que cita o número oficial com 'desde 2006' (CNN ou Poder360)."""
    for x in itens:
        if (
            "2006" in (x.get("titulo", "") + x.get("resumo", ""))
            and x.get("tipo") == "fato"
        ):
            return x
    return None


def _frase_maior_alta(ufs: list[dict], subiram: list[dict]) -> str:
    if not subiram:
        return ""
    quedas = [
        _valores_uf(u)[1] - _valores_uf(u)[0]
        for u in ufs
        if _valores_uf(u)[0] < _valores_uf(u)[1]
    ]
    maior_queda = max(quedas, default=0)
    acima = [
        u["uf"] for u in subiram if _valores_uf(u)[0] - _valores_uf(u)[1] > maior_queda
    ]
    if not acima:
        return ""
    return (
        f" Quem escreve que a abstenção caiu no país precisa dizer também que em {', '.join(acima)} ela subiu mais do que "
        f"caiu em qualquer estado (a maior queda foi de {num(maior_queda, 2)} pontos)."
    )


def _numero_oficial(x: dict) -> str:
    m = re.search(r"(\d{2},\d{2})\s*%", x.get("titulo", "") + " " + x.get("resumo", ""))
    return f"{m.group(1)}%" if m else "o número oficial"


def render(d: Dados, cap: Capitulo) -> str:
    A = d.get(ARQ)
    checar(
        d,
        ARQ,
        [
            "brasil",
            "ufs",
            "regioes",
            "capitais_x_interior",
            "histograma_pa_2t",
            "concentracao_abaixo_15",
        ],
    )
    C1 = d.get("comparacao_1t.json")
    P = d.get("presidente.json") or {}
    PV = d.get("pesquisas_vs_urna.json") or {}
    itens = T.noticias_abstencao(_noticias(d))
    nac = P.get("nacional") or {}
    br = A["brasil"]
    pa_nac = nac.get("pct_abstencao")
    pa_1t_nac = caminho(PV, "urna.primeiro_turno_brasil.abstencao_pct")
    ofi = _oficial(itens)
    ufs = A["ufs"]
    subiram = sorted(
        (u for u in ufs if _valores_uf(u)[0] > _valores_uf(u)[1]),
        key=lambda u: -(_valores_uf(u)[0] - _valores_uf(u)[1]),
    )
    menores = sorted(ufs, key=lambda u: _valores_uf(u)[0])[:6]
    conc = {x["regiao"]: x for x in A["concentracao_abaixo_15"]}
    ci = A["capitais_x_interior"]

    h = ESTILO + cabeca(
        cap,
        "Menos ausentes:<br><em>a abstenção de 2º turno mais baixa desde 2006.</em>",
        f"{pct(pa_nac)} do eleitorado não votou{f', contra {pct(pa_1t_nac)} no 1º turno' if pa_1t_nac else ''}. "
        f"Nos mesmos {inteiro(br['n_municipios'])} municípios, {pct(br['pa_2t'])} contra {pct(br['pa_1t_mesmos'])} no 1º turno "
        f"e {pct(br['pa_2022_2t_mesmos'])} no 2º turno de 2022.",
    )
    h += (
        '<div class="finding-grid">'
        + cartao(
            pct(pa_nac),
            f"abstenção no 2º turno, {milhoes(nac.get('abstencao', 0))} de eleitores",
        )
        + cartao(pp(br["delta_1t_pp"]), "contra o 1º turno, mesmos municípios")
        + cartao(
            pp(br["delta_2022_pp"]), "contra o 2º turno de 2022, mesmos municípios"
        )
        + cartao(str(len(subiram)), "UFs em que a abstenção subiu")
        + "</div>"
    )
    if ofi:
        h += p(
            f"O TSE anunciou {_numero_oficial(ofi)} na noite, e a {ofi['veiculo']} registrou que é a menor abstenção de 2º turno "
            'desde 2006. O Globo escreveu "menor desde 2010": as duas leituras cabem, porque a de 2010 conta também o '
            f"1º turno daquele ano. A diferença entre os {_numero_oficial(ofi)} oficiais e os {pct(pa_nac)} desta página é a versão do "
            "arquivo lida (a nossa é a mais nova do banco da casa, com 99,99% das seções).",
            "relato",
        )
    h += T.fontes_imprensa(itens)
    h += "<h3>Onde caiu e onde subiu</h3>"
    h += p(
        "As menores abstenções ficaram no Nordeste: "
        + ", ".join(f"{nome_uf(u['uf'])} {pct(_valores_uf(u)[0])}" for u in menores)
        + f". O Nordeste concentra {pct(conc.get('Nordeste', {}).get('pct_aptos_abaixo_15_no_pais'), 1)} do eleitorado dos "
        "municípios com abstenção abaixo de 15%.",
        "verificado",
    )
    sul = conc.get("Sul")
    if sul:
        h += p(
            f"Mas a região com a maior parte dos seus municípios abaixo de 15% é o Sul: {pct(sul['pct_municipios_abaixo_15'])} "
            f"({inteiro(sul['municipios_abaixo_15'])} de {inteiro(sul['municipios'])}), quase todos pequenos. Comparecimento "
            "alto não é marca de uma região nem de um lado.",
            "verificado",
        )
    h += F.fig_ranking(A)
    h += nota(
        "contrario",
        f"A queda não foi geral. A abstenção subiu contra o 1º turno em {len(subiram)} UFs: "
        + ", ".join(
            f"{u['uf']} ({pp(_valores_uf(u)[0] - _valores_uf(u)[1])})" for u in subiram
        )
        + ". O Norte inteiro inverte o sinal: "
        + next(
            (
                f"{pct(x['pa_1t_mesmos'])} para {pct(x['pa_2t'])}"
                for x in A["regioes"]
                if x["regiao"] == "Norte"
            ),
            "s/d",
        )
        + "."
        + _frase_maior_alta(ufs, subiram),
        "Onde a abstenção subiu.",
    )
    h += F.fig_mapa_delta(A)
    if C1:
        h += F.fig_mapas_mun(d, C1)
    h += F.fig_histograma(A)
    cap_ = ci["capitais"]
    int_ = ci["interior"]
    h += p(
        f"Capitais e interior caíram juntos: {pct(cap_['pa_2t'])} nas capitais ({pp(cap_['delta_1t_pp'])} contra o 1º turno) "
        f"e {pct(int_['pa_2t'])} no interior ({pp(int_['delta_1t_pp'])}). Contra 2022, a mudança foi de "
        f"{pp(int_['delta_2022_pp'])} no interior e {pp(cap_['delta_2022_pp'])} nas capitais.",
        "verificado",
    )
    h += F.fig_recortes(A)
    h += T.tabela_capitais(A)
    if C1:
        n_q = (C1.get("abstencao_caiu_5pp") or {}).get("n")
        n_s = (C1.get("abstencao_subiu_5pp") or {}).get("n")
        h += p(
            f"Entre os municípios com 5 mil eleitores ou mais, {inteiro(n_q)} tiveram abstenção pelo menos 5 pontos menor que "
            f"no 1º turno e {inteiro(n_s)} tiveram abstenção pelo menos 5 pontos maior."
            + (
                " Há mais municípios com alta forte do que com queda forte: a média nacional cai porque a queda moderada "
                "é quase universal, não porque houve saltos."
                if (n_s or 0) > (n_q or 0)
                else ""
            ),
            "verificado",
        )
        h += T.tabela_quedas(C1)
        h += T.lista_altas(C1)
        fig_q, q_lula, q_abs = F.fig_quintis(C1)
    else:
        fig_q, q_lula, q_abs = "", [], []
    h += T.hipoteses(d, A, q_lula, q_abs)
    h += fig_q
    h += nota(
        "juizo",
        "A queda da abstenção é o fato mais limpo da noite e o mais mal explicado. Prorrogação, mobilização e transporte "
        "foram oferecidos como causa no mesmo minuto em que o número saiu; o primeiro o dado descarta, o segundo o dado não "
        "confirma no formato em que foi dito, e o terceiro ninguém mediu. O que se pode afirmar: votou mais gente, em quase "
        "todo o país; e, pela conta de teto do capítulo Pesquisas, mesmo que todo o aumento líquido do comparecimento "
        "tivesse ido para Lula, ele continuaria à frente.",
        "Juízo editorial.",
    )
    h += FC.bloco(d)
    h += limites(
        [
            "Abstenção sobre o eleitorado das seções totalizadas; a versão lida não é a do anúncio oficial.",
            "Comparação com o 1º turno e 2022 nos mesmos municípios completos; UFs pelo arquivo da UF.",
            "Quintis por número de municípios, médias ponderadas pelo eleitorado; correlação não é causa.",
            "O acervo não tem oferta de transporte, ocorrência de boca de urna nem tempo observado em 25/10.",
            "Eleitorado pode mudar entre turnos por cancelamento e regularização; a régua usa o de cada turno.",
        ]
    )
    return h


def _noticias(d: Dados):
    for nome in ("noticias_noite.json", "../noticias_noite.json"):
        v = d.get(nome)
        if v:
            return v
    return None
