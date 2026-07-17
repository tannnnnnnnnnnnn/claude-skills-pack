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

### Hook (`hooks/safety-net.py`)
Blocks `rm -rf` on dangerous targets, force-push (allows
`--force-with-lease`), `git reset --hard`, `git clean -f`, `git checkout .`,
`git branch -D`, stash drop/clear — before they run. Locally authored,
tested, ~60 lines of Python you can read yourself.

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

## The loop, once everything is on

Work normally → claude-mem records → dream distills nightly → graphify
re-maps weekly → every session starts smarter.

## Credits
`brainstorm` adapted from obra/superpowers (Jesse Vincent) · `debug` from
obra/superpowers systematic-debugging · `worktree` from obra/superpowers
worktree skills · `dream` from grandamenium/dream-skill · safety-net inspired
by kenryu42/claude-code-safety-net · `fable` pattern from the community
Codex-review loop. All adapted and condensed; original repos linked above.
