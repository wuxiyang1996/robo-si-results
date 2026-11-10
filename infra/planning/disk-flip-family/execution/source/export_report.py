"""Export bounded public evidence and bilingual task implementation documentation."""
import argparse,gzip,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'df_family';DEST=ROOT/'infra/planning/disk-flip-family'
SETTINGS=['DF-01-G','DF-02-G','DF-02-F','DF-03-G','DF-04-G','DF-04-S']
LABELS={'DF-01-G':'原版轻柔翻圆盘','DF-02-G':'带沿浅盘 · Dex3','DF-02-F':'带沿浅盘 · Inspire','DF-03-G':'受力敏感浅盘','DF-04-G':'开放策略 · 双臂','DF-04-S':'开放策略 · 单臂'}
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');tmp.replace(p)
def read(p):return json.loads(p.read_text()) if p.exists() else {}
def copy(src,dst):dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def trace_bytes(folder):
 p=folder/'trace.jsonl'
 return p.read_bytes() if p.exists() else gzip.open(folder/'trace.jsonl.gz','rb').read()
def trajectory_export(src,dst,manifest='trajectory-download.json'):
 raw=src.read_bytes();parts=[]
 for k,offset in enumerate(range(0,len(raw),18_000_000)):
  p=dst/(src.name if len(raw)<=18_000_000 else f'{src.name}.part{k+1:02}');p.write_bytes(raw[offset:offset+18_000_000]);parts.append(dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)))
 write(dst/manifest,dict(file=src.name,bytes=len(raw),sha256=sha(src),parts=parts,reconstruct=f'Concatenate parts in listed order as {src.name}. No samples were removed.'))
 return parts

