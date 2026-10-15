#!/usr/bin/env python3
"""Pack one historical study, or check this report's narrow local-link syntax.

Prepared source-only. No operation is permitted without --released after the
quiet campaign ends. Git commands are local reads; no solver is invoked.
"""
import argparse
import datetime
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

STUDY = 'benchmark/results/packed-sampling-2026-10-15'
HELPER = 'kkt/experimental_packed_sampling.hpp'
IMPLEMENTATION = '4bb476edd38420c2d0fe6aff2f37028cbece7e9f'
ARCHIVE = 'docs/kkt-report/source-archives/packed-sampling-4bb476e'
OLD_LINK = b'../../../kkt/experimental_packed_sampling.hpp'
NEW_LINK = b'../../../docs/kkt-report/source-archives/packed-sampling-4bb476e/experimental_packed_sampling.hpp'


def require(value, message):
    if not value: raise ValueError(message)


def sha(data): return hashlib.sha256(data).hexdigest()
def file_sha(path): return sha(Path(path).read_bytes())
def blob_sha(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def relative(value):
    path=PurePosixPath(value)
    require(not path.is_absolute() and path.parts and all(p not in ('.','..') for p in path.parts), 'unsafe relative path')
    return path.as_posix()


def local(root, name, exists=True):
    path=root/relative(name)
    require(path.resolve(strict=exists)==path, 'symlink or noncanonical publication path: '+str(path))
    require(path.is_relative_to(root), 'path outside declared root')
    return path


def read_json(path):
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'duplicate JSON key');result[key]=value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs)


def write_json(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False)


def git(root,args,record):
    command=['/usr/bin/git','--no-optional-locks','--literal-pathspecs','-C',str(root),
             '-c','core.fsmonitor=false',*args]
    env={key:value for key,value in os.environ.items() if not key.startswith('GIT_')}
    completed=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=env)
    record.setdefault('git_reads',[]).append(dict(command=command,exit_status=completed.returncode,
        stdout_sha256=sha(completed.stdout),stderr=completed.stderr.decode(errors='replace')))
    require(completed.returncode==0,'local Git read failed: '+repr(command))
    return completed.stdout


def repository(root,record):
    require(Path(git(root,['rev-parse','--show-toplevel'],record).decode().strip()).resolve()==root,'wrong Git root')
    require(git(root,['rev-parse','--show-object-format'],record).strip()==b'sha1','only the declared SHA-1 repository is supported')
    return git(root,['rev-parse','HEAD'],record).decode().strip()


def tree(root,commit,paths,record):
    require(re.fullmatch('[0-9a-f]{40}',commit) is not None,'use an explicit full source commit')
    raw=git(root,['ls-tree','-r','-z','--full-tree',commit,'--',*paths],record)
    rows={}
    for item in raw.split(b'\0'):
        if not item:continue
        metadata,name=item.split(b'\t',1);mode,kind,oid=metadata.decode().split()
        name=relative(name.decode())
        require(name not in rows and kind=='blob' and mode in ('100644','100755'),'unsupported tree entry')
        rows[name]=(mode,oid)
    return rows


def checked_bytes(root,name,oid):
    data=local(root,name).read_bytes()
    require(blob_sha(data)==oid,'tracked source differs from pinned commit: '+name)
    return data


