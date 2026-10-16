"""Eventos e ciclos do VOTA, mantendo desconhecidos e falhas de leitura explícitos.

Só agregados por seção saem deste módulo. Não exporta identificadores de mesários,
sequências individuais, opções digitadas nem associações entre eleitor e voto.
"""

from __future__ import annotations

import io
import re
import statistics
import zipfile
from collections import Counter, defaultdict
from itertools import pairwise

from .cronologia import preparacao_anterior
from .processo import resumir

VERSAO = "12"
DIAS = {"04/10/2026": 0, "05/10/2026": 86400}
MAX_DESCOMPRIMIDO = 80_000_000
RE_MESARIO = re.compile(r"^Mesário \d+ habilitou o eleitor$")
RE_ASSINATURA = re.compile(
    r"Verificação de assinatura - Etapa \[\d+\] - \[(.*?)\] - \[(.*?)\]"
)
METADADOS = (
    ("Município:", "mun"),
    ("Zona Eleitoral:", "zona"),
    ("Seção Eleitoral:", "secao"),
    ("Fase da UE:", "fase"),
)
CRITICOS = {
    "Eleitor foi habilitado",
    "O voto do eleitor foi computado",
    "Aguardando digitação do identificador do eleitor",
}


def texto_critico_alterado(msg: str) -> bool:
    """Sinaliza quase correspondência, sem corrigir ou contar o evento por aproximação."""
    if msg in CRITICOS or not msg.startswith(
        ("Eleitor foi ", "O voto ", "Aguardando ")
    ):
        return False
    return any(
        len(msg) == len(c)
        and sum(a != b for a, b in zip(msg, c, strict=True)) in (1, 2)
        for c in CRITICOS
    )


def textos_zip(raw: bytes) -> list[tuple[str, str]]:
    """ZIPs aninhados de contingência; sem extração em disco e com teto de expansão."""
    out = []
    tamanho = 0

    def ler(b: bytes, prefixo: str, nivel: int):
        nonlocal tamanho
        if nivel > 5:
            raise ValueError("Mais de cinco níveis de ZIP")
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                tamanho += info.file_size
                if tamanho > MAX_DESCOMPRIMIDO:
                    raise ValueError("Log excede limite de expansão")
                conteudo = z.read(info)
                nome = prefixo + info.filename
                if conteudo.startswith(b"PK\x03\x04"):
                    ler(conteudo, nome + "/", nivel + 1)
                elif info.filename.lower().endswith((".dat", ".txt", ".log")):
                    out.append((nome, conteudo.decode("latin1")))
                else:
                    raise ValueError("Membro do log com formato não reconhecido")

    ler(raw, "", 0)
    if not out:
        raise ValueError("ZIP sem texto de log")
    return out


def segundos(data: str) -> int:
    return (
        DIAS[data[:10]]
        + int(data[11:13]) * 3600
        + int(data[14:16]) * 60
        + int(data[17:19])
    )


def distribuicao(valores: list[int]) -> dict:
    if not valores:
        return {
            "n": 0,
            "media": None,
            "p10": None,
            "p50": None,
            "p90": None,
            "max": None,
        }
    v = sorted(valores)

    def q(p):
        pos = p * (len(v) - 1)
        i = int(pos)
        return round(v[i] + (v[min(i + 1, len(v) - 1)] - v[i]) * (pos - i), 2)

    return {
        "n": len(v),
        "media": round(statistics.mean(v), 3),
        "p10": q(0.1),
        "p50": q(0.5),
        "p90": q(0.9),
        "max": max(v),
    }


