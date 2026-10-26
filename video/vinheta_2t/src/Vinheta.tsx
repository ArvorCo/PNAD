import { useEffect, useState } from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  continueRender,
  delayRender,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export const FPS = 30;
// Narração de 60,72 s (ffprobe) mais 1 s de respiro no fim.
export const DURACAO = Math.round((60.72 + 1) * FPS);

const COR = {
  fundo: "#142d2b",
  papel: "#f4f0e6",
  tinta: "#192e2b",
  verde: "#0c7a72",
  azul: "#1d4ed8",
  vermelho: "#d13c2e",
};
const SERIFA = "Fraunces, Georgia, serif";
const SANS = "Archivo, Helvetica, Arial, sans-serif";

const s = (seg: number) => Math.round(seg * FPS);

// Cortes casados com as pausas da narração (silencedetect a −35 dB).
const CENAS = {
  marca: [0, 6.6],
  leonardo: [6.6, 14.0],
  telas: [14.0, 34.6],
  qr: [34.6, 50.0],
  like: [50.0, 57.4],
  fim: [57.4, 61.72],
} as const;

const TELAS = [
  { img: "regioes.png", rotulo: "Placar por região", ini: 14.0 },
  { img: "ufs.png", rotulo: "Placar por estado", ini: 18.4 },
  { img: "evolucao.png", rotulo: "Quem está lento, quem fecha primeiro", ini: 21.2 },
  { img: "abstencao.png", rotulo: "Abstenção contra o 1º turno", ini: 24.0 },
  { img: "pausas.png", rotulo: "Pausas na divulgação", ini: 26.2 },
  { img: "governos.png", rotulo: "Seis governos em disputa", ini: 28.0 },
  { img: "projecao.png", rotulo: "Projeção a partir do que já foi contado", ini: 30.3 },
];

const useFontes = () => {
  const [handle] = useState(() => delayRender("fontes"));
  useEffect(() => {
    const fontes = [
      new FontFace("Fraunces", `url(${staticFile("fonts/fraunces-latin-opsz-normal.woff2")}) format("woff2")`, {
        weight: "100 900",
      }),
      new FontFace("Archivo", `url(${staticFile("fonts/archivo-latin-wght-normal.woff2")}) format("woff2")`, {
        weight: "100 900",
      }),
    ];
    Promise.all(fontes.map((f) => f.load()))
      .then((carregadas) => {
        carregadas.forEach((f) => document.fonts.add(f));
        continueRender(handle);
      })
      .catch(() => continueRender(handle));
  }, [handle]);
};

const entra = (frame: number, fps: number, atraso = 0) =>
  spring({ frame: frame - atraso, fps, config: { damping: 200 }, durationInFrames: 24 });

const Fade: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const frame = useCurrentFrame();
  const op = interpolate(frame, [0, 10, dur - 10, dur], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return <AbsoluteFill style={{ opacity: op }}>{children}</AbsoluteFill>;
};

const Pilula: React.FC<{ texto: string }> = ({ texto }) => {
  const frame = useCurrentFrame();
  const pulso = 0.55 + 0.45 * Math.abs(Math.sin(frame / 12));
  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 18,
        background: COR.vermelho,
        color: "#fff",
        fontFamily: SANS,
        fontWeight: 800,
        fontSize: 48,
        letterSpacing: 4,
        textTransform: "uppercase",
        padding: "14px 36px",
        borderRadius: 999,
      }}
    >
      <span style={{ width: 22, height: 22, borderRadius: 999, background: "#fff", opacity: pulso, display: "block" }} />
      {texto}
    </div>
  );
};

const Logo: React.FC<{ tam: number }> = ({ tam }) => (
  <div
    style={{
      width: tam,
      height: tam,
      borderRadius: 999,
      background: COR.papel,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
    }}
  >
    <Img src={staticFile("img/arvor.png")} style={{ width: tam * 0.86, height: tam * 0.86 }} />
  </div>
);

const Marca: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, 10);
  const c = entra(frame, fps, 22);
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 40%, #1d413e 0%, ${COR.fundo} 65%)`,
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: 40,
      }}
    >
      <div style={{ transform: `scale(${0.7 + 0.3 * a})`, opacity: a }}>
        <Logo tam={260} />
      </div>
      <div
        style={{
          fontFamily: SANS,
          fontWeight: 600,
          fontSize: 48,
          letterSpacing: 10,
          textTransform: "uppercase",
          color: "#9fd3cc",
          opacity: b,
        }}
      >
        Arvor Intelligence
      </div>
      <div
        style={{
          fontFamily: SERIFA,
          fontWeight: 700,
          fontSize: 132,
          lineHeight: 1,
          color: COR.papel,
          opacity: b,
          transform: `translateY(${(1 - b) * 40}px)`,
        }}
      >
        Apuração do 2º turno
      </div>
      <div style={{ opacity: c, transform: `translateY(${(1 - c) * 30}px)` }}>
        <Pilula texto="Ao vivo" />
      </div>
    </AbsoluteFill>
  );
};

