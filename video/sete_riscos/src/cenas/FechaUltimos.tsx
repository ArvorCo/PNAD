import type { ReactNode } from "react";
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { ClipeSeHouver } from "../componentes/ClipeSeHouver";
import { IconeAfixada, IconeBoletim, IconePessoas, IconeUrna } from "../componentes/Icones";
import { Area, Fase, Surge } from "../componentes/Quadro";
import { mola } from "../componentes/util";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { Dados, IdFechamento, IdLeiFiscal, ItemLei } from "../tipos";
import type { CenaProps } from "./registro";

type IconeP = { tamanho: number; cor?: string };

/** Senha de fila: bilhete com o número picotado. */
const IconeSenha: React.FC<IconeP> = ({ tamanho, cor = COR.tealClaro }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 64 64" fill="none" stroke={cor} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" style={{ flex: "none" }}>
    <path d="M8 18 H56 V28 A4 4 0 0 0 56 36 V46 H8 V36 A4 4 0 0 0 8 28 Z" />
    <path d="M40 18 V46" strokeDasharray="3 4" />
    <path d="M16 28 H32 M16 36 H28" />
  </svg>
);

/** Relógio pequeno para o passo "chegue perto das 17h". */
const IconeRelogio: React.FC<IconeP> = ({ tamanho, cor = COR.tealClaro }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 64 64" fill="none" stroke={cor} strokeWidth={3} strokeLinecap="round" style={{ flex: "none" }}>
    <circle cx="32" cy="32" r="24" />
    <path d="M32 32 V16 M32 32 L42 38" />
  </svg>
);

/** Código QR estilizado para o passo "fotografe o QR". */
const IconeQr: React.FC<IconeP> = ({ tamanho, cor = COR.tealClaro }) => (
  <svg width={tamanho} height={tamanho} viewBox="0 0 64 64" fill="none" stroke={cor} strokeWidth={3} strokeLinejoin="round" style={{ flex: "none" }}>
    <rect x="8" y="8" width="18" height="18" rx="2" />
    <rect x="38" y="8" width="18" height="18" rx="2" />
    <rect x="8" y="38" width="18" height="18" rx="2" />
    <rect x="14" y="14" width="6" height="6" fill={cor} stroke="none" />
    <rect x="44" y="14" width="6" height="6" fill={cor} stroke="none" />
    <rect x="14" y="44" width="6" height="6" fill={cor} stroke="none" />
    <path d="M38 38 H46 V46 M56 38 V56 H46 M38 50 V56" />
  </svg>
);

/** Relógio grande: o ponteiro dos minutos varre os últimos minutos até as 17h e para. */
const Relogio: React.FC<{ lado: number; q: number }> = ({ lado, q }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entra = mola(frame, fps, q, { damping: 16 });
  // De 16h52 a 17h00 em 1 s, com acomodação.
  const minutos = 52 + 8 * mola(frame, fps, q + 6, { damping: 18, stiffness: 70 });
  const anguloMin = (minutos / 60) * 360;
  const anguloHora = ((16 + minutos / 60) / 12) * 360;
  const pulso = 0.5 + 0.5 * Math.sin(frame * 0.18);
  return (
    <svg width={lado} height={lado} viewBox="0 0 200 200" style={{ opacity: entra, transform: `scale(${0.85 + 0.15 * entra})`, flex: "none" }}>
      <circle cx="100" cy="100" r="92" fill="rgba(6,11,26,0.82)" stroke={COR.flavio} strokeWidth="5" />
      <circle cx="100" cy="100" r="92" fill="none" stroke={COR.flavio} strokeWidth="2" opacity={0.25 + 0.35 * pulso} style={{ transform: "scale(1.04)", transformOrigin: "100px 100px" }} />
      {Array.from({ length: 12 }, (_, i) => {
        const a = (i / 12) * Math.PI * 2;
        const longo = i % 3 === 0;
        return (
          <line
            key={i}
            x1={100 + Math.sin(a) * (longo ? 70 : 76)}
            y1={100 - Math.cos(a) * (longo ? 70 : 76)}
            x2={100 + Math.sin(a) * 84}
            y2={100 - Math.cos(a) * 84}
            stroke={COR.tinta}
            strokeWidth={longo ? 5 : 3}
            strokeLinecap="round"
          />
        );
      })}
      <line x1="100" y1="100" x2="100" y2="52" stroke={COR.tinta} strokeWidth="8" strokeLinecap="round" transform={`rotate(${anguloHora} 100 100)`} />
      <line x1="100" y1="100" x2="100" y2="28" stroke={COR.ouro} strokeWidth="5" strokeLinecap="round" transform={`rotate(${anguloMin} 100 100)`} />
      <circle cx="100" cy="100" r="7" fill={COR.ouro} />
    </svg>
  );
};

