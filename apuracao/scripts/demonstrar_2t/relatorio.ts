// Relatório em Markdown da demonstração (../analysis/apuracao_2t_2026/demonstracao_1t.md).
// Só formata: todo número vem do objeto montado por scripts/demonstrar-2t.ts. Sem travessão.
import type { Diferenca, Situacao } from "../../src/paralela/conferir.ts";
import type {
  AtrasoExplicado, ConferenciaAbstencao, CoberturaMarco, EventoLido, ExemploVersao, IdadeUfs, LiderUf, PausaDetectada, RegraVersao, ReguaDossie,
} from "./analise.ts";
import type { ConferenciaBanco, ConferenciaLida, TipoCaso } from "./bu-real.ts";
import type { AtrasoInterpolado } from "./replay.ts";
import { isoBrt } from "./replay.ts";

export interface Rodada {
  rotulo: string;
  regra: "atual" | "anterior";
  limiar_min: number;
  limiar_uf_min: number;
  banco: string;
  ms: number;
  avaliacoes: number;
  versoes_presidente: { aceitas: number; regressivas: number };
  pausas: PausaDetectada[];
  cobertura: CoberturaMarco[];
  eventos_pausa: EventoLido[];
  contagem: Record<string, number>;
  atraso_degrau: number;
  atraso_interpolado: AtrasoInterpolado[];
}

export interface CasoRelatorio {
  id: number;
  tipo: TipoCaso;
  uf: string;
  municipio: string | null;
  mun: string;
  zona: number;
  secao: number;
  nota: string;
  esperado: Situacao;
  /** comparação direta; null no caso sem aux.json, que não tem BU oficial para comparar */
  direta: { situacao: Situacao; diferencas: Diferenca[]; rotulos: string[] } | null;
}

export interface Demonstracao {
  gerado_em: string;
  duracao_s: number;
  comando: string;
  fontes: Record<string, string>;
  replay: {
    janela: { inicio: string; fim: string };
    leituras: { total: number; por_classe: Record<string, number> };
    arquivos: { u: number; ab: number };
    rodadas: Rodada[];
    padrao: string;
    regua_dossie: ReguaDossie;
    exemplo_versao: ExemploVersao | null;
    ts_nacional: number;
    viradas: EventoLido[];
    coerencia_viradas: LiderUf[];
    fechamentos: (EventoLido & { dossie_gerado_brt: string | null; dif_s: number | null })[];
    regua: { atrasos: AtrasoExplicado[]; contraprova: { atraso_min: number; eventos: { em_brt: string; uf: string; patamar_min: number; atraso_min: number }[] }; abstencao: ConferenciaAbstencao };
    regra_versao: RegraVersao;
    idade_ufs_19h26: IdadeUfs[];
    idade_trecho: { de: string; ate: string } | null;
    /** seções no fim do trecho descoberto: arquivo nacional e soma das UFs */
    idade_secoes: { nacional: number; soma_ufs: number } | null;
    iguais_entre_rodadas: boolean;
  };
  bu: {
    secoes: { uf: string; municipio: string | null; mun: string; zona: number; secao: number; arquivo: string; sha256: string; origem: string; uso: string; banco: ConferenciaBanco }[];
    casos: CasoRelatorio[];
    ponte: {
      banco: string;
      antes: ConferenciaLida[];
      depois: ConferenciaLida[];
      paralela: { conferencia: Record<string, number>; recebidos: Record<string, number>; erro: string | null };
      requisicoes_tse: { url: string; status: number }[];
      eventos: { bu_id: number; tipo: string; severidade: string; texto: string; detalhe: unknown }[];
      conferida: { texto: string; detalhe: unknown } | null;
    };
  };
}

const n = (x: number | null | undefined): string => (x === null || x === undefined ? "" : x.toLocaleString("pt-BR"));
const d1 = (x: number | null | undefined): string => (x === null || x === undefined ? "" : x.toLocaleString("pt-BR", { minimumFractionDigits: 1, maximumFractionDigits: 1 }));
const hora = (brt: string | null | undefined): string => (brt ? brt.slice(11, 19) : "");
const dia = (brt: string | null | undefined): string => (brt ? `${brt.slice(8, 10)}/${brt.slice(5, 7)} ${brt.slice(11, 19)}` : "");
const linha = (c: readonly (string | number)[]): string => `| ${c.join(" | ")} |`;
const tabela = (cab: readonly string[], linhas: readonly (readonly (string | number)[])[]): string =>
  [linha(cab), linha(cab.map(() => "---")), ...linhas.map(linha)].join("\n");
const nivelTxt: Readonly<Record<string, string>> = { nacional: "nacional", geral: "geral", uf: "UF" };
const seg = (s: number): string => `${s > 0 ? "+" : ""}${s} s`;
const msBrt = (brt: string): number => Date.parse(`${brt.replace(" ", "T")}.000-03:00`);
const ms = (iso: string | null): number => (iso === null ? Number.NaN : Date.parse(iso));
const sobrepoe = (a0: number, a1: number, b0: number, b1: number): boolean => Math.min(a1, b1) > Math.max(a0, b0);
const plural = (k: number, um: string, varios: string): string => `${k} ${k === 1 ? um : varios}`;
const lista = (l: readonly string[]): string => (l.length <= 1 ? (l[0] ?? "") : `${l.slice(0, -1).join(", ")} e ${l.at(-1) ?? ""}`);
const faixa = (l: readonly number[], f: (x: number) => string = d1): string => {
  if (l.length === 0) return "";
  const a = Math.min(...l);
  const b = Math.max(...l);
  return a === b ? f(a) : `${f(a)} a ${f(b)}`;
};

