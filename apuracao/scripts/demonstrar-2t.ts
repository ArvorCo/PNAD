// Uso: bun run scripts/demonstrar-2t.ts [--db1t data/apuracao.sqlite] [--secoes data/secoes_2026.sqlite]
//        [--referencia data/referencia_1t.json] [--dossie ../analysis/apuracao_2026/dados/linha_do_tempo.json]
//        [--saida ../analysis/apuracao_2t_2026] [--limiares 5,7] [--contraprova 30] [--sem-regra-anterior]
//
// Demonstração reproduzível, com dados reais do 1º turno, de que os alertas do 2º turno funcionam.
// (a) A noite de 04/10 relida pelo coletor com o motor novo ligado (scripts/demonstrar_2t/replay.ts):
//     pausas com APURACAO_PAUSA_MIN em cada limiar, viradas, fechamentos de UF e régua do 1º turno,
//     comparados com a régua publicada no dossiê; uma rodada emula a regra de versão anterior.
// (b) Conferência da totalização paralela com BUs oficiais reais de SP, AC e exterior
//     (scripts/demonstrar_2t/bu-real.ts), pela ponte real e pela rota /api/anomalias do servidor.
// Grava demonstracao_1t.md e demonstracao_1t.json em --saida. Os bancos de origem são abertos só
// para leitura; os bancos da demonstração ficam em data/demo-*.sqlite (fora do git). Cerca de 2 min.
import type { Database } from "bun:sqlite";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, relative, resolve } from "node:path";
import { parseArgs } from "node:util";
import { PAUSAS_PADRAO } from "../src/collector/pausas.ts";
import { abrirLeitura } from "../src/db/abrir.ts";
import type { LinhaMunicipio } from "../src/db/linhas.ts";
import { titulo } from "../src/server/abr.ts";
import { carregarReferencia } from "../src/turno2/referencia.ts";
import {
  coerenciaViradas, coberturaDaRegua, conferirAbstencao, contagemPorTipo, eventos, exemploRecuperada, explicarAtrasos, idadeMedianaUfs, lerReguaDossie,
  pausasDetectadas, regraVersao, secoesEm,
} from "./demonstrar_2t/analise.ts";
import type { IdadeUfs } from "./demonstrar_2t/analise.ts";
import { compararComOficial, conferirPelaPonte, lerSecoesReais, montarCasos, origemQr, rotulos } from "./demonstrar_2t/bu-real.ts";
import { markdown } from "./demonstrar_2t/relatorio.ts";
import type { CasoRelatorio, Demonstracao, Rodada } from "./demonstrar_2t/relatorio.ts";
import { ELE_1T, isoBrt, lerFonte1t, replayNoite } from "./demonstrar_2t/replay.ts";
import type { ResumoReplay } from "./demonstrar_2t/replay.ts";

const RAIZ = resolve(import.meta.dir, "..");
const REPO = resolve(RAIZ, "..");
const TIPOS_PAUSA = [
  "pausa_nacional_inicio", "pausa_nacional_longa", "pausa_nacional_fim", "pausa_uf_inicio", "pausa_uf_fim", "pausa_geral_inicio", "pausa_geral_longa", "pausa_geral_fim",
  "soma_ufs_adiante",
] as const;
/** Instante fixo da conferência de BU: 21:00 de 04/10 em Brasília (não houve envio real no 1º turno). */
const AGORA_BU = "2026-10-05T00:00:00.000Z";
const RECEBIDO_BU = "2026-10-04T23:50:00.000Z";

const { values: a } = parseArgs({
  args: Bun.argv.slice(2),
  options: {
    db1t: { type: "string", default: join(RAIZ, "data/apuracao.sqlite") },
    secoes: { type: "string", default: join(RAIZ, "data/secoes_2026.sqlite") },
    referencia: { type: "string", default: join(RAIZ, "data/referencia_1t.json") },
    dossie: { type: "string", default: join(REPO, "analysis/apuracao_2026/dados/linha_do_tempo.json") },
    saida: { type: "string", default: join(REPO, "analysis/apuracao_2t_2026") },
    limiares: { type: "string", default: "5,7" },
    contraprova: { type: "string", default: "30" },
    "sem-regra-anterior": { type: "boolean", default: false },
  },
});