const Leonardo: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const zoom = interpolate(frame, [0, dur], [1.04, 1.16]);
  const x = interpolate(frame, [0, dur], [0, -60]);
  const t = entra(frame, fps, 12);
  return (
    <AbsoluteFill style={{ background: COR.fundo, overflow: "hidden" }}>
      <Img
        src={staticFile("img/leonardo.png")}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: `scale(${zoom}) translateX(${x}px)`,
          transformOrigin: "68% 35%",
        }}
      />
      <AbsoluteFill
        style={{ background: "linear-gradient(90deg, rgba(10,24,22,0.92) 0%, rgba(10,24,22,0.55) 38%, rgba(10,24,22,0) 60%)" }}
      />
      <div
        style={{
          position: "absolute",
          left: 110,
          bottom: 130,
          opacity: t,
          transform: `translateX(${(1 - t) * -60}px)`,
        }}
      >
        <div style={{ width: 120, height: 8, background: COR.vermelho, marginBottom: 30 }} />
        <div style={{ fontFamily: SERIFA, fontWeight: 700, fontSize: 104, color: "#fff", lineHeight: 1 }}>
          Leonardo Dias
        </div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 52, color: "#bfe3dd", marginTop: 18 }}>
          Arvor Intelligence
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Tela: React.FC<{ img: string; rotulo: string; dur: number; i: number }> = ({ img, rotulo, dur, i }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = entra(frame, fps);
  const zoom = interpolate(frame, [0, dur], [1.0, 1.06]);
  const dir = i % 2 === 0 ? 1 : -1;
  const r = entra(frame, fps, 6);
  return (
    <AbsoluteFill style={{ background: COR.fundo }}>
      <AbsoluteFill
        style={{
          padding: "60px 90px 170px",
          transform: `translateX(${(1 - e) * 140 * dir}px)`,
          opacity: e,
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            borderRadius: 24,
            overflow: "hidden",
            boxShadow: "0 30px 80px rgba(0,0,0,0.5)",
            border: `3px solid ${COR.papel}`,
          }}
        >
          <Img
            src={staticFile(`img/${img}`)}
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              transform: `scale(${zoom})`,
              transformOrigin: "50% 40%",
              filter: "blur(18px)",
            }}
          />
          <div
            style={{
              position: "absolute",
              top: 90,
              right: 120,
              background: COR.tinta,
              color: COR.papel,
              fontFamily: SANS,
              fontWeight: 700,
              fontSize: 48,
              padding: "12px 30px",
              borderRadius: 999,
            }}
          >
            Tela de teste, dados simulados
          </div>
        </div>
      </AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 90,
          bottom: 48,
          display: "flex",
          alignItems: "center",
          gap: 26,
          opacity: r,
          transform: `translateY(${(1 - r) * 30}px)`,
        }}
      >
        <div style={{ width: 16, height: 76, background: COR.vermelho, borderRadius: 4 }} />
        <div style={{ fontFamily: SERIFA, fontWeight: 700, fontSize: 72, color: COR.papel, lineHeight: 1 }}>{rotulo}</div>
      </div>
    </AbsoluteFill>
  );
};

