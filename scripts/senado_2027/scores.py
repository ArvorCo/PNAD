"""Régua K (exposição judicial) e C (contrapeso), seção 3 do CONTRATO.

Nenhum score é copiado dos relatórios de origem: a régua abaixo é aplicada aos
fatos dos JSON. Todas as constantes vivem em `REGUA`, que a página imprime a
partir daqui, sem digitar número.
"""

from __future__ import annotations

import copy
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from .base import CENARIOS, ano_de, normalizar

REGUA: dict[str, Any] = {
    "K": {
        "estagio": {
            "condenacao": 60,
            "reu": 45,
            "denuncia_oferecida": 35,
            "indiciado": 30,
            "investigado": 25,
            "alvo_de_busca": 25,
            "eleitoral_pendente": 20,
            "citado": 12,
            "representacao": 10,
            "acusacao_sem_procedimento": 5,
            "arquivado": 6,
            "absolvido_ou_trancado": 4,
            "testemunha": 2,
            "suspenso": 30,
            "condenacao_civel": 25,
            "reu_civel": 15,
            "antigo_sem_desfecho": 8,
            "arquivamento_pedido": 8,
        },
        "foro": {"STF": 10, "STJ": 5, "TSE": 5},
        "estagios_inativos": (
            "arquivado",
            "absolvido_ou_trancado",
            "testemunha",
            "acusacao_sem_procedimento",
            "antigo_sem_desfecho",
            "arquivamento_pedido",
        ),
        "regra_inativos": (
            "Caso inativo vale só os pontos do estágio: foro, relator e "
            "recência não se somam a procedimento encerrado ou parado."
        ),
        "relator_alvo": {
            "pontos": 5,
            "ministros": (
                "Alexandre de Moraes",
                "Flávio Dino",
                "Dias Toffoli",
                "Gilmar Mendes",
            ),
        },
        "recencia": {"pontos": 10, "ano_minimo": 2025},
        "peso_demais_casos": 0.3,
        "teto": 100,
        "regra_empate": (
            "Casos empatados no maior valor dividem igualmente o peso "
            "1 + 0,3 × (empatados − 1); o K não muda, só a parcela de cada caso."
        ),
    },
    "C": {
        "base": {
            "C_imp": {"DB": 85, "D": 75, "CD": 55, "C": 35, "CE": 10, "E": 3},
            "C_pec": {"DB": 92, "D": 88, "CD": 80, "C": 65, "CE": 30, "E": 10},
        },
        "ajustes": (
            {
                "chave": "declaracao_pro_impeachment",
                "rotulo": "Declaração pró-impeachment",
                "sinais": ("declaracao_pro_impeachment",),
                "C_imp": 10,
                "C_pec": 5,
            },
            {
                "chave": "assinatura_pedido_impeachment",
                "rotulo": "Assinatura de pedido de impeachment de ministro",
                "sinais": ("assinatura_pedido_impeachment",),
                "C_imp": 8,
                "C_pec": 4,
            },
            {
                "chave": "cpi_contra_ministros",
                "rotulo": "CPI contra ministros (requerimento, relatoria ou assinatura)",
                "sinais": ("cpi_contra_ministros",),
                "C_imp": 8,
                "C_pec": 4,
            },
            {
                "chave": "acao_judicial_contra_ministro",
                "rotulo": "Ação judicial contra ministro",
                "sinais": ("acao_judicial_contra_ministro",),
                "C_imp": 8,
                "C_pec": 4,
            },
            {
                "chave": "voto_pec8_sim",
                "rotulo": "Votou sim na PEC 8/2021",
                "sinais": ("voto_pec8_sim",),
                "C_imp": 3,
                "C_pec": 10,
            },
            {
                "chave": "voto_pec8_nao",
                "rotulo": "Votou não na PEC 8/2021",
                "sinais": ("voto_pec8_nao",),
                "C_imp": -10,
                "C_pec": -20,
            },
            {
                "chave": "declaracao_contra_impeachment",
                "rotulo": "Declaração contra impeachment",
                "sinais": ("declaracao_contra_impeachment",),
                "C_imp": -15,
                "C_pec": -5,
            },
            {
                "chave": "representacao_administrativa_contra_ministro",
                "rotulo": "Representação administrativa contra ministro (CNJ, Conselho)",
                "sinais": ("representacao_administrativa_contra_ministro",),
                "C_imp": 4,
                "C_pec": 2,
            },
            {
                "chave": "dialogavel_segundo_stf",
                "rotulo": "Dialogável segundo ministros do STF, ou sondou ministro",
                "sinais": ("dialogavel_segundo_stf", "sondagem_com_ministro"),
                "C_imp": -8,
                "C_pec": 0,
            },
            {
                "chave": "nao_assinou_pedido",
                "rotulo": "Não assinou pedido ou CPI da própria bancada",
                "sinais": ("nao_assinou_pedido",),
                "C_imp": -4,
                "C_pec": 0,
            },
            {
                "chave": "sem_posicao_localizada",
                "rotulo": "Sem posição localizada",
                "sinais": ("sem_posicao_localizada",),
                "C_imp": -6,
                "C_pec": -3,
            },
        ),
        "piso_autoria": {
            "rotulo": "Autoria de pedido de impeachment ou relatoria de CPI que pediu indiciamento de ministro",
            "sinais": ("autoria_pedido_impeachment",),
            "C_imp": 85,
            "C_pec": 90,
        },
        "regra_ajustes": (
            "Cada linha conta uma vez, por mais sinais do mesmo tipo que haja. "
            "Sem nenhum sinal com posição, vale a linha de sem posição localizada."
        ),
        "sinais_sem_ajuste": (
            "voto_pec8_ausente",
            "projeto_ou_pec_contra_stf",
            "defesa_do_stf",
        ),
        "alinhado_governo_lula": {
            "rotulo": "Alinhamento declarado com o governo Lula",
            "C_imp": -10,
            "C_pec": -5,
        },
        "redutor_patrimonial": {
            "rotulo": "Redutor patrimonial",
            "tipo": "patrimonial",
            "estagios_ativos": (
                "condenacao",
                "condenacao_civel",
                "reu",
                "reu_civel",
                "suspenso",
                "denuncia_oferecida",
                "indiciado",
                "investigado",
                "alvo_de_busca",
            ),
            "C_imp": 0.25,
            "C_pec": 0.10,
        },
        "cenario_lula": {
            "rotulo": "Cenário de governo Lula",
            "C_imp": {"C": -15, "CD": -15, "D": -5},
            "C_pec": {"C": -8, "CD": -8, "D": -3},
        },
        "limites": (2, 97),
    },
    "confianca": {
        "sinais_observados": (
            "voto_pec8_sim",
            "voto_pec8_nao",
            "assinatura_pedido_impeachment",
            "cpi_contra_ministros",
            "acao_judicial_contra_ministro",
            "representacao_administrativa_contra_ministro",
            "projeto_ou_pec_contra_stf",
        ),
        "minimo_observados_alta": 2,
        "sinais_sem_posicao": ("sem_posicao_localizada", "voto_pec8_ausente"),
        "incerteza_pp": {"alta": 5, "media": 9, "baixa": 14},
    },
    "simulacao": {
        "sorteios": 20000,
        "semente": 20270201,
        "correlacao_intrabloco": 0.35,
        "correlacao_nacional": 0.15,
        "limiares": {"C_pec": 49, "C_imp": 54},
        "faixa_pivo": (20, 85),
    },
}

