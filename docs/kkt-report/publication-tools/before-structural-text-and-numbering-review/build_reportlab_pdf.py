#!/usr/bin/env python3
"""Render a new ReportLab PDF from the accepted current-edition HTML, offline.

No browser or native solver is launched. This is a narrow adapter for the HTML
emitted by build_current_report.py, not an arbitrary HTML/CSS engine. Final
every-page visual QA is mandatory; successful layout is not browser/viewer QA.
"""
import argparse
import base64
import datetime
import hashlib
import html
from html.parser import HTMLParser
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote, unquote, urlsplit

FONT_DIR = Path('/Users/random_person/Library/Python/3.9/lib/python/site-packages/matplotlib/mpl-data/fonts/ttf')
FONT_FILES = {'KKT': 'DejaVuSans.ttf', 'KKT-Bold': 'DejaVuSans-Bold.ttf',
              'KKT-Italic': 'DejaVuSans-Oblique.ttf', 'KKT-BoldItalic': 'DejaVuSans-BoldOblique.ttf',
              'KKT-Mono': 'DejaVuSansMono.ttf'}
VOID = {'meta', 'link', 'img', 'br', 'hr'}


def require(value, message):
    if not value: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(data): return hashlib.sha256(data).hexdigest()
def read_json(path): return json.loads(Path(path).read_text())
def write_json(path, value):
    with path.open('x') as stream: json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')


class Node:
    def __init__(self, tag, attrs=()): self.tag=tag; self.attrs=dict(attrs); self.children=[]
    def text(self): return ''.join(child if isinstance(child, str) else child.text() for child in self.children)


