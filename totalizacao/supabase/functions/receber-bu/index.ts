// Edge Function de ingestao da totalizacao paralela: recebe os textos dos QR do BU, verifica
// (cadeia SHA-512, assinatura da urna, cadeia de certificacao do TSE, somas), aplica limite de
// taxa e Turnstile, e registra pela funcao registrar_envio (service_role). O navegador nunca
// escreve nas tabelas: esta e a unica porta de escrita.
import { createClient } from "@supabase/supabase-js";
import { lerBoletim, PERFIL_2T_2026 } from "../../../src/index.ts";
import { montarCertificado } from "../../../src/qrbu/certificado.ts";

const VERSAO_MOTOR = "receber-bu/2026-10-15.1";
const ORIGENS = new Set(["https://brasil.arvor.co", "http://localhost:4173", "http://127.0.0.1:4173", "http://localhost:8000", "http://127.0.0.1:8000"]);
const MAX_QR = 12;
const MAX_CHARS = 1200;
const LIMITE_POR_MINUTO = 120;

const MODO = Deno.env.get("MODO") ?? "oficial"; // "teste" aceita FASE S/T e qualquer pleito
const SAL_IP = Deno.env.get("SAL_IP") ?? "";
const TURNSTILE_SECRET = Deno.env.get("TURNSTILE_SECRET") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

const ESPERADO = { fase: "O", turno: 2, pleito: 3221, proc: 1219, dtpl: "20261025" };

type Corpo = { qr?: unknown; aparelho?: unknown; turnstile?: unknown; versao?: unknown };

function cors(origem: string | null): Record<string, string> {
  const permitida = origem !== null && ORIGENS.has(origem) ? origem : "https://brasil.arvor.co";
  return {
    "Access-Control-Allow-Origin": permitida,
    "Access-Control-Allow-Headers": "authorization, apikey, content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Vary": "Origin",
  };
}

function resposta(corpo: unknown, status: number, origem: string | null): Response {
  return new Response(JSON.stringify(corpo), { status, headers: { ...cors(origem), "Content-Type": "application/json; charset=utf-8" } });
}

async function sha256Hex(texto: string): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, "0")).join("");
}

async function turnstileOk(token: string, ip: string): Promise<boolean> {
  if (TURNSTILE_SECRET === "") return true;
  const form = new URLSearchParams({ secret: TURNSTILE_SECRET, response: token, remoteip: ip });
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: form });
  const j = (await r.json()) as { success?: boolean; hostname?: string };
  return j.success === true && (j.hostname === undefined || j.hostname === "brasil.arvor.co" || j.hostname.startsWith("localhost"));
}

