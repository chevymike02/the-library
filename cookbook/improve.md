# /library improve <skill-name>

**FLINT-specific command (not in Dan's base 8).** Runs the Karpathy autoresearch loop on one target skill — binary-assertion evals, mutate-one-thing-at-a-time, git reset on score drops, keep winners, bump version.

Based on: Karpathy autoresearch pattern (https://www.youtube.com/watch?v=qKU-e0x2EmE) + Simon Scrapes self-improving skills binary-eval loop (https://www.youtube.com/watch?v=wQ0duoTeAAU). Vault sources: `Brain/raw/vault-import/Research/autoresearch-skill-optimization.md`, `Research/self-improving-skills-video-research.md`.

## When to use

- User runs `/library improve <skill>` or says "improve X skill", "optimize wiki-compile", "run autoresearch on Y"
- As a follow-up to `/library audit` (which produces improvement candidates)
- After a skill's eval score drops or a new failure mode appears

## Preconditions

1. **Target skill has `eval.json`** at `<skill-dir>/eval.json` with binary assertions. If missing, stop and tell user: "No eval.json found. Create one first — see `~/.claude/skills/library/references/eval-format.md`."
2. **Target skill is git-tracked** (source-of-truth copy in `Brain/skills/` or the runtime copy is under git). This enables `git reset --hard HEAD~1` on score drops.
3. **Budget exists.** Default caps: 10 iterations OR $5 OR 30 minutes, whichever first. Override with `--iterations N`, `--budget-dollars N`, `--minutes N`.

## Budget caps (hard)

| Cap | Default | Purpose |
|-----|---------|---------|
| Iterations | 10 | Prevents runaway loops |
| Dollars | $5.00 | Prevents cost explosion |
| Wall-clock minutes | 30 | Prevents hung runs |

Check all three before every iteration. First cap hit → stop with final report.

## The loop (Karpathy, verbatim)

### Step 1 — Load state

Read:
- `<skill-dir>/SKILL.md` (the thing being optimized)
- `<skill-dir>/eval.json` (test cases + binary assertions)
- `library.yaml` entry for this skill (current `eval.last_score`, `version`)

### Step 2 — Baseline run

For each test case in `eval.json`:
- Spawn a skill-runner subprocess (via Skill tool or Claude Code CLI) with the test prompt
- Collect the output
- Run every assertion against the output
- Total score: `passes / (assertion_count × test_case_count × runs_per_case)`

Default: 10 runs per test case. Record baseline score (e.g. 32/40 = 80%).

If baseline == 100%, skip to Step 7 (record + exit).

### Step 3 — Identify dominant failure mode

Group failing assertions by assertion text. The mode with the most failures is the dominant. Only mutate for the single dominant mode per iteration. One change at a time. Simon's rule.

### Step 4 — Propose mutation

Load SKILL.md. Propose ONE mutation in this priority order:

| Priority | Mutation | When to use |
|----------|----------|-------------|
| 1 | Add explicit rule in SKILL.md body | Skill doesn't follow rule X |
| 2 | Strengthen existing rule | Skill forgets rule X under some conditions |
| 3 | Add example of correct output | Skill produces wrong format |
| 4 | Restructure workflow steps | Skill does steps in wrong order |
| 5 | Update description frontmatter | Failure is trigger-accuracy, not output quality |

Never mutate more than one section per iteration.

### Step 5 — Commit + re-run

1. Write mutated SKILL.md to `<runtime-skill-dir>/SKILL.md`
2. Mirror write to `<brain-skill-dir>/SKILL.md` (source-of-truth twin)
3. `git add` both, `git commit -m "improve: <skill> iteration N — <one-line description>"`
4. Re-run Step 2 with mutated skill

### Step 6 — Accept or reject

- **New score > old score:** accept. Update `library.yaml`:
  - `eval.last_score` → new score
  - `eval.last_run` → now ISO8601
  - `eval.criteria_count` → computed from eval.json
  - Return to Step 3 unless any budget cap hit
- **New score ≤ old score:** reject. `git reset --hard HEAD~1` on BOTH runtime and brain twin. Record attempt. Try next-priority mutation (up to 3 tries on same failure mode before giving up).

### Step 7 — Final commit + report

On exit (perfect score OR budget hit OR 3-try ceiling on a mode):

1. Bump `metadata.version` in SKILL.md frontmatter:
   - Patch (1.0.X) for rule-add / strengthen
   - Minor (1.X.0) for restructure / new example
   - Major (X.0.0) for workflow rewrite
2. Append to `<skill-dir>/CHANGELOG.md`:
   ```markdown
   ## v<new-version> — <YYYY-MM-DD>
   Autoresearch run: <old-score> → <new-score> in <N> iterations.
   Accepted mutations:
   - <description of each accepted change>
   Rejected mutations:
   - <each rejected change + why>
   Budget: <iterations> iterations, $<cost>, <minutes> min.
   ```
3. Final `git commit -m "improve: <skill> v<old> → v<new> — score <old-score> → <new-score>"`
4. Update `library.yaml`:
   ```yaml
   - name: <skill>
     ...
     version: <new>
     last_improved: <YYYY-MM-DD>
     eval:
       last_score: <new-score>
       last_run: <iso8601>
       criteria_count: <n>
   ```
5. Return summary: iterations run, mutations accepted, mutations rejected, final score, cost, path to CHANGELOG.

## Example report

```
/library improve wiki-compile

Loading wiki-compile eval.json: 4 binary criteria, 5 test cases.
Baseline: 32/40 (80%).

Iter 1 — dominant failure: "every topic has companion assertions.json" (6/10 fail).
  Mutation: strengthen Phase 3.3 with explicit example. → 38/40 ACCEPT.
Iter 2 — dominant failure: "source-precedence applied" (2/10 fail).
  Mutation: add plan-doc-vs-decisions-log example. → 40/40 ACCEPT.

Perfect score reached in 2 iterations. Stopping.
Budget used: 2/10 iterations, $0.47, 4min.
Committed: wiki-compile v1.1.0 → v1.3.0.
library.yaml updated.
CHANGELOG.md appended.
```

## Rules

1. **Binary assertions only.** eval.json assertions must be yes/no. No scales. If you find a non-binary assertion, stop and tell user to convert it first.
2. **One mutation per iteration.** Multi-variable changes = indeterminate causation.
3. **Git reset on drops.** Always. Both twins. Never keep a mutation that didn't improve score.
4. **Budget caps are absolute.** Never override without explicit user flag.
5. **Don't improve skills with `agent_profiles: [wiki-keeper]` unless wiki-keeper doctrine tests are in eval.json.** Those skills have strong domain rules — generic autoresearch might undo them. Require explicit `--bypass-doctrine-check` flag plus a warning.
6. **Never skip Step 5's mirror-write.** Runtime and brain twins must stay identical. Drift = bug.

## References

- `~/.claude/skills/library/references/eval-format.md` (to be written — spec for eval.json)
- `~/.claude/skills/library/references/karpathy-loop.md` (to be written — detailed playbook)
- `Brain/wiki/topics/research-skills-and-self-improvement.md` — DBS + autoresearch compiled wiki
- `Brain/wiki/topics/claude-code-patterns.md` — Library meta-skill + self-improving skills context
