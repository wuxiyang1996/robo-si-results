"""Two-G1 opening milestone: A opens while B actively balances on the shared clock."""
import argparse,hashlib,json,traceback,shutil
from pathlib import Path
from .genesis_env import DualDoorWorld
from .task_spec import TaskConfig,VARIANTS
from .reference import CooperativeReference
from .hold_door import HoldDoor
from humanoid.g1_self_closing_door.solution.expert_nav import navigate
from humanoid.g1_self_closing_door.solution.expert_skills import tuck_arms
from humanoid.g1_self_closing_door.solution import walk_bar_pull as W
from humanoid.g1_self_closing_door.solution.run_expert import jsonable
from infra.sandbox.pipeline import _sources


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--variant',choices=VARIANTS,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--camera',action='store_true')
    ap.add_argument('--video',action='store_true',help='record actual native physics at 10 fps')
    ap.add_argument('--stand-only',action='store_true')
    ap.add_argument('--hold-seconds',type=float,default=0.)
    ap.add_argument('--peer-cross',action='store_true')
    ap.add_argument('--deliver',action='store_true')
    ap.add_argument('--fetch-only',action='store_true',help='full reset pickup diagnostic, A actively stands; no opening/delivery claim')
    ap.add_argument('--prop-prepare',action='store_true')
    ap.add_argument('--peer-preposition',action='store_true')
    ap.add_argument('--heavy-deliver',action='store_true',help='after crate placement: A releases, B parks, A delivers parcel')
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    if not 0<=args.hold_seconds<=60:ap.error('hold duration outside [0,60] s')
    if args.peer_cross and args.hold_seconds<4:ap.error('peer crossing requires at least 4 s holding preparation')
    if args.deliver and (args.variant!='no_prop' or args.peer_cross or args.hold_seconds<4):
        ap.error('parcel continuation currently requires no_prop, held-door preparation and no empty-crossing detour')
    if args.fetch_only and (args.deliver or args.peer_cross or args.stand_only or args.hold_seconds):
        ap.error('fetch-only is a separate full-reset milestone')
    if args.prop_prepare and (args.variant!='heavy_prop' or not args.peer_cross):ap.error('crate preparation requires heavy_prop and peer-cross')
    if args.peer_preposition and not args.prop_prepare:ap.error('preposition currently belongs to the heavy-crate reference')
    if args.heavy_deliver and not args.prop_prepare:ap.error('heavy delivery requires prop-prepare and its physical prerequisites')
    args.camera=args.camera or args.video
    root=Path(__file__).resolve().parents[2];cfg=TaskConfig(args.variant)
    write=lambda name,value:(args.out/name).write_text(json.dumps(jsonable(value),indent=1)+'\n',encoding='utf8')
    write('configuration.json',cfg.manifest())
    dependencies=['multi_robot/dual_g1_self_closing_door','humanoid/g1_self_closing_door',
                  'humanoid/g1_support_retrieval','humanoid/g1_ramp_bridge_construction','infra/sandbox']
    sources={path:_sources(root/path) for path in dependencies}
    write('source-hashes.json',sources)
    for directory,files in sources.items():
        for name in files:
            target=args.out/'sources'/directory/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/directory/name,target)
    packages={}
    for name in ('humanoid/__init__.py','infra/__init__.py'):
        packages[name]=hashlib.sha256((root/name).read_bytes()).hexdigest()
        target=args.out/'frozen-package-markers'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(root/name,target)
    write('package-hashes.json',packages)
    world=DualDoorWorld(cfg,camera=args.camera);reference=None;video=None;log={};hold_log={};delivery_log={};prop_log={};result={}
    try:
        from .assets import inventory
        asset_set=inventory(cfg.manifest());asset_set['note']='captured after native construction, before the first physics step'
        write('asset-hashes.json',asset_set)
        for name in asset_set['files']:
            target=args.out/'frozen-assets'/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(root/name,target)
        reference=CooperativeReference(world);robot=reference.robots['g1_a']
        if args.video:
            from humanoid.g1_support_retrieval.solution.step_up.video import VideoWriter
            video=VideoWriter(args.out/'motion.mp4',fps=10);reference.video=video
            video.append_data(world.cam.render()[0])
        for _ in range(25 if not args.stand_only else 100):
            if not robot.step():raise RuntimeError(reference.failure)
        if args.camera:
            from PIL import Image
            Image.fromarray(world.cam.render()[0]).save(args.out/'initial.png')
        if args.stand_only:
            result=dict(ok=True,reason='shared-clock reference standing only')
        elif args.fetch_only:
            from .delivery import fetch
            fetched=fetch(reference.robots['g1_b'],delivery_log)
            result=dict(ok=bool(fetched.ok),reason=fetched.reason)
        else:
            if args.peer_preposition:
                from .approach import WaitNearDoor
                prop_log['preposition']={}
                reference.background['g1_b']=WaitNearDoor(reference.robots['g1_b'],prop_log['preposition'])
            outcome=W.run(robot,log,open_goal=1.2,timeout=35.,follow_mode='hook',load_gain=0.,max_bias=.0004,
                          walking_yaw=60.,max_open_rate=.12)
            reference.background.pop('g1_b',None)
            result=dict(ok=bool(outcome.ok),reason=outcome.reason)
            if outcome.ok and args.hold_seconds:
                controller=HoldDoor(robot,log,hold_log);reference.background['g1_a']=controller
                peer=reference.robots['g1_b'];peer.phase='peer_wait_for_held_door'
                # Preparation includes quiet capture and the QP blend. Allow
                # these to settle before requiring a full measured 2 s dwell.
                for i in range(round(max(args.hold_seconds,8.)/.02)):
                    if not peer.step():raise RuntimeError(reference.failure)
                    if (i+1)*.02>=args.hold_seconds and controller.stable>=2.:break
                result=dict(ok=controller.stable>=2.,reason='held-door dwell after shared-clock peer control' if controller.stable>=2. else 'held-door dwell under 2 s')
                if result['ok'] and args.peer_cross:
                    peer.phase='peer_tuck_for_crossing'
                    tucked=tuck_arms(peer,seconds=2.)
                    if tucked is not True:raise RuntimeError('peer arm tuck failed: '+str(tucked))
                    peer.phase='peer_empty_crossing'
                    # Stop before the crate's near corner so the subsequent
                    # aisle turn clears the complete tucked arm envelope.
                    crossing=navigate(peer,[3.5,.3],0.,timeout=25.,exclude=('box',),speed=.3)
                    hold_log['peer_crossing']=dict(ok=crossing.ok,reason=crossing.reason,metrics=crossing.metrics)
                    result=dict(ok=bool(crossing.ok and peer.pos[0]>3.2),reason='peer empty crossing while A holds door' if crossing.ok else crossing.reason)
                    if result['ok'] and args.prop_prepare:
                        from .prop import prepare
                        prepared=prepare(peer,prop_log)
                        result=dict(ok=bool(prepared.ok),reason='crate preparation while A holds' if prepared.ok else prepared.reason)
                        if result['ok'] and args.heavy_deliver:
                            from .release_door import release
                            prop_log['release']={}
                            released=release(robot,controller,prop_log['release'])
                            result=dict(ok=bool(released.ok),reason=released.reason)
                            if result['ok']:
                                peer.phase='peer_clear_parcel_route'
                                parked=navigate(peer,[4.05,-1.15],0.,timeout=18.,speed=.3,via=[[4.05,-.33]])
                                prop_log['parking']=dict(ok=parked.ok,reason=parked.reason,metrics=parked.metrics)
                                result=dict(ok=bool(parked.ok),reason=parked.reason)
                            if result['ok']:
                                from .delivery import run
                                robot.hold_legs(False)
                                delivery_log['roles']=dict(carrier='g1_a',crate_placer='g1_b')
                                delivered=run(robot,delivery_log)
                                result=dict(ok=bool(delivered.ok),reason=delivered.reason)
                if result['ok'] and args.deliver:
                    from .delivery import run
                    delivered=run(peer,delivery_log)
                    result=dict(ok=bool(delivered.ok),reason=delivered.reason)
    except Exception as error:
        traceback.print_exc();result=dict(ok=False,reason=f'{type(error).__name__}: {error}')
    finally:
        if args.camera:
            from PIL import Image
            Image.fromarray(world.cam.render()[0]).save(args.out/'final.png')
        score=world.score.info()
        result.update(variant=args.variant,seconds=world.t,task_success=score['success'],score=score,
                      scope='native heavy reference candidate; not isolated sandbox or release' if args.heavy_deliver else
                            'crate preparation while A holds; no unassisted prop or delivery' if args.prop_prepare else
                            'full-reset pickup diagnostic; no opening or delivery' if args.fetch_only else
                            'native reference delivery candidate; not isolated sandbox or release' if args.deliver else
                            'shared-clock standing' if args.stand_only else 'opening/holding/optional empty crossing milestone; no prop or delivery',
                      diagnostic_failure=None if reference is None else reference.failure)
        write('result.json',result);write('opening.json',log);write('holding.json',hold_log)
        write('delivery.json',delivery_log)
        write('prop.json',prop_log)
        if reference:
            write('trace.json',reference.rows);write('commands.json',reference.commands)
        if video is not None:video.close()
        world.close()
        write('files.json',{p.relative_to(args.out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in args.out.rglob('*') if p.is_file() and p.name!='files.json'})
    print(json.dumps(result,indent=2),flush=True)
    return 0 if result['ok'] else 1

if __name__=='__main__':raise SystemExit(main())
