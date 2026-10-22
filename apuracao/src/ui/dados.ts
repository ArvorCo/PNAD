// Carregamento das necessidades das telas: busca na fonte, grava no store,
// deduplica requisições em voo e limita a 1 busca por segundo por chave.

import type { Fonte } from "./data/api.ts";
import { ler, partesDoCaminho } from "./state/store.ts";
import type { Store } from "./state/store.ts";
import type { EventoSse, Need, State } from "./state/types.ts";
import { chaveLotes, chaveMapa, chaveResultado, chaveSerie } from "./state/types.ts";

export function chaveNeed(n: Need): string {
  switch (n.tipo) {
    case "resultado":
      return `resultados.${chaveResultado(n.ele, n.cargo, n.abr)}`;
    case "mapa":
      return `mapas.${chaveMapa(n.ele, n.cargo, n.nivel, n.pai)}`;
    case "serie":
      return `series.${chaveSerie(n.ele, n.cargo, n.abr)}`;
    case "lotes":
      return `lotes.${chaveLotes(n.ele, n.cargo, n.abr)}`;
    case "estado":
      return "estado";
    case "anomalias":
      return "anomalias";
    case "doist":
      return `doist.${n.rota}`;
  }
}

/** Rotas /api/2t/* são mais pesadas no servidor: no máximo uma busca a cada 4 s. */
export const INTERVALO_DOIST_MS = 4000;
export const INTERVALO_PADRAO_MS = 1000;
export const intervaloDe = (n: Need): number => (n.tipo === "doist" ? INTERVALO_DOIST_MS : INTERVALO_PADRAO_MS);

/** O evento do SSE invalida esta necessidade? */
export function eventoAfeta(e: EventoSse, n: Need): boolean {
  // As rotas do 2º turno derivam de qualquer arquivo novo (resultado, -ab) e das anomalias gravadas.
  if (n.tipo === "doist") return e.kind === "resultado" || e.kind === "ab" || e.kind === "anomalia";
  if (e.kind === "estado" || e.kind === "config") return n.tipo === "estado";
  if (e.kind === "anomalia") return n.tipo === "anomalias";
  if (e.kind === "ab") {
    // Monitoramento (-ab) mudou: andamento por UF e, por garantia, os mapas abaixo dele.
    if (n.tipo === "estado") return true;
    if (n.tipo !== "mapa" || n.ele !== e.ele) return false;
    return e.abr === "br" ? n.pai === "br" : n.pai.startsWith(e.abr);
  }
  // estado.br sai do arquivo nacional de presidente ou, com ele parado, da soma das UFs:
  // qualquer UF de presidente também invalida estado e o resultado nacional.
  const ufPres = e.cargo === 1 && e.abr.length === 2 && e.abr !== "br";
  if (n.tipo === "estado") return e.cargo === 1 && (e.abr === "br" || ufPres);
  // Série e lotes nacionais também podem vir da soma das UFs (mesma regra de defasagem).
  if ((n.tipo === "resultado" || n.tipo === "serie" || n.tipo === "lotes") && n.abr === "br" && n.cargo === 1 && n.ele === e.ele && ufPres) return true;
  if (n.tipo === "resultado" || n.tipo === "serie" || n.tipo === "lotes") return n.ele === e.ele && n.cargo === e.cargo && n.abr === e.abr;
  if (n.tipo === "mapa") {
    if (n.ele !== e.ele || n.cargo !== e.cargo) return false;
    // Mapa de UFs muda com qualquer UF; mapa de municípios ou zonas, com abrangências abaixo do pai.
    return n.pai === "br" ? e.abr.length === 2 || e.abr === "br" : e.abr.startsWith(n.pai);
  }
  return false;
}

/** Compara por conteúdo (JSON); valor não serializável conta como diferente. */
export function mesmoConteudo(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a === undefined || b === undefined) return false;
  try {
    return JSON.stringify(a) === JSON.stringify(b);
  } catch {
    return false;
  }
}

function lerEstado(s: State, chave: string): unknown {
  return ler(s, partesDoCaminho(chave));
}

export interface Carregador {
  carregar(n: Need): void;
  carregarTodas(ns: readonly Need[]): void;
  trocarFonte(f: Fonte): void;
}

export function criarCarregador(store: Store, fonteInicial: Fonte, aoErro: (n: Need, e: unknown) => void): Carregador {
  let fonte = fonteInicial;
  const emVoo = new Set<string>();
  const ultimo = new Map<string, number>();
  const adiados = new Map<string, ReturnType<typeof setTimeout>>();

  const buscar = async (n: Need): Promise<unknown> => {
    switch (n.tipo) {
      case "resultado":
        return fonte.resultado({ ele: n.ele, cargo: n.cargo, abr: n.abr });
      case "mapa":
        return fonte.mapa({ ele: n.ele, cargo: n.cargo, nivel: n.nivel, pai: n.pai });
      case "serie":
        return fonte.serie({ ele: n.ele, cargo: n.cargo, abr: n.abr });
      case "lotes":
        return fonte.lotes({ ele: n.ele, cargo: n.cargo, abr: n.abr });
      case "estado":
        return fonte.estado();
      case "anomalias":
        return fonte.anomalias();
      case "doist":
        return fonte.doisT(n.rota);
    }
  };

  const executar = (n: Need): void => {
    const k = chaveNeed(n);
    if (emVoo.has(k)) return;
    emVoo.add(k);
    ultimo.set(k, performance.now());
    buscar(n)
      .then(v => {
        // Rotas do 2º turno e alertas chegam como objetos novos a cada leitura; sem mudança de
        // conteúdo o estado fica como está e as telas não redesenham à toa.
        if ((n.tipo === "doist" || n.tipo === "anomalias" || n.tipo === "lotes") && mesmoConteudo(lerEstado(store.get(), k), v)) return;
        store.patch(k, v);
        // Rota do 2º turno em erro ou pendente não prova que o servidor está vivo para o HUD.
        if (n.tipo === "doist") return;
        const r = store.get().rede;
        store.patch("rede", { ...r, ultimo_ok_em: Date.now() });
      })
      .catch(e => aoErro(n, e))
      .finally(() => emVoo.delete(k));
  };

  const carregar = (n: Need): void => {
    const k = chaveNeed(n);
    const desde = performance.now() - (ultimo.get(k) ?? -Infinity);
    const intervalo = intervaloDe(n);
    if (desde >= intervalo) {
      executar(n);
      return;
    }
    if (adiados.has(k)) return;
    adiados.set(
      k,
      setTimeout(() => {
        adiados.delete(k);
        executar(n);
      }, intervalo - desde),
    );
  };

  return {
    carregar,
    carregarTodas: ns => ns.forEach(carregar),
    trocarFonte(f) {
      fonte = f;
    },
  };
}
