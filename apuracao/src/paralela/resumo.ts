// /api/2t/paralela: BUs recebidos pela totalização paralela, conferência contra o BU oficial e o
// placar dos BUs (soma dos BUs recebidos, não projeção). Só leitura de paralela_bu,
// paralela_conferencia e meta.paralela_estado; funciona com o Supabase fora do ar.
import type { Database } from "bun:sqlite";
import type { LinhaParalelaConferencia } from "../db/escrita.ts";
import { tabelaExiste } from "../secoes2t/resumo.ts";
import type { CargoParalela, Diferenca, Situacao } from "./conferir.ts";
import { rotuloDiferenca } from "./conferir.ts";
import type { EstadoParalela } from "./ponte.ts";
import { META_ESTADO, ROTULO_PARALELA } from "./ponte.ts";

interface BuRow {
  id: number;
  recebido_em: string;
  uf: string;
  mun: string;
  zona: number;
  secao: number;
  fase: string | null;
  aptos: number | null;
  comparecimento: number | null;
  hash_final: string;
  cargos_json: string;
}

export interface PlacarPresidente {
  votos: Record<string, number>;
  comparecimento: number;
  aptos: number;
  brancos: number;
  nulos: number;
  secoes: number;
}

export interface ParalelaOut {
  at: string;
  fonte: "supabase";
  atualizado_em: string | null;
  erro: string | null;
  recebidos: { bus: number; envios: number; secoes: number; ufs: number; conflitos: number };
  conferencia: { iguais: number; divergentes: number; tse_ainda_nao_publicou: number; erro: number; fora_do_oficial: number; pendentes: number };
  cobertura_uf: { uf: string; bus: number; secoes_total: number; pct: number }[];
  placar_bus: { rotulo: string; presidente: PlacarPresidente; governador: Record<string, { votos: Record<string, number>; secoes: number }> };
  divergencias: { uf: string; mun: string; zona: number; secao: number; recebido_em: string; conferido_em: string; campos: { campo: string; paralela: number | boolean | null; tse: number | boolean | null }[] }[];
  ultimos: { uf: string; mun: string; zona: number; secao: number; recebido_em: string; situacao: Situacao | "pendente" }[];
}

const chaveSec = (b: { uf: string; mun: string; zona: number; secao: number }): string => `${b.uf}|${b.mun}|${b.zona}|${b.secao}`;

function estadoDe(db: Database): EstadoParalela | null {
  const txt = db.query<{ valor: string | null }, [string]>("SELECT valor FROM meta WHERE chave = ?").get(META_ESTADO)?.valor ?? null;
  if (txt === null) return null;
  try {
    return JSON.parse(txt) as EstadoParalela;
  } catch {
    return null;
  }
}

