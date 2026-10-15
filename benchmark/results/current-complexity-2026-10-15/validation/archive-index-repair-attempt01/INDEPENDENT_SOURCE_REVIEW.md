# Independent archive-index repair review

`multigraph_design`, 2026-10-15: **source review PASS**. Compared the two installed files with `before/` and read the owner's preserved actual-format audit. No import, test, build, native execution or new archive command was performed by this reviewer.

The sole validator behavior change requires the observed Apple archive index `__.SYMDEF` exactly once at the start, followed by the same complete ordered object-member inventory. Every object is still extracted with `ar -p` and its bytes compared with the bound compiled-object hash; native object/profile, source/flags, upstream test and final-binary smoke gates are unchanged. The prepared negatives reject missing/duplicate index entries and extra object members; the existing mismatched-member-byte negative remains. No arbitrary archive member or weakened byte check is introduced.

The source change agrees with the archived format audit's reported 18 library objects, 59 upstream tests and native final main. That audit explicitly preserves attempt03 as failed; this review does not relabel it a successful build or supply missing real-smoke evidence. A fresh complete attempt remains required.

| Reviewed file | SHA-256 |
| --- | --- |
| `benchmark/current_complexity/validate_build.py` | `cb08e4c7e798cf48b27330009e68f1c93ff4aa78b55419de67cc646d5a687a6a` |
| `benchmark/current_complexity/test_validate_build.py` | `37d26e018aba191d66eb4948b3158eed455d3257e57478c63a02b755d7528cd6` |
| `actual-format-audit.json` | `69648213396206d3b2428eee91076c81eeb7d8e61674c5c7a1fc40016753c313` |
