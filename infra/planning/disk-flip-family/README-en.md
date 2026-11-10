# Disk Flip family: compact task list and object design

2026-10-29 · 4 task variants, 3 embodiments and 6 selected settings, using 3 object profiles (2 main geometries). All six have candidate experts and physics executions; 5 complete witnesses, 1 still unresolved.

A variant is an independent manipulation problem. A setting is a selected task/body/scene configuration. Parameter values, disclosure, ablations and seeds are not additional tasks; do not expand a Cartesian product.

## Task list

| Setting ID | Variant | Object | Embodiment | Task and mechanism | Status |
|---|---|---|---|---|---|
| DF-01-G | DF-01 | P1 | G1 + Dex3 | Original gentle disk flip：Push to the edge, flip under bimanual grasp, place and release; preserve the original protocol. | Fresh execution + replay passed |
| DF-02-G | DF-02 | P2 | G1 + Dex3 | Rimmed plate: three-finger grasp adaptation：Choose rim pinching, underside support or opposing-face grasp from rim clearance and finger geometry. | Complete witness + replay passed; acceptance tracked separately |
| DF-02-F | DF-02 | P2 | G1 + Inspire five-finger hand | Rimmed plate: five-finger grasp adaptation：Same world as DF-02-G; change only the hand and required control mapping, testing whether grasp strategy changes. | Executed; no full witness |
| DF-03-G | DF-03 | P3 | G1 + Dex3 | Contact-load-limited plate flip：Balance slip resistance and local load limits; distribute load or use table support when needed. | Complete witness + replay passed; acceptance tracked separately |
| DF-04-G | DF-04 | P1 | G1 + Dex3 | Open-strategy flip: dual-arm configuration：Choose one/two-hand grasp, regrasp and support transfer without the original mandatory sequence. | Complete witness + replay passed; acceptance tracked separately |
| DF-04-S | DF-04 | P1 | Stretch 3 + specified gripper | Open-strategy flip: single-arm configuration：Same object and table as DF-04-G; adapt the complete flip and release to one arm and its wrist. | Complete witness + replay passed; acceptance tracked separately |

## Object design

| ID | Object | Geometry and properties | Tasks |
|---|---|---|---|
| P1 | Standard solid disk | 200 mm diameter, 12 mm thick, 120 g; flat faces and uniform mass. | DF-01 / DF-04 |
| P2 | Rimmed shallow plate | Shallow concavity, thin rim and underside support ring; specify under-rim clearance and inverted support. Development geometry: 200 mm diameter, 20 mm total height, 120 g, 14 mm under-rim clearance. Upright/inverted static support probes passed. | DF-02 |
| P3 | Contact-load-sensitive shallow plate | Reuse P2 geometry with local contact-load limits. Initially fix friction and mass and retain a feasible safe grasp. Rigid-body damage proxy, not physical fracture. | DF-03 |

Freeze diameter, body/rim thickness, rim width and underside clearance, concavity, support-ring geometry, mass/COM/inertia, hand–object and table–object friction, and applicable local load limits. P2/P3 need stable inverted support and complete withdrawal; do not reuse the flat disk's height/contact predicates. Collision geometry must preserve the rim, cavity and insertion gaps rather than filling them.

## Protocols and paired comparisons

- Shared goal: target face up, fully in the goal region, released and stable, with public safety constraints satisfied throughout.
- DF-01 freezes the original bimanual requirement, sequence, scorer and limits. Its 6/6 executions and 2/2 replays cover only the fixed-pelvis dual-Dex3 reference and two declared initial configurations. Formal admission remains false.
- DF-02–04 use a separate extension protocol accepting every strategy satisfying the goal and public constraints, including regrasp, table support and controlled transfer. Freeze tolerances, contact-loss rules, speed/load limits and dwell times before implementation. Terminal pose cannot excuse a drop or a limit violation.
- DF-02-G/F use the same G1 body/base constraints, changing only the hand and necessary control mapping. Verify actual grasp differences rather than assuming five fingers are superior; remove the extra hand configuration if the same strategy covers both.
- DF-04-G/S share the object, table, goal and extension scorer, with separately validated initial placements and fixed bases during execution. First establish a complete Stretch flip-and-release witness. Failed single-arm screening does not prove impossibility.
- DF-03 uses an explicit local-load damage proxy. A net force that cancels opposing contacts is not a squeeze-load measure. Preserve a safe feasible grasp; visual materials do not establish physical fragility.

## Scope and validation

The three embodiments are G1 + Dex3, G1 + Inspire five-finger hand, and Stretch 3 + a specified gripper. Reuse the existing families' Stretch 3 assets; bind the gripper and control interface to concrete assets. A3, dual-arm wheeled bodies and Stretch 4 are not additional entries.

Elliptical/rectangular shapes, friction/mass/COM changes, known/unknown parameters and active-probing ablations remain within-task configurations or reserves. Declare available sensors separately; cross-body success alone does not establish self-modeling.

Registration: 4 variants, 6 settings (one original plus five extensions), 3 object profiles and 2 main geometries. Candidate experts have been executed for all six settings; 5 settings have a complete witness. New settings do not inherit historical scores. The original 14-task inventory count, controller, scorer, evidence and admission state are unchanged.

[Original task and reference evidence](/infra/task-disk-flip-en.html#task) · [Family overview](/infra/task-families-en.html#disk-flip-family) · [中文](README.md) · [Structured design](task-design.json)

[Per-setting experts, plans, trajectories and videos](IMPLEMENTATION-en.md) · [Run ledger](implementation.json)