type Marco = { id: string; texto: string; referencia: string; icone: ReactNode; q: number };

const LinhaTempo: React.FC<{ marcos: Marco[]; cor: string }> = ({ marcos, cor }) => {
  const frame = useCurrentFrame();
  const { vertical, t } = useFormato();
  const atual = marcos.reduce((acc, m, i) => (frame >= m.q ? i : acc), -1);
  return (
    <div style={{ position: "relative", display: "flex", flexDirection: "column", gap: t(vertical ? 40 : 20) }}>
      {marcos.map((m, i) => {
        const aceso = i === atual;
        return (
          <Surge key={m.id} inicio={m.q} de="esquerda">
            <div style={{ display: "flex", gap: t(18), alignItems: "center" }}>
              <div
                style={{
                  width: t(vertical ? 104 : 72),
                  height: t(vertical ? 104 : 72),
                  borderRadius: "50%",
                  flex: "none",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: aceso ? `${cor}33` : "rgba(6,11,26,0.78)",
                  border: `3px solid ${aceso ? cor : COR.linha}`,
                  boxShadow: aceso ? `0 0 26px ${cor}66` : "none",
                }}
              >
                {m.icone}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: t(4), minWidth: 0 }}>
                <Texto tamanho={vertical ? 42 : 29} cor={aceso ? COR.tinta : COR.suave} style={{ fontWeight: 700, lineHeight: 1.18 }}>
                  {m.texto}
                </Texto>
                <span style={{ fontFamily: MONO, fontSize: t(vertical ? 32 : 22), color: aceso ? COR.ouro : COR.suave, letterSpacing: 0.5 }}>{m.referencia}</span>
              </div>
            </div>
          </Surge>
        );
      })}
    </div>
  );
};

type Passo = { n: number; titulo: string; icone: ReactNode; q: number };

const Passos: React.FC<{ passos: Passo[] }> = ({ passos }) => {
  const { vertical, t } = useFormato();
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: t(vertical ? 22 : 18) }}>
      {passos.map((p) => (
        <Surge key={p.n} inicio={p.q} de="baixo">
          <div
            style={{
              height: "100%",
              background: "rgba(12,26,58,0.88)",
              border: `1px solid ${COR.linha}`,
              borderTop: `5px solid ${COR.ouro}`,
              borderRadius: 16,
              padding: `${t(vertical ? 34 : 18)}px ${t(vertical ? 26 : 20)}px`,
              minHeight: vertical ? t(270) : undefined,
              display: "flex",
              flexDirection: "column",
              gap: t(12),
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 72 : 46), color: COR.ouro, lineHeight: 1 }}>{p.n}</span>
              {p.icone}
            </div>
            <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 48 : 32), lineHeight: 1.1, color: COR.tinta, textWrap: "balance" }}>{p.titulo}</div>
          </div>
        </Surge>
      ))}
    </div>
  );
};

