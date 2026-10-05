// Avaliação final da noite da apuração de 2026: lê o banco de auditoria (somente leitura), grava
// data/boletins/final.json e data/boletins/final.md e imprime o markdown. Reexecutável a qualquer momento.
// Uso: bun run scripts/final-2026.ts   (APURACAO_DB troca o banco; padrão data/apuracao.sqlite)
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { abrirLeitura } from "../src/db/abrir.ts";
import { lerDisputas, lerLinha } from "./final_2026/db.ts";
import { brt, cand, int, pct, pp, ROTULO, tabela, tabelaBlocos, tabelaCampos } from "./final_2026/markdown.ts";
import { curto, montarAssembleias, montarCamara, montarGovernadores, montarPresidente, montarSenado, type Senador2022 } from "./final_2026/montar.ts";
import { blocoDe, campoDe, classificador, r2, vaoEstadual, type Cand } from "./final_2026/puro.ts";

const RAIZ = join(import.meta.dir, "..");
const DB = process.env.APURACAO_DB ?? join(RAIZ, "data/apuracao.sqlite");
const SAIDA = join(RAIZ, "data/boletins");

const cl = classificador(JSON.parse(readFileSync(join(RAIZ, "public/campos.json"), "utf8")) as Parameters<typeof classificador>[0]);
const s2022 = JSON.parse(readFileSync(join(RAIZ, "public/senadores_2022.json"), "utf8")) as Senador2022[];
const bytes = [DB, `${DB}-wal`].filter((p) => existsSync(p)).reduce((s, p) => s + statSync(p).size, 0);

const db = abrirLeitura(DB);
const ds = lerDisputas(db, cl);
const linha = lerLinha(db, bytes);
db.close();

const presidente = montarPresidente(ds);
const gov = montarGovernadores(ds);
const sen = montarSenado(ds, s2022, cl);
const camara = montarCamara(ds, cl);
const assembleias = montarAssembleias(ds);

// ---------------------------------------------------------------- fatos
const presUf = new Map<string, Cand[]>();
for (const [k, d] of ds) if (k.startsWith("6257:1:")) presUf.set(d.uf, d.cands);
const vao = vaoEstadual(gov.govs, presidente.finalistas, presUf);
const lider = (g: (typeof gov.govs)[number]): Cand | undefined => g.candidatos[0];
const proximos50 = [...gov.govs].sort((a, b) => Math.abs((lider(a)?.pct ?? 0) - 50) - Math.abs((lider(b)?.pct ?? 0) - 50)).slice(0, 3)
  .map((g) => ({ uf: g.uf.toUpperCase(), decisao: g.decisao, lider: curto(lider(g) as Cand), distancia_50_pp: r2(Math.abs((lider(g)?.pct ?? 0) - 50)) }));
const vaga2t = gov.govs.filter((g) => g.decisao === "segundo_turno" && g.terceiro && g.candidatos[1])
  .map((g) => ({ uf: g.uf.toUpperCase(), segundo: curto(g.candidatos[1] as Cand), terceiro: curto(g.terceiro as Cand), margem_pp: r2((g.candidatos[1]?.pct ?? 0) - (g.terceiro?.pct ?? 0)) }))
  .sort((a, b) => a.margem_pp - b.margem_pp).slice(0, 3);
const senApertadas = [...sen.saida.ufs].filter((u) => u.margem_2a_vaga_pp !== null).sort((a, b) => (a.margem_2a_vaga_pp ?? 0) - (b.margem_2a_vaga_pp ?? 0)).slice(0, 3);
const govXpres = gov.govs.map((g) => {
  const pl = presidente.ufs.find((u) => u.uf === g.uf.toUpperCase());
  const campoPres = campoDe(cl, null, pl?.partido_lider);
  const c = lider(g)?.campo ?? "indefinido";
  return { uf: g.uf.toUpperCase(), governador: lider(g)?.nome ?? "", campo_governador: c, presidenciavel_lider: pl?.lider ?? "", campo_presidenciavel: campoPres, campo_difere: c !== campoPres, bloco_difere: blocoDe(c) !== blocoDe(campoPres) };
});
const alertas = [...camara.ufs, ...assembleias.lista].flatMap((u) => u.e.alertas).concat(sen.ufs.flatMap((u) => u.e.alertas));
if (presidente.fonte === "soma_ufs") alertas.push(`placar nacional pela soma das UFs: ${presidente.nota_fonte}`);

