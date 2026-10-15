// Cadeia de hashes dos QR Codes do boletim (manual TSE 2026, seções 1.4.3 e 1.6.1).
//
//   hash1 = SHA512(dados1)
//   hashN = SHA512(conteudo(N-1) + " " + dadosN)
//   conteudo(N-1) = "dados1 HASH:hash1 dados2 HASH:hash2 ... dados(N-1) HASH:hash(N-1)"
//
// "dados" é o trecho de conteúdo de cada QR, sem o cabeçalho "QRBU:i:n VRQR:x.y" e sem os campos
// de segurança. O espaço retirado na quebra entre QR Codes volta na junção, como manda o manual.
// O conteúdo acumulado usa o HASH declarado no QR (texto impresso), não o recalculado, que é o
// que a urna encadeou. Como o hash é cumulativo, alterar os dados de um QR Code quebra o elo dele
// e todos os seguintes; alterar só o último quebra apenas o último. SHA-512 em hexadecimal maiúsculo.
import { sha512 } from "@noble/hashes/sha2.js";
import { asciiParaBytes, bytesParaHex } from "./bytes.ts";

export interface EloCadeia {
  indice: number;
  hashDeclarado: string;
  hashCalculado: string;
  confere: boolean;
}

export interface ResultadoCadeia {
  ok: boolean;
  elos: EloCadeia[];
  /** HASH declarado no último QR Code, que é o valor assinado pela urna. */
  ultimoHash: string;
  /** Texto completo "dados1 HASH:h1 ... dadosN HASH:hN" sobre o qual a cadeia foi calculada. */
  conteudoEncadeado: string;
}

export function sha512Hex(texto: string): string {
  return bytesParaHex(sha512(asciiParaBytes(texto)));
}

/** Recalcula a cadeia sobre as partes já ordenadas por índice. */
export function verificarCadeia(partes: ReadonlyArray<{ indice: number; dados: string; hash: string }>): ResultadoCadeia {
  const elos: EloCadeia[] = [];
  let acumulado = "";
  for (const parte of partes) {
    const entrada = acumulado === "" ? parte.dados : `${acumulado} ${parte.dados}`;
    const hashCalculado = sha512Hex(entrada);
    elos.push({ indice: parte.indice, hashDeclarado: parte.hash, hashCalculado, confere: hashCalculado === parte.hash });
    acumulado = `${entrada} HASH:${parte.hash}`;
  }
  return {
    ok: elos.length > 0 && elos.every((e) => e.confere),
    elos,
    ultimoHash: partes.at(-1)?.hash ?? "",
    conteudoEncadeado: acumulado,
  };
}
