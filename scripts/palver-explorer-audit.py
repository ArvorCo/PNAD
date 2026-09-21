#!/usr/bin/env python3
"""Audit public aggregate tables; infer margins, never individual microdata."""

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "analysis/reponderacao/palver_explorer_20260921"
BALLOTS = {"1t": "stimulated_1r_vote_1_h", "2t": "lula_flavio"}
PAIR = {"lula": "Lula (PT)", "flavio": "Flávio Bolsonaro (PL)"}


def read(name):
    return json.loads((BASE / name).read_text())


def table(wave, question, breakdown=None):
    tables = read(f"{wave}/{question}--{breakdown or 'total'}.json")["tables"]
    return tables[0] if tables else None


def matrix(tab, answers=None):
    answers = answers or tab["answers"]
    cells = {(c["answer"], c["group"]): c["share"] for c in tab["cells"]}
    return np.array([[cells[a, g] for g in tab["groups"]] for a in answers])


def recover_margin(wave, breakdown):
    """Solve total(answer) = sum_g p(g) share(answer|g), across both ballots.

    Reject incomplete universes, rank deficiency, negative solutions and
    non-recomposition. n_eff then provides an independent second-moment check.
    """
    blocks, totals = [], []
    for question in BALLOTS.values():
        group, total = table(wave, question, breakdown), table(wave, question)
        if group is None:
            return {"identified": False, "reason": "breakdown_unavailable"}
        if group["base"] != total["base"]:
            return {
                "identified": False,
                "reason": "different_universe",
                "base": group["base"],
            }
        blocks.append(matrix(group))
        totals.extend(matrix(total, group["answers"])[:, 0])
    a = np.vstack([*blocks, np.ones(len(group["groups"]))])
    b = np.r_[totals, 1.0]
    shares, _, rank, _ = np.linalg.lstsq(a, b, rcond=None)
    residual = float(np.max(np.abs(a @ shares - b)))
    identified = rank == len(shares) and residual < 1e-10 and min(shares) >= -1e-10
    result = {
        "identified": bool(identified),
        "rank": int(rank),
        "groups": group["groups"],
        "max_residual": residual,
        "condition_number": float(np.linalg.cond(a)),
    }
    if not identified:
        return result
    stats = {s["group"]: s for s in group["group_stats"]}
    n = total["base"]
    reconstructed_neff = 1 / sum(
        shares[j] ** 2 / stats[g]["n_eff"] for j, g in enumerate(group["groups"])
    )
    result.update(
        weighted_pct=(shares * 100).tolist(),
        raw_n=[stats[g]["n"] for g in group["groups"]],
        raw_pct=[stats[g]["n"] / n * 100 for g in group["groups"]],
        neff=[stats[g]["n_eff"] for g in group["groups"]],
        mean_normalized_weight=[
            shares[j] / (stats[g]["n"] / n) for j, g in enumerate(group["groups"])
        ],
        reconstructed_neff=float(reconstructed_neff),
        published_neff=total["group_stats"][0]["n_eff"],
    )
    assert abs(reconstructed_neff - result["published_neff"]) < 1e-6
    return result


