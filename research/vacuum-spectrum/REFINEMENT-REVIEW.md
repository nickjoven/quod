# Independent refinement regression review

Date: 2026-09-08. Scope: development-only numerical instrument checks.
This review is not model adjudication, registration, or completed sieve review.

## Executable checks

Run `python3 -m unittest discover -s scripts -p test_vacuum_refinement_contract.py -v`.
The seven tests cover:

- Exact free fourth-order discrete dispersion, normalized sine ground, Haar moments,
  and spectral selection. Small analytic calibration grids are not target cells.
- A wrong boundary closure mutant: replacing the odd extension with zero exterior
  ghosts moves both the exact free spectrum and Haar moment checks.
- Fourth-order convergence for the existing development cell g = 0.10, eta = 1
  on the fixed 600, 1200, 2400 interior-node ladder; residuals, orthogonality,
  and positive semidefinite omitted covariance are also checked.
- Observable offset and overall clock identities for a small Hermitian fixture.
- Full covariance-tail accounting, including the off-diagonal entry, at a
  deliberately inadequate analytic test cutoff.
- Rejection of nonfinite and invalid inputs by the refined angle solver.
- Independent literal checks of the ten development coordinates and 42 target IDs.

No target cells are solved by these tests. Small free calibration grids and the
intentional cutoff-edge fixture are regression controls, not characterization rungs.
Tests establish numerical consistency and mutant discrimination; they do not certify
continuum conclusions, rigorous error enclosures, overlaps, or temporal windows.

## Audit finding

The archived development implementation uses Python `max` in `within_goal`.
A NaN occurring after a finite entry can be ignored by that reduction. JSON
serialization rejects NaN, but a late rejection is insufficient for resilient
cell accounting. The new refinement runner should validate numerical fields
before appending results, reject nonfinite comparison values, preserve failed
cells explicitly, and check exact development, rung, and unrun-target coverage.
The archived source is retained unchanged to preserve its recorded provenance.

The runner's separate regression suite is responsible for those new guards and
failure paths. This review's seven tests are independent solver-level checks.
