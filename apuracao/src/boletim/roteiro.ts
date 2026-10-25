// Roteiro do boletim: prompt do 2º turno, chamada ao `claude -p` (Opus, sem sessão), segundo passo
// de enxugar quando passa do teto e guardas finais (sem travessão, sem a palavra proibida, sem markdown).
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { RAIZ_APURACAO } from "./estado.ts";
import type { Modo } from "./estado.ts";

export interface Tamanho {
  min: number;
  max: number;
  teto: number;
  alvo: string;
}

export const TAMANHOS: Readonly<Record<Modo, Tamanho>> = {
  abertura: { min: 150, max: 200, teto: 230, alvo: "170 a 190" },
  pouca: { min: 300, max: 380, teto: 420, alvo: "320 a 360" },
  muita: { min: 500, max: 600, teto: 640, alvo: "520 a 570" },
};

/** Palavras faladas: tudo menos as tags de áudio entre colchetes. */
export function contarPalavras(texto: string): number {
  return texto.replace(/\[[^\]]*\]/g, " ").split(/\s+/).filter(p => /[\p{L}\p{N}]/u.test(p)).length;
}

/** Limpeza determinística: markdown, travessão e frases com a palavra proibida. */
export function guardar(bruto: string): { texto: string; avisos: string[] } {
  const avisos: string[] = [];
  let t = bruto.replace(/\r\n/g, "\n").trim();
  t = t.replace(/^```[a-z]*\n?/i, "").replace(/\n?```$/, "");
  t = t.replace(/^#{1,6}\s+.*$/gm, "").replace(/\*\*/g, "").replace(/^\s*[-*]\s+/gm, "");
  if (/\u2014/.test(t)) {
    avisos.push("travessão removido");
    t = t.replace(/\s*\u2014\s*/g, ", ");
  }
  if (/fraud/i.test(t)) {
    avisos.push("frase com palavra proibida removida");
    t = t
      .split("\n")
      .map(par => par.split(/(?<=[.!?…])\s+/).filter(f => !/fraud/i.test(f)).join(" "))
      .join("\n");
  }
  t = t.replace(/\n{3,}/g, "\n\n").trim();
  return { texto: t, avisos };
}

/**
 * Guia de estilo da voz: `data/boletins/ESTILO.md` (o vivo, editável durante a noite, fora do git) e,
 * na falta dele, a cópia versionada ao lado deste arquivo. `APURACAO_BOLETIM_ESTILO` troca o caminho.
 */
export function caminhoEstilo(): string {
  const env = process.env.APURACAO_BOLETIM_ESTILO;
  if (env) return env;
  const vivo = join(RAIZ_APURACAO, "data/boletins/ESTILO.md");
  return existsSync(vivo) ? vivo : join(import.meta.dir, "ESTILO.md");
}

export function estilo(): string {
  return readFileSync(caminhoEstilo(), "utf8");
}

function estrutura(modo: Modo, tam: Tamanho): string {
  if (modo === "abertura") {
    return `BOLETIM DE ABERTURA (${tam.min} a ${tam.max} palavras faladas, sem contar as tags; mire em ${tam.alvo} e nunca passe de ${tam.max}): a divulgação do TSE ainda não começou ou nenhuma seção foi totalizada. Diga a hora; que é a noite da apuração do segundo turno, Flávio Bolsonaro contra Lula; que a divulgação começa às dezessete horas de Brasília; o tamanho do eleitorado apto e do número de seções (campos do JSON); que há segundo turno para governador em seis estados (Acre, Amazonas, Distrito Federal, Espírito Santo, Rio Grande do Norte e Tocantins); o que a Arvor vai acompanhar a cada dez minutos: placar, regiões, estados mais lentos contra o primeiro turno, abstenção comparada ao primeiro turno, intervalos sem versão nova publicada e a totalização paralela dos boletins de urna, que é a soma dos BUs recebidos, não projeção; feche com a régua do primeiro turno (comparecimento, brancos e nulos finais do JSON). Nenhum número que não esteja no JSON.`;
  }
  const comum = `ORDEM DOS BLOCOS (pule um bloco só se o JSON não tiver dado para ele):
1. Hora e percentual de seções totalizadas.
2. Placar nacional na ordem Flávio Bolsonaro e Lula: percentual dos votos válidos e votos de cada um, quem está à frente, diferença em pontos e em votos. Só diga que alguém foi eleito se o campo eleito_tse for true.
3. Brancos, nulos, comparecimento e abstenção nas seções apuradas, comparados ao resultado final do primeiro turno; a comparação justa da abstenção é a dos municípios já fechados contra os mesmos municípios no primeiro turno (bloco primeiro_turno_como_regua); diga isso quando usar.
4. Desde o boletim anterior: quantas seções e votos válidos chegaram, para quem foi o bloco (percentual do bloco e saldo), se a diferença abriu ou fechou.
5. Regiões: quem está à frente em cada região e por quanto.
6. Estados mais lentos e atraso contra o primeiro turno no mesmo horário; quem deve fechar por último (projeção simples, dizer que é projeção simples). Atraso pede explicação, não indica irregularidade.
7. Os seis governos em segundo turno: Acre, Amazonas, Distrito Federal, Espírito Santo, Rio Grande do Norte e Tocantins (quem está à frente, por quanto, percentual apurado; viradas).
8. Pausas, se houver: descreva como "intervalo sem versão nova publicada", com horário e duração; nunca como acusação.
9. Totalização paralela por QR: BUs recebidos, conferidos iguais ao TSE, divergências. Diga SEMPRE, com estas palavras, que é a soma dos BUs recebidos, não projeção. Se a fonte estiver indisponível ou com zero BU, diga em uma frase.
10. Alertas relevantes desde o anterior (viradas, UF que fechou, abstenção atípica, que pede explicação e não indica irregularidade).
11. Fecho de analista: a leitura do quadro em duas ou três frases, sem prever resultado que o JSON não sustenta.`;
  if (modo === "pouca") {
    return `POUCA MUDANÇA DESDE O ANTERIOR (${tam.min} a ${tam.max} palavras faladas, sem contar as tags; mire em ${tam.alvo} e nunca passe de ${tam.max}). Diga logo no começo que o quadro se mantém e seja econômico: blocos 1, 2, 4 e 11 obrigatórios; dos demais, só o que mudou.\n${comum}`;
  }
  return `MUITA NOVIDADE (${tam.min} a ${tam.max} palavras faladas, sem contar as tags; mire em ${tam.alvo} e nunca passe de ${tam.max}: escolha o que importa, não leia o JSON inteiro).\n${comum}`;
}

export function montarPrompt(resumo: { hora_brt: string; modo: Modo }, dadosJson: string, anterior: string | null): string {
  const tam = TAMANHOS[resumo.modo];
  return `Você é o analista de dados da Arvor Intelligence na noite da apuração do 2º turno da eleição presidencial de 2026 (25 de outubro), falando ao vivo na voz do Leonardo Dias. Escreva o roteiro do boletim das ${resumo.hora_brt} para o ElevenLabs seguindo EXATAMENTE o guia abaixo. Responda só com o roteiro, sem título, sem comentários, sem markdown.

GUIA DE ESTILO (vale na íntegra para tags, números por extenso, ênfase e tom; as regras de Senado, bancadas e governadores eleitos no primeiro turno e o tamanho de 500 a 600 palavras são do 1º turno e NÃO se aplicam aqui: o tamanho é o indicado abaixo):
${estilo()}

${estrutura(resumo.modo, tam)}

REGRAS QUE NÃO SE NEGOCIAM:
- Nunca invente número: só use o que está no JSON. Se um dado não está no JSON, não fale dele.
- Números por extenso na locução ("cinquenta vírgula dois por cento", "um milhão e trezentos mil"); arredonde votos grandes para a centena de milhar ou o milhar, mantendo a ordem de grandeza certa.
- Nunca use a palavra fraude nem sugira irregularidade. Nunca use travessão.
- Pausa é "intervalo sem versão nova publicada". A totalização paralela é "a soma dos BUs recebidos, não projeção". Atraso e abstenção atípica pedem explicação, não indicam irregularidade.
- Tags de áudio em inglês entre colchetes, no máximo uma a cada duas ou três frases.
- Virada, UF que fechou, pausa ou divergência só é novidade quando está em "delta" ou em "alertas_desde_o_anterior"; "viradas_na_noite" e o histórico de pausas são contexto da noite, não fato novo.
- Não repita frases nem aberturas do boletim anterior.

BOLETIM ANTERIOR (para não repetir):
${anterior ?? "(nenhum: este é o primeiro boletim da noite)"}

DADOS (JSON):
${dadosJson}`;
}

export function promptEnxugar(texto: string, modo: Modo): string {
  const tam = TAMANHOS[modo];
  return `Reescreva o roteiro abaixo com ${tam.alvo} palavras faladas (as tags entre colchetes não contam), cortando repetições e detalhes menores, mantendo a ordem dos blocos, as tags de áudio entre colchetes, os números por extenso exatamente como estão, a frase "soma dos BUs recebidos, não projeção" se ela aparecer, e o fecho de analista. Não acrescente nenhum número. Sem travessão. Responda só com o roteiro.

${texto}`;
}

/** Ambiente limpo para o CLI: sem as variáveis da sessão que lançou o gerador (CLAUDE*, ANTHROPIC*). */
export function ambienteLimpo(): Record<string, string> {
  const env: Record<string, string> = {};
  for (const [k, v] of Object.entries(process.env)) {
    if (v === undefined) continue;
    if (/^(CLAUDE|ANTHROPIC|__CF)/.test(k)) continue;
    env[k] = v;
  }
  const local = join(homedir(), ".local/bin");
  if (!(env.PATH ?? "").split(":").includes(local)) env.PATH = `${env.PATH ?? "/usr/bin:/bin"}:${local}:/opt/homebrew/bin`;
  return env;
}

export function binarioClaude(): string {
  return process.env.APURACAO_BOLETIM_CLAUDE ?? Bun.which("claude", { PATH: ambienteLimpo().PATH ?? "" }) ?? join(homedir(), ".local/bin/claude");
}

/** Uma chamada ao `claude -p` com o prompt pelo stdin. Lança em erro, saída vazia ou estouro de tempo. */
export async function chamarClaude(prompt: string, timeoutMs = 300_000): Promise<string> {
  const modelo = process.env.APURACAO_BOLETIM_MODELO ?? "opus";
  const proc = Bun.spawn([binarioClaude(), "-p", "--model", modelo, "--no-session-persistence"], {
    stdin: new Blob([prompt]),
    stdout: "pipe",
    stderr: "pipe",
    env: ambienteLimpo(),
    cwd: RAIZ_APURACAO,
  });
  const timer = setTimeout(() => proc.kill(), timeoutMs);
  try {
    const [out, err, code] = await Promise.all([new Response(proc.stdout).text(), new Response(proc.stderr).text(), proc.exited]);
    if (code !== 0) throw new Error(`claude saiu com ${code}: ${err.trim().split("\n").slice(-2).join(" ")}`.slice(0, 400));
    if (out.trim().length < 40) throw new Error(`claude devolveu saída vazia ou curta: ${out.trim().slice(0, 80)}`);
    return out;
  } finally {
    clearTimeout(timer);
  }
}

export interface ResultadoRoteiro {
  texto: string;
  palavras: number;
  palavras_bruto: number;
  enxugado: boolean;
  avisos: string[];
  ms_roteiro: number;
  ms_enxugar: number;
}

type Chamador = (prompt: string) => Promise<string>;

/** Roteiro completo: geração (uma nova tentativa em falha), enxugar acima do teto e guardas. */
export async function escreverRoteiro(
  prompt: string,
  modo: Modo,
  chamar: Chamador = p => chamarClaude(p),
  aoEtapa: (e: "roteiro" | "enxugar") => void = () => undefined,
): Promise<ResultadoRoteiro> {
  aoEtapa("roteiro");
  const t0 = performance.now();
  let bruto: string;
  try {
    bruto = await chamar(prompt);
  } catch {
    await Bun.sleep(3000);
    bruto = await chamar(prompt);
  }
  const ms_roteiro = performance.now() - t0;
  let { texto, avisos } = guardar(bruto);
  const palavras_bruto = contarPalavras(texto);
  let enxugado = false;
  let ms_enxugar = 0;
  if (palavras_bruto > TAMANHOS[modo].teto) {
    aoEtapa("enxugar");
    const t1 = performance.now();
    try {
      const g = guardar(await chamar(promptEnxugar(texto, modo)));
      if (contarPalavras(g.texto) >= TAMANHOS[modo].min * 0.8) {
        texto = g.texto;
        avisos = [...avisos, ...g.avisos];
        enxugado = true;
      } else avisos.push("enxugar devolveu texto curto demais; mantido o longo");
    } catch (e) {
      avisos.push(`enxugar falhou (${e instanceof Error ? e.message : String(e)}); mantido o longo`);
    }
    ms_enxugar = performance.now() - t1;
  }
  return { texto, palavras: contarPalavras(texto), palavras_bruto, enxugado, avisos, ms_roteiro: Math.round(ms_roteiro), ms_enxugar: Math.round(ms_enxugar) };
}
