# Embodied Terminal-Bench · robo-si

机器人能否通过写代码和做物理实验，发现工具的用途、判断自身能力，完成需要多步操作的任务？

主站：[wuxiyang1996.github.io/robo-si-results](https://wuxiyang1996.github.io/robo-si-results/)

This repository hosts the public research site and reference-video gallery. GitHub Pages is the main destination; the site presents the research questions, six task categories, task-family galleries, and an execution guide in Chinese and English.

- [任务目录 / Tasks](https://wuxiyang1996.github.io/robo-si-results/tasks/)
- [排行榜与评测结果 / Leaderboard](https://wuxiyang1996.github.io/robo-si-results/leaderboard.html)
- [研究问题 / Research](https://wuxiyang1996.github.io/robo-si-results/research.html)
- [运行与评分 / Execution guide](https://wuxiyang1996.github.io/robo-si-results/guide.html)
- [完整安装、环境恢复与 agent 测试手册](https://github.com/wuxiyang1996/robo-si/blob/main/doc/hf-246/README-zh.md)（需要仓库权限；HF 下载另需数据集权限）

The gallery contains **246 unique reference recordings covering 247 public configurations**, organized into six categories and 30 research task families. Twenty-nine families have videos; F3 remains paused. Videos are encoded at 8× and play at the browser's normal rate.

Select a gallery poster to play its representative video in place, or use the separate family link to browse variants. Videos support inline controls and fullscreen, use same-origin MP4 URLs, and are prepared from the selected Nyx originals at up to 1080p. Native 720p recordings retain their original resolution.

All four tag groups—embodiment, tools, task and difficulty—are shown in full. The 246 tasks use overall L1/L2/L3 difficulty: basic execution; adaptation and planning; diagnosis, recovery and distractor handling. Each task includes its classification rationale, while the 14 original tool-scene layer records are labeled separately.

Each video presents a reference execution, with its goal, scene conditions and demonstration notes alongside it. Agent evaluations use the execution and scoring workflow in the guide.

## Site source

| Source | Purpose |
| --- | --- |
| `site/content/site.json` | Site structure, category and family metadata |
| `site/content/pages.json` | Bilingual research and installation / agent guide |
| `site/content/tasks_*.json` | Task goals, scene conditions and demonstrated scope |
| `site/content/task_facets.json` | Four-axis tags, overall L1/L2/L3 difficulty rationales and original tool-scene layer records |
| `site/assets/` | CSS and browser JavaScript |
| `data/video-gallery.json` | Preserved video receipt and provenance; not editorial copy |
| `site/content/playback_media.json` | Same-origin browser files and their pinned release bundle |
| `site/content/leaderboard.json` | Audited 246-task result snapshot and source SHA-256 hashes |
| `tools/import_leaderboard.py` | Import a local result bundle without rerunning experiments |
| `tools/leaderboard_page.py` | Render model results, family summaries and all task rows |
| `tools/build_site.py` | Generate the publishable `dist/` directory |

## Build and preview

Python 3 is required. Building and checking the site use the standard library; no package installation is needed. The first build downloads and verifies the browser-media bundle, then reuses the ignored local cache.

```sh
python tools/build_site.py
python tools/check_site.py --root dist
python tools/check_leaderboard.py
python tools/preview_site.py --port 8765
```

Open <http://127.0.0.1:8765/robo-si-results/>. Paths include the GitHub Pages project prefix `/robo-si-results/`. The Pages workflow builds and publishes `dist/`; generated files are not edited by hand.

## Current pages and source history

The published site contains current task descriptions, research questions and the usage guide. Old research and archive pages are no longer reproduced on the website. Known former HTML addresses redirect to the relevant current page. Original evidence and source history remain in Git; the video manifest retains the provenance and checksums of the reference recordings. Obtain execution materials through the current download guide.

See [maintenance instructions](docs/MAINTAINING.md) for content ownership, validation, provenance, and publication.

## Result snapshot (2026-11-23)

The leaderboard covers 246 unique tasks and 29 active families. Astra has 99 tasks in its local scope, 30 tasks with valid independent evaluations, and 2 verified successes. It is an exploratory, incomplete run, with no aggregate 246-task success rate. The 246 reference recordings and 492 sandbox-readiness checks are shown separately from model scores. Missing and invalid scores stay empty in CSV and `null` in JSON.

To re-import this audited snapshot from the workspace:

```sh
python tools/import_leaderboard.py ../../results/astra_246_20261123
python tools/build_site.py
python tools/check_site.py --root dist
python tools/check_leaderboard.py
node --check site/assets/leaderboard.js
```

The importer verifies all input files against the bundle's `SHA256SUMS`. The public downloads contain sanitized result fields, source hashes and bundle-relative evidence paths. Full raw evidence remains in the original result bundle. When adding a new run, update the snapshot schema, counting assertions and bilingual result summary together; do not reuse this snapshot's fixed counts for a different cohort.
