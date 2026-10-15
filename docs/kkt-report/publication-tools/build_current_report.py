#!/usr/bin/env python3
"""Render a new, exclusive Markdown/HTML edition and optional capped PDF.

Source-prepared only. Do not import/run during a measurement campaign. The root
already ran the PDF skill's one-time artifact-start marker for this task; do not
repeat it. Historical report files are never targets.
"""
import argparse
import base64
import datetime
import hashlib
import html
from html.parser import HTMLParser
import importlib.metadata
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote, unquote, urlsplit

# Reviewed literal translations, not a general TeX parser. The new Markdown
# itself receives these readable offline equations. Unknown TeX fails closed.
EQUATIONS = {
    r'A\geq\frac{c}{1-p},\qquad B\geq2c+\frac{A}{2p}.':
        'A ≥ c / (1 − p),     B ≥ 2c + A / (2p).',
    r'U\leq\min\left(Q,\sum_v\operatorname{depth}(v)\right)\leq\min(Q,Bh).':
        'U ≤ min(Q, Σᵥ depth(v)) ≤ min(Q, B·h).',
    r'I_b=(c/b)\binom b2-(c-c/b).':
        'I_b = (c / b) · choose(b, 2) − (c − c / b).',
}
STYLE = '''
:root{color-scheme:light;--ink:#193044;--muted:#526575;--teal:#007e88}
*{box-sizing:border-box}body{margin:0;background:#edf1f3;color:var(--ink);font:16px/1.6 system-ui,-apple-system,sans-serif}
nav{padding:13px 24px;background:#193044;color:white;font-size:14px}nav a{color:white;margin-right:20px}
main{max-width:1060px;margin:28px auto;padding:42px 58px;background:white}
h1{font:600 39px/1.18 Georgia,serif;margin:0 0 25px}h2{font:600 27px/1.25 Georgia,serif;margin:42px 0 18px}h3{font-size:19px;line-height:1.3;margin-top:27px}
p{margin:12px 0}a{color:var(--teal);overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f4f6;padding:14px}code{font:88% ui-monospace,monospace;overflow-wrap:anywhere}
table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.4;margin:18px 0}th,td{text-align:left;padding:7px 8px;border-bottom:1px solid #dae3e7;vertical-align:top}th{background:#e8f1f2}tr:nth-child(even) td{background:#f8fafb}
figure{margin:24px 0}figure img{display:block;max-width:100%;height:auto;margin:auto}figcaption{font-size:13px;line-height:1.4;color:var(--muted);margin-top:8px}
blockquote{margin:18px 0;padding:10px 18px;border-left:3px solid var(--teal);background:#f5f9fa;font:18px/1.5 Georgia,serif}blockquote p{margin:0}
.toc{font-size:14px;border-bottom:1px solid #dae3e7;padding-bottom:18px}.toc ul{padding-left:22px}.viewer-note{padding:12px 16px;background:#f5f9fa;font-size:14px}
@media(max-width:700px){main{margin:10px;padding:24px 18px}h1{font-size:31px}h2{font-size:24px}table{font-size:11px}th,td{padding:5px}nav{padding:12px 18px}}
@page{size:A4;margin:15mm 14mm 17mm}
@media print{body{background:white;font:10.5pt/1.43 Arial,sans-serif}nav,.toc{display:none}main{max-width:none;margin:0;padding:0}h1{font-size:25pt;line-height:1.18}h2{font-size:17pt;margin:19pt 0 9pt}h3{font-size:12pt;margin:13pt 0 7pt}h1,h2,h3{break-after:avoid}p{margin:7pt 0;orphans:3;widows:3}table{font-size:8.5pt;line-height:1.27;margin:9pt 0}thead{display:table-header-group}tr{break-inside:avoid}th,td{padding:4pt}figure{break-inside:avoid;margin:12pt 0}figure img{max-height:none;object-fit:contain}figcaption{font-size:8.3pt}blockquote{font:11pt/1.5 Georgia,serif;padding:6pt 10pt;margin:9pt 0}pre,code{font-size:8.7pt}.viewer-note{font-size:9pt}a{color:#145e68;text-decoration:none}}
'''


def require(value,message):
    if not value:raise ValueError(message)


def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def sha(path):return sha_bytes(path.read_bytes())
def inside(path,root):
    try:path.relative_to(root);return True
    except ValueError:return False
