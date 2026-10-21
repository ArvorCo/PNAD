// Ponto único de leitura dos JSON gerados (CONTRATO.md, seções 3 a 6). Cada arquivo tem dono
// próprio (seção 8). O import é estático: `dados/sete_riscos.json` nasce como cópia exata de
// `dados/sete_riscos.placeholder.json` (esquema completo, valores zerados) para o projeto compilar
// antes do agente de dados, que o sobrescreve com `scripts/video-sete-riscos-dados.py`. Voz,
// mídia, capturas e música começam vazios pelo mesmo motivo.
import capturasJson from "./dados/capturas.json";
import midiaJson from "./dados/midia.json";
import musicaJson from "./dados/musica.json";
import dadosJson from "./dados/sete_riscos.json";
import vozJson from "./dados/voz.json";
import type { Capturas, Dados, Midia, Musica, Voz } from "./tipos";

export const DADOS = dadosJson as unknown as Dados;
export const VOZ = vozJson as unknown as Voz;
export const MIDIA = midiaJson as unknown as Midia;
export const CAPTURAS = capturasJson as unknown as Capturas;
export const MUSICA = musicaJson as unknown as Musica;
