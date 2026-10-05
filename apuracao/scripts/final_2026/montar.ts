// Montagem das seções do final.json a partir das disputas lidas (sem acesso a banco).
import type { DisputaLida } from "./db.ts";
import {
  blocoDe, blocos, contarPor, contarPorCampo, CAMPOS, eleitosMajoritario, eleitosProporcional, governador, r2, zeroPorCampo,
  campoDe, type Campo, type Cand, type Classificador, type Governo,
} from "./puro.ts";

export const UFS = ["ac", "al", "am", "ap", "ba", "ce", "df", "es", "go", "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr", "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to"] as const;
export const ASSEMBLEIAS = ["sp", "mg", "rj", "ba", "rs", "pr", "pe", "ce", "go", "sc", "df"] as const;

export const curto = (c: Cand): { nome: string; partido: string; campo: Campo; votos: number; pct: number; st: string | null } => ({
  nome: c.nome, partido: c.partido, campo: c.campo, votos: c.vap, pct: r2(c.pct), st: c.st,
});

const pctDe = (x: number, t: number): number => (t > 0 ? r2((100 * x) / t) : 0);

function pctPorCampo(r: Record<Campo, number>): Record<Campo, number> {
  const t = CAMPOS.reduce((s, c) => s + r[c], 0);
  const o = zeroPorCampo();
  for (const c of CAMPOS) o[c] = pctDe(r[c], t);
  return o;
}

/** Recalcula o pct sobre os válidos (o pvapn de arquivos somados não serve). */
const comPct = (cands: Cand[], vv: number): Cand[] => cands.map((c) => ({ ...c, pct: vv > 0 ? (100 * c.vap) / vv : 0 }));

export function montarPresidente(ds: Map<string, DisputaLida>) {
  const br = ds.get("6257:1:br");
  const ufs = [...UFS, "zz"].map((u) => ds.get(`6257:1:${u}`)).filter((d): d is DisputaLida => d !== undefined);
  const soma = (k: "st" | "ts" | "te" | "comparecimento" | "abstencao" | "tv" | "vv" | "vb" | "tvn"): number => ufs.reduce((s, d) => s + (d.snap[k] ?? 0), 0);
  const usarSoma = !br || (br.snap.st ?? 0) < soma("st");
  const t = (k: "st" | "ts" | "te" | "comparecimento" | "abstencao" | "tv" | "vv" | "vb" | "tvn"): number => (usarSoma ? soma(k) : (br?.snap[k] ?? 0));
  let cands: Cand[];
  if (usarSoma) {
    const m = new Map<string, Cand>();
    for (const d of ufs) for (const c of d.cands) m.set(c.sq, { ...c, vap: (m.get(c.sq)?.vap ?? 0) + c.vap });
    cands = [...m.values()];
  } else cands = br?.cands ?? [];
  const vv = t("vv");
  cands = comPct(cands, vv).sort((a, b) => b.vap - a.vap);
  const [a, b] = cands;
  const porUf = ufs.map((d) => {
    const cs = comPct(d.cands, d.vv).sort((x, y) => y.vap - x.vap);
    const l = cs[0];
    const s = cs[1];
    return { uf: d.uf.toUpperCase(), pst: r2(d.pst), lider: l?.nome ?? "", partido_lider: l?.partido ?? "", pct_lider: r2(l?.pct ?? 0), segundo: s?.nome ?? "", pct_segundo: r2(s?.pct ?? 0), margem_pp: r2((l?.pct ?? 0) - (s?.pct ?? 0)), margem_votos: (l?.vap ?? 0) - (s?.vap ?? 0) };
  });
  const estados = porUf.filter((u) => u.uf !== "ZZ");
  const venceuEm = Object.fromEntries([a, b].filter((c): c is Cand => !!c).map((c) => [c.nome, estados.filter((u) => u.lider === c.nome).map((u) => u.uf)]));
  const maiores = Object.fromEntries([a, b].filter((c): c is Cand => !!c).map((c) => [c.nome, estados.filter((u) => u.lider === c.nome).sort((x, y) => y.margem_pp - x.margem_pp).slice(0, 5).map((u) => ({ uf: u.uf, margem_pp: u.margem_pp, margem_votos: u.margem_votos }))]));
  return {
    fonte: usarSoma ? "soma_ufs" : "tse",
    nota_fonte: `arquivo nacional do TSE com ${br?.snap.st ?? 0} seções; soma dos 28 arquivos (27 UFs e exterior) com ${soma("st")}`,
    tf: br?.tf ?? false,
    gerado_em: br?.snap.gerado_em ?? null,
    pst: pctDe(t("st"), t("ts")),
    st: t("st"), ts: t("ts"), eleitores: t("te"),
    comparecimento: t("comparecimento"), pct_comparecimento: pctDe(t("comparecimento"), t("te")),
    abstencao: t("abstencao"), pct_abstencao: pctDe(t("abstencao"), t("te")),
    total_votos: t("tv"), validos: vv,
    brancos: t("vb"), pct_brancos: pctDe(t("vb"), t("tv")),
    nulos: t("tvn"), pct_nulos: pctDe(t("tvn"), t("tv")),
    top5: cands.slice(0, 5).map(curto),
    segundo_turno: (a?.pct ?? 0) <= 50,
    par_2t: [a, b].filter((c): c is Cand => !!c).map(curto),
    diferenca_pp: r2((a?.pct ?? 0) - (b?.pct ?? 0)),
    diferenca_votos: (a?.vap ?? 0) - (b?.vap ?? 0),
    ufs: estados,
    exterior: porUf.find((u) => u.uf === "ZZ") ?? null,
    venceu_em: venceuEm,
    maiores_margens: maiores,
    finalistas: [a, b].filter((c): c is Cand => !!c),
  };
}

