"""Textos do capítulo "Grupos" do dossiê do 2º turno.

Cada função recebe ``anomalia_ml.json`` lido e devolve HTML. Todo número vem do
JSON; os verbos (sobe, cai, maior, menor) e as frases de leitura são escolhidos
pelo próprio número, para continuarem certos quando o motor rodar de novo.
Selos pelo padrão da casa: verificado (o que o modelo mediu), inferência (o que
se conclui do medido), hipótese (o que pede confirmação), juízo editorial.
"""

from __future__ import annotations

from html import escape

from apuracao_2026.pagina_comum import caixa, cartao, inteiro, nota, num, p, tabela

from . import pagina_fig_anomalia_base as B

ROTULO = B.ROTULO
# Acima deste V de Cramér, dizemos que a partição é, em boa parte, geografia.
V_GEOGRAFIA = 0.30
# Acima desta parte das seções da UF líder, o grupo atípico é uma UF.
UF_DOMINANTE_PCT = 50.0


def _iteracoes_totais(aj: dict) -> int | None:
    """Iterações da partida escolhida mais as do refino adotado (tolerância apertada)."""
    ap = (aj.get("diagnostico_convergencia") or {}).get("apertado") or {}
    if ap.get("adotado") and ap.get("iteracoes_padrao") is not None:
        return int(ap["iteracoes_padrao"]) + int(ap.get("iteracoes") or 0)
    return aj.get("iteracoes")


def rotulo(A: dict) -> str:
    return str(A.get("rotulo") or ROTULO)


def _k(A: dict) -> int:
    return B.k_de(A)


def _ex(k: int) -> str:
    return B.extenso(k)


def _esc(x) -> str:
    return escape(str(x))


def _neg(x, casas: int = 4) -> str:
    """Número com o menos tipográfico (log-verossimilhança é negativa)."""
    return num(x, casas).replace("-", "−")


def _plural(n, singular: str, plural: str) -> str:
    return singular if round(n or 0) == 1 else plural


def rascunho(A: dict) -> str:
    """Frase de aviso quando o motor rodou em amostra (`rascunho.amostra`)."""
    r = A.get("rascunho") or {}
    if not r.get("amostra"):
        return ""
    total = B.g(A.get("universo") or {}, "secoes_universo")
    frase = (
        f"Versão rascunho: o motor rodou numa amostra de {inteiro(r['amostra'])} seções"
    )
    if total:
        frase += f" das {inteiro(total)} do universo"
    return frase + "; o ajuste na base inteira substitui estes números."


# ------------------------------------------------------------------ abertura


def titulo(A: dict) -> str:
    c = B.atipico(A)
    return (
        f"Os grupos de seções nos dois turnos.<br><em>{inteiro(c['secoes'])} seções formam o grupo que o modelo "
        "menos explica.</em>"
    )


def lead(A: dict) -> str:
    c = B.atipico(A)
    k = _k(A)
    return (
        f"Uma mistura gaussiana com {_ex(k)} grupos, ajustada sobre nove frações do eleitorado de "
        f"{inteiro(A['universo']['secoes'])} seções (1º e 2º turno, exterior fora), separa um grupo de "
        f"{inteiro(c['secoes'])} seções ({num(c['pct_secoes'], 1)}%) como o mais atípico: {_esc(c.get('rotulo') or 's/d')}. "
        f"{rotulo(A)}" + (f" {rascunho(A)}" if rascunho(A) else "")
    )


def como_ler(A: dict) -> str:
    u = A["universo"]
    ex = u.get("excluidas") or {}
    return caixa(
        "io",
        "Como ler",
        f" {rotulo(A)} O modelo não sabe o que é uma eleição: ele só agrupa seções cujas nove frações se "
        "parecem. Um grupo 'atípico' é o que o modelo pior descreve, e isso pode ser geografia, tamanho de seção, "
        f"a abstenção do interior ou um padrão que vale a pena olhar. Entraram {inteiro(u['secoes'])} seções com BU "
        f"nos dois turnos e 30 aptos ou mais em cada; ficaram fora {inteiro(ex.get('exterior'))} do exterior, "
        f"{inteiro(ex.get('sem_par'))} sem par entre os turnos e {inteiro(ex.get('aptos_menor_30'))} com menos de 30 aptos."
        + (f" <b>{rascunho(A)}</b>" if rascunho(A) else ""),
    )


