// Decodificador do boletim de urna (BU): o código mora em src/secoes2t/bu-decode.ts, usado pelo
// coletor do 2º turno; este arquivo o reexporta para os scripts e testes antigos e mantém o uso direto.
//
// Uso direto: bun run scripts/bu-decode.ts arquivo-bu.dat  (imprime JSON)
import { decodificarBu } from "../src/secoes2t/bu-decode.ts";

export * from "../src/secoes2t/bu-decode.ts";

if (import.meta.main) {
  const arq = process.argv[2];
  if (arq === undefined) {
    console.error("uso: bun run scripts/bu-decode.ts arquivo-bu.dat");
    process.exit(2);
  }
  const { envelope, bu } = decodificarBu(new Uint8Array(await Bun.file(arq).arrayBuffer()));
  console.log(JSON.stringify({ envelope: { ...envelope, conteudo: `${envelope.conteudo.length} octetos` }, bu }, null, 1));
}
