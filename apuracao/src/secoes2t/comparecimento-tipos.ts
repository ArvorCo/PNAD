// Contrato de /api/2t/comparecimento (vigilância de falso comparecimento): tipos compartilhados
// pelo servidor, pelo exportador e pelo telão. Cálculo em ./comparecimento.ts.

export const ROTULO_COMPARECIMENTO =
  "Sinal pede explicação, não prova irregularidade; a extensão até 19h eleva o comparecimento legitimamente.";

/** Regras declaradas dos sinais (todas por seção, contra a própria seção ou o município no 1º turno). */
export const REGRAS_COMPARECIMENTO = {
  /** comparecimento da seção no 2T menos o da mesma seção no 1T, em pontos percentuais */
  delta_pp_min: 5,
  /** parcela sem biometria ≥ fator × mediana do município no 1T ... */
  sem_bio_fator: 2,
  /** ... e ≥ este piso, em % do comparecimento */
  sem_bio_min_pct: 10,
  /** descrição (fora do escore): encerramento depois desta hora de Brasília */
  tarde_hhmm: "17:00",
  /** tardia também quando encerra depois desta hora de Brasília */
  apos_hhmm: "19:00",
  /** tardia: encerramento ao menos estes minutos depois do da própria seção no 1T */
  tardia_min_vs_1t: 30,
  /** tipo_arquivo do BU a partir do qual o boletim vem do sistema de apuração (cédula) */
  papel_tipo_min: 3,
  /** camada municipal: só municípios com ao menos esta parcela de seções apuradas */
  mun_pst_min: 30,
} as const;

export interface SinaisSecao {
  delta: boolean;
  sem_bio: boolean;
  tardia: boolean;
  papel: boolean;
}

export interface SecaoComparecimento {
  /** sigla em caixa alta */
  uf: string;
  /** código TSE com 5 dígitos */
  mun: string;
  nm: string;
  zona: number;
  secao: number;
  lat: number | null;
  lon: number | null;
  aptos: number | null;
  comp: number | null;
  /** comparecimento / aptos × 100, 2 casas */
  taxa_comp: number | null;
  taxa_comp_1t: number | null;
  delta_pp: number | null;
  /** compareceram sem biometria / comparecimento × 100 */
  sem_bio_pct: number | null;
  sem_bio_pct_1t: number | null;
  /** mediana da parcela sem biometria nas seções do município no 1T */
  sem_bio_mun_p50_1t: number | null;
  /** habilitados por ano de nascimento (biografia) / comparecimento × 100 */
  ano_nasc_pct: number | null;
  /** hora de Brasília do encerramento (último voto), hh:mm */
  encerramento_hhmm: string | null;
  /** hora de Brasília do encerramento da mesma seção no 1T, hh:mm */
  enc1_hhmm: string | null;
  /** encerramento ≥ 30 min depois do da própria seção no 1T, ou depois das 19:00 */
  tardia: boolean;
  /** descrição: hh:mm depois de 17:00 (no 1T, 92,38% das seções) */
  encerrou_apos_17h: boolean;
  apos_19h: boolean;
  /** BU do sistema de apuração (tipo_arquivo ≥ 3): votação em cédula */
  papel: boolean;
  tipo_arquivo: number | null;
  /** 1 seção, 3 contingência, 4 reserva da seção, 6 reserva encerrando a seção */
  tipo_urna: number | null;
  /** tamanho do histórico de códigos de carga (mais de 1 = urna recarregada ou trocada) */
  n_cargas: number | null;
  /** tipo_urna 3, 4 ou 6, ou mais de uma carga: urna substituída ou de contingência (fora do escore) */
  contingencia: boolean;
  /** Flávio / (Flávio + Lula) × 100 no BU do 2T */
  fatia_flavio: number | null;
  /** a mesma razão na mesma seção no 1T */
  fatia_flavio_1t: number | null;
  recebido_hhmm: string | null;
  origem: "amostra" | "paralela";
  sinais: SinaisSecao;
  /** soma dos quatro sinais (0 a 4) */
  escore: number;
}

export interface MunicipioComparecimento {
  uf: string;
  cd: string;
  nm: string;
  lat: number | null;
  lon: number | null;
  te: number;
  pst: number;
  /** comparecimento / (comparecimento + abstenção) nas seções já apuradas, × 100 */
  taxa_2t: number;
  /** 100 − pa do município no 1T */
  taxa_1t: number;
  delta_pp: number;
}

export interface Distribuicao {
  n: number;
  p50: number | null;
  p90: number | null;
}

export interface ContagemSinais {
  delta: number;
  sem_bio: number;
  /** descrição: encerradas depois das 17:00 (fora do escore) */
  tarde: number;
  tardia: number;
  apos_19h: number;
  papel: number;
  contingencia: number;
  escore_2_mais: number;
}

/**
 * Votos da prorrogação: seções tardias (encerramento ≥ 30 min depois do da própria seção no 1T, ou
 * depois das 19:00) contra a própria seção no 1T e contra as demais do mesmo município (pontuais). Deltas de fatia só
 * com n ≥ n_min; abaixo disso ficam null.
 */
export interface BlocoProrrogacao {
  uf: string;
  n_tardias: number;
  n_apos_19h: number;
  n_pontuais: number;
  /** média simples de delta_pp (2T − 1T na própria seção) */
  delta_comp_tardias: number | null;
  delta_comp_pontuais: number | null;
  /** tardias com régua do 1T e votos nos dois turnos */
  n_vs_1t: number;
  /** fatia de Flávio 2T − 1T nas tardias, ponderada pelos votos dos dois no 2T */
  delta_fatia_vs_1t_pp: number | null;
  /** tardias em municípios que também têm pontuais */
  n_vs_pontuais: number;
  /** fatia nas tardias − fatia nas pontuais do mesmo município, média ponderada pelos votos das tardias */
  delta_fatia_vs_pontuais_pp: number | null;
}

/** Ponto do mapa: [lon, lat, delta_pp | null, escore, aptos, contingência 0/1] */
export type PontoSecao = readonly [number, number, number | null, number, number, number];

export interface ComparecimentoOut {
  at: string;
  min: number | null;
  rotulo: string;
  regras: typeof REGRAS_COMPARECIMENTO;
  referencia: {
    secoes: boolean;
    gerado_em: string | null;
    municipios: boolean;
    /** linha de base: % das seções do 1T com encerramento (hh:mm) depois de 17:00, 18:00 e 19:00 */
    enc_1t_pct: { apos_1700: number | null; apos_1800: number | null; apos_1900: number | null };
  };
  totais: { recebidas: number; com_ref_1t: number; com_coord: number; amostra: number; paralela: number };
  sinais: ContagemSinais;
  delta: Distribuicao;
  por_uf: (ContagemSinais & { uf: string; recebidas: number; delta_dist: Distribuicao })[];
  pontos: PontoSecao[];
  /** as 30 seções de maior escore (desempate: maior delta) */
  top: SecaoComparecimento[];
  /** até 50 seções com urna de contingência, reserva ou mais de uma carga */
  contingencia: SecaoComparecimento[];
  prorrogacao: { n_min: number; brasil: BlocoProrrogacao; por_uf: BlocoProrrogacao[] };
  municipios: MunicipioComparecimento[];
  municipios_uf: { uf: string; n: number; delta: Distribuicao }[];
  municipios_delta: Distribuicao;
  /** os 30 municípios de maior delta positivo */
  municipios_top: MunicipioComparecimento[];
}
