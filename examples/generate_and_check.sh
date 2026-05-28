#!/usr/bin/env bash
set -euo pipefail

WORD_SIZE="${1:-8}"
NUM_WORDS="${2:-64}"
OUT_DIR="${3:-build/signoff_${WORD_SIZE}x${NUM_WORDS}}"

python3 -m sram_layoutgen \
  --word-size "${WORD_SIZE}" \
  --num-words "${NUM_WORDS}" \
  --out "${OUT_DIR}"

REPORT="$(find "${OUT_DIR}" -maxdepth 1 -name '*.report.json' | sort | head -n 1)"
GDS="$(find "${OUT_DIR}" -maxdepth 1 -name '*.gds' | sort | head -n 1)"
TOPCELL="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["name"])' "${REPORT}")"
DRC_DECK="technology/freepdk45/tech/freepdk45.lydrc"
LVS_DECK="technology/freepdk45/tech/freepdk45.lylvs"
DRC_REPORT="${OUT_DIR}/${TOPCELL}.klayout_drc.lyrdb"
LVS_REPORT="${OUT_DIR}/${TOPCELL}.klayout_lvs.lvsdb"
EXTRACTED_NETLIST="${OUT_DIR}/${TOPCELL}.extracted.sp"

KLAYOUT_BIN="${KLAYOUT_BIN:-klayout}"

if command -v "${KLAYOUT_BIN}" >/dev/null 2>&1 || [[ -x "${KLAYOUT_BIN}" ]]; then
  echo "KLayout found: ${KLAYOUT_BIN}"
  "${KLAYOUT_BIN}" -b \
    -r "${DRC_DECK}" \
    -rd input="${GDS}" \
    -rd topcell="${TOPCELL}" \
    -rd output="${DRC_REPORT}"
  echo "KLayout DRC report: ${DRC_REPORT}"

  if [[ -f "${OUT_DIR}/${TOPCELL}.sp" ]]; then
    "${KLAYOUT_BIN}" -b \
      -r "${LVS_DECK}" \
      -rd input="${GDS}" \
      -rd schematic="${OUT_DIR}/${TOPCELL}.sp" \
      -rd report="${LVS_REPORT}" \
      -rd target_netlist="${EXTRACTED_NETLIST}" \
      -rd connect_supplies=true || true
    echo "KLayout LVS report: ${LVS_REPORT}"
    echo "Extracted netlist: ${EXTRACTED_NETLIST}"
  fi
  python3 -m sram_layoutgen.signoff \
    --report "${REPORT}" \
    --drc "${DRC_REPORT}" \
    --lvs "${LVS_REPORT}" \
    --extracted "${EXTRACTED_NETLIST}"
else
  echo "KLayout CLI was not found; external signoff DRC/LVS was skipped."
  echo "If KLayout is installed on Windows, rerun like:"
  echo "  KLAYOUT_BIN='/mnt/c/Program Files/KLayout/klayout_app.exe' bash examples/generate_and_check.sh ${WORD_SIZE} ${NUM_WORDS} ${OUT_DIR}"
fi

echo "GDS: ${GDS}"
echo "Report: ${REPORT}"
