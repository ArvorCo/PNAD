import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Contador } from "../componentes/Contador";
import { inteiro, mola } from "../componentes/util";
import { useFormato } from "../formato";
import { quadro, type Cena } from "../plano";
import { COR, MONO, NIVEL_COR, NIVEL_NOME } from "../tema";
import type { Dados, Nivel } from "../tipos";

const Degrau: React.FC<{ nivel: Nivel; inicio: number; largura: number; dados: Dados; regra: string; vertical: boolean }> = ({ nivel, inicio, largura, dados, regra, vertical }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = mola(frame, fps, inicio, { damping: 15 });
  if (frame < inicio) {
    return null;
  }
  const cor = NIVEL_COR[nivel];
  const n = dados.resumo.por_nivel[nivel];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 26, opacity: p }}>
      <div style={{ width: largura * p, height: vertical ? 96 : 110, background: `linear-gradient(90deg, ${cor}, ${cor}66)`, borderRadius: 12, boxShadow: `0 0 30px ${cor}55`, flex: "none", display: "flex", alignItems: "center", paddingLeft: 24 }}>
        <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: vertical ? 30 : 34, color: COR.fundo0, letterSpacing: 3 }}>{NIVEL_NOME[nivel]}</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0 }}>
        <Contador valor={n.secoes} inicio={inicio} duracao={45} tamanho={vertical ? 64 : 74} cor={cor} />
        <Texto tamanho={vertical ? 20 : 22} cor={COR.suave}>
          seções · {inteiro(n.locais)} locais · {inteiro(n.municipios)} municípios
        </Texto>
        <Texto tamanho={vertical ? 18 : 20} cor={COR.tinta} style={{ opacity: 0.85 }}>{regra}</Texto>
      </div>
    </div>
  );
};

/** Pirâmide dos três níveis, com a regra de corte de cada um. */
export const Niveis: React.FC<{ cena: Cena; dados: Dados }> = ({ cena, dados }) => {
  const { vertical, margem, largura, altura } = useFormato();
  const p = cena.palavras;
  const qRegra = quadro(p, "Nível", 3);
  const qAlta = quadro(p, "OITENTA", 8);
  const qMedia = quadro(p, "mil", 14);
  const qBaixa = quadro(p, "onze", 17);
  const qDoze = quadro(p, "doze", 21);
  const base = vertical ? largura - 2 * margem - 330 : largura * 0.42;

  return (
    <AbsoluteFill style={{ padding: `${vertical ? 180 : 160}px ${margem}px ${vertical ? altura * 0.16 + 140 : 230}px`, justifyContent: "center", gap: vertical ? 30 : 34 }}>
      <Entrada inicio={0} de="esquerda">
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <Chip cor={COR.ouro} solido tamanho={22}>pesos somados</Chip>
          <Titulo tamanho={vertical ? 44 : 52}>Três níveis de prioridade</Titulo>
        </div>
      </Entrada>
      <Entrada inicio={qRegra} de="esquerda">
        <Texto tamanho={vertical ? 24 : 26} cor={COR.suave}>Cada critério tem peso de 1 a 3. A soma dos pesos da seção decide o nível.</Texto>
      </Entrada>
      <Degrau nivel="alta" inicio={qAlta} largura={base * 0.42} dados={dados} regra="pontuação 5 ou mais e nenhuma explicação comum no cadastro" vertical={vertical} />
      <Degrau nivel="media" inicio={qMedia} largura={base * 0.68} dados={dados} regra="pontuação 3 ou mais, ou 5 ou mais com explicação comum" vertical={vertical} />
      <Degrau nivel="baixa" inicio={qBaixa} largura={base} dados={dados} regra="o resto; aldeia e presídio nunca sobem de nível" vertical={vertical} />
      <Entrada inicio={qDoze} de="baixo">
        <Chip cor={COR.tealClaro} tamanho={vertical ? 20 : 24}>a seguir: 12 critérios, 12 seções reais</Chip>
      </Entrada>
    </AbsoluteFill>
  );
};
