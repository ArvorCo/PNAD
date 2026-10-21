// Componente único das sete cenas do capítulo 2 (CONTRATO.md, seção 7) e peças que as cenas dos
// capítulos 0 e 1 reaproveitam: fundo com reserva, cartão de lei legível, print de matéria na
// moldura do navegador. Arco de cada risco: o que é → caso real → sinal nos dados → o que o
// fiscal faz. A região de mídia (coluna esquerda no 16:9, metade de cima no 9:16) troca de fase
// na palavra dita; a coluna de cartões guarda o lugar de cada bloco desde o primeiro quadro.
import type { CSSProperties, PropsWithChildren, ReactNode } from "react";
import { AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import type { Cena, Gatilhos } from "../plano";
import { MIDIA } from "../dados";
import { useFormato } from "../formato";
import { COR, FONTE, MONO } from "../tema";
import type { Caso, Dados, Exemplo, IdRisco, Sinal } from "../tipos";
import { Chip } from "./Caixa";
import { CartaoCapitulo } from "./CartaoCapitulo";
import { CartaoSecao } from "./CartaoSecao";
import { Clipe } from "./Clipe";
import { temClipe } from "./ClipeSeHouver";
import { Contador } from "./Contador";
import { ehPendente, resolverMidia } from "./fonteMidia";
import { IconeCheck, IconeFiscal, IconeLei } from "./Icones";
import { MidiaAusente } from "./MidiaAusente";
import { Navegador, ALTURA_BARRA } from "./Navegador";
import { Area, Etiqueta, Fase, Surge, useArea } from "./Quadro";
import { ritmo } from "./ritmo";
import { Still } from "./Still";
import { mola, rampa, suave } from "./util";

// ------------------------------------------------------------------ utilitários de texto

/** "2020-11-29" → "29/11/2020". */
export const dataBr = (iso: string): string => {
  const [a, m, d] = iso.slice(0, 10).split("-");
  return d && m && a ? `${d}/${m}/${a}` : iso;
};

/** "Lei nº 9.504/1997" → "Lei 9.504/1997"; "Resolução TSE nº 23.751/2026" → "Res. TSE 23.751/2026". */
export const normaCurta = (norma: string): string => norma.replace("Resolução", "Res.").replace(/\s+nº\s+/g, " ");

/**
 * URL para a barra do navegador: sem protocolo nem "www.". Caminho com a palavra que o vídeo não
 * escreve (regra do roteiro) fica só com o domínio.
 */
export const urlCurta = (url: string): string => {
  const sem = url.replace(/^https?:\/\//, "").replace(/^www\./, "");
  return /fraud/i.test(sem) ? `${sem.split("/")[0]}/…` : sem;
};

/** "… Pena: reclusão até 4 anos e 5 a 15 dias-multa" → "pena: reclusão até 4 anos e 5 a 15 dias-multa". */
const penaDoResumo = (resumo: string): string | null => {
  const m = /Pena:\s*([^.;]+)/.exec(resumo);
  return m ? `pena: ${m[1].trim()}` : null;
};

/** "Fonte: SEDEP / Conjur, acesso em 06/10/2026" quando a data é de acesso; senão a data da matéria. */
export const linhaFonte = (f: Caso["fonte"]): string => `Fonte: ${f.veiculo}, ${f.data_e_acesso ? "acesso em " : ""}${dataBr(f.data)}`;

/** Parte de cima do print 9:16 que precisa aparecer inteira (a manchete fica no terço superior). */
const FRACAO_PRINT_VERTICAL = 0.45;

/** Cor do chip do sinal nos dados. */
export const COR_SINAL_RISCO: Record<Sinal, string> = { deixa: COR.outros, parcial: COR.ouro, nenhum: COR.alta };
const NOME_SINAL: Record<Sinal, string> = { deixa: "deixa sinal", parcial: "sinal parcial", nenhum: "nenhum sinal" };

// ------------------------------------------------------------------ fundo com reserva

/**
 * Fundo da cena: o primeiro id da lista que existe em disco (clipe em laço ou still com Ken
 * Burns), atenuado e com véu. Sem nenhum, o fundo da casa continua.
 */
export const RiscoFundo: React.FC<{ ids: readonly string[]; opacidade?: number; veu?: number }> = ({ ids, opacidade = 0.4, veu = 0.9 }) => {
  const { vertical } = useFormato();
  for (const id of ids) {
    if (MIDIA[id]?.tipo === "imagem") {
      if (!ehPendente(resolverMidia(id, vertical ? "9x16" : "16x9", "png"))) {
        return (
          <AbsoluteFill style={{ opacity: opacidade }}>
            <Still id={id} veu={veu} />
          </AbsoluteFill>
        );
      }
    } else if (temClipe(id, vertical)) {
      return (
        <AbsoluteFill style={{ opacity: opacidade }}>
          <Clipe id={id} fim="repetir" veu={veu} />
        </AbsoluteFill>
      );
    }
  }
  return null;
};

// ------------------------------------------------------------------ cartão de lei legível

export type ItemRiscoLei = { texto: string; referencia: string; q: number };

/**
 * Cartão de lei com corpo mínimo de 22 px no 16:9 e 28 px no 9:16 (o `Lei` compartilhado usa
 * 16 px na referência). Cada item entra na palavra dita e tem o lugar reservado desde o começo.
 */
export const RiscoLei: React.FC<{ titulo: string; itens: ItemRiscoLei[]; inicio: number; cor?: string; tamanho?: number; linhasReferencia?: number; style?: CSSProperties }> = ({
  titulo,
  itens,
  inicio,
  cor = COR.ouro,
  tamanho = 27,
  linhasReferencia = 2,
  style,
}) => {
  const { t, vertical } = useFormato();
  const k = vertical ? 1.18 : 1;
  return (
    <Surge inicio={inicio} style={style}>
      <div
        style={{
          background: "rgba(12,26,58,0.9)",
          border: `1px solid ${COR.linha}`,
          borderTop: `4px solid ${cor}`,
          borderRadius: 18,
          padding: `${t(18)}px ${t(24)}px`,
          boxShadow: "0 24px 70px rgba(0,0,0,0.45)",
          display: "flex",
          flexDirection: "column",
          gap: t(vertical ? 16 : 12),
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: t(12) }}>
          <IconeLei tamanho={t(34 * k)} cor={cor} />
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 28 : 22), letterSpacing: 3, color: cor }}>{titulo}</span>
        </div>
        {itens.map((item) => (
          <Surge key={item.texto + item.referencia} inicio={item.q} de="esquerda">
            <div style={{ display: "flex", gap: t(12), alignItems: "flex-start" }}>
              <IconeCheck tamanho={t(tamanho * k + 4)} cor={COR.outros} style={{ marginTop: t(2) }} />
              <div style={{ display: "flex", flexDirection: "column", gap: t(2), minWidth: 0 }}>
                <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(tamanho * k), lineHeight: 1.18, color: COR.tinta }}>{item.texto}</div>
                {linhasReferencia > 0 ? (
                <div
                  style={{
                    fontFamily: FONTE,
                    fontWeight: 500,
                    fontSize: t(vertical ? 28 : 22),
                    lineHeight: 1.22,
                    color: COR.suave,
                    display: "-webkit-box",
                    WebkitLineClamp: linhasReferencia,
                    WebkitBoxOrient: "vertical",
                    overflow: "hidden",
                  }}
                >
                  {item.referencia}
                </div>
                ) : null}
              </div>
            </div>
          </Surge>
        ))}
      </div>
    </Surge>
  );
};

