# Depth-query correctness completion

Root reports `depth-correctness03` completed with actual exit 0 in 41.34 seconds: 32 native and 36 sanitizer owned-child receipts, all groups empty. Its final gate is the completion evidence; the first two failed attempts remain preserved. Attempt01 stopped at the timing-only retention-main compile guard. Attempt02's native solver passed but the parser rejected its two legitimate topology diagnostics. Neither failed attempt is presented as a complete gate.

The third attempt follows the separately reviewed instrumentation separation and exact diagnostic parser repairs. Four parser regression groups passed first with actual exit 0. The production sources and frozen candidate build did not change for either repair. Full details and raw receipts are under `benchmark/results/scaling-investigation-2026-10-15/depth-correctness03/`; peer reviews and runner preparation remain under `benchmark/scaling_investigation/candidates/`.

This note records root's completed execution report; its author did not launch native work. The fresh paired timing campaign began only after this gate and is a separate experiment.
