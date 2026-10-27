"""Bloco "Seções com zero voto" do capítulo Grupos do dossiê do 2º turno.

Resposta à manchete da Folha de S.Paulo de 27/10/2026 ("Flávio teve zero voto em
106 urnas, nas quais Lula somou quase 15 mil"). Interface: ``bloco(d) -> str``, com
``d`` o leitor ``Dados`` do dossiê (ou um dicionário com a chave ``zeros.json``), e
``limites_itens(d) -> list[str]`` para a lista de limites do capítulo. Todo número
sai de ``analysis/apuracao_2t_2026/dados/zeros.json``, gerado por
``python3 scripts/apuracao-2t-2026-zeros.py``; nada é digitado aqui. Sem o JSON, o
bloco mostra o título e o aviso padrão de figura pendente, e o capítulo renderiza o
resto. Selos pelo padrão da casa; sem travessão; nunca "fraude"; leitura sempre do
eleitorado da seção, nunca do voto de uma pessoa.
"""

from __future__ import annotations

from collections.abc import Callable
from html import escape

from apuracao_2026.dados import regiao
from apuracao_2026.pagina_comum import (
    ERROS_DE_DADO,
    NOME_UF,
    cartao,
    inteiro,
    nota,
    num,
    p,
    tabela,
)
from apuracao_2026.pagina_fig_base import (
    GRADE,
    HALO,
    INK,
    MUTED,
    Tips,
    area,
    escala,
    ficha,
    figura_html,
    hit,
    larga_estreita,
    legenda_html,
    ln,
    r,
    svg_abre,
    t,
    ticks,
)

from .pagina_fig_anomalia_b import pendente

ARQ = "zeros.json"
NOME = "an_zeros"
COMANDO = "python3 scripts/apuracao-2t-2026-zeros.py"
ROTULO = "Atipicidade pede explicação, não prova irregularidade."
COR_2022 = "#5f6773"
COR_2026 = "#0c7a72"
ANOS = ((2022, "2022, Bolsonaro", COR_2022), (2026, "2026, Flávio", COR_2026))


# ------------------------------------------------------------------ acessores


def _z(d) -> dict | None:
    return d.get(ARQ)


def recorte(Z: dict, ano: int, turno: int, lado: str) -> dict:
    for x in Z["recortes"]:
        if (x["ano"], x["turno"], x["lado"]) == (ano, turno, lado):
            return x
    raise KeyError(f"recorte {ano} {turno}º turno {lado}")


def tipos(Z: dict, chave: str) -> dict[str, dict]:
    return {x["tipo"]: x for x in Z["tipo_local"][chave]}


def ufs_2t(Z: dict) -> list[dict]:
    """UFs com ao menos uma seção sem voto no candidato da direita, 2º turno."""
    sel = [
        x for x in Z["por_uf"] if x["zero_direita_2022_2t"] or x["zero_direita_2026_2t"]
    ]
    return sorted(
        sel,
        key=lambda x: (-x["zero_direita_2026_2t"], -x["zero_direita_2022_2t"], x["uf"]),
    )


def _data(iso: str) -> str:
    a, m, dia = iso.split("-")
    return f"{dia}/{m}/{a}"


def _lista_ufs(linhas: list[dict], n: int | None = None) -> str:
    itens = [f"{NOME_UF.get(x['uf'], x['uf'])} {inteiro(x['secoes'])}" for x in linhas]
    itens = itens[:n] if n else itens
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def _minuscula(s: str) -> str:
    """Primeira letra minúscula, salvo nome próprio (rótulo de grupo no meio da frase)."""
    if s.split(" ", 1)[0] in {"Flávio", "Lula", "Bolsonaro"}:
        return s
    return s[:1].lower() + s[1:]


def _pct(x, casas: int = 1) -> str:
    return "s/d" if x is None else f"{num(x, casas)}%"


# ------------------------------------------------------------------ figura


