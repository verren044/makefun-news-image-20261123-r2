# BUILD_LOG — news-image-20261123-r2

Entry: **THE WORLD IN ONE DAY** (Monday 23 November 2026)
Repo: `makefun-news-image-20261123-r2` (to be created by coordinator)
Contest: news-image-20261123, $100 (1st $20, 2nd $12, 3rd $6, 4th–10th $2, 11th–50th $1.20)
Entries close: 25 Nov 2026 07:00 WIB (2026-11-25T00:00:00Z). Results due 9 Dec 08:00 WIB.
Blind rounds: 23 Nov 19:00 WIB, 24 Nov 07:00 WIB, 24 Nov 19:00 WIB, 25 Nov 07:00 WIB.
Harness: program/v1. No entry fee. Quota: 10/day, 40 total.

## Kit status (BLOCKER NOTE for coordinator)

- `https://make.fun/c/news-image-20261123/kit` returned **HTTP 503 kit_pending**
  ("This kit is being built; send this again in 5 s") on every try: ~60 attempts
  over 00:18–00:44 WIB, 6–15 s apart. The downloaded file is a 276-byte JSON
  error, never a gzip tarball. The coordinator is retrying in parallel.
- Site kit level (from `x-makefun-kit-level` on the requirements endpoint): **37**.
  Task body said "expect 36" — stale; 37 is current.
- Format verified WITHOUT the 23rd kit, from two live sources:
  1. `GET /api/competitions/news-image-20261123/requirements` (200): program/v1,
     entrypoint main.py at repo root, readme_template (3 live badges),
     repo_about (homepage https://make.fun/bounty/news-image-20261123, topics
     makefun, ai-agents, bounties, growth), deadlines, payout curve, escrow.
  2. Prior-day kit on disk, `~/workspace/makefun/kits/news-image-20261120-kit/`
     (RULES.txt + competition.yaml read in full): image = whole PNG/JPEG,
     **at most 1 MiB and 1024x1024 px**, written to `/output/entry.png`,
     program runs twice, bytes must match, stdlib only, no network.
     Judge: z-ai/glm-5.3-flash pairwise; criteria in order — (1) names the day
     + specific events of that day, (2) selection/breadth across regions and
     fields, (3) reads — each story clear, nothing false, (4) faithful, no
     hype/speculation as fact, (5) craft — one clear composition, legible at
     ~300 px across, no garbled text. "Detail for its own sake does not count."
- The 23rd kit MUST be downloaded and `--version` checked before bundling;
  if its RULES differ from the 20th (dimensions/gate), the entry must be
  re-verified against them. Nothing in the live 23rd requirements contradicts
  the 20th-day format.
- `.makefun/owner.json`: written directly with the wallet from the task
  (`5dzkJVQkKc2V2mMuQDsfv8EJwtw3uLDMARNVHkjmByaX`, 58 bytes, no trailing
  newline) because the kit CLI was unreachable (503). Per the skill's verified
  lesson, no kit CLI command writes owner.json anyway; coordinator to confirm
  against the fresh kit when it lands.

## Rank-1 process — candidates (first test)

Winner pattern scored against: specific + twist + callback, dense + readable,
names the day, breadth across regions/fields, legible at ~300 px, faithful.

| # | Concept | Verdict |
|---|---------|---------|
| C1 | **Front page**: masthead + 13 anchor cards + 39 briefs + dotted world map + UTC day arc (52 stories) | **WINNER** |
| C2 | Globe hero: huge central globe, 6 big panels, few briefs | Loses to C1: ~12 stories, fails breadth (judge crit. 2) |
| C3 | Timeline spine: single vertical UTC timeline, no map | Loses to C1: buries breadth, no geography |
| C4 | Six continents: 6 region columns, map strip on top | Closest challenger; loses to C1: no anchor hierarchy — a Lisbon march reads equal to the Hormuz war, fails "most consequential" |
| C5 | War & climate split: two half-pages (Hormuz / COP31) | Loses to C1: single-beat bias, fails breadth |
| C6 | Market-crash front: Nvidia/AI rout as hero, rest briefs | Loses to C1: finance-led skew |
| C7 | Number day: 52 numbered list tiles, minimal art | Loses to C1: no hierarchy, illegible at 300 px |
| C8 | Comic strip: 8 drawn panels telling the day | Loses to C1: 8 panels is thin vs 52 stories |
| C9 | Map-first atlas: map 60% of canvas + legend list | Loses to C1: map dominates, legend text tiny |
| C10 | Headline ticker: huge masthead, 4 giant headlines, no map | Loses to C1: no map; daily leaders all carry one |
| C11 | Three-act day: Morning/Midday/Evening UTC bands | Loses to C1: time-grouping scrambles region breadth |
| C12 | Dossier grid: uniform 52-tile grid, no hierarchy | Loses to C1: judge cannot find the day's biggest stories |

