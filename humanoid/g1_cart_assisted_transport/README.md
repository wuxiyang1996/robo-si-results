# Version C â€” G1 Cart-Assisted Heavy Object Transport

**First-layer reference scope (2026-10-24):** The frozen `transport-layout-v2` candidate passed **5/5 primary full runs**, **20/20 independently started subtasks**, and **5/5 author-machine reproduction cases**. All recorded full-run repeats are **14/15**; the failed repeat remains in the evidence. The canonical controller and its 43-file reference source closure now match that candidate. See [reference evidence](acceptance/integration-20261024/evidence.json) and [integration closeout](acceptance/closeout-20261024/README.md) for current validation and packaging results. Human review and second-person reproduction remain pending, with `admitted=false`; R9 and layers 2/3 are deferred. Historical development results below remain separate evidence.


**Category:** Tool Discovery Â· **Embodiment:** Humanoid Â· **Task ID:** H2 Â· **Priority:** P0 â€” priority implementation

**Status:** Genesis and Isaac Lab environments implemented locally. The scorer requires the cargo supported on the cart at delivery (2026-10-20). Since 2026-10-21 the default scene is the rails dock (`TaskConfig.dock='rails'`): a 20 kg crate with friction 0.5 and an estimated 91 N floor-drag requirement (physical shortcut audit remains necessary), roller rails that lead it onto the dolly's roller deck, push blocks on the crate, and one-sided lane guide curbs, so the difficulty lies in the steps (load, route, detours) rather than in steering the dolly. The cart-required expert (`solution/floor_push/run_grasp_push.py`) passes in it (`rails-v10` 77.8 s; then `rails-v14` 94.6 s, `rails-v15` 75.4 s, `rails-v16` 70.1 s, `rails-v18` 70.0 s and `rails-v19` 82.2 s, 5 passes in the last 6 runs; audits passed; repeats in `solution/expert_progress.json`). The previous wedge scene (`dock='wedge'`) and its passes (`cart-v54`, `cart-v109`, `cart-v112`, `cart-v114`) are kept; see `solution/FEASIBILITY_CONDITIONS.md`. The Isaac backend has not been run with either cart scene and refuses the rails dock.

A single Unitree G1 must transport a heavy box beyond its direct carrying capacity to a designated target region. A movable cart is available in the environment, but the route includes narrow passages, so simply pushing the box in a straight line cannot reach the goal.

## Task

- The G1 cannot lift the box directly. Through physical interaction, the agent must discover its own payload limit and independently recognize the cart as an auxiliary transport tool.
- The agent explores how to load the box onto the cart, for example by pushing, tilting, lifting in stages, or using environmental supports. Loading must not assume that the robot can lift the entire box directly.
- The agent independently writes a cart-control harness that coordinates the G1's movement, applied pushing force, contact location, and the cart's motion for stable transport. The cart moves through physical robot contact, not direct commands that bypass the G1's capabilities.
- In narrow passages, the agent must account for cart dimensions, box orientation, turning radius, and the G1's mobility. It may need to reposition, change pushing direction, or make repeated pose adjustments.

Loading and maneuvering examples are candidate strategies for benchmark design, not a prescribed solution or hints supplied in the evaluation instruction. The agent must discover the cart's usefulness and the conditions under which it works.

## Advanced Variants

Vary box mass, cart payload capacity, wheel friction, passage width, and robot pushing-force limits. Every admitted variant must retain at least one physically executable solution with the available controller and scene resources. Test whether the agent discovers tool-use conditions, identifies causes of control failure, and modifies its harness.

Physical feasibility remains to be validated. Confirm both that direct lifting exceeds the robot's capability and that loading, cart transport, and final delivery are executable. Check cart stability and load capacity, wheel behavior, box retention, robot balance, contact forces, and clearance for the combined robotâ€“cartâ€“box system. Provide usable environmental supports when a validated loading route requires them.

## Evaluation Contract

