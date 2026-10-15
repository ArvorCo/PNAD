#!/usr/bin/env python3

import re
import binascii
import logging
import hashlib
import base64
import os
import asn1tools
from ecpy.curves import Curve
from ecpy.ecdsa import ECDSA
from ecpy.eddsa import EDDSA
from ecpy.keys import ECPublicKey
from asn1crypto import x509 as asn1_x509

# ASN.1 para leitura de SubjectPublicKeyInfo (com bloco DEFINITIONS)
_SUBJECT_PUBLIC_KEY_INFO_ASN1 = """
SubjectPublicKeyInfo DEFINITIONS ::= BEGIN
SubjectPublicKeyInfo ::= SEQUENCE {
    algorithm           AlgorithmIdentifier,
    subjectPublicKey    BIT STRING
}
AlgorithmIdentifier ::= SEQUENCE {
    algorithm   OBJECT IDENTIFIER,
    parameters  ANY OPTIONAL
}
END
"""
_SUBJECT_PUBLIC_KEY_INFO_DECODER = asn1tools.compile_string(_SUBJECT_PUBLIC_KEY_INFO_ASN1, codec="der")

def extrai_chave_publica_der(cert):
    try:
        # Agora recebe o objeto decodificado, não bytes
        spki_bytes = cert['tbs_certificate']['subject_public_key_info'].dump()
        spki = _SUBJECT_PUBLIC_KEY_INFO_DECODER.decode('SubjectPublicKeyInfo', spki_bytes)
        algo = spki['algorithm']['algorithm']
        pubkey_bytes = spki['subjectPublicKey'][0]
        if algo == "1.2.840.10045.2.1":  # ecPublicKey
            curve = Curve.get_curve('secp521r1')
            assert curve is not None, "Curva secp521r1 não encontrada"
            pubkey = ECPublicKey(curve.decode_point(pubkey_bytes))
            return pubkey, ECDSA(), algo
        elif algo == "1.3.6.1.4.1.44588.2.1": # Ed521
            curve = Curve.get_curve('Ed521')
            assert curve is not None, "Curva Ed521 não encontrada"
            pubkey = ECPublicKey(curve.decode_point(pubkey_bytes))
            return pubkey, EDDSA(hashlib.shake_256, hash_len=132), algo
        else:
            raise RuntimeError(f"Algoritmo de chave pública não suportado: {algo}")
    except Exception as e:
        logging.error(f"Falha ao extrair chave pública: {e}")
        raise

def extrai_certificado_der(cert_bytes):
    return asn1_x509.Certificate.load(cert_bytes)

def extrai_certificado_pem(cert_bytes):
    cert_ascii = cert_bytes.decode("ascii")
    pem_body = "".join(re.findall(r"-----BEGIN CERTIFICATE-----(.*)-----END CERTIFICATE-----", cert_ascii, re.DOTALL)).replace("\n", "")
    cert_der = base64.b64decode(pem_body)
    return asn1_x509.Certificate.load(cert_der)

def extrai_certificado(cert_bytes):
    try:
        return extrai_certificado_der(cert_bytes)
    except Exception:
        return extrai_certificado_pem(cert_bytes)

def verificar_cadeia_certificados(certificado, modelo):
    """Valida o certificado da UE diretamente contra o certificado raiz."""
    try:
        # Carrega certificado raiz
        script_dir = os.path.dirname(__file__)
        caminho_certificado_raiz = os.path.join(script_dir, 'certificados', f'ac_raiz_ue{modelo}_v1.pem')
        with open(caminho_certificado_raiz, 'rb') as f:
            root_pem = f.read()
        certificado_raiz = extrai_certificado(root_pem)
        # Extrai chave pública e verificador do certificado raiz
        chave_publica, verificador, algoritmo = extrai_chave_publica_der(certificado_raiz)

        # Obter dados a serem verificados e a assinatura do certificado
        tbs_bytes = certificado['tbs_certificate'].dump()
        sig_bytes = certificado['signature_value'].native
        logging.info(f"Validando assinatura do certificado da UE com algoritmo: {algoritmo}")

        # Para ECDSA, aplica SHA-512; para EdDSA, usa bytes crus
        if isinstance(verificador, ECDSA):
            msg = hashlib.sha512(tbs_bytes).digest()
        else:
            msg = tbs_bytes

        if verificador.verify(msg, sig_bytes, chave_publica):
            logging.info("Assinatura do certificado válida")
            return True
        else:
            logging.error("Assinatura do certificado inválida")
            return False
    except Exception as e:
        logging.error(f"Falha ao validar cadeia de certificados: {e}")
        return False

def verificar_assinatura(cert_text, assinatura, hash_bytes, modelo):
    certificado_bytes = binascii.unhexlify(cert_text)
    certificado = extrai_certificado(certificado_bytes)
    chave_publica, verificador, _ = extrai_chave_publica_der(certificado)

    if not verificar_cadeia_certificados(certificado, modelo):
        return False

    logging.info("Verificando assinatura do QR Code")
    msg = hashlib.sha512(hash_bytes).digest()
    try:
        assinatura_valida = verificador.verify(msg, assinatura, chave_publica)
    except (AssertionError, ValueError):
        assinatura_valida = False
    if assinatura_valida:
        logging.info("Assinatura verificada com sucesso!")
        return True
    else:
        logging.error("Verificação falhou.")
        return False

