-- Leitura publica integral dos BUs aceitos: o conteudo do BU e publico por natureza e o CSV de
-- reproducao sai daqui, sem nenhum segredo no job que o gera.
create or replace view v_bu_publico as
  select b.id, b.recebido_em, b.uf, b.muni, b.zona, b.secao, b.agre, b.orig, b.turno, b.pleito, b.proc,
         b.fase, b.dtpl, b.idue, b.mdue, b.vers, b.aptos, b.comparecimento, b.faltosos, b.dtfc, b.hrfc,
         b.hash_final, b.assi, b.algoritmo, encode(b.cert_der, 'hex') as cert_hex, b.cert_fingerprint,
         b.cert_subject, b.cert_issuer, b.conteudo, b.cadeia_anterior, b.cadeia
    from bu b;
create or replace view v_bu_voto_publico as
  select v.bu_id, v.idel, v.cargo, v.partido, v.candidato, v.votos from bu_voto v;
create or replace view v_bu_cargo_publico as
  select c.bu_id, c.idel, c.cargo, c.tipo, c.apta, c.nomi, c.legc, c.bran, c.nulo, c.totc from bu_cargo c;
create or replace view v_envio_publico as
  select e.id, e.recebido_em, e.status, e.motivo, e.bu_id, e.versao_motor from envio e;
-- Totais por municipio para o painel e o mapa.
create or replace view v_totais_muni as
  select b.uf, b.muni, v.cargo, v.candidato, sum(v.votos)::bigint as votos, count(distinct b.id)::integer as n_secoes
    from v_bu_unico b join bu_voto v on v.bu_id = b.id
   group by b.uf, b.muni, v.cargo, v.candidato;
create or replace view v_cobertura_muni as
  select r.uf, r.muni, count(*)::integer as secoes_total, count(u.id)::integer as secoes_com_bu,
         sum(r.aptos)::bigint as aptos_total, sum(r.aptos) filter (where u.id is not null)::bigint as aptos_com_bu
    from secao_ref r
    left join v_bu_unico u on u.uf = r.uf and u.muni = r.muni and u.zona = r.zona and u.secao = r.secao
   group by r.uf, r.muni;
grant select on v_bu_publico, v_bu_voto_publico, v_bu_cargo_publico, v_envio_publico, v_totais_muni, v_cobertura_muni to anon;