def _fichas(Z: dict, tips: Tips) -> tuple[dict[str, str], dict[str, str]]:
    ch_uf = {}
    for x in ufs_2t(Z):
        nome = NOME_UF.get(x["uf"]) or str(x["uf"])
        ch_uf[x["uf"]] = tips.add(
            ficha(
                nome,
                "seções sem voto no candidato da direita",
                [
                    (
                        "2º turno de 2022 (Bolsonaro)",
                        f"{inteiro(x['zero_direita_2022_2t'])} de {inteiro(x['secoes_2022_2t'])}",
                    ),
                    (
                        "2º turno de 2026 (Flávio)",
                        f"{inteiro(x['zero_direita_2026_2t'])} de {inteiro(x['secoes_2026_2t'])}",
                    ),
                    (
                        "1º turno, 2022 e 2026",
                        f"{inteiro(x['zero_direita_2022_1t'])} e {inteiro(x['zero_direita_2026_1t'])}",
                    ),
                ],
                ROTULO,
            )
        )
    t22, t26 = tipos(Z, "2022_2t_direita"), tipos(Z, "2026_2t_direita")
    ch_tipo = {}
    for k, x in t26.items():
        y = t22[k]
        ch_tipo[k] = tips.add(
            ficha(
                x["nome"],
                "2º turno, seções sem voto no candidato da direita",
                [
                    ("2022", f"{inteiro(y['secoes'])} ({_pct(y['pct'])})"),
                    ("2026", f"{inteiro(x['secoes'])} ({_pct(x['pct'])})"),
                    ("Votos de Lula nelas, 2026", inteiro(x["votos_adversario"])),
                ],
                "Tipo pelo nome do prédio, regra declarada em zeros.json.",
            )
        )
    return ch_uf, ch_tipo


def _barras(
    y: float,
    valores: list[int],
    x: Callable[[float], float],
    x0: float,
    alt: float,
    passo: float,
    fonte: float,
) -> list[str]:
    """Duas barras (2022 e 2026) a partir de ``y``, com o número na ponta."""
    out = []
    for i, (v, (_, _, cor)) in enumerate(zip(valores, ANOS, strict=True)):
        yb = y + i * passo
        out.append(r(x0, yb, x(v) - x0, alt, cor))
        out.append(
            t(x(v) + 6, yb + alt - 1, inteiro(v), fonte, INK, mono=True, weight="600")
        )
    return out


def _marcas(vmax: float) -> list[float]:
    """Marcas redondas que fecham acima do maior valor (47 vira 0 a 50)."""
    m = ticks(0, vmax, 6)
    if len(m) > 1 and m[-1] < vmax:
        m.append(m[-1] + (m[1] - m[0]))
    return m


def _legenda_svg(x: float, y: float, fonte: float) -> str:
    """Os dois anos na própria figura, para quem lê a imagem sem a legenda HTML."""
    out, cx = [], x
    for _, nome, cor in ANOS:
        out.append(r(cx, y - fonte + 2, fonte, fonte - 2, cor))
        out.append(t(cx + fonte + 6, y, nome, fonte, INK))
        cx += fonte + 22 + 0.56 * fonte * len(nome)
    return "".join(out)


