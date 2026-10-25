// Catálogo das telas do 2º turno: título do palco, rótulo curto (diretor e HUD), atalho de
// teclado e palavras de busca (sem acento). Sem DOM: o telão, a busca e o diretor leem daqui.

export interface Tela2T {
  id: string;
  /** Título grande do palco (frase em caixa normal, sem travessão). */
  titulo: string;
  /** Rótulo curto, sem ambiguidade, para o diretor e o HUD. */
  rotulo: string;
  /** Texto do atalho, como aparece na busca e no diretor. */
  atalho: string;
  /** Sinônimos para a busca (tecla /). */
  busca: string;
}

export const TELAS_2T: readonly Tela2T[] = [
  { id: "regioes", titulo: "Regiões do Brasil", rotulo: "Regiões", atalho: "Shift+N", busca: "regioes norte nordeste centro oeste sudeste sul exterior duelo" },
  { id: "ufs", titulo: "UFs, as mais lentas primeiro", rotulo: "27 UFs, ranking de ritmo", atalho: "Shift+U", busca: "ufs estados ranking lentas ritmo parada" },
  { id: "atraso", titulo: "Quem está lerdo", rotulo: "Atraso contra o 1º turno", atalho: "Shift+D", busca: "atraso lerdo lento demora fecha por ultimo previsao" },
  { id: "abstencao", titulo: "Abstenção contra o 1º turno", rotulo: "Abstenção contra o 1º turno", atalho: "Shift+B", busca: "abstencao comparecimento faltou 1 turno mapa" },
  { id: "secoes", titulo: "Cadeia de tempos das seções", rotulo: "Seções, cadeia de tempos", atalho: "Shift+S", busca: "secoes encerramento emissao recebimento boletim urna amostra tardias" },
  { id: "pausas", titulo: "Pausas da noite", rotulo: "Pausas do arquivo", atalho: "Shift+P", busca: "pausas pausa travou parado versao nacional soma ufs" },
  { id: "gov-2t", titulo: "Governadores, 2º turno", rotulo: "Governadores, 6 UFs", atalho: "3 ou Shift+G", busca: "governadores governador acre amazonas distrito federal espirito santo rio grande do norte tocantins" },
  { id: "paralela", titulo: "Totalização paralela", rotulo: "Paralela por QR do BU", atalho: "Shift+T", busca: "paralela totalizacao qr bu boletim conferencia divergencia" },
  { id: "alertas", titulo: "Alertas da noite", rotulo: "Alertas", atalho: "Shift+L", busca: "alertas anomalias avisos eventos" },
  { id: "evolucao", titulo: "Evolução da noite", rotulo: "Evolução dos válidos", atalho: "Shift+E", busca: "evolucao curva ao longo da noite validos duelo regioes" },
  { id: "projecao", titulo: "Projeção do resultado final", rotulo: "Projeção estatística", atalho: "Shift+J", busca: "projecao previsao final tendencia estimativa oscilacao municipios faixa" },
];

export const IDS_2T: ReadonlySet<string> = new Set(TELAS_2T.map(t => t.id));

export const tituloDa2T = (id: string): string | undefined => TELAS_2T.find(t => t.id === id)?.titulo;
