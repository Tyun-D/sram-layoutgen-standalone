# Shared Code Ownership

## Unique Shared-Code Owner

- Owner A owns all shared code that can affect both people:
- shared DFF-array core
- integration branch logic
- final `CONTROL_LOGIC` assembly and glue
- project ledgers
- reusable registry and release/seal flow

## Team-B Rule

- Owner B may create Team-B-specific helpers under the allowlist paths only.
- Owner B must not edit shared DFF-array code unless Owner A hands off one explicit commit and cites it in the handoff report.
- Owner B must not revert or overwrite concurrent Owner-A work.

## Shared Interfaces

- Team-B outputs feed Owner-A review and integration only through handoff artifacts, cherry-pickable commits, patch/bundle evidence, and GPT-approved stage reports.
- Team-B does not merge directly into the integration branch.
