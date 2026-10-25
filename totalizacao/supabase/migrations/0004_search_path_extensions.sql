-- 25/10/2026, 18:10: as 68 primeiras submissões reais foram rejeitadas com
-- "function digest(text, unknown) does not exist". O pgcrypto do Supabase vive no esquema
-- `extensions`, e a 0003 fixou search_path = public nas funções, escondendo o digest()
-- que encadeia_bu() usa. Aplicado à mão no projeto às 18:12 e reprocessadas as 68 (37 aceitas, 31 repetidas).
alter function public.encadeia_bu() set search_path = public, extensions;
alter function public.registrar_envio(jsonb) set search_path = public, extensions;
alter function public.confere_soma_cargo() set search_path = public, extensions;
