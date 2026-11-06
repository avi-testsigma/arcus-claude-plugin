---
name: pr-check
description: Use when a pull request's build is deployed and someone asks Arcus to test it (a "/arcus test" PR comment in CI, or a developer asking to check a PR against its base). Runs the story's own tests on the PR's build and on the base build, then tries to break the change with new scenarios, keeps only what fails on the PR in a way the base does not, and has Arcus judge each against the story and report one check and one comment. Never edits the app, never accepts.
---

# PR check: test the deployed change against its base, and try to break it

Two builds are deployed: the PR's and the base. You test both the same way and report only what this PR changed. Two
lanes:

- **Regression.** The story's own tests, the ones `/arcus:verify` wrote. A story case that breaks blocks the merge.
- **Break it.** New scenarios you write to find what the change broke that no case covers. Advisory: they never block.

You never see the verdict-making side: Arcus judges each difference against the story, not the diff. Your job is to
find differences honestly. Details, budgets and the local mode are in `${CLAUDE_PLUGIN_ROOT}/references/pr-check.md`.

`S` below is `${CLAUDE_PLUGIN_ROOT}/scripts/pr-check.mjs`, run with `node`. Keep every file this run writes under
`.arcus/pr-check/` (the work folder, `W`), except the scenario tests, which `arcus run` needs in the project's `tests/`.

## 1. What to test

You need: the PR build's address, the base build's address, the repo (`owner/name`), and the PR number and head commit
when there is a PR. They come from the environment (`ARCUS_PR_URL`, `ARCUS_BASE_URL`, `GITHUB_REPOSITORY`,
`ARCUS_PR_NUMBER`, `ARCUS_HEAD_SHA`), from the trigger comment, or from the user. Never guess an address. Check both
answer (`curl -sS -o /dev/null -w '%{http_code}' <url>`). One that does not: stop and say which.

Then `/arcus:setup`'s checks: the CLI, the sign-in, `arcus browsers list`, and `web` in the project's platforms.

## 2. The story

Find the issue key as `references/verifying.md` says: the trigger comment, the branch name, the commits, the PR title.

- Found: say where.
- Not found: guess. List the active sprints' stories (`arcus sprint list --json`, `arcus issue list <id> --json`), read
  the diff, and pick the story the change most plainly serves. Mark it **guessed**. A guess is said in the comment, and a
  reviewer corrects it. No story fits at all: go on without one; the regression lane then has nothing to run.

```
arcus pr-check context --issue-id <key> --json > W/context.json
```

## 3. Regression lane

```
node S story-tests --context W/context.json
```

It lists the test files that automate one of the story's cases (from `arcus.lock`). None: the lane says so in the
report ("no automated tests for this story yet") and you go on.

Run them on the PR's build, re-run the ones that failed, then (after step 5's switch, if any) on the base build. Story
tests can change the data they run on; when `ARCUS_PR_CHECK_RESET` is set, run it before each of these runs:

```
node S run --url <pr url> [--var ...] <files> > W/regression-pr.json
node S run --url <pr url> [--var ...] <failed files> > W/regression-retry.json
```

Do not fix, edit or weaken a story test here, even a failing one. A story test is the bar. The judge decides what a
failure means.

## 4. Break lane

First decide whether to run it, as `references/pr-check.md` says: `ARCUS_PR_CHECK_BREAK=off` or a change that touches
only docs or tests skips it; `on` forces it. Say why.

Then, inside the budget (`references/pr-check.md`):

1. **Learn the change.** Read the diff (`git diff <base>...HEAD`), the code it touches and what calls it, in this repo and
   in the other repos of the stack when they are checked out (`ARCUS_STACK_DIRS`). Read the story and its cases from
   `W/context.json`. Read past fixes to the same files: `git log --since=6.months --grep=fix -i --format='%h %s' --
   <files>`.
2. **List scenarios**, ranked: first what the diff changes that a user sees, then what calls the changed code, then
   where past fixes cluster. A scenario is covered only by a story test the regression lane ran in this check. A case
   in QI with no test file here, pending or not, covers nothing: write the scenario. Say the list with one line of why
   each.
3. **Write each** as one test through `/arcus:author`'s rules, in the project's `tests/`, named
   `pr-check-<short-name>.sigma`. Reuse the repo's elements first. `arcus check` clean before it runs.
4. **Run it on the PR's build** with `/arcus:run`'s rules. A failure whose owner is the test (a wrong locator, a missing
   wait): fix the test, at most three rounds. A failure whose owner is the app: keep it as it is. That is a candidate.
   A pass: the scenario found nothing; keep it in the count and move on.
5. Stop when the budget is spent or the list is done, and say which.

Re-run the candidates on the PR's build into `W/break-retry.json`. Their first runs, in one suite, go in
`W/break-pr.json` (`node S run` over the candidate files).

**Never weaken a scenario to make it pass, and never make one fail on purpose.** A scenario states what a user should
see; the build either does it or not.

## 5. The base build

When the two builds share one address (the local mode in `references/pr-check.md`), run `ARCUS_PR_CHECK_SWITCH` now and
wait until the address answers again. Then, after `ARCUS_PR_CHECK_RESET` if it is set:

```
node S run --url <base url> [--var ...] <story test files> > W/regression-base.json
node S run --url <base url> [--var ...] <candidate files> > W/break-base.json
```

## 6. Report

```
node S diff --lane regression --pr W/regression-pr.json --base W/regression-base.json --retry W/regression-retry.json > W/regression.json
node S diff --lane break --pr W/break-pr.json --base W/break-base.json --retry W/break-retry.json > W/break.json
node S request --context W/context.json --pr-url <url> --base-url <url> --repo <owner/name> [--pr <n>] [--sha <sha>] [--guessed] --diff W/regression.json --diff W/break.json --stats W/stats.json > W/request.json
arcus pr-check report W/request.json --json > W/report.json
```

`W/stats.json` holds `budget`, `minutes`, `scenarios_run` and `stopped_because`. Add `--post` to the report only when
`ARCUS_PR_CHECK_POST=1`: that posts the check and the comment on the PR. Otherwise show the rendered comment.

## 7. Findings become pending tests

A break-lane finding the judge calls `real_bug` is a test worth keeping. With `ARCUS_PR_CHECK_PUSH=1`, hand those files
to `/arcus:push` with `--sprint <id> --issue-id <key>`: they land in QI as pending cases on the story, for a person to
accept. The variable is the yes `/arcus:push` asks for: still run and show its dry run first, then push. Without it,
list them and offer the push. Never pass `--accept`.

Then delete every `pr-check-*.sigma` file and any element this run created that was not pushed. Never commit them.

## 8. Say

The story (and whether it was guessed), the regression result, how many scenarios ran and what was found, the check's
conclusion, whether it was posted, what was pushed, and what did not run and why.

## What this skill never does

- Edit the app's code, or a story test, or a case's expected result.
- Weaken a scenario, or write one meant to fail.
- Run a build the user did not name, or guess an address.
- Post without `ARCUS_PR_CHECK_POST=1`, or push without `ARCUS_PR_CHECK_PUSH=1` or a yes.
- Accept anything, sign in, or start the agent or the app.
- Commit scenario files, or leave them in `tests/`.