def _svg(Z: dict, ch_uf: dict, ch_tipo: dict, larga: bool) -> str:
    ufs = ufs_2t(Z)
    t22, t26 = tipos(Z, "2022_2t_direita"), tipos(Z, "2026_2t_direita")
    ordem = [k for k in t26 if k in t22]
    w = 1100 if larga else 380
    f_rot, f_num = (14, 13) if larga else (16, 14)
    lab = 300 if larga else 36
    x1 = w - (70 if larga else 44)
    rh, alt, passo = (26, 9, 11) if larga else (30, 10, 12)
    out: list[str] = []
    y = 26.0
    tit_a = (
        ["Seções sem voto no candidato da direita, 2º turno, por UF"]
        if larga
        else ["Seções sem voto no candidato", "da direita, 2º turno, por UF"]
    )
    for linha in tit_a:
        out.append(t(8, y, linha, 15 if larga else 16, INK, weight="700"))
        y += 20
    if larga:
        out.append(_legenda_svg(w - 330, 26, 14))
    else:
        y += 4
        out.append(_legenda_svg(8, y, 15))
        y += 22
    y += 8
    vmax = max(max(u["zero_direita_2022_2t"], u["zero_direita_2026_2t"]) for u in ufs)
    marcas = _marcas(vmax)
    topo_x = marcas[-1]
    x = escala(0, topo_x, lab + 10, x1)
    y_ini = y
    for u in ufs:
        rot = NOME_UF.get(u["uf"], u["uf"]) if larga else u["uf"]
        partes = [area(0, y - 2, w, rh), t(lab, y + 15, rot, f_rot, INK, "end")]
        partes += _barras(
            y + 2,
            [u["zero_direita_2022_2t"], u["zero_direita_2026_2t"]],
            x,
            lab + 10,
            alt,
            passo,
            f_num,
        )
        out.append(hit("".join(partes), ch_uf[u["uf"]], foco=True))
        y += rh
    for m in marcas:
        out.insert(0, ln(x(m), y_ini - 4, x(m), y, GRADE, 1))
        out.append(t(x(m), y + 16, inteiro(m), 12, MUTED, "middle", mono=True))
    out.append(t(x1, y + 34, "seções", 12, MUTED, "end"))
    y += 70
    tit_b = (
        ["Tipo do local, pelo nome do prédio, 2º turno"]
        if larga
        else ["Tipo do local, pelo nome", "do prédio, 2º turno"]
    )
    for linha in tit_b:
        out.append(t(8, y, linha, 15 if larga else 16, INK, weight="700"))
        y += 20
    y += 8
    vmax_b = max(max(t22[k]["secoes"], t26[k]["secoes"]) for k in ordem)
    marcas_b = _marcas(vmax_b)
    topo_b = marcas_b[-1]
    x0_b = lab + 10 if larga else 8
    xb = escala(0, topo_b, x0_b, x1)
    y_ini_b = y
    for k in ordem:
        nome = t26[k]["nome"]
        valores = [t22[k]["secoes"], t26[k]["secoes"]]
        if larga:
            altura = rh + 4
            partes = [
                area(0, y - 2, w, altura),
                t(lab, y + 15, nome, f_rot, INK, "end"),
            ]
            partes += _barras(y + 2, valores, xb, x0_b, alt, passo, f_num)
        else:
            altura = 58
            partes = [
                area(0, y - 2, w, altura),
                t(8, y + 14, nome, f_rot, INK, extra=HALO),
            ]
            partes += _barras(y + 24, valores, xb, x0_b, alt, passo, f_num)
        out.append(hit("".join(partes), ch_tipo[k], foco=True))
        y += altura
    for m in marcas_b:
        out.insert(0, ln(xb(m), y_ini_b - 4, xb(m), y, GRADE, 1))
        out.append(t(xb(m), y + 16, inteiro(m), 12, MUTED, "middle", mono=True))
    out.append(t(x1, y + 34, "seções", 12, MUTED, "end"))
    h = y + 46
    r26 = recorte(Z, 2026, 2, "direita")
    r22 = recorte(Z, 2022, 2, "direita")
    cab = svg_abre(
        w,
        h,
        "Seções sem voto no candidato da direita, 2022 contra 2026",
        f"Barras por UF e por tipo de local: {inteiro(r22['secoes'])} seções sem voto em Bolsonaro no 2º "
        f"turno de 2022 e {inteiro(r26['secoes'])} sem voto em Flávio no 2º turno de 2026, Brasil sem o "
        "exterior.",
    )
    return cab + "".join(out) + "</svg>"


