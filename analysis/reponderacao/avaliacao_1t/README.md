# Score Arvor e autoria dos válidos · revisão de 21/10/2026

A auditoria anterior chamava a normalização dos totais de “publicado em válidos”.
Isso não representa necessariamente o valor divulgado pela casa. Esta revisão
preserva o arquivo histórico e acrescenta uma avaliação com autoria explícita ao
relatório corrente e a `docs/assets/reponderacao_score_arvor.json`.

## Regra do score

EAM F/L = (|F estimado − F urna| + |L estimado − L urna|) / 2, em pontos percentuais.
Menor é melhor. Não é nota de 0 a 10 nem percentual de acerto. Usa as porcentagens
válidas efetivamente publicadas, com todas as candidaturas no denominador, sem
renormalizar os dois líderes ou corrigir arredondamentos. Mede apenas os líderes,
não o erro de todas as candidaturas. O erro da vantagem F−L também é exibido, mas
não ordena: erros de mesmo sinal poderiam cancelar-se.

Última onda comparável com campo encerrado entre 25/09 e 04/10 e divulgação antes
da votação. Dez casas têm válidos confirmados. Empates no EAM arredondado a 0,01 pp
compartilham posição; o nome desempata apenas a apresentação. As demais ficam ao
final, sem score e sem penalidade. Conversões Arvor dos totais são diagnósticos
separados. Não estimamos competência permanente com uma eleição, nem usamos esse
score para alterar pesos ou centrais do segundo turno.

A nota documental de setembro permanece separada e intacta. Ela mede as evidências
públicas segundo dez critérios e não é uma estimativa de erro eleitoral.

## Evidência

`publicados.json` preserva valores, URL, página, hash e método. Atlas (p. 15) e MDA
(p. 9) foram conferidas visualmente; Gerp, Nexus, Futura, G1/Quaest e Folha têm as
fontes originais já arquivadas. PoderData e Real Time/R7 publicaram os válidos nas
matérias. Quaest declara modelo próprio de eleitor provável. Palver declara no
release da onda 6, pp. 1–2, que não publica votos válidos; não atribuímos a ela a
conversão Arvor. Indexa, Meio/Ideia e Vox: válidos não localizados nas fontes
consultadas, sem afirmar que nunca foram publicados.

A Veritá foi adicionada especificamente a esta avaliação: consolidação das 27 UFs,
campo 20–25/09, no catálogo oficial desde 01/10 (`created_at`, também presente no
catálogo arquivado em 08/10). O PDF da p. 7 traz totais 44,27/43,79 e válidos
45,14/44,65 F/L. Não se confunde com o cenário de segundo turno divulgado em 05/10,
que permanece excluído. A consolidação usa eleitorado estadual e exclui exterior;
a referência oficial comum inclui exterior. A diferença de universo está declarada.
A data do catálogo documenta a divulgação; não constitui prova criptográfica de que
o conteúdo remoto nunca foi substituído.

Datafolha: a matéria da Folha divulga 42/45 F/L, enquanto normalizar os totais do
painel G1 produz outros valores. Os candidatos informados na matéria somam 98%.
Registramos a inconsistência sem “consertar” o resultado publicado. PoderData soma
101% e MDA 100,1% por arredondamento, também preservados.

## Nosso lado da comparação

`arvor_pre_urna.json` extrai o objeto Git `1688f007:docs/assets/reponderacao_validos.json`,
com hash dos bytes originais. Sete casas tinham projeção completa. A interface desse
commit iniciava em modelo + cenário central (primeira opção do seletor). A presença
condicional Nexus era transportada entre casas; indecisos eram proporcionais e não
alteravam a razão final dos válidos. Preservamos central e quatro sensibilidades,
sem escolher depois da urna aquela de menor erro e sem aplicar o resíduo pós-urna
+3,8%. Nenhuma projeção é inventada para casas sem cruzamentos completos.

A PNAD simples aparece também nos totais e nos válidos. Diferenças entre o valor
publicado da casa e o modelo completo Arvor misturam renda, presença, hipóteses e
arredondamento; não são atribuídas inteiramente à reponderação. A Central Projeção
Arvor agregada, com recência e tendência, é mostrada separadamente das projeções
individuais. Todos os arquivos de previsão anteriores e as centrais atuais ficam
intactos.

Gerar: `python scripts/reponderacao-build.py --skip-home`.
Verificar: `pytest -q tests/test_reponderacao_score_arvor.py`.
