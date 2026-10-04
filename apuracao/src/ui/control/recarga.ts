// Recarga automática do telão quando um bundle novo é compilado (hot restart do dia da eleição).
// Sonda o `Last-Modified` de /dist/ui/main.js a cada 20 s; se mudou, recarrega a página
// preservando o hash. O OBS não precisa de refresh manual. Só roda fora do mock.

const ALVO = "/dist/ui/main.js";
const INTERVALO_MS = 20_000;

export function vigiarBundle(ativo: boolean): void {
  if (!ativo) return;
  let marca: string | null = null;
  const sondar = async (): Promise<void> => {
    try {
      const r = await fetch(ALVO, { method: "HEAD", cache: "no-store" });
      const m = r.headers.get("last-modified") ?? r.headers.get("etag");
      if (!m) return;
      if (marca === null) marca = m;
      else if (m !== marca) location.reload();
    } catch {
      // sem rede: tenta no próximo ciclo
    }
  };
  void sondar();
  setInterval(() => void sondar(), INTERVALO_MS);
}
