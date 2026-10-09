import { useCurrentFrame, useVideoConfig } from "remotion";
import { COR, FONTE, MONO, NIVEL_COR, NIVEL_NOME } from "../tema";
import type { Exemplo } from "../tipos";
import { Chip } from "./Caixa";
import { decimal, inteiro, mola } from "./util";

type BarraProps = {
  nome: string;
  cor: string;
  secao: number;
  zona: number;
  progresso: number;
  compacto: boolean;
};

const Barra: React.FC<BarraProps> = ({ nome, cor, secao, zona, progresso, compacto }) => (
  <div style={{ display: "grid", gridTemplateColumns: compacto ? "88px 1fr 150px" : "110px 1fr 190px", alignItems: "center", gap: 14 }}>
    <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: compacto ? 24 : 26, color: cor }}>{nome}</div>
    <div style={{ position: "relative", height: compacto ? 26 : 30, background: "rgba(255,255,255,0.07)", borderRadius: 6, overflow: "visible" }}>
      <div
        style={{
          width: `${secao * progresso}%`,
          height: "100%",
          background: cor,
          borderRadius: 6,
          boxShadow: `0 0 18px ${cor}66`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: `${zona * progresso}%`,
          top: -6,
          bottom: -6,
          width: 3,
          background: COR.tinta,
          opacity: 0.9,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: `${zona * progresso}%`,
          top: -24,
          transform: "translateX(-50%)",
          fontFamily: MONO,
          fontSize: 13,
          letterSpacing: 1,
          color: COR.suave,
          whiteSpace: "nowrap",
        }}
      >
        zona {decimal(zona)}%
      </div>
    </div>
    <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: compacto ? 28 : 32, color: COR.tinta, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
      {decimal(secao * progresso)}%
    </div>
  </div>
);

type Props = { exemplo: Exemplo; inicio: number; compacto?: boolean };

/** Cartão da seção: cabeçalho, local, contagens e as barras seção × resto da zona. */
export const CartaoSecao: React.FC<Props> = ({ exemplo: e, inicio, compacto = false }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = mola(frame, fps, inicio, { damping: 16 });
  const barras = mola(frame, fps, inicio + 14, { damping: 20, stiffness: 90 });
  if (frame < inicio) {
    return null;
  }
  const corNivel = NIVEL_COR[e.nivel];
  const contagens: [string, number][] = [
    ["aptos", e.aptos],
    ["votantes", e.votantes],
    ["válidos", e.validos],
    ["brancos", e.brancos],
    ["nulos", e.nulos],
  ];
  return (
    <div
      style={{
        opacity: Math.min(1, p * 1.4),
        transform: `translateY(${(1 - p) * 40}px) scale(${0.96 + 0.04 * p})`,
        background: "linear-gradient(160deg, rgba(20,38,78,0.92), rgba(8,16,38,0.92))",
        border: `1px solid ${COR.linha}`,
        borderTop: `4px solid ${corNivel}`,
        borderRadius: 18,
        padding: compacto ? "20px 24px" : "24px 30px",
        boxShadow: "0 30px 80px rgba(0,0,0,0.45)",
        display: "flex",
        flexDirection: "column",
        gap: compacto ? 14 : 18,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <Chip cor={COR.tealClaro} solido tamanho={compacto ? 18 : 20}>
          {e.uf}
        </Chip>
        <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: compacto ? 34 : 40, color: COR.tinta, letterSpacing: -0.5, flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {e.municipio}
        </div>
        <Chip cor={corNivel} tamanho={compacto ? 15 : 17}>
          nível {NIVEL_NOME[e.nivel]}
        </Chip>
      </div>
      <div style={{ display: "flex", gap: 22, alignItems: "baseline", flexWrap: "wrap" }}>
        <div style={{ fontFamily: MONO, fontSize: compacto ? 20 : 22, color: COR.tealClaro, letterSpacing: 2 }}>
          ZONA {e.zona} · SEÇÃO {e.secao}
        </div>
        <div style={{ fontFamily: MONO, fontSize: compacto ? 16 : 18, color: COR.suave, letterSpacing: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", flex: 1 }}>
          {e.local}
          {e.bairro ? ` · ${e.bairro}` : ""}
        </div>
      </div>
      <div style={{ display: "flex", gap: compacto ? 14 : 22, flexWrap: "wrap" }}>
        {contagens.map(([nome, valor]) => (
          <div key={nome} style={{ fontFamily: MONO, fontSize: compacto ? 17 : 19, color: COR.suave, letterSpacing: 1 }}>
            <span style={{ color: COR.tinta, fontWeight: 700 }}>{inteiro(valor)}</span> {nome}
          </div>
        ))}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: compacto ? 22 : 26, marginTop: 6 }}>
        <Barra nome="Lula" cor={COR.lula} secao={e.lula_pct} zona={e.zona_lula_pct} progresso={barras} compacto={compacto} />
        <Barra nome="Flávio" cor={COR.flavio} secao={e.flavio_pct} zona={e.zona_flavio_pct} progresso={barras} compacto={compacto} />
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginTop: 4 }}>
        <span style={{ fontFamily: MONO, fontSize: 15, color: COR.suave, letterSpacing: 2 }}>CRITÉRIOS</span>
        {e.criterios.map((c) => (
          <Chip key={c} cor={COR.ouro} tamanho={14}>
            {c}
          </Chip>
        ))}
        <span style={{ flex: 1 }} />
        <span style={{ fontFamily: MONO, fontSize: 17, color: corNivel, letterSpacing: 2 }}>
          {e.pontuacao} PONTOS
        </span>
      </div>
    </div>
  );
};
