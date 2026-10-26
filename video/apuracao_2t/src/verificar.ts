// Portão de duração de "A noite do 2º turno": de 570 a 660 s (9:30 a 11:00). Abaixo é
// CURTO, acima é LONGO.
// Uso: npm run verificar   (node --experimental-strip-types src/verificar.ts)
// Com voz gerada, mede a duração real (voz + respiros + cauda) e sai com código 1 fora do portão.
// Sem voz, estima pelo roteiro a 145 palavras por minuto e só informa.
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { FPS, PORTAO, diferencasDeOrdem, montarCenas, mmss, trechosDosCapitulos, veredito, type CenaLinha } from "./linha.ts";
import { CAPITULOS_BASE, ORDEM } from "./ordem.ts";
import type { Voz } from "./tipos.ts";

const AQUI = path.dirname(fileURLToPath(import.meta.url));
const VOZ_JSON = path.join(AQUI, "dados", "voz.json");
const ROTEIRO = path.join(AQUI, "..", "roteiro", "roteiro.md");
const PALAVRAS_POR_MINUTO = 145;

const escrever = (linha = ""): void => {
  process.stdout.write(`${linha}\n`);
};

const virgula = (n: number, casas = 1): string => n.toFixed(casas).replace(".", ",");

/** Blocos `## id` do roteiro com o número de palavras narradas (sem comentários nem tags). */
const palavrasDoRoteiro = (texto: string): Map<string, number> => {
  const saida = new Map<string, number>();
  let atual: string | null = null;
  let corpo: string[] = [];
  const fechar = (): void => {
    if (atual) {
      const limpo = corpo
        .join("\n")
        .replace(/<!--[\s\S]*?-->/g, " ")
        .replace(/\[[a-z ]+\]/g, " ");
      saida.set(atual, limpo.split(/\s+/).filter((p) => /[\p{L}\p{N}]/u.test(p)).length);
    }
  };
  for (const linha of texto.split("\n")) {
    if (linha.startsWith("## ")) {
      fechar();
      atual = linha.slice(3).trim();
      corpo = [];
    } else if (atual !== null) {
      corpo.push(linha);
    }
  }
  fechar();
  return saida;
};

const relatorio = (cenas: CenaLinha[], titulo: string): number => {
  const total = cenas.reduce((soma, c) => soma + c.frames, 0) / FPS;
  escrever(titulo);
  escrever(`Duração total: ${mmss(total)} (${virgula(total)} s), ${cenas.length} cenas`);
  escrever();
  escrever("Capítulos:");
  for (const trecho of trechosDosCapitulos(cenas)) {
    const base = CAPITULOS_BASE.find((c) => c.id === trecho.id);
    const nome = `${String(base?.numero ?? 0).padStart(2, "0")} ${base?.titulo ?? trecho.id}`;
    const de = trecho.inicio / FPS;
    const ate = (trecho.inicio + trecho.frames) / FPS;
    escrever(`  ${nome.padEnd(34)} ${mmss(de).padStart(5)} a ${mmss(ate).padStart(5)}   (${mmss(ate - de)})`);
  }
  escrever();
  return total;
};

const principal = (): number => {
  const voz = JSON.parse(readFileSync(VOZ_JSON, "utf8")) as Voz;
  const faixa = `[${PORTAO.minimo}, ${PORTAO.maximo}] s (${mmss(PORTAO.minimo)} a ${mmss(PORTAO.maximo)})`;

  if (voz.cenas.length > 0) {
    let cenas: CenaLinha[];
    try {
      cenas = montarCenas(voz, ORDEM);
    } catch (erro) {
      escrever(`ERRO: ${(erro as Error).message}`);
      return 1;
    }
    const total = relatorio(cenas, `A noite do 2º turno, voz ${voz.modelo}`);
    const v = veredito(total);
    escrever(`Portão ${faixa}: ${v}`);
    return v === "OK" ? 0 : 1;
  }

  if (!existsSync(ROTEIRO)) {
    escrever("Sem voz (src/dados/voz.json vazio) e sem roteiro (roteiro/roteiro.md): nada a medir ainda.");
    escrever("Portão não aplicado.");
    return 0;
  }
  const contagem = palavrasDoRoteiro(readFileSync(ROTEIRO, "utf8"));
  const palavras = [...contagem.values()].reduce((a, b) => a + b, 0);
  const estimada: Voz = {
    modelo: "estimativa",
    cenas: ORDEM.map((c) => ({
      id: c.id,
      arquivo: "",
      segundos: ((contagem.get(c.id) ?? 0) / PALAVRAS_POR_MINUTO) * 60,
      texto: "",
      palavras: [],
    })),
  };
  const total = relatorio(
    montarCenas(estimada, ORDEM),
    `A noite do 2º turno, ESTIMATIVA pelo roteiro: ${palavras} palavras narradas a ${PALAVRAS_POR_MINUTO} por minuto`,
  );
  for (const erro of diferencasDeOrdem([...contagem.keys()], ORDEM)) {
    escrever(`Roteiro: ${erro}`);
  }
  escrever(`Portão ${faixa}: ${veredito(total)} (estimativa; o portão vale para a voz gerada)`);
  return 0;
};

process.exitCode = principal();