const doFechamento = (dados: Dados, id: IdFechamento): ItemLei<IdFechamento> => {
  const item = dados.fechamento.find((f) => f.id === id);
  if (!item) {
    throw new Error(`fechamento sem o item ${id}`);
  }
  return item;
};

const daLei = (dados: Dados, id: IdLeiFiscal): ItemLei<IdLeiFiscal> => {
  const item = dados.lei_fiscal.find((f) => f.id === id);
  if (!item) {
    throw new Error(`lei_fiscal sem o item ${id}`);
  }
  return item;
};

/** "Res. TSE 23.751/2026, art. 160, § 2º" → "art. 160, § 2º" (a resolução fica no título). */
const artigo = (referencia: string): string => referencia.replace(/^Res\. TSE 23\.751\/2026,\s*/, "");

/**
 * A hora de fechar: o relógio das 17h, a linha do tempo do encerramento com o artigo de cada
 * passo, a dica prática em quatro passos, a ida do fiscal com a urna até a junta e a frase final.
 */
export const FechaUltimos: React.FC<CenaProps> = ({ g, dados, cena }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, t } = useFormato();
  const ic = t(vertical ? 58 : 40);
  const marcos: Marco[] = [
    { ...doFechamento(dados, "senhas"), icone: <IconeSenha tamanho={ic} />, q: g.senha },
    { ...doFechamento(dados, "ultimos_dois"), icone: <IconePessoas tamanho={ic} />, q: g.duas },
    { ...doFechamento(dados, "bu_afixado"), icone: <IconeAfixada tamanho={ic} />, q: g.copia },
    { ...doFechamento(dados, "copia_no_encerramento"), icone: <IconeBoletim tamanho={ic} />, q: g.pedir },
  ].map((m) => ({ id: m.id, texto: m.texto, referencia: artigo(m.referencia), icone: m.icone, q: m.q }));
  const junta = daLei(dados, "ate_a_junta");
  const ip = t(vertical ? 72 : 50);
  const passos: Passo[] = [
    { n: 1, titulo: "Chegue perto das 17h", icone: <IconeRelogio tamanho={ip} cor={COR.ouro} />, q: g.chegue },
    { n: 2, titulo: "Fique na fila por último", icone: <IconePessoas tamanho={ip} cor={COR.ouro} />, q: g.fique },
    { n: 3, titulo: "Peça o boletim", icone: <IconeBoletim tamanho={ip} cor={COR.ouro} />, q: g.peca },
    { n: 4, titulo: "Fotografe o QR", icone: <IconeQr tamanho={ip} cor={COR.ouro} />, q: g.fotografe },
  ];
  const fimA = g.dica - 6;
  const fimB = g.depois - 4;
  const mais = mola(frame, fps, g.mais, { damping: 11, stiffness: 160 });

  const relogio = (
    <div style={{ display: "flex", flexDirection: vertical ? "row" : "column", alignItems: "center", gap: t(vertical ? 34 : 22) }}>
      <Relogio lado={t(vertical ? 300 : 300)} q={0} />
      <div style={{ display: "flex", flexDirection: "column", alignItems: vertical ? "flex-start" : "center", gap: t(10) }}>
        <Entrada inicio={g.dezessete} de="zoom">
          <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 120 : 108), color: COR.tinta, lineHeight: 1, letterSpacing: -2 }}>17:00</div>
        </Entrada>
        <Entrada inicio={g.dezessete + 8} de="baixo">
          <Chip cor={COR.flavio} tamanho={vertical ? 28 : 22}>
            horário de Brasília
          </Chip>
        </Entrada>
      </div>
    </div>
  );

  const titulo = (texto: string, cor: string) => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: t(10) }}>
      <Chip cor={cor} solido tamanho={vertical ? 28 : 22}>
        {texto}
      </Chip>
    </div>
  );

  const faseA = (
    <Fase de={0} ate={fimA}>
      <div style={{ display: "flex", flexDirection: "column", gap: t(vertical ? 30 : 22) }}>
        <Entrada inicio={4} de="esquerda">
          {titulo("Res. TSE 23.751/2026", COR.ouro)}
        </Entrada>
        <LinhaTempo marcos={marcos} cor={COR.ouro} />
      </div>
    </Fase>
  );

  const faseB = (
    <Fase de={fimA} ate={fimB}>
      <div style={{ display: "flex", flexDirection: "column", gap: t(vertical ? 28 : 20) }}>
        <Entrada inicio={g.dica} de="esquerda">
          <Titulo tamanho={vertical ? 68 : 58}>
            Dica <span style={{ color: COR.ouro }}>prática</span>
          </Titulo>
        </Entrada>
        <Passos passos={passos} />
      </div>
    </Fase>
  );

  const faseC = (
    <Fase de={fimB}>
      <div style={{ display: "flex", flexDirection: "column", gap: t(vertical ? 64 : 30) }}>
        <Surge inicio={g.depois} de="esquerda">
          <div
            style={{
              display: "flex",
              gap: t(20),
              alignItems: "center",
              background: "rgba(12,26,58,0.88)",
              border: `1px solid ${COR.linha}`,
              borderLeft: `6px solid ${COR.tealClaro}`,
              borderRadius: 16,
              padding: `${t(20)}px ${t(24)}px`,
            }}
          >
            <IconeUrna tamanho={t(vertical ? 110 : 76)} />
            <div style={{ display: "flex", flexDirection: "column", gap: t(6) }}>
              <Texto tamanho={vertical ? 46 : 32} style={{ fontWeight: 700 }}>
                O fiscal vai com a urna até a junta
              </Texto>
              <span style={{ fontFamily: MONO, fontSize: t(vertical ? 32 : 22), color: COR.ouro }}>{junta.referencia}</span>
            </div>
          </div>
        </Surge>
        <Surge inicio={g.fim} de="baixo">
          <Titulo tamanho={vertical ? 86 : 54}>O fim da votação é onde o voto vira número.</Titulo>
        </Surge>
        <Surge inicio={g.mais - 22} de="baixo">
          <Titulo tamanho={vertical ? 86 : 54}>
            E é onde a presença{" "}
            <span style={{ display: "inline-block", color: COR.ouro, transform: `scale(${frame < g.mais ? 1 : 0.7 + 0.3 * mais})`, opacity: frame < g.mais ? 0 : 1 }}>MAIS</span>{" "}
            pesa.
          </Titulo>
        </Surge>
      </div>
    </Fase>
  );

  return (
    <>
      <Sequence durationInFrames={g.boletim} layout="none">
        <ClipeSeHouver id="fila_secao" opacidade={0.4} veu={0.9} />
      </Sequence>
      <Sequence from={g.boletim} durationInFrames={Math.max(1, cena.frames - g.boletim)} layout="none">
        <ClipeSeHouver id="maos_boletim_porta" opacidade={0.36} veu={0.92} />
      </Sequence>
      <AbsoluteFill style={{ background: "linear-gradient(90deg, rgba(6,11,26,0.55), rgba(6,11,26,0.2))" }} />
      <Area style={{ flexDirection: vertical ? "column" : "row", gap: t(vertical ? 44 : 64), alignItems: vertical ? "stretch" : "center" }}>
        <div style={{ flex: "none", display: "flex", justifyContent: vertical ? "flex-start" : "center", width: vertical ? "100%" : t(420) }}>{relogio}</div>
        <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", justifyContent: "center", position: "relative" }}>
          <div style={{ display: "grid" }}>
            <div style={{ gridArea: "1 / 1" }}>{faseA}</div>
            <div style={{ gridArea: "1 / 1" }}>{faseB}</div>
            <div style={{ gridArea: "1 / 1" }}>{faseC}</div>
          </div>
        </div>
      </Area>
    </>
  );
};
