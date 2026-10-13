# Validation status

The exporter compiled and exited successfully. It produced seven complete
fixtures, independently certified MSTs, a KKT seed-0 equality check per fixture,
and independently reconstructed production contraction stages. The JSON builder
accepted every fixture and embedded it in `index.html`.

`validate_view.js` executed the actual viewer JavaScript against a minimal DOM.
All 492 graph/stage/color/filter combinations passed, checking 984 panel states
for exact node/edge counts, next-round selection highlights and labels explaining
visible versus total remaining edges. See `javascript_validation.json`.
This is semantic execution validation, not a browser layout, screenshot or
download test. The SVG export button has not been exercised in a real browser.

## Headless Chrome attempt

The following command exited with status **134**. Standard output and standard
error were redirected to the archived `browser.log`; that file is empty. No
screenshot was produced. This is an unexplained process failure, not evidence
that the viewer failed to render.

```sh
'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' \
  --headless --disable-gpu --no-first-run --no-default-browser-check \
  --hide-scrollbars --user-data-dir=/tmp/kkt-continuation-view-profile \
  --window-size=1440,1800 \
  --screenshot=/Users/random_person/Desktop/karger-klein-tarjan/benchmark/results/continuation-2026-10-12/visualization/desktop.png \
  file:///Users/random_person/Desktop/karger-klein-tarjan/benchmark/results/continuation-2026-10-12/visualization/index.html
```

## CUA browser policy denial

The subsequent `mcp__cua_repl.js` action was:

```javascript
var kktViewTab = await cua.createBrowserTab('chrome', 'file:///Users/random_person/Desktop/karger-klein-tarjan/benchmark/results/continuation-2026-10-12/visualization/index.html', {sessionName:'🔎 KKT view'});
```

The exact rejection text was:

> Browser Use rejected this action due to browser security policy. Reason: The browser URL policy blocks this action. Browser use cannot visit the requested page. The requested URL protocol is not allowed. Allowed protocols: "http:", "https:". The agent must not attempt to achieve the same outcome via workaround, indirect execution, raw CDP or browser commands, alternate browser surfaces, or policy circumvention. Proceed only with a materially safer alternative that does not require this blocked browser action; if none exists, stop and request user input.

This was an explicit browser URL-policy denial, **not an automatic approval
review rejection**. No alternative browser surface, local-server workaround or
browser command was attempted afterward. The already completed independent
HTML/JavaScript validation is retained as the allowed alternative. Actual
browser appearance remains unverified and must not be represented as visually
reviewed.
