// Manchetes da eleição para o boletim falado: RSS de cinco veículos (Google Notícias, G1, Folha,
// Agência Brasil, Poder360), lidos a cada ciclo com User-Agent de navegador e timeout de 10 s. Um
// feed que falha não derruba o ciclo. Janela das últimas 3 h (o dia inteiro no primeiro boletim),
// deduplicação por título normalizado, filtro por termos da eleição, no máximo 25, do mais novo.
// São manchetes dos veículos, não dados nossos: o roteiro sempre atribui.
import { horaBrt } from "./estado.ts";

export interface Feed {
  nome: string;
  url: string;
}

export const FEEDS: readonly Feed[] = [
  { nome: "Google Notícias", url: "https://news.google.com/rss/search?q=elei%C3%A7%C3%B5es+segundo+turno+apura%C3%A7%C3%A3o&hl=pt-BR&gl=BR&ceid=BR:pt-419" },
  { nome: "G1", url: "https://g1.globo.com/rss/g1/politica/" },
  { nome: "Folha", url: "https://feeds.folha.uol.com.br/poder/rss091.xml" },
  { nome: "Agência Brasil", url: "https://agenciabrasil.ebc.com.br/rss/politica/feed.xml" },
  { nome: "Poder360", url: "https://www.poder360.com.br/feed/" },
];

const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36";
export const LIMITE = 25;
export const JANELA_MS = 3 * 3600_000;

export interface Manchete {
  titulo: string;
  veiculo: string;
  link: string;
  pub_iso: string;
  hora_brt: string;
  /** Não estava na lista do boletim anterior. */
  nova: boolean;
}

export interface ResultadoFeed {
  nome: string;
  url: string;
  status: number | null;
  itens: number;
  erro: string | null;
}

export interface Noticias {
  buscado_em: string;
  janela_desde: string;
  feeds: ResultadoFeed[];
  itens: Manchete[];
}

interface Bruto {
  titulo: string;
  link: string;
  pub: string;
  fonte: string | null;
}

const ENTIDADES: Readonly<Record<string, string>> = {
  amp: "&", lt: "<", gt: ">", quot: '"', apos: "'", nbsp: " ", ordm: "º", ordf: "ª", ldquo: "\u201c", rdquo: "\u201d", lsquo: "\u2018", rsquo: "\u2019", hellip: "...",
  aacute: "á", eacute: "é", iacute: "í", oacute: "ó", uacute: "ú", atilde: "ã", otilde: "õ", ccedil: "ç", acirc: "â", ecirc: "ê", ocirc: "ô", agrave: "à", uuml: "ü",
  Aacute: "Á", Eacute: "É", Iacute: "Í", Oacute: "Ó", Uacute: "Ú", Atilde: "Ã", Otilde: "Õ", Ccedil: "Ç", Acirc: "Â", Ecirc: "Ê", Ocirc: "Ô", Agrave: "À",
};

export function decodificarEntidades(s: string): string {
  return s
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&#x([0-9a-f]+);/gi, (_m, h: string) => String.fromCodePoint(Number.parseInt(h, 16)))
    .replace(/&#(\d+);/g, (_m, d: string) => String.fromCodePoint(Number(d)))
    .replace(/&([a-z]+);/gi, (m, n: string) => ENTIDADES[n] ?? ENTIDADES[n.toLowerCase()] ?? m);
}

const tag = (bloco: string, nome: string): string | null => {
  const m = new RegExp(`<${nome}(?:\\s[^>]*)?>([\\s\\S]*?)</${nome}>`, "i").exec(bloco);
  return m?.[1] !== undefined ? decodificarEntidades(m[1]).replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim() : null;
};

/** Itens de um RSS 0.91/2.0: título, link, data e, no Google Notícias, o veículo (`<source>`). */
export function lerRss(xml: string): Bruto[] {
  const saida: Bruto[] = [];
  for (const m of xml.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)) {
    const bloco = m[1] ?? "";
    const titulo = tag(bloco, "title");
    if (!titulo) continue;
    saida.push({ titulo, link: tag(bloco, "link") ?? "", pub: tag(bloco, "pubDate") ?? tag(bloco, "dc:date") ?? "", fonte: tag(bloco, "source") });
  }
  return saida;
}

/** Bytes do feed em texto, respeitando o encoding do cabeçalho XML (a Folha vem em ISO-8859-1). */
export function decodificarXml(bytes: Uint8Array): string {
  const cabeca = new TextDecoder("latin1").decode(bytes.slice(0, 200));
  const enc = /encoding=["']([^"']+)["']/i.exec(cabeca)?.[1]?.toLowerCase() ?? "utf-8";
  if (/8859-1|latin|1252/.test(enc)) return new TextDecoder("windows-1252").decode(bytes);
  return new TextDecoder("utf-8").decode(bytes);
}

