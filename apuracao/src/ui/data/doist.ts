// Rotas /api/2t/* do 2º turno: tipos do telão e normalizadores. Cada normalizador aceita
// qualquer corpo e devolve uma `Resposta`: dados prontos, "pendente" (o servidor ainda não
// implementa a rota: `{pendente: true}`) ou "erro" (corpo `{erro}`, HTTP ruim ou forma
// irreconhecível). A tela mostra "fonte indisponível" nos dois últimos casos, nunca fica em branco.
// Números chegam já convertidos; campo ausente vira 0 ou null, nunca NaN.

export type Rota2T =
  | "regioes"
  | "ufs"
  | "abstencao"
  | "estaduais"
  | "evolucao-regiao"
  | "evolucao-uf"
  | "pausas"
  | "secoes"
  | "paralela"
  | "projecao";

export const ROTAS_2T: readonly Rota2T[] = [
  "regioes",
  "ufs",
  "abstencao",
  "estaduais",
  "evolucao-regiao",
  "evolucao-uf",
  "pausas",
  "secoes",
  "paralela",
  "projecao",
];

export type Resposta<T> = { situacao: "ok"; dados: T } | { situacao: "pendente" } | { situacao: "erro"; mensagem: string };

export const pendente = <T>(): Resposta<T> => ({ situacao: "pendente" });
export const erro = <T>(mensagem: string): Resposta<T> => ({ situacao: "erro", mensagem });
export const ok = <T>(dados: T): Resposta<T> => ({ situacao: "ok", dados });

/** Caminho e parâmetros de cada rota. A evolução pede passo de 5 min: 1 ponto por 5 min basta no telão. */
export function pedidoDaRota(rota: Rota2T): { caminho: string; params: Record<string, string | number> } {
  switch (rota) {
    case "evolucao-regiao":
      return { caminho: "/api/2t/evolucao", params: { nivel: "regiao", passo: 300 } };
    case "evolucao-uf":
      return { caminho: "/api/2t/evolucao", params: { nivel: "uf", passo: 300 } };
    default:
      return { caminho: `/api/2t/${rota}`, params: {} };
  }
}

// ---------- tipos ----------

export interface VotoAgregado {
  vap: number;
  pvapn: number;
}

export interface RefAgregado {
  pst_mesmo_relogio: number;
  atraso_min: number | null;
  pa_final_1t: number | null;
}

export interface Agregado {
  sigla: string;
  nome: string;
  ufs: string[];
  ts: number;
  st: number;
  snt: number;
  pst: number;
  te: number;
  est: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
  votos: Record<string, VotoAgregado>;
  vv: number;
  vb: number;
  vn: number;
  tv: number;
  lider: string | null;
  margem_pp: number;
  vel_10min_spm: number;
  eta_100_iso: string | null;
  ref_1t: RefAgregado | null;
  atualizado_em: string | null;
}

export interface Regioes {
  at: string;
  min: number;
  turno: number;
  referencia_1t: boolean;
  brasil: Agregado;
  regioes: Agregado[];
}

export interface RefUf {
  pst_mesmo_relogio: number;
  atraso_min: number | null;
  p50_min: number | null;
  p90_min: number | null;
  p99_min: number | null;
  p100_min: number | null;
  pa_final: number | null;
}

export interface MunicipioPendente {
  cd: string;
  nm: string;
  te: number;
  pst: number;
}

export interface UfLinha {
  uf: string;
  nome: string;
  regiao: string;
  ts: number;
  st: number;
  snt: number;
  pst: number;
  te: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
  munnr: number;
  munpt: number;
  munf: number;
  votos: Record<string, VotoAgregado>;
  lider: string | null;
  margem_pp: number;
  ultima_versao_em: string | null;
  idade_s: number | null;
  vel_10min_spm: number;
  eta_100_iso: string | null;
  parada: boolean;
  ref_1t: RefUf | null;
  pendentes_maiores: MunicipioPendente[];
}

export interface UfsResp {
  at: string;
  min: number;
  limiar_parada_min: number;
  ufs: UfLinha[];
}

export interface BlocoAbstencao {
  chave: string;
  nome: string;
  n_mun: number;
  n_mun_fechados: number;
  te_fechado: number;
  pct_te_fechado: number;
  comparecimento: number;
  abstencao: number;
  pa_2t: number | null;
  pa_1t_mesmos: number | null;
  delta_pp: number | null;
  pa_corrente: number | null;
  pa_final_1t: number | null;
}

export interface MunAbstencao {
  uf: string;
  cd: string;
  nm: string;
  te: number;
  pa_2t: number;
  pa_1t: number;
  delta_pp: number;
  fechou_min: number | null;
}

