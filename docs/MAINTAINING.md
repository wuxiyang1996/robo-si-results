# Maintaining the research site

GitHub Pages at <https://wuxiyang1996.github.io/robo-si-results/> is the main destination. Update this repository and its Pages workflow; do not republish a parallel Sites version as the current site.

## Edit the sources

| File | Edit here for |
| --- | --- |
| `site/content/site.json` | Branding, six categories, family membership, category sharing posters, and shared bilingual keywords |
| `site/content/pages.json` | Current research and usage guide |
| `site/content/research_interactive.json` | Three evaluation tracks, seven sandbox components and their walkthrough, in both languages |
| `site/content/tasks_*.json` | Bilingual task goals, scene constraints, and demonstrated scope |
| `site/content/task_facets.json` | Four tag vocabularies, overall difficulty assignments and rationales, and original tool-scene layer evidence |
| `site/assets/site.css` | Styling |
| `site/assets/site.js` | Browser behavior |
| `tools/build_site.py` | Current-page generation and legacy redirects |
| `tools/research_page.py` | Research page composition and interactive component markup |
| `tools/check_site.py` | Static validation |
| `data/video-gallery.json` | Video provenance receipt: preserve its accepted source data |
| `site/content/playback_media.json` | Browser derivatives, original-source hashes, and the pinned media bundle |
| `tools/prepare_playback_media.py` | Rebuild and verify web videos from the selected Nyx originals |
| `tools/playback_media.py` | Verify the release bundle and copy browser media into the site |

Only `research` and `guide` in `pages.json` are rendered. Each page has `title_zh`, `title_en`, `lead_zh`, `lead_en`, and `sections`. A section has `id`, bilingual `title_*` and `body_*`, and optional `links` with `label_zh`, `label_en`, and `url`. Bodies are plain text, not HTML; separate paragraphs with `\n\n`.

Sections can also contain `blocks`. Supported block types are `code` (`language`, literal `text`), `table` (`columns_zh`, `columns_en`, `rows_zh`, `rows_en`), `list` (`items_zh`, `items_en`), and `note` or `paragraph` (`text_zh`, `text_en`). Keep bilingual arrays the same length and every table row the same width. Code is HTML-escaped when rendered and copied as literal text; do not insert HTML into command examples.

The research page has a dedicated editorial layout. Keep its existing section anchors, including `tracks`, `agent-interface` and `rq1`–`rq3`. The interactive track descriptions live in `research_interactive.json`; update them alongside the protocol prose in `pages.json`. The sandbox diagram explains logical responsibilities and data flow, not a one-container-per-component deployment. Its ramp example illustrates the interface without claiming a new physical run. All explanations are present in the HTML; JavaScript adds tabs, component selection and the manual walkthrough. Test track arrow keys, all seven components, Previous/Next boundaries and language switching on desktop and a narrow viewport. Do not place translated attributes on a parent containing controls: language switching replaces translated elements' text content.

Task cards display `goal_zh`/`goal_en`, matching `conditions_zh`/`conditions_en` arrays, and any `scope_zh`/`scope_en` directly below the video. Describe what must happen, the scene and physical constraints, and what the recording actually demonstrates. Preserve configuration-specific simplifications, correct-exit criteria, and acceptance limits. `description_*` remains search metadata. Do not reintroduce expandable old-record panels, render version labels, or links to former task pages. A recorded reference success is not a learned agent's score, and an interface probe is not a full successful policy run.

Use direct, natural prose in both languages. State the task goal, physical setup and demonstrated behavior. Keep relevant limits specific: preconnected ropes, fixed joints, reduced goals or missing recorded states. Explain evaluation methodology in the research and usage pages, and keep repeated caveats out of individual cards. The visible `scope_*` heading is “演示说明 / About this demonstration”.

Typography is shared by all current pages in `site/assets/site.css`. Use `rem` for font sizes so browser font preferences remain effective. The default body is 18px at a 16px browser root, with most task and document text at 16–18px and secondary labels at 12–15px. Preserve the larger mobile sizes; allow navigation, filters and task labels to wrap instead of shrinking the text. Check long English labels as well as Chinese copy before publishing a typography change.

