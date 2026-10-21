// Risco 5: mesário mal-intencionado. Itumbiara (GO, 2018).
import { Risco } from "../componentes/Risco";
import type { CenaProps } from "./registro";

export const RiscoMesario: React.FC<CenaProps> = ({ cena, dados, g }) => (
  <Risco
    cena={cena}
    dados={dados}
    g={g}
    id="mesario"
    oQueE="Quem conduz o voto de outra pessoa dentro da cabine."
    sinalResumo="Não sobra número no boletim. Só quem está na sala vê."
    fundo={["cabine_mesario", "teclado_urna_macro"]}
    fazer={[
      { texto: "Impugna na hora", gatilho: "f1" },
      { texto: "Pede o registro na ata", gatilho: "f2" },
      { texto: "Anota hora e nome", gatilho: "f3" },
      { texto: "Não discute com o mesário", gatilho: "f4" },
    ]}
    fecho="Coragem é ficar; sabedoria é a lei no papel."
  />
);