export interface Abstencao {
  at: string;
  min: number;
  base: string;
  brasil: BlocoAbstencao;
  regioes: BlocoAbstencao[];
  ufs: BlocoAbstencao[];
  destaques: { subiu: MunAbstencao[]; caiu: MunAbstencao[] };
}

export interface CandEstadual {
  sqcand: string;
  n: string;
  nome_urna: string;
  partido: string;
  vap: number;
  pvapn: number;
  campo: string;
}

export interface Estadual {
  uf: string;
  nome: string;
  ts: number;
  st: number;
  pst: number;
  te: number;
  comparecimento: number;
  abstencao: number;
  pa: number;
  munnr: number;
  munpt: number;
  munf: number;
  cand: CandEstadual[];
  lider: string | null;
  margem_pp: number;
  viradas: { at: string; de: string; para: string }[];
  ultima_versao_em: string | null;
  idade_s: number | null;
  ref_1t: { pst_mesmo_relogio: number; atraso_min: number | null } | null;
  pa_final_1t: number | null;
}

export interface Estaduais {
  at: string;
  min: number;
  ufs: Estadual[];
}

/** Ponto da evolução: minutos após 17:00, pst, % válidos dos dois candidatos (null sem voto) e st. */
export interface PontoEvolucao {
  min: number;
  pst: number;
  a: number | null;
  b: number | null;
  st: number;
}

export interface CandEvolucao {
  sqcand: string;
  n: string;
  nome_urna: string;
}

export interface Evolucao {
  at: string;
  passo_s: number;
  /** Os dois candidatos em ordem crescente do número de urna; `a` e `b` dos pontos seguem esta ordem. */
  candidatos: CandEvolucao[];
  series: Record<string, PontoEvolucao[]>;
  referencia_1t: Record<string, [number, number][]> | null;
}

export interface PausaHistorico {
  de: string;
  ate: string;
  minutos: number;
  st_antes: number | null;
  st_depois: number | null;
}

export interface Pausas {
  at: string;
  min: number;
  limiar_min: number;
  nacional: {
    ultima_versao_em: string | null;
    idade_s: number | null;
    st: number;
    ts: number;
    em_pausa: boolean;
    pausa_atual: { desde: string; minutos: number } | null;
    historico: PausaHistorico[];
  };
  soma_ufs: { st: number; pst: number; defasagem_secoes: number; defasagem_min: number | null };
  ufs: { uf: string; ultima_versao_em: string | null; idade_s: number | null; em_pausa: boolean; st: number; ts: number; historico_n: number }[];
  referencia_1t: {
    pausa_geral: { de: string; ate: string; minutos: number } | null;
    travamento_nacional: { de: string; ate: string } | null;
  };
}

export interface LagPct {
  p50: number | null;
  p90: number | null;
  p99: number | null;
}

export interface LinhaSecoes {
  uf: string;
  alvo: number;
  recebidas: number;
  encerramento_p50_hhmm: string | null;
  encerramento_p90_hhmm: string | null;
  tarde_apos_1730_pct: number | null;
  lag_encerr_recebimento_min: LagPct;
  lag_encerr_emissao_min: LagPct;
  /** Opcional: o contrato cita a totalização do município, mas não fixa o campo. */
  lag_recebimento_totalizacao_min: LagPct | null;
  ref_1t: { lag_p50: number | null; lag_p90: number | null; enc_p90_hhmm: string | null } | null;
}

export interface SecaoTardia {
  uf: string;
  mun: string;
  nm: string;
  zona: string;
  secao: string;
  encerramento_hhmm: string;
  recebido_hhmm: string;
  lag_min: number | null;
}

export interface SecaoRecente {
  uf: string;
  mun: string;
  zona: string;
  secao: string;
  recebido_em: string;
  lag_min: number | null;
}

export interface Secoes {
  at: string;
  min: number;
  desenho: { nacional_por_uf: number; estaduais_por_uf: number; inclui_paralela: boolean; intervalo_s: number | null };
  totais: { alvo: number; recebidas: number; pendentes: number; tardias: number };
  por_uf: LinhaSecoes[];
  brasil: LinhaSecoes;
  tardias: SecaoTardia[];
  ultimas: SecaoRecente[];
}

export interface CampoDivergente {
  campo: string;
  paralela: string;
  tse: string;
}

export interface DivergenciaParalela {
  uf: string;
  mun: string;
  zona: string;
  secao: string;
  recebido_em: string | null;
  conferido_em: string | null;
  campos: CampoDivergente[];
}

export interface PlacarBus {
  votos: Record<string, number>;
  comparecimento: number;
  aptos: number;
  brancos: number;
  nulos: number;
  secoes: number;
}

