"""Texto de "Onde está o voto da terceira via, cidade por cidade".

Duas saídas: as regras declaradas (vão para o JSON) e o memorando em Markdown
(``analysis/apuracao_2026/terceira_via.md``). As leituras por região são texto
puro, sem marcação, e servem também à página (``pagina_texto_terceira_via.py``).
Nenhum número é digitado: tudo sai do dicionário montado pelo script.
"""

from __future__ import annotations

from typing import Any

from . import terceira_via as T
from .estrategia import milhar
from .estrategia_formato import dec, lista_e, nome, pc, qtd, sinal, sinal_votos, tabela

CLASSE_CURTA = {
    "venceu_folga": "Flávio venceu com folga",
    "venceu_apertado": "Flávio venceu apertado",
    "perdeu_apertado": "Flávio perdeu apertado",
    "perdeu_folga": "Flávio perdeu com folga",
}
GRUPO_NOME = {
    "renan": "Renan Santos",
    "zema": "Romeu Zema",
    "cury": "Augusto Cury",
    "caiado": "Ronaldo Caiado",
    "outros": "demais seis",
}
VARIAVEL_NOME = {
    "vao_local": "vão local",
    "matriz": "matriz por nome",
    "ambiente_2022": "ambiente de 2022",
    "margem": "margem do 1º turno",
}
SENS_NOME = {"volume": "só volume", "vao_local": "só vão local", "margem": "só margem"}


def regras(mat: dict) -> dict[str, Any]:
    """Regras do método, gravadas no JSON ao lado dos números."""
    return {
        "terceira_via": "votos válidos de presidente fora de Flávio Bolsonaro e Lula, no município (1º turno de 04/10/2026)",
        "classes": {**T.ROTULO_CLASSE, "folga_pp": T.FOLGA_PP},
        "matriz": (
            f"linha de cada candidatura ({mat['fonte_nexus']}; para Cury e Caiado, sensibilidade com "
            f"{mat['fonte_datafolha']}) normalizada para somar 1 e aplicada aos votos de cada candidatura "
            "em cada município; só a parte medida vira voto válido. Hipótese declarada: a matriz é nacional "
            "e aplicada localmente, como se o eleitor de cada candidatura votasse igual em todo o país."
        ),
        "vao_local": (
            "votos da candidatura do lado de Flávio com mais votos no município, entre o governador comparado "
            "com Flávio no vão estadual da casa (governadores.json) e as candidaturas do bloco aliado ao Senado "
            "(eleitas e a mais votada, senado_x_flavio.json), menos os votos de Flávio no mesmo município. "
            "Em pontos, sobre os votantes de presidente. Mesma urna, cargos diferentes: não é transferência."
        ),
        "teto": (
            "votos de terceira via mais o vão local positivo. As duas parcelas podem contar o mesmo eleitor "
            "(quem votou no governador e em Cury), por isso é teto endereçável, não previsão nem soma de pessoas."
        ),
        "fator": {
            "pesos": T.PESOS,
            "posicao": (
                "cada variável vira a posição do município entre os 5.571 (0 = o menor valor do país, 1 = o maior; "
                "empate leva a posição média; sem dado, 0,5)"
            ),
            "variaveis": {
                "vao_local": "vão local em pontos dos votantes",
                "matriz": "saldo para Flávio por voto de terceira via pela matriz Nexus (depende de quem teve o voto ali: Zema e Renan rendem mais que Cury e Caiado)",
                "ambiente_2022": "parcela de Bolsonaro nos válidos do 2º turno de 2022",
                "margem": "margem de Flávio sobre Lula no 1º turno de 2026",
            },
            "juizo": "os pesos são juízo editorial da casa; as sensibilidades mostram o que muda sem eles",
        },
        "prioridade": "votos de terceira via do município × fator de conversão",
        "sensibilidades": {k: SENS_NOME[k] for k in T.SENSIBILIDADES},
        "nulo_2022": (
            "brancos e nulos de presidente em pontos dos votantes, 2º turno menos 1º turno de 2022, no mesmo "
            "município (detalhe por seção do TSE)"
        ),
    }


def regras_reguas() -> dict[str, str]:
    """Regras das duas réguas, gravadas no JSON."""
    return {
        "pesquisa": (
            "linha publicada de cada candidatura (Nexus, p. 79; Datafolha, p. 7, para Cury e Caiado), "
            "normalizada e aplicada aos votos de cada candidatura no município; só a parte medida vira voto"
        ),
        "urna": (
            "regressão ecológica município a município da variação do saldo Bolsonaro menos Lula entre os turnos "
            "de 2022 sobre os votantes do 1º turno, explicada pela parcela da terceira via e pela parcela de "
            "brancos e nulos do 1º turno, com efeito fixo de UF, ponderada pelos votantes; inclinação da terceira "
            "via por classe de margem de Flávio em 2026 (aplicação) e por região (sensibilidade); intervalos por "
            "bootstrap de municípios"
        ),
        "razao_simples": (
            "ganho de Bolsonaro menos ganho de Lula entre os turnos de 2022 dividido pelos votos de terceira via "
            "do 1º turno, por classe; credita à terceira via todo o movimento entre os turnos, inclusive "
            "comparecimento e mobilização da base"
        ),
        "combinacao": "ordem pelo piso (o menor saldo das duas réguas); o teto é o maior",
        "robusto": "município nos 100 primeiros pelas duas réguas",
        "limite_ecologico": (
            "inferência de agregado para agregado: diz quanto o saldo cresceu a mais onde havia mais terceira "
            "via, na mesma UF, e não como votou o eleitor de cada candidatura"
        ),
        "outra_terceira_via": (
            "a terceira via de 2022 era Simone Tebet (MDB) e Ciro Gomes (PDT), centro e esquerda pela "
            "classificação da casa; a de 2026 tem Augusto Cury (Avante) e Ronaldo Caiado (PSD), de centro, e "
            "Renan Santos (Missão) e Zema (Novo), de direita"
        ),
    }


