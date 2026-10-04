// Contador animado: sobe do valor anterior ao novo em 900 ms (ease-out cúbico, rAF),
// formatando em pt-BR a cada quadro. Serve para votos e percentuais. Com movimento
// reduzido o valor salta direto. Quando o valor muda, aplica o sublinhado lime (.mudou).

export const DURACAO_CONTAGEM_MS = 900;

/** Ease-out cúbico: rápido no começo, assenta no fim. */
export const easeOutCubic = (t: number): number => {
  const x = Math.min(1, Math.max(0, t));
  return 1 - (1 - x) ** 3;
};

/** Valor do quadro no instante `decorrido` de uma contagem de `de` a `para`. */
export function quadro(de: number, para: number, decorrido: number, duracao = DURACAO_CONTAGEM_MS): number {
  if (duracao <= 0 || decorrido >= duracao) return para;
  return de + (para - de) * easeOutCubic(decorrido / duracao);
}

export interface Relogio {
  raf(cb: (t: number) => void): number;
  caf(id: number): void;
  agora(): number;
}

const relogioPadrao = (): Relogio => ({
  raf: cb => requestAnimationFrame(cb),
  caf: id => cancelAnimationFrame(id),
  agora: () => performance.now(),
});

export const movimentoReduzido = (): boolean =>
  typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

export interface Animador {
  /** Leva ao valor `alvo`; `animar = false` salta. Devolve true se o alvo mudou. */
  ir(alvo: number, animar?: boolean): boolean;
  /** Valor exibido agora. */
  atual(): number;
  alvo(): number;
  parar(): void;
}

/** Núcleo sem DOM: chama `aoQuadro` com o valor de cada quadro até chegar ao alvo. */
export function criarAnimador(
  aoQuadro: (valor: number) => void,
  o: { inicial?: number; duracao?: number; relogio?: Relogio; reduzido?: () => boolean } = {},
): Animador {
  const relogio = o.relogio ?? relogioPadrao();
  const duracao = o.duracao ?? DURACAO_CONTAGEM_MS;
  const reduzido = o.reduzido ?? movimentoReduzido;
  let mostrado = o.inicial ?? 0;
  let destino = mostrado;
  let origem = mostrado;
  let inicio = 0;
  let pedido: number | null = null;

  const passo = (): void => {
    const v = quadro(origem, destino, relogio.agora() - inicio, duracao);
    mostrado = v;
    aoQuadro(v);
    pedido = v === destino ? null : relogio.raf(passo);
  };

  return {
    ir(alvo, animar = true) {
      if (!Number.isFinite(alvo)) return false;
      const mudou = alvo !== destino;
      if (!mudou && pedido === null) return false;
      if (pedido !== null) relogio.caf(pedido);
      pedido = null;
      destino = alvo;
      if (!animar || reduzido() || duracao <= 0 || (origem === alvo && mostrado === alvo)) {
        mostrado = alvo;
        origem = alvo;
        aoQuadro(alvo);
        return mudou;
      }
      origem = mostrado;
      inicio = relogio.agora();
      pedido = relogio.raf(passo);
      return mudou;
    },
    atual: () => mostrado,
    alvo: () => destino,
    parar() {
      if (pedido !== null) relogio.caf(pedido);
      pedido = null;
    },
  };
}

export interface Contador {
  readonly el: HTMLElement;
  /** Define o valor. Na primeira chamada conta a partir de zero (se `contarDoZero`). */
  definir(valor: number, animar?: boolean): void;
  destroy(): void;
}

export interface OpcoesContador {
  formato: (x: number) => string;
  classe?: string;
  tag?: keyof HTMLElementTagNameMap;
  /** Primeira exibição conta de 0 até o valor (padrão true). */
  contarDoZero?: boolean;
  relogio?: Relogio;
}

export function criarContador(o: OpcoesContador): Contador {
  const el = document.createElement(o.tag ?? "span");
  el.className = `num contador${o.classe ? ` ${o.classe}` : ""}`;
  let primeiro = true;
  const animador = criarAnimador(v => {
    el.textContent = o.formato(v);
  }, o.relogio ? { relogio: o.relogio } : {});

  const sublinhar = (): void => {
    el.classList.remove("mudou");
    void el.offsetWidth; // reinicia a animação
    el.classList.add("mudou");
  };

  return {
    el,
    definir(valor, animar = true) {
      if (primeiro) {
        primeiro = false;
        const contar = (o.contarDoZero ?? true) && animar && valor !== 0;
        el.textContent = o.formato(contar ? 0 : valor);
        animador.ir(valor, contar);
        return;
      }
      if (animador.ir(valor, animar)) sublinhar();
    },
    destroy() {
      animador.parar();
    },
  };
}
