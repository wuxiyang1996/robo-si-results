# Maintaining the research site

GitHub Pages at <https://wuxiyang1996.github.io/robo-si-results/> is the main destination. Update this repository and its Pages workflow; do not republish a parallel Sites version as the current site.

## Edit the sources

| File | Edit here for |
| --- | --- |
| `site/content/site.json` | Branding, six categories, family membership, representative demos, and shared bilingual keywords |
| `site/content/pages.json` | Research, usage guide, and archive text |
| `site/content/tasks_*.json` | Chinese and English task descriptions |
| `site/assets/site.css` | Styling |
| `site/assets/site.js` | Browser behavior |
| `tools/build_site.py` | Static generation and archive routing |
| `tools/check_site.py` | Static validation |
| `data/video-gallery.json` | Video provenance receipt: preserve its accepted source data |

`pages.json` contains `research`, `guide`, and `archive`. Each page has `title_zh`, `title_en`, `lead_zh`, `lead_en`, and `sections`. A section has `id`, bilingual `title_*` and `body_*`, and optional `links` with `label_zh`, `label_en`, and `url`. Bodies are plain text, not HTML; separate paragraphs with `\n\n`.

Task copy should explain the goal, physical difficulty, and relevant actions in natural language. Keep configuration-specific simplifications, correct-exit criteria, and acceptance limits. Do not turn historical status notes or render version labels into the task description. A recorded reference success is not a learned agent's score, and an interface probe is not a full successful policy run.

## Routes and local checks

The project prefix is `/robo-si-results/`. Current routes are:

- `index.html`, `research.html`, `guide.html`, `archive.html`
- `tasks/`
- `tasks/categories/<id>.html`
- `tasks/families/<ID>.html`

Use Python 3; the build, validator, and preview tools require only the standard library.

```sh
python tools/build_site.py
python tools/check_site.py --root dist
python tools/preview_site.py --port 8765
```

Preview <http://127.0.0.1:8765/robo-si-results/>. Check both languages, navigation, mobile layout, representative demos, and at least one complete family gallery. Static validation cannot establish that videos visually match their physical records or that a robot policy succeeds. Report browser and visual checks separately.

`dist/` is generated and ignored. Do not edit it as the source of truth. The workflow uploads this generated site rather than the entire evidence repository.

The earlier `import_gallery.py`, `apply_h1_media.py`, `select_dynamic_demo.py`, and `check_gallery.py` tools document historical imports and media corrections. They do not generate the current site. Maintain the current layout through `build_site.py` and the `site/` sources.

Edit multilingual JSON as UTF-8 files. Avoid passing literal Chinese through a PowerShell pipeline whose output encoding is ASCII. The validator rejects damaged text, incomplete descriptions, and keywords outside the shared vocabulary.

## Video and evidence provenance

Gallery videos are already encoded at 8×; the browser should play at 1×. Keep the selected media URLs, hashes, source execution, timing, and acceptance scope traceable. Do not describe a visual asset replacement as a new physical run or imply that unrecorded joints were recovered.

The reorganization baseline is `b395aee4e0254f1264b5b5c5479f09d5052e991e`. Original source and evidence remain in the repository. Archived HTML is served under `archive/pages/<original-path>` with links adjusted for browsing; large historical media and raw JSON link to immutable GitHub raw URLs at the baseline. This presentation copy is distinct from the byte-preserved original in Git.

`data/archive-files.json` maps baseline paths to fixed raw/blob destinations. Legacy HTML routes redirect to current pages or archived pages while preserving query strings and fragments. The browser's 404 resolver can offer the archived-file destination. This does **not** preserve every former raw-file URL as an HTTP download endpoint: machine clients must use fixed raw or download URLs. Do not manufacture missing historical files or silently substitute unrelated evidence.

## Keep installation claims grounded

The full execution guide is maintained in the access-controlled [robo-si repository](https://github.com/wuxiyang1996/robo-si/blob/main/doc/hf-246/README-zh.md). The page copy was checked against guide blob `90a37d3ab1ed6493a340f6ae2c14a1456c88b0cf` and HF runtime revision `9dbaa30876fe4b2140af61dcb836d4d9ad32d646`.

Link readers to that guide for exact installation and agent commands. Before copying a command here, verify it against the actual release. Access to the public website does not grant access to private GitHub or HF material. Environment restoration, no-op probes, historical regrading, and full agent evaluation have different verification scopes.

## Publish and verify

Run the build and validator before publishing. After the Pages workflow succeeds, verify that the deployed commit is the intended one and check the live homepage, a category, a family, both languages, the guide, and archive routes. A successful build alone does not prove deployment or playback.

GitHub Pages documents a ten-minute deployment limit; `actions/deploy-pages@v5` caps its polling timeout at ten minutes. A longer workflow job timeout does not create a thirty-minute Pages synchronization allowance. Keep the published artifact focused on the website while retaining the original evidence in Git.
