// Risco 4: voto sob ameaça. Santa Quitéria (CE), os locais trocados no Rio e a seção ribeirinha de Bagre (PA).
import { Risco } from "../componentes/Risco";
import { decimal } from "../componentes/util";
import type { CenaProps } from "./registro";

export const RiscoMedo: React.FC<CenaProps> = ({ cena, dados, g }) => {
  const e = dados.exemplos.frente_3;
  return (
    <Risco
      cena={cena}
      dados={dados}
      g={g}
      id="medo"
      oQueE="Facção ou milícia que intimida o eleitor."
      sinalResumo="A concentração extrema só se lê com o território."
      fundo={["viela_noite", "rio_amazonia_escola"]}
      extras={[{ indice: 1, gatilho: "rio" }]}
      secao={e}
      etiquetasSecao={[`comparecimento ${decimal(e.comparecimento_pct)}%`, "o território explica; o boletim não"]}
      fazer={[
        { texto: "Não confronta", gatilho: "f1" },
        { texto: "Registra", gatilho: "f2" },
        { texto: "Força federal: só o TSE requisita", gatilho: "f3" },
      ]}
    />
  );
};
