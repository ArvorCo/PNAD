/// The X.509 certificate an urna carries in its signature file, and the
/// check that TSE's urna certification authority issued it.
library;

import 'dart:convert';

import 'der.dart';
import 'ed521.dart';

/// Ed521 public keys of TSE's urna CAs, pinned here: a key read from the
/// file being checked would prove nothing.
///
/// Certificates via github.com/doccaz/urnas-br (`docv2/python/lib/mr_util.py`,
/// from TSE's "formato-arquivos-bu-rdv-ass-digital-v2"); each key verifies
/// its CA's live CRL at https://acue20xx.tse.jus.br/lcr/acue20xx.crl
/// (checked 10/10/2026). Both CAs are issued by "AC URNA v2", which is not
/// pinned.
const tseUrnaCas = {
  // SHA-256 of the CA certificate (DER):
  // 6ae65790dae7cc5d97394e461204744c8e2f7a810d0303af828d4d3dbecfa293
  'AC UE2022':
      '371388c00ed81269ca7dd05735396caa96a8205efd7e2e96cf16557b52475e64e928'
      '9eb647684bcee2464d889b7155cec8af24f2be4d21a1a3ab15805cdf55d4ec00',
  'AC UE2020':
      '5d3d764d1123a914efbf93892db3b63d2f3c5d37a0f14a2d36d44905cc7428b97435'
      '5171df78c2a064e630b308b061a47fb0bd55715fc5b69419bfc92ed570aeb901',
};

const _ed521Oid = [0x2b, 0x06, 0x01, 0x04, 0x01, 0x82, 0xdc, 0x2c, 0x02, 0x01];
const _commonNameOid = [0x55, 0x04, 0x03];

class UrnaCertificate {
  UrnaCertificate._({
    required this.der,
    required this.subject,
    required this.issuer,
    required this.isEd521,
    required this.publicKey,
    required this.signedPart,
    required this.signature,
  });

  final List<int> der;

  /// Common names, e.g. `UEAO02293919` issued by `AC UE2022`.
  final String subject;
  final String issuer;

  /// Both the certificate's key and its issuer's signature are Ed521.
  final bool isEd521;
  final List<int> publicKey;

  /// The TBS certificate bytes the issuer signed, and its signature.
  final List<int> signedPart;
  final List<int> signature;

  /// Parses a PEM or DER certificate. Throws [FormatException] otherwise.
  static UrnaCertificate parse(List<int> bytes) {
    try {
      final der = _isPem(bytes) ? _pemToDer(bytes) : bytes;
      // Certificate ::= SEQUENCE { tbs, signatureAlgorithm, signature }.
      final cert = DerNode.parse(der).children;
      final tbs = cert[0];
      final fields = tbs.children;
      // tbs: [0] version, serial, signature, issuer, validity, subject, spki.
      final first = fields[0].isContext(0) ? 1 : 0;
      final spki = fields[first + 5].children;
      final keyBits = spki[1].bytes;
      return UrnaCertificate._(
        der: der,
        subject: _commonName(fields[first + 4]),
        issuer: _commonName(fields[first + 2]),
        isEd521:
            _same(spki[0].children[0].bytes, _ed521Oid) &&
            _same(cert[1].children[0].bytes, _ed521Oid),
        publicKey: keyBits.sublist(1),
        signedPart: tbs.encoded,
        signature: cert[2].bytes.sublist(1),
      );
    } on FormatException {
      rethrow;
    } on Object catch (e) {
      throw FormatException('Certificate: unexpected layout ($e)');
    }
  }

  /// Signed by one of TSE's urna CAs ([tseUrnaCas]), named as its issuer.
  bool issuedByTse() {
    final caKey = tseUrnaCas[issuer];
    if (caKey == null || !isEd521) return false;
    return Ed521.verify(
      publicKey: _hex(caKey),
      message: signedPart,
      signature: signature,
    );
  }

  static String _commonName(DerNode name) {
    for (final rdn in name.children) {
      for (final atv in rdn.children) {
        final parts = atv.children;
        if (_same(parts[0].bytes, _commonNameOid)) return parts[1].asString;
      }
    }
    return '';
  }

  static bool _isPem(List<int> b) =>
      b.length > 10 && latin1.decode(b.sublist(0, 10)) == '-----BEGIN';

  static List<int> _pemToDer(List<int> pem) {
    final body = ascii
        .decode(pem, allowInvalid: true)
        .split('\n')
        .map((l) => l.trim())
        .where((l) => l.isNotEmpty && !l.startsWith('-----'))
        .join();
    return base64.decode(body);
  }

  static List<int> _hex(String s) => [
    for (var i = 0; i < s.length; i += 2)
      int.parse(s.substring(i, i + 2), radix: 16),
  ];

  static bool _same(List<int> a, List<int> b) {
    if (a.length != b.length) return false;
    for (var i = 0; i < a.length; i++) {
      if (a[i] != b[i]) return false;
    }
    return true;
  }
}
