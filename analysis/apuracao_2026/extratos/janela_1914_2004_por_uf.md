# Janela 19:14:08 a 20:04:39 de 04/10/2026, por UF

Fonte: arquivos públicos do TSE em `resultados.tse.jus.br/oficial/ele2026/6257/dados/`, lidos e guardados versão a versão pelo coletor da casa (`apuracao/`), com a hora de geração que o próprio TSE grava em cada arquivo (`dg`/`hg`). Horas em Brasília.

- Arquivo nacional `br-c0001-e006257-u.json` gerado às 19:14:08 (lido às 19:14:29): 323.539 seções totalizadas de 499.248.
- Arquivo nacional gerado às 20:04:39 (lido às 20:05:18): 424.153 seções.
- Diferença: 100.614 seções.

O arquivo nacional não traz divisão por UF. A divisão vem dos 28 arquivos de UF (`<uf>-c0001-e006257-u.json`, 27 UFs e exterior), que o TSE gera em instantes próprios. Três leituras, declaradas:

1. **Retrato do nacional** (`st_retrato_nacional_1914`): a versão de cada arquivo de UF gerada até 19:08:00. instante em que a soma das UFs (322.739) fica mais perto da contagem do arquivo nacional de 19:14:08 (323.539). O arquivo nacional de 19:14:08 era o retrato de cerca de 19:08:00.
2. **Arquivo de UF no mesmo instante** (`st_arquivo_uf_1914`): a versão de cada UF gerada até 19:14:08; a soma (353.630) já estava 30.091 seções à frente do nacional.
3. **Monitoramento** (`st_monitoramento_*`): contagem por UF do arquivo `br-e006257-ab.json` gerado às 19:13:57 e às 20:05:03, que continuou sendo gerado durante a parada do arquivo de resultado.

Às 20:04:39 a soma das UFs (424.493) e o nacional (424.153) quase coincidem.

| UF | seções | retrato 19:14 | UF 19:14 | 20:04 | Δ retrato | Δ Lula | Δ Flávio |
|---|---:|---:|---:|---:|---:|---:|---:|
| SP | 103.656 | 68.117 | 76.665 | 93.379 | 25.262 | 2.470.922 | 3.124.467 |
| MG | 52.062 | 28.962 | 32.424 | 42.240 | 13.278 | 1.320.622 | 1.469.051 |
| RJ | 37.675 | 16.695 | 19.912 | 27.692 | 10.997 | 1.105.479 | 1.479.652 |
| BA | 35.476 | 15.112 | 17.249 | 23.835 | 8.723 | 1.407.625 | 615.708 |
| CE | 23.765 | 9.803 | 11.766 | 16.281 | 6.478 | 993.344 | 502.114 |
| PE | 21.418 | 10.784 | 12.270 | 16.102 | 5.318 | 928.220 | 451.986 |
| RS | 27.547 | 22.864 | 24.221 | 26.834 | 3.970 | 333.895 | 515.033 |
| MA | 18.093 | 9.765 | 10.746 | 13.676 | 3.911 | 574.668 | 279.746 |
| PA | 20.827 | 13.618 | 14.692 | 17.459 | 3.841 | 445.142 | 425.502 |
| SC | 17.326 | 12.675 | 14.055 | 16.453 | 3.778 | 239.643 | 678.232 |
| GO | 15.686 | 11.318 | 12.382 | 14.331 | 3.013 | 256.282 | 386.345 |
| RN | 8.115 | 4.805 | 5.352 | 6.783 | 1.978 | 316.593 | 191.818 |
| AL | 7.101 | 2.228 | 2.796 | 4.052 | 1.824 | 258.242 | 181.347 |
| PI | 10.225 | 6.890 | 7.512 | 8.659 | 1.769 | 277.164 | 81.878 |
| AM | 8.157 | 5.660 | 5.924 | 6.938 | 1.278 | 178.025 | 132.834 |
| SE | 5.923 | 4.270 | 4.769 | 5.510 | 1.240 | 195.602 | 88.924 |
| PR | 27.142 | 25.935 | 26.254 | 26.919 | 984 | 85.318 | 139.960 |
| MT | 8.287 | 7.024 | 7.339 | 7.937 | 913 | 70.772 | 142.424 |
| PB | 10.712 | 9.613 | 9.964 | 10.471 | 858 | 138.403 | 65.626 |
| ES | 9.844 | 9.143 | 9.368 | 9.772 | 629 | 67.958 | 79.429 |
| RO | 4.698 | 4.191 | 4.296 | 4.608 | 417 | 19.157 | 61.898 |
| AP | 1.914 | 1.237 | 1.315 | 1.600 | 363 | 41.947 | 47.342 |
| MS | 7.106 | 6.797 | 6.891 | 7.055 | 258 | 24.925 | 27.414 |
| TO | 4.384 | 4.138 | 4.221 | 4.332 | 194 | 18.225 | 22.098 |
| RR | 1.519 | 1.301 | 1.362 | 1.491 | 190 | 8.580 | 32.342 |
| AC | 2.270 | 2.087 | 2.127 | 2.226 | 139 | 9.803 | 19.413 |
| DF | 6.969 | 6.857 | 6.900 | 6.935 | 78 | 7.586 | 12.329 |
| ZZ | 1.351 | 850 | 858 | 923 | 73 | 7.568 | 10.625 |
| **Total** | 499.248 | 322.739 | 353.630 | 424.493 | 101.754 | 11.801.710 | 11.265.537 |

Colunas completas no CSV ao lado. Δ = 20:04 menos retrato de 19:14. Votos de Lula e Flávio são os nominais (`vap`) do arquivo de UF.

Limites: o retrato é aproximação por minuto cheio; os arquivos de UF e o nacional são gerados por processos separados do TSE, por isso as somas não batem no segundo. As versões brutas (JSON original com hash SHA-256) estão no banco do coletor, disponível a pedido.
