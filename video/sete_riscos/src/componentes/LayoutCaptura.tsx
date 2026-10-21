import type { ReactNode } from "react";
import { useFormato } from "../formato";
import { COR, MONO } from "../tema";
import type { FormatoMidia } from "../tipos";
import { formatoCaptura, TelaCheia, TOPO_TELA_CHEIA } from "./Gravacao";
import { ALTURA_BARRA, Navegador } from "./Navegador";
import { Fase, useArea } from "./Quadro";
import { larguraDaTela, larguraDoTelefone, Telefone } from "./Telefone";

/** Proporção da coluna do aplicativo dentro da captura de mesa (480 × 1080 no centro de 1920 × 1080). */
const COLUNA_CELULAR = 480 / 1080;

const UrlPequena: React.FC<{ url: string; cor: string }> = ({ url, cor }) => {
  const { t } = useFormato();
  return (
    <div style={{ alignSelf: "flex-start", fontFamily: MONO, fontSize: t(20), color: cor, letterSpacing: 1, padding: `${t(4)}px ${t(12)}px`, border: `1px solid ${cor}`, borderRadius: 8, background: "rgba(3,8,20,0.7)" }}>
      {url}
    </div>
  );
};

type LayoutNavegadorProps = {
  /** Captura principal: o formato dela decide a proporção da moldura. */
  id: string;
  url: string;
  inicioUrl?: number;
  cor?: string;
  /** Conteúdo da tela (clipes e sequências), conforme o formato resolvido da captura. */
  tela: (formato: FormatoMidia | null) => ReactNode;
  painel: ReactNode;
  /** Painel para a tela cheia do 9:16 (falta = `painel`), que tem menos altura. */
  painelCompacto?: ReactNode;
  /** Largura do painel lateral no 16:9, em px de referência. */
  larguraPainel?: number;
  /** Na tela cheia do 9:16, fração da área útil em que começa o painel (falta = 0,57). */
  inicioPainel?: number;
};

/** Fração da área útil, a partir do topo, em que começa o painel sobre a captura em tela cheia. */
export const INICIO_PAINEL_NAVEGADOR = 0.57;
const INICIO_PAINEL_TELEFONE = 0.69;

/**
 * Altura, em px da caixa da `TelaCheia`, da faixa da captura que fica nítida acima do painel
 * (o degradê do painel começa 6% da altura da tela antes dele), para quem monta a tela por conta.
 */
export const useJanelaTelaCheia = (inicioPainel = INICIO_PAINEL_NAVEGADOR): number => {
  const { altura } = useFormato();
  const a = useArea();
  const topo = a.topo + a.altura * inicioPainel;
  return ((Math.round((topo / altura) * 100) - 6) / 100) * altura - TOPO_TELA_CHEIA;
};

/**
 * Captura de página em moldura de navegador com um painel de texto. No 16:9, moldura à esquerda e
 * painel à direita; no 9:16 com captura de mesa, moldura em cima e painel embaixo; no 9:16 com
 * captura nativa vertical, a captura ocupa a tela inteira e o painel fica na metade de baixo.
 */
export const LayoutNavegador: React.FC<LayoutNavegadorProps> = ({
  id,
  url,
  inicioUrl,
  cor = COR.teal,
  tela,
  painel,
  painelCompacto,
  larguraPainel = 520,
  inicioPainel = INICIO_PAINEL_NAVEGADOR,
}) => {
  const { altura: alturaTela } = useFormato();
  const { vertical, t } = useFormato();
  const a = useArea();
  const formato = formatoCaptura(id, vertical);
  const proporcao = formato === "9x16" ? 9 / 16 : 16 / 9;
  const barra = t(ALTURA_BARRA);

  if (vertical && formato === "9x16") {
    const topo = a.topo + a.altura * inicioPainel;
    return (
      <>
        <TelaCheia corte={topo / alturaTela}>{tela(formato)}</TelaCheia>
        <div style={{ position: "absolute", left: a.esquerda, width: a.largura, top: topo, height: a.topo + a.altura - topo, display: "flex", flexDirection: "column", justifyContent: "flex-start", gap: t(14) }}>
          <UrlPequena url={url} cor={cor} />
          {painelCompacto ?? painel}
        </div>
      </>
    );
  }

  if (vertical) {
    return (
      <div style={{ position: "absolute", left: a.esquerda, top: a.topo, width: a.largura, height: a.altura, display: "flex", flexDirection: "column", gap: t(26) }}>
        <Navegador url={url} largura={a.largura} proporcao={proporcao} inicioUrl={inicioUrl} cor={cor}>
          {tela(formato)}
        </Navegador>
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>{painel}</div>
      </div>
    );
  }

  const gap = t(34);
  const largura = Math.min(a.largura - t(larguraPainel) - gap, (a.altura - barra) * proporcao);
  return (
    <div style={{ position: "absolute", left: a.esquerda, top: a.topo, width: a.largura, height: a.altura, display: "flex", gap, alignItems: "flex-start" }}>
      <Navegador url={url} largura={largura} proporcao={proporcao} inicioUrl={inicioUrl} cor={cor}>
        {tela(formato)}
      </Navegador>
      <div style={{ flex: 1, minWidth: 0, height: "100%", display: "flex", flexDirection: "column" }}>{painel}</div>
    </div>
  );
};

