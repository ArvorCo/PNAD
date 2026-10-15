// Validação estrutural do boletim lido dos QR Codes. Não depende da criptografia: confere que
// as somas fecham, que os campos obrigatórios da origem estão presentes e que o boletim é do
// pleito, turno e fase esperados. Devolve a lista de problemas em português; lista vazia significa
// boletim coerente.
import type { BoletimQr, CabecalhoBu, CargoBu } from "./parse.ts";

export interface Problema {
  codigo: string;
  mensagem: string;
}

export interface OpcoesValidacao {
  /** Fase esperada: "O" oficial (padrão), "S" simulado, "T" treinamento. */
  faseEsperada?: "O" | "S" | "T";
  /** Turno esperado (1 ou 2); omitido, aceita qualquer turno válido. */
  turno?: number;
  /** Data do pleito esperada em aaaammdd; omitida, não é conferida. */
  dataPleito?: string;
  /** Número do processo eleitoral esperado (PROC); omitido, não é conferido. */
  processo?: number;
  /** Número do pleito esperado (PLEI); omitido, não é conferido. */
  pleito?: number;
  /** Eleições esperadas: IDEL para a lista de códigos de cargo admitidos nela. */
  eleicoes?: Readonly<Record<number, readonly number[]>>;
  /**
   * Votos que cada eleitor dá no cargo, por código de cargo. Em 2026 o Senado renova duas
   * vagas, então cada eleitor vota duas vezes para o cargo 5 e TOTC chega ao dobro do
   * comparecimento (no exemplo grande do manual, seção 1.5.1: TOTC 762 com APTA 502 e COMP 381).
   * Padrão: { 5: 2 }; cargos ausentes valem 1.
   */
  votosPorEleitor?: Readonly<Record<number, number>>;
}

export const VOTOS_POR_ELEITOR_2026: Readonly<Record<number, number>> = { 5: 2 };

/**
 * Perfil do 2º turno oficial de 25/10/2026, informado pela coordenação do projeto: PROC 1219,
 * PLEI 3221, eleição 6258 (presidente, cargo 1) e eleição 6260 (governador, cargo 3, nos estados
 * com 2º turno). Um boletim pode trazer só a eleição presidencial.
 */
export const PERFIL_2T_2026 = {
  faseEsperada: "O",
  turno: 2,
  dataPleito: "20261025",
  processo: 1219,
  pleito: 3221,
  eleicoes: { 6258: [1], 6260: [3] },
} as const satisfies OpcoesValidacao;

const ORIGENS = new Set(["VOTA", "RED", "SA"]);
const OBRIGATORIOS_COMUNS: (keyof CabecalhoBu)[] = [
  "ORIG", "ORLC", "PROC", "DTPL", "PLEI", "TURN", "FASE", "UNFE", "MUNI", "ZONA", "SECA", "IDUE", "IDCA", "HIQT", "HICA", "VERS",
];
const DA_URNA: (keyof CabecalhoBu)[] = ["LOCA", "APTO", "APTS", "APTT", "COMP", "FALT", "DTAB", "HRAB", "DTFC", "HRFC"];
const OBRIGATORIOS_POR_ORIGEM: Record<string, (keyof CabecalhoBu)[]> = {
  VOTA: DA_URNA,
  RED: [...DA_URNA, "DTEM", "HREM"],
  SA: ["JUNT", "TURM", "DTEM", "HREM"],
};
// Campos exclusivos de outra origem (seção 1.4.2): o Sistema de Apuração não traz dados da urna
// e a urna não traz junta, turma nem emissão.
const PROIBIDOS_POR_ORIGEM: Record<string, (keyof CabecalhoBu)[]> = {
  VOTA: ["JUNT", "TURM", "DTEM", "HREM"],
  RED: ["JUNT", "TURM"],
  SA: ["LOCA", "APTO", "APTS", "APTT", "COMP", "FALT", "HBBM", "HBBG", "HBSB", "DTAB", "HRAB", "DTFC", "HRFC"],
};

