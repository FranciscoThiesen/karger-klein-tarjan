# Current Google Benchmark harness: actual gate results

The pinned library, current-object harness and real schema smoke passed. The
24-curve complexity study has **not** run. After declaration commit
`6fb39a0ea621cdcb1fe5be151c29cefab3b3aa78`, guarded preflight and a fresh strict
freeze reload both passed with actual zero exits and empty groups. The freeze
SHA-256 is `bc0abc5f8675ce9771b6ce81f5cd933afd5d3ffd36d79bc6b34b98e4a89620c7`;
it fixes 24 curves and eleven sizes. Performance release remains pending.
The earlier source-preparation documents retain
their historical status; the receipts below establish actual runtime status.

The library is Google Benchmark v1.5.2, commit
`73d4d5e8d6d449fc8663765a42aa8aeeee844489`. It was acquired from the official GitHub
repository with normal TLS verification. System DNS failed; the explicit
Git-only public address came from a recorded `dig @1.1.1.1 github.com A` query.
No credentials or system resolver settings changed.

| Gate | Actual result | Evidence |
|---|---|---|
| Initial seven mock suites | 37 groups passed | `validation/mock-*-attempt02.{json,stdout,stderr}` |
| Final affected validator/producer/outer suites | 6 + 3 + 4 groups passed | `validation/archive-index-repair-attempt01/*-tests.{json,stdout,stderr}` |
| Library and final-main build | Passed, actual outer exit 0, 90.01 s | `validation/build-attempt04/receipt.json` |
| Upstream tests | All 59 enabled tests passed; no failures/skips | Build log and bound `library-tests.xml` |
| Actual final-binary schema smoke | Two curves, 198 calls, 66 certificates passed; actual outer exit 0, 204.69 s | `validation/smoke-attempt01/receipt.json` and `inner/schema-smoke.json` |
| Fresh read-only readiness proof | Passed, actual outer exit 0 | `validation/readiness-attempt01.json` and `readiness-check-attempt01.json` |

The build proof checks all 18 native library objects and their exact archive
member bytes, the eight original physical production objects, the new main,
Apple Clang 15/SDK identity, arm64 executable and 512 MiB stack. The two smoke
curves use the actual final binary, both declared solver paths, all eleven
sizes, raw certificates and real Google Benchmark JSON. Their clocks are
diagnostic artifacts explicitly excluded from study analysis. They establish
neither a measured complexity class nor a crossover.

The complete successful build owns six inner process groups, and the smoke
owns two. Both outer receipts prove their own groups and all inner groups
empty. The readiness wrapper and final affected test wrappers also exited
zero with empty groups. No performance capture was launched.

Three failed build attempts remain preserved:

1. Attempt01 acquired the correct source, then found that `/usr/local/bin/cmake`
   was a Python launcher backed by an Intel-only interpreter. Attempt02 onward
   select the already installed universal CMake/CTest 3.30.5 binaries through
   an explicit PATH prefix.
2. Attempt02 configured natively, then upstream Release `-Werror` rejected a
   newer Clang diagnostic for its unused `sigma_gn` accumulator. The reviewed
   library/test-only flag `-Wno-error=unused-but-set-variable` keeps that warning
   visible. All other warning errors, source bytes, production objects and
   main flags remain unchanged. Its real compile database also corrected the
   checker's synthetic assumption about the exact `BUILD/src` working path.
3. Attempt03 built the library/main and passed all 59 tests, but the final
   archive checker omitted Apple's standard leading `__.SYMDEF` symbol table.
   The correction requires that exact entry, the same ordered object list and
   all object-byte hashes. Missing/duplicate metadata or extra objects fail.

Each failed attempt has a separate fresh `independent-exit-audit.json`; every
attempted group was confirmed empty, and none of the failed receipts was
promoted to success. Snapshots, focused negatives, exact diffs and independent
source-review receipts are retained in the two repair directories. Attempt04
repeated the complete build under the corrected proof.

The actual commands and relevant environment are in the exclusive invocation
and receipt files. Build outputs are under ignored `bin/current-complexity/`;
the fresh pinned source checkouts are outside the worktree under
`/Users/random_person/Desktop/kkt-benchmark-dependencies/`. All remain bound by
hashes in the records. Successful build/schema receipts are not permission to
start a performance capture.
