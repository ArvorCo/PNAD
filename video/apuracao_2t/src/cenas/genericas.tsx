// Cenas genéricas, parametrizadas por props: cartão de texto, número grande, série temporal, mapa
// de UF em cores, ranking e captura com zoom. Cada fábrica devolve o componente de uma cena do
// registro; os valores vêm de caminhos em `Dados` (`ref.ts`), então bloco ausente vira aviso de
// dado pendente na tela e o render segue.
import type { ComponentType } from "react";
import { Caixa, Chip, Entrada, Texto, Titulo } from "../componentes/Caixa";
import { Contador } from "../componentes/Contador";
import { corDivergente, corSequencial, NEUTRO_ESCALA } from "../componentes/escala";
import { MapaCores } from "../componentes/MapaCores";
import { Palco, Pilha } from "../componentes/Palco";
import { SerieGrafico, type Faixa, type Marca, type Serie } from "../componentes/SerieGrafico";
import { Tabela, type Coluna } from "../componentes/Tabela";
import { ROTULO, hhmmDe } from "../componentes/textos";
import { decimal } from "../componentes/util";
import { Zoom } from "../componentes/Zoom";
import type { Foco } from "../componentes/Clipe";
import { campoNumero, campoTexto, listaDe, numeroDe, tabelaDe, type RefNumero } from "../ref";
import { useFormato } from "../formato";
import { COR, MONO } from "../tema";
import type { CenaProps } from "./registro";

type Rotulo = keyof typeof ROTULO;

const Aviso: React.FC<{ caminho: string }> = ({ caminho }) => (
  <div
    style={{
      flex: 1,
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      gap: 10,
      border: `2px dashed ${COR.ouro}`,
      borderRadius: 16,
      background: "repeating-linear-gradient(135deg, rgba(240,200,107,0.06) 0 18px, rgba(6,11,26,0.6) 18px 36px)",
      fontFamily: MONO,
      color: COR.ouro,
      textAlign: "center",
      padding: 24,
    }}
  >
    <div style={{ fontSize: 20, letterSpacing: 3 }}>DADO PENDENTE</div>
    <div style={{ fontSize: 20, color: COR.tinta, wordBreak: "break-all" }}>{caminho}</div>
  </div>
);

const Cabecalho: React.FC<{ chip?: string; titulo?: string; cor: string }> = ({ chip, titulo, cor }) => {
  const { vertical } = useFormato();
  return (
    <Pilha gap={14}>
      {chip ? (
        <Entrada inicio={0} de="esquerda">
          <Chip cor={cor} tamanho={20}>
            {chip}
          </Chip>
        </Entrada>
      ) : null}
      {titulo ? (
        <Entrada inicio={5} de="esquerda">
          <Titulo tamanho={vertical ? 54 : 64}>{titulo}</Titulo>
        </Entrada>
      ) : null}
    </Pilha>
  );
};

const Rodape: React.FC<{ rotulo?: Rotulo }> = ({ rotulo }) =>
  rotulo ? (
    <Entrada inicio={16} de="baixo">
      <Texto tamanho={20} cor={COR.suave}>
        {ROTULO[rotulo]}
      </Texto>
    </Entrada>
  ) : null;

const quadroDe = (g: Record<string, number>, gatilho?: string): number | undefined => (gatilho === undefined ? undefined : g[gatilho]);

// ---------------------------------------------------------------- cartão de texto

export type PropsTexto = {
  chip?: string;
  titulo: string;
  subtitulo?: string;
  /** Linhas curtas que entram em sequência (as três frases da casa, por exemplo). */
  linhas?: readonly string[];
  cor?: string;
  rotulo?: Rotulo;
};

export const cenaTexto = (p: PropsTexto): ComponentType<CenaProps> => {
  const CenaTexto: React.FC<CenaProps> = () => {
    const { vertical } = useFormato();
    const cor = p.cor ?? COR.tealClaro;
    return (
      <Palco style={{ justifyContent: "center" }}>
        <Pilha gap={26} alinhar={vertical ? "center" : "flex-start"}>
          <Cabecalho chip={p.chip} cor={cor} />
          <Entrada inicio={6} de="baixo">
            <Titulo tamanho={vertical ? 80 : 104} style={{ textAlign: vertical ? "center" : "left" }}>
              {p.titulo}
            </Titulo>
          </Entrada>
          {p.subtitulo ? (
            <Entrada inicio={16} de="baixo">
              <Texto tamanho={34} cor={COR.suave}>
                {p.subtitulo}
              </Texto>
            </Entrada>
          ) : null}
          {(p.linhas ?? []).map((l, i) => (
            <Entrada key={l} inicio={26 + i * 22} de="esquerda">
              <Caixa cor={cor}>
                <Texto tamanho={30}>{l}</Texto>
              </Caixa>
            </Entrada>
          ))}
          <Rodape rotulo={p.rotulo} />
        </Pilha>
      </Palco>
    );
  };
  return CenaTexto;
};

