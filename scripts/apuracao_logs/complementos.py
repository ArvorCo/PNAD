"""BUs recuperados após lacuna da coleta antiga, sem reescrever o banco histórico."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from datetime import datetime, timezone

import asn1tools
import requests

from .coleta import BASE, DESTINO, HEADERS, ROOT

PASTA = ROOT / "data/originals/tse_logs_2026/complementos"
MANIFESTO = ROOT / "analysis/apuracao_2026/logs_urnas/complementos.json"
LACUNAS = ROOT / "analysis/apuracao_2026/logs_urnas/lacunas.json"
SPEC = ROOT / "apuracao/scripts/secoes/bu.asn1"


def registros_sa() -> dict:
    """Endereços do logSA na evidência preservada; não são ciclos do VOTA."""
    if not LACUNAS.exists():
        return {}
    resultado = {}
    for r in json.loads(LACUNAS.read_text())["linhas"]:
        if r.get("tipo_arquivo_bu") not in (3, 4, 5, 6):
            continue
        raw = (ROOT / r["arquivo"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == r["sha256"]
        for h in json.loads(raw).get("hashes", []):
            if h["hash"] != r["hash_anterior"]:
                continue
            arquivos = [a["nm"] for a in h["arq"] if a.get("tp") == "logsa"]
            assert len(arquivos) <= 1
            if arquivos:
                uf, mun, z, s = r["uf"].lower(), r["mun"], r["zona"], r["secao"]
                assert arquivos[0] == f"o03220{uf}{mun}{z:04d}{s:04d}-logsa.jez"
                resultado[(uf, mun, z, s)] = {
                    "url": f"{BASE}/{uf}/{mun}/{z:04d}/{s:04d}/{h['hash']}/{arquivos[0]}",
                    "metadados_url": r["url"],
                    "metadados_sha256": r["sha256"],
                    "analisado": False,
                }
    return resultado


def ler_bu(raw: bytes, chave: tuple, leitor) -> dict:
    env = leitor.decode("EntidadeEnvelopeGenerico", raw)
    bu = leitor.decode("EntidadeBoletimUrna", env["conteudo"])
    uf, mun, zona, secao = chave
    ident = bu["identificacaoSecao"]
    assert (
        ident["municipioZona"]["municipio"],
        ident["municipioZona"]["zona"],
        ident["secao"],
    ) == (int(mun), zona, secao)
    assert bu["fase"] == 2 and bu["cabecalho"]["idEleitoral"] == ("idPleito", 3220)
    urna = bu["urna"]
    det = bu.get("detalhamentoComparecimento", {})
    return {
        "uf": uf,
        "mun": mun,
        "zona": zona,
        "secao": secao,
        "numero_interno_urna": urna["correspondenciaResultado"]["carga"][
            "numeroInternoUrna"
        ],
        "comparecimento": bu["qtdEleitoresCompareceram"],
        "hab_biometria": det.get("qtdEleitoresHabilitadosPorBiometria"),
        "hab_ano_nascimento": det.get("qtdEleitoresHabilitadosPorBiografia"),
        "comp_sem_biometria": det.get("qtdEleitoresCompareceramSemBiometria"),
        "modelo_urna": None,
        "tipo_urna": urna["tipoUrna"],
        "tipo_arquivo": urna["tipoArquivo"],
        "n_cargas": len(bu["historicoCodigosCarga"]),
        "fase": 2,
        "pleito": 3220,
    }


def carregar() -> dict:
    if not MANIFESTO.exists():
        return {}
    registros = {
        (r["uf"], r["mun"], r["zona"], r["secao"]): r
        for r in json.loads(MANIFESTO.read_text())["linhas"]
    }
    for r in registros.values():
        for nome in ("fonte_bu", "fonte_aux"):
            fonte = r[nome]
            assert (
                hashlib.sha256((ROOT / fonte["arquivo"]).read_bytes()).hexdigest()
                == fonte["sha256"]
            )
    return registros


def enderecos() -> dict:
    """Local identificado no BU; endereço só quando existe no cadastro público."""
    registros = carregar()
    if not registros:
        return {}
    leitor = asn1tools.compile_files(str(SPEC), codec="ber", numeric_enums=True)
    resultado = {}
    for r in registros.values():
        env = leitor.decode(
            "EntidadeEnvelopeGenerico", (ROOT / r["fonte_bu"]["arquivo"]).read_bytes()
        )
        bu = leitor.decode("EntidadeBoletimUrna", env["conteudo"])
        uf, mun, z, s = r["uf"].upper(), r["mun"], r["zona"], r["secao"]
        local_id = f"{uf}-{mun}-{z}-{bu['identificacaoSecao']['local']}"
        cad = json.loads(
            (ROOT / f"docs/assets/politize/dados/mun/{uf}/{mun}.json").read_text()
        )
        locais = [
            dict(zip(cad["locais"]["colunas"], v, strict=True))
            for v in cad["locais"]["linhas"]
        ]
        loc = next((v for v in locais if v["local_id"] == local_id), {})
        resultado[f"{uf}-{z}-{s}"] = {
            "uf": uf,
            "mun": mun,
            "municipio": cad["nome"],
            "zona": z,
            "secao": s,
            "local_id": local_id,
            "local": loc.get("nome"),
            "local_disponivel": bool(loc),
            "comparecimento": r["bu"]["comparecimento"],
            **{
                k: loc.get(k)
                for k in ("endereco", "bairro", "cep", "lat", "lon", "coord_fonte")
            },
        }
    return resultado


def preparar():
    """Arquiva BUs de lacunas anteriores; não toca no SQLite em coleta."""
    if MANIFESTO.exists():
        print(
            f"{len(carregar())} BUs suplementares já preservados e hashes conferidos."
        )
        return
    PASTA.mkdir(parents=True, exist_ok=True)
    leitor = asn1tools.compile_files(str(SPEC), codec="ber", numeric_enums=True)
    linhas = []
    with requests.Session() as sessao:
        sessao.headers.update(HEADERS)
        for r in json.loads(LACUNAS.read_text())["linhas"]:
            if r["hash_anterior"] is not None or r.get("status_atual") != "Totalizada":
                continue
            aux_raw = (ROOT / r["arquivo"]).read_bytes()
            assert hashlib.sha256(aux_raw).hexdigest() == r["sha256"]
            aux = json.loads(aux_raw)
            # Mais de uma versão exige escolha explícita; nunca adivinhar o hash.
            assert len(aux["hashes"]) == 1
            h = aux["hashes"][0]
            bus = [a["nm"] for a in h["arq"] if a["nm"].endswith("-bu.dat")]
            logs = [a["nm"] for a in h["arq"] if a["nm"].endswith("-log.jez")]
            assert len(bus) == len(logs) == 1
            uf, mun, z, s = r["uf"].lower(), r["mun"], r["zona"], r["secao"]
            prefixo = f"o03220{uf}{mun}{z:04d}{s:04d}"
            assert bus[0] == prefixo + "-bu.dat" and logs[0] == prefixo + "-log.jez"
            url = f"{BASE}/{uf}/{mun}/{z:04d}/{s:04d}/{h['hash']}/{bus[0]}"
            resposta = sessao.get(url, timeout=(10, 40))
            resposta.raise_for_status()
            bu = ler_bu(resposta.content, (uf, mun, z, s), leitor)
            path = PASTA / bus[0]
            path.write_bytes(resposta.content)
            linhas.append(
                {
                    "uf": uf,
                    "mun": mun,
                    "zona": z,
                    "secao": s,
                    "hash": h["hash"],
                    "nome": logs[0],
                    "bu": bu,
                    "fonte_bu": {
                        "url": url,
                        "sha256": hashlib.sha256(resposta.content).hexdigest(),
                        "arquivo": str(path.relative_to(ROOT)),
                    },
                    "fonte_aux": {
                        "url": r["url"],
                        "sha256": r["sha256"],
                        "arquivo": r["arquivo"],
                    },
                    "obtido_em": datetime.now(timezone.utc).isoformat(),
                    "motivo": "Metadados indisponíveis na coleta anterior; BU e log agora publicados no único hash disponível.",
                }
            )
            time.sleep(0.25)
    MANIFESTO.write_text(
        json.dumps({"linhas": linhas}, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"{len(linhas)} BUs suplementares preservados; catálogo ainda não alterado.")


def aplicar():
    """Executar só após encerrar o coletor: um escritor por banco."""
    con = sqlite3.connect(DESTINO)
    with con:
        for chave, r in carregar().items():
            anterior = con.execute(
                "SELECT hash,nome FROM catalogo WHERE uf=? AND mun=? AND zona=? AND secao=?",
                chave,
            ).fetchone()
            assert anterior in ((None, None), (r["hash"], r["nome"]))
            con.execute(
                "UPDATE catalogo SET hash=?,nome=? WHERE uf=? AND mun=? AND zona=? AND secao=?",
                (r["hash"], r["nome"], *chave),
            )
        con.executemany(
            "INSERT OR REPLACE INTO meta VALUES (?,?)",
            [
                ("complementos_aplicados_em", datetime.now(timezone.utc).isoformat()),
                (
                    "complementos_manifesto_sha256",
                    hashlib.sha256(MANIFESTO.read_bytes()).hexdigest(),
                ),
            ],
        )
    con.close()
    print("Catálogo complementado; execute novamente coleta e processamento.")
