#!/usr/bin/env python3
"""Erro das pesquisas no 1º turno presidencial de 2022, por casa, contra o TSE.

Lê a transcrição manual em ``analysis/predicao_2026/erro_2022/pesquisas_2022.json``
(cada número com arquivo e página) e o resultado oficial do TSE já guardado no
repositório, e grava ``analysis/predicao_2026/erro_2022/erro_2022.json``.

O produto é descritivo. O erro comum de 2022 entra na página só como
sensibilidade ("se o erro de 2022 se repetisse"), nunca como ajuste da central:
uma eleição é uma observação só.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/predicao_2026/erro_2022"
TRANSCRICAO = BASE / "pesquisas_2022.json"
SAIDA = BASE / "erro_2022.json"
ORIGINAIS = ROOT / "data/originals/pesquisas_2022"
TSE_UF = ROOT / "analysis/voto_util/tse_2022_uf.json"
TSE_API = ROOT / "data/raw/tse_resultados/api_2022"
PREVISAO = ROOT / "docs/assets/predicao_2026_1T_presidente.json"

GRUPOS = ("lula", "bolsonaro", "tebet", "ciro", "demais")
PRINCIPAIS = GRUPOS[:4]
CAMPOS_TSE = (
    "aptos",
    "comparecimento",
    "brancos",
    "nulos",
    "validos",
    *PRINCIPAIS,
    "outros",
)
NIVEIS_PRINCIPAIS = {
    "pdf_do_instituto",
    "infografico_do_instituto",
    "materia_do_contratante",
    "imprensa_concordante",
}
# Nomes da API do TSE (campo "nm") para os quatro principais.
NOMES_API = {
    "lula": "LULA",
    "bolsonaro": "JAIR BOLSONARO",
    "tebet": "SIMONE TEBET",
    "ciro": "CIRO GOMES",
}
Z95 = 1.959963984540054


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def parcelas(votos: dict) -> dict:
    """Parcelas em pp dos válidos para Lula, Bolsonaro, Tebet, Ciro e demais."""
    validos = votos["validos"]
    out = {k: 100 * votos[k] / validos for k in PRINCIPAIS}
    out["demais"] = 100 - sum(out.values())
    return out


def ler_api(nome: str) -> dict | None:
    path = TSE_API / f"{nome}-c0001-e000544-r.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    votos: dict[str, int] = dict.fromkeys(PRINCIPAIS, 0)
    for cand in data["cand"]:
        for chave, nm in NOMES_API.items():
            if cand["nm"] == nm:
                votos[chave] = int(cand["vap"])
    return {
        "arquivo": rel(path),
        "sha256": sha256(path),
        "data_totalizacao": f"{data['dt']} {data['ht']}",
        "aptos": int(data["e"]),
        "comparecimento": int(data["c"]),
        "abstencao": int(data["a"]),
        "brancos": int(data["vb"]),
        "nulos": int(data["tvn"]),
        "validos": int(data["vv"]),
        **votos,
        "outros": int(data["vv"]) - sum(votos.values()),
    }


def resultado_oficial() -> dict:
    """1º turno de 2022 a partir dos arquivos do TSE no repositório.

    A referência rastreada é ``analysis/voto_util/tse_2022_uf.json`` (bloco
    ``brasil_2022.t1``, copiado da API de resultados do TSE, eleição 544). Se os
    JSON brutos da API estiverem presentes em ``data/raw``, o script refaz a
    conta a partir deles e exige igualdade exata.
    """
    tse = json.loads(TSE_UF.read_text())
    br = {k: v for k, v in tse["brasil_2022"]["t1"].items() if k != "fonte"}
    soma_ufs = {k: sum(uf["t1"][k] for uf in tse["ufs"]) for k in CAMPOS_TSE}
    oficial = {
        "fonte": rel(TSE_UF),
        "sha256": sha256(TSE_UF),
        "fonte_original": tse["brasil_2022"]["t1"]["fonte"],
        "abrangencia": "Brasil e exterior (total oficial da eleição 544)",
        "votos": br,
        "parcelas_validos_pp": parcelas(br),
        "comparecimento_pct_aptos": 100 * br["comparecimento"] / br["aptos"],
        "brancos_pct_comparecimento": 100 * br["brancos"] / br["comparecimento"],
        "nulos_pct_comparecimento": 100 * br["nulos"] / br["comparecimento"],
        "sem_exterior": {
            "descricao": "soma das 27 UFs em analysis/voto_util/tse_2022_uf.json",
            "votos": soma_ufs,
            "parcelas_validos_pp": parcelas(soma_ufs),
        },
        "conferencia_api_bruta": None,
    }
    api_br = ler_api("br")
    api_zz = ler_api("zz")
    if api_br is not None:
        diferencas = {k: api_br[k] - br[k] for k in CAMPOS_TSE if api_br[k] != br[k]}
        if diferencas:
            raise SystemExit(
                f"API bruta do TSE diverge do JSON rastreado: {diferencas}"
            )
        conferencia = {
            "br": {k: api_br[k] for k in ("arquivo", "sha256", "data_totalizacao")},
            "igual_ao_json_rastreado": True,
        }
        if api_zz is not None:
            fecha = all(
                soma_ufs[k] + api_zz[k] == br[k]
                for k in ("validos", "brancos", "nulos", *PRINCIPAIS)
            )
            conferencia["zz"] = {
                k: api_zz[k] for k in ("arquivo", "sha256", "data_totalizacao")
            }
            conferencia["ufs_mais_exterior_fecham_brasil"] = fecha
            if not fecha:
                raise SystemExit("27 UFs mais exterior não fecham o total do Brasil")
        oficial["conferencia_api_bruta"] = conferencia
    return oficial


def validos_da_pesquisa(p: dict) -> tuple[dict, str]:
    """Parcelas dos válidos usadas no erro e a base de onde vieram."""
    pub = p.get("validos_publicados")
    if pub:
        out = {k: float(pub[k]) for k in PRINCIPAIS}
        out["demais"] = 100 - sum(out.values())
        return out, "validos_publicados"
    if p.get("contagens"):
        c = p["contagens"]
        nomes = [k for k in c if k not in ("ns_nr", "branco_nulo", "total", "fonte")]
        soma = sum(c[k] for k in nomes)
        out = {k: 100 * c[k] / soma for k in PRINCIPAIS}
        out["demais"] = 100 - sum(out.values())
        return out, "calculado_das_contagens"
    out = validos_dos_totais(p["totais"])
    if out is None:
        raise SystemExit(f"{p['id']}: sem válidos nem totais")
    return out, "calculado_dos_totais"


def validos_dos_totais(totais: dict | None) -> dict | None:
    if not totais:
        return None
    soma = sum(float(totais[k]) for k in PRINCIPAIS)
    soma += sum(float(v) for v in totais["outros_nomeados"].values())
    out = {k: 100 * float(totais[k]) / soma for k in PRINCIPAIS}
    out["demais"] = 100 - sum(out.values())
    return out


def margem_diferenca(p: dict, v: dict) -> float:
    """Margem de 95% da diferença Lula menos Bolsonaro sob amostragem simples.

    Usa o tamanho efetivo nos válidos quando a casa publica totais (n vezes a
    fração de entrevistados com candidato); sem totais, usa n inteiro, o que
    subestima a margem. Ignora efeito de desenho, ponderação e arredondamento,
    e por isso é piso, não intervalo da casa.
    """
    totais = p.get("totais")
    frac = 1.0
    if totais:
        frac = (
            sum(float(totais[k]) for k in PRINCIPAIS)
            + sum(float(x) for x in totais["outros_nomeados"].values())
        ) / 100
    n = p["n"] * min(frac, 1.0)
    pl, pb = v["lula"] / 100, v["bolsonaro"] / 100
    var = (pl + pb - (pl - pb) ** 2) / n
    return 100 * Z95 * var**0.5


def documentos(p: dict) -> list[dict]:
    fonte = ORIGINAIS / p["id"] / "fonte.json"
    if not fonte.exists():
        return []
    meta = json.loads(fonte.read_text())
    return [
        {
            "arquivo": rel(ORIGINAIS / p["id"] / d["arquivo"]),
            "url": d["url"],
            "sha256": d["sha256"],
        }
        for d in meta["documentos"]
    ]


def avaliar(p: dict, oficial: dict) -> dict:
    v, base = validos_da_pesquisa(p)
    erros = {k: v[k] - oficial[k] for k in GRUPOS}
    dif_pesquisa = v["lula"] - v["bolsonaro"]
    dif_oficial = oficial["lula"] - oficial["bolsonaro"]
    alternativa = validos_dos_totais(p.get("totais"))
    margem = margem_diferenca(p, v)
    return {
        "id": p["id"],
        "casa": p["casa"],
        "casa_2026": p.get("casa_2026"),
        "nivel": p["nivel"],
        "incluir": p["incluir"],
        "motivo_exclusao": p.get("motivo_exclusao"),
        "registro": p["registro"],
        "campo": p["campo"],
        "n": p["n"],
        "metodo": p["metodo"],
        "base_validos": base,
        "validos_pp": v,
        "erro_pp": erros,
        "diferenca_lula_menos_bolsonaro": {
            "pesquisa": dif_pesquisa,
            "oficial": dif_oficial,
            "erro": dif_pesquisa - dif_oficial,
        },
        "erro_absoluto_medio_pp": sum(abs(e) for e in erros.values()) / len(GRUPOS),
        "margem_95_diferenca_aas_pp": margem,
        "erro_diferenca_fora_da_margem_aas": abs(dif_pesquisa - dif_oficial) > margem,
        "validos_calculados_dos_totais": alternativa,
        "documentos": documentos(p),
    }


def agregado(rows: list[dict], oficial: dict, nome: str, regra: str) -> dict:
    media = {k: statistics.fmean(r["validos_pp"][k] for r in rows) for k in GRUPOS}
    erro = {k: media[k] - oficial[k] for k in GRUPOS}
    erro_dif = (media["lula"] - media["bolsonaro"]) - (
        oficial["lula"] - oficial["bolsonaro"]
    )
    dif = [r["diferenca_lula_menos_bolsonaro"]["erro"] for r in rows]
    desvio = {k: statistics.stdev(r["erro_pp"][k] for r in rows) for k in GRUPOS}
    desvio["diferenca_lula_menos_bolsonaro"] = statistics.stdev(dif)
    return {
        "nome": nome,
        "regra": regra,
        "casas": [r["id"] for r in rows],
        "n_casas": len(rows),
        "media_simples_validos_pp": media,
        "erro_comum_pp": erro,
        "erro_comum_diferenca_lula_menos_bolsonaro": erro_dif,
        "mediana_dos_erros_diferenca_pp": statistics.median(dif),
        "erro_absoluto_medio_da_media_pp": sum(abs(e) for e in erro.values())
        / len(GRUPOS),
        "desvio_padrao_entre_casas_pp": desvio,
        "casas_que_superestimaram_lula_menos_bolsonaro": sum(1 for e in dif if e > 0),
        "componente_proprio_diferenca_pp": {
            r["id"]: r["diferenca_lula_menos_bolsonaro"]["erro"] - erro_dif
            for r in rows
        },
    }


def melhor_pior(rows: list[dict]) -> dict:
    def chave_dif(r):
        return abs(r["diferenca_lula_menos_bolsonaro"]["erro"])

    def chave_eam(r):
        return r["erro_absoluto_medio_pp"]

    def resumo(r):
        return {
            "id": r["id"],
            "casa": r["casa"],
            "erro_diferenca_pp": r["diferenca_lula_menos_bolsonaro"]["erro"],
            "erro_absoluto_medio_pp": r["erro_absoluto_medio_pp"],
        }

    return {
        "criterio_principal": "erro absoluto na diferença Lula menos Bolsonaro nos válidos",
        "melhor_casa_2022": resumo(min(rows, key=chave_dif)),
        "pior_casa_2022": resumo(max(rows, key=chave_dif)),
        "criterio_alternativo": "erro absoluto médio em Lula, Bolsonaro, Tebet, Ciro e demais",
        "melhor_casa_2022_eam": resumo(min(rows, key=chave_eam)),
        "pior_casa_2022_eam": resumo(max(rows, key=chave_eam)),
        "ressalva": "Ranking de uma onda por casa numa eleição. Casas com campo encerrado vários dias antes da urna carregam também o movimento final do eleitor; o ranking não separa as duas coisas.",
    }


def comparar_2026(rows: list[dict]) -> dict:
    if not PREVISAO.exists():
        return {"status": "arquivo da previsão de 2026 ausente"}
    data = json.loads(PREVISAO.read_text())
    efeitos = data.get("nacional", {}).get("efeitos_casa", {})
    linhas = []
    for r in rows:
        nome = r["casa_2026"]
        if not nome:
            continue
        ef = efeitos.get(nome)
        linhas.append(
            {
                "casa_2022": r["casa"],
                "casa_2026": nome,
                "erro_2022_diferenca_lula_menos_bolsonaro_pp": r[
                    "diferenca_lula_menos_bolsonaro"
                ]["erro"],
                "desvio_relativo_2026_lula_menos_flavio_pp": (
                    ef["desvio_margem_pp"] if ef else None
                ),
                "ondas_2026": ef["n_ondas"] if ef else 0,
            }
        )
    return {
        "fonte_2026": rel(PREVISAO),
        "sha256_fonte_2026": sha256(PREVISAO),
        "campo_lido": "nacional.efeitos_casa[casa].desvio_margem_pp",
        "sinal": "positivo nas duas colunas significa mais Lula: em 2022, acima do TSE; em 2026, acima da mediana das casas pareadas por época",
        "linhas": linhas,
        "ressalva": "O desvio relativo de 2026 não é erro: mede a distância da casa às outras casas no mesmo período, não à urna, que ainda não existe. Casa que errou em 2022 pode ter mudado método, amostra, equipe ou marca (FSB/BTG para Nexus, Exame/Ideia para Meio/Ideia). A tabela serve para o leitor ver, não para corrigir ninguém.",
    }


def aplicacao(principal: dict, rows: list[dict]) -> dict:
    e = principal["erro_comum_diferenca_lula_menos_bolsonaro"]
    antes = sum(1 for r in rows if r["campo"]["fim"] < "2022-10-01")
    return {
        "status": "descrição; não calculado sobre a central, que está em revisão",
        "erro_comum_2022_diferenca_lula_menos_bolsonaro_pp": e,
        "regra": "Sensibilidade 'se o erro comum de 2022 se repetisse': somar à diferença Flávio menos Lula nos válidos da central de 2026 o erro comum de 2022 na diferença Lula menos Bolsonaro, com o sinal dele. Se em 2022 a média das casas pôs Lula E pontos acima do que a urna deu na diferença, repetir esse erro significa que a diferença real F menos L seria E pontos maior do que a central.",
        "deslocamentos_pp_em_flavio_menos_lula": {
            "repeticao_de_2022": e,
            "direcao_oposta": -e,
        },
        "como_publicar": "Mostrar as duas direções lado a lado, com o mesmo destaque, e o desvio entre casas de 2022 ao lado para lembrar que o erro de cada casa variou muito em torno da média.",
        "ressalvas": [
            "Uma eleição é uma observação. Não há como estimar a distribuição do erro comum com um ponto só.",
            "2022 teve cartela, polarização, instituto, método e eleitorado diferentes de 2026; o erro pode não se repetir, pode mudar de sinal e pode mudar de tamanho.",
            "Não é ajuste da central nem prognóstico. A decisão de qualquer ajuste é do responsável pela previsão.",
            f"{antes} das {len(rows)} ondas da média principal terminaram o campo antes de 1º de outubro; parte do erro pode ser movimento real de última hora, não viés de medição.",
        ],
    }


def construir() -> dict:
    transc = json.loads(TRANSCRICAO.read_text())
    oficial_obj = resultado_oficial()
    oficial = oficial_obj["parcelas_validos_pp"]
    rows = [avaliar(p, oficial) for p in transc["pesquisas"]]
    principais = [
        r
        for r in rows
        if r["incluir"]
        and r["nivel"] in NIVEIS_PRINCIPAIS
        and r["campo"]["fim"] >= transc["criterio"]["campo_fim_min_para_media"]
        and r["campo"]["fim"] <= transc["criterio"]["campo_fim_max"]
    ]
    so_pdf = [r for r in principais if r["nivel"] == "pdf_do_instituto"]
    ampliada = principais + [r for r in rows if r["nivel"] == "imprensa_divergente"]
    sem_verita = [r for r in principais if r["id"] != "verita"]
    principal = agregado(
        principais,
        oficial,
        "principal",
        transc["criterio"]["media_principal"],
    )
    return {
        "descricao": "Erro das últimas pesquisas nacionais no 1º turno presidencial de 2022, em pontos percentuais dos votos válidos, contra o resultado oficial do TSE. Descritivo; não é prognóstico nem ajuste.",
        "gerado_por": "scripts/predicao-2026-erro-2022.py",
        "transcricao": {"arquivo": rel(TRANSCRICAO), "sha256": sha256(TRANSCRICAO)},
        "convencao_de_sinal": "erro = pesquisa menos urna; positivo superestima o candidato; na diferença Lula menos Bolsonaro, positivo superestima a vantagem de Lula",
        "resultado_oficial": oficial_obj,
        "por_casa": rows,
        "media_das_casas": principal,
        "sensibilidades_da_media": [
            agregado(
                so_pdf,
                oficial,
                "so_pdf_do_instituto",
                "só casas com PDF do próprio instituto",
            ),
            agregado(
                sem_verita,
                oficial,
                "sem_verita",
                "média principal sem o Instituto Veritá, a casa mais distante das demais",
            ),
            agregado(
                ampliada,
                oficial,
                "ampliada",
                "média principal mais a Brasmarket, que só tem imprensa divergente",
            ),
        ],
        "ranking": melhor_pior(principais),
        "comparacao_2026": comparar_2026(principais),
        "aplicacao_2026": aplicacao(principal, principais),
        "eleicao_2018": {
            "status": "não arquivada",
            "motivo": "As pesquisas finais de 2018 não foram arquivadas nesta rodada; nenhum número de 2018 entra sem documento.",
        },
        "nao_arquivadas": transc["nao_arquivadas"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").strip().partition("\n")[0]
    )
    parser.add_argument("--saida", type=Path, default=SAIDA)
    args = parser.parse_args()
    out = construir()
    args.saida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    m = out["media_das_casas"]
    print(
        f"{m['n_casas']} casas; erro comum na diferença L-B: "
        f"{m['erro_comum_diferenca_lula_menos_bolsonaro']:+.2f} pp"
    )
    for r in out["por_casa"]:
        d = r["diferenca_lula_menos_bolsonaro"]["erro"]
        print(f"  {r['casa']:<22} {d:+6.2f}  EAM {r['erro_absoluto_medio_pp']:.2f}")


if __name__ == "__main__":
    main()
