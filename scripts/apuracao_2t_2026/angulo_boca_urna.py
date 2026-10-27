"""Ângulo da boca de urna e da pressão sobre o eleitor no 2º turno de 2026.

A totalização não registra abordagem de eleitor: nenhum BU, log ou RDV mede essa
conduta. O que existe é documento, e este módulo reúne três camadas dele:

1. **Canal de relatos da casa** (Politize-se, tabela ``relato_secao`` no Supabase):
   só contagens por status de moderação, por UF e por tipo; nenhum texto, contato
   ou hash sai daqui. Acesso pelo token do CLI do Supabase no keychain
   (``politize_se.relatos``); o token nunca é impresso nem gravado.
2. **Ocorrências públicas do dia**, lidas de ``noticias_noite.json`` e das duas
   páginas oficiais do MJSP arquivadas em ``noticias_fontes/`` com SHA-256,
   separadas em registro oficial, relato de imprensa e relato anônimo por regra
   declarada (``classificar``).
3. **O caminho documental**: o que a Lei 9.504/1997 define (art. 39, § 5º, e
   art. 39-A) e o que a Resolução TSE 23.751/2026 mandou registrar na Ata da
   Mesa Receptora, lidos dos arquivos de ``data/originals/apuracao_2026/fiscais/``.

Rótulo de tudo: relato pede explicação, não prova irregularidade; contagem não
é verificação.
"""

from __future__ import annotations

import hashlib
import html as _html
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MEMOS = ROOT / "analysis/apuracao_2t_2026"
DADOS = MEMOS / "dados"
NOTICIAS = MEMOS / "noticias_noite.json"
FONTES_NOTICIAS = MEMOS / "noticias_fontes"
FONTES_FISCAIS = ROOT / "analysis/apuracao_2026/fontes_fiscais.json"
ORIGINAIS_FISCAIS = ROOT / "data/originals/apuracao_2026/fiscais"
SAIDA_JSON = DADOS / "angulo_boca_urna.json"
SAIDA_MD = DADOS / "angulo_boca_urna.md"
ROTULO = "relato pede explicação, não prova irregularidade; contagem não é verificação"

TIPOS_RELATO = [
    "fila_longa",
    "urna_trocada",
    "biometria_falhou",
    "votou_sem_biometria",
    "mesario_conduta",
    "boca_de_urna",
    "transporte_irregular",
    "local_mudou",
    "secao_fechou_cedo",
    "secao_fechou_tarde",
    "outro",
]
STATUS_RELATO = ["novo", "lido", "descartado"]
TIPOS_PRESSAO = ("boca_de_urna", "mesario_conduta", "transporte_irregular")

# ------------------------------------------------------------ ocorrências públicas

TEMAS_SEMPRE = {"ocorrencias_policiais", "boca_de_urna", "violencia_politica"}
PALAVRAS = re.compile(
    r"boca de urna|venda de voto|compra de voto|alicia|coa[çc]|pris[ãa]o|pres[oa]s?\b"
    r"|prend|detid|flagrante|apreen|crimes? eleitora",
    re.IGNORECASE,
)
OFICIAL = re.compile(
    r"\bPM\b|Pol[íi]cia|\bPF\b|\bPRF\b|\bTRE\b|TRE-|\bTSE\b|Minist[ée]rio da Justi"
    r"|Justi[çc]a Eleitoral|\b[Jj]ui[zí]|corregedor|Guarda Civil|\bGCM\b|governador"
    r"|\bMJSP\b|\bSTF\b|Zona Eleitoral",
)
ANONIMO = re.compile(r"an[ôo]nim|fonte reservada|sem identifica", re.IGNORECASE)
SUBTEMAS = [
    ("boca_de_urna", re.compile(r"boca de urna", re.IGNORECASE)),
    (
        "sigilo_ou_venda_do_voto",
        re.compile(r"venda de voto|fotograf|celular|sigilo", re.IGNORECASE),
    ),
    ("violencia", re.compile(r"atacad|agred|agress|nazist|inj[úu]ria", re.IGNORECASE)),
    ("transporte", re.compile(r"[ôo]nibus|transporte|frota|SPTrans", re.IGNORECASE)),
    ("balanco", re.compile(r"balan[çc]o|ocorr[êe]ncias", re.IGNORECASE)),
]

