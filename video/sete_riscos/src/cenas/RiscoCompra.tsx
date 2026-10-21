// Risco 2: compra de voto. Cassação de Jackson Lago (MA, 2009) e o balanço do Ministério da Justiça.
import { Risco } from "../componentes/Risco";
import type { CenaProps } from "./registro";

export const RiscoCompra: React.FC<CenaProps> = ({ cena, dados, g }) => {
  const mj = dados.riscos.find((r) => r.id === "compra")?.casos[1];
  return (
    <Risco
      cena={cena}
      dados={dados}
      g={g}
      id="compra"
      oQueE="Dinheiro ou vantagem em troca do voto."
      sinalResumo="O voto comprado é igual a qualquer outro na urna."
      fundo={["envelope_mao", "fila_secao"]}
      mj={{ valor: dados.balanco_mj["1t_2024"].compra, rotulo: `ocorrências de compra de voto em um dia, no primeiro turno de ${mj?.ano ?? ""}` }}
      fazer={[
        { texto: "Anota quem, onde e quando", gatilho: "f1" },
        { texto: "Avisa o juiz", gatilho: "f2" },
        { texto: "Celular na cabine é proibido", gatilho: "f3" },
      ]}
      fecho="Quem prova é a testemunha, não o gráfico."
    />
  );
};
