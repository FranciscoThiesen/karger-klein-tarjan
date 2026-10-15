#!/usr/bin/env python3
"""Rasterize every page of a hash-bound final ReportLab edition for visual QA.

Run only after a separate publication release, through the nonnative archival
guard. Produces page images and a receipt, never a visual-acceptance claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def require(condition, message):
    if not condition: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    directory = args.pdf_dir.resolve(strict=True)
    pdf, metadata = directory/'report.pdf', directory/'pdf_metadata.json'
    before = {str(path):sha(path) for path in (pdf, metadata, Path(__file__).resolve())}
    info = json.loads(metadata.read_text())
    require(info['schema']=='kkt_reportlab_pdf_v1' and info['validation']=='rendered_pending_visual_qa',
            'Expected completed ReportLab output')
    require(info['pdf_sha256']==before[str(pdf)] and type(info['pdf_pages']) is int and
            1 <= info['pdf_pages'] <= 40, 'PDF hash/page-count gate failed')
    from pypdf import PdfReader
    pages = PdfReader(pdf).pages
    require(len(pages)==info['pdf_pages'], 'Actual PDF page count changed')
    require(all(abs(float(page.mediabox.width)-595.2756)<.1 and
                abs(float(page.mediabox.height)-841.8898)<.1 for page in pages), 'Expected A4 pages')
    output = args.output_dir.resolve(); output.mkdir(parents=True, exist_ok=False)
    command = ['/usr/local/bin/pdftoppm', '-r', '120', '-png', str(pdf), str(output/'page')]
    record = dict(schema='kkt_final_edition_raster_v1', validation='running', input_sha256=before,
                  command=command, timeout_seconds=120, native_solver_execution=False,
                  expected_pages=len(pages), visual_qa='pending: inspect every page')
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        record.update(exit_status=result.returncode, stdout=result.stdout, stderr=result.stderr)
        require(result.returncode==0, 'Poppler failed; preserve partial raster attempt')
        images = list(output.glob('page-*.png'))
        numbers = []
        for image in images:
            match = re.fullmatch(r'page-([0-9]+)\.png', image.name)
            require(match is not None and image.is_file(), 'Unexpected page image')
            numbers.append(int(match.group(1)))
        require(len(images)==len(pages) and sorted(numbers)==list(range(1,len(pages)+1)),
                'Missing, duplicate or unexpected rasterized page')
        for path,digest in before.items(): require(sha(path)==digest, 'Input changed during rasterization')
        record.update(validation='pass', pages=len(images),
                      output_sha256={image.name:sha(image) for image in sorted(images)})
    except BaseException as error:
        record.update(validation='failed', error=repr(error)); raise
    finally:
        with (output/'receipt.json').open('x') as stream:
            json.dump(record,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(validation='pass', pages=len(images), visual_qa='pending')))


if __name__=='__main__': main()