def write(path,text):
    with path.open('x',encoding='utf-8') as stream:stream.write(text)


def equations(source):
    result=[]
    expected={re.sub(r'\s+','',key):value for key,value in EQUATIONS.items()}
    def replace(match):
        key=re.sub(r'\s+','',match.group(1))
        require(key in expected,'Unsupported display equation; add a reviewed literal translation')
        value=expected[key];result.append({'source_tex':match.group(1).strip(),'offline_text':value})
        return '\n> '+value+'\n'
    source=re.sub(r'\\\[(.*?)\\\]',replace,source,flags=re.S)
    require(not re.search(r'\\(?:\[|\]|\(|\)|[A-Za-z]+)|\$\$',source),
            'Untranslated TeX remains; no network math renderer is used')
    return source,result


class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if 'id' in values:
            require(values['id'] not in self.ids,'Duplicate generated anchor')
            self.ids.add(values['id'])
        if tag=='a' and 'href' in values:self.links.append(values['href'])


class PrintHyphens(HTMLParser):
    """Normalize visible HTML text, preserving URLs, asset bytes and U+2212."""
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.parts=[];self.replacements=0;self.raw_tag=None
    def normalized(self,value):
        self.replacements+=sum('\u2010'<=char<='\u2015' for char in value)
        return value.translate({code:ord('-') for code in range(0x2010,0x2016)})
    def handle_starttag(self,tag,attrs):
        self.parts.append(self.get_starttag_text())
        if tag in ('style','script'):self.raw_tag=tag
    def handle_startendtag(self,tag,attrs):self.parts.append(self.get_starttag_text())
    def handle_endtag(self,tag):
        self.parts.append('</'+tag+'>')
        if tag==self.raw_tag:self.raw_tag=None
    def handle_data(self,data):
        self.parts.append(data if self.raw_tag else self.normalized(data))
    def entity(self,text):
        decoded=html.unescape(text)
        self.parts.append(self.normalized(decoded) if not self.raw_tag and
                          any('\u2010'<=char<='\u2015' for char in decoded) else text)
    def handle_entityref(self,name):self.entity('&'+name+';')
    def handle_charref(self,name):self.entity('&#'+name+';')
    def handle_comment(self,data):self.parts.append('<!--'+data+'-->')
    def handle_decl(self,decl):self.parts.append('<!'+decl+'>')
    def handle_pi(self,data):self.parts.append('<?'+data+'>')


