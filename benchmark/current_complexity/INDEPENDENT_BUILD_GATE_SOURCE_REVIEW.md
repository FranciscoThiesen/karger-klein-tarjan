# Current-complexity build/schema gate — independent source review

Source-only review completed on 2026-10-15. **PASS for preparation, not execution readiness.** No module was imported, syntax-checked or tested; no library was acquired/built, no compiler or metadata command in the validator was invoked, and no native/schema curve ran. The actual producer and real artifacts remain missing.

| Reviewed source | SHA-256 |
|---|---|
| `validate_build.py` | `335db8375fa92955d6a2ac0a7bdc0627c5986a342d469a5e7f2f3441f802a001` |
| `test_validate_build.py` | `35eb5a60e068f1a428dbfef05e78eb35c7573e864fd74d8242e95174cf04505e` |
| `BUILD_GATE_PLAN.md` | `299f1a19f298dde27867ef9b45fcda5612f27687ffb0e7c3c5d6f02bef4176e2` |
| `ANALYSIS_PREPARATION.md` | `bb7c4a9d4a564e51c3f34148e04ff60e4dedb570d323349f0bc77bfdf0ad6068` |

The validator binds the complete original eighth parent proof and its eight physical production objects, the pinned clean Google Benchmark v1.5.2 checkout, source inventory, compiler/SDK, three exact library configure/build/test commands and two exact new-main commands. Native objects, configured options, compile flags, static interface, archive, upstream test report, logs and owned groups are retained. The actual archive members are compared byte-for-byte by SHA-256 with their recorded compiled objects, not accepted merely by filename. Unexpected platform/compiler/CMake output is a future review gate; this review does not establish actual compatibility or tool availability.

Two literal final-binary diagnostic curves exercise KKT and retained Borůvka on all eleven declared G(n,m) sizes. The schema gate checks 198 calls, 66 certificates, raw/library identity, algorithm input fingerprints, source/build binding and empty groups. These curves remain excluded from the future 24-curve study. No passing receipt can be supplied by a merely illustrative binary or a preparation document.

Three findings were repaired and reread: live resource observations and final empty-group samples are bound to typed command/cleanup intervals; same-name archive members must match compiled object bytes; and the smoke receipt is hashed before reading and rebound immediately afterward. Prepared negatives cover the interval/type failures, incorrect archive bytes and a smoke file changed after reading. A follow-up fixture correction places the archive-byte mock around the positive library-object test, avoiding an accidental real `ar` call on a nonexistent synthetic archive. All five fixture groups remain unexecuted.

The per-command 300-second interval includes cleanup, preserves nonzero/unknown state and rejects subsequent overlapping command evidence. Native exit, final empty group, sampled RSS ceiling and unavailable-monitor limits remain distinct checks. This is validation of evidence after a bounded producer runs; the source does not itself provide acquisition/build orchestration.

Remaining release gates are explicit: implement and independently review `build_library_main.py` and its environment/outer lifecycle policy; acquire and build the actual pinned library; run available upstream tests and the final-binary schema smoke; execute prepared mocks with retained attempts; verify the real JSON/unit/API assumptions; and obtain independent readiness/freeze and a separate quiet performance release. No current-candidate complexity fit is claimed.

`ANALYSIS_PREPARATION.md` was corrected only to acknowledge the newly written, unexecuted validator/mock sources. The earlier analysis-source receipt's document hash remains historical. Analyzer and analyzer-test semantics were not changed by this wording update.

## Later source preparation is outside this receipt

Immediately after this receipt was saved, the owner announced additional generator/environment/version checks and a newly written, unexecuted `build_library_main.py`. Those changes are not covered by the hashes or PASS above. A separate follow-up review is required; the statements about the missing producer describe the reviewed snapshot, not the newly announced source state.
