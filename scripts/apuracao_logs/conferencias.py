"""Exemplos conferidos no original, com evidência também contrária ao alarme."""

from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter

from .coleta import DESTINO, ORIGEM, url
from .parser import VERSAO, analisar, textos_zip
from .processamento import reconciliar

CASOS = [
    ("am", "98353", 56, 19, "assinatura", "Erro seguido de verificação bem-sucedida"),
    (
        "go",
        "95630",
        46,
        55,
        "contingencia_conciliada",
        "Dois fragmentos, contagem conciliada",
    ),
    (
        "sp",
        "71072",
        2,
        35,
        "contagem_divergente",
        "Contingência com trecho anterior não localizado",
    ),
    (
        "rj",
        "60011",
        8,
        61,
        "texto_malformado",
        "O texto original contém caracteres inesperados",
    ),
    (
        "pa",
        "04057",
        16,
        67,
        "relogio",
        "Relógio ajustado, contagens conciliadas",
    ),
    (
        "ba",
        "39934",
        183,
        175,
        "identidade_nao_confirmada",
        "O pacote também contém registros de outra seção",
    ),
]


def conferir():
    raw = sqlite3.connect(f"file:{DESTINO}?mode=ro", uri=True)
    src = sqlite3.connect(f"file:{ORIGEM}?mode=ro", uri=True)
    raw.row_factory = src.row_factory = sqlite3.Row
    casos = []
    for uf, mun, zona, secao, tipo, titulo in CASOS:
        key = (uf, mun, zona, secao)
        arq = raw.execute(
            "SELECT a.*,c.hash,c.nome,c.sha256_esperado FROM arquivos a JOIN catalogo c USING(uf,mun,zona,secao) WHERE uf=? AND mun=? AND zona=? AND secao=? AND a.status='ok'",
            key,
        ).fetchone()
        bu = src.execute(
            "SELECT * FROM bu WHERE uf=? AND mun=? AND zona=? AND secao=?", key
        ).fetchone()
        if not arq or not bu:
            continue
        arq, bu = dict(arq), dict(bu)
        assert hashlib.sha256(arq["zip"]).hexdigest() == arq["sha256"]
        r = reconciliar(analisar(arq["zip"], bu), bu)
        texto = "\n".join(t for _, t in textos_zip(arq["zip"]))
        computos = Counter(
            campos[2]
            for linha in set(texto.splitlines())
            if len(campos := linha.split("\t")) == 6
            and campos[0][:10] == "04/10/2026"
            and campos[4] == "O voto do eleitor foi computado"
        )
        if tipo == "assinatura":
            assert r["contagens"]["falhas_assinatura_com_sucesso_posterior"] > 0
            leitura = "A verificação de /dsk/fe/estatico/infomidia.vsc registrou ERRO às 06:56:39 e SUCESSO às 07:00:19. As três categorias de habilitação e o comparecimento fecham com o BU. O sucesso posterior faz parte do registro e não deve ser omitido."
            limite = "São mensagens do próprio sistema, sem validação criptográfica independente nesta análise."
        elif tipo == "contingencia_conciliada":
            assert r["contagem_confere"] and r["biometria_confere"]
            assert sorted(computos.values()) == [135, 136]
            leitura = "O pacote reúne 135 cômputos de uma urna e 136 da outra. A identidade da primeira está registrada na véspera, quando ela já estava ligada. A leitura conjunta reconcilia 271 cômputos, 271 ciclos e as três categorias com o BU."
            limite = "Uma contagem baseada só no arquivo final perderia o fragmento anterior. Este exemplo mostra por que é preciso abrir o pacote completo."
        elif tipo == "relogio":
            assert r["contagem_confere"] and r["biometria_confere"]
            assert not r["tempos_validos"] and r["ciclos"] == 260
            assert r["contagens"]["recuo_max_s"] == 3381
            assert "Iniciando aplicação AJUSTE DE DATA E HORA" in texto
            leitura = "O registro passa de 08:32:21 para 07:36:00 e contém a aplicação de ajuste de data e hora. Preservando a ordem de escrita do arquivo, os 260 cômputos, os 260 ciclos e as categorias de habilitação fecham com o BU. As durações ficam fora das comparações."
            limite = "Ordenar esses eventos apenas pelo carimbo criaria um ciclo incompleto artificial. A inconsistência do relógio exige separar a confiabilidade dos tempos da reconciliação das contagens."
        elif tipo == "identidade_nao_confirmada":
            assert r["contagens"]["urnas_excluidas"] == 1
            assert r["contagens"]["computados"] == 136 and bu["comparecimento"] == 272
            assert "Seção Eleitoral: 0181" in texto
            assert computos["02423907"] == 100
            leitura = "O pacote da seção 175 inclui um fragmento identificado como seção 181. Os 100 cômputos desse identificador foram excluídos; não podem ser atribuídos à seção 175. Os dois identificadores compatíveis com a seção 175 somam 136 cômputos, contra 272 comparecimentos no BU."
            limite = "A diferença restante pede os registros corretos das urnas e da contingência. Misturar o fragmento de outra seção não reconcilia o documento nem demonstra transferência de votos."
        elif tipo == "contagem_divergente":
            assert r["contagens"]["computados"] == 232 and bu["comparecimento"] == 247
            assert "Contingência executada com sucesso" in texto
            leitura = "O BU registra 247 comparecimentos; os dois fragmentos fornecidos registram 232 cômputos. Os registros do dia começam às 10:18 e às 10:53; há mensagem de contingência executada com sucesso. Os 15 eventos anteriores não foram localizados no pacote consultado."
            limite = "É uma diferença documental a reconciliar com os registros anteriores e a ata. Não identifica votos adicionados ou retirados."
        else:
            assert "Eleitor foi ha`ilitado" in texto
            assert r["contagens"]["computados"] == bu["comparecimento"]
            leitura = f'O arquivo contém literalmente “Eleitor foi ha`ilitado”, além de outras mensagens com caracteres inesperados. Os {bu["comparecimento"]} eventos exatos de cômputo fecham com o BU; o leitor reconstrói {r["ciclos"]} ciclos, pois não corrige eventos por semelhança.'
            limite = "Os bytes coincidem com o SHA-256 arquivado. Isso localiza a limitação no documento consultado, sem identificar sua causa física nem demonstrar alteração de votos."
        casos.append(
            {
                "uf": uf.upper(),
                "mun": mun,
                "zona": zona,
                "secao": secao,
                "tipo": tipo,
                "titulo": titulo,
                "leitura": leitura,
                "limite": limite,
                "url": url(arq),
                "sha256": arq["sha256"],
                "hash_anterior_confere": (
                    arq["sha256"] == arq["sha256_esperado"]
                    if arq["sha256_esperado"]
                    else None
                ),
                "versao_parser": VERSAO,
            }
        )
    raw.close()
    src.close()
    return casos