export interface Paralela {
  at: string;
  atualizado_em: string | null;
  /** Erro de leitura da fonte (Supabase) informado pelo servidor com HTTP 200. */
  erro: string | null;
  recebidos: { bus: number; envios: number; secoes: number; ufs: number; conflitos: number };
  conferencia: {
    iguais: number;
    divergentes: number;
    tse_ainda_nao_publicou: number;
    erro: number;
    fora_do_oficial: number;
    pendentes: number;
  };
  cobertura_uf: { uf: string; bus: number; secoes_total: number; pct: number }[];
  placar_bus: { presidente: PlacarBus; governador: Record<string, { votos: Record<string, number>; secoes: number }> };
  divergencias: DivergenciaParalela[];
  ultimos: { uf: string; mun: string; zona: string; secao: string; recebido_em: string | null; situacao: string }[];
}

/** Projetado de um bloco: votos dos dois, % entre os dois (= % dos válidos do 2º turno) e faixa de 90% de p_f. */
export interface ProjetadoBloco {
  f: number;
  l: number;
  p_f: number;
  p_l: number;
  p_f_validos: number;
  p_l_validos: number;
  faixa90: [number, number];
}

/** Brasil, região ou UF na projeção. `f` = Flávio (22), `l` = Lula (13). */
export interface BlocoProjecao {
  sigla: string;
  nome: string;
  pst: number;
  pct_vv_observado: number;
  /** Flávio entre os dois no 1º turno, em %. */
  p1_f: number | null;
  observado: { f: number; l: number; p_f: number | null };
  projetado: ProjetadoBloco | null;
  /** p_f observado menos o 1º turno nos mesmos municípios, em pontos. */
  swing_pp: number | null;
}

export interface CandProjecao {
  sqcand: string;
  n: string;
  nome_urna: string;
}

/** Ponto da série: minutos após 17:00, p_f projetado, faixa, p_f observado e pst. */
export interface PontoProjecao {
  min: number;
  proj: number | null;
  a: number | null;
  b: number | null;
  obs: number | null;
  pst: number;
}

export interface Projecao {
  at: string;
  min: number;
  rotulo: string;
  candidatos: { f: CandProjecao; l: CandProjecao };
  cobertura: { pst: number; st: number; ts: number; pct_vv_observado: number; municipios_observados: number; municipios_fechados: number; municipios_total: number };
  brasil: BlocoProjecao;
  regioes: BlocoProjecao[];
  ufs: BlocoProjecao[];
  parametros: { K: number; K_uf: number; erro_comum_pp: number; reps: number; nivel_faixa: number; minimo_pst: number; metodo: string };
  motivo_sem_projecao: string | null;
  serie: PontoProjecao[];
}

/** Rótulo obrigatório da projeção (tela e API). */
export const ROTULO_PROJECAO = "projeção estatística a partir do que já foi totalizado; não é resultado nem previsão de vitória";

export interface Dados2T {
  regioes: Regioes;
  ufs: UfsResp;
  abstencao: Abstencao;
  estaduais: Estaduais;
  "evolucao-regiao": Evolucao;
  "evolucao-uf": Evolucao;
  pausas: Pausas;
  secoes: Secoes;
  paralela: Paralela;
  projecao: Projecao;
}

export type Respostas2T = { [K in Rota2T]?: Resposta<Dados2T[K]> };

// ---------- leitura tolerante ----------

type Bruto = Record<string, unknown>;
const ehBruto = (x: unknown): x is Bruto => typeof x === "object" && x !== null && !Array.isArray(x);
const lista = (x: unknown): unknown[] => (Array.isArray(x) ? x : []);
const regs = (x: unknown): Bruto[] => lista(x).filter(ehBruto);
const num = (x: unknown, padrao = 0): number => (typeof x === "number" && Number.isFinite(x) ? x : padrao);
const numOuNulo = (x: unknown): number | null => (typeof x === "number" && Number.isFinite(x) ? x : null);
const txt = (x: unknown, padrao = ""): string => (typeof x === "string" ? x : typeof x === "number" ? String(x) : padrao);
const txtOuNulo = (x: unknown): string | null => (typeof x === "string" && x !== "" ? x : null);
const bool = (x: unknown): boolean => x === true;
const texts = (x: unknown): string[] => lista(x).filter((y): y is string => typeof y === "string");

/** Corpo {pendente:true} ou {erro:"..."}; null quando é um corpo normal. */
export function corpoSemDados<T>(bruto: unknown): Resposta<T> | null {
  if (!ehBruto(bruto)) return erro("resposta vazia");
  if (bruto.pendente === true) return pendente();
  if (typeof bruto.erro === "string" && bruto.erro !== "") return erro(bruto.erro);
  return null;
}

function votos(x: unknown): Record<string, VotoAgregado> {
  const saida: Record<string, VotoAgregado> = {};
  if (!ehBruto(x)) return saida;
  for (const [k, v] of Object.entries(x)) if (ehBruto(v)) saida[String(k)] = { vap: num(v.vap), pvapn: num(v.pvapn) };
  return saida;
}

