// Registro das cenas dos capítulos 3 a 5 (fechamento, mapa, fecho). Mesclado em registro.ts por
// spread. Gatilhos na ordem em que as palavras são ditas (a busca é sequencial); a reserva é o
// segundo da palavra na voz de 21/10, usado se a palavra sumir numa voz regerada.
import { capituloComFundo } from "../componentes/FechaCapitulo";
import { FechaTotalizacao } from "./FechaTotalizacao";
import { FechaUltimos } from "./FechaUltimos";
import { FechoChamada } from "./FechoChamada";
import { MapaCadastro } from "./MapaCadastro";
import { MapaFiscais } from "./MapaFiscais";
import type { CenaDef } from "./registro";

export const REGISTRO_B = {
  // 3 A hora de fechar
  "cap-fechamento": {
    componente: capituloComFundo({ clipe: "entardecer_escola", still: "boletim_porta" }),
    midia: ["boletim_porta"],
  },
  "fecha-ultimos": {
    componente: FechaUltimos,
    gatilhos: {
      dezessete: ["dezessete", 0.3],
      senha: ["senha", 2.8],
      duas: ["duas", 4.6],
      boletim: ["boletim", 9.3],
      copia: ["cópia", 10.6],
      afixada: ["afixada", 11.2],
      pedir: ["pedir", 13.8],
      dica: ["Dica", 16.1],
      chegue: ["chegue", 17.2],
      fique: ["fique", 19.3],
      peca: ["peça", 21.0],
      fotografe: ["fotografe", 22.1],
      qr: ["QR", 22.8],
      depois: ["Depois", 23.9],
      junta: ["junta", 26.0],
      fim: ["fim", 27.1],
      mais: ["MAIS", 31.1],
    },
    midia: ["fila_secao", "maos_boletim_porta"],
    sfx: [
      { arquivo: "tique", volume: 0.3 },
      { arquivo: "impressora", gatilho: "boletim", volume: 0.3 },
      { arquivo: "carimbo", gatilho: "afixada", volume: 0.28 },
      { arquivo: "blip", gatilho: "dica", volume: 0.25 },
      { arquivo: "qr", gatilho: "qr", volume: 0.35 },
      { arquivo: "passos", gatilho: "depois", volume: 0.22 },
      { arquivo: "stamp", gatilho: "mais", volume: 0.3 },
    ],
  },
  "fecha-totalizacao": {
    componente: FechaTotalizacao,
    gatilhos: {
      brasil: ["brasil", 3.3],
      aplicativo: ["aplicativo", 7.8],
      qr: ["QR", 8.9],
      confere: ["confere", 10.3],
      grava: ["grava", 13.5],
      painel: ["painel", 14.6],
      compara: ["compara", 15.0],
      rotulo: ["rótulo", 19.3],
      soma: ["soma", 20.9],
      projecao: ["projeção", 23.2],
      prova: ["Prova", 24.4],
      naoProva: ["não", 27.2],
      veredito: ["veredito", 31.2],
    },
    midia: ["cap_totalizacao_ler", "cap_totalizacao_conferir"],
    sfx: [
      { arquivo: "teclado", gatilho: "brasil", volume: 0.16 },
      { arquivo: "qr", gatilho: "qr", volume: 0.4 },
      { arquivo: "scan", gatilho: "confere", volume: 0.22 },
      { arquivo: "chime", gatilho: "compara", volume: 0.28 },
      { arquivo: "carimbo", gatilho: "soma", volume: 0.28 },
      { arquivo: "alerta", gatilho: "naoProva", volume: 0.18 },
      { arquivo: "stamp", gatilho: "veredito", volume: 0.28 },
    ],
  },
  // 4 Onde você faz diferença
  "cap-mapa": {
    componente: capituloComFundo({ still: "mapa_fundo_textura", opacidade: 0.4 }),
    midia: ["mapa_fundo_textura"],
  },
  "mapa-fiscais": {
    componente: MapaFiscais,
    gatilhos: {
      abra: ["abra", 1.4],
      busque: ["Busque", 5.4],
      cep: ["CEP", 6.0],
      zona: ["zona", 6.5],
      municipio: ["município", 7.1],
      raio: ["raio", 8.6],
      predio: ["prédio", 9.8],
      exemplo: ["exemplo", 11.3],
      bangu: ["Bangu", 12.9],
      secoes: ["vinte", 14.4],
      aptos: ["cinco", 15.9],
      uma: ["Uma", 18.7],
      conferencia: ["conferência", 20.0],
      fiscal: ["fiscal", 21.6],
      pouco: ["POUCO", 23.8],
      lista: ["lista", 25.5],
    },
    midia: ["cap_mapa_cep", "cap_mapa_busca_rj", "cap_mapa_predio_rj"],
    sfx: [
      { arquivo: "teclado", gatilho: "abra", volume: 0.16 },
      { arquivo: "zoom", gatilho: "cep", volume: 0.24 },
      { arquivo: "blip", gatilho: "raio", volume: 0.22 },
      { arquivo: "zoom", gatilho: "bangu", volume: 0.24 },
      { arquivo: "blip", gatilho: "secoes", volume: 0.24 },
      { arquivo: "alerta", gatilho: "conferencia", volume: 0.2 },
      { arquivo: "stamp", gatilho: "pouco", volume: 0.3 },
    ],
  },
  "mapa-cadastro": {
    componente: MapaCadastro,
    gatilhos: {
      fiscais: ["fiscais", 2.3],
      vinte: ["vinte", 5.5],
      prazo: ["prazo", 7.0],
      dezoito: ["dezoito", 10.2],
      mesario: ["mesário", 12.0],
      candidato: ["candidato", 12.8],
      credencial: ["credencial", 13.9],
      cadastrese: ["Cadastre", 16.5],
    },
    midia: ["cap_fiscaisdopl"],
    sfx: [
      { arquivo: "teclado", gatilho: "fiscais", volume: 0.16 },
      { arquivo: "carimbo", gatilho: "vinte", volume: 0.28 },
      { arquivo: "blip", gatilho: "dezoito", volume: 0.22 },
      { arquivo: "stamp", gatilho: "credencial", volume: 0.28 },
      { arquivo: "chime", gatilho: "cadastrese", volume: 0.26 },
    ],
  },
  // 5 Convite
  "fecho-chamada": {
    componente: FechoChamada,
    gatilhos: {
      atipicidade: ["Atipicidade", 2.1],
      lista: ["lista", 5.8],
      resolve: ["resolve", 10.7],
      sete: ["Sete", 16.8],
      fiscal: ["fiscal", 18.3],
      nenhuma: ["Nenhuma", 19.4],
      daqui: ["Daqui", 21.9],
      alguem: ["Alguém", 28.3],
      pode: ["Pode", 30.5],
      voce: ["VOCÊ", 30.9],
    },
    midia: ["fiscal_cadeira"],
    sfx: [
      { arquivo: "carimbo", gatilho: "atipicidade", volume: 0.24 },
      { arquivo: "carimbo", gatilho: "lista", volume: 0.24 },
      { arquivo: "carimbo", gatilho: "resolve", volume: 0.24 },
      { arquivo: "riser", gatilho: "alguem", volume: 0.22 },
      { arquivo: "stamp", gatilho: "voce", volume: 0.34 },
    ],
  },
} satisfies Record<string, CenaDef>;
