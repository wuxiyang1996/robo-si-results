# Sokoban: From Local Views to a Global Map

Design version: 2026-10-29 · Status: formal review preparation and continuous physical validation in progress

[Current acceptance checklist and all attempts](../../task-sokoban-acceptance-en.html) · [Earlier expert plans, trajectories and videos](../../task-sokoban-progress-en.html). This document defines the task; individual evidence determines execution status.

Can multiple robots build a consistent, updatable global map from their own local observations and use it to clear routes by pushing crates? Does communication improve mapping and execution? Can agents create useful mapping, fusion or planning software when needed?

## 1. Task and boundaries

Two robots explore walls, corridors and movable crates, clear routes through physical pushing, and dwell stably at their respective goals at the same time. Crates have no delivery targets. The first configuration is G1 + G1.

- **Inputs:** own local RGB, joint and inertial observations, own goal identity, and explicitly received messages when communication is enabled.
- **Hidden information:** the complete map, ground-truth crate poses, hidden peer state and evaluator feedback. Ground truth belongs to the environment and evaluator only.
- **Actions:** controller-driven physical contact; crates may be pushed, but not grasped, pulled, lifted or moved through state writes.
- **Success:** simultaneous own-goal arrival with dwell, stability and physical-validity checks. Retain the native L1 requirement of 2 seconds of simultaneous dwell; freeze new-level parameters before evaluation.
- **Global mapping:** connect local views into a consistent spatial representation, distinguish known from unknown, and update traversability after crates move. Grids, topological maps and other queryable representations are allowed.

Global mapping does not mean supplying an overhead image or a ground-truth map. Declare retained perception assumptions, including known grid spacing, flat ground and color coding. Removing them requires a separate experiment.

## 2. Three difficulty levels

| Task ID | Configuration | Main capability | Current status |
| --- | --- | --- | --- |
| SK-L1 | Fixed four-crate development layout; two G1s | Local exploration, mapping, pushing and arrival | Historical and new goal-arrival records retained; complete validity certification pending |
| SK-L2 | Unseen topologies; two G1s; occlusion, branches, shared bottlenecks and alternate routes | Global consistency, map fusion, dynamic updates and replanning | Three development families implemented; held-out generalization pending |
| SK-L3 | Matched maps with changed robot geometry or capability constraints | Embodiment-dependent reachability and role allocation | Two-G1 arm-effort reversal development pairs executed; capability inference and role adaptation pending |

L1 already includes local exploration and explicit messaging. L2 adds generalization to unseen topology, beyond hiding a development map from the agent. Begin L3 with controlled capability changes to two G1s, then introduce heterogeneous robots after validation. Do not assume one platform is narrower or stronger.

## 3. Communication and tools are separate factors

| Condition | Information and permissions | Purpose |
| --- | --- | --- |
| C+: explicit communication | Private workspaces and local views, with bounded messages | Measure benefits from map evidence sharing, exploration coordination and role allocation |
| C−: no explicit communication | Same inputs and budgets, message API disabled; peer motion remains visible | Measure independent mapping and implicit coordination |
| Self-built tools: main setting | Both communication conditions allow private sandbox programs | Observe creation of maps, fusion code, planners or protocols when useful |
| Fixed toolset: optional ablation | Both groups receive the same frozen tools; restrict new executable tools while preserving normal policy reasoning | Isolate the value of tool construction |

Communication does not itself construct a tool. C+ agents may exchange map fragments, interface agreements or code text within the message budget, without a shared filesystem or hidden channel. C− agents can still build tools independently.

Keep tool permissions identical in the main communication comparison. Define the boundary between executable tools and policy state before using a fixed-toolset ablation; do not claim a causal effect when that boundary cannot be enforced consistently.

Physical tools are optional future extensions, not a requirement or the definition of SK-L3. Tool count, code length and call count earn no direct credit. Record creation, actual use and outcomes; establish utility through paired comparisons.