def fig_zeros(Z: dict) -> str:
    tips = Tips()
    ch_uf, ch_tipo = _fichas(Z, tips)
    corpo = larga_estreita(
        _svg(Z, ch_uf, ch_tipo, True), _svg(Z, ch_uf, ch_tipo, False)
    )
    r26 = recorte(Z, 2026, 2, "direita")
    r22 = recorte(Z, 2022, 2, "direita")
    legenda = (
        f"Seções do Brasil, sem o exterior, sem nenhum voto no candidato da direita no 2º turno: "
        f"{inteiro(r22['secoes'])} em 2022 (Bolsonaro) e {inteiro(r26['secoes'])} em 2026 (Flávio), entre "
        f"{inteiro(r22['universo_secoes'])} e {inteiro(r26['universo_secoes'])} seções. Só aparecem as UFs com "
        "ao menos uma seção assim em um dos anos. O tipo do local sai do nome do prédio por regra declarada; "
        "nome que não diz o tipo fica como outro local. Fonte: zeros.json (bancos de BUs de 2026, arquivo por "
        "seção de 2022, cadastro do Politize)."
    )
    leg = legenda_html([(nome, cor) for _, nome, cor in ANOS], "Ano e candidato")
    return figura_html(NOME, corpo, legenda, tips, modo="full", apos=leg)


# ------------------------------------------------------------------ tabelas


def tabela_recortes(Z: dict) -> str:
    linhas = []
    for turno in (2, 1):
        for lado in ("direita", "lula"):
            a, b = recorte(Z, 2022, turno, lado), recorte(Z, 2026, turno, lado)
            quem = "no candidato da direita" if lado == "direita" else "em Lula"
            linhas.append(
                [
                    f"{turno}º turno, zero voto {quem}",
                    inteiro(a["secoes"]),
                    inteiro(a["votos_adversario"]),
                    inteiro(b["secoes"]),
                    inteiro(b["votos_adversario"]),
                ]
            )
    u22 = recorte(Z, 2022, 2, "direita")["universo_secoes"]
    u26 = recorte(Z, 2026, 2, "direita")["universo_secoes"]
    return tabela(
        [
            "recorte",
            "2022: seções",
            "2022: votos do adversário nelas",
            "2026: seções",
            "2026: votos do adversário nelas",
        ],
        linhas,
        f"Seções do Brasil, sem o exterior, sem nenhum voto num finalista. Candidato da direita: Bolsonaro em 2022, "
        f"Flávio em 2026. Universo: {inteiro(u22)} seções em 2022 e {inteiro(u26)} em 2026 (2º turno).",
    )


def _linha_secao(x: dict, lado: str) -> list:
    t1 = x.get("t1") or {}
    b22 = x.get("politize_bolsonaro22_2t_pct_validos")
    link = (
        f'<a href="{escape(x["link"])}">{escape(x["uf"])} {inteiro(x["zona"])}/'
        f"{inteiro(x['secao'])}</a>"
    )
    adv = x["lula"] if lado == "direita" else x["flavio"]
    zero_1t = t1.get("flavio") if lado == "direita" else t1.get("lula")
    return [
        link,
        escape(x["municipio"]),
        escape(x["local"] or "s/d"),
        escape(x["tipo"].replace("_", " ")),
        inteiro(x["aptos"]),
        inteiro(x["comparecimento"]),
        inteiro(adv),
        inteiro(zero_1t),
        "s/d" if b22 is None else num(b22, 1),
    ]


def tabela_secoes(Z: dict, lado: str) -> str:
    chave = "lista_zero_flavio" if lado == "direita" else "lista_zero_lula"
    lista = Z[chave]
    adv, zero = ("Lula", "Flávio") if lado == "direita" else ("Flávio", "Lula")
    return tabela(
        [
            "seção (Politize-se)",
            "município",
            "local",
            "tipo",
            "aptos",
            "compareceram",
            f"{adv}, 2º turno",
            f"{zero}, 1º turno",
            "Bolsonaro 2022, % válidos",
        ],
        [_linha_secao(x, lado) for x in lista],
        f"As {inteiro(len(lista))} seções sem voto em {zero} no 2º turno de 2026. Bolsonaro 2022: fatia do 2º "
        "turno pareada pelo cadastro do Politize (s/d quando a seção não tem par). Cada seção abre a ficha no "
        "Politize-se.",
    )


# ------------------------------------------------------------------ textos