ALVOS = ("C_imp", "C_pec")


def r1(valor: float) -> float:
    """Uma casa decimal, metade para longe do zero (como se faz à mão)."""
    return float(Decimal(repr(float(valor))).quantize(Decimal("0.1"), ROUND_HALF_UP))


def br(valor: float) -> str:
    """Número com uma casa e vírgula decimal, para texto público."""
    return f"{r1(valor):.1f}".replace(".", ",")


def regua_publicavel() -> dict:
    """Cópia da régua só com tipos de JSON (tuplas viram listas)."""

    def plano(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: plano(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [plano(v) for v in obj]
        return obj

    return plano(copy.deepcopy(REGUA))


def relator_alvo(relator: str | None) -> str | None:
    """Ministro alvo de pedidos de impeachment que relata o caso, se houver.

    Casa pelo nome completo contido no campo ou pelo sobrenome sozinho
    ("Moraes", "Min. Dino"), para não confundir com juiz homônimo de outra
    instância.
    """
    if not relator:
        return None
    texto = normalizar(relator)
    sem_titulo = " ".join(
        p for p in texto.split() if p not in {"min", "ministro", "ministra", "relator"}
    )
    for ministro in REGUA["K"]["relator_alvo"]["ministros"]:
        nome = normalizar(ministro)
        sobrenome = nome.split()[-1]
        apelidos = {nome, sobrenome, " ".join(nome.split()[-2:])}
        if ministro == "Gilmar Mendes":
            apelidos.add("gilmar")
        if f" {nome} " in f" {texto} " or sem_titulo in apelidos:
            return ministro
    return None


def pontos_caso(caso: dict) -> dict:
    """Pontos de um caso e seus quatro componentes."""
    k = REGUA["K"]
    estagio = k["estagio"][caso["estagio"]]
    inativo = caso["estagio"] in k["estagios_inativos"]
    foro = 0 if inativo else k["foro"].get(caso["foro"], 0)
    ministro = relator_alvo(caso.get("relator"))
    relator = k["relator_alvo"]["pontos"] if ministro and not inativo else 0
    ano = ano_de(caso.get("data_ultima_decisao"))
    recente = ano is not None and ano >= k["recencia"]["ano_minimo"]
    recencia = k["recencia"]["pontos"] if recente and not inativo else 0
    redutor = REGUA["C"]["redutor_patrimonial"]
    return {
        "id": caso["id"],
        "tipo": caso["tipo"],
        "estagio": caso["estagio"],
        "pontos": estagio + foro + relator + recencia,
        "componentes": {
            "estagio": estagio,
            "foro": foro,
            "relator": relator,
            "recencia": recencia,
        },
        "relator_alvo": ministro,
        "patrimonial_ativo": caso["tipo"] == redutor["tipo"]
        and caso["estagio"] in redutor["estagios_ativos"],
    }


def exposicao(casos: list[dict]) -> dict:
    """K do senador: maior caso + 0,3 × soma dos demais, teto 100.

    A parcela de cada caso é o peso dele (1 para o maior, 0,3 para os demais,
    divisão igual em empate no maior) vezes os pontos, reescalada pelo teto.
    `K_patrimonial_ativo` soma as parcelas dos casos patrimoniais ativos.
    """
    itens = [pontos_caso(c) for c in casos]
    if not itens:
        return {
            "K": 0.0,
            "K_bruto": 0.0,
            "K_por_caso": [],
            "K_patrimonial_ativo": 0.0,
        }
    k = REGUA["K"]
    peso = k["peso_demais_casos"]
    pontos = [i["pontos"] for i in itens]
    maior = max(pontos)
    empatados = pontos.count(maior)
    bruto = maior + peso * (sum(pontos) - maior)
    total = min(bruto, k["teto"])
    escala = total / bruto
    peso_maior = (1 + peso * (empatados - 1)) / empatados
    patrimonial = 0.0
    por_caso = []
    for item in itens:
        if item["pontos"] == maior:
            papel = "maior" if empatados == 1 else "empate_no_maior"
            w = peso_maior
        else:
            papel = "demais"
            w = peso
        parcela = w * item["pontos"] * escala
        if item["patrimonial_ativo"]:
            patrimonial += parcela
        por_caso.append({**item, "papel": papel, "parcela": r1(parcela)})
    return {
        "K": r1(total),
        "K_bruto": r1(bruto),
        "K_por_caso": por_caso,
        "K_patrimonial_ativo": r1(patrimonial),
    }


def _tipos_sinal(senador: dict) -> set[str]:
    return {s["tipo"] for s in senador.get("sinais_contrapeso") or []}


def _sem_posicao(tipos: set[str]) -> bool:
    return not tipos - set(REGUA["confianca"]["sinais_sem_posicao"])


def confianca(senador: dict) -> str:
    """Alta com dois ou mais sinais observados; baixa para suplente ou sem sinal."""
    regra = REGUA["confianca"]
    sinais = senador.get("sinais_contrapeso") or []
    observados = sum(1 for s in sinais if s["tipo"] in regra["sinais_observados"])
    if observados >= regra["minimo_observados_alta"]:
        return "alta"
    suplente = str(senador.get("mandato", "")).startswith("suplente")
    if suplente or _sem_posicao(_tipos_sinal(senador)):
        return "baixa"
    return "media"


def contrapeso(senador: dict, k_patrimonial_ativo: float, cenario: str) -> dict:
    """C_imp e C_pec com a lista de linhas que somam o resultado."""
    if cenario not in CENARIOS:
        raise ValueError(f"cenário {cenario!r} fora de {CENARIOS}")
    c = REGUA["C"]
    bloco = senador["bloco"]
    linhas: list[dict] = []

    def linha(chave: str, rotulo: str, imp: float, pec: float) -> None:
        linhas.append({"chave": chave, "rotulo": rotulo, "C_imp": imp, "C_pec": pec})

    linha(
        "base",
        f"Base do bloco {bloco}",
        c["base"]["C_imp"][bloco],
        c["base"]["C_pec"][bloco],
    )
    tipos = _tipos_sinal(senador)
    for ajuste in c["ajustes"]:
        rotulo = ajuste["rotulo"]
        presente = bool(tipos & set(ajuste["sinais"]))
        if ajuste["chave"] == "sem_posicao_localizada":
            # Só pesa quando não há nenhum sinal com posição: uma lista da
            # imprensa que omite o nome não apaga uma declaração localizada.
            presente = _sem_posicao(tipos)
            rotulo = f"{rotulo} (nenhum sinal com posição registrado)"
        if presente:
            linha(ajuste["chave"], rotulo, ajuste["C_imp"], ajuste["C_pec"])
    if senador.get("alinhado_governo_lula") is True:
        aj = c["alinhado_governo_lula"]
        linha("alinhado_governo_lula", aj["rotulo"], aj["C_imp"], aj["C_pec"])
    if k_patrimonial_ativo > 0:
        red = c["redutor_patrimonial"]
        linha(
            "redutor_patrimonial",
            f"{red['rotulo']} sobre K patrimonial ativo de {br(k_patrimonial_ativo)}",
            r1(-red["C_imp"] * k_patrimonial_ativo),
            r1(-red["C_pec"] * k_patrimonial_ativo),
        )
    if cenario == "lula":
        cen = c["cenario_lula"]
        imp = cen["C_imp"].get(bloco, 0)
        pec = cen["C_pec"].get(bloco, 0)
        if imp or pec:
            linha("cenario_lula", f"{cen['rotulo']} (bloco {bloco})", imp, pec)
    piso, teto = c["limites"]
    soma = {alvo: r1(sum(x[alvo] for x in linhas)) for alvo in ALVOS}
    autoria = c["piso_autoria"]
    if tipos & set(autoria["sinais"]):
        for alvo in ALVOS:
            if soma[alvo] < autoria[alvo]:
                linha(
                    "piso_autoria",
                    f"{autoria['rotulo']}: piso de {autoria[alvo]} em {alvo}",
                    *(
                        (
                            r1(autoria[a] - soma[a])
                            if a == alvo and soma[a] < autoria[a]
                            else 0
                        )
                        for a in ALVOS
                    ),
                )
        soma = {alvo: r1(sum(x[alvo] for x in linhas)) for alvo in ALVOS}
    final = {alvo: min(max(soma[alvo], piso), teto) for alvo in ALVOS}
    if final != soma:
        linha(
            "limite",
            f"Limite de {piso} a {teto}",
            r1(final["C_imp"] - soma["C_imp"]),
            r1(final["C_pec"] - soma["C_pec"]),
        )
    return {
        "C_imp": float(final["C_imp"]),
        "C_pec": float(final["C_pec"]),
        "ajustes": linhas,
    }


def pontuar(senador: dict, cenario: str = "flavio") -> dict:
    """K, C e confiança de um senador num cenário."""
    k = exposicao(senador.get("casos") or [])
    c = contrapeso(senador, k["K_patrimonial_ativo"], cenario)
    nivel = confianca(senador)
    return {
        "cenario": cenario,
        **k,
        "C_imp": c["C_imp"],
        "C_pec": c["C_pec"],
        "confianca": nivel,
        "incerteza_pp": REGUA["confianca"]["incerteza_pp"][nivel],
        "ajustes": c["ajustes"],
    }


def pontuar_cenarios(senador: dict) -> dict[str, dict]:
    """`pontuar` nos dois cenários de governo."""
    return {cenario: pontuar(senador, cenario) for cenario in CENARIOS}
