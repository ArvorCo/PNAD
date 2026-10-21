import type { CSSProperties, PropsWithChildren } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { useFormato } from "../formato";
import { COR, MONO } from "../tema";
import { mola, rampa } from "./util";

/** Altura da barra do navegador em px de referência (escalada pelo formato). */
export const ALTURA_BARRA = 46;

/** URL digitada letra a letra a partir de `inicio`, com cursor piscando enquanto digita. */
export const UrlDigitada: React.FC<{ url: string; inicio: number; duracao?: number; cor?: string }> = ({
  url,
  inicio,
  duracao = 28,
  cor = COR.tealClaro,
}) => {
  const frame = useCurrentFrame();
  const n = Math.round(rampa(frame, inicio, inicio + duracao) * url.length);
  const digitando = frame >= inicio && frame < inicio + duracao + 24;
  return (
    <>
      {url.slice(0, n)}
      <span style={{ color: cor, opacity: digitando && frame % 20 < 10 ? 1 : 0 }}>▌</span>
    </>
  );
};

const Pontos: React.FC<{ lado: number }> = ({ lado }) => (
  <div style={{ display: "flex", gap: lado * 0.6, flex: "none" }}>
    {[COR.alta, COR.media, COR.outros].map((c) => (
      <div key={c} style={{ width: lado, height: lado, borderRadius: lado / 2, background: c }} />
    ))}
  </div>
);

const Cadeado: React.FC<{ lado: number; cor: string }> = ({ lado, cor }) => (
  <svg width={lado} height={lado} viewBox="0 0 24 24" fill="none" stroke={cor} strokeWidth={2.2} style={{ flex: "none" }}>
    <rect x="5" y="11" width="14" height="10" rx="2" />
    <path d="M8 11 V8 a4 4 0 0 1 8 0 V11" />
  </svg>
);

type BarraUrlProps = {
  url: string;
  /** Quadro em que a barra entra e a URL começa a ser digitada. */
  inicio: number;
  cor?: string;
  /** Corpo da URL em px de referência. */
  tamanho?: number;
  style?: CSSProperties;
};

/** Barra de endereço solta, estilo cartão de jogo, que entra com mola e digita a URL. */
export const BarraUrl: React.FC<BarraUrlProps> = ({ url, inicio, cor = COR.tealClaro, tamanho = 40, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { t } = useFormato();
  const p = mola(frame, fps, inicio, { damping: 14 });
  return (
    <div
      style={{
        opacity: frame < inicio ? 0 : p,
        transform: `scale(${0.92 + 0.08 * p})`,
        transformOrigin: "left center",
        background: "rgba(3,8,20,0.88)",
        border: `2px solid ${cor}`,
        borderRadius: t(16),
        padding: `${t(14)}px ${t(22)}px`,
        display: "flex",
        alignItems: "center",
        gap: t(16),
        boxShadow: `0 0 40px ${cor}44`,
        ...style,
      }}
    >
      <Pontos lado={t(12)} />
      <Cadeado lado={t(tamanho * 0.6)} cor={COR.suave} />
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(tamanho), color: COR.tinta, letterSpacing: 0.5, whiteSpace: "nowrap", overflow: "hidden" }}>
        <UrlDigitada url={url} inicio={inicio + 4} cor={cor} />
      </div>
    </div>
  );
};

type NavegadorProps = PropsWithChildren<{
  url: string;
  /** Largura da área de conteúdo, em px do formato atual. */
  largura: number;
  /** Proporção largura/altura do conteúdo (16/9 para a captura de mesa). */
  proporcao: number;
  /** Se definido, a URL é digitada a partir deste quadro; senão aparece pronta. */
  inicioUrl?: number;
  cor?: string;
  style?: CSSProperties;
}>;

/** Moldura de navegador: barra com três pontos e a URL, e a área de conteúdo com a proporção dada. */
export const Navegador: React.FC<NavegadorProps> = ({ url, largura, proporcao, inicioUrl, cor = COR.teal, style, children }) => {
  const { t } = useFormato();
  const barra = t(ALTURA_BARRA);
  return (
    <div
      style={{
        width: largura,
        flex: "none",
        borderRadius: t(16),
        overflow: "hidden",
        border: `1px solid ${COR.linha}`,
        boxShadow: `0 30px 80px rgba(0,0,0,0.5), 0 0 0 2px ${cor}40`,
        background: "#0a1226",
        ...style,
      }}
    >
      <div
        style={{
          height: barra,
          display: "flex",
          alignItems: "center",
          gap: t(14),
          padding: `0 ${t(16)}px`,
          background: "linear-gradient(180deg, #16244a, #0e1a38)",
          borderBottom: `1px solid ${COR.linha}`,
        }}
      >
        <Pontos lado={t(12)} />
        <div
          style={{
            flex: 1,
            minWidth: 0,
            height: barra * 0.64,
            borderRadius: barra,
            background: "rgba(3,8,20,0.72)",
            display: "flex",
            alignItems: "center",
            gap: t(10),
            padding: `0 ${t(14)}px`,
            fontFamily: MONO,
            fontSize: t(18),
            color: COR.tinta,
            whiteSpace: "nowrap",
            overflow: "hidden",
          }}
        >
          <Cadeado lado={t(16)} cor={COR.suave} />
          {inicioUrl === undefined ? url : <UrlDigitada url={url} inicio={inicioUrl} cor={cor} />}
        </div>
      </div>
      <div style={{ position: "relative", width: largura, height: largura / proporcao, overflow: "hidden", background: COR.papel }}>{children}</div>
    </div>
  );
};
