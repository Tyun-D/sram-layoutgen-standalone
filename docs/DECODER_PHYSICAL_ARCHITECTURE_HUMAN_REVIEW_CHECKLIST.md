# Decoder Physical Architecture Human Review Checklist

- Open each `integration_shell_clean.gds` before any atlas.
- Confirm the Decoder child has two physical rows and three Top stages occupy distinct Y intervals.
- Confirm all 16 wordline drivers are row-aligned and outputs face the approved array shell.
- Cross-check `POWER_ENDPOINT_COVERAGE.csv` against `POWER_WITNESS_ATLAS.gds`; each candidate has 148 required endpoints.
- Confirm combined `integration_drc.lyrdb` contains zero markers.
- Compare P2 and P3 using `DECODER_PHYSICAL_ARCHITECTURE_COMPARISON.csv`; P3 trades smaller area for longer decoder-to-driver routing.
- Review `WL_GEOMETRY_RC.csv`, `WL_TIMING_PROXY.csv`, and waveform logs. These are normalized geometry RC proxies, not PEX.
- Treat `rc_proxy_threshold_passed=false` and `TIMING_BUDGET_AUTHORITY_PENDING` as unresolved timing review items.
- Treat the array object as `approved_nonzero_physical_shell`; full bitcell-array GDS integration remains pending.
- Do not promote these artifacts beyond `FLOORPLAN_FEASIBILITY_SHELL` without full array GDS, LVS, PEX, and an authoritative timing budget.
