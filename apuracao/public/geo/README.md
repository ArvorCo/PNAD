# Geometria compacta dos mapas

Estes arquivos são versionados porque o build Python do dossiê da apuração e
seus testes também os usam. O pacote inteiro tem aproximadamente 3,9 MB;
bancos de apuração, fontes e imagens pesadas continuam fora deste diretório.

- `br_uf.geojson` e `mun/*.geojson`: malhas do IBGE, qualidade mínima,
  arquivadas pelo script `apuracao/scripts/baixar-malhas.ts`. A fonte é a
  [API de malhas do IBGE](https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF).
  `index.json` registra bytes e quantidade de feições por UF.
- `mundo.geojson`: conversão de `world-atlas/countries-110m.json`, sem
  Antártida, feita por `apuracao/scripts/gerar-mundo.ts`.
- A malha nacional original usada por `scripts/voto_util_mapa.py` está em
  `data/originals/ibge_malhas/br_uf/br_uf_minima.geojson`; sua cópia aqui é idêntica.

Os scripts de origem preservam arquivos existentes. Atualizar a geometria
exige uma rodada explícita de coleta e revisão, não acesso à rede durante testes.