## 4. Instance design

Start with three interpretable L2 families before expanding random coverage:

1. **Complementary information:** different initial views expose different branches; one robot's discovery of a dead end or passage can reduce its peer's redundant exploration.
2. **Shared bottleneck:** clearing a crate changes the peer's reachable space and requires map updates and action ordering.
3. **Dynamic recovery:** pushing changes a route, a crate deviates from expectation or a local plan fails, requiring renewed observation and planning.

Freeze topology, crate initial states, starts and goals, physical parameters, capability settings and seeds. Split development and test sets by topology family, not just seed. Screen static connectivity and symbolic plans, then robot swept volumes, contact poses and physical feasibility. Retain complete executions for representative instances.

Retain every generated and screened instance with complete-witness, screening-passed, unknown or failed-check status. Search timeout does not prove infeasibility. Parking a crate in a corner may clear a route in this robot-goal task; traditional crate-delivery deadlock rules do not directly apply.

## 5. Evaluation: three questions

| Question | Measures | Interpretation |
| --- | --- | --- |
| Is the map correct? | Known-region coverage, occupancy/traversability, cross-region connectivity, update delay after pushes | Report coverage and accuracy together; unknown is not free space |
| Is the task completed? | Physically valid dual-goal success, elapsed time, ineffective pushes, recovery rate | Separate arrival from physical validity; missing evidence is unknown, not valid success |
| Does communication help? | Paired C+ versus C− differences in map quality, success and cost; message bytes | Match instances, repeat seeds and report uncertainty; message volume is not a benefit measure |

The current interface saves agent map snapshots at fixed intervals with timestamps, coordinate conventions and known cells. A fixed initial-frame transform supports post-run coverage, occupancy and traversability diagnostics. Only planning maps actually constructed by the agent are scored. Fixed non-wall-cell connectivity queries and latency after crate-cell transitions are now implemented. Reports include answer coverage, answered accuracy, false connections and false disconnections. Unobserved updates remain censored. These metrics target the current grid prototype; adapters for general topological representations remain future work.

Align maps to ground truth only after execution and never return alignment results to agents. Use one coordinate transform per trajectory instead of per-frame alignment that hides drift. Freeze evaluation regions and queries. Evaluate individual maps separately; score a shared map only if agents actually construct and submit it, not if the evaluator merges it for them.

Full-map coverage is diagnostic, not an incentive to explore every irrelevant corner. Task success remains legal arrival; new map metrics do not retrospectively change historical L1 scores. Omit a single-robot baseline from the first release because removing a robot changes the dual-goal task definition.

## 6. Consolidated implementation list

| ID | Priority | Work item | Completion criterion |
| --- | --- | --- | --- |
| SK-01 | P0 | Freeze task and experiment contracts | Observations, physics rules, goals, budgets and C+/C− permissions specified; sensor assumptions documented |
| SK-02 | P0 | Certify L1 | Complete substep records; classified non-hand contact and push-only checks with negative cases; new isolated full execution, independent-seed repeats and human review |
| SK-03 | P1 | Build L2 instances | Three families, topology-separated splits and layered screening; representative complete witnesses and all screening outcomes retained |
| SK-04 | P1 | Implement mapping evaluation | Reproducible snapshots, queries, fixed alignment and update timing without ground-truth leakage |
| SK-05 | P1 | Run paired communication experiments | Same instances, budgets and tool permissions; paired map, legal-success and cost results |
| SK-06 | P2 | Analyze self-built tools | Tool versions and creation/use records; fixed-toolset comparison when a causal claim is needed |
| SK-07 | P2 | Extend to capability-dependent L3 | Fixed maps and goals, declared capability changes, physical screening, capability reversal and role adaptation |

Development instances, solver-substep capture, plan/trajectory correspondence, basic map metrics, an independent no-message planner and arm-effort reversal configurations are implemented with initial executions and repaired retries completed. Completion criteria still require the case evidence: automated checks do not replace human acceptance, and authored baseline programs do not establish autonomous tool construction.

