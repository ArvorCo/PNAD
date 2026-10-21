import type { CSSProperties, PropsWithChildren, ReactNode } from "react";
import { useCurrentFrame } from "remotion";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import { Chip, Entrada, Texto, Titulo } from "./Caixa";
import { Contador } from "./Contador";
import { Area, Surge } from "./Quadro";

/** Cores dos três papéis do par: o sinal, a explicação inocente e a conferência do fiscal. */
export const COR_SINAL = COR.media;
export const COR_EXPLICACAO = COR.outros;
export const COR_CONFERE = COR.tealClaro;

type PainelProps = PropsWithChildren<{ titulo: string; cor: string; inicio: number; style?: CSSProperties }>;

/** Painel de vidro com título em mono; aparece em `inicio` e o conteúdo entra depois, palavra a palavra. */
export const PainelPar: React.FC<PainelProps> = ({ titulo, cor, inicio, style, children }) => {
  const { t, vertical } = useFormato();
  return (
    <Surge inicio={inicio} style={{ display: "flex", flexDirection: "column", minWidth: 0, minHeight: 0, ...style }}>
      <div
        style={{
          flex: 1,
          background: COR.vidro,
          border: `1px solid ${COR.linha}`,
          borderTop: `4px solid ${cor}`,
          borderRadius: 16,
          padding: `${t(18)}px ${t(24)}px`,
          boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
          display: "flex",
          flexDirection: "column",
          gap: t(12),
          overflow: "hidden",
        }}
      >
        <div style={{ fontFamily: MONO, fontSize: t(vertical ? 21 : 17), letterSpacing: 3, color: cor }}>{titulo}</div>
        {children}
      </div>
    </Surge>
  );
};

/** Linha com marcador que entra na palavra dita. */
export const Ponto: React.FC<PropsWithChildren<{ q: number; cor?: string; tamanho?: number; forte?: boolean }>> = ({
  q,
  cor = COR.tealClaro,
  tamanho = 26,
  forte = false,
  children,
}) => {
  const { t, vertical } = useFormato();
  return (
    <Entrada inicio={q} de="esquerda">
      <div style={{ display: "flex", gap: t(12), alignItems: "baseline" }}>
        <span style={{ width: t(10), height: t(10), borderRadius: t(3), background: cor, flex: "none", transform: `translateY(-${t(3)}px)` }} />
        <Texto tamanho={vertical ? Math.round(tamanho * 1.15) : tamanho} style={{ fontWeight: forte ? 700 : 500 }}>
          {children}
        </Texto>
      </div>
    </Entrada>
  );
};

/** Número grande do sinal, contando do zero, com o rótulo do diagnóstico ao lado. */
export const NumeroSinal: React.FC<{ valor: number; q: number; rotulo: ReactNode; cor?: string; casas?: number; sufixo?: string; tamanho?: number }> = ({
  valor,
  q,
  rotulo,
  cor = COR_SINAL,
  casas = 0,
  sufixo = "",
  tamanho = 76,
}) => {
  const frame = useCurrentFrame();
  const { t, vertical } = useFormato();
  if (frame < q) {
    return null;
  }
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: t(16), flexWrap: "wrap" }}>
      <Contador valor={valor} inicio={q} casas={casas} sufixo={sufixo} tamanho={t(tamanho)} cor={cor} />
      <Entrada inicio={q + 8} de="direita">
        <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 29 : 24), lineHeight: 1.2, color: COR.tinta, maxWidth: t(vertical ? 620 : 460) }}>{rotulo}</div>
      </Entrada>
    </div>
  );
};

/** Item da faixa do fiscal: texto curto que entra na palavra dita. */
export const ItemConfere: React.FC<PropsWithChildren<{ q: number }>> = ({ q, children }) => {
  const { t, vertical } = useFormato();
  return (
    <Entrada inicio={q} de="baixo">
      <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 30 : 25), color: COR.tinta, padding: `${t(6)}px ${t(14)}px`, borderRadius: 10, background: "rgba(95,211,230,0.12)", border: `1px solid ${COR_CONFERE}66` }}>
        {children}
      </div>
    </Entrada>
  );
};

type ParProps = {
  /** Posição do par (1 a 7). */
  numero: number;
  titulo: string;
  sinal: ReactNode;
  explicacao: ReactNode;
  /** Conteúdo da faixa de baixo, que entra em `qConfere`. */
  confere: ReactNode;
  qConfere: number;
  /** Quadro em que os dois painéis aparecem com o título (o conteúdo entra depois). */
  qSinal?: number;
  qExplicacao?: number;
  /** Cartão de exemplo: à direita no 16:9, embaixo dos painéis no 9:16. */
  exemplo?: ReactNode;
  /** Peso da coluna do exemplo no 16:9 (a dos painéis pesa 1). */
  pesoExemplo?: number;
  /** Peso do painel do sinal contra o da explicação (1) quando os dois estão empilhados. */
  pesoSinal?: number;
  /** No 9:16, empilha sinal e explicação em largura total mesmo com exemplo (para gráficos largos). */
  empilharNoVertical?: boolean;
  /** No 9:16, altura reservada ao exemplo desde o começo (px de referência), para a coluna não pular. */
  alturaExemploVertical?: number;
  rotuloSinal?: string;
  rotuloExplicacao?: string;
  rotuloConfere?: string;
  total?: number;
};

