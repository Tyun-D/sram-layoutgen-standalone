# Server Simulator Capability Audit

- audit_scope: `PATH tools`, `known absolute tool installs`, `version probes only`, `no package installation`
- current_server_date: `2026-07-30`

## Tool Summary

| tool | usable | path | version | role | limitations |
| --- | --- | --- | --- | --- | --- |
| ngspice | True | /usr/bin/ngspice | ****** | primary transistor-level spice smoke and regression | - |
| Xyce | True | /usr/local/xyce_parallel/bin/Xyce | Xyce DEVELOPMENT-202507091615-()-opensource | secondary spice cross-check and large-netlist simulation | - |
| xyce | False | - | - | not_usable | not found or version probe failed |
| iverilog | True | /usr/bin/iverilog | Icarus Verilog version 11.0 (stable) () | preferred digital logic regression if trusted Verilog appears | no trusted Verilog assets discovered in current project audit |
| vvp | True | /usr/bin/vvp | Icarus Verilog runtime version 11.0 (stable) () | Icarus runtime for digital logic regression | - |
| verilator | True | /opt/pdk_klayout_openroad/oss-cad-suite/bin/verilator | Verilator 5.035 devel rev v5.034-106-ge6a997e31 | secondary digital lint / fast compile if trusted Verilog appears | not on PATH; only discoverable via absolute install path |
| vcs | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| simv | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| xrun | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| irun | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| ncsim | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| vsim | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| vlog | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| vlib | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| hspice | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| spectre | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| aps | False | - | - | not_usable | not found or version probe failed; likely license-gated commercial tool |
| gtkwave | True | /usr/bin/gtkwave | Usage: /usr/bin/gtkwave [OPTION]... [DUMPFILE] [SAVEFILE] [RCFILE] | waveform viewer (GUI required) | GUI/X11 unavailable in current shell; viewer only; current shell lacks DISPLAY |
| klayout | True | /usr/bin/klayout | KLayout 0.29.12 | layout viewing and possible DRC/LVS/manual inspection | - |
| magic | True | /usr/bin/magic | 8.3.105 | layout viewing / open-source extraction candidate | no project-specific extraction/LVS deck provenance confirmed yet |
| netgen | False | - | - | not_usable | not found or version probe failed; no project-specific LVS rule deck provenance confirmed yet |
| yosys | True | /usr/bin/yosys | Yosys 0.9 (git sha1 1979e0b) | netlist inspection / synthesis experiments | - |
| openroad | True | /usr/bin/openroad | v2.0-17598-ga008522d8 | digital PnR experiments only | - |
| python3 | True | /data1/qujh/.venv/bin/python3 | Python 3.10.13 | general utility | - |
| make | True | /usr/bin/make | GNU Make 4.3 | general utility | - |
| cmake | True | /usr/bin/cmake | cmake version 3.22.1 | general utility | - |
| gcc | True | /usr/bin/gcc | gcc (Ubuntu 12.3.0-1ubuntu1~22.04.3) 12.3.0 | general utility | - |
| g++ | True | /usr/bin/g++ | g++ (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0 | general utility | - |

## Conclusions

- `ngspice` is the only clearly usable open-source primary SPICE engine already on `PATH`.
- `Xyce` is usable from `/usr/local/xyce_parallel/bin/Xyce` and is already active in other users' jobs; treat it as a secondary cross-check engine.
- `iverilog`/`vvp` are usable, but no trusted project Verilog assets were discovered in this audit, so digital regressions are asset-blocked rather than tool-blocked.
- `verilator` exists only in an absolute install path and is suitable as a secondary lint/compile engine if trusted Verilog is added later.
- `gtkwave` requires GUI/X11 and is not usable in the current headless shell.
- `magic` and `klayout` are available, but no current-project extraction/LVS rule provenance was found that would justify claiming post-layout extraction closure.
