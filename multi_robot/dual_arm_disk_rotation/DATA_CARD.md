# Disk rotation reference data

Each full run is a continuous normal-start execution of a privileged expert.
The two configurations are exact points, with three repeats each; they are
not six independently sampled environments. Two additional fresh-process
action replays are reported separately. Ablations use the nominal case and
are diagnostic comparisons, not impossibility proofs.

`trajectory.npz` contains 50 Hz `commands` and 400 Hz measured arrays: `t`,
`p`, `quat`, `yaw`, `v`, `omega`, `tilt`, `forces`, `contact_force`,
`table_force`, `q`, `qd`, `torque`, `pad_origin`, `pad_quat` and
`unexpected_collision_force`. Quaternions use wxyz; angles are radians;
positions, forces and times use SI and world coordinates. Arm arrays are
ordered left/base-x-negative then right/base-x-positive, with authored joint
order 1–7. States are post-physics-step samples. Command k applies to the next
eight physical samples; `initial_state.json` is the pre-command boundary.

`segments.json` maps high-level goals and low-level actions to half-open
command/state intervals, measured boundary states, constraints and controller
provenance. `contacts.jsonl.gz` retains per-step disk contact points/forces and
unexpected robot contacts. `link_names.json` resolves numeric contact IDs.
The exact force sign is the force on the disk in disk-contact rows; unexpected
contact rows retain the force on link A. Release videos use 10 fps and do not
replace the 400 Hz checks.

`summary.json` binds configuration, source/asset hashes, runtime, Gamma job,
GPU, command counts, termination reason and physical maxima. `source/` retains
the actual execution sources and assets. `verification.json` independently
checks recorded physics and all three representation mappings. Planned goals,
issued commands and measured states are distinct; no checkpoint fragments are
presented as continuous executions.

The recordings contain privileged disk pose, velocity, contact and verifier
information. They are for expert reproduction, imitation research and author
review. They must not be exposed as ordinary perception-agent observations.
Hidden future evaluation seeds are not included; published reference seeds
are intentionally public and must not become a held-out evaluation set.

The underlying Panda masses and inertia tensors are inherited simulation
approximations. Hardware transfer and broad friction/mass randomization are
not validated. Fixed-contact success means the current cohort does not prove
contact changes are necessary. The user approved the current reference materials for stable publication. Native
agent isolation and second-person reproduction remain unverified.
