# Totalização paralela por QR do BU

Biblioteca, banco e função de ingestão da totalização paralela do 2º turno de 25/10/2026.
A pessoa lê os QR do boletim de urna impresso em `docs/totalizacao.html`; a Edge Function
`receber-bu` verifica e grava; `scripts/totalizacao-exportar.py` publica agregados e CSV em
`docs/assets/totalizacao_dados/`; `docs/totalizacao_painel.html` mostra cobertura e placar.

## O que a conta prova

Transmissão e soma: o BU impresso na seção contra o BU publicado pelo TSE e contra a
totalização. Não prova o que acontece dentro da urna. A amostra é de quem enviou; o total parcial
é soma dos BUs recebidos, nunca projeção.

## Biblioteca (`src/`)

`lerBoletim(qrTexts, opcoes)` recebe os textos dos QR (`QRBU:i:n` e `QRCE:i:2`, em qualquer
ordem) e devolve o boletim interpretado, a cadeia SHA-512 conferida, a assinatura da urna
(ECDSA P-521 nas UE2013/2015, EdDSA Ed521 nas UE2020/2022), o certificado da urna e sua cadeia
até a AC do TSE (`src/qrbu/ac/`), e os problemas estruturais. `PERFIL_2T_2026` traz os valores
esperados do 2º turno (PROC 1219, PLEI 3221, DTPL 20261025, FASE O, IDEL 6258 e 6260).

```bash
bun install
bun test
bun run typecheck
bun run lint
```

Os dez exemplos oficiais do TSE (`tests/fixtures/exemplos_tse_2026.json`) verificam de ponta a
ponta; as fontes e seus SHA-256 estão em `data/originals/tse_qrbu_2026/fonte.json`.

## Banco (`supabase/migrations/`)

Aplicar na ordem com a API de gestão (`POST /v1/projects/<ref>/database/query`) ou pelo CLI.
Regras: RLS ligado sem policy para `anon` (tudo negado); leitura pública só pelas views `v_*`;
`envio`, `bu`, `bu_cargo`, `bu_voto` imutáveis por trigger; `bu` encadeia hashes;
`registrar_envio(jsonb)` faz dedup, conflito e gravação atômica. Nenhum segredo entra no
repositório: a chave publicável é pública por desenho e `service_role` só existe na função.

## Função (`supabase/functions/receber-bu/`)

```bash
supabase functions deploy receber-bu --project-ref brvjvizqbyfamtxogvqf --use-api --no-verify-jwt
supabase secrets set --project-ref brvjvizqbyfamtxogvqf MODO=oficial
```

Segredos: `MODO` (`teste` aceita FASE S/T; `oficial` exige o perfil do 2º turno), `SAL_IP`
(sal do hash de IP para o limite de taxa) e `TURNSTILE_SECRET` (opcional; sem ele, só o limite por
IP). A chave `SUPABASE_SERVICE_ROLE_KEY` é injetada pela plataforma.

## Conferência com o TSE

`python3 scripts/totalizacao-conferir-tse.py` compara cada BU aceito (fase O) com o `-bu.dat` ou
`-busa.dat` que o TSE publica para a seção (pleito do próprio BU), decodificado com
`apuracao/scripts/secoes/bu.asn1`, voto a voto: nominais por número, legenda por partido,
brancos, nulos, comparecimento e aptos. Grava `conferencia_tse.json` e `.csv` em
`docs/assets/totalizacao_dados/`; o painel mostra o bloco "Conferência com o TSE". Retomável:
seções já iguais ou divergentes com o mesmo hash não são refeitas (`--refazer` força). Roda no
workflow antes da exportação. Igualdade comprova transmissão e soma, nunca o interior da urna.

## Antes de 25/10

1. `supabase secrets set MODO=oficial`.
2. Esvaziar os envios de teste (`truncate envio, bu, bu_cargo, bu_voto restart identity`).
3. Criar o site Turnstile e preencher `turnstileSiteKey` em `docs/assets/totalizacao/config.js`
   e `TURNSTILE_SECRET` nos segredos.
4. Conferir que o workflow `totalizacao.yml` está habilitado (ele só agenda de 25 a 28/10).
