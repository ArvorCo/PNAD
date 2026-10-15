"""Resumo de durações e estados de cobertura, sem transformar ausência em zero."""

from __future__ import annotations

from collections import Counter

SITUACOES = {
    "lido": "Log lido e vinculado ao BU",
    "sem_nome": "Catálogo anterior sem nome de log",
    "nao_instalada": "Seção marcada como não instalada no catálogo oficial",
    "apuracao_sem_log": "BU do sistema de apuração sem log VOTA no hash arquivado",
    "sem_hash_transmissao": "Catálogo sem hash de transmissão",
    "download_pendente": "Download ainda pendente",
    "erro": "Falha de download após tentativas",
    "http_404": "Arquivo não localizado no endereço oficial (404)",
    "formato_invalido": "Resposta recebida não é ZIP",
    "hash_divergente": "SHA-256 difere do original arquivado",
    "sem_bu": "Log recuperado sem BU disponível para reconciliação",
    "processamento_pendente": "Aguardando a versão atual do leitor",
    "erro_leitura": "Pacote não interpretado pelo leitor",
}


def situacao(
    cat: dict,
    download: str | None,
    processamento: str | None,
    tem_bu: bool,
    tipo_arquivo: int | None = None,
):
    if processamento == "ok":
        return "lido"
    if processamento == "erro":
        return "erro_leitura"
    if not cat["nome"]:
        if cat.get("status_aux") == "Nao instalada":
            return "nao_instalada"
        if tipo_arquivo in (3, 4, 5, 6):
            return "apuracao_sem_log"
        return "sem_nome"
    if not cat["hash"]:
        return "sem_hash_transmissao"
    if download is None:
        return "download_pendente"
    if download != "ok":
        return download
    return "processamento_pendente" if tem_bu else "sem_bu"


def quantil(h: Counter, p: float):
    """Quantil interpolado da distribuição de ciclos, sem expandir milhões deles."""
    n = sum(h.values())
    if not n:
        return None
    pos = (n - 1) * p
    baixo, alto = int(pos), min(int(pos) + 1, n - 1)
    acumulado, a, b = 0, None, None
    for tempo, freq in sorted(h.items()):
        if acumulado <= baixo < acumulado + freq:
            a = tempo
        if acumulado <= alto < acumulado + freq:
            b = tempo
            break
        acumulado += freq
    return round(a + (b - a) * (pos - baixo), 3)


def duracoes(h: Counter):
    n = sum(h.values())
    return {
        "ciclos": n,
        "media_s": round(sum(t * v for t, v in h.items()) / n, 3) if n else None,
        "mediana_s": quantil(h, 0.5),
        "p90_s": quantil(h, 0.9),
        "histograma": sorted(h.items()),
    }