const inicio = performance.now();
const caminho = (p: string): string => relative(REPO, resolve(p));
const log = (o: Record<string, unknown>): void => console.log(JSON.stringify({ t: "demonstracao", ...o }));
const db1tPath = resolve(a.db1t ?? "");
const refPath = resolve(a.referencia ?? "");
const ref = carregarReferencia(refPath);
if (ref === null) throw new Error(`régua do 1º turno ausente: ${refPath}`);
const regua = lerReguaDossie(resolve(a.dossie ?? ""));
const limiares = (a.limiares ?? "5,7").split(",").map(Number).filter((x) => Number.isFinite(x) && x >= 1);
const limiarPadrao = limiares.includes(PAUSAS_PADRAO.limiarNacionalMin) ? PAUSAS_PADRAO.limiarNacionalMin : (limiares[0] ?? PAUSAS_PADRAO.limiarNacionalMin);
const contraprovaMin = Number(a.contraprova ?? "30");

// ---------------------------------------------------------------- (a) replay
const db1t = abrirLeitura(db1tPath);
const fonte = lerFonte1t(db1t);
log({ ev: "fonte", leituras: fonte.leituras.length, ms: Math.round(performance.now() - inicio) });

interface Plano {
  rotulo: string;
  regra: "atual" | "anterior";
  limiar: number;
  banco: string;
  contraprova: number;
}
const planos: Plano[] = limiares.map((l) => ({
  rotulo: `regra atual, limiar ${l} min`, regra: "atual", limiar: l, banco: join(RAIZ, `data/demo-replay-1t-l${l}.sqlite`), contraprova: l === limiarPadrao ? contraprovaMin : 0,
}));
if (!a["sem-regra-anterior"]) {
  planos.push({ rotulo: `regra de versão anterior, limiar ${limiarPadrao} min`, regra: "anterior", limiar: limiarPadrao, banco: join(RAIZ, `data/demo-replay-1t-anterior-l${limiarPadrao}.sqlite`), contraprova: 0 });
}

const rodadas: Rodada[] = [];
const resumos = new Map<string, ResumoReplay>();
for (const pl of planos) {
  const r = await replayNoite({ db1t, fonte, saida: pl.banco, referencia: refPath, limiarMin: pl.limiar, regra: pl.regra, contraprovaAtrasoMin: pl.contraprova });
  resumos.set(pl.rotulo, r);
  const db = abrirLeitura(pl.banco);
  try {
    const pausas = pausasDetectadas(db, regua);
    const contagem = contagemPorTipo(db);
    rodadas.push({
      rotulo: pl.rotulo, regra: pl.regra, limiar_min: r.limiar_min, limiar_uf_min: r.limiar_uf_min, banco: caminho(pl.banco), ms: r.ms, avaliacoes: r.avaliacoes,
      versoes_presidente: r.versoes_presidente, pausas, cobertura: coberturaDaRegua(pausas, regua), eventos_pausa: eventos(db, TIPOS_PAUSA), contagem,
      atraso_degrau: contagem.uf_atrasada_1t ?? 0, atraso_interpolado: r.atraso_interpolado,
    });
  } finally {
    db.close();
  }
  log({ ev: "rodada", rotulo: pl.rotulo, ms: r.ms });
}

