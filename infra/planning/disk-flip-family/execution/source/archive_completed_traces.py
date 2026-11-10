"""Lossless storage for closed development traces; preserve original byte hashes."""
import argparse,gzip,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def digest(path,compressed=False):
 h=hashlib.sha256();size=0
 with (gzip.open(path,'rb') if compressed else path.open('rb')) as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk);size+=len(chunk)
 return h.hexdigest(),size
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--all-closed',action='store_true');args=p.parse_args();selected=json.loads((ROOT/'acceptance/public-selection-development.json').read_text());runs=sorted((ROOT/'runs').glob('DF-*-a*'),key=lambda p:int(p.name.rsplit('-a',1)[-1].split('-')[0]));keep=set(selected)
 for setting in ['DF-02-G','DF-02-F','DF-03-G','DF-04-G','DF-04-S']:keep.update(p.name for p in [r for r in runs if r.name.startswith(setting+'-a')][-3:])
 if args.all_closed:keep=set()
 saved=0;count=0
 for folder in runs:
  source=folder/'trace.jsonl'
  if folder.name in keep or folder.name.startswith('DF-01') or not source.exists() or not (folder/'summary.json').exists() or not (folder/'verification.json').exists() or source.stat().st_size<20_000_000:continue
  if not args.apply:print(folder.name,source.stat().st_size);continue
  before=source.stat();raw_hash,raw_bytes=digest(source);target=folder/'trace.jsonl.gz';temporary=folder/'.trace.jsonl.gz.tmp';assert not target.exists()
  with source.open('rb') as src,temporary.open('wb') as dst:
   with gzip.GzipFile(filename='',mode='wb',fileobj=dst,mtime=0,compresslevel=6) as z:
    for chunk in iter(lambda:src.read(1024*1024),b''):z.write(chunk)
  assert digest(temporary,True)==(raw_hash,raw_bytes),'Round-trip mismatch'
  now=source.stat();assert (now.st_size,now.st_mtime_ns)==(before.st_size,before.st_mtime_ns),'Trace changed while archiving'
  os.replace(temporary,target);compressed_hash,size=digest(target)
  (folder/'trace-storage.json').write_text(json.dumps(dict(storage='gzip; lossless original bytes',file=target.name,sha256=compressed_hash,bytes=size,uncompressed_file='trace.jsonl',uncompressed_sha256=raw_hash,uncompressed_bytes=raw_bytes,restore='gzip -dc trace.jsonl.gz > trace.jsonl',full_evidence_retained=True),indent=2)+'\n')
  source.unlink();saved+=raw_bytes-size;count+=1;print(folder.name,'saved_bytes',raw_bytes-size,flush=True)
 print(json.dumps(dict(archived=count,freed_bytes=saved,original_bytes_verified=True)))
if __name__=='__main__':main()
