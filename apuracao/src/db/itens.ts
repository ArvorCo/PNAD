// Conversão de resultados normalizados em itens de lote para o Escritor.
import type { NormalizadoAb, NormalizadoCm, NormalizadoE, NormalizadoEleC, NormalizadoU } from "../parse/normalizar.ts";
import type { IdRef, ItemLote } from "./escrita.ts";

/** gzip nível 6 do corpo original, para a tabela blob. */
export function comprimir(corpo: Uint8Array<ArrayBuffer>): { gz: Uint8Array; bytes: number } {
  return { gz: Bun.gzipSync(corpo, { level: 6 }), bytes: corpo.byteLength };
}

export function sha256Hex(corpo: Uint8Array<ArrayBuffer> | string): string {
  return new Bun.CryptoHasher("sha256").update(corpo).digest("hex");
}

export function gunzipTexto(gz: Uint8Array<ArrayBuffer>): string {
  return new TextDecoder().decode(Bun.gunzipSync(gz));
}

export function itensDeU(n: NormalizadoU, snapshot: IdRef): ItemLote[] {
  const out: ItemLote[] = [
    { k: "totais", snapshot, row: n.totais },
    { k: "voto_agremiacao", snapshot, rows: n.votoAgremiacao },
    { k: "voto_partido", snapshot, rows: n.votoPartido },
  ];
  if (n.federacoes.length > 0) out.push({ k: "federacao", rows: n.federacoes });
  if (n.partidos.length > 0) out.push({ k: "partido", rows: n.partidos });
  if (n.incluiuCandidatos) {
    out.push({ k: "candidato", snapshot, rows: n.candidatos });
    out.push({ k: "voto_candidato", snapshot, rows: n.votoCandidato });
  }
  return out;
}

export function itensDeAb(n: NormalizadoAb, snapshot: IdRef): ItemLote[] {
  return n.entradas.length > 0 ? [{ k: "ab_estado", snapshot, rows: n.entradas }] : [];
}

export function itensDeE(n: NormalizadoE, snapshot: IdRef): ItemLote[] {
  return n.entradas.length > 0 ? [{ k: "e_entrada", snapshot, rows: n.entradas }] : [];
}

export function itensDeEleC(n: NormalizadoEleC): ItemLote[] {
  return [
    { k: "eleicao", rows: n.eleicoes },
    { k: "cargo", rows: n.cargos },
  ];
}

export function itensDeCm(n: NormalizadoCm): ItemLote[] {
  return [
    { k: "uf", rows: n.ufs },
    { k: "municipio", rows: n.municipios },
    { k: "zona", rows: n.zonas },
  ];
}