// ------------------------------------------------------------------ print da matéria

/**
 * Print de matéria (`cap_materia_<caso>`) dentro da moldura do navegador, ancorado no topo (onde
 * está o título) com aproximação lenta. Sem print, o painel de mídia pendente mostra a URL.
 */
export const RiscoPrint: React.FC<{ caso: Caso; largura: number; altura: number; inicio: number }> = ({ caso, largura, altura, inicio }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const { vertical, t } = useFormato();
  const fonte = resolverMidia(`cap_materia_${caso.id}`, vertical ? "9x16" : "16x9", "png");
  const conteudo = Math.max(60, altura - t(ALTURA_BARRA));
  // Print de mesa (1920 px) numa moldura estreita: aproxima no miolo do topo, onde está o título.
  const base = !ehPendente(fonte) && fonte.formato === "16x9" ? 1.5 : 1;
  const zoom = base * (1 + 0.06 * rampa(frame, inicio, durationInFrames));
  return (
    <Navegador url={urlCurta(caso.fonte.url)} largura={largura} proporcao={largura / conteudo} cor={COR.alta}>
      {ehPendente(fonte) ? (
        <MidiaAusente motivo={caso.fonte.url} />
      ) : (
        fonte.formato === "9x16" && vertical ? (
          // Print de celular no 9:16: largura que garante os 45% de cima inteiros na altura dada,
          // centrado e recortado só por baixo, sem distorcer.
          <div style={{ position: "absolute", inset: 0, background: COR.papel, display: "flex", justifyContent: "center" }}>
            <Img
              src={staticFile(fonte.arquivo)}
              style={{
                width: Math.min(largura, conteudo / ((16 / 9) * FRACAO_PRINT_VERTICAL * zoom)),
                height: "auto",
                flex: "none",
                transform: `scale(${zoom})`,
                transformOrigin: "top center",
                boxShadow: "0 0 30px rgba(0,0,0,0.25)",
              }}
            />
          </div>
        ) : (
          <Img
            src={staticFile(fonte.arquivo)}
            style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: "top center", transform: `scale(${zoom})`, transformOrigin: "top center" }}
          />
        )
      )}
    </Navegador>
  );
};

