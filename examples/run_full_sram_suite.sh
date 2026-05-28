#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_ROOT="${1:-build/full_sram_suite}"

cd "${ROOT_DIR}"
mkdir -p "${OUT_ROOT}"

SPECS=(
  "2 16"
  "4 32"
  "8 64"
)

for spec in "${SPECS[@]}"; do
  read -r WORD_SIZE NUM_WORDS <<<"${spec}"
  OUT_DIR="${OUT_ROOT}/${WORD_SIZE}x${NUM_WORDS}"
  echo "==> Generating ${WORD_SIZE}x${NUM_WORDS} into ${OUT_DIR}"
  bash examples/generate_and_check.sh "${WORD_SIZE}" "${NUM_WORDS}" "${OUT_DIR}"
done

python3 - "${OUT_ROOT}" <<'PY'
import json
import sys
from pathlib import Path

out_root = Path(sys.argv[1])
reports = sorted(out_root.glob("*x*/*.report.json"))
summary = out_root / "summary.md"

lines = [
    "# Full SRAM Suite Summary",
    "",
    "| spec | GDS | area(um^2) | utilization | DRC-lite | structural roles | generated GDS cells | signoff |",
    "|---|---:|---:|---:|---:|---:|---:|---|",
]

for report_path in reports:
    data = json.loads(report_path.read_text(encoding="utf-8"))
    spec = f"{data['word_size']}x{data['num_words']}"
    gds = Path(data["gds"]).name
    area = data["macro_area_um2"]
    util = data["utilization"] * 100.0
    drc = data["drc_violation_count"]
    complete = data.get("layout_completeness", {}).get("complete_structural_roles")
    generated = len(data.get("generated_gds_cells", []))
    signoff = "ready" if data.get("signoff_ready") else "needs external DRC/LVS"
    lines.append(
        f"| {spec} | `{gds}` | {area:.3f} | {util:.2f}% | {drc} | {complete} | {generated} | {signoff} |"
    )

summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(summary)
PY

echo "Suite summary: ${OUT_ROOT}/summary.md"
