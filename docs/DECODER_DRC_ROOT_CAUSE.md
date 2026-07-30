# Decoder DRC Root Cause

- fresh decoder rebuild marker_count: `2663`
- Dominant rules are systemic grid/contact/template violations rather than a handful of isolated parent routes.
- Current decoder children are L3 candidate geometry with `not_DRC_clean_claimed = true` in their own generation reports.
- Because child internals are not approved hard-macro signoff assets, the project cannot legitimately claim decoder top DRC closure without new child-level authority.

## Dominant Rule Families

- `GRID: vertexes on layer metal1 not on grid of 0.0025`: `747`
- `GRID: vertexes on layer cont not on grid of 0.0025`: `525`
- `GRID: vertexes on layer poly not on grid of 0.0025`: `331`
- `GRID: vertexes on layer active not on grid of 0.0025`: `256`
- `CONTACT.1`: `224`
- `GRID: vertexes on layer nplus not on grid of 0.0025`: `136`
- `GRID: vertexes on layer pplus not on grid of 0.0025`: `117`
- `CONTACT.3`: `82`
- `GRID: vertexes on layer well not on grid of 0.0025`: `71`
- `GRID: vertexes on layer vtg not on grid of 0.0025`: `60`