export function montarGovernadores(ds: Map<string, DisputaLida>) {
  const govs: Governo[] = UFS.map((u) => ds.get(`6259:3:${u}`)).filter((d): d is DisputaLida => !!d).map(governador);
  const eleitos = govs.filter((g) => g.decisao === "eleito");
  const segundo = govs.filter((g) => g.decisao === "segundo_turno");
  return {
    govs,
    saida: {
      n_eleitos_1t: eleitos.length,
      n_segundo_turno: segundo.length,
      n_tse: govs.filter((g) => g.fonte === "tse").length,
      n_provisorio: govs.filter((g) => g.fonte === "provisorio").length,
      eleitos_1t_por_campo: contarPorCampo(eleitos.map((g) => g.candidatos[0] as Cand)),
      segundo_turno_candidatos_por_campo: contarPorCampo(segundo.flatMap((g) => g.candidatos)),
      segundo_turno_pares: contarPor(segundo, (g) => g.candidatos.map((c) => blocoDe(c.campo)).sort().join(" x ")),
      ufs: govs.map((g) => ({ uf: g.uf.toUpperCase(), fonte: g.fonte, pst: r2(g.pst), decisao: g.decisao, candidatos: g.candidatos.map(curto), terceiro: g.terceiro ? curto(g.terceiro) : null })),
    },
  };
}

export interface Senador2022 {
  uf: string;
  sq_candidato: string;
  nome: string;
  partido: string;
  campo: string;
}

/** Exceção declarada em analysis/senado_2026/metodo.md: Cleitinho, eleito pelo PSC, conta como direita e Republicanos. */
const EXCECAO_2022: Record<string, { campo: Campo; partido: string }> = { "130001671677": { campo: "direita", partido: "REPUBLICANOS" } };

export function montarSenado(ds: Map<string, DisputaLida>, s2022: readonly Senador2022[], cl: Classificador) {
  const ufs = UFS.map((u) => ds.get(`6259:5:${u}`)).filter((d): d is DisputaLida => !!d).map((d) => {
    const e = eleitosMajoritario(d, 2);
    const terceiro = d.cands.filter((c) => c.valido && !e.eleitos.includes(c)).sort((x, y) => y.vap - x.vap)[0] ?? null;
    const seg = e.eleitos[1];
    return { d, e, terceiro, margem_pp: seg && terceiro ? r2(seg.pct - terceiro.pct) : null, margem_votos: seg && terceiro ? seg.vap - terceiro.vap : null };
  });
  const novos = ufs.flatMap((u) => u.e.eleitos.map((c) => ({ partido: c.partido, campo: c.campo })));
  const continuam = s2022.map((s) => {
    const x = EXCECAO_2022[s.sq_candidato];
    const doArquivo = CAMPOS.find((c) => c === s.campo && c !== "indefinido");
    return { partido: x?.partido ?? s.partido, campo: x?.campo ?? doArquivo ?? campoDe(cl, null, s.partido) };
  });
  const todos = [...continuam, ...novos];
  const porCampo = contarPorCampo(todos);
  return {
    ufs,
    saida: {
      n_ufs_tse: ufs.filter((u) => u.e.fonte === "tse").length,
      n_ufs_provisorio: ufs.filter((u) => u.e.fonte === "provisorio").length,
      ufs: ufs.map((u) => ({ uf: u.d.uf.toUpperCase(), fonte: u.e.fonte, pst: r2(u.d.pst), eleitos: u.e.eleitos.map(curto), terceiro: u.terceiro ? curto(u.terceiro) : null, margem_2a_vaga_pp: u.margem_pp, margem_2a_vaga_votos: u.margem_votos })),
      senado_2027: {
        total: todos.length,
        continuam: continuam.length,
        novos: novos.length,
        por_campo: porCampo,
        por_bloco: blocos(porCampo),
        continuam_por_campo: contarPorCampo(continuam),
        novos_por_campo: contarPorCampo(novos),
        por_partido: contarPor(todos, (x) => x.partido),
        nota: "27 eleitos em 2022 (eleitos da urna, não titulares atuais; Cleitinho como direita e Republicanos por exceção declarada) mais 54 eleitos em 2026",
      },
      comparacao_2023: { disponivel: false, nota: "analysis/senado_2026/ guarda só os 27 eleitos em 2022 (senadores_2022.json); não há a composição de 2023 com os 54 eleitos em 2018, então a comparação fica de fora" },
    },
  };
}