def _confere(Z: dict) -> str:
    m = Z["manchete"]
    r26 = recorte(Z, 2026, 2, "direita")
    ce, ex = Z["com_exterior"], Z["exterior"]
    rl = recorte(Z, 2026, 2, "lula")
    a_mais = ce["2026_2t_direita"] - r26["secoes"]
    a_mais_l = ce["2026_2t_lula"] - rl["secoes"]
    sc = ex.get("sem_comparecimento_2t_2026")
    mesmas = (
        ex.get("zero_flavio_2t_sem_comparecimento") == a_mais == sc
        and ex.get("zero_lula_2t_sem_comparecimento") == a_mais_l == sc
    )
    h = p(
        f"A {escape(m['veiculo'])} publicou em {_data(m['data'])} a manchete “{escape(m['titulo'])}”. É o ponto de "
        "partida deste bloco.",
        "relato",
    )
    frase_ex = ""
    if a_mais or a_mais_l:
        frase_ex = (
            f" Com o exterior são {inteiro(ce['2026_2t_direita'])} sem voto em Flávio e "
            f"{inteiro(ce['2026_2t_lula'])} sem voto em Lula"
        ) + (
            f": as {inteiro(a_mais)} a mais de cada lado são as mesmas seções do exterior em que ninguém votou."
            if mesmas
            else "; as diferenças estão no exterior, publicadas à parte no JSON."
        )
    h += p(
        f"O número confere. Nos boletins de urna das {inteiro(r26['universo_secoes'])} seções do Brasil, sem o "
        f"exterior, {inteiro(r26['secoes'])} não registram nenhum voto em Flávio no 2º turno, e Lula soma "
        f"{inteiro(r26['votos_adversario'])} votos nelas.{frase_ex}",
        "verificado",
    )
    rl22 = recorte(Z, 2022, 2, "lula")
    h += p(
        f"O espelho existe: {inteiro(rl['secoes'])} seções sem nenhum voto em Lula no 2º turno, com "
        f"{inteiro(rl['votos_adversario'])} votos de Flávio ({_lista_ufs(Z['zero_lula']['perfil']['ufs'])}), "
        f"todas pequenas, de {inteiro(Z['zero_lula']['perfil']['aptos']['min'])} a "
        f"{inteiro(Z['zero_lula']['perfil']['aptos']['max'])} aptos. "
        f"Em 2022 eram {inteiro(rl22['secoes'])} seções sem voto em Lula no 2º turno, com "
        f"{inteiro(rl22['votos_adversario'])} votos de Bolsonaro.",
        "verificado",
    )
    return h


def _cartoes(Z: dict) -> str:
    r26 = recorte(Z, 2026, 2, "direita")
    r22 = recorte(Z, 2022, 2, "direita")
    rl = recorte(Z, 2026, 2, "lula")
    ap = Z["zero_flavio"]["perfil"]["aptos"]
    return (
        '<div class="finding-grid">'
        + cartao(
            inteiro(r26["secoes"]),
            f"seções do Brasil sem voto em Flávio no 2º turno; Lula soma {inteiro(r26['votos_adversario'])} nelas",
        )
        + cartao(
            inteiro(r22["secoes"]),
            f"seções sem voto em Bolsonaro no 2º turno de 2022; Lula somou {inteiro(r22['votos_adversario'])}",
        )
        + cartao(
            inteiro(ap["mediana"]),
            f"aptos na seção mediana da lista de 2026, contra {inteiro(ap['mediana_pais'])} no país",
        )
        + cartao(
            inteiro(rl["secoes"]),
            f"seções sem voto em Lula no 2º turno; Flávio soma {inteiro(rl['votos_adversario'])} nelas",
        )
        + "</div>"
    )


