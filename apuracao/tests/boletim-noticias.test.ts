// Manchetes do boletim: leitura de RSS (UTF-8 e ISO-8859-1), janela, filtro, deduplicação e corte.
import { describe, expect, test } from "bun:test";
import { blocoPrompt, buscarNoticias, daEleicao, decodificarXml, inicioDoDiaBrt, lerRss, normalizar, selecionar } from "../src/boletim/noticias.ts";

const AGORA = Date.parse("2026-10-25T20:00:00.000Z"); // 17:00 de Brasília

const item = (titulo: string, pub: string, fonte?: string): string =>
  `<item><title><![CDATA[${titulo}]]></title><link>https://exemplo.com/${encodeURIComponent(titulo)}</link><pubDate>${pub}</pubDate>${fonte ? `<source url="https://x">${fonte}</source>` : ""}</item>`;

const rss = (itens: string[], enc = "UTF-8"): string => `<?xml version="1.0" encoding="${enc}"?><rss version="2.0"><channel><title>t</title>${itens.join("")}</channel></rss>`;

describe("leitura", () => {
  test("título, link, data, fonte e entidades", () => {
    const x = rss([`<item><title>TSE &#8220;n&atilde;o&#8221; muda hor&#225;rio &amp; urna</title><link>https://a</link><pubDate>Sun, 25 Oct 2026 19:30:00 +0000</pubDate><source url="https://g1">G1</source></item>`]);
    const [i] = lerRss(x);
    expect(i?.titulo).toBe("TSE “não” muda horário & urna");
    expect(i?.fonte).toBe("G1");
    expect(i?.link).toBe("https://a");
  });

  test("feed em ISO-8859-1 (Folha) sai com acento certo", () => {
    const texto = rss([item("Justiça Eleitoral garante transporte em Valença", "25 Oct 2026 15:33:00 -0300")], "ISO-8859-1");
    const bytes = Uint8Array.from([...texto].map(c => c.charCodeAt(0)));
    expect(lerRss(decodificarXml(bytes))[0]?.titulo).toBe("Justiça Eleitoral garante transporte em Valença");
  });

  test("filtro da eleição: siglas pelo texto original, sem confundir TRE com três", () => {
    expect(daEleicao("TRE-BA prende eleitor por boca de urna")).toBe(true);
    expect(daEleicao("Apuração começa às 17h")).toBe(true);
    expect(daEleicao("Lula vota em São Bernardo")).toBe(true);
    expect(daEleicao("2º turno: filas em Salvador")).toBe(true);
    expect(daEleicao("Três feridos em acidente na BR-116")).toBe(false);
    expect(daEleicao("Copom mantém juros")).toBe(false);
    expect(normalizar("Apuração, já! ")).toBe("apuracao ja");
  });
});

describe("seleção", () => {
  const porFeed = [
    {
      feed: "Google Notícias",
      itens: lerRss(rss([
        item("TSE troca urnas em Salvador - G1", "Sun, 25 Oct 2026 19:40:00 GMT", "G1"),
        item("Lula vota em São Bernardo - Folha", "Sun, 25 Oct 2026 14:00:00 GMT", "Folha"),
        item("Copom mantém juros - Valor", "Sun, 25 Oct 2026 19:50:00 GMT", "Valor"),
      ])),
    },
    {
      feed: "G1",
      itens: lerRss(rss([
        item("TSE troca urnas em Salvador", "Sun, 25 Oct 2026 19:41:00 -0000"),
        item("Eleitor é preso por transporte ilegal no Maranhão", "Sun, 25 Oct 2026 19:55:00 -0000"),
        item("Abstenção preocupa partidos", "Sun, 25 Oct 2026 16:59:00 -0000"),
      ])),
    },
  ];

  test("janela de 3 h, sufixo do Google, deduplicação, filtro, do mais novo e marca de nova", () => {
    const s = selecionar(porFeed, { agoraMs: AGORA, desdeMs: AGORA - 3 * 3600_000, anteriores: new Set(["eleitor e preso por transporte ilegal no maranhao"]) });
    expect(s.map(m => [m.hora_brt, m.veiculo, m.titulo, m.nova])).toEqual([
      ["16:55", "G1", "Eleitor é preso por transporte ilegal no Maranhão", false],
      ["16:40", "G1", "TSE troca urnas em Salvador", true],
    ]);
  });

  test("primeiro boletim pega o dia inteiro; limite de itens", () => {
    const s = selecionar(porFeed, { agoraMs: AGORA, desdeMs: inicioDoDiaBrt(AGORA), anteriores: new Set() });
    expect(s.map(m => m.titulo)).toContain("Lula vota em São Bernardo");
    expect(s.map(m => m.titulo)).toContain("Abstenção preocupa partidos");
    expect(selecionar(porFeed, { agoraMs: AGORA, desdeMs: inicioDoDiaBrt(AGORA), anteriores: new Set(), limite: 2 }).length).toBe(2);
    expect(inicioDoDiaBrt(AGORA)).toBe(Date.parse("2026-10-25T03:00:00.000Z"));
  });

  test("bloco do prompt e feed que falha não derruba", async () => {
    const srv = Bun.serve({
      hostname: "127.0.0.1",
      port: 0,
      fetch: req => (new URL(req.url).pathname === "/ok" ? new Response(rss([item("Apuração do 2º turno começa", "Sun, 25 Oct 2026 19:58:00 -0000")])) : new Response("x", { status: 403 })),
    });
    const base = srv.url.toString().replace(/\/$/, "");
    const n = await buscarNoticias({ agoraMs: AGORA, primeiro: false, anteriores: new Set(), feeds: [{ nome: "Ok", url: `${base}/ok` }, { nome: "Fora", url: `${base}/fora` }, { nome: "Morto", url: "http://127.0.0.1:9/nada" }], timeoutMs: 2000 });
    void srv.stop(true);
    expect(n.itens.map(m => m.titulo)).toEqual(["Apuração do 2º turno começa"]);
    expect(n.feeds.map(f => f.erro === null)).toEqual([true, false, false]);
    expect(blocoPrompt(n)).toBe("NOVA [16:58, Ok] Apuração do 2º turno começa");
    expect(blocoPrompt({ ...n, itens: [] })).toBeNull();
  });
});