def cartoes(A: dict) -> str:
    c = B.atipico(A)
    aj = A.get("ajuste") or {}
    return (
        '<div class="finding-grid">'
        + cartao(
            inteiro(c["secoes"]),
            f"seções no grupo mais atípico ({num(c['pct_secoes'], 1)}% das analisadas)",
        )
        + cartao(str(_k(A)), "grupos, escolhidos por regra declarada sobre BIC e ICL")
        + cartao(
            inteiro(_iteracoes_totais(aj)),
            f"iterações do EM até a convergência final; {inteiro(aj.get('sementes_no_maximo'))} de {inteiro(len(aj.get('sementes') or []) or (aj.get('n_init') or 0))} partidas no mesmo máximo",
        )
        + cartao(
            num(A.get("cramer_v_regiao"), 2),
            "V de Cramér entre grupo e região (0 = independente)",
        )
        + "</div>"
    )


def abertura(A: dict) -> str:
    c = B.atipico(A)
    dl = B.deltas(c)
    dp = B.deltas_pais(A)
    ma = A["mais_anomalo"]
    seg = ma.get("segundo") or {}
    partes = []
    for kk in ("comp", "lula", "flavio", "brancos", "nulos"):
        if kk in dl and kk in dp:
            partes.append(
                f"{B.DELTA_NOME[kk]} {B.pp_txt(dl[kk], 1)} no grupo contra {B.pp_txt(dp[kk], 1)} no país"
            )
    h = p(
        f"O grupo mais atípico tem {inteiro(c['secoes'])} seções, {inteiro(c.get('aptos_medio'))} aptos em média. "
        f"O que o distingue é o nível, não a mudança: {_esc(str(c.get('rotulo') or '').rstrip('.'))}. "
        f"Entre os turnos ele andou perto do país: {'; '.join(partes)}. Abstenção de {B.pct_txt(B.g(c, 'abst1_pct'))} "
        f"no 1º turno e {B.pct_txt(B.g(c, 'abst2_pct'))} no 2º; fatia de Flávio entre os dois finalistas de "
        f"{B.pct_txt(B.g(c, 'fatia_f1'))} para {B.pct_txt(B.g(c, 'fatia_f2'))}.",
        "verificado",
    )
    crit = _esc(
        (
            ma.get("criterio")
            or "soma dos postos de menor log-verossimilhança média e de maior dispersão"
        ).rstrip(".")
    )
    folga = ""
    if seg:
        dif = B.g(seg, "diferenca_postos") or 0
        folga = (
            f" O segundo colocado é o Grupo {int(seg['id']) + 1}, a {num(dif, 0)} {_plural(dif, 'posto', 'postos')} de "
            "distância"
            + (
                ": escolha folgada."
                if (B.g(seg, "diferenca_postos") or 0) >= 2
                else ": escolha apertada, e o leitor deve olhar os dois."
            )
        )
    h += p(
        f"Critério do grupo atípico, o mesmo do 1º turno: {crit}.{folga}", "verificado"
    )
    return h


# ------------------------------------------------------------------ o espaço


