"""Reconhece fragmentos de preparação arquivados antes da eleição.

Um relógio adiantado durante a carga pode produzir carimbos do dia da eleição
em arquivos encerrados dias antes. Exigir três evidências concordantes evita
que uma partida histórica interrompa um ciclo real de outra carga.
"""

import re
from datetime import date, timedelta

RE_ARQUIVO = re.compile(r"(?:^|/)(\d{8})(\d{2})(\d{2})(\d{4})\d{6}-\d+\.jez/")


def preparacao_anterior(nome: str, texto: str, dia: str = "04/10/2026") -> bool:
    corte = dia[6:10] + dia[3:5] + dia[:2]
    seguinte = (
        date(int(dia[6:10]), int(dia[3:5]), int(dia[:2])) + timedelta(days=1)
    ).strftime("%d/%m/%Y")
    arquivos = list(RE_ARQUIVO.finditer(nome))
    if not arquivos or not any(m[4] + m[3] + m[2] < corte for m in arquivos):
        return False
    ultimo_dia = None
    ajuste_anterior = False
    for linha in texto.splitlines():
        a = linha.split("\t")
        if len(a) != 6 or len(a[0]) != 19:
            continue
        data, _, _, app, msg, _ = a
        ultimo_dia = data[6:10] + data[3:5] + data[:2]
        # Um cômputo datado da eleição torna a origem ambígua: não o apagar.
        if data[:10] in (dia, seguinte) and (msg == "O voto do eleitor foi computado"):
            return False
        if app in ("ADH", "SCUE") and msg.startswith(
            ("Ajuste de Data e Hora ", "Data e hora que foi digitada pelo operador:")
        ):
            m = re.search(r"(\d{2})/(\d{2})/(\d{4})", msg)
            if m and m[3] + m[2] + m[1] < corte:
                ajuste_anterior = True
    return bool(ajuste_anterior and ultimo_dia and ultimo_dia < corte)