// ---------------------------------------------------------------- número grande

export type NumeroRef = { rotulo: string; valor: RefNumero; casas?: number; prefixo?: string; sufixo?: string; cor?: string };

export type PropsNumero = {
  chip?: string;
  titulo?: string;
  principal: NumeroRef;
  secundarios?: NumeroRef[];
  rotulo?: Rotulo;
  cor?: string;
};

const caminhoDe = (r: RefNumero): string => (typeof r === "number" ? String(r) : r.dado);

export const cenaNumero = (p: PropsNumero): ComponentType<CenaProps> => {
  const CenaNumero: React.FC<CenaProps> = ({ dados, g }) => {
    const { vertical, t } = useFormato();
    const cor = p.cor ?? COR.tealClaro;
    const valorPrincipal = numeroDe(dados, p.principal.valor);
    return (
      <Palco>
        <Pilha gap={22} style={{ flex: 1 }}>
          <Cabecalho chip={p.chip} titulo={p.titulo} cor={cor} />
          <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: vertical ? "center" : "flex-start", gap: t(18) }}>
            {valorPrincipal === null ? (
              <Aviso caminho={caminhoDe(p.principal.valor)} />
            ) : (
              <>
                <Contador
                  valor={valorPrincipal}
                  inicio={8}
                  duracao={46}
                  casas={p.principal.casas ?? 0}
                  prefixo={p.principal.prefixo}
                  sufixo={p.principal.sufixo}
                  tamanho={t(vertical ? 190 : 250)}
                  cor={p.principal.cor ?? cor}
                />
                <Entrada inicio={14} de="baixo">
                  <Texto tamanho={36} cor={COR.suave}>
                    {p.principal.rotulo}
                  </Texto>
                </Entrada>
              </>
            )}
            <div style={{ display: "flex", flexWrap: "wrap", gap: t(40), marginTop: t(10) }}>
              {(p.secundarios ?? []).map((s, i) => {
                const v = numeroDe(dados, s.valor);
                return (
                  <Entrada key={s.rotulo} inicio={(g.secundarios ?? 24) + i * 10} de="baixo">
                    <div style={{ display: "flex", flexDirection: "column", gap: t(6) }}>
                      {v === null ? (
                        <Chip cor={COR.ouro} tamanho={16}>
                          pendente {caminhoDe(s.valor)}
                        </Chip>
                      ) : (
                        <Contador valor={v} inicio={(g.secundarios ?? 24) + i * 10} duracao={30} casas={s.casas ?? 0} prefixo={s.prefixo} sufixo={s.sufixo} tamanho={t(72)} cor={s.cor ?? COR.tinta} />
                      )}
                      <Texto tamanho={24} cor={COR.suave}>
                        {s.rotulo}
                      </Texto>
                    </div>
                  </Entrada>
                );
              })}
            </div>
          </div>
          <Rodape rotulo={p.rotulo} />
        </Pilha>
      </Palco>
    );
  };
  return CenaNumero;
};

// ---------------------------------------------------------------- série temporal

export type SerieRef = {
  nome: string;
  cor: string;
  /**
   * Caminho de uma lista de pares `[x, y]`, de objetos com `xCampo` e `yCampo` ou de uma tabela
   * `{ colunas, linhas }` (então `xCampo` e `yCampo` são nomes de coluna).
   */
  dado: string;
  xCampo?: string | number;
  yCampo?: string | number;
  tracejada?: boolean;
};

export type MarcaRef = { x: RefNumero; rotulo: string; cor?: string; gatilho?: string };
export type FaixaRef = { de: RefNumero; ate: RefNumero; rotulo: string; cor?: string; gatilho?: string };

export type PropsSerie = {
  chip?: string;
  titulo?: string;
  series: SerieRef[];
  /** Eixo x em minutos depois das 17:00 de Brasília (`hhmm`) ou em número puro. */
  x: { min: number; max: number; ticks: readonly number[]; formato: "hhmm" | "num" };
  y: { min: number; max: number; ticks: readonly number[]; sufixo?: string; casas?: number };
  marcas?: MarcaRef[];
  faixas?: FaixaRef[];
  rotulo?: Rotulo;
  cor?: string;
};

