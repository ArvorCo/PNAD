// Tipos dos JSON gerados (CONTRATO.md, seções 3 a 6). Quem muda um esquema muda o contrato
// primeiro e depois este arquivo.

export type Nivel = "alta" | "media" | "baixa";
/** Contagem de seções por nível de atenção dos logs (0 a 3), com chave em texto como no JSON. */
export type PorAtencao = Record<"0" | "1" | "2" | "3", number>;

// ---------------------------------------------------------------- sete_riscos.json (seção 3)

export type Urna = {
  flavio_pct: number;
  lula_pct: number;
  diferenca_pp: number;
  diferenca_votos: number;
  secoes: number;
  eleitores: number;
  comparecimento_pct: number;
};

/** O que os dados mostram de cada risco: deixa rastro, rastro parcial ou nenhum. */
export type Sinal = "nenhum" | "parcial" | "deixa";

export type IdRisco = "boca_urna" | "compra" | "transporte" | "medo" | "mesario" | "pianista" | "totalizacao";

export type DispositivoLei = {
  id: string;
  norma: string;
  dispositivo: string;
  resumo: string;
  pena: string | null;
};

export type FonteCaso = {
  id: string;
  url: string;
  veiculo: string;
  data: string;
  titulo: string;
  /** Verdadeiro quando a página não traz data de publicação e `data` é a data de acesso. */
  data_e_acesso: boolean;
};

export type Caso = {
  id: string;
  ano: number;
  titulo: string;
  local: string;
  instancia: string;
  resultado_curto: string;
  rotulo_curto: string;
  fonte: FonteCaso;
};

export type RiscoDados = {
  id: IdRisco;
  /** Id da cena no roteiro (`risco-*`). */
  cena: string;
  nome: string;
  familia: string;
  o_que_e: string;
  como_aparece: string;
  sinal: Sinal;
  sinal_texto: string;
  confere: string;
  lei: DispositivoLei[];
  /** O primeiro é o caso principal. */
  casos: Caso[];
  /** Só os números que o roteiro cita; chave = id do caso do MJ. */
  numeros: Record<string, number>;
};

export type BalancoMj = {
  "1t_2024": {
    boca_urna: number;
    compra: number;
    veiculos_transporte: number;
    presos: number;
    apreendido_reais: number;
    fonte_caso: string;
  };
  "1t_2022": {
    boca_urna: number;
    compra: number;
    transporte: number;
    presos: number;
    crimes: number;
    fonte_caso: string;
  };
};

export type IdLeiFiscal = "fiscalizar" | "dois" | "credencial" | "impugnar" | "copia" | "ate_a_junta";
export type IdFechamento = "senhas" | "ultimos_dois" | "bu_afixado" | "copia_no_encerramento" | "comparar_depois";

export type ItemLei<Id extends string = string> = { id: Id; texto: string; referencia: string };

/** Seção do país com resultado do 1º turno (mapa de fiscais, completada pelo capítulo 13). */
export type SecaoResultado = {
  uf: string;
  municipio: string;
  zona: number;
  secao: number;
  aptos: number;
  votantes: number;
  comparecimento_pct: number;
  lula_pct: number;
  flavio_pct: number;
  nivel: Nivel | null;
  criterios: string[];
  explicacao: string | null;
};

/**
 * Seção nomeada no roteiro (CONTRATO.md, chaves obrigatórias de `exemplos`). Os percentuais da
 * zona são opcionais: o contrato não os exige, e o `CartaoSecao` só desenha o marcador se vierem.
 */
export type Exemplo = SecaoResultado & {
  local: string;
  bairro: string;
  logs: string[];
  atencao: number | null;
  o_que_conferir: string | null;
  zona_lula_pct?: number | null;
  zona_flavio_pct?: number | null;
};

export type ChaveExemplo =
  | "tabatinga_am"
  | "baiao_pa"
  | "puc_sp"
  | "sao_joao_missoes_mg"
  | "marau_rs"
  | "porto_acre_ac"
  | "frente_1"
  | "frente_2"
  | "frente_3";

export type LulaFrente = {
  secoes_lula_90: number;
  secoes_lula_80_comp_95: number;
  secoes_flavio_90: number;
  /** Até 12 seções, por nível (alta, media, baixa, null) e depois por `lula_pct`. */
  lista: SecaoResultado[];
};

/** Seção listada de um prédio; opcional no contrato (a grade usa `por_atencao` se faltar). */
export type SecaoPredio = {
  secao: number;
  nivel: Nivel | null;
  atencao: number;
  logs: string[];
  /** Seção com menos de 30 aptos não mostra voto (regra do Politize): pode vir nulo. */
  comparecimento: number | null;
  flavio_pct: number | null;
  lula_pct: number | null;
};

export type ChavePredio = "RJ-60011-233-1414";

export type Predio = {
  local_id: string;
  uf: string;
  municipio: string;
  zona: number;
  local: string;
  bairro: string;
  secoes_total: number;
  aptos_total: number;
  lula_pct: number;
  flavio_pct: number;
  por_atencao: PorAtencao;
  secoes?: SecaoPredio[];
};

export type Sinalizadas = { secoes: number; locais: number; alta: number; media: number; baixa: number };

export type Logs = { processados: number; atencao: PorAtencao };

export type MapaUf = { uf: string; d: string };

export type Cadastro = { site: string; prazo: string; fonte: string };

export type Dados = {
  gerado_em: string;
  /** Caminho do arquivo lido → SHA-256. */
  fontes: Record<string, string>;
  urna: Urna;
  /** Exatamente sete, na ordem do capítulo 2. */
  riscos: RiscoDados[];
  balanco_mj: BalancoMj;
  lei_fiscal: ItemLei<IdLeiFiscal>[];
  fechamento: ItemLei<IdFechamento>[];
  exemplos: Record<ChaveExemplo, Exemplo>;
  lula_frente: LulaFrente;
  predios: Predio[];
  sinalizadas: Sinalizadas;
  logs: Logs;
  mapa: { view: number; ufs: MapaUf[] };
  totalizacao: { exemplos_oficiais: number };
  cadastro: Cadastro;
};

// ---------------------------------------------------------------- midia.json (seção 4)

export type FormatoMidia = "16x9" | "9x16";

export type ItemMidia = {
  tipo: "video" | "imagem";
  formatos: FormatoMidia[];
  segundos: number;
};

export type Midia = Record<string, ItemMidia | undefined>;

// ---------------------------------------------------------------- capturas.json (seção 5)

export type Captura = {
  formatos: FormatoMidia[];
  segundos: number;
  /** Nome do still → segundo da gravação em que foi tirado. */
  stills: Record<string, number>;
};

export type Capturas = Record<string, Captura | undefined>;

// ---------------------------------------------------------------- musica.json e voz.json (seção 6)

export type FaixaMusica = { arquivo: string; segundos: number; prompt: string };

/** Uma faixa por capítulo, chave = id do capítulo; capítulo sem faixa fica em silêncio. */
export type Musica = Record<string, FaixaMusica | undefined>;

export type Palavra = { w: string; t: number; f: number };

export type CenaVoz = {
  id: string;
  arquivo: string;
  segundos: number;
  texto: string;
  palavras: Palavra[];
};

export type Voz = { modelo: string; cenas: CenaVoz[] };
