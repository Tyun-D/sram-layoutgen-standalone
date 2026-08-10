# V4 DFF False-Positive Postmortem

V4 bundled-DFF authorization is revoked. The ngspice log contained a fatal shorted voltage source, aborted analyses, and failed `.measure` statements. A subprocess return code of zero is not sufficient evidence of functional equivalence.
