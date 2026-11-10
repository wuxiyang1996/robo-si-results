"""Build a lightweight author-side summary without copying raw GPU recordings."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument("--output",type=Path,default=HERE/"p4-development-summary.json")
    args=parser.parse_args()
    attempts=[]
    for directory in sorted((HERE/"validation").glob("attempt-*")):
        match=re.fullmatch(r"attempt-(\d+)",directory.name)
        if not match: continue
        job=match[1]
        record=dict(job_id=job,artifact_path=str(directory.relative_to(REPO)),evidence_status="unknown",
                    task_success=None,formal_admission=False)
        for filename,key in (("attempt.json","execution"),("outcome.json","outcome"),("skill_refinement.json","skill_refinement")):
            path=directory/filename
            if path.is_file(): record[key]=json.loads(path.read_text())
        if "outcome" in record:
            record["task_success"]=record["outcome"].get("task_success")
            record["evidence_status"]=record["outcome"].get("evidence_status","unknown")
            if record["task_success"] is True and (record["outcome"].get("position_tolerance_rad")!=.001 or record["outcome"].get("original_five_rules_passed") is not True):
                record["task_success"]=None
                record["evidence_status"]="pending_strict_standard_and_safety_regrade"
        macro_path=directory/"prospective_macro_mapping.json"
        if macro_path.is_file():
            macro=json.loads(macro_path.read_text())
            record["prospective_macro_refinement_complete"]=bool(macro.get("prospectively_declared_macro_refinement_complete"))
            record["macro_effects_measured"]=bool(macro.get("all_macro_effects_measured"))
            record["leaf_diagnostics_complete"]=bool(macro.get("original_semantic_complete"))
        diagnostic_path=directory/"diagnostic_acceptance.json"
        if diagnostic_path.is_file():
            diagnostic=json.loads(diagnostic_path.read_text())
            record["diagnostic_accepted"]=bool(diagnostic.get("diagnostic_accepted"))
        output=subprocess.run(["sacct","-n","-P","-j",job,"--format=JobIDRaw,State,ExitCode"],text=True,capture_output=True)
        rows=[line.split("|") for line in output.stdout.splitlines()]
        exact=next((r for r in rows if r[0]==job),None)
        record["scheduler"]={"state":exact[1],"exit_code":exact[2]} if exact else {"state":"unknown"}
        log=HERE/"validation/job-logs"/f"h1-p4-development-{job}.log"
        if log.is_file():
            states=[line for line in log.read_text(errors="replace").splitlines() if line.startswith("STATE ")]
            record["last_logged_state"]=states[-1] if states else None
            record["physics_observed_in_log"]=bool(states)
        attempts.append(record)
    source_paths=[p for p in HERE.iterdir() if p.is_file() and p.suffix in (".py",".md",".json",".txt",".sbatch") and p.name not in (args.output.name,"p4-development-summary.json")]
    source_paths += [HERE.parent/"solution/push_box/run_push.py"]
    sources=[dict(path=str(path.relative_to(REPO)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),size_bytes=path.stat().st_size) for path in sorted(source_paths)]
    summary=dict(schema="h1-p4-development-summary/1",generated_at_utc=datetime.now(timezone.utc).isoformat(),
        task_id="H1S-07.P4",scope="one nominal 5 kg no-handle ground-push development profile, privileged G1 Dex3 expert",
        physical_development_profile_count=1,total_selected_tasks=22,
        full_witnesses=sum(a.get("task_success") is True for a in attempts),
        complete_prospective_macro_witnesses=sum(a.get("task_success") is True and a.get("prospective_macro_refinement_complete") is True for a in attempts),
        prescribed_repeats=3,formal_admission=False,all_22_implemented=False,
        remaining_scope=["handle pairing","randomized instances","sensor-only isolated agent interface","independent physical replay","human review","formal admission","other 21 selected tasks"],
        evidence_policy="Only measured outcome task_success=true counts as a full witness; shader/JIT planning and synthetic tests are not physical success.",
        attempts=attempts,expert_source_manifest=sources,
        raw_artifacts_policy="Raw snapshots, npz trajectories and videos remain in ignored validation/ for an external evidence packet; this JSON is lightweight.")
    args.output.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(dict(path=str(args.output),attempts=len(attempts),full_witnesses=summary["full_witnesses"])))

if __name__=="__main__": main()
