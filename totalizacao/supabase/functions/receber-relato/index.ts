// Edge Function dos relatos de seção do Politize-se. GET ?desafio=1 emite um desafio assinado
// (HMAC com SAL_IP, validade de 10 min). POST valida o esquema, o campo-armadilha `website`
// (preenchido: 200 sem gravar), o tempo mínimo de 8 s desde a emissão e a prova de trabalho,
// calcula o hash do IP e registra por registrar_relato(jsonb) (service_role), que aplica o
// limite de 5 relatos por hora por ip_hash e o uso único do desafio numa transação só. Sem
// serviço de terceiros. A resposta nunca devolve o que a pessoa escreveu nem o contato.
import { createClient } from "@supabase/supabase-js";
import { BITS_PROVA, conferirDesafio, emitirDesafio, hashDesafio, TEMPO_MINIMO_MS, VALIDADE_MS } from "../../../src/relato/desafio.ts";
import { armadilha, hashIp, ipCliente, MAX_CORPO_BYTES, resumirUA, validarRelato } from "../../../src/relato/validar.ts";

const ORIGENS = new Set(["https://brasil.arvor.co", "http://localhost:4173", "http://127.0.0.1:4173"]);
const SAL_IP = Deno.env.get("SAL_IP") ?? "";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const SERVICE_ROLE = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";

function cors(origem: string | null): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": origem !== null && ORIGENS.has(origem) ? origem : "https://brasil.arvor.co",
    "Access-Control-Allow-Headers": "authorization, apikey, content-type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Max-Age": "600",
    "Vary": "Origin",
  };
}

function resposta(corpo: Record<string, string | number>, status: number, origem: string | null): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { ...cors(origem), "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

Deno.serve(async (req) => {
  const origem = req.headers.get("origin");
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(origem) });
  if (req.method !== "POST" && req.method !== "GET") return resposta({ status: "rejeitado", motivo: "metodo invalido" }, 405, origem);
  if (origem === null || !ORIGENS.has(origem)) return resposta({ status: "rejeitado", motivo: "origem nao permitida" }, 403, origem);
  if (SAL_IP === "" || SUPABASE_URL === "" || SERVICE_ROLE === "") return resposta({ status: "rejeitado", motivo: "servico nao configurado" }, 503, origem);
  if (req.method === "GET") {
    const desafio = await emitirDesafio(SAL_IP, Date.now());
    return resposta({ status: "desafio", desafio, bits: BITS_PROVA, tempo_minimo_ms: TEMPO_MINIMO_MS, validade_ms: VALIDADE_MS }, 200, origem);
  }

  const bruto = await req.text();
  if (new TextEncoder().encode(bruto).length > MAX_CORPO_BYTES) return resposta({ status: "rejeitado", motivo: "corpo grande demais" }, 413, origem);
  let corpo: unknown;
  try {
    corpo = JSON.parse(bruto);
  } catch {
    return resposta({ status: "rejeitado", motivo: "JSON invalido" }, 400, origem);
  }
  const campo = armadilha(corpo);
  if (campo === "ausente") return resposta({ status: "rejeitado", motivo: "formulario incompleto" }, 400, origem);
  if (campo === "preenchida") return resposta({ status: "aceito" }, 200, origem); // robô: finge aceitar, não grava
  const v = validarRelato(corpo);
  if (!v.ok) return resposta({ status: "rejeitado", motivo: v.motivo }, 400, origem);
  const { desafio, nonce } = corpo as { desafio?: unknown; nonce?: unknown };
  const prova = await conferirDesafio(SAL_IP, desafio, nonce, Date.now());
  if (!prova.ok) return resposta({ status: "rejeitado", motivo: prova.motivo }, 400, origem);

  const ip = ipCliente(req.headers);

  const dia = new Date().toISOString().slice(0, 10);
  const payload = {
    ...v.relato,
    ip_hash: await hashIp(SAL_IP, dia, ip),
    user_agent: resumirUA(req.headers.get("user-agent")),
    origem: "politize-se",
    desafio_hash: await hashDesafio(desafio as string),
  };
  const db = createClient(SUPABASE_URL, SERVICE_ROLE, { auth: { persistSession: false } });
  const { data, error } = await db.rpc("registrar_relato", { p: payload });
  if (error !== null) {
    console.error("registrar_relato", error.code ?? "erro"); // sem a mensagem: o Postgres ecoa a linha recusada
    return resposta({ status: "rejeitado", motivo: "registro recusado" }, 500, origem);
  }
  const r = data as { status?: string };
  if (r.status === "limite") return resposta({ status: "limite", motivo: "muitos relatos deste aparelho; tente em uma hora" }, 429, origem);
  if (r.status === "repetido") return resposta({ status: "rejeitado", motivo: "desafio ja usado; recarregue o formulario" }, 409, origem);
  if (r.status !== "aceito") return resposta({ status: "rejeitado", motivo: "registro recusado" }, 422, origem);
  return resposta({ status: "aceito" }, 200, origem);
});
