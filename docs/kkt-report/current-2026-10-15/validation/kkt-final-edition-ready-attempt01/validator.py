import hashlib,json,re,shutil
from pathlib import Path
source=Path('/tmp/kkt-final-edition-source-prep.md')
layout=Path('/tmp/kkt-final-edition-figure-layout.json')
out=Path('/tmp/kkt-final-edition-ready-attempt01')
out.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
info={'validation':'failed','scope':'Final source/image identity and local-target existence; not tracked-link portability, renderer, PDF or visual acceptance.','source':str(source),'source_sha256':sha(source),'layout':str(layout),'layout_sha256':sha(layout),'native_execution':False,'final_render_execution':False}
try:
 text=source.read_text();decl=json.loads(layout.read_text())
 images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',text)
 assert len(images)==13 and len(set(images))==13,'main image count'
 actual={str(Path(p)):sha(p) for p in images}
 assert set(actual.values())==set(decl['figures']) and len(decl['figures'])==13,'exact image digest coverage'
 assert all(v['minimum_label_pt']>=8.5 and v['nominal_width_inches'] in (7.05,7.1) for v in decl['figures'].values()),'physical declarations'
 refs=dict(re.findall(r'^\[([^\]]+)\]:\s+(.+)$',text,re.M))
 used=set(re.findall(r'(?<!!)\[[^\]]*\]\[([^\]]+)\]',text))
 assert used<=set(refs),'undefined reference link'
 inline=re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',text)
 targets=sorted(set([*images,*inline,*refs.values()]))
 local=[]
 for raw in targets:
  if raw.startswith(('https://','http://','#')):continue
  path=Path(raw.split('#',1)[0])
  assert path.is_absolute() and path.is_file(),f'missing local file {raw}'
  assert str(path).startswith('/Users/random_person/Desktop/kkt-eighth-sampling/'),f'outside evidence root {raw}'
  local.append(str(path))
 assert not re.search(r'work.*(?:still pending|remain pending)|source draft|New-edition source preparation',text,re.I),'stale completed-study wording'
 reviews=[Path(x) for x in [
 '/tmp/kkt-final-edition-independent-source-review.md',
 '/tmp/kkt-extension-report-editorial-review-2026-10-15.md',
 '/tmp/kkt-current-google-report-source-review.md',
 '/tmp/kkt-final-edition-lower-timing-editorial-review.md',
 '/tmp/kkt-final-edition-final-work-source-review.md',
 '/tmp/kkt-final-edition-condensed-independent-review.md']]
 (out/'reviews').mkdir()
 review_entries=[]
 for path in reviews:
  copy=out/'reviews'/path.name
  shutil.copyfile(path,copy)
  assert sha(path)==sha(copy),'review copy mismatch'
  review_entries.append({'source':str(path),'copy':str(copy),'sha256':sha(path)})
 assert sha(source)==info['source_sha256'] and sha(layout)==info['layout_sha256'],'final source drift'
 info.update(validation='pass',main_image_count=13,image_sha256=actual,local_file_targets=local,local_file_target_count=len(local),reviews=review_entries,remaining_gates=['tracked/copied link proof','actual HTML/PDF generation','at most40A4pages','placed font floor and every-page visual QA'],browser_scope='Current viewer remains blocked before load by archived Browser Use file-URL security policy; no bypass authorized.')
except BaseException as e:
 info['error']=str(e)
 (out/'receipt.json').write_text(json.dumps(info,indent=2)+'\n')
 raise
(out/'receipt.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps({k:info[k] for k in ['validation','source_sha256','layout_sha256','main_image_count','local_file_target_count']}))
