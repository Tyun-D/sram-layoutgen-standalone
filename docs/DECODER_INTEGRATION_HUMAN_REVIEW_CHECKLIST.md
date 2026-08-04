# Decoder Integration Human Review Checklist

- Verify baseline, Candidate A, Candidate B top and integration-shell GDS open cleanly.
- Confirm Candidate A/B integration machine gates report DRC=0, connectivity PASS, foreign-net PASS, power PASS, determinism PASS.
- Inspect WL0-WL15 route atlas for monotonic exclusive routing.
- Inspect power atlas and pin atlas against integration shell review atlas.
- Cross-check candidate B route-length improvements against baseline summary.