function tabelaPausas(p: readonly PausaDetectada[]): string {
  return tabela(
    ["Nível", "UF", "De", "Até", "Min", "st antes → depois", "Detectada", "Na régua do dossiê (Δ início, Δ fim)"],
    p.map((x) => [
      nivelTxt[x.nivel] ?? x.nivel, x.uf?.toUpperCase() ?? "", dia(isoBrt(x.de)), dia(isoBrt(x.ate)), d1(x.minutos), `${n(x.st_antes)} → ${n(x.st_depois)}`,
      hora(isoBrt(x.detectado_em)),
      x.regua === null ? "não (lacuna abaixo de 8 min)" : `${x.regua.fonte} ${hora(isoBrt(x.regua.de))}–${hora(isoBrt(x.regua.ate))} (${seg(x.regua.dif_de_s)}, ${seg(x.regua.dif_ate_s)})`,
    ]),
  );
}

function rotuloDif(d: Diferenca): string {
  return `${d.campo}${d.chave === null ? "" : ` ${d.chave}`}: paralela ${String(d.paralela)}, TSE ${String(d.tse)}`;
}

export function markdown(d: Demonstracao): string {
  const r = d.replay;
  const rod = (rotulo: string): Rodada | undefined => r.rodadas.find((x) => x.rotulo === rotulo);
  const padrao = rod(r.padrao) ?? r.rodadas[0];
  if (!padrao) throw new Error("demonstração sem rodada");
  const atuais = r.rodadas.filter((x) => x.regra === "atual");
  const anterior = r.rodadas.find((x) => x.regra === "anterior");
  const l5 = atuais.find((x) => x.limiar_min === 5);
  const l7 = atuais.find((x) => x.limiar_min === 7);
  const mesma = (x: PausaDetectada, y: PausaDetectada): boolean => x.nivel === y.nivel && x.uf === y.uf && sobrepoe(ms(x.de), ms(x.ate ?? x.de), ms(y.de), ms(y.ate ?? y.de));
  const so5 = l5 && l7 ? l5.pausas.filter((x) => !l7.pausas.some((y) => mesma(x, y))) : [];
  const nac = (x: Rodada): PausaDetectada[] => x.pausas.filter((p) => p.nivel === "nacional");
  const out: string[] = [];
  const p = (s = ""): void => {
    out.push(s);
  };

  p("# Demonstração do motor do 2º turno com a noite real do 1º turno");
  p();
  p(`Gerado por \`${d.comando}\` em ${dia(isoBrt(d.gerado_em))} (horário de Brasília), em ${d1(d.duracao_s)} s. Arquivo irmão com todos os números: \`demonstracao_1t.json\`.`);
  p();
  p("Fontes, todas abertas só para leitura:");
  p();
  for (const [k, v] of Object.entries(d.fontes)) p(`- ${k}: \`${v}\``);
  p();
  p("Bancos gerados pela demonstração (esquema real, recriados a cada execução, fora do git):");
  p();
  for (const x of r.rodadas) p(`- ${x.rotulo}: \`${x.banco}\``);
  p(`- conferência de BU: \`${d.bu.ponte.banco}\``);
  p();

  // ------------------------------------------------------------ resumo
  p("## Resumo");
  p();
  if (l5 && l7) {
    p(`- **Pausas.** Com o limiar padrão de ${l5.limiar_min} min o motor abre ${l5.pausas.length} pausas; com ${l7.limiar_min} min, ${l7.pausas.length}. As ${so5.length} a mais do limiar de ${l5.limiar_min} min (${plural(so5.filter((x) => x.nivel === "nacional").length, "nacional", "nacionais")} e ${plural(so5.filter((x) => x.nivel === "geral").length, "geral", "gerais")}) ${so5.every((x) => x.regua === null) ? "são todas" : "não são todas"} lacunas abaixo dos ${d1(r.regua_dossie.limiar_min)} min da régua do dossiê. Com ${l7.limiar_min} min, a única pausa de nível nacional é a parada de ${hora(isoBrt(nac(l7)[0]?.de ?? null))} a ${hora(isoBrt(nac(l7)[0]?.ate ?? null))}; a pausa geral de 19:32 e o travamento das 18:00 aparecem como pausas gerais (nenhum arquivo de presidente com versão nova).`);
  }
  p(`- **Viradas e fechamentos.** ${r.viradas.length} viradas de liderança (${r.viradas.map((v) => `${v.uf?.toUpperCase() ?? ""} às ${hora(v.em_brt)}`).join(", ")}) e ${r.fechamentos.length} fechamentos de UF; líder inicial mais viradas termina no líder final em ${r.coerencia_viradas.filter((x) => x.coerente).length} de ${r.coerencia_viradas.length} arquivos de UF.`);
  p(`- **Régua do 1º turno.** \`uf_atrasada_1t\`: ${padrao.atraso_degrau} alertas (a régua lida por interpolação, como estava, daria ${padrao.atraso_interpolado.length}); \`abstencao_atipica_mun\`: ${padrao.contagem.abstencao_atipica_mun ?? 0}; \`abstencao_atipica_uf\`: ${padrao.contagem.abstencao_atipica_uf ?? 0}. A contraprova com a mesma noite atrasada em ${r.regua.contraprova.atraso_min} min dispara ${r.regua.contraprova.eventos.length} alertas de atraso.`);
  const comparados = d.bu.casos.filter((c) => c.direta !== null);
  const casosOk = comparados.filter((c) => c.direta?.situacao === c.esperado).length;
  const ponteOk = d.bu.ponte.depois.filter((x) => d.bu.casos.find((c) => c.id === x.bu_id)?.esperado === x.situacao).length;
  p(`- **Conferência de BU real.** ${d.bu.secoes.length} BUs oficiais decodificados; ${casosOk} de ${comparados.length} comparações diretas e ${ponteOk} de ${d.bu.ponte.depois.length} conferências pela ponte com a situação esperada: ${n(d.bu.ponte.paralela.conferencia.iguais)} iguais, ${n(d.bu.ponte.paralela.conferencia.divergentes)} divergentes e ${n(d.bu.ponte.paralela.conferencia.tse_ainda_nao_publicou)} à espera do TSE.`);
  p(`- **Três defeitos do motor apareceram no replay e foram corrigidos** (seção "Defeitos encontrados"): a regra de versão regressiva descartava ${n(r.regra_versao.recuperadas)} versões novas de presidente por causa do idg; a régua de atraso, lida por interpolação, acusava atraso de UF que estava no mesmo ponto do 1º turno na mesma hora; e o texto de fechamento usava carimbos de totalização fora da janela da geração (o exterior "fechava" às 09:19 do dia seguinte).`);
  p();

  // ------------------------------------------------------------ (a)
  p("## (a) A noite de 04/10 relida pelo coletor do 2º turno");
  p();
  p("### Como foi feito");
  p();
  p(`Cada leitura que o coletor do 1º turno gravou na tabela \`fetch\` para os ${r.arquivos.u} arquivos \`-u\` de presidente (Brasil, 27 UFs e exterior) e para os ${r.arquivos.ab} arquivos \`-ab\` das UFs volta a passar por \`processar()\`, o pipeline do coletor, na ordem em que a resposta chegou: ${n(r.leituras.total)} leituras (${Object.entries(r.leituras.por_classe).map(([k, v]) => `${k} ${n(v)}`).join(", ")}), de ${dia(isoBrt(r.janela.inicio))} a ${dia(isoBrt(r.janela.fim))}. Corpo novo e corpo repetido voltam com o blob original, para o próprio coletor decidir entre versão nova, cópia regressiva e corpo igual. Do \`-ab\` só entram as leituras com corpo: a régua de abstenção lê o conteúdo, e o frescor que o motor exige é o dos arquivos de presidente.`);
  p();
  p(`\`instalarTurno2\` liga o motor exatamente como no ar (detector de pausas, viradas e fechamentos gravados pelo coletor, régua do 1º turno). A configuração de turno 1 (\`APURACAO_ELEICOES=6257\`) põe a eleição 6257 e o relógio da apuração em 17:00 de 04/10 (\`T0_1T_MS\`); \`src/turno2/comum.ts\` não foi tocado. A avaliação de 30 s roda pelo Agendador com a fila vazia: o replay nunca acessa a rede. Foram ${n(padrao.avaliacoes)} avaliações por rodada.`);
  p();

  p("### Pausas detectadas");
  p();
  for (const x of atuais) {
    p(`#### Limiar nacional de ${x.limiar_min} min (\`APURACAO_PAUSA_MIN=${x.limiar_min}\`, UF ${x.limiar_uf_min} min): ${x.pausas.length} pausas`);
    p();
    p(tabelaPausas(x.pausas));
    p();
  }
  if (l5 && l7) {
    p(`#### Diferença entre ${l5.limiar_min} e ${l7.limiar_min} min`);
    p();
    p(`Só com ${l5.limiar_min} min aparecem ${so5.length} pausas:`);
    p();
    p(tabelaPausas(so5));
    p();
    const nac5 = so5.filter((x) => x.nivel === "nacional");
    const curta = nac5.find((x) => x.minutos !== null && x.minutos < l5.limiar_min);
    const fimCurta = curta ? l5.eventos_pausa.find((e) => e.tipo === "pausa_nacional_fim" && e.detalhe.de === curta.de) : undefined;
    const gerais = [...l5.pausas, ...l7.pausas].filter((x) => x.nivel === "geral" && x.regua !== null);
    const maxDif = Math.max(0, ...gerais.flatMap((x) => (x.regua ? [Math.abs(x.regua.dif_de_s), Math.abs(x.regua.dif_ate_s)] : [])));
    const real = nac(l7)[0];
    p(`As ${nac5.length} nacionais de ${hora(isoBrt(nac5[0]?.de ?? null))} a ${hora(isoBrt(nac5.at(-1)?.ate ?? null))} têm de ${faixa(nac5.map((x) => x.minutos ?? 0))} min: é a cadência do arquivo nacional naquele trecho, e nenhuma chega aos ${d1(r.regua_dossie.limiar_min)} min da régua do dossiê.`);
    if (curta && fimCurta) {
      p();
      p(`A de ${hora(isoBrt(curta.de))} fecha com ${d1(curta.minutos)} min, menos que o próprio limiar: foi aberta às ${hora(isoBrt(curta.detectado_em))}, e a versão gerada às ${hora(isoBrt(curta.ate))} só chegou às ${hora(fimCurta.em_brt)}, ${d1(Math.round((ms(fimCurta.em) - ms(curta.ate)) / 6000) / 10)} min depois de gerada, além da folga de 1 min do detector.`);
    }
    p();
    const deslocadas = l5.pausas.filter((x) => x.nivel === "geral").flatMap((x) => {
      const y = l7.pausas.find((z) => mesma(x, z));
      return y && y.de !== x.de ? [{ x, y }] : [];
    });
    for (const { x, y } of deslocadas) {
      p();
      p(`A pausa geral de ${hora(isoBrt(x.de))} começa às ${hora(isoBrt(x.de))} com ${l5.limiar_min} min e às ${hora(isoBrt(y.de))} com ${l7.limiar_min} min: o início é a última versão de presidente conhecida quando a pausa abre (${hora(isoBrt(x.detectado_em))} e ${hora(isoBrt(y.detectado_em))}), e a versão gerada às ${hora(isoBrt(y.de))} só chegou entre as duas detecções. Chegou velha, por isso entra no histórico sem encerrar a pausa.`);
    }
    p();
    p(`${nac(l7).length === 1 && nac5.length > 0 ? "Confere com o relatório do motor" : "Não confere com o relatório do motor (pausas de cadência com 5 min, só a real com 7)"}: ${l5.limiar_min} min dá ${nac5.length} pausas nacionais de cadência e ${l7.limiar_min} min deixa ${nac(l7).length === 1 && real ? `só a parada nacional de ${hora(isoBrt(real.de))} a ${hora(isoBrt(real.ate))}` : `${nac(l7).length} nacionais`}. Nos dois limiares as pausas gerais ficam a até ${maxDif} s das lacunas correspondentes do dossiê.`);
    p();
  }

  p(`### Comparação com a régua do dossiê (limiar de ${padrao.limiar_min} min)`);
  p();
  p(`Régua: \`${r.regua_dossie.arquivo}\`, limiar de ${d1(r.regua_dossie.limiar_min)} min. Regra do dossiê: "${r.regua_dossie.regra}" As três primeiras linhas são os marcos citados no pedido.`);
  p();
  p(
    tabela(
      ["Intervalo", "Nível", "De", "Até", "Min", "Na régua", "Pausas do motor que tocam o intervalo", "Min cobertos", "Mesmo nível"],
      padrao.cobertura.map((c) => [
        c.nome, nivelTxt[c.nivel] ?? c.nivel, dia(c.de_brt), dia(c.ate_brt), d1(c.minutos), c.na_regua ? "sim" : "não",
        c.pausas.map((x) => `${nivelTxt[x.nivel] ?? x.nivel} ${hora(x.de_brt)}–${hora(x.ate_brt)}`).join("; ") || "nenhuma", d1(c.coberto_min), c.mesmo_nivel ? "sim" : "não",
      ]),
    ),
  );
  p();
  p("Leitura:");
  p();
  const iv = r.regua_dossie.intervalos;
  const marco = (nome: string): CoberturaMarco | undefined => padrao.cobertura.find((c) => c.nome === nome);
  const pausasTxt = (c: CoberturaMarco): string => lista(c.pausas.map((x) => `pausa ${nivelTxt[x.nivel] ?? x.nivel} de ${hora(x.de_brt)} a ${hora(x.ate_brt)}`)) || "nenhuma pausa";
  const c18 = marco("travamento nacional");
  if (c18) {
    const todas = iv.find((x) => x.fonte === "travamentos.todas_as_ufs_sem_versao_nova" && sobrepoe(ms(x.de), ms(x.ate), msBrt(c18.de_brt), msBrt(c18.ate_brt)));
    const volta = todas ? Math.round((msBrt(c18.ate_brt) - ms(todas.ate)) / 6000) / 10 : null;
    p(`- **Travamento nacional de ${hora(c18.de_brt)} a ${hora(c18.ate_brt)}.** ${todas ? `No mesmo trecho o dossiê registra nenhuma UF com versão nova de ${hora(isoBrt(todas.de))} a ${hora(isoBrt(todas.ate))}. ` : ""}O motor cobre com ${pausasTxt(c18)}. ${c18.mesmo_nivel ? "" : `Como ninguém publicava, a pausa é geral${volta === null ? "" : `; quando as UFs voltam, o nacional volta ${d1(volta)} min depois, abaixo do limiar`}. É a regra declarada do detector: nível nacional só quando as UFs publicam e andam.`}`);
  }
  const c1848 = marco("parada do arquivo nacional");
  if (c1848) {
    const em = (x: Rodada): string => {
      const q = x.pausas.find((y) => y.nivel === "nacional" && sobrepoe(ms(y.de), ms(y.ate ?? y.de), msBrt(c1848.de_brt), msBrt(c1848.ate_brt)));
      return q?.regua ? `${x.limiar_min} min: ${seg(q.regua.dif_de_s)} no início e ${seg(q.regua.dif_ate_s)} no fim` : `${x.limiar_min} min: não detectada como nacional`;
    };
    p(`- **Parada do arquivo nacional de ${hora(c1848.de_brt)} a ${hora(c1848.ate_brt)}.** Detectada como pausa nacional; diferença contra o dossiê com limiar de ${atuais.map(em).join("; ")}.`);
  }
  const cg = marco("pausa geral");
  if (cg) {
    const q = padrao.pausas.find((y) => y.nivel === "geral" && sobrepoe(ms(y.de), ms(y.ate ?? y.de), msBrt(cg.de_brt), msBrt(cg.ate_brt)));
    p(`- **Pausa geral de ${hora(cg.de_brt)} a ${hora(cg.ate_brt)}.** ${q ? `O motor abre a pausa geral de ${hora(isoBrt(q.de))} a ${hora(isoBrt(q.ate))}. ` : ""}O dossiê mede a lacuna de geração em todos os cargos e níveis; o motor mede só os arquivos de presidente (Brasil e UFs), por isso o início é a última versão de presidente antes da parada e o fim, a primeira depois dela.`);
  }
  const maiorDescoberto = (c: CoberturaMarco): number => Math.max(0, ...c.descobertos.map((x) => (ms(x.ate) - ms(x.de)) / 60_000));
  const abertos = padrao.cobertura.filter((c) => c.nivel === "nacional" && !c.mesmo_nivel && maiorDescoberto(c) >= padrao.limiar_min);
  for (const c of abertos) {
    const acima = r.idade_ufs_19h26.filter((x) => (x.mediana_min ?? 0) > 3);
    p(`- **Arquivo nacional sem versão nova de ${hora(c.de_brt)} a ${hora(c.ate_brt)} (${d1(c.minutos)} min).** É o limite do motor que o replay mostra: ele cobre ${d1(c.coberto_min)} min com ${pausasTxt(c)}, e nenhuma é nacional. Fora das pausas gerais as UFs publicavam com o nacional parado, mas o critério de "o país publica" exige idade mediana da última versão das UFs de até 3 min em toda a janela do limiar, e no trecho descoberto${r.idade_trecho ? `, de ${hora(isoBrt(r.idade_trecho.de))} a ${hora(isoBrt(r.idade_trecho.ate))},` : ""} ela passou de 3 min em ${acima.length} de ${r.idade_ufs_19h26.length} instantes (tabela abaixo, de 30 em 30 s, calculada como no detector). ${r.idade_secoes ? `No fim desse trecho a soma das UFs tinha ${n(r.idade_secoes.soma_ufs)} seções e o arquivo nacional ${n(r.idade_secoes.nacional)}, ${n(r.idade_secoes.soma_ufs - r.idade_secoes.nacional)} a menos. ` : ""}O único aviso do motor para isso é o \`soma_ufs_adiante\`, que dispara uma vez por episódio: ${padrao.contagem.soma_ufs_adiante ?? 0} nesta noite, às ${hora(padrao.eventos_pausa.find((e) => e.tipo === "soma_ufs_adiante")?.em_brt ?? null)}.`);
  }
  if (abertos.length > 0) {
    p();
    p(tabela(["Instante", "Idade mediana (min)", "UFs"], r.idade_ufs_19h26.map((x) => [hora(x.em_brt), d1(x.mediana_min), x.ufs])));
    p();
  }
  const cauda = padrao.pausas.filter((x) => x.nivel === "geral" && x.de >= "2026-10-05T02:00:00.000Z");
  if (cauda.length > 0) {
    const pend = cauda.map((x) => r.ts_nacional - (x.st_antes ?? 0));
    p(`- **Cauda depois das 23:00.** ${cauda.length} pausas gerais (${cauda.map((x) => `${hora(isoBrt(x.de))} a ${hora(isoBrt(x.ate))}`).join(", ")}); ${cauda.filter((x) => x.regua !== null).length} delas coincidem com lacunas "nenhuma UF com versão nova" do dossiê. São reais pela definição, com ${faixa(pend, n)} seções pendentes no país, e ${cauda.filter((x) => (x.minutos ?? 0) >= 15).length} viram \`error\` por passarem de 15 min numa hora em que só faltam seções isoladas.`);
  }
  p();

  p("### Viradas de liderança");
  p();
  p(tabela(["Hora", "UF", "De", "Para", "pst", "Texto do telão"], r.viradas.map((v) => [hora(v.em_brt), v.uf?.toUpperCase() ?? "", String(v.detalhe.de_nome ?? ""), String(v.detalhe.para_nome ?? ""), d1(Number(v.detalhe.pst)), v.texto])));
  p();
  const inc = r.coerencia_viradas.filter((x) => !x.coerente);
  p(`Conferência: em cada arquivo de UF, o líder da primeira versão com voto seguido das viradas gravadas termina no líder da última versão em ${r.coerencia_viradas.length - inc.length} de ${r.coerencia_viradas.length} UFs${inc.length > 0 ? ` (fora: ${inc.map((x) => x.uf.toUpperCase()).join(", ")})` : ""}. Nenhuma virada no arquivo nacional.`);
  p();

  p("### Fechamentos de UF, em ordem");
  p();
  p(
    tabela(
      ["#", "UF", "Gerada (BRT)", "Capturada (BRT)", "Totalização corrigida", "Dossiê: gerada", "Δ", "Texto do telão"],
      r.fechamentos.map((f, i) => [
        i + 1, f.uf?.toUpperCase() ?? "", hora(isoBrt(String(f.detalhe.gerado_em ?? ""))), hora(f.em_brt), dia(isoBrt(String(f.detalhe.totalizado_em ?? ""))),
        hora(f.dossie_gerado_brt), f.dif_s === null ? "" : seg(f.dif_s), f.texto,
      ]),
    ),
  );
  p();
  const dif = r.fechamentos.filter((f) => f.dif_s !== 0);
  p(`O instante de fechamento gravado pelo coletor é a geração da primeira versão com todas as seções; ele coincide com o \`conclusao_ufs\` do dossiê em ${r.fechamentos.length - dif.length} de ${r.fechamentos.length} UFs${dif.length > 0 ? ` (diferem: ${dif.map((f) => `${f.uf?.toUpperCase() ?? ""} ${f.dif_s === null ? "sem par" : seg(f.dif_s)}`).join(", ")})` : ""}.${(() => {
    const l = r.regua_dossie.conclusao_ufs.filter((c) => c.atraso_da_regra_do_coletor_min > 0);
    return l.length === 0 ? "" : ` O dossiê já registrava, na coluna \`atraso_da_regra_do_coletor_min\`, que a regra de versão anterior atrasava o fechamento de ${lista(l.map((c) => `${c.uf} (${d1(c.atraso_da_regra_do_coletor_min)} min)`))}; a regra atual elimina essa diferença.`;
  })()}`);
  p();

  p("### Régua do 1º turno: atraso e abstenção");
  p();
  p(tabela(["Alerta", "Rodada padrão"], [
    ["`uf_atrasada_1t` (atraso em degrau, regra atual)", padrao.atraso_degrau],
    ["`uf_atrasada_1t` pela interpolação (regra anterior, recalculada só para comparação)", padrao.atraso_interpolado.length],
    ["`abstencao_atipica_mun`", padrao.contagem.abstencao_atipica_mun ?? 0],
    ["`abstencao_atipica_uf`", padrao.contagem.abstencao_atipica_uf ?? 0],
    [`contraprova: a mesma noite com ${r.regua.contraprova.atraso_min} min de atraso`, r.regua.contraprova.eventos.length],
  ]));
  p();
  const ab = r.regua.abstencao;
  p(`**Abstenção: zero, e é o esperado.** A régua de abstenção é o resultado final do próprio 1º turno por município. No fim do replay ${n(ab.municipios_fechados)} municípios estão fechados (${n(ab.fechados_te_20mil)} com 20 mil eleitores ou mais), ${n(ab.com_referencia)} deles com par na régua, em ${ab.ufs} UFs, e a maior diferença de abstenção contra a régua é de ${ab.max_delta_pp.toLocaleString("pt-BR")} pp, do tamanho do arredondamento da régua, que grava a abstenção com duas casas decimais. Medida contra ela mesma, a noite não tem como acusar 5 pp no município nem 2 pp na UF.`);
  p();
  p(`**Atraso: ${padrao.atraso_degrau} alertas residuais, todos da construção da régua.** Pela definição o resultado também devia ser zero: no mesmo relógio, a UF tem o que o 1º turno tinha. Os ${padrao.atraso_degrau} restantes vêm de versões que a régua põe antes de elas existirem: o \`RelogioArquivo\` usado por \`scripts/referencia-1t.ts\` data cada versão pelo \`totalizado_em\` (corrigido do fuso quando cabe) e, quando esse carimbo fica para trás, pelo instante da versão anterior; nenhuma das duas datas é a publicação. A tabela mostra, para cada alerta, o ponto da curva que passou da UF e a versão do 1º turno com aquelas seções:`);
  p();
  p(
    tabela(
      ["Alerta (BRT)", "UF", "Patamar", "st da UF", "Régua: passou às", "st da régua", "Versão gerada às", "totalizado_em impresso", "Régua adiantada (min)"],
      r.regua.atrasos.map((a) => [
        hora(a.em_brt), a.uf.toUpperCase(), a.patamar_min, n(a.st_2t), a.regua_hhmm ?? "", n(a.regua_st), hora(a.versao_gerada_brt), hora(a.versao_totalizada_brt), d1(a.adiantamento_min),
      ]),
    ),
  );
  p();
  {
    const at = r.regua.atrasos;
    const adiant = at.filter((a) => a.adiantamento_min !== null && a.adiantamento_min > 0);
    const depoisDoAlerta = at.filter((a) => a.versao_gerada_brt !== null && a.versao_gerada_brt > a.em_brt);
    p(`Em ${adiant.length} dos ${at.length}, a versão que a régua põe antes do alerta foi gerada de ${faixa(adiant.map((a) => a.adiantamento_min ?? 0))} min depois do instante que a régua lhe atribui (${lista([...new Set(adiant.map((a) => a.uf.toUpperCase()))])}); em ${depoisDoAlerta.length}, ela nem existia na hora do alerta. Corrigir isso é gerar a curva da régua pelo instante de publicação (\`gerado_em\`), mudança em \`scripts/referencia-1t.ts\`, que é do orquestrador; fica registrada aqui, sem edição.`);
  }
  p();
  const cp = r.regua.contraprova;
  const pat = [...new Set(cp.eventos.map((e) => e.patamar_min))].sort((a, b) => a - b);
  const p20 = cp.eventos.filter((e) => e.patamar_min === 20);
  const acima20 = cp.eventos.filter((e) => e.patamar_min > 20);
  const ufsResid = new Set(r.regua.atrasos.map((a) => a.uf.toLowerCase()));
  p(`**Contraprova.** Um segundo \`AlertasRegua\`, fora do banco, lê os mesmos estados de UF com o relógio adiantado em ${cp.atraso_min} min, como se o 2º turno repetisse o 1º com esse atraso: ${cp.eventos.length} alertas em ${new Set(cp.eventos.map((e) => e.uf)).size} UFs (patamares ${pat.join(", ")} min, de ${hora(cp.eventos[0]?.em_brt ?? null)} a ${hora(cp.eventos.at(-1)?.em_brt ?? null)}). O patamar de 20 min dispara ${p20.length} vezes, ${new Set(p20.map((e) => e.uf)).size === p20.length ? "uma por UF" : "em UFs repetidas"}, entre ${hora(p20[0]?.em_brt ?? null)} e ${hora(p20.at(-1)?.em_brt ?? null)}. Os ${acima20.length} acima de 20 min caem em ${new Set(acima20.map((e) => e.uf)).size} UFs (${lista([...new Set(acima20.map((e) => e.uf.toUpperCase()))])}; ${acima20.filter((e) => ufsResid.has(e.uf)).length} deles nas UFs dos alertas residuais) e somam ao atraso simulado o adiantamento da régua descrito acima: com ${cp.atraso_min} min de atraso, basta a régua estar ${cp.atraso_min >= 40 ? "qualquer tempo" : `${40 - cp.atraso_min} min`} adiantada para o patamar chegar a 40. O alerta funciona sobre as curvas reais; o resultado da rodada padrão não vem de um alerta desligado.`);
  p();

  // ------------------------------------------------------------ defeitos
  p("### Defeitos encontrados no replay e corrigidos");
  p();
  const rv = r.regra_versao;
  const ex = r.exemplo_versao;
  p(`**1. Regra de versão regressiva (\`src/collector/processar-corpo.ts\`).** O coletor tratava como cópia antiga toda versão com idg menor que o da versão atual, mesmo gerada depois. O idg não acompanha a hora de geração: na noite de 04/10, ${n(rv.recuperadas)} versões de presidente (Brasil e UFs) geradas depois da atual chegaram com idg menor e foram descartadas. ${ex ? `Exemplo do banco: ${ex.uf.toUpperCase()} gerado às ${hora(ex.gerado_brt)} com ${d1(ex.pst)}% das seções, capturado às ${hora(ex.capturado_brt)}, descartado porque o idg caiu de ${n(ex.idg_atual)} (versão gerada às ${hora(ex.gerado_atual_brt)}, ${d1(ex.pst_atual)}%) para ${n(ex.idg)}; pela regra anterior o arquivo só voltou a andar às ${hora(ex.volta_brt)}, ${d1(ex.parado_min)} min depois. ` : ""}A regra agora ordena pela hora de geração (dg/hg) e usa o idg só para desempatar versões com a mesma hora ou sem hora (\`versaoRegressiva\`).`);
  p();
  p(tabela(["", "Aceitas", "Regressivas"], [
    ["Regra anterior (flags gravadas pelo coletor do 1º turno)", n(rv.anterior.aceitas), n(rv.anterior.regressivas)],
    ["Regra atual (replay)", n(rv.atual.aceitas), n(rv.atual.regressivas)],
  ]));
  p();
  p(`Entre as versões aceitas pela regra atual, ${n(rv.st_regrediu)} têm menos seções que a aceita anterior do mesmo arquivo: a ordem por geração não aceita conteúdo velho.`);
  if (anterior) {
    const ufs = anterior.pausas.filter((x) => x.nivel === "uf");
    p();
    p(`A rodada "${anterior.rotulo}" emula a regra anterior (o corpo que o coletor do 1º turno marcou como regressivo volta como leitura sem corpo, que era o efeito dele) e mostra o que mudou no motor: ${anterior.pausas.length} pausas contra ${padrao.pausas.length}, ${ufs.length} delas de UF (${ufs.map((x) => `${x.uf?.toUpperCase() ?? ""} ${hora(isoBrt(x.de))}–${hora(isoBrt(x.ate))}, st ${n(x.st_antes)} → ${n(x.st_depois)}`).join("; ")}). As de UF fecham com o mesmo número de seções com que abriram: eram versões publicadas e descartadas, não paradas da UF. Com a regra anterior a régua dava ${anterior.atraso_degrau} alertas de atraso em degrau e ${anterior.atraso_interpolado.length} pela interpolação.`);
    p();
    p(tabelaPausas(anterior.pausas));
  }
  p();
  const lacuna = r.regua_dossie.intervalos.find((x) => x.fonte === "pausa_geral.lacunas");
  const noite = padrao.atraso_interpolado.filter((x) => x.em < "2026-10-05T00:00:00.000Z");
  p(`**2. Atraso contra a curva do 1º turno (\`src/collector/regua.ts\`).** O alerta usava \`atrasoVsReferencia\`, que interpola linearmente entre dois pontos da curva. ${lacuna ? `Entre ${hora(isoBrt(lacuna.de))} e ${hora(isoBrt(lacuna.ate))} o 1º turno não publicou nada; a interpolação fazia a curva subir nesse trecho, e toda UF que estava no mesmo ponto do 1º turno na mesma hora aparecia atrasada assim que o relógio passava 20 min do último ponto antes da lacuna. ` : ""}Na rodada padrão a interpolação dá ${padrao.atraso_interpolado.length} alertas${noite.length > 0 ? `, ${noite.length} deles entre ${hora(isoBrt(noite[0]?.em ?? null))} e ${hora(isoBrt(noite.at(-1)?.em ?? null))}` : ""}. O alerta agora lê a curva em degraus: atraso é há quanto tempo, no mesmo relógio, o 1º turno já tinha passado do pst em que a UF está (\`atrasoEmDegrau\`, tolerância de meia unidade da 3ª casa decimal em que a régua grava o pst, abaixo de uma seção em qualquer UF). Os patamares de 20 min e o texto do evento não mudaram.`);
  p();

  const fz = r.fechamentos.filter((f) => {
    const t = Date.parse(String(f.detalhe.totalizado_em ?? ""));
    const g = Date.parse(String(f.detalhe.gerado_em ?? ""));
    return Number.isFinite(t) && Number.isFinite(g) && (g - t < 0 || g - t > 15 * 60_000);
  });
  p(`**3. Hora do fechamento de UF no telão (\`src/server/textos.ts\`).** O texto do \`uf_fechou\` usava a totalização corrigida do fuso. Em ${fz.length} das ${r.fechamentos.length} UFs ela fica fora da janela de 15 min antes da geração do arquivo: ${lista(fz.map((f) => `${f.uf?.toUpperCase() ?? ""} (totalização ${dia(isoBrt(String(f.detalhe.totalizado_em ?? "")))}, gerado ${dia(isoBrt(String(f.detalhe.gerado_em ?? "")))})`))}. O exterior traz a totalização na hora local da cidade (\`analysis/apuracao_2026/BRIEF.md\`: Wellington, 09:19 de 05/10) e o AM, um carimbo que parou antes da última versão; o telão escreveria esses horários. Agora, fora da janela, o texto usa a geração do arquivo; dentro dela, nada muda. O detalhe gravado guarda os dois carimbos.`);
  p();

  // ------------------------------------------------------------ (b)
  p("## (b) Conferência de BU real pela totalização paralela");
  p();
  p(`Regra declarada de escolha: em cada UF, a primeira seção por (município, zona, seção) com BU guardado em \`data/secoes_2026.sqlite\` e com dois números votados para presidente (para dar o que mover). ${(() => {
    const sa = d.bu.secoes.filter((x) => x.origem === "SA");
    return sa.length === 0 ? "" : `${lista(sa.map((x) => x.uf.toUpperCase()))} entra com boletim do Sistema de Apuração (${sa.map((x) => `\`${x.arquivo}\``).join(", ")}). `;
  })()}O hash e o arquivo vêm de \`escolherHash\` sobre o aux.json original, como o coletor faz, e são conferidos com o que o banco registrou.`);
  p();
  p(
    tabela(
      ["UF", "Município", "Zona", "Seção", "Uso", "Arquivo", "Origem do QR", "sha256", "Hash, arquivo e sha256 iguais ao banco"],
      d.bu.secoes.map((s) => [s.uf.toUpperCase(), s.municipio ?? s.mun, s.zona, s.secao, s.uso, `\`${s.arquivo}\``, s.origem, `\`${s.sha256.slice(0, 16)}…\``, s.banco.hash_igual && s.banco.arquivo_igual && s.banco.sha256_igual ? "sim" : "não"]),
    ),
  );
  p();
  p("O BU decodificado (`src/secoes2t/bu-decode.ts`) vira o registro das views públicas do Supabase (uma linha por cargo e uma por número votado, legenda como `LEGP<partido>`; no Sistema de Apuração o QR não traz APTO nem COMP, que ficam nulos). O lado da paralela passa por `cargosDoBu` e `qrComparavel`, o oficial por `resumoBu`, e os dois por `comparar` (`src/paralela/conferir.ts`).");
  p();
  p("### Comparação direta");
  p();
  p(
    tabela(
      ["BU", "Seção", "Caso", "Situação", "Diferenças"],
      d.bu.casos.map((c) => [
        c.id, `${c.uf.toUpperCase()} ${c.mun} z${c.zona} s${c.secao}`, c.nota,
        c.direta === null ? "não comparado" : `${c.direta.situacao}${c.direta.situacao === c.esperado ? "" : ` (esperado ${c.esperado})`}`,
        c.direta === null ? "" : c.direta.diferencas.map(rotuloDif).join("; ") || "nenhuma",
      ]),
    ),
  );
  p();
  p("O caso sem aux.json não passa por `comparar`: sem aux não há BU oficial para buscar, e a situação vem da ponte, abaixo.");
  p();
  p("### Pela ponte do coletor");
  p();
  p(`Os ${d.bu.casos.length} registros entram pela \`PonteParalela\` real, com um Supabase falso servindo as três views e um TSE falso servindo o aux.json e o BU originais (o aux da última seção responde 404). O primeiro ciclo roda antes de a amostra buscar qualquer seção; o segundo, depois da busca.`);
  p();
  const antes = new Map(d.bu.ponte.antes.map((x) => [x.bu_id, x.situacao]));
  p(
    tabela(
      ["BU", "Caso", "1º ciclo", "2º ciclo", "Diferenças gravadas"],
      d.bu.ponte.depois.map((x) => {
        const c = d.bu.casos.find((y) => y.id === x.bu_id);
        return [x.bu_id, c ? `${c.uf.toUpperCase()}: ${c.nota}` : "", antes.get(x.bu_id) ?? "", x.situacao, x.diferencas.map(rotuloDif).join("; ") || "nenhuma"];
      }),
    ),
  );
  p();
  const req = d.bu.ponte.requisicoes_tse;
  p(`Requisições ao TSE falso: ${req.length} (${req.filter((x) => x.status === 200).length} com 200, ${req.filter((x) => x.status === 404).length} com 404). \`/api/2t/paralela\` sobre o banco da demonstração: conferência ${Object.entries(d.bu.ponte.paralela.conferencia).map(([k, v]) => `${k} ${n(v)}`).join(", ")}; erro ${d.bu.ponte.paralela.erro === null ? "nulo" : d.bu.ponte.paralela.erro}.`);
  p();
  p("### Evento `divergencia_paralela`: texto e detalhe");
  p();
  p("Texto exato que a rota `/api/anomalias` (a mesma que o telão lê, via `textoEvento` de `src/server/textos.ts`) devolve para cada divergência gravada pela ponte:");
  p();
  for (const e of d.bu.ponte.eventos) p(`- BU ${e.bu_id} (\`${e.severidade}\`): "${e.texto}"`);
  if (d.bu.ponte.conferida) p(`- lote (\`paralela_conferida\`): "${d.bu.ponte.conferida.texto}"`);
  p();
  const evx = d.bu.ponte.eventos[0];
  if (evx) {
    p(`Detalhe gravado no banco para o BU ${evx.bu_id}:`);
    p();
    p("```json");
    p(JSON.stringify(evx.detalhe, null, 2));
    p("```");
    p();
    p("O `hash_final` do QR não está no arquivo `.dat`; a demonstração usa no lugar o sha256 do BU oficial, identificado como tal no próprio campo. O `recebido_em` é um instante fixo da demonstração, porque no 1º turno não houve envio real.");
    p();
  }

  // ------------------------------------------------------------ limites
  p("## O que isso prova e o que não prova");
  p();
  p("Prova:");
  p();
  p("- que o motor, ligado como no ar, detecta pausas, viradas e fechamentos de UF sobre as versões oficiais reais da noite de 04/10, nos mesmos segundos da régua publicada no dossiê, e que o limiar de 7 min separa a parada real da cadência normal do arquivo nacional;");
  p("- que a régua do 1º turno não acusa abstenção atípica contra a própria noite e acusa atraso quando a mesma noite chega atrasada;");
  p("- que a conferência da totalização paralela decodifica BUs oficiais reais (urna e Sistema de Apuração), declara igual o que é igual, aponta campo a campo um voto movido ou um comparecimento alterado em 1, espera o TSE quando o aux.json não existe e gera o evento e o texto que o telão mostra.");
  p();
  p("Não prova:");
  p();
  p("- o comportamento da rede, do CDN e da divulgação do TSE em 25/10: cadência, atrasos de entrega e paradas do 2º turno serão outros;");
  p("- a presença de BUs na totalização paralela: nenhum BU real foi enviado por QR nesta demonstração, e a leitura do QR, a cadeia de certificados e o Supabase de produção ficaram fora;");
  p("- que uma pausa, um atraso ou uma divergência signifiquem irregularidade: pausa é intervalo sem versão nova publicada, atraso pede explicação, e a conferência de BU prova transmissão e soma da seção, não o interior da urna.");
  p();
  return `${out.join("\n").replace(/\n{3,}/g, "\n\n").trimEnd()}\n`;
}
