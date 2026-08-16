# Quaest / Globo, 14 de agosto de 2026

Arquivos oficiais da pesquisa presidencial Quaest registrada no TSE sob
`BR-06773/2026`, com campo de 10 a 13 de agosto de 2026 e divulgação em 14 de
agosto de 2026.

## Arquivos

- `relatorio.pdf`: relatório público, 197 páginas.
- `registro-tse.pdf`: ficha do PesqEle, custo declarado de R$ 314.628,00.
- `questionario.pdf`: instrumento registrado, 23 páginas e 53 perguntas numeradas.
- `anexo-territorial.pdf`: 120 municípios, 334 setores e 2.004 entrevistas.
- `declaracao.pdf`: declaração anexada ao registro.
- `nota-fiscal-1.pdf` a `nota-fiscal-6.pdf`: três parcelas divididas em partes
  iguais entre Globo Comunicação e Participações S/A e Editora Globo S/A.
- `quaest_bairros_140826.csv`: transcrição auditável do anexo, com validação do
  geocódigo de 15 dígitos na malha do Censo 2022 do IBGE.

Os seis documentos fiscais não representam seis cobranças desta rodada. São as
duas metades de três parcelas de um contrato para sete pesquisas. O contrato
fecha em R$ 2.457.876,00: seis pesquisas de R$ 314.628,00 e uma de R$ 570.108,00.

## Reprodução

```bash
python3 scripts/quaest-globo-140826-audit.py --refresh-ibge
python3 scripts/quaest-globo-140826-estrategia.py
python3 scripts/quaest-globo-140826-embed.py
python3 scripts/quaest-globo-140826-thread.py
pytest -q tests/
```

A ordem importa: `embed` copia as duas bases já geradas para dentro do HTML do
dossiê. Sem esse passo a página continua desenhando pelos arquivos JSON, o que
funciona em servidor e falha quando alguém abre o arquivo direto do disco.

O primeiro script confere os documentos, grava os hashes SHA-256, refaz as
contas do dossiê e gera:

- `docs/assets/quaest_globo_140826_data.json`
- `docs/assets/quaest_globo_140826_territory.json`

O segundo transcreve os cruzamentos das páginas 17, 21, 25, 28, 41, 72, 76, 79,
92, 96, 99, 101, 155, 158, 159 e 195 e escreve a camada estratégica em
`docs/assets/quaest_globo_140826_estrategia.json`: a equação do turno único
`12t + d + 0,5g > 10`, o prêmio de inevitabilidade, a recomposição da rejeição
por bloco político, a geografia da terceira via e o cruzamento com o plano de
governo registrado.

O terceiro monta `docs/quaest_globo_140826_thread.html` a partir do texto em
`docs/threads/quaest_globo_140826_thread.md`.

Os PDFs são fontes locais pesadas e continuam ignorados pelo Git. O README e o
CSV territorial são os artefatos leves versionáveis desta pasta.
