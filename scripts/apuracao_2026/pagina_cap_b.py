"""Capítulos 06 a 09 do dossiê da apuração: Câmara, Senado, assembleias e governadores."""

from __future__ import annotations

from . import pagina_comparacao as CMP
from . import pagina_texto_b as T
from . import pagina_texto_senado_flavio as TSF
from .pagina_comum import Capitulo, Dados, checar, limites, secao
from .pagina_texto import fig

# ------------------------------------------------------------------ 06


def r_camara(d: Dados, cap: Capitulo) -> str:
    C = d.get("camara.json")
    checar(
        d,
        "camara.json",
        [
            "por_campo",
            "blocos",
            "por_partido",
            "votos_por_campo_pct",
            "deputados_mais_votados",
        ],
    )
    b = C["blocos"]
    h = secao(
        cap,
        f"Câmara: {b['direita + centro-direita']} cadeiras<br><em>para direita e centro-direita.</em>",
        f"PL {C['por_partido'].get('PL', 0)}, PT {C['por_partido'].get('PT', 0)}. O bloco passa da maioria e não chega aos três quintos.",
    )
    h += T.camara_a(C) + fig("hemiciclo_camara", d)
    h += T.camara_b(C) + CMP.camara(d) + fig("camara_partidos", d)
    h += T.camara_c(C) + fig("votos_x_cadeiras", d)
    h += T.camara_d(C) + fig("camara_por_uf", d)
    h += limites(
        [
            "Votos de partido somam nominais e legenda; campo é classificação editorial da casa.",
            "Nas UFs provisórias, a lista sai do quociente da casa até o TSE fechar.",
        ]
    )
    h += "</section>"
    return h


# ------------------------------------------------------------------ 07


def r_senado(d: Dados, cap: Capitulo) -> str:
    S = d.get("senado.json")
    checar(
        d,
        "senado.json",
        [
            "senado_2027.por_bloco",
            "senado_2027.continuam_por_campo",
            "senado_2027.novos_por_campo",
            "eleitos_2026",
            "disputas",
        ],
    )
    s = S["senado_2027"]
    h = secao(
        cap,
        f"Senado de 2027:<br><em>{s['por_bloco']['direita + centro-direita']} de {s['total']}.</em>",
        f"Direita e centro-direita passam dos três quintos. O PL terá {s['por_partido'].get('PL', 0)} senadores.",
    )
    h += T.senado_a(S) + fig("hemiciclo_senado", d)
    h += T.senado_b(S) + CMP.senado(d) + fig("senado_segundas_vagas", d)
    h += T.senado_c(S)
    h += TSF.capitulo(d)
    h += "</section>"
    return h


# ------------------------------------------------------------------ 08


def r_assembleias(d: Dados, cap: Capitulo) -> str:
    A = d.get("assembleias.json")
    checar(d, "assembleias.json", ["casas"])
    h = secao(
        cap,
        "Assembleias<br><em>dos estados que pesam.</em>",
        f"{len(A['casas'])} casas, da maior para a menor, por campo.",
    )
    h += T.assembleias_a(A) + fig("assembleias_campo", d)
    h += T.assembleias_b(A) + CMP.assembleias(d) + "</section>"
    return h


# ------------------------------------------------------------------ 09


def r_governadores(d: Dados, cap: Capitulo) -> str:
    G = d.get("governadores.json")
    checar(
        d,
        "governadores.json",
        [
            "ufs",
            "vao_estadual.lista",
            "governador_x_presidente",
            "eleitos_1t_por_campo",
        ],
    )
    h = secao(
        cap,
        "Governadores<br><em>e o 2º turno.</em>",
        f"{G['n_eleitos_1t']} eleitos no 1º turno, {G['n_segundo_turno']} segundos turnos. O vão estadual mede o teto, não a transferência.",
    )
    h += T.governadores_a(G) + fig("vao_estadual", d)
    h += T.governadores_b(G) + fig("governadores_mapa", d)
    h += T.governadores_c(G) + CMP.governadores(d)
    h += limites(
        [
            "Vão estadual é teto endereçável: mesma urna, cargos diferentes, não diz quem votou em quem.",
            "Campo é classificação editorial da casa (tucano é centro-esquerda); exceções por candidatura declaradas.",
        ]
    )
    h += "</section>"
    return h