/**
 * Layout dos sete pares do capítulo 4: SINAL (o que o log mostra), EXPLICAÇÃO INOCENTE e, embaixo,
 * a faixa O QUE O FISCAL CONFERE, que entra na palavra da narração. A faixa tem lugar reservado
 * desde o começo para o layout não pular.
 */
export const Par: React.FC<ParProps> = ({
  numero,
  titulo,
  sinal,
  explicacao,
  confere,
  qConfere,
  qSinal = 6,
  qExplicacao = 12,
  exemplo,
  pesoExemplo = 1.25,
  pesoSinal = 1,
  empilharNoVertical = false,
  alturaExemploVertical,
  rotuloSinal = "SINAL",
  rotuloExplicacao = "EXPLICAÇÃO INOCENTE",
  rotuloConfere = "O QUE O FISCAL CONFERE",
  total = 7,
}) => {
  const { vertical, t } = useFormato();
  // Empilhados no 9:16 sem exemplo, os painéis crescem com o conteúdo; lado a lado, dividem a largura.
  const empilhado = vertical && (!exemplo || empilharNoVertical);
  const base = empilhado ? "auto" : "0";
  const painelSinal = (
    <PainelPar titulo={rotuloSinal} cor={COR_SINAL} inicio={qSinal} style={{ flex: `${pesoSinal} 1 ${base}` }}>
      {sinal}
    </PainelPar>
  );
  const painelExplicacao = (
    <PainelPar titulo={rotuloExplicacao} cor={COR_EXPLICACAO} inicio={qExplicacao} style={{ flex: `1 1 ${base}` }}>
      {explicacao}
    </PainelPar>
  );
  const faixa = (
    <div style={{ flex: "none", minHeight: t(vertical ? 190 : 122) }}>
      <Surge inicio={qConfere}>
        <div
          style={{
            background: "rgba(8,20,44,0.9)",
            border: `1px solid ${COR.linha}`,
            borderLeft: `6px solid ${COR_CONFERE}`,
            borderRadius: 16,
            padding: `${t(14)}px ${t(24)}px`,
            display: "flex",
            flexDirection: "column",
            gap: t(10),
            boxShadow: `0 0 40px ${COR_CONFERE}22`,
          }}
        >
          <div style={{ fontFamily: MONO, fontSize: t(vertical ? 21 : 17), letterSpacing: 3, color: COR_CONFERE }}>{rotuloConfere}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: t(12), alignItems: "center" }}>{confere}</div>
        </div>
      </Surge>
    </div>
  );
  const cabecalho = (
    <Entrada inicio={0} de="esquerda">
      <div style={{ display: "flex", alignItems: "center", gap: t(18), flexWrap: "wrap" }}>
        <Chip cor={COR.alta} solido tamanho={vertical ? 20 : 22}>
          par {numero} de {total}
        </Chip>
        <Titulo tamanho={vertical ? 50 : 52}>{titulo}</Titulo>
      </div>
    </Entrada>
  );
  const marcaDagua = (
    <div style={{ position: "absolute", right: 0, top: -t(30), fontFamily: MONO, fontWeight: 700, fontSize: t(180), color: COR.tinta, opacity: 0.05, lineHeight: 1 }}>
      {String(numero).padStart(2, "0")}
    </div>
  );

  if (vertical) {
    return (
      <Area style={{ gap: t(24), justifyContent: "center" }}>
        {marcaDagua}
        {cabecalho}
        {!empilhado ? (
          <div style={{ display: "flex", gap: t(18), minHeight: t(300) }}>
            {painelSinal}
            {painelExplicacao}
          </div>
        ) : (
          <>
            <div style={{ display: "flex", flexDirection: "column", minHeight: t(220) }}>{painelSinal}</div>
            <div style={{ display: "flex", flexDirection: "column", minHeight: t(200) }}>{painelExplicacao}</div>
          </>
        )}
        {exemplo ? (
          <div style={{ display: "flex", flexDirection: "column", gap: t(14), minHeight: alturaExemploVertical === undefined ? undefined : t(alturaExemploVertical) }}>{exemplo}</div>
        ) : null}
        {faixa}
      </Area>
    );
  }

  return (
    <Area style={{ gap: t(20) }}>
      {marcaDagua}
      {cabecalho}
      <div style={{ flex: 1, minHeight: 0, display: "flex", gap: t(28) }}>
        {exemplo ? (
          <>
            <div style={{ flex: "1 1 0", minWidth: 0, display: "flex", flexDirection: "column", gap: t(18) }}>
              {painelSinal}
              {painelExplicacao}
            </div>
            <div style={{ flex: `${pesoExemplo} 1 0`, minWidth: 0, display: "flex", flexDirection: "column", gap: t(14) }}>{exemplo}</div>
          </>
        ) : (
          <>
            {painelSinal}
            {painelExplicacao}
          </>
        )}
      </div>
      {faixa}
    </Area>
  );
};
