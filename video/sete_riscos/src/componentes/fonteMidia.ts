import { CAPTURAS, MIDIA } from "../dados";
import type { FormatoMidia } from "../tipos";
import { existePublico } from "./publico";

export type FonteResolvida = {
  /** Caminho dentro de `public/`, pronto para `staticFile`. */
  arquivo: string;
  formato: FormatoMidia;
  /** Verdadeiro quando o formato pedido faltou e o outro será recortado ao centro. */
  recortado: boolean;
  segundos: number;
};

export type MidiaPendente = { pendente: string };

const outro = (f: FormatoMidia): FormatoMidia => (f === "16x9" ? "9x16" : "16x9");

/**
 * Resolve um id de mídia para o arquivo do formato atual. Ids `cap_<x>` são capturas
 * (`capturas.json`), os demais vêm de `midia.json`. Prefere o formato do vídeo; na falta, usa o
 * outro com `objectFit: cover` (recorte central). Sem registro ou sem arquivo, devolve o motivo.
 */
export const resolverMidia = (
  id: string,
  formato: FormatoMidia,
  extensao: "mp4" | "png",
  nomeStill?: string,
): FonteResolvida | MidiaPendente => {
  const captura = id.startsWith("cap_") ? CAPTURAS[id.slice(4)] : undefined;
  const registro = captura ?? MIDIA[id];
  if (!registro) {
    return { pendente: `${id}: sem registro em ${id.startsWith("cap_") ? "capturas.json" : "midia.json"}` };
  }
  if (nomeStill && captura && !(nomeStill in captura.stills)) {
    return { pendente: `${id}: still "${nomeStill}" ausente em capturas.json` };
  }
  const base = nomeStill ? `${id}_${nomeStill}` : id;
  for (const f of [formato, outro(formato)]) {
    const arquivo = `midia/${base}_${f}.${extensao}`;
    if (registro.formatos.includes(f) && existePublico(arquivo)) {
      return { arquivo, formato: f, recortado: f !== formato, segundos: registro.segundos };
    }
  }
  return { pendente: `${id}: arquivo public/midia/${base}_${formato}.${extensao} ainda não existe` };
};

export const ehPendente = (r: FonteResolvida | MidiaPendente): r is MidiaPendente => "pendente" in r;
