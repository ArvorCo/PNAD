// Ponto único de leitura dos JSON gerados (CONTRATO.md, seções 3 a 6). Cada arquivo tem dono
// próprio (seção 8). O import é estático: `dados/apuracao_2t.json` nasce com o esquema completo
// e todos os blocos pendentes, para o projeto compilar antes do script de dados, que o
// sobrescreve com `scripts/video-apuracao-2t-dados.py`. Voz, mídia, capturas e música começam
// vazios pelo mesmo motivo.
import dadosJson from "./dados/apuracao_2t.json";
import capturasJson from "./dados/capturas.json";
import midiaJson from "./dados/midia.json";
import musicaJson from "./dados/musica.json";
import vozJson from "./dados/voz.json";
import type { Capturas, Dados, Midia, Musica, Voz } from "./tipos";

export const DADOS = dadosJson as unknown as Dados;
export const VOZ = vozJson as unknown as Voz;
export const MIDIA = midiaJson as unknown as Midia;
export const CAPTURAS = capturasJson as unknown as Capturas;
export const MUSICA = musicaJson as unknown as Musica;