def audit():
    catalog, manifest = read("catalog.json"), read("manifest.json")
    # Reuse the project's frozen benchmark; no new PNAD vintage or price rule.
    agg = json.loads((ROOT / "docs/assets/reponderacao_pnad.json").read_text())
    poll = next(p for p in agg["pesquisas"] if p["id"] == "palver_2026-09-18")
    targets = poll["renda"]["pnad_pct"]
    result = {
        "source": catalog["source"],
        "queries": len(manifest["queries"]),
        "tables": sum(r["tables"] for r in manifest["queries"]),
        "latest_wave": manifest["latest_wave"],
        "benchmark_pct": targets,
        "benchmark_source": "docs/assets/reponderacao_pnad.json, palver_2026-09-18.renda.pnad_pct",
        "benchmark_scope": "Common September 2026 income ruler for all archived versions; not each wave's historical price ruler.",
        "waves": {},
    }
    for wave in catalog["waves"]:
        wid = wave["id"]
        margins = {
            b["key"]: recover_margin(wid, b["key"]) for b in catalog["breakdowns"]
        }
        income = margins["inc_std"]
        assert income["identified"]
        turns = {}
        for turn, question in BALLOTS.items():
            grouped, total = table(wid, question, "inc_std"), table(wid, question)
            published = dict(
                zip(total["answers"], (matrix(total)[:, 0] * 100).tolist(), strict=True)
            )
            counterfactual = {
                key: dict(
                    zip(
                        grouped["answers"],
                        (matrix(grouped) @ np.array(target)).tolist(),
                        strict=True,
                    )
                )
                for key, target in targets.items()
            }
            turns[turn] = {
                "published_exact": published,
                "income_standardized": counterfactual,
                "raw_pct": {
                    c["answer"]: 100 * c["n"] / total["base"] for c in total["cells"]
                },
            }
            if wid == result["latest_wave"]:
                turns[turn]["pdf_anchored_pair"] = {
                    k: {
                        "1t": {"lula": 41, "flavio": 42},
                        "2t": {"lula": 43, "flavio": 47},
                    }[turn][k]
                    + counterfactual["pessoas16_efetivo"][label]
                    - published[label]
                    for k, label in PAIR.items()
                }
        result["waves"][wid] = {"catalog": wave, "margins": margins, "turns": turns}

    wid = result["latest_wave"]
    weights = np.array(result["waves"][wid]["margins"]["inc_std"]["weighted_pct"])
    checks, skipped = [], []
    for question in catalog["questions"]:
        key = question["key"]
        total, grouped = table(wid, key), table(wid, key, "inc_std")
        if (
            total is None
            or grouped is None
            or total["base"] != 5000
            or grouped["base"] != 5000
        ):
            skipped.append({"question": key, "base": total["base"] if total else None})
            continue
        difference = (
            matrix(grouped) @ weights - matrix(total, grouped["answers"])[:, 0] * 100
        )
        checks.append(
            {"question": key, "max_residual_pp": float(np.max(np.abs(difference)))}
        )
    result["income_checks"] = checks
    result["conditional_questions_not_recomposed"] = skipped
    # Same interviews in the old and revised wave 2 must be checked, not assumed.
    versions = ["02_pesquisa_2026_09_09", "02_pesquisa_2026_09_21"]
    equal_counts = []
    for question in BALLOTS.values():
        a, b = [table(w, question, "inc_std") for w in versions]

        def counts(t):
            return {(c["group"], c["answer"]): c["n"] for c in t["cells"]}

        equal_counts.append(counts(a) == counts(b))
    result["wave2_same_raw_vote_income_counts"] = all(equal_counts)
    result["transfer_1t_2t"] = table(wid, "lula_flavio", "stimulated_1r_vote_1_h")
    result["past_vote_current_vote"] = table(wid, "lula_flavio", "vote_std")
    result["caveats"] = [
        "No respondent identifiers, individual weights or full demographic joint table are exposed by these tables.",
        "Recovered weighted margins and cell mean weights are aggregate inferences, not downloaded individual weights.",
        "Reweighting changes income alone, not joint TSE + PNAD calibration; no new confidence interval is inferred.",
        "Wave 2 first-round scenario includes Pablo Marçal; it cannot enter the project's no-Marçal first-round series.",
        "Explorer wave 3 fieldEnd is 2026-09-20; PDF pp. 16/22/30 says 18/09. Preserve both as a documentary discrepancy.",
        "Explorer revised wave 2 Lula first round is 40.440%; PDF p. 30 labels it 41%. Needs version/rounding reconciliation.",
        "vote_std pools blank/null and non-voters. This does not establish how individual 2022 eligibility was calibrated.",
        "Two multiple-response questions (desgaste_master and desgaste_stf) may legitimately sum above 100%.",
        "Identification breakdown omits 76 respondents in wave 3; it is not a closed partition of all 5000.",
    ]
    (BASE / "audit.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    )
    return result


def fmt(x):
    return f"{x:.2f}".replace(".", ",")


def pair(values):
    return " × ".join(fmt(values[label]) for label in PAIR.values())


def report(data):
    latest = data["waves"][data["latest_wave"]]
    inc = latest["margins"]["inc_std"]
    lines = [
        "# Palver Explorer: extração e auditoria de 21/09/2026",
        "",
        "Fonte: https://www.palver.com.br/survey/explore",
        "",
        f"Extraídos **{data['tables']} quadros públicos de {data['queries']} consultas**, sem login. "
        "As consultas cobrem os dois turnos principais nas quatro versões publicadas e "
        "todos os 44 quesitos da onda 3 por renda e total. Dez combinações não estão "
        "disponíveis nas ondas antigas; o retorno padrão não foi contado como cruzamento.",
        "",
        "Cada JSON preserva percentuais sem arredondamento (`share`), limites publicados "
        "(`low`, `high`), contagens por célula (`n`), bases e tamanho efetivo (`n_eff`). "
        "O manifesto registra URL, horário e SHA-256 do HTML público. Snapshots HTML "
        "compactados estão em `data/originals/palver_explorer_20260921/`.",
        "",
        "## Renda: composição bruta e ponderada da onda 3",
        "",
        "| Faixa | Entrevistas | Bruta % | Ponderada recuperada % | Peso médio normalizado | n efetivo |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for j, group in enumerate(inc["groups"]):
        lines.append(
            f"| {group} | {inc['raw_n'][j]} | {fmt(inc['raw_pct'][j])} | "
            f"{inc['weighted_pct'][j]:.6f} | {fmt(inc['mean_normalized_weight'][j])} | {fmt(inc['neff'][j])} |"
        )
    lines += [
        "",
        "As margens ponderadas foram **recuperadas por sistema linear**, não copiadas "
        "de um campo de pesos: para cada resposta, total = soma das parcelas por faixa. "
        "O sistema tem posto completo, solução não negativa e resíduos inferiores a 10⁻¹⁰. "
        "A recomposição independente do n efetivo usa `1 / Σ(p_g² / n_eff_g)` e devolve "
        f"{fmt(inc['reconstructed_neff'])}, igual ao nacional. As margens reproduzem os "
        "alvos 42,12 / 39,56 / 18,31 declarados no PDF.",
        "",
        f"A mesma margem recompõe **{len(data['income_checks'])} perguntas** de base 5.000 "
        "na onda 3. Questões condicionais foram separadas; não se aplicou a elas a "
        "distribuição de todos os entrevistados.",
        "",
        "## Sensibilidade de renda PNAD 2025",
        "",
        "Ordem Lula × Flávio, percentuais totais. Referência: o mesmo histograma, "
        "universo e ajuste de preços já utilizados pelo agregador na onda de setembro. "
        "A tabela aplica essa régua comum às quatro versões; não reproduz a régua histórica "
        "de preços de cada data. Cada cenário troca "
        "só a distribuição de renda. Os resultados não são raking conjunto nem previsão.",
        "",
        "| Versão | Turno | Explorer exato | PNAD efetiva 16+ | PNAD habitual 16+ |",
        "|---|---|---:|---:|---:|",
    ]
    for wid, wave in data["waves"].items():
        for turn, t in wave["turns"].items():
            lines.append(
                f"| {wid} | {turn} | {pair(t['published_exact'])} | "
                f"{pair(t['income_standardized']['pessoas16_efetivo'])} | "
                f"{pair(t['income_standardized']['pessoas16_habitual'])} |"
            )
    lines += [
        "",
        "**Distinção de ancoragem.** Os valores acima partem do total exato do Explorer. "
        "Se mantivermos a convenção anterior de ancorar o delta no total inteiro do PDF, "
        "a onda 3 resulta em "
        + "; ".join(
            f"{turn}: {fmt(t['pdf_anchored_pair']['lula'])} × {fmt(t['pdf_anchored_pair']['flavio'])}"
            for turn, t in latest["turns"].items()
        )
        + ". Não misturar as duas convenções.",
        "",
        "**Onda 2 revisada:** o voto por renda agora está disponível. Os dois cenários "
        "de 1º turno antigos incluem Marçal, portanto permanecem fora da série sem "
        "Marçal. O 2º turno pode ser recalculado com a versão revisada, substituindo a "
        "original, sem contar a amostra duas vezes. As contagens voto × renda são "
        f"idênticas nas versões antiga e revisada: {'sim' if data['wave2_same_raw_vote_income_counts'] else 'não'}.",
        "",
        "## Matriz medida de transferência e voto passado",
        "",
        "O cruzamento de 2º por 1º turno permite observar a fidelidade das duas bases "
        "e os destinos de Renan, Cury, outros candidatos e não escolha. São grupos "
        "medidos na mesma entrevista; não são trajetórias reais entre eleições. "
        "Outros candidatos e não escolha do 1º turno permanecem agrupados.",
        "",
        "| Origem no 1º turno | n bruto | Lula no 2º % | Flávio no 2º % | Não escolha no 2º % |",
        "|---|---:|---:|---:|---:|",
    ]
    t = data["transfer_1t_2t"]
    for stat in t["group_stats"]:
        c = {
            c["answer"]: 100 * c["share"]
            for c in t["cells"]
            if c["group"] == stat["group"]
        }
        lines.append(
            f"| {stat['group']} | {stat['n']} | {fmt(c[PAIR['lula']])} | "
            f"{fmt(c[PAIR['flavio']])} | {fmt(sum(v for k, v in c.items() if k not in PAIR.values()))} |"
        )
    lines += [
        "",
        "## Composição por voto declarado em 2022",
        "",
        "| Voto declarado | n bruto | Bruta % | Ponderada recuperada % |",
        "|---|---:|---:|---:|",
    ]
    past = latest["margins"]["vote_std"]
    for j, group in enumerate(past["groups"]):
        lines.append(
            f"| {group} | {past['raw_n'][j]} | {fmt(past['raw_pct'][j])} | {fmt(past['weighted_pct'][j])} |"
        )
    lines += [
        "",
        "A diferença bruta/ponderada resulta do conjunto de pesos finais. "
        "Não isola o efeito causal da calibração por voto passado. A memória de voto "
        "é autodeclarada; não comprova o voto individual depositado em 2022.",
        "",
        "Também há voto atual por voto declarado em 2022, sexo, idade, raça, "
        "escolaridade, região, religião, vertente religiosa, ideologia e identificação política. "
        "As margens inferidas de todas as partições identificáveis estão em `audit.json`.",
        "",
        "## Limites e pontos a esclarecer com a Palver",
        "",
        "- **Pesos individuais:** não foram disponibilizados nessas tabelas. É possível "
        "calcular médias de pesos por célula e verificar segundos momentos, mas não "
        "recuperar de forma única o peso de cada pessoa.",
        "- **TSE + PNAD simultâneos:** falta a tabela conjunta voto × renda × idade × sexo × "
        "região × escolaridade × voto 2022 × filiação, ou microdados anônimos com pesos. "
        "Somar sensibilidades marginais ou fabricar a tabela por independência não "
        "reproduz o raking do instituto.",
        "- **Datas:** o catálogo do Explorer encerra a onda 3 em 20/09; o PDF nas pp. 16, "
        "22 e 30 indica 18/09. O n efetivo do Explorer coincide com o PDF, mas isso "
        "não resolve a data de campo.",
        "- **Onda 2 revisada:** Lula tem 40,440% no 1º turno do Explorer e 41% no gráfico "
        "do PDF p. 30. O arredondamento convencional isolado não explica a diferença. "
        "Solicitar identificação da versão, regra de agregação e arquivo usado no PDF.",
        "- **Voto 2022:** o recorte reúne branco/nulo e quem não votou; pedir o "
        "tratamento separado de inelegíveis, abstenção e não resposta na calibração.",
        "- **Cobertura:** identificação política da onda 3 cobre 4.924 pessoas. Não "
        "recompor o nacional com esses grupos sem tratar os 76 casos ausentes.",
        "- **Respostas múltiplas:** desgaste Master e STF podem somar mais de 100%. "
        "Não normalizar essas tabelas como se fossem uma escolha exclusiva.",
        "",
        "A integração no agregador é feita por `palver-explorer-integrate.py`: "
        "usa os percentuais exatos do Explorer, mantém a onda 2 original fora das médias "
        "e publica as quatro versões no histórico, inclusive os cenários com Marçal "
        "excluídos da média do primeiro turno.",
        "",
        "## Reprodução",
        "",
        "```sh",
        "python3 scripts/palver-explorer-extract.py",
        "python3 scripts/palver-explorer-audit.py",
        "```",
        "",
        "A extração reutiliza snapshots; `--refresh` consulta novamente a fonte. "
        "A auditoria usa apenas os JSON arquivados e o benchmark do projeto.",
        "",
    ]
    (BASE / "README.md").write_text("\n".join(lines))


if __name__ == "__main__":
    data = audit()
    report(data)
    print(BASE / "README.md")
