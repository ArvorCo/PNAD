// Pré-carga dos testes: o boletim falado do servidor usa uma pasta temporária, nunca data/boletins-2t.
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

process.env.APURACAO_BOLETIM_DIR ??= mkdtempSync(join(tmpdir(), "boletins-teste-"));
