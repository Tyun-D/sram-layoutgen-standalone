#!/usr/bin/env python3
"""Generate one standalone SRAM layout from Python API."""

from pathlib import Path

from sram_layoutgen import StandaloneSpec, write_standalone

metrics = write_standalone(StandaloneSpec(word_size=8, num_words=64), Path("build/example_8x64"))
print(metrics["gds"])
print(metrics["macro_area_um2"], metrics["utilization"])
