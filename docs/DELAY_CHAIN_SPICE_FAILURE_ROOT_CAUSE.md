# Delay Chain SPICE Failure Root Cause

## Result

- status: `ROOT_CAUSE_IDENTIFIED`
- failure_class: `EXPECTATION_AND_MEASUREMENT_MISMATCH`

## Evidence

- log excerpt: `docs/DELAY_CHAIN_SPICE_FAILURE_LOG_EXCERPT.txt`
- testbench: `simulation/spice/testbenches/delay_chain_polarity.sp`
- netlist: `simulation/spice/netlists/delay_chain.inc`
- planning contract: `docs/openyield_delay_chain_testbench_plan_report.json`

## Key Facts

- the netlist has `9` cascaded inverter stages: `Xdinv0` through `Xdinv8`
- each stage output carries `4` explicit inverter loads
- the existing smoke script classifies the case as `"buffer"` and says the output should preserve polarity
- the planning contract already identifies `DELAY_CHAIN` as `rbl -> rbl_delay` timing logic with `stage_count = 9`

## Why The Existing Smoke Fails

- an odd number of inverters implies steady-state inversion, not polarity preservation
- the low measurement window is only `0-180 ps`
- the input pulse rises at `40 ps`
- with 9 loaded stages, the delayed falling transition does not enter that early window, so `z_low` stays near `VDD`
- the log shows successful transient completion, not syntax/model failure

## Conclusion

- The current failure is not strong evidence that the formal circuit is wrong.
- The present evidence supports a more specific conclusion:
  - the smoke test expectation is inconsistent with the netlist structure
  - the measurement window is too short for the actual loaded delay chain
- No formal GDS change is justified by this failure alone.