def collect():
 attempts=[]
 for p in sorted((BASE/'runs').glob('DF-*'),key=lambda p:(p.name.rsplit('-a',1)[0],int(p.name.rsplit('-a',1)[-1].split('-')[0]))):
  if p.name.endswith('-replay'):continue
  summary=read(p/'summary.json');v=read(p/'verification.json');original=p.name.startswith('DF-01')
  infra=read(p/'infrastructure.json')
  status='completed_execution' if summary else 'infrastructure_incomplete' if infra else 'running_or_incomplete' if (p/'trace.jsonl').exists() or (p/'trace.jsonl.gz').exists() else 'setup_failed'
  success=bool(summary.get('full_task_success') and v.get('fresh_complete_execution') and v.get('independent_physics_replay') is True) if original else bool(summary.get('task_success') is True and v.get('task_success') is True and v.get('replay_matches') is True and v.get('source_hashes_match') is True)
  phase_groups={r['phase']:r['high_level'] for r in read(p/'plan.json').get('low_level',[]) if isinstance(r,dict)}
  progression=max(({'prepare':0,'grasp':1,'lift':2,'turn':3,'place':4}.get(phase_groups.get(r['phase']),0) for r in read(p/'segments.json') if isinstance(r,dict)),default=0)
  execution_success=bool(summary.get('full_task_success') if original else summary.get('task_success'))
  if execution_success and not v:status='awaiting_independent_verification'
  attempts.append(dict(execution_success=execution_success,verification_pending=bool(summary and not v),physics_hz=summary.get('physics_hz',400 if original else None),progress_rank=progression,run=p.name,setting=p.name.rsplit('-a',1)[0],physics_executed=bool(summary),success=success,failure=summary.get('error') if original else summary.get('failure'),status=status,seconds=summary.get('status',{}).get('elapsed',0) if original else summary.get('simulated_seconds',0),independent_replay=v.get('independent_physics_replay') is True if original else v.get('replay_matches') is True,seen_lift=v.get('seen_lift',summary.get('seen_lift',False)),seen_flip=v.get('seen_flip',summary.get('seen_flip',False))))
 selected=[]
 for setting in SETTINGS:
  candidates=[x for x in attempts if x['setting']==setting and x['physics_executed'] and x['independent_replay']]
  # Partial turnover outranks a lift, but never counts as task success.
  chosen=max(enumerate(candidates),key=lambda pair:(pair[1]['success'],pair[1]['seen_flip'],pair[1]['seen_lift'],pair[1]['progress_rank'],pair[0]))[1]
  selected.append(chosen.copy())
 return attempts,selected

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--selection',type=Path);args=parser.parse_args()
 DEST.mkdir(parents=True,exist_ok=True);attempts,selected=collect()
 if args.selection:
  names=read(args.selection);selected=[next(a.copy() for a in attempts if a['run']==n) for n in names]
  assert [a['setting'] for a in selected]==SETTINGS and all(a['independent_replay'] for a in selected)
 evidence=DEST/'execution';evidence.mkdir(exist_ok=True);media=read(BASE/'acceptance/public-media.json')
 for a in attempts:
  src=BASE/'runs'/a['run'];dst=evidence/'attempts'/a['run']
  for name in ['summary.json','verification.json','plan.json','segments.json','high-low-trajectory.json','model-binding.json','error.txt','run.py','model.py','pregrasp-ik.json','wrench.py','reference_interface.py','trace-storage.json','infrastructure.json']:
   if (src/name).exists():copy(src/name,dst/name)
 for a in selected:
  src=BASE/'runs'/a['run'];dst=evidence/a['run'];dst.mkdir(exist_ok=True)
  a['image_urls']={n:item['url'] for n,item in media.get(a['run'],{}).get('images',{}).items()}
  a['video_url']=media.get(a['run'],{}).get('video',{}).get('url',f"execution/{a['run']}/video.mp4")
  for name in ['summary.json','verification.json','plan.json','segments.json','high-low-trajectory.json','model-binding.json','scene.xml','initial_state.json','initial.png','final.png','trajectory.png','video.mp4','run.py','model.py','asset_hashes.json','oracle_plan.json','wrench.py','reference_interface.py','trace-storage.json','infrastructure.json']:
   if name=='video.mp4' and a['run'] in media:continue
   if name in a['image_urls']:continue
   if media.get(a['run'],{}).get('sources') and name in ['run.py','model.py','wrench.py','reference_interface.py','scene.xml']:continue
   if (src/name).exists():copy(src/name,dst/name)
  if a['run'] in media:write(dst/'external-media.json',media[a['run']])
  for stale in list(dst.glob('trajectory.npz*'))+list(dst.glob('trace.jsonl.gz*'))+list(dst.glob('*-download.json')):stale.unlink()
  if a['setting']=='DF-01-G':
   if media.get(a['run'],{}).get('trajectory'):
    item=media[a['run']]['trajectory'];a['trajectory_parts']=[item];write(dst/'trajectory-download.json',dict(**item,parts=[item],scope='Complete native trajectory hosted externally; SHA-256 binds the download.'))
   else:a['trajectory_parts']=trajectory_export(src/'trajectory.npz',dst)
  else:
   assert any(read(src/'reference-replay-verification.json').get(k) for k in ['all_physics_state_and_control_array_hashes_match','all_400hz_state_and_control_array_hashes_match'])
   for name in ['trajectory-reference.json','reference-replay-verification.json']:copy(src/name,dst/name)
   if media.get(a['run'],{}).get('trajectory'):
    item=media[a['run']]['trajectory'];assert sha(src/'trajectory-reference.npz')==item['sha256'];a['trajectory_parts']=[item];write(dst/'trajectory-download.json',dict(**item,parts=[item],scope='All held references; reconstruct every physics step with the included replay code.'))
   else:
    copy(src/'trajectory-reference.npz',dst/'trajectory-reference.npz');a['trajectory_parts']=[dict(file='trajectory-reference.npz',bytes=(dst/'trajectory-reference.npz').stat().st_size,sha256=sha(dst/'trajectory-reference.npz'))]
  compact=[]
  full_trace_hash=hashlib.sha256();trace_path=src/'trace.jsonl';stream=trace_path.open('rb') if trace_path.exists() else gzip.open(src/'trace.jsonl.gz','rb')
  for line in stream:
   full_trace_hash.update(line);row=json.loads(line)
   if a['setting']=='DF-01-G':
    disk=row['objects']['disk'];compact.append(dict(time=row['time'],phase=row.get('phase'),stage=row.get('stage'),disk_pos=disk['pos'],disk_quat=disk['quat'],robot_force=disk['robot_contact_force_n'],table_force=disk['support_force_n']))
   else:compact.append({k:v for k,v in row.items() if k!='contacts'})
  stream.close()
  with gzip.open(dst/'trace-compact.jsonl.gz','wb',compresslevel=6) as out:out.write(('\n'.join(json.dumps(x) for x in compact)+'\n').encode())
  a['trace_parts']=[dict(file='trace-compact.jsonl.gz',bytes=(dst/'trace-compact.jsonl.gz').stat().st_size,sha256=sha(dst/'trace-compact.jsonl.gz'))]
  write(dst/'trace-scope.json',dict(trace_rows=len(compact),trace_hz=50,full_trace_sha256=full_trace_hash.hexdigest(),full_local_trace=str(src/('trace.jsonl' if (src/'trace.jsonl').exists() else 'trace.jsonl.gz')),public_trace='50 Hz object state and aggregate contact loads; repetitive individual contact lists omitted. Full physics recordings remain local.'))
  if media.get(a['run'],{}).get('trace'):
   item=media[a['run']]['trace'];assert hashlib.sha256(gzip.decompress((dst/'trace-compact.jsonl.gz').read_bytes())).hexdigest()==item['uncompressed_sha256'];a['trace_parts']=[item];(dst/'trace-compact.jsonl.gz').unlink()
  if media.get(a['run'],{}).get('sources'):
   a['source_bundle']=media[a['run']]['sources']
   if (dst/'sources').exists():shutil.rmtree(dst/'sources')
  elif (src/'sources').exists():shutil.copytree(src/'sources',dst/'sources',dirs_exist_ok=True)
  a['evidence']='execution/'+a['run'];a['verification']=read(src/'verification.json')
 replay=BASE/'runs'/(selected[0]['run']+'-replay');dst=evidence/replay.name;dst.mkdir(exist_ok=True)
 for name in ['summary.json','initial_state.json','asset_hashes.json','final.png']:
  if (replay/name).exists():copy(replay/name,dst/name)
 for p in (BASE/'plate-design').iterdir():copy(p,evidence/'plate-design'/p.name)
 for p in BASE.glob('*.py'):copy(p,evidence/'source'/p.name)
 for p in BASE.glob('*.sbatch'):copy(p,evidence/'source'/p.name)
 probes=read(BASE/'plate-design/support-probes.json')
 report=dict(schema='disk-flip-implementation/1.0',updated='2026-10-29',variant_count=4,embodiment_count=3,setting_count=6,physical_attempts=sum(a['physics_executed'] for a in attempts),setup_failures=sum(a['status']=='setup_failed' for a in attempts),incomplete_attempts=sum(a['status']=='running_or_incomplete' for a in attempts),successful_executions=sum(a['success'] for a in attempts),settings_with_full_witness=sum(a['success'] for a in selected),independent_original_replays=sum(a['setting']=='DF-01-G' and a['independent_replay'] for a in attempts),infrastructure_incomplete_attempts=sum(a['status']=='infrastructure_incomplete' for a in attempts),static_support_probes=len(probes),static_support_probes_passed=sum(p['passed'] for p in probes),selected=selected,attempts=attempts,admission=False,agent_bundle_allowed=False,scope='Author-side privileged development. Failed attempts are not infeasibility proofs. Historical DF-01 scores remain separate.',limitations=['Extension controller revisions are development attempts, not a common-policy comparison.','Extension MuJoCo and original Genesis protocols are separate.','Complete witness counts require a successful execution and independent replay; qualification and external signoff are tracked separately.','A portable development scene bundle was checked for identical physical arrays; this is not a successful qualification bundle.','Inversion, support transfer, release and the complete terminal goal are separately verified per setting.'])
 for name in ['release-video-validation.json','original-isolated-recorded-policy.json','original-isolated-closed-loop.json','original-portable-validation.json','original-portable-download.json','p3-contact-feasibility.json','original-frozen-scorer-checks.json','storage-incident-20261029.json','public-media.json','isolated-boundary-G.json','isolated-boundary-F.json','isolated-boundary-S.json','plan-v1.json','status.json','action-interface-G.json','action-interface-F.json','action-interface-S.json','inspire-collision-audit.json','palm-collision-regression.json','integration-convergence-audit.json','portable-download.json']:
  if (BASE/'acceptance'/name).exists():copy(BASE/'acceptance'/name,evidence/'acceptance'/name)
 for pattern in ['extension-scorer-*.json','extension-validation-*.json','isolated-boundary-*-a*.json','extension-followup-jobs.json','live-jobs.json','ik-*.json','portable-DF-*-download.json','held-position-command-check.json','campaign-rejects-failed-baseline.json','stretch-prefix-observation-check.json','inspire-mimic-import-check.json','handoff-contact-feasibility.json','resume-progress-20261029.json','diagnostic-checkpoint-boundary.json']:
  for path in (BASE/'acceptance').glob(pattern):copy(path,evidence/'acceptance'/path.name)
 for cohort in (BASE/'qualification').glob('*/cohort-v*'):
  for name in ['manifest.json','status.json','campaign-jobs.json','submissions.json']:
   if (cohort/name).exists():copy(cohort/name,evidence/'qualification'/cohort.parent.name/cohort.name/name)
 report['monitor_snapshot']=read(BASE/'acceptance/live-jobs.json')
 report['qualification']=read(BASE/'acceptance/status.json').get('settings',[])
 report['additional_witnesses']=[]
 for attempt in attempts:
  name=attempt['run'];asset=media.get(name,{})
  if not attempt['success'] or name in {x['run'] for x in selected} or not all(asset.get(k,{}).get('url') for k in ['video','trajectory','sources']):continue
  src=BASE/'runs'/name;verification=read(src/'reference-replay-verification.json')
  if not verification.get('all_physics_state_and_control_array_hashes_match'):continue
  path=evidence/'attempts'/name
  for filename in ['reference-replay-verification.json','trajectory-reference.json']:copy(src/filename,path/filename)
  write(path/'external-media.json',asset)
  report['additional_witnesses'].append(dict(run=name,setting=attempt['setting'],seconds=attempt['seconds'],evidence='execution/attempts/'+name,media=asset,fixed_reference_prefix=bool(read(src/'plan.json').get('controller_tuning',{}).get('reference_prefix_file'))))
 report['acceptance_status']='execution/acceptance/status.json'
 report['acceptance_plan']='execution/acceptance/plan-v1.json'
 write(DEST/'implementation.json',report)
 for lang in ['zh','en']:
  zh=lang=='zh';doc=docs(report,zh);(DEST/('IMPLEMENTATION.md' if zh else 'IMPLEMENTATION-en.md')).write_text(doc)
 readme=(BASE/'README.md').read_text() if (BASE/'README.md').exists() else '';readme_extra='\n## Acceptance campaign'+readme.split('## Acceptance campaign',1)[1] if '## Acceptance campaign' in readme else ''
 (BASE/'README.md').write_text('''# Disk Flip family implementation

Author-side expert development for six selected settings. Original DF-01 uses the frozen Genesis reference; extensions use MuJoCo and official G1/Stretch assets. See [implementation report](../infra/planning/disk-flip-family/IMPLEMENTATION.md) and [machine-readable ledger](../infra/planning/disk-flip-family/implementation.json).

## Run

Use the Genesis Python environment (Python 3.12, Genesis 1.4.3, MuJoCo 3.14.0). Official meshes are currently resolved from `../robo-si-local-tests/h1-implementation-20261027/asset-cache`; exported scene paths require this cache or explicit path remapping. Each run snapshots its controller/model and records source hashes. The documentation renderer additionally requires `markdown` and `beautifulsoup4` (available in the host Python here).

```bash
sbatch -J df-example df_family/run_extension.sbatch DF-02-G a09
python -m df_family.verify df_family/runs/DF-02-G-a09
python -m df_family.plate_probe
python -m df_family.export_report
python infra/planning/render_disk_flip_family.py
```

Use a fresh attempt suffix; existing outputs are never overwritten by the runner. Original execution and replay have dedicated sbatch files. Controls act only through bounded actuators after initialization. Independent replay starts a new simulator from the recorded initial state and checks every recorded physics step. High/low coverage is not equivalent to task success.

The extension controller is a candidate, not a solved expert. A fixed base, privileged states, compound plate inertia, prototype force limits, and an alternate engine restrict all claims. No public-agent score or production admission is asserted.
'''+readme_extra)
 print(json.dumps({k:v for k,v in report.items() if k not in ['selected','attempts','limitations','monitor_snapshot','qualification']},ensure_ascii=False))

