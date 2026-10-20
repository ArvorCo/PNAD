"""Camada de mudanças de endereço do 2º turno no mapa de fiscais.

Lê ``docs/assets/politize/dados/mudancas`` (união do arquivo de locais do TSE e do painel de
seções alteradas) e acrescenta a coluna ``mudanca`` às seções do mapa. A seção que mudou e
ainda não estava no acervo ganha uma linha de nível ``mudanca``, sem pontuação histórica, com
aptos e placar do 1º turno vindos do Politize. Quando há coordenada do local do 2º turno, o
ponto da seção passa a ser o prédio novo (``local_id`` sintético ``<local>-2T<hash>``); o
endereço do 1º turno, e o ``id_1t`` do prédio antigo, ficam no objeto ``mudanca``. Sem
coordenada nova, o ponto continua no prédio do 1º turno e a ficha avisa.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MUDANCAS = ROOT / "docs/assets/politize/dados/mudancas"
CRITERIO = "mudanca_endereco"
NOME = "Mudou de endereço para o 2º turno"
FRASE = "A seção vota em outro endereço em 25/10."
NOTA = (
    "A lista é a união do arquivo de locais de votação do TSE (18/10) e do painel de seções "
    "alteradas do TSE. Onde só uma das duas fontes mostra a mudança, as fontes divergem: "
    "confira no e-Título."
)
# mesma caixa do território usada pelo build do mapa
LAT_MIN, LAT_MAX, LON_MIN, LON_MAX = -34.0, 5.5, -74.5, -28.5
CAMPOS = (
    "nome_1t",
    "end_1t",
    "bairro_1t",
    "nome_2t",
    "end_2t",
    "bairro_2t",
    "cep_2t",
    "distancia_m",
    "eleitores",
    "maps_novo",
    "motivo_tre",
    "url_tre",
    "grau_tre",
    "agregada_a",
)


def _limpa(texto):
    return " ".join(str(texto).split()) if texto else texto


def _coord(uf, lat, lon):
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return False
    if uf == "ZZ":
        return -90 <= lat <= 90 and -180 <= lon <= 180
    return LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX


def carregar(base: Path = MUDANCAS):
    """``(indice, {(uf, zona, secao): registro})`` ou ``(None, {})`` sem a camada."""
    caminho = base / "indice.json"
    if not caminho.exists():
        return None, {}
    indice = json.loads(caminho.read_text(encoding="utf-8"))
    registros = {}
    for arq in sorted(base.glob("*/*.json")):
        d = json.loads(arq.read_text(encoding="utf-8"))
        for secao, reg in d["secoes"].items():
            registros[(d["uf"], int(d["zona"]), int(secao))] = reg
    return indice, registros


def objeto(uf, reg, indice, id_1t):
    """O objeto ``mudanca`` do contrato (campos extras ficam para a ficha)."""
    cat = reg["categoria"]
    info = indice["categorias"].get(cat, {})
    com_coord = _coord(uf, reg.get("lat_2t"), reg.get("lon_2t"))
    o = {
        "cat": cat,
        "nome_cat": info.get("nome"),
        "frase": reg.get("frase") or info.get("frase"),
        "fonte": reg["fonte"],
        "real": bool(reg.get("mudanca_real")),
        "id_1t": id_1t,
        "lat_2t": reg["lat_2t"] if com_coord else None,
        "lon_2t": reg["lon_2t"] if com_coord else None,
        "coord_2t": com_coord,
    }
    for campo in CAMPOS:
        valor = reg.get(campo)
        o[campo] = _limpa(valor) if isinstance(valor, str) else valor
    return o


def _id_destino(uf, mun, zona, o):
    base = "|".join(
        str(o.get(k) or "") for k in ("nome_2t", "end_2t", "cep_2t", "lat_2t", "lon_2t")
    )
    return f"{uf}-{mun}-{zona}-2T{hashlib.sha1(base.encode()).hexdigest()[:6]}"


def aplicar(linhas, antigos, cadastro, base: Path | None = None):
    """Anexa ``mudanca`` às linhas, cria as que faltam e move o ponto para o prédio novo.

    ``linhas`` e ``antigos`` são os da ``integrar`` (``antigos`` indexa por
    ``(uf, zona, secao)``); ``cadastro`` é o ``Cadastro`` do Politize; ``base`` é a pasta
    ``mudancas`` do mesmo cadastro (a padrão é a publicada). Devolve o bloco ``mudancas``
    do índice, ou ``None`` se a camada não existe.
    """
    indice, registros = carregar(base or MUDANCAS)
    if indice is None:
        return None
    novas = 0
    for (uf, z, s), reg in sorted(registros.items()):
        zona = cadastro.zona(uf, z)
        principal = zona.get(int(reg["agregada_a"])) if reg.get("agregada_a") else None
        sec = zona.get(s) or principal
        r = antigos.get((uf, z, s))
        if r is None:
            if not sec:
                raise ValueError(f"Mudança sem vínculo cadastral: {uf}-{z}-{s}")
            mun = str(sec["mun_tse"])
            nome, locais = cadastro.municipio(uf, mun)
            loc = locais.get(sec["local_id"], {})
            r = {
                "uf": uf,
                "mun": mun,
                "municipio": nome or "",
                "zona": z,
                "secao": s,
                "local_id": sec["local_id"],
                "local": sec.get("local") or reg.get("nome_1t"),
                "endereco": loc.get("endereco") or reg.get("end_1t"),
                "bairro": loc.get("bairro") or reg.get("bairro_1t"),
                "cep": loc.get("cep"),
                "lat": loc.get("lat"),
                "lon": loc.get("lon"),
                "coord_fonte": loc.get("coord_fonte"),
                "nivel": "mudanca",
                "pontuacao": None,
                "criterios": "",
                "explicacao": None,
                "risco": None,
                "aptos": reg.get("eleitores") if not zona.get(s) else sec.get("aptos"),
                "flavio_pct": None,
                "lula_pct": None,
                "originais": False,
                "logs": [],
            }
            antigos[(uf, z, s)] = r
            linhas.append(r)
            novas += 1
        o = objeto(uf, reg, indice, r["local_id"])
        r["mudanca"] = o
        if o["coord_2t"]:
            mun = r.get("mun")
            r["local_id"] = _id_destino(uf, mun, z, o)
            r["local"] = o["nome_2t"]
            r["endereco"] = o["end_2t"]
            r["bairro"] = o["bairro_2t"]
            r["cep"] = o["cep_2t"]
            r["lat"], r["lon"] = o["lat_2t"], o["lon_2t"]
            r["coord_fonte"] = "local_2t"
    total = sum(1 for r in linhas if r.get("mudanca"))
    if total != indice["total_secoes"]:
        raise ValueError(
            f"Mudanças no mapa ({total}) diferem do índice ({indice['total_secoes']})"
        )
    eleitores = sum(r["mudanca"]["eleitores"] or 0 for r in linhas if r.get("mudanca"))
    return {
        "id": CRITERIO,
        "nome": NOME,
        "frase": FRASE,
        "nota": NOTA,
        "secoes": total,
        "eleitores": eleitores,
        "secoes_novas_no_mapa": novas,
        "com_ponto_no_local_novo": sum(
            1 for r in linhas if r.get("mudanca") and r["mudanca"]["coord_2t"]
        ),
        "por_categoria": dict(
            sorted(
                Counter(r["mudanca"]["cat"] for r in linhas if r.get("mudanca")).items()
            )
        ),
        "por_fonte": dict(
            sorted(
                Counter(
                    r["mudanca"]["fonte"] for r in linhas if r.get("mudanca")
                ).items()
            )
        ),
        "categorias": indice["categorias"],
        "gerado_em": indice.get("gerado_em"),
    }
