"""Capítulo 13, bloco "Onde está o voto da terceira via, cidade por cidade" e o nulo de 2022.

Chamado por `pagina_cap_c.r_segundo_turno`. Todo número sai de
`analysis/apuracao_2026/dados/terceira_via.json`; as leituras por região e o
juízo editorial por região vêm de `terceira_via_texto.py`, as mesmas frases do
memorando. Figura antes do parágrafo que a lê.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape

from . import pagina_texto_reguas as PR
from . import terceira_via_texto as X
from .pagina_comum import NOME_UF, caixa, inteiro, nota, num, p, tabela
from .pagina_fig_base import nome_bonito

CHAVES = [
    "agregados.brasil",
    "agregados.regioes",
    "prioridade.top",
    "prioridade.sensibilidade",
    "teto.ufs",
    "riscos",
    "contrario",
    "conversao_2022.por_classe",
    "nulo_2022.com_2t_governador",
    "nulo_2022.sem_2t_governador",
    "municipios",
]
REGIOES = ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
# Preposição antes do nome da UF ("em Goiás", "no Maranhão", "na Bahia").
NA_UF = {
    **dict.fromkeys(
        (
            "AC",
            "AM",
            "AP",
            "CE",
            "DF",
            "ES",
            "MA",
            "PA",
            "PI",
            "PR",
            "RJ",
            "RN",
            "RS",
            "TO",
        ),
        "no",
    ),
    **dict.fromkeys(("BA", "PB"), "na"),
}


def sem_quebra(html: str) -> str:
    """Tabela larga: células sem quebra de linha, rolagem lateral no celular."""
    return html.replace(
        '<div class="table-scroll"', '<div class="table-scroll tv-nowrap"', 1
    )


def pc(x: float | None, casas: int = 2) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


def mi(x: float) -> str:
    """Votos em prosa: milhões com duas casas, milhares arredondados, sem 'de' depois de 'mil'."""
    a = abs(x)
    s = "−" if x < 0 else ""
    if a >= 1_000_000:
        return (
            f"{s}{num(a / 1e6, 2)} {'milhão' if a < 2_000_000 else 'milhões'} de votos"
        )
    if a >= 10_000:
        return f"{s}{num(a / 1000, 0)} mil votos"
    return f"{s}{inteiro(a)} votos"


def sp(x: float | None, casas: int = 2) -> str:
    if x is None:
        return "s/d"
    return ("+" if x > 0 else "−" if x < 0 else "") + num(abs(x), casas)


def _estoque(D: dict, fig: Callable[[str], str]) -> str:
    ag = D["agregados"]
    nac = ag["brasil"]
    g = nac["por_grupo_pct"]
    cl = nac["por_classe"]
    folga = ((D.get("regras") or {}).get("classes") or {}).get("folga_pp", 10)
    h = "<h3>Onde está o voto da terceira via, cidade por cidade</h3>"
    h += p(
        f"Cury, Renan Santos, Caiado, Zema e as seis candidaturas menores tiveram {mi(nac['estoque'] + ag['exterior']['estoque'])}, "
        f"{mi(ag['exterior']['estoque'])} deles no exterior: Cury {pc(g['cury'])}, Renan {pc(g['renan'])}, Caiado "
        f"{pc(g['caiado'])}, Zema {pc(g['zema'])} e as demais {pc(g['outros'])}."
        + (
            " A soma dos arquivos municipais bate com o arquivo nacional candidatura a candidatura."
            if D["conferencia"]["soma_municipal_igual_nacional"]
            else " A soma dos arquivos municipais ainda difere do arquivo nacional; ver terceira_via.json, conferencia."
        ),
        "verificado",
    )
    h += caixa(
        "io",
        "Como ler este bloco",
        "<ul>"
        f"<li><strong>Classe de margem</strong>: Flávio menos Lula no município; folga a partir de {num(folga, 0)} pontos.</li>"
        "<li><strong>Vão local</strong>: o nome do lado de Flávio mais votado ali, ao governo ou ao Senado, menos "
        "Flávio.</li>"
        "<li><strong>Teto endereçável</strong>: terceira via mais vão positivo; pode contar o mesmo eleitor duas vezes."
        "</li></ul>",
    )
    h += fig("terceira_via_mapa")
    h += p(
        f"{pc(nac['onde_flavio_venceu_parcela'])} desse voto está onde Flávio venceu: {pc(cl['venceu_folga']['estoque_parcela'])} "
        f"onde venceu com folga ({inteiro(cl['venceu_folga']['municipios'])} municípios) e "
        f"{pc(cl['venceu_apertado']['estoque_parcela'])} onde venceu por menos de {num(folga, 0)} pontos. Onde Lula venceu com folga "
        f"ficam {pc(cl['perdeu_folga']['estoque_parcela'])} ({inteiro(cl['perdeu_folga']['municipios'])} municípios). "
        f"Capitais guardam {pc(ag['capitais']['parcela_do_estoque'])}; capitais e cidades com "
        f"{inteiro(ag['grandes']['corte_eleitores'])} eleitores ou mais, {pc(ag['capitais_ou_grandes']['parcela_do_estoque'])}.",
        "verificado",
    )
    h += fig("terceira_via_classes")
    linhas = []
    conv = D["conversao_2022"]["por_regiao"]
    for r in REGIOES:
        a = ag["regioes"][r]
        linhas.append(
            [
                r,
                inteiro(a["estoque"]),
                pc(a["parcela_do_estoque"]),
                pc(a["onde_flavio_venceu_parcela"]),
                pc(a["renan_zema_pct"]),
                pc(a["por_grupo_pct"]["caiado"]),
                num(a["saldo_por_voto"], 3),
                num(conv[r]["saldo"], 3),
                inteiro(a["vao_positivo"]),
                inteiro(a["municipios_vao_positivo"]),
            ]
        )
    h += tabela(
        [
            "Região",
            "Terceira via",
            "Parcela do país",
            "Onde Flávio venceu",
            "Renan + Zema",
            "Caiado",
            "Saldo por voto, matriz Nexus",
            "Razão simples de 2022",
            "Direita local acima de Flávio",
            "Municípios com direita local acima",
        ],
        linhas,
        "Saldo por voto: votos para Flávio menos votos para Lula por voto de terceira via. Matriz: hipótese. Razão "
        "simples de 2022: todo o ganho entre os turnos dividido pela terceira via do 1º turno (analogia; a régua da "
        "urna que separa a mobilização da base vem adiante).",
    )
    return h


def _matriz(D: dict) -> str:
    nac = D["agregados"]["brasil"]
    co = D["contrario"]
    m = D["matriz"]
    pub = m["publicadas_nexus"]
    go = D["agregados"]["ufs"].get("GO", {})
    return p(
        f"Pela matriz da Nexus aplicada município a município, a terceira via dá {mi(nac['para_flavio'])} a Flávio e "
        f"{mi(nac['para_lula'])} a Lula, saldo de {mi(nac['saldo'])}; {mi(nac['fora'])} ficam em branco, nulo ou "
        f"indecisão. Com o Datafolha em Cury e Caiado, o saldo vai a {mi(nac['saldo_df'])}.",
        "inferencia",
    ) + nota(
        "hipotese",
        f"A linha de cada candidatura é nacional (Nexus, p. 79: Renan, Flávio {pub['Renan']['Flávio']} e Lula "
        f"{pub['Renan']['Lula']}; Zema {pub['Zema']['Flávio']} e {pub['Zema']['Lula']}; Cury {pub['Cury']['Flávio']} e "
        f"{pub['Cury']['Lula']}; Caiado {pub['Caiado']['Flávio']} e {pub['Caiado']['Lula']}) e vale para todo município, "
        "como se o eleitor de Cury em Salvador votasse como o de Joinville. As duas medições de Caiado discordam de "
        f"lado, e em Goiás, onde ele tem {pc(co['caiado_goias']['pct_estoque_go'])} do estoque, a Nexus dá a Flávio "
        f"{mi(go.get('saldo', 0))} e o Datafolha, {mi(go.get('saldo_df', 0))}.",
        "Da matriz.",
    )


def _sem_apoio(D: dict) -> str:
    nomes = [
        f"{nome_bonito(loc['governador']['nome'])} {NA_UF.get(uf, 'em')} {NOME_UF[uf]}"
        for uf, loc in sorted(D["direita_local"].items())
        if loc.get("governador")
        and loc["governador"]["comparacao"] == "sem apoio declarado"
    ]
    return X.lista_e(nomes)


def _direita_local(D: dict, fig: Callable[[str], str]) -> str:
    nac = D["agregados"]["brasil"]
    ne = D["agregados"]["regioes"]["Nordeste"]
    h = fig("terceira_via_teto_uf")
    h += p(
        f"Em {inteiro(nac['municipios_vao_positivo'])} municípios um nome do lado de Flávio teve mais votos que ele, "
        f"{mi(nac['vao_positivo'])} acima, {pc(100 * ne['vao_positivo'] / nac['vao_positivo'])} no Nordeste. Sem os "
        f"governadores eleitos que não declararam apoio a Flávio ({_sem_apoio(D)}), o vão é de "
        f"{mi(nac['vao_positivo_sem_governador_sem_apoio'])}. Com a terceira via, o teto endereçável local chega a "
        f"{mi(nac['teto'])}: teto, não previsão.",
        "verificado",
    )
    return h


def _prioridade(D: dict, fig: Callable[[str], str]) -> str:
    P = D["prioridade"]
    soma = P["soma_top"]
    pesos = P["pesos"]
    h = nota(
        "juizo",
        f"Prioridade = votos de terceira via × fator de conversão, média ponderada da posição do município em quatro "
        f"variáveis: vão local {num(pesos['vao_local'], 2)}, matriz por nome {num(pesos['matriz'], 2)}, Bolsonaro no 2º "
        f"turno de 2022 {num(pesos['ambiente_2022'], 2)} e margem de Flávio {num(pesos['margem'], 2)}. O vão pesa mais "
        "porque é a única evidência medida no próprio município.",
        "Os pesos do índice.",
    )
    h += fig("terceira_via_prioridade")
    reg = ", ".join(f"{r} {soma['por_regiao'][r]}" for r in REGIOES)
    pcl = soma["por_classe"]
    menor = min(s["em_comum_com_central"] for s in P["sensibilidade"])
    so_vao = next(s for s in P["sensibilidade"] if s["nome"] == "vao_local")
    h += p(
        f"Os 100 primeiros somam {mi(soma['estoque'])} de terceira via e saldo esperado de {mi(soma['saldo'])} pela Nexus "
        f"({mi(soma['saldo_df'])} com o Datafolha), {pc(soma['saldo_sobre_diferenca_pct'])} da diferença do 1º turno; "
        f"{mi(soma['fora'])} vão para branco, nulo ou indecisão, a parte que a militância pode disputar. Por região, "
        f"{reg}; {pcl['venceu_folga'] + pcl['venceu_apertado']} onde Flávio venceu; {soma['capitais']} capitais. "
        f"Sem os pesos da casa, qualquer ordem alternativa mantém ao menos {menor} dos 100: o volume manda. Só pelo vão "
        f"local, o Nordeste sobe de {soma['por_regiao']['Nordeste']} para {so_vao['por_regiao']['Nordeste']} municípios.",
        "inferencia",
    )
    linhas = [
        [
            escape(X.SENS_NOME[s["nome"]]),
            str(s["em_comum_com_central"]),
            *[str(s["por_regiao"][r]) for r in REGIOES],
            inteiro(s["saldo"]),
            escape(
                ", ".join(
                    f"{nome_bonito(n['nome'])} ({n['uf']})" for n in s["primeiros"][:5]
                )
            ),
        ]
        for s in P["sensibilidade"]
    ]
    h += sem_quebra(
        tabela(
            [
                "Ordem",
                "Em comum com o índice",
                *REGIOES,
                "Saldo esperado dos 100",
                "Cinco primeiros",
            ],
            linhas,
            "Sensibilidade: os 100 primeiros com o fator trocado por uma variável só, ou sem fator (só volume).",
        )
    )
    return h


def _primeira(texto: str) -> str:
    """A primeira frase do juízo regional; os números dele estão na tabela e na frase seguinte."""
    return texto.split(". ")[0].rstrip(".") + "."


def _regioes(D: dict) -> str:
    juizo = X.juizo_regional(D)
    ordem = ("Nordeste", "Sudeste", "Sul", "Centro-Oeste", "Norte")
    h = nota(
        "juizo",
        "<ul>"
        + "".join(
            f"<li><strong>{r}:</strong> {escape(_primeira(juizo[r]))}</li>"
            for r in ordem
        )
        + "</ul>",
        "O que fazer em cada região.",
    )
    ag = D["agregados"]
    ne, se = ag["regioes"]["Nordeste"], ag["regioes"]["Sudeste"]
    perfil = X.perfis(D)
    sem = [x for x in ne["lideres"] if perfil.get(x["nome"], {}).get("sem_apoio")]
    com = [x for x in ne["lideres"] if not perfil.get(x["nome"], {}).get("sem_apoio")]
    govs = {
        loc["governador"]["nome"]
        for uf, loc in D["direita_local"].items()
        if uf in ("SP", "MG") and loc.get("governador")
    }
    dos_govs = sum(x["vao_votos"] for x in se["lideres"] if x["nome"] in govs)
    h += p(
        "No Nordeste os maiores vãos são de governadores sem apoio declarado a Flávio, teto e não palanque: "
        + X.lista_e([X._quem(x, perfil) for x in sem])
        + f". Sem eles, o vão da região cai a {mi(ne['vao_positivo_sem_governador_sem_apoio'])}, puxado por "
        + X.lista_e([X._quem(x, perfil) for x in com[:3]])
        + f". No Sudeste, {pc(100 * dos_govs / se['vao_positivo'] if se['vao_positivo'] else 0)} do vão vem de Tarcísio "
        "e Cleitinho.",
        "verificado",
    )
    linhas = []
    for r in REGIOES:
        for x in D["prioridade"]["por_regiao"][r]:
            lider = (
                f"{nome_bonito(x['local_lider'])} (+{inteiro(x['vao_votos'])})"
                if x["vao_votos"] > 0 and x["local_lider"]
                else "nenhum"
            )
            linhas.append(
                [
                    r,
                    str(x["posicao"]),
                    escape(f"{nome_bonito(x['nome'])} ({x['uf']})"),
                    inteiro(x["estoque"]),
                    sp(x["margem_pp"], 1),
                    escape(lider),
                    sp(x["saldo"], 0),
                ]
            )
    h += sem_quebra(
        tabela(
            [
                "Região",
                "Nº no país",
                "Município",
                "Terceira via",
                "Margem de Flávio (pp)",
                "Direita local acima de Flávio",
                "Saldo Nexus",
            ],
            linhas,
            "Os 10 primeiros de cada região pelo índice de prioridade.",
        )
    )
    return h


def _regressao(D: dict) -> str:
    """Os mesmos dois grupos pela régua da urna (regressão), quando ela existe no JSON."""
    if "reguas" not in D:
        return ""
    g = D["reguas"]["modelos"]["classe"]["grupos"]
    return (
        f"; a regressão, que separa a mobilização da base, dá {sp(g['perdeu_folga']['saldo'], 2)} e "
        f"{sp(g['venceu_folga']['saldo'], 2)}"
    )


def _contrario(D: dict) -> str:
    ri, co = D["riscos"], D["contrario"]
    conv = D["conversao_2022"]["por_classe"]
    nc = co["nordeste_capitais"]
    return p(
        f"Onde Lula venceu com folga ficam {mi(ri['lula_com_folga']['estoque'])}, {pc(ri['lula_com_folga']['parcela'])} do "
        f"estoque, e a matriz diz que ali cada voto rende quase o mesmo que no país "
        f"({num(ri['lula_com_folga']['saldo_por_voto'], 3)} contra {num(D['agregados']['brasil']['saldo_por_voto'], 3)}), "
        f"porque não sabe onde o eleitor mora. A urna de 2022 sabe: ali a terceira via rendeu "
        f"{num(conv['perdeu_folga']['saldo'], 2)} a Bolsonaro entre os turnos, contra {num(conv['venceu_folga']['saldo'], 2)} "
        f"onde Flávio venceu com folga (razão simples){_regressao(D)}. Nas nove capitais do Nordeste, Lula fez "
        f"{num(-nc['margem_pp'], 2)} pontos sobre Flávio e a terceira via soma {mi(nc['estoque'])}, {mi(nc['caiado'])} de "
        "Caiado.",
        "contrario",
    )


def _quintos_frase(sg: dict) -> str:
    """Frase sobre os cinco grupos sem 2º turno estadual, conforme o sinal medido."""
    deltas = [q["delta_pp"] for q in sg["quintis_terceira_via"]]
    if deltas and all(d < 0 for d in deltas):
        tendencia = (
            "caiu menos onde a terceira via era maior"
            if deltas[-1] > deltas[0]
            else "caiu mais onde a terceira via era maior"
        )
        return f"Sem disputa estadual, o branco e nulo caiu nos cinco grupos de municípios e {tendencia}"
    return "Sem disputa estadual, o branco e nulo variou assim pelos cinco grupos de municípios"


def _nulo(D: dict, fig: Callable[[str], str]) -> str:
    N = D["nulo_2022"]
    nac, cg, sg, mod, rk = (
        N["nacional"],
        N["com_2t_governador"],
        N["sem_2t_governador"],
        N["modelo"],
        N["risco_2026"],
    )
    fora = D["agregados"]["brasil"]["fora"]
    h = "<h3>O risco do voto nulo, medido em 2022</h3>"
    h += p(
        f"Entre os turnos de 2022, branco e nulo de presidente foram de {pc(nac['bn_1t_pct'])} para {pc(nac['bn_2t_pct'])} "
        f"dos votantes, {inteiro(nac['acrescimo'])} votos a mais, {pc(100 * nac['taxa'], 1)} da terceira via de então "
        f"({mi(nac['terceira_via_2022'])}).",
        "verificado",
    )
    h += fig("nulo_2022_municipios")
    quintos = ", ".join(sp(q["delta_pp"], 2) for q in sg["quintis_terceira_via"])
    h += p(
        f"O aumento foi onde havia 2º turno de governador: {sp(cg['delta_pp'], 2)} ponto nas {len(cg['ufs'])} UFs com "
        f"disputa estadual e {sp(sg['delta_pp'], 2)} nas outras {len(sg['ufs'])}. Controlando pela terceira via, o 2º "
        f"turno estadual soma {num(mod['c_governador'], 2)} ponto, e cada ponto de terceira via, "
        f"{num(mod['b_terceira_via'], 3)}. {_quintos_frase(sg)} ({quintos}, do quinto com menos terceira via ao de mais).",
        "inferencia",
    )
    h += nota(
        "hipotese",
        "O eleitor que volta à urna pelo governador e não escolhe presidente explicaria a diferença. Em 2026 há 2º turno "
        f"estadual em {', '.join(rk['ufs'])}, com {inteiro(rk['comparecimento'])} votantes; pela taxa de 2022, "
        f"{mi(rk['votos'])} podem virar branco ou nulo, {pc(X.parcela_rio(N))} deles no Rio de Janeiro. A matriz manda "
        f"{mi(fora)} da terceira via para branco, nulo ou indecisão; a urna de 2022 sugere que boa parte disso escolhe "
        "um lado ou falta.",
    )
    linhas = [
        [
            escape(f"{nome_bonito(m['nome'])} ({m['uf']})"),
            pc(m["bn_1t_pct"]),
            pc(m["bn_2t_pct"]),
            sp(m["delta_pp"], 2),
            pc(m["tv22_pct"], 1),
            "sim" if m["gov22_2t"] else "não",
            inteiro(m["estoque_2026"]),
        ]
        for m in N["maiores"]
    ]
    h += tabela(
        [
            "Município",
            "Branco e nulo, 1º turno",
            "2º turno",
            "Variação (pp)",
            "Terceira via 2022",
            "2º turno de governador em 2022",
            "Terceira via 2026",
        ],
        linhas,
        f"Municípios com {inteiro(N['corte_comparecimento'])} votantes ou mais onde o branco e nulo de presidente mais cresceu entre os turnos de 2022.",
    )
    return h


LIMITES = [
    "A matriz de transferência é nacional e aplicada localmente: hipótese declarada, não medição por município.",
    "Vão local e teto são mesma urna e cargos diferentes: não dizem quem votou em quem, e o governador sem apoio "
    "declarado a Flávio é teto, não palanque.",
    "2022 é uma eleição só, com outra terceira via (Tebet e Ciro) e outro mapa de 2º turno estadual.",
    "Os pesos do índice são juízo editorial; as sensibilidades estão ao lado.",
    "Nada aqui é previsão do 2º turno.",
]


def bloco(D: dict, fig: Callable[[str], str]) -> str:
    """HTML do bloco, na ordem: estoque, matriz, direita local, prioridade, regiões, contrário, réguas, nulo."""
    return (
        _estoque(D, fig)
        + _matriz(D)
        + _direita_local(D, fig)
        + _prioridade(D, fig)
        + _regioes(D)
        + _contrario(D)
        + (PR.bloco(D, fig) if "reguas" in D else "")
        + _nulo(D, fig)
    )
