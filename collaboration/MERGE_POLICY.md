# Merge Policy

## Authority

- Owner A is the only merge authority for this collaboration split.
- Owner B submits evidence, commits, patch, bundle, and reports. Owner B does not merge, seal, or release.

## Required Handoff Shape

- One GPT-approved minimal stage per round.
- One module-focused report per round.
- One evidence tar per round.
- Cherry-pickable commits with no forbidden-path edits.

## Integration Rules

- Owner A reviews Team-B handoff against `collaboration/HANDOFF_TEMPLATE.md` equivalent fields before integration.
- Owner A may cherry-pick Team-B commits onto the integration branch only after GPT audit says the submitted stage passed.
- If a Team-B change touches shared code or a forbidden path, the handoff is rejected until split or reworked.

## Conflict Rules

- Team-B branch rebases or conflict resolution are Owner-A coordinated.
- Team B must not resolve conflicts by changing ledgers, approved reusable GDS, OpenYield, `TIME` integration code, or shared DFF-array code.
