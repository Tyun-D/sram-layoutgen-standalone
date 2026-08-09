# Student Handoff Dependency Audit

Audit timestamp: 2026-08-09T05:02:51Z

Current smoke-test runtime:

- Python: 3.13.5 from `/opt/anaconda3/bin/python`
- Generator invocation: `python -m sram_layoutgen`
- KLayout binary: present, `KLayout 0.29.12`
- Python `klayout` / `klayout.db`: not installed and not required by the legacy smoke tests
- `gdstk`: installed, version 1.0.0, but not required by `write_standalone`
- `gdspy`: installed, version 1.6.13, but not required by `write_standalone`
- Relevant env vars during smoke test: `OPENYIELD_ROOT`, `PYTHONPATH`, `PDK_ROOT`, `OPENRAM_HOME` unset

Bundled generator dependencies:

| dependency | status | handoff action |
|---|---|---|
| Python standard library | PORTABLE | document Python version; test with target Python |
| `sram_layoutgen` package | PORTABLE | include whole package |
| `technology/freepdk45/layers.map` | PORTABLE | include |
| `technology/freepdk45/gds_lib/*.gds` | NEEDS_PACKAGING | include all hardmacro GDS |
| `technology/freepdk45/gds_lib/openram_replacements/*.gds` | NEEDS_PACKAGING | include |
| `technology/freepdk45/gds_lib/openyield_repaired/*.gds` | NEEDS_PACKAGING | include if keeping repaired alias metadata |
| `technology/freepdk45/sp_lib/*.sp` | NEEDS_PACKAGING | include for structural `.sp` references |
| `technology/freepdk45/tech/*.ly*` | OPTIONAL | include for optional KLayout DRC/LVS viewing/validation |
| KLayout binary | OPTIONAL | useful for viewing/checking GDS; not needed for default generation |
| OpenRAM source tree | OPTIONAL reference | not required by default legacy CLI smoke tests |
| OpenYield external source tree | OPTIONAL for new path | not required by default legacy CLI smoke tests |

Server-specific findings:

- The legacy generator core resolves the PDK relative to the package root and ran with no server-specific environment variables.
- Many repository docs, tests, simulation netlists, and OpenYield integration scripts contain `/data1/...`, `/tmp/...`, or `/home/...` absolute paths. These are not blocking for default `python -m sram_layoutgen` generation, but they should not be handed to a student as the primary one-command surface without cleanup.
- Current Python package locations under `/data1/qujh/.local` are server-specific. A student release should include `requirements.txt` and a clean virtualenv instruction instead of relying on that environment.

Blocking assessment:

- No runtime blocker was found for current-server execution of the legacy generator.
- Direct handoff blocker: lack of a clean student README/config/examples/requirements packaging layer. This is packaging work, not algorithm recovery.
