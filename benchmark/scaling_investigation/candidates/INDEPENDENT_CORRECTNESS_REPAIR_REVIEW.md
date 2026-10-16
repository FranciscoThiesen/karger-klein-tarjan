# Independent timing-harness gate repair review

PASS, source-only narrow repair review. This supersedes the previous runner's
execution-readiness conclusion: attempt01 exposed a compile-time harness
restriction missed in that review. The original source and failed attempt are
preserved in `depth-correctness01/runner-repair-before` and its command records.

- Revised runner: `2a2d4b7c0b6d70cfe3488b2d8940bbe978e04e0aa1c405f356eebb09b0504ac1`
- Revised note: `6c8ada3acd5632f66f16868dcb8d7efe0a46b56ddcbf419e4405ba2da33e6bb7`

`retention_control_test` includes the timing-only harness, whose explicit
`KKT_ENABLE_WORK_STATS` rejection is appropriate. The repair removes that flag
from its main and every production object in its link: native reuses the eight
checked `depth-reference` objects; sanitizer builds eight separately named
`timing-production-*` objects with the same sanitizer flags and counters off.
It never mixes instrumented and uninstrumented inline definitions in a link.
The focused differential and edge-verifier suites remain instrumented, their
counter/identity gates unchanged. Coverage metadata now labels this distinction.
No production source, compiler, SDK, algorithm policy, deadline or correctness
expectation changed. Retry02 must perform a fresh complete execution; this
review itself imported, compiled and executed nothing.