function agregado(b: Bruto): Agregado {
  const ref = ehBruto(b.ref_1t)
    ? { pst_mesmo_relogio: num(b.ref_1t.pst_mesmo_relogio), atraso_min: numOuNulo(b.ref_1t.atraso_min), pa_final_1t: numOuNulo(b.ref_1t.pa_final_1t) }
    : null;
  return {
    sigla: txt(b.sigla),
    nome: txt(b.nome, txt(b.sigla)),
    ufs: texts(b.ufs),
    ts: num(b.ts),
    st: num(b.st),
    snt: num(b.snt, Math.max(0, num(b.ts) - num(b.st))),
    pst: num(b.pst),
    te: num(b.te),
    est: num(b.est),
    comparecimento: num(b.comparecimento),
    abstencao: num(b.abstencao),
    pa: num(b.pa),
    votos: votos(b.votos),
    vv: num(b.vv),
    vb: num(b.vb),
    vn: num(b.vn),
    tv: num(b.tv),
    lider: txtOuNulo(b.lider),
    margem_pp: num(b.margem_pp),
    vel_10min_spm: num(b.vel_10min_spm),
    eta_100_iso: txtOuNulo(b.eta_100_iso),
    ref_1t: ref,
    atualizado_em: txtOuNulo(b.atualizado_em),
  };
}

export function normalizarRegioes(bruto: unknown): Resposta<Regioes> {
  const sem = corpoSemDados<Regioes>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  if (!ehBruto(b.brasil)) return erro("resposta sem o agregado do Brasil");
  const brasil = agregado(b.brasil);
  return ok({
    at: txt(b.at),
    min: num(b.min),
    turno: num(b.turno, 2),
    referencia_1t: bool(b.referencia_1t),
    brasil: { ...brasil, sigla: brasil.sigla || "BR", nome: brasil.nome || "Brasil" },
    regioes: regs(b.regioes).map(agregado),
  });
}

function refUf(x: unknown): RefUf | null {
  if (!ehBruto(x)) return null;
  return {
    pst_mesmo_relogio: num(x.pst_mesmo_relogio),
    atraso_min: numOuNulo(x.atraso_min),
    p50_min: numOuNulo(x.p50_min),
    p90_min: numOuNulo(x.p90_min),
    p99_min: numOuNulo(x.p99_min),
    p100_min: numOuNulo(x.p100_min),
    pa_final: numOuNulo(x.pa_final),
  };
}

function ufLinha(b: Bruto): UfLinha {
  return {
    uf: txt(b.uf).toUpperCase(),
    nome: txt(b.nome, txt(b.uf).toUpperCase()),
    regiao: txt(b.regiao),
    ts: num(b.ts),
    st: num(b.st),
    snt: num(b.snt, Math.max(0, num(b.ts) - num(b.st))),
    pst: num(b.pst),
    te: num(b.te),
    comparecimento: num(b.comparecimento),
    abstencao: num(b.abstencao),
    pa: num(b.pa),
    munnr: num(b.munnr),
    munpt: num(b.munpt),
    munf: num(b.munf),
    votos: votos(b.votos),
    lider: txtOuNulo(b.lider),
    margem_pp: num(b.margem_pp),
    ultima_versao_em: txtOuNulo(b.ultima_versao_em),
    idade_s: numOuNulo(b.idade_s),
    vel_10min_spm: num(b.vel_10min_spm),
    eta_100_iso: txtOuNulo(b.eta_100_iso),
    parada: bool(b.parada),
    ref_1t: refUf(b.ref_1t),
    pendentes_maiores: regs(b.pendentes_maiores).map(m => ({ cd: txt(m.cd), nm: txt(m.nm), te: num(m.te), pst: num(m.pst) })),
  };
}

export function normalizarUfs(bruto: unknown): Resposta<UfsResp> {
  const sem = corpoSemDados<UfsResp>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  if (!Array.isArray(b.ufs)) return erro("resposta sem a lista de UFs");
  return ok({ at: txt(b.at), min: num(b.min), limiar_parada_min: num(b.limiar_parada_min, 10), ufs: regs(b.ufs).map(ufLinha) });
}

function blocoAbstencao(b: Bruto): BlocoAbstencao {
  const chave = txt(b.sigla, txt(b.uf)).toUpperCase();
  return {
    chave,
    nome: txt(b.nome, chave),
    n_mun: num(b.n_mun),
    n_mun_fechados: num(b.n_mun_fechados),
    te_fechado: num(b.te_fechado),
    pct_te_fechado: num(b.pct_te_fechado),
    comparecimento: num(b.comparecimento),
    abstencao: num(b.abstencao),
    pa_2t: numOuNulo(b.pa_2t),
    pa_1t_mesmos: numOuNulo(b.pa_1t_mesmos),
    delta_pp: numOuNulo(b.delta_pp),
    pa_corrente: numOuNulo(b.pa_corrente),
    pa_final_1t: numOuNulo(b.pa_final_1t),
  };
}

