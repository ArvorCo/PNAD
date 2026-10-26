import { useCurrentFrame } from "remotion";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import { rampa, suave } from "./util";

export type Serie = { nome: string; cor: string; pontos: [number, number][]; tracejada?: boolean };
/** Linha vertical rotulada; `quadro` é o quadro da cena em que aparece (falta = desde o início). */
export type Marca = { x: number; rotulo: string; cor?: string; quadro?: number };
/** Faixa vertical sombreada entre dois valores de x. */
export type Faixa = { de: number; ate: number; rotulo: string; cor?: string; quadro?: number };

type Props = {
  series: Serie[];
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  ticksX: readonly number[];
  ticksY: readonly number[];
  formatoX: (x: number) => string;
  formatoY: (y: number) => string;
  /** Quadro em que as linhas começam a se desenhar e quantos quadros levam. */
  inicio: number;
  duracao?: number;
  marcas?: Marca[];
  faixas?: Faixa[];
};

const L = 1000;
const A = 520;
const ME = 78;
const MD = 24;
const MT = 26;
const MB = 52;

/** Gráfico de linhas de série temporal em SVG, desenhado da esquerda para a direita. */
export const SerieGrafico: React.FC<Props> = ({
  series,
  xMin,
  xMax,
  yMin,
  yMax,
  ticksX,
  ticksY,
  formatoX,
  formatoY,
  inicio,
  duracao = 90,
  marcas = [],
  faixas = [],
}) => {
  const frame = useCurrentFrame();
  const { escala } = useFormato();
  const progresso = suave(rampa(frame, inicio, inicio + duracao));
  const px = (x: number): number => ME + ((x - xMin) / (xMax - xMin)) * (L - ME - MD);
  const py = (y: number): number => A - MB - ((y - yMin) / (yMax - yMin)) * (A - MB - MT);
  const corte = xMin + progresso * (xMax - xMin);
  const fonte = 17 * (escala < 1 ? 1.1 : 1);

  return (
    <svg viewBox={`0 0 ${L} ${A}`} width="100%" height="100%" preserveAspectRatio="xMidYMid meet" style={{ overflow: "visible" }}>
      {faixas.map((f) => {
        const o = f.quadro === undefined ? 1 : rampa(frame, f.quadro, f.quadro + 12);
        return (
          <g key={`${f.de}-${f.ate}`} opacity={o}>
            <rect x={px(f.de)} y={MT} width={px(f.ate) - px(f.de)} height={A - MB - MT} fill={f.cor ?? COR.alta} fillOpacity={0.18} />
            <text x={(px(f.de) + px(f.ate)) / 2} y={MT + 22} textAnchor="middle" fontFamily={MONO} fontWeight={700} fontSize={fonte} fill={f.cor ?? COR.alta}>
              {f.rotulo}
            </text>
          </g>
        );
      })}
      {ticksY.map((y) => (
        <g key={`y${y}`}>
          <line x1={ME} x2={L - MD} y1={py(y)} y2={py(y)} stroke={COR.linha} strokeWidth={1} />
          <text x={ME - 10} y={py(y) + 5} textAnchor="end" fontFamily={MONO} fontSize={fonte} fill={COR.suave}>
            {formatoY(y)}
          </text>
        </g>
      ))}
      {ticksX.map((x) => (
        <text key={`x${x}`} x={px(x)} y={A - MB + 26} textAnchor="middle" fontFamily={MONO} fontSize={fonte} fill={COR.suave}>
          {formatoX(x)}
        </text>
      ))}
      {marcas.map((m) => {
        const o = m.quadro === undefined ? 1 : rampa(frame, m.quadro, m.quadro + 10);
        const cor = m.cor ?? COR.ouro;
        return (
          <g key={`${m.x}-${m.rotulo}`} opacity={o}>
            <line x1={px(m.x)} x2={px(m.x)} y1={MT} y2={A - MB} stroke={cor} strokeWidth={2} strokeDasharray="6 5" />
            <text x={px(m.x) + 8} y={MT + 14} fontFamily={FONTE} fontWeight={700} fontSize={fonte} fill={cor}>
              {m.rotulo}
            </text>
          </g>
        );
      })}
      {series.map((s) => {
        const visiveis = s.pontos.filter(([x]) => x >= xMin && x <= corte);
        if (visiveis.length < 2) {
          return null;
        }
        const d = visiveis.map(([x, y], i) => `${i === 0 ? "M" : "L"}${px(x).toFixed(1)} ${py(y).toFixed(1)}`).join(" ");
        const [xf, yf] = visiveis[visiveis.length - 1];
        return (
          <g key={s.nome}>
            <path d={d} fill="none" stroke={s.cor} strokeWidth={4} strokeLinejoin="round" strokeLinecap="round" strokeDasharray={s.tracejada ? "10 8" : undefined} />
            <circle cx={px(xf)} cy={py(yf)} r={6} fill={s.cor} />
          </g>
        );
      })}
      {series.map((s, i) => (
        <g key={`lg-${s.nome}`}>
          <rect x={ME + i * 230} y={A - 18} width={18} height={6} fill={s.cor} />
          <text x={ME + i * 230 + 26} y={A - 10} fontFamily={FONTE} fontWeight={700} fontSize={fonte} fill={COR.tinta}>
            {s.nome}
          </text>
        </g>
      ))}
    </svg>
  );
};