# Balanços do CICCN/MJSP transcritos das páginas arquivadas (gov.br/mj e Agência
# Brasil). Os percentuais são do próprio balanço; a contagem absoluta de boca de urna
# é derivada aqui (percentual × total) e vai marcada como tal.
BALANCOS_MJSP = [
    {
        "id": "mjsp_12h",
        "corte": "25/10/2026, relatório do CICCN das 12h (Brasília)",
        "publicado": "gov.br/mj, 25/10/2026 14h09 (atualizado 26/10 09h56)",
        "arquivo": "mj_seguranca-monitorada-tempo-real.html",
        "url": "https://www.gov.br/mj/pt-br/assuntos/noticias/segundo-turno-das-eleicoes-ocorre-com-a-seguranca-monitorada-em-tempo-real",
        "ocorrencias": 89,
        "flagrantes": 9,
        "termos_circunstanciados": 16,
        "conduzidos": 16,
        "boca_de_urna_pct": None,
        "nota": "sem divisão por tipo; a pasta cita a propaganda irregular como a principal questão",
    },
    {
        "id": "mjsp_19h",
        "corte": "25/10/2026, balanço preliminar do MJSP até as 19h",
        "publicado": "Agência Brasil, 25/10/2026 19h37",
        "arquivo": "ab_pf-vai-apurar-ataque-vereadora.html",
        "url": "https://agenciabrasil.ebc.com.br/politica/noticia/2026-10/pf-vai-apurar-ataque-vereadora-de-montes-claros-diz-diretor-geral",
        "ocorrencias": 618,
        "flagrantes": 57,
        "termos_circunstanciados": None,
        "conduzidos": 152,
        "boca_de_urna_pct": 13.3,
        "propaganda_irregular_pct": 11.3,
        "outros_crimes_eleitorais_pct": 7.6,
        "desordem_pct": 7.4,
        "desobediencia_pct": 6.6,
        "ufs_mais_ocorrencias": {"MG": 91, "RS": 59, "GO": 48, "MT": 42},
        "apreensoes": "R$ 1.897 em dinheiro, 9 veículos e 1 arma de fogo",
        "nota": "preliminar; a mesma matéria registra que a PF chamou de mais grave o ataque em Montes Claros",
    },
    {
        "id": "mjsp_final",
        "corte": "2º turno completo, relatório do CICCN",
        "publicado": "gov.br/mj, 26/10/2026 20h01",
        "arquivo": "mj_balanco-operacoes-seguranca-2o-turno.html",
        "url": "https://www.gov.br/mj/pt-br/assuntos/noticias/ministerio-da-justica-divulga-balanco-das-operacoes-de-seguranca-no-segundo-turno-das-eleicoes",
        "ocorrencias": 733,
        "flagrantes": 61,
        "termos_circunstanciados": 254,
        "conduzidos": 173,
        "boca_de_urna_pct": 12.8,
        "sigilo_do_voto_pct": 39.1,
        "propaganda_irregular_pct": 10.4,
        "outros_crimes_eleitorais_pct": 9.6,
        "apreensoes": "1 arma de fogo, 864 materiais de campanha, 10 veículos e R$ 1.897 em espécie",
        "nota": "a pasta diz que o total de ocorrências criminais foi menor que no 1º turno, sem publicar o número do 1º turno nesta página",
    },
]

# ------------------------------------------------------------------ base legal

