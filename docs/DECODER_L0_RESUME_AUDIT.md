# Decoder L0 Resume Audit

- generated_at: `2026-07-31T08:34:02Z`
- current_git_head: `62c3d663d2dc4011b9c8d06c13d080c25535a327`
- expected_pair_count: `2304`
- completed_pair_count: `2304`
- passed_pair_count: `1374`
- failed_pair_count: `930`
- missing_pair_count: `0`
- corrupt_or_incomplete_pair_count: `0`
- duplicate_pair_count: `0`
- last_completed_pair: `WORDLINEDRIVER|MY|WORDLINEDRIVER|MY|0.07|horizontal`
- last_output_timestamp: `2026-07-30T20:33:05Z`

## Notes

- Expected pair space is rebuilt from the legal orientation table, ordered left/right gate pairs, the four gap candidates in the matrix, and a horizontal placement axis.
- Missing pair set already includes any pair whose aggregate row exists but final GDS/DRC artifact is absent, empty, or SHA-mismatched.
