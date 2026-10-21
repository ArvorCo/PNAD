// Ficha do prédio no 9:16, montada sobre a gravação nativa do celular. Na gravação o mapa ocupa o
// topo e a ficha rola por baixo do botão "Fechar ficha"; com o painel da cena em cima da metade de
// baixo, sobrava só o mapa e o botão. Aqui o mapa ao vivo aparece primeiro, a ficha sobe por cima
// dele como no aplicativo, e a rolagem é uma tira feita dos stills `ficha` e `cartas`, cortada logo
// abaixo do botão, que desce até a carta em atenção 3 no tempo da narração.
import { Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { useFormato } from "../formato";
import { COR } from "../tema";
import { Clipe } from "./Clipe";
import { ehPendente, resolverMidia } from "./fonteMidia";
import { TOPO_TELA_CHEIA } from "./Gravacao";
import { MidiaAusente } from "./MidiaAusente";
import { mola } from "./util";

/** Largura e altura dos stills e da gravação 9:16, em px. */
const LARGURA_FONTE = 1080;
const ALTURA_FONTE = 1920;
/** Linha do still em que começa a ficha (a borda escura do painel do aplicativo). */
const BASE_MAPA = 730;
/** Centro do marcador do prédio no mapa da gravação 9:16 (igual em RJ e SP). */
const MARCADOR = { x: 540, y: 594 } as const;
/** Fundo da página da ficha (rgb lido no still). */
const PAPEL_FICHA = "rgb(255,253,248)";

/**
 * Medidas dos stills 9:16 de 17/10, lidas pixel a pixel (1080 × 1920). Linhas "da tira" contam a
 * partir de `corte`: a tira é `ficha[corte, emenda)` seguida de `cartas[inicioCartas, 1920)`.
 */
type Recorte = {
  /** Primeira linha só de fundo abaixo do botão "Fechar ficha" no still `ficha`. */
  corte: number;
  /** Linha do still `ficha` idêntica à linha `inicioCartas` do still `cartas`. */
  emenda: number;
  inicioCartas: number;
  /** Primeira carta de seção, logo abaixo do cabeçalho do prédio (linhas da tira). */
  primeira: readonly [number, number];
  /** Link "Ficha completa da seção no Politize" da primeira carta (linhas da tira). */
  linkPrimeira: readonly [number, number];
  /** Carta da seção em atenção 3, a de borda dourada (linhas da tira). */
  alvo: readonly [number, number];
};

export const RECORTES_FICHA: Record<string, Recorte> = {
  cap_mapa_predio_rj: { corte: 846, emenda: 1717, inicioCartas: 860, primeira: [262, 841], linkPrimeira: [792, 818], alvo: [867, 1413] },
  cap_mapa_predio_sp: { corte: 846, emenda: 1810, inicioCartas: 860, primeira: [303, 935], linkPrimeira: [886, 912], alvo: [961, 1464] },
};

/** Linha da tira no topo da folha a partir de um quadro da cena. */
export type ParadaFolha = { quadro: number; linha: number };

/** Moldura que acende sobre um trecho da tira (carta ou link) a partir de um quadro. */
export type RealceFolha = { de: number; linhas: readonly [number, number]; cor?: string };

type Props = {
  /** `cap_mapa_predio_rj` ou `cap_mapa_predio_sp`. */
  captura: string;
  /** Altura nítida da caixa da tela cheia (`useJanelaTelaCheia`). */
  janela: number;
  /** Segundo da gravação em que o mapa ao vivo começa. */
  inicioGravacao: number;
  /** Quadro em que a ficha sobe sobre o mapa. */
  qSobe: number;
  paradas: ParadaFolha[];
  realces?: RealceFolha[];
};

/**
 * Início do painel das cenas do mapa no 9:16 (fração da área útil): mais baixo que o padrão, porque
 * o painel delas cabe em menos altura e a ficha precisa de janela para mostrar uma carta inteira.
 */
export const INICIO_PAINEL_MAPA = 0.64;

/** Faixa do mapa, em px da caixa, que continua à vista acima da ficha aberta (marcador e rótulo). */
const FAIXA_MAPA = 210;
/** Altura da alça no topo da folha, em px da caixa. */
const ALCA = 24;

const recorteDoStill = (id: string, nome: string) => resolverMidia(id, "9x16", "png", nome);

export const FolhaPredioVertical: React.FC<Props> = ({ captura, janela, inicioGravacao, qSobe, paradas, realces = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { largura, altura } = useFormato();
  const recorte = RECORTES_FICHA[captura];
  const ficha = recorteDoStill(captura, "ficha");
  const cartas = recorteDoStill(captura, "cartas");
  if (!recorte || ehPendente(ficha) || ehPendente(cartas)) {
    const motivo = !recorte ? `${captura}: sem recorte medido` : ehPendente(ficha) ? ficha.pendente : ehPendente(cartas) ? cartas.pendente : "";
    return <MidiaAusente motivo={motivo} />;
  }

  // Caixa da TelaCheia: largura útil e px da caixa por px da fonte.
  const larguraCaixa = Math.min(largura, ((altura - TOPO_TELA_CHEIA) * 9) / 16);
  const k = larguraCaixa / LARGURA_FONTE;

  // Mapa ao vivo ampliado, com a borda da ficha da gravação escondida no degradê do painel; ao abrir
  // a ficha, sobe até o marcador e o rótulo das seções ficarem na faixa de cima.
  const sobe = frame < qSobe ? 0 : mola(frame, fps, qSobe, { damping: 20, stiffness: 90 });
  const km = k * 1.4;
  const topoMapaInicial = janela + 90 - BASE_MAPA * km;
  const topoMapaFinal = FAIXA_MAPA * 0.36 - MARCADOR.y * km;
  const topoMapa = topoMapaInicial + (topoMapaFinal - topoMapaInicial) * sobe;
  const topoFolha = janela + 60 + (FAIXA_MAPA - janela - 60) * sobe;

  const ordenadas = [...paradas].sort((a, b) => a.quadro - b.quadro);
  const linha =
    ordenadas.length === 0
      ? 0
      : ordenadas.length === 1
        ? ordenadas[0].linha
        : interpolate(
            frame,
            ordenadas.map((p) => p.quadro),
            ordenadas.map((p) => p.linha),
            { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) },
          );
  const pulso = 0.5 + 0.5 * Math.sin(frame * 0.22);
  const alturaFicha = (recorte.emenda - recorte.corte) * k;
  const alturaCartas = (ALTURA_FONTE - recorte.inicioCartas) * k;
  const imagem = (arquivo: string, linhaTopo: number, alturaFaixa: number) => (
    <div style={{ position: "relative", height: alturaFaixa, overflow: "hidden" }}>
      <Img src={staticFile(arquivo)} style={{ position: "absolute", left: 0, top: -linhaTopo * k, width: larguraCaixa, height: ALTURA_FONTE * k }} />
    </div>
  );

  return (
    <div style={{ position: "absolute", inset: 0 }}>
      {/* O mapa é cortado na borda da ficha da gravação, para o papel dela nunca aparecer no degradê. */}
      <div style={{ position: "absolute", left: 0, top: 0, width: "100%", height: Math.max(0, topoMapa + BASE_MAPA * km), overflow: "hidden" }}>
        <div
          style={{
            position: "absolute",
            left: larguraCaixa / 2 - MARCADOR.x * km,
            top: topoMapa,
            width: LARGURA_FONTE * km,
            height: ALTURA_FONTE * km,
          }}
        >
          <Clipe id={captura} inicio={inicioGravacao} />
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: topoFolha,
          bottom: 0,
          background: PAPEL_FICHA,
          borderRadius: "26px 26px 0 0",
          boxShadow: "0 -14px 40px rgba(6,11,26,0.35)",
          overflow: "hidden",
          paddingTop: ALCA,
        }}
      >
        <div style={{ position: "relative", transform: `translateY(${-linha * k}px)` }}>
          {imagem(ficha.arquivo, recorte.corte, alturaFicha)}
          {imagem(cartas.arquivo, recorte.inicioCartas, alturaCartas)}
          {realces.map((r, i) =>
            frame < r.de ? null : (
              <div
                key={i}
                style={{
                  position: "absolute",
                  left: 18 * k,
                  width: (LARGURA_FONTE - 36) * k,
                  top: r.linhas[0] * k - 6,
                  height: (r.linhas[1] - r.linhas[0]) * k + 12,
                  borderRadius: 18,
                  border: `4px solid ${r.cor ?? COR.ouro}`,
                  boxShadow: `0 0 ${18 + 16 * pulso}px ${r.cor ?? COR.ouro}`,
                  opacity: Math.min(1, (frame - r.de) / 10),
                }}
              />
            ),
          )}
        </div>
        {/* Alça fixa da folha: a tira rola por baixo dela. */}
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: ALCA, background: PAPEL_FICHA, boxShadow: "0 6px 10px -8px rgba(6,11,26,0.35)" }}>
          <div style={{ position: "absolute", top: 9, left: "50%", width: 70, height: 6, marginLeft: -35, borderRadius: 3, background: "rgba(6,11,26,0.25)" }} />
        </div>
      </div>
    </div>
  );
};
