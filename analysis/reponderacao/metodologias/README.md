# Comparativo metodológico, 21/09/2026

Uma ficha por instituto, referente à última onda nacional disponível no acervo nessa data. Cada JSON reúne as declarações do registro PesqEle, o confronto com o relatório da mesma onda e a justificativa dos dez critérios da nota documental. Não transferir automaticamente a ficha para uma onda nova.

As fontes públicas estão em `docs/fontes/reponderacao_metodologias/`: questionários completos e excertos integrais das três seções metodológicas do registro. O HTML original, o texto completo e a proveniência permanecem no acervo local em `data/originals/reponderacao_metodologias_20260921/`. Hashes dos documentos de origem estão nos manifestos.

## Reprodução

```sh
# Gera a página, as notas e as comparações, sem alterar a capa:
python3 scripts/reponderacao-build.py --skip-home

# Recria os excertos públicos a partir dos arquivos locais e valida seus hashes:
python3 scripts/reponderacao-registros.py --export-only

# Consulta novamente os registros dos manifestos e arquiva questionários:
python3 scripts/reponderacao-registros.py
```

Reconsultar o TSE pode retornar retificações. A exportação rejeita fontes cujo hash difere do manifesto, exigindo revisão editorial antes de substituir o material que sustentou a nota. Os recortes de relatório preservam as páginas de origem indicadas na ficha, embora sua paginação interna comece em 1.

## Interpretação

- A nota vai de 0 a 10 e mede qualidade documental/auditabilidade no acervo consultado: 1 por critério atendido, 0,5 parcial, 0 não localizado. Não é certificação da AAPOR, medida de erro eleitoral nem ranking permanente. A rubrica e suas referências estão em `scripts/reponderacao-metodos.py` e na página.
- Modalidade de coleta e recrutamento são variáveis distintas. A seleção final por cotas permanece identificada mesmo quando etapas anteriores têm sorteio.
- O voto de 2022 pode ser perguntado sem entrar nos pesos. Declarações genéricas sobre comportamento eleitoral anterior não comprovam calibração especificamente pelo segundo turno.
- O sinal relativo usa somente placares publicados de Lula × Flávio, normalizados pelos votos válidos dos dois. Cada onda é comparada à mediana de pelo menos três outros institutos, uma onda mais próxima por casa, em até sete dias da data central de campo. O resumo por instituto é a mediana dos desvios em 45 dias, não uma estimativa contra a verdade.
- A faixa de ±2 pp é editorial, sem significado de intervalo de confiança. Menos de três ondas recebe aviso. Ondas sem cruzamento de renda entram; revisões substituem a mesma amostra. Não há imputação de preferência política do instituto.

Testes do pareamento, versões, janelas e integridade das fontes: `tests/test_reponderacao_metodologias.py`. A cobertura do acervo não implica levantamento exaustivo de todas as pesquisas existentes.
