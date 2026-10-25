// Gerador do boletim falado: dados → roteiro → áudio, uma geração por vez, estado em arquivos.
import { existsSync, readFileSync, unlinkSync, writeFileSync } from "node:fs";
import { gerarAudio } from "./audio.ts";
import type { ResultadoAudio } from "./audio.ts";
import { coletarDados } from "./dados.ts";
import type { Base, SaidaDados } from "./dados.ts";
import { caminho, gravarJson, hhmmBrt, horaBrt, lerControle, lerJson } from "./estado.ts";
import type { Etapa, Gerador, Indice, ItemIndice, Pedido } from "./estado.ts";
import { idLivre, proximoCiclo } from "./relogio.ts";
import { blocoPrompt, buscarNoticias, normalizar } from "./noticias.ts";
import type { Noticias } from "./noticias.ts";
import { escreverRoteiro, montarPrompt } from "./roteiro.ts";
import type { ResultadoRoteiro } from "./roteiro.ts";

export interface Dependencias {
  dados: (o: { base: string; anterior: Base | null; hora: string; at?: string }) => Promise<SaidaDados>;
  roteiro: (prompt: string, modo: SaidaDados["resumo"]["modo"], aoEtapa: (e: "roteiro" | "enxugar") => void, folga: number) => Promise<ResultadoRoteiro>;
  /** Manchetes da eleição; falha vira lista vazia, nunca derruba o ciclo. */
  noticias: (o: { agoraMs: number; primeiro: boolean; anteriores: ReadonlySet<string> }) => Promise<Noticias>;
  audio: (txt: string) => Promise<ResultadoAudio>;
  agora: () => number;
  log: (o: Record<string, unknown>) => void;
}

export const DEPENDENCIAS_PADRAO: Dependencias = {
  dados: o => coletarDados(o),
  roteiro: (p, m, e, f) => escreverRoteiro(p, m, undefined, e, f),
  noticias: o => buscarNoticias(o),
  audio: txt => gerarAudio(txt),
  agora: () => Date.now(),
  log: o => console.log(JSON.stringify({ t: new Date().toISOString(), ...o })),
};

export interface OpcoesGerador {
  dir: string;
  api: string;
  relogioLigado: boolean;
  intervaloS: number;
  inicioMs: number;
  /** Instante fixo para os dados (ensaio sobre banco antigo). */
  at?: string;
}

export class GeradorBoletim {
  private indice: Indice;
  private gerando: string | null = null;
  private etapa: Etapa | null = null;
  private proximo: number;
  private ultimoErro: string | null = null;
  private readonly iniciadoEm: string;
  private timers: ReturnType<typeof setInterval>[] = [];

  constructor(
    private readonly o: OpcoesGerador,
    private readonly d: Dependencias = DEPENDENCIAS_PADRAO,
  ) {
    this.iniciadoEm = new Date(d.agora()).toISOString();
    const lido = lerJson<Indice>(caminho(o.dir, "indice.json")) ?? { atualizado_em: "", itens: [] };
    // Geração interrompida por queda do processo vira erro, nunca fica "gerando" para sempre.
    for (const i of lido.itens) {
      if (i.estado === "gerando") {
        i.estado = "erro";
        i.etapa = null;
        i.erro = "gerador reiniciado durante a geração";
      }
    }
    this.indice = lido;
    this.proximo = proximoCiclo(o.inicioMs, o.intervaloS, d.agora());
    this.salvarIndice();
    this.batimento();
  }

  get ocupado(): boolean {
    return this.gerando !== null;
  }

  iniciar(): void {
    this.timers.push(setInterval(() => this.tick(), 1000));
    this.timers.push(setInterval(() => this.batimento(), 2000));
    this.d.log({ evento: "gerador_no_ar", dir: this.o.dir, relogio: this.o.relogioLigado, proximo: new Date(this.proximo).toISOString() });
  }

  parar(): void {
    for (const t of this.timers) clearInterval(t);
    this.timers = [];
  }

