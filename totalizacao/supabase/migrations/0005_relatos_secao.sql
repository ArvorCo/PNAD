-- Relatos de quem votou sobre a propria secao (Politize-se, 26/10/2026).
-- Mesmos principios da totalizacao: o navegador nunca escreve; so a Edge Function
-- receber-relato (service_role) insere, por registrar_relato(jsonb); RLS ligado sem policy para
-- anon; o conteudo e imutavel; leitura publica so por duas views de contagem, nunca texto,
-- contato nem ip_hash. O status de moderacao e a unica coluna alteravel, e cada troca fica
-- registrada em relato_moderacao (tambem imutavel).

create extension if not exists pgcrypto;

do $$
begin
  if not exists (select 1 from pg_type where typname = 'relato_tipo') then
    create type relato_tipo as enum (
      'fila_longa', 'urna_trocada', 'biometria_falhou', 'votou_sem_biometria', 'mesario_conduta',
      'boca_de_urna', 'transporte_irregular', 'local_mudou', 'secao_fechou_cedo', 'secao_fechou_tarde',
      'outro');
  end if;
  if not exists (select 1 from pg_type where typname = 'relato_status') then
    create type relato_status as enum ('novo', 'lido', 'descartado');
  end if;
end $$;

create table if not exists relato_secao (
  id                bigint generated always as identity primary key,
  criado_em         timestamptz not null default now(),
  turno             smallint not null check (turno in (1, 2)),
  uf                char(2) not null check (uf in ('AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS',
                                                   'MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC',
                                                   'SP','SE','TO','ZZ')),
  zona              integer not null check (zona between 1 and 9999),
  secao             integer not null check (secao between 1 and 9999),
  local_id          text check (local_id is null or (length(local_id) <= 64 and local_id ~ '^[A-Z]{2}-[0-9]+-[0-9]+-[A-Za-z0-9_-]+$')),
  secao_no_cadastro boolean not null,          -- a secao existe em secao_ref (cadastro do 1o turno)
  tipo              relato_tipo not null,
  texto             text not null check (char_length(texto) between 1 and 1000 and btrim(texto) <> ''),
  hora_aproximada   time check (hora_aproximada is null or extract(second from hora_aproximada) = 0),
  presenciou        boolean not null,          -- true: viu; false: soube por outra pessoa
  contato           text check (contato is null or char_length(contato) between 5 and 120),
  ip_hash           text not null check (ip_hash ~ '^[0-9a-f]{64}$'),
  user_agent        text check (user_agent is null or char_length(user_agent) <= 40),
  origem            text not null check (origem in ('politize-se')),
  versao            text check (versao is null or char_length(versao) <= 32),
  status            relato_status not null default 'novo'
);
create index if not exists relato_secao_chave on relato_secao (uf, zona, secao);
create index if not exists relato_secao_ip_janela on relato_secao (ip_hash, criado_em);
create index if not exists relato_secao_status on relato_secao (status);

-- Historico de moderacao: cada troca de status, com quem e quando (quem = papel do banco).
create table if not exists relato_moderacao (
  id         bigint generated always as identity primary key,
  relato_id  bigint not null references relato_secao (id),
  de         relato_status not null,
  para       relato_status not null,
  em         timestamptz not null default now(),
  papel      text not null default current_user
);

-- Conteudo imutavel: so o status muda; apagar e proibido para qualquer papel.
create or replace function relato_protege() returns trigger
language plpgsql as $$
begin
  if tg_op = 'DELETE' then
    raise exception 'registro imutavel: DELETE em relato_secao';
  end if;
  if (to_jsonb(new) - 'status') is distinct from (to_jsonb(old) - 'status') then
    raise exception 'registro imutavel: so o status de moderacao pode mudar';
  end if;
  if new.status is distinct from old.status then
    insert into relato_moderacao (relato_id, de, para) values (old.id, old.status, new.status);
  end if;
  return new;
end $$;
drop trigger if exists relato_secao_protege on relato_secao;
create trigger relato_secao_protege before update or delete on relato_secao
  for each row execute function relato_protege();

-- Relato chega sempre como novo.
create or replace function relato_novo() returns trigger
language plpgsql as $$
begin
  new.status := 'novo';
  new.criado_em := now();
  return new;
