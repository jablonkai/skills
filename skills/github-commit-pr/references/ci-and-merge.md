# Watching CI and merging

Same procedure for both flows: after pushing, wait for the GitHub Actions run triggered by the new
commit, then merge once it is green.

## Watch the run

```bash
sha=$(git rev-parse HEAD)
run_id=""
for _ in $(seq 1 10); do
  run_id=$(gh run list --commit "$sha" --limit 1 --json databaseId --jq '.[0].databaseId // empty')
  [ -n "$run_id" ] && break
  sleep 5
done
[ -n "$run_id" ] || { echo "No CI run registered for $sha after 50s" >&2; exit 1; }
gh run watch "$run_id" --exit-status
```

- Select the run by **commit**, never by branch. `--branch ... --limit 1` returns the newest run *on
  the branch*, which may still be an older commit's run if CI has not registered the push yet — and
  if that stale run is green, the skill would merge on the strength of results that say nothing
  about what was just pushed. Pushing twice in quick succession is exactly when this bites.
- `--exit-status` makes the command exit non-zero when the run fails, so failure is easy to detect.
- The loop covers the registration delay: `gh run list` legitimately returns empty for a few seconds
  after a push, which is why the lookup is retried rather than trusted on the first call.

**If the run fails:** when the logs are long, first delegate root-causing to a read-only subagent
(see "Delegating to subagents" in SKILL.md) and pass its conclusion — failing step, error, and
`file:line` — into the `github-fix-action-error` skill; otherwise invoke that skill directly. After
the fix is committed and pushed, re-watch the new run. Repeat until the build is green or the user
aborts.

Never merge on an in-flight or pending status — `gh run watch --exit-status` is the gate.

## Step 1: Verify mergeability

```bash
gh pr view --json number,mergeable,mergeStateStatus,reviewDecision
```

Interpret the result:

- `mergeable: MERGEABLE` and `mergeStateStatus: CLEAN` → ready to merge
- `mergeStateStatus: HAS_HOOKS` → ready (post-merge hooks will run, that's fine)
- `mergeStateStatus: BLOCKED` → branch protection blocks the merge (e.g. required reviewers,
  required signed commits, code owner review). Report which gate is blocking and stop — do not
  bypass with `--admin` unless the user explicitly asks
- `mergeStateStatus: BEHIND` → base branch moved forward and the repo requires an up-to-date branch.
  Offer `gh pr update-branch <number>` and re-watch CI afterward
- `mergeable: CONFLICTING` → conflicts with the base branch. Stop and ask the user to resolve
  manually
- `mergeStateStatus: UNSTABLE` → required checks haven't completed even though our watched run
  passed. Investigate which check is pending before merging
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