/** Data aaaammdd existente no calendário. */
export function dataValida(s: string): boolean {
  const m = /^(\d{4})(\d{2})(\d{2})$/.exec(s);
  if (!m) return false;
  const [a, me, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const dt = new Date(Date.UTC(a, me - 1, d));
  return dt.getUTCFullYear() === a && dt.getUTCMonth() === me - 1 && dt.getUTCDate() === d;
}

/** Hora hhmmss entre 000000 e 235959. */
export function horaValida(s: string): boolean {
  const m = /^(\d{2})(\d{2})(\d{2})$/.exec(s);
  return m !== null && Number(m[1]) <= 23 && Number(m[2]) <= 59 && Number(m[3]) <= 59;
}

function soma(valores: number[]): number {
  return valores.reduce((s, v) => s + v, 0);
}

function nomeCargo(idel: number, c: CargoBu): string {
  return `eleição ${idel}, cargo ${c.CARG}`;
}

function validarCabecalho(h: CabecalhoBu, op: OpcoesValidacao, p: Problema[]): void {
  const add = (codigo: string, mensagem: string): void => {
    p.push({ codigo, mensagem });
  };
  const faltando = OBRIGATORIOS_COMUNS.filter((c) => h[c] === undefined);
  if (h.ORIG !== undefined && !ORIGENS.has(h.ORIG)) add("ORIGEM_DESCONHECIDA", `ORIG "${h.ORIG}" não é VOTA, RED nem SA`);
  if (h.ORIG !== undefined && ORIGENS.has(h.ORIG)) {
    faltando.push(...(OBRIGATORIOS_POR_ORIGEM[h.ORIG] ?? []).filter((c) => h[c] === undefined));
    const proibidos = (PROIBIDOS_POR_ORIGEM[h.ORIG] ?? []).filter((c) => h[c] !== undefined);
    if (proibidos.length > 0) add("CAMPO_DE_OUTRA_ORIGEM", `campos que não pertencem à origem ${h.ORIG}: ${proibidos.join(", ")}`);
  }
  if (faltando.length > 0) add("CAMPO_OBRIGATORIO_AUSENTE", `campos obrigatórios ausentes no cabeçalho: ${faltando.join(", ")}`);

  if (h.ORLC !== undefined && h.ORLC !== "LEG" && h.ORLC !== "COM") add("ORLC_INVALIDO", `ORLC "${h.ORLC}" não é LEG nem COM`);
  const fase = op.faseEsperada ?? "O";
  if (h.FASE !== undefined && h.FASE !== fase) {
    add("FASE_INESPERADA", `fase "${h.FASE}" diferente da esperada "${fase}" (O oficial, S simulado, T treinamento)`);
  }
  if (h.TURN !== undefined && h.TURN !== 1 && h.TURN !== 2) add("TURNO_INVALIDO", `turno ${h.TURN} não é 1 nem 2`);
  if (op.turno !== undefined && h.TURN !== undefined && h.TURN !== op.turno) {
    add("TURNO_INESPERADO", `turno ${h.TURN} diferente do esperado ${op.turno}`);
  }
  if (op.dataPleito !== undefined && h.DTPL !== undefined && h.DTPL !== op.dataPleito) {
    add("DATA_PLEITO_INESPERADA", `data do pleito ${h.DTPL} diferente da esperada ${op.dataPleito}`);
  }
  if (op.processo !== undefined && h.PROC !== undefined && h.PROC !== op.processo) {
    add("PROCESSO_INESPERADO", `processo eleitoral ${h.PROC} diferente do esperado ${op.processo}`);
  }
  if (op.pleito !== undefined && h.PLEI !== undefined && h.PLEI !== op.pleito) {
    add("PLEITO_INESPERADO", `pleito ${h.PLEI} diferente do esperado ${op.pleito}`);
  }
  if (h.UNFE !== undefined && !/^[A-Z]{2}$/.test(h.UNFE)) add("UF_INVALIDA", `UNFE "${h.UNFE}" não é sigla de duas letras`);
  for (const c of ["DTPL", "DTAB", "DTFC", "DTEM"] as const) {
    const v = h[c];
    if (v !== undefined && !dataValida(v)) add("DATA_INVALIDA", `${c} "${v}" não é data aaaammdd válida`);
  }
  for (const c of ["HRAB", "HRFC", "HREM"] as const) {
    const v = h[c];
    if (v !== undefined && !horaValida(v)) add("HORA_INVALIDA", `${c} "${v}" não é hora hhmmss válida`);
  }
  if (h.DTAB !== undefined && h.DTPL !== undefined && h.DTAB !== h.DTPL) {
    add("ABERTURA_FORA_DO_DIA", `urna aberta em ${h.DTAB}, mas o pleito é em ${h.DTPL}`);
  }
  if (h.DTAB && h.HRAB && h.DTFC && h.HRFC && `${h.DTFC}${h.HRFC}` < `${h.DTAB}${h.HRAB}`) {
    add("FECHAMENTO_ANTES_DA_ABERTURA", `fechamento ${h.DTFC} ${h.HRFC} anterior à abertura ${h.DTAB} ${h.HRAB}`);
  }
  if (h.IDCA !== undefined && !/^\d{24}$/.test(h.IDCA)) add("IDCA_INVALIDO", "IDCA não tem 24 dígitos");
  if (h.VERS !== undefined && !/^\d+(\.\d+)*$/.test(h.VERS)) add("VERSAO_SOFTWARE_INVALIDA", `VERS "${h.VERS}" fora do formato numérico`);
  if (h.HICA !== undefined) {
    if (h.HIQT !== undefined && h.HICA.length !== h.HIQT) {
      add("HISTORICO_CARGA_INCONSISTENTE", `HIQT ${h.HIQT}, mas há ${h.HICA.length} registros HICA`);
    }
    if (h.HICA.some((r, i) => r.sequencia !== i + 1)) add("HISTORICO_CARGA_INCONSISTENTE", "sequências HICA fora da ordem 1, 2, 3...");
    const ultima = h.HICA[h.HICA.length - 1];
    if (ultima && h.IDCA !== undefined && ultima.codigo !== h.IDCA) {
      add("HISTORICO_CARGA_INCONSISTENTE", "o último código de carga do histórico difere de IDCA");
    }
  }
  if (h.AGRE !== undefined) {
    if (new Set(h.AGRE).size !== h.AGRE.length) add("AGREGADAS_REPETIDAS", "seção agregada repetida em AGRE");
    if (h.SECA !== undefined && h.AGRE.includes(h.SECA)) add("AGREGADAS_REPETIDAS", "AGRE contém a própria seção");
  }
  if (h.APTO !== undefined) {
    if (h.APTS !== undefined && h.APTT !== undefined && h.APTS + h.APTT !== h.APTO) {
      add("APTOS_NAO_FECHAM", `APTS ${h.APTS} + APTT ${h.APTT} ≠ APTO ${h.APTO}`);
    }
    if (h.COMP !== undefined && h.COMP > h.APTO) add("COMPARECIMENTO_ACIMA_DE_APTOS", `COMP ${h.COMP} maior que APTO ${h.APTO}`);
    if (h.COMP !== undefined && h.FALT !== undefined && h.COMP + h.FALT !== h.APTO) {
      add("COMPARECIMENTO_NAO_FECHA", `COMP ${h.COMP} + FALT ${h.FALT} ≠ APTO ${h.APTO}`);
    }
  }
  if (h.COMP !== undefined && h.HBBM !== undefined && h.HBBG !== undefined && h.HBSB !== undefined) {
    const habilitados = h.HBBM + h.HBBG + h.HBSB;
    if (habilitados > h.COMP) add("HABILITADOS_ACIMA_DO_COMPARECIMENTO", `HBBM + HBBG + HBSB = ${habilitados}, maior que COMP ${h.COMP}`);
  }
}

function validarCargo(idel: number, c: CargoBu, h: CabecalhoBu, op: OpcoesValidacao, p: Problema[]): void {
  const nome = nomeCargo(idel, c);
  const add = (codigo: string, mensagem: string): void => {
    p.push({ codigo, mensagem: `${nome}: ${mensagem}` });
  };
  if (c.TIPO === undefined || c.TIPO < 0 || c.TIPO > 2) add("TIPO_CARGO_INVALIDO", `TIPO ${c.TIPO ?? "ausente"} (esperado 0, 1 ou 2)`);
  if (c.VERC === undefined) add("CAMPO_OBRIGATORIO_AUSENTE", "VERC ausente");
  const proporcional = c.TIPO === 1;
  const obrigatorios: (keyof CargoBu)[] = ["APTA", "APTS", "APTT", "NOMI", "BRAN", "NULO", "TOTC"];
  if (proporcional) obrigatorios.push("LEGC");
  const faltando = obrigatorios.filter((k) => c[k] === undefined);
  if (faltando.length > 0) add("CAMPO_OBRIGATORIO_AUSENTE", `resumo sem ${faltando.join(", ")}`);
  if (!proporcional && c.LEGC !== undefined) add("LEGENDA_EM_CARGO_NAO_PROPORCIONAL", "LEGC em cargo que não é proporcional");
  if (proporcional && c.votos.length > 0) add("VOTO_FORA_DE_PARTIDO", "voto nominal fora de bloco de partido em cargo proporcional");
  if (!proporcional && c.partidos.length > 0) add("PARTIDO_EM_CARGO_NAO_PROPORCIONAL", "bloco PART em cargo que não é proporcional");

  const todos = [...c.votos, ...c.partidos.flatMap((pt) => pt.votos)];
  const numeros = todos.map((v) => v.numero);
  if (new Set(numeros).size !== numeros.length) add("CANDIDATO_REPETIDO", "o mesmo número aparece mais de uma vez");
  const partidos = c.partidos.map((pt) => pt.PART);
  if (new Set(partidos).size !== partidos.length) add("PARTIDO_REPETIDO", "o mesmo partido aparece mais de uma vez");

  const nominais = soma(todos.map((v) => v.votos));
  if (c.NOMI !== undefined && nominais !== c.NOMI) add("NOMINAIS_NAO_FECHAM", `soma dos votos nominais ${nominais} ≠ NOMI ${c.NOMI}`);
  for (const pt of c.partidos) {
    if (pt.LEGP === undefined || pt.TOTP === undefined) {
      add("CAMPO_OBRIGATORIO_AUSENTE", `partido ${pt.PART} sem LEGP ou TOTP`);
      continue;
    }
    const total = soma(pt.votos.map((v) => v.votos)) + pt.LEGP;
    if (total !== pt.TOTP) add("PARTIDO_NAO_FECHA", `partido ${pt.PART}: nominais + LEGP = ${total} ≠ TOTP ${pt.TOTP}`);
    const fora = pt.votos.filter((v) => !String(v.numero).startsWith(String(pt.PART)));
    if (fora.length > 0) add("CANDIDATO_FORA_DO_PARTIDO", `partido ${pt.PART} contém ${fora.map((v) => v.numero).join(", ")}`);
  }
  if (proporcional && c.LEGC !== undefined) {
    const legendas = soma(c.partidos.map((pt) => pt.LEGP ?? 0));
    if (legendas !== c.LEGC) add("LEGENDA_NAO_FECHA", `soma de LEGP ${legendas} ≠ LEGC ${c.LEGC}`);
  }
  if (c.NOMI !== undefined && c.BRAN !== undefined && c.NULO !== undefined && c.TOTC !== undefined) {
    const total = c.NOMI + (c.LEGC ?? 0) + c.BRAN + c.NULO;
    if (total !== c.TOTC) {
      add("TOTAL_NAO_FECHA", `NOMI ${c.NOMI}${proporcional ? ` + LEGC ${c.LEGC ?? 0}` : ""} + BRAN ${c.BRAN} + NULO ${c.NULO} = ${total} ≠ TOTC ${c.TOTC}`);
    }
  }
  if (c.APTA !== undefined && c.APTS !== undefined && c.APTT !== undefined && c.APTS + c.APTT !== c.APTA) {
    add("APTOS_NAO_FECHAM", `APTS ${c.APTS} + APTT ${c.APTT} ≠ APTA ${c.APTA}`);
  }
  const vagas = (op.votosPorEleitor ?? VOTOS_POR_ELEITOR_2026)[c.CARG] ?? 1;
  if (c.TOTC !== undefined && c.APTA !== undefined && c.TOTC > c.APTA * vagas) {
    add("TOTAL_ACIMA_DE_APTOS", `TOTC ${c.TOTC} maior que APTA ${c.APTA}${vagas > 1 ? ` × ${vagas} votos por eleitor` : ""}`);
  }
  if (c.TOTC !== undefined && h.COMP !== undefined && c.TOTC > h.COMP * vagas) {
    add("TOTAL_ACIMA_DO_COMPARECIMENTO", `TOTC ${c.TOTC} maior que COMP ${h.COMP}${vagas > 1 ? ` × ${vagas} votos por eleitor` : ""}`);
  }
  if (c.APTA !== undefined && h.APTO !== undefined && c.APTA > h.APTO) add("APTOS_DO_CARGO_ACIMA_DA_SECAO", `APTA ${c.APTA} maior que APTO ${h.APTO}`);
}

/** Confere a coerência interna do boletim e devolve os problemas encontrados. */
export function validarBoletim(bu: BoletimQr, opcoes: OpcoesValidacao = {}): Problema[] {
  const problemas: Problema[] = [];
  const h = bu.cabecalho;
  validarCabecalho(h, opcoes, problemas);
  const idels = bu.eleicoes.map((e) => e.IDEL);
  if (new Set(idels).size !== idels.length) problemas.push({ codigo: "ELEICAO_REPETIDA", mensagem: "o mesmo IDEL aparece mais de uma vez" });
  for (const e of bu.eleicoes) {
    if (e.cargos.length === 0) problemas.push({ codigo: "ELEICAO_SEM_CARGO", mensagem: `eleição ${e.IDEL} sem nenhum cargo` });
    const cargos = e.cargos.map((c) => c.CARG);
    if (new Set(cargos).size !== cargos.length) {
      problemas.push({ codigo: "CARGO_REPETIDO", mensagem: `eleição ${e.IDEL}: o mesmo cargo aparece mais de uma vez` });
    }
    if (h.ORIG !== undefined && h.ORIG !== "SA" && (e.MAJO !== undefined || e.PROP !== undefined)) {
      problemas.push({ codigo: "CAMPO_DE_OUTRA_ORIGEM", mensagem: `eleição ${e.IDEL}: MAJO e PROP são exclusivos do Sistema de Apuração` });
    }
    const admitidos = opcoes.eleicoes?.[e.IDEL];
    if (opcoes.eleicoes !== undefined && admitidos === undefined) {
      problemas.push({ codigo: "ELEICAO_INESPERADA", mensagem: `eleição ${e.IDEL} fora das esperadas (${Object.keys(opcoes.eleicoes).join(", ")})` });
    }
    for (const c of e.cargos) {
      if (admitidos !== undefined && !admitidos.includes(c.CARG)) {
        problemas.push({ codigo: "CARGO_INESPERADO", mensagem: `eleição ${e.IDEL}: cargo ${c.CARG} fora dos esperados (${admitidos.join(", ")})` });
      }
      validarCargo(e.IDEL, c, h, opcoes, problemas);
    }
  }
  for (const d of bu.camposDesconhecidos) {
    problemas.push({ codigo: "CAMPO_DESCONHECIDO", mensagem: `campo ${d.chave}:${d.valor} desconhecido (${d.contexto}, registro ${d.posicao})` });
  }
  return problemas;
}