LEI_9504 = {
    "arquivo": "lei_9504.html",
    "fonte_id": "planalto_9504",
    "dispositivos": [
        {
            "dispositivo": "art. 39, § 5º, II",
            "texto": "É crime, no dia da eleição, a arregimentação de eleitor ou a propaganda de boca de urna, com detenção de seis meses a um ano, alternativa de prestação de serviços à comunidade pelo mesmo período e multa de 5.000 a 15.000 UFIR (redação da Lei 11.300/2006). O inciso I alcança alto-falantes, comício e carreata; o III, a divulgação de propaganda de partidos ou candidatos.",
            "trecho_conferido": "a arregimentação de eleitor ou a propaganda de boca de urna",
        },
        {
            "dispositivo": "art. 39-A",
            "texto": "É permitida a manifestação individual e silenciosa da preferência do eleitor, só por bandeira, broche, dístico e adesivo. É vedada, até o fim da votação, a aglomeração com vestuário padronizado ou esses instrumentos de modo a caracterizar manifestação coletiva. Fiscais só podem ter nome e sigla no crachá.",
            "trecho_conferido": "manifestação individual e silenciosa da preferência do eleitor",
        },
    ],
}
RES_23751 = {
    "arquivo": "p360_atos_gerais_2026.pdf",
    "fonte_id": "dje_res_23751",
    "publicacao": "DJE/TSE n. 30, 03/03/2026",
    "dispositivos": [
        {
            "dispositivo": "art. 126, VIII a X",
            "texto": "Cabe ao presidente da mesa manter a ordem na seção, dispondo de força pública (CE, art. 127, III); comunicar ao juiz eleitoral as ocorrências cuja solução dele dependa (CE, art. 127, VI); e receber as impugnações de fiscais e de qualquer eleitor, consignando-as na Ata da Mesa Receptora (CE, art. 127, VII).",
            "trecho_conferido": "manter a ordem na seção, para o que disporá de força pública",
        },
        {
            "dispositivo": "art. 128, V",
            "texto": "Cabe aos mesários lavrar a Ata da Mesa Receptora, anotando, durante os trabalhos, todas as ocorrências que se verificarem (CE, art. 128, II).",
            "trecho_conferido": "todas as ocorrências que se verificarem",
        },
        {
            "dispositivo": "art. 137, § 5º",
            "texto": "Quem recusa entregar celular ou câmera não vota; o presidente faz constar em ata os detalhes e, se preciso, aciona a força policial e comunica o juiz.",
            "trecho_conferido": "acionará a força policial para adoção das",
        },
        {
            "dispositivo": "art. 161",
            "texto": "Encerrada a votação, o presidente finaliza a Ata da Mesa Receptora, da qual constam, sem prejuízo de outras ocorrências significativas, ao menos os itens listados (CE, art. 154, III).",
            "trecho_conferido": "sem prejuízo de outras ocorrências significativas",
        },
        {
            "dispositivo": "arts. 176 e 177",
            "texto": "Candidatos, delegados e fiscais são admitidos a fiscalizar a votação, formular protestos e fazer impugnações (CE, art. 132). No dia da votação o fiscal usa crachá só com nome e sigla, vedada a padronização do vestuário (Lei 9.504, art. 39-A, § 3º).",
            "trecho_conferido": "a formular protestos e a fazer impugnações",
        },
    ],
}

