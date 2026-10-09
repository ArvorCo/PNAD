import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame } from "remotion";
import { Caixa, Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { CartaoSecao } from "../componentes/CartaoSecao";
import { Contador } from "../componentes/Contador";
import { Mapa } from "../componentes/Mapa";
import { inteiro, rampa } from "../componentes/util";
import { GATILHOS, destaque, pesoTexto } from "../destaques";
import { useFormato } from "../formato";
import { FPS, indiceDa, quadro, quadroDa, type Cena } from "../plano";
import { COR, FONTE, MONO } from "../tema";
import type { Criterio as TCriterio, Dados } from "../tipos";

type Props = { criterio: TCriterio; indice: number; cena: Cena; dados: Dados };

const NumeroGrande: React.FC<{ d: ReturnType<typeof destaque>; inicio: number; vertical: boolean }> = ({ d, inicio, vertical }) => {
  const frame = useCurrentFrame();
  const entrada = rampa(frame, inicio, inicio + 12);
  return (
    <Caixa cor={d.cor} style={{ flex: 1, minWidth: 0, opacity: entrada, transform: `scale(${0.9 + 0.1 * entrada})` }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
        {typeof d.valor === "number" ? (
          <Contador valor={d.valor} inicio={inicio} casas={d.casas} prefixo={d.prefixo} sufixo={d.sufixo} tamanho={vertical ? 72 : 84} cor={d.cor} />
        ) : (
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: vertical ? 72 : 84, color: d.cor, lineHeight: 1 }}>{d.valor}</span>
        )}
      </div>
      <Texto tamanho={vertical ? 24 : 26} style={{ marginTop: 10, fontWeight: 700 }}>{d.rotulo}</Texto>
      <Texto tamanho={vertical ? 20 : 21} cor={COR.suave} style={{ marginTop: 6 }}>{d.legenda}</Texto>
    </Caixa>
  );
};

