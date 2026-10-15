# Source-only prospective seed check

Before inserting the new seeds into this package, the following read-only
searches were run from `/Users/random_person/Desktop/kkt-compressed-queries`:

```sh
rg -n -P --glob '*.py' --glob '*.cpp' --glob '*.hpp' --glob '*.md' '(?<![0-9A-Za-z_])(11000009|11000027|2203)(?![0-9A-Za-z_])' benchmark kkt common verifier test
rg --files benchmark/results -g freeze.json | xargs rg -n -P '(?<![0-9A-Za-z_])(11000009|11000027|2203)(?![0-9A-Za-z_])'
```

Both returned no matches. An earlier digits-only-boundary search produced one
false positive: `2203` inside a hexadecimal file digest in the completed
compressed-work freeze. Tightening token boundaries removed it; it was not a
seed declaration or captured input.

This checks the prior source/protocol text in the listed trees and all existing
frozen declarations in this worktree. It does not claim to audit arbitrary
external files, other worktrees or undocumented interactive invocations. No
active held-out raw rows, logs or partial timing summaries were inspected.
Recheck declaration inventories before freeze, excluding this package's own
prospective occurrences. The declared graph seeds are 11000009/11000027 and the
scalar sampler seed is 2203; they must not be selected based on outcomes.
