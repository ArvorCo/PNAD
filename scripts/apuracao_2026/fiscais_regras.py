"""Texto declarado de cada critério do capítulo 13 (nome, regra, limiar, o que conferir).

Separado do motor para que a regra publicada e a regra aplicada fiquem lado a lado:
os limiares vêm das constantes de `fiscais_criterios`, nunca digitados duas vezes.
"""

from __future__ import annotations

from typing import Any

from . import fiscais_criterios as fc

ROTULOS = {
    "atipico": "Atipicidade estatística não é irregularidade.",
    "prioridade": "A lista é de prioridade de fiscalização, não de acusação.",
    "resolve": (
        "O que resolve cada item é a ata da mesa, o log da urna e a presença do fiscal."
    ),
}
AVISO = " ".join(ROTULOS.values())


def _n(x: float) -> str:
    """Número curto em pt-BR (vírgula decimal, sem zeros inúteis)."""
    if float(x).is_integer():
        return f"{int(x):,}".replace(",", ".")
    return f"{x:.1f}".replace(".", ",")


CRITERIOS: list[dict[str, Any]] = [
    {
        "id": "a",
        "nome": "90% ou mais com excesso sobre a zona",
        "mede": "seção quase unânime para um candidato, muito acima das vizinhas da zona",
        "regra": (
            f"Lula ou Flávio com {_n(fc.A_PCT)}% ou mais dos válidos, {fc.A_VOTANTES} "
            f"votantes ou mais e {_n(fc.A_EXCESSO)} pontos ou mais acima do resto da zona "
            "(a zona sem a própria seção). Seção casada com 2022 em que o mesmo campo já "
            f"tinha {_n(fc.A_PCT)}% ou mais (1º ou 2º turno) fica em nível baixa"
        ),
        "limiar": (
            f"{_n(fc.A_PCT)}% dos válidos; {fc.A_VOTANTES} votantes; "
            f"{_n(fc.A_EXCESSO)} pp sobre a zona"
        ),
        "explicacao_comum": (
            "aldeia, comunidade fechada ou enclave que já votava assim em 2022"
        ),
        "o_que_conferir": (
            "identificação dos eleitores (biometria ou documento) e boletim impresso "
            "afixado contra o publicado"
        ),
        "fonte": "boletins de urna por seção (secoes_2026.sqlite) e votação por seção de 2022",
    },
    {
        "id": "b",
        "nome": "zero voto num dos dois",
        "mede": "seção sem nenhum voto para Lula ou para Flávio",
        "regra": f"Lula ou Flávio com zero voto e {fc.B_VOTANTES} votantes ou mais",
        "limiar": f"0 voto; {fc.B_VOTANTES} votantes",
        "explicacao_comum": "aldeia ou comunidade fechada que vota em bloco",
        "o_que_conferir": (
            "boletim impresso afixado na porta contra o publicado e número de votantes "
            "na ata"
        ),
        "fonte": "boletins de urna por seção",
    },
    {
        "id": "c",
        "nome": "comparecimento total",
        "mede": "seção em que todos os aptos votaram (abstenção zero)",
        "regra": (
            f"comparecimento igual ou maior que os aptos e {fc.C_APTOS} aptos ou mais"
        ),
        "limiar": f"abstenção 0; {fc.C_APTOS} aptos",
        "explicacao_comum": (
            "seção de unidade prisional ou de trânsito, com cadastro pequeno e fechado"
        ),
        "o_que_conferir": (
            "caderno de votação (quem assinou), habilitações por ano de nascimento no log "
            "da urna e ata"
        ),
        "fonte": "boletins de urna por seção (aptos da eleição federal e comparecimento)",
    },
    {
        "id": "d",
        "nome": "encerramento tardio com Lula acima da zona",
        "mede": "urna que recebeu o último voto tarde e votou em Lula bem acima das vizinhas",
        "regra": (
            f"último voto às {fc.D_HORA[11:16]} de Brasília ou depois e Lula "
            f"{_n(fc.D_EXCESSO)} pontos ou mais acima do resto da zona; exterior fora"
        ),
        "limiar": f"{fc.D_HORA[11:16]} de Brasília; {_n(fc.D_EXCESSO)} pp sobre a zona",
        "explicacao_comum": (
            "fila longa em seção grande e identificação biométrica lenta (o tamanho do "
            "efeito típico dentro da zona sai de fechamento.json)"
        ),
        "o_que_conferir": (
            "senhas entregues às 17h, quantos votaram depois e habilitações por ano de "
            "nascimento no fim do dia (log da urna)"
        ),
        "fonte": "boletins de urna (hora do último voto) e fechamento.json",
    },
    {
        "id": "e",
        "nome": f"entre as {fc.E_TOP} menos prováveis da mistura",
        "mede": (
            "combinação de voto em Lula, Flávio, brancos, nulos e abstenção mais rara "
            "do país pela mistura gaussiana do capítulo 12"
        ),
        "regra": (
            f"as {fc.E_TOP} seções de menor log-verossimilhança na mistura de cinco "
            "grupos do capítulo 12, refeita com a semente e a inicialização gravadas em "
            "secoes.json e conferida contra as 50 menos prováveis publicadas"
        ),
        "limiar": f"{fc.E_TOP} menores log-verossimilhanças",
        "explicacao_comum": (
            "seção pequena com abstenção, brancos ou nulos fora do comum (aldeia, "
            "zona rural, presídio)"
        ),
        "o_que_conferir": "ata: número de votantes, brancos, nulos e ocorrências",
        "fonte": "secoes.json (clusters) e boletins de urna",
    },
    {
        "id": "f",
        "nome": "urna ou arquivo fora do padrão com voto diferente da zona",
        "mede": (
            "troca de urna, recuperação de dados ou mais de uma carga, com voto longe "
            "das vizinhas"
        ),
        "regra": (
            "arquivo recuperado ou de sistema de apuração (tipo de arquivo diferente de 1), "
            "urna de contingência ou reserva (tipo de urna diferente de 1) ou mais de uma "
            f"carga, e Lula ou Flávio {_n(fc.F_DIF)} pontos ou mais longe do resto da zona"
        ),
        "limiar": f"tipo fora do padrão; {_n(fc.F_DIF)} pp contra a zona",
        "explicacao_comum": "urna trocada por defeito ou dados recuperados de mídia",
        "o_que_conferir": (
            "ata: troca de urna ou recuperação de dados, hora, motivo, lacres e número "
            "da urna"
        ),
        "fonte": "boletins de urna (tipo de arquivo, tipo de urna, histórico de cargas)",
    },
    {
        "id": "g",
        "nome": "boletim recebido de madrugada",
        "mede": "boletim que chegou ao TSE depois da meia-noite",
        "regra": f"recebimento (dr/hr do aux.json) às {fc.G_HORA[11:16]} de 05/10 ou depois; exterior fora",
        "limiar": "00:00 de 05/10",
        "explicacao_comum": (
            "área remota com transmissão por satélite, barco ou avião"
        ),
        "o_que_conferir": (
            "hora de emissão do boletim e caminho da mídia até o ponto de transmissão"
        ),
        "fonte": "aux.json de cada seção (secoes_2026.sqlite, tabela secao)",
    },
    {
        "id": "h",
        "nome": "sem arquivo publicado ou em zona congelada",
        "mede": (
            "seção sem boletim publicado no repositório do TSE, ou que faltava num "
            "arquivo de zona que ficou parado incompleto"
        ),
        "regra": (
            "(1) seção principal ativa sem aux.json publicado (o TSE devolve 404; peso "
            f"{fc.PESOS['h_sem_arquivo']}); (2) seção que faltava num arquivo de zona de "
            "presidente que ficou parado incompleto por 6 horas ou mais depois das 17h de "
            "Brasília: as k de recebimento mais recente até a geração da versão parada, "
            f"k = seções totalizáveis menos totalizadas (peso {fc.PESOS['h_zona_congelada']})"
        ),
        "limiar": "404 no aux.json; arquivo de zona parado 6 horas ou mais",
        "explicacao_comum": (
            "atraso de publicação do TSE: os votos estão no arquivo da UF"
        ),
        "o_que_conferir": (
            "boletim impresso afixado e cópia pedida ao presidente da mesa (Lei 9.504, "
            "art. 68, § 1º)"
        ),
        "fonte": "secoes_2026.sqlite (status do aux.json) e apuracao.sqlite (versões do arquivo de zona)",
    },
    {
        "id": "i",
        "nome": "zona entre as 50 mais atípicas e seção longe da UF",
        "mede": "seção numa zona já apontada como atípica, com voto longe da própria UF",
        "regra": (
            "seção numa das 50 zonas de maior escore em anomalias.json com Lula ou Flávio "
            f"{_n(fc.I_EXCESSO_UF)} pontos ou mais acima da própria UF"
        ),
        "limiar": f"50 zonas; {_n(fc.I_EXCESSO_UF)} pp sobre a UF",
        "explicacao_comum": (
            "zona pequena, terceira via forte ou liderança local (ver a explicação da "
            "zona em anomalias.json)"
        ),
        "o_que_conferir": "ata e boletim impresso, com a explicação da zona em mãos",
        "fonte": "anomalias.json (topo) e boletins de urna",
    },
    {
        "id": "j",
        "nome": "variação 2022-2026 fora da faixa da UF",
        "mede": "seção cuja margem mudou muito mais (ou muito menos) que a da UF desde 2022",
        "regra": (
            "seção casada com 2022 (mesmo número e mesmo local), "
            f"{fc.J_MIN_VOTOS} ou mais votos nominais nos dois anos; variação da margem "
            "(Flávio menos Lula em 2026 contra Bolsonaro menos Lula no 1º turno de 2022) "
            f"a mais de {_n(fc.J_DESVIOS)} desvios-padrão da média das seções casadas da UF"
        ),
        "limiar": f"{_n(fc.J_DESVIOS)} desvios-padrão da UF",
        "explicacao_comum": (
            "eleitorado remanejado entre seções, liderança local ou candidatura "
            "estadual forte"
        ),
        "o_que_conferir": "ata e se o eleitorado da seção mudou (remanejamento)",
        "fonte": "boletins de 2026 e votacao_secao_2022_BR.zip (TSE)",
    },
    {
        "id": "k",
        "nome": "brancos ou nulos muito acima da zona",
        "mede": "seção com brancos ou nulos muito acima das outras seções da zona",
        "regra": (
            f"brancos ou nulos (% do comparecimento) {_n(fc.K_DESVIOS)} desvios-padrão ou "
            f"mais acima da média das outras seções da zona e {_n(fc.K_PP)} pontos ou mais "
            f"acima dela; {fc.K_VOTANTES} votantes ou mais e ao menos {fc.K_OUTRAS} outras "
            "seções na zona"
        ),
        "limiar": f"{_n(fc.K_DESVIOS)} desvios-padrão e {_n(fc.K_PP)} pp sobre a zona",
        "explicacao_comum": (
            "eleitor idoso ou com dificuldade na urna, orientação errada ou campanha de "
            "voto nulo local"
        ),
        "o_que_conferir": (
            "ata: reclamação sobre a urna, o teclado ou a orientação ao eleitor"
        ),
        "fonte": "boletins de urna por seção",
    },
    {
        "id": "l",
        "nome": "local com três ou mais seções sinalizadas",
        "mede": "prédio que concentra seções sinalizadas: um fiscal cobre várias",
        "regra": (
            f"local de votação com {fc.L_MIN} ou mais seções sinalizadas pelos critérios "
            "de seção (a, b, c, d, e, f, j, k); g, h e i ficam fora da contagem porque "
            "valem para o local ou a zona inteira por construção"
        ),
        "limiar": f"{fc.L_MIN} seções no mesmo local",
        "explicacao_comum": "local grande numa área que vota em bloco",
        "o_que_conferir": (
            "um fiscal no prédio pode cobrir várias seções do mesmo local (Lei 9.504, "
            "art. 65, § 1º)"
        ),
        "fonte": "cadastro de locais de votação 2026 (número do local)",
    },
]
POR_ID = {c["id"]: c for c in CRITERIOS}


