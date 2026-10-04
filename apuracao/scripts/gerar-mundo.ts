/**
 * Ativos da tela `exterior` (voto no exterior, UF `zz` do TSE).
 *
 * 1. Converte `world-atlas/countries-110m.json` (TopoJSON) em `public/geo/mundo.geojson`:
 *    só os polígonos de terra, sem a Antártida, com o código ISO numérico em `id`.
 * 2. Geocodifica as 186 cidades do exterior do cadastro de municípios do TSE
 *    (`tests/fixtures/mun-e006257-cm.json`, abr `zz`). O arquivo de locais de votação do
 *    TSE traz latitude −1 para toda cidade do exterior, então a coordenada vem do
 *    gazetteer GeoNames (`all-the-cities`, cidades com mais de mil habitantes).
 *
 * Regra de casamento, nesta ordem:
 *   a) tabela de exônimos declarada abaixo (nome em português → nome no GeoNames e país);
 *   b) casamento automático sem acento e sem pontuação contra o nome do GeoNames, fora do
 *      Brasil (o cadastro tem "RIO BRANCO", que é a cidade uruguaia, não a capital do Acre),
 *      escolhendo a maior população. Casamento automático em que outra cidade de outro país
 *      tem pelo menos um quarto da população da escolhida é ambíguo e reprova o script:
 *      a resolução precisa entrar na tabela.
 *
 * Saída: `public/geo/exterior_cidades.json` e a cópia versionada `public/exterior_cidades.json`
 * (`public/geo/` é ignorado pelo git), `[{cd, nm, lat, lon, pais}]`, com as 186 entradas.
 * O script falha se alguma cidade ficar sem coordenada.
 */
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import cidadesGeonames from "all-the-cities";

const RAIZ = resolve(import.meta.dir, "..");
const GEO = join(RAIZ, "public/geo");
const CM = join(RAIZ, "tests/fixtures/mun-e006257-cm.json");
const ATLAS = join(RAIZ, "node_modules/world-atlas/countries-110m.json");
const SAIDA_MUNDO = join(GEO, "mundo.geojson");
const SAIDA_CIDADES = join(GEO, "exterior_cidades.json");
const COPIA_CIDADES = join(RAIZ, "public/exterior_cidades.json");

/** Código ISO numérico da Antártida. */
const ANTARTIDA = "010";
/** Outra cidade com pelo menos esta fração da população da escolhida torna o casamento ambíguo. */
const LIMIAR_AMBIGUO = 0.25;

/**
 * Exônimos e cidades de consulado: nome do cadastro do TSE → [nome no GeoNames, país ISO-2].
 * Entra aqui toda cidade cujo nome em português difere do GeoNames, e toda cidade em que o
 * casamento automático escolheria outro país (a cidade do consulado brasileiro decide).
 */