def render(args,metadata):
    import markdown
    source=args.source.resolve(strict=True);root=args.repo_root.resolve(strict=True)
    base=args.asset_base.resolve(strict=True);out=args.output_dir.resolve()
    require(inside(out,root),'New edition must be inside the declared repository for relative local links')
    source_bytes=source.read_bytes();body=source_bytes.decode('utf-8')
    inputs={str(source):sha_bytes(source_bytes),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
    require(not re.search(r'\{\{[A-Z_]+\}\}',body),'Unresolved report placeholder')
    require('<!-- PAGE -->' not in body,'Use flowing headings, not inherited historical page markers')
    body,translations=equations(body)
    figures=[];external=[];local_links=[];viewers=[]
    (out/'assets').mkdir()

    def target(raw,is_image=False):
        raw=raw.strip()
        if raw.startswith('<') and raw.endswith('>'):raw=raw[1:-1]
        parsed=urlsplit(raw)
        if parsed.scheme:
            require(parsed.scheme in ('https','http','mailto') and not is_image,
                    'Only local figures and ordinary external evidence links are supported')
            return raw
        require(not parsed.netloc,'Network-relative asset/link is unsupported')
        if not parsed.path:return raw
        require(not parsed.query,'Local links with queries need explicit handling')
        path=(base/unquote(parsed.path)).resolve(strict=True)
        require(path.is_file(),'Local link is not a file: '+str(path))
        data=path.read_bytes();digest=sha_bytes(data)
        require(str(path) not in inputs or inputs[str(path)]==digest,
                'Repeated input changed while rendering: '+str(path))
        inputs[str(path)]=digest
        if is_image:
            require(path.suffix.lower() in ('.png','.svg'),'Expected a reviewed PNG or SVG figure')
            name=digest[:16]+'-'+path.name;destination=out/'assets'/name
            if destination.exists():
                require(destination.read_bytes()==data,'Conflicting copied figure asset: '+str(destination))
            else:destination.write_bytes(data)
            figures.append({'source':str(path),'sha256':digest,'asset':'assets/'+name})
            return 'assets/'+quote(name)
        if not inside(path,root):
            require(args.allow_external_local_links,
                    'Evidence outside repository: deliberately copy it or explicitly allow and disclose it: '+str(path))
            external.append(str(path))
        relative=Path(os.path.relpath(path,out)).as_posix()
        local_links.append({'source':str(path),'href':relative,'location_inside_repository':inside(path,root)})
        return quote(relative,safe='/')+('#'+parsed.fragment if parsed.fragment else '')

    # Current draft has ordinary inline images/links and one-line reference
    # definitions. Rendered anchors below validate both forms after Markdown.
    body=re.sub(r'(!?\[[^\]\n]*\]\()([^\n)]+)(\))',
                lambda m:m.group(1)+target(m.group(2),m.group(1).startswith('!'))+m.group(3),body)
    body=re.sub(r'(?m)^(\[[^\]\n]+\]:\s*)(\S+)(\s*)$',
                lambda m:m.group(1)+target(m.group(2))+m.group(3),body)
    if args.historical_viewer:
        viewer=target(str(args.historical_viewer.resolve(strict=True)))
        body+='\n\n## Historical interactive illustration\n\n'
        body+='[Open the offline 3D explorer]('+viewer+'). Historical complete n=256 examples: '
        body+='deduplicating contractions, graph seed 42 and half sampling with sample seed 0. '
        body+='These are not eighth-sampling timing inputs or a trace of its private recursion.\n'
        viewers.append({'role':'historical_deduplicating_half_illustration','href':viewer})
    if args.current_viewer:
        viewer=target(str(args.current_viewer.resolve(strict=True)))
        body+='\n\n## Current root-stage interactive reconstruction\n\n'
        body+='[Open the offline hierarchy root-stage explorer]('+viewer+'). '
        body+='Ordered and shuffled attachment fixtures use n=1,024, m/n=32, intrusion 0, '
        body+='graph seed 17000011 and sampler seed 2801. The explorer retains crossing '
        body+='parallel records and reconstructs the first two contractions, root samples '
        body+='at probabilities one half and one eighth, their sample forests and heavy-edge filtering. '
        body+='This is a root-stage reconstruction, not a recorded full recursive KKT trace. '
        body+='The half-policy root sample is reconstructed; the full half solver is not rerun by this viewer. '
        body+='It illustrates structure and filtering, not a timing result or an n=1,024 speed claim.\n'
        viewers.append({'role':'retained_parallel_root_reconstruction_half_and_eighth',
                        'href':viewer,'n':1024,'density':32,'intrusion':0,
                        'graph_seed':17000011,'sampling_seed':2801,
                        'full_recursion_trace':False})
    if external:
        body+='\n\nPublication note: some evidence links resolve outside this repository checkout. '
        body+='Those dependencies are listed in render_metadata.json; this edition is not a fully portable evidence bundle.\n'
    write(out/'REPORT.md',body)
    md=markdown.Markdown(extensions=['tables','fenced_code','sane_lists','toc'],
                         extension_configs={'toc':{'toc_depth':'2-3'}})
    fragment=md.convert(body)
    figure_pattern=r'<p><img\s+([^>]*?)\s*/?></p>'
    def figure(match):
        attributes=match.group(1)
        alt=re.search(r'\balt="([^"]*)"',attributes)
        return '<figure><img '+attributes+'><figcaption>'+(alt.group(1) if alt else '')+'</figcaption></figure>'
    fragment=re.sub(figure_pattern,figure,fragment)
    def embed(match):
        ref=html.unescape(match.group(1));path=(out/unquote(ref)).resolve(strict=True)
        require(inside(path,out/'assets'),'Unexpected image outside copied assets')
        mime='image/svg+xml' if path.suffix.lower()=='.svg' else 'image/png'
        return 'src="data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
    fragment=re.sub(r'src="([^"]+)"',embed,fragment)
    require(len(re.findall(r'src="data:',fragment))==len(figures),'Image conversion count mismatch')
    document='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(args.title)+'</title><style>'+STYLE+'</style></head><body><nav><a href="REPORT.md">Markdown source</a><a href="#contents">Contents</a></nav><main><div id="contents">'+md.toc+'</div>'+fragment+'</main></body></html>'
    typography=PrintHyphens();typography.feed(document);typography.close()
    document=''.join(typography.parts)
    links=Links();links.feed(document)
    for href in links.links:
        parsed=urlsplit(href)
        if parsed.scheme:continue
        if parsed.path:require((out/unquote(parsed.path)).is_file(),'Missing rendered local link: '+href)
        elif parsed.fragment:require(parsed.fragment in links.ids,'Missing same-page anchor: '+href)
    write(out/'report.html',document)
    metadata.update(source=str(source),source_sha256=inputs[str(source)],input_sha256=inputs,
        equation_translations=translations,figures=figures,local_evidence_links=local_links,
        external_local_dependencies=sorted(set(external)),
        linked_viewers=viewers,viewer_proof_validation='separate prerequisite, not performed by renderer',
        print_hyphens={'scope':'HTML text nodes and their character references; PDF inherits HTML',
                      'source_codepoints':'U+2010 through U+2015','replacement':'U+002D',
                      'replacement_count':typography.replacements,'math_minus_U2212_preserved':True,
                      'markdown_attributes_and_figure_bytes_unchanged':True},
        all_evidence_paths_inside_repository=not external,evidence_bundle_portability_verified=False,
        publication_file_tracking_check='pending: each linked file must be tracked or explicitly copied into the edition',
        native_build_proof_portability='not established by relative report links; original-machine paths may remain',
        embedded_figures=len(figures),
        markdown_library_version=importlib.metadata.version('Markdown'),
        browser_interaction_qa='pending',pdf_every_page_visual_qa='pending',page_cap=40)
    if args.pdf:
        from playwright.sync_api import sync_playwright
        from pypdf import PdfReader
        target_pdf=out/'report.pdf'
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            metadata['chromium_version']=browser.version
            page=browser.new_page(viewport={'width':1280,'height':960})
            errors=[];network=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            def block(route):network.append(route.request.url);route.abort()
            page.route(re.compile(r'^https?://'),block)
            page.goto((out/'report.html').as_uri(),wait_until='load',timeout=30000)
            page.evaluate('document.fonts.ready')
            page.wait_for_function('[...document.images].every(i => i.complete && i.naturalWidth > 0)',timeout=30000)
            require(not errors and not network,'Browser resource/JavaScript failure')
            page.pdf(path=str(target_pdf),format='A4',print_background=True,prefer_css_page_size=True,
                display_header_footer=True,header_template='<span></span>',
                footer_template='<div style="font-size:8px;color:#617080;width:100%;text-align:center">KKT in practice · <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
            require(not errors and not network,'Browser error during PDF printing')
            browser.close()
        pages=len(PdfReader(target_pdf).pages)
        metadata.update(pdf_pages=pages,pdf_sha256=sha(target_pdf),
            playwright_version=importlib.metadata.version('playwright'),
            pypdf_version=importlib.metadata.version('pypdf'),pdf_automatic_load_checks='pass')
        require(0<pages<=40,'PDF exceeds the forty-page cap: '+str(pages))
    else:metadata['pdf_pages']=None
    for path,digest in inputs.items():require(sha(Path(path))==digest,'Input changed while rendering: '+path)
    metadata['output_sha256']={str(path.relative_to(out)):sha(path) for path in out.rglob('*') if path.is_file()}
    metadata['validation']='rendered_pending_visual_qa'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--asset-base',type=Path,required=True)
    parser.add_argument('--repo-root',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--title',default='KKT in practice: current evidence')
    parser.add_argument('--historical-viewer',type=Path)
    parser.add_argument('--current-viewer',type=Path)
    parser.add_argument('--allow-external-local-links',action='store_true')
    parser.add_argument('--pdf',action='store_true')
    args=parser.parse_args();out=args.output_dir.resolve()
    require(not out.exists(),'Refusing to overwrite an edition/attempt directory')
    out.mkdir(parents=True)
    metadata={'schema':'kkt_current_report_render_v1','validation':'running','command':sys.argv,
        'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'native_solver_execution':False,'historical_files_modified':False,
        'visual_acceptance_is_separate':True}
    try:render(args,metadata)
    except BaseException as error:
        metadata.update(validation='failed',error=repr(error));raise
    finally:write(out/'render_metadata.json',json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({key:metadata.get(key) for key in ('validation','embedded_figures','pdf_pages','page_cap')}))


if __name__=='__main__':main()
