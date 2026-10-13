#!/usr/bin/env python3
"""Independent exact-rational checks of the numeric expectation evaluator."""
import importlib.util
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "plot_continuation_retention.py"
spec = importlib.util.spec_from_file_location("retention", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
checked = 0
capped = 0
max_absolute_error = 0.0
max_relative_error = 0.0
for n in (4, 8, 16, 32, 64, 128):
    for density in sorted({1, 2, 3, 4, (n-1)//2}):
        m = density*n
        if m > math.comb(n, 2):
            continue
        B, U = m-n+1, math.comb(n, 2)-n+1
        for r in range(n.bit_length()):
            b, q = 2**r, n//2**r
            S = math.comb(q, 2)-(q-1)
            if S == 0:
                exact = Fraction(q-1)
            else:
                numerator = 0 if U-b*b < B else math.comb(U-b*b, B)
                no_hit = Fraction(numerator, math.comb(U, B))
                exact = q-1+S*(1-no_hit)
            point = module.expected_residual(n, density, r)
            estimate = point["expected_edges_estimate"]
            error = float(abs(Fraction.from_float(estimate)-exact))
            tolerance = 16*math.ulp(max(1.0, float(exact))) + point["saturation_error_bound_edges"]
            if error > tolerance:
                raise AssertionError((n, density, r, error, tolerance))
            if point["numeric_method"] == "tail_capped_no_hit_le_exp_minus_50":
                capped += 1
                # The capped expectation is an exact integer. This checks the
                # omitted rational probability against the numeric expression
                # of the analytical S*exp(-50) bound, with rounding allowance.
                if Fraction.from_float(estimate) < exact or error > point["saturation_error_bound_edges"]*(1+1e-12):
                    raise AssertionError("saturation bound violated")
            max_absolute_error = max(max_absolute_error, error)
            if exact:
                max_relative_error = max(max_relative_error, error/float(exact))
            checked += 1
output = {
    "status": "pass", "exact_rational_cases": checked,
    "script_sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
    "sizes": [4, 8, 16, 32, 64, 128], "saturated_cases_checked": capped,
    "reference": "fractions.Fraction and independent math.comb(U-b*b,B)/math.comb(U,B)",
    "maximum_absolute_error_edges": max_absolute_error,
    "maximum_relative_error_nonzero_expectation": max_relative_error,
    "acceptance": "16 ulps at scale max(1,exact expectation), plus the analytical saturation bound",
    "scope": "Finite small-integer checks, not a proof of correctly rounded libm evaluations",
}
Path(__file__).with_name("math_validation.json").write_text(json.dumps(output, indent=2)+"\n")
print(json.dumps(output, indent=2))