const Telas: React.FC = () => {
  const fim = CENAS.telas[1];
  return (
    <AbsoluteFill style={{ background: COR.fundo }}>
      {TELAS.map((t, i) => {
        const prox = i + 1 < TELAS.length ? TELAS[i + 1].ini : fim;
        const de = s(t.ini - CENAS.telas[0]);
        const dur = s(prox) - s(t.ini);
        return (
          <Sequence key={t.img} from={de} durationInFrames={dur}>
            <Tela img={t.img} rotulo={t.rotulo} dur={dur} i={i} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const Qr: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, 14);
  const c = entra(frame, fps, 28);
  const pulso = 1 + 0.015 * Math.sin(frame / 10);
  return (
    <AbsoluteFill style={{ background: COR.papel, flexDirection: "row", alignItems: "center", padding: "0 120px", gap: 110 }}>
      <div
        style={{
          background: "#fff",
          padding: 36,
          borderRadius: 32,
          boxShadow: "0 30px 80px rgba(25,46,43,0.25)",
          border: `6px solid ${COR.tinta}`,
          transform: `scale(${(0.8 + 0.2 * a) * pulso})`,
          opacity: a,
        }}
      >
        <Img src={staticFile("img/qr.svg")} style={{ width: 640, height: 640, display: "block" }} />
      </div>
      <div style={{ flex: 1 }}>
        <div
          style={{
            fontFamily: SANS,
            fontWeight: 700,
            fontSize: 48,
            letterSpacing: 6,
            textTransform: "uppercase",
            color: COR.verde,
            opacity: b,
          }}
        >
          Totalização paralela
        </div>
        <div
          style={{
            fontFamily: SERIFA,
            fontWeight: 800,
            fontSize: 112,
            lineHeight: 1.02,
            color: COR.tinta,
            marginTop: 24,
            opacity: b,
            transform: `translateY(${(1 - b) * 30}px)`,
          }}
        >
          TEM UM BU?
          <br />
          <span style={{ color: COR.vermelho }}>LEIA-O AGORA</span>
        </div>
        <div
          style={{
            marginTop: 46,
            display: "inline-block",
            background: COR.tinta,
            color: COR.papel,
            fontFamily: SANS,
            fontWeight: 700,
            fontSize: 60,
            padding: "18px 34px",
            borderRadius: 16,
            opacity: c,
          }}
        >
          brasil.arvor.co/totalizacao
        </div>
        <div style={{ fontFamily: SANS, fontWeight: 500, fontSize: 48, color: COR.tinta, marginTop: 34, opacity: c }}>
          Cada boletim é conferido contra o oficial, seção por seção.
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Like: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, 18);
  return (
    <AbsoluteFill style={{ background: COR.azul, alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 30 }}>
      <div
        style={{
          fontFamily: SERIFA,
          fontWeight: 800,
          fontSize: 150,
          color: "#fff",
          opacity: a,
          transform: `scale(${0.85 + 0.15 * a})`,
        }}
      >
        Deixe o like.
      </div>
      <div
        style={{
          fontFamily: SERIFA,
          fontWeight: 800,
          fontSize: 150,
          color: COR.papel,
          opacity: b,
          transform: `translateY(${(1 - b) * 40}px)`,
        }}
      >
        Compartilhe.
      </div>
      <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 52, color: "#dbe5ff", marginTop: 20, opacity: b }}>
        Fique com a gente até o fim.
      </div>
    </AbsoluteFill>
  );
};

const Fim: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, 12);
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 40%, #1d413e 0%, ${COR.fundo} 65%)`,
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: 36,
      }}
    >
      <div style={{ opacity: a, transform: `scale(${0.8 + 0.2 * a})` }}>
        <Logo tam={220} />
      </div>
      <div style={{ fontFamily: SERIFA, fontWeight: 700, fontSize: 110, color: COR.papel, opacity: a }}>
        A divulgação começa agora
      </div>
      <div
        style={{
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: 64,
          color: "#9fd3cc",
          letterSpacing: 2,
          opacity: b,
        }}
      >
        brasil.arvor.co
      </div>
      <div style={{ opacity: b }}>
        <Pilula texto="Ao vivo" />
      </div>
    </AbsoluteFill>
  );
};

const Cena: React.FC<{ faixa: readonly [number, number]; children: (dur: number) => React.ReactNode }> = ({
  faixa,
  children,
}) => {
  const de = s(faixa[0]);
  const dur = s(faixa[1]) - de;
  return (
    <Sequence from={de} durationInFrames={dur}>
      <Fade dur={dur}>{children(dur)}</Fade>
    </Sequence>
  );
};

export const Vinheta: React.FC = () => {
  useFontes();
  return (
    <AbsoluteFill style={{ background: COR.fundo }}>
      <Cena faixa={CENAS.marca}>{() => <Marca />}</Cena>
      <Cena faixa={CENAS.leonardo}>{(dur) => <Leonardo dur={dur} />}</Cena>
      <Cena faixa={CENAS.telas}>{() => <Telas />}</Cena>
      <Cena faixa={CENAS.qr}>{() => <Qr />}</Cena>
      <Cena faixa={CENAS.like}>{() => <Like />}</Cena>
      <Cena faixa={CENAS.fim}>{() => <Fim />}</Cena>
      <Audio src={staticFile("abertura.mp3")} />
    </AbsoluteFill>
  );
};
