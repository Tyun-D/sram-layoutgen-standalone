# Delay Chain SPICE Validation Report

- primary_tool: `ngspice`
- secondary_tool: `Xyce`
- contract: `9-stage loaded inverter chain`, expected polarity `INVERTING`

## Primary Result

- `ngspice` transient completed without syntax/model crash.
- First input rise crossed `0.5 V` at `42.5 ps`; matching output fall crossed `0.5 V` at `215.084 ps`.
- First input fall crossed `0.5 V` at `167.5 ps`; matching output rise crossed `0.5 V` at `337.391 ps`.
- Stable observation points show `Z(300 ps) = -1.099 mV` and `Z(430 ps) = 1.010294 V`.
- Conclusion: `delay_chain` matches the OpenYield `9-stage` inverting contract on the primary server chain.

## Secondary Result

- `Xyce` returned `rc=1`.
- Observed incompatibility: the standalone netlist invocation did not bind `delay_chain` and Xyce reported `Subcircuit DELAY_CHAIN has not been defined`.
- This does not overturn the primary conclusion because the project-selected primary chain is `ngspice`.

## Boundary

- This report proves polarity-consistent transient behavior on the server primary toolchain.
- This report does not claim full timing characterization, PVT coverage, replica-bitline calibration, or post-layout timing signoff.