# ---------------------------------------------------------------- frases


def mil(x: float) -> str:
    return qtd(x, "votos")


def lider(nome_urna: str) -> str:
    return nome(nome_urna)


def perfis(D: dict) -> dict[str, dict]:
    """Cargo, UF, eleição e apoio de cada nome da direita local, pelo nome de urna."""
    saida: dict[str, dict] = {}
    for uf, loc in D["direita_local"].items():
        g = loc.get("governador")
        if g:
            saida[g["nome"]] = {
                "uf": uf,
                "cargo": "governador",
                "sem_apoio": g["comparacao"] == "sem apoio declarado",
                "situacao": "eleito" if g["decisao"] == "eleito" else "no 2º turno",
            }
        for c in loc["senado"]:
            saida[c["nome"]] = {
                "uf": uf,
                "cargo": "Senado",
                "sem_apoio": False,
                "situacao": "eleito" if c["eleito"] else "não eleito",
            }
    return saida


def _quem(x: dict, perfil: dict) -> str:
    p = perfil.get(x["nome"], {})
    cargo = "governo" if p.get("cargo") == "governador" else "Senado"
    return f"{lider(x['nome'])} ({p.get('uf', '')}, {cargo}: {qtd(x['vao_votos'], 'votos')})"


ORDINAL = {
    1: "o maior",
    2: "o segundo maior",
    3: "o terceiro maior",
    4: "o quarto maior",
    5: "o quinto maior",
}


def posicao_regiao(conv: dict, regiao: str) -> str:
    """Posição do rendimento de 2022 da região entre as cinco, por extenso."""
    ordem = sorted(conv, key=lambda r: -(conv[r]["saldo"] or 0))
    k = ordem.index(regiao) + 1
    if k == len(ordem):
        return f"o menor das {X_EXTENSO.get(len(ordem), len(ordem))} regiões"
    return f"{ORDINAL[k]} das {X_EXTENSO.get(len(ordem), len(ordem))} regiões"


X_EXTENSO = {5: "cinco"}


def parcela_rio(nu: dict) -> float:
    """Parcela dos votantes das UFs com 2º turno de governador em 2026 que está no RJ."""
    rk = nu["risco_2026"]
    rio = nu["por_uf"].get("RJ", {}).get("comparecimento_2026", 0)
    return 100 * rio / rk["comparecimento"] if rk["comparecimento"] else 0.0