## 7. Existing evidence and acceptance limits

**Five of six configurations pass the complete development checks**: L1 8056510 (368.34 s), information asymmetry 8056410 (299.50 s), shared bottleneck 8056508 (247.68 s), dynamic update 8056865 (349.46 s), and weak-arm B 8068573 (332.60 s). Each continuous run connects expert execution, high/low plans, measured trajectories, control-boundary and physics-substep checks, directional contact review, and video validation. All five packets have been independently extracted, their audits recomputed, and anonymous downloads verified. The B packet includes a separate controller-attribution correction; original evidence remains unchanged.

All six configurations have independently recomputed dual-goal arrivals. Weak-arm A still lacks a complete contact-valid witness: A 8066561 arrived in 312.14 s with one reverse-contact flag. B 8067384 had six opposed-face substeps during lowering; B 8068573 passes all 13 checks. A dispatch audit found that its requested v66 profile actually selected the legacy controller. It establishes the recorded legacy execution, not the effectiveness of the v66 repair. Qualification must freeze the identified effective controller. Earlier unsigned A 8057644 (96 directional flags) and B 8057059 (three reverse-contact flags) packets remain available with their failed checks. Incomplete arrivals do not add complete witnesses. All repairs, failures and new runs remain in the [acceptance index](../../task-sokoban-acceptance-en.html).

In the historical L3-A 8057644 arrival, A’s local and planning maps cover 57/63 cells and B’s local map covers 54/63 cells, with all known occupancy correct. A answers all 465 connectivity queries correctly; B answers 440 correctly and leaves 25 unknown. This authored development map does not establish unseen-topology generalization or waive contact failures.

Development policies now test exploration before pushing and memory of completed passages. Passage evidence comes from own completed actions or explicit peer completion messages and corrects false static-wall labels; newly observed crates remain dynamic obstacles. Replanning on one retained map restored an eight-walk route. This offline result is not a new physical witness.

Each isolated policy runs in private filesystem, PID and network namespaces, receiving only its own sensors and explicit messages. Isolated L1 8066789 reached both goals in 434.54 s and passed the isolated-input and directional-contact checks. Full contact review nevertheless found 44 opposed-face physics substeps, including 11 sampled control records; it is not a complete isolated witness. Two corresponding context clips are prepared for review. Later isolated L1 8067259 arrived in 367.64 s with two reverse-contact flags and no opposed faces; it also remains incomplete. Earlier isolated L1 8056919 and its 196 reverse-contact flags remain retained. Runtime integrity checks prohibit pose writes, attachments and external forces, and verify source, model and physical parameters.

Historical L1 8011370 (279.18 s), subsequent arrivals and failed attempts remain available. New checks do not retroactively expand the scope of old evidence; recorded-input replay is not a new physical execution. Brief non-hand contact in the complete dynamic-update witness has a context clip for human classification and must not be described as contact-free execution.

After all six development witnesses pass, freeze the expert, source, physics and scorer before the 18 predeclared qualification slots: six communication-enabled witnesses, six matched communication-disabled outcomes, two additional same-seed L1 repetitions (one isolated), two additional seeds, and two reserved topologies. Repetitions include a second physical host. Retain all outcomes without replacing failed seeds or test layouts.

Human video review and independent-person reproduction remain unsigned. Keep `task_success=null` and `formal_admission=false`. Report development success, mapping quality, communication benefit, tool construction and admission separately. Authored cases do not establish unseen-map generalization; capability reversal alone does not demonstrate capability identification or role adaptation.

[Task and historical evidence](../../task-sokoban-en.html#witness) · [Acceptance preparation and all attempts](../../task-sokoban-acceptance-en.html) · [Earlier implementation evidence](../../task-sokoban-progress-en.html)