export function resumoParalela(db: Database, o: { at: string | undefined; agora: string }): ParalelaOut {
  const at = o.at ?? o.agora;
  const estado = estadoDe(db);
  const temTabelas = tabelaExiste(db, "paralela_bu") && tabelaExiste(db, "paralela_conferencia");
  const bus = temTabelas
    ? db
        .query<BuRow, [string]>(
          `SELECT id, recebido_em, uf, mun, zona, secao, fase, aptos, comparecimento, hash_final, cargos_json
           FROM paralela_bu WHERE recebido_em <= ? ORDER BY id`,
        )
        .all(at)
    : [];
  const confs = temTabelas
    ? new Map(
        db
          .query<LinhaParalelaConferencia, [string]>("SELECT * FROM paralela_conferencia WHERE conferido_em <= ?")
          .all(at)
          .map((c) => [c.bu_id, c] as const),
      )
    : new Map<number, LinhaParalelaConferencia>();

  // seções oficiais com mais de um BU distinto ficam fora do placar, como em v_bu_unico
  const oficiais = bus.filter((b) => b.fase === "O");
  const hashes = new Map<string, Set<string>>();
  for (const b of oficiais) {
    const k = chaveSec(b);
    const s = hashes.get(k) ?? new Set<string>();
    s.add(b.hash_final);
    hashes.set(k, s);
  }
  const conflitos = [...hashes.values()].filter((s) => s.size > 1).length;
  const unicos = oficiais.filter((b) => (hashes.get(chaveSec(b))?.size ?? 0) === 1);

  const presidente: PlacarPresidente = { votos: {}, comparecimento: 0, aptos: 0, brancos: 0, nulos: 0, secoes: 0 };
  const governador: Record<string, { votos: Record<string, number>; secoes: number }> = {};
  const vistos = new Set<string>();
  for (const b of unicos) {
    const k = chaveSec(b);
    if (vistos.has(k)) continue;
    vistos.add(k);
    const cargos = JSON.parse(b.cargos_json) as CargoParalela[];
    const pres = cargos.find((c) => c.cargo === 1);
    if (pres) {
      presidente.secoes += 1;
      presidente.comparecimento += b.comparecimento ?? 0;
      presidente.aptos += b.aptos ?? 0;
      presidente.brancos += pres.bran;
      presidente.nulos += pres.nulo;
      for (const [n, v] of Object.entries(pres.votos)) if (!n.startsWith("LEGP")) presidente.votos[n] = (presidente.votos[n] ?? 0) + v;
    }
    const gov = cargos.find((c) => c.cargo === 3);
    if (gov) {
      const g = (governador[b.uf.toUpperCase()] ??= { votos: {}, secoes: 0 });
      g.secoes += 1;
      for (const [n, v] of Object.entries(gov.votos)) if (!n.startsWith("LEGP")) g.votos[n] = (g.votos[n] ?? 0) + v;
    }
  }

  const conferencia = { iguais: 0, divergentes: 0, tse_ainda_nao_publicou: 0, erro: 0, fora_do_oficial: 0, pendentes: 0 };
  const CAMPO: Readonly<Record<Situacao, keyof typeof conferencia>> = {
    igual: "iguais", divergente: "divergentes", tse_ainda_nao_publicou: "tse_ainda_nao_publicou", erro: "erro", fora_do_oficial: "fora_do_oficial",
  };
  for (const b of bus) {
    const c = confs.get(b.id);
    conferencia[c ? CAMPO[c.situacao] : "pendentes"] += 1;
  }
  const porId = new Map(bus.map((b) => [b.id, b] as const));
  const divergencias = [...confs.values()]
    .filter((c) => c.situacao === "divergente" && porId.has(c.bu_id))
    .sort((a, b) => (a.conferido_em < b.conferido_em ? 1 : a.conferido_em > b.conferido_em ? -1 : b.bu_id - a.bu_id))
    .slice(0, 50)
    .map((c) => {
      const dif = c.diferencas_json === null ? [] : (JSON.parse(c.diferencas_json) as Diferenca[]);
      return {
        uf: c.uf.toUpperCase(), mun: c.mun, zona: c.zona, secao: c.secao, recebido_em: porId.get(c.bu_id)?.recebido_em ?? c.primeira_em,
        conferido_em: c.conferido_em, campos: dif.map((d) => ({ campo: rotuloDiferenca(d), paralela: d.paralela, tse: d.tse })),
      };
    });

  const cobertura = (estado?.cobertura_uf ?? [])
    .map((c) => ({
      uf: c.uf.toUpperCase(), bus: c.secoes_com_bu, secoes_total: c.secoes_total,
      pct: c.secoes_total > 0 ? Math.round((10000 * c.secoes_com_bu) / c.secoes_total) / 100 : 0,
    }))
    .sort((a, b) => (a.uf < b.uf ? -1 : 1));

  return {
    at,
    fonte: "supabase",
    atualizado_em: estado?.atualizado_em ?? null,
    erro: estado === null ? "totalização paralela ainda não consultada" : estado.erro,
    recebidos: {
      bus: oficiais.length,
      envios: estado?.estatisticas?.envios ?? bus.length,
      secoes: hashes.size,
      ufs: new Set(oficiais.map((b) => b.uf)).size,
      conflitos,
    },
    conferencia,
    cobertura_uf: cobertura,
    placar_bus: { rotulo: ROTULO_PARALELA, presidente, governador },
    divergencias,
    ultimos: [...bus]
      .sort((a, b) => (a.recebido_em < b.recebido_em ? 1 : a.recebido_em > b.recebido_em ? -1 : b.id - a.id))
      .slice(0, 20)
      .map((b) => ({ uf: b.uf.toUpperCase(), mun: b.mun, zona: b.zona, secao: b.secao, recebido_em: b.recebido_em, situacao: confs.get(b.id)?.situacao ?? "pendente" })),
  };
}
