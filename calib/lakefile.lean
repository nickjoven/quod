import Lake
open Lake DSL

package «quod-calib»

-- Same pin as the calibration target: Jin's project and its Mathlib, by path.
require «crouzeix-conjecture» from "jin/Lean"

@[default_target]
lean_lib Quod
