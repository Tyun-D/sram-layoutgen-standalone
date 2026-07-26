# Team-B Start Here

## Goal

Help close the remaining OpenYield control-support module backlog without touching project ledgers, reusable release assets, approved reusable GDS, OpenYield source, or Owner-A integration code.

## Locked Commits

- Project baseline branch: `feature/step45-clean-array-aggregation`
- Project baseline commit: `480ca5200f31bb0c21cdcfbdde25ff50f40108b0`
- OpenYield locked commit: `1c34428d8b913963c4971d093b1a7c2df97a2509`

## Your Assigned Modules

- Family 1: `PNAND2`, `PNAND3`, `AND2`, `AND3`
- Family 2: `pdrive`, `pdrive2_for_pre`, `wl_pdrive`
- Family 3: `delay_chain`, `wen_delay_chain`

## Hard Prohibitions

- Do not generate any new GDS unless a later GPT audit explicitly authorizes that exact next stage.
- Do not start `Wave4A2`.
- Do not start `TIME` or final `CONTROL_LOGIC` implementation.
- Do not modify approved reusable GDS.
- Do not modify `/data1/qujh/work/external/OpenYield`.
- Do not modify the four project ledger files.
- Do not change `next_stage_allowed`.
- Do not seal or release anything yourself.

## Stage Discipline

- Execute exactly one GPT-approved minimal stage per round.
- Stop after each round and generate a report plus a tarball of evidence.
- Submit the report and tarball back to project GPT for audit.
- Do not auto-advance without the next GPT instruction.

## Review Discipline

- Machine PASS does not mean reusable.
- Human review is organized by Owner A.
- Team B may produce candidates and evidence only after explicit stage approval.
- Team B never self-labels anything as reusable or human reviewed.

## Working Rules

- Stay inside `collaboration/ALLOWED_PATHS_TEAM_B.txt`.
- Treat `collaboration/FORBIDDEN_PATHS_TEAM_B.txt` as read-only.
- Read `collaboration/EXISTING_GDS_QUALIFICATION_POLICY.md` before evaluating any prior artifact.
- Use `collaboration/team_b/HANDOFF_TEMPLATE.md` for every submission.
