// Auditoria do 2º turno: pausas, amostra de seções e totalização paralela. Contrato em
// ../../../analysis/apuracao_2t_2026/CONTRATO.md. Só leitura: quem detecta e grava é o coletor.
import type { Database } from "bun:sqlite";
import { resumoParalela } from "../paralela/resumo.ts";
import type { ParalelaOut } from "../paralela/resumo.ts";
import { resumoComparecimento } from "../secoes2t/comparecimento.ts";
import type { ComparecimentoOut } from "../secoes2t/comparecimento-tipos.ts";
import { resumoSecoes, tabelaExiste } from "../secoes2t/resumo.ts";
import type { SecoesOut } from "../secoes2t/resumo.ts";
import { minutosDesde17h, T0_1T_MS, T0_2T_MS } from "../turno2/comum.ts";
import { carregarReferencia, carregarReferenciaSecoes } from "../turno2/referencia.ts";
import { CacheCurto } from "./cache.ts";
import { municipios as municipiosMu } from "./indicadores/municipios.ts";
import { eleicoes } from "./api-config.ts";
import { FIM, municipiosIndex } from "./consultas.ts";
import type { Contexto } from "./contexto.ts";
import type { Params } from "./http.ts";

interface ConfigGravada {
  pausas?: { limiar_min?: number; limiar_uf_min?: number };
  secoes?: { nacional_por_uf?: number; estaduais_por_uf?: number; intervalo_s?: number };
}

function configGravada(db: Database): ConfigGravada {
  const v = db.query<{ valor: string | null }, []>("SELECT valor FROM meta WHERE chave = 'turno2_config'").get()?.valor ?? null;
  if (v === null) return {};
  try {
    return JSON.parse(v) as ConfigGravada;
  } catch {
    return {};
  }
}

const t0De = (db: Database): number => (eleicoes(db).turno === 2 ? T0_2T_MS : T0_1T_MS);
const r1 = (x: number): number => Math.round(x * 10) / 10;
const segundos = (de: string | null, ate: string): number | null => {
  if (de === null) return null;
  const d = (Date.parse(ate) - Date.parse(de)) / 1000;
  return Number.isFinite(d) ? Math.round(d) : null;
};

// ---------------------------------------------------------------- /api/2t/pausas

interface VersaoArq {
  nivel: string;
  uf: string | null;
  gerado_em: string | null;
  st: number | null;
  ts: number | null;
}

interface PausaRow {
  nivel: "nacional" | "uf" | "geral";
  uf: string | null;
  de: string;
  ate: string | null;
  minutos: number | null;
  st_antes: number | null;
  st_depois: number | null;
  detectado_em: string;
}

interface Historico {
  de: string;
  ate: string;
  minutos: number;
  st_antes: number | null;
  st_depois: number | null;
}

export interface PausasOut {
  at: string;
  min: number | null;
  limiar_min: number;
  nacional: {
    ultima_versao_em: string | null;
    idade_s: number | null;
    st: number;
    ts: number;
    em_pausa: boolean;
    pausa_atual: { desde: string; minutos: number } | null;
    historico: Historico[];
  };
  soma_ufs: { st: number; pst: number; defasagem_secoes: number; defasagem_min: number };
  ufs: { uf: string; ultima_versao_em: string | null; idade_s: number | null; em_pausa: boolean; st: number; ts: number; historico_n: number }[];
  referencia_1t: { pausa_geral: { de: string; ate: string; minutos: number }; travamento_nacional: { de: string; ate: string } };
}

/** Pausas do 1º turno (04/10/2026), da régua: referência fixa do contrato. */
const REFERENCIA_1T: PausasOut["referencia_1t"] = {
  pausa_geral: { de: "19:32", ate: "20:02", minutos: 29.6 },
  travamento_nacional: { de: "18:00", ate: "18:10" },
};

/** União de intervalos de pausa (em curso = sem `ate`), na ordem de início. */
export function unirPausas(l: readonly PausaRow[]): PausaRow[] {
  const ord = [...l].sort((a, b) => (a.de < b.de ? -1 : a.de > b.de ? 1 : 0));
  const out: PausaRow[] = [];
  for (const p of ord) {
    const u = out.at(-1);
    if (u && (u.ate === null || p.de <= u.ate)) {
      if (u.ate !== null && (p.ate === null || p.ate > u.ate)) {
        u.ate = p.ate;
        u.st_depois = p.st_depois;
      }
      u.minutos = u.ate === null ? null : r1((Date.parse(u.ate) - Date.parse(u.de)) / 60000);
      if (p.detectado_em < u.detectado_em) u.detectado_em = p.detectado_em;
      continue;
    }
    out.push({ ...p });
  }
  return out;
}

