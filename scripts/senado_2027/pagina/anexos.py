"""Anexo, arbitragem e fontes da página do Senado de 2027."""

from __future__ import annotations

import json
import re
from html import escape as esc

from senado_2026.pagina.comum import data_br, num

from . import fixo
from . import texto as tx
from .comum import (
    ESTAGIO,
    RELATORIOS_ORIGEM,
    REPO,
    SINAL,
    _chip,
    _evento,
    _iso_br,
    _link,
    _nome_link,
    _partido_uf,
    _pessoas,
    _tabela,
)

ANEXO = (
    ("Arquivamentos", ("arquivado", "arquivamento_pedido")),
    ("Absolvições e trancamentos", ("absolvido_ou_trancado",)),
    ("Pendências eleitorais", ("eleitoral_pendente",)),
    ("Casos antigos sem desfecho", ("antigo_sem_desfecho",)),
)


def anexo(data: dict) -> str:
    idx = _pessoas(data)
    blocos = []
    for titulo, estagios in ANEXO:
        itens = []
        for info in idx.values():
            for c in info["pessoa"].get("casos") or []:
                if c["estagio"] not in estagios:
                    continue
                f = (c.get("fontes") or [None])[0]
                itens.append(
                    (
                        info["pessoa"]["nome"],
                        f"<li><b>{_nome_link(info)}</b> ({_partido_uf(info['pessoa'])}): "
                        f"{esc(c['titulo'])}. {_chip(c['estagio'])} "
                        f"Última decisão: {data_br(c.get('data_ultima_decisao'))}."
                        f"{' Fonte: ' + _link(f) if f else ''}</li>",
                    )
                )
        itens.sort(key=lambda x: x[0])
        blocos.append(
            f"<h3>{titulo} ({len(itens)})</h3>"
            + ("<ul>" + "".join(h for _, h in itens) + "</ul>" if itens else "")
        )
    return "".join(blocos)


def _relatorios_txt(v) -> str:
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            return esc(v)
    if isinstance(v, dict):
        return "; ".join(
            f"{esc(k)}: "
            + (
                esc(_rotulo_codigo(x))
                if isinstance(x, str)
                else esc(json.dumps(x, ensure_ascii=False))
            )
            for k, x in v.items()
        )
    return esc(str(v))


def _rotulo_codigo(v) -> str:
    v = str(v or "")
    return ESTAGIO.get(v) or SINAL.get(v) or v.replace("_", " ")


def arbitragem(data: dict) -> str:
    idx = _pessoas(data)
    arb = data["arbitragem"]
    rows = []
    for d in arb["decisoes"]:
        info = idx.get(d["senador"])
        nome = _nome_link(info) if info else esc(d["senador"])
        rows.append(
            [
                nome,
                esc(d.get("campo") or ""),
                _relatorios_txt(d.get("relatorios")),
                esc(_rotulo_codigo(d.get("decisao"))),
                _iso_br(d.get("fonte")),
            ]
        )
    return f"<p>{esc(arb.get('regra', ''))}</p>" + _tabela(
        ["Senador", "Campo", "O que diziam", "Decisão", "Motivo e fonte"],
        rows,
        "Arbitragem entre os quatro relatórios",
    )


