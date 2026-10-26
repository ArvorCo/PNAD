// Registro das cenas: qual componente desenha cada id da ordem, com gatilhos de fala, mídia usada
// e efeitos sonoros. `satisfies Record<CenaId, CenaDef>` faz o typecheck falhar se faltar cena.
// Caminhos conferidos em 25/10/2026 (22:45) contra os JSON do dossiê e contra o roteiro final;
// `tests/test_video_apuracao_2t.py` prova que cada `dado:` resolve. Gatilhos casados com a voz
// (palavra que dispara, reserva em segundos): o número secundário entra quando é dito.
import type { ComponentType } from "react";
import { CartaoCapitulo } from "../componentes/CartaoCapitulo";
import { TESE } from "../componentes/textos";
import type { CenaId } from "../ordem";
import type { Cena, Gatilhos } from "../plano";
import { COR } from "../tema";
import type { Dados } from "../tipos";
import { cenaCaptura, cenaMapa, cenaNumero, cenaRanking, cenaSerie, cenaTexto } from "./genericas";

export type CenaProps = { cena: Cena; dados: Dados; g: Gatilhos };

/** Nome do gatilho → [palavra que dispara, reserva em segundos se a palavra não for dita]. */
export type DefinicaoGatilhos = Record<string, readonly [palavra: string, reservaSegundos: number]>;

/** Efeito de `public/sfx/` tocado no início da cena ou no quadro de um gatilho. */
export type SfxCena = { arquivo: string; gatilho?: string; volume?: number };

export type CenaDef = {
  componente: ComponentType<CenaProps>;
  gatilhos?: DefinicaoGatilhos;
  /** Ids de `midia.json` (ou `cap_<id>` de `capturas.json`) usados pela cena; o teste confere. */
  midia?: string[];
  sfx?: SfxCena[];
};

/** Modo de coleta das pesquisas (`pesquisas_vs_urna.pesquisas[].modo`) em português corrente. */
const MODO_COLETA = { telefone: "telefone", presencial: "presencial", online: "online", misto: "misto", nao_informado: "não informado" } as const;

const CAP: CenaDef = { componente: CartaoCapitulo, gatilhos: { numero: ["Capítulo", 0.2] } };

/** Eixo x da noite: de 17:00 (0) a 22:30 (330 min) em Brasília. */
const EIXO_NOITE = { min: 0, max: 330, ticks: [0, 60, 120, 180, 240, 300], formato: "hhmm" } as const;
const EIXO_PST = { min: 0, max: 100, ticks: [0, 25, 50, 75, 100], sufixo: "%" } as const;
const SERIE_PST = { nome: "seções totalizadas", cor: COR.tealClaro, dado: "linha_do_tempo.nacional.serie", xCampo: "min", yCampo: "pst" } as const;

