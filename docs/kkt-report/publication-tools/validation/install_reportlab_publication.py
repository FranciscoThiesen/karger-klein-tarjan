#!/usr/bin/env python3
"""Exclusive byte-preserving install of reviewed publication sources only."""
import hashlib
import json
from pathlib import Path

SOURCE=Path('/tmp/kkt-current-report-publish-prep').resolve()
DEST=Path('/Users/random_person/Desktop/kkt-eighth-sampling/docs/kkt-report/publication-tools').resolve()
FILES={name:name for name in ('build_reportlab_pdf.py','test_reportlab_pdf.py','REPORTLAB_FALLBACK.md',
    'INDEPENDENT_REPORTLAB_SOURCE_REVIEW.md','FINAL_INTEGRATION_CHECKLIST.md','build_current_report.py',
    'INDEPENDENT_RENDERER_ADDENDUM_REVIEW.md','INDEPENDENT_PORTABILITY_REVIEW.md')}
FILES['README.md']='CURRENT_HTML_RENDERER_PREPARATION.md'
for name in ('build_reportlab_pdf.py','test_reportlab_pdf.py','REPORTLAB_FALLBACK.md'):
    relative='before-structural-text-and-numbering-review/'+name;FILES[relative]=relative
PINS={'build_reportlab_pdf.py':'b670b09cfef6e903ec3f739f52fe91c8e8da5446f124b27e8c4e37f70283ad73',
      'test_reportlab_pdf.py':'951309bd801fc71dbf33c121620683e9740a8a2f4e0607e48b3c0d5748f9931f',
      'REPORTLAB_FALLBACK.md':'fb0cc38352bdcc081b2be69f3023da2f739cbdd93376a1c8297a21a1d1184566'}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt=DEST/'REPORTLAB_INSTALLATION.json'
    if receipt.exists() or any((DEST/path).exists() for path in FILES.values()):
        raise ValueError('Refusing an existing installation target')
    before={name:sha(SOURCE/name) for name in FILES}
    if any(before[name]!=value for name,value in PINS.items()):raise ValueError('Reviewed source hash changed')
    record={'schema':'reportlab_publication_source_install_v1','validation':'running',
            'source_root':str(SOURCE),'destination':str(DEST),'native_solver_execution':False,
            'installer_sha256':sha(Path(__file__).resolve()),'files':[]}
    try:
        for source,destination in FILES.items():
            path=DEST/destination;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write((SOURCE/source).read_bytes())
            if sha(path)!=before[source]:raise ValueError('Copied source differs: '+source)
            record['files'].append({'source':source,'destination':destination,'sha256':before[source]})
        if before!={name:sha(SOURCE/name) for name in FILES}:raise ValueError('Preparation source changed during install')
        record['validation']='pass'
    except BaseException as error:record.update(validation='failed',error=repr(error));raise
    finally:
        with receipt.open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
    print(json.dumps({'validation':'pass','copied_files':len(FILES),'receipt':str(receipt)}))


if __name__=='__main__':main()
