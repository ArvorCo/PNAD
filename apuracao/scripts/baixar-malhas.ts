/**
 * Baixa as malhas municipais do IBGE (qualidade mínima) para as 27 UFs e a
 * malha nacional por UF, e confere cada `codarea` contra o `cdi` do cadastro
 * de municípios do TSE (`tests/fixtures/mun-e006259-cm.json`).
 *
 * Saída: public/geo/mun/{UF}.geojson, public/geo/br_uf.geojson e
 * public/geo/index.json. Arquivos já presentes não são baixados de novo.
 */
import { copyFile, mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

const RAIZ = resolve(import.meta.dir, "..");
const PNAD = resolve(RAIZ, "..");
const GEO = join(RAIZ, "public/geo");
const MUN = join(GEO, "mun");
const CM = join(RAIZ, "tests/fixtures/mun-e006259-cm.json");
const BR_LOCAL = join(PNAD, "data/originals/ibge_malhas/br_uf/br_uf_minima.geojson");
const BR_URL =
  "https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF";
const UF_URL = (cod: string): string =>
  `https://servicodados.ibge.gov.br/api/v3/malhas/estados/${cod}?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=municipio`;

const PARALELO = 3;
const TENTATIVAS = 4;

/** Código IBGE da UF, mesma tabela de scripts/voto_util_mapa.py (IBGE_UF). */
const IBGE_UF: Record<string, string> = {
  "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
  "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
  "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
  "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF",
};

interface Feature {
  properties: { codarea: string };
}
interface Colecao {
  features: Feature[];
}
interface Cadastro {
  abr: { cd: string; mu: { cdi: string }[] }[];
}
interface Entrada {
  uf: string;
  arquivo: string;
  bytes: number;
  n_features: number;
}

async function existe(caminho: string): Promise<boolean> {
  try {
    return (await stat(caminho)).size > 0;
  } catch {
    return false;
  }
}

async function baixar(url: string, destino: string): Promise<void> {
  let ultimo: unknown = null;
  for (let i = 1; i <= TENTATIVAS; i++) {
    try {
      const resp = await fetch(url, { headers: { "User-Agent": "arvor-apuracao/0.1" } });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const texto = await resp.text();
      const json = JSON.parse(texto) as Colecao;
      if (!Array.isArray(json.features) || json.features.length === 0) {
        throw new Error("GeoJSON sem features");
      }
      await writeFile(destino, texto);
      return;
    } catch (erro) {
      ultimo = erro;
      await Bun.sleep(1000 * 2 ** (i - 1));
    }
  }
  throw new Error(`falhou ${url}: ${String(ultimo)}`);
}

async function emParalelo<T>(itens: T[], n: number, fn: (item: T) => Promise<void>): Promise<void> {
  const fila = [...itens];
  const trabalhadores = Array.from({ length: n }, async () => {
    for (let item = fila.shift(); item !== undefined; item = fila.shift()) await fn(item);
  });
  await Promise.all(trabalhadores);
}

async function ler<T>(caminho: string): Promise<T> {
  return JSON.parse(await readFile(caminho, "utf-8")) as T;
}

async function main(): Promise<void> {
  await mkdir(MUN, { recursive: true });

  const brDestino = join(GEO, "br_uf.geojson");
  if (!(await existe(brDestino))) {
    if (await existe(BR_LOCAL)) await copyFile(BR_LOCAL, brDestino);
    else await baixar(BR_URL, brDestino);
  }

  const pares = Object.entries(IBGE_UF);
  await emParalelo(pares, PARALELO, async ([cod, uf]) => {
    const destino = join(MUN, `${uf}.geojson`);
    if (await existe(destino)) return;
    await baixar(UF_URL(cod), destino);
    console.log(`baixado ${uf}`);
  });

  const cadastro = await ler<Cadastro>(CM);
  const tsePorUf = new Map(cadastro.abr.map((a) => [a.cd.toUpperCase(), new Set(a.mu.map((m) => m.cdi))]));

  const indice: Entrada[] = [];
  let total = 0;
  let divergencias = 0;
  for (const uf of [...Object.values(IBGE_UF)].sort()) {
    const arquivo = `mun/${uf}.geojson`;
    const caminho = join(GEO, arquivo);
    const bytes = (await stat(caminho)).size;
    const malha = await ler<Colecao>(caminho);
    const ibge = new Set(malha.features.map((f) => String(f.properties.codarea)));
    const tse = tsePorUf.get(uf) ?? new Set<string>();
    const soIbge = [...ibge].filter((c) => !tse.has(c));
    const soTse = [...tse].filter((c) => !ibge.has(c));
    divergencias += soIbge.length + soTse.length;
    total += bytes;
    indice.push({ uf, arquivo, bytes, n_features: malha.features.length });
    const nota =
      soIbge.length + soTse.length === 0
        ? "ok"
        : `só IBGE: [${soIbge.join(", ")}]  só TSE: [${soTse.join(", ")}]`;
    console.log(`${uf}  ${String(malha.features.length).padStart(4)} mun  ${String(bytes).padStart(8)} B  ${nota}`);
  }
  const brBytes = (await stat(brDestino)).size;
  indice.push({
    uf: "BR",
    arquivo: "br_uf.geojson",
    bytes: brBytes,
    n_features: (await ler<Colecao>(brDestino)).features.length,
  });
  await writeFile(join(GEO, "index.json"), `${JSON.stringify(indice, null, 2)}\n`);
  console.log(`municipais: ${(total / 1e6).toFixed(2)} MB; br_uf: ${(brBytes / 1e3).toFixed(1)} kB`);
  console.log(`divergências IBGE × TSE: ${divergencias}`);
}

await main();