def fontes(data: dict) -> str:
    vistos: dict[str, dict] = {}

    def add(f: dict | None) -> None:
        if not f or not f.get("url"):
            return
        vistos.setdefault(f["url"], f)

    for info in _pessoas(data).values():
        p = info["pessoa"]
        for c in p.get("casos") or []:
            for f in c.get("fontes") or []:
                add(f)
        for s in p.get("sinais_contrapeso") or []:
            for f in s.get("fontes") or []:
                add(f)
        voto = p.get("votacao_2026") or {}
        if voto.get("fonte"):
            add({"url": voto["fonte"], "veiculo": "TSE", "acesso": ""})
    for f in data["contexto"].get("fontes", {}).values():
        add(f)
    grupos: dict[str, list[dict]] = {}
    for f in vistos.values():
        grupos.setdefault(f.get("veiculo") or "Outros", []).append(f)
    blocos = []
    for veiculo in sorted(grupos, key=lambda v: (-len(grupos[v]), v.lower())):
        lst = sorted(grupos[veiculo], key=lambda f: f.get("data") or "", reverse=True)
        blocos.append(
            f"<li><b>{esc(veiculo)}</b> ({len(lst)})<ul>"
            + "".join(f"<li>{_link(f)}</li>" for f in lst)
            + "</ul></li>"
        )
    origem = "".join(
        f'<li><a href="{REPO}{caminho}" rel="noopener">{nome}</a>: relatório de '
        "origem, usado só para localizar fatos e para a figura de dispersão.</li>"
        for nome, caminho in RELATORIOS_ORIGEM
    )
    hashes = data.get("hashes_sha256") or {}
    return (
        f"<p>{len(vistos)} endereços únicos, agrupados por veículo. O selo diz se a "
        "página foi aberta e lida, se só o trecho do buscador foi visto, ou se o dado "
        "veio de relatório anterior.</p>"
        f'<details class="gv-tec"><summary>Todas as fontes ({len(vistos)})</summary>'
        f"<ul>{''.join(blocos)}</ul></details>"
        f"<p><b>Os quatro relatórios de origem</b></p><ul>{origem}</ul>"
        "<p><b>Dados para download:</b> "
        '<a href="assets/senado_2027.json">JSON do modelo e das fichas</a> e '
        '<a href="assets/senado_2027.csv">CSV com um senador por linha</a>. '
        f"O JSON guarda o SHA-256 de {len(hashes)} arquivos de entrada.</p>"
    )


def limites(data: dict) -> str:
    tit = tx.titulares(data)
    k0 = sum(1 for t in tit if t["scores"]["K"] == 0)
    casos = [c for t in tit for c in t.get("casos") or []]
    fontes = [f for c in casos for f in c.get("fontes") or []]
    busca = sum(1 for f in fontes if f.get("acesso") == "trecho_de_busca")
    anterior = sum(1 for f in fontes if f.get("acesso") == "relatorio_anterior")
    sigilo = sum(
        1 for c in casos if re.search(r"sigil", (c.get("resumo") or "").lower())
    )
    par = data["simulacao"]["parametros"]
    nv = data["contexto"].get("nao_verificado", [])
    gilmar = _evento(data, "csouto")
    gil_txt = (
        f" O próprio Gilmar Mendes, citado na imprensa: {_iso_br(gilmar['fato'])}"
        if gilmar
        else ""
    )
    return (
        "<ul>"
        f"<li><b>K = 0 não é certidão.</b> {k0} dos {len(tit)} senadores têm K "
        "igual a zero: nada foi localizado nas fontes desta pesquisa, na data de "
        "corte. Isso não prova ausência de procedimento.</li>"
        "<li><b>O orçamento de buscas acabou antes do fim.</b> Cada senador teve um "
        "teto de buscas e de páginas abertas. Das "
        f"{len(fontes)} fontes de casos, {busca} foram lidas só no trecho do buscador "
        f"e {anterior} vêm de relatório anterior sem reabertura.</li>"
        "<li><b>Sites que bloqueiam leitura automática.</b> G1, Folha, UOL e o portal "
        "do STF bloqueiam o acesso da ferramenta; resultado nulo de busca nesses "
        "sites não é prova de ausência.</li>"
        f"<li><b>Sigilo.</b> {sigilo} casos mencionam sigilo no resumo. Inquérito "
        "sigiloso pode existir sem aparecer em nenhuma fonte pública.</li>"
        "<li><b>Declaração recua depois da posse.</b> C mede o que o senador disse e "
        f"fez até {data_br(data.get('referencia'))}, não o que fará.{gil_txt}</li>"
        "<li><b>Senadores não votam de forma independente.</b> A simulação trata a "
        "dependência com um choque comum por bloco (correlação "
        f"{num(par['correlacao_intrabloco'], 2)}) e um nacional "
        f"({num(par['correlacao_nacional'], 2)}). Acordo de liderança pode mover "
        "um bloco inteiro mais do que isso.</li>"
        "<li><b>O cenário Flávio é condicional.</b> Ele supõe a vitória de Flávio "
        "Bolsonaro no 2º turno de 25/10/2026 e não é previsão do resultado.</li>"
        "</ul>"
        + (
            "<p><b>O que ficou sem verificação:</b></p><ul>"
            + "".join(f"<li>{esc(x)}</li>" for x in nv)
            + "</ul>"
            if nv
            else ""
        )
        + fixo.checklist_leitor()
    )
