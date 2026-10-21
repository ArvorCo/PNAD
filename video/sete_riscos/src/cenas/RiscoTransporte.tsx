// Risco 3: transporte de eleitores. Reserva (PR, 2004), Anchieta (SC, 2012) e veículos apreendidos.
import { Risco } from "../componentes/Risco";
import type { CenaProps } from "./registro";

export const RiscoTransporte: React.FC<CenaProps> = ({ cena, dados, g }) => {
  const mj = dados.riscos.find((r) => r.id === "transporte")?.casos.find((c) => c.id === dados.balanco_mj["1t_2024"].fonte_caso);
  return (
    <Risco
      cena={cena}
      dados={dados}
      g={g}
      id="transporte"
      oQueE="Só a Justiça Eleitoral organiza o transporte. Quem mais fornecer comete crime."
      sinalResumo="Seção rural com comparecimento acima do padrão. Quase sempre, só o fiscal vê."
      fundo={["van_eleitores", "fila_secao"]}
      extras={[{ indice: 1, gatilho: "anchieta" }]}
      mj={{ valor: dados.balanco_mj["1t_2024"].veiculos_transporte, rotulo: `veículos apreendidos no primeiro turno de ${mj?.ano ?? ""}` }}
      fazer={[
        { texto: "Anota placa e hora", gatilho: "f1" },
        { texto: "Avisa o juiz", gatilho: "f2" },
        { texto: "Não aborda o motorista", gatilho: "f3" },
      ]}
      fecho="Sabedoria é ver sem se meter."
    />
  );
};
