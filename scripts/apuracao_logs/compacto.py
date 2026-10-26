"""Guarda compacta do log do 2º turno sem perder evidência.

Em 2026 a mesma carga serviu aos dois turnos: o ``logd.dat`` do 2º turno começa,
em regra, com o mesmo conteúdo do log do 1º turno já preservado em
``logs.sqlite`` e acrescenta o dia 25/10. Guardar o ZIP inteiro dos dois turnos
excede o disco (estimativa no contrato). O modo compacto guarda:

* ``prefixo_1t``: quando o texto do log do 1º turno da mesma seção é prefixo
  byte a byte do texto do 2º, só o restante vai comprimido em xz, e o prefixo
  fica por referência (chave da seção, SHA-256 do ZIP e do texto do 1º turno).
  As linhas de metadado do prefixo (identidade, modelo, fase, carga, ajuste de
  relógio) seguem em cópia, para o leitor; a contagem do prefixo vai junto.
* ``xz_completo``: sem prefixo verificável (urna diferente, reserva, vários
  membros), o texto inteiro de cada membro vai em xz.
* ``zip``: ZIP aninhado ou membro não textual; guarda-se o original.

Em todos os casos ficam o SHA-256 do ZIP original, o diretório do ZIP (nome,
tamanho, CRC-32 de cada membro) e o SHA-256 do texto completo; ``reconstruir``
refaz o texto e confere esse hash. O ZIP original pode ser baixado de novo pelo
endereço oficial e conferido pelo SHA-256 registrado.
"""

from __future__ import annotations

import hashlib
import io
import json
import lzma
import zipfile
import zlib

PREFIXOS_META = (
    "Município:",
    "Zona Eleitoral:",
    "Seção Eleitoral:",
    "Fase da UE:",
    "Código de carga ",
    "Identificador da mídia de carga:",
    "Ajuste de Data e Hora ",
    "Data e hora que foi digitada pelo operador:",
)


def _manter(linha: bytes) -> bool:
    """Metadado que o leitor usa, ou linha malformada (contada como inválida)."""
    a = linha.split(b"\t")
    if len(a) != 6:
        return bool(linha.strip())
    msg = a[4].decode("latin1")
    return msg.startswith(PREFIXOS_META) or "Modelo de Urna:" in msg


def membros(raw: bytes) -> list[tuple[zipfile.ZipInfo, bytes]] | None:
    """Membros de texto de primeiro nível; ``None`` quando há aninhamento."""
    out = []
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            conteudo = z.read(info)
            if conteudo.startswith(b"PK\x03\x04") or not info.filename.lower().endswith(
                (".dat", ".txt", ".log")
            ):
                return None
            out.append((info, conteudo))
    return out


def texto_1t(raw_1t: bytes | None) -> bytes | None:
    if not raw_1t:
        return None
    m = membros(raw_1t)
    if not m or len(m) != 1:
        return None
    return m[0][1]


