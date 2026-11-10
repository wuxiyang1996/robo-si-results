"""Publish verified run evidence with content hashes and full video decoding."""
import argparse,gzip,hashlib,json,subprocess,tarfile
from pathlib import Path
import imageio.v2 as imageio
import imageio_ffmpeg
from .publish_evidence import publish
BASE=Path(__file__).resolve().parent
STAGE=BASE.parent.parent/'df-release-staging-20261029'
def main():
 p=argparse.ArgumentParser();p.add_argument('runs',nargs='+');a=p.parse_args();STAGE.mkdir(exist_ok=True)
 manifest=BASE/'acceptance/public-media.json';media=json.loads(manifest.read_text());video_report=BASE/'acceptance/release-video-validation.json';videos=json.loads(video_report.read_text())
 for name in a.runs:
  src=BASE/'runs'/name;v=json.loads((src/'verification.json').read_text());assert v['replay_matches'];reference=json.loads((src/'reference-replay-verification.json').read_text());assert reference['all_physics_state_and_control_array_hashes_match'];row=media.setdefault(name,{})
  if not any(x['run']==name for x in videos['videos']):
   video=src/'video.mp4';result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-threads','1','-i',str(video),'-f','null','-'],capture_output=True,text=True)
   with imageio.get_reader(video) as reader:meta=reader.get_meta_data();frames=reader.count_frames()
   expected=json.loads((src/'summary.json').read_text())['video_frames'];assert result.returncode==0 and not result.stderr.strip() and frames==expected and meta['fps']==10
   videos['videos'].append(dict(run=name,sha256=hashlib.sha256(video.read_bytes()).hexdigest(),bytes=video.stat().st_size,decoded_frames=frames,expected_frames=expected,fps=meta['fps'],duration_s=meta['duration'],full_decode_passed=True,errors=''));video_report.write_text(json.dumps(videos,indent=2)+'\n')
  def save():manifest.write_text(json.dumps(media,indent=2)+'\n')
  if 'video' not in row:row['video']=publish(src/'video.mp4',name+'-video');save()
  if 'trajectory' not in row:row['trajectory']=publish(src/'trajectory-reference.npz',name+'-trajectory');save()
  if 'trace' not in row:
   compact=STAGE/(name+'-trace-compact.jsonl.gz');stream=(src/'trace.jsonl').open('rb') if (src/'trace.jsonl').exists() else gzip.open(src/'trace.jsonl.gz','rb');digest=hashlib.sha256()
   with gzip.open(compact,'wb',compresslevel=6) as out:
    for line in stream:
     data=(json.dumps({k:v for k,v in json.loads(line).items() if k!='contacts'})+'\n').encode();out.write(data);digest.update(data)
   stream.close();row['trace']=publish(compact,name+'-trace');row['trace'].update(file='trace-compact.jsonl.gz',uncompressed_sha256=digest.hexdigest());save()
  for image in ['initial.png','final.png','trajectory.png']:
   images=row.setdefault('images',{})
   if image not in images:images[image]=publish(src/image,name+'-'+Path(image).stem);save()
  if 'sources' not in row:
   archive=STAGE/(name+'-sources.tar.gz')
   with tarfile.open(archive,'w:gz') as tar:
    items=list(dict.fromkeys([*json.loads((src/'summary.json').read_text())['source_hashes'],'initial_state.json','model-binding.json']))
    for item in items:
     assert Path(item).name==item
     tar.add(src/item,arcname=name+'/'+item)
   row['sources']=publish(archive,name+'-sources');save()
  print(name,'verified assets published',flush=True)
if __name__=='__main__':main()
