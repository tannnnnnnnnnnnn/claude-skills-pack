# claude-skills-pack

A self-improving Claude Code setup: orchestration skills, a destructive-command
blocker, nightly memory consolidation, and a personal knowledge graph.
Everything runs locally.

**Cheatsheet:** open `cheatsheet.html` in a browser — one page, when to use what.

## Install

```bash
bash install.sh
```

Copies skills into `~/.claude/skills/`, installs the safety-net hook, wires
both hooks into `~/.claude/settings.json` (merges — never overwrites your
existing config), and adds the auto-dream trigger to `~/.claude/CLAUDE.md`.
Restart Claude Code afterwards. Re-running is safe.

## What's inside

### Skills (`skills/`)
| Skill | Use |
|---|---|
| `/brainstorm` | idea → approved written design, no code until sign-off |
| `/ultrathink` | one hard decision, deep reasoning, one recommendation |
| `/manager` | big mixed task — plans, routes to best worker, reviews all |
| `/codex-orchestrate` | coding-only: Claude plans/reviews, Codex implements |
| `/ultracode` | same check across a whole repo, parallel agents |
| `/debug` | root-cause discipline, no guess-patches |
| `/worktree` | risky work on a safe copy; `/worktree done` to finish |
| `/fable` | Codex reviews your diff in a loop until APPROVED |
| `/dream` | memory consolidation (also auto-runs every 24h) |
| `/plan-big-execute-small` | delegate bulk reading to cheap parallel agents |
| `/stop-slop` | strip AI-writing tells from prose |
| `/lifeboat` | manual checkpoint of in-flight task state (auto version runs via hooks) |
| `/estimate` | pre-task token cost + % of weekly/5h limit, before you spend it |

### Hooks (`hooks/`)
- **safety-net.py** — blocks `rm -rf` on dangerous targets, force-push
  (allows `--force-with-lease`), `git reset --hard`, `git clean -f`,
  `git checkout .`, `git branch -D`, stash drop/clear — before they run.
- **lifeboat-save.py / lifeboat-restore.py** — when the context window
  fills and Claude compacts the conversation, save snapshots your
  in-flight task state (recent intent, edited files, git state) with zero
  token cost; restore injects it once on your next message so work
  continues where it left off. Pattern adapted from u-ichi/compact-plus.

- **lifeboat-restore** also carries a *context-cost nudge*: crossing ~350k/600k context injects a one-line warning that each message is now re-reading the whole context (the #1 token drain).

Budget tooling (`budget/`): `budget.py` measures token use since your weekly reset from local transcripts (zero API cost) and calibrates your plan ceiling from a UI reading; `/estimate` uses it. Your real `calibration.json` stays local; the repo ships a template.

All locally authored, tested, short Python you can read yourself.

### Routines (`routines/`)
Templates for two scheduled tasks (Claude Code → Scheduled section, or ask
Claude to schedule them):
- **dream-nightly** — daily: consolidate memory + refresh knowledge graph +
  morning brief.
- **graphify-weekly-review** — Sundays: re-cluster the graph, report new
  connections, knowledge gaps, stale zones.

⚠️ Both reference an Obsidian vault at `~/Desktop/AI Brain` — edit the paths
to your own vault (or delete the graph steps if you skip graphify).

### Not bundled (install from official sources — installer prints commands)
- **Codex plugin + CLI** — the executor `/fable`, `/manager`,
  `/codex-orchestrate` delegate to. Needs an OpenAI/ChatGPT login.
- **graphifyy** — knowledge-graph engine behind `/graphify`. PyPI package is
  `graphifyy` (double y — official, verified; repo: Graphify-Labs/graphify).
- **claude-mem** — automatic session memory. Tip: `CLAUDE_MEM_TELEMETRY=0`
  disables its default-on anonymous analytics.
- **caveman** — token-saving reply compression (JuliusBrussee/caveman).
- **claude-video /watch** — lets Claude watch videos (bradautomates/claude-video); needs yt-dlp + ffmpeg.
- **rtk** (rtk-ai/rtk) — PreToolUse hook that rewrites Bash commands (git status/diff/log, cat, grep, test runners) to route through a compressing proxy, cutting 60-90% off their output tokens before they hit context. Install: `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh` then `rtk init -g` (review the script first — verifies checksums, no telemetry unless you opt in). Wire into settings.json as a second PreToolUse/Bash entry AFTER safety-net, so destructive-command blocking still sees the raw command first.

## The loop, once everything is on

Work normally → claude-mem records → dream distills nightly → graphify
re-maps weekly → every session starts smarter.

## Credits
`brainstorm` adapted from obra/superpowers (Jesse Vincent) · `debug` from
obra/superpowers systematic-debugging · `worktree` from obra/superpowers
worktree skills · `dream` from grandamenium/dream-skill · safety-net inspired
by kenryu42/claude-code-safety-net · `fable` pattern from the community
Codex-review loop. All adapted and condensed; original repos linked above.