def empacotar(raw: bytes, raw_1t: bytes | None = None) -> dict:
    """Pacote compacto de um ZIP de log; ``raw_1t`` é o ZIP do 1º turno da seção."""
    sha_zip = hashlib.sha256(raw).hexdigest()
    m = membros(raw)
    base = {"sha256_zip": sha_zip, "bytes_zip": len(raw)}
    if m is None:
        return {**base, "formato": "zip", "blob": raw, "diretorio": None}
    diretorio = [
        {
            "nome": info.filename,
            "bytes": info.file_size,
            "crc32": info.CRC,
            "sha256": hashlib.sha256(c).hexdigest(),
        }
        for info, c in m
    ]
    anterior = texto_1t(raw_1t)
    if (
        len(m) == 1
        and anterior
        and anterior.endswith(b"\n")
        and m[0][1].startswith(anterior)
    ):
        texto = m[0][1]
        resto = texto[len(anterior) :]
        linhas_prefixo = anterior.split(b"\n")
        meta = b"\n".join(x for x in linhas_prefixo if _manter(x))
        nao_meta = sum(1 for x in linhas_prefixo if x.strip() and not _manter(x))
        corpo = (
            json.dumps(
                {"meta_prefixo": len(meta), "resto": len(resto)}, separators=(",", ":")
            ).encode()
            + b"\n"
            + meta
            + resto
        )
        return {
            **base,
            "formato": "prefixo_1t",
            "diretorio": diretorio,
            "sha256_prefixo": hashlib.sha256(anterior).hexdigest(),
            "sha256_zip_1t": hashlib.sha256(raw_1t).hexdigest(),
            "linhas_prefixo_omitidas": nao_meta,
            "blob": lzma.compress(corpo, preset=6),
        }
    corpo = b"".join(
        json.dumps(
            {"nome": info.filename, "bytes": len(c)}, ensure_ascii=False
        ).encode()
        + b"\n"
        + c
        for info, c in m
    )
    return {
        **base,
        "formato": "xz_completo",
        "diretorio": diretorio,
        "blob": lzma.compress(corpo, preset=6),
    }


def ler_para_analise(pacote: dict) -> tuple[list[tuple[str, str]], int]:
    """Textos para ``parser.analisar_textos`` e linhas omitidas por referência."""
    if pacote["formato"] == "zip":
        from .parser import textos_zip

        return textos_zip(pacote["blob"]), 0
    corpo = lzma.decompress(pacote["blob"])
    if pacote["formato"] == "prefixo_1t":
        cab, _, resto = corpo.partition(b"\n")
        n = json.loads(cab)
        meta, cauda = resto[: n["meta_prefixo"]], resto[n["meta_prefixo"] :]
        assert len(cauda) == n["resto"]
        nome = pacote["diretorio"][0]["nome"]
        texto = (
            meta
            + (b"\n" if meta and cauda and not cauda.startswith(b"\n") else b"")
            + cauda
        )
        return [(nome, texto.decode("latin1"))], pacote["linhas_prefixo_omitidas"]
    return [(nome, c.decode("latin1")) for nome, c in _membros_xz(corpo)], 0


def _membros_xz(corpo: bytes) -> list[tuple[str, bytes]]:
    out, pos = [], 0
    while pos < len(corpo):
        fim = corpo.index(b"\n", pos)
        cab = json.loads(corpo[pos:fim])
        pos = fim + 1
        out.append((cab["nome"], corpo[pos : pos + cab["bytes"]]))
        pos += cab["bytes"]
    return out


def reconstruir(pacote: dict, raw_1t: bytes | None = None) -> list[tuple[str, bytes]]:
    """Texto integral de cada membro, conferido contra CRC-32 e SHA-256 do original."""
    if pacote["formato"] == "zip":
        assert hashlib.sha256(pacote["blob"]).hexdigest() == pacote["sha256_zip"]
        return [(i.filename, c) for i, c in membros(pacote["blob"]) or []]
    corpo = lzma.decompress(pacote["blob"])
    if pacote["formato"] == "prefixo_1t":
        assert raw_1t is not None, "prefixo guardado por referência ao 1º turno"
        assert hashlib.sha256(raw_1t).hexdigest() == pacote["sha256_zip_1t"]
        anterior = texto_1t(raw_1t)
        cab, _, resto = corpo.partition(b"\n")
        n = json.loads(cab)
        textos = [
            (pacote["diretorio"][0]["nome"], anterior + resto[n["meta_prefixo"] :])
        ]
    else:
        textos = _membros_xz(corpo)
    for (nome, c), d in zip(textos, pacote["diretorio"], strict=True):
        assert nome == d["nome"] and len(c) == d["bytes"]
        assert (
            zlib.crc32(c) == d["crc32"] and hashlib.sha256(c).hexdigest() == d["sha256"]
        )
    return textos