const EXONIMOS: Readonly<Record<string, readonly [string, string]>> = {
  "ABIDJÃ": ["Abidjan", "CI"],
  "ADIS ABEBA": ["Addis Ababa", "ET"],
  "AMSTERDÃ": ["Amsterdam", "NL"],
  "AMÃ": ["Amman", "JO"],
  "ANCARA": ["Ankara", "TR"],
  "ARGEL": ["Algiers", "DZ"],
  "ARTIGAS": ["Artigas", "UY"],
  "ASSUNÇÃO": ["Asunción", "PY"],
  "ASTANA": ["Nur-Sultan", "KZ"],
  "ATENAS": ["Athens", "GR"],
  "ATLANTA": ["Atlanta", "US"],
  "BAGDÁ": ["Baghdad", "IQ"],
  "BAREIN": ["Manama", "BH"],
  "BARCELONA": ["Barcelona", "ES"],
  "BEIRUTE": ["Beirut", "LB"],
  "BELGRADO": ["Belgrade", "RS"],
  "BERLIM": ["Berlin", "DE"],
  "BOGOTÁ": ["Bogotá", "CO"],
  "BOSTON": ["Boston", "US"],
  "BRUXELAS": ["Brussels", "BE"],
  "BUCARESTE": ["Bucharest", "RO"],
  "BUDAPESTE": ["Budapest", "HU"],
  "CAIENA": ["Cayenne", "GF"],
  "CAIRO": ["Cairo", "EG"],
  "CAMBERRA": ["Canberra", "AU"],
  "CANTÃO": ["Guangzhou", "CN"],
  "CASTRIES": ["Castries", "LC"],
  "CHUY": ["Chui", "UY"],
  "CIDADE DO CABO": ["Cape Town", "ZA"],
  "COLOMBO": ["Colombo", "LK"],
  "CONACRI": ["Conakry", "GN"],
  "CONCEPCIÓN": ["Concepción", "PY"],
  "COPENHAGUE": ["Copenhagen", "DK"],
  "CÓRDOBA": ["Córdoba", "AR"],
  "DACCA": ["Dhaka", "BD"],
  "DACAR": ["Dakar", "SN"],
  "DAMASCO": ["Damascus", "SY"],
  "DÍLI": ["Dili", "TL"],
  "EDIMBURGO": ["Edinburgh", "GB"],
  "ESTOCOLMO": ["Stockholm", "SE"],
  "FARO": ["Faro", "PT"],
  "FRANKFURT": ["Frankfurt am Main", "DE"],
  "GENEBRA": ["Genève", "CH"],
  "GEORGETOWN": ["Georgetown", "GY"],
  "GUATEMALA": ["Guatemala City", "GT"],
  "HANÓI": ["Hanoi", "VN"],
  "HAVANA": ["Havana", "CU"],
  "HELSINQUE": ["Helsinki", "FI"],
  "HOUSTON": ["Houston", "US"],
  "IAUNDÊ": ["Yaoundé", "CM"],
  "IEREVAN": ["Yerevan", "AM"],
  "ISLAMABADE": ["Islamabad", "PK"],
  "ISTAMBUL": ["Istanbul", "TR"],
  "JACARTA": ["Jakarta", "ID"],
  "KATMANDU": ["Kathmandu", "NP"],
  "KIEV": ["Kyiv", "UA"],
  "KINGSTON-JAMAICA": ["Kingston", "JM"],
  "KUAITE": ["Kuwait City", "KW"],
  "LA PAZ": ["La Paz", "BO"],
  "LAGOS": ["Lagos", "NG"],
  "LILONGUE": ["Lilongwe", "MW"],
  "LIMA": ["Lima", "PE"],
  "LISBOA": ["Lisbon", "PT"],
  "LIUBLIANA": ["Ljubljana", "SI"],
  "LONDRES": ["London", "GB"],
  "LOS ANGELES": ["Los Angeles", "US"],
  "LUSACA": ["Lusaka", "ZM"],
  "MADRI": ["Madrid", "ES"],
  "MARSELHA": ["Marseille", "FR"],
  "MASCATE": ["Muscat", "OM"],
  "MEXICO": ["Mexico City", "MX"],
  "MIAMI": ["Miami", "US"],
  "MILÃO": ["Milan", "IT"],
  "MONTEVIDÉU": ["Montevideo", "UY"],
  "MONTREAL": ["Montréal", "CA"],
  "MOSCOU": ["Moscow", "RU"],
  "MUNIQUE": ["Munich", "DE"],
  "NAGÓIA": ["Nagoya", "JP"],
  "NAIRÓBI": ["Nairobi", "KE"],
  "NICOSIA": ["Nicosia", "CY"],
  "NOVA DELHI": ["New Delhi", "IN"],
  "NOVA YORK": ["New York City", "US"],
  "ORLANDO": ["Orlando", "US"],
  "OTTAWA": ["Ottawa", "CA"],
  "PANAMA": ["Panamá", "PA"],
  "PARIS": ["Paris", "FR"],
  "PASO LOS LIBRES": ["Paso de los Libres", "AR"],
  "PEQUIM": ["Beijing", "CN"],
  "PORT OF SPAIN": ["Port of Spain", "TT"],
  "PORTO": ["Porto", "PT"],
  "PORTO PRÍNCIPE": ["Port-au-Prince", "HT"],
  "PRAGA": ["Prague", "CZ"],
  "PRAIA": ["Praia", "CV"],
  "RIADE": ["Riyadh", "SA"],
  "RIO BRANCO": ["Río Branco", "UY"],
  "RIVERA": ["Rivera", "UY"],
  "ROMA": ["Rome", "IT"],
  "SAINT JOHNS": ["Saint John’s", "AG"],
  "SANTIAGO": ["Santiago", "CL"],
  "SEUL": ["Seoul", "KR"],
  "SINGAPURA": ["Singapore", "SG"],
  "ST GEORGES DE LOYAPOCK": ["Saint-Georges", "GF"],
  "SÃO DOMINGOS": ["Santo Domingo", "DO"],
  "SÃO FRANCISCO": ["San Francisco", "US"],
  "SÃO JOSÉ": ["San José", "CR"],
  "SÃO SALVADOR": ["San Salvador", "SV"],
  "SÃO TOMÉ": ["São Tomé", "ST"],
  "SÓFIA": ["Sofia", "BG"],
  "TAIPÉ": ["Taipei", "TW"],
  "TALIN": ["Tallinn", "EE"],
  "TEERÃ": ["Tehran", "IR"],
  "TÓQUIO": ["Tokyo", "JP"],
  "TRÍPOLI": ["Tripoli", "LY"],
  "UAGADUGU": ["Ouagadougou", "BF"],
  "VANCOUVER": ["Vancouver", "CA"],
  "VARSÓVIA": ["Warsaw", "PL"],
  "VIENA": ["Vienna", "AT"],
  "WASHINGTON": ["Washington, D.C.", "US"],
  "WELLINGTON": ["Wellington", "NZ"],
  "XANGAI": ["Shanghai", "CN"],
  "ZURIQUE": ["Zürich", "CH"],
};

