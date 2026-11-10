# Sources and licenses

- `assets/ur10e/` is the unmodified UR10e directory subset from
  [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/f3b6013629c7b94f8ee93fd977b161fa8350f9bc/universal_robots_ur10e),
  commit `f3b6013629c7b94f8ee93fd977b161fa8350f9bc`. Its BSD-3-Clause license,
  original copyright and README are included. `SOURCE.json` records provenance.
- The procedural table, target, racket, ball and scene assembly in `scene.py`
  are task-authored. The upstream XML is parsed and extended in memory; its
  shipped source remains unchanged.
- Original code and documentation in this task directory use the included MIT
  license. This does not relicense the rest of robo-si or its third-party files.
- MuJoCo, PyTorch, NumPy, SciPy, ImageIO, Pillow, GLFW, PyOpenGL and their
  dependencies retain their own licenses; the release references their pinned
  packages and does not bundle or relicense their binaries.

Design context: [HOPE](https://github.com/hitchopen/HOPE),
[Isaaclab-TableTennisRobot](https://github.com/leonardung/Isaaclab-TableTennisRobot),
and [PingpongDuo](https://arxiv.org/abs/2610.20579). No code, policies, motion
recordings or assets from those three projects are redistributed here. The
current expert is a task-authored analytic planner and torque controller, not a
claimed reproduction of their published performance.