def espaco(A: dict) -> str:
    f = A.get("features") or {}
    cols = f.get("colunas") or list(B.COLUNA_NOME)
    nomes = "; ".join(B.COLUNA_NOME.get(c, c) for c in cols)
    eq = f.get("equivalencia_afim")
    if not eq:
        eq = (
            "A mistura com covariância completa é invariante a transformações afins invertíveis: trocar as quatro "
            "colunas do 2º turno por diferenças contra o 1º muda a parametrização, não a verossimilhança nem a "
            "partição. Por isso o capítulo ajusta nos níveis e publica os centros também em diferenças."
        )
    h = p(
        f"Cada seção é um ponto em {_ex(len(cols))} dimensões: {nomes}; todas em porcentagem do eleitorado apto do "
        "próprio turno. Comparecimento e abstenção entram implícitos, porque são a soma e o complemento dessas "
        "frações; incluí-los como décima coluna deixaria a covariância singular. Antes do ajuste, cada coluna é "
        "padronizada (média zero, desvio um entre as seções), como no 1º turno.",
        "verificado",
    )
    h += p(_esc(eq), "verificado")
    pad = f.get("padronizacao") or {}
    if pad:
        linhas = []
        for c in cols:
            x = pad.get(c) or {}
            linhas.append(
                [
                    B.COLUNA_NOME.get(c, c),
                    num(B.g(x, "media"), 2),
                    num(B.g(x, "desvio"), 2),
                ]
            )
        h += tabela(
            ["fração do eleitorado", "média (%)", "desvio-padrão (pp)"],
            linhas,
            "As nove colunas e a padronização aplicada antes do ajuste.",
        )
    return h


# ------------------------------------------------------------------ k


def escolha_k(A: dict) -> str:
    k = _k(A)
    kj, ki = B.g(A, "k_joelho_bic"), B.g(A, "k_min_icl")
    declarada = _esc(B.g(A, "regra_declarada", "regra", padrao="")).rstrip(".")
    resultado = _esc(B.g(A, "regra", padrao="")).rstrip(".")
    regra = f"A regra: {declarada}." if declarada else ""
    if resultado and resultado != declarada:
        regra += f" O resultado: {resultado}."
    bic = sorted(A.get("bic") or [], key=lambda x: x["k"])
    frase_k = ""
    if bic:
        b0, b1 = bic[0], bic[-1]
        queda = float(b0["bic"]) - float(b1["bic"])
        frase_k = (
            f" De k = {b0['k']} a k = {b1['k']} o BIC cai {inteiro(queda)} pontos; a regra marca o k em que a queda "
            "seguinte fica abaixo de 5% desse total."
        )
    concord = "concordam" if kj == ki else "divergem"
    h = p(
        f"O número de grupos não é achado: é escolha por regra declarada antes de olhar o resultado. {regra}{frase_k} "
        f"Joelho do BIC em k = {kj}, mínimo do ICL em k = {ki}; os dois critérios {concord}, e o escolhido é k = {k}.",
        "verificado",
    )
    if kj != ki:
        h += p(
            "Quando o joelho do BIC e o mínimo do ICL divergem, a regra prefere o joelho: o ICL penaliza grupos "
            "sobrepostos e tende a pedir menos grupos. A tabela mostra os dois para o leitor conferir.",
            "inferencia",
        )
    return h


# ------------------------------------------------------------------ convergência


