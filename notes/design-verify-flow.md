# Design: verify a change with the story's own cases (0.9.0)

0.8.0 runs one test that the user names. This note adds one skill, `verify`, for the developer whose coding agent has
just changed a user-facing flow. It automates the test cases that Arcus already holds for the story, runs them against
the local app until they pass, puts the evidence on the PR, and pushes the tests as pending cases linked to the story.
Read it with `design-authoring-plugin.md` and `design-run-skill.md`.

## Why a separate skill

`author`, `run` and `push` each do one job and stop. A developer who asks "prove this change works" wants all three, in
order, for the cases of one story, ending in one PR comment. That is a flow over the other skills, not a step inside
any of them. `verify` owns the order and the PR comment. It calls the other skills for the work, so each keeps its own
gate: `author`'s `check`, `run`'s address rule, `push`'s dry run and yes.

## What it needs from the CLI

The QI commands of arcus-cli 0.1.3 on the `release/context-versioning` line, plus a case's content in `test show`
(it needs QI's plugin route for one case):

| Need | Command |
|---|---|
| The sprint | `arcus sprint list`, `arcus sprint show <id>` |
| The story | `arcus issue list <sprint>` |
| The story's cases | `arcus test list --sprint <id> --issue-id <key> --json` |
| What a case expects: preconditions, steps, expected results | `arcus test show <case id> --json` |
| Push as pending cases linked to the story | `arcus push --sprint <id> --issue-id <key>` (no `--accept`) |

A CLI without `arcus sprint` is too old: stop and run `setup`.

## The flow

```text
story ──► cases ──► author ──► run ──► PR comment ──► push (pending) ··· merge ··► developer accepts
                       ▲         │
                       └─ fix ───┘   fix the code or the test, never the case
```

1. **The story.** From what the user said, the branch name or the commit messages: an issue key. Then the sprint that
   holds it. Ask when neither is plain. Never guess a story.
2. **The cases.** `arcus test list --sprint --issue-id --json`, then `arcus test show <id> --json` for each case's
   steps. Each case is one test to automate. The case's steps and
   expected results are what the test must check. The diff decides which cases this change touches. It never decides
   what a case expects.
3. **No cases.** QI generates a story's cases. The skill does not invent them. It says so and stops, with where to
   generate them. A changed flow that the story's cases do not cover gets one candidate test, marked new in the comment.
4. **Author.** One `.sigma` file per case, titled as the case is titled, through `author`'s rules.
5. **Run.** Each test through `run`'s rules, against the local app, until it passes. The limits of `run` hold: three
   rounds, stop on the same failure twice.
6. **The PR comment.** One "Ran locally" comment, edited in place on each re-run. It is labelled as the developer's own
   run on their machine.
7. **Push.** Through `push`, with `--sprint` and `--issue-id`, so the tests land in QI as pending cases on the story.
   Never `--accept`.
8. **After merge.** The developer accepts the cases into Arcus. QA confirms them. The skill says so. It never accepts.

## Decisions

1. **Arcus decides what must pass.** The story's cases are the bar. The agent automates them first, and drafts a new
   case only for a changed flow they do not cover. That is what makes the result more than the developer's own opinion
   of what to check.
2. **A failure against an approved case is never fixed by editing the case.** Fixing the code is free. Fixing the test
   (a wrong locator, a missing wait) is free. Changing what an approved case expects is an intent change. The skill does
   not make it. It lists the case, the step, what the case expects and what the app now does under "Proposed intent
   changes" in the comment, and leaves the test failing. QA or the PM decides in QI.
3. **Never weaken a test.** `author`'s and `run`'s rule. Any change to a test's steps or `verify` lines after its first
   run is listed in the comment, so a reviewer sees it.
4. **A local run is the developer's signal, not proof.** The comment says "Ran locally" and whose machine. It never
   says "passed in Arcus", and it never presents itself as the check CI will run.
5. **Posting the comment needs a yes, once per PR.** It is visible to the team. The skill shows the comment first. Later
   edits of the same comment, on re-runs, need no new yes. With no PR yet, the comment is printed for the user to paste.
6. **The comment is found by a marker**, `<!-- arcus:ran-locally -->`, so a re-run edits it and never adds a second one.
7. **Every gap is said.** A case that was not automated, a test that did not run, a stack that was down: each is a line
   in the comment, with why. No silent skip.
8. **Push never writes to the library directly.** If `ARCUS_PUSH_DIRECT_LIBRARY` is set, the skill stops and says to
   unset it.
9. **Several tests run one after another** with one line each, until `arcus run` takes a folder. Then one call.
10. **Where the tests run is a target, not a backend.** Local by default, or a deployed target the repo names (edge, a
    preview). It changes only `--base-url`. Cases and pushes stay in the project `arcus.json` names.
11. **Version 0.9.0.** A new skill is a minor.

## What changes

| File | Change |
|---|---|
| `skills/verify/SKILL.md` | new |
| `references/verifying.md` | new: the comment's shape, the marker, intent changes, how to find the story |
| `skills/author/SKILL.md`, `skills/run/SKILL.md`, `skills/push/SKILL.md` | name `/arcus:verify` where a user asks to prove a change |
| `commands/help.md`, `README.md` | the new skill and flow |
| `plugin.json` | 0.9.0 |
| `tests/` | the skill, the new CLI surface, the handovers |

## Evals

Not in 0.9.0. Each case needs QI to answer `arcus test list --sprint --issue-id` with known cases, and the eval
scaffolds have no way to stand in for Arcus yet. They come once there is a fixture for that, or against a seeded
project on a local stack:

| Case | Proves |
|---|---|
| `verify-automates-the-story-cases` | the tests written are the story's cases, one each, titled as the cases are |
| `verify-does-not-edit-an-approved-case` | a failure against an approved case's expected result is listed as an intent change, and the `verify` stays |
| `verify-with-no-cases-stops` | with no cases on the story, nothing is invented and the user is told where to generate them |

## Out of scope

Running in CI, comparing with the base branch, and judging a failure as a bug. Those belong to the PR check that runs
after deployment. Accepting into Arcus. Recording a local run in Arcus (the CLI has no such command yet).
