import { useCurrentFrame } from "remotion";
import { COR } from "../tema";
import type { MapaUf } from "../tipos";
import { rampa, suave } from "./util";

type Props = {
  mapa: { view: number; ufs: MapaUf[] };
  /** Quadro em que o contorno começa a ser desenhado. */
  inicio: number;
  /** UF → cor de preenchimento; UF sem cor fica só no contorno. */
  cores: Record<string, string>;
  /** UFs com contorno realçado. */
  destaque?: string[];
};

/** Mapa do Brasil em SVG: contorno que se desenha, depois o preenchimento por UF. */
export const MapaCores: React.FC<Props> = ({ mapa, inicio, cores, destaque = [] }) => {
  const frame = useCurrentFrame();
  const traco = suave(rampa(frame, inicio, inicio + 45));
  const preenche = rampa(frame, inicio + 25, inicio + 65);
  return (
    <svg width="100%" height="100%" viewBox={`0 0 ${mapa.view} ${mapa.view}`} preserveAspectRatio="xMidYMid meet" style={{ overflow: "visible" }}>
      {mapa.ufs.map((u) => {
        const forte = destaque.includes(u.uf);
        const cor = cores[u.uf];
        return (
          <path
            key={u.uf}
            d={u.d}
            pathLength={1}
            fill={cor ?? "none"}
            fillOpacity={cor ? preenche : 0}
            stroke={forte ? COR.papel : COR.tealClaro}
            strokeWidth={forte ? 3 : 1.4}
            strokeDasharray={1}
            strokeDashoffset={1 - traco}
            strokeLinejoin="round"
          />
        );
      })}
    </svg>
  );
};
