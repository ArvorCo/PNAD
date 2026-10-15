# Quaest nacional, divulgação de 14/10/2026 — íntegra recebida em 15/10

## Documento e reprodução

Cópia fornecida pelo usuário em Downloads, preservada byte a byte em
`data/originals/quaest_102026_14/Quaest_14102026.pdf` e publicada em
`docs/fontes/quaest_14102026.pdf`. 152 páginas, 55.270.493 bytes, SHA-256
`112fd4b9b104d288394f27d98da77ec1bc2636cce144bb718f8986caf90c7592`.
O hash identifica a cópia; não é autenticação externa. Ambos os PDFs usam LFS.

- `python3 scripts/quaest-141026-integra.py --render-pages`: valida hash, renderiza
  152 WebPs e grava catálogo com título, texto nativo, tema e hash por imagem.
- `python3 scripts/quaest-141026-build.py`: exporta temas/contas, atualiza a
  proveniência da ficha e gera o dossiê. Normalmente não precisa renderizar PDF.
- `python3 scripts/reponderacao-pnad.py calcular --hoje 2026-10-15` e
  `python3 scripts/reponderacao-build.py`: propagam a revisão documental às
  centrais. Perfil e votos são os mesmos; os resultados numéricos não mudam.
- Cards: `python3 scripts/social-cards.py --only quaest_14102026 reponderacao_pnad reponderacao_pnad_log hub`.

As 23 fichas em `temas/` têm formulação publicada, universo, totais/recortes
identificados, leitura, limites e páginas. Cobertura temática completa não significa
transcrição numérica de todas as células históricas. As séries e demais recortes
continuam disponíveis nas 152 páginas originais. Valores foram lidos nas imagens;
texto nativo e OCR servem para localizar, nunca substituir a conferência visual.
Ausência de rótulo não vira zero. Totais inteiros são arredondados.

## Transferência, memória e denominadores

P. 19: a linha de 22% mistura branco, nulo e quem não foi votar. Intenção atual
nesse grupo: Flávio 38%, Lula 43%, indecisos 2%, branco/nulo/não vai votar 17%.
São respostas declaradas, não distribuição algorítmica de abstencionistas.
Produtos dos números arredondados: 8,36 pp F e 9,46 pp L sobre o total; saldo
1,10 pp L. As linhas de retenção/troca entre finalistas e NS/NR do voto passado
não são mostradas; não existe matriz completa para conferir o fechamento.
“Outros” tem menos de 1%, sem peso exato: preservar null.

P. 129: memória F35/L34/BN-ausência22/NSNR3. Comparar com **todos os aptos**,
Brasil sem ZZ, nunca com votos válidos. Fonte oficial compacta já arquivada em
`analysis/apuracao_2026/dados/presidente.json`, soma das 27 UFs, com hash e
snapshot gravados no JSON da auditoria. F35,4565/L34,0382 e 24,6210% sem voto
válido (20,8421% ausência; 3,7789% BN). A proximidade agregada contraria a alegação
de enorme desaparecimento dos ausentes, mas não identifica calibração por voto
passado, representatividade dos grupos nem ausência futura.

A sensibilidade reduz proporcionalmente apenas as intenções F/L do grupo misto,
com restante do topline fixo. Retenção de 100% reproduz 46/44; 0% dá 37,64/34,54,
ou 52,1474% F entre os dois. Não distingue ausência de voto inválido, não estima
comparecimento, não tem IC e não entra nas centrais.

## Eleitor provável e ausência

Não se localizou regra publicada de likely voter na íntegra (método pp. 2–4,
intenção pp. 17–29, interesse pp. 117–118, memória p. 129, catálogo completo)
ou na transcrição arquivada de BR-08729/2026. Isso não demonstra inexistência
de tratamentos internos não divulgados. O questionário de 27 páginas foi
visualizado na consulta anterior, mas não arquivado integralmente: filtros e
sequência não estão completamente auditados.

O universo declarado é de eleitores brasileiros de 16 anos ou mais. Não há
escore, limiar, tamanho filtrado, taxa prevista ou validação publicada. Os 9%
juntam BN e intenção de faltar: não são previsão de abstenção nem implicam 91%
de comparecimento. Quem declara candidato também pode faltar. Uma abstenção
futura menor que a anterior não é matematicamente impossível; falta uma ponte
publicada entre intenção e voto efetivo.

Interesse: 51/31/17/1 (muito/pouco/nada/NSNR), p. 117. Voto por interesse p. 29:
50/47, 45/41, 39/37. Selecionar só os muito interessados dá 51,5464% F entre
os dois, contra 51,1111% no total. É filtro ilustrativo sem validação, não
likely voter da Quaest ou recomendado pela Arvor. O voto do 1% NSNR não é
publicado e não é imputado. Firmeza da escolha (pp. 31–32) não é presença.

## Perfil, calibração e comparabilidade

O perfil 31/42/27 está publicado na p. 147, sob a seção “Perfil da amostra”
(p. 143). A ficha passa de `cota_registrada` a `perfil_publicado`, mantendo
`etapa_ponderacao` não informada: não há indicação antes/depois dos pesos,
bases brutas/ponderadas, distribuição dos pesos, tamanho efetivo ou não resposta
à renda. P. 3 declara “MrP ou rake”, sem especificação operacional. A conta PNAD
segue 45,398 F / 44,531 L, ancorada no topline e condicionada à adequação dessa
margem aos cruzamentos da p. 24. Mesma edição PNADC anual 2025 declarada; não
alegar uso de PNAD antiga.

O PDF agrega Centro-Oeste/Norte nos cruzamentos, enquanto o G1 os separa;
conservar fontes e dimensões separadas. O cenário de 2T deixa de hipotético em
03/10 para efetivo em 14/10 (p. 17). Firmeza e expectativa mudam de pergunta
(1T→2T), pp. 31 e 62. Não interpretar salto da expectativa como votos ganhos,
probabilidade de vitória ou série de pergunta literalmente constante.

## Outros limites editoriais

- Potencial pergunta “poderia votar”, mas legenda usa “votaria”; não é intenção
  efetiva nem teto validado. Rejeição é independente, não partição de 100%.
- Medo compara Lula à família Bolsonaro; motivos têm bases condicionais distintas.
- Propostas pp. 114–115: manter cinco respostas. Aprovar após ler não implica
  conhecimento prévio. A página não identifica autoria por item; recortes com
  células não rotuladas não são completados por diferença/adivinhação.
- Renda versus preços é percepção, não renda real medida por PNAD/IPCA.
- Preocupações p. 120 mostra apenas seis mais citadas, soma 94%; os 6% omitidos
  não são automaticamente indecisos. Série sem onda de 03/10.
- Escolha alternativa, momento e motivos do 1T são memória retrospectiva;
  bases de roteamento não publicadas. Não inferir causalidade ou presença.
- Subgrupos de candidatos pequenos têm margens muito altas (p. 4); margens
  não identificam bases, efeito de desenho ou significância de diferenças.
- A transcrição PesqEle anterior permanece intacta e datada: indisponibilidade
  observada às 01h12 não descreve o portal agora. Nenhum anexo territorial novo
  veio neste PDF. Não inferir irregularidade pela ausência do documento.
