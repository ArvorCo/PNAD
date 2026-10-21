import { Sequence, useCurrentFrame, useVideoConfig } from "remotion";
import { Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Clipe } from "../componentes/Clipe";
import { FolhaPredioVertical, INICIO_PAINEL_MAPA, RECORTES_FICHA } from "../componentes/FolhaPredio";
import { focoDaGravacao, segundoDoStill } from "../componentes/Gravacao";
import { GradeSecoes } from "../componentes/GradeSecoes";
import { LayoutNavegador, useJanelaTelaCheia } from "../componentes/LayoutCaptura";
import { BarraUrl } from "../componentes/Navegador";
import { Etiqueta, Fase, Surge } from "../componentes/Quadro";
import { nomeProprio } from "../componentes/textos";
import { decimal, inteiro, mola, rampa } from "../componentes/util";
import { CAPTURAS } from "../dados";
import { useFormato } from "../formato";
import { FPS } from "../plano";
import { COR, FONTE, MONO } from "../tema";
import type { FormatoMidia, Predio } from "../tipos";
import type { CenaProps } from "./registro";

const PREDIO = "cap_mapa_predio_rj";
/** A busca por CEP de Bangu, quando a captura existir; senão a busca pela zona 233. */
const BUSCA = CAPTURAS.mapa_cep ? "cap_mapa_cep" : "cap_mapa_busca_rj";
const URL = "brasil.arvor.co/fiscais_mapa.html";
/** Botões de raio do mapa de fiscais, em km (linha reta). */
const RAIOS = [1, 2, 5, 10, 15, 20, 30, 50];

/** Barra Flávio × Lula do prédio no 1º turno (válidos), na ordem da casa. */
const VotoPredio: React.FC<{ predio: Predio; q: number }> = ({ predio, q }) => {
  const frame = useCurrentFrame();
  const { vertical, t } = useFormato();
  const p = rampa(frame, q, q + 24);
  const tam = vertical ? 28 : 22;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: t(6), opacity: rampa(frame, q, q + 8) }}>
      <span style={{ fontFamily: MONO, fontSize: t(tam), color: COR.suave, letterSpacing: 1 }}>1º turno no prédio</span>
      <div style={{ display: "flex", height: t(vertical ? 18 : 14), borderRadius: 7, overflow: "hidden", background: COR.linha }}>
        <div style={{ width: `${predio.flavio_pct * p}%`, background: COR.flavio }} />
        <div style={{ flex: 1 }} />
        <div style={{ width: `${predio.lula_pct * p}%`, background: COR.lula }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: FONTE, fontWeight: 700, fontSize: t(tam + 2) }}>
        <span style={{ color: COR.flavio }}>Flávio {decimal(predio.flavio_pct, 2)}%</span>
        <span style={{ color: COR.lula }}>Lula {decimal(predio.lula_pct, 2)}%</span>
      </div>
    </div>
  );
};

/** "Um fiscal para 21 seções é POUCO", com POUCO entrando na palavra. */
const Pouco: React.FC<{ secoes: number; q: number; qPouco: number }> = ({ secoes, q, qPouco }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const { vertical } = useFormato();
  const k = mola(frame, fps, qPouco, { damping: 10, stiffness: 170 });
  return (
    <Surge inicio={q} de="baixo">
      <Titulo tamanho={vertical ? 80 : 46}>
        Um fiscal para {inteiro(secoes)} seções é{" "}
        <span style={{ display: "inline-block", color: COR.alta, opacity: frame < qPouco ? 0 : 1, transform: `scale(${frame < qPouco ? 0.6 : 0.6 + 0.4 * k})`, transformOrigin: "left bottom" }}>
          POUCO.
        </span>
      </Titulo>
    </Surge>
  );
};

/**
 * Onde fiscalizar: o endereço do mapa de fiscais, a busca real (CEP, zona ou município, e o raio) e
 * a ficha da escola de Bangu, com as 21 seções no nível de atenção de cada uma e a frase do fiscal.
 */
