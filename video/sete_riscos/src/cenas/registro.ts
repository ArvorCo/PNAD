// Registro das cenas: qual componente desenha cada id da ordem, com gatilhos de fala, mídia usada
// e efeitos sonoros. `satisfies Record<CenaId, CenaDef>` faz o typecheck falhar se faltar cena.
// Este arquivo cobre os capítulos 0 a 2 (abertura, lei, riscos); os capítulos 3 a 5 vivem em
// registro_b.ts e entram por spread. Gatilhos na ordem em que as palavras são ditas (a busca é
// sequencial); a reserva em segundos é o tempo real da palavra em voz.json.
import type { ComponentType } from "react";
import { CartaoCapitulo } from "../componentes/CartaoCapitulo";
import { RiscoCapitulo } from "../componentes/Risco";
import type { CenaId } from "../ordem";
import type { Cena, Gatilhos } from "../plano";
import type { Dados } from "../tipos";
import { Abertura } from "./Abertura";
import { LeiPoderes } from "./LeiPoderes";
import { LeiPostura } from "./LeiPostura";
import { REGISTRO_B } from "./registro_b";
import { RiscoBocaDeUrna } from "./RiscoBocaDeUrna";
import { RiscoCompra } from "./RiscoCompra";
import { RiscoMedo } from "./RiscoMedo";
import { RiscoMesario } from "./RiscoMesario";
import { RiscoPianista } from "./RiscoPianista";
import { RiscoTotalizacao } from "./RiscoTotalizacao";
import { RiscoTransporte } from "./RiscoTransporte";
import { Tese } from "./Tese";

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