// ------------------------------------------------------------------ cartões da coluna

/** Painel de vidro com título em mono e borda de cor; ocupa a altura que recebe. */
export const RiscoPainel: React.FC<PropsWithChildren<{ titulo: ReactNode; cor: string; style?: CSSProperties }>> = ({ titulo, cor, style, children }) => {
  const { t, vertical } = useFormato();
  return (
    <div
      style={{
        background: COR.vidro,
        border: `1px solid ${COR.linha}`,
        borderTop: `4px solid ${cor}`,
        borderRadius: 16,
        padding: `${t(18)}px ${t(24)}px`,
        boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
        display: "flex",
        flexDirection: "column",
        gap: t(vertical ? 14 : 10),
        overflow: "hidden",
        ...style,
      }}
    >
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 28 : 22), letterSpacing: 3, color: cor, display: "flex", alignItems: "center", gap: t(14), flexWrap: "wrap" }}>
        {titulo}
      </div>
      {children}
    </div>
  );
};

/** Texto que corta em `linhas` linhas com reticências (para nunca invadir o bloco de baixo). */
const Corte: React.FC<PropsWithChildren<{ linhas: number; tamanho: number; cor?: string; peso?: number }>> = ({ linhas, tamanho, cor = COR.tinta, peso = 500, children }) => (
  <div
    style={{
      fontFamily: FONTE,
      fontWeight: peso,
      fontSize: tamanho,
      lineHeight: 1.24,
      color: cor,
      display: "-webkit-box",
      WebkitLineClamp: linhas,
      WebkitBoxOrient: "vertical",
      overflow: "hidden",
      flex: "none",
    }}
  >
    {children}
  </div>
);

