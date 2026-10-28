"""Cruza locais cadastrais com os rasters públicos GENI/Fogo Cruzado de 2024."""

import base64
import hashlib
import io
import json
import math
from collections import defaultdict

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

from .dados import OUTPUT, ROOT, ler, linhas

FONTE = ROOT / "data/originals/analise_realidade_eleicao"
GRUPOS = ("ADA", "CV", "Milícia", "TCP")
RAIO_TERRA = 6378137


def mercator(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def pixel(lat, lon, bounds, width, height):
    """Reproduz degree2tile do renderer, não o popup linear em latitude."""
    (north, west), (south, east) = bounds
    if not (south < lat <= north and west <= lon < east):
        return None
    x = math.floor((lon - west) / (east - west) * width)
    y = math.floor(
        (mercator(north) - mercator(lat)) / (mercator(north) - mercator(south)) * height
    )
    return min(width - 1, x), min(height - 1, y)


def carregar_camadas():
    raw = (FONTE / "geni_mapa_2024_widget.json").read_bytes()
    meta = ler(FONTE / "geni_mapa_2024.fonte.json")
    assert hashlib.sha256(raw).hexdigest() == meta["sha256_widget"]
    calls = json.loads(raw)["x"]["calls"]
    legends = {
        c["args"][0]["group"]: dict(
            zip(c["args"][0]["colors"], c["args"][0]["labels"], strict=True)
        )
        for c in calls
        if c["method"] == "addLegend"
    }
    layers = {}
    for c in calls:
        if c["method"] != "addRasterImage":
            continue
        uri, bounds, _, group, _ = c["args"]
        rgba = np.asarray(Image.open(io.BytesIO(base64.b64decode(uri.split(",")[1]))))
        ids = np.zeros(rgba.shape[:2], dtype=np.uint8)
        palette = legends[group]
        for color, label in palette.items():
            rgb = [int(color[i : i + 2], 16) for i in (1, 3, 5)]
            ids[(rgba[:, :, :3] == rgb).all(axis=2) & (rgba[:, :, 3] >= 10)] = (
                GRUPOS.index(label) + 1
            )
        assert not np.any((rgba[:, :, 3] >= 10) & (ids == 0)), "Cor desconhecida"
        # Distância conservadora à borda do pixel distinto: menor escala terrestre
        # da janela, menos a diagonal de um pixel (posição subpixel desconhecida).
        h, w = ids.shape
        (north, west), (south, east) = bounds
        scale = min(math.cos(math.radians(north)), math.cos(math.radians(south)))
        dx = RAIO_TERRA * math.radians(east - west) / w * scale
        dy = RAIO_TERRA * (mercator(north) - mercator(south)) / h * scale
        distances = np.zeros(ids.shape, dtype=np.float32)
        for k in range(1, 5):
            mask = ids == k
            padded = np.pad(mask, 1, constant_values=False)
            dist = distance_transform_edt(padded, sampling=(dy, dx))[1:-1, 1:-1]
            distances[mask] = np.maximum(0, dist[mask] - math.hypot(dx, dy))
        key = "controle" if group.startswith("Controle") else "influencia"
        layers[key] = {
            "ids": ids,
            "distancias": distances,
            "bounds": bounds,
            "uri": uri,
            "pixel_m": [dx, dy],
            "cores": palette,
        }
    return layers, meta


def classificar(layer, lat, lon):
    h, w = layer["ids"].shape
    pos = pixel(lat, lon, layer["bounds"], w, h)
    if pos is None:
        return None, None
    x, y = pos
    k = int(layer["ids"][y, x])
    return (GRUPOS[k - 1] if k else "Sem marcação"), float(layer["distancias"][y, x])


def somar(rows):
    f, votos_lula = (sum(r[k] for r in rows) for k in ("flavio", "lula"))
    return {
        "locais": len(rows),
        "secoes": sum(r["secoes"] for r in rows),
        "flavio": f,
        "lula": votos_lula,
        "validos": f + votos_lula,
        "pct_lula": 100 * votos_lula / (f + votos_lula) if f + votos_lula else None,
        "pct_flavio": 100 * f / (f + votos_lula) if f + votos_lula else None,
    }


def construir():
    layers, meta = carregar_camadas()
    rows, excluidos, hashes = [], defaultdict(int), {}
    for p in sorted((ROOT / "docs/assets/politize_se/dados/mun/RJ").glob("*.json")):
        m = ler(p)
        oldpath = ROOT / f"docs/assets/politize/dados/mun/RJ/{p.name}"
        old = {r["local_id"]: r for r in linhas(ler(oldpath)["locais"])}
        for path in (p, oldpath):
            hashes[str(path.relative_to(ROOT))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
        for r in linhas(m["locais"]):
            prev = old.get(r["local_id"], {})
            if (
                prev.get("coord_fonte") != "cadastro"
                or r["lat"] is None
                or r["lon"] is None
            ):
                excluidos["sem_coordenada_cadastral"] += 1
                continue
            if (
                r["n_secoes"] != r["n_bu2"]
                or r["flavio2"] is None
                or r["lula2"] is None
            ):
                excluidos["bu_incompleto"] += 1
                continue
            control, dist = classificar(layers["controle"], r["lat"], r["lon"])
            if control is None:
                excluidos["fora_janela"] += 1
                continue
            infl, dist_infl = classificar(layers["influencia"], r["lat"], r["lon"])
            rows.append(
                {
                    "local_id": r["local_id"],
                    "municipio": m["nome"],
                    "mun_tse": m["mun_tse"],
                    "zona": r["zona"],
                    "nome": r["nome"],
                    "lat": r["lat"],
                    "lon": r["lon"],
                    "coord_fonte": "cadastro",
                    "secoes": r["n_secoes"],
                    "flavio": r["flavio2"],
                    "lula": r["lula2"],
                    "controle": control,
                    "influencia": infl,
                    "interior_controle_m": round(dist, 1),
                    "interior_influencia_m": round(dist_infl, 1),
                    "link": r["link"],
                }
            )
    resumo = []
    for layer in layers:
        for group in (*GRUPOS, "Sem marcação"):
            for margem in (0, 100, 300):
                if group == "Sem marcação" and margem:
                    continue
                subset = [
                    r
                    for r in rows
                    if r[layer] == group and r[f"interior_{layer}_m"] >= margem
                ]
                resumo.append(
                    {
                        "camada": layer,
                        "grupo": group,
                        "margem_m": margem,
                        **somar(subset),
                    }
                )
    recortes = []
    for layer in layers:
        for nivel in ("municipio", "zona"):
            groups = defaultdict(list)
            for r in rows:
                if r[layer] == "Sem marcação":
                    continue
                zone = r["zona"] if nivel == "zona" else None
                groups[(r["municipio"], r["mun_tse"], zone, r[layer])].append(r)
            for (mun, code, zona, group), subset in sorted(groups.items()):
                recortes.append(
                    {
                        "camada": layer,
                        "nivel": nivel,
                        "municipio": mun,
                        "mun_tse": code,
                        "zona": zona,
                        "grupo": group,
                        **somar(subset),
                    }
                )
    return {
        "fonte": meta,
        "hashes_locais": hashes,
        "excluidos_rj": dict(excluidos),
        "janela": layers["controle"]["bounds"],
        "pixel_m_conservador": layers["controle"]["pixel_m"],
        "referencias": [
            {k: m[k] for k in ("nome", "sede_lat", "sede_lon")}
            for m in ler(OUTPUT / "dados.json")["municipios"]
            if m["ibge"] in ("3304557", "3303302", "3303500", "3301702", "3304904")
        ],
        "total_janela": somar(rows),
        "resumo": resumo,
        "recortes": recortes,
        "locais": rows,
        "sobreposicao_controle_influencia": somar(
            [
                r
                for r in rows
                if r["controle"] != "Sem marcação" and r["influencia"] != "Sem marcação"
            ]
        ),
        "metodo": "Interseção pontual em Web Mercator, mesma transformação do renderer oficial. Cores exatas da legenda, sem interpolação. Somente coordenadas cadastrais e BUs completos. Sensibilidades retiram locais a menos de 100/300 m da borda de outra classe, com distância conservadora descontando diagonal do pixel. Não são intervalos de confiança nem erros de geocodificação conhecidos.",
        "limites": "Território de 2024, voto de 2026. Camada de imagem, não vetores originais; resolução aproximada de 34×37 m. Coordenadas não auditadas em campo. Sem marcação não significa ausência de domínio. Janela é a extensão retangular publicada, não a fronteira administrativa da RMRJ. Local de votação não identifica residência, escolha individual, vínculo com grupo ou coação. Controle e influência são análises separadas e não devem ser somados.",
    }


def main():
    d = construir()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "territorio.json").write_text(
        json.dumps(d, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n"
    )
    print(
        json.dumps(
            {k: d[k] for k in ("total_janela", "excluidos_rj", "resumo")},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
