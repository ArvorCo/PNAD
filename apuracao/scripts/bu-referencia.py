"""Decodificação de referência de um -bu.dat com asn1tools, no formato do decodificador TS.

Serve de gabarito independente para tests/bu-decode.test.ts: o decodificador em
TypeScript (scripts/bu-decode.ts) tem de reproduzir esta saída campo a campo.

Especificação: scripts/secoes/bu.asn1, cópia verbatim de docv2/spec/bu.asn1 em
github.com/doccaz/urnas-br (commit 6026afb6, 15/10/2024), que reproduz o pacote do
TSE "formato-arquivos-bu-rdv-ass-digital-v2"; SHA-256
e53e28e9812bb7e19cc4bcc77b6ce48f25c413f62a60369a91c4f269e19b7ed6.

Uso, num ambiente com asn1tools 0.169.0 (não é dependência do projeto):
    python3 -m venv /tmp/venv && /tmp/venv/bin/pip install asn1tools==0.169.0
    /tmp/venv/bin/python scripts/bu-referencia.py \\
        tests/fixtures/bu/o03220sp7107200010001-bu.dat \\
        > tests/fixtures/bu/o03220sp7107200010001-bu.asn1tools.json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import asn1tools

SPEC = Path(__file__).resolve().parent / "secoes" / "bu.asn1"
ENUMS = [
    "Fase",
    "TipoUrna",
    "TipoArquivo",
    "TipoEnvelope",
    "TipoCargoConsulta",
    "TipoVoto",
    "CargoConstitucional",
    "TipoApuracao",
    "MotivoApuracaoEletronica",
    "MotivoApuracaoManual",
    "MotivoApuracaoMistaComBU",
    "MotivoApuracaoMistaComMR",
]
MOTIVO_POR_ALTERNATIVA = {
    "apuracaoMistaMR": "MotivoApuracaoMistaComMR",
    "apuracaoMistaBUAE": "MotivoApuracaoMistaComBU",
    "apuracaoTotalmenteManual": "MotivoApuracaoManual",
    "apuracaoEletronica": "MotivoApuracaoEletronica",
}


def enumeracoes(texto: str) -> dict[str, dict[str, int]]:
    """Rótulo para código de cada ENUMERATED da especificação."""
    out: dict[str, dict[str, int]] = {}
    for nome in ENUMS:
        m = re.search(nome + r" ::= ENUMERATED \{(.*?)\}", texto, re.DOTALL)
        if m is None:
            raise SystemExit(f"enumeração {nome} ausente da especificação")
        out[nome] = {k: int(v) for k, v in re.findall(r"(\w+)\s*\((\d+)\)", m[1])}
    return out


def converter(env: dict[str, Any], bu: dict[str, Any], e: dict[str, dict[str, int]]):
    def cab(c):
        tipo, valor = c["idEleitoral"]
        return {
            "dataGeracao": c["dataGeracao"],
            "idEleitoral": {"tipo": tipo, "valor": valor},
        }

    def mz(m):
        return {"municipio": m["municipio"], "zona": m["zona"]}

    def secao(s):
        return {
            "municipioZona": mz(s["municipioZona"]),
            "local": s["local"],
            "secao": s["secao"],
        }

    def id_urna(x):
        if x[0] == "identificacaoSecaoEleitoral":
            return {"tipo": x[0], "secao": secao(x[1])}
        return {"tipo": x[0], "municipioZona": mz(x[1]["municipioZona"])}

    def motivo(sa):
        if sa is None:
            return None
        alt, v = sa
        tipo = v.get("tipoApuracao", v.get("tipoapuracao"))
        return {
            "alternativa": alt,
            "tipoApuracao": e["TipoApuracao"][tipo],
            "motivoApuracao": e[MOTIVO_POR_ALTERNATIVA[alt]][v["motivoApuracao"]],
        }

    def cargo(c):
        tipo, valor = c
        if tipo == "cargoConstitucional":
            valor = e["CargoConstitucional"][valor]
        return {"tipo": tipo, "valor": valor}

    def votavel(v):
        ident = v.get("identificacaoVotavel")
        return {
            "tipoVoto": e["TipoVoto"][v["tipoVoto"]],
            "quantidadeVotos": v["quantidadeVotos"],
            "partido": None if ident is None else ident["partido"],
            "codigo": None if ident is None else ident["codigo"],
            "ordemGeracaoHash": v["ordemGeracaoHash"],
            "hash": v["hash"].hex(),
        }

    def eleicao(r):
        return {
            "idEleicao": r["idEleicao"],
            "qtdEleitoresAptos": r["qtdEleitoresAptos"],
            "qtdEleitoresAptosSecao": r["qtdEleitoresAptosSecao"],
            "qtdEleitoresAptosTTE": r["qtdEleitoresAptosTTE"],
            "resultadosVotacao": [
                {
                    "tipoCargo": e["TipoCargoConsulta"][rv["tipoCargo"]],
                    "qtdComparecimento": rv["qtdComparecimento"],
                    "totaisVotosCargo": [
                        {
                            "codigoCargo": cargo(t["codigoCargo"]),
                            "ordemImpressao": t["ordemImpressao"],
                            "votosVotaveis": [votavel(v) for v in t["votosVotaveis"]],
                        }
                        for t in rv["totaisVotosCargo"]
                    ],
                }
                for rv in r["resultadosVotacao"]
            ],
            "ultimoHashVotosVotavel": r["ultimoHashVotosVotavel"].hex(),
            "assinaturaUltimoHashVotosVotavel": r[
                "assinaturaUltimoHashVotosVotavel"
            ].hex(),
        }

    u = bu["urna"]
    cg = u["correspondenciaResultado"]["carga"]
    alt, dados = bu["dadosSecaoSA"]
    hist = bu.get("historicoVotoImpresso")
    return {
        "envelope": {
            "cabecalho": cab(env["cabecalho"]),
            "fase": e["Fase"][env["fase"]],
            "temUrna": "urna" in env,
            "identificacao": id_urna(env["identificacao"]),
            "tipoEnvelope": e["TipoEnvelope"][env["tipoEnvelope"]],
            "cifrado": "seguranca" in env,
        },
        "bu": {
            "cabecalho": cab(bu["cabecalho"]),
            "fase": e["Fase"][bu["fase"]],
            "urna": {
                "tipoUrna": e["TipoUrna"][u["tipoUrna"]],
                "versaoVotacao": u["versaoVotacao"],
                "correspondenciaResultado": {
                    "identificacao": id_urna(
                        u["correspondenciaResultado"]["identificacao"]
                    ),
                    "carga": {
                        "numeroInternoUrna": cg["numeroInternoUrna"],
                        "numeroSerieFC": cg["numeroSerieFC"].hex(),
                        "identificadorGeradorMidia": dict(
                            cg["identificadorGeradorMidia"]
                        ),
                        "dataHoraCarga": cg["dataHoraCarga"],
                        "codigoCarga": cg["codigoCarga"],
                    },
                },
                "tipoArquivo": e["TipoArquivo"][u["tipoArquivo"]],
                "numeroSerieFV": u["numeroSerieFV"].hex(),
                "motivoUtilizacaoSA": motivo(u.get("motivoUtilizacaoSA")),
            },
            "identificacaoSecao": secao(bu["identificacaoSecao"]),
            "dataHoraEmissao": bu["dataHoraEmissao"],
            "dadosSecao": (
                {
                    "dataHoraAbertura": dados["dataHoraAbertura"],
                    "dataHoraEncerramento": dados["dataHoraEncerramento"],
                    "dataHoraDesligamentoVotoImpresso": dados.get(
                        "dataHoraDesligamentoVotoImpresso"
                    ),
                }
                if alt == "dadosSecao"
                else None
            ),
            "dadosSA": (
                {
                    "juntaApuradora": dados["juntaApuradora"],
                    "turmaApuradora": dados["turmaApuradora"],
                    "numeroInternoUrnaOrigem": dados.get("numeroInternoUrnaOrigem"),
                }
                if alt == "dadosSA"
                else None
            ),
            "qtdEleitoresCompareceram": bu["qtdEleitoresCompareceram"],
            "detalhamentoComparecimento": bu.get("detalhamentoComparecimento"),
            "resultadosVotacaoPorEleicao": [
                eleicao(r) for r in bu["resultadosVotacaoPorEleicao"]
            ],
            "historicoCodigosCarga": list(bu["historicoCodigosCarga"]),
            "historicoVotoImpresso": None if hist is None else [dict(h) for h in hist],
        },
    }


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("uso: python scripts/bu-referencia.py arquivo-bu.dat")
    conv = asn1tools.compile_files(str(SPEC), codec="ber")
    env = conv.decode("EntidadeEnvelopeGenerico", Path(sys.argv[1]).read_bytes())
    bu = conv.decode("EntidadeBoletimUrna", env["conteudo"])
    e = enumeracoes(SPEC.read_text(encoding="utf-8"))
    json.dump(converter(env, bu, e), sys.stdout, ensure_ascii=False, indent=1)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
