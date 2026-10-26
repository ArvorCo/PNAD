-- Relatos sem Cloudflare (26/10/2026): a Edge Function receber-relato passa a exigir desafio
-- proprio (HMAC com SAL_IP), prova de trabalho, tempo minimo de 8 s e campo-armadilha. Cada
-- desafio vale para um relato so: desafio_hash e unico.

alter table relato_secao add column if not exists desafio_hash text
  check (desafio_hash is null or desafio_hash ~ '^[0-9a-f]{64}$');
create unique index if not exists relato_secao_desafio on relato_secao (desafio_hash);

create or replace function registrar_relato(p jsonb) returns jsonb
language plpgsql as $$
declare
  v_recentes integer;
  v_cadastro boolean;
begin
  if coalesce(p->>'ip_hash', '') = '' or coalesce(p->>'desafio_hash', '') = '' then
    return jsonb_build_object('status', 'rejeitado', 'motivo', 'sem ip_hash ou desafio');
  end if;
  perform pg_advisory_xact_lock(hashtext('relato|' || (p->>'ip_hash')));
  if exists (select 1 from relato_secao where desafio_hash = p->>'desafio_hash') then
    return jsonb_build_object('status', 'repetido', 'motivo', 'desafio ja usado');
  end if;
  select count(*) into v_recentes from relato_secao
   where ip_hash = p->>'ip_hash' and criado_em > now() - interval '1 hour';
  if v_recentes >= 5 then
    return jsonb_build_object('status', 'limite', 'motivo', 'limite de 5 relatos por hora');
  end if;
  select exists (select 1 from secao_ref
                  where uf = lower(p->>'uf') and zona = (p->>'zona')::int and secao = (p->>'secao')::int)
    into v_cadastro;
  insert into relato_secao (turno, uf, zona, secao, local_id, secao_no_cadastro, tipo, texto, hora_aproximada,
                            presenciou, contato, ip_hash, user_agent, origem, versao, desafio_hash)
    values ((p->>'turno')::smallint, upper(p->>'uf'), (p->>'zona')::int, (p->>'secao')::int, nullif(p->>'local_id', ''),
            v_cadastro, (p->>'tipo')::relato_tipo, p->>'texto', nullif(p->>'hora_aproximada', '')::time,
            (p->>'presenciou')::boolean, nullif(p->>'contato', ''), p->>'ip_hash', nullif(p->>'user_agent', ''),
            p->>'origem', nullif(p->>'versao', ''), p->>'desafio_hash');
  return jsonb_build_object('status', 'aceito');
exception when unique_violation then
  return jsonb_build_object('status', 'repetido', 'motivo', 'desafio ja usado');
end $$;

alter function registrar_relato(jsonb) set search_path = public, extensions;
revoke all on function registrar_relato(jsonb) from public, anon, authenticated;
grant execute on function registrar_relato(jsonb) to service_role;