def docs(r,zh):
 title='Disk Flip：专家实现与逐项执行证据' if zh else 'Disk Flip: expert implementation and per-setting execution evidence'
 d=f'# {title}\n\n2026-10-29 · 4 variants · 3 embodiments · 6 settings\n\n'
 if zh:
  d+=f"**已为 6 个配置实现候选专家与执行记录；完整成功见证目前为 {r['settings_with_full_witness']}/6。** 本轮共 {r['physical_attempts']} 次有物理轨迹的专家执行、{r['setup_failures']} 次启动失败；另有 {r['independent_original_replays']} 次原版独立动作回放和 4 次静态支撑探针。只把完整成功且独立验证通过的执行称作成功解。失败录像展示真实问题，不证明该配置不可行。\n\n"
  d+='原版 DF-01-G 修订执行 a03 为 478.26 s，23,913 个控制步、5 个高层目标、26 个低层动作段，独立回放通过。新证据单列，不改写历史 6/6 执行、2/2 回放的统计。正式准入仍为 false。\n\n'
 else:
  d+=f"**Candidate experts and execution records exist for all six settings; {r['settings_with_full_witness']}/6 currently has a complete successful witness.** This round includes {r['physical_attempts']} physics executions, {r['setup_failures']} setup failures, {r['independent_original_replays']} independent original replays and four static support probes. Failed attempts do not prove infeasibility.\n\nThe revised original execution a03 spans 478.26 s, 23,913 controls, five high-level goals and 26 low-level segments. Its independent action replay passed. Historical 6/6 executions and 2/2 replays remain separate; formal admission remains false.\n\n"
 pending=[a for a in r['attempts'] if a.get('execution_success') and a.get('verification_pending')]
 if pending:
  names=', '.join(f"{a['run']} ({a['seconds']:.2f} s)" for a in pending)
  d+=(f"完整执行已满足目标、等待独立回放：**{names}**。这些候选暂不计入成功见证。\n\n" if zh else f"Full executions met the goal and await independent replay: **{names}**. These candidates are not yet counted as verified witnesses.\n\n")
 if read(BASE/'acceptance/inspire-mimic-import-check.json').get('passed'):
  d+=('Inspire 导入修正：[核对记录](execution/acceptance/inspire-mimic-import-check.json)。保留官方 12 条 mimic 联动约束，去掉导入器重复添加的 12 条；惯量、几何、关节限位和执行器数组不变。历史 F 失败尝试保留旧模型，新模型必须重新完成完整运行与回放。\n\n' if zh else 'Inspire import correction: [audit](execution/acceptance/inspire-mimic-import-check.json). Retain the 12 official mimic linkages and remove 12 duplicates added by the adapter. Inertials, geometry, joint limits and actuators are unchanged. Historical failed F attempts retain their original models; the corrected importer requires fresh execution and replay.\n\n')
 if zh:
  d+='## 正式验收进度\n\n[固定验收方案](execution/acceptance/plan-v1.json) · [实时导出状态](execution/acceptance/status.json)\n\n全部开发尝试与正式重复队列分开。每个配置须先完成全流程见证，再冻结控制器、连续执行 3 次新运行并独立回放；失败重复不能替换。还需反例与非法动作检查、便携资产、隔离动作接口、视频复核和第二人复现。DF-01-G 的 cohort-v1 三次闭环执行成功，但独立回放失败（稳定时间 1.99 s，且末态偏差超出容差），该队列保留为未通过。修订专家 a03 继续推至目标区内部后再释放，完整执行与独立回放均通过；其 cohort-v2 的三次新运行与独立回放均已通过。扩展配置的冻结队列与通过数量见下表；没有人工签字。\n\n冻结原版评分器的 [38 项反例与回归检查](execution/acceptance/original-frozen-scorer-checks.json)通过；这些是评分器与几何检查，不是物理成功执行。\n\n新增[积分步长诊断](execution/acceptance/integration-convergence-audit.json)：同一 Stretch 撤手检查点在 400 Hz 下出现角速度超限，在更小步长下完成卸载。已启动 2,000 Hz 的完整开发重跑；该局部诊断不计作全任务成功，旧 400 Hz 失败记录不改写。\n\nG/F/S 动作接口已分别通过 7 类拒绝与原子提交探针；此外，三种手型均通过独立 Python 进程发送的 7 类非法动作测试，拒绝后物理状态与参考保持不变，3 s 无动作测试不会误报成功。这些仍是边界探针，不是完整任务的隔离执行或操作系统安全沙箱。Inspire 手掌碰撞体已按官方网格分解，消除了单凸包填满拇指关节槽导致的假碰撞，质量与惯性保持不变。\n\n'
 else:
  d+='## Formal acceptance progress\n\n[Frozen acceptance plan](execution/acceptance/plan-v1.json) · [Exported status](execution/acceptance/status.json)\n\nDevelopment attempts are separate from qualification. Each setting needs a complete witness, a frozen controller, three fresh uninterrupted repetitions and independent replay. Failed repetitions cannot be replaced. Counterexamples, illegal-action checks, portable assets, process isolation, video review and second-person reproduction are also required. DF-01-G cohort-v1 passed three closed-loop runs but failed replay (1.99 s final stability and endpoint mismatch); it remains failed. Revised expert a03 pushes farther inside the unchanged goal region and passed a complete run and replay; cohort-v2 passed all three fresh runs and its independent replay. Extension cohort status is reported below; no human signoff is claimed. [Integration-step diagnostics](execution/acceptance/integration-convergence-audit.json) found a Stretch release failure at 400 Hz but successful unloading with smaller steps. Fresh 2,000 Hz development executions are running; checkpoint diagnostics are not full witnesses, and archived 400 Hz failures remain failures. Seven rejection/atomicity probes passed for each G/F/S action interface; separate-process G/F/S probes also reject seven illegal action classes atomically, and physical no-ops cannot satisfy the goal. These are boundary probes, not complete isolated task executions or an OS security sandbox. Inspire palm decomposition removes false convex-hull socket contacts while preserving official inertials.\n\n'
 if zh:
  d+='[原版 cohort-v1](execution/qualification/DF-01-G/cohort-v1/status.json) · [原版 cohort-v2](execution/qualification/DF-01-G/cohort-v2/status.json) · 独立进程探针：[Dex3](execution/acceptance/isolated-boundary-G.json) / [Inspire](execution/acceptance/isolated-boundary-F.json) / [SG3](execution/acceptance/isolated-boundary-S.json)\n\n'
 else:
  d+='[Original cohort-v1](execution/qualification/DF-01-G/cohort-v1/status.json) · [Original cohort-v2](execution/qualification/DF-01-G/cohort-v2/status.json) · Separate-process probes: [Dex3](execution/acceptance/isolated-boundary-G.json) / [Inspire](execution/acceptance/isolated-boundary-F.json) / [SG3](execution/acceptance/isolated-boundary-S.json)\n\n'
 q=next((x.get('qualification_progress') for x in r['qualification'] if x['setting']=='DF-01-G'),{}) or {}
 count=sum(x.get('full_success',False) for x in q.get('repetitions',[]))
 d+=(f"当前冻结队列 {q.get('cohort','pending')}：新运行 {count}/3 通过；独立回放 {q.get('replay_status','pending')}。\n\n" if zh else f"Current frozen cohort {q.get('cohort','pending')}: {count}/3 fresh executions passed; independent replay {q.get('replay_status','pending')}.\n\n")
 for row in r['qualification']:
  if row['setting']=='DF-01-G' or not row.get('qualification_progress'):continue
  progress=row['qualification_progress'];count=sum(x.get('full_success',False) for x in progress.get('repetitions',[]));cohort=row['qualification_cohort'];link=f"execution/qualification/{row['setting']}/{cohort}/status.json"
  d+=(f"{row['setting']} [{cohort}]({link})：新运行 {count}/3 通过；独立回放 {progress.get('replay_status','pending')}。\n\n" if zh else f"{row['setting']} [{cohort}]({link}): {count}/3 fresh executions passed; independent replay {progress.get('replay_status','pending')}.\n\n")
 live=r.get('monitor_snapshot',{});active=[x for x in live.get('runs',[]) if x.get('scheduler',{}).get('state')=='RUNNING']
 if active:
  d+=(f"运行快照（{live.get('checked_at','')}；[完整记录](execution/acceptance/live-jobs.json)）：\n\n" if zh else f"Run snapshot ({live.get('checked_at','')}; [full record](execution/acceptance/live-jobs.json)):\n\n")
  for row in active:
   state=('执行失败，独立回放处理中' if zh else 'execution failed; independent replay in progress') if row.get('terminal_summary') and row.get('failure') else ('完整执行进行中，尚未计为成功' if zh else 'full execution in progress; not counted as success')
   d+=f"- {row['run']}: {state}; {(row.get('last_time') or 0):.2f} s; {row.get('phase','')}.\n"
  d+='\n'
 if r['infrastructure_incomplete_attempts']:
  d+=(f"另有 {r['infrastructure_incomplete_attempts']} 次运行因共享存储写满而未完成，另记为基础设施中断，不计为任务物理失败或成功；[事故记录](execution/acceptance/storage-incident-20261029.json)保留最后可读状态。替代输出目录中的新尝试从初态重跑。\n\n" if zh else f"{r['infrastructure_incomplete_attempts']} additional runs were interrupted by shared-storage exhaustion. They count as infrastructure-incomplete, not physical failures or successes; [incident records](execution/acceptance/storage-incident-20261029.json) retain readable partial states. New attempts use fresh initial states and alternate output storage.\n\n")
 isolated=read(BASE/'acceptance/original-isolated-closed-loop.json')
 if isolated.get('passed'):
  replay='通过' if isolated.get('independent_physics_replay') is True else '待完成'
  d+=(f"原版闭环专家已在独立 Python 进程中完成全任务：通过 JSON 接收只读状态，在线产生 {isolated['commands_from_child']:,} 次关节目标；物理与评分由父进程持有，无共享仿真内存。该执行的独立回放：{replay}。[执行与边界探针报告](execution/acceptance/original-isolated-closed-loop.json)。这仍是特权专家验证，不是公开智能体成绩或操作系统安全沙箱。\n\n" if zh else f"The original online closed-loop expert completed the task in a separate Python process, receiving read-only JSON observations and emitting {isolated['commands_from_child']:,} joint commands. The parent owns physics and scoring, with no shared simulator memory. Independent replay: {'passed' if isolated.get('independent_physics_replay') is True else 'pending'}. [Execution and rejection probes](execution/acceptance/original-isolated-closed-loop.json). This is privileged expert validation, not a public-agent score or OS sandbox.\n\n")
 original_portable=read(BASE/'acceptance/original-portable-download.json')
 if original_portable:
  d+=(f"[下载原版专家复现包]({original_portable['url']}) · [大小、SHA-256 与范围](execution/acceptance/original-portable-download.json) · [便携源码全流程运行验证](execution/acceptance/original-portable-validation.json)。包内含机器人资产及许可证、冻结专家与评分器、三次重复、独立回放、隔离执行、轨迹、视频和复现命令。\n\n" if zh else f"[Download original expert reproduction bundle]({original_portable['url']}) · [Size, SHA-256 and scope](execution/acceptance/original-portable-download.json) · [Fresh portable-source execution](execution/acceptance/original-portable-validation.json). Includes robot assets/licenses, frozen expert/scorer, three repetitions, replay, process-isolated execution, trajectories, videos and commands.\n\n")
 d+=('| 配置 | 自动验收门槛 | 人工视频复核 | 第二人复现 |\n|---|---|---|---|\n' if zh else '| Setting | Automatic gates | Human video review | Second-person reproduction |\n|---|---|---|---|\n')
 for row in r.get('qualification',[]):
  gates=row.get('automatic_gates',{});passed=sum(g['status']=='passed' for g in gates.values())
  d+=f"| {row['setting']} | {passed}/{len(gates)} | {'待完成' if zh else 'pending'} | {'待完成' if zh else 'pending'} |\n"
 d+='\n'
 portable=read(BASE/'acceptance/portable-download.json')
 if portable:d+=f"[Historical portable development scenes]({portable['url']}) · [SHA-256 / scope](execution/acceptance/portable-download.json)\n\n"
 d+='| Setting | '+('选定执行' if zh else 'Selected run')+' | '+('结果 / 中止原因' if zh else 'Result / stop reason')+' | '+('时长' if zh else 'Duration')+' | Hz | '+('独立回放' if zh else 'Replay')+' |\n|---|---|---|---|---|---|\n'
 for a in r['selected']:d+=f"| [{a['setting']}](#{a['setting'].lower()}) | {a['run']} | {'完整成功' if zh and a['success'] else 'success' if a['success'] else a['failure']} | {a['seconds']:.2f} s | {a['physics_hz']} | {'通过' if zh and a['independent_replay'] else 'pass' if a['independent_replay'] else 'not verified'} |\n"
 if zh:
  d+='''
## 实现与物理边界

原版从已有发布证据冻结源码，保持 Genesis 原评分器、资产与限制；专家修订另存冻结版本。扩展使用 MuJoCo 3.14.0，扩展证据包含历史 400 Hz 与新 2,000 Hz 执行，逐条频率见上表；均为 50 Hz 控制/状态记录、10 fps 视频。独立验证器从初始状态重放记录的执行器控制，逐步比较 qpos/qvel，检查载荷、速度、执行器限制和高低层轨迹覆盖；回放匹配不代表任务成功。

G/F 使用官方同一 G1 29-DOF 身体、分别绑定 Dex3 / Inspire DFQ 手。Inspire 关节耦合保留；Stretch 使用官方 Stretch 3 + SG3 资产、原传动及手指耦合。基座固定。扩展身体使用有界执行器；仅初始化设置状态，策略执行不写盘体位置/速度、不开对象焊接、不施加外部搬运力。转换适配与固定骨盆相邻外壳的碰撞排除写入各 run 的 model-binding.json。此证据不支持自由站立或硬件可行性的结论。

新场景共同使用 0.86 m 高桌面、近边 x=0.35 m、盘中心起点 (0.40, 0)、目标 (0.50, 0)。这是已有 50 mm 悬伸的开发场景；原版仍从 (0.50, 0) 推到边缘。G/F 的场景与物体保持相同；控制器可因手型调整。Stretch 起始站位迭代过，逐次 scene.xml 留档。当前结果不是统一策略的身体性能排名。

扩展阈值在各次 plan.json 中声明：盘线速度 ≤0.12 m/s、角速度 ≤0.65 rad/s、机器人总接触载荷 ≤18 N、桌面总载荷 ≤8 N；P3 每个接触刚体对盘的载荷模长之和 ≤4 N。机器人自接触与桌碰总载荷各 ≤20 N；失去全部支撑 >0.10 s 即失败。目标面偏差 ≤8°、目标平面误差 ≤45 mm、全盘位于桌面、无手接触、稳定 2 s。P3 的 4 N 是待完整见证校准的刚体损伤代理，不是材料断裂模型。

当前执行候选采用“抓持—抬升—翻转—放回”路径。最终开发评分器允许受控桌面翻转，lift 标志只作为诊断；本轮存档候选仍要求先抬升，Dex3 与 Stretch 的开发执行已观察到完整翻面，Stretch 进一步做到倒扣落桌；支撑交接、撤手及最终目标按配置单独验证，完整成功状态见上表。已增加桌边重抓、切向柔顺和按载荷交接的控制分支，失败阈值保持不变。

## 盘体设计已落实到碰撞几何

![盘体径向剖面](execution/plate-design/plate-cross-section.png)

- P1：直径 200 mm、厚 12 mm、质量 120 g。
- P2/P3：外径 200 mm、总高 20 mm、质量 120 g；盘底厚 4 mm；薄沿厚 6 mm，径向范围 79–100 mm；盘腔深 10 mm。底部支撑圈半径 53–60 mm、高 6 mm，形成 14 mm 沿下净空。
- 浅盘由底面与 32 段壁/沿/支撑圈凸体组合，保留凹腔和间隙；惯性为组合几何近似，局部重叠不代表精确实体 CAD。盘/桌的滑动摩擦系数设为 0.7，实际手接触还受官方手几何的接触混合参数影响，见 scene.xml。
- P1/P2 正放、倒扣各进行 5 s 无抓持支撑测试，末 2 s 稳定：4/4 通过。P3 复用 P2 几何。该探针仅验证支撑姿态；抓持、翻转和撤手仍须完成全流程验证。

[静态探针数值](execution/plate-design/support-probes.json) · [全部尝试台账](implementation.json) · [源代码：控制器](execution/source/run.py) · [模型](execution/source/model.py) · [独立验证器](execution/source/verify.py)

## 每个配置：计划、轨迹、物理与视频
'''
 else:
  d+='''
## Implementation boundaries

DF-01 uses frozen original Genesis sources and scoring. Extensions use MuJoCo 3.14.0: selected historical extension records use 400 Hz physics; new development runs use 2,000 Hz. Both use 50 Hz control/trace and 10 fps video. Independent replay compares every qpos/qvel sample from a fresh initial state, and checks actuator limits, contact loads and high/low coverage. Replay agreement is not task success. Official G1 Dex3/Inspire bodies share the same 29-DOF base; Stretch 3 uses official SG3 geometry and linkage. Bases are fixed. All model adaptations and effort limits are recorded per run. No hardware or free-standing feasibility is claimed.

Extension start (0.40, 0) has 50 mm overhang at the x=0.35 m table edge; target is (0.50, 0), table height 0.86 m. Original DF-01 still pushes from (0.50, 0). G/F share the world and object; hand-specific controllers may differ. Stretch base placement changed during development. This is not a common-policy embodiment ranking.

Per-run plans declare linear/angular speed caps of 0.12 m/s and 0.65 rad/s; robot/table contact sums of 18/8 N; P3 additionally caps each contacting body at 4 N. Self/table collision loads above 20 N or unsupported time above 0.10 s fail. The goal requires ≤8° normal error, ≤45 mm planar error, whole-disk tabletop containment, full release and 2 s stability. P3 is a provisional rigid-body load proxy, not fracture simulation.

The executed candidate uses grasp–lift–turn–place. The final development scorer permits controlled supported turnover with lift only a diagnostic. Dex3 and Stretch development attempts have reached full inversion, and Stretch has reached inverted setdown. Support transfer, release and the final goal are checked independently for each setting; see the verified witness table. Edge regrasp, tangential compliance and load-based release are under development; no failed attempt is relabeled successful.

## Physical disk design

![Radial cross section](execution/plate-design/plate-cross-section.png)

P1: 200 mm diameter, 12 mm thick, 120 g. P2/P3: 200 × 20 mm, 120 g; 4 mm floor, 6 mm rim over radii 79–100 mm, 10 mm cavity, support-ring radii 53–60 mm and height 6 mm, 14 mm under-rim clearance. Separate convex sectors retain the cavity/gaps; compound inertia is an approximation with overlapping components, not exact solid CAD. Object/table sliding friction is 0.7; effective hand friction also depends on imported contact parameters. Four 5 s upright/inverted static support probes passed (P1/P2, final 2 s stable). This is not a complete grasp/flip/release witness.

[Support probes](execution/plate-design/support-probes.json) · [All attempts](implementation.json) · [Controller](execution/source/run.py) · [Model](execution/source/model.py) · [Verifier](execution/source/verify.py)

## Per-setting plans, trajectories, physics and videos
'''
 for a in r['selected']:
  setting=a['setting'];p=a['evidence'];src=BASE/'runs'/a['run'];v=a['verification'];mapping=read(src/'high-low-trajectory.json')
  d+=f'\n<h3 id="{setting.lower()}">{setting} · {LABELS[setting] if zh else a["run"]}</h3>\n\n'
  outcome=('完整成功；独立动作回放通过。' if zh else 'Complete success; independent action replay passed.') if a['success'] else (f"候选失败：`{a['failure']}`，停止于 {a['seconds']:.2f} s。尚无完整物理可行性见证。" if zh else f"Failed candidate: `{a['failure']}` at {a['seconds']:.2f} s. No complete feasibility witness yet.")
  d+=outcome+'\n\n'
  if read(src/'plan.json').get('controller_tuning',{}).get('reference_prefix_file'):
   d+=('策略范围：固定标称关节参考前缀，再根据实测状态完成撤手；每个物理步重新执行并评分。这是标称物理见证，不是可泛化的闭环策略。\n\n' if zh else 'Policy scope: fixed nominal joint-reference prefix followed by measured-state withdrawal. Every physics step is freshly executed and scored. This is a nominal physical witness, not a generalizing closed-loop policy.\n\n')
  for alternate in r.get('additional_witnesses',[]):
   if alternate['setting']!=setting:continue
   ap=alternate['evidence'];am=alternate['media'];policy=('固定标称参考前缀' if zh else 'fixed nominal reference prefix') if alternate['fixed_reference_prefix'] else ('在线专家' if zh else 'online expert')
   d+=(f"补充完整见证：**{alternate['run']} · {policy} · {alternate['seconds']:.2f} s**。独立物理回放与紧凑参考回放均通过；当前冻结验收队列保持独立记录。\n\n" if zh else f"Additional complete witness: **{alternate['run']} · {policy} · {alternate['seconds']:.2f} s**. Independent native and compact-reference replays passed; the frozen qualification cohort remains separately tracked.\n\n")
   d+=f"[Video]({am['video']['url']}) · [Plan]({ap}/plan.json) · [High/low → trajectory]({ap}/high-low-trajectory.json) · [Verification]({ap}/verification.json) · [Reference replay]({ap}/reference-replay-verification.json) · [Trajectory]({am['trajectory']['url']}) · [Frozen sources]({am['sources']['url']}) · [SHA-256]({ap}/external-media.json)\n\n"
  download=read(BASE/'acceptance'/f'portable-{setting}-download.json')
  if download.get('url'):
   d+=f'[Portable frozen expert]({download["url"]}) · [SHA-256 / scope](execution/acceptance/portable-{setting}-download.json)\n\n'
  d+=f'<video controls preload="none" playsinline poster="{a.get('image_urls',{}).get('initial.png',p+'/initial.png')}" src="{a['video_url']}"></video>\n\n'
  d+=f'[{"计划" if zh else "Plan"}]({p}/plan.json) · [High/low → trajectory]({p}/high-low-trajectory.json) · [{"独立验证" if zh else "Verification"}]({p}/verification.json) · [Summary]({p}/summary.json) · [50 Hz trace / scope]({p}/trace-scope.json) · [Video]({a['video_url']})\n\n'
  d+='Trajectory: '+' · '.join(f'[{x["file"]}]({x.get("url",p+"/"+x["file"])})' for x in a['trajectory_parts'])+f' · [SHA-256 / replay]({p}/'+('trajectory-download.json' if a['setting']=='DF-01-G' else 'trajectory-reference.json')+')\n\n'
  if a['setting']!='DF-01-G':d+=f'[Reference replay verification]({p}/reference-replay-verification.json) · [Replay script](execution/source/compact_evidence.py)\n\n'
  d+='Trace: '+' · '.join(f'[{x["file"]}]({x.get("url",p+"/"+x["file"])})' for x in a['trace_parts'])+'\n\n'
  if a.get('source_bundle'):d+=f'[Frozen execution sources]({a["source_bundle"]["url"]}) · [External artifact hashes]({p}/external-media.json)\n\n'
  d+=f'![{setting} trajectory]({a.get('image_urls',{}).get('trajectory.png',p+'/trajectory.png')})\n\n'
  d+='| High level | Low level | Time (s) | '+('状态' if zh else 'State')+' |\n|---|---|---|---|\n'
  for x in mapping:
   times=x.get('time_interval_s',x.get('time_interval'));d+=f"| {x['high_level']} | {x.get('id',x.get('low_level'))} · {x['phase']} | {times[0]:.2f}–{times[1]:.2f} | {'completed' if x.get('completed',True) else 'interrupted'} |\n"
  if not a['success']:d+=('\n尚未执行的计划段不显示为已完成；全部预期动作见 plan.json。优先展示独立验证的完整成功、其次翻面与抬盘阶段证据、再取较新版本；历史修订见执行台账。\n' if zh else '\nUnexecuted planned actions are not shown as completed; see plan.json for the full candidate.\n')
 if zh:d+='''
## 尚需解决

- 五指手需要结合实际指长与耦合重新设计接近/夹持，避免双手相撞；单手候选也必须证明受力闭合。
- P2/P3 需同时控制盘沿夹持、底面与支撑圈接触，建立可保持的安全载荷余量。静态支撑通过不能证明可抓取。
- 逐配置核对稳定抓持、支撑交接、撤手与完整目标；只有连续执行和独立回放均通过才计入完整见证。
- 完整见证建立后，才能冻结扩展协议、开展配对比较与不同初始条件测试。所有 privileged expert 代码、初态和轨迹只供作者验证，不进入 agent bundle。

## 复现限制

每条证据提供源码、场景、初态、控制参考序列、物体轨迹、验证报告与哈希。受托管包大小限制，扩展下载包保存每个 50 Hz 控制周期的保持参考和端点物体状态；回放脚本按对应场景的 400 / 2,000 Hz 步长重建全部关节状态与执行器控制，逐数组 SHA-256 与原始执行完全一致（逐条链接验证报告）。原版仍提供原生控制轨迹。网页 trace 保留 50 Hz 物体状态与聚合载荷，省略重复的逐接触明细。完整原始 NPZ/JSONL 继续保存在本地 `df_family/runs/`，没有被覆盖。已额外构建 5 个扩展开发场景的便携资产包：299 个去重资产、相对路径、上游许可证，编译后的物理数组与原场景逐项相同。它用于复现开发场景，不是通过验收的专家包；网页中的逐 run 原始 scene.xml 仍保留当时路径。
'''
 else:d+='''
## Remaining work and reproduction

Resolve hand-specific approach and force closure, preserve safe P2/P3 load margin, and complete turnover, support transfer and withdrawal for dual/single-arm candidates. Full witnesses are needed before protocol freeze, paired comparisons and initial-condition robustness tests. All privileged expert artifacts remain author-only and excluded from agent bundles.

To fit hosting limits, extension downloads retain every held 50 Hz reference and endpoint object state. The replay script reconstructs all joint states and actuator controls at each scene’s declared 400 / 2,000 Hz rate; every reconstructed array SHA-256 matches the original execution (see each linked report). Original DF-01 retains its native control trajectory. Public traces retain 50 Hz object states and aggregate loads, omitting repetitive individual contact lists. Full original NPZ/JSONL files remain unchanged in local df_family/runs/. A separate portable development bundle contains five extension scenes, 299 deduplicated assets, relative paths and upstream licenses; compiled physical arrays match the originals. It is a development scene bundle, not a qualified expert bundle. Archived per-run scenes retain their original paths.
'''
 return d
if __name__=='__main__':main()
