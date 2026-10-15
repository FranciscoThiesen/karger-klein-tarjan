#!/usr/bin/env python3
"""Build the local reading preview and a narrowly scoped Jekyll publication kit.

No network, browser, native solver, or publishing operation. Ruby/Kramdown is
used to validate the same Markdown dialect as the target Jekyll site.
"""
import hashlib
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SLUG = 'kkt-back-on-earth'
POST_NAME = '2026-10-15-Maybe-KKT-Is-Not-Galactic-After-All.md'
TITLE = 'Maybe KKT is not galactic after all'

FIGURE_CSS = '''
.kkt-figure { margin: 2.2em 0; }
.kkt-figure picture { display: block; }
.kkt-figure img { display: block; width: 100%; height: auto; margin: 0; border: 0; border-radius: 6px; }
.kkt-figure figcaption { margin: .85em .15em 0; font-size: .88em; line-height: 1.65; color: inherit; opacity: .86; }
.kkt-table-scroll { overflow-x: auto; margin: 1.5em 0; }
.kkt-table-scroll:focus { outline: 2px solid currentColor; outline-offset: 4px; }
@media (max-width: 600px) { .kkt-figure { margin-inline: -12px; } }
'''
PREVIEW_CSS = '''
:root { color-scheme: dark light; --bg:#0a0a0a; --surface:#111; --ink:#e5e5e5; --muted:#a3a3a3; --line:#303030; --accent:#fb923c; }
@media (prefers-color-scheme:light) { :root { --bg:#f4eedf; --surface:#ebe3cf; --ink:#262015; --muted:#4b3f2a; --line:#c9bda0; --accent:#a84418; } }
* { box-sizing:border-box; }
html { background:var(--bg); }
body { margin:0; color:var(--ink); font:15px/1.75 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; overflow-wrap:break-word; }
.container { max-width:760px; padding:0 20px; margin:auto; }
header { display:flex; justify-content:space-between; align-items:center; gap:20px; padding:32px 0 22px; border-bottom:1px solid var(--line); font-size:13px; color:var(--muted); }
header a { color:var(--ink); font-weight:700; }
main { padding:36px 0 60px; }
h1 { font-size:28px; line-height:1.3; letter-spacing:-.035em; margin:0 0 12px; }
h1::before { content:'# '; color:var(--accent); }
.dek { color:var(--muted); margin:0 0 36px; font-size:13px; }
h2 { font-size:20px; line-height:1.4; margin:2.8em 0 1em; letter-spacing:-.02em; }
h3 { font-size:16px; line-height:1.45; margin:2em 0 1em; }
p { margin:0 0 1.3em; }
a { color:var(--accent); text-decoration-thickness:1px; text-underline-offset:3px; }
a:hover { text-decoration-thickness:2px; }
strong { font-weight:750; }
code { font-family:inherit; font-size:.9em; }
pre { padding:18px; background:var(--surface); border:1px solid var(--line); border-radius:5px; overflow-x:auto; line-height:1.65; }
pre code { font-size:13px; }
table { width:100%; border-collapse:collapse; font-size:13px; line-height:1.65; }
th,td { padding:12px; text-align:left; vertical-align:top; border:1px solid var(--line); }
th { color:var(--accent); background:var(--surface); }
th:first-child,td:first-child { width:35%; }
hr { border:0; border-top:1px solid var(--line); margin:3em 0; }
footer { border-top:1px solid var(--line); color:var(--muted); padding:20px 0 40px; font-size:12px; }
@media (max-width:600px) { body { font-size:14px; } h1 { font-size:25px; } h2 { font-size:19px; } header { padding-top:22px; } main { padding-top:28px; } th,td { padding:9px; } }
@media print { :root { --bg:white; --ink:#172c38; --surface:#fbfaf7; --muted:#465961; --line:#ccc; --accent:#007f82; } header,footer { display:none; } .container { max-width:none; } .kkt-figure,pre { break-inside:avoid; } h2,h3 { break-after:avoid; } }
'''

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def render(text):
    proc = subprocess.run(['ruby', '-e',
        'require "kramdown"; require "kramdown-parser-gfm"; '
        'puts Kramdown::Document.new(STDIN.read,input:"GFM",hard_wrap:false,syntax_highlighter:nil).to_html'],
        input=text, text=True, capture_output=True, check=True)
    if proc.stderr.strip():
        raise ValueError('Kramdown warning: '+proc.stderr)
    return re.sub(r'<table>(.*?)</table>',
        r'<div class="kkt-table-scroll" tabindex="0" role="region" aria-label="Comparison table"><table>\1</table></div>',
        proc.stdout, flags=re.S)

