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
import { D } from "./dados";

export const FPS_E = 30;
// Narração de 237,64 s (ffprobe) mais 2 s de respiro no fim.
export const DURACAO_E = Math.round((237.64 + 2) * FPS_E);

const COR = {
  fundo: "#142d2b",
  papel: "#f4f0e6",
  tinta: "#192e2b",
  verde: "#0c7a72",
  claro: "#9fd3cc",
  azul: "#1d4ed8",
  vermelho: "#d13c2e",
};
const SERIFA = "Fraunces, Georgia, serif";
const SANS = "Archivo, Helvetica, Arial, sans-serif";
const s = (seg: number) => Math.round(seg * FPS_E);
const n = (v: number) => v.toLocaleString("pt-BR");
const pc = (v: number, c = 1) => v.toLocaleString("pt-BR", { minimumFractionDigits: c, maximumFractionDigits: c });

// Cortes nas emendas dos parágrafos da narração (duração de cada parte por ffprobe).
const CENAS: [string, number, number][] = [
  ["marca", 0, 6.72],
  ["placar", 6.72, 51.12],
  ["projecao", 51.12, 76.8],
  ["linha", 76.8, 92.48],
  ["abstencao", 92.48, 120.16],
  ["paralela", 120.16, 135.92],
  ["comparecimento", 135.92, 170.08],
  ["governos", 170.08, 204.87],
  ["telas", 204.87, 215.92],
  ["convite", 215.92, 228.96],
  ["fim", 228.96, 239.64],
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

const Kicker: React.FC<{ texto: string; cor?: string }> = ({ texto, cor = COR.claro }) => (
  <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 48, letterSpacing: 6, textTransform: "uppercase", color: cor }}>
    {texto}
  </div>
);

const Marca: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, 10);
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
        <Logo tam={240} />
      </div>
      <div style={{ opacity: b }}>
        <Kicker texto="Arvor Intelligence" />
      </div>
      <div style={{ fontFamily: SERIFA, fontWeight: 700, fontSize: 120, lineHeight: 1, color: COR.papel, opacity: b }}>
        Apuração do 2º turno
      </div>
      <div
        style={{
          fontFamily: SANS,
          fontWeight: 800,
          fontSize: 56,
          letterSpacing: 4,
          textTransform: "uppercase",
          color: "#fff",
          background: COR.vermelho,
          padding: "12px 36px",
          borderRadius: 999,
          opacity: b,
        }}
      >
        Boletim final
      </div>
    </AbsoluteFill>
  );
};

const Bloco: React.FC<{ nome: string; votos: number; p: number; cor: string; t: number }> = ({ nome, votos, p, cor, t }) => (
  <div style={{ flex: 1, background: cor, borderRadius: 28, padding: "40px 50px", opacity: t, transform: `translateY(${(1 - t) * 40}px)` }}>
    <div style={{ fontFamily: SANS, fontWeight: 800, fontSize: 64, color: "#fff", letterSpacing: 2 }}>{nome}</div>
    <div style={{ fontFamily: SERIFA, fontWeight: 800, fontSize: 168, color: "#fff", lineHeight: 1.05 }}>{pc(p)}%</div>
    <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 60, color: "#fff" }}>{n(votos)} votos</div>
  </div>
);

const Placar: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, 8);
  const conta = s(28.08 - 6.72);
  const c = entra(frame, fps, conta);
  const d = entra(frame, fps, conta + 30);
  return (
    <AbsoluteFill style={{ background: COR.fundo, padding: "70px 100px", gap: 40 }}>
      <Kicker texto={`Presidente · ${pc(D.pst, 2)}% das seções totalizadas`} />
      <div style={{ display: "flex", gap: 50 }}>
        <Bloco nome="LULA (PT)" votos={D.lula.votos} p={D.lula.pvapn} cor={COR.vermelho} t={a} />
        <Bloco nome="FLÁVIO (PL)" votos={D.flavio.votos} p={D.flavio.pvapn} cor={COR.azul} t={b} />
      </div>
      <div style={{ display: "flex", gap: 50, alignItems: "stretch", opacity: c, transform: `translateY(${(1 - c) * 30}px)` }}>
        <div style={{ flex: 1, background: COR.papel, borderRadius: 24, padding: "28px 44px" }}>
          <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 48, color: COR.verde }}>Diferença</div>
          <div style={{ fontFamily: SERIFA, fontWeight: 800, fontSize: 112, color: COR.tinta, lineHeight: 1.05 }}>{n(D.diferenca)}</div>
        </div>
        <div style={{ flex: 1, background: COR.papel, borderRadius: 24, padding: "28px 44px" }}>
          <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 48, color: COR.verde }}>Falta apurar (base do 1º turno)</div>
          <div style={{ fontFamily: SERIFA, fontWeight: 800, fontSize: 112, color: COR.tinta, lineHeight: 1.05 }}>&lt; 230 mil</div>
        </div>
      </div>
      <div
        style={{
          alignSelf: "center",
          fontFamily: SANS,
          fontWeight: 800,
          fontSize: 72,
          letterSpacing: 3,
          textTransform: "uppercase",
          color: "#fff",
          background: COR.verde,
          padding: "14px 48px",
          borderRadius: 999,
          opacity: d,
        }}
      >
        Sem virada possível
      </div>
    </AbsoluteFill>
  );
};

