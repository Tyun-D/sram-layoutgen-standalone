# Post-layout Extraction Provenance Audit

- status: `NOT_AVAILABLE_WITH_CURRENT_EVIDENCE`

## What Was Found

- `klayout` executable is available on the server.
- `technology/freepdk45/tech/freepdk45.lylvs` exists and contains FreePDK45 device extraction plus LVS target-netlist writing logic.
- `technology/freepdk45/tech/freepdk45.lyt` exists and provides the current layer map / connectivity view for FreePDK45.

## What Was Not Found

- No project-local FreePDK45 `magic` techfile or extraction script.
- No project-local `netgen` executable or setup file.
- No proven parasitic RC extraction deck or refreshed LVS binding loop tied to the current project closure run.

## Conclusion

- The repo contains partial KLayout-based LVS/extraction provenance.
- That is not enough to promote current post-layout simulation to available status.
- Current project state remains `NOT_AVAILABLE_WITH_CURRENT_EVIDENCE`.
