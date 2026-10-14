#!/usr/bin/env python3
"""Isolated offline Chromium interaction QA; run only outside timing captures."""
import argparse, hashlib, json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--view-dir',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
parser.add_argument('--executable-path')
parser.add_argument('--families',nargs='+',default=['leaf_hierarchy4','leaf_distance4','leaf_shuffled4','leaf_random4'])
args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'schema':'attachment_rounds_browser_v1','validation':'pending','records':[],'native_performance_measurement':False}
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=args.executable_path)
  report['browser_version']=browser.version
  context=browser.new_context(viewport={'width':1440,'height':1100},device_scale_factor=1,accept_downloads=True)
  for family in args.families:
   page=context.new_page(); errors=[]; external=[]
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.on('request',lambda request:external.append(request.url) if not request.url.startswith(('file:','data:','blob:')) else None)
   source=args.view_dir/(family+'.html');page.goto(source.resolve().as_uri());page.wait_for_function('typeof state !== "undefined" && state.round===0')
   record={'family':family,'html_sha256':sha(source),'screenshots':[],'every_round_checked':0}
   def shot(suffix):
    target=args.output_dir/(family+'-'+suffix+'.png');page.screenshot(path=str(target),full_page=True)
    record['screenshots'].append({'path':target.name,'sha256':sha(target)})
   # Exercise every actual state using the visible next control, not direct state mutation.
   count=int(page.locator('#round').get_attribute('max'))
   for stage in range(count+1):
    assert page.locator('#round').input_value()==str(stage)
    status=page.evaluate('({round:state.round,active:state.active_vertices,edges:state.edges.length,components:state.component_count})')
    assert status['round']==stage
    expected=f"{status['active']:,} active vertices · {status['edges']:,} quotient edges · {status['components']:,} logical component"
    assert page.locator('#round-counts').inner_text().startswith(expected)
    record['every_round_checked']+=1
    if stage==0:shot('initial')
    if stage==2:shot('after-two')
    if stage<count:page.locator('#round-forward').click()
   assert page.locator('#round-forward').is_disabled()
   assert 'Finished tree' in page.locator('#round-stage').inner_text()
   assert status['active']==0 and status['components']==1 and status['edges']==0
   shot('terminal')
   page.locator('#round-back').click();assert page.locator('#round').input_value()==str(count-1)
   page.locator('#round').focus();page.keyboard.press('Home');page.keyboard.press('ArrowRight');page.keyboard.press('ArrowRight')
   assert page.locator('#round').input_value()=='2'
   page.locator('#layout-mode').select_option('ring')
   page.locator('#show-other').check();page.locator('#show-next').uncheck()
   page.locator('#show-local').uncheck();page.locator('#show-core').uncheck()
   page.wait_for_function('document.getElementById("visible-count").textContent.startsWith("0 visible")')
   page.locator('#show-core').check();page.locator('#show-local').check();page.locator('#show-next').check()
   page.locator('#rank').focus();page.keyboard.press('Home')
   page.wait_for_function('document.getElementById("visible-count").textContent.startsWith("0 visible")')
   page.keyboard.press('End')
   page.locator('#front').click();page.wait_for_timeout(50)
   point=page.evaluate('({x:currentProjected[0],y:currentProjected[1]})')
   page.locator('#graph').click(position=point)
   assert 'Current component:' in page.locator('#inspector').inner_text()
   page.locator('#clear-selection').click()
   assert 'Click a current component' in page.locator('#inspector').inner_text()
   page.locator('#auto').check();page.wait_for_timeout(60);page.locator('#auto').uncheck()
   page.locator('#graph').focus();page.keyboard.press('ArrowRight');page.keyboard.press('+')
   page.set_viewport_size({'width':390,'height':844});shot('narrow-after-two')
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
   page.locator('#reset').click()
   assert page.locator('#round').input_value()=='0' and page.locator('#show-next').is_checked()
   assert page.locator('#layout-mode').input_value()=='dyadic'
   with page.expect_download() as download_info:page.locator('#download').click()
   downloaded=args.output_dir/(family+'-download.png');download_info.value.save_as(downloaded)
   assert downloaded.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
   record.update(download_sha256=sha(downloaded),javascript_errors=errors,external_requests=external)
   assert not errors and not external
   report['records'].append(record);page.close()
  context.close();browser.close()
 report['validation']='pass'
except Exception as error:
 report['validation']='fail'
 report['error']=str(error)
 raise
finally:
 (args.output_dir/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