Deliver the heavy box into the designated target region through continuous physical interaction while respecting declared collision, stability, and load constraints. Unless an instance explicitly requires unloading, delivery with the box stably supported on the cart is valid. Do not silently introduce an unloading requirement that exceeds the robot's capability.

Define numerical tolerances, the required final dwell time, and permitted contacts before evaluation. Allow valid alternative loading and maneuvering strategies. Record robot actions, contact changes, repositioning, failures, recovery attempts, and interaction costs. Success must not rely on state edits, direct cart actuation, or contact bypasses.

Evaluate whether the agent distinguishes robot pushing or lifting limits from cart overload, wheel friction, poor contact, and geometric obstruction using the observations available in its track. Capability and world-property variants should change physical or controller behavior, not just descriptive metadata.

## Implementation Priorities

- [x] Build matching Genesis / Isaac Lab scenes with G1, heavy box, passive cart, staggered narrow passages, and target region.
- [ ] Validate the direct-lifting limitation and at least one feasible loading strategy.
- [ ] Validate contact-driven cart motion, stable transport, passage negotiation, and final delivery.
- [x] Provide joint-only control, state observations, dwell-based success and constraint checks.
- [ ] Add advanced variants with verified feasible solutions, then evaluate tool discovery, failure diagnosis, and agent-written harness adaptation.

## Core Capabilities Evaluated

Autonomous Tool Discovery Â· Physical Reasoning Â· Harness Construction Â· Load and Mobility Constraints Â· Embodied Self-Modeling Â· Long-Horizon Planning