CAMINHO_DOCUMENTAL = [
    {
        "passo": "Na seção, na hora",
        "quem": "qualquer eleitor, fiscal ou delegado de partido",
        "como": "pede ao presidente da mesa que registre a ocorrência na Ata da Mesa Receptora (Res. 23.751, art. 128, V); fiscal pode formular protesto e impugnação (art. 176); o presidente pode chamar a força pública e comunica o juiz eleitoral (art. 126, VIII e IX).",
        "vira": "Ata da Mesa Receptora, que acompanha o BU até a Junta Eleitoral (art. 161).",
        "fonte": "Resolução TSE 23.751/2026, PDF arquivado",
    },
    {
        "passo": "Fora da seção, no mesmo dia",
        "quem": "qualquer pessoa, pela polícia que estiver no local ou na delegacia",
        "como": "boca de urna é crime do dia da eleição (Lei 9.504, art. 39, § 5º, II); a polícia lavra auto de prisão em flagrante ou termo circunstanciado e conduz à autoridade. São esses registros que o CICCN/MJSP soma no balanço.",
        "vira": "boletim de ocorrência, auto de prisão em flagrante ou termo circunstanciado, encaminhados ao juiz eleitoral.",
        "fonte": "Lei 9.504/1997 arquivada; balanço do MJSP de 26/10/2026",
    },
    {
        "passo": "Depois do dia",
        "quem": "eleitor, partido ou Ministério Público Eleitoral",
        "como": "representação ao juiz eleitoral da zona ou ouvidoria do TRE da UF; os endereços e prazos de cada TRE não foram conferidos nesta rodada.",
        "vira": "procedimento na Justiça Eleitoral, com número e andamento públicos.",
        "fonte": "não conferida nesta rodada",
    },
    {
        "passo": "Canal da casa",
        "quem": "quem votou e notou algo na própria seção",
        "como": "bloco 'Notou algo na sua seção?' na ficha da seção do Politize-se, tipo 'boca_de_urna' ou 'mesario_conduta', texto de até 1.000 caracteres, hora aproximada e se presenciou. Relato anônimo por padrão; contato só se informado; texto nunca publicado.",
        "vira": "linha imutável em relato_secao, contada nas views públicas por UF, tipo e seção; moderação registrada em relato_moderacao. Não substitui a ata nem o boletim de ocorrência.",
        "fonte": "analysis/politize_se/CONTRATO.md, seção Relatos; migrações 0005 e 0006",
    },
]


# ------------------------------------------------------------------ utilidades


def sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def agora_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def texto_html(caminho: Path) -> str:
    """Texto corrido de uma página arquivada, sem script, estilo nem marcação."""
    bruto = caminho.read_bytes()
    try:
        t = bruto.decode("utf-8")
    except UnicodeDecodeError:  # páginas do Planalto são latin-1
        t = bruto.decode("latin-1")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.DOTALL)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", t))
    return re.sub(r"\s+", " ", t)


def derivado_boca_de_urna(b: dict[str, Any]) -> int | None:
    """Contagem aproximada de boca de urna = percentual publicado × total, arredondado."""
    pct = b.get("boca_de_urna_pct")
    if pct is None or not b.get("ocorrencias"):
        return None
    return round(b["ocorrencias"] * pct / 100)


# --------------------------------------------------------------- canal de relatos

SQL_CONTAGENS = """
select 'total' as k, '' as v, count(*)::int as n from relato_secao
union all select 'status', status::text, count(*)::int from relato_secao group by status
union all select 'tipo', tipo::text, count(*)::int from relato_secao group by tipo
union all select 'uf', uf, count(*)::int from relato_secao group by uf
union all select 'turno', turno::text, count(*)::int from relato_secao group by turno
union all select 'presenciou', presenciou::text, count(*)::int from relato_secao
  group by presenciou
union all select 'cadastro', secao_no_cadastro::text, count(*)::int from relato_secao
  group by secao_no_cadastro
union all select 'moderacao', para::text, count(*)::int from relato_moderacao group by para
union all select 'primeiro', to_char(min(criado_em) at time zone 'UTC', 'YYYY-MM-DD HH24"h"'),
  0 from relato_secao
union all select 'ultimo', to_char(max(criado_em) at time zone 'UTC', 'YYYY-MM-DD HH24"h"'),
  0 from relato_secao
order by 1, 2
""".strip()


def _consultar_supabase() -> list[dict]:
    from politize_se import relatos

    return relatos.consultar(SQL_CONTAGENS, relatos.token_cli())


