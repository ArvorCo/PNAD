// Detector de pausas do 2º turno sobre os arquivos -u de presidente (br e UF).
// Pausa = intervalo sem versão nova publicada (gerado_em) com st < ts por mais que o limiar,
// enquanto outro nível avança; não é acusação. "Avança" = em toda a janela do limiar até agora
// as UFs estavam publicando (idade mediana da última versão até metade do limiar do nível, no
// mínimo 3 min) e a soma delas andou. Sem isso, cada travamento geral do 1º turno (18:00, 19:17, 19:32) virava
// dezenas de pausas de UF: as UFs voltam com segundos ou minutos de diferença. A detecção ainda
// espera uma folga (padrão 1 min) além do limiar, porque o CDN entrega a versão nova com atraso
// de até dois minutos (replay do 1º turno). Três níveis:
//   nacional: arquivo br parado enquanto as UFs publicam e andam;
//   uf: arquivo da UF parado enquanto as demais publicam e andam;
//   geral: nenhum arquivo (br nem UF) com versão nova e seções pendentes (o caso de 19:32 a
//          20:02 no 1º turno, quando a regra "outro nível avança" não dispara por definição).
// Puro: recebe versões e o relógio, devolve itens de lote (eventos e linhas de `pausa`).
import type { Database } from "bun:sqlite";
import type { EventoNovo, ItemLote, LinhaPausa } from "../db/escrita.ts";
import { isoDe } from "./relogio.ts";

export const ROTULO_PAUSA = "intervalo sem versão nova publicada, não acusação";

export interface OpcoesPausas {
  /** eleição federal (6258 no 2º turno) */
  ele: number;
  limiarNacionalMin: number;
  limiarUfMin: number;
  /** pausa nacional ou geral a partir deste tamanho vira error */
  longaMin: number;
  /** espera além do limiar antes de abrir a pausa (atraso de entrega do CDN) */
  folgaMin: number;
  /** soma das UFs à frente do nacional em mais que esta fração de ts (%) ... */
  adiantePct: number;
  /** ... por mais que estes minutos */
  adianteMin: number;
}

export const PAUSAS_PADRAO: Omit<OpcoesPausas, "ele"> = {
  limiarNacionalMin: 5,
  limiarUfMin: 10,
  folgaMin: 1,
  longaMin: 15,
  adiantePct: 2,
  adianteMin: 5,
};

export interface Versao {
  geradoMs: number;
  st: number;
  ts: number;
}

/** null = arquivo nacional; sigla minúscula = UF. */
export type Frescor = (uf: string | null) => boolean;

type Nivel = LinhaPausa["nivel"];

interface Aberta {
  nivel: Nivel;
  uf: string | null;
  de: string;
  deMs: number;
  stAntes: number;
  detectadoEm: string;
  longa: boolean;
}

/** Idade mediana máxima das UFs para o país contar como publicando (cadência típica do 1º turno: 3 min). */
const PUBLICANDO_MIN_MS = 3 * 60_000;
const NAC = "";
const GERAL = "*";
const min1 = (ms: number): number => Math.round(ms / 6000) / 10;

export class DetectorPausas {
  /** histórico de versões por arquivo: "" nacional, sigla da UF */
  private readonly hist = new Map<string, Versao[]>();
  private readonly abertas = new Map<string, Aberta>();
  private adianteDesde: number | null = null;
  private adianteEmitido = false;

  constructor(private readonly o: OpcoesPausas) {}

  /** UFs com pelo menos uma versão vista. */
  get ufs(): string[] {
    return [...this.hist.keys()].filter((k) => k !== NAC).sort();
  }

  private lista(chave: string): Versao[] {
    let l = this.hist.get(chave);
    if (!l) {
      l = [];
      this.hist.set(chave, l);
    }
    return l;
  }

  /** st da última versão gerada até `ms` (0 sem versão). */
  stEm(uf: string, ms: number): number {
    const l = this.hist.get(uf);
    if (!l) return 0;
    for (let i = l.length - 1; i >= 0; i--) {
      const v = l[i] as Versao;
      if (v.geradoMs <= ms) return v.st;
    }
    return 0;
  }

