import gzip,json,hashlib
from pathlib import Path
import numpy as np
base=Path(__file__).resolve().parents[1];p=base/'runs/v3j-rope-heading-a47';roles=json.loads((p/'contact-roles.json').read_text())['links']
receivers={rid:{int(i) for i,r in roles.items() if r['entity'].startswith(rid+'_coupler_')} for rid in ['go2_a','go2_b']};rope={int(i) for i,r in roles.items() if r['entity'].startswith('rope_')}
peaks={rid:dict(resultant_n=0.,sum_norm_n=0.,single_contact_n=0.,resultant_peak_time_s=None,phase=None) for rid in receivers};samples=0
with gzip.open(p/'contacts.jsonl.gz','rt') as stream:
 for line in stream:
  row=json.loads(line);samples+=1;c=row['contacts'];forces={rid:np.zeros(3) for rid in receivers};sums={rid:0. for rid in receivers}
  for a,b,f in zip(c['link_a'],c['link_b'],c['force']):
   f=np.asarray(f);n=float(np.linalg.norm(f))
   for rid,links in receivers.items():
    sign=1 if a in links and b in rope else -1 if b in links and a in rope else 0
    if sign:forces[rid]+=sign*f;sums[rid]+=n;peaks[rid]['single_contact_n']=max(peaks[rid]['single_contact_n'],n)
  for rid,f in forces.items():
   n=float(np.linalg.norm(f));r=peaks[rid];r['sum_norm_n']=max(r['sum_norm_n'],sums[rid])
   if n>r['resultant_n']:r.update(resultant_n=n,resultant_peak_time_s=row['time_s'],phase=row['phase'])
r=dict(schema='m4-complete-connector-load-audit/1',attempt=p.name,samples=samples,peaks=peaks,source_sha256=hashlib.sha256((p/'contacts.jsonl.gz').read_bytes()).hexdigest(),method='Sum signed native contact forces between every rope link and receiver+pin assembly. Contact ordering is accounted for; reversing global sign leaves resultant magnitudes unchanged. Internal assembly forces excluded. Sum of contact norms and individual contact peak reported separately.',scope='Offline load diagnosis; no new score or unvalidated material strength inference. Existing 150 N pin/eye service and 300 N hard contact checks are not renamed as a whole-assembly norm-sum rating.',formal_admission=False)
(base/'design/complete-connector-load-a47.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
