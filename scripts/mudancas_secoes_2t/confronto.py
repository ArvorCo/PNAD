"""Confronto com os números públicos e com o painel do TSE de seções alteradas.

As contagens alternativas são declaradas antes de comparar (``HIPOTESES``); para cada
número público, a mais próxima é rotulada como hipótese de reconciliação, com o que
ela não explica ao lado. Não se combinam categorias até acertar um número.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from mudancas_secoes_2t import distancia as di
from mudancas_secoes_2t import endereco as en
from mudancas_secoes_2t.endereco import semelhanca_nomes

ROOT = Path(__file__).resolve().parents[2]
PAINEL = (
    ROOT / "data/originals/mudancas_secoes_2t/tse_painel_secoes_alteradas_20261018.json"
)
UFS_TSE = ("SP", "MG", "RJ", "BA")
SEMELHANCA_MESMO_LOCAL = 0.5

PUBLICOS: list[dict[str, Any]] = [
    {
        "id": "tse_agencia_brasil",
        "fonte": "TSE via Agência Brasil (17/10/2026), levantamento de 16/10",
        "secoes": 4352,
        "eleitores": None,
        "exterior": None,
        "por_uf": {"SP": 982, "MG": 514, "RJ": 431, "BA": 312},
        "carimbo": "16/10/2026 (dado citado pelo TSE)",
    },
    {
        "id": "coligacao_peticao",
        "fonte": "Relatório anexo à petição da coligação Brasil Pronto pra Mais "
        "(TSE 0603126-92.2026.6.00.0000), relatório de 17/10/2026 às 6h28",
        "secoes": 4864,
        "eleitores": 1795241,
        "exterior": None,
        "por_uf": None,
        "carimbo": "17/10/2026 06:28",
    },
    {
        "id": "forum_exportacao",
        "fonte": "Revista Fórum, exportação do sistema do TSE; O Tempo/Folhapress: 2.033 "
        "seções e 592 mil eleitores",
        "secoes": 2033,
        "eleitores": 592870,
        "exterior": 18,
        "por_uf": None,
        "carimbo": "18/10/2026 11:27",
    },
    {
        "id": "painel_tse",
        "fonte": "Portal de Estatísticas do TSE, painel Seções Eleitorais Alteradas no "
        "Segundo Turno",
        "secoes": 1106,
        "eleitores": 321382,
        "exterior": 0,
        "por_uf": None,
        "carimbo": "18/10/2026 20:27",
    },
]


def hipoteses(cls: pd.DataFrame) -> dict[str, pd.Series]:
    c = cls["categoria_cadastro"]
    t1, t2 = cls["temp_1t_cadastro"], cls["temp_2t_cadastro"]
    return {
        "fora_do_original_2t": t2,
        "fora_do_original_1t": t1,
        "fora_do_original_1t_ou_2t": t1 | t2,
        "numero_de_local_mudou_abcx": c.isin(list("ABCX")),
        "qualquer_alteracao_a_h": c != "Z",
        "alteracao_sem_ajuste_de_coordenada_a_g": c.isin(list("ABCXDEFG")),
        "mudanca_real": cls["mudanca_real"],
    }


DESCRICAO = {
    "fora_do_original_2t": "seções que no 2º turno votam fora do local original do cadastro",
    "fora_do_original_1t": "seções que no 1º turno votaram fora do local original",
    "fora_do_original_1t_ou_2t": "fora do original em pelo menos um dos turnos",
    "numero_de_local_mudou_abcx": "número do local mudou entre os arquivos (A, B, C, X)",
    "qualquer_alteracao_a_h": "qualquer alteração de cadastro (A a H)",
    "alteracao_sem_ajuste_de_coordenada_a_g": "alteração de número, nome, endereço ou "
    "coordenada acima de 300 m (A a G)",
    "mudanca_real": "mudança real de prédio (regra deste laudo)",
}


def contagens(cls: pd.DataFrame) -> dict[str, dict[str, Any]]:
    out = {}
    for nome, m in hipoteses(cls).items():
        s = cls[m.astype(bool)]
        principais = s[~s["agregada"]]
        vc = s["uf"].value_counts()
        out[nome] = {
            "descricao": DESCRICAO[nome],
            "secoes": len(s),
            "secoes_principais": len(principais),
            "secoes_brasil": int((s["uf"] != "ZZ").sum()),
            "secoes_exterior": int((s["uf"] == "ZZ").sum()),
            "eleitores": int(s["eleitores_2t"].sum()),
            "eleitores_eleicao_federal": int(s["eleitores_federal"].sum()),
            "por_uf": {u: int(vc.get(u, 0)) for u in UFS_TSE},
        }
    return out


def _dif(nosso: int, publico: int | None) -> dict[str, Any] | None:
    if publico is None:
        return None
    return {
        "nosso": nosso,
        "publico": publico,
        "diferenca": nosso - publico,
        "diferenca_pct": (
            round((nosso - publico) / publico * 100, 2) if publico else None
        ),
    }


def confronto_publico(
    cls: pd.DataFrame, painel: dict[str, Any] | None
) -> dict[str, Any]:
    cont = contagens(cls)
    itens = []
    for pub in PUBLICOS:
        if pub["id"] == "painel_tse" and painel is None:
            continue
        distancias = {
            nome: abs(c["secoes"] - pub["secoes"]) / pub["secoes"]
            + (
                abs(c["eleitores"] - pub["eleitores"]) / pub["eleitores"]
                if pub["eleitores"]
                else 0
            )
            for nome, c in cont.items()
        }
        melhor = min(distancias, key=lambda k: distancias[k])
        c = cont[melhor]
        item = {
            **pub,
            "hipotese_mais_proxima": melhor,
            "descricao_hipotese": c["descricao"],
            "secoes": _dif(c["secoes"], pub["secoes"]),
            "eleitores": _dif(c["eleitores"], pub["eleitores"]),
            "exterior": _dif(c["secoes_exterior"], pub["exterior"]),
            "por_uf": (
                {u: _dif(c["por_uf"][u], v) for u, v in pub["por_uf"].items()}
                if pub["por_uf"]
                else None
            ),
            "rotulo": "hipótese de reconciliação, não prova de método",
        }
        item["o_que_nao_explica"] = _nao_explica(pub, c, cont)
        itens.append(item)
    return {
        "hipoteses": cont,
        "numeros_publicos": itens,
        "eleitores_fora_do_original_2t_contra_coligacao": _dif(
            cont["fora_do_original_2t"]["eleitores"], 1795241
        ),
        "regra": "As hipóteses são declaradas antes da comparação; a mais próxima soma a "
        "diferença relativa de seções e a de eleitores quando o número público traz os "
        "dois. Não se combinam categorias até acertar um número.",
    }


def _mil(x: int) -> str:
    return f"{x:,}".replace(",", ".")


def _pct(x: float) -> str:
    return f"{x:+.1f}".replace(".", ",")


def _nao_explica(
    pub: dict[str, Any], c: dict[str, Any], cont: dict[str, Any]
) -> list[str]:
    out = []
    dif_s = (c["secoes"] - pub["secoes"]) / pub["secoes"] * 100
    if abs(dif_s) > 2:
        out.append(
            f"A contagem de seções difere {_pct(dif_s)}% ({_mil(c['secoes'])} contra "
            f"{_mil(pub['secoes'])})."
        )
    if pub["eleitores"]:
        dif_e = (c["eleitores"] - pub["eleitores"]) / pub["eleitores"] * 100
        if abs(dif_e) > 2:
            out.append(f"Os eleitores diferem {_pct(dif_e)}%.")
    if pub["por_uf"]:
        maximo_rj = max(h["por_uf"]["RJ"] for h in cont.values())
        if pub["por_uf"].get("RJ", 0) > maximo_rj:
            out.append(
                f"RJ {pub['por_uf']['RJ']} não aparece em nenhum recorte do arquivo de "
                f"18/10 (máximo {maximo_rj})."
            )
        for u, v in pub["por_uf"].items():
            if u != "RJ" and abs(c["por_uf"][u] - v) > 0.1 * v:
                out.append(f"{u}: {_mil(c['por_uf'][u])} contra {_mil(v)}.")
    if not out:
        out.append("A diferença fica abaixo de 2% em seções e eleitores.")
    return out


def ler_painel() -> tuple[pd.DataFrame | None, dict[str, Any] | None]:
    if not PAINEL.exists():
        return None, None
    bruto = PAINEL.read_bytes()
    d = json.loads(bruto)
    meta = {
        "caminho": str(PAINEL.relative_to(ROOT)),
        "bytes": len(bruto),
        "sha256": hashlib.sha256(bruto).hexdigest(),
        "fonte": d.get("fonte"),
        "url": d.get("url"),
        "ultima_atualizacao_tse": d.get("ultima_atualizacao_tse"),
        "lido_em": d.get("lido_em"),
        "linhas": len(d["linhas"]),
        "total_declarado": d.get("total_declarado"),
    }
    p = pd.DataFrame(d["linhas"])
    p["zona"] = p["zona"].astype("int64")
    p["secao"] = p["secao"].astype("int64")
    return p, meta


FONTE_ORIGINAL = "local_original_do_cadastro"


def _valor(x: Any) -> Any:
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else x


def locais_originais(
    cls: pd.DataFrame, chaves: set[tuple]
) -> dict[tuple, dict[str, Any]]:
    """Endereço do local original para seções em que o painel dá o original como final.

    Nome e endereço vêm de NM_LOCAL_VOTACAO_ORIGINAL e DS_ENDERECO_LOCVT_ORIGINAL da
    própria linha do arquivo de 18/10. Bairro, CEP e coordenada vêm de outra seção
    principal que vote nesse número de local no 2º turno, no mesmo município e zona
    (o número do local é contado dentro da zona); coordenada repetida por três ou
    mais locais do município fica de fora.
    """
    princ = cls[~cls["agregada"]]
    fonte: dict[tuple, dict[str, Any]] = {}
    for r in princ[
        [
            "uf",
            "mun",
            "zona",
            "local_2t",
            "bairro_2t",
            "cep_2t",
            "lat_2t",
            "lon_2t",
            "coord_repetida_2t",
        ]
    ].to_dict("records"):
        chave_local = (r["uf"], r["mun"], int(r["zona"]), int(r["local_2t"]))
        atual = fonte.get(chave_local)
        if atual is None or (
            atual["lat_2t"] is None and _valor(r["lat_2t"]) is not None
        ):
            fonte[chave_local] = {str(kk): _valor(v) for kk, v in r.items()}
    out: dict[tuple, dict[str, Any]] = {}
    base = {
        (str(r["uf"]), int(r["zona"]), int(r["secao"])): {
            str(c): v for c, v in r.items()
        }
        for r in cls[
            cls[["uf", "zona", "secao"]].apply(tuple, axis=1).isin(chaves)
        ].to_dict("records")
    }
    for k in sorted(chaves):
        s = base[k]
        nome, endereco = s["nome_original_2t"], s["endereco_original_2t"]
        f = fonte.get((k[0], s["mun"], int(k[1]), int(s["original_2t"])))
        lat = lon = None
        bairro = cep = None
        if f is not None:
            bairro, cep = f["bairro_2t"], f["cep_2t"]
            if f["lat_2t"] is not None and not f["coord_repetida_2t"]:
                lat, lon = f["lat_2t"], f["lon_2t"]
        lat1 = None if s["coord_repetida_1t"] else _valor(s["lat_1t"])
        lon1 = None if lat1 is None else _valor(s["lon_1t"])
        dist = (
            en.haversine_m(lat1, lon1, lat, lon)
            if lat1 is not None and lat is not None
            else None
        )
        consulta = ", ".join(
            x
            for x in (nome, endereco, s["municipio"], k[0])
            if isinstance(x, str) and x
        )
        out[k] = {
            "nome_2t": nome,
            "end_2t": endereco,
            "bairro_2t": bairro,
            "cep_2t": cep,
            "lat_2t": lat,
            "lon_2t": lon,
            "distancia_m": None if dist is None else round(dist, 0),
            "maps_novo": di.maps_novo(lat, lon, consulta),
            "endereco_fonte": FONTE_ORIGINAL,
        }
    return out


def confronto_painel(
    cls: pd.DataFrame, painel: pd.DataFrame, meta: dict[str, Any]
) -> dict:
    """Seção a seção: painel do TSE contra o conjunto A+B+C+X do arquivo de locais."""
    chave = ["uf", "zona", "secao"]
    if cls.duplicated(chave).any():
        raise ValueError("chave (uf, zona, seção) não é única no cadastro")
    zip_set = cls[cls["categoria_cadastro"].isin(list("ABCX"))]
    base = cls.set_index(chave)
    kp = set(map(tuple, painel[chave].to_numpy().tolist()))
    kz = set(map(tuple, zip_set[chave].to_numpy().tolist()))
    pidx = painel.set_index(chave)
    linhas = []
    for k in sorted(kp | kz):
        r = base.loc[k]
        fonte = (
            "ambos" if k in kp and k in kz else ("so_painel" if k in kp else "so_zip")
        )
        item = {
            "uf": k[0],
            "zona": int(k[1]),
            "secao": int(k[2]),
            "municipio": r["municipio"],
            "mun_tse": r["mun"],
            "fonte": fonte,
            "categoria_cadastro": r["categoria_cadastro"],
            "mudanca_real": bool(r["mudanca_real"]),
            "fora_do_original_1t": bool(r["temp_1t_cadastro"]),
            "fora_do_original_2t": bool(r["temp_2t_cadastro"]),
            "local_1t": int(r["local_cadastro_1t"]),
            "local_2t": int(r["local_cadastro_2t"]),
            "nome_1t": r["nome_1t"],
            "nome_2t": r["nome_2t"],
            "nome_original": r["nome_original_2t"],
            "eleitores_zip": int(r["eleitores_2t"]),
        }
        if k in kp:
            p = pidx.loc[k]
            item.update(
                {
                    "painel_local_inicial": p["local_inicial"],
                    "painel_local_final": p["local_final"],
                    "painel_eleitorado": int(p["eleitorado"]),
                    "inicial_confere_1t": semelhanca_nomes(
                        p["local_inicial"], r["nome_1t"]
                    )
                    >= SEMELHANCA_MESMO_LOCAL,
                    "final_confere_2t": semelhanca_nomes(p["local_final"], r["nome_2t"])
                    >= SEMELHANCA_MESMO_LOCAL,
                    "final_e_o_original": semelhanca_nomes(
                        p["local_final"], r["nome_original_2t"]
                    )
                    >= SEMELHANCA_MESMO_LOCAL,
                }
            )
        linhas.append(item)
    df = pd.DataFrame(linhas)
    amb = df[df["fonte"] == "ambos"]
    sp = df[df["fonte"] == "so_painel"]
    sz = df[df["fonte"] == "so_zip"]
    hip_painel = (
        sp["final_e_o_original"] & ~sp["final_confere_2t"] & sp["fora_do_original_2t"]
    )
    hip_zip = sz["fora_do_original_2t"] & ~sz["fora_do_original_1t"]
    chaves_orig = {
        (r["uf"], int(r["zona"]), int(r["secao"]))
        for r in sp[hip_painel].to_dict("records")
    }
    originais = locais_originais(cls, chaves_orig)
    lista_painel = [
        {str(c): v for c, v in x.items()}
        for x in sp.replace({np.nan: None}).to_dict("records")
    ]
    for item in lista_painel:
        o = originais.get((item["uf"], int(item["zona"]), int(item["secao"])))
        if o is not None:
            item["local_final_painel"] = o
    de = cls[cls["categoria_cadastro"].isin(["D", "E"])]
    de_real = de[de["mudanca_real"]]
    chaves_de = set(map(tuple, de[chave].to_numpy().tolist()))
    chaves_de_real = set(map(tuple, de_real[chave].to_numpy().tolist()))
    resumo = {
        "painel": meta,
        "mesmo_numero_outro_predio": {
            "secoes_d_e_no_arquivo": len(chaves_de),
            "secoes_d_e_com_mudanca_real": len(chaves_de_real),
            "listadas_no_painel": len(chaves_de & kp),
            "nota": "O painel lista troca de local (inicial e final); seção que mantém o "
            "número e muda de prédio (D e E) fica de fora, inclusive o caso confirmado pelo "
            "TRE-RJ (zona 188, seções 123 a 127).",
        },
        "conjunto_zip": "número do local mudou entre o arquivo de 02/10 e o de 18/10 "
        "(categorias A, B, C e X)",
        "uniao": len(df),
        "ambos": len(amb),
        "so_painel": len(sp),
        "so_zip": len(sz),
        "concordancia_pct": round(len(amb) / len(df) * 100, 2) if len(df) else None,
        "ambos_nomes_conferem": int(
            (amb["inicial_confere_1t"] & amb["final_confere_2t"]).sum()
        ),
        "ambos_eleitorado_painel": int(amb["painel_eleitorado"].sum()),
        "ambos_eleitores_zip": int(amb["eleitores_zip"].sum()),
        "so_painel_por_categoria_zip": sp["categoria_cadastro"]
        .value_counts()
        .to_dict(),
        "so_zip_por_categoria": sz["categoria_cadastro"].value_counts().to_dict(),
        "so_painel_por_uf": sp["uf"].value_counts().to_dict(),
        "so_zip_por_uf": sz["uf"].value_counts().to_dict(),
        "hipotese": {
            "enunciado": "O painel parece considerar final o local original do cadastro "
            "quando a interdição do 1º turno acabou, enquanto o arquivo de locais ainda "
            "traz o temporário nos dois turnos; e o inverso nas só do arquivo: o arquivo "
            "traz a nova realocação e o painel não a lista.",
            "so_painel_final_e_o_original_e_zip_segue_temporario": int(
                hip_painel.sum()
            ),
            "so_painel_total": len(sp),
            "so_zip_nova_realocacao": int(hip_zip.sum()),
            "so_zip_total": len(sz),
            "resultado": _resultado(hip_painel, sp, hip_zip, sz),
        },
        "listas": {
            "so_painel": lista_painel,
            "so_zip": sz.drop(
                columns=[
                    c
                    for c in df.columns
                    if c.startswith(("painel_", "inicial_", "final_"))
                ]
            )
            .replace({np.nan: None})
            .to_dict("records"),
        },
        "rotulo": "Medição da divergência entre duas publicações do TSE com o mesmo "
        "carimbo de hora (18/10/2026 20:27); não diz qual das duas está certa.",
    }
    return {"resumo": resumo, "tabela": df, "originais": originais}


def _resultado(hp: pd.Series, sp: pd.DataFrame, hz: pd.Series, sz: pd.DataFrame) -> str:
    return (
        f"Nas {len(sp)} seções só do painel, {int(hp.sum())} têm no painel como local "
        "final o local original do cadastro, enquanto o arquivo de locais as mantém no "
        f"temporário nos dois turnos. Nas {len(sz)} só do arquivo, {int(hz.sum())} são "
        "novas realocações (original no 1º turno, temporário no 2º) que o painel não lista."
    )