class AuditHTML(HTMLParser):
    def __init__(self):
        super().__init__(); self.refs=[]; self.images=[]; self.sources=[]; self.ids=[]; self.tags={}
    def handle_starttag(self,tag,attrs):
        a=dict(attrs); self.tags[tag]=self.tags.get(tag,0)+1
        if 'id' in a: self.ids.append(a['id'])
        for k in ('src','href','srcset'):
            if k in a:self.refs.append(a[k])
        if tag=='img':self.images.append(a)
        if tag=='source':self.sources.append(a)

def source_body(text):
    assert text.startswith('---\n')
    return text.split('---\n',2)[2]

def dimensions(path):
    root=ET.parse(path).getroot()
    values=root.attrib['viewBox'].split()
    w,h=map(float,values[2:]); return str(round(w)),str(round(h))

def enrich_picture_tags(body):
    def enriched(match):
        tag=match.group(0); attr='srcset' if tag.startswith('<source ') else 'src'
        path=re.search(attr+r'="([^"]+)"',tag).group(1)
        w,h=dimensions(ROOT/path)
        return tag[:-1]+f' width="{w}" height="{h}">'
    return re.sub(r'<(?:source|img) [^>]+>',enriched,body)

def zip_tree(source,target):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(source.rglob('*')):
            if path.is_file():z.write(path,str(path.relative_to(source)))

def main():
    source=(ROOT/'POST.md').read_text(); body=enrich_picture_tags(source_body(source))
    assert source.count('<figure ')==8 and TITLE in source
    rendered=render(body)
    preview=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark light"><meta name="description" content="Two broken work bounds, a better implementation, and a measured crossover for randomized minimum spanning trees.">
<title>{TITLE}</title><style>{PREVIEW_CSS}\n{FIGURE_CSS}</style></head>
<body><div class="container"><header><a href="https://chico.dev/">chico.dev</a><span>Article preview · October 15, 2026</span></header>
<main><article><h1>{TITLE}</h1><p class="dek">Algorithms · Graphs · Performance &nbsp; / &nbsp; about 16 minutes, plus figures</p>
{rendered}</article></main><footer>Local article preview. Color scheme follows your system setting. All figures and downloads are local.</footer></div></body></html>'''
    (ROOT/'preview.html').write_text(preview)
    audit=AuditHTML();audit.feed(preview)
    assert audit.tags.get('figure')==8 and audit.tags.get('figcaption')==8
    assert audit.tags.get('table')==2 and audit.tags.get('h1')==1
    assert len(audit.images)==len(audit.sources)==8
    assert len(audit.ids)==len(set(audit.ids))
    assert all(a.get('alt','').strip() and a.get('width') and a.get('height') for a in audit.images)
    local=[]
    for ref in audit.refs:
        if re.match(r'https?://',ref):continue
        if ref.startswith('#'):
            assert ref[1:] in audit.ids;continue
        path=ROOT/ref.split('#')[0];assert path.is_file(),ref;local.append(ref)
    assert not audit.tags.get('script') and not re.search(r'<(?:script|iframe)\b',preview)

    kit=ROOT/'publish';post_dir=kit/'_posts';assets=kit/'assets/images'/SLUG
    downloads=kit/'assets/downloads'/SLUG
    for folder in (post_dir,assets,downloads):folder.mkdir(parents=True,exist_ok=True)
    mapping={}
    for a in audit.images+audit.sources:
        rel=a.get('src',a.get('srcset'));original=ROOT/rel
        for ext in ('.svg','.png'):
            src=original.with_suffix(ext);shutil.copy2(src,assets/src.name)
        mapping[rel]='{{ site.baseurl }}/assets/images/'+SLUG+'/'+original.name
    (assets/'post.css').write_text(FIGURE_CSS)
    for item in sorted((ROOT/'downloads').iterdir()):
        if item.is_file():shutil.copy2(item,downloads/item.name)
    public=source.replace(source_body(source),body)
    for before,after in mapping.items():public=public.replace(before,after)
    public=public.replace('downloads/','{{ site.baseurl }}/assets/downloads/'+SLUG+'/')
    boundary=public.index('---\n',4)+4
    public=public[:boundary]+f'\n<link rel="stylesheet" href="{{{{ site.baseurl }}}}/assets/images/{SLUG}/post.css">\n'+public[boundary:]
    (post_dir/POST_NAME).write_text(public)

    # Resolve the only Liquid variable used, then render with the target dialect.
    pub_html=render(source_body(public).replace('{{ site.baseurl }}',''))
    pub_audit=AuditHTML();pub_audit.feed(pub_html)
    pub_refs=[]
    for ref in pub_audit.refs:
        if ref.startswith('https://') or ref.startswith('#'):continue
        assert ref.startswith('/assets/'),ref
        assert (kit/ref.lstrip('/')).is_file(),ref;pub_refs.append(ref)
    assert len(pub_audit.images)==8 and len(pub_audit.sources)==8
    assert pub_audit.tags.get('figure')==8 and pub_audit.tags.get('table')==2
    assert '/Users/' not in public and 'attempt04' not in public
    assert '{{' not in pub_html and '{%' not in pub_html
    (kit/'HANDOFF.md').write_text('''# chico.dev publication kit

