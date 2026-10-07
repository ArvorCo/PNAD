"""Relatório do build em ``analysis/politize/relatorio_build.md``.

Cobertura (locais com voto, com 2022, perfil por seção ou por zona, setor), distribuição
do índice, arquétipos e as duas conferências do contrato: soma de Flávio e Lula nos
locais contra o banco de boletins, e média nacional do esperado recentrado contra a
urna. Todo número sai do próprio build; nada é digitado à mão.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import arquetipos, fontes
from . import metricas as mt
from .montagem import APTOS_MIN_SECAO, Local, ResultadoUF, m_validos

ARQUIVO = fontes.ROOT / "analysis/politize/relatorio_build.md"
# Totalização oficial do TSE (analysis/apuracao_2026/BRIEF.md, linha 9).
OFICIAL_FLAVIO = 56_104_503
OFICIAL_LULA = 53_879_538
PERCENTIS = (1, 5, 10, 25, 50, 75, 90, 95, 99)


def _n(x: float | int | None, casas: int = 0) -> str:
    if x is None:
        return "sem dado"
    if casas == 0:
        return f"{round(x):,}".replace(",", ".")
    texto = f"{x:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def _pct(parte: float, todo: float, casas: int = 1) -> str:
    return "sem dado" if not todo else _n(100.0 * parte / todo, casas) + "%"


def estatisticas(resultados: Sequence[ResultadoUF]) -> dict[str, Any]:
    locais: list[Local] = [x for r in resultados for x in r.locais]
    secoes = [s for r in resultados for s in r.secoes()]
    brasil = [x for x in locais if x.cad.uf != "ZZ"]
    aptos = sum(x.c["aptos"] for x in locais)
    aptos_br = sum(x.c["aptos"] for x in brasil)
    st: dict[str, Any] = {
        "n_locais": len(locais),
        "n_secoes": len(secoes),
        "aptos": aptos,
        "flavio": sum(x.c["flavio"] for x in locais),
        "lula": sum(x.c["lula"] for x in locais),
        "terceira": sum(x.c["terceira"] for x in locais),
        "secoes_flavio": sum(s.c["flavio"] for s in secoes),
        "secoes_lula": sum(s.c["lula"] for s in secoes),
        "banco_flavio": sum(r.meta["votos"]["banco_flavio"] for r in resultados),
        "banco_lula": sum(r.meta["votos"]["banco_lula"] for r in resultados),
        "fora_lista": 0,
        "secoes_sem_bu": sum(
            r.meta["votos"]["secoes_principais_sem_bu"] for r in resultados
        ),
        "secoes_soma_divergente": sum(
            r.meta["votos"]["secoes_soma_diferente_do_comparecimento"]
            for r in resultados
        ),
        "secoes_fora_cadastro": sum(
            r.meta["secoes_fora_do_cadastro"] for r in resultados
        ),
        "locais_brasil": len(brasil),
        "locais_com_ponto": sum(1 for x in brasil if x.cad.lat is not None),
        "locais_com_setor": sum(1 for x in brasil if x.setor and x.setor[0]),
        "locais_com_cep": sum(1 for x in brasil if x.cad.cep),
        "aptos_casados": sum(x.c["aptos_casado"] for x in locais),
        "locais_com_2022": sum(1 for x in locais if x.c["aptos_casado"] > 0),
        "locais_2022_integral": sum(
            1 for x in locais if x.c["aptos"] and x.c["aptos_casado"] == x.c["aptos"]
        ),
        "locais_com_renda": sum(1 for x in brasil if x.renda is not None),
        "aptos_brasil": aptos_br,
        "situacao": Counter((x.m.get("setor_situacao") or "sem setor") for x in brasil),
        "tipo": Counter((x.m.get("setor_tipo") or "sem setor") for x in brasil),
        "arquetipo": Counter(x.m["arquetipo"] for x in locais),
        "arquetipo_aptos": Counter(),
        "secundario": Counter(x.m["arquetipo_secundario"] for x in locais),
        "arquetipo_secoes": Counter(s.m["arquetipo"] for s in secoes),
        "indice": mt.percentis(
            [x.m["indice"] for x in locais if x.m["indice"] is not None], PERCENTIS
        ),
        "indice_secoes": mt.percentis(
            [
                s.m["indice"]
                for s in secoes
                if s.m["indice"] is not None and s.c["aptos"] >= APTOS_MIN_SECAO
            ],
            PERCENTIS,
        ),
        "secoes_pequenas": sum(1 for s in secoes if s.c["aptos"] < APTOS_MIN_SECAO),
        "potencial": mt.percentis(
            [x.m["potencial"] for x in locais if x.m["potencial"] is not None],
            PERCENTIS,
        ),
        "saturados": sum(1 for x in locais if x.m["indice"] == 100),
        "perfil_por_uf": {
            r.uf: (
                r.meta["perfil_secao"],
                r.meta["locais_perfil_secao"],
                r.meta["locais_perfil_zona"],
                r.meta["locais_sem_perfil"],
            )
            for r in resultados
        },
        "faltam_zero": sum(1 for x in locais if x.m["faltam"] == 0),
        "vao_medio": mt.media_ponderada(
            (x.m.get("vao_perfil_pp"), m_validos(x)) for x in brasil
        ),
        "vao_medio_secoes": mt.media_ponderada(
            (s.m.get("vao_perfil_pp"), m_validos(s)) for s in secoes
        ),
        "esperado_medio": mt.media_ponderada(
            (x.m.get("esperado_flavio_v"), m_validos(x)) for x in brasil
        ),
        "urna_brasil": mt.pct(
            sum(x.c["flavio"] for x in brasil if x.esperado is not None),
            sum(m_validos(x) for x in brasil if x.esperado is not None),
        ),
        "esperado_uf": {
            r.uf: (
                mt.media_ponderada(
                    (x.m.get("esperado_flavio_v"), m_validos(x)) for x in r.locais
                ),
                mt.media_ponderada(
                    (x.m.get("esperado_lula_v"), m_validos(x)) for x in r.locais
                ),
            )
            for r in resultados
        },
        "percentil": mt.percentis(
            [x.m["percentil"] for x in locais if x.m.get("percentil") is not None],
            PERCENTIS,
        ),
        "urna_com_exterior": mt.pct(
            sum(x.c["flavio"] for x in locais), sum(m_validos(x) for x in locais)
        ),
        "esperado_medio_lula": mt.media_ponderada(
            (x.m.get("esperado_lula_v"), m_validos(x)) for x in brasil
        ),
    }
    for x in locais:
        st["arquetipo_aptos"][x.m["arquetipo"]] += x.c["aptos"]
    por_regiao: dict[str, list[Local]] = {}
    for x in locais:
        por_regiao.setdefault(fontes.UFS[x.cad.uf][1], []).append(x)
    st["regioes"] = {
        reg: {
            "locais": len(xs),
            "flavio_v": mt.pct(sum(x.c["flavio"] for x in xs), sum(map(m_validos, xs))),
            "indice": mt.media_ponderada((x.m["indice"], x.c["aptos"]) for x in xs),
            "vao": mt.media_ponderada(
                (x.m.get("vao_perfil_pp"), m_validos(x)) for x in xs
            ),
            "c_perfil": mt.media_ponderada(
                (x.m.get("c_perfil"), x.c["aptos"]) for x in xs
            ),
            "c_ausentes": mt.media_ponderada(
                (x.m["c_ausentes"], x.c["aptos"]) for x in xs
            ),
            "saturados": sum(1 for x in xs if x.m["indice"] == 100),
        }
        for reg, xs in sorted(por_regiao.items())
    }
    for r in resultados:
        st["fora_lista"] += r.meta["votos"].get("votos_fora_lista", 0)
    return st


def escrever(
    st: Mapping[str, Any],
    resultados: Sequence[ResultadoUF],
    parametros: Mapping[str, Any],
    nacional: Mapping[str, Any],
    meta: Mapping[str, Any],
) -> Path:
    rec = parametros["recentragem"]
    ufs = [r.uf for r in resultados]
    completo = set(ufs) == set(fontes.UFS)
    pnad = parametros["pnad"]
    lin: list[str] = []
    add = lin.append
    add("# Politize sua vizinhança: relatório do build")
    add("")
    add(
        f"Gerado em {meta['gerado_em']} por `{meta['comando']}`. Tempo total: "
        f"{_n(meta['segundos'], 1)} s."
    )
    add("")
    add(
        f"Escopo: {'nacional (27 UFs e exterior)' if completo else ', '.join(ufs)}. "
        f"Contrato: `analysis/politize/CONTRATO.md`. Decisões e desvios: "
        f"`analysis/politize/DECISOES.md`."
    )
    add("")
    add("## Conferência das somas")
    add("")
    add("| conta | Flávio (22) | Lula (13) |")
    add("|---|---:|---:|")
    add(f"| soma dos locais | {_n(st['flavio'])} | {_n(st['lula'])} |")
    add(
        f"| soma das seções (camada zona/) | {_n(st['secoes_flavio'])} | "
        f"{_n(st['secoes_lula'])} |"
    )
    add(
        f"| banco de boletins (`voto_secao`, cargo 1) | {_n(st['banco_flavio'])} | "
        f"{_n(st['banco_lula'])} |"
    )
    add(
        f"| diferença locais menos banco | {_n(st['flavio'] - st['banco_flavio'])} | "
        f"{_n(st['lula'] - st['banco_lula'])} |"
    )
    if completo:
        add(
            f"| totalização oficial do TSE | {_n(OFICIAL_FLAVIO)} | {_n(OFICIAL_LULA)} |"
        )
        add(
            f"| oficial menos banco | {_n(OFICIAL_FLAVIO - st['banco_flavio'])} | "
            f"{_n(OFICIAL_LULA - st['banco_lula'])} |"
        )
    add("")
    add(
        f"Seções principais sem boletim no banco: {_n(st['secoes_sem_bu'])}. "
        "São as seções do exterior não instaladas e as 20 seções de Betim, Uberlândia "
        "e Carapicuíba cujo arquivo não foi publicado (`aux_404`), que a totalização "
        "oficial inclui e o banco por seção não tem; é a diferença entre o banco e o "
        "total oficial. Votos nominais em número fora da lista de candidaturas "
        f"(número 28) contam como nulos, como no TSE: {_n(st['fora_lista'])} votos. "
        f"Seções cuja soma de votos difere do comparecimento: "
        f"{_n(st['secoes_soma_divergente'])}. Seções com boletim fora do cadastro de "
        f"locais: {_n(st['secoes_fora_cadastro'])}."
    )
    add("")
    add("## Recentragem do voto esperado (por UF)")
    add("")
    add(f"Método: {rec['metodo']}.")
    add("")
    add(
        "| UF | válidos | bruto Flávio | urna Flávio | desloc. Flávio | recentrado "
        "Flávio | bruto Lula | urna Lula | desloc. Lula | recentrado Lula | confere |"
    )
    add("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
    falhas = 0
    for uf, r in sorted(rec["por_uf"].items()):
        esp_f, esp_l = st["esperado_uf"].get(uf, (None, None))
        ok = (
            esp_f is not None
            and abs(esp_f - r["urna_flavio"]) <= 0.05
            and abs(esp_l - r["urna_lula"]) <= 0.05
        )
        falhas += not ok
        add(
            f"| {uf} | {_n(r['validos'])} | {_n(r['esperado_bruto_flavio'], 2)} | "
            f"{_n(r['urna_flavio'], 2)} | {_n(r['deslocamento_flavio_pp'], 2)} | "
            f"{_n(esp_f, 3)} | {_n(r['esperado_bruto_lula'], 2)} | "
            f"{_n(r['urna_lula'], 2)} | {_n(r['deslocamento_lula_pp'], 2)} | "
            f"{_n(esp_l, 3)} | {'ok' if ok else 'FALHOU'} |"
        )
    add("")
    add(
        f"Conferência por UF (média do esperado recentrado = urna da UF, tolerância "
        f"0,05 pp): {len(rec['por_uf']) - falhas} de {len(rec['por_uf'])} ok."
    )
    if completo and st["esperado_medio"] is not None:
        dif = st["esperado_medio"] - st["urna_brasil"]
        dif_ext = st["esperado_medio"] - st["urna_com_exterior"]
        add(
            f"Média nacional do esperado recentrado: {_n(st['esperado_medio'], 4)} "
            f"(Lula {_n(st['esperado_medio_lula'], 4)}), contra a urna dos locais no "
            f"Brasil {_n(st['urna_brasil'], 4)} (diferença {_n(dif, 4)} pp) e a urna "
            f"nacional com exterior {_n(st['urna_com_exterior'], 4)} (diferença "
            f"{_n(dif_ext, 4)} pp; tolerância 0,05 pp: "
            f"{'ok' if abs(dif_ext) <= 0.05 else 'FALHOU'}). Vão médio ponderado por "
            f"válidos nos locais: {_n(st['vao_medio'], 4)} pp; nas seções: "
            f"{_n(st['vao_medio_secoes'], 4)} pp (o deslocamento é calculado sobre os "
            "locais e aplicado igual às seções)."
        )
    add("")
    add(
        "Voto por faixa de renda nas pesquisas (válidos, média simples das duas casas):"
    )
    add("")
    add("| faixa | Flávio | Lula |")
    add("|---|---:|---:|")
    for nome, v in zip(
        ("até 2 SM", "2 a 5 SM", "mais de 5 SM"),
        parametros["voto_faixa"]["media"],
        strict=True,
    ):
        add(f"| {nome} | {_n(v['flavio'], 2)} | {_n(v['lula'], 2)} |")
    add("")
    add("## Cobertura")
    add("")
    add(
        f"- Locais com voto: {_n(st['n_locais'])} ({_n(st['locais_brasil'])} no Brasil); "
        f"seções principais com boletim: {_n(st['n_secoes'])}; aptos: {_n(st['aptos'])}."
    )
    add(
        f"- Locais no Brasil com coordenada: {_n(st['locais_com_ponto'])} "
        f"({_pct(st['locais_com_ponto'], st['locais_brasil'])}); com setor censitário: "
        f"{_n(st['locais_com_setor'])} ({_pct(st['locais_com_setor'], st['locais_brasil'])}); "
        f"com CEP válido: {_n(st['locais_com_cep'])}."
    )
    add(
        f"- 2022 (mesma seção e mesmo número de local): {_n(st['locais_com_2022'])} locais "
        f"com ao menos uma seção casada, {_n(st['locais_2022_integral'])} com todas; aptos "
        f"casados {_pct(st['aptos_casados'], st['aptos'])} dos aptos."
    )
    add(f"- Renda estimada (PNAD): {_n(st['locais_com_renda'])} locais no Brasil.")
    add(
        "- Situação do setor: "
        + ", ".join(f"{k} {_n(v)}" for k, v in sorted(st["situacao"].items()))
    )
    add(
        "- Tipo do setor: "
        + ", ".join(f"{k} {_n(v)}" for k, v in sorted(st["tipo"].items()))
    )
    add("")
    add("Perfil do eleitorado por UF (fonte; locais por seção, por zona, sem perfil):")
    add("")
    add("| UF | arquivo por seção | locais por seção | locais por zona | sem perfil |")
    add("|---|---|---:|---:|---:|")
    for uf, (motivo, n_sec, n_zona, n_sem) in sorted(st["perfil_por_uf"].items()):
        add(f"| {uf} | {motivo} | {_n(n_sec)} | {_n(n_zona)} | {_n(n_sem)} |")
    add("")
    add("## Índice de conversa")
    add("")
    add(
        f"Teto do potencial: {_n(parametros['teto_potencial'])} votos por 100 aptos. "
        f"p99 observado do potencial: {_n(parametros['p99_potencial'], 2)}. Locais com "
        f"índice 100 (saturados): {_n(st['saturados'])}."
    )
    add("")
    add(
        "| ponto da distribuição | índice (locais) | índice (seções com 30 aptos ou "
        "mais) | potencial (locais) | coluna `percentil` (locais do Brasil) |"
    )
    add("|---|---:|---:|---:|---:|")
    for q in PERCENTIS:
        k = f"p{q}"
        add(
            f"| {k} | {_n(st['indice'][k], 1)} | {_n(st['indice_secoes'][k], 1)} | "
            f"{_n(st['potencial'][k], 2)} | {_n(st['percentil'][k], 1)} |"
        )
    add("")
    add(
        "A coluna `percentil` é a posição do potencial do local entre os locais do "
        "Brasil com boletim (0 a 100, arredondada para baixo; 100 = maior potencial do "
        "país); a da seção usa as seções com 30 aptos ou mais; `percentil_uf` repete a "
        "conta dentro da UF. O exterior só tem `percentil_uf`."
    )
    add("")
    add(
        f"Seções com menos de {APTOS_MIN_SECAO} aptos (votos omitidos na camada zona/): "
        f"{_n(st['secoes_pequenas'])}."
    )
    add("")
    add(
        "Por região (médias ponderadas: índice e componentes por aptos, vão por válidos):"
    )
    add("")
    add(
        "| região | locais | Flávio (% válidos) | índice médio | vão do perfil (pp) | "
        "c_perfil | c_ausentes | índice 100 |"
    )
    add("|---|---:|---:|---:|---:|---:|---:|---:|")
    for reg, r in st["regioes"].items():
        add(
            f"| {reg} | {_n(r['locais'])} | {_n(r['flavio_v'], 1)} | "
            f"{_n(r['indice'], 1)} | {_n(r['vao'], 2)} | {_n(r['c_perfil'], 2)} | "
            f"{_n(r['c_ausentes'], 2)} | {_n(r['saturados'])} |"
        )
    add("")
    add("## Arquétipos")
    add("")
    add("| arquétipo | locais | % dos locais | % dos aptos | seções | secundário |")
    add("|---|---:|---:|---:|---:|---:|")
    for cod in arquetipos.CODIGOS:
        add(
            f"| {arquetipos.NOMES[cod]} (`{cod}`) | {_n(st['arquetipo'][cod])} | "
            f"{_pct(st['arquetipo'][cod], st['n_locais'])} | "
            f"{_pct(st['arquetipo_aptos'][cod], st['aptos'])} | "
            f"{_n(st['arquetipo_secoes'][cod])} | {_n(st['secundario'][cod])} |"
        )
    add(f"| sem secundário | | | | | {_n(st['secundario'][None])} |")
    add("")
    add("## Conta do 2º turno")
    add("")
    t = parametros["transferencia_terceira"]
    add(
        f"Transferência da terceira via: {_n(100 * t['sem_escolha'])}% sem escolha, "
        f"{_n(100 * t['flavio_entre_escolhem'])}% de quem escolhe para Flávio "
        f"(coeficientes {_n(t['coef_flavio'], 3)} e {_n(t['coef_lula'], 3)}). Taxa de "
        f"conversão declarada: {_n(parametros['taxa_conversao'], 2)}."
    )
    add("")
    add(
        f"Projeção somada (nacional do build): Flávio {_n(nacional.get('flavio_2t'))}, "
        f"Lula {_n(nacional.get('lula_2t'))}. Locais onde Flávio já passa: "
        f"{_n(st['faltam_zero'])} de {_n(st['n_locais'])}."
    )
    add("")
    add("## PNAD")
    add("")
    add(
        f"Preços de {pnad['mes_precos']} (fator IPCA {_n(pnad['fator_ipca'], 5)} sobre "
        f"{pnad['mes_base']}); salário mínimo de 2026: R$ {_n(pnad['salario_minimo_2026'])}. "
        f"Células substituídas por terem menos de 30 observações: "
        f"{_n(pnad['celulas_substituidas'])}."
    )
    add("")
    add("## Tempos por UF (s)")
    add("")
    add(", ".join(f"{uf} {_n(s, 1)}" for uf, s in meta["tempos"].items()))
    add("")
    ARQUIVO.write_text("\n".join(lin), encoding="utf-8")
    return ARQUIVO
