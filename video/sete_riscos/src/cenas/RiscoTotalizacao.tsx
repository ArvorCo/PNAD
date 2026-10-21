// Risco 7: totalização que não bate com o boletim. Caso Proconsult (RJ, 1982).
import { Risco } from "../componentes/Risco";
import type { CenaProps } from "./registro";

export const RiscoTotalizacao: React.FC<CenaProps> = ({ cena, dados, g }) => (
  <Risco
    cena={cena}
    dados={dados}
    g={g}
    id="totalizacao"
    titulo="Totalização que não bate com o boletim"
    oQueE="A totalização não bater com o boletim."
    sinalResumo="O boletim impresso e o publicado têm de ser iguais."
    fundo={["fita_impressora_antiga", "boletim_impressora"]}
    fazer={[
      { texto: "Pede a cópia do boletim", gatilho: "f1" },
      { texto: "Lê o QR", gatilho: "f2" },
      { texto: "Compara com o site do TSE", gatilho: "f3" },
    ]}
    fecho="Coragem é guardar o papel. Sabedoria é conferir sem acusar."
  />
);
