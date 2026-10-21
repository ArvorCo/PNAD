import type { ReactNode } from "react";
import { AbsoluteFill } from "remotion";
import { CAPTURAS } from "../dados";
import { useFormato } from "../formato";
import { FPS } from "../plano";
import { COR, MONO } from "../tema";
import type { Captura, FormatoMidia } from "../tipos";
import { Clipe, type Foco } from "./Clipe";
import { ehPendente, resolverMidia } from "./fonteMidia";

/** `capturas.json` traz, além do contrato, os tempos de cada still por formato. */
type CapturaPorFormato = Captura & {
  por_formato?: Partial<Record<FormatoMidia, { segundos: number; stills: Record<string, number> }>>;
};

/** Formato do arquivo que o `Clipe` vai tocar para este id no formato do vídeo; `null` se pendente. */
export const formatoCaptura = (id: string, vertical: boolean): FormatoMidia | null => {
  const r = resolverMidia(id, vertical ? "9x16" : "16x9", "mp4");
  return ehPendente(r) ? null : r.formato;
};

/** Segundo da gravação em que o still `nome` foi tirado, no formato dado (com reserva no geral). */
export const segundoDoStill = (id: string, nome: string, formato: FormatoMidia | null): number | null => {
  const c = CAPTURAS[id.replace(/^cap_/, "")] as CapturaPorFormato | undefined;
  if (!c) {
    return null;
  }
  const doFormato = formato ? c.por_formato?.[formato]?.stills[nome] : undefined;
  return doFormato ?? c.stills[nome] ?? null;
};

/** Ponto de zoom marcado no tempo da gravação (segundos), como o still que o mostra. */
export type PontoGravacao = { t: number; x: number; y: number; escala: number };

/**
 * Converte pontos marcados no tempo da gravação em `Foco` no tempo da cena, para um clipe que
 * começa no segundo `inicio` da gravação e entra no quadro `deslocamento` da cena.
 */
export const focoDaGravacao = (pontos: PontoGravacao[], inicio: number, deslocamento = 0): Foco[] =>
  pontos.map((p) => ({ quadro: Math.round((p.t - inicio) * FPS) + deslocamento, x: p.x, y: p.y, escala: p.escala }));

/**
 * Aviso pequeno de mídia ainda não gerada, num canto livre da tela (fora da legenda), para o
 * buraco aparecer nos stills sem cobrir o conteúdo da cena.
 */
export const MidiaPendente: React.FC<{ motivo: string }> = ({ motivo }) => {
  const { vertical, margem } = useFormato();
  return (
    <div
      style={{
        position: "absolute",
        right: margem,
        bottom: vertical ? 200 : 150,
        maxWidth: vertical ? 620 : 250,
        padding: "8px 12px",
        border: `2px dashed ${COR.ouro}`,
        borderRadius: 10,
        background: "rgba(6,11,26,0.85)",
        fontFamily: MONO,
        fontSize: 13,
        lineHeight: 1.3,
        color: COR.ouro,
        letterSpacing: 0.5,
      }}
    >
      MÍDIA PENDENTE · {motivo}
    </div>
  );
};

/**
 * Clipe de fundo em tela cheia, atenuado e com véu, atrás do conteúdo da cena. Sem arquivo,
 * mostra só o aviso pequeno de mídia pendente.
 */
export const FundoClipe: React.FC<{ id: string; opacidade?: number; inicio?: number }> = ({ id, opacidade = 0.42, inicio = 0 }) => {
  const { vertical } = useFormato();
  const r = resolverMidia(id, vertical ? "9x16" : "16x9", "mp4");
  if (ehPendente(r)) {
    return <MidiaPendente motivo={r.pendente} />;
  }
  return (
    <AbsoluteFill style={{ opacity: opacidade }}>
      <Clipe id={id} fim="repetir" veu inicio={inicio} />
    </AbsoluteFill>
  );
};

/** Topo da captura em tela cheia no 9:16: abaixo da barra de progresso do HUD. */
export const TOPO_TELA_CHEIA = 126;

/**
 * Captura nativa 9:16 em tela cheia (só no vídeo vertical): escurece o topo para o HUD e, a partir
 * de `corte` (fração da altura da tela), a parte de baixo onde fica o painel.
 */
export const TelaCheia: React.FC<{ children: ReactNode; corte?: number }> = ({ children, corte = 0.5 }) => {
  const { largura, altura } = useFormato();
  // A captura começa logo abaixo do HUD e mantém 9:16, para o cabeçalho do aplicativo não ficar
  // embaixo da marca e do progresso.
  const topo = TOPO_TELA_CHEIA;
  const alturaCaixa = altura - topo;
  const larguraCaixa = Math.min(largura, (alturaCaixa * 9) / 16);
  const c = Math.round(corte * 100);
  return (
    <>
      <div style={{ position: "absolute", top: topo, left: (largura - larguraCaixa) / 2, width: larguraCaixa, height: alturaCaixa, borderRadius: "28px 28px 0 0", overflow: "hidden", boxShadow: "0 0 60px rgba(0,0,0,0.5)" }}>
        {children}
      </div>
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, rgba(6,11,26,0) 0%, rgba(6,11,26,0) ${c - 6}%, rgba(6,11,26,0.97) ${c - 1}%, rgba(6,11,26,1) ${c + 2}%, rgba(6,11,26,1) 100%)`,
        }}
      />
    </>
  );
};


