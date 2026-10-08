---
name: graph-loop
description: Turn any linear workflow into a graph and run it. Walks a workflow you already do step-by-step, applies the fake-edge test to find the waits that carry no data, audits for hidden edges (shared files, browser, rate-limited APIs), picks the shape (chain / diamond / router / cycle), emits a GRAPH SPEC, then runs it as a coordinated fleet via the Workflow tool with caps and fresh-context verifiers. Domain-agnostic — works on research, discovery pipelines, content pipelines, repo sweeps, analytics, launches, not just code. Triggers - "graph loop", "/graph-loop", "draw the graph", "graph this workflow", "fake edge test", "can this run in parallel", "make this parallel", "fan this out".
argument-hint: "<the workflow to graph, or a goal to build a graph for>"
allowed-tools: "*"
user-invocable: true
---

# /graph-loop — draw the graph, then run it

A graph is **a plan for your AI work, drawn so you can see it**: which jobs happen, and
which job waits for which. Two parts only.

- **Node** = one job. One agent, one bounded task, one input, one output.
- **Edge** = one job needs what another produced. **An edge only counts when real data
  passes along it.**

> Nodes do the thinking. Edges carry the results. That's the whole vocabulary.

A node is only wire-able if it has a **contract**:

```text
▸ NODE CONTRACT
JOB:     one bounded job, nothing else
IN:      { ...defined fields }        ← passed in, never assumed
OUT:     { ...defined fields }        ← schema'd, not a wall of free text
SCHEMA:  enforced. free text → rejected and retried
WHY:     a defined output is what lets the NEXT node consume this one
         without a human in the middle.
```

## The loop

### 1. DRAW — list the nodes
Take the workflow the user already runs (or the goal they want) and write it out as
numbered jobs. Most workflows arrive as a **chain** — "do A, then B, then C" — which is
technically already a graph, just the saddest one: every node with one arrow in and one
out. A chain has no redundancy; if C stalls, D never happens and A's work is stranded.

### 2. THE FAKE-EDGE TEST — the core move
Walk the steps in order. At each one ask exactly one question:

> **Does this step actually need the result of the step before it?**

- **Yes** → real edge. Keep the order.
- **No** → **there is no edge. The wait is wasted.** Those jobs run at the same time.

Expect **2–3 fake edges in almost any workflow.** Classic tell: *"review file A for
bugs, then review file B"* — B never reads A's output; they're sequential only because
that's the order they were typed.

Why it matters: N linear steps cost N sequential failure points and the latency of all N
**added together**. The same jobs as a graph carry only the 3–5 dependencies that really
exist and finish at the speed of the **slowest layer**, not the sum.

> The model was never the bottleneck. The line you drew was.

### 3. THE HIDDEN-EDGE AUDIT — do not skip this
Two nodes can look independent (their prompts never mention each other) while sharing a
**resource**. That is a real edge nobody wrote down. Check every parallel candidate for:

- the same **file** or output path
- the same **browser session / tab** (a very common one here)
- the same **rate-limited API** or account
- the same working directory / git branch

**Fix by isolating** — `isolation: "worktree"` per agent, its own browser tab, its own
output path — **or accept the serialization.** Any two nodes writing the same file need
an edge, not parallelism.

### 4. PICK THE SHAPE
- **Chain** — each step waits. Slowest shape. Only when steps genuinely need each other.
- **Diamond** — split → fan out → verify → merge. **The workhorse; usually the answer.**
- **Router** — one node inspects a result and picks the path. For branching work; the
  decision lives in the structure, not in a guess.
- **Cycle** — repeat until N rounds turn up nothing new. For discovery of unknown size.
  **Always with a hard cap** or it runs until the budget is gone.

### 5. EMIT THE GRAPH SPEC
Write it in this shape and show the user **before running anything**:

```text
▸ GRAPH SPEC
GOAL:        <one sentence>
FAN OUT:     <the independent jobs, run at once>
RULE:        <what every node's output must contain>
VERIFY:      <independent checker, fresh context, what it tries to kill>
MERGE:       <how results combine>
CAP:         <hard limit on agents/items for this run>
ON FAIL:     flag any node that returns nothing, never skip it silently
REPORT:      <the single artifact that lands>
HUMAN GATE:  <what must not happen without asking>
```

