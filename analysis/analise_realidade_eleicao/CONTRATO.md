# Geografia do voto e triagem de auditoria

## Reprodução

Executar da raiz, com as fontes locais preservadas:

```sh
.venv/bin/python scripts/analise-realidade-dados.py
.venv/bin/python scripts/analise-realidade-auditoria.py
PYTHONPATH=scripts .venv/bin/python -m analise_realidade_eleicao.territorio
.venv/bin/python scripts/analise-realidade-build.py
```

O build publica `docs/analise_realidade_eleicao.html`, JSONs e CSVs. Os módulos
de apresentação ficam em `scripts/analise_realidade_eleicao/`. Não editar HTML
gerado. O dossiê complementar usa `scripts/apuracao-2t-2026-build.py`; não é
necessário recoletar a apuração para modificar os gráficos.

## Universos e denominadores

- Totalização: 5.571 municípios brasileiros, exterior excluído. Capitais:
  somente locais dentro da capital, mesmo quando a zona abrange outra cidade.
- Cortes de Flávio: estritos, calculados sobre contagens inteiras, antes de
  arredondar. A área dos círculos é proporcional à diferença absoluta de votos;
  uma escala compartilhada permite comparar os quatro mapas.
- Renda: aproximação por células PNAD 2025 × perfil eleitoral, não renda
  municipal diretamente observada. Não inferir voto individual ou causalidade.
- IPS Brasil 2026 não é IDHM nem riqueza. Preservar a falta de cobertura de Boa
  Esperança do Norte. Não apresentar IDHM municipal de 2010 como indicador atual.
- Homicídios ausentes permanecem ausentes. Lista FBSP significa documentação
  municipal de presença, não ausência comprovada fora dela nem domínio de bairro.

## Controle e influência territorial

Fonte: mapa GENI/UFF–Fogo Cruzado de 2024, versão publicada com relatório de 2025.
JSON público incorporado à página e biblioteca de renderização preservados em
`data/originals/analise_realidade_eleicao/`, com URLs e SHA-256. A publicação é
raster de 4.096 × 1.928 pixels; não foram obtidos os vetores originais.

O cruzamento usa a transformação Web Mercator de `degree2tile` do renderer
`addRasterImage`. Não usar interpolação linear da latitude: essa fórmula aparece
no popup da fonte, mas não corresponde ao posicionamento desenhado da imagem.
Cores exatas da legenda identificam grupos; pixels transparentes significam
“sem marcação”. Cor não reconhecida deve interromper o processamento.

Entram somente locais do RJ com coordenada cadastral, votos presentes e BUs
completos, dentro da extensão retangular da imagem. A janela não equivale ao
limite administrativo da Região Metropolitana. A malha municipal compacta do
IBGE em `apuracao/public/geo/mun/RJ.geojson` serve apenas de referência visual.

Controle e influência são partições separadas. Há sobreposição entre camadas:
nunca somar seus votos. Locais cadastrais distintos no mesmo prédio não são
duplicação de eleitores, mas não devem ser chamados de prédios distintos.

Sensibilidades de 100 e 300 m excluem locais próximos a outra classe. A distância
euclidiana ao pixel diferente usa a menor escala terrestre da janela, desconta
uma diagonal de pixel e considera fora da imagem como outra classe. Esses
cortes não são erros de geocodificação medidos nem intervalos de confiança. As
coordenadas não foram verificadas em campo; fronteiras e controles podem ter
mudado entre 2024 e 2026. O local de votação não revela residência, pertencimento
a grupo armado ou coação do eleitor.

## Investigação eleitoral

Uma hipótese deve identificar mecanismo, registros afetados e evidência que a
confirmaria ou refutaria. Mesma regra e mesma apresentação para ambos os lados.
Priorizar inconsistência material entre fontes independentes e impossibilidade
aritmética; usar anomalias estatísticas para ordenar investigação documental.

Concordância entre arquivos da mesma origem testa sua consistência, não certifica
o registro original da escolha do eleitor. Autenticidade criptográfica, software
executado, cadeia de custódia, cadernos e liberdade do voto têm escopos próprios.
A coleta paralela voluntária não é amostra probabilística representativa.

A triagem municipal compara previsões fora da amostra com e sem voto de primeiro
turno. Não estima probabilidade de fraude nem quantidade de votos adulterados.
Folds não são separação espacial; UF pode absorver um efeito estadual comum,
e o primeiro turno pode compartilhar eventuais problemas. Resultados descobertos
exploratoriamente requerem replicação e múltiplas comparações antes de alegar
significância. Uma transferência entre candidatos altera a margem em dois votos;
uma inclusão ou retirada altera em um. Aplicar somente a alterações demonstradas,
sem somar resíduos de modelo ou sinais sobrepostos.

## Validação

Testes `test_analise_realidade_*` cobrem denominadores, ausências, cortes, junções,
proveniência, modelo fora da amostra, projeção Mercator e partições territoriais.
`test_apuracao_2t_espelho.py` verifica a simetria de valores e intervalos e a
presença dos dois candidatos nos gráficos. Não transportar achados exploratórios
para uma conclusão de fraude ou integridade completa.