const fatos = {
  comparecimento: presidente.comparecimento, pct_comparecimento: presidente.pct_comparecimento, pct_abstencao: presidente.pct_abstencao,
  brancos_nulos: presidente.brancos + presidente.nulos, pct_brancos_nulos: r2(presidente.pct_brancos + presidente.pct_nulos),
  exterior: presidente.exterior,
  governadores_mais_perto_de_50: proximos50,
  governadores_vaga_2t_mais_apertada: vaga2t,
  senado_2a_vaga_mais_apertada: senApertadas.map((u) => ({ uf: u.uf, segundo: u.eleitos[1], terceiro: u.terceiro, margem_pp: u.margem_2a_vaga_pp, margem_votos: u.margem_2a_vaga_votos })),
  governador_x_presidente: { ufs_campo_difere: govXpres.filter((x) => x.campo_difere).length, ufs_bloco_difere: govXpres.filter((x) => x.bloco_difere).length, nota: "governador eleito ou líder do 1º turno contra o presidenciável que liderou a UF", ufs: govXpres },
  vao_estadual: { nota: "candidatura ao governo (eleita ou no par do 2º turno) menos o finalista presidencial do mesmo bloco na mesma UF, em pontos dos válidos; mesma urna, cargos diferentes; não é transferência", lista: vao },
  linha_do_tempo: linha,
  alertas,
};

const final = {
  gerado_em: new Date().toISOString(),
  banco: DB,
  presidente: { ...presidente, finalistas: undefined },
  governadores: gov.saida,
  senado: sen.saida,
  camara: camara.saida,
  assembleias: assembleias.saida,
  fatos,
};