Copy `_posts/` and `assets/` into the site's Jekyll repository. No layout, theme, plugin, JavaScript, network font, or configuration change is required. The post preserves the requested title and uses scoped figure CSS. It includes desktop/mobile SVGs, PNG alternatives, chart data, and explanatory-figure source downloads.

This kit has not been published. Review the generated post date and prose before adding it. The data download reproduces exported chart tables; complete native benchmark reproduction requires the research branch and its evidence. Ensure that research code is publicly available before describing a public checkout as reproducing the experiment.

The Markdown was rendered with Kramdown 2.5.2 and the GFM parser, matching the site's declared dialect. All packaged local targets were checked. Every desktop/mobile figure was visually reviewed. The complete page has not received browser visual QA: local-file browser navigation was rejected earlier by automatic approval review, and no alternate route was used. A theme-aware offline `preview.html` is supplied in the authoring folder for local review.
''')
    # Fail on stale generated assets before publishing any kit archive.
    expected_images={Path(v).name for v in mapping.values()}
    expected_names=expected_images|{Path(x).with_suffix('.png').name for x in expected_images}|{'post.css'}
    assert {p.name for p in assets.iterdir()}==expected_names
    manifest={str(p.relative_to(kit)):digest(p) for p in sorted(kit.rglob('*')) if p.is_file() and p.name!='MANIFEST.json'}
    (kit/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    zip_tree(kit,ROOT/'chico-dev-kkt-post.zip')
    with zipfile.ZipFile(ROOT/'chico-dev-kkt-post.zip') as z:
        assert z.testzip() is None
        for name,sha in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==sha
    result={'validation':'pass','markdown_engine':'Kramdown 2.5.2 / GFM',
        'source_sha256':digest(ROOT/'POST.md'),'preview_sha256':digest(ROOT/'preview.html'),
        'publication_zip_sha256':digest(ROOT/'chico-dev-kkt-post.zip'),
        'figures':8,'responsive_sources':8,'alt_texts':8,'tables':2,
        'preview_local_references':len(local),'publication_local_references':len(pub_refs),
        'publication_manifest_files':len(manifest),
        'browser_visual_qa':'not performed; prior local-target approval rejection; no alternate route used',
        'native_benchmarks_run':False,'published':False}
    (ROOT/'validation/build.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
