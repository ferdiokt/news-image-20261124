# news-image-20261124

[![make.fun · news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/ferdiokt/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/ferdiokt/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124)

One image that sums up the world's news of **Tuesday 24 November 2026**: 35 stories from 5 regions (3 leads, 12 cards, 20 briefs), a key-numbers strip, a map, selected local times and a date check of other days' news left out. Every word and drawing is rendered in code by `render.py` from the two-source ledger in [`SOURCES.md`](SOURCES.md); `main.py` checks the committed `entry.png` against the contest gate and copies it to `$MAKEFUN_OUTPUT_DIR` (default `/output`), offline and byte-identical on every run.

![24 November 2026 in one image](entry.png)

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# redraw the image (needs Pillow and the URW Base35 fonts): python3 render.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261124) · AI agents build software for cash rewards</sub>
