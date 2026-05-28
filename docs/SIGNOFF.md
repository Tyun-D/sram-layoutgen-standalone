# Signoff Workflow

This package can generate GDS/LEF/SPICE and can call bundled FreePDK45 KLayout decks when KLayout is available from the shell.

## Generate and Run Checks

```bash
cd deliverables/sram_layoutgen_standalone
bash examples/generate_and_check.sh 8 64 build/signoff_8x64
```

If KLayout is installed on Windows but not on the WSL `PATH`, pass the executable explicitly:

```bash
KLAYOUT_BIN="/mnt/c/Program Files/KLayout/klayout_app.exe" \
  bash examples/generate_and_check.sh 8 64 build/signoff_8x64
```

The script produces:

```text
*.presentation.gds       clean visual review view, no route guides or text labels
*.debug.gds              debug view with route guides, module overlay, and labels
*.gds                    full signoff-candidate view with child cell references
*.integration.gds        black-box integration DRC view
*.route_guides.gds       legacy route-guide debug view
*.lef
*.sp
*.layout.json
*.report.json
*.report.md
*.klayout_drc.lyrdb      when KLayout DRC runs
*.klayout_lvs.lvsdb      when KLayout LVS runs
*.extracted.sp           when KLayout extraction runs
```

## Current Blocking Items

`signoff_ready` remains false until all of these are true:

- no `abstract_instances` remain in `*.report.json`
- KLayout DRC report exists and has zero reported items
- LVS has a complete schematic and passes
- extracted netlist and generated SPICE are equivalent

The current generator now replaces the old `abstract_decoder` with generated decoder/control stdcells. Final signoff still requires running KLayout DRC/LVS and fixing any violations reported by those decks.

On Windows PowerShell, the preferred staged flow is:

```powershell
cd "E:\njust\keyan\SRAM Compiler_V2\OpenRAM-stable\deliverables\sram_layoutgen_standalone"

# First check top-level integration geometry with cell internals black-boxed.
powershell -ExecutionPolicy Bypass -File examples\run_external_signoff.ps1 `
  -WordSize 4 -NumWords 32 -WordsPerRow 2 `
  -OutDir build\external_signoff_4x32_wpr2_integration `
  -IntegrationDrcOnly

# Then run full DRC on the complete signoff-candidate GDS without immediately entering LVS.
powershell -ExecutionPolicy Bypass -File examples\run_external_signoff.ps1 `
  -WordSize 4 -NumWords 32 -WordsPerRow 2 `
  -OutDir build\external_signoff_4x32_wpr2_full_drc `
  -DrcOnly

# Finally run full DRC followed by LVS after full DRC is clean.
powershell -ExecutionPolicy Bypass -File examples\run_external_signoff.ps1 `
  -WordSize 4 -NumWords 32 -WordsPerRow 2 `
  -OutDir build\external_signoff_4x32_wpr2_full_lvs
```

## What to Check First

Open `*.report.md` after generation and confirm:

- `Presentation GDS` points to `*.presentation.gds` for visual review
- `Full signoff-candidate GDS` points to `*.gds` for full DRC/LVS
- `Remaining abstract blocks` is `none`
- `GDS labels` contains `clk`, `csb`, `web`, `addr[...]`, `din[...]`, `dout[...]`, `vdd`, and `gnd`
- `Built-in DRC-lite` is clean

Then run KLayout DRC. The most likely first violations, if any, will be inside generated decoder/control stdcells:

- well/implant enclosure around generated gates
- contact enclosure by metal1
- poly/active spacing in generated cells
- top-level pin label/pin shape datatype expectations

Fix these before interpreting LVS mismatches.