/** Cartão "o que o fiscal faz": verbos que entram na palavra e o fecho da postura. */
const CartaoFiscal: React.FC<{ q: number; itens: { texto: string; q: number }[]; fecho?: { texto: string; q: number } }> = ({ q, itens, fecho }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { t, vertical } = useFormato();
  const p = mola(frame, fps, q, { damping: 16 });
  const brilho = 1 - rampa(frame, q + 6, q + 40);
  return (
    <div
      style={{
        height: "100%",
        background: "linear-gradient(160deg, rgba(14,58,70,0.94), rgba(6,18,40,0.94))",
        border: `2px solid ${COR.tealClaro}`,
        borderRadius: 22,
        padding: `${t(vertical ? 30 : 30)}px ${t(vertical ? 34 : 38)}px`,
        boxShadow: `0 0 ${70 * brilho + 20}px ${COR.tealClaro}${brilho > 0.05 ? "66" : "33"}, 0 30px 80px rgba(0,0,0,0.5)`,
        display: "flex",
        flexDirection: "column",
        gap: t(vertical ? 26 : 28),
        transform: `scale(${0.94 + 0.06 * p})`,
        opacity: Math.min(1, p * 1.5),
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: t(18) }}>
        <IconeFiscal tamanho={t(vertical ? 74 : 70)} cor={COR.tealClaro} />
        <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 32 : 30), letterSpacing: 4, color: COR.tealClaro }}>O QUE O FISCAL FAZ</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: t(vertical ? 20 : 22) }}>
        {itens.map((item) => (
          <Surge key={item.texto} inicio={item.q} de="esquerda">
            <div style={{ display: "flex", gap: t(16), alignItems: "flex-start" }}>
              <IconeCheck tamanho={t(vertical ? 48 : 48)} cor={COR.outros} style={{ marginTop: t(2) }} />
              <span style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 46 : 46), lineHeight: 1.1, color: COR.tinta }}>{item.texto}</span>
            </div>
          </Surge>
        ))}
      </div>
      {fecho ? (
        <Surge inicio={fecho.q} style={{ marginTop: "auto" }}>
          <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 36 : 32), lineHeight: 1.15, color: COR.ouro, borderTop: `1px solid ${COR.linha}`, paddingTop: t(14) }}>{fecho.texto}</div>
        </Surge>
      ) : null}
    </div>
  );
};

/** Selo grande do número do caso do Ministério da Justiça, sobre o print. */
const SeloMj: React.FC<{ valor: number; rotulo: string; q: number }> = ({ valor, rotulo, q }) => {
  const { t, vertical } = useFormato();
  return (
    <Surge inicio={q} de="zoom">
      <div
        style={{
          background: "rgba(6,11,26,0.94)",
          border: `2px solid ${COR.ouro}`,
          borderRadius: 16,
          padding: `${t(14)}px ${t(22)}px`,
          boxShadow: "0 20px 60px rgba(0,0,0,0.6)",
          display: "flex",
          alignItems: "center",
          gap: t(18),
        }}
      >
        <Contador valor={valor} inicio={q} duracao={30} tamanho={t(vertical ? 84 : 76)} cor={COR.ouro} />
        <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 30 : 26), lineHeight: 1.15, color: COR.tinta, maxWidth: t(vertical ? 560 : 430) }}>{rotulo}</div>
      </div>
    </Surge>
  );
};

// ------------------------------------------------------------------ o componente Risco

type Fazer = { texto: string; gatilho: string };

export type RiscoProps = {
  cena: Cena;
  dados: Dados;
  g: Gatilhos;
  id: IdRisco;
  /** Uma frase curta da narração que diz o que é o risco. */
  oQueE: string;
  /** Resumo do sinal nos dados, com as palavras da narração. */
  sinalResumo: string;
  /** Ids de fundo em ordem de preferência (o primeiro que existir em disco). */
  fundo: readonly string[];
  /** Verbos do fiscal; cada um entra no gatilho de nome `gatilho`. */
  fazer: readonly Fazer[];
  /** Frase de postura que fecha o cartão do fiscal (gatilho `fecho`). */
  fecho?: string;
  /** Número do balanço do Ministério da Justiça (gatilho `mj`). */
  mj?: { valor: number; rotulo: string };
  /** Seção real citada na narração (gatilho `secao`). */
  secao?: Exemplo;
  /** Etiquetas ao lado da seção (comparecimento etc.), na ordem em que entram depois de `secao`. */
  etiquetasSecao?: readonly string[];
  /** Casos seguintes da lista citados na narração: índice em `casos` e gatilho de entrada. */
  extras?: readonly { indice: number; gatilho: string }[];
  /** Título no lugar de `nome` quando o nome do cenário não é o que a narração diz. */
  titulo?: string;
};

