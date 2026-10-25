// Painel "Boletim" do diretor: lista dos boletins falados, gerar agora, tocar, parar e descartar.
// Lê /api/boletins a cada 2 s; comandos por POST (só de 127.0.0.1, com o cabeçalho da casa).

interface Item {
  id: string;
  hora: string;
  estado: "gerando" | "pronto" | "no_ar" | "tocado" | "erro" | "descartado";
  etapa: string | null;
  origem: string;
  modo: string | null;
  palavras: number | null;
  duracao_s: number | null;
  resumo: string | null;
  erro: string | null;
}

interface Lista {
  agora: string;
  gerador: { vivo: boolean; relogio_ligado?: boolean; proximo_ciclo_em?: string | null; gerando?: string | null; etapa?: string | null; ultimo_erro?: string | null };
  no_ar: { id: string; hora: string | null; desde: string; duracao_s: number | null; decorrido_s: number } | null;
  itens: Item[];
}

const ROTULO: Readonly<Record<Item["estado"], string>> = { gerando: "gerando", pronto: "pronto", no_ar: "no ar", tocado: "tocado", erro: "erro", descartado: "descartado" };
const ETAPA: Readonly<Record<string, string>> = { dados: "lendo os dados", roteiro: "escrevendo o roteiro", enxugar: "enxugando o roteiro", audio: "gerando o áudio" };

function el<K extends keyof HTMLElementTagNameMap>(tag: K, attrs: Record<string, string> = {}, texto = ""): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (texto) e.textContent = texto;
  return e;
}

const hora = (iso: string): string => new Date(iso).toLocaleTimeString("pt-BR", { timeZone: "America/Sao_Paulo", hour: "2-digit", minute: "2-digit" });
function mmss(s: number | null): string {
  if (s === null || !Number.isFinite(s)) return "-";
  const t = Math.max(0, Math.round(s));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}

async function post(caminho: string): Promise<string | null> {
  try {
    const r = await fetch(caminho, { method: "POST", headers: { "x-apuracao": "boletim" } });
    if (r.ok) return null;
    const j = (await r.json().catch(() => ({}))) as { erro?: string };
    return j.erro ?? `HTTP ${r.status}`;
  } catch (e) {
    return e instanceof Error ? e.message : String(e);
  }
}

