import { useCurrentFrame, useVideoConfig } from "remotion";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { Predio } from "../tipos";
import { ATENCAO_COR, comoNivel, NIVEIS_ATENCAO, nomeAtencao, type NivelAtencao } from "./atencao";
import { inteiro, mola, rampa } from "./util";

type Peca = { secao: number | null; nivel: NivelAtencao | null };

/**
 * Seções do prédio com nível de atenção: a lista `secoes` quando o JSON a traz (com número), senão
 * uma peça sem número por seção contada em `por_atencao`, do nível mais alto para o mais baixo.
 */
const pecasComSinal = (predio: Predio): Peca[] => {
  if (predio.secoes && predio.secoes.length > 0) {
    return [...predio.secoes].sort((a, b) => a.secao - b.secao).map((s) => ({ secao: s.secao, nivel: comoNivel(s.atencao) }));
  }
  return [...NIVEIS_ATENCAO].reverse().flatMap((n) => Array.from({ length: predio.por_atencao[String(n) as "0"] }, () => ({ secao: null, nivel: n })));
};

/** Quantas seções do prédio aparecem no mapa com algum nível de atenção. */
const contarComSinal = (predio: Predio): number => predio.secoes?.length ?? NIVEIS_ATENCAO.reduce<number>((soma, n) => soma + predio.por_atencao[String(n) as "0"], 0);

type GradeProps = {
  predio: Predio;
  /** Quadro em que os ladrilhos começam a entrar (um a cada dois quadros). */
  inicio: number;
  /** Largura disponível em px do formato atual. */
  largura: number;
  colunas: number;
  /** Lado máximo do ladrilho em px de referência. */
  ladoMaximo?: number;
  /** Seção destacada com anel pulsante a partir de `qDestaque`. */
  destaque?: number | null;
  qDestaque?: number;
  /** Nível de atenção aceso (os outros esmaecem); `null` acende todos. */
  nivelAtivo?: NivelAtencao | null;
};

/**
 * Uma peça por seção do prédio: as seções listadas no mapa, na cor do nível de atenção e com o
 * número, e as que não aparecem no mapa (sem sinal no log) em cinza tracejado, até `secoes_total`.
 */
export const GradeSecoes: React.FC<GradeProps> = ({ predio, inicio, largura, colunas, ladoMaximo = 96, destaque = null, qDestaque = 0, nivelAtivo = null }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { t } = useFormato();
  const gap = t(8);
  const lado = Math.min(t(ladoMaximo), (largura - (colunas - 1) * gap) / colunas);
  const listadas = pecasComSinal(predio);
  const semSinal = Math.max(0, predio.secoes_total - listadas.length);
  const pulso = 0.5 + 0.5 * Math.sin(frame * 0.25);
  const pecas: Peca[] = [...listadas, ...Array.from({ length: semSinal }, () => ({ secao: null, nivel: null }))];

  return (
    <div style={{ display: "grid", gridTemplateColumns: `repeat(${colunas}, ${lado}px)`, gap, width: colunas * lado + (colunas - 1) * gap }}>
      {pecas.map((p, i) => {
        const q = inicio + i * 2;
        const e = mola(frame, fps, q, { damping: 13, stiffness: 140 });
        const cor = p.nivel === null ? COR.linha : ATENCAO_COR[p.nivel];
        const cheia = p.nivel !== null && p.nivel > 0;
        const apagada = nivelAtivo !== null && p.nivel !== nivelAtivo;
        const alvo = destaque !== null && p.secao === destaque && frame >= qDestaque;
        const realce = alvo ? rampa(frame, qDestaque, qDestaque + 10) : 0;
        return (
          <div
            key={i}
            style={{
              width: lado,
              height: lado,
              borderRadius: lado * 0.18,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: cheia ? cor : "rgba(6,11,26,0.6)",
              border: p.nivel === null ? `2px dashed ${COR.linha}` : `3px solid ${cor}`,
              opacity: frame < q ? 0 : (apagada ? 0.28 : 1) * Math.min(1, e * 1.4),
              transform: `scale(${(0.6 + 0.4 * e) * (1 + 0.14 * realce)})`,
              boxShadow: alvo ? `0 0 0 ${t(4)}px ${COR.tinta}, 0 0 ${t(30) * pulso + t(10)}px ${cor}` : "none",
              zIndex: alvo ? 2 : 1,
              fontFamily: MONO,
              fontWeight: 700,
              fontSize: lado * 0.3,
              color: cheia ? (p.nivel === 1 ? COR.fundo0 : COR.tinta) : COR.suave,
            }}
          >
            {p.secao ?? "·"}
          </div>
        );
      })}
    </div>
  );
};

type LegendaProps = {
  predio: Predio;
  inicio: number;
  nivelAtivo?: NivelAtencao | null;
  /** Rótulo da última linha, para as seções que não aparecem no mapa. */
  rotuloSemSinal?: string;
  tamanho?: number;
};

/** Contagem por nível de atenção no prédio, com o nível citado aceso. */
export const LegendaAtencao: React.FC<LegendaProps> = ({ predio, inicio, nivelAtivo = null, rotuloSemSinal = "sem sinal no log", tamanho = 21 }) => {
  const frame = useCurrentFrame();
  const { t } = useFormato();
  const semSinal = Math.max(0, predio.secoes_total - contarComSinal(predio));
  const linhas: { chave: string; cor: string; cheia: boolean; n: number; nome: string; nivel: NivelAtencao | null }[] = [
    ...[...NIVEIS_ATENCAO].reverse().map((n) => ({ chave: String(n), cor: ATENCAO_COR[n], cheia: n > 0, n: predio.por_atencao[String(n) as "0"], nome: nomeAtencao(n), nivel: n as NivelAtencao })),
    { chave: "sem", cor: COR.linha, cheia: false, n: semSinal, nome: rotuloSemSinal, nivel: null },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: t(6) }}>
      {linhas.map((l, i) => {
        const q = inicio + i * 4;
        const aceso = nivelAtivo === null || l.nivel === nivelAtivo;
        return (
          <div
            key={l.chave}
            style={{
              display: "flex",
              alignItems: "center",
              gap: t(12),
              opacity: frame < q ? 0 : rampa(frame, q, q + 8) * (aceso ? 1 : 0.35),
              padding: `${t(3)}px ${t(10)}px`,
              borderRadius: 8,
              background: nivelAtivo !== null && l.nivel === nivelAtivo ? `${l.cor}26` : "transparent",
            }}
          >
            <span
              style={{
                width: t(18),
                height: t(18),
                borderRadius: t(5),
                flex: "none",
                background: l.cheia ? l.cor : "transparent",
                border: l.nivel === null ? `2px dashed ${COR.suave}` : `3px solid ${l.cor}`,
              }}
            />
            <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(tamanho + 4), color: COR.tinta, minWidth: t(40), textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
              {inteiro(l.n)}
            </span>
            <span style={{ fontFamily: FONTE, fontWeight: 500, fontSize: t(tamanho), color: aceso ? COR.tinta : COR.suave }}>{l.nome}</span>
          </div>
        );
      })}
    </div>
  );
};