See the [Tool Discovery category](../../README.md#tool-discovery) and the benchmark proposal in [English](../../doc/self-modeling-benchmark-v4-en.html#humanoid-h2) or [ä¸­æ–‡](../../doc/self-modeling-benchmark-v4-zh.html#humanoid-h2).

## Running the dual-backend environment

Run PowerShell from `D:/rsi_vla/robo-si`:

```powershell
$env:OMNI_KIT_ACCEPT_EULA = 'YES' # existing locally accepted Isaac installation
.\humanoid\g1_cart_assisted_transport\scripts\run.ps1 -Sim both
.\humanoid\g1_cart_assisted_transport\scripts\run.ps1 -Sim genesis -NumEnvs 1 -Steps 3000 -Viewer
.\humanoid\g1_cart_assisted_transport\scripts\run.ps1 -Sim isaac -NumEnvs 1 -Steps 3000 -Viewer
```

`both` runs the two backends sequentially in their separate Python environments. Override paths with `-GenesisPython` or `-IsaacPython`. `-Primitive` displays the collision proxies without downloaded visual meshes. The default pose is a scene probe, not a transport controller. First-time Genesis compilation can take several minutes.

The G1 MJCF and converted USD are reused from H1. Downloaded visual assets have already been prepared on this machine. On a fresh checkout, follow the H1 asset setup instructions, then run:

```powershell
& "$env:USERPROFILE\anaconda3\envs\isaaclab\python.exe" .\humanoid\g1_cart_assisted_transport\scripts\prepare_assets.py
```

Preparation uses the installed Isaac Python USD libraries without starting Kit, plus numpy, trimesh and Pillow. No Blender is needed. Poly Haven downloads use 1K textures and verify the API's MD5 hashes. SHA-256 checksums for all downloaded files are recorded in `assets/visuals/downloads.json`.

## Existing assets and individual scene parts

Enabled by default with `TaskConfig(asset_visuals=True)`. See [asset_sources.json](asset_sources.json) for original URLs, authors, licenses and adaptations. Downloaded third-party files and generated conversions are excluded from git.

| Scene part | Source | Adaptation |
|---|---|---|
| Chassis, four individual wheels, caster brackets | NVIDIA Dolly | Extracted USD meshes, fitted to H2 chassis and wheel links |
| Physical U-shaped handle | Locally authored geometry | Three visible cylinder colliders on a 1 kg link fixed to the chassis; identical dimensions in both backends |
| Loading support and cart bearing surface | NVIDIA warehouse pallet | Separate full-height support and thin deck-insert variants |
| Heavy cargo | Poly Haven Wooden Crate 02 | Textured mesh, 25 kg dynamic box collision proxy |
| Eight shelving modules | Poly Haven Steel Frame Shelves 01 | Individual modules; five shelf boards and four uprights each have collision proxies |
| Sixteen storage bins | Poly Haven Plastic Crate 01 | Separate visual instances and fixed box collision proxies |
| Floor and perimeter walls | Poly Haven Concrete Floor 02 / Painted Plaster Wall | Downloaded diffuse textures on locally generated geometry |

The Sketchfab candidate's official download API returned HTTP 401, requiring authorized login; NVIDIA Dolly is used instead. NVIDIA assets retain their separate license, while the listed Poly Haven assets are CC0. Neither the textures nor third-party models are claimed as original repository assets.

Rack depth is 0.45 m and the two offset passages are 1.25 m wide. Shelf gaps are physical gaps, not invisible solid walls. Storage bins are fixed scenery, not additional movable tools. Pallet and cargo collision shapes remain simplified. The source Dolly's swivel-joint dynamics are not imported: the current cart retains H2's four passive fixed-direction wheel axes. Turning therefore requires frictional sliding. The wood insert makes the visible bearing surface agree with the solid deck collision proxy.

Both backends load the same prepared textured OBJ geometry. Isaac generates corresponding USD meshes with UsdPreviewSurface materials and repeating UV textures. This implementation preserves diffuse appearance; it does not reproduce all original PBR shader channels. Lighting and tone mapping differ between simulators.

Previews: [Genesis](media/assets-genesis.png), [Isaac Lab](media/assets-isaac.png).

## Scene and control contract

- Cargo: 25 kg, 0.48 x 0.44 x 0.40 m, initially on a 0.23 m loading support. The empty cart is parked at (2.6, 1.5) m, away from the cargo and direct route, so loading requires repositioning. This is a candidate layout, not a validated loading solution.
- Cart: 12 kg chassis, 0.90 x 0.60 x 0.06 m; four 0.5 kg wheels of radius 0.08 m; 1 kg fixed U-shaped handle, for 15 kg total empty mass. The handle crossbar is 0.52 m wide, 0.85 m above the floor at reset, and 0.036 m in diameter. Both posts and the crossbar have physical collisions and can transmit contact forces to the chassis. No action directly commands the cart.
- Actions: 43 joint targets in `robot.JOINT_NAMES` order. Targets are `default_q + 0.25 * action`; actions are clipped to +/-20 and targets to joint limits. Finite actuator effort limits follow the H1 motor model.
- Timing: 200 Hz physics, 50 Hz control, 120 s timeout.
- Observations: 183 values: joint positions 43, joint velocities 43, previous actions 43, robot/cargo/cart body states 13 each, four wheel positions and velocities 8, cart support/floor support/non-foot impact forces 3, goal XY 2, loaded-history flag and dwell time 2. Body states are local position, wxyz quaternion, linear velocity and angular velocity.
- Success: all eight cargo corners lie within the 1.40 x 1.40 m goal; cargo is upright, speed < 0.08 m/s and angular speed < 0.15 rad/s, and supported by the cart or floor with at least half its weight for 2 s. Delivery on the cart is valid. Other physically valid delivery strategies are not rejected merely for omitting the cart.
- Failure: robot fall, cart tip, out-of-bounds bodies, nonfinite states, non-foot contact force > 800 N, or loading above the declared cart capacity. Default capacity is 40 kg; this is an evaluation constraint, not a structural failure simulation.
- Rewards: first success +20, first failure -10. Auto-reset preserves terminal states in `extras['final_observation']` with its mask.

```python
import torch
from humanoid.g1_cart_assisted_transport.genesis_env import G1CartAssistedTransportGenesis

env = G1CartAssistedTransportGenesis(num_envs=2)
try:
    obs, reward, done, extras = env.step(torch.zeros(2, 43, device=env.device))
    obs = env.reset([0])
finally:
    env.close()
```

For Isaac, start AppLauncher before importing `G1CartAssistedTransportIsaac`. Its step/reset contract is the same. This is a full-state development interface, not an isolated anti-cheating evaluation sandbox.

## Validation and limits

For asset revision 2, the three handle structural tests pass in the installed
Isaac Python environment, including URDF/USD geometry and inertial equivalence.
The Genesis [handle contact fixture](solution/runs/handle-asset-smoke-v2/report.json)
also passes: contact with only the crossbar moves the cart, with no relative
handle/deck drift. See its [close-up](solution/runs/handle-asset-smoke-v2/handle_closeup.png).
This deliberately isolated fixture is not a robot grasp or task solution.
Isaac physics with the new handle has not yet been revalidated; older backend
reports below describe the previous cart asset.

```powershell
python -m unittest discover -s tests -p test_cart_assisted_transport.py
```

Nine regression tests pass, including dwell, support, falls, overload, whole-box containment, shelf gaps and passage clearance. Each backend has also completed two-instance physical smoke tests: 50 control steps, partial-reset isolation, followed by independent cart-load and floor-support fixtures. Representative 25 kg support measurements are approximately 245.25 N in Genesis and 245 N in Isaac. Reports are in `media/extended-genesis.json` and `media/extended-isaac.json`.

Diagnostic load/floor fixtures directly place cargo in test code and are explicitly not robot task solutions. Successful reports contain `checks_passed`; the launcher checks both that flag and report modification time so a stale file cannot count as a new pass.

Isaac uses a separate fixed ground body per environment for reliable filtered contact-force reporting and physics cloning. Preview defaults use D3D12 and a single GPU on Windows. Both textured previews have been rendered and inspected. Close callbacks are cleared before shutdown to avoid Isaac Lab's render-on-stop loop.

Still unvalidated: direct-lift infeasibility across allowable robot configurations, robot-driven loading, contact-driven turning through both passages, and a complete transport solution. Mass/friction/damping variants change physical behavior but have not been certified solvable. Asset adaptation and smoke tests do not establish benchmark feasibility.

### Extended, less explicit layout

The room is 10.5 x 5 m (previously 8.5 x 5 m), with offset passages at x=4.5 and 7.4 m and the delivery target at (9.45, 0.70) m. The cart is parked in a side bay without a tool-use marker. Two additional fixed pallets and four individual storage bins reuse the existing downloaded assets; all have collision proxies. These stored props are scenery. The original loading pallet remains beneath the movable cargo. There are 8 rack modules and 20 storage bins in total. Floor visuals, physical floor, room bounds, cameras and instance spacing follow the extended layout. Cargo delivery on the floor remains valid; cart use is not a required success condition.

### Expert-reference development

Asset revision 2 adds the physical handle requested during expert development.
The graspable tube geometry, hollow-tube inertia, fixed mount and added mass are
shared by the URDF and USD generators. Motion planners include all three handle
colliders and refresh them from the measured cart pose. Historical runs below
used the previous cart without this physical handle; they are not validation of
the revised cart. Full loading and transport remain unvalidated. Current status
is tracked in [solution/expert_progress.json](solution/expert_progress.json).

Local candidate controllers and measured results are documented in
[solution/README.md](solution/README.md). A default-start Genesis rollout has
executed navigation, full-body crouching, hand-contact-driven empty-cart motion,
release, and recovery using only the original joint-action interface. This is a
partial manipulation milestone. A separate default-start cargo rollout has now
pushed the original 25 kg box 8.59 mm on its pallet, withdrawn the hands and
recovered standing with a two-second settled endpoint. This is one short
physical primitive; cart docking, cargo loading, passage transport,
and full task success remain unverified. Saved open-loop actions are not a
certified replay policy; use the feedback controller and inspect each run report.

A subsequent default-start foot-push rollout moved the empty cart 0.604 m
including passive coasting, then completed withdrawal, measured landing and a
two-second settled standing recovery in 42.92 s. Original dynamics and actuator
limits were unchanged. Its video and recorded actions/observations are in
`solution/runs/foot-cart-v5`; this adds an empty-cart primitive, while full cargo
delivery remains unverified.