  /** Soma do st das UFs (sem `exceto`) no instante `ms`. */
  somaUfs(ms: number, exceto: string | null = null): number {
    let s = 0;
    for (const uf of this.hist.keys()) if (uf !== NAC && uf !== exceto) s += this.stEm(uf, ms);
    return s;
  }

  private somaTsUfs(): number {
    let s = 0;
    for (const [uf, l] of this.hist) if (uf !== NAC) s += l.at(-1)?.ts ?? 0;
    return s;
  }

  /** Geração da última versão do arquivo até `ms` (null sem versão). */
  private geradoAte(l: readonly Versao[], ms: number): number | null {
    for (let i = l.length - 1; i >= 0; i--) {
      const v = l[i] as Versao;
      if (v.geradoMs <= ms) return v.geradoMs;
    }
    return null;
  }

  /** Idade mediana (ms), no instante `t`, da última versão das UFs (sem `exceto`); null sem UF. */
  private idadeMedianaUfs(t: number, exceto: string | null = null): number | null {
    const idades: number[] = [];
    for (const [uf, l] of this.hist) {
      if (uf === NAC || uf === exceto) continue;
      const g = this.geradoAte(l, t);
      if (g !== null) idades.push(t - g);
    }
    if (idades.length === 0) return null;
    idades.sort((a, b) => a - b);
    return idades[Math.floor((idades.length - 1) / 2)] ?? null;
  }

  /**
   * Arquivo parado desde `geradoMs` por mais que `limiarMin` dentro do trecho em que o país
   * publica, e as outras UFs somaram seções na janela do limiar. Devolve as somas ou null.
   */
  private paradoComPaisAndando(agora: number, geradoMs: number, limiarMin: number, exceto: string | null): { agora: number; antes: number } | null {
    const limiar = limiarMin * 60000;
    if (agora - geradoMs <= limiar + this.o.folgaMin * 60000) return null;
    for (let t = agora - limiar; t <= agora; t += 30_000) {
      const m = this.idadeMedianaUfs(t, exceto);
      if (m === null || m > Math.max(limiar / 2, PUBLICANDO_MIN_MS)) return null;
    }
    const somaAgora = this.somaUfs(Number.POSITIVE_INFINITY, exceto);
    const somaAntes = this.somaUfs(agora - limiar, exceto);
    return somaAgora > somaAntes ? { agora: somaAgora, antes: somaAntes } : null;
  }

  private ultimaGeracaoMs(): number | null {
    let m: number | null = null;
    for (const l of this.hist.values()) {
      const g = l.at(-1)?.geradoMs;
      if (g !== undefined && (m === null || g > m)) m = g;
    }
    return m;
  }

  private evento(nivel: Nivel, uf: string | null, em: string, tipo: string, severidade: "info" | "warn" | "error", detalhe: unknown): ItemLote {
    const row: EventoNovo = {
      em, tipo, severidade, eleicao_cd: this.o.ele, cargo_cd: 1, nivel: nivel === "uf" ? "uf" : "br", uf: nivel === "uf" ? uf : null, detalhe,
    };
    return { k: "evento", row };
  }

  private fechar(chave: string, a: Aberta, ateMs: number, stDepois: number, em: string): ItemLote[] {
    this.abertas.delete(chave);
    const ate = isoDe(ateMs);
    const minutos = min1(ateMs - a.deMs);
    const row: LinhaPausa = {
      nivel: a.nivel, uf: a.uf, de: a.de, ate, minutos, st_antes: a.stAntes, st_depois: stDepois, detectado_em: a.detectadoEm,
    };
    const tipo = `pausa_${a.nivel}_fim`;
    return [
      { k: "pausa", row },
      this.evento(a.nivel, a.uf, em, tipo, "info", { de: a.de, ate, minutos, st_antes: a.stAntes, st_depois: stDepois, rotulo: ROTULO_PAUSA }),
    ];
  }

