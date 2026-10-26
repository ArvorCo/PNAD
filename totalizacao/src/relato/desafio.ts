// Barreiras contra robô sem terceiros para os relatos do Politize-se: desafio emitido pela
// própria função (carimbo de emissão + aleatório + HMAC-SHA256 com SAL_IP), prova de trabalho
// (sha256(desafio + nonce) com BITS_PROVA bits zero no início) e tempo mínimo entre abrir o
// formulário (pedir o desafio) e enviar. Funções puras, usadas pela Edge Function e pelos testes.

export const BITS_PROVA = 18;
export const TEMPO_MINIMO_MS = 8_000;
export const VALIDADE_MS = 10 * 60_000;
const RE_DESAFIO = /^(\d{13})\.([0-9a-f]{32})\.([0-9a-f]{64})$/;
const RE_NONCE = /^\d{1,12}$/;

const hex = (b: ArrayBuffer | Uint8Array) => Array.from(b instanceof Uint8Array ? b : new Uint8Array(b), (x) => x.toString(16).padStart(2, "0")).join("");

async function hmac(sal: string, msg: string): Promise<string> {
  const chave = await crypto.subtle.importKey("raw", new TextEncoder().encode(sal), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return hex(await crypto.subtle.sign("HMAC", chave, new TextEncoder().encode(`relato-desafio|${msg}`)));
}

/** Comparação em tempo constante de duas cadeias hex do mesmo tamanho. */
function iguais(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let d = 0;
  for (let i = 0; i < a.length; i++) d |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return d === 0;
}

export function zerosIniciais(bytes: Uint8Array, bits: number): boolean {
  let i = 0;
  for (; bits >= 8; bits -= 8, i++) if (bytes[i] !== 0) return false;
  return bits === 0 || ((bytes[i] ?? 255) >> (8 - bits)) === 0;
}

export async function emitirDesafio(sal: string, agoraMs: number, aleatorio?: string): Promise<string> {
  const r = aleatorio ?? hex(crypto.getRandomValues(new Uint8Array(16)));
  const t = String(Math.trunc(agoraMs)).padStart(13, "0");
  return `${t}.${r}.${await hmac(sal, `${t}.${r}`)}`;
}

export type Conferencia = { ok: true; emitidoMs: number } | { ok: false; motivo: string };

export async function conferirDesafio(sal: string, desafio: unknown, nonce: unknown, agoraMs: number, bits = BITS_PROVA): Promise<Conferencia> {
  if (typeof desafio !== "string" || typeof nonce !== "string") return { ok: false, motivo: "prova ausente" };
  const m = RE_DESAFIO.exec(desafio);
  if (m === null || !RE_NONCE.test(nonce)) return { ok: false, motivo: "prova malformada" };
  const [, t = "", r = "", assinatura = ""] = m;
  if (!iguais(assinatura, await hmac(sal, `${t}.${r}`))) return { ok: false, motivo: "desafio nao emitido por este servico" };
  const emitidoMs = Number(t);
  const idade = agoraMs - emitidoMs;
  if (idade < TEMPO_MINIMO_MS) return { ok: false, motivo: "envio rapido demais" };
  if (idade > VALIDADE_MS) return { ok: false, motivo: "desafio expirado" };
  const h = new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(desafio + nonce)));
  if (!zerosIniciais(h, bits)) return { ok: false, motivo: "prova de trabalho invalida" };
  return { ok: true, emitidoMs };
}

/** Hash do desafio para impedir reuso (gravado no relato, único). */
export async function hashDesafio(desafio: string): Promise<string> {
  return hex(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`uso|${desafio}`)));
}