export function montarProporcional(ds: Map<string, DisputaLida>, chaves: readonly string[]) {
  return chaves.map((k) => ds.get(k)).filter((d): d is DisputaLida => !!d).map((d) => ({ d, e: eleitosProporcional(d) }));
}

export function montarCamara(ds: Map<string, DisputaLida>, cl: Classificador) {
  const ufs = montarProporcional(ds, UFS.map((u) => `6259:6:${u}`));
  const eleitos = ufs.flatMap((u) => u.e.eleitos);
  const porCampo = contarPorCampo(eleitos);
  const votos = new Map<string, number>();
  for (const u of ufs) for (const p of u.d.partidos) votos.set(p.sigla, (votos.get(p.sigla) ?? 0) + p.tvtn + p.tvtl);
  const votosCampo = zeroPorCampo();
  for (const [sg, v] of votos) votosCampo[campoDe(cl, null, sg)] += v;
  // Conferência: nas UFs finais, a alocação provisória reproduz a marca do TSE?
  const conferencia = ufs.filter((u) => u.e.fonte === "tse").map((u) => {
    const prov = eleitosProporcional({ ...u.d, tf: false });
    const a = contarPor(u.e.eleitos, (c) => c.partido);
    const b = contarPor(prov.eleitos, (c) => c.partido);
    const difs = [...new Set([...Object.keys(a), ...Object.keys(b)])].filter((p) => a[p] !== b[p]).map((p) => `${p}: TSE ${a[p] ?? 0}, provisório ${b[p] ?? 0}`);
    const nomes = new Set(u.e.eleitos.map((c) => c.sq));
    return { uf: u.d.uf.toUpperCase(), partidos_iguais: difs.length === 0, mesmos_nomes: prov.eleitos.every((c) => nomes.has(c.sq)), diferencas: difs };
  });
  return {
    ufs,
    saida: {
      vagas_total: ufs.reduce((s, u) => s + u.d.vagas, 0),
      eleitos_total: eleitos.length,
      n_ufs_tse: ufs.filter((u) => u.e.fonte === "tse").length,
      n_ufs_provisorio: ufs.filter((u) => u.e.fonte === "provisorio").length,
      ufs_provisorias: ufs.filter((u) => u.e.fonte === "provisorio").map((u) => u.d.uf.toUpperCase()),
      por_campo: porCampo,
      por_campo_pct: pctPorCampo(porCampo),
      blocos: blocos(porCampo),
      por_partido: contarPor(eleitos, (c) => c.partido),
      votos_por_campo: votosCampo,
      votos_por_campo_pct: pctPorCampo(votosCampo),
      nota_votos: "votos de legenda mais nominais válidos (tvtn + tvtl de voto_partido) somados nos 27 arquivos de UF",
      conferencia_provisorio_x_tse: conferencia,
      ufs: ufs.map((u) => ({ uf: u.d.uf.toUpperCase(), fonte: u.e.fonte, pst: r2(u.d.pst), vagas: u.d.vagas, qe: u.e.qe, por_campo: contarPorCampo(u.e.eleitos), eleitos: u.e.eleitos.map(curto) })),
    },
  };
}

export function montarAssembleias(ds: Map<string, DisputaLida>) {
  const lista = montarProporcional(ds, ASSEMBLEIAS.map((u) => (u === "df" ? "6259:8:df" : `6259:7:${u}`)));
  return {
    lista,
    saida: lista.map((u) => ({
      uf: u.d.uf.toUpperCase(),
      casa: u.d.cargo === 8 ? "Câmara Legislativa" : "Assembleia Legislativa",
      fonte: u.e.fonte,
      pst: r2(u.d.pst),
      vagas: u.d.vagas,
      por_campo: contarPorCampo(u.e.eleitos),
      blocos: blocos(contarPorCampo(u.e.eleitos)),
      por_partido: contarPor(u.e.eleitos, (c) => c.partido),
      mais_votados: [...u.d.cands].sort((a, b) => b.vap - a.vap).slice(0, 3).map(curto),
    })),
  };
}
