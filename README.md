# Embodied Terminal-Bench · robo-si

Public site: https://wuxiyang1996.github.io/robo-si-results/

The gallery organizes 246 unique completed-reference recordings, covering 247 public configurations, into six categories and 30 research task families. Twenty-nine families have delivered videos; F3 remains paused. All active gallery videos are rendered at 8× and play at the browser's normal rate.

| Category | Families |
| --- | --- |
| Access and retrieval | H1, H4, M1, M3, FRG, SLR |
| Loads and transport | H2, H5, H6, M2, M4, F5 |
| Fine manipulation and assembly | ASM, GEAR, JNG, DF, DR, FT |
| Deformable materials | F1, F2, F3, F4, F6, F7 |
| Multistep planning and procedures | SK, Hanoi, MTC, SC, PC |
| Dynamic response and timing | TT |

The homepage presents one demo per category. Category pages present one representative per family. Family pages contain the complete delivered collection and task-specific scope notes. The original v6 research template is retained.

- [Installation, environment restoration and agent testing](https://github.com/wuxiyang1996/robo-si/blob/main/doc/hf-246/README-zh.md) — repository access required.
- [Pinned HF runtime and evidence release](https://huggingface.co/datasets/IntelligenceLab/robo-si/tree/9dbaa30876fe4b2140af61dcb836d4d9ad32d646/releases/benchmark-246-runtime-and-evidence-20261109-v1) — dataset access required.
- [Current video manifest](data/video-gallery.json): video/poster URLs, hashes, frame rates, scope and provenance.
- [Publication validation](data/gallery-validation.json): gallery checks, preserved evidence and historical link limitations.
- [Historical acceptance notes](README-acceptance-20261104.md).

Videos are Nyx presentation renders of recorded physical executions. They retain each task's accepted scope, including correct exits. They are not learned-agent benchmark scores. Display asset updates do not establish a new physical run, new task success or a different collision model. Historical references, privileged experts and ordinary-interface runs remain separately identified.

This is a static GitHub Pages project site, published from main at the repository root with .nojekyll. Paths use the /robo-si-results/ project prefix. Public video binaries are versioned in the robo-si-review-assets releases; the 2026-11-09 H1 fine-grained revision preserves the prior video hashes in the manifest.

The importer tools/import_gallery.py preserves evidence JSON bytes. tools/apply_h1_media.py applies verified render receipts. tools/check_gallery.py verifies the 246 records, six categories, thirty families, links and original evidence. Browser visual QA is separately reported and must not be inferred from static checks.
