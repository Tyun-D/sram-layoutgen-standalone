# Full SRAM Top Physical Pin Contract

- status: `READY`
- functional oracle: `FUNCTIONAL_ORACLE_PENDING`
- formal timing authority: `TIMING_AUTHORITY_PENDING`
- preferred boundary side is physical-design policy, not logical authority.

| pin | direction | bit | preferred side | allowed metal |
|---|---|---:|---|---|
| `addr[0]` | `input` | `0` | `left` | `m4/m5` |
| `addr[1]` | `input` | `1` | `left` | `m4/m5` |
| `addr[2]` | `input` | `2` | `left` | `m4/m5` |
| `addr[3]` | `input` | `3` | `left` | `m4/m5` |
| `din[0]` | `input` | `0` | `bottom` | `m4/m5` |
| `dout[0]` | `output` | `0` | `bottom` | `m4/m5` |
| `din[1]` | `input` | `1` | `bottom` | `m4/m5` |
| `dout[1]` | `output` | `1` | `bottom` | `m4/m5` |
| `din[2]` | `input` | `2` | `bottom` | `m4/m5` |
| `dout[2]` | `output` | `2` | `bottom` | `m4/m5` |
| `din[3]` | `input` | `3` | `bottom` | `m4/m5` |
| `dout[3]` | `output` | `3` | `bottom` | `m4/m5` |
| `din[4]` | `input` | `4` | `bottom` | `m4/m5` |
| `dout[4]` | `output` | `4` | `bottom` | `m4/m5` |
| `din[5]` | `input` | `5` | `bottom` | `m4/m5` |
| `dout[5]` | `output` | `5` | `bottom` | `m4/m5` |
| `din[6]` | `input` | `6` | `bottom` | `m4/m5` |
| `dout[6]` | `output` | `6` | `bottom` | `m4/m5` |
| `din[7]` | `input` | `7` | `bottom` | `m4/m5` |
| `dout[7]` | `output` | `7` | `bottom` | `m4/m5` |
| `din[8]` | `input` | `8` | `bottom` | `m4/m5` |
| `dout[8]` | `output` | `8` | `bottom` | `m4/m5` |
| `din[9]` | `input` | `9` | `bottom` | `m4/m5` |
| `dout[9]` | `output` | `9` | `bottom` | `m4/m5` |
| `din[10]` | `input` | `10` | `bottom` | `m4/m5` |
| `dout[10]` | `output` | `10` | `bottom` | `m4/m5` |
| `din[11]` | `input` | `11` | `bottom` | `m4/m5` |
| `dout[11]` | `output` | `11` | `bottom` | `m4/m5` |
| `din[12]` | `input` | `12` | `bottom` | `m4/m5` |
| `dout[12]` | `output` | `12` | `bottom` | `m4/m5` |
| `din[13]` | `input` | `13` | `bottom` | `m4/m5` |
| `dout[13]` | `output` | `13` | `bottom` | `m4/m5` |
| `din[14]` | `input` | `14` | `bottom` | `m4/m5` |
| `dout[14]` | `output` | `14` | `bottom` | `m4/m5` |
| `din[15]` | `input` | `15` | `bottom` | `m4/m5` |
| `dout[15]` | `output` | `15` | `bottom` | `m4/m5` |
| `clk` | `input` | `None` | `left` | `m4/m5/m6` |
| `csb` | `input` | `None` | `left` | `m4/m5/m6` |
| `web` | `input` | `None` | `left` | `m4/m5/m6` |
| `vdd` | `inout` | `None` | `top_bottom_straps` | `m4/m5/m6` |
| `gnd` | `inout` | `None` | `top_bottom_straps` | `m4/m5/m6` |
| `PRE` | `internal_control_observable` | `None` | `debug_or_internal_no_required_top_pin` | `m3/m4` |
| `WL_EN` | `internal_control_observable` | `None` | `debug_or_internal_no_required_top_pin` | `m3/m4` |
| `S_EN` | `internal_control_observable` | `None` | `debug_or_internal_no_required_top_pin` | `m3/m4` |
| `W_EN` | `internal_control_observable` | `None` | `debug_or_internal_no_required_top_pin` | `m3/m4` |
| `TIME` | `internal_control_observable` | `None` | `debug_or_internal_no_required_top_pin` | `m3/m4` |
