#!/usr/bin/env python3
"""Check the offline editions, every explorer stage, and responsive layout."""
import argparse
import hashlib
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screenshots', type=Path, required=True)
    args = parser.parse_args()
    args.screenshots.mkdir(parents=True, exist_ok=True)
    raw = json.loads((HERE / 'graph_data.json').read_text())
    assert len(raw) == 7
    records = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for filename in ('report.html', 'graph-explorer.html'):
            page = browser.new_page(viewport={'width': 1280, 'height': 960})
            errors, network = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            def block(route):
                network.append(route.request.url)
                route.abort()
            page.route(re.compile(r'^https?://'), block)
            page.goto((HERE / filename).as_uri(), wait_until='load')
            assert page.evaluate('window.kktExplorer.graphCount') == 7
            assert page.evaluate('[...document.images].every(i=>i.complete && i.naturalWidth>0)')
            for graph in raw:
                page.locator('#family').select_option(graph['family'])
                for mode, layer in enumerate((0, 1, 2, 2, 2)):
                    page.locator('#stage').select_option(str(mode))
                    state = page.evaluate('window.kktExplorer.getState()')
                    assert state == {'family': graph['family'], 'stage': mode,
                                     'vertices': graph['stages'][layer]['n']}
                    label = page.locator('#graph-info').inner_text()
                    assert str(graph['stages'][layer]['n']) in label
                    if mode == 3:
                        assert str(len(graph['sampled_ids'])) in label and 'sample' in label.lower()
                    records.append({'edition': filename, **state, 'label': label})
            canvas = page.locator('#graph-canvas')
            canvas.scroll_into_view_if_needed()
            before = canvas.evaluate('(c)=>c.toDataURL()')
            canvas.focus()
            canvas.press('ArrowRight')
            after = canvas.evaluate('(c)=>c.toDataURL()')
            assert before != after, 'Keyboard rotation did not change rendered canvas'
            canvas.press('+')
            assert canvas.evaluate('(c)=>c.toDataURL()') != after
            before = canvas.evaluate('(c)=>c.toDataURL()')
            box = canvas.bounding_box()
            page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            page.mouse.down()
            page.mouse.move(box['x'] + box['width'] / 2 + 55, box['y'] + box['height'] / 2 + 20)
            page.mouse.up()
            assert canvas.evaluate('(c)=>c.toDataURL()') != before
            before = canvas.evaluate('(c)=>c.toDataURL()')
            page.mouse.wheel(0, 120)
            page.wait_for_function('(old)=>document.getElementById("graph-canvas").toDataURL()!==old', arg=before)
            page.locator('#context-edges').uncheck()
            page.locator('#context-edges').check()
            page.locator('#reset-camera').click()
            page.locator('#family').select_option('grid3d_distance')
            page.locator('#stage').select_option('4')
            page.locator('#explorer').screenshot(path=str(args.screenshots / (filename + '-explorer.png')))
            assert not errors, errors
            assert not network, network
            page.set_viewport_size({'width': 390, 'height': 844})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
            page.screenshot(path=str(args.screenshots / (filename + '-mobile.png')))
            page.close()
        browser.close()
    report = (HERE / 'REPORT.md').read_text()
    assert '{{' not in report
    missing = []
    for target in re.findall(r'\]\(([^)]+)\)', report):
        if not re.match(r'https?://|#', target) and not (HERE / target.split('#')[0]).exists():
            missing.append(target)
    assert not missing, missing
    result = {'result': 'pass', 'explorer_stage_checks': len(records),
              'offline_network_requests': 0, 'javascript_errors': 0,
              'desktop_and_mobile_widths': [1280, 390],
              'keyboard_rotation_and_zoom': 'pass', 'pointer_drag_and_wheel_zoom': 'pass',
              'markdown_local_links': 'pass',
              'edition_sha256': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                 for name in ('REPORT.md', 'report.html', 'graph-explorer.html')},
              'stage_checks': records}
    (HERE / 'browser_validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Passed 70 explorer-stage checks, offline rendering, controls, images, local links and mobile width.')


if __name__ == '__main__':
    main()
