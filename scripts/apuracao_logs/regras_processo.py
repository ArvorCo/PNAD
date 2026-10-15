"""Referências do processo observado, respeitando caminho de identificação."""

import numpy as np

from .processo import TIPOS


def campos_processo(r, principal):
    p = r.get("processo_observado", {})
    # Empate entre quantidades de cargos não autoriza comparar outro grupo.
    if p.get("cargos") != principal:
        p = {}
    processo, cadencia = p.get("processo", {}), p.get("cadencia", {})
    tipos = p.get("por_tipo", {})
    return {
        **{
            f"{nome}_taxa": (
                100 * r["contagens"].get(chave, 0) / r["bu"]["comparecimento"]
                if r["bu"].get("comparecimento")
                else None
            )
            for nome, chave in (
                ("retomadas", "retomadas_inatividade"),
                ("cancelamentos", "habilitacoes_canceladas"),
            )
        },
        "processo_media": processo.get("media"),
        "processo_mediana": processo.get("p50"),
        "processo_p90": processo.get("p90"),
        "n_processo": processo.get("n", 0),
        "processo_excluidos": p.get("excluidos_identificacao", 0),
        "cadencia_mediana": cadencia.get("p50"),
        "cadencia_media": cadencia.get("media"),
        "n_cadencia": cadencia.get("n", 0),
        "rajada10_s": p.get("rajada10_s"),
        "janelas10": p.get("janelas10", 0),
        "faixa_volume": str(min(5, cadencia.get("n", 0) // 100)),
        "processo_tipos": tipos,
        **{f"processo_{t}": tipos.get(t, {}).get("p50") for t in TIPOS},
        **{f"n_processo_{t}": tipos.get(t, {}).get("n", 0) for t in TIPOS},
        "inspecoes": r.get("inspecoes", {}).get("n", 0),
        "inspecao_max": r.get("inspecoes", {}).get("max"),
        "retomadas_inatividade": r["contagens"].get("retomadas_inatividade", 0),
        "cancelamentos_habilitacao": r["contagens"].get("habilitacoes_canceladas", 0),
        "reinicios_sistema": r["contagens"].get("reinicios_sistema_em_votacao", 0),
        "ocorrencias_operacionais": r.get("ocorrencias_operacionais", []),
    }


def avaliar_processo(df, referencias, desvios):
    refs, flags = {}, {}
    elegivel = (
        df.elegivel_tempo & (df.n_processo >= 30) & (df.n_processo >= 0.9 * df.n_tempo)
    )
    tipos_rapidos = np.zeros(len(df), dtype=bool)
    for tipo in TIPOS:
        campo = f"processo_{tipo}"
        ok = elegivel & df.elegivel_bio & (df[f"n_{campo}"] >= 30)
        ref = referencias(df, campo, ["uf", "modelo", "cargos"], ok, 3)
        refs[campo] = ref
        tipos_rapidos |= (
            ok
            & (df[campo] < ref.ref - desvios * ref.escala)
            & (df[campo] < 0.5 * ref.ref)
        ).to_numpy()
    flags["processo_rapido"] = tipos_rapidos
    ok = df.elegivel_tempo & (df.n_cadencia >= 30)
    for campo in ("cadencia_mediana", "rajada10_s"):
        grupos = ["uf", "modelo", "cargos"]
        if campo == "rajada10_s":
            grupos += ["faixa_volume"]
        refs[campo] = referencias(df, campo, grupos, ok, 3)
    ref = refs["cadencia_mediana"]
    flags["cadencia_rapida"] = (
        ok
        & (df.cadencia_mediana < ref.ref - desvios * ref.escala)
        & (df.cadencia_mediana < 0.5 * ref.ref)
    ).to_numpy()
    ref = refs["rajada10_s"]
    flags["rajada_rapida"] = (
        ok
        & (df.rajada10_s < ref.ref - desvios * ref.escala)
        & (df.rajada10_s < 0.5 * ref.ref)
        & (df.rajada10_s < 0.5 * df.cadencia_mediana)
    ).to_numpy()
    denominadores = {
        "processo_rapido": int(
            (
                elegivel
                & df.elegivel_bio
                & np.logical_or.reduce(
                    [
                        (df[f"n_processo_{t}"] >= 30)
                        & refs[f"processo_{t}"].ref.notna()
                        for t in TIPOS
                    ]
                )
            ).sum()
        ),
        "cadencia_rapida": int((ok & refs["cadencia_mediana"].ref.notna()).sum()),
        "rajada_rapida": int(
            (ok & df.rajada10_s.notna() & refs["rajada10_s"].ref.notna()).sum()
        ),
    }
    for nome, cod, contagem in (
        ("retomadas", "retomadas_inatividade", "retomadas_inatividade"),
        ("cancelamentos", "cancelamentos_habilitacao", "cancelamentos_habilitacao"),
    ):
        campo = f"{nome}_taxa"
        ok = df.elegivel_tempo & (df.comparecimento >= 50)
        ref = referencias(df, campo, ["uf", "modelo", "cargos"], ok, 1)
        refs[campo] = ref
        flags[cod] = (
            ok
            & (df[contagem] >= 3)
            & (df[campo] > ref.ref + desvios * ref.escala)
            & (df[campo] >= ref.ref + 5)
        ).to_numpy()
        denominadores[cod] = int((ok & ref.ref.notna()).sum())
    return flags, refs, denominadores