  /** Um passo do laço: pedido manual e relógio. */
  tick(): void {
    const pedidoPath = caminho(this.o.dir, "pedido.json");
    const pedido = existsSync(pedidoPath) ? lerJson<Pedido>(pedidoPath) : null;
    if (existsSync(pedidoPath)) {
      try {
        unlinkSync(pedidoPath);
      } catch {
        // outro leitor já apagou
      }
    }
    if (pedido && !this.ocupado) {
      void this.gerar("manual", this.d.agora());
      return;
    }
    const agora = this.d.agora();
    if (agora < this.proximo) return;
    const slot = this.proximo;
    this.proximo = proximoCiclo(this.o.inicioMs, this.o.intervaloS, slot + 1000);
    if (!this.o.relogioLigado) return;
    if (this.ocupado) {
      this.d.log({ evento: "ciclo_pulado", slot: horaBrt(slot), motivo: `geração ${this.gerando} em andamento` });
      return;
    }
    void this.gerar("relogio", slot);
  }

  private batimento(): void {
    const g: Gerador = {
      pid: process.pid,
      iniciado_em: this.iniciadoEm,
      batimento_em: new Date(this.d.agora()).toISOString(),
      relogio_ligado: this.o.relogioLigado,
      intervalo_s: this.o.intervaloS,
      inicio_em: new Date(this.o.inicioMs).toISOString(),
      proximo_ciclo_em: this.o.relogioLigado ? new Date(this.proximo).toISOString() : null,
      gerando: this.gerando,
      etapa: this.etapa,
      ultimo_erro: this.ultimoErro,
    };
    try {
      gravarJson(caminho(this.o.dir, "gerador.json"), g);
    } catch (e) {
      this.d.log({ evento: "batimento_falhou", erro: String(e) });
    }
  }

  private salvarIndice(): void {
    this.indice.atualizado_em = new Date(this.d.agora()).toISOString();
    gravarJson(caminho(this.o.dir, "indice.json"), this.indice);
  }

  private atualizar(id: string, p: Partial<ItemIndice>): void {
    const i = this.indice.itens.find(x => x.id === id);
    if (!i) return;
    Object.assign(i, p, { atualizado_em: new Date(this.d.agora()).toISOString() });
    this.salvarIndice();
  }

  private mudarEtapa(id: string, e: Etapa): void {
    this.etapa = e;
    this.atualizar(id, { etapa: e });
    this.batimento();
  }

  /** Último boletim pronto e não descartado: base do delta e texto para não repetir. */
  private anterior(): { base: Base | null; texto: string | null; id: string | null } {
    const c = lerControle(this.o.dir);
    const prontos = this.indice.itens.filter(i => i.estado === "pronto" && !c.descartados[i.id]).sort((a, b) => b.criado_em.localeCompare(a.criado_em));
    const ult = prontos[0];
    if (!ult) return { base: null, texto: null, id: null };
    const dados = lerJson<SaidaDados>(caminho(this.o.dir, `${ult.id}.dados.json`));
    let texto: string | null = null;
    try {
      texto = readFileSync(caminho(this.o.dir, `${ult.id}.txt`), "utf8");
    } catch {
      texto = null;
    }
    return { base: dados?.base ?? null, texto, id: ult.id };
  }

  /** Manchetes do ciclo: o dia inteiro sem boletim anterior, 3 h depois; nunca lança. */
  private async lerNoticias(anteriorId: string | null): Promise<Noticias | null> {
    try {
      const prev = anteriorId ? lerJson<Noticias>(caminho(this.o.dir, `${anteriorId}.noticias.json`)) : null;
      const anteriores = new Set((prev?.itens ?? []).map(m => normalizar(m.titulo)));
      return await this.d.noticias({ agoraMs: this.d.agora(), primeiro: anteriorId === null, anteriores });
    } catch (e) {
      this.d.log({ evento: "noticias_falhou", erro: String(e) });
      return null;
    }
  }

