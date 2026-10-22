// Frases curtas em pt-BR para eventos e anomalias do telão e da auditoria.
import { nomeCargo, nomeUf, titulo } from "./abr.ts";
import type { MunicipioInfo } from "./consultas.ts";

export interface EscopoEvento {
  nivel: string | null;
  uf: string | null;
  municipio_cd: string | null;
  zona_cd: string | null;
  cargo_cd: number | null;
}

/** "19:38" no horário de Brasília (deslocamento fixo de -03:00). */
export function horaBrt(iso: string | null): string {
  if (!iso) return "";
  const t = Date.parse(iso);
  if (!Number.isFinite(t)) return "";
  const d = new Date(t - 3 * 3600_000);
  return `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
}

export function nomeEscopoEvento(e: EscopoEvento, muns: ReadonlyMap<string, MunicipioInfo>, curto = false): string {
  if (e.uf === null || e.nivel === "br") return e.uf === null ? "Brasil" : nomeUf(e.uf);
  const uf = e.uf;
  if (e.municipio_cd === null) return curto ? uf.toUpperCase() : nomeUf(uf);
  const m = muns.get(e.municipio_cd);
  const mun = m?.nome ? `${titulo(m.nome)} (${uf.toUpperCase()})` : `${uf}${e.municipio_cd}`;
  return e.zona_cd === null ? mun : `zona ${Number(e.zona_cd)} de ${mun}`;
}

const CAMPOS_CONTAGEM: Readonly<Record<string, string>> = {
  st: "seções",
  pst: "percentual de seções",
  vvc: "votos válidos",
  vv: "votos válidos",
  vnom: "votos nominais",
  tv: "votos totais",
  comparecimento: "comparecimento",
  est: "eleitorado apurado",
  vap: "votos de candidatura",
};

type Detalhe = Record<string, unknown>;

const num = (d: Detalhe, k: string): number | null => {
  const v = d[k];
  return typeof v === "number" && Number.isFinite(v) ? v : null;
};

/** 12,3 (vírgula decimal, uma ou duas casas). */
export function decimal(v: number | null, casas = 1): string {
  if (v === null) return "";
  return v.toFixed(casas).replace(".", ",");
}

/** "29,6 min" ou "7 min" (inteiro quando não há fração). */
function minutos(v: number | null): string {
  if (v === null) return "";
  return Number.isInteger(v) ? `${v} min` : `${decimal(v)} min`;
}

function secaoTxt(d: Detalhe, e: EscopoEvento, muns: ReadonlyMap<string, MunicipioInfo>): string {
  const sec = txt(d, "secao");
  const z = e.zona_cd !== null ? Number(e.zona_cd) : null;
  const mun = nomeEscopoEvento({ ...e, zona_cd: null }, muns);
  return `seção ${sec ?? "?"}${z !== null ? ` da zona ${z}` : ""} de ${mun}`;
}

const txt = (d: Detalhe, ...k: string[]): string | null => {
  for (const c of k) {
    const v = d[c];
    if (typeof v === "string" && v !== "") return v;
    if (typeof v === "number") return String(v);
  }
  return null;
};

function campoContagem(d: Detalhe): string {
  const c = txt(d, "campo", "campos");
  if (c && CAMPOS_CONTAGEM[c]) return CAMPOS_CONTAGEM[c];
  const lista = Array.isArray(d.campos) ? d.campos.filter((x): x is string => typeof x === "string") : [];
  const primeiro = lista[0];
  return primeiro && CAMPOS_CONTAGEM[primeiro] ? CAMPOS_CONTAGEM[primeiro] : "contagem";
}

/** Frase de um evento a partir do tipo e do detalhe gravado. */
export function textoEvento(tipo: string, em: string, e: EscopoEvento, detalhe: unknown, muns: ReadonlyMap<string, MunicipioInfo>): string {
  const d: Detalhe = detalhe !== null && typeof detalhe === "object" ? (detalhe as Detalhe) : {};
  const onde = nomeEscopoEvento(e, muns);
  const cargo = e.cargo_cd !== null ? ` (${nomeCargo(e.cargo_cd).nome.toLocaleLowerCase("pt-BR")})` : "";
  switch (tipo) {
    case "virada": {
      const de = txt(d, "de_nome", "de");
      const para = txt(d, "para_nome", "para");
      return de && para ? `Virada em ${nomeEscopoEvento(e, muns, true)}: ${para} passa ${de}` : `Virada em ${onde}${cargo}`;
    }
    case "regressao_contagem":
      return `Regressão de ${campoContagem(d)} em ${onde}${cargo}`;
    case "regressao_pst":
      return `Regressão do percentual de seções em ${onde}${cargo}`;
    case "idg_regressivo":
      return `Cópia antiga do CDN em ${onde}${cargo}`;
    case "municipio_finalizado":
      return `${onde} terminou a apuração às ${horaBrt(txt(d, "totalizado_em") ?? em)}`;
    case "fechou":
    case "uf_fechou":
      return `${onde} fechou às ${horaBrt(txt(d, "totalizado_em") ?? em)}`;
    case "candidato_novo":
      return `Candidatura nova em ${onde}${cargo}`;
    case "candidato_sumiu":
      return `Candidatura sumiu em ${onde}${cargo}`;
    case "eleito_mudou":
      return `Situação de eleição mudou em ${onde}${cargo}`;
    case "municipio_desconhecido":
      return `Município fora do cadastro em ${onde}`;
    case "schema_drift":
      return `Formato novo de arquivo em ${onde}${cargo}`;
    case "parse_error":
      return `Falha ao ler arquivo de ${onde}${cargo}`;
    case "e_file_appeared":
      return `Arquivo agregado apareceu em ${onde}${cargo}`;
    case "skew_relogio":
      return `Relógio local desviado ${txt(d, "skew_s", "s") ?? ""} s do TSE`.replace("  ", " ");
    case "sweep_inicio":
      return "Varredura completa iniciada";
    case "sweep_fim":
      return "Varredura completa concluída";
    case "shutdown":
      return "Coletor desligado";
    case "atraso":
      return `Atraso na divulgação de ${onde}${cargo}`;
    case "pausa_nacional_inicio":
      return `Arquivo nacional sem versão nova desde ${horaBrt(txt(d, "desde"))} (${minutos(num(d, "minutos"))})`;
    case "pausa_nacional_longa":
      return `Arquivo nacional segue sem versão nova desde ${horaBrt(txt(d, "desde"))} (${minutos(num(d, "minutos"))})`;
    case "pausa_nacional_fim":
      return `Arquivo nacional voltou a publicar às ${horaBrt(txt(d, "ate") ?? em)}, após ${minutos(num(d, "minutos"))} sem versão nova`;
    case "pausa_geral_inicio":
      return `Nenhum arquivo do TSE com versão nova desde ${horaBrt(txt(d, "desde"))} (${minutos(num(d, "minutos"))})`;
    case "pausa_geral_longa":
      return `Divulgação do TSE segue sem versão nova desde ${horaBrt(txt(d, "desde"))} (${minutos(num(d, "minutos"))})`;
    case "pausa_geral_fim":
      return `Divulgação do TSE voltou às ${horaBrt(txt(d, "ate") ?? em)}, após ${minutos(num(d, "minutos"))} sem versão nova`;
    case "pausa_uf_inicio":
      return `${onde} sem versão nova desde ${horaBrt(txt(d, "desde"))} (${minutos(num(d, "minutos"))})`;
    case "pausa_uf_fim":
      return `${onde} voltou a publicar às ${horaBrt(txt(d, "ate") ?? em)}, após ${minutos(num(d, "minutos"))} sem versão nova`;
    case "soma_ufs_adiante":
      return `Soma das UFs ${decimal(num(d, "diferenca_pct"))}% à frente do arquivo nacional`;
    case "uf_atrasada_1t":
      return `${onde} ${num(d, "patamar_min") ?? ""} min atrás do ritmo do 1º turno`;
    case "abstencao_atipica_mun":
      return `Abstenção em ${onde}: ${decimal(num(d, "pa_2t"))}% contra ${decimal(num(d, "pa_1t"))}% no 1º turno`;
    case "abstencao_atipica_uf":
      return `${onde}: abstenção de ${decimal(num(d, "pa_2t"))}% contra ${decimal(num(d, "pa_1t_mesmos"))}% no 1º turno nos municípios fechados`;
    case "secao_tardia":
      return `${secaoTxt(d, e, muns)} encerrou às ${txt(d, "encerramento_hhmm") ?? horaBrt(txt(d, "encerramento_iso"))}`.replace(/^s/, "S");
    case "divergencia_paralela":
      return `BU da totalização paralela difere do oficial na ${secaoTxt(d, e, muns)}`;
    case "paralela_conferida": {
      const n = num(d, "conferidos") ?? 0;
      return `Totalização paralela: ${n} ${n === 1 ? "BU conferido" : "BUs conferidos"}, ${num(d, "iguais") ?? 0} iguais e ${num(d, "divergentes") ?? 0} com diferença`;
    }
    default:
      return `${tipo.replaceAll("_", " ")} em ${onde}${cargo}`;
  }
}

export type Categoria = "virada" | "regressao" | "fechou" | "atraso" | "pausa" | "divergencia" | "abstencao" | "paralela" | "outro";

export function categoria(tipo: string): Categoria {
  if (tipo === "virada") return "virada";
  if (tipo.startsWith("regressao") || tipo === "idg_regressivo") return "regressao";
  if (tipo === "municipio_finalizado" || tipo === "fechou" || tipo === "uf_fechou") return "fechou";
  if (tipo === "atraso" || tipo === "skew_relogio" || tipo === "uf_atrasada_1t" || tipo === "secao_tardia") return "atraso";
  if (tipo.startsWith("pausa_nacional_") || tipo.startsWith("pausa_uf_") || tipo.startsWith("pausa_geral_") || tipo === "soma_ufs_adiante") return "pausa";
  if (tipo === "divergencia_paralela") return "divergencia";
  if (tipo === "abstencao_atipica_mun" || tipo === "abstencao_atipica_uf") return "abstencao";
  if (tipo === "paralela_conferida") return "paralela";
  return "outro";
}