export const REGISTRO = {
  // 0 Abertura
  abertura: {
    componente: Abertura,
    gatilhos: {
      barcarena: ["Barcarena", 1.24],
      secao: ["seção", 3.2],
      rural: ["rural", 3.52],
      comparecimento: ["comparecimento", 8.8],
      pais: ["país", 11.68],
      lula90: ["duas", 12.36],
      fimLula: ["seções", 14.24],
      flavio: ["Flávio", 17.76],
      fimFlavio: ["seis", 19.32],
      atipicidade: ["Atipicidade", 20.08],
      ninguem: ["Ninguém", 23.18],
      so: ["só", 25.6],
      ve: ["VÊ", 26.8],
    },
    midia: ["rua_escola_amanhecer_still", "rio_amazonia_escola"],
    sfx: [
      { arquivo: "scan", gatilho: "lula90", volume: 0.18 },
      { arquivo: "stamp", gatilho: "atipicidade", volume: 0.22 },
    ],
  },
  tese: {
    componente: Tese,
    gatilhos: {
      fiscal: ["fiscal", 2.08],
      ve: ["vê", 2.56],
      anota: ["anota", 3.25],
      pede: ["pede", 4.0],
      discute: ["discute", 5.36],
      grita: ["grita", 6.4],
      muda: ["muda", 7.32],
      protege: ["protege", 8.72],
      precisa: ["precisa", 11.48],
      arma: ["arma", 12.08],
      gritaria: ["gritaria", 12.64],
      teatral: ["coragem", 13.68],
      atencao: ["atenção", 15.6],
      papel: ["papel", 16.56],
      lei: ["lei", 17.6],
      sete: ["Sete", 18.84],
      um: ["um", 19.95],
      leiFim: ["LEI", 21.36],
    },
    midia: ["fiscal_cadeira", "secao_vazia"],
    sfx: [
      { arquivo: "blip", gatilho: "ve", volume: 0.22 },
      { arquivo: "blip", gatilho: "anota", volume: 0.22 },
      { arquivo: "blip", gatilho: "pede", volume: 0.22 },
      { arquivo: "stamp", gatilho: "leiFim", volume: 0.26 },
    ],
  },
  // 1 O fiscal e a lei
  "cap-lei": { componente: CartaoCapitulo, gatilhos: { numero: ["Capítulo", 0.2], titulo: ["fiscal", 1.44] } },
  "lei-poderes": {
    componente: LeiPoderes,
    gatilhos: {
      inicio: ["Primeiro", 0.27],
      fiscalizar: ["fiscalizar", 5.55],
      dois: ["dois", 8.72],
      credencial: ["credencial", 11.68],
      impugnar: ["impugnar", 15.76],
      copia: ["cópia", 22.8],
      junta: ["junta", 28.56],
      tudo: ["Tudo", 30.79],
    },
    midia: ["fiscal_cadeira"],
    sfx: [
      { arquivo: "tique", gatilho: "fiscalizar", volume: 0.2 },
      { arquivo: "tique", gatilho: "dois", volume: 0.2 },
      { arquivo: "tique", gatilho: "credencial", volume: 0.2 },
      { arquivo: "tique", gatilho: "impugnar", volume: 0.2 },
      { arquivo: "tique", gatilho: "copia", volume: 0.2 },
      { arquivo: "tique", gatilho: "junta", volume: 0.2 },
    ],
  },
  "lei-postura": {
    componente: LeiPostura,
    gatilhos: {
      sabedoria: ["Sabedoria", 2.0],
      coragem: ["coragem", 3.08],
      lei: ["lei", 4.4],
      cracha: ["crachá", 5.36],
      discute: ["discute", 8.56],
      anota: ["anota", 10.88],
      ata: ["campo", 15.2],
      sai: ["mandar", 20.56],
      ministerio: ["Ministério", 27.08],
      decide: ["decide", 32.12],
      calma: ["calma", 37.84],
      coragemFim: ["Coragem", 39.76],
      sabedoriaFim: ["Sabedoria", 41.6],
      motivo: ["MOTIVO", 43.16],
    },
    midia: ["ata_mesa_still", "atas_mesa_lampada"],
    sfx: [
      { arquivo: "caneta", gatilho: "anota", volume: 0.3 },
      { arquivo: "papel", gatilho: "ata", volume: 0.26 },
      { arquivo: "stamp", gatilho: "motivo", volume: 0.26 },
    ],
  },
  // 2 Sete riscos. Em cada risco: caso (carimbo), sinal (alerta), fiscal (caneta ou papel).
  "cap-riscos": { componente: RiscoCapitulo, gatilhos: { numero: ["Capítulo", 0.2], titulo: ["Sete", 1.6] }, midia: ["secao_vazia"] },
  "risco-boca-de-urna": {
    componente: RiscoBocaDeUrna,
    gatilhos: {
      caso: ["Paulista", 7.96],
      mj: ["contou", 26.8],
      sinal: ["Sinal", 30.0],
      lei: ["pena", 35.92],
      fiscal: ["fiscal", 39.08],
      f1: ["registra", 39.64],
      f2: ["anota", 41.36],
      f3: ["aciona", 43.24],
      fecho: ["Coragem", 45.36],
    },
    midia: ["santinhos_calcada", "fila_secao", "cap_materia_paulista_pe_2020"],
    sfx: [
      { arquivo: "carimbo", gatilho: "caso", volume: 0.3 },
      { arquivo: "alerta", gatilho: "sinal", volume: 0.22 },
      { arquivo: "caneta", gatilho: "fiscal", volume: 0.3 },
    ],
  },
  "risco-compra": {
    componente: RiscoCompra,
    gatilhos: {
      lei: ["artigo", 9.72],
      caso: ["dois", 11.6],
      sinal: ["Sinal", 25.44],
      mj: ["quatrocentas", 29.48],
      fiscal: ["fiscal", 32.96],
      f1: ["anota", 33.44],
      f2: ["avisa", 35.76],
      f3: ["Celular", 37.2],
      fecho: ["Quem", 42.04],
    },
    midia: ["envelope_mao", "fila_secao", "cap_materia_jackson_lago_2009"],
    sfx: [
      { arquivo: "carimbo", gatilho: "caso", volume: 0.3 },
      { arquivo: "alerta", gatilho: "sinal", volume: 0.22 },
      { arquivo: "caneta", gatilho: "fiscal", volume: 0.3 },
    ],
  },
  "risco-transporte": {
    componente: RiscoTransporte,
    gatilhos: {
      lei: ["crime", 8.24],
      caso: ["Reserva", 9.28],
      anchieta: ["Anchieta", 19.76],
      sinal: ["Sinal", 28.64],
      mj: ["cinquenta", 35.04],
      fiscal: ["fiscal", 37.96],
      f1: ["placa", 38.8],
      f2: ["avisa", 40.0],
      f3: ["aborda", 41.6],
      fecho: ["Sabedoria", 43.12],
    },
    midia: ["van_eleitores", "fila_secao", "cap_materia_hornung_reserva_2004"],
    sfx: [
      { arquivo: "carimbo", gatilho: "caso", volume: 0.3 },
      { arquivo: "alerta", gatilho: "sinal", volume: 0.22 },
      { arquivo: "caneta", gatilho: "fiscal", volume: 0.3 },
    ],
  },
  "risco-medo": {
    componente: RiscoMedo,
    gatilhos: {
      lei: ["artigo", 7.92],
      caso: ["Santa", 11.04],
      rio: ["Rio", 23.6],
      sinal: ["Sinal", 28.96],
      secao: ["Bagre", 35.12],
      fiscal: ["fiscal", 45.28],
      f1: ["confronta", 46.04],
      f2: ["registra", 47.17],
      f3: ["Força", 47.92],
    },
    midia: ["viela_noite", "rio_amazonia_escola", "cap_materia_santa_quiteria_ce_faccao_2024"],
    sfx: [
      { arquivo: "sirene_longe", volume: 0.1 },
      { arquivo: "carimbo", gatilho: "caso", volume: 0.3 },
      { arquivo: "alerta", gatilho: "sinal", volume: 0.22 },
      { arquivo: "caneta", gatilho: "fiscal", volume: 0.3 },
    ],
  },
  "risco-mesario": {
    componente: RiscoMesario,
    gatilhos: {
      caso: ["Itumbiara", 7.76],
      sinal: ["Sinal", 24.24],
      fiscal: ["fiscal", 30.88],
      f1: ["impugna", 31.36],
      lei: ["artigo", 32.64],
      f2: ["registre", 35.68],
      f3: ["Anota", 36.96],
      f4: ["discute", 39.12],
      fecho: ["Coragem", 40.64],
    },
    midia: ["cabine_mesario", "teclado_urna_macro", "cap_materia_itumbiara_2018"],
    sfx: [
      { arquivo: "passos", volume: 0.2 },
      { arquivo: "carimbo", gatilho: "caso", volume: 0.3 },
      { arquivo: "alerta", gatilho: "sinal", volume: 0.22 },
      { arquivo: "caneta", gatilho: "fiscal", volume: 0.3 },
    ],
  },
  "risco-pianista": {
    componente: RiscoPianista,
    gatilhos: {
      lei: ["artigo", 6.68],
      caso: ["Pescaria", 8.8],
      macapa: ["Macapá", 26.64],
      sinal: ["Sinal", 33.04],
      secao: ["Baião", 37.52],
      fiscal: ["fiscal", 46.48],
      f1: ["fica", 47.04],
      f2: ["confere", 48.4],
    },
    midia: ["caderno_assinatura", "urna_mesa_lacre", "cap_materia_pescaria_brava_2016"],
    sfx: [
      { arquivo: "carimbo", gatilho: "caso", volume: 0.3 },
      { arquivo: "alerta", gatilho: "sinal", volume: 0.22 },
      { arquivo: "caneta", gatilho: "fiscal", volume: 0.3 },
    ],
  },
  "risco-totalizacao": {
    componente: RiscoTotalizacao,
    gatilhos: {
      caso: ["Rio", 4.96],
      sinal: ["Sinal", 20.95],
      fiscal: ["fiscal", 27.92],
      f1: ["cópia", 28.64],
      f2: ["QR", 29.68],
      f3: ["compara", 30.32],
      lei: ["artigo", 32.64],
      fecho: ["Coragem", 39.52],
    },
    midia: ["fita_impressora_antiga", "boletim_impressora", "cap_materia_proconsult_rj_1982"],
    sfx: [
      { arquivo: "carimbo", gatilho: "caso", volume: 0.3 },
      { arquivo: "alerta", gatilho: "sinal", volume: 0.22 },
      { arquivo: "papel", gatilho: "fiscal", volume: 0.3 },
    ],
  },
  // Capítulos 3 a 5 vivem em registro_b.ts.
  ...REGISTRO_B,
} satisfies Record<CenaId, CenaDef>;

export const definicaoDe = (id: CenaId): CenaDef => REGISTRO[id];