export const MapaFiscais: React.FC<CenaProps> = ({ g, dados, cena }) => {
  const frame = useCurrentFrame();
  const { vertical, t } = useFormato();
  const predio = dados.predios[0];
  const janela = useJanelaTelaCheia(INICIO_PAINEL_MAPA);
  const recorte = RECORTES_FICHA[PREDIO];
  const alvo = predio.secoes?.find((s) => s.atencao === 3)?.secao ?? null;
  const troca = g.exemplo - 6;

  const tela = (formato: FormatoMidia | null) => {
    // A busca por CEP leva mais tempo que a fala: começa de modo que o resultado apareça pouco antes
    // do exemplo. A busca pela zona começa um pouco antes da digitação.
    const resultado = segundoDoStill(BUSCA, "resultado", formato) ?? 10.45;
    const inicioBusca =
      BUSCA === "cap_mapa_cep"
        ? Math.max(0, resultado - troca / FPS + 0.8)
        : Math.max(0, (segundoDoStill(BUSCA, "inicio", formato) ?? 3.4) - 1.2);
    const ficha = segundoDoStill(PREDIO, "ficha", formato) ?? 4.72;
    const inicioPredio = Math.max(0, ficha - 1.6);
    const relativo = (q: number) => q - troca;
    const predioTela =
      formato === "9x16" && recorte ? (
        <FolhaPredioVertical
          captura={PREDIO}
          janela={janela}
          inicioGravacao={inicioPredio}
          qSobe={relativo(g.bangu)}
          paradas={[
            { quadro: 0, linha: 0 },
            { quadro: relativo(g.uma - 10), linha: 0 },
            { quadro: relativo(g.uma + 20), linha: recorte.alvo[0] - 10 },
          ]}
          realces={[{ de: relativo(g.conferencia), linhas: recorte.alvo }]}
        />
      ) : (
        <Clipe
          id={PREDIO}
          inicio={inicioPredio}
          foco={focoDaGravacao(
            [
              { t: inicioPredio, x: 0.6, y: 0.4, escala: 1 },
              { t: ficha + 0.2, x: 0.6, y: 0.4, escala: 1.05 },
              { t: ficha + 1.2, x: 0.6, y: 0.15, escala: 1.6 },
            ],
            inicioPredio,
          )}
        />
      );
    return (
      <>
        <Sequence durationInFrames={troca + 8} layout="none">
          <Clipe id={BUSCA} inicio={inicioBusca} />
        </Sequence>
        <Sequence from={troca} durationInFrames={Math.max(1, cena.frames - troca)} layout="none">
          {predioTela}
        </Sequence>
      </>
    );
  };

  const tamEt = vertical ? 28 : 22;
  const busca = (
    <div style={{ display: "flex", flexDirection: "column", gap: t(vertical ? 18 : 16) }}>
      {/* No 16:9 a URL já está na barra do navegador: aqui vira etiqueta embaixo do título. */}
      {vertical ? <BarraUrl url={URL} inicio={g.abra} cor={COR.teal} tamanho={30} style={{ alignSelf: "flex-start", maxWidth: "100%" }} /> : null}
      <Entrada inicio={vertical ? g.busque : g.abra} de="esquerda">
        <Titulo tamanho={vertical ? 52 : 44}>Busque onde você vota</Titulo>
      </Entrada>
      {vertical ? null : (
        <Surge inicio={g.abra + 8}>
          <div style={{ alignSelf: "flex-start", display: "inline-block", maxWidth: "100%", fontFamily: MONO, fontWeight: 700, fontSize: t(22), color: COR.tinta, padding: `${t(6)}px ${t(12)}px`, borderRadius: 8, border: `2px solid ${COR.teal}`, background: "rgba(3,8,20,0.8)", whiteSpace: "nowrap", overflow: "hidden" }}>
            {URL}
          </div>
        </Surge>
      )}
      <div style={{ display: "flex", gap: t(10), flexWrap: "wrap" }}>
        <Surge inicio={g.cep}>
          <Etiqueta cor={COR.tealClaro} tamanho={tamEt}>
            CEP
          </Etiqueta>
        </Surge>
        <Surge inicio={g.zona}>
          <Etiqueta cor={COR.tealClaro} tamanho={tamEt}>
            zona
          </Etiqueta>
        </Surge>
        <Surge inicio={g.municipio}>
          <Etiqueta cor={COR.tealClaro} tamanho={tamEt}>
            município
          </Etiqueta>
        </Surge>
      </div>
      <div style={{ display: "flex", gap: t(8), flexWrap: "wrap" }}>
        {RAIOS.map((r, i) => {
          // Os oito botões entram em meio segundo, todos legíveis antes do "prédio por prédio".
          const q = g.raio + i * 2 - 6;
          const ativo = r === 2 && frame >= g.raio + 20;
          return (
            <div
              key={r}
              style={{
                opacity: rampa(frame, q, q + 6),
                fontFamily: MONO,
                fontWeight: 700,
                fontSize: t(vertical ? 28 : 22),
                padding: `${t(4)}px ${t(10)}px`,
                borderRadius: 8,
                border: `2px solid ${ativo ? COR.tinta : COR.linha}`,
                background: ativo ? COR.tinta : "rgba(6,11,26,0.6)",
                color: ativo ? COR.fundo0 : COR.tinta,
              }}
            >
              {r} km
            </div>
          );
        })}
      </div>
      <Surge inicio={g.predio}>
        <Texto tamanho={vertical ? 34 : 28} style={{ fontWeight: 700 }}>
          Prédio por prédio.
        </Texto>
      </Surge>
    </div>
  );

  const cabecalhoPredio = (
    <div style={{ display: "flex", flexDirection: "column", gap: t(8) }}>
      <div style={{ display: "flex", gap: t(10), flexWrap: "wrap" }}>
        <Chip cor={COR.teal} solido tamanho={vertical ? 26 : 20}>
          {predio.uf}
        </Chip>
        <Chip cor={COR.suave} tamanho={vertical ? 26 : 20}>
          zona {predio.zona}
        </Chip>
      </div>
      <Titulo tamanho={vertical ? 52 : 42}>
        {nomeProprio(predio.bairro)}, {predio.municipio}
      </Titulo>
      <div style={{ fontFamily: MONO, fontSize: t(vertical ? 28 : 22), color: COR.tealClaro, letterSpacing: 1 }}>{predio.local}</div>
    </div>
  );

  const contagens = (
    <div style={{ display: "flex", gap: t(10), flexWrap: "wrap" }}>
      <Surge inicio={g.secoes}>
        <Etiqueta cor={COR.tinta} solido tamanho={tamEt}>
          {inteiro(predio.secoes_total)} seções
        </Etiqueta>
      </Surge>
      <Surge inicio={g.aptos}>
        <Etiqueta cor={COR.tealClaro} tamanho={tamEt}>
          {inteiro(predio.aptos_total)} eleitores
        </Etiqueta>
      </Surge>
      <Surge inicio={g.conferencia}>
        <Etiqueta cor="#a77bff" tamanho={tamEt}>
          {inteiro(predio.por_atencao["3"])} em conferência do arquivo
        </Etiqueta>
      </Surge>
    </div>
  );

  const lista = (
    <Surge inicio={g.lista} de="baixo">
      <Etiqueta cor={COR.ouro} tamanho={tamEt}>
        lista de prioridade, não de acusação
      </Etiqueta>
    </Surge>
  );

  const painel = (
    <div style={{ display: "grid", height: "100%" }}>
      <Fase de={0} ate={troca} style={{ gridArea: "1 / 1" }}>
        {busca}
      </Fase>
      <Fase de={troca} style={{ gridArea: "1 / 1" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: t(16) }}>
          {cabecalhoPredio}
          {contagens}
          <GradeSecoes predio={predio} inicio={g.secoes + 4} largura={t(520)} colunas={7} ladoMaximo={62} destaque={alvo} qDestaque={g.conferencia} nivelAtivo={frame >= g.conferencia && frame < g.fiscal ? 3 : null} />
          <Fase de={g.aptos + 10} ate={g.fiscal - 4}>
            <VotoPredio predio={predio} q={g.aptos + 10} />
          </Fase>
          <Fase de={g.fiscal - 4}>
            <div style={{ display: "flex", flexDirection: "column", gap: t(14) }}>
              <Pouco secoes={predio.secoes_total} q={g.fiscal - 4} qPouco={g.pouco} />
              {lista}
            </div>
          </Fase>
        </div>
      </Fase>
    </div>
  );

  // Tela cheia do 9:16: o painel tem menos altura, então cada etapa ocupa o lugar da anterior.
  const painelCompacto = (
    <div style={{ display: "grid" }}>
      <Fase de={0} ate={troca} style={{ gridArea: "1 / 1" }}>
        {busca}
      </Fase>
      <Fase de={troca} ate={g.fiscal - 4} style={{ gridArea: "1 / 1" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: t(16) }}>
          {cabecalhoPredio}
          {contagens}
          <Fase de={g.aptos + 10}>
            <VotoPredio predio={predio} q={g.aptos + 10} />
          </Fase>
        </div>
      </Fase>
      <Fase de={g.fiscal - 4} style={{ gridArea: "1 / 1" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: t(22) }}>
          <Pouco secoes={predio.secoes_total} q={g.fiscal - 4} qPouco={g.pouco} />
          {lista}
        </div>
      </Fase>
    </div>
  );

  return (
    <LayoutNavegador
      id={PREDIO}
      url={URL}
      cor={COR.teal}
      tela={tela}
      painel={painel}
      painelCompacto={painelCompacto}
      larguraPainel={560}
      inicioPainel={INICIO_PAINEL_MAPA}
    />
  );
};
