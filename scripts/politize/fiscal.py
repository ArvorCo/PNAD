"""Fiscalização por seção no Politize: critérios, pontos e nível de atenção (funções puras).

Toda seção precisa de fiscal. Este módulo não decide quem precisa e quem não precisa:
ele lista, para cada seção, os motivos a mais que os números da seção, do local de
votação, da zona e do território dão para fiscalizar com cuidado redobrado. Junta três
fontes de sinal:

1. os 12 critérios do capítulo 13 do dossiê da apuração (``fiscais.json``), com o nível
   que o capítulo deu à seção e ao local;
2. critérios novos, medidos no boletim de urna de todas as seções (identificação sem a
   digital, troca de urna, modelo de urna com mais troca, abertura tardia, fila no
   fechamento, comparecimento atípico, tamanho, trânsito, disputa apertada, eleitorado
   que mais pede ajuda);
3. o risco do território do capítulo 13 (crime organizado com mapeamento público,
   homicídios, favela, terra indígena ou quilombo, fronteira, garimpo, unidade
   prisional, distância da sede), agora para todos os locais.

Pontos e cortes são juízo editorial por regra declarada, não medição de irregularidade.
Atipicidade estatística não é irregularidade; a lista é de prioridade de fiscalização,
não de acusação; o que resolve é a ata da mesa, o log da urna e a presença do fiscal.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- limiares declarados

ANO_NASC_PCT = 20.0  # liberados pelo ano de nascimento, % do comparecimento
ANO_NASC_PCT_Z = 12.0  # ... ou 12% com z >= 3 contra as outras seções da zona
Z_ZONA = 3.0
MIN_OUTRAS = 8  # seções da zona, além da própria, para o z valer
MIN_VOTANTES = 50
SEM_DIGITAL_PCT = 35.0  # eleitores sem biometria cadastrada, % do comparecimento
ABERTURA_MIN = 30  # primeiro voto 30 min ou mais depois das 8h de Brasília
ABERTURA_APTOS = 100
FILA_MIN = 60  # último voto 60 min ou mais depois das 17h de Brasília
GRANDE_APTOS = 400
TRANSITO_APTOS = 20
COMPARECIMENTO_ABST = 5.0  # abstenção de até 5% ...
COMPARECIMENTO_APTOS = 100  # ... com 100 aptos ou mais e 3 desvios abaixo da zona
DISPUTA_PP = 5.0
DISPUTA_VALIDOS_SECAO = 100
DISPUTA_VALIDOS_LOCAL = 500
IDOSOS_PCT = 45.0  # p95 das seções com perfil próprio
FUND_INC_PCT = 60.0  # p95
LOCAL_GRANDE_SECOES = 15
SEDE_KM = 50.0
MODELO_ANTIGO = "UE2013"

PESOS: dict[str, int] = {
    "c13_alta": 6,
    "c13_media": 4,
    "c13_baixa": 2,
    "id_ano": 3,
    "urna_troca": 3,
    "comparecimento": 3,
    "abertura": 2,
    "id_sem_digital": 1,
    "fila": 1,
    "urna_2013": 1,
    "grande": 1,
    "transito": 1,
    "disputa": 1,
    "assistido": 1,
    "local_c13_alta": 2,
    "local_c13_media": 1,
    "local_c13_baixa": 1,
    "local_grande": 1,
    "territorio_alto": 2,
    "territorio_medio": 1,
    "zona_atipica": 1,
    "zona_congelada": 1,
}

# pontos do território (os mesmos do capítulo 13; distância à sede em linha reta)
PONTOS_TERRITORIO: dict[str, int] = {
    "crime_organizado": 2,
    "homicidios_q5": 2,
    "homicidios_q4": 1,
    "favela": 1,
    "indigena_quilombo": 1,
    "prisional": 1,
    "fronteira": 1,
    "garimpo": 1,
    "sede_distante": 1,
}
TERRITORIO_ALTO = 4
TERRITORIO_MEDIO = 2

NIVEIS = ("maxima", "alta", "reforcada", "padrao")
CORTES = {"maxima": 6, "alta": 4, "reforcada": 1}


def nivel(pontos: int) -> str:
    """Nível de atenção pela soma de pontos (cortes em ``CORTES``)."""
    if pontos >= CORTES["maxima"]:
        return "maxima"
    if pontos >= CORTES["alta"]:
        return "alta"
    if pontos >= CORTES["reforcada"]:
        return "reforcada"
    return "padrao"


# ---------------------------------------------------------------- formatação


def br(v: float, casas: int = 1) -> str:
    """Número no formato brasileiro, com vírgula decimal."""
    return f"{v:.{casas}f}".replace(".", ",")


def hhmm(minutos_desde_meia_noite: float) -> str:
    m = round(minutos_desde_meia_noite)
    return f"{m // 60}h{m % 60:02d}"


# ---------------------------------------------------------------- estatística


def z_contra_outras(
    valores: np.ndarray, grupos: Sequence[Sequence[Any]], minimo: int = MIN_OUTRAS
) -> tuple[np.ndarray, np.ndarray]:
    """Escore z de cada linha contra as OUTRAS linhas do mesmo grupo (sem a própria).

    Média e desvio-padrão amostral das demais. Devolve ``(z, media_das_outras)``;
    ``NaN`` quando o grupo tem menos de ``minimo`` outras linhas válidas ou desvio zero.
    """
    v = np.asarray(valores, dtype=float)
    ok = ~np.isnan(v)
    base = pd.DataFrame(
        {
            "v": np.where(ok, v, 0.0),
            "q": np.where(ok, v * v, 0.0),
            "n": ok.astype(float),
        }
    )
    cols = []
    for i, g in enumerate(grupos):
        base[f"g{i}"] = list(g)
        cols.append(f"g{i}")
    agr = base.groupby(cols)[["v", "q", "n"]].transform("sum")
    n_out = agr["n"].to_numpy() - ok.astype(float)
    s_out = agr["v"].to_numpy() - base["v"].to_numpy()
    q_out = agr["q"].to_numpy() - base["q"].to_numpy()
    with np.errstate(divide="ignore", invalid="ignore"):
        media = s_out / n_out
        var = (q_out - n_out * media * media) / (n_out - 1)
        dp = np.sqrt(np.clip(var, 0, None))
        z = (v - media) / dp
    invalido = (n_out < minimo) | ~ok | ~(dp > 1e-9)
    z[invalido] = np.nan
    media = np.where(n_out >= minimo, media, np.nan)
    return z, media


# ---------------------------------------------------------------- sinais da seção


def _pct(parte: np.ndarray, todo: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(todo > 0, 100 * parte / todo, np.nan)


def sinais_secao(d: pd.DataFrame) -> list[list[list[str]]]:
    """Sinais de cada seção a partir do boletim e das métricas do Politize.

    Colunas esperadas: ``uf, zona, aptos, comparecimento, ano_nasc, sem_digital,
    abertura_min, encerramento_min`` (minutos desde 0h, hora de Brasília, ``NaN`` no
    exterior), ``tipo_urna, n_cargas, tipo_arquivo, modelo_urna, aptos_tte, abst_a,
    margem_v, validos, a60, fund_inc, perfil_fonte``. Devolve, por linha, a lista de
    ``[código, detalhe]``.
    """
    num = {
        c: d[c].astype(float).to_numpy()
        for c in ("comparecimento", "ano_nasc", "sem_digital", "aptos", "abst_a")
    }
    comp = np.nan_to_num(num["comparecimento"])
    an = _pct(num["ano_nasc"], comp)
    sd = _pct(num["sem_digital"], comp)
    grupos = [d["uf"].tolist(), d["zona"].tolist()]
    an_z, an_media = z_contra_outras(np.where(comp >= MIN_VOTANTES, an, np.nan), grupos)
    ab = np.where(num["aptos"] >= COMPARECIMENTO_APTOS, num["abst_a"], np.nan)
    ab_z, ab_media = z_contra_outras(ab, grupos)

    saida: list[list[list[str]]] = []
    registros = [{str(k): v for k, v in r.items()} for r in d.to_dict("records")]
    for i, r in enumerate(registros):
        s: list[list[str]] = []
        c = float(comp[i])
        aptos = _f(r.get("aptos")) or 0.0
        a_pct, a_z, a_med = float(an[i]), float(an_z[i]), float(an_media[i])
        if c >= MIN_VOTANTES and not math.isnan(a_pct):
            forte = a_pct >= ANO_NASC_PCT
            relativo = a_pct >= ANO_NASC_PCT_Z and not math.isnan(a_z) and a_z >= Z_ZONA
            if forte or relativo:
                ref = (
                    ""
                    if math.isnan(a_med)
                    else f"; nas outras seções da zona, {br(a_med)}%"
                )
                s.append(
                    [
                        "id_ano",
                        f"{int(_f(r.get('ano_nasc')) or 0)} de {int(c)} eleitores "
                        f"({br(a_pct)}%) liberados pelo ano de nascimento, sem a digital "
                        f"conferir{ref}",
                    ]
                )
        troca = _texto_troca(
            r.get("tipo_urna"), r.get("n_cargas"), r.get("tipo_arquivo")
        )
        if troca:
            s.append(["urna_troca", troca])
        abst = _f(r.get("abst_a"))
        b_z, b_med = float(ab_z[i]), float(ab_media[i])
        if (
            abst is not None
            and abst <= COMPARECIMENTO_ABST
            and aptos >= COMPARECIMENTO_APTOS
            and not math.isnan(b_z)
            and b_z <= -Z_ZONA
        ):
            s.append(
                [
                    "comparecimento",
                    f"abstenção de {br(abst)}% contra {br(b_med)}% nas outras seções "
                    "da zona",
                ]
            )
        ab_min = _f(r.get("abertura_min"))
        if (
            ab_min is not None
            and ab_min >= 8 * 60 + ABERTURA_MIN
            and aptos >= ABERTURA_APTOS
        ):
            s.append(["abertura", f"primeiro voto às {hhmm(ab_min)} de Brasília"])
        s_pct = float(sd[i])
        if c >= MIN_VOTANTES and not math.isnan(s_pct) and s_pct >= SEM_DIGITAL_PCT:
            s.append(
                [
                    "id_sem_digital",
                    f"{int(_f(r.get('sem_digital')) or 0)} de {int(c)} eleitores "
                    f"({br(s_pct)}%) sem digital cadastrada, identificados por documento",
                ]
            )
        en_min = _f(r.get("encerramento_min"))
        if en_min is not None and en_min >= 17 * 60 + FILA_MIN:
            s.append(["fila", f"último voto às {hhmm(en_min)} de Brasília"])
        if r.get("modelo_urna") == MODELO_ANTIGO:
            s.append(["urna_2013", "urna modelo 2013 no 1º turno"])
        if aptos >= GRANDE_APTOS:
            s.append(["grande", f"{int(aptos)} eleitores aptos"])
        tte = _f(r.get("aptos_tte")) or 0.0
        if tte >= TRANSITO_APTOS:
            s.append(["transito", f"{int(tte)} eleitores em trânsito"])
        margem = _f(r.get("margem_v"))
        if (
            margem is not None
            and abs(margem) <= DISPUTA_PP
            and (_f(r.get("validos")) or 0.0) >= DISPUTA_VALIDOS_SECAO
        ):
            s.append(["disputa", _texto_margem(margem, "nesta seção")])
        if r.get("perfil_fonte") == "secao":
            partes = []
            a60, fund = _f(r.get("a60")), _f(r.get("fund_inc"))
            if a60 is not None and a60 >= IDOSOS_PCT:
                partes.append(f"{br(a60)}% com 60 anos ou mais")
            if fund is not None and fund >= FUND_INC_PCT:
                partes.append(f"{br(fund)}% sem o fundamental completo")
            if partes:
                s.append(["assistido", " e ".join(partes)])
        saida.append(s)
    return saida


def _f(v: Any) -> float | None:
    """Float ou ``None`` (aceita ``None``, ``NaN``, número e texto com vírgula)."""
    return _float(v)


TIPO_URNA = {
    3: "urna de contingência",
    4: "urna de reserva",
    6: "urna de reserva no fim",
}


def _texto_troca(tipo_urna: Any, n_cargas: Any, tipo_arquivo: Any) -> str:
    """Descrição da troca de urna ou da recuperação de votos; vazio quando não houve."""
    partes = []
    tu, nc, ta = _float(tipo_urna), _float(n_cargas), _float(tipo_arquivo)
    if tu is not None and tu != 1:
        partes.append(TIPO_URNA.get(int(tu), f"urna tipo {int(tu)}"))
    if nc is not None and nc > 1:
        partes.append(f"{int(nc)} cargas registradas")
    if ta is not None and ta != 1:
        partes.append(
            "votos recuperados" if ta == 2 else "boletim de sistema de apuração"
        )
    return "; ".join(partes)


def _texto_margem(margem_v: float, onde: str) -> str:
    if abs(margem_v) < 0.05:
        return f"Flávio e Lula empataram {onde} no 1º turno"
    lider = "Flávio" if margem_v > 0 else "Lula"
    return f"{lider} à frente por {br(abs(margem_v))} pontos dos válidos {onde}"


# ---------------------------------------------------------------- local e território


def sinais_local(
    secoes: int,
    margem_v: float | None,
    validos: int | None,
    c13_nivel: str | None,
    c13_n: int,
) -> list[list[str]]:
    s: list[list[str]] = []
    if c13_nivel in ("alta", "media", "baixa") and c13_n > 0:
        nome = {"alta": "alto", "media": "médio", "baixa": "baixo"}[c13_nivel]
        s.append(
            [
                f"local_c13_{c13_nivel}",
                f"{c13_n} {'seção sinalizada' if c13_n == 1 else 'seções sinalizadas'} "
                f"no capítulo 13; nível do local: {nome}",
            ]
        )
    if secoes >= LOCAL_GRANDE_SECOES:
        s.append(["local_grande", f"{secoes} seções no mesmo prédio"])
    if (
        margem_v is not None
        and not math.isnan(margem_v)
        and abs(margem_v) <= DISPUTA_PP
        and (validos or 0) >= DISPUTA_VALIDOS_LOCAL
    ):
        s.append(["disputa", _texto_margem(margem_v, "no local de votação")])
    return s


def _flag(v: Any) -> bool | None:
    if v is None:
        return None
    t = str(v).strip()
    if t == "" or t.lower() in {"nan", "none"}:
        return None
    try:
        return bool(int(float(t)))
    except ValueError:
        return None


def _float(v: Any) -> float | None:
    if v is None:
        return None
    t = str(v).strip().replace(",", ".")
    if t == "" or t.lower() in {"nan", "none"}:
        return None
    try:
        x = float(t)
    except ValueError:
        return None
    return None if math.isnan(x) else x


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(min(1.0, a)))


def territorio(
    loc: Mapping[str, Any] | None,
    mun: Mapping[str, Any] | None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict[str, Any] | None:
    """Risco do território pela regra de pontos do capítulo 13 (distância em linha reta).

    ``loc``: linha de ``fiscais_risco_locais.csv.gz``; ``mun``: linha de
    ``fiscais_risco_municipios.csv``. Nulo quando nenhuma camada cobre o local.
    """
    motivos: list[str] = []
    pts = 0
    cobertas = 0
    if mun:
        co = str(mun.get("crime_organizado") or "").strip()
        if co:
            cobertas += 1
            if (
                co == "mapeamento público"
                and str(mun.get("crime_organizado_fontes") or "").strip()
            ):
                pts += PONTOS_TERRITORIO["crime_organizado"]
                motivos.append("mapeamento público de crime organizado no município")
        q = _float(mun.get("homicidios_quintil"))
        if q is not None:
            cobertas += 1
            if q >= 4:
                pts += PONTOS_TERRITORIO["homicidios_q5" if q >= 5 else "homicidios_q4"]
                taxa = _float(mun.get("homicidios_taxa_100mil"))
                ano = str(mun.get("homicidios_ano") or "").strip()
                txt = f"{br(taxa)} por 100 mil" if taxa is not None else "taxa sem dado"
                motivos.append(
                    f"homicídios no {int(q)}º quintil do país ({txt}"
                    f"{', ' + ano if ano else ''}, Atlas da Violência)"
                )
    if loc:
        for campo, chave, rotulo in (
            ("favela", "favela", "favela ou comunidade urbana (IBGE)"),
            ("prisional", "prisional", "unidade prisional ou socioeducativa"),
        ):
            v = _flag(loc.get(campo))
            if v is not None:
                cobertas += 1
                if v:
                    pts += PONTOS_TERRITORIO[chave]
                    motivos.append(rotulo)
        ti, qu = _flag(loc.get("terra_indigena")), _flag(loc.get("quilombo"))
        if ti is not None or qu is not None:
            cobertas += 1
            if ti or qu:
                pts += PONTOS_TERRITORIO["indigena_quilombo"]
                motivos.append(
                    "terra indígena a até 2 km" if ti else "quilombo a até 2 km (proxy)"
                )
    fonte_fg = loc or mun
    if fonte_fg:
        for campo, rotulo in (
            ("fronteira", "faixa de fronteira"),
            ("garimpo", "garimpo"),
        ):
            v = _flag(fonte_fg.get(campo))
            if v is not None:
                cobertas += 1
                if v:
                    pts += PONTOS_TERRITORIO[campo]
                    motivos.append(rotulo)
    if mun and lat is not None and lon is not None:
        slat, slon = _float(mun.get("sede_lat")), _float(mun.get("sede_lon"))
        if slat is not None and slon is not None:
            cobertas += 1
            km = haversine_km(slat, slon, lat, lon)
            if km >= SEDE_KM:
                pts += PONTOS_TERRITORIO["sede_distante"]
                motivos.append(f"a {br(km, 0)} km da sede do município, em linha reta")
    if cobertas == 0:
        return None
    if pts >= TERRITORIO_ALTO:
        niv = "alto"
    elif pts >= TERRITORIO_MEDIO:
        niv = "medio"
    else:
        niv = "baixo"
    return {"nivel": niv, "pontos": pts, "motivos": motivos}


# ---------------------------------------------------------------- pontuação


def pontos_de(codigos: Iterable[str]) -> int:
    return sum(PESOS.get(c, 0) for c in codigos)


def pontuar(
    sec: Sequence[Sequence[str]],
    loc: Sequence[Sequence[str]],
    zona: Sequence[Sequence[str]],
    c13_secao: str | None,
    terr: Mapping[str, Any] | None,
) -> int:
    """Soma de pontos de uma seção: seção, local, zona, capítulo 13 e território.

    O sinal do capítulo 13 do LOCAL só conta quando a própria seção não foi
    sinalizada (senão o mesmo achado entraria duas vezes). ``disputa`` conta uma vez,
    venha da seção ou do local.
    """
    cods = [c for c, _ in sec]
    vistos = set(cods)
    for c, _ in loc:
        if c.startswith("local_c13_") and c13_secao:
            continue
        if c in vistos:
            continue
        vistos.add(c)
        cods.append(c)
    cods += [c for c, _ in zona]
    if c13_secao:
        cods.append(f"c13_{c13_secao}")
    if terr and terr.get("nivel") in ("alto", "medio"):
        cods.append(f"territorio_{terr['nivel']}")
    return pontos_de(cods)
