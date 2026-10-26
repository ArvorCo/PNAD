"""Mesma urna nos dois turnos? Classificação por seção (regra pura, testável).

O número interno da urna vem do BU (``numero_interno_urna``) e o código de carga também.
Tipo de urna 3, 4 ou 6 é contingência ou reserva acionada no dia. Uma urna trocada entre
os turnos tem explicação técnica comum (defeito, substituição, reserva); a classificação
descreve o que o BU mostra e não prova irregularidade.
"""

from __future__ import annotations

TIPOS_RESERVA = frozenset({3, 4, 6})

SITUACOES = {
    "mesma": "Mesma urna nos dois turnos, com a mesma carga.",
    "mesma_recarga": "Mesma urna nos dois turnos, carregada de novo entre eles.",
    "reserva": "Urna de reserva ou contingência acionada no dia do 2º turno.",
    "nova": "Urna diferente da do 1º turno, que não emitiu boletim no 1º turno (substituída entre os turnos).",
    "outra_secao_zona": "Urna diferente da do 1º turno, que no 1º turno serviu outra seção da mesma zona.",
    "outra_secao_municipio": "Urna diferente da do 1º turno, que no 1º turno serviu outra zona do mesmo município.",
    "outro_municipio": "Urna diferente da do 1º turno, que no 1º turno serviu outro município.",
    "sem_1t": "Sem boletim desta seção no 1º turno para comparar a urna.",
}


def situacao(
    id1: int | None,
    id2: int | None,
    carga1: str | None,
    carga2: str | None,
    tipo2: int | None,
    origem_1t: tuple[str, str, int, int] | None,
    chave: tuple[str, str, int, int],
) -> str | None:
    """Código de ``SITUACOES`` ou ``None`` sem boletim do 2º turno.

    ``origem_1t``: (uf, mun, zona, seção) onde o número interno ``id2`` emitiu BU no
    1º turno, se emitiu; ``chave`` é a própria seção.
    """
    if id2 is None:
        return None
    if id1 is None:
        return "sem_1t"
    if id1 == id2:
        return "mesma" if (carga1 or "") == (carga2 or "") else "mesma_recarga"
    if origem_1t is not None and origem_1t != chave:
        if origem_1t[:2] != chave[:2]:
            return "outro_municipio"
        if origem_1t[2] == chave[2]:
            return "outra_secao_zona"
        return "outra_secao_municipio"
    if tipo2 in TIPOS_RESERVA:
        return "reserva"
    return "nova"