export function criarPainelBoletim(): HTMLElement {
  const sec = el("section", { class: "boletim" });
  sec.append(el("h2", {}, "boletim falado"));
  const status = el("div", { class: "bol-status" });
  const noAr = el("div", { class: "bol-noar", "aria-live": "polite" });
  const acoes = el("div", { class: "controles" });
  const bGerar = el("button", { type: "button" }, "gerar agora");
  const bParar = el("button", { type: "button", class: "bol-parar" }, "parar");
  const msg = el("span", { class: "bol-msg", role: "status" });
  const todosRot = el("label", { class: "bol-todos" });
  const todos = el("input", { type: "checkbox" });
  todosRot.append(todos, "mostrar descartados");
  acoes.append(bGerar, bParar, todosRot, msg);
  const lista = el("ol", { class: "bol-lista" });
  sec.append(status, noAr, acoes, lista);

    let assinatura = "";
  const abertos = new Set<string>();

  const avisar = (texto: string, falhou: boolean): void => {
    msg.textContent = texto;
    msg.dataset.erro = falhou ? "1" : "0";
  };

  const acao = async (caminho: string, ok: string): Promise<void> => {
    const e = await post(caminho);
    avisar(e ? `falhou: ${e}` : ok, e !== null);
    await atualizar();
  };

  bGerar.addEventListener("click", () => void acao("/api/boletins/gerar", "pedido de geração enviado"));
  bParar.addEventListener("click", () => void acao("/api/boletins/parar", "boletim parado"));
  todos.addEventListener("change", () => {
    assinatura = "";
    void atualizar();
  });

  const linha = (it: Item): HTMLLIElement => {
    const li = el("li", { "data-estado": it.estado, "data-id": it.id });
    const cab = el("div", { class: "bol-cab" });
    cab.append(
      el("strong", { class: "bol-hora" }, it.hora),
      el("span", { class: "bol-estado" }, it.estado === "gerando" && it.etapa ? `${ROTULO[it.estado]}: ${ETAPA[it.etapa] ?? it.etapa}` : ROTULO[it.estado]),
      el("span", { class: "bol-num" }, `${mmss(it.duracao_s)} · ${it.palavras ?? 0} palavras${it.modo ? ` · ${it.modo}` : ""}${it.origem === "manual" ? " · manual" : ""}`),
    );
    const botoes = el("span", { class: "bol-botoes" });
    if (it.estado !== "gerando" && it.estado !== "erro") {
      const b = el("button", { type: "button", class: "bol-tocar" }, it.estado === "pronto" ? "tocar" : "tocar de novo");
      b.addEventListener("click", () => void acao(`/api/boletins/${it.id}/tocar`, `boletim das ${it.hora} no ar`));
      botoes.append(b);
    }
    if (it.estado !== "gerando") {
      const b = el("button", { type: "button", class: "bol-descartar" }, "descartar");
      b.addEventListener("click", () => {
        if (confirm(`Descartar o boletim das ${it.hora}?`)) void acao(`/api/boletins/${it.id}/descartar`, `boletim das ${it.hora} descartado`);
      });
      botoes.append(b);
    }
    cab.append(botoes);
    li.append(cab);
    li.append(el("p", { class: "bol-resumo" }, it.erro ? `erro: ${it.erro}` : (it.resumo ?? "")));
    if (it.estado !== "gerando" && it.estado !== "erro") {
      const det = el("details");
      if (abertos.has(it.id)) det.open = true;
      det.append(el("summary", {}, "roteiro e prévia do áudio"));
      const corpo = el("div", { class: "bol-corpo" });
      det.append(corpo);
      const carregar = async (): Promise<void> => {
        if (corpo.dataset.carregado === "1") return;
        corpo.dataset.carregado = "1";
        try {
          const r = await fetch(`/api/boletins/${it.id}`, { cache: "no-store" });
          const j = (await r.json()) as { texto: string | null; mp3: string | null };
          const audio = el("audio", { controls: "", preload: "none" });
          if (j.mp3) audio.src = j.mp3;
          corpo.replaceChildren(audio, el("pre", {}, j.texto ?? "(sem texto)"));
        } catch {
          corpo.textContent = "não foi possível ler o roteiro";
        }
      };
      det.addEventListener("toggle", () => {
        if (det.open) {
          abertos.add(it.id);
          void carregar();
        } else abertos.delete(it.id);
      });
      if (det.open) void carregar();
      li.append(det);
    }
    return li;
  };

  const desenhar = (l: Lista): void => {
    const g = l.gerador;
    const partes = [g.vivo ? "gerador no ar" : "gerador FORA DO AR (scripts/start-boletim.sh)"];
    if (g.vivo) partes.push(g.relogio_ligado ? (g.proximo_ciclo_em ? `próximo ciclo às ${hora(g.proximo_ciclo_em)}` : "relógio ligado") : "relógio desligado: só geração manual");
    if (g.gerando) partes.push(`gerando ${g.gerando}${g.etapa ? `: ${ETAPA[g.etapa] ?? g.etapa}` : ""}`);
    if (g.ultimo_erro) partes.push(`último erro: ${g.ultimo_erro}`);
    status.textContent = partes.join(" · ");
    status.dataset.vivo = g.vivo ? "1" : "0";
    bGerar.disabled = !g.vivo || Boolean(g.gerando);
    bParar.disabled = l.no_ar === null;
    noAr.textContent = l.no_ar ? `NO AR: boletim das ${l.no_ar.hora ?? l.no_ar.id}, ${mmss(l.no_ar.decorrido_s)} de ${mmss(l.no_ar.duracao_s)}` : "nada no ar";
    noAr.dataset.noar = l.no_ar ? "1" : "0";
    const sig = JSON.stringify(l.itens.map(i => [i.id, i.estado, i.etapa, i.palavras, i.duracao_s, i.resumo, i.erro]));
    if (sig === assinatura) return;
    assinatura = sig;
    lista.replaceChildren(...l.itens.map(linha));
    if (l.itens.length === 0) lista.append(el("li", { class: "bol-vazio" }, "nenhum boletim ainda"));
  };

  async function atualizar(): Promise<void> {
    try {
      const r = await fetch(todos.checked ? "/api/boletins?todos=1" : "/api/boletins", { cache: "no-store" });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      desenhar((await r.json()) as Lista);
    } catch (e) {
      status.textContent = `servidor sem resposta para /api/boletins (${e instanceof Error ? e.message : String(e)})`;
      status.dataset.vivo = "0";
    }
  }

  void atualizar();
  setInterval(() => void atualizar(), 2000);
  return sec;
}
