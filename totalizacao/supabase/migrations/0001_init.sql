-- Totalizacao paralela por QR do BU (2o turno 2026).
-- Principios: o navegador nunca escreve; so a Edge Function (service_role) insere; tabelas de
-- registro sao imutaveis (sem UPDATE/DELETE para qualquer papel); leitura publica so por views
-- agregadas. Toda linha aceita guarda o conteudo integral do QR, a assinatura e o certificado
-- da urna, para reverificacao independente a partir do CSV publicado.

create extension if not exists pgcrypto;

-- Referencia de secoes (cadastro TSE): denominador da cobertura. Carga pelo job, leitura publica.
create table if not exists secao_ref (
  uf        char(2) not null,
  muni      integer not null,
  zona      integer not null,
  secao     integer not null,
  aptos     integer,
  local     integer,
  nome_muni text,
  primary key (uf, muni, zona, secao)
);

-- Log imutavel de envios (aceitos ou nao).
create table if not exists envio (
  id            bigint generated always as identity primary key,
  recebido_em   timestamptz not null default now(),
  aparelho_hash text,                 -- pseudonimo do aparelho (hash), nunca identificador pessoal
  ip_hash       text,                 -- sha256(ip + sal do dia), so para limite de taxa
  qr_textos     text[] not null,      -- textos brutos dos QR (QRBU e QRCE)
  status        text not null check (status in ('aceito','repetido','conflito','rejeitado')),
  motivo        text,
  bu_id         bigint,
  versao_motor  text not null
);
create index if not exists envio_recebido_em on envio (recebido_em);
create index if not exists envio_ip_janela on envio (ip_hash, recebido_em);

-- BU aceito: QR integro, cadeia SHA-512 conferida, assinatura valida pelo certificado da urna.
create table if not exists bu (
  id              bigint generated always as identity primary key,
  recebido_em     timestamptz not null default now(),
  envio_id        bigint not null,
  uf              char(2) not null,
  muni            integer not null,
  zona            integer not null,
  secao           integer not null,
  agre            text,
  orig            text not null check (orig in ('VOTA','RED','SA')),
  turno           smallint not null check (turno in (1,2)),
  pleito          integer not null,
  proc            integer not null,
  fase            char(1) not null check (fase in ('O','S','T')),
  dtpl            date not null,
  idue            bigint not null,            -- numero de serie da urna
  mdue            text,                       -- modelo da urna (certificado)
  vers            text,
  aptos           integer check (aptos >= 0),
  comparecimento  integer check (comparecimento >= 0),
  faltosos        integer check (faltosos >= 0),
  dtfc            date,
  hrfc            time,
  hash_final      text not null check (hash_final ~ '^[0-9A-F]{128}$'),
  assi            text not null check (assi ~ '^[0-9A-F]+$'),
  algoritmo       text not null check (algoritmo in ('ECDSA P-521','EdDSA Ed521')),
  cert_der        bytea not null,
  cert_fingerprint text not null,             -- sha256 hex do certificado DER
  cert_subject    text,
  cert_issuer     text,
  conteudo        text not null,              -- secao de conteudo remontada, inclusive HASH:
  cadeia_anterior text,                       -- hash de encadeamento da linha anterior
  cadeia          text not null,              -- sha256(cadeia_anterior || hash_final || assi)
  check (comparecimento is null or aptos is null or comparecimento <= aptos),
  unique (uf, muni, zona, secao, hash_final)
);
create index if not exists bu_secao on bu (uf, muni, zona, secao);
create index if not exists bu_idue on bu (idue);

-- Resumo por cargo dentro de cada BU.
create table if not exists bu_cargo (
  bu_id   bigint not null references bu (id),
  idel    integer not null,
  cargo   smallint not null,
  tipo    smallint not null check (tipo in (0,1,2)),
  apta    integer not null check (apta >= 0),
  nomi    integer not null check (nomi >= 0),
  legc    integer not null default 0 check (legc >= 0),
  bran    integer not null check (bran >= 0),
  nulo    integer not null check (nulo >= 0),
  totc    integer not null check (totc >= 0),
  primary key (bu_id, idel, cargo),
  check (nomi + legc + bran + nulo = totc),
  check (totc <= apta)
);

-- Votos por candidato (ou legenda) dentro de cada cargo.
create table if not exists bu_voto (
  bu_id     bigint not null references bu (id),
  idel      integer not null,
  cargo     smallint not null,
  partido   integer,
  candidato text not null,       -- numero do candidato; 'LEGP<partido>' para legenda
  votos     integer not null check (votos >= 0),
  primary key (bu_id, idel, cargo, candidato),
  foreign key (bu_id, idel, cargo) references bu_cargo (bu_id, idel, cargo)
);

-- Imutabilidade: nenhum papel altera ou apaga registro.
create or replace function recusa_alteracao() returns trigger
language plpgsql as $$
begin
  raise exception 'registro imutavel: % em %', tg_op, tg_table_name;
end $$;

do $$
declare t text;
begin
  foreach t in array array['envio','bu','bu_cargo','bu_voto'] loop
    execute format('drop trigger if exists %I_imutavel on %I', t, t);
    execute format('create trigger %I_imutavel before update or delete on %I for each row execute function recusa_alteracao()', t, t);
  end loop;
end $$;

