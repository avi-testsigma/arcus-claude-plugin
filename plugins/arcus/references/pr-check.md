# PR check: budgets, when to try to break it, and the local mode

The details behind `/arcus:pr-check`. The skill says the order.

## When the break lane runs

| Signal | Then |
|---|---|
| `ARCUS_PR_CHECK_BREAK=off`, or the PR has the label `arcus:no-break` | Skip it. Say so in the report |
| `ARCUS_PR_CHECK_BREAK=on`, or the label `arcus:break` | Run it |
| Every changed file is documentation (`*.md`, `docs/`), a test (`*.test.*`, `__tests__/`, `e2e/`) or CI config | Skip it |
| Otherwise | Run it when the diff changes something a user can see: a screen, a route, a request the app makes, data it shows. Say in one line why |

## Budget

The run stops at whichever limit comes first, and says which.

| Level (`ARCUS_PR_CHECK_BUDGET`) | Time for the break lane | Scenarios written |
|---|---|---|
| `low` (default) | 20 minutes | 8 |
| `high` | 45 minutes | 20 |

The time counts from the first scenario to the last run on the PR's build. The regression lane and the base runs are not
counted: they are bounded by the number of tests.

Order scenarios so the ones most likely to find something run first: what the diff changes that a user sees, then the
callers of the changed code, then the areas where past fixes cluster. When the budget runs out, the rest are listed in
the report as not run.

## A scenario

- One user goal per test, written as a user would do it, with a `verify` for each thing a user should see.
- Not a copy of a story case: the regression lane already runs those.
- Not about how the code is built (class names, internal state). The judge throws those out as test issues.
- Never shaped to fail. A scenario that passes is a scenario that found nothing.

## What counts

`node S diff` keeps a test only when it **failed on the PR's build and failed again on a re-run there, while the base
build passed or failed another way** (at another step, or with another message). A story test that was already broken
on the base can still show this PR breaking it earlier. Everything else is listed in the report and not judged:

- passed on both: the story's cases that held,
- failed the same way on the base: already broken, not this PR's,
- passed on the re-run: flaky,
- did not compile, or did not run on one side.

## The judge

Arcus judges each difference from the story, its cases, the test, both outcomes and the failing step's screenshot from
each build (`node S request` attaches them; `--no-images` leaves them out). It never sees the diff. Verdicts:
`real_bug`, `intended_change`, `test_issue`, `environment_issue`, `ambiguous`. A story case that is a real bug or
unclear blocks the merge. An intended change asks for the case to be updated in QI. The break lane never blocks; a
low-confidence bug there is reported as unclear.

## Local mode: one address, two builds

Locally, the app's sign-in can be tied to one host, so both builds are served at the same address one after the other.
Set `ARCUS_PR_URL` and `ARCUS_BASE_URL` to that address, and `ARCUS_PR_CHECK_SWITCH` to a command that replaces the PR's
build with the base build and returns once it is serving. The skill runs everything on the PR's build first, runs the
switch once, then runs the base side.

## Environment

| Variable | Means |
|---|---|
| `ARCUS_PR_URL`, `ARCUS_BASE_URL` | The two deployed builds |
| `ARCUS_PR_NUMBER`, `ARCUS_HEAD_SHA`, `GITHUB_REPOSITORY` | Where the report goes |
| `ARCUS_STACK_DIRS` | Other repos of the stack, checked out, colon-separated, to read |
| `ARCUS_PR_CHECK_BUDGET` | `low` or `high` |
| `ARCUS_PR_CHECK_BREAK` | `on` or `off` |
| `ARCUS_PR_CHECK_SWITCH` | Local mode only: the command that serves the base build |
| `ARCUS_PR_CHECK_RESET` | A command that puts the test data back, run before each run of the story tests |
| `ARCUS_PR_CHECK_POST` | `1` posts the check and the comment |
| `ARCUS_PR_CHECK_PUSH` | `1` pushes real findings to QI as pending cases without asking |
