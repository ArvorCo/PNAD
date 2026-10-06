"""Extrato por UF da janela 19:14:08 a 20:04:39 de 04/10/2026 (hora de Brasília).

Lê `apuracao/data/apuracao.sqlite` (somente leitura) e grava
`analysis/apuracao_2026/extratos/janela_1914_2004_por_uf.csv` e `.md`: para cada UF,
as seções totalizadas e os votos de Lula e Flávio no arquivo de resultado da UF
(`<uf>-c0001-e006257-u.json`) na última versão gerada até cada instante, mais o
instante cujo retrato das UFs reproduz a contagem do arquivo nacional, e a contagem
por UF do arquivo de monitoramento nacional (`br-e006257-ab.json`) mais próximo.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BANCO = RAIZ / "apuracao/data/apuracao.sqlite"
SAIDA = RAIZ / "analysis/apuracao_2026/extratos/janela_1914_2004_por_uf"
NACIONAL_1 = "2026-10-04T22:14:08.000Z"  # 19:14:08 BRT
NACIONAL_2 = "2026-10-04T23:04:39.000Z"  # 20:04:39 BRT
AB_1 = "2026-10-04T22:13:57.000Z"
AB_2 = "2026-10-04T23:05:03.000Z"
ELE, CARGO = 6257, 1


def conectar(caminho: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{caminho}?mode=ro", uri=True)


def candidatos(con: sqlite3.Connection) -> tuple[str, str]:
    numeros = {
        int(n): sq
        for sq, n in con.execute(
            "SELECT sqcand, numero FROM candidato WHERE eleicao_cd=? AND cargo_cd=?",
            (ELE, CARGO),
        )
    }
    return numeros[13], numeros[22]


def ufs(con: sqlite3.Connection) -> list[str]:
    return [
        r[0]
        for r in con.execute(
            "SELECT DISTINCT uf FROM arquivo WHERE tipo='u' AND nivel='uf' "
            "AND cargo_cd=? AND eleicao_cd=? ORDER BY uf",
            (CARGO, ELE),
        )
    ]


def versao_uf(
    con: sqlite3.Connection, uf: str, ate: str, lula: str, flavio: str
) -> dict:
    r = con.execute(
        """SELECT s.id, s.gerado_em, t.st, t.ts, t.vvc FROM snapshot s
           JOIN arquivo a ON a.id = s.arquivo_id JOIN totais t ON t.snapshot_id = s.id
           WHERE a.tipo='u' AND a.nivel='uf' AND a.cargo_cd=? AND a.eleicao_cd=? AND a.uf=?
             AND s.regressivo=0 AND s.gerado_em<=?
           ORDER BY s.gerado_em DESC LIMIT 1""",
        (CARGO, ELE, uf, ate),
    ).fetchone()
    votos = dict(
        con.execute(
            "SELECT sqcand, vap FROM voto_candidato WHERE snapshot_id=? AND sqcand IN (?, ?)",
            (r[0], lula, flavio),
        ).fetchall()
    )
    return {
        "gerado_em": r[1],
        "st": r[2],
        "ts": r[3],
        "validos": r[4],
        "lula": votos.get(lula, 0),
        "flavio": votos.get(flavio, 0),
    }


def soma_ufs(
    con: sqlite3.Connection, ate: str, lista: list[str], lula: str, flavio: str
) -> int:
    return sum(versao_uf(con, uf, ate, lula, flavio)["st"] for uf in lista)


def nacional(con: sqlite3.Connection, gerado_em: str) -> dict:
    r = con.execute(
        """SELECT s.capturado_em, t.st, t.ts FROM snapshot s
           JOIN arquivo a ON a.id = s.arquivo_id JOIN totais t ON t.snapshot_id = s.id
           WHERE a.tipo='u' AND a.nivel='br' AND a.cargo_cd=? AND a.eleicao_cd=? AND s.gerado_em=?""",
        (CARGO, ELE, gerado_em),
    ).fetchone()
    return {"gerado_em": gerado_em, "lido_em": r[0], "st": r[1], "ts": r[2]}


def monitoramento(con: sqlite3.Connection, gerado_em: str) -> dict[str, int]:
    sid = con.execute(
        """SELECT s.id FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id
           WHERE a.tipo='ab' AND a.nivel='br' AND a.eleicao_cd=? AND s.gerado_em=?""",
        (ELE, gerado_em),
    ).fetchone()[0]
    return {
        r[0]: r[1]
        for r in con.execute(
            "SELECT cdabr, st FROM ab_estado WHERE snapshot_id=? AND tpabr='uf'", (sid,)
        )
    }


def retrato(
    con: sqlite3.Connection, alvo: int, lista: list[str], lula: str, flavio: str
) -> str:
    """Instante (minuto cheio) cuja soma das UFs fica mais perto da contagem nacional."""
    import datetime as dt

    melhor, dist = "", 10**9
    base = dt.datetime(2026, 10, 4, 21, 50)
    for m in range(30):
        t = (base + dt.timedelta(minutes=m)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        d = abs(soma_ufs(con, t, lista, lula, flavio) - alvo)
        if d < dist:
            melhor, dist = t, d
    return melhor


def n(x: int) -> str:
    """Inteiro com ponto de milhar."""
    return f"{n(x)}".replace(",", ".")


def brt(iso: str) -> str:
    import datetime as dt

    t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")) - dt.timedelta(hours=3)
    return t.strftime("%H:%M:%S")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--banco", type=Path, default=BANCO)
    args = ap.parse_args()
    con = conectar(args.banco)
    lula, flavio = candidatos(con)
    lista = ufs(con)
    n1, n2 = nacional(con, NACIONAL_1), nacional(con, NACIONAL_2)
    t_retrato = retrato(con, n1["st"], lista, lula, flavio)
    ab1, ab2 = monitoramento(con, AB_1), monitoramento(con, AB_2)
    linhas = []
    for uf in lista:
        a = versao_uf(con, uf, NACIONAL_1, lula, flavio)
        r = versao_uf(con, uf, t_retrato, lula, flavio)
        b = versao_uf(con, uf, NACIONAL_2, lula, flavio)
        linhas.append(
            {
                "uf": uf.upper(),
                "secoes_total": b["ts"],
                "st_retrato_nacional_1914": r["st"],
                "st_arquivo_uf_1914": a["st"],
                "arquivo_uf_gerado_1914": brt(a["gerado_em"]),
                "st_arquivo_uf_2004": b["st"],
                "arquivo_uf_gerado_2004": brt(b["gerado_em"]),
                "delta_st_retrato": b["st"] - r["st"],
                "delta_st_arquivo_uf": b["st"] - a["st"],
                "st_monitoramento_1913": ab1.get(uf),
                "st_monitoramento_2005": ab2.get(uf),
                "lula_retrato_1914": r["lula"],
                "flavio_retrato_1914": r["flavio"],
                "lula_2004": b["lula"],
                "flavio_2004": b["flavio"],
                "delta_lula": b["lula"] - r["lula"],
                "delta_flavio": b["flavio"] - r["flavio"],
            }
        )
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SAIDA.with_suffix(".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    tot = {
        k: sum(x[k] or 0 for x in linhas)
        for k in linhas[0]
        if k not in ("uf",) and not k.startswith("arquivo")
    }
    md = [
        "# Janela 19:14:08 a 20:04:39 de 04/10/2026, por UF",
        "",
        "Fonte: arquivos públicos do TSE em `resultados.tse.jus.br/oficial/ele2026/6257/dados/`, lidos e guardados versão a versão pelo coletor da casa (`apuracao/`), com a hora de geração que o próprio TSE grava em cada arquivo (`dg`/`hg`). Horas em Brasília.",
        "",
        f"- Arquivo nacional `br-c0001-e006257-u.json` gerado às {brt(n1['gerado_em'])} (lido às {brt(n1['lido_em'])}): {n(n1['st'])} seções totalizadas de {n(n1['ts'])}.",
        f"- Arquivo nacional gerado às {brt(n2['gerado_em'])} (lido às {brt(n2['lido_em'])}): {n(n2['st'])} seções.",
        f"- Diferença: {n(n2['st'] - n1['st'])} seções.",
        "",
        "O arquivo nacional não traz divisão por UF. A divisão vem dos 28 arquivos de UF (`<uf>-c0001-e006257-u.json`, 27 UFs e exterior), que o TSE gera em instantes próprios. Três leituras, declaradas:",
        "",
        f"1. **Retrato do nacional** (`st_retrato_nacional_1914`): a versão de cada arquivo de UF gerada até {brt(t_retrato)}, instante em que a soma das UFs ({n(tot['st_retrato_nacional_1914'])}) fica mais perto da contagem do arquivo nacional de 19:14:08 ({n(n1['st'])}). O arquivo nacional de 19:14:08 era o retrato de cerca de {brt(t_retrato)}.",
        f"2. **Arquivo de UF no mesmo instante** (`st_arquivo_uf_1914`): a versão de cada UF gerada até 19:14:08; a soma ({n(tot['st_arquivo_uf_1914'])}) já estava {n(tot['st_arquivo_uf_1914'] - n1['st'])} seções à frente do nacional.",
        f"3. **Monitoramento** (`st_monitoramento_*`): contagem por UF do arquivo `br-e006257-ab.json` gerado às {brt(AB_1)} e às {brt(AB_2)}, que continuou sendo gerado durante a parada do arquivo de resultado.",
        "",
        f"Às 20:04:39 a soma das UFs ({n(tot['st_arquivo_uf_2004'])}) e o nacional ({n(n2['st'])}) quase coincidem. O monitoramento somava {n(tot['st_monitoramento_1913'])} seções às {brt(AB_1)} e {n(tot['st_monitoramento_2005'])} às {brt(AB_2)}: depois da parada, ficou atrás dos arquivos de UF.",
        "",
        "| UF | seções | retrato 19:14 | UF 19:14 | 20:04 | Δ retrato | Δ Lula | Δ Flávio |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for x in sorted(linhas, key=lambda x: -x["delta_st_retrato"]):
        md.append(
            f"| {x['uf']} | {n(x['secoes_total'])} | {n(x['st_retrato_nacional_1914'])} | {n(x['st_arquivo_uf_1914'])} | {n(x['st_arquivo_uf_2004'])} | {n(x['delta_st_retrato'])} | {n(x['delta_lula'])} | {n(x['delta_flavio'])} |"
        )
    md.append(
        f"| **Total** | {n(tot['secoes_total'])} | {n(tot['st_retrato_nacional_1914'])} | {n(tot['st_arquivo_uf_1914'])} | {n(tot['st_arquivo_uf_2004'])} | {n(tot['delta_st_retrato'])} | {n(tot['delta_lula'])} | {n(tot['delta_flavio'])} |"
    )
    md += [
        "",
        "Colunas completas no CSV ao lado. Δ = 20:04 menos retrato de 19:14. Votos de Lula e Flávio são os nominais (`vap`) do arquivo de UF.",
        "",
        "Limites: o retrato é aproximação por minuto cheio; os arquivos de UF e o nacional são gerados por processos separados do TSE, por isso as somas não batem no segundo. As versões brutas (JSON original com hash SHA-256) estão no banco do coletor, disponível a pedido.",
    ]
    SAIDA.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(SAIDA.with_suffix(".csv"), len(linhas), "UFs; retrato", brt(t_retrato), tot)


if __name__ == "__main__":
    main()
