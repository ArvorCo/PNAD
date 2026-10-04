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
    default:
      return `${tipo.replaceAll("_", " ")} em ${onde}${cargo}`;
  }
}

export type Categoria = "virada" | "regressao" | "fechou" | "atraso" | "outro";

export function categoria(tipo: string): Categoria {
  if (tipo === "virada") return "virada";
  if (tipo.startsWith("regressao") || tipo === "idg_regressivo") return "regressao";
  if (tipo === "municipio_finalizado" || tipo === "fechou" || tipo === "uf_fechou") return "fechou";
  if (tipo === "atraso" || tipo === "skew_relogio") return "atraso";
  return "outro";
}
