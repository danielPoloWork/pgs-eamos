# Git / PR / CI / Release Schema

The branch / commit / PR / release policy as data (RFC-0001 §8; AGENTS.md §6). The workflow gates
read it; the reference instance is [`git.yaml`](git.yaml).

```yaml
version: <int>
branch_naming: { pattern: "<type>/<short-kebab>", types: [<type>, ...] }
commit:
  convention: conventional-commits
  scopes: [<scope>, ...]
  one_logical_change_per_pr: <bool>
  one_pr_at_a_time: <bool>
pr:
  draft_by:  <role | implementing-role>   # who drafts
  opened_by: human                         # who opens / marks ready (non-delegable)
  merged_by: human                         # who merges (non-delegable)
  merge_method: <squash | merge | rebase>
  assignee: <str>
  one_type_label: <bool>
  required_crosslinks: [rfc, milestone]    # the PR body must reference these
  template: <path to PR template>
release: { scheme: semver, ..., publish_by: human }   # the human publishes (non-delegable)
traceability: { graph: <str>, gate: <gate-id> }
```

## Invariants

- **The human opens, merges, and publishes.** `opened_by`, `merged_by`, `publish_by` are `human`
  and non-delegable (AGENTS.md §6). The agent drafts the PR and the draft release; it never crosses
  these.
- **Exhaustive PR metadata.** Every PR carries an **assignee**, exactly **one type label**, a
  **milestone**, and a body that crosslinks its **RFC** and **milestone item** — the bar this repo
  imposes (mirrors EADOS).
- **One logical change per PR; one PR at a time.**