function munAbstencao(b: Bruto): MunAbstencao {
  return {
    uf: txt(b.uf).toUpperCase(),
    cd: txt(b.cd),
    nm: txt(b.nm),
    te: num(b.te),
    pa_2t: num(b.pa_2t),
    pa_1t: num(b.pa_1t),
    delta_pp: num(b.delta_pp),
    fechou_min: numOuNulo(b.fechou_min),
  };
}

export function normalizarAbstencao(bruto: unknown): Resposta<Abstencao> {
  const sem = corpoSemDados<Abstencao>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  if (!ehBruto(b.brasil)) return erro("resposta sem o bloco do Brasil");
  const d = ehBruto(b.destaques) ? b.destaques : {};
  return ok({
    at: txt(b.at),
    min: num(b.min),
    base: txt(b.base, "municipios_fechados"),
    brasil: { ...blocoAbstencao(b.brasil), chave: "BR", nome: "Brasil" },
    regioes: regs(b.regioes).map(blocoAbstencao),
    ufs: regs(b.ufs).map(blocoAbstencao),
    destaques: { subiu: regs(d.subiu).map(munAbstencao), caiu: regs(d.caiu).map(munAbstencao) },
  });
}

function estadual(b: Bruto): Estadual {
  const ref = ehBruto(b.ref_1t) ? { pst_mesmo_relogio: num(b.ref_1t.pst_mesmo_relogio), atraso_min: numOuNulo(b.ref_1t.atraso_min) } : null;
  return {
    uf: txt(b.uf).toUpperCase(),
    nome: txt(b.nome, txt(b.uf).toUpperCase()),
    ts: num(b.ts),
    st: num(b.st),
    pst: num(b.pst),
    te: num(b.te),
    comparecimento: num(b.comparecimento),
    abstencao: num(b.abstencao),
    pa: num(b.pa),
    munnr: num(b.munnr),
    munpt: num(b.munpt),
    munf: num(b.munf),
    cand: regs(b.cand).map(c => ({
      sqcand: txt(c.sqcand),
      n: txt(c.n),
      nome_urna: txt(c.nome_urna),
      partido: txt(c.partido),
      vap: num(c.vap),
      pvapn: num(c.pvapn),
      campo: txt(c.campo, "indefinido"),
    })),
    lider: txtOuNulo(b.lider),
    margem_pp: num(b.margem_pp),
    viradas: regs(b.viradas).map(v => ({ at: txt(v.at), de: txt(v.de), para: txt(v.para) })),
    ultima_versao_em: txtOuNulo(b.ultima_versao_em),
    idade_s: numOuNulo(b.idade_s),
    ref_1t: ref,
    pa_final_1t: numOuNulo(b.pa_final_1t),
  };
}

export function normalizarEstaduais(bruto: unknown): Resposta<Estaduais> {
  const sem = corpoSemDados<Estaduais>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  if (!Array.isArray(b.ufs)) return erro("resposta sem a lista de estaduais");
  return ok({ at: txt(b.at), min: num(b.min), ufs: regs(b.ufs).map(estadual) });
}

/** Ordena os candidatos pelo número de urna e reordena as colunas a/b de cada ponto na mesma ordem. */
export function normalizarEvolucao(bruto: unknown): Resposta<Evolucao> {
  const sem = corpoSemDados<Evolucao>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  if (!ehBruto(b.series)) return erro("resposta sem séries");
  const brutos = regs(b.candidatos).map(c => ({ sqcand: txt(c.sqcand), n: txt(c.n), nome_urna: txt(c.nome_urna) }));
  const ordem = brutos.map((c, i) => ({ c, i })).sort((x, y) => x.c.n.localeCompare(y.c.n, "pt-BR", { numeric: true }));
  const trocar = ordem[0]?.i === 1;
  const series: Record<string, PontoEvolucao[]> = {};
  for (const [chave, pts] of Object.entries(b.series)) {
    series[chave.toUpperCase()] = lista(pts)
      .filter((p): p is unknown[] => Array.isArray(p))
      .map(p => {
        const x = numOuNulo(p[2]);
        const y = numOuNulo(p[3]);
        return { min: num(p[0]), pst: num(p[1]), a: trocar ? y : x, b: trocar ? x : y, st: num(p[4]) };
      })
      .sort((p, q) => p.min - q.min);
  }
  let ref: Record<string, [number, number][]> | null = null;
  if (ehBruto(b.referencia_1t)) {
    ref = {};
    for (const [chave, pts] of Object.entries(b.referencia_1t)) {
      ref[chave.toUpperCase()] = lista(pts)
        .filter((p): p is unknown[] => Array.isArray(p))
        .map((p): [number, number] => [num(p[0]), num(p[1])])
        .sort((p, q) => p[0] - q[0]);
    }
  }
  return ok({ at: txt(b.at), passo_s: num(b.passo_s, 60), candidatos: ordem.map(o => o.c), series, referencia_1t: ref });
}

