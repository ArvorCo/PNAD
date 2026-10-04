"""Gera public/campos.json: cor e ordem de cada campo e o campo de cada partido.

A classificação vem de `PARTIDO_CAMPO` (scripts/voto_util_base.py) e a paleta de
`scripts/senado_2026/pagina/comum.py`, as mesmas das páginas publicadas. As
chaves de `partidos` seguem a grafia do campo `sg` da API de resultados do TSE
("PC do B", "PODE", "UNIÃO"), com as federações ("PT/PC do B/PV") resolvidas
pelos partidos que as compõem. Copia também os 27 senadores eleitos em 2022
(analysis/senado_2026/senadores_2022.json, campos sem renomear) para
public/senadores_2022.json. Ao final, confere se todo `sg`/`sgp` presente nas
fixtures do coletor resolve para um campo.
"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ.parent / "scripts"
FIXTURES = RAIZ / "tests" / "fixtures"
SAIDA = RAIZ / "public" / "campos.json"
SENADORES_ORIGEM = RAIZ.parent / "analysis" / "senado_2026" / "senadores_2022.json"
SENADORES = RAIZ / "public" / "senadores_2022.json"

# Grafia do TSE (campo `sg`) -> chave de PARTIDO_CAMPO.
ALIAS_TSE = {
    "PC do B": "PCdoB",
    "PODE": "PODEMOS",
    "SD": "SOLIDARIEDADE",
    "REP": "REPUBLICANOS",
    "MOB": "MOBILIZA",
}

# Partidos ausentes de PARTIDO_CAMPO, com o motivo da classificação.
# PMB: as listas de direita ampla da casa (mg-082026-camada2.py e
# sp-092026-camada2.py) o agrupam com AGIR e MOBILIZA, que são centro-direita.
EXTRA = {"PMB": ("centro-direita", "agrupado com AGIR e MOBILIZA nos atlas")}

# Exceções por candidatura (SQ_CANDIDATO do TSE), quando a sigla não descreve o campo.
# Decisão editorial do Leonardo na noite de 04/10/2026.
EXCECOES_CANDIDATO = {
    "20002553711": (
        "centro-direita",
        "Marina JHC, Senado AL, PSDB; grupo do prefeito JHC",
    ),
    "20002553350": ("centro-direita", "JHC, governo AL, PSDB; ex-PL, mesmo grupo"),
}

# Federações registradas em 2026, na grafia do TSE.
FEDERACOES = (
    "PT/PC do B/PV",
    "PSDB/CIDADANIA",
    "PSOL/REDE",
    "PRD/SOLIDARIEDADE",
    "UNIÃO/PP",
)


def carregar() -> tuple[dict[str, str], dict[str, str], tuple[str, ...], dict]:
    sys.path.insert(0, str(SCRIPTS))
    base = importlib.import_module("voto_util_base")
    comum = importlib.import_module("senado_2026.pagina.comum")
    return base.PARTIDO_CAMPO, comum.COR, comum.ORDEM, comum.ROTULO


def campo_partido(sg: str, partido_campo: dict[str, str]) -> str | None:
    if sg in EXTRA:
        return EXTRA[sg][0]
    chave = ALIAS_TSE.get(sg, sg)
    return partido_campo.get(chave) or partido_campo.get(chave.upper())


def siglas_fixtures() -> set[str]:
    achadas: set[str] = set()

    def andar(no: object) -> None:
        if isinstance(no, dict):
            for k, v in no.items():
                if k in ("sg", "sgp") and isinstance(v, str) and v:
                    achadas.add(v)
                andar(v)
        elif isinstance(no, list):
            for item in no:
                andar(item)

    for arq in sorted(FIXTURES.rglob("*.json")):
        andar(json.loads(arq.read_text(encoding="utf-8")))
    return achadas


def copiar_senadores(campos: dict) -> int:
    dados = json.loads(SENADORES_ORIGEM.read_text(encoding="utf-8"))
    ufs = {s["uf"] for s in dados}
    if len(dados) != 27 or len(ufs) != 27:
        raise SystemExit(f"senadores_2022: {len(dados)} linhas, {len(ufs)} UFs")
    for s in dados:
        faltam = {"uf", "nome", "partido", "campo"} - s.keys()
        if faltam or s["campo"] not in campos:
            raise SystemExit(f"senadores_2022 inválido em {s.get('uf')}: {faltam}")
    SENADORES.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return len(dados)


def main() -> None:
    partido_campo, cor, ordem, rotulo = carregar()
    campos = {
        c: {"cor": cor[c], "ordem": i, "rotulo": rotulo[c]} for i, c in enumerate(ordem)
    }

    partidos: dict[str, str] = {}
    for sg, campo in partido_campo.items():
        partidos[sg] = campo
    for tse, chave in ALIAS_TSE.items():
        partidos[tse] = partido_campo[chave]
    for sg, (campo, _) in EXTRA.items():
        partidos[sg] = campo

    conflitos = []
    for fed in FEDERACOES:
        componentes = [campo_partido(p, partido_campo) for p in fed.split("/")]
        if None in componentes:
            raise SystemExit(f"federação com partido sem campo: {fed} {componentes}")
        if len(set(componentes)) > 1:
            conflitos.append((fed, componentes))
        partidos[fed] = componentes[0] or "indefinido"

    nao_resolvidas = []
    for sg in sorted(siglas_fixtures()):
        if sg not in partidos:
            campo = campo_partido(sg, partido_campo)
            if campo is None:
                nao_resolvidas.append(sg)
                partidos[sg] = "indefinido"
            else:
                partidos[sg] = campo

    for campo in partidos.values():
        if campo not in campos:
            raise SystemExit(f"campo sem cor: {campo}")

    for sq, (campo, _) in EXCECOES_CANDIDATO.items():
        if campo not in campos:
            raise SystemExit(f"exceção {sq} com campo sem cor: {campo}")
    saida = {
        "campos": campos,
        "partidos": dict(sorted(partidos.items())),
        "excecoes": {sq: c for sq, (c, _) in EXCECOES_CANDIDATO.items()},
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"{SAIDA.relative_to(RAIZ)}: {len(campos)} campos, {len(partidos)} siglas")
    print(f"{SENADORES.relative_to(RAIZ)}: {copiar_senadores(campos)} senadores")
    for fed, comps in conflitos:
        print(f"federação mista, campo do primeiro partido: {fed} {comps}")
    print(f"siglas das fixtures sem campo: {nao_resolvidas or 'nenhuma'}")


if __name__ == "__main__":
    main()
