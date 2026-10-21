// Risco 1: boca de urna. Caso de Paulista (PE, 2020) e o balanço do Ministério da Justiça.
import { Risco } from "../componentes/Risco";
import type { CenaProps } from "./registro";

export const RiscoBocaDeUrna: React.FC<CenaProps> = ({ cena, dados, g }) => {
  const mj = dados.riscos.find((r) => r.id === "boca_urna")?.casos[1];
  return (
    <Risco
      cena={cena}
      dados={dados}
      g={g}
      id="boca_urna"
      oQueE="Propaganda e aliciamento no dia da eleição, na porta do local."
      sinalResumo="Voto aliciado é igual a qualquer outro na urna."
      fundo={["santinhos_calcada", "fila_secao"]}
      mj={{ valor: dados.balanco_mj["1t_2024"].boca_urna, rotulo: `ocorrências de boca de urna no primeiro turno de ${mj?.ano ?? ""}, segundo o Ministério da Justiça` }}
      fazer={[
        { texto: "Registra de fora da seção", gatilho: "f1" },
        { texto: "Anota hora e local", gatilho: "f2" },
        { texto: "Aciona o juiz e a polícia", gatilho: "f3" },
      ]}
      fecho="Coragem é ficar. Sabedoria é não dar motivo."
    />
  );
};
