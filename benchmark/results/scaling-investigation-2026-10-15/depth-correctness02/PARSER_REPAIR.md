# Preserved attempt02 parser rejection

Attempt02's native retention test exited zero and printed its exact expected coverage summary. The controller rejected the fixture's legitimate stderr, so the attempt remains failed; its partial native results do not establish the full sanitizer gate.

`benchmark/retention_control.cpp:134` emits one topology-attempt diagnostic for each crossover fixture. `test/retention_control_test.cpp:206` calls the two fixed `gnm_random` cases. The preserved successful child stderr is exactly:

```text
crossover_topology_attempts=1
crossover_topology_attempts=1
```

The pre-repair runner, documentation and first repair review are copied under `runner-repair-before/`. The old runner SHA-256 is `2a2d4b7c0b6d70cfe3488b2d8940bbe978e04e0aa1c405f356eebb09b0504ac1`. `parser-repair.diff` contains the only runner change: a literal expected stderr string and exact equality to that string. No coverage count, solver, native compile/link recipe, resource rule or cleanup proof changed.

Final source SHA-256 values:

- `run_correctness.py`: `ceac902634ce9f45b7c1c262c225afe65817acee4834e98fc5a0cf66a8c11386`
- `test_run_correctness.py`: `728ef732c3ae717975eaed967099b23551e6d4a3a9a530dedb550fe9a234f145`
- `CORRECTNESS_RUNNER.md`: `5fe14283f4d3904191d06898865047d57df20f66b21d6e95fdc62be189866f7f`

The four parser regression groups read six hash-pinned actual stdout/stderr files from this attempt. They accept all three completed native positive outputs, reject a change to each retention coverage count, require exactly two known diagnostic lines, and reject added stdout or arbitrary diagnostics. Root executed these tests successfully: actual exit 0, output chunk `d1968f`, elapsed 0.161 seconds. This execution result was reported by root; the repair author did not run the tests or native work. Independent source/actual-output review is saved in `benchmark/scaling_investigation/candidates/INDEPENDENT_CORRECTNESS_PARSER_REVIEW.md`.

Root launched a fresh `depth-correctness03` attempt after that gate. Attempt02 artifacts are not resumed or overwritten. Completion of attempt03 must be established by its own final receipt.