Deno.serve(async (req) => {
  const origem = req.headers.get("origin");
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origem) });
  if (req.method !== "POST") return resposta({ status: "rejeitado", motivo: "metodo invalido" }, 405, origem);

  let corpo: Corpo;
  try {
    corpo = (await req.json()) as Corpo;
  } catch {
    return resposta({ status: "rejeitado", motivo: "JSON invalido" }, 400, origem);
  }
  const qr = corpo.qr;
  if (!Array.isArray(qr) || qr.length === 0 || qr.length > MAX_QR || !qr.every((t) => typeof t === "string" && t.length <= MAX_CHARS && /^[A-Z0-9 $%*+\-./:]+$/.test(t))) {
    return resposta({ status: "rejeitado", motivo: "lista de QR invalida" }, 400, origem);
  }
  const textos = qr as string[];
  const aparelho = typeof corpo.aparelho === "string" ? corpo.aparelho.slice(0, 64) : "";
  const versaoApp = typeof corpo.versao === "string" ? corpo.versao.slice(0, 32) : "";

  const ip = req.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? req.headers.get("cf-connecting-ip") ?? "0.0.0.0";
  const dia = new Date().toISOString().slice(0, 10);
  const ipHash = await sha256Hex(`${SAL_IP}|${dia}|${ip}`);
  const aparelhoHash = aparelho === "" ? null : await sha256Hex(`${SAL_IP}|${aparelho}`);

  const db = createClient(SUPABASE_URL, SERVICE_ROLE, { auth: { persistSession: false } });
  const { data: recentes, error: erroLimite } = await db.rpc("envios_recentes", { p_ip_hash: ipHash, p_segundos: 60 });
  if (erroLimite !== null) return resposta({ status: "rejeitado", motivo: `banco indisponivel: ${erroLimite.message}` }, 503, origem);
  if ((recentes as number) >= LIMITE_POR_MINUTO) return resposta({ status: "rejeitado", motivo: "muitos envios; tente em um minuto" }, 429, origem);

  if (TURNSTILE_SECRET !== "" && !(typeof corpo.turnstile === "string" && (await turnstileOk(corpo.turnstile, ip)))) {
    return resposta({ status: "rejeitado", motivo: "verificacao anti-robo falhou" }, 403, origem);
  }

  const base = { aparelho_hash: aparelhoHash, ip_hash: ipHash, qr_textos: textos, versao_motor: `${VERSAO_MOTOR} app=${versaoApp}` };
  const rejeitar = async (motivo: string, status = 422) => {
    await db.rpc("registrar_envio", { p: { ...base, status: "rejeitado", motivo } });
    return resposta({ status: "rejeitado", motivo, bu: null }, status, origem);
  };

  // Em modo de teste a fase esperada e a do proprio boletim (exemplos oficiais sao FASE S).
  const previa = MODO === "teste" ? lerBoletim(textos) : null;
  const faseTeste = previa?.boletim?.cabecalho.FASE;
  const opcoes = MODO === "teste" ? { faseEsperada: faseTeste === "S" || faseTeste === "T" || faseTeste === "O" ? faseTeste : "O" } : PERFIL_2T_2026;
  const leitura = lerBoletim(textos, opcoes);
  if (leitura.boletim === null || !leitura.autentico || !leitura.valido) {
    const motivo = leitura.problemas.length > 0 ? leitura.problemas.map((q) => q.mensagem).join("; ") : "boletim nao autentico";
    return rejeitar(motivo);
  }
  const bu = leitura.boletim;
  const h = bu.cabecalho;
  const cert = leitura.certificado;
  if (cert === null || leitura.assinatura === null || leitura.assinatura.algoritmo === null || leitura.ultimoHash === null || leitura.assinaturaHex === null || leitura.conteudo === null) {
    return rejeitar("leitura incompleta");
  }
  if (h.UNFE === undefined || h.MUNI === undefined || h.ZONA === undefined || h.SECA === undefined || h.ORIG === undefined || h.TURN === undefined || h.PLEI === undefined || h.PROC === undefined || h.FASE === undefined || h.DTPL === undefined || h.IDUE === undefined) {
    return rejeitar("cabecalho do boletim incompleto");
  }
  const certDerHex = Array.from(montarCertificado(textos.filter((t) => t.startsWith("QRCE:"))).der, (b) => b.toString(16).padStart(2, "0")).join("");

  const cargos = bu.eleicoes.flatMap((e) =>
    e.cargos.map((c) => ({
      idel: e.IDEL,
      cargo: c.CARG,
      tipo: c.TIPO ?? 0,
      apta: c.APTA ?? 0,
      nomi: c.NOMI ?? 0,
      legc: c.LEGC ?? 0,
      bran: c.BRAN ?? 0,
      nulo: c.NULO ?? 0,
      totc: c.TOTC ?? 0,
      votos: [
        ...c.votos.map((v) => ({ partido: null, candidato: String(v.numero), votos: v.votos })),
        ...c.partidos.flatMap((p) => [
          ...p.votos.map((v) => ({ partido: p.PART, candidato: String(v.numero), votos: v.votos })),
          ...((p.LEGP ?? 0) > 0 ? [{ partido: p.PART, candidato: `LEGP${p.PART}`, votos: p.LEGP ?? 0 }] : []),
        ]),
      ],
    })),
  );
  const data8 = (d: string) => `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`;
  const hora6 = (t: string) => `${t.slice(0, 2)}:${t.slice(2, 4)}:${t.slice(4, 6)}`;
  const payload = {
    ...base,
    status: "aceito",
    bu: {
      uf: h.UNFE.toLowerCase(), muni: h.MUNI, zona: h.ZONA, secao: h.SECA, agre: h.AGRE === undefined ? null : h.AGRE.join("."),
      orig: h.ORIG, turno: h.TURN, pleito: h.PLEI, proc: h.PROC, fase: h.FASE, dtpl: data8(h.DTPL),
      idue: h.IDUE, mdue: cert.modelo, vers: h.VERS ?? null, aptos: h.APTO ?? null, comparecimento: h.COMP ?? null,
      faltosos: h.FALT ?? null, dtfc: h.DTFC === undefined ? null : data8(h.DTFC), hrfc: h.HRFC === undefined ? null : hora6(h.HRFC),
      hash_final: leitura.ultimoHash, assi: leitura.assinaturaHex, algoritmo: leitura.assinatura.algoritmo,
      cert_hex: certDerHex, cert_subject: cert.titularCN, cert_issuer: cert.emissorCN,
      conteudo: leitura.conteudo, cargos,
    },
  };
  const { data, error } = await db.rpc("registrar_envio", { p: payload });
  if (error !== null) return rejeitar(`registro recusado: ${error.message}`, 422);
  const r = data as { status: string; motivo: string | null; bu: unknown };
  return resposta({ status: r.status, motivo: r.motivo, bu: r.bu }, 200, origem);
});
