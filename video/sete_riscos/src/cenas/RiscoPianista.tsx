// Risco 6: mesário pianista. Pescaria Brava (SC, 2016), Macapá (AP, 2024) e a seção de Baião (PA).
import { Risco } from "../componentes/Risco";
import { decimal, inteiro } from "../componentes/util";
import type { CenaProps } from "./registro";

export const RiscoPianista: React.FC<CenaProps> = ({ cena, dados, g }) => {
  const e = dados.exemplos.baiao_pa;
  return (
    <Risco
      cena={cena}
      dados={dados}
      g={g}
      id="pianista"
      oQueE="Quem vota no lugar de quem não veio."
      sinalResumo="Comparecimento perto de cem por cento. Isso não prova nada."
      fundo={["caderno_assinatura", "urna_mesa_lacre"]}
      extras={[{ indice: 1, gatilho: "macapa" }]}
      secao={e}
      etiquetasSecao={[`${inteiro(e.votantes)} de ${inteiro(e.aptos)} votaram`, `comparecimento ${decimal(e.comparecimento_pct, 0)}%`, "isso não prova nada"]}
      fazer={[
        { texto: "Fica até o fim", gatilho: "f1" },
        { texto: "Confere o caderno de assinaturas contra o boletim", gatilho: "f2" },
      ]}
    />
  );
};
