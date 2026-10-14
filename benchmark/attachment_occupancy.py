#!/usr/bin/env python3
"""Expected compactor edge volume for the ideal dyadic attachment model.

This is a random-subset model, not a fit to timings or a prediction of elapsed
time. It applies to hierarchy/distance weights with deterministic aligned core
partitions. Core-only shuffled and globally random weights do not satisfy that
partition assumption. Finite seeded PRNG output is a measured realization, not
a proof of uniformity over all shortcut subsets.

Numerical cutoffs bound the deliberately omitted contribution to an expected
edge count, rather than bounding only a probability. The reported truncation
bound excludes ordinary floating-point roundoff; it is not an interval-arithmetic
certificate. Products use log1p, occupied probabilities use expm1, and sums use
fsum to avoid the main cancellation and accumulation problems.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import itertools
import json
import math
from typing import Any


DEFAULT_ABSOLUTE_COUNT_TOLERANCE = 1e-15
MAX_EXACT_FLOAT_INTEGER = (1 << 53) - 1


def _integer(value: int, name: str, minimum: int = 0) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")


def _tolerance(value: float) -> None:
    if not math.isfinite(value) or value < 0:
        raise ValueError("absolute count tolerance must be finite and nonnegative")


@dataclass(frozen=True)
class Avoidance:
    probability: float
    occupied_probability: float
    # None represents a returned zero probability, either exact or truncated.
    # `method` distinguishes those cases without nonstandard JSON infinities.
    log_probability: float | None
    omitted_count_bound: float
    product_terms: int
    method: str


def zero_probability(
    population: int,
    selected: int,
    marked: int,
    *,
    count_scale: int = 1,
    absolute_count_tolerance: float = DEFAULT_ABSOLUTE_COUNT_TOLERANCE,
) -> Avoidance:
    """Probability a uniform selected-subset contains no marked population item.

    P0 = C(population-marked, selected) / C(population, selected).
    Symmetry permits the shorter product, of length min(selected, marked):
    product_i (1 - max(selected, marked)/(population-i)).

    A cutoff is allowed only if its omitted contribution to a count multiplied
    by count_scale is below absolute_count_tolerance. Setting the tolerance to
    zero disables that approximation (ordinary float roundoff remains).
    """
    for name, value in (("population", population), ("selected", selected), ("marked", marked)):
        _integer(value, name)
    _integer(count_scale, "count_scale", 1)
    _tolerance(absolute_count_tolerance)
    if selected > population or marked > population:
        raise ValueError("selected and marked counts cannot exceed population")
    if population > MAX_EXACT_FLOAT_INTEGER:
        raise ValueError("population exceeds the supported exactly representable float-integer range")
    if selected == 0 or marked == 0:
        return Avoidance(1.0, 0.0, 0.0, 0.0, 0, "exact_one")
    if selected + marked > population:
        return Avoidance(0.0, 1.0, None, 0.0, 0, "exact_zero")

    small, large = sorted((selected, marked))
    # Every factor is <= exp(-large/population), hence P0 <= exp(-Bh/U).
    # Two extra natural-log units leave a generous margin at the floating-point
    # cutoff comparison. Return the requested tolerance as a conservative
    # truncation budget, rather than an underflowed exponential advertised as 0.
    if absolute_count_tolerance > 0:
        cutoff = math.log(count_scale) - math.log(absolute_count_tolerance) + 2.0
        if (selected * marked) / population >= cutoff:
            return Avoidance(0.0, 1.0, None, absolute_count_tolerance, 0, "exponential_bound")

    log_p0 = math.fsum(math.log1p(-large / (population - i)) for i in range(small))
    return Avoidance(
        math.exp(log_p0),
        -math.expm1(log_p0),
        log_p0,
        0.0,
        small,
        "log_product",
    )


@dataclass(frozen=True)
class CoreQuotient:
    core_block_size: int
    components: int
    expected_edges: float
    absolute_truncation_bound: float
    guaranteed_path_pairs: int
    nonadjacent_pairs: int
    shortcut_slots_per_nonadjacent_pair: int
    avoidance_method: str
    product_terms: int


def expected_core_quotient(
    core_vertices: int,
    shortcuts: int,
    core_block_size: int,
    *,
    absolute_count_tolerance: float = DEFAULT_ABSOLUTE_COUNT_TOLERANCE,
) -> CoreQuotient:
    """Expected edges after merging aligned blocks in a path-plus-shortcuts core.

    For q core vertices, B uniformly selected non-path pairs, block size s and
    k=q/s blocks, adjacent blocks have k-1 guaranteed path edges. Every other
    block pair has s*s eligible shortcut slots, giving

      (k-1) + (C(k,2)-(k-1)) * (1-C(U-s*s,B)/C(U,B)),

    where U=C(q,2)-(q-1). Internal and parallel-edge removal are both included.

    This floating-point helper conservatively requires q*q <= 2**53-1 so
    every pair population, possible block-pair slot count and exact edge
    count is representable as a float integer. It intentionally rejects some
    much larger theoretical cores whose particular quotient could be computed
    exactly; the supported attachment CLI has q <= 2**20.
    """
    _integer(core_vertices, "core_vertices", 2)
    _integer(shortcuts, "shortcuts")
    _integer(core_block_size, "core_block_size", 1)
    _tolerance(absolute_count_tolerance)
    if core_vertices & (core_vertices - 1) or core_block_size & (core_block_size - 1):
        raise ValueError("core vertices and block size must be powers of two")
    if core_block_size > core_vertices:
        raise ValueError("core block size exceeds the core")
    # Check before exact-result shortcuts too: those still return float counts.
    # A uniform q-squared bound covers every quotient of a supported core,
    # including the unused slot count in the terminal one-component quotient.
    if core_vertices * core_vertices > MAX_EXACT_FLOAT_INTEGER:
        raise ValueError("squared core size exceeds the supported exactly representable float-integer range")
    available = core_vertices * (core_vertices - 1) // 2 - (core_vertices - 1)
    if shortcuts > available:
        raise ValueError("too many shortcuts for the simple path-backed core")
    components = core_vertices // core_block_size
    guaranteed = components - 1
    nonadjacent = components * (components - 1) // 2 - guaranteed
    slots = core_block_size * core_block_size
    if core_block_size == 1:
        # Preserve this exactly known integer instead of reconstructing it by
        # multiplying a rounded B/U probability by U.
        return CoreQuotient(1, components, float(core_vertices - 1 + shortcuts), 0.0,
                            guaranteed, nonadjacent, 1, "exact_core_count", 0)
    if nonadjacent == 0:
        return CoreQuotient(core_block_size, components, float(guaranteed), 0.0,
                            guaranteed, 0, slots, "no_nonadjacent_pairs", 0)
    avoidance = zero_probability(
        available, shortcuts, slots, count_scale=nonadjacent,
        absolute_count_tolerance=absolute_count_tolerance,
    )
    expected = math.fsum((float(guaranteed), nonadjacent * avoidance.occupied_probability))
    return CoreQuotient(core_block_size, components, expected, avoidance.omitted_count_bound,
                        guaranteed, nonadjacent, slots, avoidance.method, avoidance.product_terms)


def attachment_expectation(
    n: int,
    density: int,
    block_size: int,
    *,
    absolute_count_tolerance: float = DEFAULT_ABSOLUTE_COUNT_TOLERANCE,
) -> dict[str, Any]:
    """Expected original-plus-core contraction inputs for one supported model."""
    _integer(n, "n", 32)
    _integer(density, "density", 1)
    _integer(block_size, "block_size", 1)
    _tolerance(absolute_count_tolerance)
    if n > 1 << 22 or n & (n - 1) or density > 512 or block_size not in (4, 16):
        raise ValueError("unsupported attachment dimensions")
    m = n * density
    q = n // block_size
    local = n - q
    core_edges = m - local
    shortcuts = core_edges - (q - 1)
    available = q * (q - 1) // 2 - (q - 1)
    if m > 1 << 27 or m >= 0x3F3F3F3F or core_edges < q - 1 or shortcuts > available:
        raise ValueError("attachment core violates simple-graph capacity or edge budget")

    quotients = [expected_core_quotient(q, shortcuts, 1 << r,
                                      absolute_count_tolerance=absolute_count_tolerance)
                 for r in range(q.bit_length())]
    rounds: list[dict[str, Any]] = [{
        "round": 1, "input_vertices": n, "expected_input_edges": float(m),
        "input_absolute_truncation_bound": 0.0, "output_vertices": q,
        "expected_output_edges": float(core_edges), "output_absolute_truncation_bound": 0.0,
        "original_component_count": q, "original_component_size": block_size,
    }]
    for r, current in enumerate(quotients[:-1]):
        following = quotients[r + 1]
        rounds.append({
            "round": r + 2, "input_vertices": current.components,
            "expected_input_edges": current.expected_edges,
            "input_absolute_truncation_bound": current.absolute_truncation_bound,
            # Production removes the final isolated quotient vertex.
            "output_vertices": following.components if following.components > 1 else 0,
            "expected_output_edges": following.expected_edges,
            "output_absolute_truncation_bound": following.absolute_truncation_bound,
            "original_component_count": following.components,
            "original_component_size": block_size * following.core_block_size,
        })
    volume = math.fsum(row["expected_input_edges"] for row in rounds)
    error_bound = math.fsum(row["input_absolute_truncation_bound"] for row in rounds)
    return {
        "schema": "attachment_occupancy_v1",
        "model": "ideal uniform subset of non-path core pairs with fixed dyadic partitions",
        "applicable_weight_modes": ["hierarchy", "distance"],
        "applicable_endpoint_modes": ["leaf", "community"],
        "not_applicable_weight_modes": ["shuffled", "random"],
        "predicts_elapsed_time": False,
        "n": n, "m": m, "density": density, "block_size": block_size,
        "core_vertices": q, "local_star_edges": local, "core_edges": core_edges,
        "shortcuts": shortcuts, "available_shortcut_pairs": available,
        "first_round_retained_edge_fraction": core_edges / m,
        "rounds": rounds,
        "core_quotients": [asdict(item) for item in quotients],
        "expected_edge_input_volume": volume,
        "normalized_edge_input_volume": volume / m,
        "absolute_volume_truncation_bound": error_bound,
        "normalized_volume_truncation_bound": error_bound / m,
        "per_quotient_absolute_count_tolerance": absolute_count_tolerance,
        "numerical_scope": "truncation bounds exclude ordinary floating-point roundoff",
        "sampling_scope": "finite PRNG graph seeds are realizations, not a proof of uniform subset sampling",
    }


def self_test() -> dict[str, Any]:
    """Bounded exact-combination and independently enumerated tiny-core checks."""
    probability_cases = 0
    for population in range(25):
        for selected in range(population + 1):
            denominator = math.comb(population, selected)
            for marked in range(population + 1):
                numerator = math.comb(population - marked, selected) if population - marked >= selected else 0
                result = zero_probability(population, selected, marked, absolute_count_tolerance=0)
                exact_p0 = numerator / denominator
                exact_occupied = (denominator - numerator) / denominator
                if not (math.isclose(result.probability, exact_p0, rel_tol=5e-14, abs_tol=2e-15) and
                        math.isclose(result.occupied_probability, exact_occupied, rel_tol=5e-14, abs_tol=2e-15)):
                    raise AssertionError((population, selected, marked, result, exact_p0))
                probability_cases += 1

    cutoff = zero_probability(512, 256, 256, count_scale=10**12)
    exact_omitted_count = 10**12 / math.comb(512, 256)
    if cutoff.method != "exponential_bound" or not exact_omitted_count <= cutoff.omitted_count_bound <= 1e-15:
        raise AssertionError("count-scaled avoidance cutoff failed its exact combination bound")

    enumeration_cases = 0
    for q in (4, 8):
        path = [(v - 1, v) for v in range(1, q)]
        available = [(u, v) for u in range(q) for v in range(u + 2, q)]
        for count in sorted({0, 1, 2, len(available) - 1, len(available)}):
            sums = [0] * q.bit_length()
            realizations = 0
            for chosen in itertools.combinations(available, count):
                graph = [*path, *chosen]
                for r in range(q.bit_length()):
                    size = 1 << r
                    quotient_pairs = {(u // size, v // size) for u, v in graph if u // size != v // size}
                    sums[r] += len(quotient_pairs)
                realizations += 1
            for r, total in enumerate(sums):
                predicted = expected_core_quotient(q, count, 1 << r, absolute_count_tolerance=0)
                if not math.isclose(predicted.expected_edges, total / realizations, rel_tol=2e-14, abs_tol=2e-14):
                    raise AssertionError((q, count, r, predicted, total, realizations))
                enumeration_cases += 1

    dimensions = [(32, 1, 4), (64, 1, 16), (64, 2, 4), (1024, 2, 16),
                  (512, 16, 4), (8192, 16, 16)]
    for n, density, b in dimensions:
        result = attachment_expectation(n, density, b)
        rows = result["rounds"]
        if (len(rows) != 1 + int(math.log2(n // b)) or rows[0]["expected_input_edges"] != n * density or
                rows[0]["expected_output_edges"] != n * density - n + n // b or
                rows[-1]["expected_input_edges"] != 1 or rows[-1]["output_vertices"] != 0 or
                rows[-1]["original_component_size"] != n):
            raise AssertionError("attachment round indexing or original-component dimensions failed")
    rejected = 0
    for args in [(32, 2, 4), (512, 2, 16), (48, 2, 4), (64, 2, 8), (64, 0, 4),
                 (1 << 22, 33, 4), (1 << 23, 2, 16)]:
        try:
            attachment_expectation(*args)
        except ValueError:
            rejected += 1
        else:
            raise AssertionError(("invalid attachment dimensions accepted", args))
    domain_rejected = 0
    for args in [(1 << 27, 0, 1), (1 << 54, 0, 1),
                 (1 << 54, 0, 1 << 53), (1 << 54, 0, 1 << 54)]:
        try:
            expected_core_quotient(*args)
        except ValueError:
            domain_rejected += 1
        else:
            raise AssertionError(("oversized core accepted through a shortcut branch", args))
    # Largest supported dyadic q: exact-result branches must retain their counts.
    boundary_q = 1 << 26
    if (expected_core_quotient(boundary_q, 0, 1).expected_edges != boundary_q - 1 or
            expected_core_quotient(boundary_q, 0, boundary_q // 2).expected_edges != 1 or
            expected_core_quotient(boundary_q, 0, boundary_q).expected_edges != 0):
        raise AssertionError("supported core-domain boundary changed exact counts")
    return {"validation": "pass", "exact_probability_cases": probability_cases,
            "enumerated_quotient_expectations": enumeration_cases,
            "count_scaled_cutoff_checks": 1, "supported_dimension_cases": len(dimensions),
            "invalid_dimension_cases": rejected,
            "oversized_core_rejections": domain_rejected, "exact_domain_boundary_cases": 3}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("self-test", help="run bounded exact-combination and tiny-core enumeration checks")
    predict = commands.add_parser("predict", help="emit ideal expected contraction volume as JSON")
    predict.add_argument("--n", type=int, required=True)
    predict.add_argument("--density", type=int, required=True)
    predict.add_argument("--block-size", type=int, choices=(4, 16), required=True)
    predict.add_argument("--absolute-count-tolerance", type=float, default=DEFAULT_ABSOLUTE_COUNT_TOLERANCE)
    args = parser.parse_args()
    try:
        result = self_test() if args.command == "self-test" else attachment_expectation(
            args.n, args.density, args.block_size, absolute_count_tolerance=args.absolute_count_tolerance)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