The homepage and `tasks/` share a compact task-family gallery. Six category buttons and an “All” button filter 29 representative videos. Clicking a poster plays the video in that card; a separate title and task-count link opens the family's variants. The homepage and task gallery default to all 29 recorded families; explicit category links still select their requested category. Representatives come from `family_representatives` in the original media manifest, including `TT-R-G-U` for the arm-versus-humanoid example. Category pages use the same family cards; the single-family dynamic category directly shows its tasks. F3 remains a separate paused-design link with no invented recording. Keep the research question and three contributions above the homepage gallery.

Category controls use native buttons with `aria-pressed`; play, retry and fullscreen controls are separate from navigation links. Preserve category selection when reloading or changing language, and keep all family links usable without JavaScript. Individual task pages retain their video players, search, and task filters. Videos load only after a click, pause when filtered out or offscreen, and offer native playback controls. Never wrap a player in a navigation link or use a release-download URL as the browser media source.

The four tag axes are `embodiment`, `tools`, `task`, and `difficulty`. Their URL values are stable slugs; bilingual labels belong in `task_facets.json`. Every recording must have all four dimensions. Show every value in homepage, category and family-card summaries as well as individual task cards; wrap long labels instead of truncating them with `+N`, ellipses or hidden rows. Tools describe physical tools available in the scene, including candidates, rather than APIs or guaranteed use. The family gallery tests all selected tags against the **same recording**, not against independent family-wide unions. Selected tags carry into both the family title and task-count links. Individual cards expose the same tags as filter buttons. The six primary category buttons remain a separate filter.

Difficulty describes the task's **overall complexity**, using the user-confirmed three-level scheme:

- **L1 · Basic execution:** direct operations or short action sequences with a clear approach.
- **L2 · Adaptation and planning:** multi-step actions under known constraints, tool or body adaptation, or coordination between robots.
- **L3 · Diagnosis, recovery and distractors:** hidden states, misleading candidates or faults that call for diagnosis, recovery or experiments to judge feasibility.

Assign every one of the 246 records exactly one value, `l1`, `l2` or `l3`, with `difficulty_basis: "editorial-assessment"` and a task-specific bilingual rationale in `difficulty_note_zh` / `difficulty_note_en`. The rationale is displayed below the complete tag set. Assess the task's conditions and required decisions; task-ID suffixes and execution-interface levels are not automatic difficulty assignments.

Keep the 14 original tool-scene layer declarations separately in `source_scene_layer`, with `value` (`layer-1`, `layer-2` or `layer-3`), `note_zh`, `note_en`, and `sources`. Other records use `null`. These source layers describe the proposal's cumulative, same-seed tool scenes and appear as “原始工具场景层 / Original tool-scene layer”; they do not replace the overall difficulty label. Website difficulty metadata remains separate from evaluated-agent observations and prompts. Public copies are emitted in `data/task-facets.json` and `data/task-index.json`.

## Routes and local checks

The project prefix is `/robo-si-results/`. Current routes are:

- `index.html`, `research.html`, `guide.html`
- `tasks/`
- `tasks/search.html`
- `tasks/categories/<id>.html`
- `tasks/families/<ID>.html`

Use Python 3; the build, validator, and preview tools require only the standard library.

```sh
python tools/build_site.py
python tools/check_site.py --root dist
python tools/preview_site.py --port 8765
```

Preview <http://127.0.0.1:8765/robo-si-results/>. Check both languages, category selection, thumbnail navigation, mobile layout, keyboard focus, and playback in at least one complete family gallery. Confirm that the “All” view includes 29 families and that F3 is described separately. Check that all four tag groups wrap fully at 320px, that each task shows its overall difficulty rationale, and that original scene layers have their separate label. Check the visible M4 goal, constraints, and preconnected scope, the guide's download/install/agent steps and copy buttons, and an old M4 URL redirect. Static validation checks family coverage, direct links, representative posters, visible task conditions, escaped code examples, legacy redirects, and all 246 task players. It cannot establish that videos visually match their physical records or that a robot policy succeeds. Report browser and visual checks separately.

`dist/` is generated and ignored. Do not edit it as the source of truth. Each build replaces this repository's generated directory so retired HTML and assets cannot remain from an earlier build. The workflow uploads only `dist/`, not the entire source and evidence repository.