export const REGISTRO = {
  // 0 Abertura
  abertura: {
    componente: cenaNumero({
      chip: "25/10/2026 · 17:07:09 a 19:01:44",
      titulo: "O TSE parou de publicar",
      principal: { rotulo: "minutos sem nenhum arquivo novo, de nenhum tipo", valor: { dado: "linha_do_tempo.pausas.silencio_geral.minutos" }, casas: 1, cor: COR.alta },
      secundarios: [
        { rotulo: "leituras do nosso coletor no intervalo", valor: { dado: "linha_do_tempo.pausas.silencio_geral.leituras_no_intervalo" } },
        { rotulo: "versões geradas dentro do intervalo", valor: { dado: "linha_do_tempo.pausas.silencio_geral.versoes_geradas_dentro" } },
      ],
      rotulo: "pausa",
      cor: COR.tealClaro,
    }),
    gatilhos: { secundarios: ["coletor", 9] },
    sfx: [{ arquivo: "tique.mp3", volume: 0.6 }],
  },
  tese: {
    componente: cenaTexto({
      chip: "tese",
      titulo: TESE,
      linhas: ["Não comemoramos o resultado. Comemoramos o método.", "O que a urna registrou e o que falta explicar."],
      cor: COR.ouro,
    }),
  },
  // 1 A noite minuto a minuto. Eixo x das séries: minutos depois das 17:00 de Brasília.
  "cap-noite": CAP,
  "noite-stf": {
    componente: cenaTexto({
      chip: "a prorrogação, pelas fontes da noite",
      titulo: "STF, Reclamação 101673",
      linhas: [
        "17:01 · PGE opina por manter o fim às 17h (Estadão)",
        "17:03 · Zanin prorroga a votação até 19h (STF)",
        "17:49 · TSE avisa as seções (Poder360)",
        "18:08 · vale só onde a seção seguia aberta (Agência Brasil)",
        "18:17 · TRE-SP recebe o aviso; mais de 80% fechadas (Agência Brasil)",
      ],
      cor: COR.ouro,
    }),
    sfx: [{ arquivo: "papel.mp3", volume: 0.5 }],
  },
  "noite-parada": {
    componente: cenaSerie({
      chip: "intervalo sem versão nova publicada",
      series: [SERIE_PST],
      x: EIXO_NOITE,
      y: EIXO_PST,
      faixas: [{ de: { dado: "linha_do_tempo.pausas.parada_geral.de_min" }, ate: { dado: "linha_do_tempo.pausas.parada_geral.ate_min" }, rotulo: "sem versão nova", cor: COR.alta, gatilho: "faixa" }],
      rotulo: "pausa",
      cor: COR.flavio,
    }),
    gatilhos: { faixa: ["silêncio", 2] },
  },
  "noite-virada": {
    componente: cenaSerie({
      chip: "Flávio × Lula nos votos válidos, contagem observada",
      series: [
        { nome: "Flávio", cor: COR.flavio, dado: "linha_do_tempo.nacional.serie", xCampo: "min", yCampo: "pct_flavio" },
        { nome: "Lula", cor: COR.lula, dado: "linha_do_tempo.nacional.serie", xCampo: "min", yCampo: "pct_lula" },
      ],
      x: { min: 125, max: 330, ticks: [150, 210, 270, 330], formato: "hhmm" },
      y: { min: 44, max: 56, ticks: [44, 47, 50, 53, 56], sufixo: "%" },
      // 19:50 e 20:25 (`projecao_noite.pontos_com_flavio_a_frente_no_observado`), em minutos depois das 17:00.
      faixas: [{ de: 170, ate: 205, rotulo: "Flávio à frente na contagem", cor: COR.flavio, gatilho: "faixa" }],
      cor: COR.flavio,
    }),
    gatilhos: { faixa: ["Flávio", 3] },
  },
  "noite-fim": {
    componente: cenaNumero({
      chip: "resultado na última versão do dossiê",
      principal: { rotulo: "Lula nos votos válidos", valor: { dado: "presidente.nacional.pct_lula" }, casas: 2, sufixo: "%", cor: COR.lula },
      secundarios: [
        { rotulo: "Flávio nos votos válidos", valor: { dado: "presidente.nacional.pct_flavio" }, casas: 2, sufixo: "%", cor: COR.flavio },
        { rotulo: "votos de diferença", valor: { dado: "presidente.nacional.margem_lula_votos" } },
        { rotulo: "votos de diferença no Norte", valor: { dado: "presidente.regioes[0].margem_lula_votos" }, cor: COR.ouro },
      ],
      cor: COR.flavio,
    }),
    gatilhos: { secundarios: ["Flávio", 8] },
  },
  // 2 A projeção
  "cap-projecao": CAP,
  "proj-primeiro-ponto": {
    componente: cenaNumero({
      chip: "19:15 · primeiro ponto com projeção",
      principal: { rotulo: "Flávio projetado nos votos entre os dois", valor: { dado: "projecao_noite.primeiro_ponto_com_projecao.p_f_projetado" }, casas: 2, sufixo: "%", cor: COR.flavio },
      secundarios: [
        { rotulo: "das seções totalizadas", valor: { dado: "projecao_noite.primeiro_ponto_com_projecao.pst" }, casas: 2, sufixo: "%" },
        { rotulo: "faixa de 90%: de", valor: { dado: "projecao_noite.primeiro_ponto_com_projecao.faixa90[0]" }, casas: 2, sufixo: "%" },
        { rotulo: "faixa de 90%: até", valor: { dado: "projecao_noite.primeiro_ponto_com_projecao.faixa90[1]" }, casas: 2, sufixo: "%" },
      ],
      rotulo: "projecao",
      cor: COR.ouro,
    }),
    gatilhos: { secundarios: ["faixa", 8] },
  },
  "proj-serie": {
    componente: cenaSerie({
      chip: "Flávio entre os dois: projetado × observado",
      series: [
        { nome: "projetado", cor: COR.ouro, dado: "projecao_noite.pontos", xCampo: "min", yCampo: "p_f_projetado" },
        { nome: "observado", cor: COR.tealClaro, dado: "projecao_noite.pontos", xCampo: "min", yCampo: "p_f_observado", tracejada: true },
      ],
      x: { min: 135, max: 330, ticks: [150, 210, 270, 330], formato: "hhmm" },
      y: { min: 44, max: 52, ticks: [44, 46, 48, 50, 52], sufixo: "%" },
      marcas: [{ x: { dado: "projecao_noite.primeiro_ponto_com_projecao.min" }, rotulo: "primeira projeção", cor: COR.ouro }],
      rotulo: "projecao",
      cor: COR.ouro,
    }),
  },
  "proj-sem-virada": {
    componente: cenaCaptura({ chip: "a projeção na tela da apuração, 21:25", captura: "cap_tela_projecao", cor: COR.ouro, rotulo: "projecao", foco: [{ quadro: 0, x: 0.3, y: 0.3, escala: 1 }, { quadro: 500, x: 0.25, y: 0.3, escala: 1.25 }] }),
    midia: ["cap_tela_projecao"],
    sfx: [{ arquivo: "stamp.mp3", volume: 0.5 }],
  },
  // 3 Entre os dois turnos
  "cap-turnos": CAP,
  "turnos-swing-uf": {
    componente: cenaMapa({
      chip: "parte de Flávio entre os finalistas, 2º turno menos 1º",
      dado: "comparacao_1t.ufs",
      campoValor: "swing_h2h_flavio_pp",
      escala: { tipo: "divergente", dominio: 4.5 },
      legenda: { esquerda: "Flávio caiu", direita: "Flávio subiu" },
      cor: COR.lula,
    }),
  },
  "turnos-transferencia": {
    componente: cenaNumero({
      chip: "estimativa ecológica: agregado, não o voto de ninguém",
      principal: { rotulo: "milhões que faltaram no 1º turno e votaram no 2º", valor: { dado: "transferencia.resposta.voltaram_milhoes" }, casas: 2 },
      secundarios: [
        { rotulo: "parte de Flávio no ganho entre turnos", valor: { dado: "transferencia.contabilidade.parte_flavio_pct" }, casas: 1, sufixo: "%", cor: COR.flavio },
        { rotulo: "para Lula, de cada 100 a mais (seções)", valor: { dado: "transferencia.resposta.secoes_por_100_lula" }, casas: 1, cor: COR.lula },
        { rotulo: "para Lula, de cada 100 a mais (municípios)", valor: { dado: "transferencia.resposta.liquido_por_100_lula" }, casas: 1, cor: COR.lula },
        { rotulo: "da terceira via para Flávio", valor: { dado: "transferencia.resposta.terceira_flavio_pct" }, casas: 1, sufixo: "%", cor: COR.flavio },
      ],
      cor: COR.lula,
    }),
    gatilhos: { secundarios: ["Flávio", 4] },
  },
  "turnos-abstencao": {
    componente: cenaMapa({
      chip: "abstenção contra o 1º turno, pontos percentuais",
      dado: "abstencao.ufs",
      campoValor: "delta_1t_pp",
      escala: { tipo: "divergente", dominio: 8, baixa: COR.tealClaro, alta: COR.ouro },
      legenda: { esquerda: "caiu", direita: "subiu" },
      destaque: ["AP", "RR", "AC"],
      rotulo: "atraso",
      cor: COR.lula,
    }),
  },
  // 4 Seção por seção (censo dos 499.207 boletins de urna)
  "cap-secoes": CAP,
  "secoes-encerramento": {
    componente: cenaNumero({
      chip: "todos os boletins de urna, seção por seção",
      principal: { rotulo: "dos boletins emitidos até as 17:30", valor: { dado: "secoes.prorrogacao.brasil.pct_bu_emitido_ate_1730" }, casas: 2, sufixo: "%" },
      secundarios: [
        { rotulo: "boletins lidos", valor: { dado: "secoes.totais.secoes" } },
        { rotulo: "encerrados depois das 19h", valor: { dado: "secoes.prorrogacao.brasil.n_apos_1900" }, cor: COR.ouro },
        { rotulo: "das seções, encerradas depois das 19h", valor: { dado: "secoes.prorrogacao.brasil.pct_apos_1900" }, casas: 2, sufixo: "%", cor: COR.ouro },
        { rotulo: "dos boletins recebidos antes das 19h", valor: { dado: "secoes.prorrogacao.brasil.pct_recebido_antes_1900" }, casas: 2, sufixo: "%", cor: COR.alta },
      ],
      rotulo: "atraso",
      cor: COR.media,
    }),
    gatilhos: { secundarios: ["Noventa", 8] },
  },
  "secoes-biometria": {
    componente: cenaNumero({
      chip: "biometria baixa: sinal que já existia no 1º turno",
      principal: { rotulo: "seções com o sinal que já o tinham no 1º turno", valor: { dado: "secoes.agregados.brasil.persistencia.sem_bio_ja_no_1t" } },
      secundarios: [
        { rotulo: "seções com o sinal no 2º turno", valor: { dado: "secoes.agregados.brasil.persistencia.sem_bio_n" } },
        { rotulo: "Candeias (BA), z. 127, s. 336: salto sem biometria reconhecida, pp", valor: { dado: "secoes_ranking.secoes[28].salto_bio_pp" }, casas: 2, cor: COR.ouro },
      ],
      rotulo: "atipicidade",
      cor: COR.media,
    }),
    gatilhos: { secundarios: ["Candeias", 10] },
  },
  "secoes-comparecimento": {
    componente: cenaNumero({
      chip: "comparecimento contra a mesma seção no 1º turno",
      principal: { rotulo: "variação média por seção, pontos", valor: { dado: "secoes.agregados.brasil.delta_comp.media" }, casas: 2, prefixo: "+" },
      secundarios: [
        { rotulo: "seções com +5 pontos ou mais", valor: { dado: "secoes.agregados.brasil.sinais.delta" } },
        { rotulo: "parte de Flávio nelas (dif. em dif., pp)", valor: { dado: "secoes_voto.sinais[0].did_fatia_flavio_pp" }, casas: 2, cor: COR.lula },
        { rotulo: "nas de biometria baixa (dif. em dif., pp)", valor: { dado: "secoes_voto.sinais[3].did_fatia_flavio_pp" }, casas: 2, cor: COR.lula },
      ],
      rotulo: "atipicidade",
      cor: COR.media,
    }),
    gatilhos: { secundarios: ["Quarenta", 5] },
  },
  "secoes-ranking": {
    componente: cenaRanking({
      chip: "as seções que pedem explicação",
      dado: "secoes_ranking.secoes",
      colunas: [
        { titulo: "UF", campo: "uf", largura: 1 },
        { titulo: "município", campo: "municipio", largura: 4 },
        { titulo: "zona", campo: "zona", formato: "inteiro", largura: 1 },
        { titulo: "seção", campo: "secao", formato: "inteiro", largura: 1 },
        { titulo: "escore", campo: "escore", formato: "inteiro", largura: 1 },
        { titulo: "Δ comparecimento (pp)", campo: "delta_comp_pp", formato: "decimal", casas: 2, largura: 2 },
      ],
      limite: 8,
      rotulo: "atipicidade",
      cor: COR.media,
    }),
  },
  // 5 Pesquisas contra a urna (distância = diferença Flávio menos Lula da pesquisa menos a da urna;
  // medida do que mudou entre o último campo e a urna, TESE.md)
  "cap-pesquisas": CAP,
  "pesq-erro": {
    componente: cenaRanking({
      chip: "distância até a urna na diferença Flávio menos Lula, última onda de cada casa (pp)",
      dado: "pesquisas_vs_urna.pesquisas",
      colunas: [
        { titulo: "instituto", campo: "instituto", largura: 4 },
        { titulo: "modo", campo: "modo", largura: 2, rotulos: MODO_COLETA },
        { titulo: "Flávio nos válidos", campo: "validos_do_total.flavio", formato: "decimal", casas: 2, largura: 2 },
        { titulo: "distância (pp)", campo: "erro_validos_do_total.erro_f_menos_l", formato: "decimal", casas: 2, largura: 2 },
      ],
      ordenar: { campo: "erro_validos_do_total.erro_f_menos_l", ordem: "decrescente" },
      limite: 10,
      cor: COR.outros,
    }),
  },
  "pesq-reponderacao": {
    componente: cenaRanking({
      chip: "a régua de renda da casa: distância até a urna, publicado × reponderado (pp)",
      dado: "pesquisas_vs_urna.efeito_reponderacao.por_casa",
      colunas: [
        { titulo: "instituto", campo: "instituto", largura: 4 },
        { titulo: "publicado", campo: "erro_publicado_f_menos_l", formato: "decimal", casas: 2, largura: 2 },
        { titulo: "reponderado", campo: "erro_reponderado_f_menos_l", formato: "decimal", casas: 2, largura: 2 },
        { titulo: "efeito", campo: "direcao", largura: 2 },
      ],
      ordenar: { campo: "erro_reponderado_f_menos_l", ordem: "decrescente" },
      limite: 11,
      cor: COR.outros,
    }),
  },
  "pesq-hipotese": {
    componente: cenaNumero({
      chip: "hipótese do autor, refeita no simulador",
      principal: { rotulo: "presença relativa de Flávio que reproduz a urna", valor: { dado: "hipotese_autor.presenca_necessaria_a" }, casas: 2, sufixo: "%", cor: COR.ouro },
      secundarios: [
        { rotulo: "no cenário do tweet das 21:41", valor: { dado: "hipotese_autor.reproducao_tweet.parametros.presenca_relativa" }, casas: 1, sufixo: "%" },
        { rotulo: "hipótese da central antes da urna", valor: { dado: "pesquisas_vs_urna.centrais.presenca_relativa_pct" }, casas: 1, prefixo: "+", sufixo: "%" },
      ],
      rotulo: "hipotese",
      cor: COR.ouro,
    }),
    gatilhos: { secundarios: ["Ninguém", 14] },
  },
  // 6 As urnas por dentro (logs, assinaturas, RDV e totalização paralela)
  "cap-urnas": CAP,
  "urnas-cadencia": {
    componente: cenaNumero({
      chip: "logs das urnas: votos computados depois das 17h",
      principal: { rotulo: "dos votos do 2º turno entre 17h e 19h", valor: { dado: "logs.cadencia.brasil_2t.pct_17_19" }, casas: 3, sufixo: "%", cor: COR.teal },
      secundarios: [
        { rotulo: "votos entre 17h e 19h", valor: { dado: "logs.cadencia.brasil_2t.computados_17_19" } },
        { rotulo: "no 1º turno, entre 17h e 19h", valor: { dado: "logs.cadencia.amostra_1t.brasil_1t.pct_17_19" }, casas: 2, sufixo: "%", cor: COR.ouro },
        { rotulo: "votos depois das 19h", valor: { dado: "logs.cadencia.brasil_2t.computados_depois_19" }, cor: COR.alta },
        { rotulo: "dos votos entre 8h e 9h", valor: { dado: "logs.cadencia.brasil_2t.pct_primeira_hora" }, casas: 2, sufixo: "%" },
      ],
      rotulo: "atipicidade",
      cor: COR.teal,
    }),
    gatilhos: { secundarios: ["trinta", 10] },
  },
  "urnas-integridade": {
    componente: cenaNumero({
      chip: "log contra boletim, seção por seção",
      principal: { rotulo: "logs com a contagem igual à do boletim", valor: { dado: "logs.cobertura.contagem_confere" } },
      secundarios: [
        { rotulo: "logs lidos", valor: { dado: "logs.cobertura.lidos" } },
        { rotulo: "seções com o sistema religado na votação", valor: { dado: "logs.reinicios.secoes" }, cor: COR.ouro },
        { rotulo: "efeito no voto contra o 1º turno, pp", valor: { dado: "logs.reinicios.voto[0].dif_em_dif_contra_1t.media_pp" }, casas: 3 },
      ],
      rotulo: "atipicidade",
      cor: COR.teal,
    }),
    gatilhos: { secundarios: ["Doze", 8] },
  },
  "urnas-assinatura": {
    componente: cenaNumero({
      chip: "assinatura da urna e registro digital do voto",
      principal: { rotulo: "arquivos de assinatura lidos com cadeia e assinatura válidas", valor: { dado: "metadados.turnos.2t.coerencia_vsc.cadeia_ate_a_ac.sim" } },
      secundarios: [
        { rotulo: "com cadeia inválida", valor: { dado: "metadados.turnos.2t.coerencia_vsc.cadeia_ate_a_ac.nao" } },
        { rotulo: "RDVs lidos iguais ao boletim (coleta parcial)", valor: { dado: "rdv.cobertura.total.confere" } },
        { rotulo: "seções com a série da memória de resultado repetida", valor: { dado: "logs.metadados.serie_mr.secoes_em_repeticao" }, cor: COR.ouro },
      ],
      rotulo: "atipicidade",
      cor: COR.teal,
    }),
    gatilhos: { secundarios: ["registro", 8] },
  },
  "paralela-177": {
    componente: cenaNumero({
      chip: "totalização paralela por QR",
      principal: { rotulo: "BUs recebidos e conferidos voto a voto", valor: { dado: "paralela.recebidos.bus" }, casas: 0 },
      secundarios: [
        { rotulo: "UFs com BU", valor: { dado: "paralela.recebidos.ufs" } },
        { rotulo: "iguais ao arquivo do TSE", valor: { dado: "paralela.conferencia.igual" }, cor: COR.teal },
      ],
      rotulo: "paralela",
      cor: COR.teal,
    }),
    gatilhos: { secundarios: ["quinze", 5] },
    sfx: [{ arquivo: "qr.mp3", volume: 0.6 }],
  },
  // 7 Fecho
  "cap-fecho": CAP,
  "fecho-arvor": {
    componente: cenaCaptura({ chip: "Arvor Intelligence · laudos em brasil.arvor.co", captura: "cap_dossie_topo", endereco: "brasil.arvor.co/apuracao_2T_2026.html", cor: COR.tealClaro }),
    midia: ["cap_dossie_topo"],
  },
  "fecho-chamada": {
    componente: cenaTexto({
      chip: "arvor.co",
      titulo: "A chave de ouro é o método",
      linhas: ["Dados abertos.", "Conta na tela.", "Erro admitido."],
    }),
    sfx: [{ arquivo: "chime.mp3", volume: 0.5 }],
  },
} satisfies Record<CenaId, CenaDef>;

export const definicaoDe = (id: CenaId): CenaDef => REGISTRO[id];