  /**
   * Versão nova de um arquivo (uf null = nacional). Fecha a pausa aberta dele e a geral.
   * Versões com geração igual ou anterior à última conhecida são ignoradas. Versão que chega
   * já velha (gerada antes do limiar, entregue tarde pelo CDN) entra no histórico mas não
   * encerra pausa: nada novo foi publicado desde então.
   */
  observar(uf: string | null, v: Versao, em: string): ItemLote[] {
    const chave = uf ?? NAC;
    const l = this.lista(chave);
    const ult = l.at(-1);
    if (ult && v.geradoMs <= ult.geradoMs) return [];
    l.push(v);
    const out: ItemLote[] = [];
    const chegada = Date.parse(em);
    const velha = (limiarMin: number): boolean => Number.isFinite(chegada) && chegada - v.geradoMs > limiarMin * 60000;
    const a = this.abertas.get(chave);
    if (a && !velha(a.nivel === "uf" ? this.o.limiarUfMin : this.o.limiarNacionalMin)) out.push(...this.fechar(chave, a, v.geradoMs, v.st, em));
    const g = this.abertas.get(GERAL);
    if (g && !velha(this.o.limiarNacionalMin)) out.push(...this.fechar(GERAL, g, v.geradoMs, this.somaUfs(Number.POSITIVE_INFINITY), em));
    return out;
  }

  private abrir(chave: string, nivel: Nivel, uf: string | null, deMs: number, stAntes: number, agora: number, extra: Record<string, unknown>): ItemLote[] {
    const de = isoDe(deMs);
    const detectadoEm = isoDe(agora);
    const minutos = min1(agora - deMs);
    const longa = nivel !== "uf" && minutos >= this.o.longaMin;
    this.abertas.set(chave, { nivel, uf, de, deMs, stAntes, detectadoEm, longa });
    const row: LinhaPausa = { nivel, uf, de, ate: null, minutos: null, st_antes: stAntes, st_depois: null, detectado_em: detectadoEm };
    const limiar = nivel === "uf" ? this.o.limiarUfMin : this.o.limiarNacionalMin;
    return [
      { k: "pausa", row },
      this.evento(nivel, uf, detectadoEm, `pausa_${nivel}_inicio`, longa ? "error" : "warn", {
        desde: de, minutos, limiar_min: limiar, st: stAntes, ...extra, rotulo: ROTULO_PAUSA,
      }),
    ];
  }

  /** Avaliação periódica: abre pausas, escala as longas e acompanha a soma das UFs adiante. */
  avaliar(agora: number, fresco: Frescor): ItemLote[] {
    const out: ItemLote[] = [];
    const em = isoDe(agora);
    const somaAgora = this.somaUfs(Number.POSITIVE_INFINITY);
    const somaTs = this.somaTsUfs();

    // geral: nada novo em nenhum arquivo, seções pendentes, e o coletor enxergando o TSE
    const ultG = this.ultimaGeracaoMs();
    if (ultG !== null && !this.abertas.has(GERAL) && somaAgora > 0 && somaAgora < somaTs && fresco(null) && agora - ultG > (this.o.limiarNacionalMin + this.o.folgaMin) * 60000) {
      out.push(...this.abrir(GERAL, "geral", null, ultG, somaAgora, agora, { ts: somaTs }));
    }

    // nacional
    const nac = this.hist.get(NAC)?.at(-1);
    if (nac && !this.abertas.has(NAC) && nac.ts > 0 && nac.st < nac.ts && fresco(null)) {
      const anda = this.paradoComPaisAndando(agora, nac.geradoMs, this.o.limiarNacionalMin, null);
      if (anda) out.push(...this.abrir(NAC, "nacional", null, nac.geradoMs, nac.st, agora, { ts: nac.ts, soma_ufs_st: anda.agora, soma_ufs_st_antes: anda.antes }));
    }

    // UFs
    for (const uf of this.ufs) {
      const v = this.hist.get(uf)?.at(-1);
      if (!v || this.abertas.has(uf) || v.ts <= 0 || v.st >= v.ts || !fresco(uf)) continue;
      const anda = this.paradoComPaisAndando(agora, v.geradoMs, this.o.limiarUfMin, uf);
      if (anda) out.push(...this.abrir(uf, "uf", uf, v.geradoMs, v.st, agora, { ts: v.ts, outras_ufs_st: anda.agora, outras_ufs_st_antes: anda.antes }));
    }

    // escalada das longas (nacional e geral), uma vez por pausa
    for (const [chave, a] of this.abertas) {
      if (a.nivel === "uf" || a.longa) continue;
      const minutos = min1(agora - a.deMs);
      if (minutos < this.o.longaMin) continue;
      a.longa = true;
      out.push(this.evento(a.nivel, null, em, `pausa_${a.nivel}_longa`, "error", { desde: a.de, minutos, st: a.stAntes, rotulo: ROTULO_PAUSA, chave }));
    }

    // soma das UFs adiante do nacional
    if (nac && nac.ts > 0) {
      const dif = somaAgora - nac.st;
      const pct = (100 * dif) / nac.ts;
      if (pct > this.o.adiantePct) {
        this.adianteDesde ??= agora;
        const minutos = min1(agora - this.adianteDesde);
        if (!this.adianteEmitido && minutos > this.o.adianteMin) {
          this.adianteEmitido = true;
          out.push(
            this.evento("nacional", null, em, "soma_ufs_adiante", "warn", {
              soma_ufs_st: somaAgora, st: nac.st, ts: nac.ts, diferenca_secoes: dif, diferenca_pct: Math.round(pct * 100) / 100, minutos,
              desde: isoDe(this.adianteDesde), rotulo: ROTULO_PAUSA,
            }),
          );
        }
      } else {
        this.adianteDesde = null;
        this.adianteEmitido = false;
      }
    }
    return out;
  }