interface CidadeGeonames {
  name: string;
  altName: string;
  country: string;
  population: number;
  loc: { coordinates: [number, number] };
}

interface MunicipioCm {
  cd: string;
  nm: string;
}
interface Cadastro {
  abr: { cd: string; mu: MunicipioCm[] }[];
}

interface CidadeExterior {
  cd: string;
  nm: string;
  lat: number;
  lon: number;
  pais: string;
}

/** Sem acento, sem pontuação, caixa baixa, espaços simples. */
const normalizar = (s: string): string =>
  s
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();

const r4 = (x: number): number => Math.round(x * 1e4) / 1e4;

type Anel = [number, number][];

/**
 * Anéis que cruzam o antimeridiano (Rússia, Fiji) saltam de +180 para −180 e riscariam o mapa
 * de ponta a ponta. Desenrola a longitude para o anel ficar contínuo e, se ele passar de ±180,
 * acrescenta a cópia deslocada de 360°; o componente recorta tudo na caixa do mapa.
 */
function semAntimeridiano(anel: Anel): Anel[] {
  const cont: Anel = [];
  let desloc = 0;
  let anterior: number | null = null;
  for (const [lon, lat] of anel) {
    if (anterior !== null) {
      if (lon - anterior > 180) desloc -= 360;
      else if (anterior - lon > 180) desloc += 360;
    }
    anterior = lon;
    cont.push([lon + desloc, lat]);
  }
  const lons = cont.map(p => p[0]);
  const min = Math.min(...lons);
  const max = Math.max(...lons);
  const saida: Anel[] = [cont];
  if (max > 180) saida.push(cont.map(([x, y]) => [x - 360, y]));
  if (min < -180) saida.push(cont.map(([x, y]) => [x + 360, y]));
  return saida;
}

const arred = (anel: Anel): Anel => anel.map(([x, y]) => [Math.round(x * 100) / 100, Math.round(y * 100) / 100]);

/** Polígonos do país como lista de polígonos (anéis), já sem salto no antimeridiano. */
function poligonos(g: { type: string; coordinates: unknown }): Anel[][] {
  const lista = g.type === "Polygon" ? [g.coordinates as Anel[]] : (g.coordinates as Anel[][]);
  const saida: Anel[][] = [];
  for (const pol of lista) {
    const [ext, ...furos] = pol;
    if (!ext) continue;
    // Furos ficam com o exterior original; os países da malha 110m que cruzam o antimeridiano não têm furo.
    const exts = semAntimeridiano(ext);
    exts.forEach((e, i) => saida.push(i === 0 ? [arred(e), ...furos.map(arred)] : [arred(e)]));
  }
  return saida;
}