def ler_qrcodes_interativo():
    """
    Lê interativamente os QR codes do certificado e do BU, validando e montando as partes.
    Retorna o texto completo do certificado, um dicionário com os campos do BU e o modelo da urna.
    """
    def _ler_uma_parte():
        """Lê uma única parte do QR code do input do usuário."""
        print("\nEscaneie/copie o QR code (Enter duas vezes para finalizar, :reiniciar para recomeçar):")
        linhas = []
        while True:
            try:
                linha = input()
                if linha == '':
                    break
                if linha.strip() == ':reiniciar':
                    return None, None
                linhas.append(linha)
            except EOFError:
                if not linhas:
                    return None, {}
                break
        texto = '\n'.join(linhas)
        campos = parse_qrcode_text(texto) if texto.strip() else {}
        return texto, campos

    def _processa_parte(texto, campos, estado):
        """Valida e processa uma parte do QR code, atualizando o estado da leitura."""
        # Identifica o tipo (QRCE ou QRBU) e extrai o índice e o total
        tipo_chave = 'QRCE' if 'QRCE' in campos else 'QRBU' if 'QRBU' in campos else None
        if not tipo_chave or not campos.get(tipo_chave):
            print("Não foi possível identificar o tipo do QR code (QRCE/QRBU). Tente novamente.")
            return False

        try:
            idx, total_lido = map(int, campos[tipo_chave].split(':'))
        except (ValueError, AttributeError):
            print(f"Formato inválido para o campo {tipo_chave}. Tente novamente.")
            return False

        descricao_tipo = 'certificado' if tipo_chave == 'QRCE' else 'BU'

        # Valida o IDUE
        idue_atual = campos.get('IDUE')
        if idue_atual:
            if estado['idue_esperado'] is None:
                estado['idue_esperado'] = idue_atual
            elif idue_atual != estado['idue_esperado']:
                print(f"Este QR code pertence a uma urna diferente (esperado: {estado['idue_esperado']}, lido: {idue_atual}).")
                return False

        # Valida o total de partes
        if estado['total'][tipo_chave] is None:
            estado['total'][tipo_chave] = total_lido
        elif total_lido != estado['total'][tipo_chave]:
            print(f"Total de partes do {descricao_tipo} inconsistente (esperado: {estado['total'][tipo_chave]}, lido: {total_lido}).")
            return False

        # Verifica se a parte já foi lida
        if idx in estado['partes'][tipo_chave]:
            print(f"A parte {idx} do {descricao_tipo} já foi lida. Para substituir, reinicie a leitura.")
            return False

        # Armazena a parte e o modelo da urna (se aplicável)
        estado['partes'][tipo_chave][idx] = texto
        if tipo_chave == 'QRCE' and estado['modelo_ue'] is None and campos.get('MDUE'):
            estado['modelo_ue'] = campos.get('MDUE')

        print(f"Parte {idx} de {total_lido} do {descricao_tipo} registrada com sucesso.")
        return True

    def _leitura_completa(estado):
        """Verifica se todas as partes do certificado e do BU foram lidas."""
        qrce_completo = estado['total']['QRCE'] and len(estado['partes']['QRCE']) == estado['total']['QRCE']
        qrbu_completo = estado['total']['QRBU'] and len(estado['partes']['QRBU']) == estado['total']['QRBU']
        return qrce_completo and qrbu_completo

    # Estado inicial da leitura
    estado = {
        'partes': {'QRCE': {}, 'QRBU': {}},
        'total': {'QRCE': None, 'QRBU': None},
        'idue_esperado': None,
        'modelo_ue': None,
    }

    print("\nIniciando leitura dos QR codes do certificado e do BU.")

    while not _leitura_completa(estado):
        total_ce = estado['total']['QRCE']
        lidas_ce = len(estado['partes']['QRCE'])
        total_bu = estado['total']['QRBU']
        lidas_bu = len(estado['partes']['QRBU'])

        print(f"Status -> Certificado: {lidas_ce}/{total_ce or '?'} | BU: {lidas_bu}/{total_bu or '?'}")

        texto, campos = _ler_uma_parte()
        if texto is None:
            if campos is None:  # Sinal para reiniciar
                print("Leitura reiniciada pelo usuário.")
                return ler_qrcodes_interativo()
            print("Leitura encerrada antes de receber todos os QR Codes.")
            return None, None, None

        if not campos:
            print("QR code vazio ou inválido. Tente novamente.")
            continue

        _processa_parte(texto, campos, estado)

    print("\nTodos os QR codes foram lidos com sucesso!")

    # Monta o resultado final
    cert_text = ''.join(
        parse_qrcode_text(estado['partes']['QRCE'][i]).get('CERT', '')
        for i in sorted(estado['partes']['QRCE'])
    )
    bu_text = ' '.join(estado['partes']['QRBU'][i] for i in sorted(estado['partes']['QRBU']))
    bu_dict = parse_qrcode_text(bu_text)

    return cert_text.strip(), bu_dict, estado['modelo_ue']

def parse_qrcode_text(qr_text):
    """
    Recebe o texto de um QR code e retorna um dicionário campo/valor.
    O campo valor pode conter ':'.
    """
    result = {}
    campos = qr_text.strip().split()
    for campo in campos:
        if ':' in campo:
            chave, valor = campo.split(':', 1)
            result[chave] = valor
    return result

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("Por favor, escaneie os QR codes conforme solicitado.")
    cert_text, bu_dict, modelo_ue = ler_qrcodes_interativo()
    if bu_dict is None:
        raise SystemExit(1)
    assinatura = bu_dict.get('ASSI')
    hash_qr = bu_dict.get('HASH')

    # Validação dos campos extraídos
    if assinatura is None or hash_qr is None:
        logging.error("Não foi possível extrair assinatura ou hash do QR Code do BU. Verifique os dados lidos.")
        exit(1)

    assinatura_valida = verificar_assinatura(
        cert_text=cert_text,
        assinatura=bytes.fromhex(assinatura),
        hash_bytes=bytes.fromhex(hash_qr),
        modelo=modelo_ue)
    raise SystemExit(0 if assinatura_valida else 1)
