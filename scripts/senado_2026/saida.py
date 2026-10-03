"""Monta `docs/assets/predicao_senado.json` no esquema da seção 3 do CONTRATO.

Junta seleção de ondas, sorteios, composição de 2027, sensibilidades e
validação. Todo número publicado sai daqui; a página não recalcula nada.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from . import base as B
from . import calibracao as C
from . import motor as M
from . import senado as S

REPO = "https://github.com/ArvorCo/PNAD/blob/main/"
INCERTEZA = {"baixa": 0.6, "media": 0.35}
# Diferença entre a primeira e a segunda dupla abaixo da qual a dupla mais
# provável é tratada como empate (cerca de 7 erros-padrão de Monte Carlo com
# 20 mil sorteios).
EMPATE_DUPLA = 0.02


def br(x: float, casas: int = 1) -> str:
    """Número no formato brasileiro, vírgula decimal."""
    return f"{x:.{casas}f}".replace(".", ",")


def _iso(d) -> str | None:
    return d.isoformat() if d else None


def _campo_txt(o: dict) -> str | None:
    if not o["campo_inicio"]:
        return None
    return f"{o['campo_inicio'].isoformat()} a {o['campo_fim'].isoformat()}"


def _onda_usada(o: dict, peso: float) -> dict:
    return {
        "arquivo": o["arquivo"],
        "instituto": o["instituto"],
        "casa": o["casa"],
        "peso": peso,
        "campo_inicio": _iso(o["campo_inicio"]),
        "campo_fim": _iso(o["campo_fim"]),
        "campo": _campo_txt(o),
        "campo_inferido": bool(o["campo_inferido"]),
        "regra_campo": o["campo_inferido"],
        "divulgacao": _iso(o["divulgacao"]),
        "dias_ate_eleicao": (B.ELEICAO - o["campo_fim"]).days,
        "n": o["n"],
        "n_usado": o["n_usado"],
        "n_assumido": o["n_assumido"],
        "votos_por_eleitor": o["votos_por_eleitor"],
        "registro_tse": o["registro_tse"],
        "url": o["fonte"]["url"] or o["fonte"]["painel_url"],
        "pagina": o["fonte"]["pagina"],
        "retiradas": o["retiradas"],
    }


def _incerteza(cobertura: str, p_dupla: float) -> str:
    if cobertura != "recente":
        return "alta"
    if p_dupla >= INCERTEZA["baixa"]:
        return "baixa"
    if p_dupla >= INCERTEZA["media"]:
        return "media"
    return "alta"


def _dupla_lider_por_casa(prep: dict) -> dict[str, list[str]]:
    """Os dois maiores de cada casa, nos válidos da própria casa."""
    saida = {}
    nomes = [c["nome"] for c in prep["candidatos"]]
    for casa in prep["media"]["casas"]:
        v = casa["candidatos"]
        ordem = sorted(range(len(v)), key=lambda i: -v[i])[:2]
        saida[casa["onda"]["arquivo"]] = sorted(nomes[i] for i in ordem)
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
        "eleitos_provaveis": [],
        "dupla_mais_provavel": [],
        "p_dupla_mais_provavel": None,
        "duplas": [],
        "incerteza": "alta",
        "notas": [],
    }
    if prep["media"] is None or resumo is None:
        base["notas"].append(
            "Sem pesquisa estimulada no acervo: o estado não tem nome entre os "
            "eleitos prováveis; nas somas nacionais as duas vagas saem da "
            "distribuição neutra declarada em parametros.estados_sem_pesquisa."
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
    linhas = []
    for i, c in enumerate(cands):
        linhas.append(
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
        )
    base["media"] = sorted(linhas, key=lambda x: -x["validos"])
    probs = []
    for i, c in enumerate(cands):
        probs.append(
            {
                "nome": c["nome"],
                "nome_urna": c["nome_urna"],
                "partido": c["partido"],
                "campo": c["campo"],
                "sq_candidato": c["sq_candidato"],
                "foto": c["foto"],
                "p_eleito": resumo["p_eleito"][i],
                "p_primeiro": resumo["p_primeiro"][i],
                "ic90_validos": resumo["ic90"][i],
                "validos_mediana": resumo["mediana"][i],
                "validos_central": c["validos"],
            }
        )
    base["probabilidades"] = sorted(probs, key=lambda x: (-x["p_eleito"], x["nome"]))
    modal = resumo["duplas"][0]
    p_por_nome = {p["nome"]: p["p_eleito"] for p in probs}
    dupla = sorted(modal["nomes"], key=lambda n: -p_por_nome[n])
    base["dupla_mais_provavel"] = dupla
    base["eleitos_provaveis"] = dupla
    base["p_dupla_mais_provavel"] = modal["p"]
    base["duplas"] = [{"nomes": d["nomes"], "p": d["p"]} for d in resumo["duplas"]]
    base["incerteza"] = _incerteza(prep["cobertura"], modal["p"])
    segunda = resumo["duplas"][1]["p"] if len(resumo["duplas"]) > 1 else 0.0
    base["p_segunda_dupla"] = segunda
    base["dupla_empatada"] = modal["p"] - segunda < EMPATE_DUPLA
    base["soma_p_eleito"] = sum(resumo["p_eleito"])
    top2 = [p["nome"] for p in base["probabilidades"][:2]]
    notas = base["notas"]
    if sorted(top2) != sorted(dupla):
        notas.append(
            "Os dois nomes de maior probabilidade individual não formam a dupla "
            f"mais frequente nos sorteios ({top2[0]} e {top2[1]})."
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
        for r in o["retiradas"]:
            notas.append(
                f"{o['arquivo']}: {r['nome_pesquisa']} retirou a candidatura em "
                f"{r['data_retirada']}; o voto medido passou a indeciso."
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
    return base


def _texto_justificativa(erro: M.Erro, detalhe: dict, cal: dict | None) -> str:
    if erro.fonte != "wikipedia_2022" or not cal:
        return (
            "Hipótese declarada: desvio de "
            f"{br(C.HIPOTESE['sd_pp_30'])} pontos dos válidos para candidatura em "
            "30%. Erro de pesquisa de Senado no Brasil é maior que o presidencial: "
            "muitas candidaturas, voto útil tardio e amostras estaduais menores."
        )
    est = cal["estatisticas"]["casas_principais"]
    comp = est["candidaturas_entre_20_e_40_pct"]
    cob = cal["cobertura"]
    return (
        f"Calibrado com {cob['n_pesquisas_casas_principais']} pesquisas finais de "
        f"Datafolha, Ipec e Quaest em {cob['n_estados_casas_principais']} estados "
        "na eleição de Senado de 2022 contra a urna (TSE). Entre candidaturas que "
        f"fizeram de 20% a 40% dos válidos, a raiz do erro quadrático médio foi "
        f"{br(comp['rmse'])} pontos (n = {comp['n']}), com a amostragem dentro. "
        "A escala no log das frações é a variância não amostral das "
        "candidaturas com ao menos 10% dos válidos, descontadas a parte amostral "
        "(n / 1,5) e a deriva medida entre ondas seguidas da mesma casa. O efeito "
        "de campo comum aos estados entra simétrico, nas duas direções: o viés "
        "de 2022 não desloca a central."
    )


def _calibracao_resumo(cal: dict | None, erro: M.Erro) -> dict:
    if not cal or erro.fonte != "wikipedia_2022":
        return {"fonte": "hipotese", "estados": [], "url": None}
    est = cal["estatisticas"]["casas_principais"]
    return {
        "fonte": "wikipedia_2022",
        "estados": cal["cobertura"]["estados_casas_principais"],
        "n_estados": cal["cobertura"]["n_estados_casas_principais"],
        "n_pesquisas": cal["cobertura"]["n_pesquisas_casas_principais"],
        "erro_medio_abs_pp": est["por_candidatura"]["erro_medio_absoluto"],
        "rmse_pp": est["por_candidatura"]["rmse"],
        "erro_medio_abs_20_40_pp": est["candidaturas_entre_20_e_40_pct"][
            "erro_medio_absoluto"
        ],
        "rmse_20_40_pp": est["candidaturas_entre_20_e_40_pct"]["rmse"],
        "erro_medio_abs_diferenca_2_3_pp": est["diferenca_2o_3o"][
            "erro_medio_absoluto"
        ],
        "desvio_diferenca_2_3_pp": est["diferenca_2o_3o"]["desvio_padrao"],
        "vies_medio_por_campo_pp": {
            k: v.get("media") for k, v in est["por_campo"].items()
        },
        "url": REPO + "analysis/senado_2026/calibracao_2022.json",
        "urls_wikipedia": [f["url"] for f in cal.get("fontes_wikipedia", [])],
    }


def _comparar(central: dict, alt: dict, preps: list[dict]) -> list[dict]:
    mudam = []
    for prep in preps:
        uf = prep["uf"]
        if uf not in central["resumos"] or uf not in alt["resumos"]:
            continue
        a = central["resumos"][uf]["duplas"][0]
        b = alt["resumos"][uf]["duplas"][0]
        if sorted(a["nomes"]) != sorted(b["nomes"]):
            mudam.append(
                {
                    "uf": uf,
                    "central": a["nomes"],
                    "p_central": a["p"],
                    "sensibilidade": b["nomes"],
                    "p_sensibilidade": b["p"],
                }
            )
    return mudam


def _resumo_comp(comp: dict) -> dict:
    return {
        "por_campo": {k: v["esperado"] for k, v in comp["por_campo"].items()},
        "por_grupo": {
            k: {"esperado": v["esperado"], "ic90": v["ic90"]}
            for k, v in comp["por_grupo"].items()
        },
        "p_maioria_direita_mais_centro_direita": comp[
            "p_maioria_direita_mais_centro_direita"
        ],
        "p_41_direita_centro_direita_centro": comp[
            "p_41_direita_centro_direita_centro"
        ],
        "p_41_esquerda_centro_esquerda": comp["p_41_esquerda_centro_esquerda"],
    }


def _pct(x: float) -> str:
    return f"{br(100 * x, 0)}%"


def _achado_contrario(comp: dict, sens: list[dict], estados: dict) -> str:
    """O achado que mais pesa contra a leitura central, gerado dos números."""
    g = comp["por_grupo"]
    if g["direita"]["esperado"] >= g["esquerda"]["esperado"]:
        nome, chaves = "direita e centro-direita", (
            "p_maioria_direita_mais_centro_direita",
            "p_49_direita_centro_direita",
            "p_54_bloco_oposicao",
        )
        bloco = g["direita"]
    else:
        nome, chaves = "esquerda e centro-esquerda", (
            "p_41_esquerda_centro_esquerda",
            "p_49_esquerda_centro_esquerda",
            "p_54_esquerda_centro_esquerda",
        )
        bloco = g["esquerda"]
    p41, p49, p54 = (comp[k] for k in chaves)
    partes = [
        f"A leitura central põe o bloco de {nome} com {br(bloco['esperado'])} "
        f"cadeiras esperadas e maioria (41) em {_pct(p41)} dos sorteios, mas três "
        f"quintos (49) só em {_pct(p49)} e dois terços (54) em {_pct(p54)}."
    ]
    dobrado = next((s for s in sens if s["chave"] == "erro_dobrado"), None)
    if dobrado:
        chave_maioria = (
            "p_maioria_direita_mais_centro_direita"
            if nome.startswith("direita")
            else "p_41_esquerda_centro_esquerda"
        )
        if chave_maioria in dobrado:
            partes.append(
                f"Com o erro dobrado, a maioria cai para {_pct(dobrado[chave_maioria])}"
                f" e a dupla mais provável muda em {len(dobrado['duplas_que_mudam'])} "
                "estados."
            )
    frageis = sorted(
        uf
        for uf, e in estados.items()
        if e["p_dupla_mais_provavel"] is not None and e["p_dupla_mais_provavel"] < 0.3
    )
    if frageis:
        partes.append(
            f"Em {len(frageis)} estados a dupla mais provável aparece em menos de 30% "
            f"dos sorteios ({', '.join(frageis)})."
        )
    return " ".join(partes)


def prever(
    ondas: list[dict],
    tse: B.Tse,
    senadores_2022: list[dict] | None,
    eleitorado: dict,
    cal: dict | None,
    *,
    simulacoes: int = M.SIMULACOES,
    semente: int = M.SEMENTE,
    mistura_uniforme: float = M.MISTURA_UNIFORME,
    deff: float = M.DEFF,
    sensibilidades: bool = True,
    agora: datetime | None = None,
) -> dict:
    erro, detalhe = M.erro_calibrado(cal)
    preps = [M.preparar_estado(uf, ondas, tse) for uf in B.UFS]
    kw = {"simulacoes": simulacoes, "semente": semente, "deff": deff}
    central = M.rodar(preps, erro, mistura_uniforme=mistura_uniforme, **kw)
    fixos = S.continuam(senadores_2022)
    comp = S.composicao(
        central["campos_novos"], central["partidos_novos"], central["partidos"], fixos
    )
    estados = {
        p["uf"]: estado_saida(p, central["resumos"].get(p["uf"]), eleitorado)
        for p in preps
    }

    sens = []
    if sensibilidades:
        for chave, rotulo, descricao, e, mist in (
            (
                "erro_dobrado",
                "Erro dobrado",
                "Desvios do erro não amostral e da deriva multiplicados por 2.",
                erro.escalado(2.0),
                mistura_uniforme,
            ),
            (
                "indecisos_uniformes",
                "Indecisos 100% uniformes",
                "Todo sorteio reparte os indecisos igualmente entre os nomes com ao "
                "menos 1 ponto.",
                erro,
                1.0,
            ),
        ):
            alt = M.rodar(preps, e, mistura_uniforme=mist, **kw)
            comp_alt = S.composicao(
                alt["campos_novos"], alt["partidos_novos"], alt["partidos"], fixos
            )
            sens.append(
                {
                    "chave": chave,
                    "rotulo": rotulo,
                    "descricao": descricao,
                    "duplas_que_mudam": _comparar(central, alt, preps),
                    **_resumo_comp(comp_alt),
                }
            )

    usadas = [o for p in preps for o in p["usadas"]]
    ids_usadas = {id(o) for o in usadas}
    discordam = []
    for p in preps:
        if p["media"] is None or len(p["usadas"]) < 2:
            continue
        lideres = _dupla_lider_por_casa(p)
        if len({tuple(v) for v in lideres.values()}) > 1:
            discordam.append({"uf": p["uf"], "duplas_por_pesquisa": lideres})
    retiradas = []
    for o in ondas:
        for r in o["retiradas"]:
            data_r = r["data_retirada"]
            ini, fim = _iso(o["campo_inicio"]), _iso(o["campo_fim"])
            relacao = (
                "posterior"
                if ini and ini > data_r
                else "durante" if fim and fim >= data_r else "anterior"
            )
            retiradas.append(
                {
                    "arquivo": o["arquivo"],
                    "uf": o["uf"],
                    "nome_pesquisa": r["nome_pesquisa"],
                    "valor_pp": r["valor_pp"],
                    "data_retirada": data_r,
                    "campo": _campo_txt(o),
                    "relacao_com_o_campo": relacao,
                    "usada_na_previsao": id(o) in ids_usadas,
                    "fonte": r["fonte"],
                }
            )
    sem_tse = sorted(
        {
            (p["uf"], c["nome_pesquisa"])
            for p in preps
            for c in p["candidatos"]
            if not c["sq_candidato"]
        }
    )
    aliases = [
        {"uf": p["uf"], "nome": c["nome"], "variantes": c["aliases"]}
        for p in preps
        for c in p["candidatos"]
        if len(c["aliases"]) > 1
    ]
    somas = [e["soma_p_eleito"] for e in estados.values() if "soma_p_eleito" in e]

    escala = M.sd_pp(erro)
    validacao = {
        "recomposicao": [B.recomposicao(o) for o in ondas],
        "recomposicao_maior_diferenca_pp": max(
            (
                abs(r["diferenca"])
                for r in (B.recomposicao(o) for o in ondas)
                if r["diferenca"] is not None
            ),
            default=None,
        ),
        "fechamento_maior_desvio_pp_um_voto": max(
            (
                abs(B.recomposicao(o)["fechamento_em_100"])
                for o in ondas
                if o["votos_por_eleitor"] == 1 and B.motivo_descarte(o) is None
            ),
            default=None,
        ),
        "casas_discordam_dupla_lider": discordam,
        "soma_p_eleito_maior_desvio": max((abs(s - 2) for s in somas), default=None),
        "composicao_fecha_em_81": comp["fecha_em_81_em_todo_sorteio"],
        "sem_candidatura_tse": [{"uf": u, "nome_pesquisa": n} for u, n in sem_tse],
        "apelidos_tse": tse.via_apelido,
        "ambiguidades_tse": tse.ambiguidades,
        "aliases": aliases,
        "retiradas": retiradas,
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
        "calibracao_2022": _calibracao_resumo(cal, erro),
        "sensibilidades": sens,
        "achado_contrario": _achado_contrario(comp, sens, estados),
    }
    agora = agora or datetime.now(timezone.utc)
    parametros = {
        "meia_vida_dias": B.MEIA_VIDA_DIAS,
        "janela_campo_minimo": B.CORTE_CAMPO.isoformat(),
        "inferencia_campo_divulgacao_desde": B.CORTE_INFERENCIA.isoformat(),
        "simulacoes": simulacoes,
        "semente": semente,
        "deff": deff,
        "justificativa_deff": (
            "Kish com cerca de 6 entrevistas por setor censitário e correlação "
            "intraclasse perto de 0,1: deff = 1 + 5 x 0,1 = 1,5. Hipótese declarada."
        ),
        "n_ausente": min(
            (o["n_usado"] for o in ondas if o["n_assumido"]), default=None
        ),
        "justificativa_n_ausente": (
            "Onda sem n publicado usa o menor n declarado no acervo, para não "
            "atribuir precisão desconhecida."
        ),
        "mistura_indecisos": {
            "proporcional": 1 - mistura_uniforme,
            "uniforme": mistura_uniforme,
        },
        "limiar_uniforme_pp": B.LIMIAR_UNIFORME_PP,
        "indecisos_regra": (
            "Central: indecisos repartidos na proporção do voto declarado. "
            "Uniforme: indecisos repartidos em partes iguais entre os nomes com ao "
            "menos 1 ponto. Branco e nulo nunca viram voto válido. Em cada sorteio "
            "um dos dois cenários é escolhido com as probabilidades acima."
        ),
        "votos_por_eleitor_regra": (
            "Quando a pergunta pede dois nomes (votos_por_eleitor = 2), todos os "
            "valores são divididos por 2 antes de combinar: a média trabalha com a "
            "fração de menções. O n da amostragem continua o de entrevistados."
        ),
        "erro": {
            **M.descrever_erro(erro),
            **detalhe,
            "fracao_estadual_do_resto": M.FRACAO_ESTADUAL,
            "corrida_referencia_pct": list(M.CORRIDA_REFERENCIA),
        },
        "escala_erro_pp": escala,
        "escala_erro_pp_com_deriva_7_dias": M.sd_pp(erro, dias=7),
        "justificativa_erro": _texto_justificativa(erro, detalhe, cal),
        "decomposicao_erro": (
            "Logística-normal: ao log da fração válida de cada candidatura somam-se "
            "um choque do campo comum a todos os estados (variância "
            f"{br(erro.var_nacional, 4)}), um choque do campo no estado "
            f"({br(erro.var_estadual, 4)}), um choque próprio ({br(erro.var_idio, 4)}) e "
            f"a deriva de {br(erro.var_deriva_dia, 5)} por dia até 04/10; depois "
            "renormaliza. A divisão entre campo no estado e candidatura não é "
            "identificada em 2022 e segue a fração declarada."
        ),
        "incerteza_regra": (
            "alta quando a cobertura não é recente ou a dupla mais provável sai em "
            f"menos de {INCERTEZA['media']:.0%} dos sorteios; média de "
            f"{INCERTEZA['media']:.0%} a {INCERTEZA['baixa']:.0%}; baixa acima."
        ),
        "estados_sem_pesquisa": {
            "ufs": [p["uf"] for p in preps if p["cobertura"] == "sem_pesquisa"],
            "distribuicao_campos": central["distribuicao_sem_pesquisa"],
            "regra": (
                "Hipótese neutra: cada vaga de estado sem pesquisa é sorteada da "
                "distribuição de campos das vagas sorteadas nos estados com "
                "cobertura recente."
            ),
        },
        "campo_classificacao": (
            "Campo é classificação editorial da casa (PARTIDO_CAMPO em "
            "scripts/voto_util_base.py): tucano é centro-esquerda; PSD, MDB e "
            "Avante, centro; União, PP, Podemos, PRD, Agir e Mobiliza, "
            "centro-direita; PL, Novo, Republicanos, PRTB, DC, Democrata e Missão, "
            "direita. Partido vem do TSE quando o nome casa, senão da pesquisa."
        ),
        "senado_2027_regra": (
            "Os 27 de 2022 são os eleitos na urna, não os titulares atuais: "
            "suplência, licença e migração partidária ficam fora do modelo. A única "
            "exceção é partido extinto (PSC, incorporado ao Podemos em 2023)."
        ),
        "o_que_nao_faz": (
            "Não prevê votos; não modela coligação, desistência nem transferência "
            "entre candidaturas; não usa o resultado de 2022 como prior de nome."
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
        }
        for o in sorted(usadas, key=lambda o: (o["uf"], o["arquivo"]))
    ]
    return {
        "gerado_em": agora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_referencia": B.DATA_REFERENCIA.isoformat(),
        "eleicao": B.ELEICAO.isoformat(),
        "parametros": parametros,
        "estados": estados,
        "senado_2027": {"continuam": fixos, **comp},
        "validacao": validacao,
        "fontes": fontes,
    }
