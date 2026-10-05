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
from .pagina_comum import NOME_UF, inteiro, num, p, rotulo, tabela
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
    h = "<h3>Onde está o voto da terceira via, cidade por cidade</h3>"
    h += p(
        f"Cury, Renan Santos, Caiado, Zema e as seis candidaturas menores tiveram {mi(nac['estoque'] + ag['exterior']['estoque'])}: "
        f"{mi(nac['estoque'])} no Brasil e {mi(ag['exterior']['estoque'])} no exterior. Cury tem {pc(g['cury'])} desse voto, "
        f"Renan {pc(g['renan'])}, Caiado {pc(g['caiado'])}, Zema {pc(g['zema'])} e as demais {pc(g['outros'])}."
        + (
            " A soma dos arquivos municipais do TSE bate com o arquivo nacional candidatura a candidatura."
            if D["conferencia"]["soma_municipal_igual_nacional"]
            else " A soma dos arquivos municipais ainda difere do arquivo nacional; ver terceira_via.json, conferencia."
        ),
        "verificado",
    )
    h += (
        '<aside class="io"><b>Como ler este bloco</b>'
        "<ul>"
        "<li><strong>Terceira via</strong> é todo voto válido de presidente fora de Flávio e Lula, no município.</li>"
        "<li><strong>Classe de margem</strong> é a vantagem de Flávio sobre Lula no município, com folga a partir de 10 pontos. "
        "É uma das quatro variáveis do índice, nunca filtro: a análise cobre o país inteiro.</li>"
        "<li><strong>Vão local</strong> é o nome do lado de Flávio com mais votos no município, ao governo ou ao Senado, menos os "
        "votos de Flávio. Mesma urna, cargos diferentes: mostra que há eleitor que vota na direita local e não em Flávio, "
        "não diz quem.</li>"
        "<li><strong>Teto endereçável</strong> é terceira via mais vão positivo. Pode contar o mesmo eleitor duas vezes: é teto, "
        "não previsão.</li>"
        "</ul></aside>"
    )
    h += fig("terceira_via_mapa")
    h += p(
        f"{pc(nac['onde_flavio_venceu_parcela'])} do voto de terceira via está em municípios onde Flávio venceu: "
        f"{pc(cl['venceu_folga']['estoque_parcela'])} onde venceu com folga ({inteiro(cl['venceu_folga']['municipios'])} "
        f"municípios) e {pc(cl['venceu_apertado']['estoque_parcela'])} onde venceu por menos de 10 pontos. Onde Lula venceu "
        f"com folga ficam {pc(cl['perdeu_folga']['estoque_parcela'])}, em {inteiro(cl['perdeu_folga']['municipios'])} "
        f"municípios. As capitais guardam {pc(ag['capitais']['parcela_do_estoque'])} do estoque; capitais e cidades com "
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
        ],
        linhas,
        "Saldo por voto: votos para Flávio menos votos para Lula por voto de terceira via. Pela matriz, hipótese; razão "
        "simples de 2022: todo o ganho entre os turnos dividido pela terceira via do 1º turno, no mesmo território "
        "(analogia; a regressão que separa a mobilização da base está em Pesquisa contra urna).",
    )
    return h


def _matriz(D: dict) -> str:
    nac = D["agregados"]["brasil"]
    co = D["contrario"]
    m = D["matriz"]
    pub = m["publicadas_nexus"]
    return (
        p(
            f"Pela matriz da Nexus aplicada município a município, os votos de terceira via dão a Flávio {mi(nac['para_flavio'])} "
            f"e a Lula {mi(nac['para_lula'])}, saldo de {mi(nac['saldo'])}; {mi(nac['fora'])} ficam em branco, nulo ou "
            f"indecisão. Com as linhas do Datafolha para Cury e Caiado, o saldo vai a {mi(nac['saldo_df'])}. São os números "
            "nacionais do capítulo, agora com endereço.",
            "inferencia",
        )
        + '<aside class="hyp"><b>Hipótese da matriz</b>'
        f"A linha de cada candidatura é nacional (Nexus, p. 79: eleitorado de Renan com Flávio {pub['Renan']['Flávio']} e Lula "
        f"{pub['Renan']['Lula']}; Zema {pub['Zema']['Flávio']} e {pub['Zema']['Lula']}; Cury {pub['Cury']['Flávio']} e "
        f"{pub['Cury']['Lula']}; Caiado {pub['Caiado']['Flávio']} e {pub['Caiado']['Lula']}) e é aplicada a cada município "
        "como se o eleitor de Cury em Salvador votasse como o de Cury em Joinville. Por isso o saldo por voto só muda com a "
        "composição local: onde Zema e Renan pesam mais, rende mais; onde Caiado pesa, rende menos. As duas medições de "
        f"Caiado discordam de lado, e em Goiás, onde ele tem {pc(co['caiado_goias']['pct_estoque_go'])} do estoque, a escolha "
        "da linha decide o sinal.</aside>"
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
        f"Em {inteiro(nac['municipios_vao_positivo'])} municípios um nome do lado de Flávio, ao governo ou ao Senado, teve "
        f"mais votos que ele, somando {mi(nac['vao_positivo'])} acima dele; {pc(100 * ne['vao_positivo'] / nac['vao_positivo'])} "
        f"desse vão está no Nordeste. Sem os governadores eleitos que não declararam apoio a Flávio, {_sem_apoio(D)}, "
        f"o vão é de {mi(nac['vao_positivo_sem_governador_sem_apoio'])}. "
        f"Somado à terceira via, o teto endereçável local chega a {mi(nac['teto'])}: rótulo obrigatório, teto endereçável, "
        "não previsão.",
        "verificado",
    )
    return h