def pack(args,record):
    source=args.source_root.resolve(strict=True);target=args.repo_root.resolve(strict=True)
    require(source!=target,'source and publication worktrees must differ')
    record.update(source_root=str(source),repo_root=str(target),source_commit=args.source_commit,
                  implementation_commit=IMPLEMENTATION,readme_only_content_change=True,
                  native_artifacts_copied=False,native_proof_portability=False)
    require(repository(source,record)==args.source_commit,'source HEAD does not match the declared evidence commit')
    record['target_head']=repository(target,record)
    study=local(target,STUDY,False);archive=local(target,ARCHIVE,False)
    require(not study.exists() and not archive.exists(),'refusing existing study or source archive')
    require(not git(target,['ls-files','--stage','-z','--',STUDY,ARCHIVE],record),
            'destination contains tracked paths, including possible working-tree deletions')
    require(args.receipt.resolve()==archive/'COPY_RECEIPT.json','pack receipt must be the fixed new archive receipt')
    entries=tree(source,args.source_commit,[STUDY,HELPER],record)
    require(HELPER in entries and STUDY+'/README.md' in entries,'missing tracked helper or study README')
    require(all(name==HELPER or name.startswith(STUDY+'/') for name in entries),'extra source entry')
    old_helper=tree(source,IMPLEMENTATION,[HELPER],record)
    require(old_helper=={HELPER:entries[HELPER]},'helper differs from tested implementation commit')
    # Only tracked commit entries are copied. No recursive filesystem copy.
    payload={name:checked_bytes(source,name,oid) for name,(_,oid) in entries.items()}
    require(payload[STUDY+'/README.md'].count(OLD_LINK)==1,'expected exactly one copied README helper link')
    require(all(not name.endswith(('.o','.a','.so','.dylib')) for name in payload),'unexpected compiled artifact in study')
    magic=(b'\x7fELF',b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xce\xfa\xed\xfe',b'\xfe\xed\xfa\xce',b'\xca\xfe\xba\xbe')
    require(all(not data.startswith(magic) for data in payload.values()),'unexpected native executable artifact')
    archive.mkdir(parents=True);record['output_started']=True;study.mkdir(parents=True)
    record['files']=[]
    for name,(mode,oid) in entries.items():
        data=payload[name]
        destination=ARCHIVE+'/experimental_packed_sampling.hpp' if name==HELPER else name
        copied=data.replace(OLD_LINK,NEW_LINK) if name==STUDY+'/README.md' else data
        path=local(target,destination,False);path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(copied)
        path.chmod(0o755 if mode=='100755' else 0o644)
        record['files'].append(dict(source=name,destination=destination,git_mode=mode,source_blob=oid,
            original_sha256=sha(data),copied_sha256=sha(copied),readme_link_rewritten=name==STUDY+'/README.md'))
    require(repository(source,record)==args.source_commit,'source HEAD changed during copy')
    require(repository(target,record)==record['target_head'],'destination HEAD changed during copy')
    require(not git(target,['ls-files','--stage','-z','--',STUDY,ARCHIVE],record),
            'destination paths were staged during copy')
    for row in record['files']:
        require(file_sha(local(source,row['source']))==row['original_sha256'],'source changed during copy')
        require(file_sha(local(target,row['destination']))==row['copied_sha256'],'copied bytes changed')
    require(sum(row['readme_link_rewritten'] for row in record['files'])==1,'wrong changed-file count')
    record.update(validation='pass',copied_study_files=len(entries)-1,archived_helper_files=1,
        readme_link_change={'before':OLD_LINK.decode(),'after':NEW_LINK.decode()},
        historical_files_modified=False,
        limitation='Copied raw proof retains original-machine paths and binary dependencies; this is a publication evidence copy, not a portable rebuild.')


def index(root,record):
    result={}
    raw=git(root,['ls-files','--stage','-z'],record)
    for item in raw.split(b'\0'):
        if not item:continue
        metadata,name=item.split(b'\t',1);mode,oid,stage=metadata.decode().split();name=relative(name.decode())
        require(stage=='0' and name not in result,'unmerged/duplicate index entry')
        result[name]=(mode,oid)
    return result,sha(raw)


def add_explicit(root,files,path,digest=None):
    unresolved=Path(os.path.abspath(path));path=unresolved.resolve(strict=True)
    require(path==unresolved,'explicit inclusion is a symlink or has a symlink ancestor')
    require(path.is_relative_to(root) and path.is_file(),'explicit file outside publication root or not a file')
    name=path.relative_to(root).as_posix();path=local(root,name)
    actual=file_sha(path);require(digest is None or actual==digest,'changed explicitly included file')
    require(name not in files or files[name]==actual,'conflicting explicit inclusion')
    files[name]=actual


def copy_receipt(root,path,files):
    receipt_hash=file_sha(path);value=read_json(path)
    require(file_sha(path)==receipt_hash,'copy receipt changed while reading')
    require(value['schema']=='kkt_publication_pack_v1' and value['validation']=='pass','incomplete publication copy')
    require(Path(value['repo_root']).resolve()==root and value['implementation_commit']==IMPLEMENTATION,'wrong copy destination/origin')
    require(value['readme_link_change']=={'before':OLD_LINK.decode(),'after':NEW_LINK.decode()},'wrong copied README rewrite')
    rows=value['files'];require(len(rows)==value['copied_study_files']+1 and value['archived_helper_files']==1,'incomplete copy inventory')
    names=set();changed=[]
    for row in rows:
        name=relative(row['destination']);require(name not in names,'duplicate copied file');names.add(name)
        require(type(row['readme_link_rewritten']) is bool,'invalid copy change flag')
        if row['source']==HELPER:
            require(name==ARCHIVE+'/experimental_packed_sampling.hpp' and row['readme_link_rewritten'] is False,'wrong helper archive')
        else:require(name==row['source'] and name.startswith(STUDY+'/'),'copy changed an unexpected path')
        data=local(root,name).read_bytes()
        add_explicit(root,files,root/name,row['copied_sha256'])
        if row['readme_link_rewritten']:
            require(name==STUDY+'/README.md' and data.count(NEW_LINK)==1 and OLD_LINK not in data,'unexpected README change')
            original=data.replace(NEW_LINK,OLD_LINK);changed.append(name)
        else:original=data
        require(sha(original)==row['original_sha256'] and blob_sha(original)==row['source_blob'],'copy does not reconstruct original bytes')
    require(changed==[STUDY+'/README.md'] and ARCHIVE+'/experimental_packed_sampling.hpp' in names,'missing helper or README proof')
    add_explicit(root,files,path,receipt_hash)


def render_receipt(root,path,files):
    receipt_hash=file_sha(path);value=read_json(path)
    require(file_sha(path)==receipt_hash,'renderer receipt changed while reading')
    require(value['schema']=='kkt_current_report_render_v1' and value['validation']=='rendered_pending_visual_qa','incomplete report render')
    require(value['external_local_dependencies']==[],'final renderer retained external local evidence')
    for name,digest in value['output_sha256'].items():
        name=relative(name);add_explicit(root,files,Path(path).resolve().parent/name,digest)
    add_explicit(root,files,path,receipt_hash)


def markdown_links(text):
    # This report uses ordinary inline destinations and one-line definitions.
    # Fenced examples are not evidence links; other Markdown constructs must be
    # reviewed explicitly instead of pretending this is a general parser.
    lines=[];fence=None
    for line in text.splitlines():
        match=re.match(r'^\s*(`{3,}|~{3,})',line)
        if match:
            marker=match.group(1)
            if fence is None:fence=marker
            elif marker[0]==fence[0] and len(marker)>=len(fence):fence=None
            continue
        if fence is None:lines.append(line)
    require(fence is None,'unclosed Markdown code fence')
    body='\n'.join(lines)
    body=re.sub(r'`+[^`\n]*`+','',body)
    require(not re.search(r'<\s*(?:a|img)\b',body,re.I),'raw HTML evidence links need the HTML verifier')
    definitions={}
    for label,destination in re.findall(r'(?m)^\[([^\]\n]+)\]:\s*(\S+)\s*$',body):
        require(label not in definitions,'duplicate reference definition');definitions[label]=destination
    inline=re.findall(r'!?\[[^\]\n]*\]\(([^\n)]+)\)',body)
    residual=re.sub(r'!?\[[^\]\n]*\]\([^\n)]+\)','',body)
    require('](' not in residual,'unsupported inline Markdown link')
    for label in re.findall(r'!?\[[^\]\n]*\]\[([^\]\n]+)\]',body):
        require(label in definitions,'missing Markdown reference definition')
    return [(value,'markdown') for value in [*inline,*definitions.values()]]


class HTMLLinks(HTMLParser):
    def __init__(self):super().__init__();self.links=[]
    def handle_starttag(self,tag,attrs):
        values=dict(attrs)
        if tag in ('a','link') and 'href' in values:self.links.append((values['href'],'href'))
        if tag in ('img','script','iframe') and 'src' in values:self.links.append((values['src'],'src'))


def directory_inventory(path):
    result=[]
    for entry in sorted(path.rglob('*')):
        require(not entry.is_symlink(),'symlink in linked directory')
        require(entry.is_file() or entry.is_dir(),'unsupported linked-directory entry')
        result.append({'name':entry.relative_to(path).as_posix(),
                       'kind':'file' if entry.is_file() else 'directory'})
    return result


def verify(args,record):
    root=args.repo_root.resolve(strict=True);record['repo_root']=str(root)
    head=repository(root,record);tracked,index_hash=index(root,record);explicit={};bindings={}
    for path in args.copy_receipt:copy_receipt(root,path,explicit)
    for path in args.render_metadata:render_receipt(root,path,explicit)
    for path in args.included:add_explicit(root,explicit,path)
    def accepted(path):
        path=Path(path).resolve(strict=True)
        require(path.is_relative_to(root),'external local link forbidden: '+str(path))
        name=path.relative_to(root).as_posix();path=local(root,name)
        data=path.read_bytes();digest=sha(data)
        if name in explicit:require(explicit[name]==digest,'included file changed')
        else:
            require(name in tracked and tracked[name][0] in ('100644','100755'),'linked file is neither tracked nor explicitly included: '+name)
            require(blob_sha(data)==tracked[name][1],'linked tracked file differs from the index; stage it or explicitly include current bytes: '+name)
        require(name not in bindings or bindings[name]==digest,'linked file changed while checking');bindings[name]=digest
        return name
    links=[];directories={}
    for document in args.document:
        unresolved=Path(os.path.abspath(document));document=unresolved.resolve(strict=True)
        require(document==unresolved,'document is a symlink or has a symlink ancestor')
        name=accepted(document);data=document.read_bytes()
        require(sha(data)==bindings[name],'publication document changed while reading');text=data.decode('utf-8')
        if document.suffix.lower()=='.md':found=markdown_links(text)
        elif document.suffix.lower()=='.html':
            parser=HTMLLinks();parser.feed(text);parser.close();found=parser.links
        else:raise ValueError('document must be this report Markdown or HTML')
        require(found,'no links found in declared publication document')
        for raw,kind in found:
            raw=raw.strip()
            if raw.startswith('<') and raw.endswith('>'):raw=raw[1:-1]
            parsed=urlsplit(raw)
            if parsed.scheme in ('https','http','mailto'):continue
            if parsed.scheme=='data':
                require(kind=='src' and raw.startswith(('data:image/png;base64,','data:image/svg+xml;base64,')),'unexpected data link');continue
            require(not parsed.scheme and not parsed.netloc and not parsed.query,'unsupported or external local link: '+raw)
            if not parsed.path:continue  # Same-document fragments get renderer/browser QA.
            unresolved=document.parent/unquote(parsed.path)
            target=unresolved.resolve(strict=True)
            require(target==Path(os.path.abspath(unresolved)),'linked symlink would need a separate publication policy')
            require(target.is_relative_to(root),'external local evidence forbidden: '+str(target))
            if target.is_dir():
                inventory=directory_inventory(target)
                key=target.relative_to(root).as_posix()
                require(key not in directories or directories[key]==inventory,'linked directory changed between references')
                directories[key]=inventory
                members=[target/entry['name'] for entry in inventory if entry['kind']=='file']
                require(members,'empty linked evidence directory')
                for member in members:accepted(member)
                links.append(dict(document=str(document),href=raw,directory_members=len(members)))
            else:links.append(dict(document=str(document),href=raw,file=accepted(target)))
    require(repository(root,record)==head and index(root,record)[1]==index_hash,'repository/index changed while checking links')
    for name,digest in {**explicit,**bindings}.items():require(file_sha(local(root,name))==digest,'publication file changed')
    for name,inventory in directories.items():
        require(directory_inventory(local(root,name))==inventory,'linked directory membership changed')
    record.update(validation='pass',repo_head=head,index_inventory_sha256=index_hash,local_links=links,
                  verified_file_sha256=bindings,explicitly_included_sha256=explicit,
                  linked_directory_inventories=directories,
                  external_local_links=0,file_link_completeness=True,
                  fragment_and_browser_validation='separate outstanding acceptance gate',
                  native_proof_portability=False,
                  limitation='Verifies publication file inclusion and bytes, not portable native rebuilds or original-machine proof replay.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='operation',required=True)
    packing=sub.add_parser('pack-packed');packing.add_argument('--source-root',type=Path,required=True)
    packing.add_argument('--source-commit',required=True)
    checking=sub.add_parser('verify-links');checking.add_argument('--document',type=Path,action='append',required=True)
    for name in ('copy-receipt','render-metadata','included'):checking.add_argument('--'+name,type=Path,action='append',default=[])
    for command in (packing,checking):
        command.add_argument('--repo-root',type=Path,required=True);command.add_argument('--receipt',type=Path,required=True)
        command.add_argument('--released',action='store_true')
    args=parser.parse_args();require(args.released,'explicit post-timing publication release required')
    receipt=args.receipt.resolve();require(not receipt.exists(),'refusing existing receipt')
    if args.operation=='verify-links':require(receipt.parent.is_dir(),'create the exclusive review directory first')
    record=dict(schema='kkt_publication_pack_v1' if args.operation=='pack-packed' else 'kkt_publication_links_v1',
                validation='running',invocation=sys.argv,source_sha256=file_sha(__file__),native_solver_execution=False,
                created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    try:
        (pack if args.operation=='pack-packed' else verify)(args,record)
        require(file_sha(__file__)==record['source_sha256'],'publication script changed')
    except BaseException as error:record.update(validation='failed',error=repr(error));raise
    finally:
        # Early refusal creates no target tree; its outer guard still preserves
        # the error. Once a copy/verification starts, never overwrite a receipt.
        if args.operation=='verify-links' or record.get('output_started'):
            write_json(receipt,record)
    print(json.dumps({key:record[key] for key in ('validation','schema','native_solver_execution')}))


if __name__=='__main__':main()
