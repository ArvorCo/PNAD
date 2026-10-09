import { AbsoluteFill, useCurrentFrame } from "remotion";
import { useFormato } from "../formato";
import { COR } from "../tema";
import { ruido } from "./util";

const PARTICULAS = 70;

/** Fundo de jogo: gradiente noturno, grade em perspectiva, partículas e varredura. */
export const Fundo: React.FC = () => {
  const frame = useCurrentFrame();
  const { largura, altura } = useFormato();
  const deslocaGrade = (frame * 0.35) % 80;
  const varredura = ((frame * 2.2) % (altura + 600)) - 300;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse at 30% 10%, ${COR.fundo1} 0%, ${COR.fundo0} 60%, #03060f 100%)`,
      }}
    >
      <svg
        width={largura}
        height={altura}
        style={{ position: "absolute", inset: 0, opacity: 0.55 }}
      >
        <defs>
          <pattern
            id="grade"
            width={80}
            height={80}
            patternUnits="userSpaceOnUse"
            patternTransform={`translate(${deslocaGrade} ${deslocaGrade * 0.6})`}
          >
            <path
              d="M 80 0 L 0 0 0 80"
              fill="none"
              stroke={COR.teal}
              strokeOpacity={0.16}
              strokeWidth={1}
            />
          </pattern>
          <linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="white" stopOpacity={0.15} />
            <stop offset="0.5" stopColor="white" stopOpacity={0.6} />
            <stop offset="1" stopColor="white" stopOpacity={0.1} />
          </linearGradient>
          <mask id="mascara">
            <rect width={largura} height={altura} fill="url(#fade)" />
          </mask>
        </defs>
        <rect width={largura} height={altura} fill="url(#grade)" mask="url(#mascara)" />
        {Array.from({ length: PARTICULAS }, (_, i) => {
          const x = ruido(i * 3 + 1) * largura;
          const velocidade = 0.25 + ruido(i * 3 + 2) * 0.6;
          const y = (altura + ((ruido(i * 3 + 3) * altura - frame * velocidade) % (altura + 40))) % (altura + 40);
          const r = 1 + ruido(i * 7) * 2.2;
          const brilho = 0.25 + 0.45 * Math.abs(Math.sin(frame * 0.03 + i));
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r={r}
              fill={i % 5 === 0 ? COR.tealClaro : COR.suave}
              opacity={brilho}
            />
          );
        })}
        <rect
          x={0}
          y={varredura}
          width={largura}
          height={220}
          fill={COR.tealClaro}
          opacity={0.05}
        />
      </svg>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at 50% 50%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.55) 100%)",
        }}
      />
    </AbsoluteFill>
  );
};