def _prioridade(D: dict, fig: Callable[[str], str]) -> str:
    P = D["prioridade"]
    soma = P["soma_top"]
    pesos = P["pesos"]
    h = (
        '<aside class="juizo"><b>Juízo editorial: os pesos do índice</b>'
        f"Prioridade = votos de terceira via × fator de conversão. O fator é a média ponderada da posição do município entre "
        f"os 5.571 em quatro variáveis: vão local {num(pesos['vao_local'], 2)}, matriz por nome {num(pesos['matriz'], 2)}, "
        f"Bolsonaro no 2º turno de 2022 {num(pesos['ambiente_2022'], 2)} e margem de Flávio no 1º turno "
        f"{num(pesos['margem'], 2)}. O vão local pesa mais porque é a única evidência medida no próprio município; a margem "
        "pesa menos porque repete em parte o ambiente de 2022.</aside>"
    )
    h += fig("terceira_via_prioridade")
    reg = ", ".join(f"{r} {soma['por_regiao'][r]}" for r in REGIOES)
    pcl = soma["por_classe"]
    h += p(
        f"Os 100 primeiros somam {mi(soma['estoque'])} de terceira via e saldo esperado de {mi(soma['saldo'])} pela matriz "
        f"Nexus ({mi(soma['saldo_df'])} com o Datafolha em Cury e Caiado): {pc(soma['saldo_sobre_diferenca_pct'])} da "
        f"diferença de {mi(P['diferenca_nacional'])} do 1º turno. A parte que a matriz manda para branco, nulo ou indecisão "
        f"nesses 100 é de {mi(soma['fora'])}, e é a que a militância pode disputar. Por região: {reg}. Por classe: "
        f"{pcl['venceu_folga']} onde Flávio venceu com folga, {pcl['venceu_apertado']} apertado, {pcl['perdeu_apertado']} "
        f"onde perdeu apertado e {pcl['perdeu_folga']} onde perdeu com folga; {soma['capitais']} são capitais.",
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
    menor = min(s["em_comum_com_central"] for s in P["sensibilidade"])
    so_vao = next(s for s in P["sensibilidade"] if s["nome"] == "vao_local")
    h += p(
        f"Sem os pesos da casa a lista muda pouco: qualquer das três ordens alternativas mantém pelo menos {menor} dos 100. "
        f"O volume manda, e o fator reordena dentro dele. A ordem só pelo vão local é a que mais muda: leva "
        f"{so_vao['por_regiao']['Nordeste']} municípios do Nordeste aos 100, contra {soma['por_regiao']['Nordeste']} no índice.",
        "inferencia",
    )
    return h


def _regioes(D: dict) -> str:
    leit = X.leituras_regionais(D)
    juizo = X.juizo_regional(D)
    h = "".join(
        p(f"<b>{r}.</b> {escape(leit[r])}", "inferencia")
        for r in ("Nordeste", "Sudeste", "Sul", "Centro-Oeste", "Norte")
    )
    h += (
        '<aside class="juizo"><b>Juízo editorial: o que fazer em cada região</b><ul>'
        + "".join(
            f"<li><strong>{r}:</strong> {escape(juizo[r])}</li>"
            for r in ("Nordeste", "Sudeste", "Sul", "Centro-Oeste", "Norte")
        )
        + "</ul></aside>"
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
    return (
        p(
            f"{pc(ri['concentracao']['capitais_ou_grandes_parcela'])} do estoque está em capitais e cidades grandes, onde a "
            "militância de rua rende menos por hora e a mídia, as redes e o palanque rendem mais.",
            "juizo",
        )
        + f"<p>{rotulo('inferencia')} <span class=\"selo selo-contrario\">Achado contrário</span> Onde Lula venceu com folga ficam "
        f"{mi(ri['lula_com_folga']['estoque'])}, {pc(ri['lula_com_folga']['parcela'])} do estoque. Pela matriz nacional, ali "
        f"cada voto rende quase o mesmo que no país ({num(ri['lula_com_folga']['saldo_por_voto'], 3)} contra "
        f"{num(D['agregados']['brasil']['saldo_por_voto'], 3)}), porque a matriz não "
        f"sabe onde o eleitor mora. A urna de 2022 sabe: nesses municípios, cada voto de terceira via do 1º turno rendeu saldo "
        f"de {num(conv['perdeu_folga']['saldo'], 2)} a Bolsonaro entre os turnos, contra {num(conv['venceu_folga']['saldo'], 2)} "
        f"onde Flávio venceu com folga em 2026 (razão simples, analogia de uma eleição){_regressao(D)}. O trabalho ali rende "
        "menos por voto. Nas nove capitais do Nordeste Lula fez "
        f"{num(-nc['margem_pp'], 2)} pontos sobre Flávio, e a terceira via soma {mi(nc['estoque'])}, com {mi(nc['caiado'])} de "
        "Caiado, cuja linha Nexus dá mais a Lula que a Flávio.</p>"
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
        return f"Sem disputa estadual, o branco e nulo caiu nos cinco grupos de municípios, e {tendencia}"
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
        f"dos votantes, {inteiro(nac['acrescimo'])} votos a mais. A terceira via de 2022 tinha {mi(nac['terceira_via_2022'])}: "
        f"o branco e nulo novo equivale a {pc(100 * nac['taxa'], 1)} dela. Fonte: detalhe por seção do TSE, conferido com o "
        "arquivo nacional de 2022.",
        "verificado",
    )
    h += fig("nulo_2022_municipios")
    quintos = ", ".join(sp(q["delta_pp"], 2) for q in sg["quintis_terceira_via"])
    h += p(
        f"O aumento foi onde havia 2º turno de governador: {sp(cg['delta_pp'], 2)} ponto nas {len(cg['ufs'])} UFs com disputa "
        f"estadual ({', '.join(cg['ufs'])}) e {sp(sg['delta_pp'], 2)} nas outras {len(sg['ufs'])}. Controlando pela terceira "
        f"via, o 2º turno estadual soma {num(mod['c_governador'], 2)} ponto ao aumento, e cada ponto de terceira via, "
        f"{num(mod['b_terceira_via'], 3)}. {_quintos_frase(sg)} (do quinto de municípios com menos terceira via ao de "
        f"mais: {quintos}).",
        "inferencia",
    )
    h += (
        '<aside class="hyp"><b>Hipótese, não achado</b>'
        "O eleitor que volta à urna pelo governador e não escolhe presidente explicaria a diferença. Em 2026 há 2º turno "
        f"estadual em {', '.join(rk['ufs'])}, com {inteiro(rk['comparecimento'])} votantes no 1º turno; pela taxa de 2022, "
        f"{mi(rk['votos'])} estão em risco de virar branco ou nulo; {pc(X.parcela_rio(N))} desses votantes estão no Rio de "
        "Janeiro. A matriz Nexus manda "
        f"{mi(fora)} da terceira via para branco, nulo ou indecisão; a urna de 2022 sugere que boa parte disso escolhe um "
        "lado ou falta, e que o risco maior de nulo está onde há outra disputa na cédula.</aside>"
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
    h += p(
        "A terceira via de 2022 era outra (Simone Tebet e Ciro Gomes). O acervo da casa tem só as últimas ondas de 1º turno de "
        "2022 (data/originals/pesquisas_2022/); não há ali pesquisa de 2º turno com o cruzamento pelo voto em Tebet ou Ciro, e "
        "nenhuma foi usada.",
        "verificado",
    )
    return h


def _limites() -> str:
    itens = [
        "A matriz de transferência é nacional e aplicada localmente: hipótese declarada, não medição por município.",
        "Vão local e teto são mesma urna e cargos diferentes: não dizem quem votou em quem, e o governador sem apoio "
        "declarado a Flávio é teto, não palanque.",
        "2022 é uma eleição só, com outra terceira via e outro mapa de 2º turno estadual.",
        "Os pesos do índice são juízo editorial; as sensibilidades estão ao lado.",
        "Nada aqui é previsão do 2º turno.",
    ]
    return (
        "<details><summary>Limites deste bloco</summary><ul>"
        + "".join(f"<li>{i}</li>" for i in itens)
        + "</ul></details>"
    )


def bloco(D: dict, fig: Callable[[str], str]) -> str:
    """HTML completo do bloco, na ordem: estoque, matriz, direita local, prioridade, regiões, contrário, nulo."""
    return (
        _estoque(D, fig)
        + _matriz(D)
        + _direita_local(D, fig)
        + _prioridade(D, fig)
        + _regioes(D)
        + _contrario(D)
        + (PR.bloco(D, fig) if "reguas" in D else "")
        + _nulo(D, fig)
        + _limites()
    )
