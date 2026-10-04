// Resumo dos últimos N minutos da apuração para o boletim falado (locutor automático).
// Lê só a API local e imprime um JSON compacto. Uso: bun run scripts/boletim-dados.ts [minutos]

export {};

const BASE = process.env.APURACAO_API ?? "http://127.0.0.1:4180";
const JANELA_MIN = Number(process.argv[2] ?? "10");

type Num = number;
interface Cand { sqcand: string; n: string; nmu: string; sg: string; vap: Num; pvapn: Num }
interface Resultado { s: { ts: Num; st: Num; pst: Num }; e: { te: Num; c: Num; a: Num; pc: Num; pa: Num }; v: { vv: Num; vb: Num; vn: Num; pvb: Num; pvn: Num; tv: Num }; dt_ht: string | null; cand: Cand[]; fonte?: "tse" | "soma_ufs"; nacional_tse?: { hg: string | null; st: Num; pst: Num } }
interface Lote { at: string; st: Num; d_st: Num; pst: Num; vv: Num; d_vv: Num; cand: Record<string, { vap: Num; d_vap: Num }> }
interface Lotes { candidatos: { sqcand: string; nmu: string }[]; lotes: Lote[]; fonte?: "tse" | "soma_ufs" }
interface Unidade { cd: string; nm: string; pst: Num; tf: boolean; te?: Num; lider?: { nmu: string; sg: string; pvapn: Num; campo?: string }; segundo?: { nmu: string; pvapn: Num }; margem?: Num }
interface Estado { agora: string; br: { ts: Num; st: Num; pst: Num; dt_ht: string | null; hg: string | null; atraso_s: Num | null }; ufs: { uf: string; nome?: string; pst: Num; st: Num; ts: Num; munf: Num; munpt: Num; munnr: Num }[]; historico: { at: string; st: Num; pst: Num }[]; coletor: { taxas_60s?: Record<string, Num>; fila?: Record<string, Num> } | null }
interface Anomalia { at: string; tipo: string; tipo_bruto?: string; texto: string; uf?: string | null }

async function j<T>(path: string): Promise<T> {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return (await r.json()) as T;
}
const brt = (iso: string | null | undefined): string => (iso ? new Date(iso).toLocaleTimeString("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit" }) : "");
const r1 = (x: Num): Num => Math.round(x * 10) / 10;

const [estado, br, lotes, mapaUf, mapaGov, mapaSen, anomalias, zz] = await Promise.all([
  j<Estado>("/api/estado"),
  j<Resultado>("/api/resultado?ele=6257&cargo=1&abr=br"),
  j<Lotes>("/api/lotes?ele=6257&cargo=1&abr=br&top=6"),
  j<{ unidades: Unidade[] }>("/api/mapa?ele=6257&cargo=1&nivel=uf"),
  j<{ unidades: Unidade[] }>("/api/mapa?ele=6259&cargo=3&nivel=uf"),
  j<{ unidades: Unidade[] }>("/api/mapa?ele=6259&cargo=5&nivel=uf&top=2"),
  j<Anomalia[]>("/api/anomalias?limit=60"),
  j<Resultado>("/api/resultado?ele=6257&cargo=1&abr=zz").catch(() => null),
]);

const agora = Date.parse(estado.agora);
const corte = agora - JANELA_MIN * 60_000;
const recentes = lotes.lotes.filter((l) => Date.parse(l.at) >= corte);
const antes = lotes.lotes.filter((l) => Date.parse(l.at) < corte).at(-1) ?? null;
const ultimo = lotes.lotes.at(-1) ?? null;
const principais = br.cand.slice(0, 6);
const janela = principais.map((c) => {
  const dv = antes ? (ultimo?.cand[c.sqcand]?.vap ?? 0) - (antes.cand[c.sqcand]?.vap ?? 0) : (ultimo?.cand[c.sqcand]?.vap ?? 0);
  return { nmu: c.nmu, sg: c.sg, vap: c.vap, pct: r1(c.pvapn), ganho_janela: dv };
});
const somaJanela = janela.reduce((a, c) => a + Math.max(0, c.ganho_janela), 0);
for (const c of janela) (c as { pct_do_que_chegou?: Num }).pct_do_que_chegou = somaJanela > 0 ? r1((100 * Math.max(0, c.ganho_janela)) / somaJanela) : 0;
const pctAntes = antes ? principais.map((c) => ({ nmu: c.nmu, pct: antes.vv > 0 ? r1((100 * (antes.cand[c.sqcand]?.vap ?? 0)) / antes.vv) : 0 })) : [];

// Ritmo: seções por minuto na janela e projeção ingênua de 100%.
const hist = estado.historico;
const h0 = hist.filter((h) => Date.parse(h.at) >= corte)[0] ?? hist[0];
const hN = hist.at(-1);
const minutos = h0 && hN ? (Date.parse(hN.at) - Date.parse(h0.at)) / 60_000 : 0;
const secPorMin = minutos > 0 && h0 && hN ? (hN.st - h0.st) / minutos : 0;
const faltam = estado.br.ts - estado.br.st;
const previsao = secPorMin > 0 ? new Date(agora + (faltam / secPorMin) * 60_000).toISOString() : null;