def organizar_contagens(linhas: list[dict], consultado_em: str) -> dict[str, Any]:
    """Transforma as linhas (k, v, n) em contagens completas; zero onde não há relato."""
    por: dict[str, dict[str, int]] = {}
    marcos: dict[str, str | None] = {"primeiro": None, "ultimo": None}
    total = 0
    for x in linhas:
        k, v, n = x["k"], x["v"], int(x["n"])
        if k == "total":
            total = n
        elif k in marcos:
            marcos[k] = v or None
        else:
            por.setdefault(k, {})[v] = n
    por_tipo = {t: por.get("tipo", {}).get(t, 0) for t in TIPOS_RELATO}
    por_status = {s: por.get("status", {}).get(s, 0) for s in STATUS_RELATO}
    return {
        "consultado_em": consultado_em,
        "fonte": "Supabase PNAD, tabelas relato_secao e relato_moderacao, só contagens",
        "total": total,
        "por_status": por_status,
        "por_tipo": por_tipo,
        "por_uf": dict(sorted(por.get("uf", {}).items())),
        "por_turno": dict(sorted(por.get("turno", {}).items())),
        "presenciou": {
            "sim": por.get("presenciou", {}).get("true", 0),
            "nao": por.get("presenciou", {}).get("false", 0),
        },
        "secao_no_cadastro": {
            "sim": por.get("cadastro", {}).get("true", 0),
            "nao": por.get("cadastro", {}).get("false", 0),
        },
        "moderacao_por_destino": dict(sorted(por.get("moderacao", {}).items())),
        "pressao_sobre_o_eleitor": sum(por_tipo[t] for t in TIPOS_PRESSAO),
        "ativos": total - por_status["descartado"],
        "primeiro_relato_utc_hora": marcos["primeiro"],
        "ultimo_relato_utc_hora": marcos["ultimo"],
        "limites": [
            "contagem de declarações de quem enviou; nenhuma foi verificada por documento",
            "texto, contato, hora exata e hash nunca saem do banco para este arquivo",
            "o canal abriu em 26/10/2026, depois do dia da votação",
        ],
    }


def relatos_contagens(consulta=_consultar_supabase) -> dict[str, Any]:
    """Contagens do canal de relatos; se o acesso falhar, registra o erro e segue."""
    quando = agora_utc()
    try:
        linhas = consulta()
    except Exception as e:  # o motivo vira registro, não parada
        return {
            "consultado_em": quando,
            "erro": f"{type(e).__name__}: {str(e)[:160]}",
            "fonte": "Supabase PNAD, tabela relato_secao (acesso falhou)",
        }
    return organizar_contagens(linhas, quando)


# ------------------------------------------------------------ ocorrências do dia


def classificar(item: dict[str, Any]) -> str:
    """registro_oficial, relato_imprensa ou relato_anonimo, por regra declarada.

    Oficial quando quem disse é polícia, Justiça Eleitoral, MJSP, governo ou juízo.
    Anônimo quando a fonte é declarada anônima ou reservada. O resto é imprensa,
    inclusive partido ou campanha falando pela boca de um veículo.
    """
    quem = item.get("quem_disse") or ""
    if ANONIMO.search(quem):
        return "relato_anonimo"
    if OFICIAL.search(quem):
        return "registro_oficial"
    return "relato_imprensa"


def subtema(item: dict[str, Any]) -> str:
    texto = f"{item.get('titulo', '')} {item.get('resumo', '')}"
    for nome, rx in SUBTEMAS:
        if rx.search(texto):
            return nome
    return "outro"


def pertinente(item: dict[str, Any]) -> bool:
    if item.get("tema") in TEMAS_SEMPRE:
        return True
    return bool(PALAVRAS.search(f"{item.get('titulo', '')} {item.get('resumo', '')}"))


