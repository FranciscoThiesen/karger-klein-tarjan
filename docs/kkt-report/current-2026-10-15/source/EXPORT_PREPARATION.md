# Publication export: source preparation, not executed

This helper copies the accepted main-report/evidence inventory outside the source
worktree, preserving every repository-relative path and every file's bytes.
It never traverses absolute build/object paths embedded in JSON, CSV or source.
Those remain original-machine evidence, not a portable native rebuild promise.

Inputs are the final passing `kkt_publication_links_v1` receipt, its original
repository, the reviewed `pack_publication.py` parser, and explicit final PDF/QA
artifacts. Do not run against a provisional link manifest. The destination and
receipt must not exist. Run through the existing bounded nonnative validation
guard after root releases export; no solver, browser or server is launched.

Example (replace FINAL paths with the completed accepted attempt):

```sh
/usr/bin/python3 -B export_publication.py --released \
  --repo-root /Users/random_person/Desktop/kkt-eighth-sampling \
  --links-receipt /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/validation/FINAL-publication-links.json \
  --link-helper /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/source/pack_publication.py \
  --document /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/FINAL/REPORT.md \
  --document /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/FINAL/REPORT.html \
  --include /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/FINAL/REPORT.pdf \
  --include /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/validation/FINAL-page-QA.json \
  --destination /Users/random_person/Desktop/kkt-publication-export-attempt01 \
  --receipt /Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/current-2026-10-15/validation/export-attempt01.json
```

The accepted receipt's bound and explicitly included files define the bounded
inventory. `--include` adds final artifacts expressly authorized for this export.
Pass the final main Markdown and HTML with `--document`; add the current viewer
as a primary document too if its static resources should be mandatory. The
existing narrow Markdown syntax is reused, not replaced with a general parser.
Every main-document local resource must resolve within the export with matching
bytes. Absolute local URLs (including repository-root-relative links), symlinks,
unsupported resource forms and unresolved main links fail closed. Remote
citations are retained; remote main resource dependencies fail. Native/build
trees, compiled artifacts and private power-log directories are excluded; a
main link to an excluded target fails. Ordinary textual scripts remain evidence.

Supplementary Markdown/HTML/CSS are scanned within the copied inventory, but
their links do not pull in further archives or native dependencies. Absolute,
missing or unbundled historical targets are listed as scoped limitations. This
keeps old bytes and raw machine paths intact without claiming every historical
hyperlink is portable. Partial exports and failed receipts are preserved; use
a new attempt path after fixing a declaration. The final receipt is also saved
as the export's `EXPORT_MANIFEST.json`; it hashes original copied files, not itself.

The output proves declared file inclusion, main-link closure and byte preservation.
It does not check page layout, anchor semantics, dynamic JavaScript URLs or
interactive viewer behavior; the pending browser restriction remains disclosed.
No actual copies, imports, test execution or source hashing occurred during
this preparation. Source review and later final-manifest execution are separate.