// ---------------------------------------------------------------- markdown
const p = presidente;
const md: string[] = [];
md.push(`# Apuração 2026: avaliação final`, "", `Gerado às ${brt(final.gerado_em)} (Brasília). Presidente com ${pct(p.pst)} das seções (${p.fonte === "tse" ? "arquivo nacional do TSE" : "soma dos arquivos das UFs"}).`, "");
md.push("## Presidente", "", tabela(["Candidatura", "Votos", "% válidos"], p.top5.map((c) => [`${c.nome} (${c.partido})`, int(c.votos), pct(c.pct)])), "");
md.push(p.segundo_turno ? `Segundo turno: **${p.par_2t.map((c) => c.nome).join(" x ")}**, diferença de ${pp(p.diferenca_pp)} (${int(p.diferenca_votos)} votos).` : `Eleito no 1º turno: **${p.par_2t[0]?.nome ?? ""}**.`, "");
for (const [nome, ufs] of Object.entries(p.venceu_em)) md.push(`- ${nome} venceu em ${ufs.length} UFs: ${ufs.join(", ")}.`);
md.push(`- Comparecimento ${pct(p.pct_comparecimento)} (${int(p.comparecimento)}); abstenção ${pct(p.pct_abstencao)}; brancos ${pct(p.pct_brancos)} e nulos ${pct(p.pct_nulos)} dos votos.`);
if (p.exterior) md.push(`- Exterior (${pct(p.exterior.pst)} apurado): ${p.exterior.lider} ${pct(p.exterior.pct_lider)} x ${p.exterior.segundo} ${pct(p.exterior.pct_segundo)}.`);
md.push("");
const c = camara.saida;
md.push("## Câmara dos Deputados", "", `${int(c.eleitos_total)} de ${int(c.vagas_total)} cadeiras. ${c.n_ufs_tse} UFs com eleitos marcados pelo TSE e ${c.n_ufs_provisorio} pela alocação provisória (${c.ufs_provisorias.join(", ")}).`, "");
md.push(tabelaCampos([{ nome: "Cadeiras", dados: c.por_campo }, { nome: "Votos", dados: c.votos_por_campo }], true), "", tabelaBlocos(c.blocos), "");
md.push(`Conferência nas UFs finais: a alocação provisória reproduz os partidos do TSE em ${c.conferencia_provisorio_x_tse.filter((x) => x.partidos_iguais).length} de ${c.conferencia_provisorio_x_tse.length} UFs e os nomes em ${c.conferencia_provisorio_x_tse.filter((x) => x.mesmos_nomes).length}.`, "");
const s = sen.saida.senado_2027;
md.push("## Senado de 2027", "", `${s.total} cadeiras: ${s.continuam} eleitas em 2022 e ${s.novos} em 2026 (${sen.saida.n_ufs_tse} UFs com marca do TSE, ${sen.saida.n_ufs_provisorio} provisórias).`, "");
md.push(tabelaCampos([{ nome: "Ficam (2022)", dados: s.continuam_por_campo }, { nome: "Eleitos 2026", dados: s.novos_por_campo }, { nome: "Senado 2027", dados: s.por_campo }], false), "", tabelaBlocos(s.por_bloco), "", sen.saida.comparacao_2023.nota + ".", "");
md.push("## Assembleias", "", tabela(["UF", "Fonte", "Vagas", ...Object.values(ROTULO)], assembleias.saida.map((a) => [a.uf, a.fonte === "tse" ? "TSE" : "provisória", int(a.vagas), ...Object.keys(ROTULO).map((k) => int(a.por_campo[k as keyof typeof ROTULO]))])), "");
md.push(...assembleias.saida.map((a) => `- ${a.uf}, mais votados: ${a.mais_votados.map((m) => `${m.nome} (${m.partido}) ${int(m.votos)}`).join("; ")}.`), "");
const g = gov.saida;
md.push("## Governadores", "", `${g.n_eleitos_1t} eleitos no 1º turno e ${g.n_segundo_turno} estados com 2º turno (${g.n_tse} pela marca do TSE, ${g.n_provisorio} provisórios).`, "");
md.push(tabelaCampos([{ nome: "Eleitos no 1º turno", dados: g.eleitos_1t_por_campo }, { nome: "Candidaturas no 2º turno", dados: g.segundo_turno_candidatos_por_campo }], false), "");
md.push(tabela(["UF", "Situação", "Candidaturas"], g.ufs.map((u) => [u.uf, u.decisao === "eleito" ? `eleito (${u.fonte === "tse" ? "TSE" : "provisório"})` : "2º turno", u.candidatos.map(cand).join(" x ")])), "");
md.push("## Fatos da noite", "");
md.push(`- Governo, mais perto dos 50%: ${proximos50.map((x) => `${x.uf} ${x.lider.nome} ${pct(x.lider.pct)}`).join("; ")}.`);
md.push(`- Governo, vaga no 2º turno mais apertada: ${vaga2t.map((x) => `${x.uf} ${x.segundo.nome} ${pct(x.segundo.pct)} x ${x.terceiro.nome} ${pct(x.terceiro.pct)}`).join("; ")}.`);
md.push(`- Senado, 2ª vaga mais apertada: ${senApertadas.map((u) => `${u.uf} ${u.eleitos[1]?.nome ?? ""} x ${u.terceiro?.nome ?? ""} (${pp(u.margem_2a_vaga_pp ?? 0)}, ${int(u.margem_2a_vaga_votos ?? 0)} votos)`).join("; ")}.`);
md.push(`- Governador de campo diferente do presidenciável que liderou a UF: ${fatos.governador_x_presidente.ufs_campo_difere} UFs (de bloco diferente: ${fatos.governador_x_presidente.ufs_bloco_difere}).`, "");
md.push("### Vão estadual", "", tabela(["UF", "Governo", "%", "Presidente", "%", "Vão (pp)"], vao.map((v) => [v.uf.toUpperCase(), `${v.governador} (${v.partido})`, pct(v.pct_governador), v.presidenciavel, pct(v.pct_presidenciavel), v.vao_pp.toLocaleString("pt-BR")])), "");
md.push("### Auditoria da noite", "");
md.push(`- Primeira totalização nacional: ${brt(linha.primeira_totalizacao)}; primeiro arquivo nacional com seções gerado às ${brt(linha.primeiro_arquivo_com_secoes)}.`);
md.push(`- Arquivo nacional parado: ${linha.travamentos_nacional.map((l) => `${brt(l.de)} a ${brt(l.ate)} (${int(l.minutos)} min)`).join("; ") || "nenhum intervalo acima de 10 min"}.`);
md.push(`- Arquivos das UFs parados: ${linha.travamentos_ufs.map((l) => `${brt(l.de)} a ${brt(l.ate)} (${int(l.minutos)} min)`).join("; ") || "nenhum intervalo acima de 10 min"}.`);
md.push(`- UFs a 100% no presidente: ${linha.uf_100.map((u) => `${u.uf.toUpperCase()} ${brt(u.gerado_em ?? u.capturado_em).slice(0, 5)}`).join(", ")}.`);
md.push(`- ${int(linha.snapshots)} versões gravadas, ${int(linha.fetches)} requisições, banco com ${(linha.bytes_banco / 1e9).toLocaleString("pt-BR", { maximumFractionDigits: 2 })} GB.`);
if (alertas.length > 0) md.push("", "### Alertas", "", ...alertas.map((a) => `- ${a}`));
const texto = `${md.join("\n")}\n`;

mkdirSync(SAIDA, { recursive: true });
writeFileSync(join(SAIDA, "final.json"), `${JSON.stringify(final, null, 1)}\n`);
writeFileSync(join(SAIDA, "final.md"), texto);
console.log(texto);
