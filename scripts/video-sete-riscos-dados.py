#!/usr/bin/env python3
"""Dados do vídeo "Sete riscos, um fiscal" (video/sete_riscos), lidos das fontes da casa.

Grava `video/sete_riscos/src/dados/sete_riscos.json`, que o Remotion importa e que o teste
`tests/test_video_sete_riscos.py` confere contra o roteiro. O esquema está em
`video/sete_riscos/CONTRATO.md`, seção 3. Nada é digitado à mão, salvo as constantes de
resolução declaradas abaixo (artigo ao lado, conferidas em `roteiro/fontes.md`); `fontes`
guarda o SHA-256 de todo arquivo lido.

Regras declaradas:

- Percentuais com duas casas. Voto em Lula e em Flávio sobre votos válidos (Flávio + Lula +
  terceira via), como no mapa de fiscais e no Politize.
- Riscos: tabela da seção 3 do contrato. Texto do risco vem do cenário de
  `fontes_fiscais.json`; a lei vem de `base_legal`, cujo texto se chama `conteudo` na fonte e
  vira `resumo` aqui; `pena` fica null quando a entrada não tem esse campo. Cada caso leva a
  primeira fonte da lista do caso que tenha URL (`veiculo`, `data` e `titulo` como na fonte).
  Id inexistente encerra o script com a mensagem do id.
- `balanco_mj`: números extraídos por expressão regular declarada (`REGEX_MJ`) do `resumo` e
  do `resultado` dos casos `mj_1t_2024` e `mj_1t_2022`; "1.170" vira 1170 e "R$ 638 mil" vira
  638000. Expressão que não casa encerra o script com a frase lida.
- `lei_fiscal` e `fechamento`: `texto` curto declarado (para o cartão do vídeo) e, quando a
  disposição está em `base_legal`, o `conteudo` de lá em `base_legal_conteudo`.
- Universo do país: o Politize (`docs/assets/politize/dados/zona/<UF>/<zona>.json`) tem uma
  linha por seção principal de todo o país (499.187), com contagens de voto; o mapa de fiscais
  só lista as seções com algum sinal (177.770). Por isso `lula_frente` lê o voto do Politize e
  completa nível, critérios e explicação pelo mapa quando a seção está nele. No mapa, a
  coluna `comparecimento` é a contagem de votantes (não percentual): comparecimento_pct =
  100 × votantes / aptos. O SHA-256 da pasta do Politize é um só, o SHA-256 da lista ordenada
  de linhas "caminho relativo<TAB>sha256 do arquivo" (`hash_pasta`).
- `lula_frente`: lula_pct >= 80, comparecimento_pct >= 95, aptos >= 100, fora do exterior (ZZ)
  e sem explicação de aldeia ou terra indígena, unidade prisional ou presídio e voto em
  trânsito (`EXCLUI_EXPLICACAO`). Além do contrato, exclui também o local cujo nome indica
  aldeia, escola indígena ou unidade prisional (`EXCLUI_LOCAL`): fora do capítulo 13 a seção
  não tem explicação escrita, e uma escola indígena não pode aparecer como motivação. Ordem:
  nível (alta, media, baixa, null; o nível "logs" do mapa conta como null), lula_pct
  decrescente, comparecimento decrescente, UF, zona, seção. Até 12. `secoes_lula_90` e
  `secoes_flavio_90` contam o país inteiro com aptos >= 100 e as mesmas exclusões.
- Exemplos e prédio: seção pelo mapa de fiscais, completada pelo capítulo 13 (`fiscais.json`),
  pela mesma função da masterclass (`exemplo`). `explicacao` é a explicação provável do
  capítulo 13 ou, fora dele, a do mapa. Voto do prédio somado nas seções do Politize do local.

Uso: python3 scripts/video-sete-riscos-dados.py
"""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SAIDA = ROOT / "video" / "sete_riscos" / "src" / "dados" / "sete_riscos.json"
FONTES_FISCAIS = ROOT / "analysis" / "apuracao_2026" / "fontes_fiscais.json"
PRESIDENTE = ROOT / "analysis" / "apuracao_2026" / "dados" / "presidente.json"
INDICE = ROOT / "docs" / "assets" / "fiscais_mapa" / "indice.json"
FISCAIS = ROOT / "analysis" / "apuracao_2026" / "dados" / "fiscais.json"
POLITIZE_ZONA = ROOT / "docs" / "assets" / "politize" / "dados" / "zona"
MALHA = ROOT / "apuracao" / "public" / "geo" / "br_uf.geojson"
QR = ROOT / "totalizacao" / "tests" / "fixtures" / "exemplos_tse_2026.json"
MASTERCLASS = SCRIPTS / "video-masterclass-dados.py"
FISCAIS_VIDEO = SCRIPTS / "video-fiscais-dados.py"
FAMILIAS = SCRIPTS / "apuracao_logs" / "familias.py"

