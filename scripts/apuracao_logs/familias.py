"""Famílias legíveis dos diagnósticos dos logs e nível de atenção para o mapa de fiscais.

Os 25 diagnósticos de ``criterios.py`` são técnicos e se sobrepõem (reinício do sistema e
reinício do VOTA costumam ser o mesmo episódio; ciclo não reconstruído costuma ser o
ciclo interrompido pelo reinício). Para um fiscal leigo, o mapa agrupa os diagnósticos
em cinco famílias com nome em português corrente e ordena as seções num nível de
atenção de 0 a 3. É ordenação para fiscalização, por regra declarada, não probabilidade
de irregularidade: os logs não alteram a pontuação histórica do capítulo 13.

Regra do nível de atenção (``atencao``):

- 3: ao menos um diagnóstico de conferência do arquivo (assinatura, relógio, contagem
  ou categorias não reconciliadas, zerésima ausente, texto malformado, identidade não
  confirmada) ou diagnósticos de três famílias diferentes;
- 2: diagnósticos de duas famílias diferentes, fora os de rotina;
- 1: um ou mais diagnósticos de uma só família, fora os de rotina;
- 0: só registros de rotina (operação com bateria, inspeção de cinco minutos ou mais).

As famílias seguem a co-ocorrência medida nos 499.176 logs (memorando de 16/10/2026):
ciclo não reconstruído acompanha reinício em 96% dos casos e fica em energia; retomadas
após inatividade e suspensões andam com votação lenta (lift 32) e ficam no ritmo;
inspeção longa e meia hora sem voto andam juntas (lift 4,7) e dependem do tamanho da
seção. Conferência do arquivo é só integridade e sobe sozinha ao nível 3.
"""

from __future__ import annotations

from collections.abc import Iterable

FAMILIAS: dict[str, dict] = {
    "energia": {
        "nome": "Energia e reinícios",
        "curto": "Energia",
        "explica": "A urna ligou de novo, usou a bateria, registrou erro técnico ou deixou um ciclo de votação sem fechar.",
        "conferir": "Pergunte à mesa a hora e o motivo; confira na ata se a contagem continuou de onde parou.",
        "criterios": [
            "bateria",
            "reinicio_sistema",
            "reinicios",
            "erro_tecnico",
            "ciclos_incompletos",
        ],
    },
    "identificacao": {
        "nome": "Identificação do eleitor",
        "curto": "Identificação",
        "explica": "Muitos eleitores liberados sem a digital, demora na habilitação ou habilitações canceladas.",
        "conferir": "Acompanhe a identificação: documento com foto, tentativas da digital e o que o mesário anota na ata.",
        "criterios": [
            "sem_biometria_alta",
            "biografica_alta",
            "identificacao_lenta",
            "cancelamentos_habilitacao",
        ],
    },
    "ritmo": {
        "nome": "Ritmo da votação",
        "curto": "Ritmo",
        "explica": "Votação mais lenta ou mais rápida que as urnas parecidas, suspensa várias vezes ou com muitas retomadas após tela parada.",
        "conferir": "Veja se houve dificuldade de uso, acessibilidade ou abandono; não associe horários a pessoas.",
        "criterios": [
            "tempo_lento",
            "tempo_rapido",
            "processo_rapido",
            "cadencia_rapida",
            "rajada_rapida",
            "retomadas_inatividade",
            "suspensoes",
        ],
    },
    "paradas": {
        "nome": "Pausas e inspeções",
        "curto": "Pausas",
        "explica": "Inspeção de cinco minutos ou mais, ou meia hora sem nenhum voto; em seção pequena, pausas longas são esperadas.",
        "conferir": "Peça o motivo de cada pausa e confira se consta na ata; inspeção também é rotina.",
        "criterios": ["inspecao_prolongada", "intervalo_longo"],
    },
    "arquivo": {
        "nome": "Conferência do arquivo",
        "curto": "Arquivo",
        "explica": "O arquivo do log não fecha com o boletim, tem relógio inconsistente, falha de assinatura ou trecho não reconhecido.",
        "conferir": "Preserve o original e peça conferência formal à Justiça Eleitoral; não é prova de alteração de voto.",
        "criterios": [
            "assinatura",
            "relogio",
            "contagem_divergente",
            "biometria_divergente",
            "zeresima_ausente",
            "texto_malformado",
            "identidade_nao_confirmada",
        ],
    },
}