def completar(criterios: list[dict[str, Any]], fechamento: dict[str, Any]) -> None:
    """Põe no critério d o efeito típico medido no capítulo de encerramento.

    Lê o estimador `tarde19_zona` (seção que encerrou às 19h ou depois contra as
    demais da mesma zona) de `fechamento.json`; sem ele, o texto fica como está.
    """
    est = {
        e.get("id"): e for e in (fechamento.get("voto") or {}).get("estimadores", [])
    }
    r = (est.get("tarde19_zona") or {}).get("resultado") or {}
    lula = r.get("lula_pp") or {}
    if lula.get("estimativa") is None or not lula.get("ic95"):
        return
    a, b = lula["ic95"]
    d = next(c for c in criterios if c["id"] == "d")
    d["explicacao_comum"] = (
        "fila longa em seção grande e identificação biométrica lenta: no capítulo de "
        "encerramento, a seção que fechou às 19h ou depois tem, em média, "
        f"{_s(lula['estimativa'])} pontos de Lula sobre as demais da mesma zona (IC 95% "
        f"de {_s(a)} a {_s(b)}); o limiar de {_n(fc.D_EXCESSO)} pontos fica acima disso"
    )


def _s(x: float) -> str:
    return f"{x:+.2f}".replace(".", ",")


def pesos_json() -> dict[str, int]:
    return dict(fc.PESOS)


def cortes_json() -> dict[str, Any]:
    return {
        "alta": fc.CORTE_ALTA,
        "media": fc.CORTE_MEDIA,
        "iguais": {"alta": fc.CORTE_ALTA_IGUAIS, "media": fc.CORTE_MEDIA_IGUAIS},
        "regra": (
            f"alta: pontuação {fc.CORTE_ALTA} ou mais e nenhuma explicação comum "
            "documentada (aldeia, presídio, exterior, trânsito, seção minúscula); média: "
            f"{fc.CORTE_MEDIA} ou mais, ou {fc.CORTE_ALTA} ou mais com explicação comum; "
            "baixa: o resto. Seção de 90% que já votava assim em 2022 (enclave) fica em "
            "baixa. Com pesos iguais, cada critério vale 1: alta com "
            f"{fc.CORTE_ALTA_IGUAIS} critérios ou mais, média com {fc.CORTE_MEDIA_IGUAIS}"
        ),
    }
