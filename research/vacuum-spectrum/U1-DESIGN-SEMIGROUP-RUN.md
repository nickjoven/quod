# Recovered-design U(1) direct propagation execution

Instrument commit: `ac1c679`. State: **unregistered development samples**.

All 80 requested direct evolutions completed without failures in 126.3
seconds, using 30 fresh ground preparations and 10 explicitly reused
corrected finest-grid grounds. Every finest-grid development cell has a
sampled pair that qualifies for both P and P^2 against the existing 1e-6
combined relative error budget.

In particular, the dimensionless pair [20,24] qualifies in all ten cells;
the maximum combined bound there is below 4.41e-8. This reports the sampled
development evidence without choosing a registered time window. Physical
times are scaled by each cell's corrected first-even gap. The odd full gap
is separately reported and is not estimated from even-probe decay.

The combined error adds certified mixture bias and numerical slope error
obtained by comparing direct binary64 correlations against exact infinite-model
intervals. Tolerance agreement is only diagnostic. All earlier and coarser
nonqualifying pairs remain visible in the report.

Report: `u1-design-semigroup.json`. SHA-256:
`22c3f5234f07b6dca2d463f70ac4da811aa26d9ef23a581eec5065456b51d5d8`.
All 109 numerical tests and `git diff --check` passed.
Input/source hashes and full request accounting passed. The archive test
replays every window and combined correlation bound. Methods, commands and
trusted-base limits are in [U1-DESIGN-SEMIGROUP.md](U1-DESIGN-SEMIGROUP.md).
All 42 targets remain unrun; registration and independent review are
outstanding, and original pilot replication still needs the missing code/JSON.