export function normalizarPausas(bruto: unknown): Resposta<Pausas> {
  const sem = corpoSemDados<Pausas>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  const nac = ehBruto(b.nacional) ? b.nacional : null;
  if (!nac) return erro("resposta sem o arquivo nacional");
  const atual = ehBruto(nac.pausa_atual) ? { desde: txt(nac.pausa_atual.desde), minutos: num(nac.pausa_atual.minutos) } : null;
  const soma = ehBruto(b.soma_ufs) ? b.soma_ufs : {};
  const ref = ehBruto(b.referencia_1t) ? b.referencia_1t : {};
  const intervalo = (x: unknown): { de: string; ate: string; minutos: number } | null =>
    ehBruto(x) ? { de: txt(x.de), ate: txt(x.ate), minutos: num(x.minutos) } : null;
  const trav = ehBruto(ref.travamento_nacional) ? { de: txt(ref.travamento_nacional.de), ate: txt(ref.travamento_nacional.ate) } : null;
  return ok({
    at: txt(b.at),
    min: num(b.min),
    limiar_min: num(b.limiar_min, 5),
    nacional: {
      ultima_versao_em: txtOuNulo(nac.ultima_versao_em),
      idade_s: numOuNulo(nac.idade_s),
      st: num(nac.st),
      ts: num(nac.ts),
      em_pausa: bool(nac.em_pausa),
      pausa_atual: atual,
      historico: regs(nac.historico).map(h => ({
        de: txt(h.de),
        ate: txt(h.ate),
        minutos: num(h.minutos),
        st_antes: numOuNulo(h.st_antes),
        st_depois: numOuNulo(h.st_depois),
      })),
    },
    soma_ufs: {
      st: num(soma.st),
      pst: num(soma.pst),
      defasagem_secoes: num(soma.defasagem_secoes),
      defasagem_min: numOuNulo(soma.defasagem_min),
    },
    ufs: regs(b.ufs).map(u => ({
      uf: txt(u.uf).toUpperCase(),
      ultima_versao_em: txtOuNulo(u.ultima_versao_em),
      idade_s: numOuNulo(u.idade_s),
      em_pausa: bool(u.em_pausa),
      st: num(u.st),
      ts: num(u.ts),
      historico_n: num(u.historico_n),
    })),
    referencia_1t: { pausa_geral: intervalo(ref.pausa_geral), travamento_nacional: trav },
  });
}

function lag(x: unknown): LagPct {
  return ehBruto(x) ? { p50: numOuNulo(x.p50), p90: numOuNulo(x.p90), p99: numOuNulo(x.p99) } : { p50: null, p90: null, p99: null };
}

function linhaSecoes(b: Bruto): LinhaSecoes {
  const ref = ehBruto(b.ref_1t)
    ? { lag_p50: numOuNulo(b.ref_1t.lag_p50), lag_p90: numOuNulo(b.ref_1t.lag_p90), enc_p90_hhmm: txtOuNulo(b.ref_1t.enc_p90_hhmm) }
    : null;
  return {
    uf: txt(b.uf).toUpperCase(),
    alvo: num(b.alvo),
    recebidas: num(b.recebidas),
    encerramento_p50_hhmm: txtOuNulo(b.encerramento_p50_hhmm),
    encerramento_p90_hhmm: txtOuNulo(b.encerramento_p90_hhmm),
    tarde_apos_1730_pct: numOuNulo(b.tarde_apos_1730_pct),
    lag_encerr_recebimento_min: lag(b.lag_encerr_recebimento_min),
    lag_encerr_emissao_min: lag(b.lag_encerr_emissao_min),
    lag_recebimento_totalizacao_min: ehBruto(b.lag_recebimento_totalizacao_min) ? lag(b.lag_recebimento_totalizacao_min) : null,
    ref_1t: ref,
  };
}