async function gerarMundo(): Promise<number> {
  const topo = JSON.parse(await readFile(ATLAS, "utf8")) as Topology<{ countries: GeometryCollection<{ name: string }> }>;
  const colecao = feature(topo, topo.objects.countries);
  const features = colecao.features
    .filter(f => String(f.id) !== ANTARTIDA && f.geometry && (f.geometry.type === "Polygon" || f.geometry.type === "MultiPolygon"))
    .map(f => ({
      type: "Feature",
      id: String(f.id ?? ""),
      properties: { id: String(f.id ?? ""), name: f.properties?.name ?? "" },
      geometry: { type: "MultiPolygon", coordinates: poligonos(f.geometry as { type: string; coordinates: unknown }) },
    }));
  await writeFile(SAIDA_MUNDO, JSON.stringify({ type: "FeatureCollection", features }));
  return features.length;
}

function geocodificar(municipios: MunicipioCm[]): { cidades: CidadeExterior[]; porTabela: number; automaticas: string[]; falhas: string[] } {
  const base = cidadesGeonames as unknown as CidadeGeonames[];
  const indice = new Map<string, CidadeGeonames[]>();
  for (const c of base) {
    for (const nome of new Set([c.name, c.altName].filter(Boolean).map(normalizar))) {
      const lista = indice.get(nome);
      if (lista) lista.push(c);
      else indice.set(nome, [c]);
    }
  }
  const tabela = new Map(Object.entries(EXONIMOS).map(([k, v]) => [normalizar(k), v]));
  const maior = (xs: CidadeGeonames[]): CidadeGeonames | undefined => [...xs].sort((a, b) => b.population - a.population)[0];

  const cidades: CidadeExterior[] = [];
  const automaticas: string[] = [];
  const falhas: string[] = [];
  let porTabela = 0;
  for (const m of municipios) {
    const chave = normalizar(m.nm);
    const regra = tabela.get(chave);
    let achada: CidadeGeonames | undefined;
    if (regra) {
      const [nome, pais] = regra;
      achada = maior((indice.get(normalizar(nome)) ?? []).filter(c => c.country === pais));
      if (!achada) {
        falhas.push(`${m.nm}: a tabela aponta ${nome} (${pais}), ausente do GeoNames`);
        continue;
      }
      porTabela++;
    } else {
      const candidatas = (indice.get(chave) ?? []).filter(c => c.country !== "BR");
      achada = maior(candidatas);
      if (!achada) {
        falhas.push(`${m.nm}: sem casamento automático`);
        continue;
      }
      const escolhida = achada;
      const rival = candidatas.find(c => c.country !== escolhida.country && c.population >= LIMIAR_AMBIGUO * escolhida.population);
      if (rival) {
        falhas.push(`${m.nm}: ambíguo entre ${escolhida.name} (${escolhida.country}, ${escolhida.population}) e ${rival.name} (${rival.country}, ${rival.population})`);
        continue;
      }
      automaticas.push(`${m.nm} → ${achada.name} (${achada.country}, ${achada.population})`);
    }
    const [lon, lat] = achada.loc.coordinates;
    cidades.push({ cd: m.cd, nm: m.nm, lat: r4(lat), lon: r4(lon), pais: achada.country });
  }
  return { cidades, porTabela, automaticas, falhas };
}

async function main(): Promise<void> {
  await mkdir(GEO, { recursive: true });
  const nPaises = await gerarMundo();
  console.log(`mundo.geojson: ${nPaises} países (sem a Antártida)`);

  const cm = JSON.parse(await readFile(CM, "utf8")) as Cadastro;
  const zz = cm.abr.find(a => a.cd.toLowerCase() === "zz");
  if (!zz) throw new Error("cadastro sem a abrangência zz");
  const { cidades, porTabela, automaticas, falhas } = geocodificar(zz.mu);

  console.log(`casamento automático: ${automaticas.length}`);
  for (const a of automaticas) console.log(`  ${a}`);
  console.log(`pela tabela de exônimos: ${porTabela}`);
  if (falhas.length > 0) {
    for (const f of falhas) console.error(`  ${f}`);
    throw new Error(`${falhas.length} cidades do exterior sem coordenada resolvida`);
  }
  if (cidades.length !== zz.mu.length) throw new Error(`esperava ${zz.mu.length} cidades, saíram ${cidades.length}`);
  cidades.sort((a, b) => a.cd.localeCompare(b.cd));
  const json = `${JSON.stringify(cidades, null, 0).replace(/\},\{/g, "},\n{")}\n`;
  await writeFile(SAIDA_CIDADES, json);
  await writeFile(COPIA_CIDADES, json);
  console.log(`exterior_cidades.json: ${cidades.length} cidades`);
}

await main();
