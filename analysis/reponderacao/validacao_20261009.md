# Reorganização e simulador do 2º turno — 09/10/2026

O relatório principal abre em votos válidos e cenários. O arquivo do 1º turno e
o diário documental ficam em páginas próprias, com links antigos encaminhados.
O diário preserva 112 ondas e 18 versões anteriores da atualização documental.
Os dados legados mantêm os campos de diferença L−F; a exibição usa F−L.

## Central condicional

Datafolha (campo 06–08/10) e PoderData (05–07/10), peso igual entre casas e
normalização dos válidos por pesquisa. PNAD + propensões históricas Nexus +
presença relativa de Flávio multiplicada por 1,05. A hipótese foi escolhida
depois do 1º turno e não é uma taxa medida por candidato na urna.

- Flávio: 55,3237%; Lula: 44,6763%; diferença F−L: +10,6474 pp.
- Abstenção: 20,4217% do eleitorado; brancos/nulos: 4,6057% dos presentes.
- Sem probabilidade de vitória ou intervalo preditivo validado.
- Série descritiva de sete dias preservada separadamente; pode incluir campos
  anteriores ao encerramento do 1º turno.

## Vox Brasil

Relatório de 16 páginas, divulgação 09/10, registro BR-09623/2026.
Perfil de renda na p. 6; placar na p. 7; nenhum voto cruzado por renda.
Registro e questionário conferidos visualmente no PesqEle: o alvo cita Censo
2022 sem tabela, variável ou universo; a pergunta 4 não define o conceito de
renda. Resultado publicado preservado; nenhum ajuste imputado.

O PDF público coincide por SHA-256 com o recebido em Downloads. Fonte e hash
em `data/originals/vox_102026_09/fonte.json`; a transcrição pública do registro
é uma conferência visual, não o PDF original do questionário.

## Verificação

- `pytest -q`: 2.007 passaram, cinco omitidos por condições locais/dependências.
- Após os ajustes finais de apresentação e links: 54 testes relevantes passaram.
- Ruff e `git diff --check` passaram; sitemap consistente com as três rotas.
- Python e JavaScript reproduzem os resultados, inclusive extremos dos controles.
- Conservação de massas, sinal da presença relativa, saída desigual para B/N e
  compartilhamento de todos os parâmetros verificados.
- Playwright: presets, teclado, PNG 1200×630, copiar e reabrir link, dados e motor
  arquivados, versão ausente com erro explícito, restauração, âncoras antigas,
  telas de 360/390/768 px e conteúdo estático com JS desligado passaram.
- Sem IDs duplicados ou âncoras internas ausentes; GA uma vez por página e
  três cards sociais próprios conferidos.

Os snapshots publicados de dados e motores devem permanecer no acervo para
preservar os links. Rascunhos locais não publicados foram descartados.