type LayoutTelefoneProps = {
  id: string;
  tela: (formato: FormatoMidia | null) => ReactNode;
  painel: ReactNode;
  /** Bloco largo embaixo (no 16:9, embaixo do painel). */
  rodape?: ReactNode;
  /** Na tela cheia do 9:16 não cabem os dois: o painel sai e o rodapé entra neste quadro. */
  trocaRodape?: number;
  /** Painel único para a tela cheia do 9:16 (substitui painel e rodapé). */
  painelCompacto?: ReactNode;
  cor?: string;
};

/**
 * Captura de aplicativo dentro de um aparelho. A captura de mesa mostra o aplicativo numa coluna
 * de 480 px no centro; o `Clipe` com recorte central a enquadra sozinho numa tela de 4:9. Captura
 * nativa 9:16 no vídeo vertical vai para a tela inteira.
 */
export const LayoutTelefone: React.FC<LayoutTelefoneProps> = ({ id, tela, painel, rodape, trocaRodape, painelCompacto, cor = COR.tealClaro }) => {
  const { vertical, t, altura: alturaTela } = useFormato();
  const a = useArea();
  const formato = formatoCaptura(id, vertical);
  const proporcao = formato === "9x16" ? 9 / 16 : COLUNA_CELULAR;

  if (vertical && formato === "9x16") {
    const topo = a.topo + a.altura * (painelCompacto ? INICIO_PAINEL_TELEFONE : 0.42);
    return (
      <>
        <TelaCheia corte={topo / alturaTela}>{tela(formato)}</TelaCheia>
        <div style={{ position: "absolute", left: a.esquerda, width: a.largura, top: topo, height: a.topo + a.altura - topo, display: "flex", flexDirection: "column", justifyContent: "flex-start", gap: t(20) }}>
          {painelCompacto ? (
            painelCompacto
          ) : trocaRodape === undefined ? (
            <>
              {painel}
              {rodape}
            </>
          ) : (
            <>
              <Fase de={0} ate={trocaRodape}>
                {painel}
              </Fase>
              <Fase de={trocaRodape}>{rodape}</Fase>
            </>
          )}
        </div>
      </>
    );
  }

  if (vertical) {
    const alturaAparelho = a.altura * 0.64;
    const tela0 = larguraDaTela(alturaAparelho, proporcao, t);
    return (
      <div style={{ position: "absolute", left: a.esquerda, top: a.topo, width: a.largura, height: a.altura, display: "flex", flexDirection: "column", gap: t(26) }}>
        <div style={{ display: "flex", gap: t(28), alignItems: "flex-start" }}>
          <Telefone largura={tela0} proporcao={proporcao} cor={cor}>
            {tela(formato)}
          </Telefone>
          <div style={{ flex: 1, minWidth: 0, height: alturaAparelho, display: "flex", flexDirection: "column" }}>{painel}</div>
        </div>
        {rodape}
      </div>
    );
  }

  const tela0 = larguraDaTela(a.altura, proporcao, t);
  return (
    <div style={{ position: "absolute", left: a.esquerda, top: a.topo, width: a.largura, height: a.altura, display: "flex", gap: t(44), alignItems: "flex-start" }}>
      <div style={{ width: larguraDoTelefone(tela0, t), flex: "none", marginLeft: t(24) }}>
        <Telefone largura={tela0} proporcao={proporcao} cor={cor}>
          {tela(formato)}
        </Telefone>
      </div>
      <div style={{ flex: 1, minWidth: 0, height: "100%", display: "flex", flexDirection: "column", gap: t(22) }}>
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>{painel}</div>
        {rodape}
      </div>
    </div>
  );
};
