"""Exporta documentação municipal e rasters GENI, sem inferir domínio municipal."""

import base64
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from analise_realidade_eleicao.territorio import carregar_camadas, classificar
from apuracao_2026.fiscais_territorio import _crime, referencias_crime

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs/assets/politize_se/seguranca"


def ler(path):
    return json.loads(path.read_text())


def tabela(d):
    return [dict(zip(d["colunas"], r, strict=True)) for r in d["linhas"]]


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    municipal = ROOT / "data/outputs/fiscais_risco_municipios.csv"
    contexto = ROOT / "analysis/apuracao_2026/dados/contexto_seguranca.json"
    with municipal.open(newline="", encoding="utf-8") as f:
        rows = {f"{r['uf']}-{r['mun_tse']}": r for r in csv.DictReader(f)}
    validos = {i["id"] for i in ler(contexto)["itens"] if i["tema"] == "faccao_milicia"}
    muns = {}
    for key, r in rows.items():
        crime = _crime(r, validos)
        # A matéria cita estas cidades como sedes de gabinetes, não como
        # ocorrência ou área de influência. Não transportar o falso positivo.
        if key in {"CE-14478", "CE-15598"} and crime:
            crime["fontes"] = [f for f in crime["fontes"] if f != "ctx-034"]
            if not crime["fontes"]:
                continue
        if crime and crime["status"] == "mapeamento público":
            muns[key] = {"nome": r["municipio"], "fontes": crime["fontes"]}
    layers, meta = carregar_camadas()
    cartografia = {}
    for key, layer in layers.items():
        arquivo = f"{key}-2024.png"
        raw = base64.b64decode(layer["uri"].split(",")[1])
        (DEST / arquivo).write_bytes(raw)
        cartografia[key] = {
            "arquivo": arquivo,
            "bounds": layer["bounds"],
            "cores": {label: color for color, label in layer["cores"].items()},
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    # Só classificar pontos cadastrais que ainda coincidem com o cadastro-fonte.
    originais = {}
    fontes = [municipal, contexto]
    for p in sorted((ROOT / "docs/assets/politize/dados/mun/RJ").glob("*.json")):
        originais.update({r["local_id"]: r for r in tabela(ler(p)["locais"])})
        fontes.append(p)
    mapa = ROOT / "docs/assets/politize_se_mapa/uf/RJ.json"
    fontes.append(mapa)
    locais = {}
    for r in tabela(ler(mapa)["locais"]):
        prev = originais.get(r["id"], {})
        cadastral = prev.get("coord_fonte") == "cadastro" and all(
            isinstance(r[k], (int, float))
            and isinstance(prev.get(k), (int, float))
            and abs(r[k] - prev[k]) < 0.00001
            for k in ("lat", "lon")
        )
        item = {"coordenada_cadastral": cadastral}
        for key, layer in layers.items():
            grupo, margem = (
                classificar(layer, r["lat"], r["lon"]) if cadastral else (None, None)
            )
            item[key] = grupo
            item[key + "_borda_m"] = round(margem, 1) if margem is not None else None
        locais[r["id"]] = item
    referencias = referencias_crime(rows, validos)
    referencias["fbsp-cartografias-amazonia-2025"] = (
        "FBSP / Instituto Mãe Crioula, Cartografias da Violência na Amazônia, "
        "novembro de 2025, quadros 3.2 a 3.10 por UF (campo nov/2024–set/2025), "
        "https://forumseguranca.org.br/wp-content/uploads/2025/11/"
        "cartografias-violencia-amazonia-2025.pdf"
    )
    out = {
        "versao": 1,
        "compilado": "2026-10-29",
        "municipios": muns,
        "referencias": referencias,
        "revisao": "Fontes consultadas em 29/10/2026. Sobral e Juazeiro do Norte removidos: ctx-034 cita sedes de gabinetes de segurança, não demonstra presença municipal. FBSP: 343 de 344 nomes associados ao TSE; Amanã/AM não associado. Presença municipal não implica controle de todos os bairros.",
        "locais_rj": locais,
        "cartografia": cartografia,
        "fonte_territorial": meta,
        "publicacao_territorial": "2025-12-04",
        "relatorio": "https://geni.uff.br/wp-content/uploads/sites/357/2025/12/Relatorio-Mapa-2025-Alt3.pdf",
        "nota": "Presença municipal não delimita área controlada. GENI/UFF e Fogo Cruzado: controle e influência em 2024, publicados em 2025; não são situação verificada em 2026. Interseção pontual em Web Mercator com raster de aproximadamente 34×37 m, só coordenadas cadastrais coincidentes. Sem marcação não comprova ausência. Nenhuma camada identifica voto, coação ou vínculo de moradores com grupos.",
        "contagens": {
            "municipios_documentados": len(muns),
            "municipios_fbsp": sum(
                "fbsp-cartografias-amazonia-2025" in " ".join(m["fontes"])
                for m in muns.values()
            ),
            "controle_rj": dict(
                Counter(r["controle"] or "Sem cobertura" for r in locais.values())
            ),
        },
    }
    (DEST / "dados.json").write_text(
        json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n"
    )
    (DEST / "proveniencia.json").write_text(
        json.dumps(
            {
                "fontes": {
                    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in fontes
                },
                "widget": meta,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(json.dumps(out["contagens"], ensure_ascii=False))


if __name__ == "__main__":
    main()