def fases_da_bateria(
    instantes: list[int], zeresimas: list[int], computados: list[int]
) -> tuple[dict[str, int], list[int]]:
    """Quando a urna passou para a bateria: antes da zerésima, entre a zerésima e o
    primeiro voto, durante a votação (do primeiro ao último cômputo) ou depois.

    Devolve as contagens por fase e os instantes da fase de votação, que a publicação
    cruza entre seções do mesmo município. Sem zerésima, tudo antes do primeiro voto
    conta como pré-votação; sem cômputo, tudo conta como pré-zerésima ou pré-votação.
    """
    fases = Counter()
    votacao = []
    zer = min(zeresimas) if zeresimas else None
    primeiro = min(computados) if computados else None
    ultimo = max(computados) if computados else None
    for t in instantes:
        if zer is not None and t < zer:
            fases["pre_zeresima"] += 1
        elif primeiro is None or t < primeiro:
            fases["pre_votacao"] += 1
        elif t <= ultimo:
            fases["votacao"] += 1
            votacao.append(t)
        else:
            fases["pos_votacao"] += 1
    return dict(fases), sorted(votacao)


def analisar(raw: bytes, identidade: dict | None = None) -> dict:
    arquivos = textos_zip(raw)
    cont = Counter()
    membros = []
    identidades = defaultdict(dict)
    fases = defaultdict(set)
    modelos = defaultdict(set)
    eventos = []
    vistos = set()
    anteriores = defaultdict(dict)
    for nome, texto in arquivos:
        local = []
        anterior = {}
        historico = preparacao_anterior(nome, texto)
        for linha in texto.splitlines():
            a = linha.split("\t")
            if len(a) != 6:
                if linha.strip():
                    cont["linhas_invalidas"] += 1
                continue
            data, nivel, urna, app, msg, _ = a
            cont["linhas_total"] += 1
            if data[:10] not in DIAS:
                # Uma urna pode permanecer ligada desde a véspera. Sua identidade
                # não precisa reaparecer no dia 4; só usar o último metadado
                # anterior, nunca substituir um metadado do próprio dia.
                ordem = data[6:10] + data[3:5] + data[:2] + data[11:19]
                if len(data) == 19 and ordem[:8] < "20261004":
                    pares = [
                        (campo, msg.split(":", 1)[1].strip())
                        for prefixo, campo in METADADOS
                        if msg.startswith(prefixo)
                    ]
                    if "Modelo de Urna:" in msg:
                        pares.append(("modelo", msg.split(":", 1)[1].strip()))
                    for campo, valor in pares:
                        if (
                            campo not in anteriores[urna]
                            or ordem > anteriores[urna][campo][0]
                        ):
                            anteriores[urna][campo] = (ordem, valor)
                continue
            if historico:
                cont["eventos_preparacao_excluidos"] += 1
                continue
            try:
                t = segundos(data)
            except (ValueError, IndexError):
                cont["linhas_invalidas"] += 1
                continue
            if urna in anterior and t < anterior[urna]:
                cont["recuos_relogio"] += 1
                cont["recuo_max_s"] = max(cont["recuo_max_s"], anterior[urna] - t)
            anterior[urna] = t
            if linha in vistos:
                cont["linhas_duplicadas"] += 1
                continue
            vistos.add(linha)
            if msg.startswith("Fase da UE:"):
                fases[urna].add(msg.split(":", 1)[1].strip())
            if "Modelo de Urna:" in msg:
                modelos[urna].add(msg.split(":", 1)[1].strip())
            for prefixo, campo in (
                ("Município:", "mun"),
                ("Zona Eleitoral:", "zona"),
                ("Seção Eleitoral:", "secao"),
            ):
                if msg.startswith(prefixo):
                    identidades[urna][campo] = msg.split(":", 1)[1].strip()
            local.append((t, urna, app, nivel, msg))
        if local:
            membros.append({"arquivo": nome, "eventos": len(local)})
            eventos.extend(local)
    # A ordem temporal emenda fragmentos de contingência. Em um arquivo único
    # com recuo de relógio, porém, vale a sequência de escrita: ordenar pelo
    # carimbo pode mover uma partida anterior para dentro de um ciclo posterior.
    # Recuos sempre invalidam as durações, inclusive quando a contagem fecha.
    if len(membros) != 1 or not cont["recuos_relogio"]:
        eventos.sort(key=lambda x: x[0])
    for urna, meta in anteriores.items():
        for campo in ("mun", "zona", "secao"):
            if campo not in identidades[urna] and campo in meta:
                identidades[urna][campo] = meta[campo][1]
        if not fases[urna] and "fase" in meta:
            fases[urna].add(meta["fase"][1])
        if not modelos[urna] and "modelo" in meta:
            modelos[urna].add(meta["modelo"][1])
    permitidas = set()
    for _, u, _, _, _ in eventos:
        if u in permitidas:
            continue
        if fases[u] and fases[u] != {"Oficial"}:
            continue
        if identidade:
            ids = identidades[u]
            conflita = any(
                int(ids[k]) != int(identidade[k]) for k in ids if k in identidade
            )
            propria = str(identidade.get("numero_interno_urna", "")).zfill(8) == u
            if conflita or not (len(ids) == 3 or propria):
                continue
        permitidas.add(u)
    cont["urnas_excluidas"] = len({e[1] for e in eventos} - permitidas)
    ciclos = []
    estados = {}
    inicios, zerésimas, encerramentos, computados = [], [], [], []
    erros = Counter()
    avisos = Counter()
    ultimo_por_urna = {}
    encerradas = set()
    reinicios_em_voto = 0
    assinaturas = defaultdict(list)
    horarios_erros = []
    sessoes, ordens = Counter(), Counter()
    inspecoes = {}
    duracoes_inspecao = []
    ocorrencias = []
    bateria_t = []

    def vazio():
        return {
            "ident": None,
            "identificacoes": 0,
            "cancelamento": False,
            "hab": None,
            "tipo": "desconhecida",
            "tentativas": 0,
            "cargos": 0,
            "parcial": False,
            "manual": False,
            "dado_confere": False,
        }

    for t, urna, app, nivel, msg in eventos:
        if urna not in permitidas:
            continue
        cont["eventos_dia"] += 1
        if texto_critico_alterado(msg):
            cont["mensagens_criticas_alteradas"] += 1
        if nivel in ("ERRO", "FATAL"):
            cont["erros"] += 1
            horarios_erros.append(t)
            # Catálogo sem números pessoais, caminhos ou conteúdo arbitrário.
            categoria = next(
                (
                    x
                    for x in (
                        "impress",
                        "mídia",
                        "assinatura",
                        "biometr",
                        "teclado",
                        "bateria",
                    )
                    if x in msg.lower()
                ),
                "outros",
            )
            erros[categoria] += 1
        if nivel == "ALERTA":
            cont["alertas"] += 1
        baixa = msg.lower()
        assinatura = RE_ASSINATURA.fullmatch(msg)
        if assinatura:
            assinaturas[(urna, assinatura[1])].append(assinatura[2])
        if "assinatura" in baixa and (
            "[falha]" in baixa or "[erro]" in baixa or "inválid" in baixa
        ):
            cont["falhas_assinatura_declaradas"] += 1
        if "relógio" in baixa and any(x in baixa for x in ("ajust", "alter", "erro")):
            cont["ajustes_relogio"] += 1
        if "operando" in baixa and "bateria interna" in baixa:
            cont["eventos_bateria"] += 1
            bateria_t.append(t)
        if app == "LOGD" and msg.startswith("Urna ligada em "):
            cont["partidas_sistema"] += 1
            if urna in ultimo_por_urna and urna not in encerradas:
                cont["reinicios_sistema_em_votacao"] += 1
                ocorrencias.append({"tipo": "reinicio_sistema", "segundo": t})
            sessoes[urna] += 1
            if estados.get(urna, {}).get("hab") is not None:
                cont["ciclos_interrompidos"] += 1
            estados[urna] = vazio()
            inspecoes.pop(urna, None)
        if app != "VOTA":
            continue
        st = estados.setdefault(urna, vazio())
        if msg.startswith("Iniciando aplicação"):
            inicios.append(t)
            sessoes[urna] += 1
            inspecoes.pop(urna, None)
            if urna in ultimo_por_urna and urna not in encerradas:
                reinicios_em_voto += 1
                ocorrencias.append({"tipo": "reinicio_vota", "segundo": t})
            if st["hab"] is not None:
                cont["ciclos_interrompidos"] += 1
            estados[urna] = st = vazio()
        elif msg == "Gerando relatório [ZERÉSIMA] [TÉRMINO]":
            zerésimas.append(t)
        elif msg == "Procedimento de encerramento confirmado":
            encerramentos.append(t)
            encerradas.add(urna)
        elif msg == "Aguardando digitação do identificador do eleitor":
            if st["hab"] is not None:
                cont["ciclos_sem_computo"] += 1
            estados[urna] = st = vazio()
        elif msg == "Identificador do eleitor digitado pelo mesário":
            if st["hab"] is None:
                st["ident"] = t
                st["identificacoes"] += 1
                st["tipo"] = "desconhecida"
                st["manual"] = False
                st["tentativas"] = 0
        elif msg.startswith("Solicita digital. Tentativa"):
            st["tentativas"] += 1
        elif msg == "Tipo de habilitação do eleitor [biométrica]":
            st["tipo"] = "biometrica"
        elif msg == "Solicitação de dado pessoal do eleitor para habilitação manual":
            st["manual"] = True
        elif msg == "Dado digitado confere":
            st["dado_confere"] = True
        elif RE_MESARIO.match(msg) or msg.startswith(
            "Digital coletada bate com uma digital gravada após o registro inicial"
        ):
            if st["manual"]:
                st["tipo"] = "biografica"
        elif msg == "Ano de nascimento digitado é igual ao do cadastro":
            if not st["manual"]:
                st["tipo"] = "sem_biometria"
        elif msg == "Eleitor foi habilitado":
            cont["habilitacoes"] += 1
            if st["manual"] and st["dado_confere"] and st["tipo"] == "desconhecida":
                st["tipo"] = "biografica"
            if st["hab"] is not None:
                cont["habilitacoes_sobrepostas"] += 1
            st["hab"] = t
        elif msg.startswith("Voto confirmado para ["):
            st["cargos"] += 1
        elif msg == "Eleitor foi suspenso pelo mesário":
            cont["suspensoes"] += 1
            st["parcial"] = True
        elif msg == "Eleitor foi suspenso e não confirmou nenhum voto":
            cont["suspensoes_sem_voto"] += 1
            estados[urna] = vazio()
        elif msg == "Eleitor votou parcialmente e em seguida foi suspenso":
            cont["suspensoes_parciais"] += 1
            st["parcial"] = True
        elif msg == "Atribuido voto nulo por suspensão [Presidente]":
            cont["nulos_presidente_suspensao"] += 1
        elif msg == "O voto do eleitor foi computado":
            cont["computados"] += 1
            computados.append(t)
            ultimo_por_urna[urna] = t
            ordens[urna] += 1
            if st["hab"] is None:
                cont["computados_sem_habilitacao"] += 1
            else:
                ciclos.append(
                    {
                        **st,
                        "fim": t,
                        "urna": urna,
                        "sessao": sessoes[urna],
                        "ordem": ordens[urna],
                    }
                )
            estados[urna] = vazio()
        elif "cancelada" in baixa and "habilitação" in baixa:
            cont["habilitacoes_canceladas"] += 1
            st["cancelamento"] = True
            ocorrencias.append({"tipo": "cancelamento_habilitacao", "segundo": t})
            # Há logs reais em que o pedido de cancelamento cruza com a captura
            # ainda em andamento e o eleitor é habilitado logo depois. O ciclo só
            # termina quando o VOTA volta a aguardar outro identificador.
        elif msg == "Inspeção da urna iniciada":
            cont["inspecoes_iniciadas"] += 1
            inspecoes[urna] = t
        elif msg == "Inspeção da urna terminada":
            cont["inspecoes_terminadas"] += 1
            inicio = inspecoes.pop(urna, None)
            if inicio is not None and t >= inicio:
                duracoes_inspecao.append(t - inicio)
                ocorrencias.append({"tipo": "inspecao", "segundo": inicio, "fim_s": t})
        elif msg == "Eleitor voltou a digitar enquanto estava sendo suspenso":
            cont["retomadas_inatividade"] += 1
        elif msg == "O eleitor identificado já votou":
            cont["identificacao_ja_votou"] += 1
        elif msg.startswith("Eleitor sem atividade por"):
            cont["avisos_inatividade"] += 1
        if nivel == "ALERTA":
            categoria = (
                "digitacao"
                if any(x in baixa for x in ("inválid", "diferente", "identificador"))
                else "outros"
            )
            avisos[categoria] += 1
    cont["ciclos_abertos"] = sum(s["hab"] is not None for s in estados.values())
    cont["reinicios_durante_votacao"] = reinicios_em_voto
    cont["partidas_vota"] = len(inicios)
    cont["zeresimas"] = len(zerésimas)
    cont["encerramentos"] = len(encerramentos)
    completos = [c for c in ciclos if not c["parcial"] and c["cargos"] > 0]
    invalidar = bool(cont["recuos_relogio"] or cont["ajustes_relogio"])
    resolvidas = 0
    for resultados in assinaturas.values():
        sucesso = False
        for resultado in reversed(resultados):
            if resultado == "SUCESSO":
                sucesso = True
            elif resultado in ("ERRO", "FALHA") and sucesso:
                resolvidas += 1
    cont["falhas_assinatura_com_sucesso_posterior"] = 0 if invalidar else resolvidas
    cont["falhas_assinatura_sem_sucesso_localizado"] = (
        0 if invalidar else cont["falhas_assinatura_declaradas"] - resolvidas
    )
    cont["falhas_assinatura_ordem_incerta"] = (
        cont["falhas_assinatura_declaradas"] if invalidar else 0
    )
    cont["erros_na_janela_votacao"] = (
        sum(
            min(c["hab"] for c in ciclos) <= t <= max(computados)
            for t in horarios_erros
        )
        if ciclos and computados and not invalidar
        else None
    )
    processo = resumir(ciclos, invalidar, distribuicao)
    fases_bateria, bateria_votacao = fases_da_bateria(bateria_t, zerésimas, computados)
    grupos = {}
    for n in sorted({c["cargos"] for c in completos}):
        g = [c for c in completos if c["cargos"] == n]
        grupos[str(n)] = distribuicao(
            [] if invalidar else [c["fim"] - c["hab"] for c in g]
        )
    tipos = Counter(c["tipo"] for c in ciclos)
    duracoes = [] if invalidar else [c["fim"] - c["hab"] for c in completos]
    habilitacao = (
        []
        if invalidar
        else [c["hab"] - c["ident"] for c in ciclos if c["ident"] is not None]
    )
    intervalos = [] if invalidar else [b - a for a, b in pairwise(computados)]
    # Histograma permite média nacional ponderada por ciclos sem microdados.
    hist = Counter(duracoes)
    return {
        "versao_parser": VERSAO,
        "processo_observado": processo,
        "inspecoes": distribuicao([] if invalidar else duracoes_inspecao),
        "ocorrencias_operacionais": ocorrencias,
        "bateria_fases": fases_bateria,
        "bateria_votacao_segundos": bateria_votacao,
        "contagens": dict(cont),
        "membros": membros,
        "urnas": len(permitidas),
        "modelos": sorted({m for u in permitidas for m in modelos[u]}),
        "tipos_habilitacao_computados": dict(tipos),
        "ciclos": len(ciclos),
        "tempo_voto": distribuicao(duracoes),
        "tempo_habilitacao": distribuicao(habilitacao),
        "intervalo_computados": distribuicao(intervalos),
        "tempo_por_cargos": grupos,
        "histograma_voto": sorted(hist.items()),
        "tempos_validos": not invalidar,
        "primeiro_computo_s": min(computados) if computados else None,
        "ultimo_computo_s": max(computados) if computados else None,
        "zeresima_antes": bool(
            zerésimas and computados and min(zerésimas) <= min(computados)
        ),
        "encerramento_depois": bool(
            encerramentos and computados and max(encerramentos) >= max(computados)
        ),
        "erros_categoria": dict(erros),
        "alertas_categoria": dict(avisos),
    }
