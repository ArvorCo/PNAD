// Carregador das malhas locais com cache em memória. O componente de mapa (F2)
// projeta e desenha; aqui só se busca e se guarda o GeoJSON.

export type Posicao = [number, number];

export interface Geometria {
  type: "Polygon" | "MultiPolygon";
  coordinates: Posicao[][] | Posicao[][][];
}

export interface Feicao {
  type: "Feature";
  properties: Record<string, unknown>;
  geometry: Geometria | null;
}

export interface ColecaoFeicoes {
  type: "FeatureCollection";
  features: Feicao[];
}

const cache = new Map<string, Promise<ColecaoFeicoes>>();

function buscar(url: string): Promise<ColecaoFeicoes> {
  let p = cache.get(url);
  if (!p) {
    p = fetch(url).then(async r => {
      if (!r.ok) throw new Error(`malha ausente: ${url} (HTTP ${r.status})`);
      return (await r.json()) as ColecaoFeicoes;
    });
    // Falha não fica em cache: a próxima tentativa busca de novo.
    p.catch(() => cache.delete(url));
    cache.set(url, p);
  }
  return p;
}

/** Malha das 27 UFs. */
export const malhaUfs = (): Promise<ColecaoFeicoes> => buscar("/geo/br_uf.geojson");

/** Malha municipal de uma UF (sigla em qualquer caixa). */
export const malhaMunicipios = (uf: string): Promise<ColecaoFeicoes> => buscar(`/geo/mun/${uf.toUpperCase()}.geojson`);

/** Pré-carrega malhas sem esperar (para a próxima tela da playlist). */
export function preCarregar(uf?: string | null): void {
  void malhaUfs().catch(() => undefined);
  if (uf) void malhaMunicipios(uf).catch(() => undefined);
}

/** Código IBGE de uma feição, aceitando os nomes de propriedade usados pelo IBGE e pela casa. */
export function codigoIbge(f: Feicao): string {
  const p = f.properties;
  const v = p.codarea ?? p.codigo_ibg ?? p.cdi ?? p.CD_MUN ?? p.CD_UF ?? p.id;
  return v === undefined || v === null ? "" : String(v);
}
