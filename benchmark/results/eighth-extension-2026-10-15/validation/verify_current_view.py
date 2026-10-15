#!/usr/bin/env python3
"""Local browser integration test for the exact assembled root viewer."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
from playwright.sync_api import sync_playwright


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--viewer', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    viewer = args.viewer.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    initial = sha(viewer)
    report = {'schema': 'current_hierarchy_browser_qa_v1', 'validation': 'running',
              'viewer': str(viewer), 'viewer_sha256': initial,
              'source_sha256': sha(Path(__file__).resolve()),
              'python': sys.version, 'python_executable': sys.executable,
              'playwright': importlib.metadata.version('playwright'),
              'state_checks': [], 'control_checks': [], 'screenshots': {},
              'javascript_errors': [], 'external_requests': [],
              'browser_closed': False}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            report['browser_version'] = browser.version
            try:
                for width, height, mobile in [(1280, 960, False), (390, 844, True)]:
                    context = browser.new_context(viewport={'width': width, 'height': height},
                                                  is_mobile=mobile, has_touch=mobile)
                    page = context.new_page()
                    page.on('pageerror', lambda error: report['javascript_errors'].append(str(error)))
                    def blocked(route):
                        report['external_requests'].append(route.request.url)
                        route.abort()
                    page.route(re.compile(r'^https?://'), blocked)
                    page.goto(viewer.as_uri(), wait_until='load', timeout=30000)
                    assert page.evaluate('window.kktRootView.graphs') == 2
                    data = json.loads(page.locator('#graph-data').text_content())
                    canvas = page.locator('#canvas')
                    for family in range(2):
                        page.locator('#family').select_option(str(family))
                        graph = data['graphs'][family]
                        for policy in range(2):
                            page.locator('#policy').select_option(str(policy))
                            sample = graph['samples'][policy]
                            for stage in range(5):
                                page.locator('#stage').select_option(str(stage))
                                layer = graph['stages'][min(stage, 2)]
                                mst = set(graph['mst_ids'])
                                forest = set(sample['forest_ids']) if stage >= 3 else set()
                                sampled = set(sample['sampled_ids'])
                                essential = sum(e[3] in mst or e[3] in forest for e in layer['edges'])
                                candidates = sum(e[3] not in mst and e[3] not in forest and
                                                 (stage != 3 or e[3] in sampled) for e in layer['edges'])
                                expected = f"{layer['n']:,} vertices · {layer['m']:,} full edges"
                                if stage >= 3:
                                    expected += (f" · {sample['sample_edges']:,} sampled · {sample['forest_components']} sample components"
                                                 f" · {sample['heavy_edges']:,} heavy / {sample['light_edges']:,} light")
                                expected += f" · drawing {essential} essential + {min(512, candidates)} context edges"
                                actual = page.locator('#counts').inner_text()
                                assert actual == expected, (width, family, policy, stage, actual, expected)
                                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (width, family, policy, stage, 'horizontal overflow')
                                assert canvas.evaluate('(c)=>c.width>0 && c.height>0')
                                report['state_checks'].append({'width': width, 'height': height,
                                    'mobile_emulation': mobile, 'family': family, 'policy': policy,
                                    'stage': stage, 'counts': actual, 'essential_edges': essential,
                                    'context_edges': min(512, candidates)})
                                if policy == 1 and stage in (3, 4):
                                    name = f'w{width}-family{family}-stage{stage}.png'
                                    page.screenshot(path=str(args.output / name), full_page=True)
                                    report['screenshots'][name] = sha(args.output / name)
                    page.locator('#family').select_option('0')
                    page.locator('#stage').select_option('4')
                    page.locator('#policy').select_option('1')
                    page.locator('#reset').click()
                    canvas.scroll_into_view_if_needed()
                    canvas.focus()
                    initial_canvas = canvas.evaluate('(c)=>c.toDataURL()')
                    canvas.press('ArrowRight')
                    rotated = canvas.evaluate('(c)=>c.toDataURL()')
                    assert rotated != initial_canvas
                    canvas.press('+')
                    assert canvas.evaluate('(c)=>c.toDataURL()') != rotated
                    canvas.press('r')
                    assert canvas.evaluate('(c)=>c.toDataURL()') == initial_canvas
                    box = canvas.bounding_box()
                    page.mouse.move(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    page.mouse.down()
                    page.mouse.move(box['x'] + box['width']/2 + 50, box['y'] + box['height']/2 + 20)
                    page.mouse.up()
                    dragged = canvas.evaluate('(c)=>c.toDataURL()')
                    assert dragged != initial_canvas
                    page.mouse.wheel(0, 120)
                    page.wait_for_function('(old)=>document.getElementById("canvas").toDataURL()!==old', arg=dragged)
                    page.locator('#context').uncheck()
                    assert page.locator('#counts').inner_text().endswith('+ 0 context edges')
                    no_context = canvas.evaluate('(c)=>c.toDataURL()')
                    page.locator('#context').check()
                    assert canvas.evaluate('(c)=>c.toDataURL()') != no_context
                    page.locator('#reset').click()
                    assert canvas.evaluate('(c)=>c.toDataURL()') == initial_canvas
                    report['control_checks'].append({'width': width, 'keyboard_rotate_zoom_reset': 'pass',
                                                    'mouse_drag_wheel': 'pass', 'context_toggle_reset': 'pass'})
                    context.close()
                assert len(report['state_checks']) == 40
                assert not report['javascript_errors'], report['javascript_errors']
                assert not report['external_requests'], report['external_requests']
                assert sha(viewer) == initial, 'viewer drift'
                report['validation'] = 'pass'
            finally:
                browser.close()
                report['browser_closed'] = True
    except BaseException as error:
        report['validation'] = 'failed'
        report['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        (args.output / 'browser.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('validation', 'browser_version', 'browser_closed')}))


if __name__ == '__main__':
    main()
