import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { Caixa, Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Contador } from "../componentes/Contador";
import { mola, rampa } from "../componentes/util";
import { useFormato } from "../formato";
import { quadro, type Cena } from "../plano";
import { COR, FONTE, MONO } from "../tema";

/** Barra de navegador com a URL, estilo cartão de jogo. */
const Navegador: React.FC<{ url: string; inicio: number; cor: string; tamanho: number }> = ({ url, inicio, cor, tamanho }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = mola(frame, fps, inicio, { damping: 14 });
  const digitadas = Math.round(rampa(frame, inicio + 6, inicio + 40) * url.length);
  if (frame < inicio) {
    return null;
  }
  return (
    <div style={{ transform: `scale(${0.9 + 0.1 * p})`, opacity: p, background: "rgba(3,8,20,0.85)", border: `2px solid ${cor}`, borderRadius: 18, padding: "18px 26px", display: "flex", alignItems: "center", gap: 18, boxShadow: `0 0 40px ${cor}44` }}>
      <div style={{ display: "flex", gap: 8 }}>
        {[COR.alta, COR.media, COR.outros].map((c) => (
          <div key={c} style={{ width: 14, height: 14, borderRadius: 7, background: c }} />
        ))}
      </div>
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: tamanho, color: COR.tinta, letterSpacing: 1, whiteSpace: "nowrap" }}>
        {url.slice(0, digitadas)}
        <span style={{ color: cor, opacity: frame % 20 < 10 ? 1 : 0 }}>▌</span>
      </div>
    </div>
  );
};

const Item: React.FC<{ inicio: number; numero: string; texto: string; cor: string; tamanho: number }> = ({ inicio, numero, texto, cor, tamanho }) => (
  <Entrada inicio={inicio} de="esquerda">
    <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
      <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: tamanho + 4, color: cor, minWidth: 56 }}>{numero}</span>
      <Texto tamanho={tamanho}>{texto}</Texto>
    </div>
  </Entrada>
);

/** Ação 1: seja fiscal, em fiscaisdopl.com.br, com o roteiro do dia. */
export const Acao1: React.FC<{ cena: Cena }> = ({ cena }) => {
  const { vertical, margem, altura, largura } = useFormato();
  const p = cena.palavras;
  const qUrl = quadro(p, "fiscais", 2.5);
  const qMinuto = quadro(p, "minuto", 6);
  const qTitulo = quadro(p, "título", 7.5);
  const qPrazo = quadro(p, "prazo", 9);
  const passos: [number, string][] = [
    [quadro(p, "sete", 13), "Chegar antes das 7h e assistir à zerésima"],
    [quadro(p, "lacres", 16), "Conferir lacres e número da urna"],
    [quadro(p, "sala", 18), "Ficar na sala o dia inteiro"],
    [quadro(p, "ata", 20), "Anotar na ata cada ocorrência, com hora"],
    [quadro(p, "boletim", 24), "Pedir a via do boletim impresso e comparar com o publicado"],
  ];
  const qSem = quadro(p, "Sem", 29);
  const t = vertical ? 24 : 26;

  return (
    <AbsoluteFill style={{ padding: `${vertical ? 170 : 150}px ${margem}px ${vertical ? altura * 0.16 + 130 : 220}px`, gap: 20 }}>
      <Entrada inicio={0} de="esquerda">
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <Chip cor={COR.alta} solido tamanho={24}>ação 1</Chip>
          <Titulo tamanho={vertical ? 54 : 64}>Seja fiscal</Titulo>
        </div>
      </Entrada>
      <Navegador url="fiscaisdopl.com.br" inicio={qUrl} cor={COR.alta} tamanho={vertical ? 44 : 56} />
      <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
        <Entrada inicio={qMinuto} de="baixo"><Chip cor={COR.ouro} tamanho={vertical ? 17 : 19}>cadastro em 1 minuto</Chip></Entrada>
        <Entrada inicio={qTitulo} de="baixo"><Chip cor={COR.ouro} tamanho={vertical ? 17 : 19}>título de eleitor + selfie</Chip></Entrada>
        <Entrada inicio={qPrazo} de="baixo"><Chip cor={COR.alta} tamanho={vertical ? 17 : 19}>prazo: 24 de outubro</Chip></Entrada>
      </div>
      <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 24, flex: vertical ? "none" : 1 }}>
        <Caixa cor={COR.tealClaro} titulo="NO DIA" style={{ flex: vertical ? "none" : 1, display: "flex", flexDirection: "column", gap: 14, justifyContent: "center" }}>
          {passos.map(([q, texto], i) => (
            <Item key={texto} inicio={q} numero={String(i + 1).padStart(2, "0")} texto={texto} cor={COR.tealClaro} tamanho={t} />
          ))}
        </Caixa>
        <Entrada inicio={qSem} de="baixo" style={{ width: vertical ? "100%" : largura * 0.3, flex: "none" }}>
          <Caixa cor={COR.ouro} style={{ height: "100%", display: "flex", flexDirection: "column", justifyContent: "center" }}>
            <Titulo tamanho={vertical ? 34 : 38}>Sem confronto.</Titulo>
            <Texto tamanho={t} cor={COR.suave} style={{ marginTop: 10 }}>Prova é foto, hora, lugar e nome.</Texto>
          </Caixa>
        </Entrada>
      </div>
    </AbsoluteFill>
  );
};