const pontoDe = (item: unknown, xc: string | number, yc: string | number): [number, number] | null => {
  if (Array.isArray(item)) {
    const x = item[Number(xc)];
    const y = item[Number(yc)];
    return typeof x === "number" && typeof y === "number" ? [x, y] : null;
  }
  const x = campoNumero(item, String(xc));
  const y = campoNumero(item, String(yc));
  return x === null || y === null ? null : [x, y];
};

const pontosDa = (dados: CenaProps["dados"], s: SerieRef): [number, number][] => {
  const tabela = tabelaDe(dados, s.dado);
  if (tabela) {
    const xi = tabela.colunas.indexOf(String(s.xCampo));
    const yi = tabela.colunas.indexOf(String(s.yCampo));
    return xi < 0 || yi < 0 ? [] : tabela.linhas.map((l) => pontoDe(l, xi, yi)).filter((x): x is [number, number] => x !== null);
  }
  const itens = listaDe(dados, s.dado) ?? [];
  return itens.map((i) => pontoDe(i, s.xCampo ?? 0, s.yCampo ?? 1)).filter((x): x is [number, number] => x !== null);
};

export const cenaSerie = (p: PropsSerie): ComponentType<CenaProps> => {
  const CenaSerie: React.FC<CenaProps> = ({ dados, g }) => {
    const cor = p.cor ?? COR.tealClaro;
    const series: Serie[] = [];
    const faltam: string[] = [];
    for (const s of p.series) {
      const pontos = pontosDa(dados, s);
      if (pontos.length < 2) {
        faltam.push(s.dado);
      } else {
        series.push({ nome: s.nome, cor: s.cor, pontos, tracejada: s.tracejada });
      }
    }
    const formatoX = p.x.formato === "hhmm" ? hhmmDe : (v: number): string => decimal(v, 0);
    const marcas: Marca[] = [];
    for (const m of p.marcas ?? []) {
      const x = numeroDe(dados, m.x);
      if (x !== null) {
        marcas.push({ x, rotulo: m.rotulo, cor: m.cor, quadro: quadroDe(g, m.gatilho) });
      }
    }
    const faixas: Faixa[] = [];
    for (const f of p.faixas ?? []) {
      const de = numeroDe(dados, f.de);
      const ate = numeroDe(dados, f.ate);
      if (de !== null && ate !== null) {
        faixas.push({ de, ate, rotulo: f.rotulo, cor: f.cor, quadro: quadroDe(g, f.gatilho) });
      }
    }
    return (
      <Palco>
        <Pilha gap={18} style={{ flex: 1 }}>
          <Cabecalho chip={p.chip} titulo={p.titulo} cor={cor} />
          <div style={{ flex: 1, minHeight: 0, display: "flex" }}>
            {faltam.length > 0 ? (
              <Aviso caminho={faltam.join(" | ")} />
            ) : (
              <SerieGrafico
                series={series}
                xMin={p.x.min}
                xMax={p.x.max}
                yMin={p.y.min}
                yMax={p.y.max}
                ticksX={p.x.ticks}
                ticksY={p.y.ticks}
                formatoX={formatoX}
                formatoY={(v) => `${decimal(v, p.y.casas ?? 0)}${p.y.sufixo ?? ""}`}
                inicio={10}
                duracao={100}
                marcas={marcas}
                faixas={faixas}
              />
            )}
          </div>
          <Rodape rotulo={p.rotulo} />
        </Pilha>
      </Palco>
    );
  };
  return CenaSerie;
};

// ---------------------------------------------------------------- mapa de UF em cores

export type PropsMapa = {
  chip?: string;
  titulo?: string;
  /** Caminho de uma lista de objetos com a sigla da UF e um valor. */
  dado: string;
  campoUf?: string;
  campoValor: string;
  escala: { tipo: "divergente"; dominio: number; baixa?: string; alta?: string } | { tipo: "sequencial"; min: number; max: number };
  legenda: { esquerda: string; direita: string };
  destaque?: string[];
  rotulo?: Rotulo;
  cor?: string;
};