class Document(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.root=Node('root'); self.stack=[self.root]
    def handle_starttag(self, tag, attrs):
        require(len(dict(attrs)) == len(attrs), 'Duplicate HTML attribute')
        node=Node(tag,attrs); self.stack[-1].children.append(node)
        if tag not in VOID: self.stack.append(node)
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_endtag(self, tag):
        require(len(self.stack)>1 and self.stack[-1].tag==tag, 'Unbalanced HTML tag: '+tag)
        self.stack.pop()
    def handle_data(self, data): self.stack[-1].children.append(data)
    def close(self):
        super().close(); require(len(self.stack)==1, 'Unclosed HTML')


def nodes(node, tag):
    result=[]
    for child in node.children:
        if isinstance(child,Node):
            if child.tag==tag: result.append(child)
            result.extend(nodes(child,tag))
    return result


def bind(bound, path, expected=None):
    path=Path(path).resolve(strict=True); value=sha(path)
    require(expected is None or expected==value, 'Input digest mismatch: '+str(path))
    require(str(path) not in bound or bound[str(path)]==value, 'Input changed: '+str(path))
    bound[str(path)]=value; return path


def checked_edition(edition, figure_spec):
    edition=edition.resolve(strict=True); bound={}
    meta_path=bind(bound,edition/'render_metadata.json'); meta=read_json(meta_path)
    require(meta['schema']=='kkt_current_report_render_v1' and
            meta['validation']=='rendered_pending_visual_qa', 'Need completed accepted HTML renderer output')
    require(meta['external_local_dependencies']==[], 'Final PDF cannot use external local evidence links')
    for path,value in meta['input_sha256'].items(): bind(bound,path,value)
    for path,value in meta['output_sha256'].items():
        target=(edition/path).resolve(strict=True)
        require(target.is_relative_to(edition), 'Output inventory escapes edition')
        bind(bound,target,value)
    require('report.html' in meta['output_sha256'] and 'REPORT.md' in meta['output_sha256'], 'Missing primary edition outputs')
    spec_path=bind(bound,figure_spec); specs=read_json(spec_path)
    require(type(specs) is dict and specs.get('schema')=='kkt_pdf_figure_layout_v1' and
            type(specs.get('figures')) is dict, 'Invalid figure layout declaration')
    require(set(specs['figures'])=={item['sha256'] for item in meta['figures']}, 'Figure declaration must cover every embedded digest exactly')
    document=Document(); document.feed((edition/'report.html').read_text()); document.close()
    mains=nodes(document.root,'main'); require(len(mains)==1,'Expected exactly one main report body')
    return meta,specs['figures'],mains[0],bound


def page_gate(pdf):
    from pypdf import PdfReader
    reader=PdfReader(pdf); count=len(reader.pages)
    require(1<=count<=40,'Actual PDF must contain 1..40 pages, found '+str(count))
    for page in reader.pages:
        require(abs(float(page.mediabox.width)-595.2756)<.1 and
                abs(float(page.mediabox.height)-841.8898)<.1,'Non-A4 PDF page')
    return count


class Adapter:
    def __init__(self, edition, output, metadata, specs, bound, font_dir):
        from reportlab.lib import colors
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph
        self.edition=edition; self.output=output; self.metadata=metadata; self.specs=specs; self.bound=bound
        self.image_index=0; self.blocks=[]; self.figures=[]; self.links=[]; self.anchors=set(); self.used_specs=set()
        self.width=595.2755905511812-28*72/25.4
        self.height=841.8897637795277-32*72/25.4
        self.Paragraph=Paragraph; self.pdfmetrics=pdfmetrics
        for name,file in FONT_FILES.items():
            path=bind(bound,font_dir/file); pdfmetrics.registerFont(TTFont(name,str(path)))
        pdfmetrics.registerFontFamily('KKT',normal='KKT',bold='KKT-Bold',italic='KKT-Italic',boldItalic='KKT-BoldItalic')
        self.styles={}
        for name,size,leading in (('body',10,14),('h1',23,28),('h2',16,20),('h3',12,16),
                                  ('h4',10.5,14),('table',8.5,11),('caption',9,12),('code',9,12),('quote',10,14)):
            self.styles[name]=ParagraphStyle(name,fontName='KKT-Mono' if name=='code' else
                ('KKT-Bold' if name.startswith('h') else 'KKT'),fontSize=size,leading=leading,
                textColor=colors.HexColor('#193044'),spaceAfter=7 if name!='table' else 0,
                spaceBefore=12 if name in ('h2','h3','h4') else 0,
                keepWithNext=name.startswith('h'),splitLongWords=1,allowWidows=0,allowOrphans=0)

    def text(self, value, font='KKT'):
        require(not any('\u2010'<=char<='\u2015' for char in value), 'Unnormalized visible dash in accepted HTML')
        glyphs=self.pdfmetrics.getFont(font).face.charToGlyph
        require(all(char.isspace() or ord(char) in glyphs for char in value),
                'Missing embedded-font glyph: '+repr(''.join(char for char in value if not char.isspace() and ord(char) not in glyphs)))
        return html.escape(value)

    def inline(self, node, font='KKT'):
        if isinstance(node,str): return self.text(node,font)
        tag=node.tag
        if tag=='br': return '<br/>'
        mappings={'strong':('b','KKT-Bold'),'b':('b','KKT-Bold'),'em':('i','KKT-Italic'),
                  'i':('i','KKT-Italic'),'code':('font','KKT-Mono'),'sup':('super',font),'sub':('sub',font)}
        if tag in mappings:
            output_tag,next_font=mappings[tag]; body=''.join(self.inline(c,next_font) for c in node.children)
            attrs=' name="KKT-Mono"' if tag=='code' else ''
            return '<'+output_tag+attrs+'>'+body+'</'+output_tag+'>'
        if tag=='a':
            href=node.attrs.get('href'); require(href is not None,'Anchor without href')
            parts=urlsplit(href)
            if not parts.scheme and parts.path:
                target=(self.edition/unquote(parts.path)).resolve(strict=True)
                require(target.is_file(),'PDF link target missing')
                bind(self.bound,target)
                href=quote(os.path.relpath(target,self.output),safe='/')+('#'+parts.fragment if parts.fragment else '')
            elif parts.scheme: require(parts.scheme in ('http','https','mailto'),'Unsupported PDF link scheme')
            self.links.append(href)
            return '<link href="'+html.escape(href,quote=True)+'" color="#007e88">'+''.join(self.inline(c,font) for c in node.children)+'</link>'
        require(tag in ('span',),'Unsupported inline HTML: '+tag)
        return ''.join(self.inline(c,font) for c in node.children)

    def paragraph(self,node,kind='body',prefix=''):
        text=prefix+''.join(self.inline(child, 'KKT-Mono' if kind=='code' else 'KKT') for child in node.children)
        if 'id' in node.attrs:
            identity=node.attrs['id'];require(identity not in self.anchors,'Duplicate PDF anchor');self.anchors.add(identity)
            text='<a name="'+html.escape(identity,quote=True)+'"/>'+text
        self.blocks.append({'tag':node.tag,'text':node.text()})
        return self.Paragraph(text,self.styles[kind])

    def figure(self,node):
        from reportlab.platypus import Image,KeepTogether,Spacer
        imgs=[c for c in node.children if isinstance(c,Node) and c.tag=='img']
        captions=[c for c in node.children if isinstance(c,Node) and c.tag=='figcaption']
        require(len(imgs)==1 and len(captions)==1 and all(
            (isinstance(c,str) and not c.strip()) or c in imgs+captions for c in node.children),'Unsupported figure structure')
        require(self.image_index<len(self.metadata['figures']),'Unexpected HTML figure')
        item=self.metadata['figures'][self.image_index];self.image_index+=1
        raw=imgs[0].attrs['src'];require(raw.startswith('data:image/png;base64,'),
            'ReportLab fallback requires a reviewed PNG figure; select the existing equivalent PNG before HTML rendering')
        image_data=base64.b64decode(raw.partition(',')[2],validate=True)
        require(digest(image_data)==item['sha256'],'Embedded HTML/figure digest mismatch')
        path=(self.edition/item['asset']).resolve(strict=True)
        require(path.is_relative_to(self.edition/'assets') and
                self.metadata['output_sha256'].get(item['asset'])==item['sha256'], 'Figure is not a bound copied asset')
        path=bind(self.bound,path,item['sha256']); spec=self.specs[item['sha256']]
        require(set(spec)=={'nominal_width_inches','minimum_label_pt','basis'},'Unexpected figure size fields')
        for key in ('nominal_width_inches','minimum_label_pt'):
            require(type(spec[key]) in (int,float) and math.isfinite(spec[key]) and spec[key]>0,'Invalid figure size')
        require(type(spec['basis']) is str and spec['basis'].strip(),'Figure label declaration needs reviewed source basis')
        nominal=spec['nominal_width_inches']*72; width=min(nominal,self.width)
        actual_min=spec['minimum_label_pt']*width/nominal
        require(actual_min>=8.5-1e-9,'Figure labels would shrink below 8.5pt; use a paper layout, not an undersized figure')
        picture=Image(str(path));height=width*picture.imageHeight/picture.imageWidth
        picture.drawWidth=width;picture.drawHeight=height;picture.hAlign='CENTER'
        caption=self.paragraph(captions[0],'caption');_,caption_height=caption.wrap(self.width,self.height)
        require(height+caption_height+24<=self.height,'Figure and caption exceed one A4 page at legible size')
        self.figures.append(dict(sha256=item['sha256'],asset=item['asset'],width_pt=width,height_pt=height,
            declared_minimum_label_pt=spec['minimum_label_pt'],placed_minimum_label_pt=actual_min,
            declaration_basis=spec['basis'],page_scale_visual_qa='pending'))
        self.used_specs.add(item['sha256'])
        return [KeepTogether([Spacer(1,7),picture,Spacer(1,5),caption,Spacer(1,7)])]

    def table(self,node):
        from reportlab.lib import colors
        from reportlab.platypus import Table,TableStyle,Spacer
        groups=[c for c in node.children if isinstance(c,Node)]
        require(all(c.tag in ('thead','tbody','tr') for c in groups),'Unsupported table group')
        rows=[];header_count=0
        for group in groups:
            row_nodes=[group] if group.tag=='tr' else [c for c in group.children if isinstance(c,Node)]
            require(all(row.tag=='tr' for row in row_nodes),'Unexpected table row')
            if group.tag=='thead':header_count+=len(row_nodes)
            rows.extend(row_nodes)
        require(rows,'Empty table')
        cells=[[c for c in row.children if isinstance(c,Node)] for row in rows]; columns=len(cells[0])
        require(columns>0 and all(len(row)==columns for row in cells),'Ragged table')
        require(all(c.tag in ('th','td') and not ('colspan' in c.attrs or 'rowspan' in c.attrs)
                    for row in cells for c in row),'Unsupported spanning table')
        weights=[max(9,min(32,max(len(cells[r][col].text()) for r in range(len(cells))))) for col in range(columns)]
        widths=[self.width*w/sum(weights) for w in weights]
        require(min(widths)>=32,'Too many/narrow table columns; split the publication table without omitting data')
        values=[]
        for row in cells:
            result=[]
            for cell in row:
                # Bold headers are an inherited paragraph style, not unbalanced markup.
                paragraph=self.paragraph(cell,'table')
                if cell.tag=='th':
                    from copy import copy
                    paragraph.style=copy(paragraph.style);paragraph.style.fontName='KKT-Bold'
                result.append(paragraph)
            values.append(result)
        table=Table(values,colWidths=widths,repeatRows=header_count,hAlign='LEFT',splitByRow=1)
        table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),
            ('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
            ('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#dae3e7')),
            ('BACKGROUND',(0,0),(-1,header_count-1),colors.HexColor('#e8f1f2'))] if header_count else
            [('VALIGN',(0,0),(-1,-1),'TOP')]))
        width,_=table.wrap(self.width,self.height);require(width<=self.width+.01,'Table exceeds page width')
        return [table,Spacer(1,8)]

    def flow(self,node):
        from reportlab.platypus import HRFlowable,Indenter
        if isinstance(node,str):require(not node.strip(),'Unwrapped body text');return []
        tag=node.tag
        if tag=='div' and node.attrs.get('id')=='contents':return [] # Generated duplicate navigation only.
        if tag in ('p','h1','h2','h3','h4'):return [self.paragraph(node,tag if tag!='p' else 'body')]
        if tag=='figure':return self.figure(node)
        if tag=='table':return self.table(node)
        if tag=='blockquote':
            require(all((isinstance(c,str) and not c.strip()) or (isinstance(c,Node) and c.tag=='p') for c in node.children),
                    'Unsupported blockquote content')
            return [Indenter(left=10),*[self.paragraph(c,'quote') for c in node.children if isinstance(c,Node)],Indenter(left=-10)]
        if tag=='pre':
            require(all(isinstance(c,str) or (c.tag=='code' and all(isinstance(v,str) for v in c.children))
                        for c in node.children),'Unsupported preformatted content')
            value=node.text();self.blocks.append({'tag':'pre','text':value})
            text=self.text(value,'KKT-Mono').replace(' ','&#160;').replace('\n','<br/>')
            return [self.Paragraph(text,self.styles['code'])]
        if tag in ('ul','ol'):
            result=[]; index=0
            for item in node.children:
                if isinstance(item,str):require(not item.strip(),'Unwrapped list text');continue
                require(item.tag=='li','Unexpected list child');index+=1
                result.append(Indenter(left=12))
                inline=Node('p');inline.children=[]
                for child in item.children:
                    require(not isinstance(child,Node) or child.tag not in ('ul','ol','table','figure'),
                            'Nested list/block needs explicit layout review')
                    if isinstance(child,Node) and child.tag=='p':inline.children.extend(child.children)
                    else:inline.children.append(child)
                result.append(self.paragraph(inline,prefix=str(index)+'. ' if tag=='ol' else '• '))
                result.append(Indenter(left=-12))
            return result
        if tag=='hr':return [HRFlowable(width='100%',thickness=.4,spaceBefore=8,spaceAfter=8)]
        raise ValueError('Unsupported report block: '+tag)


