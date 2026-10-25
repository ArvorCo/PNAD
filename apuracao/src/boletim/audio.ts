// Áudio do boletim: chama o scripts/boletim-tts.py do 1º turno (ElevenLabs eleven_v4, por parágrafo
// com previous_text/next_text, estabilidade 0,4, estilo 0,3, concat pelo ffmpeg), que já leu 30
// boletins na noite de 04/10 sem falha. Porte para TypeScript ficou para depois: no dia da eleição,
// o caminho provado tem menos risco. A duração vem do ffprobe.
import { existsSync, statSync } from "node:fs";
import { join } from "node:path";
import { RAIZ_APURACAO } from "./estado.ts";
import { ambienteLimpo } from "./roteiro.ts";

async function rodar(cmd: string[], timeoutMs: number): Promise<{ code: number; out: string; err: string }> {
  const proc = Bun.spawn(cmd, { stdout: "pipe", stderr: "pipe", env: ambienteLimpo(), cwd: RAIZ_APURACAO });
  const timer = setTimeout(() => proc.kill(), timeoutMs);
  try {
    const [out, err, code] = await Promise.all([new Response(proc.stdout).text(), new Response(proc.stderr).text(), proc.exited]);
    return { code, out, err };
  } finally {
    clearTimeout(timer);
  }
}

export async function duracaoMp3(mp3: string): Promise<number | null> {
  const r = await rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3], 20_000);
  const d = Number.parseFloat(r.out.trim());
  return r.code === 0 && Number.isFinite(d) ? Math.round(d * 10) / 10 : null;
}

export interface ResultadoAudio {
  mp3: string;
  duracao_s: number | null;
  log: string;
  ms: number;
}

/** Gera HHMM.mp3 ao lado de HHMM.txt; uma nova tentativa em falha. */
export async function gerarAudio(txt: string, timeoutMs = 300_000): Promise<ResultadoAudio> {
  const mp3 = txt.replace(/\.txt$/, ".mp3");
  const script = process.env.APURACAO_BOLETIM_TTS ?? join(RAIZ_APURACAO, "scripts/boletim-tts.py");
  const t0 = performance.now();
  let ultimo = "";
  for (let tentativa = 1; tentativa <= 2; tentativa += 1) {
    const r = await rodar(["python3", script, txt], timeoutMs);
    ultimo = `${r.out}\n${r.err}`.trim();
    if (r.code === 0 && existsSync(mp3) && statSync(mp3).size > 1000) {
      return { mp3, duracao_s: await duracaoMp3(mp3), log: ultimo, ms: Math.round(performance.now() - t0) };
    }
    if (tentativa === 1) await Bun.sleep(3000);
  }
  throw new Error(`áudio falhou: ${ultimo.split("\n").slice(-2).join(" ").slice(0, 400)}`);
}
