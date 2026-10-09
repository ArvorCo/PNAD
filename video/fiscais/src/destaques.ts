import { decimal, hora, inteiro } from "./componentes/util";
import { COR } from "./tema";
import type { Criterio, Dados } from "./tipos";

export type Destaque = {
  /** Número animado (number) ou texto fixo (string, por exemplo uma hora). */
  valor: number | string;
  casas?: number;
  prefixo?: string;
  sufixo?: string;
  rotulo: string;
  legenda: string;
  cor: string;
};

/** Palavras da narração que disparam o cartão, o número grande e a caixa "o que conferir". */
export const GATILHOS: Record<string, { cartao: string; numero: string; conferir: string }> = {
  a: { cartao: "Pinheiro", numero: "vinte", conferir: "confere" },
  b: { cartao: "Almeirim", numero: "zero", conferir: "método" },
  c: { cartao: "Baião", numero: "cem", conferir: "resolve" },
  d: { cartao: "Igarapé", numero: "vinte", conferir: "separa" },
  e: { cartao: "Ervália", numero: "trinta", conferir: "resolve" },
  f: { cartao: "São", numero: "duas", conferir: "exige" },
  g: { cartao: "Juruti", numero: "meio-dia", conferir: "confere" },
  h: { cartao: "Vitória", numero: "catorze", conferir: "resolve" },
  i: { cartao: "Sobral", numero: "vírgula", conferir: "três" },
  j: { cartao: "Afrânio", numero: "mudou", conferir: "confere" },
  k: { cartao: "Fortaleza", numero: "cinco", conferir: "critério" },
  l: { cartao: "Escola", numero: "nove", conferir: "aqui" },
};

const num = (x: unknown): number => (typeof x === "number" ? x : Number(x));
const str = (x: unknown): string => (typeof x === "string" ? x : String(x));

export const pesoTexto = (c: Criterio): string =>
  typeof c.peso === "number"
    ? `peso ${c.peso}`
    : "peso " + Object.values(c.peso).join(" / ");

/** O número que a cena de cada critério põe em destaque, sempre lido do exemplo real. */
export const destaque = (c: Criterio, dados: Dados): Destaque => {
  const e = c.exemplo;
  const det = e.detalhe ?? {};
  switch (c.id) {
    case "a": {
      const cand = str(det.candidato) === "lula" ? "Lula" : "Flávio";
      const pct = cand === "Lula" ? e.lula_pct : e.flavio_pct;
      const zona = cand === "Lula" ? e.zona_lula_pct : e.zona_flavio_pct;
      return {
        valor: num(det.excesso_zona_pp),
        casas: 1,
        prefixo: "+",
        sufixo: " pp",
        rotulo: "acima do resto da zona",
        legenda: `${cand} ${decimal(pct)}% na seção, ${decimal(zona)}% no resto da zona`,
        cor: COR.alta,
      };
    }
    case "b":
      return {
        valor: 0,
        sufixo: " votos",
        rotulo: `para ${str(det.zerado) === "flavio" ? "Flávio" : "Lula"} em ${inteiro(num(det.votantes))} votantes`,
        legenda: `Em 2022 a seção já dava ${decimal(e.lula_2022_pct ?? 0)}% a Lula: nível baixa`,
        cor: COR.media,
      };
    case "c":
      return {
        valor: num(det.comparecimento_pct),
        sufixo: "%",
        rotulo: "de comparecimento",
        legenda: `${inteiro(num(det.aptos))} aptos, ${inteiro(num(det.comparecimento))} votantes; no país, um em cada cinco ficou em casa`,
        cor: COR.alta,
      };
    case "d":
      return {
        valor: hora(str(det.encerramento_brasilia)),
        rotulo: "último voto, hora de Brasília",
        legenda: `Lula +${decimal(num(det.excesso_zona_lula_pp))} pp sobre o resto da zona`,
        cor: COR.alta,
      };
    case "e": {
      const k = e.detalhes.k as { brancos?: { pct: number; media_zona_pct: number } } | undefined;
      const b = k?.brancos;
      return {
        valor: e.brancos,
        sufixo: " brancos",
        rotulo: `em ${inteiro(e.votantes)} votantes`,
        legenda: b
          ? `${decimal(b.pct)}% de brancos contra ${decimal(b.media_zona_pct)}% na zona; posição ${inteiro(num(det.posicao))} entre as 200`
          : `posição ${inteiro(num(det.posicao))} entre as 200 menos prováveis`,
        cor: COR.media,
      };
    }
    case "f":
      return {
        valor: num(det.n_cargas),
        sufixo: " cargas",
        rotulo: str(det.tipo_urna),
        legenda: `Lula +${decimal(num(det.dif_zona_lula_pp))} pp sobre o resto da zona`,
        cor: COR.alta,
      };
    case "g":
      return {
        valor: hora(str(det.recebido_tse)),
        rotulo: `recebido pelo TSE em ${str(det.recebido_tse).slice(8, 10)}/${str(det.recebido_tse).slice(5, 7)}`,
        legenda: `A urna fechou às ${hora(e.encerramento_brasilia)} do dia anterior`,
        cor: COR.media,
      };
    case "h": {
      const sem = dados.sem_arquivo_por_zona
        .map((z) => `${z.municipio.charAt(0) + z.municipio.slice(1).toLowerCase()} ${z.secoes}`)
        .join(", ");
      return {
        valor: num(det.secoes_faltando_na_zona),
        sufixo: " seções",
        rotulo: `fora da totalização da zona por ${decimal(num(det.horas_parada))} h`,
        legenda: `${inteiro(dados.sem_arquivo_por_zona.reduce((s, z) => s + z.secoes, 0))} seções sem arquivo publicado: ${sem}`,
        cor: COR.alta,
      };
    }
    case "i":
      return {
        valor: num(det.excesso_uf_lula_pp),
        casas: 1,
        prefixo: "+",
        sufixo: " pp",
        rotulo: "Lula acima do estado inteiro",
        legenda: `Lula ${decimal(e.lula_pct)}% na seção, ${decimal(e.uf_lula_pct)}% no ${e.uf}; zona na posição ${inteiro(num(det.posicao_zona))} entre as 50`,
        cor: COR.alta,
      };
    case "j":
      return {
        valor: num(det.variacao_margem_pp),
        casas: 1,
        prefixo: "+",
        sufixo: " pp",
        rotulo: "variação da margem desde 2022",
        legenda: `Lula ${decimal(e.lula_2022_pct ?? 0)}% em 2022, ${decimal(e.lula_pct)}% em 2026; ${decimal(num(det.z))} desvios-padrão`,
        cor: COR.media,
      };
    case "k": {
      const b = (det.brancos ?? det.nulos) as { pct: number; media_zona_pct: number; z: number };
      return {
        valor: b.pct,
        casas: 1,
        sufixo: "%",
        rotulo: det.brancos ? "de votos em branco" : "de votos nulos",
        legenda: `média da zona ${decimal(b.media_zona_pct)}%; ${decimal(b.z)} desvios-padrão acima`,
        cor: COR.media,
      };
    }
    default:
      return {
        valor: e.local_secoes_sinalizadas ?? num(det.secoes_sinalizadas_no_local),
        sufixo: " seções",
        rotulo: `do mesmo prédio na lista, de ${inteiro(e.local_secoes_total ?? 0)}`,
        legenda: `${inteiro(num(det.secoes_sinalizadas_no_local))} delas por critérios da própria seção`,
        cor: COR.alta,
      };
  }
};