### 6. RUN IT
The machinery is the **`Workflow` tool** — `parallel()`, `pipeline()`, `agent()`,
schemas, worktree isolation. Coordination runs as *code*, so passing results between
agents costs no extra context in the session.

**Gate:** `Workflow` is **opt-in in this harness.** It only fires if the user says
"workflow" / "use a workflow" / "ultracode" / invokes a skill that calls it. If they
haven't, either ask for the go-ahead or fall back to **parallel `Agent` calls in one
message** (no opt-in needed, covers most fan-outs).

### 7. SAVE
A run that came out good becomes a named, re-runnable graph. Save the spec.

## The diamond, concretely

**fan out → reduce → synthesize.** The craft is in the four details:

```js
// FAN OUT — independent work, all at once, cheap model on boring nodes
const raw = await parallel(angles.map(a => () => agent({
  task: `research: ${a}. every claim needs a source url + date.`,
  schema: Finding,              // validated output, not free text
  model: "haiku",               // boring node → cheap
})));

// REDUCE — plain code. no model, no tokens.
const findings = dedupeBySource(raw.flat().filter(Boolean));

// VERIFY — a FRESH skeptic per finding, trying to kill it
const survivors = await parallel(findings.map(f => () => agent({
  task: "try to disprove this. return keep | drop + why.",
  input: f,                     // the finding ONLY, never the worker's chat
  model: "sonnet",              // judgment node → stronger
})));

// SYNTHESIZE — one agent writes the answer from what survived
return agent({ task: "one report, ranked by confidence, sources attached.",
               input: survivors.filter(v => v.verdict === "keep") });
```

Cheap models where the work is boring, the strong one where judgment lives, the reduce
done in free code, one synthesis at the end. Same skeleton behind a market scan, a code
review, a research report — swap the angles.

## The checker is the whole trick

**Never let the agent that did the work check the work.** Models miss most of their own
mistakes. Put a separate node on the edge whose only job is to try to kill the finding.

**And the catch nobody names: the checker needs a clean context.** Hand it the worker's
chat and it isn't checking, it's nodding along to itself in a different font. *A graph of
agents sharing one context is a single loop in a costume — it breaks the same way, later
and pricier.*

```text
▸ VERIFIER NODE
INPUT:    the finding only — never the worker's chat
CONTEXT:  fresh and empty; it has not seen the work it judges
CHECKS:   three lenses in parallel (three different beat ten identical)
  1. is it correct?      → does the claim hold up
  2. is it current?      → is the source recent, not stale
  3. is the source real? → does the link resolve to the claim it's cited for
PASS:     keep only on majority
FAIL:     drop before it reaches the final answer
```

Verify a **real signal** — "the test actually passed", not "the agent said it's done".

## Where graphs break — build the guard in

1. **Context collapse.** 1,000 outputs into one synthesis blows the window.
   → **Layer the fan-in:** batch → summarize each batch → combine the summaries. Never
   pour the raw pile into the final step.
2. **False independence.** See the hidden-edge audit above. Isolate or serialize.
3. **Silent node failure.** In a chain a failure is obvious; in a graph one dead node
   among 200 slips into a report that looks complete.
   → **Every merge counts its inputs against what it expected and flags the gap.** Never
   synthesize on a partial set and call it complete.

## Anchors — topology does not buy truth

Build every checker on outputs derived from the same source and everything is
**consistent while nothing is verified.** That graph fails exactly like the single loop
did — later, pricier, with more green lights on the way down.

A graph needs **nodes that cannot be argued with**: a test that *actually ran*, a number
pulled live from the source system, revenue that landed, a customer who stayed. And some
rules stay **frozen** precisely because they're the ones an optimizer would bend to win.

> The graph is only as honest as the things inside it that refuse to move.

## When NOT to build one

