#!/usr/bin/env python3
"""Pesquisas, centrais e projeção territorial contra a urna do 2º turno de 2026.

Lê a urna (``analysis/apuracao_2t_2026/dados/presidente.json`` ou, sem ele, o
placar ao vivo do servidor da apuração), o acervo de pesquisas
``analysis/reponderacao/pesquisas/``, o agregador por renda
(``docs/assets/reponderacao_pnad.json``), o snapshot das centrais
(``docs/assets/reponderacao_simulador.json``), as estaduais pós-urna e os mapas
de previsão por UF, e grava em ``analysis/apuracao_2t_2026/dados/``:

- ``pesquisas_vs_urna.json``: última onda de cada casa com campo encerrado a
  partir de 19/10, publicado, oficial e reponderado contra a urna; centrais;
  tendência; hipóteses medidas; comparação com o 1º turno e com 2022;
- ``pesquisas_estaduais.json``: estaduais do 2º turno contra a urna por UF;
- ``projecao_pre_urna.json``: projeções por UF de 19, 24 e 25/10 contra a urna;
- ``pesquisas.md``: memorando com números, consultas e hipóteses.

Uso:
    python3 scripts/apuracao-2t-2026-pesquisas.py
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from apuracao_2t_2026 import pesquisas_autor as A
from apuracao_2t_2026 import pesquisas_memo as MEMO
from apuracao_2t_2026 import pesquisas_nacionais as N
from apuracao_2t_2026 import pesquisas_territorio as T
from apuracao_2t_2026 import pesquisas_urna as U
from apuracao_2026 import pesquisas as P

ROOT = U.ROOT
DADOS = ROOT / "analysis/apuracao_2t_2026/dados"
PESQUISAS = ROOT / "analysis/reponderacao/pesquisas"
PNAD = ROOT / "docs/assets/reponderacao_pnad.json"
SIMULADOR = ROOT / "docs/assets/reponderacao_simulador.json"
PRESENCA = ROOT / "analysis/reponderacao/historico_2t/presenca.json"
MAPA = ROOT / "docs/assets/mapa_previsao_2t_2026.json"
SECOES_CSV = ROOT / "docs/assets/projecao_secoes_2t_ufs.csv"
ESTADUAIS = ROOT / "analysis/projecao_secoes_2t/estaduais.json"
ESTADUAIS_DIR = ROOT / "analysis/reponderacao/estaduais"
PESQ_1T = ROOT / "analysis/apuracao_2026/dados/pesquisas_vs_urna.json"
ERRO_2022 = ROOT / "analysis/predicao_2026/erro_2022/erro_2022.json"
TRAVESSAO = chr(0x2014)


def ler(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def arredondar(x: Any, casas: int = 6) -> Any:
    if isinstance(x, float):
        return round(x, casas)
    if isinstance(x, dict):
        return {k: arredondar(v, casas) for k, v in x.items()}
    if isinstance(x, list | tuple):
        return [arredondar(v, casas) for v in x]
    return x


def gravar(nome: str, dados: dict[str, Any]) -> None:
    texto = json.dumps(arredondar(dados), ensure_ascii=False, indent=1)
    if TRAVESSAO in texto:
        raise SystemExit(f"{nome}: travessão no texto gerado")
    (DADOS / nome).write_text(texto + "\n", encoding="utf-8")


def mapa_de(referencia: str) -> tuple[dict[str, Any], str] | None:
    """Versão do mapa de previsão com essa referência: disco ou histórico git."""
    atual = ler(MAPA)
    if atual["referencia"] == referencia:
        return atual, "arquivo de trabalho"
    commits = subprocess.run(
        ["git", "log", "--format=%h", "--", U.rel(MAPA)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()
    for h in commits:
        bruto = subprocess.run(
            ["git", "show", f"{h}:{U.rel(MAPA)}"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout
        if bruto and json.loads(bruto)["referencia"] == referencia:
            return json.loads(bruto), f"git {h}"
    return None


def carregar_ondas(pnad: dict[str, dict]) -> list[dict[str, Any]]:
    ondas = []
    for path in sorted(PESQUISAS.glob("*.json")):
        p = ler(path)
        if "2t" not in (p.get("publicado") or {}):
            continue
        if p["campo"]["fim"] < N.INICIO_POS_URNA or p["campo"]["inicio"] < "2026-10-05":
            continue
        x = N.onda(p, pnad)
        x["fonte"] = U.fonte(path)
        ondas.append(x)
    return ondas


def conferir_snapshot(finais: list[dict], sim: dict[str, Any]) -> dict[str, Any]:
    """O reponderado usado aqui precisa ser o mesmo que entrou na Projeção."""
    sel = {s["id"]: s for s in sim["projection"]["selected"]}
    for x in finais:
        s = sel.get(x["id"])
        if s and s.get("pnad") and x["reponderado"]:
            for k in ("flavio", "lula"):
                if abs(s["pnad"][k] - x["reponderado"]["total"][k]) > 0.01:
                    raise SystemExit(f"{x['id']}: PNAD difere da Projeção ({k})")
    ids = {x["id"] for x in finais}
    return {
        "na_projecao_fora_daqui": sorted(set(sel) - ids),
        "aqui_fora_da_projecao": sorted(ids - set(sel)),
        "nota": (
            "Data Ranking (campo até 16/10) entra na Projeção, mas fica fora daqui pela "
            "regra de campo encerrado a partir de 19/10"
        ),
    }


def presenca_necessaria(
    finais: list[dict], centrais: dict[str, Any], alvo: dict[str, float]
) -> dict[str, Any]:
    """Quanto a razão F/L de cada referência precisava mudar para bater a urna."""
    media_pub = N.resumo_finais(finais, alvo)["media_simples_validos"]
    extra = 1 + (centrais.get("presenca_relativa_pct") or 0.0) / 100
    med = N.multiplicador_necessario(centrais["media_arvor"]["validos"], alvo)
    proj = N.multiplicador_necessario(centrais["projecao_arvor"]["validos"], alvo)
    return {
        "regra": (
            "100 × [(F/L urna) / (F/L referência) − 1]; não separa presença por "
            "candidato de erro de medição"
        ),
        "media_simples_publicada_20_casas": N.multiplicador_necessario(media_pub, alvo),
        "media_arvor": med,
        "media_arvor_sem_o_extra": 100 * (extra * (1 + med / 100) - 1),
        "projecao_arvor": proj,
        "projecao_arvor_sem_o_extra": 100 * (extra * (1 + proj / 100) - 1),
        "extra_central_pct": centrais.get("presenca_relativa_pct"),
        "autor_cenario_pct": -12.5,
        "autor_empate_pct": -6.4,
    }


def main() -> None:
    urna = U.carregar_urna()
    um = U.primeiro_turno()
    pnad_json, sim = ler(PNAD), ler(SIMULADOR)
    pnad = N.vetores_pnad(pnad_json, sim)
    alvo = urna["brasil"]["validos"]
    alvo_sem_zz = urna["brasil_sem_exterior"]["validos"]

    ondas = [N.comparar(x, alvo) for x in carregar_ondas(pnad)]
    finais = N.ultima_por_casa(ondas)
    for x in finais:
        x["erro_sem_exterior"] = N.erro(x["validos_do_total"], alvo_sem_zz)
    conferencia = conferir_snapshot(finais, sim)
    ranking = P.ordenar_por_erro(
        finais, lambda x: x["erro_validos_do_total"]["erro_f_menos_l"]
    )
    pesq_1t = ler(PESQ_1T)
    erro22 = ler(ERRO_2022)
    r1 = pesq_1t["resumo_ultimas_ondas"]
    m22 = erro22["media_das_casas"]

    mapa25 = mapa_de("2026-10-25")
    mapa24 = mapa_de("2026-10-24")
    if mapa25 is None:
        raise SystemExit("Mapa de previsão de 25/10 ausente")
    transportado = {u["uf"]: u["transportado"] for u in mapa25[0]["ufs"]}

    centrais = N.centrais(sim, alvo)
    centrais["sem_exterior"] = {
        k: N.erro(v["validos"], alvo_sem_zz)
        for k, v in centrais.items()
        if isinstance(v, dict) and "validos" in v
    }

    saida = {
        "descricao": (
            "Pesquisas nacionais de 2º turno com campo encerrado a partir de 19/10/2026 "
            "(última onda de cada casa), centrais da casa e hipóteses medidas contra a urna. "
            "Erro = pesquisa menos urna em pontos dos válidos; na diferença F−L, positivo "
            "superestima Flávio. erro_lula_menos_flavio traz o sinal do 1º turno."
        ),
        "gerado_por": "scripts/apuracao-2t-2026-pesquisas.py",
        "fontes": [
            U.fonte(p)
            for p in (PNAD, SIMULADOR, PRESENCA, MAPA, PESQ_1T, ERRO_2022)
            if p.exists()
        ],
        "urna": {
            "fonte": urna["fonte"],
            "brasil": urna["brasil"],
            "brasil_sem_exterior": urna["brasil_sem_exterior"],
            "regioes": urna["regioes"],
            "abstencao_mesmos_municipios": urna["abstencao_mesmos_municipios"],
            "primeiro_turno_brasil": um["brasil"],
        },
        "regra_validos": (
            "candidaturas renormalizadas para 100; indecisos, branco/nulo e não vai votar "
            "fora; válidos oficiais da casa guardados à parte"
        ),
        "regra_selecao": (
            "acervo analysis/reponderacao/pesquisas com placar de 2º turno, campo iniciado "
            "depois de 04/10 e encerrado a partir de 19/10; última onda por casa pelo fim do "
            "campo e pela divulgação"
        ),
        "conferencia_snapshot": conferencia,
        "pesquisas": finais,
        "ranking": [x["id"] for x in ranking],
        "resumo": N.resumo_finais(finais, alvo),
        "por_modo": N.por_modo(finais),
        "efeito_reponderacao": N.efeito_reponderacao(finais),
        "centrais": centrais,
        "tendencia_publicada": N.tendencia(ondas),
        "hipoteses": {
            "presenca_declarada": N.presenca_declarada(finais, ler(PRESENCA), alvo),
            "indecisos_extremo": N.indecisos_extremo(finais, alvo),
            "contabilidade_entre_turnos": T.contabilidade(urna, um, transportado),
            "indecisos_divisao_autor": N.indecisos_divisao(finais, alvo, 0.348),
            "presenca_relativa_necessaria": presenca_necessaria(finais, centrais, alvo),
        },
        "primeiro_turno": {
            "fonte": U.fonte(PESQ_1T),
            "erro_comum_lula_menos_flavio": r1["publicado"]["media"],
            "mediana": r1["publicado"]["mediana"],
            "desvio_entre_casas": r1["publicado"]["desvio_padrao"],
            "n_casas": r1["publicado"]["n"],
            "agregador_publicado_erro": pesq_1t["medias"]["agregador_publicado"][
                "diferenca_lula_menos_flavio"
            ]["erro"],
            "agregador_reponderado_erro": pesq_1t["medias"]["agregador_reponderado"][
                "diferenca_lula_menos_flavio"
            ]["erro"],
            "efeito_reponderacao_ultimas_ondas": pesq_1t["efeito_reponderacao"][
                "ultimas_ondas"
            ],
        },
        "painel_1t_2t": N.painel_1t(finais, pesq_1t),
        "referencia_2022": {
            "fonte": U.fonte(ERRO_2022),
            "erro_comum_lula_menos_bolsonaro": m22[
                "erro_comum_diferenca_lula_menos_bolsonaro"
            ],
            "mediana": m22["mediana_dos_erros_diferenca_pp"],
            "erro_medio_bolsonaro_pp": -4.33,
            "nota": "1º turno de 2022, 12 casas; Bolsonaro −4,33 conforme AGENTS.md",
        },
    }
    DADOS.mkdir(parents=True, exist_ok=True)
    gravar("pesquisas_vs_urna.json", saida)

    est = ler(ESTADUAIS)["pesquisas"]
    for path in sorted(ESTADUAIS_DIR.glob("*.json")):
        p = ler(path)
        if all(p["id"] != e["id"] for e in est):
            est.append(p)
    estaduais = {
        "descricao": "Estaduais presidenciais de 2º turno contra a urna da UF.",
        "gerado_por": "scripts/apuracao-2t-2026-pesquisas.py",
        "fontes": [U.fonte(ESTADUAIS)]
        + [U.fonte(p) for p in sorted(ESTADUAIS_DIR.glob("*.json"))],
        "urna_fonte": urna["fonte"],
        **T.estaduais(est, urna, mapa25[0]),
    }
    gravar("pesquisas_estaduais.json", estaduais)

    metodos = T.metodos_mapa(mapa25[0], "25_10")
    if mapa24:
        metodos |= T.metodos_mapa(mapa24[0], "24_10")
    metodos |= T.metodos_csv(SECOES_CSV)
    avaliados = {
        k: T.avaliar_metodo(k, m["rotulo"], m["votos"], urna)
        for k, m in metodos.items()
    }
    projecao = {
        "descricao": (
            "Projeções da casa por UF contra a urna por UF (Brasil sem exterior). Erro na "
            "parcela de Flávio entre os dois; na diferença F−L é o dobro."
        ),
        "gerado_por": "scripts/apuracao-2t-2026-pesquisas.py",
        "fontes": [U.fonte(MAPA), U.fonte(SECOES_CSV)],
        "versoes_mapa": {
            "25_10": mapa25[1],
            "24_10": mapa24[1] if mapa24 else None,
        },
        "urna_fonte": urna["fonte"],
        "metodos": avaliados,
        "ranking_rmse": sorted(
            avaliados, key=lambda k: avaliados[k]["rmse_flavio_pp_ponderado"]
        ),
    }
    gravar("projecao_pre_urna.json", projecao)

    autor = A.refazer(urna)
    gravar("hipotese_autor.json", autor)

    memo = MEMO.memorando(
        arredondar(saida),
        arredondar(estaduais),
        arredondar(projecao),
        arredondar(autor),
    )
    if TRAVESSAO in memo:
        raise SystemExit("pesquisas.md: travessão no texto")
    (DADOS / "pesquisas.md").write_text(memo, encoding="utf-8")
    print(
        f"gravado: {U.rel(DADOS)}/pesquisas_vs_urna.json, pesquisas_estaduais.json, "
        "projecao_pre_urna.json, hipotese_autor.json, pesquisas.md"
    )


if __name__ == "__main__":
    main()
