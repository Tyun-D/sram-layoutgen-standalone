# PDK interconnect RC authority audit

No local FreePDK45 technology, KLayout, Magic, or OpenRCX asset provides a complete traceable set of metal sheet resistance, fringe/area capacitance, and via resistance values for this flow. Existing extracted SRAM artifacts do not provide a geometry-to-RC calibration contract.

The highest defensible evidence remains `NORMALIZED_GEOMETRY_RC_PROXY`. All V2 reports state `NOT_POST_LAYOUT_PEX`; absolute R, C, and RC fields remain `AUTHORITY_PENDING` rather than using guessed values.
