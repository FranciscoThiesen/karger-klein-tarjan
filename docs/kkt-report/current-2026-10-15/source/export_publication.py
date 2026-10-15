#!/usr/bin/env python3
"""Copy and check the report/evidence link closure; never replay native proof.

Source preparation only. Run only after the final accepted link manifest exists.
Requires Python >=3.9 and the reviewed pack_publication.py narrow Markdown parser.
"""
import argparse
import datetime
import hashlib
from html.parser import HTMLParser
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


def require(ok,message):
    if not ok: raise ValueError(message)
def sha(data): return hashlib.sha256(data).hexdigest()
def digest(path): return sha(Path(path).read_bytes())
def canonical(path,exists=True):
    unresolved=Path(os.path.abspath(path)); resolved=unresolved.resolve(strict=exists)
    require(unresolved==resolved,'symlink/noncanonical path: '+str(path))
    return resolved
def read_json(path):
    def unique(pairs):
        value={}
        for key,item in pairs:
            require(key not in value,'duplicate JSON key'); value[key]=item
        return value
    return json.loads(Path(path).read_text(),object_pairs_hook=unique)
def relative(name):
    path=Path(name)
    require(not path.is_absolute() and path.parts and all(p not in ('.','..') for p in path.parts),
            'unsafe repository relative path')
    return path.as_posix()


def excluded(name,data=None):
    parts=Path(name).parts; base=Path(name).name.lower()
    if any(p in ('.git','.build','bin','__pycache__') for p in parts): return 'native/build/private tree'
    if any('power-audit' in p.lower() for p in parts) or base in ('pmset.log','pmset-full.log'):
        return 'private power log'
    if Path(name).suffix.lower() in ('.o','.a','.so','.dylib','.dll','.exe','.pyc'):
        return 'compiled binary'
    magic=(b'\x7fELF',b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xce\xfa\xed\xfe',
           b'\xfe\xed\xfa\xce',b'\xca\xfe\xba\xbe',b'\xbe\xba\xfe\xca',b'!<arch>\n',b'MZ')
    if data is not None and data.startswith(magic): return 'native binary magic'
    return None


class ResourceLinks(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.style=False
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        require(tag!='base','HTML base changes relative-link meaning')
        require('srcset' not in values,'srcset needs a separately reviewed parser')
        if 'href' in values: self.links.append((values['href'],'link' if tag=='a' else 'asset'))
        for key in ('src','poster','data','xlink:href'):
            if key in values:self.links.append((values[key],'asset'))
        if 'style' in values:self.css(values['style'])
        if tag=='style':self.style=True
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)
    def handle_endtag(self,tag):
        if tag=='style':self.style=False
    def handle_data(self,data):
        if self.style:self.css(data)
    def css(self,text):
        require(not re.search(r'@import\b',text,re.I),'CSS import unsupported')
        for value in re.findall(r'url\(\s*([^)]*?)\s*\)',text,re.I):
            self.links.append((value.strip('"\''),'asset'))


def links(name,data,markdown):
    suffix=Path(name).suffix.lower()
    if suffix=='.md':
        text=data.decode('utf-8');found=markdown(text)
        # Parent parser intentionally labels all destinations alike. Preserve
        # its validation, but distinguish this report's inline/full-reference
        # images so a remote image cannot masquerade as a remote citation.
        images=set(re.findall(r'!\[[^\]\n]*\]\(([^\n)]+)\)',text))
        definitions=dict(re.findall(r'(?m)^\[([^\]\n]+)\]:\s*(\S+)\s*$',text))
        for label in re.findall(r'!\[[^\]\n]*\]\[([^\]\n]+)\]',text):
            require(label in definitions,'undefined image reference');images.add(definitions[label])
        return [(value,'asset' if value in images else kind) for value,kind in found]
    if suffix in ('.html','.htm'):
        parser=ResourceLinks();parser.feed(data.decode('utf-8'));parser.close();return parser.links
    if suffix=='.css':
        parser=ResourceLinks();parser.css(data.decode('utf-8'));return parser.links
    return []  # JSON/CSV/source paths are evidence content, never dependency traversal.