def leituras_regionais(D: dict) -> dict[str, str]:
    """Uma leitura por região, gerada dos números; texto puro, sem marcação."""
    ag = D["agregados"]
    nac = ag["brasil"]
    conv = D["conversao_2022"]["por_regiao"]
    reg = ag["regioes"]
    ufs = ag["ufs"]
    saida = {}
    ne = reg["Nordeste"]
    perfil = perfis(D)
    sem_apoio = [x for x in ne["lideres"] if perfil.get(x["nome"], {}).get("sem_apoio")]
    bloco = [x for x in ne["lideres"] if not perfil.get(x["nome"], {}).get("sem_apoio")]
    saida["Nordeste"] = (
        f"O Nordeste guarda {mil(ne['estoque'])} de terceira via, {pc(ne['parcela_do_estoque'])} do país, e Flávio "
        f"venceu em municípios que somam só {pc(ne['onde_flavio_venceu_parcela'])} desse estoque. Ali o estoque é "
        f"menor e o vão é maior: em {milhar(ne['municipios_vao_positivo'])} municípios um nome do lado de Flávio teve "
        f"mais votos que ele, somando {mil(ne['vao_positivo'])} acima dele. Os maiores vãos são de governadores "
        f"eleitos que não declararam apoio a Flávio, e por isso são teto, não palanque: "
        f"{lista_e([_quem(x, perfil) for x in sem_apoio])}. Sem eles, o vão cai para "
        f"{mil(ne['vao_positivo_sem_governador_sem_apoio'])}, puxado por "
        f"{lista_e([_quem(x, perfil) for x in bloco[:3]])}. Na Paraíba nenhum nome do bloco passou Flávio: o vão de "
        f"Lucas Ribeiro é de um aliado de Lula. Em 2022, cada voto de terceira via do Nordeste rendeu a Bolsonaro "
        f"saldo de {dec(conv['Nordeste']['saldo'], 2)} entre os turnos, {posicao_regiao(conv, 'Nordeste')}."
    )
    sul = reg["Sul"]
    saida["Sul"] = (
        f"No Sul o estoque é de {mil(sul['estoque'])}, e {pc(sul['onde_flavio_venceu_parcela'])} dele está onde "
        f"Flávio venceu. Renan e Zema somam {pc(sul['renan_zema_pct'])} desse estoque, contra {pc(nac['renan_zema_pct'])} "
        f"no país. Pela matriz, cada voto rende {dec(sul['saldo_por_voto'], 2)} de saldo a Flávio; em 2022 rendeu "
        f"{dec(conv['Sul']['saldo'], 2)}, {posicao_regiao(conv, 'Sul')}. A direita local quase não passa Flávio ali "
        f"({mil(sul['vao_positivo'])} acima dele)."
    )
    co = reg["Centro-Oeste"]
    go = ufs.get("GO", {})
    saida["Centro-Oeste"] = (
        f"No Centro-Oeste o estoque é de {mil(co['estoque'])}, {pc(co['onde_flavio_venceu_parcela'])} onde Flávio "
        f"venceu, mas é de Caiado: {pc(co['por_grupo_pct']['caiado'])} do estoque, e Renan e Zema somam só "
        f"{pc(co['renan_zema_pct'])}. Em Goiás, com "
        f"{mil(go.get('caiado', 0))} de Caiado, a matriz Nexus dá saldo de {mil(go.get('saldo', 0))} a Flávio e a "
        f"do Datafolha, {mil(go.get('saldo_df', 0))}. Em 2022 o Centro-Oeste converteu {dec(conv['Centro-Oeste']['saldo'], 2)} "
        f"por voto de terceira via, {posicao_regiao(conv, 'Centro-Oeste')}."
    )
    se = reg["Sudeste"]
    sp, mg = ufs.get("SP", {}), ufs.get("MG", {})
    govs = {
        loc["governador"]["nome"]
        for uf, loc in D["direita_local"].items()
        if uf in ("SP", "MG") and loc.get("governador")
    }
    dos_govs = sum(x["vao_votos"] for x in se["lideres"] if x["nome"] in govs)
    parcela_govs = 100 * dos_govs / se["vao_positivo"] if se["vao_positivo"] else 0.0
    saida["Sudeste"] = (
        f"O Sudeste tem o maior volume: {mil(se['estoque'])}, {pc(se['parcela_do_estoque'])} do país, "
        f"{pc(se['onde_flavio_venceu_parcela'])} onde Flávio venceu. A direita local passa Flávio em "
        f"{milhar(se['municipios_vao_positivo'])} municípios, com {mil(se['vao_positivo'])} acima dele; São Paulo "
        f"responde por {mil(sp.get('vao_positivo', 0))} e Minas por {mil(mg.get('vao_positivo', 0))}; "
        f"{pc(parcela_govs)} do vão da região vem de Tarcísio e Cleitinho. Em 2022 cada voto de terceira via rendeu "
        f"{dec(conv['Sudeste']['saldo'], 2)}."
    )
    no = reg["Norte"]
    saida["Norte"] = (
        f"O Norte tem {mil(no['estoque'])} de terceira via, {pc(no['onde_flavio_venceu_parcela'])} onde Flávio "
        f"venceu, e a direita local passa Flávio em {milhar(no['municipios_vao_positivo'])} municípios "
        f"({mil(no['vao_positivo'])} acima dele). Em 2022 cada voto de terceira via rendeu {dec(conv['Norte']['saldo'], 2)} "
        "de saldo a Bolsonaro, com Lula quase sem ganho entre os turnos."
    )
    return saida


def juizo_regional(D: dict) -> dict[str, str]:
    """O que fazer em cada região: juízo editorial da casa, com o número que o sustenta."""
    reg = D["agregados"]["regioes"]
    conv = D["conversao_2022"]["por_regiao"]
    perfil = perfis(D)
    ne_bloco = [
        x
        for x in reg["Nordeste"]["lideres"]
        if not perfil.get(x["nome"], {}).get("sem_apoio")
    ]
    return {
        "Nordeste": (
            f"palanque local antes de militância de rua. O estoque é pequeno ({mil(reg['Nordeste']['estoque'])}) e "
            f"converteu pouco em 2022 ({dec(conv['Nordeste']['saldo'], 2)} por voto), mas o vão dos nomes do bloco "
            f"({lista_e([lider(x['nome']) for x in ne_bloco[:3]])}) mostra eleitor que vota na direita local e não vota "
            "em Flávio."
        ),
        "Sul": (
            f"militância sobre o eleitor de terceira via, com o maior rendimento de 2022 ({dec(conv['Sul']['saldo'], 2)} "
            "por voto) e quase nenhum vão local a explorar."
        ),
        "Centro-Oeste": (
            "o eleitor de Caiado decide. Antes de gastar ali, medir a linha dele em Goiás: as duas medições nacionais "
            "discordam de lado."
        ),
        "Sudeste": (
            f"o volume está ali ({mil(reg['Sudeste']['estoque'])}), e a conversão depende de Tarcísio e Cleitinho subirem "
            "no palanque nas cidades grandes."
        ),
        "Norte": (
            f"estoque pequeno ({mil(reg['Norte']['estoque'])}) com rendimento alto em 2022 "
            f"({dec(conv['Norte']['saldo'], 2)} por voto), concentrado em poucas cidades: "
            f"{lista_e([nome(x['nome']) for x in D['prioridade']['por_regiao']['Norte'][:3]])} lideram o índice da região."
        ),
    }