const Captura: React.FC<{ img: string; titulo: string; legenda?: string; dur: number }> = ({ img, titulo, legenda, dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = entra(frame, fps);
  const r = entra(frame, fps, 8);
  const zoom = interpolate(frame, [0, dur], [1.0, 1.05]);
  return (
    <AbsoluteFill style={{ background: COR.fundo }}>
      <div style={{ position: "absolute", left: 90, top: 46, right: 90, opacity: r }}>
        <div style={{ fontFamily: SERIFA, fontWeight: 700, fontSize: 72, color: COR.papel, lineHeight: 1.05 }}>{titulo}</div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 150,
          right: 150,
          top: 160,
          bottom: legenda ? 150 : 50,
          borderRadius: 22,
          overflow: "hidden",
          border: `3px solid ${COR.papel}`,
          boxShadow: "0 30px 80px rgba(0,0,0,0.5)",
          opacity: e,
          transform: `translateY(${(1 - e) * 40}px)`,
        }}
      >
        <Img
          src={staticFile(`final/${img}`)}
          style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "50% 0%", transform: `scale(${zoom})`, transformOrigin: "50% 30%" }}
        />
      </div>
      {legenda ? (
        <div
          style={{
            position: "absolute",
            left: 90,
            right: 90,
            bottom: 40,
            fontFamily: SANS,
            fontWeight: 700,
            fontSize: 52,
            color: COR.claro,
            opacity: r,
            textAlign: "center",
          }}
        >
          {legenda}
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

const Linha: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  // Posições fixas (não proporcionais ao relógio) para os rótulos de 17:00 e 17:07 não se sobreporem.
  const marcos = [
    { h: "17:00", t: "Início da live", x: 180, cor: COR.claro, cima: false, ancora: "start", dx: -22 },
    { h: "17:07", t: "TSE para a divulgação", x: 440, cor: COR.vermelho, cima: true, ancora: "middle", dx: 0 },
    { h: "19:01", t: "Divulgação retomada", x: 1180, cor: COR.claro, cima: false, ancora: "middle", dx: 0 },
    { h: "21:21", t: "99,8% apurado", x: 1660, cor: COR.claro, cima: true, ancora: "end", dx: 22 },
  ];
  const x0 = 180;
  const x1 = 1660;
  const prog = interpolate(frame, [0, s(8)], [0, 1], { extrapolateRight: "clamp" });
  const ponta = x0 + (x1 - x0) * prog;
  const t = entra(frame, fps);
  return (
    <AbsoluteFill style={{ background: COR.fundo, padding: "70px 90px" }}>
      <Kicker texto="A noite" />
      <div style={{ fontFamily: SERIFA, fontWeight: 700, fontSize: 88, color: COR.papel, marginTop: 16, opacity: t }}>
        Prorrogação inédita de duas horas
      </div>
      <svg width={1740} height={640} style={{ marginTop: 20 }}>
        <line x1={x0} x2={ponta} y1={330} y2={330} stroke={COR.papel} strokeWidth={10} strokeLinecap="round" />
        <rect x={440} y={290} width={Math.max(0, Math.min(1180, ponta) - 440)} height={80} fill={COR.vermelho} rx={10} />
        {prog > 0.65 ? (
          <text x={810} y={347} textAnchor="middle" fill="#fff" fontFamily={SANS} fontWeight={800} fontSize={48}>
            {pc(D.pausa.minutos)} min sem divulgação
          </text>
        ) : null}
        {marcos.map((m, i) => {
          const vis = interpolate(frame, [s(i * 1.8), s(i * 1.8) + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const yh = m.cima ? 200 : 450;
          const yt = m.cima ? 262 : 515;
          return (
            <g key={m.h} opacity={vis}>
              <circle cx={m.x} cy={330} r={22} fill={m.cor} stroke={COR.fundo} strokeWidth={6} />
              <text x={m.x} y={yh} textAnchor={m.ancora} dx={m.dx} fill={COR.papel} fontFamily={SERIFA} fontWeight={800} fontSize={76}>
                {m.h}
              </text>
              <text x={m.x} y={yt} textAnchor={m.ancora} dx={m.dx} fill={COR.claro} fontFamily={SANS} fontWeight={700} fontSize={48}>
                {m.t}
              </text>
            </g>
          );
        })}
      </svg>
    </AbsoluteFill>
  );
};

const Abstencao: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = entra(frame, fps);
  const max = 22;
  return (
    <AbsoluteFill style={{ background: COR.papel, padding: "60px 100px" }}>
      <Kicker texto="Abstenção nos municípios fechados" cor={COR.verde} />
      <div style={{ fontFamily: SERIFA, fontWeight: 800, fontSize: 92, color: COR.tinta, marginTop: 10, opacity: t }}>
        {pc(D.abst_br)}% no 2º turno, contra {pc(D.abst_br_1t)}% no 1º
      </div>
      <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 22 }}>
        {D.abst.map((u, i) => {
          const g = entra(frame, fps, s(5) + i * s(2.6));
          return (
            <div key={u.uf} style={{ display: "flex", alignItems: "center", gap: 30, opacity: g }}>
              <div style={{ width: 560, fontFamily: SANS, fontWeight: 700, fontSize: 52, color: COR.tinta }}>{u.nome}</div>
              <div style={{ flex: 1, height: 70, position: "relative" }}>
                <div style={{ position: "absolute", left: 0, top: 0, height: 70, width: `${(u.pa / max) * 100 * g}%`, background: COR.verde, borderRadius: 8, display: "block" }} />
              </div>
              <div style={{ width: 200, textAlign: "right", fontFamily: SERIFA, fontWeight: 800, fontSize: 64, color: COR.tinta }}>{pc(u.pa)}%</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const Paralela: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, s(2));
  const c = entra(frame, fps, s(8));
  const r = D.paralela.recebidos;
  const k = D.paralela.conferencia;
  return (
    <AbsoluteFill style={{ background: COR.papel, flexDirection: "row", alignItems: "center", padding: "0 110px", gap: 100 }}>
      <div style={{ background: "#fff", padding: 30, borderRadius: 30, border: `6px solid ${COR.tinta}`, opacity: a, transform: `scale(${0.85 + 0.15 * a})` }}>
        <Img src={staticFile("img/qr.svg")} style={{ width: 560, height: 560, display: "block" }} />
      </div>
      <div style={{ flex: 1 }}>
        <Kicker texto="Totalização paralela" cor={COR.verde} />
        <div style={{ fontFamily: SERIFA, fontWeight: 800, fontSize: 104, color: COR.tinta, lineHeight: 1.05, marginTop: 20, opacity: b }}>
          {n(r.bus)} boletins
          <br />
          em {r.ufs} estados
        </div>
        <div style={{ display: "flex", gap: 30, marginTop: 40, opacity: c }}>
          <div style={{ background: COR.verde, color: "#fff", borderRadius: 20, padding: "20px 34px", fontFamily: SANS, fontWeight: 800, fontSize: 60 }}>
            {n(k.iguais)} iguais
          </div>
          <div style={{ background: COR.tinta, color: "#fff", borderRadius: 20, padding: "20px 34px", fontFamily: SANS, fontWeight: 800, fontSize: 60 }}>
            {k.divergentes} divergências
          </div>
        </div>
        <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 48, color: COR.tinta, marginTop: 30, opacity: c }}>
          Conferidos voto a voto contra o arquivo oficial.
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Comparecimento: React.FC<{ dur: number }> = ({ dur }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const g = D.comp.sinais;
  const itens = [
    `${n(g.delta)} com comparecimento 5 pontos acima`,
    `${n(g.sem_bio)} com habilitação sem biometria alta`,
    `${n(g.contingencia)} urnas de contingência`,
    `${n(g.tardia)} tardias, ${n(g.apos_19h)} encerradas após 19h`,
    `${n(g.papel)} votação em cédula`,
  ];
  const zoom = interpolate(frame, [0, dur], [1.0, 1.04]);
  return (
    <AbsoluteFill style={{ background: COR.fundo, flexDirection: "row" }}>
      <div style={{ width: 1000, height: "100%", overflow: "hidden", position: "relative" }}>
        <Img src={staticFile("final/comparecimento.png")} style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "0% 0%", transform: `scale(${zoom})`, transformOrigin: "0% 0%" }} />
        <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(20,45,43,0) 70%, rgba(20,45,43,1) 100%)" }} />
      </div>
      <div style={{ flex: 1, padding: "70px 70px 60px 30px", display: "flex", flexDirection: "column", gap: 22 }}>
        <Kicker texto={`${n(D.comp.totais.recebidas)} seções conferidas`} />
        {itens.map((t, i) => {
          const v = entra(frame, fps, s(3) + i * s(3.2));
          return (
            <div key={t} style={{ fontFamily: SANS, fontWeight: 700, fontSize: 48, color: COR.papel, opacity: v, lineHeight: 1.15 }}>
              {t}
            </div>
          );
        })}
        <div style={{ marginTop: "auto", background: COR.papel, color: COR.tinta, borderRadius: 18, padding: "22px 28px", fontFamily: SERIFA, fontWeight: 800, fontSize: 52, opacity: entra(frame, fps, s(22)) }}>
          Sinal pede explicação, não prova irregularidade.
        </div>
      </div>
    </AbsoluteFill>
  );
};

const TELAS = ["pres.png", "regioes.png", "ufs.png", "pausas.png", "paralela.png"];
const Telas: React.FC<{ dur: number }> = ({ dur }) => {
  const cada = Math.floor(dur / TELAS.length);
  return (
    <AbsoluteFill style={{ background: COR.fundo }}>
      {TELAS.map((img, i) => (
        <Sequence key={img} from={i * cada} durationInFrames={i === TELAS.length - 1 ? dur - i * cada : cada}>
          <Captura img={img} titulo="Seguimos apurando até a última seção, no exterior" dur={cada} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

const Convite: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, s(3));
  const c = entra(frame, fps, s(8));
  return (
    <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 35%, #1d413e 0%, ${COR.fundo} 65%)`, alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 34 }}>
      <div style={{ opacity: a, transform: `scale(${0.8 + 0.2 * a})` }}>
        <Logo tam={220} />
      </div>
      <div style={{ fontFamily: SERIFA, fontWeight: 800, fontSize: 112, color: COR.papel, opacity: a }}>Arvor Intelligence</div>
      <div style={{ fontFamily: SANS, fontWeight: 600, fontSize: 56, color: COR.claro, opacity: b }}>Produtos de inteligência artificial e dados</div>
      <div style={{ display: "flex", gap: 40, marginTop: 20, opacity: c }}>
        {["arvor.co", "brasil.arvor.co"].map((u) => (
          <div key={u} style={{ background: COR.papel, color: COR.tinta, fontFamily: SANS, fontWeight: 800, fontSize: 72, padding: "18px 44px", borderRadius: 18 }}>
            {u}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const Fim: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const a = entra(frame, fps);
  const b = entra(frame, fps, s(4));
  return (
    <AbsoluteFill style={{ background: COR.papel, alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 40 }}>
      <div style={{ fontFamily: SERIFA, fontWeight: 800, fontSize: 132, color: COR.tinta, textAlign: "center", lineHeight: 1.05, opacity: a }}>
        A conta na tela,
        <br />
        <span style={{ color: COR.vermelho }}>seção por seção.</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 30, opacity: b }}>
        <Logo tam={120} />
        <div style={{ fontFamily: SANS, fontWeight: 700, fontSize: 60, color: COR.tinta }}>Boa noite. brasil.arvor.co</div>
      </div>
    </AbsoluteFill>
  );
};

const cena = (id: string, dur: number) => {
  switch (id) {
    case "marca":
      return <Marca />;
    case "placar":
      return <Placar />;
    case "projecao":
      return (
        <Captura
          img="projecao.png"
          titulo="A projeção apontou Lula desde o início"
          legenda={`19h14, com ${pc(D.proj_primeiro[5])}% das seções: Flávio ${pc(D.proj_primeiro[1])}%. No fim: projetado ${pc(D.proj_final)}%, observado ${pc(D.obs_final)}%.`}
          dur={dur}
        />
      );
    case "linha":
      return <Linha />;
    case "abstencao":
      return <Abstencao />;
    case "paralela":
      return <Paralela />;
    case "comparecimento":
      return <Comparecimento dur={dur} />;
    case "governos":
      return <Captura img="gov-2t.png" titulo="Seis governos no 2º turno" dur={dur} />;
    case "telas":
      return <Telas dur={dur} />;
    case "convite":
      return <Convite />;
    default:
      return <Fim />;
  }
};

export const Encerramento: React.FC = () => {
  useFontes();
  return (
    <AbsoluteFill style={{ background: COR.fundo }}>
      <Audio src={staticFile("encerramento.mp3")} />
      {CENAS.map(([id, ini, fim]) => {
        const dur = s(fim) - s(ini);
        return (
          <Sequence key={id} from={s(ini)} durationInFrames={dur}>
            <Fade dur={dur}>{cena(id, dur)}</Fade>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
