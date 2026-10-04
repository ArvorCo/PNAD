// Recarga automática do telão quando um bundle novo é compilado (hot restart do dia da eleição).
// Sonda o `Last-Modified` de /dist/ui/main.js a cada 20 s; se mudou, recarrega a página
// preservando o hash. O OBS não precisa de refresh manual. Só roda fora do mock.

const ALVOS = ["/dist/ui/main.js", "/playlist.json"];
const INTERVALO_MS = 20_000;

export function vigiarBundle(ativo: boolean): void {
  if (!ativo) return;
  const marcas = new Map<string, string>();
  const sondar = async (): Promise<void> => {
    for (const alvo of ALVOS) {
      try {
        const r = await fetch(alvo, { method: "HEAD", cache: "no-store" });
        const m = r.headers.get("last-modified") ?? r.headers.get("etag");
        if (!m) continue;
        const antes = marcas.get(alvo);
        if (antes === undefined) marcas.set(alvo, m);
        else if (m !== antes) {
          location.reload();
          return;
        }
      } catch {
        // sem rede: tenta no próximo ciclo
      }
    }
  };
  void sondar();
  setInterval(() => void sondar(), INTERVALO_MS);
}
