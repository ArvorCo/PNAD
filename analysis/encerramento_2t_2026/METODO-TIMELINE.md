# Super timeline — cômputo, encerramento e recebimento

Revisão de 29/10/2026. Nova imagem complementar; a imagem e os dados anteriores
permanecem disponíveis. Gerador `scripts/supertimeline-2t-2026-build.py`, módulos
`supertimeline_dados.py` e `supertimeline_figura.py`. Saídas em
`docs/assets/encerramento_2t_2026/`: PNG, PDF vetorial, `supertimeline.json`,
`supertimeline.csv` e `logs-dia.json`.

## Universo e três medidas

Brasil sem exterior, seções principais, pleito 3221, eleição presidencial 6258.
São 497.897 seções; cada seção entra uma vez na trilha de encerramento e uma vez
na trilha de recebimento. As contagens de votos, comparecimento, aptos e UFs são
agregadas novamente pela data de cada evento, sem transportar a composição do
encerramento para o recebimento.

1. **Cômputos:** evento literal `O voto do eleitor foi computado`, sem candidato.
   Mesmo conjunto elegível publicado: 497.725 seções, 127.812.804 cômputos,
   99,96729% do comparecimento. Sem imputar horário aos 41.827 presentes das
   seções excluídas. Os critérios, motivos de exclusão e hashes são preservados
   integralmente em `logs_cobertura`, conforme `METODO.md`.
2. **Encerramento:** `dadosSecao.dataHoraEncerramento`, decodificado em
   `bu.encerramento`. Votos e comparecimento são os do dia inteiro nas seções que
   encerraram na faixa, como na imagem anterior.
3. **Recebimento:** `dr/hr` do único hash selecionado no `aux.json`, conferido com
   `secao.dr_hr` em cada seção. Votos e comparecimento são os do dia inteiro nas
   seções cujo pacote tem esse carimbo. Não é início do envio, tempo de rede,
   leitura ao vivo da apuração ou instante de totalização. Todos os pacotes deste
   extrato são únicos; o gerador rejeita versões ambíguas.

As três barras usam bases próprias: cômputos elegíveis para a primeira e 497.897
seções para cada uma das demais. O panorama conserva tempo proporcional; a tabela
amplia os minutos de encerramento. As durações das linhas são diferentes e suas
contagens não devem ser comparadas como taxas por minuto.

## Horas e segundos

Histograma horário dos logs é agregado das métricas reconciliadas, convertendo
cada hora local para Brasília com a mesma tabela municipal da versão anterior.
Não há interpolação dos cômputos dentro das horas. Cada histograma deve somar o
comparecimento de sua seção; o hash do extrato completo, critérios, quantidade de
seções e total devem coincidir com o agregado anterior antes de qualquer desenho.

Horas completas: 08:00:00–08:59:59, 09:00:00–09:59:59, até 16:00:00–16:59:59.
A faixa antes de 08h é conservada nos dados e só é escondida na imagem quando
está explicitamente vazia nas três fontes. O primeiro cômputo elegível é 08:00:19.
A ponte de 17h00:00 contém exatamente 280 cômputos: diferença entre o acumulado
exato previamente relido até 17h e o histograma anterior a 17h. Nenhum segundo é
contado duas vezes. Os cortes da imagem anterior de 17h00 até 19h00 são preservados,
com os mesmos limites inclusivos. A primeira linha antiga aparece agora como o
acumulado de todos os cômputos até 17h00, não como um novo lote de 127 milhões.

Após 19h, os cortes são 20h, 21h, 22h, 23h e 00h de 26/10, sempre (início, fim].
Há 11 cômputos depois das 19h e o último é 19:06:21; portanto todos pertencem à
primeira dessas faixas. Se uma nova fonte trouxer cômputos a partir das 20h, o
agregador aborta e exige releitura da cauda em vez de distribuir valores por
hipótese. Datas de recebimento aceitam o dia seguinte e estendem os cortes até
a hora que inclui o último evento. Nesta publicação não há recebimentos de 26/10:
o último é 25/10 às 23:21:40. A linha 00h de 26/10 contém a faixa 23h–00h, não
atribui esses eventos ao dia seguinte.

O subtotal literal “após 19h” da imagem anterior é conservado no final e claramente
rotulado como subtotal das linhas finais. Não é somado novamente aos totais.

## Pausa observada e cronologias divergentes

Os primeiros 1.484 pacotes têm carimbos até 17:08:53. O próximo é 19:03:37:
1h54min44s entre registros consecutivos. A anotação descreve o conjunto de
carimbos arquivados; não identifica a causa nem prova paralisação da transmissão.

Dezesseis seções têm divergência na ordem encerramento/emissão/recebimento,
incluindo uma recebida às 16:59:34. Seus carimbos **permanecem na sequência de
recebimentos**, com marca * e contagem na faixa. Elas não são apagadas ou
reposicionadas para tornar a curva mais plausível. Na análise de duração
encerramento→recebimento anterior, esses 16 casos ficam fora dos intervalos
comparáveis; os objetivos dos dois recortes são diferentes.

## Preservação e validação

Teste compara cada campo da versão anterior, incluindo contagens, acumulados,
percentuais e todas as UFs, com a trilha de encerramento da nova versão. O subtotal
após 19h é idêntico. As duas trilhas de BUs devem recompor todos os totais de
seções, aptos, comparecimento, válidos, candidatos, brancos e nulos. As
sequências por segundo recompõem cada faixa; a série de logs recompõe seu total.
Teste adicional cobre virada de data e carimbos locais convertidos para Brasília.

```sh
.venv/bin/python scripts/supertimeline-2t-2026-build.py
.venv/bin/pytest -q tests/test_supertimeline_2t_2026.py tests/test_encerramento_2t_2026.py tests/test_encerramento_logs.py
```

`--so-imagem` redesenha os agregados salvos; `--refazer` força releitura das métricas
horárias; `--so-dados` não renderiza. A versão antiga continua acessível pelos
mesmos endereços. A nova imagem é ligada no mapa e no Politize junto às anteriores.