def convergencia(A: dict) -> str:
    aj = A.get("ajuste") or {}
    K = A.get("kmeans") or {}
    ari = K.get("ari_com_mistura_k_estrela") or {}
    sem = aj.get("sementes") or []
    n_part = (
        len(sem)
        if isinstance(sem, list) and sem and isinstance(sem[0], dict)
        else (
            len(sem) * len(aj.get("inits") or [1])
            if isinstance(sem, list)
            else aj.get("n_init")
        )
    )
    dg = aj.get("diagnostico_convergencia") or {}
    frase_dg = _esc(dg.get("frase")) if isinstance(dg, dict) and dg.get("frase") else ""
    conv = "convergiu" if aj.get("convergiu") else "não convergiu"
    tol = (
        num(aj.get("tol"), 8).rstrip("0").rstrip(",")
        if aj.get("tol") is not None
        else "s/d"
    )
    h = p(
        f"O EM {conv} em {inteiro(aj.get('iteracoes'))} iterações na base ajustada, com tolerância {tol} e teto de "
        f"{inteiro(aj.get('max_iter'))}; {inteiro(aj.get('sementes_no_maximo'))} de {inteiro(n_part)} partidas "
        f"(inicializações {' e '.join(_esc(i) for i in aj.get('inits') or [])}) chegaram ao mesmo máximo. "
        f"Log-verossimilhança média de {_neg(aj.get('loglik_media'), 4)} por seção; {num(aj.get('segundos'), 0)} segundos de ajuste.",
        "verificado",
    )
    if frase_dg:
        h += p(frase_dg, "verificado")
    a1, a2 = ari.get("niveis"), ari.get("niveis_e_deltas")
    if a1 is not None or a2 is not None:
        leitura = (
            "as duas partições quase coincidem"
            if max(x for x in (a1, a2) if x is not None) >= 0.8
            else (
                "as partições são parecidas, não iguais"
                if max(x for x in (a1, a2) if x is not None) >= 0.5
                else "o k-means corta a nuvem de outro jeito"
            )
        )
        h += p(
            f"Contraste: o k-means, que não é invariante à troca de níveis por diferenças, rodou nos dois enquadramentos. "
            f"Índice de Rand ajustado com a partição da mistura em k = {_k(A)}: {num(a1, 2)} nos nove níveis e "
            f"{num(a2, 2)} em níveis e diferenças; {leitura}. A mistura continua sendo o modelo publicado, porque é a "
            "única das duas que dá a cada seção uma densidade, e é a densidade que define o atípico.",
            "inferencia",
        )
    return h


# ------------------------------------------------------------------ os grupos


def grupos(A: dict) -> str:
    cs = B.componentes(A)
    k = _k(A)
    maior = max(cs, key=lambda c: c["secoes"])
    menor = min(cs, key=lambda c: c["secoes"])
    h = p(
        f"Os {_ex(k)} grupos vão de {inteiro(menor['secoes'])} seções (Grupo {menor['id'] + 1}) a {inteiro(maior['secoes'])} "
        f"(Grupo {maior['id'] + 1}), ordenados pela fração de Lula no 2º turno. O rótulo de cada um é gerado por regra: "
        "diz o que distingue o centro do grupo do centro do país, em diferenças entre os turnos e em terceira via do 1º.",
        "verificado",
    )
    v_reg, v_uf = A.get("cramer_v_regiao"), A.get("cramer_v_uf")
    if v_reg is not None:
        forca = (
            "forte"
            if v_reg >= 0.5
            else (
                "moderada a forte"
                if v_reg >= V_GEOGRAFIA
                else "moderada" if v_reg >= 0.15 else "fraca"
            )
        )
        h += p(
            f"Grupo é geografia? Em parte. V de Cramér de {num(v_reg, 2)} entre grupo e região e de {num(v_uf, 2)} entre "
            f"grupo e UF: associação {forca}. A figura da composição regional e o botão da dispersão (cor pela região) "
            "deixam o leitor ver isso sem confiar na nossa frase.",
            "inferencia",
        )
    return h


# ------------------------------------------------------------------ o grupo atípico


