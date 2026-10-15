# Publication portability wording — narrow source rereview

PASS for the narrow correction. Prior sources/addendum are preserved under `before-portability-wording/`. No imports, Git inventory checks, rendering or other execution occurred.

Reviewed renderer SHA-256: `ad0a30727f7c6434ada8d97836b6be038c9a0dfae769fac2a848db3e2cfc9663`. Reviewed README SHA-256: `5c0df179d10ab4e911af30cfcd6dca3302ab0398651ce350f1c737ad4a257b2f`.

The renderer now records repository location separately from portability: `location_inside_repository` and `all_evidence_paths_inside_repository` cannot pass `evidence_bundle_portability_verified`, which remains false. Tracking or deliberate copying is an explicit pending publication check. Relative link rewriting still works as before; it does not make original-machine native proof paths/objects a portable rebuild bundle. The README requires final tracked/copied evidence and testing outside the original checkout. This source correction does not claim those gates have run.