/**
 * Uma cena de risco. Gatilhos lidos de `g`: `caso`, `sinal`, `lei`, `fiscal`, mais `mj`,
 * `secao`, `fecho` e os de cada verbo, quando a cena os declara.
 */
export const Risco: React.FC<RiscoProps> = ({ cena, dados, g: gBruto, id, oQueE, sinalResumo, fundo, fazer, fecho, mj, secao, etiquetasSecao = [], extras = [], titulo: tituloProprio }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical, t } = useFormato();
  const area = useArea();
  const g = ritmo(cena, gBruto);
  const indice = dados.riscos.findIndex((r) => r.id === id);
  const risco = dados.riscos[indice];
  if (!risco) {
    return null;
  }
  const caso = risco.casos[0];
  const q = (nome: string, reserva: number): number => g[nome] ?? reserva;
  const qCaso = q("caso", 60);
  const qSinal = q("sinal", 300);
  const qLei = q("lei", qSinal);
  const qFiscal = q("fiscal", cena.frames - 150);
  const qSecao = secao ? q("secao", qFiscal) : qFiscal;
  const corSinal = COR_SINAL_RISCO[risco.sinal];
  const resultado = caso.resultado_curto ?? (caso as Caso & { resultado?: string }).resultado ?? caso.rotulo_curto;

  // Dimensões da região de mídia.
  const gap = t(vertical ? 18 : 30);
  const cabecalho = t(vertical ? 168 : 70);
  const larguraMidia = vertical ? area.largura : Math.round(((area.largura - gap) * 1.1) / 2.1);
  // No 9:16 o print fica alto enquanto o caso é narrado (45% de cima da página, com a manchete) e
  // encolhe no sinal, quando os cartões de baixo precisam do lugar.
  const alturaPrintAlto = t(ALTURA_BARRA) + Math.round(larguraMidia * (16 / 9) * FRACAO_PRINT_VERTICAL);
  const alturaCompacta = Math.round(area.altura * 0.37);
  const alturaMidia = vertical
    ? Math.round(alturaPrintAlto + (alturaCompacta - alturaPrintAlto) * suave(rampa(frame, qSinal, qSinal + 20)))
    : area.altura - cabecalho - gap;
  const alturaChips = t(54);
  const alturaNavegador = vertical ? alturaMidia : alturaMidia - alturaChips - t(12);

  const entradaCab = mola(frame, fps, 0, { damping: 16 });
  const titulo = (
    <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", alignItems: vertical ? "flex-start" : "center", gap: t(vertical ? 12 : 22), height: cabecalho, opacity: entradaCab, transform: `translateX(${(1 - entradaCab) * -40}px)` }}>
      <div style={{ display: "flex", alignItems: "center", gap: t(14), flex: "none" }}>
        <Chip cor={COR.alta} solido tamanho={vertical ? 26 : 22}>
          risco {indice + 1} de {dados.riscos.length}
        </Chip>
        <div style={{ display: "flex", gap: t(6) }}>
          {dados.riscos.map((r, i) => (
            <div key={r.id} style={{ width: t(14), height: t(14), borderRadius: t(4), background: i <= indice ? COR.alta : "rgba(255,255,255,0.14)", opacity: i === indice ? 1 : 0.7 }} />
          ))}
        </div>
      </div>
      <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 54 : 50), lineHeight: 1.04, letterSpacing: -1, color: COR.tinta, textWrap: "balance" }}>{tituloProprio ?? risco.nome}</div>
    </div>
  );

  const camada: CSSProperties = { position: "absolute", inset: 0, display: "flex", flexDirection: "column" };

  const regiaoMidia = (
    <div style={{ position: "relative", width: larguraMidia, height: alturaMidia, flex: "none" }}>
      <Fase de={0} ate={qCaso} style={{ ...camada, justifyContent: "center" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: t(16), padding: `${t(28)}px ${t(34)}px`, borderLeft: `6px solid ${COR.alta}`, background: "rgba(6,11,26,0.55)", borderRadius: 16 }}>
          <span style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 28 : 24), letterSpacing: 4, color: COR.alta }}>O QUE É</span>
          <div style={{ fontFamily: FONTE, fontWeight: 700, fontSize: t(vertical ? 58 : 52), lineHeight: 1.1, letterSpacing: -1, color: COR.tinta, textWrap: "balance" }}>{oQueE}</div>
        </div>
      </Fase>
      <Fase de={qCaso} ate={secao ? qSecao : qFiscal} style={{ ...camada, gap: t(12) }}>
        <div style={{ position: "relative" }}>
          <RiscoPrint caso={caso} largura={larguraMidia} altura={alturaNavegador} inicio={qCaso} />
          {mj ? (
            <div style={{ position: "absolute", inset: 0, background: "rgba(6,11,26,0.7)", opacity: rampa(frame, q("mj", qSinal), q("mj", qSinal) + 12), borderRadius: t(16) }} />
          ) : null}
          {mj ? (
            <div style={vertical ? { position: "absolute", left: t(18), right: t(18), top: t(ALTURA_BARRA) + t(18) } : { position: "absolute", right: t(18), bottom: t(18) }}>
              <SeloMj valor={mj.valor} rotulo={mj.rotulo} q={q("mj", qSinal)} />
            </div>
          ) : null}
        </div>
        <div
          style={
            vertical
              ? { position: "absolute", left: 0, right: 0, bottom: 0, display: "flex", flexDirection: "column", gap: t(8), padding: `${t(40)}px ${t(18)}px ${t(16)}px`, background: "linear-gradient(180deg, rgba(6,11,26,0) 0%, rgba(6,11,26,0.92) 40%)", borderRadius: `0 0 ${t(16)}px ${t(16)}px` }
              : { display: "flex", gap: t(12), alignItems: "center", flexWrap: "wrap", height: alturaChips, overflow: "hidden" }
          }
        >
          <div style={{ display: "flex", gap: t(12), alignItems: "center", flexWrap: "wrap" }}>
          <Chip cor={COR.ouro} solido tamanho={vertical ? 28 : 24}>
            {String(caso.ano)}
          </Chip>
          <Chip cor={COR.tealClaro} tamanho={vertical ? 26 : 22}>
            {caso.local}
          </Chip>
          {extras.map(({ indice: i, gatilho }) => {
            const outro = risco.casos[i];
            return outro ? (
              <Surge key={outro.id} inicio={q(gatilho, qSinal)} de="direita">
                <Etiqueta cor={COR.ouro} tamanho={22}>
                  {outro.ano} · {outro.rotulo_curto}
                </Etiqueta>
              </Surge>
            ) : null;
          })}
          </div>
          {vertical ? <div style={{ fontFamily: FONTE, fontWeight: 500, fontSize: t(28), color: COR.tinta }}>{linhaFonte(caso.fonte)}</div> : null}
        </div>
      </Fase>
      {secao ? (
        <Fase de={qSecao} ate={qFiscal} style={{ ...camada, justifyContent: "center", gap: t(16) }}>
          <CartaoSecao exemplo={secao} inicio={qSecao} />
          <div style={{ display: "flex", gap: t(12), flexWrap: "wrap" }}>
            {etiquetasSecao.map((e, i) => (
              <Surge key={e} inicio={qSecao + 16 + i * 10}>
                <Etiqueta cor={COR.ouro} tamanho={24}>
                  {e}
                </Etiqueta>
              </Surge>
            ))}
          </div>
        </Fase>
      ) : null}
      <Fase de={qFiscal} style={camada}>
        <CartaoFiscal q={qFiscal} itens={fazer.map((f) => ({ texto: f.texto, q: q(f.gatilho, qFiscal) }))} fecho={fecho ? { texto: fecho, q: q("fecho", cena.frames - 60) } : undefined} />
      </Fase>
    </div>
  );

  const tamanhoCorpo = t(vertical ? 30 : 26);
  const cartaoCaso = (
    <RiscoPainel titulo={<>O CASO · {caso.ano}</>} cor={COR.ouro} style={{ height: "100%" }}>
      <Corte linhas={2} tamanho={t(vertical ? 32 : 30)} peso={700}>
        {caso.titulo}
      </Corte>
      {vertical ? null : (
        <>
          <Corte linhas={4} tamanho={tamanhoCorpo} cor={COR.suave}>
            {resultado}
          </Corte>
          <div style={{ marginTop: "auto", flex: "none", fontFamily: FONTE, fontSize: t(22), color: COR.suave }}>{linhaFonte(caso.fonte)}</div>
        </>
      )}
    </RiscoPainel>
  );

  const cartaoSinal = (
    <RiscoPainel
      cor={corSinal}
      style={{ height: "100%" }}
      titulo={
        <>
          SINAL NOS DADOS
          <Chip cor={corSinal} solido tamanho={vertical ? 26 : 22}>
            {NOME_SINAL[risco.sinal]}
          </Chip>
        </>
      }
    >
      <Corte linhas={vertical ? 2 : 3} tamanho={t(vertical ? 34 : 30)} peso={700}>
        {sinalResumo}
      </Corte>
      <div style={{ fontFamily: MONO, fontWeight: 700, fontSize: t(vertical ? 28 : 22), letterSpacing: 3, color: COR.suave, marginTop: t(6) }}>COMO APARECE NO DIA</div>
      <Corte linhas={vertical ? 2 : 3} tamanho={tamanhoCorpo} cor={COR.suave}>
        {risco.como_aparece}
      </Corte>
    </RiscoPainel>
  );

  const itensLei: ItemRiscoLei[] = risco.lei.map((l, i) => ({
    texto: `${normaCurta(l.norma)}, ${l.dispositivo}`,
    referencia: l.pena ? `pena: ${l.pena}` : penaDoResumo(l.resumo) ?? l.resumo.split(/[.:;]/)[0],
    q: qLei + i * 10,
  }));

  const colunaCartoes = (
    <div style={{ display: "flex", flexDirection: "column", gap, flex: 1, minHeight: 0, minWidth: 0 }}>
      <div style={{ position: "relative", flex: 1, minHeight: 0 }}>
        <Fase de={qCaso} ate={qSinal} style={camada}>
          {cartaoCaso}
        </Fase>
        <Fase de={qSinal} style={camada}>
          {cartaoSinal}
        </Fase>
      </div>
      <RiscoLei
        titulo="A LEI"
        itens={itensLei}
        inicio={qLei}
        tamanho={vertical ? 24 : risco.lei.length > 2 ? 24 : 26}
        linhasReferencia={vertical ? 0 : risco.lei.length > 2 ? 1 : 2}
      />
    </div>
  );

  return (
    <>
      <RiscoFundo ids={fundo} opacidade={0.38} />
      <Area style={{ gap }}>
        {titulo}
        <div style={{ display: "flex", flexDirection: vertical ? "column" : "row", gap, flex: 1, minHeight: 0 }}>
          {regiaoMidia}
          {colunaCartoes}
        </div>
      </Area>
    </>
  );
};

// ------------------------------------------------------------------ cartão de capítulo com fundo

/** Cartão de capítulo (`CartaoCapitulo`) sobre o still da seção vazia, para o capítulo dos riscos. */
export const RiscoCapitulo: React.FC<React.ComponentProps<typeof CartaoCapitulo>> = (props) => (
  <>
    <RiscoFundo ids={["secao_vazia"]} opacidade={0.5} veu={0.9} />
    <CartaoCapitulo {...props} />
  </>
);