def ocorrencias_publicas(noticias: dict[str, Any]) -> dict[str, Any]:
    itens = []
    for it in noticias["itens"]:
        if not pertinente(it):
            continue
        itens.append(
            {
                "quando": it["quando"],
                "veiculo": it["veiculo"],
                "titulo": it["titulo"],
                "url": it["url"],
                "tipo_acervo": it["tipo"],
                "tema_acervo": it.get("tema"),
                "subtema": subtema(it),
                "classe": classificar(it),
                "quem_disse": it.get("quem_disse"),
                "resumo": it["resumo"],
                "fonte_arquivo": it.get("fonte_arquivo"),
                "sha256": it.get("sha256"),
            }
        )
    itens.sort(key=lambda x: x["quando"])
    classes = dict.fromkeys(
        ("registro_oficial", "relato_imprensa", "relato_anonimo"), 0
    )
    subtemas: dict[str, int] = {}
    for x in itens:
        classes[x["classe"]] += 1
        subtemas[x["subtema"]] = subtemas.get(x["subtema"], 0) + 1
    return {
        "fonte": str(NOTICIAS.relative_to(ROOT)),
        "gerado_em_acervo": noticias.get("gerado_em"),
        "regra": (
            "entram os itens de tema ocorrencias_policiais, boca_de_urna e "
            "violencia_politica, mais qualquer item cujo título ou resumo cite boca de "
            "urna, venda ou compra de voto, aliciamento, coação, prisão, detenção, "
            "flagrante, apreensão ou crime eleitoral"
        ),
        "n": len(itens),
        "por_classe": classes,
        "por_subtema": dict(sorted(subtemas.items())),
        "boca_de_urna_nominais": [x for x in itens if x["subtema"] == "boca_de_urna"],
        "itens": itens,
    }


def balancos() -> list[dict[str, Any]]:
    saida = []
    for b in BALANCOS_MJSP:
        caminho = FONTES_NOTICIAS / b["arquivo"]
        texto = texto_html(caminho) if caminho.exists() else ""
        conferido = bool(texto) and str(b["ocorrencias"]) in texto
        saida.append(
            {
                **b,
                "boca_de_urna_n_derivado": derivado_boca_de_urna(b),
                "fonte_arquivo": str(
                    (FONTES_NOTICIAS / b["arquivo"]).relative_to(ROOT)
                ),
                "sha256": sha256(caminho) if caminho.exists() else None,
                "total_conferido_no_arquivo": conferido,
            }
        )
    return saida


# ------------------------------------------------------------------ base legal


def base_legal() -> dict[str, Any]:
    fontes = {}
    if FONTES_FISCAIS.exists():
        ff = json.loads(FONTES_FISCAIS.read_text(encoding="utf-8"))
        fontes = {f["id"]: f for f in ff["fontes"]}
    saida = {}
    for nome, norma in (("lei_9504", LEI_9504), ("res_23751", RES_23751)):
        caminho = ORIGINAIS_FISCAIS / norma["arquivo"]
        f = fontes.get(norma["fonte_id"], {})
        texto = ""
        if caminho.exists():
            if caminho.suffix == ".pdf":
                texto = subprocess.run(
                    ["pdftotext", "-layout", str(caminho), "-"],
                    capture_output=True,
                    text=True,
                    check=False,
                ).stdout
                texto = re.sub(r"\s+", " ", texto)
            else:
                texto = texto_html(caminho)
        dispositivos = [
            {
                **d,
                "conferido_no_arquivo": bool(texto) and d["trecho_conferido"] in texto,
            }
            for d in norma["dispositivos"]
        ]
        saida[nome] = {
            "arquivo": str(caminho.relative_to(ROOT)),
            "existe": caminho.exists(),
            "sha256_arquivo": sha256(caminho) if caminho.exists() else None,
            "sha256_manifesto": f.get("sha256"),
            "url": f.get("url"),
            "titulo": f.get("titulo"),
            "publicacao": norma.get("publicacao"),
            "dispositivos": dispositivos,
        }
    return saida


# ----------------------------------------------------------------------- montagem


def montar(consulta=_consultar_supabase) -> dict[str, Any]:
    noticias = json.loads(NOTICIAS.read_text(encoding="utf-8"))
    return {
        "gerado_em": agora_utc(),
        "script": "scripts/apuracao-2t-2026-angulo-boca-urna.py",
        "rotulo": ROTULO,
        "o_que_a_totalizacao_nao_mede": (
            "nenhum BU, log de urna ou RDV registra abordagem, pressão ou propaganda "
            "junto ao eleitor; este ângulo é documental, não estatístico"
        ),
        "relatos": relatos_contagens(consulta),
        "balancos_mjsp": balancos(),
        "ocorrencias": ocorrencias_publicas(noticias),
        "base_legal": base_legal(),
        "caminho_documental": CAMINHO_DOCUMENTAL,
    }