const ufs = estado.ufs.filter((u) => u.uf !== "zz").map((u) => ({ uf: u.uf.toUpperCase(), nome: u.nome, pst: r1(u.pst), st: u.st, ts: u.ts, munf: u.munf }));
const maisAdiantadas = [...ufs].sort((a, b) => b.pst - a.pst).slice(0, 5);
const maisAtrasadas = [...ufs].sort((a, b) => a.pst - b.pst).slice(0, 5);
const porUf = mapaUf.unidades.filter((u) => u.cd !== "zz").map((u) => ({ uf: u.cd.toUpperCase(), pst: r1(u.pst), lider: u.lider?.nmu, pct: u.lider ? r1(u.lider.pvapn) : null, segundo: u.segundo?.nmu, margem: u.margem !== undefined ? r1(u.margem) : null }));
const apertadas = porUf.filter((u) => u.margem !== null && u.pst >= 5).sort((a, b) => (a.margem ?? 99) - (b.margem ?? 99)).slice(0, 5);
const governadores = mapaGov.unidades.map((u) => ({ uf: u.cd.toUpperCase(), pst: r1(u.pst), lider: u.lider?.nmu, sg: u.lider?.sg, pct: u.lider ? r1(u.lider.pvapn) : null, decidido_1t: u.pst >= 100 && (u.lider?.pvapn ?? 0) > 50 }));
const senado = mapaSen.unidades.map((u) => ({ uf: u.cd.toUpperCase(), pst: r1(u.pst), lideres: (u as { top?: { nmu: string; sg: string; pvapn: Num }[] }).top?.slice(0, 2).map((t) => `${t.nmu} (${t.sg}) ${r1(t.pvapn)}%`) ?? [] }));
const viradas = anomalias.filter((a) => a.tipo === "virada" && Date.parse(a.at) >= corte).map((a) => `${brt(a.at)} ${a.texto}`);
const regressoes = anomalias.filter((a) => a.tipo === "regressao" && a.tipo_bruto !== "idg_regressivo" && Date.parse(a.at) >= corte).map((a) => `${brt(a.at)} ${a.texto}`);
const fechamentos = anomalias.filter((a) => a.tipo === "fechou" && Date.parse(a.at) >= corte).map((a) => a.texto);

const saida = {
  agora_brt: brt(estado.agora),
  janela_min: JANELA_MIN,
  nacional: {
    pst: r1(estado.br.pst), st: estado.br.st, ts: estado.br.ts,
    totalizacao_tse: brt(estado.br.dt_ht), atraso_leitura_s: estado.br.atraso_s !== null ? Math.round(estado.br.atraso_s) : null,
    validos: br.v.vv, total_votos: br.v.tv, brancos_pct: br.v.tv > 0 ? r1((100 * br.v.vb) / br.v.tv) : 0, nulos_pct: br.v.tv > 0 ? r1((100 * (br.v.tv - br.v.vv - br.v.vb)) / br.v.tv) : 0, comparecimento_pct: r1(br.e.pc), abstencao_pct: r1(br.e.pa),
    fonte_nacional: br.fonte ?? "tse",
    nacional_tse: br.fonte === "soma_ufs" && br.nacional_tse
      ? { nota: `arquivo nacional de presidente do TSE atrasado: gerado às ${brt(br.nacional_tse.hg)} com ${r1(br.nacional_tse.pst)}% das seções; o placar nacional aqui é a soma das 27 UFs e do exterior; os ganhos da janela ainda vêm do arquivo do TSE`, gerado_brt: brt(br.nacional_tse.hg), st: br.nacional_tse.st, pst: r1(br.nacional_tse.pst) }
      : null,
    candidatos: janela, pct_no_inicio_da_janela: pctAntes,
    diferenca_1_2_pp: janela.length >= 2 ? r1((janela[0]?.pct ?? 0) - (janela[1]?.pct ?? 0)) : null,
    diferenca_1_2_votos: janela.length >= 2 ? (janela[0]?.vap ?? 0) - (janela[1]?.vap ?? 0) : null,
  },
  lotes_na_janela: { fonte: lotes.fonte ?? "tse", n: recentes.length, secoes: recentes.reduce((a, l) => a + l.d_st, 0), validos: recentes.reduce((a, l) => a + l.d_vv, 0), ultimo: ultimo ? { hora: brt(ultimo.at), secoes: ultimo.d_st, validos: ultimo.d_vv } : null },
  ritmo: { secoes_por_min: Math.round(secPorMin), faltam_secoes: faltam, previsao_100_brt: brt(previsao) || null, minutos_medidos: r1(minutos) },
  ufs: { mais_adiantadas: maisAdiantadas, mais_atrasadas: maisAtrasadas, disputas_apertadas: apertadas, por_uf: porUf },
  governadores: { decididos_1t: governadores.filter((g) => g.decidido_1t), lideres: governadores },
  senado,
  exterior: zz ? { pst: r1(zz.s.pst), lider: zz.cand[0]?.nmu, pct: r1(zz.cand[0]?.pvapn ?? 0), segundo: zz.cand[1]?.nmu, pct2: r1(zz.cand[1]?.pvapn ?? 0) } : null,
  viradas, regressoes, fechamentos_uf: fechamentos,
  coletor: estado.coletor ? { taxas_60s: estado.coletor.taxas_60s, fila: estado.coletor.fila } : null,
};
console.log(JSON.stringify(saida, null, 1));
