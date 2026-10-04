// Carregamento das necessidades das telas: busca na fonte, grava no store,
// deduplica requisições em voo e limita a 1 busca por segundo por chave.

import type { Fonte } from "./data/api.ts";
import type { Store } from "./state/store.ts";
import type { EventoSse, Need } from "./state/types.ts";
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
  }
}

/** O evento do SSE invalida esta necessidade? */
export function eventoAfeta(e: EventoSse, n: Need): boolean {
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
  if (n.tipo === "resultado" && n.abr === "br" && n.cargo === 1 && n.ele === e.ele && ufPres) return true;
  if (n.tipo === "resultado" || n.tipo === "serie" || n.tipo === "lotes") return n.ele === e.ele && n.cargo === e.cargo && n.abr === e.abr;
  if (n.tipo === "mapa") {
    if (n.ele !== e.ele || n.cargo !== e.cargo) return false;
    // Mapa de UFs muda com qualquer UF; mapa de municípios ou zonas, com abrangências abaixo do pai.
    return n.pai === "br" ? e.abr.length === 2 || e.abr === "br" : e.abr.startsWith(n.pai);
  }
  return false;
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
  const INTERVALO = 1000;

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
    }
  };

  const executar = (n: Need): void => {
    const k = chaveNeed(n);
    if (emVoo.has(k)) return;
    emVoo.add(k);
    ultimo.set(k, performance.now());
    buscar(n)
      .then(v => {
        store.patch(k, v);
        const r = store.get().rede;
        store.patch("rede", { ...r, ultimo_ok_em: Date.now() });
      })
      .catch(e => aoErro(n, e))
      .finally(() => emVoo.delete(k));
  };

  const carregar = (n: Need): void => {
    const k = chaveNeed(n);
    const desde = performance.now() - (ultimo.get(k) ?? -Infinity);
    if (desde >= INTERVALO) {
      executar(n);
      return;
    }
    if (adiados.has(k)) return;
    adiados.set(
      k,
      setTimeout(() => {
        adiados.delete(k);
        executar(n);
      }, INTERVALO - desde),
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