def atipico(A: dict) -> str:
    c = B.atipico(A)
    ufs = c.get("ufs_top") or []
    regs = c.get("regioes") or []
    h = ""
    if ufs:
        lista = ", ".join(
            f"{B.nome_uf(u['uf'])} {num(u['pct_do_cluster'], 1)}% do grupo"
            + (
                f" ({num(u['pct_da_uf'], 1)}% das seções da UF)"
                if u.get("pct_da_uf") is not None
                else ""
            )
            for u in ufs[:5]
        )
        h += p(
            f"Onde está: {lista}."
            + (
                f" Região dominante: {_esc(regs[0]['regiao'])}, {num(regs[0]['pct_do_cluster'], 1)}% do grupo."
                if regs
                else ""
            ),
            "verificado",
        )
    fatia, ic_f = B.medida_voto(A, "fatia")
    did, ic_d = B.medida_voto(A, "did")
    v = B.voto(A)
    if fatia is not None or did is not None:
        frases = []
        if fatia is not None:
            z = B.contem_zero(ic_f)
            lado = "maior" if fatia > 0 else "menor"
            frases.append(
                f"a fatia de Flávio no 2º turno é {B.pp_txt(abs(fatia), 2).lstrip('+')} {lado} que nas vizinhas do mesmo "
                f"município ({B.ic_txt(ic_f)}{'; o intervalo inclui o zero' if z else '; o intervalo não inclui o zero' if z is not None else ''})"
            )
        if did is not None:
            z = B.contem_zero(ic_d)
            dirc = "Flávio" if did > 0 else "Lula"
            frases.append(
                f"em diferença em diferenças contra o 1º turno, a fatia andou {B.pp_txt(abs(did), 2).lstrip('+')} na direção de "
                f"{dirc} a mais que nas vizinhas ({B.ic_txt(ic_d)}{'; inclui o zero' if z else '; não inclui o zero' if z is not None else ''})"
            )
        h += p(
            f"O voto, publicado seja qual for o sinal: em {inteiro(B.g(v, 'n', 'n_sinal_comparavel'))} seções do grupo com "
            f"vizinhas comparáveis, {'; '.join(frases)}.",
            "verificado",
        )
        h += p(
            "Diferença contra vizinhas não é efeito: o grupo foi definido pelas próprias frações de voto, então uma "
            "diferença de fatia é esperada por construção. O número que informa é a diferença em diferenças, e mesmo "
            "ela mistura composição do eleitorado com qualquer outra coisa.",
            "inferencia",
        )
    s = c.get("sinais") or {}
    pais_s = B.sinais_pais(A)
    if s:
        partes = []
        for kk, nome in B.SINAL_NOME.items():
            if B.g(s, kk) is None:
                continue
            comp = (
                f" contra {B.pct_txt(pais_s.get(kk), 2)} no país"
                if pais_s.get(kk) is not None
                else ""
            )
            partes.append(f"{nome}: {B.pct_txt(B.g(s, kk), 2)}{comp}")
        h += p(
            "Cruzamento com os sinais do capítulo anterior, que foram definidos sem olhar o voto: "
            + "; ".join(partes)
            + ". Um grupo definido por voto que concentra sinais operacionais pede leitura conjunta; um que não "
            "concentra é só composição.",
            "verificado",
        )
    h += p(
        f"As {inteiro(len(B.amostras(A)))} amostras da tabela são as seções de menor log-verossimilhança dentro do grupo, "
        "cada uma com link para a ficha no Politize-se, onde o grupo e a densidade aparecem ao lado dos demais sinais. "
        + rotulo(A),
        "verificado",
    )
    return h


# ------------------------------------------------------------------ achado contrário


def _tamanho(A: dict, itens: list[str]) -> None:
    """Grupo é tamanho de seção? O V de Cramér com a faixa de aptos responde."""
    v_tam = A.get("cramer_v_tamanho")
    if v_tam is None:
        return
    if v_tam >= V_GEOGRAFIA:
        itens.append(
            f"a partição também é tamanho de seção: V de Cramér de {num(v_tam, 2)} com a faixa de aptos. Seção "
            "pequena tem frações mais voláteis, e o modelo lê volatilidade como grupo"
        )
    else:
        itens.append(
            f"a partição não é tamanho de seção: V de Cramér de {num(v_tam, 2)} com a faixa de aptos"
        )


