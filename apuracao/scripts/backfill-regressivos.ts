// Normaliza versões marcadas como regressivas que são, na verdade, a versão mais nova do
// arquivo pela hora de geração do TSE e ficaram sem voto_candidato/voto_partido (o coletor
// pula a normalização de versão regressiva). Caso real: as finais de deputado do AM em 05/10.
// Uso: bun run scripts/backfill-regressivos.ts [--db data/apuracao.sqlite] [--so-listar]
import { parseArgs } from "node:util";
import { abrirEscrita } from "../src/db/abrir.ts";
import { Escritor } from "../src/db/escrita.ts";
import { gunzipTexto, itensDeU } from "../src/db/itens.ts";
import { normalizarU, politicaPara } from "../src/parse/normalizar.ts";
import { parseCorpo } from "../src/parse/schemas.ts";
import type { Nivel } from "../src/types.ts";

const { values: a } = parseArgs({
  args: Bun.argv.slice(2),
  options: { db: { type: "string", default: "data/apuracao.sqlite" }, "so-listar": { type: "boolean", default: false } },
});
const db = abrirEscrita(a.db ?? "data/apuracao.sqlite");
interface Alvo { id: number; arquivo_id: number; sha256: string; cargo_cd: number; nivel: string; uf: string | null; gerado_em: string }
const alvos = db
  .query<Alvo, []>(
    `SELECT s.id, s.arquivo_id, s.sha256, a.cargo_cd, a.nivel, a.uf, s.gerado_em
       FROM snapshot s JOIN arquivo a ON a.id = s.arquivo_id
      WHERE a.tipo = 'u' AND s.regressivo = 1
        AND s.gerado_em = (SELECT MAX(s2.gerado_em) FROM snapshot s2 WHERE s2.arquivo_id = s.arquivo_id)
        AND NOT EXISTS (SELECT 1 FROM voto_candidato vc WHERE vc.snapshot_id = s.id)
      ORDER BY s.id`,
  )
  .all();
console.log(`versões mais novas marcadas regressivas e sem candidatos: ${alvos.length}`);
if (a["so-listar"]) {
  for (const x of alvos) console.log(x.id, x.nivel, x.uf, "cargo", x.cargo_cd, x.gerado_em);
  process.exit(0);
}
const esc = new Escritor(db);
let feitos = 0;
for (const x of alvos) {
  const blob = db.query<{ gz: Uint8Array<ArrayBuffer> }, [string]>("SELECT gz FROM blob WHERE sha256 = ?").get(x.sha256);
  if (!blob) {
    console.log("sem blob", x.id);
    continue;
  }
  const p = parseCorpo("u", gunzipTexto(blob.gz));
  if (!p.ok || p.parsed.tipo !== "u") {
    console.log("parse falhou", x.id);
    continue;
  }
  const n = normalizarU(p.parsed.data, {
    uf: x.uf, politicaCandidatos: politicaPara(x.cargo_cd, x.nivel as Nivel), primeiro: false, forcarCandidatos: true,
  });
  db.transaction(() => esc.gravarLote(itensDeU(n, x.id)))();
  feitos++;
  console.log("normalizado", x.id, x.nivel, x.uf, "cargo", x.cargo_cd, "candidatos", n.votoCandidato.length);
}
console.log(`feitos ${feitos}`);
db.close();