const rotuloPadrao = `regra atual, limiar ${limiarPadrao} min`;
const plPadrao = planos.find((x) => x.rotulo === rotuloPadrao);
const rodPadrao = rodadas.find((x) => x.rotulo === rotuloPadrao);
if (!plPadrao || !rodPadrao) throw new Error("rodada padrão ausente");
const dbP: Database = abrirLeitura(plPadrao.banco);
const viradas = eventos(dbP, ["virada"]);
const conclusao = new Map(regua.conclusao_ufs.map((c) => [c.uf.toLowerCase(), c]));
const fechamentos = eventos(dbP, ["uf_fechou"]).map((f) => {
  const c = conclusao.get(f.uf ?? "");
  const g = typeof f.detalhe.gerado_em === "string" ? Date.parse(f.detalhe.gerado_em) : Number.NaN;
  const dossie = c ? Date.parse(`${c.gerado_brt.replace(" ", "T")}.000-03:00`) : Number.NaN;
  return { ...f, dossie_gerado_brt: c?.gerado_brt ?? null, dif_s: Number.isFinite(g) && Number.isFinite(dossie) ? Math.round((g - dossie) / 1000) : null };
});
const tsNacional = dbP
  .query<{ ts: number | null }, [number]>(
    `SELECT t.ts FROM arquivo a JOIN snapshot s ON s.id = a.ultimo_snapshot_id JOIN totais t ON t.snapshot_id = s.id
     WHERE a.tipo = 'u' AND a.eleicao_cd = ? AND a.cargo_cd = 1 AND a.nivel = 'br'`,
  )
  .get(ELE_1T)?.ts ?? 0;
// trecho mais longo de parada nacional sem pausa do motor: onde medir o critério "o país publica"
const descoberto = rodPadrao.cobertura
  .filter((c) => c.nivel === "nacional" && !c.mesmo_nivel)
  .flatMap((c) => c.descobertos)
  .filter((x) => Date.parse(x.ate) - Date.parse(x.de) >= rodPadrao.limiar_min * 60_000)
  .sort((x, y) => Date.parse(y.ate) - Date.parse(y.de) - (Date.parse(x.ate) - Date.parse(x.de)))[0];
const idade: IdadeUfs[] = descoberto ? idadeMedianaUfs(dbP, descoberto.de, descoberto.ate) : [];
const contraprova = (resumos.get(rotuloPadrao)?.contraprova ?? []).map((e) => {
  const d = e.detalhe as { patamar_min: number; atraso_min: number };
  return { em_brt: isoBrt(e.em), uf: e.uf ?? "", patamar_min: d.patamar_min, atraso_min: d.atraso_min };
});
const chaveRegua = (x: Rodada): string =>
  JSON.stringify(["virada", "uf_fechou", "uf_atrasada_1t", "abstencao_atipica_mun", "abstencao_atipica_uf"].map((t) => x.contagem[t] ?? 0));
const atuais = rodadas.filter((x) => x.regra === "atual");
const replay: Demonstracao["replay"] = {
  janela: { inicio: new Date(fonte.inicioMs).toISOString(), fim: new Date(fonte.fimMs).toISOString() },
  leituras: { total: fonte.leituras.length, por_classe: fonte.contagem },
  arquivos: fonte.arquivos,
  rodadas,
  padrao: rotuloPadrao,
  regua_dossie: { ...regua, arquivo: caminho(regua.arquivo) },
  exemplo_versao: exemploRecuperada(db1t),
  ts_nacional: tsNacional,
  viradas,
  coerencia_viradas: coerenciaViradas(dbP, viradas),
  fechamentos,
  regua: {
    atrasos: explicarAtrasos(db1t, ref, eventos(dbP, ["uf_atrasada_1t"])),
    contraprova: { atraso_min: contraprovaMin, eventos: contraprova },
    abstencao: conferirAbstencao(dbP, ref),
  },
  regra_versao: regraVersao(db1t, dbP),
  idade_ufs_19h26: idade,
  idade_trecho: descoberto ?? null,
  idade_secoes: descoberto ? secoesEm(dbP, descoberto.ate) : null,
  iguais_entre_rodadas: atuais.every((x) => chaveRegua(x) === chaveRegua(rodPadrao)),
};
dbP.close();
log({ ev: "analise", ms: Math.round(performance.now() - inicio) });

