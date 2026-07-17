# Quaest jul/2026 — a dupla invisibilidade do crime organizado

## Síntese

Testei a hipótese de que pesquisas domiciliares evitam áreas dominadas pelo crime
organizado, aplicada à Genial/Quaest (registro TSE BR-07181/2026, campo 10 a 13 de
julho de 2026, 2.004 entrevistas, 334 setores por rodada). O teste tem duas pernas.

### Perna 1 — Cobertura territorial (Fato aritmético)

Classifiquei cada um dos 667 setores distintos das rodadas de junho e julho pelo
geocódigo de 15 dígitos, cruzando com o Censo 2022 do IBGE (arquivo básico de
agregados por setor, coluna `CD_TIPO = 1` = Favela e Comunidade Urbana).

A ficha declara sorteio de setores por PPT (Probabilidade Proporcional ao Tamanho)
sobre a população do Censo 2022. Logo o esperado de setores de favela em cada
município é a fração da população municipal que vive em setores FCU (share ponderado
por população), e não a fração simples de setores.

**Nacional (jun+jul agregados):** 47 setores de favela observados contra 55,98
esperados. Déficit de ~9 setores (~16%), `P(X ≤ 47) = 0,090`. Sub-representação leve
e não significativa. Não há zero absoluto nem exclusão sistemática.

**Por capital (observado / esperado):**
- São Paulo: 6 / 6,6 — praticamente no alvo (15,1% da população em favela)
- Salvador: 4 / 3,4 — acima do esperado (42,7%)
- Rio de Janeiro: 4 / 5,2 — pouco abaixo (21,7%)
- Belém: 1 / 3,4 — o déficit mais visível (57,2%, `P ≤ obs = 0,056`)
- Belo Horizonte: 0 / 1,3; Brasília: 0 / 0,7 — zeros, mas com esperado baixo

O déficit se concentra em Belém, BH, Brasília e Rio. SP no alvo e Salvador acima
**derrubam a versão forte** da hipótese. Ressalva decisiva: isto audita o **sorteio
publicado**, não o **campo**. Substituições de domicílio por segurança, se
ocorressem, não são observáveis sem microdados. A ficha não declara nada sobre isso.

### Perna 2 — Agenda temática (Fato de omissão)

Varredura dos 101 itens do questionário registrado (Quaest_Questionario_072026.pdf):
**zero** ocorrências de segurança, violência, facção, tráfico, PCC, milícia, assalto,
roubo ou homicídio. A palavra "crime" aparece 1 vez (crimes financeiros de Vorcaro /
Banco Master); "Polícia Federal" 2 vezes (roteiros dos blocos Master e Jaques Wagner).
No mesmo instrumento: 22 menções a Michelle, 17 a tarifa.

Contexto verificado: Datafolha/FBSP (mai/2026) mede **41,2% dos brasileiros de 16+
(≈68,7 milhões)** vendo facções ou milícias no próprio bairro, 55,9% nas capitais;
61,4% dizem que os grupos influenciam as regras locais. Mesma abordagem domiciliar,
universo 16+ e n≈2.004 da Quaest — espelho metodológico: dá para medir o tema.
Segurança pública é o problema #1 do país em 2026 e superou a corrupção pela primeira
vez na série Nexus/BTG, com preocupação igual entre eleitores de Lula e da direita.

## Veredito calibrado

- **Hipótese forte (evitar favelas no sorteio): refutada pela aritmética.** A amostra
  inclui favelas a ~84% da taxa esperada. Déficit leve, não conclusivo. Inferência.
- **Achado que sobrevive: agenda por omissão.** Ausência total de segurança no
  instrumento é Fato. A razão é Hipótese (rodada focada em corrida e economia, leitura
  benigna; ou recorte conveniente ao contratante). Efeito no placar não calculado.
- Nada disto é exclusivo da Quaest: qualquer domiciliar enfrenta acesso restrito. O
  diferencial auditável seria **declarar** substituições e segurança — a ficha não o faz.

## Fontes
IBGE Censo 2022 (Agregados por Setores, básico BR; FCU: 12.348 favelas, 16,4 mi,
8,1% da população); Datafolha/FBSP mai/2026; FBSP Anuário 2025; ficha PesqEle
BR-07181/2026; Quaest_Questionario_072026.pdf. Reprodução:
`python3 scripts/quaest-favela-audit.py` → `docs/assets/quaest_0726_favelas.json`.

---

## Post (primeira pessoa, ≤2000 chars)

Testei uma hipótese incômoda na Genial/Quaest de julho: pesquisa domiciliar evita favela?

Peguei os 667 setores sorteados nas duas rodadas, classifiquei cada geocódigo pelo Censo 2022 do IBGE e comparei com o que o próprio desenho da Quaest prevê. A ficha diz que sorteia setores por probabilidade proporcional à população. Então o esperado de setores de favela é a fatia da população municipal que mora em favela.

Resultado nacional: 47 setores de favela sorteados contra 55,98 esperados. Déficit de uns 9, cerca de 16%, com probabilidade 0,090. É uma sub representação leve, não é exclusão sistemática, e não é zero. São Paulo saiu no alvo (6 contra 6,6), Salvador saiu acima (4 contra 3,4). Isso derruba a versão forte da hipótese. O buraco existe em Belém, Belo Horizonte, Brasília e Rio, mas é pequeno demais para cravar intenção.

Importante: isso audita o sorteio publicado, não o campo. Se houve troca de domicílio por segurança, não dá para ver sem microdados. E a ficha da Quaest não declara uma linha sobre substituição por área de risco.

O que me pegou foi a segunda invisibilidade. Varri as 101 perguntas do questionário registrado. Segurança pública: zero. Violência, facção, tráfico, PCC, milícia, assalto, homicídio: zero. A palavra crime aparece uma vez, e é sobre o Banco Master. No mesmo instrumento, Michelle aparece 22 vezes e tarifa 17.

Enquanto isso, o Datafolha mediu 41,2% dos brasileiros, quase 69 milhões, vendo facção ou milícia no próprio bairro, 55,9% nas capitais. Mesma pesquisa domiciliar, mesmo n de 2 mil. Dá para medir. Segurança é o problema número 1 do país em 2026.

Meu veredito é cirúrgico. A tese de evitar favela no sorteio não se sustenta na conta. A que sobra é a agenda por omissão: o tema que governa a vida de dezenas de milhões e lidera a preocupação do eleitor não recebe uma única pergunta, enquanto a crise palaciana ganha dezenas. A ausência é fato. A razão, eu deixo como hipótese honesta.

Contas e código abertos em brasil.arvor.co