/** Título comparável: minúsculas, sem acento, sem pontuação. */
export function normalizar(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9º ]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const TERMOS = /\b(eleicao|eleicoes|eleitora(l|is)|eleitor(es|a|as)?|urnas?|votacao|apuracao|secao|secoes|abstencao|boca de urna|transporte|lula|flavio|bolsonaro|segundo turno|2º turno|2o turno|mesari[oa]s?)\b/;
const SIGLAS = /\b(TSE|TREs?)\b/;

/** É notícia da eleição? Siglas pelo texto original (TRE não pode casar com "três"). */
export function daEleicao(titulo: string): boolean {
  return SIGLAS.test(titulo) || TERMOS.test(normalizar(titulo));
}

/** Google Notícias põe " - Veículo" no fim do título. */
function separarFonte(b: Bruto, feed: string): { titulo: string; veiculo: string } {
  if (b.fonte) {
    const suf = ` - ${b.fonte}`;
    return { titulo: b.titulo.endsWith(suf) ? b.titulo.slice(0, -suf.length).trim() : b.titulo, veiculo: b.fonte };
  }
  return { titulo: b.titulo, veiculo: feed };
}

export interface OpcoesSelecao {
  agoraMs: number;
  desdeMs: number;
  anteriores: ReadonlySet<string>;
  limite?: number;
}

/** Janela, filtro, deduplicação e corte; do mais novo para o mais antigo. */
export function selecionar(porFeed: { feed: string; itens: Bruto[] }[], o: OpcoesSelecao): Manchete[] {
  const vistos = new Set<string>();
  const todas: Manchete[] = [];
  for (const { feed, itens } of porFeed) {
    for (const b of itens) {
      const t = Date.parse(b.pub);
      if (!Number.isFinite(t) || t < o.desdeMs || t > o.agoraMs + 10 * 60_000) continue;
      const { titulo, veiculo } = separarFonte(b, feed);
      if (!daEleicao(titulo)) continue;
      const chave = normalizar(titulo);
      if (!chave || vistos.has(chave)) continue;
      vistos.add(chave);
      todas.push({ titulo, veiculo, link: b.link, pub_iso: new Date(t).toISOString(), hora_brt: horaBrt(t), nova: !o.anteriores.has(chave) });
    }
  }
  return todas.sort((a, b) => b.pub_iso.localeCompare(a.pub_iso)).slice(0, o.limite ?? LIMITE);
}

async function baixar(f: Feed, timeoutMs: number): Promise<{ r: ResultadoFeed; itens: Bruto[] }> {
  try {
    const res = await fetch(f.url, { headers: { "user-agent": UA, accept: "application/rss+xml, application/xml, text/xml, */*" }, signal: AbortSignal.timeout(timeoutMs) });
    if (!res.ok) return { r: { nome: f.nome, url: f.url, status: res.status, itens: 0, erro: `HTTP ${res.status}` }, itens: [] };
    const itens = lerRss(decodificarXml(new Uint8Array(await res.arrayBuffer())));
    return { r: { nome: f.nome, url: f.url, status: res.status, itens: itens.length, erro: null }, itens };
  } catch (e) {
    return { r: { nome: f.nome, url: f.url, status: null, itens: 0, erro: e instanceof Error ? e.message : String(e) }, itens: [] };
  }
}

export interface OpcoesBusca {
  agoraMs: number;
  /** Primeiro boletim: o dia inteiro (desde 00:00 de Brasília); depois, as últimas 3 h. */
  primeiro: boolean;
  anteriores: ReadonlySet<string>;
  feeds?: readonly Feed[];
  timeoutMs?: number;
}

export function inicioDoDiaBrt(agoraMs: number): number {
  const dia = new Date(agoraMs).toLocaleDateString("en-CA", { timeZone: "America/Sao_Paulo" });
  return Date.parse(`${dia}T00:00:00-03:00`);
}

export async function buscarNoticias(o: OpcoesBusca): Promise<Noticias> {
  const desdeMs = o.primeiro ? inicioDoDiaBrt(o.agoraMs) : o.agoraMs - JANELA_MS;
  const res = await Promise.all((o.feeds ?? FEEDS).map(f => baixar(f, o.timeoutMs ?? 10_000)));
  const itens = selecionar(res.map((x, i) => ({ feed: (o.feeds ?? FEEDS)[i]?.nome ?? x.r.nome, itens: x.itens })), { agoraMs: o.agoraMs, desdeMs, anteriores: o.anteriores });
  return { buscado_em: new Date(o.agoraMs).toISOString(), janela_desde: new Date(desdeMs).toISOString(), feeds: res.map(x => x.r), itens };
}

/** Bloco do prompt: `[hh:mm, veículo] título`, com NOVA nas que o boletim anterior não listou. */
export function blocoPrompt(n: Noticias | null): string | null {
  if (!n || n.itens.length === 0) return null;
  return n.itens.map(m => `${m.nova ? "NOVA " : ""}[${m.hora_brt}, ${m.veiculo}] ${m.titulo}`).join("\n");
}
