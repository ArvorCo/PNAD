#!/usr/bin/env bash
# Depósito dos bancos brutos das urnas de 2026 no Internet Archive (archive.org).
#
# Pré-requisitos (uma vez, com a conta do Leonardo): `ia configure` (grava a chave em
# ~/.config/internetarchive/ia.ini; nunca entra no repositório). Os hashes SHA-256 vêm de
# analysis/apuracao_2t_2026/deposito/hashes_brutos.json, gerado antes do envio.
#
# Uso:
#   bash scripts/deposito-archive.sh --dry-run        # mostra o que subiria
#   bash scripts/deposito-archive.sh                  # envia (retoma e pula o que já está igual)
#   bash scripts/deposito-archive.sh --registrar      # grava analysis/apuracao_2t_2026/deposito_bruto.json
set -euo pipefail
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
IA="${IA:-$HOME/.local/bin/ia}"
ITEM="${ITEM:-arvor-apuracao-2026-urnas-brasil}"
HASHES="analysis/apuracao_2t_2026/deposito/hashes_brutos.json"
META="analysis/apuracao_2t_2026/deposito/item.json"
MODO="${1:-}"

[ -f "$HASHES" ] || { echo "faltam os hashes: $HASHES"; exit 2; }
[ -f "$META" ] || { echo "falta a ficha do item: $META"; exit 2; }

ARQUIVOS=$(python3 -c "import json;print('\n'.join(a['arquivo'] for a in json.load(open('$HASHES'))['arquivos']))")
ARGS=$(python3 - <<EOF
import json
m=json.load(open("$META"))
print(" ".join(f"--metadata={k}:{v}" for k,v in m["metadata"].items()))
EOF
)

echo "item: https://archive.org/details/$ITEM"
echo "$ARQUIVOS" | while read -r f; do printf "  %10.2f GB  %s\n" "$(echo "scale=2; $(stat -f %z "$f")/1e9" | bc)" "$f"; done
if [ "$MODO" = "--dry-run" ]; then exit 0; fi

if [ "$MODO" = "--registrar" ]; then
  python3 - <<EOF
import json, subprocess, time
h=json.load(open("$HASHES")); m=json.load(open("$META"))
meta=json.loads(subprocess.check_output(["$IA","metadata","$ITEM"]))
arqs={f["name"]: f for f in meta.get("files", [])}
out={"item":"$ITEM","url":"https://archive.org/details/$ITEM","registrado_em":time.strftime("%Y-%m-%dT%H:%M:%S%z"),
     "titulo":m["metadata"]["title"],"arquivos":[]}
for a in h["arquivos"]:
    nome=a["arquivo"].split("/")[-1]; f=arqs.get(nome)
    out["arquivos"].append({**a,"nome":nome,"no_archive":bool(f),"bytes_no_archive":int(f["size"]) if f else None,
                            "md5_archive":f.get("md5") if f else None,
                            "url":f"https://archive.org/download/$ITEM/{nome}"})
json.dump(out,open("analysis/apuracao_2t_2026/deposito_bruto.json","w"),ensure_ascii=False,indent=1)
faltam=[x["nome"] for x in out["arquivos"] if not x["no_archive"] or x["bytes_no_archive"]!=x["bytes"]]
print("registrado; divergentes ou ausentes:", faltam or "nenhum")
EOF
  exit 0
fi

# envio pela biblioteca (metadados com espaços e acentos chegam inteiros); --checksum pula o que já está igual
python3 - <<EOF
import json, sys
from internetarchive import upload
h=json.load(open("$HASHES")); m=json.load(open("$META"))["metadata"]
arqs=[a["arquivo"] for a in h["arquivos"]]
arqs.append("$HASHES")
import os
if os.path.exists("docs/assets/apuracao_2t/dataset/DICIONARIO.md"):
    arqs.append("docs/assets/apuracao_2t/dataset/DICIONARIO.md")
    arqs.append("docs/assets/apuracao_2t/dataset/secoes_1t_2t_2026.csv.gz")
nomes={a: ("hashes_sha256.json" if a=="$HASHES" else os.path.basename(a)) for a in arqs}
from internetarchive import get_item
remotos={f["name"]: int(f.get("size") or 0) for f in get_item("$ITEM").files}
for a in arqs:
    tam=os.path.getsize(a)
    if remotos.get(nomes[a]) == tam:
        print("já no item, mesmo tamanho; pulando", a, flush=True)
        continue
    print("enviando", a, flush=True)
    r=upload("$ITEM", files={nomes[a]: a}, metadata=m, checksum=True, retries=10, retries_sleep=30, verbose=True, verify=True)
    print("  ->", [getattr(x, "status_code", x) for x in r], flush=True)
print("envio concluído; rode --registrar depois que o archive.org terminar de derivar")
EOF
