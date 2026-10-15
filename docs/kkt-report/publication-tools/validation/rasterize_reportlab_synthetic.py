#!/usr/bin/env python3
"""Bounded synthetic PDF rasterization only; no browser or native solver."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
PDF=HERE/'reportlab-fixtures-attempt01/positive/pdf/report.pdf'
EXPECTED='79ec8a386ea1e233ee2d6264009bae17c7130b2671dafec7b07f627eb15b9059'
OUTPUT=HERE/'reportlab-raster-attempt01'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if sha(PDF)!=EXPECTED:raise ValueError('Synthetic PDF changed before rasterization')
    OUTPUT.mkdir(exist_ok=False)
    record={'schema':'reportlab_synthetic_raster_v1','validation':'running','source_sha256':sha(Path(__file__).resolve()),
            'native_solver_execution':False,'input_pdf':str(PDF),'input_sha256':EXPECTED,
            'command':['/usr/local/bin/pdftoppm','-r','120','-png',str(PDF),str(OUTPUT/'page')]}
    try:
        result=subprocess.run(record['command'],capture_output=True,text=True,timeout=45)
        record.update(exit_status=result.returncode,stdout=result.stdout,stderr=result.stderr)
        if result.returncode!=0:raise ValueError('Rasterization failed')
        pages=sorted(OUTPUT.glob('page-*.png'))
        if len(pages)!=1:raise ValueError('Synthetic one-page fixture produced wrong raster count')
        if sha(PDF)!=EXPECTED:raise ValueError('Synthetic PDF changed during rasterization')
        record.update(validation='pass',output_sha256={path.name:sha(path) for path in pages},visual_qa='pending')
    except BaseException as error:record.update(validation='failed',error=repr(error));raise
    finally:
        with (OUTPUT/'receipt.json').open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps({'validation':'pass','pages':len(pages)}))


if __name__=='__main__':main()
