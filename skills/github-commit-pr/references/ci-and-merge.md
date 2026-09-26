# Watching CI and merging

Same procedure for both flows: after pushing, wait for the GitHub Actions run triggered by the new
commit, then merge once it is green.

## Watch the runs

A push can trigger several workflows (e.g. `build.yml` and `lint.yml`), and each is its own run.
Watch **all** runs for the pushed commit — merging after only the first one finishes would land a
change whose other workflow is still red.

```bash
sha=$(git rev-parse HEAD)
run_ids=""
for _ in $(seq 1 10); do
  run_ids=$(gh run list --commit "$sha" --json databaseId --jq '.[].databaseId')
  [ -n "$run_ids" ] && break
  sleep 5
done
[ -n "$run_ids" ] || { echo "No CI run registered for $sha after 50s" >&2; exit 1; }
failed=""
for id in $run_ids; do
  gh run watch "$id" --exit-status >/dev/null || failed="$failed $id"
done
echo "failed runs:${failed:- none}"
```

- Select runs by **commit**, never by branch. `--branch ... --limit 1` returns the newest run *on
  the branch*, which may still be an older commit's run if CI has not registered the push yet — and
  if that stale run is green, the skill would merge on the strength of results that say nothing
  about what was just pushed. Pushing twice in quick succession is exactly when this bites.
- `--exit-status` makes each watch exit non-zero when its run fails, so failure is easy to detect.
- The loop covers the registration delay: `gh run list` legitimately returns empty for a few seconds
  after a push, which is why the lookup is retried rather than trusted on the first call.
- No run after 50s: check whether the repo has workflows that trigger on this event
  (`ls .github/workflows/`, their `on:` keys). A repo with no CI at all has nothing to wait for —
  say so in the report and go to the merge step; a repo whose workflows simply haven't registered
  yet gets one more wait, then report and stop.

**If a run fails**, first classify the failure — the right response depends on *why* it failed.

### Billing / quota failures: validate locally, then merge

GitHub refuses to start jobs when the account's Actions minutes or spending limit are exhausted or a
payment failed. The run shows up as failed, but no step ever executed — the code was never tested,
so the red status says nothing about the change. Recognise it by both signals:

```bash
gh run view "$id" --json jobs --jq '.jobs[] | "\(.name): \(.conclusion), \(.steps | length) steps"'
gh run view "$id" | grep -iE 'billing|spending limit|payments have failed|account is locked'
```

- every failed job has **0 steps** — nothing ran — and
- the annotation reads like *"The job was not started because recent account payments have failed
  or your spending limit needs to be increased"* or *"…your account is locked due to a billing
  issue"*.

A user's guess ("probably out of Actions minutes") is not evidence — check the signals. A job that
ran steps and failed a test is a real failure even if the account is also near its limit.

When it is a billing failure, don't invoke `github-fix-action-error` — there is nothing in the code
to fix, and retrying CI will fail the same way. Run CI's checks locally instead:

1. Read the workflow files that trigger on this event (`.github/workflows/*.yml`, jobs with
   `pull_request`/`push`) and collect their `run:` commands — build, test, lint, validate scripts.
   Also run any validation the repo's `AGENTS.md`/`CLAUDE.md`/`CONTRIBUTING.md` requires before
   committing.
2. Run them locally from the repo root (quiet flags, filter the output). Skip steps that only make
   sense on the runner — deploy, publish, upload-artifact, anything needing repository secrets —
   and list them as not verified.
3. **All pass** → the change may be merged on the strength of the local validation. Tell the user
   plainly in the merge confirmation that CI did not run and what was run locally instead, e.g.
   *"CI didn't start (GitHub billing: spending limit). Locally `validate.sh` and `lint.sh` pass.
   Merge PR #12 with `--squash`?"* Then continue with the mergeability check below.
4. **Anything fails** → it's a real failure: fix it like any other, and don't merge.

If branch protection requires the failed check, `gh pr merge` will be `BLOCKED`. Local validation
does not by itself authorise `--admin`: report the block and let the user decide whether to bypass
it (explicitly) or wait until billing is fixed and re-run CI with `gh run rerun "$id"`.

### Real failures: root-cause and fix

When the logs are long, first delegate root-causing to a read-only subagent (see "Delegating to
subagents" in SKILL.md) and pass its conclusion — failing step, error, and `file:line` — into the
`github-fix-action-error` skill; otherwise invoke that skill directly. After the fix is committed
and pushed, re-watch the new runs. Repeat until the build is green or the user aborts.

Never merge on an in-flight or pending status — `gh run watch --exit-status` is the gate. The only
exception to "green CI before merge" is the billing case above, and there local validation takes
CI's place; it is never skipped outright.

## Step 1: Verify mergeability

```bash
gh pr view --json number,mergeable,mergeStateStatus,reviewDecision
```

Interpret the result:

- `mergeable: MERGEABLE` and `mergeStateStatus: CLEAN` → ready to merge
- `mergeStateStatus: HAS_HOOKS` → ready (post-merge hooks will run, that's fine)
- `mergeable: UNKNOWN` / `mergeStateStatus: UNKNOWN` → GitHub is still computing mergeability,
  common right after a push. Wait a few seconds and query again before deciding anything
- `mergeStateStatus: BLOCKED` → branch protection blocks the merge: a required check that is
  pending or failed, required reviewers, code owner review, signed commits. Report which gate is
  blocking and stop — do not bypass with `--admin` unless the user explicitly asks
- `mergeStateStatus: BEHIND` → base branch moved forward and the repo requires an up-to-date branch.
  Offer `gh pr update-branch <number>` and re-watch CI afterward
- `mergeable: CONFLICTING` / `mergeStateStatus: DIRTY` → conflicts with the base branch. Stop and
  ask the user to resolve manually
- `mergeStateStatus: UNSTABLE` → mergeable, but a non-required check is failing or still running.
  Look at `gh pr checks <number>` and tell the user which one before merging — it may be a workflow
  you didn't watch
- `mergeStateStatus: DRAFT` → the PR is a draft. Ask whether to mark it ready (`gh pr ready`)
- `reviewDecision: CHANGES_REQUESTED` → at least one reviewer has requested changes. Stop and let the
  user address the review

## Step 2: Choose a merge strategy

Read the repo's allowed strategies so the chosen flag will actually work:

```bash
gh repo view --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed
```

Preference order: `--squash` (cleanest history for feature PRs), then `--merge`, then `--rebase`.
Pick the first one that's allowed. The skill exists to land PRs cleanly, so squash is the right
default — but never pick a strategy the repo doesn't permit, or `gh pr merge` will reject it.

## Step 3: Confirm and merge

Merging is a shared-state action visible to collaborators, and it's effectively irreversible (revert
PRs are possible but messy), so confirm with the user once before doing it. Keep the prompt short —
they already opted in by invoking this skill:

> "CI is green. Merge PR #<number> with `--squash` and delete the branch? (y/n)"

If the user declines, skip the merge and just report. If they confirm:

```bash
gh pr merge <number> --<strategy> --delete-branch
```

Notes:

- `--delete-branch` removes both the local and remote branch after merge — this is the usual
  cleanup, but skip the flag if the user objects.
- If the merge command fails because of branch protection (e.g. 405 method not allowed, "Pull
  Request is not mergeable"), surface the error and stop. Do not retry with `--admin` unless
  explicitly asked.
- If `gh pr merge` succeeds, the local branch is gone; subsequent `git` commands should not assume it
  still exists. Switch back to the base branch and pull:

```bash
git checkout <base-branch>
git pull
```