export function normalizarSecoes(bruto: unknown): Resposta<Secoes> {
  const sem = corpoSemDados<Secoes>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  if (!ehBruto(b.brasil)) return erro("resposta sem o bloco do Brasil");
  const d = ehBruto(b.desenho) ? b.desenho : {};
  const t = ehBruto(b.totais) ? b.totais : {};
  const recebidas = num(t.recebidas);
  return ok({
    at: txt(b.at),
    min: num(b.min),
    desenho: {
      nacional_por_uf: num(d.nacional_por_uf),
      estaduais_por_uf: num(d.estaduais_por_uf),
      inclui_paralela: bool(d.inclui_paralela),
      intervalo_s: numOuNulo(d.intervalo_s),
    },
    totais: { alvo: num(t.alvo), recebidas, pendentes: num(t.pendentes), tardias: num(t.tardias) },
    por_uf: regs(b.por_uf).map(linhaSecoes),
    brasil: { ...linhaSecoes(b.brasil), uf: "BR" },
    tardias: regs(b.tardias).map(s => ({
      uf: txt(s.uf).toUpperCase(),
      mun: txt(s.mun),
      nm: txt(s.nm),
      zona: txt(s.zona),
      secao: txt(s.secao),
      encerramento_hhmm: txt(s.encerramento_hhmm),
      recebido_hhmm: txt(s.recebido_hhmm),
      lag_min: numOuNulo(s.lag_min),
    })),
    ultimas: regs(b.ultimas).map(s => ({
      uf: txt(s.uf).toUpperCase(),
      mun: txt(s.mun),
      zona: txt(s.zona),
      secao: txt(s.secao),
      recebido_em: txt(s.recebido_em),
      lag_min: numOuNulo(s.lag_min),
    })),
  });
}

function placarBus(x: unknown): PlacarBus {
  const b = ehBruto(x) ? x : {};
  const v: Record<string, number> = {};
  if (ehBruto(b.votos)) for (const [k, n] of Object.entries(b.votos)) v[k] = num(n);
  return { votos: v, comparecimento: num(b.comparecimento), aptos: num(b.aptos), brancos: num(b.brancos), nulos: num(b.nulos), secoes: num(b.secoes) };
}

export function normalizarParalela(bruto: unknown): Resposta<Paralela> {
  // A paralela pode trazer `erro` junto dos últimos números (a leitura do Supabase falhou, mas
  // o servidor guardou a última): sem o bloco `recebidos`, vale como erro; com ele, a tela avisa.
  if (!(ehBruto(bruto) && ehBruto(bruto.recebidos))) {
    const sem = corpoSemDados<Paralela>(bruto);
    return sem ?? erro("resposta sem os BUs recebidos");
  }
  const b = bruto;
  const r = ehBruto(b.recebidos) ? b.recebidos : {};
  const c = ehBruto(b.conferencia) ? b.conferencia : {};
  const pb = ehBruto(b.placar_bus) ? b.placar_bus : {};
  const gov: Record<string, { votos: Record<string, number>; secoes: number }> = {};
  if (ehBruto(pb.governador)) {
    for (const [uf, g] of Object.entries(pb.governador)) {
      if (!ehBruto(g)) continue;
      const votosUf: Record<string, number> = {};
      if (ehBruto(g.votos)) for (const [k, n] of Object.entries(g.votos)) votosUf[k] = num(n);
      gov[uf.toUpperCase()] = { votos: votosUf, secoes: num(g.secoes) };
    }
  }
  return ok({
    at: txt(b.at),
    atualizado_em: txtOuNulo(b.atualizado_em),
    erro: txtOuNulo(b.erro),
    recebidos: { bus: num(r.bus), envios: num(r.envios), secoes: num(r.secoes), ufs: num(r.ufs), conflitos: num(r.conflitos) },
    conferencia: {
      iguais: num(c.iguais),
      divergentes: num(c.divergentes),
      tse_ainda_nao_publicou: num(c.tse_ainda_nao_publicou),
      erro: num(c.erro),
      fora_do_oficial: num(c.fora_do_oficial),
      pendentes: num(c.pendentes),
    },
    cobertura_uf: regs(b.cobertura_uf).map(u => ({ uf: txt(u.uf).toUpperCase(), bus: num(u.bus), secoes_total: num(u.secoes_total), pct: num(u.pct) })),
    placar_bus: { presidente: placarBus(pb.presidente), governador: gov },
    divergencias: regs(b.divergencias).map(d => ({
      uf: txt(d.uf).toUpperCase(),
      mun: txt(d.mun),
      zona: txt(d.zona),
      secao: txt(d.secao),
      recebido_em: txtOuNulo(d.recebido_em),
      conferido_em: txtOuNulo(d.conferido_em),
      campos: regs(d.campos).map(f => ({ campo: txt(f.campo), paralela: txt(f.paralela), tse: txt(f.tse) })),
    })),
    ultimos: regs(b.ultimos).map(u => ({
      uf: txt(u.uf).toUpperCase(),
      mun: txt(u.mun),
      zona: txt(u.zona),
      secao: txt(u.secao),
      recebido_em: txtOuNulo(u.recebido_em),
      situacao: txt(u.situacao),
    })),
  });
}

