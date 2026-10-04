#!/usr/bin/env bash
# Fixtures reais do TSE usadas pelos testes (tests/fixtures/).
# Origem: baixadas com curl de https://resultados.tse.jus.br/oficial em 03/10/2026
# (estado zerado de 2026, ciclo ele2026, pleito 3220) e dos arquivos de 2024
# (ciclo ele2024, eleição 619) para valores reais. Os corpos de erro vêm do bucket
# (NoSuchKey) e do Akamai (Access Denied, ambiente simulado).
# Este script só recria o que faltar; se as fixtures existem, não faz nada.
set -euo pipefail
cd "$(dirname "$0")/.."
DEST=tests/fixtures
BASE=https://resultados.tse.jus.br/oficial
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"

baixar() { # destino url
  local destino="$DEST/$1"
  [[ -s "$destino" ]] && return 0
  mkdir -p "$(dirname "$destino")"
  echo "baixando $1"
  curl -fsSL --compressed -A "$UA" -o "$destino" "$2"
}

baixar ele-c.json "$BASE/comum/config/ele-c.json"
for ele in 6257 6259 6261; do
  baixar "mun-e00$ele-cm.json" "$BASE/ele2026/$ele/config/mun-e00$ele-cm.json"
done
baixar br-e006257-ab.json "$BASE/ele2026/6257/dados/br/br-e006257-ab.json"
baixar sp-e006257-ab.json "$BASE/ele2026/6257/dados/sp/sp-e006257-ab.json"
baixar zz-e006257-ab.json "$BASE/ele2026/6257/dados/zz/zz-e006257-ab.json"
baixar br-c0001-e006257-u.json "$BASE/ele2026/6257/dados/br/br-c0001-e006257-u.json"
baixar sp-c0001-e006257-u.json "$BASE/ele2026/6257/dados/sp/sp-c0001-e006257-u.json"
baixar zz-c0001-e006257-u.json "$BASE/ele2026/6257/dados/zz/zz-c0001-e006257-u.json"
baixar sp71072-c0001-e006257-u.json "$BASE/ele2026/6257/dados/sp/sp71072-c0001-e006257-u.json"
baixar sp71072-z0001-c0001-e006257-u.json "$BASE/ele2026/6257/dados/sp/sp71072-z0001-c0001-e006257-u.json"
baixar sp-c0003-e006259-u.json "$BASE/ele2026/6259/dados/sp/sp-c0003-e006259-u.json"
baixar sp71072-c0007-e006259-u.json "$BASE/ele2026/6259/dados/sp/sp71072-c0007-e006259-u.json"
baixar df-c0008-e006259-u.json "$BASE/ele2026/6259/dados/df/df-c0008-e006259-u.json"
baixar sp-p003220-cs.json "$BASE/ele2026/arquivo-urna/3220/config/sp/sp-p003220-cs.json"
baixar 2024/br-e000619-ab.json "$BASE/ele2024/619/dados/br/br-e000619-ab.json"
baixar 2024/sp-e000619-ab.json "$BASE/ele2024/619/dados/sp/sp-e000619-ab.json"
baixar 2024/sp-c0011-e000619-e.json "$BASE/ele2024/619/dados/sp/sp-c0011-e000619-e.json"
baixar 2024/sp71072-c0011-e000619-u.json "$BASE/ele2024/619/dados/sp/sp71072-c0011-e000619-u.json"
baixar 2024/sp71072-c0013-e000619-u.json "$BASE/ele2024/619/dados/sp/sp71072-c0013-e000619-u.json"
# tests/fixtures/erros/ (nosuchkey.xml, access-denied.html) foram salvos à mão de respostas reais.
echo "fixtures ok"