def _onde(Z: dict) -> str:
    pf = Z["zero_flavio"]["perfil"]
    n = pf["secoes"]
    top = pf["ufs"][:5]
    ap, cp = pf["aptos"], pf["comparecimento"]
    f0 = ap["faixas"][0]
    rg = max(Z["por_regiao"], key=lambda x: x["zero_direita_2026_2t"])
    return p(
        f"Ficam em {inteiro(pf['municipios'])} municípios. {_lista_ufs(top)} somam "
        f"{inteiro(sum(x['secoes'] for x in top))} das {inteiro(n)}. Na região {escape(rg['regiao'])}, que tem "
        f"{_pct(rg['pct_das_secoes_2026_2t'])} das seções do país, ficam {inteiro(rg['zero_direita_2026_2t'])} "
        f"({_pct(rg['pct_da_lista_2026_2t'])} da lista). São seções pequenas: {inteiro(ap['mediana'])} "
        f"aptos na mediana, contra {inteiro(ap['mediana_pais'])} no país; {inteiro(f0['secoes'])} têm menos de "
        f"{inteiro(f0['ate'] + 1)} aptos ({_pct(f0['pct'])} da lista, contra {_pct(f0['pct_pais'])} das seções do "
        f"país). Somam {inteiro(ap['soma'])} aptos e {inteiro(cp['soma'])} comparecimentos ({_pct(cp['pct'], 2)}, "
        f"contra {_pct(cp['pct_pais'], 2)} no país).",
        "verificado",
    )


def _tipo(Z: dict) -> str:
    t26 = tipos(Z, "2026_2t_direita")
    muns = Z["regra_tipo_local"]["municipios_comunidade"]
    nomes = [escape(m["nome"]) for m in muns]
    muns_txt = ", ".join(nomes[:-1]) + " e " + nomes[-1] if len(nomes) > 1 else nomes[0]
    ufs = {m["uf"] for m in muns}
    if len(ufs) == 1:
        muns_txt += f", no {NOME_UF.get(next(iter(ufs)), '')}"
    pela_regra = Z["zero_flavio"].get("comunidade_pela_regra_do_municipio")
    regra = (
        f" ({inteiro(pela_regra)} delas pela regra declarada que trata como comunidade as seções de {muns_txt})"
        if pela_regra
        else ""
    )
    return p(
        f"Pelo nome do prédio no cadastro, {inteiro(t26['aldeia_indigena']['secoes'])} ficam em aldeia ou escola "
        f"indígena, {inteiro(t26['comunidade']['secoes'])} em comunidade, quilombo ou ribeirinha{regra}, "
        f"{inteiro(t26['prisao']['secoes'])} em unidade prisional ou socioeducativa e "
        f"{inteiro(t26['outro']['secoes'])} em outro local, porque o nome não diz o tipo. Lula soma "
        f"{inteiro(t26['aldeia_indigena']['votos_adversario'])} votos nas seções em aldeia.",
        "verificado",
    )


def _padrao(Z: dict) -> str:
    zf = Z["zero_flavio"]
    n = zf["perfil"]["secoes"]
    t1, rp = zf["primeiro_turno"], zf["repeticao_2022"]
    pol = rp.get("politize") or {}
    aus = rp["chave_ausente_por_tipo"]
    h = p(
        f"O padrão não nasceu no 2º turno. Nas mesmas {inteiro(n)} seções, Flávio somou {inteiro(t1['votos_soma'])} "
        f"votos no 1º turno: zero em {inteiro(t1['secoes_zero'])} delas e no máximo 5 em {inteiro(t1['secoes_ate_5'])} "
        f"(o maior número numa seção foi {inteiro(t1['maximo'])}).",
        "verificado",
    )
    h += p(
        f"E não nasceu em 2026: das {inteiro(n)}, {inteiro(rp['chave_presente'])} têm a mesma chave (UF, município, "
        f"zona e seção) no arquivo de 2022; em {inteiro(rp['zero_2t'])} delas Bolsonaro também teve zero voto no 2º "
        f"turno. Nas {inteiro(pol.get('pareadas'))} seções pareadas pelo cadastro do Politize, a fatia de Bolsonaro "
        f"no 2º turno de 2022 foi de {_pct(pol.get('mediana_pct_validos'))} dos válidos na mediana, "
        f"{inteiro(pol.get('zeros_exatos'))} zeros exatos e no máximo {_pct(pol.get('maximo_pct_validos'))}. As outras "
        f"{inteiro(rp['chave_ausente'])} não têm a mesma chave em 2022 (seção renumerada ou criada depois); "
        f"{inteiro(aus.get('aldeia_indigena'))} delas ficam em aldeia.",
        "verificado",
    )
    return h


