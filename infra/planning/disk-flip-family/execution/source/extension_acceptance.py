"""Bind supplemental extension checks to the same verified baseline."""
import argparse,hashlib,json
from pathlib import Path
BASE=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text()) if p.exists() else {}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--setting',required=True);p.add_argument('--baseline',required=True);p.add_argument('--scorer',type=Path,required=True);p.add_argument('--boundary',type=Path,required=True);p.add_argument('--isolated',type=Path,required=True);p.add_argument('--portable',type=Path,required=True);p.add_argument('--bundle',type=Path,required=True);a=p.parse_args();run=BASE/'runs'/a.baseline;s=read(run/'summary.json');v=read(run/'verification.json');sc=read(a.scorer);bd=read(a.boundary);iso=read(a.isolated);portable=read(a.portable)
 complete=s.get('task_success') is True and v.get('task_success') is True and v.get('replay_matches') is True
 scorer=complete and sc.get('passed') is True and sc.get('source_sha256')==s.get('source_hashes',{}).get('run.py')
 boundary=bd.get('passed') is True and bd.get('scene_sha256')==sha(run/'scene.xml') and not bd.get('no_op',{}).get('task_success',True)
 isolated=complete and iso.get('passed') is True and iso.get('complete_isolated_execution') is True and iso.get('all_physics_state_and_control_array_hashes_match') is True and iso.get('negative_cases_passed') is True and iso.get('scene_sha256')==sha(run/'scene.xml') and iso.get('baseline_verification_sha256')==sha(run/'verification.json')
 manifest=a.bundle/'expert-manifest.json';bundle=read(manifest);download=read(BASE/'acceptance'/f'portable-{a.setting}-download.json')
 portable_ok=complete and bool(download.get('url')) and download.get('bundle_manifest_sha256')==portable.get('bundle_manifest_sha256') and bool(bundle) and bundle.get('baseline_verification_sha256')==sha(run/'verification.json') and portable.get('bundle_manifest_sha256')==sha(manifest) and all(sha(a.bundle/n)==h for n,h in bundle.get('files',{}).items()) and portable.get('passed') is True and portable.get('setting')==a.setting and portable.get('compiled_physics_arrays_identical') is True
 checks=dict(no_op_and_stage_counterexamples=bool(scorer and boundary),integrity_and_illegal_action_probes=bool(isolated),isolated_action_interface_execution=bool(isolated),portable_assets_and_reproducible_commands=bool(portable_ok))
 report=dict(setting=a.setting,baseline=a.baseline,baseline_verified=complete,checks=checks,evidence={k:str(getattr(a,k)) for k in ['scorer','boundary','isolated','portable','bundle']},policy_is_closed_loop=iso.get('policy_is_closed_loop'),scope='Evidence-bound automated supplemental checks. Recorded-policy process test is distinct from an online closed-loop child expert. No human signoff or second-person claim.')
 out=BASE/'acceptance'/f'extension-validation-{a.setting}.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
