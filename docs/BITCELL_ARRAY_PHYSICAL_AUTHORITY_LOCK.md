# Bitcell array physical authority lock

No audited local file qualifies as an approved standalone full 16-row bitcell-array handoff.

The 4x4 `bitcell_array.gds` is explicitly an L3 sizing template with no DRC claim. The 16x16 golden-reference GDS contains real flat storage geometry, but not a standalone array hierarchy or authoritative WL/BL/BR/power pin manifest, and its report leaves external DRC/LVS/PEX pending.

Therefore `ARRAY_INTEGRATION_LEVEL=FLOORPLAN_FEASIBILITY_SHELL` and `FULL_BITCELL_ARRAY_GDS_INTEGRATION=PENDING` remain locked. `TREAL_L3_array_authority_pending` is retained only as a failed diagnostic: 4707 DRC markers plus connectivity, power, foreign-net, and alignment failures.
