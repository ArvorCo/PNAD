"""Monta `docs/assets/predicao_governador.json` (seção 3 do CONTRATO).

Junta seleção de ondas, pares medidos, sorteios, resumo nacional,
sensibilidades e validação. Todo número publicado sai daqui; a página não
recalcula nada.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from senado_2026 import base as SB
from senado_2026 import calibracao as C
from senado_2026 import motor as SM
from senado_2026.saida import _calibracao_resumo, _onda_usada, br

from . import base as B
from . import motor as M

REPO = "https://github.com/ArvorCo/PNAD/blob/main/"
# Classificação da disputa pela probabilidade de eleição da candidatura favorita.
CLASSES = (
    ("decidida", 0.9),
    ("provavel", 0.7),
    ("apertada", 0.0),
)


def _iso(d) -> str | None:
    return d.isoformat() if d else None


def _campo_txt(o: dict) -> str | None:
    if not o["campo_inicio"]:
        return None
    return f"{o['campo_inicio'].isoformat()} a {o['campo_fim'].isoformat()}"


def _classe(p_fav: float) -> str:
    for nome, piso in CLASSES:
        if p_fav >= piso:
            return nome
    return "apertada"


def _incerteza(cobertura: str, p_fav: float) -> str:
    if cobertura != "recente":
        return "alta"
    if p_fav >= 0.85:
        return "baixa"
    if p_fav >= 0.6:
        return "media"
    return "alta"


def _linhas_prob(cands: list[dict], r: dict) -> list[dict]:
    probs = [
        {
            "nome": c["nome"],
            "nome_urna": c["nome_urna"],
            "partido": c["partido"],
            "campo": c["campo"],
            "sq_candidato": c["sq_candidato"],
            "foto": c["foto"],
            "p_eleito": r["p_eleito"][i],
            "p_vence_1t": r["p_vence_1t"][i],
            "p_vence_2t": r["p_vence_2t"][i],
            "p_vai_2t": r["p_vai_2t"][i],
            "p_primeiro": r["p_primeiro"][i],
            "ic90_validos": r["ic90"][i],
            "validos_mediana": r["mediana"][i],
            "validos_central": c["validos"],
        }
        for i, c in enumerate(cands)
    ]
    return sorted(
        probs, key=lambda x: (-x["p_eleito"], -x["validos_central"], x["nome"])
    )


def _pares(prep: dict, r: dict) -> list[dict]:
    cands = prep["candidatos"]
    saida = []
    for par in r["pares"]:
        a, b = par["indices"]
        medido = prep["pares"].get((a, b))
        item = {
            "nomes": par["nomes"],
            "partidos": [cands[a]["partido"], cands[b]["partido"]],
            "campos": [cands[a]["campo"], cands[b]["campo"]],
            "fotos": [cands[a]["foto"], cands[b]["foto"]],
            "p_par": par["p_par"],
            "medido": bool(medido),
            "projecao": {
                par["nomes"][0]: 100 * par["fracao_a_media"],
                par["nomes"][1]: 100 * (1 - par["fracao_a_media"]),
            },
            "ic90_primeiro_nome": [100 * x for x in par["fracao_a_ic90"]],
            "p_vence_dado_par": {
                par["nomes"][0]: par["p_a_vence_dado_par"],
                par["nomes"][1]: 1 - par["p_a_vence_dado_par"],
            },
            "medicao": None,
        }
        if medido:
            item["medicao"] = {
                "fracao_primeiro_nome": 100 * medido["fracao_a"],
                "n_par": medido["n_par"],
                "recente": medido["recente"],
                "ondas": medido["ondas"],
            }
        saida.append(item)
    return saida


def _pares_medidos_lista(prep: dict) -> list[dict]:
    cands = prep["candidatos"]
    saida = []
    for (a, b), par in sorted(prep["pares"].items()):
        saida.append(
            {
                "nomes": [cands[a]["nome"], cands[b]["nome"]],
                "fracao_primeiro_nome": 100 * par["fracao_a"],
                "n_par": par["n_par"],
                "recente": par["recente"],
                "ondas": par["ondas"],
            }
        )
    return saida


def estado_saida(prep: dict, resumo: dict | None, eleitorado: dict) -> dict:
    uf = prep["uf"]
    base = {
        "uf": uf,
        "nome": B.UFS[uf],
        "eleitorado": eleitorado.get(uf),
        "pesquisas_usadas": [],
        "pesquisas_descartadas": prep["descartadas"],
        "cobertura": prep["cobertura"],
        "media": [],
        "probabilidades": [],
        "favorito": None,
        "p_favorito": None,
        "p_decide_1t": None,
        "p_segundo_turno": None,
        "pares_2t": [],
        "pares_medidos": [],
        "classe": None,
        "incerteza": "alta",
        "notas": [],
    }
    if prep["media"] is None or resumo is None:
        base["notas"].append(
            "Sem pesquisa estimulada no acervo: o estado não tem favorito nem "
            "entra nas somas nacionais."
        )
        return base
    media = prep["media"]
    cands = prep["candidatos"]
    base["pesquisas_usadas"] = [
        _onda_usada(o, w) for o, w in zip(prep["usadas"], media["pesos"], strict=True)
    ]
    base["indecisos"] = 100 * media["indecisos"]
    base["branco_nulo"] = 100 * media["branco_nulo"]
    base["outros_validos"] = 100 * media["outros_validos"]
    base["dias_ate_eleicao_ponderado"] = media["dias_ate_eleicao"]
    por_casa = defaultdict(dict)
    for casa in media["casas"]:
        soma_v = sum(casa["candidatos"]) + casa["outros"]
        for i, x in enumerate(casa["candidatos"]):
            por_casa[i][casa["onda"]["arquivo"]] = 100 * x / soma_v
    base["media"] = sorted(
        (
            {
                "nome": c["nome"],
                "nome_urna": c["nome_urna"],
                "nome_pesquisa": c["nome_pesquisa"],
                "aliases": c["aliases"],
                "partido": c["partido"],
                "campo": c["campo"],
                "sq_candidato": c["sq_candidato"],
                "foto": c["foto"],
                "valor": c["valor"],
                "validos": c["validos"],
                "validos_uniforme": c["validos_uniforme"],
                "validos_por_pesquisa": por_casa[i],
            }
            for i, c in enumerate(cands)
        ),
        key=lambda x: -x["validos"],
    )
    probs = _linhas_prob(cands, resumo)
    base["probabilidades"] = probs
    base["favorito"] = probs[0]["nome"]
    base["p_favorito"] = probs[0]["p_eleito"]
    base["p_decide_1t"] = resumo["p_decide_1t"]
    base["p_segundo_turno"] = 1 - resumo["p_decide_1t"]
    base["pares_2t"] = _pares(prep, resumo)
    base["pares_medidos"] = _pares_medidos_lista(prep)
    base["classe"] = _classe(probs[0]["p_eleito"])
    base["incerteza"] = _incerteza(prep["cobertura"], probs[0]["p_eleito"])
    base["soma_p_eleito"] = sum(resumo["p_eleito"])
    notas = base["notas"]
    lider_media = base["media"][0]["nome"]
    if lider_media != base["favorito"]:
        notas.append(
            f"A candidatura mais votada na média ({lider_media}) não é a favorita "
            f"na eleição ({base['favorito']}): o 2º turno medido inverte a ordem."
        )
    if prep["cobertura"] == "antiga":
        notas.append(
            "Nenhuma onda com campo a partir de 28/09: a média usa a onda mais "
            "recente de cada casa como prior fraca, com a deriva dos dias extras."
        )
    for o in prep["usadas"]:
        if o["campo_inferido"] == "divulgacao_menos_1_a_3_dias":
            notas.append(
                f"{o['arquivo']}: campo não publicado; inferido como 1 a 3 dias "
                "antes da divulgação."
            )
        elif o["campo_inferido"] == "data_de_divulgacao":
            notas.append(
                f"{o['arquivo']}: campo não publicado; a data de divulgação faz as "
                "vezes de fim do campo."
            )
        if o["n_assumido"]:
            notas.append(
                f"{o['arquivo']}: n não publicado; assumido o menor n do acervo "
                f"({o['n_usado']})."
            )
    for casa in media["casas"]:
        if casa["ausentes"]:
            nomes = [
                cands[j]["nome"]
                for j, p in enumerate(media["pessoas"])
                if p["chave"] in casa["ausentes"]
            ]
            notas.append(
                f"{casa['onda']['arquivo']} não lista {', '.join(nomes)}: "
                "contado como zero nessa onda."
            )
    sem_tse = [c["nome"] for c in cands if not c["sq_candidato"]]
    if sem_tse:
        notas.append(
            "Sem casamento com candidatura do TSE: " + ", ".join(sem_tse) + "."
        )
    for nc in prep["pares_nao_casados"]:
        notas.append(
            f"{nc['arquivo']}: par de 2º turno {nc['par'][0]} × {nc['par'][1]} não "
            "casa com a lista do 1º turno e ficou fora."
        )
    if not prep["pares"]:
        notas.append(
            "Nenhum par de 2º turno medido: a projeção de 2º turno usa a "
            "transferência declarada por campo."
        )
    return base


def _comparar(central: dict, alt: dict) -> list[dict]:
    mudam = []
    for uf, r in central["resumos"].items():
        if uf not in alt["resumos"]:
            continue
        a = max(range(len(r["p_eleito"])), key=lambda i: r["p_eleito"][i])
        b = max(
            range(len(alt["resumos"][uf]["p_eleito"])),
            key=lambda i: alt["resumos"][uf]["p_eleito"][i],
        )
        if a != b:
            mudam.append({"uf": uf, "central": a, "sensibilidade": b})
    return mudam


def _justificativa_erro(erro: SM.Erro, cal: dict | None) -> str:
    if erro.fonte != "wikipedia_2022" or not cal:
        return (
            "Hipótese declarada: desvio de "
            f"{br(C.HIPOTESE['sd_pp_30'])} pontos dos válidos para candidatura em 30%, "
            "sem calibração conferível de governador."
        )
    est = cal["estatisticas"]["casas_principais"]
    comp = est["candidaturas_entre_20_e_40_pct"]
    cob = cal["cobertura"]
    return (
        f"Calibrado com {cob['n_pesquisas_casas_principais']} pesquisas finais de "
        f"Datafolha, Ipec e Quaest para governador em {cob['n_estados_casas_principais']} "
        "estados na eleição de 2022 contra a urna (TSE, cargo 3), por "
        "scripts/governador-2026-calibracao.py. Entre candidaturas que fizeram de "
        f"20% a 40% dos válidos, a raiz do erro quadrático médio foi {br(comp['rmse'])} "
        f"pontos (n = {comp['n']}), com a amostragem dentro. A escala no log das "
        "frações é a variância não amostral das candidaturas com ao menos 10% dos "
        "válidos, descontadas a parte amostral (n / 1,5) e a deriva medida entre "
        "ondas seguidas da mesma casa. O efeito de campo comum entra simétrico, nas "
        "duas direções: o viés de 2022 não desloca a central."
    )


def prever(
    ondas: list[dict],
    tse: B.Tse,
    eleitorado: dict,
    cal: dict | None,
    *,
    simulacoes: int = M.SIMULACOES,
    semente: int = M.SEMENTE,
    mistura_uniforme: float = SM.MISTURA_UNIFORME,
    deff: float = SM.DEFF,
    sensibilidades: bool = True,
    agora: datetime | None = None,
) -> dict:
    erro, detalhe = SM.erro_calibrado(cal)
    preps = [M.preparar_estado(uf, ondas, tse) for uf in B.UFS]
    kw = {"simulacoes": simulacoes, "semente": semente, "deff": deff}
    central = M.rodar(preps, erro, mistura_uniforme=mistura_uniforme, **kw)
    estados = {
        p["uf"]: estado_saida(p, central["resumos"].get(p["uf"]), eleitorado)
        for p in preps
    }
    nac = M.nacional(central)
    sens = []
    if sensibilidades:
        for chave, rotulo, descricao, e, mist, pares in (
            (
                "erro_dobrado",
                "Erro dobrado",
                "Desvios do erro não amostral e da deriva multiplicados por 2.",
                erro.escalado(2.0),
                mistura_uniforme,
                True,
            ),
            (
                "indecisos_uniformes",
                "Indecisos 100% uniformes",
                "Todo sorteio reparte os indecisos igualmente entre os nomes com ao "
                "menos 1 ponto.",
                erro,
                1.0,
                True,
            ),
            (
                "sem_pares_medidos",
                "Sem os pares medidos",
                "Todo 2º turno sai da transferência declarada por campo, ignorando "
                "as medições de 2º turno dos institutos.",
                erro,
                mistura_uniforme,
                False,
            ),
        ):
            alt = M.rodar(preps, e, mistura_uniforme=mist, usar_pares=pares, **kw)
            nac_alt = M.nacional(alt)
            mudam = _comparar(central, alt)
            for m in mudam:
                cands = preps[list(B.UFS).index(m["uf"])]["candidatos"]
                m["central"] = cands[m["central"]]["nome"]
                m["sensibilidade"] = cands[m["sensibilidade"]]["nome"]
            sens.append(
                {
                    "chave": chave,
                    "rotulo": rotulo,
                    "descricao": descricao,
                    "favoritos_que_mudam": mudam,
                    "decididos_1t_esperado": (nac_alt.get("decididos_1t") or {}).get(
                        "esperado"
                    ),
                    "por_grupo": {
                        g: v["esperado"]
                        for g, v in nac_alt.get("por_grupo", {}).items()
                    },
                    "p_decide_1t": {
                        uf: r["p_decide_1t"] for uf, r in alt["resumos"].items()
                    },
                }
            )
    usadas = [o for p in preps for o in p["usadas"]]
    discordam = []
    for p in preps:
        if p["media"] is None or len(p["usadas"]) < 2:
            continue
        lideres = {}
        nomes = [c["nome"] for c in p["candidatos"]]
        for casa in p["media"]["casas"]:
            v = casa["candidatos"]
            lideres[casa["onda"]["arquivo"]] = nomes[
                max(range(len(v)), key=v.__getitem__)
            ]
        if len(set(lideres.values())) > 1:
            discordam.append({"uf": p["uf"], "lider_por_pesquisa": lideres})
    sem_tse = sorted(
        {
            (p["uf"], c["nome_pesquisa"])
            for p in preps
            for c in p["candidatos"]
            if not c["sq_candidato"]
        }
    )
    somas = [e["soma_p_eleito"] for e in estados.values() if "soma_p_eleito" in e]
    recomp = [SB.recomposicao(o) for o in ondas]
    validacao = {
        "recomposicao": recomp,
        "recomposicao_maior_diferenca_pp": max(
            (abs(r["diferenca"]) for r in recomp if r["diferenca"] is not None),
            default=None,
        ),
        "fechamento_maior_desvio_pp": max(
            (
                abs(SB.recomposicao(o)["fechamento_em_100"])
                for o in ondas
                if SB.motivo_descarte(o) is None
            ),
            default=None,
        ),
        "casas_discordam_lider": discordam,
        "soma_p_eleito_maior_desvio": max((abs(s - 1) for s in somas), default=None),
        "sem_candidatura_tse": [{"uf": u, "nome_pesquisa": n} for u, n in sem_tse],
        "apelidos_tse": tse.via_apelido,
        "ambiguidades_tse": tse.ambiguidades,
        "pares_2t_nao_casados": [
            {"uf": p["uf"], **nc} for p in preps for nc in p["pares_nao_casados"]
        ],
        "pares_2t_medidos_total": sum(len(p["pares"]) for p in preps),
        "ufs_com_par_medido": sorted(p["uf"] for p in preps if p["pares"]),
        "campo_inferido": [
            {
                "arquivo": o["arquivo"],
                "regra": o["campo_inferido"],
                "campo": _campo_txt(o),
            }
            for o in usadas
            if o["campo_inferido"]
        ],
        "n_assumido": [
            {"arquivo": o["arquivo"], "n_usado": o["n_usado"]}
            for o in usadas
            if o["n_assumido"]
        ],
        "calibracao_2022": {
            **_calibracao_resumo(cal, erro),
            "url": REPO + "analysis/governador_2026/calibracao_2022.json",
            "cargo": "governador",
        },
        "sensibilidades": sens,
    }
    agora = agora or datetime.now(timezone.utc)
    escala = SM.sd_pp(erro)
    parametros = {
        "meia_vida_dias": B.MEIA_VIDA_DIAS,
        "janela_campo_minimo": B.CORTE_CAMPO.isoformat(),
        "inferencia_campo_divulgacao_desde": SB.CORTE_INFERENCIA.isoformat(),
        "simulacoes": simulacoes,
        "semente": semente,
        "deff": deff,
        "justificativa_deff": (
            "Kish com cerca de 6 entrevistas por setor censitário e correlação "
            "intraclasse perto de 0,1: deff = 1 + 5 x 0,1 = 1,5. Hipótese declarada."
        ),
        "mistura_indecisos": {
            "proporcional": 1 - mistura_uniforme,
            "uniforme": mistura_uniforme,
        },
        "limiar_uniforme_pp": SB.LIMIAR_UNIFORME_PP,
        "indecisos_regra": (
            "Central: indecisos repartidos na proporção do voto declarado. "
            "Uniforme: indecisos repartidos em partes iguais entre os nomes com ao "
            "menos 1 ponto. Branco e nulo nunca viram voto válido. Em cada sorteio "
            "um dos dois cenários é escolhido com as probabilidades acima."
        ),
        "maioria": M.MAIORIA,
        "regra_1t": (
            "Eleição no 1º turno quando a candidatura mais votada passa de 50% dos "
            "votos válidos (candidaturas e 'outros'; branco, nulo e indecisos fora). "
            "Senão, as duas mais votadas disputam o 2º turno."
        ),
        "regra_2t_medido": (
            "Par medido pelo instituto: a fração publicada do primeiro nome entre "
            "os dois, combinada por recência entre as casas que mediram o par, "
            "recebe o ruído amostral do par, a deriva até a eleição e a mesma "
            "diferença de choques não amostrais do 1º turno (quem errou o campo no "
            "1º turno erra no 2º)."
        ),
        "regra_2t_transferencia": (
            "Par não medido: cada candidatura eliminada transfere "
            f"{br(100 * M.TRANSFERENCIA_VALIDA, 0)}% do voto a um dos finalistas, "
            "dividido por proximidade entre campos (softmax de menos a distância na "
            "reta esquerda, centro-esquerda, centro, centro-direita, direita, "
            f"temperatura {br(M.TRANSFERENCIA_TAU)}); o resto vira branco, nulo ou "
            f"abstenção. Ruído extra de {br(M.SD_TRANSFERENCIA_LOGIT, 2)} no logit. "
            "Hipótese declarada, sem medição."
        ),
        "transferencia": {
            "fracao_valida": M.TRANSFERENCIA_VALIDA,
            "tau": M.TRANSFERENCIA_TAU,
            "sd_logit": M.SD_TRANSFERENCIA_LOGIT,
            "posicoes": M.POSICAO,
        },
        "erro": {
            **SM.descrever_erro(erro),
            **detalhe,
            "fracao_estadual_do_resto": SM.FRACAO_ESTADUAL,
            "corrida_referencia_pct": list(SM.CORRIDA_REFERENCIA),
        },
        "escala_erro_pp": escala,
        "escala_erro_pp_com_deriva_7_dias": SM.sd_pp(erro, dias=7),
        "justificativa_erro": _justificativa_erro(erro, cal),
        "decomposicao_erro": (
            "Logística-normal: ao log da fração válida de cada candidatura somam-se "
            "um choque do campo comum a todos os estados (variância "
            f"{br(erro.var_nacional, 4)}), um choque do campo no estado "
            f"({br(erro.var_estadual, 4)}), um choque próprio ({br(erro.var_idio, 4)}) e "
            f"a deriva de {br(erro.var_deriva_dia, 5)} por dia até 04/10; depois "
            "renormaliza."
        ),
        "classes_regra": (
            "decidida: favorita com 90% ou mais de chance; provável: de 70% a 90%; "
            "apertada: abaixo de 70%."
        ),
        "incerteza_regra": (
            "alta quando a cobertura não é recente ou a favorita tem menos de 60%; "
            "média de 60% a 85%; baixa acima."
        ),
        "campo_classificacao": (
            "Campo é classificação editorial da casa (PARTIDO_CAMPO em "
            "scripts/voto_util_base.py): tucano é centro-esquerda; PSD, MDB e "
            "Avante, centro; União, PP, Podemos, PRD, Agir e Mobiliza, "
            "centro-direita; PL, Novo, Republicanos, PRTB, DC, Democrata e Missão, "
            "direita. Partido vem do TSE quando o nome casa, senão da pesquisa."
        ),
        "o_que_nao_faz": (
            "Não prevê votos; não modela desistência, coligação nem comparecimento; "
            "não usa o resultado de 2022 como prior de nome; os cenários "
            "alternativos de 1º turno dos institutos ficam fora da média."
        ),
    }
    fontes = [
        {
            "arquivo": o["arquivo"],
            "instituto": o["instituto"],
            "uf": o["uf"],
            "campo": _campo_txt(o),
            "campo_inferido": bool(o["campo_inferido"]),
            "n": o["n"],
            "registro_tse": o["registro_tse"],
            "url": o["fonte"]["url"] or o["fonte"]["painel_url"],
            "pagina": o["fonte"]["pagina"],
            "arquivo_bruto": o["fonte"]["arquivo"],
            "sha256": o["fonte"]["sha256"],
            "pares_2t": len(o["segundo_turno"]),
        }
        for o in sorted(usadas, key=lambda o: (o["uf"], o["arquivo"]))
    ]
    # Ondas usadas só pelo 2º turno (não entraram na média do 1º turno).
    arquivos_usados = {f["arquivo"] for f in fontes}
    for p in preps:
        for par in p["pares"].values():
            for onda_par in par["ondas"]:
                if onda_par["arquivo"] in arquivos_usados:
                    continue
                o = next(x for x in ondas if x["arquivo"] == onda_par["arquivo"])
                arquivos_usados.add(o["arquivo"])
                fontes.append(
                    {
                        "arquivo": o["arquivo"],
                        "instituto": o["instituto"],
                        "uf": o["uf"],
                        "campo": _campo_txt(o),
                        "campo_inferido": bool(o["campo_inferido"]),
                        "n": o["n"],
                        "registro_tse": o["registro_tse"],
                        "url": o["fonte"]["url"] or o["fonte"]["painel_url"],
                        "pagina": o["fonte"]["pagina"],
                        "arquivo_bruto": o["fonte"]["arquivo"],
                        "sha256": o["fonte"]["sha256"],
                        "pares_2t": len(o["segundo_turno"]),
                        "so_segundo_turno": True,
                    }
                )
    fontes.sort(key=lambda f: (f["uf"], f["arquivo"]))
    ranking = sorted(
        (e for e in estados.values() if e["p_favorito"] is not None),
        key=lambda e: (e["p_favorito"], -e["p_segundo_turno"]),
    )
    return {
        "gerado_em": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_referencia": B.DATA_REFERENCIA.isoformat(),
        "eleicao": B.ELEICAO.isoformat(),
        "segundo_turno_data": "2026-10-25",
        "parametros": parametros,
        "estados": estados,
        "nacional": {
            **nac,
            "ranking_apertadas": [e["uf"] for e in ranking],
            "por_classe": {
                k: sorted(e["uf"] for e in estados.values() if e["classe"] == k)
                for k, _ in CLASSES
            },
            "sem_pesquisa": sorted(
                e["uf"] for e in estados.values() if e["cobertura"] == "sem_pesquisa"
            ),
        },
        "validacao": validacao,
        "fontes": fontes,
    }
