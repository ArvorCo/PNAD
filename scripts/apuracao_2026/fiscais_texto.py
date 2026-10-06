"""Achados, limites e memorando do capítulo 13 (onde colocar fiscal).

Toda frase sai dos números gravados no JSON do capítulo; nada é digitado à mão.
Vocabulário: "atípico" e "exige explicação documental"; nunca "fraude". Toda
frase pública carrega o rótulo: atipicidade estatística não é irregularidade, a
lista é de prioridade de fiscalização, não de acusação, e o que resolve cada item é
a ata da mesa, o log da urna e a presença do fiscal.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from .fiscais_regras import AVISO, CRITERIOS, ROTULOS
from .secoes_base import num

NOME_NIVEL = {"alta": "alta", "media": "média", "baixa": "baixa"}

LIMITES = [
    "Atipicidade estatística não é irregularidade: cada critério aponta seção que pede "
    "explicação, não seção com irregularidade. A lista é de prioridade de fiscalização, "
    "não de acusação.",
    "O boletim de urna mostra quanto se votou, não por quê. O que separa liderança local, "
    "erro de mesário, fila e irregularidade é a ata da mesa, o log da urna e a presença do "
    "fiscal no dia.",
    "Pesos e cortes de nível são juízo editorial declarado; a sensibilidade a pesos iguais "
    "fica publicada ao lado.",
    "Tipo de local (aldeia, presídio, zona rural, hospital) é inferência por palavra-chave "
    "no cadastro do TSE, não verificação no terreno.",
    "Excesso sobre a zona compara a seção com o resto da própria zona; zona com uma seção "
    "só não tem régua e fica fora dos critérios que dependem dela.",
    "O casamento com 2022 exige mesmo número de seção e mesmo nome de local; seção "
    "renumerada ou mudada de prédio fica sem comparação (critérios a, enclave, e j).",
    "A mistura gaussiana cobre só as seções válidas do capítulo 12; as três zonas "
    "divergentes (Betim 319, Uberlândia 279, Carapicuíba 388) entram nos demais critérios.",
    "As 20 seções sem aux.json publicado não têm voto conhecido: entram só pelo critério h.",
    "O 2º turno tem outra cédula e outro comparecimento: a lista prioriza onde houve "
    "atipicidade no 1º turno, não prevê o que vai acontecer no 2º.",
    "A camada de risco do território é contexto público com data, não avaliação de "
    "segurança: o nível de risco fiscal é regra declarada e deve ser validado com a PM e o "
    "TRE local antes de mandar alguém ao local.",
    "Crime organizado só aparece onde há mapeamento público documentado; ausência de "
    "mapeamento não é ausência de risco.",
]


def base_legal(fechamento: Mapping[str, Any]) -> list[dict[str, Any]]:
    """As fontes legais sobre fiscal já conferidas no capítulo de encerramento."""
    out = []
    for f in fechamento.get("fontes_legais", []):
        norma = str(f.get("norma", ""))
        disp = str(f.get("dispositivo", ""))
        if "9.504" in norma or "art. 132" in disp:
            out.append(
                {
                    "norma": norma,
                    "dispositivo": disp,
                    "conteudo": f.get("conteudo"),
                    "como_conferido": f.get("como_conferido"),
                    "fonte": "analysis/apuracao_2026/dados/fechamento.json",
                }
            )
    return out


def _pct(a: float, b: float) -> str:
    return num(100 * a / b, 1) if b else "n/d"


def leitura_sensibilidade(s: Mapping[str, Any]) -> str:
    return (
        f"Com pesos iguais, {num(s['mudam_nivel'], 0)} seções mudam de nível "
        f"({num(s['mudam_nivel_pct'] or 0, 1)}%); a correlação de postos entre as duas "
        f"pontuações é {num(s['spearman_pontuacao'] or 0, 3)}; dos 100 locais de maior "
        f"pontuação, {s['top100_locais_comum']} continuam entre os 100 primeiros, e dos 100 "
        f"municípios, {s['top100_municipios_comum']}."
    )


def _local_txt(r: Mapping[str, Any]) -> str:
    end = ", ".join(x for x in (r.get("endereco"), r.get("bairro")) if x)
    return (
        f"{r.get('local')} ({end}), {r['municipio']} ({r['uf']}), zona {r['zona']}"
        if end
        else f"{r.get('local')}, {r['municipio']} ({r['uf']}), zona {r['zona']}"
    )


def achados(d: Mapping[str, Any]) -> dict[str, list[str]]:
    r = d["resumo"]
    u = d["meta"]["universo"]
    crit = {c["id"]: c for c in d["criterios"]}
    pn = r["por_nivel"]
    n = r["secoes_sinalizadas"]
    cong = d["zonas_congeladas"]
    sem = d["sem_arquivo"]
    mist = d["meta"]["mistura"]["conferencia"]
    verificado = [
        f"Universo: {num(u['secoes_universo'], 0)} seções, das quais "
        f"{num(u['secoes_validas_cap12'], 0)} são as válidas do capítulo 12, "
        f"{num(u['secoes_zona_divergente_integras'], 0)} têm boletim íntegro nas três "
        "zonas que divergem do arquivo de zona do TSE e "
        f"{u['secoes_sem_arquivo']} não têm arquivo publicado.",
        f"{num(n, 0)} seções disparam ao menos um critério ({_pct(n, u['secoes_universo'])}% "
        f"do universo), em {num(d['resumo']['fiscais']['um_por_local']['todos'], 0)} locais "
        f"de votação: {num(pn['alta']['secoes'], 0)} em nível alta, "
        f"{num(pn['media']['secoes'], 0)} em média e {num(pn['baixa']['secoes'], 0)} em "
        f"baixa. {ROTULOS['atipico']}",
        "Seções por critério: "
        + "; ".join(
            f"{c['id']} ({c['nome']}) {num(c['secoes'], 0)}" for c in d["criterios"]
        )
        + ".",
        f"A mistura gaussiana do capítulo 12 foi refeita com a semente gravada: "
        f"{mist['iguais']} das {mist['comparadas']} seções menos prováveis publicadas "
        f"saem iguais, com diferença máxima de {num(mist['maior_diferenca_loglik'], 3)} na "
        "log-verossimilhança.",
    ]
    if cong:
        conferem = sum(1 for z in cong if z.get("conferem"))
        faltam = sum(int(z.get("secoes_faltando") or 0) for z in cong)
        horas = [z["horas_parada"] for z in cong]
        verificado.append(
            f"{len(cong)} arquivos de zona de presidente ficaram parados incompletos por "
            f"{num(min(horas), 1)} a {num(max(horas), 1)} horas depois da última versão "
            f"gerada perto das 21h de Brasília, com {faltam} seções faltando. Em "
            f"{conferem} das {len(cong)} zonas, as seções que faltavam são exatamente as "
            "recebidas no último minuto antes da versão parada, separadas das anteriores "
            "por 30 segundos ou mais: o lote chegou e não entrou na totalização da zona. "
            "Os votos estão no arquivo da UF."
        )
    if sem:
        por = {}
        for s in sem:
            por[(s["municipio"], s["uf"], s["zona"])] = (
                por.get((s["municipio"], s["uf"], s["zona"]), 0) + 1
            )
        verificado.append(
            f"{len(sem)} seções principais ativas não têm aux.json publicado (o TSE devolve "
            "404): "
            + "; ".join(
                f"{m} ({uf}), zona {z}: {k}" for (m, uf, z), k in sorted(por.items())
            )
            + ". Exigem explicação documental: o boletim impresso afixado e a cópia pedida "
            "ao presidente da mesa resolvem."
        )
    inferido = []
    a = crit["a"]
    inferido.append(
        f"O critério a (90% ou mais com excesso de 20 pontos sobre a zona) dispara em "
        f"{num(a['secoes'], 0)} seções; {num(r['enclaves_2022'], 0)} delas já votavam "
        "assim em 2022 e ficam em nível baixa como enclaves."
    )
    k = crit["k"]
    inferido.append(
        f"O critério que mais sinaliza é o de brancos ou nulos muito acima da zona "
        f"({num(k['secoes'], 0)} seções, {num(k['so_este'], 0)} só por ele); com peso 1, "
        f"quase todas ficam em nível baixa ({num(k['secoes_por_nivel']['baixa'], 0)})."
    )
    inferido.append(d["sensibilidade"]["leitura"])
    f = r["fiscais"]
    juizo = [
        f"Um fiscal por local cobre as seções de nível alta em "
        f"{num(f['um_por_local']['alta'], 0)} locais e as de alta e média em "
        f"{num(f['um_por_local']['alta_media'], 0)}; um por seção pede "
        f"{num(f['um_por_secao']['alta_media'], 0)} fiscais para alta e média e "
        f"{num(f['um_por_secao']['todos'], 0)} para a lista inteira. A lei permite que um "
        "fiscal cubra várias seções do mesmo local (Lei 9.504, art. 65, § 1º).",
        d["prioridade_pl"]["leitura"],
    ]
    top = d["prioridade_pl"]["geral"]["municipios"][:5]
    if top:
        juizo.append(
            "Pela pontuação somada, os cinco municípios que pedem mais fiscal são "
            + "; ".join(
                f"{m['municipio']} ({m['uf']}), {num(m['secoes'], 0)} seções"
                for m in top
            )
            + f". {ROTULOS['prioridade']}"
        )
    hipotese = [
        "Seção quase unânime, com zero voto num dos dois ou com comparecimento total, sem "
        "explicação comum, pode vir de liderança local, de erro de mesário, de eleitor "
        "levado em bloco ou de irregularidade. O boletim não separa essas hipóteses: "
        f"{ROTULOS['resolve'][0].lower()}{ROTULOS['resolve'][1:]}",
        "Seção que encerrou depois das 19h com Lula muito acima da zona pode ser fila longa "
        "em área pobre (o efeito típico dentro da zona está no capítulo de encerramento) ou "
        "pode pedir conferência das habilitações por ano de nascimento no fim do dia; só o "
        "log da urna separa as duas.",
    ]
    ec = r["explicacao_comum"]
    contrario = [
        f"Das {num(ec['baixa'], 0)} seções de nível baixa, {num(ec['baixa_aldeia_presidio'], 0)} "
        "são aldeias ou unidades prisionais pelo cadastro: a explicação comum documentada "
        "desarma boa parte do que parece bizarro.",
        f"{num(ec['secoes'], 0)} das {num(n, 0)} seções sinalizadas têm explicação comum "
        "documentada (aldeia, presídio, exterior, trânsito ou seção minúscula) e por regra "
        "nunca chegam a nível alta.",
    ]
    bruto = sorted(d["por_local"], key=lambda x: (-x["pontuacao_soma"], -x["secoes"]))
    if bruto:
        dez = bruto[:10]
        nao_alta = sum(1 for x in dez if x["nivel"] != "alta")
        ind = sum(
            1
            for x in dez
            if x.get("tipo_local_inferido") == "aldeia ou terra indígena"
            or (x.get("risco") or {}).get("terra_indigena")
        )
        contrario.append(
            f"Pela pontuação bruta, {nao_alta} dos 10 locais mais pontuados não chegam a "
            f"nível alta e {ind} ficam em aldeia ou terra indígena: são lugares que votam "
            "em bloco e somam muitas seções no mesmo prédio. Por isso a lista de "
            "prioridade ordena primeiro pelo nível, que separa a explicação comum, e só "
            "depois pela pontuação."
        )
    fl = sum(
        1
        for s in d["secoes"]
        if "a" in s["criterios"] and s["detalhe"]["a"]["candidato"] == "flavio"
    )
    contrario.append(
        f"A atipicidade não tem lado só: {num(fl, 0)} das {num(a['secoes'], 0)} seções do "
        "critério a são de Flávio com 90% ou mais, e o fiscal que vigia uma seção protege "
        "os dois votos."
    )
    return {
        "verificado": verificado,
        "inferido": inferido,
        "juizo": juizo,
        "hipotese": hipotese,
        "contrario": contrario,
    }


# ---------------------------------------------------------------- memorando


def _tabela(cab: Sequence[str], linhas: Sequence[Sequence[Any]]) -> list[str]:
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    for linha in linhas:
        out.append("| " + " | ".join("" if v is None else str(v) for v in linha) + " |")
    return out


def memorando(d: Mapping[str, Any]) -> str:
    r = d["resumo"]
    m = d["meta"]
    L: list[str] = [
        "# Onde colocar fiscal: prioridade de fiscalização por seção, 2º turno de 2026",
        "",
        f"Gerado em {d['gerado_em']} por `scripts/apuracao-2026-fiscais.py`. Dados em "
        "`analysis/apuracao_2026/dados/fiscais.json` (contrato em "
        "`analysis/apuracao_2026/CONTRATO_FISCAIS.md`, versão "
        f"{d['versao_contrato']}).",
        "",
        f"> {AVISO}",
        "",
        "## Método",
        "",
        "- Universo: as seções válidas do capítulo 12, as seções com boletim íntegro das "
        "três zonas que divergem do arquivo de zona do TSE e as seções principais ativas "
        "sem arquivo publicado. Zona, município e UF recalculados sobre esse universo.",
        "- Doze critérios com limiar declarado; pontuação = soma de pesos; nível por cortes "
        "declarados. " + m["cortes_nivel"]["regra"] + ".",
        "- Pesos: " + "; ".join(f"{k} {v}" for k, v in m["pesos"].items()) + ".",
        "- Explicação comum documentada (tira a seção do nível alta): "
        + "; ".join(
            f"{e['rotulo']} ({e['regra']})"
            for e in m["explicacoes_comuns"]
            if e["grupo"] == "comum_documentada"
        )
        + ".",
        "",
        "## Critérios",
        "",
    ]
    L += _tabela(
        ["id", "nome", "regra", "peso", "seções", "alta", "média", "baixa", "só este"],
        [
            [
                c["id"],
                c["nome"],
                c["regra"],
                c["peso"] if not isinstance(c["peso"], dict) else "3 ou 1",
                num(c["secoes"], 0),
                c["secoes_por_nivel"]["alta"],
                num(c["secoes_por_nivel"]["media"], 0),
                num(c["secoes_por_nivel"]["baixa"], 0),
                num(c["so_este"], 0),
            ]
            for c in d["criterios"]
        ],
    )
    L += ["", "Explicação comum e o que o fiscal confere:", ""]
    L += [
        f"- **{c['id']}**: explicação comum: {c['explicacao_comum']}. O fiscal confere: "
        f"{c['o_que_conferir']}."
        for c in d["criterios"]
    ]
    L += ["", "## Resultado", ""]
    L += _tabela(
        [
            "nível",
            "seções",
            "locais",
            "municípios",
            "aptos das seções",
            "aptos dos locais",
        ],
        [
            [
                NOME_NIVEL[n],
                num(v["secoes"], 0),
                num(v["locais"], 0),
                num(v["municipios"], 0),
                num(v["aptos"], 0),
                num(v["aptos_locais"], 0),
            ]
            for n, v in r["por_nivel"].items()
        ],
    )
    el = r["eleitorado"]
    fi = r["fiscais"]
    L += [
        "",
        f"- Eleitorado das seções sinalizadas: {num(el['aptos_sinalizadas'], 0)} aptos "
        f"({num(el['pct_sinalizadas'] or 0, 2)}% do universo); dos locais inteiros que as "
        f"contêm: {num(el['aptos_locais_sinalizados'], 0)} ({num(el['pct_locais'] or 0, 2)}%).",
        f"- Fiscais, um por local: alta {num(fi['um_por_local']['alta'], 0)}; alta e média "
        f"{num(fi['um_por_local']['alta_media'], 0)}; todos {num(fi['um_por_local']['todos'], 0)}.",
        f"- Fiscais, um por seção: alta {num(fi['um_por_secao']['alta'], 0)}; alta e média "
        f"{num(fi['um_por_secao']['alta_media'], 0)}; todos {num(fi['um_por_secao']['todos'], 0)}. "
        f"Base legal: {fi['base_legal']}.",
        "",
        "### Os 10 municípios de maior pontuação somada",
        "",
    ]
    L += _tabela(
        [
            "#",
            "município",
            "seções",
            "alta",
            "média",
            "locais",
            "pontuação",
            "Flávio × Lula (%)",
        ],
        [
            [
                i + 1,
                f"{x['municipio']} ({x['uf']})",
                num(x["secoes"], 0),
                x["alta"],
                x["media"],
                num(x["locais"], 0),
                num(x["pontuacao_soma"], 0),
                f"{num(x['flavio_pct'] or 0, 1)} × {num(x['lula_pct'] or 0, 1)}",
            ]
            for i, x in enumerate(
                sorted(d["por_municipio"], key=lambda x: x["posicao_pontuacao"])[:10]
            )
        ],
    )
    L += [
        "",
        "### Os 10 primeiros locais (nível do local, depois pontuação somada)",
        "",
    ]
    top_l = d["por_local"][:10]
    L += _tabela(
        [
            "#",
            "local e endereço",
            "seções sinalizadas",
            "nível",
            "pontuação",
            "critérios",
        ],
        [
            [
                i + 1,
                _local_txt(x),
                f"{x['secoes']} de {x['secoes_local']}",
                NOME_NIVEL.get(x["nivel"], x["nivel"]),
                x["pontuacao_soma"],
                ", ".join(f"{k} {v}" for k, v in x["criterios"].items()),
            ]
            for i, x in enumerate(top_l)
        ],
    )
    if d["zonas_congeladas"]:
        L += ["", "### Arquivos de zona parados incompletos", ""]
        L += _tabela(
            [
                "UF",
                "município (TSE)",
                "zona",
                "versão parada (Brasília)",
                "horas",
                "faltavam",
                "identificadas",
                "conferem",
            ],
            [
                [
                    z["uf"],
                    z["mun_tse"],
                    z["zona"],
                    z.get("ultima_incompleta_brasilia"),
                    num(z["horas_parada"], 1),
                    z["secoes_faltando"],
                    z.get("secoes_identificadas"),
                    "sim" if z.get("conferem") else "não",
                ]
                for z in d["zonas_congeladas"]
            ],
        )
    s = d["sensibilidade"]
    L += [
        "",
        "## Sensibilidade a pesos iguais",
        "",
        s["regra"] + ".",
        "",
        s["leitura"],
        "",
    ]
    L += _tabela(
        ["nível com pesos", "nível com pesos iguais", "seções"],
        [
            [
                NOME_NIVEL[x["nivel_pesos"]],
                NOME_NIVEL[x["nivel_iguais"]],
                num(x["secoes"], 0),
            ]
            for x in s["matriz"]
        ],
    )
    L += [
        "",
        "## Risco e contexto do território",
        "",
        m["risco_regra"]["texto"] + ".",
        "",
    ]
    L += _tabela(
        ["camada", "fonte", "status", "seções cobertas", "motivo"],
        [
            [
                f.get("camada"),
                f.get("nome") or f.get("chave"),
                f.get("status"),
                f.get("cobertura_secoes"),
                f.get("motivo"),
            ]
            for f in m["fontes_risco"]
        ],
    )
    L += ["", "## Exportáveis", ""]
    L += [
        f"- `{e['caminho']}`: {e['conteudo']}; {num(e['linhas'], 0)} linhas; "
        f"{num(e['bytes'] / 1e6, 2)} MB; SHA-256 `{e['sha256']}`."
        for e in m["exportaveis"]
    ]
    for chave, titulo in (
        ("verificado", "Verificado"),
        ("inferido", "Inferido"),
        ("juizo", "Juízo editorial"),
        ("hipotese", "Hipótese"),
        ("contrario", "Achado contrário"),
    ):
        L += ["", f"## {titulo}", ""]
        L += [f"- {x}" for x in d["achados"][chave]]
    L += ["", "## Limites", ""]
    L += [f"- {x}" for x in d["limites"]]
    L += ["", "## Fontes", ""]
    L += [
        f"- `{f['caminho']}`: {f['descricao']}; {num(f['bytes'], 0)} bytes; "
        + (
            f"SHA-256 `{f['sha256']}`."
            if f.get("sha256")
            else f"{f.get('motivo_sem_hash')}."
        )
        for f in m["fontes"]
    ]
    L += [
        f"- {b['norma']}, {b['dispositivo']}: {b['conteudo']}. {b['como_conferido']}."
        for b in m["base_legal"]
    ]
    texto = "\n".join(L) + "\n"
    if "—" in texto:
        raise ValueError("travessão no memorando")
    return texto


__all__ = ["CRITERIOS", "LIMITES", "achados", "base_legal", "memorando"]
