/* Totalização paralela: configuração pública do aplicativo.
   Valores públicos por desenho: a chave publicável do Supabase só autoriza a
   função de ingestão, que valida assinatura e hash do boletim no servidor.
   Ao publicar uma versão nova, mude `versao`: o service worker usa esse valor
   como nome do cache e troca a casca inteira do aplicativo. */
window.TOTALIZACAO_CONFIG = {
  supabaseUrl: "https://brvjvizqbyfamtxogvqf.supabase.co",
  publishableKey: "sb_publishable_OdrY6f2C-CdRzkorgyaudQ_taVWSIKw",
  funcaoUrl: "https://brvjvizqbyfamtxogvqf.supabase.co/functions/v1/receber-bu",
  turnstileSiteKey: null,
  versao: "2026-10-15.2"
};