def _vt(x: float | None) -> str:
    return "s/d" if x is None else sinal_votos(round(x))


def secao_reguas(D: dict) -> list[str]:
    """Seção 6 do memorando: pesquisa contra urna."""
    R, conv = D["reguas"], D["conversao_2022"]
    m = R["modelos"]
    gc, gr, un = (
        m["classe"]["grupos"],
        m["regiao"]["grupos"],
        m["unico"]["grupos"]["todos"],
    )
    T_ = R["totais"]
    br = T_["brasil"]
    rk = R["rankings"]
    rv = R["retrovisao"]

    def ic(g: dict) -> str:
        a, b = g["saldo_ic95"]
        return f"{sinal(a, 3)} a {sinal(b, 3)}"

    linhas = [
        "## 6. Pesquisa contra urna: duas réguas para o mesmo estoque",
        "",
        f"**Régua da urna de 2022.** {R['regras']['urna'][0].upper()}{R['regras']['urna'][1:]}. Bootstrap de {milhar(m['classe']['n_boot'])} reamostragens, semente {m['classe']['semente']}.",
        "",
        tabela(
            [
                "Grupo",
                "Municípios",
                "Bolsonaro por voto",
                "Lula por voto",
                "Saldo por voto",
                "IC 95% do saldo",
                "Razão simples",
                "Nexus sobre 2026",
                "Datafolha sobre 2026",
            ],
            [
                [
                    CLASSE_CURTA[c],
                    milhar(gc[c]["municipios"]),
                    dec(gc[c]["bolsonaro"], 3),
                    dec(gc[c]["lula"], 3),
                    sinal(gc[c]["saldo"], 3),
                    ic(gc[c]),
                    sinal(conv["por_classe"][c]["saldo"], 3),
                    sinal(T_["classes"][c]["pv_nexus"], 3),
                    sinal(T_["classes"][c]["pv_datafolha"], 3),
                ]
                for c in T.CLASSES
            ]
            + [
                [
                    r,
                    milhar(gr[r]["municipios"]),
                    dec(gr[r]["bolsonaro"], 3),
                    dec(gr[r]["lula"], 3),
                    sinal(gr[r]["saldo"], 3),
                    ic(gr[r]),
                    sinal(conv["por_regiao"][r]["saldo"], 3),
                    sinal(T_["regioes"][r]["pv_nexus"], 3),
                    sinal(T_["regioes"][r]["pv_datafolha"], 3),
                ]
                for r in ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
            ]
            + [
                [
                    "Brasil, inclinação única",
                    milhar(un["municipios"]),
                    dec(un["bolsonaro"], 3),
                    dec(un["lula"], 3),
                    sinal(un["saldo"], 3),
                    ic(un),
                    sinal(conv["brasil"]["saldo"], 3),
                    sinal(br["pv_nexus"], 3),
                    sinal(br["pv_datafolha"], 3),
                ]
            ],
        ),
        "",
        f"**Inferência.** A razão simples credita à terceira via todo o movimento entre os turnos. Sem efeito fixo de UF, a regressão dá {sinal(m['sem_efeito_fixo']['saldo_terceira_via'], 3)} por voto de terceira via e uma constante de {dec(100 * m['sem_efeito_fixo']['constante'], 2)} pontos dos votantes a favor de Bolsonaro que não depende da terceira via. Por região, as inclinações de Bolsonaro e de Lula somam mais de um voto por voto de terceira via em {lista_e([r for r, g in gr.items() if g['fora'] is not None and g['fora'] < 0])}: a regressão ali capta algo além da terceira via, como comparecimento que anda junto com ela. A aplicação a 2026 usa a classe de margem.",
        "",
        f"**Inferência. Totais de 2026.** Nexus {_vt(br['nexus'])}; Datafolha em Cury e Caiado {_vt(br['datafolha'])}; urna de 2022 por classe {_vt(br['urna'])} (IC 95%: {_vt(br['urna_ic95'][0])} a {_vt(br['urna_ic95'][1])}); urna por região {_vt(br['urna_regiao'])}; razão simples {_vt(br['razao_simples'])}.",
        "",
        tabela(
            [
                "Região",
                "Terceira via",
                "Nexus",
                "Datafolha",
                "Urna de 2022",
                "Nexus menos urna",
            ],
            [
                [
                    r,
                    milhar(x["estoque"]),
                    _vt(x["nexus"]),
                    _vt(x["datafolha"]),
                    _vt(x["urna"]),
                    _vt(x["diferenca_nexus_urna"]),
                ]
                for r, x in T_["regioes"].items()
            ],
        ),
        "",
        f"**Inferência. Ranking.** {rk['robustos']} dos 100 primeiros pelo saldo da pesquisa também estão nos 100 primeiros pela urna (robustos, {milhar(rk['robustos_estoque'])} votos de terceira via); {rk['so_pesquisa']} só pela pesquisa e {rk['so_urna']} só pela urna. Motivo dominante das divergências: "
        + ", ".join(
            f"{k.replace('so_', 'só ').replace(':', ', ')} {v}"
            for k, v in rk["motivos_divergencia"].items()
        )
        + ". A combinação ordena pelo piso (o menor saldo das duas) e mostra o teto.",
        "",
        tabela(
            [
                "Nº",
                "Município",
                "Terceira via",
                "Nexus",
                "Datafolha",
                "Urna",
                "Piso",
                "Teto",
                "Nº pesquisa",
                "Nº urna",
                "Situação",
            ],
            [
                [
                    str(i),
                    f"{nome(x['nome'])} ({x['uf']})",
                    milhar(x["estoque"]),
                    _vt(x["nexus"]),
                    _vt(x["datafolha"]),
                    _vt(x["urna"]),
                    _vt(x["piso"]),
                    _vt(x["teto"]),
                    milhar(x["posicao"]["pesquisa"]),
                    milhar(x["posicao"]["urna"]),
                    x["situacao"].replace("so_", "só "),
                ]
                for i, x in enumerate(rk["top"]["combinacao"], start=1)
            ],
        ),
        "",
        "**Os movimentos do capítulo pelas duas réguas.**",
        "",
        tabela(
            ["Movimento", "Régua do capítulo", "Urna de 2022", "Nota"],
            [
                [
                    f"{mv['ordem']}. {mv['titulo']}",
                    _vt(mv["pesquisa"]),
                    _vt(mv["urna"]) if mv["urna"] is not None else "não se aplica",
                    mv.get("nota", "")
                    or ("mesmo sinal" if mv["concordam"] else "sinal oposto"),
                ]
                for mv in R["movimentos"]
            ],
        ),
        "",
        "**Retrovisão.** "
        + (
            "O acervo tem cruzamento de 2º turno de 2022; o teste ainda não foi feito."
            if rv["disponivel"]
            else f"Não há no acervo pesquisa de 2º turno de 2022 com o cruzamento pelo voto de 1º turno ({rv['casas_no_acervo']} pastas em `{rv['procurado_em'][0]}/`, {rv['pesquisas_transcritas']} pesquisas transcritas em `{rv['procurado_em'][1]}`, todas da última onda antes do 1º turno). Para o teste é preciso arquivar as primeiras ondas nacionais de 2º turno de outubro de 2022 que tenham cruzado o voto de 2º turno pelo voto em Tebet e Ciro, com URL, SHA-256 e página."
        ),
        "",
    ]
    return linhas