def _linha_balanco(b: dict[str, Any]) -> str:
    boca = (
        f"{b['boca_de_urna_pct']}% (cerca de {b['boca_de_urna_n_derivado']}, derivado)"
        if b.get("boca_de_urna_pct") is not None
        else "sem divisão por tipo"
    )
    return (
        f"| {b['corte']} | {b['ocorrencias']} | {b['flagrantes']} | "
        f"{b.get('conduzidos') if b.get('conduzidos') is not None else ''} | {boca} | {b['publicado']} |"
    )


def markdown(d: dict[str, Any]) -> str:
    r = d["relatos"]
    linhas = [
        "# Boca de urna e pressão sobre o eleitor, 2º turno de 2026",
        "",
        f"Gerado em {d['gerado_em']} por `{d['script']}`. Rótulo: {d['rotulo']}.",
        "",
        f"{d['o_que_a_totalizacao_nao_mede']}.",
        "",
        "## Balanços oficiais do MJSP (CICCN)",
        "",
        "| Corte | Ocorrências | Flagrantes | Conduzidos | Boca de urna | Publicado |",
        "|---|---|---|---|---|---|",
        *[_linha_balanco(b) for b in d["balancos_mjsp"]],
        "",
        "A contagem absoluta de boca de urna é derivada (percentual × total); o MJSP publicou só o percentual.",
        "",
        f"## Canal de relatos da casa (consultado em {r['consultado_em']})",
        "",
    ]
    if "erro" in r:
        linhas += [f"Acesso falhou: {r['erro']}.", ""]
    else:
        linhas += [
            f"Total {r['total']}; por status {r['por_status']}; pressão sobre o eleitor "
            f"(boca_de_urna, mesario_conduta, transporte_irregular) {r['pressao_sobre_o_eleitor']}.",
            f"Por tipo: {r['por_tipo']}.",
            f"Por UF: {r['por_uf']}. Presenciou: {r['presenciou']}. Seção no cadastro: {r['secao_no_cadastro']}.",
            f"Primeiro relato {r['primeiro_relato_utc_hora']} UTC; último {r['ultimo_relato_utc_hora']} UTC.",
            "",
        ]
    o = d["ocorrencias"]
    linhas += [
        f"## Ocorrências públicas do dia ({o['n']} itens do acervo)",
        "",
        f"Por classe: {o['por_classe']}. Por subtema: {o['por_subtema']}.",
        "",
        "| Hora | Classe | Subtema | Veículo | Título | Quem disse |",
        "|---|---|---|---|---|---|",
    ]
    for x in o["itens"]:
        linhas.append(
            f"| {x['quando'][11:16]} | {x['classe']} | {x['subtema']} | {x['veiculo']} | "
            f"[{x['titulo']}]({x['url']}) | {x['quem_disse'] or ''} |"
        )
    linhas += ["", "## Base legal conferida nos arquivos", ""]
    for nome, n in d["base_legal"].items():
        linhas.append(
            f"### {nome}: `{n.get('arquivo', '')}` (SHA-256 {n.get('sha256_arquivo')})"
        )
        for disp in n["dispositivos"]:
            ok = "conferido" if disp["conferido_no_arquivo"] else "NÃO conferido"
            linhas.append(f"- {disp['dispositivo']} ({ok}): {disp['texto']}")
        linhas.append("")
    linhas += ["## Como um relato vira documento", ""]
    for c in d["caminho_documental"]:
        linhas.append(
            f"- **{c['passo']}** ({c['quem']}): {c['como']} Vira: {c['vira']} Fonte: {c['fonte']}"
        )
    linhas.append("")
    return "\n".join(linhas)