# CONTRATO.md, seção 3: risco, cena, cenário em fontes_fiscais, casos (o primeiro é o
# principal) e ids de base_legal, nesta ordem.
RISCOS: tuple[tuple[str, str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("boca_urna", "risco-boca-de-urna", "boca_urna",
     ("paulista_pe_2020", "mj_1t_2024"), ("l9504_39_p5", "l9504_39a")),
    ("compra", "risco-compra", "compra",
     ("jackson_lago_2009", "mj_1t_2024"), ("l9504_41a", "ce_299")),
    ("transporte", "risco-transporte", "transporte",
     ("hornung_reserva_2004", "anchieta_sc_2012", "mj_1t_2024"), ("l6091_11", "l6091_5")),
    ("medo", "risco-medo", "medo",
     ("santa_quiteria_ce_faccao_2024", "trerj_locais_votacao_milicia_2024"),
     ("ce_301", "ce_23_xiv")),
    ("mesario", "risco-mesario", "mesario",
     ("itumbiara_2018", "paulista_pe_2020"), ("ce_309", "ce_132")),
    ("pianista", "risco-pianista", "pianista",
     ("pescaria_brava_2016", "doppelganger_macapa_2024"), ("ce_309", "res_23751_senhas")),
    ("totalizacao", "risco-totalizacao", "apuracao_papel",
     ("proconsult_rj_1982", "rj_1994_proporcional_anulada"),
     ("l9504_68", "res_23751_bu", "l9504_66")),
)  # fmt: skip
# Número que o roteiro cita em cada risco, tirado do balanço do MJ de 2024.
NUMEROS_MJ = {
    "boca_urna": "boca_urna",
    "compra": "compra",
    "transporte": "veiculos_transporte",
}

# Expressões declaradas para o balanço do MJ: (chave, campo do caso, expressão, conversão).
REGEX_MJ: dict[str, tuple[tuple[str, str, str, str], ...]] = {
    "mj_1t_2024": (
        ("boca_urna", "resumo", r"(\d[\d.]*) ocorrências de boca de urna", "int"),
        ("compra", "resumo", r"(\d[\d.]*) de compra de votos", "int"),
        ("veiculos_transporte", "resultado", r"(\d[\d.]*) veículos apreendidos", "int"),
        ("presos", "resultado", r"(\d[\d.]*) presos", "int"),
        ("apreendido_reais", "resumo", r"R\$ (\d[\d.]*) mil apreendidos", "mil"),
    ),
    "mj_1t_2022": (
        ("boca_urna", "resumo", r"com (\d[\d.]*) ocorrências", "int"),
        ("compra", "resumo", r"compra de votos (\d[\d.]*)", "int"),
        ("transporte", "resumo", r"transporte irregular (\d[\d.]*)", "int"),
        ("presos", "resultado", r"crimes eleitorais e (\d[\d.]*) prisões", "int"),
        ("crimes", "resultado", r"(\d[\d.]*) crimes eleitorais e", "int"),
    ),
}

RES = "Res. TSE 23.751/2026"
# Conferido em roteiro/fontes.md: textos curtos dos cartões, com o artigo ao lado.
LEI_FISCAL: tuple[tuple[str, str, str, str | None], ...] = (
    ("fiscalizar", "Fiscalizar todas as fases da votação e da apuração",
     "Lei 9.504/1997, art. 66", "l9504_66"),
    ("dois", "Até dois fiscais por partido em cada seção, um de cada vez",
     f"Lei 9.504/1997, art. 65, § 4º; {RES}, art. 175, § 1º", "l9504_65"),
    ("credencial", "A credencial é expedida pelo partido",
     f"Lei 9.504/1997, art. 65, § 2º; {RES}, art. 175, § 8º", "l9504_65"),
    ("impugnar", "Protestar e impugnar, inclusive a identidade do eleitor",
     f"Código Eleitoral, art. 132; {RES}, art. 176", "ce_132"),
    ("copia", "Receber cópia do boletim de urna no encerramento",
     f"Lei 9.504/1997, art. 68, § 1º; {RES}, art. 127, XV", "l9504_68"),
    ("ate_a_junta", "Acompanhar a urna e o material até a entrega na Junta",
     f"{RES}, art. 165", None),
)  # fmt: skip
# Conferido em roteiro/fontes.md: o encerramento da seção.
FECHAMENTO: tuple[tuple[str, str, str, str | None], ...] = (
    ("senhas", "Às 17h, quem está na fila recebe senha e vota",
     f"{RES}, art. 160, § 2º", "res_23751_senhas"),
    ("ultimos_dois",
     "As duas últimas pessoas a votar são convidadas a acompanhar o encerramento e recebem o boletim",
     f"{RES}, art. 160, § 1º", "res_23751_senhas"),
    ("bu_afixado", "Uma cópia do boletim de urna fica afixada na seção",
     f"{RES}, art. 127, IX", "res_23751_bu"),
    ("copia_no_encerramento", "A via do boletim é entregue a quem a requerer no encerramento",
     f"{RES}, art. 127, XV", "res_23751_bu"),
    ("comparar_depois",
     "Os boletins publicados podem ser comparados depois com os gerados nas seções",
     f"{RES}, art. 263", None),
)  # fmt: skip
CADASTRO = {
    "site": "fiscaisdopl.com.br",
    "prazo": "2026-10-24",
    "fonte": "fontes.md#fiscaisdopl",
}

# CONTRATO.md, seção 3: UF, zona e seção de cada exemplo nomeado.
EXEMPLOS: dict[str, tuple[str, int, int]] = {
    "tabatinga_am": ("AM", 36, 30),
    "baiao_pa": ("PA", 35, 238),
    "puc_sp": ("SP", 1, 257),
    "sao_joao_missoes_mg": ("MG", 166, 267),
    "marau_rs": ("RS", 62, 15),
    "porto_acre_ac": ("AC", 1, 621),
}
PREDIOS = ("RJ-60011-233-1414",)

LULA_MIN, COMP_MIN, APTOS_MIN, UNANIME, LISTA_MAX = 80.0, 95.0, 100, 90.0, 12
EXCLUI_EXPLICACAO = re.compile(
    r"aldeia|terra ind[ií]gena|prisional|pres[ií]dio|tr[aâ]nsito|exterior",
    re.IGNORECASE,
)
EXCLUI_LOCAL = re.compile(
    r"\bALDEIA\b|IND[IÍ]GENA|PRES[IÍ]DIO|PENITENCI|PRISIONAL|SOCIOEDUC|CADEIA P[UÚ]BLICA",
    re.IGNORECASE,
)
NIVEL_ORDEM = {"alta": 0, "media": 1, "baixa": 2}


def carregar(nome: str):
    """Importa um script de nome com hífen (scripts/ está no caminho) sem rodar o `main`."""
    return importlib.import_module(nome)


mc = carregar("video-masterclass-dados")
r2 = mc.r2


def hash_pasta(pasta: Path) -> str:
    """SHA-256 das linhas "caminho relativo<TAB>sha256", em ordem, dos .json da pasta."""
    linhas = [
        f"{p.relative_to(ROOT)}\t{hashlib.sha256(p.read_bytes()).hexdigest()}\n"
        for p in sorted(pasta.rglob("*.json"))
    ]
    return hashlib.sha256("".join(linhas).encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- urna


def bloco_urna(pres: dict) -> dict:
    n = pres["nacional"]
    return {
        "flavio_pct": r2(n["pct"]["flavio"]),
        "lula_pct": r2(n["pct"]["lula"]),
        "diferenca_pp": r2(n["diferenca_pp"]),
        "diferenca_votos": n["diferenca_votos"],
        "flavio_votos": n["votos"]["flavio"],
        "lula_votos": n["votos"]["lula"],
        "validos": n["validos"],
        "secoes": n["secoes"],
        "eleitores": n["eleitores"],
        "comparecimento": n["comparecimento"],
        "comparecimento_pct": r2(n["pct_comparecimento"]),
        "gerado_em": n["gerado_em"],
    }


# --------------------------------------------------------------------------- riscos e MJ


def _numero_mj(texto: str, conversao: str) -> int:
    n = int(texto.replace(".", ""))
    return n * 1000 if conversao == "mil" else n


def bloco_balanco(casos: dict) -> dict:
    saida = {}
    for caso_id, regras in REGEX_MJ.items():
        caso = casos.get(caso_id)
        if caso is None:
            raise SystemExit(f"balanço do MJ: caso {caso_id} não existe")
        bloco = {}
        for chave, campo, padrao, conversao in regras:
            achado = re.search(padrao, caso[campo])
            if not achado:
                raise SystemExit(
                    f"{caso_id}.{campo}: '{padrao}' não casa com: {caso[campo]}"
                )
            bloco[chave] = _numero_mj(achado[1], conversao)
        bloco["fonte_caso"] = caso_id
        saida[caso_id.removeprefix("mj_")] = bloco
    return saida


def _fonte_do_caso(caso: dict, fontes: dict) -> dict:
    for fid in caso["fontes"]:
        f = fontes.get(fid)
        if f is None:
            raise SystemExit(f"caso {caso['id']}: fonte {fid} não existe")
        if f.get("url"):
            fonte = {k: f.get(k) for k in ("id", "url", "veiculo", "data", "titulo")}
            # Página sem data de publicação: `data` é a data de acesso, e a tela diz isso.
            fonte["data_e_acesso"] = "data de acesso" in (f.get("como_conferido") or "")
            return fonte
    raise SystemExit(f"caso {caso['id']}: nenhuma fonte com URL")


def _lei(lid: str, base: dict) -> dict:
    item = base.get(lid)
    if item is None:
        raise SystemExit(f"base_legal: id {lid} não existe")
    return {
        "id": lid,
        "norma": item["norma"],
        "dispositivo": item["dispositivo"],
        "resumo": item["conteudo"],
        "pena": item.get("pena"),
    }


def bloco_riscos(ff: dict, balanco: dict) -> list[dict]:
    cenarios = {c["id"]: c for c in ff["cenarios"]}
    casos = {c["id"]: c for c in ff["casos"]}
    base = {b["id"]: b for b in ff["base_legal"]}
    fontes = {f["id"]: f for f in ff["fontes"]}
    saida = []
    for rid, cena, cid, caso_ids, lei_ids in RISCOS:
        cen = cenarios.get(cid)
        if cen is None:
            raise SystemExit(f"risco {rid}: cenário {cid} não existe")
        lista = []
        for caso_id in caso_ids:
            caso = casos.get(caso_id)
            if caso is None:
                raise SystemExit(f"risco {rid}: caso {caso_id} não existe")
            lista.append(
                {
                    "id": caso_id,
                    "ano": caso["ano"],
                    "data": caso.get("data"),
                    "titulo": caso["titulo"],
                    "local": caso["local"],
                    "instancia": caso["instancia"],
                    "resultado_curto": caso.get("resultado_curto"),
                    "resultado": caso["resultado"],
                    "rotulo_curto": caso.get("rotulo_curto"),
                    "rotulo": caso.get("rotulo"),
                    "fonte": _fonte_do_caso(caso, fontes),
                }
            )
        numeros = (
            {"mj_1t_2024": balanco["1t_2024"][NUMEROS_MJ[rid]]}
            if "mj_1t_2024" in caso_ids and rid in NUMEROS_MJ
            else {}
        )
        saida.append(
            {
                "id": rid,
                "cena": cena,
                "cenario": cid,
                "nome": cen["nome"],
                "familia": cen["familia"],
                "o_que_e": cen["o_que_e"],
                "como_aparece": cen["como_aparece"],
                "sinal": cen["sinal"],
                "sinal_texto": cen["sinal_texto"],
                "confere": cen["confere"],
                "confere_curto": cen.get("confere_curto"),
                "lei": [_lei(lid, base) for lid in lei_ids],
                "casos": lista,
                "numeros": numeros,
            }
        )
    return saida


def bloco_textos(itens, base: dict) -> list[dict]:
    saida = []
    for iid, texto, referencia, lid in itens:
        if lid is not None and lid not in base:
            raise SystemExit(f"base_legal: id {lid} não existe")
        saida.append(
            {
                "id": iid,
                "texto": texto,
                "referencia": referencia,
                "base_legal": lid,
                "base_legal_conteudo": base[lid]["conteudo"] if lid else None,
            }
        )
    return saida


# --------------------------------------------------------------------------- seções


def ler_politize(fontes) -> dict:
    """Uma linha por seção principal do país, pela chave (UF, zona, seção)."""
    fontes.hashes[str(POLITIZE_ZONA.relative_to(ROOT))] = hash_pasta(POLITIZE_ZONA)
    saida = {}
    for arquivo in sorted(POLITIZE_ZONA.rglob("*.json")):
        z = json.loads(arquivo.read_text(encoding="utf-8"))
        nomes = {m["mun_tse"]: m["nome"] for m in z["municipios"]}
        colunas = z["secoes"]["colunas"]
        for linha in z["secoes"]["linhas"]:
            s = dict(zip(colunas, linha, strict=True))
            s["municipio"] = nomes.get(s["mun_tse"])
            saida[(z["uf"], int(z["zona"]), s["secao"])] = s
    return saida


def mapa_todo(mapa, partes) -> dict:
    saida = {}
    for uf in partes:
        for s in mapa.uf(uf)["secoes"]:
            saida[(uf, s["local"]["zona"], s["secao"])] = s
    return saida


def _pct(p: dict, chave: str) -> float | None:
    validos = sum(p[k] or 0 for k in ("flavio", "lula", "terceira"))
    return 100 * (p[chave] or 0) / validos if validos else None


def _excluida(chave: tuple, p: dict, m: dict | None, cap13: dict) -> bool:
    if chave[0] == "ZZ":
        return True
    c13 = cap13.get(chave) or {}
    explicacoes = (c13.get("explicacao_provavel"), m and m["explicacao"])
    if any(e and EXCLUI_EXPLICACAO.search(e) for e in explicacoes):
        return True
    nomes = [p.get("local") or "", p.get("bairro") or ""]
    if m:
        nomes += [m["local"]["local"] or "", m["local"]["bairro"] or ""]
    return any(EXCLUI_LOCAL.search(n) for n in nomes)


def bloco_lula_frente(politize: dict, secoes_mapa: dict, cap13: dict) -> dict:
    lula_90 = flavio_90 = 0
    candidatas = []
    for chave, p in politize.items():
        aptos = p["aptos"] or 0
        lula, flavio = _pct(p, "lula"), _pct(p, "flavio")
        if aptos < APTOS_MIN or lula is None:
            continue
        m = secoes_mapa.get(chave)
        if _excluida(chave, p, m, cap13):
            continue
        lula_90 += lula >= UNANIME
        flavio_90 += flavio >= UNANIME
        comp = 100 * (p["comparecimento"] or 0) / aptos
        if lula < LULA_MIN or comp < COMP_MIN:
            continue
        c13 = cap13.get(chave) or {}
        nivel = mc._nivel(c13.get("nivel") or (m and m["nivel"]))
        candidatas.append(
            {
                "uf": chave[0],
                "municipio": p["municipio"],
                "zona": chave[1],
                "secao": chave[2],
                "local_id": p["local_id"],
                "local": p["local"],
                "bairro": p["bairro"],
                "aptos": aptos,
                "votantes": p["comparecimento"],
                "comparecimento_pct": r2(comp),
                "lula_pct": r2(lula),
                "flavio_pct": r2(flavio),
                "nivel": nivel,
                "criterios": c13.get("criterios") or list((m and m["criterios"]) or ""),
                "explicacao": c13.get("explicacao_provavel") or (m and m["explicacao"]),
                "no_mapa": m is not None,
            }
        )
    candidatas.sort(
        key=lambda s: (
            NIVEL_ORDEM.get(s["nivel"], 3),
            -s["lula_pct"],
            -s["comparecimento_pct"],
            s["uf"],
            s["zona"],
            s["secao"],
        )
    )
    return {
        "secoes_lula_90": lula_90,
        "secoes_lula_80_comp_95": len(candidatas),
        "secoes_flavio_90": flavio_90,
        "regra": (
            f"lula_pct >= {LULA_MIN:g}, comparecimento_pct >= {COMP_MIN:g}, aptos >= "
            f"{APTOS_MIN}, fora do exterior e sem aldeia, terra indígena, unidade prisional "
            "ou voto em trânsito (pela explicação ou pelo nome do local); ordem por nível e "
            "por lula_pct"
        ),
        "lista": candidatas[:LISTA_MAX],
    }


def _exemplo(chave, mapa, cap13, familias, nomes, projetar) -> dict:
    m = mapa.secao(*chave)
    c13 = cap13.get(chave)
    e = mc.exemplo(m, c13, familias, nomes, projetar)
    e["explicacao"] = (c13 or {}).get("explicacao_provavel") or m["explicacao"]
    return e


def bloco_exemplos(mapa, cap13, frente, familias, nomes, projetar) -> dict:
    alvos = dict(EXEMPLOS)
    for i, s in enumerate(frente["lista"][:3], start=1):
        alvos[f"frente_{i}"] = (s["uf"], s["zona"], s["secao"])
    return {
        k: _exemplo(v, mapa, cap13, familias, nomes, projetar) for k, v in alvos.items()
    }


def bloco_predios(mapa, politize: dict, familias, projetar) -> list[dict]:
    saida = []
    for local_id in PREDIOS:
        local, secoes = mapa.local(local_id)
        por_atencao = {str(k): 0 for k in range(4)}
        sem_log = 0
        for s in secoes:
            if s["atencao"] is None:
                sem_log += 1
            else:
                por_atencao[str(s["atencao"])] += 1
        do_local = [p for p in politize.values() if p["local_id"] == local_id]
        if len(do_local) != local["secoes_total"]:
            raise SystemExit(
                f"{local_id}: {len(do_local)} seções no Politize, "
                f"{local['secoes_total']} no mapa"
            )
        votos = {k: sum(p[k] or 0 for p in do_local) for k in ("flavio", "lula")}
        validos = sum(
            p[k] or 0 for p in do_local for k in ("flavio", "lula", "terceira")
        )
        saida.append(
            {
                "local_id": local_id,
                "uf": local["uf"],
                "municipio": local["municipio"],
                "zona": local["zona"],
                "local": local["local"],
                "endereco": local["endereco"],
                "bairro": local["bairro"],
                "secoes_total": local["secoes_total"],
                "aptos_total": local["aptos_total"],
                "votantes_total": sum(p["comparecimento"] or 0 for p in do_local),
                "lula_pct": r2(100 * votos["lula"] / validos),
                "flavio_pct": r2(100 * votos["flavio"] / validos),
                "risco": mc._risco(local["risco"]),
                "risco_motivos": local["risco_motivos"] or [],
                "secoes_listadas": len(secoes),
                "por_atencao": por_atencao,
                "sem_log": sem_log,
                "xy": projetar(local["lon"], local["lat"]),
                "secoes": [
                    {
                        "secao": s["secao"],
                        "nivel": mc._nivel(s["nivel"]),
                        "criterios": list(s["criterios"] or ""),
                        "atencao": s["atencao"],
                        "logs": s["logs"] or [],
                        "logs_nomes": [familias.NOME_CURTO[c] for c in s["logs"] or []],
                        "aptos": s["aptos"],
                        "comparecimento": s["comparecimento"],
                        "flavio_pct": r2(s["flavio_pct"]),
                        "lula_pct": r2(s["lula_pct"]),
                    }
                    for s in secoes
                ],
            }
        )
    return saida


# --------------------------------------------------------------------------- main


def main() -> None:
    fontes = mc.Fontes()
    fontes.marcar(MASTERCLASS)
    ff = fontes.json(FONTES_FISCAIS)
    pres = fontes.json(PRESIDENTE)
    indice = fontes.json(INDICE)
    fiscais = fontes.json(FISCAIS)
    malha = fontes.json(MALHA)
    familias = mc.modulo("apuracao_logs.familias", FAMILIAS, fontes)
    fontes.marcar(FISCAIS_VIDEO)
    fiscais_video = carregar("video-fiscais-dados")
    mapa = mc.MapaUF(indice, fontes)
    cap13 = {(s["uf"], s["zona"], s["secao"]): s for s in fiscais["secoes"]}
    nomes = {c["id"]: c["nome"] for c in fiscais["criterios"]}
    politize = ler_politize(fontes)
    secoes_mapa = mapa_todo(mapa, indice["partes"])
    base = {b["id"]: b for b in ff["base_legal"]}
    casos = {c["id"]: c for c in ff["casos"]}

    balanco = bloco_balanco(casos)
    frente = bloco_lula_frente(politize, secoes_mapa, cap13)
    sinal = mc.bloco_sinalizadas(fiscais)
    saida = {
        "gerado_em": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fontes": {},
        "rotulos": indice["rotulos"],
        "urna": bloco_urna(pres),
        "riscos": bloco_riscos(ff, balanco),
        "balanco_mj": balanco,
        "lei_fiscal": bloco_textos(LEI_FISCAL, base),
        "fechamento": bloco_textos(FECHAMENTO, base),
        "exemplos": bloco_exemplos(
            mapa, cap13, frente, familias, nomes, fiscais_video.projetar
        ),
        "lula_frente": frente,
        "predios": bloco_predios(mapa, politize, familias, fiscais_video.projetar),
        "sinalizadas": {
            k: sinal[k] for k in ("secoes", "locais", "alta", "media", "baixa")
        },
        "logs": {
            "processados": indice["logs"]["cobertura"]["processados"],
            "atencao": dict(indice["resumo"]["atencao"]),
        },
        "mapa": mc.bloco_mapa(malha, fiscais_video),
        "totalizacao": {"exemplos_oficiais": len(fontes.json(QR)["exemplos"])},
        "cadastro": CADASTRO,
    }
    saida["fontes"] = dict(sorted(fontes.hashes.items()))
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(
        json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    resumo(saida)


def resumo(s: dict) -> None:
    print(f"{SAIDA.relative_to(ROOT)}: {SAIDA.stat().st_size // 1024} KB, ", end="")
    print(f"{len(s['fontes'])} fontes com SHA-256")
    print(f"  urna: {json.dumps(s['urna'], ensure_ascii=False)}")
    for r in s["riscos"]:
        c = r["casos"][0]
        print(f"  risco {r['id']}: {c['id']} ({c['ano']}) {c['fonte']['url']}")
    print(f"  balanco_mj: {json.dumps(s['balanco_mj'], ensure_ascii=False)}")
    f = s["lula_frente"]
    print(
        f"  lula_frente: lula_90={f['secoes_lula_90']} flavio_90={f['secoes_flavio_90']} "
        f"lula_80_comp_95={f['secoes_lula_80_comp_95']}"
    )
    for x in f["lista"]:
        print(
            f"    {x['uf']} {x['municipio']} z{x['zona']} s{x['secao']} lula={x['lula_pct']} "
            f"comp={x['comparecimento_pct']} nivel={x['nivel']} {x['local']}"
        )
    for chave, e in s["exemplos"].items():
        print(
            f"  exemplo {chave}: {e['uf']} {e['municipio']} z{e['zona']} s{e['secao']} "
            f"lula={e['lula_pct']} flavio={e['flavio_pct']} comp={e['comparecimento_pct']} "
            f"nivel={e['nivel']}"
        )
    for p in s["predios"]:
        print(
            f"  prédio {p['local_id']} {p['local']}: {p['secoes_total']} seções, "
            f"lula {p['lula_pct']} flavio {p['flavio_pct']}, por atenção {p['por_atencao']}"
        )
    print(f"  sinalizadas: {s['sinalizadas']} logs: {s['logs']}")


if __name__ == "__main__":
    main()