  /** Pausa em curso de um arquivo (para testes e diagnóstico). */
  aberta(uf: string | null | "geral"): { de: string; detectado_em: string } | null {
    const a = this.abertas.get(uf === "geral" ? GERAL : (uf ?? NAC));
    return a ? { de: a.de, detectado_em: a.detectadoEm } : null;
  }

  /**
   * Partida: histórico das versões de br e UFs (presidente) e pausas sem `ate` do banco.
   * Pausa aberta cujo arquivo já tem versão posterior a `de` fecha na hora (queda no meio).
   */
  carregar(db: Database, agora: number): ItemLote[] {
    type L = { nivel: string; uf: string | null; gerado_em: string | null; st: number | null; ts: number | null };
    const rows = db
      .query<L, [number]>(
        `SELECT a.nivel, a.uf, s.gerado_em, t.st, t.ts FROM arquivo a
         JOIN snapshot s ON s.arquivo_id = a.id AND s.regressivo = 0 JOIN totais t ON t.snapshot_id = s.id
         WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel IN ('br', 'uf') ORDER BY s.id`,
      )
      .all(this.o.ele);
    for (const r of rows) {
      const g = r.gerado_em === null ? Number.NaN : Date.parse(r.gerado_em);
      if (!Number.isFinite(g)) continue;
      const chave = r.nivel === "br" ? NAC : (r.uf ?? NAC);
      const l = this.lista(chave);
      const ult = l.at(-1);
      if (ult && g <= ult.geradoMs) continue;
      l.push({ geradoMs: g, st: r.st ?? 0, ts: r.ts ?? 0 });
    }
    type P = { nivel: Nivel; uf: string | null; de: string; st_antes: number | null; detectado_em: string };
    const abertas = db.query<P, []>("SELECT nivel, uf, de, st_antes, detectado_em FROM pausa WHERE ate IS NULL").all();
    const longas = new Set(
      db
        .query<{ d: string | null }, []>("SELECT json_extract(detalhe, '$.desde') AS d FROM evento WHERE tipo IN ('pausa_nacional_longa', 'pausa_geral_longa')")
        .all()
        .map((x) => x.d),
    );
    const out: ItemLote[] = [];
    const em = isoDe(agora);
    for (const p of abertas) {
      const chave = p.nivel === "geral" ? GERAL : p.nivel === "nacional" ? NAC : (p.uf ?? NAC);
      const a: Aberta = { nivel: p.nivel, uf: p.uf, de: p.de, deMs: Date.parse(p.de), stAntes: p.st_antes ?? 0, detectadoEm: p.detectado_em, longa: longas.has(p.de) };
      const posterior = p.nivel === "geral"
        ? [...this.hist.values()].flatMap((l) => l.filter((v) => v.geradoMs > a.deMs)).sort((x, y) => x.geradoMs - y.geradoMs)[0]
        : this.hist.get(chave)?.find((v) => v.geradoMs > a.deMs);
      if (posterior) {
        const stDepois = p.nivel === "geral" ? this.somaUfs(posterior.geradoMs) : posterior.st;
        out.push(...this.fechar(chave, a, posterior.geradoMs, stDepois, em));
      } else {
        this.abertas.set(chave, a);
      }
    }
    return out;
  }
}
