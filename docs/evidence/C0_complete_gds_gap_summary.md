# Geometry Connection Gap Summary

## 1. Why current R5 GDS is not a complete SRAM GDS
- The top GDS still contains `39` contract-pin-based signal routes, `8` contract rail stitches, and `2` approximate power straps.
- Only `4` entries are geometry-routed, while `81` referenced pins are not geometry-backed at the module boundary.
- Visual audit found `47` suspicious large rectangles and `47` geometry entries that behave like placeholder stripes/straps rather than exact access routing.

## 2. Which connections are still contract-only
- Wordline contract routes: `4`.
- Bitline contract routes: `32`.
- Control contract routes: `7`.
- Top IO contract routes: `0`.

## 3. Which connections are approximate-only
- Approximate route count from R5 audits: `0`.
- Approximate power geometry count: `2`.
- Placeholder bbox-only geometry detected in top-level rectangles, especially long WL/BL/rail stripes that dominate the visible macro silhouette.

## 4. Which power connections are still contract / approximate
- Contract rail stitches remain on `8` entries.
- Geometry power stitch count is only `0`, so there is no evidence of real per-instance VDD/GND tap closure yet.

## 5. Which pins still lack real geometry
- Wordline missing pin count: `8`.
- Bitline missing pin count: `32`.
- Control missing pin count: `12`.
- Power missing pin count: `29`.
- Top pin missing geometry count: `0`.

## 6. Why KLayout does not look like a real SRAM macro
- The top cell adds long, simple rectangles for routing/power/pin proof over a referenced R3 structure, so the visible overlay looks like stripes, straps, and label-aligned blocks instead of dense access-aware routing.
- The largest visible polygons are wide rails or long channels rather than detailed via ladders, jogs, and exact module landing shapes.

## 7. What C1-C6 must add
- C1: extract OpenRAM / SRAM baseline physical rules, legal layers, pitch, access, rail, and wrapper assumptions needed for real closure.
- C2: replace contract or label-only module pins with real pin geometry and access metadata for WL / BL / BR / control / VDD / GND / top IO.
- C3: rebuild array / row / column / control floorplan around actual access windows and routing channels so the macro shape becomes SRAM-like.
- C4: replace bbox-only stripes with real WL / BL / BR / control / IO routing between extracted source/target geometries.
- C5: replace contract rail stitching and approximate straps with explicit VDD/GND taps, continuity, and per-module geometry.
- C6: run full GDS completeness verification, attempt DRC/LVS on the repaired geometry, and deliver evidence without upgrading signoff claims prematurely.

## 8. Highest priority blockers
- BLK_001 `CONTRACT_ROUTE` on `WL[0]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.
- BLK_002 `CONTRACT_ROUTE` on `WL[1]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.
- BLK_003 `CONTRACT_ROUTE` on `WL[2]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.
- BLK_004 `CONTRACT_ROUTE` on `WL[3]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.
- BLK_005 `CONTRACT_ROUTE` on `BL[0]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.
- BLK_006 `CONTRACT_ROUTE` on `BL[0]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.
- BLK_007 `CONTRACT_ROUTE` on `BL[0]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.
- BLK_008 `CONTRACT_ROUTE` on `BL[0]`: Route terminates on contract pin ownership or prototype-only handoff instead of module pin geometry.

## GDS Visual Audit
- top_cell_name: `openyield_routed_power_pin_sram`
- cell_count: `204`
- recursive_instance_count: `699`
- shapes_without_any_net_to_shape_entry_count: `0`
- net_to_shape_entries_without_gds_shape_match_count: `0`
