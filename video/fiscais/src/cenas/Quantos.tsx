import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Caixa, Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Contador } from "../componentes/Contador";
import { rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { quadro, type Cena } from "../plano";
import { COR, MONO } from "../tema";
import type { Dados } from "../tipos";

const Pessoas: React.FC<{ quantidade: number; porPonto: number; inicio: number; cor: string; largura: number }> = ({ quantidade, porPonto, inicio, cor, largura }) => {
  const frame = useCurrentFrame();
  const pontos = Math.ceil(quantidade / porPonto);
  const colunas = Math.max(8, Math.round(Math.sqrt(pontos * 2.2)));
  const tam = Math.min(18, Math.floor(largura / colunas) - 3);
  const visiveis = rampa(frame, inicio, inicio + 50) * pontos;
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 3, width: colunas * (tam + 3), marginTop: 16 }}>
      {Array.from({ length: pontos }, (_, i) => (
        <div key={i} style={{ width: tam, height: tam, borderRadius: tam / 2, background: i < visiveis ? cor : "rgba(255,255,255,0.08)" }} />
      ))}
    </div>
  );
};

/** Quantos fiscais a lista pede, em três recortes, com pictograma. */
export const Quantos: React.FC<{ cena: Cena; dados: Dados }> = ({ cena, dados }) => {
  const { vertical, margem, largura, altura } = useFormato();
  const p = cena.palavras;
  const f = dados.resumo.fiscais_um_por_local;
  const q1 = quadro(p, "CINQUENTA", 3);
  const q2 = quadro(p, "oitocentas", 7);
  const q3 = quadro(p, "dez", 10);
  const qGente = quadro(p, "gente", 13);
  const colunas: [number, number, string, string, number][] = [
    [q1, f.alta, "nível alta", COR.alta, 1],
    [q2, f.alta_media, "alta e média", COR.media, 4],
    [q3, f.todos, "lista inteira", COR.tealClaro, 40],
  ];
  const larguraCol = vertical ? largura - 2 * margem : (largura - 2 * margem - 60) / 3;

  return (
    <AbsoluteFill style={{ padding: `${vertical ? 180 : 160}px ${margem}px ${vertical ? altura * 0.16 + 140 : 230}px`, gap: 24 }}>
      <Entrada inicio={0} de="esquerda">
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <Chip cor={COR.ouro} solido tamanho={22}>um fiscal por local</Chip>
          <Titulo tamanho={vertical ? 44 : 52}>Quantas pessoas isso pede?</Titulo>
        </div>
      </Entrada>
      <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 30, flex: 1, alignItems: vertical ? "stretch" : "flex-start" }}>
        {colunas.map(([q, valor, rotulo, cor, porPonto]) => (
          <Entrada key={rotulo} inicio={q} de="baixo" style={{ flex: 1, minWidth: 0 }}>
            <Caixa cor={cor}>
              <Contador valor={valor} inicio={q} duracao={45} tamanho={vertical ? 64 : 84} cor={cor} />
              <Texto tamanho={22} cor={COR.suave} style={{ fontFamily: MONO, letterSpacing: 2, textTransform: "uppercase", fontSize: 18, marginTop: 6 }}>pessoas · {rotulo}</Texto>
              <Pessoas quantidade={valor} porPonto={porPonto} inicio={q} cor={cor} largura={larguraCol - 60} />
              <Texto tamanho={16} cor={COR.suave} style={{ fontFamily: MONO, marginTop: 8 }}>
                {porPonto === 1 ? "cada ponto, uma pessoa" : `cada ponto, ${porPonto} pessoas`}
              </Texto>
            </Caixa>
          </Entrada>
        ))}
      </div>
      <Entrada inicio={qGente} de="baixo">
        <Titulo tamanho={vertical ? 40 : 48} cor={COR.tealClaro}>É gente que existe. Falta estar na sala.</Titulo>
        <Texto tamanho={vertical ? 18 : 20} cor={COR.suave} style={{ marginTop: 8 }}>Lei 9.504/1997, art. 65, § 1º: um fiscal pode cobrir mais de uma seção no mesmo local.</Texto>
      </Entrada>
    </AbsoluteFill>
  );
};