// ---------------------------------------------------------------- (b) BU real
const dbSec = abrirLeitura(resolve(a.secoes ?? ""));
const publicadas = lerSecoesReais(dbSec, ["sp", "ac", "zz"]);
const semAux = lerSecoesReais(dbSec, ["ac"], true)[0];
dbSec.close();
if (publicadas.length === 0 || semAux === undefined) throw new Error("seções reais com BU não encontradas");
const cds = [...new Set([...publicadas, semAux].map((s) => s.s.mun))];
const municipios = db1t
  .query<LinhaMunicipio, []>(`SELECT cd, uf, ibge, nome, capital, eleitores, origem FROM municipio WHERE cd IN (${cds.map((c) => `'${c}'`).join(", ")})`)
  .all();
db1t.close();
const nomeMun = new Map(municipios.map((m) => [`${m.uf}|${m.cd}`, titulo(m.nome)]));
for (const s of [...publicadas, semAux]) s.municipio = nomeMun.get(`${s.s.uf}|${s.s.mun}`) ?? null;
const casos = montarCasos(publicadas, semAux, RECEBIDO_BU);
const ponte = await conferirPelaPonte(casos, { db: join(RAIZ, "data/demo-paralela-1t.sqlite"), municipios, agora: AGORA_BU });
const casosRel: CasoRelatorio[] = casos.map((c) => {
  const dif = c.tipo === "aux_nao_publicado" ? null : compararComOficial(c.reg, c.secao);
  return {
    id: c.id, tipo: c.tipo, uf: c.secao.s.uf, municipio: c.secao.municipio, mun: c.secao.s.mun, zona: c.secao.s.zona, secao: c.secao.s.secao, nota: c.nota, esperado: c.esperado,
    direta: dif === null ? null : { situacao: dif.length === 0 ? "igual" : "divergente", diferencas: dif, rotulos: rotulos(dif) },
  };
});
const evDiv = ponte.anomalias
  .filter((x) => x.tipo === "divergencia_paralela")
  .map((x) => ({ bu_id: Number((x.detalhe as { bu_id?: number }).bu_id), tipo: x.tipo, severidade: x.severidade, texto: x.texto, detalhe: x.detalhe }))
  .sort((x, y) => x.bu_id - y.bu_id);
const conferida = ponte.anomalias.find((x) => x.tipo === "paralela_conferida");
const bu: Demonstracao["bu"] = {
  secoes: [...publicadas, semAux].map((s) => ({
    uf: s.s.uf, municipio: s.municipio, mun: s.s.mun, zona: s.s.zona, secao: s.s.secao, arquivo: s.buNome, sha256: s.buSha256, origem: origemQr(s.boletim),
    uso: s === semAux ? "aux.json não publicado (o TSE falso responde 404)" : "igual, voto movido e comparecimento + 1", banco: s.banco,
  })),
  casos: casosRel,
  ponte: {
    banco: caminho(ponte.db), antes: ponte.antes, depois: ponte.depois, paralela: ponte.paralela, requisicoes_tse: ponte.requisicoes_tse, eventos: evDiv,
    conferida: conferida ? { texto: conferida.texto, detalhe: conferida.detalhe } : null,
  },
};

// ---------------------------------------------------------------- saída
const demo: Demonstracao = {
  gerado_em: new Date().toISOString(),
  duracao_s: Math.round((performance.now() - inicio) / 100) / 10,
  comando: "bun run scripts/demonstrar-2t.ts",
  fontes: {
    "banco do 1º turno": caminho(db1tPath),
    "BUs por seção do 1º turno": caminho(a.secoes ?? ""),
    "régua do 1º turno": caminho(refPath),
    "régua de pausas do dossiê": caminho(regua.arquivo),
  },
  replay,
  bu,
};
const saida = resolve(a.saida ?? "");
mkdirSync(saida, { recursive: true });
writeFileSync(join(saida, "demonstracao_1t.json"), `${JSON.stringify(demo, null, 1)}\n`);
writeFileSync(join(saida, "demonstracao_1t.md"), markdown(demo));
log({ ev: "fim", s: demo.duracao_s, saida: caminho(saida) });
