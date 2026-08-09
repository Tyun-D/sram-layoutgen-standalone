# Full SRAM Control Path Authority

- status: `CONTROL_PATH_PHYSICAL_ASSETS_NOT_READY`
- can generate control path candidates: `False`
- reason: Required TIME/control physical assets are missing or only metadata/candidate geometry.

| module | ready_for_top | blocker |
|---|---:|---|
| `control_logic` | `False` | M12C2 says can_claim_control_logic_physical_ready=false; CONTROL_LOGIC generator manifest says candidate geometry does not claim final routing or signoff; time/control placement readiness report marks control subblocks physical_ready=false |
| `DFF` | `True` | - |
| `DFF_BUF` | `True` | - |
| `delay_chain` | `False` | DELAY_CHAIN module manifest says candidate geometry does not claim final routing or signoff; time/control placement readiness marks DELAY_CHAIN_CLUSTER physical_ready=false; no standalone final-GDS connectivity/foreign-net/negative-suite top-use gate found for delay_chain_v2 |
| `pdrive` | `False` | no pdrive_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints; no pdrive pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found |
| `wl_pdrive` | `False` | no wl_pdrive_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints; no wl_pdrive pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found |
| `pdrive2_for_pre` | `False` | no pdrive2_for_pre_v2 GDS asset found in repo, evidence package, /data1 search, historical worktrees, or checkpoints; no pdrive2_for_pre pin map, DRC, connectivity, power endpoint, pin-access, determinism, or negative-suite evidence found |