def contrario(A: dict) -> str:
    c = B.atipico(A)
    v_reg, v_uf, v_mod = (
        A.get("cramer_v_regiao"),
        A.get("cramer_v_uf"),
        A.get("cramer_v_modelo"),
    )
    ufs = c.get("ufs_top") or []
    itens = []
    if v_reg is not None and v_reg >= V_GEOGRAFIA:
        itens.append(
            f"a partição é, em boa parte, geografia: V de Cramér de {num(v_reg, 2)} com a região e {num(v_uf, 2)} com a UF. "
            "Quem agrupa seções por voto no Brasil agrupa Nordeste contra Sul antes de qualquer outra coisa"
        )
    elif v_reg is not None:
        itens.append(
            f"a partição não é só geografia: V de Cramér de {num(v_reg, 2)} com a região e {num(v_uf, 2)} com a UF"
        )
    if (
        ufs
        and ufs[0].get("pct_do_cluster") is not None
        and ufs[0]["pct_do_cluster"] >= UF_DOMINANTE_PCT
    ):
        itens.append(
            f"o grupo atípico é, antes de tudo, {B.nome_uf(ufs[0]['uf'])}: {num(ufs[0]['pct_do_cluster'], 1)}% das suas seções estão lá"
        )
    pa = B.pais(A)
    ce = B.centro(c)
    ap_g, ap_p = c.get("aptos_medio"), B.aptos_medio_pais(A)
    if ap_g is not None and ap_p is not None and ap_p and abs(ap_g / ap_p - 1) >= 0.2:
        itens.append(
            f"o grupo atípico tem seções {'menores' if ap_g < ap_p else 'maiores'} que a média ({inteiro(ap_g)} contra "
            f"{inteiro(ap_p)} aptos): parte da atipicidade é variância de seção pequena, não comportamento"
        )
    _tamanho(A, itens)
    if v_mod is not None:
        itens.append(
            f"modelo da urna quase não separa os grupos: V de Cramér de {num(v_mod, 2)}"
            if v_mod < 0.15
            else f"o modelo da urna se associa aos grupos (V de Cramér de {num(v_mod, 2)}), o que acompanha a geografia da distribuição das urnas"
        )
    did, ic_d = B.medida_voto(A, "did")
    if did is not None and B.contem_zero(ic_d):
        itens.append(
            f"a diferença em diferenças do voto no grupo atípico ({B.pp_txt(did, 2)}) tem IC que inclui o zero: o dado não "
            "sustenta mudança de voto própria do grupo"
        )
    if "lula2" in ce and "lula2" in pa:
        itens.append(
            f"o grupo atípico não é 'o grupo de um candidato': Lula tem {B.pct_txt(ce['lula2'])} do eleitorado nele contra "
            f"{B.pct_txt(pa['lula2'])} no país; Flávio, {B.pct_txt(ce.get('flavio2'))} contra {B.pct_txt(pa.get('flavio2'))}"
        )
    texto = (
        "<ul>" + "".join(f"<li>{i[:1].upper()}{i[1:]}.</li>" for i in itens) + "</ul>"
    )
    return nota("contrario", texto, "O que a mistura não separa")


# ------------------------------------------------------------------ limites


def limites_itens(A: dict) -> list[str]:
    return [
        rotulo(A),
        "k é escolha por regra declarada (joelho do BIC, senão mínimo do ICL), não propriedade dos dados; outra regra dá outro k, e a tabela mostra os candidatos.",
        "O grupo depende da padronização: as nove colunas entram com média zero e desvio um, o que dá a brancos e nulos (frações pequenas) o mesmo peso de Lula e Flávio.",
        "Nenhuma seção individual é acusada: o sinal por seção é pertencer a um grupo, e a densidade é relativa ao modelo, não a uma regra legal.",
        "Exterior fora: a abstenção muito acima da média formaria um grupo só com essas urnas e distorceria os demais.",
        "Diferença contra vizinhas é esperada por construção, porque o grupo foi definido pelo voto; só a diferença em diferenças informa, e com IC.",
        "Seções com menos de 30 aptos em qualquer turno e sem BU nos dois turnos ficaram fora; o universo está na caixa Como ler.",
    ]


__all__ = [
    "ROTULO",
    "abertura",
    "atipico",
    "cartoes",
    "como_ler",
    "contrario",
    "convergencia",
    "escolha_k",
    "espaco",
    "grupos",
    "lead",
    "limites_itens",
    "titulo",
]