def target(root,document,raw,kind):
    raw=raw.strip()
    if raw.startswith('<') and raw.endswith('>'):raw=raw[1:-1]
    parsed=urlsplit(raw)
    if parsed.scheme in ('http','https','mailto'):
        require(kind not in ('asset','src'),'remote resource breaks offline publication closure')
        return None
    if parsed.scheme=='data':
        require(kind in ('asset','src') and raw.startswith(('data:image/','data:font/')),'unsupported data resource')
        return None
    require(not parsed.scheme and not parsed.netloc and not parsed.query,'unsupported link: '+raw)
    path=unquote(parsed.path)
    require(not path.startswith('/') and '\\' not in path,'absolute local link: '+raw)
    if not path:return None
    resolved=canonical(root/Path(document).parent/path)
    require(resolved.is_relative_to(root),'local link escapes publication root: '+raw)
    return resolved.relative_to(root).as_posix()


def run(args,record):
    root=canonical(args.repo_root); destination=canonical(args.destination,False)
    require(not destination.exists(),'refusing existing export destination')
    require(not destination.is_relative_to(root) and not root.is_relative_to(destination),
            'export must be outside and must not contain the original repository')
    manifest=canonical(args.links_receipt); helper=canonical(args.link_helper)
    require(manifest.is_relative_to(root) and helper.is_relative_to(root),'receipt/helper outside repository')
    pins={str(manifest):digest(manifest),str(helper):digest(helper),str(Path(__file__).resolve()):digest(__file__)}
    accepted=read_json(manifest)
    require(accepted['schema']=='kkt_publication_links_v1' and accepted['validation']=='pass' and
            accepted['file_link_completeness'] is True and accepted['external_local_links']==0 and
            canonical(accepted['repo_root'])==root,'unaccepted final publication link receipt')
    require(digest(manifest)==pins[str(manifest)],'manifest changed while reading')
    spec=importlib.util.spec_from_file_location('_export_narrow_link_parser',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    require(digest(helper)==pins[str(helper)],'link parser changed during import')
    declared={}
    for inventory in ('verified_file_sha256','explicitly_included_sha256'):
        for name,value in accepted[inventory].items():
            name=relative(name)
            require(name not in declared or declared[name]==value,'conflicting manifest binding')
            declared[name]=value
    for path in (manifest,helper,*map(canonical,args.include)):
        require(path.is_relative_to(root) and path.is_file(),'explicit file outside repository')
        name=path.relative_to(root).as_posix(); value=digest(path)
        require(name not in declared or declared[name]==value,'explicit file conflicts with accepted receipt')
        declared[name]=value
    # Deliberately bounded by the accepted main-report inventory. Historical
    # README links do not expand this into a native archive reconstruction.
    primary=set()
    for path in map(canonical,args.document):
        require(path.is_relative_to(root) and path.suffix.lower() in ('.md','.html','.htm'),
                'primary document must be repository Markdown/HTML')
        name=path.relative_to(root).as_posix()
        require(name in declared,'primary document missing from accepted/explicit inventory')
        primary.add(name)
    require(any(Path(p).suffix.lower()=='.md' for p in primary) and
            any(Path(p).suffix.lower() in ('.html','.htm') for p in primary),
            'declare both final Markdown and HTML as primary documents')
    payload={}; omitted=[]
    for name,value in declared.items():
        path=canonical(root/name);require(path.is_file(),'expected regular publication file')
        data=path.read_bytes();require(sha(data)==value,'accepted file changed: '+name)
        reason=excluded(name,data)
        if reason:
            omitted.append(dict(path=name,reason=reason));continue
        payload[name]=value
    require(primary.issubset(payload),'primary document excluded')

    def inspect(base):
        found=[]; limitations=[]
        for name,value in payload.items():
            path=canonical(base/name);require(digest(path)==value,'publication file changed')
            try:references=links(name,path.read_bytes(),module.markdown_links)
            except (ValueError,UnicodeError) as error:
                require(name not in primary,'primary document parse failed: '+str(error))
                limitations.append(dict(document=name,error=str(error)));continue
            for raw,kind in references:
                try:
                    other=target(base,name,raw,kind)
                    if other is None:continue
                    included=other in payload or any(p.startswith(other+'/') for p in payload)
                    require(included,'target outside declared export inventory: '+other)
                    found.append(dict(document=name,href=raw,target=other))
                except (ValueError,OSError) as error:
                    require(name not in primary,'primary link unresolved: '+name+' '+raw+' '+str(error))
                    # Keep stable reasons independent of original/relocated root.
                    limitations.append(dict(document=name,href=raw,
                        reason='Supplementary link unsupported, absolute, missing, excluded or outside accepted export inventory'))
        return found,limitations

    original_links,original_limits=inspect(root)
    for path,value in pins.items():require(digest(path)==value,'input/parser changed')
    destination.mkdir(parents=True)
    record['output_started']=True
    for name,value in payload.items():
        source=canonical(root/name);require(digest(source)==value,'source changed before copy')
        output=destination/name;output.parent.mkdir(parents=True,exist_ok=True)
        with output.open('xb') as stream:stream.write(source.read_bytes())
        require(digest(output)==value,'copy differs')
    # Resolve again only against the relocated tree. Historical unbundled links
    # are explicit limitations, never silently declared portable.
    relocated,limitations=inspect(destination)
    require(relocated==original_links and limitations==original_limits,'relocated link identities differ')
    for name,value in payload.items():require(digest(root/name)==value,'source changed during export')
    for path,value in pins.items():require(digest(path)==value,'manifest/parser changed during export')
    record.update(validation='pass',repo_root=str(root),destination=str(destination),input_sha256=pins,
                  accepted_links_receipt=str(manifest),files_sha256=payload,primary_documents=sorted(primary),
                  relocated_local_links=relocated,excluded_declared_files=omitted,
                  file_count=len(payload),local_link_count=len(relocated),primary_absolute_local_links=0,
                  primary_document_link_completeness=True,supplementary_link_limitations=limitations,
                  bytes_preserved=True,raw_json_machine_paths_preserved=True,
                  native_proof_portability=False,browser_validation=False,
                  limitations='Publication file closure only. Does not traverse JSON/source machine paths, replay native proofs, validate fragments/dynamic JavaScript or substitute for browser QA.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo-root','links-receipt','link-helper','destination','receipt'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--include',type=Path,action='append',default=[])
    parser.add_argument('--document',type=Path,action='append',required=True)
    parser.add_argument('--released',action='store_true');args=parser.parse_args()
    require(args.released,'final-manifest publication release required')
    receipt=canonical(args.receipt,False);require(not receipt.exists() and receipt.parent.is_dir(),'receipt must be exclusive with existing parent')
    record=dict(schema='kkt_publication_export_v1',validation='running',invocation=sys.argv,
                source_sha256=digest(__file__),native_solver_execution=False,
                created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        run(args,record)
        # The manifest is publication metadata, not an additional original
        # evidence file. It intentionally does not attempt to hash itself.
        manifest=canonical(args.destination)/'EXPORT_MANIFEST.json'
        require(not manifest.exists(),'export manifest name collision')
        with manifest.open('x') as stream:json.dump(record,stream,indent=2,allow_nan=False);stream.write('\n')
    except BaseException as error:record.update(validation='failed',error=repr(error));raise
    finally:
        with receipt.open('x') as stream:json.dump(record,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:record[k] for k in ('validation','file_count','local_link_count','native_proof_portability')}))


if __name__=='__main__':main()
