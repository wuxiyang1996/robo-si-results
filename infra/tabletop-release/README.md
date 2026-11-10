# Tabletop reference-data release

**项目状态：汉诺塔、工具辅助桌面装配均已完成。** 用户于 2026-10-24 确认按下述各自已发布范围结项。人工验收、独立复现及文档维护作为后续事项保留；原始测试结果与正式准入记录保持独立。

Hanoi: standalone sequential manipulation, 3/4/5 disks, 58/58 fixed scenarios, 19/19 final pipeline checks. Assembly: first layer only, 8/8 scenarios, 14/14 final pipeline checks. User publication authorization is recorded in `release-authorization.json`; human acceptance and second-person reproduction remain pending.

[Release and offline packet](https://github.com/wuxiyang1996/robo-si/releases/tag/tabletop-20261023). Download `tabletop-20261023.zip` and `SHA256SUMS.txt`, verify the archive SHA-256, and extract into a fresh directory. Open `infra/tabletop-zh.html` or `infra/tabletop-en.html`; no build or server is required. The archive includes all 321 reviewer-facing evidence files and two separate frozen source snapshots. Media and NPZ files are release assets, excluded from Git history.

For a Git clone, run `python infra/tabletop-release/download_evidence.py` with authenticated GitHub CLI access. It downloads the release, verifies SHA-256 and restores the media under `infra/tabletop-release`; the complete packet stays in `.tabletop-release-cache/`.

Run `python verify_release.py` from the extracted packet to verify every packaged file. Use `snapshots/hanoi` for Hanoi and `snapshots/assembly` for Assembly; do not mix their shared runtimes. Install each snapshot's `requirements-genesis.txt`, including the recorded Genesis environment, and follow the exact per-scenario commands on the page. GPU/Genesis and Docker are required by the corresponding physical/container pipeline steps. The packet includes required G1 assets, their available license files, selected training NPZ files and the canonical source logs for those training episodes. Historical runs outside the selected release are excluded.

The 19/19 and 14/14 checks were run against the recorded snapshot digests, not against an arbitrary future main branch. Browser notes are private local drafts; exported notes do not alter admission. Five-disk Hanoi retains its placement-8 contact-gap quality flag.
