#!/usr/bin/env python3
"""Render the Markdown and embedded explorer to a self-contained HTML edition.

The --pdf option additionally uses Chromium's print layout to check the user-
requested <=40 page limit. Read the PDF skill and run its artifact-start marker
before the first PDF-authoring invocation. Dependencies: markdown, playwright,
pypdf; Chromium installed through python3 -m playwright install chromium.
"""
import argparse
import base64
import html
import json
from pathlib import Path
import re
import markdown

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
STYLE='''
:root{color-scheme:light;--ink:#193044;--muted:#516575;--teal:#007e88}
*{box-sizing:border-box}body{margin:0;background:#e9eff2;color:var(--ink);font:16px/1.65 system-ui,-apple-system,sans-serif}
nav{position:sticky;top:0;z-index:20;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;background:#193044;color:#fff;padding:12px 26px;font-size:14px}nav a{color:#fff;margin-left:14px}nav strong{font-weight:600}
main{max-width:1030px;margin:28px auto}.page{background:white;padding:48px 62px;margin:0 0 24px;box-shadow:0 2px 12px #1930440d}
h1{font:600 46px/1.13 Georgia,serif;letter-spacing:-1px;margin:14px 0 24px}h2{font:600 28px/1.24 Georgia,serif;margin:0 0 22px}h3{font-size:18px;line-height:1.3}p{margin:12px 0}strong{font-weight:650}a{color:var(--teal);text-underline-offset:3px}code{font:88% ui-monospace,Menlo,monospace;background:#f0f4f6;padding:1px 3px;border-radius:3px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f4f6;padding:16px}pre code{padding:0}table{border-collapse:collapse;width:100%;font-size:13px;line-height:1.45;margin:18px 0}th{text-align:left;background:#e8f1f2;font-weight:650}th,td{padding:7px 9px;border-bottom:1px solid #d9e1e6;vertical-align:top}tr:nth-child(even) td{background:#f8fafb}td code{white-space:normal}img{display:block;max-width:100%;height:auto;margin:16px auto}li{margin:7px 0}blockquote{border-left:3px solid var(--teal);margin:18px 0;padding:2px 20px;background:#f5f9fa}.page-number{font-size:11px;color:#758693;text-transform:uppercase;letter-spacing:1px;margin-bottom:15px}.caption{font-size:13px;color:var(--muted)}.interactive-inline{margin:22px -25px}.interactive-inline h3{margin-top:20px}.explorer{background:#f8fbfc;padding:16px;border:1px solid #d9e1e6}.explorer-controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:13px}select,button{font:inherit;padding:7px;border:1px solid #b9c7d0;border-radius:4px;background:#fff;color:#193044}canvas{width:100%;height:510px;touch-action:none;cursor:grab;background:linear-gradient(#f8fbfc,#fff)}canvas:focus{outline:2px solid #007e88}#graph-info{font-variant-numeric:tabular-nums;font-weight:600}#node-detail,#stage-explanation{font-size:13px}#node-detail{min-height:21px}.contents{columns:2;font-size:13px}.contents a{display:block;margin:5px 0}
@media(max-width:700px){main{margin:12px}.page{padding:25px 22px}h1{font-size:34px}h2{font-size:25px}table{font-size:11px}th,td{padding:5px}nav{position:static;padding:10px 15px}.interactive-inline{margin:18px -10px}canvas{height:420px}.contents{columns:1}}
@page{size:A4;margin:14mm 14mm 17mm}
@media print{body{background:white;font:10.2pt/1.42 Arial,sans-serif;color:#193044}nav,.interactive-inline{display:none!important}main{max-width:none;margin:0}.page{padding:0;margin:0;box-shadow:none;break-after:page}.page:last-child{break-after:auto}.page-number{font-size:8pt;margin-bottom:10pt}h1{font-size:30pt;margin:10pt 0 16pt}h2{font-size:20pt;margin:0 0 12pt}h3{font-size:12pt}p{margin:8pt 0}a{color:#145e68;text-decoration:none;overflow-wrap:anywhere}code{font-size:8.6pt}table{font-size:8.25pt;line-height:1.25;margin:10pt 0;break-inside:avoid}th,td{padding:4pt 5pt}img{max-height:164mm;object-fit:contain;margin:9pt auto}li{margin:5pt 0}.contents{font-size:8pt}.caption{font-size:8pt}blockquote{margin:10pt 0}h1,h2,h3{break-after:avoid}tr{break-inside:avoid}}
'''


def embed_images(rendered):
    def sub(match):
        ref=html.unescape(match.group(1))
        if re.match(r'https?://|data:',ref):return match.group(0)
        path=(HERE/ref).resolve()
        if not path.is_file():raise ValueError('Missing figure: '+str(path))
        mime='image/svg+xml' if path.suffix=='.svg' else 'image/png'
        return 'src="data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
    return re.sub(r'src="([^"]+)"',sub,rendered)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pdf',action='store_true');args=p.parse_args()
    source=(HERE/'REPORT.md').read_text()
    if re.search(r'\{\{[A-Z_]+\}\}',source):raise ValueError('Unresolved report data placeholder')
    fragment=(HERE/'explorer_fragment.html').read_text()
    parts=source.split('<!-- PAGE -->')
    if len(parts)>40:raise ValueError('More than 40 planned sections')
    sections=[]
    for i,part in enumerate(parts):
        part=part.replace('<!-- EXPLORER -->','<div class="interactive-inline"><h3>Explore these exact transformations in 3D</h3>'+fragment+'</div>')
        rendered=markdown.markdown(part,extensions=['tables','fenced_code','sane_lists'])
        sections.append(f'<section class="page" id="section-{i}"><div class="page-number">KKT in practice · {i+1:02d} / {len(parts):02d}</div>'+embed_images(rendered)+'</section>')
    document='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Making KKT practical</title><style>'+STYLE+'</style></head><body><nav><strong>Making KKT practical</strong><span><a href="REPORT.md">Markdown source</a><a href="#section-15">New results</a><a href="#explorer">3D explorer</a><a href="#section-24">Ablation</a></span></nav><main>'+''.join(sections)+'</main></body></html>'
    (HERE/'report.html').write_text(document)
    meta={'markdown_sha256':__import__('hashlib').sha256(source.encode()).hexdigest(),'planned_sections':len(parts),'word_count_approx':len(source.split()),'embedded_figures':len(re.findall('src="data:',document))}
    if args.pdf:
        from playwright.sync_api import sync_playwright
        from pypdf import PdfReader
        out=ROOT/'output/pdf';out.mkdir(parents=True,exist_ok=True)
        target=out/'kkt-practical-report.pdf'
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            page=browser.new_page(viewport={'width':1200,'height':900})
            errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto((HERE/'report.html').as_uri(),wait_until='load')
            page.evaluate('document.fonts.ready')
            page.pdf(path=str(target),format='A4',print_background=True,prefer_css_page_size=True,
                     display_header_footer=True,header_template='<span></span>',
                     footer_template='<div style="font-size:8px;color:#617080;width:100%;text-align:center">Making KKT practical · <span class="pageNumber"></span> / <span class="totalPages"></span></div>')
            browser.close()
        if errors:raise RuntimeError('Browser errors: '+str(errors))
        pages=len(PdfReader(target).pages)
        if pages>40:raise ValueError(f'Printed PDF exceeds cap: {pages} pages')
        meta.update(pdf_pages=pages,pdf_sha256=__import__('hashlib').sha256(target.read_bytes()).hexdigest())
    (HERE/'render_metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps(meta))

if __name__=='__main__':main()
