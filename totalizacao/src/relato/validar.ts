// Validação do relato de seção (Politize-se) antes de qualquer acesso ao banco. Função pura,
// usada pela Edge Function receber-relato e pelos testes. O banco confere de novo pelas
// restrições da tabela relato_secao (migração 0005).

export const TIPOS_RELATO = [
  "fila_longa",
  "urna_trocada",
  "biometria_falhou",
  "votou_sem_biometria",
  "mesario_conduta",
  "boca_de_urna",
  "transporte_irregular",
  "local_mudou",
  "secao_fechou_cedo",
  "secao_fechou_tarde",
  "outro",
] as const;
export type TipoRelato = (typeof TIPOS_RELATO)[number];

export const UFS_RELATO = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA",
  "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO", "ZZ",
] as const;

export const MAX_TEXTO = 1000;
export const MAX_CONTATO = 120;
export const MAX_CORPO_BYTES = 8192;
export const LIMITE_POR_HORA = 5;

export type Relato = {
  turno: 1 | 2;
  uf: string;
  zona: number;
  secao: number;
  local_id: string | null;
  tipo: TipoRelato;
  texto: string;
  hora_aproximada: string | null;
  presenciou: boolean;
  contato: string | null;
  versao: string | null;
};

export type Validacao = { ok: true; relato: Relato } | { ok: false; motivo: string };

const RE_LOCAL = /^[A-Z]{2}-\d+-\d+-[A-Za-z0-9_-]+$/;
const RE_HORA = /^([01]\d|2[0-3]):[0-5]\d$/;
const RE_EMAIL = /^[^\s@<>"']{1,64}@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$/;
// Controles proibidos no texto livre (quebra de linha e tabulação ficam).
// eslint-disable-next-line no-control-regex
const RE_CONTROLE = /[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F‪-‮⁦-⁩]/;

function inteiro(v: unknown, min: number, max: number): number | null {
  const n = typeof v === "string" && /^\d{1,4}$/.test(v) ? Number(v) : v;
  return typeof n === "number" && Number.isInteger(n) && n >= min && n <= max ? n : null;
}

/** Contato opcional: e-mail ou telefone (10 a 13 dígitos depois de tirar pontuação). */
export function normalizarContato(v: unknown): string | null | undefined {
  if (v === undefined || v === null) return null;
  if (typeof v !== "string") return undefined;
  const t = v.trim();
  if (t === "") return null;
  if (t.length > MAX_CONTATO) return undefined;
  if (t.includes("@")) return RE_EMAIL.test(t) ? t.toLowerCase() : undefined;
  if (!/^[\d\s()+.-]+$/.test(t)) return undefined;
  const digitos = t.replace(/\D/g, "");
  return digitos.length >= 10 && digitos.length <= 13 ? `+${digitos.length <= 11 ? `55${digitos}` : digitos}` : undefined;
}

export function validarRelato(corpo: unknown): Validacao {
  if (typeof corpo !== "object" || corpo === null || Array.isArray(corpo)) return { ok: false, motivo: "corpo invalido" };
  const c = corpo as Record<string, unknown>;
  const turno = c.turno === 1 || c.turno === 2 ? c.turno : c.turno === "1" ? 1 : c.turno === "2" ? 2 : null;
  if (turno === null) return { ok: false, motivo: "turno invalido" };
  const uf = typeof c.uf === "string" ? c.uf.toUpperCase() : "";
  if (!(UFS_RELATO as readonly string[]).includes(uf)) return { ok: false, motivo: "UF invalida" };
  const zona = inteiro(c.zona, 1, 9999);
  const secao = inteiro(c.secao, 1, 9999);
  if (zona === null || secao === null) return { ok: false, motivo: "zona ou secao invalida" };
  let local_id: string | null = null;
  if (c.local_id !== undefined && c.local_id !== null && c.local_id !== "") {
    if (typeof c.local_id !== "string" || c.local_id.length > 64 || !RE_LOCAL.test(c.local_id) || !c.local_id.startsWith(`${uf}-`)) {
      return { ok: false, motivo: "local invalido" };
    }
    local_id = c.local_id;
  }
  if (typeof c.tipo !== "string" || !(TIPOS_RELATO as readonly string[]).includes(c.tipo)) return { ok: false, motivo: "tipo invalido" };
  const tipo = c.tipo as TipoRelato;
  if (typeof c.texto !== "string") return { ok: false, motivo: "texto obrigatorio" };
  const texto = c.texto.replace(/\r\n?/g, "\n").trim();
  if (texto === "") return { ok: false, motivo: "texto obrigatorio" };
  if ([...texto].length > MAX_TEXTO) return { ok: false, motivo: `texto acima de ${MAX_TEXTO} caracteres` };
  if (RE_CONTROLE.test(texto)) return { ok: false, motivo: "texto com caracteres de controle" };
  let hora_aproximada: string | null = null;
  if (c.hora_aproximada !== undefined && c.hora_aproximada !== null && c.hora_aproximada !== "") {
    if (typeof c.hora_aproximada !== "string" || !RE_HORA.test(c.hora_aproximada)) return { ok: false, motivo: "hora invalida" };
    hora_aproximada = c.hora_aproximada;
  }
  if (typeof c.presenciou !== "boolean") return { ok: false, motivo: "presenciou invalido" };
  const contato = normalizarContato(c.contato);
  if (contato === undefined) return { ok: false, motivo: "contato invalido" };
  const versao = typeof c.versao === "string" && /^[\w.-]{1,32}$/.test(c.versao) ? c.versao : null;
  return { ok: true, relato: { turno, uf, zona, secao, local_id, tipo, texto, hora_aproximada, presenciou: c.presenciou, contato, versao } };
}

/** Navegador e sistema, sem versão: o bastante para separar robô de gente, pouco para identificar. */
export function resumirUA(ua: string | null): string | null {
  if (ua === null || ua.trim() === "") return null;
  const so = /android/i.test(ua) ? "android" : /iphone|ipad|ipod/i.test(ua) ? "ios" : /windows/i.test(ua) ? "windows" : /mac os x|macintosh/i.test(ua) ? "mac" : /linux|cros/i.test(ua) ? "linux" : "outro";
  const nav = /edg\//i.test(ua) ? "edge" : /samsungbrowser/i.test(ua) ? "samsung" : /opr\/|opera/i.test(ua) ? "opera" : /firefox|fxios/i.test(ua) ? "firefox" : /crios|chrome|chromium/i.test(ua) ? "chrome" : /safari/i.test(ua) ? "safari" : /curl|wget|python|httpie|go-http|node|deno|bun/i.test(ua) ? "script" : "outro";
  return `${so}/${nav}`;
}

/** IP do cliente atrás do proxy do Supabase: primeiro item do x-forwarded-for. */
export function ipCliente(h: { get(nome: string): string | null }): string {
  return h.get("x-forwarded-for")?.split(",")[0]?.trim() || h.get("cf-connecting-ip") || "0.0.0.0";
}

export async function hashIp(sal: string, dia: string, ip: string): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${sal}|relato|${dia}|${ip}`));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Campo-armadilha `website`: escondido para gente, preenchido por robô de formulário. */
export function armadilha(corpo: unknown): "ausente" | "vazia" | "preenchida" {
  if (typeof corpo !== "object" || corpo === null) return "ausente";
  const v = (corpo as Record<string, unknown>).website;
  if (typeof v !== "string") return "ausente";
  return v === "" ? "vazia" : "preenchida";
}