FAMILIA_DE: dict[str, str] = {
    c: f for f, spec in FAMILIAS.items() for c in spec["criterios"]
}

ROTINA = frozenset({"bateria", "inspecao_prolongada"})
ARQUIVO_FORTE = frozenset(FAMILIAS["arquivo"]["criterios"])

NIVEIS_ATENCAO: dict[int, dict[str, str]] = {
    0: {
        "nome": "Registro de rotina",
        "frase": "Só bateria ou inspeção longa no log: registro operacional comum, sem outro sinal.",
    },
    1: {
        "nome": "Um sinal",
        "frase": "Um tipo de ocorrência no log, além da rotina.",
    },
    2: {
        "nome": "Sinais combinados",
        "frase": "Ocorrências de dois tipos diferentes no mesmo log.",
    },
    3: {
        "nome": "Conferir o arquivo",
        "frase": "O arquivo pede conferência formal, ou há ocorrências de três tipos diferentes.",
    },
}

# Nomes curtos, em português corrente, para o mapa e a lista. Os técnicos ficam no relatório.
NOME_CURTO: dict[str, str] = {
    "processo_rapido": "Digitação ao voto muito rápida",
    "cadencia_rapida": "Votos em sequência muito rápida",
    "rajada_rapida": "Trecho de dez votos muito rápido",
    "reinicio_sistema": "Urna ligou de novo durante a votação",
    "inspecao_prolongada": "Inspeção de cinco minutos ou mais",
    "retomadas_inatividade": "Muitas retomadas após tela parada",
    "cancelamentos_habilitacao": "Muitas habilitações canceladas",
    "tempo_rapido": "Votação muito mais rápida que as parecidas",
    "tempo_lento": "Votação muito mais lenta que as parecidas",
    "identificacao_lenta": "Habilitação demorada",
    "biografica_alta": "Muitos liberados sem reconhecer a digital",
    "sem_biometria_alta": "Muitos eleitores sem digital cadastrada",
    "suspensoes": "Votação suspensa várias vezes",
    "reinicios": "Aplicativo de votação reiniciado",
    "bateria": "Funcionou na bateria",
    "erro_tecnico": "Erro técnico registrado",
    "assinatura": "Falha de assinatura declarada",
    "relogio": "Relógio inconsistente",
    "ciclos_incompletos": "Ciclo de votação não reconstruído",
    "contagem_divergente": "Contagem do log difere do boletim",
    "biometria_divergente": "Categorias de identificação não fecham",
    "zeresima_ausente": "Zerésima não localizada no arquivo",
    "intervalo_longo": "Meia hora sem nenhum voto",
    "texto_malformado": "Trecho do log não reconhecido",
    "identidade_nao_confirmada": "Identidade da urna não confirmada",
}


def familias_de(sinais: Iterable[str]) -> list[str]:
    """Famílias presentes, na ordem declarada em ``FAMILIAS``."""
    presentes = {FAMILIA_DE[c] for c in sinais if c in FAMILIA_DE}
    return [f for f in FAMILIAS if f in presentes]


def atencao(sinais: Iterable[str]) -> int:
    """Nível de atenção de 0 a 3 pela regra declarada no cabeçalho do módulo."""
    s = [c for c in sinais if c in FAMILIA_DE]
    if not s:
        return 0
    fams = set(familias_de(s))
    if ARQUIVO_FORTE.intersection(s) or len(fams) >= 3:
        return 3
    fora_rotina = [c for c in s if c not in ROTINA]
    if not fora_rotina:
        return 0
    if len({FAMILIA_DE[c] for c in fora_rotina}) >= 2:
        return 2
    return 1


def catalogo(criterios: dict[str, dict]) -> dict:
    """Bloco ``logs.familias`` do índice do mapa: famílias com contagem de seções por critério."""
    out = {}
    for cod, spec in FAMILIAS.items():
        out[cod] = {
            "nome": spec["nome"],
            "curto": spec["curto"],
            "explica": spec["explica"],
            "conferir": spec["conferir"],
            "criterios": [c for c in spec["criterios"] if c in criterios],
        }
    return out