end $$;
drop trigger if exists relato_secao_novo on relato_secao;
create trigger relato_secao_novo before insert on relato_secao
  for each row execute function relato_novo();

drop trigger if exists relato_moderacao_imutavel on relato_moderacao;
create trigger relato_moderacao_imutavel before update or delete on relato_moderacao
  for each row execute function recusa_alteracao();

-- Registro atomico: limite de 5 relatos por ip_hash na ultima hora, conferido sob lock do proprio
-- ip_hash (duas chamadas simultaneas do mesmo IP nao passam juntas do limite). A Edge Function ja
-- validou o esquema; as restricoes da tabela conferem de novo.
create or replace function registrar_relato(p jsonb) returns jsonb
language plpgsql as $$
declare
  v_recentes integer;
  v_cadastro boolean;
begin
  if coalesce(p->>'ip_hash', '') = '' then
    return jsonb_build_object('status', 'rejeitado', 'motivo', 'sem ip_hash');
  end if;
  perform pg_advisory_xact_lock(hashtext('relato|' || (p->>'ip_hash')));
  select count(*) into v_recentes from relato_secao
   where ip_hash = p->>'ip_hash' and criado_em > now() - interval '1 hour';
  if v_recentes >= 5 then
    return jsonb_build_object('status', 'limite', 'motivo', 'limite de 5 relatos por hora');
  end if;
  select exists (select 1 from secao_ref
                  where uf = lower(p->>'uf') and zona = (p->>'zona')::int and secao = (p->>'secao')::int)
    into v_cadastro;
  insert into relato_secao (turno, uf, zona, secao, local_id, secao_no_cadastro, tipo, texto, hora_aproximada,
                            presenciou, contato, ip_hash, user_agent, origem, versao)
    values ((p->>'turno')::smallint, upper(p->>'uf'), (p->>'zona')::int, (p->>'secao')::int, nullif(p->>'local_id', ''),
            v_cadastro, (p->>'tipo')::relato_tipo, p->>'texto', nullif(p->>'hora_aproximada', '')::time,
            (p->>'presenciou')::boolean, nullif(p->>'contato', ''), p->>'ip_hash', nullif(p->>'user_agent', ''),
            p->>'origem', nullif(p->>'versao', ''));
  return jsonb_build_object('status', 'aceito');
end $$;

-- Contagens publicas, sem texto, contato, hora nem ip. Descartados ficam fora.
create or replace view v_relatos_resumo as
  select uf, tipo::text as tipo, turno, count(*)::integer as n
    from relato_secao where status <> 'descartado'
   group by uf, tipo, turno;

create or replace view v_relatos_secao as
  select uf, zona, secao, tipo::text as tipo, turno, count(*)::integer as n
    from relato_secao where status <> 'descartado'
   group by uf, zona, secao, tipo, turno;

-- search_path fixo; pgcrypto no esquema extensions (licao da 0004).
alter function relato_protege() set search_path = public, extensions;
alter function relato_novo() set search_path = public, extensions;
alter function registrar_relato(jsonb) set search_path = public, extensions;

-- Seguranca: RLS sem policy (negado para anon/authenticated); escrita so pela funcao.
alter table relato_secao enable row level security;
alter table relato_moderacao enable row level security;
revoke all on relato_secao, relato_moderacao from public, anon, authenticated;
revoke all on function registrar_relato(jsonb) from public, anon, authenticated;
revoke all on function relato_protege() from public, anon, authenticated;
revoke all on function relato_novo() from public, anon, authenticated;
grant execute on function registrar_relato(jsonb) to service_role;
grant select, insert on relato_secao to service_role;
grant usage, select on all sequences in schema public to service_role;
revoke all on v_relatos_resumo, v_relatos_secao from public, authenticated;
grant select on v_relatos_resumo, v_relatos_secao to anon;
-- TRUNCATE nao dispara o trigger de imutabilidade: nenhum papel da API o recebe.
revoke truncate, references, trigger on relato_secao, relato_moderacao from service_role;
revoke truncate, references, trigger on v_relatos_resumo, v_relatos_secao from service_role;
