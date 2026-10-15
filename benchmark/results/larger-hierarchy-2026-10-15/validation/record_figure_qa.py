#!/usr/bin/env python3
"""Archive already-performed visual review and independently recheck render hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--panels', type=int, required=True)
    parser.add_argument('--notes', required=True)
    args = parser.parse_args()
    folder = args.directory.resolve(strict=True)
    receipt, prose = folder / 'QA.json', folder / 'QA.md'
    if receipt.exists() or prose.exists():
        raise ValueError('refusing to overwrite figure QA')
    provenance_path = folder / 'provenance.json'
    provenance = json.loads(provenance_path.read_text())
    inputs = provenance.get('input_sha256', provenance.get('source_sha256'))
    for path, digest in inputs.items():
        if sha(path) != digest:
            raise ValueError('render input changed: ' + path)
    for name, digest in provenance['output_sha256'].items():
        if sha(folder / name) != digest:
            raise ValueError('render output changed: ' + name)
    images = []
    for name in provenance['output_sha256']:
        if not name.endswith('.png'):
            continue
        raw = (folder / name).read_bytes()
        if raw[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError('wrong PNG signature')
        width, height = struct.unpack('>II', raw[16:24])
        images.append(dict(file=name, width=width, height=height, sha256=sha(folder / name)))
    if not images:
        raise ValueError('no reviewed PNGs')
    value = dict(schema='larger_study_figure_visual_qa_v1', validation='pass',
                 reviewer='multigraph_design', original_resolution_inspection=True,
                 panels_inspected=args.panels, pngs=images, notes=args.notes,
                 provenance_sha256=sha(provenance_path), qa_script_sha256=sha(__file__),
                 declared_inputs_rehashed=len(inputs), declared_outputs_rehashed=len(provenance['output_sha256']),
                 svg_pdf_generated_and_hashed=True, svg_pdf_separately_rasterized=False)
    with receipt.open('x') as stream:
        json.dump(value, stream, indent=2); stream.write('\n')
    with prose.open('x') as stream:
        stream.write('# Figure visual QA\n\nPASS. `multigraph_design` inspected all ' + str(len(images)) +
                     ' PNGs at original resolution and all ' + str(args.panels) + ' panels. ' + args.notes +
                     '\n\nAll declared source/input and output hashes were independently rechecked. '
                     'SVG/PDF counterparts were generated and hashed, not separately rasterized. '
                     'The renderer\'s pending-review provenance is preserved; this later [QA receipt](QA.json) records visual approval.\n')
    print(json.dumps(dict(validation='pass', pngs=len(images), panels=args.panels, directory=str(folder))))


if __name__ == '__main__':
    main()
