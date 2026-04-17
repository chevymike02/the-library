# /library audit

**FLINT-specific command (not in Dan's base 8).** Scans the compiled Brain wiki and the library catalog, proposes gaps — new skills to build, skills to improve, or orphaned entries to remove.

## When to use

- User runs `/library audit` or says "find skill gaps", "what skills are we missing", "audit the library against the wiki"
- After a large wiki-compile batch (new topics may reveal new skill opportunities)
- Before a planning session — surface improvement candidates
- Scheduled (e.g., weekly) to keep the skill backlog fresh

## Steps

### 1. Read the library catalog

- Parse `library.yaml` and enumerate every entry under `library.skills`, `library.agents`, `library.prompts`.
- Build a set of known capability-names (skill names + description keywords).

### 2. Read the Brain wiki topics

- Glob `~/Desktop/Flintv2/Brain/wiki/topics/*.md`.
- For each topic, read the Summary, Key Facts, and Decisions sections.

### 3. Gap analysis — four findings

**Finding A — Manual workflows with no skill wrapping them:**
- Patterns in topic text that indicate repeated manual steps: "run X, then Y, then Z", "I keep doing this by hand", "we manually", "currently runs manually", "step-by-step process for X".
- For each detected workflow, check whether a skill in `library.yaml` covers it by matching keywords against skill descriptions.
- If no match → propose a new skill. Shape:
  ```
  Proposed skill: <slug>
  Evidence: <topic>.md line N describes <workflow summary>
  Suggested allowed-tools: <inferred from workflow>
  Closest existing skill: <name or "none">
  Priority: high | medium | low (based on workflow frequency)
  ```

**Finding B — External services cited in wiki without a wrapping skill:**
- Grep wiki topics for API mentions (e.g., "via Firecrawl", "calls the Outscraper API", "uses the Teller mTLS endpoint").
- For each unique service, check if a skill wraps it.
- If not → propose a service-wrapper skill.

**Finding C — Orphan catalog entries:**
- For each entry in `library.yaml`, check that the `source` path actually exists on disk (for local://) or is reachable (for http://, via `gh api` HEAD check).
- If missing → propose removal or path correction.

**Finding D — Low-score skills (from `eval.last_score` field):**
- For each skill with `eval.last_score` below 90% of `criteria_count`, add to improvement list.
- Skills with `eval.last_score: null` (never run) rank as medium priority for initial eval-and-improve run.

### 4. Write the skills-backlog file

Output to `~/Desktop/Flintv2/Brain/wiki/skills-backlog.md`:

```markdown
# Skills Backlog — Generated 2026-MM-DD

## New skills proposed (Finding A + B)
| Priority | Slug | Evidence | Suggested tools |
|----------|------|----------|-----------------|
| ...

## Existing skills to improve (Finding D)
| Priority | Name | Current score | Failure mode |
|----------|------|---------------|--------------|

## Orphan entries (Finding C)
| Entry | Issue | Proposed fix |
|-------|-------|--------------|
```

### 5. Update library.yaml

Populate `improvement_queue` in `library.yaml`:

```yaml
improvement_queue:
  - { target: <skill-name>, action: improve, reason: "never evaled", priority: medium }
  - { target: <proposed-new-skill>, action: create, reason: "gap from audit", priority: high }
```

### 6. Return summary to caller

Short report: N new skills proposed, N existing to improve, N orphans, path to full backlog file.

## Rules

1. **Never auto-create skills.** Only propose. User reviews backlog, decides what to build.
2. **Never auto-remove catalog entries.** Only propose. Orphan detection flags; user confirms removal via `/library remove`.
3. **Cite evidence for every proposal.** Every entry in the backlog must reference a specific wiki topic file + line range.
4. **Respect wiki-keeper doctrine.** This cookbook reads Brain/wiki/ but never writes to topics/. Writes are confined to `library.yaml` and `Brain/wiki/skills-backlog.md`.

## Sources

- Pattern from FLINT skill infrastructure plan (`~/Desktop/Flintv2/Brain/raw/vault-import/Projects/flint/skill-library-infrastructure-plan-2026-04-16.md`)
- Builds on Brain wiki topics `research-skills-and-self-improvement` (DBS + autoresearch) and `claude-code-patterns` (Library meta-skill, self-improving skills)
- Complements Dan's base 8 commands — reads the catalog his commands manage, proposes what to add/change
