-- Registro atomico de um envio: a Edge Function (service_role) ja verificou QR, cadeia SHA-512,
-- assinatura e cadeia de certificacao; aqui entram a deduplicacao, o conflito e a gravacao em
-- uma transacao so. Nunca chamada por anon (sem grant).

create or replace function registrar_envio(p jsonb) returns jsonb
language plpgsql as $$
declare
  v_envio_id bigint;
  v_bu_id bigint;
  v_status text;
  v_motivo text;
  v_existente bigint;
  v_outros integer;
  b jsonb := p->'bu';
  c jsonb;
  v jsonb;
begin
  -- Rejeicao decidida pela funcao de borda: so registra.
  if (p->>'status') = 'rejeitado' then
    insert into envio (aparelho_hash, ip_hash, qr_textos, status, motivo, versao_motor)
      values (p->>'aparelho_hash', p->>'ip_hash', array(select jsonb_array_elements_text(p->'qr_textos')), 'rejeitado', p->>'motivo', p->>'versao_motor')
      returning id into v_envio_id;
    return jsonb_build_object('status', 'rejeitado', 'motivo', p->>'motivo', 'envio_id', v_envio_id, 'bu', null);
  end if;

  perform pg_advisory_xact_lock(hashtext(format('%s-%s-%s-%s', b->>'uf', b->>'muni', b->>'zona', b->>'secao')));

  select id into v_existente from bu
   where uf = b->>'uf' and muni = (b->>'muni')::int and zona = (b->>'zona')::int and secao = (b->>'secao')::int
     and hash_final = b->>'hash_final';
  select count(*) into v_outros from bu
   where uf = b->>'uf' and muni = (b->>'muni')::int and zona = (b->>'zona')::int and secao = (b->>'secao')::int
     and hash_final <> b->>'hash_final';

  if v_existente is not null then
    v_status := 'repetido'; v_bu_id := v_existente;
    v_motivo := 'mesma secao e mesmo hash ja registrados';
  else
    v_status := case when v_outros > 0 then 'conflito' else 'aceito' end;
    v_motivo := case when v_outros > 0 then format('%s BU(s) com hash diferente para a mesma secao', v_outros) else null end;
  end if;

  insert into envio (aparelho_hash, ip_hash, qr_textos, status, motivo, versao_motor)
    values (p->>'aparelho_hash', p->>'ip_hash', array(select jsonb_array_elements_text(p->'qr_textos')), v_status, v_motivo, p->>'versao_motor')
    returning id into v_envio_id;

  if v_existente is null then
    insert into bu (envio_id, uf, muni, zona, secao, agre, orig, turno, pleito, proc, fase, dtpl, idue, mdue, vers,
                    aptos, comparecimento, faltosos, dtfc, hrfc, hash_final, assi, algoritmo, cert_der,
                    cert_fingerprint, cert_subject, cert_issuer, conteudo, cadeia)
      values (v_envio_id, b->>'uf', (b->>'muni')::int, (b->>'zona')::int, (b->>'secao')::int, b->>'agre', b->>'orig',
              (b->>'turno')::smallint, (b->>'pleito')::int, (b->>'proc')::int, b->>'fase', (b->>'dtpl')::date,
              (b->>'idue')::bigint, b->>'mdue', b->>'vers', (b->>'aptos')::int, (b->>'comparecimento')::int,
              (b->>'faltosos')::int, (b->>'dtfc')::date, (b->>'hrfc')::time, b->>'hash_final', b->>'assi',
              b->>'algoritmo', decode(b->>'cert_hex', 'hex'), '', b->>'cert_subject', b->>'cert_issuer',
              b->>'conteudo', '')
      returning id into v_bu_id;
    for c in select * from jsonb_array_elements(b->'cargos') loop
      insert into bu_cargo (bu_id, idel, cargo, tipo, apta, nomi, legc, bran, nulo, totc)
        values (v_bu_id, (c->>'idel')::int, (c->>'cargo')::smallint, (c->>'tipo')::smallint, (c->>'apta')::int,
                (c->>'nomi')::int, coalesce((c->>'legc')::int, 0), (c->>'bran')::int, (c->>'nulo')::int, (c->>'totc')::int);
      for v in select * from jsonb_array_elements(c->'votos') loop
        insert into bu_voto (bu_id, idel, cargo, partido, candidato, votos)
          values (v_bu_id, (c->>'idel')::int, (c->>'cargo')::smallint, (v->>'partido')::int, v->>'candidato', (v->>'votos')::int);
      end loop;
    end loop;
    -- Forca a conferencia das somas aqui, para o erro voltar a quem chamou e nao so no commit.
    set constraints bu_voto_soma immediate;
  end if;

  return jsonb_build_object('status', v_status, 'motivo', v_motivo, 'envio_id', v_envio_id,
    'bu', jsonb_build_object('uf', b->>'uf', 'muni', (b->>'muni')::int, 'zona', (b->>'zona')::int,
                             'secao', (b->>'secao')::int, 'hash', b->>'hash_final', 'id', v_bu_id));
end $$;

-- Limite de taxa: envios por ip_hash na janela.
create or replace function envios_recentes(p_ip_hash text, p_segundos integer) returns integer
language sql stable as $$
  select count(*)::integer from envio where ip_hash = p_ip_hash and recebido_em > now() - make_interval(secs => p_segundos);
$$;

revoke all on function registrar_envio(jsonb) from public, anon, authenticated;
revoke all on function envios_recentes(text, integer) from public, anon, authenticated;
grant execute on function registrar_envio(jsonb) to service_role;
grant execute on function envios_recentes(text, integer) to service_role;
-- service_role (so a Edge Function) escreve nas tabelas e le as sequencias.
grant select, insert on envio, bu, bu_cargo, bu_voto to service_role;
grant select on secao_ref to service_role;
grant usage, select on all sequences in schema public to service_role;
-- search_path fixo (aviso do advisor de seguranca do Supabase).
alter function recusa_alteracao() set search_path = public;
alter function confere_soma_cargo() set search_path = public;
alter function encadeia_bu() set search_path = public;
alter function envios_recentes(text, integer) set search_path = public;
alter function registrar_envio(jsonb) set search_path = public;
