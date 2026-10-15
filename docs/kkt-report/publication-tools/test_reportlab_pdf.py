#!/usr/bin/env python3
"""Focused PDF gates; synthetic artifacts are retained under an exclusive path.

Run only after root releases nonperformance rendering. No browser/native solver
is launched. Final report rendering and every-page QA are separate tasks.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


pdf=module('_reportlab_pdf_gate','build_reportlab_pdf.py')
html_renderer=module('_html_pdf_gate','build_current_report.py')
ARTIFACTS=None


def fixture(name,extra=''):
    from PIL import Image,ImageDraw,ImageFont
    root=ARTIFACTS/name;root.mkdir()
    image=Image.new('RGB',(1420,500),'#f3f8fa');draw=ImageDraw.Draw(image)
    font=ImageFont.truetype(str(pdf.FONT_DIR/'DejaVuSans.ttf'),36)
    draw.text((45,45),'SYNTHETIC FIGURE - no benchmark data',fill='#193044',font=font)
    draw.text((45,130),'Minimum declared label: 9 pt at 7.1 inches',fill='#193044',font=font)
    draw.line((60,390,1360,390),fill='#007e88',width=5)
    image.save(root/'figure.png')
    (root/'evidence.txt').write_text('Synthetic evidence only.\n')
    body=r'''# Synthetic current edition

This body has **bold**, *italic*, `inline code`, an en–dash, an em—dash,
and a mathematical minus −. [Evidence](evidence.txt) stays a local link.

## Offline equations

\[
A\geq\frac{c}{1-p},\qquad B\geq2c+\frac{A}{2p}.
\]

\[
U\leq\min\left(Q,\sum_v\operatorname{depth}(v)\right)\leq\min(Q,Bh).
\]

\[
I_b=(c/b)\binom b2-(c-c/b).
\]

## Controls and ranges

| Case | KKT | Retained Boruvka | Deduplicating Boruvka | Kruskal | Prim | Original Boruvka |
| --- | --- | --- | --- | --- | --- | --- |
| synthetic_small_identifier | 1.49 | 1.00 | 1.19 | 0.78 | 0.81 | 0.89 |
| synthetic_large_identifier | 0.84 | 1.00 | 2.15 | 0.72 | 0.79 | 1.13 |

1. A numbered item.
2. Another item preserving the endpoint loss.

- One bullet with **emphasis**.
- Another bullet with [same-page navigation](#offline-equations).

```text
This_code_path_is_deliberately_long_to_exercise_wrapping_without_reducing_the_fixed_nine_point_type_size_and_without_clipping_the_page_frame.
    indentation is retained
```

![Synthetic chart caption, preserving every stated range.](figure.png)

## Closing body sentinel

No measurements or final report text are synthesized here.
'''+extra
    source=root/'source.md';source.write_text(body)
    edition=root/'edition';edition.mkdir()
    metadata=dict(schema='kkt_current_report_render_v1',validation='running')
    args=argparse.Namespace(source=source,repo_root=root,asset_base=root,output_dir=edition,
        title='Synthetic PDF gate',historical_viewer=None,current_viewer=None,
        allow_external_local_links=False,pdf=False)
    html_renderer.render(args,metadata);pdf.write_json(edition/'render_metadata.json',metadata)
    spec=root/'figure-layout.json';pdf.write_json(spec,dict(schema='kkt_pdf_figure_layout_v1',figures={
        pdf.sha(root/'figure.png'):dict(nominal_width_inches=7.1,minimum_label_pt=9,
                                      basis='Synthetic fixture only; 36px labels on a 1420px-wide PNG.')}))
    output=root/'pdf';output.mkdir()
    return argparse.Namespace(edition=edition,figure_layout=spec,output_dir=output,
                              font_dir=pdf.FONT_DIR,title='Synthetic PDF gate')


class ReportLabGates(unittest.TestCase):
    def test_accepted_html_equations_links_tables_image_and_actual_a4_pdf(self):
        from pypdf import PdfReader
        args=fixture('positive');receipt={};pdf.render(args,receipt)
        pdf.write_json(args.output_dir/'pdf_metadata.json',receipt)
        self.assertEqual(receipt['validation'],'rendered_pending_visual_qa')
        self.assertTrue(1<=receipt['pdf_pages']<=40)
        self.assertEqual(receipt['table_font_pt'],8.5)
        self.assertEqual(receipt['figures'][0]['placed_minimum_label_pt'],9)
        pages=PdfReader(args.output_dir/'report.pdf').pages
        text='\n'.join(page.extract_text() for page in pages)
        for phrase in ('Synthetic current edition','Closing body sentinel','0.84','1.49','Σᵥ','≤','≥','−'):
            self.assertIn(phrase,text)
        self.assertNotIn('—',text);self.assertNotIn('–',text)
        self.assertIn('#offline-equations',receipt['links'])
        self.assertIn('../evidence.txt',receipt['links'])
        self.assertEqual(len(receipt['figures']),1)
        self.assertEqual(len([b for b in receipt['body_blocks'] if b['tag']=='td']),14)
        self.assertTrue(any(page.get('/Annots') for page in pages))

    def test_changed_input_missing_glyph_and_unsupported_blocks_fail_closed(self):
        args=fixture('changed-source');source=args.edition.parent/'source.md';source.write_text(source.read_text()+'drift')
        with self.assertRaisesRegex(ValueError,'digest mismatch'):pdf.render(args,{})
        args=fixture('unsupported-block', '\n<details><summary>Hidden content must not disappear</summary>Body</details>\n')
        with self.assertRaisesRegex(ValueError,'Unsupported report block'):pdf.render(args,{})
        args=fixture('missing-glyph','\nUnknown glyph: \U0010ffff\n')
        with self.assertRaisesRegex(ValueError,'Missing embedded-font glyph'):pdf.render(args,{})
        document=pdf.Document()
        with self.assertRaisesRegex(ValueError,'Unbalanced'):document.feed('<main><p>bad</main>')
        # Each malformed structural form is parsed directly, so the negative
        # cannot pass merely because the accepted HTML hash was changed.
        args=fixture('structural-negatives')
        meta,specs,main,bound=pdf.checked_edition(args.edition,args.figure_layout)
        adapter=pdf.Adapter(args.edition,args.output_dir,meta,specs,bound,pdf.FONT_DIR)
        snippets=(
            ('<table>stray<tbody><tr><td>kept</td></tr></tbody></table>','table structural text'),
            ('<table><tbody>stray<tr><td>kept</td></tr></tbody></table>','table structural text'),
            ('<table><tbody><tr>stray<td>kept</td></tr></tbody></table>','table structural text'),
            ('<table><tr>stray<td>kept</td></tr></table>','table structural text'),
            ('<ol start="3"><li>must remain third</li></ol>','custom list numbering'),
            ('<ol reversed><li>descending</li></ol>','custom list numbering'),
            ('<ol type="a"><li>alphabetic</li></ol>','custom list numbering'),
            ('<ol><li value="7">must remain seventh</li></ol>','custom list item'),
            ('<ul><li value="7">unsupported value</li></ul>','custom list item'),
            ('<ul type="square"><li>unsupported marker</li></ul>','custom list numbering'),
            ('<ol><li type="a">unsupported marker</li></ol>','custom list item'))
        for source,error in snippets:
            document=pdf.Document();document.feed(source);document.close()
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,error):
                adapter.flow(document.root.children[0])

    def test_figure_size_completeness_asset_and_visible_dash_gates(self):
        args=fixture('figure-gates');initial=pdf.read_json(args.figure_layout);key=next(iter(initial['figures']))
        for field,value,error in (('minimum_label_pt',8.4,'below 8.5'),
                                  ('nominal_width_inches',15.5,'below 8.5'),
                                  ('minimum_label_pt',True,'Invalid figure size')):
            changed=copy.deepcopy(initial);changed['figures'][key][field]=value
            args.figure_layout.write_text(json.dumps(changed))
            with self.subTest(field=field,value=value),self.assertRaisesRegex(ValueError,error):pdf.render(args,{})
        changed=copy.deepcopy(initial);changed['figures']['a'*64]=changed['figures'].pop(key)
        args.figure_layout.write_text(json.dumps(changed))
        with self.assertRaisesRegex(ValueError,'cover every embedded'):pdf.render(args,{})
        args.figure_layout.write_text(json.dumps(initial))
        meta,specs,main,bound=pdf.checked_edition(args.edition,args.figure_layout)
        adapter=pdf.Adapter(args.edition,args.output_dir,meta,specs,bound,pdf.FONT_DIR)
        with self.assertRaisesRegex(ValueError,'Unnormalized'):adapter.text('unprocessed—dash')
        meta['figures'][0]['asset']='../figure.png'
        figure=pdf.nodes(main,'figure')[0]
        with self.assertRaisesRegex(ValueError,'bound copied asset'):adapter.figure(figure)

    def test_actual_pdf_page_cap_and_paper_size_boundaries(self):
        from pypdf import PdfWriter
        directory=ARTIFACTS/'page-cap';directory.mkdir()
        for count in (0,1,40,41):
            writer=PdfWriter()
            for _ in range(count):writer.add_blank_page(width=595.2756,height=841.8898)
            path=directory/(str(count)+'.pdf')
            with path.open('xb') as stream:writer.write(stream)
            if 1<=count<=40:self.assertEqual(pdf.page_gate(path),count)
            else:
                with self.assertRaisesRegex(ValueError,'1..40'):pdf.page_gate(path)
        writer=PdfWriter();writer.add_blank_page(width=612,height=792)
        path=directory/'letter.pdf'
        with path.open('xb') as stream:writer.write(stream)
        with self.assertRaisesRegex(ValueError,'Non-A4'):pdf.page_gate(path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--artifacts-dir',type=Path,required=True)
    args,remaining=parser.parse_known_args();ARTIFACTS=args.artifacts_dir.resolve();ARTIFACTS.mkdir(parents=True,exist_ok=False)
    unittest.main(argv=[__file__,*remaining],verbosity=2)