export function calcularPausas(db: Database, atParam: string | undefined, agora: string, t0Ms: number, ele: number, limiar: number): PausasOut {
  const at = atParam ?? agora;
  const versoes = db
    .query<VersaoArq, [string, number]>(
      `SELECT a.nivel, a.uf, s.gerado_em, t.st, t.ts FROM arquivo a
       JOIN snapshot s ON s.id = (SELECT MAX(s2.id) FROM snapshot s2 WHERE s2.arquivo_id = a.id AND s2.regressivo = 0 AND s2.capturado_em <= ?1)
       LEFT JOIN totais t ON t.snapshot_id = s.id
       WHERE a.tipo = 'u' AND a.eleicao_cd = ?2 AND a.cargo_cd = 1 AND a.nivel IN ('br', 'uf')`,
    )
    .all(atParam ?? FIM, ele);
  const pausas = tabelaExiste(db, "pausa")
    ? db.query<PausaRow, [string]>("SELECT nivel, uf, de, ate, minutos, st_antes, st_depois, detectado_em FROM pausa WHERE detectado_em <= ? ORDER BY de").all(at)
    : [];
  const doNivel = (nivel: PausaRow["nivel"], uf: string | null): PausaRow[] => pausas.filter((p) => p.nivel === nivel && (nivel !== "uf" || p.uf === uf));
  const atual = (l: readonly PausaRow[]): { desde: string; minutos: number } | null => {
    const p = l.find((x) => x.ate === null || x.ate > at);
    return p ? { desde: p.de, minutos: r1((Date.parse(at) - Date.parse(p.de)) / 60000) } : null;
  };
  const historico = (l: readonly PausaRow[]): Historico[] =>
    l
      .filter((x): x is PausaRow & { ate: string } => x.ate !== null && x.ate <= at)
      .map((x) => ({ de: x.de, ate: x.ate, minutos: x.minutos ?? r1((Date.parse(x.ate) - Date.parse(x.de)) / 60000), st_antes: x.st_antes, st_depois: x.st_depois }));

  const br = versoes.find((v) => v.nivel === "br");
  const ufs = versoes.filter((v) => v.nivel === "uf" && v.uf !== null).sort((a, b) => ((a.uf ?? "") < (b.uf ?? "") ? -1 : 1));
  const somaSt = ufs.reduce((s, v) => s + (v.st ?? 0), 0);
  const somaTs = ufs.reduce((s, v) => s + (v.ts ?? 0), 0);
  const stBr = br?.st ?? 0;
  const defasagem = somaSt - stBr;
  const maxUf = ufs.reduce<string | null>((m, v) => (v.gerado_em !== null && (m === null || v.gerado_em > m) ? v.gerado_em : m), null);
  const defMin = defasagem > 0 && maxUf !== null && br?.gerado_em ? Math.max(0, r1((Date.parse(maxUf) - Date.parse(br.gerado_em)) / 60000)) : 0;
  // O bloco nacional junta as pausas do arquivo nacional e as gerais (nenhum arquivo publica):
  // nas duas o arquivo nacional ficou sem versão nova; intervalos sobrepostos viram um só.
  const nac = unirPausas([...doNivel("nacional", null), ...doNivel("geral", null)]);
  return {
    at,
    min: minutosDesde17h(at, t0Ms),
    limiar_min: limiar,
    nacional: {
      ultima_versao_em: br?.gerado_em ?? null, idade_s: segundos(br?.gerado_em ?? null, at), st: stBr, ts: br?.ts ?? 0,
      em_pausa: atual(nac) !== null, pausa_atual: atual(nac), historico: historico(nac),
    },
    soma_ufs: { st: somaSt, pst: somaTs > 0 ? Math.round((10000 * somaSt) / somaTs) / 100 : 0, defasagem_secoes: defasagem, defasagem_min: defMin },
    ufs: ufs.map((v) => {
      const l = doNivel("uf", v.uf);
      return {
        uf: (v.uf ?? "").toUpperCase(), ultima_versao_em: v.gerado_em, idade_s: segundos(v.gerado_em, at), em_pausa: atual(l) !== null,
        st: v.st ?? 0, ts: v.ts ?? 0, historico_n: historico(l).length,
      };
    }),
    referencia_1t: REFERENCIA_1T,
  };
}

export function pausas(ctx: Contexto, db: Database, p: Params): PausasOut {
  const at = p.at();
  const limiar = configGravada(db).pausas?.limiar_min ?? 5;
  return calcularPausas(db, at, ctx.agora(), t0De(db), eleicoes(db).federal, limiar);
}

// ---------------------------------------------------------------- /api/2t/secoes

export function secoes(ctx: Contexto, db: Database, p: Params): SecoesOut {
  const cfg = configGravada(db).secoes ?? {};
  const muns = municipiosIndex(db);
  return resumoSecoes(db, {
    at: p.at(), agora: ctx.agora(), t0Ms: t0De(db), ref: carregarReferencia(),
    desenho: { nacional_por_uf: cfg.nacional_por_uf ?? 150, estaduais_por_uf: cfg.estaduais_por_uf ?? 600, inclui_paralela: true, intervalo_s: cfg.intervalo_s ?? 900 },
    nome: (cd) => muns.get(cd)?.nome ?? null,
  });
}

// ---------------------------------------------------------------- /api/2t/paralela

export function paralela(ctx: Contexto, db: Database, p: Params): ParalelaOut {
  return resumoParalela(db, { at: p.at(), agora: ctx.agora() });
}

// ---------------------------------------------------------------- /api/2t/comparecimento

const cacheComparecimento = new CacheCurto<ComparecimentoOut>(10_000, 16);

/** Vigilância de falso comparecimento; cache de 10 s (secao_2t muda sem mudar snapshot). */
export function comparecimento(ctx: Contexto, db: Database, p: Params): ComparecimentoOut {
  const at = p.at();
  const janela = Math.floor(Date.now() / 10_000);
  return cacheComparecimento.obter([db.filename, at ?? ""].join("|"), janela, () => {
    const ele = eleicoes(db).federal;
    const muns = municipiosIndex(db);
    return resumoComparecimento(db, {
      at, agora: ctx.agora(), t0Ms: t0De(db), eleFederal: ele, refSecoes: carregarReferenciaSecoes(), ref1t: carregarReferencia(),
      municipios: municipiosMu(db, ele, 1, at), nome: (cd) => muns.get(cd)?.nome ?? null,
    });
  });
}

export function limparCacheComparecimento(): void {
  cacheComparecimento.limpar();
}
