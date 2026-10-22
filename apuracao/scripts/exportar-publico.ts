// Uso: bun run scripts/exportar-publico.ts [--saida ../docs/assets/apuracao_2t] [--base http://127.0.0.1:4180]
//
// Exporta o estado público da apuração do 2º turno (25/10/2026) para o GitHub Pages.
// Chama a API local do telão (porta em APURACAO_PORT, padrão 4180), grava um JSON compacto por
// rota em docs/assets/apuracao_2t/ e um manifest.json com gerado_em, turno, sha256 e bytes de
// cada arquivo e a lista de rotas pendentes (resposta {pendente:true}, erro ou prazo estourado).
//
// Rota com erro não derruba a exportação: o arquivo anterior fica como está e a rota entra em
// `pendentes`. Sem arquivo anterior, grava {"pendente":true}. Nunca grava identificador pessoal:
// campos com nome de CPF, e-mail, telefone ou título de eleitor são removidos antes de gravar.
// Código de saída: 0 se gravou o manifesto, 1 se nem o manifesto pôde ser gravado.
import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PADRAO_SAIDA = join(RAIZ, "..", "docs", "assets", "apuracao_2t");
const PRAZO_MS = 20_000;
const ALVO_BYTES = 2 * 1024 * 1024;
const PROIBIDOS = /^(cpf|email|e_mail|telefone|celular|titulo|titulo_eleitor|nr_titulo|nome_eleitor|ip|ip_hash)$/i;

interface Rota {
  arquivo: string;
  caminho: string;
}

const ROTAS: readonly Rota[] = [
  { arquivo: "estado", caminho: "/api/estado" },
  { arquivo: "config", caminho: "/api/config" },
  { arquivo: "regioes", caminho: "/api/2t/regioes" },
  { arquivo: "ufs", caminho: "/api/2t/ufs" },
  { arquivo: "abstencao", caminho: "/api/2t/abstencao" },
  { arquivo: "estaduais", caminho: "/api/2t/estaduais" },
  { arquivo: "evolucao", caminho: "/api/2t/evolucao?nivel=regiao&passo=120" },
  { arquivo: "pausas", caminho: "/api/2t/pausas" },
  { arquivo: "secoes", caminho: "/api/2t/secoes" },
  { arquivo: "paralela", caminho: "/api/2t/paralela" },
  { arquivo: "anomalias", caminho: "/api/anomalias?limit=60" },
  { arquivo: "resultado", caminho: "/api/resultado?ele=6258&cargo=1&abr=br" },
  { arquivo: "mapa", caminho: "/api/mapa?ele=6258&cargo=1&nivel=uf" },
];

function argumento(nome: string, padrao: string): string {
  const i = process.argv.indexOf(nome);
  const valor = i >= 0 ? process.argv[i + 1] : undefined;
  return valor ?? padrao;
}

/** Remove, em qualquer nível, chaves que identificariam uma pessoa. */
function limpar(valor: unknown): unknown {
  if (Array.isArray(valor)) return valor.map(limpar);
  if (valor !== null && typeof valor === "object") {
    const saida: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(valor as Record<string, unknown>)) {
      if (!PROIBIDOS.test(k)) saida[k] = limpar(v);
    }
    return saida;
  }
  return valor;
}

function ehPendente(corpo: unknown): boolean {
  return typeof corpo === "object" && corpo !== null && (corpo as { pendente?: unknown }).pendente === true;
}

async function buscar(base: string, caminho: string): Promise<unknown> {
  const resp = await fetch(base + caminho, {
    headers: { accept: "application/json" },
    signal: AbortSignal.timeout(PRAZO_MS),
  });
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return (await resp.json()) as unknown;
}

function gravarAtomico(destino: string, texto: string): void {
  const tmp = `${destino}.tmp`;
  writeFileSync(tmp, texto);
  renameSync(tmp, destino);
}

function sha256(texto: string): string {
  return createHash("sha256").update(texto).digest("hex");
}

async function main(): Promise<void> {
  const saida = resolve(argumento("--saida", PADRAO_SAIDA));
  const porta = process.env["APURACAO_PORT"] ?? "4180";
  const base = argumento("--base", `http://127.0.0.1:${porta}`);
  mkdirSync(saida, { recursive: true });

  const pendentes: string[] = [];
  const erros: Record<string, string> = {};
  const arquivos: Record<string, { sha256: string; bytes: number }> = {};
  let turno: number | null = null;

  for (const rota of ROTAS) {
    const destino = join(saida, `${rota.arquivo}.json`);
    let texto: string | null = null;
    try {
      const corpo = limpar(await buscar(base, rota.caminho));
      if (ehPendente(corpo)) {
        pendentes.push(rota.arquivo);
      } else {
        let final = corpo;
        if (rota.arquivo === "config" && typeof corpo === "object" && corpo !== null) {
          // a página só usa turno, eleições e UFs; o cadastro de 5.570 municípios fica de fora
          const { municipios: _fora, ...resto } = corpo as Record<string, unknown>;
          final = resto;
          const t = resto["turno"];
          if (typeof t === "number") turno = t;
        }
        texto = JSON.stringify(final);
      }
    } catch (e) {
      pendentes.push(rota.arquivo);
      erros[rota.arquivo] = e instanceof Error ? e.message : String(e);
    }
    if (texto !== null) {
      gravarAtomico(destino, texto);
    } else if (existsSync(destino)) {
      texto = readFileSync(destino, "utf8");
    } else {
      texto = JSON.stringify({ pendente: true });
      gravarAtomico(destino, texto);
    }
    arquivos[rota.arquivo] = { sha256: sha256(texto), bytes: Buffer.byteLength(texto) };
  }

  const total = Object.values(arquivos).reduce((s, a) => s + a.bytes, 0);
  const manifesto = {
    gerado_em: new Date().toISOString(),
    turno,
    fonte: base.replace(/^https?:\/\//, "") === `127.0.0.1:${porta}` ? "local" : "outra",
    total_bytes: total,
    acima_do_alvo: total > ALVO_BYTES,
    pendentes,
    erros,
    arquivos,
  };
  gravarAtomico(join(saida, "manifest.json"), JSON.stringify(manifesto));
  console.log(
    `exportado: ${Object.keys(arquivos).length} arquivos, ${(total / 1024).toFixed(0)} KiB, ` +
      `pendentes: ${pendentes.length ? pendentes.join(",") : "nenhum"}`,
  );
}

main().catch((e: unknown) => {
  console.error("falha ao exportar:", e);
  process.exit(1);
});
