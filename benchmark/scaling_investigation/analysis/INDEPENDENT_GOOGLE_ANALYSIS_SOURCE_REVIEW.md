# Actual Google export analysis: source review

Source review PASS for `analyze_candidate_google.py` and its four prepared test groups. No import, mock execution, capture read or native work was performed for this review. Runtime validation remains the owner's/root's separate gate.

The literal six-curve matrix retains all 594 native records, 198 warmups, 396 matched native clock ratios, 66 input/clock summaries, 396 two-call means and 132 absolute-time summaries. Integer/Fraction arithmetic preserves ratio numerators/denominators and the distinction between medians of matched ratios and ratios of separate medians. Both clocks retain all six calls per size, their full range and all losses. Pairing is by callback/iteration labels across separate process curves, not simultaneous host state.

The source checks frozen Python/helper identities before loading the strict Google runner. That runner supplies completed build, capture, schema and lifecycle proof; the analyzer adds literal identity/fingerprint checks and rechecks its input inventory. Original Google JSON copies are verified byte-identical. Six actual library BigO/RMS records are retained rather than replaced by custom fits. CPU-selected model semantics, the manual coefficient using that same model, CPU-only exported RMS, and undefined cross-policy coefficient ratios when model labels differ are correctly represented.

Prepared tests cover the full independently spelled size matrix, exact means/ratios, absolute ranges and losses, missing/duplicate/type/fingerprint failures, unchanged actual library exports, and different-model coefficient handling. The final statistics fixture repeats reference `[10,100,1000]` versus depth `[5,110,900]`: paired median 0.9 wins while the separate-median ratio 1.1 loses, with four winning and two losing individual pairs. This directly guards the observed direction-of-comparison pitfall.

Reviewed final SHA-256: analyzer `2e2542fd5da46f828eb33d2b67813f3ad311e6487e7b679d7bf68aaadc1e14a5`; tests `b522f69dec909d476917d04cc537364e9f88b6d6e97289dff70d093d30200729`.