  /** Uma geração completa. Nunca duas ao mesmo tempo; devolve o id ou null se ocupado. */
  async gerar(origem: "relogio" | "manual", instante: number): Promise<string | null> {
    if (this.gerando) return null;
    // Ensaio sobre banco antigo (APURACAO_BOLETIM_AT): a hora do boletim é a do dado.
    if (this.o.at && origem === "manual") instante = Date.parse(this.o.at);
    const id = idLivre(hhmmBrt(instante), x => this.indice.itens.some(i => i.id === x) || existsSync(caminho(this.o.dir, `${x}.meta.json`)));
    this.gerando = id;
    const criado = new Date(this.d.agora()).toISOString();
    const hora = horaBrt(instante);
    this.indice.itens.push({ id, hora, estado: "gerando", etapa: "dados", origem, criado_em: criado, atualizado_em: criado, modo: null, palavras: null, duracao_s: null, resumo: null, erro: null });
    this.salvarIndice();
    this.d.log({ evento: "geracao_inicio", id, origem });
    const t0 = this.d.agora();
    const tempos: Record<string, number> = {};
    const meta: Record<string, unknown> = { id, hora, origem, criado_em: criado };
    try {
      this.mudarEtapa(id, "dados");
      const ant = this.anterior();
      const tD = performance.now();
      const dados = await this.d.dados({ base: this.o.api, anterior: ant.base, hora, ...(this.o.at ? { at: this.o.at } : {}) });
      tempos.dados_ms = Math.round(performance.now() - tD);
      gravarJson(caminho(this.o.dir, `${id}.dados.json`), dados);
      this.atualizar(id, { modo: dados.resumo.modo, resumo: dados.linha });
      const dadosJson = JSON.stringify(dados.resumo, null, 1);
      const tN = performance.now();
      const noticias = await this.lerNoticias(ant.id);
      tempos.noticias_ms = Math.round(performance.now() - tN);
      if (noticias) gravarJson(caminho(this.o.dir, `${id}.noticias.json`), noticias);
      const bloco = blocoPrompt(noticias);
      const prompt = montarPrompt(dados.resumo, dadosJson, ant.texto, bloco);
      writeFileSync(caminho(this.o.dir, `${id}.prompt.txt`), prompt);
      const folga = bloco ? (dados.resumo.modo === "abertura" ? 80 : 120) : 0;
      const rot = await this.d.roteiro(prompt, dados.resumo.modo, e => this.mudarEtapa(id, e), folga);
      tempos.roteiro_ms = rot.ms_roteiro;
      tempos.enxugar_ms = rot.ms_enxugar;
      const txt = caminho(this.o.dir, `${id}.txt`);
      writeFileSync(txt, `${rot.texto}\n`);
      this.atualizar(id, { palavras: rot.palavras });
      this.mudarEtapa(id, "audio");
      const aud = await this.d.audio(txt);
      tempos.audio_ms = aud.ms;
      writeFileSync(caminho(this.o.dir, `${id}.tts.log`), `${aud.log}\n`);
      tempos.total_ms = this.d.agora() - t0;
      Object.assign(meta, {
        modo: dados.resumo.modo,
        motivos_modo: dados.resumo.motivos_modo,
        anterior: ant.id,
        palavras: rot.palavras,
        palavras_bruto: rot.palavras_bruto,
        enxugado: rot.enxugado,
        avisos: rot.avisos,
        duracao_s: aud.duracao_s,
        resumo: dados.linha,
        noticias: noticias ? { itens: noticias.itens.length, novas: noticias.itens.filter(n => n.nova).length, feeds: noticias.feeds.map(f => `${f.nome}: ${f.erro ?? f.itens}`) } : null,
        tempos,
        modelo_roteiro: process.env.APURACAO_BOLETIM_MODELO ?? "opus",
        modelo_voz: process.env.BOLETIM_MODEL ?? "eleven_v4",
        pronto_em: new Date(this.d.agora()).toISOString(),
        erro: null,
      });
      gravarJson(caminho(this.o.dir, `${id}.meta.json`), meta);
      this.etapa = null;
      this.atualizar(id, { estado: "pronto", etapa: null, duracao_s: aud.duracao_s, palavras: rot.palavras });
      this.ultimoErro = null;
      this.d.log({ evento: "geracao_pronta", id, palavras: rot.palavras, duracao_s: aud.duracao_s, tempos });
      return id;
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      this.ultimoErro = `${id}: ${msg}`;
      tempos.total_ms = this.d.agora() - t0;
      gravarJson(caminho(this.o.dir, `${id}.meta.json`), { ...meta, erro: msg, tempos, etapa: this.etapa });
      this.atualizar(id, { estado: "erro", etapa: null, erro: msg.slice(0, 300) });
      this.d.log({ evento: "geracao_erro", id, etapa: this.etapa, erro: msg });
      return id;
    } finally {
      this.gerando = null;
      this.etapa = null;
      this.batimento();
    }
  }
}