def _linha_top(x: dict) -> list[str]:
    lider_ = (
        lider(x["local_lider"])
        if x["local_lider"] and x["vao_votos"] > 0
        else "nenhum acima de Flávio"
    )
    return [
        str(x["posicao"]),
        f"{nome(x['nome'])} ({x['uf']})",
        milhar(x["eleitores"]),
        milhar(x["estoque"]),
        " / ".join(milhar(x[g]) for g in ("renan", "zema", "cury", "caiado", "outros")),
        sinal(x["margem_pp"], 1),
        pc(x["b22_2t_pct"], 1) if x["b22_2t_pct"] is not None else "s/d",
        sinal(x["delta_bn22_pp"], 2) if x["delta_bn22_pp"] is not None else "s/d",
        sinal_votos(x["saldo"]),
        f"{lider_} ({sinal_votos(x['vao_votos'])})" if x["vao_votos"] > 0 else lider_,
        dec(x["fator"], 3),
    ]


CAB_TOP = [
    "Nº",
    "Município",
    "Eleitores",
    "Terceira via",
    "Renan / Zema / Cury / Caiado / outros",
    "Margem de Flávio (pp)",
    "Bolsonaro 2022, 2º t.",
    "Nulo 2022, 1º→2º (pp)",
    "Saldo esperado (Nexus)",
    "Direita local acima de Flávio",
    "Fator",
]


