# Third-party notices

The frozen G1 MJCF and referenced meshes in `assets/g1/` are BSD-3-Clause; the license is included. They were copied without modification from this repository's `humanoid/g1_support_retrieval/assets/unitree_g1/`. `assets/g1/SOURCE.json` records exact local SHA-256 hashes and upstream context. No upstream commit identity is inferred from these local files. The upstream README is retained as attribution; its illustrations and alternate models are not part of this subset.

`scene.py` assembles the scene at runtime: free pelvis preserved; position actuators replaced by torque motors with the original effort limits; passive 120 g racket attached to the right wrist; table, floor, net and ball added. There are no pelvis welds, root actuators or disabled robot collision geometries.

The ball planner, temporal scorer and evidence tooling are adapted from the repository's MIT-licensed UR10e table-tennis reference. Whole-body QP design also follows the repository's contact inverse-dynamics prototype, with no imported policy weights. New task code is covered by the accompanying MIT license.

Runtime dependencies are installed separately and retain their own licenses, including MuJoCo, OSQP, NumPy, SciPy, PyTorch and imageio. HOPE, Isaaclab-TableTennisRobot and PingpongDuo are design context only; no controller or training code from those projects is bundled.
