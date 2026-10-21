import { Sequence, useCurrentFrame } from "remotion";
import { Chip, Texto, Titulo } from "../componentes/Caixa";
import { Clipe } from "../componentes/Clipe";
import { formatoCaptura, segundoDoStill } from "../componentes/Gravacao";
import { IconeCheck, IconeX } from "../componentes/Icones";
import { BarraUrl } from "../componentes/Navegador";
import { Area, Etiqueta, Surge, useArea } from "../componentes/Quadro";
import { larguraDaTela, larguraDoTelefone, Telefone } from "../componentes/Telefone";
import { rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { FPS } from "../plano";
import { COR, MONO } from "../tema";
import type { CenaProps } from "./registro";

const LER = "cap_totalizacao_ler";
const CONFERIR = "cap_totalizacao_conferir";
/** Proporção da coluna do aplicativo dentro da captura de mesa (480 × 1080 no centro de 1920 × 1080). */
const COLUNA_CELULAR = 480 / 1080;

/** Linha de leitura que varre a tela do celular enquanto o QR é lido. */
const Varredura: React.FC<{ de: number; ate: number }> = ({ de, ate }) => {
  const frame = useCurrentFrame();
  if (frame < de || frame > ate) {
    return null;
  }
  const p = ((frame - de) % 40) / 40;
  const o = rampa(frame, de, de + 6) * (1 - rampa(frame, ate - 6, ate));
  return (
    <div
      style={{
        position: "absolute",
        left: "6%",
        right: "6%",
        top: `${18 + p * 60}%`,
        height: 4,
        borderRadius: 2,
        background: COR.outros,
        boxShadow: `0 0 24px ${COR.outros}`,
        opacity: o,
      }}
    />
  );
};

type Passo = { n: number; texto: string; detalhe: string; q: number };

/** Linha "prova / não prova" do rótulo fixo. */
const LinhaRotulo: React.FC<{ sim: string; nao: string; qSim: number; qNao: number }> = ({ sim, nao, qSim, qNao }) => {
  const { vertical, t } = useFormato();
  const tam = vertical ? 40 : 28;
  return (
    <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: t(vertical ? 8 : 28), flexWrap: "wrap" }}>
      <Surge inicio={qSim} de="esquerda">
        <div style={{ display: "flex", alignItems: "center", gap: t(12) }}>
          <IconeCheck tamanho={t(tam + 10)} cor={COR.outros} />
          <Texto tamanho={tam} style={{ fontWeight: 700 }}>
            {sim}
          </Texto>
        </div>
      </Surge>
      <Surge inicio={qNao} de="esquerda">
        <div style={{ display: "flex", alignItems: "center", gap: t(12) }}>
          <IconeX tamanho={t(tam + 10)} cor={COR.alta} />
          <Texto tamanho={tam} style={{ fontWeight: 700 }}>
            {nao}
          </Texto>
        </div>
      </Surge>
    </div>
  );
};

/**
 * Com o boletim na mão: o endereço da totalização paralela, o aplicativo real lendo os QR do
 * exemplo oficial do TSE e a tela de conferência (nunca o envio), os três passos e o rótulo fixo
 * do que a soma prova e do que não prova.
 */