-- Soma dos votos nominais deve bater com NOMI (+ LEGC) do cargo. Conferido no fim da transacao.
create or replace function confere_soma_cargo() returns trigger
language plpgsql as $$
declare
  c record;
  s_nom integer;
  s_leg integer;
begin
  select * into c from bu_cargo where bu_id = new.bu_id and idel = new.idel and cargo = new.cargo;
  select coalesce(sum(votos) filter (where candidato not like 'LEGP%'), 0),
         coalesce(sum(votos) filter (where candidato like 'LEGP%'), 0)
    into s_nom, s_leg
    from bu_voto where bu_id = new.bu_id and idel = new.idel and cargo = new.cargo;
  if s_nom <> c.nomi or s_leg <> c.legc then
    raise exception 'soma de votos nao bate com o resumo do cargo % (bu %): nominais % x %, legenda % x %',
      new.cargo, new.bu_id, s_nom, c.nomi, s_leg, c.legc;
  end if;
  return null;
end $$;
drop trigger if exists bu_voto_soma on bu_voto;
create constraint trigger bu_voto_soma after insert on bu_voto
  deferrable initially deferred for each row execute function confere_soma_cargo();

-- Encadeamento de hashes: cada BU aceito aponta para o anterior; serializado por lock.
create or replace function encadeia_bu() returns trigger
language plpgsql as $$
declare ant text;
begin
  perform pg_advisory_xact_lock(42);
  select cadeia into ant from bu order by id desc limit 1;
  new.cadeia_anterior := ant;
  new.cadeia := encode(digest(coalesce(ant, '') || new.hash_final || new.assi, 'sha256'), 'hex');
  new.cert_fingerprint := encode(digest(new.cert_der, 'sha256'), 'hex');
  return new;
end $$;
drop trigger if exists bu_encadeia on bu;
create trigger bu_encadeia before insert on bu for each row execute function encadeia_bu();

-- Secoes com mais de um BU distinto: ficam fora dos totais e aparecem como conflito.
create or replace view v_conflito as
  select uf, muni, zona, secao, count(*) as n_bus, array_agg(hash_final order by id) as hashes
    from bu where fase = 'O'
   group by uf, muni, zona, secao having count(*) > 1;

-- Um BU por secao (o unico aceito), so secoes sem conflito e fase oficial.
create or replace view v_bu_unico as
  select b.* from bu b
   where b.fase = 'O'
     and not exists (select 1 from v_conflito c where c.uf = b.uf and c.muni = b.muni and c.zona = b.zona and c.secao = b.secao);

create or replace view v_totais_uf as
  select b.uf, v.cargo, v.candidato, sum(v.votos)::bigint as votos, count(distinct b.id)::integer as n_secoes
    from v_bu_unico b join bu_voto v on v.bu_id = b.id
   group by b.uf, v.cargo, v.candidato;

create or replace view v_totais_br as
  select v.cargo, v.candidato, sum(v.votos)::bigint as votos, count(distinct b.id)::integer as n_secoes
    from v_bu_unico b join bu_voto v on v.bu_id = b.id
   where v.cargo = 1
   group by v.cargo, v.candidato;

create or replace view v_resumo_cargo_uf as
  select b.uf, c.cargo, sum(c.apta)::bigint as aptos, sum(c.totc)::bigint as comparecimento,
         sum(c.bran)::bigint as brancos, sum(c.nulo)::bigint as nulos, sum(c.nomi)::bigint as nominais,
         count(*)::integer as n_secoes
    from v_bu_unico b join bu_cargo c on c.bu_id = b.id
   group by b.uf, c.cargo;

create or replace view v_cobertura_uf as
  select r.uf,
         count(*)::integer as secoes_total,
         count(u.id)::integer as secoes_com_bu,
         (select count(*) from v_conflito c where c.uf = r.uf)::integer as secoes_em_conflito,
         sum(r.aptos)::bigint as aptos_total,
         sum(r.aptos) filter (where u.id is not null)::bigint as aptos_com_bu
    from secao_ref r
    left join v_bu_unico u on u.uf = r.uf and u.muni = r.muni and u.zona = r.zona and u.secao = r.secao
   group by r.uf;

create or replace view v_estatisticas as
  select (select count(*) from envio) as envios,
         (select count(*) from envio where status = 'aceito') as envios_aceitos,
         (select count(*) from envio where status = 'rejeitado') as envios_rejeitados,
         (select count(*) from bu where fase = 'O') as bus_oficiais,
         (select count(*) from v_conflito) as secoes_em_conflito,
         (select max(recebido_em) from envio) as ultimo_envio,
         now() as consultado_em;

-- Seguranca: RLS ligado em tudo e nenhuma policy para anon/authenticated (negado por padrao).
alter table secao_ref enable row level security;
alter table envio enable row level security;
alter table bu enable row level security;
alter table bu_cargo enable row level security;
alter table bu_voto enable row level security;
revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from anon, authenticated;
alter default privileges in schema public revoke all on tables from anon, authenticated;
alter default privileges in schema public revoke all on sequences from anon, authenticated;
alter default privileges in schema public revoke all on functions from anon, authenticated;
-- Views agregadas sao a unica leitura publica. security_invoker=false: a view le as tabelas como dona.
grant select on v_totais_uf, v_totais_br, v_resumo_cargo_uf, v_cobertura_uf, v_estatisticas, v_conflito to anon;
