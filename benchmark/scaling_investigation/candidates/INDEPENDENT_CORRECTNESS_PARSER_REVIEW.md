# Independent actual-output parser repair review

PASS, source and preserved-output review only. No imports, tests or native runs
were performed by this reviewer. Attempt02 remains a failed gate attempt even
though the retention solver process itself exited successfully.

- `run_correctness.py`: `ceac902634ce9f45b7c1c262c225afe65817acee4834e98fc5a0cf66a8c11386`
- `test_run_correctness.py`: `728ef732c3ae717975eaed967099b23551e6d4a3a9a530dedb550fe9a234f145`
- `CORRECTNESS_RUNNER.md`: `5fe14283f4d3904191d06898865047d57df20f66b21d6e95fdc62be189866f7f`

The narrow production-runner diff accepts exactly two newline-terminated
`crossover_topology_attempts=1` stderr lines from the fixed retention suite.
The included harness emits one such line for each crossover fixture; the test
declares exactly two connected G(n,m) fixtures with fixed sizes/seeds. The
preserved successful process output contains those two lines and the unchanged
28/819/35/35/140/10 coverage summary. All six actual positive-output hashes
match the parser-test literals.

This accepts an expected harness diagnostic, not arbitrary stderr. Four new
parser groups exercise all actual positive outputs, each changed coverage
count, missing/duplicate/altered/prefixed/suffixed topology diagnostics, extra
stdout and unrelated diagnostics in the other suites. Native object/flag,
counter, sanitizer, lifecycle, assertion and wrong-dispatch checks are unchanged.
The prior overly strict empty-stderr expectation was a parser error; it provides
no evidence of a solver defect. Fresh correctness03 execution remains required.