def _leitura(Z: dict) -> str:
    r26, r22 = recorte(Z, 2026, 2, "direita"), recorte(Z, 2022, 2, "direita")
    r1, r122 = recorte(Z, 2026, 1, "direita"), recorte(Z, 2022, 1, "direita")
    mais = r26["universo_secoes"] - r22["universo_secoes"]
    menos = "menos" if r26["secoes"] < r22["secoes"] else "mais"
    return p(
        "A leitura que os números sustentam: é geografia de comunidade fechada e pequena, aldeia, quilombo e "
        "ribeirinha, onde o eleitorado da seção vota quase em bloco, e o mesmo padrão aparece no 1º turno e em "
        f"2022, nas mesmas seções. Em 2026 há {menos} seções assim que em 2022: {inteiro(r26['secoes'])} contra "
        f"{inteiro(r22['secoes'])} no 2º turno e {inteiro(r1['secoes'])} contra {inteiro(r122['secoes'])} no 1º, "
        f"mesmo com {inteiro(mais)} seções a mais no país no 2º turno.",
        "inferencia",
    )


def _mistura(Z: dict) -> str:
    m = Z["zero_flavio"].get("mistura") or {}
    if not m.get("disponivel"):
        return ""
    gs = m["por_grupo"]
    partes = [
        f"{inteiro(g['secoes'])}{' caem' if i == 0 else ''} no Grupo {g['id'] + 1}"
        + (
            " (o grupo atípico)"
            if g["id"] == m["grupo_atipico"]
            else f" ({escape(_minuscula(str(g.get('rotulo') or '').rstrip('.')))})"
        )
        for i, g in enumerate(gs)
    ]
    lista = (
        ", ".join(partes[:-1]) + " e " + partes[-1] if len(partes) > 1 else partes[0]
    )
    leitura = (
        "São a ponta de uma nuvem contínua, não um padrão à parte."
        if m["no_grupo_atipico"] < m["no_universo"] / 2
        else "A maioria cai no grupo atípico."
    )
    return p(
        f"A mistura deste capítulo não trata essas seções como um grupo próprio. Das {inteiro(m['no_universo'])} "
        f"que entram no modelo (as outras {inteiro(m['fora_do_universo'])} ficam fora porque o modelo exige 30 aptos "
        f"ou mais nos dois turnos), {lista}. {leitura}",
        "inferencia",
    )


def _contrario(Z: dict) -> str:
    r22 = recorte(Z, 2022, 2, "direita")
    t22, t26 = tipos(Z, "2022_2t_direita"), tipos(Z, "2026_2t_direita")
    n26 = Z["zero_flavio"]["perfil"]["secoes"]
    aus = Z["zero_flavio"]["repeticao_2022"]["chave_ausente_por_tipo"]
    rg = {x["regiao"]: x for x in Z["por_regiao"]}
    ne, no = rg["Nordeste"], rg["Norte"]
    top22 = [
        x
        for x in sorted(Z["por_uf"], key=lambda x: -x["zero_direita_2022_2t"])
        if regiao(x["uf"]) == "Nordeste"
    ][:2]
    top_txt = _lista_ufs(
        [{"uf": x["uf"], "secoes": x["zero_direita_2022_2t"]} for x in top22]
    )
    texto = (
        "<ul>"
        f"<li>A leitura de comunidade fechada vale melhor para 2026 que para 2022. Em 2022 a lista era maior e mais "
        f"nordestina: {_pct(ne['pct_da_lista_2022_2t'])} no Nordeste ({top_txt}), contra "
        f"{_pct(ne['pct_da_lista_2026_2t'])} em 2026, quando o Norte passou de {_pct(no['pct_da_lista_2022_2t'])} "
        f"para {_pct(no['pct_da_lista_2026_2t'])}. Pelo nome do prédio, {inteiro(t22['outro']['secoes'])} das "
        f"{inteiro(r22['secoes'])} de 2022 ficam como outro local e {inteiro(t22['prisao']['secoes'])} estavam em "
        "unidade prisional ou socioeducativa.</li>"
        f"<li>As seções em aldeia passaram de {inteiro(t22['aldeia_indigena']['secoes'])} para "
        f"{inteiro(t26['aldeia_indigena']['secoes'])}, e {inteiro(aus.get('aldeia_indigena'))} das de 2026 não têm a "
        "mesma chave em 2022: parte do aumento vem de seção nova ou renumerada, que não tem par em 2022 para "
        "comparar.</li>"
        f"<li>Mesmo em 2026, {inteiro(t26['outro']['secoes'])} das {inteiro(n26)} ficam como outro local: o nome do "
        "prédio não basta para afirmar que toda seção da lista é comunidade fechada.</li>"
        "</ul>"
    )
    return nota("contrario", texto, "O que a leitura não cobre")