const Campo: React.FC<{ rotulo: string; valor: string; inicio: number; largura: number }> = ({ rotulo, valor, inicio, largura }) => {
  const frame = useCurrentFrame();
  const n = Math.round(rampa(frame, inicio, inicio + 18) * valor.length);
  return (
    <div style={{ width: largura, display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontFamily: MONO, fontSize: 15, letterSpacing: 2, color: COR.suave }}>{rotulo}</span>
      <div style={{ border: `2px solid ${frame >= inicio ? COR.tealClaro : COR.linha}`, borderRadius: 10, padding: "10px 14px", fontFamily: MONO, fontWeight: 700, fontSize: 30, color: COR.tinta, minHeight: 56 }}>
        {frame >= inicio ? valor.slice(0, n) : ""}
      </div>
    </div>
  );
};

/** Ação 2: politize sua vizinhança, com o formulário e o boletim do local. */
export const Acao2: React.FC<{ cena: Cena }> = ({ cena }) => {
  const frame = useCurrentFrame();
  const { vertical, margem, altura, largura } = useFormato();
  const p = cena.palavras;
  const qUrl = quadro(p, "brasil", 3);
  const qUf = quadro(p, "UF", 8);
  const qZona = quadro(p, "zona", 9);
  const qSecao = quadro(p, "seção", 10);
  const qBoletim = quadro(p, "recebe", 12);
  const qVotou = quadro(p, "como", 14);
  const qCasa = quadro(p, "quanta", 16);
  const qOutro = quadro(p, "quantos", 18);
  const qIndice = quadro(p, "índice", 21);
  const qLado = quadro(p, "lado", 25);
  const qConversar = quadro(p, "conversar", 29);
  const qSilencio = quadro(p, "silêncio", 32);
  const indice = Math.round(rampa(frame, qIndice, qIndice + 50) * 67);
  const t = vertical ? 24 : 26;

  return (
    <AbsoluteFill style={{ padding: `${vertical ? 170 : 150}px ${margem}px ${vertical ? altura * 0.16 + 130 : 220}px`, gap: 20 }}>
      <Entrada inicio={0} de="esquerda">
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <Chip cor={COR.outros} solido tamanho={24}>ação 2</Chip>
          <Titulo tamanho={vertical ? 50 : 60}>Politize sua vizinhança</Titulo>
        </div>
      </Entrada>
      <Navegador url="brasil.arvor.co/politize" inicio={qUrl} cor={COR.outros} tamanho={vertical ? 40 : 56} />
      <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap: 24, flex: vertical ? "none" : 1 }}>
        <Caixa cor={COR.tealClaro} titulo="ONDE VOCÊ VOTA?" style={{ width: vertical ? "100%" : largura * 0.32, flex: "none" }}>
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
            <Campo rotulo="UF" valor="SP" inicio={qUf} largura={100} />
            <Campo rotulo="ZONA" valor="001" inicio={qZona} largura={130} />
            <Campo rotulo="SEÇÃO" valor="0257" inicio={qSecao} largura={150} />
          </div>
          <Texto tamanho={18} cor={COR.suave} style={{ marginTop: 14 }}>Está no título de eleitor e no e-Título. Nada sai do seu aparelho.</Texto>
          <Entrada inicio={qLado} de="baixo" style={{ marginTop: 16 }}>
            <Chip cor={COR.flavio} tamanho={16}>lado declarado: Flávio no 2º turno</Chip>
          </Entrada>
        </Caixa>
        {frame >= qBoletim ? (
          <Entrada inicio={qBoletim} de="baixo" style={{ flex: 1, minWidth: 0 }}>
            <Caixa cor={COR.outros} titulo="BOLETIM DA VIZINHANÇA" style={{ height: vertical ? "auto" : "100%", display: "flex", flexDirection: "column", gap: 14 }}>
              <Item inicio={qVotou} numero="▣" texto="Como o seu local votou no 1º turno" cor={COR.lula} tamanho={t} />
              <Item inicio={qCasa} numero="☾" texto="Quanta gente ficou em casa" cor={COR.media} tamanho={t} />
              <Item inicio={qOutro} numero="◇" texto="Quantos votaram em outro nome" cor={COR.outros} tamanho={t} />
              {frame >= qIndice ? (
                <div style={{ marginTop: 6 }}>
                  <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
                    <Contador valor={67} inicio={qIndice} duracao={50} tamanho={vertical ? 56 : 64} cor={COR.tealClaro} />
                    <span style={{ fontFamily: FONTE, fontSize: t, color: COR.tinta }}>índice de conversa, de 0 a 100</span>
                  </div>
                  <div style={{ height: 14, background: "rgba(255,255,255,0.08)", borderRadius: 7, marginTop: 8, overflow: "hidden" }}>
                    <div style={{ width: `${indice}%`, height: "100%", background: `linear-gradient(90deg, ${COR.teal}, ${COR.tealClaro})` }} />
                  </div>
                </div>
              ) : null}
            </Caixa>
          </Entrada>
        ) : null}
      </div>
      <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
        <Entrada inicio={qConversar} de="baixo"><Chip cor={COR.outros} solido tamanho={vertical ? 20 : 24}>converse antes, com quem você conhece</Chip></Entrada>
        <Entrada inicio={qSilencio} de="baixo"><Chip cor={COR.alta} tamanho={vertical ? 20 : 24}>no dia, silêncio (Lei 9.504, art. 39-A)</Chip></Entrada>
      </div>
    </AbsoluteFill>
  );
};
