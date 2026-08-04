# WL timing authority review packet

Logic-owner confirmation is limited to four questions:

1. What is the WL active window?
2. What is the maximum permitted WL0-WL15 arrival skew?
3. What is the maximum permitted WL rise/fall time or latest stable time?
4. Do read and write use the same WL timing budget?

Until these are answered, `FORMAL_TIMING_PASS` is prohibited. Geometry and ngspice proxy results may be used only for engineering Pareto ranking.
