"""Report keys actually read by the snapshotted controller; no guessed aliases."""
import ast,hashlib,json
from pathlib import Path

def audit(source,tuning):
 tree=ast.parse(source.read_text());known=set()
 def mapping(node):return isinstance(node,ast.Attribute) and node.attr=='tuning'
 for node in ast.walk(tree):
  if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='get' and mapping(node.func.value) and node.args and isinstance(node.args[0],ast.Constant):known.add(node.args[0].value)
  if isinstance(node,ast.Subscript) and mapping(node.value) and isinstance(node.slice,ast.Constant):known.add(node.slice.value)
  if isinstance(node,ast.Compare) and isinstance(node.left,ast.Constant) and any(mapping(n) for n in node.comparators):known.add(node.left.value)
 values=json.loads(tuning.read_text());unknown=sorted(set(values)-known)
 return dict(controller_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),unknown_keys=unknown,all_keys_read=not unknown,scope='Static literal-key audit; validates spelling, not physical performance or whether a conditional branch executes.')
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('tuning',type=Path);p.add_argument('--source',type=Path,default=Path(__file__).with_name('run.py'));a=p.parse_args();r=audit(a.source,a.tuning);print(json.dumps(r));raise SystemExit(not r['all_keys_read'])
