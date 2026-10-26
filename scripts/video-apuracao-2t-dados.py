#!/usr/bin/env python3
"""Dados do vídeo "A noite do 2º turno" (video/apuracao_2t), lidos do dossiê da apuração.

Lê os blocos de `analysis/apuracao_2t_2026/dados/` (presidente, linha_do_tempo, projecao_noite,
comparacao_1t, abstencao, secoes_ranking, pesquisas_vs_urna, paralela, secoes, secoes_voto,
hipotese_autor) e a malha de UFs, e grava
`video/apuracao_2t/src/dados/apuracao_2t.json`, que o Remotion importa estaticamente.

Tolera ausência: o dossiê é escrito em paralelo e nem todo bloco existe ainda. Bloco que falta
entra em `pendentes`; a cena que o usa mostra "DADO PENDENTE" no lugar do número. O bundle do
Remotion carrega o JSON inteiro em toda cena, então chave de primeiro nível acima de
LIMITE_CHAVE bytes (os `municipios` e `secoes` por localidade, que o vídeo não desenha) é
omitida e listada em `avisos`; se o bloco ainda passar de LIMITE_BLOCO, não é embutido e vai
para `pendentes`. Todo arquivo lido tem o SHA-256
gravado em `fontes`. O mapa projetado por UF é o mesmo dos vídeos dos fiscais, da masterclass e
dos sete riscos.

Uso:
    python3 scripts/video-apuracao-2t-dados.py
"""

from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DADOS = ROOT / "analysis" / "apuracao_2t_2026" / "dados"
SAIDA = ROOT / "video" / "apuracao_2t" / "src" / "dados" / "apuracao_2t.json"
MALHA = ROOT / "apuracao" / "public" / "geo" / "br_uf.geojson"

BLOCOS = (
    "presidente",
    "linha_do_tempo",
    "projecao_noite",
    "comparacao_1t",
    "abstencao",
    "secoes_ranking",
    "pesquisas_vs_urna",
    "paralela",
    "secoes",
    "secoes_voto",
    "hipotese_autor",
    "logs",
    "rdv",
    "metadados",
    "transferencia",
)
LIMITE_CHAVE = 200_000
LIMITE_BLOCO = 600_000


def carregar(nome: str):
    """Importa um script de nome com hífen (scripts/ está no caminho) sem rodar o `main`."""
    return importlib.import_module(nome)


def tamanho_json(valor: object) -> int:
    return len(json.dumps(valor, ensure_ascii=False))


def enxugar(
    bloco: str, conteudo: object, avisos: list[str], profundidade: int = 2
) -> object:
    """Tira as chaves maiores que LIMITE_CHAVE e avisa quais e de que tamanho. Um dicionário
    grande demais desce um nível (até `profundidade`): fica com as subchaves que cabem, para que
    um resumo pequeno ao lado de uma lista pesada (`secoes.agregados.brasil` ao lado de
    `por_municipio`) continue embutido."""
    if not isinstance(conteudo, dict):
        return conteudo
    saida = {}
    for chave, valor in conteudo.items():
        tamanho = tamanho_json(valor)
        if tamanho <= LIMITE_CHAVE:
            saida[chave] = valor
        elif isinstance(valor, dict) and profundidade > 1:
            sub_avisos: list[str] = []
            menor = enxugar(f"{bloco}.{chave}", valor, sub_avisos, profundidade - 1)
            if tamanho_json(menor) <= LIMITE_CHAVE:
                saida[chave] = menor
                avisos.extend(sub_avisos)
            else:
                avisos.append(f"{bloco}.{chave}: {tamanho} bytes omitidos")
        else:
            avisos.append(f"{bloco}.{chave}: {tamanho} bytes omitidos")
    return saida


def montar() -> dict:
    mc = carregar("video-masterclass-dados")
    fiscais_video = carregar("video-fiscais-dados")
    fontes = mc.Fontes()
    fontes.marcar(ROOT / "scripts" / "video-masterclass-dados.py")
    fontes.marcar(ROOT / "scripts" / "video-fiscais-dados.py")
    malha = fontes.json(MALHA)

    saida: dict = {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fontes": {},
        "pendentes": [],
        "avisos": [],
        "mapa": mc.bloco_mapa(malha, fiscais_video),
    }
    for bloco in BLOCOS:
        caminho = DADOS / f"{bloco}.json"
        if not caminho.exists():
            saida["pendentes"].append(bloco)
            continue
        conteudo = fontes.json(caminho)
        conteudo = enxugar(bloco, conteudo, saida["avisos"])
        tamanho = tamanho_json(conteudo)
        if tamanho > LIMITE_BLOCO:
            saida["avisos"].append(
                f"{bloco}: {tamanho} bytes acima de {LIMITE_BLOCO} mesmo enxuto; não embutido"
            )
            saida["pendentes"].append(bloco)
            continue
        saida[bloco] = conteudo
    saida["fontes"] = dict(sorted(fontes.hashes.items()))
    return saida


def resumo(dados: dict) -> None:
    prontos = [b for b in BLOCOS if b in dados]
    print(f"{SAIDA.relative_to(ROOT)}: {len(dados['mapa']['ufs'])} UFs no mapa")
    print(f"  blocos prontos ({len(prontos)}): {', '.join(prontos) or 'nenhum'}")
    print(
        f"  pendentes ({len(dados['pendentes'])}): {', '.join(dados['pendentes']) or 'nenhum'}"
    )
    for aviso in dados["avisos"]:
        print(f"  aviso: {aviso}")


def main() -> None:
    dados = montar()
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    resumo(dados)


if __name__ == "__main__":
    main()