export const cenaMapa = (p: PropsMapa): ComponentType<CenaProps> => {
  const CenaMapa: React.FC<CenaProps> = ({ dados }) => {
    const { vertical, t } = useFormato();
    const cor = p.cor ?? COR.tealClaro;
    const lista = listaDe(dados, p.dado);
    const cores: Record<string, string> = {};
    for (const item of lista ?? []) {
      const uf = campoTexto(item, p.campoUf ?? "uf");
      const v = campoNumero(item, p.campoValor);
      if (uf !== null && v !== null) {
        cores[uf] = p.escala.tipo === "divergente" ? corDivergente(v, p.escala.dominio, p.escala.baixa, p.escala.alta) : corSequencial(v, p.escala.min, p.escala.max);
      }
    }
    const vazio = Object.keys(cores).length === 0;
    return (
      <Palco>
        <Pilha gap={18} style={{ flex: 1 }}>
          <Cabecalho chip={p.chip} titulo={p.titulo} cor={cor} />
          <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: vertical ? "column" : "row", gap: t(30), alignItems: "center" }}>
            <div style={{ flex: 1, minHeight: 0, minWidth: 0, display: "flex", alignSelf: "stretch" }}>
              {vazio ? <Aviso caminho={`${p.dado}[].${p.campoValor}`} /> : <MapaCores mapa={dados.mapa} inicio={6} cores={cores} destaque={p.destaque} />}
            </div>
            <Entrada inicio={30} de="baixo">
              <div style={{ display: "flex", flexDirection: "column", gap: t(10), minWidth: t(260) }}>
                <div
                  style={{
                    height: t(18),
                    borderRadius: 9,
                    background:
                      p.escala.tipo === "divergente"
                        ? `linear-gradient(90deg, ${p.escala.baixa ?? COR.lula}, ${NEUTRO_ESCALA}, ${p.escala.alta ?? COR.flavio})`
                        : `linear-gradient(90deg, ${NEUTRO_ESCALA}, ${COR.tealClaro})`,
                  }}
                />
                <div style={{ display: "flex", justifyContent: "space-between", fontFamily: MONO, fontSize: t(18), color: COR.suave }}>
                  <span>{p.legenda.esquerda}</span>
                  <span>{p.legenda.direita}</span>
                </div>
              </div>
            </Entrada>
          </div>
          <Rodape rotulo={p.rotulo} />
        </Pilha>
      </Palco>
    );
  };
  return CenaMapa;
};

// ---------------------------------------------------------------- ranking

export type PropsRanking = {
  chip?: string;
  titulo?: string;
  dado: string;
  colunas: Coluna[];
  limite?: number;
  /** Ordena a lista por este campo numérico antes de cortar em `limite`. */
  ordenar?: { campo: string; ordem: "crescente" | "decrescente" };
  destaque?: string;
  rotulo?: Rotulo;
  cor?: string;
};

const ordenada = (lista: unknown[] | null, ordenar: PropsRanking["ordenar"]): unknown[] | null => {
  if (lista === null || !ordenar) {
    return lista;
  }
  const sinal = ordenar.ordem === "crescente" ? 1 : -1;
  const ultimo = sinal === 1 ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;
  const chave = (i: unknown): number => campoNumero(i, ordenar.campo) ?? ultimo;
  return [...lista].sort((a, b) => sinal * (chave(a) - chave(b)));
};

export const cenaRanking = (p: PropsRanking): ComponentType<CenaProps> => {
  const CenaRanking: React.FC<CenaProps> = ({ dados }) => {
    const cor = p.cor ?? COR.tealClaro;
    const lista = ordenada(listaDe(dados, p.dado), p.ordenar);
    return (
      <Palco>
        <Pilha gap={18} style={{ flex: 1 }}>
          <Cabecalho chip={p.chip} titulo={p.titulo} cor={cor} />
          <div style={{ flex: 1, minHeight: 0, display: "flex", overflow: "hidden" }}>
            {lista === null || lista.length === 0 ? <Aviso caminho={p.dado} /> : <Tabela colunas={p.colunas} linhas={lista.slice(0, p.limite ?? 8)} inicio={10} cor={cor} destaque={p.destaque} />}
          </div>
          <Rodape rotulo={p.rotulo} />
        </Pilha>
      </Palco>
    );
  };
  return CenaRanking;
};

// ---------------------------------------------------------------- captura com zoom

export type PropsCaptura = {
  chip?: string;
  titulo?: string;
  /** Id `cap_<id>` de `capturas.json`. */
  captura: string;
  nome?: string;
  video?: boolean;
  endereco?: string;
  foco?: Foco[];
  rotulo?: Rotulo;
  cor?: string;
};

export const cenaCaptura = (p: PropsCaptura): ComponentType<CenaProps> => {
  const CenaCaptura: React.FC<CenaProps> = () => {
    const cor = p.cor ?? COR.tealClaro;
    return (
      <Palco>
        <Pilha gap={18} style={{ flex: 1 }}>
          <Cabecalho chip={p.chip} titulo={p.titulo} cor={cor} />
          <div style={{ flex: 1, minHeight: 0, display: "flex", justifyContent: "center", alignItems: "center" }}>
            <Zoom id={p.captura} nome={p.nome} video={p.video} endereco={p.endereco} foco={p.foco} />
          </div>
          <Rodape rotulo={p.rotulo} />
        </Pilha>
      </Palco>
    );
  };
  return CenaCaptura;
};