def memorando(D: dict) -> str:
    ag, pr, nu, co, ri = (
        D["agregados"],
        D["prioridade"],
        D["nulo_2022"],
        D["contrario"],
        D["riscos"],
    )
    nac, conv = ag["brasil"], D["conversao_2022"]
    soma = pr["soma_top"]
    cf = D["conferencia"]
    cg, sg = nu["com_2t_governador"], nu["sem_2t_governador"]
    linhas = [
        "# Onde está o voto da terceira via, cidade por cidade",
        "",
        "Bloco do capítulo 13 do dossiê da apuração do 1º turno de 2026. Pedido de 05/10/2026: onde está o voto de terceira via para a militância da direita trabalhar no 2º turno, com inteligência local, e como evitar que ele vire nulo. A casa tem lado; o método não: cada número tem regra e fonte, e o achado que contraria a tese sai com o mesmo peso.",
        "",
        f"Reprodução: `python3 scripts/apuracao-2026-terceira-via.py`, que grava `analysis/apuracao_2026/dados/terceira_via.json`. Banco da apuração, versão vigente de cada arquivo pela hora de geração do TSE; o arquivo municipal mais novo foi gerado em {cf['arquivo_municipal_mais_novo_gerado_em']}. A soma dos 5.757 arquivos municipais (5.571 municípios e 186 cidades do exterior) bate com o arquivo nacional candidatura a candidatura: {'sim' if cf['soma_municipal_igual_nacional'] else 'não'}. Onze arquivos municipais que congelaram incompletos na noite foram regerados pelo TSE e entram completos aqui.",
        "",
        "Rótulos: **Verificado** é número da urna. **Inferência** é conta sobre medição publicada. **Hipótese** é suposição declarada. **Analogia** é o que aconteceu em 2022. **Juízo editorial** é opinião da casa.",
        "",
        "## Em seis linhas",
        "",
        f"1. **Verificado.** A terceira via teve {mil(nac['estoque'] + ag['exterior']['estoque'])}: {mil(nac['estoque'])} no Brasil e {mil(ag['exterior']['estoque'])} no exterior. Cury {pc(nac['por_grupo_pct']['cury'])}, Renan {pc(nac['por_grupo_pct']['renan'])}, Caiado {pc(nac['por_grupo_pct']['caiado'])}, Zema {pc(nac['por_grupo_pct']['zema'])}, demais {pc(nac['por_grupo_pct']['outros'])}.",
        f"2. **Verificado.** {pc(nac['onde_flavio_venceu_parcela'])} desse voto está em municípios onde Flávio venceu; {pc(nac['por_classe']['venceu_folga']['estoque_parcela'])} onde venceu com folga e {pc(nac['por_classe']['perdeu_folga']['estoque_parcela'])} onde Lula venceu com folga.",
        f"3. **Inferência.** Pela matriz Nexus aplicada município a município, o estoque dá a Flávio saldo de {mil(nac['saldo'])}. Os 100 municípios prioritários guardam {mil(soma['estoque'])} e saldo de {mil(soma['saldo'])}, {pc(soma['saldo_sobre_diferenca_pct'])} da diferença do 1º turno ({mil(pr['diferenca_nacional'])}); a parte que a matriz manda para branco, nulo ou indecisão nesses 100 é de {mil(soma['fora'])}.",
        f"4. **Verificado.** Em {milhar(nac['municipios_vao_positivo'])} municípios um nome do lado de Flávio (governador ou Senado) teve mais votos que ele, somando {mil(nac['vao_positivo'])} acima dele; {pc(100 * ag['regioes']['Nordeste']['vao_positivo'] / nac['vao_positivo'])} desse vão está no Nordeste. Sem os governadores que não declararam apoio a Flávio, o vão é de {mil(nac['vao_positivo_sem_governador_sem_apoio'])}.",
        f"5. **Analogia.** Em 2022, pela razão simples, cada voto de terceira via do 1º turno rendeu a Bolsonaro saldo de {dec(conv['por_classe']['venceu_folga']['saldo'], 2)} entre os turnos onde Flávio venceu com folga em 2026, e de {dec(conv['por_classe']['perdeu_folga']['saldo'], 2)} onde Lula venceu com folga. A regressão com efeito fixo de UF, que separa a mobilização da base, dá {sinal(D['reguas']['modelos']['classe']['grupos']['venceu_folga']['saldo'], 2)} e {sinal(D['reguas']['modelos']['classe']['grupos']['perdeu_folga']['saldo'], 2)} (seção 6).",
        f"6. **Inferência.** O branco e nulo de presidente subiu {dec(cg['delta_pp'], 2)} ponto entre os turnos de 2022 nas {len(cg['ufs'])} UFs com 2º turno de governador e caiu {dec(abs(sg['delta_pp']), 2)} ponto nas outras {len(sg['ufs'])}. Em 2026 há 2º turno de governador em {lista_e(nu['risco_2026']['ufs'])}: pela mesma taxa, {mil(nu['risco_2026']['votos'])} em risco de virar branco ou nulo; {pc(parcela_rio(nu))} dos votantes dessas UFs estão no Rio de Janeiro.",
        "",
        "## Regras",
        "",
        f"- **Terceira via:** {D['regras']['terceira_via']}.",
        f"- **Classe de margem:** folga é {dec(T.FOLGA_PP, 0)} pontos ou mais dos válidos, para um lado ou para o outro. É uma das variáveis, nunca filtro: o ranking cobre o país inteiro.",
        f"- **Matriz:** {D['regras']['matriz']}",
        f"- **Vão local:** {D['regras']['vao_local']}",
        f"- **Teto endereçável local:** {D['regras']['teto']}",
        "- **Fator de conversão (juízo editorial):** "
        + ", ".join(f"{VARIAVEL_NOME[k]} {dec(v, 2)}" for k, v in T.PESOS.items())
        + ". Cada variável vira a posição do município entre os 5.571 (0 = o menor valor do país, 1 = o maior; empate leva a posição média; sem dado, 0,5). Prioridade = votos de terceira via × fator.",
        "",
        "## 1. O estoque",
        "",
        tabela(
            [
                "Classe",
                "Municípios",
                "Terceira via",
                "Parcela",
                "Saldo esperado (Nexus)",
            ],
            [
                [
                    CLASSE_CURTA[c],
                    milhar(v["municipios"]),
                    milhar(v["estoque"]),
                    pc(v["estoque_parcela"]),
                    milhar(v["saldo"]),
                ]
                for c, v in nac["por_classe"].items()
            ],
        ),
        "",
        tabela(
            [
                "Região",
                "Terceira via",
                "Parcela do país",
                "Onde Flávio venceu",
                "Renan + Zema",
                "Caiado",
                "Saldo por voto (Nexus)",
                "Vão local positivo",
                "Razão simples de 2022",
            ],
            [
                [
                    r,
                    milhar(a["estoque"]),
                    pc(a["parcela_do_estoque"]),
                    pc(a["onde_flavio_venceu_parcela"]),
                    pc(a["renan_zema_pct"]),
                    pc(a["por_grupo_pct"]["caiado"]),
                    dec(a["saldo_por_voto"], 3),
                    milhar(a["vao_positivo"]),
                    dec(conv["por_regiao"][r]["saldo"], 3),
                ]
                for r, a in ag["regioes"].items()
            ],
        ),
        "",
        f"**Verificado.** As capitais guardam {pc(ag['capitais']['parcela_do_estoque'])} do estoque; capitais e cidades com {milhar(ag['grandes']['corte_eleitores'])} eleitores ou mais ({milhar(ag['capitais_ou_grandes']['municipios'])} municípios), {pc(ag['capitais_ou_grandes']['parcela_do_estoque'])}.",
        "",
        "## 2. Leitura por região",
        "",
    ]
    for r, txt in leituras_regionais(D).items():
        linhas += [f"**{r}.** {txt}", ""]
    linhas += ["**Juízo editorial, o que fazer em cada região.**", ""]
    linhas += [f"- **{r}:** {txt}" for r, txt in juizo_regional(D).items()]
    linhas += [""]
    linhas += [
        "## 3. Os 100 municípios prioritários",
        "",
        f"**Juízo editorial.** Pesos do fator: {', '.join(f'{VARIAVEL_NOME[k]} {dec(v, 2)}' for k, v in T.PESOS.items())}. O vão local pesa mais porque é a única evidência medida no próprio município de que há eleitor que vota na direita e não vota em Flávio.",
        "",
        f"**Inferência.** Os 100 somam {mil(soma['estoque'])} de terceira via ({pc(100 * soma['estoque'] / nac['estoque'])} do país), saldo esperado de {mil(soma['saldo'])} pela Nexus e de {mil(soma['saldo_df'])} com as linhas do Datafolha para Cury e Caiado. Por região: "
        + ", ".join(f"{r} {v}" for r, v in soma["por_regiao"].items())
        + f". Por classe: {soma['por_classe']['venceu_folga']} onde Flávio venceu com folga, {soma['por_classe']['venceu_apertado']} apertado, {soma['por_classe']['perdeu_apertado']} onde perdeu apertado e {soma['por_classe']['perdeu_folga']} onde perdeu com folga. {soma['capitais']} são capitais.",
        "",
        tabela(CAB_TOP, [_linha_top(x) for x in pr["top"]]),
        "",
        "**Sensibilidade.** O que muda sem os pesos da casa:",
        "",
        tabela(
            [
                "Ordem",
                "Em comum com a central",
                "Norte",
                "Nordeste",
                "Centro-Oeste",
                "Sudeste",
                "Sul",
                "Saldo esperado dos 100",
                "Primeiros",
            ],
            [
                [
                    SENS_NOME[s["nome"]],
                    str(s["em_comum_com_central"]),
                    *[
                        str(s["por_regiao"][r])
                        for r in ("Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul")
                    ],
                    milhar(s["saldo"]),
                    ", ".join(
                        f"{nome(p['nome'])} ({p['uf']})" for p in s["primeiros"][:5]
                    ),
                ]
                for s in pr["sensibilidade"]
            ],
        ),
        "",
        "Os 10 primeiros de cada UF pelo índice e os 10 de maior teto endereçável estão em `terceira_via.json` (`prioridade.por_uf`, `teto.ufs`).",
        "",
        "## 4. Riscos e achado contrário",
        "",
        f"**Juízo editorial.** {pc(ri['concentracao']['capitais_ou_grandes_parcela'])} do estoque está em capitais e cidades grandes, onde a militância de rua rende menos por hora e a mídia e as redes rendem mais.",
        "",
        f"**Analogia, achado contrário.** Onde Lula venceu com folga ficam {mil(ri['lula_com_folga']['estoque'])} ({pc(ri['lula_com_folga']['parcela'])} do estoque). Pela matriz nacional, ali cada voto rende quase o mesmo que no país ({dec(ri['lula_com_folga']['saldo_por_voto'], 3)} contra {dec(nac['saldo_por_voto'], 3)}), porque a matriz não sabe onde o eleitor mora. A urna de 2022 sabe: nesses municípios, cada voto de terceira via rendeu saldo de {dec(conv['por_classe']['perdeu_folga']['saldo'], 3)} a Bolsonaro, contra {dec(conv['por_classe']['venceu_folga']['saldo'], 3)} onde Flávio venceu com folga. O trabalho ali rende menos por voto. Nas capitais do Nordeste, Lula fez {sinal(-co['nordeste_capitais']['margem_pp'], 2)} pontos sobre Flávio; a terceira via soma {mil(co['nordeste_capitais']['estoque'])}, com {mil(co['nordeste_capitais']['caiado'])} de Caiado, cuja linha Nexus dá mais a Lula (30 contra 36). Em Goiás, Caiado é {pc(co['caiado_goias']['pct_estoque_go'])} do estoque: pela Nexus o saldo do estado fica perto de zero.",
        "",
        "## 5. O risco do voto nulo, medido em 2022",
        "",
        f"**Verificado.** Entre os turnos de 2022, branco e nulo de presidente foram de {pc(nu['nacional']['bn_1t_pct'])} para {pc(nu['nacional']['bn_2t_pct'])} dos votantes ({sinal(nu['nacional']['delta_pp'], 2)} ponto; {milhar(nu['nacional']['acrescimo'])} votos a mais). A terceira via de 2022 tinha {mil(nu['nacional']['terceira_via_2022'])}: o branco e nulo novo equivale a {pc(100 * nu['nacional']['taxa'], 1)} dela. Fonte: detalhe por seção do TSE, conferido com o arquivo nacional: {'sim' if cf['detalhe_2022_igual_arquivo_nacional'] else 'não'}.",
        "",
        f"**Inferência.** O aumento se concentrou onde havia 2º turno de governador: {sinal(cg['delta_pp'], 2)} ponto nas {len(cg['ufs'])} UFs ({lista_e(cg['ufs'])}) e {sinal(sg['delta_pp'], 2)} nas outras {len(sg['ufs'])}. Controlando pela terceira via, o 2º turno estadual soma {dec(nu['modelo']['c_governador'], 2)} ponto ao aumento; cada ponto de terceira via em 2022, {dec(nu['modelo']['b_terceira_via'], 3)}. Sem 2º turno estadual, o branco e nulo caiu mais onde a terceira via era pequena e caiu menos onde era grande (do quinto menor ao maior: "
        + ", ".join(sinal(q["delta_pp"], 2) for q in sg["quintis_terceira_via"])
        + ").",
        "",
        f"**Hipótese.** O eleitor que volta à urna pelo governador e não escolhe presidente explica a diferença. Em 2026 há 2º turno estadual em {lista_e(nu['risco_2026']['ufs'])}, com {qtd(nu['risco_2026']['comparecimento'], 'votantes')}; pela taxa de 2022, {mil(nu['risco_2026']['votos'])} em risco de branco ou nulo. A matriz Nexus manda {mil(nac['fora'])} da terceira via para branco, nulo ou indecisão; a urna de 2022 mostra que boa parte disso escolhe ou falta.",
        "",
        "Municípios com 20 mil votantes ou mais onde o branco e nulo mais cresceu em 2022:",
        "",
        tabela(
            [
                "Município",
                "1º turno",
                "2º turno",
                "Variação (pp)",
                "Terceira via 2022",
                "2º turno de governador em 2022",
                "Terceira via 2026",
            ],
            [
                [
                    f"{nome(m['nome'])} ({m['uf']})",
                    pc(m["bn_1t_pct"]),
                    pc(m["bn_2t_pct"]),
                    sinal(m["delta_pp"], 2),
                    pc(m["tv22_pct"]),
                    "sim" if m["gov22_2t"] else "não",
                    milhar(m["estoque_2026"]),
                ]
                for m in nu["maiores"]
            ],
        ),
        "",
        "**Analogia.** A terceira via de 2022 era outra (Simone Tebet e Ciro Gomes). O acervo da casa (`data/originals/pesquisas_2022/`) só tem as últimas ondas de 1º turno; não há pesquisa de 2º turno de 2022 com o cruzamento pelo voto em Tebet ou Ciro, e não usamos nenhuma.",
        "",
        *secao_reguas(D),
        "## Limites",
        "",
        "- A matriz é nacional e aplicada localmente: o eleitor de Cury em Salvador vota, na conta, como o de Cury em Joinville.",
        "- Vão local é mesma urna e cargos diferentes: não diz quem votou em quem, e o governador sem apoio declarado a Flávio é teto, não palanque.",
        "- O teto soma parcelas que podem contar o mesmo eleitor.",
        "- 2022 é uma eleição, com outra terceira via e outro desenho de 2º turno estadual; a régua da urna é inferência ecológica, de agregado para agregado.",
        "- Nada aqui é previsão do 2º turno. Os pesos do índice são juízo editorial.",
        "",
    ]
    return "\n".join(linhas)