The earlier `import_gallery.py`, `apply_h1_media.py`, `select_dynamic_demo.py`, and `check_gallery.py` tools document historical imports and media corrections. They do not generate the current site. Maintain the current layout through `build_site.py` and the `site/` sources.

Edit multilingual JSON as UTF-8 files. Avoid passing literal Chinese through a PowerShell pipeline whose output encoding is ASCII. The validator rejects damaged text, incomplete descriptions, and keywords outside the shared vocabulary.

## Current pages and original evidence

Gallery videos are already encoded at 8×; the browser should play at 1×. Keep the selected media URLs, hashes, source execution, timing, and acceptance scope traceable. Do not describe a visual asset replacement as a new physical run or imply that unrecorded joints were recovered.

Browser media lives at same-origin `media/videos/<ID>.mp4` and `media/posters/<ID>.jpg`. The browser never needs the GitHub Release download redirect. The build obtains a hash-pinned bundle from the assets repository, checks each file, and copies only the manifest's media into `dist/`. The local `.cache/browser-media/` directory is ignored. Keep all 246 videos present and total media below 900 MiB so the complete Pages artifact stays below its 1 GB limit.

To regenerate media, use `tools/prepare_playback_media.py` with a verified source map whose `source_manifest_sha256` matches `data/video-gallery.json`. Each source file is also checked against that catalog's `source_8x_sha256`. The browser profile is H.264/yuv420p, CRF 18, medium preset, at most 1920×1080 and 30 fps, with no upscaling, no audio and a faststart MP4 header. Native 720p remains 720p. The tool fully decodes every output and verifies duration within one output frame. Posters retain the selected source timestamps. Encoding needs FFmpeg plus FFprobe or PyAV; ordinary builds need only Python's standard library and network access for the first bundle fetch.

Package only the manifest's `media/` files into a ZIP, publish it as an immutable asset release, and add its URL and SHA256 under `bundle` in `site/content/playback_media.json`. Do not replace the original recording receipt. Verify live `video/mp4` responses and byte-range requests after deployment, then test actual advancing playback, seeking, fullscreen, and mobile layout. A successful HTTP response alone does not prove browser playback.

The website publishes current research, task, and guide content only. Previous HTML pages, archive asset trees, and raw evidence trees are not copied into the deploy artifact. Source history and original evidence remain available in Git; they are not additional public website versions.

`data/legacy-routes.json` maps previous HTML addresses to current pages. Both the old route and its former `archive/pages/` counterpart contain a small redirect, not the old document. Redirects preserve query strings and map known task fragments to their current recording IDs. For example, `archive/pages/archive-m4-20261104.html#M4-01` opens `tasks/families/M4.html#M4-01`. The 404 resolver uses the same current-route map and no longer redirects raw files into an archive. Machine clients must use the documented release download addresses; do not manufacture missing files or silently substitute unrelated evidence.

The source baseline `b395aee4e0254f1264b5b5c5479f09d5052e991e` is used only to enumerate former HTML routes. Do not link active pages to the retired Sites domain or to old HTML routes. The immutable video manifest keeps its original provenance fields for verification; those fields are not navigation links in the task cards.

## Keep installation claims grounded

The full execution guide is maintained in the access-controlled [robo-si repository](https://github.com/wuxiyang1996/robo-si/blob/main/doc/hf-246/README-zh.md). The page copy was checked against guide blob `90a37d3ab1ed6493a340f6ae2c14a1456c88b0cf` and HF runtime revision `9dbaa30876fe4b2140af61dcb836d4d9ad32d646`.

The current usage page presents the verified release's download, installation, environment checks, and agent-testing commands directly. Before changing a command, check its actual release script and CLI arguments. Preserve fixed release identifiers where reproducibility requires them. Access to the public website does not grant access to private GitHub or HF material. Environment restoration, no-op probes, historical regrading, and full agent evaluation have different verification scopes.

## Publish and verify

Run the build and validator before publishing. After the Pages workflow succeeds, verify that the deployed commit is the intended one and check the live homepage, a category, a family, both languages, the guide, and legacy redirects. A successful build alone does not prove deployment or playback.

GitHub Pages documents a ten-minute deployment limit; `actions/deploy-pages@v5` caps its polling timeout at ten minutes. A longer workflow job timeout does not create a thirty-minute Pages synchronization allowance. Keep the published artifact focused on the website while retaining the original evidence in Git.