/** Uma fase por critério: regra, seção real com os números, número em destaque e o que conferir. */
export const CriterioCena: React.FC<Props> = ({ criterio, indice, cena, dados }) => {
  const frame = useCurrentFrame();
  const { vertical, largura, altura, margem } = useFormato();
  const g = GATILHOS[criterio.id];
  const palavras = cena.palavras;
  const iCartao = indiceDa(palavras, g.cartao);
  const qCartao = quadro(palavras, g.cartao, 5);
  const iNumero = indiceDa(palavras, g.numero, iCartao);
  const qNumero = quadroDa(palavras, g.numero, iCartao) ?? qCartao + 90;
  const qConferir = quadroDa(palavras, g.conferir, iNumero) ?? Math.round(cena.segundos * 0.72 * FPS);
  const d = destaque(criterio, dados);
  const topo = vertical ? 170 : 150;
  const base = vertical ? altura * 0.16 + 150 : 240;
  const mapaTamanho = vertical ? 380 : 300;

  const cabecalho = (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <Entrada inicio={0} de="esquerda">
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <Chip cor={COR.ouro} solido tamanho={vertical ? 20 : 22}>
            critério {String(indice).padStart(2, "0")} / 12
          </Chip>
          <Chip cor={COR.suave} tamanho={vertical ? 15 : 16}>{pesoTexto(criterio)}</Chip>
        </div>
      </Entrada>
      <Entrada inicio={6} de="esquerda">
        <Titulo tamanho={vertical ? 46 : 50}>{criterio.nome.charAt(0).toUpperCase() + criterio.nome.slice(1)}</Titulo>
      </Entrada>
      <Entrada inicio={14} de="esquerda">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontFamily: MONO, fontSize: vertical ? 18 : 19, color: COR.tealClaro, letterSpacing: 1.5 }}>LIMIAR</span>
          <Texto tamanho={vertical ? 22 : 24} cor={COR.tinta}>{criterio.limiar}</Texto>
        </div>
      </Entrada>
      <Entrada inicio={22} de="esquerda">
        <div style={{ display: "flex", gap: 18, alignItems: "baseline", fontFamily: MONO, color: COR.suave, fontSize: vertical ? 18 : 19, letterSpacing: 1 }}>
          <span><span style={{ color: COR.tinta, fontWeight: 700, fontSize: vertical ? 30 : 34 }}>{inteiro(criterio.secoes)}</span> seções</span>
          <span style={{ color: COR.alta }}>{inteiro(criterio.por_nivel.alta)} alta</span>
          <span style={{ color: COR.media }}>{inteiro(criterio.por_nivel.media)} média</span>
          <span style={{ color: COR.baixa }}>{inteiro(criterio.por_nivel.baixa)} baixa</span>
        </div>
      </Entrada>
    </div>
  );

  const conferir = frame >= qConferir ? (
    <Entrada inicio={qConferir} de="baixo">
      <Caixa cor={COR.outros} titulo="O QUE O FISCAL CONFERE">
        <Texto tamanho={vertical ? 24 : 24}>{criterio.o_que_conferir}</Texto>
      </Caixa>
    </Entrada>
  ) : (
    <Entrada inicio={30} de="baixo">
      <Caixa cor={COR.suave} titulo="EXPLICAÇÃO COMUM">
        <Texto tamanho={vertical ? 22 : 22} cor={COR.suave}>{criterio.explicacao_comum}</Texto>
      </Caixa>
    </Entrada>
  );

  const mapa = (
    <Entrada inicio={qCartao + 8} de="zoom" style={{ width: mapaTamanho, flex: "none" }}>
      <Mapa mapa={dados.mapa} tamanho={mapaTamanho} inicio={qCartao - 30} realce={[criterio.exemplo.uf]} alvo={criterio.exemplo.xy} />
    </Entrada>
  );

  return (
    <AbsoluteFill>
      <Audio src={staticFile("sfx/stamp.mp3")} volume={0.35} />
      <Sequence from={qCartao} durationInFrames={60}>
        <Audio src={staticFile("sfx/scan.mp3")} volume={0.25} />
      </Sequence>
      <Sequence from={qNumero} durationInFrames={30}>
        <Audio src={staticFile("sfx/blip.mp3")} volume={0.4} />
      </Sequence>
      {vertical ? (
        <div style={{ position: "absolute", left: margem, right: margem, top: topo, bottom: base, display: "flex", flexDirection: "column", gap: 26 }}>
          {cabecalho}
          <CartaoSecao exemplo={criterio.exemplo} inicio={qCartao} />
          <div style={{ display: "flex", gap: 18, alignItems: "stretch" }}>
            {frame >= qNumero ? <NumeroGrande d={d} inicio={qNumero} vertical /> : <div style={{ flex: 1 }} />}
            {mapa}
          </div>
          {conferir}
        </div>
      ) : (
        <div style={{ position: "absolute", left: margem, right: margem, top: topo, bottom: base, display: "flex", gap: 36 }}>
          <div style={{ width: largura * 0.33, display: "flex", flexDirection: "column", gap: 24 }}>
            {cabecalho}
            <div style={{ flex: 1 }} />
            {conferir}
          </div>
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 22, minWidth: 0 }}>
            <CartaoSecao exemplo={criterio.exemplo} inicio={qCartao} />
            <div style={{ display: "flex", gap: 22, alignItems: "stretch", flex: 1 }}>
              {frame >= qNumero ? <NumeroGrande d={d} inicio={qNumero} vertical={false} /> : <div style={{ flex: 1 }} />}
              {mapa}
            </div>
          </div>
        </div>
      )}
      <div style={{ position: "absolute", right: margem, top: topo - 8, fontFamily: FONTE, fontSize: 120, fontWeight: 700, color: COR.tinta, opacity: 0.06, lineHeight: 1 }}>
        {criterio.id.toUpperCase()}
      </div>
    </AbsoluteFill>
  );
};