def _juizo(Z: dict) -> str:
    n = Z["zero_flavio"]["perfil"]["secoes"]
    return nota(
        "juizo",
        "A manchete acerta o número. O que ela não diz é que o espelho existe, que o padrão se repete nas mesmas "
        "seções desde 2022 e que hoje há menos seções assim que em 2022. Seção sem voto num candidato descreve o eleitorado daquela "
        "seção, nunca o voto de uma pessoa: o voto é secreto. "
        f"{ROTULO} Cada uma das {inteiro(n)} tem ficha no Politize-se, na tabela abaixo.",
    )


def bloco(d) -> str:
    """O bloco inteiro: título, textos, figura, tabelas; pendente sem ``zeros.json``."""
    h = '<h3 id="zeros">Seções com zero voto</h3>'
    Z = _z(d)
    if Z is None:
        return h + pendente(NOME, f"zeros.json ausente; rode {COMANDO}")
    try:
        corpo = _confere(Z) + _cartoes(Z) + _onde(Z) + fig_zeros(Z) + _tipo(Z)
        corpo += _padrao(Z) + tabela_recortes(Z) + _leitura(Z) + _mistura(Z)
        corpo += _contrario(Z) + _juizo(Z)
        corpo += tabela_secoes(Z, "lula")
        corpo += (
            "<details><summary>As "
            f"{inteiro(len(Z['lista_zero_flavio']))} seções sem voto em Flávio, uma a uma</summary>"
            f"{tabela_secoes(Z, 'direita')}</details>"
        )
    except ERROS_DE_DADO as erro:
        return h + pendente(NOME, f"zeros.json: {type(erro).__name__} {erro}")
    return h + corpo


def limites_itens(d) -> list[str]:
    """Limites do bloco, acrescentados aos do capítulo; vazio sem ``zeros.json``."""
    Z = _z(d)
    if Z is None:
        return []
    try:
        t26 = tipos(Z, "2026_2t_direita")
        n = Z["zero_flavio"]["perfil"]["secoes"]
        aus = Z["zero_flavio"]["repeticao_2022"]["chave_ausente"]
    except ERROS_DE_DADO:
        return []
    return [
        "Seções com zero voto: seção sem voto num candidato descreve o eleitorado da seção, não o voto de uma "
        "pessoa, e não prova irregularidade.",
        f"O tipo do local sai do nome do prédio por regra declarada e conservadora; {inteiro(t26['outro']['secoes'])} "
        f"das {inteiro(n)} seções sem voto em Flávio ficam como outro local.",
        f"A comparação seção a seção com 2022 usa a mesma chave (UF, município, zona e seção) e perde as "
        f"renumeradas ou criadas depois: {inteiro(aus)} das {inteiro(n)}.",
    ]


__all__ = [
    "ARQ",
    "NOME",
    "bloco",
    "fig_zeros",
    "limites_itens",
    "recorte",
    "tabela_recortes",
    "tabela_secoes",
    "tipos",
    "ufs_2t",
]