def render(args,receipt):
    from reportlab import rl_config
    from reportlab.lib.pagesizes import A4
    edition=args.edition.resolve(strict=True);out=args.output_dir.resolve()
    meta,specs,main,bound=checked_edition(edition,args.figure_layout)
    bind(bound,Path(__file__).resolve())
    adapter=Adapter(edition,out,meta,specs,bound,args.font_dir.resolve(strict=True));story=[]
    for child in main.children:story.extend(adapter.flow(child))
    require(adapter.image_index==len(meta['figures']) and adapter.used_specs==set(specs),'Incomplete figure conversion')
    for href in adapter.links:
        if href.startswith('#'):require(unquote(href[1:]) in adapter.anchors,'Missing PDF internal anchor: '+href)
    require(story and adapter.blocks,'Empty report body')
    initial=dict(bound);pdf=out/'report.pdf'
    # A default frame normally has 6pt internal padding, which would
    # shrink the declared paper width. Remove that padding explicitly.
    from reportlab.platypus import Frame,PageTemplate
    from reportlab.platypus.doctemplate import BaseDocTemplate
    doc=BaseDocTemplate(str(pdf),pagesize=A4,leftMargin=14*72/25.4,rightMargin=14*72/25.4,
        topMargin=15*72/25.4,bottomMargin=17*72/25.4,title=args.title,author='KKT experiment report')
    frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,leftPadding=0,rightPadding=0,
                topPadding=0,bottomPadding=0,id='body')
    def page(canvas,document):
        canvas.saveState();canvas.setFont('KKT',9);canvas.setFillColorRGB(.32,.40,.46)
        canvas.drawCentredString(A4[0]/2,9*72/25.4,'KKT in practice  |  '+str(document.page));canvas.restoreState()
    doc.addPageTemplates(PageTemplate(id='report',frames=frame,onPage=page))
    old=rl_config.allowTableBoundsErrors
    try:
        rl_config.allowTableBoundsErrors=0;doc.build(story)
    finally:rl_config.allowTableBoundsErrors=old
    pages=page_gate(pdf)
    for path,value in initial.items():require(sha(path)==value,'Input changed during PDF render: '+path)
    receipt.update(validation='rendered_pending_visual_qa',pdf_pages=pages,pdf_sha256=sha(pdf),
        input_sha256=initial,figures=adapter.figures,body_blocks=adapter.blocks,
        body_text_sha256=digest(json.dumps(adapter.blocks,ensure_ascii=False,separators=(',',':')).encode()),
        links=adapter.links,anchors=sorted(adapter.anchors),
        reportlab_version=importlib.metadata.version('reportlab'),pypdf_version=importlib.metadata.version('pypdf'),
        text_font_pt=10,code_font_pt=9,table_font_pt=8.5,caption_font_pt=9,
        typography_source='Already normalized accepted HTML; original Markdown/HTML/assets unchanged',
        generated_navigation_omitted='HTML nav and duplicate contents list only; all main report content retained',
        figure_label_check='Declared source minimum times physical placement scale; visual confirmation still required')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edition',type=Path,required=True)
    parser.add_argument('--figure-layout',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--font-dir',type=Path,default=FONT_DIR)
    parser.add_argument('--title',default='KKT in practice: current evidence')
    args=parser.parse_args();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=False)
    receipt=dict(schema='kkt_reportlab_pdf_v1',validation='running',command=sys.argv,
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_solver_execution=False,
        historical_files_modified=False,page_cap=40,pdf_every_page_visual_qa='pending',
        browser_interaction_qa='not performed; unavailable browser is not replaced by PDF layout',
        viewer_interaction_qa='pending separately',publication_link_completeness='separate tracked/copied-link gate')
    try:render(args,receipt)
    except BaseException as error:receipt.update(validation='failed',error=repr(error));raise
    finally:write_json(out/'pdf_metadata.json',receipt)
    print(json.dumps({key:receipt.get(key) for key in ('validation','pdf_pages','page_cap','pdf_sha256')}))


if __name__=='__main__':main()