export const FechaTotalizacao: React.FC<CenaProps> = ({ g, dados, cena }) => {
  const { vertical, t } = useFormato();
  const formato = formatoCaptura(LER, vertical);
  const proporcao = formato === "9x16" ? 9 / 16 : COLUNA_CELULAR;
  const comparar = dados.fechamento.find((f) => f.id === "comparar_depois");

  // Gravação 1 (até o painel): a explicação do aplicativo e, a partir de "aplicativo", a câmera
  // lendo os três QR até a tela "tudo lido". Gravação 2: a conferência dos cargos, sem enviar.
  const ficha = segundoDoStill(LER, "ficha", formato) ?? 5.08;
  const camera = segundoDoStill(LER, "camera", formato) ?? 13.64;
  const completo = segundoDoStill(CONFERIR, "completo", formato) ?? 7.65;
  const entraCamera = Math.max(1, g.aplicativo - Math.round(0.4 * FPS));
  const tela = (
    <>
      <Sequence durationInFrames={entraCamera} layout="none">
        <Clipe id={LER} inicio={Math.max(0, ficha - 0.5)} />
      </Sequence>
      <Sequence from={entraCamera} durationInFrames={Math.max(1, g.painel - entraCamera)} layout="none">
        <Clipe id={LER} inicio={Math.max(0, camera - 0.6)} />
      </Sequence>
      <Sequence from={g.painel} durationInFrames={Math.max(1, cena.frames - g.painel)} layout="none">
        <Clipe id={CONFERIR} inicio={Math.max(0, completo - 0.4)} />
      </Sequence>
      <Varredura de={g.qr - 12} ate={g.confere + 20} />
    </>
  );

  const passos: Passo[] = [
    { n: 1, texto: "Lê os QR do boletim", detalhe: "um por vez, na câmera", q: g.qr },
    { n: 2, texto: "Confere a assinatura da urna", detalhe: "contra os certificados", q: g.confere },
    { n: 3, texto: "Grava e compara com o TSE", detalhe: comparar ? `mesma seção · ${comparar.referencia}` : "mesma seção", q: g.compara },
  ];
  const tamPasso = vertical ? 32 : 24;
  const listaPassos = (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: t(vertical ? 16 : 12) }}>
      {passos.map((p) => (
        <Surge key={p.n} inicio={p.q} de="esquerda">
          <Etiqueta cor={COR.outros} tamanho={tamPasso} style={{ display: "flex", gap: t(14), alignItems: "baseline" }}>
            <span style={{ fontFamily: MONO, color: COR.outros }}>{p.n}</span>
            <span style={{ display: "flex", flexDirection: "column", gap: t(2) }}>
              <span>{p.texto}</span>
              <span style={{ fontFamily: MONO, fontWeight: 500, fontSize: t(vertical ? 28 : 22), color: COR.suave }}>{p.detalhe}</span>
            </span>
          </Etiqueta>
        </Surge>
      ))}
    </div>
  );

  const rotulo = (
    <Surge inicio={g.rotulo} de="baixo">
      <div
        style={{
          background: "rgba(12,26,58,0.9)",
          border: `2px solid ${COR.ouro}`,
          borderRadius: 18,
          padding: `${t(vertical ? 22 : 18)}px ${t(24)}px`,
          display: "flex",
          flexDirection: "column",
          gap: t(12),
          boxShadow: `0 0 40px ${COR.ouro}22`,
        }}
      >
        <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 28 : 22), letterSpacing: 3, color: COR.ouro }}>O RÓTULO</span>
        <LinhaRotulo sim="Soma dos boletins recebidos" nao="não é projeção" qSim={g.soma} qNao={g.projecao} />
        <LinhaRotulo sim="Prova transmissão e totalização" nao="não prova o interior da urna" qSim={g.prova} qNao={g.naoProva} />
        <Surge inicio={g.veredito - 14} de="zoom">
          <Titulo tamanho={vertical ? 56 : 38} cor={COR.ouro}>
            É conferência, não é veredito.
          </Titulo>
        </Surge>
      </div>
    </Surge>
  );

  const cabecalho = (
    <div style={{ display: "flex", flexDirection: "column", gap: t(14) }}>
      <div style={{ display: "flex", alignItems: "center", gap: t(14), flexWrap: "wrap" }}>
        <Chip cor={COR.outros} solido tamanho={vertical ? 26 : 22}>
          totalização paralela
        </Chip>
      </div>
      <BarraUrl url="brasil.arvor.co/totalizacao" inicio={g.brasil - 10} cor={COR.outros} tamanho={vertical ? 40 : 34} style={{ alignSelf: "flex-start" }} />
    </div>
  );

  if (vertical) {
    const alturaAparelho = t(800);
    const telaL = larguraDaTela(alturaAparelho, proporcao, t);
    return (
      <Area style={{ gap: t(26) }}>
        {cabecalho}
        <div style={{ display: "flex", gap: t(26), alignItems: "flex-start" }}>
          <Telefone largura={telaL} proporcao={proporcao} cor={COR.outros}>
            {tela}
          </Telefone>
          <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", gap: t(18) }}>{listaPassos}</div>
        </div>
        {rotulo}
      </Area>
    );
  }

  return (
    <Area style={{ flexDirection: "row", gap: t(56), alignItems: "flex-start" }}>
      <AparelhoLargo proporcao={proporcao}>{tela}</AparelhoLargo>
      <div style={{ flex: 1, minWidth: 0, height: "100%", display: "flex", flexDirection: "column", gap: t(22) }}>
        {cabecalho}
        {listaPassos}
        {rotulo}
      </div>
    </Area>
  );
};

/** Aparelho do 16:9 ocupando a altura útil. */
const AparelhoLargo: React.FC<{ proporcao: number; children: React.ReactNode }> = ({ proporcao, children }) => {
  const { t } = useFormato();
  const a = useArea();
  const telaL = larguraDaTela(a.altura, proporcao, t);
  return (
    <div style={{ width: larguraDoTelefone(telaL, t), flex: "none", marginLeft: t(24) }}>
      <Telefone largura={telaL} proporcao={proporcao} cor={COR.outros}>
        {children}
      </Telefone>
    </div>
  );
};
