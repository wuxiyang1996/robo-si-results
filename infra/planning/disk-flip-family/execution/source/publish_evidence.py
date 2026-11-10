"""Publish explicitly selected, content-addressed evidence assets and verify digests."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
REPOSITORY='wuxiyang1996/robo-si-review-assets';TAG='disk-flip-evidence-20261029'
GH='/fs/gamma-projects/vlm-robot/conda/bin/gh'
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
def publish(path,label):
 h=digest(path);suffix=''.join(path.suffixes);name=f'disk-flip-{label}-{h[:12]}{suffix}'
 release=json.loads(subprocess.check_output([GH,'api',f'repos/{REPOSITORY}/releases/tags/{TAG}']))
 asset=next((a for a in release['assets'] if a['name']==name),None)
 if asset is None:
  with tempfile.TemporaryDirectory(prefix='df-evidence-upload-') as directory:
   target=Path(directory)/name;shutil.copyfile(path,target)
   subprocess.run([GH,'release','upload',TAG,str(target),'--repo',REPOSITORY],check=True)
  release=json.loads(subprocess.check_output([GH,'api',f'repos/{REPOSITORY}/releases/tags/{TAG}']));asset=next(a for a in release['assets'] if a['name']==name)
 assert asset['size']==path.stat().st_size and asset.get('digest')=='sha256:'+h,asset['name']
 return dict(file=path.name,url=asset['browser_download_url'],sha256=h,bytes=asset['size'])
def main():
 p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('--label',required=True);p.add_argument('--receipt',type=Path,required=True);a=p.parse_args();r=publish(a.path,a.label);a.receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
if __name__=='__main__':main()