A graph buys **breadth, not judgment**. Skip it when:
- the task is small or isolated (coordination is pure overhead)
- the user wants to approve every step (a graph's point is running wide without them)
- the work is exploratory and the goal isn't known yet (steer one agent instead)
- the steps genuinely depend on each other

**The tell: run the fake-edge test. If no two jobs are independent, there is no graph —
it's a loop, and a loop is fine.**

## Cost — state it before fanning out

A graph costs more than a chat. A lot more. Coordination gets cheaper; the work doesn't,
and a fleet burns a pile. Public reference point: the Bun runtime rewrite ran ~50
workflows, up to 64 concurrent agents, ~535k → 1M+ lines in ~11 days — **and ~$165,000
in usage**, with a human designing and watching it throughout.

**Always: announce the planned agent count and rough cost, cap the first run small, watch
what it costs, widen only once a run has earned it.** Honor the build bar in `manager` —
name the hours saved or the output shipped.

## Ready specs (swap the brackets)

```text
▸ DECISION-GRADE RESEARCH
GOAL: decision-grade research on [question]
FAN OUT:     5 distinct angles, one researcher each, in parallel
RULE:        every finding needs a source link + date
VERIFY:      a skeptic attacks each finding, drop what fails
MERGE:       survivors into one report ranked by confidence
CAP:         [n] · ON FAIL: flag non-returns
HUMAN GATE:  change nothing after the report without asking
```

```text
▸ REPO / CODEBASE SWEEP
GOAL: find every [pattern] and propose a fix for each
FAN OUT:     one agent per file, in parallel, worktree-isolated
VERIFY:      independent checker per proposal, fresh context
DEDUPE:      against everything already seen
CAP:         [n] files this run
REPORT:      how many files came back, so nothing fails silently
```

```text
▸ DISCOVERY OF UNKNOWN SIZE (the cycle)
GOAL: hunt [target] for [issues]
FAN OUT:     finders in parallel
DEDUPE:      each new find against everything seen
VERIFY:      independent checker on survivors
LOOP:        until two rounds in a row find nothing new
CAP:         hard limit on total agents so it can't run away
REPORT:      final list ranked by severity
```

```text
▸ LAUNCH / GTM KIT
GOAL: full launch kit for [thing], aimed at [audience]
PARALLEL (research):  buyer + their exact words · where they spend time · competitor pitches
MERGE:       one-page positioning doc
HUMAN GATE:  show the positioning doc before any writing
PARALLEL (writing):   landing copy · launch posts · outreach messages
VERIFY:      checker compares every asset to the positioning doc, flags drift
HUMAN GATE:  never send or publish anything
```

## Worked examples — shapes worth drawing

Starting points, not verified plans. Re-run the audit against your own files before acting.

**A weekly discovery pipeline** (scrape → score → shortlist → act) — a chain by default, but
*scoring each item is independent*: fan out one scorer per new row, verify with a fresh
skeptic, merge single-writer. Hidden edge: every worker appends to the same table, so the
merge is one writer, never parallel.

**A media/content pipeline** (brief → shotlist → generate → QC → assemble) — mostly real
edges, since each stage consumes the last. But *generation per shot is independent* — fan out,
QC each on a fresh checker. Hidden edge: a shared credit balance and rate-limited providers,
so cap concurrency.

**A per-client review process** — clients are independent by construction: one node each,
verify against a rule set, merge into one pack. Anchor on raw source values, never on a
summary of them.

**A site or docs build** — parallel by page or section, then one merge pass for voice
consistency. Verify every factual claim on a fresh checker; placeholder strings reaching
production is exactly what an anchor catches.

**A mature multi-stage pipeline** — worth auditing, and often the answer is *don't*. One real
audit found **zero fake edges**: every candidate passed real data, and a shared browser session
created hidden edges on top. That is the skill working correctly — *if no two jobs are
independent, there is no graph; it's a loop, and a loop is fine.* It is also why the audit must
read each node's **declared inputs**, never its one-line description: all three "obvious" fake
edges there turned out to be real.

## Related — don't duplicate these

- **`manager`** — owns *routing* (which model per node) + budget ceiling + retry cap +
  the build bar. This skill owns *topology* (what waits for what). Use both: draw the
  graph here, route the nodes there.
- **`Workflow` tool docs** — the machinery and its patterns. Read rather than reinvent.
- **`/loop`** — when the fake-edge test finds nothing independent, it's a loop; that has
  its own 4-condition gate in `~/CLAUDE.md`.
- **The verify-before-asserting rule** — no claim ships unless it was checked live
  against the source system. That rule is what an anchor enforces mechanically.
