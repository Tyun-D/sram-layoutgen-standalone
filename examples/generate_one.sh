#!/usr/bin/env bash
set -euo pipefail
python3 -m sram_layoutgen \
  --word-size 8 \
  --num-words 64 \
  --out build/example_8x64
