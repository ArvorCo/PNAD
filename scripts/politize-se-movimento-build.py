#!/usr/bin/env python3
"""Publica movimento horário das seções para Politize-se e seu mapa."""

from politize_se.movimento import publicar

if __name__ == "__main__":
    m = publicar()
    print(f"{m['cobertas']} de {m['secoes']} seções; {m['votos']} votos computados")
