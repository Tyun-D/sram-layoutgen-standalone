# Project Long Range Delta Review Checklist

| item | focus | evidence |
| --- | --- | --- |
| P0-003 owner-confirmation resolution | Confirm blocked-external classification is correctly separated from Team B owner review | docs/P0_003_OWNER_CONFIRMATION_RESOLUTION.md |
| Formal config inventory | Check source-backed vs degraded config rows and support levels | docs/FORMAL_SRAM_CONFIG_INVENTORY.csv |
| Claim boundary | Verify unsupported signoff/tapeout claims are blocked | docs/M2R_SIGNOFF_BOUNDARY_AUDIT.md; docs/PROJECT_CLAIM_POLICY.md |
| Decoder boundary | Verify decoder remains blocked for physical closure because placement/handoff are still metadata-only and no decoder gate harness exists | docs/DECODER_PHYSICAL_CLOSURE_AUDIT.md |
| Multi-bank boundary | Verify single-bank authority remains the current boundary | docs/MULTIBANK_PHYSICAL_FLOW_AUDIT.md |
| Figure and table index | Verify each figure row is tied to a real source path and SHA | docs/FINAL_FIGURE_AND_TABLE_INDEX.csv |
| Project technical draft | Verify claims match current evidence and limitations | docs/PROJECT_FINAL_TECHNICAL_DRAFT.md |
