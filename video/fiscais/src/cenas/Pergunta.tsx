import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Caixa, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Contador } from "../componentes/Contador";
import { rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { quadro, type Cena } from "../plano";
import { COR, MONO } from "../tema";
import type { Dados } from "../tipos";

const Numero: React.FC<{ valor: number; rotulo: string; inicio: number; cor?: string; casas?: number; sufixo?: string; tamanho: number }> = ({ valor, rotulo, inicio, cor = COR.tinta, casas, sufixo, tamanho }) => (
  <Entrada inicio={inicio} de="baixo" style={{ flex: 1, minWidth: 0 }}>
    <Caixa cor={cor} style={{ height: "100%" }}>
      <Contador valor={valor} inicio={inicio} duracao={50} tamanho={tamanho} cor={cor} casas={casas} sufixo={sufixo} />
      <Texto tamanho={24} cor={COR.suave} style={{ marginTop: 8, fontFamily: MONO, letterSpacing: 1.5, textTransform: "uppercase", fontSize: 18 }}>{rotulo}</Texto>
    </Caixa>
  </Entrada>
);

/** O que foi lido, o que saiu e as três frases que valem para tudo. */
export const Pergunta: React.FC<{ cena: Cena; dados: Dados }> = ({ cena, dados }) => {
  const frame = useCurrentFrame();
  const { vertical, margem, altura } = useFormato();
  const p = cena.palavras;
  const r = dados.resumo;
  const qLidas = quadro(p, "quatrocentas", 2.5);
  const qDoze = quadro(p, "Doze", 8);
  const qTreze = quadro(p, "TREZE", 14);
  const qPct = quadro(p, "dois", 17);
  const qLocais = quadro(p, "dez", 19);
  const qFrases = quadro(p, "Antes", 26);
  const qF1 = quadro(p, "Atipicidade", 30);
  const qF2 = quadro(p, "lista", 34);
  const qF3 = quadro(p, "resolve", 38);
  const somem = 1 - rampa(frame, qFrases - 8, qFrases + 6);
  const tam = vertical ? 64 : 76;

  return (
    <AbsoluteFill style={{ padding: `${vertical ? 180 : 160}px ${margem}px ${vertical ? altura * 0.16 + 140 : 230}px` }}>
      {somem > 0 ? (
        <div style={{ opacity: somem, display: "flex", flexDirection: "column", gap: 22, height: "100%" }}>
          <Entrada inicio={0} de="esquerda">
            <Titulo tamanho={vertical ? 46 : 54}>Lemos todos os boletins de urna do 1º turno</Titulo>
          </Entrada>
          <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 22, flex: vertical ? "none" : 1 }}>
            <Numero valor={r.secoes_universo} rotulo="seções lidas, uma a uma" inicio={qLidas} tamanho={tam} />
            <Numero valor={12} rotulo="critérios com regra e peso declarados" inicio={qDoze} cor={COR.ouro} tamanho={tam} />
          </div>
          <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 22, flex: vertical ? "none" : 1 }}>
            <Numero valor={r.secoes_sinalizadas} rotulo="seções sinalizadas" inicio={qTreze} cor={COR.alta} tamanho={tam} />
            <Numero valor={r.pct_sinalizadas} rotulo="do eleitorado do país" inicio={qPct} cor={COR.tealClaro} casas={1} sufixo="%" tamanho={tam} />
            <Numero valor={r.fiscais_um_por_local.todos} rotulo="locais de votação, com endereço" inicio={qLocais} cor={COR.media} tamanho={tam} />
          </div>
        </div>
      ) : null}
      {frame >= qFrases ? (
        <AbsoluteFill style={{ padding: `${vertical ? 180 : 160}px ${margem}px`, justifyContent: "center", gap: 26 }}>
          <Entrada inicio={qFrases} de="esquerda">
            <Titulo tamanho={vertical ? 40 : 44} cor={COR.tealClaro}>Três frases que valem para tudo</Titulo>
          </Entrada>
          {[
            [qF1, "01", dados.rotulos.atipico, COR.alta],
            [qF2, "02", dados.rotulos.prioridade, COR.media],
            [qF3, "03", dados.rotulos.resolve, COR.outros],
          ].map(([q, n, texto, cor]) => (
            <Entrada key={String(n)} inicio={Number(q)} de="esquerda">
              <Caixa cor={String(cor)} style={{ display: "flex", gap: 24, alignItems: "center" }}>
                <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: vertical ? 48 : 60, color: String(cor) }}>{String(n)}</span>
                <Titulo tamanho={vertical ? 40 : 46}>{String(texto)}</Titulo>
              </Caixa>
            </Entrada>
          ))}
        </AbsoluteFill>
      ) : null}
    </AbsoluteFill>
  );
};
