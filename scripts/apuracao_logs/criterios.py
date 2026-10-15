"""Diagnósticos operacionais, sem usar candidato ou resultado do voto.

Limiares exploratórios declarados. Não são testes confirmatórios, probabilidade de
fraude ou infração. Sinais correlacionados não somam pontos à classificação antiga.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MIN_PARES = 30
DESVIOS_ROBUSTOS = 4


def criterio(nome, grupo, regra, limite, conferir):
    return {
        "nome": nome,
        "grupo": grupo,
        "regra": regra,
        "limite": limite,
        "conferir": conferir,
    }


CRITERIOS = {
    "tempo_rapido": criterio(
        "Votação mais rápida que a referência",
        "tempo",
        "Mediana abaixo da referência menos 4 escalas robustas e menor que metade dela; ≥30 ciclos completos do mesmo número de cargos.",
        "Rapidez não identifica voto automatizado. Familiaridade, idade e quantidade de cargos afetam o tempo.",
        "Conferir os ciclos completos, o número de cargos e a ata, sem associar horários a pessoas ou opções de voto.",
    ),
    "tempo_lento": criterio(
        "Votação mais lenta que a referência",
        "tempo",
        "Mediana acima da referência mais 4 escalas robustas e maior que 1,5 vez a referência; ≥30 ciclos completos.",
        "Dificuldade de uso, acessibilidade e perfil etário podem explicar a diferença.",
        "Conferir apoio de acessibilidade, orientação da mesa, teclado e ocorrências da ata.",
    ),
    "identificacao_lenta": criterio(
        "Habilitação mais lenta que a referência",
        "tempo",
        "Mediana entre identificador digitado e habilitação acima da referência mais 4 escalas robustas, com excesso ≥20 segundos e ao menos 30 etapas observadas.",
        "O log mede a etapa eletrônica após a digitação. Não mede o tempo total na fila.",
        "Conferir dificuldades de leitura das digitais, cadastro e atendimento documentado na ata.",
    ),
    "biografica_alta": criterio(
        "Habilitação biográfica acima da referência",
        "biometria",
        "Biográficas / (biométricas + biográficas) acima da referência mais 4 escalas robustas e ≥10 pontos percentuais acima; denominador ≥50.",
        "A comparação na mesma zona e modelo não controla idade, ocupação ou qualidade do cadastro. Procedimento previsto não é voto irregular.",
        "Conferir tentativas de reconhecimento, habilitações biográficas e documentação da mesa.",
    ),
    "sem_biometria_alta": criterio(
        "Eleitores sem biometria acima da referência",
        "biometria",
        "Sem biometria / comparecimento acima da referência mais 4 escalas robustas e ≥10 pontos percentuais acima; comparecimento ≥50.",
        "Diferenças de cadastramento biométrico são uma explicação possível. Não confundir com falha de reconhecimento.",
        "Comparar a cobertura do cadastro da seção e do local antes de atribuir a taxa à operação da urna.",
    ),
    "suspensoes": criterio(
        "Suspensões repetidas de votação",
        "operacao",
        "Ao menos 3 suspensões e taxa ≥1% dos computados mais suspensões sem voto.",
        "Suspensão pode ocorrer por abandono ou dificuldade. Voto parcial e suspensão sem voto são eventos diferentes.",
        "Conferir motivo na ata, votos parciais e nulos por suspensão, preservando o sigilo.",
    ),
    "reinicios": criterio(
        "Aplicação reiniciada durante a votação",
        "operacao",
        "Ao menos uma nova partida do VOTA depois de um voto computado e antes do encerramento observado.",
        "Reinício pode ser recuperação normal. O evento não demonstra perda ou alteração de votos.",
        "Conferir hora, motivo, continuidade das contagens e eventual troca de urna na ata.",
    ),
    "bateria": criterio(
        "Operação com bateria registrada",
        "operacao",
        "Ao menos uma mensagem explícita de operação com bateria interna no dia da votação.",
        "A bateria é um recurso de continuidade. O registro não mede duração da falta de energia nem prova defeito.",
        "Conferir fornecimento de energia e eventuais interrupções de atendimento na ata.",
    ),
    "erro_tecnico": criterio(
        "Erro técnico registrado no dia",
        "operacao",
        "Ao menos um evento classificado ERRO ou FATAL pelo log no dia da votação.",
        "ALERTA não entra aqui: inclui erro de digitação normal. Gravidade e recuperação exigem leitura do evento original.",
        "Conferir mensagem, subsistema, recuperação e ata; erro registrado não é necessariamente erro sem solução.",
    ),
    "assinatura": criterio(
        "Falha declarada de verificação de assinatura",
        "integridade",
        "Mensagem de assinatura com [FALHA], [ERRO] ou indicação de inválida.",
        "É o que o software registrou. Esta leitura não é validação criptográfica independente do pacote.",
        "Preservar o original e solicitar conferência de assinaturas, mídias, certificados e providências à Justiça Eleitoral.",
    ),
    "relogio": criterio(
        "Sequência temporal inconsistente ou relógio ajustado",
        "qualidade",
        "Horário retrocede dentro do mesmo arquivo e urna, ou há mensagem explícita de ajuste, alteração ou erro do relógio.",
        "Carimbos fora de ordem podem decorrer de gravação assíncrona ou relógio. Por cautela, invalidam os tempos da seção nesta análise, mesmo se o recuo for de apenas um segundo.",
        "Conferir ajuste do relógio, continuidade de arquivos e ata antes de interpretar qualquer duração.",
    ),
    "ciclos_incompletos": criterio(
        "Ciclo de votação não reconstruído",
        "qualidade",
        "Voto computado sem habilitação reconhecida, habilitação sobreposta, ciclo aberto ou interrompido pelo reinício.",
        "Pode ser fragmento ausente, contingência ou limitação do leitor. Não significa eleitor sem identificação.",
        "Conferir todos os membros do pacote, logs da urna substituída e mensagens não reconhecidas pelo leitor.",
    ),
    "contagem_divergente": criterio(
        "Contagem do log não reconciliada com o BU",
        "qualidade",
        "Quantidade de eventos de voto computado ou ciclos reconstruídos difere do comparecimento no BU do mesmo hash.",
        "Discrepância documental ou de extração pede reconciliação. Não demonstra alteração do resultado.",
        "Conferir identidade, versão, contingência, todos os arquivos do log e BU correspondente.",
    ),
    "biometria_divergente": criterio(
        "Categorias de habilitação não reconciliadas",
        "qualidade",
        "Categorias dos ciclos computados não reproduzem as três contagens do BU, ou há tipo não reconhecido.",
        "Pode revelar uma mensagem ainda não coberta pelo leitor. A seção fica fora da comparação de biometria.",
        "Conferir vocabulário do modelo da urna, ciclos suspensos e totais do BU antes de comparar taxas.",
    ),
    "zeresima_ausente": criterio(
        "Zerésima anterior não localizada no pacote",
        "qualidade",
        "Há voto computado, mas nenhum término da geração da zerésima anterior ao primeiro cômputo foi localizado.",
        "Ausência no pacote lido não prova ausência da emissão ou impressão. Pode faltar arquivo de origem.",
        "Conferir zerésima impressa, ata, log anterior e eventuais procedimentos de contingência.",
    ),
    "intervalo_longo": criterio(
        "Intervalo de 30 minutos entre cômputos",
        "tempo",
        "Maior intervalo entre dois votos computados consecutivos ≥1.800 segundos, com relógio sem recuo ou ajuste identificado.",
        "Intervalo inclui ociosidade, identificação e votação. Não mede fila nem prova paralisação.",
        "Conferir movimento do local e ocorrências da ata no intervalo, sem inferir quem votou.",
    ),
    "texto_malformado": criterio(
        "Estrutura ou texto crítico malformado",
        "qualidade",
        "Linha com estrutura inválida ou mensagem crítica com uma ou duas substituições de caracteres, mantendo comprimento e prefixo reconhecíveis de habilitação, cômputo ou espera de identificador.",
        "Sinal de qualidade do registro ou vocabulário não reconhecido. O leitor não corrige o texto por aproximação nem deduz alteração de votos ou causa física.",
        "Comparar os bytes originais e os fragmentos do pacote; solicitar conferência da cadeia de integridade e dos registros de contingência.",
    ),
    "identidade_nao_confirmada": criterio(
        "Identidade ou fase de parte dos registros não confirmada",
        "qualidade",
        "Há identificadores de urna com fase incompatível, identidade de seção divergente ou metadados insuficientes. Seus eventos foram excluídos das contagens.",
        "Pode ser fragmento de outra seção, contingência, metadado ausente ou texto malformado. Eventos excluídos não são atribuídos à seção consultada.",
        "Conferir município, zona, seção, fase e número interno nos fragmentos originais e nos registros de contingência, sem misturar contagens de seções diferentes.",
    ),
}


def campos(r: dict) -> dict:
    c, bu = r["contagens"], r["bu"]
    cargos = r["tempo_por_cargos"]
    principal = max(cargos, key=lambda k: cargos[k]["n"]) if cargos else "0"
    tempo = cargos.get(principal, {})
    comp = bu.get("comparecimento") or 0
    bio = (bu.get("hab_biometria") or 0) + (bu.get("hab_ano_nascimento") or 0)
    modelos = r["modelos"]
    modelo_bu = bu.get("modelo_urna")
    modelo = modelos[0] if len(modelos) == 1 else modelo_bu
    modelo_comparavel = (
        bool(modelo)
        and len(modelos) <= 1
        and not (modelos and modelo_bu and modelo_bu not in modelos)
    )
    motivos_tempo = list(r["motivos_tempo"])
    if not modelo_comparavel:
        motivos_tempo.append("modelo_indeterminado_misto_ou_divergente")
    if tempo.get("n", 0) < 30 and "menos_de_30_ciclos" not in motivos_tempo:
        motivos_tempo.append("menos_de_30_ciclos_mesmos_cargos")
    return {
        "modelo": " + ".join(modelos) if len(modelos) > 1 else modelo or "desconhecido",
        "modelo_comparavel": modelo_comparavel,
        "cargos": principal,
        "n_tempo": tempo.get("n", 0),
        "voto_mediana": tempo.get("p50"),
        "voto_media": tempo.get("media"),
        "voto_p90": tempo.get("p90"),
        "habilitacao_mediana": r["tempo_habilitacao"]["p50"],
        "n_habilitacao": r["tempo_habilitacao"]["n"],
        "biografica_pct": (
            100 * bu["hab_ano_nascimento"] / bio
            if bio and bu.get("hab_ano_nascimento") is not None
            else None
        ),
        "sem_biometria_pct": (
            100 * bu["comp_sem_biometria"] / comp
            if comp and bu.get("comp_sem_biometria") is not None
            else None
        ),
        "den_bio": bio,
        "biometricas_bu": bu.get("hab_biometria"),
        "biograficas_bu": bu.get("hab_ano_nascimento"),
        "sem_biometria_bu": bu.get("comp_sem_biometria"),
        "habilitacoes_log": r["tipos_habilitacao_computados"],
        "comparecimento": comp,
        "elegivel_tempo": not motivos_tempo,
        "elegivel_bio": bool(r["biometria_confere"] and r["contagem_confere"]),
        "biometria_status": (
            "ausente_bu"
            if r["biometria_confere"] is None
            else "confere" if r["biometria_confere"] else "divergente"
        ),
        "suspensoes": c.get("suspensoes", 0),
        "reinicios": c.get("reinicios_durante_votacao", 0),
        "erros": c.get("erros", 0),
        "intervalo_max": r["intervalo_computados"]["max"],
        "computados": c.get("computados", 0),
        "ciclos_reconstruidos": r["ciclos"],
        "motivos_tempo": motivos_tempo,
        "erros_categoria": r["erros_categoria"],
        "erros_na_janela_votacao": c.get("erros_na_janela_votacao"),
        "assinatura_sucesso_posterior": c.get(
            "falhas_assinatura_com_sucesso_posterior", 0
        ),
        "assinatura_sem_sucesso_localizado": c.get(
            "falhas_assinatura_sem_sucesso_localizado", 0
        ),
        "assinatura_ordem_incerta": c.get("falhas_assinatura_ordem_incerta", 0),
        "recuo_max_s": c.get("recuo_max_s", 0),
        "mensagens_criticas_alteradas": c.get("mensagens_criticas_alteradas", 0),
        "linhas_invalidas": c.get("linhas_invalidas", 0),
        "identificadores_excluidos": c.get("urnas_excluidas", 0),
    }


def referencias(
    df: pd.DataFrame, coluna: str, grupos: list[str], elegivel: pd.Series, piso: float
) -> pd.DataFrame:
    t = df.assign(_x=pd.to_numeric(df[coluna], errors="coerce").where(elegivel))
    g = t.groupby(grupos)["_x"]
    med = g.transform("median")
    n = g.transform("count")
    desvios = (t["_x"] - med).abs()
    mad = t.assign(_d=desvios).groupby(grupos)["_d"].transform("median")
    escala = (1.4826 * mad).clip(lower=piso)
    return pd.DataFrame({"ref": med.where(n >= MIN_PARES), "escala": escala, "n": n})


def avaliar(
    df: pd.DataFrame, resumos: list[dict], desvios: float = DESVIOS_ROBUSTOS
) -> tuple[list[list[str]], dict]:
    flags = {k: np.zeros(len(df), dtype=bool) for k in CRITERIOS}
    refs = {}
    # Exterior fica em seu próprio estrato; tempos também separam quantidade de cargos.
    for campo in ("voto_mediana", "habilitacao_mediana"):
        elegivel = df.elegivel_tempo & (
            (df.n_habilitacao >= 30) if campo == "habilitacao_mediana" else True
        )
        refs[campo] = referencias(df, campo, ["uf", "modelo", "cargos"], elegivel, 3)
    for campo in ("biografica_pct", "sem_biometria_pct"):
        den = df.den_bio if campo == "biografica_pct" else df.comparecimento
        refs[campo] = referencias(
            df,
            campo,
            ["uf", "mun", "zona", "modelo"],
            df.elegivel_bio & df.modelo_comparavel & (den >= 50),
            1,
        )
    v = refs["voto_mediana"]
    flags["tempo_rapido"] = (
        df.elegivel_tempo
        & (df.voto_mediana < v.ref - desvios * v.escala)
        & (df.voto_mediana < 0.5 * v.ref)
    ).to_numpy()
    flags["tempo_lento"] = (
        df.elegivel_tempo
        & (df.voto_mediana > v.ref + desvios * v.escala)
        & (df.voto_mediana > 1.5 * v.ref)
    ).to_numpy()
    h = refs["habilitacao_mediana"]
    flags["identificacao_lenta"] = (
        df.elegivel_tempo
        & (df.n_habilitacao >= 30)
        & (df.habilitacao_mediana > h.ref + desvios * h.escala)
        & (df.habilitacao_mediana >= h.ref + 20)
    ).to_numpy()
    for campo, cod, den in (
        ("biografica_pct", "biografica_alta", df.den_bio),
        ("sem_biometria_pct", "sem_biometria_alta", df.comparecimento),
    ):
        b = refs[campo]
        flags[cod] = (
            df.elegivel_bio
            & df.modelo_comparavel
            & (den >= 50)
            & (df[campo] > b.ref + desvios * b.escala)
            & (df[campo] >= b.ref + 10)
        ).to_numpy()
    for i, r in enumerate(resumos):
        c = r["contagens"]
        n = c.get("computados", 0)
        flags["suspensoes"][i] = c.get("suspensoes", 0) >= max(
            3, 0.01 * (n + c.get("suspensoes_sem_voto", 0))
        )
        for cod, campo in (
            ("reinicios", "reinicios_durante_votacao"),
            ("bateria", "eventos_bateria"),
            ("erro_tecnico", "erros"),
            ("assinatura", "falhas_assinatura_declaradas"),
        ):
            flags[cod][i] = c.get(campo, 0) > 0
        flags["relogio"][i] = not r["tempos_validos"]
        flags["ciclos_incompletos"][i] = any(
            c.get(k, 0)
            for k in (
                "computados_sem_habilitacao",
                "habilitacoes_sobrepostas",
                "ciclos_abertos",
                "ciclos_interrompidos",
                "ciclos_sem_computo",
            )
        )
        flags["contagem_divergente"][i] = not r["contagem_confere"]
        flags["biometria_divergente"][i] = r["biometria_confere"] is False
        flags["zeresima_ausente"][i] = n > 0 and not r["zeresima_antes"]
        flags["intervalo_longo"][i] = (
            r["tempos_validos"] and (r["intervalo_computados"]["max"] or 0) >= 1800
        )
        flags["texto_malformado"][i] = bool(
            c.get("linhas_invalidas", 0) or c.get("mensagens_criticas_alteradas", 0)
        )
        flags["identidade_nao_confirmada"][i] = c.get("urnas_excluidas", 0) > 0
    return [[k for k in CRITERIOS if flags[k][i]] for i in range(len(df))], refs
