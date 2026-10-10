"""Lê o roteiro autorado, valida contra o contrato e monta o payload do jogo.

Entrada: ``analysis/politize_game/roteiro/*.json`` (personagens, cenarios, npcs, npcs_b,
interface). Apoio: ``docs/assets/politize/textos.json`` e ``propostas.json``, que são a
única fonte de fatos e lições. Saída: dicionário pronto para virar
``docs/politize_game/dados.js`` (``window.POLITIZE_GAME = {...};``).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ROTEIRO = ROOT / "analysis/politize_game/roteiro"
APOIO = ROOT / "docs/assets/politize"
SAIDA = ROOT / "docs/politize_game/dados.js"

TRAVESSAO = "—"

PERSONAGENS = [
    "chad_genz", "tio_churras", "tia_zap", "mae_crista", "chad_40_cristao",
    "nerd_gamer", "nerd_antifeminista", "empreendedora_mei", "motoboy_app", "agro_jovem",
]  # fmt: skip
CENARIOS = [
    "whatsapp_familia", "padaria", "mercado", "bar", "shopping", "praia", "show",
    "game_online", "churrasco", "uber", "saida_do_culto", "academia", "fila_do_banco",
    "rede_x",
]  # fmt: skip
NPCS_A = [
    "petista_ideologico", "lulista_gratidao", "universitario_humanas",
    "feminista_militante", "militante_ong", "professora_sindicalizada",
    "lulista_pragmatico", "aposentada_inss", "sindicalista_cut", "isentao_cury",
    "faria_limer_zema", "coronel_caiado",
]  # fmt: skip
NPCS_B = [
    "mbl_perdido", "tiktoker_antissistema", "bolsonarista_magoado", "irmao_indeciso",
    "abstencionista_ressaca", "nulista_protesto", "branquista", "empresario_zema",
    "motorista_app_renan", "dona_de_casa_ne", "gamer_apolitico", "concursado_cury",
]  # fmt: skip

CAMPOS = {
    "terceira_via", "nao_votou", "nulo_branco", "lulista_pragmatico",
    "esquerda_ideologica", "direita_desgarrada",
}  # fmt: skip
ORIGENS = {
    "cury", "renan", "caiado", "zema", "outros_nominais", "abstencao", "brancos",
    "nulos", "bolsonaro_2022", "lula",
}  # fmt: skip
DESFECHOS = {"flavio", "nulo", "lula", "sem_mudanca"}
TIPOS = {"melhor", "ok", "erro", "grave"}
FAIXAS = {"melhor": (12, 18), "ok": (3, 8), "erro": (-15, -8), "grave": (-30, -30)}
TAGS_OPCAO = {
    "pergunta", "escuta", "respeito", "programa", "voto_util", "alternancia",
    "comparecimento", "boato", "medo", "pressao", "desqualifica", "sermao",
    "interrompe", "carona", "favor", "boca_de_urna", "ameaca", "mentira",
}  # fmt: skip
TAGS_ILEGAIS = {"carona", "favor", "boca_de_urna", "ameaca"}
TAGS_NPC = {
    "boomer", "jovem", "genz", "cristao", "evangelico", "catolico", "agro", "interior",
    "nordeste", "periferia", "classe_media", "rico", "gamer", "nerd", "universitario",
    "trabalhador", "autonomo", "app", "empreendedor", "servidor", "aposentado",
    "mulher", "homem", "mae", "pai", "sindicato", "esquerda", "direita", "liberal",
    "antissistema", "autoajuda", "academia", "zap", "superior", "fund_inc",
}  # fmt: skip
TEMAS_POLITIZE = {
    "Violência", "Saúde", "Economia", "Educação", "Corrupção", "Enchentes",
    "Infraestrutura",
}  # fmt: skip
VISUAL_OBRIGATORIO = {
    "pele", "cabelo", "estilo_cabelo", "acessorio", "roupa", "roupa_tipo", "barba",
}  # fmt: skip
INTERFACE_CHAVES = {
    "titulo", "subtitulo", "deck", "tutorial", "rotulos", "fases", "graus",
    "compartilhar", "aviso", "dicas_gerais", "rodape", "fim",
}  # fmt: skip

# Textos de apoio das leis, escritos uma vez e citados pelo roteiro por chave.
LEIS = {
    "lei.art299": (
        "Oferecer dinheiro, comida, carona, dádiva ou qualquer vantagem para obter voto "
        "é corrupção eleitoral (Código Eleitoral, Lei 4.737/1965, art. 299), com pena de "
        "reclusão. Vale para quem dá e para quem promete."
    ),
    "lei.6091": (
        "O transporte de eleitores no dia da eleição é regulado pela Lei 6.091/1974: só o "
        "serviço gratuito organizado pela Justiça Eleitoral. Levar alguém para votar em "
        "troca do voto é crime."
    ),
    "lei.9504.39": (
        "No dia da eleição é proibida a boca de urna, a aglomeração com bandeira e a "
        "distribuição de material de campanha (Lei 9.504/1997, art. 39, § 5º). Converse "
        "antes do dia 25; no dia, silêncio."
    ),
    "lei.voto_secreto": (
        "O voto é secreto. Ninguém é obrigado a dizer em quem votou, e nenhum número "
        "público descreve uma pessoa: a leitura das urnas é agregada por seção."
    ),
}

_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
_FONTE_INDICE = re.compile(r"^(.*)\[(\d+)\]$")


class RoteiroInvalido(ValueError):
    """Erro de contrato no roteiro, com todas as falhas listadas."""


def _ler(nome: str, base: Path = ROTEIRO) -> dict[str, Any]:
    return json.loads((base / f"{nome}.json").read_text(encoding="utf-8"))


def carregar_apoio(base: Path = APOIO) -> tuple[dict, dict]:
    textos = json.loads((base / "textos.json").read_text(encoding="utf-8"))
    propostas = json.loads((base / "propostas.json").read_text(encoding="utf-8"))
    return textos, propostas


def resolver_fonte(chave: str, textos: dict, propostas: dict) -> str:
    """Devolve o texto de apoio apontado por uma chave do contrato, ou levanta KeyError."""
    if chave in LEIS:
        return LEIS[chave]
    partes = chave.split(".")
    if partes[0] == "propostas" and len(partes) == 3:
        tema_id, pagina = partes[1], partes[2]
        for tema in propostas["temas"]:
            if tema["id"] != tema_id:
                continue
            for cit in tema["citacoes"]:
                if str(cit["pagina"]) == pagina:
                    return f"{cit['titulo']}: {cit['texto']} (plano de governo, p. {pagina})"
        raise KeyError(chave)
    if partes[0] != "textos":
        raise KeyError(chave)
    atual: Any = textos
    for parte in partes[1:]:
        m = _FONTE_INDICE.match(parte)
        atual = atual[m.group(1)][int(m.group(2))] if m else atual[parte]
    if not isinstance(atual, str):
        raise KeyError(chave)
    return atual


def _opcao(
    op: dict, onde: str, erros: list[str], textos: dict, propostas: dict
) -> None:
    for campo in ("texto", "tipo", "efeito", "tags", "reacao"):
        if campo not in op:
            erros.append(f"{onde}: opção sem '{campo}'")
            return
    if op["tipo"] not in TIPOS:
        erros.append(f"{onde}: tipo '{op['tipo']}' inválido")
        return
    lo, hi = FAIXAS[op["tipo"]]
    if not isinstance(op["efeito"], int) or not lo <= op["efeito"] <= hi:
        erros.append(
            f"{onde}: efeito {op['efeito']} fora da faixa {lo}..{hi} para {op['tipo']}"
        )
    desconhecidas = set(op["tags"]) - TAGS_OPCAO
    if desconhecidas:
        erros.append(f"{onde}: tags desconhecidas {sorted(desconhecidas)}")
    if op["tipo"] in ("erro", "grave"):
        if not op.get("licao"):
            erros.append(f"{onde}: opção {op['tipo']} sem 'licao'")
        if not op.get("fonte"):
            erros.append(f"{onde}: opção {op['tipo']} sem 'fonte'")
    ilegal = op["tipo"] == "grave" and set(op["tags"]) & TAGS_ILEGAIS
    if ilegal and not str(op.get("fonte", "")).startswith("lei."):
        erros.append(f"{onde}: conduta ilegal precisa citar uma lei como fonte")
    if "programa" in op["tags"] and not str(op.get("fonte", "")).startswith(
        "propostas."
    ):
        erros.append(f"{onde}: tag programa exige fonte 'propostas.<tema>.<pagina>'")
    if op.get("fonte"):
        try:
            op["fonte_texto"] = resolver_fonte(op["fonte"], textos, propostas)
        except (KeyError, IndexError, TypeError):
            erros.append(f"{onde}: fonte '{op['fonte']}' não existe")


def _conjunto(
    ops: list[dict],
    onde: str,
    erros: list[str],
    minimo: int,
    maximo: int,
    textos: dict,
    propostas: dict,
    exige_melhor: bool = True,
) -> None:
    if not isinstance(ops, list) or not minimo <= len(ops) <= maximo:
        erros.append(f"{onde}: precisa de {minimo} a {maximo} opções")
        return
    for i, op in enumerate(ops):
        _opcao(op, f"{onde}[{i}]", erros, textos, propostas)
    tipos = [op.get("tipo") for op in ops]
    if exige_melhor and tipos.count("melhor") != 1:
        erros.append(f"{onde}: precisa de exatamente 1 opção 'melhor'")


def _visual(v: Any, onde: str, erros: list[str]) -> None:
    if not isinstance(v, dict):
        erros.append(f"{onde}: visual ausente")
        return
    faltam = VISUAL_OBRIGATORIO - set(v)
    if faltam:
        erros.append(f"{onde}: visual sem {sorted(faltam)}")
    for cor in ("pele", "cabelo", "roupa"):
        if cor in v and not _HEX.match(str(v[cor])):
            erros.append(f"{onde}: visual.{cor} não é hex de 6 dígitos")


def validar_personagens(d: dict, erros: list[str]) -> None:
    ids = [p.get("id") for p in d.get("personagens", [])]
    if ids != PERSONAGENS:
        erros.append(f"personagens: ids esperados {PERSONAGENS}, vieram {ids}")
    for p in d.get("personagens", []):
        onde = f"personagens.{p.get('id')}"
        for campo in ("nome", "idade", "bio", "trunfo", "fraqueza", "fala_inicial"):
            if campo not in p:
                erros.append(f"{onde}: sem '{campo}'")
        trunfo = p.get("trunfo", {})
        if not isinstance(trunfo.get("tags"), list) or not trunfo.get("texto"):
            erros.append(f"{onde}: trunfo precisa de tags e texto")
        elif set(trunfo["tags"]) - TAGS_NPC:
            erros.append(f"{onde}: trunfo com tags fora da lista")
        fraq = p.get("fraqueza", {})
        if fraq.get("tag") not in TAGS_OPCAO or not fraq.get("texto"):
            erros.append(f"{onde}: fraqueza precisa de uma tag de opção e texto")
        _visual(p.get("visual"), onde, erros)


def validar_cenarios(
    d: dict, erros: list[str], textos: dict, propostas: dict
) -> set[str]:
    ids = [c.get("id") for c in d.get("cenarios", [])]
    if sorted(ids) != sorted(CENARIOS):
        erros.append(
            f"cenarios: ids esperados {sorted(CENARIOS)}, vieram {sorted(ids)}"
        )
    sugeridos: set[str] = set()
    for c in d.get("cenarios", []):
        onde = f"cenarios.{c.get('id')}"
        for campo in ("nome", "hora", "publico", "descricao", "ambiente", "abordagem"):
            if campo not in c:
                erros.append(f"{onde}: sem '{campo}'")
        if c.get("publico") not in (1, 2, 3):
            erros.append(f"{onde}: publico precisa ser 1, 2 ou 3")
        amb = c.get("ambiente", {})
        paleta = amb.get("paleta", [])
        if len(paleta) != 3 or not all(_HEX.match(str(x)) for x in paleta):
            erros.append(f"{onde}: ambiente.paleta precisa de 3 cores hex")
        if not isinstance(amb.get("props"), list) or not 2 <= len(amb["props"]) <= 4:
            erros.append(f"{onde}: ambiente.props precisa de 2 a 4 itens")
        _conjunto(
            c.get("abordagem", []), f"{onde}.abordagem", erros, 3, 4, textos, propostas
        )
        sugeridos.update(c.get("npcs_sugeridos", []))
    return sugeridos


def validar_npcs(
    d: dict,
    esperados: list[str],
    onde_arq: str,
    erros: list[str],
    textos: dict,
    propostas: dict,
) -> None:
    ids = [n.get("id") for n in d.get("npcs", [])]
    if ids != esperados:
        erros.append(f"{onde_arq}: ids esperados {esperados}, vieram {ids}")
    for n in d.get("npcs", []):
        onde = f"{onde_arq}.{n.get('id')}"
        for campo in (
            "nome",
            "idade",
            "genero",
            "campo",
            "origem",
            "tags",
            "dificuldade",
            "confianca_inicial",
            "desfechos",
            "limiares",
            "bio",
            "visual",
            "cenarios",
            "tema",
            "queixa",
            "escuta",
            "objecoes",
            "fecho",
            "desfecho_texto",
        ):
            if campo not in n:
                erros.append(f"{onde}: sem '{campo}'")
        if n.get("campo") not in CAMPOS:
            erros.append(f"{onde}: campo inválido")
        if n.get("origem") not in ORIGENS:
            erros.append(f"{onde}: origem inválida")
        if n.get("genero") not in ("M", "F"):
            erros.append(f"{onde}: genero precisa ser M ou F")
        tags = set(n.get("tags", []))
        if not 2 <= len(tags) <= 4 or tags - TAGS_NPC:
            erros.append(f"{onde}: tags precisam ser 2 a 4 da lista do contrato")
        if n.get("dificuldade") not in (1, 2, 3):
            erros.append(f"{onde}: dificuldade 1, 2 ou 3")
        ci = n.get("confianca_inicial")
        if not isinstance(ci, int) or not 10 <= ci <= 55:
            erros.append(f"{onde}: confianca_inicial fora de 10..55")
        desf = n.get("desfechos", {})
        if set(desf) != {"alto", "medio", "baixo"} or set(desf.values()) - DESFECHOS:
            erros.append(f"{onde}: desfechos precisam de alto/medio/baixo válidos")
        lim = n.get("limiares", {})
        if not (
            isinstance(lim.get("alto"), int)
            and isinstance(lim.get("medio"), int)
            and 0 < lim["medio"] < lim["alto"] <= 100
        ):
            erros.append(f"{onde}: limiares precisam de 0 < medio < alto <= 100")
        _visual(n.get("visual"), onde, erros)
        cen = n.get("cenarios", [])
        if not 2 <= len(cen) <= 5 or set(cen) - set(CENARIOS):
            erros.append(f"{onde}: cenarios precisam ser 2 a 5 ids válidos")
        if n.get("tema") not in TEMAS_POLITIZE:
            erros.append(f"{onde}: tema fora dos temas do Politize")
        _conjunto(n.get("escuta", []), f"{onde}.escuta", erros, 3, 4, textos, propostas)
        obj = n.get("objecoes", [])
        if len(obj) != 2:
            erros.append(f"{onde}: precisa de exatamente 2 objeções")
        graves = 0
        for i, o in enumerate(obj):
            if not o.get("fala"):
                erros.append(f"{onde}.objecoes[{i}]: sem fala")
            _conjunto(
                o.get("opcoes", []),
                f"{onde}.objecoes[{i}]",
                erros,
                4,
                4,
                textos,
                propostas,
            )
            tipos = [x.get("tipo") for x in o.get("opcoes", [])]
            if "erro" not in tipos and "grave" not in tipos:
                erros.append(
                    f"{onde}.objecoes[{i}]: precisa de ao menos 1 erro ou grave"
                )
            graves += tipos.count("grave")
        graves += sum(1 for x in n.get("escuta", []) if x.get("tipo") == "grave")
        graves += sum(1 for x in n.get("fecho", []) if x.get("tipo") == "grave")
        if graves < 1:
            erros.append(f"{onde}: precisa de ao menos 1 opção grave")
        _conjunto(n.get("fecho", []), f"{onde}.fecho", erros, 3, 3, textos, propostas)
        dt = n.get("desfecho_texto", {})
        if set(dt) != DESFECHOS or not all(dt.values()):
            erros.append(f"{onde}: desfecho_texto precisa das 4 chaves com texto")


def validar_interface(d: dict, erros: list[str]) -> None:
    faltam = INTERFACE_CHAVES - set(d)
    if faltam:
        erros.append(f"interface: sem {sorted(faltam)}")
    graus = d.get("graus", [])
    if len(graus) != 5 or any(
        "min_saldo" not in g or "nome" not in g or "frase" not in g for g in graus
    ):
        erros.append("interface.graus: 5 graus com min_saldo, nome e frase")
    elif [g["min_saldo"] for g in graus] != sorted(g["min_saldo"] for g in graus):
        erros.append("interface.graus: do pior ao melhor, min_saldo crescente")
    for frase in d.get("compartilhar", []):
        if "{flavio}" not in frase:
            erros.append("interface.compartilhar: toda frase precisa de {flavio}")


def _varrer_textos(obj: Any, caminho: str, erros: list[str]) -> None:
    if isinstance(obj, str):
        if TRAVESSAO in obj:
            erros.append(f"{caminho}: travessão proibido")
        if "eleitores dele" in obj or "eleitores dela" in obj:
            erros.append(f"{caminho}: escreva 'eleitorado de X'")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _varrer_textos(v, f"{caminho}.{k}", erros)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _varrer_textos(v, f"{caminho}[{i}]", erros)


def montar(base: Path = ROTEIRO, apoio: Path = APOIO) -> dict[str, Any]:
    """Lê, valida e devolve o payload. Levanta RoteiroInvalido com todas as falhas."""
    textos, propostas = carregar_apoio(apoio)
    erros: list[str] = []
    personagens = _ler("personagens", base)
    cenarios = _ler("cenarios", base)
    npcs_a = _ler("npcs", base)
    npcs_b = _ler("npcs_b", base)
    interface = _ler("interface", base)

    validar_personagens(personagens, erros)
    sugeridos = validar_cenarios(cenarios, erros, textos, propostas)
    validar_npcs(npcs_a, NPCS_A, "npcs", erros, textos, propostas)
    validar_npcs(npcs_b, NPCS_B, "npcs_b", erros, textos, propostas)
    validar_interface(interface, erros)

    npcs = npcs_a.get("npcs", []) + npcs_b.get("npcs", [])
    ids_npc = {n.get("id") for n in npcs}
    if sugeridos - ids_npc:
        erros.append(
            f"cenarios.npcs_sugeridos desconhecidos: {sorted(sugeridos - ids_npc)}"
        )
    for p in personagens.get("personagens", []):
        tags = set(p.get("trunfo", {}).get("tags", []))
        if not any(tags & set(n.get("tags", [])) for n in npcs):
            erros.append(f"personagens.{p.get('id')}: trunfo não casa com nenhum NPC")
    campos = {c: sum(1 for n in npcs if n.get("campo") == c) for c in CAMPOS}
    if campos["terceira_via"] + campos["direita_desgarrada"] < 3:
        erros.append("mistura: menos de 3 NPCs de terceira via ou direita desgarrada")
    if campos["nao_votou"] + campos["nulo_branco"] < 2:
        erros.append("mistura: menos de 2 NPCs faltosos ou nulo/branco")
    if campos["lulista_pragmatico"] < 2 or campos["esquerda_ideologica"] < 1:
        erros.append("mistura: faltam lulistas pragmáticos ou esquerda ideológica")

    payload = {
        "versao": "1.0",
        "personagens": personagens.get("personagens", []),
        "cenarios": cenarios.get("cenarios", []),
        "npcs": npcs,
        "interface": interface,
        "fontes": {k: LEIS[k] for k in LEIS},
    }
    _varrer_textos(payload, "roteiro", erros)
    if erros:
        raise RoteiroInvalido("\n".join(erros))
    return payload


def para_js(payload: dict[str, Any]) -> str:
    corpo = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    # </script> dentro de string JSON quebraria a página; o escape é inofensivo em JS.
    corpo = corpo.replace("</", "<\\/")
    return (
        "/* Gerado por scripts/politize-game-build.py a partir de "
        "analysis/politize_game/roteiro/. Nao editar a mao. */\n"
        f"window.POLITIZE_GAME={corpo};\n"
    )


def gravar(saida: Path = SAIDA) -> dict[str, Any]:
    payload = montar()
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(para_js(payload), encoding="utf-8")
    return payload
