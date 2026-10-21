import type { CSSProperties } from "react";
import { COR } from "../tema";

type P = { tamanho: number; cor?: string; style?: CSSProperties };

const Svg: React.FC<P & { children: React.ReactNode }> = ({ tamanho, cor = COR.tealClaro, style, children }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 64 64" fill="none" stroke={cor} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" style={{ flex: "none", ...style }}>
    {children}
  </svg>
);

/** Urna eletrônica: tela à esquerda, teclado à direita. */
export const IconeUrna: React.FC<P> = (p) => (
  <Svg {...p}>
    <rect x="6" y="14" width="52" height="36" rx="5" />
    <rect x="12" y="20" width="22" height="16" rx="2" />
    {[0, 1, 2].map((l) =>
      [0, 1, 2].map((c) => <circle key={`${l}${c}`} cx={41 + c * 6} cy={22 + l * 6} r={1.6} fill={p.cor ?? COR.tealClaro} stroke="none" />),
    )}
    <rect x="39" y="40" width="14" height="5" rx="1.5" />
    <path d="M14 50 L10 58 M50 50 L54 58" />
  </Svg>
);

/** Boletim impresso: fita de papel com linhas e um código QR no pé. */
export const IconeBoletim: React.FC<P> = (p) => (
  <Svg {...p}>
    <path d="M16 6 H48 V56 L44 52 L40 56 L36 52 L32 56 L28 52 L24 56 L20 52 L16 56 Z" />
    <path d="M22 14 H42 M22 20 H42 M22 26 H36" />
    <rect x="24" y="32" width="16" height="14" rx="1" />
    <path d="M28 36 H30 M34 36 H36 M28 41 H36" />
  </Svg>
);

/** Cópia afixada: folha presa por um alfinete. */
export const IconeAfixada: React.FC<P> = (p) => (
  <Svg {...p}>
    <rect x="14" y="14" width="36" height="44" rx="3" />
    <path d="M22 28 H42 M22 35 H42 M22 42 H36" />
    <circle cx="32" cy="10" r="5" />
    <path d="M32 15 V20" />
  </Svg>
);

/** Duas pessoas e uma via na mão. */
export const IconePessoas: React.FC<P> = (p) => (
  <Svg {...p}>
    <circle cx="20" cy="18" r="7" />
    <circle cx="40" cy="18" r="7" />
    <path d="M8 50 C8 36 32 36 32 50 M28 50 C28 36 52 36 52 50" />
    <rect x="44" y="34" width="14" height="18" rx="2" />
    <path d="M47 40 H55 M47 45 H53" />
  </Svg>
);

export const IconeCheck: React.FC<P> = (p) => (
  <Svg {...p}>
    <circle cx="32" cy="32" r="24" />
    <path d="M21 33 L29 41 L44 24" />
  </Svg>
);

export const IconeX: React.FC<P> = (p) => (
  <Svg {...p}>
    <circle cx="32" cy="32" r="24" />
    <path d="M23 23 L41 41 M41 23 L23 41" />
  </Svg>
);

/** Balança: cartão de lei. */
export const IconeLei: React.FC<P> = (p) => (
  <Svg {...p}>
    <path d="M32 8 V56 M20 56 H44 M12 16 H52" />
    <path d="M12 16 L4 34 H20 Z M52 16 L44 34 H60 Z" />
  </Svg>
);

/** Pessoa com crachá: fiscal. */
export const IconeFiscal: React.FC<P> = (p) => (
  <Svg {...p}>
    <circle cx="32" cy="16" r="9" />
    <path d="M12 58 C12 38 52 38 52 58" />
    <rect x="35" y="44" width="11" height="8" rx="1.5" />
  </Svg>
);
