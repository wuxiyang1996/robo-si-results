# Embodied Terminal-Bench · robo-si

机器人能否通过写代码和做物理实验，发现工具的用途、判断自身能力，完成需要多步操作的任务？

主站：[wuxiyang1996.github.io/robo-si-results](https://wuxiyang1996.github.io/robo-si-results/)

This repository hosts the public research site and reference-video gallery. GitHub Pages is the main destination; the site presents the research questions, six task categories, task-family galleries, and an execution guide in Chinese and English.

- [任务目录 / Tasks](https://wuxiyang1996.github.io/robo-si-results/tasks/)
- [研究问题 / Research](https://wuxiyang1996.github.io/robo-si-results/research.html)
- [运行与评分 / Execution guide](https://wuxiyang1996.github.io/robo-si-results/guide.html)
- [完整安装、环境恢复与 agent 测试手册](https://github.com/wuxiyang1996/robo-si/blob/main/doc/hf-246/README-zh.md)（需要仓库权限；HF 下载另需数据集权限）

The gallery contains **246 unique reference recordings covering 247 public configurations**, organized into six categories and 30 research task families. Twenty-nine families have videos; F3 remains paused. Videos are encoded at 8× and play at the browser's normal rate.

These are reference executions, not a new agent's benchmark success rate. Each task retains its own acceptance scope, including correct exits. Historical runs, privileged experts, and ordinary-interface runs remain distinct. Interface probes, historical regrading, and fresh complete policy runs are different checks. Rendering changes do not establish new physical execution.

## Site source

| Source | Purpose |
| --- | --- |
| `site/content/site.json` | Site structure, category and family metadata |
| `site/content/pages.json` | Bilingual research and installation / agent guide |
| `site/content/tasks_*.json` | Task goals, scene conditions and demonstrated scope |
| `site/content/task_facets.json` | Embodiment, physical tools, task operations and source-backed scene difficulty tags |
| `site/assets/` | CSS and browser JavaScript |
| `data/video-gallery.json` | Preserved video receipt and provenance; not editorial copy |
| `tools/build_site.py` | Generate the publishable `dist/` directory |

## Build and preview

Python 3 is required. The site tools use the standard library; no package installation is needed.

```sh
python tools/build_site.py
python tools/check_site.py --root dist
python tools/preview_site.py --port 8765
```

Open <http://127.0.0.1:8765/robo-si-results/>. Paths include the GitHub Pages project prefix `/robo-si-results/`. The Pages workflow builds and publishes `dist/`; generated files are not edited by hand.

## Current pages and source history

The published site contains current task descriptions, research questions and the usage guide. Old research and archive pages are no longer reproduced on the website. Known former HTML addresses redirect to the relevant current page. Original evidence and source history remain in Git; the video manifest retains the provenance and checksums of the reference recordings. Obtain execution materials through the current download guide.

See [maintenance instructions](docs/MAINTAINING.md) for content ownership, validation, provenance, and publication.