Pairwise: C1 beat all 11 (11-0). Twist/callback in C1: the masthead carries
"52 STORIES - 6 CONTINENTS - 1 DAY"; the UTC day arc opens with the UN lethal-AI
talks and closes with the Hormuz strikes — the day opens and closes on its two
most consequential threads; the numbers strip (720/9, -14%, $58,895, 52) is the
callback to the anchor cards.

## News sourcing (all as reported 23 Nov 2026)

Searched live 23 Nov 00:30–00:45 WIB. Corroborated across ≥2 sources each:
Hormuz war (Iran strikes US base Bahrain, Houthis fire on Saudi, tankers hit);
COP31 collapse (Turkiye draft drops "fossil fuels"); Kyiv drone (14 missing) +
Russian ship fire off Finland; El Chapo Isidro captured (11 killed, Sinaloa);
Indonesia factory fire (7 found, 50 missing); Nepal PM Shah–Modi talks;
India 720/9 record (Rahul 136, Pant 128); UN lethal-AI talks continue (00:02 UTC);
Korea minister quits (AI cheating); Lisbon march; Myanmar–ASEAN; Verstappen
Las Vegas GP; AI rout (Nvidia -14% Fri, $125.53; S&P -8.6% week, Nasdaq -10%;
Bitcoin ~$58,895); Anthropic IPO $83; Fed 9 Dec; ATP finals; football/cricket.
No precise times claimed except the verified 00:02 UTC UN item; day-arc slots
are labelled Early/Morning/Afternoon/Evening, not clock times.

## Practice result

- `main.py` (Python 3.13, stdlib only) run twice, different output dirs:
  `entry.png` 1024x1024 RGB, **38,720 bytes** (gate: ≤1,048,576),
  sha256 `fbebc2c7380373535c632e3203bdecba0d9a12283db31b08e9d5fbc51d9ba411`,
  **byte-identical both runs** (`cmp` clean).
- Stories: **52** (13 anchors + 39 briefs), asserted in code.
- Viewed at full size: title, all 13 anchor cards, map + dots, day arc,
  numbers strip and all 39 briefs read clearly.
- Fixes found by viewing: (1) lowercase text rendered blank — 5x7 font is
  uppercase-only, so `text()` now uppercases at draw time; (2) badge-icon
  star polygon used absolute coords and drew a red star over the masthead —
  fixed to icon-relative coords; (3) two-digit anchor numbers crowded their
  region tags — region label now offset by measured number width; (4) map dots
  3/4, 5/13, 2/9 overlapped — nudges added; (5) anchor 3 and 12 subheads
  trimmed to 3 lines so they stay inside their cards.
- Fonts: none downloaded — design uses a hand-authored 5x7 bitmap font
  embedded in main.py; no font files needed at grade time.
- `thinking_revised`: main.py written fully, then rewritten fully once more
  (v2, this file) with the fixes above.

## Files (local commit)

- main.py — 26,778 bytes
- README.md — 1,509 bytes (3 live badges, repo makefun-news-image-20261123-r2)
- LICENSE — 1,090 bytes (SPDX-License-Identifier: MIT, first line)
- .makefun/owner.json — 58 bytes (wallet 5dzkJVQkKc2V2mMuQDsfv8EJwtw3uLDMARNVHkjmByaX)
- BUILD_LOG.md — this file
- entry.png is NOT committed (main.py builds it at grade time).

## Still to do (coordinator)

1. Download the 23rd kit fresh, verify `node cli/makefun.mjs --version` (site: 37).
2. Create GitHub repo `makefun-news-image-20261123-r2` (after opening — it is),
   push, set About (homepage + topics from requirements above).
3. Bundle (single builder session, --no-discover), kit check, submit before
   25 Nov 07:00 WIB; first blind round 23 Nov 19:00 WIB.
