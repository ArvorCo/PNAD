#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict


def make_markdown_cell(text: str) -> Dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(True),
    }


def make_code_cell(code: str) -> Dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": code.splitlines(True),
    }


def main(argv=None) -> int:
    nb_path = Path("notebooks/PNADC_exploration.ipynb")
    if not nb_path.exists():
        print(f"ERROR: notebook not found: {nb_path}", file=sys.stderr)
        return 1
    nb = json.loads(nb_path.read_text(encoding="utf-8"))
    cells: List[Dict] = nb.get("cells", [])

    md = make_markdown_cell(
        """# NPV Setup (IPCA BCB) — deflate VD4020 to present value

This section fetches monthly IPCA from BCB, builds deflators to the latest available month, and computes:
- `VD4020__rendim_efetivo_qq_trabalho_YYYYMM` (BRL at present prices)
- `VD4020__rendim_efetivo_qq_trabalho_mw` (in minimum wages, parameterized)
"""
    )

    code_fetch = make_code_cell(
        """
import pandas as pd
from urllib.request import urlopen, Request
import json
from datetime import datetime

INCOME_COL = "VD4020__rendim_efetivo_qq_trabalho"
MIN_WAGE = 1518.0  # adjust if needed

def fetch_ipca_bcb_variation(series: int = 433):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series}/dados?formato=json"
    req = Request(url, headers={"User-Agent": "pnad-npv/1.0"})
    with urlopen(req, timeout=60) as resp:
        data = resp.read().decode("utf-8")
    items = json.loads(data)
    # items: {"data":"mm/yyyy" or "dd/mm/yyyy", "valor":"x,yy"}
    out = []
    for it in items:
        d = str(it.get("data", ""))
        parts = d.split("/")
        if len(parts) == 2:
            m, y = int(parts[0]), int(parts[1])
        else:
            # dd/mm/yyyy
            m, y = int(parts[1]), int(parts[2])
        val = float(str(it.get("valor", "")).replace(",", "."))
        out.append((f"{y}-{m:02d}", val))
    df = pd.DataFrame(out, columns=["ym", "pct_month"]).sort_values("ym").reset_index(drop=True)
    return df

def build_index_from_pct(df: pd.DataFrame) -> pd.DataFrame:
    # Compose an index by capitalizing monthly variations; base cancels in ratios.
    idx = (1.0 + df["pct_month"] / 100.0).cumprod()
    out = pd.DataFrame({"ym": df["ym"], "index": idx})
    return out

ipca = fetch_ipca_bcb_variation()
ipca_idx = build_index_from_pct(ipca)
TARGET_YM = ipca_idx["ym"].iloc[-1]  # latest available month
TARGET_IDX = float(ipca_idx.loc[ipca_idx["ym"] == TARGET_YM, "index"].iloc[0])
# Rebase to target to avoid huge numbers; factor = 1 / (index / index_target)
ipca_idx["rebased_to_target"] = ipca_idx["index"] / TARGET_IDX
ipca_idx["factor_to_target"] = 1.0 / ipca_idx["rebased_to_target"]
print({"target_month": TARGET_YM, "sample_factor_prev_month": float(ipca_idx["factor_to_target"].iloc[-2])})
"""
    )

    code_apply = make_code_cell(
        """
# Load base (prefer parquet) with robust path resolution
import os
from pathlib import Path
import pandas as pd

def find_in_data(fn: str) -> Path | None:
    # Search current directory and parents for a 'data/<fn>'
    for base in [Path.cwd()] + list(Path.cwd().parents):
        cand = base / "data" / fn
        if cand.exists():
            return cand
    return None

parquet_file = find_in_data("base_labeled.parquet")
csv_file = find_in_data("base_labeled.csv")

if parquet_file and parquet_file.exists():
    df = pd.read_parquet(parquet_file)
elif csv_file and csv_file.exists():
    df = pd.read_csv(csv_file)
else:
    raise FileNotFoundError("Missing base_labeled.{parquet,csv} under a data/ directory near this notebook")

print({"resolved_parquet": str(parquet_file) if parquet_file else None,
       "resolved_csv": str(csv_file) if csv_file else None})

# Derive YYYY-MM reference from Ano/Trimestre (use last month of the quarter)
Q2M = {1: "03", 2: "06", 3: "09", 4: "12"}
def to_int(x):
    try:
        return int(str(x).strip())
    except Exception:
        return None

year_col = next((c for c in df.columns if c.startswith("Ano__")), "Ano__ano_de_referncia")
quarter_col = next((c for c in df.columns if c.startswith("Trimestre__")), "Trimestre__trimestre_de_referncia")
df["ym"] = df[year_col].map(lambda x: str(x).split(".")[0]) + "-" + df[quarter_col].map(lambda x: Q2M.get(to_int(x), "12"))

# Merge factors
df = df.merge(ipca_idx[["ym", "factor_to_target"]], on="ym", how="left")

# Coverage checks (sanity): ensure ref periods are recent as expected
ym_stats = {
    "ym_min": df["ym"].min(),
    "ym_max": df["ym"].max(),
    "factor_coverage": int(df["factor_to_target"].notna().sum()),
    "rows": int(len(df)),
}
print({"ref_period": ym_stats})

# Apply deflator to income column and convert to minimum wages
npv_col = f"{INCOME_COL}_{TARGET_YM.replace('-', '')}"
mw_col = f"{INCOME_COL}_mw"
df[npv_col] = pd.to_numeric(df[INCOME_COL], errors="coerce") * df["factor_to_target"]
df[mw_col] = df[npv_col] / float(MIN_WAGE)

print(df[[INCOME_COL, npv_col, mw_col]].describe(include="all"))
df.head()

# Persist NPV-adjusted dataset for downstream SQL/EDA
out_dir = (parquet_file or csv_file).parent if (parquet_file or csv_file) else (Path.cwd()/".."/"data").resolve()
npv_parquet = out_dir / "base_labeled_npv.parquet"
df.to_parquet(npv_parquet, index=False)
npv_csv = out_dir / "base_labeled_npv.csv"
try:
    df.to_csv(npv_csv, index=False)
except Exception:
    pass
print({"saved_parquet": str(npv_parquet), "saved_csv": str(npv_csv)})
"""
    )

    new_cells = [md, code_fetch, code_apply]
    nb["cells"] = new_cells + cells
    nb_path.write_text(json.dumps(nb, ensure_ascii=False), encoding="utf-8")
    print(f"Prepended {len(new_cells)} cells to {nb_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
