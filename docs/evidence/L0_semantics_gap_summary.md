# L0 Semantics Gap Summary

## Closed

- `bitcell_array`, `dummy_array`, `replica_array`, `row_decoder`, `wordline_driver`, `column_mux`, `sense_amp`, `write_driver`, and `precharge` now have source-backed L0 semantic rows with known role, ports, and top-level connectivity.

## Remaining L0 Gaps

- OpenYield has no explicit reusable `SRAM_TOP` or `BANK` class. The current top-level SRAM semantics live in `Sram6TCoreTestbench.create_testbench()`.
- OpenYield source is row/column oriented. It does not define first-class `word_size`, `num_words`, `words_per_row`, `num_banks`, `num_ports`, or write-mask parameters.
- `TIME` is a composite control/timing generator, so `CONTROL_LOGIC`, `GATED_CLOCK_PATH`, `WORDLINE_ENABLE_PATH`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, and `WRITE_ENABLE_PATH` are source-backed but not yet frozen as standalone local semantic objects.
- Column muxing is only partially generalized. The current source hard-codes `mux_in=2` when `choose_columnmux=True`.
- Local layoutgen still uses metadata/proxy/control-adapter layers for decoder/control integration rather than one closed canonical semantic contract.

## L0 Blocking Decision

- L0 semantic closure is materially advanced and reportable.
- L0 is not strong enough yet to enter unrestricted L1 physical primitive closure.
- The largest blocker is the missing canonical mapping from logical SRAM spec terms (`word_size`, `num_words`, `words_per_row`) to OpenYield physical row/column semantics plus composite `TIME` decomposition.
