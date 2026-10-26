#!/bin/bash
# Reconsolida a chuva de 25/10 e regera as páginas que a consomem (sem commit).
# Chamado pelas fotos agendadas do CEMADEN; pode ser rodado à mão.
set -euo pipefail
cd "$(dirname "$0")"
python3 clima-2t.py --consolidar --fonte "${1:-ifs}"
python3 politize-se-build.py
python3 politize-se-mapa-build.py
python3 apuracao-2t-2026-logs.py
python3 apuracao-2t-2026-build.py
