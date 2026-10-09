import { useCurrentFrame } from "remotion";
import { COR, NIVEL_COR } from "../tema";
import type { Dados } from "../tipos";
import { rampa, suave } from "./util";

type Props = {
  mapa: Dados["mapa"];
  tamanho: number;
  /** Quadro em que o contorno começa a ser desenhado. */
  inicio: number;
  /** Quadro em que os pontos começam a aparecer; `null` esconde os pontos. */
  inicioPontos?: number | null;
  /** Coordenada projetada para marcar um alvo com anel pulsante. */
  alvo?: [number, number] | null;
  /** UFs a realçar com preenchimento mais forte. */
  realce?: string[];
  /** Rótulos de UF a escrever (sigla → texto). */
  rotulos?: Record<string, string>;
  centros?: Record<string, [number, number]>;
};

/** Mapa do Brasil em SVG, contorno desenhado com dasharray, pontos por nível e alvo pulsante. */
export const Mapa: React.FC<Props> = ({
  mapa,
  tamanho,
  inicio,
  inicioPontos = null,
  alvo = null,
  realce = [],
  rotulos = {},
  centros = {},
}) => {
  const frame = useCurrentFrame();
  const traco = suave(rampa(frame, inicio, inicio + 55));
  const preenche = rampa(frame, inicio + 30, inicio + 70);
  const pontosP = inicioPontos === null ? 0 : suave(rampa(frame, inicioPontos, inicioPontos + 90));
  const nAlta = mapa.pontos.length;
  const nBaixa = mapa.pontos_baixa.length;
  const pulso = (frame % 40) / 40;

  return (
    <svg
      width={tamanho}
      height={tamanho}
      viewBox={`0 0 ${mapa.view} ${mapa.view}`}
      style={{ overflow: "visible" }}
    >
      <defs>
        <filter id="brilho" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {mapa.ufs.map((u) => {
        const forte = realce.includes(u.uf);
        return (
          <path
            key={u.uf}
            d={u.d}
            pathLength={1}
            fill={forte ? COR.teal : COR.teal}
            fillOpacity={preenche * (forte ? 0.42 : 0.1)}
            stroke={forte ? COR.tealClaro : COR.teal}
            strokeWidth={forte ? 2.6 : 1.4}
            strokeDasharray={1}
            strokeDashoffset={1 - traco}
            strokeLinejoin="round"
          />
        );
      })}
      {pontosP > 0
        ? mapa.pontos_baixa.map(([x, y], i) =>
            i < pontosP * nBaixa ? (
              <circle key={`b${i}`} cx={x} cy={y} r={1.6} fill={COR.baixa} opacity={0.55} />
            ) : null,
          )
        : null}
      {pontosP > 0
        ? mapa.pontos.map(([x, y, nivel], i) => {
            const idx = nAlta - 1 - i;
            if (idx >= pontosP * nAlta) {
              return null;
            }
            const alta = nivel === "alta";
            return (
              <circle
                key={`p${i}`}
                cx={x}
                cy={y}
                r={alta ? 5 : 3}
                fill={NIVEL_COR[nivel]}
                opacity={alta ? 0.95 : 0.8}
                filter={alta ? "url(#brilho)" : undefined}
              />
            );
          })
        : null}
      {Object.entries(rotulos).map(([uf, texto]) => {
        const c = centros[uf];
        if (!c) {
          return null;
        }
        return (
          <g key={uf}>
            <rect
              x={c[0] - 54}
              y={c[1] - 22}
              width={108}
              height={44}
              rx={8}
              fill={COR.fundo0}
              stroke={COR.alta}
              strokeWidth={2}
            />
            <text
              x={c[0]}
              y={c[1] + 9}
              textAnchor="middle"
              fontFamily="JetBrains Mono, monospace"
              fontWeight={700}
              fontSize={26}
              fill={COR.tinta}
            >
              {texto}
            </text>
          </g>
        );
      })}
      {alvo ? (
        <g>
          <circle
            cx={alvo[0]}
            cy={alvo[1]}
            r={10 + pulso * 40}
            fill="none"
            stroke={COR.alta}
            strokeWidth={3}
            opacity={1 - pulso}
          />
          <circle
            cx={alvo[0]}
            cy={alvo[1]}
            r={10 + ((pulso + 0.5) % 1) * 40}
            fill="none"
            stroke={COR.alta}
            strokeWidth={2}
            opacity={1 - ((pulso + 0.5) % 1)}
          />
          <circle cx={alvo[0]} cy={alvo[1]} r={9} fill={COR.alta} filter="url(#brilho)" />
          <line
            x1={alvo[0] - 30}
            x2={alvo[0] + 30}
            y1={alvo[1]}
            y2={alvo[1]}
            stroke={COR.alta}
            strokeWidth={2}
          />
          <line
            x1={alvo[0]}
            x2={alvo[0]}
            y1={alvo[1] - 30}
            y2={alvo[1] + 30}
            stroke={COR.alta}
            strokeWidth={2}
          />
        </g>
      ) : null}
    </svg>
  );
};
