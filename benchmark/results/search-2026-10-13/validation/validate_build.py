from pathlib import Path
import subprocess,json,hashlib,struct
root=Path('/Users/random_person/Desktop/karger-klein-tarjan'); dst=Path('/tmp/kkt-mst-search'); exe=root/'bin/mst_search'
base=['--family','hierarchical_path','--n','128','--density','4']
cases=[[],['--family','bad','--n','128','--density','4'],['--family','line_metric','--n','8388608','--density','4'],['--family','hierarchical_path','--n','4194304','--density','33'],['--family','hierarchical_path','--n','128','--density','0'],['--family','hierarchical_path','--n','127','--density','4'],['--family','hierarchical_path','--n','32','--density','32'],base+['--repetitions','4'],base+['--repetitions','0'],base+['--repetitions','105'],base+['--warmups','0'],base+['--warmups','101'],base+['--n','128'],base+['--graph-seed','-1'],base+['--graph-seed','4294967296'],base+['--intrusion-per-mille','0'],['--family','lifted_hierarchy4','--n','32','--density','4'],['--family','lifted_random2','--n','128','--density','512'],['--family','lifted_distance4','--n','4194304','--density','33']]
checks=[]
for args in cases:
 p=subprocess.run([str(exe),*args],capture_output=True,text=True)
 assert p.returncode!=0 and not p.stdout and 'Running ' not in p.stderr,(args,p.returncode,p.stdout,p.stderr)
 checks.append({'args':args,'exit_code':p.returncode,'stderr':p.stderr.strip()})
p=subprocess.run([str(exe),'--help'],capture_output=True,text=True)
assert p.returncode==0 and 'multiple of five' in p.stdout

def macho(path):
 b=path.read_bytes();magic,_,_,_,ncmds=struct.unpack_from('<5I',b)
 assert magic==0xfeedfacf
 pos=32; result={'path':str(path),'sha256':hashlib.sha256(b).hexdigest()}
 for _ in range(ncmds):
  cmd,size=struct.unpack_from('<II',b,pos)
  if cmd==0x80000028:result['stack_bytes']=struct.unpack_from('<Q',b,pos+16)[0]
  if cmd==0x19:
   nsects=struct.unpack_from('<I',b,pos+64)[0]
   for j in range(nsects):
    off=pos+72+j*80;name=b[off:off+16].split(b'\0')[0];seg=b[off+16:off+32].split(b'\0')[0]
    if name==b'__text' and seg==b'__TEXT':
     secsize=struct.unpack_from('<Q',b,off+40)[0];fileoff=struct.unpack_from('<I',b,off+48)[0]
     result['text_bytes']=secsize;result['text_sha256']=hashlib.sha256(b[fileoff:fileoff+secsize]).hexdigest()
  pos+=size
 return result
normal=macho(exe);large=macho(root/'bin/large_stack/mst_search')
assert large['stack_bytes']==536870912 and normal['stack_bytes']==0
assert normal['text_sha256']==large['text_sha256']
result={'validation':'pass','timing_runs':0,'negative_cli_checks':checks,'help_check':'pass','normal_binary':normal,'large_stack_binary':large,'text_identity':'pass','source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'benchmark/mst_search.cpp',root/'benchmark/search_fixtures.hpp',root/'Makefile']},'scope':'Final lifted fixture dispatch; only invalid CLI/help executed, no solver measurements.'}
(dst/'final_validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'validation':'pass','negative_checks':len(checks),'text_sha256':large['text_sha256'],'stack_bytes':large['stack_bytes']}))