function blocoProjecao(b: Bruto): BlocoProjecao {
  const o: Bruto = ehBruto(b.observado) ? b.observado : {};
  const pj = ehBruto(b.projetado) ? b.projetado : null;
  const fx = pj ? lista(pj.faixa90) : [];
  const pf = pj ? num(pj.p_f) : 0;
  return {
    sigla: txt(b.sigla).toUpperCase(),
    nome: txt(b.nome, txt(b.sigla)),
    pst: num(b.pst),
    pct_vv_observado: num(b.pct_vv_observado),
    p1_f: numOuNulo(b.p1_f),
    observado: { f: num(o.f), l: num(o.l), p_f: numOuNulo(o.p_f) },
    projetado: pj
      ? {
          f: num(pj.f),
          l: num(pj.l),
          p_f: pf,
          p_l: num(pj.p_l, 100 - pf),
          p_f_validos: num(pj.p_f_validos),
          p_l_validos: num(pj.p_l_validos),
          faixa90: [num(fx[0], pf), num(fx[1], pf)],
        }
      : null,
    swing_pp: numOuNulo(b.swing_pp),
  };
}

function candProjecao(x: unknown, n: string): CandProjecao {
  const c: Bruto = ehBruto(x) ? x : {};
  return { sqcand: txt(c.sqcand), n: txt(c.n, n), nome_urna: txt(c.nome_urna) };
}

/** Projeção ao vivo: blocos com `projetado` null antes da base mínima; série ordenada pelo relógio. */
export function normalizarProjecao(bruto: unknown): Resposta<Projecao> {
  const sem = corpoSemDados<Projecao>(bruto);
  if (sem) return sem;
  const b = bruto as Bruto;
  if (!ehBruto(b.brasil)) return erro("resposta sem o bloco do Brasil");
  const cob: Bruto = ehBruto(b.cobertura) ? b.cobertura : {};
  const par: Bruto = ehBruto(b.parametros) ? b.parametros : {};
  const cands: Bruto = ehBruto(b.candidatos) ? b.candidatos : {};
  return ok({
    at: txt(b.at),
    min: num(b.min),
    rotulo: txt(b.rotulo, ROTULO_PROJECAO) || ROTULO_PROJECAO,
    candidatos: { f: candProjecao(cands.f, "22"), l: candProjecao(cands.l, "13") },
    cobertura: {
      pst: num(cob.pst),
      st: num(cob.st),
      ts: num(cob.ts),
      pct_vv_observado: num(cob.pct_vv_observado),
      municipios_observados: num(cob.municipios_observados),
      municipios_fechados: num(cob.municipios_fechados),
      municipios_total: num(cob.municipios_total),
    },
    brasil: blocoProjecao(b.brasil),
    regioes: regs(b.regioes).map(blocoProjecao),
    ufs: regs(b.ufs).map(blocoProjecao),
    parametros: {
      K: num(par.K),
      K_uf: num(par.K_uf),
      erro_comum_pp: num(par.erro_comum_pp),
      reps: num(par.reps),
      nivel_faixa: num(par.nivel_faixa, 90),
      minimo_pst: num(par.minimo_pst, 1),
      metodo: txt(par.metodo),
    },
    motivo_sem_projecao: txtOuNulo(b.motivo_sem_projecao),
    serie: lista(b.serie)
      .filter((p): p is unknown[] => Array.isArray(p))
      .map(p => ({ min: num(p[0]), proj: numOuNulo(p[1]), a: numOuNulo(p[2]), b: numOuNulo(p[3]), obs: numOuNulo(p[4]), pst: num(p[5]) }))
      .sort((p, q) => p.min - q.min),
  });
}

export const NORMALIZADORES: { [K in Rota2T]: (bruto: unknown) => Resposta<Dados2T[K]> } = {
  regioes: normalizarRegioes,
  ufs: normalizarUfs,
  abstencao: normalizarAbstencao,
  estaduais: normalizarEstaduais,
  "evolucao-regiao": normalizarEvolucao,
  "evolucao-uf": normalizarEvolucao,
  pausas: normalizarPausas,
  secoes: normalizarSecoes,
  paralela: normalizarParalela,
  projecao: normalizarProjecao,
};

/** Dados prontos da rota, ou null quando ela ainda não respondeu, está pendente ou falhou. */
export function dadosDe<K extends Rota2T>(respostas: Respostas2T | undefined, rota: K): Dados2T[K] | null {
  const r = respostas?.[rota] as Resposta<Dados2T[K]> | undefined;
  return r && r.situacao === "ok" ? r.dados : null;
}

/** Texto curto de uma fonte sem dados, para o painel da tela ("fonte indisponível" por padrão). */
export function textoSemFonte(respostas: Respostas2T | undefined, rota: Rota2T): string {
  const r = respostas?.[rota];
  if (!r) return "aguardando a fonte";
  if (r.situacao === "pendente") return "fonte indisponível: o servidor ainda não publica esta rota";
  if (r.situacao === "erro") return `fonte indisponível: ${r.mensagem}`;
  return "";
}
